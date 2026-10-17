"""Build the report figures from the committed JSON in results/ (research only).

Usage: python research/make_figures.py
"""
import json
import math
import os
import statistics as st

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, 'results')
FIG = os.path.join(ROOT, 'docs', 'figures')
VARIANTS = ['development', 'sparse', 'cold_start', 'delayed', 'shift', 'drift']
FAMILY = {'development': 'standard', 'sparse': 'sparse', 'cold_start': 'cold start',
          'delayed': 'delayed', 'shift': 'shift', 'drift': 'drift'}
CONFIG = {'no_asks': 'No asks', 'maxcard_only': 'Max matching only',
          'maxcard_newcomer_only': 'Max matching + newcomer bonus', 'targeted_asks_only': 'Targeted asks only',
          'v1_no_newcomer_bonus': 'v1 without newcomer bonus', 'v1': 'v1 (submitted)'}
DARK, GREY, ROSE, LIGHT = '#2E3A59', '#9AA0A6', '#D98C8C', '#C9CCD1'


def load(name):
    with open(os.path.join(RES, name)) as f:
        return json.load(f)


def save(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, name), dpi=180)
    plt.close(fig)


def paired(rows, ref, new):
    """Per-family mean and SE of the expected-score difference new - ref (200 members, so x0.5)."""
    base = {(r['variant'], r['seed']): r['expected_msmi'] for r in rows if r['policy'] == ref}
    out = {}
    for v in VARIANTS:
        d = [0.5 * (r['expected_msmi'] - base[(v, r['seed'])]) for r in rows if r['policy'] == new and r['variant'] == v]
        out[v] = (st.mean(d), st.stdev(d) / math.sqrt(len(d)))
    return out


def overall(fam):
    return st.mean(m for m, _ in fam.values()), math.sqrt(sum(se ** 2 for _, se in fam.values())) / len(fam)


def fig_gain_by_family():
    splits = [('Validation (420 worlds)', 'research_validation.json', DARK),
              ('Held-out test (120 worlds)', 'research_test_split_expected.json', ROSE)]
    fig, ax = plt.subplots(figsize=(8, 3.6))
    width = 0.38
    for i, (label, name, colour) in enumerate(splits):
        fam = paired(load(name), 'greedy', 'v1')
        xs = [j + (i - 0.5) * width for j in range(len(VARIANTS))]
        ax.bar(xs, [fam[v][0] for v in VARIANTS], width, yerr=[fam[v][1] for v in VARIANTS],
               color=colour, capsize=3, label=label)
    ax.axhline(0, color='black', lw=0.8)
    ax.set_xticks(range(len(VARIANTS)), [FAMILY[v] for v in VARIANTS])
    ax.set_ylabel('Expected score, v1 − greedy')
    ax.set_title('Expected gain of v1 over greedy by scenario family (paired, mean ± SE)', fontsize=11)
    ax.legend(frameon=False)
    save(fig, 'fig2_gain_by_family.png')


def fig_funnel():
    runs = [('v1', 'final.json', DARK), ('greedy', 'baseline_greedy.json', GREY),
            ('random', 'baseline_random.json', ROSE), ('no asks', 'baseline_no_asks.json', LIGHT)]
    stages = [('Introductions', 'assignments'), ('Mutual acceptances', 'mutual_acceptances'),
              ('Dates', 'dates'), ('MSMI pairs', 'mutual_second_meeting_intention')]
    episodes = {label: load(name)['episodes'] for label, name, _ in runs}
    fig, axes = plt.subplots(1, len(stages), figsize=(11, 3.3))
    for ax, (title, key) in zip(axes, stages):
        values = [sum(e[key] for e in episodes[label]) for label, _, _ in runs]
        ax.bar([label for label, _, _ in runs], values, color=[c for _, _, c in runs])
        for i, v in enumerate(values):
            ax.text(i, v, str(v), ha='center', va='bottom', fontsize=8)
        ax.set_title(title, fontsize=10)
        ax.tick_params(axis='x', labelsize=8)
        ax.margins(y=0.15)
    fig.suptitle('Totals over the 18 public episodes (official evaluator, seeds 101–103 × 6 families)', fontsize=11)
    save(fig, 'fig1_funnel.png')


def fig_ablation():
    rows = load('research_ablation.json')
    order = ['no_asks', 'maxcard_only', 'maxcard_newcomer_only', 'targeted_asks_only', 'v1_no_newcomer_bonus', 'v1']
    stats = [overall(paired(rows, 'greedy', p)) for p in order]
    rest = [(m, se) for (m, se), p in zip(stats, order) if p != 'no_asks']
    left, right = min(-0.01, min(m - se for m, se in rest) - 0.005), max(m + se for m, se in rest) + 0.006
    fig, ax = plt.subplots(figsize=(8, 3.6))
    ys = list(range(len(order)))
    ax.barh(ys, [m for m, _ in stats], xerr=[se for _, se in stats], capsize=3,
            color=[DARK if p == 'v1' else GREY for p in order])
    for y, p, (m, se) in zip(ys, order, stats):
        if p == 'no_asks':
            ax.text(0.0005, y, f'No asks: {m:+.3f} (bar cut off)', va='center', fontsize=8)
        else:
            ax.text(max(m + se, 0) + 0.0004, y, f'{m:+.4f}', va='center', fontsize=8)
    ax.set_yticks(ys, [CONFIG[p] for p in order])
    ax.set_xlim(left, right)
    ax.axvline(0, color='black', lw=0.8)
    ax.set_xlabel('Expected score vs greedy (paired, mean ± SE)')
    ax.set_title('Ablation, validation seeds 2000–2019 (120 worlds each)', fontsize=11)
    save(fig, 'fig4_ablation.png')


def fig_calibration():
    splits = [('Public, 18 worlds', 'research_public_check.json'), ('Validation, 420 worlds', 'research_validation.json'),
              ('Held-out test, 120 worlds', 'research_test_split_expected.json')]
    fig, axes = plt.subplots(1, len(splits), figsize=(10, 3.4))
    for ax, (title, name) in zip(axes, splits):
        rows = load(name)
        for i, (policy, colour) in enumerate([('greedy', GREY), ('v1', DARK)]):
            mine = [r for r in rows if r['policy'] == policy]
            real = sum(r['mutual_second_meeting_intention'] for r in mine)
            exp = sum(r['expected_msmi'] for r in mine)
            ax.bar(i, real, 0.6, color=colour)
            ax.errorbar(i, exp, yerr=math.sqrt(exp), fmt='o', color='black', ms=4, capsize=4)
            ax.text(i, real / 2, f'{real} realized\n{exp:.1f} expected', ha='center', va='center', fontsize=8,
                    color='white' if policy == 'v1' else 'black')
        ax.set_xticks([0, 1], ['greedy', 'v1'])
        ax.set_title(title, fontsize=10)
        ax.margins(y=0.15)
    axes[0].set_ylabel('MSMI pairs')
    fig.suptitle('Realized MSMI pairs (bars) vs expected (dots, ± 1 SD)', fontsize=11)
    save(fig, 'fig3_calibration.png')


if __name__ == '__main__':
    os.makedirs(FIG, exist_ok=True)
    fig_gain_by_family()
    fig_funnel()
    fig_ablation()
    fig_calibration()
    print('figures written to', FIG, sorted(os.listdir(FIG)))
