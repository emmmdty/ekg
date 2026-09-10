#!/usr/bin/env python
"""Convert LLMERE causal generations into strict MAVEN-ERE official predictions.

LLMERE emits one generation for every focal-event/partition example, whereas
the frozen organisers' evaluator consumes one complete prediction object per
document. This converter preserves every internal-dev document and keeps the
official candidate universe intact. Repeated identical references within one
otherwise valid field are normalized to one relation-set member; ungenerated
or malformed model responses are errors, never implicit all-NONE fallbacks.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from ekg.relations.maven_ere_official import CAUSAL_SUBTYPES, empty_official_prediction

_REFERENCE = re.compile(r"^<(?P<event>e[0-9]+)(?:\s+[^>]*)?>$")
_EXPECTED_LABELS = set(CAUSAL_SUBTYPES)


class ConversionError(ValueError):
    """Raised when a generation cannot be converted without inventing output."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ConversionError(f"{path}:{line_number} is not JSON") from exc
        if not isinstance(record, dict):
            raise ConversionError(f"{path}:{line_number} is not a JSON object")
        records.append(record)
    return records


def load_manifest_ids(path: Path) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    ids = payload.get("doc_ids")
    if not isinstance(ids, list) or not all(isinstance(item, str) for item in ids):
        raise ConversionError(f"{path} has no string doc_ids list")
    if len(ids) != len(set(ids)):
        raise ConversionError(f"{path} repeats a document id")
    return sorted(ids)


def event_mentions(record: dict[str, Any]) -> list[dict[str, Any]]:
    mentions = [
        mention
        for event in record.get("events", [])
        for mention in event.get("mention", [])
        if isinstance(mention, dict)
    ]
    if not mentions and record.get("events"):
        raise ConversionError(f"{record.get('id')} has an event without a mention list")
    try:
        return sorted(
            mentions,
            key=lambda item: (item["sent_id"], item["offset"][0], item["id"]),
        )
    except (KeyError, IndexError, TypeError) as exc:
        raise ConversionError(f"{record.get('id')} has a malformed event mention") from exc


def partitions_per_event(record: dict[str, Any], *, partition_size: int) -> int:
    mentions = event_mentions(record)
    if partition_size <= 0:
        raise ConversionError("partition size must be positive")
    other_events = len(mentions) - 1
    if other_events <= 0:
        return 1
    return (other_events + partition_size - 1) // partition_size


def _parse_references(text: str, *, line_number: int, label: str) -> list[str]:
    if text in {"none", "none.", "NONE", "NONE.", "None", "None."}:
        return []
    references: list[str] = []
    for raw in text.split(", "):
        match = _REFERENCE.fullmatch(raw)
        if match is None:
            raise ConversionError(
                f"generation {line_number} has malformed {label} reference {raw!r}"
            )
        references.append(match.group("event"))
    return list(dict.fromkeys(references))


def parse_causal_prediction(record: dict[str, Any], *, line_number: int) -> dict[str, list[str]]:
    prediction = record.get("predict")
    if not isinstance(prediction, str):
        raise ConversionError(f"generation {line_number} has no string predict field")
    first_line = prediction.split("\n", maxsplit=1)[0].strip().rstrip(".")
    if not first_line:
        raise ConversionError(f"generation {line_number} has an empty first prediction line")

    parsed: dict[str, list[str]] = {}
    for field in first_line.split("; "):
        label, separator, values = field.partition(": ")
        if not separator or label not in _EXPECTED_LABELS:
            raise ConversionError(f"generation {line_number} has malformed causal field {field!r}")
        if label in parsed:
            raise ConversionError(f"generation {line_number} repeats causal label {label}")
        parsed[label] = _parse_references(values, line_number=line_number, label=label)
    if set(parsed) != _EXPECTED_LABELS:
        raise ConversionError(
            f"generation {line_number} must contain exactly "
            f"{sorted(_EXPECTED_LABELS)}, got {sorted(parsed)}"
        )
    return parsed


def _prediction_lines(path: Path) -> list[dict[str, Any]]:
    lines = read_jsonl(path)
    if not lines:
        raise ConversionError(f"{path} has no generated predictions")
    return lines


def convert_predictions(
    *,
    source_records: Iterable[dict[str, Any]],
    manifest_ids: Iterable[str],
    generations: Iterable[dict[str, Any]],
    partition_size: int,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    source_by_id: dict[str, dict[str, Any]] = {}
    for record in source_records:
        doc_id = record.get("id")
        if not isinstance(doc_id, str):
            raise ConversionError("source record has no string id")
        if doc_id in source_by_id:
            raise ConversionError(f"source repeats document id {doc_id}")
        source_by_id[doc_id] = record

    ordered_ids = list(manifest_ids)
    missing = set(ordered_ids) - set(source_by_id)
    if missing:
        raise ConversionError(
            f"source is missing {len(missing)} manifest ids: {sorted(missing)[:3]}"
        )

    generation_rows = list(generations)
    cursor = 0
    predictions: list[dict[str, Any]] = []
    emitted_pairs = 0
    expected_generations = 0
    for doc_id in ordered_ids:
        source = source_by_id[doc_id]
        mentions = event_mentions(source)
        per_event = partitions_per_event(source, partition_size=partition_size)
        expected_generations += len(mentions) * per_event
        prediction = empty_official_prediction(source)
        emitted: dict[str, set[tuple[str, str]]] = {label: set() for label in CAUSAL_SUBTYPES}
        by_number = {f"e{index}": str(mention["id"]) for index, mention in enumerate(mentions)}
        for source_mention in mentions:
            head = str(source_mention["id"])
            for _ in range(per_event):
                if cursor >= len(generation_rows):
                    raise ConversionError(
                        f"generation ended at {cursor}; expected {expected_generations} rows "
                        f"through {doc_id}"
                    )
                parsed = parse_causal_prediction(generation_rows[cursor], line_number=cursor + 1)
                cursor += 1
                for label, references in parsed.items():
                    for reference in references:
                        if reference not in by_number:
                            raise ConversionError(
                                f"generation {cursor} references unknown {reference} "
                                f"in document {doc_id}"
                            )
                        tail = by_number[reference]
                        if tail == head:
                            raise ConversionError(
                                f"generation {cursor} emits a causal self-pair in document {doc_id}"
                            )
                        emitted[label].add((head, tail))
        prediction["causal_relations"] = {
            label: [list(pair) for pair in sorted(emitted[label])] for label in CAUSAL_SUBTYPES
        }
        emitted_pairs += sum(len(pairs) for pairs in emitted.values())
        predictions.append(prediction)

    if cursor != len(generation_rows):
        raise ConversionError(
            f"generation contains {len(generation_rows) - cursor} trailing rows "
            f"after {len(ordered_ids)} documents"
        )
    return predictions, {
        "documents": len(predictions),
        "expected_generation_rows": expected_generations,
        "generation_rows": cursor,
        "partition_size": partition_size,
        "emitted_causal_pairs": emitted_pairs,
    }


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--generations", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--partition-size", default=30, type=int)
    args = parser.parse_args()

    for path in (args.source, args.manifest, args.generations):
        if not path.is_file():
            raise SystemExit(f"required input is absent: {path}")
    try:
        predictions, report = convert_predictions(
            source_records=read_jsonl(args.source),
            manifest_ids=load_manifest_ids(args.manifest),
            generations=_prediction_lines(args.generations),
            partition_size=args.partition_size,
        )
    except ConversionError as exc:
        raise SystemExit(f"LLMERE causal conversion failed: {exc}") from exc

    write_jsonl(args.output, predictions)
    report.update(
        {
            "schema_version": "ekg.llmere_causal_conversion.v1",
            "inputs": {
                "source_sha256": sha256_file(args.source),
                "manifest_sha256": sha256_file(args.manifest),
                "generations_sha256": sha256_file(args.generations),
            },
            "output": {
                "path": str(args.output),
                "sha256": sha256_file(args.output),
            },
        }
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"[llmere] converted {report['generation_rows']} generations across "
        f"{report['documents']} documents; emitted {report['emitted_causal_pairs']} causal pairs"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
