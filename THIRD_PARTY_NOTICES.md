# Third-party assets, licences and tools

| Asset | Version | Used for | Licence |
|---|---|---|---|
| CRSU x Romeo & Juliet starter kit (`kit.py`, `evaluate.py`, `organise.py`, `baselines.py`, tests, data, docs) | 1.0.0 (commit a1ba174) | Simulator, evaluator, baselines and synthetic data | `LICENSE` and `DATA_LICENSE.md` |
| NetworkX, vendored in `vendor/networkx` (tests removed) | 3.4.2 | Inference: `max_weight_matching` | BSD-3-Clause, see `THIRD_PARTY_LICENSE_networkx.txt` |
| Python, Docker base image `python:3.12.7-slim` | 3.12.7 | Inference runtime | PSF License |
| NumPy and Matplotlib (`requirements-research.txt`) | Results made with NumPy 2.5.3 and Matplotlib 3.11.2 | Offline research and figures only, not in the image | BSD-3-Clause; Matplotlib licence (PSF-based) |

- No trained model, external data, pretrained weights, network access or API calls are used at inference. No training compute is needed.
- Hidden simulator values are read only by the offline code in `research/`, never by `policy.py` or anything in the Docker image.
- The team's own work (`policy.py`, `test_policy_v1.py`, `run_experiments.sh`, `research/`, `README.md`, `REPORT.md` and `docs/figures/`) is under the MIT licence in `LICENSE-TEAM`.
- Tools: we used AI assistants (Notion AI and the Cursor editor) for parts of the code, analysis and writing. The team reviewed all code and ran every experiment reported.
