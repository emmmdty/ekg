"""Train labels stay on train; null mass is separate from real antecedent ranking."""

import importlib.util
import math
from pathlib import Path

import pytest


def script():
    path = Path(__file__).resolve().parents[2] / 'scripts/run_frozen_null_control.py'
    assert path.exists(), 'null control entrypoint missing'
    spec = importlib.util.spec_from_file_location('null_control', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_first_nonsingleton_is_not_a_repeat():
    gold = {'events': [{'id': 'e', 'mention': [{'id': 'a'}, {'id': 'c'}]},
                       {'id': 'f', 'mention': [{'id': 'b'}]}]}
    assert script().newness_labels(gold, ['a', 'b', 'c']) == [0, 0, 1]


def test_supervision_requires_exact_mention_coverage():
    gold = {'events': [{'id': 'e', 'mention': [{'id': 'a'}]}]}
    with pytest.raises(ValueError):
        script().newness_labels(gold, ['unknown'])


def test_null_mass_preserves_complete_rows_and_real_ranking():
    rows = script().probability_rows(['a', 'b', 'c'], [[], [0], [0, 0]],
                                     [100, math.log(4), math.log(4)],
                                     {'a': 'T', 'b': 'T', 'c': 'T'})
    assert rows[0] == [1]
    assert rows[1] == pytest.approx([0.8, 0.2])
    assert rows[2] == pytest.approx([0.4, 0.4, 0.2])


def test_cross_type_evidence_cannot_create_a_link():
    rows = script().probability_rows(['a', 'b'], [[], [100]], [0, 100],
                                     {'a': 'T', 'b': 'U'})
    assert rows == [[1], [0, 1]]


def test_feature_context_is_limited_to_legal_prior_mentions():
    torch = pytest.importorskip('torch')
    features = script().feature_rows(torch.tensor([[1.], [3.], [9.]]),
                                    [[], [0], [50, 0]], ['T', 'T', 'U'], torch)
    assert features[0].tolist() == [1, 0, 0, 0, 0, 0]
    assert features[1].tolist() == pytest.approx([3, 1, 1, 0, 0, math.log(2)])
    assert features[2].tolist() == [9, 0, 0, 0, 0, 0]


def test_shuffle_only_changes_semantic_blocks_in_prespecified_groups():
    import numpy as np

    features = np.array([[1., 2., 3., 0., 0., 1.], [4., 5., 6., 0., 0., 1.]])
    result = script().shuffle_semantics(features, ['d', 'd'], ['T', 'T'], [1, 1])
    assert sorted(result[:, 0]) == [1, 4]
    assert result[:, 3:].tolist() == features[:, 3:].tolist()
    assert sorted(map(tuple, result[:, :3])) == [(1., 2., 3.), (4., 5., 6.)]


def test_nonfinite_null_logits_fail():
    with pytest.raises(ValueError):
        script().probability_rows(['a'], [[]], [float('nan')], {'a': 'T'})


def test_training_budget_cannot_drift():
    import json

    root = Path(__file__).resolve().parents[2]
    config = json.loads((root / 'configs/c5_frozen_null_control_20261013.json').read_text())
    config['training']['epochs'] = 11
    with pytest.raises(ValueError, match='training'):
        script().validate_settings(config)
