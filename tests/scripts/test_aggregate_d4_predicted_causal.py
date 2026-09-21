import importlib.util
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]


def _load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


aggregate = _load_script("aggregate_d4_predicted_causal")

LABELS = ("CT+", "PS+", "CT-", "PS-", "Uu")


def _brute_macro_f1(gold: list[str], predicted: list[str]) -> float:
    scores = []
    for label in LABELS:
        tp = sum(1 for g, p in zip(gold, predicted, strict=True) if g == p == label)
        n_pred = sum(1 for p in predicted if p == label)
        n_gold = sum(1 for g in gold if g == label)
        scores.append(2 * tp / (n_pred + n_gold) if n_pred + n_gold else 0.0)
    return sum(scores) / len(LABELS)


def test_confusion_macro_f1_matches_a_brute_force_scorer() -> None:
    generator = np.random.default_rng(13)
    gold = [LABELS[i] for i in generator.integers(0, 5, size=200)]
    predicted = [LABELS[i] for i in generator.integers(0, 5, size=200)]
    matrix = np.zeros((5, 5), dtype=np.int64)
    for g, p in zip(gold, predicted, strict=True):
        matrix[LABELS.index(g), LABELS.index(p)] += 1

    assert aggregate._macro_f1(matrix) == _brute_macro_f1(gold, predicted)
    per_class = aggregate._class_f1(matrix)
    assert sum(per_class.values()) / 5 == _brute_macro_f1(gold, predicted)


def test_per_document_matrices_split_by_document_and_sum_to_the_pool() -> None:
    document_ids = ["d1", "d2"]
    mentions = {"d1": ["m1", "m2"], "d2": ["m3"]}
    gold = {"m1": "CT+", "m2": "PS-", "m3": "Uu"}
    predicted = {"m1": "CT+", "m2": "CT+", "m3": "Uu"}

    matrices = aggregate.per_document_matrices(document_ids, mentions, gold, predicted)

    assert matrices.shape == (2, 25)
    assert matrices.sum() == 3
    assert matrices[1].reshape(5, 5)[4, 4] == 1
    assert matrices.sum(axis=0).reshape(5, 5)[3, 0] == 1


def test_paired_bootstrap_is_exactly_zero_for_identical_arms() -> None:
    generator = np.random.default_rng(7)
    arm = generator.integers(0, 4, size=(40, 25))

    result = aggregate.paired_bootstrap(arm, arm, draws=50, seed=13)

    assert result["delta"] == 0.0
    assert result["ci_low"] == result["ci_high"] == 0.0
    assert result["positive"] is False


def test_paired_bootstrap_detects_a_uniform_improvement() -> None:
    # `better` fixes one rare-class error in every document; `worse` keeps it.
    worse = np.zeros((60, 25), dtype=np.int64)
    better = np.zeros((60, 25), dtype=np.int64)
    for row in range(60):
        worse[row, 0] = better[row, 0] = 20  # CT+ correct
        worse[row, 3 * 5 + 0] = 1  # PS- predicted CT+
        better[row, 3 * 5 + 3] = 1  # PS- correct

    result = aggregate.paired_bootstrap(better, worse, draws=200, seed=13)

    assert result["delta"] > 0.0
    assert result["positive"] is True
    assert result["ci_low"] > 0.0


def test_frozen_gate_constants_match_the_contract() -> None:
    contract = (ROOT / "docs/phases/PHASE_D4_predicted_causal_residual.md").read_text(
        encoding="utf-8"
    )
    assert "`.583995`" in contract
    assert aggregate.MACRO_TARGET == 0.583995
    assert aggregate.FLOORS == {"PS-": 0.352456, "Uu": 0.166850}
    assert "`.352456`" in contract and "`.166850`" in contract
    assert aggregate.BOOTSTRAP_DRAWS == 10000
    assert "10,000" in contract
    assert aggregate.EXPECTED_DOCUMENTS == 2913
    assert aggregate.EXPECTED_MENTIONS == 73939
