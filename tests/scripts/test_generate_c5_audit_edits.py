import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "generate_c5_audit_edits",
    ROOT / "scripts/generate_c5_audit_edits.py",
)
assert SPEC is not None and SPEC.loader is not None
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


def _generator() -> dict:
    return {
        "model": "Qwen/Qwen3-8B",
        "config_revision": "a" * 40,
        "weight_revision": "b" * 40,
        "provider": "local",
        "license": "Apache-2.0",
        "decoding": {
            "do_sample": False,
            "temperature": 0.0,
            "top_p": 1.0,
            "max_new_tokens": 1536,
            "seed": 260920,
            "enable_thinking": False,
        },
    }


def _request(item_id: str) -> dict:
    return {
        "item_id": item_id,
        "generator": _generator(),
        "messages": [
            {"role": "system", "content": "system"},
            {"role": "user", "content": "user"},
        ],
        "response_format": "json_object",
    }


def _response(item_id: str) -> dict:
    return {
        "item_id": item_id,
        "edited_context": "The attack happened.",
        "edited_left_trigger": "attack",
        "edited_right_trigger": "happened",
        "edit_rationale": "one local edit",
    }


def test_request_bindings_require_exact_generator_and_count() -> None:
    rows = runner.validate_request_bindings(
        [_request("a"), _request("b")],
        _generator(),
        expected_items=2,
    )
    assert [row["item_id"] for row in rows] == ["a", "b"]

    drifted = _request("a")
    drifted["generator"] = {**_generator(), "weight_revision": "c" * 40}
    with pytest.raises(ValueError, match="differs from frozen config"):
        runner.validate_request_bindings([drifted], _generator(), expected_items=1)


def test_request_bindings_reject_duplicates_and_message_drift() -> None:
    with pytest.raises(ValueError, match="duplicate request"):
        runner.validate_request_bindings(
            [_request("a"), _request("a")], _generator(), expected_items=2
        )

    row = _request("a")
    row["messages"].reverse()
    with pytest.raises(ValueError, match="system then user"):
        runner.validate_request_bindings([row], _generator(), expected_items=1)


def test_strict_response_accepts_only_bare_exact_json() -> None:
    payload = _response("a")
    assert runner.parse_strict_response("a", json.dumps(payload)) == payload

    with pytest.raises(ValueError, match="bare JSON"):
        runner.parse_strict_response("a", f"```json\n{json.dumps(payload)}\n```")
    with pytest.raises(ValueError, match="item_id mismatch"):
        runner.parse_strict_response("b", json.dumps(payload))
    with pytest.raises(ValueError, match="fields must be exactly"):
        runner.parse_strict_response("a", json.dumps({**payload, "extra": "no"}))
