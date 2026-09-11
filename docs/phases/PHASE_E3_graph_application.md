# PHASE E3 — 事件图谱构建与下游事件预测应用

> **重定向（2026-09-11，作者选定「乙」形态）。** 取代原 `PHASE_E3_factorial_consumers.md` 的
> 24 条件 same-instance factorial 契约。原契约的 **2×2×3×2 factorial、Holm 校正家族、
> frozen-vs-fine-tuned 同 backbone 对照、消费者预测有效性阻断门全部撤销**，理由见
> `../results/PHASE_R1.md` §21.1：九篇同领域学位论文无一设立「不属于任何方法的独立评估章」，
> 且本任务 MRR 绝对值（.1802）撑不起主章的竞争性论断。
>
> 本 phase 改为**带公开对手的应用章**（参照陈泽《事件知识图谱构建关键技术及应用研究》第 6 章
> 「基于事件知识图谱的脚本事件预测」的体例）：三章方法串成构建流水线，在下游事件预测任务上
> 以**公开发表方法**为对手评估应用价值，并顺带量化构建误差的下游代价。
>
> 历史三图事实见 [`../results/PHASE_E.md`](../results/PHASE_E.md)；旧 E2 不同语料消费者契约不得执行。

## Goal

回答两个问题，**都不要求本章胜过任何方法章**：

1. **应用价值**：用 C5/A4/D4（或其 fallback）构建出的事件图谱驱动下游事件预测，在冻结的本地重建
   CGEP-MAVEN 协议上，相对**公开发表的对手方法**处于什么位置；
2. **构建代价**：gold 图与 predicted 图之间的下游差距有多大，占整张图全部价值的多少。

Specification coverage：RS-004、FR-002–FR-004、FR-008–FR-009、FR-016、QR-005、QR-007、
SC-005–SC-007。

## Inputs

- P1 冻结的 ID namespace、query 生成器版本/来源 hash 与目标 schema；
- C5 cluster / A4 relation / D4 factuality 的 immutable bundle 及各自 status；
  任一 phase `failed` 或 `blocked` 时读取其显式 `fallback_component_bundle_id`，
  **并在表头标明该臂的上游方法身份**；
- 4090 上的 SeDGPL 权重 `ch4_sedgpl.pt`（1.5G，`--load-model` 可复用，实测 load 后
  `predicted` 复现 .1583 逐位一致）、random/frequency 与历史 paired-rank caches；
- MAVEN valid gold 仅作 reference，不得冒充 predicted arm。

禁止：跨不同 queries/候选集比较绝对分数；用删节点代替 factuality 属性；丢弃某 arm 不可评分的样本后
再比较；沿用 source/stored edge order（**主表一律 canonical 序**，见 §E.2 的边序陷阱）。

## Baselines

对手分三类，同一批 queries / candidates / scorer：

1. **公开发表方法**（本章的外部对手，**不少于 3 个**）：名单与 FR-016 保真度状态由
   [`../BASELINE_ROSTER.md`](../BASELINE_ROSTER.md) §6 持有，**在跑本章主表之前必须先冻结该节**；
   每个复现必须先在其原始基准上复现其已发表数字（状态 (a)），否则标「透明适配」（状态 (b)）并列差异；
2. **平凡对照**：random、frequency——用于确认任务本身不平凡；
3. **无图/扰动对照**：`no_graph`（删光边）、`rewired`（边数/类型/子类型全同、端点随机重挂）
   ——用于证明消费者确实在读图。

⚠️ **2 与 3 已经跑完并通过**（2026-08-30，冻结 SeDGPL 权重、不重训、不选任何东西）：
`gold .1802 > rewired .1185 > no_graph .0811`，三者严格有序，差距是本章噪声地板（±.003–.004）的
一到两个数量级。本轮**不重跑**，直接引用 `../results/PHASE_E.md`。

## Tasks

### E3.0 冻结不可变 evaluation unit

按公开 CGEP 任务定义与已记录生成器，冻结完整 query/candidate manifest、随机 seed、source/generator
hashes、candidate-ID digest 与 population counts。该轴明确标为「**本地重建协议**」，不得声称逐项复现
论文未公开的派生 split/candidates。当前 1,908 实例仅是预期规模；若重建校验导致变化，须在看任何
consumer 结果前冻结并披露原因。

每个 query 固定 `instance_id/doc_id/anchor mention/gold mention/candidate mention IDs/label`。
无法映射的 arm fail-fast，不得删题。

### E3.1 闭合三类真实上游输入接口

- identity：gold/pred mention-to-cluster，通过稳定 mention IDs 重建 node grouping；
- relation：gold/pred typed directed edges，保留原始概率与 source IDs；
- factuality：gold/pred 五类概率与 evidence，以 node-attribute sidecar 或 `metadata` 序列化；
- 所有 arm 使用同一事件文本、candidate IDs、**canonical edge order** 与 scorer。

先做 20-query CPU fixture，断言 gold 与 predicted 两套条件的 ID 集完全一致、无重复/缺失。
**只需 gold / predicted 两档**（原 24 条件 factorial 已撤销）。

### E3.2 图谱构建流程、统计与可视化

串联 C5 → A4 → D4 产出完整事件图谱，记录：节点数、各类型边数、事实性分布、
连通分量、平均度、可达率。产出一张可读的子图可视化（工具不限，Neo4j 非强制）。
本节是**描述性**的，不承担任何胜出论断。

### E3.3 下游事件预测对比实验（本章主表）

在冻结的 evaluation unit 上，对所有 §Baselines 第 1、2 类方法与本文构建图各跑一次，报告
**MRR 与 Hit@1/3/10/20/50**。表形态按 `../BASELINE_ROSTER.md` §5：

```
公开方法 A[ref] / B[ref] / C[ref]  →  random / frequency  →  本文构建图（predicted）  →  本文构建图（gold 上界）
```

随机性消费者使用 matched seeds 13/17/42；每个 consumer/seed 在预注册的同一训练数据/训练图上
**只训练一次**，并在全部质量 arm 复用同一 checkpoint；quality 只改变输入图，
**不得**为 gold/predicted arm 分别重训。

### E3.4 构建质量评估

- **构建损失**：gold 图与 predicted 图的 ΔMRR，以及它占整张图全部价值（`gold − no_graph`）的比例；
- **受控单变量扰动曲线**：在 gold 图上按幅度注入删边/增边/并节点/拆节点，嵌套采样保证曲线量的是
  幅度而非抽样运气；
- 文档聚类配对 bootstrap ≥ 10,000 次，报 effect size 与 95% CI；
- 每个对照独立测噪声地板，**小于地板的效应不作正面主张**。

已有实测（`../results/PHASE_E.md`）可直接引用，无需重跑：构建损失 −.0218（占整图价值 22.0%）、
拆节点 −.0184 > 删边 −.0081 > 增边 −.0047、打乱 temporal 按构造恒为 0。

### E3.5 叙事闭环

结论只允许在证据范围内表述：

1. 本文构建图在下游预测上**相对公开对手**处于什么位置（可胜可负，如实报）；
2. 构建误差造成多少下游代价，哪一类构建错误最伤；
3. 一致性指标与可重建性不对齐（causal_scc–R1 的 ρ = −0.064，而 R1–R2 ρ = +0.783）。

不得从不同语料、不同 backbone 或不同 queries 的绝对分数推出因果机制。
**不再作「消费者类型（frozen vs fine-tuned）导致敏感性差异」的论断**——该对照已撤销。

## Done when

- evaluation unit manifest 冻结，gold/predicted 两档 ID 集逐位一致；
- identity/relation/factuality 读取真实 C5/A4/D4 bundle，或读取其显式 fallback 并在表头标明身份；
- 主表含 **≥3 个公开发表对手**，每个带 FR-016 保真度状态；跑不了的进可得性表写明障碍；
- 构建损失、扰动曲线、配对 CI 与噪声地板完整；
- 图谱统计与可视化产出；
- 结果追加到 `docs/results/PHASE_E.md` 的 v6 小节；
- 本地三件套全绿，远端权重/log/bundle 可追溯。

## Stop conditions

- query/candidate/label 在任何 arm 漂移：立即停止，回 E3.0，不运行消费者；
- 任一 blocked phase 既无 bundle 也无可校验 fallback component bundle：该 predicted arm 不成立，
  本章只报能成立的部分，**不得用 gold proxy 补位**；
- 找不到 ≥3 个可跑的公开对手：本章降为**描述性构建与应用章**（保留构建流程、统计、可视化、
  构建损失与扰动曲线），**不作任何相对外部方法的位置论断**；这是允许的收缩，不是 phase 失败；
- 不更换 ForecastQA/CRAB/叙事完形来救主结果，不扩大到 14B/70B/闭源模型。

## 已撤销（2026-09-11，不得恢复）

- 2×2×3×2 共 24 条基础条件的 same-instance factorial 及其主效应/交互分析；
- Holm 校正的确认性 contrast 家族；
- frozen-vs-fine-tuned 同 backbone 对照与由此而来的「消费者依赖性」因果论断；
- 「fine-tuned graph arm 两个工程轮后仍不优于 BART/text-only 与 frequency 则 Ch4 不作独立章」
  这条阻断门——本章不再以胜过消费者对照为存在前提。

回收的预算（粗估 15–20 GPU·day）回流给 C5/A4/D4 的方法实验与外部对手复现。

## Handoff

E3 完成后进入 H2。H2 只补缺失的种子/消融/复现检查，不重新设计方法、不重开止损路线。

## GPU

4090 为主；5090 每次逐次授权。先跑 20-query 与最长输入 smoke，再估算完整对比实验时间；
命令、`/data/TJK/ekg`、预期 `runs/stages/e3/...`、权重与 log 必须先展示。
