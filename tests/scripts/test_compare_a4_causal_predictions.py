"""Native causal contrasts must pool counts and preserve document pairing."""
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

from ekg.relations.maven_ere_official import empty_official_prediction

spec = importlib.util.spec_from_file_location(
    'compare_a4_causal_predictions',
    Path(__file__).resolve().parents[2] / 'scripts/compare_a4_causal_predictions.py',
)
assert spec and spec.loader
m = importlib.util.module_from_spec(spec)


@pytest.fixture(autouse=True)
def script_path(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))


def load():
    spec.loader.exec_module(m)
    return m


def test_pooled_micro_f1_is_not_mean_document_f1():
    mod = load()
    left = np.array([[1, 0, 0], [0, 0, 9]])
    right = np.array([[0, 0, 1], [0, 0, 9]])
    out = mod.paired_counts(left, right, draws=10000, seed=13)
    assert out['delta_pp'] == pytest.approx(200 / 11)
    assert out['ci_lo_pp'] == 0
    assert out['ci_hi_pp'] == 100
    assert mod.paired_counts(left, left, draws=99, seed=13)['ci_hi_pp'] == 0


def test_wrong_subtype_counts_fp_and_fn_and_cartesian_gold_is_expanded():
    mod = load()
    raw = {'id': 'd', 'events': [
        {'id': 'e1', 'mention': [{'id': 'a'}, {'id': 'b'}]},
        {'id': 'e2', 'mention': [{'id': 'c'}]},
    ], 'causal_relations': {'CAUSE': [['e1', 'e2']], 'PRECONDITION': []}}
    left = empty_official_prediction(raw)
    left['causal_relations']['CAUSE'] = [['a', 'c']]
    right = empty_official_prediction(raw)
    right['causal_relations']['PRECONDITION'] = [['a', 'c']]
    result = mod.compare({'d': raw}, {'d': left}, {'d': right}, digest=None,
                         draws=50, seed=13)
    assert result['left_counts'] == [1, 0, 1]
    assert result['right_counts'] == [0, 1, 2]
    assert result['true_positive_exchange'] == {'shared': 0, 'recovered': 1, 'lost': 0}
    assert result['paired']['delta_pp'] == pytest.approx(200 / 3)
    with pytest.raises(ValueError, match='document IDs differ'):
        mod.compare({'d': raw}, {}, {'d': right}, digest=None, draws=5, seed=13)


def test_independent_official_metric_mismatch_fails():
    mod = load()
    with pytest.raises(ValueError, match='official scorer'):
        mod.check_official([1, 0, 1], {'causal_f1': 90})


def test_final_valid_is_rejected_before_gold_or_predictions_are_read(tmp_path, monkeypatch):
    mod = load()
    path = tmp_path / 'manifest.json'
    path.write_text(json.dumps({'split_role': 'final-valid'}))
    monkeypatch.setattr('sys.argv', [
        'compare_a4_causal_predictions.py', '--gold', '/absent', '--pred', '/absent',
        '--manifest', str(path), '--evaluator', '/absent', '--plan', '/absent',
        '--output', str(tmp_path / 'out.json'),
    ])
    with pytest.raises(ValueError, match='internal-dev'):
        mod.main()


def test_real_official_scorer_cli_and_frozen_comparator_identity(tmp_path, monkeypatch):
    mod = load()
    from ekg.core.stage_bundle import sha256_file
    from ekg.relations.maven_ere_official import candidate_population_digest

    raw = {'id': 'd', 'events': [
        {'id': 'e1', 'mention': [{'id': 'a'}]},
        {'id': 'e2', 'mention': [{'id': 'b'}]},
    ], 'causal_relations': {'CAUSE': [['e1', 'e2']], 'PRECONDITION': []}}
    prediction = empty_official_prediction(raw)
    prediction['causal_relations']['CAUSE'] = [['a', 'b']]
    gold, pred, control, manifest = [tmp_path / name for name in
                                      ('gold.jsonl', 'pred.jsonl', 'control.jsonl', 'manifest')]
    gold.write_text(json.dumps(raw) + '\n')
    pred.write_text(json.dumps(prediction) + '\n')
    control.write_text(json.dumps(empty_official_prediction(raw)) + '\n')
    manifest.write_text(json.dumps({'split_role': 'internal-dev', 'doc_ids': ['d']}))
    evaluator = Path('data/protocols/v6/tools/maven_ere_evaluate.py')
    plan = tmp_path / 'plan.json'
    plan.write_text(json.dumps({
        'gold_sha256': sha256_file(gold), 'dev_manifest_sha256': sha256_file(manifest),
        'evaluator_sha256': sha256_file(evaluator), 'documents': 1,
        'candidate_digest': candidate_population_digest({'d': raw})[0],
        'comparators': [{'name': 'control', 'predictions': str(control),
                         'sha256': sha256_file(control)}],
        'paired_analysis': {'resamples': 100, 'rng_seed': 13, 'interpretation': 'single seed'},
        'limitations': [],
    }))
    output = tmp_path / 'comparison.json'
    argv = ['compare_a4_causal_predictions.py']
    for name, path in [('gold', gold), ('pred', pred), ('manifest', manifest),
                       ('evaluator', evaluator), ('plan', plan), ('output', output)]:
        argv.extend(['--' + name, str(path)])
    monkeypatch.setattr('sys.argv', argv)
    assert mod.main() == 0
    row = json.loads(output.read_text())['contrasts']['control']
    assert row['left_official']['causal_f1'] == 100
    assert row['paired']['delta_pp'] == 100
    with pytest.raises(FileExistsError):
        mod.main()
    output.unlink()
    control.write_text('changed')
    with pytest.raises(ValueError, match='comparator drift'):
        mod.main()
    assert not output.exists()
