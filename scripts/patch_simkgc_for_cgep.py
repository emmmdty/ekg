#!/usr/bin/env python
"""Teach SimKGC to dump CGEP candidate scores, and record the patch (G-11a).

Same contract as `patch_csprom_kg_for_cgep.py`: the opponent only writes out the
512 candidate scores per query, and ranking, ties and Hit@k happen in
`scripts/score_kgc_opponent.py` with `succession/metrics.py`, the scorer every
other row of table 6-2 went through. SimKGC's own loop averages the forward and
backward directions and counts hits at 1/3/10 only; CGEP asks for neither.

Three edits, none of them touching the model, the loss or the scoring function:

* `config.py` -- add `cgep-maven` to the task whitelist, plus two options. The
  task string reaches exactly two places (`doc._parse_entity_name`, which strips
  WordNet's `_NN_1` suffixes, and a wiki5m assertion in `rerank`), so a new name
  takes the generic branch, which is the right one for plain trigger words.
* `evaluate.py` -- dump `batch_score` at the 512 candidate columns, placed
  **after** `rerank_by_graph` (that is part of their method) and **before** the
  known-triplet filtering (that is KGC's filtered protocol, which CGEP does not
  use, and our scorer would double-count it).
* `evaluate.py` -- arm the dump on the forward direction only: backward
  prediction asks "which head explains this tail", which is not a CGEP question.

    uv run python scripts/patch_simkgc_for_cgep.py --repo /data/TJK/baselines/SimKGC
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

# Each sentinel must be text that ONLY its own edit introduces. The dump edit's
# body contains `_CGEP_STATE['active']`, so using that as the arm edit's sentinel
# made the arm look already-applied the moment the dump landed.
SENTINELS = {
    "config": "cgep_scores",
    "state": "module state so the dump needs no signature change",
    "dump": "'row': start + _idx",
    "arm": "arm the dump for the forward direction only",
}

CONFIG_ANCHOR = (
    "assert args.task.lower() in "
    "['wn18rr', 'fb15k237', 'wiki5m_ind', 'wiki5m_trans']"
)
CONFIG_PATCH = """# ekg patch (CGEP) 2026-09-17: a new task name, and a dump. The task string only
# reaches doc._parse_entity_name (WordNet suffix stripping) and a wiki5m assertion
# in rerank, so 'cgep-maven' takes the generic branch -- the right one for plain
# trigger words.
assert args.task.lower() in [
    'wn18rr', 'fb15k237', 'wiki5m_ind', 'wiki5m_trans', 'cgep-maven']"""

ARGS_ANCHOR = """parser.add_argument('--eval-model-path', default='', type=str, metavar='N',
                    help='path to model, only used for evaluation')"""
ARGS_PATCH = """parser.add_argument('--eval-model-path', default='', type=str, metavar='N',
                    help='path to model, only used for evaluation')
# ekg patch (CGEP) 2026-09-17: CGEP ranks 512 named candidates per query, not the
# entity table. These two options only add a dump; nothing else reads them.
parser.add_argument('--cgep-candidates', default='', type=str,
                    help='test_candidates.json: one list of candidate entity ids per row')
parser.add_argument('--cgep-scores', default='', type=str,
                    help='one JSON object per row with those candidates and their scores')"""

DUMP_ANCHOR = """        # re-ranking based on topological structure
        rerank_by_graph(batch_score, examples[start:end], entity_dict=entity_dict)"""
DUMP_PATCH = """        # re-ranking based on topological structure
        rerank_by_graph(batch_score, examples[start:end], entity_dict=entity_dict)

        # ekg patch (CGEP) 2026-09-17: dump the 512 candidate scores. Placed after
        # rerank_by_graph -- that is part of SimKGC -- and before the known-triplet
        # filtering below, which is KGC's filtered protocol rather than CGEP's, and
        # which our scorer neither expects nor needs. Row index is start + idx
        # because load_data preserves file order and nothing shuffles evaluation.
        if _CGEP_STATE['active']:
            with open(_CGEP_STATE['scores'], 'a', encoding='utf-8') as _fh:
                for _idx in range(batch_score.size(0)):
                    _cands = [entity_dict.entity_to_idx(_c)
                              for _c in _CGEP_STATE['candidates'][start + _idx]]
                    _fh.write(json.dumps({
                        'row': start + _idx,
                        'gold': int(batch_target[_idx].item()),
                        'candidates': _cands,
                        'scores': [float(batch_score[_idx, _c]) for _c in _cands],
                    }) + '\\n')"""

ARM_ANCHOR = """    hr_tensor, _ = predictor.predict_by_examples(examples)"""
ARM_PATCH = """    # ekg patch (CGEP) 2026-09-17: arm the dump for the forward direction only.
    # Backward prediction asks which head explains a tail, which is not a CGEP
    # question, and its rows would collide with the forward rows in the dump.
    _CGEP_STATE['active'] = bool(eval_forward and args.cgep_scores and args.cgep_candidates)
    if _CGEP_STATE['active']:
        _CGEP_STATE['scores'] = args.cgep_scores
        _CGEP_STATE['candidates'] = json.load(open(args.cgep_candidates, encoding='utf-8'))
        open(args.cgep_scores, 'w', encoding='utf-8').close()

    hr_tensor, _ = predictor.predict_by_examples(examples)"""

# The anchor has to include the decorator: `def compute_metrics` is preceded by
# `@torch.no_grad()`, and inserting between a decorator and its def is a syntax
# error -- which python only reports when the module is imported, i.e. after the
# training run that produced the checkpoint.
STATE_ANCHOR = """@torch.no_grad()
def compute_metrics(hr_tensor: torch.tensor,"""
STATE_PATCH = """# ekg patch (CGEP) 2026-09-17: module state so the dump needs no signature change
# on functions the rest of the repo calls.
_CGEP_STATE = {'active': False, 'scores': '', 'candidates': []}


@torch.no_grad()
def compute_metrics(hr_tensor: torch.tensor,"""


def _apply(path: Path, edits: list[tuple[str, str, str]]) -> tuple[str, str]:
    before = path.read_text(encoding="utf-8")
    text = before
    for anchor, patched, sentinel in edits:
        if sentinel in text:
            raise SystemExit(f"{path.name}: the {sentinel!r} edit is already applied")
        if anchor not in text:
            raise SystemExit(f"{path.name}: anchor not found -- upstream moved, do not force it")
        text = text.replace(anchor, patched, 1)
    path.write_text(text, encoding="utf-8")
    return (
        hashlib.sha256(before.encode()).hexdigest(),
        hashlib.sha256(text.encode()).hexdigest(),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()

    plan = {
        "config.py": [
            (CONFIG_ANCHOR, CONFIG_PATCH, "cgep-maven"),
            (ARGS_ANCHOR, ARGS_PATCH, SENTINELS["config"]),
        ],
        "evaluate.py": [
            (STATE_ANCHOR, STATE_PATCH, SENTINELS["state"]),
            (DUMP_ANCHOR, DUMP_PATCH, SENTINELS["dump"]),
            (ARM_ANCHOR, ARM_PATCH, SENTINELS["arm"]),
        ],
    }
    for name, edits in plan.items():
        before, after = _apply(args.repo / name, edits)
        print(f"[patch] {name}\n          before {before}\n          after  {after}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
