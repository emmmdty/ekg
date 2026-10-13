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


def test_continuous_geometry_separates_error_and_correct_links_without_argmax_veto():
    gold, cache, _ = fixture()
    for event in gold['events']:
        for mention in event['mention']:
            mention['type'] = 'event'
    q = {'d::a': [1, 0, 0, 0, 0], 'd::b': [1, 0, 0, 0, 0],
         'd::c': [0.6, 0.4, 0, 0, 0]}
    result = module().geometry_profile(gold, cache, q)
    assert result['all']['true_mean_distance'] == 0
    assert result['all']['false_mean_distance'] == pytest.approx(0.16)
    assert result['same_type'] == result['all']


def test_cross_type_false_link_does_not_enter_same_type_geometry():
    gold, cache, _ = fixture()
    for event in gold['events']:
        for mention in event['mention']:
            mention['type'] = 'event' if mention['id'] != 'c' else 'other'
    q = {f'd::{key}': [1, 0, 0, 0, 0] for key in ['a', 'b', 'c']}
    result = module().geometry_profile(gold, cache, q)
    assert result['all']['false_links'] == 1
    assert result['same_type']['false_links'] == 0
    assert result['same_type']['false_mean_distance'] is None


def test_document_geometry_summary_weights_documents_equally():
    rows = [{'all': {'false_mean_distance': 0.5, 'true_mean_distance': 0.1}},
            {'all': {'false_mean_distance': 0.3, 'true_mean_distance': 0.1}},
            {'all': {'false_mean_distance': None, 'true_mean_distance': 0.1}}]
    result = module().geometry_summary(rows, 'all')
    assert result['paired_documents'] == 2
    assert result['mean_false_minus_true'] == pytest.approx(0.3)
    assert result['bootstrap95'][0] > 0


def test_official_event_type_is_explicitly_projected_to_mentions():
    gold, cache, _ = fixture()
    gold['events'][0]['type'] = 'event'
    gold['events'][1]['type'] = 'other'
    typed = module().typed_gold_view(gold)
    assert 'type' not in gold['events'][0]['mention'][0]
    assert typed['events'][0]['mention'][0]['type'] == 'event'
    q = {f'd::{key}': [1, 0, 0, 0, 0] for key in ['a', 'b', 'c']}
    result = module().geometry_profile(typed, cache, q)
    assert result['all']['false_links'] == 1
    assert result['same_type']['false_links'] == 0
