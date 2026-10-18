"""Thin reuse of the external ERGO trainer; no encoder or native run admission.

The prefix meter reproduces the upstream *binary* training log, including wrong
positive subtypes counted as correct. It must never select a native checkpoint.
Native selection uses the pinned official three-class causal evaluator.
"""
from __future__ import annotations

import ast
import logging
from functools import partial
from pathlib import Path
from types import SimpleNamespace

from ekg.core.stage_bundle import sha256_file


class BinaryPrefixMeter:
    """Count only appended items instead of rescanning the growing prefix per doc."""

    def __init__(self):
        self.gold = self.predicted = None
        self.seen = self.correct = self.positive_gold = self.positive_predicted = 0

    def __call__(self, gold, predicted, logger):
        if len(gold) != len(predicted):
            raise ValueError("gold/predicted prefix length mismatch")
        if self.gold is not gold or self.predicted is not predicted:
            self.gold, self.predicted = gold, predicted
            self.seen = self.correct = self.positive_gold = self.positive_predicted = 0
        if len(gold) < self.seen:
            raise ValueError("upstream prefixes must append within an epoch")
        for i in range(self.seen, len(gold)):
            g, p = gold[i], predicted[i]
            self.positive_gold += int(g != 0)
            self.positive_predicted += int(p != 0)
            self.correct += int(g != 0 and p != 0)
        self.seen = len(gold)
        p = self.correct / (self.positive_predicted + 1e-100) if self.positive_predicted else 0.0
        r = self.correct / self.positive_gold if self.positive_gold else 0.0
        f = 2 * p * r / (p + r + 1e-100) if r + p > 1e-4 else 0.0
        logger.info(f"correct {self.correct}, predicted {self.positive_predicted}, "
                    f"golden {self.positive_gold}")
        return p, r, f


def load_train_epoch(path: Path, expected_sha: str, compute_f1):
    """Compile the exact pinned function body, avoiding unrelated missing ESL imports."""
    if sha256_file(path) != expected_sha:
        raise ValueError("original trainer source drift")
    import numpy as np
    import torch

    nodes = [n for n in ast.parse(path.read_text()).body
             if isinstance(n, ast.FunctionDef) and n.name == "train_epoch"]
    if len(nodes) != 1:
        raise ValueError("expected exactly one original train_epoch")
    # Original body/math retained; reject nonfinite norms before clipping can erase them.
    guarded_nn = SimpleNamespace(utils=SimpleNamespace(clip_grad_norm_=partial(
        torch.nn.utils.clip_grad_norm_, error_if_nonfinite=True)))
    namespace = {"torch": torch, "nn": guarded_nn, "np": np, "logging": logging,
                 "logger": logging.getLogger("external_ergo_train"), "compute_f1": compute_f1}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), namespace)
    return namespace["train_epoch"]


def load_linear_scheduler(path: Path, expected_sha: str):
    """Use the original HF linear schedule function alongside its original AdamW."""
    if sha256_file(path) != expected_sha:
        raise ValueError("original scheduler source drift")
    import torch

    nodes = [n for n in ast.parse(path.read_text()).body
             if isinstance(n, ast.FunctionDef) and n.name == "get_linear_schedule_with_warmup"]
    if len(nodes) != 1:
        raise ValueError("expected exactly one original linear scheduler")
    namespace = {"Optimizer": torch.optim.Optimizer,
                 "LambdaLR": torch.optim.lr_scheduler.LambdaLR}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), namespace)
    return namespace["get_linear_schedule_with_warmup"]
