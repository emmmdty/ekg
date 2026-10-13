#!/usr/bin/env python
"""Read-only selected-antecedent error coverage; no changed cluster or main metric."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path

from ekg.core.protocol import load_manifest_ids
from ekg.core.stage_bundle import sha256_file


def profile(gold, cache, labels):
    identity = {}
    for event in gold['events']:
        for mention in event['mention']:
            if mention['id'] in identity:
                raise ValueError('duplicate gold mention')
            identity[mention['id']] = event['id']
    ids = cache['mentions']
    if (gold['id'] != cache['id'] or len(ids) != len(set(ids)) or set(ids) != set(identity)
            or any(f"{gold['id']}::{mention}" not in labels for mention in ids)):
        raise ValueError('cache/gold/observation coverage mismatch')
    if len(cache['probabilities']) != len(ids):
        raise ValueError('probability coverage mismatch')
    result = Counter(mentions=len(ids), selected_links=0, selected_false_links=0,
                     selected_true_links=0, different_observation_false_links=0,
                     different_observation_true_links=0, all_candidates_different_observation=0,
                     dummy_selections=0, antecedent_candidates=0)
    for index, probabilities in enumerate(cache['probabilities']):
        if (len(probabilities) != index + 1 or not all(
                math.isfinite(value) and 0 <= value <= 1 for value in probabilities)
                or not math.isclose(sum(probabilities), 1, abs_tol=1e-5)):
            raise ValueError('invalid probability row')
        label = labels[f"{gold['id']}::{ids[index]}"]
        different = [label != labels[f"{gold['id']}::{previous}"] for previous in ids[:index]]
        result['antecedent_candidates'] += index
        result['all_candidates_different_observation'] += sum(different)
        antecedent = max(range(index + 1), key=probabilities.__getitem__)
        if antecedent == index:
            result['dummy_selections'] += 1
            continue
        result['selected_links'] += 1
        kind = 'true' if identity[ids[index]] == identity[ids[antecedent]] else 'false'
        result[f'selected_{kind}_links'] += 1
        if different[antecedent]:
            result[f'different_observation_{kind}_links'] += 1
    return dict(result)


def typed_gold_view(gold):
    # Official ERE types live on events; this analysis uses a mention-local view.
    return {**gold, 'events': [{**event, 'mention': [
        {**mention, 'type': event['type']} for mention in event['mention']]}
        for event in gold['events']]}


def geometry_profile(gold, cache, observations):
    mentions = {mention['id']: (event['id'], mention['type']) for event in gold['events']
                for mention in event['mention']}
    distances = {bucket: {'true': [], 'false': []} for bucket in ('all', 'same_type')}
    ids = cache['mentions']
    for index, values in enumerate(cache['probabilities']):
        antecedent = max(range(index + 1), key=values.__getitem__)
        if antecedent == index:
            continue
        current, previous = ids[index], ids[antecedent]
        q = observations[f"{gold['id']}::{current}"]
        r = observations[f"{gold['id']}::{previous}"]
        for vector in (q, r):
            if (len(vector) != 5 or not all(math.isfinite(v) and 0 <= v <= 1 for v in vector)
                    or not math.isclose(sum(vector), 1.0, abs_tol=1e-5)):
                raise ValueError('invalid observation probability vector')
        distance = 0.5 * sum((a - b) ** 2 for a, b in zip(q, r, strict=True))
        kind = 'true' if mentions[current][0] == mentions[previous][0] else 'false'
        distances['all'][kind].append(distance)
        if mentions[current][1] == mentions[previous][1]:
            distances['same_type'][kind].append(distance)
    return {bucket: {key: value for kind, values in groups.items() for key, value in (
        (f'{kind}_links', len(values)),
        (f'{kind}_mean_distance', sum(values) / len(values) if values else None))}
            for bucket, groups in distances.items()}


def geometry_summary(documents, bucket):
    import numpy as np

    differences = [row[bucket]['false_mean_distance'] - row[bucket]['true_mean_distance']
                   for row in documents if row[bucket]['false_mean_distance'] is not None
                   and row[bucket]['true_mean_distance'] is not None]
    result = {'paired_documents': len(differences), 'mean_false_minus_true': None,
              'bootstrap95': None, 'bootstrap_draws': 2000, 'bootstrap_seed': 13}
    if differences:
        result['mean_false_minus_true'] = float(np.mean(differences))
    if len(differences) >= 2:
        means = np.random.default_rng(13).choice(
            differences, size=(2000, len(differences)), replace=True).mean(axis=1)
        result['bootstrap95'] = np.quantile(means, [0.025, 0.975]).tolist()
    return result


def main():
    from export_official_coref_cpu import validate_cache_document

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    if (config['diagnostic_only'] is not True or config['final_valid_accessed'] is not False
            or config['schema_version'] not in (
                'ekg.c5_observation_overlap.v1', 'ekg.c5_observation_geometry.v1')):
        raise ValueError('diagnostic role drift')
    continuous = config['schema_version'] == 'ekg.c5_observation_geometry.v1'
    if continuous and config['distance'] != 'half_squared_l2':
        raise ValueError('frozen probability geometry drift')
    if sha256_file(Path(__file__)) != config['entrypoint_sha256']:
        raise ValueError('overlap entrypoint drift')
    for path, expected in config['input_sha256'].items():
        if sha256_file(Path(path)) != expected:
            raise ValueError(f'input hash drift: {path}')
    manifest = json.loads(Path(config['manifest']).read_text())
    if manifest['dataset'] != 'maven_ere' or manifest['split_role'] != 'internal-dev':
        raise ValueError('overlap is internal-dev only')
    ids = set(load_manifest_ids(Path(config['manifest'])))
    gold = {row['id']: row for row in map(
        json.loads, Path(config['gold']).read_text().splitlines())}
    cache = [json.loads(line) for line in Path(config['scores']).read_text().splitlines()]
    if len(cache) != len(ids) or {row['id'] for row in cache} != ids or set(gold) != ids:
        raise ValueError('document population mismatch')
    observer = json.loads(Path(config['observation_metadata']).read_text())
    if (observer['fit_calls'] != 0 or observer['consumer_factuality_labels_accessed'] is not False
            or observer['final_valid_accessed'] is not False
            or observer['probabilities_sha256'] != sha256_file(Path(config['observations']))):
        raise ValueError('deployed observer lineage drift')
    observations = [json.loads(line) for line in
                    Path(config['observations']).read_text().splitlines()]
    labels = {row['mention_id']: row['label'] for row in observations}
    vectors = {row['mention_id']: row['probabilities'] for row in observations}
    population = {f"{row['id']}::{mention}" for row in cache for mention in row['mentions']}
    if len(labels) != len(observations) or set(labels) != population:
        raise ValueError('observation mention coverage mismatch')
    documents, totals = [], Counter()
    for row in cache:
        validate_cache_document(row)
        result = profile(gold[row['id']], row, labels)
        totals.update(result)
        if continuous:
            result.update(geometry_profile(typed_gold_view(gold[row['id']]), row, vectors))
        documents.append({'id': row['id'], **result})
    output = Path(config['output'])
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True, exist_ok=False)
    (output / 'documents.jsonl').write_text(''.join(json.dumps(row) + '\n' for row in documents))
    report = {'diagnostic_only': True, 'final_valid_accessed': False,
              'documents': len(documents), 'totals': dict(totals),
              'affected_false_link_documents': sum(
                  row['different_observation_false_links'] > 0 for row in documents),
              'affected_true_link_documents': sum(
                  row['different_observation_true_links'] > 0 for row in documents),
              'config_sha256': sha256_file(args.config), 'input_sha256': config['input_sha256'],
              'documents_sha256': sha256_file(output / 'documents.jsonl'),
              'limitations': ['Selected-link errors are not MUC link errors or gains',
                              'No changed coreference predictions or method training',
                              'Observed dev is exploratory, not confirmatory',
                              'Counted pair dependence cannot establish document-level power']}
    if continuous:
        report['probability_geometry'] = {bucket: geometry_summary(documents, bucket)
                                          for bucket in ('all', 'same_type')}
        report['distance'] = config['distance']
    (output / 'report.json').write_text(json.dumps(report, indent=2, sort_keys=True))
    print(json.dumps({key: report[key] for key in ('documents', 'totals',
                     'affected_false_link_documents', 'affected_true_link_documents')}, indent=2))
    if continuous:
        print(json.dumps(report['probability_geometry'], indent=2))


if __name__ == '__main__':
    main()
