import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_load_script("calibrate_d4_relation_posteriors")
_load_script("audit_d4_class_weight_correction")
audit = _load_script("audit_d4_dirichlet_holdout")


def test_document_split_is_deterministic_disjoint_and_uses_frozen_halves() -> None:
    document_ids = [f"doc-{index}" for index in range(9)]

    calibration, gate = audit.split_document_ids(3, document_ids)
    repeated = audit.split_document_ids(3, list(reversed(document_ids)))

    assert (calibration, gate) == repeated
    assert len(calibration) == 4
    assert len(gate) == 5
    assert set(calibration).isdisjoint(gate)
    assert set(calibration) | set(gate) == set(document_ids)


def test_document_split_rejects_duplicate_ids() -> None:
    with pytest.raises(ValueError, match="unique"):
        audit.split_document_ids(1, ["same", "same"])


def test_decision_metrics_count_wrong_subtype_as_fp_and_fn() -> None:
    labels = np.asarray([1, 2, 0, 0])
    predictions = np.asarray([2, 2, 1, 0])

    metrics = audit._decision_metrics(predictions, labels)

    assert metrics["tp"] == 1
    assert metrics["fp"] == 2
    assert metrics["fn"] == 1
    assert metrics["causal_exact_subtype_f1"] == pytest.approx(0.4)


def test_preregistered_gate_constants_are_not_tunable_cli_arguments() -> None:
    assert audit.MINIMUM_CAUSAL_F1 == 0.300
    assert audit.MINIMUM_BRIER_IMPROVEMENT == 0.0027
    assert audit.SPLIT_NAMESPACE == "r1-v62-c25r3"
