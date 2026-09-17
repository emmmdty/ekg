#!/usr/bin/env python
"""Write the frozen Ch6 unit as a knowledge-graph-completion dataset (G-11a).

Two of table 6-2's four external opponents -- CSProm-KG and SimKGC -- are KGC
models. Neither implements CGEP: SeDGPL's paper reports numbers for them, but the
adaptation that produced those numbers was never released, so ours is a
**transparent adaptation** (FR-016 state (b)) and every difference from their
published setting has to be listed rather than discovered later.

The mapping is the close one, which is presumably why SeDGPL's authors picked
these two: a CGEP query is ``(anchor, relation, ?)`` over a fixed candidate set,
and KGC's ``predict_tail`` is ``(head, relation, ?)`` over all entities. Entities
are event mentions, named by their trigger and described by their sentence;
relations are the three that carry ECG topology.

**What goes into the training graph, and why.** SeDGPL sees each instance's own
gold ECG *minus that instance's query edge* as its prompt, so gold valid-split
structure is available to the consumer at test time under this protocol. A KGC
model has no per-query context input, so the equivalent is to put those edges in
the KG -- and then **every one of the 1,908 query edges must come out**, because
one instance's query edge is another instance's context inside the same ECG and
a single static KG cannot exclude them per instance.

Two differences this creates, both in the opponent's favour and both listed in
the manifest rather than argued away:

1. those valid-split context edges *train* the KGC embeddings, where SeDGPL only
   reads them at inference;
2. valid entities that appear in no surviving training triple keep their
   initialised structural embedding, so only the text half of the model speaks
   for them. That is the transductive-vocabulary problem SeDGPL solves by
   building its ``<a_i>`` inventory over train and test together.

    uv run python scripts/export_cgep_as_kgc.py --output runs/stages/E3/kgc/CGEP-MAVEN
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path

from ekg.core.io import read_jsonl
from ekg.core.stage_bundle import id_digest, sha256_file
from ekg.succession.data.cgep import extract_ecgs, iter_documents

SCHEMA_VERSION = "ekg.cgep_as_kgc.v1"

# The three subtypes `topology_triples` lets through, in a fixed order so the
# relation ids are a property of this script rather than of dict iteration.
RELATIONS = ("CAUSE", "PRECONDITION", "SUBEVENT_OF")

RELATION_NAMES = {
    "CAUSE": "causes",
    "PRECONDITION": "is a precondition for",
    "SUBEVENT_OF": "has subevent",
}


def _numbered(path: Path, lines: list[str]) -> None:
    """Their readers take a count on line 1 and assert it; `helper.read` fails loudly."""
    path.write_text(f"{len(lines)}\n" + "".join(f"{line}\n" for line in lines), encoding="utf-8")


def _collect(paths: list[Path], min_nodes: int) -> tuple[dict[str, object], list[tuple]]:
    """Every ECG node and topology triple of these splits, keyed by node id."""
    nodes: dict[str, object] = {}
    triples: list[tuple[str, str, str]] = []
    for ecg in (
        ecg
        for path in paths
        for doc in iter_documents([str(path)])
        for ecg in extract_ecgs(doc, min_nodes=min_nodes)
    ):
        for node in ecg.nodes:
            nodes.setdefault(node.node_id, node)
        # `extract_ecgs` already filtered to topology, so every subtype here is
        # one of RELATIONS; the check is a tripwire for a future subtype, not a filter.
        for head, subtype, tail in ecg.edges:
            if subtype not in RELATIONS:
                raise SystemExit(f"unexpected ECG subtype {subtype!r}")
            triples.append((ecg.nodes[head].node_id, subtype, ecg.nodes[tail].node_id))
    return nodes, triples


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--unit", type=Path, default=Path("runs/stages/E3/e3-v61-20260917"))
    parser.add_argument("--train", type=Path, default=Path("data/processed/maven_ere/train.jsonl"))
    parser.add_argument("--valid", type=Path, default=Path("data/processed/maven_ere/valid.jsonl"))
    parser.add_argument("--min-nodes", type=int, default=4, help="must match the unit's freeze")
    parser.add_argument("--valid-fraction", type=float, default=0.03,
                        help="slice of the *training* triples held out as the KGC dev set. "
                             "Never the test queries: their trainer selects a checkpoint on it")
    parser.add_argument("--seed", type=int, default=209)
    parser.add_argument("--output", type=Path, default=Path("runs/stages/E3/kgc/CGEP-MAVEN"))
    args = parser.parse_args()

    manifest = json.loads((args.unit / "manifest.json").read_text(encoding="utf-8"))
    on_disk = sha256_file(args.unit / "queries.jsonl")
    if on_disk != manifest["unit"]["sha256"]:
        raise SystemExit(f"unit drifted: {on_disk} != frozen {manifest['unit']['sha256']}")
    if args.min_nodes != manifest["generator"]["params"]["min_nodes"]:
        raise SystemExit("--min-nodes differs from the unit's freeze; the ECGs would not match")

    queries = list(read_jsonl(args.unit / "queries.jsonl"))
    nodes, triples = _collect([args.train, args.valid], args.min_nodes)

    unknown = {
        node
        for row in queries
        for node in (row["anchor"], row["gold"], *row["candidates"])
        if node not in nodes
    }
    if unknown:
        raise SystemExit(f"{len(unknown)} unit nodes are in no ECG; the splits do not match")

    ent_ids = {node_id: i for i, node_id in enumerate(sorted(nodes))}
    rel_ids = {name: i for i, name in enumerate(RELATIONS)}

    # Every query edge leaves the training graph. One instance's query edge is
    # another instance's context inside the same ECG, so excluding them per
    # instance is impossible in a single static KG -- all 1,908 come out.
    held_out = {(row["anchor"], row["relation"], row["gold"]) for row in queries}
    train_triples = sorted({t for t in triples if t not in held_out})
    still_leaked = held_out & set(train_triples)
    if still_leaked:
        raise SystemExit(f"{len(still_leaked)} query edges survived into the training graph")

    rng = random.Random(args.seed)
    rng.shuffle(train_triples)
    cut = int(len(train_triples) * args.valid_fraction)
    dev_triples, train_triples = train_triples[:cut], sorted(train_triples[cut:])

    args.output.mkdir(parents=True, exist_ok=True)
    _numbered(args.output / "entity2id.txt",
              [f"{node_id}\t{i}" for node_id, i in ent_ids.items()])
    _numbered(args.output / "relation2id.txt", [f"{name}\t{i}" for name, i in rel_ids.items()])
    _numbered(args.output / "entityid2name.txt",
              [f"{i}\t{nodes[n].trigger}" for n, i in ent_ids.items()])
    _numbered(args.output / "entityid2description.txt",
              [f"{i}\t{nodes[n].sentence}" for n, i in ent_ids.items()])
    _numbered(args.output / "relationid2name.txt",
              [f"{i}\t{RELATION_NAMES[name]}" for name, i in rel_ids.items()])

    def _write(stem: str, rows: list[tuple[str, str, str]]) -> None:
        _numbered(args.output / f"{stem}2id.txt",
                  [f"{ent_ids[h]} {ent_ids[t]} {rel_ids[r]}" for h, r, t in rows])
        _numbered(args.output / f"{stem}2id_name.txt",
                  [f"{nodes[h].trigger} | {nodes[t].trigger} | {RELATION_NAMES[r]}"
                   for h, r, t in rows])

    test_rows = [(row["anchor"], row["relation"], row["gold"]) for row in queries]
    _write("train", train_triples)
    _write("valid", dev_triples)
    _write("test", test_rows)

    # The one file their code does not have. CGEP ranks 512 named candidates, not
    # the whole entity set, so the scorer masks everything outside this line.
    candidates = args.output / "test_candidates.txt"
    _numbered(candidates,
              [" ".join(str(ent_ids[c]) for c in row["candidates"]) for row in queries])

    # Who still has structural signal after the query edges leave. This is the
    # number that decides how to read a KGC opponent's row, so it is computed
    # rather than assumed: CGEP's query rule makes the gold successor a leaf
    # (outdeg 0, indeg 1 in its ECG), so removing its one edge isolates it --
    # under *any* triple-level split, not just this one.
    in_graph = {e for h, _, t in train_triples for e in (h, t)}
    anchors = {h for h, _, _ in test_rows}
    golds = {t for _, _, t in test_rows}
    pool = {c for row in queries for c in row["candidates"]}
    coverage = {
        "entities_in_training_graph": len(in_graph),
        "anchors": len(anchors),
        "anchors_in_training_graph": len(anchors & in_graph),
        "golds": len(golds),
        "golds_in_training_graph": len(golds & in_graph),
        "candidate_pool": len(pool),
        "candidate_pool_in_training_graph": len(pool & in_graph),
    }

    report = {
        "schema_version": SCHEMA_VERSION,
        "fidelity": "FR-016 (b) transparent adaptation -- neither KGC opponent implements CGEP, "
                    "and SeDGPL's adaptation was never released",
        "unit": {"path": str(args.unit), "sha256": manifest["unit"]["sha256"]},
        "counts": {
            "entities": len(ent_ids),
            "relations": len(rel_ids),
            "train_triples": len(train_triples),
            "dev_triples": len(dev_triples),
            "test_queries": len(test_rows),
            "query_edges_removed_from_graph": len(held_out),
            "candidates_per_query": len(queries[0]["candidates"]),
        },
        "coverage": coverage,
        "differences_from_the_published_setting": [
            "the opponent's published task is KGC, not CGEP; this mapping is ours",
            "valid-split context edges train the KGC embeddings, where SeDGPL reads them "
            "only at inference",
            "valid entities in no surviving training triple keep an initialised structural "
            "embedding, so only the text half of the model speaks for them",
            "scoring is masked to the 512 named candidates of each query, not the entity set",
            "EVERY gold successor is isolated in the training graph: CGEP picks query edges "
            "whose tail has outdeg 0 and indeg 1, so removing the query edge removes that "
            "node's only edge. Any KGC model that scores candidates through a learned "
            "per-entity structural embedding is therefore biased against the correct answer, "
            "and this holds under any triple-level split. SeDGPL is not: it scores by token "
            "id over a vocabulary built across train and test",
            "the KGC dev set is a seeded slice of the training triples; the 1,908 CGEP "
            "queries are never used for checkpoint selection",
        ],
        "digests": {
            "test_query_ids": id_digest(row["instance_id"] for row in queries),
            "candidates": hashlib.sha256(candidates.read_bytes()).hexdigest(),
        },
    }
    (args.output / "export_manifest.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    c = report["counts"]
    print(
        f"[kgc] {c['entities']} entities  {c['relations']} relations\n"
        f"[kgc] train={c['train_triples']} dev={c['dev_triples']} test={c['test_queries']} "
        f"(removed {c['query_edges_removed_from_graph']} query edges from the graph)\n"
        f"[kgc] in training graph: anchors {coverage['anchors_in_training_graph']}"
        f"/{coverage['anchors']}  golds {coverage['golds_in_training_graph']}"
        f"/{coverage['golds']}  candidate pool "
        f"{coverage['candidate_pool_in_training_graph']}/{coverage['candidate_pool']}\n"
        f"[kgc] wrote {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
