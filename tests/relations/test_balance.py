"""Tests for adaptive relation-family balancing (pure CPU, numpy only)."""

from __future__ import annotations

import numpy as np
import pytest

from ekg.relations.balance import (
    ADAPTIVE_WORKPOINT,
    ALL_COMPONENTS,
    IGNORE_INDEX,
    NORMALIZED_RISK,
    FamilyRiskNormalizer,
    WorkPointController,
    best_none_shift,
    validate_components,
)


def f1_at_shift(logits: np.ndarray, targets: np.ndarray, shift: float) -> float:
    """Independent, obvious implementation the fast path is checked against."""
    scored = targets != IGNORE_INDEX
    logits, targets = logits[scored], targets[scored]
    shifted = logits.copy()
    shifted[:, 0] += shift
    pred = shifted.argmax(axis=1)
    tp = int(((pred == targets) & (targets > 0)).sum())
    fp = int(((pred > 0) & (pred != targets)).sum())
    fn = int(((targets > 0) & (pred != targets)).sum())
    return 0.0 if tp == 0 else 2 * tp / (2 * tp + fp + fn)


def test_components_are_validated_and_canonically_ordered() -> None:
    assert validate_components([ADAPTIVE_WORKPOINT, NORMALIZED_RISK]) == ALL_COMPONENTS
    assert validate_components([]) == ()
    with pytest.raises(ValueError, match="unknown family-balance components"):
        validate_components(["gradnorm"])
    with pytest.raises(ValueError, match="duplicate"):
        validate_components([NORMALIZED_RISK, NORMALIZED_RISK])


def test_risk_normalizer_seeds_from_the_first_loss_then_smooths() -> None:
    normalizer = FamilyRiskNormalizer(["causal", "temporal"], decay=0.5)
    # The first observation seeds the EMA, so step one is already normalized
    # instead of passing a raw magnitude through.
    assert normalizer.update("causal", 4.0) == 4.0
    assert normalizer.update("causal", 2.0) == 3.0
    # Families are tracked separately -- that is the entire point.
    assert normalizer.update("temporal", 10.0) == 10.0
    assert normalizer.scales["causal"] == 3.0

    with pytest.raises(KeyError):
        normalizer.update("subevent", 1.0)
    with pytest.raises(ValueError, match="non-finite"):
        normalizer.update("causal", float("nan"))


def test_risk_normalizer_never_divides_by_zero() -> None:
    normalizer = FamilyRiskNormalizer(["causal"])
    assert normalizer.update("causal", 0.0) > 0.0


def test_best_shift_is_exact_and_round_trips_through_an_independent_scorer() -> None:
    rng = np.random.default_rng(13)
    n = 400
    targets = rng.integers(0, 3, size=n)
    logits = rng.normal(size=(n, 3))
    # Make the positives weakly separable, and bias NONE upward so the model
    # under-predicts -- the mirror image of the measured causal defect.
    logits[targets > 0, 1:] += 0.8
    logits[:, 0] += 1.5

    shift, f1, f1_at_zero = best_none_shift(logits, targets)
    assert f1_at_zero == pytest.approx(f1_at_shift(logits, targets, 0.0))
    assert f1 == pytest.approx(f1_at_shift(logits, targets, shift))
    # It is an optimum, not just an improvement: no other cut scores higher.
    margins = (np.delete(logits, 0, axis=1).max(axis=1) - logits[:, 0])
    grid = np.concatenate([margins - 1e-6, margins + 1e-6, [-10.0, 10.0]])
    assert f1 >= max(f1_at_shift(logits, targets, float(s)) for s in grid) - 1e-9
    assert f1 > f1_at_zero


def test_best_shift_ignores_pairs_the_protocol_does_not_score() -> None:
    logits = np.array([[0.0, 5.0], [0.0, 5.0], [5.0, 0.0], [0.0, 5.0]])
    targets = np.array([1, 1, 0, IGNORE_INDEX])
    shift, f1, _ = best_none_shift(logits, targets)
    assert f1 == pytest.approx(1.0)
    # The ignored row would have been a false positive had it been counted.
    assert f1_at_shift(logits, targets, shift) == pytest.approx(1.0)


def test_best_shift_refuses_a_family_with_nothing_to_measure() -> None:
    logits = np.zeros((3, 2))
    with pytest.raises(ValueError, match="no gold positive"):
        best_none_shift(logits, np.zeros(3, dtype=int))
    with pytest.raises(ValueError, match="no scoreable pair"):
        best_none_shift(logits, np.full(3, IGNORE_INDEX))
    with pytest.raises(ValueError, match=r"logits must be"):
        best_none_shift(np.zeros((3, 1)), np.zeros(3, dtype=int))


def test_controller_accumulates_damped_offsets_and_records_the_trajectory() -> None:
    logits = np.array([[3.0, 0.0], [3.0, 0.0], [0.0, 3.0], [3.0, 0.0]])
    targets = np.array([1, 1, 1, 0])
    controller = WorkPointController(["causal"], damping=0.5)

    first = controller.observe(1, "causal", logits, targets)
    # NONE dominates three of four rows, so the optimum shifts NONE *down*.
    assert first < 0
    second = controller.observe(2, "causal", logits, targets)
    assert second == pytest.approx(first + 0.5 * controller.trajectory[-1]["measured_shift"])

    assert [row["epoch"] for row in controller.trajectory] == [1, 2]
    assert controller.trajectory[0]["offset_before"] == 0.0
    assert controller.trajectory[0]["dev_f1_at_shift"] > controller.trajectory[0]["dev_f1_at_zero"]
    with pytest.raises(KeyError):
        controller.observe(3, "temporal", logits, targets)
