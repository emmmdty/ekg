import copy
import importlib.util
from pathlib import Path

import pytest

from ekg.relations.ergo_adapter import (
    causal_targets,
    criss_cross_mask,
    export_causal_classes,
    longformer_inputs,
    marked_document,
    native_pair_features,
)


def document():
    return {
        "id": "d", "tokens": [["one", "two", "three"]], "TIMEX": [],
        "event_mentions": [
            {"id": "c", "sent_id": 0, "offset": [2, 3], "type": "ignored"},
            {"id": "a", "sent_id": 0, "offset": [0, 1]},
            {"id": "b", "sent_id": 0, "offset": [1, 2]},
        ],
    }


def test_marker_text_preserves_words_and_orders_endpoints_without_type_input():
    raw = document()
    before = copy.deepcopy(raw)
    text, markers = marked_document(raw)
    assert text == "<t> one </t> <t> two </t> <t> three </t>"
    assert markers == ["a", "b", "c"]
    assert raw == before
    raw["event_mentions"][0]["type"] = "another type"
    assert marked_document(raw) == (text, markers)


def test_longformer_global_boundaries_match_released_cache_without_padding_attention():
    f = longformer_inputs([0, 50265, 99, 50266, 2], padded_length=8)
    assert f == {
        "enc_input_ids": [0, 50265, 99, 50266, 2, 1, 1, 1],
        "enc_mask_ids": [1, 1, 1, 1, 1, 0, 0, 0],
        "global_attention_mask": [1, 0, 0, 0, 1, 0, 0, 0],
    }
    assert longformer_inputs([0, 99, 2], padded_length=3)["global_attention_mask"] == [1, 0, 1]
    for wrong in ([0, 99, 3], [1, 99, 2], [0, 1, 99, 2], [0, 99, 99, 99, 2]):
        with pytest.raises(ValueError):
            longformer_inputs(wrong, padded_length=4)


def test_overlapping_and_coincident_mentions_are_all_preserved():
    raw = document()
    raw["event_mentions"][0]["offset"] = [0, 2]
    raw["event_mentions"][2]["offset"] = [0, 1]
    text, markers = marked_document(raw)
    assert markers == ["a", "b", "c"]
    assert text.count("<t>") == text.count("</t>") == 3
    assert text.replace("<t>", "").replace("</t>", "").split() == raw["tokens"][0]


@pytest.mark.parametrize("bad", ["gold", "offset", "duplicate", "marker", "singleton"])
def test_marker_inputs_fail_closed(bad):
    raw = document()
    if bad == "gold":
        raw["events"] = []
    elif bad == "offset":
        raw["event_mentions"][0]["offset"] = [2, 4]
    elif bad == "duplicate":
        raw["event_mentions"][0]["id"] = "a"
    elif bad == "marker":
        raw["tokens"][0][0] = "text<t>collision"
    else:
        raw["event_mentions"] = raw["event_mentions"][:1]
    with pytest.raises(ValueError):
        marked_document(raw)


def test_complete_directed_pair_interface_and_marker_identity():
    raw = document()
    f = native_pair_features(raw, {"c": 11, "a": 2, "b": 7})
    assert f["pair_ids"] == [("a", "b"), ("a", "c"), ("b", "a"),
                             ("b", "c"), ("c", "a"), ("c", "b")]
    assert f["t1_pos"] == [2, 2, 7, 7, 11, 11]
    assert f["t2_pos"] == [7, 11, 2, 11, 2, 7]
    for wrong in ({"a": 2}, {"a": 2, "b": 2, "c": 11},
                  {"a": 2, "b": -1, "c": 11}, {"a": 2, "b": True, "c": 11}):
        with pytest.raises(ValueError):
            native_pair_features(raw, wrong)


def gold_document():
    raw = document()
    return {
        "id": "d", "TIMEX": [],
        "events": [
            {"id": "e1", "mention": raw["event_mentions"][1:]},
            {"id": "e2", "mention": raw["event_mentions"][:1]},
        ],
        "causal_relations": {"PRECONDITION": [["e1", "e2"]], "CAUSE": []},
    }


def test_native_labels_cartesian_expansion_direction_and_subtype_round_trip():
    raw, gold = document(), gold_document()
    labels = causal_targets(raw, gold)
    assert labels == [0, 1, 0, 1, 0, 0]
    p = export_causal_classes(raw, labels)
    assert p["causal_relations"] == {"CAUSE": [], "PRECONDITION": [["a", "c"], ["b", "c"]]}
    assert p["coreference"] == []
    assert all(not v for v in p["temporal_relations"].values())
    gold["causal_relations"] = {"PRECONDITION": [], "CAUSE": [["e2", "e1"]]}
    assert causal_targets(raw, gold) == [0, 0, 0, 0, 2, 2]


@pytest.mark.parametrize("bad", ["coverage", "doc", "conflict", "unknown_subtype", "event"])
def test_gold_supervision_rejects_bad_alignment(bad):
    raw, gold = document(), gold_document()
    if bad == "coverage":
        gold["events"][0]["mention"] = gold["events"][0]["mention"][:1]
    elif bad == "doc":
        gold["id"] = "other"
    elif bad == "conflict":
        gold["causal_relations"]["CAUSE"] = [["e1", "e2"]]
    elif bad == "unknown_subtype":
        gold["causal_relations"]["OTHER"] = []
    else:
        gold["causal_relations"]["CAUSE"] = [["unknown", "e1"]]
    with pytest.raises(ValueError):
        causal_targets(raw, gold)


@pytest.mark.parametrize("labels", [[0], [0, 0, 0, 0, 0, 3], [0, 0, 0, 0, 0, True]])
def test_export_cannot_hide_unknown_classes_or_missing_candidates(labels):
    with pytest.raises(ValueError):
        export_causal_classes(document(), labels)


def test_export_matches_official_subtype_metric_and_binary_case():
    path = Path("data/protocols/v6/tools/maven_ere_evaluate.py")
    spec = importlib.util.spec_from_file_location("ergo_official_evaluator", path)
    evaluator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(evaluator)
    raw, gold = document(), gold_document()
    labels = causal_targets(raw, gold)
    exact = export_causal_classes(raw, labels)
    assert evaluator.evaluate({"d": gold}, {"d": exact}, "causal")["causal_f1"] == 100.0
    swapped = export_causal_classes(raw, [2 if v == 1 else v for v in labels])
    scores = evaluator.evaluate({"d": gold}, {"d": swapped}, "causal")
    assert scores == {"causal_precision": 0.0, "causal_recall": 0.0, "causal_f1": 0.0}
    one_missed = export_causal_classes(raw, [0, 1, 0, 0, 0, 0])
    scores = evaluator.evaluate({"d": gold}, {"d": one_missed}, "causal")
    assert scores["causal_precision"] == 100.0 and scores["causal_recall"] == 50.0
    assert scores["causal_f1"] == pytest.approx(200 / 3)


def test_mask_matches_original_no_self_policy_and_reciprocal_neighbors():
    torch = pytest.importorskip("torch")
    # ab and cd do not share endpoints; ba is a legitimate neighbor of ab.
    pairs = [("a", "b"), ("b", "a"), ("c", "d")]
    actual = criss_cross_mask(pairs)
    assert actual.dtype == torch.bool
    assert actual.tolist() == [[True, False, True], [False, True, True], [True, True, True]]
    # A full two-event native population avoids the original singleton-neighborhood issue.
    assert criss_cross_mask(pairs[:2]).tolist() == [[True, False], [False, True]]
    with pytest.raises(ValueError):
        criss_cross_mask([("a", "a")])
