"""Post-hoc calibration for exhaustive relation-family posteriors."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class TemperatureFit:
    """Result of one-dimensional validation-NLL temperature fitting."""

    temperature: float
    inverse_temperature: float
    iterations: int
    gradient: float


def validate_probabilities(probabilities: NDArray[np.float64]) -> None:
    """Reject arrays that cannot be converted back to finite softmax logits."""
    if probabilities.ndim != 2 or probabilities.shape[1] < 2:
        raise ValueError("probabilities must have shape (rows, classes>=2)")
    if probabilities.shape[0] == 0:
        raise ValueError("cannot calibrate an empty posterior population")
    if not np.isfinite(probabilities).all():
        raise ValueError("probabilities contain non-finite values")
    if not (probabilities > 0.0).all():
        raise ValueError("temperature scaling requires strictly positive probabilities")
    if not np.allclose(probabilities.sum(axis=1), 1.0, rtol=0.0, atol=1e-6):
        raise ValueError("posterior rows do not sum to one")


def _validate_labels(labels: NDArray[np.int64], rows: int, classes: int) -> None:
    if labels.shape != (rows,):
        raise ValueError("labels must have shape (rows,)")
    if not np.issubdtype(labels.dtype, np.integer):
        raise ValueError("labels must be integer class indices")
    if (labels < 0).any() or (labels >= classes).any():
        raise ValueError("labels contain an out-of-range class index")


def _softmax(logits: NDArray[np.float64]) -> NDArray[np.float64]:
    shifted = logits - logits.max(axis=1, keepdims=True)
    exponentials = np.exp(shifted)
    return exponentials / exponentials.sum(axis=1, keepdims=True)


def temperature_scale(
    probabilities: NDArray[np.float64], inverse_temperature: float
) -> NDArray[np.float64]:
    """Apply ``softmax(log(p) / T)`` where ``inverse_temperature = 1/T``."""
    validate_probabilities(probabilities)
    if not math.isfinite(inverse_temperature) or inverse_temperature <= 0.0:
        raise ValueError("inverse temperature must be finite and positive")
    return _softmax(np.log(probabilities) * inverse_temperature)


def scale_probability_tuple(
    probabilities: tuple[float, ...], inverse_temperature: float
) -> tuple[float, ...]:
    """Small-row equivalent of :func:`temperature_scale` for JSONL streaming."""
    if len(probabilities) < 2:
        raise ValueError("probability tuple must contain at least two classes")
    if not all(math.isfinite(value) and value > 0.0 for value in probabilities):
        raise ValueError("temperature scaling requires finite positive probabilities")
    if abs(math.fsum(probabilities) - 1.0) > 1e-6:
        raise ValueError("posterior row does not sum to one")
    if not math.isfinite(inverse_temperature) or inverse_temperature <= 0.0:
        raise ValueError("inverse temperature must be finite and positive")
    logits = [math.log(value) * inverse_temperature for value in probabilities]
    maximum = max(logits)
    exponentials = [math.exp(value - maximum) for value in logits]
    total = math.fsum(exponentials)
    return tuple(value / total for value in exponentials)


def correct_class_weights(
    probabilities: NDArray[np.float64], class_weights: NDArray[np.float64]
) -> NDArray[np.float64]:
    """Invert class-weighted categorical cross-entropy scores analytically."""
    validate_probabilities(probabilities)
    if class_weights.shape != (probabilities.shape[1],):
        raise ValueError("class weights must have shape (classes,)")
    if not np.isfinite(class_weights).all() or not (class_weights > 0.0).all():
        raise ValueError("class weights must be finite and positive")
    corrected = probabilities / class_weights
    return corrected / corrected.sum(axis=1, keepdims=True)


def multiclass_nll(
    probabilities: NDArray[np.float64], labels: NDArray[np.int64]
) -> float:
    validate_probabilities(probabilities)
    _validate_labels(labels, probabilities.shape[0], probabilities.shape[1])
    return float(-np.log(probabilities[np.arange(labels.size), labels]).mean())


def multiclass_brier(
    probabilities: NDArray[np.float64], labels: NDArray[np.int64]
) -> float:
    validate_probabilities(probabilities)
    _validate_labels(labels, probabilities.shape[0], probabilities.shape[1])
    targets = np.zeros_like(probabilities)
    targets[np.arange(labels.size), labels] = 1.0
    return float(np.square(probabilities - targets).sum(axis=1).mean())


def fit_temperature(
    probabilities: NDArray[np.float64],
    labels: NDArray[np.int64],
    *,
    gradient_tolerance: float = 1e-10,
    maximum_iterations: int = 80,
) -> TemperatureFit:
    """Minimize unweighted validation NLL by convex bisection over ``1/T``.

    For fixed logits, NLL is convex in inverse temperature. Its derivative is
    monotone, so bracketing the unique zero avoids optimizer/version drift.
    """
    validate_probabilities(probabilities)
    rows, classes = probabilities.shape
    _validate_labels(labels, rows, classes)
    if gradient_tolerance <= 0.0 or not math.isfinite(gradient_tolerance):
        raise ValueError("gradient tolerance must be finite and positive")
    if maximum_iterations <= 0:
        raise ValueError("maximum iterations must be positive")

    logits = np.log(probabilities)
    true_logits = logits[np.arange(rows), labels]

    def gradient(inverse_temperature: float) -> float:
        calibrated = _softmax(logits * inverse_temperature)
        expected_logits = np.sum(calibrated * logits, axis=1)
        return float(np.mean(expected_logits - true_logits))

    lower = 0.0
    lower_gradient = gradient(lower)
    if lower_gradient >= 0.0:
        raise ValueError("validation NLL has no finite positive-temperature optimum")

    upper = 1.0
    upper_gradient = gradient(upper)
    expansions = 0
    while upper_gradient < 0.0:
        upper *= 2.0
        expansions += 1
        if not math.isfinite(upper) or expansions > 60:
            raise ValueError("could not bracket a finite temperature optimum")
        upper_gradient = gradient(upper)

    midpoint = upper
    midpoint_gradient = upper_gradient
    iterations = 0
    for iteration in range(1, maximum_iterations + 1):
        iterations = iteration
        midpoint = (lower + upper) / 2.0
        midpoint_gradient = gradient(midpoint)
        if abs(midpoint_gradient) <= gradient_tolerance:
            break
        if midpoint_gradient < 0.0:
            lower = midpoint
        else:
            upper = midpoint

    if midpoint <= 0.0 or not math.isfinite(midpoint):
        raise ValueError("temperature fit did not produce a positive finite solution")
    return TemperatureFit(
        temperature=1.0 / midpoint,
        inverse_temperature=midpoint,
        iterations=iterations,
        gradient=midpoint_gradient,
    )
