#!/usr/bin/env python
"""Read frozen train-only CPU observers; predict unlabeled consumer documents."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import joblib
import numpy as np
import sklearn

from ekg.core.protocol import load_manifest_ids
from ekg.core.stage_bundle import sha256_file
from ekg.relations.data.maven_fact import FACTUALITY_LABELS as LABELS


def validate_scope(summary, records, ids):
    if (summary['diagnostic_only'] is not True or summary['seed'] != 13
            or summary['final_valid_accessed'] is not False
            or summary['consumer_evaluation_labels_accessed'] is not False):
        raise ValueError('upstream consumer scope/role drift')
    if len(records) != len(ids) or {row['id'] for row in records} != ids:
        raise ValueError('consumer document coverage mismatch')
    for row in records:
        if ('events' in row or 'coreference' in row or 'event_mentions' not in row
                or any('factuality' in mention or 'evidence' in mention
                       for mention in row['event_mentions'])):
            raise ValueError('consumer requires unlabeled input')
    for fold in summary['folds']:
        if ids.intersection(fold['train_doc_ids']) or ids.intersection(fold['evaluation_doc_ids']):
            raise ValueError('upstream partition touched consumer documents')


def predict_documents(records, models):
    # Reuse the exact train observer's trigger marking, without its train loader.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from probe_factuality_observations import marked_text

    examples = [(row, mention) for row in records for mention in row['event_mentions']]
    ids = [f"{row['id']}::{mention['id']}" for row, mention in examples]
    if len(ids) != len(set(ids)):
        raise ValueError('duplicate consumer mention')
    texts = [marked_text(row, mention) for row, mention in examples]
    probabilities = []
    for bundle in models:
        classifier = bundle['classifier']
        if set(classifier.classes_) != set(LABELS):
            raise ValueError('observer class coverage drift')
        order = [list(classifier.classes_).index(label) for label in LABELS]
        values = classifier.predict_proba(bundle['vectorizer'].transform(texts))[:, order]
        if (values.shape != (len(examples), len(LABELS)) or not np.isfinite(values).all()
                or (values < 0).any() or (values > 1).any()
                or not np.allclose(values.sum(axis=1), 1.0)):
            raise ValueError('invalid observer probabilities')
        probabilities.append(values)
    mean = np.mean(probabilities, axis=0)
    return [{'doc_id': row['id'], 'mention_id': mention_id,
             'label': LABELS[int(values.argmax())], 'probabilities': values.tolist()}
            for (row, _), mention_id, values in zip(examples, ids, mean, strict=True)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    if (config['schema_version'] != 'ekg.c5_deployed_observation.v1'
            or config['diagnostic_only'] is not True or config['seed'] != 13
            or config['aggregation'] != 'equal_probability_mean'
            or config['final_valid_accessed'] is not False or len(config['models']) != 5
            or sklearn.__version__ != config['sklearn_version']):
        raise ValueError('frozen observation deployment configuration drift')
    if sha256_file(Path(__file__)) != config['entrypoint_sha256']:
        raise ValueError('deployment entrypoint drift')
    for path, expected in config['input_sha256'].items():
        if sha256_file(Path(path)) != expected:
            raise ValueError(f'input hash drift: {path}')
    manifest = json.loads(Path(config['manifest']).read_text())
    if manifest['dataset'] != 'maven_ere' or manifest['split_role'] != 'internal-dev':
        raise ValueError('deployment is internal-dev only')
    producer = json.loads(Path(config['producer_summary']).read_text())
    provenance = json.loads(Path(config['producer_provenance']).read_text())
    if sha256_file(Path(config['producer_summary'])) != provenance['summary_sha256']:
        raise ValueError('producer provenance drift')
    records = [json.loads(line) for line in Path(config['input']).read_text().splitlines()]
    validate_scope(producer, records, set(load_manifest_ids(Path(config['manifest']))))
    for path, fold in zip(config['models'], producer['folds'], strict=True):
        if sha256_file(Path(path)) != fold['model_sha256']:
            raise ValueError('observer model provenance drift')
    output = Path(config['output'])
    if output.exists():
        raise FileExistsError(output)
    rows = predict_documents(records, [joblib.load(path) for path in config['models']])
    output.mkdir(parents=True, exist_ok=False)
    with (output / 'probabilities.jsonl').open('x') as handle:
        for row in rows:
            handle.write(json.dumps(row, allow_nan=False) + '\n')
    metadata = {'diagnostic_only': True, 'seed': 13, 'fit_calls': 0,
                'documents': len(records), 'mentions': len(rows), 'class_order': list(LABELS),
                'prediction_counts': dict(Counter(row['label'] for row in rows)),
                'split_role': 'internal-dev', 'final_valid_accessed': False,
                'consumer_factuality_labels_accessed': False, 'model_location': 'local only',
                'config_sha256': sha256_file(args.config),
                'input_sha256': config['input_sha256'],
                'aggregation': config['aggregation'], 'entrypoint_sha256': sha256_file(
                    Path(__file__)), 'probabilities_sha256': sha256_file(
                        output / 'probabilities.jsonl'),
                'limitations': ['Fixed weak auxiliary observer, not a method contribution',
                                'No coreference prediction or main metric produced']}
    (output / 'metadata.json').write_text(json.dumps(metadata, indent=2, sort_keys=True))
    print(json.dumps({key: metadata[key] for key in
                      ('documents', 'mentions', 'prediction_counts', 'fit_calls')}, indent=2))


if __name__ == '__main__':
    main()
