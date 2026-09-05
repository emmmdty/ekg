#!/usr/bin/env python
"""Train and evaluate one leakage-free R1 factuality OOF baseline fold."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from ekg.core.protocol import load_manifest_ids
from ekg.core.stage_bundle import sha256_file
from ekg.factuality.baselines import BASELINE_POOLINGS
from ekg.relations.data.maven_fact import load_maven_fact


class OOFRunError(ValueError):
    """The requested fold is not bound to the frozen CV protocol."""


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise OOFRunError(message)


def validate_fold(repo: Path, cv_path: Path, fold: int) -> dict[str, Path]:
    cv = _load(cv_path)
    _require(cv.get("schema_version") == "ekg.r1_factuality_cv.v1", "CV schema")
    _require(cv.get("config", {}).get("final_valid_accessed") is False, "CV final-valid access")
    rows = {int(row["fold"]): row for row in cv.get("folds", [])}
    _require(fold in rows, f"unknown fold {fold}")
    row = rows[fold]
    paths: dict[str, Path] = {}
    id_sets: dict[str, set[str]] = {}
    for role in ("train", "selection_dev", "evaluation"):
        entry = row[role]
        path = repo / entry["path"]
        _require(path.is_file(), f"missing {role} manifest")
        _require(sha256_file(path) == entry["sha256"], f"{role} manifest hash")
        ids = load_manifest_ids(path)
        _require(len(ids) == entry["doc_count"], f"{role} document count")
        paths[role] = path
        id_sets[role] = set(ids)
    roles = tuple(id_sets)
    for index, left in enumerate(roles):
        for right in roles[index + 1 :]:
            _require(not (id_sets[left] & id_sets[right]), f"{left}/{right} overlap")
    _require(sum(map(len, id_sets.values())) == cv["source"]["documents"], "fold cover")
    return paths


def commands(args: argparse.Namespace, manifests: dict[str, Path]) -> tuple[list[str], list[str]]:
    checkpoint = args.output / "checkpoint"
    train = [
        sys.executable,
        "-u",
        "scripts/train_factuality_detector.py",
        "--train",
        str(args.source),
        "--train-manifest",
        str(manifests["train"]),
        "--dev-manifest",
        str(manifests["selection_dev"]),
        "--detector",
        "baseline",
        "--pooling",
        args.pooling,
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
        "scripts/evaluate_factuality.py",
        "--valid",
        str(args.source),
        "--checkpoint",
        str(checkpoint),
        "--baseline-pooling",
        args.pooling,
        "--manifest",
        str(manifests["evaluation"]),
        "--max-length",
        str(args.max_length),
        "--dump-gold-labels",
        str(args.output / "evaluation_labels.json"),
        "--output",
        str(args.output / "evaluation_report.json"),
    ]
    return train, evaluate


def _git_commit(repo: Path) -> str:
    return subprocess.run(
        ("git", "rev-parse", "HEAD"),
        cwd=repo,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()


def execute(args: argparse.Namespace, manifests: dict[str, Path]) -> None:
    _require(not args.output.exists(), f"refusing to overwrite run: {args.output}")
    _require(args.source.is_file(), f"missing source: {args.source}")
    cv = _load(args.cv)
    _require(sha256_file(args.source) == cv["source"]["sha256"], "source hash")
    source_docs = {doc.doc_id: doc for doc in load_maven_fact(args.source)}
    evaluation_ids = load_manifest_ids(manifests["evaluation"])
    missing = [doc_id for doc_id in evaluation_ids if doc_id not in source_docs]
    _require(not missing, f"evaluation has {len(missing)} unknown documents")

    args.output.mkdir(parents=True)
    train, evaluate = commands(args, manifests)
    metadata = {
        "schema_version": "ekg.r1_factuality_oof_run.v1",
        "status": "incomplete",
        "fold": args.fold,
        "pooling": args.pooling,
        "seed": args.seed,
        "commit": _git_commit(args.repo),
        "cv_sha256": sha256_file(args.cv),
        "source_sha256": sha256_file(args.source),
        "manifest_sha256": {
            role: sha256_file(path) for role, path in manifests.items()
        },
        "train_argv": train,
        "evaluation_argv": evaluate,
        "selection_uses_evaluation": False,
        "final_valid_accessed": False,
    }
    metadata_path = args.output / "run_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    try:
        subprocess.run(train, cwd=args.repo, check=True)
        subprocess.run(evaluate, cwd=args.repo, check=True)
        report = _load(args.output / "evaluation_report.json")
        labels = _load(args.output / "evaluation_labels.json")
        expected_mentions = {
            mention.mention_id
            for doc_id in evaluation_ids
            for mention in source_docs[doc_id].mentions
        }
        _require(report.get("n_documents") == len(evaluation_ids), "evaluation docs")
        _require(set(labels) == expected_mentions, "evaluation mention cover")
        checkpoint = args.output / "checkpoint"
        required = (
            checkpoint / "baseline_config.json",
            checkpoint / "baseline_head.pt",
            checkpoint / "config.json",
            checkpoint / "dev_curve.json",
            checkpoint / "model.safetensors",
            args.output / "evaluation_labels.json",
            args.output / "evaluation_report.json",
        )
        for path in required:
            _require(path.is_file(), f"missing output: {path}")
        metadata["artifact_sha256"] = {
            str(path.relative_to(args.output)): sha256_file(path) for path in required
        }
        metadata["selection"] = _load(checkpoint / "dev_curve.json")["selected_epoch"]
        metadata["evaluation"] = {
            "documents": report["n_documents"],
            "mentions": report["gold_graph"]["n_mentions"],
            "macro_f1": report["gold_graph"]["macro_f1"],
            "per_class": report["gold_graph"]["per_class"],
        }
        metadata["status"] = "complete"
    except Exception:
        metadata["status"] = "failed"
        metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
        raise
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--cv", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--fold", required=True, type=int)
    parser.add_argument("--pooling", required=True, choices=BASELINE_POOLINGS)
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
    args.repo = args.repo.resolve()
    args.cv = args.cv.resolve()
    args.source = args.source.resolve()
    args.model = args.model.resolve()
    args.output = args.output.resolve()
    manifests = validate_fold(args.repo, args.cv, args.fold)
    train, evaluate = commands(args, manifests)
    if not args.execute:
        print(json.dumps({"train_argv": train, "evaluation_argv": evaluate}, indent=2))
        return 0
    execute(args, manifests)
    print(f"[r1-factuality-oof] complete: {args.pooling} fold {args.fold}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
