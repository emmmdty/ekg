# PHASE D4 — typed cue 与分解式事件事实性检测

> **FROZEN / NOT STARTED。** 本契约由 R1 T023/T024 放行。历史 D3 evidence locator 家族保持 failed；
> D4 的 treatment 是 typed cues 条件下的 known/unknown→modality→polarity 决策结构。只允许 seed 13，
> 额外 seeds 未获授权。

## Goal

检验 typed cue 表示与分解式决策能否减少 unknown、modality-only、polarity-only 三类注册 confusion，并在
预冻结五折 OOF 协议上超过 RoBERTa+CLS 与 DMRoBERTa 的 pooled five-class macro-F1，同时守住稀有类和
supporting-evidence 质量。

Specification coverage：RS-003、FR-001、FR-003–FR-007、FR-009–FR-012、FR-014–FR-015、
QR-001–QR-004、QR-006–QR-007、SC-001、SC-004、SC-006–SC-009。

## Inputs

- P1：`runs/stages/P1/p1-v6-20260904-r15/protocol.json`，SHA-256
  `1e31a9acef39261f776f7ed4069fd73f4531e8d12b55779bfc0fbd74c67f9655`；
- R1：`runs/stages/R1/r1-v61-20260904/protocol.json`、`cross_artifact_audit.json`、
  `factuality_cv/factuality_cv.json`；protocol SHA-256 以 `docs/results/PHASE_R1.md` 为准，audit SHA-256
  只从 `docs/HANDOFF.md` / `docs/TODO.md` 读取，避免 audit 对结果页形成自引用；
- factuality CV manifest SHA-256：
  `3a724cf77a2a34bb11f40d225725504b176e4d62e916c5b34c92f9d10a52c5c4`；
- MAVEN-FACT train SHA-256：`190522b44f0702af030161924d7cb94c4a06bd5d6e2b40d79f8f1eaa5886bab7`；
- accepted OOF baseline root：
  `gpu-4090:/data/TJK/ekg/runs/stages/R1/r1-v61-factuality-oof-r2/`，acceptance SHA-256
  `7de7177f9eb4e837c5c4eb8ff6822d103a9b0cb022065bf1d2ae34ce367e58af`，summary SHA-256
  `21e7e50596aa773f54037b95146c37838c68c250e579ae955b2730db6fe88165`；
- encoder：ModelScope 可下载的 RoBERTa-base，冻结到内容寻址目录
  `.../roberta-base/71be7419a60dcce0fc276654c8f9213b41f8def71a0c3465d7fed2352c961ea9`；
- train manifest SHA-256：`e9a939440eb0dbea76e6ce56d0b06b5a1009118eefdfcb93ae85f4a38e8c609a`；
  final-valid manifest `d39e83dd…776d5` 只记入 ledger，不在 pilot 读取。

禁止改变五类标签、fold rotation、selection-dev 规则、pooled evaluator 或 `EventNode` 字段；禁止把 gold
supporting words 当推理输入。291-document 历史结果只能作历史证据，不与 2,913-document OOF 主表相减。

## Baselines and causal matrix

同一五折 OOF manifest/input/selection/evaluator 下冻结：

1. RoBERTa+CLS primary anchor；
2. DMRoBERTa dynamic-multi strongest alternative；
3. MAVEN-FACT supporting-word pipeline 的 leakage-free OOF protocol adaptation；
4. typed cues + factorized decisions + cue-conditioned residual（full）；
5. typed cue/input/capacity 保持、改为 flat five-class head（remove-core）；
6. document 内 cue representation permutation，保持 cue count/span length/labels（negative control）。

1–2 的已验收 outputs 不重训；3–6 各 fold 使用相同 train/selection-dev/evaluation，evaluation 从不参与
checkpoint、threshold、结构或 weighting 选择。

## Tasks

### D4.0 implementation and local gate

实现 typed cue sidecar、三级 logits 与确定性五类重组、flat-head remove-core、document-internal permutation、
三类 confusion mediator、evidence exporter。测试五类概率和为 1、缺 evidence 显式输出、fold 隔离、坏 ID/
offset、负控不跨文档及 `EventNode` schema lock。运行三件套。

### D4.1 immutable preflight and baseline replay

物化 `runs/stages/D4/d4-v61-typed-cues-r1/preflight/`，绑定 R1/P1、CV folds、source、encoder、baseline
OOF predictions、code/config/command hashes 与 final-valid ledger。独立重算 CLS/DMRoBERTa pooled 指标；
再以相同五折协议建立 supporting-word baseline，不能沿用历史 291-doc 数字。

### D4.2 CPU/CUDA smoke

CPU fixture 覆盖五类、空 cue、多个 cue、Uu 与不连续 evidence。4090 单卡跑一个 fold 的 10 documents，
完成 full/remove-core/permutation forward/backward/export/reload；断言 loss/logits/spans 有限且 evaluation ID
没有进入 train/selection。

### D4.3 seed-13 five-fold pilot

按 frozen rotation 运行 5 folds × 3 arms（full/remove-core/permutation），每 fold 只用 selection-dev 选
checkpoint。汇总前检查 2,913 documents / 73,939 mentions 恰好一次 OOF prediction；保存逐实例 class
probabilities、typed cues、evidence、三级 logits 和 confusion 类型。

### D4.4 promotion and handoff

seed-13 pooled 结果同时过主门、中介、负控与护栏后，只写 `confirmation_eligible=true` 并停下请求额外
seeds 授权。获授权后 matched seeds 13/17/42 复用相同 folds，做 document-cluster paired bootstrap；配置
冻结后 sealed final-valid 一次。无论 pass/failed 均输出不可变 handoff。

## Promotion gate

- seed-13 full pooled five-class macro-F1 严格高于 CLS 与 DMRoBERTa；
- full 相对 remove-core 降低三类注册 confusion 总率，permutation 消除该改善；
- 任一 anchor 非零 F1 类不得塌为 0；PS−/Uu 两类 macro-F1 相对 CLS 的 non-inferiority margin 为 `-0.030`；
- evidence macro(CT−/PS+/PS−) 与 pooled span F1 均不得低于同协议 supporting-word baseline `0.030`；
- confirmation：仅在授权后，matched seeds 13/17/42 的 mean macro-F1 delta ≥ `+0.030`，至少 2/3 为正，
  10,000 次 document-cluster paired-bootstrap 95% CI 下界 > 0，且均值超过 DMRoBERTa；
- accuracy、calibration、mediator、per-class 与 evidence 都不能替代 five-class macro-F1。

## Stop conditions

- fold 泄漏、evaluation 参与选模、ID 覆盖不完整或 fabricated evidence：立即停止；
- full 不减少注册 confusion，或 permutation 保留相同改善：机制 claim 失败；
- 任一有效周期不胜两 baseline 或违反 rare/evidence guardrail：该周期失败；两个有效周期后封存；
- 不换标签、放松 macro-F1、扫 post-hoc threshold、扩大 backbone/数据或使用 final-valid feedback 救结果。

## Bundle

`runs/stages/D4/d4-v61-typed-cues-r1/` 必含 `protocol.json`、fold manifests/checkpoint identities、完整 OOF
class/evidence predictions、raw pooled metrics、mediator/paired statistics、`status.json` 与
`fallback_component_bundle_id`。结果数字只追加到 `docs/results/PHASE_D.md`。

## GPU command

实现与 preflight 完成后，固定入口为：

```bash
cd /data/TJK/ekg
CUDA_VISIBLE_DEVICES=2 .venv/bin/python -u scripts/run_d4_typed_cue_oof.py \
  --contract runs/stages/D4/d4-v61-typed-cues-r1/preflight/protocol.json \
  --seed 13 \
  --output runs/stages/D4/d4-v61-typed-cues-r1/pilot/seed-13
```

启动前须展示这条命令、`/data/TJK/ekg` 和预期目录，并重新核卡；长任务用 `setsid nohup`。脚本或
preflight 尚不存在、当前 commit 未过本地 gate、GPU 非空闲时均不得启动。
