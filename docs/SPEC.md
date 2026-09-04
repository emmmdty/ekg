# Research Specification: Occurrence-level Event Graph Construction and Use

| Field | Value |
|---|---|
| Specification ID | `001-occurrence-ekg-thesis` |
| Version | `1.0.0` |
| Created | `2026-09-04` |
| Status | Review-ready |
**Input**: Build a thesis-grade occurrence-level event graph system with three method contributions and one system-level
evaluation, without lowering quality when an initial method fails.

> This file defines **WHAT and WHY**, not HOW. Binding principles are in
> [the research constitution](../.specify/memory/constitution.md). Candidate methods, architecture and experiment
> sequencing belong to [`RESEARCH_PLAN.md`](RESEARCH_PLAN.md); executable work belongs to
> [`TASKS.md`](TASKS.md) and [`phases/`](phases/README.md); current state belongs to [`TODO.md`](TODO.md) and
> [`HANDOFF.md`](HANDOFF.md); observed numbers belong only to [`results/`](results/README.md).

## Problem Statement

Occurrence-level event graphs must distinguish event identity, represent typed relations and attach factuality while
remaining useful to downstream consumers. Errors can originate at any construction stage and interact after propagation.
The research must answer:

> **How can occurrence identity, event relations and event factuality be improved under reproducible public protocols,
> and what marginal and interaction costs do their errors impose on different graph consumers on the same instances?**

The intended thesis has three independently validated method contributions and one system evaluation contribution.
Methods are deliberately unspecified: the specification constrains outcomes and evidence quality, not the solution.

## Research Scenarios and Independent Tests

### RS-001 — Resolve event identity (Priority: P1)

A graph builder can group mentions referring to the same real-world occurrence without merging distinct occurrences.

**Why this priority**: Identity defines graph nodes and therefore conditions every downstream edge and attribute.

**Independent test**: Evaluate a frozen identity method and strong baselines on the same public manifest with gold event
mentions and the same official scorer; verify primary improvement, secondary-metric guardrails and clustering behavior.

**Acceptance scenarios**:

1. **Given** a frozen public evaluation protocol and baseline roster, **when** identity predictions are scored, **then**
   every method uses the same mentions, documents and evaluator.
2. **Given** ambiguous same-trigger or cross-sentence mentions, **when** the proposed method changes its decisions,
   **then** a pre-registered mechanism diagnostic explains the direction without using gold identity at inference.
3. **Given** predicted identity output, **when** it is exported, **then** every mention maps to exactly one traceable
   cluster and exposes calibrated confidence without changing `EventNode` fields.

### RS-002 — Extract typed event relations (Priority: P1)

A graph builder can predict causal, subevent and temporal relations while preserving the full frozen candidate and
evaluation contract.

**Why this priority**: Relations define graph structure and are the main carrier of multi-event reasoning.

**Independent test**: Evaluate a frozen relation method against multiple strong, protocol-aligned method families with
gold component inputs; verify the causal primary outcome and mandatory subevent/temporal guardrails.

**Acceptance scenarios**:

1. **Given** one candidate universe, **when** baselines and the proposed method run, **then** none may silently prune,
   add, relabel or drop evaluation candidates.
2. **Given** a claimed relation mechanism, **when** its core component is removed or replaced by the strongest
   alternative, **then** the pre-registered mediator and primary outcome test can confirm or falsify the claim.
3. **Given** relation predictions, **when** exported, **then** endpoint IDs, direction, type probabilities, confidence and
   upstream identity provenance are complete and verifiable.

### RS-003 — Detect event factuality and evidence (Priority: P1)

A graph builder can assign the public factuality label set and supporting evidence without allowing majority classes to
hide failures on polarity, modality or unknown cases.

**Why this priority**: Consumers must distinguish asserted, possible, negated and unknown events rather than treating
every detected event as fact.

**Independent test**: Evaluate a frozen method and strong baselines on one public protocol with the standard multiclass
primary metric, evidence metrics and pre-registered rare-class guardrails.

**Acceptance scenarios**:

1. **Given** identical gold mentions, **when** factuality systems are compared, **then** all classes, per-class results and
   supporting-evidence results are reported.
2. **Given** a claimed evidence or decision mechanism, **when** its core component is ablated, **then** both the public
   primary outcome and a mechanism-specific confusion diagnostic are recomputed.
3. **Given** predicted factuality output, **when** exported, **then** class probabilities, evidence spans, node IDs and
   provenance are present; missing evidence is not replaced by a fabricated default.

### RS-004 — Measure downstream error cost (Priority: P1)

The system can quantify the marginal and interaction effects of identity, relation and factuality quality on credible
graph consumers using the same documents, queries, candidates and checkpoints.

**Why this priority**: Component scores alone do not establish whether construction improvements matter to use cases.

**Independent test**: Run a pre-registered same-instance factorial with standard ranking metrics, graph-dependence
controls, credible baselines and paired inference.

**Acceptance scenarios**:

1. **Given** fixed queries and candidate ordering, **when** one graph-quality factor changes, **then** every other consumer
   input and the checkpoint remain identical.
2. **Given** a consumer included in conclusions, **when** tested against text-only/frequency controls and graph
   perturbations, **then** predictive validity and graph dependence are separately established.
3. **Given** positive, null or negative interactions, **when** reported, **then** all are retained with uncertainty, noise
   floor and the exact boundary of the supported claim.

## Requirements

### Functional Research Requirements

- **FR-001**: The project MUST deliver three independently testable method studies: identity, relation and factuality.
- **FR-002**: The project MUST deliver one same-instance system study of upstream error propagation and consumer
  dependence; it MUST NOT invent a fourth extraction method merely to fill the chapter.
- **FR-003**: Every component MUST export an immutable, typed, ID-aligned artifact usable by the next stage and by the
  system evaluation.
- **FR-004**: Every component study MUST separate gold-upstream component isolation from predicted-upstream end-to-end
  evaluation.
- **FR-005**: Every method claim MUST identify a falsifiable mechanism, a public primary outcome, at least one core
  ablation and at least one negative control.
- **FR-006**: Every primary comparison MUST run representative strong baselines under the same manifest, candidate
  universe, input assumptions and evaluator; paper numbers from incompatible protocols are context only.
- **FR-007**: Randomized primary anchors and proposed methods MUST use matched seeds. Statistical inference MUST cluster
  at document level and preserve all dependent instances within a sampled document.
- **FR-008**: The system evaluation MUST use standard MRR/Hit@k metrics, pre-registered contrasts, paired uncertainty,
  multiple-comparison control and explicit graph-dependence checks.
- **FR-009**: Results MUST be traceable to code, configuration, command, data/manifest/evaluator hashes, checkpoint,
  per-instance predictions and immutable raw metrics.
- **FR-010**: Final-valid outputs MUST NOT be used to select method structure, hyperparameters, thresholds, epochs or
  claims. Historical access MUST be disclosed.
- **FR-011**: A failed candidate mechanism MUST retain its result identity. It MAY be replaced by a substantively
  different design, but MUST NOT be relabeled, tuned without bound or rescued by changing the primary outcome.
- **FR-012**: Existing public implementations MUST be reused when available; local adaptations MUST preserve upstream
  provenance and document fidelity gaps.
- **FR-013**: Cross-dataset mappings MUST verify document, mention, event, offset and label identities and fail on
  duplicates, missing required IDs or ambiguous mappings.
- **FR-014**: Extension data MUST live in metadata; the public `EventNode` schema MUST NOT gain task-specific fields.
- **FR-015**: Every GPU method run MUST be preceded by a locally passing implementation gate and a frozen experiment
  contract. Additional random seeds require explicit user authorization.

### Quality and Evidence Requirements

- **QR-001**: Ch1–Ch3 primary outcomes MUST each exceed a frozen primary anchor and another strong, distinct method
  family under one protocol.
- **QR-002**: For randomized primary comparisons, the mean improvement MUST be positive, at least two of three matched
  seed differences MUST be positive, and the document-cluster paired-bootstrap 95% confidence-interval lower bound MUST
  exceed zero.
- **QR-003**: Mandatory secondary metrics MUST satisfy prospectively registered non-inferiority guardrails. Aggregate
  improvements MUST NOT hide a relation family or rare factuality group collapsing to an unusable state.
- **QR-004**: Confirmatory comparisons MUST report absolute effect, uncertainty, matched-seed values and sample standard
  deviation. Statistical significance alone is insufficient; the minimum meaningful effect and power assumptions MUST
  be recorded before the run.
- **QR-005**: Ch4 consumers used for substantive conclusions MUST beat strong protocol-aligned controls and pass a graph
  dependence test. Consumer-by-quality effects may take any sign when these prerequisites hold.
- **QR-006**: All required code checks, contract checks and CPU end-to-end smoke tests MUST pass before result promotion.
- **QR-007**: Negative and null results MUST remain in the evidence record; diagnostics cannot substitute for failed
  primary outcomes.

### Key Entities

- **Event mention**: A text occurrence with stable document, sentence and span identity.
- **Event occurrence**: A cluster of mentions referring to one real-world event.
- **Event node**: The schema-stable graph representation of an occurrence; task outputs reside in metadata.
- **Relation edge**: A typed, directed relation with endpoint IDs, probabilities, provenance and optional evidence.
- **Factuality assertion**: Label probabilities and evidence spans linked to a stable event-node identity.
- **Evaluation unit**: A document cluster containing all dependent mentions, pairs or downstream queries sampled together.
- **Stage bundle**: Immutable protocol, predictions, raw metrics and status plus externally verifiable provenance.
- **Consumer**: A model that reads a fixed serialization of event-graph information to rank fixed candidates.

## Edge Cases and Failure Behavior

- If an official test set has no accessible gold or submission channel, the project MUST use a declared public protocol
  and MUST NOT present it as the hidden official test.
- If a public method uses a different split, candidate set, input premise or scorer, its paper score MUST NOT enter a
  direct superiority claim.
- If an evaluation set cannot provide adequate power for the declared meaningful effect, the plan MUST add legitimate
  evidence, strengthen the method or narrow the claim; it MUST NOT relax inference after seeing results.
- If gold auxiliary information leaks the target, it MAY define an oracle upper bound but MUST NOT count as a deployable
  method input.
- If upstream output is missing or incompatible, downstream execution MUST stop. Gold proxies MUST NOT masquerade as
  predicted arms.
- If a consumer ignores graph input, its quality-factor effects MUST NOT support a graph-sensitivity conclusion.
- If infrastructure fails without returning metrics and all identities are unchanged, an exact retry MAY occur and MUST
  be logged. Once any result is observed, changing the run forfeits the original confirmatory identity.
- If a mechanism fails, the chapter requirement remains open. Scope reduction is allowed only through a prospective,
  versioned amendment backed by feasibility evidence and explicit user/adviser approval.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All three method studies satisfy QR-001 through QR-004 on their standard public primary outcomes.
- **SC-002**: The identity study reports the standard coreference metric family and passes its frozen primary and
  guardrail criteria.
- **SC-003**: The relation study reports causal, subevent and temporal precision/recall/F1 and passes its frozen primary
  and guardrail criteria.
- **SC-004**: The factuality study reports the full public class set, macro and per-class results, evidence results and
  passes its frozen primary and guardrail criteria.
- **SC-005**: The system study completes the full same-instance intervention matrix or prospectively justified equivalent,
  establishes consumer validity and graph dependence, and reports pre-registered main/interaction effects with corrected
  paired inference.
- **SC-006**: Every thesis table entry can be independently traced to one immutable bundle and recomputed from its raw
  predictions with the frozen evaluator.
- **SC-007**: Cross-stage document/query IDs have no duplicate, missing or silently dropped required instances.
- **SC-008**: Full tests, lint and CPU end-to-end smoke checks pass at every promoted code identity.
- **SC-009**: Thesis reviewers can identify one coherent research question linking all chapters, while each method study
  remains independently falsifiable and does not rely on another proposed method being successful.

## Scope Boundaries

- No new human labels, preference labels or manual sample selection may enter training, model selection or primary
  evaluation.
- Closed models, multi-agent systems, finance applications, patents, the archived TKG line, generative extraction/RL and
  unrelated cross-dataset expansion are outside the critical path.
- Larger backbones, additional datasets and efficiency improvements are allowed only as plan choices; they cannot replace
  a failed mechanism claim or create an unfair baseline comparison.
- Thesis prose production is outside the implementation plan; evidence, figures, tables and reproducible artifacts are in
  scope.

## Assumptions and Dependencies

- Public MAVEN-family assets can be used under their licenses, but exact version and cross-dataset ID coverage must be
  verified by the plan.
- The project has lawful access to CPU development resources and approved remote GPU resources.
- The applicable university/discipline degree standard depends on degree type and admission year and must be recorded in
  the research plan; the project quality criteria above remain the internal target unless this specification is amended.
- Method families, model architecture, baseline roster, data augmentation, experiment ordering and compute budget are
  intentionally **not assumptions of this specification**. They are revisable design decisions.
