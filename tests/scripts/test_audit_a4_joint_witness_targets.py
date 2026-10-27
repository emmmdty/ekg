"""Protect witness orientation, label conditioning and native mention coverage."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest

PATH = Path(__file__).parents[2] / 'scripts/audit_a4_joint_witness_targets.py'


def load():
    assert PATH.exists(), 'joint witness target census is missing'
    spec = importlib.util.spec_from_file_location('joint_witness_targets', PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_native_chain_and_reverse_leg_order_remain_distinct():
    matrix = np.array([[-1, 1, 0], [0, -1, 2], [0, 0, -1]])
    r = load().count_triples(matrix)
    assert r['chain'].sum() == 6
    assert r['chain'][1, 2, 0] == 1
    assert r['reverse_chain'][2, 1, 0] == 1
    assert r['chain'].sum(axis=(0, 1)).tolist() == [4, 1, 1]
    assert r['fork'][1:, 1:, :].sum() == 0
    assert r['collider'][1:, 1:, :].sum() == 0


def test_two_mentions_keep_native_pair_labels_without_fabricating_witness():
    matrix = np.array([[-1, 2], [0, -1]])
    assert all(x.sum() == 0 for x in load().count_triples(matrix).values())


@pytest.mark.parametrize('matrix', [
    np.array([[0, 1], [0, -1]]),
    np.array([[-1, 3], [0, -1]]),
    np.zeros((2, 3), dtype=int),
])
def test_invalid_diagonal_or_native_label_population_fails(matrix):
    with pytest.raises(ValueError):
        load().count_triples(matrix)


def test_coref_duplicates_are_retained_and_reported_as_separate_population():
    events = [
        {'id': 'a', 'mention': [{'id': 'a0'}, {'id': 'a1'}]},
        {'id': 'b', 'mention': [{'id': 'b0'}]},
        {'id': 'c', 'mention': [{'id': 'c0'}]},
    ]
    raw = {'d': {'id': 'd', 'events': events,
                 'causal_relations': {'PRECONDITION': [['a', 'b']], 'CAUSE': [['b', 'c']]}}}
    features = {'d': {'id': 'd', 'mention_ids': ['a0', 'a1', 'b0', 'c0']}}
    targets = {'d': {'id': 'd', 'target': [0, 1, 0, 0, 1, 0, 0, 0, 2, 0, 0, 0]}}
    r = load().audit(raw, features, targets)
    assert r['native_class_counts'] == [9, 2, 1]
    assert r['mention_triples'] == 24
    assert r['distinct_event_triples'] == 6
    assert r['mention_triples_with_three_distinct_events'] == 12
    assert np.array(r['native']['chain']).sum(axis=(0, 1)).tolist() == [18, 4, 2]


def test_missing_feature_document_cannot_silently_drop_a_document():
    with pytest.raises(ValueError):
        load().audit({'d': {}}, {}, {})
