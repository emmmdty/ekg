"""Check structural implication hypotheses on the original native training graph only."""
from __future__ import annotations

import argparse
import json
from itertools import combinations, permutations
from pathlib import Path

from ekg.core.stage_bundle import sha256_file
from ekg.relations.maven_ere_official import records_by_id


def audit(records):
    masks = {str(i): {'event_pairs': [0, 0, 0], 'mention_pairs': [0, 0, 0]}
             for i in range(16)}
    unordered = {name: {'event_pairs': [0, 0], 'mention_pairs': [0, 0]}
                 for name in ['either_chain', 'fork', 'collider']}
    native, distinct = [0, 0, 0], [0, 0, 0]
    self_pairs = self_units = events_total = mentions_total = 0
    counterexamples, per_doc = {}, []
    for doc_id, row in records.items():
        if doc_id != row['id']:
            raise ValueError('record ID mismatch')
        members = {}
        all_mentions = set()
        for event in row['events']:
            eid = event['id']
            mids = [m['id'] for m in event['mention']]
            if eid in members or not mids or len(set(mids)) != len(mids):
                raise ValueError('duplicate event/mention or empty event')
            if all_mentions.intersection(mids):
                raise ValueError('mention has multiple event owners')
            all_mentions.update(mids)
            members[eid] = len(mids)
        if set(row['causal_relations']) != {'PRECONDITION', 'CAUSE'}:
            raise ValueError('complete native subtypes required')
        labels = {}
        incoming, outgoing = {e: set() for e in members}, {e: set() for e in members}
        for name, edges in row['causal_relations'].items():
            for a, b in edges:
                if a not in members or b not in members or a == b or (a, b) in labels:
                    raise ValueError('invalid/duplicate/overlapping native edge')
                labels[a, b] = ['NONE', 'PRECONDITION', 'CAUSE'].index(name)
                outgoing[a].add(b)
                incoming[b].add(a)
        dm = {str(i): [0, 0, 0] for i in range(16)}
        for a, b in permutations(members, 2):
            chain = outgoing[a] & incoming[b]
            reverse = outgoing[b] & incoming[a]
            fork = incoming[a] & incoming[b]
            collider = outgoing[a] & outgoing[b]
            mask = int(bool(chain)) + 2 * bool(reverse) + 4 * bool(fork) + 8 * bool(collider)
            label, weight = labels.get((a, b), 0), members[a] * members[b]
            masks[str(mask)]['event_pairs'][label] += 1
            masks[str(mask)]['mention_pairs'][label] += weight
            dm[str(mask)][label] += 1
            native[label] += weight
            distinct[label] += 1
        for a, b in combinations(members, 2):
            witnesses = {
                'either_chain': (outgoing[a] & incoming[b]) | (outgoing[b] & incoming[a]),
                'fork': incoming[a] & incoming[b], 'collider': outgoing[a] & outgoing[b]}
            exists = int((a, b) in labels or (b, a) in labels)
            for name, nodes in witnesses.items():
                if not nodes:
                    continue
                unordered[name]['event_pairs'][exists] += 1
                unordered[name]['mention_pairs'][exists] += members[a] * members[b]
                if not exists and name not in counterexamples:
                    counterexamples[name] = {
                        'document_id': doc_id, 'event_pair': [a, b],
                        'witness_event': sorted(nodes)[0], 'annotation_both_directions': 'NONE'}
        sp = sum(n * (n - 1) for n in members.values())
        su = sum(n > 1 for n in members.values())
        self_pairs += sp
        self_units += su
        native[0] += sp
        events_total += len(members)
        mentions_total += len(all_mentions)
        per_doc.append({'document_id': doc_id, 'distinct_event_masks': dm,
                        'within_coref_ordered_pairs': sp, 'within_coref_event_self_units': su})
    if [sum(v['event_pairs'][i] for v in masks.values()) for i in range(3)] != distinct:
        raise ValueError('event denominator does not conserve')
    expanded = [sum(v['mention_pairs'][i] for v in masks.values()) for i in range(3)]
    expanded[0] += self_pairs
    if expanded != native:
        raise ValueError('native denominator does not conserve')
    return {'documents': len(records), 'events': events_total, 'mentions': mentions_total,
            'native_class_counts': native, 'distinct_event_class_counts': distinct,
            'within_coref_ordered_pairs': self_pairs, 'within_coref_event_self_units': self_units,
            'masks': masks, 'unordered': unordered, 'counterexamples': counterexamples,
            'per_doc': per_doc}


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
            raise ValueError(f'native motif source/input drift: {path}')
    with Path(cfg['train_raw']).open() as stream:
        records = records_by_id((json.loads(line) for line in stream), source=cfg['train_raw'])
    if set(records) != set(manifest['doc_ids']) or len(records) != manifest['doc_count']:
        raise ValueError('complete frozen train population required')
    report = audit(records)
    if report['native_class_counts'] != cfg['expected_native_class_counts']:
        raise ValueError('native population disagrees with existing frozen train')
    output = Path(cfg['output'])
    output.mkdir(parents=True, exist_ok=False)
    per_doc = report.pop('per_doc')
    report.update(schema_version='ekg.a4_native_motif_audit.v1', status='complete',
                  config_sha256=sha256_file(args.config), encoder_calls=0, optimizer_steps=0,
                  final_valid_accessed=False, method_admitted=False,
                  limitations=[
                      'Gold other edges are oracle information, unavailable at inference.',
                      'Annotation-NONE is not a world noncausal claim.',
                      'Motif association does not establish an intervention or a new method.',
                      'Overlapping motifs are retained; event/mention denominators differ.',
                  ])
    (output / 'per_doc.json').write_text(json.dumps(per_doc, indent=2) + '\n')
    (output / 'config.json').write_bytes(args.config.read_bytes())
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
