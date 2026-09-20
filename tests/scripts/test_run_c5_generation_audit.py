import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / "runs/stages/R1/r1-v62-20260920/c5_generation_audit_plan.json"
SPEC = importlib.util.spec_from_file_location(
    "run_c5_generation_audit",
    ROOT / "scripts/run_c5_generation_audit.py",
)
assert SPEC is not None and SPEC.loader is not None
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


def _generator() -> dict:
    return {
        "model": "open/model",
        "config_revision": "a" * 40,
        "weight_revision": "b" * 40,
        "provider": "local-transformers",
        "license": "test-license",
        "decoding": {
            "do_sample": False,
            "temperature": 0.0,
            "top_p": 1.0,
            "max_new_tokens": 256,
            "seed": 260920,
            "enable_thinking": False,
        },
    }


def _generations(plan: dict) -> list[dict]:
    return [
        {
            "item_id": item["item_id"],
            "edited_context": f"Edited {item['left_trigger']} and {item['right_trigger']}.",
            "edited_left_trigger": item["left_trigger"],
            "edited_right_trigger": item["right_trigger"],
            "edit_rationale": "Changed one local wording while preserving event facts.",
        }
        for item in plan["items"]
    ]


def _reviews(plan: dict, value: bool = True) -> list[dict]:
    return [
        {
            "item_id": item["item_id"],
            "label_preserved": value,
            "fluent": value,
            "single_variable_compliant": value,
        }
        for item in plan["items"]
    ]


def test_requests_bind_all_frozen_items_and_disclose_generator() -> None:
    plan = audit.load_plan(PLAN)

    requests = audit.build_requests(plan, _generator())

    assert len(requests) == 100
    assert {row["item_id"] for row in requests} == {
        item["item_id"] for item in plan["items"]
    }
    assert all(row["generator"]["config_revision"] == "a" * 40 for row in requests)
    assert all("classifier" not in str(row).lower() for row in requests)


def test_generation_validation_and_review_template_hide_strata() -> None:
    plan = audit.load_plan(PLAN)
    generations = audit.validate_generations(plan, _generations(plan))

    review = audit.build_review_template(plan, generations)

    assert len(review) == 100
    assert all("stratum" not in row for row in review)
    assert all("classifier" not in row for row in review)
    assert {row["required_relation_after_edit"] for row in review} == {
        "coreferent",
        "non-coreferent",
    }


def test_generation_validation_rejects_missing_duplicate_and_deleted_trigger() -> None:
    plan = audit.load_plan(PLAN)
    rows = _generations(plan)
    with pytest.raises(ValueError, match="coverage mismatch"):
        audit.validate_generations(plan, rows[:-1])

    duplicate = [*rows, rows[0]]
    with pytest.raises(ValueError, match="duplicate generation"):
        audit.validate_generations(plan, duplicate)

    rows[0] = {**rows[0], "edited_context": "Neither target is present."}
    with pytest.raises(ValueError, match="absent from edited_context"):
        audit.validate_generations(plan, rows)


def test_review_thresholds_accept_exact_boundary_and_reject_below_it() -> None:
    plan = audit.load_plan(PLAN)
    reviews = _reviews(plan)
    first_stratum = plan["items"][0]["stratum"]
    same_stratum = [
        item["item_id"] for item in plan["items"] if item["stratum"] == first_stratum
    ]
    by_id = {row["item_id"]: row for row in reviews}
    for item_id in same_stratum[:5]:
        by_id[item_id]["label_preserved"] = False
    for row in reviews[:5]:
        row["fluent"] = False
    for row in reviews[:10]:
        row["single_variable_compliant"] = False

    boundary = audit.score_reviews(plan, reviews)

    assert boundary["status"] == "pass"
    assert boundary["rates"]["overall"]["label_preserved"] == 0.95
    assert boundary["rates"]["label_preserved_by_stratum"][first_stratum] == 0.9
    assert boundary["classifier_training_authorized"] is False

    by_id[same_stratum[5]]["label_preserved"] = False
    below = audit.score_reviews(plan, reviews)
    assert below["status"] == "failed"
    assert below["criteria"]["label_preserved_overall"] is False


def test_reviews_require_real_booleans() -> None:
    plan = audit.load_plan(PLAN)
    reviews = _reviews(plan)
    reviews[0]["fluent"] = 1

    with pytest.raises(ValueError, match="must be boolean"):
        audit.score_reviews(plan, reviews)


def test_generator_config_is_exact_and_complete() -> None:
    config = _generator()
    assert audit.validate_generator_config(config) == config

    with pytest.raises(ValueError, match="fields must be"):
        audit.validate_generator_config({**config, "checkpoint": "extra"})
