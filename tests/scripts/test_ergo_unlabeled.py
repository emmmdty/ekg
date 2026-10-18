import copy
import importlib.util
from pathlib import Path

import pytest


def script():
    spec = importlib.util.spec_from_file_location(
        "ergo_unlabeled", Path("scripts/prepare_ergo_unlabeled.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def source():
    return {"id": "d", "title": "unused", "sentences": ["A caused B"],
            "tokens": [["A", "caused", "B"]],
            "event_mentions": [
                {"id": "b", "sent_id": 0, "offset": [2, 3], "trigger_word": "B",
                 "type": "secret-b", "type_id": 19},
                {"id": "a", "sent_id": 0, "offset": [0, 1], "trigger_word": "A",
                 "type": "secret-a", "type_id": 20}], "TIMEX": []}


def test_unlabeled_projection_rejects_gold_and_removes_given_type_metadata():
    raw = source()
    original = copy.deepcopy(raw)
    projection = script().project_unlabeled(raw)
    assert projection == {"id": "d", "tokens": [["A", "caused", "B"]], "TIMEX": [],
                          "event_mentions": [
                              {"id": "b", "sent_id": 0, "offset": [2, 3]},
                              {"id": "a", "sent_id": 0, "offset": [0, 1]}]}
    assert raw == original
    for field in ("events", "causal_relations", "coreference"):
        with pytest.raises(ValueError, match="unlabeled"):
            script().project_unlabeled(raw | {field: []})


def test_unlabeled_packing_retains_physical_marker_order_and_every_direction():
    raw = script().project_unlabeled(source())
    # BOS <t> A </t> caused <t> B </t> EOS; B occurred first in source metadata.
    encoded = [0, 50265, 8, 50266, 9, 50265, 10, 50266, 2]
    packed, witness = script().pack_feature(raw, encoded, start=50265, end=50266, length=12)
    assert packed == {"id": "d", "mention_ids": ["a", "b"],
                      "enc_input_ids": encoded + [1, 1, 1], "enc_mask_ids": [1] * 9 + [0] * 3,
                      "global_attention_mask": [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
                      "t1_pos": [1, 5], "t2_pos": [5, 1]}
    assert witness["pairs"] == 2
    assert witness["nonpad_tokens"] == 9
    assert witness["marker_positions"] == {"a": 1, "b": 5}
    for bad in (encoded[:-1], [0, 50265, 8, 50266, 2], encoded + [50265]):
        with pytest.raises(ValueError, match="endpoint|BOS|EOS"):
            script().pack_feature(raw, bad, start=50265, end=50266, length=12)
    with pytest.raises(ValueError, match="overlong"):
        script().pack_feature(raw, encoded, start=50265, end=50266, length=8)
