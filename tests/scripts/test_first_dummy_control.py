"""A conventional marginal target must supervise the first of every gold cluster."""
import importlib.util
from pathlib import Path

import pytest


def script():
    path = Path(__file__).resolve().parents[2] / 'scripts/run_first_dummy_control.py'
    assert path.exists(), 'first-dummy control entrypoint missing'
    spec = importlib.util.spec_from_file_location('first_dummy_control', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_only_missing_first_dummy_changes():
    legacy = script().antecedent_targets([[0], [1, 2]], 3, corrected=False)
    corrected = script().antecedent_targets([[0], [1, 2]], 3, corrected=True)
    assert legacy == [[1, 0, 0], [0, 0, 0], [0, 1, 0]]
    assert corrected == [[1, 0, 0], [0, 1, 0], [0, 1, 0]]


def test_gold_order_does_not_change_earlier_antecedents():
    assert script().antecedent_targets([[3, 1, 0], [2]], 4, corrected=True) == [
        [1, 0, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0], [1, 1, 0, 0]]


@pytest.mark.parametrize('clusters', [[[0], [0, 1]], [[0]], [[0, 2]], [[], [0, 1]]])
def test_incomplete_or_duplicate_gold_is_rejected(clusters):
    with pytest.raises(ValueError):
        script().antecedent_targets(clusters, 2, corrected=True)


def test_typed_probability_keeps_dummy_and_excludes_cross_type():
    torch = pytest.importorskip('torch')
    rows = script().typed_probabilities([torch.empty(0), torch.tensor([100.]),
                                        torch.tensor([0., 100.])], ['T', 'U', 'T'], torch)
    assert rows[0].tolist() == [1.]
    assert rows[1].tolist() == [0., 1.]
    assert rows[2].tolist() == pytest.approx([.5, 0., .5])


def test_missing_dummy_gives_zero_gradient_and_correction_penalizes_wrong_link():
    torch = pytest.importorskip('torch')
    theta = torch.zeros(3, dtype=torch.float64, requires_grad=True)
    rows = [theta.new_ones(1), torch.softmax(torch.stack([theta[0], theta[0]*0]), 0),
            torch.softmax(torch.stack([theta[1], theta[2], theta[2]*0]), 0)]
    old = script().marginal_loss(rows, [[0], [1, 2]], corrected=False, torch=torch)
    fixed = script().marginal_loss(rows, [[0], [1, 2]], corrected=True, torch=torch)
    old_grad = torch.autograd.grad(old, theta, retain_graph=True)[0]
    new_grad = torch.autograd.grad(fixed, theta)[0]
    assert old_grad[0] == 0
    assert new_grad[0] == pytest.approx(1/6)
    assert new_grad[1:].tolist() == pytest.approx(old_grad[1:].tolist())


def test_budget_is_fixed_and_is_not_a_method_admission():
    config = {'control_only': True, 'method_admitted': False, 'seed': 13,
              'training': {'epochs': 5, 'lr': .0003, 'batch_size': 8,
                           'arms': ['legacy', 'corrected'], 'encoder_frozen': True}}
    script().validate_settings(config)
    config['training']['epochs'] = 6
    with pytest.raises(ValueError):
        script().validate_settings(config)
