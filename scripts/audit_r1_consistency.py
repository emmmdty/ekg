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
    "FR-016": _entries(
        ["docs/BASELINE_ROSTER.md#fr-016-fidelity-states"],
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
    """An audited artifact is missing, so the audit itself cannot be performed."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ConsistencyAuditError(message)


class _Findings:
    """Collect every inconsistency instead of stopping at the first one.

    T023 is an audit, not an acceptance test: stopping at the first failure hides the
    remaining rows and, because the old code demanded a checked T023, made the audit a
    precondition for itself.
    """

    def __init__(self) -> None:
        self.items: list[dict[str, str]] = []

    def check(self, condition: bool, code: str, message: str) -> bool:
        if not condition:
            self.items.append({"code": code, "message": message})
        return condition


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


def _contract_binding_state(
    binding: dict[str, object] | None, relative: str, actual_sha256: str
) -> str:
    if binding is None:
        return "pending_t024"
    if binding.get("state") == "blocked":
        return "blocked_pre_admission"
    if binding.get("path") == relative and binding.get("sha256") == actual_sha256:
        return "frozen"
    return "drifted"


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

    findings = _Findings()
    spec_text = (repo / "docs/SPEC.md").read_text(encoding="utf-8")
    tasks_text = (repo / "docs/TASKS.md").read_text(encoding="utf-8")
    defined = _defined_requirement_ids(spec_text)
    unmapped = sorted(defined - set(TRACEABILITY))
    unknown_mapped = sorted(set(TRACEABILITY) - defined)
    findings.check(
        not unmapped, "requirement-unmapped", f"SPEC requirements with no mapping: {unmapped}"
    )
    findings.check(
        not unknown_mapped,
        "requirement-undeclared",
        f"mapped requirements absent from SPEC: {unknown_mapped}",
    )

    tasks = _task_ids(tasks_text)
    referenced_tasks = {
        task for entry in TRACEABILITY.values() for task in entry["verification_tasks"]
    }
    findings.check(
        referenced_tasks <= tasks,
        "task-undeclared",
        f"traceability map references undeclared tasks: {sorted(referenced_tasks - tasks)}",
    )
    for requirement, entry in TRACEABILITY.items():
        findings.check(
            bool(entry["current_evidence"]),
            "requirement-no-evidence",
            f"requirement has no evidence: {requirement}",
        )
        findings.check(
            bool(entry["verification_tasks"]),
            "requirement-no-task",
            f"requirement has no tasks: {requirement}",
        )
        findings.check(
            bool(entry["phase_contracts"]),
            "requirement-no-contract",
            f"requirement has no contract: {requirement}",
        )
        for reference in entry["current_evidence"]:
            relative, _, anchor = reference.partition("#")
            if not findings.check(
                (repo / relative).is_file(),
                "evidence-missing",
                f"requirement evidence missing for {requirement}: {relative}",
            ):
                continue
            if anchor and relative.endswith(".md"):
                headings = _markdown_heading_anchors(
                    (repo / relative).read_text(encoding="utf-8")
                )
                findings.check(
                    anchor in headings,
                    "evidence-anchor-missing",
                    f"requirement evidence anchor missing for {requirement}: {reference}",
                )
            if anchor and relative.endswith(".json"):
                findings.check(
                    _json_pointer_exists(_load(repo / relative), anchor),
                    "evidence-pointer-missing",
                    f"requirement evidence pointer missing for {requirement}: {reference}",
                )

    # T023 depends on T012-T022 only. T023 may not require itself, and T024 is released by
    # this audit rather than being a precondition for it.
    incomplete = [
        f"T{number:03d}"
        for number in range(12, 23)
        if not _checked_task(tasks_text, f"T{number:03d}")
    ]
    findings.check(
        not incomplete, "prerequisite-task-open", f"T023 prerequisites not complete: {incomplete}"
    )

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
    findings.check(
        not undeclared,
        "document-undeclared-requirement",
        f"documents reference undeclared requirements: {undeclared}",
    )

    r1_root = repo / R1_ROOT
    r1_protocol_path = r1_root / "protocol.json"
    r1_protocol = _load(r1_protocol_path)
    findings.check(
        r1_protocol.get("schema_version") == "ekg.r1_protocol.v1",
        "protocol-schema",
        "R1 protocol schema is not ekg.r1_protocol.v1",
    )
    audit_script = "scripts/audit_r1_consistency.py"
    findings.check(
        r1_protocol.get("code", {}).get("files", {}).get(audit_script)
        == sha256_file(repo / audit_script),
        "audit-script-hash-drift",
        "R1 protocol does not freeze the current consistency-audit script",
    )
    artifact_identities: dict[str, dict[str, str]] = {}
    for name, artifact in r1_protocol.get("artifacts", {}).items():
        path = r1_root / artifact["path"]
        if not findings.check(
            path.is_file(), "artifact-missing", f"R1 protocol artifact missing: {name}"
        ):
            continue
        actual = sha256_file(path)
        artifact_identities[name] = {
            "path": artifact["path"],
            "frozen_sha256": artifact["sha256"],
            "actual_sha256": actual,
            "state": "frozen" if actual == artifact["sha256"] else "drifted",
        }
        findings.check(
            actual == artifact["sha256"],
            "artifact-hash-drift",
            f"R1 artifact hash drift: {name} frozen {artifact['sha256']} actual {actual}",
        )
    reconciliation = r1_protocol.get("artifacts", {}).get(
        "relation_code_hash_reconciliation"
    )
    findings.check(
        reconciliation is not None,
        "relation-code-hash-artifact-missing",
        "R1 protocol has no relation code-hash reconciliation artifact",
    )
    if reconciliation is not None:
        reconciliation_payload = _load(r1_root / reconciliation["path"])
        for run_name, run in reconciliation_payload["runs"].items():
            metadata_path = r1_root / run["metadata_path"]
            metadata = _load(metadata_path)
            findings.check(
                sha256_file(metadata_path) == run["metadata_sha256_after"],
                "relation-run-metadata-drift",
                f"relation run metadata drift: {run_name}",
            )
            findings.check(
                metadata["protocol_binding"]["hashes"].get("supervised_extractor")
                == run["supervised_extractor"]["sha256"],
                "relation-extractor-hash-drift",
                f"relation extractor hash drift: {run_name}",
            )
    final_valid = r1_protocol.get("final_valid_ledger", {})
    findings.check(
        not final_valid.get("used_for_model_or_method_selection"),
        "final-valid-leakage",
        "final-valid was used for model or method selection",
    )
    status = _load(r1_root / "status.json")
    prerequisites = {f"T{number:03d}" for number in range(12, 23)}
    findings.check(
        set(status.get("completed_tasks", [])) >= prerequisites,
        "status-task-mismatch",
        "R1 status does not close T012-T022",
    )

    # T024 can freeze each independently approved phase while recording an explicit
    # pre-admission block for another. An absent binding is pending before T024; a blocked
    # record is deliberately not a document hash binding; all other declared bindings must
    # reproduce the contract file exactly.
    contracts = r1_protocol.get("phase_contracts") or {}
    contract_states: dict[str, dict[str, object]] = {}
    for name, relative in METHOD_PHASE_PATHS.items():
        contract_path = repo / relative
        binding = contracts.get(name)
        state: dict[str, object] = {
            "path": relative,
            "missing_sections": _missing_contract_sections(
                contract_path.read_text(encoding="utf-8")
            ),
            "frozen_in_protocol": False,
        }
        actual = sha256_file(contract_path)
        binding_state = _contract_binding_state(binding, relative, actual)
        state["state"] = binding_state
        if binding_state == "blocked_pre_admission":
            state["reason"] = binding.get("reason")
            findings.check(
                bool(binding.get("reason")),
                "contract-block-reason",
                f"{name} phase block has no reason",
            )
        elif binding_state in {"frozen", "drifted"}:
            state["frozen_in_protocol"] = binding_state == "frozen"
            findings.check(
                binding_state == "frozen",
                "contract-drift",
                f"{name} phase contract does not match its frozen binding",
            )
            findings.check(
                not state["missing_sections"],
                "contract-sections-missing",
                f"{name} contract sections missing: {state['missing_sections']}",
            )
        contract_states[name] = state

    p1_path, a3_path = repo / P1_PROTOCOL, repo / A3_PROTOCOL
    _require(p1_path.is_file(), "P1 protocol missing")
    _require(a3_path.is_file(), "A3 protocol missing")
    findings.check(
        sha256_file(p1_path) == "1e31a9acef39261f776f7ed4069fd73f4531e8d12b55779bfc0fbd74c67f9655",
        "p1-identity-drift",
        "P1 trust root identity drift",
    )
    findings.check(
        sha256_file(a3_path) == "c187bf03978674edd29ac209658ccb62d457b744a209e864a0fef0e9eee9359e",
        "a3-identity-drift",
        "A3 handoff identity drift",
    )

    r1_pass_blockers = [
        f"R1 status is {status.get('status')}, not pass",
        *(f"phase contract pending T024: {name}" for name, state in contract_states.items()
          if state["state"] == "pending_t024"),
        *(f"phase contract blocked before admission: {name}"
          for name, state in contract_states.items()
          if state["state"] == "blocked_pre_admission"),
        *(f"cross-artifact finding open: {item['code']}" for item in findings.items),
    ]
    return {
        "schema_version": "ekg.r1_cross_artifact_audit.v2",
        "status": "pass" if not findings.items else "blocked",
        "findings": findings.items,
        "requirements": TRACEABILITY,
        "coverage": {
            "declared_requirements": len(defined),
            "mapped_requirements": len(TRACEABILITY),
            "referenced_tasks": len(referenced_tasks),
            "unmapped_requirements": unmapped,
            "undeclared_requirement_references": undeclared,
        },
        "artifact_identities": artifact_identities,
        "phase_contracts": contract_states,
        "r1_status": status.get("status"),
        "r1_pass_blockers": r1_pass_blockers,
        "artifact_sha256": {relative: sha256_file(repo / relative) for relative in AUDITED_PATHS},
        "trust_roots": {
            "r1_protocol": {
                "path": f"{R1_ROOT}/protocol.json",
                "sha256": sha256_file(r1_protocol_path),
            },
            "p1_protocol": {"path": P1_PROTOCOL, "sha256": sha256_file(p1_path)},
            "a3_protocol": {"path": A3_PROTOCOL, "sha256": sha256_file(a3_path)},
        },
        "final_valid_used_for_model_or_method_selection": bool(
            final_valid.get("used_for_model_or_method_selection")
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = build_audit(args.repo_root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    mapped = report["coverage"]["mapped_requirements"]
    print(f"{report['status'].upper()}: {mapped} requirements mapped")
    for item in report["findings"]:
        print(f"  {item['code']}: {item['message']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
