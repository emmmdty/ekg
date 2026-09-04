from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "report_r1_prospective_power", ROOT / "scripts/report_r1_prospective_power.py"
)
assert SPEC and SPEC.loader
power = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(power)


def test_muc_score_from_counts() -> None:
    counts = np.array([8.0, 10.0, 9.0, 10.0])

    assert power._muc_score(counts)[0] == pytest.approx(2 * 0.8 * 0.9 / 1.7)


def test_macro_f1_perfect_confusion() -> None:
    confusion = np.eye(len(power.FACT_CLASSES))

    assert power._macro_f1(confusion.ravel())[0] == 1.0


def test_power_curve_is_deterministic_and_detects_large_correction() -> None:
    base = np.array([[0.0, 1.0, 0.0, 1.0]] * 8)
    correction_docs = np.arange(8)
    correction_deltas = np.array([[1.0, 0.0, 1.0, 0.0]] * 8)
    bootstrap = np.eye(8, dtype=int)
    kwargs = {
        "steps": (8,),
        "score": power._muc_score,
        "bootstrap_counts": bootstrap,
        "trials": 3,
    }

    first = power._power_curve(
        base,
        correction_docs,
        correction_deltas,
        rng=np.random.default_rng(7),
        **kwargs,
    )
    second = power._power_curve(
        base,
        correction_docs,
        correction_deltas,
        rng=np.random.default_rng(7),
        **kwargs,
    )

    assert first == second
    assert first[0]["power"] == 1.0
