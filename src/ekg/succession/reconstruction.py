"""ECG reconstructability: can the successor-prediction problems still be posed
on the *constructed* (predicted -> repaired -> admitted) graph, not just on gold?

CGEP poses one successor query per gold Event-Causality-Graph query edge
(tail out-degree 0, in-degree 1; docs/SPEC.md §6). A query is only answerable if
its gold successor edge survives construction — exactly the per-query ``reachable``
flag CS-CRP (`core.calibration.propagation`) reserves budget for.

We reuse the authoritative CGEP construction (`succession.data.cgep`) unchanged,
swapping predicted edges in for gold via `dataclasses.replace` while holding the
gold coreference frame fixed, and report two honest views:

- **R1 reachability** — fraction of gold query edges present in the predicted
  causal+subevent topology (recall-flavored; the CS-CRP bridge). CRC admission
  trades this against precision under an FNR bound, so it may hold flat or dip.
- **R2 query-edge fidelity** — precision/recall/F1 of the query edges the
  *predicted* graph induces vs. the gold ones. Repair (drop cyclic/contradictory
  edges) + admission (drop low-confidence edges) lift precision, so R2's F1 can
  rise where R1 cannot — the honest place to look for a repair gain.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace

from ekg.core.eval.relation import PRF
from ekg.core.schema import EventGraph
from ekg.relations.data.maven_ere import RelationDocument
from ekg.succession.data.cgep import _topology_edges, extract_ecgs, query_edge_indices

__all__ = ["corpus_reconstruction", "reconstruction_report", "ecg_reachable_flags"]

QueryPair = tuple[str, str]


def _query_pairs(ecgs: list) -> list[QueryPair]:
    """The (head_id, tail_id) of every ECG query edge, in document order."""
    pairs: list[QueryPair] = []
    for ecg in ecgs:
        for pos in query_edge_indices(ecg):
            head, _, tail = ecg.edges[pos]
            pairs.append((ecg.nodes[head].node_id, ecg.nodes[tail].node_id))
    return pairs


def _topology_pairs(doc: RelationDocument, include_subevent: bool) -> set[QueryPair]:
    return {(h, t) for h, _, t in _topology_edges(doc, include_subevent=include_subevent)}


def ecg_reachable_flags(
    doc: RelationDocument,
    predicted_graph: EventGraph,
    *,
    min_nodes: int = 4,
    include_subevent: bool = True,
) -> list[bool]:
    """Per gold query edge: is it present in the predicted causal+subevent topology?

    One flag per successor-prediction query, in gold-ECG document order — the list
    CS-CRP consumes as ``reachable``.
    """
    gold_queries = _query_pairs(
        extract_ecgs(doc, min_nodes=min_nodes, include_subevent=include_subevent)
    )
    pred_doc = replace(doc, gold_edges=list(predicted_graph.edges))
    pred_topology = _topology_pairs(pred_doc, include_subevent)
    return [pair in pred_topology for pair in gold_queries]


def reconstruction_report(
    doc: RelationDocument,
    predicted_graph: EventGraph,
    *,
    min_nodes: int = 4,
    include_subevent: bool = True,
) -> dict:
    """R1 reachability + R2 query-edge fidelity of ``predicted_graph`` vs gold ECGs.

    Both views hold the gold coreference frame fixed (only the causal+subevent
    edges differ), so the numbers isolate the relation stage's structural effect.
    """
    pred_doc = replace(doc, gold_edges=list(predicted_graph.edges))
    gold_ecgs = extract_ecgs(doc, min_nodes=min_nodes, include_subevent=include_subevent)
    pred_ecgs = extract_ecgs(pred_doc, min_nodes=min_nodes, include_subevent=include_subevent)

    gold_queries = _query_pairs(gold_ecgs)
    gold_q, pred_q = set(gold_queries), set(_query_pairs(pred_ecgs))
    pred_topology = _topology_pairs(pred_doc, include_subevent)
    gold_topology = _topology_pairs(doc, include_subevent)

    flags = [pair in pred_topology for pair in gold_queries]
    prf = PRF.from_counts(len(gold_q & pred_q), len(pred_q), len(gold_q))
    n_queries = len(flags)
    return {
        "n_gold_ecgs": len(gold_ecgs),
        "n_gold_queries": n_queries,
        "r1_reachable": sum(flags),
        "r1_reachability_rate": sum(flags) / n_queries if n_queries else 0.0,
        "r2_query_prf": {
            "precision": float(prf["precision"]),
            "recall": float(prf["recall"]),
            "f1": float(prf["f1"]),
            "tp": int(prf["tp"]),
            "n_pred": int(prf["n_pred"]),
            "n_gold": int(prf["n_gold"]),
        },
        "topology_recall": (
            len(gold_topology & pred_topology) / len(gold_topology) if gold_topology else 0.0
        ),
    }


def corpus_reconstruction(pairs: Sequence[tuple[RelationDocument, EventGraph]]) -> dict:
    """Corpus R1 reachability rate + micro-aggregated R2 query-edge PRF.

    Micro rather than macro: a document with forty query edges should weigh forty
    times a document with one, since the downstream table is scored per query.
    """
    reachable = queries = ecgs = 0
    tp = n_pred = n_gold = 0
    for doc, graph in pairs:
        report = reconstruction_report(doc, graph)
        reachable += report["r1_reachable"]
        queries += report["n_gold_queries"]
        ecgs += report["n_gold_ecgs"]
        prf = report["r2_query_prf"]
        tp, n_pred, n_gold = tp + prf["tp"], n_pred + prf["n_pred"], n_gold + prf["n_gold"]
    agg = PRF.from_counts(tp, n_pred, n_gold)
    return {
        "n_gold_ecgs": ecgs,
        "n_gold_queries": queries,
        "r1_reachable": reachable,
        "r1_reachability_rate": reachable / queries if queries else 0.0,
        "r2_query_prf": {
            "precision": float(agg["precision"]),
            "recall": float(agg["recall"]),
            "f1": float(agg["f1"]),
            "tp": int(agg["tp"]),
            "n_pred": int(agg["n_pred"]),
            "n_gold": int(agg["n_gold"]),
        },
    }
