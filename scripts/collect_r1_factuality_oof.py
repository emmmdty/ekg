#!/usr/bin/env python
"""Validate and pool the ten R1 factuality OOF baseline runs."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from ekg.core.stage_bundle import sha256_file
from ekg.factuality.baselines import BASELINE_POOLINGS
from ekg.factuality.metrics import factuality_report
from ekg.relations.data.maven_fact import load_maven_fact


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def wait_for_runs(run_root: Path, seconds: int) -> None:
    while True:
        states: list[str] = []
        for pooling in BASELINE_POOLINGS:
            for fold in range(1, 6):
                path = run_root / pooling / f"fold-{fold}/run_metadata.json"
                states.append(_load(path).get("status", "invalid") if path.is_file() else "pending")
        if any(state == "failed" for state in states):
            raise ValueError("an OOF run failed while the collector was waiting")
        if states == ["complete"] * 10:
            return
        print(
            f"[r1-factuality-oof] waiting: complete={states.count('complete')}/10",
            flush=True,
        )
        time.sleep(seconds)


def collect(run_root: Path, cv_path: Path, source: Path, output: Path) -> dict:
    cv_sha256 = sha256_file(cv_path)
    source_sha256 = sha256_file(source)
    cv = _load(cv_path)
    if cv.get("status") != "pass" or cv.get("config", {}).get("final_valid_accessed"):
        raise ValueError("factuality CV protocol is not eligible")
    documents = list(load_maven_fact(source))
    gold = {mention.mention_id: mention.factuality for doc in documents for mention in doc.mentions}
    pooled: dict[str, dict] = {}
    for pooling in BASELINE_POOLINGS:
        labels: dict[str, str] = {}
        folds: list[dict] = []
        for fold in range(1, 6):
            fold_dir = run_root / pooling / f"fold-{fold}"
            metadata_path = fold_dir / "run_metadata.json"
            metadata = _load(metadata_path)
            if metadata.get("status") != "complete":
                raise ValueError(f"{pooling} fold {fold} is not complete")
            if metadata.get("final_valid_accessed") or metadata.get("selection_uses_evaluation"):
                raise ValueError(f"{pooling} fold {fold} violates evaluation isolation")
            if metadata.get("cv_sha256") != cv_sha256:
                raise ValueError(f"{pooling} fold {fold} CV hash drift")
            if metadata.get("source_sha256") != source_sha256:
                raise ValueError(f"{pooling} fold {fold} source hash drift")
            labels_path = fold_dir / "evaluation_labels.json"
            expected_hash = metadata.get("artifact_sha256", {}).get("evaluation_labels.json")
            if expected_hash != sha256_file(labels_path):
                raise ValueError(f"{pooling} fold {fold} labels hash drift")
            fold_labels = _load(labels_path)
            overlap = labels.keys() & fold_labels.keys()
            if overlap:
                raise ValueError(f"{pooling} fold {fold} duplicates {len(overlap)} mentions")
            labels.update(fold_labels)
            folds.append(
                {
                    "fold": fold,
                    "selected_epoch": metadata["selection"],
                    "evaluation_macro_f1": metadata["evaluation"]["macro_f1"],
                    "labels_sha256": expected_hash,
                }
            )
        missing = gold.keys() - labels.keys()
        extra = labels.keys() - gold.keys()
        if missing or extra:
            raise ValueError(
                f"{pooling} OOF mention mismatch: missing={len(missing)} extra={len(extra)}"
            )
        labels_output = output.parent / f"{pooling}_oof_labels.json"
        _write(labels_output, labels)
        pooled[pooling] = {
            "folds": folds,
            "labels": {
                "path": str(labels_output),
                "sha256": sha256_file(labels_output),
                "mentions": len(labels),
            },
            "report": factuality_report(labels, gold),
        }
    anchor = max(BASELINE_POOLINGS, key=lambda name: pooled[name]["report"]["macro_f1"])
    summary = {
        "schema_version": "ekg.r1_factuality_oof_summary.v1",
        "status": "pass",
        "run_root": str(run_root),
        "cv_sha256": cv_sha256,
        "source_sha256": source_sha256,
        "documents": len(documents),
        "mentions": len(gold),
        "final_valid_accessed": False,
        "anchor_selection_rule": "highest pooled five-class OOF macro-F1; ties follow roster",
        "anchor": anchor,
        "baselines": pooled,
    }
    _write(output, summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", required=True, type=Path)
    parser.add_argument("--cv", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--wait-seconds", type=int, default=0)
    args = parser.parse_args()
    if args.wait_seconds:
        wait_for_runs(args.run_root, args.wait_seconds)
    summary = collect(args.run_root, args.cv, args.source, args.output)
    scores = {
        name: baseline["report"]["macro_f1"]
        for name, baseline in summary["baselines"].items()
    }
    print(f"[r1-factuality-oof] PASS anchor={summary['anchor']} scores={scores}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
