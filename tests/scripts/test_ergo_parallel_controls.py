"""Parallel known controls must change only the declared component."""
import ast
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


def module(monkeypatch):
    monkeypatch.syspath_prepend(str(Path('scripts').resolve()))
    spec = importlib.util.spec_from_file_location('ergo_parallel',
                                                Path('scripts/run_ergo_native_control.py'))
    out = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(out)
    return out


def test_ast_installs_once_after_model_creation_and_preserves_other_statements(monkeypatch):
    m = module(monkeypatch)
    original = 'def main():\n    model = external.LongformerCausalModel(13)\n    return model\n'
    derived = m.controlled_source(original)
    tree = ast.parse(derived)
    body = tree.body[0].body
    assert body[1].value.func.id == '_install_control'
    del body[1]
    assert ast.dump(tree) == ast.dump(ast.parse(original))
    calls = []
    namespace = {'external': SimpleNamespace(LongformerCausalModel=lambda v: {'seed': v}),
                 '_install_control': lambda model: calls.append(model)}
    exec(derived, namespace)
    assert namespace['main']() == {'seed': 13}
    assert calls == [{'seed': 13}]
    with pytest.raises(ValueError, match='exactly one'):
        m.controlled_source('model = unrelated()')
    with pytest.raises(ValueError, match='exactly one'):
        m.controlled_source(original + '\n' + original.replace('main', 'other'))


def test_gamma0_preserves_alpha_and_rejects_unknown_control(monkeypatch):
    m = module(monkeypatch)
    loss = SimpleNamespace(gamma=2, alpha=SimpleNamespace(tolist=lambda: [.25, .75, .75]))
    model = SimpleNamespace(focal_loss=loss, loss_type='focal')
    m.install_control(model, 'gamma0')
    assert loss.gamma == 0
    assert loss.alpha.tolist() == [.25, .75, .75]
    with pytest.raises(ValueError, match='unknown control'):
        m.install_control(model, 'try_more')


def test_complete_graph_keeps_weights_dropout_rng_and_masks_diagonal(monkeypatch):
    torch = pytest.importorskip('torch')
    m = module(monkeypatch)

    class Layer(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.weight = torch.nn.Parameter(torch.randn(3, 3))
            self.dropout = torch.nn.Dropout(.2)

        def forward(self, pairs, mask):
            return self.dropout(pairs @ self.weight), mask

    layer = Layer()
    model = SimpleNamespace(RGT_layer=layer, loss_type='focal', focal_loss=SimpleNamespace(
        gamma=2, alpha=torch.tensor([.25, .75, .75])))
    before = {k: v.clone() for k, v in layer.state_dict().items()}
    pairs = torch.ones(1, 4, 3)
    old_mask = torch.ones(1, 4, 4, dtype=torch.bool)
    old_mask[:, 0, 1] = False
    torch.manual_seed(13)
    original_values, _ = layer(pairs, old_mask)
    info = m.install_control(model, 'complete_graph')
    torch.manual_seed(13)
    values, mask = layer(pairs, old_mask)
    assert torch.equal(values, original_values)
    assert torch.equal(mask[0], torch.eye(4, dtype=torch.bool))
    assert old_mask.sum() == 15
    assert info['mask_calls'] == 1
    assert all(torch.equal(v, before[k]) for k, v in layer.state_dict().items())


def test_training_rejects_missing_control_cuda_evidence_before_reading_inputs(monkeypatch):
    m = module(monkeypatch)
    with pytest.raises(ValueError, match='control CUDA preflight'):
        m.require_control_evidence({'control_name': 'gamma0', 'pins': {}})
