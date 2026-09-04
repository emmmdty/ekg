# PHASE R1 — 三方法章的方法设计冻结

> **PREPARATORY TASKS ACTIVE；最终 promotion 受 A3 handoff 约束。** 不读取 A3 待出结果的学位版本、
> 一手文献、公开实现、数据 ID 和 Ch1/Ch3 功效审计可并行；Ch2 最终因果 brief、跨产物一致性审计和
> method contract 必须等待 A3 handoff。本 phase 不训练 proposed model，不访问 final-valid 指标，
> 不产生章节 PASS。

## Goal

在写 C5/A4/D4 方法代码前证明三件事：每章的新机制确实不同于已失败路线和最近公开方法；现有数据与
评测能检出最小有意义效应；每个方法的因果链、强 baseline、负控、消融和跨章接口能够被单变量识别。

## Inputs

- 最新 P1 trust root；A3 `status=failed` immutable handoff 是最终 promotion 输入，准备性任务可先不读取；
- `docs/results/PHASE_A.md`、`PHASE_C.md`、`PHASE_D.md`、`PHASE_E.md` 的逐实例产物入口；
- [`../replan/METHODOLOGY_REDESIGN_20260904.md`](../replan/METHODOLOGY_REDESIGN_20260904.md)；
- MAVEN-ERE、MAVEN-ARG、MAVEN-FACT 的公开版本和许可；
- 2022–2026 一手论文与可取得的官方代码。

禁止把论文不同 split 数字写进统一主表，禁止用 gold arguments/evidence 代替预测输入，禁止在本 phase
运行 proposed GPU pilot。若逐实例 anchor predictions 不可取得，power audit 必须标 blocked，不能用汇总
均值猜方差。

## Tasks

### R1.1 学位与论文评价版本冻结

记录作者的学位类型、入学年份、学科/专业以及适用的同济授予标准文件 URL/发布日期/hash。将行政要求
和项目自定科研硬门分列；后者只可更高，不得用行政最低线替代。

验证：`protocol/degree_requirements.json` 含来源、适用性、未确认项与确认人；未知信息显式 `null`，不猜。

### R1.2 最近方法与公开实现矩阵

每章至少列最近三个直接相邻方法，字段固定为：paper/venue/year、task/input、dataset/split、candidate
universe、evaluator/metrics、backbone/size、official code/checkpoint、核心机制、消融、统计检验、与本项目
可比性。优先官方仓库；拉取后记录 upstream commit、license、原始 hash 和透明补丁计划。

验证：

- Ch1 必含 CorefPrompt、RESIJ/官方 joint 与一个可运行 argument-aware baseline；
- Ch2 必含 2025 two-stage ERE、RESIJ、TacoERE/KnowQA 和 official joint；
- Ch3 必含 MAVEN-FACT 官方 pipeline、DMRoBERTa、ModaFact 或另一个结构化 modality/factuality 方法；
- “无公开代码”不能写成“已复现”；若强对手无法忠实运行，必须换另一强方法或把章节标 blocked。

### R1.3 跨数据 ID 与输入可部署性审计

构建只读 coverage report：ERE↔ARG↔FACT 的 doc ID、event/mention ID、offset、event type、argument role、
许可与版本 hash；检查一对多、重复、缺失、offset drift。任何自动映射必须有 deterministic rule 和人工不
参与训练/选模的少量 spot check；未知映射 fail-fast。

验证：合成交集 fixtures、真实数据全量 uniqueness/set equality、坏 offset/重复 ID/未知 role 负测。

### R1.4 前瞻性 power 与最小有意义效应

从冻结 anchor 的逐文档 predictions 进行 simulation-based power analysis。每章在看 proposed 结果前冻结：

- evaluation unit 与 cluster 层级；
- 主指标最小有意义效应和 80% power 下的 MDE；
- internal-dev promotion threshold；
- final paired bootstrap、seed aggregation 与多重比较家族；
- 功效不足时的合法补强方案（预冻结 repeated splits、cross-validation 或额外公开同任务数据）。

验证：固定 RNG、可重跑脚本、power curve 原始表与配置 hash；不得用 post-hoc observed proposed effect
反推目标效应。

### R1.5 三份因果 design brief

每份必须包含：observed error、可干预原因、treatment、mediator、main outcome、negative control、full/
-core/strongest-alternative 三臂、guardrails、promotion、stop、GPU 预算和 novelty contrast。

- C5：mention-local argument posterior → role compatibility/uncertainty → false-merge risk → MUC；
- A4：pair evidence/sufficiency → cross-sentence false-positive risk → causal micro-F1；
- D4：typed cues/factorization → modality/polarity/Uu confusion → five-class macro-F1。

若 treatment 不能改变预注册 mediator，即使主指标偶然上升也不能确认机制；若 mediator 改善而主指标不
胜出，保留诊断但章节不 PASS。

### R1.6 新 phase 与 trust roots

只有对应 R1.1–R1.5 条件和跨产物一致性审计全部 PASS 后，才为通过准入审查的方法生成可执行 phase。
每份列确切 manifests、baseline
roster、anchor rule、candidate/evaluator、config/code hash 集、CPU/CUDA smoke、单种子 promotion、三种子
授权门、final-valid ledger 和 immutable bundle schema。

## Promotion gate

R1 PASS 必须同时满足：

1. 行政标准适用版本已确认或不影响科研硬门的未知项已显式隔离；
2. 三章都有可运行的多个强同协议 baseline 方案；
3. 跨数据 ID 输入闭环且无静默缺失；
4. 每章的目标效应在设计上达到 80% power，或已有冻结的合法补强方案；
5. 三个核心机制均可由单变量消融和中介负控识别；
6. 至少一份方法 contract 与新 P1-compatible trust root 已冻结；其余方法可在自身条件满足后独立放行。

不预设首先放行 C5、A4 或 D4。若 R1 证明某方法依赖另一方法的真实上游，则等待该 handoff 后再做最后
hash 绑定；若无此依赖，可按资源并行或重排。E3 始终等待三类所需上游 handoff。

## Stop conditions

- 找不到多个可运行强 baseline：该章 blocked，继续 baseline engineering，不用弱对手降标；
- MAVEN-ARG/ERE ID 无可靠映射：停止 argument 输入线，回文献设计其他 mention-local 监督；
- 目标效应低于可检测范围：不降低 CI，改评测设计或提出更强机制；
- 新方法与最近工作只有组件换名或 backbone 差异：拒绝立项；
- 需要闭源模型、人工新增 gold 或未经授权 final-valid 反馈才能成立：拒绝立项；
- 任一来源、hash 或逐实例 prediction 缺失：对应审计 blocked，不填默认值。

## Outputs

```text
runs/stages/R1/r1-v61-<date>/
├── protocol.json
├── literature_matrix.json
├── id_coverage.json
├── power_analysis.json
├── design_briefs.json
└── status.json
```

另更新 RESEARCH_PLAN/TASKS/TODO/HANDOFF 和获准生成的 phase contracts；只有研究问题、范围或质量要求
变化时才修订 SPEC。实验数字仍只进入 `docs/results/`。

## GPU

默认不用 GPU。官方 baseline 的最小加载 smoke 若确有必要，只能在 4090 用单卡短任务；运行前展示确切
命令、cwd 与预期产物。不得在 R1 启动 proposed training，5090 仍逐次授权。
