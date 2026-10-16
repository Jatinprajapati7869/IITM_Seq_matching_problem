#!/usr/bin/env bash
# Reproduces every result in results/ with the official evaluator (real subprocess per call).
# Public seeds 101,102,103 x all six scenario families = 18 episodes per policy.
set -euo pipefail
PY=${PYTHON:-python}
S=101,102,103
mkdir -p results
lane1() {
  $PY evaluate.py --policy policy.py --seeds $S --variants all --output results/final.json            # submitted v1
  POLICY_CONFIG=targeted_asks_only $PY evaluate.py --policy policy.py --seeds $S --variants all --output results/ablation_targeted_asks_only.json
  for b in greedy no_asks random; do
    $PY evaluate.py --policy baselines.py --baseline $b --seeds $S --variants all --output results/baseline_$b.json
  done
}
lane2() {
  POLICY_CONFIG=maxcard_only $PY evaluate.py --policy policy.py --seeds $S --variants all --output results/ablation_maxcard_only.json
  POLICY_CONFIG=maxcard_newcomer_only $PY evaluate.py --policy policy.py --seeds $S --variants all --output results/ablation_maxcard_newcomer_only.json
  POLICY_CONFIG=v1_no_newcomer_bonus $PY evaluate.py --policy policy.py --seeds $S --variants all --output results/ablation_v1_no_newcomer_bonus.json
}
lane1 > results/lane1.log 2>&1 &
lane2 > results/lane2.log 2>&1
wait
echo done
