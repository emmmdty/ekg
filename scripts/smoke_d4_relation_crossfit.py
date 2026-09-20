#!/usr/bin/env python
"""Bounded CUDA smoke for the D4 relation train-to-posterior path.

This is deliberately separate from the immutable five-fold runner.  It trains
one epoch on the 30-document relation fixture, selects on five fixture documents,
and dumps their exhaustive causal posteriors.  Its score is never a model-
selection or thesis result.
"""

from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
from pathlib import Path

from ekg.core.stage_bundle import sha256_file
from ekg.relations.data.maven_ere import load_maven_ere
from ekg.relations.pairs import candidate_pairs


class D4SmokeError(ValueError):
    """The bounded CUDA smoke did not satisfy its execution contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise D4SmokeError(message)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def smoke_contract(source: Path, *, seed: int = 13, dev_docs: int = 5) -> dict:
    docs = list(load_maven_ere(source))
    shuffled = list(docs)
    random.Random(seed).shuffle(shuffled)
    selected = shuffled[:dev_docs]
    _require(len(selected) == dev_docs, "smoke source has too few documents")
    return {
        "doc_ids": [doc.doc_id for doc in selected],
        "documents": len(selected),
        "ordered_mention_pairs": sum(len(candidate_pairs(doc)) for doc in selected),
    }


def commands(
    args: argparse.Namespace, contract: dict, manifest: Path
) -> tuple[list[str], list[str]]:
    checkpoint = args.output / "checkpoint"
    train = [
        sys.executable,
        "-u",
        "scripts/train_supervised_relations.py",
        "--train",
        str(args.source),
        "--model",
        str(args.model),
        "--output",
        str(checkpoint),
        "--epochs",
        "1",
        "--lr",
        "1e-5",
        "--head-lr",
        "1e-4",
        "--warmup-steps",
        "0",
        "--accum-steps",
        "8",
        "--neg-ratio",
        "inf",
        "--weight-alpha",
        "0.5",
        "--dev-metric",
        "macro",
        "--dev-docs",
        "5",
        "--seed",
        "13",
        "--official-mention-expansion",
        "--families",
        "causal",
        "subevent",
        "temporal",
        "--family-loss-rates",
        "temporal=2,causal=4,subevent=4",
        "--coref-aux-rate",
        "0.4",
        "--save-best-by-family",
    ]
    dump = [
        sys.executable,
        "-u",
        "scripts/dump_relation_causal_posteriors.py",
        "--data",
        str(args.source),
        "--manifest",
        str(manifest),
        "--checkpoint",
        str(checkpoint / "by_family" / "causal"),
        "--output",
        str(args.output / "causal_posteriors.jsonl"),
        "--metadata-output",
        str(args.output / "causal_posteriors.metadata.json"),
        "--expected-documents",
        str(contract["documents"]),
        "--expected-pairs",
        str(contract["ordered_mention_pairs"]),
        "--max-length",
        "512",
    ]
    return train, dump


def execute(args: argparse.Namespace, contract: dict) -> None:
    _require(not args.output.exists(), f"refusing to overwrite smoke: {args.output}")
    _require(args.model.is_dir(), f"model directory is missing: {args.model}")
    args.output.mkdir(parents=True)
    manifest = args.output / "evaluation_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": "ekg.d4_relation_smoke_manifest.v1",
                "doc_count": contract["documents"],
                "doc_ids": contract["doc_ids"],
                "source_sha256": sha256_file(args.source),
                "selection_only": True,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    train, dump = commands(args, contract, manifest)
    metadata = {
        "schema_version": "ekg.d4_relation_crossfit_smoke.v1",
        "status": "incomplete",
        "scientific_result": False,
        "source_sha256": sha256_file(args.source),
        "manifest_sha256": sha256_file(manifest),
        "train_argv": train,
        "dump_argv": dump,
    }
    metadata_path = args.output / "smoke.json"
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    try:
        subprocess.run(train, cwd=args.repo, check=True)
        training = _load(args.output / "checkpoint" / "run_metadata.json")
        _require(training.get("device") == "cuda", "smoke did not run on CUDA")
        selection_path = args.output / "checkpoint/by_family/causal/selection.json"
        _require(selection_path.is_file(), "causal family checkpoint was not selected")
        subprocess.run(dump, cwd=args.repo, check=True)
        posterior = _load(args.output / "causal_posteriors.metadata.json")
        _require(posterior.get("documents") == contract["documents"], "posterior docs")
        _require(
            posterior.get("ordered_mention_pairs") == contract["ordered_mention_pairs"],
            "posterior pairs",
        )
        artifacts = (
            selection_path,
            args.output / "checkpoint/by_family/causal/heads.pt",
            args.output / "checkpoint/by_family/causal/model.safetensors",
            args.output / "causal_posteriors.jsonl",
            args.output / "causal_posteriors.metadata.json",
        )
        for path in artifacts:
            _require(path.is_file(), f"missing smoke artifact: {path}")
        metadata.update(
            {
                "status": "complete",
                "device": "cuda",
                "selection": _load(selection_path),
                "posterior": {
                    "documents": posterior["documents"],
                    "ordered_mention_pairs": posterior["ordered_mention_pairs"],
                },
                "artifacts_sha256": {
                    str(path.relative_to(args.output)): sha256_file(path)
                    for path in artifacts
                },
            }
        )
    except Exception:
        metadata["status"] = "failed"
        metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
        raise
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("data/processed/maven_ere/train_smoke.jsonl"),
    )
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    args.repo = args.repo.resolve()
    args.source = args.source.resolve()
    args.model = args.model.resolve()
    args.output = args.output.resolve()
    contract = smoke_contract(args.source)
    manifest = args.output / "evaluation_manifest.json"
    train, dump = commands(args, contract, manifest)
    if not args.execute:
        print(json.dumps({"contract": contract, "train_argv": train, "dump_argv": dump}, indent=2))
        return 0
    execute(args, contract)
    print("[d4-relation-crossfit-smoke] complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
