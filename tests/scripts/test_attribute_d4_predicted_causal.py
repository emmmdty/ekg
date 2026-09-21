import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


attribute = _load_script("attribute_d4_predicted_causal")


def test_strata_split_on_whether_the_residual_can_reach_the_mention() -> None:
    # Zero in-degree means an exactly zero residual, so that stratum is the one
    # where full and base can only differ through training noise.
    assert attribute._stratum(0) == "in_degree_0"
    assert attribute._stratum(1) == "in_degree_1"
    assert attribute._stratum(2) == "in_degree_2plus"
    assert attribute._stratum(37) == "in_degree_2plus"


def test_sidecar_documents_group_contiguous_rows(tmp_path: Path) -> None:
    path = tmp_path / "s.jsonl"
    path.write_text(
        '{"doc_id": "a", "n": 1}\n{"doc_id": "a", "n": 2}\n{"doc_id": "b", "n": 3}\n',
        encoding="utf-8",
    )

    grouped = [(doc_id, len(rows)) for doc_id, rows in attribute._sidecar_documents(path)]

    assert grouped == [("a", 2), ("b", 1)]
