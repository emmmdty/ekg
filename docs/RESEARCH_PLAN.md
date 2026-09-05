# Research Plan: Occurrence-level Event Graph Construction and Use

| Field | Value |
|---|---|
| Plan Version | `0.2.1` |
| Date | `2026-09-05` |
| Spec | [`SPEC.md`](SPEC.md) |
| Status | Working design; method hypotheses remain revisable until their phase protocol is frozen. |

## Summary

The plan tests whether explicit local evidence adequacy and uncertainty can reduce occurrence-graph construction errors
and explain downstream risk. The current candidate designs are argument-uncertainty-aware identity resolution,
pair-evidence-sufficiency relation extraction and structured factuality inference. These are **hypotheses, not spec
requirements**: literature, ID, power or pilot evidence may replace them while the outcomes in `SPEC.md` remain stable.

Detailed evidence and primary-source links are in
[`replan/METHODOLOGY_REDESIGN_20260904.md`](replan/METHODOLOGY_REDESIGN_20260904.md).

## Technical Context

| Context | Choice |
|---|---|
| Language/toolchain | Python, existing `uv` project |
| Core code | `src/ekg/nodes`, `src/ekg/relations`, `src/ekg/factuality`, `src/ekg/succession` |
| Evaluation | official/public task scorers, per-document predictions, document-cluster paired bootstrap |
| Storage | content-addressed files and immutable stage bundles |
| Testing | pytest, ruff, `ekg-smoke`, protocol fixtures and CPU cache replay |
| Local platform | WSL2/Ubuntu, CPU only |
| Remote platform | `gpu-4090`; `gpu-5090` only with per-use approval |
| Current data families | MAVEN-ERE, MAVEN-ARG, MAVEN-FACT, locally rebuilt CGEP-MAVEN protocol |
| Scale | single-backbone component experiments first; matched seeds and ablations only after promotion |

## Constitution Check

| Principle | Plan compliance | Gate |
|---|---|---|
| Research validity | One manifest/candidate/evaluator per comparison; final-valid excluded from selection | PASS |
| Adaptable design | Candidate mechanisms live here, not in the specification | PASS |
| Reproducibility | P1 trust root and immutable stage bundles required | PASS: P1 r15 and A3 failed handoff r17 frozen |
| Honest evidence | Existing A3/D3/C4 failures retain identity; oracle inputs remain oracle | PASS |
| Testable simplicity | Each candidate must define treatment, mediator, outcome, ablation and negative control | CONDITIONAL: briefs exist; baseline/power gates remain blocked |
| Reuse first | Official implementations preferred; fidelity matrix required | BLOCKED for Ch1/Ch2: no second recent same-protocol runnable method |

No proposed-method GPU work is allowed until the conditional items pass.

## Research Basis

The plan is grounded in these primary-source observations:

- MAVEN-ERE treats event identity and multiple relation types as interacting structure rather than independent labels.
- MAVEN-ARG makes event-cluster argument supervision available, but the R1 full audit found incomplete ERE mention
  coverage and conflicting parent clusters. It cannot be copied into a deployable mention-local identity input.
- CorefPrompt supports event-type and argument compatibility as useful identity signals.
- RESIJ uses rich event structures and cross-relation constraints; the method frontier is beyond fixed family weights.
- TacoERE, KnowQA and 2025 two-stage ERE motivate pair-specific compression, evidence or retrieval, but their split and
  candidate contracts differ and require local protocol alignment.
- MAVEN-FACT and ModaFact motivate explicit evidence, modality and polarity structure; simple feature concatenation can
  overfit.
- NLP power-analysis research motivates prospective MDE/power simulation in addition to paired confidence intervals.

The literature matrix, code availability and exact protocol deltas are R1 deliverables. No paper score becomes a local
baseline result until its method is run under the local frozen protocol.

## Current Candidate Design

### Identity study

**Observed problem**: Existing context/confusability experiments did not yield a stable primary improvement. An
event-level gold-argument oracle has signal but leaks cluster identity when copied to every mention.

**Candidate hypothesis**: A mention-local argument-role posterior, aligned across mention pairs and weighted by predictive
uncertainty, reduces false merges among lexically similar occurrences.

**Candidate treatment**: role posteriors from a frozen mention-local semantic-role extractor that is independent of
MAVEN-ARG cluster gold, followed by role alignment and uncertainty-aware pair/clustering risk. Missing extraction is an
explicit state, never a fallback to event-level arguments.

**Required mediator**: pre-registered false-merge and calibration behavior on ambiguous/cross-sentence slices.

**Minimum causal matrix**: anchor; strong argument-aware baseline; proposed; no arguments; hard arguments without
uncertainty; uncertainty negative control. Gold arguments remain a separate oracle.

### Relation study

**Observed problem**: Fixed/adaptive family workpoints and three approximate retrieval variants failed their frozen gates.
A3.6 has now accounted for official rates, coreference auxiliary and per-family selection: the best recipe still misses the
causal anchor, and 7,115 of its 9,490 causal false positives are cross-sentence.

**Candidate hypothesis**: Under the complete candidate universe, pair-specific evidence sufficiency and abstention risk
can reduce cross-sentence false positives without sacrificing recall or other relation families.

**Candidate treatment**: evidence-span selection and sufficiency risk integrated with typed relation prediction. Retrieval
or hard negatives may shape training/evidence, but cannot remove evaluation candidates.

**Required mediator**: cross-sentence causal false positives decrease while causal recall and subevent/temporal guardrails
remain non-inferior.

**Minimum causal matrix**: official anchor; protocol-aligned two-stage/public-family baseline; proposed; no sufficiency;
random/window evidence; no structural constraint.

### Factuality study

**Observed problem**: Existing evidence-conditioned systems are not statistically separated from strong baselines, and a
gold-evidence oracle does not reveal a sufficiently large remaining evidence-location ceiling. The original 291-document
design is underpowered, but the pre-frozen 2,913-document five-fold OOF design has accepted RoBERTa+CLS/DMRoBERTa
anchors and passes prospective power for the registered minimum meaningful effect.

**Candidate hypothesis**: Separating evidence sufficiency/unknown, modality and polarity decisions with typed cue spans
reduces structured confusions that a pooled five-class head cannot express.

**Candidate treatment**: certainty/polarity factorization plus a cue-conditioned residual and consistent five-class
output distribution. Better evidence location alone is explicitly not the treatment.

**Required mediator**: a document-cluster paired reduction in the pre-registered unknown, modality-only and polarity-only
confusion rate for full versus flat-head remove-core; cue permutation must remove that reduction.

**Minimum causal matrix**: primary anchor; official evidence pipeline; proposed; flat five-class head; cue-permutation
negative control. T022 freezes this causal brief; T023 consistency audit and T024 executable contract remain mandatory
before a seed-13 pilot, and extra seeds still require separate authorization.

### System evaluation

The consumer study retains fixed queries, candidates, serialization and checkpoints while varying identity, relation and
factuality quality. It includes random/frequency, text-only and graph consumers, graph-dependence controls and a
same-backbone frozen/fine-tuned contrast. Input uncertainty/risk may be analyzed only after the base factorial is valid.

## Evaluation Design

### Protocol layers

1. **Component isolation**: gold upstream inputs identify each component method.
2. **End-to-end propagation**: immutable predicted upstream bundles measure practical degradation.
3. **Consumer factorial**: same-instance interventions estimate marginal and interaction effects.

### Model-selection discipline

- Train/internal-dev or pre-frozen repeated splits drive design and selection.
- Final-valid is evaluated once as a sealed batch after model/config/checkpoint/threshold identities are frozen.
- Historical final-valid access is disclosed and cannot be erased by a new counter.
- Infrastructure-only retry is allowed only when no metric was returned and all identities are unchanged.

### Statistics and power

- Estimate the power curve and MDE from frozen anchor per-document outputs before proposed results.
- Pre-register a minimum meaningful primary effect and mandatory non-inferiority margins.
- Aggregate matched seeds inside each document bootstrap draw; report raw seeds, mean and sample standard deviation.
- Use at least 10,000 document-cluster bootstrap draws for primary anchor comparisons.
- Correct finite pre-registered Ch4 contrast families with Holm; mark all other comparisons exploratory.
- If a dataset is underpowered, add a pre-frozen repeated-split/cross-validation or public external-validation design. Do
  not weaken the primary outcome after observing results.

## Data and Interface Design

```text
gold event mentions
  → identity bundle: mention → occurrence cluster + risk
  → relation bundle: typed directed edges + probabilities/evidence/risk
  → factuality bundle: class probabilities + evidence/risk
  → fixed consumer instances: query + candidates + graph serialization
```

Every boundary validates source hashes, schema version, IDs, duplicates, missing instances and upstream status. Task
outputs use `EventNode.metadata`; no task-specific schema fields are added. MAVEN-family cross-dataset mapping must prove
doc/event/mention/offset identity before any argument or factuality join.

## Design Freeze and Execution Strategy

The current dependency plan is:

`P1/A3.6 closed → R1 baseline/input closure → {identity, relation, factuality} → consumer factorial → thesis audit`.

The three component studies may be reordered or run in parallel when R1 finds no real data/model dependency. This is a
plan choice, not a specification requirement. It may change after R1, provided every study remains independently
testable and cross-stage provenance is intact; the consumer factorial waits for all required upstream handoffs.

Within a mechanism family, a maximum of two valid design cycles prevents unbounded tuning. A failed family is archived.
A new family requires a new R1-style brief demonstrating a different causal intervention, literature boundary, power plan
and protocol version; changing a name, seed, threshold or backbone is not a new family.

## Plan Change Policy

Plan changes are expected when research evidence falsifies a hypothesis. Every material change must state:

1. which specification requirement it serves;
2. what evidence invalidated the previous design;
3. why the new design is materially different and simpler alternatives are insufficient;
4. which protocol/hash/task artifacts must change;
5. how completed results retain their original identity.

Changing the plan does not require changing the specification unless the research outcome, scope or quality bar changes.
Any such specification amendment requires the constitution governance process and explicit user approval.

## Complexity Tracking

| Complexity | Why currently justified | Simpler alternative rejected because |
|---|---|---|
| Three component methods plus one factorial | Required thesis outcome and end-to-end scientific question | Independent component scores cannot quantify propagation |
| Multiple public data families | No single released dataset carries every required label and consumer task | Silent joins or synthetic gold would invalidate conclusions |
| Matched seeds + clustered inference + power analysis | Model randomness and document dependence are material | Single-run or instance-i.i.d. inference overstates certainty |
| Immutable bundles and external trust roots | Thesis tables must be reproducible across machines/phases | Markdown summaries cannot verify data/code/checkpoint identity |

## Open Design Questions for R1

- Which degree-type/admission-year standard applies administratively?
- Which frozen mention-local semantic-role extractor can cover MAVEN-ERE without MAVEN-ARG cluster supervision?
- Which recent strong methods have accessible official code/checkpoints and compatible licenses?
- Is a hidden official evaluation route available? If not, which external or repeated-split validation offers adequate
  power without contaminating final-valid?
- What minimum meaningful effects are scientifically defensible for each primary outcome?
