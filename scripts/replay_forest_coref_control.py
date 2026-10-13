#!/usr/bin/env python
"""Fixed joint-connectivity controls on an immutable antecedent cache."""
from __future__ import annotations

import argparse
import json
import math
import os
import random
from pathlib import Path

import numpy as np

from ekg.core.protocol import load_manifest_ids
from ekg.core.stage_bundle import sha256_file


def typed_probabilities(logits, kinds):
    if len(logits) != len(kinds):
        raise ValueError('type/score population mismatch')
    result = []
    for i, row in enumerate(logits):
        if len(row) != i or not all(math.isfinite(v) for v in row):
            raise ValueError('invalid logits')
        legal = [j for j in range(i) if kinds[j] == kinds[i]]
        maximum = max([0.0, *(row[j] for j in legal)])
        values = [math.exp(row[j] - maximum) if j in legal else 0.0 for j in range(i)]
        values.append(math.exp(-maximum))
        total = sum(values)
        result.append([v / total for v in values])
    return result


def posterior_scores(rows, kinds):
    n = len(rows)
    if n != len(kinds) or not n:
        raise ValueError('posterior population mismatch')
    for i, row in enumerate(rows):
        if (len(row) != i + 1 or not all(math.isfinite(v) and v >= 0 for v in row)
                or not math.isclose(sum(row), 1.0, abs_tol=1e-12)
                or any(row[k] != 0 for k in range(i) if kinds[k] != kinds[i])):
            raise ValueError('invalid typed antecedent distribution')
    joint, shuffled, root = np.eye(n), np.eye(n), np.zeros((n, n))
    root[0, 0], rng = rows[0][0], random.Random(13)
    for j in range(1, n):
        parent = np.asarray(rows[j][:j])
        value = joint[:j, :j] @ parent
        joint[j, :j], joint[:j, j] = value, value
        root[j] = parent @ root[:j]
        root[j, j] = rows[j][j]
        groups = {}
        for k in range(j):
            groups.setdefault(kinds[k], []).append(k)
        perm = list(range(j))
        for indices in groups.values():
            source = list(indices)
            rng.shuffle(source)
            for dest, src in zip(indices, source, strict=True):
                perm[dest] = src
        value = joint[:j, :j][np.ix_(perm, perm)] @ parent
        shuffled[j, :j], shuffled[:j, j] = value, value
    return joint, root @ root.T, shuffled


def decoder_rows(scores, parent_rows, kinds):
    if scores.shape != (len(kinds), len(kinds)) or len(parent_rows) != len(kinds):
        raise ValueError('decoder population mismatch')
    return [[float(scores[i, j]) if kinds[i] == kinds[j] else -1000.0 for j in range(i)]
            + [parent_rows[i][i]] for i in range(len(kinds))]


def main():
    from export_official_coref_cpu import (
        input_population,
        require_parity,
        validate_cache_document,
        validate_records,
    )
    from replay_typed_coref_control import constrain_types, decode_rows, load_decoder

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    if (config['schema_version'] != 'ekg.forest_posterior_control.v1'
            or config['control_only'] is not True or config['seed'] != 13
            or config['final_valid_accessed'] is not False
            or os.environ.get('CUDA_VISIBLE_DEVICES') != '-1'):
        raise ValueError('forest control identity drift')
    for path, expected in config['input_sha256'].items():
        if sha256_file(Path(path)) != expected:
            raise ValueError(f'input hash drift: {path}')
    ids = set(load_manifest_ids(Path(config['manifest'])))
    manifest = json.loads(Path(config['manifest']).read_text())
    if manifest['dataset'] != 'maven_ere' or manifest['split_role'] != 'internal-dev':
        raise ValueError('forest manifest role drift')
    records = validate_records(
        [json.loads(line) for line in Path(config['input']).read_text().splitlines()], ids)
    if input_population(records)['candidate_id_digest'] != config['candidate_digest']:
        raise ValueError('forest candidate drift')
    cache = [json.loads(line) for line in Path(config['scores']).read_text().splitlines()]
    originals_list = [json.loads(line) for line in Path(config['original_predictions']).read_text(
        ).splitlines()]
    original = {r['id']: r for r in originals_list}
    if (len(cache) != len(ids) or {r['id'] for r in cache} != ids or len(originals_list) != len(ids)
            or set(original) != ids):
        raise ValueError('forest cache/prediction population drift')
    output = Path(config['output'])
    if output.exists():
        raise FileExistsError(output)
    import torch

    if torch.cuda.is_available():
        raise ValueError('forest replay is CPU only')
    torch.set_num_threads(4)
    decoder = load_decoder(Path(config['utility']))
    predictions = {arm: [] for arm in ('joint', 'root_product', 'ancestry_shuffle')}
    differences = []
    for doc in cache:
        validate_cache_document(doc)
        mids = doc['mentions']
        types = {m['id']: m['type'] for m in records[doc['id']]['event_mentions']}
        kinds = [types[m] for m in mids]
        baseline = decode_rows(constrain_types(mids, doc['probabilities'], types), mids,
                               decoder, torch)
        require_parity(original[doc['id']], baseline, mids)
        parent = typed_probabilities(doc['pair_logits'], kinds)
        # Re-normalization must preserve the original typed production decisions.
        require_parity(original[doc['id']], decode_rows(parent, mids, decoder, torch), mids)
        joint, product, shuffled = posterior_scores(parent, kinds)
        differences.append({'id': doc['id'], 'mentions': len(mids),
                            'joint_product_max_abs': float(np.abs(joint - product).max()),
                            'changed_shuffle_real_scores': int(np.count_nonzero(
                                np.tril(joint - shuffled, -1)))})
        for arm, scores in zip(predictions, (joint, product, shuffled), strict=True):
            clusters = decode_rows(decoder_rows(scores, parent, kinds), mids, decoder, torch)
            predictions[arm].append({**original[doc['id']], 'coreference': clusters})
    output.mkdir(parents=True, exist_ok=False)
    for arm, rows in predictions.items():
        (output / (arm + '_predictions.jsonl')).write_text(
            ''.join(json.dumps(r) + '\n' for r in rows))
    (output / 'differences.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in differences))
    metadata = {'status': 'complete', 'config_sha256': sha256_file(args.config),
                'documents': len(ids), 'control_only': True, 'optimizer_steps': 0,
                'original_typed_decoder_parity': 'all documents exact',
                'renormalized_parent_decoder_parity': 'all documents exact',
                'final_valid_accessed': False, 'artifact_sha256': {
                    p.name: sha256_file(p) for p in output.iterdir()}}
    (output / 'status.json').write_text(json.dumps(metadata, indent=2, sort_keys=True) + '\n')
    print(json.dumps(metadata, indent=2))


if __name__ == '__main__':
    main()
