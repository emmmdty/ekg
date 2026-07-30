#!/usr/bin/env python
"""Build the MAVEN-ERE CodaLab submission (`test_prediction.jsonl` + `submission.zip`).

The official test split withholds the coreference clusters and every relation,
handing over only a flat `event_mentions` list, so this is the first time Ch1
(coreference) and Ch2 (relations) run as one pipeline: cluster the mentions,
then label every candidate mention pair.

Three facts read off the official scorer (`THU-KEG/MAVEN-ERE/evaluate.py`) decide
the output shape, and getting any of them wrong silently costs score:

* **Relations are scored per *mention* pair, not per event pair.** The scorer
  expands each gold cluster-level relation to every mention pair across the two
  clusters, then micro-averages over the positive labels. So emitting the
  extractor's raw per-pair output is exactly right, and `--propagate-coref`
  (off by default) additionally copies a predicted relation across the predicted
  clusters -- more recall, more risk, hence opt-in.
* **Pairs are ordered.** The scorer keys on `m1 + m2` with both directions
  enumerated separately, so a directed edge must not be mirrored.
* **Coreference singletons are free.** Any mention absent from the submitted
  clusters is scored as its own singleton, so only non-trivial clusters are
  written.

`--from-labeled` strips a labelled split (valid) down to the test shape and runs
the identical path over it. That dry run is not optional: CodaLab's submission
quota is limited and `EXPERIMENTS.md` §1 forbids tuning on test, so the format
and the numbers get checked against local gold *before* a submission is spent.

    # dry run on valid, then score with the official evaluate.py
    uv run python scripts/build_maven_ere_submission.py --from-labeled \\
        --test data/processed/maven_ere/valid.jsonl --predictor lexical \\
        --output runs/submission/valid_prediction.jsonl
"""

from __future__ import annotations

import argparse
import json
import zipfile
from collections import defaultdict
from pathlib import Path

from ekg.core.io import read_jsonl
from ekg.core.schema import RelationEdge, RelationType
from ekg.nodes.canonical import canonicalize
from ekg.nodes.coref import candidate_coref_pairs
from ekg.relations.data.maven_ere import RelationDocument, _parse_unlabeled

# Every key the scorer looks up must exist, empty or not: a missing key is read
# as "no prediction" for that whole subtype rather than an empty one.
TEMPORAL_SUBTYPES = ("BEFORE", "OVERLAP", "CONTAINS", "SIMULTANEOUS", "ENDS-ON", "BEGINS-ON")
CAUSAL_SUBTYPES = ("CAUSE", "PRECONDITION")

_FAMILY_KEY = {
    RelationType.TEMPORAL: "temporal_relations",
    RelationType.CAUSAL: "causal_relations",
    RelationType.SUBEVENT: "subevent_relations",
}


def strip_to_test_shape(record: dict) -> dict:
    """Turn a labelled MAVEN-ERE record into the test file's shape.

    Flattens `events` into `event_mentions` (carrying the event type down onto
    each mention, which is what the test file does) and drops every relation
    field. Used by `--from-labeled` so the dry run exercises the *same* code path
    the real submission will, rather than a lookalike.
    """
    mentions = [
        {**mention, "type": event.get("type", "Unknown"), "type_id": event.get("type_id")}
        for event in record.get("events", [])
        for mention in (event.get("mention") or event.get("mentions") or [])
    ]
    return {
        "id": record.get("id"),
        "title": record.get("title", ""),
        "tokens": record.get("tokens"),
        "sentences": record.get("sentences"),
        "event_mentions": mentions,
        "TIMEX": record.get("TIMEX", []),
    }


def _bare_id(namespaced: str) -> str:
    """`{doc_id}::{mention_id}` -> `mention_id`; the scorer wants the bare form."""
    return namespaced.split("::", 1)[1] if "::" in namespaced else namespaced


def predict_coreference(
    doc: RelationDocument, scorer, *, threshold: float, band: float
) -> list[list[str]]:
    """Non-singleton predicted clusters, as bare mention ids."""
    if len(doc.nodes) < 2:
        return []
    pairs = candidate_coref_pairs(doc.nodes)
    scores = scorer.score(doc.nodes, pairs, doc.doc_text) if pairs else {}
    result = canonicalize(doc.nodes, scores, threshold=threshold, band=band)
    return [
        sorted(_bare_id(m) for m in cluster)
        for cluster in result.clusters()
        if len(cluster) > 1
    ]


def _cluster_lookup(clusters: list[list[str]]) -> dict[str, list[str]]:
    return {m: cluster for cluster in clusters for m in cluster}


def relation_payload(
    edges: list[RelationEdge],
    *,
    threshold: float,
    clusters: list[list[str]] | None = None,
) -> dict:
    """Group admitted edges into the scorer's three relation fields.

    `clusters` turns on coreference propagation: a relation predicted between two
    mentions is also asserted between their cluster-mates, which is how the gold
    is expanded. Deduplicated, and self-pairs are dropped -- the scorer only
    enumerates `m1 != m2`, so a self-pair would raise a KeyError on its side.
    """
    by_key: dict[str, dict[str, set[tuple[str, str]]]] = {
        "temporal_relations": defaultdict(set),
        "causal_relations": defaultdict(set),
        "subevent_relations": defaultdict(set),
    }
    lookup = _cluster_lookup(clusters or [])
    for edge in edges:
        if edge.confidence < threshold:
            continue
        field = _FAMILY_KEY.get(edge.relation_type)
        if field is None:  # coreference never reaches the relation fields
            continue
        subtype = "subevent" if field == "subevent_relations" else (edge.subtype or "")
        head, tail = _bare_id(edge.head_id), _bare_id(edge.tail_id)
        heads = lookup.get(head, [head])
        tails = lookup.get(tail, [tail])
        for h in heads:
            for t in tails:
                if h != t:
                    by_key[field][subtype].add((h, t))

    payload: dict = {
        "temporal_relations": {
            s: sorted(list(p) for p in by_key["temporal_relations"].get(s, set()))
            for s in TEMPORAL_SUBTYPES
        },
        "causal_relations": {
            s: sorted(list(p) for p in by_key["causal_relations"].get(s, set()))
            for s in CAUSAL_SUBTYPES
        },
        "subevent_relations": sorted(
            list(p) for p in by_key["subevent_relations"].get("subevent", set())
        ),
    }
    return payload


def _build_scorer(name: str, checkpoint: str | None):
    if name == "lexical":
        from ekg.nodes.coref import LexicalCoreferenceScorer

        return LexicalCoreferenceScorer()
    from ekg.nodes.coref import SupervisedCoreferenceScorer

    if not checkpoint:
        raise SystemExit("--coref-predictor supervised needs --coref-checkpoint")
    return SupervisedCoreferenceScorer(checkpoint_path=checkpoint)


def _build_extractor(name: str, checkpoint: str | None):
    if name == "none":
        return None
    from ekg.relations.extractor.supervised import SupervisedRelationExtractor

    if not checkpoint:
        raise SystemExit("--relation-predictor supervised needs --relation-checkpoint")
    return SupervisedRelationExtractor(checkpoint_path=checkpoint, max_distance=None)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--test", type=Path,
        default=Path("data/processed/maven_ere/test_unlabeled.jsonl"),
    )
    parser.add_argument(
        "--from-labeled", action="store_true",
        help="input is a labelled split; strip it to the test shape first (dry run)",
    )
    parser.add_argument(
        "--coref-predictor", default="supervised", choices=("supervised", "lexical")
    )
    parser.add_argument("--coref-checkpoint")
    parser.add_argument(
        "--coref-threshold", type=float, default=0.7,
        help="Phase C's selected operating point; do not retune on test",
    )
    parser.add_argument("--coref-band", type=float, default=0.1)
    parser.add_argument(
        "--relation-predictor", default="supervised", choices=("supervised", "none")
    )
    parser.add_argument("--relation-checkpoint")
    parser.add_argument(
        "--relation-threshold", type=float, default=0.7,
        help="Phase A's selected threshold; do not retune on test",
    )
    parser.add_argument(
        "--propagate-coref", action="store_true",
        help="also assert each relation between the cluster-mates of its endpoints",
    )
    parser.add_argument("--limit", type=int, help="first N documents (smoke)")
    parser.add_argument(
        "--shard", metavar="K/N",
        help="process only documents with index %% N == K, so N processes can split the "
             "corpus across GPUs. Shards are merged by concatenation; document order "
             "within a shard is preserved and the scorer keys by id, so order is free",
    )
    parser.add_argument("--output", type=Path,
                        default=Path("runs/submission/test_prediction.jsonl"))
    parser.add_argument("--zip", dest="make_zip", action="store_true",
                        help="also write submission.zip next to the output")
    args = parser.parse_args()

    scorer = _build_scorer(args.coref_predictor, args.coref_checkpoint)
    extractor = _build_extractor(args.relation_predictor, args.relation_checkpoint)

    records = list(read_jsonl(args.test))
    if args.from_labeled:
        records = [strip_to_test_shape(r) for r in records]
    if args.limit:
        records = records[: args.limit]
    if args.shard:
        k, _, n = args.shard.partition("/")
        k, n = int(k), int(n)
        if not 0 <= k < n:
            raise SystemExit(f"--shard K/N needs 0 <= K < N, got {args.shard}")
        records = records[k::n]
        print(f"[submission] shard {k}/{n}: {len(records)} documents")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    n_clusters = n_rel = 0
    with args.output.open("w", encoding="utf-8") as fh:
        for index, record in enumerate(records, start=1):
            doc, _ = _parse_unlabeled(record)
            clusters = predict_coreference(
                doc, scorer, threshold=args.coref_threshold, band=args.coref_band
            )
            edges: list[RelationEdge] = []
            if extractor is not None and doc.nodes:
                from ekg.relations.extractor.base import ExtractionContext

                edges = extractor.extract(
                    list(doc.nodes), ExtractionContext(doc_text={doc.doc_id: doc.doc_text})
                )
            payload = relation_payload(
                edges,
                threshold=args.relation_threshold,
                clusters=clusters if args.propagate_coref else None,
            )
            n_clusters += len(clusters)
            n_rel += sum(len(v) for v in payload["temporal_relations"].values())
            n_rel += sum(len(v) for v in payload["causal_relations"].values())
            n_rel += len(payload["subevent_relations"])
            fh.write(
                json.dumps({"id": doc.doc_id, "coreference": clusters, **payload}) + "\n"
            )
            if index % 50 == 0:
                print(f"[submission] {index}/{len(records)} docs, "
                      f"{n_clusters} clusters, {n_rel} relations", flush=True)

    print(f"[submission] wrote {len(records)} documents to {args.output}")
    print(f"[submission] {n_clusters} non-singleton clusters, {n_rel} relation pairs")

    if args.make_zip:
        archive = args.output.parent / "submission.zip"
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
            # arcname strips the directory: the scorer expects the file at the root.
            zf.write(args.output, arcname="test_prediction.jsonl")
        print(f"[submission] wrote {archive}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
