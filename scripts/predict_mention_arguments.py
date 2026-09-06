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
_LOCAL_AUTO_CLASSES = {"AutoModel", "AutoModelForCausalLM"}
QWEN3_FILES = {
    "config.json": (728, "f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30"),
    "generation_config.json": (
        239,
        "2325da0f15bb848e018c5ae071b7943332e9f871d6b60e2ed22ca97d4cb993d2",
    ),
    "model-00001-of-00005.safetensors": (
        3_996_250_744,
        "31d6a825ae35f11fb85b195b4c42c146c051e446433125a215336abdf95cbf5f",
    ),
    "model-00002-of-00005.safetensors": (
        3_993_160_032,
        "5991236cea6fe21f3d43cab0f0e84448734fbbe0789816202989f2ddc9d18282",
    ),
    "model-00003-of-00005.safetensors": (
        3_959_604_768,
        "c5185c4794be2d8a9784d5753c9922db38df478ce11f9ed0b415b7304d896836",
    ),
    "model-00004-of-00005.safetensors": (
        3_187_841_392,
        "b5ee7de71fbf17db3d5704e0c8f2bc7d005ca9e1d7ca2aeb19827b0cfcaa917a",
    ),
    "model-00005-of-00005.safetensors": (
        1_244_659_840,
        "20c2d6366ab85c90786ccdd829cd2b9e7d30ef3b2ebbb998280e7e4014b542ff",
    ),
    "model.safetensors.index.json": (
        32_878,
        "f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc",
    ),
    "tokenizer.json": (
        11_422_654,
        "aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4",
    ),
    "tokenizer_config.json": (
        9_732,
        "d5d09f07b48c3086c508b30d1c9114bd1189145b74e982a265350c923acd8101",
    ),
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_qwen3_snapshot(root: Path) -> dict[str, dict[str, int | str]]:
    files = {}
    for relative, (size, expected) in QWEN3_FILES.items():
        path = root / relative
        if not path.is_file() or path.stat().st_size != size:
            raise ValueError(f"Qwen3 model file size mismatch: {relative}")
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            while chunk := handle.read(8 * 1024 * 1024):
                digest.update(chunk)
        actual = digest.hexdigest()
        if actual != expected:
            raise ValueError(f"Qwen3 model file hash mismatch: {relative}")
        files[relative] = {"bytes": size, "sha256": actual}
    return files


def prepare_nuextract_model(model, tokenizer) -> int:
    """Apply NuExtract remote-code token IDs for text-only generation."""
    model.img_context_token_id = tokenizer.convert_tokens_to_ids("<IMG_CONTEXT>")
    return tokenizer.convert_tokens_to_ids("<|im_end|>")


def decode_nuextract_responses(tokenizer, generated) -> list[str]:
    """Decode NuExtract continuations; its inputs-embeds path omits prompt IDs."""
    return tokenizer.batch_decode(generated, skip_special_tokens=True)


def qwen_argument_message(row: dict) -> str:
    """Describe the strict schema without a literal filler that can be copied."""
    return (
        "Extract only the participant(s) and place(s) of the specified event. "
        "Every returned value must be an exact substring of the sentence. Return exactly "
        "one JSON object with arrays under participant and place; use an empty array when "
        "the role is absent. Do not return schema descriptions or placeholder values.\n"
        f"Event type: {row['event_type']}\n"
        f"Event trigger: {row['trigger']}\n"
        f"Sentence: {row['sentence']}\n"
        'Output schema: {"participant": [], "place": []}'
    )


def localize_dynamic_auto_map(config, *, model_repo: str) -> None:
    """Force NuExtract's downloaded remote code to resolve from the local snapshot."""
    auto_map = getattr(config, "auto_map", {})
    for key in _LOCAL_AUTO_CLASSES:
        reference = auto_map.get(key)
        if not isinstance(reference, str) or "--" not in reference:
            continue
        repo, local_reference = reference.split("--", 1)
        if repo != model_repo:
            raise ValueError(f"unexpected dynamic-code repository for {key}: {repo}")
        auto_map[key] = local_reference


def ensure_generation_mixin(language_model, generation_mixin) -> None:
    """Restore the generation API removed from PreTrainedModel in Transformers 4.50+."""
    if hasattr(language_model, "generate"):
        return
    patched_class = type(
        f"{type(language_model).__name__}WithGenerationMixin",
        (type(language_model), generation_mixin),
        {},
    )
    language_model.__class__ = patched_class


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
                    "event_type": node.event_type,
                    "trigger": node.trigger,
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
    parser.add_argument("--backend", choices=("nuextract", "qwen3"), default="nuextract")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--batch-size", type=int, default=16)
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
    from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer

    model_files = None
    if args.backend == "qwen3":
        model_files = validate_qwen3_snapshot(args.model)
        tokenizer = AutoTokenizer.from_pretrained(
            args.model, padding_side="left", local_files_only=True
        )
        model = AutoModelForCausalLM.from_pretrained(
            args.model, torch_dtype=torch.bfloat16, local_files_only=True
        ).to("cuda").eval()
        eos_token_id = tokenizer.eos_token_id
    else:
        tokenizer = AutoTokenizer.from_pretrained(
            args.model,
            trust_remote_code=True,
            padding_side="left",
            local_files_only=True,
        )
        model_repo = args.model_id.split("@", 1)[0]
        config = AutoConfig.from_pretrained(
            args.model, trust_remote_code=True, local_files_only=True
        )
        localize_dynamic_auto_map(config, model_repo=model_repo)
        model = AutoModelForCausalLM.from_pretrained(
            args.model,
            config=config,
            trust_remote_code=True,
            torch_dtype=torch.bfloat16,
            local_files_only=True,
        ).to("cuda").eval()
        from transformers.generation import GenerationMixin

        ensure_generation_mixin(model.language_model, GenerationMixin)
        eos_token_id = prepare_nuextract_model(model, tokenizer)
    args.output.mkdir(parents=True)
    output = args.output / "predictions.jsonl"
    with output.open("w", encoding="utf-8") as handle, torch.no_grad():
        for offset in range(0, len(requests), args.batch_size):
            batch = requests[offset : offset + args.batch_size]
            conversations = [
                [
                    {
                        "role": "user",
                        "content": (
                            qwen_argument_message(row)
                            if args.backend == "qwen3"
                            else row["message"]
                        ),
                    }
                ]
                for row in batch
            ]
            template_kwargs = {"enable_thinking": False} if args.backend == "qwen3" else {}
            prompts = tokenizer.apply_chat_template(
                conversations,
                tokenize=False,
                add_generation_prompt=True,
                **template_kwargs,
            )
            encoded = tokenizer(prompts, return_tensors="pt", padding=True).to("cuda")
            generation_kwargs = {"pixel_values": None} if args.backend == "nuextract" else {}
            generated = model.generate(
                **encoded,
                **generation_kwargs,
                do_sample=False,
                num_beams=1,
                max_new_tokens=128,
                eos_token_id=eos_token_id,
            )
            if args.backend == "qwen3":
                generated = generated[:, encoded.input_ids.shape[1] :]
            responses = decode_nuextract_responses(tokenizer, generated)
            for row, response in zip(batch, responses, strict=True):
                try:
                    roles = parse_roles(
                        response,
                        row["sentence"],
                        sentence_start=row["sentence_start"],
                        trigger_start=row["trigger_start"],
                    )
                except ValueError as exc:
                    raise ValueError(
                        f"invalid response for {row['mention_id']}: {response!r}"
                    ) from exc
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
        "backend": args.backend,
        "model_id": args.model_id,
        "model_files": model_files,
        "model_revision": model_revision,
        "documents": len(docs),
        "mentions": len(requests),
        "mentions_in_manifests": len(all_requests),
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
