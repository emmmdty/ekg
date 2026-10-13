# C5 · conventional first-dummy supervision control

C-41 / T087 only. Known-target baseline engineering, `control_only=true`,
`method_admitted=false`; no proposed-method or chapter contribution promotion.
Scientific value and feasibility predeclared in results/PHASE_R1.md §25.50.
Pinned-source actual gradient/coverage proof is in §25.49. Old results remain immutable.

Input: same full train manifest, frozen teacher current-mention embeddings, original
pair-MLP checkpoint, task-given types. Internal-dev embeddings contain no labels.
No new data, observers, OOF error labels, backbone, seed, GPU, or weight transfers.

One variable: conventional gold dummy for the earliest mention of each non-singleton
cluster. Legacy targets must match the pinned source `fill_expand` exactly. Both arms
use the same type policy, raw pair scorer, original dummy-zero/argmax forest decoder,
Adam, training order/dropout seed 13, batch eight documents, five complete train epochs.
Both start from the same original scorer weights. Encoder and relation outputs freeze.
The clamp-before-sum convention is preserved in both arms. Endpoint is final epoch;
no dev model selection, threshold/temperature sweep, or extra seeds.

Before fitting: entrypoint/config/input hashes; manifests/feature population and labels;
source resolution; real root-cause audit; full dev raw-logit exact parity and typed
cluster parity. CPU smoke uses first eight train documents for one optimizer step,
exports all dev predictions but does not score them. Smoke is a runnability/parity gate.
Full fit requires complete smoke with this same config SHA.

Comparison: sealed strongest type control, matched legacy continuation, corrected
continuation. Score all four official metrics only after both full predictions seal;
independent evaluator runs and paired document bootstrap. Report every arm and guardrail.
Known-target correction has no novelty claim and does not pass the proposed-method
power requirement. A metric drop or no supported useful gain stops this fixed action;
no epoch/lr/head/decoder rescue. A positive result is control improvement, with limited
frozen-encoder adaptation scope, not a full original-joint retraining result.

Use 4090 CPU four threads, CUDA hidden. New namespace:
`runs/stages/R1/r1-v63-c5-20261013/first_dummy_control/{smoke,fit}/`.
Existing paths reject overwrite. Weights stay on 4090; nonweight artifacts may be copied
with SHA verification. Record source commit/config/checkpoint/input hashes and exact argv.

Required checks: complete local pytest/ruff/CPU smoke, actual remote Torch tests, then
control smoke. Exact full execution command and output identity are disclosed before run.
