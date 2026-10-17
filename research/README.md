# Research code (offline only)

Nothing in this folder is used by the submitted policy, and none of it is copied into the Docker image. It produces the expected-score evidence in REPORT.md sections 1 and 6 to 8.

- `harness.py` runs the official `evaluate.episode` loop with in-process policy calls and a faster copy of the simulator. After each episode it computes `expected_msmi`, the exact probability that each introduction ends in a mutual second-meeting intention, from hidden simulator values. The policy never receives these values.
- `compare.py` runs a paired comparison of any configurations in `policy.CONFIGS` on the same worlds. It prints realized and expected scores, coverage, and realized against expected successes (z) for each configuration, and paired differences against the first one.
- `oracle_ranking.py` is a diagnostic, not a policy. It runs greedy with feasible pairs ordered by their true hidden MSMI probability, to estimate the most that perfect pair ranking could add (REPORT.md section 1).
- `checks.py` confirms that the harness takes exactly the same actions as the official evaluator on the public seeds, and counts members who can never be introduced because they declined a hard field.
- `make_figures.py` builds the figures in `docs/figures/` from the committed JSON in `results/`.

```bash
pip install -r requirements-research.txt
python research/compare.py --policies greedy,v1 --seeds 2000-2069 --out results/research_validation.json > results/research_validation.txt
python research/compare.py --policies greedy,no_asks,v1 --seeds 101-103 --out results/research_public_check.json > results/research_public_check.txt
python research/checks.py
python research/make_figures.py
```

The full list of research commands is in the main README. Seeds: validation 2000 to 2069, test 3000 to 3019 (run once for the frozen v1), public 101 to 103.
