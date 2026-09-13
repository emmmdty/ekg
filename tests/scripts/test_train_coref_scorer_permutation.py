"""C5's three arms differ by one switch each; none may silently become another.

`full` is the role-compatibility residual, `remove-core` drops it, `permutation`
keeps it but reads vectors shuffled inside document x event type.  The shuffle
itself is pinned by `tests/nodes/test_role_uncertainty.py`.  What these tests
pin is the arm *definition*, where two silent substitutions are possible:

* asking for the control without the component it controls would produce a
  remove-core number wearing a negative-control label;
* `--argument-predictions` selects the corpus (MAVEN-ERE) as well as the
  annotation, so an arm that omits it trains on MAVEN-Arg instead and the arms
  stop sharing one pair population.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "train_coref_scorer",
    Path(__file__).resolve().parents[2] / "scripts" / "train_coref_scorer.py",
)
_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _MODULE
_SPEC.loader.exec_module(_MODULE)  # type: ignore[union-attr]

_PREDICTIONS = ("--argument-predictions", "absent.jsonl")


def _rejection(monkeypatch, capsys, *flags: str) -> str:
    """Why `main` refused this arm, or "" if the arm itself was accepted.

    `argparse` reports through stderr and exits 2, while our own checks raise
    `SystemExit(message)`, so both channels are read.  Anything that gets past
    arm validation dies on the absent corpus -- exactly the signal we want.
    """
    monkeypatch.setattr(
        sys, "argv",
        ["train_coref_scorer.py", "--train", "absent.jsonl", "--output", "unused", *flags],
    )
    try:
        _MODULE.main()
    except SystemExit as exc:
        return f"{exc}\n{capsys.readouterr().err}"
    except Exception:
        return ""
    return ""


def test_the_control_without_its_component_is_refused(monkeypatch, capsys) -> None:
    assert "role_compatibility" in _rejection(
        monkeypatch, capsys, "--permute-role-features", *_PREDICTIONS
    )


def test_the_control_with_its_component_is_accepted(monkeypatch, capsys) -> None:
    assert _rejection(
        monkeypatch, capsys,
        "--permute-role-features", "--components", "role_compatibility", *_PREDICTIONS,
    ) == ""


def test_the_component_alone_is_the_full_arm_not_the_control(monkeypatch, capsys) -> None:
    assert _rejection(
        monkeypatch, capsys, "--components", "role_compatibility", *_PREDICTIONS
    ) == ""


def test_role_compatibility_without_its_input_is_refused(monkeypatch, capsys) -> None:
    """It reads `argument_evidence`, which only the prediction file supplies."""
    assert "requires --argument-predictions" in _rejection(
        monkeypatch, capsys, "--components", "role_compatibility"
    )


def test_the_prediction_file_needs_no_consumer(monkeypatch, capsys) -> None:
    """C5's remove-core arm passes it purely to stay on the same corpus."""
    assert _rejection(monkeypatch, capsys, *_PREDICTIONS) == ""
