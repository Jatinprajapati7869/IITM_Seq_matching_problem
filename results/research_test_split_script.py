"""E17 final confirmation on the UNTOUCHED test split (seeds 3000-3019, all six families), frozen v1 vs greedy.
Uses the submitted /data/final/sub/policy.py. Expected metric uses hidden values: OFFLINE RESEARCH ONLY."""
import sys, json, time; sys.path.insert(0,'/data/lab'); sys.path.insert(1,'/data/final/sub')
from multiprocessing import Pool
from harness import run_episode, VARIANTS, summary, paired
import importlib.util
_sp=importlib.util.spec_from_file_location('final_policy','/data/final/sub/policy.py'); final=importlib.util.module_from_spec(_sp); _sp.loader.exec_module(final)
assert 'v1' in final.CONFIGS
def dec(q, cfg):
    final._START = time.monotonic(); return final.decide(q, cfg)
def job(a):
    pol, v, s = a; r = run_episode(lambda q: dec(q, pol), s, v); r['policy'] = pol; return r
if __name__ == '__main__':
    with Pool(2) as p: rows = p.map(job, [(pol, v, s) for pol in ['greedy', 'v1'] for v in VARIANTS for s in range(3000, 3020)], chunksize=4)
    json.dump(rows, open('exp3_test.json', 'w'))
    by = {pol: [r for r in rows if r['policy'] == pol] for pol in ['greedy', 'v1']}
    for pol in by:
        S = summary(by[pol]); print(pol, 'invalid', S['invalid'], 'expected', round(S['primary_expected']['overall'], 4), 'realized', round(S['primary_realized']['overall'], 4), 'coverage', round(S['coverage']['overall'], 4))
    print('paired expected v1-greedy', {k: f'{m:+.4f}±{se:.4f}' for k, (m, se) in paired(by['greedy'], by['v1']).items()})
    print('paired coverage', {k: f'{m:+.4f}±{se:.4f}' for k, (m, se) in paired(by['greedy'], by['v1'], key='coverage').items()})
