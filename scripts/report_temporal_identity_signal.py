#!/usr/bin/env python
"""Train-only C5 temporal feasibility audit; no model or clustering intervention.

Sentence DATE surfaces are observable proxies, not event time anchors. Gold
event-level BEFORE edges reveal distinct gold identities by construction and
are reported separately; they cannot certify a deployable coreference signal.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

from ekg.core.stage_bundle import sha256_file
from ekg.nodes.coref import HARD_SIMILARITY, trigger_similarity

STATES = ("same_date_surface", "different_date_surface", "unknown_date")
BUCKETS = ("all_same_type", "high_similarity_cross_sentence")


def validate_manifest(manifest):
    if manifest["dataset"] != "maven_ere" or manifest["split_role"] != "train":
        raise ValueError("temporal signal audit is train-only")
    ids = manifest["doc_ids"]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate manifest document")
    if not ids or len(ids) != manifest["doc_count"]:
        raise ValueError("manifest document count mismatch")
    return set(ids)


def sentence_dates(record):
    surfaces = defaultdict(set)
    seen = set()
    for timex in record["TIMEX"]:
        if timex["id"] in seen:
            raise ValueError("duplicate TIMEX id")
        seen.add(timex["id"])
        sent, (start, end) = timex["sent_id"], timex["offset"]
        if not (0 <= sent < len(record["tokens"])
                and 0 <= start < end <= len(record["tokens"][sent])):
            raise ValueError("invalid TIMEX offset")
        surface = " ".join(record["tokens"][sent][start:end])
        if surface != timex["mention"]:
            raise ValueError("TIMEX surface/token mismatch")
        if timex["type"] == "DATE":
            surfaces[sent].add(surface.casefold())
    return {sent: next(iter(values)) if len(values := surfaces[sent]) == 1 else None
            for sent in range(len(record["tokens"]))}


def empty_buckets():
    return {bucket: {state: {"coreferent": 0, "noncoreferent": 0} for state in STATES}
            for bucket in BUCKETS}


def audit_document(record):
    dates = sentence_dates(record)
    event_ids, mentions = {}, {}
    by_type = defaultdict(list)
    for event in record["events"]:
        if event["id"] in event_ids:
            raise ValueError("duplicate event id")
        event_ids[event["id"]] = event
        for mention in event["mention"]:
            if mention["id"] in mentions:
                raise ValueError("duplicate mention id")
            sent, (start, end) = mention["sent_id"], mention["offset"]
            if not (0 <= sent < len(record["tokens"])
                    and 0 <= start < end <= len(record["tokens"][sent])):
                raise ValueError("invalid mention offset")
            mentions[mention["id"]] = (event["id"], mention)
            by_type[event["type"]].append((event["id"], mention))
    known = set(event_ids) | {timex["id"] for timex in record["TIMEX"]}
    before_pairs = 0
    for subtype, edges in record["temporal_relations"].items():
        for left, right in edges:
            if left not in known or right not in known:
                raise ValueError("unknown temporal endpoint")
            if left == right:
                raise ValueError("self temporal edge")
            if subtype == "BEFORE" and left in event_ids and right in event_ids:
                a, b = event_ids[left], event_ids[right]
                if a["type"] == b["type"]:
                    before_pairs += len(a["mention"]) * len(b["mention"])
    buckets = empty_buckets()
    similarities = {}
    for group in by_type.values():
        ordered = sorted(group, key=lambda row: (row[1]["sent_id"], row[1]["offset"][0],
                                                row[1]["id"]))
        for (left_event, left), (right_event, right) in combinations(ordered, 2):
            left_date, right_date = dates[left["sent_id"]], dates[right["sent_id"]]
            state = ("unknown_date" if left_date is None or right_date is None else
                     "same_date_surface" if left_date == right_date else "different_date_surface")
            label = "coreferent" if left_event == right_event else "noncoreferent"
            buckets["all_same_type"][state][label] += 1
            if left["sent_id"] == right["sent_id"]:
                continue
            key = (left["trigger_word"], right["trigger_word"])
            if key not in similarities:
                similarities[key] = trigger_similarity(*key)
            if similarities[key] >= HARD_SIMILARITY:
                buckets["high_similarity_cross_sentence"][state][label] += 1
    return {"id": record["id"], "mentions": len(mentions), "timex": len(record["TIMEX"]),
            "sentences": len(dates), "unique_date_sentences": sum(v is not None
                                                                    for v in dates.values()),
            "pairs": buckets, "gold_before": {"same_type_mention_pairs": before_pairs,
                                               "identity_circularity": True}}


def audit_source(source, manifest_path, output):
    manifest = json.loads(manifest_path.read_text())
    ids = validate_manifest(manifest)
    if sha256_file(source) != manifest["source_sha256"]:
        raise ValueError("source hash differs from frozen manifest")
    detail_path = output.with_suffix(".documents.jsonl")
    if output.exists() or detail_path.exists():
        raise FileExistsError("audit output already exists")
    rows, seen = [], set()
    with source.open() as handle:
        for line in handle:
            record = json.loads(line)
            if record["id"] not in ids:
                continue
            if record["id"] in seen:
                raise ValueError("duplicate source document")
            seen.add(record["id"])
            rows.append(audit_document(record))
    if seen != ids:
        raise ValueError("manifest/source coverage mismatch")
    counts, buckets = Counter(), empty_buckets()
    for row in rows:
        counts.update({key: row[key] for key in
                       ("mentions", "timex", "sentences", "unique_date_sentences")})
        counts["gold_before_same_type_pairs"] += row["gold_before"]["same_type_mention_pairs"]
        for bucket in BUCKETS:
            for state in STATES:
                for label in ("coreferent", "noncoreferent"):
                    buckets[bucket][state][label] += row["pairs"][bucket][state][label]
    report = {"schema_version": "ekg.temporal_identity_audit.v1", "documents": len(rows),
              "scope": "frozen train only; exploratory feasibility; not model results",
              "final_valid_accessed": False, "counts": dict(counts), "pairs": buckets,
              "input_sha256": {str(p): sha256_file(p) for p in (source, manifest_path)},
              "script_sha256": sha256_file(Path(__file__)),
              "high_similarity": HARD_SIMILARITY,
              "limitations": ["DATE surfaces are sentence proxies, not event time anchors",
                               "Different surfaces can denote identical or overlapping times",
                               "Missing/ambiguous DATE input is unknown, not disagreement",
                               "TIMEX spans are supplied annotations, not predicted detection",
                               "Gold BEFORE endpoints are distinct gold clusters by construction",
                               "No predictions, MUC effect, power or mechanism admission here"]}
    output.parent.mkdir(parents=True, exist_ok=True)
    with detail_path.open("x") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    report["documents_sha256"] = sha256_file(detail_path)
    with output.open("x") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("source", "manifest", "output"):
        parser.add_argument(f"--{option}", required=True, type=Path)
    args = parser.parse_args()
    report = audit_source(args.source, args.manifest, args.output)
    print(json.dumps({key: report[key] for key in ("documents", "counts", "pairs")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
