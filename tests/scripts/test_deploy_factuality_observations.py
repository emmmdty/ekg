"""Deploy frozen train observers without fitting or consuming factuality gold."""

import importlib.util
from pathlib import Path

import numpy as np
import pytest

from ekg.relations.data.maven_fact import FACTUALITY_LABELS as LABELS


def script():
    path = Path(__file__).resolve().parents[2] / 'scripts/deploy_factuality_observations.py'
    spec = importlib.util.spec_from_file_location('deploy_factuality_observations', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def record():
    return {'id': 'heldout', 'tokens': [['They', 'will', 'arrive']],
            'event_mentions': [{'id': 'm', 'sent_id': 0, 'offset': [2, 3]}]}


def ledger():
    return {'diagnostic_only': True, 'seed': 13, 'final_valid_accessed': False,
            'consumer_evaluation_labels_accessed': False,
            'folds': [{'train_doc_ids': ['train'], 'evaluation_doc_ids': ['train_oof']}]}


def test_consumer_document_cannot_appear_in_any_upstream_partition():
    module = script()
    module.validate_scope(ledger(), [record()], {'heldout'})
    for partition in ('train_doc_ids', 'evaluation_doc_ids'):
        summary = ledger()
        summary['folds'][0][partition] = ['heldout']
        with pytest.raises(ValueError, match='consumer'):
            module.validate_scope(summary, [record()], {'heldout'})


@pytest.mark.parametrize('location', ['document', 'mention'])
def test_gold_factuality_is_rejected_before_predict(location):
    row = record()
    if location == 'document':
        row['events'] = []
    else:
        row['event_mentions'][0]['factuality'] = 'CT+'
    with pytest.raises(ValueError, match='unlabeled'):
        script().validate_scope(ledger(), [row], {'heldout'})


def test_manifest_coverage_must_be_exact():
    with pytest.raises(ValueError, match='coverage'):
        script().validate_scope(ledger(), [record()], {'another'})


class Vectorizer:
    def transform(self, texts):
        assert texts == ['They will * arrive *']
        return texts


class Classifier:
    def __init__(self, classes, values):
        self.classes_ = np.array(classes)
        self.values = values

    def predict_proba(self, features):
        return np.array([self.values])


def test_equal_mean_respects_each_model_class_order_without_fit():
    first = {'vectorizer': Vectorizer(), 'classifier': Classifier(LABELS, [1, 0, 0, 0, 0])}
    second = {'vectorizer': Vectorizer(),
              'classifier': Classifier(list(reversed(LABELS)), [1, 0, 0, 0, 0])}
    rows = script().predict_documents([record()], [first, second])
    assert rows[0]['mention_id'] == 'heldout::m'
    assert rows[0]['probabilities'] == [0.5, 0, 0, 0, 0.5]
    assert rows[0]['label'] == LABELS[0]


def test_invalid_model_probabilities_fail_without_repair():
    model = {'vectorizer': Vectorizer(), 'classifier': Classifier(LABELS, [1, 1, 0, 0, 0])}
    with pytest.raises(ValueError, match='probabilities'):
        script().predict_documents([record()], [model])
