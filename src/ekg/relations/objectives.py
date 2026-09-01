"""Loss functions for supervised event-relation extraction.

``AdaptiveThresholdObjective`` is a direct adaptation of ATLOP's official
``ATLoss`` (Zhou et al., AAAI 2021).  In this project every relation family is
single-label, so its NONE class at index 0 is exactly ATLOP's threshold class:
positive rows rank their gold subtype above NONE and NONE above every other
subtype; negative rows rank NONE above every positive subtype.
"""

from __future__ import annotations

import torch
import torch.nn.functional as F

from ekg.relations.objective_registry import (
    ADAPTIVE_THRESHOLD_OBJECTIVE,
    CROSS_ENTROPY_OBJECTIVE,
    relation_objective_factories,
)

__all__ = ["AdaptiveThresholdObjective", "CrossEntropyObjective"]


@relation_objective_factories.register(CROSS_ENTROPY_OBJECTIVE)
class CrossEntropyObjective:
    """The historical weighted cross-entropy objective, unchanged."""

    def __call__(
        self,
        logits: torch.Tensor,
        target: torch.Tensor,
        *,
        weight: torch.Tensor | None,
        ignore_index: int,
    ) -> torch.Tensor:
        return F.cross_entropy(
            logits,
            target,
            weight=weight,
            ignore_index=ignore_index,
        )


@relation_objective_factories.register(ADAPTIVE_THRESHOLD_OBJECTIVE)
class AdaptiveThresholdObjective:
    """ATLOP adaptive-threshold loss with NONE fixed at class index 0."""

    def __call__(
        self,
        logits: torch.Tensor,
        target: torch.Tensor,
        *,
        weight: torch.Tensor | None,
        ignore_index: int,
    ) -> torch.Tensor:
        if weight is not None:
            raise ValueError("adaptive_threshold does not accept external class weights")
        valid = target != ignore_index
        if not torch.any(valid):
            raise ValueError("adaptive_threshold received no scoreable rows")
        logits = logits[valid]
        target = target[valid]
        labels = F.one_hot(target, num_classes=logits.shape[-1]).to(logits.dtype)

        threshold = torch.zeros_like(labels)
        threshold[:, 0] = 1.0
        labels[:, 0] = 0.0

        positive_mask = (labels + threshold).bool()
        negative_mask = (1.0 - labels).bool()
        floor = torch.finfo(logits.dtype).min

        positive_logits = logits.masked_fill(~positive_mask, floor)
        positive_loss = -(F.log_softmax(positive_logits, dim=-1) * labels).sum(dim=-1)

        negative_logits = logits.masked_fill(~negative_mask, floor)
        negative_loss = -F.log_softmax(negative_logits, dim=-1)[:, 0]
        return (positive_loss + negative_loss).mean()
