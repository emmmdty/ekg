import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
CALIBRATE_SPEC = importlib.util.spec_from_file_location(
    "calibrate_d4_relation_posteriors",
    ROOT / "scripts/calibrate_d4_relation_posteriors.py",
)
assert CALIBRATE_SPEC is not None and CALIBRATE_SPEC.loader is not None
calibrate = importlib.util.module_from_spec(CALIBRATE_SPEC)
sys.modules[CALIBRATE_SPEC.name] = calibrate
CALIBRATE_SPEC.loader.exec_module(calibrate)

AUDIT_SPEC = importlib.util.spec_from_file_location(
    "audit_d4_class_weight_correction",
    ROOT / "scripts/audit_d4_class_weight_correction.py",
)
assert AUDIT_SPEC is not None and AUDIT_SPEC.loader is not None
audit = importlib.util.module_from_spec(AUDIT_SPEC)
sys.modules[AUDIT_SPEC.name] = audit
AUDIT_SPEC.loader.exec_module(audit)


def _run_metadata(*, alpha: str = "0.5") -> dict:
    return {
        "configuration": {
            "weight_alpha": alpha,
            "neg_ratio": "inf",
            "official_mention_expansion": True,
        },
        "protocol_binding": {
            "candidate_summaries": {
                "train": {
                    "population_counts": {
                        "ordered_mention_pairs": 1000,
                        "positive_causal:CAUSE": 50,
                        "positive_causal:PRECONDITION": 150,
                    }
                }
            }
        },
    }


def test_training_class_weights_match_trainer_formula() -> None:
    weights, counts = audit.training_class_weights(_run_metadata())

    assert counts == [800, 50, 150]
    np.testing.assert_allclose(
        weights,
        np.sqrt(np.asarray([1000 / 2400, 1000 / 150, 1000 / 450])),
    )


def test_training_class_weights_reject_recipe_drift() -> None:
    with pytest.raises(ValueError, match="weight_alpha drifted"):
        audit.training_class_weights(_run_metadata(alpha="0.7"))


def test_selection_accumulator_reports_exact_subtype_f1_and_brier() -> None:
    raw = np.asarray([[0.2, 0.7, 0.1], [0.4, 0.5, 0.1], [0.8, 0.1, 0.1]])
    corrected = np.asarray([[0.4, 0.5, 0.1], [0.7, 0.2, 0.1], [0.9, 0.05, 0.05]])
    labels = np.asarray([1, 0, 0])
    accumulator = audit.SelectionAccumulator()

    accumulator.add(raw, corrected, labels)
    report = accumulator.report()

    assert report["raw_causal_f1"] == pytest.approx(2 / 3)
    assert report["corrected_causal_f1"] == 1.0
    assert report["corrected_multiclass_brier"] < report["raw_multiclass_brier"]
