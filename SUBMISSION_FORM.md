# Text to paste into the "Final submission" GitHub issue

**Team name and size**
Outliers, 2 participant(s)

**Public source URL and immutable version**
Repository: https://github.com/Jatinprajapati7869/CSRU
Commit SHA: <FULL 40-CHARACTER SHA from `git rev-parse HEAD`>

**Report and results URLs**
Report: https://github.com/Jatinprajapati7869/CSRU/blob/<SHA>/REPORT.md
Results: https://github.com/Jatinprajapati7869/CSRU/tree/<SHA>/results
(final.json = v1; baseline_greedy/no_asks/random.json; ablation_*.json; container_check.json; research_test_split_expected.json)

**Build and evaluation commands**
python -m unittest -v
python verify_data.py
python evaluate.py --seeds 101,102,103 --variants all --output results/final.json
docker build -t sequential-policy:submission .
python evaluate.py --image sequential-policy:submission --seeds 101 --output results/container_check.json
Full reproduction: ./run_experiments.sh
Inference is offline, CPU only and deterministic. There are no network calls, no GPU and no trained model. NetworkX 3.4.2 is vendored, so the image builds without credentials or package downloads.

**Assets, licences and tools**
Starter kit 1.0.0 (kit licence and data licence). NetworkX 3.4.2, vendored (BSD-3-Clause, licence included). Base image python:3.12.7-slim (PSF). No external data, no pretrained or trained models, and no training compute. NumPy was used for offline research analysis only and is not in the image. An AI coding assistant (Notion AI) was used for code, analysis and writing; all code and results were reviewed and run by the team. See THIRD_PARTY_NOTICES.md.

**Validation and comparisons**
- All three baselines (greedy, no_asks, random) and v1 were run on identical public seeds 101–103 across all six scenario families: 18/18 valid episodes for each.
- Four ablations: targeted asks only, maximum matching only, maximum matching + newcomer bonus, and v1 without the newcomer bonus.
- Successful Docker build and container evaluation: results/container_check.json, plus GitHub Actions.
- 0 invalid episodes in all runs. See REPORT.md sections 5–9.
