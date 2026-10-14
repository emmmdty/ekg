"""An explicitly authorized target must not relax the sealed 4090 entrypoint."""
import importlib.util
import sys
from pathlib import Path

import pytest


def script():
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / 'scripts'))
    path = root / 'scripts/profile_joint_cost_target.py'
    assert path.exists(), 'authorized target adapter missing'
    spec = importlib.util.spec_from_file_location('joint_cost_target', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def settings():
    return {'authorization': 'C41-5090-20261014', 'seed': 13, 'method_admitted': False,
            'optimizer_steps': 0, 'final_valid_accessed': False}


def test_authorized_cpu_and_single_cuda_target():
    module = script()
    module.validate_target(settings(), 'cpu', '-1', False, '/mnt/aidata/tongjiakai/ekg')
    module.validate_target(settings(), 'cuda', '0', True, '/mnt/aidata/tongjiakai/ekg')


@pytest.mark.parametrize('device,visible,available,cwd', [
    ('cuda', '0', True, '/data/TJK/ekg'), ('cuda', '0,1', True, '/mnt/aidata/tongjiakai/ekg'),
    ('cuda', '0', False, '/mnt/aidata/tongjiakai/ekg'),
    ('cpu', '0', True, '/mnt/aidata/tongjiakai/ekg'), ('cpu', '-1', False, '/local')])
def test_wrong_machine_or_device_is_rejected(device, visible, available, cwd):
    with pytest.raises(ValueError):
        script().validate_target(settings(), device, visible, available, cwd)


@pytest.mark.parametrize('key,value', [('authorization', 'decoder-only'), ('seed', 42),
                                      ('method_admitted', True), ('optimizer_steps', 1),
                                      ('final_valid_accessed', True)])
def test_scope_drift_is_rejected(key, value):
    config = settings()
    config[key] = value
    with pytest.raises(ValueError):
        script().validate_target(config, 'cpu', '-1', False, '/mnt/aidata/tongjiakai/ekg')


def test_gpu_requires_same_config_cpu_completion():
    module = script()
    good = {'status': 'complete', 'config_sha256': 'abc', 'device': 'cpu'}
    module.require_cpu_report(good, 'abc')
    for bad in [{**good, 'status': 'failed'}, {**good, 'config_sha256': 'def'},
                {**good, 'device': 'cuda'}]:
        with pytest.raises(ValueError):
            module.require_cpu_report(bad, 'abc')
