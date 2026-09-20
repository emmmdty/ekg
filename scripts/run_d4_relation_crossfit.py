#!/usr/bin/env python
"""Train and dump one frozen D4 leakage-free relation cross-fit fold.

The command is a no-op unless ``--execute`` is supplied.  It materializes only
the fold's train and selection-dev documents, trains the registered official
joint recipe, selects its causal-family checkpoint on selection-dev, and dumps
exhaustive causal posteriors for the untouched evaluation documents.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from ekg.core.protocol import load_manifest_ids
from ekg.core.stage_bundle import sha256_file


class D4CrossfitError(ValueError):
    """The requested run is not identical to the frozen D4 protocol."""


def _load(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise D4CrossfitError(f"{path} must contain a JSON object")
    return payload


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise D4CrossfitError(message)


def validate_fold(repo: Path, plan_path: Path, fold: int) -> dict:
    plan = _load(plan_path)
    _require(
        plan.get("schema_version") == "r1-v62-d4-crossfit-plan-v1",
        "D4 cross-fit plan schema mismatch",
    )
    _require(
        plan.get("decision", {}).get("protocol_design_closed") is True,
        "D4 cross-fit protocol is not closed",
    )
    source_entry = plan.get("inputs", {}).get("ere_train", {})
    source = (repo / source_entry.get("path", "")).resolve()
    _require(source.is_file(), "registered MAVEN-ERE source is missing")
    _require(sha256_file(source) == source_entry.get("sha256"), "source hash mismatch")
    cv_entry = plan.get("inputs", {}).get("factuality_cv", {})
    cv_path = (repo / cv_entry.get("path", "")).resolve()
    _require(cv_path.is_file(), "registered factuality CV is missing")
    _require(sha256_file(cv_path) == cv_entry.get("sha256"), "factuality CV hash mismatch")

    rows = {int(row["fold"]): row for row in plan.get("folds", [])}
    _require(fold in rows, f"unknown D4 cross-fit fold {fold}")
    row = rows[fold]
    paths: dict[str, Path] = {}
    id_sets: dict[str, set[str]] = {}
    for role in ("train", "selection_dev", "evaluation"):
        entry = row["manifests"][role]
        path = (repo / entry["path"]).resolve()
        _require(path.is_file(), f"missing {role} manifest")
        _require(sha256_file(path) == entry["sha256"], f"{role} manifest hash mismatch")
        ids = load_manifest_ids(path)
        _require(len(ids) == entry["documents"], f"{role} document count mismatch")
        paths[role] = path
        id_sets[role] = set(ids)
    roles = tuple(id_sets)
    for index, left in enumerate(roles):
        for right in roles[index + 1 :]:
            _require(not (id_sets[left] & id_sets[right]), f"{left}/{right} overlap")

    source_ids = {
        json.loads(line)["id"]
        for line in source.read_text(encoding="utf-8").splitlines()
        if line
    }
    _require(set().union(*id_sets.values()) == source_ids, "fold does not cover source")
    _require(
        row.get("seed") == 13,
        "D4 cross-fit seed drifted from the single authorized seed",
    )
    return {"plan": plan, "row": row, "source": source, "manifests": paths}


def commands(
    args: argparse.Namespace,
    fold_data: dict,
    training_source: Path,
) -> tuple[list[str], list[str]]:
    row = fold_data["row"]
    manifests = fold_data["manifests"]
    checkpoint = args.output / "checkpoint"
    causal_checkpoint = checkpoint / "by_family" / "causal"
    train = [
        sys.executable,
        "-u",
        "scripts/train_supervised_relations.py",
        "--train",
        str(training_source),
        "--train-manifest",
        str(manifests["train"]),
        "--dev-manifest",
        str(manifests["selection_dev"]),
        "--d4-crossfit-plan",
        str(args.plan),
        "--d4-crossfit-fold",
        str(args.fold),
        "--repo-root",
        str(args.repo),
        "--official-mention-expansion",
        "--families",
        "causal",
        "subevent",
        "temporal",
        "--model",
        str(args.model),
        "--epochs",
        "50",
        "--lr",
        "1e-5",
        "--head-lr",
        "1e-4",
        "--warmup-steps",
        "200",
        "--accum-steps",
        "8",
        "--neg-ratio",
        "inf",
        "--weight-alpha",
        "0.5",
        "--dev-metric",
        "macro",
        "--seed",
        str(row["seed"]),
        "--family-loss-rates",
        "temporal=2,causal=4,subevent=4",
        "--coref-aux-rate",
        "0.4",
        "--save-best-by-family",
        "--output",
        str(checkpoint),
    ]
    expected = row["expected_output"]
    dump = [
        sys.executable,
        "-u",
        "scripts/dump_relation_causal_posteriors.py",
        "--data",
        str(fold_data["source"]),
        "--manifest",
        str(manifests["evaluation"]),
        "--checkpoint",
        str(causal_checkpoint),
        "--output",
        str(args.output / "causal_posteriors.jsonl"),
        "--metadata-output",
        str(args.output / "causal_posteriors.metadata.json"),
        "--expected-documents",
        str(expected["documents"]),
        "--expected-pairs",
        str(expected["ordered_mention_pairs"]),
        "--max-length",
        "512",
    ]
    return train, dump


def _git_commit(repo: Path) -> str:
    return subprocess.run(
        ("git", "rev-parse", "HEAD"),
        cwd=repo,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()


def _tree_hashes(root: Path) -> dict[str, str]:
    _require(root.is_dir(), f"directory is missing: {root}")
    files = [path for path in sorted(root.rglob("*")) if path.is_file()]
    _require(bool(files), f"directory is empty: {root}")
    return {path.relative_to(root).as_posix(): sha256_file(path) for path in files}


def _materialize_training_source(
    source: Path,
    train_manifest: Path,
    dev_manifest: Path,
    output: Path,
) -> None:
    selected = set(load_manifest_ids(train_manifest)) | set(load_manifest_ids(dev_manifest))
    lines = []
    seen = set()
    for line in source.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        doc_id = json.loads(line)["id"]
        if doc_id in selected:
            lines.append(line)
            seen.add(doc_id)
    _require(seen == selected, "materialized source does not cover train + selection-dev")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def execute(args: argparse.Namespace, fold_data: dict) -> None:
    _require(not args.output.exists(), f"refusing to overwrite run: {args.output}")
    args.output.mkdir(parents=True)
    training_source = args.output / "training_source.jsonl"
    manifests = fold_data["manifests"]
    _materialize_training_source(
        fold_data["source"],
        manifests["train"],
        manifests["selection_dev"],
        training_source,
    )
    train, dump = commands(args, fold_data, training_source)
    metadata = {
        "schema_version": "ekg.d4_relation_crossfit_run.v1",
        "status": "incomplete",
        "fold": args.fold,
        "seed": fold_data["row"]["seed"],
        "commit": _git_commit(args.repo),
        "plan_sha256": sha256_file(args.plan),
        "source_sha256": sha256_file(fold_data["source"]),
        "training_source_sha256": sha256_file(training_source),
        "manifest_sha256": {
            role: sha256_file(path) for role, path in manifests.items()
        },
        "model_files_sha256": _tree_hashes(args.model),
        "train_argv": train,
        "dump_argv": dump,
        "selection_uses_evaluation": False,
        "final_valid_accessed": False,
    }
    metadata_path = args.output / "run_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    try:
        subprocess.run(train, cwd=args.repo, check=True)
        causal_checkpoint = args.output / "checkpoint" / "by_family" / "causal"
        selection = _load(causal_checkpoint / "selection.json")
        _require(selection.get("family") == "causal", "causal checkpoint selection drift")
        subprocess.run(dump, cwd=args.repo, check=True)
        posterior = _load(args.output / "causal_posteriors.metadata.json")
        expected = fold_data["row"]["expected_output"]
        _require(posterior.get("documents") == expected["documents"], "posterior docs")
        _require(
            posterior.get("ordered_mention_pairs") == expected["ordered_mention_pairs"],
            "posterior pairs",
        )
        required = (
            training_source,
            causal_checkpoint / "selection.json",
            causal_checkpoint / "heads.pt",
            causal_checkpoint / "model.safetensors",
            args.output / "causal_posteriors.jsonl",
            args.output / "causal_posteriors.metadata.json",
        )
        for path in required:
            _require(path.is_file(), f"missing output: {path}")
        metadata["causal_selection"] = selection
        metadata["artifacts_sha256"] = {
            str(path.relative_to(args.output)): sha256_file(path) for path in required
        }
        metadata["posterior"] = {
            "documents": posterior["documents"],
            "ordered_mention_pairs": posterior["ordered_mention_pairs"],
            "sha256": posterior["output_sha256"],
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
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--fold", required=True, type=int)
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    args.repo = args.repo.resolve()
    args.plan = args.plan.resolve()
    args.model = args.model.resolve()
    args.output = args.output.resolve()
    fold_data = validate_fold(args.repo, args.plan, args.fold)
    training_source = args.output / "training_source.jsonl"
    train, dump = commands(args, fold_data, training_source)
    if not args.execute:
        print(json.dumps({"train_argv": train, "dump_argv": dump}, indent=2))
        return 0
    execute(args, fold_data)
    print(f"[d4-relation-crossfit] complete: fold {args.fold}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
