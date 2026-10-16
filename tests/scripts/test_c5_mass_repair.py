"""Repair admission rejects missing evidence before model loading or updates."""
import importlib.util
import json
import sys
from pathlib import Path

import pytest


def script():
    path = Path(__file__).resolve().parents[2] / 'scripts/run_c5_mass_repair.py'
    assert path.exists(), 'mass repair entrypoint missing'
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location('c5_mass_repair', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_repair_training_requires_completed_parity_and_smoke(tmp_path):
    module = script()
    config = {'output': str(tmp_path), 'admission': str(tmp_path / 'admission.json')}
    with pytest.raises((ValueError, FileNotFoundError)):
        module.require_repair_admission(config, 'config-hash')
    assert not (tmp_path / 'train').exists()


def test_repair_admission_rejects_tampered_production_artifact(tmp_path):
    module = script()
    from ekg.core.stage_bundle import sha256_file

    evidence = tmp_path / 'smoke.json'
    evidence.write_text('{"status":"complete"}')
    admission = tmp_path / 'admission.json'
    admission.write_text(json.dumps({'method_admitted': True, 'config_sha256': 'cfg',
        'evidence_sha256': {str(evidence): sha256_file(evidence)}}))
    evidence.write_text('{"status":"failed"}')
    with pytest.raises(ValueError, match='evidence'):
        module.require_repair_admission({'output': str(tmp_path),
                                        'admission': str(admission)}, 'cfg')


def test_parity_comparison_checks_each_parameter_not_only_loss():
    module = script()
    torch = pytest.importorskip('torch')
    parameter = torch.nn.Parameter(torch.tensor([1.]))
    model = torch.nn.ParameterList([parameter])
    report = module.compare_objectives(model, lambda: parameter.square().sum(),
        lambda: parameter.square().sum() + (parameter - parameter.detach()).sum(), torch)
    assert report['loss_close']
    assert not report['gradient_parity']['passed']
    assert parameter.item() == 1.
