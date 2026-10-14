"""R1 actual-initializer CPU gradient audit; no optimization or method training."""
import ast
import hashlib
import importlib
import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

import torch
from transformers import RobertaTokenizer

from ekg.core.stage_bundle import sha256_file

assert Path.cwd() == Path('/mnt/aidata/tongjiakai/ekg')
assert os.environ['CUDA_VISIBLE_DEVICES'] == '-1' and not torch.cuda.is_available()
sys.path.insert(0, str(Path('scripts').resolve()))
from profile_joint_cost_target import verify_inputs  # noqa: E402
from profile_original_joint_cost import fixture, parameter_digest, set_checkpointing  # noqa: E402
from run_first_dummy_control import marginal_loss, typed_probabilities  # noqa: E402

config = json.loads(Path('configs/c5_cost_5090_20261014.json').read_text())
verify_inputs(config)
assert sha256_file(Path('scripts/run_first_dummy_control.py')) == (
    '0dbbfc88f61b9d0104b7bfc74841c17d8faf17096ef39a6055ee671e07b9e847')
source = Path(config['source_root']).resolve()
sys.path.insert(0, str(source))
data, model_module = (importlib.import_module('src.' + name) for name in ('data', 'model'))
for name, module in [('data', data), ('model', model_module)]:
    assert Path(module.__file__).resolve() == source / 'src' / (name + '.py')
matrix_source = Path('runs/stages/R1/r1-v63-c5-20261013/training_interface_audit/audit.py')
assert sha256_file(matrix_source) == (
    '93b7fa097e67c5d2d1338c938ecef0ccbed240625a27701ede174322b0467988')
selected = [f for f in ast.parse(matrix_source.read_text()).body
            if isinstance(f, ast.FunctionDef) and f.name == 'matrices']
assert len(selected) == 1
scope = {'torch': torch}
exec(compile(ast.Module(body=selected, type_ignores=[]), str(matrix_source), 'exec'), scope)
matrices = scope['matrices']
out = Path('runs/stages/R1/r1-v64-c5-5090-20261014/actual_aux_cpu')
out.mkdir(exist_ok=False)
torch.set_num_threads(4)
torch.manual_seed(13)
ids, expected_chunks = fixture(json.loads(Path(config['census']).read_text()), 'peak')
raw = {r['id']: r for r in map(json.loads, Path(config['train_input']).read_text().splitlines())}
tokenizer = RobertaTokenizer.from_pretrained(config['pretrained'], local_files_only=True)
dataset = data.myDataset.__new__(data.myDataset)
dataset.tokenizer, dataset.max_length, dataset.ignore_nonetype = tokenizer, 256, False
dataset.examples = [data.Document(raw[doc_id], ignore_nonetype=False) for doc_id in ids]
dataset.tokenize()
dataset.to_tensor()
batch = data.collator(dataset.tokenized_samples)
assert batch['input_ids'].shape == (expected_chunks, 256)
model = model_module.Model(len(tokenizer), model_name=config['pretrained'])
model.train()
set_checkpointing(model.encoder.model.module, True)
before = parameter_digest(model)
captured = []
hook = model.coref_scorer.score.register_forward_hook(
    lambda _m, _i, output: captured.append(output))
torch.manual_seed(13)
start = time.perf_counter()
_, temporal, causal, subevent = model(batch)
hook.remove()
forward_seconds = time.perf_counter() - start
terms = {name: [] for name in ('marginal', 'exact', 'root', 'mass', 'shuffle')}
cursor = 0
for doc, record in zip(dataset.examples, [raw[doc_id] for doc_id in ids], strict=True):
    mids = [doc.events[i]['id'] for i in doc.events_idx]
    mapping = {m['id']: e['type'] for e in record['events'] for m in e['mention']}
    assert set(mids) == set(mapping)
    n = len(mids)
    if n > 1:
        scores = captured[cursor].flatten()
        cursor += 1
        assert len(scores) == n * (n - 1) // 2
        logits = [scores.new_empty(0), *torch.split(scores, list(range(1, n)))]
    else:
        logits = [temporal.new_empty(0)]
    rows = typed_probabilities(logits, [mapping[mid] for mid in mids], torch)
    terms['marginal'].append(marginal_loss(rows, doc.coref_labels, corrected=True, torch=torch))
    gold = {i: label for label, group in enumerate(doc.coref_labels) for i in group}
    groups = defaultdict(list)
    for i, mid in enumerate(mids):
        groups[mapping[mid]].append(i)
    soft_pred = [temporal.sum() * 0 for _ in range(4)]
    soft_tp = [temporal.sum() * 0 for _ in range(4)]
    positive = 0
    for kind, indices in groups.items():
        local_rows = [rows[j][indices[:position + 1]] for position, j in enumerate(indices)]
        c, product = matrices(local_rows)
        lower = torch.tril_indices(len(indices), len(indices), offset=-1)
        exact, root = c[lower[0], lower[1]], product[lower[0], lower[1]]
        denominator, numerator = (1 - root).sum(), (exact - root).sum()
        if float(denominator.detach()) == 0:
            assert float(numerator.detach()) == 0
            alpha = denominator * 0
        else:
            alpha = numerator / denominator
        order = sorted(range(len(indices)), key=lambda i: hashlib.sha256(
            f'seed13|{doc.id}|{kind}|{mids[indices[i]]}'.encode()).hexdigest())
        alternatives = [exact, root, root + alpha * (1 - root),
                        c[order][:, order][lower[0], lower[1]]]
        target = temporal.new_tensor([gold[indices[int(i)]] == gold[indices[int(j)]]
                                      for i, j in lower.T])
        positive += int(target.sum())
        for arm, score in enumerate(alternatives):
            soft_pred[arm] = soft_pred[arm] + score.sum()
            soft_tp[arm] = soft_tp[arm] + (score * target).sum()
    for i, name in enumerate(('exact', 'root', 'mass', 'shuffle')):
        terms[name].append(1 - (2 * soft_tp[i] + 1) / (soft_pred[i] + positive + 1))
assert cursor == len(captured)
losses = {name: torch.stack(values).mean() for name, values in terms.items()}
relations = sum(weight * torch.nn.functional.cross_entropy(
    score.reshape(-1, score.shape[-1]), batch[key + '_labels'].reshape(-1), ignore_index=-100)
    for weight, key, score in zip((2., 4., 4.), ('temporal', 'causal', 'subevent'),
                                 (temporal, causal, subevent), strict=True))
losses = {'relations': relations, **losses}
parameters = [(name, p) for name, p in model.named_parameters()
              if name.startswith(('encoder.', 'coref_scorer.'))]
references, report = {}, {}


def vector_norm(gradients, prefix):
    return sum(float(g.double().square().sum()) for (name, _), g in
               zip(parameters, gradients, strict=True)
               if g is not None and name.startswith(prefix)) ** .5


for name, loss in losses.items():
    start = time.perf_counter()
    gradients = torch.autograd.grad(loss, [p for _, p in parameters],
                                    retain_graph=True, allow_unused=True)
    assert torch.isfinite(loss) and all(torch.isfinite(g).all() for g in gradients if g is not None)
    item = {'loss': float(loss.detach()), 'seconds': time.perf_counter() - start,
            'head_norm': vector_norm(gradients, 'coref_scorer.'),
            'encoder_norm': vector_norm(gradients, 'encoder.'),
            'unused_parameters': [n for (n, _), g in zip(parameters, gradients, strict=True)
                                  if g is None]}
    assert item['encoder_norm'] > 0
    if name != 'relations':
        assert item['head_norm'] > 0
        item['weighted_head_norm'] = .4 * item['head_norm']
        item['weighted_encoder_norm'] = .4 * item['encoder_norm']
    else:
        assert item['head_norm'] == 0
    for reference_name, reference in references.items():
        for prefix in ('encoder.', 'coref_scorer.'):
            dot = sum(float((g.double() * ref.double()).sum()) for (n, _), g, ref in
                      zip(parameters, gradients, reference, strict=True)
                      if n.startswith(prefix) and g is not None and ref is not None)
            denominator = vector_norm(gradients, prefix) * vector_norm(reference, prefix)
            item[prefix + 'cosine_to_' + reference_name] = (
                dot / denominator if denominator else None)
    if name in ('relations', 'marginal'):
        references[name] = [g.detach().clone() if g is not None else None for g in gradients]
    report[name] = item
    print(name, json.dumps(item), flush=True)
assert parameter_digest(model) == before
result = {'status': 'complete', 'method_admitted': False, 'optimizer_steps': 0,
          'final_valid_accessed': False, 'machine': 'gpu-5090 CPU only', 'doc_ids': ids,
          'token_chunks': expected_chunks, 'forward_seconds': forward_seconds,
          'parameter_sha256_before_and_after': before, 'arms': report,
          'config_sha256': sha256_file(Path('configs/c5_cost_5090_20261014.json')),
          'input_sha256': config['input_sha256'],
          'pretrained_digest': config['pretrained_digest'],
          'matrix_source_sha256': sha256_file(matrix_source),
          'script_sha256': sha256_file(Path(__file__)),
          'limitations': 'Initial pretrained model, one frozen train fixture. No actual parameter '
          'update, deployment predictions, CUDA/optimizer memory or epoch budget. '
          'Fixed scales unchanged.'}
(out / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
