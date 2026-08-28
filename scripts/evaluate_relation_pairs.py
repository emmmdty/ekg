#!/usr/bin/env python
"""Re-score a relation predictions dump in the pair-classification setting.

The supervised MAVEN-ERE literature (RoBERTa micro F1 51.8 etc.) reports
pair-classification numbers: gold mentions given, every candidate pair labelled.
This script projects an existing edge-list dump (`evaluate_relations.py
--dump-predictions`, format ``{"doc_id", "edges": [...]}`` per line) onto that
setting via `relations.pairs` — no model re-run needed — and reports per-family
and micro pair P/R/F1, hallucination counts, the optional windowed setting
(``--max-distance``) and the structural window recall ceilings
(``--window-ceilings``), corpus-aggregated.

    uv run python scripts/evaluate_relation_pairs.py \
        --predictions runs/relations/valid_predictions.jsonl \
        --gold-path data/processed/maven_ere/valid.jsonl \
        --candidate-digest <frozen-candidate-sha256> \
        --window-ceilings 8 16 24 \
        --output runs/relations/pair_eval.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from ekg.core.eval.relation import PRF
from ekg.core.schema import RelationEdge
from ekg.relations.data.maven_ere import load_maven_ere
from ekg.relations.maven_ere_official import candidate_population_digest, records_by_id
from ekg.relations.pairs import pair_prf, window_recall_ceiling

_FAMILY_KEYS = ("coreference", "temporal", "causal", "subevent", "micro")
_DIAG_KEYS = (
    "hallucinated_pred_pairs",
    "out_of_window_gold",
    "out_of_window_pred",
    "n_universe",
)


def _load_predictions(path: Path, min_confidence: float = 0.0) -> dict[str, list[RelationEdge]]:
    """Edges per document, optionally keeping only those at/above a confidence floor.

    The floor is the precision/recall dial of a pair classifier: plain arg-max
    over-predicts whenever training rebalanced the classes (negative downsampling
    and/or class weights), so sweeping it separates "the model cannot find them"
    from "the decision rule admits too many".
    """
    pred_by_doc: dict[str, list[RelationEdge]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        record = json.loads(line)
        doc_id = str(record["doc_id"])
        if doc_id in pred_by_doc:
            raise ValueError(f"duplicate prediction document ID: {doc_id}")
        edges = [RelationEdge.model_validate(e) for e in record.get("edges", [])]
        pred_by_doc[doc_id] = [
            e for e in edges if e.confidence >= min_confidence
        ]
    return pred_by_doc


def _aggregate(per_doc: list[dict]) -> dict:
    """Sum per-doc counts into corpus-level PRFs + diagnostics."""
    totals = {key: {"tp": 0, "n_pred": 0, "n_gold": 0} for key in _FAMILY_KEYS}
    diagnostics = dict.fromkeys(_DIAG_KEYS, 0)
    for result in per_doc:
        for key in _FAMILY_KEYS:
            for counter in ("tp", "n_pred", "n_gold"):
                totals[key][counter] += int(result[key][counter])
        for key in _DIAG_KEYS:
            diagnostics[key] += int(result["diagnostics"][key])
    report: dict = {
        key: PRF.from_counts(c["tp"], c["n_pred"], c["n_gold"]) for key, c in totals.items()
    }
    report["diagnostics"] = diagnostics
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--predictions", required=True, type=Path, help="edge-list dump JSONL")
    parser.add_argument("--gold-path", required=True, type=Path, help="MAVEN-ERE style JSONL")
    parser.add_argument(
        "--max-distance", type=int, help="windowed universe (textual mention distance)"
    )
    parser.add_argument(
        "--window-ceilings", type=int, nargs="+",
        help="report the structural recall ceiling for these window sizes",
    )
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.0,
        help="drop predicted edges below this confidence (precision/recall dial)",
    )
    parser.add_argument(
        "--candidate-digest",
        required=True,
        help="expected frozen all-pairs candidate SHA-256",
    )
    parser.add_argument("--output", type=Path, help="write the JSON report here")
    args = parser.parse_args()

    raw_gold = [
        json.loads(line)
        for line in args.gold_path.read_text(encoding="utf-8").splitlines()
        if line
    ]
    gold_by_id = records_by_id(raw_gold, source=str(args.gold_path))
    candidate_digest, population = candidate_population_digest(gold_by_id)
    if candidate_digest != args.candidate_digest:
        raise SystemExit(
            f"candidate digest mismatch: expected {args.candidate_digest}, got {candidate_digest}"
        )
    docs = list(load_maven_ere(args.gold_path))
    pred_by_doc = _load_predictions(args.predictions, args.min_confidence)
    gold_ids = {doc.doc_id for doc in docs}
    prediction_ids = set(pred_by_doc)
    if prediction_ids != gold_ids:
        raise SystemExit(
            "prediction document IDs differ from gold: "
            f"missing={sorted(gold_ids - prediction_ids)} "
            f"extra={sorted(prediction_ids - gold_ids)}"
        )
    per_doc = [
        pair_prf(pred_by_doc.get(doc.doc_id, []), doc, max_distance=args.max_distance)
        for doc in docs
    ]
    report: dict = {
        "n_docs": len(docs),
        "max_distance": args.max_distance,
        "min_confidence": args.min_confidence,
        "candidate_id_digest": candidate_digest,
        "population_counts": population,
        "hashes": {
            "gold": hashlib.sha256(args.gold_path.read_bytes()).hexdigest(),
            "predictions": hashlib.sha256(args.predictions.read_bytes()).hexdigest(),
        },
        "pair": _aggregate(per_doc),
    }
    if args.window_ceilings:
        report["window_recall_ceiling"] = {
            str(w): window_recall_ceiling(docs, w) for w in args.window_ceilings
        }

    micro = report["pair"]["micro"]
    diag = report["pair"]["diagnostics"]
    print(
        f"[pair] docs={len(docs)} micro P={micro['precision']:.3f} "
        f"R={micro['recall']:.3f} F1={micro['f1']:.3f} | "
        f"hallucinated={diag['hallucinated_pred_pairs']} "
        f"universe={diag['n_universe']}"
    )
    for family in ("coreference", "temporal", "causal", "subevent"):
        row = report["pair"][family]
        print(
            f"  {family:<12} P={row['precision']:.3f} R={row['recall']:.3f} "
            f"F1={row['f1']:.3f} (gold={row['n_gold']})"
        )
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
