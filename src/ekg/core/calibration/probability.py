"""Probability calibration: make a raw score mean what it claims.

The conformal calibrators in this package control a *risk level* (they answer
"where do I threshold to miss at most alpha?"). This module answers the other
question a downstream error budget needs: "when this stage says 0.8, is it right
80% of the time?" — the mapping from an uncalibrated score to a probability.

Isotonic regression is the fitter: non-parametric, monotone (so it never
reorders the ranking the score already encodes) and standard for calibration
when the calibration split has enough points. Fitting on a *held-out* split is
mandatory — the same lesson as the conformal fit, where fitting on train
inflated the fixture metrics.

`expected_calibration_error` (in `core.eval.faithfulness`) measures the result;
`reliability_curve` returns the per-bin numbers behind it for plotting.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

import numpy as np
from sklearn.isotonic import IsotonicRegression

__all__ = ["IsotonicProbabilityCalibrator", "reliability_curve"]


class IsotonicProbabilityCalibrator:
    """Monotone score -> probability map fitted on held-out (score, correct) pairs."""

    def __init__(self, thresholds: list[float] | None = None, values: list[float] | None = None):
        self._thresholds = thresholds
        self._values = values

    def fit(
        self, scores: Sequence[float], correct: Sequence[bool]
    ) -> IsotonicProbabilityCalibrator:
        if len(scores) != len(correct):
            raise ValueError("scores and correct must be the same length")
        if not scores:
            raise ValueError("cannot fit a calibrator on an empty calibration split")
        model = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip")
        model.fit(np.asarray(scores, dtype=float), np.asarray(correct, dtype=float))
        # Keep the fitted step function as plain data so the calibrator is
        # serializable and reloadable without a sklearn version handshake.
        self._thresholds = [float(x) for x in model.X_thresholds_]
        self._values = [float(y) for y in model.y_thresholds_]
        return self

    def transform(self, scores: Sequence[float]) -> list[float]:
        if self._thresholds is None or self._values is None:
            raise RuntimeError("calibrator must be fit before transform")
        mapped = np.interp(
            np.asarray(scores, dtype=float),
            np.asarray(self._thresholds),
            np.asarray(self._values),
        )
        return [float(min(1.0, max(0.0, p))) for p in mapped]

    def save(self, path: str | Path) -> None:
        if self._thresholds is None or self._values is None:
            raise RuntimeError("calibrator must be fit before save")
        Path(path).write_text(json.dumps({"x": self._thresholds, "y": self._values}))

    @classmethod
    def load(cls, path: str | Path) -> IsotonicProbabilityCalibrator:
        payload = json.loads(Path(path).read_text())
        return cls(payload["x"], payload["y"])


def reliability_curve(
    probs: Sequence[float], correct: Sequence[bool], n_bins: int = 10
) -> list[dict]:
    """Per-bin mean confidence vs realised accuracy — the ECE, unaggregated.

    Only populated bins are returned, so an empty bin never reads as a perfectly
    calibrated one.
    """
    if len(probs) != len(correct):
        raise ValueError("probs and correct must be the same length")
    conf_sum = [0.0] * n_bins
    acc_sum = [0.0] * n_bins
    count = [0] * n_bins
    for p, ok in zip(probs, correct, strict=True):
        b = min(n_bins - 1, max(0, int(p * n_bins)))
        conf_sum[b] += p
        acc_sum[b] += 1.0 if ok else 0.0
        count[b] += 1
    return [
        {
            "bin": b,
            "count": count[b],
            "confidence": conf_sum[b] / count[b],
            "accuracy": acc_sum[b] / count[b],
        }
        for b in range(n_bins)
        if count[b]
    ]
