#!/usr/bin/env python
"""Predict participant/place spans for each MAVEN-ERE mention with NuExtract."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

from ekg.core.protocol import load_manifest_ids
from ekg.relations.data.maven_ere import load_maven_ere

TEMPLATE = '{"participant": ["verbatim-string"], "place": ["verbatim-string"]}'


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare_nuextract_model(model, tokenizer) -> int:
    """Apply NuExtract remote-code token IDs for text-only generation."""
    model.img_context_token_id = tokenizer.convert_tokens_to_ids("<IMG_CONTEXT>")
    return tokenizer.convert_tokens_to_ids("<|im_end|>")


def decode_nuextract_responses(tokenizer, generated) -> list[str]:
    """Decode NuExtract continuations; its inputs-embeds path omits prompt IDs."""
    return tokenizer.batch_decode(generated, skip_special_tokens=True)


def parse_roles(
    response: str,
    sentence: str,
    *,
    sentence_start: int,
    trigger_start: int,
) -> dict[str, list[dict]]:
    """Parse NuExtract JSON and locate each filler nearest to the trigger."""
    start, end = response.find("{"), response.rfind("}")
    if start < 0 or end < start:
        raise ValueError(f"model response has no JSON object: {response!r}")
    payload = json.loads(response[start : end + 1])
    unknown = set(payload) - {"participant", "place"}
    if unknown:
        raise ValueError(f"model returned unknown roles: {sorted(unknown)}")
    roles: dict[str, list[dict]] = {}
    for role in ("participant", "place"):
        values = payload.get(role) or []
        if isinstance(values, str):
            values = [values]
        if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
            raise ValueError(f"model returned invalid {role} values")
        fillers = []
        for value in dict.fromkeys(values):
            matches = list(re.finditer(re.escape(value), sentence, re.IGNORECASE))
            if not matches:
                raise ValueError(f"predicted filler is not verbatim: {value!r}")
            distances = [abs(sentence_start + match.start() - trigger_start) for match in matches]
            nearest = min(distances)
            if distances.count(nearest) != 1:
                raise ValueError(f"equidistant filler occurrence is ambiguous: {value!r}")
            match = matches[distances.index(nearest)]
            surface = sentence[match.start() : match.end()]
            fillers.append(
                {
                    "text": surface,
                    "char_start": sentence_start + match.start(),
                    "char_end": sentence_start + match.end(),
                }
            )
        if fillers:
            roles[role] = fillers
    return roles


def _requests(docs) -> list[dict]:
    requests = []
    for doc in docs:
        starts = []
        cursor = 0
        sentences = doc.doc_text.split("\n")
        for sentence in sentences:
            starts.append(cursor)
            cursor += len(sentence) + 1
        for node in doc.nodes:
            span = node.trigger_evidence[0]
            if span.sent_id is None or not 0 <= span.sent_id < len(sentences):
                raise ValueError(f"{node.event_id}: trigger has no valid sentence")
            sentence = sentences[span.sent_id]
            message = (
                "Extract only the participant(s) and place(s) of the specified event.\n"
                f"Event type: {node.event_type}\n"
                f"Event trigger: {node.trigger}\n"
                f"Sentence: {sentence}"
            )
            requests.append(
                {
                    "doc_id": doc.doc_id,
                    "mention_id": node.event_id,
                    "sentence": sentence,
                    "sentence_start": starts[span.sent_id],
                    "trigger_start": span.char_start,
                    "message": f"# Template:\n{TEMPLATE}\n# Context:\n{message}",
                }
            )
    return requests


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ere", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path, nargs="+")
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
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
    requests = _requests(docs)
    if args.limit:
        requests = requests[: args.limit]

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        args.model, trust_remote_code=True, padding_side="left"
    )
    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        trust_remote_code=True,
        torch_dtype=torch.bfloat16,
    ).to("cuda").eval()
    eos_token_id = prepare_nuextract_model(model, tokenizer)
    args.output.mkdir(parents=True)
    output = args.output / "predictions.jsonl"
    with output.open("w", encoding="utf-8") as handle, torch.no_grad():
        for offset in range(0, len(requests), args.batch_size):
            batch = requests[offset : offset + args.batch_size]
            prompts = tokenizer.apply_chat_template(
                [[{"role": "user", "content": row["message"]}] for row in batch],
                tokenize=False,
                add_generation_prompt=True,
            )
            encoded = tokenizer(prompts, return_tensors="pt", padding=True).to("cuda")
            generated = model.generate(
                **encoded,
                pixel_values=None,
                do_sample=False,
                num_beams=1,
                max_new_tokens=128,
                eos_token_id=eos_token_id,
            )
            responses = decode_nuextract_responses(tokenizer, generated)
            for row, response in zip(batch, responses, strict=True):
                roles = parse_roles(
                    response,
                    row["sentence"],
                    sentence_start=row["sentence_start"],
                    trigger_start=row["trigger_start"],
                )
                result = {
                    "doc_id": row["doc_id"],
                    "mention_id": row["mention_id"],
                    "status": "ok" if roles else "empty",
                    "roles": roles,
                }
                handle.write(json.dumps(result, sort_keys=True) + "\n")
            handle.flush()
            done = min(offset + len(batch), len(requests))
            print(f"predicted {done}/{len(requests)}", flush=True)

    try:
        model_revision = subprocess.check_output(
            ["git", "-C", str(args.model), "rev-parse", "HEAD"], text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        model_revision = None
    metadata = {
        "schema_version": "ekg.mention_arguments.v1",
        "status": "complete",
        "command_argv": list(sys.argv),
        "model_id": args.model_id,
        "model_revision": model_revision,
        "documents": len(docs),
        "mentions": len(requests),
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
