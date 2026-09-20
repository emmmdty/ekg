#!/usr/bin/env python
"""Run the frozen C5 generation audit once on a pinned local Qwen3 snapshot.

The runner is deliberately strict: it preserves every raw response, accepts
only a bare JSON object with the frozen five fields, never repairs a response,
and publishes parsed generations only when all 100 items validate.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Iterable, Mapping
from pathlib import Path

from ekg.core.stage_bundle import sha256_file

REQUEST_FIELDS = {"item_id", "generator", "messages", "response_format"}
OUTPUT_FIELDS = {
    "item_id",
    "edited_context",
    "edited_left_trigger",
    "edited_right_trigger",
    "edit_rationale",
}


def load_requests(path: Path) -> list[dict]:
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line:
            raise ValueError(f"{path}:{line_number}: blank JSONL row")
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"{path}:{line_number}: request must be a JSON object")
        rows.append(row)
    if not rows:
        raise ValueError(f"{path} has no requests")
    return rows


def validate_request_bindings(
    rows: Iterable[Mapping], generator: Mapping, *, expected_items: int = 100
) -> list[dict]:
    bound = []
    seen = set()
    for row in rows:
        if set(row) != REQUEST_FIELDS:
            raise ValueError(f"request fields must be exactly {sorted(REQUEST_FIELDS)}")
        item_id = row["item_id"]
        if not isinstance(item_id, str) or not item_id:
            raise ValueError("request item_id must be a non-empty string")
        if item_id in seen:
            raise ValueError(f"duplicate request item_id: {item_id}")
        seen.add(item_id)
        if row["generator"] != generator:
            raise ValueError(f"{item_id}: request generator differs from frozen config")
        messages = row["messages"]
        if (
            not isinstance(messages, list)
            or [message.get("role") for message in messages] != ["system", "user"]
            or any(not isinstance(message.get("content"), str) for message in messages)
        ):
            raise ValueError(f"{item_id}: request messages must be system then user")
        if row["response_format"] != "json_object":
            raise ValueError(f"{item_id}: response_format must be json_object")
        bound.append(dict(row))
    if len(bound) != expected_items:
        raise ValueError(f"expected {expected_items} requests, got {len(bound)}")
    return bound


def parse_strict_response(item_id: str, response: str) -> dict:
    """Accept one bare JSON object; markdown fences or salvage are forbidden."""
    try:
        payload = json.loads(response.strip())
    except json.JSONDecodeError as exc:
        raise ValueError(f"{item_id}: response is not one bare JSON object") from exc
    if not isinstance(payload, dict) or set(payload) != OUTPUT_FIELDS:
        raise ValueError(f"{item_id}: response fields must be exactly {sorted(OUTPUT_FIELDS)}")
    if payload["item_id"] != item_id:
        raise ValueError(f"{item_id}: response item_id mismatch")
    return payload


def _write_jsonl_new(path: Path, rows: Iterable[Mapping]) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(
            json.dumps(dict(row), ensure_ascii=False, sort_keys=True) + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--requests", required=True, type=Path)
    parser.add_argument("--generator-config", required=True, type=Path)
    parser.add_argument("--model-path", required=True, type=Path)
    parser.add_argument("--raw-output", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    for path in (args.raw_output, args.output, args.report):
        if path.exists():
            raise FileExistsError(f"refusing to overwrite: {path}")

    from predict_mention_arguments import validate_qwen3_snapshot
    from run_c5_generation_audit import (
        _load_object,
        _write_object_new,
        load_plan,
        validate_generations,
        validate_generator_config,
    )

    generator = validate_generator_config(_load_object(args.generator_config))
    plan = load_plan(args.plan)
    requests = validate_request_bindings(load_requests(args.requests), generator)
    if [row["item_id"] for row in requests] != [item["item_id"] for item in plan["items"]]:
        raise ValueError("request order or item IDs differ from the frozen audit plan")
    model_files = validate_qwen3_snapshot(args.model_path)

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    if not torch.cuda.is_available():
        raise RuntimeError("C5 generation audit requires CUDA; local CPU inference is forbidden")
    decoding = generator["decoding"]
    torch.manual_seed(decoding["seed"])
    torch.cuda.manual_seed_all(decoding["seed"])
    tokenizer = AutoTokenizer.from_pretrained(str(args.model_path), local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(
        str(args.model_path),
        local_files_only=True,
        torch_dtype=torch.bfloat16,
        low_cpu_mem_usage=True,
    ).to("cuda").eval()

    args.raw_output.parent.mkdir(parents=True, exist_ok=True)
    parsed = []
    errors = []
    with args.raw_output.open("x", encoding="utf-8") as raw_handle, torch.no_grad():
        for index, request in enumerate(requests, 1):
            encoded = tokenizer.apply_chat_template(
                request["messages"],
                add_generation_prompt=True,
                tokenize=True,
                return_dict=True,
                return_tensors="pt",
                enable_thinking=decoding["enable_thinking"],
            ).to("cuda")
            generate_kwargs = {
                "do_sample": decoding["do_sample"],
                "max_new_tokens": decoding["max_new_tokens"],
                "pad_token_id": tokenizer.eos_token_id,
            }
            if decoding["do_sample"]:
                generate_kwargs.update(
                    temperature=decoding["temperature"],
                    top_p=decoding["top_p"],
                )
            generated = model.generate(**encoded, **generate_kwargs)
            continuation = generated[0, encoded["input_ids"].shape[-1] :]
            response = tokenizer.decode(continuation, skip_special_tokens=True)
            raw_row = {
                "item_id": request["item_id"],
                "response": response,
                "prompt_tokens": int(encoded["input_ids"].shape[-1]),
                "generated_tokens": int(continuation.shape[-1]),
            }
            raw_handle.write(json.dumps(raw_row, ensure_ascii=False, sort_keys=True) + "\n")
            raw_handle.flush()
            try:
                parsed.append(parse_strict_response(request["item_id"], response))
            except ValueError as exc:
                errors.append({"item_id": request["item_id"], "error": str(exc)})
            print(f"generated {index}/{len(requests)}", flush=True)

    report = {
        "schema_version": "r1-v62-c5-generation-run-report-v1",
        "status": "failed_format" if errors else "complete",
        "items_requested": len(requests),
        "items_parsed": len(parsed),
        "errors": errors,
        "classifier_training_authorized": False,
        "hashes": {
            "plan": sha256_file(args.plan),
            "requests": sha256_file(args.requests),
            "generator_config": sha256_file(args.generator_config),
            "raw_output": sha256_file(args.raw_output),
        },
        "model_files": model_files,
    }
    if not errors:
        validated = validate_generations(plan, parsed)
        _write_jsonl_new(args.output, [validated[item["item_id"]] for item in plan["items"]])
        report["hashes"]["output"] = sha256_file(args.output)
    _write_object_new(args.report, report)
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
