# Tasks: EKG Thesis Research Program

**Input**: [`SPEC.md`](SPEC.md), [`RESEARCH_PLAN.md`](RESEARCH_PLAN.md)
**Current executable scope**: R1 v6.2 new-family admission. C-13–C-21 are complete: A4 is rejected on novelty;
D4 waits for real cross-fit predicted posteriors; C5 C-22 waits for an idle 4090, snapshot-path recheck, generation and
blind review. The v6.1
typed-cue / pair-evidence / role-compatibility phases below are historical closed failures, not runnable backlog.

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

## Phase 3b — R1 v6.2 new-family admission

**Purpose**: Respond to the failed first cycles by finding materially different, literature-grounded mechanisms and
closing their data/protocol/code/power prerequisites before any new GPU experiment.

- [x] **T048 [P] [RS-001–RS-003]** Audit primary papers and official code for exact-task fit, mechanism overlap,
  runnable status and protocol gaps → `literature_refresh.json` records paper/code evidence and rejects renamed old
  families.
- [x] **T049 [RS-003]** Measure D4 structural-input identity and coverage by relation family → 2,913 documents /
  73,939 mentions align; only 291 documents have held-out predictions and causal-only incidence is reported separately.
- [x] **T050 [RS-002]** Audit A4 formal-rationale assets and official LLMERE partition behavior → direct-pair coverage
  is corrected to 100%, two-hop retention is measured, and the direction is rejected because nearby work preempts the
  proposed scientific claim.
- [x] **T051 [RS-001]** Measure both C5 shortcut directions, source pools and prospective exact-test power → high-sim
  false merges and low-sim missed true links are both bound; target power is at least 80%.
- [x] **T052 [RS-003]** Freeze the five-fold D4 cross-fit plan and posterior schema → train/selection/evaluation are
  pairwise disjoint, every FACT document is evaluated exactly once, and missing predictions remain fail-fast.
- [x] **T053 [RS-001]** Freeze the 100-item C5 generation sample, blind-review rubric and thresholds → generator and
  classifier runs remain unauthorized until the one-shot generation audit exists.
- [x] **T059 [RS-003]** Implement the D4 causal-posterior dump adapter and exhaustive fail-fast validation → targeted
  tests and the complete local gate pass; no relation model is trained and no cross-fit predictions are fabricated.
- [x] **T060 [RS-001]** Implement the frozen C5 generation-request, output-validation, blind-review and threshold-scoring
  harness → targeted tests and the complete local gate pass; no generator or classifier is run.
- [x] **T061 [RS-001]** Freeze the single open generator, deterministic decoding, 100 requests and no-repair GPU runner
  → local tests and hashes pass; no model is called.
- [ ] **T062 [RS-001]** After the exact 4090 command is disclosed, generate the 100 frozen edits once and preserve raw
  successes/failures → currently blocked by non-idle GPUs and an interrupted snapshot-path check; no prompt repair,
  selective rerun or classifier training; human blind review remains separate.

**Checkpoint**: D4 and C5 have conditional design admission, not method effectiveness. A4 has no admitted phase.
T059 only closes a code prerequisite; D4 remains input-blocked until five real evaluation dumps exist. T060/T061
likewise cannot pass C5's generation-quality gate without T062's 100 actual edits and human blind-review decisions.

## Phase 3c — D4 single-chapter execution queue

**Purpose**: Follow the author's first-principles, one-chapter-at-a-time instruction. C5 T062 remains pending but is
not active while this queue advances.

- [x] **T063 [P] [RS-003]** Freeze D4's final target, mandatory conditions, intermediate metrics and error log →
  `results/PHASE_R1.md` §25 distinguishes the minimum baseline win from the +.030 meaningful target and corrects the
  unsupported attribution of two project diagnostics to the MAVEN-FACT paper.
- [x] **T064 [RS-003]** Implement a hash-bound D4 relation cross-fit runner without weakening the P1 trainer binding →
  train+selection-dev are the only materialized training records, evaluation appears only in posterior inference,
  official-joint recipe or `71be7419…` backbone drift fails before CUDA, and targeted plus complete local gates pass.
- [x] **T065 [RS-003]** Disclose and run one bounded 4090 CUDA smoke for the cross-fit train→causal checkpoint→posterior
  path → gpu-4090 GPU1 completed in about 32 seconds; metadata says CUDA, 5,198 exhaustive posterior rows and all
  required artifacts independently rehash, and the smoke score is explicitly excluded from recipe selection.
- [x] **T066 [RS-003]** Generate all five seed-13 relation cross-fit posterior dumps → all five immutable run
  records completed with exact 2,913-document/2,532,394-pair coverage and independently verified artifact hashes.
- [x] **T067 [RS-003]** Aggregate and quality-check the five posterior dumps → coverage/no-gold and pooled causal
  F1 `.308141` passed, but multiclass Brier `.068750` was worse than the evaluation-prevalence no-skill `.041427`;
  status is `quality_gate_failed` at the input-probability layer, not a D4 mechanism result.
- [x] **T067a [RS-003]** Run the preregistered scalar-temperature calibration cycle → argmax/F1 remained exactly
  `.308141` and Brier improved `.068750 → .064155`, but still failed the `< .0414265581` gate; the complete negative
  report and five calibrated sidecars remain preserved.
- [x] **T067b [RS-003]** Test the materially different class-weight loss correction on selection-dev only → Brier fell
  `.068231 → .041942`, but remained above no-skill `.041427`; causal F1 fell `.308297 → .279911`, so the frozen gate
  rejected it without reading or transforming evaluation artifacts.
- [x] **T067c [P] [RS-003]** Return to primary literature and test a third probability/decision mechanism on untouched
  selection documents → full Dirichlet Brier `.034240` beat no-skill `.040057` by `.005817`; cost-aware F1 `.300990`
  passed while plain argmax collapsed to `.081921`, so all preregistered holdout gates passed without evaluation access.
- [ ] **T067d [RS-003]** Run the separately frozen C-25R3 formal input gate once → refit each Dirichlet map on its full
  selection fold, publish immutable natural-posterior sidecars, then read evaluation gold once and require Brier at
  least `.0027` below no-skill plus cost-aware F1 ≥`.300`; no refit or threshold change after the formal result.
- [ ] **T068 [P] [RS-003]** Freeze the predicted-causal D4 phase contract after T067d passes → exact three arms,
  project-defined consistency mediators, rare-class floors, bootstrap inference and stop/second-cycle branches are
  fixed before method results exist.
- [ ] **T069 [RS-003]** Implement the uncertainty-gated causal residual and rewiring control → no/low-confidence edges
  drive the residual to zero, all arms keep identical base/budget, and the complete local gate passes.
- [ ] **T070 [RS-003]** Run a bounded one-fold CUDA smoke of all three D4 arms → forward/backward/evaluator/mediator
  outputs close without entering the thesis table.
- [ ] **T071 [RS-003]** Run and score the five-fold, three-arm, seed-13 D4 experiment → pooled five-class macro-F1,
  per-class guardrails, paired document bootstrap, semantic consistency mediator and rewiring falsification are all
  published to the D4 result page; a failed first cycle triggers a materially new second design cycle, not chapter-wide
  abandonment.

**Checkpoint**: T071 is the first new D4 method-effectiveness result. Extra seeds remain separately authorized and
cannot start merely because the cross-fit folds ran in parallel.

## Phase 4 — C5 identity method (v6.1 historical failure; do not rerun)

- [x] **T025 [RS-001]** Implement the C5 posterior/uncertainty sidecar, role-alignment residual, registered mediator,
  bundle exporter and fail-fast ID/schema tests → targeted tests and the complete local gate pass.
- [x] **T026 [RS-001]** Materialize C5 immutable preflight and replay official-joint, annealed no-argument and Qwen3
  argument-aware baselines → hashes, population and official coreference metrics independently validate.
- [x] **T027 [RS-001]** Run the registered seed-13 full/remove-core/hard-argument/permutation matrix after CPU/CUDA
  smoke → only the frozen treatment varies and no gold event-level argument enters a deployable arm.
- [x] **T028 [RS-001]** Score the C5 pilot with official MUC/B3/CEAFe/BLANC and the false-merge mediator → apply every
  single-seed gate without changing threshold, epoch, input or claim.
- [x] **T029 [RS-001]** T028 failed, so stop without extra seeds or final-valid access → immutable failed handoff emitted;
  the role-compatibility family is sealed.

## Phase 5 — A4 relation method (v6.1 historical failure; do not rerun)

- [x] **T030 [RS-002]** Implement pair evidence selection, retained/removed counterfactual forwards, registered
  mediator, exporter and full-candidate tests → targeted tests and the complete local gate pass.
- [x] **T031 [RS-002]** Materialize A4 immutable preflight and replay A3 fallback plus TacoERE adaptation → P1/A3/R1,
  candidate, evaluator, baseline predictions and metrics hashes independently validate.
- [x] **T032 [RS-002]** Run the registered seed-13 full/remove-core/non-evidence/no-constraint matrix after CPU/CUDA
  smoke → all arms preserve the complete candidate universe and differ only on registered variables.
- [x] **T033 [RS-002]** Score causal/subevent/temporal P/R/F1 and cross-sentence error mediator → apply primary,
  recall, family guardrail and negative-control gates without post-hoc pruning or thresholds.
- [x] **T034 [RS-002]** T033 failed, so stop without extra seeds or final-valid access → immutable failed handoff emitted;
  the pair-evidence family is sealed.

## Phase 6 — D4 factuality method (v6.1 historical failure; do not rerun)

- [x] **T035 [RS-003]** Implement typed cues, factorized logits/recomposition, flat-head control, cue permutation,
  registered confusion mediator and evidence exporter → targeted tests and complete local gate pass.
- [x] **T036 [RS-003]** Materialize D4 immutable preflight, revalidate accepted CLS/DMRoBERTa OOF predictions and
  build the leakage-free supporting-word OOF baseline → fold, source, code and metric identities validate.
- [x] **T037 [RS-003]** Run seed-13 five-fold full/remove-core/permutation after CPU/CUDA smoke → each of 2,913
  documents and 73,939 mentions receives exactly one evaluation prediction per arm with no fold leakage.
- [x] **T038 [RS-003]** Recompute pooled five-class/evidence metrics and registered confusions → apply primary,
  rare-class, evidence and negative-control gates without substituting diagnostics for macro-F1.
- [x] **T039 [RS-003]** T038 failed, so stop without extra seeds or final-valid access → immutable failed handoff emitted;
  the typed-cue family is sealed.

## Phase 7 — E3 event-prediction application

The former T040–T044 24-condition factorial, Holm family and frozen-vs-fine-tuned same-backbone design were withdrawn
by the author and are **not executable tasks**. Current Ch6 does not have to beat a method chapter.

- [x] **T054 [RS-004]** Freeze the reconstructed query/candidate evaluation unit and validate stable IDs → 1,908
  queries share one immutable candidate universe and no query edge leaks into the training graph.
- [x] **T055 [RS-004]** Close the gold/predicted upstream interface and reproduce random/frequency/project graph rows →
  every table row uses the same frozen evaluator and states its upstream identity.
- [x] **T056 [RS-004]** Transparently adapt and run the available public opponents → fidelity gaps, structural
  incompatibilities and non-comparable failure modes are reported instead of being claimed as wins.
- [x] **T057 [RS-004]** Export ranks/raw metrics and freeze the evidence-supported claim boundary → Table 6-2 and
  the graph-quality/downstream mismatch analysis are traceable in `results/PHASE_E.md`.
- [ ] **T058 [RS-004]** Run matched seeds only after explicit authorization → until then every Table 6-2 row remains
  labelled single-seed; no final claim silently treats it as confirmatory.

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
| RS-001; SC-002 | T013, T016, T017, T020, T023–T029, T048, T051, T053, T060–T062 | C5 |
| RS-002; SC-003 | T001–T011, T014, T018, T021, T023–T024, T030–T034, T048, T050 | A4 |
| RS-003; SC-004 | T015, T019, T022–T024, T035–T039, T048–T049, T052, T059, T063–T071 | D4 |
| RS-004; SC-005 | T023–T024, T054–T058 | E3 |
| FR-001–FR-005; SC-001 | T020–T039, T048–T058 | C5/A4/D4/E3 |
| FR-006, FR-012 | T013–T015, T020–T024, T026, T031, T036 | Baseline fidelity |
| FR-007; QR-001–QR-004 | T017–T024, T029, T034, T039, T051–T053, T058 | Matched seeds, power and inference |
| FR-008; QR-005 | T023–T024, T054–T058 | Consumer predictive validity |
| FR-009–FR-011; QR-007 | T001–T011, T023–T058 | Bundles and honest evidence |
| FR-013–FR-014 | T001–T005, T016, T023, T025, T035, T049, T052, T054, T059, T045 | ID/schema boundaries |
| FR-015; QR-006 | T004–T005, T009, T024–T026, T030–T031, T035–T036, T045, T048–T062 | Gates/auth |
| SC-006–SC-009 | T023–T024, T045–T058 | Reproduction/traceability acceptance |

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
- T025–T039 are completed historical failures and are not runnable; C-13–C-18/T048–T053 supersede their design queue.
- T048–T053, T059–T061 and T063–T064 are complete; T062 has not started and is inactive while D4 is the sole
  chapter queue. T065–T071 are declared in `EXPERIMENT_PLAN.md`; only T065 is next. A4 has no executable task.
- T054–T057 are complete; T058 waits for explicit matched-seed authorization. T045 waits for the intended final E3
  identity, not for the withdrawn factorial.
- Within method phases, baseline reproduction and engineering tests may run in parallel only when they do not
  expose confirmatory results early or share mutable experimental state.
