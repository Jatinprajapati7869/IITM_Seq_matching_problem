"""Two research-only checks used in REPORT.md. Usage: python research/checks.py

1. The research harness reproduces the official evaluator: on the public seeds, action hashes and
   MSMI counts in results/research_public_check.json must equal the official evaluator JSON files.
2. How many members can never be introduced because they declined at least one hard field.
   This uses only kit.generate, which builds the same worlds as the evaluator.
"""
import json
import os
import statistics as st
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from evaluate import VARIANTS  # noqa: E402
from kit import HARD, generate  # noqa: E402

OFFICIAL = {'v1': 'final.json', 'greedy': 'baseline_greedy.json', 'no_asks': 'baseline_no_asks.json'}


def load(name):
    with open(os.path.join(ROOT, 'results', name)) as f:
        return json.load(f)


def check_harness():
    rows = load('research_public_check.json')
    ok = True
    for policy, name in OFFICIAL.items():
        official = {(e['variant'], e['seed']): e for e in load(name)['episodes']}
        mine = [r for r in rows if r['policy'] == policy]
        same_actions = sum(r['action_sha256'] == official[(r['variant'], r['seed'])]['action_sha256'] for r in mine)
        same_msmi = sum(r['mutual_second_meeting_intention'] ==
                        official[(r['variant'], r['seed'])]['mutual_second_meeting_intention'] for r in mine)
        print(f'{policy}: identical actions in {same_actions}/{len(mine)} episodes, identical MSMI in {same_msmi}/{len(mine)}')
        ok = ok and same_actions == same_msmi == len(mine) == len(official)
    return ok


def declined_share(seeds=range(2000, 2020)):
    print(f'Members with a declined hard field (never introducible), seeds {seeds.start}-{seeds.stop - 1}:')
    for variant in VARIANTS:
        shares = []
        for seed in seeds:
            members = generate(seed, 200, 'evaluation', variant)['members']
            blocked = sum(any(m['field_status'][k] == 'declined' for k in HARD) for m in members)
            shares.append(blocked / len(members))
        print(f'  {variant}: {100 * st.mean(shares):.1f}%')


if __name__ == '__main__':
    passed = check_harness()
    declined_share()
    sys.exit(0 if passed else 1)
