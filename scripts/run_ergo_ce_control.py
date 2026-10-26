"""Select the author's built-in CE via the unchanged, pinned known-control runner.

The runner's execution/CPU/CUDA/initializer/scoring gates remain intact. Its file
identity binds this extension, while config pins separately bind the original
runner used as a library. No original entrypoint or source file is edited.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from ekg.core.stage_bundle import sha256_file

HELPER = Path('scripts/run_ergo_native_control.py')


def install_ce(model, control):
    if (control != 'unweighted_ce' or model.loss_type != 'focal'
            or model.focal_loss.gamma != 2
            or model.focal_loss.alpha.tolist() != [.25, .75, .75]):
        raise ValueError('one original unweighted CE control required')
    model.loss_type = 'ce'
    return {'name': control, 'mask_calls': 0, 'selected_original_loss': 'ce_loss',
            'graph_unchanged': True, 'focal_object_unchanged': True}


def control_runner(cfg):
    if str(HELPER) not in cfg['pins'] or sha256_file(HELPER) != cfg['pins'][str(HELPER)]:
        raise ValueError('pinned original control runner required')
    namespace = {'__name__': '_ergo_ce_runner', '__file__': str(Path(__file__).resolve())}
    exec(compile(HELPER.read_text(), str(HELPER), 'exec'), namespace)
    namespace['CONTROLS'] = ('unweighted_ce',)
    namespace['install_control'] = install_ce
    return namespace


def main():
    # The delegated original parser validates all operations and optional arguments.
    config = Path(sys.argv[sys.argv.index('--config')+1])
    namespace = control_runner(json.loads(config.read_text()))
    namespace['main']()


if __name__ == '__main__':
    main()
