"""Contracts the role-compatibility residual has to hold before any GPU run."""

from __future__ import annotations

import pytest

from ekg.core.schema import EventNode, EvidenceSpan
from ekg.nodes.discriminative import (
    ROLE_COMPATIBILITY,
    head_input_dim,
    validate_components,
)
from ekg.nodes.role_uncertainty import (
    ROLE_FEATURE_NAMES,
    argument_sidecar,
    batch_role_compatibility_features,
    incompatible_role_merges,
    mention_argument_state,
    permute_role_features,
    role_compatibility_features,
)


def mention(
    event_id: str,
    *,
    doc_id: str = "doc-1",
    event_type: str = "Attack",
    state: str = "ok",
    participant: tuple[str, ...] = (),
    place: tuple[str, ...] = (),
) -> EventNode:
    evidence: dict[str, list[EvidenceSpan]] = {}
    for role, fillers in (("participant", participant), ("place", place)):
        spans = [
            EvidenceSpan(doc_id=doc_id, char_start=index, char_end=index + len(text), text=text)
            for index, text in enumerate(fillers)
        ]
        if spans:
            evidence[role] = spans
    return EventNode(
        event_id=event_id,
        event_type=event_type,
        doc_id=doc_id,
        trigger="attacked",
        argument_evidence=evidence,
        metadata={"argument_prediction_status": state},
    )


def features_of(head: EventNode, tail: EventNode) -> dict[str, float]:
    return dict(zip(ROLE_FEATURE_NAMES, role_compatibility_features(head, tail), strict=True))


def test_a_mention_without_a_recorded_state_is_an_error_not_an_empty_one() -> None:
    node = mention("m1")
    node.metadata.pop("argument_prediction_status")
    with pytest.raises(ValueError, match="argument state"):
        mention_argument_state(node)

    node.metadata["argument_prediction_status"] = "unknown"
    with pytest.raises(ValueError, match="argument state"):
        mention_argument_state(node)


def test_missing_on_one_side_is_not_scored_as_disagreement() -> None:
    present = mention("m1", participant=("the militia",))
    absent = mention("m2", state="empty")

    values = features_of(present, absent)

    assert values["participant_one_missing"] == 1.0
    assert values["participant_both_present"] == 0.0
    assert values["participant_both_missing"] == 0.0
    # The agreement features must stay silent: there was nothing to compare.
    assert values["participant_exact_match"] == 0.0
    assert values["participant_token_jaccard"] == 0.0


def test_both_sides_missing_is_its_own_fact() -> None:
    values = features_of(mention("m1", state="empty"), mention("m2", state="empty"))

    assert values["participant_both_missing"] == 1.0
    assert values["place_both_missing"] == 1.0
    assert values["participant_one_missing"] == 0.0
    assert values["either_unresolved"] == 1.0


def test_incompatible_fillers_separate_from_compatible_ones() -> None:
    head = mention("m1", participant=("the militia",), place=("Aleppo",))
    same = mention("m2", participant=("the militia",), place=("Aleppo",))
    other = mention("m3", participant=("the police",), place=("Homs",))

    agree, disagree = features_of(head, same), features_of(head, other)

    assert agree["participant_exact_match"] == 1.0
    assert agree["participant_token_jaccard"] == 1.0
    assert disagree["participant_exact_match"] == 0.0
    assert disagree["participant_token_jaccard"] == 0.0
    # Both pairs had evidence on both sides; only the verdict differs.
    assert agree["participant_both_present"] == disagree["participant_both_present"] == 1.0


def test_partial_and_rejected_states_mark_the_pair_unresolved() -> None:
    head = mention("m1", participant=("the militia",), state="partial")
    tail = mention("m2", participant=("the militia",), state="ok")

    values = features_of(head, tail)

    assert values["head_unresolved"] == 1.0
    assert values["tail_unresolved"] == 0.0
    assert values["either_unresolved"] == 1.0
    # An unresolved state does not erase the comparison that was possible.
    assert values["participant_exact_match"] == 1.0


def test_duplicate_fillers_do_not_inflate_overlap() -> None:
    head = mention("m1", participant=("the militia", "the militia"))
    tail = mention("m2", participant=("the militia",))

    assert features_of(head, tail)["participant_token_jaccard"] == 1.0


def test_permutation_keeps_the_stratum_marginals_and_breaks_the_pairing() -> None:
    nodes = [
        mention("m1", participant=("a",)),
        mention("m2", participant=("b",)),
        mention("m3", participant=("c",)),
        mention("m4", state="empty"),
    ]
    nodes_by_id = {node.event_id: node for node in nodes}
    pairs = [("m1", "m2"), ("m1", "m3"), ("m2", "m3"), ("m1", "m4"), ("m2", "m4")]
    features = batch_role_compatibility_features(pairs, nodes_by_id)

    permuted = permute_role_features(pairs, nodes_by_id, features, seed=13)

    assert sorted(map(tuple, permuted)) == sorted(map(tuple, features))
    assert permute_role_features(pairs, nodes_by_id, features, seed=13) == permuted


def test_permutation_never_crosses_an_event_type() -> None:
    nodes = [
        mention("m1", event_type="Attack", participant=("a",)),
        mention("m2", event_type="Attack", participant=("a",)),
        mention("m3", event_type="Arriving", state="empty"),
        mention("m4", event_type="Arriving", state="empty"),
    ]
    nodes_by_id = {node.event_id: node for node in nodes}
    pairs = [("m1", "m2"), ("m3", "m4")]
    features = batch_role_compatibility_features(pairs, nodes_by_id)

    permuted = permute_role_features(pairs, nodes_by_id, features, seed=13)

    # Each stratum holds one pair, so shuffling inside it cannot move anything.
    assert permuted == [list(row) for row in features]


def test_permutation_rejects_a_feature_table_that_does_not_cover_the_pairs() -> None:
    nodes_by_id = {node.event_id: node for node in (mention("m1"), mention("m2"))}
    with pytest.raises(ValueError, match="cover"):
        permute_role_features([("m1", "m2")], nodes_by_id, [], seed=13)


def test_mediator_counts_only_the_false_merges_it_claims_to_reduce() -> None:
    nodes = [
        mention("m1", participant=("the militia",)),
        mention("m2", participant=("the police",)),
        mention("m3", participant=("the militia",)),
        mention("m4", state="empty"),
    ]
    nodes_by_id = {node.event_id: node for node in nodes}
    pairs = [("m1", "m2"), ("m1", "m3"), ("m1", "m4")]
    merged = {("m1", "m2"): True, ("m1", "m3"): True, ("m1", "m4"): True}
    gold = {("m1", "m2"): False, ("m1", "m3"): True, ("m1", "m4"): False}

    counts = incompatible_role_merges(pairs, nodes_by_id, merged, gold)

    assert counts["pairs"] == 3
    assert counts["merged"] == 3
    assert counts["false_merges"] == 2
    # Only m1/m2 disagrees on a role both sides answered; m1/m4 is merely missing.
    assert counts["role_incompatible"] == 1
    assert counts["incompatible_merges"] == 1
    assert counts["incompatible_false_merges"] == 1


def test_mediator_refuses_a_pair_with_no_prediction() -> None:
    nodes_by_id = {node.event_id: node for node in (mention("m1"), mention("m2"))}
    with pytest.raises(ValueError, match="missing a prediction"):
        incompatible_role_merges([("m1", "m2")], nodes_by_id, {}, {("m1", "m2"): True})


def test_sidecar_covers_every_mention_including_the_empty_ones() -> None:
    nodes = [
        mention("m1", participant=("the militia",), place=("Aleppo",)),
        mention("m2", state="empty"),
        mention("m3", state="rejected"),
    ]

    sidecar = argument_sidecar(nodes)

    assert set(sidecar) == {"m1", "m2", "m3"}
    assert sidecar["m1"]["filler_count"] == 2
    assert sidecar["m2"] == {
        "doc_id": "doc-1",
        "event_type": "Attack",
        "state": "empty",
        "roles": {},
        "filler_count": 0,
    }
    assert sidecar["m3"]["state"] == "rejected"


def test_sidecar_rejects_a_duplicated_mention() -> None:
    with pytest.raises(ValueError, match="duplicate mention"):
        argument_sidecar([mention("m1"), mention("m1")])


def test_the_residual_is_one_component_that_switches_independently() -> None:
    assert ROLE_COMPATIBILITY in validate_components([ROLE_COMPATIBILITY])
    base = head_input_dim(8, ())
    with_role = head_input_dim(8, (ROLE_COMPATIBILITY,))

    # remove-core drops exactly the residual inputs and nothing else.
    assert with_role - base == len(ROLE_FEATURE_NAMES)
    assert head_input_dim(8, ("confusability", ROLE_COMPATIBILITY)) - head_input_dim(
        8, ("confusability",)
    ) == len(ROLE_FEATURE_NAMES)


def test_event_node_gained_no_field_for_any_of_this() -> None:
    # The schema lock: role state travels in metadata, never as a new column.
    assert "argument_prediction_status" not in EventNode.model_fields
    assert set(EventNode.model_fields) == {
        "event_id",
        "event_type",
        "doc_id",
        "trigger",
        "trigger_evidence",
        "arguments",
        "argument_evidence",
        "time_anchor",
        "subject",
        "confidence",
        "metadata",
    }
