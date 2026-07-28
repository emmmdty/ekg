"""CPU-testable pieces of the factuality training / reporting scripts."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from ekg.relations.data.maven_fact import FACTUALITY_LABELS, load_maven_fact

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"


def _load(name: str):
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def fact_docs(fixtures_dir):
    return list(load_maven_fact(fixtures_dir / "maven_fact" / "sample.jsonl"))


def test_class_weights_are_inverse_frequency_normalized(fact_docs) -> None:
    weights = _load("train_factuality_detector").class_weights(fact_docs, alpha=1.0)
    assert len(weights) == len(FACTUALITY_LABELS)
    # CT+ is the majority class in the fixture (2 of 6), so it is down-weighted
    # relative to the singleton classes.
    ct_plus = weights[FACTUALITY_LABELS.index("CT+")]
    uu = weights[FACTUALITY_LABELS.index("Uu")]
    assert ct_plus < uu
    assert sum(weights) / len(weights) == pytest.approx(1.0)


def test_alpha_zero_is_uniform_and_alpha_interpolates(fact_docs) -> None:
    module = _load("train_factuality_detector")
    uniform = module.class_weights(fact_docs, alpha=0.0)
    assert uniform == pytest.approx([1.0] * len(FACTUALITY_LABELS))
    # The inverted-U that Phase A measured lives between these ends: a half
    # exponent must sit strictly between no compensation and full inverse
    # frequency, never outside them.
    half = module.class_weights(fact_docs, alpha=0.5)
    full = module.class_weights(fact_docs, alpha=1.0)
    ct_plus = FACTUALITY_LABELS.index("CT+")
    assert full[ct_plus] < half[ct_plus] < uniform[ct_plus]


def test_class_weights_zero_out_classes_with_no_examples(fixtures_dir) -> None:
    module = _load("train_factuality_detector")
    docs = list(load_maven_fact(fixtures_dir / "maven_fact" / "sample.jsonl"))[:1]
    weights = module.class_weights(docs, alpha=0.5)
    # fdoc1 has no PS- and no Uu: an absent class gets weight 0 rather than an
    # infinite up-weight that would just add noise to the loss scale.
    assert weights[FACTUALITY_LABELS.index("PS-")] == 0.0
    assert weights[FACTUALITY_LABELS.index("Uu")] == 0.0
    assert all(w > 0 for w in weights if w)


def test_evaluate_scores_a_lexicon_detector_end_to_end(fact_docs) -> None:
    from ekg.factuality.detection import LexiconFactualityDetector

    module = _load("train_factuality_detector")
    detector = LexiconFactualityDetector().fit(fact_docs)
    report, evidence_prf = module.evaluate(detector, fact_docs)
    # Memorizing its own training set, the lexicon is perfect on it — which is
    # exactly why the floor it sets has to be read on held-out data.
    assert report["macro_f1"] == pytest.approx(1.0)
    assert report["n_mentions"] == sum(len(d.mentions) for d in fact_docs)
    # The lexicon predicts no evidence at all, so its span score is a real zero
    # against a non-empty gold set rather than an undefined division.
    assert evidence_prf["n_pred"] == 0
    assert evidence_prf["n_gold"] > 0
    assert evidence_prf["f1"] == 0.0
