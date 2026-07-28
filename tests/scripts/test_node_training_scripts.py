"""CPU-testable data preparation of the node-stage training scripts."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from ekg.relations.data import load_maven_arg
from ekg.relations.data.maven_arg import NONE_TYPE

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"


def _load(name: str):
    # Scripts import each other by bare name (as they do when run directly, with
    # their own directory on sys.path), so put `scripts/` there before loading.
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def arg_docs(fixtures_dir):
    return list(load_maven_arg(fixtures_dir / "maven_arg" / "sample.jsonl"))


def test_detection_labels_pin_none_at_index_zero(arg_docs) -> None:
    labels = _load("train_event_detector").detection_labels(arg_docs)
    assert labels[0] == NONE_TYPE
    assert labels == [NONE_TYPE, "Attacking", "Causation", "Motion"]


def test_detection_labels_reject_a_split_without_events(arg_docs) -> None:
    module = _load("train_event_detector")
    for doc in arg_docs:
        doc.candidates = [c for c in doc.candidates if c.event_type == NONE_TYPE]
    with pytest.raises(ValueError, match="NONE only"):
        module.detection_labels(arg_docs)


def test_coref_training_pairs_keep_only_documents_with_a_positive(arg_docs) -> None:
    module = _load("train_coref_scorer")
    per_doc = module.build_training_pairs(arg_docs, neg_ratio=10.0, hard_fraction=0.5, seed=0)
    # adoc1 has the two-mention event; adoc2 is all singletons and is dropped.
    assert set(per_doc) == {"adoc1"}
    assert sum(1 for p in per_doc["adoc1"] if p.label) == 1


def test_coref_training_refuses_a_split_without_any_positive(arg_docs) -> None:
    module = _load("train_coref_scorer")
    with pytest.raises(ValueError, match="refusing to train"):
        module.build_training_pairs(arg_docs[1:], neg_ratio=10.0, hard_fraction=0.5, seed=0)


def test_sweep_scores_each_document_once_across_cells(arg_docs) -> None:
    """The sweep varies threshold/band, which never change the pair scores."""
    module = _load("sweep_canonical_nodes")

    class CountingScorer:
        def __init__(self) -> None:
            self.calls = 0

        def score(self, nodes, pairs, doc_text=""):
            self.calls += 1
            return dict.fromkeys(pairs, 0.5)

    inner = CountingScorer()
    cached = module.CachingScorer(inner)
    doc = arg_docs[0]
    pairs = [(doc.nodes[0].event_id, doc.nodes[1].event_id)]
    for _ in range(5):
        cached.score(doc.nodes, pairs, doc.doc_text)
    assert inner.calls == 1
    assert cached.misses == 1
