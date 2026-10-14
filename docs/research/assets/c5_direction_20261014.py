"""Train-label directional derivatives at a constructed uniform parent distribution."""
import ast
import hashlib
import json
import os
import time
from collections import Counter, defaultdict
from pathlib import Path

import torch

ROOT = Path('runs/stages/R1/r1-v63-c5-20261013')
OUT = ROOT / 'learning_direction_audit'
TRAIN = Path('runs/stages/A3/a3-v6-baselines-r10/preflight/data/MAVEN_ERE/train.jsonl')
ORDER = ROOT / 'frozen_null_control/cache/train/documents.jsonl'
MANIFEST = Path('data/protocols/v6/manifests/maven_ere_train.json')
SOURCE = ROOT / 'training_interface_audit/audit.py'
EXPECTED = {TRAIN: '20ea01ebe71fb8c8e4f207368673cc71f29840a290698eefe15de3a24a3b6f05',
            ORDER: 'a30f606e369c6ed9b0ceb86251ca79c786397c7d6c92da9246bc117c13a0f648',
            MANIFEST: '47d19cc9a17e38259bfbb7f9206c675c7362f41252d23f414ea6cfd46015ca68',
            SOURCE: '93b7fa097e67c5d2d1338c938ecef0ccbed240625a27701ede174322b0467988'}
assert os.environ['CUDA_VISIBLE_DEVICES'] == '-1' and not torch.cuda.is_available()
for path, digest in EXPECTED.items():
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, str(path)
OUT.mkdir(exist_ok=False)
torch.set_num_threads(4)
selected = [node for node in ast.parse(SOURCE.read_text()).body
            if isinstance(node, ast.FunctionDef) and node.name == 'matrices']
assert len(selected) == 1
namespace = {'torch': torch}
exec(compile(ast.Module(body=selected, type_ignores=[]), str(SOURCE), 'exec'), namespace)
matrices = namespace['matrices']
EPS = 1e-8


def kernel(bias, n):
    rows = [bias.new_ones(1)]
    for j in range(1, n):
        rows.append(torch.softmax(torch.cat((bias.expand(j), bias.new_zeros(1))), 0))
    c, product = matrices(rows)
    indices = torch.tril_indices(n, n, offset=-1)
    denominator = (1 - product[indices[0], indices[1]]).sum()
    correction = (c[indices[0], indices[1]] - product[indices[0], indices[1]]).sum()
    if float(denominator.detach()) == 0:
        assert float(correction.detach()) == 0
        alpha = denominator * 0
    else:
        alpha = correction / denominator
    return c, product, product + alpha * (1 - product)


def marginal(groups, mentions, bias):
    terms = []
    exp_bias = bias.exp()
    for block in groups.values():
        seen = Counter()
        for j, (_, label) in enumerate(block):
            gold_previous = seen[label]
            probability = (exp_bias if gold_previous else bias.new_ones(())) / (j * exp_bias + 1)
            targets = gold_previous or 1
            summed = targets * probability.clamp(EPS, 1 - EPS) + (mentions - targets) * EPS
            terms.append(-summed.log())
            seen[label] += 1
    return torch.stack(terms).mean()


def statistics(groups, doc_id, cache):
    prediction, true_positive = [0.] * 4, [0.] * 4
    derivative_prediction, derivative_tp = [0.] * 4, [0.] * 4
    positive = 0
    for kind, block in groups.items():
        n = len(block)
        values, derivatives = cache[n]
        order = sorted(range(n), key=lambda i: hashlib.sha256(
            f'seed13|{doc_id}|{kind}|{block[i][0]}'.encode()).hexdigest())
        all_values = [*values, values[0][order][:, order]]
        all_derivatives = [*derivatives, derivatives[0][order][:, order]]
        for j in range(n):
            for i in range(j):
                same = block[i][1] == block[j][1]
                positive += same
                for arm in range(4):
                    score, slope = float(all_values[arm][j, i]), float(all_derivatives[arm][j, i])
                    prediction[arm] += score
                    true_positive[arm] += score * same
                    derivative_prediction[arm] += slope
                    derivative_tp[arm] += slope * same
    loss, slope = {}, {}
    for arm, name in enumerate(('exact', 'root', 'mass', 'shuffle')):
        numerator = 2 * true_positive[arm] + 1
        denominator = prediction[arm] + positive + 1
        loss[name] = 1 - numerator / denominator
        slope[name] = (numerator * derivative_prediction[arm]
                       - 2 * derivative_tp[arm] * denominator) / denominator ** 2
    return loss, slope, positive


records = [json.loads(line) for line in TRAIN.read_text().splitlines()]
ordering = [json.loads(line) for line in ORDER.read_text().splitlines()]
ids = json.loads(MANIFEST.read_text())['doc_ids']
assert [r['id'] for r in records] == [r['id'] for r in ordering] == ids and len(ids) == 2622
bias = torch.zeros((), dtype=torch.float64, requires_grad=True)
start = time.perf_counter()
cache = {}
for n in range(1, 29):
    cache[n] = torch.autograd.functional.jvp(lambda b, size=n: kernel(b, size),
                                           bias, torch.ones_like(bias))
rows, representatives = [], {}
maximum_marginal_error = 0.
for record, ordering_row in zip(records, ordering, strict=True):
    mapping = {m['id']: (e['id'], e['type']) for e in record['events'] for m in e['mention']}
    assert set(mapping) == set(ordering_row['mentions'])
    assert [mapping[mid][1] for mid in ordering_row['mentions']] == ordering_row['types']
    groups = defaultdict(list)
    for mid in ordering_row['mentions']:
        label, kind = mapping[mid]
        groups[kind].append((mid, label))
    mentions = len(mapping)
    value = marginal(groups, mentions, bias)
    gradient = float(torch.autograd.grad(value, bias)[0])
    independent = 0.
    for block in groups.values():
        seen = Counter()
        for j, (_, label) in enumerate(block):
            gold_previous = seen[label]
            targets = gold_previous or 1
            probability = 1 / (j + 1)
            dp = (1 if gold_previous else -j) / (j + 1) ** 2
            independent -= targets * dp / (targets * probability + (mentions - targets) * EPS)
            seen[label] += 1
    independent /= mentions
    maximum_marginal_error = max(maximum_marginal_error, abs(independent - gradient))
    assert abs(independent - gradient) <= 1e-10
    losses, slopes, positive = statistics(groups, record['id'], cache)
    legal = sum(len(block) * (len(block) - 1) // 2 for block in groups.values())
    group = 'no_legal' if not legal else 'positive' if positive else 'no_positive'
    representatives.setdefault(group, (groups, record['id'], mentions))
    rows.append({'id': record['id'], 'group': group, 'positive_pairs': positive,
                 'legal_pairs': legal, 'marginal_loss': float(value.detach()),
                 'marginal_gradient': gradient, 'aux_loss': losses, 'aux_gradient': slopes,
                 'combined_coref_gradient': {k: .4 * (gradient + slope)
                                            for k, slope in slopes.items()}})

# Independent full-document central differences in the first train document of each stratum.
fd_errors = {}
for group, (groups, doc_id, _mentions) in representatives.items():
    caches = {sign: {n: (kernel(torch.tensor(sign * 1e-6, dtype=torch.float64), n),
                         tuple(torch.zeros((n, n)) for _ in range(3)))
                    for n in {len(block) for block in groups.values()}} for sign in (-1, 1)}
    minus, plus = (statistics(groups, doc_id, caches[sign])[0] for sign in (-1, 1))
    analytic = statistics(groups, doc_id, cache)[1]
    for arm in analytic:
        error = abs((plus[arm] - minus[arm]) / 2e-6 - analytic[arm])
        assert error <= 1e-8
        fd_errors[group + ':' + arm] = error

summary = {}
for name in ('all', 'positive', 'no_positive', 'no_legal'):
    chosen = rows if name == 'all' else [row for row in rows if row['group'] == name]
    summary[name] = {'documents': len(chosen),
                     'mean_marginal_gradient': sum(r['marginal_gradient'] for r in chosen)
                     / len(chosen),
                     'arms': {}}
    for arm in ('exact', 'root', 'mass', 'shuffle'):
        gradients = [r['aux_gradient'][arm] for r in chosen]
        summary[name]['arms'][arm] = {
            'mean_aux_gradient': sum(gradients) / len(chosen),
            'positive_aux_gradient_documents': sum(g > 1e-12 for g in gradients),
            'negative_aux_gradient_documents': sum(g < -1e-12 for g in gradients),
            'mean_combined_coref_gradient': sum(r['combined_coref_gradient'][arm]
                                               for r in chosen) / len(chosen)}
report = {'status': 'complete', 'method_admitted': False, 'neural_model_loaded': False,
          'optimizer_steps': 0, 'final_valid_accessed': False, 'real_logit_bias': 0.,
          'torch_version': torch.__version__, 'cpu_threads': 4, 'summary': summary,
          'maximum_marginal_autograd_vs_analytic_error': maximum_marginal_error,
          'maximum_full_document_aux_fd_error': max(fd_errors.values()),
          'finite_difference_errors': fd_errors, 'elapsed_seconds': time.perf_counter() - start,
          'input_sha256': {str(k): v for k, v in EXPECTED.items()},
          'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'limitation': 'Actual train labels, constructed common-bias direction at uniform logits; '
          'not actual pretrained scores, shared neural update directions, error repair or MUC.'}
(OUT / 'documents.jsonl').write_text(''.join(json.dumps(row) + '\n' for row in rows))
(OUT / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2), flush=True)
