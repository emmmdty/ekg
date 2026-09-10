from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


def _load_converter():
    path = Path("scripts/convert_llmere_causal_predictions.py")
    spec = importlib.util.spec_from_file_location("llmere_converter", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CONVERTER = _load_converter()


def _document(doc_id: str) -> dict:
    return {
        "id": doc_id,
        "events": [
            {"id": "EV1", "mention": [{"id": "m1", "sent_id": 0, "offset": [0, 1]}]},
            {"id": "EV2", "mention": [{"id": "m2", "sent_id": 0, "offset": [2, 3]}]},
        ],
        "TIMEX": [],
    }


def test_converter_emits_complete_official_shape_for_partitioned_generations():
    predictions, report = CONVERTER.convert_predictions(
        source_records=[_document("d1")],
        manifest_ids=["d1"],
        generations=[
            {"predict": "CAUSE: <e1 event>; PRECONDITION: none\nignored rationale"},
            {"predict": "CAUSE: none; PRECONDITION: <e0 event>"},
        ],
        partition_size=30,
    )

    assert report == {
        "documents": 1,
        "expected_generation_rows": 2,
        "generation_rows": 2,
        "partition_size": 30,
        "emitted_causal_pairs": 2,
    }
    assert predictions == [
        {
            "id": "d1",
            "coreference": [],
            "temporal_relations": {
                "BEFORE": [],
                "OVERLAP": [],
                "CONTAINS": [],
                "SIMULTANEOUS": [],
                "ENDS-ON": [],
                "BEGINS-ON": [],
            },
            "causal_relations": {"CAUSE": [["m1", "m2"]], "PRECONDITION": [["m2", "m1"]]},
            "subevent_relations": [],
        }
    ]


def test_converter_rejects_malformed_generation_instead_of_defaulting_to_none():
    with pytest.raises(CONVERTER.ConversionError, match="must contain exactly"):
        CONVERTER.convert_predictions(
            source_records=[_document("d1")],
            manifest_ids=["d1"],
            generations=[
                {"predict": "CAUSE: none"},
                {"predict": "CAUSE: none; PRECONDITION: none"},
            ],
            partition_size=30,
        )


def test_converter_deduplicates_identical_references_within_one_field():
    predictions, report = CONVERTER.convert_predictions(
        source_records=[_document("d1")],
        manifest_ids=["d1"],
        generations=[
            {"predict": "CAUSE: <e1 event>, <e1 event>; PRECONDITION: none"},
            {"predict": "CAUSE: none; PRECONDITION: none"},
        ],
        partition_size=30,
    )

    assert report["emitted_causal_pairs"] == 1
    assert predictions[0]["causal_relations"] == {
        "CAUSE": [["m1", "m2"]],
        "PRECONDITION": [],
    }


def test_converter_rejects_trailing_generation_rows():
    with pytest.raises(CONVERTER.ConversionError, match="trailing rows"):
        CONVERTER.convert_predictions(
            source_records=[_document("d1")],
            manifest_ids=["d1"],
            generations=[
                {"predict": "CAUSE: none; PRECONDITION: none"},
                {"predict": "CAUSE: none; PRECONDITION: none"},
                {"predict": "CAUSE: none; PRECONDITION: none"},
            ],
            partition_size=30,
        )
