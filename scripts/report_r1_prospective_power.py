#!/usr/bin/env python
"""Prospective document-cluster power analysis for the R1 design gate.

The injected systems only correct errors made by a frozen anchor. They are not
candidate method results. This lets us estimate the smallest detectable effect
before any proposed model is trained, while preserving the paired document unit.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from collections.abc import Callable
from pathlib import Path

import numpy as np

from ekg.core.stage_bundle import sha256_file
from ekg.relations.data.maven_fact import load_maven_fact
from ekg.relations.maven_ere_official import gold_to_official_prediction

FACT_CLASSES = ("CT+", "PS+", "CT-", "PS-", "Uu")
ScoreFunction = Callable[[np.ndarray], np.ndarray]


def _load_jsonl_by_id(path: Path) -> dict[str, dict]:
    records: dict[str, dict] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line:
            continue
        record = json.loads(line)
        doc_id = record.get("id")
        if not isinstance(doc_id, str) or not doc_id or doc_id in records:
            raise ValueError(f"invalid/duplicate document ID at {path}:{line_number}")
        records[doc_id] = record
    return records


def _muc_counts(key: list[set[str]], response: list[set[str]]) -> tuple[int, int]:
    mention_to_cluster = {
        mention: frozenset(cluster) for cluster in response for mention in cluster
    }
    numerator = denominator = 0
    for cluster in key:
        partitions = {
            mention_to_cluster.get(mention, frozenset((mention,))) for mention in cluster
        }
        numerator += len(cluster) - len(partitions)
        denominator += len(cluster) - 1
    return numerator, denominator


def _coref_document_counts(gold_record: dict, prediction: dict) -> np.ndarray:
    gold = [
        {mention["id"] for mention in event["mention"]}
        for event in gold_record.get("events", [])
    ]
    mention_ids = {mention for cluster in gold for mention in cluster}
    predicted: list[set[str]] = []
    assigned: set[str] = set()
    for raw_cluster in prediction.get("coreference", []):
        cluster = {
            mention
            for mention in raw_cluster
            if mention in mention_ids and mention not in assigned
        }
        if cluster:
            predicted.append(cluster)
            assigned.update(cluster)
    predicted.extend([{mention}] for mention in sorted(mention_ids - assigned))
    recall_num, recall_den = _muc_counts(gold, predicted)
    precision_num, precision_den = _muc_counts(predicted, gold)
    return np.array([precision_num, precision_den, recall_num, recall_den], dtype=float)


def _muc_score(counts: np.ndarray) -> np.ndarray:
    counts = np.atleast_2d(counts)
    precision = np.divide(
        counts[:, 0],
        counts[:, 1],
        out=np.zeros(len(counts)),
        where=counts[:, 1] != 0,
    )
    recall = np.divide(
        counts[:, 2],
        counts[:, 3],
        out=np.zeros(len(counts)),
        where=counts[:, 3] != 0,
    )
    return np.divide(
        2 * precision * recall,
        precision + recall,
        out=np.zeros(len(counts)),
        where=(precision + recall) != 0,
    )


def _macro_f1(confusions: np.ndarray) -> np.ndarray:
    confusions = np.atleast_2d(confusions).reshape(-1, len(FACT_CLASSES), len(FACT_CLASSES))
    true_positive = np.diagonal(confusions, axis1=1, axis2=2)
    predicted = confusions.sum(axis=1)
    gold = confusions.sum(axis=2)
    precision = np.divide(
        true_positive,
        predicted,
        out=np.zeros_like(true_positive),
        where=predicted != 0,
    )
    recall = np.divide(
        true_positive,
        gold,
        out=np.zeros_like(true_positive),
        where=gold != 0,
    )
    f1 = np.divide(
        2 * precision * recall,
        precision + recall,
        out=np.zeros_like(precision),
        where=(precision + recall) != 0,
    )
    return f1.mean(axis=1)


def _micro_f1(counts: np.ndarray) -> np.ndarray:
    counts = np.atleast_2d(counts)
    true_positive, false_positive, false_negative = counts.T
    denominator = 2 * true_positive + false_positive + false_negative
    return np.divide(
        2 * true_positive,
        denominator,
        out=np.zeros(len(counts)),
        where=denominator != 0,
    )


def _bootstrap_document_counts(
    n_documents: int, *, resamples: int, rng: np.random.Generator
) -> np.ndarray:
    samples = rng.integers(0, n_documents, size=(resamples, n_documents))
    counts = np.zeros((resamples, n_documents), dtype=np.int16)
    rows = np.repeat(np.arange(resamples), n_documents)
    np.add.at(counts, (rows, samples.ravel()), 1)
    return counts


def _power_curve(
    base_by_doc: np.ndarray,
    correction_docs: np.ndarray,
    correction_deltas: np.ndarray,
    *,
    steps: tuple[int, ...],
    score: ScoreFunction,
    bootstrap_counts: np.ndarray,
    trials: int,
    rng: np.random.Generator,
) -> list[dict]:
    base_total = base_by_doc.sum(axis=0)
    base_point = float(score(base_total)[0])
    base_bootstrap = bootstrap_counts @ base_by_doc
    base_bootstrap_scores = score(base_bootstrap)
    rows: list[dict] = []
    for requested in steps:
        if requested > len(correction_docs):
            continue
        detected = 0
        effects: list[float] = []
        lower_bounds: list[float] = []
        for _ in range(trials):
            selected = rng.choice(len(correction_docs), size=requested, replace=False)
            docs = correction_docs[selected]
            deltas = correction_deltas[selected]
            injected_total = base_total + deltas.sum(axis=0)
            effects.append(float(score(injected_total)[0]) - base_point)
            boot_delta_counts = np.einsum(
                "bk,kf->bf", bootstrap_counts[:, docs], deltas, optimize=True
            )
            bootstrap_effects = score(base_bootstrap + boot_delta_counts) - base_bootstrap_scores
            lower = float(np.quantile(bootstrap_effects, 0.025))
            lower_bounds.append(lower)
            detected += lower > 0
        rows.append(
            {
                "corrections": requested,
                "effect_median": float(np.median(effects)),
                "effect_min": min(effects),
                "effect_max": max(effects),
                "ci_low_median": float(np.median(lower_bounds)),
                "power": detected / trials,
            }
        )
    return rows


def _first_powered_row(rows: list[dict], target: float = 0.8) -> dict | None:
    return next((row for row in rows if row["power"] >= target), None)


def analyze_identity(
    gold_path: Path,
    prediction_path: Path,
    *,
    bootstrap_counts: np.ndarray,
    trials: int,
    rng: np.random.Generator,
) -> dict:
    gold = _load_jsonl_by_id(gold_path)
    predictions = _load_jsonl_by_id(prediction_path)
    if set(gold) != set(predictions):
        raise ValueError("identity gold/prediction document sets differ")
    doc_ids = sorted(gold)
    base_by_doc = np.stack(
        [_coref_document_counts(gold[doc_id], predictions[doc_id]) for doc_id in doc_ids]
    )
    perfect_by_doc = np.stack(
        [
            _coref_document_counts(
                gold[doc_id],
                {
                    "coreference": [
                        [mention["id"] for mention in event["mention"]]
                        for event in gold[doc_id].get("events", [])
                    ]
                },
            )
            for doc_id in doc_ids
        ]
    )
    deltas = perfect_by_doc - base_by_doc
    correction_docs = np.flatnonzero(np.any(deltas != 0, axis=1))
    curve = _power_curve(
        base_by_doc,
        correction_docs,
        deltas[correction_docs],
        steps=(1, 2, 3, 5, 8, 12, 16, 24, 32, 48, 64),
        score=_muc_score,
        bootstrap_counts=bootstrap_counts,
        trials=trials,
        rng=rng,
    )
    mde = _first_powered_row(curve)
    return {
        "status": "pass" if mde and mde["effect_median"] <= 0.01 else "underpowered",
        "evaluation_unit": "document cluster",
        "primary_metric": "official MUC F1",
        "minimum_meaningful_effect": 0.01,
        "anchor_point": float(_muc_score(base_by_doc.sum(axis=0))[0]),
        "documents": len(doc_ids),
        "correctable_documents": len(correction_docs),
        "power_curve": curve,
        "mde_at_80_percent_power": mde,
        "legal_strengthening": (
            "Pre-freeze repeated train/internal-dev document splits and aggregate matched-seed "
            "paired estimates; keep final-valid sealed."
        ),
    }


def _causal_edges(record: dict) -> set[tuple[str, str, str]]:
    return {
        (str(subtype), str(head), str(tail))
        for subtype, pairs in record.get("causal_relations", {}).items()
        for head, tail in pairs
    }


def _relation_inputs(
    gold_path: Path, prediction_path: Path
) -> tuple[np.ndarray, np.ndarray, np.ndarray, int]:
    gold_records = _load_jsonl_by_id(gold_path)
    predictions = _load_jsonl_by_id(prediction_path)
    if set(gold_records) != set(predictions):
        raise ValueError("relation gold/prediction document sets differ")

    base_by_doc: list[np.ndarray] = []
    correction_docs: list[int] = []
    correction_deltas: list[np.ndarray] = []
    cross_sentence_false_positives = 0
    for doc_index, doc_id in enumerate(sorted(gold_records)):
        raw_gold = gold_records[doc_id]
        gold = gold_to_official_prediction(raw_gold)
        prediction = predictions[doc_id]
        gold_edges = _causal_edges(gold)
        predicted_edges = _causal_edges(prediction)
        true_positive = len(gold_edges & predicted_edges)
        false_positive_edges = predicted_edges - gold_edges
        false_negative = len(gold_edges - predicted_edges)
        base_by_doc.append(
            np.array([true_positive, len(false_positive_edges), false_negative], dtype=float)
        )

        mention_sentences = {
            str(mention["id"]): int(mention["sent_id"])
            for event in raw_gold.get("events", [])
            for mention in event.get("mention", [])
        }
        cross_sentence = sum(
            mention_sentences[head] != mention_sentences[tail]
            for _, head, tail in false_positive_edges
        )
        if cross_sentence:
            correction_docs.append(doc_index)
            correction_deltas.append(np.array([0.0, -cross_sentence, 0.0]))
            cross_sentence_false_positives += cross_sentence

    return (
        np.stack(base_by_doc),
        np.asarray(correction_docs, dtype=int),
        np.stack(correction_deltas),
        cross_sentence_false_positives,
    )


def analyze_relation(
    gold_path: Path,
    prediction_path: Path,
    *,
    bootstrap_counts: np.ndarray,
    trials: int,
    rng: np.random.Generator,
) -> dict:
    base_by_doc, correction_docs, correction_deltas, false_positives = _relation_inputs(
        gold_path, prediction_path
    )
    steps = tuple(
        step
        for step in (1, 2, 3, 5, 8, 12, 16, 24, 32, 48, 64, 96, 128, 192, 256)
        if step <= len(correction_docs)
    )
    curve = _power_curve(
        base_by_doc,
        correction_docs,
        correction_deltas,
        steps=steps,
        score=_micro_f1,
        bootstrap_counts=bootstrap_counts,
        trials=trials,
        rng=rng,
    )
    mde = _first_powered_row(curve)
    return {
        "status": "pass" if mde and mde["effect_median"] <= 0.01 else "underpowered",
        "evaluation_unit": "document cluster",
        "primary_metric": "official causal micro-F1",
        "minimum_meaningful_effect": 0.01,
        "anchor_point": float(_micro_f1(base_by_doc.sum(axis=0))[0]),
        "documents": len(base_by_doc),
        "correctable_documents": len(correction_docs),
        "correctable_cross_sentence_false_positives": false_positives,
        "injected_treatment": (
            "remove every cross-sentence causal false positive in a sampled anchor-error "
            "document; do not alter true positives, false negatives, candidates, or labels"
        ),
        "power_curve": curve,
        "mde_at_80_percent_power": mde,
        "legal_strengthening": (
            "Pre-freeze repeated train/internal-dev document splits and aggregate matched-seed "
            "paired estimates; keep final-valid sealed."
        ),
    }


def _factuality_inputs(
    gold_path: Path, manifest_path: Path, prediction_path: Path
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, int]]:
    predicted = json.loads(prediction_path.read_text(encoding="utf-8"))
    class_id = {label: index for index, label in enumerate(FACT_CLASSES)}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_ids = manifest.get("doc_ids")
    if not isinstance(expected_ids, list) or len(expected_ids) != manifest.get("doc_count"):
        raise ValueError(f"invalid factuality manifest: {manifest_path}")
    all_documents = {document.doc_id: document for document in load_maven_fact(gold_path)}
    missing = [doc_id for doc_id in expected_ids if doc_id not in all_documents]
    if missing:
        raise ValueError(f"factuality manifest has {len(missing)} unknown document IDs")
    documents = [all_documents[doc_id] for doc_id in expected_ids]
    doc_index = {document.doc_id: index for index, document in enumerate(documents)}
    by_doc = np.zeros((len(documents), len(FACT_CLASSES), len(FACT_CLASSES)), dtype=float)
    correction_docs: list[int] = []
    correction_deltas: list[np.ndarray] = []
    support: Counter[str] = Counter()
    for document in documents:
        for mention in document.mentions:
            key = mention.mention_id
            if key not in predicted:
                key = f"{document.doc_id}::{mention.mention_id}"
            if key not in predicted:
                raise ValueError(
                    "missing factuality prediction: "
                    f"{document.doc_id}::{mention.mention_id}"
                )
            gold_label = mention.factuality
            pred_label = predicted[key]
            if gold_label not in class_id or pred_label not in class_id:
                raise ValueError(f"unknown factuality label at {key}: {gold_label}/{pred_label}")
            gold_id, pred_id = class_id[gold_label], class_id[pred_label]
            by_doc[doc_index[document.doc_id], gold_id, pred_id] += 1
            support[gold_label] += 1
            if gold_label in {"PS-", "Uu"} and gold_label != pred_label:
                delta = np.zeros((len(FACT_CLASSES), len(FACT_CLASSES)), dtype=float)
                delta[gold_id, pred_id] -= 1
                delta[gold_id, gold_id] += 1
                correction_docs.append(doc_index[document.doc_id])
                correction_deltas.append(delta.ravel())
    return (
        by_doc.reshape(len(documents), -1),
        np.asarray(correction_docs, dtype=int),
        np.stack(correction_deltas),
        dict(sorted(support.items())),
    )


def analyze_factuality(
    gold_path: Path,
    manifest_path: Path,
    prediction_path: Path,
    *,
    bootstrap_counts: np.ndarray,
    trials: int,
    rng: np.random.Generator,
) -> dict:
    base_by_doc, correction_docs, correction_deltas, support = _factuality_inputs(
        gold_path, manifest_path, prediction_path
    )
    steps = tuple(
        step
        for step in (1, 2, 3, 5, 8, 12, 16, 20, 24, 28, 32)
        if step <= len(correction_docs)
    )
    curve = _power_curve(
        base_by_doc,
        correction_docs,
        correction_deltas,
        steps=steps,
        score=_macro_f1,
        bootstrap_counts=bootstrap_counts,
        trials=trials,
        rng=rng,
    )
    mde = _first_powered_row(curve)
    return {
        "status": "pass" if mde and mde["effect_median"] <= 0.03 else "underpowered",
        "evaluation_unit": "document cluster",
        "primary_metric": "five-class macro-F1",
        "minimum_meaningful_effect": 0.03,
        "anchor_point": float(_macro_f1(base_by_doc.sum(axis=0))[0]),
        "documents": len(base_by_doc),
        "support": support,
        "correctable_rare_mentions": len(correction_docs),
        "power_curve": curve,
        "mde_at_80_percent_power": mde,
        "legal_strengthening": (
            "Pre-freeze stratified repeated splits or cross-validation that preserves PS-/Uu "
            "support. Report FactBank/UW only as separate external-validity tables because their "
            "label spaces are not the MAVEN-FACT five-class protocol."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--identity-gold", required=True, type=Path)
    parser.add_argument("--identity-predictions", required=True, type=Path)
    parser.add_argument("--identity-metrics", required=True, type=Path)
    parser.add_argument("--relation-gold", required=True, type=Path)
    parser.add_argument("--relation-predictions", required=True, type=Path)
    parser.add_argument("--relation-metrics", required=True, type=Path)
    parser.add_argument("--factuality-gold", required=True, type=Path)
    parser.add_argument("--factuality-manifest", required=True, type=Path)
    parser.add_argument("--factuality-predictions", required=True, type=Path)
    parser.add_argument("--factuality-report", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--resamples", type=int, default=2000)
    parser.add_argument("--trials", type=int, default=200)
    parser.add_argument("--seed", type=int, default=260904)
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    identity_docs = len(_load_jsonl_by_id(args.identity_gold))
    factuality_manifest = json.loads(args.factuality_manifest.read_text(encoding="utf-8"))
    factuality_docs = factuality_manifest.get("doc_count")
    relation_docs = len(_load_jsonl_by_id(args.relation_gold))
    if identity_docs != factuality_docs or identity_docs != relation_docs:
        raise SystemExit(
            "identity/relation/factuality document counts differ: "
            f"{identity_docs}/{relation_docs}/{factuality_docs}"
        )
    bootstrap_counts = _bootstrap_document_counts(
        identity_docs, resamples=args.resamples, rng=rng
    )
    report = {
        "schema_version": "ekg.r1_prospective_power.v1",
        "status": "partial",
        "config": {
            "rng_seed": args.seed,
            "simulation_trials": args.trials,
            "bootstrap_resamples": args.resamples,
            "power_target": 0.8,
            "confidence_interval": 0.95,
            "final_valid_accessed": False,
        },
        "anchors": {
            "identity_gold": {
                "path": str(args.identity_gold),
                "sha256": sha256_file(args.identity_gold),
            },
            "identity_predictions": {
                "path": str(args.identity_predictions),
                "sha256": sha256_file(args.identity_predictions),
            },
            "identity_metrics": {
                "path": str(args.identity_metrics),
                "sha256": sha256_file(args.identity_metrics),
            },
            "relation_gold": {
                "path": str(args.relation_gold),
                "sha256": sha256_file(args.relation_gold),
            },
            "relation_predictions": {
                "path": str(args.relation_predictions),
                "sha256": sha256_file(args.relation_predictions),
            },
            "relation_metrics": {
                "path": str(args.relation_metrics),
                "sha256": sha256_file(args.relation_metrics),
            },
            "factuality_gold": {
                "path": str(args.factuality_gold),
                "sha256": sha256_file(args.factuality_gold),
            },
            "factuality_manifest": {
                "path": str(args.factuality_manifest),
                "sha256": sha256_file(args.factuality_manifest),
            },
            "factuality_predictions": {
                "path": str(args.factuality_predictions),
                "sha256": sha256_file(args.factuality_predictions),
            },
            "factuality_report": {
                "path": str(args.factuality_report),
                "sha256": sha256_file(args.factuality_report),
            },
        },
        "identity": analyze_identity(
            args.identity_gold,
            args.identity_predictions,
            bootstrap_counts=bootstrap_counts,
            trials=args.trials,
            rng=rng,
        ),
        "relation": analyze_relation(
            args.relation_gold,
            args.relation_predictions,
            bootstrap_counts=bootstrap_counts,
            trials=args.trials,
            rng=rng,
        ),
        "factuality": analyze_factuality(
            args.factuality_gold,
            args.factuality_manifest,
            args.factuality_predictions,
            bootstrap_counts=bootstrap_counts,
            trials=args.trials,
            rng=rng,
        ),
    }
    statuses = [report[name]["status"] for name in ("identity", "relation", "factuality")]
    report["status"] = "pass" if statuses == ["pass", "pass", "pass"] else "blocked"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[r1-power] {report['status']}: wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
