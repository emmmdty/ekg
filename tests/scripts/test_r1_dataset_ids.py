from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "audit_r1_dataset_ids", ROOT / "scripts/audit_r1_dataset_ids.py"
)
assert SPEC and SPEC.loader
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


def test_duplicate_document_ids_fail_fast(tmp_path: Path) -> None:
    path = tmp_path / "duplicate.jsonl"
    path.write_text('{"id":"d"}\n{"id":"d"}\n', encoding="utf-8")

    with pytest.raises(audit.IdentityAuditError, match="duplicate document ID"):
        audit.load_records(path)


def test_bad_token_offset_fails_fast() -> None:
    record = {
        "id": "d",
        "tokens": [["happened"]],
        "events": [
            {
                "id": "e",
                "mention": [
                    {
                        "id": "m",
                        "trigger_word": "happened",
                        "sent_id": 0,
                        "offset": [0, 2],
                    }
                ],
            }
        ],
    }

    with pytest.raises(audit.IdentityAuditError, match="bad token offset"):
        audit.event_mentions(record, token_offsets=True)


def test_unknown_entity_reference_fails_fast() -> None:
    record = {
        "id": "d",
        "document": "event",
        "entities": [],
        "events": [{"argument": {"Agent": [{"entity_id": "missing"}]}}],
    }

    with pytest.raises(audit.IdentityAuditError, match="unknown entity reference"):
        audit.validate_arg_arguments(record, allowed_roles={"Agent"})


def test_unknown_argument_role_fails_fast() -> None:
    record = {
        "id": "d",
        "document": "event",
        "entities": [],
        "events": [{"argument": {"Unknown": []}}],
    }

    with pytest.raises(audit.IdentityAuditError, match="unknown argument role"):
        audit.validate_arg_arguments(record, allowed_roles={"Agent"})


def test_structural_valid_access_ledger_is_explicit() -> None:
    assert audit.FINAL_VALID_ACCESS["file_accessed"] is True
    assert audit.FINAL_VALID_ACCESS["relation_or_factuality_metrics_accessed"] is False
    assert audit.FINAL_VALID_ACCESS["used_for_model_or_method_selection"] is False
