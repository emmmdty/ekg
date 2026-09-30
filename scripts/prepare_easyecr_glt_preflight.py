#!/usr/bin/env python
"""Freeze the non-leaking EasyECR Global-Local Topic input triplet.

The published EasyECR recipe selects checkpoints and cluster thresholds on its
``dev`` input.  Project internal-dev is the frozen 291-document evaluation
unit, so it must be supplied only as an unlabeled ``test``-shape file.  This
script deterministically reserves a separate selection-dev subset from P1
train before any G-19 model result exists.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

EXPECTED_P1_PROTOCOL_SHA256 = "1e31a9acef39261f776f7ed4069fd73f4531e8d12b55779bfc0fbd74c67f9655"
SELECTION_NAMESPACE = "g19-selection-v1:"


class PreflightError(ValueError):
    """A G-19 input would violate its frozen split or provenance contract."""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PreflightError(f"cannot read JSON object: {path}") from exc
    if not isinstance(payload, dict):
        raise PreflightError(f"{path} must contain a JSON object")
    return payload


def _read_jsonl(path: Path) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    by_id: dict[str, dict[str, Any]] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise PreflightError(f"invalid JSON at {path}:{line_number}") from exc
        doc_id = record.get("id") if isinstance(record, dict) else None
        if not isinstance(doc_id, str) or not doc_id:
            raise PreflightError(f"missing string document id at {path}:{line_number}")
        if doc_id in by_id:
            raise PreflightError(f"duplicate document id in source: {doc_id}")
        records.append(record)
        by_id[doc_id] = record
    if not records:
        raise PreflightError(f"source is empty: {path}")
    return records, by_id


def _manifest_ids(path: Path, *, role: str, source_hash: str) -> list[str]:
    manifest = _read_json(path)
    if manifest.get("dataset") != "maven_ere" or manifest.get("split_role") != role:
        raise PreflightError(f"{path} is not the MAVEN-ERE {role} manifest")
    if manifest.get("source_sha256") != source_hash:
        raise PreflightError(f"{path} source digest differs from --source")
    ids = manifest.get("doc_ids")
    if not isinstance(ids, list) or not all(isinstance(item, str) and item for item in ids):
        raise PreflightError(f"{path} has invalid doc_ids")
    if len(ids) != len(set(ids)) or manifest.get("doc_count") != len(ids):
        raise PreflightError(f"{path} has duplicate IDs or an incorrect count")
    return ids


def _selection_ids(train_ids: list[str], size: int) -> list[str]:
    if not 0 < size < len(train_ids):
        raise PreflightError("--selection-size must be positive and smaller than P1 train")
    return sorted(
        train_ids,
        key=lambda doc_id: hashlib.sha256(f"{SELECTION_NAMESPACE}{doc_id}".encode()).hexdigest(),
    )[:size]


def _unlabeled_test_record(record: dict[str, Any]) -> dict[str, Any]:
    events = record.get("events")
    if not isinstance(events, list):
        raise PreflightError(f"source document {record['id']} has no event clusters")
    event_mentions: list[dict[str, Any]] = []
    for event in events:
        if not isinstance(event, dict) or not isinstance(event.get("mention"), list):
            raise PreflightError(f"source document {record['id']} has malformed event clusters")
        for mention in event["mention"]:
            if not isinstance(mention, dict):
                raise PreflightError(f"source document {record['id']} has malformed mention")
            event_mentions.append(
                {
                    **mention,
                    "type": event.get("type", "Unknown"),
                    "type_id": event.get("type_id"),
                }
            )
    return {
        "id": record["id"],
        "title": record.get("title", ""),
        "tokens": record.get("tokens", []),
        "sentences": record.get("sentences", []),
        "event_mentions": event_mentions,
        "TIMEX": record.get("TIMEX", []),
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    serialized = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path.write_text(serialized, encoding="utf-8")


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(
            json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records
        ),
        encoding="utf-8",
    )


def prepare(
    *,
    source: Path,
    train_manifest: Path,
    evaluation_manifest: Path,
    p1_protocol: Path,
    expected_p1_protocol_sha256: str,
    output: Path,
    selection_size: int,
) -> dict[str, Any]:
    if output.exists():
        raise PreflightError(f"output already exists: {output}")
    if sha256_file(p1_protocol) != expected_p1_protocol_sha256:
        raise PreflightError("P1 protocol digest differs from the frozen G-19 trust root")

    source_hash = sha256_file(source)
    source_records, source_by_id = _read_jsonl(source)
    train_ids = _manifest_ids(train_manifest, role="train", source_hash=source_hash)
    evaluation_ids = _manifest_ids(
        evaluation_manifest,
        role="internal-dev",
        source_hash=source_hash,
    )
    if set(train_ids) & set(evaluation_ids):
        raise PreflightError("P1 train and internal-dev overlap")
    if set(train_ids) | set(evaluation_ids) != set(source_by_id):
        raise PreflightError("P1 manifests do not exactly partition the source")

    selection_ids = _selection_ids(train_ids, selection_size)
    selection_set = set(selection_ids)
    training_set = set(train_ids) - selection_set
    evaluation_set = set(evaluation_ids)
    if training_set & evaluation_set or selection_set & evaluation_set:
        raise PreflightError("selection or training overlaps frozen evaluation")

    output.mkdir(parents=True)
    training_records = [record for record in source_records if record["id"] in training_set]
    selection_records = [record for record in source_records if record["id"] in selection_set]
    evaluation_records = [source_by_id[doc_id] for doc_id in evaluation_ids]
    paths = {
        "train": output / "train.jsonl",
        # EasyECR's MAVEN loader decides whether to build the labelled Event
        # container from the filename.  This is selection-only ground truth,
        # hence the conventional ``valid`` suffix is required; evaluation
        # remains the separate unlabeled test-shaped file below.
        "selection_dev": output / "selection-valid.jsonl",
        "evaluation_test": output / "evaluation-test.jsonl",
    }
    _write_jsonl(paths["train"], training_records)
    _write_jsonl(paths["selection_dev"], selection_records)
    _write_jsonl(
        paths["evaluation_test"],
        [_unlabeled_test_record(record) for record in evaluation_records],
    )

    selection_manifest = {
        "dataset": "maven_ere",
        "derivation": "sha256(g19-selection-v1:<doc_id>) ascending; first selection_size",
        "doc_count": len(selection_ids),
        "doc_ids": selection_ids,
        "parent_manifest": str(train_manifest),
        "p1_protocol_sha256": expected_p1_protocol_sha256,
        "selection_namespace": SELECTION_NAMESPACE,
        "source_path": str(source),
        "source_sha256": source_hash,
        "split_role": "selection-dev",
    }
    _write_json(output / "selection_manifest.json", selection_manifest)

    artifact_hashes = {name: sha256_file(path) for name, path in paths.items()}
    artifact_hashes["selection_manifest"] = sha256_file(output / "selection_manifest.json")
    report = {
        "artifact_sha256": artifact_hashes,
        "candidate_universe": "MAVEN-ERE gold event mentions; no mention pruning",
        "evaluation_gold_access": False,
        "input_protocol_delta": (
            "Global-Local Topic trains on 2,331 P1-train documents after reserving 291 "
            "selection-dev documents; existing 2,622-document anchor training is not reused."
        ),
        "p1_protocol_sha256": expected_p1_protocol_sha256,
        "schema_version": "ekg.easyecr_glt_preflight.v2",
        "selection_loader_path_semantics": (
            "selection-valid.jsonl is labelled selection-only input; EasyECR's "
            "MAVEN loader uses the 'valid' filename marker to construct Event objects."
        ),
        "source_sha256": source_hash,
        "split_counts": {
            "evaluation": len(evaluation_records),
            "selection_dev": len(selection_records),
            "training": len(training_records),
        },
        "upstream": "hqyang/EasyECR@f6cd779fbddc7ced2b14397041f83d92713115a9",
    }
    _write_json(output / "preflight.json", report)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("data/processed/maven_ere/train.jsonl"),
    )
    parser.add_argument(
        "--train-manifest",
        type=Path,
        default=Path("data/protocols/v6/manifests/maven_ere_train.json"),
    )
    parser.add_argument(
        "--evaluation-manifest",
        type=Path,
        default=Path("data/protocols/v6/manifests/maven_ere_internal-dev.json"),
    )
    parser.add_argument(
        "--p1-protocol", type=Path, default=Path("runs/stages/P1/p1-v6-20260904-r15/protocol.json")
    )
    parser.add_argument("--expected-p1-protocol-sha256", default=EXPECTED_P1_PROTOCOL_SHA256)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--selection-size", type=int, default=291)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = prepare(
        source=args.source,
        train_manifest=args.train_manifest,
        evaluation_manifest=args.evaluation_manifest,
        p1_protocol=args.p1_protocol,
        expected_p1_protocol_sha256=args.expected_p1_protocol_sha256,
        output=args.output,
        selection_size=args.selection_size,
    )
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
