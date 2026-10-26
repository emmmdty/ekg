"""Audit native train opportunities for same-surface, different-context supervision."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from itertools import permutations
from pathlib import Path

from ekg.core.stage_bundle import sha256_file
from ekg.relations.maven_ere_official import records_by_id


def document_rows(row):
    mentions, owners = {}, {}
    events = {event['id']: event for event in row['events']}
    if len(events) != len(row['events']):
        raise ValueError('duplicate event IDs')
    for eid, event in events.items():
        if not event['mention']:
            raise ValueError('event without mention')
        for m in event['mention']:
            mid, sent = m['id'], m['sent_id']
            a, b = m['offset']
            if (mid in mentions or type(sent) is not int or not 0 <= sent < len(row['tokens'])
                    or type(a) is not int or type(b) is not int
                    or not 0 <= a < b <= len(row['tokens'][sent])):
                raise ValueError('duplicate mention or invalid span')
            surface = ' '.join(' '.join(row['tokens'][sent][a:b]).casefold().split())
            if not surface:
                raise ValueError('empty trigger surface')
            mentions[mid] = (surface, sent, a, b)
            owners[mid] = eid
    if set(row['causal_relations']) != {'CAUSE', 'PRECONDITION'}:
        raise ValueError('complete native subtypes required')
    labels = {}
    for label, edges in row['causal_relations'].items():
        for a, b in edges:
            if a not in events or b not in events or a == b or (a, b) in labels:
                raise ValueError('invalid/overlapping native causal edge')
            labels[a, b] = ['NONE', 'PRECONDITION', 'CAUSE'].index(label)
    text_hash = hashlib.sha256(json.dumps(row['tokens'], ensure_ascii=False).encode()).hexdigest()
    for head, tail in permutations(mentions, 2):
        h, t = mentions[head], mentions[tail]
        key = h[0], t[0]
        event_pair = owners[head], owners[tail]
        yield (key, labels.get(event_pair, 0), row['id'], text_hash, event_pair,
               (text_hash, h[1:], t[1:]))


def audit(records):
    if any(key != row['id'] for key, row in records.items()):
        raise ValueError('record ID mismatch')
    # Retain only groups with a native positive: no NONE-only group can be eligible.
    positive_groups = set()
    for row in records.values():
        for key, label, *_ in document_rows(row):
            if label:
                positive_groups.add(key)
    candidates = []
    native_counts, event_counts = Counter(), Counter()
    support = defaultdict(lambda: [set(), set(), set()])
    signatures = defaultdict(set)
    for row in records.values():
        event_units = {}
        for value in document_rows(row):
            key, label, doc_id, text_hash, event_pair, signature = value
            native_counts[label] += 1
            if event_pair in event_units and event_units[event_pair] != label:
                raise ValueError('event pair has inconsistent native labels')
            event_units[event_pair] = label
            if key in positive_groups:
                candidates.append(value)
                support[key][label].add(text_hash)
                signatures[signature].add(label)
        event_counts.update(event_units.values())
    eligible_counts = Counter()
    eligible_events, eligible_docs, eligible_keys = {}, set(), set()
    group_counts = defaultdict(Counter)
    for key, label, doc_id, text_hash, event_pair, _ in candidates:
        other = (support[key][1] | support[key][2]) if label == 0 else support[key][0]
        if not other or (len(other) == 1 and text_hash in other):
            continue
        eligible_counts[label] += 1
        eligible_events[doc_id, event_pair] = label
        eligible_docs.add(doc_id)
        eligible_keys.add(key)
        group_counts[key][label] += 1
    return {
        'documents': len(records), 'native_class_counts': [native_counts[i] for i in range(3)],
        'induced_event_pair_class_counts': [event_counts[i] for i in range(3)],
        'positive_surface_groups': len(positive_groups),
        'eligible_surface_groups': len(eligible_keys),
        'eligible_native_class_counts': [eligible_counts[i] for i in range(3)],
        'eligible_event_pair_class_counts': [list(eligible_events.values()).count(i)
                                            for i in range(3)],
        'eligible_documents': len(eligible_docs),
        'positive_subtype_conflicting_surface_groups': sum(
            bool(v[1] and v[2]) for v in support.values()),
        'identical_input_conflicting_signatures': sum(len(v) > 1 for v in signatures.values()),
        'groups': [{'surface': list(key), 'eligible_native_class_counts':
                    [group_counts[key][i] for i in range(3)]} for key in sorted(eligible_keys)],
        'limitations': [
            'Native annotation-NONE is not a world noncausal statement.',
            'Natural matching is not a randomized or counterfactual intervention.',
            'Native-induced event-pair units include within-coref self units.',
            'Document text differences do not isolate which semantic factor changed.',
            'Counts establish signal availability, not novelty, learnability or held-out benefit.',
        ],
    }


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
            raise ValueError(f'matched-context source/input drift: {path}')
    with Path(cfg['train_raw']).open() as stream:
        records = records_by_id((json.loads(line) for line in stream), source=cfg['train_raw'])
    if set(records) != set(manifest['doc_ids']) or len(records) != manifest['doc_count']:
        raise ValueError('complete frozen train population required')
    report = audit(records)
    if report['native_class_counts'] != cfg['expected_native_class_counts']:
        raise ValueError('native class population disagrees with frozen training cache')
    output = Path(cfg['output'])
    output.mkdir(parents=True, exist_ok=False)
    groups = report.pop('groups')
    (output/'groups.json').write_text(json.dumps(groups, ensure_ascii=False, indent=2)+'\n')
    report.update(schema_version='ekg.a4_matched_context_audit.v1', status='complete',
                  config_sha256=sha256_file(args.config), encoder_calls=0, optimizer_steps=0,
                  final_valid_accessed=False, signal_only_not_method_admission=True)
    (output/'config.json').write_bytes(args.config.read_bytes())
    (output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
