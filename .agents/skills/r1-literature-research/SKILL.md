---
name: r1-literature-research
description: Use when EKG work concerns R1 literature review, baseline or input closure, method novelty, official paper or code verification, runnable baseline selection, causal design briefs, or tasks T020 through T024.
---

# R1 Literature Research

Treat these requests as deep research automatically; the user does not need to name a research mode or plugin.

1. Read `docs/HANDOFF.md`, then the relevant parts of
   `docs/phases/PHASE_R1_method_design_freeze.md`, `docs/TASKS.md`, `docs/TODO.md`, and
   `docs/results/PHASE_R1.md`. Follow their current dependencies and stop conditions.
2. Search authoritative primary sources in multiple passes. Prefer the published paper or official
   preprint plus the authors' official code, release, model card, or checkpoint page. Cite claims and
   record enough identity information to reproduce the lookup.
3. For every candidate baseline or method, verify dataset, split, candidate universe, evaluator,
   input assumptions, code revision, license, checkpoint availability, and runnable status. Read the
   first-party result table before citing an external benchmark number.
4. Keep literature evidence separate from project measurements. Experimental numbers remain
   authoritative only in `docs/results/`; mismatched protocols are not comparable baselines.
5. Preserve R1 validity boundaries: do not inspect final-valid outcomes, select methods from proposed
   method results, substitute random initialization for a missing official checkpoint, or start
   proposed GPU training before the relevant R1 gate passes.
6. When asked to advance R1, carry the active task through to its required repository artifacts and
   validations. When asked only for an explanation, make no repository changes.

If a required primary source, implementation, or checkpoint cannot be verified, record the exact
blocker and continue only with independent work that remains valid.
