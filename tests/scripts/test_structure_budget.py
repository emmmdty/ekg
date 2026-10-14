"""Cost probes must allocate real optimizer state without training model weights."""
import importlib.util
from pathlib import Path

import pytest


def script():
    path = Path(__file__).resolve().parents[2] / 'scripts/profile_c5_structure_budget.py'
    assert path.exists(), 'fixed structure/optimizer cost entrypoint missing'
    spec = importlib.util.spec_from_file_location('structure_budget', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('change', [
    {'seed': 42}, {'probe_lr': 1e-8}, {'method_admitted': True},
    {'final_valid_accessed': True}, {'checkpointing': False},
])
def test_probe_rejects_actual_training_or_scope_drift(change):
    config = {'seed': 13, 'probe_lr': 0., 'method_admitted': False,
              'final_valid_accessed': False, 'checkpointing': True}
    with pytest.raises(ValueError):
        script().validate_scope({**config, **change}, 'cpu', '-1', False, '/data/TJK/ekg')


def test_probe_rejects_local_full_model_and_multiple_visible_cards():
    config = {'seed': 13, 'probe_lr': 0., 'method_admitted': False,
              'final_valid_accessed': False, 'checkpointing': True}
    module = script()
    with pytest.raises(ValueError):
        module.validate_scope(config, 'cpu', '-1', False, '/tmp')
    with pytest.raises(ValueError):
        module.validate_scope(config, 'cuda', '0,1', True, '/data/TJK/ekg')


def test_optimizer_probe_real_moments_but_no_parameter_update():
    torch = pytest.importorskip('torch')
    module = script()
    encoder, head = torch.nn.Linear(2, 2), torch.nn.Linear(2, 1)
    before = [p.detach().clone() for p in [*encoder.parameters(), *head.parameters()]]
    optimizers = module.probe_optimizers(encoder.parameters(), head.parameters(), torch)
    for _ in range(2):
        head(encoder(torch.ones(1, 2))).square().sum().backward()
        for optimizer in optimizers:
            optimizer.step()
            optimizer.zero_grad(set_to_none=True)
    for p, expected in zip([*encoder.parameters(), *head.parameters()], before, strict=True):
        assert torch.equal(p, expected)
    states = [state for opt in optimizers for state in opt.state.values()]
    assert len(states) == 4 and all(float(s['step']) == 2 for s in states)
    assert sum(float(s['exp_avg'].abs().sum()) for s in states) > 0
    moment_bytes = sum(p.numel() * 8 for p in [*encoder.parameters(), *head.parameters()])
    assert module.optimizer_state_bytes(optimizers) > moment_bytes
    optimizers[0].param_groups[0]['lr'] = 1e-3
    with pytest.raises(ValueError):
        module.require_zero_lr(optimizers)


def test_auxiliary_aggregates_document_pairs_and_preserves_empty_case():
    torch = pytest.importorskip('torch')
    module = script()
    # Two independent same-type pairs: positive p=.6 and negative p=.2.
    rows = [torch.tensor([1.]), torch.tensor([.6, .4], requires_grad=True),
            torch.tensor([0., 0., 1.]), torch.tensor([0., 0., .2, .8], requires_grad=True)]
    c = module.auxiliary_loss(rows, [[0, 1], [2], [3]], ['A', 'A', 'B', 'B'],
                              'doc', list('abcd'), 'exact', torch)
    # Document aggregation: 1-(2*.6+1)/(.6+.2+1+1)=3/14; not a mean of type losses.
    assert c.item() == pytest.approx(3 / 14, abs=1e-7)
    c.backward()
    assert rows[1].grad is not None and rows[3].grad is not None
    empty = module.auxiliary_loss([torch.tensor([1.])], [[0]], ['A'],
                                  'doc', ['a'], 'exact', torch)
    assert empty.item() == 0
