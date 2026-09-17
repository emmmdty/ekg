#!/usr/bin/env python
"""Describe the two graphs Ch6 scores on, side by side (PHASE_E3 task E3.2).

Purely descriptive: this section carries no winning claim, it says what the
`gold` and `predicted` graphs of the frozen unit actually are, so a reader of
table 6-2 knows what the .0218 construction loss was paid on. The upstream
identity of `predicted` is whatever `upstream_registry.json` says (E3.1); it is
not C5/A4/D4, which share no document with this unit.

Reachability is R1 from `succession.reconstruction`, the same function the
propagation table reports, rather than a second definition that would drift.

    uv run python scripts/report_e3_graph_profile.py \\
        --relation-dump runs/factuality/predicted_edges_valid.jsonl \\
        --factuality-labels runs/factuality/predicted_labels_valid.json
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import networkx as nx

from ekg.core.io import read_jsonl
from ekg.core.schema import EventGraph, RelationEdge
from ekg.relations.data import load_maven_ere
from ekg.relations.data.maven_fact import FACTUALITY_LABELS, load_maven_fact
from ekg.succession.data.cgep import topology_triples
from ekg.succession.reconstruction import corpus_reconstruction

# Causal + subevent are what the ECG topology reads; temporal is carried but
# structurally orthogonal, which is why scrambling it costs exactly zero
# downstream (`docs/results/PHASE_E.md`). Counted separately for that reason.
TOPOLOGY = ("causal", "subevent")


def _profile(docs: list, edges_by_doc: dict[str, list[RelationEdge]]) -> dict:
    by_type: Counter[str] = Counter()
    by_subtype: Counter[str] = Counter()
    components: list[int] = []
    degrees: list[float] = []
    pairs = []
    for doc in docs:
        edges = edges_by_doc.get(doc.doc_id, [])
        for edge in edges:
            by_type[str(edge.relation_type.value)] += 1
            by_subtype[f"{edge.relation_type.value}/{edge.subtype}"] += 1
        graph = nx.Graph()
        graph.add_nodes_from(node.event_id for node in doc.nodes)
        graph.add_edges_from((h, t) for h, _, t in topology_triples(edges))
        components.append(nx.number_connected_components(graph))
        degrees.extend(dict(graph.degree()).values())
        pairs.append((doc, EventGraph(nodes={n.event_id: n for n in doc.nodes}, edges=edges)))

    reconstruction = corpus_reconstruction(pairs)
    return {
        "documents": len(docs),
        "nodes": sum(len(doc.nodes) for doc in docs),
        "edges_total": int(sum(by_type.values())),
        "edges_by_type": dict(sorted(by_type.items())),
        "edges_by_subtype": dict(sorted(by_subtype.items())),
        "topology_edges": int(sum(v for k, v in by_type.items() if k in TOPOLOGY)),
        "connected_components": sum(components),
        "mean_topology_degree": round(sum(degrees) / len(degrees), 4) if degrees else 0.0,
        "r1_reachability_rate": reconstruction["r1_reachability_rate"],
        "r2_query_f1": reconstruction["r2_query_prf"]["f1"],
    }


def _dot(doc, edges: list[RelationEdge], keep: set[str]) -> str:
    """One document's topology as Graphviz DOT: no new dependency, renders anywhere."""
    label = {n.event_id: (n.trigger or n.event_id.split("::")[1][:6]) for n in doc.nodes}
    style = {"causal": "solid", "subevent": "dashed"}
    lines = [f'digraph "{doc.doc_id}" {{', "  rankdir=LR; node [shape=box, fontsize=10];"]
    for node in sorted(keep):
        lines.append(f'  "{node}" [label="{label.get(node, node)}"];')
    for edge in edges:
        if edge.head_id in keep and edge.tail_id in keep:
            kind = str(edge.relation_type.value)
            if kind in TOPOLOGY:
                lines.append(
                    f'  "{edge.head_id}" -> "{edge.tail_id}" '
                    f'[label="{edge.subtype}", style={style[kind]}];'
                )
    lines.append("}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--unit", type=Path, default=Path("runs/stages/E3/e3-v61-20260917"))
    parser.add_argument("--ere", type=Path, default=Path("data/processed/maven_ere/valid.jsonl"))
    parser.add_argument("--fact", type=Path, default=Path("data/processed/maven_fact/valid.jsonl"))
    parser.add_argument("--relation-dump", type=Path, required=True)
    parser.add_argument("--factuality-labels", type=Path)
    parser.add_argument("--output", type=Path, default=Path("runs/cgep/e3_graph_profile.json"))
    parser.add_argument("--figure-doc", help="doc_id for the subgraph figure; default: the "
                                             "smallest document that still has a gold ECG")
    args = parser.parse_args()

    registry = json.loads((args.unit / "upstream_registry.json").read_text(encoding="utf-8"))
    keep = {
        node.split("::", 1)[0]
        for row in read_jsonl(args.unit / "queries.jsonl")
        for node in (row["anchor"], row["gold"], *row["candidates"])
    }
    docs = [doc for doc in load_maven_ere(args.ere) if doc.doc_id in keep]
    if len(docs) != len(keep):
        raise SystemExit(f"{args.ere} covers {len(docs)}/{len(keep)} unit documents")

    predicted_edges: dict[str, list[RelationEdge]] = {}
    for record in read_jsonl(args.relation_dump):
        if record["doc_id"] in keep:
            predicted_edges[record["doc_id"]] = [
                RelationEdge.model_validate(e) for e in record["edges"]
            ]
    gold_edges = {doc.doc_id: list(doc.gold_edges) for doc in docs}

    factuality = {"gold": Counter(), "predicted": Counter()}
    for doc in load_maven_fact(args.fact):
        if doc.doc_id in keep:
            factuality["gold"].update(m.factuality for m in doc.mentions)
    if args.factuality_labels:
        labels = json.loads(args.factuality_labels.read_text(encoding="utf-8"))
        factuality["predicted"].update(
            label for node, label in labels.items() if node.split("::", 1)[0] in keep
        )

    report = {
        "unit": {"path": str(args.unit), "sha256": registry["unit"]["sha256"]},
        "conditions": {
            name: {
                "upstream_identity": registry["conditions"][name]["upstream_identity"],
                **_profile(docs, edges),
                "factuality_distribution": {
                    label: factuality[name][label] for label in FACTUALITY_LABELS
                } or None,
            }
            for name, edges in (("gold", gold_edges), ("predicted", predicted_edges))
        },
    }

    figure_doc = args.figure_doc or min(
        (doc for doc in docs if topology_triples(gold_edges[doc.doc_id])),
        key=lambda d: len(d.nodes),
    ).doc_id
    doc = next(d for d in docs if d.doc_id == figure_doc)
    frame = {node for h, _, t in topology_triples(gold_edges[figure_doc]) for node in (h, t)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for name, edges in (("gold", gold_edges), ("predicted", predicted_edges)):
        path = args.output.with_name(f"{args.output.stem}_{figure_doc[:8]}_{name}.dot")
        path.write_text(_dot(doc, edges[figure_doc], frame), encoding="utf-8")
        print(f"[e3.2] wrote {path}")
    report["figure"] = {"doc_id": figure_doc, "nodes_in_frame": len(frame)}

    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for name, prof in report["conditions"].items():
        print(
            f"[e3.2] {name:9s} nodes={prof['nodes']} edges={prof['edges_total']} "
            f"topology={prof['topology_edges']} components={prof['connected_components']} "
            f"mean_deg={prof['mean_topology_degree']} r1={prof['r1_reachability_rate']:.4f}"
        )
    print(f"[e3.2] wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
