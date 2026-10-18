#!/usr/bin/env python
"""Independently reload a completed native ERGO checkpoint and recompute official causal scores."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace

from ekg.core.protocol import load_manifest_ids
from ekg.core.stage_bundle import sha256_file
from ekg.relations.ergo_adapter import export_causal_classes
from ekg.relations.maven_ere_official import records_by_id, validate_official_predictions


def load_completed_native_run(config_path, report_path):
    report = json.loads(report_path.read_text())
    if report['status'] != 'complete' or report['epochs_completed'] != 20:
        raise ValueError('complete native run required before checkpoint verification')
    cfg = json.loads(config_path.read_text())
    if (cfg['schema_version'] != 'ekg.ergo_native_training.v2' or cfg['seed'] != 13
            or cfg['epochs'] != 20 or cfg['final_valid_accessed'] is not False
            or report['seed'] != 13 or report['final_valid_accessed'] is not False
            or not all(cfg[k] is True for k in
                       ('training_admitted','budget_admitted','dev_capacity_admitted'))
            or sha256_file(config_path) != report['config_sha256']):
        raise ValueError('complete run/config identity mismatch')
    checkpoint = Path(report['checkpoint'])
    if (not checkpoint.is_file() or sha256_file(checkpoint) != report['checkpoint_sha256']
            or type(report['best_epoch']) is not int or not 1 <= report['best_epoch'] <= 20):
        raise ValueError('selected checkpoint identity mismatch')
    return cfg, report, checkpoint


def require_cached_class_parity(expected, actual, ids):
    if set(expected) != set(actual) or set(actual) != set(ids):
        raise ValueError('complete cached/replayed class coverage required')
    for key in ids:
        if (expected[key] != actual[key] or any(type(v) is not int or v not in (0,1,2)
                for values in (expected[key],actual[key]) for v in values)):
            raise ValueError(f'checkpoint replay class mismatch: {key}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--report', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--device', required=True, choices=('cpu','cuda'))
    args = parser.parse_args()
    cfg, report, checkpoint = load_completed_native_run(args.config, args.report)
    roots = {'gpu-4090':'/data/TJK/ekg', 'gpu-5090':'/mnt/aidata/tongjiakai/ekg'}
    if cfg['server'] not in roots or str(Path.cwd()) != roots[cfg['server']]:
        raise ValueError('checkpoint stays on its training server; no local encoder')
    for name, expected in cfg['pins'].items():
        if sha256_file(Path(name)) != expected:
            raise ValueError(f'verification input/source drift: {name}')
    scope = None
    if cfg['server'] == 'gpu-5090':
        record = cfg['authorization_record']
        if record not in cfg['pins']:
            raise ValueError('pinned backup verification authorization required')
        authorization = json.loads(Path(record).read_text())
        if (authorization['status'] != 'explicitly_authorized'
                or authorization['scope'] != 'ERGO_native_20epochs_seed13'
                or 'independent_checkpoint_verify' not in authorization['operations']):
            raise ValueError('explicit checkpoint verification scope required on backup')
        scope = authorization['scope']
    if args.output.exists():
        raise FileExistsError(args.output)
    ids = load_manifest_ids(Path(cfg['dev_manifest']))
    features = records_by_id(map(json.loads, Path(cfg['dev_features']).read_text().splitlines()),
                             source='independent dev features')
    from prepare_ergo_unlabeled import project_unlabeled
    from train_ergo_native import validate_feature_population

    validate_feature_population(list(features.values()), cfg['dev_digest'])
    raw = records_by_id((project_unlabeled(json.loads(line)) for line in
                         Path(cfg['dev_raw']).read_text().splitlines()),
                        source='independent dev raw')
    if set(ids) != set(features) or set(features) != set(raw):
        raise ValueError('complete dev feature/raw coverage required')
    cached_file = args.report.parent / f"epoch-{report['best_epoch']:02d}-classes.jsonl"
    cached_rows = records_by_id(map(json.loads,cached_file.read_text().splitlines()),
                                source='selected epoch classes')
    cached = {key:value['classes'] for key,value in cached_rows.items()}
    if set(cached) != set(ids):
        raise ValueError('complete cached class coverage required')
    import torch
    from preflight_ergo_native import validate_preflight_environment
    from profile_ergo_native_cost import model_inputs
    from profile_original_joint_cost import require_empty_gpu
    from score_maven_ere_official import _load_evaluator

    gpu = None
    if args.device == 'cpu':
        if os.environ.get('CUDA_VISIBLE_DEVICES') != '-1' or torch.cuda.is_available():
            raise ValueError('CPU verification must hide CUDA')
    else:
        name = validate_preflight_environment(
            device='cuda',server=cfg['server'],cwd=str(Path.cwd()),
            visible=os.environ.get('CUDA_VISIBLE_DEVICES'),available=torch.cuda.is_available(),
            cuda_admitted=True,authorization_scope=scope)
        gpu = require_empty_gpu(os.environ['CUDA_VISIBLE_DEVICES'])
        if name not in torch.cuda.get_device_name(0):
            raise ValueError('verification GPU model mismatch')
    torch.set_num_threads(12)
    torch.manual_seed(13)
    torch.backends.cuda.matmul.allow_tf32 = False
    device = torch.device(args.device)
    state = torch.load(checkpoint, map_location='cpu', weights_only=True)
    if state['epoch'] != report['best_epoch'] or state['config_sha256'] != report['config_sha256']:
        raise ValueError('checkpoint metadata mismatch')
    assets = Path(cfg['pretrained'])
    if {p.name for p in assets.iterdir()} != set(cfg['model_files']):
        raise ValueError('verification pretrained file-set drift')
    spec = importlib.util.spec_from_file_location('external_ergo_verify', cfg['model_source'])
    external = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(external)
    model = external.LongformerCausalModel(SimpleNamespace(
        class_weight=0.75,gamma=2,loss_type='focal',num_heads=4,dropout_att=0.1,
        dropout_emb=0.3,y_class=3,model_name_or_path=str(assets),device=device))
    model.pretrained_model.resize_token_embeddings(50267,mean_resizing=False)
    model.load_state_dict(state['model'],strict=True)
    del state
    model.to(device)
    if any(p.dtype != torch.float32 for p in model.parameters()):
        raise ValueError('original float32 checkpoint required')
    model.eval()
    predictions, classes = {}, {}
    with torch.no_grad():
        for key in ids:
            feature = features[key]
            loss, logits = model(**model_inputs(feature,[0]*len(feature['t1_pos']),device))
            if not torch.isfinite(loss) or not torch.isfinite(logits).all():
                raise ValueError('nonfinite checkpoint inference')
            classes[key] = logits.argmax(-1).cpu().tolist()
            predictions[key] = export_causal_classes(raw[key],classes[key])
    require_cached_class_parity(cached,classes,ids)
    gold = records_by_id(map(json.loads,Path(cfg['dev_gold']).read_text().splitlines()),
                         source='gold for independent official scorer only')
    population = validate_official_predictions(gold,predictions,
                                                expected_candidate_digest=cfg['dev_digest'])
    scores = _load_evaluator(Path(cfg['evaluator'])).evaluate(gold,predictions,'causal')
    if scores != report['best_scores']:
        raise ValueError('independent official scores differ from selected run report')
    for name, expected in cfg['pins'].items():
        if sha256_file(Path(name)) != expected:
            raise ValueError(f'input/source changed during verification: {name}')
    if sha256_file(checkpoint) != report['checkpoint_sha256']:
        raise ValueError('checkpoint changed during verification')
    args.output.mkdir(parents=True,exist_ok=False)
    for name, rows in [('predictions',predictions.values()),
                       ('classes',({'id':key,'classes':classes[key]} for key in ids))]:
        (args.output/f'{name}.jsonl').write_text(
            ''.join(json.dumps(row,separators=(',',':'))+'\n' for row in rows))
    result = {'status':'complete','scope':'independent selected-checkpoint causal verification',
              'device':args.device,'gpu':gpu,'server':cfg['server'],
              'config_sha256':report['config_sha256'],'checkpoint_sha256':report['checkpoint_sha256'],
              'selected_epoch':report['best_epoch'],'cached_classes_equal':True,
              'official_scores_equal':True,'official_causal_scores':scores,'population':population,
              'evaluator_sha256':sha256_file(Path(cfg['evaluator'])),
              'cached_classes_sha256':sha256_file(cached_file),
              'artifact_sha256':{p.name:sha256_file(p) for p in args.output.iterdir()},
              'optimizer_api_calls':0,'new_training_epochs':0,'final_valid_accessed':False,
              'other_families':'not applicable; no guardrail claim'}
    (args.output/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2),flush=True)


if __name__ == '__main__':
    main()
