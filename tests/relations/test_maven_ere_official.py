"""Strict wrapper tests independent of the externally restored evaluator."""

from __future__ import annotations

import copy

import pytest

from ekg.relations.maven_ere_official import (
    OfficialProtocolError,
    candidate_population_digest,
    candidate_protocol_summary,
    gold_to_official_prediction,
    records_by_id,
    temporal_candidate_summary,
    validate_official_predictions,
)


def _gold() -> dict:
    mention = lambda item: {"id": item}  # noqa: E731
    return {
        "id": "d1",
        "events": [
            {"id": "e1", "mention": [mention("m1"), mention("m2")]},
            {"id": "e2", "mention": [mention("m3"), mention("m4")]},
        ],
        "TIMEX": [{"id": "t1"}],
        "temporal_relations": {"BEFORE": [["e1", "t1"]]},
        "causal_relations": {"CAUSE": [["e1", "e2"]]},
        "subevent_relations": [["e1", "e2"]],
    }


def test_gold_converter_expands_event_relations_and_passes_strict_validation() -> None:
    gold = _gold()
    prediction = gold_to_official_prediction(gold)

    assert prediction["causal_relations"]["CAUSE"] == [
        ["m1", "m3"],
        ["m1", "m4"],
        ["m2", "m3"],
        ["m2", "m4"],
    ]
    assert prediction["temporal_relations"]["BEFORE"] == [["m1", "t1"], ["m2", "t1"]]
    digest, counts = candidate_population_digest({"d1": gold})
    result = validate_official_predictions(
        {"d1": gold},
        {"d1": prediction},
        expected_candidate_digest=digest,
    )
    assert result == {"candidate_id_digest": digest, **counts}


def test_wrapper_rejects_missing_document_duplicate_id_and_unknown_endpoint() -> None:
    gold = _gold()
    prediction = gold_to_official_prediction(gold)
    with pytest.raises(OfficialProtocolError, match="missing"):
        validate_official_predictions({"d1": gold}, {})
    with pytest.raises(OfficialProtocolError, match="duplicate"):
        records_by_id([prediction, prediction], source="pred")

    bad = copy.deepcopy(prediction)
    bad["causal_relations"]["CAUSE"][0][1] = "ghost"
    with pytest.raises(OfficialProtocolError, match="unknown endpoint"):
        validate_official_predictions({"d1": gold}, {"d1": bad})


def test_wrapper_rejects_duplicate_conflicting_and_drifted_candidates() -> None:
    gold = _gold()
    prediction = gold_to_official_prediction(gold)
    duplicate = copy.deepcopy(prediction)
    duplicate["causal_relations"]["CAUSE"].append(["m1", "m3"])
    with pytest.raises(OfficialProtocolError, match="duplicate pair"):
        validate_official_predictions({"d1": gold}, {"d1": duplicate})

    conflict = copy.deepcopy(prediction)
    conflict["causal_relations"]["PRECONDITION"].append(["m1", "m3"])
    with pytest.raises(OfficialProtocolError, match="conflicts"):
        validate_official_predictions({"d1": gold}, {"d1": conflict})

    with pytest.raises(OfficialProtocolError, match="digest mismatch"):
        validate_official_predictions(
            {"d1": gold},
            {"d1": prediction},
            expected_candidate_digest="0" * 64,
        )


def test_wrapper_rejects_extra_document_self_pair_and_missing_subtype() -> None:
    gold = _gold()
    prediction = gold_to_official_prediction(gold)
    extra = copy.deepcopy(prediction)
    extra["id"] = "d2"
    with pytest.raises(OfficialProtocolError, match="extra=.*d2"):
        validate_official_predictions(
            {"d1": gold},
            {"d1": prediction, "d2": extra},
        )

    self_pair = copy.deepcopy(prediction)
    self_pair["causal_relations"]["CAUSE"] = [["m1", "m1"]]
    with pytest.raises(OfficialProtocolError, match="self pair"):
        validate_official_predictions({"d1": gold}, {"d1": self_pair})

    missing_subtype = copy.deepcopy(prediction)
    del missing_subtype["causal_relations"]["PRECONDITION"]
    with pytest.raises(OfficialProtocolError, match="must contain exactly"):
        validate_official_predictions({"d1": gold}, {"d1": missing_subtype})


def test_wrapper_rejects_repeated_coreference_mention() -> None:
    gold = _gold()
    prediction = gold_to_official_prediction(gold)
    prediction["coreference"].append(["m1"])

    with pytest.raises(OfficialProtocolError, match="repeats mention m1"):
        validate_official_predictions({"d1": gold}, {"d1": prediction})


def test_temporal_universe_includes_timex_and_causal_universe_does_not() -> None:
    """Official MAVEN-ERE uses a different candidate universe per relation family.

    `joint/src/data.py` scores temporal with ``ignore_timex=False`` but causal and
    subevent with ``ignore_timex=True``. Merging the two universes would silently
    change the causal/subevent denominators.
    """
    record = {
        "id": "doc-1",
        "events": [
            {"id": "EV1", "mention": [{"id": "m1", "sent_id": 0, "offset": [0, 1]}]},
            {"id": "EV2", "mention": [{"id": "m2", "sent_id": 0, "offset": [2, 3]}]},
        ],
        "TIMEX": [{"id": "TIME_1", "sent_id": 0, "offset": [4, 5]}],
        "temporal_relations": {"BEFORE": [["EV1", "TIME_1"]]},
        "causal_relations": {"CAUSE": [["EV1", "EV2"]]},
        "subevent_relations": [],
    }

    causal = candidate_protocol_summary([record])["population_counts"]
    temporal = temporal_candidate_summary([record])["population_counts"]

    # causal/subevent: 2 event mentions -> 2 ordered pairs, no TIMEX endpoint
    assert causal["event_mentions"] == 2
    assert causal["ordered_mention_pairs"] == 2
    # temporal: 2 events + 1 TIMEX -> 3*2 ordered pairs, TIMEX is scoreable
    assert temporal["timex_mentions"] == 1
    assert temporal["scoreable_mentions"] == 3
    assert temporal["ordered_mention_pairs"] == 6
    assert temporal["positive_temporal:BEFORE"] == 1


def test_bidirectional_temporal_subtypes_are_scored_both_ways() -> None:
    """SIMULTANEOUS/BEGINS-ON are symmetric in official BIDIRECTIONAL_REL."""
    def _record(subtype: str) -> dict:
        return {
            "id": "doc-1",
            "events": [
                {"id": "EV1", "mention": [{"id": "m1", "sent_id": 0, "offset": [0, 1]}]},
                {"id": "EV2", "mention": [{"id": "m2", "sent_id": 0, "offset": [2, 3]}]},
            ],
            "TIMEX": [],
            "temporal_relations": {subtype: [["EV1", "EV2"]]},
        }

    symmetric = temporal_candidate_summary([_record("SIMULTANEOUS")])["population_counts"]
    directed = temporal_candidate_summary([_record("BEFORE")])["population_counts"]

    assert symmetric["positive_temporal:SIMULTANEOUS"] == 2
    assert directed["positive_temporal:BEFORE"] == 1
