#!/usr/bin/env python
"""Matched pair-MLP adaptation for the conventional first-mention dummy target."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from pathlib import Path

import numpy as np

from ekg.core.protocol import load_manifest_ids
from ekg.core.stage_bundle import sha256_file


def antecedent_targets(clusters, mentions, *, corrected):
    flat = [i for cluster in clusters for i in cluster]
    if (any(not cluster for cluster in clusters) or len(flat) != len(set(flat))
            or set(flat) != set(range(mentions))):
        raise ValueError('gold cluster population mismatch')
    labels = [[0] * mentions for _ in range(mentions)]
    for cluster in clusters:
        ordered = sorted(cluster)
        if corrected or len(cluster) == 1:
            labels[ordered[0]][ordered[0]] = 1
        for position, current in enumerate(ordered):
            for earlier in ordered[:position]:
                labels[current][earlier] = 1
    return labels


def typed_probabilities(logits, types, torch):
    if len(logits) != len(types) or any(len(row) != i for i, row in enumerate(logits)):
        raise ValueError('antecedent score population mismatch')
    rows = []
    for j, scores in enumerate(logits):
        if not torch.isfinite(scores).all():
            raise ValueError('nonfinite pair scores')
        legal = torch.tensor([types[i] == types[j] for i in range(j)],
                             device=scores.device, dtype=torch.bool)
        real = scores.masked_fill(~legal, -torch.inf)
        rows.append(torch.softmax(torch.cat((real, scores.new_zeros(1))), dim=0))
    return rows


def marginal_loss(rows, clusters, *, corrected, torch):
    size = len(rows)
    target = rows[0].new_tensor(antecedent_targets(clusters, size, corrected=corrected))
    probs = torch.stack([torch.nn.functional.pad(p, (0, size - len(p)), value=-1000)
                         for p in rows])
    # Preserve the published source's clamp-before-sum convention in both arms.
    return -torch.log(torch.clamp(probs * target, 1e-8, 1 - 1e-8).sum(dim=1)).mean()


def validate_settings(config):
    expected = {'epochs': 5, 'lr': .0003, 'batch_size': 8,
                'arms': ['legacy', 'corrected'], 'encoder_frozen': True}
    if (config['training'] != expected or config['seed'] != 13
            or config['control_only'] is not True or config['method_admitted'] is not False):
        raise ValueError('fixed control budget/role drift')


def pair_logits(head, embed, torch):
    size = len(embed)
    if size == 1:
        return [embed.new_empty(0)]
    current, earlier = zip(*[(j, i) for j in range(size) for i in range(j)], strict=True)
    first, second = embed[list(current)], embed[list(earlier)]
    scores = head.score(torch.cat((first, second, first * second), dim=1)).flatten()
    return [embed.new_empty(0), *torch.split(scores, list(range(1, size)))]


def load_jsonl(path):
    rows = [json.loads(line) for line in Path(path).read_text().splitlines()]
    if len({r['id'] for r in rows}) != len(rows):
        raise ValueError(f'duplicate document ID: {path}')
    return rows


def execute(config, config_sha, stage, torch):
    from export_official_coref_cpu import require_parity
    from replay_typed_coref_control import decode_rows

    source = Path(config['source_root']).resolve()
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(source))
    modules = {name: importlib.import_module('src.' + name) for name in ('model', 'utils')}
    for name, module in modules.items():
        if Path(module.__file__).resolve() != source / 'src' / (name + '.py'):
            raise ValueError('official source resolution drift')
    audit = json.loads(Path(config['interface_report']).read_text())
    if (audit['optimizer_steps'] != 0 or audit['toy_legacy_gradient'][0] != 0
            or audit['toy_corrected_gradient'][0] <= 0):
        raise ValueError('first-dummy root-cause audit not confirmed')
    root = Path(config['output'])
    output = root / stage
    if output.exists():
        raise FileExistsError(output)
    if stage == 'fit':
        smoke = json.loads((root / 'smoke/status.json').read_text())
        if smoke['status'] != 'complete' or smoke['config_sha256'] != config_sha:
            raise ValueError('verified smoke required')
    cache = Path(config['feature_cache'])
    docs = {role: load_jsonl(cache / role / 'documents.jsonl') for role in ('train', 'dev')}
    features = {}
    for role in ('train', 'dev'):
        ids = set(load_manifest_ids(Path(config[role + '_manifest'])))
        if {r['id'] for r in docs[role]} != ids:
            raise ValueError('feature/manifest document mismatch')
        payload = np.load(cache / role / 'features.npz')
        if role == 'dev' and 'labels' in payload.files:
            raise ValueError('dev feature cache must be unlabeled')
        x = payload['features']
        if x.shape[1] != 2307 or not np.isfinite(x).all():
            raise ValueError('feature shape/value drift')
        start = 0
        for row in docs[role]:
            if (row['start'] != start or row['end'] != start + len(row['mentions'])
                    or len(row['types']) != len(row['mentions'])):
                raise ValueError('noncontiguous feature/mention population')
            start = row['end']
        if start != len(x):
            raise ValueError('feature population mismatch')
        features[role] = torch.from_numpy(x[:, :768].copy())
    if {r['id'] for r in docs['train']} & {r['id'] for r in docs['dev']}:
        raise ValueError('train/dev overlap')
    gold = {r['id']: r for r in load_jsonl(config['train_input'])}
    if set(gold) != {r['id'] for r in docs['train']}:
        raise ValueError('train supervision population mismatch')
    clusters = {}
    for row in docs['train']:
        indices = {mid: i for i, mid in enumerate(row['mentions'])}
        if len(indices) != len(row['mentions']):
            raise ValueError('duplicate train mention')
        record = gold[row['id']]
        gold_types = {m['id']: e['type'] for e in record['events'] for m in e['mention']}
        if (set(gold_types) != set(indices)
                or row['types'] != [gold_types[m] for m in row['mentions']]):
            raise ValueError('train mention/type drift')
        groups = [[indices[m['id']] for m in e['mention']] for e in record['events']]
        labels = antecedent_targets(groups, len(indices), corrected=False)
        if labels != modules['utils'].fill_expand(groups).tolist():
            raise ValueError('legacy target/source parity failure')
        clusters[row['id']] = groups
    scores = {r['id']: r for r in load_jsonl(config['scores'])}
    anchor = {r['id']: r for r in load_jsonl(config['typed_predictions'])}
    if set(scores) != set(anchor) or set(scores) != {r['id'] for r in docs['dev']}:
        raise ValueError('dev prediction/feature population mismatch')
    checkpoint = torch.load(config['checkpoint'], map_location='cpu', weights_only=False)
    state = {key.removeprefix('coref_scorer.'): value for key, value in checkpoint['model'].items()
             if key.startswith('coref_scorer.')}
    del checkpoint
    head = modules['model'].CorefPairScorer()
    head.load_state_dict(state, strict=True)
    head.eval()
    with torch.no_grad():
        for row in docs['dev']:
            doc_id = row['id']
            logits = pair_logits(head, features['dev'][row['start']:row['end']], torch)
            if (row['mentions'] != scores[doc_id]['mentions']
                    or [p.tolist() for p in logits] != scores[doc_id]['pair_logits']):
                raise ValueError('full dev raw-logit replay parity failure')
            probs = typed_probabilities(logits, row['types'], torch)
            pred = decode_rows([p.tolist() for p in probs], row['mentions'],
                               modules['utils'].get_predicted_clusters, torch)
            require_parity(anchor[doc_id], pred, row['mentions'])
    output.mkdir(parents=True, exist_ok=False)
    history = {}
    for arm in config['training']['arms']:
        head.load_state_dict(state, strict=True)
        torch.manual_seed(13)
        optimizer = torch.optim.Adam(head.parameters(), lr=.0003)
        train_docs = docs['train'][:8] if stage == 'smoke' else docs['train']
        epochs = 1 if stage == 'smoke' else 5
        history[arm] = []
        for epoch in range(epochs):
            head.train()
            order = torch.randperm(len(train_docs)).tolist()
            total = 0.
            for start in range(0, len(order), 8):
                batch = [train_docs[i] for i in order[start:start + 8]]
                optimizer.zero_grad()
                losses = []
                for row in batch:
                    logits = pair_logits(head, features['train'][row['start']:row['end']], torch)
                    probs = typed_probabilities(logits, row['types'], torch)
                    losses.append(marginal_loss(probs, clusters[row['id']],
                                                corrected=arm == 'corrected', torch=torch))
                loss = torch.stack(losses).mean()
                if not torch.isfinite(loss):
                    raise ValueError('nonfinite control training loss')
                loss.backward()
                optimizer.step()
                total += float(loss.detach()) * len(batch)
            history[arm].append(total / len(train_docs))
            print(f'{arm} epoch {epoch + 1}: loss={history[arm][-1]:.6f}', flush=True)
        head.eval()
        predictions = []
        with torch.no_grad():
            for row in docs['dev']:
                logits = pair_logits(head, features['dev'][row['start']:row['end']], torch)
                probs = typed_probabilities(logits, row['types'], torch)
                pred = decode_rows([p.tolist() for p in probs], row['mentions'],
                                   modules['utils'].get_predicted_clusters, torch)
                predictions.append({**anchor[row['id']], 'coreference': pred})
        arm_root = output / arm
        arm_root.mkdir(exist_ok=False)
        (arm_root / 'predictions.jsonl').write_text(''.join(json.dumps(r, sort_keys=True) + '\n'
                                                        for r in predictions))
        torch.save({'state_dict': head.state_dict(), 'seed': 13, 'final_epoch': epochs},
                   arm_root / 'pair_head.pt')
    (output / 'training.json').write_text(json.dumps(history, indent=2) + '\n')
    status = {'status': 'complete', 'config_sha256': config_sha, 'control_only': True,
              'method_admitted': False, 'seed': 13, 'epochs': epochs, 'train_docs': len(train_docs),
              'dev_docs': len(docs['dev']), 'parity': 'exact full dev logits/typed clusters',
              'encoder_optimizer_steps': 0, 'dev_gold_accessed': False,
              'final_valid_accessed': False,
              'artifact_sha256': {str(p.relative_to(output)): sha256_file(p)
                                 for p in sorted(output.rglob('*')) if p.is_file()}}
    (output / 'status.json').write_text(json.dumps(status, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--stage', required=True, choices=('smoke', 'fit'))
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    validate_settings(config)
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '-1':
        raise ValueError('CPU-only control required')
    if sha256_file(Path(__file__)) != config['entrypoint_sha256']:
        raise ValueError('entrypoint drift')
    for path, expected in config['input_sha256'].items():
        if sha256_file(Path(path)) != expected:
            raise ValueError(f'input hash drift: {path}')
    import torch

    if torch.cuda.is_available():
        raise ValueError('CPU-only control required')
    torch.set_num_threads(4)
    torch.set_num_interop_threads(1)
    execute(config, sha256_file(args.config), args.stage, torch)


if __name__ == '__main__':
    main()
