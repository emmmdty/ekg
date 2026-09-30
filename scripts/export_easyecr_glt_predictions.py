#!/usr/bin/env python
"""Convert G-19's frozen raw clusters to MAVEN-ERE official prediction shape.

This is intentionally a post-inference step.  It may read labelled evaluation
records only to validate identities and to supply the required all-NONE fields
for relation families that Global-Local Topic does not predict.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from ekg.relations.maven_ere_official import (
    OfficialProtocolError,
    candidate_population_digest,
    empty_official_prediction,
    records_by_id,
    validate_official_predictions,
)


class G19ExportError(ValueError):
    """Raw G-19 clusters cannot be safely converted to official shape."""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    try:
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    except (OSError, json.JSONDecodeError) as exc:
        raise G19ExportError(f"cannot read JSONL: {path}") from exc
    if not all(isinstance(row, dict) for row in rows):
        raise G19ExportError(f"{path} contains a non-object JSONL row")
    return rows


def _event_mention_ids(record: dict[str, Any]) -> set[str]:
    return {
        str(mention["id"])
        for event in record.get("events", [])
        for mention in event.get("mention", [])
    }


def convert(
    gold_rows: list[dict[str, Any]], raw_rows: list[dict[str, Any]]
) -> tuple[list[dict], dict]:
    try:
        gold = records_by_id(gold_rows, source="G-19 labelled evaluation")
        raw = records_by_id(raw_rows, source="G-19 raw clusters")
    except OfficialProtocolError as exc:
        raise G19ExportError(str(exc)) from exc
    if set(gold) != set(raw):
        raise G19ExportError(
            "raw cluster document IDs differ from labelled evaluation: "
            f"missing={sorted(set(gold) - set(raw))} extra={sorted(set(raw) - set(gold))}"
        )

    predictions: list[dict] = []
    for doc_id, record in gold.items():
        row = raw[doc_id]
        clusters = row.get("clusters")
        mention_ids = row.get("mention_ids")
        if not isinstance(clusters, list) or not isinstance(mention_ids, list):
            raise G19ExportError(f"{doc_id} raw row needs clusters and mention_ids lists")
        known = _event_mention_ids(record)
        if set(map(str, mention_ids)) != known or len(mention_ids) != len(known):
            raise G19ExportError(f"{doc_id} raw mention coverage differs from frozen gold mentions")
        assigned: list[str] = []
        converted_clusters: list[list[str]] = []
        for cluster in clusters:
            if not isinstance(cluster, list) or not cluster:
                raise G19ExportError(f"{doc_id} contains an empty/malformed raw cluster")
            members = [str(item) for item in cluster]
            if len(members) != len(set(members)):
                raise G19ExportError(f"{doc_id} repeats a mention inside one raw cluster")
            converted_clusters.append(members)
            assigned.extend(members)
        if set(assigned) != known or len(assigned) != len(known):
            raise G19ExportError(f"{doc_id} raw clusters do not partition frozen gold mentions")
        prediction = empty_official_prediction(record)
        prediction["coreference"] = converted_clusters
        predictions.append(prediction)
    try:
        exported = records_by_id(predictions, source="G-19 export")
        population = validate_official_predictions(gold, exported)
    except OfficialProtocolError as exc:
        raise G19ExportError(str(exc)) from exc
    return predictions, population


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", required=True, type=Path)
    parser.add_argument("--raw-clusters", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.manifest.exists():
        raise SystemExit("G-19 export outputs are immutable and must not already exist")
    predictions, population = convert(_read_jsonl(args.gold), _read_jsonl(args.raw_clusters))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "".join(json.dumps(item, sort_keys=True) + "\n" for item in predictions), encoding="utf-8"
    )
    gold = records_by_id(_read_jsonl(args.gold), source=str(args.gold))
    digest, counts = candidate_population_digest(gold)
    args.manifest.write_text(
        json.dumps(
            {
                "schema_version": "ekg.easyecr_glt_official_export.v1",
                "raw_clusters_sha256": sha256_file(args.raw_clusters),
                "gold_sha256": sha256_file(args.gold),
                "predictions_sha256": sha256_file(args.output),
                "candidate_population_digest": digest,
                "candidate_population_counts": counts,
                "validated_population": population,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"[g19] wrote official-shape predictions: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
