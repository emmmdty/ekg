"""Torch tests for registered event-relation training objectives."""

from __future__ import annotations

import pytest


def test_cross_entropy_registry_is_exactly_the_historical_objective() -> None:
    torch = pytest.importorskip("torch")
    import torch.nn.functional as F

    from ekg.relations.objective_registry import build_relation_objective

    logits = torch.tensor([[0.1, 0.8, -0.2], [0.5, -0.1, 0.2]], requires_grad=True)
    target = torch.tensor([1, 0])
    weight = torch.tensor([0.5, 2.0, 1.0])
    expected = F.cross_entropy(logits, target, weight=weight, ignore_index=-100)
    actual = build_relation_objective("cross_entropy")(
        logits, target, weight=weight, ignore_index=-100
    )
    assert torch.equal(actual, expected)


def test_adaptive_threshold_matches_atlop_official_formula_and_ignores_rows() -> None:
    torch = pytest.importorskip("torch")
    import torch.nn.functional as F

    from ekg.relations.objective_registry import build_relation_objective

    logits = torch.tensor(
        [[0.2, 1.1, -0.4], [1.2, 0.1, -0.3], [9.0, -9.0, -9.0]],
        requires_grad=True,
    )
    target = torch.tensor([1, 0, -100])
    actual = build_relation_objective("adaptive_threshold")(
        logits, target, weight=None, ignore_index=-100
    )

    valid_logits = logits[:2]
    labels = F.one_hot(target[:2], num_classes=3).float()
    threshold = torch.zeros_like(labels)
    threshold[:, 0] = 1.0
    labels[:, 0] = 0.0
    positive_mask = labels + threshold
    negative_mask = 1.0 - labels
    positive_logits = valid_logits - (1.0 - positive_mask) * 1e30
    negative_logits = valid_logits - (1.0 - negative_mask) * 1e30
    expected = (
        -(F.log_softmax(positive_logits, -1) * labels).sum(-1)
        - F.log_softmax(negative_logits, -1)[:, 0]
    ).mean()
    assert torch.allclose(actual, expected)

    actual.backward()
    assert torch.isfinite(logits.grad).all()
    assert torch.count_nonzero(logits.grad[2]) == 0


def test_adaptive_threshold_rewards_the_required_positive_none_ranking() -> None:
    torch = pytest.importorskip("torch")

    from ekg.relations.objective_registry import build_relation_objective

    objective = build_relation_objective("adaptive_threshold")
    positive = torch.tensor([1])
    negative = torch.tensor([0])

    good_positive = objective(
        torch.tensor([[0.0, 3.0, -2.0]]), positive, weight=None, ignore_index=-100
    )
    reversed_positive = objective(
        torch.tensor([[3.0, 0.0, -2.0]]), positive, weight=None, ignore_index=-100
    )
    good_negative = objective(
        torch.tensor([[3.0, 0.0, -2.0]]), negative, weight=None, ignore_index=-100
    )
    reversed_negative = objective(
        torch.tensor([[0.0, 3.0, -2.0]]), negative, weight=None, ignore_index=-100
    )

    assert good_positive < reversed_positive
    assert good_negative < reversed_negative


def test_adaptive_threshold_rejects_external_weights_and_empty_family() -> None:
    torch = pytest.importorskip("torch")

    from ekg.relations.objective_registry import build_relation_objective

    objective = build_relation_objective("adaptive_threshold")
    logits = torch.zeros(2, 3)
    target = torch.tensor([0, 1])
    with pytest.raises(ValueError, match="external class weights"):
        objective(logits, target, weight=torch.ones(3), ignore_index=-100)
    with pytest.raises(ValueError, match="no scoreable rows"):
        objective(logits, torch.full((2,), -100), weight=None, ignore_index=-100)
