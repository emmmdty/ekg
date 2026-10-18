#!/usr/bin/env python
"""Bounded real ERGO cost, original class bodies, complete native candidates, lr=0."""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import math
import os
import resource
import socket
import time
import typing
from pathlib import Path
from types import SimpleNamespace

from ekg.core.stage_bundle import sha256_file
from ekg.relations.ergo_adapter import criss_cross_mask


def load_legacy_adamw(path, expected_sha):
    """Use the pinned original HF class without installing an old entire stack."""
    if sha256_file(path) != expected_sha:
        raise ValueError("legacy optimizer source drift")
    import torch
    from transformers.utils.versions import require_version

    nodes = [n for n in ast.parse(path.read_text()).body
             if isinstance(n, ast.ClassDef) and n.name == "AdamW"]
    if len(nodes) != 1:
        raise ValueError("expected exactly one original AdamW class")
    namespace = {"torch": torch, "nn": torch.nn, "Optimizer": torch.optim.Optimizer,
                 "math": math, **{n: getattr(typing, n) for n in ("Callable", "Iterable", "Tuple")},
                 "require_version": require_version}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), namespace)
    return namespace["AdamW"]


def parameter_identities(model):
    """Compare exact numeric values, counting zero signs without modifying parameters."""
    import numpy as np

    raw, numeric = hashlib.sha256(), hashlib.sha256()
    negative_zeros = 0
    for name, parameter in model.named_parameters():
        values = parameter.detach().cpu().contiguous().numpy().copy()
        header = f"{name}:{values.dtype}:{values.shape}\n".encode()
        raw.update(header)
        numeric.update(header)
        raw.update(values.tobytes())
        negative_zeros += int(np.count_nonzero((values == 0) & np.signbit(values)))
        values[values == 0] = 0.0
        numeric.update(values.tobytes())
    return {"raw_sha256": raw.hexdigest(), "numeric_sha256": numeric.hexdigest(),
            "negative_zero_values": negative_zeros}


def model_inputs(feature, target, device):
    import torch

    heads, tails = feature["t1_pos"], feature["t2_pos"]
    pairs = [(str(a), str(b)) for a, b in zip(heads, tails, strict=True)]
    n = len(feature["mention_ids"])
    if len(target) != len(pairs) or len(pairs) != n * (n - 1):
        raise ValueError("incomplete native candidate population")
    positions = set(heads + tails)
    if len(positions) != n or any(
        not 0 < p < len(feature["enc_input_ids"]) or feature["enc_input_ids"][p] != 50265
        or feature["enc_mask_ids"][p] != 1 for p in positions
    ):
        raise ValueError("event marker identity mismatch")
    return {key: torch.tensor([feature[key]], device=device)
            for key in ("enc_input_ids", "enc_mask_ids", "global_attention_mask")} | {
        "t1_pos": [heads], "t2_pos": [tails], "target": [target],
        "mh_self_attention_mask": criss_cross_mask(pairs).unsqueeze(0).to(device),
    }


def read_document(path, doc_id):
    with path.open() as stream:
        for line in stream:
            row = json.loads(line)
            if row["id"] == doc_id:
                return row
    raise ValueError(f"cost fixture absent: {doc_id}")


def trim_trailing_padding(feature):
    """Remove only verified masked padding; Longformer handles its window padding."""
    keys = ("enc_input_ids", "enc_mask_ids", "global_attention_mask")
    mask = feature["enc_mask_ids"]
    size = sum(mask)
    if (not 2 <= size <= len(mask) or any(len(feature[k]) != len(mask) for k in keys)
            or mask != [1] * size + [0] * (len(mask) - size)
            or feature["enc_input_ids"][size:] != [1] * (len(mask) - size)
            or any(feature["global_attention_mask"][size:])):
        raise ValueError("non-trailing or invalid padding")
    return feature | {key: feature[key][:size] for key in keys}



def execution_feature(feature, config):
    """Dispatch explicit frozen cost versions; canonical v3 never trims its input."""
    modes = {"ekg.ergo_native_cost.v2": ("drop_only_verified_trailing_pad", True),
             "ekg.ergo_native_cost.v3": ("retain_all_4096", False),
             "ekg.ergo_native_cost.v4": ("retain_all_4096", False)}
    if config["schema_version"] not in modes:
        raise ValueError("unknown padding contract version")
    policy, parity = modes[config["schema_version"]]
    if config["padding_policy"] != policy or config["padding_parity_required"] is not parity:
        raise ValueError("inconsistent padding contract")
    return trim_trailing_padding(feature) if parity else feature


def validate_execution_scope(config, case, *, cwd, visible, available, hostname):
    """Bind this bounded CUDA proposal to its actual backup server, not a fake 4090."""
    if (config["schema_version"] != "ekg.ergo_native_cost.v4"
            or config["server"] != "gpu-5090"
            or cwd != "/mnt/aidata/tongjiakai/ekg"
            or hostname != "server-System-Product-Name"
            or visible != "0" or not available or case["device"] != "cuda"
            or config["cuda_admitted"] is not True or config["training_admitted"] is not False):
        raise ValueError("bounded 5090 cost requires its pinned host/root/card and no training")
    return "RTX 5090", "GPU-07af326b-f41d-a706-2150-bc560c7db304"


def run(config_path, case_name):
    import torch
    from profile_original_joint_cost import compare_gradients, require_empty_gpu, validate_device

    config = json.loads(config_path.read_text())
    case = config["cases"][case_name]
    if (config["seed"] != 13
            or config["final_valid_accessed"] is not False
            or config["optimizer_api_calls"] != 2 or config["learning_rate"] != 0.0
            or config["cpu_threads"] != 12):
        raise ValueError("remote frozen zero-lr cost scope required")
    expected_name, expected_uuid = "RTX 4090", None
    if config["schema_version"] == "ekg.ergo_native_cost.v4":
        expected_name, expected_uuid = validate_execution_scope(
            config, case, cwd=str(Path.cwd()), visible=os.environ.get("CUDA_VISIBLE_DEVICES"),
            available=torch.cuda.is_available(), hostname=socket.gethostname())
    else:
        if str(Path.cwd()) != "/data/TJK/ekg":
            raise ValueError("original cost requires the primary server root")
        validate_device(case["device"], os.environ.get("CUDA_VISIBLE_DEVICES"),
                        torch.cuda.is_available(), "gpu-4090")
    gpu = None
    if case["device"] == "cuda":
        if config["cuda_admitted"] is not True:
            raise ValueError("CUDA cost needs a separate admission after the CPU result")
        gpu = require_empty_gpu(os.environ["CUDA_VISIBLE_DEVICES"])
        if (expected_name not in torch.cuda.get_device_name(0)
                or (expected_uuid is not None and gpu["uuid"] != expected_uuid)):
            raise ValueError("pinned GPU model/UUID required")
    output = Path(config["output"]) / case_name
    if output.exists():
        raise FileExistsError(output)
    print(json.dumps({"phase": "verify_inputs", "case": case_name}), flush=True)
    for path, expected in config["pins"].items():
        if sha256_file(Path(path)) != expected:
            raise ValueError(f"cost input/code drift: {path}")
    weights = Path(config["pretrained"])
    if {p.name for p in weights.iterdir()} != set(config["model_files"]):
        raise ValueError("pretrained file-set drift")
    feature = read_document(Path(config["features"]), case["doc_id"])
    target = read_document(Path(config["targets"]), case["doc_id"])["target"]
    if (len(feature["t1_pos"]) != case["pairs"]
            or sum(feature["enc_mask_ids"]) != case["nonpad_tokens"]
            or len(feature["enc_input_ids"]) != 4096):
        raise ValueError("frozen complete fixture dimensions differ")
    model_feature = execution_feature(feature, config)
    output.mkdir(parents=True, exist_ok=False)
    (output / "status.json").write_text(
        json.dumps({"status": "running", "pid": os.getpid()}) + "\n")
    torch.set_num_threads(config["cpu_threads"])
    torch.manual_seed(13)
    torch.backends.cuda.matmul.allow_tf32 = False
    device = torch.device(case["device"])
    source = Path(config["model_source"])
    spec = importlib.util.spec_from_file_location("external_ergo_cost", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    args = SimpleNamespace(**config["model_args"], model_name_or_path=str(weights), device=device)
    print(json.dumps({"phase": "load_original_model", "case": case_name}), flush=True)
    model = module.LongformerCausalModel(args)
    # Old transformers initialized added embeddings independently; retain that policy explicitly.
    model.pretrained_model.resize_token_embeddings(50267, mean_resizing=False)
    model.to(device)
    if any(p.dtype != torch.float32 for p in model.parameters()):
        raise ValueError("full original float32 model required")
    inputs = model_inputs(model_feature, target, device)
    model.eval()
    parity = {"applied": False, "reason": "Canonical complete4096 input retained unchanged."}
    if config["padding_parity_required"]:
        full_inputs = model_inputs(feature, target, device)
        print(json.dumps({"phase": "padding_parity", "case": case_name}), flush=True)
        reference_loss, reference_logits = model(**full_inputs)
        reference_loss.backward()
        gradients = {n: p.grad.detach().cpu().clone() for n, p in model.named_parameters()
                     if p.grad is not None}
        reference_loss = reference_loss.detach().cpu()
        reference_logits = reference_logits.detach().cpu()
        model.zero_grad(set_to_none=True)
        trimmed_loss, trimmed_logits = model(**inputs)
        trimmed_loss.backward()
        parity = compare_gradients(model, gradients, torch)
        parity["loss_absolute_error"] = float((trimmed_loss.detach().cpu() - reference_loss).abs())
        parity["logits_max_absolute_error"] = float(
            (trimmed_logits.detach().cpu() - reference_logits).abs().max())
        if (not parity["passed"] or not torch.allclose(trimmed_loss.detach().cpu(), reference_loss,
                                                      rtol=1e-4, atol=1e-6)
                or not torch.allclose(trimmed_logits.detach().cpu(), reference_logits,
                                      rtol=1e-4, atol=1e-6)):
            raise ValueError(f"padding loss/logits/full-gradient parity failed: {parity}")
        del gradients, reference_loss, reference_logits, trimmed_loss, trimmed_logits, full_inputs
        model.zero_grad(set_to_none=True)
    print(json.dumps({"phase": "target_independence", "case": case_name}), flush=True)
    with torch.no_grad():
        _, first = model(**inputs)
        _, shadow = model(**(inputs | {"target": [[(v + 1) % 3 for v in target]]}))
        if not torch.isfinite(first).all() or not torch.equal(first, shadow):
            raise ValueError("nonfinite or target-dependent model logits")
    del first, shadow
    before = parameter_identities(model)
    adamw = load_legacy_adamw(Path(config["optimizer_source"]),
                             config["pins"][config["optimizer_source"]])
    no_decay = ("bias", "LayerNorm.bias", "LayerNorm.weight")
    groups = [{"params": [p for n, p in model.named_parameters()
                          if not any(v in n for v in no_decay)], "weight_decay": 0.01},
              {"params": [p for n, p in model.named_parameters()
                          if any(v in n for v in no_decay)], "weight_decay": 0.0}]
    optimizer = adamw(groups, lr=0.0, eps=1e-8)
    rows = []
    for step in range(2):
        model.train()
        model.zero_grad(set_to_none=False)
        if case["device"] == "cuda":
            torch.cuda.reset_peak_memory_stats()
            torch.cuda.synchronize()
        print(json.dumps({"phase": "cold" if step == 0 else "warm", "case": case_name}), flush=True)
        start = time.perf_counter()
        loss, logits = model(**inputs)
        if not torch.isfinite(loss) or not torch.isfinite(logits).all():
            raise ValueError("nonfinite original ERGO loss/logits")
        loss.backward()
        if any(not torch.isfinite(p.grad).all() for p in model.parameters() if p.grad is not None):
            raise ValueError("nonfinite full-model gradient")
        norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        if not torch.isfinite(norm):
            raise ValueError("nonfinite gradient norm")
        optimizer.step()
        if case["device"] == "cuda":
            torch.cuda.synchronize()
        seconds = time.perf_counter() - start
        after = parameter_identities(model)
        if before["numeric_sha256"] != after["numeric_sha256"]:
            raise ValueError("parameter numeric values changed at zero lr")
        rows.append({"step": step, "seconds_including_gradient_validation": seconds,
                     "loss": float(loss.detach()), "unclipped_grad_norm": float(norm),
                     "parameter_identity": after,
                     "cuda_peak_allocated": torch.cuda.max_memory_allocated()
                     if case["device"] == "cuda" else None,
                     "cuda_peak_reserved": torch.cuda.max_memory_reserved()
                     if case["device"] == "cuda" else None})
        del loss, logits
    if sha256_file(source) != config["pins"][str(source)]:
        raise ValueError("original source changed during execution")
    weight_file = str(weights / "pytorch_model.bin")
    if sha256_file(Path(weight_file)) != config["pins"][weight_file]:
        raise ValueError("pretrained weights changed during execution")
    report = {"status": "complete", "case": case_name, "fixture": case,
              "config_sha256": sha256_file(config_path), "device": case["device"], "gpu": gpu,
              "torch_version": torch.__version__, "original_classes_unchanged": True,
              "padding_parity": parity, "cpu_threads": config["cpu_threads"],
              "padding_policy": config["padding_policy"],
              "API_input_length": len(model_feature["enc_input_ids"]),
              "Longformer_internal_window_padded_length": (
                  (len(model_feature["enc_input_ids"]) + 511) // 512 * 512),
              "resize_added_embeddings_mean_resizing": False,
              "target_independent_logits": True, "optimizer_api_calls": 2, "nonzero_lr_steps": 0,
              "epoch_count": 0, "parameter_values_unchanged": True,
              "parameter_bytes_unchanged": before["raw_sha256"] == after["raw_sha256"],
              "parameter_before": before, "steps": rows,
              "parameter_count": sum(p.numel() for p in model.parameters()),
              "unused_gradient_names": [n for n, p in model.named_parameters() if p.grad is None],
              "optimizer_state_bytes": sum(v.numel() * v.element_size()
                   for state in optimizer.state.values() for v in state.values()
                   if isinstance(v, torch.Tensor)),
              "cpu_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              "final_valid_accessed": False,
              "limitations": ["Eval gradient parity does not imply equal training dropout streams.",
                              "Fixture cost only, no epoch budget or ERGO performance claim.",
                              "Full epochs and performance remain untested."]}
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    (output / "status.json").write_text(
        json.dumps({"status": "complete", "pid": os.getpid()}) + "\n")
    print(json.dumps(report, indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--case", required=True)
    args = parser.parse_args()
    run(args.config, args.case)


if __name__ == "__main__":
    main()
