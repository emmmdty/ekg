"""Zero-LR instrumentation may restore signed zero, but must reject numeric updates."""
import importlib.util
from pathlib import Path

import pytest


def script():
    path = Path(__file__).resolve().parents[2] / 'scripts/profile_c5_structure_budget_r2.py'
    assert path.exists(), 'signed-zero integrity cost adapter missing'
    spec = importlib.util.spec_from_file_location('budget_integrity', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_native_zero_lr_step_is_audited_and_only_signed_zero_restored():
    torch = pytest.importorskip('torch')
    module = script()
    p = torch.nn.Parameter(torch.tensor([-0., 0., 1.]))
    optimizer = torch.optim.Adam([p], lr=0.)
    receipts = module.attach_integrity_hooks([optimizer], torch)
    p.grad = torch.tensor([-1., -1., 1.])
    optimizer.step()
    assert torch.signbit(p).tolist() == [True, False, False]
    assert p.tolist() == [0., 0., 1.]
    assert len(receipts) == 1 and receipts[0]['zero_sign_restorations'] == 1
    assert receipts[0]['numeric_parameters_equal'] is True
    assert float(optimizer.state[p]['step']) == 1
    assert receipts[0]['raw_sha256_before'] != receipts[0]['raw_sha256_after_native_step']
    assert receipts[0]['raw_sha256_before'] == receipts[0]['raw_sha256_after_integrity']


def test_any_numeric_update_is_rejected_without_undoing_it():
    torch = pytest.importorskip('torch')
    module = script()
    p = torch.nn.Parameter(torch.tensor([1.]))
    optimizer = torch.optim.Adam([p], lr=0.)
    module.attach_integrity_hooks([optimizer], torch)
    p.data.add_(.25)
    p.grad = torch.ones_like(p)
    with pytest.raises(ValueError, match='numerical parameter update'):
        optimizer.step()
    assert p.item() == 1.25


def test_cost_hook_rejects_learning_rate_change_before_step():
    torch = pytest.importorskip('torch')
    module = script()
    p = torch.nn.Parameter(torch.tensor([1.]))
    optimizer = torch.optim.Adam([p], lr=0.)
    module.attach_integrity_hooks([optimizer], torch)
    optimizer.param_groups[0]['lr'] = 1e-3
    p.grad = torch.ones_like(p)
    with pytest.raises(ValueError, match='must not train weights'):
        optimizer.step()
    assert p.item() == 1
