"""The diagnostic must differentiate exactly the losses used by training."""

import pytest

from ekg.nodes.encoding import TORCH_AVAILABLE

pytestmark = pytest.mark.skipif(not TORCH_AVAILABLE, reason="needs torch")


def test_decomposed_loss_matches_original_formula_and_ignores_timex():
    import torch
    from torch.nn.functional import cross_entropy

    from ekg.relations.evidence_objective import loss_terms
    from ekg.relations.pair_evidence import build_pair_evidence, sufficiency_necessity_loss
    from ekg.relations.pair_heads import PAIR_EVIDENCE_HEAD, build_pair_head

    torch.manual_seed(13)
    heads = build_pair_head(PAIR_EVIDENCE_HEAD, hidden_size=2,
                            subtype_counts={"causal": 3, "subevent": 2}).eval()
    features = torch.randn(2, 8, requires_grad=True)
    distances = torch.tensor([0, 1])
    logits = heads(features, distances)
    targets = {"causal": torch.tensor([1, -100]), "subevent": torch.tensor([1, -100])}
    cf = {"retained": features[:1] * .7, "masked": features[:1] * .2}
    records = [build_pair_evidence("d", "a", "b", head_sent=0, tail_sent=2, n_sentences=3)]
    primary, revision, hinge = loss_terms(heads, features, distances, logits, targets,
                                           cf, [0], records, arm="full")
    expected_revision = cross_entropy(heads(features[:1], distances[:1],
                                           cf["retained"])["causal"], targets["causal"][:1])
    expected_hinge = sufficiency_necessity_loss(
        heads.base(features[:1], distances[:1])["causal"],
        heads.base(cf["masked"], distances[:1])["causal"],
        heads.base(cf["retained"], distances[:1])["causal"],
        targets["causal"][:1], scoreable=torch.tensor([True]))
    assert torch.equal(revision, expected_revision)
    assert torch.equal(hinge, expected_hinge)
    assert torch.equal(primary["causal"], cross_entropy(logits["causal"], targets["causal"]))
    (sum(primary.values()) + revision + hinge).backward()
    assert features.grad is not None and torch.isfinite(features.grad).all()

