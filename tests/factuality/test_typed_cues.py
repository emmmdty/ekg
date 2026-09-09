"""CPU contracts for the D4 typed-cue/factorized factuality family."""

from __future__ import annotations

import pytest

from ekg.factuality.detection import build_factuality_detector, factuality_detectors
from ekg.factuality.typed_cues import (
    FULL_ARM,
    PERMUTATION_ARM,
    REMOVE_CORE_ARM,
    build_typed_cue_decision_head,
    cue_type_targets,
    factor_targets,
    permutation_indices,
    recompose_factor_probabilities,
    structured_confusion_report,
)
from ekg.nodes.encoding import TORCH_AVAILABLE
from ekg.relations.data.maven_fact import FACTUALITY_LABELS, load_maven_fact


def test_factor_targets_cover_the_unchanged_five_label_space() -> None:
    assert factor_targets(FACTUALITY_LABELS) == [
        (0, 0, 0),  # CT+
        (0, 1, 0),  # PS+
        (0, 0, 1),  # CT-
        (0, 1, 1),  # PS-
        (1, 0, 0),  # Uu
    ]
    with pytest.raises(ValueError, match="unknown factuality label"):
        factor_targets(["not-a-label"])


def test_typed_cue_targets_keep_modality_and_polarity_separate(fixtures_dir) -> None:
    docs = list(load_maven_fact(fixtures_dir / "maven_fact" / "sample.jsonl"))
    mention = docs[0].mentions[1]  # CT- with three annotated evidence words.
    candidates = [
        cue
        for cue in docs[0].mentions[1].evidence
    ]
    assert cue_type_targets(candidates, mention) == [(0, 1), (0, 1), (0, 1)]


def test_permutation_is_replayable_and_stays_inside_each_document() -> None:
    doc_ids = ["a", "a", "a", "b", "b", "c"]
    first = permutation_indices(doc_ids, 13)
    assert first == permutation_indices(doc_ids, 13)
    for destination, origin in enumerate(first):
        assert doc_ids[destination] == doc_ids[origin]
    assert sorted(first) == list(range(len(doc_ids)))


def test_structured_confusions_only_count_the_registered_pairs() -> None:
    gold = {
        "unknown": "Uu",
        "modality": "CT+",
        "polarity": "PS+",
        "both": "CT+",
    }
    predicted = {
        "unknown": "CT+",
        "modality": "PS+",
        "polarity": "PS-",
        "both": "PS-",
    }
    report = structured_confusion_report(predicted, gold)
    assert report == {
        "unknown": 1,
        "modality_only": 1,
        "polarity_only": 1,
        "total": 3,
        "rate": 0.75,
        "mentions": 4,
    }


def test_typed_cue_detector_is_loaded_through_the_lazy_registry() -> None:
    detector = build_factuality_detector("typed_cue", arm=FULL_ARM)
    assert "typed_cue" in factuality_detectors
    assert detector.arm == FULL_ARM


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="needs torch")
def test_factor_recomposition_is_normalized_and_matches_the_five_corners() -> None:
    import torch

    # Each row makes one of the five states near-certain.  The public output
    # remains in FACTUALITY_LABELS order, rather than a new factor label space.
    logits = torch.tensor(
        [
            [-10.0, -10.0, -10.0],
            [-10.0, 10.0, -10.0],
            [-10.0, -10.0, 10.0],
            [-10.0, 10.0, 10.0],
            [10.0, 0.0, 0.0],
        ]
    )
    probabilities = recompose_factor_probabilities(logits)
    assert torch.allclose(probabilities.sum(dim=-1), torch.ones(5))
    assert probabilities.argmax(dim=-1).tolist() == list(range(5))


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="needs torch")
def test_full_and_flat_control_have_identical_parameter_budget() -> None:
    full = build_typed_cue_decision_head(8, 3, arm=FULL_ARM)
    flat = build_typed_cue_decision_head(8, 3, arm=REMOVE_CORE_ARM)
    permutation = build_typed_cue_decision_head(8, 3, arm=PERMUTATION_ARM)
    def count(module) -> int:
        return sum(parameter.numel() for parameter in module.parameters())

    assert count(full) == count(flat) == count(permutation)
