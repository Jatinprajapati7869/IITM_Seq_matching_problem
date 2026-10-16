# Research harness (offline analysis only)

**Nothing in this folder is used by the submitted policy, and nothing here is copied into the Docker image.** It reproduces the low-noise evidence in REPORT.md sections 6 and 7.

- `harness.py`: runs the official `evaluate.episode` in-process with a faster simulator that is semantically identical; it took the same actions as the CLI in 72 of 72 checked episodes. *After* each episode, it computes `expected_msmi`: the exact probability that each introduction becomes a mutual second-meeting intention, using hidden simulator values. The policy never receives these values.
- `compare.py`: runs a paired comparison of any `policy.CONFIGS` entries on the same worlds. It prints realized and expected scores, coverage and realized-vs-expected calibration (z) for each policy.

```bash
pip install -r requirements-research.txt          # numpy, research only
python research/compare.py --policies greedy,v1 --seeds 2000-2019 --out results/research_validation.json
python research/compare.py --policies greedy,v1 --seeds 3000-3019 --out results/research_test_split_expected.json
```

Seed protocol: validation 2000–2499 for development, test 3000–3499 for confirmation only (3000–3019 used once for the frozen v1), public 101–103 for the official evaluator only.
