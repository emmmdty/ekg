#!/usr/bin/env python
"""Train-only anaphoricity controls on immutable official representations."""

from __future__ import annotations

import argparse
import importlib
import json
import math
import os
import random
import sys
from pathlib import Path

import numpy as np

from ekg.core.protocol import load_manifest_ids
from ekg.core.stage_bundle import model_content_digest, sha256_file


def newness_labels(gold, ids):
    identity = {}
    for event in gold['events']:
        for mention in event['mention']:
            if mention['id'] in identity:
                raise ValueError('duplicate train mention')
            identity[mention['id']] = event['id']
    if len(ids) != len(set(ids)) or set(ids) != set(identity):
        raise ValueError('train supervision population mismatch')
    seen, labels = set(), []
    for mid in ids:
        labels.append(int(identity[mid] in seen))
        seen.add(identity[mid])
    return labels


def probability_rows(ids, logits, null_logodds, types):
    if (len(ids) != len(set(ids)) or set(ids) != set(types)
            or len(logits) != len(ids) or len(null_logodds) != len(ids)):
        raise ValueError('null inference population mismatch')
    rows = []
    for i, (scores, logodds) in enumerate(zip(logits, null_logodds, strict=True)):
        if len(scores) != i or not all(math.isfinite(v) for v in [*scores, logodds]):
            raise ValueError('nonfinite/incomplete null scores')
        legal = [j for j in range(i) if types[ids[j]] == types[ids[i]]]
        values = [0.0] * (i + 1)
        if not legal:
            values[i] = 1.0
        else:
            maximum = max(scores[j] for j in legal)
            lse = maximum + math.log(sum(math.exp(scores[j] - maximum) for j in legal))
            dummy = lse - logodds
            maximum = max(maximum, dummy)
            total = sum(math.exp(scores[j] - maximum) for j in legal) + math.exp(dummy - maximum)
            for j in legal:
                values[j] = math.exp(scores[j] - maximum) / total
            values[i] = math.exp(dummy - maximum) / total
        rows.append(values)
    return rows


def feature_rows(embed, logits, types, torch):
    if len(embed) != len(logits) or len(types) != len(embed):
        raise ValueError('feature population mismatch')
    rows = []
    for i, scores in enumerate(logits):
        if len(scores) != i or not all(math.isfinite(v) for v in scores):
            raise ValueError('feature score shape/value mismatch')
        legal = [j for j in range(i) if types[j] == types[i]]
        empty = torch.zeros_like(embed[i])
        if legal:
            best = max(legal, key=scores.__getitem__)
            mean, top = embed[legal].mean(dim=0), embed[best]
            values = torch.tensor([scores[j] for j in legal])
            numeric = [scores[best], float(torch.logsumexp(values, dim=0)), math.log1p(len(legal))]
        else:
            mean, top, numeric = empty, empty, [0.0, 0.0, 0.0]
        rows.append(torch.cat((embed[i], mean, top, torch.tensor(numeric))))
    result = torch.stack(rows)
    if not torch.isfinite(result).all():
        raise ValueError('nonfinite contextual features')
    return result


def shuffle_semantics(features, docs, types, opportunities):
    if not len(features) == len(docs) == len(types) == len(opportunities):
        raise ValueError('shuffle population mismatch')
    groups = {}
    for i, (doc, kind, count) in enumerate(zip(docs, types, opportunities, strict=True)):
        bucket = count if count <= 1 else 2 if count <= 4 else 5
        groups.setdefault((doc, kind, bucket), []).append(i)
    result, rng = features.copy(), random.Random(13)
    for group in groups.values():
        source = list(group)
        rng.shuffle(source)
        result[group, :-3] = features[source, :-3]
    return result


def validate_settings(config):
    expected = {'epochs': 10, 'lr': 0.001, 'batch_size': 512, 'hidden': 200, 'dropout': 0.2,
                'arms': ['semantic', 'numeric_only', 'shuffled_semantic'],
                'fit_only_nonempty_legal_set': True}
    if config['training'] != expected:
        raise ValueError('frozen training budget drift')


def load_records(path, expected_ids):
    rows = [json.loads(line) for line in Path(path).read_text().splitlines()]
    result = {row['id']: row for row in rows}
    if len(result) != len(rows) or set(result) != expected_ids:
        raise ValueError(f'document scope mismatch: {path}')
    return result


def finish(output, config_sha, **metadata):
    status = {'status': 'complete', 'config_sha256': config_sha, **metadata,
              'artifact_sha256': {str(p.relative_to(output)): sha256_file(p)
                                 for p in sorted(output.rglob('*'))
                                 if p.is_file() and p.name != 'status.json'}}
    (output / 'status.json').write_text(json.dumps(status, indent=2, sort_keys=True) + '\n')


def export(config, config_sha, role, output, smoke, torch):
    from export_official_coref_cpu import (
        input_population,
        require_parity,
        validate_cache_document,
        validate_records,
    )
    from replay_typed_coref_control import constrain_types, decode_rows
    from run_symmetric_coref_control import directional_logits
    from transformers import RobertaTokenizer

    expected = set(load_manifest_ids(Path(config[role + '_manifest'])))
    records = load_records(config[role + '_input'], expected)
    if role == 'dev':
        validate_records(list(records.values()), expected)
        if input_population(records)['candidate_id_digest'] != config['candidate_digest']:
            raise ValueError('dev candidate population drift')
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(Path(config['source_root']).resolve()))
    modules = {name: importlib.import_module('src.' + name)
               for name in ('model', 'data', 'utils', 'dump_result')}
    for name, module in modules.items():
        if Path(module.__file__).resolve() != (
                Path(config['source_root']) / 'src' / (name + '.py')).resolve():
            raise ValueError('encoder source mismatch')
    tokenizer = RobertaTokenizer.from_pretrained(config['pretrained'], local_files_only=True)
    model = modules['model'].Model(len(tokenizer), model_name=config['pretrained'])
    checkpoint = torch.load(config['checkpoint'], map_location='cpu', weights_only=False)
    model.load_state_dict(checkpoint['model'], strict=True)
    del checkpoint
    model.eval()
    cached = load_records(config['scores'], set(load_manifest_ids(Path(config['dev_manifest']))))
    original = load_records(config['original_predictions'], set(cached))
    loader = modules['data'].get_dataloader(
        tokenizer, 'train' if role == 'train' else 'test', data_dir=config['data_dir'],
        max_length=256, batch_size=8, shuffle=False, ignore_nonetype=False)
    output.mkdir(parents=True, exist_ok=False)
    arrays, labels, documents, seen = [], [], [], set()
    with torch.no_grad():
        for index, batch in enumerate(loader):
            embeds = model.encoder({key: batch[key] for key in (
                'input_ids', 'attention_mask', 'event_spans', 'splits')})
            for doc_id, embed, event_idx in zip(
                    batch['doc_id'], embeds, batch['events_idx'], strict=True):
                record = records[doc_id]
                if doc_id in seen:
                    raise ValueError('duplicate feature document')
                seen.add(doc_id)
                ordered = [event for event in modules['data'].Document(record).events
                           if not event['id'].startswith('TIME')]
                mids = [event['id'] for event in ordered]
                if role == 'train':
                    type_map = {m['id']: e['type'] for e in record['events'] for m in e['mention']}
                    labels.extend(newness_labels(record, mids))
                else:
                    type_map = {m['id']: m['type'] for m in record['event_mentions']}
                kinds = [type_map[mid] for mid in mids]
                forward, _ = directional_logits(model.coref_scorer.score, embed[event_idx], torch)
                if role == 'dev':
                    validate_cache_document(cached[doc_id])
                    if (mids != cached[doc_id]['mentions']
                            or forward != cached[doc_id]['pair_logits']):
                        raise ValueError('dev forward/cache exact parity failed')
                    clusters = decode_rows(constrain_types(mids, cached[doc_id]['probabilities'],
                                                          type_map), mids,
                                           modules['utils'].get_predicted_clusters, torch)
                    require_parity(original[doc_id], clusters, mids)
                features = feature_rows(embed[event_idx], forward, kinds, torch)
                start = sum(len(array) for array in arrays)
                arrays.append(features.numpy())
                documents.append({'id': doc_id, 'mentions': mids, 'types': kinds,
                                  'start': start, 'end': start + len(mids)})
            print(f'{role} batch {index + 1}: {len(seen)} documents', flush=True)
            if smoke:
                break
    if not smoke and seen != expected:
        raise ValueError('full feature population mismatch')
    payload = {'features': np.concatenate(arrays)}
    if role == 'train':
        payload['labels'] = np.asarray(labels, dtype=np.float32)
    np.savez_compressed(output / 'features.npz', **payload)
    (output / 'documents.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in documents))
    finish(output, config_sha, role=role, documents=len(seen), mentions=len(payload['features']),
           encoder_optimizer_steps=0, dev_gold_accessed=False, final_valid_accessed=False)


def fit(config, config_sha, output, torch):
    from export_official_coref_cpu import require_smoke
    from replay_typed_coref_control import decode_rows, load_decoder
    from sklearn.preprocessing import StandardScaler

    root = Path(config['output'])
    for role in ('train', 'dev'):
        require_smoke(root / 'cache' / role, config_sha)
    train = np.load(root / 'cache/train/features.npz')
    dev = np.load(root / 'cache/dev/features.npz')
    if 'labels' in dev.files:
        raise ValueError('dev cache must not contain targets')
    def docs(role):
        return [json.loads(line) for line in (root / 'cache' / role / 'documents.jsonl').read_text(
            ).splitlines()]
    train_docs, dev_docs = docs('train'), docs('dev')
    if {r['id'] for r in train_docs} & {r['id'] for r in dev_docs}:
        raise ValueError('train/dev overlap')
    features, target = train['features'], train['labels']
    legal_counts = np.rint(np.expm1(features[:, -1])).astype(int)
    fit_rows = legal_counts > 0
    if (len(target) != len(features) or not np.isfinite(features).all()
            or set(np.unique(target)) != {0, 1}):
        raise ValueError('invalid training features/targets')
    flat_docs = [r['id'] for r in train_docs for _ in r['mentions']]
    flat_types = [kind for r in train_docs for kind in r['types']]
    candidates = {
        'semantic': features,
        'numeric_only': np.concatenate((np.zeros_like(features[:, :-3]), features[:, -3:]), axis=1),
        'shuffled_semantic': shuffle_semantics(features, flat_docs, flat_types, legal_counts),
    }
    ids = set(load_manifest_ids(Path(config['dev_manifest'])))
    cache = load_records(config['scores'], ids)
    original = load_records(config['original_predictions'], ids)
    decoder = load_decoder(Path(config['utility']))
    output.mkdir(parents=True, exist_ok=False)
    for arm, x in candidates.items():
        scaler = StandardScaler().fit(x[fit_rows])
        x_train = torch.tensor(scaler.transform(x[fit_rows]).astype(np.float32))
        x_dev = dev['features'].copy()
        if arm == 'numeric_only':
            x_dev[:, :-3] = 0
        x_dev = torch.tensor(scaler.transform(x_dev).astype(np.float32))
        y = torch.tensor(target[fit_rows])
        torch.manual_seed(13)
        head = torch.nn.Sequential(torch.nn.Linear(x.shape[1], 200), torch.nn.ReLU(),
                                   torch.nn.Dropout(0.2), torch.nn.Linear(200, 1))
        optimizer = torch.optim.Adam(head.parameters(), lr=0.001)
        history = []
        for epoch in range(10):
            head.train()
            order = torch.randperm(len(y))
            loss_sum = 0.0
            for indices in order.split(512):
                optimizer.zero_grad()
                logits = head(x_train[indices]).flatten()
                loss = torch.nn.functional.binary_cross_entropy_with_logits(logits, y[indices])
                if not torch.isfinite(loss):
                    raise ValueError('nonfinite null training loss')
                loss.backward()
                optimizer.step()
                loss_sum += float(loss.detach()) * len(indices)
            history.append(loss_sum / len(y))
            print(f'{arm} epoch {epoch + 1}: train BCE={history[-1]:.6f}', flush=True)
        head.eval()
        with torch.no_grad():
            null_logodds = torch.cat([head(chunk).flatten() for chunk in x_dev.split(512)]).tolist()
        predictions = []
        for row in dev_docs:
            doc_id, mids = row['id'], row['mentions']
            if mids != cache[doc_id]['mentions']:
                raise ValueError('dev cache ordering mismatch')
            rows = probability_rows(mids, cache[doc_id]['pair_logits'],
                                    null_logodds[row['start']:row['end']],
                                    dict(zip(mids, row['types'], strict=True)))
            predictions.append({**original[doc_id], 'coreference': decode_rows(
                rows, mids, decoder, torch)})
        arm_root = output / arm
        arm_root.mkdir(exist_ok=False)
        torch.save({'state_dict': head.state_dict(), 'scaler_mean': scaler.mean_,
                    'scaler_scale': scaler.scale_, 'final_epoch': 10, 'seed': 13},
                   arm_root / 'null_head.pt')
        (arm_root / 'predictions.jsonl').write_text(''.join(
            json.dumps(r, sort_keys=True) + '\n' for r in predictions))
        (arm_root / 'training.json').write_text(json.dumps({'bce': history, 'fit_mentions': len(y),
                                                         'fit_positive': int(y.sum()),
                                                         'dev_targets_read': False}, indent=2))
    finish(output, config_sha, control_only=True, exploratory=True, seed=13,
           endpoint_epoch=10, encoder_optimizer_steps=0, final_valid_accessed=False)


def main():
    from export_official_coref_cpu import require_smoke

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--stage', choices=('smoke', 'cache-train', 'cache-dev', 'fit'),
                        required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    validate_settings(config)
    if (config['schema_version'] != 'ekg.c5_frozen_null_control.v1'
            or config['control_only'] is not True or config['final_valid_accessed'] is not False
            or config['seed'] != 13 or os.environ.get('CUDA_VISIBLE_DEVICES') != '-1'):
        raise ValueError('null control role drift')
    if sha256_file(Path(__file__)) != config['entrypoint_sha256']:
        raise ValueError('null control entrypoint drift')
    for path, expected in config['input_sha256'].items():
        if sha256_file(Path(path)) != expected:
            raise ValueError(f'input hash drift: {path}')
    train_ids = set(load_manifest_ids(Path(config['train_manifest'])))
    dev_ids = set(load_manifest_ids(Path(config['dev_manifest'])))
    if train_ids & dev_ids:
        raise ValueError('train/dev manifest overlap')
    for role, expected_role in [('train', 'train'), ('dev', 'internal-dev')]:
        manifest = json.loads(Path(config[role + '_manifest']).read_text())
        if manifest['dataset'] != 'maven_ere' or manifest['split_role'] != expected_role:
            raise ValueError('manifest role drift')
    if model_content_digest(Path(config['pretrained'])) != config['pretrained_digest']:
        raise ValueError('pretrained digest drift')
    import torch

    if torch.cuda.is_available():
        raise ValueError('null control must use CPU')
    torch.set_num_threads(4)
    torch.set_num_interop_threads(1)
    torch.manual_seed(13)
    root, config_sha = Path(config['output']), sha256_file(args.config)
    if args.stage == 'smoke':
        if (root / 'smoke').exists():
            raise FileExistsError(root / 'smoke')
        for role in ('train', 'dev'):
            export(config, config_sha, role, root / 'smoke' / role, True, torch)
        finish(root / 'smoke', config_sha, control_only=True)
    else:
        require_smoke(root / 'smoke', config_sha)
        if args.stage.startswith('cache-'):
            role = args.stage.removeprefix('cache-')
            export(config, config_sha, role, root / 'cache' / role, False, torch)
        else:
            if (root / 'arms').exists():
                raise FileExistsError(root / 'arms')
            fit(config, config_sha, root / 'arms', torch)


if __name__ == '__main__':
    main()
