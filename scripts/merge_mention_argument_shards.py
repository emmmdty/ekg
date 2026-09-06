#!/usr/bin/env python
"""Merge and validate deterministic mention-argument inference shards."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

from predict_mention_arguments import _requests

from ekg.core.protocol import load_manifest_ids
from ekg.nodes.predicted_arguments import apply_predicted_arguments
from ekg.relations.data.maven_ere import load_maven_ere


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ordered_rows(rows: list[dict], expected_ids: list[str]) -> list[dict]:
    by_id = {}
    for row in rows:
        mention_id = str(row.get("mention_id", ""))
        if not mention_id or mention_id in by_id:
            raise ValueError(f"duplicate or empty mention prediction: {mention_id!r}")
        by_id[mention_id] = row
    expected = set(expected_ids)
    missing, extra = expected - by_id.keys(), by_id.keys() - expected
    if missing or extra:
        raise ValueError(f"missing predictions={len(missing)} extra predictions={len(extra)}")
    return [by_id[mention_id] for mention_id in expected_ids]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ere", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path, nargs="+")
    parser.add_argument("--shards", required=True, type=Path, nargs="+")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        parser.error(f"output directory is not empty: {args.output}")

    wanted = [doc_id for manifest in args.manifest for doc_id in load_manifest_ids(manifest)]
    if len(wanted) != len(set(wanted)):
        parser.error("manifests overlap or contain duplicate document IDs")
    by_id = {doc.doc_id: doc for doc in load_maven_ere(args.ere)}
    missing_docs = set(wanted) - by_id.keys()
    if missing_docs:
        parser.error(f"manifest documents missing from ERE source: {len(missing_docs)}")
    docs = [by_id[doc_id] for doc_id in wanted]
    expected_ids = [row["mention_id"] for row in _requests(docs)]

    shard_records = []
    rows = []
    model_ids = set()
    shard_indices = set()
    expected_count = len(args.shards)
    for prediction_path in args.shards:
        metadata_path = prediction_path.parent / "run_metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata.get("schema_version") != "ekg.mention_arguments.v1":
            raise ValueError(f"bad shard schema: {prediction_path}")
        if metadata.get("status") != "complete" or metadata.get("final_valid_accessed"):
            raise ValueError(f"incomplete or contaminated shard: {prediction_path}")
        if metadata.get("num_shards") != expected_count:
            raise ValueError(f"shard-count mismatch: {prediction_path}")
        if metadata.get("predictions_sha256") != _sha256(prediction_path):
            raise ValueError(f"shard prediction hash mismatch: {prediction_path}")
        model_ids.add(metadata.get("model_id"))
        shard_indices.add(metadata.get("shard_index"))
        shard_rows = [
            json.loads(line)
            for line in prediction_path.read_text(encoding="utf-8").splitlines()
            if line
        ]
        if len(shard_rows) != metadata.get("mentions"):
            raise ValueError(f"shard row-count mismatch: {prediction_path}")
        rows.extend(shard_rows)
        shard_records.append(
            {
                "path": str(prediction_path),
                "predictions_sha256": _sha256(prediction_path),
                "metadata_sha256": _sha256(metadata_path),
                "mentions": len(shard_rows),
                "shard_index": metadata.get("shard_index"),
            }
        )
    if len(model_ids) != 1 or shard_indices != set(range(expected_count)):
        raise ValueError("shards do not have one model and every expected index")

    merged = ordered_rows(rows, expected_ids)
    args.output.mkdir(parents=True)
    output = args.output / "predictions.jsonl"
    output.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in merged),
        encoding="utf-8",
    )
    apply_predicted_arguments(docs, output)
    status_counts = Counter(row["status"] for row in merged)
    rejected_fillers = sum(len(row.get("rejected", [])) for row in merged)
    metadata = {
        "schema_version": "ekg.mention_arguments_merged.v1",
        "status": "complete",
        "command_argv": list(sys.argv),
        "model_id": model_ids.pop(),
        "documents": len(docs),
        "mentions": len(merged),
        "prediction_status_counts": dict(sorted(status_counts.items())),
        "rejected_fillers": rejected_fillers,
        "source_sha256": _sha256(args.ere),
        "manifest_sha256": {str(path): _sha256(path) for path in args.manifest},
        "predictions_sha256": _sha256(output),
        "shards": sorted(shard_records, key=lambda row: row["shard_index"]),
        "final_valid_accessed": False,
    }
    (args.output / "run_metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"merged {len(merged)} predictions from {expected_count} shards")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
