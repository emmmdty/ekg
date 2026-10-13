"""A given-type control changes ranking eligibility, preserving scorer and dummy."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def module():
    spec = importlib.util.spec_from_file_location(
        'typed_coref_control', ROOT / 'scripts/replay_typed_coref_control.py')
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def test_mask_preserves_valid_scores_dummy_and_full_shape():
    original = [[1.0], [0.8, 0.2], [0.4, 0.35, 0.25]]
    ranked = module().constrain_types(['a', 'b', 'c'], original,
                                     {'a': 'A', 'b': 'B', 'c': 'B'})
    assert ranked == [[1.0], [-1000, 0.2], [-1000, 0.35, 0.25]]
    assert original == [[1.0], [0.8, 0.2], [0.4, 0.35, 0.25]]


def test_same_types_are_exact_identity():
    original = [[1.0], [0.8, 0.2]]
    assert module().constrain_types(['a', 'b'], original, {'a': 'A', 'b': 'A'}) == original


def test_missing_type_fails_without_default():
    with pytest.raises(ValueError, match='coverage'):
        module().constrain_types(['a', 'b'], [[1], [0.8, 0.2]], {'a': 'A'})


def test_partial_antecedent_rows_fail():
    with pytest.raises(ValueError, match='shape'):
        module().constrain_types(['a', 'b'], [[1], [0.8]], {'a': 'A', 'b': 'B'})


def test_real_official_decoder_keeps_replacement_antecedent_on_cpu():
    import json

    torch = pytest.importorskip('torch')
    config = json.loads((ROOT / 'configs/c5_typed_control_20261013.json').read_text())
    utility = Path(config['utility'])
    if not utility.exists():
        pytest.skip('frozen official utility remains on gpu-4090')
    decoder = module().load_decoder(utility)
    original = [[1.0], [0.8, 0.2], [0.4, 0.35, 0.25]]
    constrained = module().constrain_types(['a', 'b', 'c'], original,
                                          {'a': 'A', 'b': 'B', 'c': 'B'})
    assert module().decode_rows(original, ['a', 'b', 'c'], decoder, torch) == [['a', 'b', 'c']]
    assert module().decode_rows(constrained, ['a', 'b', 'c'], decoder, torch) == [['b', 'c']]
