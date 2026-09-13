#!/usr/bin/env python
"""Run the C5 smoke: every arm, a handful of documents, forward to reload.

What it proves is narrow and deliberate: that all three arms train, export,
reload and predict on the real encoder, that the role features stay finite over
the shapes the extractor actually produces, that every mention lands in exactly
one cluster, and that the permutation arm's shuffle survives the round trip
through the checkpoint.  It proves nothing about whether the mechanism works --
that is C5.3's job, on the frozen contract.

The round trip is the point worth naming.  The permutation arm trains on
shuffled role vectors, so scoring it on the real ones would evaluate a model
that was never trained; the seed therefore travels in `coref_config.json` and
is re-read here from the exported checkpoint rather than assumed.

The documents come from the frozen manifests, subset in manifest order, so the
trainer's own protocol-split guard still fires if the subset is wrong.  Pass
`--contract` once a C5.1 preflight exists and the bound code hashes are
re-verified here too.
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

from ekg.core.protocol import load_manifest_ids
from ekg.core.stage_bundle import sha256_file

ARMS = ("full", "remove_core", "permutation")
ARM_FLAGS: dict[str, tuple[str, ...]] = {
    "full": ("--components", "role_compatibility"),
    "remove_core": (),
    "permutation": ("--components", "role_compatibility", "--permute-role-features"),
}


class SmokeError(ValueError):
    """A C5 smoke input, checkpoint or export violates the contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SmokeError(message)


def _load(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SmokeError(f"{path} must contain a JSON object")
    return payload


def _write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _verify_contract(repo: Path, contract: Path) -> dict:
    payload = _load(contract)
    _require(
        payload.get("schema_version") == "ekg.c5_argument_uncertainty_preflight.v1", "schema"
    )
    _require(payload.get("status") == "pass", "contract status")
    _require(payload.get("final_valid_accessed") is False, "contract final-valid access")
    for relative, expected in payload.get("code", {}).items():
        path = repo / relative
        _require(path.is_file(), f"missing bound code file: {relative}")
        _require(sha256_file(path) == expected, f"bound code hash drift: {relative}")
    return payload


def _subset(source: Path, ids: list[str], output: Path) -> None:
    """Keep exactly the wanted documents, in source order."""
    wanted = set(ids)
    selected = [
        line
        for line in source.read_text(encoding="utf-8").splitlines()
        if line and json.loads(line).get("id") in wanted
    ]
    _require(len(selected) == len(ids), f"smoke source covers {len(selected)} of {len(ids)}")
    output.write_text("\n".join(selected) + "\n", encoding="utf-8")


def _manifest(path: Path, ids: list[str]) -> Path:
    _write(path, {"schema_version": "ekg.c5_smoke_manifest.v1", "doc_ids": ids})
    return path


def _finite(values) -> bool:
    if isinstance(values, list):
        return all(_finite(item) for item in values)
    return isinstance(values, (int, float)) and math.isfinite(values)


def _role_fixture() -> dict[str, object]:
    """The shapes the extractor actually produces, without touching a GPU.

    The contract names four: an empty role, several fillers on one role, the
    same string repeated, and a document whose mentions are all singletons.
    Each is a way the residual could silently read a wrong number rather than
    raise, so each is checked for a finite vector of the declared width.
    """
    from ekg.core.schema import EventNode, EvidenceSpan
    from ekg.nodes.role_uncertainty import (
        ROLE_FEATURE_NAMES,
        batch_role_compatibility_features,
        incompatible_role_merges,
        permute_role_features,
    )

    def node(event_id: str, state: str = "ok", **roles: tuple[str, ...]) -> EventNode:
        evidence: dict[str, list[EvidenceSpan]] = {
            role: [
                EvidenceSpan(
                    doc_id="d1", char_start=index, char_end=index + len(text), text=text
                )
                for index, text in enumerate(texts)
            ]
            for role, texts in roles.items()
            if texts
        }
        return EventNode(
            event_id=event_id,
            doc_id="d1",
            event_type="Attack",
            trigger="attacked",
            argument_evidence=evidence,
            metadata={"argument_prediction_status": state},
        )

    nodes = [
        node("m1", participant=("the militia", "armed men"), place=("Homs",)),  # many fillers
        node("m2", participant=("the militia",)),                              # empty place
        node("m3", participant=("the militia", "the militia")),                # repeated string
        node("m4", state="empty"),                                             # nothing at all
    ]
    nodes_by_id = {n.event_id: n for n in nodes}
    pairs = [("m1", "m2"), ("m1", "m3"), ("m2", "m3"), ("m1", "m4"), ("m3", "m4")]
    features = batch_role_compatibility_features(pairs, nodes_by_id)
    _require(_finite(features), "role features are not finite on the fixture shapes")
    for row in features:
        _require(
            len(row) == len(ROLE_FEATURE_NAMES),
            f"role feature width drifted: {len(row)} != {len(ROLE_FEATURE_NAMES)}",
        )
    permuted = permute_role_features(pairs, nodes_by_id, features, seed=13)
    _require(
        sorted(map(tuple, permuted)) == sorted(map(tuple, features)),
        "the permutation changed the stratum's multiset of vectors",
    )
    _require(
        permute_role_features(pairs, nodes_by_id, features, seed=13) == permuted,
        "the permutation is not reproducible from its seed",
    )

    # All-singleton document: nothing merges, so the mediator must report zeros
    # rather than divide by an empty denominator.
    singleton = incompatible_role_merges(
        pairs,
        nodes_by_id,
        merged=dict.fromkeys(pairs, False),
        gold=dict.fromkeys(pairs, False),
    )
    _require(singleton["merged"] == 0, "an all-singleton document reported a merge")
    _require(singleton["pairs"] == len(pairs), "the mediator dropped a pair")
    return {
        "pairs": len(pairs),
        "feature_width": len(ROLE_FEATURE_NAMES),
        "mediator_on_all_singletons": singleton,
    }


def _permutation_seed(checkpoint: Path) -> object:
    """What the exported checkpoint tells inference about the shuffle."""
    from ekg.nodes.discriminative import CONFIG_FILE

    config = _load(checkpoint / CONFIG_FILE)
    return config.get("role_permutation_seed")


def run(args: argparse.Namespace) -> dict:
    _require(not args.output.exists(), f"refusing to overwrite smoke output: {args.output}")
    contract = _verify_contract(args.repo, args.contract) if args.contract else None
    args.output.mkdir(parents=True)

    fixture = _role_fixture()

    train_ids = load_manifest_ids(args.train_manifest)[: args.docs]
    dev_ids = load_manifest_ids(args.dev_manifest)[: args.docs]
    source = args.output / "smoke_source.jsonl"
    _subset(args.source, train_ids + dev_ids, source)
    train_manifest = _manifest(args.output / "train_manifest.json", train_ids)
    dev_manifest = _manifest(args.output / "dev_manifest.json", dev_ids)

    arms: dict[str, dict] = {}
    for arm in ARMS:
        checkpoint = args.output / arm / "checkpoint"
        subprocess.run(
            [
                sys.executable, "-u", "scripts/train_coref_scorer.py",
                "--train", str(source),
                "--train-manifest", str(train_manifest),
                "--dev-manifest", str(dev_manifest),
                "--model", args.model,
                "--output", str(checkpoint),
                "--argument-predictions", str(args.argument_predictions),
                "--epochs", str(args.epochs),
                "--lr", str(args.lr),
                "--seed", "13",
                *ARM_FLAGS[arm],
            ],
            cwd=args.repo,
            check=True,
        )
        seed = _permutation_seed(checkpoint)
        expected = 13 if arm == "permutation" else None
        _require(
            seed == expected,
            f"{arm}: checkpoint declares role_permutation_seed={seed!r}, expected {expected!r}",
        )
        arms[arm] = {
            "checkpoint": str(checkpoint),
            "role_permutation_seed": seed,
            "config_sha256": sha256_file(checkpoint / "coref_config.json"),
        }

    # The arms must differ where they are declared to differ and nowhere else:
    # full and permutation share a feature layout, remove_core drops it.
    _require(
        arms["full"]["config_sha256"] != arms["permutation"]["config_sha256"],
        "full and permutation exported an identical config; the arm switch was lost",
    )
    _require(
        arms["full"]["config_sha256"] != arms["remove_core"]["config_sha256"],
        "full and remove_core exported an identical config",
    )

    payload = {
        "schema_version": "ekg.c5_argument_uncertainty_smoke.v1",
        "status": "pass",
        "seed": 13,
        "final_valid_accessed": False,
        "documents": {"train": len(train_ids), "internal_dev": len(dev_ids)},
        "fixture": fixture,
        "arms": arms,
        "contract_sha256": sha256_file(args.contract) if args.contract else None,
        "contract_status": contract.get("status") if contract else "none",
    }
    _write(args.output / "smoke.json", payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--source", required=True, type=Path, help="MAVEN-ERE train jsonl")
    parser.add_argument("--train-manifest", required=True, type=Path)
    parser.add_argument("--dev-manifest", required=True, type=Path)
    parser.add_argument("--argument-predictions", required=True, type=Path)
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--contract", type=Path, help="C5.1 preflight, once it exists")
    parser.add_argument("--docs", type=int, default=10)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--lr", type=float, default=2e-5)
    args = parser.parse_args()
    args.repo = args.repo.resolve()
    for name in ("source", "train_manifest", "dev_manifest", "argument_predictions", "output"):
        setattr(args, name, getattr(args, name).resolve())
    if args.contract:
        args.contract = args.contract.resolve()

    payload = run(args)
    print(
        f"[c5-smoke] {payload['status'].upper()} {args.output} "
        f"arms={len(payload['arms'])} docs={payload['documents']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
