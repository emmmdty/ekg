#!/usr/bin/env python
"""Train the discriminative supervised relation extractor on MAVEN-ERE (server / CUDA).

Builds pair-classification rows from gold mentions (`relations.pairs.pair_examples`),
downsamples the dominant NONE class, and trains a RoBERTa encoder plus a registered
pair head with a registered relation objective. Saves encoder, tokenizer and head
to `--output`, which `configs/relations/supervised.yaml` then loads.

This is the *discriminative* trainer — not `train_relation_extractor.py`, which is
the retained generative LoRA baseline.

Data preparation (`build_training_rows` / `downsample_negatives` / `class_weights`) is
pure Python and unit-tested on CPU; training needs the `llm` extra + a GPU:

    uv run --extra llm python scripts/train_supervised_relations.py \
        --train data/processed/maven_ere/train.jsonl \
        --model roberta-base \
        --output runs/relations/supervised_maven

`train_smoke.jsonl` / `valid_smoke.jsonl` are the small subsets for a quick check.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import sys
from pathlib import Path

from ekg.core.stage_bundle import StageBundleError, is_sha256, validate_stage_bundle
from ekg.relations.balance import (
    ADAPTIVE_WORKPOINT,
    NONE_INDEX,
    NORMALIZED_RISK,
    FamilyRiskNormalizer,
    WorkPointController,
    position_none_offsets,
    workpoint_key,
)
from ekg.relations.balance import (
    ALL_COMPONENTS as BALANCE_COMPONENTS,
)
from ekg.relations.balance import (
    CONFIG_FILE as BALANCE_CONFIG_FILE,
)
from ekg.relations.balance import validate_components as validate_balance_components
from ekg.relations.data.maven_ere import load_maven_ere
from ekg.relations.extractor.supervised import FAMILY_SUBTYPES
from ekg.relations.maven_ere_official import frozen_candidate_protocol, records_by_id
from ekg.relations.objective_registry import (
    ADAPTIVE_THRESHOLD_OBJECTIVE,
    CROSS_ENTROPY_OBJECTIVE,
    RELATION_OBJECTIVE_NAMES,
)
from ekg.relations.pair_heads import (
    LINEAR_HEAD,
    PAIR_HEAD_CONFIG_FILE,
    PAIR_HEAD_NAMES,
    PROTOTYPE_DEPENDENCY_HEAD,
    PROTOTYPE_HEAD,
)
from ekg.relations.pairs import POSITION_BUCKETS, PairExample, pair_examples
from ekg.relations.prototype import (
    prototype_dependency_matrix,
    select_prototype_support,
)

# Official MAVEN-ERE marks unscoreable family/pair combinations with -100
# (`joint/src/data.py::get_relation_labels`), which is also torch's default.
_IGNORE_INDEX = -100


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def validate_v6_protocol_inputs(
    *,
    repo_root: Path,
    train_path: Path,
    train_manifest: Path,
    dev_manifest: Path,
    protocol_root: Path,
    expected_p1_protocol_sha256: str,
) -> dict:
    """Bind an A3 run to P1's source, two allowed splits, and label universe.

    This intentionally runs before importing torch. A path with the right IDs but
    drifted bytes, a swapped final-valid manifest, or a different event-to-mention
    expansion must fail without spending GPU time.
    """
    repo_root = repo_root.resolve()
    protocol_root = protocol_root.resolve()
    train_path = train_path.resolve()
    train_manifest = train_manifest.resolve()
    dev_manifest = dev_manifest.resolve()
    registry_path = protocol_root / "registry.json"
    candidate_path = protocol_root / "ch2_candidate_protocol.json"
    registry = _load_json(registry_path)
    if registry.get("protocol") != "v6":
        raise ValueError("protocol registry is not v6")
    if registry.get("global_protocol_status") != "pass":
        raise ValueError("P1 global protocol status is not pass")
    if registry.get("a3_entry_status") != "pass":
        raise ValueError("P1 A3 entry status is not pass")
    if not registry.get("p1_bundle_id") or not registry.get("p1_bundle_protocol_sha256"):
        raise ValueError("protocol registry does not identify a validated P1 bundle")
    if not is_sha256(expected_p1_protocol_sha256):
        raise ValueError("expected P1 protocol digest is not a SHA-256 hex string")
    if registry["p1_bundle_protocol_sha256"] != expected_p1_protocol_sha256:
        raise ValueError("registry P1 protocol digest differs from the command trust root")
    p1_bundle = repo_root / "runs/stages/P1" / registry["p1_bundle_id"]
    try:
        validate_stage_bundle(
            p1_bundle,
            evidence_root=repo_root,
            expected_protocol_sha256=expected_p1_protocol_sha256,
            known_upstream_bundle_ids=set(),
        )
    except StageBundleError as exc:
        raise ValueError(f"P1 stage bundle validation failed: {exc}") from exc

    source_rel = "data/processed/maven_ere/train.jsonl"
    expected_source = (repo_root / source_rel).resolve()
    if train_path != expected_source:
        raise ValueError(f"v6 --train must be the registered source {expected_source}")
    source_hash = sha256_file(train_path)
    if source_hash != registry.get("source_sha256", {}).get(source_rel):
        raise ValueError("registered MAVEN-ERE train source hash mismatch")

    expected_manifests = {
        "train": (protocol_root / "manifests/maven_ere_train.json").resolve(),
        "internal-dev": (
            protocol_root / "manifests/maven_ere_internal-dev.json"
        ).resolve(),
    }
    supplied = {"train": train_manifest, "internal-dev": dev_manifest}
    manifest_hashes: dict[str, str] = {}
    manifest_payloads: dict[str, dict] = {}
    for role, path in supplied.items():
        expected = expected_manifests[role]
        if path != expected:
            raise ValueError(f"v6 {role} manifest must be {expected}")
        relative = path.relative_to(protocol_root).as_posix()
        actual_hash = sha256_file(path)
        if actual_hash != registry.get("manifest_sha256", {}).get(relative):
            raise ValueError(f"registered {role} manifest hash mismatch")
        payload = _load_json(path)
        required = {
            "dataset": "maven_ere",
            "split_role": role,
            "source_path": source_rel,
            "source_sha256": source_hash,
        }
        for key, expected_value in required.items():
            if payload.get(key) != expected_value:
                raise ValueError(
                    f"{role} manifest {key} mismatch: "
                    f"expected {expected_value!r}, got {payload.get(key)!r}"
                )
        ids = load_manifest_ids(path)
        if payload.get("doc_count") != len(ids):
            raise ValueError(f"{role} manifest doc_count does not match doc_ids")
        manifest_hashes[role] = actual_hash
        manifest_payloads[role] = payload

    candidate_hash = sha256_file(candidate_path)
    if candidate_hash != registry.get("candidate_protocol_sha256"):
        raise ValueError("registered Ch2 candidate protocol hash mismatch")
    frozen_candidates = _load_json(candidate_path)
    raw_records = [
        json.loads(line)
        for line in train_path.read_text(encoding="utf-8").splitlines()
        if line
    ]
    raw_by_id = records_by_id(raw_records, source=str(train_path))
    selected_ids: set[str] = set()
    summaries: dict[str, dict] = {}
    for role, payload in manifest_payloads.items():
        ids = payload["doc_ids"]
        missing = set(ids) - raw_by_id.keys()
        if missing:
            raise ValueError(f"{role} manifest has {len(missing)} IDs absent from source")
        overlap = selected_ids & set(ids)
        if overlap:
            raise ValueError(f"v6 train/internal-dev overlap on {len(overlap)} documents")
        selected_ids.update(ids)
        summary = frozen_candidate_protocol(raw_by_id[item] for item in ids)
        if summary != frozen_candidates.get(role):
            raise ValueError(f"{role} candidate or expanded-label population drift")
        summaries[role] = summary
    if selected_ids != set(raw_by_id):
        raise ValueError(
            "v6 train/internal-dev manifests do not exactly partition the registered source"
        )

    return {
        "schema_version": "ekg.a3_protocol_binding.v1",
        "p1_bundle_id": registry["p1_bundle_id"],
        "p1_bundle_protocol_sha256": expected_p1_protocol_sha256,
        "hashes": {
            "registry": sha256_file(registry_path),
            "candidate_protocol": candidate_hash,
            "train_source": source_hash,
            "train_manifest": manifest_hashes["train"],
            "internal_dev_manifest": manifest_hashes["internal-dev"],
            "trainer": sha256_file(Path(__file__).resolve()),
        },
        "candidate_summaries": summaries,
        "split_counts": {
            role: len(payload["doc_ids"]) for role, payload in manifest_payloads.items()
        },
        "final_valid_accessed": False,
    }


def _checkpoint_hashes(output: Path) -> dict[str, str]:
    return {
        path.relative_to(output).as_posix(): sha256_file(path)
        for path in sorted(output.rglob("*"))
        if path.is_file() and path.name != "run_metadata.json"
    }


def _write_run_metadata(output: Path, payload: dict) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output / "run_metadata.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def build_training_rows(
    docs,
    max_distance: int | None = None,
    *,
    expand_event_relations: bool = False,
) -> list[PairExample]:
    """Every document's labelled candidate universe, flattened.

    `pair_examples` already carries exactly what a pair classifier trains on
    (endpoint ids + one gold subtype per family, empty labels = negative), and it is
    the same universe evaluation scores against — so the rows *are* its output.
    """
    rows: list[PairExample] = []
    for doc in docs:
        rows.extend(
            pair_examples(
                doc,
                max_distance,
                expand_event_relations=expand_event_relations,
            )
        )
    return rows


def load_manifest_ids(path: Path) -> list[str]:
    """Load and validate the explicit document IDs frozen by P1."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    ids = payload.get("doc_ids")
    if not isinstance(ids, list) or not ids or not all(isinstance(item, str) for item in ids):
        raise ValueError(f"{path} must contain a non-empty string list at doc_ids")
    if len(ids) != len(set(ids)):
        raise ValueError(f"{path} contains duplicate doc_ids")
    return ids


def split_docs_by_manifests(docs, train_manifest: Path, dev_manifest: Path):
    """Split documents by explicit P1 manifests and reject omission or overlap."""
    docs = list(docs)
    docs_by_id = {doc.doc_id: doc for doc in docs}
    if len(docs_by_id) != len(docs):
        raise ValueError("training source contains duplicate document IDs")
    train_ids = load_manifest_ids(train_manifest)
    dev_ids = load_manifest_ids(dev_manifest)
    overlap = set(train_ids) & set(dev_ids)
    if overlap:
        raise ValueError(f"train/dev manifests overlap on {len(overlap)} document IDs")
    selected = set(train_ids) | set(dev_ids)
    missing = selected - docs_by_id.keys()
    omitted = docs_by_id.keys() - selected
    if missing or omitted:
        raise ValueError(
            "manifest/source ID mismatch: "
            f"missing_from_source={len(missing)} omitted_from_manifests={len(omitted)}"
        )
    return [docs_by_id[item] for item in train_ids], [docs_by_id[item] for item in dev_ids]


def downsample_negatives(
    rows: list[PairExample], ratio: float, seed: int = 13
) -> list[PairExample]:
    """Keep every positive pair, subsample negatives to `ratio` per positive.

    Deterministic for a given seed. Raises when there is no positive at all:
    training on NONE only silently learns the majority class — exactly the failure
    behind the 0.4% causal recall — so this fails loudly instead of hiding it.

    ``ratio=inf`` keeps every negative, i.e. turns downsampling off. That is what
    the official MAVEN-ERE baseline does: its `Document.get_labels` enumerates all
    ``n^2 - n`` ordered mention pairs and labels the rest NONE, with no sampling
    anywhere (`THU-KEG/MAVEN-ERE/causal/src/data.py`). Ours defaulted to 30:1 and
    *also* applied inverse-frequency class weights — two corrections pushing the
    same way, which is the leading suspect for our collapsed precision.
    """
    if math.isinf(ratio):
        if not any(r.labels for r in rows):
            raise ValueError("no positive pair in the training rows")
        return list(rows)
    positives = [r for r in rows if r.labels]
    negatives = [r for r in rows if not r.labels]
    if not positives:
        raise ValueError("no positive pairs in training rows -- refusing to train on NONE only")
    keep = min(len(negatives), int(len(positives) * ratio))
    return positives + random.Random(seed).sample(negatives, keep)


def class_weights(
    rows: list[PairExample], alpha: float | dict[str, float] = 1.0
) -> dict[str, list[float]]:
    """Inverse-frequency weight per label per family, tempered by `alpha`.

    The weight is `(total / (k * count)) ** alpha`: alpha=1 is plain inverse
    frequency, alpha=0 is uniform (off), alpha=0.5 the usual middle ground. `alpha`
    may be a single value (all families) or a per-family dict.

    Tempering matters because the families differ in sparsity by ~39:3.4:1
    (temporal:causal:subevent gold), so a *per-family* alpha is the right control:
    the dense families (temporal) want a low alpha or they over-predict, the sparse
    ones (causal) want a higher alpha or their recall/F1 stays capped. A single
    global setting has to compromise across that whole range.
    """
    weights: dict[str, list[float]] = {}
    for family, subtypes in FAMILY_SUBTYPES.items():
        a = alpha[family] if isinstance(alpha, dict) else alpha
        index = {s: i for i, s in enumerate(subtypes)}
        counts = [0] * len(subtypes)
        for row in rows:
            # Pairs the official protocol does not score for this family (a TIMEX
            # endpoint under causal/subevent) are not negatives — counting them
            # would distort the inverse-frequency weights by ~700k phantom NONEs.
            if family in row.ignored_families:
                continue
            # No gold label for this family = the negative class. An *unknown*
            # subtype must not be silently folded into NONE — that is how positives
            # go missing — so the lookup raises instead.
            counts[index[row.labels.get(family, "NONE")]] += 1
        total = sum(counts)
        weights[family] = [
            (total / (len(subtypes) * c)) ** a if c else 0.0 for c in counts
        ]
    return weights


def parse_weight_alpha(spec: str) -> float | dict[str, float]:
    """Parse `--weight-alpha`: a bare float, or `causal=0.7,temporal=0.25,...`.

    A per-family spec must name every family so no default is silently applied to
    an unlisted one (an unnamed family would otherwise train with a surprise alpha).
    """
    if "=" not in spec:
        return float(spec)
    per = dict(item.split("=", 1) for item in spec.split(","))
    parsed = {fam: float(per[fam]) for fam in FAMILY_SUBTYPES if fam in per}
    missing = set(FAMILY_SUBTYPES) - parsed.keys()
    extra = set(per) - set(FAMILY_SUBTYPES)
    if missing or extra:
        raise ValueError(
            f"per-family --weight-alpha must name exactly {sorted(FAMILY_SUBTYPES)}; "
            f"missing={sorted(missing)} unknown={sorted(extra)}"
        )
    return parsed


def parse_family_loss_rates(spec: str) -> dict[str, float]:
    """Parse one positive loss multiplier for every relation family."""
    items = [item.split("=", 1) for item in spec.split(",")]
    if any(len(item) != 2 for item in items):
        raise ValueError("--family-loss-rates entries must use family=value")
    per = dict(items)
    if len(per) != len(items):
        raise ValueError("--family-loss-rates contains a duplicate family")
    missing = set(FAMILY_SUBTYPES) - per.keys()
    extra = set(per) - set(FAMILY_SUBTYPES)
    if missing or extra:
        raise ValueError(
            f"--family-loss-rates must name exactly {sorted(FAMILY_SUBTYPES)}; "
            f"missing={sorted(missing)} unknown={sorted(extra)}"
        )
    rates = {family: float(per[family]) for family in FAMILY_SUBTYPES}
    if any(rate <= 0.0 for rate in rates.values()):
        raise ValueError("--family-loss-rates values must all be positive")
    return rates


def validate_confirmation_families(families: list[str]) -> tuple[str, ...]:
    """A3's frozen candidate protocol covers all three relation families.

    Temporal is in scope because the official baselines score it (with TIMEX
    endpoints) and MAVEN-ERE supplies the gold; excluding it would report a
    narrower task than the methods we compare against.
    """
    if len(families) != len(set(families)):
        raise ValueError("--families contains duplicates")
    selected = tuple(families)
    if set(selected) != {"causal", "subevent", "temporal"}:
        raise ValueError(
            "v6 confirmation requires exactly --families causal subevent temporal; "
            "the frozen A3 protocol scores all three"
        )
    return selected


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--train", required=True, type=Path, help="MAVEN-ERE train jsonl")
    parser.add_argument("--model", required=True, type=str, help="base RoBERTa (name or path)")
    parser.add_argument("--output", required=True, type=Path, help="checkpoint directory")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument(
        "--neg-ratio", type=float, default=3.0,
        help="negatives per positive; `inf` keeps every negative, which is what the "
             "official MAVEN-ERE baseline does (no sampling at all)",
    )
    parser.add_argument(
        "--weight-alpha",
        type=str,
        default="1.0",
        help="class-imbalance dial (PHASE_A ablation): CE weight = inverse_freq ** alpha. "
        "A bare float applies to all families (1.0 = plain inverse, 0.0 = off, 0.5 = middle), "
        "or per-family e.g. 'causal=0.7,temporal=0.25,subevent=0.5'.",
    )
    parser.add_argument(
        "--relation-objective",
        choices=RELATION_OBJECTIVE_NAMES,
        default=CROSS_ENTROPY_OBJECTIVE,
        help="registered training objective. adaptive_threshold is the official "
        "ATLOP loss with NONE as the pair-dependent threshold and requires "
        "--weight-alpha 0.0",
    )
    parser.add_argument("--max-distance", type=int, default=None, help="None = document-level")
    parser.add_argument(
        "--max-length", type=int, default=512, help="512 covers the longest sentence (322 tokens)"
    )
    parser.add_argument(
        "--head-lr", type=float, default=None,
        help="separate learning rate for the pair heads; the official baseline runs the "
             "encoder at 1e-5 and the scorer at 1e-4. Default None keeps one rate for "
             "everything. ⚠️ Phase C diverged at head lr 1e-3 -- that is 10x the official "
             "value, not evidence against 1e-4",
    )
    parser.add_argument(
        "--warmup-steps", type=int, default=0,
        help="linear warmup on the encoder rate (the official baseline uses 200); 0 = off",
    )
    parser.add_argument(
        "--dev-metric", choices=("micro", "macro"), default="micro",
        help="how --dev-docs scores an epoch. micro pools all families and is "
             "dominated by temporal (~39x subevent's pair count); macro weights the "
             "three families equally. Default stays micro so existing runs reproduce",
    )
    parser.add_argument(
        "--accum-steps", type=int, default=1,
        help="accumulate gradients over N documents before stepping. The official "
             "baseline batches 8 documents; ours updates per document (= batch 1), "
             "which both adds gradient noise and makes --warmup-steps mean 8x fewer "
             "documents than the official 200",
    )
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument(
        "--dev-docs", type=int, default=0,
        help="hold out this many TRAIN docs as dev and keep the best-scoring epoch "
             "(the official baseline selects on dev; 0 = off, keep the last epoch). "
             "Never carved from valid -- selecting and reporting on the same split "
             "would bias the reported number",
    )
    parser.add_argument(
        "--train-manifest",
        type=Path,
        help="P1 manifest for training doc IDs; must be paired with --dev-manifest",
    )
    parser.add_argument(
        "--dev-manifest",
        type=Path,
        help="P1 manifest for internal-dev IDs; must be paired with --train-manifest",
    )
    parser.add_argument(
        "--protocol-root",
        type=Path,
        help="P1 v6 protocol directory; required with explicit manifests",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="repository root used to resolve the P1-registered source path",
    )
    parser.add_argument(
        "--p1-protocol-sha256",
        help="external trust-root hash for the registry-selected P1 protocol.json",
    )
    parser.add_argument(
        "--official-mention-expansion",
        action="store_true",
        help="expand event-level relations across all cluster mention pairs, matching "
        "the official MAVEN-ERE causal/joint candidate labels; required for v6",
    )
    parser.add_argument(
        "--families",
        nargs="+",
        choices=tuple(FAMILY_SUBTYPES),
        default=list(FAMILY_SUBTYPES),
        help="relation heads included in loss and checkpoint selection",
    )
    parser.add_argument(
        "--family-loss-rates",
        default="temporal=1,causal=1,subevent=1",
        help="positive per-family loss multipliers; official joint recipe uses "
             "temporal=2,causal=4,subevent=4",
    )
    parser.add_argument(
        "--save-best-by-family",
        action="store_true",
        help="also retain the encoder+heads snapshot that maximizes each family's dev F1",
    )
    parser.add_argument(
        "--coref-aux-rate",
        type=float,
        default=0.0,
        help="auxiliary coreference loss multiplier; official joint recipe uses 0.4",
    )
    parser.add_argument(
        "--pair-head",
        choices=PAIR_HEAD_NAMES,
        default=LINEAR_HEAD,
        help="registered pair-scoring geometry; prototype arms use train-only support",
    )
    parser.add_argument(
        "--balance-components",
        nargs="*",
        default=[],
        choices=list(BALANCE_COMPONENTS),
        help=(
            "adaptive relation-family balancing (A3.2); empty = the reproduction base's "
            "plain sum of class-weighted family losses. "
            "normalized_risk divides each family by an EMA of its own loss scale; "
            "adaptive_workpoint feeds each family x same/cross-sentence group's measured "
            "F1-optimal NONE-logit offset back into the training loss "
            "(inference stays a plain argmax)"
        ),
    )
    args = parser.parse_args()
    balance_components = validate_balance_components(args.balance_components)
    try:
        family_loss_rates = parse_family_loss_rates(args.family_loss_rates)
    except (TypeError, ValueError) as exc:
        parser.error(str(exc))
    if args.coref_aux_rate < 0.0:
        parser.error("--coref-aux-rate must be non-negative")
    if args.coref_aux_rate and args.pair_head != LINEAR_HEAD:
        parser.error("--coref-aux-rate currently requires the linear pair head")

    objective_alpha = parse_weight_alpha(args.weight_alpha)
    if args.relation_objective == ADAPTIVE_THRESHOLD_OBJECTIVE:
        if objective_alpha != 0.0:
            parser.error("adaptive_threshold requires --weight-alpha 0.0")
        if args.pair_head != LINEAR_HEAD:
            parser.error("adaptive_threshold requires the linear pair head")
        if balance_components:
            parser.error("adaptive_threshold cannot be mixed with balance components")

    if args.pair_head != LINEAR_HEAD and balance_components:
        parser.error("prototype pair heads cannot be mixed with work-point components")

    if bool(args.train_manifest) != bool(args.dev_manifest):
        parser.error("--train-manifest and --dev-manifest must be provided together")
    if args.train_manifest and args.dev_docs:
        parser.error("--dev-docs cannot be combined with explicit manifests")
    if bool(args.protocol_root) != bool(args.train_manifest):
        parser.error("--protocol-root and both manifests must be provided together")
    if bool(args.p1_protocol_sha256) != bool(args.train_manifest):
        parser.error("--p1-protocol-sha256 and both manifests must be provided together")
    if args.train_manifest and not args.official_mention_expansion:
        parser.error("v6 manifest runs require --official-mention-expansion")

    selected_families = tuple(args.families)
    if args.train_manifest:
        try:
            selected_families = validate_confirmation_families(args.families)
        except ValueError as exc:
            parser.error(str(exc))

    protocol_binding = None
    if args.train_manifest:
        try:
            protocol_binding = validate_v6_protocol_inputs(
                repo_root=args.repo_root,
                train_path=args.train,
                train_manifest=args.train_manifest,
                dev_manifest=args.dev_manifest,
                protocol_root=args.protocol_root,
                expected_p1_protocol_sha256=args.p1_protocol_sha256,
            )
        except ValueError as exc:
            parser.error(str(exc))
        if args.output.exists() and any(args.output.iterdir()):
            parser.error(
                f"v6 confirmation output directory is not empty: {args.output}; "
                "use a new immutable run directory"
            )

    run_metadata = {
        "schema_version": "ekg.relation_training_run.v1",
        "status": "incomplete",
        "confirmation_eligible": protocol_binding is not None,
        "command_argv": list(sys.argv),
        "working_directory": str(Path.cwd().resolve()),
        "protocol_binding": protocol_binding,
        "final_valid_accessed": False,
        "configuration": {
            "train": str(args.train.resolve()),
            "model": args.model,
            "epochs": args.epochs,
            "lr": args.lr,
            "head_lr": args.head_lr,
            "neg_ratio": "inf" if math.isinf(args.neg_ratio) else args.neg_ratio,
            "weight_alpha": args.weight_alpha,
            "relation_objective": args.relation_objective,
            "max_distance": args.max_distance,
            "max_length": args.max_length,
            "warmup_steps": args.warmup_steps,
            "dev_metric": args.dev_metric,
            "accum_steps": args.accum_steps,
            "seed": args.seed,
            "official_mention_expansion": args.official_mention_expansion,
            "families": list(selected_families),
            "family_loss_rates": family_loss_rates,
            "save_best_by_family": args.save_best_by_family,
            "coref_aux_rate": args.coref_aux_rate,
            "pair_head": args.pair_head,
            "balance_components": list(balance_components),
        },
    }
    _write_run_metadata(args.output, run_metadata)

    # torch-only imports stay inside main so the data helpers above import on CPU.
    import torch
    from transformers import AutoModel, AutoTokenizer

    from ekg.relations.extractor.supervised import (
        _pair_features,
        distance_bucket,
        encode_trigger_reps,
    )
    from ekg.relations.objective_registry import build_relation_objective
    from ekg.relations.pair_heads import build_pair_head

    # TIMEX nodes are required whenever temporal is scored: 39% of gold temporal
    # relations have a TIMEX endpoint and are otherwise unrepresentable.
    docs = list(load_maven_ere(args.train, include_timex="temporal" in selected_families))
    if args.train_manifest:
        train_docs, dev_docs = split_docs_by_manifests(
            docs, args.train_manifest, args.dev_manifest
        )
    else:
        legacy_docs = list(docs)
        random.Random(args.seed).shuffle(legacy_docs)
        dev_docs = legacy_docs[: args.dev_docs] if args.dev_docs else []
        train_docs = legacy_docs[args.dev_docs :] if args.dev_docs else legacy_docs
        if args.dev_docs:
            print(
                "[train] WARNING: runtime --dev-docs split is historical/exploratory; "
                "v6 requires explicit manifests",
                flush=True,
            )

    train_rows_full = build_training_rows(
        train_docs,
        args.max_distance,
        expand_event_relations=args.official_mention_expansion,
    )
    rows = downsample_negatives(
        train_rows_full, args.neg_ratio, args.seed
    )
    dev_rows = build_training_rows(
        dev_docs,
        args.max_distance,
        expand_event_relations=args.official_mention_expansion,
    )
    alpha = objective_alpha
    weights = None if alpha == 0.0 else class_weights(rows, alpha)
    docs_by_id = {d.doc_id: d for d in docs}
    rows_by_doc: dict[str, list[PairExample]] = {}
    for row in rows:
        rows_by_doc.setdefault(row.doc_id, []).append(row)
    for row in dev_rows:
        rows_by_doc.setdefault(row.doc_id, []).append(row)
    kept = "all (no downsampling)" if math.isinf(args.neg_ratio) else f"{args.neg_ratio}:1"
    print(
        f"[train] {len(docs)} docs, {len(rows)} rows (negatives {kept}), "
        f"weight_alpha={args.weight_alpha}, lr={args.lr}, head_lr={args.head_lr}, "
        f"warmup={args.warmup_steps}, accum={args.accum_steps}, "
        f"max_length={args.max_length}",
        flush=True,
    )

    device = "cuda" if torch.cuda.is_available() else "cpu"
    run_metadata["device"] = device
    _write_run_metadata(args.output, run_metadata)
    torch.manual_seed(args.seed)
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    encoder = AutoModel.from_pretrained(args.model).to(device)
    counts = {fam: len(subs) for fam, subs in FAMILY_SUBTYPES.items()}
    heads = build_pair_head(
        args.pair_head,
        hidden_size=encoder.config.hidden_size,
        subtype_counts=counts,
    ).to(device)
    coref_aux_head = (
        build_pair_head(
            LINEAR_HEAD,
            hidden_size=encoder.config.hidden_size,
            subtype_counts={"coreference": 2},
        ).to(device)
        if args.coref_aux_rate
        else None
    )
    prototype_families = tuple(counts)
    if args.pair_head == PROTOTYPE_DEPENDENCY_HEAD:
        heads.set_dependency(
            prototype_dependency_matrix(
                train_rows_full,
                FAMILY_SUBTYPES,
                prototype_families,
            )
        )

    if args.pair_head in {PROTOTYPE_HEAD, PROTOTYPE_DEPENDENCY_HEAD}:
        assignments = select_prototype_support(
            train_rows_full,
            FAMILY_SUBTYPES,
            prototype_families,
            seed=args.seed,
        )
        row_by_key = {
            (row.doc_id, row.head_id, row.tail_id): row for row in train_rows_full
        }
        selected_by_doc: dict[str, list[PairExample]] = {}
        for key in assignments:
            selected_by_doc.setdefault(key[0], []).append(row_by_key[key])
        support: dict[str, list[list[torch.Tensor]]] = {
            family: [[] for _ in FAMILY_SUBTYPES[family]]
            for family in prototype_families
        }
        encoder.eval()
        heads.eval()
        with torch.no_grad():
            for doc_id, doc_rows in selected_by_doc.items():
                doc = docs_by_id[doc_id]
                embs = encode_trigger_reps(
                    encoder, tokenizer, doc.nodes, doc.doc_text, args.max_length, device
                )
                pair_features = _pair_features(
                    torch.stack([embs[row.head_id] for row in doc_rows]),
                    torch.stack([embs[row.tail_id] for row in doc_rows]),
                )
                dist_ids = torch.tensor(
                    [distance_bucket(row.distance) for row in doc_rows], device=device
                )
                projected = heads.project(pair_features, dist_ids)
                for row, embedding in zip(doc_rows, projected, strict=True):
                    key = (row.doc_id, row.head_id, row.tail_id)
                    for family, label in assignments[key]:
                        support[family][label].append(embedding)
        initializers = {
            family: torch.stack(
                [torch.stack(items).mean(dim=0) for items in support[family]]
            )
            for family in prototype_families
        }
        heads.set_prototypes(initializers)
        encoder.train()
        heads.train()
        shown = {
            family: [len(items) for items in support[family]]
            for family in prototype_families
        }
        print(f"[train] prototype support per class: {shown}", flush=True)
    weight_tensors = (
        {f: torch.tensor(w, device=device) for f, w in weights.items()} if weights else {}
    )
    relation_objective = build_relation_objective(args.relation_objective)
    risk_normalizer = (
        FamilyRiskNormalizer(selected_families)
        if NORMALIZED_RISK in balance_components
        else None
    )
    work_point = (
        WorkPointController(
            [
                workpoint_key(family, position)
                for family in selected_families
                for position in POSITION_BUCKETS
            ]
        )
        if ADAPTIVE_WORKPOINT in balance_components
        else None
    )
    position_index = {position: index for index, position in enumerate(POSITION_BUCKETS)}
    position_ids_by_doc = (
        {
            doc_id: torch.tensor(
                [position_index[row.position] for row in doc_rows],
                device=device,
            )
            for doc_id, doc_rows in rows_by_doc.items()
        }
        if work_point
        else {}
    )
    if balance_components:
        print(f"[train] family balance: {list(balance_components)}", flush=True)
    label_index = {f: {s: i for i, s in enumerate(subs)} for f, subs in FAMILY_SUBTYPES.items()}
    # Two param groups rather than one rate: the official baseline trains the encoder
    # at 1e-5 and the scorer head at 1e-4, and gives the head plain Adam (no decoupled
    # weight decay), which `weight_decay=0.0` reproduces inside AdamW.
    head_parameters = list(heads.parameters())
    if coref_aux_head is not None:
        head_parameters += list(coref_aux_head.parameters())
    optimiser = torch.optim.AdamW(
        [
            {"params": list(encoder.parameters()), "lr": args.lr},
            {
                "params": head_parameters,
                "lr": args.head_lr if args.head_lr is not None else args.lr,
                "weight_decay": 0.0,
            },
        ],
        lr=args.lr,
    )
    # Held-out dev carved out of TRAIN, never from valid: selecting the checkpoint on
    # valid and then reporting valid would bias the reported number. The official
    # baseline selects on dev and reports test; we have no test, so the split has to
    # come out of train instead.
    train_ids = [doc.doc_id for doc in train_docs]
    dev_ids = [doc.doc_id for doc in dev_docs]

    scheduler = None
    if args.warmup_steps > 0:
        from transformers import get_linear_schedule_with_warmup

        # Count optimiser steps, not documents: with --accum-steps N the schedule
        # advances once per N docs, and dev docs never enter the training loop.
        # Getting this wrong stretches the decay past the end of training, so the
        # rate never actually anneals.
        steps_per_epoch = math.ceil(len(train_ids) / args.accum_steps)
        scheduler = get_linear_schedule_with_warmup(
            optimiser, args.warmup_steps, args.epochs * steps_per_epoch
        )
    if dev_ids:
        print(
            f"[train] holdout dev: {len(dev_ids)} docs (from train), "
            f"training on {len(train_ids)}",
            flush=True,
        )

    def save_checkpoint(destination: Path | None = None) -> None:
        destination = destination or args.output
        destination.mkdir(parents=True, exist_ok=True)
        encoder.save_pretrained(destination)
        tokenizer.save_pretrained(destination)
        torch.save(heads.state_dict(), destination / "heads.pt")
        if coref_aux_head is not None:
            torch.save(coref_aux_head.state_dict(), destination / "coref_aux_head.pt")
        (destination / PAIR_HEAD_CONFIG_FILE).write_text(
            json.dumps(
                {
                    "schema_version": "ekg.relation_pair_head.v1",
                    "name": args.pair_head,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        # The mechanism lives in the objective, so inference needs nothing from
        # it -- but the checkpoint still has to say what it was trained under, or
        # an arm can be mistaken for the control after the fact.
        (destination / BALANCE_CONFIG_FILE).write_text(
            json.dumps(
                {
                    "components": list(balance_components),
                    "families": list(selected_families),
                    "position_buckets": list(POSITION_BUCKETS) if work_point else [],
                    "applied_at_inference": False,
                    "none_offsets": dict(work_point.offsets) if work_point else {},
                    "risk_scales": dict(risk_normalizer.scales) if risk_normalizer else {},
                    "trajectory": work_point.trajectory if work_point else [],
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

    def dev_f1() -> tuple[float, dict[str, float]]:
        """Pair-level F1 over non-NONE classes; `--dev-metric` picks micro or macro.

        Micro pools every family, so it is dominated by whichever family has the most
        candidate pairs -- temporal outnumbers subevent ~39:1 on valid. A run selected
        on micro happily trades subevent away for temporal (measured: temporal +3.84
        while subevent fell 22.26 -> 19.65). Macro weights the three families equally.
        """
        encoder.eval()
        heads.eval()
        per_family = {fam: [0, 0, 0] for fam in selected_families}  # tp, fp, fn
        # Raw logits, unshifted: the controller has to measure where the boundary
        # *is*, and the reported dev F1 is a plain argmax over these same numbers.
        collected: dict[str, list] = (
            {
                workpoint_key(family, position): []
                for family in selected_families
                for position in POSITION_BUCKETS
            }
            if work_point
            else {}
        )
        with torch.no_grad():
            for doc_id in dev_ids:
                doc = docs_by_id[doc_id]
                doc_rows = rows_by_doc[doc_id]
                embs = encode_trigger_reps(
                    encoder, tokenizer, doc.nodes, doc.doc_text, args.max_length, device
                )
                logits = heads(
                    _pair_features(
                        torch.stack([embs[r.head_id] for r in doc_rows]),
                        torch.stack([embs[r.tail_id] for r in doc_rows]),
                    ),
                    torch.tensor([distance_bucket(r.distance) for r in doc_rows], device=device),
                )
                for family in selected_families:
                    gold = torch.tensor(
                        [
                            _IGNORE_INDEX
                            if family in r.ignored_families
                            else label_index[family][r.labels.get(family, "NONE")]
                            for r in doc_rows
                        ],
                        device=device,
                    )
                    if work_point is not None:
                        dev_logits = logits[family].detach().float().cpu().numpy()
                        dev_targets = gold.detach().cpu().numpy()
                        row_positions = [row.position for row in doc_rows]
                        for position in POSITION_BUCKETS:
                            mask = [item == position for item in row_positions]
                            if any(mask):
                                collected[workpoint_key(family, position)].append(
                                    (dev_logits[mask], dev_targets[mask])
                                )
                    scored = gold != _IGNORE_INDEX
                    pred = logits[family].argmax(dim=-1)
                    hit = (pred == gold) & scored
                    gold = torch.where(scored, gold, torch.zeros_like(gold))
                    pred = torch.where(scored, pred, torch.zeros_like(pred))
                    per_family[family][0] += int(((gold > 0) & hit).sum())
                    per_family[family][1] += int(((pred > 0) & ~hit).sum())
                    per_family[family][2] += int(((gold > 0) & ~hit).sum())
        encoder.train()
        heads.train()

        def f1_of(tp: int, fp: int, fn: int) -> float:
            if tp == 0:
                return 0.0
            p, r = tp / (tp + fp), tp / (tp + fn)
            return 2 * p * r / (p + r)

        by_family = {fam: f1_of(*counts) for fam, counts in per_family.items()}
        if collected:
            import numpy as np

            for group, parts in collected.items():
                if not parts:
                    raise ValueError(f"no internal-dev pairs for work-point group {group}")
                dev_logits = np.concatenate([p[0] for p in parts])
                dev_targets = np.concatenate([p[1] for p in parts])
                work_point.observe(epoch, group, dev_logits, dev_targets)
        if args.dev_metric == "macro":
            return sum(by_family.values()) / len(by_family), by_family
        pooled = [sum(c[i] for c in per_family.values()) for i in range(3)]
        return f1_of(*pooled), by_family

    best_f1 = -1.0
    best_epoch: int | None = None
    best_by_family: dict[str, float] = {}
    family_selection = {
        family: {"best_f1": -1.0, "best_epoch": None}
        for family in selected_families
    }
    none_offsets: dict[str, torch.Tensor] = {}

    def rebuild_offsets() -> None:
        """Two train-time NONE shifts per family: same sentence and cross sentence.

        Epoch 0 starts with six exact zeros. Internal-dev then updates each
        family/position loop independently; inference never reads these tensors.
        """
        if work_point is None:
            return
        for family in selected_families:
            none_offsets[family] = torch.as_tensor(
                position_none_offsets(
                    family,
                    POSITION_BUCKETS,
                    work_point.offsets,
                ),
                dtype=torch.float32,
                device=device,
            )

    rebuild_offsets()
    encoder.train()
    heads.train()
    for epoch in range(args.epochs):
        doc_ids = list(train_ids)
        random.Random(args.seed + epoch).shuffle(doc_ids)
        running = 0.0
        for seen, doc_id in enumerate(doc_ids, start=1):
            doc = docs_by_id[doc_id]
            embs = encode_trigger_reps(
                encoder, tokenizer, doc.nodes, doc.doc_text, args.max_length, device
            )
            doc_rows = rows_by_doc[doc_id]
            # One batched pair feature per document: per-pair construction launches
            # a kernel per candidate (thousands in a single document).
            head_emb = torch.stack([embs[r.head_id] for r in doc_rows])
            tail_emb = torch.stack([embs[r.tail_id] for r in doc_rows])
            dist_ids = torch.tensor(
                [distance_bucket(r.distance) for r in doc_rows], device=device
            )
            pair_features = _pair_features(head_emb, tail_emb)
            logits = heads(pair_features, dist_ids)
            loss = torch.zeros((), device=device)
            for family in selected_families:
                target = torch.tensor(
                    [
                        _IGNORE_INDEX
                        if family in r.ignored_families
                        else label_index[family][r.labels.get(family, "NONE")]
                        for r in doc_rows
                    ],
                    device=device,
                )
                family_logits = logits[family]
                if none_offsets:
                    # Train-time only. Adding the same shift at inference would
                    # cancel: cross-entropy would just teach the model to
                    # subtract it back out. Shifting only the objective makes the
                    # boundary part of what the encoder learns, and leaves the
                    # test-time rule a plain argmax.
                    family_logits = family_logits.clone()
                    family_logits[:, NONE_INDEX] += none_offsets[family][
                        position_ids_by_doc[doc_id]
                    ]
                family_loss = relation_objective(
                    family_logits,
                    target,
                    weight=weight_tensors.get(family),
                    ignore_index=_IGNORE_INDEX,
                )
                if risk_normalizer is not None:
                    family_loss = family_loss / risk_normalizer.update(
                        family, float(family_loss.detach())
                    )
                loss = loss + family_loss_rates[family] * family_loss
            if coref_aux_head is not None:
                coref_target = torch.tensor(
                    [
                        _IGNORE_INDEX
                        if "coreference" in row.ignored_families
                        else int("coreference" in row.labels)
                        for row in doc_rows
                    ],
                    device=device,
                )
                coref_logits = coref_aux_head(pair_features, dist_ids)["coreference"]
                coref_loss = torch.nn.functional.cross_entropy(
                    coref_logits,
                    coref_target,
                    ignore_index=_IGNORE_INDEX,
                )
                loss = loss + args.coref_aux_rate * coref_loss
            running += float(loss.detach())
            # Scale so the accumulated gradient matches a true batch of that size,
            # and step the scheduler with the optimiser -- stepping it per document
            # would race through the warmup N times too fast.
            (loss / args.accum_steps).backward()
            if seen % args.accum_steps == 0 or seen == len(doc_ids):
                optimiser.step()
                if scheduler is not None:
                    scheduler.step()
                optimiser.zero_grad()
            if seen % 500 == 0:  # long run: report progress inside the epoch too
                print(
                    f"[train] epoch {epoch} {seen}/{len(doc_ids)} docs "
                    f"running_loss={running / seen:.4f}",
                    flush=True,
                )
        print(f"[train] epoch {epoch} mean_loss={running / max(1, len(doc_ids)):.4f}", flush=True)
        if dev_ids:
            f1, by_family = dev_f1()
            better = f1 > best_f1
            detail = " ".join(f"{fam[:4]}={v:.3f}" for fam, v in by_family.items())
            print(
                f"[dev] epoch {epoch} {args.dev_metric}_f1={f1:.4f} ({detail})"
                + (f"  <- best (was {best_f1:.4f}), saving" if better else "  (keeping best)"),
                flush=True,
            )
            if better:
                best_f1 = f1
                best_epoch = epoch
                best_by_family = by_family
                save_checkpoint()
            if args.save_best_by_family:
                for family, family_f1 in by_family.items():
                    selected = family_selection[family]
                    if family_f1 <= selected["best_f1"]:
                        continue
                    selected.update(best_f1=family_f1, best_epoch=epoch)
                    family_output = args.output / "by_family" / family
                    save_checkpoint(family_output)
                    (family_output / "selection.json").write_text(
                        json.dumps(
                            {"family": family, "epoch": epoch, "dev_f1": family_f1},
                            indent=2,
                            sort_keys=True,
                        )
                        + "\n",
                        encoding="utf-8",
                    )
            if work_point is not None:
                rebuild_offsets()
                shown = {f: round(v, 3) for f, v in work_point.offsets.items()}
                print(f"[balance] epoch {epoch} none-offsets {shown}", flush=True)

    if not dev_ids:  # no selection signal: last epoch is all we have
        save_checkpoint()
        print(f"[train] saved last-epoch encoder + heads to {args.output}")
    else:
        print(f"[train] best dev {args.dev_metric}_f1={best_f1:.4f}; checkpoint at {args.output}")
    run_metadata.update(
        {
            "status": "complete",
            "selection": {
                "metric": args.dev_metric if dev_ids else "last_epoch",
                "best_epoch": best_epoch,
                "best_f1": best_f1 if dev_ids else None,
                "best_by_family": best_by_family,
                "family_checkpoints": family_selection if args.save_best_by_family else {},
            },
            "checkpoint_sha256": _checkpoint_hashes(args.output),
        }
    )
    _write_run_metadata(args.output, run_metadata)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
