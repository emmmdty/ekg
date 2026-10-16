"""Typed parent supervision with exact shared-ancestry or matched pair objectives.

Extracted from the sealed C41 research probe without changing its loss arithmetic.
Torch imports remain inside numerical methods; cached parent decoding is pure CPU.
"""
from __future__ import annotations

import hashlib
import math
from collections import defaultdict

from ekg.core.registry import Registry

connectivity_objectives = Registry('coreference_objective')
ARMS = ('marginal', 'root', 'exact', 'mass', 'shuffle')


def typed_parent_rows(logits, types):
    import torch

    if not logits or len(logits) != len(types) or any(len(r) != j for j, r in enumerate(logits)):
        raise ValueError('antecedent score/type population mismatch')
    rows = []
    for j, scores in enumerate(logits):
        if not torch.isfinite(scores).all():
            raise ValueError('nonfinite pair scores')
        legal = torch.tensor([types[i] == types[j] for i in range(j)],
                             device=scores.device, dtype=torch.bool)
        real = scores.masked_fill(~legal, -torch.inf)
        rows.append(torch.softmax(torch.cat((real, scores.new_zeros(1))), dim=0))
    return rows


def pair_matrices(rows):
    import torch

    c = rows[0].new_ones((1, 1))
    q = c
    for j in range(1, len(rows)):
        p = rows[j]
        v = c @ p[:j]
        c = torch.cat([torch.cat([c, v[:, None]], 1),
                       torch.cat([v[None, :], c.new_ones((1, 1))], 1)], 0)
        root = torch.cat([p[:j] @ q, p[j:j + 1]])
        q = torch.cat([torch.nn.functional.pad(q, (0, 1)), root[None, :]], 0)
    return c, q @ q.T


def decode_cached_parents(mentions, rows, types):
    """Replay exact cached float32 probabilities with the original argmax tie rule."""
    if (not mentions or len(set(mentions)) != len(mentions)
            or len(rows) != len(mentions) or len(types) != len(mentions)):
        raise ValueError('cached mention/type population mismatch')
    groups = [{i} for i in range(len(mentions))]
    for j, row in enumerate(rows):
        if (len(row) != j + 1 or not all(math.isfinite(p) and 0 <= p <= 1 for p in row)
                or not math.isclose(sum(row), 1., abs_tol=1e-5)
                or any(row[i] != 0 for i in range(j) if types[i] != types[j])):
            raise ValueError('corrupt/cross-type cached parent row')
        parent = max(range(j + 1), key=row.__getitem__)
        if parent < j:
            union = groups[parent] | groups[j]
            for i in union:
                groups[i] = union
    unique = {tuple(sorted(group)) for group in groups if len(group) > 1}
    return sorted(sorted(mentions[i] for i in group) for group in unique)


@connectivity_objectives.register('forest_pair')
class ForestPairObjective:
    """Fixed C41 loss family; inference uses the same typed parent argmax in all arms."""

    def __init__(self, *, arm):
        if arm not in ARMS:
            raise ValueError('unknown forest objective arm')
        self.arm = arm

    def __call__(self, logits, clusters, types, doc_id, mentions):
        import torch

        rows = typed_parent_rows(logits, types)
        size = len(rows)
        flat = [i for group in clusters for i in group]
        if (len(mentions) != size or len(set(mentions)) != size
                or any(not group for group in clusters) or len(flat) != len(set(flat))
                or set(flat) != set(range(size))):
            raise ValueError('gold cluster/mention population mismatch')
        if any(len({types[i] for i in group}) != 1 for group in clusters):
            raise ValueError('gold cluster spans incompatible types')
        labels = [[0] * size for _ in range(size)]
        for group in clusters:
            ordered = sorted(group)
            labels[ordered[0]][ordered[0]] = 1
            for position, j in enumerate(ordered):
                for i in ordered[:position]:
                    labels[j][i] = 1
        target = rows[0].new_tensor(labels)
        probs = torch.stack([torch.nn.functional.pad(p, (0, size - len(p)), value=-1000)
                             for p in rows])
        marginal = -torch.log(torch.clamp(probs * target, 1e-8, 1 - 1e-8).sum(dim=1)).mean()
        return {'marginal': marginal,
                'auxiliary': self._auxiliary(rows, clusters, types, doc_id, mentions, torch)}

    def _auxiliary(self, rows, clusters, types, doc_id, mentions, torch):
        zero = rows[-1].sum() * 0
        if self.arm == 'marginal':
            return zero
        gold = {i: label for label, group in enumerate(clusters) for i in group}
        groups = defaultdict(list)
        for i, kind in enumerate(types):
            groups[kind].append(i)
        predicted, true_positive, positive = zero, zero, 0
        for kind, indices in groups.items():
            local = [rows[j][indices[:pos + 1]] for pos, j in enumerate(indices)]
            c, product = pair_matrices(local)
            lower = torch.tril_indices(len(indices), len(indices), -1, device=c.device)
            exact, root = c[lower[0], lower[1]], product[lower[0], lower[1]]
            if self.arm == 'exact':
                score = exact
            elif self.arm == 'root':
                score = root
            elif self.arm == 'mass':
                denominator, delta = (1 - root).sum(), (exact - root).sum()
                if float(denominator.detach()) == 0:
                    if float(delta.detach()) != 0:
                        raise ValueError('zero mass denominator with nonzero delta')
                    alpha = denominator * 0
                else:
                    alpha = delta / denominator
                score = root + alpha * (1 - root)
            else:
                order = sorted(range(len(indices)), key=lambda i: hashlib.sha256(
                    f'seed13|{doc_id}|{kind}|{mentions[indices[i]]}'.encode()).hexdigest())
                score = c[order][:, order][lower[0], lower[1]]
            target = c.new_tensor([gold[indices[j]] == gold[indices[i]]
                                   for j in range(len(indices)) for i in range(j)])
            positive += int(target.sum().detach())
            predicted = predicted + score.sum()
            true_positive = true_positive + (score * target).sum()
        return 1 - (2 * true_positive + 1) / (predicted + positive + 1)
