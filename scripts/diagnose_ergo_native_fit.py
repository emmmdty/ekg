"""Measure native train fit of the frozen selected ERGO checkpoint, without updates."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from ekg.core.stage_bundle import sha256_file
from ekg.relations.ergo_adapter import CAUSAL_CLASSES


def confusion_for_labels(target, predicted):
    if (not target or len(target) != len(predicted)
            or any(type(v) is not int or v not in (0, 1, 2) for v in [*target, *predicted])):
        raise ValueError('complete integer native classes required')
    result = np.zeros((3, 3), dtype=np.int64)
    np.add.at(result, (target, predicted), 1)
    return result


def causal_metrics(confusion):
    c = np.asarray(confusion)
    if (c.shape != (3, 3) or not np.issubdtype(c.dtype, np.integer) or np.any(c < 0)):
        raise ValueError('nonnegative integer 3x3 confusion required')
    tp = int(c[1, 1] + c[2, 2])
    predicted, gold = int(c[:, 1:].sum()), int(c[1:, :].sum())
    return {'true_positive': tp, 'false_positive': predicted-tp, 'false_negative': gold-tp,
            'causal_precision': 100*tp/predicted if predicted else 0.,
            'causal_recall': 100*tp/gold if gold else 0.,
            'causal_f1': 200*tp/(predicted+gold) if predicted+gold else 0.}


def require_train_manifest(manifest):
    if manifest['split_role'] != 'train':
        raise ValueError('only the original train manifest is allowed')


def require_fit_scope(cfg, native, proof):
    if (cfg['diagnostic_admitted'] is not True or cfg['final_valid_accessed'] is not False
            or cfg['seed'] != 13):
        raise ValueError('frozen diagnostic scope required')
    if (proof.get('status') != 'complete' or proof.get('cached_classes_equal') is not True
            or proof.get('official_scores_equal') is not True
            or proof.get('final_valid_accessed') is not False):
        raise ValueError('complete independent replay proof required')
    if (native.get('control_name') is not None or native['seed'] != 13 or native['epochs'] != 20
            or native['final_valid_accessed'] is not False):
        raise ValueError('the fixed full native run is required')


def predict_fit(model, rows, device, *, deadline, on_document):
    import torch
    from profile_ergo_native_cost import model_inputs

    confusion = np.zeros((3, 3), dtype=np.int64)
    model.eval()
    with torch.no_grad():
        for feature, target in rows:
            if time.monotonic() > deadline:
                raise TimeoutError('train-fit wall budget exhausted')
            inputs = model_inputs(feature, [0]*len(target), device)
            loss, logits = model(**inputs)
            if (logits.shape != (len(target), 3) or logits.dtype != torch.float32
                    or not torch.isfinite(loss).all() or not torch.isfinite(logits).all()):
                raise ValueError('finite complete native logits required')
            labels = logits.argmax(-1).cpu().tolist()
            current = confusion_for_labels(target, labels)
            confusion += current
            on_document(feature['id'], labels, current)
    return confusion


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path)
    args = parser.parse_args()
    cfg = json.loads(args.config.read_text())
    if cfg['diagnostic_admitted'] is not True:
        raise ValueError('diagnostic not admitted')
    if cfg['schema_version'] != 'ekg.ergo_native_fit.v1':
        raise ValueError('frozen train-fit v1 contract required')
    native_path, report_path = Path(cfg['native_config']), Path(cfg['training_report'])
    proof_path = Path(cfg['independent_report'])
    for path in (native_path, report_path, proof_path, Path(__file__).relative_to(Path.cwd())):
        if str(path) not in cfg['pins'] or sha256_file(path) != cfg['pins'][str(path)]:
            raise ValueError(f'fit source identity mismatch: {path}')
    native = json.loads(native_path.read_text())
    proof = json.loads(proof_path.read_text())
    require_fit_scope(cfg, native, proof)
    require_train_manifest(json.loads(Path(native['train_manifest']).read_text()))
    if (str(Path.cwd()) != '/data/TJK/ekg' or cfg['server'] != 'gpu-4090'
            or native['server'] != cfg['server'] or os.environ.get('CUDA_VISIBLE_DEVICES') != '1'):
        raise ValueError('train-fit encoder runs only on its primary server and fixed GPU1')
    if cfg['wall_seconds'] <= 0:
        raise ValueError('explicit wall budget required')
    started = time.monotonic()
    deadline = started + cfg['wall_seconds']
    output = Path(cfg['output'])
    output.mkdir(parents=True, exist_ok=False)
    (output/'config.json').write_bytes(args.config.read_bytes())
    config_sha = sha256_file(args.config)

    def status(phase, completed=0):
        value = {'status': 'running', 'phase': phase, 'pid': os.getpid(),
                 'documents_completed': completed, 'config_sha256': config_sha}
        tmp = output/'status.json.tmp'
        tmp.write_text(json.dumps(value)+'\n')
        tmp.replace(output/'status.json')
        print(json.dumps(value), flush=True)

    status('verify_frozen_assets')
    for path, h in cfg['pins'].items():
        if sha256_file(Path(path)) != h:
            raise ValueError(f'fit input/source drift: {path}')
    from train_ergo_native import aligned_training_data, validate_feature_population
    from verify_ergo_native_checkpoint import load_completed_native_run

    _, report, checkpoint = load_completed_native_run(native_path, report_path)
    if (proof['config_sha256'] != report['config_sha256']
            or proof['checkpoint_sha256'] != report['checkpoint_sha256']
            or proof['selected_epoch'] != report['best_epoch']):
        raise ValueError('selected checkpoint and independent replay differ')
    reference = json.loads(Path(cfg['dev_reference']).read_text())
    dev_confusion = reference['contrasts']['full_minus_official_joint_primary']['left_confusion']
    dev_metrics = causal_metrics(dev_confusion)
    if any(not np.isclose(dev_metrics[key], value, rtol=0, atol=1e-10)
           for key, value in proof['official_causal_scores'].items()):
        raise ValueError('native confusion disagrees with verified official dev scoring')
    rows = aligned_training_data(Path(native['train_features']), Path(native['train_targets']),
                                 Path(native['train_manifest']))
    validate_feature_population([f for f, _ in rows], native['train_digest'])
    target_counts = np.bincount([v for _, target in rows for v in target], minlength=3)
    if (len(rows) != cfg['expected_documents'] or int(target_counts.sum()) != cfg['expected_pairs']
            or target_counts.tolist() != cfg['expected_class_counts']):
        raise ValueError('complete frozen train population required')
    import torch
    from profile_original_joint_cost import require_empty_gpu

    torch.set_num_threads(12)
    torch.manual_seed(13)
    torch.backends.cuda.matmul.allow_tf32 = False
    device = torch.device('cuda')
    status('load_selected_checkpoint')
    state = torch.load(checkpoint, map_location='cpu', weights_only=True)
    if state['epoch'] != report['best_epoch'] or state['config_sha256'] != report['config_sha256']:
        raise ValueError('checkpoint metadata mismatch')
    weights = Path(native['pretrained'])
    if {p.name for p in weights.iterdir()} != set(native['model_files']):
        raise ValueError('pretrained file-set drift')
    spec = importlib.util.spec_from_file_location('ergo_fit_model', native['model_source'])
    external = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(external)
    model = external.LongformerCausalModel(SimpleNamespace(
        class_weight=.75, gamma=2, loss_type='focal', num_heads=4, dropout_att=.1,
        dropout_emb=.3, y_class=3, model_name_or_path=str(weights), device=device))
    model.pretrained_model.resize_token_embeddings(50267, mean_resizing=False)
    model.load_state_dict(state['model'], strict=True)
    del state
    gpu = require_empty_gpu('1')
    if (gpu['uuid'] != cfg['gpu_uuid'] or not torch.cuda.is_available()
            or 'RTX 4090' not in torch.cuda.get_device_name(0)):
        raise ValueError('fixed available primary GPU required')
    model.to(device)
    if any(p.dtype != torch.float32 for p in model.parameters()):
        raise ValueError('original float32 checkpoint required')
    status('train_forward')
    completed = 0
    forward_started = time.monotonic()
    with (output/'classes.jsonl').open('x') as classes, (output/'counts.jsonl').open('x') as counts:
        def document(key, labels, confusion):
            nonlocal completed
            completed += 1
            classes.write(json.dumps({'id': key, 'classes': labels}, separators=(',', ':'))+'\n')
            counts.write(json.dumps({'id': key, 'confusion': confusion.tolist()})+'\n')
            if completed % 100 == 0 or completed == len(rows):
                classes.flush()
                counts.flush()
                status('train_forward', completed)

        confusion = predict_fit(model, rows, device, deadline=deadline, on_document=document)
    torch.cuda.synchronize()
    forward_seconds = time.monotonic()-forward_started
    if completed != len(rows) or confusion.sum(axis=1).tolist() != target_counts.tolist():
        raise ValueError('native prediction/target count conservation failed')
    for path, h in cfg['pins'].items():
        if sha256_file(Path(path)) != h:
            raise ValueError(f'source/input changed during fit diagnostic: {path}')
    if (sha256_file(checkpoint) != report['checkpoint_sha256']
            or sha256_file(args.config) != config_sha):
        raise ValueError('checkpoint/config changed during fit diagnostic')
    if time.monotonic() > deadline:
        raise TimeoutError('train-fit wall budget exhausted during final checks')
    result = {'status': 'complete', 'scope': 'in-sample native three-class fit diagnostic only',
              'config_sha256': config_sha, 'checkpoint_sha256': report['checkpoint_sha256'],
              'selected_epoch': report['best_epoch'], 'gpu': gpu, 'documents': completed,
              'relation_pairs': int(confusion.sum()), 'confusion_order': list(CAUSAL_CLASSES),
              'confusion': confusion.tolist(), 'native_train_metrics': causal_metrics(confusion),
              'verified_dev_metrics': proof['official_causal_scores'],
              'native_dev_metric_equivalence': True, 'forward_seconds': forward_seconds,
              'total_seconds': time.monotonic()-started, 'optimizer_api_calls': 0,
              'new_training_epochs': 0, 'final_valid_accessed': False,
              'targets_passed_to_model': 'all-zero placeholders',
              'limitations': ['In-sample fit, not a new main-table or held-out performance.',
                              'Does not uniquely identify optimization or generalization cause.']}
    (output/'report.json').write_text(json.dumps(result, indent=2)+'\n')
    (output/'status.json').write_text(json.dumps({'status': 'complete', 'pid': os.getpid(),
                                                'documents_completed': completed})+'\n')
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    main()
