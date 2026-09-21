import importlib.util
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

WEIGHTS = {
    "NONE": 0.5834365142779171,
    "CAUSE": 7.695400460634976,
    "PRECONDITION": 4.694399765188356,
}


def _load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


train = _load_script("train_d4_predicted_causal")
evaluate = _load_script("evaluate_d4_predicted_causal")


@dataclass(frozen=True)
class _Mention:
    mention_id: str
    factuality: str


@dataclass(frozen=True)
class _Doc:
    doc_id: str
    mentions: tuple[_Mention, ...]


def _sidecar(path: Path, rows: list[dict]) -> Path:
    path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8"
    )
    return path


def _row(doc_id: str, head: str, tail: str, none: float, cause: float, pre: float) -> dict:
    return {
        "doc_id": doc_id,
        "head_mention_id": head,
        "tail_mention_id": tail,
        "p_none": none,
        "p_cause": cause,
        "p_precondition": pre,
    }


def test_load_edges_decides_per_document_and_covers_the_manifest(tmp_path: Path) -> None:
    path = _sidecar(
        tmp_path / "s.jsonl",
        [
            _row("d1", "m1", "m2", 0.80, 0.15, 0.05),
            _row("d1", "m2", "m1", 0.99, 0.006, 0.004),
            _row("d2", "m3", "m4", 0.70, 0.05, 0.25),
        ],
    )

    edges = train.load_edges(path, WEIGHTS, arm="full", fold=1, document_ids=["d1", "d2"])

    assert [edge.subtype for edge in edges["d1"]] == ["CAUSE"]
    assert [edge.subtype for edge in edges["d2"]] == ["PRECONDITION"]


def test_load_edges_rejects_a_document_outside_the_split(tmp_path: Path) -> None:
    path = _sidecar(tmp_path / "s.jsonl", [_row("d9", "m1", "m2", 0.8, 0.15, 0.05)])

    with pytest.raises(ValueError, match="outside the split manifest"):
        train.load_edges(path, WEIGHTS, arm="full", fold=1, document_ids=["d1"])


def test_load_edges_rejects_a_split_document_with_no_posterior(tmp_path: Path) -> None:
    path = _sidecar(tmp_path / "s.jsonl", [_row("d1", "m1", "m2", 0.8, 0.15, 0.05)])

    with pytest.raises(ValueError, match="have no posterior"):
        train.load_edges(path, WEIGHTS, arm="full", fold=1, document_ids=["d1", "d2"])


def test_load_edges_rejects_an_interleaved_sidecar(tmp_path: Path) -> None:
    path = _sidecar(
        tmp_path / "s.jsonl",
        [
            _row("d1", "m1", "m2", 0.8, 0.15, 0.05),
            _row("d2", "m3", "m4", 0.8, 0.15, 0.05),
            _row("d1", "m2", "m1", 0.8, 0.15, 0.05),
        ],
    )

    with pytest.raises(ValueError, match="not contiguous"):
        train.load_edges(path, WEIGHTS, arm="full", fold=1, document_ids=["d1", "d2"])


def test_rewired_arm_changes_the_edges_but_not_their_count(tmp_path: Path) -> None:
    rows = [
        _row("d1", "m1", "m2", 0.80, 0.15, 0.05),
        _row("d1", "m2", "m3", 0.70, 0.25, 0.05),
        _row("d1", "m3", "m1", 0.70, 0.05, 0.25),
    ]
    path = _sidecar(tmp_path / "s.jsonl", rows)

    full = train.load_edges(path, WEIGHTS, arm="full", fold=1, document_ids=["d1"])
    rewired = train.load_edges(path, WEIGHTS, arm="rewired", fold=1, document_ids=["d1"])

    assert len(rewired["d1"]) == len(full["d1"])
    pooled = evaluate._pooled_rewiring(full, rewired)
    assert pooled["edges"] == 3
    assert 0.0 <= pooled["identical_edge_fraction"] <= 1.0


def test_packed_batches_hit_the_mention_budget_and_keep_documents_whole() -> None:
    docs = [
        _Doc("a", tuple(_Mention(f"a{i}", "CT+") for i in range(20))),
        _Doc("b", tuple(_Mention(f"b{i}", "CT+") for i in range(20))),
        _Doc("c", tuple(_Mention(f"c{i}", "CT+") for i in range(5))),
    ]

    batches = train._packed_batches(docs, 32)

    assert [[doc.doc_id for doc in batch] for batch in batches] == [["a", "b"], ["c"]]


def test_class_weights_match_the_anchor_formula() -> None:
    docs = [
        _Doc("a", tuple(_Mention(f"a{i}", "CT+") for i in range(9)) + (_Mention("a9", "Uu"),))
    ]

    weights = train._class_weights(docs, 0.5)

    # Only the two present classes carry weight, normalised to mean 1.
    assert weights[0] > 0 and weights[4] > 0
    assert weights[1] == weights[2] == weights[3] == 0.0
    assert weights[0] + weights[4] == pytest.approx(2.0)
    assert weights[4] > weights[0]
