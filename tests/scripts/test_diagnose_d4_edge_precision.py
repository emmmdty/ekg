import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


diagnose = _load_script("diagnose_d4_edge_precision")


def test_the_diagnostic_declares_itself_and_keeps_the_frozen_rule() -> None:
    # A cutoff curve is one careless copy-paste away from becoming a tuned
    # threshold, so the marker and the unchanged rule are asserted, not assumed.
    assert diagnose.CUTOFFS[0] == 0.0
    assert tuple(sorted(diagnose.CUTOFFS)) == diagnose.CUTOFFS
    source = (ROOT / "scripts/diagnose_d4_edge_precision.py").read_text(encoding="utf-8")
    assert '"diagnostic_only": True' in source
    assert "argmax_k w_k p_k (unchanged; this is not a sweep)" in source
