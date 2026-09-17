#!/usr/bin/env python
"""Close Ch6's three upstream input interfaces against the frozen unit (PHASE_E3 task E3.1).

E3.3 scores several graphs over **one** frozen query set. Before any of them runs,
each graph's three upstream layers -- identity, relation, factuality -- have to be
pinned to a real artefact, and every node the unit asks about has to exist in all of
them. A layer that silently misses documents would not fail the run; it would quietly
produce a weaker arm.

The upstream identity is **not** C5/A4/D4. Those three ran on slices of *train*
(291 / 291 / 2,913 documents) while the unit is built on *valid*: measured document
intersection is 0, so their registered fallbacks -- each one a prediction file on
another split -- cannot be replayed here (`docs/results/PHASE_E.md`, E3.1 blockage).
Option (yi3) stands instead: the `predicted` condition keeps the v5 discriminative
extractor's own valid output, the same upstream that produced the published .1583.
Every table carrying this arm must say so; `upstream_identity` below is that string.

This registers and verifies; it does not copy. Materialising a second copy of edges
the consumer already reads from `--dump` would give two files to keep in sync, so the
registry names each source with its digest and asserts coverage against the unit.

    uv run python scripts/close_e3_upstream_inputs.py --unit runs/stages/E3/e3-v61-20260917 \
        --relation-dump runs/factuality/predicted_edges_valid.jsonl \
        --factuality-labels runs/factuality/predicted_labels_valid.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ekg.core.io import read_jsonl
from ekg.core.stage_bundle import id_digest, sha256_file
from ekg.relations.data import load_maven_ere
from ekg.relations.data.maven_fact import FACTUALITY_LABELS, load_maven_fact

SCHEMA_VERSION = "ekg.e3_upstream_registry.v1"

# What the `predicted` condition's graph actually came from, verbatim for table headers.
PREDICTED_IDENTITY = (
    "v5 discriminative extractor on MAVEN-ERE valid (the upstream of the published "
    ".1583 row); not C5/A4/D4, whose runs share no document with this unit"
)
GOLD_IDENTITY = "MAVEN-ERE / MAVEN-FACT released valid annotations"


def _canonical(edges: list[dict]) -> list[tuple[str, str, str, str]]:
    """Edge set as an order-independent key. Stored order is a measured confound."""
    return sorted(
        (e["head_id"], e["relation_type"], str(e.get("subtype") or ""), e["tail_id"])
        for e in edges
    )


def _unit(unit_dir: Path, fixture: int | None) -> dict:
    manifest = json.loads((unit_dir / "manifest.json").read_text(encoding="utf-8"))
    queries = unit_dir / "queries.jsonl"
    on_disk = sha256_file(queries)
    if on_disk != manifest["unit"]["sha256"]:
        raise SystemExit(f"unit drifted: {on_disk} != frozen {manifest['unit']['sha256']}")

    rows = list(read_jsonl(queries))
    if fixture:
        rows = rows[:fixture]
    nodes: set[str] = set()
    for row in rows:
        nodes.update((row["anchor"], row["gold"], *row["candidates"]))
    if len(rows) != len({r["instance_id"] for r in rows}):
        raise SystemExit("duplicate instance_id in the frozen unit")
    # Candidates are drawn from the *corpus-wide* pool, not the query's own document,
    # so the document set the layers must cover comes from the node ids -- taking it
    # from `doc_id` alone would under-cover by two orders of magnitude on a fixture.
    docs = {node.split("::", 1)[0] for node in nodes} | {row["doc_id"] for row in rows}
    return {"manifest": manifest, "rows": rows, "nodes": nodes, "docs": docs}


def _identity_layers(docs: list) -> dict[str, dict[str, str]]:
    """node -> cluster id, for both conditions.

    Gold grouping is the released coreference. The extractor predicted **no**
    coreference on valid (`runs/submission/valid_prediction_sup.jsonl` has
    `coreference: []` on all 710 documents, and its dump scores n_pred=0), so the
    predicted grouping is every mention its own cluster. That is a fact about the
    v5 extractor, recorded rather than patched: an identity layer invented here
    would be a fourth method nobody trained.
    """
    gold: dict[str, str] = {}
    singleton: dict[str, str] = {}
    for doc in docs:
        for event_id, members in doc.clusters.items():
            for node in members:
                if node in gold:
                    raise SystemExit(f"{node} appears in two gold clusters")
                gold[node] = f"{doc.doc_id}::{event_id}"
        for node in doc.nodes:
            singleton[node.event_id] = node.event_id
    return {"gold": gold, "predicted": singleton}


def _relation_layers(docs: list, dump: Path, keep: set[str]) -> tuple[dict, dict]:
    """Edge sets per condition, plus the coverage facts the registry records."""
    node_ids = {doc.doc_id: {n.event_id for n in doc.nodes} for doc in docs}
    gold = {
        doc.doc_id: _canonical([e.model_dump() for e in doc.gold_edges])
        for doc in docs
        if doc.doc_id in keep
    }
    predicted: dict[str, list] = {}
    for record in read_jsonl(dump):
        if record["doc_id"] in keep:
            predicted[record["doc_id"]] = _canonical(record["edges"])
    missing = keep - set(predicted)
    if missing:
        raise SystemExit(f"{dump} covers {len(keep) - len(missing)}/{len(keep)} unit documents")
    for doc_id, edges in predicted.items():
        stray = {end for head, _, _, tail in edges for end in (head, tail)} - node_ids[doc_id]
        if stray:
            raise SystemExit(f"{doc_id}: {len(stray)} predicted endpoints outside the node frame")
    return gold, predicted


def _factuality_layers(fact_path: Path, keep: set[str], labels: Path | None) -> dict:
    gold: dict[str, str] = {}
    for doc in load_maven_fact(fact_path):
        if doc.doc_id in keep:
            for mention in doc.mentions:
                gold[mention.mention_id] = mention.factuality
    bad = {label for label in gold.values()} - set(FACTUALITY_LABELS)
    if bad:
        raise SystemExit(f"unknown factuality labels {sorted(bad)}")
    predicted = json.loads(labels.read_text(encoding="utf-8")) if labels else None
    return {"gold": gold, "predicted": predicted}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--unit", type=Path, default=Path("runs/stages/E3/e3-v61-20260917"))
    parser.add_argument("--ere", type=Path, default=Path("data/processed/maven_ere/valid.jsonl"))
    parser.add_argument("--fact", type=Path, default=Path("data/processed/maven_fact/valid.jsonl"))
    parser.add_argument(
        "--relation-dump", type=Path, required=True,
        help="the v5 extractor's predicted edges on valid. No default on purpose: the "
             "published .1583 came from runs/factuality/predicted_edges_valid.jsonl on "
             "gpu-4090, and runs/relations/supervised_dump.jsonl is a *different*, "
             "earlier dump of the same day -- a default here would silently register "
             "the wrong upstream",
    )
    parser.add_argument(
        "--factuality-labels", type=Path,
        help="{mention_id: label} from the Phase D detector. Absent means the predicted "
             "factuality layer is registered as pending rather than closed",
    )
    parser.add_argument("--fixture", type=int, help="first N queries only (E3.1's CPU fixture)")
    parser.add_argument("--no-write", action="store_true", help="assert only")
    args = parser.parse_args()

    unit = _unit(args.unit, args.fixture)
    keep, nodes = unit["docs"], unit["nodes"]
    print(f"[e3.1] unit: {len(unit['rows'])} queries  {len(keep)} docs  {len(nodes)} nodes")

    docs = [doc for doc in load_maven_ere(args.ere) if doc.doc_id in keep]
    if len(docs) != len(keep):
        raise SystemExit(f"{args.ere} covers {len(docs)}/{len(keep)} unit documents")

    identity = _identity_layers(docs)
    gold_edges, pred_edges = _relation_layers(docs, args.relation_dump, keep)
    factuality = _factuality_layers(args.fact, keep, args.factuality_labels)

    # A node the unit asks about but a layer has never heard of is a silent weakening
    # of that arm, so it is fatal here rather than a missing row later.
    for name, table in (
        ("identity/gold", identity["gold"]),
        ("identity/predicted", identity["predicted"]),
        ("factuality/gold", factuality["gold"]),
    ):
        gap = nodes - set(table)
        if gap:
            raise SystemExit(f"{name} misses {len(gap)} of {len(nodes)} unit nodes")

    # The two conditions differ in graph context only: queries, candidates and labels
    # are the frozen unit's, so their id digests must be the same object.
    digests = {
        cond: id_digest(nodes) for cond in ("gold", "predicted")
    }
    if digests["gold"] != digests["predicted"]:
        raise SystemExit("gold and predicted node id sets differ")
    if not args.fixture and digests["gold"] != unit["manifest"]["unit"]["candidate_id_digest"]:
        # candidate digest covers candidates only; anchors and gold answers are drawn
        # from the same pool, so equality is the expected state and a difference is news.
        print("[e3.1] note: node digest != frozen candidate digest (anchors/answers added)")

    registry = {
        "schema_version": SCHEMA_VERSION,
        "status": "closed" if factuality["predicted"] is not None else "closed_except_factuality",
        "unit": {
            "path": str(args.unit),
            "sha256": unit["manifest"]["unit"]["sha256"],
            "instances": len(unit["rows"]),
            "documents": len(keep),
            "nodes": len(nodes),
            "node_id_digest": digests["gold"],
        },
        "conditions": {
            "gold": {"upstream_identity": GOLD_IDENTITY},
            "predicted": {"upstream_identity": PREDICTED_IDENTITY},
        },
        "layers": {
            "identity": {
                "gold": {"source": str(args.ere), "sha256": sha256_file(args.ere),
                         "clusters": len(set(identity["gold"].values()))},
                "predicted": {"source": "singleton (extractor predicted no coreference)",
                              "evidence": "runs/relations/supervised_dump_metrics.json "
                                          "coreference.n_pred = 0 over 710 valid documents",
                              "clusters": len(set(identity["predicted"].values()))},
            },
            "relation": {
                "gold": {"source": str(args.ere), "sha256": sha256_file(args.ere),
                         "edges": sum(len(v) for v in gold_edges.values())},
                "predicted": {"source": str(args.relation_dump),
                              "sha256": sha256_file(args.relation_dump),
                              "edges": sum(len(v) for v in pred_edges.values())},
            },
            "factuality": {
                "gold": {"source": str(args.fact), "sha256": sha256_file(args.fact),
                         "labels": len(factuality["gold"])},
                "predicted": (
                    {"source": str(args.factuality_labels),
                     "sha256": sha256_file(args.factuality_labels),
                     "labels": len(factuality["predicted"])}
                    if factuality["predicted"] is not None
                    else {"status": "pending",
                          "provenance": "scripts/evaluate_factuality.py --dump-labels, Phase D "
                                        "detector; the 2026-07-29 dump lives on gpu-4090",
                          "measured_downstream_effect": "purified -0.0001, purified_oracle "
                                                        "-0.0000 MRR (docs/results/PHASE_E.md)"}
                ),
            },
        },
        "edge_order": "canonical (sorted head/type/subtype/tail); stored order is a "
                      "measured confound, see src/ekg/succession/graph_context.py",
    }
    print(
        f"[e3.1] identity gold={registry['layers']['identity']['gold']['clusters']} clusters / "
        f"predicted={registry['layers']['identity']['predicted']['clusters']} singletons\n"
        f"[e3.1] relation gold={registry['layers']['relation']['gold']['edges']} / "
        f"predicted={registry['layers']['relation']['predicted']['edges']} edges\n"
        f"[e3.1] factuality gold={registry['layers']['factuality']['gold']['labels']} labels, "
        f"predicted={registry['layers']['factuality']['predicted'].get('status', 'closed')}\n"
        f"[e3.1] status={registry['status']}"
    )
    if not args.no_write:
        out = args.unit / "upstream_registry.json"
        out.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"[e3.1] wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
