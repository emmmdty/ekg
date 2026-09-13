#!/usr/bin/env python
"""Freeze the immutable Ch6 evaluation unit (PHASE_E3 task E3.0).

Ch6's main table (`docs/EXPERIMENT_PLAN.md` §7.4) scores four external CGEP
methods, two trivial controls and this project's own built graph on **one** set
of queries.  Those arms are weeks apart and on two machines, so the unit has to
be a file with a digest rather than "whatever ``build_cgep`` returns that day":
if queries, candidates or labels drift between arms, every arm scored before the
drift has to be rerun (`docs/phases/PHASE_E3_graph_application.md`, stop
conditions).  This script writes that file and can re-verify it later.

The unit is a **local reconstruction** protocol, not a reproduction of SeDGPL's
released split: its ``MAVENSubWoRe.npy`` was never published, so the paper's
CGEP-MAVEN numbers are not same-data comparable.  The reconstruction rules and
what each of them is checked against live in ``ekg.succession.data.cgep``.

    uv run python scripts/freeze_e3_evaluation_unit.py --output runs/stages/E3/e3-v61-20260913
    uv run python scripts/freeze_e3_evaluation_unit.py --verify runs/stages/E3/e3-v61-20260913
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from ekg.core.stage_bundle import content_digest, id_digest, sha256_file, tree_sha256
from ekg.succession.data.cgep import CgepInstance, build_cgep, iter_documents

SCHEMA_VERSION = "ekg.e3_evaluation_unit.v1"

# Every file that decides which queries, candidates and labels come out. A change
# here does not by itself invalidate the unit -- the queries digest does -- but it
# is what a later mismatch gets traced through.
GENERATOR_FILES = (
    "src/ekg/succession/data/cgep.py",
    "src/ekg/relations/data/maven_ere.py",
    "scripts/freeze_e3_evaluation_unit.py",
)

# Measured on this unit and already published in `docs/results/PHASE_E.md`
# (gold .1802 > rewired .1185 > no_graph .0811, construction loss -.0218). New
# arms are only comparable with those rows while the unit digest is unchanged.
REFERENCE_RESULTS = "docs/results/PHASE_E.md (gold .1802 / predicted .1583, n=1908)"

_EXPECTED_INSTANCES = 1908


def _query_line(instance: CgepInstance) -> str:
    """One frozen problem: the six fields PHASE_E3 E3.0 pins per query."""
    head, subtype, tail = instance.query_edge
    return json.dumps(
        {
            "instance_id": instance.instance_id,
            "doc_id": instance.doc_id,
            "anchor": instance.nodes[head].node_id,
            "relation": subtype,
            "gold": instance.nodes[tail].node_id,
            "label": instance.label,
            "candidates": [node.node_id for node in instance.candidates],
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _render(instances: list[CgepInstance]) -> bytes:
    return ("\n".join(_query_line(i) for i in instances) + "\n").encode()


def _build(args: argparse.Namespace) -> tuple[list[CgepInstance], dict[str, float]]:
    return build_cgep(
        iter_documents([str(args.source)]),
        min_nodes=args.min_nodes,
        include_subevent=not args.no_subevent,
        n_candidates=args.candidates,
        seed=args.seed,
    )


def _manifest(args: argparse.Namespace, instances: list[CgepInstance], stats, payload) -> dict:
    candidates = {node.node_id for i in instances for node in i.candidates}
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "frozen",
        "protocol": (
            "local reconstruction of CGEP-MAVEN; SeDGPL's MAVENSubWoRe.npy was never "
            "released, so the paper's CGEP-MAVEN numbers are not same-data comparable "
            "and must not be entered into the Ch6 main table"
        ),
        "generator": {
            "params": {
                "seed": args.seed,
                "min_nodes": args.min_nodes,
                "include_subevent": not args.no_subevent,
                "n_candidates": args.candidates,
            },
            "files": {path: sha256_file(args.repo / path) for path in GENERATOR_FILES},
            "tree_sha256": tree_sha256(args.repo, [Path(p) for p in GENERATOR_FILES]),
        },
        "source": {"path": str(args.source), "sha256": sha256_file(args.source)},
        "unit": {
            "queries": "queries.jsonl",
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
            "query_id_digest": id_digest(i.instance_id for i in instances),
            "candidate_id_digest": id_digest(candidates),
        },
        "population": {
            "instances": len(instances),
            "documents_in_source": int(stats["documents"]),
            "documents_with_instances": len({i.doc_id for i in instances}),
            "ecgs": int(stats["ecgs"]),
            "candidates_per_instance": args.candidates,
            "distinct_candidate_nodes": len(candidates),
            "candidate_pool_nodes": int(stats["candidate_pool"]),
            "mean_distinct_answers": round(stats["distinct_answers"], 4),
        },
        "reference_results": REFERENCE_RESULTS,
        "final_valid_ledger": (
            "MAVEN-ERE public valid is read as Ch6's held-out evaluation split: event "
            "mentions, causal/subevent gold edges and document text. No model or "
            "method choice is made from it -- E3.3 trains each consumer once on the "
            "pre-registered training graph and reuses that checkpoint across arms."
        ),
    }


def freeze(args: argparse.Namespace) -> dict:
    instances, stats = _build(args)
    if args.expect_instances and len(instances) != args.expect_instances:
        raise SystemExit(
            f"instance count drifted: {len(instances)} != {args.expect_instances}. "
            "PHASE_E3 E3.0 requires the change be frozen and disclosed before any "
            "consumer result is read; pass --expect-instances to accept it."
        )
    payload = _render(instances)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "queries.jsonl").write_bytes(payload)
    manifest = _manifest(args, instances, stats, payload)
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def verify(args: argparse.Namespace) -> tuple[dict, list[str]]:
    """Rebuild from source and report every axis that moved away from the freeze."""
    manifest = json.loads((args.verify / "manifest.json").read_text(encoding="utf-8"))
    params = manifest["generator"]["params"]
    args.seed = params["seed"]
    args.min_nodes = params["min_nodes"]
    args.no_subevent = not params["include_subevent"]
    args.candidates = params["n_candidates"]
    args.source = Path(manifest["source"]["path"])

    drift: list[str] = []
    stored = sha256_file(args.source)
    if stored != manifest["source"]["sha256"]:
        drift.append(f"source sha256 {stored} != {manifest['source']['sha256']}")

    # Provenance, not validity: the generator may be edited as long as the unit
    # it produces is unchanged, so this is reported separately from a drifted unit.
    files = {path: sha256_file(args.repo / path) for path in manifest["generator"]["files"]}
    if content_digest(files) != content_digest(manifest["generator"]["files"]):
        changed = [p for p, h in files.items() if manifest["generator"]["files"].get(p) != h]
        drift.append(f"generator files changed (provenance only): {', '.join(sorted(changed))}")

    instances, _ = _build(args)
    rebuilt = hashlib.sha256(_render(instances)).hexdigest()
    on_disk = sha256_file(args.verify / "queries.jsonl")
    if on_disk != manifest["unit"]["sha256"]:
        drift.append(f"queries.jsonl on disk {on_disk} != frozen {manifest['unit']['sha256']}")
    if rebuilt != manifest["unit"]["sha256"]:
        drift.append(f"rebuild from source {rebuilt} != frozen {manifest['unit']['sha256']}")
    return manifest, drift


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument(
        "--source", type=Path, default=Path("data/processed/maven_ere/valid.jsonl")
    )
    parser.add_argument("--seed", type=int, default=209, help="SeDGPL's seed")
    parser.add_argument("--min-nodes", type=int, default=4)
    parser.add_argument("--no-subevent", action="store_true", help="causal edges only")
    parser.add_argument("--candidates", type=int, default=512)
    parser.add_argument(
        "--expect-instances", type=int, default=_EXPECTED_INSTANCES,
        help="fail unless the rebuild yields this many instances; 0 disables",
    )
    parser.add_argument("--output", type=Path, help="directory to freeze into")
    parser.add_argument("--verify", type=Path, help="re-check an existing frozen unit")
    args = parser.parse_args()
    if (args.output is None) == (args.verify is None):
        parser.error("pass exactly one of --output or --verify")
    args.repo = args.repo.resolve()

    if args.verify is not None:
        manifest, drift = verify(args)
        for line in drift:
            print(f"[e3-unit] DRIFT {line}")
        blocking = [line for line in drift if "provenance only" not in line]
        print(
            f"[e3-unit] {'FAIL' if blocking else 'PASS'} {args.verify} "
            f"instances={manifest['population']['instances']} "
            f"unit_sha256={manifest['unit']['sha256']}"
        )
        return 1 if blocking else 0

    manifest = freeze(args)
    print(
        f"[e3-unit] FROZEN {args.output} "
        f"instances={manifest['population']['instances']} "
        f"documents={manifest['population']['documents_with_instances']} "
        f"unit_sha256={manifest['unit']['sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
