#!/usr/bin/env python
"""Audit class versus antecedent decision units with sealed null heads."""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path

import numpy as np

from ekg.core.protocol import load_manifest_ids
from ekg.core.stage_bundle import sha256_file

ARMS = ('semantic', 'numeric_only', 'shuffled_semantic')


def decision_rows(ids, logits, logodds, kinds):
    n = len(ids)
    if len(set(ids)) != n or not len(logits) == len(logodds) == len(kinds) == n:
        raise ValueError('decision-unit population mismatch')
    rows = []
    for i, (scores, z) in enumerate(zip(logits, logodds, strict=True)):
        if len(scores) != i or not all(math.isfinite(v) for v in [z, *scores]):
            raise ValueError('invalid decision-unit scores')
        legal = [j for j in range(i) if kinds[j] == kinds[i]]
        winner = max(legal, key=scores.__getitem__) if legal and z > 0 else i
        rows.append([int(j == winner) for j in range(i + 1)])
    return rows


def restore_scaler(mean, scale):
    from sklearn.preprocessing import StandardScaler

    scaler = StandardScaler()
    scaler.mean_, scaler.scale_ = mean, scale
    scaler.n_features_in_ = len(mean)
    return scaler


def load_head(path, torch):
    weights = torch.load(path, map_location='cpu', weights_only=False)
    if weights['seed'] != 13 or weights['final_epoch'] != 10:
        raise ValueError('sealed head identity drift')
    scaler = restore_scaler(weights['scaler_mean'], weights['scaler_scale'])
    head = torch.nn.Sequential(torch.nn.Linear(scaler.n_features_in_, 200), torch.nn.ReLU(),
                               torch.nn.Dropout(0.2), torch.nn.Linear(200, 1))
    head.load_state_dict(weights['state_dict'], strict=True)
    head.eval()
    return head, scaler


def main():
    from export_official_coref_cpu import require_parity
    from replay_typed_coref_control import decode_rows, load_decoder
    from run_frozen_null_control import probability_rows

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    args = parser.parse_args()
    c = json.loads(args.config.read_text())
    if (c['schema_version'] != 'ekg.null_decision_unit_audit.v1' or c['seed'] != 13
            or c['final_valid_accessed'] is not False or c['control_only'] is not True
            or os.environ.get('CUDA_VISIBLE_DEVICES') != '-1'):
        raise ValueError('null-unit audit identity drift')
    for path, expected in c['input_sha256'].items():
        if sha256_file(Path(path)) != expected:
            raise ValueError(f'audit input hash drift: {path}')
    root, output = Path(c['null_root']), Path(c['output'])
    if output.exists():
        raise FileExistsError(output)
    status = json.loads((root / 'arms/status.json').read_text())
    cache_status = json.loads((root / 'cache/dev/status.json').read_text())
    if (status['status'] != 'complete' or cache_status['status'] != 'complete'
            or status['config_sha256'] != c['source_config_sha256']
            or cache_status['config_sha256'] != c['source_config_sha256']):
        raise ValueError('source head/cache status drift')
    docs = [json.loads(line) for line in (
        root / 'cache/dev/documents.jsonl').read_text().splitlines()]
    ids = set(load_manifest_ids(Path(c['manifest'])))
    if len(docs) != len(ids) or {r['id'] for r in docs} != ids:
        raise ValueError('decision-unit document scope drift')
    manifest = json.loads(Path(c['manifest']).read_text())
    if manifest['dataset'] != 'maven_ere' or manifest['split_role'] != 'internal-dev':
        raise ValueError('decision-unit manifest role drift')
    cache_list = [json.loads(line) for line in Path(c['scores']).read_text().splitlines()]
    cache = {r['id']: r for r in cache_list}
    if len(cache_list) != len(ids) or set(cache) != ids:
        raise ValueError('raw-score document scope drift')
    dev = np.load(root / 'cache/dev/features.npz')
    if dev.files != ['features'] or not np.isfinite(dev['features']).all():
        raise ValueError('dev features invalid or contain targets')
    import torch

    if torch.cuda.is_available():
        raise ValueError('decision-unit replay is CPU only')
    torch.set_num_threads(4)
    decoder = load_decoder(Path(c['utility']))
    predictions, head_logits = {}, {}
    for arm in ARMS:
        head, scaler = load_head(root / 'arms' / arm / 'null_head.pt', torch)
        x = dev['features'].copy()
        if arm == 'numeric_only':
            x[:, :-3] = 0
        transformed = torch.tensor(scaler.transform(x).astype(np.float32))
        with torch.no_grad():
            z = torch.cat([head(chunk).flatten() for chunk in transformed.split(512)]).tolist()
        prior_list = [json.loads(line) for line in (
            root / 'arms' / arm / 'predictions.jsonl').read_text().splitlines()]
        prior = {r['id']: r for r in prior_list}
        if len(prior_list) != len(ids) or set(prior) != ids:
            raise ValueError('sealed source prediction scope drift')
        predictions[arm], head_logits[arm], previous_end = [], [], 0
        for doc in docs:
            mid, start, end = doc['mentions'], doc['start'], doc['end']
            row = cache[doc['id']]
            if mid != row['mentions'] or start != previous_end or end - start != len(mid):
                raise ValueError('feature/raw mention order or offsets drift')
            previous_end = end
            logits, types = row['pair_logits'], dict(zip(mid, doc['types'], strict=True))
            old = probability_rows(mid, logits, z[start:end], types)
            require_parity(prior[doc['id']], decode_rows(old, mid, decoder, torch), mid)
            new = decision_rows(mid, logits, z[start:end], doc['types'])
            predictions[arm].append({**prior[doc['id']], 'coreference': decode_rows(
                new, mid, decoder, torch)})
            head_logits[arm].append({'id': doc['id'], 'mentions': mid, 'logodds': z[start:end]})
        if previous_end != len(z):
            raise ValueError('feature coverage drift')
    output.mkdir(parents=True, exist_ok=False)
    for arm in ARMS:
        for suffix, data in [('predictions', predictions), ('head_logits', head_logits)]:
            (output / (arm + '_' + suffix + '.jsonl')).write_text(
                ''.join(json.dumps(r) + '\n' for r in data[arm]))
    report = {'status': 'complete', 'config_sha256': sha256_file(args.config), 'control_only': True,
              'source_predictions_parity': 'all three arms/all documents exact',
              'documents': len(ids), 'optimizer_steps': 0, 'final_valid_accessed': False,
              'artifact_sha256': {p.name: sha256_file(p) for p in output.iterdir()}}
    (output / 'status.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
