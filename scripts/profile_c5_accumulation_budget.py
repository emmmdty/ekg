#!/usr/bin/env python
"""Zero-update C5 costs with real four-microbatch accumulation and shape envelopes."""
from __future__ import annotations

import argparse
import importlib
import json
import os
import resource
import sys
import time
from pathlib import Path

from ekg.core.stage_bundle import model_content_digest, sha256_file


def accumulate_cycle(loss_at, optimizers, scheduler, torch, device):
    """Match historical global-step cadence, releasing each graph after backward."""
    parameters = [p for opt in optimizers for group in opt.param_groups for p in group['params']]
    if any(group['lr'] != 0 for opt in optimizers for group in opt.param_groups):
        raise ValueError('zero learning rate required')
    if any(p.grad is not None for p in parameters):
        raise ValueError('clean gradients required at cycle boundary')

    def synchronize():
        if device == 'cuda':
            torch.cuda.synchronize()

    microbatches = []
    for index in range(4):
        synchronize()
        if device == 'cuda':
            torch.cuda.reset_peak_memory_stats()
        start = time.perf_counter()
        loss = loss_at(index)
        if not torch.isfinite(loss):
            raise ValueError('nonfinite accumulation loss')
        value = float(loss.detach())
        (loss / 4).backward()
        synchronize()
        elapsed = time.perf_counter() - start
        del loss
        gradients = [p.grad for p in parameters if p.grad is not None]
        if not gradients or not all(torch.isfinite(g).all() for g in gradients):
            raise ValueError('missing/nonfinite accumulation gradients')
        row = {'index': index, 'loss': value, 'forward_backward_seconds': elapsed,
               'gradient_parameters': len(gradients),
               'gradient_bytes': sum(g.numel() * g.element_size() for g in gradients)}
        if device == 'cuda':
            row.update(cuda_peak_allocated_bytes=torch.cuda.max_memory_allocated(),
                       cuda_peak_reserved_bytes=torch.cuda.max_memory_reserved())
        microbatches.append(row)
    synchronize()
    start = time.perf_counter()
    for optimizer in optimizers:
        optimizer.step()
    scheduler.step()
    synchronize()
    optimizer_seconds = time.perf_counter() - start
    state_bytes = sum(v.numel() * v.element_size() for opt in optimizers
                      for state in opt.state.values() for v in state.values()
                      if isinstance(v, torch.Tensor))
    optimizer_peak = {}
    if device == 'cuda':
        optimizer_peak = {'cuda_peak_allocated_bytes': torch.cuda.max_memory_allocated(),
                          'cuda_peak_reserved_bytes': torch.cuda.max_memory_reserved()}
    for optimizer in optimizers:
        optimizer.zero_grad(set_to_none=True)
    return {'loss': sum(r['loss'] for r in microbatches) / 4, 'microbatches': microbatches,
            'optimizer_seconds_including_integrity': optimizer_seconds,
            'optimizer_state_bytes': state_bytes, 'optimizer_peak': optimizer_peak}


def execute(config, arm, device, torch):
    import profile_c5_structure_budget as core
    from profile_c5_structure_budget_r2 import attach_integrity_hooks
    from profile_original_joint_cost import parameter_digest, require_empty_gpu, set_checkpointing
    from transformers import RobertaTokenizer, get_linear_schedule_with_warmup

    execution_start = time.perf_counter()
    budget = json.loads(Path(config['budget_config']).read_text())
    core.validate_scope(budget, device, os.environ.get('CUDA_VISIBLE_DEVICES'),
                        torch.cuda.is_available(), Path.cwd())
    for path, expected in {**budget['input_sha256'], **config['input_sha256']}.items():
        if sha256_file(Path(path)) != expected:
            raise ValueError('input/source drift: ' + path)
    if model_content_digest(Path(budget['pretrained'])) != budget['pretrained_digest']:
        raise ValueError('initializer drift')
    gpu = require_empty_gpu(os.environ['CUDA_VISIBLE_DEVICES']) if device == 'cuda' else None
    shape = json.loads(Path(config['shape_report']).read_text())
    source = Path(budget['source_root']).resolve()
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(source))
    model_module = importlib.import_module('src.model')
    data = importlib.import_module('src.data')
    if Path(model_module.__file__).resolve() != source / 'src/model.py':
        raise ValueError('official model resolution mismatch')
    if Path(data.__file__).resolve() != source / 'src/data.py':
        raise ValueError('official data resolution mismatch')
    records = list(map(json.loads, Path(budget['train_input']).read_text().splitlines()))
    expected_ids = json.loads(Path(budget['train_manifest']).read_text())['doc_ids']
    if [r['id'] for r in records] != expected_ids:
        raise ValueError('train order mismatch')
    lookup = {r['id']: r for r in records}
    tokenizer = RobertaTokenizer.from_pretrained(budget['pretrained'], local_files_only=True)
    fixtures = []
    input_io_seconds = time.perf_counter() - execution_start
    setup_start = time.perf_counter()
    for name in config['fixture_order']:
        description = shape['fixtures'][name]
        selected = [lookup[doc_id] for doc_id in description['doc_ids']]
        dataset = data.myDataset.__new__(data.myDataset)
        dataset.tokenizer, dataset.max_length, dataset.ignore_nonetype = tokenizer, 256, False
        dataset.examples = [data.Document(r, ignore_nonetype=False) for r in selected]
        dataset.tokenize()
        dataset.to_tensor()
        batch = data.collator(dataset.tokenized_samples)
        if batch['input_ids'].shape != (description['chunks'], 256):
            raise ValueError('fixture chunk drift')
        expected_pairs = description['max_relation_pairs']
        if any(batch[k + '_labels'].shape != (8, expected_pairs)
               for k in ('temporal', 'causal', 'subevent')):
            raise ValueError('fixture relation shape drift')
        fixtures.append((name, batch, dataset.examples, selected))
    torch.manual_seed(13)
    model = model_module.Model(len(tokenizer), model_name=budget['pretrained']).to(device)
    model.train()
    set_checkpointing(model.encoder.model.module, True)
    encoder, scorers = core.probe_optimizers(model.encoder.parameters(),
        (p for n, p in model.named_parameters() if not n.startswith('encoder.')), torch)
    optimizers = [scorers, encoder]
    scheduler = get_linear_schedule_with_warmup(encoder, num_warmup_steps=200,
                                              num_training_steps=32800)
    receipts = attach_integrity_hooks(optimizers, torch)
    before = parameter_digest(model)
    setup_seconds = time.perf_counter() - setup_start
    runs = []
    for cycle in ('cold', 'warm'):
        transfers = []

        def loss_at(index, transfers=transfers):
            _, batch, documents, selected = fixtures[index]
            start = time.perf_counter()
            active = {k: v.to(device) if isinstance(v, torch.Tensor) else v
                      for k, v in batch.items()}
            if device == 'cuda':
                torch.cuda.synchronize()
            transfers.append(time.perf_counter() - start)
            loss, _ = core.objective(model, active, documents, selected, arm, torch)
            return loss

        run = accumulate_cycle(loss_at, optimizers, scheduler, torch, device)
        overhead = sum(r['integrity_seconds'] for r in receipts[-2:])
        run.update(cycle=cycle, integrity_seconds=overhead,
                   optimizer_seconds=run['optimizer_seconds_including_integrity'] - overhead,
                   transfer_seconds=transfers, scheduler_last_epoch=scheduler.last_epoch,
                   cpu_process_cumulative_maxrss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        if run['optimizer_seconds'] < 0 or parameter_digest(model) != before:
            raise ValueError('timing/zero-update integrity failed')
        runs.append(run)
        print(json.dumps(run), flush=True)
    if len(receipts) != 4 or scheduler.last_epoch != 2:
        raise ValueError('optimizer/scheduler cadence mismatch')
    return {'status': 'complete', 'method_admitted': False, 'final_valid_accessed': False,
            'weight_updates': 0, 'seed': 13, 'probe_lr': 0., 'arm': arm, 'device': device,
            'gpu': gpu, 'torch_version': torch.__version__, 'runs': runs,
            'integrity_receipts': receipts, 'parameter_sha256_before_and_after': before,
            'fixtures': shape['fixtures'], 'setup_seconds': setup_seconds,
            'input_validation_and_read_seconds': input_io_seconds,
            'total_execute_seconds': time.perf_counter() - execution_start,
            'script_sha256': sha256_file(Path(__file__)),
            'limitations': 'Two four-microbatch zero-LR cycles, shape envelopes not an epoch. '
            'Integrity CPU snapshots/signed-zero work separately timed. No learning or evaluation.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--device', choices=('cpu', 'cuda'), required=True)
    parser.add_argument('--arm', choices=('marginal', 'root', 'exact', 'mass', 'shuffle'),
                        required=True)
    args = parser.parse_args()
    import torch

    config = json.loads(args.config.read_text())
    if (config['seed'] != 13 or config['probe_lr'] != 0. or config['method_admitted']
            or config['final_valid_accessed'] or config['fixture_order'] !=
            ['peak', 'worst', 'relation_envelope', 'structure_envelope']):
        raise ValueError('fixed accumulation scope drift')
    if sha256_file(Path(__file__)) != config['entrypoint_sha256']:
        raise ValueError('entrypoint drift')
    output = Path(config['output']) / args.device / args.arm
    output.mkdir(parents=True, exist_ok=False)
    torch.set_num_threads(4)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.enabled = False
    try:
        report = execute(config, args.arm, args.device, torch)
        report['config_sha256'] = sha256_file(args.config)
        report['input_sha256'] = config['input_sha256']
        (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    except Exception as exc:
        failure = {'status': 'failed', 'error': repr(exc)}
        (output / 'failure.json').write_text(json.dumps(failure) + '\n')
        raise
    hashes = {p.name: sha256_file(p) for p in output.iterdir() if p.is_file()}
    (output / 'artifact_hashes.json').write_text(json.dumps(hashes, indent=2) + '\n')


if __name__ == '__main__':
    main()
