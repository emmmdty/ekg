"""Protect distinct-context eligibility and native/coref denominators."""
import importlib.util
from pathlib import Path

import pytest

PATH = Path(__file__).parents[2]/'scripts/audit_a4_matched_contexts.py'


def load():
    assert PATH.exists(), 'matched-context train audit is missing'
    spec = importlib.util.spec_from_file_location('matched_contexts', PATH)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def row(key, words, cause):
    return {'id': key, 'tokens': [words], 'events': [
        {'id': 'a', 'mention': [{'id': 'h', 'sent_id': 0, 'offset': [0, 1]}]},
        {'id': 'b', 'mention': [{'id': 't', 'sent_id': 0, 'offset': [1, 2]}]}],
        'causal_relations': {'CAUSE': [['a', 'b']] if cause else [], 'PRECONDITION': []}}


def test_cross_document_mixed_signal_and_coref_duplicates_count_separately():
    p = row('p', ['hit', 'hurt', 'today'], True)
    p['tokens'] = [['hit', 'hit', 'hit', 'hurt', 'today']]
    p['events'][0]['mention'] = [
        {'id': str(i), 'sent_id': 0, 'offset': [i, i+1]} for i in range(3)]
    p['events'][1]['mention'][0]['offset'] = [3, 4]
    r = load().audit({'p': p, 'n': row('n', ['hit', 'hurt', 'yesterday'], False)})
    assert r['native_class_counts'] == [11, 0, 3]
    assert r['induced_event_pair_class_counts'] == [4, 0, 1]
    assert r['eligible_surface_groups'] == 1
    assert r['eligible_native_class_counts'] == [1, 0, 3]
    assert r['eligible_event_pair_class_counts'] == [1, 0, 1]
    assert r['eligible_documents'] == 2


def test_distinct_ids_with_identical_text_are_not_context_contrasts():
    r = load().audit({'p': row('p', ['hit', 'hurt'], True),
                      'n': row('n', ['hit', 'hurt'], False)})
    assert r['eligible_surface_groups'] == 0
    assert r['identical_input_conflicting_signatures'] == 1
    assert r['eligible_native_class_counts'] == [0, 0, 0]


def test_same_document_label_variation_does_not_create_cross_document_signal():
    p = row('p', ['hit', 'hurt', 'hit'], True)
    p['events'].append({'id': 'c', 'mention': [
        {'id': 'other', 'sent_id': 0, 'offset': [2, 3]}]})
    r = load().audit({'p': p})
    assert r['eligible_surface_groups'] == 0
    assert r['native_class_counts'] == [5, 0, 1]


def test_subtype_conflict_is_not_causal_vs_none_support():
    p, q = row('p', ['hit', 'hurt', 'today'], True), row('q', ['hit', 'hurt'], True)
    q['causal_relations'] = {'CAUSE': [], 'PRECONDITION': [['a', 'b']]}
    r = load().audit({'p': p, 'q': q})
    assert r['eligible_surface_groups'] == 0
    assert r['positive_subtype_conflicting_surface_groups'] == 1


def test_duplicate_mentions_fail_instead_of_inflating_supervision():
    p = row('p', ['hit', 'hurt'], True)
    p['events'][1]['mention'][0]['id'] = 'h'
    with pytest.raises(ValueError):
        load().audit({'p': p})
