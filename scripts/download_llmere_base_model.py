#!/usr/bin/env python
"""Freeze an ungated Llama-3 mirror revision before downloading its weights."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from huggingface_hub import HfApi, snapshot_download


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", default="NousResearch/Meta-Llama-3-8B")
    parser.add_argument("--endpoint", default="https://huggingface.co")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--record", required=True, type=Path)
    args = parser.parse_args()

    info = HfApi(endpoint=args.endpoint).model_info(args.repository)
    if not info.sha:
        raise SystemExit(f"model hub returned no immutable revision for {args.repository}")
    local = snapshot_download(
        repo_id=args.repository,
        revision=info.sha,
        local_dir=args.output,
        local_dir_use_symlinks=False,
        endpoint=args.endpoint,
    )
    payload = {
        "repository": args.repository,
        "endpoint": args.endpoint,
        "revision": info.sha,
        "resolved_path": local,
        "ungated_mirror": True,
    }
    args.record.parent.mkdir(parents=True, exist_ok=True)
    args.record.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[llmere] downloaded {args.repository}@{info.sha} to {local}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
