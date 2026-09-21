#!/usr/bin/env python
"""Rewrite a frozen D4 sidecar with gold causal labels, for the oracle row only.

The failed cycle passed messages over edges that were 22.4% correct. The single
cheapest way to tell "the edges were too noisy" apart from "the mechanism does
nothing" is to hand the *same* pipeline a perfect graph and see whether the gain
appears. That row is explicitly **non-deployable**: the phase contract gives
oracle no arm, and its numbers may only appear as a diagnostic line in
`docs/results/PHASE_R1.md`, never in a promotion gate.

Every row of the source sidecar is kept in place — same documents, same ordered
candidate pairs, same order — so the only thing that changes is which pairs come
out of `decide_edges` and how confident they are. Those two move together by
construction: an oracle both knows the right edges and is certain about them,
and the write-up has to say so rather than pretend only one variable moved.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

from ekg.core.protocol import load_manifest_ids
from ekg.core.schema import RelationType
from ekg.core.stage_bundle import sha256_file
from ekg.relations.data.maven_ere import load_maven_ere
from ekg.relations.pairs import gold_pair_labels

# Strictly positive and summing to one: `decide_edges` rejects zeros, and the
# frozen cost-aware rule must still land on the gold class for every gold pair.
CERTAIN = 0.998
RESIDUAL = 0.001

FIELD = {"CAUSE": "p_cause", "PRECONDITION": "p_precondition", "NONE": "p_none"}


def build(
    *, source: Path, manifest: Path, relation_source: Path, output: Path
) -> dict:
    if output.exists():
        raise FileExistsError(f"refusing to overwrite: {output}")
    wanted = set(load_manifest_ids(manifest))
    gold = {
        doc.doc_id: gold_pair_labels(
            doc, family=RelationType.CAUSAL, expand_event_relations=True
        )
        for doc in load_maven_ere(relation_source)
        if doc.doc_id in wanted
    }
    missing = wanted - set(gold)
    if missing:
        raise ValueError(f"{len(missing)} manifest documents are absent from the relations")

    counts = {"NONE": 0, "CAUSE": 0, "PRECONDITION": 0}
    output.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=output.parent,
        prefix=f".{output.name}.",
        suffix=".tmp",
        delete=False,
    )
    temporary = Path(handle.name)
    rows = 0
    try:
        with handle, source.open(encoding="utf-8") as reader:
            for line in reader:
                row = json.loads(line)
                doc_id = row["doc_id"]
                if doc_id not in gold:
                    raise ValueError(f"{doc_id} is outside the manifest")
                label = gold[doc_id].get(
                    (row["head_mention_id"], row["tail_mention_id"]), "NONE"
                )
                if label not in FIELD:
                    raise ValueError(f"unexpected gold causal subtype {label!r}")
                counts[label] += 1
                for name, field in FIELD.items():
                    row[field] = CERTAIN if name == label else RESIDUAL
                handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
                rows += 1
        os.replace(temporary, output)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise

    return {
        "schema_version": "ekg.d4_gold_sidecar.v1",
        "deployable": False,
        "role": "oracle diagnostic row; never a promotion-gate arm",
        "source": {"path": str(source), "sha256": sha256_file(source)},
        "manifest": {"path": str(manifest), "sha256": sha256_file(manifest)},
        "relation_source": {
            "path": str(relation_source),
            "sha256": sha256_file(relation_source),
        },
        "output": {"path": str(output), "sha256": sha256_file(output)},
        "rows": rows,
        "gold_label_counts": counts,
        "certain_probability": CERTAIN,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path, help="frozen sidecar to mirror")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--relation-source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(
        json.dumps(
            build(
                source=args.source.resolve(),
                manifest=args.manifest.resolve(),
                relation_source=args.relation_source.resolve(),
                output=args.output.resolve(),
            ),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
