"""Catch label leakage, reversed-pair collapse and native subtype miscounting."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_PATH = Path(__file__).parents[2] / 'scripts/report_a4_surface_generalization.py'


@pytest.fixture(autouse=True)
def script_path(monkeypatch):
    monkeypatch.syspath_prepend(str(_PATH.parent))


def module():
    assert _PATH.exists(), 'surface generalization diagnostic is missing'
    spec = importlib.util.spec_from_file_location('surface_diagnostic', _PATH)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def document():
    return {'id': 'd', 'tokens': [['FELL', '  ill '], ['rain']], 'event_mentions': [
        {'id': 'a', 'sent_id': 0, 'offset': [0, 2]},
        {'id': 'b', 'sent_id': 1, 'offset': [0, 1]},
        {'id': 'c', 'sent_id': 0, 'offset': [1, 2]}]}


def test_surface_membership_is_ordered_and_train_positive_has_priority():
    m = module()
    row = document()
    features = {'d': {'id': 'd', 'mention_ids': ['b', 'a', 'c']}}
    # b->a positive; a->b NONE; c->a also positive, distinct ordered surface pair.
    index = m.training_index({'d': row}, features, {'d': {'target': [1, 0, 0, 0, 0, 2]}})
    assert index[('rain', 'fell ill')] is True
    assert index[('fell ill', 'rain')] is False
    strata = m.strata(row, ['a', 'b', 'c'], index)
    assert strata[0] == 'train-NONE-only-seen/cross-sentence'
    assert strata[2] == 'train-positive-seen/cross-sentence'
    assert strata[4] == 'train-positive-seen/same-sentence'
    row['causal_relations'] = {'CAUSE': [['a', 'b']]}
    assert m.strata(row, ['a', 'b', 'c'], index) == strata
    assert m.strata(row, ['a', 'b', 'c'], {}) == [
        'unseen/cross-sentence', 'unseen/same-sentence', 'unseen/cross-sentence',
        'unseen/cross-sentence', 'unseen/same-sentence', 'unseen/cross-sentence']


def test_positive_coverage_survives_later_none_example():
    m = module()
    first, second = document(), document()
    second['id'] = 'e'
    feats = {k: {'mention_ids': ['a', 'b', 'c']} for k in ('d', 'e')}
    index = m.training_index({'d': first, 'e': second}, feats,
                             {'d': {'target': [2, 0, 0, 0, 0, 0]},
                              'e': {'target': [0, 0, 0, 0, 0, 0]}})
    assert index[('fell ill', 'rain')] is True


@pytest.mark.parametrize('change', ['offset', 'duplicate', 'missing'])
def test_invalid_mentions_fail_instead_of_silently_changing_population(change):
    m = module()
    row = document()
    if change == 'offset':
        row['event_mentions'][0]['offset'] = [0, 99]
    elif change == 'duplicate':
        row['event_mentions'].append(row['event_mentions'][0])
    else:
        row['event_mentions'].pop()
    with pytest.raises(ValueError):
        m.strata(row, ['a', 'b', 'c'], {})


def test_subtype_swap_counts_as_fp_and_fn_and_cells_conserve_population():
    m = module()
    report = m.count_cells(['unseen/same-sentence']*3, [0, 1, 2],
                           {'full': [1, 2, 2], 'joint': [0, 1, 0]})
    cell = report['unseen/same-sentence']
    assert cell['full']['confusion'] == [[0, 1, 0], [0, 0, 1], [0, 0, 1]]
    assert cell['full']['metrics']['true_positive'] == 1
    assert cell['full']['metrics']['false_positive'] == 2
    assert cell['full']['metrics']['false_negative'] == 1
    assert cell['joint']['metrics']['causal_f1'] == pytest.approx(200/3)
    assert sum(sum(map(sum, c['full']['confusion'])) for c in report.values()) == 3
    with pytest.raises(ValueError):
        m.count_cells(['unseen/same-sentence'], [0, 1], {'full': [0, 1]})
    with pytest.raises(ValueError):
        m.count_cells(['unseen/same-sentence'], [0], {'full': [3]})
