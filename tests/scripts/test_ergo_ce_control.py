"""CE selector must preserve predictions/parameters and keep its own evidence identity."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

PATH = Path('scripts/run_ergo_ce_control.py')


def module(monkeypatch):
    assert PATH.exists(), 'CE control entry is missing'
    monkeypatch.syspath_prepend(str(PATH.resolve().parent))
    spec = importlib.util.spec_from_file_location('ergo_ce_control', PATH)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def toy():
    return SimpleNamespace(loss_type='focal', focal_loss=SimpleNamespace(
        gamma=2, alpha=SimpleNamespace(tolist=lambda: [.25, .75, .75])))


def test_ce_selection_preserves_focal_and_rejects_scope_expansion(monkeypatch):
    m = module(monkeypatch)
    model = toy()
    info = m.install_ce(model, 'unweighted_ce')
    assert model.loss_type == 'ce'
    assert model.focal_loss.gamma == 2
    assert model.focal_loss.alpha.tolist() == [.25, .75, .75]
    assert info['selected_original_loss'] == 'ce_loss'
    with pytest.raises(ValueError):
        m.install_ce(toy(), 'gamma0')
    with pytest.raises(ValueError):
        m.install_ce(model, 'unweighted_ce')


def test_delegated_real_runner_fails_on_missing_or_changed_helper_identity(monkeypatch):
    m = module(monkeypatch)
    with pytest.raises(ValueError):
        m.control_runner({'pins': {}})
    from ekg.core.stage_bundle import sha256_file
    helper = 'scripts/run_ergo_native_control.py'
    cfg = {'pins': {helper: sha256_file(Path(helper))}}
    namespace = m.control_runner(cfg)
    namespace['install_control'](toy(), 'unweighted_ce')
    with pytest.raises(ValueError):
        namespace['install_control'](toy(), 'complete_graph')
    with pytest.raises(ValueError):
        namespace['require_control_evidence']({'control_name': 'unweighted_ce', 'pins': {}})
    cfg['pins'][helper] = '0'*64
    with pytest.raises(ValueError):
        m.control_runner(cfg)


def test_real_original_forward_selects_exact_ce_without_altering_logits(monkeypatch):
    torch = pytest.importorskip('torch')
    import torch.nn.functional as functional

    m = module(monkeypatch)
    source = Path('runs/external/ERGO/afa3d347ec360242c01d15a34b1f1ae63714c789/model.py')
    if not source.exists():
        pytest.skip('official source exists on primary server; not a local full-encoder test')
    spec = importlib.util.spec_from_file_location('official_ergo_ce_test', source)
    external = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(external)

    class TinyEncoder(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.emb = torch.nn.Embedding(8, 768)

        def forward(self, input_ids, **kwargs):
            return (self.emb(input_ids),)

    monkeypatch.setattr(external.LongformerModel, 'from_pretrained',
                        lambda *a, **k: TinyEncoder())
    model = external.LongformerCausalModel(SimpleNamespace(
        device='cpu', model_name_or_path='not-loaded', num_heads=4, dropout_att=.1,
        dropout_emb=.3, y_class=3, class_weight=.75, gamma=2, loss_type='focal'))
    model.eval()
    state = {k: v.clone() for k, v in model.state_dict().items()}
    inputs = dict(enc_input_ids=torch.tensor([[0, 1, 2, 3]]),
                  enc_mask_ids=torch.ones(1, 4, dtype=torch.long),
                  global_attention_mask=torch.ones(1, 4, dtype=torch.long),
                  t1_pos=[[1, 2, 3]], t2_pos=[[2, 3, 1]],
                  mh_self_attention_mask=torch.eye(3, dtype=torch.bool), target=[[0, 1, 2]])
    _, original_logits = model(**inputs)
    m.install_ce(model, 'unweighted_ce')
    loss, logits = model(**inputs)
    assert torch.equal(logits, original_logits)
    assert torch.equal(loss, functional.cross_entropy(logits, torch.tensor([0, 1, 2])))
    assert all(torch.equal(v, state[k]) for k, v in model.state_dict().items())
    loss.backward()
    assert all(torch.isfinite(p.grad).all() for p in model.parameters() if p.grad is not None)
    # gamma0 remains weighted: this is why that sealed arm cannot stand in for CE.
    weighted = external.focal_loss(alpha=.75, gamma=0, num_classes=3)
    z = torch.zeros(1, 3)
    none = weighted(z, torch.tensor([0]))
    positive = weighted(z, torch.tensor([1]))
    assert float(positive/none) == pytest.approx(3.)


def test_real_runner_executes_ce_extension_and_records_its_identity(monkeypatch, tmp_path):
    import json
    import sys

    from ekg.core.stage_bundle import sha256_file

    m = module(monkeypatch)
    entry, output, execution = tmp_path/'entry.py', tmp_path/'out', tmp_path/'execution'
    entry.write_text('''from pathlib import Path
import json
from types import SimpleNamespace
external = SimpleNamespace(LongformerCausalModel=lambda ignored: SimpleNamespace(
    loss_type='focal', focal_loss=SimpleNamespace(
        gamma=2, alpha=SimpleNamespace(tolist=lambda: [.25,.75,.75]))))
def main():
    model = external.LongformerCausalModel(13)
    assert model.loss_type == 'ce'
    output = Path('''+repr(str(output))+''')
    output.mkdir()
    (output/'production_report.json').write_text(json.dumps(
        {'parameter_before': {'numeric_sha256': 'test-initializer'}}))
''')
    initializer = tmp_path/'initializer.json'
    initializer.write_text(json.dumps({'parameter_before': {'numeric_sha256': 'test-initializer'}}))
    helper = 'scripts/run_ergo_native_control.py'
    cfg = {'control_name': 'unweighted_ce', 'server': 'gpu-4090',
           'output': str(output), 'control_execution': str(execution),
           'initializer_reference': str(initializer), 'pins': {}}
    for path in [helper, str(PATH), str(entry), str(initializer)]:
        cfg['pins'][path] = sha256_file(Path(path))
    config = tmp_path/'config.json'
    config.write_text(json.dumps(cfg))
    namespace = m.control_runner(cfg)
    namespace['ENTRIES'] = {'preflight': str(entry)}
    monkeypatch.setattr(sys, 'argv', ['run', '--operation', 'preflight', '--config', str(config)])
    namespace['main']()
    record = json.loads((execution/'execution.json').read_text())
    assert record['status'] == 'complete'
    assert record['installed'][0]['selected_original_loss'] == 'ce_loss'
    assert record['initializer_matches_full'] is True
    assert record['wrapper_sha256'] == sha256_file(PATH)
