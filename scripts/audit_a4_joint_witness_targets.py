"""Count native joint witness supervision without calling a model or reading dev."""
from __future__ import annotations

import argparse
import json
from itertools import permutations
from pathlib import Path

import numpy as np

from ekg.core.stage_bundle import sha256_file
from ekg.relations.maven_ere_official import records_by_id

PATTERNS = ('chain', 'reverse_chain', 'fork', 'collider')


def count_triples(labels):
    matrix = np.asarray(labels)
    if (matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]
            or not np.issubdtype(matrix.dtype, np.integer)
            or not np.all(np.diag(matrix) == -1)):
        raise ValueError('square integer native matrix with excluded diagonal required')
    n = len(matrix)
    if not np.isin(matrix[~np.eye(n, dtype=bool)], [0, 1, 2]).all():
        raise ValueError('invalid native class')
    counts = {name: np.zeros((3, 3, 3), dtype=np.int64) for name in PATTERNS}
    for w in range(n):
        other = np.delete(np.arange(n), w)
        target = matrix[np.ix_(other, other)]
        valid = ~np.eye(n - 1, dtype=bool)
        inc, out = matrix[other, w], matrix[w, other]
        legs = ((inc, out), (out, inc), (out, out), (inc, inc))
        for name, (a, b) in zip(PATTERNS, legs, strict=True):
            code = 9 * a[:, None] + 3 * b[None, :] + target
            counts[name] += np.bincount(code[valid], minlength=27).reshape(3, 3, 3)
    base = np.bincount(matrix[~np.eye(n, dtype=bool)], minlength=3)
    for values in counts.values():
        if not np.array_equal(values.sum(axis=(0, 1)), base * max(n - 2, 0)):
            raise ValueError('per-target witness multiplicity does not conserve')
    return counts


def audit(records, features, targets):
    if set(records) != set(features) or set(records) != set(targets):
        raise ValueError('complete matching native train IDs required')
    total = {name: np.zeros((3, 3, 3), dtype=np.int64) for name in PATTERNS}
    event_total = {name: np.zeros((3, 3, 3), dtype=np.int64) for name in PATTERNS}
    native = np.zeros(3, dtype=np.int64)
    triples = event_triples = distinct_owner_triples = no_witness_pairs = 0
    maximum = {'document_id': None, 'mentions': 0, 'triples': 0}
    per_doc = []
    for did, row in records.items():
        if any(item['id'] != did for item in [row, features[did], targets[did]]):
            raise ValueError('document ID mismatch')
        owners, sizes = {}, {}
        for event in row['events']:
            eid = event['id']
            if eid in sizes or not event['mention']:
                raise ValueError('duplicate or empty event')
            sizes[eid] = len(event['mention'])
            for mention in event['mention']:
                if mention['id'] in owners:
                    raise ValueError('duplicate mention')
                owners[mention['id']] = eid
        mids = features[did]['mention_ids']
        y = targets[did]['target']
        n, e = len(mids), len(sizes)
        if (not n or len(set(mids)) != n or set(mids) != set(owners)
                or len(y) != n * (n - 1)
                or any(type(v) is not int or v not in (0, 1, 2) for v in y)):
            raise ValueError('complete ordered native candidates required')
        if set(row['causal_relations']) != {'CAUSE', 'PRECONDITION'}:
            raise ValueError('complete native relation subtypes required')
        gold = {}
        for label, name in enumerate(('NONE', 'PRECONDITION', 'CAUSE')):
            if label == 0:
                continue
            for a, b in row['causal_relations'][name]:
                if a not in sizes or b not in sizes or a == b or (a, b) in gold:
                    raise ValueError('invalid native event edge')
                gold[a, b] = label
        expected = [gold.get((owners[a], owners[b]), 0) for a, b in permutations(mids, 2)]
        if y != expected:
            raise ValueError('cached supervision disagrees with raw native expansion')
        matrix = np.full((n, n), -1, dtype=np.int64)
        matrix[~np.eye(n, dtype=bool)] = y
        em = np.full((e, e), -1, dtype=np.int64)
        em[~np.eye(e, dtype=bool)] = [gold.get(pair, 0) for pair in permutations(sizes, 2)]
        dc, ec = count_triples(matrix), count_triples(em)
        for name in PATTERNS:
            total[name] += dc[name]
            event_total[name] += ec[name]
        native += np.bincount(y, minlength=3)
        nt = n * (n - 1) * max(n - 2, 0)
        triples += nt
        event_triples += e * (e - 1) * max(e - 2, 0)
        distinct_owner_triples += n**3 - 3 * n * sum(x*x for x in sizes.values()) + 2 * sum(
            x**3 for x in sizes.values())
        if n < 3:
            no_witness_pairs += n * (n - 1)
        if n > maximum['mentions']:
            maximum = {'document_id': did, 'mentions': n, 'triples': nt}
        per_doc.append({'document_id': did, 'mentions': n, 'events': e,
                        'native': {k: v.tolist() for k, v in dc.items()},
                        'distinct_event': {k: v.tolist() for k, v in ec.items()}})
    return {'documents': len(records), 'native_class_counts': native.tolist(),
            'mention_triples': triples, 'distinct_event_triples': event_triples,
            'mention_triples_with_three_distinct_events': distinct_owner_triples,
            'native_pairs_without_witness': no_witness_pairs, 'max_document': maximum,
            'native': {k: v.tolist() for k, v in total.items()},
            'distinct_event': {k: v.tolist() for k, v in event_total.items()}, 'per_doc': per_doc}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path)
    args = parser.parse_args()
    cfg = json.loads(args.config.read_text())
    manifest = json.loads(Path(cfg['manifest']).read_text())
    if manifest['split_role'] != 'train' or cfg['final_valid_accessed'] is not False:
        raise ValueError('original train only')
    for path, digest in cfg['pins'].items():
        if sha256_file(Path(path)) != digest:
            raise ValueError(f'witness input/source drift: {path}')
    loaded = []
    for key in ('train_raw', 'features', 'targets'):
        with Path(cfg[key]).open() as stream:
            rows = (json.loads(line) for line in stream)
            if key == 'features':
                rows = ({'id': r['id'], 'mention_ids': r['mention_ids']} for r in rows)
            loaded.append(records_by_id(rows, source=cfg[key]))
    if set(loaded[0]) != set(manifest['doc_ids']):
        raise ValueError('frozen train population mismatch')
    report = audit(*loaded)
    if report['native_class_counts'] != cfg['expected_native_class_counts']:
        raise ValueError('native pair counts disagree with frozen reference')
    output = Path(cfg['output'])
    output.mkdir(parents=True, exist_ok=False)
    per_doc = report.pop('per_doc')
    nt = report['max_document']['triples']
    report.update(schema_version='ekg.a4_joint_witness_targets.v1', status='complete',
                  config_sha256=sha256_file(args.config), method_admitted=False,
                  encoder_calls=0, optimizer_steps=0, final_valid_accessed=False,
                  direct_materialization_bytes={'three_768d_vectors_fp32': nt * 2304 * 4,
                                                'four_3x3_joint_tables_fp32': nt * 36 * 4},
                  limitations=['Counts are not novelty, learnability, power or method benefit.',
                               'Gold identity is diagnostic only; inference may not use it.',
                               ('Tensor sizes are for direct materialization, '
                                'not a universal bound.'),
                               'CUDA, optimizer state and backprop memory remain unmeasured.'])
    (output / 'config.json').write_bytes(args.config.read_bytes())
    (output / 'per_doc.json').write_text(json.dumps(per_doc, indent=2) + '\n')
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
