#!/usr/bin/env python
"""Diagnose BEFORE conflicts in an existing frozen anchor; never alter clusters.

This is exploratory analysis of previously inspected internal-dev predictions.
Gold evaluates conflicts but does not supply the temporal input. No MUC gain,
training, threshold selection or new-method admission is implied.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from itertools import combinations
from pathlib import Path

from report_coref_error_profile import official_clusterings

from ekg.core.protocol import load_manifest_ids
from ekg.core.stage_bundle import sha256_file
from ekg.nodes.coref import HARD_SIMILARITY, trigger_similarity
from ekg.relations.maven_ere_official import candidate_population_digest

COUNTERS = ("merged_pairs", "before_conflicts", "high_similarity_cross_sentence_merged",
            "high_similarity_cross_sentence_before")


def audit_conflicts(gold, prediction):
    _, clusters, mentions = official_clusterings(gold, prediction)
    known = set(mentions) | {timex["id"] for timex in gold["TIMEX"]}
    before = set()
    for left, right in prediction["temporal_relations"]["BEFORE"]:
        if left not in known or right not in known:
            raise ValueError("unknown predicted temporal endpoint")
        if left == right:
            raise ValueError("self predicted temporal edge")
        before.add(tuple(sorted((left, right))))
    types = {mention["id"]: event["type"] for event in gold["events"]
             for mention in event["mention"]}
    counts = {key: {"gold_same": 0, "gold_different": 0} for key in COUNTERS}
    for cluster in clusters:
        for left, right in combinations(sorted(cluster), 2):
            a, b = mentions[left], mentions[right]
            label = "gold_same" if a.event_id == b.event_id else "gold_different"
            counts["merged_pairs"][label] += 1
            conflict = (left, right) in before
            if conflict:
                counts["before_conflicts"][label] += 1
            target = (types[left] == types[right] and a.sent_id != b.sent_id
                      and trigger_similarity(a.trigger, b.trigger) >= HARD_SIMILARITY)
            if target:
                counts["high_similarity_cross_sentence_merged"][label] += 1
                if conflict:
                    counts["high_similarity_cross_sentence_before"][label] += 1
    return {"id": gold["id"], **counts}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("gold", "pred", "manifest", "anchor-metrics", "output"):
        parser.add_argument(f"--{option}", required=True, type=Path)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    if manifest["dataset"] != "maven_ere" or manifest["split_role"] != "internal-dev":
        raise ValueError("only existing internal-dev anchor diagnostic is permitted")
    ids = set(load_manifest_ids(args.manifest))
    anchor = json.loads(args.anchor_metrics.read_text())
    if (sha256_file(args.pred) != anchor["hashes"]["predictions"]
            or sha256_file(args.gold) != anchor["hashes"]["gold"]):
        raise ValueError("gold/predictions do not match frozen anchor metrics")
    detail = args.output.with_suffix(".documents.jsonl")
    if args.output.exists() or detail.exists():
        raise FileExistsError("diagnostic output already exists")
    gold_rows = [json.loads(line) for line in args.gold.read_text().splitlines() if line.strip()]
    pred_rows = [json.loads(line) for line in args.pred.read_text().splitlines() if line.strip()]
    gold = {row["id"]: row for row in gold_rows}
    pred = {row["id"]: row for row in pred_rows}
    if (len(gold) != len(gold_rows) or len(pred) != len(pred_rows)
            or set(gold) != ids or set(pred) != ids):
        raise ValueError("manifest/anchor document coverage mismatch")
    digest, population = candidate_population_digest(gold)
    if digest != anchor["population"]["candidate_id_digest"]:
        raise ValueError("frozen anchor candidate digest mismatch")
    rows = [audit_conflicts(gold[doc_id], pred[doc_id]) for doc_id in sorted(ids)]
    totals = {key: Counter() for key in COUNTERS}
    for row in rows:
        for key in COUNTERS:
            totals[key].update(row[key])
    report = {"schema_version": "ekg.temporal_coref_conflicts.v1", "documents": len(rows),
              "scope": "previously inspected internal-dev; exploratory diagnostic only",
              "final_valid_accessed": False, "candidate_digest": digest,
              "population": population, "counts": {key: dict(v) for key, v in totals.items()},
              "high_similarity": HARD_SIMILARITY,
              "input_sha256": {str(p): sha256_file(p) for p in
                               (args.gold, args.pred, args.manifest, args.anchor_metrics)},
              "script_sha256": sha256_file(Path(__file__)),
              "limitations": ["Pair counts are dependent; no MUC intervention or power",
                               "BEFORE denotes predicted time, never gold temporal edges",
                               "Anchor conflict behavior may not transfer to another scorer",
                               "This inspected unit cannot supply prospective confirmation"]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with detail.open("x") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    report["documents_sha256"] = sha256_file(detail)
    with args.output.open("x") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(report["counts"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
