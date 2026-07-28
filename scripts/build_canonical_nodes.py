#!/usr/bin/env python
"""Phase-C pipeline: MAVEN mentions -> canonical event nodes, with the numbers.

Runs detection, similar-event discrimination and uncertainty-aware
canonicalization over one split and reports, on a held-out document set:

- **detection**: typed and identification-only micro-F1 over MAVEN's candidate
  universe (gold triggers + `negative_triggers`);
- **coreference**: MUC / B³ / CEAFe / CoNLL against gold clusters;
- **mis-merge**: pairwise merge P/R plus the mis-merge rate on the *hard* subset
  (same type, near-identical triggers) — the similar-event failure mode;
- **confidence**: ECE and the reliability curve of `node_confidence`, calibrated
  on the held-out calibration split only;
- **coref-family FNR**: the canonical clusters projected back onto coreference
  edges and scored on MAVEN-ERE gold with Phase B's own
  `stratified_admission_report`, so the improvement over the 1.000 that the
  relation extractor leaves (it has no coreference head at all) is read off the
  same ruler. The report also carries `coverage_ceiling`, the share of ERE gold
  coref pairs whose mentions exist in MAVEN-Arg — recall cannot exceed it.

Canonicalization runs over MAVEN-Arg documents: their character offsets are
exact (verified 0 mismatch), while the MAVEN-ERE loader tolerates an
unlocatable trigger as span (0, 0), which would silently pool the wrong token.
Mention ids are shared between the two releases, so gold coreference edges still
come from MAVEN-ERE and the comparison stays apples-to-apples.

    uv run python scripts/build_canonical_nodes.py \\
        --arg data/processed/maven_arg/valid.jsonl \\
        --ere data/processed/maven_ere/valid.jsonl \\
        --scorer lexical --threshold 0.7 --band 0.0 \\
        --out runs/canonical_nodes_lexical.json
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from ekg.core.calibration import IsotonicProbabilityCalibrator, reliability_curve
from ekg.core.eval import conll_coref_f1, expected_calibration_error, muc
from ekg.core.eval.relation import PRF, relation_prf
from ekg.core.schema import RelationEdge, RelationType
from ekg.nodes.canonical import CanonicalNode, canonicalize
from ekg.nodes.coref import (
    candidate_coref_pairs,
    cluster_of_nodes,
    coreference_scorers,
    labelled_coref_pairs,
)
from ekg.nodes.detection import detection_prf, event_detectors
from ekg.nodes.metrics import mis_merge_report
from ekg.relations.admission import stratified_admission_report
from ekg.relations.data import load_maven_arg, load_maven_ere
from ekg.relations.data.maven_arg import ArgumentDocument


def split_index(n: int, cal_ratio: float) -> int:
    """Phase-B's calibration split, replicated so document sets line up exactly."""
    return min(n - 1, max(1, int(n * cal_ratio))) if n > 1 else 0


def score_document(scorer, doc: ArgumentDocument) -> dict[tuple[str, str], float]:
    pairs = candidate_coref_pairs(doc.nodes)
    return scorer.score(doc.nodes, pairs, doc.doc_text) if pairs else {}


def cluster_correctness(
    nodes: Sequence[CanonicalNode], cluster_of: dict[str, str]
) -> list[tuple[float, bool]]:
    """(raw confidence, cluster is exactly a gold cluster) — the calibration rows."""
    gold_members: dict[str, set[str]] = {}
    for mention, event in cluster_of.items():
        gold_members.setdefault(event, set()).add(mention)
    rows = []
    for node in nodes:
        members = set(node.mention_cluster)
        event = cluster_of.get(node.mention_cluster[0], "")
        rows.append((node.raw_confidence, members == gold_members.get(event, set())))
    return rows


def ere_population_coreference(
    ere_docs: Sequence, by_doc_nodes: dict[str, list[CanonicalNode]]
) -> dict:
    """Our clustering re-scored on **MAVEN-ERE's** mention population.

    Published MAVEN-ERE coreference numbers are computed over ERE's mentions
    (17,780 in valid); canonicalization runs on MAVEN-Arg's (16,996) because only
    those carry exact character offsets. Both are internally consistent, but they
    are *different populations*, so our MUC and the published MUC are not on the
    same ruler until this is measured.

    An ERE mention the pipeline never saw is counted as its own singleton — the
    honest accounting (the system genuinely produced nothing for it), not a
    charitable one that would quietly drop it from the denominator.
    """
    predicted: list[set[str]] = []
    gold: list[set[str]] = []
    covered = total = 0
    for doc in ere_docs:
        ere_ids = {node.event_id for node in doc.nodes}
        total += len(ere_ids)

        seen: set[str] = set()
        for node in by_doc_nodes.get(doc.doc_id, []):
            cluster = {m for m in node.mention_cluster if m in ere_ids}
            if cluster:
                predicted.append(cluster)
                seen |= cluster
        covered += len(seen)
        predicted.extend({m} for m in sorted(ere_ids - seen))

        by_event: dict[str, set[str]] = {}
        for node in doc.nodes:
            by_event.setdefault(node.metadata["event"], set()).add(node.event_id)
        gold.extend(by_event.values())

    report = dict(conll_coref_f1(predicted, gold))
    # MAVEN-ERE's own table reports MUC precision and recall separately (its
    # RoBERTa-base baseline is recall-leaning at P 79.2 / R 84.0), so carry both
    # or there is no way to tell which side we are behind on.
    muc_prf = muc(predicted, gold)
    report["muc_precision"] = muc_prf["precision"]
    report["muc_recall"] = muc_prf["recall"]
    report["mention_coverage"] = covered / total if total else 0.0
    report["n_ere_mentions"] = total
    report["n_covered"] = covered
    return report


def coref_edges(nodes: Sequence[CanonicalNode]) -> list[RelationEdge]:
    """Canonical clusters projected back onto the coreference edges Ch2 never emits."""
    edges = []
    for node in nodes:
        members = node.mention_cluster
        for i, head in enumerate(members):
            for tail in members[i + 1 :]:
                edges.append(
                    RelationEdge(
                        head_id=head,
                        tail_id=tail,
                        relation_type=RelationType.COREFERENCE,
                        directed=False,
                        confidence=node.node_confidence,
                        evidence=node.evidence_spans,
                    )
                )
    return edges


def run(
    arg_docs: list[ArgumentDocument],
    ere_docs: list,
    *,
    scorer_name: str,
    scorer_path: str | None,
    threshold: float,
    band: float,
    cal_ratio: float,
    scorer=None,
) -> tuple[dict, list[CanonicalNode]]:
    """One operating point end to end.

    `scorer` lets a caller pass an already-built (or caching) scorer so a sweep
    over thresholds pays for scoring once instead of once per cell.
    """
    if scorer is None:
        scorer = coreference_scorers.create(
            scorer_name, **({"checkpoint_path": scorer_path} if scorer_path else {})
        )
    cut = split_index(len(arg_docs), cal_ratio)
    cal_docs, test_docs = arg_docs[:cut], arg_docs[cut:]

    # --- calibrate node_confidence on the held-out calibration split ---------- #
    cal_rows: list[tuple[float, bool]] = []
    for doc in cal_docs:
        result = canonicalize(
            doc.nodes, score_document(scorer, doc), threshold=threshold, band=band
        )
        cal_rows.extend(cluster_correctness(result.nodes, cluster_of_nodes(doc.nodes)))
    calibrator = IsotonicProbabilityCalibrator().fit(
        [s for s, _ in cal_rows], [c for _, c in cal_rows]
    )

    # --- run the test split -------------------------------------------------- #
    all_nodes: list[CanonicalNode] = []
    predicted_clusters: list[set[str]] = []
    gold_clusters: list[set[str]] = []
    cluster_of: dict[str, str] = {}
    hard_pairs = []
    raw_scores: list[float] = []
    node_probs: list[float] = []
    correct: list[bool] = []
    abstained = 0
    with_args = total_mentions = 0

    for doc in test_docs:
        doc_cluster_of = cluster_of_nodes(doc.nodes)
        cluster_of.update(doc_cluster_of)
        scores = score_document(scorer, doc)
        result = canonicalize(
            doc.nodes, scores, threshold=threshold, band=band, calibrator=calibrator
        )
        all_nodes.extend(result.nodes)
        abstained += len(result.abstained_merges)
        predicted_clusters.extend(result.clusters())
        gold_clusters.extend(doc.gold_clusters())
        hard_pairs.extend(p for p in labelled_coref_pairs(doc.nodes, doc_cluster_of) if p.hard)

        for score, ok in cluster_correctness(result.nodes, doc_cluster_of):
            raw_scores.append(score)
            correct.append(ok)
        node_probs.extend(n.node_confidence for n in result.nodes)
        with_args += sum(1 for n in doc.nodes if n.arguments)
        total_mentions += len(doc.nodes)

    report: dict = {
        "config": {
            "scorer": scorer_name,
            "scorer_path": scorer_path,
            "threshold": threshold,
            "band": band,
            "cal_ratio": cal_ratio,
            "n_cal_docs": len(cal_docs),
            "n_test_docs": len(test_docs),
        },
        "coreference": conll_coref_f1(predicted_clusters, gold_clusters),
        "mis_merge": mis_merge_report(predicted_clusters, cluster_of, hard_pairs),
        "abstained_merges": abstained,
        "confidence": {
            "ece_raw": expected_calibration_error(raw_scores, correct),
            "ece_calibrated": expected_calibration_error(node_probs, correct),
            "reliability": reliability_curve(node_probs, correct),
            "n_nodes": len(all_nodes),
            "exact_cluster_accuracy": sum(correct) / len(correct) if correct else 0.0,
        },
        "arguments": {
            "mentions_with_arguments": with_args,
            "mentions": total_mentions,
        },
    }

    # --- coref-family FNR on Phase B's ruler --------------------------------- #
    ere_test = ere_docs[split_index(len(ere_docs), cal_ratio) :]
    by_doc_nodes: dict[str, list[CanonicalNode]] = {}
    for node in all_nodes:
        by_doc_nodes.setdefault(node.doc_id, []).append(node)
    pairs = [
        (coref_edges(by_doc_nodes.get(doc.doc_id, [])), doc.gold_edges) for doc in ere_test
    ]
    stratified = stratified_admission_report(pairs)
    # `by_type` reports recall/FNR only; without precision a flood of spurious
    # merges would read as an improvement, so the full family PRF goes with it.
    coref_prf = relation_prf(
        [e for edges, _ in pairs for e in edges],
        [g for _, gold in pairs for g in gold],
    )["coreference"]
    covered = n_gold_coref = 0
    for doc in ere_test:
        known = {
            mention
            for node in by_doc_nodes.get(doc.doc_id, [])
            for mention in node.mention_cluster
        }
        for edge in doc.gold_edges:
            if edge.relation_type is not RelationType.COREFERENCE:
                continue
            n_gold_coref += 1
            covered += int({edge.head_id, edge.tail_id} <= known)
    # The same clustering on the population published numbers use.
    report["coreference_ere_population"] = ere_population_coreference(ere_test, by_doc_nodes)
    report["coref_family_fnr"] = {
        "n_ere_test_docs": len(ere_test),
        "by_type": stratified["by_type"],
        "coreference_prf": coref_prf,
        "coverage_ceiling": covered / n_gold_coref if n_gold_coref else 0.0,
        "baseline_fnr": 1.0,
        "baseline_note": (
            "the Phase A/B supervised extractor has no coreference head "
            "(FAMILY_SUBTYPES covers temporal/causal/subevent only), so its "
            "coref n_pred is 0 by construction"
        ),
    }
    return report, all_nodes


def evaluate_detection(
    docs: list[ArgumentDocument], detector_name: str, detector_path: str | None
) -> dict:
    kwargs = {"checkpoint_path": detector_path} if detector_path else {}
    detector = event_detectors.create(detector_name, **kwargs)
    typed_tp = typed_pred = typed_gold = 0
    ident_tp = 0
    n_candidates = 0
    for doc in docs:
        report = detection_prf(detector.detect(doc), doc.candidates)
        typed_tp += report["typed"]["tp"]
        typed_pred += report["typed"]["n_pred"]
        typed_gold += report["typed"]["n_gold"]
        ident_tp += report["identification"]["tp"]
        n_candidates += report["n_candidates"]
    return {
        "detector": detector_name,
        "typed": PRF.from_counts(typed_tp, typed_pred, typed_gold),
        "identification": PRF.from_counts(ident_tp, typed_pred, typed_gold),
        "n_candidates": n_candidates,
        "n_docs": len(docs),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arg", required=True, type=Path, help="MAVEN-Arg jsonl")
    parser.add_argument("--ere", required=True, type=Path, help="MAVEN-ERE jsonl (same split)")
    parser.add_argument("--scorer", default="lexical", help="coreference scorer name")
    parser.add_argument("--scorer-path", default=None, help="scorer checkpoint (supervised)")
    parser.add_argument("--detector", default=None, help="event detector name (optional)")
    parser.add_argument("--detector-path", default=None, help="detector checkpoint")
    parser.add_argument("--threshold", type=float, default=0.7)
    parser.add_argument("--band", type=float, default=0.0, help="abstention band half-width")
    parser.add_argument("--cal-ratio", type=float, default=0.3)
    parser.add_argument("--limit", type=int, default=None, help="first N documents (smoke)")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--nodes-out", type=Path, default=None, help="canonical nodes jsonl")
    args = parser.parse_args()

    arg_docs = list(load_maven_arg(args.arg))
    ere_docs = list(load_maven_ere(args.ere))
    if args.limit:
        arg_docs = arg_docs[: args.limit]
        keep = {d.doc_id for d in arg_docs}
        ere_docs = [d for d in ere_docs if d.doc_id in keep]

    report, nodes = run(
        arg_docs,
        ere_docs,
        scorer_name=args.scorer,
        scorer_path=args.scorer_path,
        threshold=args.threshold,
        band=args.band,
        cal_ratio=args.cal_ratio,
    )
    if args.detector:
        cut = split_index(len(arg_docs), args.cal_ratio)
        report["detection"] = evaluate_detection(
            arg_docs[cut:], args.detector, args.detector_path
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, default=float))
    if args.nodes_out:
        args.nodes_out.parent.mkdir(parents=True, exist_ok=True)
        args.nodes_out.write_text(
            "\n".join(node.to_event_node().model_dump_json() for node in nodes) + "\n"
        )
    print(json.dumps(report, indent=2, default=float)[:4000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
