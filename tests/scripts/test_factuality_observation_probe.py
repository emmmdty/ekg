"""Prevent gold-feature and vocabulary leakage in the CPU observation probe."""

import copy
import importlib.util
import json
from pathlib import Path

import joblib
import pytest

ROOT = Path(__file__).resolve().parents[2]


def script():
    spec = importlib.util.spec_from_file_location(
        "probe_factuality_observations", ROOT / "scripts/probe_factuality_observations.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def config():
    return json.loads((ROOT / 'configs/c5_factuality_observation_probe_20261012.json').read_text())


def test_marked_text_does_not_read_gold_annotations():
    record = {"tokens": [["they", "might", "attack", "later"]], "events": ["gold"]}
    mention = {"sent_id": 0, "offset": [2, 3], "factuality": "PS+", "evidence_word": "might"}
    assert script().marked_text(record, mention) == "they might * attack * later"
    changed = copy.deepcopy(mention)
    changed.update(factuality="CT-", evidence_word="gold alternative", id="other gold identity")
    assert script().marked_text(record, changed) == script().marked_text(record, mention)


def test_bad_offsets_are_rejected():
    with pytest.raises(ValueError, match="offset"):
        script().marked_text({"tokens": [["attack"]]}, {"sent_id": 0, "offset": [0, 2]})


def test_config_rejects_seed_and_role_drift():
    for change in ({"seed": 42}, {"diagnostic_only": False}, {"final_valid_accessed": True}):
        c = config()
        c.update(change)
        with pytest.raises(ValueError):
            script().validate_config(c)


def test_document_crossfit_keeps_vocabulary_and_targets_separate(tmp_path):
    module = script()
    c = config()
    examples = []
    for doc in range(10):
        for i, label in enumerate(module.LABELS):
            examples.append({"doc_id": f"d{doc}", "mention_id": f"d{doc}::m{i}",
                             "text": f"classword{i} * trigger * unique_doc_{doc}", "label": label})
    output = tmp_path / 'probe'
    summary = module.crossfit(examples, c, output)
    assert summary['mentions'] == 50
    assert summary['diagnostic_only'] is True
    rows = [json.loads(line) for line in (output / 'probabilities.jsonl').read_text().splitlines()]
    assert len({r['mention_id'] for r in rows}) == 50
    for fold in summary['folds']:
        assert not set(fold['train_doc_ids']) & set(fold['evaluation_doc_ids'])
        model = joblib.load(output / f"fold-{fold['fold']}" / 'model.joblib')
        for doc_id in fold['evaluation_doc_ids']:
            assert f'unique_doc_{doc_id[1:]}' not in model['vectorizer'].vocabulary_
    for row in rows:
        assert len(row['probabilities']) == len(module.LABELS)
        assert sum(row['probabilities']) == pytest.approx(1.0)
        assert 'gold' not in row
    with pytest.raises(FileExistsError):
        module.crossfit(examples, c, output)


def test_missing_training_class_stops_without_majority_fallback(tmp_path):
    with pytest.raises(ValueError, match="classes"):
        script().crossfit([{"doc_id": f"d{i}", "mention_id": f"d{i}::m", "text": 'attack',
                           "label": 'CT+'} for i in range(10)], config(), tmp_path / 'bad')
