#!/usr/bin/env python
"""Verify ten matched head runs and reuse the frozen document-paired scorer."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ekg.core.stage_bundle import sha256_file


def validate_run(root, head, fold, cv_hash, source_hash):
    metadata = json.loads((root / "run_metadata.json").read_text())
    expected = {"status": "complete", "seed": 13, "head_name": head, "pooling": "cls",
                "fold": fold, "cv_sha256": cv_hash, "source_sha256": source_hash,
                "final_valid_accessed": False, "selection_uses_evaluation": False}
    if any(metadata.get(key) != value for key, value in expected.items()):
        raise ValueError(f"run identity or selection mismatch: {root}")
    if (metadata["artifact_sha256"]["evaluation_labels.json"]
            != sha256_file(root / "evaluation_labels.json")):
        raise ValueError(f"label hash mismatch: {root}")
    return metadata


def main():
    from compare_d4_label_dumps import compare
    from launch_recovery_validation import check_dependencies, check_files

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--cv", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--runs", required=True, type=Path)
    parser.add_argument("--anchor-runs", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    repo = Path.cwd()
    plan = json.loads(args.plan.read_text())
    check_files(repo, {"seed": 13, "inputs": plan["anchor_inputs"],
                       "models": {}, "outputs": []})
    names = [f"d4-{head}-fold-{fold}" for head in ("linear", "tanh5") for fold in range(1, 6)]
    check_dependencies(repo, plan, {"depends_on": names}, sha256_file(args.plan))
    provenance = {}
    for head in ("linear", "tanh5"):
        for fold in range(1, 6):
            path = args.runs / head / f"fold-{fold}"
            validate_run(path, head, fold, sha256_file(args.cv), sha256_file(args.source))
            provenance[str(path)] = sha256_file(path / "run_metadata.json")
    common = {"repo": repo, "cv": args.cv, "source": args.source}
    report = {"diagnostic_only": True, "method_admitted": False,
              "schema_version": "ekg.recovery_head_comparison.v1",
              "run_metadata_sha256": provenance,
              "tanh5_vs_linear": compare(**common, left=(args.runs, "tanh5"),
                                         right=(args.runs, "linear")),
              "linear_vs_frozen_anchor": compare(**common, left=(args.runs, "linear"),
                                                 right=(args.anchor_runs, "cls"))}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as handle:
        json.dump(report, handle, indent=2, allow_nan=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
