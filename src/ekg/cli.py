"""End-to-end CPU smoke over the bundled fixtures.

Runs the event-graph construction pipeline with the torch-free baselines so a
fresh local checkout can prove the cross-stage contracts, graph construction,
consistency repair, evidence grounding, and the multi-agent scaffold all work
-- without a GPU:

    mentions -> canonical event nodes (identity, deduplicated + confidence)
    event nodes -> RelationPipeline -> EventGraph (consistent, grounded)
                -> MultiAgentRelationPipeline (agentic construction + verifier)

Exposed as the `ekg-smoke` console script.
"""

from __future__ import annotations

import os
from pathlib import Path

from ekg.core.eval.consistency import consistency_report
from ekg.core.io import load_event_nodes
from ekg.nodes.canonical import canonicalize
from ekg.nodes.coref import candidate_coref_pairs, cluster_of_nodes, coreference_scorers
from ekg.nodes.detection import detection_prf, event_detectors
from ekg.nodes.metrics import mis_merge_report
from ekg.relations import RelationPipeline
from ekg.relations.data import load_maven_arg
from ekg.relations.pipeline import MultiAgentRelationPipeline


def _fixtures_dir() -> Path:
    override = os.environ.get("EKG_FIXTURES")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[2] / "data" / "fixtures"


def run_smoke() -> int:
    fixtures = _fixtures_dir()
    print(f"[ekg-smoke] fixtures: {fixtures}")

    # 0) Identity: mentions -> deduplicated canonical nodes with a confidence.
    arg_docs = list(load_maven_arg(fixtures / "maven_arg" / "sample.jsonl"))
    detector = event_detectors.create("lexicon").fit(arg_docs)
    scorer = coreference_scorers.create("lexical")
    canonical = 0
    mentions = 0
    for doc in arg_docs:
        detected = detection_prf(detector.detect(doc), doc.candidates)
        result = canonicalize(
            doc.nodes, scorer.score(doc.nodes, candidate_coref_pairs(doc.nodes)), threshold=0.9
        )
        merges = mis_merge_report(result.clusters(), cluster_of_nodes(doc.nodes), pairs=[])
        canonical += len(result.nodes)
        mentions += len(doc.nodes)
        print(
            f"[nodes] {doc.doc_id}: mentions={len(doc.nodes)} canonical={len(result.nodes)} "
            f"detection_f1={detected['typed']['f1']:.3f} mis_merge={merges['mis_merge_rate']:.3f}"
        )
    print(f"[nodes] {mentions} mentions -> {canonical} canonical nodes")

    # 1) Relations: nodes -> evidence-grounded, consistent event graph.
    nodes = load_event_nodes(fixtures / "event_graph_zh" / "event_nodes.jsonl")
    graph = RelationPipeline().build_graph(nodes)
    print(
        f"[relations] nodes={len(graph.nodes)} edges={len(graph.edges)} "
        f"(dropped_ungrounded={graph.metadata.get('edges_dropped_ungrounded')})"
    )
    print(f"[relations] consistency: {consistency_report(graph)}")

    # 2) Multi-agent upgrade: same inputs, agentic construction + verifier.
    ma_graph = MultiAgentRelationPipeline().build_graph(nodes)
    faithful = [e.faithfulness for e in ma_graph.edges if e.faithfulness is not None]
    mean_faith = sum(faithful) / len(faithful) if faithful else 0.0
    print(
        f"[relations:multi-agent] edges={len(ma_graph.edges)} "
        f"mean_edge_faithfulness={mean_faith:.3f}"
    )

    print("[ekg-smoke] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_smoke())
