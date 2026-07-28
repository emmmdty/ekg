#!/usr/bin/env python
"""Report Phase D on MAVEN-FACT valid: detection, robustness, purification.

Three results in one pass over the split, because they must share a population:

1. **detection** — 5-class macro-F1 (the headline; accuracy is a footnote on a
   94.9%-CT+ corpus) plus per-class P/R/F1, the majority-class floor computed
   from the same gold, and evidence-span P/R/F1 over the 843 annotated mentions.
2. **robustness** — the same detector re-run with Phase A's *predicted* edges
   replacing the gold graph. MAVEN-FACT reports gold-input numbers only; the
   drop is what the metric costs on a graph the pipeline actually built. The
   two conditions differ in the edge set and nothing else.
3. **purification** — the predicted labels applied back to the graph (CT− nodes
   dropped, hedged nodes down-weighted), with graph size and consistency
   reported on both sides so shrinkage is not mistaken for repair.

The predicted graph is built by the Phase A extractor over the *same* documents:
MAVEN-FACT and MAVEN-ERE share doc ids and all 17,780 valid mention ids
(verified), so predicted edges join onto factuality mentions with no mapping.

    .venv/bin/python -u scripts/evaluate_factuality.py \
        --valid data/processed/maven_fact/valid.jsonl \
        --checkpoint runs/factuality/supervised_6ep \
        --extractor-checkpoint runs/relations/supervised_maven \
        --output runs/factuality_valid.json
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from ekg.core.schema import EventGraph
from ekg.factuality.detection import (
    LexiconFactualityDetector,
    SupervisedFactualityDetector,
)
from ekg.factuality.evidence import SAME_SENTENCE_RECALL_CEILING, gold_evidence_spans
from ekg.factuality.metrics import (
    evidence_span_prf,
    factuality_report,
    majority_baseline_report,
)
from ekg.factuality.purification import DEFAULT_POLICY, purification_report, purify_graph
from ekg.relations.data.maven_fact import (
    FactualityDocument,
    factuality_distribution,
    load_maven_fact,
)


def run_detector(
    detector, docs: Sequence[FactualityDocument], edges_by_doc: dict | None = None
) -> tuple[dict[str, str], dict[str, set[tuple[int, int]]]]:
    """Predicted labels and evidence spans over `docs`.

    ``edges_by_doc`` replaces each document's gold graph with a predicted one;
    None keeps gold, which is MAVEN-FACT's own setting.
    """
    labels: dict[str, str] = {}
    evidence: dict[str, set[tuple[int, int]]] = {}
    for doc in docs:
        edges = None if edges_by_doc is None else edges_by_doc.get(doc.doc_id, [])
        predictions = (
            detector.predict(doc, edges)
            if isinstance(detector, SupervisedFactualityDetector)
            else detector.predict(doc)
        )
        for mention_id, prediction in predictions.items():
            labels[mention_id] = prediction.factuality
            evidence[mention_id] = {(s.char_start, s.char_end) for s in prediction.evidence}
    return labels, evidence


def score(
    labels: dict[str, str],
    evidence: dict[str, set[tuple[int, int]]],
    docs: Sequence[FactualityDocument],
) -> dict:
    gold = {m.mention_id: m.factuality for doc in docs for m in doc.mentions}
    report = factuality_report(labels, gold)
    span_prf = evidence_span_prf(evidence, gold_evidence_spans(docs))
    return {
        "macro_f1": report["macro_f1"],
        "accuracy": report["accuracy"],
        "per_class": {label: dict(prf) for label, prf in report["per_class"].items()},
        "n_mentions": report["n_mentions"],
        "evidence_span": dict(span_prf),
        "evidence_recall_ceiling": SAME_SENTENCE_RECALL_CEILING,
    }


def predicted_edges(
    docs: Sequence[FactualityDocument], checkpoint: str, max_length: int
) -> dict[str, list]:
    """Phase A's predicted relation edges, per document."""
    from ekg.relations.extractor.base import ExtractionContext
    from ekg.relations.extractor.supervised import SupervisedRelationExtractor

    extractor = SupervisedRelationExtractor(
        checkpoint_path=checkpoint, max_distance=None, max_length=max_length
    )
    edges: dict[str, list] = {}
    for i, doc in enumerate(docs, 1):
        context = ExtractionContext(doc_text={doc.doc_id: doc.doc_text})
        edges[doc.doc_id] = extractor.extract(doc.nodes, context)
        if i % 50 == 0:
            total = sum(len(v) for v in edges.values())
            print(f"extracted {i}/{len(docs)} documents, {total} edges", flush=True)
    return edges


def graph_of(docs: Sequence[FactualityDocument], edges_by_doc: dict | None) -> EventGraph:
    """One corpus-level graph, from gold edges or predicted ones."""
    nodes = {n.event_id: n for doc in docs for n in doc.nodes}
    edges = [
        edge
        for doc in docs
        for edge in (doc.gold_edges if edges_by_doc is None else edges_by_doc.get(doc.doc_id, []))
    ]
    return EventGraph(nodes=nodes, edges=edges)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--valid", required=True, type=Path, help="MAVEN-FACT valid jsonl")
    parser.add_argument("--checkpoint", type=Path, help="trained factuality detector dir")
    parser.add_argument(
        "--lexicon", type=Path, help="lexicon checkpoint json (the memorization floor)"
    )
    parser.add_argument(
        "--extractor-checkpoint",
        type=Path,
        help="Phase A relation extractor; enables the predicted-graph condition",
    )
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--stride", type=int, default=128)
    parser.add_argument("--no-structure", action="store_true")
    parser.add_argument("--limit", type=int, default=None, help="first N documents (smoke)")
    parser.add_argument("--output", type=Path, help="write the report JSON here")
    args = parser.parse_args()

    docs = list(load_maven_fact(args.valid))
    if args.limit:
        docs = docs[: args.limit]
    gold = {m.mention_id: m.factuality for doc in docs for m in doc.mentions}
    distribution = factuality_distribution(docs)
    baseline = majority_baseline_report(gold)
    print(f"{len(docs)} documents, {len(gold)} mentions")
    print(f"label distribution: {distribution}")
    print(
        f"majority baseline: macro-F1 {baseline['macro_f1']:.4f} "
        f"accuracy {baseline['accuracy']:.4f}"
    )

    result: dict = {
        "n_documents": len(docs),
        "label_distribution": distribution,
        "majority_baseline": {
            "macro_f1": baseline["macro_f1"],
            "accuracy": baseline["accuracy"],
        },
        "evidence_mismatches_dropped": sum(d.evidence_mismatches for d in docs),
    }

    if args.lexicon:
        labels, evidence = run_detector(
            LexiconFactualityDetector(checkpoint_path=args.lexicon), docs
        )
        result["lexicon"] = score(labels, evidence, docs)
        print(f"lexicon: macro-F1 {result['lexicon']['macro_f1']:.4f}")

    if not args.checkpoint:
        _write(result, args.output)
        return 0

    detector = SupervisedFactualityDetector(
        checkpoint_path=str(args.checkpoint),
        max_length=args.max_length,
        stride=args.stride,
        use_structure=not args.no_structure,
    )
    gold_labels, gold_evidence = run_detector(detector, docs)
    result["gold_graph"] = score(gold_labels, gold_evidence, docs)
    print(
        f"gold-input: macro-F1 {result['gold_graph']['macro_f1']:.4f} "
        f"accuracy {result['gold_graph']['accuracy']:.4f} "
        f"evidence-F1 {result['gold_graph']['evidence_span']['f1']:.4f}"
    )

    purified = purify_graph(graph_of(docs, None), gold_labels, DEFAULT_POLICY)
    result["purification_gold_graph"] = _serializable(
        purification_report(graph_of(docs, None), purified)
    )

    if args.extractor_checkpoint:
        edges_by_doc = predicted_edges(docs, str(args.extractor_checkpoint), args.max_length)
        result["n_predicted_edges"] = sum(len(v) for v in edges_by_doc.values())
        predicted_labels, predicted_evidence = run_detector(detector, docs, edges_by_doc)
        result["predicted_graph"] = score(predicted_labels, predicted_evidence, docs)
        drop = result["gold_graph"]["macro_f1"] - result["predicted_graph"]["macro_f1"]
        result["robustness_drop_macro_f1"] = drop
        # How many labels actually moved: a small macro-F1 drop with many label
        # changes is a different finding from a stable prediction.
        result["n_labels_changed"] = sum(
            1 for k, v in predicted_labels.items() if gold_labels[k] != v
        )
        print(
            f"predicted-input: macro-F1 {result['predicted_graph']['macro_f1']:.4f} "
            f"(drop {drop:+.4f}), {result['n_labels_changed']} labels changed"
        )
        before = graph_of(docs, edges_by_doc)
        result["purification_predicted_graph"] = _serializable(
            purification_report(before, purify_graph(before, predicted_labels, DEFAULT_POLICY))
        )

    _write(result, args.output)
    return 0


def _serializable(report: dict) -> dict:
    """`consistency_report` returns nested dicts of numbers; keep them as-is."""
    return json.loads(json.dumps(report, default=float))


def _write(result: dict, output: Path | None) -> None:
    text = json.dumps(result, ensure_ascii=False, indent=2, default=float)
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text)
        print(f"wrote {output}")
    else:
        print(text)


if __name__ == "__main__":
    raise SystemExit(main())
