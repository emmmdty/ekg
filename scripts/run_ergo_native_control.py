"""Run a known ERGO control through unchanged pinned native entrypoints."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import sys
from pathlib import Path

from ekg.core.stage_bundle import sha256_file

ENTRIES = {'preflight': 'scripts/preflight_ergo_native.py',
           'train': 'scripts/train_ergo_native.py',
           'verify': 'scripts/verify_ergo_native_checkpoint.py'}
CONTROLS = ('complete_graph', 'gamma0')


def controlled_source(source):
    class Install(ast.NodeTransformer):
        count = 0

        def visit_Assign(self, node):
            if (len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
                    and node.targets[0].id == 'model' and isinstance(node.value, ast.Call)
                    and isinstance(node.value.func, ast.Attribute)
                    and node.value.func.attr == 'LongformerCausalModel'):
                self.count += 1
                return [node, ast.Expr(ast.Call(ast.Name('_install_control', ast.Load()),
                                               [ast.Name('model', ast.Load())], []))]
            return self.generic_visit(node)

    install = Install()
    tree = install.visit(ast.parse(source))
    if install.count != 1:
        raise ValueError('exactly one original model constructor required')
    return ast.unparse(ast.fix_missing_locations(tree)) + '\n'


def install_control(model, control):
    if control not in CONTROLS:
        raise ValueError('unknown control')
    if (model.loss_type != 'focal' or model.focal_loss.gamma != 2
            or model.focal_loss.alpha.tolist() != [.25, .75, .75]):
        raise ValueError('original focal configuration required before intervention')
    info = {'name': control, 'mask_calls': 0}
    if control == 'gamma0':
        model.focal_loss.gamma = 0
    else:
        def complete_graph(unused_module, args):
            import torch

            pairs, mask = args
            n = pairs.shape[1]
            if (n < 2 or mask.dtype != torch.bool or mask.shape != (pairs.shape[0], n, n)
                    or not mask.diagonal(dim1=-2, dim2=-1).all()):
                raise ValueError('original nonempty boolean graph mask required')
            info['mask_calls'] += 1
            return pairs, torch.eye(n, dtype=torch.bool, device=mask.device).unsqueeze(0).expand_as(
                mask)

        model.RGT_layer.register_forward_pre_hook(complete_graph)
    return info


def require_control_evidence(cfg):
    names = ('control_preflight_execution', 'control_preflight_config')
    if any(k not in cfg or cfg[k] not in cfg['pins'] for k in names):
        raise ValueError('own pinned control CUDA preflight required')
    for key in names:
        if sha256_file(Path(cfg[key])) != cfg['pins'][cfg[key]]:
            raise ValueError('control CUDA preflight identity drift')
    execution = json.loads(Path(cfg[names[0]]).read_text())
    smoke_cfg = json.loads(Path(cfg[names[1]]).read_text())
    if (execution['status'] != 'complete' or execution['operation'] != 'preflight'
            or execution['control'] != cfg['control_name']
            or smoke_cfg['control_name'] != cfg['control_name'] or smoke_cfg['device'] != 'cuda'
            or smoke_cfg['server'] != cfg['server']
            or execution['config_sha256'] != cfg['pins'][cfg[names[1]]]
            or execution['wrapper_sha256'] != sha256_file(Path(__file__))):
        raise ValueError('matching actual control CUDA preflight required')
    for key in ('production_smoke_report', 'dev_capacity_report'):
        filename = ('production_report.json' if key == 'production_smoke_report'
                    else 'capacity_report.json')
        expected = Path(smoke_cfg['output']) / filename
        if Path(cfg[key]) != expected:
            raise ValueError('control training must use its own CUDA evidence')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--operation', choices=ENTRIES, required=True)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--report', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--device', choices=('cpu', 'cuda'))
    args = parser.parse_args()
    cfg = json.loads(args.config.read_text())
    if cfg['control_name'] not in CONTROLS or cfg['server'] != 'gpu-4090':
        raise ValueError('fixed known control on primary server required')
    entry = Path(ENTRIES[args.operation])
    for path in (entry, Path(__file__).relative_to(Path.cwd())):
        if str(path) not in cfg['pins'] or sha256_file(path) != cfg['pins'][str(path)]:
            raise ValueError(f'pinned original/control entry required: {path}')
    if args.operation != 'preflight':
        require_control_evidence(cfg)
    argv = [str(entry), '--config', str(args.config)]
    if args.operation == 'verify':
        if args.report is None or args.output is None or args.device is None:
            raise ValueError('explicit report/output/device required for control verification')
        argv += ['--report', str(args.report), '--output', str(args.output),
                 '--device', args.device]
        record_dir = args.output.with_name(args.output.name + '-execution')
    else:
        if any(v is not None for v in (args.report, args.output, args.device)):
            raise ValueError('report/output/device only apply to checkpoint verification')
        record_dir = Path(cfg['control_execution'])
    source = controlled_source(entry.read_text())
    record_dir.mkdir(parents=True, exist_ok=False)
    (record_dir / 'derived_entry.py').write_text(source)
    record = {'status': 'running', 'operation': args.operation, 'control': cfg['control_name'],
              'config_sha256': sha256_file(args.config), 'original_entry': str(entry),
              'original_entry_sha256': sha256_file(entry), 'wrapper_sha256': sha256_file(
                  Path(__file__)),
              'derived_source_sha256': hashlib.sha256(source.encode()).hexdigest(),
              'installed': []}
    record_path = record_dir / 'execution.json'
    record_path.write_text(json.dumps(record, indent=2) + '\n')

    def install(model):
        record['installed'].append(install_control(model, cfg['control_name']))

    namespace = {'__name__': '_ergo_control_entry', '__file__': str(entry),
                 '_install_control': install}
    previous_argv = sys.argv
    try:
        sys.argv = argv
        exec(compile(source, str(record_dir / 'derived_entry.py'), 'exec'), namespace)
        namespace['main']()
        if len(record['installed']) != 1:
            raise ValueError('control was not installed exactly once')
        if cfg['control_name'] == 'complete_graph' and record['installed'][0]['mask_calls'] == 0:
            raise ValueError('complete graph was never applied')
        if args.operation == 'preflight':
            production = json.loads((Path(cfg['output']) / 'production_report.json').read_text())
            ref = Path(cfg['initializer_reference'])
            if str(ref) not in cfg['pins'] or sha256_file(ref) != cfg['pins'][str(ref)]:
                raise ValueError('pinned full initializer reference required')
            expected = json.loads(ref.read_text())['parameter_before']['numeric_sha256']
            if production['parameter_before']['numeric_sha256'] != expected:
                raise ValueError('control/full initial model parameters differ')
            record['initializer_matches_full'] = True
        record['status'] = 'complete'
    except BaseException as exc:
        record.update(status='failed', error=repr(exc))
        raise
    finally:
        sys.argv = previous_argv
        record_path.write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record, indent=2), flush=True)


if __name__ == '__main__':
    main()
