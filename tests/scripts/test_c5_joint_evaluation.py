"""C41 evaluation waits for every valid endpoint and resamples document counts."""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest


def script():
    path = Path(__file__).resolve().parents[2] / 'scripts/evaluate_c5_joint_dependence.py'
    assert path.exists(), 'C41 evaluation collector missing'
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location('c5_joint_evaluation', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_incomplete_endpoint_prevents_evaluation(tmp_path):
    module = script()
    root = tmp_path / 'arm'
    root.mkdir()
    (root / 'status.json').write_text(json.dumps({'status': 'running'}))
    with pytest.raises(ValueError, match='endpoint'):
        module.endpoint(root, 'expected')
    assert not (tmp_path / 'evaluation').exists()


def test_endpoint_rejects_tampered_prediction(tmp_path):
    module = script()
    from ekg.core.stage_bundle import sha256_file

    pred = tmp_path / 'predictions.jsonl'
    pred.write_text('{"id":"original"}\n')
    report = tmp_path / 'report.json'
    report.write_text(json.dumps({'status': 'complete', 'epochs': 100,
        'optimizer_steps': 8200, 'microbatches': 32800, 'config_sha256': 'cfg',
        'cpu_cache_replay_and_source_decoder_parity': True, 'final_valid_accessed': False}))
    (tmp_path / 'status.json').write_text(json.dumps({'status': 'complete',
        'config_sha256': 'cfg', 'artifact_sha256': {'predictions.jsonl': sha256_file(pred),
                                                'report.json': sha256_file(report)}}))
    pred.write_text('{"id":"changed"}\n')
    with pytest.raises(ValueError, match='hash'):
        module.endpoint(tmp_path, 'cfg')


def test_paired_bootstrap_identical_system_has_exact_zero_difference():
    module = script()
    counts = np.array([[3, 4, 3, 5], [1, 2, 1, 2], [0, 0, 0, 0]], dtype=float)
    result = module.paired_comparison(counts, counts)
    assert result['muc_difference_points'] == 0.
    assert result['interval_95_points'] == [0., 0.]


def test_corpus_muc_aggregates_links_before_computing_document_difference():
    module = script()
    # Left P=R=1/2 -> F1=50; right P=R=1/4 -> F1=25.
    left = np.array([[1, 1, 1, 1], [0, 1, 0, 1]], dtype=float)
    right = np.array([[0, 1, 0, 1], [1, 3, 1, 3]], dtype=float)
    result = module.paired_comparison(left, right)
    assert result['muc_difference_points'] == pytest.approx(25.)
