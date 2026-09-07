#!/usr/bin/env python
"""Prepare the frozen LLMERE-causal transparent-adaptation run tree.

The official LLMERE repository supplies MAVEN-ERE data construction but no
trainer, inference entry point, model revision, or dependency manifest.  This
script makes those adaptations explicit: it checks out the frozen upstream,
uses its causal converter without edits, validates the fixed R1 population, and
writes the two LLaMA-Factory configurations that the remote launcher executes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

# The canonical URL remains the identity recorded in the run metadata.  The
# transport mirror only avoids the repeatedly observed direct-GitHub TLS reset
# on gpu-4090; the detached commit and tree checks below are authoritative.
UPSTREAM_URL = "https://github.com/HerbertHu/LLMERE.git"
UPSTREAM_TRANSPORT_URL = "https://gh-proxy.com/https://github.com/HerbertHu/LLMERE.git"
UPSTREAM_COMMIT = "94d4ef2781ec7e071d38ac7fd8632a8fffbda798"
UPSTREAM_TREE = "f0fd6928ac8bad89efa76ea47b8237fb1b8fa06f"
P1_PROTOCOL_SHA256 = "1e31a9acef39261f776f7ed4069fd73f4531e8d12b55779bfc0fbd74c67f9655"
R1_PROTOCOL_SHA256 = "199852a1f0b81e088f7568d9462d9fe226db15bdd21a78346b6d03bef80cf058"
EXPECTED_TRAIN_ROWS = 48_365
EXPECTED_DEV_ROWS = 11_149


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def command(argv: list[str], *, cwd: Path) -> None:
    print("+", " ".join(argv), flush=True)
    subprocess.run(argv, cwd=cwd, check=True)


def git_value(repository: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repository), *args], text=True, encoding="utf-8"
    ).strip()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_hash(path: Path, expected: str, *, label: str) -> None:
    actual = sha256_file(path)
    if actual != expected:
        raise SystemExit(f"{label} hash mismatch: expected {expected}, got {actual}")


def generated_config(
    *, model_path: Path, dataset_dir: Path, output_dir: Path, predict: bool
) -> dict[str, Any]:
    config: dict[str, Any] = {
        "model_name_or_path": str(model_path),
        "trust_remote_code": False,
        "stage": "sft",
        "finetuning_type": "lora",
        "lora_rank": 64,
        "lora_target": "all",
        "dataset_dir": str(dataset_dir),
        "template": "llama3",
        "cutoff_len": 2048,
        "overwrite_cache": True,
        "preprocessing_num_workers": 16,
        "dataloader_num_workers": 4,
        "output_dir": str(output_dir),
        "overwrite_output_dir": True,
        "report_to": "none",
        "bf16": True,
        "seed": 13,
        "ddp_timeout": 180000000,
        "disable_gradient_checkpointing": False,
    }
    if predict:
        config.update(
            {
                "adapter_name_or_path": str(output_dir.parent / "train/adapter"),
                "do_predict": True,
                "eval_dataset": "llmere_causal_internal_dev",
                "per_device_eval_batch_size": 1,
                "predict_with_generate": True,
                "max_new_tokens": 512,
            }
        )
    else:
        config.update(
            {
                "do_train": True,
                "dataset": "llmere_causal_train",
                "logging_steps": 10,
                "save_strategy": "epoch",
                "save_total_limit": 1,
                "save_only_model": True,
                "per_device_train_batch_size": 1,
                "gradient_accumulation_steps": 8,
                "learning_rate": 2.0e-4,
                "num_train_epochs": 3.0,
                "lr_scheduler_type": "cosine",
            }
        )
    return config


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", default=".", type=Path)
    parser.add_argument("--run-root", required=True, type=Path)
    parser.add_argument("--model-path", required=True, type=Path)
    args = parser.parse_args()

    project = args.project_root.resolve()
    run_root = args.run_root.resolve()
    model_path = args.model_path.resolve()
    source = project / "data/processed/maven_ere/train.jsonl"
    train_manifest = project / "data/protocols/v6/manifests/maven_ere_train.json"
    dev_manifest = project / "data/protocols/v6/manifests/maven_ere_internal-dev.json"
    p1_protocol = project / "runs/stages/P1/p1-v6-20260904-r15/protocol.json"
    r1_protocol = project / "runs/stages/R1/r1-v61-20260904/protocol.json"
    split_builder = project / "scripts/build_llmere_splits.py"
    for path in (source, train_manifest, dev_manifest, p1_protocol, r1_protocol, split_builder):
        if not path.is_file():
            raise SystemExit(f"required input is absent: {path}")
    ensure_hash(p1_protocol, P1_PROTOCOL_SHA256, label="P1 protocol")
    ensure_hash(r1_protocol, R1_PROTOCOL_SHA256, label="R1 protocol")
    if not model_path.is_dir():
        raise SystemExit(f"base-model directory is absent: {model_path}")

    adapter = run_root / "adapter"
    upstream = run_root / "upstream/llmere"
    if upstream.exists():
        raise SystemExit(f"refusing to overwrite an existing upstream checkout: {upstream}")
    command(["git", "clone", UPSTREAM_TRANSPORT_URL, str(upstream)], cwd=project)
    command(["git", "checkout", "--detach", UPSTREAM_COMMIT], cwd=upstream)
    commit = git_value(upstream, "rev-parse", "HEAD")
    tree = git_value(upstream, "rev-parse", "HEAD^{tree}")
    if commit != UPSTREAM_COMMIT or tree != UPSTREAM_TREE:
        raise SystemExit(f"LLMERE identity mismatch: commit={commit}, tree={tree}")

    converter = upstream / "data_handle_MAVEN_ERE/convert_causal.py"
    converter_before = sha256_file(converter)
    copied_builder = adapter / "build_llmere_splits.py"
    copied_builder.parent.mkdir(parents=True, exist_ok=True)
    copied_builder.write_bytes(split_builder.read_bytes())
    command(
        [
            sys.executable,
            str(copied_builder),
            "--source",
            str(source),
            "--train-manifest",
            str(train_manifest),
            "--internal-dev-manifest",
            str(dev_manifest),
            "--out",
            str(upstream / "data/MAVEN_ERE_split"),
        ],
        cwd=project,
    )
    command([sys.executable, str(converter)], cwd=converter.parent)
    converter_after = sha256_file(converter)
    if converter_before != converter_after:
        raise SystemExit("upstream causal converter changed during preparation")

    causal_dir = upstream / "data/converted/MAVEN_ERE/causal"
    train_rows = load_json(causal_dir / "train.json")
    dev_rows = load_json(causal_dir / "test.json")
    if len(train_rows) != EXPECTED_TRAIN_ROWS or len(dev_rows) != EXPECTED_DEV_ROWS:
        raise SystemExit(
            "LLMERE causal conversion count mismatch: "
            f"train={len(train_rows)}, internal_dev={len(dev_rows)}"
        )
    dataset_info = {
        "llmere_causal_train": {
            "file_name": "train.json",
            "formatting": "alpaca",
            "columns": {"prompt": "instruction", "query": "input", "response": "output"},
        },
        "llmere_causal_internal_dev": {
            "file_name": "test.json",
            "formatting": "alpaca",
            "columns": {"prompt": "instruction", "query": "input", "response": "output"},
        },
    }
    _write_json(causal_dir / "dataset_info.json", dataset_info)
    train_config = generated_config(
        model_path=model_path,
        dataset_dir=causal_dir,
        output_dir=run_root / "train/adapter",
        predict=False,
    )
    predict_config = generated_config(
        model_path=model_path,
        dataset_dir=causal_dir,
        output_dir=run_root / "predict",
        predict=True,
    )
    train_config_path = adapter / "llmere_causal_sft.yaml"
    predict_config_path = adapter / "llmere_causal_predict.yaml"
    _write_json(train_config_path, train_config)
    _write_json(predict_config_path, predict_config)

    metadata = {
        "schema_version": "ekg.llmere_causal_transparent_adaptation.v1",
        "task": "E8 / llmere-causal-s13",
        "status": "prepared",
        "classification": "transparent adaptation; not an official reproduction",
        "fidelity_gaps": {
            "B1": (
                "LLMERE supplies no trainer or inference code; these LLaMA-Factory "
                "configurations are project-owned adaptation code."
            ),
            "B2": (
                "Use NousResearch/Meta-Llama-3-8B ungated mirror; record a recursive "
                "weight manifest before training."
            ),
            "B3": "LLaMA-Factory is installed only in the separate llmere virtual environment.",
            "B4": (
                "Generated outputs are converted by project-owned strict code and scored "
                "only with the frozen organisers' evaluate.py."
            ),
            "partition_ceiling": (
                "LLMERE partitions each focal event into k=30 groups. Relations whose "
                "endpoints never co-occur cannot be generated, but all frozen candidates "
                "remain in the official scorer."
            ),
        },
        "upstream": {
            "url": UPSTREAM_URL,
            "transport_url": UPSTREAM_TRANSPORT_URL,
            "commit": commit,
            "tree": tree,
            "causal_converter_sha256": converter_before,
            "causal_converter_unmodified": True,
        },
        "inputs": {
            "p1_protocol_sha256": sha256_file(p1_protocol),
            "r1_protocol_sha256": sha256_file(r1_protocol),
            "source_train_sha256": sha256_file(source),
            "train_manifest_sha256": sha256_file(train_manifest),
            "internal_dev_manifest_sha256": sha256_file(dev_manifest),
        },
        "converted_data": {
            "train_rows": len(train_rows),
            "internal_dev_rows": len(dev_rows),
            "train_sha256": sha256_file(causal_dir / "train.json"),
            "internal_dev_sha256": sha256_file(causal_dir / "test.json"),
            "dataset_info_sha256": sha256_file(causal_dir / "dataset_info.json"),
        },
        "adapter_code": {
            "split_builder_sha256": sha256_file(copied_builder),
            "prediction_converter_sha256": sha256_file(
                project / "scripts/convert_llmere_causal_predictions.py"
            ),
        },
        "configs": {
            "train": {"path": str(train_config_path), "sha256": sha256_file(train_config_path)},
            "predict": {
                "path": str(predict_config_path),
                "sha256": sha256_file(predict_config_path),
            },
        },
        "adaptation_choices_not_reported_by_llmere": {
            "per_device_train_batch_size": 1,
            "gradient_accumulation_steps": 8,
            "generation_max_new_tokens": 512,
            "reason": (
                "fixed memory-safe execution choices for a single RTX 4090 24GB; they "
                "are not claimed to be official LLMERE settings."
            ),
        },
    }
    _write_json(adapter / "run_metadata.json", metadata)
    print(f"[llmere] prepared {run_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
