#!/usr/bin/env bash
# Resume the E8 namespace after base-model acquisition completed successfully.
# Run only on gpu-4090. The checks intentionally reject any partial train,
# prediction, score, or LLMERE preparation tree instead of overwriting it.
set -euo pipefail

project_root=${1:?usage: resume_llmere_causal_adapter.sh /data/TJK/ekg GPU_INDEX}
gpu_index=${2:?usage: resume_llmere_causal_adapter.sh /data/TJK/ekg GPU_INDEX}
run_root="$project_root/runs/stages/R1/r1-v61-20260904/baselines/relation/llmere-causal-s13"
worker_env="$project_root/.venv-llmere-causal-s13"
model_path="$run_root/weights/NousResearch--Meta-Llama-3-8B"
llamafactory_root="$run_root/upstream/llama-factory"
llamafactory_ref=ca75f1edf3cb50343ed1c98605141c3e22075b5f
candidate_digest=313ec48e657374bc5afb7d09df9282c32f1d7a3acfdbfe1bc35435765042df3c

cd "$project_root"
test -s "$run_root/adapter/base_model.json"
test -d "$model_path"
test -x "$worker_env/bin/python"
test -x "$worker_env/bin/llamafactory-cli"
test -d "$llamafactory_root"
test "$(git -C "$llamafactory_root" rev-parse HEAD)" = "$llamafactory_ref"
test -z "$(git -C "$llamafactory_root" status --porcelain)"
test ! -e "$run_root/upstream/llmere"
test ! -e "$run_root/train"
test ! -e "$run_root/predict"
test ! -e "$run_root/score"
test ! -e "$run_root/adapter/run_metadata.json"

CUDA_VISIBLE_DEVICES="$gpu_index" "$project_root/.venv/bin/python" -u \
  scripts/prepare_llmere_causal_adapter.py \
  --project-root "$project_root" \
  --run-root "$run_root" \
  --model-path "$model_path"

CUDA_VISIBLE_DEVICES="$gpu_index" "$worker_env/bin/llamafactory-cli" train \
  "$run_root/adapter/llmere_causal_sft.yaml"
CUDA_VISIBLE_DEVICES="$gpu_index" "$worker_env/bin/llamafactory-cli" train \
  "$run_root/adapter/llmere_causal_predict.yaml"

generated="$run_root/predict/generated_predictions.jsonl"
official_predictions="$run_root/score/official_predictions.jsonl"
conversion_report="$run_root/score/conversion_report.json"
official_metrics="$run_root/score/official_metrics.json"
"$project_root/.venv/bin/python" -u scripts/convert_llmere_causal_predictions.py \
  --source data/processed/maven_ere/train.jsonl \
  --manifest data/protocols/v6/manifests/maven_ere_internal-dev.json \
  --generations "$generated" \
  --output "$official_predictions" \
  --report "$conversion_report"
"$project_root/.venv/bin/python" -u scripts/score_maven_ere_official.py \
  --gold "$run_root/upstream/llmere/data/MAVEN_ERE_split/test.jsonl" \
  --pred "$official_predictions" \
  --candidate-digest "$candidate_digest" \
  --output "$official_metrics"
"$project_root/.venv/bin/python" -u scripts/finalize_llmere_causal_adapter.py \
  --run-root "$run_root" \
  --worker-python "$worker_env/bin/python" \
  --llamafactory-root "$llamafactory_root" \
  --model-path "$model_path" \
  --model-record "$run_root/adapter/base_model.json" \
  --generated-predictions "$generated" \
  --official-predictions "$official_predictions" \
  --conversion-report "$conversion_report" \
  --official-metrics "$official_metrics"
