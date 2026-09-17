#!/usr/bin/env python
"""Teach CSProm-KG to dump CGEP candidate scores, and record the patch (G-11a).

FR-016 state (b) requires the transparent patches and their before/after hashes,
so this is a script rather than a hand-applied edit: it refuses on an anchor it
does not recognise, it is idempotent, and it prints the hashes the results page
has to carry.

**It does not touch the model, the loss, the optimiser or the metric.** The only
addition is: for each test query, write out the raw scores of that query's 512
named candidates, taken straight off `logits` before any of the authors' own
filtering. Ranking, ties and Hit@k then happen in
`scripts/score_kgc_opponent.py` with `succession/metrics.py` -- the scorer every
other row of table 6-2 went through. Letting their `get_performance` produce the
row instead would mix two tie conventions and average in head prediction, which
CGEP does not ask for.

    uv run python scripts/patch_csprom_kg_for_cgep.py --repo /data/TJK/baselines/CSProm-KG
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

# One sentinel per edit: after the first edit lands, a shared marker would make the
# next edit look already-applied, and its anchor is shared text that is legitimately
# still there.
SENTINELS = {
    "args": "-cgep_candidates",
    "start": "_cgep_candidates = None",
    "dump": "'scores': [float(logits[_i, _c]) for _c in _cands]",
}

ARGS_ANCHOR = """    parser.add_argument('-use_log_ranks', action='store_true', help='')"""
ARGS_PATCH = """    parser.add_argument('-use_log_ranks', action='store_true', help='')
    # ekg patch (CGEP) 2026-09-17: CGEP ranks 512 named candidates per query, not the
    # entity table. These two options only add a dump; nothing else reads them.
    parser.add_argument('-cgep_candidates', type=str, default='',
                        help='test_candidates.txt: one line of candidate ids per test row')
    parser.add_argument('-cgep_scores', type=str, default='',
                        help='one JSON object per test row: those candidates and their scores')"""

START_ANCHOR = """    def on_validation_epoch_start(self):
        self._ekg_ranks = [[], []]"""
START_PATCH = """    def on_validation_epoch_start(self):
        self._ekg_ranks = [[], []]
        # ekg patch (CGEP) 2026-09-17: candidates are read once and the dump is
        # truncated per epoch, so a rerun cannot append to a stale file.
        self._cgep_candidates = None
        if getattr(self.configs, 'cgep_candidates', ''):
            with open(self.configs.cgep_candidates, encoding='utf-8') as fh:
                lines = fh.read().strip('\\n').split('\\n')
            assert int(lines[0]) == len(lines) - 1, 'candidate file count line disagrees'
            self._cgep_candidates = [[int(x) for x in line.split()] for line in lines[1:]]
        if getattr(self.configs, 'cgep_scores', ''):
            open(self.configs.cgep_scores, 'w', encoding='utf-8').close()"""

DUMP_ANCHOR = """        logits, _ = self(ent_rel, src_ids, src_mask)
        logits = logits.detach()"""
DUMP_PATCH = """        logits, _ = self(ent_rel, src_ids, src_mask)
        logits = logits.detach()
        # ekg patch (CGEP) 2026-09-17: dump the raw candidate scores *before* the
        # authors' filtered-ranking masking, so our scorer sees exactly what the
        # model said. dataloader 0 is predict_tail, which is the CGEP direction;
        # predict_head is not a CGEP question and is left alone.
        if dataset_idx == 0 and getattr(self, '_cgep_candidates', None) is not None \\
                and getattr(self.configs, 'cgep_scores', ''):
            import json as _json
            base = batch_idx * self.configs.val_batch_size
            with open(self.configs.cgep_scores, 'a', encoding='utf-8') as _fh:
                for _i in range(len(src_ent)):
                    _cands = self._cgep_candidates[base + _i]
                    _fh.write(_json.dumps({
                        'row': base + _i,
                        'gold': int(tgt_ent[_i]),
                        'candidates': _cands,
                        'scores': [float(logits[_i, _c]) for _c in _cands],
                    }) + '\\n')"""


def _apply(path: Path, anchor: str, patched: str, sentinel: str) -> tuple[str, str]:
    before = path.read_text(encoding="utf-8")
    if sentinel in before:
        raise SystemExit(f"{path.name}: the {sentinel!r} edit is already applied")
    if anchor not in before:
        raise SystemExit(f"{path.name}: anchor not found -- upstream moved, do not force it")
    after = before.replace(anchor, patched, 1)
    path.write_text(after, encoding="utf-8")
    return (
        hashlib.sha256(before.encode()).hexdigest(),
        hashlib.sha256(after.encode()).hexdigest(),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()

    for name, anchor, patched, key in (
        ("main.py", ARGS_ANCHOR, ARGS_PATCH, "args"),
        ("models/P_model.py", START_ANCHOR, START_PATCH, "start"),
        ("models/P_model.py", DUMP_ANCHOR, DUMP_PATCH, "dump"),
    ):
        before, after = _apply(args.repo / name, anchor, patched, SENTINELS[key])
        print(f"[patch] {name}\n          before {before}\n          after  {after}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
