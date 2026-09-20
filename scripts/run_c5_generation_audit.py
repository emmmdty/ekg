#!/usr/bin/env python
"""Build, validate and score the frozen C5 counterfactual generation audit.

This script never calls a generator. It creates the one-shot request set,
validates externally generated JSONL, creates a classifier-blind human review
sheet, and applies the thresholds frozen in the C-18 audit plan.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from collections.abc import Iterable, Mapping
from pathlib import Path

from ekg.core.stage_bundle import sha256_file

PLAN_SCHEMA = "r1-v62-c5-generation-audit-plan-v1"
GENERATOR_FIELDS = {
    "model",
    "config_revision",
    "weight_revision",
    "provider",
    "license",
    "decoding",
}
DECODING_FIELDS = {
    "do_sample",
    "temperature",
    "top_p",
    "max_new_tokens",
    "seed",
    "enable_thinking",
}


def _load_object(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _load_jsonl(path: Path) -> list[dict]:
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line:
            raise ValueError(f"{path}:{line_number}: blank JSONL row")
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"{path}:{line_number}: row must be a JSON object")
        rows.append(row)
    if not rows:
        raise ValueError(f"{path} has no rows")
    return rows


def _write_jsonl_new(path: Path, rows: Iterable[Mapping]) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(
            json.dumps(dict(row), sort_keys=True, separators=(",", ":")) + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )


def _write_object_new(path: Path, payload: Mapping) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(dict(payload), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def load_plan(path: Path) -> dict:
    plan = _load_object(path)
    if plan.get("schema_version") != PLAN_SCHEMA:
        raise ValueError(f"unexpected generation-audit schema: {plan.get('schema_version')!r}")
    items = plan.get("items")
    if not isinstance(items, list) or len(items) != 100:
        raise ValueError("generation-audit plan must contain exactly 100 items")
    ids = [item.get("item_id") for item in items if isinstance(item, dict)]
    if len(ids) != len(items) or any(not isinstance(item_id, str) for item_id in ids):
        raise ValueError("every generation-audit item needs a string item_id")
    if len(set(ids)) != len(ids):
        raise ValueError("generation-audit plan contains duplicate item IDs")
    strata = Counter(item.get("stratum") for item in items)
    if strata != {"hard_noncoreferent": 50, "divergent_coreferent": 50}:
        raise ValueError(f"generation-audit strata drifted: {dict(strata)}")
    return plan


def validate_generator_config(config: Mapping) -> dict:
    if set(config) != GENERATOR_FIELDS:
        raise ValueError(f"generator config fields must be {sorted(GENERATOR_FIELDS)}")
    for field in GENERATOR_FIELDS - {"decoding"}:
        if not isinstance(config[field], str) or not config[field]:
            raise ValueError(f"generator config {field} must be a non-empty string")
    decoding = config["decoding"]
    if not isinstance(decoding, dict) or set(decoding) != DECODING_FIELDS:
        raise ValueError(f"decoding fields must be {sorted(DECODING_FIELDS)}")
    if not isinstance(decoding["do_sample"], bool):
        raise ValueError("decoding do_sample must be boolean")
    if not isinstance(decoding["enable_thinking"], bool):
        raise ValueError("decoding enable_thinking must be boolean")
    if not isinstance(decoding["max_new_tokens"], int) or decoding["max_new_tokens"] <= 0:
        raise ValueError("decoding max_new_tokens must be a positive integer")
    if not isinstance(decoding["seed"], int):
        raise ValueError("decoding seed must be an integer")
    for field in ("temperature", "top_p"):
        if not isinstance(decoding[field], (int, float)):
            raise ValueError(f"decoding {field} must be numeric")
    return dict(config)


def _expected_relation(stratum: str) -> str:
    if stratum == "hard_noncoreferent":
        return "non-coreferent"
    if stratum == "divergent_coreferent":
        return "coreferent"
    raise ValueError(f"unknown generation stratum: {stratum!r}")


def build_requests(plan: Mapping, generator: Mapping) -> list[dict]:
    generator = validate_generator_config(generator)
    requests = []
    system = (
        "You edit event mentions for a controlled scientific audit. Return exactly one JSON "
        "object and no markdown. Preserve the stated coreference label and all event facts."
    )
    for item in plan["items"]:
        relation = _expected_relation(item["stratum"])
        direction = (
            "make exactly one target trigger lexically less similar to the other"
            if relation == "non-coreferent"
            else "make exactly one target trigger lexically more similar to the other"
        )
        task = {
            "context_sentences": item["context_sentences"],
            "left_trigger": item["left_trigger"],
            "right_trigger": item["right_trigger"],
            "required_relation_after_edit": relation,
            "intervention": direction,
            "constraints": [
                "edit exactly one target event mention and only its local wording",
                "do not add, remove or change an event fact",
                "keep both target events explicitly present",
                "return string fields item_id, edited_context, edited_left_trigger, "
                "edited_right_trigger and edit_rationale",
                f"copy item_id exactly as {item['item_id']}",
            ],
        }
        requests.append(
            {
                "item_id": item["item_id"],
                "generator": generator,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": json.dumps(task, ensure_ascii=False)},
                ],
                "response_format": "json_object",
            }
        )
    return requests


def validate_generations(plan: Mapping, rows: Iterable[Mapping]) -> dict[str, dict]:
    required = set(plan["generator_output_contract"]["required_fields"])
    expected = {item["item_id"] for item in plan["items"]}
    by_id: dict[str, dict] = {}
    for row in rows:
        if set(row) != required:
            raise ValueError(f"generation fields must be exactly {sorted(required)}")
        item_id = row.get("item_id")
        if not isinstance(item_id, str) or not item_id:
            raise ValueError("generation item_id must be a non-empty string")
        if item_id in by_id:
            raise ValueError(f"duplicate generation item_id: {item_id}")
        for field in required - {"item_id"}:
            if not isinstance(row[field], str) or not row[field].strip():
                raise ValueError(f"{item_id}: {field} must be a non-empty string")
        context = row["edited_context"].casefold()
        for field in ("edited_left_trigger", "edited_right_trigger"):
            if row[field].casefold() not in context:
                raise ValueError(f"{item_id}: {field} is absent from edited_context")
        by_id[item_id] = dict(row)
    if set(by_id) != expected:
        raise ValueError(
            "generation item coverage mismatch: "
            f"missing={len(expected - set(by_id))} extra={len(set(by_id) - expected)}"
        )
    return by_id


def build_review_template(plan: Mapping, generations: Mapping[str, Mapping]) -> list[dict]:
    rows = []
    for item in plan["items"]:
        generated = generations[item["item_id"]]
        rows.append(
            {
                "item_id": item["item_id"],
                "original_context": "\n".join(item["context_sentences"]),
                "original_left_trigger": item["left_trigger"],
                "original_right_trigger": item["right_trigger"],
                "required_relation_after_edit": _expected_relation(item["stratum"]),
                "edited_context": generated["edited_context"],
                "edited_left_trigger": generated["edited_left_trigger"],
                "edited_right_trigger": generated["edited_right_trigger"],
                "edit_rationale": generated["edit_rationale"],
                "label_preserved": None,
                "fluent": None,
                "single_variable_compliant": None,
                "notes": "",
            }
        )
    return rows


def score_reviews(plan: Mapping, reviews: Iterable[Mapping]) -> dict:
    binary_fields = tuple(plan["blind_review"]["binary_fields"])
    expected = {item["item_id"]: item["stratum"] for item in plan["items"]}
    by_id: dict[str, Mapping] = {}
    for row in reviews:
        item_id = row.get("item_id")
        if not isinstance(item_id, str) or not item_id:
            raise ValueError("review item_id must be a non-empty string")
        if item_id in by_id:
            raise ValueError(f"duplicate review item_id: {item_id}")
        for field in binary_fields:
            if type(row.get(field)) is not bool:
                raise ValueError(f"{item_id}: review field {field} must be boolean")
        by_id[item_id] = row
    if set(by_id) != set(expected):
        raise ValueError(
            "review item coverage mismatch: "
            f"missing={len(set(expected) - set(by_id))} "
            f"extra={len(set(by_id) - set(expected))}"
        )

    overall = {
        field: sum(bool(row[field]) for row in by_id.values()) / len(by_id)
        for field in binary_fields
    }
    label_by_stratum = {}
    for stratum in sorted(set(expected.values())):
        ids = [item_id for item_id, value in expected.items() if value == stratum]
        preserved = sum(bool(by_id[item_id]["label_preserved"]) for item_id in ids)
        label_by_stratum[stratum] = preserved / len(ids)
    thresholds = plan["blind_review"]["pass_thresholds"]
    criteria = {
        "label_preserved_overall": overall["label_preserved"]
        >= thresholds["label_preserved_overall"],
        "label_preserved_each_stratum": min(label_by_stratum.values())
        >= thresholds["label_preserved_each_stratum"],
        "fluent_overall": overall["fluent"] >= thresholds["fluent_overall"],
        "single_variable_compliant_overall": overall["single_variable_compliant"]
        >= thresholds["single_variable_compliant_overall"],
    }
    return {
        "schema_version": "r1-v62-c5-generation-audit-report-v1",
        "items": len(by_id),
        "rates": {"overall": overall, "label_preserved_by_stratum": label_by_stratum},
        "thresholds": thresholds,
        "criteria": criteria,
        "status": "pass" if all(criteria.values()) else "failed",
        "classifier_training_authorized": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    requests = subparsers.add_parser("requests")
    requests.add_argument("--plan", required=True, type=Path)
    requests.add_argument("--generator-config", required=True, type=Path)
    requests.add_argument("--output", required=True, type=Path)

    review = subparsers.add_parser("review-template")
    review.add_argument("--plan", required=True, type=Path)
    review.add_argument("--generations", required=True, type=Path)
    review.add_argument("--output", required=True, type=Path)

    score = subparsers.add_parser("score")
    score.add_argument("--plan", required=True, type=Path)
    score.add_argument("--generations", required=True, type=Path)
    score.add_argument("--reviews", required=True, type=Path)
    score.add_argument("--output", required=True, type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    plan = load_plan(args.plan)
    if args.command == "requests":
        generator = _load_object(args.generator_config)
        rows = build_requests(plan, generator)
        _write_jsonl_new(args.output, rows)
        report = {
            "items": len(rows),
            "plan_sha256": sha256_file(args.plan),
            "generator_config_sha256": sha256_file(args.generator_config),
            "requests_sha256": sha256_file(args.output),
        }
    else:
        generations = validate_generations(plan, _load_jsonl(args.generations))
        if args.command == "review-template":
            rows = build_review_template(plan, generations)
            _write_jsonl_new(args.output, rows)
            report = {
                "items": len(rows),
                "plan_sha256": sha256_file(args.plan),
                "generations_sha256": sha256_file(args.generations),
                "review_template_sha256": sha256_file(args.output),
            }
        else:
            scored = score_reviews(plan, _load_jsonl(args.reviews))
            report = {
                **scored,
                "plan_sha256": sha256_file(args.plan),
                "generations_sha256": sha256_file(args.generations),
                "reviews_sha256": sha256_file(args.reviews),
            }
            _write_object_new(args.output, report)
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
