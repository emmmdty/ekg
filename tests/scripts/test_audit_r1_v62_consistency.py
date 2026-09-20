import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "audit_r1_v62_consistency",
    ROOT / "scripts/audit_r1_v62_consistency.py",
)
assert SPEC is not None and SPEC.loader is not None
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


def test_consumer_amendment_contains_no_withdrawn_tasks() -> None:
    amended = {
        task
        for tasks in audit.TASK_AMENDMENTS.values()
        for task in tasks
    }

    assert not amended & {"T040", "T041", "T042", "T043", "T044"}
    assert {"T054", "T055", "T056", "T057", "T058"} <= amended
    assert audit.V62_TASKS <= amended
