"""RESEARCH-ONLY harness (never imported by policy.py). Official evaluate.episode logic, in-process policy calls, faster but equivalent simulator,
plus a RESEARCH-ONLY exact expected-MSMI metric computed from latent truth (never visible to policies)."""
import sys, json, math, statistics as st
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, 'vendor')]
from unittest.mock import patch
import numpy as np
import evaluate
from kit import Simulator, generate
VARIANTS = evaluate.VARIANTS
SEEDS = {'train': range(1000, 2000), 'validation': range(2000, 2500), 'test': range(3000, 3500), 'public': [101, 102, 103]}

class FastSimulator(Simulator):
    """Same semantics as kit.Simulator; caches pause times instead of scanning every event per member."""
    def __init__(self, world):
        super().__init__(world); self._pause = {}
    def available(self, m):
        i = m['member_id']; p = self._pause.get(i)
        return m['arrived_day'] <= self.day < m['exit_day'] and not (p is not None and p <= self.day) and self.busy.get(i, -1) <= self.day
    def advance(self, pairs):
        super().advance(pairs)
        ends = {x['introduction_id']: (x['user_a'], x['user_b']) for x in self.introductions}
        for e in self.events:
            if e['event'] == 'pause_after_mutual_interest':
                for i in ends[e['introduction_id']]:
                    self._pause[i] = min(self._pause.get(i, 10**9), e['observed_day'])

# ---- exact expected P(MSMI | introduction) — RESEARCH ONLY ----
_x, _w = np.polynomial.hermite_e.hermegauss(40); _w = _w / _w.sum(); _S = _x * .45
def _sig(z): return 1 / (1 + np.exp(-z))
_DATE_OK = {}
def date_ok(variant):
    if variant not in _DATE_OK:
        if variant != 'delayed': _DATE_OK[variant] = 1.0
        else:
            ok = tot = 0
            for a in range(1, 8):
                for b in range(1, 8):
                    for u in range(1, 15):
                        for v in range(5, 13): tot += 1; ok += max(a, b) + u + v <= 30
            _DATE_OK[variant] = ok / tot
    return _DATE_OK[variant]
def p_msmi(a, b, variant, day):
    f, g = a['truth'], b['truth']
    w = {'relationship_goal': .7, 'relationship_pace': .4, 'lifestyle': .25, 'conversations': .2}
    if variant == 'shift': w = {'relationship_goal': .25, 'relationship_pace': .8, 'lifestyle': -.25, 'conversations': .5}
    fit = sum(x * (1 if f[k] == g[k] else -.5) for k, x in w.items()); dr = -.5 if variant == 'drift' and day >= 35 else 0
    gm = .4 * (f['relationship_goal'] == g['relationship_goal'])
    v = (a['response_rate'] * _sig(-.25 + a['bias'] + fit + _S + dr) * b['response_rate'] * _sig(-.25 + b['bias'] + fit + _S + dr)
         * a['response_rate'] * _sig(.15 + a['second_bias'] + _S + gm) * b['response_rate'] * _sig(.15 + b['second_bias'] + _S + gm))
    return float((v * _w).sum()) * .78 * .36 * date_ok(variant)

def run_episode(decide, seed, variant, sim_class=None):
    sim_class = sim_class or FasterSimulator
    """decide(request)->response. Requests/responses round-trip through JSON exactly like the real boundary."""
    holder = {}
    class Tracked(sim_class):
        def __init__(self, world): super().__init__(world); holder['sim'] = self
    def inv(command, request, timeout=10):
        raw = json.dumps(request, allow_nan=False)
        if len(raw.encode()) > evaluate.LIMIT: raise ValueError('Request exceeds 1 MiB')
        out = json.loads(json.dumps(decide(json.loads(raw)), allow_nan=False))
        return evaluate.validate_response(out, request['phase']), 0.0
    try:
        with patch('evaluate.invoke', side_effect=inv):
            row = evaluate.episode(generate(seed, 200, 'evaluation', variant), [], simulator_class=Tracked)
    except (ValueError, TypeError, KeyError, OSError) as e:
        return {'valid': False, 'error': str(e), 'seed': seed, 'variant': variant}
    sim = holder['sim']
    row['expected_msmi'] = sum(p_msmi(sim.members[i['user_a']], sim.members[i['user_b']], variant, i['assigned_day']) for i in sim.introductions)
    row.update(seed=seed, variant=variant); row.pop('first_introduction_wait_days', None) if False else None
    return row

def summary(rows):
    """Primary score as the official formula, plus the low-noise expected version."""
    out = {}
    for key, f in [('primary_realized', lambda r: r['msmi_per_100_arrived_members']), ('primary_expected', lambda r: 100 * r['expected_msmi'] / r['arrived_members']),
                   ('coverage', lambda r: r['coverage']), ('mutual_per_100', lambda r: r['mutual_acceptances_per_100']), ('assignments', lambda r: r['assignments']), ('ask_cost', lambda r: r['ask_cost'])]:
        fam = {v: st.mean(f(r) for r in rows if r['variant'] == v) for v in VARIANTS if any(r['variant'] == v for r in rows)}
        out[key] = {'overall': st.mean(fam.values()), **fam}
    out['invalid'] = sum(not r['valid'] for r in rows)
    return out

def paired(rows_a, rows_b, key='expected_msmi'):
    """Mean per-episode difference B-A in primary-score units (x0.5), with SE, per family and overall."""
    A = {(r['variant'], r['seed']): r for r in rows_a}; res = {}
    for v in VARIANTS:
        d = [0.5 * (r[key] - A[(v, r['seed'])][key]) for r in rows_b if r['variant'] == v and (v, r['seed']) in A]
        if d: res[v] = (st.mean(d), st.stdev(d) / math.sqrt(len(d)) if len(d) > 1 else 0)
    m = st.mean(x[0] for x in res.values()); se = math.sqrt(sum(x[1] ** 2 for x in res.values())) / len(res)
    res['overall'] = (m, se); return res

class FasterSimulator(FastSimulator):
    """observe() without deepcopy: safe here because run_episode JSON-copies every request before the policy sees it."""
    def observe(self):
        vis = []
        for m in self.members.values():
            if m['arrived_day'] > self.day: continue
            o = {k: m[k] for k in ['member_id','pool_id','synthetic','age','gender','zone','arrived_day','fields','field_status','field_observed_day','source']}
            o['available'] = self.available(m); vis.append(o)
        return {'schema_version': '1.0.0', 'synthetic': True, 'day': self.day, 'ask_budget_remaining': 12 - self.ask_spent, 'members': vis,
                'introductions': self.introductions, 'feedback': [e for e in self.events if e['observed_day'] <= self.day], 'ask_log': self.ask_log}
