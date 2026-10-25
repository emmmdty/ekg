"""Train-fit diagnostics must keep native errors and labels outside inference."""
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pytest


def script(monkeypatch):
    monkeypatch.syspath_prepend(str(Path('scripts').resolve()))
    spec = importlib.util.spec_from_file_location(
        'diagnose_ergo_native_fit', Path('scripts/diagnose_ergo_native_fit.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_positive_subtype_swaps_are_both_false_positive_and_false_negative(monkeypatch):
    m = script(monkeypatch)
    c = m.confusion_for_labels([1, 2, 0], [2, 1, 0])
    result = m.causal_metrics(c)
    assert result['true_positive'] == 0
    assert result['false_positive'] == result['false_negative'] == 2
    assert result['causal_f1'] == 0  # binary positive/negative F1 would be 100


@pytest.mark.parametrize('target,pred', [([0], [1, 2]), ([True], [0]), ([1], [3]), ([1.], [1])])
def test_invalid_or_partial_native_classes_fail(monkeypatch, target, pred):
    with pytest.raises(ValueError, match='native classes'):
        script(monkeypatch).confusion_for_labels(target, pred)


def test_native_counts_match_real_official_scorer_and_cartesian_gold(monkeypatch):
    m = script(monkeypatch)
    from score_maven_ere_official import _load_evaluator

    from ekg.relations.ergo_adapter import export_causal_classes

    mentions = [{'id': x, 'sent_id': 0, 'offset': [i, i+1]} for i, x in enumerate('abc')]
    gold = {'id': 'd', 'events': [
        {'id': 'e1', 'mention': mentions[:2]}, {'id': 'e2', 'mention': mentions[2:]},
    ], 'causal_relations': {'CAUSE': [['e1', 'e2']], 'PRECONDITION': []}}
    raw = {'id': 'd', 'tokens': [['A', 'B', 'C']], 'TIMEX': [], 'event_mentions': mentions}
    target = [0, 2, 0, 2, 0, 0]
    predicted = [0, 2, 0, 1, 2, 0]
    evaluator = _load_evaluator(Path('data/protocols/v6/tools/maven_ere_evaluate.py'))
    pred = export_causal_classes(raw, predicted)
    official = evaluator.evaluate({'d': gold}, {'d': pred}, 'causal')
    metrics = m.causal_metrics(m.confusion_for_labels(target, predicted))
    for key in official:
        assert metrics[key] == pytest.approx(official[key])
    assert metrics['causal_f1'] == 40


def test_sealed_manifest_and_missing_replay_proof_cannot_be_admitted(monkeypatch):
    m = script(monkeypatch)
    with pytest.raises(ValueError, match='train manifest'):
        m.require_train_manifest({'split_role': 'final-valid'})
    with pytest.raises(ValueError, match='independent replay'):
        m.require_fit_scope({'diagnostic_admitted': True, 'final_valid_accessed': False,
                             'seed': 13}, {'final_valid_accessed': False}, {})


def test_without_admission_reads_no_source_or_checkpoint(tmp_path):
    cfg = tmp_path / 'config.json'
    cfg.write_text(json.dumps({'diagnostic_admitted': False}))
    result = subprocess.run([sys.executable, 'scripts/diagnose_ergo_native_fit.py',
                             '--config', str(cfg)], capture_output=True, text=True)
    assert result.returncode != 0
    assert 'diagnostic not admitted' in result.stderr


def test_actual_inference_hides_targets_disables_gradients_and_keeps_parameters(monkeypatch):
    torch = pytest.importorskip('torch')
    m = script(monkeypatch)

    class Stub(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.weight = torch.nn.Parameter(torch.ones(1))

        def forward(self, **kwargs):
            assert not self.training and not torch.is_grad_enabled()
            assert kwargs['target'] == [[0, 0]]
            return self.weight.sum(), torch.tensor([[0., 1., 3.], [0., 3., 1.]])

    f = {'id': 'd', 'mention_ids': ['a', 'b'],
         'enc_input_ids': [0, 50265, 8, 50266, 50265, 9, 50266, 2],
         'enc_mask_ids': [1]*8, 'global_attention_mask': [1, 0, 0, 0, 0, 0, 0, 1],
         't1_pos': [1, 4], 't2_pos': [4, 1]}
    model = Stub()
    records = []
    before = model.weight.detach().clone()
    c = m.predict_fit(model, [(f, [1, 2])], torch.device('cpu'),
                      deadline=time.monotonic()+60,
                      on_document=lambda key, pred, conf: records.append((key, pred)))
    assert records == [('d', [2, 1])]
    assert m.causal_metrics(c)['causal_f1'] == 0
    assert torch.equal(model.weight, before) and model.weight.grad is None
    with pytest.raises(TimeoutError, match='wall budget'):
        m.predict_fit(model, [(f, [1, 2])], torch.device('cpu'),
                      deadline=time.monotonic()-1, on_document=lambda *args: None)


def test_confusion_rejects_noninteger_or_negative_counts(monkeypatch):
    m = script(monkeypatch)
    with pytest.raises(ValueError, match='confusion'):
        m.causal_metrics(np.full((3, 3), -1))
    with pytest.raises(ValueError, match='confusion'):
        m.causal_metrics(np.zeros((3, 3), dtype=float))


def test_only_verified_full_checkpoint_and_train_manifest_are_accepted(monkeypatch):
    m = script(monkeypatch)
    cfg = {'diagnostic_admitted': True, 'final_valid_accessed': False, 'seed': 13}
    native = {'seed': 13, 'epochs': 20, 'final_valid_accessed': False}
    proof = {'status': 'complete', 'cached_classes_equal': True,
             'official_scores_equal': True, 'final_valid_accessed': False}
    m.require_fit_scope(cfg, native, proof)
    m.require_train_manifest({'split_role': 'train'})
    with pytest.raises(ValueError, match='full native run'):
        m.require_fit_scope(cfg, native | {'control_name': 'gamma0'}, proof)
    with pytest.raises(ValueError, match='independent replay'):
        m.require_fit_scope(cfg, native, proof | {'final_valid_accessed': True})
    with pytest.raises(ValueError, match='train manifest'):
        m.require_train_manifest({'split_role': 'internal-dev'})
