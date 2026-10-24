"""Compare frozen causal controls using official counts and paired documents."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from report_a4_direction_errors import profile
from report_r1_prospective_power import (
    _bootstrap_document_counts,
    _causal_edges,
    _load_jsonl_by_id,
    _micro_f1,
)
from score_maven_ere_official import _load_evaluator

from ekg.core.protocol import load_manifest_ids
from ekg.core.stage_bundle import sha256_file
from ekg.relations.maven_ere_official import gold_to_official_prediction


def paired_counts(left, right, *, draws, seed):
    left, right = np.asarray(left), np.asarray(right)
    if (left.shape != right.shape or left.ndim != 2 or left.shape[1] != 3
            or not len(left) or draws <= 0 or np.any(left < 0) or np.any(right < 0)):
        raise ValueError('aligned nonnegative per-document TP/FP/FN counts required')
    weights = _bootstrap_document_counts(
        len(left), resamples=draws, rng=np.random.default_rng(seed))
    deltas = (_micro_f1(weights @ left) - _micro_f1(weights @ right)) * 100
    point = float((_micro_f1(left.sum(axis=0)) - _micro_f1(right.sum(axis=0)))[0]) * 100
    return {'delta_pp': point, 'ci_lo_pp': float(np.quantile(deltas, 0.025)),
            'ci_hi_pp': float(np.quantile(deltas, 0.975)),
            'documents': len(left), 'resamples': draws, 'rng_seed': seed}


def check_official(counts, scores):
    value = float(_micro_f1(np.asarray(counts))[0]) * 100
    if not np.isclose(value, scores['causal_f1'], rtol=0, atol=1e-10):
        raise ValueError('pooled counts disagree with official scorer')


def compare(gold, left, right, *, digest, draws, seed):
    profiles = [profile(gold, predictions, expected_candidate_digest=digest)
                for predictions in (left, right)]
    counts = [np.array([[r['true_positive'], r['predicted_positive'] - r['true_positive'],
                        r['gold_positive'] - r['true_positive']]
                       for r in p['documents']], dtype=np.int64) for p in profiles]
    exchanges = {'shared': 0, 'recovered': 0, 'lost': 0}
    by_doc = []
    for key in sorted(gold):
        g = _causal_edges(gold_to_official_prediction(gold[key]))
        a, b = _causal_edges(left[key]) & g, _causal_edges(right[key]) & g
        row = {'shared': len(a & b), 'recovered': len(a - b), 'lost': len(b - a)}
        for name, value in row.items():
            exchanges[name] += value
        by_doc.append({'id': key, **row})
    return {'left_counts': counts[0].sum(axis=0).tolist(),
            'right_counts': counts[1].sum(axis=0).tolist(),
            'paired': paired_counts(*counts, draws=draws, seed=seed),
            'true_positive_exchange': exchanges, 'exchange_by_document': by_doc,
            'left_profile': profiles[0], 'right_profile': profiles[1]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('gold', 'pred', 'manifest', 'evaluator', 'plan', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    if json.loads(args.manifest.read_text())['split_role'] != 'internal-dev':
        raise ValueError('Only internal-dev is allowed for this exploratory comparison')
    if args.output.exists():
        raise FileExistsError(args.output)
    plan = json.loads(args.plan.read_text())
    for path, key in ((args.gold, 'gold_sha256'), (args.manifest, 'dev_manifest_sha256'),
                      (args.evaluator, 'evaluator_sha256')):
        if sha256_file(path) != plan[key]:
            raise ValueError(f'frozen analysis identity drift: {path}')
    gold, left = _load_jsonl_by_id(args.gold), _load_jsonl_by_id(args.pred)
    ids = load_manifest_ids(args.manifest)
    if set(gold) != set(ids) or len(ids) != plan['documents']:
        raise ValueError('complete frozen analysis population required')
    evaluator = _load_evaluator(args.evaluator)
    scores = evaluator.evaluate(gold, left, 'causal')
    rows = {}
    for control in plan['comparators']:
        path = Path(control['predictions'])
        if sha256_file(path) != control['sha256']:
            raise ValueError(f'frozen comparator drift: {path}')
        right = _load_jsonl_by_id(path)
        result = compare(gold, left, right, digest=plan['candidate_digest'],
                         draws=plan['paired_analysis']['resamples'],
                         seed=plan['paired_analysis']['rng_seed'])
        right_scores = evaluator.evaluate(gold, right, 'causal')
        check_official(result['left_counts'], scores)
        check_official(result['right_counts'], right_scores)
        result.update(left_official=scores, right_official=right_scores)
        rows[control['name']] = result
    output = {'schema_version': 'ekg.a4_causal_comparison.v1', 'contrasts': rows,
              'prediction_sha256': sha256_file(args.pred), 'plan_sha256': sha256_file(args.plan),
              'limitations': plan['limitations'] + [plan['paired_analysis']['interpretation']],
              'final_valid_accessed': False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as stream:
        stream.write(json.dumps(output, indent=2) + '\n')
    print(json.dumps({k: v['paired'] for k, v in rows.items()}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
