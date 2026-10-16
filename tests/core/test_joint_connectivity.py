"""Production forest supervision must preserve sealed research behavior and replay."""
import importlib
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest


def component():
    path = Path(__file__).resolve().parents[2] / 'src/ekg/core/joint_connectivity.py'
    assert path.exists(), 'production joint-connectivity component missing'
    return importlib.import_module('ekg.core.joint_connectivity')


def test_registry_import_and_cpu_replay_do_not_require_torch():
    module = component()
    assert 'forest_pair' in module.connectivity_objectives
    result = subprocess.run([sys.executable, '-c',
        'import sys; from ekg.core.joint_connectivity import connectivity_objectives; '
        'assert "forest_pair" in connectivity_objectives; assert "torch" not in sys.modules'],
        env={**os.environ, 'PYTHONPATH': 'src'}, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    replay = module.decode_cached_parents(['a', 'b', 'c', 'd'],
        [[1.], [.5, .5], [0., 0., 1.], [.1, .8, 0., .1]], ['A', 'A', 'B', 'A'])
    assert replay == [['a', 'b', 'd']]


@pytest.mark.parametrize('rows,types', [
    ([[1.], [.5, .5]], ['A', 'B']),
    ([[1.], [float('nan'), 0.]], ['A', 'A']),
    ([[1.], [.2]], ['A', 'A']),
    ([[1.], [.2, .3]], ['A', 'A']),
])
def test_cpu_replay_rejects_corrupt_or_cross_type_cache(rows, types):
    with pytest.raises(ValueError):
        component().decode_cached_parents(['a', 'b'], rows, types)


@pytest.mark.parametrize('arm', ['marginal', 'root', 'exact', 'mass', 'shuffle'])
def test_production_value_and_all_logit_gradients_match_sealed_research(arm):
    module = component()
    torch = pytest.importorskip('torch')
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
    core = importlib.import_module('profile_c5_structure_budget')
    canonical = importlib.import_module('run_first_dummy_control')
    logits = [torch.tensor(row, dtype=torch.float64, requires_grad=True)
              for row in ([], [1.], [0., 0.], [0., 1., 0.], [0., 0., 1., 0.])]
    types, clusters, mentions = ['A', 'A', 'B', 'A', 'B'], [[0, 3], [1], [2, 4]], list('abcde')
    objective = module.connectivity_objectives.create('forest_pair', arm=arm)
    actual = objective(logits, clusters, types, 'doc', mentions)
    rows = canonical.typed_probabilities(logits, types, torch)
    expected = {'marginal': canonical.marginal_loss(rows, clusters, corrected=True, torch=torch),
                'auxiliary': core.auxiliary_loss(rows, clusters, types, 'doc', mentions,
                                                  arm, torch)}
    for name in expected:
        assert torch.equal(actual[name], expected[name])
    a = torch.autograd.grad(sum(actual.values()), logits[1:], retain_graph=True)
    b = torch.autograd.grad(sum(expected.values()), logits[1:])
    assert all(torch.equal(x, y) for x, y in zip(a, b, strict=True))
    cached = [p.detach().tolist() for p in module.typed_parent_rows(logits, types)]
    assert module.decode_cached_parents(mentions, cached, types) == [['a', 'b', 'd'], ['c', 'e']]


def test_singleton_empty_pairs_and_type_conflict_fail_fast():
    module = component()
    torch = pytest.importorskip('torch')
    objective = module.connectivity_objectives.create('forest_pair', arm='exact')
    value = objective([torch.empty(0)], [[0]], ['A'], 'doc', ['a'])
    assert float(value['auxiliary']) == 0.
    assert np.isfinite(float(value['marginal']))
    with pytest.raises(ValueError, match='type'):
        objective([torch.empty(0), torch.zeros(1)], [[0, 1]], ['A', 'B'], 'doc', ['a', 'b'])
    with pytest.raises(ValueError):
        module.connectivity_objectives.create('forest_pair', arm='unknown')
