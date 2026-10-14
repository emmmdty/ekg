#!/usr/bin/env python
"""Authorized 5090 adapter around the immutable original-joint cost implementation."""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import sys
from pathlib import Path

import profile_original_joint_cost as core

from ekg.core.stage_bundle import model_content_digest, sha256_file


def validate_target(config, device, visible, available, cwd):
    expected = {'authorization': 'C41-5090-20261014', 'seed': 13, 'method_admitted': False,
                'optimizer_steps': 0, 'final_valid_accessed': False}
    if any(config.get(key) != value for key, value in expected.items()):
        raise ValueError('authorized cost-only scope drift')
    if str(Path(cwd).resolve()) != '/mnt/aidata/tongjiakai/ekg':
        raise ValueError('authorized target cwd mismatch')
    if device == 'cpu':
        core.validate_device('cpu', visible, available, 'gpu-5090')
    elif device != 'cuda' or not available or visible is None or not visible.isdecimal():
        raise ValueError('one explicitly visible CUDA card required')


def require_cpu_report(report, config_sha):
    if (report['status'] != 'complete' or report['config_sha256'] != config_sha
            or report['device'] != 'cpu'):
        raise ValueError('same-config complete CPU report required')


def verify_inputs(config):
    for path, expected in config['input_sha256'].items():
        if sha256_file(Path(path)) != expected:
            raise ValueError('target input hash drift: ' + path)
    if model_content_digest(Path(config['pretrained'])) != config['pretrained_digest']:
        raise ValueError('target pretrained digest drift')
    if sha256_file(Path(core.__file__)) != config['core_entrypoint_sha256']:
        raise ValueError('sealed core cost source drift')


def tokenization(config, torch):
    from transformers import RobertaTokenizer

    verify_inputs(config)
    source = Path(config['source_root']).resolve()
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(source))
    data = importlib.import_module('src.data')
    if Path(data.__file__).resolve() != source / 'src/data.py':
        raise ValueError('official data source resolution drift')
    tokenizer = RobertaTokenizer.from_pretrained(config['pretrained'], local_files_only=True)
    dataset = data.myDataset(tokenizer, str(Path(config['train_input']).parent), 'train',
                             max_length=256, ignore_nonetype=False)
    ids = json.loads(Path(config['train_manifest']).read_text())['doc_ids']
    if [doc.id for doc in dataset.examples] != ids or len(ids) != 2622:
        raise ValueError('full train ID/order mismatch')
    rows, digest = [], hashlib.sha256()
    for sample in dataset.tokenized_samples:
        projection = {key: value.tolist() if isinstance(value, torch.Tensor) else value
                      for key, value in sample.items()}
        encoded = json.dumps(projection, sort_keys=True, separators=(',', ':')).encode()
        digest.update(encoded + b'\n')
        rows.append({'id': sample['doc_id'],
                     'projection_sha256': hashlib.sha256(encoded).hexdigest(),
                     'chunks': sample['input_ids'].shape[0],
                     'nonpad_tokens': int(sample['attention_mask'].sum())})
    return {'status': 'complete', 'device': 'cpu', 'method_admitted': False,
            'optimizer_steps': 0, 'neural_model_loaded': False, 'final_valid_accessed': False,
            'pretrained_digest': config['pretrained_digest'], 'documents': len(rows),
            'chunks': sum(row['chunks'] for row in rows),
            'nonpad_tokens': sum(row['nonpad_tokens'] for row in rows),
            'full_tokenization_and_training_labels_sha256': digest.hexdigest(), 'rows': rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--mode', choices=('tokenization', 'cpu', 'cuda'), required=True)
    parser.add_argument('--fixture', choices=('peak', 'worst'))
    args = parser.parse_args()
    import torch

    config = json.loads(args.config.read_text())
    config_sha = sha256_file(args.config)
    device = 'cuda' if args.mode == 'cuda' else 'cpu'
    validate_target(config, device, os.environ.get('CUDA_VISIBLE_DEVICES'),
                    torch.cuda.is_available(), Path.cwd())
    verify_inputs(config)
    if sha256_file(Path(__file__)) != config['entrypoint_sha256']:
        raise ValueError('target adapter source drift')
    if args.mode != 'tokenization' and args.fixture is None:
        raise ValueError('cost fixture required')
    torch.set_num_threads(4)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.enabled = False
    root = Path(config['output'])
    output = root / 'tokenization' if args.mode == 'tokenization' else root / device / args.fixture
    if args.mode == 'cuda':
        require_cpu_report(json.loads((root / 'cpu' / args.fixture / 'report.json').read_text()),
                           config_sha)
    output.mkdir(parents=True, exist_ok=False)
    try:
        report = tokenization(config, torch) if args.mode == 'tokenization' else core.execute(
            config, device, args.fixture, output, torch)
        report.update(config_sha256=config_sha, entrypoint_sha256=config['entrypoint_sha256'],
                      core_entrypoint_sha256=config['core_entrypoint_sha256'],
                      authorization=config['authorization'], input_sha256=config['input_sha256'])
        if args.mode == 'tokenization':
            rows = report.pop('rows')
            (output / 'documents.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rows))
        (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    except Exception as exc:
        (output / 'failure.json').write_text(json.dumps(
            {'status': 'failed', 'error': repr(exc), 'optimizer_steps': 0}) + '\n')
        raise
    hashes = {p.name: sha256_file(p) for p in output.iterdir() if p.is_file()}
    (output / 'artifact_hashes.json').write_text(json.dumps(hashes, indent=2) + '\n')
    if report['status'] != 'complete':
        raise ValueError('target original/checkpointed gradients differ')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
