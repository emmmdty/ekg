#!/usr/bin/env python
"""Train-only, zero-update cost probe of the published full joint architecture."""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import resource
import subprocess
import sys
import time
from pathlib import Path

from ekg.core.protocol import load_manifest_ids
from ekg.core.stage_bundle import model_content_digest, sha256_file


def validate_device(device, visible, available, host):
    if device == 'cpu':
        if visible not in ('', '-1') or available:
            raise ValueError('CPU execution requires CUDA hidden before importing torch')
    elif (device != 'cuda' or host != 'gpu-4090' or not available
          or visible is None or not visible.isdecimal()):
        raise ValueError('CUDA requires one explicitly selected card on gpu-4090')


def fixture(census, name):
    prefix = {'peak': 'fixed_numpy_rng13_batch8_peak',
              'worst': 'any_eight_docs_worst_case'}[name]
    ids, chunks = census[prefix + '_ids'], census[prefix + '_chunks']
    if len(ids) != 8 or len(set(ids)) != 8 or not isinstance(chunks, int) or chunks < 8:
        raise ValueError('invalid frozen eight-document cost fixture')
    return ids, chunks


def require_empty_gpu(index):
    output = subprocess.check_output([
        'nvidia-smi', '-i', index, '--query-gpu=uuid,memory.used',
        '--format=csv,noheader,nounits'], text=True).strip()
    uuid, memory = [part.strip() for part in output.split(',')]
    processes = subprocess.check_output([
        'nvidia-smi', '--query-compute-apps=gpu_uuid,pid',
        '--format=csv,noheader,nounits'], text=True)
    if int(memory) >= 512 or any(line.split(',')[0].strip() == uuid
                                for line in processes.splitlines()):
        raise ValueError('selected GPU is occupied; do not launch')
    return {'index': index, 'uuid': uuid, 'memory_before_mib': int(memory)}


def set_checkpointing(encoder, enabled):
    if enabled:
        encoder.gradient_checkpointing_enable(
            gradient_checkpointing_kwargs={'use_reentrant': False, 'preserve_rng_state': True})
    else:
        encoder.gradient_checkpointing_disable()


def parameter_digest(model):
    digest = hashlib.sha256()
    for name, parameter in model.named_parameters():
        digest.update(name.encode() + b'\0')
        digest.update(parameter.detach().cpu().contiguous().numpy().tobytes())
    return digest.hexdigest()


def compare_gradients(model, reference, torch):
    actual = {name: p.grad for name, p in model.named_parameters() if p.grad is not None}
    if set(actual) != set(reference):
        raise ValueError('gradient population mismatch')
    maximum, passed = 0., True
    for name, gradient in actual.items():
        current = gradient.detach().cpu()
        if not torch.isfinite(current).all():
            raise ValueError('nonfinite gradient: ' + name)
        maximum = max(maximum, float((current - reference[name]).abs().max()))
        passed &= torch.allclose(current, reference[name], rtol=1e-4, atol=1e-6)
    return {'passed': bool(passed), 'parameters_with_gradient': len(actual),
            'max_absolute_error': maximum, 'rtol': 1e-4, 'atol': 1e-6}


def original_loss(outputs, batch, fill_expand, torch):
    coref, temporal, causal, subevent = outputs
    losses = []
    for probs, clusters in zip(coref, batch['coref_labels'], strict=True):
        labels = fill_expand(clusters).to(probs.device)
        summed = (probs * labels).clamp(1e-8, 1 - 1e-8).sum(dim=1)
        losses.append(-summed.log().mean())
    terms = {'coreference': torch.stack(losses).mean()}
    for key, scores in zip(('temporal', 'causal', 'subevent'),
                           (temporal, causal, subevent), strict=True):
        terms[key] = torch.nn.functional.cross_entropy(
            scores.reshape(-1, scores.shape[-1]), batch[key + '_labels'].reshape(-1),
            ignore_index=-100)
    loss = sum(weight * terms[key] for key, weight in
               zip(terms, (.4, 2., 4., 4.), strict=True))
    if not torch.isfinite(loss):
        raise ValueError('nonfinite original joint loss')
    return loss, {key: float(value.detach()) for key, value in terms.items()}


def execute(config, device, name, output, torch):
    from transformers import RobertaTokenizer

    for path, expected in config['input_sha256'].items():
        if sha256_file(Path(path)) != expected:
            raise ValueError('input hash drift: ' + path)
    pretrained = Path(config['pretrained'])
    if model_content_digest(pretrained) != config['pretrained_digest']:
        raise ValueError('pretrained content drift')
    census = json.loads(Path(config['census']).read_text())
    ids, expected_chunks = fixture(census, name)
    manifest = load_manifest_ids(Path(config['train_manifest']))
    raw = [json.loads(line) for line in Path(config['train_input']).read_text().splitlines()]
    if [r['id'] for r in raw] != manifest or len(manifest) != 2622:
        raise ValueError('full train manifest/order drift')
    raw = {row['id']: row for row in raw}
    if not set(ids) <= raw.keys():
        raise ValueError('fixture outside train manifest')
    source = Path(config['source_root']).resolve()
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(source))
    modules = {key: importlib.import_module('src.' + key)
               for key in ('model', 'data', 'utils')}
    for key, module in modules.items():
        if Path(module.__file__).resolve() != source / 'src' / (key + '.py'):
            raise ValueError('official source resolution drift')
    tokenizer = RobertaTokenizer.from_pretrained(pretrained, local_files_only=True)
    dataset = modules['data'].myDataset.__new__(modules['data'].myDataset)
    dataset.tokenizer, dataset.max_length, dataset.ignore_nonetype = tokenizer, 256, False
    dataset.examples = [modules['data'].Document(raw[doc_id], ignore_nonetype=False)
                        for doc_id in ids]
    dataset.tokenize()
    dataset.to_tensor()
    batch = modules['data'].collator(dataset.tokenized_samples)
    if batch['doc_id'] != ids or batch['input_ids'].shape != (expected_chunks, 256):
        raise ValueError('tokenized fixture drift')
    gpu = require_empty_gpu(os.environ['CUDA_VISIBLE_DEVICES']) if device == 'cuda' else None
    torch.manual_seed(13)
    model = modules['model'].Model(len(tokenizer), model_name=str(pretrained)).to(device)
    model.train()
    batch = {key: value.to(device) if isinstance(value, torch.Tensor) else value
             for key, value in batch.items()}
    before = parameter_digest(model)
    runs, reference = [], None
    for enabled in (False, True):
        model.zero_grad(set_to_none=True)
        set_checkpointing(model.encoder.model.module, enabled)
        torch.manual_seed(13)
        if device == 'cuda':
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
            torch.cuda.reset_peak_memory_stats()
        start = time.perf_counter()
        loss, terms = original_loss(model(batch), batch, modules['utils'].fill_expand, torch)
        if device == 'cuda':
            torch.cuda.synchronize()
        forward = time.perf_counter() - start
        start = time.perf_counter()
        loss.backward()
        if device == 'cuda':
            torch.cuda.synchronize()
        backward = time.perf_counter() - start
        measured = {'checkpointing': enabled, 'loss': float(loss.detach()), 'terms': terms,
                    'forward_seconds': forward, 'backward_seconds': backward,
                    'cpu_process_cumulative_maxrss_kib': resource.getrusage(
                        resource.RUSAGE_SELF).ru_maxrss}
        if device == 'cuda':
            measured.update(cuda_peak_allocated_bytes=torch.cuda.max_memory_allocated(),
                            cuda_peak_reserved_bytes=torch.cuda.max_memory_reserved())
        if reference is None:
            reference = {}
            for key, parameter in model.named_parameters():
                if parameter.grad is not None:
                    if not torch.isfinite(parameter.grad).all():
                        raise ValueError('nonfinite reference gradient: ' + key)
                    reference[key] = parameter.grad.detach().cpu().clone()
        else:
            measured['gradient_parity'] = compare_gradients(model, reference, torch)
            measured['loss_parity'] = abs(runs[0]['loss'] - measured['loss']) <= 1e-6
        if parameter_digest(model) != before:
            raise ValueError('zero-update parameter invariant failed')
        runs.append(measured)
        (output / ('checkpoint_' + str(enabled).lower() + '.json')).write_text(
            json.dumps(measured, indent=2) + '\n')
        del loss
        print(json.dumps(measured), flush=True)
    parameter_bytes = sum(p.numel() * p.element_size() for p in model.parameters())
    return {'status': 'complete' if runs[-1]['gradient_parity']['passed']
            and runs[-1]['loss_parity'] else 'failed',
            'method_admitted': False, 'optimizer_steps': 0, 'final_valid_accessed': False,
            'device': device, 'gpu': gpu, 'seed': 13, 'fixture': name,
            'doc_ids': ids, 'token_chunks': expected_chunks, 'runs': runs,
            'parameter_sha256_before_and_after': before, 'parameter_bytes': parameter_bytes,
            'projected_two_fp32_adam_moments_bytes': 2 * parameter_bytes,
            'optimizer_memory_measured': False, 'torch_version': torch.__version__,
            'limitations': 'Train-only original loss, no optimizer/update/evaluation; CPU RSS is '
            'process cumulative and includes parity buffers. One fixture timing is not epoch '
            'wallclock, and projected moments are not an optimizer peak measurement.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--device', choices=('cpu', 'cuda'), required=True)
    parser.add_argument('--fixture', choices=('peak', 'worst'), required=True)
    args = parser.parse_args()
    import torch

    host = 'gpu-4090' if Path.cwd().resolve() == Path('/data/TJK/ekg') else 'local'
    validate_device(args.device, os.environ.get('CUDA_VISIBLE_DEVICES'),
                    torch.cuda.is_available(), host)
    config = json.loads(args.config.read_text())
    if (config['seed'] != 13 or config['method_admitted'] is not False
            or config['optimizer_steps'] != 0 or config['final_valid_accessed'] is not False):
        raise ValueError('cost probe role/seed drift')
    if sha256_file(Path(__file__)) != config['entrypoint_sha256']:
        raise ValueError('cost probe source drift')
    torch.set_num_threads(4)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.enabled = False
    output = Path(config['output']) / args.device / args.fixture
    output.mkdir(parents=True, exist_ok=False)
    try:
        report = execute(config, args.device, args.fixture, output, torch)
        report['config_sha256'] = sha256_file(args.config)
        report['entrypoint_sha256'] = config['entrypoint_sha256']
        report['input_sha256'] = config['input_sha256']
    except Exception as exc:
        (output / 'failure.json').write_text(json.dumps(
            {'status': 'failed', 'error': repr(exc), 'optimizer_steps': 0}) + '\n')
        raise
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    hashes = {p.name: sha256_file(p) for p in output.iterdir() if p.is_file()}
    (output / 'artifact_hashes.json').write_text(json.dumps(hashes, indent=2) + '\n')
    if report['status'] != 'complete':
        raise ValueError('original/checkpointed loss or gradients differ')


if __name__ == '__main__':
    main()
