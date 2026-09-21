import numpy as np
import pytest

from ekg.relations.calibration import (
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
