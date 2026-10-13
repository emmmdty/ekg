"""Keep selected antecedent errors distinct from posterior candidates and MUC."""

import importlib.util
from pathlib import Path

import pytest


def module():
    path = Path(__file__).resolve().parents[2] / 'scripts/report_coref_observation_overlap.py'
    spec = importlib.util.spec_from_file_location('coref_observation_overlap', path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def fixture():
    gold = {'id': 'd', 'events': [
        {'id': 'e', 'mention': [{'id': 'a'}, {'id': 'b'}]},
        {'id': 'f', 'mention': [{'id': 'c'}]}]}
    cache = {'id': 'd', 'mentions': ['a', 'b', 'c'],
             'probabilities': [[1], [0.8, 0.2], [0.2, 0.7, 0.1]]}
    q = {f'd::{key}': label for key, label in [('a', 'CT+'), ('b', 'CT+'), ('c', 'PS+')]}
    return gold, cache, q


def test_only_selected_links_count_as_anchor_errors():
    report = module().profile(*fixture())
    assert report['selected_links'] == 2
    assert report['selected_false_links'] == 1
    assert report['different_observation_false_links'] == 1
    assert report['different_observation_true_links'] == 0
    assert report['all_candidates_different_observation'] == 2


def test_dummy_is_never_a_false_merge_link():
    gold, cache, q = fixture()
    cache['probabilities'][2] = [0.1, 0.2, 0.7]
    report = module().profile(gold, cache, q)
    assert report['selected_links'] == 1
    assert report['selected_false_links'] == 0
    assert report['dummy_selections'] == 2


def test_incomplete_observer_or_gold_population_fails():
    gold, cache, q = fixture()
    q.pop('d::c')
    with pytest.raises(ValueError, match='coverage'):
        module().profile(gold, cache, q)
    gold['events'][1]['mention'][0]['id'] = 'another'
    with pytest.raises(ValueError, match='coverage'):
        module().profile(gold, cache, fixture()[2])


def test_no_difference_keeps_errors_visible():
    gold, cache, q = fixture()
    q['d::c'] = 'CT+'
    report = module().profile(gold, cache, q)
    assert report['selected_false_links'] == 1
    assert report['different_observation_false_links'] == 0
