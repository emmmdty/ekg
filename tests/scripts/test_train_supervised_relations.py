"""CPU tests for the supervised trainer's data preparation.

Only the pure-Python helpers are exercised here (the training loop needs a GPU).
The script is loaded by path because `scripts/` is not on `pythonpath` — the same
pattern as `test_evaluate_relation_pairs.py`.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from ekg.relations.pairs import PairExample

_REPO = Path(__file__).resolve().parents[2]
_PROTOCOL = _REPO / "data" / "protocols" / "v6"


def _load_script():
    path = _REPO / "scripts" / "train_supervised_relations.py"
    spec = importlib.util.spec_from_file_location("train_supervised_relations", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


tr = _load_script()


def _example(index: int, labels: dict[str, str]) -> PairExample:
    return PairExample(
        doc_id="d1", head_id=f"h{index}", tail_id=f"t{index}", distance=1, labels=labels
    )


def test_downsample_negatives_is_deterministic_and_hits_the_ratio():
    rows = [_example(i, {}) for i in range(100)]
    rows += [_example(1000 + i, {"causal": "CAUSE"}) for i in range(4)]
    first = tr.downsample_negatives(rows, ratio=3.0, seed=13)
    second = tr.downsample_negatives(rows, ratio=3.0, seed=13)
    assert first == second  # same seed -> same subset
    assert sum(1 for r in first if r.labels) == 4  # every positive kept
    assert sum(1 for r in first if not r.labels) == 12  # 3 negatives per positive


def test_downsample_negatives_refuses_when_there_are_no_positives():
    # Training on NONE only would silently learn the majority class -- fail loudly.
    with pytest.raises(ValueError):
        tr.downsample_negatives([_example(i, {}) for i in range(10)], ratio=3.0)


def test_class_weights_downweight_the_dominant_none_class():
    rows = [_example(i, {}) for i in range(8)]
    rows += [_example(100 + i, {"causal": "CAUSE"}) for i in range(2)]
    causal = tr.class_weights(rows)["causal"]  # (NONE, CAUSE, PRECONDITION)
    assert causal[0] < causal[1]  # frequent NONE weighted below the sparse CAUSE
    assert causal[2] == 0.0  # never seen -> no weight


def test_class_weights_alpha_tempers_the_imbalance_correction():
    # alpha is the dial between plain inverse frequency (1.0) and uniform (0.0):
    # full weighting makes dense families over-predict, none buries the sparsest.
    rows = [_example(i, {}) for i in range(8)]
    rows += [_example(100 + i, {"causal": "CAUSE"}) for i in range(2)]
    full = tr.class_weights(rows, alpha=1.0)["causal"]
    half = tr.class_weights(rows, alpha=0.5)["causal"]
    assert half[1] < full[1]  # sparse class corrected less aggressively
    assert half[0] > full[0]  # dominant class penalised less
    assert half[1] == pytest.approx(full[1] ** 0.5)


def test_class_weights_accepts_per_family_alpha():
    rows = [_example(i, {}) for i in range(8)]
    rows += [_example(100 + i, {"causal": "CAUSE"}) for i in range(2)]
    per = tr.class_weights(rows, {"causal": 1.0, "temporal": 0.0, "subevent": 0.0})
    assert per["causal"] == tr.class_weights(rows, 1.0)["causal"]  # causal uses its own alpha
    assert per["temporal"] == tr.class_weights(rows, 0.0)["temporal"]  # temporal uses its own


def test_parse_weight_alpha_bare_float_and_per_family():
    assert tr.parse_weight_alpha("0.5") == 0.5
    assert tr.parse_weight_alpha("causal=0.7,temporal=0.25,subevent=0.5") == {
        "causal": 0.7,
        "temporal": 0.25,
        "subevent": 0.5,
    }


def test_parse_weight_alpha_requires_every_family():
    # A per-family spec must name all three -- an unlisted family would otherwise
    # train with a silent default alpha.
    with pytest.raises(ValueError):
        tr.parse_weight_alpha("causal=0.7,temporal=0.25")  # subevent missing
    with pytest.raises(ValueError):
        tr.parse_weight_alpha("causal=0.7,temporal=0.25,subevent=0.5,bogus=1.0")  # unknown


def test_v6_confirmation_families_exclude_temporal() -> None:
    assert tr.validate_confirmation_families(["causal", "subevent"]) == (
        "causal",
        "subevent",
    )
    with pytest.raises(ValueError, match="temporal is outside"):
        tr.validate_confirmation_families(["temporal", "causal", "subevent"])
    with pytest.raises(ValueError, match="duplicates"):
        tr.validate_confirmation_families(["causal", "causal", "subevent"])


def _write_manifest(path: Path, ids: list[str]) -> Path:
    path.write_text(json.dumps({"doc_ids": ids}), encoding="utf-8")
    return path


def test_explicit_manifests_control_split_independently_of_model_seed(tmp_path: Path):
    docs = [SimpleNamespace(doc_id=item) for item in ("d1", "d2", "d3")]
    train = _write_manifest(tmp_path / "train.json", ["d3", "d1"])
    dev = _write_manifest(tmp_path / "dev.json", ["d2"])

    train_docs, dev_docs = tr.split_docs_by_manifests(docs, train, dev)

    assert [doc.doc_id for doc in train_docs] == ["d3", "d1"]
    assert [doc.doc_id for doc in dev_docs] == ["d2"]


def test_explicit_manifests_reject_overlap_and_omission(tmp_path: Path):
    docs = [SimpleNamespace(doc_id=item) for item in ("d1", "d2", "d3")]
    train = _write_manifest(tmp_path / "train.json", ["d1", "d2"])
    overlap = _write_manifest(tmp_path / "overlap.json", ["d2", "d3"])
    with pytest.raises(ValueError, match="overlap"):
        tr.split_docs_by_manifests(docs, train, overlap)

    dev = _write_manifest(tmp_path / "dev.json", [])
    with pytest.raises(ValueError, match="non-empty"):
        tr.split_docs_by_manifests(docs, train, dev)


_TEST_P1_HASH = "a" * 64


def _ready_protocol(tmp_path: Path) -> Path:
    root = tmp_path / "v6"
    (root / "manifests").mkdir(parents=True)
    for name in (
        "maven_ere_train.json",
        "maven_ere_internal-dev.json",
        "maven_ere_final-valid.json",
    ):
        shutil.copy2(_PROTOCOL / "manifests" / name, root / "manifests" / name)
    shutil.copy2(_PROTOCOL / "ch2_candidate_protocol.json", root)
    registry = json.loads((_PROTOCOL / "registry.json").read_text(encoding="utf-8"))
    registry.update(
        {
            "global_protocol_status": "pass",
            "a3_entry_status": "pass",
            "p1_bundle_id": "unit-test-bundle",
            "p1_bundle_protocol_sha256": _TEST_P1_HASH,
        }
    )
    (root / "registry.json").write_text(json.dumps(registry), encoding="utf-8")
    return root


def _validate_current_protocol(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> dict:
    monkeypatch.setattr(tr, "validate_stage_bundle", lambda *args, **kwargs: {})
    protocol = _ready_protocol(tmp_path)
    return tr.validate_v6_protocol_inputs(
        repo_root=_REPO,
        train_path=_REPO / "data/processed/maven_ere/train.jsonl",
        train_manifest=protocol / "manifests/maven_ere_train.json",
        dev_manifest=protocol / "manifests/maven_ere_internal-dev.json",
        protocol_root=protocol,
        expected_p1_protocol_sha256=_TEST_P1_HASH,
    )


def test_v6_protocol_binding_recomputes_split_and_label_universe(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    binding = _validate_current_protocol(monkeypatch, tmp_path)

    assert binding["split_counts"] == {"train": 2622, "internal-dev": 291}
    assert binding["final_valid_accessed"] is False
    assert binding["candidate_summaries"]["train"]["population_counts"][
        "ordered_mention_pairs"
    ] == 2_297_524
    assert binding["candidate_summaries"]["internal-dev"]["population_counts"][
        "ordered_mention_pairs"
    ] == 234_870


def test_v6_protocol_binding_rejects_wrong_trust_root(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    monkeypatch.setattr(tr, "validate_stage_bundle", lambda *args, **kwargs: {})
    protocol = _ready_protocol(tmp_path)
    with pytest.raises(ValueError, match="differs from the command trust root"):
        tr.validate_v6_protocol_inputs(
            repo_root=_REPO,
            train_path=_REPO / "data/processed/maven_ere/train.jsonl",
            train_manifest=protocol / "manifests/maven_ere_train.json",
            dev_manifest=protocol / "manifests/maven_ere_internal-dev.json",
            protocol_root=protocol,
            expected_p1_protocol_sha256="0" * 64,
        )


def test_v6_protocol_binding_rejects_final_valid_as_dev(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    monkeypatch.setattr(tr, "validate_stage_bundle", lambda *args, **kwargs: {})
    protocol = _ready_protocol(tmp_path)
    with pytest.raises(ValueError, match="internal-dev manifest must be"):
        tr.validate_v6_protocol_inputs(
            repo_root=_REPO,
            train_path=_REPO / "data/processed/maven_ere/train.jsonl",
            train_manifest=protocol / "manifests/maven_ere_train.json",
            dev_manifest=protocol / "manifests/maven_ere_final-valid.json",
            protocol_root=protocol,
            expected_p1_protocol_sha256=_TEST_P1_HASH,
        )


def test_v6_protocol_binding_rejects_recomputed_label_drift(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    monkeypatch.setattr(tr, "validate_stage_bundle", lambda *args, **kwargs: {})
    protocol = _ready_protocol(tmp_path)
    real_summary = tr.candidate_protocol_summary

    def drifted(records):
        summary = real_summary(records)
        summary["candidate_label_digest_sha256"] = "0" * 64
        return summary

    monkeypatch.setattr(tr, "candidate_protocol_summary", drifted)
    with pytest.raises(ValueError, match="candidate or expanded-label population drift"):
        tr.validate_v6_protocol_inputs(
            repo_root=_REPO,
            train_path=_REPO / "data/processed/maven_ere/train.jsonl",
            train_manifest=protocol / "manifests/maven_ere_train.json",
            dev_manifest=protocol / "manifests/maven_ere_internal-dev.json",
            protocol_root=protocol,
            expected_p1_protocol_sha256=_TEST_P1_HASH,
        )
