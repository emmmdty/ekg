"""The LLM control has to be scored on what the model said, not on a repair.

An LLM row sits in each chapter's main table next to fine-tuned systems, so the
one thing that would make it dishonest is post-hoc patching: quietly dropping a
mention it never answered for, unioning two clusters it put a mention in twice,
or keeping a relation between ids no document contains.  Each of those would
raise the score without the model earning it.

So these tests pin the parses at exactly that boundary -- what is kept, what is
rejected, and that nothing is invented -- plus the one place a default is
unavoidable: `factuality_report` demands every gold mention, so an unanswered
one has to be labelled something, and that something is declared rather than
chosen per run.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ekg.llm_baseline import (
    CHAPTERS,
    UNANSWERED_FACTUALITY,
    extract_json_object,
    load_llm_baseline_config,
    official_shape,
    parse_factuality,
    parse_identity,
    parse_relation,
    render_prompt,
)

_ROOT = Path(__file__).resolve().parents[1]
_CONFIG = _ROOT / "data/protocols/v6/llm_baseline.json"
_IDS = [f"m{i}" for i in range(1, 6)]


@pytest.fixture(scope="module")
def config():
    return load_llm_baseline_config(_CONFIG)


def _mentions(ids=_IDS):
    return [
        {"mention_id": m, "trigger": f"t{i}", "sent_id": i} for i, m in enumerate(ids)
    ]


def test_the_config_carries_a_template_for_every_chapter(config) -> None:
    for chapter in CHAPTERS:
        section = config.chapter(chapter)
        assert "prompt_template" in section
        assert "mention_line" in section
    assert config.lora["finetuning_type"] == "lora"
    assert config.lora["seed"] == 13
    # Greedy: a sampled control would not be reproducible from its seed alone.
    assert config.decoding["temperature"] == 0.0


def test_the_config_has_a_hash_to_pin_it_by(config) -> None:
    assert len(config.sha256) == 64


def test_every_mention_makes_it_into_the_prompt(config) -> None:
    for chapter in CHAPTERS:
        prompt = render_prompt(config, chapter, document="doc", mentions=_mentions())
        for mention_id in _IDS:
            assert mention_id in prompt


def test_a_prompt_that_asks_nothing_is_refused(config) -> None:
    with pytest.raises(ValueError, match="asks the model nothing"):
        render_prompt(config, "relation", document="doc", mentions=[])


def test_a_mention_listed_twice_is_refused(config) -> None:
    doubled = _mentions() + _mentions(["m1"])
    with pytest.raises(ValueError, match="twice"):
        render_prompt(config, "identity", document="doc", mentions=doubled)


def test_json_is_recovered_from_the_prose_models_wrap_it_in() -> None:
    assert extract_json_object('Sure! {"a": 1} hope that helps') == {"a": 1}


def test_a_response_with_no_json_raises_rather_than_abstaining() -> None:
    with pytest.raises(ValueError, match="no JSON object"):
        extract_json_object("I cannot answer that.")


def test_factuality_labels_every_gold_mention_even_when_the_model_did_not() -> None:
    parsed = parse_factuality('{"m1": "CT+", "m2": "PS-"}', _IDS)
    assert set(parsed.prediction) == set(_IDS)
    assert parsed.answered == ["m1", "m2"]
    assert parsed.missing == ["m3", "m4", "m5"]
    for mention_id in parsed.missing:
        assert parsed.prediction[mention_id] == UNANSWERED_FACTUALITY


def test_factuality_rejects_an_invented_label_instead_of_guessing_near_it() -> None:
    parsed = parse_factuality('{"m1": "PROBABLY"}', ["m1"])
    assert "m1" in parsed.rejected
    assert parsed.prediction["m1"] == UNANSWERED_FACTUALITY
    assert parsed.answered == []


def test_factuality_records_a_label_for_a_mention_never_asked_about() -> None:
    parsed = parse_factuality('{"m1": "CT+", "ghost": "CT+"}', ["m1"])
    assert "ghost" in parsed.rejected
    assert "ghost" not in parsed.prediction


def test_an_unparseable_factuality_response_is_a_full_miss_not_an_empty_file() -> None:
    parsed = parse_factuality("I refuse.", _IDS)
    assert parsed.missing == _IDS
    assert set(parsed.prediction) == set(_IDS)
    assert len(parsed.rejected) == len(_IDS)


def test_relation_keeps_the_official_shape_whatever_the_model_returns(config) -> None:
    parsed = parse_relation("nonsense", "doc1", _IDS, config)
    assert parsed.prediction == official_shape("doc1", config)
    assert "response" in parsed.rejected


def test_relation_drops_pairs_the_document_cannot_contain(config) -> None:
    text = json.dumps(
        {
            "causal_relations": {"CAUSE": [["m1", "m2"], ["m1", "ghost"], ["m3", "m3"]]},
            "temporal_relations": {"BEFORE": [["m2", "m3"]]},
            "subevent_relations": [["m4", "m5"]],
        }
    )
    parsed = parse_relation(text, "doc1", _IDS, config)
    assert parsed.prediction["causal_relations"]["CAUSE"] == [["m1", "m2"]]
    assert parsed.prediction["temporal_relations"]["BEFORE"] == [["m2", "m3"]]
    assert parsed.prediction["subevent_relations"] == [["m4", "m5"]]
    assert len(parsed.rejected) == 2  # the unknown id and the self-relation


def test_relation_refuses_a_type_that_is_not_in_the_family(config) -> None:
    text = json.dumps({"causal_relations": {"ENABLES": [["m1", "m2"]]}})
    parsed = parse_relation(text, "doc1", _IDS, config)
    assert "causal_relations.ENABLES" in parsed.rejected
    assert parsed.prediction["causal_relations"] == {"CAUSE": [], "PRECONDITION": []}


def test_identity_refuses_to_put_one_mention_in_two_clusters(config) -> None:
    """Unioning them would score differently, and the scorer accepts either."""
    text = json.dumps({"coreference": [["m1", "m2"], ["m2", "m3"]]})
    parsed = parse_identity(text, "doc1", _IDS, config)
    assert parsed.prediction["coreference"] == [["m1", "m2"]]
    assert any("already in another cluster" in reason for reason in parsed.rejected.values())


def test_identity_drops_a_singleton_group_without_calling_it_an_error(config) -> None:
    text = json.dumps({"coreference": [["m1", "m2"], ["m3"]]})
    parsed = parse_identity(text, "doc1", _IDS, config)
    assert parsed.prediction["coreference"] == [["m1", "m2"]]
    assert parsed.rejected == {}
    assert "m3" in parsed.missing


def test_identity_records_an_id_from_no_document(config) -> None:
    text = json.dumps({"coreference": [["m1", "ghost"], ["m1", "m2"]]})
    parsed = parse_identity(text, "doc1", _IDS, config)
    assert any("not in this document" in reason for reason in parsed.rejected.values())
    assert all("ghost" not in cluster for cluster in parsed.prediction["coreference"])


def test_the_recorded_fixture_responses_cover_every_chapter() -> None:
    payload = json.loads(
        (_ROOT / "data/fixtures/llm_baseline/responses.json").read_text(encoding="utf-8")
    )
    assert set(payload["responses"]) == set(CHAPTERS)


def test_the_fixture_document_holds_the_ten_inputs_c7_asks_for() -> None:
    document = json.loads(
        (_ROOT / "data/fixtures/llm_baseline/document.jsonl").read_text(encoding="utf-8")
    )
    mentions = [m for event in document["events"] for m in event["mention"]]
    assert len(mentions) == 10
    assert all(m.get("factuality") for m in mentions), "each needs a gold label to score"
