import pytest

from ekg.factuality.causal_residual import (
    EDGE_SUBTYPES,
    CausalEdge,
    build_causal_residual,
    consistency_violations,
    decide_edges,
    residual_inputs,
    rewire_edges,
    rewiring_diagnostics,
    validate_arm,
)

# The frozen fold-1 trainer weights (C-25R3F): NONE is down-weighted and the two
# rare subtypes up-weighted, which is exactly why plain argmax is not the rule.
WEIGHTS = {
    "NONE": 0.5834365142779171,
    "CAUSE": 7.695400460634976,
    "PRECONDITION": 4.694399765188356,
}


def _row(head: str, tail: str, none: float, cause: float, precondition: float) -> dict:
    return {
        "doc_id": "d1",
        "head_mention_id": head,
        "tail_mention_id": tail,
        "p_none": none,
        "p_cause": cause,
        "p_precondition": precondition,
    }


def test_decide_edges_uses_the_cost_aware_rule_not_plain_argmax() -> None:
    # Plain argmax says NONE (.80); the frozen weights say CAUSE (.15*7.70 > .80*.58).
    edges = decide_edges([_row("m1", "m2", 0.80, 0.15, 0.05)], WEIGHTS)

    assert edges == [
        CausalEdge(
            head_mention_id="m1", tail_mention_id="m2", subtype="CAUSE", confidence=0.15
        )
    ]


def test_decide_edges_emits_nothing_for_confident_none() -> None:
    assert decide_edges([_row("m1", "m2", 0.99, 0.006, 0.004)], WEIGHTS) == []


@pytest.mark.parametrize(
    "row",
    [
        _row("m1", "m2", 0.5, 0.5, 0.0),
        _row("m1", "m2", 0.5, 0.4, 0.2),
    ],
)
def test_decide_edges_rejects_unusable_posteriors(row: dict) -> None:
    with pytest.raises(ValueError):
        decide_edges([row], WEIGHTS)


def test_decide_edges_requires_the_frozen_class_weights() -> None:
    with pytest.raises(ValueError, match="class weights"):
        decide_edges([_row("m1", "m2", 0.8, 0.15, 0.05)], {"NONE": 1.0, "CAUSE": 1.0})


def _graph() -> list[CausalEdge]:
    return [
        CausalEdge("m1", "m2", "CAUSE", 0.41),
        CausalEdge("m1", "m3", "PRECONDITION", 0.33),
        CausalEdge("m2", "m4", "CAUSE", 0.52),
        CausalEdge("m3", "m4", "CAUSE", 0.28),
        CausalEdge("m4", "m5", "PRECONDITION", 0.61),
        CausalEdge("m5", "m1", "CAUSE", 0.47),
    ]


def test_rewiring_preserves_degrees_and_payload_multiset() -> None:
    original = _graph()

    rewired = rewire_edges(original, fold=1, doc_id="d1")

    report = rewiring_diagnostics(original, rewired)
    assert report.structure_preserved is True
    assert report.edges == len(original)
    assert all(e.head_mention_id != e.tail_mention_id for e in rewired)


def test_rewiring_is_seeded_by_fold_and_document_not_by_the_training_seed() -> None:
    original = _graph()

    assert rewire_edges(original, fold=1, doc_id="d1") == rewire_edges(
        original, fold=1, doc_id="d1"
    )
    assert rewire_edges(original, fold=2, doc_id="d1") != rewire_edges(
        original, fold=1, doc_id="d1"
    )
    assert rewire_edges(original, fold=1, doc_id="d2") != rewire_edges(
        original, fold=1, doc_id="d1"
    )


def test_rewiring_an_empty_graph_stays_empty() -> None:
    assert rewire_edges([], fold=1, doc_id="d1") == []


def test_residual_inputs_index_into_the_trigger_matrix_per_subtype() -> None:
    grouped = residual_inputs(_graph(), ["m1", "m2", "m3", "m4", "m5"])

    assert set(grouped) == set(EDGE_SUBTYPES)
    assert grouped["CAUSE"] == ([0, 1, 2, 4], [1, 3, 3, 0], [0.41, 0.52, 0.28, 0.47])
    assert grouped["PRECONDITION"] == ([0, 3], [2, 4], [0.33, 0.61])


def test_residual_inputs_reject_an_edge_outside_the_scored_mentions() -> None:
    with pytest.raises(KeyError, match="leaves the mention set"):
        residual_inputs(_graph(), ["m1", "m2"])


def test_validate_arm_rejects_an_unregistered_arm() -> None:
    assert validate_arm("rewired") == "rewired"
    with pytest.raises(ValueError, match="unknown D4 arm"):
        validate_arm("oracle")


def test_mediators_count_positive_target_under_negative_source_only() -> None:
    gold = {
        ("m1", "m2"): "CAUSE",  # CT- -> CT+ : violation
        ("m1", "m3"): "CAUSE",  # CT- -> PS- : fine
        ("m4", "m5"): "PRECONDITION",  # PS- -> PS+ : violation
        ("m2", "m5"): "PRECONDITION",  # CT+ -> PS+ : fine
    }
    labels = {"m1": "CT-", "m2": "CT+", "m3": "PS-", "m4": "PS-", "m5": "PS+"}

    report = consistency_violations(gold, labels)

    assert report["CAUSE"] == {"violations": 1, "pairs": 2, "rate": 0.5}
    assert report["PRECONDITION"] == {"violations": 1, "pairs": 2, "rate": 0.5}


def test_mediators_drop_pairs_with_an_unknown_endpoint_from_both_sides() -> None:
    gold = {("m1", "m2"): "CAUSE", ("m1", "m3"): "CAUSE"}
    labels = {"m1": "CT-", "m2": "Uu", "m3": "CT+"}

    report = consistency_violations(gold, labels)

    assert report["CAUSE"] == {"violations": 1, "pairs": 1, "rate": 1.0}


def test_mediators_fail_fast_on_an_unscored_mention() -> None:
    with pytest.raises(KeyError, match="unscored mention"):
        consistency_violations({("m1", "m2"): "CAUSE"}, {"m1": "CT-"})


@pytest.mark.gpu
def test_residual_is_a_no_op_without_edges_and_at_initialisation() -> None:
    torch = pytest.importorskip("torch")
    module = build_causal_residual(4)
    triggers = torch.randn(5, 4)
    empty = {subtype: ([], [], []) for subtype in EDGE_SUBTYPES}

    assert torch.equal(module(triggers, empty), triggers)
    # Zero-initialised messages: the arm starts as base even with a full graph.
    populated = residual_inputs(_graph(), ["m1", "m2", "m3", "m4", "m5"])
    assert torch.equal(module(triggers, populated), triggers)


@pytest.mark.gpu
def test_residual_scales_with_the_gate_and_trains() -> None:
    torch = pytest.importorskip("torch")
    module = build_causal_residual(4)
    with torch.no_grad():
        for message in module.messages.values():
            message.weight.fill_(0.1)
    triggers = torch.ones(5, 4)
    inputs = residual_inputs(_graph(), ["m1", "m2", "m3", "m4", "m5"])
    faint = {
        subtype: (sources, targets, [gate * 1e-6 for gate in gates])
        for subtype, (sources, targets, gates) in inputs.items()
    }

    strong = module(triggers, inputs)
    weak = module(triggers, faint)

    assert not torch.allclose(strong, triggers)
    assert torch.allclose(weak, triggers, atol=1e-5)
    strong.sum().backward()
    assert all(message.weight.grad.abs().sum() > 0 for message in module.messages.values())


def test_rewiring_terminates_on_a_hub_graph_that_defeats_stub_shuffling() -> None:
    # One source, one sink and a shared middle: almost every independent
    # re-pairing of stubs makes a self-loop or a duplicate. Real fold-1
    # document 002383d0…dac3 is this shape, and it exhausted the first
    # implementation's 1,000 retries.
    hub = [CausalEdge("h", f"t{i}", "CAUSE", 0.2 + i / 100) for i in range(8)]
    hub += [CausalEdge(f"t{i}", "z", "PRECONDITION", 0.3 + i / 100) for i in range(8)]

    rewired = rewire_edges(hub, fold=1, doc_id="hub")

    report = rewiring_diagnostics(hub, rewired)
    assert report.structure_preserved is True
    assert report.edges == len(hub)
    assert all(e.head_mention_id != e.tail_mention_id for e in rewired)
    assert len({(e.head_mention_id, e.tail_mention_id) for e in rewired}) == len(hub)
