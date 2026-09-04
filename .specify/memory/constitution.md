<!--
Sync Impact Report
- Version: none → 1.0.0
- Added principles: Research Validity; Outcome Spec / Adaptable Design; Reproducibility;
  Honest Evidence; Testable Simplicity; Reuse Before Reimplementation
- Added sections: Research Quality Gates; Spec-Driven Workflow
- Follow-up TODOs: none
-->

# EKG Research Constitution

## Core Principles

### I. Research Validity Is Non-Negotiable

Every confirmatory claim MUST use aligned manifests, candidate universes, input assumptions and evaluators. Primary
outcomes and anchors MUST be frozen before proposed-method results are observed. Final-valid data MUST NOT drive model,
threshold or hyperparameter selection. Statistical uncertainty, matched seeds, guardrails and multiple-comparison control
MUST match the data dependency structure. Progress, cost or a desirable narrative MUST NOT override validity.

### II. Specify Outcomes, Keep Designs Adaptable

The specification MUST define the research problem, required capabilities, measurable outcomes, constraints and edge
cases without prescribing a particular model, component or phase sequence. Technical hypotheses, architectures,
baselines and experiment order belong to the research plan and MAY change when evidence falsifies them. Tasks and
runtime status MUST remain outside the specification. A failed mechanism MUST NOT silently change an accepted outcome;
it triggers redesign under the same quality bar unless feasibility evidence supports a prospective amendment.

### III. Reproducibility and Traceability

Every result used in a thesis claim MUST be traceable from table to immutable metrics, per-instance predictions,
checkpoint, command, configuration, code revision, data/manifest hashes and evaluator identity. Cross-stage consumers
MUST validate IDs and provenance before use. A bundle MUST NOT self-certify its own trust root. Reproduction fixes MUST
be separated from method effects.

### IV. Honest Evidence and No Leakage

Negative, null and degraded results MUST be retained and reported. Gold arguments, gold evidence and gold upstream
structures MAY be used only as explicit oracle or component-isolation inputs; they MUST NOT be labeled deployable.
Different splits, candidates, scorers or hidden input assumptions MUST NOT be compared as if they formed one leaderboard.
Missing IDs and incompatible schemas MUST fail fast rather than receive defaults or fallback predictions.

### V. Testable Simplicity

Each method claim MUST have a falsifiable causal chain, a public primary outcome, a core ablation and a negative control.
Implementation MUST use the smallest design that isolates the claimed mechanism. Code changes MUST include the necessary
tests, call-site/config updates and CPU replay path. `EventNode` remains schema-stable; extensions use `metadata`.

### VI. Reuse Before Reimplementation

Official or mature public implementations MUST be adapted when available. Transparent environment, path, data-interface
or checkpoint patches are allowed only with upstream revision and before/after hashes recorded. A local approximation
MUST be labeled as such and MUST NOT be presented as a faithful reproduction.

## Research Quality Gates

- Ch1–Ch3 method claims MUST improve their frozen public primary outcome over the primary anchor and another strong,
  distinct method family under one protocol, with matched seeds, document-cluster paired uncertainty and mandatory
  guardrails. Diagnostic or self-invented metrics cannot replace the primary outcome.
- Ch4 MUST use standard ranking metrics, credible consumers, graph-dependence controls, same-instance interventions and
  paired inference. Consumer-by-quality interactions may be positive, null or negative when the design is valid.
- Power and minimum meaningful effect MUST be considered before confirmatory runs. Low power does not justify weaker
  inference; the design, evidence base or claim must change prospectively.
- Any feasibility-based reduction in scope requires explicit user and adviser approval, a written evidence record and a
  versioned specification amendment. Agents MUST NOT lower the thesis standard autonomously.

## Spec-Driven Workflow

The project follows the official GitHub Spec Kit separation of concerns:

1. **Constitution** (`.specify/memory/constitution.md`): stable, non-negotiable principles.
2. **Specification** (`docs/SPEC.md`): WHAT/WHY, scenarios, requirements, entities, edge cases and measurable outcomes.
3. **Research plan** (`docs/RESEARCH_PLAN.md`): current HOW—literature synthesis, hypotheses, architecture and
   evaluation design. It is evidence-adaptive.
4. **Tasks** (`docs/TASKS.md` and `docs/phases/`): executable work with dependencies and independent verification.
5. **Implementation and evidence** (`src/`, `scripts/`, `tests/`, `docs/results/`): code and immutable observations.
6. **Runtime state** (`docs/TODO.md`, `docs/HANDOFF.md`): current position only; it cannot redefine requirements.

Before implementation, the current plan MUST pass a constitution check. After tasks are generated, a consistency audit
MUST verify that every requirement maps to one or more tasks and tests, and that no task invents a new requirement.

## Governance

This constitution outranks the specification, plan, tasks and runtime documents. Amendments require a rationale, impact
assessment, migration notes and semantic version bump. The specification may be amended only prospectively; completed
experimental judgments remain governed by their frozen protocol. Every phase review MUST check constitution compliance,
require explicit justification for complexity and update downstream artifacts when an upstream contract changes.

**Version**: 1.0.0 | **Ratified**: 2026-09-04 | **Last Amended**: 2026-09-04
