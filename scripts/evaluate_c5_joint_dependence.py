#!/usr/bin/env python
"""Collect the frozen C41 comparisons only after every valid endpoint is sealed."""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np

from ekg.core.protocol import load_manifest_ids
from ekg.core.stage_bundle import sha256_file
from ekg.relations.maven_ere_official import validate_official_predictions


def endpoint(root, config_sha):
    status = json.loads((root / 'status.json').read_text())
    if status['status'] != 'complete' or status.get('config_sha256') != config_sha:
        raise ValueError('incomplete/mismatched endpoint: ' + str(root))
    for name in ('predictions.jsonl', 'report.json'):
        if sha256_file(root / name) != status['artifact_sha256'][name]:
            raise ValueError('endpoint artifact hash mismatch: ' + str(root / name))
    report = json.loads((root / 'report.json').read_text())
    if (report['status'] != 'complete' or report['epochs'] != 100
            or report['optimizer_steps'] != 8200 or report['microbatches'] != 32800
            or report['config_sha256'] != config_sha or report['final_valid_accessed']
            or not report['cpu_cache_replay_and_source_decoder_parity']):
        raise ValueError('endpoint budget/replay/validity mismatch: ' + str(root))
    if report['checkpoint_sha256'] != status['artifact_sha256']['checkpoint.pt']:
        raise ValueError('endpoint checkpoint identity mismatch: ' + str(root))
    return {'root': str(root), 'config_sha256': config_sha,
            'status_sha256': sha256_file(root / 'status.json'),
            'predictions_sha256': sha256_file(root / 'predictions.jsonl'),
            'report_sha256': sha256_file(root / 'report.json'),
            'checkpoint_sha256': report['checkpoint_sha256'],
            'training_commit': status['commit']}


def paired_comparison(left, right):
    from report_r1_prospective_power import _muc_score

    if left.shape != right.shape or left.ndim != 2 or left.shape[1] != 4 or not len(left):
        raise ValueError('paired document/count population mismatch')
    samples = np.random.default_rng(13).integers(0, len(left), size=(2000, len(left)))
    difference = 100 * (_muc_score(left[samples].sum(1)) - _muc_score(right[samples].sum(1)))
    observed = 100 * float(_muc_score(left.sum(0))[0] - _muc_score(right.sum(0))[0])
    return {'muc_difference_points': observed,
            'interval_95_points': np.quantile(difference, [.025, .975]).tolist(),
            'paired_documents': len(left), 'bootstrap_resamples': 2000, 'rng': 13,
            'exploratory_unadjusted_single_seed': True}


def by_id(path, ids):
    from score_maven_ere_official import _by_id

    records = _by_id(path)
    if set(records) != ids:
        raise ValueError('evaluation document population mismatch: ' + str(path))
    return records


def collect(overlay, plan, endpoint_ids, output):
    from report_coref_error_profile import (
        _cross_check,
        _load_evaluator,
        aggregate,
        profile_document,
    )
    from report_r1_prospective_power import _coref_document_counts, _muc_score

    ids = set(load_manifest_ids(Path(plan['manifest'])))
    gold = by_id(Path(plan['gold']), ids)
    paths = {name: Path(row['root']) / 'predictions.jsonl' for name, row in endpoint_ids.items()}
    paths.update({name: Path(path) for name, path in plan['anchors'].items()})
    evaluator = _load_evaluator(Path(plan['evaluator']))
    metrics, profiles, counts, errors = {}, {}, {}, {}
    documents = sorted(ids)
    for name, path in paths.items():
        pred = by_id(path, ids)
        validate_official_predictions(
            gold, pred, expected_candidate_digest=plan['candidate_digest'])
        score_path = output / (name + '_official.json')
        command = [sys.executable, 'scripts/score_maven_ere_official.py',
            '--evaluator', plan['evaluator'], '--source-lock', plan['source_lock'],
            '--gold', plan['gold'], '--pred', str(path), '--candidate-digest',
            plan['candidate_digest'], '--output', str(score_path)]
        result = subprocess.run(command, text=True, capture_output=True)
        (output / (name + '_official.log')).write_text(result.stdout + result.stderr)
        if result.returncode:
            raise ValueError('official scoring failed: ' + name)
        metrics[name] = json.loads(score_path.read_text())['scores']
        counts[name] = np.array([_coref_document_counts(gold[d], pred[d]) for d in documents])
        if not math.isclose(float(_muc_score(counts[name].sum(0))[0]) * 100,
                            metrics[name]['muc_f1'], abs_tol=1e-9):
            raise ValueError('independent MUC mismatch: ' + name)
        per_doc = {d: profile_document(gold[d], pred[d]) for d in documents}
        profiles[name] = aggregate(list(per_doc.values()))
        _cross_check(evaluator, gold, pred, profiles[name])
        errors[name] = {kind: {(d, *pair) for d, row in per_doc.items() for pair in row[kind]}
                        for kind in ('under_merged', 'over_merged')}
    comparisons = {name: paired_comparison(counts['exact'], rows)
                   for name, rows in counts.items() if name != 'exact'}
    exchanges = {name: {kind: {'recovered_pairs': len(other[kind] - errors['exact'][kind]),
                             'introduced_pairs': len(errors['exact'][kind] - other[kind])}
                       for kind in ('under_merged', 'over_merged')}
                 for name, other in errors.items() if name != 'exact'}
    exact = metrics['exact']
    target = plan['target_reference']
    gates = {'target_gain': exact['muc_f1'] - metrics[target]['muc_f1'] >=
             plan['target_muc_gain_points_over_frozen_strong_control'],
             'positive_controls': all(exact['muc_f1'] > metrics[name]['muc_f1']
                                      for name in plan['must_exceed_positive_controls']),
             'paired_attribution': all(comparisons[right]['muc_difference_points'] > 0
                 and comparisons[right]['interval_95_points'][0] > 0
                 for left, right in plan['primary_attribution_comparisons']),
             'negative_control': exact['muc_f1'] > metrics['shuffle']['muc_f1'],
             'guardrails': all(exact[key] >= metrics[name][key] for key in plan['guardrails']
                               for name in plan['guardrail_reference_arms'])}
    (output / 'document_counts.jsonl').write_text(''.join(json.dumps({'id': d,
        'counts': {name: values[i].tolist() for name, values in counts.items()}}) + '\n'
        for i, d in enumerate(documents)))
    return {'status': 'complete', 'endpoint_identities': endpoint_ids,
            'metrics': metrics, 'paired_comparisons': comparisons, 'profiles': profiles,
            'error_exchanges': exchanges, 'scientific_gates': gates,
            'single_seed_exploration_passed': all(gates.values()),
            'final_confirmation_complete': False, 'final_valid_accessed': False,
            'numerical_repair': overlay['numerical_repair_disclosure'],
            'limitations': plan['limitations']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    args = parser.parse_args()
    overlay = json.loads(args.config.read_text())
    for path, expected in overlay['input_sha256'].items():
        if sha256_file(Path(path)) != expected:
            raise ValueError('evaluation overlay source/input drift: ' + path)
    plan_path = Path(overlay['base_evaluation'])
    plan = json.loads(plan_path.read_text())
    for path, expected in plan['input_sha256'].items():
        if sha256_file(Path(path)) != expected:
            raise ValueError('frozen evaluation input drift: ' + path)
    if set(overlay['endpoints']) != {'marginal', 'root', 'exact', 'mass', 'shuffle'}:
        raise ValueError('fixed five-arm coverage required')
    endpoint_ids = {name: endpoint(Path(row['root']), row['config_sha256'])
                    for name, row in overlay['endpoints'].items()}
    # No gold/prediction scoring is performed before every endpoint check above succeeds.
    output = Path(overlay['output'])
    output.mkdir(parents=True, exist_ok=False)
    status = {'status': 'running', 'config_sha256': sha256_file(args.config),
              'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()}
    try:
        report = collect(overlay, plan, endpoint_ids, output)
        report['evaluation_plan_sha256'] = sha256_file(plan_path)
        (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        status.update(status='complete', artifact_sha256={p.name: sha256_file(p)
                      for p in output.iterdir() if p.is_file()})
    except Exception as exc:
        status.update(status='failed', error=repr(exc))
        raise
    finally:
        (output / 'status.json').write_text(json.dumps(status, indent=2) + '\n')


if __name__ == '__main__':
    main()
