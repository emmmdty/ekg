"""A balanced derivative on base logits need not protect the shared encoder."""

import importlib.util
from pathlib import Path

import pytest

from ekg.nodes.encoding import TORCH_AVAILABLE

spec = importlib.util.spec_from_file_location(
    "audit_auxiliary_gradients", Path(__file__).resolve().parents[2]
    / "scripts/audit_auxiliary_gradients.py",
)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="needs torch")
def test_opposite_gradients_report_main_task_ascent_without_mutating_gradients():
    import torch

    parameter = torch.tensor([1.0], requires_grad=True)
    report = module.gradient_report(-parameter.sum(), 3 * parameter.sum(), [parameter])
    assert report["cosine"] == pytest.approx(-1.0)
    assert report["primary_dot_combined"] == pytest.approx(-2.0)
    assert parameter.grad is None


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="needs torch")
def test_zero_gradient_is_not_reported_as_alignment():
    import torch

    parameter = torch.tensor([1.0], requires_grad=True)
    report = module.gradient_report(parameter.sum(), 0 * parameter.sum(), [parameter])
    assert report["cosine"] is None
    assert report["auxiliary_norm"] == 0


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="needs torch")
def test_real_consistency_loss_can_cancel_base_derivative_and_conflict_on_shared_parameters():
    report = module.a4_fixture()
    assert report["base_logit_gradient"] == pytest.approx(0.0)
    assert report["alignment"]["auxiliary_norm"] == pytest.approx(1.0)
    assert report["alignment"]["cosine"] == pytest.approx(-1.0)
    assert report["alignment"]["primary_dot_combined"] < 0
