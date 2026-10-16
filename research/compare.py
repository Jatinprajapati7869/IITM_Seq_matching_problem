"""RESEARCH-ONLY paired comparison of policy configurations on many simulator worlds.

Runs the official evaluate.episode logic in-process (same actions as the CLI; verified 72/72 episodes)
and adds a low-noise 'expected' score: the exact MSMI probability of every introduction made, computed
from hidden simulator values AFTER the episode. Hidden values are never visible to the policy.

Usage (from the repo root):
  python research/compare.py --policies greedy,v1 --seeds 2000-2049 --out results/research_val.json
  python research/compare.py --policies v1,v2_candidate --seeds 2000-2049 --variants development,cold_start
The FIRST policy is the reference for paired differences. Policy names are keys of policy.CONFIGS.
"""
import argparse, importlib.util, json, math, os, statistics as st, sys, time
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness  # noqa: E402

ROOT = harness.ROOT
_spec = importlib.util.spec_from_file_location('submitted_policy', os.path.join(ROOT, 'policy.py'))
POLICY = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(POLICY)


def _decide(q, cfg):
    POLICY._START = time.monotonic()  # each real call is a fresh process; reset the per-call time guard
    return POLICY.decide(q, cfg)


def job(a):
    pol, v, s = a
    t = time.time(); r = harness.run_episode(lambda q: _decide(q, pol), s, v)
    r.update(policy=pol, wall_seconds=time.time() - t); return r


def seeds(text):
    out = []
    for part in text.split(','):
        lo, _, hi = part.partition('-'); out += list(range(int(lo), int(hi or lo) + 1))
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--policies', required=True); p.add_argument('--seeds', required=True)
    p.add_argument('--variants', default='all'); p.add_argument('--workers', type=int, default=2)
    p.add_argument('--out', default=None)
    a = p.parse_args()
    pols = a.policies.split(','); V = harness.VARIANTS if a.variants == 'all' else a.variants.split(',')
    for x in pols:
        assert x in POLICY.CONFIGS, f'unknown policy {x}; choose from {sorted(POLICY.CONFIGS)}'
    tasks = [(x, v, s) for x in pols for v in V for s in seeds(a.seeds)]
    with Pool(a.workers) as pool: rows = pool.map(job, tasks, chunksize=2)
    if a.out:
        os.makedirs(os.path.dirname(a.out) or '.', exist_ok=True); json.dump(rows, open(a.out, 'w'))
    by = {x: [r for r in rows if r['policy'] == x] for x in pols}
    print('policy | invalid | expected score | realized score | coverage | realized/expected successes (z)')
    for x in pols:
        R = by[x]; S = harness.summary(R); real = sum(r['mutual_second_meeting_intention'] for r in R if r['valid'])
        exp = sum(r['expected_msmi'] for r in R if r['valid']); z = (real - exp) / math.sqrt(exp) if exp else 0
        print(f"{x} | {S['invalid']} | {S['primary_expected']['overall']:.4f} | {S['primary_realized']['overall']:.4f} | {S['coverage']['overall']:.4f} | {real}/{exp:.1f} ({z:+.1f})")
    ref = by[pols[0]]
    for x in pols[1:]:
        d = harness.paired(ref, by[x])
        print(f'\nPaired expected-score difference {x} - {pols[0]} (mean ± SE):')
        print('  ' + ', '.join(f'{k} {m:+.4f}±{se:.4f}' for k, (m, se) in d.items()))
        c = harness.paired(ref, by[x], key='coverage')
        print('  coverage: ' + ', '.join(f'{k} {2*m:+.4f}±{2*se:.4f}' for k, (m, se) in c.items()))


if __name__ == '__main__':
    main()
