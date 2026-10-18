#!/usr/bin/env python
"""Bounded real ERGO native interface smoke, no epochs or dev gold."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import resource
import time
from pathlib import Path
from types import SimpleNamespace

from ekg.core.stage_bundle import sha256_file
from ekg.relations.ergo_training import BinaryPrefixMeter, load_linear_scheduler, load_train_epoch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path)
    args = parser.parse_args()
    cfg = json.loads(args.config.read_text())
    if cfg['device'] == 'cuda' and cfg['cuda_admitted'] is not True:
        raise ValueError('CUDA preflight not admitted by cost-only authorization')
    if (str(Path.cwd()) != '/data/TJK/ekg' or cfg['device'] != 'cpu'
            or os.environ.get('CUDA_VISIBLE_DEVICES') != '-1'
            or cfg['schema_version'] != 'ekg.ergo_native_preflight.v1'
            or cfg['seed'] != 13 or cfg['final_valid_accessed'] is not False):
        raise ValueError('this frozen preflight is primary-server CPU only')
    for name, expected in cfg['pins'].items():
        if sha256_file(Path(name)) != expected:
            raise ValueError(f'preflight source/input drift: {name}')
    output = Path(cfg['output'])
    if output.exists():
        raise FileExistsError(output)
    import torch
    from profile_ergo_native_cost import (
        load_legacy_adamw,
        model_inputs,
        parameter_identities,
        read_document,
    )
    from train_ergo_native import native_train_batch

    if torch.cuda.is_available():
        raise ValueError('CPU preflight must hide CUDA')
    torch.set_num_threads(12)
    torch.manual_seed(13)
    output.mkdir(parents=True, exist_ok=False)
    (output / 'status.json').write_text(json.dumps({'status': 'running', 'pid': os.getpid()})+'\n')
    weights = Path(cfg['pretrained'])
    if {p.name for p in weights.iterdir()} != set(cfg['model_files']):
        raise ValueError('pretrained file-set drift')
    spec = importlib.util.spec_from_file_location('external_ergo_preflight', cfg['model_source'])
    external = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(external)
    model = external.LongformerCausalModel(SimpleNamespace(
        class_weight=0.75, gamma=2, loss_type='focal', num_heads=4, dropout_att=0.1,
        dropout_emb=0.3, y_class=3, model_name_or_path=str(weights), device=torch.device('cpu')))
    model.pretrained_model.resize_token_embeddings(50267, mean_resizing=False)
    if any(p.dtype != torch.float32 for p in model.parameters()):
        raise ValueError('original float32 model required')

    def finite_forward(module, unused, result):
        if any(not torch.isfinite(value).all() for value in result):
            raise ValueError('nonfinite original forward')

    model.register_forward_hook(finite_forward)
    before = parameter_identities(model)
    feature = read_document(Path(cfg['dev_features']), cfg['dev_max']['id'])
    if (len(feature['t1_pos']) != cfg['dev_max']['pairs']
            or sum(feature['enc_mask_ids']) != cfg['dev_max']['nonpad_tokens']
            or len(feature['enc_input_ids']) != 4096):
        raise ValueError('maximum dev complete4096 dimensions differ')
    packed = model_inputs(feature, [0]*len(feature['t1_pos']), torch.device('cpu'))
    print(json.dumps({'phase': 'maximum_unlabeled_dev'}), flush=True)
    model.eval()
    start = time.perf_counter()
    with torch.no_grad():
        _, reference = model(**packed)
        _, shadow = model(**(packed | {'target': [[1]*len(feature['t1_pos'])]}))
        if not torch.equal(reference, shadow):
            raise ValueError('target-dependent inference logits')
    capacity = {'status': 'complete', 'device': 'cpu', 'max_pairs': cfg['dev_max']['pairs'],
                'fixture': cfg['dev_max'], 'gold_accessed': False, 'optimizer_api_calls': 0,
                'target_independent_logits': True, 'API_input_length': 4096,
                'seconds_for_two_forwards': time.perf_counter()-start,
                'config_sha256': sha256_file(args.config), 'CUDA_capacity_established': False}
    (output / 'capacity_report.json').write_text(json.dumps(capacity, indent=2)+'\n')
    del reference, shadow, packed
    no_decay = ('bias', 'LayerNorm.bias', 'LayerNorm.weight')
    groups = [{'params': [p for n,p in model.named_parameters()
                          if not any(v in n for v in no_decay)], 'weight_decay': 0.01},
              {'params': [p for n,p in model.named_parameters()
                          if any(v in n for v in no_decay)], 'weight_decay': 0.0}]
    source = Path(cfg['optimizer_source'])
    optimizer = load_legacy_adamw(source, cfg['pins'][str(source)])(groups, lr=0., eps=1e-8)
    calls = []
    unused_per_batch = []

    def finite_gradient(opt, unused_args, unused_kwargs):
        if any(group['lr'] != 0. for group in opt.param_groups):
            raise ValueError('zero lr required')
        if any(not torch.isfinite(p.grad).all() for p in model.parameters() if p.grad is not None):
            raise ValueError('nonfinite full-model gradient')
        unused_per_batch.append([n for n,p in model.named_parameters() if p.grad is None])
        calls.append(len(calls)+1)

    optimizer.register_step_pre_hook(finite_gradient)
    schedule = load_linear_scheduler(source, cfg['pins'][str(source)])(
        optimizer, num_warmup_steps=0.2, num_training_steps=2)
    rows = []
    for fixture in cfg['train_fixtures']:
        f = read_document(Path(cfg['train_features']), fixture['id'])
        target = read_document(Path(cfg['train_targets']), fixture['id'])['target']
        if len(f['enc_input_ids']) != 4096 or len(target) != fixture['pairs']:
            raise ValueError('fixed complete train fixture mismatch')
        rows.append((f, target))
    if len(rows) != 2:
        raise ValueError('exactly two original-function lr0 batches required')
    loader = torch.utils.data.DataLoader(rows, batch_size=1, shuffle=False,
                                         collate_fn=native_train_batch, num_workers=0)
    epoch = load_train_epoch(Path(cfg['train_source']), cfg['pins'][cfg['train_source']],
                             BinaryPrefixMeter())
    print(json.dumps({'phase': 'original_train_epoch_two_lr0_batches'}), flush=True)
    start = time.perf_counter()
    epoch(SimpleNamespace(device=torch.device('cpu'), gradient_accumulation_steps=1,
                          max_grad_norm=1., logging_steps=20), model, loader, optimizer, schedule)
    seconds = time.perf_counter()-start
    after = parameter_identities(model)
    if before['numeric_sha256'] != after['numeric_sha256'] or len(calls) != 2:
        raise ValueError('original-function zero-lr numeric identity/call count failed')
    for name, expected in cfg['pins'].items():
        if sha256_file(Path(name)) != expected:
            raise ValueError(f'source/input changed during preflight: {name}')
    report = {'status': 'complete', 'device': 'cpu', 'original_train_epoch_unchanged': True,
              'parameter_values_unchanged': True, 'parameter_bytes_unchanged': (
                  before['raw_sha256'] == after['raw_sha256']), 'parameter_before': before,
              'parameter_after': after, 'optimizer_api_calls': len(calls), 'nonzero_lr_steps': 0,
              'native_epochs': 0, 'train_fixtures': cfg['train_fixtures'],
              'training_seconds': seconds,
              'cpu_peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              'unused_gradient_names_per_batch': unused_per_batch,
              'final_valid_accessed': False, 'dev_gold_accessed': False, 'GPU_compute': False,
              'checkpoint_saved': False, 'predictions_saved': False,
              'config_sha256': sha256_file(args.config), 'CUDA_production_admitted': False}
    (output / 'production_report.json').write_text(json.dumps(report, indent=2)+'\n')
    (output / 'status.json').write_text(json.dumps({'status':'complete','pid':os.getpid()})+'\n')
    print(json.dumps({'capacity':capacity,'production':report},indent=2),flush=True)


if __name__ == '__main__':
    main()
