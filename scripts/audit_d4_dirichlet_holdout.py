#!/usr/bin/env python
"""Audit Dirichlet calibration and cost-aware decisions on untouched D4 holdouts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
from audit_d4_class_weight_correction import (
    _git_commit,
    _load_object,
    training_class_weights,
)
from calibrate_d4_relation_posteriors import (
    CLASSES,
    _load_selection,
    _selection_metrics,
    _validate_posterior_metadata,
)

from ekg.core.protocol import load_manifest_ids
from ekg.core.stage_bundle import sha256_file
from ekg.relations.calibration import (
    cost_sensitive_predictions,
    dirichlet_calibrate,
    fit_dirichlet_calibration,
    multiclass_brier,
    multiclass_nll,
)
from ekg.relations.data.maven_ere import load_maven_ere
from ekg.relations.pairs import candidate_pairs

PAPER_URL = (
    "https://proceedings.neurips.cc/paper/2019/hash/"
    "8ca01ea920679a0fe3728441494041b9-Abstract.html"
)
OFFICIAL_CODE_URL = (
    "https://github.com/dirichletcal/dirichlet_python/tree/"
    "b03f65fc6582cad89497b977b3b33a3c4fe48e39"
)
DECISION_PAPER_URL = "https://arxiv.org/abs/2007.07314"
SPLIT_NAMESPACE = "r1-v62-c25r3"
MINIMUM_CAUSAL_F1 = 0.300
MINIMUM_BRIER_IMPROVEMENT = 0.0027


def split_document_ids(fold: int, document_ids: list[str]) -> tuple[list[str], list[str]]:
    """Create deterministic, document-disjoint calibration and gate halves."""
    if fold <= 0:
        raise ValueError("fold must be positive")
    if len(document_ids) < 2 or len(set(document_ids)) != len(document_ids):
        raise ValueError("selection document IDs must be unique and non-trivial")

    def split_key(doc_id: str) -> tuple[str, str]:
        digest = hashlib.sha256(
            f"{SPLIT_NAMESPACE}|{fold}|{doc_id}".encode()
        ).hexdigest()
        return digest, doc_id

    ordered = sorted(document_ids, key=split_key)
    boundary = len(ordered) // 2
    calibration = ordered[:boundary]
    gate = ordered[boundary:]
    if set(calibration).intersection(gate):
        raise AssertionError("calibration and gate documents overlap")
    return calibration, gate


def _id_digest(document_ids: list[str]) -> str:
    payload = "".join(f"{doc_id}\n" for doc_id in document_ids).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def selection_masks(
    *,
    fold: int,
    document_ids: list[str],
    documents: dict[str, object],
    expected_pairs: int,
) -> tuple[np.ndarray, np.ndarray, list[tuple[str, int, int]]]:
    """Expand a document split to pair masks without crossing document boundaries."""
    calibration_ids, gate_ids = split_document_ids(fold, document_ids)
    calibration_set = set(calibration_ids)
    gate_set = set(gate_ids)
    calibration_mask = np.zeros(expected_pairs, dtype=np.bool_)
    gate_mask = np.zeros(expected_pairs, dtype=np.bool_)
    gate_slices: list[tuple[str, int, int]] = []
    offset = 0
    for doc_id in document_ids:
        if doc_id not in documents:
            raise ValueError(f"selection document absent from source: {doc_id}")
        pairs = sum(1 for _ in candidate_pairs(documents[doc_id]))
        if pairs <= 0:
            raise ValueError(f"selection document has no candidate pairs: {doc_id}")
        end = offset + pairs
        if end > expected_pairs:
            raise ValueError("document pair ranges exceed the selection posterior")
        if doc_id in calibration_set:
            calibration_mask[offset:end] = True
        elif doc_id in gate_set:
            gate_mask[offset:end] = True
            gate_slices.append((doc_id, offset, end))
        else:
            raise AssertionError("selection document was not assigned to either split")
        offset = end
    if offset != expected_pairs:
        raise ValueError(
            f"selection pair range mismatch: expected {expected_pairs}, got {offset}"
        )
    if np.any(calibration_mask & gate_mask) or not np.all(calibration_mask | gate_mask):
        raise AssertionError("pair split is not disjoint and exhaustive")
    return calibration_mask, gate_mask, gate_slices


def _decision_metrics(predictions: np.ndarray, labels: np.ndarray) -> dict:
    if predictions.shape != labels.shape:
        raise ValueError("predictions and labels must have the same shape")
    positive = labels > 0
    exact = predictions == labels
    tp = int(np.sum(positive & exact))
    fp = int(np.sum((predictions > 0) & ~exact))
    fn = int(np.sum(positive & ~exact))
    denominator = 2 * tp + fp + fn
    return {
        "causal_exact_subtype_f1": 2 * tp / denominator if denominator else 0.0,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "prediction_counts": {
            name: int(np.sum(predictions == index))
            for index, name in enumerate(CLASSES)
        },
    }


def _posterior_metrics(
    probabilities: np.ndarray,
    labels: np.ndarray,
    decisions: np.ndarray,
) -> dict:
    return {
        "nll": multiclass_nll(probabilities, labels),
        "multiclass_brier": multiclass_brier(probabilities, labels),
        **_decision_metrics(decisions, labels),
    }


def audit_dirichlet_holdout(*, repo: Path, plan_path: Path) -> dict:
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

    source_documents = list(load_maven_ere(source_path))
    documents = {doc.doc_id: doc for doc in source_documents}
    if len(documents) != len(source_documents):
        raise ValueError("source contains duplicate document IDs")
    observed_documents: set[str] = set()
    input_hashes = {
        str(plan_path): sha256_file(plan_path),
        str(source_path): sha256_file(source_path),
    }
    fold_reports = []
    pooled_raw = []
    pooled_natural = []
    pooled_labels = []
    pooled_cost_decisions = []
    document_records = []
    calibration_document_total = 0
    gate_document_total = 0

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
        calibration_mask, gate_mask, gate_slices = selection_masks(
            fold=fold,
            document_ids=document_ids,
            documents=documents,
            expected_pairs=expected_pairs,
        )
        calibration_ids, gate_ids = split_document_ids(fold, document_ids)
        calibration_document_total += len(calibration_ids)
        gate_document_total += len(gate_ids)

        training_metadata_path = run_dir / "checkpoint" / "run_metadata.json"
        weights, training_counts = training_class_weights(
            _load_object(training_metadata_path)
        )
        fit = fit_dirichlet_calibration(raw[calibration_mask], labels[calibration_mask])
        gate_raw = raw[gate_mask]
        gate_labels = labels[gate_mask]
        gate_natural = dirichlet_calibrate(gate_raw, fit)
        gate_cost_decisions = cost_sensitive_predictions(gate_natural, weights)
        gate_plain_decisions = gate_natural.argmax(axis=1)

        pooled_raw.append(gate_raw)
        pooled_natural.append(gate_natural)
        pooled_labels.append(gate_labels)
        pooled_cost_decisions.append(gate_cost_decisions)

        gate_offset = 0
        for doc_id, start, end in gate_slices:
            size = end - start
            local_labels = labels[start:end]
            local_natural = gate_natural[gate_offset : gate_offset + size]
            targets = np.zeros_like(local_natural)
            targets[np.arange(size), local_labels] = 1.0
            document_records.append(
                {
                    "doc_id": doc_id,
                    "rows": size,
                    "label_counts": np.bincount(
                        local_labels, minlength=len(CLASSES)
                    ),
                    "natural_brier_sum": float(
                        np.square(local_natural - targets).sum()
                    ),
                }
            )
            gate_offset += size
        if gate_offset != gate_labels.size:
            raise AssertionError("gate document slices do not cover gate pairs")

        prevalence = np.bincount(gate_labels, minlength=len(CLASSES)) / gate_labels.size
        fold_reports.append(
            {
                "fold": fold,
                "training_counts": dict(zip(CLASSES, training_counts, strict=True)),
                "class_weights": dict(zip(CLASSES, weights.tolist(), strict=True)),
                "split": {
                    "calibration_documents": len(calibration_ids),
                    "gate_documents": len(gate_ids),
                    "calibration_document_ids_sha256": _id_digest(calibration_ids),
                    "gate_document_ids_sha256": _id_digest(gate_ids),
                    "calibration_pairs": int(calibration_mask.sum()),
                    "gate_pairs": int(gate_mask.sum()),
                },
                "fit": {
                    "iterations": fit.iterations,
                    "coefficients": fit.coefficients.tolist(),
                    "intercept": fit.intercept.tolist(),
                },
                "gate_raw": _selection_metrics(gate_raw, gate_labels),
                "gate_natural_plain_argmax": _posterior_metrics(
                    gate_natural, gate_labels, gate_plain_decisions
                ),
                "gate_natural_cost_aware": _posterior_metrics(
                    gate_natural, gate_labels, gate_cost_decisions
                ),
                "gate_prevalence_no_skill_brier": 1.0
                - float(np.square(prevalence).sum()),
            }
        )
        for path in (
            manifest_path,
            posterior_path,
            metadata_path,
            training_metadata_path,
        ):
            input_hashes[str(path)] = sha256_file(path)

    if observed_documents != set(documents):
        raise ValueError("selection folds do not cover the source exactly once")
    if calibration_document_total != 1455 or gate_document_total != 1458:
        raise ValueError("frozen document split counts drifted")

    raw = np.concatenate(pooled_raw)
    natural = np.concatenate(pooled_natural)
    labels = np.concatenate(pooled_labels)
    cost_decisions = np.concatenate(pooled_cost_decisions)
    plain_decisions = natural.argmax(axis=1)
    label_counts = np.bincount(labels, minlength=len(CLASSES))
    prevalence = label_counts / labels.size
    no_skill_brier = 1.0 - float(np.square(prevalence).sum())
    natural_brier = multiclass_brier(natural, labels)
    raw_brier = multiclass_brier(raw, labels)
    improvement_over_no_skill = no_skill_brier - natural_brier

    document_differences = []
    for record in document_records:
        rows = record["rows"]
        counts = record["label_counts"]
        no_skill_sum = rows * (1.0 + float(np.square(prevalence).sum()))
        no_skill_sum -= 2.0 * float(np.dot(counts, prevalence))
        document_differences.append(
            record["natural_brier_sum"] / rows - no_skill_sum / rows
        )
    cost_metrics = _posterior_metrics(natural, labels, cost_decisions)
    plain_metrics = _posterior_metrics(natural, labels, plain_decisions)
    pooled = {
        "rows": int(labels.size),
        "documents": gate_document_total,
        "label_counts": dict(zip(CLASSES, label_counts.tolist(), strict=True)),
        "raw": _selection_metrics(raw, labels),
        "natural_plain_argmax": plain_metrics,
        "natural_cost_aware": cost_metrics,
        "gate_prevalence_no_skill_brier": no_skill_brier,
        "natural_brier_improvement_over_no_skill": improvement_over_no_skill,
        "document_macro_natural_minus_no_skill_brier_mean": float(
            np.mean(document_differences)
        ),
        "document_macro_natural_minus_no_skill_brier_sd": float(
            np.std(document_differences, ddof=1)
        ),
    }
    gate = {
        "brier_improves_raw_pass": natural_brier < raw_brier,
        "brier_target_pass": improvement_over_no_skill
        >= MINIMUM_BRIER_IMPROVEMENT,
        "cost_aware_causal_f1_pass": cost_metrics["causal_exact_subtype_f1"]
        >= MINIMUM_CAUSAL_F1,
    }
    gate["passed"] = all(gate.values())
    return {
        "schema_version": "ekg.d4_dirichlet_holdout_audit.v1",
        "status": "accepted_for_formal_freeze"
        if gate["passed"]
        else "rejected_at_selection_gate",
        "evaluation_artifacts_accessed": False,
        "scientific_result": "selection document-holdout feasibility",
        "commit": _git_commit(repo),
        "method": {
            "name": "full_dirichlet_natural_posterior_with_cost_aware_decision",
            "posterior_formula": "softmax(W log(q) + b)",
            "decision_formula": "argmax_k w_k p_k",
            "fit_objective": "unweighted multinomial NLL",
            "penalty": None,
            "solver": "scikit-learn LogisticRegression(lbfgs)",
            "tolerance": 1e-10,
            "maximum_iterations": 1000,
            "paper": PAPER_URL,
            "official_code": OFFICIAL_CODE_URL,
            "decision_paper": DECISION_PAPER_URL,
        },
        "split": {
            "namespace": SPLIT_NAMESPACE,
            "rule": "sort SHA256(namespace|fold|doc_id); first floor(n/2) calibrates",
            "calibration_documents": calibration_document_total,
            "gate_documents": gate_document_total,
            "pair_level_overlap": 0,
        },
        "contract": {
            "minimum_gate_brier_improvement_over_no_skill": MINIMUM_BRIER_IMPROVEMENT,
            "minimum_cost_aware_causal_f1": MINIMUM_CAUSAL_F1,
            "power": {
                "test": "one-sided paired document mean, alpha=0.05",
                "reference_sd": 0.04100650041439706,
                "target_effect": MINIMUM_BRIER_IMPROVEMENT,
                "gate_documents": 1458,
                "power": 0.8076553144903685,
            },
            "single_variable_ablation": "plain argmax(p) versus argmax(w*p)",
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
    report = audit_dirichlet_holdout(repo=args.repo, plan_path=args.plan)
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
