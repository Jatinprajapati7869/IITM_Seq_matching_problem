"""RESEARCH-ONLY: build report figures from committed JSON results. Usage: python research/make_figures.py"""
import json, math, os, statistics as st
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES, FIG = os.path.join(ROOT, 'results'), os.path.join(ROOT, 'docs', 'figures')
os.makedirs(FIG, exist_ok=True)
VAR = ['development', 'sparse', 'cold_start', 'delayed', 'shift', 'drift']
INDIGO, GREY, PINK = '#2E3A59', '#9AA0A6', '#D98C8C'


def load(name):
    p = os.path.join(RES, name)
    return json.load(open(p)) if os.path.exists(p) else None


def paired_by_family(rows, ref='greedy', new='v1'):
    A = {(r['variant'], r['seed']): r for r in rows if r['policy'] == ref}
    out = {}
    for v in VAR:
        d = [0.5 * (r['expected_msmi'] - A[(v, r['seed'])]['expected_msmi']) for r in rows
             if r['policy'] == new and r['variant'] == v and (v, r['seed']) in A]
        if len(d) > 1:
            out[v] = (st.mean(d), st.stdev(d) / math.sqrt(len(d)))
    return out


# Figure 1: expected-score gain of v1 over greedy by family (each research JSON found)
sets = [(n, f) for n, f in [('Validation', 'research_validation.json'), ('Untouched test', 'research_test_split_expected.json')] if load(f)]
if sets:
    fig, ax = plt.subplots(figsize=(8, 3.6)); w = 0.8 / len(sets)
    for i, (label, f) in enumerate(sets):
        d = paired_by_family(load(f))
        xs = [j + i * w for j in range(len(VAR))]
        ax.bar(xs, [d.get(v, (0, 0))[0] for v in VAR], w, yerr=[d.get(v, (0, 0))[1] for v in VAR],
               color=[INDIGO, PINK][i % 2], capsize=3, label=label)
    ax.axhline(0, color='black', lw=0.8); ax.set_xticks([j + 0.4 - w / 2 for j in range(len(VAR))]); ax.set_xticklabels(VAR)
    ax.set_ylabel('Expected score: v1 − greedy'); ax.set_title('v1 gain over greedy by scenario family (mean ± SE, paired worlds)')
    ax.legend(frameon=False); fig.tight_layout(); fig.savefig(os.path.join(FIG, 'fig1_gain_by_family.png'), dpi=180); plt.close(fig)

# Figure 2: outcome funnel from the official evaluator runs (18 public worlds)
pols = [('v1', 'final.json', INDIGO), ('greedy', 'baseline_greedy.json', GREY), ('random', 'baseline_random.json', PINK)]
stages = [('Introductions', 'assignments'), ('Mutual acceptances', 'mutual_acceptances'), ('Dates', 'dates'), ('MSMI pairs', 'mutual_second_meeting_intention')]
if all(load(f) for _, f, _ in pols):
    fig, axes = plt.subplots(1, len(stages), figsize=(10, 3.2))
    for ax, (label, key) in zip(axes, stages):
        vals = [sum(e[key] for e in load(f)['episodes']) for _, f, _ in pols]
        ax.bar([p for p, _, _ in pols], vals, color=[c for _, _, c in pols]); ax.set_title(label, fontsize=10)
        for i, v in enumerate(vals): ax.text(i, v, str(v), ha='center', va='bottom', fontsize=8)
    fig.suptitle('Outcome funnel, official evaluator, public seeds 101–103 × 6 families (totals)', fontsize=11)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, 'fig2_funnel.png'), dpi=180); plt.close(fig)

# Figure 3: ablation (expected score vs greedy) from research_ablation.json if present
ab = load('research_ablation.json')
if ab:
    order = [p for p in ['no_asks', 'targeted_asks_only', 'maxcard_only', 'maxcard_newcomer_only', 'v1_no_newcomer_bonus', 'v1'] if any(r['policy'] == p for r in ab)]
    means, ses = [], []
    for p in order:
        d = paired_by_family(ab, 'greedy', p); m = st.mean(x[0] for x in d.values()); se = math.sqrt(sum(x[1] ** 2 for x in d.values())) / len(d)
        means.append(m); ses.append(se)
    fig, ax = plt.subplots(figsize=(8, 3.4))
    ax.barh(order, means, xerr=ses, color=[INDIGO if p == 'v1' else GREY for p in order], capsize=3)
    ax.axvline(0, color='black', lw=0.8); ax.set_xlabel('Expected score vs greedy (mean ± SE)'); ax.set_title('Ablation: which parts matter')
    if 'no_asks' in order: ax.set_xlim(left=min(-0.02, min(m for p, m in zip(order, means) if p != 'no_asks') - 0.01))
    if 'no_asks' in order:
        i = order.index('no_asks')
        ax.text(ax.get_xlim()[0], i, f"  no_asks = {means[i]:+.3f} (bar clipped)", va='center', fontsize=8, color='white')
    fig.tight_layout(); fig.savefig(os.path.join(FIG, 'fig3_ablation.png'), dpi=180); plt.close(fig)
print('figures in', FIG, sorted(os.listdir(FIG)))
