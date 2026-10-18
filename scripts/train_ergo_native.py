#!/usr/bin/env python
"""Run the pinned external ERGO epoch with native inputs and official dev selection."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import random
import socket
import time
from pathlib import Path
from types import SimpleNamespace

from ekg.core.protocol import load_manifest_ids
from ekg.core.stage_bundle import sha256_file
from ekg.relations.ergo_adapter import export_causal_classes
from ekg.relations.ergo_training import BinaryPrefixMeter, load_linear_scheduler, load_train_epoch
from ekg.relations.maven_ere_official import (
    candidate_population_digest,
    records_by_id,
    validate_official_predictions,
)


def aligned_training_data(features_path, targets_path, manifest_path):
    features = records_by_id(map(json.loads, features_path.read_text().splitlines()),
                             source="features")
    targets = records_by_id(map(json.loads, targets_path.read_text().splitlines()),
                            source="targets")
    ids = load_manifest_ids(manifest_path)
    if set(ids) != set(features) or set(ids) != set(targets):
        raise ValueError("complete train feature/target/manifest coverage required")
    rows = []
    for key in ids:
        feature, target = features[key], targets[key]["target"]
        n = len(feature["mention_ids"])
        if (len(target) != n * (n - 1) or len(feature["t1_pos"]) != len(target)
                or len(feature["t2_pos"]) != len(target)
                or any(type(v) is not int or v not in (0, 1, 2) for v in target)):
            raise ValueError("complete native targets required")
        rows.append((feature, target))
    return rows


def require_production_evidence(cfg):
    reports = [json.loads(Path(name).read_text()) for name in cfg["cost_reports"]]
    if any(r["status"] != "complete" or r["device"] != "cuda" for r in reports):
        raise ValueError("complete CUDA costs required; CPU reports cannot admit training")
    required = {"padding_policy": "retain_all_4096", "parameter_values_unchanged": True,
                "nonzero_lr_steps": 0, "optimizer_api_calls": 2, "epoch_count": 0}
    if (len(reports) != 3 or len(set(cfg["cost_reports"])) != 3
            or {r["case"] for r in reports} != {"cuda_typical", "cuda_worst", "cuda_longest"}
            or any(any(r[k] != v for k, v in required.items()) for r in reports)):
        raise ValueError("all three complete original-input zero-lr costs required")
    cost_config = Path(cfg["cost_config"])
    if (str(cost_config) not in cfg["pins"]
            or json.loads(cost_config.read_text())["server"] != cfg["server"]
            or any(r["config_sha256"] != sha256_file(cost_config) for r in reports)):
        raise ValueError("cost report identity/server mismatch")
    for name in [*cfg["cost_reports"], cfg["dev_capacity_report"], cfg["production_smoke_report"]]:
        if name not in cfg["pins"]:
            raise ValueError("pinned evidence required")
    capacity = json.loads(Path(cfg["dev_capacity_report"]).read_text())
    smoke = json.loads(Path(cfg["production_smoke_report"]).read_text())
    if (capacity["status"] != "complete" or capacity["device"] != "cuda"
            or capacity["max_pairs"] != cfg["dev_max_pairs"]
            or capacity["gold_accessed"] is not False or capacity["optimizer_api_calls"] != 0
            or capacity["target_independent_logits"] is not True):
        raise ValueError("maximum unlabeled dev CUDA capacity required")
    if (smoke["status"] != "complete" or smoke["device"] != "cuda"
            or smoke["original_train_epoch_unchanged"] is not True
            or smoke["parameter_values_unchanged"] is not True
            or smoke["nonzero_lr_steps"] != 0):
        raise ValueError("original-function native CUDA production smoke required")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    args = parser.parse_args()
    cfg = json.loads(args.config.read_text())
    if not all(cfg[k] is True for k in (
            "training_admitted", "budget_admitted", "dev_capacity_admitted")):
        raise ValueError("training not admitted: budget, dev capacity and production gates needed")
    if (cfg["schema_version"] != "ekg.ergo_native_training.v1" or cfg["seed"] != 13
            or cfg["epochs"] != 20 or cfg["learning_rate"] != 2e-5
            or cfg["final_valid_accessed"] is not False):
        raise ValueError("frozen native training contract required")
    roots = {"gpu-4090": "/data/TJK/ekg", "gpu-5090": "/mnt/aidata/tongjiakai/ekg"}
    server = cfg["server"]
    visible = os.environ.get("CUDA_VISIBLE_DEVICES")
    if (server not in roots or str(Path.cwd()) != roots[server]
            or visible not in ({"0"} if server == "gpu-5090" else {"0", "1", "2", "3"})):
        raise ValueError("explicit admitted remote server/root/card required")
    for name, expected in cfg["pins"].items():
        if sha256_file(Path(name)) != expected:
            raise ValueError(f"training input/source drift: {name}")
    require_production_evidence(cfg)
    if cfg["wall_seconds"] <= 0:
        raise ValueError("explicit positive wall budget required")
    if server == "gpu-5090":
        auth = json.loads(Path(cfg["authorization_record"]).read_text())
        if (cfg["authorization_record"] not in cfg["pins"]
                or auth["status"] != "explicitly_authorized"
                or auth["scope"] != "ERGO_native_20epochs_seed13"
                or socket.gethostname() != "server-System-Product-Name"):
            raise ValueError("5090 full training needs its own explicit authorization")
    output = Path(cfg["output"])
    if output.exists():
        raise FileExistsError(output)
    import numpy as np
    import torch
    from prepare_ergo_unlabeled import project_unlabeled
    from profile_ergo_native_cost import load_legacy_adamw, model_inputs
    from profile_original_joint_cost import require_empty_gpu

    if not torch.cuda.is_available():
        raise ValueError("admitted CUDA training requires its selected GPU")
    gpu = require_empty_gpu(visible)
    expected_name = "RTX 5090" if server == "gpu-5090" else "RTX 4090"
    if gpu["uuid"] != cfg["gpu_uuid"] or expected_name not in torch.cuda.get_device_name(0):
        raise ValueError("pinned training GPU identity required")
    train = aligned_training_data(Path(cfg["train_features"]), Path(cfg["train_targets"]),
                                  Path(cfg["train_manifest"]))
    dev_ids = load_manifest_ids(Path(cfg["dev_manifest"]))
    dev = records_by_id(map(json.loads, Path(cfg["dev_features"]).read_text().splitlines()),
                        source="dev features")
    raw = records_by_id((project_unlabeled(json.loads(line)) for line in
                         Path(cfg["dev_raw"]).read_text().splitlines()), source="dev raw")
    gold = records_by_id(map(json.loads, Path(cfg["dev_gold"]).read_text().splitlines()),
                         source="dev gold for scorer only")
    if set(dev_ids) != set(dev) or set(dev) != set(raw) or set(raw) != set(gold):
        raise ValueError("complete dev coverage required")
    digest, population = candidate_population_digest(gold)
    if (digest != cfg["dev_digest"] or population["documents"] != 291 or len(train) != 2622):
        raise ValueError("frozen native split/candidate population required before training")
    raw_digest, _ = candidate_population_digest({
        key: {"events": [{"mention": [m]} for m in value["event_mentions"]],
              "TIMEX": value["TIMEX"]} for key, value in raw.items()})
    if raw_digest != digest:
        raise ValueError("unlabeled/gold dev candidate identity mismatch")
    torch.set_num_threads(12)
    random.seed(13)
    np.random.seed(13)
    torch.manual_seed(13)
    torch.backends.cuda.matmul.allow_tf32 = False
    weights = Path(cfg["pretrained"])
    if {p.name for p in weights.iterdir()} != set(cfg["model_files"]):
        raise ValueError("pretrained file-set drift")
    spec = importlib.util.spec_from_file_location("external_ergo_train", cfg["model_source"])
    external = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(external)
    model = external.LongformerCausalModel(SimpleNamespace(
        class_weight=0.75, gamma=2, loss_type="focal", num_heads=4, dropout_att=0.1,
        dropout_emb=0.3, y_class=3, model_name_or_path=str(weights), device=torch.device("cuda")))
    model.pretrained_model.resize_token_embeddings(50267, mean_resizing=False)
    model.to("cuda")
    if any(p.dtype != torch.float32 for p in model.parameters()):
        raise ValueError("original float32 model required")
    deadline = time.monotonic() + cfg["wall_seconds"]

    def check_forward(module, inputs, result):
        if time.monotonic() > deadline:
            raise TimeoutError("native training wall budget exhausted")
        if any(not torch.isfinite(value).all() for value in result):
            raise ValueError("nonfinite original loss/logits")

    model.register_forward_hook(check_forward)
    no_decay = ("bias", "LayerNorm.bias", "LayerNorm.weight")
    groups = [{"params": [p for n, p in model.named_parameters()
                          if not any(v in n for v in no_decay)], "weight_decay": 0.01},
              {"params": [p for n, p in model.named_parameters()
                          if any(v in n for v in no_decay)], "weight_decay": 0.0}]
    optimizer_source = Path(cfg["optimizer_source"])
    adamw = load_legacy_adamw(optimizer_source, cfg["pins"][str(optimizer_source)])
    optimizer = adamw(groups, lr=2e-5, eps=1e-8)

    def check_gradients(opt, unused_args, unused_kwargs):
        if any(not torch.isfinite(p.grad).all() for p in model.parameters() if p.grad is not None):
            raise ValueError("nonfinite original full-model gradient")

    optimizer.register_step_pre_hook(check_gradients)
    schedule = load_linear_scheduler(optimizer_source, cfg["pins"][str(optimizer_source)])(
        optimizer, num_warmup_steps=len(train) * 20 * 0.1, num_training_steps=len(train) * 20)

    def collate(batch):
        if len(batch) != 1:
            raise ValueError("original batch1 required")
        feature, target = batch[0]
        packed = model_inputs(feature, target, torch.device("cpu"))
        return tuple(packed[key] for key in (
            "enc_input_ids", "enc_mask_ids", "global_attention_mask", "t1_pos", "t2_pos",
            "mh_self_attention_mask", "target"))

    loader = torch.utils.data.DataLoader(
        train, batch_size=1, sampler=torch.utils.data.RandomSampler(train),
        collate_fn=collate, num_workers=0)
    epoch_fn = load_train_epoch(Path(cfg["train_source"]), cfg["pins"][cfg["train_source"]],
                                BinaryPrefixMeter())
    model_args = SimpleNamespace(device=torch.device("cuda"), gradient_accumulation_steps=1,
                                 max_grad_norm=1.0, logging_steps=20)
    spec = importlib.util.spec_from_file_location("native_official_evaluator", cfg["evaluator"])
    evaluator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(evaluator)
    output.mkdir(parents=True, exist_ok=False)
    config_sha = sha256_file(args.config)
    (output / "config.json").write_bytes(args.config.read_bytes())
    (output / "status.json").write_text(json.dumps({
        "status": "running", "pid": os.getpid(), "config_sha256": config_sha,
        "epochs_completed": 0, "server": server}) + "\n")
    best_f1, best_epoch, best_scores = -1.0, None, None
    rows = []
    for epoch in range(1, 21):
        model.zero_grad()
        train_metrics = epoch_fn(model_args, model, loader, optimizer, schedule)
        predictions, classes = {}, []
        model.eval()
        with torch.no_grad():
            for key in dev_ids:
                feature = dev[key]
                _, logits = model(**model_inputs(feature, [0] * len(feature["t1_pos"]),
                                                  torch.device("cuda")))
                labels = logits.argmax(-1).cpu().tolist()
                predictions[key] = export_causal_classes(raw[key], labels)
                classes.append({"id": key, "classes": labels})
        validate_official_predictions(
            gold, predictions, expected_candidate_digest=cfg["dev_digest"])
        scores = evaluator.evaluate(gold, predictions, "causal")
        for name, records in (("predictions", predictions.values()), ("classes", classes)):
            (output / f"epoch-{epoch:02d}-{name}.jsonl").write_text(
                "".join(json.dumps(record, separators=(",", ":")) + "\n" for record in records))
        f1 = scores["causal_f1"]
        if f1 > best_f1:
            best_f1, best_epoch, best_scores = f1, epoch, scores
            checkpoint = output / "best.pt.partial"
            torch.save({"model": model.state_dict(), "epoch": epoch, "config_sha256": config_sha},
                       checkpoint)
            checkpoint.rename(output / "best.pt")
        row = {"epoch": epoch, "upstream_binary_train_log": train_metrics,
               "official_dev_causal": scores, "best_epoch": best_epoch}
        rows.append(row)
        (output / "status.json").write_text(json.dumps(
            {"status": "running", "pid": os.getpid(), "config_sha256": config_sha,
             "epochs_completed": epoch, "rows": rows}, indent=2) + "\n")
        print(json.dumps(row), flush=True)
    # Identity checks after execution; pretrained source is never a trained output.
    for name, expected in cfg["pins"].items():
        if sha256_file(Path(name)) != expected:
            raise ValueError(f"source/input changed during training: {name}")
    if sha256_file(args.config) != config_sha:
        raise ValueError("training configuration changed during execution")
    report = {"status": "complete", "epochs_completed": 20, "seed": 13, "gpu": gpu,
              "config_sha256": config_sha, "best_epoch": best_epoch, "best_scores": best_scores,
              "selection": "strict official internal-dev causal F1; earliest tie",
              "checkpoint": str(output / "best.pt"), "checkpoint_sha256": sha256_file(
                  output / "best.pt"), "server": server, "final_valid_accessed": False,
              "FR_016": "b transparent native adaptation; no published benchmark replication",
              "other_families": "not applicable; placeholders are not guardrail scores"}
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    (output / "status.json").write_text(json.dumps(
        {"status": "complete", "pid": os.getpid(), "epochs_completed": 20}) + "\n")
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
