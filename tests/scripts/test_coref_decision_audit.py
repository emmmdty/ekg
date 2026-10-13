"""Catch confounding first mentions, false nulls, and wrong antecedent ranking."""

import importlib.util
from pathlib import Path

import pytest


def module():
    path = Path(__file__).resolve().parents[2] / 'scripts/report_coref_decision_audit.py'
    assert path.exists(), 'decision audit entrypoint missing'
    spec = importlib.util.spec_from_file_location('decision_audit', path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def fixture():
    # a,b,d,e belong together; c is another event. Fixed logits imply:
    # b: false null, right real rank; c: first-mention false link;
    # d: false null, wrong real rank; e: wrong non-null antecedent.
    gold = {'id': 'd', 'events': [
        {'id': 'x', 'type': 'T', 'mention': [{'id': x} for x in ['a', 'b', 'd', 'e']]},
        {'id': 'y', 'type': 'T', 'mention': [{'id': 'c'}]}]}
    cache = {'id': 'd', 'mentions': ['a', 'b', 'c', 'd', 'e'],
             'pair_logits': [[], [-1], [2, 1], [-3, -2, -1], [1, 2, 3, 0]]}
    types = {x: 'T' for x in cache['mentions']}
    return gold, cache, types


def test_classifies_null_errors_separately_from_wrong_antecedents():
    result = module().analyze_document(*fixture())
    assert [row['category'] for row in result['decisions']] == [
        'correct_dummy', 'false_dummy_rank_correct', 'false_first_link',
        'false_dummy_rank_wrong', 'wrong_antecedent']
    assert result['clusters']['baseline'] == [['a', 'c', 'e']]
    assert result['clusters']['null_only'] == [['a', 'b'], ['c', 'e']]
    assert result['clusters']['requires_ranking'] == [['a', 'c'], ['b', 'd', 'e']]
    assert result['clusters']['all'] == [['a', 'b', 'd', 'e']]


def test_type_policy_comes_from_task_input_and_preserves_dummy():
    gold, cache, types = fixture()
    types['c'] = 'U'
    gold['events'][1]['type'] = 'U'
    result = module().analyze_document(gold, cache, types)
    assert result['decisions'][2]['category'] == 'correct_dummy'
    assert result['decisions'][3]['category'] == 'false_dummy_rank_correct'
    assert result['decisions'][4]['category'] == 'correct_link'
    assert result['clusters']['baseline'] == [['b', 'e']]


def test_first_mention_is_not_equivalent_to_singleton():
    gold, cache, types = fixture()
    result = module().analyze_document(gold, cache, types)
    assert result['decisions'][0]['gold_has_predecessor'] is False
    assert result['decisions'][0]['gold_cluster_size'] == 4


@pytest.mark.parametrize('breakage', ['unknown', 'duplicate', 'shape', 'nonfinite', 'type'])
def test_invalid_population_or_score_fails(breakage):
    gold, cache, types = fixture()
    if breakage == 'unknown':
        cache['mentions'][-1] = 'unknown'
    elif breakage == 'duplicate':
        gold['events'][1]['mention'].append({'id': 'a'})
    elif breakage == 'shape':
        cache['pair_logits'][3] = []
    elif breakage == 'nonfinite':
        cache['pair_logits'][1][0] = float('nan')
    else:
        types['b'] = 'other'
    with pytest.raises(ValueError):
        module().analyze_document(gold, cache, types)
