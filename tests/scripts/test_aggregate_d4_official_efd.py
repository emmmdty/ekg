import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_load_script("aggregate_d4_predicted_causal")
official = _load_script("aggregate_d4_official_efd")


def _run(tmp_path: Path, predictions: list[int], labels: list[int]) -> Path:
    run = tmp_path / "fold-1"
    run.mkdir()
    docs = [
        {
            "id": "d1",
            "events": [
                {"id": "E1", "mention": [{"id": "m1", "factuality": "CT+"},
                                         {"id": "m2", "factuality": "PS-"}]},
                {"id": "E2", "mention": [{"id": "m3", "factuality": "Uu"}]},
            ],
        }
    ]
    (run / "evaluation.jsonl").write_text(
        "\n".join(json.dumps(d, sort_keys=True) for d in docs) + "\n", encoding="utf-8"
    )
    (run / "report.json").write_text(
        json.dumps({"test_predictions": predictions, "test_labels": labels}), encoding="utf-8"
    )
    return run


def test_order_follows_the_upstream_loader_and_labels_are_verified(tmp_path: Path) -> None:
    # Upstream ids: CT+=0, CT-=1, PS+=2, PS-=3, Uu=4.
    run = _run(tmp_path, predictions=[0, 2, 4], labels=[0, 3, 4])

    assert official.mention_order(run / "evaluation.jsonl") == [
        ("d1", "m1"), ("d1", "m2"), ("d1", "m3")
    ]
    assert official.fold_predictions(run) == {
        ("d1", "m1"): "CT+",
        ("d1", "m2"): "PS+",
        ("d1", "m3"): "Uu",
    }


def test_a_misaligned_dump_is_rejected_rather_than_silently_realigned(tmp_path: Path) -> None:
    # Labels say the second mention is CT+, the split file says PS-.
    run = _run(tmp_path, predictions=[0, 0, 4], labels=[0, 0, 4])

    with pytest.raises(ValueError, match="disagrees with the dumped labels"):
        official.fold_predictions(run)


def test_a_truncated_dump_is_rejected(tmp_path: Path) -> None:
    run = _run(tmp_path, predictions=[0, 3], labels=[0, 3])

    with pytest.raises(ValueError, match="3 mentions but 2 predictions"):
        official.fold_predictions(run)


def test_the_upstream_label_order_is_not_ours() -> None:
    from ekg.relations.data.maven_fact import FACTUALITY_LABELS

    assert official.UPSTREAM_LABELS == ("CT+", "CT-", "PS+", "PS-", "Uu")
    assert tuple(FACTUALITY_LABELS) != official.UPSTREAM_LABELS
