#!/usr/bin/env python
"""Run the D4 CUDA smoke on ten train-only documents and all three arms."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from ekg.core.protocol import load_manifest_ids
from ekg.core.stage_bundle import sha256_file


class SmokeError(ValueError):
    """A D4 smoke input, checkpoint or export violates the frozen contract."""


def _load(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SmokeError(f"{path} must contain a JSON object")
    return payload


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SmokeError(message)


def _write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _verify_contract(repo: Path, contract: Path) -> dict:
    payload = _load(contract)
    _require(payload.get("schema_version") == "ekg.d4_typed_cue_preflight.v1", "contract schema")
    _require(payload.get("status") == "pass", "contract status")
    _require(payload.get("seed") == 13, "contract seed")
    _require(payload.get("final_valid_accessed") is False, "contract final-valid access")
    code = payload.get("code")
    _require(isinstance(code, dict), "contract code hashes")
    for relative, expected in code.items():
        path = repo / relative
        _require(path.is_file(), f"missing bound code file: {relative}")
        _require(sha256_file(path) == expected, f"bound code hash drift: {relative}")
    return payload


def _subset_source(source: Path, ids: list[str], output: Path) -> None:
    wanted = set(ids)
    rows = [line for line in source.read_text(encoding="utf-8").splitlines() if line]
    selected = [line for line in rows if json.loads(line).get("id") in wanted]
    _require(len(selected) == len(ids), "smoke source document coverage")
    output.write_text("\n".join(selected) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> dict:
    _require(not args.output.exists(), f"refusing to overwrite smoke output: {args.output}")
    contract = _verify_contract(args.repo, args.contract)
    source = Path(contract["source"]["path"])
    cv_path = Path(contract["cv"]["path"])
    model = Path(contract["model"]["path"])
    _require(
        source.is_file() and cv_path.is_file() and model.is_dir(),
        "smoke source/CV/model missing",
    )
    cv = _load(cv_path)
    rows = {int(row["fold"]): row for row in cv.get("folds", [])}
    _require(args.fold in rows, f"unknown fold {args.fold}")
    train_manifest = args.repo / rows[args.fold]["train"]["path"]
    train_ids = load_manifest_ids(train_manifest)
    _require(args.documents >= 2, "smoke needs at least two documents")
    selected = train_ids[: args.documents]
    _require(len(selected) == args.documents, "train fold is too small for smoke")
    split = args.documents // 2
    train_ids, selection_ids = selected[:split], selected[split:]
    _require(train_ids and selection_ids, "smoke train/selection split")
    args.output.mkdir(parents=True)
    source_subset = args.output / "training_source.jsonl"
    _subset_source(source, selected, source_subset)
    outputs: dict[str, dict] = {}
    training = contract["training"]
    for arm in training["arms"]:
        arm_root = args.output / arm
        train_manifest_path = arm_root / "train.json"
        selection_manifest_path = arm_root / "selection.json"
        _write(train_manifest_path, {"doc_ids": train_ids})
        _write(selection_manifest_path, {"doc_ids": selection_ids})
        checkpoint = arm_root / "checkpoint"
        train = [
            sys.executable,
            "-u",
            "scripts/train_d4_typed_cue.py",
            "--train",
            str(source_subset),
            "--train-manifest",
            str(train_manifest_path),
            "--selection-manifest",
            str(selection_manifest_path),
            "--model",
            str(model),
            "--output",
            str(checkpoint),
            "--arm",
            arm,
            "--epochs",
            "1",
            "--lr",
            str(training["lr"]),
            "--alpha",
            str(training["alpha"]),
            "--cue-weight",
            str(training["cue_weight"]),
            "--max-length",
            str(training["max_length"]),
            "--stride",
            str(training["stride"]),
            "--seed",
            str(contract["seed"]),
            "--permutation-seed",
            str(training["permutation_seed"]),
        ]
        evaluate = [
            sys.executable,
            "-u",
            "scripts/evaluate_d4_typed_cue.py",
            "--source",
            str(source_subset),
            "--checkpoint",
            str(checkpoint),
            "--manifest",
            str(selection_manifest_path),
            "--arm",
            arm,
            "--max-length",
            str(training["max_length"]),
            "--stride",
            str(training["stride"]),
            "--permutation-seed",
            str(training["permutation_seed"]),
            "--labels-output",
            str(arm_root / "labels.json"),
            "--sidecar-output",
            str(arm_root / "typed_cues.json"),
            "--output",
            str(arm_root / "report.json"),
        ]
        subprocess.run(train, cwd=args.repo, check=True)
        subprocess.run(evaluate, cwd=args.repo, check=True)
        required = (
            checkpoint / "config.json",
            checkpoint / "model.safetensors",
            checkpoint / "typed_cue_config.json",
            checkpoint / "typed_cue_head.pt",
            checkpoint / "typed_cue_decision_head.pt",
            checkpoint / "dev_curve.json",
            arm_root / "labels.json",
            arm_root / "typed_cues.json",
            arm_root / "report.json",
        )
        for path in required:
            _require(path.is_file(), f"{arm}: missing smoke output {path.name}")
        labels = _load(arm_root / "labels.json")
        sidecar = _load(arm_root / "typed_cues.json")
        _require(set(labels) == set(sidecar), f"{arm}: labels/sidecar coverage")
        _require(all(row.get("state") in {"ok", "empty"} for row in sidecar.values()), arm)
        outputs[arm] = {
            "train_argv": train,
            "evaluate_argv": evaluate,
            "report_sha256": sha256_file(arm_root / "report.json"),
            "labels_sha256": sha256_file(arm_root / "labels.json"),
            "sidecar_sha256": sha256_file(arm_root / "typed_cues.json"),
            "mentions": len(labels),
        }
    result = {
        "schema_version": "ekg.d4_typed_cue_smoke.v1",
        "status": "pass",
        "final_valid_accessed": False,
        "fold": args.fold,
        "documents": args.documents,
        "source_subset_sha256": sha256_file(source_subset),
        "contract_sha256": sha256_file(args.contract),
        "arms": outputs,
    }
    _write(args.output / "smoke.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--fold", type=int, default=1)
    parser.add_argument("--documents", type=int, default=10)
    args = parser.parse_args()
    args.repo = args.repo.resolve()
    args.contract = args.contract.resolve()
    args.output = args.output.resolve()
    result = run(args)
    print(f"[d4-smoke] PASS fold={result['fold']} arms={len(result['arms'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
