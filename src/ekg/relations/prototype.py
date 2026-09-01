"""Prototype-matching pair heads inspired by ProtoEM.

This is a transparent local adaptation, not an official ProtoEM reproduction.
It reuses the frozen candidate population and the existing document encoder,
changes only the scoring geometry, and optionally propagates information across
relation prototypes using label co-occurrence measured on the training split.
"""

from __future__ import annotations

import random
from collections.abc import Mapping, Sequence

import numpy as np

from ekg.relations.pair_heads import (
    PROTOTYPE_DEPENDENCY_HEAD,
    PROTOTYPE_HEAD,
    pair_head_factories,
)
from ekg.relations.pairs import PairExample

__all__ = [
    "PROTOTYPE_SUPPORT_PER_CLASS",
    "prototype_dependency_matrix",
    "select_prototype_support",
]

PROTOTYPE_SUPPORT_PER_CLASS = 32


def _label_layout(
    family_subtypes: Mapping[str, Sequence[str]], families: Sequence[str]
) -> tuple[list[tuple[str, str]], dict[tuple[str, str], int]]:
    labels = [
        (family, subtype)
        for family in families
        for subtype in family_subtypes[family]
    ]
    return labels, {label: index for index, label in enumerate(labels)}


def select_prototype_support(
    rows: Sequence[PairExample],
    family_subtypes: Mapping[str, Sequence[str]],
    families: Sequence[str],
    *,
    per_class: int = PROTOTYPE_SUPPORT_PER_CLASS,
    seed: int = 13,
) -> dict[tuple[str, str, str], list[tuple[str, int]]]:
    """Select a deterministic, train-only support set for every family class."""
    if per_class <= 0:
        raise ValueError("prototype support per class must be positive")
    shuffled = list(rows)
    random.Random(seed).shuffle(shuffled)
    selected: dict[tuple[str, int], list[PairExample]] = {
        (family, index): []
        for family in families
        for index in range(len(family_subtypes[family]))
    }
    label_index = {
        family: {subtype: index for index, subtype in enumerate(family_subtypes[family])}
        for family in families
    }
    for row in shuffled:
        for family in families:
            if family in row.ignored_families:
                continue
            index = label_index[family][row.labels.get(family, "NONE")]
            bucket = selected[(family, index)]
            if len(bucket) < per_class:
                bucket.append(row)
        if all(len(bucket) >= per_class for bucket in selected.values()):
            break
    missing = [key for key, bucket in selected.items() if not bucket]
    if missing:
        raise ValueError(f"no training support examples for prototype classes {missing}")

    assignments: dict[tuple[str, str, str], list[tuple[str, int]]] = {}
    for key, bucket in selected.items():
        for row in bucket:
            row_key = (row.doc_id, row.head_id, row.tail_id)
            assignments.setdefault(row_key, []).append(key)
    return assignments


def prototype_dependency_matrix(
    rows: Sequence[PairExample],
    family_subtypes: Mapping[str, Sequence[str]],
    families: Sequence[str],
) -> np.ndarray:
    """Positive-label co-occurrence, symmetric-normalized with self loops.

    NONE is deliberately self-only.  On the frozen training split, every causal
    positive co-occurs with subevent NONE, so including negative co-occurrence
    would make that uninformative edge dominate the causal prototype graph and
    bury the measured CAUSE/PRECONDITION -> BEFORE dependency.
    """
    labels, index = _label_layout(family_subtypes, families)
    counts = np.zeros((len(labels), len(labels)), dtype=np.float64)
    for row in rows:
        active = [
            index[(family, row.labels[family])]
            for family in families
            if family not in row.ignored_families and family in row.labels
        ]
        for left in active:
            for right in active:
                if left != right:
                    counts[left, right] += 1.0
    counts = (counts + counts.T) / 2.0
    counts += np.eye(len(labels), dtype=np.float64)
    degree = counts.sum(axis=1)
    if np.any(degree <= 0):
        raise ValueError("prototype dependency graph has an isolated label")
    scale = np.diag(1.0 / np.sqrt(degree))
    return scale @ counts @ scale


try:  # pragma: no cover - exercised on a GPU host
    import torch
    import torch.nn as nn

    from ekg.relations.extractor.supervised import DISTANCE_BUCKETS

    def prototype_logits(
        embeddings: torch.Tensor, prototypes: torch.Tensor
    ) -> torch.Tensor:
        """Negative Euclidean distance: the nearer prototype must score higher."""
        return -torch.cdist(embeddings, prototypes, p=2)


    class PrototypePairClassifier(nn.Module):
        """Shared pair projection followed by per-relation prototype matching."""

        def __init__(
            self,
            hidden_size: int,
            subtype_counts: dict[str, int],
            *,
            dependency: bool,
            mlp_hidden: int = 150,
            dist_dim: int = 32,
        ) -> None:
            super().__init__()
            self.families = tuple(subtype_counts)
            self.subtype_counts = dict(subtype_counts)
            self.distance = nn.Embedding(len(DISTANCE_BUCKETS) + 1, dist_dim)
            nn.init.zeros_(self.distance.weight)
            in_dim = hidden_size * 4 + dist_dim
            self.projector = nn.Sequential(
                nn.Linear(in_dim, mlp_hidden),
                nn.ReLU(),
                nn.Dropout(0.2),
                nn.Linear(mlp_hidden, mlp_hidden),
                nn.ReLU(),
                nn.Dropout(0.2),
            )
            self.prototypes = nn.ParameterDict(
                {
                    family: nn.Parameter(torch.empty(count, mlp_hidden))
                    for family, count in subtype_counts.items()
                }
            )
            for value in self.prototypes.values():
                nn.init.xavier_uniform_(value)

            total = sum(subtype_counts.values())
            self.dependency = dependency
            self.register_buffer("dependency_matrix", torch.eye(total))
            if dependency:
                self.neighbor = nn.Linear(mlp_hidden, mlp_hidden, bias=False)
                nn.init.zeros_(self.neighbor.weight)

        def project(
            self, pair_feats: torch.Tensor, dist_ids: torch.Tensor
        ) -> torch.Tensor:
            features = torch.cat([pair_feats, self.distance(dist_ids)], dim=-1)
            return self.projector(features)

        def set_dependency(self, matrix: np.ndarray) -> None:
            expected = self.dependency_matrix.shape
            if matrix.shape != expected:
                raise ValueError(
                    f"dependency matrix {matrix.shape} does not match {tuple(expected)}"
                )
            self.dependency_matrix.copy_(
                torch.as_tensor(
                    matrix,
                    dtype=self.dependency_matrix.dtype,
                    device=self.dependency_matrix.device,
                )
            )

        def set_prototypes(self, values: Mapping[str, torch.Tensor]) -> None:
            if set(values) != set(self.families):
                raise ValueError("prototype initializers do not match relation families")
            with torch.no_grad():
                for family in self.families:
                    expected = self.prototypes[family].shape
                    if values[family].shape != expected:
                        raise ValueError(
                            f"{family} prototype initializer {values[family].shape} "
                            f"does not match {tuple(expected)}"
                        )
                    self.prototypes[family].copy_(values[family])

        def _prototype_matrix(self) -> torch.Tensor:
            base = torch.cat([self.prototypes[family] for family in self.families])
            if not self.dependency:
                return base
            return base + self.neighbor(self.dependency_matrix @ base)

        def forward(
            self, pair_feats: torch.Tensor, dist_ids: torch.Tensor
        ) -> dict[str, torch.Tensor]:
            instances = self.project(pair_feats, dist_ids)
            prototype_matrix = self._prototype_matrix()
            output: dict[str, torch.Tensor] = {}
            start = 0
            for family in self.families:
                end = start + self.subtype_counts[family]
                output[family] = prototype_logits(
                    instances, prototype_matrix[start:end]
                )
                start = end
            return output


    @pair_head_factories.register(PROTOTYPE_HEAD)
    def _build_prototype_head(
        hidden_size: int, subtype_counts: dict[str, int]
    ) -> PrototypePairClassifier:
        return PrototypePairClassifier(
            hidden_size, subtype_counts, dependency=False
        )


    @pair_head_factories.register(PROTOTYPE_DEPENDENCY_HEAD)
    def _build_prototype_dependency_head(
        hidden_size: int, subtype_counts: dict[str, int]
    ) -> PrototypePairClassifier:
        return PrototypePairClassifier(
            hidden_size, subtype_counts, dependency=True
        )

except ImportError:  # pragma: no cover - local CPU environment intentionally lacks torch
    pass
