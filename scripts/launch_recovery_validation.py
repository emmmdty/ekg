#!/usr/bin/env python
"""Check a frozen recovery job, or explicitly execute it on an empty GPU.

Default is CPU-only verification and printing exact commands. Execute only in
the authorized remote context; 5090 authorization still comes from the user.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
from pathlib import Path

from ekg.core.stage_bundle import model_content_digest, sha256_file


def check_files(repo, job):
    if job["seed"] != 13:
        raise ValueError("only frozen seed 13 is authorized")
    for path, expected in job["inputs"].items():
        if sha256_file(repo / path) != expected:
            raise ValueError(f"input hash mismatch: {path}")
    for path, expected in job["models"].items():
        if model_content_digest(repo / path) != expected:
            raise ValueError(f"model content hash mismatch: {path}")
    for path in job["outputs"]:
        if (repo / path).exists():
            raise FileExistsError(f"refusing to overwrite {path}")


def check_gpu_rows(devices, processes, index):
    rows = {int(r[0]): r for line in devices.splitlines()
            if (r := [v.strip() for v in line.split(",")]) and len(r) == 4}
    if index not in rows:
        raise ValueError(f"unknown GPU index {index}")
    _, uuid, memory, utilization = rows[index]
    if (int(memory) > 512 or int(utilization) > 5
            or any(line.split(",")[0].strip() == uuid for line in processes.splitlines())):
        raise ValueError(f"GPU {index} is occupied")
    return uuid


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--job", required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--gpu", type=int)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text())
    if (plan["schema_version"] != "ekg.recovery_jobs.v1"
            or plan["final_valid_accessed"] is not False):
        raise ValueError("invalid recovery contract")
    job = plan["jobs"][args.job]
    repo = Path.cwd().resolve()
    if str(repo) != job["cwd"]:
        raise ValueError(f"job requires cwd {job['cwd']}")
    check_files(repo, {"seed": 13, "inputs": plan["code_sha256"],
                       "models": {}, "outputs": []})
    check_files(repo, job)
    for argv in job["commands"]:
        print(shlex.join(argv), flush=True)
    if not args.execute:
        print("CPU preflight PASS; no model execution")
        return 0
    if args.gpu is None:
        raise ValueError("explicit GPU index required")
    devices = subprocess.check_output(["nvidia-smi", "--query-gpu=index,uuid,memory.used,"
        "utilization.gpu", "--format=csv,noheader,nounits"], text=True)
    processes = subprocess.check_output(["nvidia-smi", "--query-compute-apps=gpu_uuid,pid",
                                         "--format=csv,noheader,nounits"], text=True)
    uuid = check_gpu_rows(devices, processes, args.gpu)
    environment = {**os.environ, "CUDA_VISIBLE_DEVICES": uuid,
                   "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"}
    subprocess.run([".venv/bin/python", "-c",
                    "import torch; assert torch.cuda.is_available(), 'CUDA unavailable'"],
                   check=True, cwd=repo, env=environment)
    status_path = repo / job["status_output"]
    status_path.parent.mkdir(parents=True, exist_ok=True)
    status = {"job": args.job, "plan_sha256": sha256_file(args.plan),
              "seed": 13, "gpu_uuid": uuid, "status": "running",
              "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
              "commands": job["commands"]}
    with status_path.open("x") as handle:
        json.dump(status, handle, indent=2)
    try:
        for argv in job["commands"]:
            subprocess.run(argv, check=True, cwd=repo, env=environment)
        status["artifact_sha256"] = {path: sha256_file(repo / path)
            for path in job["expected_files"]}
        status["status"] = "complete"
    except BaseException:
        status["status"] = "failed"
        raise
    finally:
        status_path.write_text(json.dumps(status, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
