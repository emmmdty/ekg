"""A finite CE run must not compare an unverified or failed training result."""
import os
import subprocess
from pathlib import Path

import pytest

PIPELINE = Path('scripts/run_ergo_ce_pipeline_20261026.sh').resolve()


@pytest.fixture
def sandbox(tmp_path):
    (tmp_path/'.venv/bin').mkdir(parents=True)
    python = tmp_path/'.venv/bin/python'
    python.write_text('''#!/usr/bin/env python3
import os, sys
from pathlib import Path
stage = sys.argv[sys.argv.index('--operation')+1] if '--operation' in sys.argv else 'compare'
if stage == os.environ.get('CE_TEST_FAILURE'):
    sys.exit(31)
Path(stage+'.marker').write_text(os.environ['CUDA_VISIBLE_DEVICES'])
''')
    python.chmod(0o755)
    env_file = tmp_path/'bash_env'
    env_file.write_text('cd() { builtin cd "$CE_TEST_ROOT"; }\n')
    return tmp_path, {**os.environ, 'BASH_ENV': str(env_file), 'CE_TEST_ROOT': str(tmp_path)}


def execute(env):
    assert PIPELINE.exists(), 'finite CE pipeline is missing'
    return subprocess.run(['bash', str(PIPELINE)], env=env, capture_output=True, text=True)


def test_success_completes_verification_then_cpu_comparison(sandbox):
    root, env = sandbox
    result = execute(env)
    assert result.returncode == 0, result.stderr
    assert (root/'train.marker').read_text() == '1'
    assert (root/'verify.marker').read_text() == '1'
    assert (root/'compare.marker').read_text() == '-1'
    assert (root/'logs/ergo-ce-pipeline-20261026.exit').read_text().strip() == '0'


@pytest.mark.parametrize('failed_stage', ['train', 'verify'])
def test_failure_preserves_exit_and_prevents_unverified_comparison(sandbox, failed_stage):
    root, env = sandbox
    result = execute({**env, 'CE_TEST_FAILURE': failed_stage})
    assert result.returncode == 31
    assert not (root/'compare.marker').exists()
    if failed_stage == 'train':
        assert not (root/'verify.marker').exists()
    assert (root/'logs/ergo-ce-pipeline-20261026.exit').read_text().strip() == '31'


def test_existing_log_is_preserved_and_no_second_run_starts(sandbox):
    root, env = sandbox
    (root/'logs').mkdir()
    log = root/'logs/ergo-ce-training-20261026.log'
    log.write_text('sealed prior log')
    result = execute(env)
    assert result.returncode != 0
    assert log.read_text() == 'sealed prior log'
    assert not (root/'train.marker').exists()
