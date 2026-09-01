"""Registered training objectives for supervised event-relation extraction."""

from __future__ import annotations

import importlib
from typing import Any

from ekg.core.registry import Registry

__all__ = [
    "ADAPTIVE_THRESHOLD_OBJECTIVE",
    "CROSS_ENTROPY_OBJECTIVE",
    "RELATION_OBJECTIVE_NAMES",
    "build_relation_objective",
    "relation_objective_factories",
]

CROSS_ENTROPY_OBJECTIVE = "cross_entropy"
ADAPTIVE_THRESHOLD_OBJECTIVE = "adaptive_threshold"
RELATION_OBJECTIVE_NAMES = (
    CROSS_ENTROPY_OBJECTIVE,
    ADAPTIVE_THRESHOLD_OBJECTIVE,
)

relation_objective_factories: Registry[Any] = Registry("relation_training_objective")


def build_relation_objective(name: str):
    """Lazy-load and construct one registered relation objective."""
    if name not in RELATION_OBJECTIVE_NAMES:
        raise ValueError(f"unknown relation objective {name!r}")
    if name not in relation_objective_factories:
        importlib.import_module("ekg.relations.objectives")
    return relation_objective_factories.create(name)
