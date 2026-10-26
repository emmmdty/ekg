#!/usr/bin/env bash
# One finite admitted CE experiment; stop on failure, retain every raw artifact.
set -euo pipefail
cd /data/TJK/ekg
mkdir -p logs
for r114_log in logs/ergo-ce-training-20261026.log logs/ergo-ce-independent-20261026.log logs/ergo-ce-comparison-20261026.log logs/ergo-ce-pipeline-20261026.exit; do
    test ! -e "$r114_log"
done
trap 'r114_exit=$?; printf "%s\n" "$r114_exit" > logs/ergo-ce-pipeline-20261026.exit' EXIT
export CUDA_VISIBLE_DEVICES=1 PYTHONPATH=src:scripts OMP_NUM_THREADS=12
export TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
printf 'phase=train\n'
timeout --signal=TERM --kill-after=60s 173400s .venv/bin/python -u scripts/run_ergo_ce_control.py \
    --operation train --config configs/ergo_ce_training_20261026.json \
    > logs/ergo-ce-training-20261026.log 2>&1
printf 'phase=independent_verify\n'
timeout --signal=TERM --kill-after=60s 3600s .venv/bin/python -u scripts/run_ergo_ce_control.py \
    --operation verify --config configs/ergo_ce_training_20261026.json \
    --report runs/stages/A4/a4-ergo-control-unweighted-ce-20261026/seed-13/report.json \
    --output runs/stages/R1/r1-v114-ergo-ce-independent-20261026/ce --device cuda \
    > logs/ergo-ce-independent-20261026.log 2>&1
printf 'phase=five_frozen_comparisons\n'
CUDA_VISIBLE_DEVICES=-1 timeout --signal=TERM --kill-after=60s 300s .venv/bin/python -u scripts/compare_a4_causal_predictions.py \
    --gold runs/stages/A3/a3-v6-baselines-r10/preflight/data/MAVEN_ERE/valid.jsonl \
    --pred runs/stages/R1/r1-v114-ergo-ce-independent-20261026/ce/predictions.jsonl \
    --manifest data/protocols/v6/manifests/maven_ere_internal-dev.json \
    --evaluator data/protocols/v6/tools/maven_ere_evaluate.py \
    --plan runs/stages/R1/r1-v113-ergo-ce-budget-20261026/comparison_plan.json \
    --output runs/stages/R1/r1-v115-ergo-ce-comparison-20261026/report.json \
    > logs/ergo-ce-comparison-20261026.log 2>&1
printf 'phase=complete\n'
