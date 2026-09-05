from __future__ import annotations

import importlib.util
from pathlib import Path

from ekg.factuality.baselines import BASELINE_POOLINGS

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "collect_r1_factuality_oof", ROOT / "scripts/collect_r1_factuality_oof.py"
)
assert SPEC and SPEC.loader
collector = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(collector)


def test_baseline_roster_has_cls_and_dynamic_multi() -> None:
    assert BASELINE_POOLINGS == ("cls", "dynamic_multi")
    assert callable(collector.collect)
