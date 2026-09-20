#!/usr/bin/env python
"""Run the frozen R1 audit with the author-approved v6.2 task amendments.

The v6.1 audit script is part of its immutable protocol identity and must not be
edited. This wrapper updates task traceability for the withdrawn consumer
factorial and the admitted v6.2 research/code tasks.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

_FROZEN_PATH = Path(__file__).with_name("audit_r1_consistency.py")
_FROZEN_SPEC = importlib.util.spec_from_file_location("audit_r1_consistency_v61", _FROZEN_PATH)
if _FROZEN_SPEC is None or _FROZEN_SPEC.loader is None:
    raise RuntimeError(f"cannot load frozen audit: {_FROZEN_PATH}")
frozen = importlib.util.module_from_spec(_FROZEN_SPEC)
_FROZEN_SPEC.loader.exec_module(frozen)

TASK_AMENDMENTS = {
    "RS-001": [
        "T025", "T026", "T027", "T028", "T029", "T048", "T051", "T053", "T060", "T061"
    ],
    "RS-002": ["T030", "T031", "T032", "T033", "T034", "T048", "T050"],
    "RS-003": ["T035", "T036", "T037", "T038", "T039", "T048", "T049", "T052", "T059"],
    "RS-004": ["T054", "T055", "T056", "T057", "T058"],
    "FR-002": ["T054", "T057"],
    "FR-003": ["T029", "T034", "T039", "T057"],
    "FR-004": ["T028", "T033", "T038", "T057"],
    "FR-005": ["T027", "T032", "T037", "T051", "T052", "T053"],
    "FR-006": ["T026", "T031", "T036", "T048", "T050"],
    "FR-007": ["T029", "T034", "T039", "T051"],
    "FR-008": ["T055", "T057"],
    "FR-009": [
        "T026", "T029", "T031", "T034", "T036", "T039", "T057", "T059", "T060"
    ],
    "FR-010": ["T029", "T034", "T039", "T058"],
    "FR-011": ["T028", "T033", "T038", "T048", "T049", "T050", "T051", "T052", "T053"],
    "FR-013": ["T025", "T049", "T052", "T054", "T059"],
    "FR-014": ["T025", "T035", "T054"],
    "FR-015": ["T026", "T031", "T036", "T053", "T059", "T060", "T061"],
    "QR-001": ["T028", "T033", "T038", "T051", "T052", "T053"],
    "QR-003": ["T028", "T033", "T038", "T051", "T052", "T053"],
    "QR-004": ["T029", "T034", "T039", "T051"],
    "QR-005": ["T055", "T056", "T057"],
    "QR-006": ["T025", "T030", "T035", "T054", "T045"],
    "QR-007": ["T028", "T033", "T038", "T057"],
    "SC-002": ["T028", "T029", "T051", "T053", "T060", "T061"],
    "SC-003": ["T033", "T034", "T050"],
    "SC-004": ["T038", "T039", "T049", "T052", "T059"],
    "SC-005": ["T055", "T056", "T057"],
    "SC-006": ["T057", "T045", "T046"],
    "SC-007": ["T054", "T045"],
    "SC-008": ["T025", "T030", "T035", "T054", "T045"],
}

V62_TASKS = {"T048", "T049", "T050", "T051", "T052", "T053", "T059", "T060", "T061"}
V62_ARTIFACTS = (
    "literature_refresh.json",
    "d4_structural_input_audit.json",
    "a4_rationale_asset_audit.json",
    "c5_counterfactual_feasibility_audit.json",
    "d4_crossfit_plan.json",
    "c5_generation_audit_plan.json",
    "c5_generation/requests.jsonl",
    "status.json",
)


def build_audit(repo: Path) -> dict:
    for requirement, tasks in TASK_AMENDMENTS.items():
        frozen.TRACEABILITY[requirement]["verification_tasks"] = list(tasks)
    report = frozen.build_audit(repo)
    tasks_text = (repo / "docs/TASKS.md").read_text(encoding="utf-8")
    incomplete = sorted(task for task in V62_TASKS if not frozen._checked_task(tasks_text, task))
    v62_root = repo / "runs/stages/R1/r1-v62-20260920"
    missing = sorted(name for name in V62_ARTIFACTS if not (v62_root / name).is_file())
    if incomplete:
        report["findings"].append(
            {"code": "v62-task-open", "message": f"v6.2 tasks not complete: {incomplete}"}
        )
    if missing:
        report["findings"].append(
            {"code": "v62-artifact-missing", "message": f"v6.2 artifacts missing: {missing}"}
        )
    report["status"] = "pass" if not report["findings"] else "blocked"
    report["amendment"] = {
        "reason": "map withdrawn consumer factorial and admitted R1 v6.2 tasks",
        "script": "scripts/audit_r1_v62_consistency.py",
        "script_sha256": frozen.sha256_file(Path(__file__).resolve()),
        "frozen_v61_audit_unchanged": True,
        "v62_tasks": sorted(V62_TASKS),
        "v62_artifact_sha256": {
            name: frozen.sha256_file(v62_root / name)
            for name in V62_ARTIFACTS
            if (v62_root / name).is_file()
        },
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = build_audit(args.repo_root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"{report['status'].upper()}: {report['coverage']['mapped_requirements']} mapped")
    for item in report["findings"]:
        print(f"  {item['code']}: {item['message']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
