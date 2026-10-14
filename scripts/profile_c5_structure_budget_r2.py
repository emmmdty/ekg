#!/usr/bin/env python
"""Instrument immutable cost probe: reject numeric updates, restore only zero signs."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from pathlib import Path

from ekg.core.stage_bundle import sha256_file


def raw_digest(values):
    digest = hashlib.sha256()
    for index, value in enumerate(values):
        digest.update(str(index).encode() + b'\0')
        digest.update(value.detach().cpu().contiguous().numpy().tobytes())
    return digest.hexdigest()


def attach_integrity_hooks(optimizers, torch):
    receipts = []
    for optimizer_index, optimizer in enumerate(optimizers):
        parameters = [p for group in optimizer.param_groups for p in group['params']]
        baseline = [p.detach().cpu().clone() for p in parameters]
        before = raw_digest(baseline)

        def pre(opt, _args, _kwargs):
            if any(group['lr'] != 0 for group in opt.param_groups):
                raise ValueError('optimizer probe must not train weights')

        def post(opt, _args, _kwargs, parameters=parameters, baseline=baseline,
                 before=before, optimizer_index=optimizer_index):
            is_cuda = any(p.device.type == 'cuda' for p in parameters)
            if is_cuda:
                # Charge native optimizer kernels to native optimizer time.
                torch.cuda.synchronize()
            start = time.perf_counter()
            current = [p.detach().cpu().clone() for p in parameters]
            if not all(torch.equal(a, b) for a, b in zip(current, baseline, strict=True)):
                raise ValueError('numerical parameter update in zero-lr cost probe')
            native_digest = raw_digest(current)
            restored = 0
            with torch.no_grad():
                for p, actual, reference in zip(parameters, current, baseline, strict=True):
                    flips = torch.signbit(actual) != torch.signbit(reference)
                    if flips.any():
                        if not torch.all((actual[flips] == 0) & (reference[flips] == 0)):
                            raise ValueError('sign change outside zero elements')
                        if not p.is_contiguous():
                            raise ValueError('zero-sign restoration requires contiguous parameter')
                        indices = torch.nonzero(flips.flatten(), as_tuple=False).flatten()
                        p.view(-1)[indices.to(p.device)] = reference.flatten()[indices].to(p.device)
                        restored += len(indices)
            if is_cuda:
                torch.cuda.synchronize()
            after = raw_digest([p.detach().cpu() for p in parameters])
            if after != before:
                raise ValueError('zero-sign integrity restoration failed')
            receipts.append({'optimizer_index': optimizer_index,
                             'numeric_parameters_equal': True,
                             'zero_sign_restorations': restored,
                             'raw_sha256_before': before,
                             'raw_sha256_after_native_step': native_digest,
                             'raw_sha256_after_integrity': after,
                             'integrity_seconds': time.perf_counter() - start})

        optimizer.register_step_pre_hook(pre)
        optimizer.register_step_post_hook(post)
    return receipts


def main():
    import profile_c5_structure_budget as core

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--device', choices=('cpu', 'cuda'), required=True)
    parser.add_argument('--fixture', choices=('peak', 'worst'), required=True)
    parser.add_argument('--arm', choices=core.ARMS, required=True)
    args = parser.parse_args()
    import torch

    config = json.loads(args.config.read_text())
    config['_config_sha256'] = sha256_file(args.config)
    core.validate_scope(config, args.device, os.environ.get('CUDA_VISIBLE_DEVICES'),
                        torch.cuda.is_available(), Path.cwd())
    if (sha256_file(Path(__file__)) != config['entrypoint_sha256']
            or sha256_file(Path(core.__file__)) != config['core_entrypoint_sha256']):
        raise ValueError('sealed cost/adapter source drift')
    original_factory = core.probe_optimizers
    receipt_groups = []

    def tracked_optimizers(encoder, scorers, torch):
        optimizers = original_factory(encoder, scorers, torch)
        receipt_groups.append(attach_integrity_hooks(optimizers, torch))
        return optimizers

    core.probe_optimizers = tracked_optimizers
    torch.set_num_threads(4)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.enabled = False
    output = Path(config['output']) / args.device / args.fixture / args.arm
    output.mkdir(parents=True, exist_ok=False)
    try:
        report = core.execute(config, args.device, args.fixture, args.arm, torch)
        if len(receipt_groups) != 1 or len(receipt_groups[0]) != 4:
            raise ValueError('four audited native optimizer calls required')
        receipts = receipt_groups[0]
        for cycle, run in enumerate(report['runs']):
            overhead = sum(x['integrity_seconds'] for x in receipts[2 * cycle:2 * cycle + 2])
            native = run['optimizer_seconds'] - overhead
            if native < 0:
                raise ValueError('optimizer timing accounting failed')
            run['optimizer_seconds_including_integrity'] = run['optimizer_seconds']
            run['optimizer_seconds'] = native
            run['integrity_seconds'] = overhead
        report.update(script_sha256=sha256_file(Path(__file__)),
                      core_script_sha256=sha256_file(Path(core.__file__)),
                      integrity_receipts=receipts,
                      signed_zero_restored=True,
                      limitations=report['limitations'] + ' CPU parameter-integrity snapshots '
                      'and signed-zero restoration are instrument overhead, timed separately. '
                      'Native raw byte changes are retained in receipts; numeric updates fail.')
        (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    except Exception as exc:
        (output / 'failure.json').write_text(json.dumps(
            {'status': 'failed', 'error': repr(exc), 'probe_lr': 0.,
             'integrity_receipts': receipt_groups}) + '\n')
        raise
    hashes = {p.name: sha256_file(p) for p in output.iterdir() if p.is_file()}
    (output / 'artifact_hashes.json').write_text(json.dumps(hashes, indent=2) + '\n')


if __name__ == '__main__':
    main()
