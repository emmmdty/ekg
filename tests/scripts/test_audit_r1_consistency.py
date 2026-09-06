from __future__ import annotations

import importlib.util
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO / "scripts/audit_r1_consistency.py"
_SPEC = importlib.util.spec_from_file_location("audit_r1_consistency", _SCRIPT)
assert _SPEC and _SPEC.loader
audit = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(audit)


def test_traceability_exactly_covers_spec_requirements() -> None:
    spec = (_REPO / "docs/SPEC.md").read_text(encoding="utf-8")

    assert audit._defined_requirement_ids(spec) == set(audit.TRACEABILITY)


def test_requirement_parser_ignores_acceptance_scenario_suffixes() -> None:
    text = "RS-001 RS-001.1 FR-015 QR-006 SC-009"

    assert audit._base_requirement_ids(text) == {
        "RS-001",
        "FR-015",
        "QR-006",
        "SC-009",
    }


def test_checked_task_requires_checked_markdown_item() -> None:
    tasks = "- [x] **T023** done\n- [ ] **T024** pending\n"

    assert audit._checked_task(tasks, "T023")
    assert not audit._checked_task(tasks, "T024")


def test_phase_contract_requires_every_execution_section() -> None:
    complete = "\n".join(audit.CONTRACT_SECTIONS)

    assert audit._missing_contract_sections(complete) == []
    assert audit._missing_contract_sections(complete.replace("## GPU command", "")) == [
        "## GPU command"
    ]


def test_markdown_heading_anchors_cover_english_and_chinese_titles() -> None:
    text = "## Current Candidate Design\n### E3.4 统计推断\n## 错误隔离与交接\n"

    assert audit._markdown_heading_anchors(text) == {
        "current-candidate-design",
        "e34-统计推断",
        "错误隔离与交接",
    }


def test_json_pointer_requires_a_real_nested_path() -> None:
    payload = {"briefs": {"identity": {"guardrails": []}}}

    assert audit._json_pointer_exists(payload, "/briefs/identity/guardrails")
    assert not audit._json_pointer_exists(payload, "/identity")
    assert not audit._json_pointer_exists(payload, "briefs/identity")
