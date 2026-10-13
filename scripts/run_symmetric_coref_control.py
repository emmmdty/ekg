#!/usr/bin/env python
"""Fixed bidirectional scoring of a frozen official head; no fit or gold inference."""

from __future__ import annotations

import argparse
import importlib
import json
import math
import os
import random
import subprocess
import sys
from pathlib import Path

from ekg.core.protocol import load_manifest_ids
from ekg.core.stage_bundle import model_content_digest, sha256_file


def combine_logits(forward, reverse):
    if len(forward) != len(reverse) or any(
            len(a) != i or len(b) != i or not all(math.isfinite(v) for v in [*a, *b])
            for i, (a, b) in enumerate(zip(forward, reverse, strict=True))):
        raise ValueError('directional score population/value mismatch')
    return [[*(0.5 * (a + b) for a, b in zip(left, right, strict=True)), 0.0]
            for left, right in zip(forward, reverse, strict=True)]


def shuffle_reverse(ids, reverse, types):
    combine_logits(reverse, reverse)
    if len(ids) != len(set(ids)) or set(ids) != set(types) or len(ids) != len(reverse):
        raise ValueError('negative-control type population mismatch')
    result = [list(row) for row in reverse]
    groups = {}
    for i in range(len(ids)):
        for j in range(i):
            if types[ids[i]] == types[ids[j]]:
                groups.setdefault(types[ids[i]], []).append((i, j))
    rng = random.Random(13)
    for indices in groups.values():
        values = [reverse[i][j] for i, j in indices]
        rng.shuffle(values)
        for (i, j), value in zip(indices, values, strict=True):
            result[i][j] = value
    return result


def directional_logits(head, embed, torch):
    n = embed.shape[0]
    if n == 0:
        raise ValueError('empty mention population')
    forward, reverse = [[]], [[]]
    if n > 1:
        current, previous = torch.tril_indices(n, n, offset=-1, device=embed.device)
        a, b = embed[current], embed[previous]
        left = head(torch.cat((a, b, a * b), dim=1)).flatten().tolist()
        right = head(torch.cat((b, a, a * b), dim=1)).flatten().tolist()
        position = 0
        for i in range(1, n):
            forward.append(left[position:position + i])
            reverse.append(right[position:position + i])
            position += i
    return forward, reverse


def main():
    from export_official_coref_cpu import (
        input_population,
        require_parity,
        require_smoke,
        validate_cache_document,
        validate_records,
    )
    from replay_typed_coref_control import constrain_types, decode_rows

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--scope', required=True, choices=('smoke', 'full'))
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    if (config['schema_version'] != 'ekg.c5_symmetric_control.v1'
            or config['control_only'] is not True or config['final_valid_accessed'] is not False
            or config['seed'] != 13 or config['reverse_weight'] != 0.5
            or config['cpu_threads'] != 4 or config['batch_size'] != 8
            or config['max_length'] != 256 or os.environ.get('CUDA_VISIBLE_DEVICES') != '-1'):
        raise ValueError('frozen CPU control scope drift')
    if sha256_file(Path(__file__)) != config['entrypoint_sha256']:
        raise ValueError('entrypoint drift')
    for path, expected in config['input_sha256'].items():
        if sha256_file(Path(path)) != expected:
            raise ValueError(f'input drift: {path}')
    if model_content_digest(Path(config['pretrained'])) != config['pretrained_digest']:
        raise ValueError('pretrained content drift')
    manifest = json.loads(Path(config['manifest']).read_text())
    if manifest['dataset'] != 'maven_ere' or manifest['split_role'] != 'internal-dev':
        raise ValueError('internal-dev control only')
    ids = set(load_manifest_ids(Path(config['manifest'])))
    config_sha = sha256_file(args.config)
    output = Path(config['output']) / args.scope
    if output.exists():
        raise FileExistsError(output)
    if args.scope == 'full':
        require_smoke(Path(config['output']) / 'smoke', config_sha)

    def load(path):
        rows = [json.loads(line) for line in Path(path).read_text().splitlines()]
        by_id = {row['id']: row for row in rows}
        if len(by_id) != len(rows) or set(by_id) != ids:
            raise ValueError(f'document population mismatch: {path}')
        return by_id

    records = validate_records(list(load(config['input']).values()), ids)
    population = input_population(records)
    if population['candidate_id_digest'] != config['candidate_digest']:
        raise ValueError('candidate digest drift')
    cached, original = load(config['scores']), load(config['original_predictions'])
    import torch
    from transformers import RobertaTokenizer

    if torch.cuda.is_available():
        raise ValueError('CUDA must remain invisible')
    torch.set_num_threads(4)
    torch.set_num_interop_threads(1)
    torch.manual_seed(13)
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(Path(config['source_root']).resolve()))
    modules = {name: importlib.import_module('src.' + name)
               for name in ('model', 'data', 'utils', 'dump_result')}
    for name, module in modules.items():
        if Path(module.__file__).resolve() != (
                Path(config['source_root']) / 'src' / (name + '.py')).resolve():
            raise ValueError('official module source mismatch')
    tokenizer = RobertaTokenizer.from_pretrained(config['pretrained'], local_files_only=True)
    model = modules['model'].Model(len(tokenizer), model_name=config['pretrained'])
    checkpoint = torch.load(config['checkpoint'], map_location='cpu', weights_only=False)
    model.load_state_dict(checkpoint['model'], strict=True)
    del checkpoint
    model.eval()
    if any(p.device.type != 'cpu' for p in model.parameters()):
        raise ValueError('model must remain on CPU')
    loader = modules['data'].get_dataloader(
        tokenizer, 'test', data_dir=config['data_dir'], max_length=256,
        batch_size=8, shuffle=False, ignore_nonetype=False)
    decoder = modules['utils'].get_predicted_clusters
    output.mkdir(parents=True, exist_ok=False)
    status = {'status': 'running', 'scope': args.scope, 'config_sha256': config_sha,
              'pid': os.getpid(), 'device': 'cpu', 'optimizer_steps': 0,
              'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()}
    (output / 'status.json').write_text(json.dumps(status, indent=2))
    seen, predictions, score_rows = set(), {arm: [] for arm in ('symmetric', 'shuffled')}, []
    try:
        with torch.no_grad():
            for index, batch in enumerate(loader):
                embeds = model.encoder({key: batch[key] for key in (
                    'input_ids', 'attention_mask', 'event_spans', 'splits')})
                for doc_id, embed, event_idx in zip(
                        batch['doc_id'], embeds, batch['events_idx'], strict=True):
                    mids = [m['id'] for m in modules['dump_result'].CorefDocument(
                        records[doc_id]).events]
                    if mids != cached[doc_id]['mentions'] or doc_id in seen:
                        raise ValueError('cached mention ordering/coverage drift')
                    validate_cache_document(cached[doc_id])
                    forward, reverse = directional_logits(model.coref_scorer.score,
                                                          embed[event_idx], torch)
                    if forward != cached[doc_id]['pair_logits']:
                        raise ValueError('original forward logits not exact cache parity')
                    types = {m['id']: m['type'] for m in records[doc_id]['event_mentions']}
                    base_rows = constrain_types(mids, cached[doc_id]['probabilities'], types)
                    base_clusters = decode_rows(base_rows, mids, decoder, torch)
                    require_parity(original[doc_id], base_clusters, mids)
                    control_reverse = shuffle_reverse(mids, reverse, types)
                    for arm, other in (('symmetric', reverse), ('shuffled', control_reverse)):
                        logits = combine_logits(forward, other)
                        probabilities = [torch.softmax(torch.tensor(row), dim=0).tolist()
                                         for row in logits]
                        rows = constrain_types(mids, probabilities, types)
                        clusters = decode_rows(rows, mids, decoder, torch)
                        predictions[arm].append({**original[doc_id], 'coreference': clusters})
                    score_rows.append({'id': doc_id, 'mentions': mids,
                                       'forward_logits': forward, 'reverse_logits': reverse})
                    seen.add(doc_id)
                print(f'batch {index + 1}: {len(seen)} documents; exact forward/typed parity',
                      flush=True)
                if args.scope == 'smoke':
                    break
        if args.scope == 'full' and seen != ids:
            raise ValueError('full control coverage mismatch')
        for arm, rows in predictions.items():
            (output / (arm + '_predictions.jsonl')).write_text(''.join(
                json.dumps(row, sort_keys=True) + '\n' for row in rows))
        (output / 'directional_scores.jsonl').write_text(''.join(
            json.dumps(row, allow_nan=False) + '\n' for row in score_rows))
        metadata = {**status, 'status': 'complete', 'control_only': True, 'exploratory': True,
                    'final_valid_accessed': False, 'documents': len(seen),
                    'full_input_population': population, 'reverse_weight': 0.5,
                    'dummy_logit': 0, 'type_policy': 'given_type_equality',
                    'forward_parity': 'all original logits exact',
                    'typed_baseline_parity': 'all non-singleton clusters exact',
                    'checkpoint_location': config['checkpoint'],
                    'input_sha256': config['input_sha256'], 'seed': 13,
                    'negative_control': 'reverse logits permuted in document/type pair groups',
                    'relation_fields': 'copied from original; no relation head inference'}
        (output / 'metadata.json').write_text(json.dumps(metadata, indent=2, sort_keys=True))
        status.update(status='complete', documents=len(seen), artifact_sha256={
            p.name: sha256_file(p) for p in sorted(output.iterdir()) if p.name != 'status.json'})
    except Exception as error:
        status.update(status='failed', error=f'{type(error).__name__}: {error}')
        raise
    finally:
        (output / 'status.json').write_text(json.dumps(status, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
