"""Describe frozen dev predictions by train-only ordered trigger surface coverage."""
from __future__ import annotations

import argparse
import json
from itertools import permutations
from pathlib import Path

import numpy as np
from diagnose_ergo_native_fit import causal_metrics, confusion_for_labels
from report_a4_direction_errors import LABELS, _labels

from ekg.core.stage_bundle import sha256_file
from ekg.relations.maven_ere_official import (
    gold_to_official_prediction,
    records_by_id,
    validate_official_predictions,
)

COVERAGE = ('train-positive-seen', 'train-NONE-only-seen', 'unseen')
CELLS = tuple(f'{a}/{b}' for a in COVERAGE for b in ('same-sentence', 'cross-sentence'))


def contexts(record, mention_ids):
    mentions = (record['event_mentions'] if 'event_mentions' in record else
                [m for event in record['events'] for m in event['mention']])
    result = {}
    for mention in mentions:
        mid, sent = mention['id'], mention['sent_id']
        start, end = mention['offset']
        if (mid in result or type(sent) is not int or not 0 <= sent < len(record['tokens'])
                or type(start) is not int or type(end) is not int
                or not 0 <= start < end <= len(record['tokens'][sent])):
            raise ValueError('duplicate mention or invalid trigger offset')
        surface = ' '.join(' '.join(record['tokens'][sent][start:end]).casefold().split())
        if not surface:
            raise ValueError('empty trigger surface')
        result[mid] = (surface, sent)
    if len(set(mention_ids)) != len(mention_ids) or set(result) != set(mention_ids):
        raise ValueError('complete unique feature/mention population required')
    return result


def training_index(records, features, targets):
    if set(records) != set(features) or set(records) != set(targets):
        raise ValueError('complete train IDs required')
    index = {}
    for doc_id, feature in features.items():
        mids = feature['mention_ids']
        ctx = contexts(records[doc_id], mids)
        target = targets[doc_id]['target']
        if (len(target) != len(mids)*(len(mids)-1)
                or any(type(v) is not int or v not in (0, 1, 2) for v in target)):
            raise ValueError('complete native train target population required')
        for (head, tail), label in zip(permutations(mids, 2), target, strict=True):
            key = (ctx[head][0], ctx[tail][0])
            index[key] = index.get(key, False) or label != 0
    return index


def strata(record, mention_ids, index):
    ctx = contexts(record, mention_ids)
    result = []
    for head, tail in permutations(mention_ids, 2):
        key = (ctx[head][0], ctx[tail][0])
        coverage = ('unseen' if key not in index else
                    'train-positive-seen' if index[key] else 'train-NONE-only-seen')
        distance = 'same-sentence' if ctx[head][1] == ctx[tail][1] else 'cross-sentence'
        result.append(f'{coverage}/{distance}')
    return result


def count_cells(membership, gold, predictions):
    if (len(membership) != len(gold) or not predictions
            or any(len(p) != len(gold) for p in predictions.values())
            or any(cell not in CELLS for cell in membership)):
        raise ValueError('complete fixed cell population required')
    result = {}
    for cell in CELLS:
        indices = [i for i, value in enumerate(membership) if value == cell]
        result[cell] = {}
        for name, predicted in predictions.items():
            matrix = (confusion_for_labels([gold[i] for i in indices],
                                          [predicted[i] for i in indices])
                      if indices else np.zeros((3, 3), dtype=np.int64))
            result[cell][name] = {'confusion': matrix.tolist(),
                                     'metrics': causal_metrics(matrix)}
    return result


def load(path):
    with Path(path).open() as stream:
        return records_by_id((json.loads(line) for line in stream if line.strip()), source=path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    args = parser.parse_args()
    cfg = json.loads(args.config.read_text())
    if cfg['final_valid_accessed'] is not False:
        raise ValueError('final-valid is sealed')
    for key, role in (('train_manifest', 'train'), ('dev_manifest', 'internal-dev')):
        manifest = json.loads(Path(cfg[key]).read_text())
        if manifest['split_role'] != role:
            raise ValueError('only original train and internal-dev are allowed')
    for path, digest in cfg['pins'].items():
        if sha256_file(Path(path)) != digest:
            raise ValueError(f'surface input/source drift: {path}')
    output = Path(cfg['output'])
    output.mkdir(parents=True, exist_ok=False)
    (output/'config.json').write_bytes(args.config.read_bytes())
    train, train_features, train_targets = (load(cfg[k]) for k in
                                            ('train_raw', 'train_features', 'train_targets'))
    manifest = json.loads(Path(cfg['train_manifest']).read_text())
    if set(manifest['doc_ids']) != set(train) or len(train) != manifest['doc_count']:
        raise ValueError('train differs from frozen manifest')
    index = training_index(train, train_features, train_targets)
    dev, features = (load(cfg[k]) for k in ('dev_unlabeled', 'dev_features'))
    manifest = json.loads(Path(cfg['dev_manifest']).read_text())
    if (set(dev) != set(features) or set(dev) != set(manifest['doc_ids'])
            or len(dev) != manifest['doc_count'] or set(train) & set(dev)):
        raise ValueError('frozen disjoint dev population required')
    # Membership is fixed before opening dev gold/predictions.
    membership = {key: strata(dev[key], f['mention_ids'], index) for key, f in features.items()}
    with (output/'membership.jsonl').open('x') as stream:
        for key in sorted(membership):
            stream.write(json.dumps({'id': key, 'strata': membership[key]})+'\n')
    gold, full, joint, classes = (load(cfg[k]) for k in
                                 ('dev_gold', 'full_predictions',
                                  'joint_predictions', 'full_classes'))
    for pred in (full, joint):
        validate_official_predictions(gold, pred, expected_candidate_digest=cfg['dev_digest'])
    if set(classes) != set(features) or set(gold) != set(features):
        raise ValueError('complete frozen classes/gold/features required')
    totals = {cell: {arm: np.zeros((3, 3), dtype=np.int64) for arm in ('full', 'joint')}
              for cell in CELLS}
    with (output/'documents.jsonl').open('x') as stream:
        for key, feature in features.items():
            pairs = list(permutations(feature['mention_ids'], 2))
            maps = [_labels(gold_to_official_prediction(gold[key])),
                    _labels(full[key]), _labels(joint[key])]
            y, p, j = [[LABELS.index(labels.get(pair, 'NONE')) for pair in pairs]
                       for labels in maps]
            if p != classes[key]['classes']:
                raise ValueError('native full classes and official predictions disagree')
            cells = count_cells(membership[key], y, {'full': p, 'joint': j})
            stream.write(json.dumps({'id': key, 'cells': cells})+'\n')
            for cell in CELLS:
                for arm in ('full', 'joint'):
                    totals[cell][arm] += np.asarray(cells[cell][arm]['confusion'])
    reference = json.loads(Path(cfg['comparison_reference']).read_text())
    contrast = reference['contrasts']['full_minus_official_joint_primary']
    for arm, side in (('full', 'left'), ('joint', 'right')):
        if sum(totals[c][arm] for c in CELLS).tolist() != contrast[f'{side}_confusion']:
            raise ValueError('strata do not conserve independently verified native dev confusion')
    report = {'schema_version': 'ekg.a4_surface_generalization.v1', 'diagnostic_only': True,
              'documents': len(dev), 'config_sha256': sha256_file(args.config),
              'membership_sha256': sha256_file(output/'membership.jsonl'),
              'train_ordered_surface_pairs': len(index),
              'train_positive_surface_pairs': sum(index.values()),
              'cells': {cell: {arm: {'confusion': matrix.tolist(),
                                     'metrics': causal_metrics(matrix)}
                               for arm, matrix in arms.items()} for cell, arms in totals.items()},
              'global_confusion_conserved': True, 'dev_labels_used_for_strata': False,
              'encoder_calls': 0, 'new_training_epochs': 0, 'final_valid_accessed': False,
              'limitations': ['Exact normalized surface coverage is not semantic coverage.',
                              'NONE is an annotation; strata are not causal effects.',
                              'No threshold, checkpoint, candidate or prediction changes.']}
    (output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
