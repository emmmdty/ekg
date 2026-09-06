#!/usr/bin/env python
"""Predict mention-local participant/place spans with ModelScope OneKE."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from predict_mention_arguments import _requests, parse_roles

from ekg.core.protocol import load_manifest_ids
from ekg.relations.data.maven_ere import load_maven_ere

_ROLES = {"participant", "place"}
_EMPTY_VALUES = {"", "NAN", "NONE", "NULL"}
_SYSTEM_PROMPT = (
    "<<SYS>>\nYou are a helpful assistant. You perform faithful information "
    "extraction.\n<</SYS>>\n\n"
)
ONEKE_FILES = {
    "config.json": (676, "c490b4eebd65fcc5b9af955344c9b4f84114b8ecfa56e0ace9cbff33a3c89024"),
    "configuration.json": (
        65,
        "084e63482865b26a7f4fd043a1bfb67b755707c7aa32d302d07cc6a3a4d0b208",
    ),
    "pytorch_model-00001-of-00003.bin": (
        9_940_832_938,
        "9f1d0e5973b9c428bb71334c22abd72592b0cfd73d8242bb76b7e284a2e920c0",
    ),
    "pytorch_model-00002-of-00003.bin": (
        9_867_476_673,
        "81f9c0b70774391a9c0de879a1098977ffd336364b7a1ec6a232a9cbb02b274d",
    ),
    "pytorch_model-00003-of-00003.bin": (
        6_700_645_527,
        "b4ecd8ad32be39f367cd48070563e9bfd038efac4072487c9dbe7803409a3c8b",
    ),
    "pytorch_model.bin.index.json": (
        29_894,
        "53210b932f39dfbcb706e7c1285a8aa26fc8c570f4415108146bcd4999cca961",
    ),
    "special_tokens_map.json": (
        435,
        "dfd7f38bbbe1f22c1f6e05db6241ad82176a9765d91b51b3fee3e3835e6ac75f",
    ),
    "tokenizer.model": (
        844_403,
        "a3b8844863b200dfcca971db228e96ce388290dfcf72c15d7a9d2f604bac787c",
    ),
    "tokenizer_config.json": (
        766,
        "305a57cf5eca7b87705ffe64d9c0ccb23ff09e85342597227ac4207953f7fea6",
    ),
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_model_snapshot(
    root: Path, expected: dict[str, tuple[int, str]] = ONEKE_FILES
) -> dict[str, dict[str, int | str]]:
    records = {}
    for relative, (size, digest) in expected.items():
        path = root / relative
        if not path.is_file() or path.stat().st_size != size:
            raise ValueError(f"model file size mismatch: {relative}")
        actual = _sha256(path)
        if actual != digest:
            raise ValueError(f"model file hash mismatch: {relative}")
        records[relative] = {"bytes": size, "sha256": actual}
    return records


def one_ke_prompt(row: dict) -> str:
    instruction = {
        "instruction": (
            "You are an expert in event argument extraction. Extract arguments only "
            f"for the event triggered by {row['trigger']!r}. Return participant and "
            "place values exactly as written in the input. Return NAN or an empty "
            "dictionary when absent. Respond with one parseable JSON value."
        ),
        "schema": [
            {
                "event_type": row["event_type"],
                "trigger": row["trigger"],
                "arguments": ["participant", "place"],
            }
        ],
        "input": row["sentence"],
    }
    return f"[INST] {_SYSTEM_PROMPT}{json.dumps(instruction, ensure_ascii=False)}[/INST]"


def _json_value(response: str):
    positions = [position for token in ("{", "[") if (position := response.find(token)) >= 0]
    if not positions:
        raise ValueError(f"model response has no JSON value: {response!r}")
    start = min(positions)
    decoder = json.JSONDecoder()
    payload, _ = decoder.raw_decode(response[start:])
    return payload


def _role_values(arguments: dict) -> dict[str, list[str]]:
    roles: dict[str, list[str]] = {}
    for raw_role, raw_values in arguments.items():
        role = str(raw_role).casefold()
        if role not in _ROLES:
            raise ValueError(f"model returned unknown role: {raw_role!r}")
        if raw_values is None or (
            isinstance(raw_values, str) and raw_values.upper() in _EMPTY_VALUES
        ):
            continue
        values = raw_values if isinstance(raw_values, list) else [raw_values]
        if any(not isinstance(value, str) for value in values):
            raise ValueError(f"model returned invalid {raw_role} values")
        kept = [value for value in values if value.upper() not in _EMPTY_VALUES]
        if kept:
            roles[role] = kept
    return roles


def normalize_oneke_response(response: str, *, trigger: str) -> dict[str, list[str]]:
    """Normalize OneKE direct-role or event-list JSON without inventing missing values."""
    payload = _json_value(response)
    if isinstance(payload, dict):
        keys = set(map(str.casefold, payload))
        event_fields = {"arguments", "event_type", "event_trigger", "trigger"}
        if keys <= _ROLES or not keys & event_fields:
            return _role_values(payload)

    candidates = payload if isinstance(payload, list) else [payload]
    if not all(isinstance(candidate, dict) for candidate in candidates):
        raise ValueError("OneKE event response must contain JSON objects")
    if not candidates:
        return {}
    matching = [
        candidate
        for candidate in candidates
        if str(candidate.get("trigger", candidate.get("event_trigger", ""))).casefold()
        == trigger.casefold()
    ]
    selected = matching if matching else candidates
    if len(selected) != 1:
        raise ValueError(f"OneKE returned {len(selected)} ambiguous events for trigger {trigger!r}")
    arguments = selected[0].get("arguments")
    if arguments is None:
        direct = {
            key: value
            for key, value in selected[0].items()
            if str(key).casefold() in _ROLES
        }
        arguments = direct
    if not isinstance(arguments, dict):
        raise ValueError("OneKE event arguments are not a JSON object")
    return _role_values(arguments)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ere", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path, nargs="+")
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--num-shards", type=int, default=1)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    if not 1 <= args.batch_size:
        parser.error("batch size must be positive")
    if not 1 <= args.num_shards or not 0 <= args.shard_index < args.num_shards:
        parser.error("invalid shard index/count")
    if args.output.exists() and any(args.output.iterdir()):
        parser.error(f"output directory is not empty: {args.output}")

    wanted = [doc_id for manifest in args.manifest for doc_id in load_manifest_ids(manifest)]
    if len(wanted) != len(set(wanted)):
        parser.error("manifests overlap or contain duplicate document IDs")
    by_id = {doc.doc_id: doc for doc in load_maven_ere(args.ere)}
    missing = set(wanted) - by_id.keys()
    if missing:
        parser.error(f"manifest documents missing from ERE source: {len(missing)}")
    docs = [by_id[doc_id] for doc_id in wanted]
    all_requests = _requests(docs)
    requests = all_requests[args.shard_index :: args.num_shards]
    if args.limit:
        requests = requests[: args.limit]

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    model_files = validate_model_snapshot(args.model)
    tokenizer = AutoTokenizer.from_pretrained(
        args.model, trust_remote_code=True, local_files_only=True, padding_side="left"
    )
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = tokenizer.eos_token_id
    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        llm_int8_threshold=6.0,
        llm_int8_has_fp16_weight=False,
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
    )
    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        device_map="auto",
        quantization_config=quantization,
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
        local_files_only=True,
    ).eval()

    args.output.mkdir(parents=True)
    output = args.output / "predictions.jsonl"
    with output.open("w", encoding="utf-8") as handle, torch.no_grad():
        for offset in range(0, len(requests), args.batch_size):
            batch = requests[offset : offset + args.batch_size]
            encoded = tokenizer(
                [one_ke_prompt(row) for row in batch], return_tensors="pt", padding=True
            ).to(model.device)
            generated = model.generate(
                **encoded,
                do_sample=False,
                num_beams=1,
                max_new_tokens=128,
            )
            responses = tokenizer.batch_decode(
                generated[:, encoded.input_ids.shape[1] :], skip_special_tokens=True
            )
            for row, response in zip(batch, responses, strict=True):
                normalized = normalize_oneke_response(response, trigger=row["trigger"])
                roles = parse_roles(
                    json.dumps(normalized),
                    row["sentence"],
                    sentence_start=row["sentence_start"],
                    trigger_start=row["trigger_start"],
                )
                handle.write(
                    json.dumps(
                        {
                            "doc_id": row["doc_id"],
                            "mention_id": row["mention_id"],
                            "status": "ok" if roles else "empty",
                            "roles": roles,
                            "raw_response": response,
                        },
                        sort_keys=True,
                    )
                    + "\n"
                )
            handle.flush()
            done = min(offset + len(batch), len(requests))
            print(f"predicted shard {args.shard_index}: {done}/{len(requests)}", flush=True)

    metadata = {
        "schema_version": "ekg.mention_arguments.v1",
        "status": "complete",
        "command_argv": list(sys.argv),
        "backend": "oneke_4bit_nf4",
        "model_id": args.model_id,
        "model_files": model_files,
        "documents_in_manifests": len(docs),
        "mentions_in_manifests": len(all_requests),
        "mentions": len(requests),
        "num_shards": args.num_shards,
        "shard_index": args.shard_index,
        "source_sha256": _sha256(args.ere),
        "manifest_sha256": {str(path): _sha256(path) for path in args.manifest},
        "predictions_sha256": _sha256(output),
        "final_valid_accessed": False,
    }
    (args.output / "run_metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
