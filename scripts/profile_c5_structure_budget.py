#!/usr/bin/env python
"""Train-fixture costs of frozen C5 objectives, with real zero-lr optimizer steps."""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib
import json
import os
import sys
import time
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

from ekg.core.stage_bundle import model_content_digest, sha256_file

ARMS = ('marginal', 'root', 'exact', 'mass', 'shuffle')
MATRIX_SOURCE = Path('runs/stages/R1/r1-v63-c5-20261013/training_interface_audit/audit.py')
MATRIX_SHA = '93b7fa097e67c5d2d1338c938ecef0ccbed240625a27701ede174322b0467988'


def validate_scope(config, device, visible, available, cwd):
    required = {'seed': 13, 'probe_lr': 0., 'method_admitted': False,
                'final_valid_accessed': False, 'checkpointing': True}
    if any(config.get(k) != v for k, v in required.items()):
        raise ValueError('fixed zero-update cost scope drift')
    if str(Path(cwd).resolve()) != '/data/TJK/ekg':
        raise ValueError('full model cost allowed only on remote 4090')
    if device == 'cpu':
        if visible != '-1' or available:
            raise ValueError('CPU requires hidden CUDA')
    elif device != 'cuda' or not available or visible is None or not visible.isdecimal():
        raise ValueError('single visible CUDA card required')


def probe_optimizers(encoder_parameters, scorer_parameters, torch):
    # Match published AdamW encoder / Adam scorers. Zero LR is a cost-only change.
    return (torch.optim.AdamW(encoder_parameters, lr=0.),
            torch.optim.Adam(scorer_parameters, lr=0.))


def require_zero_lr(optimizers):
    if any(group['lr'] != 0 for opt in optimizers for group in opt.param_groups):
        raise ValueError('optimizer probe must not train weights')


def optimizer_state_bytes(optimizers):
    return sum(value.numel() * value.element_size() for opt in optimizers
               for state in opt.state.values() for value in state.values()
               if hasattr(value, 'numel'))


@lru_cache(maxsize=1)
def matrix_function(torch):
    if sha256_file(MATRIX_SOURCE) != MATRIX_SHA:
        raise ValueError('audited matrix source drift')
    functions = [node for node in ast.parse(MATRIX_SOURCE.read_text()).body
                 if isinstance(node, ast.FunctionDef) and node.name == 'matrices']
    if len(functions) != 1:
        raise ValueError('unique matrix function required')
    scope = {'torch': torch}
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(MATRIX_SOURCE), 'exec'), scope)
    return scope['matrices']


def auxiliary_loss(rows, clusters, types, doc_id, mids, arm, torch):
    if arm not in ARMS or len(rows) != len(types) or len(rows) != len(mids):
        raise ValueError('objective/population mismatch')
    gold = {i: label for label, group in enumerate(clusters) for i in group}
    if len(gold) != sum(map(len, clusters)) or set(gold) != set(range(len(rows))):
        raise ValueError('gold cluster population mismatch')
    zero = rows[-1].sum() * 0
    if arm == 'marginal':
        return zero
    groups = defaultdict(list)
    for i, kind in enumerate(types):
        groups[kind].append(i)
    predicted, true_positive, positive = zero, zero, 0
    for kind, indices in groups.items():
        local = [rows[j][indices[:pos + 1]] for pos, j in enumerate(indices)]
        c, product = matrix_function(torch)(local)
        lower = torch.tril_indices(len(indices), len(indices), -1, device=c.device)
        exact, root = c[lower[0], lower[1]], product[lower[0], lower[1]]
        if arm == 'exact':
            score = exact
        elif arm == 'root':
            score = root
        elif arm == 'mass':
            denominator, delta = (1 - root).sum(), (exact - root).sum()
            if float(denominator.detach()) == 0:
                if float(delta.detach()) != 0:
                    raise ValueError('zero mass denominator with nonzero delta')
                alpha = denominator * 0
            else:
                alpha = delta / denominator
            score = root + alpha * (1 - root)
        else:
            order = sorted(range(len(indices)), key=lambda i: hashlib.sha256(
                f'seed13|{doc_id}|{kind}|{mids[indices[i]]}'.encode()).hexdigest())
            score = c[order][:, order][lower[0], lower[1]]
        # Gold is CPU metadata; this does not read CUDA indices back to host.
        target = c.new_tensor([gold[indices[j]] == gold[indices[i]]
                               for j in range(len(indices)) for i in range(j)])
        positive += int(target.sum().detach())
        predicted = predicted + score.sum()
        true_positive = true_positive + (score * target).sum()
    return 1 - (2 * true_positive + 1) / (predicted + positive + 1)


def objective(model, batch, documents, records, arm, torch):
    from run_first_dummy_control import marginal_loss, typed_probabilities

    captured = []
    hook = model.coref_scorer.score.register_forward_hook(
        lambda _m, _i, output: captured.append(output))
    try:
        _, temporal, causal, subevent = model(batch)
    finally:
        hook.remove()
    canonical, auxiliary, cursor = [], [], 0
    for doc, record in zip(documents, records, strict=True):
        mids = [doc.events[i]['id'] for i in doc.events_idx]
        mapping = {m['id']: e['type'] for e in record['events'] for m in e['mention']}
        if set(mids) != set(mapping) or len(mids) != len(mapping):
            raise ValueError('mention/type population mismatch')
        n = len(mids)
        if n > 1:
            scores = captured[cursor].flatten()
            cursor += 1
            if len(scores) != n * (n - 1) // 2:
                raise ValueError('pair score population mismatch')
            logits = [scores.new_empty(0), *torch.split(scores, list(range(1, n)))]
        else:
            logits = [temporal.new_empty(0)]
        types = [mapping[mid] for mid in mids]
        rows = typed_probabilities(logits, types, torch)
        canonical.append(marginal_loss(rows, doc.coref_labels, corrected=True, torch=torch))
        auxiliary.append(auxiliary_loss(rows, doc.coref_labels, types, doc.id, mids, arm, torch))
    if cursor != len(captured):
        raise ValueError('unexpected coreference score hook outputs')
    terms = {'marginal': torch.stack(canonical).mean(),
             'auxiliary': torch.stack(auxiliary).mean()}
    for name, scores in zip(('temporal', 'causal', 'subevent'),
                            (temporal, causal, subevent), strict=True):
        terms[name] = torch.nn.functional.cross_entropy(
            scores.reshape(-1, scores.shape[-1]), batch[name + '_labels'].reshape(-1),
            ignore_index=-100)
    loss = .4 * (terms['marginal'] + terms['auxiliary']) + sum(
        weight * terms[name] for name, weight in
        zip(('temporal', 'causal', 'subevent'), (2., 4., 4.), strict=True))
    if not torch.isfinite(loss):
        raise ValueError('nonfinite structured loss')
    return loss, {key: float(value.detach()) for key, value in terms.items()}


def execute(config, device, name, arm, torch):
    from profile_original_joint_cost import (
        fixture,
        parameter_digest,
        require_empty_gpu,
        set_checkpointing,
    )
    from transformers import RobertaTokenizer

    for path, expected in config['input_sha256'].items():
        if sha256_file(Path(path)) != expected:
            raise ValueError('input hash drift: ' + path)
    if model_content_digest(Path(config['pretrained'])) != config['pretrained_digest']:
        raise ValueError('pretrained content drift')
    for kind in ('peak', 'worst'):
        r = json.loads((Path(config['original_cuda']) / kind / 'report.json').read_text())
        if r['status'] != 'complete' or not r['runs'][-1]['gradient_parity']['passed']:
            raise ValueError('original CUDA parity required')
    gpu = require_empty_gpu(os.environ['CUDA_VISIBLE_DEVICES']) if device == 'cuda' else None
    source = Path(config['source_root']).resolve()
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(source))
    modules = {key: importlib.import_module('src.' + key) for key in ('model', 'data')}
    for key, module in modules.items():
        if Path(module.__file__).resolve() != source / 'src' / (key + '.py'):
            raise ValueError('official source resolution mismatch')
    ids, chunks = fixture(json.loads(Path(config['census']).read_text()), name)
    raw = list(map(json.loads, Path(config['train_input']).read_text().splitlines()))
    if [r['id'] for r in raw] != json.loads(Path(config['train_manifest']).read_text())['doc_ids']:
        raise ValueError('train manifest/order mismatch')
    raw = {r['id']: r for r in raw}
    records = [raw[doc_id] for doc_id in ids]
    tokenizer = RobertaTokenizer.from_pretrained(config['pretrained'], local_files_only=True)
    data = modules['data']
    dataset = data.myDataset.__new__(data.myDataset)
    dataset.tokenizer, dataset.max_length, dataset.ignore_nonetype = tokenizer, 256, False
    dataset.examples = [data.Document(r, ignore_nonetype=False) for r in records]
    dataset.tokenize()
    dataset.to_tensor()
    batch = data.collator(dataset.tokenized_samples)
    if batch['input_ids'].shape != (chunks, 256) or batch['doc_id'] != ids:
        raise ValueError('fixture tokenization drift')
    batch = {k: v.to(device) if isinstance(v, torch.Tensor) else v for k, v in batch.items()}
    torch.manual_seed(13)
    model = modules['model'].Model(len(tokenizer), model_name=config['pretrained']).to(device)
    model.train()
    set_checkpointing(model.encoder.model.module, True)
    before = parameter_digest(model)
    optimizers = probe_optimizers(model.encoder.parameters(),
                                 (p for n, p in model.named_parameters()
                                  if not n.startswith('encoder.')), torch)
    runs = []
    for cycle in ('cold', 'warm'):
        require_zero_lr(optimizers)
        torch.manual_seed(13)
        if device == 'cuda':
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
            torch.cuda.reset_peak_memory_stats()
        timings = {}
        start = time.perf_counter()
        loss, terms = objective(model, batch, dataset.examples, records, arm, torch)
        if device == 'cuda':
            torch.cuda.synchronize()
        timings['forward_seconds'] = time.perf_counter() - start
        start = time.perf_counter()
        loss.backward()
        if device == 'cuda':
            torch.cuda.synchronize()
        timings['backward_seconds'] = time.perf_counter() - start
        gradients = [(n, p.grad) for n, p in model.named_parameters() if p.grad is not None]
        if not gradients or not all(torch.isfinite(g).all() for _, g in gradients):
            raise ValueError('missing/nonfinite model gradients')
        start = time.perf_counter()
        for optimizer in optimizers:
            optimizer.step()
        if device == 'cuda':
            torch.cuda.synchronize()
        timings['optimizer_seconds'] = time.perf_counter() - start
        item = {'cycle': cycle, 'loss': float(loss.detach()), 'terms': terms,
                **timings, 'gradient_parameters': len(gradients),
                'optimizer_state_bytes': optimizer_state_bytes(optimizers)}
        if device == 'cuda':
            item.update(cuda_peak_allocated_bytes=torch.cuda.max_memory_allocated(),
                        cuda_peak_reserved_bytes=torch.cuda.max_memory_reserved())
        if parameter_digest(model) != before:
            raise ValueError('zero-lr parameter invariant failed')
        runs.append(item)
        for optimizer in optimizers:
            optimizer.zero_grad(set_to_none=True)
        del loss, gradients
        print(json.dumps(item), flush=True)
    return {'status': 'complete', 'method_admitted': False, 'weight_updates': 0,
            'optimizer_steps_per_optimizer': 2, 'optimizer_api_calls': 4, 'probe_lr': 0.,
            'seed': 13, 'final_valid_accessed': False, 'device': device, 'gpu': gpu,
            'fixture': name, 'arm': arm, 'doc_ids': ids, 'chunks': chunks, 'runs': runs,
            'parameter_sha256_before_and_after': before, 'torch_version': torch.__version__,
            'config_sha256': config['_config_sha256'], 'input_sha256': config['input_sha256'],
            'pretrained_digest': config['pretrained_digest'],
            'script_sha256': sha256_file(Path(__file__)),
            'limitations': 'Two train-fixture cost steps at strictly zero LR; real optimizer '
            'state/temporaries, no weight updates, epoch budget, deployment or method effects.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--device', choices=('cpu', 'cuda'), required=True)
    parser.add_argument('--fixture', choices=('peak', 'worst'), required=True)
    parser.add_argument('--arm', choices=ARMS, required=True)
    args = parser.parse_args()
    import torch

    config = json.loads(args.config.read_text())
    config['_config_sha256'] = sha256_file(args.config)
    validate_scope(config, args.device, os.environ.get('CUDA_VISIBLE_DEVICES'),
                   torch.cuda.is_available(), Path.cwd())
    if sha256_file(Path(__file__)) != config['entrypoint_sha256']:
        raise ValueError('cost source drift')
    torch.set_num_threads(4)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.enabled = False
    output = Path(config['output']) / args.device / args.fixture / args.arm
    output.mkdir(parents=True, exist_ok=False)
    try:
        report = execute(config, args.device, args.fixture, args.arm, torch)
        (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    except Exception as exc:
        (output / 'failure.json').write_text(json.dumps(
            {'status': 'failed', 'error': repr(exc), 'probe_lr': 0.,
             'optimizer_calls_before_failure': 'see execution log'}) + '\n')
        raise
    hashes = {p.name: sha256_file(p) for p in output.iterdir() if p.is_file()}
    (output / 'artifact_hashes.json').write_text(json.dumps(hashes, indent=2) + '\n')


if __name__ == '__main__':
    main()
