import math

import pytest

from ekg.relations.posteriors import causal_posterior_rows


def test_causal_posterior_rows_preserve_full_ordered_universe() -> None:
    pairs = [("d::m1", "d::m2"), ("d::m2", "d::m1")]
    scores = {
        pairs[0]: (0.7, 0.2, 0.1),
        pairs[1]: (0.1, 0.3, 0.6),
    }

    rows = causal_posterior_rows("d", pairs, scores)

    assert [(row["head_mention_id"], row["tail_mention_id"]) for row in rows] == pairs
    assert rows[0] == {
        "doc_id": "d",
        "head_mention_id": "d::m1",
        "tail_mention_id": "d::m2",
        "p_none": 0.7,
        "p_cause": 0.2,
        "p_precondition": 0.1,
    }


@pytest.mark.parametrize(
    ("scores", "message"),
    [
        ({}, "coverage mismatch"),
        ({("a", "b"): (0.5, 0.5)}, "expected three"),
        ({("a", "b"): (0.5, 0.4, 0.4)}, "do not sum"),
        ({("a", "b"): (math.nan, 0.5, 0.5)}, "non-finite"),
        ({("a", "b"): (-0.1, 0.5, 0.6)}, "outside"),
    ],
)
def test_causal_posterior_rows_fail_fast(scores, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        causal_posterior_rows("d", [("a", "b")], scores)


def test_causal_posterior_rows_reject_self_or_duplicate_pairs() -> None:
    with pytest.raises(ValueError, match="self-pair"):
        causal_posterior_rows("d", [("a", "a")], {("a", "a"): (1.0, 0.0, 0.0)})
    with pytest.raises(ValueError, match="duplicate"):
        causal_posterior_rows(
            "d",
            [("a", "b"), ("a", "b")],
            {("a", "b"): (1.0, 0.0, 0.0)},
        )
