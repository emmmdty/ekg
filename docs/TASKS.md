# Tasks: EKG Thesis Research Program

**Input**: [`SPEC.md`](SPEC.md), [`RESEARCH_PLAN.md`](RESEARCH_PLAN.md)
**Current executable scope**: R1 baseline/input closure, factuality OOF anchors and cross-artifact review. P1/A3.6 are
closed; proposed-method implementation remains blocked.
Proposed-method implementation tasks are intentionally not generated until R1 approves their design and contracts.

## Format

`[ID] [P?] [Scenario] Description → verification`

- `[P]` means the task can run in parallel because it does not share mutable files or experimental dependencies.
- Scenarios map to `RS-001` identity, `RS-002` relation, `RS-003` factuality and `RS-004` system evaluation.
- A checked task requires its stated artifact and verification evidence, not only edited prose.

## Phase 1 — Restore protocol single sources

**Purpose**: Close the identified P1 traceability gaps before rebuilding the trust root.

- [x] **T001 [RS-002]** Replace the relation trainer's manifest/split shadow helpers with
  `ekg.core.protocol` and preserve non-string-ID fail-fast behavior in `scripts/train_supervised_relations.py`,
  `src/ekg/core/protocol.py` and `tests/core/test_protocol_split.py` → targeted protocol/trainer tests pass.
- [x] **T002 [RS-002]** Add `src/ekg/core/protocol.py` to the P1 code hash set in
  `scripts/build_p1_bundle.py` → bundle unit tests prove the dependency is covered.
- [x] **T003 [P] [RS-002]** Replace P1-controlled duplicate file-hash helpers with
  `ekg.core.stage_bundle.sha256_file` → targeted P1/script tests pass and no behavior changes.
- [x] **T004 [RS-002]** Run the complete local quality gate on the final code identity → `uv run pytest`,
  `uv run ruff check src tests scripts`, and `uv run ekg-smoke` all pass.
- [x] **T005 [RS-002]** Run `scripts/run_p1_local_gate.py` and review its diff → local protocol gate is PASS and any
  generated identity change is explained.

**Checkpoint**: Code identity is eligible for a new P1 trust root.

## Phase 2 — Close A3 without rewriting history

**Purpose**: Separate official-recipe reproduction differences from the failed A3 method family.

- [x] **T006 [RS-002]** Commit and push the validated code/docs as logical units → local/remote commit identities are
  recorded and worktree has no unintended changes.
- [x] **T007 [RS-002]** Rebuild the P1 trust root from the final commit and independently rehash it → new bundle validates
  externally and the old P1 remains immutable.
- [x] **T008 [RS-002]** Freeze the A3.6 four-arm command/config matrix using one seed and identical data/candidates/
  evaluator/backbone/budget → matrix review shows only the intended recipe variables differ.
- [x] **T009 [RS-002]** Present exact 4090 command, cwd, GPU selection check and expected artifacts to the user before
  launch → pre-run record exists; no long job starts implicitly.
- [x] **T010 [RS-002]** Run and score local recipe, rates-only, rates+coref-aux and rates+coref-aux+per-family-selection →
  four immutable outputs use the official evaluator; no old curve is recycled.
- [x] **T011 [RS-002]** Append actual results only to `docs/results/PHASE_A.md` and export an A3 `status=failed`
  relation fallback bundle → hashes, command, checkpoint location and final-valid ledger are complete.

**Checkpoint**: A3 is closed; recipe improvements, if any, are baseline reproduction rather than method credit.

## Phase 3 — R1 research-design review

**Purpose**: Produce evidence-backed plans without locking the specification to a solution.

- [x] **T012 [P]** Record degree type, admission year and the applicable university/discipline standard in the R1
  provenance artifact → official source/version/applicability are explicit; unknown values remain `null`.
- [x] **T013 [P] [RS-001]** Build the identity-study primary-paper and official-code matrix → at least three direct strong
  method families have split/input/scorer/code-fidelity fields.
- [x] **T014 [P] [RS-002]** Build the relation-study primary-paper and official-code matrix → official joint, 2025
  two-stage ERE, RESIJ and TacoERE/KnowQA coverage or documented replacement.
- [x] **T015 [P] [RS-003]** Build the factuality-study primary-paper and official-code matrix → official MAVEN-FACT,
  DMRoBERTa and structured modality/factuality coverage or documented replacement.
- [x] **T016 [RS-001]** Audit MAVEN-ERE/ARG/FACT document, event, mention, offset and role identities with fail-fast
  fixtures → full coverage/ambiguity report and version hashes; no silent mapping.
- [x] **T017 [P] [RS-001]** Generate prospective identity power/MDE analysis from frozen per-document anchor outputs →
  fixed RNG, raw power table, 80% target and minimum meaningful effect.
- [x] **T018 [P] [RS-002]** Generate prospective relation power/MDE analysis → same evidence requirements as T017.
- [x] **T019 [P] [RS-003]** Generate prospective factuality power/MDE analysis including rare-class limitations → same
  evidence requirements as T017 plus a legal evidence-strengthening path.
- [ ] **T020 [RS-001]** Write the identity causal design brief (treatment, mediator, outcome, negative control, ablations,
  guardrails, stop) → constitution/spec traceability review passes.
- [ ] **T021 [RS-002]** Write the relation causal design brief → same review, and inference preserves the full candidate
  universe.
- [x] **T022 [RS-003]** Write the factuality causal design brief → same review, and diagnostics cannot replace macro-F1.
- [ ] **T023** Run the cross-artifact consistency audit across constitution, SPEC, plan, tasks, phase contracts and result
  identities → every requirement maps to a task/test; no task adds an undeclared outcome.
- [ ] **T024** Freeze each approved method phase contract only after its R1 prerequisites and T023 pass → exact inputs,
  baselines, protocol hashes, promotion, stop, bundle and GPU commands exist; independent phases may be released in any
  evidence-supported order.

**Checkpoint**: R1 PASS releases one method phase. Candidate mechanisms may be replaced during R1 if evidence rejects
them; `SPEC.md` does not need amendment unless the outcome or quality requirement changes.

## Later Phases — Generated after R1

The following are dependency placeholders, not implementation tasks:

1. Identity method phase satisfying RS-001 and SC-002.
2. Relation method phase satisfying RS-002 and SC-003.
3. Factuality method phase satisfying RS-003 and SC-004.
4. Same-instance consumer factorial satisfying RS-004 and SC-005.
5. Reproduction/traceability acceptance satisfying SC-006 through SC-009.

Each phase's tasks will be generated from its frozen design brief and grouped so its component study is independently
testable. This prevents the task list from prematurely turning a current hypothesis into a permanent specification.

## Requirements Traceability

This matrix records coverage without pretending that future implementation details are already known.

| Specification coverage | Current task evidence | Later executable coverage |
|---|---|---|
| RS-001; SC-002 | T013, T016, T017, T020, T023, T024 | Identity method phase |
| RS-002; SC-003 | T001–T011, T014, T018, T021, T023, T024 | Relation method phase |
| RS-003; SC-004 | T015, T019, T022, T023, T024 | Factuality method phase |
| RS-004; SC-005 | T023, T024 | Consumer-factorial phase |
| FR-001–FR-005; SC-001 | T020–T024 | Three method phases + consumer phase |
| FR-006, FR-012 | T013–T015, T020–T024 | Baseline fidelity tasks in each method phase |
| FR-007; QR-001–QR-004 | T017–T022, T024 | Matched-seed, power, guardrail and inference tasks |
| FR-008; QR-005 | T023, T024 | Consumer validity, graph-dependence and factorial tasks |
| FR-009–FR-011; QR-007 | T001–T011, T023, T024 | Bundle/result/negative-evidence checks in every phase |
| FR-013–FR-014 | T001–T005, T016, T023 | ID/schema tests at each stage boundary |
| FR-015; QR-006 | T004, T005, T009, T024 | Local gates and run-authorization checks in every phase |
| SC-006–SC-009 | T023, T024 | Final reproduction/traceability acceptance phase |

T023 fails if any row has neither current evidence nor a generated later task. Placeholders may establish planned
coverage, but they cannot be checked complete until the corresponding executable tasks and verification artifacts exist.

## Dependencies and Parallel Opportunities

- T004 depends on T001–T003; T005 depends on T004.
- T006–T011 are sequential because each changes or consumes the trust root and experimental identity.
- T012–T019 are complete. T020–T022 may progress independently as each chapter closes its baseline/input/power blocker;
  no proposed method is released merely because its brief exists.
- T017–T019 may run in parallel after their required per-document outputs are verified.
- T020–T022 depend on the corresponding literature and power tasks; they may run in parallel with one another.
- T023 depends on T012–T022; each T024 contract depends on T023 and that method's prerequisites, not on a fixed chapter
  order.
- Within future method phases, baseline reproduction and engineering tests may run in parallel only when they do not
  expose confirmatory results early or share mutable experimental state.
