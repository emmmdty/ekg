"""A4 training and diagnostics share the exact loss and supervised row rule."""

from ekg.relations.pair_evidence import arm_flags, consistency_rows, necessity_scoreable


def supervised_rows(records, logits, targets, *, arm: str):
    causal = logits["causal"].detach().argmax(dim=-1).tolist()
    gold = targets["causal"].tolist()
    return consistency_rows(
        records,
        [g not in (-100, 0) for g in gold],
        [g != -100 and p != 0 for p, g in zip(causal, gold, strict=True)],
        arm=arm,
    )


def loss_terms(heads, features, distances, logits, targets, cf, selected, records, *, arm):
    import torch
    from torch.nn.functional import cross_entropy

    from ekg.relations.pair_evidence import sufficiency_necessity_loss

    primary = {
        family: cross_entropy(logits[family], target, ignore_index=-100)
        for family, target in targets.items()
    }
    revision = hinge = logits["causal"].sum() * 0
    if selected:
        picked = torch.tensor(selected, device=features.device)
        target = targets["causal"][picked]
        revised = heads(features[picked], distances[picked], cf["retained"])
        revision = cross_entropy(revised["causal"], target, ignore_index=-100)
        if arm_flags(arm).consistency_loss:
            hinge = sufficiency_necessity_loss(
                heads.base(features[picked], distances[picked])["causal"],
                heads.base(cf["masked"], distances[picked])["causal"],
                heads.base(cf["retained"], distances[picked])["causal"],
                target,
                scoreable=torch.tensor([necessity_scoreable(records[i], arm=arm)
                                        for i in selected], device=features.device),
                ignore_index=-100,
            )
    return primary, revision, hinge
