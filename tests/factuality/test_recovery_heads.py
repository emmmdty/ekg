"""Changing only a factuality head must survive checkpoint round-trip."""

import pytest

from ekg.nodes.encoding import TORCH_AVAILABLE


def test_unknown_head_rejected_before_loading_torch():
    from ekg.factuality.recovery_heads import validate_head

    with pytest.raises(ValueError, match="unknown"):
        validate_head("guess")


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="needs torch")
def test_linear_control_keeps_legacy_state_and_bottleneck_round_trips():
    import torch
    from torch import nn

    from ekg.factuality.recovery_heads import build_head

    torch.manual_seed(13)
    legacy = nn.Linear(8, 5)
    torch.manual_seed(13)
    control = build_head("linear", 8, 5)
    assert torch.equal(legacy.weight, control.weight)
    features = torch.randn(3, 8, requires_grad=True)
    head = build_head("tanh5", 8, 5)
    restored = build_head("tanh5", 8, 5)
    restored.load_state_dict(head.state_dict())
    assert torch.equal(head(features), restored(features))
    head(features).sum().backward()
    assert features.grad is not None and torch.isfinite(features.grad).all()

