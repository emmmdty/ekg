#!/usr/bin/env python
"""Prepare fixed ERGO internal-dev inputs without gold, encoder or predictions."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

from ekg.core.protocol import load_manifest_ids
from ekg.core.stage_bundle import sha256_file
from ekg.relations.ergo_adapter import longformer_inputs, marked_document, native_pair_features
from ekg.relations.maven_ere_official import candidate_population_digest, records_by_id


def project_unlabeled(raw):
    if set(raw) != {"id", "title", "sentences", "tokens", "event_mentions", "TIMEX"}:
        raise ValueError("frozen unlabeled test-shaped source required")
    return {"id": raw["id"], "tokens": raw["tokens"], **{
        key: [{k: item[k] for k in ("id", "sent_id", "offset")} for item in raw[key]]
        for key in ("event_mentions", "TIMEX")}}


def pack_feature(raw, encoded, *, start, end, length):
    text, mids = marked_document(raw)
    positions = [i for i, value in enumerate(encoded) if value == start]
    if len(positions) != len(mids) or encoded.count(end) != len(mids):
        raise ValueError(f"endpoint marker loss: {raw['id']}")
    if len(encoded) > length:
        raise ValueError(f"overlong complete input: {raw['id']}")
    marker_positions = dict(zip(mids, positions, strict=True))
    pairs = native_pair_features(raw, marker_positions)
    feature = {"id": raw["id"], "mention_ids": mids,
               **longformer_inputs(encoded, padded_length=length),
               "t1_pos": pairs["t1_pos"], "t2_pos": pairs["t2_pos"]}
    witness = {"id": raw["id"], "nonpad_tokens": len(encoded), "mentions": len(mids),
               "pairs": len(pairs["pair_ids"]), "marker_positions": marker_positions,
               "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
               "input_ids_sha256": hashlib.sha256(
                   json.dumps(encoded, separators=(",", ":")).encode()).hexdigest()}
    return feature, witness


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    if (os.environ.get("CUDA_VISIBLE_DEVICES") != "-1"
            or config["schema_version"] != "ekg.ergo_unlabeled_features.v1"
            or config["split"] != "internal-dev" or config["max_length"] != 4096
            or config["global_attention_policy"] != "BOS_EOS_from_released_cache"
            or config["final_valid_accessed"] is not False):
        raise ValueError("frozen CPU-only internal-dev input scope required")
    for path, expected in config["input_sha256"].items():
        if sha256_file(Path(path)) != expected:
            raise ValueError(f"input/code drift: {path}")
    output = Path(config["output"])
    if output.exists():
        raise FileExistsError(output)
    ids = load_manifest_ids(Path(config["manifest"]))
    records = records_by_id(
        (project_unlabeled(json.loads(line)) for line in
         Path(config["source"]).read_text().splitlines()),
        source="unlabeled internal-dev")
    if set(records) != set(ids):
        raise ValueError("complete manifest coverage required")
    digest, population = candidate_population_digest({
        doc_id: {"events": [{"mention": [m]} for m in raw["event_mentions"]], "TIMEX": raw["TIMEX"]}
        for doc_id, raw in records.items()})
    if digest != config["candidate_digest"] or population != config["expected_population"]:
        raise ValueError("native complete candidate identity drift")
    from transformers import LongformerTokenizerFast

    assets = Path(config["tokenizer"])
    if {p.name for p in assets.iterdir()} != set(config["tokenizer_files"]):
        raise ValueError("tokenizer file-set drift")
    tokenizer = LongformerTokenizerFast.from_pretrained(assets, local_files_only=True)
    if (tokenizer.add_tokens(["<t>", "</t>"]) != 2 or len(tokenizer) != 50267
            or tokenizer.pad_token_id != 1):
        raise ValueError("original marker vocabulary drift")
    start, end = tokenizer.convert_tokens_to_ids(["<t>", "</t>"])
    output.mkdir(parents=True, exist_ok=False)
    witnesses = []
    with (output / "features.jsonl").open("x") as stream:
        for doc_id in ids:
            raw = records[doc_id]
            text, _ = marked_document(raw)
            encoded = tokenizer.encode(text, add_special_tokens=True, truncation=False)
            feature, witness = pack_feature(raw, encoded, start=start, end=end, length=4096)
            stream.write(json.dumps(feature, separators=(",", ":")) + "\n")
            witnesses.append(witness)
    (output / "documents.jsonl").write_text(
        "".join(json.dumps(row, separators=(",", ":")) + "\n" for row in witnesses))
    report = {"status": "complete", "scope": "unlabeled internal-dev inputs only",
              "candidate_digest": digest, "population": population,
              "max_nonpad_tokens": max(row["nonpad_tokens"] for row in witnesses),
              "max_mentions": max(row["mentions"] for row in witnesses),
              "max_pairs": max(row["pairs"] for row in witnesses),
              "total_nonpad_tokens": sum(row["nonpad_tokens"] for row in witnesses),
              "config_sha256": sha256_file(args.config),
              "gold_accessed": False, "encoder_loaded": False, "optimizer_steps": 0,
              "predictions_generated": False, "final_valid_accessed": False,
              "global_attention_policy": config["global_attention_policy"], "padded_length": 4096,
              "artifact_sha256": {p.name: sha256_file(p) for p in output.iterdir()}}
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
