import importlib.util
from pathlib import Path

import numpy as np
import pytest


def module():
    path = Path('scripts/replay_forest_coref_control.py')
    spec = importlib.util.spec_from_file_location('forest_control_test', path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def test_joint_keeps_shared_ancestry():
    joint, product, _ = module().posterior_scores([[1], [.5, .5], [0, .5, .5]], ['x'] * 3)
    assert joint[1, 2] == .5
    assert product[1, 2] == .25
    assert np.array_equal(joint.diagonal(), np.ones(3))


def test_hard_forest_product_matches_joint():
    joint, product, _ = module().posterior_scores([[1], [1, 0], [0, 1, 0]], ['x'] * 3)
    assert np.array_equal(joint, product)


def test_type_mask_renormalizes_with_original_dummy():
    rows = module().typed_probabilities([[], [1000], [0, 1000]], ['x', 'y', 'x'])
    assert rows == [[1], [0, 1], [.5, 0, .5]]


@pytest.mark.parametrize('rows,kinds', [([[1], [.5]], ['x', 'x']),
                                       ([[1], [1, 1]], ['x', 'x']),
                                       ([[1], [-.1, 1.1]], ['x', 'x']),
                                       ([[1]], [])])
def test_invalid_distribution_fails(rows, kinds):
    with pytest.raises(ValueError):
        module().posterior_scores(rows, kinds)


def test_shuffle_preserves_direct_parent_term_and_types():
    p = [[1], [.5, .5], [.5, 0, .5], [0, .2, .4, .4]]
    joint, _, shuffled = module().posterior_scores(p, ['x'] * 4)
    assert np.all(shuffled[np.tril_indices(4, -1)] >= np.array(
        [p[i][j] for i in range(4) for j in range(i)]))
    assert np.array_equal(shuffled, module().posterior_scores(p, ['x'] * 4)[2])
    assert not np.array_equal(shuffled, joint)


def test_official_decoder_keeps_dummy_not_connectivity_diagonal():
    torch = pytest.importorskip('torch')
    spec = importlib.util.spec_from_file_location(
        'typed_decoder_test', Path('scripts/replay_typed_coref_control.py'))
    utility = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(utility)

    def decoder(matrix):
        assert torch.allclose(matrix.diagonal(), torch.tensor([1., .6, .6]))
        return [[0], [1], [2]], None

    m = module()
    p = [[1], [.4, .6], [0, .4, .6]]
    joint, _, _ = m.posterior_scores(p, ['x'] * 3)
    scores = m.decoder_rows(joint, p, ['x'] * 3)
    assert utility.decode_rows(scores, ['a', 'b', 'c'], decoder, torch) == []
