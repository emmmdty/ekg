#!/usr/bin/env python
"""Evaluate one D4 typed-cue checkpoint on a manifest-selected fold only."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ekg.core.protocol import load_manifest_ids
from ekg.factuality.evidence import SAME_SENTENCE_RECALL_CEILING, gold_evidence_spans
from ekg.factuality.metrics import evidence_span_report, factuality_report
from ekg.factuality.typed_cues import (
    TypedCueFactualityDetector,
    structured_confusion_report,
    validate_typed_cue_arm,
)
from ekg.relations.data.maven_fact import factuality_distribution, load_maven_fact


def _write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--checkpoint", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--arm", required=True, choices=("full", "remove_core", "permutation"))
    parser.add_argument("--max-length", type=int, default=128)
    parser.add_argument("--stride", type=int, default=64)
    parser.add_argument("--permutation-seed", type=int, default=13)
    parser.add_argument("--labels-output", required=True, type=Path)
    parser.add_argument("--sidecar-output", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.arm = validate_typed_cue_arm(args.arm)
    for path in (args.source, args.checkpoint, args.manifest):
        if not path.exists():
            raise SystemExit(f"missing input: {path}")

    wanted = load_manifest_ids(args.manifest)
    documents = {doc.doc_id: doc for doc in load_maven_fact(args.source)}
    missing = set(wanted) - documents.keys()
    if missing:
        raise SystemExit(f"manifest has {len(missing)} documents absent from source")
    docs = [documents[doc_id] for doc_id in wanted]
    detector = TypedCueFactualityDetector(
        args.checkpoint,
        arm=args.arm,
        max_length=args.max_length,
        stride=args.stride,
        use_structure=False,
        permutation_seed=args.permutation_seed,
    )
    labels: dict[str, str] = {}
    evidence: dict[str, set[tuple[int, int]]] = {}
    sidecar: dict[str, dict[str, object]] = {}
    gold: dict[str, str] = {}
    for doc in docs:
        predictions = detector.predict(doc)
        expected = {mention.mention_id for mention in doc.mentions}
        if set(predictions) != expected or set(detector.last_sidecar) != expected:
            raise RuntimeError(f"{doc.doc_id}: prediction or sidecar coverage mismatch")
        labels.update({mention_id: item.factuality for mention_id, item in predictions.items()})
        evidence.update(
            {
                mention_id: {(span.char_start, span.char_end) for span in item.evidence}
                for mention_id, item in predictions.items()
            }
        )
        sidecar.update(detector.last_sidecar)
        gold.update({mention.mention_id: mention.factuality for mention in doc.mentions})
    if set(labels) != set(gold) or set(sidecar) != set(gold):
        raise RuntimeError("pooled prediction or sidecar coverage mismatch")
    report = factuality_report(labels, gold)
    payload = {
        "schema_version": "ekg.d4_typed_cue_evaluation.v1",
        "arm": args.arm,
        "documents": len(docs),
        "mentions": len(gold),
        "label_distribution": factuality_distribution(docs),
        "macro_f1": report["macro_f1"],
        "accuracy": report["accuracy"],
        "per_class": report["per_class"],
        "structured_confusion": structured_confusion_report(labels, gold),
        "evidence": evidence_span_report(evidence, gold_evidence_spans(docs), gold),
        "evidence_recall_ceiling": SAME_SENTENCE_RECALL_CEILING,
    }
    _write(args.labels_output, labels)
    _write(args.sidecar_output, sidecar)
    _write(args.output, payload)
    print(
        f"[d4-evaluate] arm={args.arm} docs={len(docs)} "
        f"macro-F1={payload['macro_f1']:.4f}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
