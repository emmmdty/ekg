#!/usr/bin/env python
"""Refit one D4 Dirichlet map on full selection and transform a target split without gold.

The default target is the fold's evaluation split — that is the C-25R3F formal
gate. The detector in C-27 also needs the *same frozen map* applied to its own
train and selection-dev documents, so ``--target-role`` names which split is
being transformed. Only ``evaluation`` may not reuse the selection manifest;
for the other two roles the in-sample optimism is the point and is disclosed in
``docs/results/PHASE_R1.md`` §25.14, not silently allowed.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

import numpy as np
from audit_d4_class_weight_correction import _load_object, training_class_weights
from audit_d4_dirichlet_holdout import (
    DECISION_PAPER_URL,
    OFFICIAL_CODE_URL,
    PAPER_URL,
    _posterior_metrics,
)
from calibrate_d4_relation_posteriors import (
    CLASSES,
    PROBABILITY_FIELDS,
    _load_selection,
    _probabilities,
    _rows,
    _selection_metrics,
    _validate_posterior_metadata,
    _write_object_atomically,
)

from ekg.core.stage_bundle import sha256_file
from ekg.relations.calibration import (
    DirichletFit,
    cost_sensitive_predictions,
    dirichlet_calibrate,
    fit_dirichlet_calibration,
)

TARGET_ROLES = ("evaluation", "train", "selection_dev")


def _flush_rows(
    *,
    rows: list[dict],
    probabilities: list[tuple[float, float, float]],
    fit: DirichletFit,
    class_weights: np.ndarray,
    handle,
    plain_counts: np.ndarray,
    cost_counts: np.ndarray,
) -> None:
    if not rows:
        return
    natural = dirichlet_calibrate(np.asarray(probabilities, dtype=np.float64), fit)
    plain_predictions = natural.argmax(axis=1)
    cost_predictions = cost_sensitive_predictions(natural, class_weights)
    plain_counts += np.bincount(plain_predictions, minlength=len(CLASSES))
    cost_counts += np.bincount(cost_predictions, minlength=len(CLASSES))
    for row, values in zip(rows, natural, strict=True):
        transformed = dict(row)
        for field, value in zip(PROBABILITY_FIELDS, values.tolist(), strict=True):
            transformed[field] = value
        handle.write(json.dumps(transformed, sort_keys=True, separators=(",", ":")) + "\n")


def formalize_fold(
    *,
    fold: int,
    source_path: Path,
    selection_manifest_path: Path,
    selection_posterior_path: Path,
    selection_metadata_path: Path,
    evaluation_posterior_path: Path,
    evaluation_metadata_path: Path,
    training_metadata_path: Path,
    output_path: Path,
    metadata_output_path: Path,
    expected_selection_documents: int,
    expected_selection_pairs: int,
    expected_evaluation_pairs: int,
    target_role: str = "evaluation",
) -> dict:
    if target_role not in TARGET_ROLES:
        raise ValueError(f"unknown target role {target_role!r}, expected {TARGET_ROLES}")
    paths = [
        source_path,
        selection_manifest_path,
        selection_posterior_path,
        selection_metadata_path,
        evaluation_posterior_path,
        evaluation_metadata_path,
        training_metadata_path,
        output_path,
        metadata_output_path,
    ]
    (
        source_path,
        selection_manifest_path,
        selection_posterior_path,
        selection_metadata_path,
        evaluation_posterior_path,
        evaluation_metadata_path,
        training_metadata_path,
        output_path,
        metadata_output_path,
    ) = [path.resolve() for path in paths]
    if output_path.exists() or metadata_output_path.exists():
        raise FileExistsError("refusing to overwrite Dirichlet posterior artifacts")

    selection_metadata = _validate_posterior_metadata(
        metadata_path=selection_metadata_path,
        posterior_path=selection_posterior_path,
        source_path=source_path,
        manifest_path=selection_manifest_path,
    )
    evaluation_metadata = _validate_posterior_metadata(
        metadata_path=evaluation_metadata_path,
        posterior_path=evaluation_posterior_path,
        source_path=source_path,
        manifest_path=None,
    )
    selection_checkpoint = selection_metadata.get("inputs", {}).get("checkpoint", {})
    evaluation_checkpoint = evaluation_metadata.get("inputs", {}).get("checkpoint", {})
    if selection_checkpoint.get("files") != evaluation_checkpoint.get("files"):
        raise ValueError("selection and evaluation posterior checkpoints differ")
    evaluation_manifest_hash = (
        evaluation_metadata.get("inputs", {}).get("manifest", {}).get("sha256")
    )
    if target_role == "evaluation" and evaluation_manifest_hash == sha256_file(
        selection_manifest_path
    ):
        raise ValueError("selection and evaluation manifests must differ")

    selection_probabilities, labels = _load_selection(
        source_path=source_path,
        manifest_path=selection_manifest_path,
        posterior_path=selection_posterior_path,
        expected_documents=expected_selection_documents,
        expected_pairs=expected_selection_pairs,
    )
    training_metadata = _load_object(training_metadata_path)
    class_weights, training_counts = training_class_weights(training_metadata)
    checkpoint_hashes = training_metadata.get("checkpoint_sha256", {})
    causal_prefix = "by_family/causal/"
    causal_checkpoint_hashes = {
        name.removeprefix(causal_prefix): digest
        for name, digest in checkpoint_hashes.items()
        if name.startswith(causal_prefix)
    }
    if causal_checkpoint_hashes != selection_checkpoint.get("files"):
        raise ValueError("training metadata and posterior checkpoints differ")
    fit = fit_dirichlet_calibration(selection_probabilities, labels)
    natural_selection = dirichlet_calibrate(selection_probabilities, fit)
    selection_cost_decisions = cost_sensitive_predictions(
        natural_selection, class_weights
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=output_path.parent,
        prefix=f".{output_path.name}.",
        suffix=".tmp",
        delete=False,
    )
    temporary = Path(handle.name)
    plain_counts = np.zeros(len(CLASSES), dtype=np.int64)
    cost_counts = np.zeros(len(CLASSES), dtype=np.int64)
    batch_rows: list[dict] = []
    batch_probabilities: list[tuple[float, float, float]] = []
    rows = 0
    try:
        with handle:
            for line_number, row in _rows(evaluation_posterior_path):
                location = f"{evaluation_posterior_path}:{line_number}"
                batch_rows.append(row)
                batch_probabilities.append(_probabilities(row, location=location))
                rows += 1
                if len(batch_rows) == 10_000:
                    _flush_rows(
                        rows=batch_rows,
                        probabilities=batch_probabilities,
                        fit=fit,
                        class_weights=class_weights,
                        handle=handle,
                        plain_counts=plain_counts,
                        cost_counts=cost_counts,
                    )
                    batch_rows.clear()
                    batch_probabilities.clear()
            _flush_rows(
                rows=batch_rows,
                probabilities=batch_probabilities,
                fit=fit,
                class_weights=class_weights,
                handle=handle,
                plain_counts=plain_counts,
                cost_counts=cost_counts,
            )
        if rows != expected_evaluation_pairs:
            raise ValueError(
                "evaluation pair count mismatch: "
                f"expected {expected_evaluation_pairs}, got {rows}"
            )
        os.replace(temporary, output_path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise

    metadata = {
        "schema_version": "ekg.d4_dirichlet_calibration.v1",
        "fold": fold,
        # Kept under "evaluation" whatever the role is: the aggregator's frozen
        # provenance check reads that key, and the formal sidecars are published.
        "target_role": target_role,
        "method": {
            "name": "full_dirichlet_natural_posterior_with_cost_aware_decision",
            "posterior_formula": "softmax(W log(q) + b)",
            "decision_formula": "argmax_k w_k p_k",
            "fit_objective": "unweighted multiclass NLL on full selection-dev",
            "penalty": None,
            "solver": "scikit-learn LogisticRegression(lbfgs)",
            "tolerance": 1e-10,
            "maximum_iterations": 1000,
            "paper": PAPER_URL,
            "official_code": OFFICIAL_CODE_URL,
            "decision_paper": DECISION_PAPER_URL,
            "coefficients": fit.coefficients.tolist(),
            "intercept": fit.intercept.tolist(),
            "iterations": fit.iterations,
        },
        "selection": {
            "documents": expected_selection_documents,
            "ordered_mention_pairs": expected_selection_pairs,
            "raw": _selection_metrics(selection_probabilities, labels),
            "natural_plain_argmax": _selection_metrics(natural_selection, labels),
            "natural_cost_aware": _posterior_metrics(
                natural_selection, labels, selection_cost_decisions
            ),
        },
        "evaluation": {
            "ordered_mention_pairs": rows,
            "gold_accessed": False,
            "plain_prediction_counts": dict(
                zip(CLASSES, plain_counts.tolist(), strict=True)
            ),
            "cost_aware_prediction_counts": dict(
                zip(CLASSES, cost_counts.tolist(), strict=True)
            ),
        },
        "class_order": list(CLASSES),
        "class_weights": dict(zip(CLASSES, class_weights.tolist(), strict=True)),
        "training_counts": dict(zip(CLASSES, training_counts, strict=True)),
        "gold_fields_present": False,
        "inputs": {
            "source": {"path": str(source_path), "sha256": sha256_file(source_path)},
            "selection_manifest": {
                "path": str(selection_manifest_path),
                "sha256": sha256_file(selection_manifest_path),
            },
            "selection_posterior": {
                "path": str(selection_posterior_path),
                "sha256": sha256_file(selection_posterior_path),
            },
            "selection_metadata": {
                "path": str(selection_metadata_path),
                "sha256": sha256_file(selection_metadata_path),
            },
            "evaluation_posterior": {
                "path": str(evaluation_posterior_path),
                "sha256": sha256_file(evaluation_posterior_path),
            },
            "evaluation_metadata": {
                "path": str(evaluation_metadata_path),
                "sha256": sha256_file(evaluation_metadata_path),
            },
            "training_metadata": {
                "path": str(training_metadata_path),
                "sha256": sha256_file(training_metadata_path),
            },
            "checkpoint_files": selection_checkpoint.get("files"),
        },
        "output": {"path": str(output_path), "sha256": sha256_file(output_path)},
    }
    _write_object_atomically(metadata, metadata_output_path)
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fold", required=True, type=int)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--selection-manifest", required=True, type=Path)
    parser.add_argument("--selection-posterior", required=True, type=Path)
    parser.add_argument("--selection-metadata", required=True, type=Path)
    parser.add_argument("--evaluation-posterior", required=True, type=Path)
    parser.add_argument("--evaluation-metadata", required=True, type=Path)
    parser.add_argument("--training-metadata", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--metadata-output", required=True, type=Path)
    parser.add_argument("--expected-selection-documents", required=True, type=int)
    parser.add_argument("--expected-selection-pairs", required=True, type=int)
    parser.add_argument("--expected-evaluation-pairs", required=True, type=int)
    parser.add_argument("--target-role", default="evaluation", choices=TARGET_ROLES)
    args = parser.parse_args()
    metadata = formalize_fold(
        fold=args.fold,
        source_path=args.source,
        selection_manifest_path=args.selection_manifest,
        selection_posterior_path=args.selection_posterior,
        selection_metadata_path=args.selection_metadata,
        evaluation_posterior_path=args.evaluation_posterior,
        evaluation_metadata_path=args.evaluation_metadata,
        training_metadata_path=args.training_metadata,
        output_path=args.output,
        metadata_output_path=args.metadata_output,
        expected_selection_documents=args.expected_selection_documents,
        expected_selection_pairs=args.expected_selection_pairs,
        expected_evaluation_pairs=args.expected_evaluation_pairs,
        target_role=args.target_role,
    )
    print(
        json.dumps(
            {
                "fold": metadata["fold"],
                "iterations": metadata["method"]["iterations"],
                "selection": metadata["selection"],
                "evaluation": metadata["evaluation"],
                "output": metadata["output"],
                "metadata_output": str(args.metadata_output),
                "metadata_sha256": sha256_file(args.metadata_output),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
