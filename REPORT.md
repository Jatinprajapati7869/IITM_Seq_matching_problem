# Getting More Workable Pairs Introduced in Time: Technical Report (Round 2)

**Team:** _<team name>_ · **Policy:** v1 (`policy.py`) · **Kit:** 1.0.0 · All people and outcomes are synthetic. The results describe this simulator only.

## 1 Hypothesis and decision objective

**Hypothesis.** The score is limited mainly by *how many workable pairs get introduced before the people involved become unavailable*, not by how well pairs are ranked. In a research-only diagnostic, we let greedy rank pairs by their true hidden success probability. This added only about +0.012 on seeds 101–105, which puts a ceiling on what any ranking model can gain. So v1 targets clarification and allocation instead.

**Objective at each decision.** Each day, v1 (a) spends the 12-unit ask budget on members whose answers could make the most pairs feasible, and (b) introduces the largest possible set of feasible pairs that don't overlap. It never breaks a hard constraint and never makes an action the simulator would reject.

## 2 Method

**Reciprocal eligibility.** A pair is proposed only if both members are available, both have every hard field observed, the pair hasn't been introduced before, and the kit's `eligibility()` returns `feasible` in both directions. A missing hard field is never treated as a pass. A known hard failure blocks the pair.

**Validity shield.** Before returning, v1 removes any ask or pair that would be rejected: unknown or unavailable IDs, duplicate asks, going over budget, reused people, repeated pairs, or pairs that aren't feasible. If a component raises an error, v1 falls back to the baseline asks and greedy matching, and if those fail it returns an empty, valid response. If a call is already slower than 6 s, it uses the cheap greedy matcher. One invalid assessed episode makes a whole submission ineligible, so v1 is built to always return a valid response.

**Clarification (targeted asks).** The candidates are the same as the baseline's: available, incomplete members with no declined hard field. They are ranked by *potential*: the number of non-paused members who are not already known to be infeasible with them. A complete partner counts 1 and an incomplete one counts 0.5. Ties are broken by earliest arrival, then by ID. The hard-constraint bundle costs 3 units, so up to 4 members are asked each day. Members who declined a hard field are never asked again, because they can never become complete.

**Allocation (maximum-cardinality matching).** Possible pairs form a general graph, not a two-sided one, because preferences don't depend on a person's own gender. v1 runs `networkx.max_weight_matching(maxcardinality=True)`, with edge weight = 1 + 0.5 × (number of never-introduced endpoints) + 0.01 × (shared observed soft fields). Maximum cardinality comes first, so the weights only break ties between sets of the same size. Soft fields never override hard constraints.

**Waiting.** v1 doesn't hold pairs back on purpose. If a pair is feasible and fits in the maximum matching, it is introduced the same day. Members without a feasible partner wait, and they are still counted as unserved.

## 3 Observations, missing data, delays and leakage

- **Inputs:** only the request (`state`, `memory`). v1 uses `fields`, `field_status`, `available`, `arrived_day`, `introductions` and `feedback` (to detect pauses after mutual interest). Memory is passed through unchanged, and no state is kept between calls.
- **Missing or declined data:** if something is not asked, it stays unknown. A declined answer stays unknown and blocks the member's hard eligibility. Missing feedback is never treated as a preference label.
- **Delayed feedback:** v1 doesn't learn from outcomes, so delayed or missing feedback can't bias it. It reads feedback only to avoid asking members who are already paused.
- **Leakage prevention:** hidden simulator values (true fields, response rates, success probabilities) appear **only** in offline research analysis, never in `policy.py`. `test_runner.py` checks that no world fields reach the policy. Settings were fixed before the test split was used.

## 4 Training, assets and randomness

There is no training, no learned parameters, no external data, no pretrained model and no network access at inference. The only inference asset is vendored NetworkX 3.4.2 (BSD-3-Clause). v1 is deterministic, so no inference random seed is needed. All provenance and licences are in `THIRD_PARTY_NOTICES.md`. An AI coding assistant was used for code, analysis and writing, and the team reviewed and ran everything.

## 5 Results with the official evaluator (public seeds 101–103 × six families = 18 worlds per policy)

All runs used `evaluate.py` in trusted-local mode, with one real subprocess per call and identical seeds and families. Full JSON is in `results/`, and the commands are in `run_experiments.sh`.
| Policy | Valid episodes | Primary score (MSMI/100) | ± SE | Coverage | Mutual acc./100 | Ask cost/episode | Ranking key |
|---|---|---|---|---|---|---|---|
| v1 (submitted) | 18/18 | 0.333 | 0.081 | 0.379 | 6.17 | 207 | eligible=True |
| greedy | 18/18 | 0.389 | 0.065 | 0.372 | 5.50 | 207 | eligible=True |
| no_asks | 18/18 | 0.139 | 0.054 | 0.143 | 1.75 | 0 | eligible=True |
| random | 18/18 | 0.278 | 0.083 | 0.377 | 5.33 | 207 | eligible=True |
| ablation: targeted asks only | 18/18 | 0.444 | 0.114 | 0.370 | 6.36 | 207 | eligible=True |
| ablation: max matching only | 18/18 | 0.306 | 0.082 | 0.374 | 5.69 | 207 | eligible=True |
| ablation: max matching + newcomer bonus | 18/18 | 0.278 | 0.060 | 0.379 | 5.64 | 207 | eligible=True |
| ablation: v1 without newcomer bonus | 18/18 | 0.333 | 0.081 | 0.373 | 6.72 | 207 | eligible=True |

**Per scenario family: MSMI per 100 arrived members (mean of seeds 101-103)**

| Policy | development | sparse | cold_start | delayed | shift | drift |
|---|---|---|---|---|---|---|
| v1 (submitted) | 0.500 | 0.000 | 0.333 | 0.500 | 0.333 | 0.333 |
| greedy | 0.500 | 0.167 | 0.167 | 0.500 | 0.500 | 0.500 |
| no_asks | 0.167 | 0.000 | 0.000 | 0.333 | 0.167 | 0.167 |
| random | 0.333 | 0.167 | 0.167 | 0.167 | 0.500 | 0.333 |
| ablation: targeted asks only | 0.500 | 0.000 | 0.333 | 0.833 | 0.500 | 0.500 |
| ablation: max matching only | 0.500 | 0.167 | 0.000 | 0.167 | 0.500 | 0.500 |
| ablation: max matching + newcomer bonus | 0.333 | 0.167 | 0.000 | 0.333 | 0.500 | 0.333 |
| ablation: v1 without newcomer bonus | 0.500 | 0.000 | 0.333 | 0.500 | 0.333 | 0.333 |

**Per scenario family: coverage (share of members with at least one introduction)**

| Policy | development | sparse | cold_start | delayed | shift | drift |
|---|---|---|---|---|---|---|
| v1 (submitted) | 0.438 | 0.145 | 0.380 | 0.435 | 0.438 | 0.438 |
| greedy | 0.432 | 0.145 | 0.360 | 0.430 | 0.432 | 0.432 |
| no_asks | 0.183 | 0.043 | 0.080 | 0.183 | 0.183 | 0.183 |
| random | 0.440 | 0.145 | 0.363 | 0.438 | 0.433 | 0.440 |
| ablation: targeted asks only | 0.428 | 0.145 | 0.367 | 0.425 | 0.428 | 0.428 |
| ablation: max matching only | 0.433 | 0.145 | 0.368 | 0.433 | 0.432 | 0.433 |
| ablation: max matching + newcomer bonus | 0.440 | 0.145 | 0.375 | 0.438 | 0.438 | 0.440 |
| ablation: v1 without newcomer bonus | 0.433 | 0.145 | 0.365 | 0.430 | 0.433 | 0.433 |

**Outcome funnel and operations (totals over 18 episodes; waits pooled over served members)**

| Policy | Introductions | Dates | Mutual acceptances | MSMI pairs | Missing feedback | Served | Unserved | Median first wait (days) | 90th pct wait | Ask cost | Inference s/episode (mean, max) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| v1 (submitted) | 1458 | 177 | 222 | 12 | 741 | 1365 | 2235 | 3 | 16 | 3720 | 15.8, 23.4 |
| greedy | 1437 | 155 | 198 | 14 | 819 | 1338 | 2262 | 4 | 16 | 3720 | 10.1, 11.1 |
| no_asks | 438 | 48 | 63 | 5 | 240 | 514 | 3086 | 0 | 13 | 0 | 11.5, 13.5 |
| random | 1449 | 158 | 192 | 10 | 754 | 1356 | 2244 | 5 | 16 | 3720 | 10.4, 12.2 |
| ablation: targeted asks only | 1404 | 178 | 229 | 16 | 744 | 1333 | 2267 | 4 | 16 | 3720 | 7.2, 9.0 |
| ablation: max matching only | 1430 | 172 | 205 | 11 | 803 | 1347 | 2253 | 4 | 16 | 3720 | 15.5, 23.2 |
| ablation: max matching + newcomer bonus | 1441 | 170 | 203 | 10 | 816 | 1366 | 2234 | 4 | 16 | 3720 | 14.6, 15.4 |
| ablation: v1 without newcomer bonus | 1431 | 193 | 242 | 12 | 694 | 1344 | 2256 | 3 | 16 | 3720 | 15.8, 20.3 |

Paired realized difference v1 - greedy over the same 18 worlds: MSMI -0.056 ± 0.080; coverage +0.0075 ± 0.0024; v1 better/equal/worse in 3/10/5 worlds.

**How to read these results.** Public worlds have very few successes: there are 12–16 qualifying pairs per policy across 18 worlds, and one pair changes the score by about 0.028. The realized v1 − greedy difference (−0.056 ± 0.080) is well within noise. v1 was better in 3 worlds, equal in 10 and worse in 5. On these same 18 worlds, the research expected-score difference is −0.0002 ± 0.0049 (Round 1 analysis), so neither policy had a real edge here. What *does* show up clearly on these worlds is **coverage: +0.0075 ± 0.0024** (v1 serves more distinct members), and v1 has more dates and mutual acceptances than greedy (177 vs 155 dates; 222 vs 198 acceptances). We don't choose the submitted policy from 18 noisy worlds. The decision rests on the low-noise evidence in Section 6.

## 6 Lower-noise evidence: expected score on many worlds

Realized outcomes are too rare to separate the policies. Our research measure sums the simulator's exact success probability for every introduction made. This uses hidden values offline only, never inside the policy. We checked it against reality: over 3,925 single-pair runs it predicted 45.0 successes and 42 happened, and on new worlds the predicted and actual results stayed within noise in every family. Our faster harness took the same actions as `evaluate.py` in 72 of 72 episodes.

| Policy (change in expected score vs greedy, paired, mean ± SE) | Worlds | Change |
|---|---|---|
| no_asks | 120 (validation 2000–2019) | −0.2542 ± 0.0065 |
| random | 120 | −0.0026 ± 0.0030 |
| Targeted asks only | 120 | +0.0040 ± 0.0029 |
| Max matching only | 120 | +0.0017 ± 0.0019 |
| Max matching + newcomer bonus | 120 | +0.0027 ± 0.0021 |
| **v1 (all parts)** | 120 | **+0.0077 ± 0.0025** |
| v1, fresh validation worlds | 300 (2020–2069) | +0.0046 ± 0.0018 |
| v1, all validation worlds | 420 | +0.0055 ± 0.0015 |
| **v1, untouched test split (frozen settings, run once)** | 120 (test 3000–3019) | **+0.0143 ± 0.0030** |

**Final confirmation on the untouched test split.** Settings were frozen before this run, and it was done once at the end (`results/research_test_split_expected.json`). v1's expected gain was positive in **every** family: development +0.020, sparse +0.001, cold start +0.014, delayed +0.020, shift +0.012, drift +0.019. Distinct-member coverage rose by +0.30 ± 0.04 percentage points. The realized counts on those 120 worlds went the other way: v1 had 86 successes against greedy's 106 (−0.083 ± 0.052 per 100). v1's 86 matches its expected 86.5, while greedy's 106 is about 2.5 SD above its own expected 83.1. We report this openly. Our reading is that greedy was lucky on these outcome draws, but the realized result is exactly the kind of variation a single private evaluation can show.

The gain is consistent but small. On validation, +0.0055 is about 1.3 extra successful pairs across 120 episodes, so on one private evaluation v1 would beat greedy only about 54% of the time.

## 7 Ablation (hypothesis-driven)

**Claim tested:** only *combining* better clarification (more feasible members, sooner) with throughput allocation (more of them introduced) raises the score, because each part feeds the other.

- **Remove targeted asks (max matching only, ± newcomer bonus):** expected gain falls from +0.0077 to +0.0017 or +0.0027. More pairs introduced each day helps only a little when the pool of complete members is the bottleneck.
- **Remove max matching (targeted asks only):** +0.0040 ± 0.0029. More members become complete, but greedy matching wastes some of them at busy members.
- **Remove the newcomer bonus (`v1_no_newcomer_bonus`, official run):** coverage drops from 0.379 to 0.373, which matches the claim that the bonus spreads introductions to people who haven't had one yet.
- **Remove clarification entirely (no_asks):** −0.254. Asking is by far the most important part, because members can't be introduced until their hard fields are known.

**When it hurts:** in **cold start** v1 shows no expected gain (−0.0017 ± 0.0044). When most members are incomplete, ordering asks by potential partners can delay people who would complete a pair with someone already known. A pairing-aware ask order is the next thing to test.

## 8 Failure cases and stress conditions

- **Sparse supply:** there are about 22 feasible pairs per world, against about 119 in the standard family, and coverage is 0.145 for every policy that asks. There is very little to optimise, and many members simply have no feasible partner. They are counted as unserved, not removed.
- **Withheld or declined constraints:** in the kit, a missing hard field is declined with probability 0.07 and never filled. About 32.5% of members (39.0% in cold start) can never be introduced. v1 never asks them again and never guesses for them.
- **Incompatible candidates:** known hard failures always block a pair, and missing information is never treated as compatibility.
- **Competition for the same candidate:** someone with many possible partners can be in only one introduction at a time and is then busy for 8 days, so some of their pairs run out of time. This is the largest loss that can still be reduced (about 0.030 expected points for v1).
- **Pauses after success:** a success removes both people, along with their other possible pairs (about 0.052 points). No policy can recover this.
- **Delayed feedback and drift/shift:** v1 doesn't learn from outcomes, so delays and drift can't mislead it. The other side of this is that it can't take advantage of them either.
- **Validity under stress:** there were 0 invalid episodes across 840 validation episodes, 18 × 8 official runs and the test split. In replication, the shield never had to remove an action (0 of 39,474 asks and 0 of 45,483 pairs). The fallback was exercised in tests, by forcing errors and by running under Python 3.9 where vendored NetworkX can't import: it returned valid greedy actions.

## 9 Runtime and resources

| Measure | Value | Limit |
|---|---|---|
| Slowest call, in-process (ask / match) | 0.169 s / 0.432 s | 10 s per call, including startup |
| Slowest call as a fresh read-only process, day-25 state with 200 members | 0.84 s | 10 s |
| Inference per 120-call episode, official runs (mean, max) | 15.8 s, 23.4 s, including about 120 process startups | n/a |
| Largest request / response | 476 KB / under 1 KB | 1 MiB |
| Memory carried | `{}` | 1 MiB |
| Image contents | `kit.py`, `policy.py`, NetworkX (4.4 MB) | 2 GiB |

The Docker build and the offline container evaluation (`--network=none`, 2 CPUs, 1 GiB, read-only) run with the commands in `README.md`, and also in GitHub Actions on every push (`.github/workflows/verify.yml`). The output of the local container check is committed as `results/container_check.json`.

## 10 Limitations

- These outcomes are invented, and the simulator's response model, constraint-disclosure rates and 8-day busy period are assumptions. Nothing here shows that v1 would raise real second-meeting intention, or that its effect would be equal across groups of real people.
- The gain is small compared with noise on a single private evaluation. We report it as a modest, consistent improvement, not a guaranteed win.
- The expected-score measure depends on the simulator's own probability model. It is a research tool, not product evidence. Historical propensities are not supplied, so no off-policy claims are made.
- v1 doesn't learn per-member response tendencies or do lookahead scheduling. Both are untested future work.

## 11 Product integration note (Vouchsafe)

- **Consent and hard constraints:** v1 would only suggest people who have opted in to introductions. Hard constraints (who they want to meet, age range, zones, smoking, children, relationship structure, schedule) would be checked again against current, confirmed answers when an introduction is sent, not only when it was computed.
- **Human approval:** v1 produces *suggestions*. A matchmaker approves each one, and both members must accept before contact details are shared. Nobody is introduced automatically.
- **Explanations and uncertainty:** each suggestion would come with a plain reason (for example, "You both want a long-term relationship and share 2 of 4 lifestyle preferences; all your stated requirements are met") and a statement of what is still unknown. We would not show a success percentage, because synthetic probabilities are not calibrated for real people.
- **Declining and correcting:** members can decline a question (it stays unknown and isn't asked again), decline a suggestion without penalty, and correct any answer. Corrections take effect before the next suggestion.
- **Data minimisation:** the adapter sends only the fields the policy needs: opaque IDs, hard-constraint answers and their status, availability, arrival day and the few soft fields used for tie-breaks. It never sends names, photos, contact details, conversations or exact locations. Nothing is kept between calls.
- **Failure monitoring:** log every shield drop and fallback (both should be zero), monitor how long members wait for their first introduction and how many are never served, broken down by fairness-relevant groups, and track ask burden per member and the rate of declined suggestions. Alerts would pause automation.
- **Assumptions to validate first:** how burdensome the bundled question is in practice, whether the response and pause dynamics hold, whether maximising introductions leads to good real experiences or causes fatigue, and whether coverage gains are spread evenly. These need an authorised pilot with human review before any real use.

## 12 Reproducing

See `README.md` for the exact commands. `./run_experiments.sh` regenerates every file in `results/`. Seeds: public 101–103 (official runs), validation 2000–2069 (development), test 3000–3019 (one final confirmation). There are no training seeds and no inference randomness.
