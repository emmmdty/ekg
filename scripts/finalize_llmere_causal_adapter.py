#!/usr/bin/env python
"""Record hashes and score identity after an LLMERE-causal remote run."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_manifest(path: Path) -> tuple[str, list[dict[str, str]]]:
    if not path.is_dir():
        raise SystemExit(f"directory is absent: {path}")
    entries: list[dict[str, str]] = []
    digest = hashlib.sha256()
    for child in sorted(item for item in path.rglob("*") if item.is_file()):
        relative = child.relative_to(path).as_posix()
        checksum = sha256_file(child)
        entries.append({"path": relative, "sha256": checksum})
        digest.update(f"{relative}\t{checksum}\n".encode())
    if not entries:
        raise SystemExit(f"directory has no files: {path}")
    return digest.hexdigest(), entries


def command_output(argv: list[str]) -> str:
    return subprocess.check_output(argv, text=True, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", required=True, type=Path)
    parser.add_argument("--worker-python", required=True, type=Path)
    parser.add_argument("--model-path", required=True, type=Path)
    parser.add_argument("--model-record", required=True, type=Path)
    parser.add_argument("--generated-predictions", required=True, type=Path)
    parser.add_argument("--official-predictions", required=True, type=Path)
    parser.add_argument("--conversion-report", required=True, type=Path)
    parser.add_argument("--official-metrics", required=True, type=Path)
    args = parser.parse_args()

    metadata_path = args.run_root / "adapter/run_metadata.json"
    if not metadata_path.is_file():
        raise SystemExit(f"metadata is absent: {metadata_path}")
    for path in (
        args.worker_python,
        args.model_path,
        args.model_record,
        args.generated_predictions,
        args.official_predictions,
        args.conversion_report,
        args.official_metrics,
    ):
        if not path.exists():
            raise SystemExit(f"required output is absent: {path}")

    metadata: dict[str, Any] = json.loads(metadata_path.read_text(encoding="utf-8"))
    model_tree_sha, model_entries = tree_manifest(args.model_path)
    model_record = json.loads(args.model_record.read_text(encoding="utf-8"))
    freeze = command_output([str(args.worker_python), "-m", "pip", "freeze", "--all"])
    environment_path = args.run_root / "adapter/llamafactory_environment.txt"
    environment_path.write_text(freeze, encoding="utf-8")
    metrics = json.loads(args.official_metrics.read_text(encoding="utf-8"))
    metadata.update(
        {
            "status": "scored",
            "base_model": {
                "repository": "NousResearch/Meta-Llama-3-8B",
                "path": str(args.model_path),
                "record": model_record,
                "record_sha256": sha256_file(args.model_record),
                "recursive_sha256": model_tree_sha,
                "files": model_entries,
            },
            "environment": {
                "python": str(args.worker_python),
                "freeze_path": str(environment_path),
                "freeze_sha256": sha256_file(environment_path),
            },
            "outputs": {
                "generated_predictions": {
                    "path": str(args.generated_predictions),
                    "sha256": sha256_file(args.generated_predictions),
                },
                "official_predictions": {
                    "path": str(args.official_predictions),
                    "sha256": sha256_file(args.official_predictions),
                },
                "conversion_report": {
                    "path": str(args.conversion_report),
                    "sha256": sha256_file(args.conversion_report),
                },
                "official_metrics": {
                    "path": str(args.official_metrics),
                    "sha256": sha256_file(args.official_metrics),
                },
            },
            "official_causal_scores": {
                key: value for key, value in metrics["scores"].items() if "causal" in key.lower()
            },
        }
    )
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"[llmere] recorded scored run metadata at {metadata_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
