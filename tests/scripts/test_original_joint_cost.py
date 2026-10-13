"""The cost probe must preserve gradients and refuse unsafe execution."""
import importlib.util
from pathlib import Path

import pytest


def script():
    path = Path(__file__).resolve().parents[2] / 'scripts/profile_original_joint_cost.py'
    assert path.exists(), 'original joint cost profiler missing'
    spec = importlib.util.spec_from_file_location('joint_cost', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('visible,available', [('', False), ('-1', False)])
def test_cpu_requires_cuda_hidden(visible, available):
    script().validate_device('cpu', visible, available, 'gpu-4090')


@pytest.mark.parametrize('device,visible,available,host', [
    ('cpu', '0', True, 'gpu-4090'), ('cpu', None, False, 'gpu-4090'),
    ('cuda', '0,1', True, 'gpu-4090'), ('cuda', '0', True, 'local'),
    ('cuda', '0', False, 'gpu-4090'), ('cuda', '0', True, 'gpu-5090')])
def test_unsafe_device_selection_rejected(device, visible, available, host):
    with pytest.raises(ValueError):
        script().validate_device(device, visible, available, host)


def test_fixture_must_match_census_population_and_chunk_count():
    module = script()
    census = {'fixed_numpy_rng13_batch8_peak_ids': list('abcdefgh'),
              'fixed_numpy_rng13_batch8_peak_chunks': 23}
    assert module.fixture(census, 'peak') == (list('abcdefgh'), 23)
    census['fixed_numpy_rng13_batch8_peak_ids'][0] = 'b'
    with pytest.raises(ValueError):
        module.fixture(census, 'peak')


def test_full_loss_matches_published_clamp_and_weights():
    torch = pytest.importorskip('torch')
    module = script()
    probs = torch.tensor([[1., -1000.], [.2, .8]], requires_grad=True)
    logits = [torch.tensor([[[1., -1.], [-2., 2.]]], requires_grad=True)
              for _ in range(3)]
    batch = {'coref_labels': [[[0, 1]]],
             **{key + '_labels': torch.tensor([[0, -100]])
                for key in ('temporal', 'causal', 'subevent')}}
    def fill(_):
        return torch.tensor([[0., 0.], [1., 0.]])
    loss, parts = module.original_loss(([probs], *logits), batch, fill, torch)
    expected_coref = -(torch.tensor(2e-8).log() + torch.tensor(.2 + 1e-8).log()) / 2
    expected_ce = torch.nn.functional.cross_entropy(logits[0][:, 0], torch.tensor([0]))
    assert loss.item() == pytest.approx((.4 * expected_coref + 10 * expected_ce).item())
    assert set(parts) == {'coreference', 'temporal', 'causal', 'subevent'}
    loss.backward()
    assert probs.grad[0].abs().sum() == 0
    assert all(x.grad.abs().sum() > 0 for x in logits)


def test_nonreentrant_roberta_checkpoint_preserves_dropout_loss_and_all_gradients():
    torch = pytest.importorskip('torch')
    transformers = pytest.importorskip('transformers')
    module = script()
    torch.set_num_threads(2)
    torch.manual_seed(13)
    model = transformers.RobertaModel(transformers.RobertaConfig(
        vocab_size=31, hidden_size=16, num_hidden_layers=2, num_attention_heads=2,
        intermediate_size=24, max_position_embeddings=32))
    model.train()
    ids = torch.tensor([[0, 5, 6, 7, 2]])
    gradients = None
    before = module.parameter_digest(model)
    for enabled in (False, True):
        module.set_checkpointing(model, enabled)
        model.zero_grad(set_to_none=True)
        torch.manual_seed(13)
        loss = model(ids).last_hidden_state[:, 1, 3].sum()
        loss.backward()
        if gradients is None:
            gradients = {n: p.grad.clone() for n, p in model.named_parameters()
                         if p.grad is not None}
            first_loss = loss.item()
        else:
            assert loss.item() == pytest.approx(first_loss, abs=1e-7)
            report = module.compare_gradients(model, gradients, torch)
            assert report['passed'] is True
    assert module.parameter_digest(model) == before


def test_missing_or_changed_gradient_is_not_silently_accepted():
    torch = pytest.importorskip('torch')
    module = script()
    model = torch.nn.Linear(2, 1)
    reference = {'weight': torch.ones_like(model.weight), 'bias': torch.ones_like(model.bias)}
    model.weight.grad = torch.zeros_like(model.weight)
    with pytest.raises(ValueError, match='population'):
        module.compare_gradients(model, reference, torch)
    model.bias.grad = torch.ones_like(model.bias)
    assert module.compare_gradients(model, reference, torch)['passed'] is False
