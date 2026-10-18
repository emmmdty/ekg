#!/usr/bin/env python
"""Bounded real ERGO native interface smoke, no epochs or dev gold."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import resource
import socket
import time
from pathlib import Path
from types import SimpleNamespace

from ekg.core.stage_bundle import sha256_file
from ekg.relations.ergo_training import BinaryPrefixMeter, load_linear_scheduler, load_train_epoch


def validate_preflight_environment(*, device, server, cwd, visible, available,
                                   cuda_admitted, authorization_scope):
    roots = {'gpu-4090': '/data/TJK/ekg', 'gpu-5090': '/mnt/aidata/tongjiakai/ekg'}
    if server not in roots or cwd != roots[server]:
        raise ValueError('preflight requires its real remote root')
    if device == 'cpu':
        if server != 'gpu-4090' or visible != '-1' or available:
            raise ValueError('CPU preflight must hide CUDA on primary server')
        return None
    if (device != 'cuda' or not available or cuda_admitted is not True
            or visible not in ({'0'} if server == 'gpu-5090' else {'0','1','2','3'})):
        raise ValueError('CUDA preflight requires one admitted empty card')
    if (server == 'gpu-5090' and authorization_scope not in
            {'ERGO_native_production_smoke', 'ERGO_native_20epochs_seed13'}):
        raise ValueError('new 5090 production scope required; cost permission is insufficient')
    return 'RTX 5090' if server == 'gpu-5090' else 'RTX 4090'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path)
    args = parser.parse_args()
    cfg = json.loads(args.config.read_text())
    if cfg['device'] == 'cuda' and cfg['cuda_admitted'] is not True:
        raise ValueError('CUDA preflight not admitted by cost-only authorization')
    if (cfg['schema_version'] != 'ekg.ergo_native_preflight.v2'
            or cfg['seed'] != 13 or cfg['final_valid_accessed'] is not False):
        raise ValueError('frozen native preflight v2 required; v1 replays use e7de4fa')
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

    scope = None
    if cfg['device'] == 'cuda' and cfg['server'] == 'gpu-5090':
        record = cfg['authorization_record']
        if record not in cfg['pins']:
            raise ValueError('pinned 5090 production authorization required')
        authorization = json.loads(Path(record).read_text())
        if authorization['status'] != 'explicitly_authorized':
            raise ValueError('explicit 5090 production authorization required')
        scope = authorization['scope']
        if socket.gethostname() != 'server-System-Product-Name':
            raise ValueError('actual backup host required')
    name = validate_preflight_environment(
        device=cfg['device'], server=cfg['server'], cwd=str(Path.cwd()),
        visible=os.environ.get('CUDA_VISIBLE_DEVICES'), available=torch.cuda.is_available(),
        cuda_admitted=cfg['cuda_admitted'], authorization_scope=scope)
    gpu = None
    if cfg['device'] == 'cuda':
        from profile_original_joint_cost import require_empty_gpu

        gpu = require_empty_gpu(os.environ['CUDA_VISIBLE_DEVICES'])
        if gpu['uuid'] != cfg['gpu_uuid'] or name not in torch.cuda.get_device_name(0):
            raise ValueError('preflight GPU identity mismatch')
    device = torch.device(cfg['device'])
    is_cuda = cfg['device'] == 'cuda'
    torch.set_num_threads(12)
    torch.manual_seed(13)
    torch.backends.cuda.matmul.allow_tf32 = False
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
        dropout_emb=0.3, y_class=3, model_name_or_path=str(weights), device=device))
    model.pretrained_model.resize_token_embeddings(50267, mean_resizing=False)
    model.to(device)
    if any(p.dtype != torch.float32 for p in model.parameters()):
        raise ValueError('original float32 model required')

    def finite_forward(module, unused, result):
        if any(not torch.isfinite(value).all() for value in result):
            raise ValueError('nonfinite original forward')

    model.register_forward_hook(finite_forward)
    before = parameter_identities(model)
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
    if cfg['device'] == 'cuda':
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.synchronize()
    start = time.perf_counter()
    epoch(SimpleNamespace(device=device, gradient_accumulation_steps=1,
                          max_grad_norm=1., logging_steps=20), model, loader, optimizer, schedule)
    if cfg['device'] == 'cuda':
        torch.cuda.synchronize()
    seconds = time.perf_counter()-start
    after = parameter_identities(model)
    if before['numeric_sha256'] != after['numeric_sha256'] or len(calls) != 2:
        raise ValueError('original-function zero-lr numeric identity/call count failed')
    optimizer_bytes = sum(value.numel()*value.element_size()
        for state in optimizer.state.values() for value in state.values()
        if isinstance(value, torch.Tensor))
    training_peak = ({'cuda_peak_allocated': torch.cuda.max_memory_allocated(),
                      'cuda_peak_reserved': torch.cuda.max_memory_reserved()}
                     if cfg['device'] == 'cuda' else {})
    feature = read_document(Path(cfg['dev_features']), cfg['dev_max']['id'])
    if (len(feature['t1_pos']) != cfg['dev_max']['pairs']
            or sum(feature['enc_mask_ids']) != cfg['dev_max']['nonpad_tokens']
            or len(feature['enc_input_ids']) != 4096):
        raise ValueError('maximum dev complete4096 dimensions differ')
    if cfg['device'] == 'cuda':
        torch.cuda.reset_peak_memory_stats()
    packed = model_inputs(feature, [0]*len(feature['t1_pos']), device)
    print(json.dumps({'phase': 'maximum_unlabeled_dev'}), flush=True)
    model.eval()
    if cfg['device'] == 'cuda':
        torch.cuda.synchronize()
    start = time.perf_counter()
    with torch.no_grad():
        _, reference = model(**packed)
        _, shadow = model(**(packed | {'target': [[1]*len(feature['t1_pos'])]}))
        if not torch.equal(reference, shadow):
            raise ValueError('target-dependent inference logits')
    if cfg['device'] == 'cuda':
        torch.cuda.synchronize()
    capacity = {'status': 'complete', 'device': cfg['device'], 'max_pairs': cfg['dev_max']['pairs'],
                'fixture': cfg['dev_max'], 'gold_accessed': False, 'optimizer_api_calls': 0,
                'target_independent_logits': True, 'API_input_length': 4096,
                'seconds_for_two_forwards': time.perf_counter()-start,
                'config_sha256': sha256_file(args.config),
                'CUDA_capacity_established': is_cuda,
                'gpu': gpu, 'optimizer_state_resident_bytes': optimizer_bytes}
    if cfg['device'] == 'cuda':
        capacity['cuda_peak_allocated'] = torch.cuda.max_memory_allocated()
        capacity['cuda_peak_reserved'] = torch.cuda.max_memory_reserved()
    (output / 'capacity_report.json').write_text(json.dumps(capacity, indent=2)+'\n')
    del reference, shadow, packed
    for name, expected in cfg['pins'].items():
        if sha256_file(Path(name)) != expected:
            raise ValueError(f'source/input changed during preflight: {name}')
    report = {'status': 'complete', 'device': cfg['device'], 'original_train_epoch_unchanged': True,
              'parameter_values_unchanged': True, 'parameter_bytes_unchanged': (
                  before['raw_sha256'] == after['raw_sha256']), 'parameter_before': before,
              'parameter_after': after, 'optimizer_api_calls': len(calls), 'nonzero_lr_steps': 0,
              'native_epochs': 0, 'train_fixtures': cfg['train_fixtures'],
              'training_seconds': seconds,
              'cpu_peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              'unused_gradient_names_per_batch': unused_per_batch,
              'final_valid_accessed': False, 'dev_gold_accessed': False, 'GPU_compute': is_cuda,
              'checkpoint_saved': False, 'predictions_saved': False,
              'config_sha256': sha256_file(args.config),
              'CUDA_production_admitted': is_cuda, 'gpu': gpu,
              'optimizer_state_bytes': optimizer_bytes, **training_peak}
    (output / 'production_report.json').write_text(json.dumps(report, indent=2)+'\n')
    (output / 'status.json').write_text(json.dumps({'status':'complete','pid':os.getpid()})+'\n')
    print(json.dumps({'capacity':capacity,'production':report},indent=2),flush=True)


if __name__ == '__main__':
    main()
