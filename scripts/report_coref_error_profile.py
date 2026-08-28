#!/usr/bin/env python
"""Split the coreference error mass into under-merges and over-merges.

`score_maven_ere_official.py` reports MUC as three ratios (72.98 / 82.56 / 77.47)
and stops there. Those ratios cannot size an asymmetric objective: they say the
gap is recall-shaped but not *how many* decisions went each way, and the two
directions are different errors downstream -- a missing link splits one event
into two graph nodes, a spurious link fuses two events into one. This script
reports the counts, in the two currencies that matter:

* **pairwise** -- mention pairs, which is what the pair classifier in
  `nodes/coref.py` is actually trained on, so a loss weight ratio reads off it
  directly. These are exactly the official `blanc()` counters `wn` (gold
  coreferent, predicted apart = under-merge) and `wc` (predicted together, gold
  apart = over-merge).
* **MUC links** -- `missing = sum_G (p(G)-1)` and `spurious = sum_P (g(P)-1)`,
  which reconcile arithmetically with the headline 77.47.

Both are computed on the official mention population (gold clusters from
`events`; every gold mention the prediction does not cluster becomes its own
singleton), and both are cross-checked against the organisers' own `evaluate.py`
before anything is printed -- see `_cross_check`. The evaluator is deliberately
**not vendored**; pass its path. Fetch it once with:

    curl -o /tmp/maven_evaluate.py \\
      https://raw.githubusercontent.com/THU-KEG/MAVEN-ERE/main/evaluate.py

    uv run python scripts/report_coref_error_profile.py \\
        --evaluator /tmp/maven_evaluate.py \\
        --gold data/processed/maven_ere/valid.jsonl \\
        --pred runs/submission/valid_prediction_sup.jsonl \\
        --output runs/coref_error_profile_valid.json
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from collections import Counter
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path

from ekg.core.eval import muc_link_errors
from ekg.nodes.coref import HARD_SIMILARITY, trigger_similarity
from ekg.nodes.metrics import merge_prf

# Surface-similarity buckets for the missed/spurious pairs. The split at
# HARD_SIMILARITY is the one that decides whether reweighting can help: a missed
# pair whose triggers are near-identical is one the scorer saw and under-called,
# a missed pair at low similarity needs more than a threshold move.
SIMILARITY_EDGES = (0.2, 0.4, 0.6, 0.8, 1.0)


def _load_evaluator(path: Path):
    spec = importlib.util.spec_from_file_location("maven_ere_evaluate", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot import an evaluator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _by_id(path: Path) -> dict[str, dict]:
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    by_id = {r["id"]: r for r in records}
    if len(by_id) != len(records):
        raise SystemExit(f"{path}: {len(records)} lines but {len(by_id)} unique ids")
    return by_id


@dataclass(frozen=True, slots=True)
class Mention:
    """The gold facts about one mention that the error profile stratifies on."""

    trigger: str
    sent_id: int
    event_id: str


def official_clusterings(
    gold_record: dict, pred_record: dict
) -> tuple[list[set[str]], list[set[str]], dict[str, Mention]]:
    """Gold and predicted clusterings over the official mention population.

    Mirrors `evaluate_coreference` in the organisers' `evaluate.py`: gold
    clusters are the mention lists of `events`, a predicted cluster keeps only
    mentions that exist in gold, and every gold mention left unclustered is
    appended as its own singleton.

    Where the official code is silently lenient this is fail-fast instead. It
    writes a sentinel `-1` when a mention appears in two predicted clusters and
    drops mentions it does not recognise; both are prediction-file bugs that
    would quietly move the numbers, so they raise here.
    """
    mentions: dict[str, Mention] = {}
    gold: list[set[str]] = []
    for event in gold_record["events"]:
        cluster = set()
        for mention in event["mention"]:
            if mention["id"] in mentions:
                raise SystemExit(f"{gold_record['id']}: duplicate gold mention {mention['id']}")
            mentions[mention["id"]] = Mention(
                trigger=mention["trigger_word"], sent_id=mention["sent_id"], event_id=event["id"]
            )
            cluster.add(mention["id"])
        gold.append(cluster)

    predicted: list[set[str]] = []
    seen: set[str] = set()
    for cluster in pred_record.get("coreference", []):
        unknown = [m for m in cluster if m not in mentions]
        if unknown:
            raise SystemExit(f"{gold_record['id']}: predicted mentions absent from gold: {unknown}")
        repeated = seen.intersection(cluster)
        if repeated:
            raise SystemExit(f"{gold_record['id']}: mentions in two predicted clusters: {repeated}")
        seen.update(cluster)
        if cluster:
            predicted.append(set(cluster))
    predicted.extend({m} for m in mentions if m not in seen)
    return gold, predicted, mentions


def _similarity_bucket(similarity: float) -> str:
    for edge in SIMILARITY_EDGES:
        if similarity < edge:
            return f"<{edge:g}"
    return "1.0"


def _pair_profile(pairs: list[tuple[str, str]], mentions: dict[str, Mention]) -> dict:
    """How the erring pairs are distributed over trigger similarity and distance."""
    buckets: Counter[str] = Counter()
    hard = cross_sentence = 0
    for left, right in pairs:
        a, b = mentions[left], mentions[right]
        similarity = trigger_similarity(a.trigger, b.trigger)
        buckets[_similarity_bucket(similarity)] += 1
        hard += similarity >= HARD_SIMILARITY
        cross_sentence += a.sent_id != b.sent_id
    return {
        "n": len(pairs),
        "similarity_buckets": dict(buckets),
        "n_similarity_ge_hard": hard,
        "n_cross_sentence": cross_sentence,
    }


def _erring_pairs(
    clusters: list[set[str]], other_of: dict[str, frozenset[str]]
) -> list[tuple[str, str]]:
    """Pairs joined by `clusters` that `other_of` keeps apart."""
    return [
        (a, b)
        for cluster in clusters
        for a, b in combinations(sorted(cluster), 2)
        if other_of[a] != other_of[b]
    ]


def profile_document(gold_record: dict, pred_record: dict) -> dict:
    gold, predicted, mentions = official_clusterings(gold_record, pred_record)
    gold_of = {m: frozenset(c) for c in gold for m in c}
    pred_of = {m: frozenset(c) for c in predicted for m in c}

    links = muc_link_errors(predicted, gold)
    pairs = merge_prf(predicted, {m: mention.event_id for m, mention in mentions.items()})

    # p(G): pieces a gold cluster was scattered into. g(P): gold clusters a
    # predicted cluster fused. Singletons are omitted -- they cannot err.
    scatter = Counter(len({pred_of[m] for m in c}) for c in gold if len(c) > 1)
    fusion = Counter(len({gold_of[m] for m in c}) for c in predicted if len(c) > 1)
    return {
        "n_mentions": len(mentions),
        "muc": {
            "missing_links": links["missing_links"],
            "gold_links": links["gold_links"],
            "spurious_links": links["spurious_links"],
            "predicted_links": links["predicted_links"],
        },
        "pairwise": {
            "correct_coref": pairs["tp"],
            "predicted_coref": pairs["n_pred"],
            "gold_coref": pairs["n_gold"],
        },
        "scatter": scatter,
        "fusion": fusion,
        "under_merged": _erring_pairs(gold, pred_of),
        "over_merged": _erring_pairs(predicted, gold_of),
        "gold_sizes": Counter(len(c) for c in gold),
        # A cluster whose every mention landed in a different predicted cluster:
        # the prediction recovered none of its links, not merely some.
        "fully_scattered": sum(
            1 for c in gold if len(c) > 1 and len({pred_of[m] for m in c}) == len(c)
        ),
        "n_gold_multi": sum(1 for c in gold if len(c) > 1),
        "n_pred_multi": sum(1 for c in predicted if len(c) > 1),
        "mentions": mentions,
    }


def _share(part: int, whole: int) -> float:
    return part / whole if whole else 0.0


def aggregate(profiles: list[dict]) -> dict:
    """Corpus totals. Counts are summed *before* any ratio, as MUC requires."""
    muc = Counter()
    pairwise = Counter()
    scatter: Counter[int] = Counter()
    fusion: Counter[int] = Counter()
    gold_sizes: Counter[int] = Counter()
    under: list[tuple[str, str]] = []
    over: list[tuple[str, str]] = []
    mentions: dict[str, Mention] = {}
    n_mentions = fully_scattered = n_gold_multi = n_pred_multi = 0

    for profile in profiles:
        muc.update(profile["muc"])
        pairwise.update(profile["pairwise"])
        scatter.update(profile["scatter"])
        fusion.update(profile["fusion"])
        gold_sizes.update(profile["gold_sizes"])
        under.extend(profile["under_merged"])
        over.extend(profile["over_merged"])
        mentions.update(profile["mentions"])
        n_mentions += profile["n_mentions"]
        fully_scattered += profile["fully_scattered"]
        n_gold_multi += profile["n_gold_multi"]
        n_pred_multi += profile["n_pred_multi"]

    # A missed pair belongs to exactly one gold cluster, so its size is well
    # defined; this says whether the misses sit in 2-mention clusters or in the
    # long tail, which decides how much of MUC recall a fix can even reach.
    gold_size_of_event = Counter(m.event_id for m in mentions.values())
    under_by_size = Counter(gold_size_of_event[mentions[left].event_id] for left, _ in under)

    n_under, n_over = len(under), len(over)
    errors = n_under + n_over
    missing, spurious = muc["missing_links"], muc["spurious_links"]
    link_errors = missing + spurious
    return {
        "n_documents": len(profiles),
        "n_mentions": n_mentions,
        "pairwise": {
            "under_merged": n_under,
            "over_merged": n_over,
            "n_errors": errors,
            "under_merged_share": _share(n_under, errors),
            "over_merged_share": _share(n_over, errors),
            "gold_coref_pairs": pairwise["gold_coref"],
            "predicted_coref_pairs": pairwise["predicted_coref"],
            "correct_coref_pairs": pairwise["correct_coref"],
            "recall": _share(pairwise["correct_coref"], pairwise["gold_coref"]),
            "precision": _share(pairwise["correct_coref"], pairwise["predicted_coref"]),
        },
        "muc": {
            "missing_links": missing,
            "spurious_links": spurious,
            "n_errors": link_errors,
            "missing_share": _share(missing, link_errors),
            "spurious_share": _share(spurious, link_errors),
            "gold_links": muc["gold_links"],
            "predicted_links": muc["predicted_links"],
            "recall": 1.0 - _share(missing, muc["gold_links"]),
            "precision": 1.0 - _share(spurious, muc["predicted_links"]),
        },
        "structure": {
            "n_gold_multi_clusters": n_gold_multi,
            "n_pred_multi_clusters": n_pred_multi,
            "n_gold_fully_scattered": fully_scattered,
            "gold_cluster_sizes": dict(sorted(gold_sizes.items())),
            "scatter_pieces": dict(sorted(scatter.items())),
            "fusion_gold_clusters": dict(sorted(fusion.items())),
            "under_merged_by_gold_cluster_size": dict(sorted(under_by_size.items())),
        },
        "under_merged_profile": _pair_profile(under, mentions),
        "over_merged_profile": _pair_profile(over, mentions),
    }


def _cross_check(evaluator, gold: dict[str, dict], pred: dict[str, dict], totals: dict) -> None:
    """Refuse to report anything the organisers' scorer does not confirm.

    Two independent checks, both fail-fast: the MUC ratios derived from our link
    counts must equal the official ones, and our pairwise counts must equal the
    official `blanc()` counters summed the same way. If the mention population
    were rebuilt even slightly differently, one of these moves.
    """
    official = evaluator.evaluate_coreference(gold, pred)
    for key in ("precision", "recall"):
        ours, theirs = totals["muc"][key], official[f"muc_{key}"] / 100.0
        if abs(ours - theirs) > 1e-9:
            raise SystemExit(f"MUC {key} disagrees with the official scorer: {ours} vs {theirs}")

    rc = wc = wn = 0
    for doc_id, gold_record in gold.items():
        gold_clusters, predicted, _ = official_clusterings(gold_record, pred[doc_id])
        to_gold = {m: tuple(sorted(c)) for c in gold_clusters for m in c}
        to_pred = {m: tuple(sorted(c)) for c in predicted for m in c}
        doc_rc, doc_wc, _, doc_wn = evaluator.blanc(to_pred, to_gold)
        rc, wc, wn = rc + doc_rc, wc + doc_wc, wn + doc_wn

    ours = (
        totals["pairwise"]["correct_coref_pairs"],
        totals["pairwise"]["over_merged"],
        totals["pairwise"]["under_merged"],
    )
    if ours != (rc, wc, wn):
        raise SystemExit(
            f"pairwise counts disagree with official blanc(): {ours} vs {(rc, wc, wn)}"
        )
    print(f"[profile] ✔ cross-checked against the official scorer "
          f"(MUC F1 {official['muc_f1']:.2f}, BLANC F1 {official['blanc_f1']:.2f})")


def _print_report(totals: dict) -> None:
    pair, muc = totals["pairwise"], totals["muc"]
    print(f"\n[profile] {totals['n_documents']} documents, {totals['n_mentions']} gold mentions\n")
    print("  error direction        pairs      share      MUC links      share")
    print(f"  under-merge  {pair['under_merged']:10d} {pair['under_merged_share']:10.1%}"
          f" {muc['missing_links']:14d} {muc['missing_share']:10.1%}")
    print(f"  over-merge   {pair['over_merged']:10d} {pair['over_merged_share']:10.1%}"
          f" {muc['spurious_links']:14d} {muc['spurious_share']:10.1%}")
    print(f"  ratio under/over        {_share(pair['under_merged'], pair['over_merged']):.2f}x"
          f"                {_share(muc['missing_links'], muc['spurious_links']):.2f}x")
    print(f"\n  denominators: gold coref pairs {pair['gold_coref_pairs']}, predicted "
          f"{pair['predicted_coref_pairs']}; gold links {muc['gold_links']}, predicted "
          f"{muc['predicted_links']}")
    print(f"  pairwise P/R {pair['precision']:.4f} / {pair['recall']:.4f}"
          f"   MUC P/R {muc['precision']:.4f} / {muc['recall']:.4f}")

    structure = totals["structure"]
    print(f"\n  gold multi-mention clusters {structure['n_gold_multi_clusters']}"
          f" (fully scattered {structure['n_gold_fully_scattered']}),"
          f" predicted {structure['n_pred_multi_clusters']}")
    print(f"  pieces per split gold cluster p(G): {structure['scatter_pieces']}")
    print(f"  gold clusters per predicted cluster g(P): {structure['fusion_gold_clusters']}")
    print(f"  under-merged pairs by gold cluster size: "
          f"{structure['under_merged_by_gold_cluster_size']}")

    for name in ("under_merged_profile", "over_merged_profile"):
        profile = totals[name]
        print(f"\n  {name.replace('_', ' ')}: n={profile['n']}, "
              f"trigger similarity >= {HARD_SIMILARITY}: {profile['n_similarity_ge_hard']}"
              f" ({_share(profile['n_similarity_ge_hard'], profile['n']):.1%}), "
              f"cross-sentence: {profile['n_cross_sentence']}"
              f" ({_share(profile['n_cross_sentence'], profile['n']):.1%})")
        print(f"    similarity buckets: {profile['similarity_buckets']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evaluator", required=True, type=Path,
                        help="path to the organisers' evaluate.py (not vendored here)")
    parser.add_argument("--gold", required=True, type=Path, help="labelled split, e.g. valid.jsonl")
    parser.add_argument("--pred", required=True, type=Path, help="predictions in official shape")
    parser.add_argument("--output", type=Path, help="write the profile as JSON here")
    args = parser.parse_args()

    evaluator = _load_evaluator(args.evaluator)
    gold, pred = _by_id(args.gold), _by_id(args.pred)
    missing = set(gold) - set(pred)
    if missing:
        # The official scorer reads these as all-singleton; profiling a partial
        # prediction would silently understate the over-merge side.
        raise SystemExit(
            f"{len(missing)} gold documents have no prediction, e.g. {sorted(missing)[0]}"
        )

    totals = aggregate([profile_document(gold[doc_id], pred[doc_id]) for doc_id in gold])
    _cross_check(evaluator, gold, pred, totals)
    _print_report(totals)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(totals, indent=2), encoding="utf-8")
        print(f"\n[profile] wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
