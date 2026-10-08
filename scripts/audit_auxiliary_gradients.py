#!/usr/bin/env python
"""Audit shared-parameter loss gradients, with a tiny CPU A4 counterexample.

The fixture tests an implication, not a trained model or benchmark. A negative
primary-dot-combined predicts main-loss ascent for an infinitesimal SGD step;
it does not establish an Adam trajectory or explain a measured F1 by itself.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from ekg.core.stage_bundle import sha256_file


def gradient_report(primary, auxiliary, parameters, *, weight: float = 1.0) -> dict:
    import torch

    if not math.isfinite(weight) or weight < 0:
        raise ValueError("auxiliary weight must be finite and non-negative")
    parameters = tuple(parameters)
    if not parameters:
        raise ValueError("explicit shared parameters are required")

    def vector(loss):
        grads = torch.autograd.grad(loss, parameters, retain_graph=True, allow_unused=True)
        # An unused parameter has a mathematically zero partial derivative.
        return torch.cat([
            (torch.zeros_like(p) if g is None else g).detach().reshape(-1).double()
            for p, g in zip(parameters, grads, strict=True)
        ])

    main, aux = vector(primary), vector(auxiliary)
    if not torch.isfinite(main).all() or not torch.isfinite(aux).all():
        raise ValueError("non-finite loss gradients")
    main_norm, aux_norm = float(main.norm()), float(aux.norm())
    dot = float(main.dot(aux))
    return {
        "primary_norm": main_norm,
        "auxiliary_norm": aux_norm,
        "primary_dot_auxiliary": dot,
        "cosine": dot / (main_norm * aux_norm) if main_norm and aux_norm else None,
        "weight": weight,
        "primary_dot_combined": float(main.dot(main + weight * aux)),
    }


def a4_fixture() -> dict:
    import torch
    from torch.nn.functional import cross_entropy

    from ekg.relations.pair_evidence import sufficiency_necessity_loss

    theta = torch.tensor(1.0, requires_grad=True)
    zero = theta * 0
    base = torch.stack((zero, 2 * theta, zero)).unsqueeze(0)
    retained = torch.stack((zero, theta, zero)).unsqueeze(0)
    masked = torch.stack((zero, 2 * theta, zero)).unsqueeze(0)
    target = torch.tensor([1])
    auxiliary = sufficiency_necessity_loss(
        base, masked, retained, target, scoreable=torch.tensor([True])
    )
    base_gradient = torch.autograd.grad(auxiliary, base, retain_graph=True)[0]
    return {
        "schema_version": "ekg.a4_gradient_counterexample.v1",
        "diagnostic_only": True,
        "input_kind": "analytic CPU fixture; no trained model or corpus",
        "primary_loss": float(cross_entropy(base, target).detach()),
        "auxiliary_loss": float(auxiliary.detach()),
        "base_logit_gradient": float(base_gradient[0, 1]),
        "alignment": gradient_report(cross_entropy(base, target), auxiliary, [theta], weight=0.5),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = a4_fixture()
    report["script_sha256"] = sha256_file(Path(__file__))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
