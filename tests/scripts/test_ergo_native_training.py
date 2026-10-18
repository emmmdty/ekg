import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


def script(monkeypatch):
    monkeypatch.syspath_prepend(str(Path("scripts").resolve()))
    spec = importlib.util.spec_from_file_location(
        "ergo_training_entry", Path("scripts/train_ergo_native.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_training_without_admission_reads_no_data_or_encoder(tmp_path):
    output = tmp_path / 'run'
    config = tmp_path / 'config.json'
    config.write_text(json.dumps({'training_admitted': False, 'budget_admitted': False,
                                  'dev_capacity_admitted': False, 'output': str(output)}))
    result = subprocess.run(
        [sys.executable, 'scripts/train_ergo_native.py', '--config', str(config)],
        capture_output=True, text=True)
    assert result.returncode != 0
    assert 'training not admitted' in result.stderr
    assert not output.exists()


def test_training_loader_rejects_missing_document_and_partial_targets(tmp_path, monkeypatch):
    module = script(monkeypatch)
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps({'doc_ids': ['a', 'b']}))
    features, targets = tmp_path / 'features.jsonl', tmp_path / 'targets.jsonl'
    rows = [{'id': key, 'mention_ids': ['x', 'y'], 't1_pos': [1, 4], 't2_pos': [4, 1]}
            for key in ['b', 'a']]
    features.write_text(''.join(json.dumps(row) + '\n' for row in rows))
    targets.write_text('{"id":"a","target":[0,2]}\n{"id":"b","target":[1,0]}\n')
    data = module.aligned_training_data(features, targets, manifest)
    assert [row[0]['id'] for row in data] == ['a', 'b']
    assert [row[1] for row in data] == [[0, 2], [1, 0]]
    targets.write_text('{"id":"a","target":[0]}\n{"id":"b","target":[1,0]}\n')
    with pytest.raises(ValueError, match='complete'):
        module.aligned_training_data(features, targets, manifest)
    targets.write_text('{"id":"a","target":[0,2]}\n')
    with pytest.raises(ValueError, match='coverage'):
        module.aligned_training_data(features, targets, manifest)


def test_cpu_cost_reports_cannot_admit_cuda_training(tmp_path, monkeypatch):
    reports = []
    for i in range(3):
        path = tmp_path / f'cost-{i}.json'
        path.write_text(json.dumps({'status': 'complete', 'device': 'cpu'}))
        reports.append(str(path))
    cfg = {'cost_reports': reports}
    with pytest.raises(ValueError, match='CUDA'):
        script(monkeypatch).require_production_evidence(cfg)


def test_native_collator_matches_original_seven_field_batch(tmp_path, monkeypatch):
    torch = pytest.importorskip('torch')
    feature = {'id': 'd', 'mention_ids': ['a', 'b'],
               'enc_input_ids': [0, 50265, 8, 50266, 50265, 9, 50266, 2],
               'enc_mask_ids': [1] * 8, 'global_attention_mask': [1, 0, 0, 0, 0, 0, 0, 1],
               't1_pos': [1, 4], 't2_pos': [4, 1]}
    batch = script(monkeypatch).native_train_batch([(feature, [0, 2])])
    assert len(batch) == 7
    assert batch[0].tolist() == [[0, 50265, 8, 50266, 50265, 9, 50266, 2]]
    assert batch[1].tolist() == [[1] * 8]
    assert batch[2].tolist() == [[1, 0, 0, 0, 0, 0, 0, 1]]
    assert batch[3:5] == ([[1, 4]], [[4, 1]])
    assert batch[5].dtype == torch.bool
    assert batch[5].tolist() == [[[True, False], [False, True]]]
    assert batch[6] == [[0, 2]]
    with pytest.raises(ValueError, match='batch1'):
        script(monkeypatch).native_train_batch([(feature, [0, 2])] * 2)


def test_preflight_cannot_use_cost_permission_as_cuda_smoke_admission(tmp_path):
    config = tmp_path / 'preflight.json'
    output = tmp_path / 'output'
    config.write_text(json.dumps({'device': 'cuda', 'cuda_admitted': False, 'output': str(output)}))
    result = subprocess.run(
        [sys.executable, 'scripts/preflight_ergo_native.py', '--config', str(config)],
        capture_output=True, text=True)
    assert result.returncode != 0
    assert 'CUDA preflight not admitted' in result.stderr
    assert not output.exists()
