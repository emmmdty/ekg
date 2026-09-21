#!/usr/bin/env python
"""Audit analytic class-weight correction on D4 selection-dev folds only."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from calibrate_d4_relation_posteriors import (
    CLASSES,
    _load_selection,
    _selection_metrics,
    _validate_posterior_metadata,
)

from ekg.core.protocol import load_manifest_ids
from ekg.core.stage_bundle import sha256_file
from ekg.relations.calibration import correct_class_weights

PAPER_URL = "https://arxiv.org/abs/2205.04613"


def _load_object(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"missing artifact: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _git_commit(repo: Path) -> str:
    return subprocess.run(
        ("git", "rev-parse", "HEAD"),
        cwd=repo,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()


def training_class_weights(run_metadata: dict) -> tuple[np.ndarray, list[int]]:
    """Reproduce the causal weights used by the frozen trainer."""
    configuration = run_metadata.get("configuration", {})
    if configuration.get("weight_alpha") != "0.5":
        raise ValueError("training weight_alpha drifted from 0.5")
    if configuration.get("neg_ratio") != "inf":
        raise ValueError("training negative sampling drifted from inf")
    if configuration.get("official_mention_expansion") is not True:
        raise ValueError("official mention expansion was not enabled")
    population = (
        run_metadata.get("protocol_binding", {})
        .get("candidate_summaries", {})
        .get("train", {})
        .get("population_counts", {})
    )
    total = population.get("ordered_mention_pairs")
    cause = population.get("positive_causal:CAUSE")
    precondition = population.get("positive_causal:PRECONDITION")
    if not all(isinstance(value, int) and value > 0 for value in (total, cause, precondition)):
        raise ValueError("training causal population counts are missing or invalid")
    none = total - cause - precondition
    if none <= 0:
        raise ValueError("training NONE count is not positive")
    counts = [none, cause, precondition]
    weights = np.asarray(
        [(total / (len(CLASSES) * count)) ** 0.5 for count in counts],
        dtype=np.float64,
    )
    return weights, counts


@dataclass
class SelectionAccumulator:
    rows: int = 0
    label_counts: np.ndarray = field(
        default_factory=lambda: np.zeros(len(CLASSES), dtype=np.int64)
    )
    raw_prediction_counts: np.ndarray = field(
        default_factory=lambda: np.zeros(len(CLASSES), dtype=np.int64)
    )
    corrected_prediction_counts: np.ndarray = field(
        default_factory=lambda: np.zeros(len(CLASSES), dtype=np.int64)
    )
    raw_tp: int = 0
    raw_fp: int = 0
    raw_fn: int = 0
    corrected_tp: int = 0
    corrected_fp: int = 0
    corrected_fn: int = 0
    raw_brier_sum: float = 0.0
    corrected_brier_sum: float = 0.0

    def add(
        self,
        raw: np.ndarray,
        corrected: np.ndarray,
        labels: np.ndarray,
    ) -> None:
        raw_predictions = raw.argmax(axis=1)
        corrected_predictions = corrected.argmax(axis=1)
        positive = labels > 0
        raw_exact = raw_predictions == labels
        corrected_exact = corrected_predictions == labels
        self.rows += labels.size
        self.label_counts += np.bincount(labels, minlength=len(CLASSES))
        self.raw_prediction_counts += np.bincount(
            raw_predictions, minlength=len(CLASSES)
        )
        self.corrected_prediction_counts += np.bincount(
            corrected_predictions, minlength=len(CLASSES)
        )
        self.raw_tp += int(np.sum(positive & raw_exact))
        self.raw_fp += int(np.sum((raw_predictions > 0) & ~raw_exact))
        self.raw_fn += int(np.sum(positive & ~raw_exact))
        self.corrected_tp += int(np.sum(positive & corrected_exact))
        self.corrected_fp += int(np.sum((corrected_predictions > 0) & ~corrected_exact))
        self.corrected_fn += int(np.sum(positive & ~corrected_exact))
        targets = np.zeros_like(raw)
        targets[np.arange(labels.size), labels] = 1.0
        self.raw_brier_sum += float(np.square(raw - targets).sum())
        self.corrected_brier_sum += float(np.square(corrected - targets).sum())

    def report(self) -> dict:
        if self.rows == 0:
            raise ValueError("cannot report an empty selection population")

        def f1(tp: int, fp: int, fn: int) -> float:
            denominator = 2 * tp + fp + fn
            return 2 * tp / denominator if denominator else 0.0

        prevalence = self.label_counts / self.rows
        return {
            "rows": self.rows,
            "label_counts": dict(zip(CLASSES, self.label_counts.tolist(), strict=True)),
            "raw_prediction_counts": dict(
                zip(CLASSES, self.raw_prediction_counts.tolist(), strict=True)
            ),
            "corrected_prediction_counts": dict(
                zip(CLASSES, self.corrected_prediction_counts.tolist(), strict=True)
            ),
            "raw_causal_f1": f1(self.raw_tp, self.raw_fp, self.raw_fn),
            "corrected_causal_f1": f1(
                self.corrected_tp, self.corrected_fp, self.corrected_fn
            ),
            "raw_multiclass_brier": self.raw_brier_sum / self.rows,
            "corrected_multiclass_brier": self.corrected_brier_sum / self.rows,
            "selection_prevalence_no_skill_brier": 1.0
            - float(np.square(prevalence).sum()),
        }


def audit_selection_correction(
    *,
    repo: Path,
    plan_path: Path,
    minimum_causal_f1: float = 0.300,
) -> dict:
    repo = repo.resolve()
    plan_path = plan_path.resolve()
    plan = _load_object(plan_path)
    if plan.get("schema_version") != "r1-v62-d4-crossfit-plan-v2":
        raise ValueError("D4 cross-fit plan schema drifted")
    source_entry = plan.get("inputs", {}).get("ere_train", {})
    source_path = (repo / source_entry.get("path", "")).resolve()
    if sha256_file(source_path) != source_entry.get("sha256"):
        raise ValueError("registered source hash mismatch")
    folds = plan.get("folds", [])
    if [row.get("fold") for row in folds] != [1, 2, 3, 4, 5]:
        raise ValueError("cross-fit plan must contain folds 1 through 5")

    accumulator = SelectionAccumulator()
    fold_reports = []
    input_hashes = {
        str(plan_path): sha256_file(plan_path),
        str(source_path): sha256_file(source_path),
    }
    observed_documents: set[str] = set()
    for row in folds:
        fold = row["fold"]
        manifest_entry = row["manifests"]["selection_dev"]
        manifest_path = (repo / manifest_entry["path"]).resolve()
        if sha256_file(manifest_path) != manifest_entry["sha256"]:
            raise ValueError(f"fold {fold}: selection manifest hash mismatch")
        document_ids = load_manifest_ids(manifest_path)
        overlap = observed_documents.intersection(document_ids)
        if overlap:
            raise ValueError(f"fold {fold}: repeated selection documents")
        observed_documents.update(document_ids)

        run_dir = plan_path.parent / "relation_crossfit" / f"fold-{fold}"
        posterior_path = run_dir / "selection_causal_posteriors.jsonl"
        metadata_path = run_dir / "selection_causal_posteriors.metadata.json"
        posterior_metadata = _validate_posterior_metadata(
            metadata_path=metadata_path,
            posterior_path=posterior_path,
            source_path=source_path,
            manifest_path=manifest_path,
        )
        expected_pairs = posterior_metadata.get("ordered_mention_pairs")
        if not isinstance(expected_pairs, int) or expected_pairs <= 0:
            raise ValueError(f"fold {fold}: invalid selection pair count")
        raw, labels = _load_selection(
            source_path=source_path,
            manifest_path=manifest_path,
            posterior_path=posterior_path,
            expected_documents=manifest_entry["documents"],
            expected_pairs=expected_pairs,
        )
        training_metadata_path = run_dir / "checkpoint" / "run_metadata.json"
        training_metadata = _load_object(training_metadata_path)
        weights, counts = training_class_weights(training_metadata)
        corrected = correct_class_weights(raw, weights)
        accumulator.add(raw, corrected, labels)
        fold_reports.append(
            {
                "fold": fold,
                "documents": len(document_ids),
                "ordered_mention_pairs": expected_pairs,
                "training_counts": dict(zip(CLASSES, counts, strict=True)),
                "class_weights": dict(zip(CLASSES, weights.tolist(), strict=True)),
                "raw_metrics": _selection_metrics(raw, labels),
                "corrected_metrics": _selection_metrics(corrected, labels),
            }
        )
        for path in (
            manifest_path,
            posterior_path,
            metadata_path,
            training_metadata_path,
        ):
            input_hashes[str(path)] = sha256_file(path)

    source_document_ids = {
        json.loads(line)["id"]
        for line in source_path.read_text(encoding="utf-8").splitlines()
        if line
    }
    if observed_documents != source_document_ids:
        raise ValueError("selection folds do not cover the source exactly once")
    pooled = accumulator.report()
    f1_pass = pooled["corrected_causal_f1"] >= minimum_causal_f1
    improves_raw = (
        pooled["corrected_multiclass_brier"] < pooled["raw_multiclass_brier"]
    )
    beats_no_skill = (
        pooled["corrected_multiclass_brier"]
        < pooled["selection_prevalence_no_skill_brier"]
    )
    gate = {
        "causal_f1_pass": f1_pass,
        "brier_improves_raw_pass": improves_raw,
        "brier_beats_no_skill_pass": beats_no_skill,
        "passed": f1_pass and improves_raw and beats_no_skill,
    }
    return {
        "schema_version": "ekg.d4_class_weight_correction_selection_audit.v1",
        "status": "accepted_for_formal_freeze" if gate["passed"] else "rejected_at_selection_gate",
        "evaluation_artifacts_accessed": False,
        "scientific_result": "selection-only feasibility",
        "commit": _git_commit(repo),
        "method": {
            "name": "analytic_class_weight_loss_correction",
            "formula": "p_k = (q_k / w_k) / sum_j(q_j / w_j)",
            "parameters_fit": 0,
            "class_weight_source": "frozen per-fold trainer counts and alpha=0.5",
            "paper": PAPER_URL,
        },
        "contract": {
            "minimum_pooled_selection_causal_f1": minimum_causal_f1,
            "corrected_brier_must_improve_raw": True,
            "corrected_brier_must_beat_selection_prevalence_no_skill": True,
        },
        "folds": fold_reports,
        "pooled": pooled,
        "gate": gate,
        "input_sha256": dict(sorted(input_hashes.items())),
        "command_argv": sys.argv,
    }


def _write_report(report: dict, output: Path) -> None:
    if output.exists():
        raise FileExistsError(f"refusing to overwrite selection audit: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=output.parent,
        prefix=f".{output.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        temporary = Path(handle.name)
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    try:
        os.replace(temporary, output)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = audit_selection_correction(repo=args.repo, plan_path=args.plan)
    _write_report(report, args.output)
    print(
        json.dumps(
            {
                "status": report["status"],
                "pooled": report["pooled"],
                "gate": report["gate"],
                "output": str(args.output),
                "output_sha256": sha256_file(args.output),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
