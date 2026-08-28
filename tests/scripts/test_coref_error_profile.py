"""The under-merge / over-merge split, on clusterings small enough to count by hand.

The corpus run cross-checks itself against the organisers' `evaluate.py`, which
is not vendored and so cannot run here. These tests pin the two things that
cross-check cannot: that the mention population is rebuilt the way the official
`evaluate_coreference` rebuilds it (singleton fill included), and that a
malformed prediction raises instead of being quietly absorbed.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "report_coref_error_profile",
    Path(__file__).resolve().parents[2] / "scripts" / "report_coref_error_profile.py",
)
_MODULE = importlib.util.module_from_spec(_SPEC)
# Registered before exec because `@dataclass` resolves annotations through
# `sys.modules[cls.__module__]`, which does not exist yet for a file-loaded module.
sys.modules[_SPEC.name] = _MODULE
_SPEC.loader.exec_module(_MODULE)  # type: ignore[union-attr]

aggregate = _MODULE.aggregate
official_clusterings = _MODULE.official_clusterings
profile_document = _MODULE.profile_document


def _gold(*events: tuple[str, list[tuple[str, str, int]]]) -> dict:
    """`("EV1", [(mention_id, trigger, sent_id), ...])` -> a MAVEN-ERE record."""
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


GOLD = _gold(
    ("EV1", [("a", "attack", 0), ("b", "attacked", 3), ("c", "assault", 7)]),
    ("EV2", [("d", "raid", 1)]),
    ("EV3", [("e", "raid", 5)]),
)


def test_unclustered_mentions_become_singletons() -> None:
    """The official scorer fills these in; profiling has to agree or the counts shift."""
    gold, predicted, mentions = official_clusterings(GOLD, {"coreference": [["a", "b"]]})
    assert gold == [{"a", "b", "c"}, {"d"}, {"e"}]
    assert sorted(map(sorted, predicted)) == [["a", "b"], ["c"], ["d"], ["e"]]
    assert mentions["b"].trigger == "attacked"
    assert mentions["c"].event_id == "EV1"


def test_split_cluster_is_counted_as_under_merge() -> None:
    totals = aggregate([profile_document(GOLD, {"coreference": [["a", "b"]]})])
    pairwise, muc = totals["pairwise"], totals["muc"]
    assert (pairwise["under_merged"], pairwise["over_merged"]) == (2, 0)  # a-c and b-c
    assert (muc["missing_links"], muc["spurious_links"]) == (1, 0)
    assert pairwise["under_merged_share"] == pytest.approx(1.0)
    assert (pairwise["gold_coref_pairs"], pairwise["predicted_coref_pairs"]) == (3, 1)


def test_fused_clusters_are_counted_as_over_merge() -> None:
    """`d` and `e` are different events that share the trigger "raid"."""
    totals = aggregate([profile_document(GOLD, {"coreference": [["a", "b", "c"], ["d", "e"]]})])
    pairwise, muc = totals["pairwise"], totals["muc"]
    assert (pairwise["under_merged"], pairwise["over_merged"]) == (0, 1)
    assert (muc["missing_links"], muc["spurious_links"]) == (0, 1)
    assert totals["over_merged_profile"]["n_similarity_ge_hard"] == 1  # identical triggers
    assert totals["over_merged_profile"]["n_cross_sentence"] == 1


def test_both_directions_are_reported_separately() -> None:
    totals = aggregate([profile_document(GOLD, {"coreference": [["a", "b"], ["c", "d"]]})])
    pairwise = totals["pairwise"]
    assert (pairwise["under_merged"], pairwise["over_merged"]) == (2, 1)
    assert pairwise["under_merged_share"] == pytest.approx(2 / 3)
    assert (totals["muc"]["missing_links"], totals["muc"]["spurious_links"]) == (1, 1)
    assert totals["structure"]["under_merged_by_gold_cluster_size"] == {3: 2}
    assert totals["structure"]["scatter_pieces"] == {2: 1}  # EV1 torn into two pieces
    assert totals["structure"]["fusion_gold_clusters"] == {1: 1, 2: 1}


def test_perfect_prediction_has_no_errors() -> None:
    totals = aggregate([profile_document(GOLD, {"coreference": [["a", "b", "c"]]})])
    assert totals["pairwise"]["n_errors"] == 0
    assert totals["muc"]["n_errors"] == 0
    assert totals["muc"]["precision"] == pytest.approx(1.0)
    assert totals["muc"]["recall"] == pytest.approx(1.0)


def test_fully_scattered_cluster_is_flagged() -> None:
    totals = aggregate([profile_document(GOLD, {"coreference": []})])
    assert totals["structure"]["n_gold_fully_scattered"] == 1
    assert totals["structure"]["n_pred_multi_clusters"] == 0
    assert totals["muc"]["recall"] == pytest.approx(0.0)


def test_a_mention_in_two_predicted_clusters_raises() -> None:
    """The official code writes a `-1` sentinel here rather than complaining."""
    with pytest.raises(SystemExit, match="two predicted clusters"):
        official_clusterings(GOLD, {"coreference": [["a", "b"], ["b", "c"]]})


def test_a_mention_absent_from_gold_raises() -> None:
    with pytest.raises(SystemExit, match="absent from gold"):
        official_clusterings(GOLD, {"coreference": [["a", "zzz"]]})
