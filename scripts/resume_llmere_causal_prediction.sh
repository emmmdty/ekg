#!/usr/bin/env bash
# Resume E8 after its SFT adapter is complete but prediction has not started.
# Run only on gpu-4090. It refuses to overwrite generated predictions or scores.
set -euo pipefail

project_root=${1:?usage: resume_llmere_causal_prediction.sh /data/TJK/ekg GPU_INDEX}
gpu_index=${2:?usage: resume_llmere_causal_prediction.sh /data/TJK/ekg GPU_INDEX}
run_root="$project_root/runs/stages/R1/r1-v61-20260904/baselines/relation/llmere-causal-s13"
worker_env="$project_root/.venv-llmere-causal-s13"
model_path="$run_root/weights/NousResearch--Meta-Llama-3-8B"
llamafactory_root="$run_root/upstream/llama-factory"
llamafactory_ref=ca75f1edf3cb50343ed1c98605141c3e22075b5f
llmere_ref=94d4ef2781ec7e071d38ac7fd8632a8fffbda798
llmere_tree=f0fd6928ac8bad89efa76ea47b8237fb1b8fa06f
candidate_digest=313ec48e657374bc5afb7d09df9282c32f1d7a3acfdbfe1bc35435765042df3c

cd "$project_root"
test -s "$run_root/adapter/base_model.json"
test -s "$run_root/adapter/run_metadata.json"
test -s "$run_root/adapter/llmere_causal_predict.yaml"
test -s "$run_root/train/adapter/adapter_model.safetensors"
test -s "$run_root/train/adapter/train_results.json"
test -d "$model_path"
test -x "$worker_env/bin/python"
test -x "$worker_env/bin/llamafactory-cli"
test -d "$llamafactory_root"
test "$(git -C "$llamafactory_root" rev-parse HEAD)" = "$llamafactory_ref"
test -z "$(git -C "$llamafactory_root" status --porcelain)"
test -d "$run_root/upstream/llmere/.git"
test "$(git -C "$run_root/upstream/llmere" rev-parse HEAD)" = "$llmere_ref"
test "$(git -C "$run_root/upstream/llmere" rev-parse HEAD^{tree})" = "$llmere_tree"
test ! -e "$run_root/predict"
test ! -e "$run_root/score"

"$project_root/.venv/bin/python" - "$run_root" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

run_root = Path(sys.argv[1])
metadata = json.loads((run_root / "adapter/run_metadata.json").read_text(encoding="utf-8"))
if metadata.get("status") != "prepared":
    raise SystemExit(f"expected prepared metadata, got {metadata.get('status')!r}")
upstream = metadata.get("upstream", {})
converter = run_root / "upstream/llmere/data_handle_MAVEN_ERE/convert_causal.py"
actual = hashlib.sha256(converter.read_bytes()).hexdigest()
if actual != upstream.get("causal_converter_sha256"):
    raise SystemExit("LLMERE causal converter hash no longer matches prepared metadata")
results = json.loads((run_root / "train/adapter/train_results.json").read_text(encoding="utf-8"))
if results.get("epoch") != 3.0 or results.get("train_runtime", 0) <= 0:
    raise SystemExit(f"SFT completion record is invalid: {results}")
PY

"$worker_env/bin/python" -m pip install \
  jieba==0.42.1 \
  nltk==3.9.1 \
  rouge-chinese==1.0.3
"$worker_env/bin/python" - <<'PY'
import jieba
import nltk
import rouge_chinese
from importlib.metadata import version

assert version("jieba") == "0.42.1", jieba.__version__
assert version("nltk") == "3.9.1", nltk.__version__
assert version("rouge-chinese") == "1.0.3", rouge_chinese
PY

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
