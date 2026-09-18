"""What the untrained role signal claims about a pair, on cases counted by hand.

The corpus run's own guard is the bucket it inherits from C-11; what it cannot
check is that "no comparable role" stays distinct from "roles disagree". Collapse
those two and a pair the extractor said nothing about would rank as suppressible
evidence, which is exactly the confusion `role_uncertainty` exists to avoid.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
from tests.nodes.test_role_uncertainty import mention

_SPEC = importlib.util.spec_from_file_location(
    "estimate_role_suppression_signal",
    Path(__file__).resolve().parents[2] / "scripts" / "estimate_role_suppression_signal.py",
)
_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _MODULE
_SPEC.loader.exec_module(_MODULE)  # type: ignore[union-attr]

pair_evidence = _MODULE.pair_evidence


def test_disjoint_fillers_are_incompatible() -> None:
    incompatible, agreement = pair_evidence(
        mention("m1", participant=("the militia",)), mention("m2", participant=("the police",))
    )
    assert incompatible
    assert agreement == pytest.approx(0.0)


def test_shared_filler_is_compatible() -> None:
    incompatible, agreement = pair_evidence(
        mention("m1", participant=("the militia",)), mention("m2", participant=("militia",))
    )
    assert not incompatible
    assert agreement == pytest.approx(1.0)


def test_a_role_only_one_side_filled_is_not_evidence() -> None:
    """One-sided roles are skipped entirely, not scored as disagreement."""
    incompatible, agreement = pair_evidence(
        mention("m1", participant=("the militia",), place=("Kabul",)),
        mention("m2", participant=("militia",)),
    )
    assert not incompatible
    assert agreement == pytest.approx(1.0)  # only `participant` was comparable


def test_no_comparable_role_scores_none() -> None:
    incompatible, agreement = pair_evidence(mention("m1"), mention("m2", place=("Kabul",)))
    assert not incompatible
    assert agreement is None


def test_agreement_averages_the_comparable_roles() -> None:
    incompatible, agreement = pair_evidence(
        mention("m1", participant=("the militia",), place=("Kabul",)),
        mention("m2", participant=("militia",), place=("Herat",)),
    )
    assert incompatible  # `place` disagrees even though `participant` matches
    assert agreement == pytest.approx(0.5)
