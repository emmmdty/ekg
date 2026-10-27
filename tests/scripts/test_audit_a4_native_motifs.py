"""Catch invented edges, reversed witnesses and inflated coreference denominators."""
import importlib.util
from pathlib import Path

import pytest

PATH = Path(__file__).parents[2] / 'scripts/audit_a4_native_motifs.py'


def load():
    assert PATH.exists(), 'native motif feasibility audit is missing'
    spec = importlib.util.spec_from_file_location('native_motifs', PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def row(cause=(), precondition=(), duplicate_a=False):
    return {'id': 'doc', 'events': [
        {'id': e, 'mention': [{'id': e + str(i)} for i in
                             range(2 if e == 'a' and duplicate_a else 1)]}
        for e in ['a', 'b', 'c']],
        'causal_relations': {'CAUSE': list(cause), 'PRECONDITION': list(precondition)}}


def test_chain_witness_does_not_invent_direct_relation_or_reverse_orientation():
    r = load().audit({'doc': row([['a', 'b']], [['b', 'c']])})
    assert r['native_class_counts'] == [4, 1, 1]
    assert r['masks']['1']['event_pairs'] == [1, 0, 0]
    assert r['masks']['2']['event_pairs'] == [1, 0, 0]
    assert r['masks']['0']['event_pairs'] == [2, 1, 1]
    assert r['unordered']['either_chain']['event_pairs'] == [1, 0]


@pytest.mark.parametrize(('edges', 'pattern', 'mask'), [
    ([['c', 'a'], ['c', 'b']], 'fork', '4'),
    ([['a', 'c'], ['b', 'c']], 'collider', '8'),
])
def test_common_cause_or_effect_does_not_make_leaf_events_related(edges, pattern, mask):
    r = load().audit({'doc': row(edges)})
    assert r['masks'][mask]['event_pairs'] == [2, 0, 0]
    assert r['unordered'][pattern]['event_pairs'] == [1, 0]


def test_reverse_only_relation_is_positive_in_binary_existence_comparison():
    r = load().audit({'doc': row([['c', 'a'], ['c', 'b'], ['b', 'a']])})
    assert r['masks']['4']['event_pairs'] == [1, 0, 1]
    assert r['unordered']['fork']['event_pairs'] == [0, 1]


def test_coref_expansion_and_self_units_have_separate_denominators():
    r = load().audit({'doc': row([['a', 'b']], [['b', 'c']], duplicate_a=True)})
    assert r['native_class_counts'] == [9, 1, 2]
    assert r['distinct_event_class_counts'] == [4, 1, 1]
    assert r['within_coref_ordered_pairs'] == 2
    assert r['within_coref_event_self_units'] == 1
    assert r['masks']['1']['mention_pairs'] == [2, 0, 0]
    assert r['unordered']['either_chain']['mention_pairs'] == [2, 0]


@pytest.mark.parametrize('bad', ['unknown_endpoint', 'overlapping_label', 'duplicate_event'])
def test_invalid_native_graph_is_rejected(bad):
    data = row([['a', 'b']])
    if bad == 'unknown_endpoint':
        data['causal_relations']['CAUSE'].append(['x', 'b'])
    elif bad == 'overlapping_label':
        data['causal_relations']['PRECONDITION'].append(['a', 'b'])
    else:
        data['events'].append(data['events'][0])
    with pytest.raises(ValueError):
        load().audit({'doc': data})
