# Tasks: EKG Thesis Research Program

**Input**: [`SPEC.md`](SPEC.md), [`RESEARCH_PLAN.md`](RESEARCH_PLAN.md)
**Current executable scope**: R1 baseline/input closure, factuality OOF anchors and cross-artifact review. P1/A3.6 are
closed; proposed-method implementation remains blocked.
Method-phase tasks are generated from the frozen R1 design contracts; they remain unchecked until their stated
implementation and verification evidence exists.

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
- [x] **T020 [RS-001]** Write the identity causal design brief (treatment, mediator, outcome, negative control, ablations,
  guardrails, stop) → constitution/spec traceability review passes.
- [x] **T021 [RS-002]** Write the relation causal design brief → same review, and inference preserves the full candidate
  universe.
- [x] **T022 [RS-003]** Write the factuality causal design brief → same review, and diagnostics cannot replace macro-F1.
- [x] **T023** Run the cross-artifact consistency audit across constitution, SPEC, plan, tasks, phase contracts and result
  identities → every requirement maps to a task/test; no task adds an undeclared outcome.
- [x] **T024** Freeze each approved method phase contract only after its R1 prerequisites and T023 pass → A4/D4 frozen
  with exact inputs, baselines, protocol bindings, promotion, stop, bundle and GPU commands; C5 deliberately remains
  unapproved and unbound because E10 found ACCI not runnable, so it awaits an author-selected replacement family.

**Checkpoint**: R1 PASS releases one method phase. Candidate mechanisms may be replaced during R1 if evidence rejects
them; `SPEC.md` does not need amendment unless the outcome or quality requirement changes.

## Phase 4 — C5 identity method

- [ ] **T025 [RS-001]** Implement the C5 posterior/uncertainty sidecar, role-alignment residual, registered mediator,
  bundle exporter and fail-fast ID/schema tests → targeted tests and the complete local gate pass.
- [ ] **T026 [RS-001]** Materialize C5 immutable preflight and replay official-joint, annealed no-argument and Qwen3
  argument-aware baselines → hashes, population and official coreference metrics independently validate.
- [ ] **T027 [RS-001]** Run the registered seed-13 full/remove-core/hard-argument/permutation matrix after CPU/CUDA
  smoke → only the frozen treatment varies and no gold event-level argument enters a deployable arm.
- [ ] **T028 [RS-001]** Score the C5 pilot with official MUC/B3/CEAFe/BLANC and the false-merge mediator → apply every
  single-seed gate without changing threshold, epoch, input or claim.
- [ ] **T029 [RS-001]** If T028 passes, stop for explicit extra-seed authorization; if authorized, run matched seeds,
  paired inference and one sealed final-valid evaluation → emit immutable pass/failed handoff either way.

## Phase 5 — A4 relation method

- [ ] **T030 [RS-002]** Implement pair evidence selection, retained/removed counterfactual forwards, registered
  mediator, exporter and full-candidate tests → targeted tests and the complete local gate pass.
- [ ] **T031 [RS-002]** Materialize A4 immutable preflight and replay A3 fallback plus TacoERE adaptation → P1/A3/R1,
  candidate, evaluator, baseline predictions and metrics hashes independently validate.
- [ ] **T032 [RS-002]** Run the registered seed-13 full/remove-core/non-evidence/no-constraint matrix after CPU/CUDA
  smoke → all arms preserve the complete candidate universe and differ only on registered variables.
- [ ] **T033 [RS-002]** Score causal/subevent/temporal P/R/F1 and cross-sentence error mediator → apply primary,
  recall, family guardrail and negative-control gates without post-hoc pruning or thresholds.
- [ ] **T034 [RS-002]** If T033 passes, stop for explicit extra-seed authorization; if authorized, run matched seeds,
  paired inference and one sealed final-valid evaluation → emit immutable pass/failed handoff either way.

## Phase 6 — D4 factuality method

- [ ] **T035 [RS-003]** Implement typed cues, factorized logits/recomposition, flat-head control, cue permutation,
  registered confusion mediator and evidence exporter → targeted tests and complete local gate pass.
- [ ] **T036 [RS-003]** Materialize D4 immutable preflight, revalidate accepted CLS/DMRoBERTa OOF predictions and
  build the leakage-free supporting-word OOF baseline → fold, source, code and metric identities validate.
- [ ] **T037 [RS-003]** Run seed-13 five-fold full/remove-core/permutation after CPU/CUDA smoke → each of 2,913
  documents and 73,939 mentions receives exactly one evaluation prediction per arm with no fold leakage.
- [ ] **T038 [RS-003]** Recompute pooled five-class/evidence metrics and registered confusions → apply primary,
  rare-class, evidence and negative-control gates without substituting diagnostics for macro-F1.
- [ ] **T039 [RS-003]** If T038 passes, stop for explicit extra-seed authorization; if authorized, run matched seeds,
  paired inference and one sealed final-valid evaluation → emit immutable pass/failed handoff either way.

## Phase 7 — E3 same-instance consumer factorial

- [ ] **T040 [RS-004]** Freeze reconstructed query/candidate evaluation units and validate C5/A4/D4 bundle adapters →
  all 24 base conditions have identical IDs and no gold proxy masquerades as predicted input.
- [ ] **T041 [RS-004]** Reproduce random/frequency/text-only/graph consumers and same-backbone frozen/fine-tuned
  controls → strong graph arm passes predictive validity before quality effects are inspected.
- [ ] **T042 [RS-004]** Run graph/no-graph or gold/permuted dependence controls → at least one conclusion-bearing
  consumer passes its registered graph-dependence test above its noise floor.
- [ ] **T043 [RS-004]** Run the 2×2×3×2 same-instance factorial and paired document bootstrap with Holm correction →
  fixed queries, candidates and checkpoints yield all registered marginal and interaction contrasts.
- [ ] **T044 [RS-004]** Export ranks/raw metrics/status and choose the evidence-supported Ch4 claim boundary → positive,
  null and negative effects remain in one immutable E3 handoff.

## Phase 8 — H2 reproduction and thesis acceptance

- [ ] **T045** Re-run full tests/lint/smoke plus cross-bundle ID/hash/evaluator checks at every promoted identity →
  no missing instance, unchecked schema drift or unrecomputable metric remains.
- [ ] **T046** Recompute each intended thesis table from immutable raw predictions and frozen evaluators → every entry
  maps to one bundle/commit/config/checkpoint and all failed/null evidence identities remain visible.
- [ ] **T047** Audit the four-chapter research-question closure and independent falsifiability → SC-001–SC-009 receive
  pass/failed evidence without adding a new outcome or silently lowering the specification.

## Requirements Traceability

This matrix records coverage without pretending that future implementation details are already known.

| Specification coverage | Current task evidence | Later executable coverage |
|---|---|---|
| RS-001; SC-002 | T013, T016, T017, T020, T023–T029 | C5 |
| RS-002; SC-003 | T001–T011, T014, T018, T021, T023–T024, T030–T034 | A4 |
| RS-003; SC-004 | T015, T019, T022–T024, T035–T039 | D4 |
| RS-004; SC-005 | T023–T024, T040–T044 | E3 |
| FR-001–FR-005; SC-001 | T020–T024, T025–T044 | C5/A4/D4/E3 |
| FR-006, FR-012 | T013–T015, T020–T024, T026, T031, T036 | Baseline fidelity |
| FR-007; QR-001–QR-004 | T017–T024, T029, T034, T039 | Matched seeds, power and inference |
| FR-008; QR-005 | T023–T024, T040–T044 | Consumer validity and factorial |
| FR-009–FR-011; QR-007 | T001–T011, T023–T024, T025–T047 | Bundles and honest evidence |
| FR-013–FR-014 | T001–T005, T016, T023, T025, T035, T040, T045 | ID/schema boundaries |
| FR-015; QR-006 | T004–T005, T009, T024–T026, T030–T031, T035–T036, T040, T045 | Gates/auth |
| SC-006–SC-009 | T023–T024, T040–T047 | Reproduction/traceability acceptance |

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
- T025/T030/T035 are independently runnable after T024; each following chapter task is sequential within that chapter.
- T040 waits for C5/A4/D4 immutable handoffs or their explicit fallback component bundles; T045 waits for E3.
- Within method phases, baseline reproduction and engineering tests may run in parallel only when they do not
  expose confirmatory results early or share mutable experimental state.
