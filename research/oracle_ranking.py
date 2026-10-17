"""Research-only diagnostic: how much could better pair ranking help?

The "oracle" keeps everything about the greedy baseline (same asks, same feasible pairs, same greedy
matcher) except one thing: it orders feasible pairs by their true hidden MSMI probability
(harness.p_msmi) instead of by shared soft fields. No real policy can see these values, so this is
not a policy. It estimates the most that a perfect pair-quality model could add to greedy.

Usage, from the repository root:
  python research/oracle_ranking.py --seeds 101-105,2000-2019 --out results/research_oracle_ranking.json

Each comma-separated seed range is also reported on its own.
"""
import argparse, json, os, sys, time
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness  # noqa: E402
from compare import POLICY, _decide, seeds  # noqa: E402

_LIVE = {}


class OracleSimulator(harness.FasterSimulator):
    """Remembers the running simulator so the oracle can read hidden member values."""
    def __init__(self, world):
        super().__init__(world); _LIVE['sim'] = self


def oracle_decide(request, variant):
    if request['phase'] == 'ask':
        return _decide(request, 'greedy')
    s, sim = request['state'], _LIVE['sim']
    edges = sorted((-harness.p_msmi(sim.members[k[0]], sim.members[k[1]], variant, s['day']), k)
                   for _, _, k in POLICY.feasible_edges(s))
    used, pairs = set(), []
    for _, k in edges:
        if not used.intersection(k):
            pairs.append(list(k)); used.update(k)
    return {'pairs': POLICY.shield_pairs(s, pairs), 'memory': request.get('memory') or {}}


def job(a):
    pol, v, s = a
    t = time.time()
    if pol == 'oracle':
        r = harness.run_episode(lambda q: oracle_decide(q, v), s, v, sim_class=OracleSimulator)
    else:
        r = harness.run_episode(lambda q: _decide(q, pol), s, v)
    r.update(policy=pol, wall_seconds=time.time() - t); return r


def report(rows, label):
    g = [r for r in rows if r['policy'] == 'greedy']; o = [r for r in rows if r['policy'] == 'oracle']
    sg, so = harness.summary(g), harness.summary(o)
    print(f'\nSeeds {label} ({len(g)} episodes per policy)')
    print('policy | invalid | expected score | coverage')
    for name, S in (('greedy', sg), ('oracle', so)):
        print(f"{name} | {S['invalid']} | {S['primary_expected']['overall']:.4f} | {S['coverage']['overall']:.4f}")
    d = harness.paired(g, o); c = harness.paired(g, o, key='coverage')
    print('Paired expected-score difference oracle - greedy (mean ± SE):')
    print('  ' + ', '.join(f'{k} {m:+.4f}±{se:.4f}' for k, (m, se) in d.items()))
    print('  coverage: ' + ', '.join(f'{k} {2*m:+.4f}±{2*se:.4f}' for k, (m, se) in c.items()))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', default='101-105,2000-2019'); p.add_argument('--workers', type=int, default=2)
    p.add_argument('--out', default=None)
    a = p.parse_args()
    groups = [(part, seeds(part)) for part in a.seeds.split(',')]
    all_seeds = sorted({s for _, ss in groups for s in ss})
    tasks = [(x, v, s) for x in ('greedy', 'oracle') for v in harness.VARIANTS for s in all_seeds]
    with Pool(a.workers) as pool: rows = pool.map(job, tasks, chunksize=2)
    if a.out:
        os.makedirs(os.path.dirname(a.out) or '.', exist_ok=True); json.dump(rows, open(a.out, 'w'))
    for label, ss in groups:
        report([r for r in rows if r['seed'] in set(ss)], label)


if __name__ == '__main__':
    main()
