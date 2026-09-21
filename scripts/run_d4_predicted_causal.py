#!/usr/bin/env python
"""Run one arm × one fold of the D4 v6.2 experiment, binding every input first.

Layered exactly like `run_r1_factuality_oof.py`, and it reuses that script's
fold validator so the two families cannot drift apart on split discipline: the
evaluation manifest is checked here, physically kept out of the training
command, and only handed to the separate evaluation process.

`--execute` is required to touch a GPU; without it the script prints the two
commands it would run, which is the pre-launch check the runbook asks for.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from run_r1_factuality_oof import _git_commit, validate_fold

from ekg.core.protocol import load_manifest_ids
from ekg.core.stage_bundle import sha256_file
from ekg.factuality.causal_residual import ARMS, validate_arm
from ekg.relations.data.maven_fact import load_maven_fact

CALIBRATION_SCHEMA = "ekg.d4_dirichlet_calibration.v1"


class D4RunError(ValueError):
    """The requested arm/fold is not bound to the frozen inputs."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise D4RunError(message)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sidecars(crossfit: Path, fold: int) -> dict[str, Path]:
    run_dir = crossfit / f"fold-{fold}"
    return {
        "train": run_dir / "train_dirichlet_causal_posteriors.jsonl",
        "selection_dev": run_dir / "selection_dirichlet_causal_posteriors.jsonl",
        "evaluation": run_dir / "dirichlet_causal_posteriors.jsonl",
        "calibration": run_dir / "dirichlet_calibration.metadata.json",
    }


def validate_structure(crossfit: Path, fold: int) -> dict[str, Path]:
    """Every split's edges must come from the same frozen fold map."""
    paths = sidecars(crossfit, fold)
    for name, path in paths.items():
        _require(path.is_file(), f"missing {name} sidecar: {path}")
    reference = _load(paths["calibration"])
    _require(
        reference.get("schema_version") == CALIBRATION_SCHEMA,
        "Dirichlet calibration schema drift",
    )
    _require(reference.get("fold") == fold, "calibration metadata belongs to another fold")
    _require(reference.get("gold_fields_present") is False, "sidecar reports gold fields")
    for stem, role in (("train", "train"), ("selection", "selection_dev")):
        metadata = _load(crossfit / f"fold-{fold}" / f"{stem}_dirichlet_calibration.metadata.json")
        _require(metadata.get("fold") == fold, f"{role} calibration fold drift")
        _require(metadata.get("target_role") == role, f"{role} calibration target drift")
        for key in ("coefficients", "intercept", "iterations"):
            _require(
                metadata["method"][key] == reference["method"][key],
                f"{role} sidecar came from a different Dirichlet map",
            )
        _require(
            sha256_file(paths[role]) == metadata["output"]["sha256"],
            f"{role} sidecar hash drift",
        )
    _require(
        sha256_file(paths["evaluation"]) == reference["output"]["sha256"],
        "evaluation sidecar hash drift",
    )
    return paths


def commands(
    args: argparse.Namespace, manifests: dict[str, Path], paths: dict[str, Path]
) -> tuple[list[str], list[str]]:
    checkpoint = args.output / "checkpoint"
    train = [
        sys.executable,
        "-u",
        "scripts/train_d4_predicted_causal.py",
        "--arm",
        args.arm,
        "--fold",
        str(args.fold),
        "--train",
        str(args.output / "training_source.jsonl"),
        "--train-manifest",
        str(manifests["train"]),
        "--dev-manifest",
        str(manifests["selection_dev"]),
        "--train-sidecar",
        str(paths["train"]),
        "--dev-sidecar",
        str(paths["selection_dev"]),
        "--calibration-metadata",
        str(paths["calibration"]),
        "--model",
        str(args.model),
        "--output",
        str(checkpoint),
        "--epochs",
        str(args.epochs),
        "--lr",
        str(args.lr),
        "--alpha",
        str(args.alpha),
        "--batch-size",
        str(args.batch_size),
        "--max-length",
        str(args.max_length),
        "--seed",
        str(args.seed),
    ]
    evaluate = [
        sys.executable,
        "-u",
        "scripts/evaluate_d4_predicted_causal.py",
        "--arm",
        args.arm,
        "--fold",
        str(args.fold),
        "--checkpoint",
        str(checkpoint),
        "--source",
        str(args.source),
        "--relation-source",
        str(args.relation_source),
        "--manifest",
        str(manifests["evaluation"]),
        "--sidecar",
        str(paths["evaluation"]),
        "--output",
        str(args.output / "evaluation_report.json"),
        "--labels-output",
        str(args.output / "evaluation_labels.json"),
    ]
    return train, evaluate


def execute(
    args: argparse.Namespace, manifests: dict[str, Path], paths: dict[str, Path]
) -> dict:
    _require(not args.output.exists(), f"refusing to overwrite run: {args.output}")
    _require(args.source.is_file(), f"missing source: {args.source}")
    docs = {doc.doc_id: doc for doc in load_maven_fact(args.source)}
    evaluation_ids = load_manifest_ids(manifests["evaluation"])
    unknown = [doc_id for doc_id in evaluation_ids if doc_id not in docs]
    _require(not unknown, f"evaluation has {len(unknown)} unknown documents")

    args.output.mkdir(parents=True)
    training_ids = set(load_manifest_ids(manifests["train"])) | set(
        load_manifest_ids(manifests["selection_dev"])
    )
    lines = [
        line
        for line in args.source.read_text(encoding="utf-8").splitlines()
        if line and json.loads(line).get("id") in training_ids
    ]
    _require(len(lines) == len(training_ids), "training source document cover")
    training_source = args.output / "training_source.jsonl"
    training_source.write_text("\n".join(lines) + "\n", encoding="utf-8")

    train, evaluation = commands(args, manifests, paths)
    _require(
        str(manifests["evaluation"]) not in train,
        "the evaluation manifest must not appear in the training command",
    )
    metadata = {
        "schema_version": "ekg.d4_predicted_causal_run.v1",
        "status": "incomplete",
        "arm": args.arm,
        "fold": args.fold,
        "seed": args.seed,
        "commit": _git_commit(args.repo),
        "contract": "docs/phases/PHASE_D4_predicted_causal_residual.md",
        "source_sha256": sha256_file(args.source),
        "relation_source_sha256": sha256_file(args.relation_source),
        "training_source_sha256": sha256_file(training_source),
        "manifest_sha256": {role: sha256_file(path) for role, path in manifests.items()},
        "sidecar_sha256": {role: sha256_file(path) for role, path in paths.items()},
        "train_argv": train,
        "evaluation_argv": evaluation,
        "selection_uses_evaluation": False,
        "final_valid_accessed": False,
    }
    metadata_path = args.output / "run_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    try:
        subprocess.run(train, cwd=args.repo, check=True)
        subprocess.run(evaluation, cwd=args.repo, check=True)
        report = _load(args.output / "evaluation_report.json")
        labels = _load(args.output / "evaluation_labels.json")
        expected = {
            mention.mention_id
            for doc_id in evaluation_ids
            for mention in docs[doc_id].mentions
        }
        _require(report["documents"] == len(evaluation_ids), "evaluation document cover")
        _require(set(labels) == expected, "evaluation mention cover")
        metadata["evaluation"] = {
            "documents": report["documents"],
            "mentions": report["mentions"],
            "macro_f1": report["macro_f1"],
            "per_class_f1": {name: row["f1"] for name, row in report["per_class"].items()},
            "mediators": report["mediators"],
        }
        metadata["selected_epoch"] = _load(
            args.output / "checkpoint" / "d4_predicted_causal_config.json"
        )["selected_epoch"]
        metadata["status"] = "complete"
    except Exception:
        metadata["status"] = "failed"
        metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
        raise
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--cv", required=True, type=Path)
    parser.add_argument("--crossfit", required=True, type=Path, help="relation_crossfit dir")
    parser.add_argument("--source", required=True, type=Path, help="MAVEN-FACT jsonl")
    parser.add_argument("--relation-source", required=True, type=Path, help="MAVEN-ERE jsonl")
    parser.add_argument("--arm", required=True, choices=ARMS)
    parser.add_argument("--fold", required=True, type=int)
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--alpha", type=float, default=0.5)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--max-length", type=int, default=128)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    validate_arm(args.arm)
    for name in ("repo", "cv", "crossfit", "source", "relation_source", "model", "output"):
        setattr(args, name, getattr(args, name).resolve())
    manifests = validate_fold(args.repo, args.cv, args.fold)
    paths = validate_structure(args.crossfit, args.fold)
    train, evaluation = commands(args, manifests, paths)
    if not args.execute:
        print(json.dumps({"train_argv": train, "evaluation_argv": evaluation}, indent=2))
        return 0
    metadata = execute(args, manifests, paths)
    print(f"[d4-predicted-causal] {metadata['status']}: {args.arm} fold {args.fold}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
