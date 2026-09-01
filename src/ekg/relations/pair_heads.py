"""Registered pair-scoring heads and checkpoint identity.

The training and inference paths both resolve a head from this registry.  Old
checkpoints predate ``pair_head.json`` and therefore resolve to ``linear``;
new mechanisms must write the file so their architecture cannot be mistaken
for the reproduction baseline.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

from ekg.core.registry import Registry

__all__ = [
    "LINEAR_HEAD",
    "PAIR_HEAD_CONFIG_FILE",
    "PAIR_HEAD_NAMES",
    "PROTOTYPE_DEPENDENCY_HEAD",
    "PROTOTYPE_HEAD",
    "build_pair_head",
    "load_pair_head_config",
    "pair_head_factories",
]

PAIR_HEAD_CONFIG_FILE = "pair_head.json"
LINEAR_HEAD = "linear"
PROTOTYPE_HEAD = "prototype"
PROTOTYPE_DEPENDENCY_HEAD = "prototype_dependency"
PAIR_HEAD_NAMES = (LINEAR_HEAD, PROTOTYPE_HEAD, PROTOTYPE_DEPENDENCY_HEAD)

pair_head_factories: Registry[Any] = Registry("relation_pair_head")


def load_pair_head_config(checkpoint: Path) -> dict[str, str]:
    """Read the immutable head identity; legacy checkpoints are linear."""
    path = checkpoint / PAIR_HEAD_CONFIG_FILE
    if not path.is_file():
        return {"schema_version": "legacy", "name": LINEAR_HEAD}
    payload = json.loads(path.read_text(encoding="utf-8"))
    expected = {"schema_version", "name"}
    if not isinstance(payload, dict) or set(payload) != expected:
        raise ValueError(f"{path} must contain exactly {sorted(expected)}")
    if payload["schema_version"] != "ekg.relation_pair_head.v1":
        raise ValueError(f"{path} has an unsupported schema_version")
    if payload["name"] not in PAIR_HEAD_NAMES:
        raise ValueError(f"{path} has unknown pair head {payload['name']!r}")
    return payload


def build_pair_head(name: str, **kwargs: object):
    """Lazy-load and construct a registered pair head."""
    if name not in PAIR_HEAD_NAMES:
        raise ValueError(f"unknown pair head {name!r}")
    if name not in pair_head_factories:
        module = (
            "ekg.relations.extractor.supervised"
            if name == LINEAR_HEAD
            else "ekg.relations.prototype"
        )
        importlib.import_module(module)
    return pair_head_factories.create(name, **kwargs)
