"""Submitted policy v1: validity shield + targeted constraint asks + maximum-cardinality matching.

Uses ONLY the observable JSON request (state + policy memory). It never reads hidden simulator
objects, world seeds or organiser files. Deterministic: no randomness is used at inference
(declared inference random seed: none required; see README).

Entry point: reads one JSON request on stdin, writes one JSON response on stdout, exits 0.
The `--baseline` option passed by the reference runner in local mode is accepted and ignored;
the supplied baselines live in baselines.py.
"""
import argparse
import itertools
import json
import os
import sys
import time

_START = time.monotonic()
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, 'vendor'))  # vendored networkx 3.4.2 (BSD-3-Clause)
sys.path.insert(0, _HERE)

from kit import eligibility, HARD, SOFT  # noqa: E402

COVERAGE_BONUS = 0.5    # tie-break weight per never-introduced endpoint
SOFT_WEIGHT = 0.01      # tie-break weight per shared observed soft field
PENDING_WEIGHT = 0.5    # weight of a still-incomplete potential partner when ranking asks
TIME_GUARD_S = 6.0      # if the call is already this slow, use the cheap greedy matcher instead


# ---------- observable helpers ----------
def complete(m):
    return all(m['fields'].get(k) is not None for k in HARD)


def blocked(m):
    return any(m.get('field_status', {}).get(k) == 'declined' for k in HARD)


def past_pairs(s):
    return {tuple(sorted((i['user_a'], i['user_b']))) for i in s.get('introductions', [])}


def paused_ids(s):
    ends = {i['introduction_id']: (i['user_a'], i['user_b']) for i in s.get('introductions', [])}
    return {x for e in s.get('feedback', []) if e.get('event') == 'pause_after_mutual_interest'
            for x in ends.get(e.get('introduction_id'), ())}


def served_ids(s):
    return {x for i in s.get('introductions', []) for x in (i['user_a'], i['user_b'])}


def soft_score(a, b):
    return sum(a['fields'].get(k) is not None and a['fields'].get(k) == b['fields'].get(k) for k in SOFT)


def feasible_edges(s):
    av = [m for m in s['members'] if m['available'] and complete(m)]
    past, out = past_pairs(s), []
    for a, b in itertools.combinations(av, 2):
        key = tuple(sorted((a['member_id'], b['member_id'])))
        if key not in past and eligibility(a, b)['status'] == 'feasible':
            out.append((a, b, key))
    return out


# ---------- clarification ----------
def asks_baseline(s):
    el = [m for m in s['members'] if m['available'] and not complete(m) and not blocked(m)]
    return [{'member_id': m['member_id'], 'field': 'constraints'} for m in el[:s['ask_budget_remaining'] // 3]]


def asks_targeted(s):
    """Same candidate set as the baseline, ordered by how many partners each member could unlock."""
    past, gone = past_pairs(s), paused_ids(s)
    pool = [m for m in s['members'] if not blocked(m) and m['member_id'] not in gone]
    cands = [m for m in pool if m['available'] and not complete(m)]

    def potential(c):
        tot = 0.0
        for j in pool:
            if j is c or tuple(sorted((c['member_id'], j['member_id']))) in past:
                continue
            if eligibility(c, j)['status'] != 'infeasible':
                tot += 1.0 if complete(j) else PENDING_WEIGHT
        return tot

    ranked = sorted(cands, key=lambda m: (-potential(m), m['arrived_day'], m['member_id']))
    return [{'member_id': m['member_id'], 'field': 'constraints'} for m in ranked[:s['ask_budget_remaining'] // 3]]


# ---------- allocation ----------
def match_greedy(s):
    edges = sorted((-soft_score(a, b), key) for a, b, key in feasible_edges(s))
    used, out = set(), []
    for _, k in edges:
        if not used.intersection(k):
            out.append(list(k))
            used.update(k)
    return out


def match_maxcard(s, coverage_bonus=COVERAGE_BONUS):
    """Maximum-cardinality matching on the general graph; ties broken by newcomer bonus, then soft fields."""
    import networkx as nx
    served, g = served_ids(s), nx.Graph()
    for a, b, key in feasible_edges(s):
        w = 1.0 + coverage_bonus * ((key[0] not in served) + (key[1] not in served)) + SOFT_WEIGHT * soft_score(a, b)
        g.add_edge(key[0], key[1], weight=w)
    return sorted(sorted(p) for p in nx.max_weight_matching(g, maxcardinality=True))


# ---------- validity shield: drop anything the simulator would reject ----------
def shield_asks(s, asks):
    by = {m['member_id']: m for m in s['members']}
    seen, left, out = set(), s['ask_budget_remaining'], []
    for a in asks:
        if not (isinstance(a, dict) and set(a) == {'member_id', 'field'}):
            continue
        i, f = a['member_id'], a['field']
        if not (isinstance(i, str) and isinstance(f, str)) or i not in by or not by[i]['available']:
            continue
        if f not in ['constraints'] + list(SOFT) or (i, f) in seen:
            continue
        cost = 3 if f == 'constraints' else 1
        if cost > left:
            continue
        seen.add((i, f))
        left -= cost
        out.append({'member_id': i, 'field': f})
    return out


def shield_pairs(s, pairs):
    by = {m['member_id']: m for m in s['members']}
    past, used, out = past_pairs(s), set(), []
    for p in pairs:
        if not (isinstance(p, (list, tuple)) and len(p) == 2 and all(isinstance(x, str) for x in p)):
            continue
        a, b = p
        if a == b or a not in by or b not in by or a in used or b in used:
            continue
        if not (by[a]['available'] and by[b]['available']) or tuple(sorted(p)) in past:
            continue
        if eligibility(by[a], by[b])['status'] != 'feasible':
            continue
        used.update(p)
        out.append([a, b])
    return out


# ---------- configurations (v1 is submitted; others are ablations) ----------
CONFIGS = {
    'v1': (asks_targeted, match_maxcard),
    'greedy': (asks_baseline, match_greedy),
    'no_asks': (lambda s: [], match_greedy),
    'targeted_asks_only': (asks_targeted, match_greedy),
    'maxcard_only': (asks_baseline, lambda s: match_maxcard(s, 0.0)),
    'maxcard_newcomer_only': (asks_baseline, match_maxcard),
    'v1_no_newcomer_bonus': (asks_targeted, lambda s: match_maxcard(s, 0.0)),
}


def decide(request, config='v1'):
    """Return a valid response for any well-formed request; on internal errors degrade safely."""
    s = request['state']
    memory = request.get('memory')
    memory = memory if isinstance(memory, dict) else {}
    ask_fn, match_fn = CONFIGS[config]
    if request['phase'] == 'ask':
        for fn in (ask_fn, asks_baseline):
            try:
                return {'asks': shield_asks(s, fn(s)), 'memory': memory}
            except Exception as exc:  # pragma: no cover - defensive
                print('ask fallback: %r' % (exc,), file=sys.stderr)
        return {'asks': [], 'memory': memory}
    fns = (match_fn, match_greedy) if time.monotonic() - _START < TIME_GUARD_S else (match_greedy,)
    for fn in fns:
        try:
            return {'pairs': shield_pairs(s, fn(s)), 'memory': memory}
        except Exception as exc:  # pragma: no cover - defensive
            print('match fallback: %r' % (exc,), file=sys.stderr)
    return {'pairs': [], 'memory': memory}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', default=None, help='accepted for runner compatibility; ignored')
    parser.parse_known_args()
    request = json.load(sys.stdin)
    config = os.environ.get('POLICY_CONFIG', 'v1')
    sys.stdout.write(json.dumps(decide(request, config), allow_nan=False))
    sys.stdout.flush()


if __name__ == '__main__':
    main()
