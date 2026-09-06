# PHASE A4 — 完整候选上的关系证据充分性与必要性

> **FROZEN / NOT STARTED。** 本契约由 R1 T023/T024 放行。A3 的工作点、近似 retriever、prototype 与
> ATLoss 保持 failed/sealed；A4 是不同机制家族。只允许 seed 13，额外 seeds 未获授权。

## Goal

检验 pair-specific evidence sufficiency/necessity supervision 能否在不删任何评测候选的条件下减少无支持的
跨句 causal false positives，并使 official causal positive micro-F1 超过 A3 fallback 与独立 TacoERE
protocol adaptation，同时守住 subevent、temporal 与 causal recall。

Specification coverage：RS-002、FR-001、FR-003–FR-007、FR-009–FR-012、FR-015、QR-001–QR-004、
QR-006–QR-007、SC-001、SC-003、SC-006–SC-009。

## Inputs

- P1：`runs/stages/P1/p1-v6-20260904-r15/protocol.json`，SHA-256
  `1e31a9acef39261f776f7ed4069fd73f4531e8d12b55779bfc0fbd74c67f9655`；
- A3 failed handoff：`runs/stages/A3/a3-v6-20260905-r17/protocol.json`，SHA-256
  `c187bf03978674edd29ac209658ccb62d457b744a209e864a0fef0e9eee9359e`；
- R1：`runs/stages/R1/r1-v61-20260904/protocol.json` 与同目录 `cross_artifact_audit.json`；protocol SHA-256
  以 `docs/results/PHASE_R1.md` 为准，audit SHA-256 只从 `docs/HANDOFF.md` / `docs/TODO.md` 读取，避免
  audit 对结果页形成自引用；
- train/internal-dev manifest SHA-256：`47d19cc9a17e38259bfbb7f9206c675c7362f41252d23f414ea6cfd46015ca68` /
  `f5457b302be57663f8e618d977c492909c3210682804cb486bd67ccc8c171b5f`；
- MAVEN-ERE train SHA-256：`6a5519fe7c30448690adb13d49217c50d474fc57480eae10aecb29df7eb638b7`；
- internal-dev candidate digest：`15a3b1a548625624642130190b39411e6346866ff8594c2af2020cfbdac10910`；
- official evaluator SHA-256：`32919e86d98c6fafae6aa9505579e2c356caee12c32c1a8c719910acec359598`；
- encoder：ModelScope 可下载的 RoBERTa-base，冻结到内容寻址目录
  `.../roberta-base/71be7419a60dcce0fc276654c8f9213b41f8def71a0c3465d7fed2352c961ea9`；
- T021 TacoERE adaptation：checkpoint、predictions、official metrics、transparent fidelity delta 与 SHA-256
  只从 R1 protocol 读取；运行数字只从 `docs/results/PHASE_R1.md` 读取。

禁止评测时 retrieval/pruning；禁止改变 official mention expansion、candidate order、TIMEX 对称性、关系方向
或 scorer。A3 failed bundle 保持原身份，不因 A4 重新标记。

## Baselines and causal matrix

同一 manifest/candidate/evaluator/backbone 下冻结：

1. MAVEN-ERE official joint；
2. A3.6 strongest fallback（official recipe，failed method identity retained）；
3. TacoERE-inspired K=3 cluster-conditioned RoBERTa adaptation（independent recent family）；
4. proposed pair evidence sufficiency/necessity（full）；
5. full 去掉 evidence objectives（remove-core）；
6. length-matched non-evidence sentence（negative control）；
7. evidence representation 保留、sufficiency/necessity consistency disabled（no structural constraint）。

矩阵 3–7 必须使用完整冻结候选；TF-IDF/KMeans 仅为 baseline 的 context construction，不得成为 A4 的
proposed treatment 或修改候选。

## Tasks

### A4.0 implementation and local gate

实现 evidence selector、masked/retained counterfactual forward、中介统计和 bundle exporter。测试完整候选、
方向、空 evidence、length-matched control、remove-core 单变量性、TIMEX train/inference 对称和 hash drift。
运行三件套。

### A4.1 immutable preflight and baseline replay

物化 `runs/stages/A4/a4-v61-pair-evidence-r1/preflight/`，绑定 R1/P1/A3、source/manifest/candidate/evaluator、
encoder、baseline predictions、code/config/command hashes 和 final-valid ledger。独立重算 A3 fallback 与
TacoERE adaptation 的 official 三族 P/R/F1；人口或 hash 不等立即停止。

### A4.2 CPU/CUDA smoke

CPU fixture 覆盖同句、跨句、无正边、TIMEX 与反向 pair。4090 单卡 10 documents 跑一次
forward/backward/export/reload；断言 full/remove-core 的初始 base logits 一致、counterfactual loss 有限、
predictions 行数与 candidate digest 完全一致。

### A4.3 seed-13 pilot

运行矩阵 4–7 的 seed 13，固定 50 epochs、warmup 200、encoder lr `1e-5`、head lr `1e-4`、gradient
accumulation 8、full negatives、per-family checkpoint selection。逐实例保存 evidence、原/移除/保留 evidence
logits 和 cross-sentence error profile；不扫 threshold。

### A4.4 promotion and handoff

seed-13 同时过主门、中介、负控和护栏后，只写 `confirmation_eligible=true` 并停下请求额外 seeds 授权。
授权后 matched seeds 13/17/42 做 paired inference；最终配置冻结后 sealed final-valid 一次。无论 pass/failed
都输出不可变 handoff。

## Promotion gate

- seed-13 causal F1 严格高于 A3 fallback 与 TacoERE adaptation；
- full 相对 remove-core 降低 cross-sentence causal false-positive rate，且 length-matched control 不保留相同
  sufficiency/necessity mediator；causal recall 不低于 A3 fallback 1.0 个绝对 F1 点；
- subevent F1 ≥ `0.2875`，temporal F1 ≥ `0.5063`；candidate population/digest 必须逐位相同；
- confirmation：仅在授权后，matched seeds 13/17/42 的 mean causal delta ≥ `+0.010`，至少 2/3 为正，
  10,000 次 document-cluster paired-bootstrap 95% CI 下界 > 0，且均值超过两条强 baseline；
- 辅助 evidence/abstention 指标只能支持或否定机制，不能替代 causal 主指标。

## Stop conditions

- 任何候选被删除、增加、重排或无法评分：立即停止并回 A4.1；
- full 不降低注册 mediator、negative control 保留同样 mediator、或增益只来自 recall collapse：机制失败；
- 任一有效周期未超过两条强 baseline 或破坏 relation guardrail：该周期失败；两个有效周期后封存；
- 不恢复第四个 retriever、阈值/损失扫参、换 split/更大 backbone 或 final-valid feedback。

## Bundle

`runs/stages/A4/a4-v61-pair-evidence-r1/` 必含 `protocol.json`、完整 candidate predictions、evidence 与三种
counterfactual logits、raw official metrics、error/paired statistics、checkpoint hashes、`status.json` 与
`fallback_component_bundle_id`。结果数字只追加到 `docs/results/PHASE_A.md`。

## GPU command

实现与 preflight 完成后，固定入口为：

```bash
cd /data/TJK/ekg
CUDA_VISIBLE_DEVICES=1 .venv/bin/python -u scripts/run_a4_pair_evidence.py \
  --contract runs/stages/A4/a4-v61-pair-evidence-r1/preflight/protocol.json \
  --seed 13 \
  --output runs/stages/A4/a4-v61-pair-evidence-r1/pilot/seed-13
```

启动前须展示这条命令、`/data/TJK/ekg` 和预期目录，并重新核卡；长任务用 `setsid nohup`。脚本或
preflight 尚不存在、当前 commit 未过本地 gate、GPU 非空闲时均不得启动。
