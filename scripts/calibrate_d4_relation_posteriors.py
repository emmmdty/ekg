#!/usr/bin/env python
"""Fit selection-only scalar temperature and transform one D4 evaluation fold."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

import numpy as np

from ekg.core.protocol import load_manifest_ids
from ekg.core.schema import RelationType
from ekg.core.stage_bundle import sha256_file
from ekg.relations.calibration import (
    fit_temperature,
    multiclass_brier,
    multiclass_nll,
    scale_probability_tuple,
    temperature_scale,
)
from ekg.relations.data.maven_ere import load_maven_ere
from ekg.relations.pairs import candidate_pairs, gold_pair_labels

CLASSES = ("NONE", "CAUSE", "PRECONDITION")
PROBABILITY_FIELDS = ("p_none", "p_cause", "p_precondition")
ROW_FIELDS = {
    "doc_id",
    "head_mention_id",
    "tail_mention_id",
    *PROBABILITY_FIELDS,
}
PAPER_URL = "https://proceedings.mlr.press/v70/guo17a.html"
OFFICIAL_CODE_URL = (
    "https://github.com/gpleiss/temperature_scaling/blob/master/temperature_scaling.py"
)


def _load_object(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _write_object_atomically(payload: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        temporary = Path(handle.name)
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    try:
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _probabilities(row: dict, *, location: str) -> tuple[float, float, float]:
    if set(row) != ROW_FIELDS:
        raise ValueError(f"{location}: posterior row fields drifted")
    values: list[float] = []
    for field in PROBABILITY_FIELDS:
        raw = row[field]
        if not isinstance(raw, (int, float)) or isinstance(raw, bool):
            raise ValueError(f"{location}: {field} is not numeric")
        values.append(float(raw))
    result = tuple(values)
    try:
        scale_probability_tuple(result, 1.0)
    except ValueError as exc:
        raise ValueError(f"{location}: invalid posterior probabilities: {exc}") from exc
    return result


def _rows(path: Path):
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                raise ValueError(f"{path}:{line_number}: blank posterior row")
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{line_number}: row is not an object")
            yield line_number, row


def _validate_posterior_metadata(
    *,
    metadata_path: Path,
    posterior_path: Path,
    source_path: Path,
    manifest_path: Path | None,
) -> dict:
    metadata = _load_object(metadata_path)
    if metadata.get("schema_version") != "ekg.relation_causal_posteriors.v1":
        raise ValueError(f"{metadata_path}: posterior schema drifted")
    if metadata.get("class_order") != list(CLASSES):
        raise ValueError(f"{metadata_path}: class order drifted")
    if metadata.get("gold_fields_present") is not False:
        raise ValueError(f"{metadata_path}: posterior reports gold fields")
    if metadata.get("output_sha256") != sha256_file(posterior_path):
        raise ValueError(f"{metadata_path}: posterior hash mismatch")
    inputs = metadata.get("inputs", {})
    if inputs.get("data", {}).get("sha256") != sha256_file(source_path):
        raise ValueError(f"{metadata_path}: source hash mismatch")
    if manifest_path is not None:
        if inputs.get("manifest", {}).get("sha256") != sha256_file(manifest_path):
            raise ValueError(f"{metadata_path}: manifest hash mismatch")
    return metadata


def _load_selection(
    *,
    source_path: Path,
    manifest_path: Path,
    posterior_path: Path,
    expected_documents: int,
    expected_pairs: int,
) -> tuple[np.ndarray, np.ndarray]:
    documents = list(load_maven_ere(source_path))
    docs = {doc.doc_id: doc for doc in documents}
    if len(docs) != len(documents):
        raise ValueError("source contains duplicate document IDs")
    document_ids = load_manifest_ids(manifest_path)
    if len(document_ids) != expected_documents:
        raise ValueError("selection document count mismatch")
    probabilities = np.empty((expected_pairs, len(CLASSES)), dtype=np.float64)
    labels = np.empty(expected_pairs, dtype=np.int64)
    posterior_rows = iter(_rows(posterior_path))
    index = 0
    for doc_id in document_ids:
        if doc_id not in docs:
            raise ValueError(f"selection document absent from source: {doc_id}")
        doc = docs[doc_id]
        gold = gold_pair_labels(
            doc,
            family=RelationType.CAUSAL,
            expand_event_relations=True,
        )
        for head, tail in candidate_pairs(doc):
            if index >= expected_pairs:
                raise ValueError("selection posterior has more pairs than expected")
            try:
                line_number, row = next(posterior_rows)
            except StopIteration as exc:
                raise ValueError("selection posterior ended early") from exc
            location = f"{posterior_path}:{line_number}"
            observed = (
                row.get("doc_id"),
                row.get("head_mention_id"),
                row.get("tail_mention_id"),
            )
            if observed != (doc_id, head, tail):
                raise ValueError(f"{location}: selection candidate/order mismatch")
            label = gold.get((head, tail), "NONE")
            if label not in CLASSES:
                raise ValueError(f"{location}: unknown causal label {label}")
            probabilities[index] = _probabilities(row, location=location)
            labels[index] = CLASSES.index(label)
            index += 1
    try:
        line_number, _ = next(posterior_rows)
    except StopIteration:
        line_number = None
    if line_number is not None:
        raise ValueError(f"{posterior_path}:{line_number}: unexpected extra row")
    if index != expected_pairs:
        raise ValueError(f"selection pair count mismatch: expected {expected_pairs}, got {index}")
    return probabilities, labels


def _selection_metrics(probabilities: np.ndarray, labels: np.ndarray) -> dict:
    predictions = probabilities.argmax(axis=1)
    positive = labels > 0
    predicted_positive = predictions > 0
    exact = predictions == labels
    tp = int(np.sum(positive & exact))
    fp = int(np.sum(predicted_positive & ~exact))
    fn = int(np.sum(positive & ~exact))
    denominator = 2 * tp + fp + fn
    return {
        "nll": multiclass_nll(probabilities, labels),
        "multiclass_brier": multiclass_brier(probabilities, labels),
        "prediction_counts": {
            name: int(np.sum(predictions == index))
            for index, name in enumerate(CLASSES)
        },
        "causal_exact_subtype_f1": 2 * tp / denominator if denominator else 0.0,
    }


def calibrate_fold(
    *,
    fold: int,
    source_path: Path,
    selection_manifest_path: Path,
    selection_posterior_path: Path,
    selection_metadata_path: Path,
    evaluation_posterior_path: Path,
    evaluation_metadata_path: Path,
    output_path: Path,
    metadata_output_path: Path,
    expected_selection_documents: int,
    expected_selection_pairs: int,
    expected_evaluation_pairs: int,
) -> dict:
    source_path = source_path.resolve()
    selection_manifest_path = selection_manifest_path.resolve()
    selection_posterior_path = selection_posterior_path.resolve()
    selection_metadata_path = selection_metadata_path.resolve()
    evaluation_posterior_path = evaluation_posterior_path.resolve()
    evaluation_metadata_path = evaluation_metadata_path.resolve()
    output_path = output_path.resolve()
    metadata_output_path = metadata_output_path.resolve()
    if output_path.exists() or metadata_output_path.exists():
        raise FileExistsError("refusing to overwrite calibrated posterior artifacts")
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
    if evaluation_manifest_hash == sha256_file(selection_manifest_path):
        raise ValueError("selection and evaluation manifests must differ")

    selection_probabilities, labels = _load_selection(
        source_path=source_path,
        manifest_path=selection_manifest_path,
        posterior_path=selection_posterior_path,
        expected_documents=expected_selection_documents,
        expected_pairs=expected_selection_pairs,
    )
    fit = fit_temperature(selection_probabilities, labels)
    calibrated_selection = temperature_scale(
        selection_probabilities, fit.inverse_temperature
    )
    raw_metrics = _selection_metrics(selection_probabilities, labels)
    calibrated_metrics = _selection_metrics(calibrated_selection, labels)
    if raw_metrics["prediction_counts"] != calibrated_metrics["prediction_counts"]:
        raise AssertionError("temperature scaling changed selection argmax")

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
    raw_counts = np.zeros(len(CLASSES), dtype=np.int64)
    calibrated_counts = np.zeros(len(CLASSES), dtype=np.int64)
    rows = 0
    try:
        with handle:
            for line_number, row in _rows(evaluation_posterior_path):
                location = f"{evaluation_posterior_path}:{line_number}"
                raw = _probabilities(row, location=location)
                calibrated = scale_probability_tuple(raw, fit.inverse_temperature)
                raw_prediction = max(range(len(CLASSES)), key=raw.__getitem__)
                calibrated_prediction = max(
                    range(len(CLASSES)), key=calibrated.__getitem__
                )
                if raw_prediction != calibrated_prediction:
                    raise AssertionError(f"{location}: temperature changed argmax")
                raw_counts[raw_prediction] += 1
                calibrated_counts[calibrated_prediction] += 1
                transformed = dict(row)
                for field, value in zip(PROBABILITY_FIELDS, calibrated, strict=True):
                    transformed[field] = float(value)
                handle.write(
                    json.dumps(transformed, sort_keys=True, separators=(",", ":"))
                    + "\n"
                )
                rows += 1
        if rows != expected_evaluation_pairs:
            raise ValueError(
                "evaluation pair count mismatch: "
                f"expected {expected_evaluation_pairs}, got {rows}"
            )
        if not np.array_equal(raw_counts, calibrated_counts):
            raise AssertionError("temperature scaling changed evaluation predictions")
        os.replace(temporary, output_path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise

    metadata = {
        "schema_version": "ekg.d4_temperature_calibration.v1",
        "fold": fold,
        "method": {
            "name": "scalar_temperature_scaling",
            "formula": "softmax(log(p) / T)",
            "fit_objective": "unweighted multiclass NLL on selection-dev",
            "paper": PAPER_URL,
            "official_code": OFFICIAL_CODE_URL,
            "temperature": fit.temperature,
            "inverse_temperature": fit.inverse_temperature,
            "iterations": fit.iterations,
            "terminal_gradient": fit.gradient,
        },
        "selection": {
            "documents": expected_selection_documents,
            "ordered_mention_pairs": expected_selection_pairs,
            "raw_metrics": raw_metrics,
            "calibrated_metrics": calibrated_metrics,
        },
        "evaluation": {
            "ordered_mention_pairs": rows,
            "gold_accessed": False,
            "argmax_unchanged": True,
            "raw_prediction_counts": dict(zip(CLASSES, raw_counts.tolist(), strict=True)),
            "calibrated_prediction_counts": dict(
                zip(CLASSES, calibrated_counts.tolist(), strict=True)
            ),
        },
        "class_order": list(CLASSES),
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
            "checkpoint_files": selection_checkpoint.get("files"),
        },
        "output": {
            "path": str(output_path),
            "sha256": sha256_file(output_path),
        },
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
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--metadata-output", required=True, type=Path)
    parser.add_argument("--expected-selection-documents", required=True, type=int)
    parser.add_argument("--expected-selection-pairs", required=True, type=int)
    parser.add_argument("--expected-evaluation-pairs", required=True, type=int)
    args = parser.parse_args()
    metadata = calibrate_fold(
        fold=args.fold,
        source_path=args.source,
        selection_manifest_path=args.selection_manifest,
        selection_posterior_path=args.selection_posterior,
        selection_metadata_path=args.selection_metadata,
        evaluation_posterior_path=args.evaluation_posterior,
        evaluation_metadata_path=args.evaluation_metadata,
        output_path=args.output,
        metadata_output_path=args.metadata_output,
        expected_selection_documents=args.expected_selection_documents,
        expected_selection_pairs=args.expected_selection_pairs,
        expected_evaluation_pairs=args.expected_evaluation_pairs,
    )
    print(json.dumps(metadata, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
