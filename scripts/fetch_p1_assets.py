#!/usr/bin/env python
"""Restore and verify P1's pinned official MAVEN-ERE source assets."""

from __future__ import annotations

import argparse
import json
import subprocess
import urllib.request
from pathlib import Path

from ekg.core.stage_bundle import sha256_file as _sha256

REPOSITORY = "https://github.com/THU-KEG/MAVEN-ERE.git"
COMMIT = "ac81a9711a69f43f55bfbc50b3bb573fd11c64b0"
EVALUATOR_URL = (
    "https://raw.githubusercontent.com/THU-KEG/MAVEN-ERE/"
    f"{COMMIT}/evaluate.py"
)
EVALUATOR_SHA256 = "32919e86d98c6fafae6aa9505579e2c356caee12c32c1a8c719910acec359598"


def _run(*args: str, cwd: Path | None = None) -> str:
    completed = subprocess.run(
        args,
        cwd=cwd,
        check=True,
        text=True,
        capture_output=True,
    )
    return completed.stdout.strip()


def _restore_repository(path: Path) -> None:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        _run("git", "clone", "--filter=blob:none", REPOSITORY, str(path))
    if not (path / ".git").exists():
        raise RuntimeError(f"{path} exists but is not a Git checkout")
    current = _run("git", "rev-parse", "HEAD", cwd=path)
    if current != COMMIT:
        dirty = _run("git", "status", "--porcelain", cwd=path)
        if dirty:
            raise RuntimeError(f"refusing to change dirty external checkout {path}")
        _run("git", "fetch", "origin", COMMIT, cwd=path)
        _run("git", "checkout", "--detach", COMMIT, cwd=path)
    actual = _run("git", "rev-parse", "HEAD", cwd=path)
    if actual != COMMIT:
        raise RuntimeError(f"official checkout mismatch: expected {COMMIT}, got {actual}")


def _restore_evaluator(path: Path) -> None:
    if path.exists() and _sha256(path) == EVALUATOR_SHA256:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".download")
    urllib.request.urlretrieve(EVALUATOR_URL, temporary)
    actual = _sha256(temporary)
    if actual != EVALUATOR_SHA256:
        raise RuntimeError(
            f"downloaded evaluator hash mismatch: expected {EVALUATOR_SHA256}, got {actual}"
        )
    temporary.replace(path)


def _apply_patch(checkout: Path, patch: Path) -> None:
    reverse = subprocess.run(
        (
            "git",
            "apply",
            "--ignore-space-change",
            "--ignore-whitespace",
            "--reverse",
            "--check",
            str(patch.resolve()),
        ),
        cwd=checkout,
        text=True,
        capture_output=True,
    )
    if reverse.returncode == 0:
        return
    check = subprocess.run(
        (
            "git",
            "apply",
            "--ignore-space-change",
            "--ignore-whitespace",
            "--check",
            str(patch.resolve()),
        ),
        cwd=checkout,
        text=True,
        capture_output=True,
    )
    if check.returncode != 0:
        raise RuntimeError(f"patch cannot be applied cleanly: {check.stderr.strip()}")
    _run(
        "git",
        "apply",
        "--ignore-space-change",
        "--ignore-whitespace",
        str(patch.resolve()),
        cwd=checkout,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("data/protocols/v6"))
    args = parser.parse_args()

    checkout = args.root / "sources" / "MAVEN-ERE"
    evaluator = args.root / "tools" / "maven_ere_evaluate.py"
    patch = Path("patches/p1/maven_ere_current_stack.patch")
    _restore_repository(checkout)
    _restore_evaluator(evaluator)
    _apply_patch(checkout, patch)
    lock = {
        "schema_version": "ekg.external_source_lock.v1",
        "repository": REPOSITORY,
        "commit": COMMIT,
        "license": "GPL-3.0",
        "license_path": str(checkout / "LICENSE"),
        "local_checkout": str(checkout),
        "patches": [
            {
                "path": str(patch),
                "sha256": _sha256(patch),
                "scope": "current transformers compatibility only; no protocol semantics",
            }
        ],
        "evaluator": {
            "url": EVALUATOR_URL,
            "local_path": str(evaluator),
            "sha256": _sha256(evaluator),
        },
    }
    lock_path = args.root / "source_lock.json"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[p1-assets] PASS: commit={COMMIT} evaluator={EVALUATOR_SHA256}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
