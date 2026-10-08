"""Recovery probes preserve train-only selection and all cached candidates."""

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from ekg.nodes.encoding import TORCH_AVAILABLE

ROOT = Path(__file__).resolve().parents[2]


def script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_gradient_sample_is_train_only_and_independent_of_source_order():
    select = script("audit_a4_checkpoint_gradients").select_documents
    docs = [SimpleNamespace(doc_id=i, nodes=[SimpleNamespace(event_type="x")] * 2,
                            doc_text="sentence")
            for i in ("train-a", "dev", "train-b")]
    first = select(docs, {"train-a", "train-b"}, 2)
    assert {d.doc_id for d in first} == {"train-a", "train-b"}
    assert [d.doc_id for d in first] == [d.doc_id for d in select(docs[::-1],
                                                              {"train-a", "train-b"}, 2)]
    with pytest.raises(ValueError, match="eligible"):
        select(docs, {"train-a"}, 2)


def test_cache_rejects_missing_duplicate_future_and_nonfinite_pairs():
    validate = script("probe_coref_decoders").validate_cache_record
    valid = {"id": "d", "mentions": ["a", "b", "c"],
             "average_order": ["a", "b", "c"],
             "types": ["x", "x", "y"], "scores": [["a", "b", 0.6]]}
    validate(valid)
    for scores in ([], [["a", "b", 0.6]] * 2, [["b", "a", 0.6]],
                   [["a", "b", float("nan")]], [["a", "b", 1.1]]):
        with pytest.raises(ValueError):
            validate({**valid, "scores": scores})


def test_average_replay_requires_identical_original_clusters():
    check = script("probe_coref_decoders").require_same_clusters
    check({"id": "d", "coreference": [["b", "a"]]}, [["a", "b"]])
    with pytest.raises(ValueError, match="reproduce"):
        check({"id": "d", "coreference": [["a", "b"]]}, [])


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="needs torch")
def test_official_decoder_connects_chain_and_masks_different_types():
    module = script("probe_coref_decoders")
    row = {"id": "d", "mentions": ["a", "b", "c", "z"],
           "average_order": ["a", "b", "c", "z"],
           "types": ["x", "x", "x", "y"],
           "scores": [["a", "b", .8], ["a", "c", .2], ["b", "c", .9]]}
    utils = ROOT / "data/protocols/v6/sources/MAVEN-ERE/coreference/src/utils.py"
    assert module.decode_official(row, utils) == [["a", "b", "c"]]


@pytest.fixture
def tiny_encoder(tmp_path):
    pytest.importorskip("torch")
    from transformers import BertConfig, BertModel, BertTokenizerFast

    model = tmp_path / "tiny"
    model.mkdir()
    (model / "vocab.txt").write_text("[PAD]\n[UNK]\n[CLS]\n[SEP]\n[MASK]\n*\n")
    BertTokenizerFast(vocab_file=str(model / "vocab.txt")).save_pretrained(model)
    BertModel(BertConfig(vocab_size=6, hidden_size=8, num_hidden_layers=1,
                         num_attention_heads=2, intermediate_size=16)).save_pretrained(model)
    return model


@pytest.mark.parametrize("name", ["linear", "tanh5"])
def test_real_tiny_training_and_detector_reload(name, tiny_encoder, tmp_path, monkeypatch):
    import torch

    from ekg.factuality.baselines import BaselineFactualityDetector
    from ekg.relations.data.maven_fact import load_maven_fact

    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
    docs = list(load_maven_fact(ROOT / "data/fixtures/maven_fact/sample.jsonl"))
    output = tmp_path / name
    script("train_factuality_detector").train_baseline(
        docs, docs, model_name=str(tiny_encoder), output=output, epochs=1,
        lr=2e-5, alpha=.5, pooling="cls", max_length=64, batch_size=32, seed=13,
        head_name=name)
    assert json.loads((output / "baseline_config.json").read_text())["head_name"] == name
    assert json.loads((output / "dev_curve.json").read_text())["selected_epoch"] == 1
    detector = BaselineFactualityDetector(checkpoint_path=str(output))
    assert set(detector.predict(docs[0])) == {m.mention_id for m in docs[0].mentions}


def test_real_audit_forward_and_gradients_on_tiny_encoder(tiny_encoder, monkeypatch):
    import sys

    from transformers import AutoModel, AutoTokenizer

    from ekg.relations.data.maven_ere import load_maven_ere
    from ekg.relations.extractor.supervised import FAMILY_SUBTYPES
    from ekg.relations.pair_heads import PAIR_EVIDENCE_HEAD, build_pair_head

    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    # The trainer imports its existing encoder functions with torch available.
    assert "torch" in sys.modules
    doc = next(load_maven_ere(ROOT / "data/fixtures/maven_ere/sample_with_text.jsonl",
                              include_timex=True))
    encoder = AutoModel.from_pretrained(tiny_encoder)
    heads = build_pair_head(PAIR_EVIDENCE_HEAD, hidden_size=8,
                            subtype_counts={f: len(s) for f, s in FAMILY_SUBTYPES.items()})
    result = script("audit_a4_checkpoint_gradients").audit_document(
        doc, encoder, AutoTokenizer.from_pretrained(tiny_encoder), heads,
        max_length=64, weight=1., device="cpu")
    assert result["selected_rows"]
    assert result["encoder_alignment"]["main_vs_revision"]["primary_norm"] > 0
    assert all(p.grad is None for p in encoder.parameters())


def test_real_coref_export_and_replay_match_old_submission(tiny_encoder, tmp_path, monkeypatch):
    import torch

    from ekg.nodes.coref import SupervisedCoreferenceScorer
    from ekg.nodes.discriminative import head_input_dim
    from ekg.relations.data.maven_ere import _parse_unlabeled

    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
    submission = script("build_maven_ere_submission")
    source = ROOT / "data/fixtures/maven_ere/sample_with_text.jsonl"
    docs = [_parse_unlabeled(submission.strip_to_test_shape(json.loads(line)))[0]
            for line in source.read_text().splitlines() if line.strip()]
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"doc_ids": [d.doc_id for d in docs]}))
    arguments = tmp_path / "arguments.jsonl"
    arguments.write_text("".join(json.dumps({"doc_id": d.doc_id, "mention_id": n.event_id,
                                             "status": "empty", "roles": {}}) + "\n"
                                  for d in docs for n in d.nodes))
    torch.save(torch.nn.Linear(head_input_dim(8, ()), 2).state_dict(),
               tiny_encoder / "coref_head.pt")
    (tiny_encoder / "coref_config.json").write_text(
        json.dumps({"components": [], "argument_source": "none"}))
    old = SupervisedCoreferenceScorer(checkpoint_path=str(tiny_encoder))
    original = tmp_path / "original.jsonl"
    original.write_text("".join(json.dumps({"id": d.doc_id,
        "coreference": submission.predict_coreference(d, old, threshold=.7, band=0.)})
        + "\n" for d in docs))
    cache = tmp_path / "pairs.jsonl"
    module = script("probe_coref_decoders")
    module.export(SimpleNamespace(source=source, manifest=manifest, arguments=arguments,
                                   checkpoint=tiny_encoder, output=cache))
    output = tmp_path / "replay"
    module.replay(SimpleNamespace(cache=cache, original=original, output=output,
        utils=ROOT / "data/protocols/v6/sources/MAVEN-ERE/coreference/src/utils.py"))
    assert (output / "average.jsonl").is_file()
    assert (output / "antecedent.jsonl").is_file()
    assert (output / "provenance.json").is_file()
