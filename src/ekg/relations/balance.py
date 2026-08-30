"""Adaptive relation-family balancing for the joint pair classifier.

Two measured facts, from `docs/results/PHASE_A.md`, decide this module's shape.

**The families do not share a working point.** Re-cutting the reproduction base's
own emitted edges at a grid of confidence thresholds moves causal F1 31.42 ->
33.15 (best at 0.65), leaves subevent monotonically *worse* than its uncut 30.62,
and drives temporal below its pre-registered 50.63 guardrail past 0.60. One
global dial -- which is what a single class-weight exponent is -- cannot put
three families in three different places.

**Re-cutting alone is not enough anyway.** Its causal ceiling, 33.15, sits 0.02
*below* the frozen primary anchor. So a mechanism that only slides along the
existing precision/recall curve cannot clear the gate; it has to change the
curve, which means changing what the encoder learns.

Hence two components, switchable independently so the ablation can say which one
does the work:

``normalized_risk``
    The objective is a plain sum of three family cross-entropies. Their
    magnitudes are not comparable -- temporal carries ~39x the gold pairs of
    subevent and seven subtypes against two -- so "whoever has the biggest loss
    dominates the shared encoder" is the rule currently in force, by accident.
    Dividing each family by a detached EMA of its own scale makes the three
    contribute comparably, which is what "family balance" has to mean before any
    working-point argument is even well posed.

``adaptive_workpoint``
    Each epoch, measure on internal-dev where each family's F1-optimal decision
    boundary actually is -- exactly, by sweeping the sorted NONE-vs-best-positive
    margins, not over a grid -- and feed that offset back into the *training*
    loss as an additive shift on the NONE logit.

    Applying the shift during training and leaving inference untouched is
    deliberate and is the whole point (cf. Menon et al., *Long-tail learning via
    logit adjustment*, ICLR 2021). Adding the same bias at train and test time
    would cancel: cross-entropy would simply teach the model to subtract it
    again. Adjusting only the loss makes the model bake the shifted boundary
    into its representation, and leaves the test-time rule a plain argmax -- so
    nothing the mechanism gains can be waved away as test-time thresholding,
    which the phase contract excludes.

    The offsets accumulate across epochs and the loop converges when the newly
    measured optimum stops moving, which is also the signal that a family has
    reached its own working point. `LOOP_DAMPING` is the damping of that control
    loop, not a tuned dial.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

import numpy as np

__all__ = [
    "ALL_COMPONENTS",
    "NORMALIZED_RISK",
    "ADAPTIVE_WORKPOINT",
    "CONFIG_FILE",
    "IGNORE_INDEX",
    "LOOP_DAMPING",
    "NONE_INDEX",
    "validate_components",
    "FamilyRiskNormalizer",
    "WorkPointController",
    "best_none_shift",
]

CONFIG_FILE = "family_balance.json"

NORMALIZED_RISK = "normalized_risk"
ADAPTIVE_WORKPOINT = "adaptive_workpoint"
ALL_COMPONENTS = (NORMALIZED_RISK, ADAPTIVE_WORKPOINT)

# Damping of the working-point control loop. Taking the freshly measured optimum
# whole (1.0) makes successive epochs overshoot each other, because each estimate
# is made on a model that was itself trained under the previous offset.
LOOP_DAMPING = 0.5

# Index of the NONE class in every family's subtype tuple.
NONE_INDEX = 0

# Targets the official protocol does not score for a family (a TIMEX endpoint
# under causal/subevent); torch's cross-entropy default, kept identical here.
IGNORE_INDEX = -100


def validate_components(components: Iterable[str]) -> tuple[str, ...]:
    selected = tuple(components)
    unknown = set(selected) - set(ALL_COMPONENTS)
    if unknown:
        raise ValueError(f"unknown family-balance components: {sorted(unknown)}")
    if len(set(selected)) != len(selected):
        raise ValueError("duplicate family-balance components")
    return tuple(c for c in ALL_COMPONENTS if c in selected)


class FamilyRiskNormalizer:
    """Detached EMA of each family's own loss scale.

    Returns the divisor to apply to that family's loss. The first observation
    seeds the EMA, so the very first step is already normalized rather than
    passing an arbitrary raw magnitude through.
    """

    def __init__(self, families: Sequence[str], decay: float = 0.9) -> None:
        if not 0.0 < decay < 1.0:
            raise ValueError(f"decay must be in (0, 1), got {decay}")
        self.decay = decay
        self.scales: dict[str, float] = dict.fromkeys(families, 0.0)

    def update(self, family: str, loss_value: float) -> float:
        if family not in self.scales:
            raise KeyError(f"unknown family {family!r}")
        if not np.isfinite(loss_value):
            raise ValueError(f"{family}: non-finite loss {loss_value}")
        current = self.scales[family]
        self.scales[family] = (
            loss_value if current == 0.0 else self.decay * current + (1 - self.decay) * loss_value
        )
        # A family whose loss has genuinely reached zero must not divide by it.
        return max(self.scales[family], 1e-8)


def best_none_shift(
    logits: np.ndarray, targets: np.ndarray
) -> tuple[float, float, float]:
    """The additive NONE-logit shift maximizing this family's positive-class F1.

    Only the NONE column moves, so a pair is predicted positive exactly when its
    margin (best positive logit minus the NONE logit) exceeds the shift. Sorting
    the margins therefore enumerates *every* decision the shift can produce, and
    the optimum is found exactly rather than sampled on a grid.

    Returns `(shift, f1_at_shift, f1_at_zero)`. F1 is micro over the positive
    classes, the same quantity the trainer's dev metric and the official scorer
    average -- a shift chosen on one axis and reported on another is the trap
    that already cost this project a chapter's conclusion.
    """
    if logits.ndim != 2 or logits.shape[1] < 2:
        raise ValueError(f"logits must be (n, k>=2), got {logits.shape}")
    if targets.shape != (logits.shape[0],):
        raise ValueError(f"targets {targets.shape} does not match logits {logits.shape}")

    scored = targets != IGNORE_INDEX
    logits, targets = logits[scored], targets[scored]
    if not len(targets):
        raise ValueError("no scoreable pair for this family")

    positive = np.delete(logits, NONE_INDEX, axis=1)
    best_positive = positive.max(axis=1)
    # +1 because column NONE_INDEX was removed before the argmax.
    positive_class = positive.argmax(axis=1) + 1
    margin = best_positive - logits[:, NONE_INDEX]

    gold_positive = targets > 0
    n_gold = int(gold_positive.sum())
    if not n_gold:
        raise ValueError("no gold positive for this family")

    order = np.argsort(-margin, kind="stable")
    margin, positive_class, targets = margin[order], positive_class[order], targets[order]
    correct = (positive_class == targets).astype(np.int64)

    # Walking the sorted margins, the first i pairs are predicted positive.
    tp = np.concatenate([[0], np.cumsum(correct)])
    n_pred = np.arange(len(margin) + 1)
    denominator = n_pred + n_gold
    f1 = np.where(denominator > 0, 2 * tp / np.maximum(denominator, 1), 0.0)

    best_i = int(f1.argmax())
    # A shift strictly between the two margins that bracket the cut reproduces it.
    if best_i == 0:
        shift = float(margin[0]) + 1.0
    elif best_i == len(margin):
        shift = float(margin[-1]) - 1.0
    else:
        shift = float((margin[best_i - 1] + margin[best_i]) / 2)
    at_zero = float(f1[int((margin > 0).sum())])
    return shift, float(f1[best_i]), at_zero


class WorkPointController:
    """Per-family NONE-logit offsets, accumulated from what internal-dev measures.

    The offsets are applied to the *training* loss only; `trajectory` keeps every
    epoch's measurement so a flat tail (the loop having converged) or a family
    still drifting is visible in the record instead of inferred.
    """

    def __init__(self, families: Sequence[str], damping: float = LOOP_DAMPING) -> None:
        if not 0.0 < damping <= 1.0:
            raise ValueError(f"damping must be in (0, 1], got {damping}")
        self.damping = damping
        self.offsets: dict[str, float] = dict.fromkeys(families, 0.0)
        self.trajectory: list[dict] = []

    def observe(self, epoch: int, family: str, logits: np.ndarray, targets: np.ndarray) -> float:
        if family not in self.offsets:
            raise KeyError(f"unknown family {family!r}")
        shift, f1_at_shift, f1_at_zero = best_none_shift(logits, targets)
        previous = self.offsets[family]
        # Minus, not plus. The offset is added to the NONE logit *inside the
        # loss*, and cross-entropy answers by pushing the raw NONE logit the
        # other way -- so asking for "cut higher" (shift > 0) means subtracting.
        # With the sign inverted the loop multiplies its own error by 1.5 an
        # epoch: the first A3.2 run reached an offset of 1e7 by epoch 49 and
        # collapsed temporal to 0.000 F1.
        self.offsets[family] = previous - self.damping * shift
        self.trajectory.append(
            {
                "epoch": epoch,
                "family": family,
                "measured_shift": shift,
                "offset_before": previous,
                "offset_after": self.offsets[family],
                "dev_f1_at_shift": f1_at_shift,
                "dev_f1_at_zero": f1_at_zero,
            }
        )
        return self.offsets[family]
