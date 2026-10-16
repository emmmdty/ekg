"""Check actual gradient accumulation, optimizer cadence and fail-fast costs."""
import importlib.util
from pathlib import Path

import pytest


def script():
    path = Path(__file__).resolve().parents[2] / 'scripts/profile_c5_accumulation_budget.py'
    assert path.exists(), 'accumulation budget entrypoint missing'
    spec = importlib.util.spec_from_file_location('c5_accumulation_budget', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_accumulation_matches_mean_gradient_with_real_optimizer_state():
    module = script()
    torch = pytest.importorskip('torch')
    parameter = torch.nn.Parameter(torch.tensor([2.]))
    optimizer = torch.optim.Adam([parameter], lr=0.)
    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lambda _: 1.)
    seen = []

    def loss(index):
        seen.append(None if parameter.grad is None else parameter.grad.item())
        return (parameter * (index + 1)).square().sum()

    result = module.accumulate_cycle(loss, [optimizer], scheduler, torch, 'cpu')
    # Mean of four squared losses has d/dp = 2*2*mean(1,4,9,16)=30.
    assert optimizer.state[parameter]['exp_avg'].item() == pytest.approx(3.)
    assert seen == [None, 1., 5., 14.]
    assert parameter.item() == 2. and parameter.grad is None
    assert float(optimizer.state[parameter]['step']) == scheduler.last_epoch == 1
    assert len(result['microbatches']) == 4
    assert result['loss'] == pytest.approx(30.)
    assert all(r['gradient_bytes'] == 4 for r in result['microbatches'])


def test_nonfinite_loss_fails_before_optimizer_step():
    module = script()
    torch = pytest.importorskip('torch')
    parameter = torch.nn.Parameter(torch.tensor([2.]))
    optimizer = torch.optim.Adam([parameter], lr=0.)
    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lambda _: 1.)
    with pytest.raises(ValueError, match='nonfinite'):
        module.accumulate_cycle(lambda _: parameter.sum() * float('nan'),
                                [optimizer], scheduler, torch, 'cpu')
    assert not optimizer.state and scheduler.last_epoch == 0


def test_probe_rejects_nonzero_lr_and_dirty_gradients():
    module = script()
    torch = pytest.importorskip('torch')
    parameter = torch.nn.Parameter(torch.tensor([2.]))
    optimizer = torch.optim.Adam([parameter], lr=.1)
    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lambda _: 1.)
    with pytest.raises(ValueError, match='zero'):
        module.accumulate_cycle(lambda _: parameter.square().sum(),
                                [optimizer], scheduler, torch, 'cpu')
    optimizer.param_groups[0]['lr'] = 0.
    parameter.grad = torch.ones_like(parameter)
    with pytest.raises(ValueError, match='gradient'):
        module.accumulate_cycle(lambda _: parameter.square().sum(),
                                [optimizer], scheduler, torch, 'cpu')
