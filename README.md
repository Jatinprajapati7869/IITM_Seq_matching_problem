# Getting more workable pairs introduced in time: policy v1

**Team Outliers** — final submission for the CRSU x Romeo & Juliet Hackathon (Vouchsafe track), starter kit **1.0.0**. Full write-up: **[REPORT.md](REPORT.md)** · Figures: **[docs/figures/](docs/figures/)** · JSON: **[results/](results/)**.

### Results at a glance

| Source | Metric | v1 | greedy | random | no_asks |
|---|---|---:|---:|---:|---:|
| Official evaluator (seeds 101–103 × 6 families; `results/*.json`) | Primary score (MSMI/100) | **0.333** | 0.389 | 0.278 | 0.139 |
| Same | Coverage | **0.379** | 0.372 | 0.377 | 0.143 |
| Research expected gain vs greedy (paired; `research/compare.py`) | Validation 2000–2069 | **+0.0055 ± 0.0015** | — | — | — |
| Same | Test 3000–3019 (frozen, rerun in repo) | **+0.0143 ± 0.0030** | — | — | — |

Research commands (offline; uses hidden simulator values **only** in `research/`, never in `policy.py`):

```bash
uv run --python 3.12 python research/compare.py --policies greedy,v1 --seeds 2000-2069 --workers 8 --out results/research_validation.json
uv run --python 3.12 python research/compare.py --policies greedy,v1 --seeds 3000-3019 --workers 8 --out results/research_test_split_expected.json
```

**Policy v1** (`policy.py`) has three parts:
1. **Validity shield:** removes any ask or pair the simulator would reject.
2. **Targeted constraint asks:** asks first the members who could unlock the most possible partners.
3. **Maximum-cardinality matching:** finds the largest set of pairs each day on the general graph. Ties are broken by a bonus of 0.5 for each member never introduced before, then by 0.01 for each shared soft field.

It uses only the observable JSON request. It does not train a model and contains no randomness.

## Environment

| Item | Value |
|---|---|
| Python | 3.12.7 in Docker (`python:3.12.7-slim`). Local runs need Python 3.10 or later (tested with 3.12 and 3.13). |
| Dependencies | Inference uses the standard library plus **NetworkX 3.4.2, vendored in `vendor/`**. Nothing needs installing, and the image builds without network access or credentials. |
| Training seeds | **None.** v1 has no trained parameters. Research seeds are declared below. |
| Inference random seed | **None required.** v1 is deterministic. The supplied random baseline uses `random.Random(17 + day)`. |
| Hardware | CPU only. The slowest call is about 0.43 s in-process, or about 0.9 s including Python startup, against the 10 s limit. |

## Exact commands (run from this folder)

```bash
python -m unittest -v                     # kit tests + test_policy_v1.py
python verify_data.py
python evaluate.py --seeds 101,102,103 --variants all --output results/final.json      # v1 (policy.py)
docker build -t sequential-policy:submission .
python evaluate.py --image sequential-policy:submission --seeds 101 --output results/container_check.json
```

To reproduce every result (v1, the three baselines and the ablations; about 1.5 hours on 2 cores), run:

```bash
./run_experiments.sh
```

- Baselines: `python evaluate.py --policy baselines.py --baseline greedy|no_asks|random ...` (this is the unchanged starter `policy.py`).
- Ablations: `POLICY_CONFIG=<name> python evaluate.py --policy policy.py ...`, where `<name>` is one of `targeted_asks_only`, `maxcard_only`, `maxcard_newcomer_only` or `v1_no_newcomer_bonus`.
- `policy.py` accepts the runner's `--baseline` argument and ignores it, so it always runs v1 unless `POLICY_CONFIG` is set. The container needs no arguments.

## Seeds used

| Split | Seeds | Use |
|---|---|---|
| Public | 101–103 | Official-evaluator comparisons in `results/` |
| Validation | 2000–2069 | Development and replication (Round 1) |
| Test | 3000–3019 | One final confirmation of the frozen v1 (see the report) |

## Files

| File | Purpose |
|---|---|
| `policy.py` | Submitted policy and ablation configurations |
| `baselines.py` | Supplied greedy, no-asks and random-feasible baselines (unchanged) |
| `test_policy_v1.py` | Interface, validity, fallback and packaging tests for v1 |
| `Dockerfile`, `.dockerignore` | Offline image with `kit.py`, `policy.py` and `vendor/` |
| `run_experiments.sh` | Reproduces all JSON results |
| `REPORT.md` | Technical report with the product integration note |
| `THIRD_PARTY_NOTICES.md` | Provenance, licences and tools |
| `LICENSE-TEAM` | MIT licence for our own code; kit files keep the organisers' LICENSE |
| `research/` | Offline harness and expected-score comparisons (not in Docker image) |
| `KIT_README.md` | The organisers' original README |

All people and outcomes are synthetic. Results describe this simulator only.
