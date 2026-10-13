#!/usr/bin/env python
"""Exploratory gold-conditioned antecedent surgeries; never deployable predictions."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path

from ekg.core.protocol import load_manifest_ids
from ekg.core.stage_bundle import sha256_file
from ekg.relations.maven_ere_official import validate_official_predictions

ARMS = ('baseline', 'null_only', 'requires_ranking', 'all')
NULL_ERRORS = {'false_first_link', 'false_dummy_rank_correct'}
RANK_ERRORS = {'false_dummy_rank_wrong', 'wrong_antecedent'}


def clusters_from_antecedents(ids, antecedents):
    roots, groups = [], {}
    for i, j in enumerate(antecedents):
        if not 0 <= j <= i:
            raise ValueError('invalid antecedent index')
        root = i if j == i else roots[j]
        roots.append(root)
        groups.setdefault(root, []).append(ids[i])
    return sorted(sorted(group) for group in groups.values() if len(group) > 1)


def analyze_document(gold, cache, types):
    identities, sizes, gold_types = {}, {}, {}
    for event in gold['events']:
        for mention in event['mention']:
            mid = mention['id']
            if mid in identities:
                raise ValueError('duplicate gold mention')
            identities[mid] = event['id']
            sizes[mid] = len(event['mention'])
            gold_types[mid] = event['type']
    ids, logits = cache['mentions'], cache['pair_logits']
    if (gold['id'] != cache['id'] or len(ids) != len(set(ids))
            or set(ids) != set(identities) or set(ids) != set(types)
            or types != gold_types):
        raise ValueError('identity/type population mismatch')
    if len(logits) != len(ids) or any(
            len(row) != i or not all(math.isfinite(v) for v in row)
            for i, row in enumerate(logits)):
        raise ValueError('invalid logit shape/value')
    decisions, selected = [], {arm: [] for arm in ARMS}
    for i, mid in enumerate(ids):
        legal = [j for j in range(i) if types[ids[j]] == types[mid]]
        predecessors = [j for j in legal if identities[ids[j]] == identities[mid]]
        # Original dummy logit is exactly zero; ties choose the first index.
        scores = [*logits[i], 0.0]
        chosen = max([*legal, i], key=scores.__getitem__)
        best_real = max(legal, key=scores.__getitem__) if legal else None
        if chosen == i:
            if not predecessors:
                category = 'correct_dummy'
            elif best_real in predecessors:
                category = 'false_dummy_rank_correct'
            else:
                category = 'false_dummy_rank_wrong'
        elif chosen in predecessors:
            category = 'correct_link'
        elif not predecessors:
            category = 'false_first_link'
        else:
            category = 'wrong_antecedent'
        oracle = max(predecessors, key=scores.__getitem__) if predecessors else i
        for arm in ARMS:
            repair = (arm == 'all' or arm == 'null_only' and category in NULL_ERRORS
                      or arm == 'requires_ranking' and category in RANK_ERRORS)
            selected[arm].append(oracle if repair else chosen)
        decisions.append({
            'mention_id': mid, 'category': category, 'gold_has_predecessor': bool(predecessors),
            'gold_cluster_size': sizes[mid], 'legal_real_candidates': len(legal),
            'selected_antecedent': None if chosen == i else ids[chosen],
            'best_real_logit': scores[best_real] if best_real is not None else None,
            'best_gold_logit': scores[oracle] if predecessors else None,
        })
    clusters = {arm: clusters_from_antecedents(ids, selected[arm]) for arm in ARMS}
    expected = sorted(sorted(m['id'] for m in e['mention'])
                      for e in gold['events'] if len(e['mention']) > 1)
    if clusters['all'] != expected:
        raise ValueError('full oracle failed to recover gold clusters')
    return {'decisions': decisions, 'clusters': clusters}


def main():
    from export_official_coref_cpu import require_parity, validate_cache_document, validate_records
    from report_coref_error_profile import _load_evaluator
    from report_r1_prospective_power import _coref_document_counts, _muc_score

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    if (config['schema_version'] != 'ekg.c5_decision_audit.v1'
            or config['diagnostic_only'] is not True or config['final_valid_accessed'] is not False
            or config['arms'] != list(ARMS) or config['exploratory'] is not True):
        raise ValueError('diagnostic scope drift')
    if sha256_file(Path(__file__)) != config['entrypoint_sha256']:
        raise ValueError('entrypoint drift')
    for path, expected in config['input_sha256'].items():
        if sha256_file(Path(path)) != expected:
            raise ValueError(f'input drift: {path}')
    manifest = json.loads(Path(config['manifest']).read_text())
    if manifest['dataset'] != 'maven_ere' or manifest['split_role'] != 'internal-dev':
        raise ValueError('internal-dev diagnostic only')
    ids = set(load_manifest_ids(Path(config['manifest'])))

    def load(path):
        rows = [json.loads(line) for line in Path(path).read_text().splitlines()]
        by_id = {row['id']: row for row in rows}
        if len(rows) != len(by_id) or set(by_id) != ids:
            raise ValueError(f'document coverage mismatch: {path}')
        return by_id

    gold, cache, original = [load(config[key]) for key in ('gold', 'scores', 'predictions')]
    inputs = validate_records(list(load(config['input']).values()), ids)
    evaluator = _load_evaluator(Path(config['evaluator']))
    source_lock = json.loads(Path(config['source_lock']).read_text())
    if sha256_file(Path(config['evaluator'])) != source_lock['evaluator']['sha256']:
        raise ValueError('P1 evaluator drift')
    output = Path(config['output'])
    if output.exists():
        raise FileExistsError(output)
    predictions = {arm: {} for arm in ARMS}
    documents, totals = [], Counter()
    for doc_id in sorted(ids):
        validate_cache_document(cache[doc_id])
        types = {m['id']: m['type'] for m in inputs[doc_id]['event_mentions']}
        result = analyze_document(gold[doc_id], cache[doc_id], types)
        require_parity(original[doc_id], result['clusters']['baseline'], cache[doc_id]['mentions'])
        counts = Counter(row['category'] for row in result['decisions'])
        totals.update(counts)
        for arm in ARMS:
            predictions[arm][doc_id] = {**original[doc_id], 'coreference': result['clusters'][arm]}
        documents.append({'id': doc_id, 'category_counts': dict(counts),
                          'decisions': result['decisions']})
    import numpy as np

    metrics, counts_by_arm = {}, {}
    for arm in ARMS:
        validate_official_predictions(gold, predictions[arm],
                                      expected_candidate_digest=config['candidate_digest'])
        metrics[arm] = evaluator.evaluate_coreference(gold, predictions[arm])
        counts = np.array([_coref_document_counts(gold[d], predictions[arm][d])
                           for d in sorted(ids)])
        counts_by_arm[arm] = counts
        independent = float(_muc_score(counts.sum(axis=0))[0]) * 100
        if not math.isclose(independent, metrics[arm]['muc_f1'], abs_tol=1e-9):
            raise ValueError(f'independent MUC mismatch: {arm}')
    output.mkdir(parents=True, exist_ok=False)
    for arm in ARMS[1:]:
        (output / f'oracle_{arm}.jsonl').write_text(''.join(
            json.dumps(predictions[arm][d], sort_keys=True) + '\n' for d in sorted(ids)))
    (output / 'documents.jsonl').write_text(''.join(json.dumps(row) + '\n' for row in documents))
    (output / 'paired_counts.jsonl').write_text(''.join(json.dumps({
        'id': d, **{arm: counts_by_arm[arm][i].tolist() for arm in ARMS}}) + '\n'
        for i, d in enumerate(sorted(ids))))
    report = {'schema_version': 'ekg.c5_decision_audit.report.v1',
              'diagnostic_only': True, 'exploratory': True, 'deployable': False,
              'final_valid_accessed': False, 'documents': len(ids),
              'category_counts': dict(totals), 'official_metrics': metrics,
              'muc_counts': {arm: counts_by_arm[arm].sum(axis=0).tolist() for arm in ARMS},
              'baseline_parity': 'all documents exact', 'independent_muc': 'all arms exact',
              'config_sha256': sha256_file(args.config), 'input_sha256': config['input_sha256'],
              'limitations': [
                  'Gold-conditioned oracle; no deployable signal or method improvement',
                  'Explored internal-dev; no confirmatory power or causal attribution',
                  'Partial oracle effects need not add; first mentions differ from singletons']}
    (output / 'report.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    manifest = {p.name: sha256_file(p) for p in sorted(output.iterdir())}
    (output / 'artifact_hashes.json').write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    print(json.dumps({key: report[key] for key in (
        'category_counts', 'official_metrics', 'muc_counts', 'baseline_parity')}, indent=2))


if __name__ == '__main__':
    main()
