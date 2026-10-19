---
name: ekg-research-loop
description: Direct autonomous EKG experiment research when advancing method contributions, recovering from failed candidates, searching papers or baselines, or assessing whether results meet the project's thesis requirements. Use for research decisions and execution; not for status-only questions or unrelated coding.
---

# EKG research loop

Deliver validated method contributions against the existing research outcomes. The author delegates
routine scientific decisions and execution; do not require the author to supply hypotheses, select
baselines, interpret failures, or repeat a request to continue. A skill does not establish novelty,
improvement, independent review, or unattended execution.

## Enter through the actual decision

Read the latest `docs/HANDOFF.md`, then the active row of `docs/EXPERIMENT_PLAN.md` and only the
evidence needed for that row. Follow the repository's Git/ownership and validity/resource boundaries.
Do not restart a completed stage because an older paragraph or example says to start there.

Identify the current scientific claim, its public primary outcome, strongest valid controls, and
the missing decision. Use constitution/SPEC and current author amendments for acceptance, never a
framework's generic publication rubric. Existing numeric targets remain in their authoritative
contracts/results; do not replace them with an LLM score or a new proxy.

Route on evidence:

| Current state | Next action |
|---|---|
| Implementation or input failure | Diagnose and repair before interpreting performance; retain failed artifacts |
| Baseline cannot reproduce or is incomparable | Verify official paper/table and runnable source, adapt transparently or record the exact blocker |
| No admitted candidate, or scientific hypothesis failed | Run the research loop below; stop the fixed failed candidate, not the chapter objective |
| Candidate and production gates satisfied | Execute the frozen experiment through all endpoints and independent scoring |
| Only a resource/permission dependency remains | State its exact unlock; do useful independent work already allowed by the main table, without repeating completed preparations |
| Primary outcome improves | Test attribution, strong rivals, guardrails and the existing confirmation requirements before claiming a contribution |

## Research loop: failure changes the next experiment

1. Extract what the strongest control gets wrong. Separate observed errors from causal explanations,
   in-sample fit from generalization, and precision gains from recall losses. Preserve denominators.
2. Search primary literature and official implementations around that error or falsified assumption.
   Refresh search when a candidate fails, its nearest neighbor covers the proposed mechanism, a
   baseline is not runnable, or results contradict the motivation. Avoid generic paper collections.
   Use the existing `r1-literature-research` skill for mechanism/source/fidelity verification.
3. Keep a small competing set of explanations, including a simpler known method. For each plausible
   candidate state: signal actually available at inference, mechanism changing decisions, nearest
   published mechanism, predicted error corrections, expected countervailing errors, and falsifier.
   Reuse an existing candidate card rather than creating a new planning file for each check.
4. Prefer the experiment that separates these explanations and can support the required main-table
   claim. A CPU/toy check may reject a candidate or verify implementation, but cannot prove corpus
   improvement. Do not substitute speed, a bigger backbone, or module count for research value.
5. Decide. Reject a candidate with evidence, request a specific missing fact, or advance one feasible
   intervention. Update the authoritative plan before changing the active route. Do not hand an
   unranked direction list back to the author or declare "needs more research" without a next action.

Use hypothesis-generation and scientific-critical-thinking for specific missing reasoning, not to
repeat their templates. A sequential proposal/critique by one model is self-review. Only describe a
review as independent if a separate authorized review actually occurred; this skill authorizes no
additional agents, external models, API spending, uploads, or messages.

## Baselines and execution

- A baseline search ends in a runnable, protocol-aligned comparison or a named obstacle. Verify
  trainer, preprocessing, objective, decoder, weights, dataset/split/candidates/scorer and input
  assumptions. "Repository exists" is insufficient. Use public implementations, not reimplementations
  from prose labeled as reproduction. Keep FR-016 status and the existing roster reporting rules.
- Before method training, establish its value/feasibility, nearest-neighbor difference, strongest
  simple rival, core ablation, negative control, guardrails, existing power requirement and budget.
  Freeze those under the current project process; do not create a second admission system.
- Reuse existing training/evaluation entrypoints. Run meaningful local and actual Torch/CUDA checks
  as required; then complete the full frozen single-seed comparison. A smoke pass is not an effect.
- Use the frozen official scorer on the complete population. Compare full with its strongest
  controls, inspect error exchanges and secondary costs, and keep independent recomputation.
  Do not retain only the best arm, change evaluation after observing results, or use final-valid
  as iterative feedback. Keep exploration separate from any later authorized confirmation.
- On failure, update the explanation and next decision using measured evidence. Do not keep the
  same mechanism alive by renaming it, sweeping parameters, changing seeds, or weakening controls.

## Close the scientific loop

After each decisive result, explicitly answer: did the public outcome improve, did the core
comparison identify the proposed contribution, did guardrails hold, and which requirement remains
unmet? State "unmet" when evidence is absent; negative results do not silently satisfy a requirement
for positive method contributions. Do not change thesis structure or graduation standards yourself.

Write observations in `docs/results/`, decisions/status in the existing main table and HANDOFF,
commit/push, then continue the next authorized task within the active work session. Track scientific
outcomes separately from engineering preparation. Do not create `findings.md`, another task queue,
cron jobs, GPU watchers, or an automatic paper-writing stage.

Before adding another preparation task, name the decision it will change and check whether that
evidence already exists. If all legitimate independent work is complete, report the actual blocker
and unlock condition. Continuous operation requires an available session/runtime; instructions
alone do not create an always-on service or override a user stop or a tool budget.

Workflow sources and selection limits: `docs/RESEARCH_SKILLS.md` section "2026-10-19". This is a
project-specific instruction adaptation, not an installed or validated deployment of RD-Agent,
AI-Researcher, AI Scientist, or Orchestra's full autoresearch package.
