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
    position_none_offsets,
    validate_components,
    workpoint_key,
)
from ekg.relations.pairs import CROSS_SENTENCE, SAME_SENTENCE


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


def test_controller_moves_against_the_measured_shift_and_records_the_trajectory() -> None:
    logits = np.array([[3.0, 0.0], [3.0, 0.0], [0.0, 3.0], [3.0, 0.0]])
    targets = np.array([1, 1, 1, 0])
    controller = WorkPointController(["causal"], damping=0.5)

    first = controller.observe(1, "causal", logits, targets)
    measured = controller.trajectory[0]["measured_shift"]
    # NONE dominates three of four rows, so the family is under-emitting and the
    # measured shift is negative ("cut lower"). The offset must move the *other*
    # way: it is added to NONE inside the loss, and cross-entropy answers by
    # pushing the raw NONE logit in the opposite direction. Getting this sign
    # backwards is a positive feedback loop, not a slow start.
    assert measured < 0
    assert first == pytest.approx(-0.5 * measured)
    assert first > 0

    second = controller.observe(2, "causal", logits, targets)
    assert second == pytest.approx(first - 0.5 * controller.trajectory[-1]["measured_shift"])

    assert [row["epoch"] for row in controller.trajectory] == [1, 2]
    assert controller.trajectory[0]["offset_before"] == 0.0
    assert controller.trajectory[0]["dev_f1_at_shift"] > controller.trajectory[0]["dev_f1_at_zero"]
    with pytest.raises(KeyError):
        controller.observe(3, "temporal", logits, targets)


def test_closed_loop_contracts_instead_of_running_away() -> None:
    """The loop against a model that fully absorbs the offset it was trained under.

    Training with `+b` on the NONE logit drives the *raw* NONE logit down by `b`,
    so the raw margin a later epoch measures is `calibrated + b`. Iterating must
    contract toward the offset that makes a plain argmax optimal. The first
    version of this loop had the update sign inverted: each epoch multiplied the
    offset by 1.5 instead of halving the error, and 50 epochs of that reached
    1e7 and took the model with it (`logs/a32_workpoint.log`).
    """
    rng = np.random.default_rng(7)
    n = 600
    targets = rng.integers(0, 2, size=n)
    calibrated = rng.normal(size=n) + 1.2 * targets - 0.9  # under-emitting model

    controller = WorkPointController(["causal"], damping=0.5)
    offset, measured = 0.0, []
    for epoch in range(12):
        logits = np.stack([np.zeros(n), calibrated + offset], axis=1)
        offset = controller.observe(epoch, "causal", logits, targets)
        measured.append(abs(controller.trajectory[-1]["measured_shift"]))

    assert measured[-1] < measured[0] / 4, "the loop is not contracting"
    assert abs(offset) < 5.0, "the offset ran away"
    # Converged means the plain argmax is already at this family's optimum.
    final = np.stack([np.zeros(n), calibrated + offset], axis=1)
    _, best_f1, f1_at_zero = best_none_shift(final, targets)
    assert f1_at_zero == pytest.approx(best_f1, abs=0.02)


def test_position_workpoints_are_measured_and_applied_independently() -> None:
    same_key = workpoint_key("causal", SAME_SENTENCE)
    cross_key = workpoint_key("causal", CROSS_SENTENCE)
    controller = WorkPointController([same_key, cross_key], damping=0.5)

    # Same-sentence pairs under-emit: the optimal cut is lower, so the train-time
    # NONE offset must move positive (the existing sign regression).
    same_logits = np.array([[3.0, 0.0], [3.0, 0.0], [0.0, 3.0], [3.0, 0.0]])
    same_targets = np.array([1, 1, 1, 0])
    same_offset = controller.observe(1, same_key, same_logits, same_targets)

    # Cross-sentence pairs over-emit: only the highest-margin row is truly positive,
    # so the optimal cut is higher and its train-time offset moves negative.
    cross_logits = np.stack([np.zeros(4), np.array([0.5, 0.4, 3.0, 0.3])], axis=1)
    cross_targets = np.array([0, 0, 1, 0])
    cross_offset = controller.observe(1, cross_key, cross_logits, cross_targets)

    assert same_offset > 0
    assert cross_offset < 0
    mapped = position_none_offsets(
        "causal",
        [SAME_SENTENCE, CROSS_SENTENCE, SAME_SENTENCE],
        controller.offsets,
    )
    assert mapped.tolist() == pytest.approx([same_offset, cross_offset, same_offset])
    # A mutation that collapses both position buckets to one family offset would
    # make these equal and is therefore caught by this fixture.
    assert mapped[0] != mapped[1]


def test_position_workpoint_rejects_unknown_or_missing_buckets() -> None:
    with pytest.raises(ValueError, match="unknown relation position"):
        workpoint_key("causal", "adjacent")
    with pytest.raises(KeyError):
        position_none_offsets(
            "causal",
            [SAME_SENTENCE],
            {workpoint_key("causal", CROSS_SENTENCE): 0.0},
        )
