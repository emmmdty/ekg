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
compare = _load_script("compare_d4_label_dumps")


def test_pooled_labels_reject_a_mention_scored_in_two_folds(tmp_path: Path) -> None:
    root = tmp_path / "runs"
    for fold in range(1, 6):
        directory = root / "full" / f"fold-{fold}"
        directory.mkdir(parents=True)
        (directory / "evaluation_labels.json").write_text(
            json.dumps({"m1": "CT+"}), encoding="utf-8"
        )

    with pytest.raises(ValueError, match="scored twice"):
        compare._pooled_labels(root, "full")


def test_pooled_labels_merge_disjoint_folds(tmp_path: Path) -> None:
    root = tmp_path / "runs"
    for fold in range(1, 6):
        directory = root / "full" / f"fold-{fold}"
        directory.mkdir(parents=True)
        (directory / "evaluation_labels.json").write_text(
            json.dumps({f"m{fold}": "CT+"}), encoding="utf-8"
        )

    assert compare._pooled_labels(root, "full") == {f"m{i}": "CT+" for i in range(1, 6)}


def test_the_comparison_declares_itself_diagnostic() -> None:
    source = (ROOT / "scripts/compare_d4_label_dumps.py").read_text(encoding="utf-8")
    assert '"diagnostic_only": True' in source
