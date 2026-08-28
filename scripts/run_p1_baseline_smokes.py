#!/usr/bin/env python
"""Run the three P1 Ch2 baseline adapters on one frozen 10-document fixture.

These are deliberately schema-only CPU smokes: each real source adapter receives
its own label-vector convention and writes the official prediction shape. Constant
NONE labels are not model outputs and no score is treated as baseline evidence.
P1.6 separately performs a real checkpoint/model forward smoke on the 4090.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import py_compile
import subprocess
from pathlib import Path

from ekg.relations.data.maven_ere import load_maven_ere
from ekg.relations.maven_ere_official import (
    candidate_population_digest,
    empty_official_prediction,
    records_by_id,
    validate_official_predictions,
)
from ekg.relations.pairs import pair_examples


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _test_shape(record: dict) -> dict:
    mentions = [
        {**mention, "type": event.get("type", "Unknown"), "type_id": event.get("type_id")}
        for event in record.get("events", [])
        for mention in event.get("mention", [])
    ]
    return {
        "id": record["id"],
        "title": record.get("title", ""),
        "tokens": record.get("tokens", []),
        "sentences": record.get("sentences", []),
        "event_mentions": mentions,
        "TIMEX": record.get("TIMEX", []),
    }


def _normalize_single(raw: list[dict], gold: list[dict]) -> list[dict]:
    raw_by_id = records_by_id(raw, source="official-single adapter")
    normalized = []
    for record in gold:
        prediction = empty_official_prediction(record)
        prediction["causal_relations"] = raw_by_id[record["id"]]["causal_relations"]
        normalized.append(prediction)
    return normalized


def _official_single(
    source: Path, fixture: Path, gold: list[dict], output: Path
) -> list[dict]:
    module = _load_module("p1_official_single_dump", source / "causal/src/dump_result.py")
    predictions = []
    for record in gold:
        n_mentions = sum(len(event.get("mention", [])) for event in record.get("events", []))
        predictions.append(
            {"doc_id": record["id"], "preds": [2] * (n_mentions * (n_mentions - 1))}
        )
    raw_dir = output / "source_adapter"
    module.dump_result(str(fixture), predictions, str(raw_dir))
    return _normalize_single(_load_jsonl(raw_dir / "test_prediction.jsonl"), gold)


def _official_joint(
    source: Path, fixture: Path, gold: list[dict]
) -> list[dict]:
    module = _load_module("p1_official_joint_dump", source / "joint/src/dump_result.py")
    causal = []
    subevent = []
    temporal = []
    coreference = []
    for record in gold:
        n_mentions = sum(len(event.get("mention", [])) for event in record.get("events", []))
        n_temporal = n_mentions + len(record.get("TIMEX", []))
        causal.append(
            {"doc_id": record["id"], "preds": [0] * (n_mentions * (n_mentions - 1))}
        )
        subevent.append(
            {"doc_id": record["id"], "preds": [0] * (n_mentions * (n_mentions - 1))}
        )
        temporal.append(
            {"doc_id": record["id"], "preds": [6] * (n_temporal * (n_temporal - 1))}
        )
        coreference.append({"doc_id": record["id"], "clusters": []})
    all_results: dict[str, dict] = {}
    module.causal_dump(str(fixture), causal, all_results)
    module.subevent_dump(str(fixture), subevent, all_results)
    module.temporal_dump(str(fixture), temporal, all_results)
    module.coref_dump(str(fixture), coreference, all_results)
    return [all_results[record["id"]] for record in gold]


def _local_pair(gold_path: Path, gold: list[dict]) -> tuple[list[dict], int]:
    docs = list(load_maven_ere(gold_path))
    rows = sum(
        len(pair_examples(doc, expand_event_relations=True))
        for doc in docs
    )
    return [empty_official_prediction(record) for record in gold], rows


def _compile_entrypoints(source: Path) -> list[str]:
    paths = [
        source / "causal/main.py",
        source / "joint/main.py",
        source / "utils/model.py",
        source / "joint/src/model.py",
    ]
    for path in paths:
        py_compile.compile(str(path), doraise=True)
    return [str(path) for path in paths]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("data/protocols/v6"))
    parser.add_argument("--docs", type=int, default=10)
    args = parser.parse_args()
    if args.docs != 10:
        raise SystemExit("P1 fixture size is frozen at exactly 10 documents")

    manifest_path = args.root / "manifests/maven_ere_internal-dev.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    fixture_ids = manifest["doc_ids"][: args.docs]
    source_gold = _load_jsonl(Path(manifest["source_path"]))
    source_by_id = records_by_id(source_gold, source=manifest["source_path"])
    gold = [source_by_id[item] for item in fixture_ids]
    internal_dev = [source_by_id[item] for item in manifest["doc_ids"]]
    longest = max(
        internal_dev,
        key=lambda record: (
            sum(len(sentence) for sentence in record.get("tokens", [])),
            str(record["id"]),
        ),
    )
    fixture_dir = args.root / "baselines/fixture"
    gold_path = fixture_dir / "gold.jsonl"
    test_path = fixture_dir / "test.jsonl"
    longest_gold_path = fixture_dir / "longest_gold.jsonl"
    longest_test_path = fixture_dir / "longest_test.jsonl"
    _write_jsonl(gold_path, gold)
    _write_jsonl(test_path, [_test_shape(record) for record in gold])
    _write_jsonl(longest_gold_path, [longest])
    _write_jsonl(longest_test_path, [_test_shape(longest)])
    gold_by_id = records_by_id(gold, source=str(gold_path))
    candidate_digest, population = candidate_population_digest(gold_by_id)

    source = args.root / "sources/MAVEN-ERE"
    commit = subprocess.run(
        ("git", "rev-parse", "HEAD"),
        cwd=source,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    source_lock = json.loads((args.root / "source_lock.json").read_text(encoding="utf-8"))
    compiled = _compile_entrypoints(source)

    outputs: dict[str, tuple[list[dict], dict]] = {}
    local_predictions, local_rows = _local_pair(gold_path, gold)
    outputs["local_pair"] = (
        local_predictions,
        {
            "implementation": "ekg.relations.pairs.pair_examples",
            "candidate_rows": local_rows,
            "license": "MIT",
            "input_assumptions": {
                "mentions": "gold event mentions",
                "candidate_universe": "all ordered event-mention pairs excluding self",
                "gold_expansion": "event relations expand to the Cartesian product of mentions",
                "model_input": False,
            },
        },
    )
    outputs["official_single"] = (
        _official_single(source, test_path, gold, args.root / "baselines/official_single"),
        {
            "implementation": "MAVEN-ERE causal/src/dump_result.py",
            "source_commit": commit,
            "license": "GPL-3.0",
            "input_assumptions": {
                "mentions": "gold event mentions in official test shape",
                "candidate_universe": "official all ordered event-mention pairs",
                "label_vector": "causal NONE id 2",
                "model_input": False,
            },
        },
    )
    outputs["official_joint"] = (
        _official_joint(source, test_path, gold),
        {
            "implementation": "MAVEN-ERE joint/src/dump_result.py",
            "source_commit": commit,
            "license": "GPL-3.0",
            "input_assumptions": {
                "mentions": "gold event mentions/TIMEX in official test shape",
                "candidate_universe": "official all ordered pairs per relation family",
                "label_vector": "joint NONE ids causal/subevent 0 and temporal 6",
                "model_input": False,
            },
        },
    )

    summary = {
        "schema_version": "ekg.p1_baseline_smoke.v1",
        "fixture_doc_ids": fixture_ids,
        "fixture_gold_sha256": _sha256(gold_path),
        "fixture_test_sha256": _sha256(test_path),
        "longest_internal_dev": {
            "doc_id": longest["id"],
            "source_token_count": sum(
                len(sentence) for sentence in longest.get("tokens", [])
            ),
            "selection": "max source token count in frozen 291-doc internal-dev; tie doc_id",
            "gold_sha256": _sha256(longest_gold_path),
            "test_sha256": _sha256(longest_test_path),
        },
        "candidate_id_digest": candidate_digest,
        "population_counts": population,
        "source_lock_sha256": _sha256(args.root / "source_lock.json"),
        "source_commit": commit,
        "source_patch": source_lock["patches"],
        "compiled_entrypoints": compiled,
        "smokes": {},
    }
    for name, (predictions, metadata) in outputs.items():
        prediction_by_id = records_by_id(predictions, source=name)
        validation = validate_official_predictions(
            gold_by_id,
            prediction_by_id,
            expected_candidate_digest=candidate_digest,
        )
        output_dir = args.root / "baselines" / name
        prediction_path = output_dir / "predictions.jsonl"
        _write_jsonl(prediction_path, predictions)
        smoke = {
            **metadata,
            "status": "pass",
            "schema_only": True,
            "model_execution": False,
            "constant_label_policy": "all NONE; never score as baseline evidence",
            "prediction_sha256": _sha256(prediction_path),
            "validation": validation,
        }
        (output_dir / "smoke.json").write_text(
            json.dumps(smoke, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        summary["smokes"][name] = smoke
    summary_path = args.root / "baselines/smoke_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"[p1-baselines] PASS: {len(outputs)} adapters x {len(gold)} docs; "
        f"candidate={candidate_digest}; schema_only=true"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
