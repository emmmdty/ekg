"""The suppression bound, on clusterings small enough to count by hand.

The corpus run cross-checks itself by replaying the arm's own MUC F1 through the
organisers' `evaluate.py`, which is not vendored and so cannot run here. What
these tests pin is the part that cross-check cannot see: that a veto only splits
a cluster when it actually disconnects it, and that `oracle` spares the pairs
`blind` throws away. Both decide whether the printed ceiling means anything.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "report_coref_suppression_bound",
    Path(__file__).resolve().parents[2] / "scripts" / "report_coref_suppression_bound.py",
)
_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _MODULE
_SPEC.loader.exec_module(_MODULE)  # type: ignore[union-attr]

bucket_pairs = _MODULE.bucket_pairs
suppress_document = _MODULE.suppress_document


def _gold(*events: tuple[str, list[tuple[str, str, int]]]) -> dict:
    return {
        "id": "doc1",
        "events": [
            {
                "id": event_id,
                "mention": [
                    {"id": mid, "trigger_word": trigger, "sent_id": sent}
                    for mid, trigger, sent in mentions
                ],
            }
            for event_id, mentions in events
        ],
    }


# `d`/`e` are different events sharing the trigger "raid" -- a merge of the two
# is exactly the over-merge the >= 0.8 bucket is supposed to catch.
GOLD = _gold(
    ("EV1", [("a", "attack", 0), ("b", "attacked", 3)]),
    ("EV2", [("d", "raid", 1)]),
    ("EV3", [("e", "raid", 5)]),
)


def test_no_op_returns_the_prediction_unchanged() -> None:
    clusters, wrong, right = suppress_document(
        GOLD, {"coreference": [["d", "e"]]}, tau=None, oracle=True, cross_only=True
    )
    assert clusters == [["d", "e"]]
    assert (wrong, right) == (0, 0)


def test_the_bucket_splits_a_fused_cluster() -> None:
    clusters, wrong, right = suppress_document(
        GOLD, {"coreference": [["d", "e"]]}, tau=0.8, oracle=True, cross_only=True
    )
    assert clusters == []  # both mentions fall back to singletons
    assert (wrong, right) == (1, 0)


def test_blind_also_vetoes_the_correct_pair() -> None:
    """`a`/`b` are one gold event with near-identical triggers: the recall cost."""
    pred = {"coreference": [["a", "b"]]}
    kept, _, _ = suppress_document(GOLD, pred, tau=0.8, oracle=True, cross_only=True)
    lost, wrong, right = suppress_document(GOLD, pred, tau=0.8, oracle=False, cross_only=True)
    assert kept == [["a", "b"]]
    assert (lost, wrong, right) == ([], 0, 1)


def test_a_cluster_held_together_below_the_bucket_does_not_split() -> None:
    """The whole point of the bound: "attack"-"raid" is out of reach at 0.8."""
    clusters, wrong, _ = suppress_document(
        GOLD, {"coreference": [["a", "d", "e"]]}, tau=0.8, oracle=True, cross_only=True
    )
    assert clusters == [["a", "d", "e"]]  # only d-e was vetoed; a still joins both
    assert wrong == 1


def test_bucket_pairs_tags_wrong_and_right() -> None:
    pairs = bucket_pairs(
        {"doc1": GOLD}, {"doc1": {"coreference": [["a", "b"], ["d", "e"]]}},
        tau=0.8, cross_only=True,
    )
    assert sorted((a, b, is_wrong) for _, a, b, is_wrong in pairs) == [
        ("a", "b", False),
        ("d", "e", True),
    ]
