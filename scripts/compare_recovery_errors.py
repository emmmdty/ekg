#!/usr/bin/env python
"""Compare cached causal/coreference errors without selecting a model or threshold.

Counts describe the frozen evaluation documents; they are not a new main metric
or evidence that a particular loss caused the difference. No model is loaded.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from itertools import combinations
from pathlib import Path

from ekg.core.stage_bundle import sha256_file
from ekg.relations.maven_ere_official import (
    gold_to_official_prediction,
    records_by_id,
    validate_official_predictions,
)


def positives(record: dict, family: str) -> set[tuple[str, ...]]:
    if family == "coreference":
        return {
            tuple(pair) for cluster in record["coreference"]
            for pair in combinations(sorted(cluster), 2)
        }
    if family == "causal":
        return {
            (subtype, head, tail)
            for subtype, pairs in record["causal_relations"].items()
            for head, tail in pairs
        }
    raise ValueError(f"unknown comparison family: {family}")


def compare(gold: dict, control: dict, candidate: dict, *, family: str) -> dict:
    population = validate_official_predictions(gold, control)
    validate_official_predictions(
        gold, candidate, expected_candidate_digest=population["candidate_id_digest"]
    )
    documents = []
    total: Counter[str] = Counter()
    for doc_id in sorted(gold):
        g = positives(gold_to_official_prediction(gold[doc_id]), family)
        b, c = positives(control[doc_id], family), positives(candidate[doc_id], family)
        counts = {
            "recovered_positives": len((c - b) & g),
            "lost_positives": len((b - c) & g),
            "removed_false_positives": len((b - c) - g),
            "added_false_positives": len((c - b) - g),
            "control_true_positives": len(b & g),
            "candidate_true_positives": len(c & g),
            "control_false_positives": len(b - g),
            "candidate_false_positives": len(c - g),
            "gold_positives": len(g),
        }
        total.update(counts)
        documents.append({"doc_id": doc_id, **counts})
    return {
        "schema_version": "ekg.recovery_error_comparison.v1",
        "diagnostic_only": True,
        "family": family,
        "population": population,
        "total": dict(total),
        "documents": documents,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", required=True, type=Path)
    parser.add_argument("--control", required=True, type=Path)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--family", required=True, choices=("causal", "coreference"))
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    paths = {name: getattr(args, name) for name in ("gold", "control", "candidate")}
    records = {
        name: records_by_id(
            (json.loads(line) for line in path.read_text().splitlines() if line.strip()),
            source=str(path),
        ) for name, path in paths.items()
    }
    report = compare(**records, family=args.family)
    report["inputs"] = {
        name: {"path": str(path), "sha256": sha256_file(path)}
        for name, path in paths.items()
    }
    report["script_sha256"] = sha256_file(Path(__file__))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report["total"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
