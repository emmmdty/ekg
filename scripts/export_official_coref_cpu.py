#!/usr/bin/env python
"""Read the frozen official joint model on remote CPU; require exact cluster parity."""

from __future__ import annotations

import argparse
import importlib
import json
import math
import os
import subprocess
import sys
from pathlib import Path

from ekg.core.protocol import load_manifest_ids
from ekg.core.stage_bundle import model_content_digest, sha256_file


def validate_cache_document(row):
    ids, probabilities, logits = row["mentions"], row["probabilities"], row["pair_logits"]
    if len(ids) != len(set(ids)) or len(probabilities) != len(ids) or len(logits) != len(ids):
        raise ValueError("mention/probability population mismatch")
    for i, (values, scores) in enumerate(zip(probabilities, logits, strict=True)):
        if (len(values) != i + 1 or not all(math.isfinite(v) and 0 <= v <= 1 for v in values)
                or not math.isclose(sum(values), 1.0, abs_tol=1e-5)):
            raise ValueError("invalid or incomplete antecedent probability row")
        if len(scores) != i or not all(math.isfinite(v) for v in scores):
            raise ValueError("invalid or incomplete logit row")
        all_scores = [*scores, 0.0]
        maximum = max(all_scores)
        unnormalized = [math.exp(value - maximum) for value in all_scores]
        expected = [value / sum(unnormalized) for value in unnormalized]
        if any(not math.isclose(a, b, rel_tol=1e-4, abs_tol=1e-6)
               for a, b in zip(values, expected, strict=True)):
            raise ValueError("probabilities differ from original logits/dummy")


def require_parity(original, clusters, mentions):
    def normalized(groups):
        seen = set()
        for group in groups:
            if (len(group) != len(set(group)) or not set(group) <= set(mentions)
                    or seen.intersection(group)):
                raise ValueError("unknown or duplicate cluster mention")
            seen.update(group)
        return sorted(sorted(group) for group in groups if len(group) > 1)

    if normalized(original["coreference"]) != normalized(clusters):
        raise ValueError(f"strong-anchor cluster parity failed: {original['id']}")


def validate_records(records, ids):
    if any("events" in row or "coreference" in row or "event_mentions" not in row
           for row in records):
        raise ValueError("official CPU export requires unlabeled test shape")
    by_id = {row["id"]: row for row in records}
    if len(by_id) != len(records) or set(by_id) != ids:
        raise ValueError("input/manifest document coverage mismatch")
    return by_id


def input_population(records):
    from ekg.relations.maven_ere_official import candidate_population_digest

    # The existing digest reads spans from `events`; singleton wrappers supply
    # only IDs/spans for enumeration and are never passed to the model.
    structural = {doc_id: {"events": [{"mention": [mention]}
                                      for mention in row["event_mentions"]],
                           "TIMEX": row["TIMEX"]} for doc_id, row in records.items()}
    digest, counts = candidate_population_digest(structural)
    return {"candidate_id_digest": digest, **counts}


def require_smoke(root, config_sha):
    status = json.loads((root / "status.json").read_text())
    if status["status"] != "complete" or status["config_sha256"] != config_sha:
        raise ValueError("matching completed CPU smoke required")
    if not status["artifact_sha256"]:
        raise ValueError("CPU smoke has no artifacts")
    for relative, expected in status["artifact_sha256"].items():
        if sha256_file(root / relative) != expected:
            raise ValueError("CPU smoke artifact hash drift")


def preflight(config, config_sha, scope):
    if (config["schema_version"] != "ekg.c5_official_cpu_cache.v1"
            or config["device"] != "cpu" or config["diagnostic_only"] is not True
            or config["final_valid_accessed"] is not False or config["seed"] != 13
            or config["cpu_threads"] != 4 or config["batch_size"] != 8
            or config["max_length"] != 256):
        raise ValueError("frozen CPU diagnostic configuration drift")
    if sha256_file(Path(__file__)) != config["entrypoint_sha256"]:
        raise ValueError("CPU entrypoint hash drift")
    if sha256_file(Path(config["p1_protocol"])) != config["p1_sha256"]:
        raise ValueError("current P1 binding drift")
    for path, expected in config["input_sha256"].items():
        if sha256_file(Path(path)) != expected:
            raise ValueError(f"frozen input hash drift: {path}")
    if model_content_digest(Path(config["pretrained"])) != config["pretrained_digest"]:
        raise ValueError("pretrained content identity drift")
    manifest = json.loads(Path(config["manifest"]).read_text())
    if manifest["dataset"] != "maven_ere" or manifest["split_role"] != "internal-dev":
        raise ValueError("CPU cache is internal-dev only")
    ids = set(load_manifest_ids(Path(config["manifest"])))
    path = Path(config["data_dir"]) / "test.jsonl"
    records = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    by_id = validate_records(records, ids)
    population = input_population(by_id)
    if population["candidate_id_digest"] != config["candidate_digest"]:
        raise ValueError("frozen candidate digest drift")
    output = Path(config["output"]) / scope
    if output.exists():
        raise FileExistsError(output)
    if scope == "full":
        require_smoke(Path(config["output"]) / "smoke", config_sha)
    return by_id, population


def execute(config, config_sha, scope, records, population):
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "-1":
        raise ValueError("explicit CUDA_VISIBLE_DEVICES=-1 required for remote CPU export")
    import torch
    from transformers import RobertaTokenizer

    if torch.cuda.is_available():
        raise ValueError("CUDA must be invisible")
    torch.set_num_threads(config["cpu_threads"])
    torch.set_num_interop_threads(1)
    torch.manual_seed(config["seed"])
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(Path(config["source_root"]).resolve()))
    data_module = importlib.import_module("src.data")
    model_module = importlib.import_module("src.model")
    utils_module = importlib.import_module("src.utils")
    dump_module = importlib.import_module("src.dump_result")
    for name, module in (("data", data_module), ("model", model_module),
                         ("utils", utils_module), ("dump_result", dump_module)):
        if Path(module.__file__).resolve() != (
                Path(config["source_root"]) / "src" / f"{name}.py").resolve():
            raise ValueError("imported module is outside the frozen official source")
    tokenizer = RobertaTokenizer.from_pretrained(config["pretrained"], local_files_only=True)
    model = model_module.Model(len(tokenizer), model_name=config["pretrained"])
    checkpoint = torch.load(config["checkpoint"], map_location="cpu", weights_only=False)
    model.load_state_dict(checkpoint["model"], strict=True)
    del checkpoint
    model.eval()
    if any(parameter.device.type != "cpu" for parameter in model.parameters()):
        raise ValueError("model must remain entirely on CPU")
    dataloader = data_module.get_dataloader(
        tokenizer, "test", data_dir=config["data_dir"], max_length=config["max_length"],
        batch_size=config["batch_size"], shuffle=False, ignore_nonetype=False)
    originals = {row["id"]: row for row in
                 map(json.loads, Path(config["original_predictions"]).read_text().splitlines())}
    if set(originals) != set(records):
        raise ValueError("anchor prediction document population mismatch")
    output = Path(config["output"]) / scope
    output.mkdir(parents=True, exist_ok=False)
    status = {"status": "running", "config_sha256": config_sha, "scope": scope,
              "pid": os.getpid(), "device": "cpu", "cpu_threads": config["cpu_threads"],
              "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()}
    (output / "status.json").write_text(json.dumps(status, indent=2))
    captured = []
    hook = model.coref_scorer.score.register_forward_hook(
        lambda module, inputs, result: captured.append(result.detach().flatten().tolist()))
    seen = set()
    try:
        with (output / "scores.jsonl").open("x") as cache, (
                output / "predictions.jsonl").open("x") as predictions, torch.no_grad():
            for batch_index, batch in enumerate(dataloader):
                captured.clear()
                encoder_inputs = {key: batch[key] for key in
                                  ("input_ids", "attention_mask", "event_spans", "splits")}
                embeds = model.encoder(encoder_inputs)
                probabilities = model.coref_scorer(embeds, batch["events_idx"])
                raw_index = 0
                for doc_id, probability in zip(batch["doc_id"], probabilities, strict=True):
                    events = dump_module.CorefDocument(records[doc_id]).events
                    ids = [event["id"] for event in events]
                    logits = [[]]
                    if len(ids) > 1:
                        values = captured[raw_index]
                        raw_index += 1
                        position = 0
                        for n_antecedents in range(1, len(ids)):
                            logits.append(values[position:position + n_antecedents])
                            position += n_antecedents
                        if position != len(values):
                            raise ValueError("original scorer logit coverage mismatch")
                    row = {"id": doc_id, "mentions": ids, "pair_logits": logits,
                           "probabilities": [probability[i, :i + 1].tolist()
                                             for i in range(len(ids))]}
                    validate_cache_document(row)
                    clusters, _ = utils_module.get_predicted_clusters(probability)
                    clusters = [[ids[index] for index in group] for group in clusters]
                    require_parity(originals[doc_id], clusters, ids)
                    if doc_id in seen:
                        raise ValueError("duplicate exported document")
                    seen.add(doc_id)
                    cache.write(json.dumps(row, allow_nan=False) + "\n")
                    prediction = {**originals[doc_id], "coreference": clusters}
                    predictions.write(json.dumps(prediction) + "\n")
                if raw_index != len(captured):
                    raise ValueError("unmatched original scorer outputs")
                print(f"batch {batch_index + 1}: {len(seen)} documents, exact parity", flush=True)
                if scope == "smoke" and batch_index + 1 == config["smoke_batches"]:
                    break
        if scope == "full" and seen != set(records):
            raise ValueError("full cache document coverage mismatch")
        metadata = {"diagnostic_only": True, "device": "cpu", "cuda_visible_devices": "-1",
                    "documents": len(seen), "scope": scope, "seed": 13,
                    "full_input_population": population, "config_sha256": config_sha,
                    "checkpoint_location": str(Path(config["checkpoint"]).resolve()),
                    "checkpoint_sha256": config["input_sha256"][config["checkpoint"]],
                    "input_sha256": config["input_sha256"],
                    "entrypoint_sha256": sha256_file(Path(__file__)),
                    "parity": "exact non-singleton clusters; no changed decoder or threshold",
                    "candidate_policy": "all event antecedents and dummy; no type filtering",
                    "relation_fields": "copied from frozen prediction; no relation forward",
                    "final_valid_accessed": False, "optimizer_steps": 0}
        (output / "metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True))
        status.update(status="complete", documents=len(seen), artifact_sha256={
            name: sha256_file(output / name) for name in
            ("scores.jsonl", "predictions.jsonl", "metadata.json")})
    except Exception as error:
        status.update(status="failed", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        hook.remove()
        (output / "status.json").write_text(json.dumps(status, indent=2, sort_keys=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--scope", choices=("smoke", "full"), required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    config_sha = sha256_file(args.config)
    records, population = preflight(config, config_sha, args.scope)
    print(json.dumps({"preflight": "pass", "scope": args.scope,
                      "population": population}), flush=True)
    if args.execute:
        execute(config, config_sha, args.scope, records, population)


if __name__ == "__main__":
    main()
