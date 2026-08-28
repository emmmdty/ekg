#!/usr/bin/env python
"""Run and record P1's three mandatory local verification commands."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from ekg.core.stage_bundle import tree_sha256

COMMANDS = {
    "pytest": ["uv", "run", "pytest"],
    "ruff": ["uv", "run", "ruff", "check", "src", "tests", "scripts"],
    "ekg_smoke": ["uv", "run", "ekg-smoke"],
}


def _tested_files() -> list[Path]:
    files = [Path("pyproject.toml"), Path("uv.lock")]
    for root in (Path("src"), Path("tests"), Path("scripts")):
        files.extend(path for path in root.rglob("*.py") if path.is_file())
    return files


def main() -> int:
    output = Path("data/protocols/v6/local_gate.json")
    tested_files = _tested_files()
    before_hash = tree_sha256(Path.cwd(), tested_files)
    results = {}
    passed = True
    for name, command in COMMANDS.items():
        print(f"[p1-local] running: {' '.join(command)}", flush=True)
        completed = subprocess.run(command, text=True, capture_output=True)
        results[name] = {
            "command": command,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
        passed &= completed.returncode == 0
        print(completed.stdout, end="")
        if completed.stderr:
            print(completed.stderr, end="")
    payload = {
        "schema_version": "ekg.p1_local_gate.v1",
        "status": "pass" if passed else "failed",
        "tested_tree_sha256": before_hash,
        "tested_file_count": len(tested_files),
        "results": results,
    }
    after_hash = tree_sha256(Path.cwd(), tested_files)
    if after_hash != before_hash:
        payload["status"] = "failed"
        payload["tree_changed_during_gate"] = True
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[p1-local] {payload['status'].upper()}: wrote {output}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
