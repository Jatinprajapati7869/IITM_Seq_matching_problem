# Third-party assets, licences and tools

| Asset | Version | Where used | Licence |
|---|---|---|---|
| CRSU x Romeo & Juliet starter kit (`kit.py`, `evaluate.py`, `organise.py`, `baselines.py`, tests, data) | 1.0.0 (commit a1ba174) | Simulator, evaluator, baselines, synthetic data | See `LICENSE` and `DATA_LICENSE.md` |
| NetworkX (vendored in `vendor/networkx`, tests removed) | 3.4.2 | Inference: `max_weight_matching` | BSD-3-Clause, `THIRD_PARTY_LICENSE_networkx.txt` |
| Python (Docker base image `python:3.12.7-slim`) | 3.12.7 | Inference runtime | PSF License |

- **No trained model, no external data, no pretrained weights and no network or API calls** are used at inference. Training compute required: none.
- **Research-only tools (not in the image):** NumPy, for the offline expected-score analysis that reads simulator-hidden values. That analysis was never run inside the policy.
- **Coding tools:** an AI assistant (Notion AI) helped with code, analysis and writing. The team reviewed and ran all code and results.
