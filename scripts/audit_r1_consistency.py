#!/usr/bin/env python
"""Audit R1 requirements, executable tasks, phase contracts, and trust identities."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from ekg.core.stage_bundle import sha256_file

PHASE_PATHS = {
    "identity": "docs/phases/PHASE_C5_argument_uncertainty.md",
    "relation": "docs/phases/PHASE_A4_pair_evidence.md",
    "factuality": "docs/phases/PHASE_D4_typed_cue_factuality.md",
    "consumer": "docs/phases/PHASE_E3_factorial_consumers.md",
}
METHOD_PHASE_PATHS = {key: PHASE_PATHS[key] for key in ("identity", "relation", "factuality")}
CONTRACT_SECTIONS = (
    "## Inputs",
    "## Baselines and causal matrix",
    "## Tasks",
    "## Promotion gate",
    "## Stop conditions",
    "## Bundle",
    "## GPU command",
)

AUDITED_PATHS = (
    ".specify/memory/constitution.md",
    "docs/SPEC.md",
    "docs/RESEARCH_PLAN.md",
    "docs/TASKS.md",
    "docs/phases/README.md",
    "docs/phases/PHASE_R1_method_design_freeze.md",
    *PHASE_PATHS.values(),
    "docs/phases/PHASE_H2_thesis_acceptance.md",
    "docs/results/PHASE_P1.md",
    "docs/results/PHASE_A.md",
    "docs/results/PHASE_C.md",
    "docs/results/PHASE_D.md",
    "docs/results/PHASE_E.md",
    "docs/results/PHASE_R1.md",
)

R1_ROOT = "runs/stages/R1/r1-v61-20260904"
P1_PROTOCOL = "runs/stages/P1/p1-v6-20260904-r15/protocol.json"
A3_PROTOCOL = "runs/stages/A3/a3-v6-20260905-r17/protocol.json"


def _entries(evidence: list[str], tasks: list[str], phases: list[str]) -> dict[str, list[str]]:
    return {
        "current_evidence": evidence,
        "verification_tasks": tasks,
        "phase_contracts": phases,
    }


TRACEABILITY = {
    "RS-001": _entries(
        [f"{R1_ROOT}/design_briefs.json#/briefs/identity"],
        ["T025", "T026", "T027", "T028", "T029"],
        [PHASE_PATHS["identity"]],
    ),
    "RS-002": _entries(
        [f"{R1_ROOT}/design_briefs.json#/briefs/relation"],
        ["T030", "T031", "T032", "T033", "T034"],
        [PHASE_PATHS["relation"]],
    ),
    "RS-003": _entries(
        [f"{R1_ROOT}/design_briefs.json#/briefs/factuality"],
        ["T035", "T036", "T037", "T038", "T039"],
        [PHASE_PATHS["factuality"]],
    ),
    "RS-004": _entries(
        ["docs/phases/PHASE_E3_factorial_consumers.md"],
        ["T040", "T041", "T042", "T043", "T044"],
        [PHASE_PATHS["consumer"]],
    ),
    "FR-001": _entries(
        ["docs/RESEARCH_PLAN.md#current-candidate-design"],
        ["T025", "T030", "T035"],
        [PHASE_PATHS["identity"], PHASE_PATHS["relation"], PHASE_PATHS["factuality"]],
    ),
    "FR-002": _entries(
        ["docs/phases/PHASE_E3_factorial_consumers.md#goal"],
        ["T040", "T044"],
        [PHASE_PATHS["consumer"]],
    ),
    "FR-003": _entries(
        ["docs/phases/README.md#错误隔离与交接"],
        ["T029", "T034", "T039", "T044"],
        list(PHASE_PATHS.values()),
    ),
    "FR-004": _entries(
        ["docs/RESEARCH_PLAN.md#protocol-layers"],
        ["T028", "T033", "T038", "T043"],
        list(PHASE_PATHS.values()),
    ),
    "FR-005": _entries(
        [f"{R1_ROOT}/design_briefs.json"],
        ["T027", "T032", "T037"],
        [PHASE_PATHS["identity"], PHASE_PATHS["relation"], PHASE_PATHS["factuality"]],
    ),
    "FR-006": _entries(
        [f"{R1_ROOT}/literature_matrix.json", "docs/results/PHASE_R1.md"],
        ["T026", "T031", "T036"],
        [PHASE_PATHS["identity"], PHASE_PATHS["relation"], PHASE_PATHS["factuality"]],
    ),
    "FR-007": _entries(
        [f"{R1_ROOT}/power_analysis.json"],
        ["T029", "T034", "T039"],
        [PHASE_PATHS["identity"], PHASE_PATHS["relation"], PHASE_PATHS["factuality"]],
    ),
    "FR-008": _entries(
        ["docs/phases/PHASE_E3_factorial_consumers.md#e34-统计推断"],
        ["T042", "T043", "T044"],
        [PHASE_PATHS["consumer"]],
    ),
    "FR-009": _entries(
        ["docs/phases/README.md#错误隔离与交接"],
        ["T026", "T029", "T031", "T034", "T036", "T039", "T044"],
        list(PHASE_PATHS.values()),
    ),
    "FR-010": _entries(
        [f"{R1_ROOT}/protocol.json#/final_valid_ledger"],
        ["T029", "T034", "T039", "T044"],
        list(PHASE_PATHS.values()),
    ),
    "FR-011": _entries(
        ["docs/results/PHASE_A.md", "docs/results/PHASE_C.md", "docs/results/PHASE_D.md"],
        ["T028", "T033", "T038"],
        [PHASE_PATHS["identity"], PHASE_PATHS["relation"], PHASE_PATHS["factuality"]],
    ),
    "FR-012": _entries(
        [f"{R1_ROOT}/literature_matrix.json"],
        ["T026", "T031", "T036"],
        [PHASE_PATHS["identity"], PHASE_PATHS["relation"], PHASE_PATHS["factuality"]],
    ),
    "FR-013": _entries(
        [f"{R1_ROOT}/id_coverage.json"],
        ["T025", "T040"],
        [PHASE_PATHS["identity"], PHASE_PATHS["consumer"]],
    ),
    "FR-014": _entries(
        ["tests/core/test_propagation.py"],
        ["T025", "T035", "T040"],
        [PHASE_PATHS["identity"], PHASE_PATHS["factuality"], PHASE_PATHS["consumer"]],
    ),
    "FR-015": _entries(
        ["docs/phases/README.md#运行方式"],
        ["T026", "T031", "T036"],
        [PHASE_PATHS["identity"], PHASE_PATHS["relation"], PHASE_PATHS["factuality"]],
    ),
    "QR-001": _entries(
        [f"{R1_ROOT}/design_briefs.json#/briefs"],
        ["T028", "T033", "T038"],
        [PHASE_PATHS["identity"], PHASE_PATHS["relation"], PHASE_PATHS["factuality"]],
    ),
    "QR-002": _entries(
        ["docs/RESEARCH_PLAN.md#statistics-and-power"],
        ["T029", "T034", "T039"],
        [PHASE_PATHS["identity"], PHASE_PATHS["relation"], PHASE_PATHS["factuality"]],
    ),
    "QR-003": _entries(
        [
            f"{R1_ROOT}/design_briefs.json#/briefs/identity/guardrails",
            f"{R1_ROOT}/design_briefs.json#/briefs/relation/guardrails",
            f"{R1_ROOT}/design_briefs.json#/briefs/factuality/guardrails",
        ],
        ["T028", "T033", "T038"],
        [PHASE_PATHS["identity"], PHASE_PATHS["relation"], PHASE_PATHS["factuality"]],
    ),
    "QR-004": _entries(
        [f"{R1_ROOT}/power_analysis.json"],
        ["T029", "T034", "T039"],
        [PHASE_PATHS["identity"], PHASE_PATHS["relation"], PHASE_PATHS["factuality"]],
    ),
    "QR-005": _entries(
        ["docs/phases/PHASE_E3_factorial_consumers.md#e32-预测有效性与图依赖正控"],
        ["T041", "T042", "T044"],
        [PHASE_PATHS["consumer"]],
    ),
    "QR-006": _entries(
        ["docs/phases/README.md#运行方式"],
        ["T025", "T030", "T035", "T040", "T045"],
        [*PHASE_PATHS.values(), "docs/phases/PHASE_H2_thesis_acceptance.md"],
    ),
    "QR-007": _entries(
        ["docs/results/PHASE_A.md", "docs/results/PHASE_C.md", "docs/results/PHASE_D.md"],
        ["T028", "T033", "T038", "T044"],
        list(PHASE_PATHS.values()),
    ),
    "SC-001": _entries(
        ["docs/RESEARCH_PLAN.md#evaluation-design"],
        ["T029", "T034", "T039"],
        [PHASE_PATHS["identity"], PHASE_PATHS["relation"], PHASE_PATHS["factuality"]],
    ),
    "SC-002": _entries(
        [f"{R1_ROOT}/anchors/identity/official_joint_metrics.json"],
        ["T028", "T029"],
        [PHASE_PATHS["identity"]],
    ),
    "SC-003": _entries(["docs/results/PHASE_A.md"], ["T033", "T034"], [PHASE_PATHS["relation"]]),
    "SC-004": _entries(
        [f"{R1_ROOT}/factuality_cv/factuality_cv.json"],
        ["T038", "T039"],
        [PHASE_PATHS["factuality"]],
    ),
    "SC-005": _entries(
        ["docs/phases/PHASE_E3_factorial_consumers.md#e33-全-factorial"],
        ["T042", "T043", "T044"],
        [PHASE_PATHS["consumer"]],
    ),
    "SC-006": _entries(
        ["docs/phases/README.md#错误隔离与交接"],
        ["T044", "T045", "T046"],
        [PHASE_PATHS["consumer"], "docs/phases/PHASE_H2_thesis_acceptance.md"],
    ),
    "SC-007": _entries(
        [f"{R1_ROOT}/id_coverage.json"],
        ["T040", "T045"],
        [PHASE_PATHS["consumer"], "docs/phases/PHASE_H2_thesis_acceptance.md"],
    ),
    "SC-008": _entries(
        ["docs/phases/README.md#运行方式"],
        ["T025", "T030", "T035", "T040", "T045"],
        [*PHASE_PATHS.values(), "docs/phases/PHASE_H2_thesis_acceptance.md"],
    ),
    "SC-009": _entries(
        ["docs/SPEC.md#problem-statement", "docs/RESEARCH_PLAN.md#summary"],
        ["T046", "T047"],
        ["docs/phases/PHASE_H2_thesis_acceptance.md"],
    ),
}


class ConsistencyAuditError(ValueError):
    """A declared requirement, task, artifact, or trust identity is inconsistent."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ConsistencyAuditError(message)


def _base_requirement_ids(text: str) -> set[str]:
    return set(re.findall(r"\b(?:RS|FR|QR|SC)-\d{3}\b", text))


def _defined_requirement_ids(spec_text: str) -> set[str]:
    patterns = (
        r"^### (RS-\d{3})\b",
        r"^- \*\*(FR-\d{3})\*\*:",
        r"^- \*\*(QR-\d{3})\*\*:",
        r"^- \*\*(SC-\d{3})\*\*:",
    )
    return {match for pattern in patterns for match in re.findall(pattern, spec_text, re.M)}


def _task_ids(tasks_text: str) -> set[str]:
    return set(re.findall(r"\*\*(T\d{3})\b", tasks_text))


def _checked_task(tasks_text: str, task_id: str) -> bool:
    return bool(re.search(rf"^- \[x\] \*\*{task_id}\b", tasks_text, re.M))


def _missing_contract_sections(text: str) -> list[str]:
    return [section for section in CONTRACT_SECTIONS if section not in text]


def _markdown_heading_anchors(text: str) -> set[str]:
    anchors = set()
    for title in re.findall(r"^#{1,6}\s+(.+?)\s*$", text, re.M):
        slug = re.sub(r"[^\w\s-]", "", title.casefold())
        anchors.add(re.sub(r"[\s-]+", "-", slug).strip("-"))
    return anchors


def _json_pointer_exists(payload, pointer: str) -> bool:
    if not pointer.startswith("/"):
        return False
    current = payload
    for raw in pointer[1:].split("/"):
        key = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return False
    return True


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_audit(repo: Path) -> dict:
    for relative in AUDITED_PATHS:
        _require((repo / relative).is_file(), f"audited artifact missing: {relative}")

    spec_text = (repo / "docs/SPEC.md").read_text(encoding="utf-8")
    tasks_text = (repo / "docs/TASKS.md").read_text(encoding="utf-8")
    defined = _defined_requirement_ids(spec_text)
    _require(defined == set(TRACEABILITY), "traceability map does not exactly cover SPEC")

    tasks = _task_ids(tasks_text)
    referenced_tasks = {
        task for entry in TRACEABILITY.values() for task in entry["verification_tasks"]
    }
    _require(referenced_tasks <= tasks, "traceability map references undeclared tasks")
    for requirement, entry in TRACEABILITY.items():
        _require(entry["current_evidence"], f"requirement has no evidence: {requirement}")
        _require(entry["verification_tasks"], f"requirement has no tasks: {requirement}")
        _require(entry["phase_contracts"], f"requirement has no contract: {requirement}")
        for reference in entry["current_evidence"]:
            relative, _, anchor = reference.partition("#")
            _require(
                (repo / relative).is_file(),
                f"requirement evidence missing for {requirement}: {relative}",
            )
            if anchor and relative.endswith(".md"):
                headings = _markdown_heading_anchors(
                    (repo / relative).read_text(encoding="utf-8")
                )
                _require(
                    anchor in headings,
                    f"requirement evidence anchor missing for {requirement}: {reference}",
                )
            if anchor and relative.endswith(".json"):
                _require(
                    _json_pointer_exists(_load(repo / relative), anchor),
                    f"requirement evidence pointer missing for {requirement}: {reference}",
                )
    for task in ("T020", "T021", "T022", "T023", "T024"):
        _require(_checked_task(tasks_text, task), f"R1 task is not complete: {task}")

    scanned = (
        "docs/RESEARCH_PLAN.md",
        "docs/TASKS.md",
        "docs/phases/PHASE_R1_method_design_freeze.md",
        *PHASE_PATHS.values(),
        "docs/phases/PHASE_E3_factorial_consumers.md",
        "docs/phases/PHASE_H2_thesis_acceptance.md",
    )
    undeclared: dict[str, list[str]] = {}
    for relative in scanned:
        referenced = _base_requirement_ids((repo / relative).read_text(encoding="utf-8"))
        unknown = sorted(referenced - defined)
        if unknown:
            undeclared[relative] = unknown
    _require(not undeclared, f"documents reference undeclared requirements: {undeclared}")

    r1_root = repo / R1_ROOT
    r1_protocol_path = r1_root / "protocol.json"
    r1_protocol = _load(r1_protocol_path)
    _require(r1_protocol.get("schema_version") == "ekg.r1_protocol.v1", "R1 protocol schema")
    for name, artifact in r1_protocol.get("artifacts", {}).items():
        path = r1_root / artifact["path"]
        _require(path.is_file(), f"R1 protocol artifact missing: {name}")
        _require(sha256_file(path) == artifact["sha256"], f"R1 artifact hash drift: {name}")
    final_valid = r1_protocol.get("final_valid_ledger", {})
    _require(not final_valid.get("used_for_model_or_method_selection"), "final-valid leakage")
    status = _load(r1_root / "status.json")
    _require(status.get("status") == "pass", "R1 status is not pass")
    _require(
        set(status.get("completed_tasks", [])) >= {f"T{number:03d}" for number in range(12, 25)},
        "R1 status does not close T012-T024",
    )

    contracts = r1_protocol.get("phase_contracts", {})
    _require(set(contracts) == set(METHOD_PHASE_PATHS), "R1 phase-contract set mismatch")
    for name, relative in METHOD_PHASE_PATHS.items():
        contract_path = repo / relative
        missing_sections = _missing_contract_sections(contract_path.read_text(encoding="utf-8"))
        _require(not missing_sections, f"{name} contract sections missing: {missing_sections}")
        binding = contracts[name]
        _require(binding.get("path") == relative, f"{name} contract path mismatch")
        _require(
            binding.get("sha256") == sha256_file(contract_path),
            f"{name} contract hash drift",
        )

    p1_path, a3_path = repo / P1_PROTOCOL, repo / A3_PROTOCOL
    _require(p1_path.is_file(), "P1 protocol missing")
    _require(a3_path.is_file(), "A3 protocol missing")
    _require(
        sha256_file(p1_path) == "1e31a9acef39261f776f7ed4069fd73f4531e8d12b55779bfc0fbd74c67f9655",
        "P1 identity drift",
    )
    _require(
        sha256_file(a3_path) == "c187bf03978674edd29ac209658ccb62d457b744a209e864a0fef0e9eee9359e",
        "A3 identity drift",
    )

    return {
        "schema_version": "ekg.r1_cross_artifact_audit.v1",
        "status": "pass",
        "requirements": TRACEABILITY,
        "coverage": {
            "declared_requirements": len(defined),
            "mapped_requirements": len(TRACEABILITY),
            "referenced_tasks": len(referenced_tasks),
            "unmapped_requirements": [],
            "undeclared_requirement_references": {},
        },
        "artifact_sha256": {relative: sha256_file(repo / relative) for relative in AUDITED_PATHS},
        "trust_roots": {
            "r1_protocol": {
                "path": f"{R1_ROOT}/protocol.json",
                "sha256": sha256_file(r1_protocol_path),
            },
            "p1_protocol": {"path": P1_PROTOCOL, "sha256": sha256_file(p1_path)},
            "a3_protocol": {"path": A3_PROTOCOL, "sha256": sha256_file(a3_path)},
        },
        "final_valid_used_for_model_or_method_selection": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = build_audit(args.repo_root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"PASS: {report['coverage']['mapped_requirements']} requirements mapped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
