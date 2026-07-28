"""Probability calibration: isotonic fit, reliability curve, ECE improvement."""

from __future__ import annotations

import random

import pytest

from ekg.core.calibration import IsotonicProbabilityCalibrator, reliability_curve
from ekg.core.eval import expected_calibration_error


def _overconfident_stream(n: int = 2000, seed: int = 0):
    """Scores whose true accuracy is `score ** 2` — systematically overconfident."""
    rng = random.Random(seed)
    scores = [rng.random() for _ in range(n)]
    correct = [rng.random() < s**2 for s in scores]
    return scores, correct


def test_isotonic_calibration_reduces_ece() -> None:
    scores, correct = _overconfident_stream()
    cut = len(scores) // 2
    calibrator = IsotonicProbabilityCalibrator().fit(scores[:cut], correct[:cut])
    calibrated = calibrator.transform(scores[cut:])

    raw_ece = expected_calibration_error(scores[cut:], correct[cut:])
    cal_ece = expected_calibration_error(calibrated, correct[cut:])
    assert cal_ece < raw_ece / 2
    assert all(0.0 <= p <= 1.0 for p in calibrated)


def test_calibration_is_monotone() -> None:
    scores, correct = _overconfident_stream()
    calibrator = IsotonicProbabilityCalibrator().fit(scores, correct)
    probe = [i / 20 for i in range(21)]
    mapped = calibrator.transform(probe)
    assert mapped == sorted(mapped)


def test_transform_before_fit_is_fail_fast() -> None:
    with pytest.raises(RuntimeError, match="fit"):
        IsotonicProbabilityCalibrator().transform([0.5])


def test_fit_rejects_mismatched_lengths() -> None:
    with pytest.raises(ValueError, match="same length"):
        IsotonicProbabilityCalibrator().fit([0.1, 0.2], [True])


def test_calibrator_round_trips_through_disk(tmp_path) -> None:
    scores, correct = _overconfident_stream(400)
    calibrator = IsotonicProbabilityCalibrator().fit(scores, correct)
    path = tmp_path / "calibrator.json"
    calibrator.save(path)
    reloaded = IsotonicProbabilityCalibrator.load(path)
    assert reloaded.transform(scores[:20]) == calibrator.transform(scores[:20])


def test_reliability_curve_reports_populated_bins_only() -> None:
    curve = reliability_curve([0.05, 0.15, 0.95], [False, True, True], n_bins=10)
    assert [b["bin"] for b in curve] == [0, 1, 9]
    assert curve[0]["count"] == 1
    assert curve[2]["accuracy"] == 1.0
    assert sum(b["count"] for b in curve) == 3
