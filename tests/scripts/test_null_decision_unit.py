import importlib.util

import pytest


def module():
    spec = importlib.util.spec_from_file_location(
        'null_unit', 'scripts/replay_null_decision_unit.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_class_action_differs_from_per_candidate_competition():
    # q=.6 over two equally probable real parents: each=.3 < dummy=.4.
    rows = module().decision_rows(['a', 'b', 'c'], [[], [0], [0, 0]],
                                  [-5, -5, .4054651081], ['x'] * 3)
    assert rows[2] == [1, 0, 0]


def test_real_antecedent_rank_and_type_policy_unchanged():
    rows = module().decision_rows(['a', 'b', 'c', 'd'], [[], [100], [0, 50], [2, 100, 3]],
                                  [10, 10, 10, 10], ['x', 'y', 'x', 'x'])
    assert rows == [[1], [0, 1], [1, 0, 0], [0, 0, 1, 0]]


def test_dummy_for_nonpositive_or_empty_real_set():
    assert module().decision_rows(['a', 'b', 'c'], [[], [50], [50, 50]],
                                  [10, 0, -1], ['x'] * 3) == [[1], [0, 1], [0, 0, 1]]


@pytest.mark.parametrize('logits,z,kinds', [([[], []], [0, 1], ['x', 'x']),
                                          ([[], [0]], [0, float('nan')], ['x', 'x']),
                                          ([[]], [0], [])])
def test_invalid_inputs_fail(logits, z, kinds):
    with pytest.raises(ValueError):
        module().decision_rows(['a', 'b'][:len(z)], logits, z, kinds)


def test_reloaded_scaler_preserves_float32_transform():
    np = pytest.importorskip('numpy')
    from sklearn.preprocessing import StandardScaler
    fit = np.array([[.11, 1000], [.27, 2], [.69, .0003]], dtype=np.float32)
    original = StandardScaler().fit(fit)
    new = module().restore_scaler(original.mean_, original.scale_)
    assert np.array_equal(original.transform(fit), new.transform(fit))


def test_sealed_head_roundtrip(tmp_path):
    torch = pytest.importorskip('torch')
    import numpy as np

    torch.manual_seed(13)
    head = torch.nn.Sequential(torch.nn.Linear(3, 200), torch.nn.ReLU(),
                               torch.nn.Dropout(.2), torch.nn.Linear(200, 1))
    head.eval()
    path = tmp_path / 'head.pt'
    torch.save({'state_dict': head.state_dict(), 'scaler_mean': np.zeros(3),
                'scaler_scale': np.ones(3), 'seed': 13, 'final_epoch': 10}, path)
    new, _ = module().load_head(path, torch)
    x = torch.tensor([[.1, .2, .3]])
    assert torch.equal(head(x), new(x))
