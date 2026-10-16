"""Mass matching remains defined when independent-root products round to one."""
import importlib
import itertools
import math
import subprocess
import sys

import pytest


def component():
    return importlib.import_module('ekg.core.mass_connectivity')


def test_mass_component_import_is_lazy():
    result = subprocess.run([sys.executable, '-c',
        'import sys; import ekg.core.mass_connectivity; assert "torch" not in sys.modules'],
        capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_disagreement_probabilities_match_independent_forest_enumeration():
    module = component()
    torch = pytest.importorskip('torch')
    rows = [torch.tensor(row, dtype=torch.float64) for row in
            ([1.], [.4, .6], [.2, .3, .5], [.1, .2, .3, .4])]
    exact, root = module.disagreement_matrices(rows)
    expected = torch.zeros((4, 4), dtype=torch.float64)
    marginals = torch.zeros_like(expected)
    for parents in itertools.product(*(range(j + 1) for j in range(4))):
        weight = math.prod(float(rows[j][p]) for j, p in enumerate(parents))
        roots = []
        for j, p in enumerate(parents):
            roots.append(j if p == j else roots[p])
        for i in range(4):
            marginals[i, roots[i]] += weight
            for j in range(4):
                expected[i, j] += weight * (roots[i] != roots[j])
    independent = torch.tensor([[sum(float(marginals[i, a] * marginals[j, b])
        for a in range(4) for b in range(4) if a != b) for j in range(4)] for i in range(4)],
        dtype=torch.float64)
    torch.testing.assert_close(exact, expected, rtol=0, atol=2e-16)
    torch.testing.assert_close(root, independent, rtol=0, atol=2e-16)


@pytest.mark.parametrize('scale', [0., 12., 30., 60., 100., 300., 1000.])
def test_saturated_mass_has_finite_loss_and_gradients(scale):
    module = component()
    torch = pytest.importorskip('torch')
    logits = [torch.empty(0)] + [torch.full((j,), scale, requires_grad=True)
                                for j in range(1, 6)]
    loss = module.ForestMassComplementObjective()(logits, [[0, 2, 4], [1, 3, 5]],
        ['A'] * 6, 'saturated', list('abcdef'))
    gradients = torch.autograd.grad(sum(loss.values()), logits[1:])
    assert 0 <= float(loss['auxiliary'].detach()) <= 1
    assert all(bool(g.isfinite().all()) for g in gradients)


def test_original_saturation_counterexample_is_finite_without_defaulting_to_root():
    module = component()
    torch = pytest.importorskip('torch')
    from ekg.core.joint_connectivity import ForestPairObjective

    values = [[], [23.76926040649414], [22.151933670043945, 26.776874542236328],
              [8.750518798828125, -3.6504006385803223, 19.773067474365234],
              [17.37267303466797, 10.379216194152832, 26.682018280029297, 30.578304290771484]]
    logits = [torch.tensor(v, requires_grad=True) for v in values]
    args = (logits, [list(range(5))], ['A'] * 5, 'counterexample', list('abcde'))
    with pytest.raises(ValueError, match='zero mass denominator'):
        ForestPairObjective(arm='mass')(*args)
    actual = module.ForestMassComplementObjective()(*args)
    assert actual['auxiliary'].item() > 0
    assert all(bool(g.isfinite().all()) for g in
               torch.autograd.grad(sum(actual.values()), logits[1:]))


def test_typed_objective_preserves_marginal_and_mass_value_and_gradient():
    module = component()
    torch = pytest.importorskip('torch')
    from ekg.core.joint_connectivity import ForestPairObjective

    logits = [torch.tensor(v, dtype=torch.float64, requires_grad=True)
              for v in ([], [1.], [0., 0.], [0., 1., 0.], [0., 0., 1., 0.])]
    args = (logits, [[0, 3], [1], [2, 4]], ['A', 'A', 'B', 'A', 'B'], 'd', list('abcde'))
    actual = module.ForestMassComplementObjective()(*args)
    expected = ForestPairObjective(arm='mass')(*args)
    assert torch.equal(actual['marginal'], expected['marginal'])
    torch.testing.assert_close(actual['auxiliary'], expected['auxiliary'], rtol=0, atol=1e-15)
    a = torch.autograd.grad(sum(actual.values()), logits[1:], retain_graph=True)
    b = torch.autograd.grad(sum(expected.values()), logits[1:])
    for x, y in zip(a, b, strict=True):
        torch.testing.assert_close(x, y, rtol=1e-12, atol=1e-14)
