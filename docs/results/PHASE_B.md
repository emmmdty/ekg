# Phase B 实测档案 · Ch2 一致性修复与 CRC 准入

> 本文件是 **Phase B 的实测档案**：当时跑出的真实数字、口径、踩过的坑。
> 实时状态见 [`../TODO.md`](../TODO.md)，阶段契约见 [`../phases/`](../phases/README.md)。
> **数字以本文件为准**：TODO 与 EXPERIMENTS 只引用、不复制。

### Phase B 实施（2026-07-25，W1–W4 代码完成 CPU 全绿）

在 Phase A 的边打分之上加三件（复用既有 consistency/admission/cgep/grounding，不重写）：

- **W1 可追溯修复**（`relations/consistency`）：`RepairEdit`/`RepairTrace` + `solve_with_trace`；
  `GreedyConsistencySolver` 发出每条 drop/add 审计（violation ∈ {causal_cycle, temporal_cycle,
  temporal_closure, coref_dedup, temporal_dedup, subevent_dedup}）与 before/after `consistency_report`
  快照。`_break_cycles`/`_dedup` 重构为 traced 版本，**`solve()` 输出逐字节不变**（新增默认锁测试
  `solve(g).edges == solve_with_trace(g)[0].edges`）；`identity` 自动 no-op。
- **W2 分层 FNR**（`relations/admission`）：`stratified_admission_report` 报**边际**（CRC 边界所在层）/
  **分族**（causal/temporal/subevent/coref 各自 recall→FNR）/**doc-macro**（按篇平均 FNR）+ 准入集大小；
  表述按 SPEC §5.5——交换性 + 固定后处理下的**边际期望 FNR**，不写「每篇/每类都保证」。不动 `admission_report`。
- **W3 ECG 可重建率**（新 `succession/reconstruction`，复用 `extract_ecgs` 口径）：**R1 query 边可达率**
  （召回义，= CS-CRP `run_cross_stage` 消费的 `reachable` 标志）+ **R2 query 边保真**（precision 义，
  修复去矛盾环后可升）。层级放 succession 侧避免 core→succession 倒置。
- **W4 离线编排**（`scripts/consistency_repair_report.py` + `configs/relations/supervised_dump.yaml`）：
  消费**原始边 dump**（GPU 端 `evaluate_relations --dump-predictions` + `consistency: identity` + 无准入）→
  每 doc 重建图 → `solve_with_trace` → CRC 准入（cal 分片校准、复刻 repair∘admit 固定映射）→ 分层 FNR +
  准入集大小 + before/after consistency + R1/R2 + 每 query `reachable` 标志。checkpoint 不下本地。

- **合成 dump 验证（CPU，如实）**：注入因果环 m1→m2→m4→m1（最弱边 conf 0.2），repair 后——
  `causal_cyclic_scc` **1→0**、`dropped=1`（violation=causal_cycle）；**R1 持平 1.0**（环不删除 query 边，
  召回不受影响）、**R2 f1 0→1.0**（环使 m4 出度 1、破坏 query 边保真，修复恢复）。**修复增益如实落在
  precision 义 R2、非召回义 R1**——与 PHASE_B 止损口径一致（R1 受 α_edge 约束可持平/略降）。
- **验证基线（两端不同不是回归）**：本地无 torch = **241 passed / 12 skipped**；服务器有 torch =
  **252 passed / 1 skipped**。ruff 0、ekg-smoke OK（只增不改）。交付当时是 269/12，2026-07-27 重构
  移除 SARGE/Phase G 测试后降到 241；**不得拿旧计数判断回归**。
### Phase B 真实图闭环（2026-07-28，首次跑通，**结果混合**）

dump 在 **gpu-5090** 上产出（4090 全天 4 卡被他人占满；5090 环境当日配好，见 `GPU_RUNBOOK.md` §−1）：
710 篇 / **242,869 条原始边**（342/篇）/ 62MB，sha256 双端一致。离线分析 497 篇 held-out test
（α=0.2、cal_ratio=0.3），产物 `runs/relations/consistency_repair_supervised.json`。

| 档 | causal_cyclic_scc | causal_cyclic_edges | temporal_cyclic_scc | temporal_cyclic_edges | temporal_closure_gap | R1 可达率 | R2 query f1 |
|---|---|---|---|---|---|---|---|
| raw（identity） | 752 | 2,290 | 614 | 36,523 | 83.78 | **0.7310** | **0.0622** |
| repaired | **0** | **0** | **0** | **0** | **0** | 0.7294 | 0.0620 |
| repaired + 准入 | 0 | 0 | 0 | 0 | 0 | 0.7294 | 0.0620 |

`repair_trace`：**dropped 8,119 / added 8,770**（补的闭包边多于删的矛盾边）。

- ✅ **一致性违反被清零**：752 个 causal 强连通分量、614 个 temporal 强连通分量（卷入 36,523 条边）
  全部消除，closure_gap 83.78→0。这一档是确凿的。
- ❌ **但 ECG 可重建率没有增益，两项都微降**：R1 0.7310→**0.7294**（-2 个 query）、R2 f1
  0.0622→**0.0620**（precision .1339→.1321）。**合成 dump 上 R2 0→1.0 的增益在真实图上没有复现。**
  机制上看得见原因：修复主要在**补闭包边**（added 8,770 > dropped 8,119），`n_pred` 381→386 而
  `tp` 恒为 51 —— 补进来的边没有命中 gold query，只稀释了 precision。
- ⚠️ **按 PHASE_B 止损口径这一条已触发**（「若 R2 增益也微弱 → 退 consistency-aware reranking /
  constrained decoding，仍成章，不换指标」）。**不粉饰、不换指标**：Ch2 的可讲点收缩为
  「可追溯修复把结构违反清零」+ 误差传播分析，**不再声称修复提升下游可重建性**。

**风控准入（分层 FNR，α=0.2）——目标不可达，原因是召回上限**：

| 层 | 数值 |
|---|---|
| 边际 | P .2675 / R .5258 / **FNR .4742** / F1 .3546 |
| 分族 FNR | coref **1.000**(n=2887，模型 n_pred=0) · temporal .4469(n=71549) · causal .5616(n=6599) · subevent .4065(n=2165) |
| doc-macro FNR | .4925 |
| 准入集 | 163,533（均值 329/篇），**τ=0.0** |

- **τ 校准出 0 = 准入退化为「全收」**，故 `repaired+准入` 与 `repaired` 逐项相同。
- 根因不是 CRC 实现，而是**可行域为空**：抽取器边际召回只有 .5258 → FNR 下界 .4742，**任何
  α < .474 的目标都不可能满足**，即使准入全部边。α=0.2 本身超出了这个 predicted 图的能力上限。
  后续要么放宽 α 到 >.48 报有意义的 τ，要么先抬 Phase A 召回。coref 一族 FNR=1.0 是因为
  supervised 抽取器在 valid 上 **coref 预测数为 0**（`n_pred=0`），不是准入把它筛掉的。
