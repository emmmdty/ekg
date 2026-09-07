#!/usr/bin/env python
"""Materialize LLMERE's MAVEN-ERE splits from the frozen v6 manifests.

LLMERE's upstream ``split_data.py`` makes a random 8:2 split of the public
training data.  That is not the R1 protocol: this helper writes its train
split from the 2,622-document manifest and writes both valid and test from the
291-document internal-development manifest.  The upstream converters then run
unchanged against the files produced here.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _load_ids(path: Path) -> set[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    ids = payload.get("doc_ids")
    if not isinstance(ids, list) or not all(isinstance(item, str) for item in ids):
        raise SystemExit(f"{path} has no string doc_ids list")
    return set(ids)


def build_splits(
    *, source: Path, train_manifest: Path, dev_manifest: Path, output: Path
) -> dict[str, int]:
    """Write LLMERE-compatible train/valid/test JSONL files and return sizes."""
    train_ids, dev_ids = _load_ids(train_manifest), _load_ids(dev_manifest)
    if train_ids & dev_ids:
        raise SystemExit("train and internal-dev manifests overlap")

    lines: dict[str, str] = {}
    source_lines = source.read_text(encoding="utf-8").splitlines(keepends=True)
    for line_number, line in enumerate(source_lines, start=1):
        record = json.loads(line)
        doc_id = record.get("id")
        if not isinstance(doc_id, str):
            raise SystemExit(f"{source}:{line_number} has no string id")
        if doc_id in lines:
            raise SystemExit(f"{source} repeats document id {doc_id}")
        lines[doc_id] = line

    requested = train_ids | dev_ids
    missing = requested - set(lines)
    if missing:
        raise SystemExit(f"{len(missing)} manifest ids absent from {source}: {sorted(missing)[:3]}")

    output.mkdir(parents=True, exist_ok=True)
    sizes: dict[str, int] = {}
    for name, ids in (("train", train_ids), ("valid", dev_ids), ("test", dev_ids)):
        (output / f"{name}.jsonl").write_text(
            "".join(lines[doc_id] for doc_id in sorted(ids)), encoding="utf-8"
        )
        sizes[name] = len(ids)
    return sizes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source", type=Path, default=Path("data/processed/maven_ere/train.jsonl")
    )
    parser.add_argument(
        "--train-manifest",
        type=Path,
        default=Path("data/protocols/v6/manifests/maven_ere_train.json"),
    )
    parser.add_argument(
        "--internal-dev-manifest",
        type=Path,
        default=Path("data/protocols/v6/manifests/maven_ere_internal-dev.json"),
    )
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    for path in (args.source, args.train_manifest, args.internal_dev_manifest):
        if not path.is_file():
            raise SystemExit(f"required input is absent: {path}")
    sizes = build_splits(
        source=args.source,
        train_manifest=args.train_manifest,
        dev_manifest=args.internal_dev_manifest,
        output=args.out,
    )
    for name, count in sizes.items():
        print(f"{name}: {count} documents")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
