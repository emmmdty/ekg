"""Tests for the ProtoEM-inspired relation pair heads."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from ekg.relations.pair_heads import (
    LINEAR_HEAD,
    PROTOTYPE_DEPENDENCY_HEAD,
    PROTOTYPE_HEAD,
    build_pair_head,
    load_pair_head_config,
)
from ekg.relations.pairs import SAME_SENTENCE, PairExample
from ekg.relations.prototype import (
    prototype_dependency_matrix,
    select_prototype_support,
)

_SUBTYPES = {
    "temporal": ("NONE", "BEFORE"),
    "causal": ("NONE", "CAUSE"),
    "subevent": ("NONE", "SUBEVENT_OF"),
}
_FAMILIES = tuple(_SUBTYPES)


def _row(index: int, labels: dict[str, str]) -> PairExample:
    return PairExample(
        doc_id=f"d{index // 4}",
        head_id=f"h{index}",
        tail_id=f"t{index}",
        distance=1,
        position=SAME_SENTENCE,
        labels=labels,
    )


def test_pair_head_config_defaults_legacy_checkpoints_to_linear(tmp_path: Path) -> None:
    assert load_pair_head_config(tmp_path)["name"] == LINEAR_HEAD


def test_pair_head_config_rejects_ambiguous_or_unknown_payload(tmp_path: Path) -> None:
    path = tmp_path / "pair_head.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "ekg.relation_pair_head.v1",
                "name": "unknown",
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="unknown pair head"):
        load_pair_head_config(tmp_path)
    path.write_text(json.dumps({"name": PROTOTYPE_HEAD}), encoding="utf-8")
    with pytest.raises(ValueError, match="exactly"):
        load_pair_head_config(tmp_path)


def test_support_selection_is_deterministic_and_covers_every_class() -> None:
    rows = [
        _row(i, {"temporal": "BEFORE", "causal": "CAUSE", "subevent": "SUBEVENT_OF"})
        for i in range(4)
    ]
    rows += [_row(10 + i, {}) for i in range(4)]
    first = select_prototype_support(
        rows, _SUBTYPES, _FAMILIES, per_class=2, seed=13
    )
    second = select_prototype_support(
        rows, _SUBTYPES, _FAMILIES, per_class=2, seed=13
    )
    assert first == second
    covered = {assignment for assignments in first.values() for assignment in assignments}
    assert covered == {
        (family, index) for family in _FAMILIES for index in range(2)
    }


def test_dependency_matrix_encodes_observed_cross_family_cooccurrence() -> None:
    rows = [
        _row(i, {"temporal": "BEFORE", "causal": "CAUSE"})
        for i in range(8)
    ]
    rows += [_row(100 + i, {}) for i in range(2)]
    matrix = prototype_dependency_matrix(rows, _SUBTYPES, _FAMILIES)
    assert matrix.shape == (6, 6)
    assert np.allclose(matrix, matrix.T)
    # Layout is temporal NONE/BEFORE, causal NONE/CAUSE, subevent NONE/SUBEVENT.
    assert matrix[1, 3] > matrix[1, 2]
    assert np.all(np.diag(matrix) > 0)
    # NONE prototypes are self-only; sparse negative co-occurrence must not
    # drown out positive relation semantics.
    assert np.count_nonzero(matrix[0]) == 1
    assert np.count_nonzero(matrix[2]) == 1


def test_prototype_logits_prefer_the_nearer_class_and_backpropagate() -> None:
    torch = pytest.importorskip("torch")
    from ekg.relations.prototype import prototype_logits

    instances = torch.tensor([[0.1, 0.0]], requires_grad=True)
    prototypes = torch.tensor([[0.0, 0.0], [2.0, 0.0]], requires_grad=True)
    logits = prototype_logits(instances, prototypes)
    assert logits.argmax(dim=-1).item() == 0
    logits[0, 0].backward()
    assert instances.grad is not None and prototypes.grad is not None


def test_registered_prototype_heads_have_expected_shapes_and_dependency_noop() -> None:
    torch = pytest.importorskip("torch")

    counts = {"temporal": 2, "causal": 2, "subevent": 2}
    plain = build_pair_head(PROTOTYPE_HEAD, hidden_size=4, subtype_counts=counts)
    dependency = build_pair_head(
        PROTOTYPE_DEPENDENCY_HEAD,
        hidden_size=4,
        subtype_counts=counts,
    )
    dependency.load_state_dict(plain.state_dict(), strict=False)
    assert torch.allclose(plain._prototype_matrix(), dependency._prototype_matrix())

    pair_features = torch.randn(3, 16)
    distances = torch.tensor([0, 1, 2])
    output = dependency(pair_features, distances)
    assert {family: tuple(logits.shape) for family, logits in output.items()} == {
        "temporal": (3, 2),
        "causal": (3, 2),
        "subevent": (3, 2),
    }
