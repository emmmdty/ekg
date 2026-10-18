#!/usr/bin/env python
"""Prepare ERGO-native train features and separate gold targets, without an encoder."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import Counter
from pathlib import Path

from ekg.core.protocol import load_manifest_ids
from ekg.core.stage_bundle import sha256_file
from ekg.relations.ergo_adapter import (
    causal_targets,
    longformer_inputs,
    marked_document,
    native_pair_features,
)
from ekg.relations.maven_ere_official import candidate_population_digest, records_by_id


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    if (os.environ.get("CUDA_VISIBLE_DEVICES") != "-1"
            or config["schema_version"] != "ekg.ergo_native_features.v1"
            or config["final_valid_accessed"] is not False or config["max_length"] != 4096
            or config["global_attention_policy"] != "BOS_EOS_from_released_cache"):
        raise ValueError("CPU-only frozen feature scope required")
    for path, expected in config["input_sha256"].items():
        if sha256_file(Path(path)) != expected:
            raise ValueError(f"input/code identity drift: {path}")
    output = Path(config["output"])
    if output.exists():
        raise FileExistsError(output)
    ids = load_manifest_ids(Path(config["manifest"]))
    records = records_by_id(map(json.loads, Path(config["unlabeled"]).read_text().splitlines()),
                            source="unlabeled")
    gold = records_by_id(map(json.loads, Path(config["gold"]).read_text().splitlines()),
                         source="gold")
    reference = records_by_id(
        map(json.loads, Path(config["reference_documents"]).read_text().splitlines()),
        source="capacity witness")
    if set(records) != set(gold) or set(records) != set(ids) or set(reference) != set(ids):
        raise ValueError("complete train/manifest/reference coverage required")
    digest, population = candidate_population_digest({
        doc_id: {"events": [{"mention": [m]} for m in raw["event_mentions"]],
                 "TIMEX": raw["TIMEX"]} for doc_id, raw in records.items()
    })
    if digest != config["candidate_digest"]:
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
    class_counts = Counter()
    maximum = 0
    with (output / "features.jsonl").open("x") as features_file, (
            output / "targets.jsonl").open("x") as targets_file:
        for doc_id in ids:
            raw = records[doc_id]
            text, mids = marked_document(raw)
            encoded = tokenizer.encode(text, add_special_tokens=True, truncation=False)
            positions = [i for i, value in enumerate(encoded) if value == start]
            if (len(positions) != len(mids) or encoded.count(end) != len(mids)
                    or len(encoded) > config["max_length"]):
                raise ValueError(f"endpoint loss or overlong input: {doc_id}")
            marker_positions = dict(zip(mids, positions, strict=True))
            packed_ids = json.dumps(encoded, separators=(",", ":")).encode()
            identity = hashlib.sha256(packed_ids).hexdigest()
            if (identity != reference[doc_id]["input_ids_sha256"]
                    or marker_positions != reference[doc_id]["marker_positions"]):
                raise ValueError(f"full input differs from capacity witness: {doc_id}")
            pair_features = native_pair_features(raw, marker_positions)
            target = causal_targets(raw, gold[doc_id])
            if len(target) != len(pair_features["pair_ids"]):
                raise ValueError("target/candidate population mismatch")
            size = len(encoded)
            maximum = max(maximum, size)
            feature = {
                "id": doc_id, "mention_ids": mids,
                **longformer_inputs(encoded, padded_length=config["max_length"]),
                "t1_pos": pair_features["t1_pos"], "t2_pos": pair_features["t2_pos"],
            }
            features_file.write(json.dumps(feature, separators=(",", ":")) + "\n")
            targets_file.write(json.dumps({"id": doc_id, "target": target}) + "\n")
            class_counts.update(target)
    if dict(class_counts) != {int(k): v for k, v in config["expected_class_counts"].items()}:
        raise ValueError("native target counts differ from frozen anchor supervision")
    report = {
        "status": "complete", "scope": "Native train features only; not ERGO inference/training",
        "candidate_digest": digest, "population": population, "max_encoded_tokens": maximum,
        "class_counts": dict(class_counts), "padding_length": config["max_length"],
        "global_attention_policy": config["global_attention_policy"],
        "targets_in_model_text": False,
        "encoder_loaded": False, "optimizer_steps": 0, "final_valid_accessed": False,
        "config_sha256": sha256_file(args.config),
        "artifact_sha256": {p.name: sha256_file(p) for p in output.iterdir()},
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
