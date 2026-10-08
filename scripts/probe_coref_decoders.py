#!/usr/bin/env python
"""Export frozen C5 pair probabilities once; replay two fixed cluster decoders.

Antecedent decoding is a transparent adaptation of binary pair probabilities,
not a reproduction of the official antecedent-trained model. No threshold sweep.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from itertools import combinations
from pathlib import Path

from ekg.core.stage_bundle import sha256_file

UTILS_SHA256 = "5c04f98972addcf041eb7c0a03a6bd536334741291f04291cec9d51a7a773406"


def validate_cache_record(row):
    ids, types = row["mentions"], row["types"]
    if len(ids) != len(set(ids)) or len(types) != len(ids):
        raise ValueError("duplicate mentions or mismatched types")
    if (len(row["average_order"]) != len(ids)
            or set(row["average_order"]) != set(ids)):
        raise ValueError("average-link mention order mismatch")
    expected = {(a, b) for (i, a), (j, b) in combinations(enumerate(ids), 2)
                if types[i] == types[j]}
    seen = set()
    for a, b, probability in row["scores"]:
        if (a, b) not in expected or (a, b) in seen:
            raise ValueError("duplicate, future or out-of-universe pair")
        if not math.isfinite(probability) or not 0 <= probability <= 1:
            raise ValueError("invalid pair probability")
        seen.add((a, b))
    if seen != expected:
        raise ValueError("missing cached candidates")


def decode_official(row, utils: Path):
    validate_cache_record(row)
    if sha256_file(utils) != UTILS_SHA256:
        raise ValueError("official decoder source hash mismatch")
    import torch

    spec = importlib.util.spec_from_file_location("pinned_maven_coref_utils", utils)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    ids = row["mentions"]
    if not ids:
        return []
    index = {m: i for i, m in enumerate(ids)}
    matrix = torch.full((len(ids), len(ids)), -1.0, dtype=torch.float64)
    matrix.diagonal().fill_(0.5)
    for a, b, probability in row["scores"]:
        matrix[index[b], index[a]] = probability
    # Argmax of p is identical to argmax of logit(p) against the zero-logit dummy.
    # p=.5 ties choose the earliest antecedent, matching the upstream torch argmax.
    clusters, _ = module.get_predicted_clusters(matrix)
    return sorted(sorted(ids[i] for i in cluster) for cluster in clusters if len(cluster) > 1)


def decode_average(row):
    validate_cache_record(row)
    from ekg.nodes.canonical import _cluster_mentions, _symmetric

    scores = {(a, b): p for a, b, p in row["scores"]}
    clusters, _, _ = _cluster_mentions(row["average_order"], _symmetric(scores), 0.7, 0.0)
    return sorted(sorted(cluster) for cluster in clusters if len(cluster) > 1)


def require_same_clusters(original, replayed):
    expected = sorted(sorted(c) for c in original["coreference"] if len(c) > 1)
    if expected != replayed:
        raise ValueError(f"average decoder failed to reproduce frozen prediction: {original['id']}")


def export(args):
    from build_maven_ere_submission import strip_to_test_shape

    from ekg.core.protocol import load_manifest_ids
    from ekg.nodes.coref import SupervisedCoreferenceScorer, candidate_coref_pairs
    from ekg.nodes.predicted_arguments import apply_predicted_arguments
    from ekg.relations.data.maven_ere import _parse_unlabeled

    ids = set(load_manifest_ids(args.manifest))
    docs = [_parse_unlabeled(strip_to_test_shape(json.loads(line)))[0]
            for line in args.source.read_text().splitlines()
            if line.strip() and str(json.loads(line)["id"]) in ids]
    if {d.doc_id for d in docs} != ids or len(docs) != len(ids):
        raise ValueError("manifest/source coverage mismatch")
    apply_predicted_arguments(docs, args.arguments, allow_extra=True)
    scorer = SupervisedCoreferenceScorer(checkpoint_path=str(args.checkpoint))
    with args.output.open("x") as handle:
        for doc in docs:
            nodes = sorted(doc.nodes, key=lambda n: (n.trigger_evidence[0].char_start, n.event_id))
            pairs = candidate_coref_pairs(nodes)
            # The historical scorer's distance features use doc.nodes order.
            # Keep that order, even when it differs from textual antecedent order.
            scores = scorer.score(doc.nodes, pairs, doc.doc_text) if pairs else {}
            def bare(value):
                return value.split("::", 1)[-1]
            row = {"id": doc.doc_id, "mentions": [bare(n.event_id) for n in nodes],
                   "average_order": [bare(n.event_id) for n in doc.nodes],
                   "types": [n.event_type for n in nodes],
                   "scores": [[bare(a), bare(b), scores[(a, b)]] for a, b in pairs]}
            validate_cache_record(row)
            handle.write(json.dumps(row, allow_nan=False) + "\n")
    metadata = {"schema_version": "ekg.coref_pair_cache.v1", "diagnostic_only": True,
                "checkpoint_location": str(args.checkpoint.resolve()),
                "input_sha256": {str(p): sha256_file(p) for p in
                    (args.source, args.manifest, args.arguments, Path(__file__))},
                "checkpoint_sha256": {p.name: sha256_file(p)
                    for p in args.checkpoint.iterdir() if p.is_file()},
                "cache_sha256": sha256_file(args.output), "documents": len(docs)}
    with args.output.with_suffix(".metadata.json").open("x") as handle:
        json.dump(metadata, handle, indent=2)


def replay(args):
    rows = [json.loads(line) for line in args.cache.read_text().splitlines() if line.strip()]
    originals = [json.loads(line) for line in args.original.read_text().splitlines()
                 if line.strip()]
    original_by_id = {row["id"]: row for row in originals}
    if len({r["id"] for r in rows}) != len(rows):
        raise ValueError("duplicate cached documents")
    if len(original_by_id) != len(originals) or set(original_by_id) != {r["id"] for r in rows}:
        raise ValueError("frozen predictions/cache document coverage mismatch")
    args.output.mkdir(parents=True, exist_ok=False)
    for name, decoder in (("average", decode_average),
                          ("antecedent", lambda row: decode_official(row, args.utils))):
        with (args.output / f"{name}.jsonl").open("x") as handle:
            for row in rows:
                clusters = decoder(row)
                if name == "average":
                    require_same_clusters(original_by_id[row["id"]], clusters)
                prediction = {"id": row["id"], "coreference": clusters,
                              "temporal_relations": {k: [] for k in
                                  ("BEFORE", "OVERLAP", "CONTAINS", "SIMULTANEOUS",
                                   "ENDS-ON", "BEGINS-ON")},
                              "causal_relations": {"CAUSE": [], "PRECONDITION": []},
                              "subevent_relations": []}
                handle.write(json.dumps(prediction) + "\n")
    with (args.output / "provenance.json").open("x") as handle:
        json.dump({"cache_sha256": sha256_file(args.cache),
                   "original_predictions_sha256": sha256_file(args.original),
                   "decoder_sha256": sha256_file(args.utils),
                   "script_sha256": sha256_file(Path(__file__)),
                   "average_threshold": .7, "average_band": 0.0,
                   "antecedent_dummy_probability": .5,
                   "candidate_policy": "all same-type unordered pairs; textual order",
                   "fidelity": "FR-016(b): binary scores; official decoder only",
                   "diagnostic_only": True}, handle, indent=2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode", required=True)
    source = modes.add_parser("export")
    for option in ("source", "manifest", "arguments", "checkpoint", "output"):
        source.add_argument(f"--{option}", required=True, type=Path)
    cached = modes.add_parser("replay")
    for option in ("cache", "utils", "original", "output"):
        cached.add_argument(f"--{option}", required=True, type=Path)
    args = parser.parse_args()
    if args.mode == "export":
        args.output.parent.mkdir(parents=True, exist_ok=True)
        export(args)
    else:
        replay(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
