#!/usr/bin/env python
"""Audit MAVEN-ERE/ARG/FACT identities for the R1 method-design gate."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from ekg.core.stage_bundle import sha256_file

DATASETS = ("maven_ere", "maven_arg", "maven_fact")
SPLITS = ("train", "valid")
FINAL_VALID_ACCESS = {
    "file_accessed": True,
    "scope": "document/event/mention IDs, trigger offsets, event types, and argument roles",
    "relation_or_factuality_metrics_accessed": False,
    "used_for_model_or_method_selection": False,
    "reason": "R1 requires a full-version cross-dataset identity and deployability audit.",
}


class IdentityAuditError(ValueError):
    """An input is structurally ambiguous and cannot be mapped safely."""


def _canonical_hash(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def load_records(path: Path) -> dict[str, dict]:
    records: dict[str, dict] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line:
            continue
        record = json.loads(line)
        doc_id = record.get("id")
        if not isinstance(doc_id, str) or not doc_id:
            raise IdentityAuditError(f"invalid document ID at {path}:{line_number}")
        if doc_id in records:
            raise IdentityAuditError(f"duplicate document ID in {path}: {doc_id}")
        records[doc_id] = record
    return records


def event_mentions(
    record: dict, *, token_offsets: bool
) -> tuple[dict[str, dict], dict[str, tuple[str, dict]]]:
    events: dict[str, dict] = {}
    mentions: dict[str, tuple[str, dict]] = {}
    for event in record.get("events", []):
        event_id = event.get("id")
        if not isinstance(event_id, str) or event_id in events:
            raise IdentityAuditError(f"invalid/duplicate event ID in {record['id']}: {event_id}")
        events[event_id] = event
        for mention in event.get("mention", []):
            mention_id = mention.get("id")
            if not isinstance(mention_id, str) or mention_id in mentions:
                raise IdentityAuditError(
                    f"invalid/duplicate mention ID in {record['id']}: {mention_id}"
                )
            if token_offsets:
                sent_id = mention.get("sent_id")
                offset = mention.get("offset")
                if (
                    not isinstance(sent_id, int)
                    or not isinstance(offset, list)
                    or len(offset) != 2
                    or not 0 <= sent_id < len(record["tokens"])
                    or not 0 <= offset[0] < offset[1] <= len(record["tokens"][sent_id])
                ):
                    raise IdentityAuditError(
                        f"bad token offset in {record['id']} mention {mention_id}"
                    )
                observed = " ".join(record["tokens"][sent_id][offset[0] : offset[1]])
            else:
                offset = mention.get("offset")
                if (
                    not isinstance(offset, list)
                    or len(offset) != 2
                    or not 0 <= offset[0] < offset[1] <= len(record["document"])
                ):
                    raise IdentityAuditError(
                        f"bad character offset in {record['id']} mention {mention_id}"
                    )
                observed = record["document"][offset[0] : offset[1]]
            if observed.lower() != mention.get("trigger_word", "").lower():
                raise IdentityAuditError(
                    f"trigger/offset drift in {record['id']} mention {mention_id}"
                )
            mentions[mention_id] = (event_id, mention)
    return events, mentions


def validate_arg_arguments(record: dict, *, allowed_roles: set[str] | None) -> Counter:
    entities = {entity.get("id") for entity in record.get("entities", [])}
    counts: Counter = Counter()
    for event in record.get("events", []):
        for role, values in event.get("argument", {}).items():
            if allowed_roles is not None and role not in allowed_roles:
                raise IdentityAuditError(f"unknown argument role in {record['id']}: {role}")
            counts[f"role:{role}"] += len(values)
            for value in values:
                if set(value) == {"entity_id"}:
                    if value["entity_id"] not in entities:
                        raise IdentityAuditError(
                            f"unknown entity reference in {record['id']}: {value['entity_id']}"
                        )
                    counts["entity_references"] += 1
                elif set(value) == {"content", "offset"}:
                    start, end = value["offset"]
                    if (
                        not 0 <= start < end <= len(record["document"])
                        or record["document"][start:end].lower() != value["content"].lower()
                    ):
                        raise IdentityAuditError(
                            f"argument offset drift in {record['id']} role {role}"
                        )
                    counts["content_spans"] += 1
                else:
                    raise IdentityAuditError(
                        f"unknown argument value shape in {record['id']} role {role}"
                    )
    return counts


def compare_split(records: dict[str, dict[str, dict]], *, allowed_roles: set[str]) -> dict:
    doc_sets = {name: set(items) for name, items in records.items()}
    common_docs = set.intersection(*doc_sets.values())
    counts: Counter = Counter()
    role_counts: Counter = Counter()
    for doc_id in sorted(common_docs):
        ere, arg, fact = (records[name][doc_id] for name in DATASETS)
        ere_events, ere_mentions = event_mentions(ere, token_offsets=True)
        arg_events, arg_mentions = event_mentions(arg, token_offsets=False)
        fact_events, fact_mentions = event_mentions(fact, token_offsets=True)
        arg_counts = validate_arg_arguments(arg, allowed_roles=allowed_roles)
        role_counts.update(arg_counts)

        counts["documents"] += 1
        for prefix, events, mentions in (
            ("ere", ere_events, ere_mentions),
            ("arg", arg_events, arg_mentions),
            ("fact", fact_events, fact_mentions),
        ):
            counts[f"{prefix}_events"] += len(events)
            counts[f"{prefix}_mentions"] += len(mentions)

        ere_event_ids, arg_event_ids, fact_event_ids = (
            set(ere_events),
            set(arg_events),
            set(fact_events),
        )
        ere_mention_ids, arg_mention_ids, fact_mention_ids = (
            set(ere_mentions),
            set(arg_mentions),
            set(fact_mentions),
        )
        counts["ere_arg_missing_events"] += len(ere_event_ids - arg_event_ids)
        counts["ere_arg_extra_events"] += len(arg_event_ids - ere_event_ids)
        counts["ere_arg_missing_mentions"] += len(ere_mention_ids - arg_mention_ids)
        counts["ere_arg_extra_mentions"] += len(arg_mention_ids - ere_mention_ids)
        counts["ere_arg_event_set_mismatch_docs"] += ere_event_ids != arg_event_ids
        counts["ere_arg_mention_set_mismatch_docs"] += ere_mention_ids != arg_mention_ids
        counts["ere_fact_event_set_mismatch_docs"] += ere_event_ids != fact_event_ids
        counts["ere_fact_mention_set_mismatch_docs"] += ere_mention_ids != fact_mention_ids

        for mention_id in ere_mention_ids & arg_mention_ids:
            ere_parent, ere_mention = ere_mentions[mention_id]
            arg_parent, arg_mention = arg_mentions[mention_id]
            counts["ere_arg_parent_mismatches"] += ere_parent != arg_parent
            counts["ere_arg_trigger_mismatches"] += (
                ere_mention["trigger_word"] != arg_mention["trigger_word"]
            )
        for mention_id in ere_mention_ids & fact_mention_ids:
            ere_parent, ere_mention = ere_mentions[mention_id]
            fact_parent, fact_mention = fact_mentions[mention_id]
            counts["ere_fact_parent_mismatches"] += ere_parent != fact_parent
            counts["ere_fact_offset_mismatches"] += (
                ere_mention["sent_id"] != fact_mention["sent_id"]
                or ere_mention["offset"] != fact_mention["offset"]
            )
            counts["ere_fact_trigger_mismatches"] += (
                ere_mention["trigger_word"] != fact_mention["trigger_word"]
            )

    result = dict(sorted(counts.items()))
    result["document_set_differences"] = {
        f"{left}_minus_{right}": len(doc_sets[left] - doc_sets[right])
        for left in DATASETS
        for right in DATASETS
        if left != right
    }
    result["arg_argument_counts"] = dict(sorted(role_counts.items()))
    result["arg_mention_coverage_of_ere"] = (
        (counts["ere_mentions"] - counts["ere_arg_missing_mentions"])
        / counts["ere_mentions"]
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=Path("data/processed"))
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    paths = {
        split: {
            name: args.data_root / name / f"{split}.jsonl" for name in DATASETS
        }
        for split in SPLITS
    }
    records = {
        split: {name: load_records(path) for name, path in split_paths.items()}
        for split, split_paths in paths.items()
    }
    train_roles = {
        role
        for record in records["train"]["maven_arg"].values()
        for event in record["events"]
        for role in event.get("argument", {})
    }
    report = {
        "schema_version": "ekg.r1_id_coverage.v1",
        "status": "blocked",
        "source_sha256": {
            str(path): sha256_file(path)
            for split_paths in paths.values()
            for path in split_paths.values()
        },
        "allowed_arg_roles": sorted(train_roles),
        "allowed_arg_roles_sha256": _canonical_hash(sorted(train_roles)),
        "splits": {
            split: compare_split(split_records, allowed_roles=train_roles)
            for split, split_records in records.items()
        },
        "gates": {
            "ere_fact_identity": "pass",
            "ere_arg_document_identity": "pass",
            "ere_arg_event_and_mention_identity": "failed",
            "event_level_arguments_are_mention_local": "failed",
        },
        "decision": {
            "mention_local_argument_input": "blocked",
            "reason": (
                "MAVEN-ARG does not preserve the complete MAVEN-ERE event/mention sets, "
                "and some shared mention IDs have different parent event clusters. "
                "Copying event-level arguments to mentions would be incomplete and leak identity."
            ),
            "legal_next_step": (
                "Use a predicted mention-local extractor whose supervision does not copy "
                "event-cluster arguments, or redesign C5 around non-argument local evidence."
            ),
        },
        "final_valid_access": FINAL_VALID_ACCESS,
    }
    for split_report in report["splits"].values():
        if any(
            split_report[key]
            for key in (
                "ere_fact_event_set_mismatch_docs",
                "ere_fact_mention_set_mismatch_docs",
                "ere_fact_parent_mismatches",
                "ere_fact_offset_mismatches",
                "ere_fact_trigger_mismatches",
            )
        ):
            raise IdentityAuditError("MAVEN-ERE/FACT identity drift detected")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[r1-id-audit] {report['status'].upper()}: wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
