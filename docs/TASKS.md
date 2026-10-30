# Tasks: EKG Thesis Research Program

**2026-10-30 / T087当前切片完成**：作者确认的九张已发表成绩表见
[九表导航](research/20261030_data_first_scope/NINE_TABLES.md)，原分只在R1 §25.152，
来源R129。无代码照样收录可核原分论文，不启动复现/训练/模型实现。整条科研任务
不据此标done，仍同一队列；后续按作者验收接续。

**2026-10-30 / T087最新覆盖**：同一C41-A-R审查切片完成CDCR三语料/三方法章的
外部条件、原表、LLM与公开发布件取舍，入口
[EXTERNAL_READINESS](research/20261030_data_first_scope/EXTERNAL_READINESS.md)，证据R1
§25.151。作者本轮要求暂不复现baseline；下一框架内方法设计，无模型/训练或旧R122。
此处只更新接续，不将整条科研任务标done，不新增队列。


**10-27当前接续覆盖**：R119一手源码、R120完整原train联合标签与独立三维网格核验、
R121精确代数/estimand裁决已完成，证据及限制只见R1 §25.142–§25.144。普通full-Q
读出直接报创新的版本拒绝；one-hot极限不能否定所有软结构。当前同队C41-A-R/T087
进入R122的D-only vs full-Q/product/aux-only/pair归属负控设计裁决（§25.145）；不重做
人口、toy、旧模型或CE。新方法/训练尚未准入，UAIGR全文缺口未冒充闭合，O1–O4
仍未完成。Goal工具此前仍paused；按作者继续指令执行，不冒称自动active或新建Goal。

**Input**: [`SPEC.md`](SPEC.md), [`RESEARCH_PLAN.md`](RESEARCH_PLAN.md)
**Current executable scope**: the author delegated scientific route selection and improvement decisions on
2026-10-08. C-35–C-40/G-22 now govern root-cause diagnostics, GitHub skills, primary research, implementation,
and frozen seed-13 validation on the existing MAVEN tasks. T073–T080 are historical completed/cancelled work;
ESC is no longer a mandatory predecessor. Old sealed failures and resource/validity boundaries remain intact.

## Format

**2026-10-27 / T087最新覆盖**：R117官方SERE来源/纯检索器回放、R118原train结构
规则与独立edge-join核算完成；硬结构蕴含版本拒绝，结果与限制R1 §25.141。C41-A-R
仍wip，当前R119同见证联合可靠性机制审查（§25.142），只按主表§4执行。不得将
该数据/协议否决当方法效果FAIL或正向贡献；无新模型/额外seed/final-valid许可。

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
- [x] **T067d [RS-003]** Run the separately frozen C-25R3 formal input gate once → five immutable natural-posterior
  sidecars were published before any gold access, then evaluation gold was read once over the exact
  2,913 docs / 2,532,394 pairs: Brier `.03513538` beat no-skill `.04142656` by `.00629118` and cost-aware F1
  `.30602311` cleared `.300`, so the gate passed; hard F1 did not improve over raw `.30814055` (−`.00211744`),
  and the plain-argmax ablation collapsed to `.07912232`. Maps, weights and thresholds are frozen from here.
- [x] **T068 [P] [RS-003]** Freeze the predicted-causal D4 phase contract after T067d passes →
  `docs/phases/PHASE_D4_predicted_causal_residual.md` fixes the three arms (full / base / degree-, direction-,
  subtype- and confidence-preserving rewiring), the frozen edge construction (`argmax w_k p_k`, confidence is the
  natural posterior, zero edges imply an exactly zero residual), both project-defined mediators with numerator,
  denominator and aggregation, the rare-class floors (PS− ≥`.352456`, Uu ≥`.166850`), 10,000 document-cluster
  paired bootstrap resamples and the stop/second-cycle branches — all before any method result exists.
- [x] **T069 [RS-003]** Implement the uncertainty-gated causal residual and rewiring control → no/low-confidence edges
  drive the residual to zero, all arms keep identical base/budget, and the complete local gate passes.
- [x] **T070 [RS-003]** Run a bounded one-fold CUDA smoke of all three D4 arms → forward/backward/evaluator/mediator
  outputs close without entering the thesis table.
- [x] **T071 [RS-003]** Run and score the five-fold, three-arm, seed-13 D4 experiment → pooled macro-F1 came out
  base `.543166`, full `.540671`, rewired `.532591`; the paired document-cluster bootstrap put `full - base` at
  `-.002495` (CI `[-.015608, +.010516]`) and `full - rewired` at `+.008080` with a CI crossing zero, so four of the
  five necessary gates failed and the mechanism is not effective. Coverage hit 2,913 documents / 73,939 mentions
  exactly and no gold edge reached a model arm.
- [x] **T071b [RS-003]** Re-run the same three arms with the document-packing rule repaired → the repair's own
  rationale is falsified: base moved by `.000028` (`.543166` -> `.543138`) across 910 and 1,248 optimiser steps per
  epoch, so the step count is not the source of its `.010829` gap to the anchor. `full` rose to `.549878`, but the
  configuration change alone moved it `+.009207` — more than the `+.006740` full-minus-base effect in the better of
  the two runs — so the effect sits below the configuration noise floor. Both runs leave the registered consistency
  mediators pointing the wrong way, and G-18 remains the registered result.
- [x] **T072 [RS-003]** Run the official MAVEN-FACT EFD relation hookup with gold and frozen predicted structures →
  ten fold-runs complete with exact 2,913-document / 73,939-mention OOF coverage; gold does not outperform predicted
  under paired document bootstrap. The result is FR-016(b), gold is non-deployable, and neither row enters a gate.

**Checkpoint**: T071 is the first new D4 method-effectiveness result. Extra seeds remain separately authorized and
cannot start merely because the cross-fit folds ran in parallel.

## Phase 3d — Public-paper comparability uplift

**Purpose**: Convert external-method evidence into directly auditable same-protocol rows without mistaking a
single-seed transparent adaptation for a reproduction of a published result.

- [x] **T073 [P] [RS-001–RS-003]** Freeze the P (published reference) / V (original-benchmark fidelity) /
  U (unified-protocol) registry, seven required provenance fields, execution order and forbidden claims →
  `COMPARABILITY_PLAN.md` is linked from the executable main table; no experiment score is changed.
- [x] **T074 [RS-001]** Run the EasyECR Global-Local Topic transparent adaptation once on the frozen 291-document
  coreference unit → first hash-split the 2,622 P1 train documents into a 2,331-document train and a 291-document
  selection-dev, so evaluation is untouched; an isolated-venv import/one-batch smoke precedes fixed-seed-13
  training, project official MUC/B³/CEAFe/BLANC recomputation, raw clusters, upstream/patch hashes and a complete
  FR-016(b) record. The 2,331-vs-2,622 train delta is disclosed; any environment, identity or coverage failure is
  preserved as the named blocker rather than repaired by reimplementation. Completed G-19 evidence:
  `results/PHASE_R1.md` §25.28.
- [ ] **T075 [RS-002] — CANCELLED by author (2026-10-02), not backlog.** The planned LLMERE recovery stop rule
  requires internal-dev target content; C-29.6 found a protocol blocker and the author chose no generation/scoring.
  LLMERE retains a named FR-016(b) availability row with no U score. Evidence: `results/PHASE_R1.md` §25.29.
- [x] **T076 [RS-001–RS-003]** Independently rebuild the relevant thesis rows from raw predictions and audit all claims
  → every P/V/U row has the seven provenance fields, FR-016 state and `single-seed / non-confirmatory` label; only
  same-chapter, same-unit U rows expose deltas, and every missing field is excluded from the main table.
  C-30 completed; LLMERE has no score to recompute. Evidence: `results/PHASE_R1.md` §25.29.

**Checkpoint**: G-19 contributes an auditable single-seed FR-016(b) adaptation; LLMERE contributes a named
availability blocker. No second scored row is claimed. Neither result establishes published-paper superiority.

## Phase 3e — Bounded research round (closed at admission, no model experiment)

- [x] **T077 [RS-001–RS-003] / C-31** Audit at most three mechanism cards → all three excluded with primary
  evidence; `no_admissible_candidate`, no contract or training. See `results/PHASE_R1.md` §25.30.
- [x] **T078 [RS-002] / C-31b** Record the author's one-benchmark authorization and ESC v0.9 evidence card →
  external E-layer scope is explicit and does not replace MAVEN U rows. See `results/PHASE_R1.md` §25.31.
- [x] **T079 [RS-002] / C-32a** Audit ESC source/split/candidates/scorer → audit completed with
  `protocol_blocked`, not protocol PASS. The retrospective narrows its rationale; no immutable E preflight,
  model, GPU or E score exists. See `results/PHASE_R1.md` §25.32–§25.33.
- [x] **T080 [RS-001–RS-003] / C-34** Review the blocked research round → source-backed corrections,
  synthetic CPU split checks, next-R0 constraints and an author decision card are complete.
  See `results/PHASE_R1.md` §25.33; C-32b/G-21/C-33 remain unstarted.

**Checkpoint**: This round established admission evidence, not mechanism effectiveness. The 2026-10-08
author delegation releases a new in-scope research queue; it does not reopen old experiment identities.

## Phase 3f — Delegated method recovery

- [x] **T081 [RS-001–RS-003] / C-35** Recompute error exchanges and isolate loss/input/decoder hypotheses
  → evidence distinguishes measured facts, refuted explanations and untested alternatives.
- [x] **T082 [RS-001–RS-003] / C-36** Install useful GitHub research skills into the project
  → pinned sources, preserved licenses, file hashes, precedence and applied diagnostics in `RESEARCH_SKILLS.md`.
- [x] **T083 [RS-001–RS-003] / C-37** Audit primary mechanisms and official code; agent selects next diagnostics
  → concrete feasible cards, rival predictions, strongest same-protocol controls, no unsupported novelty claims.
- [x] **T084 [RS-001–RS-003] / C-38** Implement frozen diagnostics and shared execution interfaces
  → real tiny-model training/reload/gradient/decoder tests passed on both machines; no new mechanism admitted.
- [ ] **T085 [RS-001–RS-003] / C-39, G-22** Freeze preflight and execute admitted seed-13 comparisons
  → CPU package/asset gates passed (§25.35); D4 CUDA smokes, ten seed-13 folds and frozen CPU collection
  completed (§25.37). C5 CUDA smoke completed (§25.38); full audit and A4 CUDA remain pending.
- [ ] **T086 [RS-001–RS-003] / C-40** Recompute actual improvements and make the next scientific decision
  → D4 head-control decision completed (§25.37): retain linear, reject this tanh5 route; no new method claim.
  A4/C5 pending. Main results, ablations/negative controls and explicit limitations govern further admission.
  C5 real-checkpoint CUDA smoke completed 2026-10-12 (average-cluster parity and six hashes PASS);
  the full decoder audit remains pending, authorized only on an empty 5090 GPU.
  Bounded occupancy waiting ended without an audit launch; no automatic watcher remains.
- [ ] **T087 [RS-001–RS-003] / C-41** In progress: chapterwise next-method R1 research (2026-10-12; C5 first)
  **R109 now complete:** fixed selected full checkpoint predicted the entire original train
  population without updates; actual exit0/GONE, bincount/sklearn independent replay passed.
  Results and limits R1 §25.130. Next R110: train-only lexical pair exposure by sentence locality
  over frozen full/joint dev predictions, plus nearest-neighbor mechanism/code review (§25.131).
  No new encoder/labels/seed; no automatic new method admission. Author resumed conversation;
  Goal API still paused, not represented as active.
  **2026-10-25 completed endpoints and verification:** R107 all three selected-checkpoint
  replays passed exact full-population classes/official-score parity, actual exit0/GONE. R108
  all pre-frozen contrasts, document CIs/error exchanges and explicit independent resampling
  completed; no confirmed gain/new contribution (authoritative table PHASE_A, R1 §25.129).
  Do not restart/sweep/reseed these runs. Next R109: frozen full checkpoint, complete original
  train population, no-grad native-three-class fit diagnosis; software/CPU/budget admission
  still to prepare (§25.130), no new method training. Goal active, scientific O1–O4 unmet.
  **2026-10-24 parallel GPU request:** published ERGO complete-graph and gamma0 controls are
  frozen within C41-A-R, not a second queue. Both actual CUDA preflights completed exit0/GONE,
  optimizer-resident max-dev and exact initial-parameter parity passed. R106 own budget/configs
  admitted; GPUs0/2 workers25466/25461 now train full20epochs seed13 alongside original GPU1
  worker13841. Await each complete run and independent controlled checkpoint replay/official
  paired comparison. No new seed/final-valid/5090/transfer; not novel method evidence (§25.128).
  **2026-10-24 resumed by author:** free primary 4090 GPUs verified; resume the existing ERGO
  cost decision in C41-A-R with a separate full4096 v3 primary-server config/contract. Three fixed
  train fixtures run independently on GPUs1/2/0, seed13 and two lr0 calls each; GPU3 retained.
  No repeated full CPU preparation, no epoch admission or new scientific result. See R1 §25.125.
  Goal API still reports old blocked; work follows the explicit resume instruction without a new
  replacement Goal or a false active-state claim. Fresh blocking audit starts on this resume.
  R102 all three original-input CUDA cost cases completed with exit0/GONE and mirrored hashes
  (R1 §25.125). R103 actual original-trainer CUDA production and optimizer-resident max-dev capacity both
  completed exit0/GONE with mirrored hashes (R1 §25.126). R104 measured budget and three
  comparators are frozen before scores; next execute the separate admitted primary-4090 full
  seed13/20epoch config, then independently reload/officially score and compare errors (§25.127).
  Original inputs/math remain; no extra seed, final-valid or checkpoint transfer.
  Actual training worker13841 is ALIVE in epoch1; no complete epoch score yet. Frozen
  comparison entrypoint is implemented/tested, waiting for the completed checkpoint verification.
  **2026-10-19 resource exit:** current independent CPU preparation is closed. Successful SSH
  checks still show both hosts occupied, no ERGO workers and no new CUDA cost outputs. The same
  resource dependency spans three Goal turns; the blocking audit is R1 §25.124. Thread Goal moves
  to blocked after handoff, while T087 remains wip and scientific outcomes unmet. Resume at the
  existing cost contract on a newly verified free GPU; no watcher, repeated smoke or new permission
  request for the already authorized cost scope.
  **2026-10-19 current override:** the author explicitly requested concrete experiment planning
  followed by actual CPU work while GPUs are unavailable, superseding the 10-18 stage-close-only
  limit. The existing master table/OKR now specify controls, ablations, guardrails, dependencies
  and failure branches. R100 cached-train direction/subtype residual analysis and conservation/
  set-based recomputation completed (R1 §25.122); no model calls, new score or admission. The thread
  Goal was created and verified active from current C41-A-R; no watcher. Next GPU action remains
  the existing bounded ERGO cost contract; full training and confirmation retain their gates.
  R101 fixed train case review, native annotation-definition and direct mechanism/source checks
  also completed (R1 §25.123). SemDI is availability-only, CaSR's pinned current tree has partial
  data only; neither is a newly runnable native baseline. No relabeling or generic semantic-module
  proposal was admitted. Independent CPU preparation is closed; do not fabricate more smoke tasks.
  **2026-10-16 current override:** the author confirmed the 4090 has recovered and requested
  project-wide OKRs, measurable scientific outcomes and top-down task decomposition.
  C41-R completed original-machine pins/initializer/manifests, source synchronization and untracked
  preservation plus real CPU torch tests (R1 §25.68); C41-B completed ten CUDA cost cases and five-arm accumulation/shape/budget closure (R1 §25.69);
  C41-A completed both design and production admission (R1 §25.70–§25.72, release51c27eb);
  C41-T/V completed all five valid endpoints and independent LOCAL/4090 official evaluation
  with identical reports. The fixed exact/pair-F1 candidate failed its scientific gates; stop it
  without a parameter/epoch search or extra seeds. Original mass failure is preserved; repaired
  mass completed under a separate float64-auxiliary identity, with the precision limitation disclosed.
  D4 own-train anchor replay/input visibility and source review completed; current binding template
  has no admitted candidate (R1 §25.83–§25.86), without a proposed training/effect claim. Formal
  current work is C41-A-R. Identity/MIL priors and native identifiability are closed (R1 §25.88); full-train CPU replay and independent official scoring closed, PID1657823 is GONE; current target template not admitted, context diagnosis also closed (§25.93); ERGO native capacity/source review closed (§25.95); transparent interfaces, original-4090 weights and cache-global inputs closed (§25.97); full-model CPU short cost closed (§25.99); PAD-only worst-case parity failed and stopped (§25.102); canonical full-padding CPU shapes closed (§25.105); unlabeled internal-dev inputs closed and bounded 5090 A4 cost explicitly authorized, staging/weights ready but no empty GPU; original-trainer toy and real CPU native/max-dev smoke closed (§25.111/§25.114), v2 input/evidence gates implemented but training unadmitted (§25.115); no epoch/training or GPU launch. No optimizer/model admission. ERGO remains availability preparation (§25.90). Scientific O1/O2 remain unmet; future D4 alternatives require new R1 evidence.
  2026-10-18 stage close requested by the author: no empty GPU. CUDA preflight and independent
  selected-checkpoint verification interfaces have CPU gate tests; actual CUDA/reload remains
  unverified (R1 §25.116–§25.117). The new v2_close review config keeps all admissions false.
  The existing 5090 cost permission remains valid; no watcher or new research starts this turn.
  The new 5090 migration adapter C41-S is deferred, not completed.
  Follow EXPERIMENT_PLAN §3.9 and the 10-16 C41 subtable; `research/20261016_project_okr.md`
  maps O1–O4/KRs to C5, D4, A4, conditional confirmation and final traceability tasks.
  R1 §25.66 records resource evidence; the 10-15 source ledger/candidate science remains valid.
  Preserve C5 → D4 → A4 and one active queue; chapter preparation may overlap long training.
  C5 now has admission for the frozen seed13 exploration only; no extra seeds, weight transfer,
  new 5090 authorization or E3 experiments follows.
  Earlier history below is retained and does not supersede the current override.
  → use reliable controls and observed errors to audit distinct mechanisms, runnable public implementations,
  deployable inputs, rivals, falsifiable predictions, strong comparisons, ablations/negative controls and power.
  A4/C5 GPU diagnostics are not a prerequisite for literature research; preserve one active task and all validity/
  resource boundaries. Work through C5 → D4 → A4; control recovery or a rejected candidate does not complete
  a chapter. No new mechanism or GPU training contract has been admitted; see
  `research/20261012_chapterwise_optimization.md` and `results/PHASE_R1.md` §25.38 onward.
  Author requested continued work until a verifiable breakthrough. The new window acts as the
  event-semantics/KG research lead (PI), with sequential method review and experiment ownership;
  follow `HANDOFF.md` role instructions and §0.3.5 without expanding resource authorization.
  Train factuality scope audits, the official-joint CPU cache, weak-observer deployment/geometry,
  the given-type control and its residual profile are complete (§25.39–§25.42).
  The weak observer route stops. The derived control improved all four official coreference metrics,
  with independent scores and paired counts verified; it is a known rule, not an admitted innovation.
  The 10-13 continuation completed the first-party matrix, train-label scope and frozen antecedent
  decision/oracle audit with independent official scoring (§25.43; implementation `a6d159d`).
  Gold-conditioned null repair exposes the main coverage, without deployable improvement or power.
  Ordinary newness/singleton heads and erasure-to-dummy are prior mechanisms, not admitted innovation.
  Next follow `research/20261013_c5_newness_admission.md`: audit train-only document-isolated
  scorer error-state inputs and selective/error-correction neighbors; close the distinct mechanism,
  power and ablation/negative-control rules before a method contract or training.
  Do not rerun completed exports or reuse historical pools/power as fresh admission evidence.
  T087 remains active; the existing 5090 decoder audit is separately authorized only on an empty GPU.
  On 2026-10-14 the author also authorized C41 original-joint cost and post-R1 five-arm seed-13
  training on an empty 5090, with each job at most one day; checkpoint transfers, longer jobs
  and additional seeds remain separately authorized. Full-train token/label parity and both
  original-model CPU cost fixtures completed (§25.59); common-bias and per-edge synthetic
  gradient diagnostics completed (§25.58/§25.60). Actual fixed-aux CPU gradients completed
  (§25.61): head/encoder connected, finite,
  parameters unchanged; no unique exact-method benefit demonstrated. Nonweight artifacts
  and executed sources were hash-verified on LOCAL and 5090.
  These checks do not establish deployed gains or admit method training.
  C-41 latest: original-joint full four-head CPU backward on both frozen chunk fixtures and
  nonreentrant checkpoint loss/all-gradient equality verified (§25.54); five-arm loss/endpoint
  design and pre-method conditional power assumption rebound to five completed controls (§25.55).
  LOCAL CPU-only synthetic objective boundary/precision/autograd audit and full-train
  label sparsity/uniform-prior risk diagnostic completed (§25.56–§25.57), without model
  loading or updates. Empty-pair NumPy mask failure was repaired under a new r2 namespace;
  the original failure/source are preserved. No deployment benefit is inferred.
  Original-model CUDA cost/parity completed on both fixtures after 4090 release (§25.62).
  Structured/real-optimizer cost probe is frozen (§25.63); its first CPU case failed a raw
  signed-zero byte invariant. Original failure/code/config/log remain sealed; r2 admits only
  zero-sign restoration after exact numeric equality, records native byte changes and audits
  all actual optimizer calls. Eleven corresponding CPU tests executed on 4090, complete
  original-model r2 CPU verification completed: all numeric values unchanged, actual moments
  allocated, native zero-sign changes recorded and restored. Ten CUDA cases still await empty
  GPUs, which are occupied again.
  Structured CUDA/optimizer headroom and the formal execution contract remain pending; no method
  admission or new deployment gain. Code/config/contract: original_joint_cost_20261013.
  Author reiterated actual metrics or overall-method innovation as the deliverable. A fixed
  bidirectional-score control completed with independent scores and did not beat the typed
  strongest control (§25.44); stop it without alpha/threshold repair. A train-only frozen
  null-head control completed with negative independently reproduced metrics (§25.45), with matched arms,
  fixed seed 13/epoch 10 and no updates to the original encoder/scorer. It is a known-mechanism
  control, not an admitted novelty claim; stop it without a parameter rescue. Joint-connectivity
  algebra is verified but not admitted (§25.46). The fixed forest posterior control finished without useful gain or supported attribution (§25.47);
  stop its action. The sealed-head decision-unit audit also completed without recovery (§25.48);
  old predictions replayed exactly. All four fixed-control routes stop. Next R1 examines learning
  with exact joint dependence (§25.49): toy wrong-edge gradient cancellation is verified against
  finite differences; full-train structural opportunities and type-block sizes are independently verified.
  Pinned joint first-dummy supervision blindness and full-model gradient connectivity are confirmed.
  The fixed legacy-versus-corrected pair-MLP adaptation completed and independently scored
  without gain (§25.50); stop its action. It is baseline engineering, not novelty.
  Covariance decomposition and total-mass rival are verified (§25.52); conditional power sensitivity
  is measured (§25.51), not an effect prediction or unknown-variance guarantee.
  Full-train original tokenizer/chunk census is complete (§25.53); reuse its fixed peak/worst
  inputs for actual single-GPU cost smoke when an authorized GPU is empty. Full-model budget/power/
  admission remain open. No contribution PASS.

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
- T048–T053, T059–T061 and T063–T072 are complete; T062 has not started and remains paused. T073 is complete;
  T081 → T082 → T083 → T084 → T085 → T086 is the current delegated recovery queue.
  T075 is cancelled and is not an active prerequisite.
- T054–T057 are complete; T058 waits for explicit matched-seed authorization. T045 waits for the intended final E3
  identity, not for the withdrawn factorial.
- Within method phases, baseline reproduction and engineering tests may run in parallel only when they do not
  expose confirmatory results early or share mutable experimental state.

**2026-10-26 R110闭合/接R111**：C41-A-R/T087仍wip。原dev完整词面×句距分层和独立12张native矩阵一致；最近邻裁决/数字见R1 §25.132。当前只原train同词面对异语境监督机会、去重复和最近邻审查（§25.133）；不是新方法准入，不重跑既有dev或模型。O1–O4未达。

**2026-10-26 R111闭合/接R112**：仍C41-A-R/T087；R111原train信号和独立SQL通过，普通匹配contrast创新表述因CNC最近邻被拒。主表下一为原作者内置unweighted CE已知强控制（R1 §25.134–§25.135），只一个固定配置，先CPU/实际CUDA/预算；无新训练/原创方法准入，无alpha/gamma/lr搜索或旧臂重起。

**2026-10-26 R112 CUDA闭合/接R113预算**：仍C41-A-R/T087。CE原机CPU/实际CUDA已过，exit0/GONE；当前仅已有成本入口一次cold/warm最大train lr0计时后裁完整预算（R1 §25.136/CE合同），不是新方法或训练已启动，不重复封存准备/旧三臂。

**2026-10-26 R113完整CE准入**：同C41-A-R/T087，实际CPU/CUDA/init/一次cost及完整预算都过（R1 §25.137）；下一按CE合同部署/全pin/空卡联核后执行唯一seed13/20epoch强控制。当前尚无epoch；不重复探针/旧臂或把已知CE当原创。完整后独立重载/五对照，O1–O4未满足。

**2026-10-26 CE实际CUDA运行中**：C41-A-R/T087唯一活动项；launcher1152477/train1152480，固定GPU1/seed13/20epoch。接续先核pipeline阶段/.exit/真实进程；成功后自动独立核分和五对照，失败即停，不重复启动。身份/快照/限制见R1 §25.138，当前未出完整分数，O1–O4未达。

**2026-10-27 CE全链完成覆盖**：CE固定训练、独立核分、五对照全部完成、exit0/GONE，当前无活动CE GPU任务。主指标/区间仅PHASE_A最新节，验收及57件双端归档见R1 §25.139。未证稳定收益/新方法价值，C41-A-R/T087科学目标仍wip，O1–O4未达；本次状态问题下无新训练，不重跑旧控制/探针或扩seed，新机制仍待R1准入。
