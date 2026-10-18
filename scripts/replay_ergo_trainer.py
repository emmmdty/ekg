#!/usr/bin/env python
"""CPU-only toy replay of unchanged ERGO train_epoch and a logging-only adapter."""
from __future__ import annotations

import argparse
import ast
import copy
import json
import logging
import os
from pathlib import Path
from types import SimpleNamespace

from ekg.core.stage_bundle import sha256_file
from ekg.relations.ergo_training import BinaryPrefixMeter, load_train_epoch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    args = parser.parse_args()
    cfg = json.loads(args.config.read_text())
    if (os.environ.get("CUDA_VISIBLE_DEVICES") != "-1"
            or cfg["schema_version"] != "ekg.ergo_trainer_replay.v1"
            or cfg["seed"] != 13 or cfg["final_valid_accessed"] is not False):
        raise ValueError("CPU-only toy replay scope required")
    for name, expected in cfg["pins"].items():
        if sha256_file(Path(name)) != expected:
            raise ValueError(f"replay source drift: {name}")
    output = Path(cfg["output"])
    if output.exists():
        raise FileExistsError(output)
    import numpy as np
    import torch
    from profile_ergo_native_cost import load_legacy_adamw, parameter_identities

    if torch.cuda.is_available():
        raise ValueError("CUDA must be hidden for toy replay")
    torch.set_num_threads(1)
    torch.manual_seed(13)
    # Independent reference: compile actual upstream functions with their original log scorer.
    reference_ns = {"torch": torch, "nn": torch.nn, "np": np, "logging": logging,
                    "logger": logging.getLogger("upstream_replay")}
    for name, function in ((cfg["utils_source"], "compute_f1"),
                           (cfg["train_source"], "train_epoch")):
        nodes = [n for n in ast.parse(Path(name).read_text()).body
                 if isinstance(n, ast.FunctionDef) and n.name == function]
        assert len(nodes) == 1
        exec(compile(ast.Module(body=nodes, type_ignores=[]), name, "exec"), reference_ns)
    schedule_ns = {"Optimizer": torch.optim.Optimizer,
                   "LambdaLR": torch.optim.lr_scheduler.LambdaLR}
    nodes = [n for n in ast.parse(Path(cfg["optimizer_source"]).read_text()).body
             if isinstance(n, ast.FunctionDef) and n.name == "get_linear_schedule_with_warmup"]
    assert len(nodes) == 1
    exec(compile(ast.Module(body=nodes, type_ignores=[]), cfg["optimizer_source"], "exec"),
         schedule_ns)
    original = reference_ns["compute_f1"]
    meter = BinaryPrefixMeter()
    g, p = [], []
    for gold, pred in (([1, 2, 0], [2, 0, 1]), ([0, 2], [0, 2]), ([0, 0], [0, 0])):
        g.extend(gold)
        p.extend(pred)
        assert meter(g, p, reference_ns["logger"]) == original(g, p, reference_ns["logger"])

    class ToyModel(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.fc = torch.nn.Linear(2, 3)

        def forward(self, enc_input_ids, **unused):
            logits = self.fc(enc_input_ids.float())
            target = torch.tensor(unused["target"][0])
            return torch.nn.functional.cross_entropy(logits, target), logits

    reference = ToyModel()
    adapted = copy.deepcopy(reference)
    before = parameter_identities(reference)
    adamw = load_legacy_adamw(Path(cfg["optimizer_source"]), cfg["pins"][cfg["optimizer_source"]])
    optimizers = [adamw(m.parameters(), lr=1e-3, eps=1e-8) for m in (reference, adapted)]
    schedulers = [schedule_ns["get_linear_schedule_with_warmup"](
        opt, num_warmup_steps=0.4, num_training_steps=4) for opt in optimizers]
    epochs = [reference_ns["train_epoch"], load_train_epoch(
        Path(cfg["train_source"]), cfg["pins"][cfg["train_source"]], BinaryPrefixMeter())]
    toy = SimpleNamespace(device=torch.device("cpu"), gradient_accumulation_steps=1,
                          max_grad_norm=1.0, logging_steps=20)
    batches = [(torch.tensor([[1., 2.], [3., 4.]]), torch.ones(2, 2), torch.ones(2, 2),
                [[1, 2]], [[2, 1]], torch.zeros(1, 2, 2, dtype=torch.bool), [targets])
               for targets in ([0, 2], [1, 0])]
    rows = []
    for epoch in range(2):
        metrics = [fn(toy, model, batches, opt, schedule) for fn, model, opt, schedule in
                   zip(epochs, (reference, adapted), optimizers, schedulers, strict=True)]
        assert metrics[0] == metrics[1]
        assert all(torch.equal(a, b) for a, b in zip(
            reference.parameters(), adapted.parameters(), strict=True))
        assert schedulers[0].state_dict() == schedulers[1].state_dict()
        for left, right in zip(optimizers[0].state.values(), optimizers[1].state.values(),
                               strict=True):
            assert left.keys() == right.keys()
            assert all(torch.equal(left[k], right[k]) if isinstance(left[k], torch.Tensor)
                       else left[k] == right[k] for k in left)
        rows.append({"toy_pass": epoch, "original_metrics": metrics[0],
                     "adapted_metrics": metrics[1], "parameters_equal": True})
    assert before["numeric_sha256"] != parameter_identities(adapted)["numeric_sha256"]
    report = {"status": "complete", "scope": "toy nine-parameter linear model only",
              "original_function_body_unchanged": True, "binary_logging_exact": True,
              "parameters_optimizer_scheduler_equal": True, "toy_optimizer_calls_per_variant": 4,
              "native_epochs": 0, "encoder_loaded": False, "gpu_compute": False,
              "final_valid_accessed": False, "seed": 13, "rows": rows,
              "config_sha256": sha256_file(args.config), "before": before,
              "after": parameter_identities(adapted)}
    output.mkdir(parents=True, exist_ok=False)
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
