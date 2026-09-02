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


def test_coref_training_can_retain_all_negative_documents(arg_docs) -> None:
    module = _load("train_coref_scorer")
    per_doc = module.build_training_pairs(
        arg_docs,
        neg_ratio=10.0,
        hard_fraction=0.5,
        seed=0,
        include_negative_only_docs=True,
    )

    assert set(per_doc) == {"adoc1"}  # adoc2 has one mention and therefore no candidate pair

    # Add a second same-type singleton so the all-negative document contributes.
    clone = arg_docs[1].nodes[0].model_copy(deep=True)
    clone.event_id = "adoc2::m5"
    clone.metadata["event"] = "EV4"
    clone.trigger_evidence[0].char_start = 19
    clone.trigger_evidence[0].char_end = 27
    arg_docs[1].nodes.append(clone)
    per_doc = module.build_training_pairs(
        arg_docs,
        neg_ratio=10.0,
        hard_fraction=0.5,
        seed=0,
        include_negative_only_docs=True,
    )
    assert set(per_doc) == {"adoc1", "adoc2"}
    assert len(per_doc["adoc2"]) == 1
    assert not per_doc["adoc2"][0].label


def test_coref_training_refuses_a_split_without_any_positive(arg_docs) -> None:
    module = _load("train_coref_scorer")
    with pytest.raises(ValueError, match="refusing to train"):
        module.build_training_pairs(arg_docs[1:], neg_ratio=10.0, hard_fraction=0.5, seed=0)


def test_ere_population_counts_unseen_mentions_as_singletons() -> None:
    """The pipeline's population is smaller than ERE's; the gap must not vanish."""
    module = _load("build_canonical_nodes")

    class FakeNode:
        def __init__(self, event_id, event):
            self.event_id = event_id
            self.metadata = {"event": event}

    class FakeDoc:
        doc_id = "d"
        # ERE has m1..m4; m1/m2 corefer, m3/m4 corefer.
        nodes = [
            FakeNode("m1", "E1"),
            FakeNode("m2", "E1"),
            FakeNode("m3", "E2"),
            FakeNode("m4", "E2"),
        ]

    class FakeCanonical:
        doc_id = "d"
        mention_cluster = ["m1", "m2"]

    report = module.ere_population_coreference([FakeDoc()], {"d": [FakeCanonical()]})
    # m3/m4 were never seen: counted as two singletons, so their gold link is a
    # miss rather than silently dropped from the denominator.
    assert report["n_ere_mentions"] == 4
    assert report["n_covered"] == 2
    assert report["mention_coverage"] == 0.5
    assert report["muc_f1"] == pytest.approx(2 / 3)  # 1 of 2 gold links recovered


def test_ere_population_perfect_when_fully_covered() -> None:
    module = _load("build_canonical_nodes")

    class FakeNode:
        def __init__(self, event_id, event):
            self.event_id = event_id
            self.metadata = {"event": event}

    class FakeDoc:
        doc_id = "d"
        nodes = [FakeNode("m1", "E1"), FakeNode("m2", "E1")]

    class FakeCanonical:
        doc_id = "d"
        mention_cluster = ["m1", "m2"]

    report = module.ere_population_coreference([FakeDoc()], {"d": [FakeCanonical()]})
    assert report["muc_f1"] == 1.0
    assert report["mention_coverage"] == 1.0


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


def test_coref_trainer_requires_both_manifests_together() -> None:
    """A half-specified split would silently fall back to training on everything."""
    import importlib.util

    path = Path(__file__).resolve().parents[2] / "scripts/train_coref_scorer.py"
    spec = importlib.util.spec_from_file_location("train_coref_scorer", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert hasattr(module, "build_eval_pairs")
    source = path.read_text(encoding="utf-8")
    # selection must run on the complete pair universe, not the sampled one
    assert "dev_pairs=build_eval_pairs(dev_docs)" in source
    assert "--train-manifest and --dev-manifest must be given together" in source


def test_maven_arg_and_ere_share_document_ids() -> None:
    """The two corpora are the same documents with different annotation layers.

    This is why the coreference trainer must apply the P1 MAVEN-ERE manifests:
    training on the full MAVEN-Arg train would otherwise include every one of the
    291 internal-dev documents that model selection is supposed to be held out on.
    """
    import json

    root = Path(__file__).resolve().parents[2]
    manifests = root / "data/protocols/v6/manifests"
    dev_ids = set(json.loads((manifests / "maven_ere_internal-dev.json").read_text())["doc_ids"])
    arg_train = root / "data/processed/maven_arg/train.jsonl"
    if not arg_train.exists():  # corpus not present in this checkout
        pytest.skip("MAVEN-Arg train not available")
    arg_ids = {json.loads(line)["id"] for line in arg_train.open(encoding="utf-8") if line.strip()}

    assert dev_ids <= arg_ids
