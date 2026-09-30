from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _ROOT / "scripts" / "export_easyecr_glt_predictions.py"
_SPEC = importlib.util.spec_from_file_location("export_easyecr_glt_predictions", _SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
G19ExportError = _MODULE.G19ExportError
convert = _MODULE.convert


def _gold() -> dict:
    return {
        "id": "doc-1",
        "events": [
            {"id": "event-1", "mention": [{"id": "m1"}, {"id": "m2"}]},
            {"id": "event-2", "mention": [{"id": "m3"}]},
        ],
        "TIMEX": [],
        "temporal_relations": {},
        "causal_relations": {},
        "subevent_relations": [],
    }


def test_convert_keeps_cluster_partition_and_emits_empty_relation_families() -> None:
    predictions, population = convert(
        [_gold()],
        [
            {
                "id": "doc-1",
                "mention_ids": ["m1", "m2", "m3"],
                "clusters": [["m1", "m2"], ["m3"]],
            }
        ],
    )

    assert predictions[0]["coreference"] == [["m1", "m2"], ["m3"]]
    assert predictions[0]["temporal_relations"] == {
        "BEFORE": [],
        "OVERLAP": [],
        "CONTAINS": [],
        "SIMULTANEOUS": [],
        "ENDS-ON": [],
        "BEGINS-ON": [],
    }
    assert population["documents"] == 1
    assert population["event_mentions"] == 3


def test_convert_rejects_a_raw_cluster_that_does_not_partition_mentions() -> None:
    with pytest.raises(G19ExportError, match="partition"):
        convert(
            [_gold()],
            [
                {
                    "id": "doc-1",
                    "mention_ids": ["m1", "m2", "m3"],
                    "clusters": [["m1", "m2"], ["m2", "m3"]],
                }
            ],
        )
