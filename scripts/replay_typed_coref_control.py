#!/usr/bin/env python
"""Transparent given-type control on frozen scores, using the original decoder."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path

from ekg.core.protocol import load_manifest_ids
from ekg.core.stage_bundle import sha256_file


def constrain_types(ids, rows, types):
    if len(ids) != len(set(ids)) or set(ids) != set(types):
        raise ValueError('mention/type coverage mismatch')
    if len(rows) != len(ids) or any(len(row) != i + 1 for i, row in enumerate(rows)):
        raise ValueError('antecedent shape mismatch')
    return [[value if j == i or types[ids[j]] == types[ids[i]] else -1000
             for j, value in enumerate(row)] for i, row in enumerate(rows)]


def load_decoder(path):
    spec = importlib.util.spec_from_file_location('frozen_typed_control_utils', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.get_predicted_clusters


def decode_rows(rows, ids, decoder, torch):
    matrix = torch.full((len(ids), len(ids)), -1000.0, dtype=torch.float32, device='cpu')
    for i, row in enumerate(rows):
        matrix[i, :i + 1] = torch.tensor(row, dtype=torch.float32, device='cpu')
    clusters, _ = decoder(matrix)
    return sorted(sorted(ids[index] for index in group) for group in clusters if len(group) > 1)


def main():
    from export_official_coref_cpu import (
        input_population,
        require_parity,
        validate_cache_document,
        validate_records,
    )

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    if (config['schema_version'] != 'ekg.c5_typed_control.v1'
            or config['control_only'] is not True or config['final_valid_accessed'] is not False
            or config['constraint'] != 'given_type_equality' or config['seed'] != 13
            or config['cpu_threads'] != 4 or os.environ.get('CUDA_VISIBLE_DEVICES') != '-1'):
        raise ValueError('frozen typed-control CPU role drift')
    if sha256_file(Path(__file__)) != config['entrypoint_sha256']:
        raise ValueError('typed-control entrypoint drift')
    for path, expected in config['input_sha256'].items():
        if sha256_file(Path(path)) != expected:
            raise ValueError(f'input hash drift: {path}')
    manifest = json.loads(Path(config['manifest']).read_text())
    if manifest['dataset'] != 'maven_ere' or manifest['split_role'] != 'internal-dev':
        raise ValueError('typed control is internal-dev only')
    ids = set(load_manifest_ids(Path(config['manifest'])))
    records = validate_records([json.loads(line) for line in
                               Path(config['input']).read_text().splitlines()], ids)
    if input_population(records)['candidate_id_digest'] != config['candidate_digest']:
        raise ValueError('candidate digest drift')
    cache = [json.loads(line) for line in Path(config['scores']).read_text().splitlines()]
    originals = {row['id']: row for row in map(
        json.loads, Path(config['original_predictions']).read_text().splitlines())}
    if len(cache) != len(ids) or {row['id'] for row in cache} != ids or set(originals) != ids:
        raise ValueError('full cached document population mismatch')
    output = Path(config['output'])
    if output.exists():
        raise FileExistsError(output)
    import torch

    if torch.cuda.is_available():
        raise ValueError('CUDA must remain invisible')
    torch.set_num_threads(config['cpu_threads'])
    decoder = load_decoder(Path(config['utility']))
    predictions, changes = [], []
    for row in cache:
        validate_cache_document(row)
        mentions = row['mentions']
        original_clusters = decode_rows(row['probabilities'], mentions, decoder, torch)
        require_parity(originals[row['id']], original_clusters, mentions)
        types = {mention['id']: mention['type']
                 for mention in records[row['id']]['event_mentions']}
        ranked = constrain_types(mentions, row['probabilities'], types)
        clusters = decode_rows(ranked, mentions, decoder, torch)
        predictions.append({**originals[row['id']], 'coreference': clusters})
        changes.append({'id': row['id'], 'clusters_changed': clusters != original_clusters})
    output.mkdir(parents=True, exist_ok=False)
    (output / 'predictions.jsonl').write_text(''.join(
        json.dumps(row) + '\n' for row in predictions))
    (output / 'changes.jsonl').write_text(''.join(json.dumps(row) + '\n' for row in changes))
    metadata = {'status': 'complete', 'control_only': True, 'exploratory': True,
                'final_valid_accessed': False, 'device': 'cpu', 'seed': 13, 'optimizer_steps': 0,
                'documents': len(records), 'changed_documents': sum(
                    row['clusters_changed'] for row in changes),
                'constraint': config['constraint'], 'config_sha256': sha256_file(args.config),
                'input_sha256': config['input_sha256'], 'baseline_parity': 'all documents exact',
                'type_source': 'frozen unlabeled test input; no gold file read',
                'candidate_policy': 'all original IDs; cross-type antecedent ranking forbidden',
                'relation_fields': 'copied from frozen predictions; no relation inference',
                'predictions_sha256': sha256_file(output / 'predictions.jsonl'),
                'changes_sha256': sha256_file(output / 'changes.jsonl'),
                'limitations': ['Known constraint control, not a new method or MTL reproduction',
                                'Original frozen anchor remains immutable']}
    (output / 'metadata.json').write_text(json.dumps(metadata, indent=2, sort_keys=True))
    print(json.dumps(metadata, indent=2))


if __name__ == '__main__':
    main()
