import numpy as np
import pytest

from ekg.relations.calibration import (
    correct_class_weights,
    cost_sensitive_predictions,
    dirichlet_calibrate,
    fit_dirichlet_calibration,
    fit_temperature,
    multiclass_nll,
    temperature_scale,
)


def test_temperature_fit_reduces_nll_and_preserves_argmax() -> None:
    probabilities = np.asarray(
        [
            [0.80, 0.15, 0.05],
            [0.80, 0.15, 0.05],
            [0.10, 0.80, 0.10],
            [0.10, 0.15, 0.75],
        ],
        dtype=np.float64,
    )
    labels = np.asarray([0, 1, 1, 2], dtype=np.int64)

    fit = fit_temperature(probabilities, labels)
    calibrated = temperature_scale(probabilities, fit.inverse_temperature)

    assert fit.temperature > 0.0
    assert multiclass_nll(calibrated, labels) < multiclass_nll(probabilities, labels)
    np.testing.assert_array_equal(calibrated.argmax(axis=1), probabilities.argmax(axis=1))


def test_temperature_fit_recovers_known_softening() -> None:
    rows = []
    labels = []
    for target in range(3):
        base = np.full(3, 0.15, dtype=np.float64)
        base[target] = 0.70
        rows.extend([base] * 20)
        labels.extend([target] * 14)
        labels.extend([(target + 1) % 3] * 3)
        labels.extend([(target + 2) % 3] * 3)
    calibrated = np.asarray(rows, dtype=np.float64)
    label_array = np.asarray(labels, dtype=np.int64)
    overconfident = temperature_scale(calibrated, inverse_temperature=2.0)

    fit = fit_temperature(overconfident, label_array)
    restored = temperature_scale(overconfident, fit.inverse_temperature)

    assert fit.temperature == pytest.approx(2.0, rel=1e-6)
    assert multiclass_nll(restored, label_array) < multiclass_nll(
        overconfident, label_array
    )


@pytest.mark.parametrize(
    "probabilities",
    [
        np.asarray([[0.0, 0.5, 0.5]], dtype=np.float64),
        np.asarray([[0.2, 0.2, 0.2]], dtype=np.float64),
        np.asarray([[float("nan"), 0.5, 0.5]], dtype=np.float64),
    ],
)
def test_temperature_scaling_rejects_invalid_probabilities(
    probabilities: np.ndarray,
) -> None:
    with pytest.raises(ValueError):
        temperature_scale(probabilities, inverse_temperature=1.0)


def test_class_weight_correction_inverts_weighted_categorical_scores() -> None:
    posterior = np.asarray([[0.90, 0.07, 0.03], [0.30, 0.20, 0.50]])
    weights = np.asarray([0.5, 4.0, 2.0])
    weighted = posterior * weights
    weighted /= weighted.sum(axis=1, keepdims=True)

    corrected = correct_class_weights(weighted, weights)

    np.testing.assert_allclose(corrected, posterior, rtol=0.0, atol=1e-12)


def test_class_weight_correction_rejects_invalid_weights() -> None:
    probabilities = np.asarray([[0.8, 0.1, 0.1]])

    with pytest.raises(ValueError, match="finite and positive"):
        correct_class_weights(probabilities, np.asarray([1.0, 0.0, 2.0]))


def test_dirichlet_calibration_recovers_multiclass_probability_distortion() -> None:
    natural_rows = np.asarray(
        [[0.7, 0.2, 0.1], [0.2, 0.6, 0.2], [0.1, 0.2, 0.7]],
        dtype=np.float64,
    )
    raw_rows = np.square(natural_rows)
    raw_rows /= raw_rows.sum(axis=1, keepdims=True)
    probabilities = np.repeat(raw_rows, 100, axis=0)
    labels = np.concatenate(
        [
            np.repeat(np.arange(3), (70, 20, 10)),
            np.repeat(np.arange(3), (20, 60, 20)),
            np.repeat(np.arange(3), (10, 20, 70)),
        ]
    )

    fit = fit_dirichlet_calibration(probabilities, labels)
    calibrated = dirichlet_calibrate(probabilities, fit)

    assert fit.iterations < 1000
    assert multiclass_nll(calibrated, labels) < multiclass_nll(probabilities, labels)
    np.testing.assert_allclose(calibrated[::100], natural_rows, atol=1e-4)


def test_dirichlet_calibration_requires_every_class() -> None:
    probabilities = np.asarray([[0.8, 0.1, 0.1], [0.2, 0.7, 0.1]])
    labels = np.asarray([0, 1])

    with pytest.raises(ValueError, match="every class"):
        fit_dirichlet_calibration(probabilities, labels)


def test_cost_sensitive_predictions_are_separate_from_natural_argmax() -> None:
    probabilities = np.asarray([[0.8, 0.15, 0.05], [0.6, 0.3, 0.1]])
    weights = np.asarray([0.5, 4.0, 2.0])

    predictions = cost_sensitive_predictions(probabilities, weights)

    np.testing.assert_array_equal(probabilities.argmax(axis=1), [0, 0])
    np.testing.assert_array_equal(predictions, [1, 1])
