#!/usr/bin/env python
"""Fixed-endpoint official joint training with the admitted C41 objective family."""
from __future__ import annotations

import argparse
import importlib
import json
import os
import random
import subprocess
import sys
import time
from pathlib import Path

from ekg.core.joint_connectivity import (
    ARMS,
    connectivity_objectives,
    decode_cached_parents,
    typed_parent_rows,
)
from ekg.core.protocol import load_manifest_ids
from ekg.core.stage_bundle import model_content_digest, sha256_file

TRAINING = {'epochs': 100, 'batch_size': 8, 'accumulation_steps': 4,
            'scorer_lr': .0003, 'encoder_lr': .00002, 'warmup_steps': 200,
            'scheduler_training_steps': 32800, 'max_length': 256,
            'checkpointing': True, 'cpu_threads': 4}


def train_to_endpoint(batches, loss_at, optimizers, scheduler, torch, *, epochs, on_epoch):
    if not batches or (len(batches) * epochs) % 4:
        raise ValueError('microbatch budget must be divisible by four')
    parameters = [p for opt in optimizers for g in opt.param_groups for p in g['params']]
    if any(p.grad is not None for p in parameters):
        raise ValueError('unexpected initial gradients')
    step, updates = 0, 0
    start = time.perf_counter()
    for epoch in range(epochs):
        total = 0.
        for batch in batches:
            loss = loss_at(batch)
            if not torch.isfinite(loss):
                raise ValueError('nonfinite training loss')
            total += float(loss.detach())
            (loss / 4).backward()
            del loss
            step += 1
            if step % 4 == 0:
                gradients = [p.grad for p in parameters if p.grad is not None]
                if not gradients or not all(torch.isfinite(g).all() for g in gradients):
                    raise ValueError('missing/nonfinite training gradients')
                for optimizer in optimizers:
                    optimizer.step()
                scheduler.step()
                for optimizer in optimizers:
                    optimizer.zero_grad(set_to_none=True)
                updates += 1
        on_epoch({'epoch': epoch + 1, 'microbatches': step, 'optimizer_steps': updates,
                  'mean_train_loss': total / len(batches),
                  'elapsed_seconds': time.perf_counter() - start})
    return {'microbatches': step, 'optimizer_steps': updates, 'epochs': epochs}


def forward_with_logits(model, batch):
    captured = []
    handle = model.coref_scorer.score.register_forward_hook(
        lambda _module, _inputs, values: captured.append(values))
    try:
        outputs = model(batch)
    finally:
        handle.remove()
    logits, cursor = [], 0
    for indices in batch['events_idx']:
        n = len(indices)
        if n < 1:
            raise ValueError('empty event population')
        if n > 1:
            scores = captured[cursor].flatten()
            cursor += 1
            if len(scores) != n * (n - 1) // 2:
                raise ValueError('raw pair-score coverage mismatch')
            import torch
            logits.append([scores.new_empty(0), *torch.split(scores, list(range(1, n)))])
        else:
            logits.append([outputs[1].new_empty(0)])
    if cursor != len(captured):
        raise ValueError('unmatched raw pair scores')
    return outputs, logits


def joint_loss(model, batch, documents, records, objective, torch):
    outputs, all_logits = forward_with_logits(model, batch)
    canonical, auxiliary = [], []
    for doc, raw, logits in zip(documents, records, all_logits, strict=True):
        mids = [doc.events[i]['id'] for i in doc.events_idx]
        types = {m['id']: event['type'] for event in raw['events'] for m in event['mention']}
        if set(mids) != set(types) or len(mids) != len(types):
            raise ValueError('train mention/type population mismatch')
        terms = objective(logits, doc.coref_labels, [types[m] for m in mids], doc.id, mids)
        canonical.append(terms['marginal'])
        auxiliary.append(terms['auxiliary'])
    terms = {'marginal': torch.stack(canonical).mean(),
             'auxiliary': torch.stack(auxiliary).mean()}
    for name, scores in zip(('temporal', 'causal', 'subevent'), outputs[1:], strict=True):
        terms[name] = torch.nn.functional.cross_entropy(
            scores.reshape(-1, scores.shape[-1]), batch[name + '_labels'].reshape(-1),
            ignore_index=-100)
    loss = .4 * (terms['marginal'] + terms['auxiliary']) + sum(
        weight * terms[name] for name, weight in
        zip(('temporal', 'causal', 'subevent'), (2., 4., 4.), strict=True))
    return loss, {k: float(v.detach()) for k, v in terms.items()}


def preflight(config, config_sha, stage, device):
    if (config['seed'] != 13 or config['training'] != TRAINING
            or config['arms'] != list(ARMS) or config['design_admitted'] is not True
            or config['final_valid_accessed'] is not False):
        raise ValueError('fixed design/training scope drift')
    if Path.cwd().resolve() != Path('/data/TJK/ekg'):
        raise ValueError('full-model execution allowed only on original 4090')
    if (device == 'cpu') != (stage == 'parity'):
        raise ValueError('CPU is restricted to pre-update parity; smoke/train require CUDA')
    if device == 'cpu' and os.environ.get('CUDA_VISIBLE_DEVICES') != '-1':
        raise ValueError('CPU parity requires hidden CUDA')
    if device == 'cuda' and not os.environ.get('CUDA_VISIBLE_DEVICES', '').isdecimal():
        raise ValueError('single visible CUDA card required')
    for path, expected in config['input_sha256'].items():
        if sha256_file(Path(path)) != expected:
            raise ValueError('contract/input/source drift: ' + path)
    if sha256_file(Path(__file__)) != config['entrypoint_sha256']:
        raise ValueError('production entrypoint drift')
    if model_content_digest(Path(config['pretrained'])) != config['pretrained_digest']:
        raise ValueError('initializer drift')
    if stage in ('smoke', 'train'):
        from export_official_coref_cpu import require_smoke

        require_smoke(Path(config['output']) / 'parity/all', config_sha)
    if stage == 'train':
        for arm in ARMS:
            root = Path(config['output']) / 'smoke' / arm
            require_smoke(root, config_sha)
            report = json.loads((root / 'report.json').read_text())
            if (report['optimizer_steps'] != 1 or report['zero_lr_hooks_used']
                    or report['cpu_cache_replay_and_source_decoder_parity'] is not True):
                raise ValueError('valid nonzero-LR full export smoke required')
        admission = json.loads(Path(config['admission']).read_text())
        if (admission['method_admitted'] is not True or admission['config_sha256'] != config_sha
                or not admission['code_sha256'] == config['code_sha256']):
            raise ValueError('matching final method admission required')
        for path, expected in admission['smoke_sha256'].items():
            if sha256_file(Path(path)) != expected:
                raise ValueError('production smoke evidence drift')
    for path, expected in config['code_sha256'].items():
        if sha256_file(Path(path)) != expected:
            raise ValueError('production code drift: ' + path)


def prepare(config, torch):
    import numpy as np
    from transformers import RobertaTokenizer

    torch.set_num_threads(4)
    np.random.seed(13)
    random.seed(13)
    torch.manual_seed(13)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.enabled = False
    source = Path(config['source_root']).resolve()
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(source))
    modules = {name: importlib.import_module('src.' + name)
               for name in ('model', 'data', 'utils', 'dump_result')}
    for name, module in modules.items():
        if Path(module.__file__).resolve() != source / 'src' / (name + '.py'):
            raise ValueError('official source resolution mismatch')
    tokenizer = RobertaTokenizer.from_pretrained(config['pretrained'], local_files_only=True)
    raw = list(map(json.loads, Path(config['train_input']).read_text().splitlines()))
    expected = load_manifest_ids(Path(config['train_manifest']))
    if [r['id'] for r in raw] != expected or len(raw) != 2622:
        raise ValueError('full train manifest/order mismatch')
    return modules, tokenizer, {r['id']: r for r in raw}


def fixture_batch(config, name, modules, tokenizer, records):
    shape = json.loads(Path(config['shape_report']).read_text())['fixtures'][name]
    selected = [records[doc_id] for doc_id in shape['doc_ids']]
    data = modules['data']
    dataset = data.myDataset.__new__(data.myDataset)
    dataset.tokenizer, dataset.max_length, dataset.ignore_nonetype = tokenizer, 256, False
    dataset.examples = [data.Document(r, ignore_nonetype=False) for r in selected]
    dataset.tokenize()
    dataset.to_tensor()
    batch = data.collator(dataset.tokenized_samples)
    if batch['input_ids'].shape != (shape['chunks'], 256):
        raise ValueError('smoke fixture tokenization drift')
    return batch, dataset.examples, selected


def move_batch(batch, device, torch):
    return {k: v.to(device) if isinstance(v, torch.Tensor) else v for k, v in batch.items()}


def parity(config, modules, tokenizer, records, torch):
    import profile_c5_structure_budget as research
    from profile_original_joint_cost import compare_gradients, parameter_digest, set_checkpointing

    batch, documents, selected = fixture_batch(config, 'peak', modules, tokenizer, records)
    model = modules['model'].Model(len(tokenizer), model_name=config['pretrained'])
    model.train()
    set_checkpointing(model.encoder.model.module, True)
    before = parameter_digest(model)
    rows = []
    for arm in ARMS:
        reference, terms = None, None
        for implementation in ('research', 'production'):
            model.zero_grad(set_to_none=True)
            torch.manual_seed(13)
            if implementation == 'research':
                loss, terms = research.objective(model, batch, documents, selected, arm, torch)
                loss.backward()
                reference = {n: p.grad.detach().clone() for n, p in model.named_parameters()
                             if p.grad is not None}
                expected_loss = float(loss.detach())
            else:
                objective = connectivity_objectives.create('forest_pair', arm=arm)
                loss, actual_terms = joint_loss(model, batch, documents, selected, objective, torch)
                loss.backward()
                gradients = compare_gradients(model, reference, torch)
                if actual_terms != terms or float(loss.detach()) != expected_loss:
                    raise ValueError('production loss/term parity failed')
                if not gradients['passed']:
                    raise ValueError('production all-parameter gradient parity failed')
                rows.append({'arm': arm, 'loss': expected_loss, 'gradient_parity': gradients})
            del loss
    if parameter_digest(model) != before:
        raise ValueError('CPU parity changed model parameters')
    return {'status': 'complete', 'weight_updates': 0, 'arms': rows,
            'parameter_sha256_before_and_after': before, 'final_valid_accessed': False}


def fit(config, arm, stage, output, modules, tokenizer, records, torch):
    from profile_original_joint_cost import parameter_digest, require_empty_gpu, set_checkpointing
    from transformers import get_linear_schedule_with_warmup

    gpu = require_empty_gpu(os.environ['CUDA_VISIBLE_DEVICES'])
    model = modules['model'].Model(len(tokenizer), model_name=config['pretrained']).cuda()
    model.train()
    set_checkpointing(model.encoder.model.module, True)
    before = parameter_digest(model)
    scorer = torch.optim.Adam((p for n, p in model.named_parameters()
                              if not n.startswith('encoder.')), lr=.0003)
    encoder = torch.optim.AdamW(model.encoder.parameters(), lr=.00002)
    optimizers = [scorer, encoder]
    scheduler = get_linear_schedule_with_warmup(encoder, num_warmup_steps=200,
                                              num_training_steps=32800)
    objective = connectivity_objectives.create('forest_pair', arm=arm)
    if stage == 'smoke':
        batches = [fixture_batch(config, name, modules, tokenizer, records)
                   for name in ('peak', 'worst', 'relation_envelope', 'structure_envelope')]
        epochs = 1
    else:
        data = modules['data']
        batches = data.get_dataloader(
            tokenizer, 'train', data_dir=str(Path(config['train_input']).parent),
            max_length=256, batch_size=8, shuffle=True, ignore_nonetype=False)
        if len(batches) != 328:
            raise ValueError('full train dataloader budget drift')
        if [d.id for d in batches.dataset.examples] != list(records):
            raise ValueError('training dataset population/order drift')
        documents = {d.id: d for d in batches.dataset.examples}
        epochs = 100

    def loss_at(item):
        model.train()
        if stage == 'smoke':
            batch, docs, selected = item
        else:
            batch = item
            docs = [documents[doc_id] for doc_id in batch['doc_id']]
            selected = [records[doc_id] for doc_id in batch['doc_id']]
        batch = move_batch(batch, 'cuda', torch)
        return joint_loss(model, batch, docs, selected, objective, torch)[0]

    def on_epoch(row):
        with (output / 'training.jsonl').open('a') as stream:
            stream.write(json.dumps(row) + '\n')
        print(json.dumps(row), flush=True)

    result = train_to_endpoint(batches, loss_at, optimizers, scheduler, torch,
                               epochs=epochs, on_epoch=on_epoch)
    torch.cuda.synchronize()
    after = parameter_digest(model)
    if before == after or scheduler.last_epoch != result['optimizer_steps']:
        raise ValueError('weight update/scheduler smoke or endpoint failed')
    result.update(status='complete', arm=arm, stage=stage, gpu=gpu,
                  parameter_sha256_before=before, parameter_sha256_after=after,
                  cuda_peak_allocated_bytes=torch.cuda.max_memory_allocated(),
                  cuda_peak_reserved_bytes=torch.cuda.max_memory_reserved(),
                  final_valid_accessed=False, zero_lr_hooks_used=False,
                  method_admitted=(stage == 'train'))
    if stage == 'train':
        checkpoint = output / 'checkpoint.pt'
        torch.save({'model': model.state_dict(), 'scorer_optimizer': scorer.state_dict(),
                    'encoder_optimizer': encoder.state_dict(), 'scheduler': scheduler.state_dict(),
                    'endpoint': result, 'seed': 13}, checkpoint)
        result['checkpoint_sha256'] = sha256_file(checkpoint)
        ids = set(load_manifest_ids(Path(config['dev_manifest'])))
        if ids & set(records):
            raise ValueError('train/dev overlap')
        export_predictions(config['dev_input'], ids, config['candidate_digest'],
                           model, output, modules, tokenizer, torch)
    else:
        from export_official_coref_cpu import input_population

        projected = project_unlabeled(batches[0][2])
        smoke_dir = output / 'train_smoke_input'
        smoke_dir.mkdir(exist_ok=False)
        smoke_input = smoke_dir / 'test.jsonl'
        smoke_input.write_text(''.join(json.dumps(row) + '\n' for row in projected))
        mapping = {row['id']: row for row in projected}
        digest = input_population(mapping)['candidate_id_digest']
        export_predictions(str(smoke_input), set(mapping), digest, model, output,
                           modules, tokenizer, torch)
    result['cpu_cache_replay_and_source_decoder_parity'] = True
    return result


def project_unlabeled(records):
    return [{'id': raw['id'], 'tokens': raw['tokens'], 'TIMEX': raw['TIMEX'],
             'event_mentions': [{**{k: v for k, v in mention.items() if k != 'eid'},
                                 'type': event['type']}
                                for event in raw['events'] for mention in event['mention']]}
            for raw in records]


def export_predictions(input_path, ids, candidate_digest, model, output, modules, tokenizer, torch):
    from export_official_coref_cpu import input_population, validate_records

    raw = list(map(json.loads, Path(input_path).read_text().splitlines()))
    records = validate_records(raw, ids)
    if input_population(records)['candidate_id_digest'] != candidate_digest:
        raise ValueError('endpoint full candidate population drift')
    data = modules['data']
    batches = data.get_dataloader(
        tokenizer, 'test', data_dir=str(Path(input_path).parent),
        max_length=256, batch_size=8, shuffle=False, ignore_nonetype=False)
    coref, relations = [], {name: [] for name in ('temporal', 'causal', 'subevent')}
    seen = set()
    model.eval()
    with (output / 'scores.jsonl').open('x') as cache, torch.no_grad():
        for batch in batches:
            active = move_batch(batch, 'cuda', torch)
            outputs, all_logits = forward_with_logits(model, active)
            for i, (doc_id, logits) in enumerate(zip(batch['doc_id'], all_logits, strict=True)):
                if doc_id in seen:
                    raise ValueError('duplicate endpoint document')
                seen.add(doc_id)
                events = modules['dump_result'].CorefDocument(records[doc_id]).events
                mids = [event['id'] for event in events]
                types = [event['type'] for event in events]
                rows = typed_parent_rows(logits, types)
                cached = [p.cpu().tolist() for p in rows]
                clusters = decode_cached_parents(mids, cached, types)
                matrix = torch.full((len(mids), len(mids)), -1000., dtype=torch.float32)
                for j, row in enumerate(cached):
                    matrix[j, :j + 1] = torch.tensor(row)
                original, _ = modules['utils'].get_predicted_clusters(matrix)
                original = sorted(sorted(mids[j] for j in group) for group in original
                                  if len(group) > 1)
                if clusters != original:
                    raise ValueError('CPU cached-parent/source decoder parity failed')
                index = {mid: j for j, mid in enumerate(mids)}
                coref.append({'doc_id': doc_id,
                              'clusters': [[index[mid] for mid in group] for group in clusters]})
                cache.write(json.dumps({'id': doc_id, 'mentions': mids, 'types': types,
                                        'pair_logits': [p.cpu().tolist() for p in logits],
                                        'probabilities': cached}, allow_nan=False) + '\n')
                for name, scores in zip(relations, outputs[1:], strict=True):
                    labels = batch[name + '_labels'][i]
                    predictions = scores[i].argmax(-1).cpu()
                    relations[name].append({'doc_id': doc_id,
                                             'preds': predictions[labels >= 0].tolist()})
    if seen != ids:
        raise ValueError('incomplete endpoint document coverage')
    predictions = {}
    dump = modules['dump_result']
    dump.coref_dump(input_path, coref, predictions)
    for name in relations:
        getattr(dump, name + '_dump')(input_path, relations[name], predictions)
    if set(predictions) != ids:
        raise ValueError('incomplete official prediction export')
    (output / 'predictions.jsonl').write_text(''.join(
        json.dumps(predictions[doc_id]) + '\n' for doc_id in sorted(predictions)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--stage', choices=('parity', 'smoke', 'train'), required=True)
    parser.add_argument('--arm', choices=ARMS, default='exact')
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    config_sha = sha256_file(args.config)
    device = 'cpu' if args.stage == 'parity' else 'cuda'
    preflight(config, config_sha, args.stage, device)
    print(json.dumps({'preflight': 'pass', 'stage': args.stage, 'arm': args.arm}), flush=True)
    if not args.execute:
        return
    import torch

    if (device == 'cpu' and torch.cuda.is_available()
            or device == 'cuda' and not torch.cuda.is_available()):
        raise ValueError('requested execution device unavailable or not hidden')
    output = Path(config['output']) / args.stage / ('all' if args.stage == 'parity' else args.arm)
    output.mkdir(parents=True, exist_ok=False)
    status = {'status': 'running', 'pid': os.getpid(), 'stage': args.stage, 'arm': args.arm,
              'config_sha256': config_sha, 'commit': subprocess.check_output(
                  ['git', 'rev-parse', 'HEAD'], text=True).strip(),
              'final_valid_accessed': False, 'torch_version': torch.__version__}
    (output / 'status.json').write_text(json.dumps(status, indent=2) + '\n')
    try:
        modules, tokenizer, records = prepare(config, torch)
        if args.stage == 'parity':
            result = parity(config, modules, tokenizer, records, torch)
        else:
            result = fit(config, args.arm, args.stage, output, modules, tokenizer, records, torch)
        result['config_sha256'] = config_sha
        (output / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
        artifacts = {str(p.relative_to(output)): sha256_file(p)
                     for p in output.rglob('*') if p.is_file() and p.name != 'status.json'}
        status.update(status='complete', artifact_sha256=artifacts)
    except Exception as exc:
        status.update(status='failed', error=repr(exc))
        raise
    finally:
        (output / 'status.json').write_text(json.dumps(status, indent=2) + '\n')


if __name__ == '__main__':
    main()
