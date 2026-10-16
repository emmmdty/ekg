"""Cancellation-free evaluation of the existing mass-matched forest objective."""
from __future__ import annotations

from collections import defaultdict

from ekg.core.joint_connectivity import (
    ForestPairObjective,
    connectivity_objectives,
    typed_parent_rows,
)


def disagreement_matrices(rows):
    """Same-forest and independent-forest disagreement, using only positive sums."""
    import torch

    exact = rows[0].new_zeros((1, 1))
    roots = rows[0].new_ones((1, 1))
    for j, p in enumerate(rows[1:], 1):
        values = exact @ p[:j] + p[j]
        exact = torch.cat((torch.cat((exact, values[:, None]), 1),
                           torch.cat((values[None, :], exact.new_zeros((1, 1))), 1)), 0)
        marginal = torch.cat((p[:j] @ roots, p[j:j + 1]))
        roots = torch.cat((torch.nn.functional.pad(roots, (0, 1)), marginal[None, :]), 0)
    left = torch.nn.functional.pad(roots[:, :-1].cumsum(1), (1, 0))
    right = torch.nn.functional.pad(roots[:, 1:].flip((1,)).cumsum(1).flip((1,)), (0, 1))
    return exact, roots @ (left + right).T


@connectivity_objectives.register('forest_pair_mass_complement')
class ForestMassComplementObjective:
    """Keep FP32 marginal unchanged; evaluate only mass auxiliary in float64."""

    def __call__(self, logits, clusters, types, doc_id, mentions):
        import torch

        terms = ForestPairObjective(arm='marginal')(logits, clusters, types, doc_id, mentions)
        rows = typed_parent_rows([row.to(torch.float64) for row in logits], types)
        zero = rows[-1].sum() * 0
        predicted, true_positive, positive = zero, zero, 0
        gold = {i: label for label, group in enumerate(clusters) for i in group}
        groups = defaultdict(list)
        for i, kind in enumerate(types):
            groups[kind].append(i)
        for indices in groups.values():
            local = [rows[j][indices[:pos + 1]] for pos, j in enumerate(indices)]
            exact, root = disagreement_matrices(local)
            lower = torch.tril_indices(len(indices), len(indices), -1, device=exact.device)
            exact, root = exact[lower[0], lower[1]], root[lower[0], lower[1]]
            denominator, total = root.sum(), exact.sum()
            if float(denominator.detach()) == 0:
                if float(total.detach()) != 0:
                    raise ValueError('zero root disagreement with nonzero exact disagreement')
                score = 1 - root
            else:
                score = 1 - total * (root / denominator)
            target = score.new_tensor([gold[indices[j]] == gold[indices[i]]
                                       for j in range(len(indices)) for i in range(j)])
            positive += int(target.sum().detach())
            predicted = predicted + score.sum()
            true_positive = true_positive + (score * target).sum()
        terms['auxiliary'] = 1 - (2 * true_positive + 1) / (predicted + positive + 1)
        return terms
