import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


def script(monkeypatch):
    monkeypatch.syspath_prepend(str(Path('scripts').resolve()))
    spec = importlib.util.spec_from_file_location(
        'ergo_checkpoint_verify', Path('scripts/verify_ergo_native_checkpoint.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_incomplete_run_rejects_before_checkpoint_config_or_model_reads(tmp_path, monkeypatch):
    report = tmp_path / 'report.json'
    report.write_text(json.dumps({'status': 'running', 'epochs_completed': 1}))
    with pytest.raises(ValueError, match='complete native run'):
        script(monkeypatch).load_completed_native_run(tmp_path / 'missing.json', report)


def test_completed_run_binds_checkpoint_bytes_and_config_identity(tmp_path, monkeypatch):
    cfg = tmp_path / 'config.json'
    cfg.write_text(json.dumps({'schema_version': 'ekg.ergo_native_training.v2', 'seed': 13,
                              'epochs': 20, 'final_valid_accessed': False,
                              'training_admitted': True, 'budget_admitted': True,
                              'dev_capacity_admitted': True}))
    checkpoint = tmp_path / 'best.pt'
    checkpoint.write_bytes(b'metadata fixture; not real weights')
    report = tmp_path / 'report.json'
    report.write_text(json.dumps({'status': 'complete', 'epochs_completed': 20, 'seed': 13,
                                 'final_valid_accessed': False, 'best_epoch': 2,
                                 'config_sha256': hashlib.sha256(cfg.read_bytes()).hexdigest(),
                                 'checkpoint': str(checkpoint),
                                 'checkpoint_sha256': hashlib.sha256(
                                     checkpoint.read_bytes()).hexdigest()}))
    _, _, path = script(monkeypatch).load_completed_native_run(cfg, report)
    assert path == checkpoint
    checkpoint.write_bytes(checkpoint.read_bytes()+b'changed')
    with pytest.raises(ValueError, match='checkpoint identity'):
        script(monkeypatch).load_completed_native_run(cfg, report)


def test_checkpoint_replay_requires_every_doc_and_exact_three_class_labels(monkeypatch):
    checker = script(monkeypatch).require_cached_class_parity
    checker({'d': [0, 2]}, {'d': [0, 2]}, ['d'])
    with pytest.raises(ValueError, match='class mismatch'):
        checker({'d': [0, 2]}, {'d': [0, 1]}, ['d'])
    with pytest.raises(ValueError, match='coverage'):
        checker({'d': [0, 2]}, {}, ['d'])
