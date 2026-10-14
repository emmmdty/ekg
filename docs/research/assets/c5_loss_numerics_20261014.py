"""R1 synthetic boundary audit; no model, optimizer, training or evaluation."""
import ast
import hashlib
import json
import os
import time
from pathlib import Path

import torch

ROOT = Path('runs/stages/R1/r1-v63-c5-20261013')
OUT = ROOT / 'learning_numerics_audit'
SOURCE = ROOT / 'training_interface_audit/audit.py'
SOURCE_SHA = '93b7fa097e67c5d2d1338c938ecef0ccbed240625a27701ede174322b0467988'
assert os.environ['CUDA_VISIBLE_DEVICES'] == '-1' and not torch.cuda.is_available()
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA
assert not (OUT / 'report.json').exists()
torch.set_num_threads(4)
selected = [f for f in ast.parse(SOURCE.read_text()).body
            if isinstance(f, ast.FunctionDef) and f.name == 'matrices']
assert len(selected) == 1
namespace = {'torch': torch}
exec(compile(ast.Module(body=selected, type_ignores=[]), str(SOURCE), 'exec'), namespace)
matrices = namespace['matrices']


def compute(theta, n, labels):
    rows = [theta.new_ones(1)]
    start = 0
    for j in range(1, n):
        logits = torch.cat((theta[start:start + j], theta.new_zeros(1)))
        rows.append(torch.softmax(logits, 0))
        start += j
    c, product = matrices(rows)
    index = torch.tril_indices(n, n, offset=-1)
    exact, independent = c[index[0], index[1]], product[index[0], index[1]]
    correction = (exact - independent).sum()
    denominator = (1 - independent).sum()
    zero_denominator = float(denominator.detach()) == 0
    if zero_denominator:
        assert float(correction.detach()) == 0, 'zero denominator with nonzero correction'
        alpha = denominator * 0
    else:
        alpha = correction / denominator
    rival = independent + alpha * (1 - independent)
    order = sorted(range(n), key=lambda i: hashlib.sha256(
        f'seed13|stress-{n}|T|mention-{i}'.encode()).hexdigest())
    shuffled = c[order][:, order][index[0], index[1]]
    target = theta.new_tensor([labels[int(i)] == labels[int(j)]
                               for i, j in index.T])
    scores = {'exact': exact, 'root': independent, 'mass': rival, 'shuffle': shuffled}
    losses = {name: 1 - (2 * (value * target).sum() + 1)
              / (value.sum() + target.sum() + 1) + theta.sum() * 0
              for name, value in scores.items()}
    return losses, scores, {'zero_denominator': zero_denominator,
                            'alpha': float(alpha.detach()),
                            'mass_error': float((rival.sum() - exact.sum()).detach().abs())}


def logits(n, scenario):
    if scenario == 'random':
        return torch.randn(n * (n - 1) // 2, generator=torch.Generator().manual_seed(13),
                           dtype=torch.float64)
    result = torch.zeros(n * (n - 1) // 2, dtype=torch.float64)
    if scenario == 'dummy':
        result.fill_(-40)
    if scenario == 'chain':
        start = 0
        for j in range(1, n):
            result[start + j - 1] = 40
            start += j
    return result


cases, failures, worst = [], [], {'loss_precision': 0., 'gradient_precision': 0.,
                                 'finite_difference': 0., 'mass_error': 0.}
for n in (1, 2, 4, 8, 28):
    for scenario in ('zero', 'random', 'dummy', 'chain'):
        for partition in ('singleton', 'one', 'parity'):
            labels = {'singleton': list(range(n)), 'one': [0] * n,
                      'parity': [i % 2 for i in range(n)]}[partition]
            reference = {}
            for dtype in (torch.float64, torch.float32):
                theta = logits(n, scenario).to(dtype).requires_grad_()
                start = time.perf_counter()
                loss, scores, diagnostics = compute(theta, n, labels)
                gradients = {name: torch.autograd.grad(value, theta, retain_graph=True)[0]
                             for name, value in loss.items()}
                elapsed = time.perf_counter() - start
                record = {'n': n, 'scenario': scenario, 'partition': partition,
                          'dtype': str(dtype), 'four_aux_forward_backward_seconds': elapsed,
                          **diagnostics, 'arms': {}}
                mass = float(scores['exact'].sum().detach())
                if diagnostics['mass_error'] > 1e-4 + 1e-6 * mass:
                    failures.append([n, scenario, partition, str(dtype), 'mass'])
                worst['mass_error'] = max(worst['mass_error'], diagnostics['mass_error'])
                for name, value in loss.items():
                    gradient = gradients[name]
                    finite = bool(torch.isfinite(value) and torch.isfinite(gradient).all())
                    bounded = bool(((scores[name] >= -1e-5)
                                    & (scores[name] <= 1 + 1e-5)).all())
                    if not finite or not bounded:
                        failures.append([n, scenario, partition, str(dtype), name, 'range'])
                    if n == 1:
                        assert float(value.detach()) == 0 and gradient.numel() == 0
                    record['arms'][name] = {'loss': float(value.detach()),
                                            'gradient_norm': float(gradient.norm()),
                                            'finite': finite, 'bounded': bounded}
                    if dtype == torch.float64:
                        reference[name] = (value.detach(), gradient.detach())
                    else:
                        expected_value, expected_gradient = reference[name]
                        error = float((value.detach() - expected_value).abs())
                        grad_error = float((gradient.double() - expected_gradient).abs().max()
                                           ) if gradient.numel() else 0.
                        worst['loss_precision'] = max(worst['loss_precision'], error)
                        worst['gradient_precision'] = max(worst['gradient_precision'], grad_error)
                        if (error > 1e-5 or not torch.allclose(
                                gradient.double(), expected_gradient, rtol=1e-4, atol=1e-6)):
                            failures.append([n, scenario, partition, name, 'precision'])
                cases.append(record)

# Independent central differences for the full final objective, including alpha derivatives.
theta = logits(4, 'random').requires_grad_()
values = compute(theta, 4, [0, 1, 0, 1])[0]
for name, value in values.items():
    gradient = torch.autograd.grad(value, theta, retain_graph=True)[0]
    numerical = []
    for i in range(len(theta)):
        step = torch.zeros_like(theta)
        step[i] = 1e-6
        plus = compute(theta.detach() + step, 4, [0, 1, 0, 1])[0][name]
        minus = compute(theta.detach() - step, 4, [0, 1, 0, 1])[0][name]
        numerical.append(float((plus - minus) / 2e-6))
    error = float((gradient - theta.new_tensor(numerical)).abs().max())
    worst['finite_difference'] = max(worst['finite_difference'], error)
    if error > 1e-8:
        failures.append([name, 'finite_difference', error])
report = {'status': 'failed' if failures else 'complete', 'method_admitted': False,
          'neural_model_loaded': False, 'optimizer_steps': 0, 'datasets_accessed': False,
          'final_valid_accessed': False, 'torch_version': torch.__version__, 'threads': 4,
          'cases': len(cases), 'aux_gradient_checks': 4 * len(cases),
          'maximum_absolute_errors': worst, 'failures': failures,
          'source_sha256': SOURCE_SHA,
          'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'limitations': 'Synthetic probabilities/labels; kernel timing is not a model epoch '
          'budget or optimizer memory. Boundary gradients do not predict MAVEN gains.'}
OUT.mkdir(exist_ok=True)
(OUT / 'cases.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in cases))
(OUT / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2), flush=True)
if failures:
    raise ValueError('preregistered numerical audit failed; preserve outputs')
