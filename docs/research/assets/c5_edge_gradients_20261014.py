"""Train-label per-parent gradients at uniform logits; no neural model or updates."""
import ast
import hashlib
import json
import os
from collections import defaultdict
from pathlib import Path

import torch

ROOT = Path('runs/stages/R1/r1-v63-c5-20261013')
OUT = ROOT / 'learning_edge_gradient_audit'
SOURCE = ROOT / 'training_interface_audit/audit.py'
assert os.environ['CUDA_VISIBLE_DEVICES'] == '-1' and not torch.cuda.is_available()
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == (
    '93b7fa097e67c5d2d1338c938ecef0ccbed240625a27701ede174322b0467988')
selected = [f for f in ast.parse(SOURCE.read_text()).body
            if isinstance(f, ast.FunctionDef) and f.name == 'matrices']
assert len(selected) == 1
scope = {'torch': torch}
exec(compile(ast.Module(body=selected, type_ignores=[]), str(SOURCE), 'exec'), scope)
matrices = scope['matrices']
torch.set_num_threads(4)
names = ('exact', 'root', 'mass', 'shuffle')
inputs = json.loads((ROOT / 'learning_direction_audit/report.json').read_text())['input_sha256']
for path, digest in inputs.items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest, path
ordering = [json.loads(line) for line in (ROOT / 'frozen_null_control/cache/train/documents.jsonl')
            .read_text().splitlines()]
records = [json.loads(line) for line in Path(
    'runs/stages/A3/a3-v6-baselines-r10/preflight/data/MAVEN_ERE/train.jsonl')
    .read_text().splitlines()]
common = {r['id']: r for r in map(json.loads,
          (ROOT / 'learning_direction_audit/documents.jsonl').read_text().splitlines())}
assert len(records) == len(ordering) == len(common) == 2622


def losses(theta, groups, doc_id, mentions):
    marginal = []
    predicted = [theta.sum() * 0 for _ in names]
    tp = [theta.sum() * 0 for _ in names]
    positive, start = 0, 0
    for kind, block in groups.items():
        n = len(block)
        rows = [theta.new_ones(1)]
        for j in range(1, n):
            rows.append(torch.softmax(torch.cat((theta[start:start + j], theta.new_zeros(1))), 0))
            start += j
        c, product = matrices(rows)
        indices = torch.tril_indices(n, n, offset=-1)
        exact, root = c[indices[0], indices[1]], product[indices[0], indices[1]]
        denominator = (1 - root).sum()
        numerator = (exact - root).sum()
        if float(denominator.detach()) == 0:
            assert float(numerator.detach()) == 0
            alpha = denominator * 0
        else:
            alpha = numerator / denominator
        order = sorted(range(n), key=lambda i: hashlib.sha256(
            f'seed13|{doc_id}|{kind}|{block[i][0]}'.encode()).hexdigest())
        scores = [exact, root, root + alpha * (1 - root),
                  c[order][:, order][indices[0], indices[1]]]
        truth = theta.new_tensor([block[int(i)][1] == block[int(j)][1] for i, j in indices.T])
        positive += int(truth.sum())
        for arm, score in enumerate(scores):
            predicted[arm] = predicted[arm] + score.sum()
            tp[arm] = tp[arm] + (score * truth).sum()
        for j, (_, label) in enumerate(block):
            target = [i for i in range(j) if block[i][1] == label] or [j]
            summed = rows[j][target].clamp(1e-8, 1 - 1e-8).sum() + (mentions - len(target)) * 1e-8
            marginal.append(-summed.log())
    assert start == theta.numel()
    result = {'marginal': torch.stack(marginal).mean() + theta.sum() * 0}
    result.update({name: 1 - (2 * tp[i] + 1) / (predicted[i] + positive + 1)
                   for i, name in enumerate(names)})
    return result


totals = {group: {name: {'positive': 0, 'negative': 0, 'zero': 0, 'sum': 0.}
                 for name in ('marginal', *names, *(f'combined_{name}' for name in names))}
          for group in ('wrong', 'true', 'ancestor_wrong')}
rows, representatives = [], {}
maximum_sum_error, maximum_fd_error, candidates = 0., 0., 0
OUT.mkdir(exist_ok=False)
for record, cache in zip(records, ordering, strict=True):
    assert record['id'] == cache['id']
    mapping = {m['id']: (e['id'], e['type']) for e in record['events'] for m in e['mention']}
    assert set(mapping) == set(cache['mentions'])
    assert [mapping[mid][1] for mid in cache['mentions']] == cache['types']
    groups = defaultdict(list)
    for mid in cache['mentions']:
        label, kind = mapping[mid]
        groups[kind].append((mid, label))
    edges = []
    for block in groups.values():
        for j in range(1, len(block)):
            for i in range(j):
                true = block[i][1] == block[j][1]
                ancestor = not true and any(block[k][1] == block[j][1] for k in range(i + 1, j))
                edges.append(('true' if true else 'wrong', ancestor))
    theta = torch.zeros(len(edges), dtype=torch.float64, requires_grad=True)
    value = losses(theta, groups, record['id'], len(mapping))
    gradients = {name: torch.autograd.grad(v, theta, retain_graph=True)[0]
                 for name, v in value.items()}
    for name in ('marginal', *names):
        expected = common[record['id']]['marginal_gradient'] if name == 'marginal' else (
            common[record['id']]['aux_gradient'][name])
        error = abs(float(gradients[name].sum()) - expected)
        maximum_sum_error = max(maximum_sum_error, error)
        assert error <= 1e-8 and torch.isfinite(gradients[name]).all()
    gradients.update({f'combined_{name}': .4 * (gradients['marginal'] + gradients[name])
                      for name in names})
    for i, (group, ancestor) in enumerate(edges):
        for subset in [group, *(['ancestor_wrong'] if ancestor else [])]:
            for name, gradient in gradients.items():
                g = float(gradient[i])
                sign = 'positive' if g > 1e-12 else 'negative' if g < -1e-12 else 'zero'
                totals[subset][name][sign] += 1
                totals[subset][name]['sum'] += g
    if edges:
        representatives.setdefault('first_legal',
                                   (groups, record['id'], len(mapping), len(edges), 0))
    if any(ancestor for _, ancestor in edges):
        index = next(i for i, (_, ancestor) in enumerate(edges) if ancestor)
        representatives.setdefault('first_ancestor',
                                   (groups, record['id'], len(mapping), len(edges), index))
    if max(map(len, groups.values())) == 28:
        representatives.setdefault('largest_block',
                                   (groups, record['id'], len(mapping), len(edges), 0))
    rows.append({'id': record['id'], 'candidates': len(edges),
                 'ancestor_wrong_candidates': sum(a for _, a in edges),
                 'gradient_sums': {k: float(v.sum()) for k, v in gradients.items()}})
    candidates += len(edges)
assert candidates == 66141
for groups, doc_id, mentions, size, index in representatives.values():
    theta = torch.zeros(size, dtype=torch.float64, requires_grad=True)
    value = losses(theta, groups, doc_id, mentions)
    step = torch.zeros_like(theta)
    step[index] = 1e-6
    plus, minus = losses(theta.detach() + step, groups, doc_id, mentions), losses(
        theta.detach() - step, groups, doc_id, mentions)
    for name in value:
        gradient = float(torch.autograd.grad(value[name], theta, retain_graph=True)[0][index])
        numerical = float((plus[name] - minus[name]) / 2e-6)
        maximum_fd_error = max(maximum_fd_error, abs(numerical - gradient))
        assert abs(numerical - gradient) <= 1e-8
report = {'status': 'complete', 'method_admitted': False, 'neural_model_loaded': False,
          'optimizer_steps': 0, 'final_valid_accessed': False, 'documents': len(rows),
          'candidates': candidates, 'gradient_direction_counts': totals,
          'maximum_sum_vs_common_bias_error': maximum_sum_error,
          'maximum_selected_edge_fd_error': maximum_fd_error,
          'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'input_sha256': inputs,
          'limitation': 'Uniform synthetic logits with actual train labels. Candidate-gradient '
          'signs do not establish actual pretrained errors, neural updates, power or MUC.'}
(OUT / 'documents.jsonl').write_text(''.join(json.dumps(row) + '\n' for row in rows))
(OUT / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2), flush=True)
