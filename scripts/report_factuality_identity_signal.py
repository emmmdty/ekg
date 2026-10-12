#!/usr/bin/env python
"""Train-only factuality/identity oracle audit; never a deployable prediction."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from itertools import combinations, combinations_with_replacement
from pathlib import Path

from ekg.core.stage_bundle import sha256_file
from ekg.nodes.coref import HARD_SIMILARITY, trigger_similarity

LABELS = ("CT+", "CT-", "PS+", "PS-", "Uu")
BUCKETS = ("all_same_type", "high_similarity_cross_sentence")


def validate_manifest(manifest, dataset):
    if manifest["dataset"] != dataset or manifest["split_role"] != "train":
        raise ValueError("factuality identity audit is train-only")
    ids = manifest["doc_ids"]
    if not ids or len(set(ids)) != len(ids) or len(ids) != manifest["doc_count"]:
        raise ValueError("invalid manifest document population")
    return set(ids)


def mention_index(record):
    result = {}
    for event in record["events"]:
        for mention in event["mention"]:
            if mention["id"] in result:
                raise ValueError("duplicate mention")
            result[mention["id"]] = (event["id"], event["type"], mention)
    return result


def empty_pairs():
    return {bucket: {"|".join(pair): {"coreferent": 0, "noncoreferent": 0}
                     for pair in combinations_with_replacement(LABELS, 2)} for bucket in BUCKETS}


def audit_document(ere, fact, *, observations=None):
    if ere["id"] != fact["id"] or ere["tokens"] != fact["tokens"]:
        raise ValueError("document/token alignment mismatch")
    mentions, annotations = mention_index(ere), mention_index(fact)
    if set(mentions) != set(annotations):
        raise ValueError("mention population alignment mismatch")
    if observations is not None and set(observations) != set(mentions):
        raise ValueError("observation coverage mismatch")
    by_type, clusters = defaultdict(list), defaultdict(set)
    labels = Counter()
    for mid, (event_id, event_type, mention) in mentions.items():
        _, fact_type, annotation = annotations[mid]
        if fact_type != event_type or any(mention[k] != annotation[k]
                                         for k in ("sent_id", "offset", "trigger_word")):
            raise ValueError("type/span alignment mismatch")
        sent, (start, end) = mention["sent_id"], mention["offset"]
        if not (0 <= sent < len(ere["tokens"])
                and 0 <= start < end <= len(ere["tokens"][sent])):
            raise ValueError("span alignment invalid")
        label = annotation["factuality"] if observations is None else observations[mid]
        if label not in LABELS:
            raise ValueError(f"unknown factuality label: {label!r}")
        labels[label] += 1
        clusters[event_id].add(label)
        by_type[event_type].append((event_id, mention, label))
    pairs = empty_pairs()
    for group in by_type.values():
        for (left_event, left, a), (right_event, right, b) in combinations(group, 2):
            key = "|".join(sorted((a, b), key=LABELS.index))
            identity = "coreferent" if left_event == right_event else "noncoreferent"
            pairs["all_same_type"][key][identity] += 1
            if left["sent_id"] != right["sent_id"] and trigger_similarity(
                    left["trigger_word"], right["trigger_word"]) >= HARD_SIMILARITY:
                pairs["high_similarity_cross_sentence"][key][identity] += 1
    return {"id": ere["id"], "mentions": len(mentions), "label_counts": dict(labels),
            "label_source": "gold_factuality" if observations is None else "predicted_factuality",
            "gold_clusters": len(clusters),
            "mixed_label_gold_clusters": sum(len(values) > 1 for values in clusters.values()),
            "pairs": pairs}


def load_train(source, manifest_path, dataset):
    manifest = json.loads(manifest_path.read_text())
    ids = validate_manifest(manifest, dataset)
    if sha256_file(source) != manifest["source_sha256"]:
        raise ValueError("source hash differs from frozen manifest")
    records = {}
    with source.open() as handle:
        for line in handle:
            record = json.loads(line)
            if record["id"] not in ids:
                continue
            if record["id"] in records:
                raise ValueError("duplicate source document")
            records[record["id"]] = record
    if set(records) != ids:
        raise ValueError("manifest/source coverage mismatch")
    return records


def load_observations(path, source):
    summary_path = path.parent / "summary.json"
    summary = json.loads(summary_path.read_text())
    provenance_path = path.parent / "provenance.json"
    provenance = json.loads(provenance_path.read_text())
    if (sha256_file(path) != summary["probabilities_sha256"]
            or sha256_file(summary_path) != provenance["summary_sha256"]
            or sha256_file(source) != provenance["input_sha256"][str(source)]
            or summary["consumer_evaluation_labels_accessed"] is not False
            or summary["diagnostic_only"] is not True or summary["seed"] != 13
            or set(summary["class_order"]) != set(LABELS)):
        raise ValueError("observation provenance/role mismatch")
    by_doc = defaultdict(dict)
    for line in path.read_text().splitlines():
        row = json.loads(line)
        doc_id, mid = row["doc_id"], row["mention_id"]
        prefix, bare = mid.split("::", 1)
        values = row["probabilities"]
        if (prefix != doc_id or bare in by_doc[doc_id] or len(values) != len(LABELS)
                or not all(math.isfinite(p) and 0 <= p <= 1 for p in values)
                or not math.isclose(sum(values), 1.0, abs_tol=1e-6)
                or row["label"] != summary["class_order"][max(range(len(values)),
                                                             key=values.__getitem__)]):
            raise ValueError("invalid or duplicate observation")
        by_doc[doc_id][bare] = row["label"]
    return by_doc


def audit_sources(ere_source, fact_source, ere_manifest, fact_manifest, output, observations=None):
    detail = output.with_suffix(".documents.jsonl")
    if output.exists() or detail.exists():
        raise FileExistsError("audit output already exists")
    ere = load_train(ere_source, ere_manifest, "maven_ere")
    fact = load_train(fact_source, fact_manifest, "maven_fact")
    if set(ere) != set(fact):
        raise ValueError("cross-dataset train document alignment mismatch")
    observed = None if observations is None else load_observations(observations, fact_source)
    if observed is not None and set(observed) != set(ere):
        raise ValueError("observation document coverage mismatch")
    rows = [audit_document(ere[doc_id], fact[doc_id],
                           observations=None if observed is None else observed[doc_id])
            for doc_id in sorted(ere)]
    pairs, counts, labels = empty_pairs(), Counter(), Counter()
    for row in rows:
        counts.update({key: row[key] for key in
                       ("mentions", "gold_clusters", "mixed_label_gold_clusters")})
        labels.update(row["label_counts"])
        for bucket in BUCKETS:
            for key, values in row["pairs"][bucket].items():
                for identity, count in values.items():
                    pairs[bucket][key][identity] += count
    inputs = [ere_source, fact_source, ere_manifest, fact_manifest]
    if observations is not None:
        inputs += [observations, observations.parent / "summary.json",
                   observations.parent / "provenance.json"]
    report = {"schema_version": "ekg.factuality_identity_audit.v1", "documents": len(rows),
              "scope": "frozen train only; exploratory signal; no coreference model results",
              "label_source": rows[0]["label_source"],
              "final_valid_accessed": False, "counts": dict(counts),
              "label_counts": dict(labels), "pairs": pairs, "high_similarity": HARD_SIMILARITY,
              "input_sha256": {str(p): sha256_file(p) for p in inputs},
              "script_sha256": sha256_file(Path(__file__)),
              "limitations": ["Gold factuality is not a deployable input",
                               "Train factuality contains LLM pre-annotation",
                               "Same identity can have source-relative factuality differences",
                               "FACT cluster IDs and arguments are not used",
                               "Pair counts do not establish MUC effect, power or novelty",
                               "Observed signal uses argmax classes, not calibrated certainty"]}
    output.parent.mkdir(parents=True, exist_ok=True)
    with detail.open("x") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    report["documents_sha256"] = sha256_file(detail)
    with output.open("x") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("ere-source", "fact-source", "ere-manifest", "fact-manifest", "output"):
        parser.add_argument(f"--{option}", required=True, type=Path)
    parser.add_argument("--observations", type=Path)
    args = parser.parse_args()
    result = audit_sources(args.ere_source, args.fact_source, args.ere_manifest,
                           args.fact_manifest, args.output, args.observations)
    print(json.dumps({key: result[key] for key in
                      ("documents", "counts", "label_counts", "pairs")}, indent=2))


if __name__ == "__main__":
    main()
