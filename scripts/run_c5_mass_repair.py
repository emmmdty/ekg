#!/usr/bin/env python
"""Isolated numerical repair of the frozen mass arm; all other arms stay sealed."""
from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
from pathlib import Path

import run_c5_joint_dependence as base

from ekg.core.mass_connectivity import ForestMassComplementObjective
from ekg.core.stage_bundle import sha256_file


def require_repair_admission(config, config_sha):
    admission = json.loads(Path(config['admission']).read_text())
    if (admission['method_admitted'] is not True
            or admission['config_sha256'] != config_sha or not admission['evidence_sha256']):
        raise ValueError('matching repair admission required')
    for path, expected in admission['evidence_sha256'].items():
        if sha256_file(Path(path)) != expected:
            raise ValueError('repair evidence drift: ' + path)
    from export_official_coref_cpu import require_smoke

    root = Path(config['output'])
    for path in (root / 'parity/all', root / 'smoke/mass'):
        require_smoke(path, config_sha)
    report = json.loads((root / 'smoke/mass/report.json').read_text())
    if (report['optimizer_steps'] != 1 or report['zero_lr_hooks_used']
            or not report['cpu_cache_replay_and_source_decoder_parity']):
        raise ValueError('repair nonzero update/export smoke required')


def compare_objectives(model, legacy, repaired, torch):
    from profile_original_joint_cost import compare_gradients

    model.zero_grad(set_to_none=True)
    torch.manual_seed(13)
    value = legacy()
    expected = float(value.detach())
    value.backward()
    gradients = {n: p.grad.detach().clone() for n, p in model.named_parameters()
                 if p.grad is not None}
    del value
    model.zero_grad(set_to_none=True)
    torch.manual_seed(13)
    value = repaired()
    actual = float(value.detach())
    value.backward()
    return {'legacy_loss': expected, 'repaired_loss': actual,
            'loss_close': math.isclose(expected, actual, rel_tol=1e-4, abs_tol=1e-6),
            'gradient_parity': compare_gradients(model, gradients, torch)}


def parity(config, modules, tokenizer, records, torch):
    from profile_original_joint_cost import parameter_digest, set_checkpointing

    batch, documents, selected = base.fixture_batch(config, 'peak', modules, tokenizer, records)
    model = modules['model'].Model(len(tokenizer), model_name=config['pretrained'])
    model.train()
    set_checkpointing(model.encoder.model.module, True)
    before = parameter_digest(model)
    legacy = base.connectivity_objectives.create('forest_pair', arm='mass')
    repaired = ForestMassComplementObjective()
    report = compare_objectives(model,
        lambda: base.joint_loss(model, batch, documents, selected, legacy, torch)[0],
        lambda: base.joint_loss(model, batch, documents, selected, repaired, torch)[0], torch)
    if (not report['loss_close'] or not report['gradient_parity']['passed']
            or parameter_digest(model) != before):
        raise ValueError('full-model repair loss/gradient/parameter parity failed: ' + str(report))
    return {'status': 'complete', 'weight_updates': 0, 'comparison': report,
            'parameter_sha256_before_and_after': before, 'final_valid_accessed': False}


def fit(config, stage, output, modules, tokenizer, records, torch):
    """Frozen fit wiring copied solely to inject the repaired objective explicitly."""
    from profile_original_joint_cost import parameter_digest, require_empty_gpu, set_checkpointing
    from transformers import get_linear_schedule_with_warmup

    gpu = require_empty_gpu(os.environ['CUDA_VISIBLE_DEVICES'])
    model = modules['model'].Model(len(tokenizer), model_name=config['pretrained']).cuda()
    model.train()
    set_checkpointing(model.encoder.model.module, True)
    before = parameter_digest(model)
    scorer = torch.optim.Adam((p for n, p in model.named_parameters()
                              if not n.startswith('encoder.')), lr=.0003)
    encoder = torch.optim.AdamW(model.encoder.parameters(), lr=.00002)
    scheduler = get_linear_schedule_with_warmup(encoder, num_warmup_steps=200,
                                              num_training_steps=32800)
    objective = ForestMassComplementObjective()
    if stage == 'smoke':
        batches = [base.fixture_batch(config, name, modules, tokenizer, records)
                   for name in ('peak', 'worst', 'relation_envelope', 'structure_envelope')]
        epochs = 1
    else:
        data = modules['data']
        batches = data.get_dataloader(tokenizer, 'train',
            data_dir=str(Path(config['train_input']).parent), max_length=256,
            batch_size=8, shuffle=True, ignore_nonetype=False)
        if len(batches) != 328 or [d.id for d in batches.dataset.examples] != list(records):
            raise ValueError('training population/order/budget drift')
        documents = {d.id: d for d in batches.dataset.examples}
        epochs = 100

    def loss_at(item):
        model.train()
        if stage == 'smoke':
            batch, docs, selected = item
        else:
            batch = item
            docs = [documents[doc_id] for doc_id in batch['doc_id']]
            selected = [records[doc_id] for doc_id in batch['doc_id']]
        batch = base.move_batch(batch, 'cuda', torch)
        return base.joint_loss(model, batch, docs, selected, objective, torch)[0]

    def on_epoch(row):
        with (output / 'training.jsonl').open('a') as stream:
            stream.write(json.dumps(row) + '\n')
        print(json.dumps(row), flush=True)

    result = base.train_to_endpoint(batches, loss_at, [scorer, encoder], scheduler, torch,
                                    epochs=epochs, on_epoch=on_epoch)
    torch.cuda.synchronize()
    after = parameter_digest(model)
    if before == after or scheduler.last_epoch != result['optimizer_steps']:
        raise ValueError('repair actual update/scheduler failed')
    result.update(status='complete', arm='mass', stage=stage, gpu=gpu,
        parameter_sha256_before=before, parameter_sha256_after=after,
        cuda_peak_allocated_bytes=torch.cuda.max_memory_allocated(),
        cuda_peak_reserved_bytes=torch.cuda.max_memory_reserved(), final_valid_accessed=False,
        zero_lr_hooks_used=False, method_admitted=(stage == 'train'),
        mass_auxiliary_precision='float64', canonical_and_model_precision='float32')
    if stage == 'train':
        checkpoint = output / 'checkpoint.pt'
        torch.save({'model': model.state_dict(), 'scorer_optimizer': scorer.state_dict(),
                    'encoder_optimizer': encoder.state_dict(), 'scheduler': scheduler.state_dict(),
                    'endpoint': result, 'seed': 13}, checkpoint)
        result['checkpoint_sha256'] = sha256_file(checkpoint)
        ids = set(base.load_manifest_ids(Path(config['dev_manifest'])))
        if ids & set(records):
            raise ValueError('train/dev overlap')
        base.export_predictions(config['dev_input'], ids, config['candidate_digest'],
                                model, output, modules, tokenizer, torch)
    else:
        from export_official_coref_cpu import input_population

        projected = base.project_unlabeled(batches[0][2])
        folder = output / 'train_smoke_input'
        folder.mkdir(exist_ok=False)
        path = folder / 'test.jsonl'
        path.write_text(''.join(json.dumps(row) + '\n' for row in projected))
        mapping = {row['id']: row for row in projected}
        digest = input_population(mapping)['candidate_id_digest']
        base.export_predictions(str(path), set(mapping), digest,
                                model, output, modules, tokenizer, torch)
    result['cpu_cache_replay_and_source_decoder_parity'] = True
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--stage', choices=('parity', 'smoke', 'train'), required=True)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    repair = json.loads(args.config.read_text())
    digest = sha256_file(args.config)
    original = Path(repair['base_config'])
    if sha256_file(original) != repair['base_config_sha256']:
        raise ValueError('base configuration drift')
    config = json.loads(original.read_text())
    device = 'cpu' if args.stage == 'parity' else 'cuda'
    base.preflight(config, repair['base_config_sha256'], args.stage, device)
    for path, expected in {**repair['code_sha256'], **repair['input_sha256']}.items():
        if sha256_file(Path(path)) != expected:
            raise ValueError('repair source/input drift: ' + path)
    if args.stage != 'parity':
        from export_official_coref_cpu import require_smoke

        require_smoke(Path(repair['output']) / 'parity/all', digest)
    if args.stage == 'train':
        require_repair_admission(repair, digest)
    print(json.dumps({'preflight': 'pass', 'stage': args.stage}), flush=True)
    if not args.execute:
        return
    import torch

    if ((device == 'cpu' and torch.cuda.is_available())
            or (device == 'cuda' and not torch.cuda.is_available())):
        raise ValueError('requested device unavailable or not hidden')
    output = Path(repair['output']) / args.stage / ('all' if args.stage == 'parity' else 'mass')
    output.mkdir(parents=True, exist_ok=False)
    status = {'status': 'running', 'pid': os.getpid(), 'stage': args.stage, 'arm': 'mass',
        'config_sha256': digest, 'base_config_sha256': repair['base_config_sha256'],
        'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        'final_valid_accessed': False, 'torch_version': torch.__version__}
    (output / 'status.json').write_text(json.dumps(status, indent=2) + '\n')
    try:
        modules, tokenizer, records = base.prepare(config, torch)
        result = (parity(config, modules, tokenizer, records, torch) if args.stage == 'parity'
                  else fit(config, args.stage, output, modules, tokenizer, records, torch))
        result['config_sha256'] = digest
        (output / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
        artifacts = {str(p.relative_to(output)): sha256_file(p) for p in output.rglob('*')
                     if p.is_file() and p.name != 'status.json'}
        status.update(status='complete', artifact_sha256=artifacts)
    except Exception as exc:
        status.update(status='failed', error=repr(exc))
        raise
    finally:
        (output / 'status.json').write_text(json.dumps(status, indent=2) + '\n')


if __name__ == '__main__':
    main()
