# PHASE A3 — 关系族均衡的长上下文事件关系抽取

> **ACTIVE / ENTRY PASS。** P1 `global_protocol_status=pass` 且 `a3_entry_status=pass` 已满足。历史 A/A2 数字只见
> [`../results/PHASE_A.md`](../results/PHASE_A.md)，旧 A2 契约不得继续执行。

## Goal

在冻结 MAVEN-ERE gold-mention 协议上回答：区别于固定任务权重的自适应关系族平衡，能否在不牺牲
subevent 的前提下提高 causal，并稳定超过预注册主锚。类型/方向约束是可删除的二级假设。

## Inputs

- P1 r3 trust root：`runs/stages/P1/p1-v6-20260828-r3/`，其 `protocol.json` SHA-256 固定为
  `e449e7313c2b0b9235b413f3292877f1a842e4ed85be4d7ba020d28601c4f84f`；任何 A3 命令都必须显式传入，
  不能从待验证 bundle 自取 hash；
- P1 冻结的 train/internal-dev/final-valid manifests、official evaluator 与 stage schema v2；
- P1 通过同 schema smoke 的 local pair、official single、official joint；
- CPU 预检计划 `runs/stages/A3/a3-v6-baselines-r3/preflight/execution_plan.json`；远端须从当前 P1
  trust root 重新物化，不直接复制本地绝对路径；
- 当前长窗口 relation extractor 与历史 checkpoint，仅作初始化/对照；
- gold mentions。predicted mentions 只进入端到端副表，不进入组件主表。

禁止：TIMEX 未闭环时把 temporal 放进主贡献；用 valid 选 epoch/阈值；把 warmup/epoch/梯度累积写成创新。

## Tasks

### A3.0 baseline 全协议重跑

- 先在 `/data/TJK/ekg` 执行 CPU 物化（不加载模型、不使用 GPU）：

  ```bash
  .venv/bin/python scripts/prepare_a3_baselines.py \
    --p1-protocol-sha256 e449e7313c2b0b9235b413f3292877f1a842e4ed85be4d7ba020d28601c4f84f
  ```

  物化器必须重新验证 P1 v2 bundle、source/manifests/candidate/label digests，只写 P1 train 与 internal-dev；
  official `test.jsonl` 是同一 internal-dev ID 的无标签形状，不得读取/复制 final-valid。记录 materializer
  打印的 `plan_sha256`；launcher 必须显式接收该外部可信值并拒绝任何未计划 source/data 文件。
- 每个 baseline/seed 先运行不带 `--execute` 的 launcher，向作者展示其打印的**完整** argv、cwd、预期产物；
  确认 4090 空闲后才在相同命令末尾加 `--execute`。示例：

  ```bash
  .venv/bin/python scripts/run_a3_baseline.py \
    --p1-protocol-sha256 e449e7313c2b0b9235b413f3292877f1a842e4ed85be4d7ba020d28601c4f84f \
    --plan-sha256 9ea3aa84acc1e781256aadc45cf3078775952f91a71ba78526718356f2a18bdf \
    --baseline local_pair --seed 13
  ```

  launcher 每次只运行一个 job，拒绝覆盖既有 run-dir；正式运行保存实际训练/推理/scorer argv、cwd、GPU
  preflight、return codes、checkpoint/prediction/metric hashes。任一 skipped document、缺失输出、candidate
  drift 或 partial official payload 未能严格归一化都使该 run `failed`，不得进入 baseline 表。
- 使用相同 manifests、candidate population、输入字段、evaluator 和输出 schema；
- 必含本地 pair、official single、official joint；RESIJ 仅在公开实现或忠实复现闭环时可选纳入；
- local pair 的 v6 loss/选模只包含 causal+subevent；未训练 temporal head 不得进入推理。official single/joint
  保持官方 README recipe，透明 model-path 适配只改隔离副本中的模型路径并保存前后 hash；
- 先只用 train/internal-dev 完成训练、选模和主锚选择；不得提前查看新 baseline 的 final-valid 分数；
- 在任何方法结果产生前冻结 internal-dev `primary anchor`；随机主锚必须跑 matched seeds 13/17/42；
- 保存 candidate-ID digest/population counts，并预注册 subevent 非劣 margin 与 document-cluster CI；
- 完成后冻结 baseline table，不因主方法结果不好临时换弱对手。

### A3.1 复现底座冻结

把共享长窗口、官方优化器/调度、梯度累积和 train-internal-dev best checkpoint 固定成 reproduction base。
该底座只证明输入/训练协议正确，不作为方法贡献。输出 causal/subevent 的 dev P/R/F1 与跨句分层。

### A3.2 Mechanism 1：关系族均衡联合目标

只改变关系族优化：采用归一化 family risk、自适应梯度平衡或等价非固定机制，避免 candidate 数量多的
族主导选模和梯度。MAVEN-ERE official joint 已有固定任务 loss factors，固定权重/网格/只改 best-checkpoint
选择不算新方法。设计必须同时给出 causal、subevent 的梯度/损失贡献和 P/R/F1。

seed 13 做 internal-dev pilot。只有实现、测试和协议 smoke 均通过才计一个核心设计周期；若 causal 不升
或 subevent 越过非劣界，允许第二个核心设计周期，第二次仍失败即停止，不扫连续权重网格。

### A3.3 Mechanism 2：类型/方向约束

只在 A3.2 冻结结果上加入事件类型表示与关系方向约束。类型词表必须随 checkpoint/bundle 保存；约束的
候选全集与 gold population 不得变化。它们是二级机制：失败时删除对应 claim，不消耗/重置核心预算，
也不阻断 A3.2 promotion；各自最多一次实现 + 一次定向修订。

### A3.4 Promotion 与三种子

只有 internal-dev pilot 同时满足以下条件才进入 13/17/42 完整训练：

- causal 高于 seed-13 primary anchor；
- subevent 通过预注册非劣 margin；
- 增益不是 candidate/阈值交换，跨句分层完整报告；
- A3.2 相对 reproduction base 的 causal document-cluster 95% CI 下界大于 0。

配置、代码、checkpoint、阈值 hashes 与 final-valid access ledger 冻结后，baseline/主锚/方法三种子在
同一个 sealed batch 中运行 final valid；final valid 不反馈到结构、阈值、epoch 或候选选择。只有未返回
指标且 hashes 完全一致的基础设施失败可原样重试；否则相关运行标 `exploratory`。

### A3.5 导出与端到端副表

无论最终 pass/failed，都导出冻结的 710-doc gold-mention 逐 pair probabilities/labels，并投影到 Ch4 所需
graph edges；failed 产物保留身份。predicted-mention 端到端副表依赖后续 C4 bundle，推迟到 E3，不在 A3
用历史/代理 Ch1 产物提前闭环。

## Done when

- 至少三个 baseline 同协议主表完整；
- 我们三种子 causal 均值高于 primary anchor 和另一不同方法族强 baseline，且相对主锚的 document-cluster
  paired-bootstrap 95% CI 下界大于 0，至少 2/3 matched-seed delta 为正；
- subevent 通过预注册非劣界，逐族 P/R/F1 和跨句分层完整；
- adaptive family-balance 核心消融齐全；实际保留的 type/direction claim 才要求对应消融；
- stage bundle hashes/IDs/schema 校验 PASS；
- `docs/results/PHASE_A.md` 追加 v6 小节，本文件不复制数字；
- 本地三件套全绿，4090 checkpoint/log 位置可追溯。

## Stop conditions

- 两个有效核心设计周期后 causal 仍不超过同 split primary anchor，或 subevent 越过非劣界：停止主方法；
- 任何增益只来自 valid 选模、candidate population 改变或 evaluator 差异：结果作废并退回 P1；
- 类型/方向二级机制无效：删除其方法主张，不增加核心周期，不用 temporal/TIMEX 或更大 backbone 补洞；
- 全局 manifest/evaluator 漂移：停止全链并回到 P1；仅某 baseline checkout 漂移：冻结当前 A3 为 failed/
  blocked handoff，不污染 D3；
- 方法失败时输出 `status=failed`，保留长上下文复现与关系族冲突诊断，作为系统组件交给 D3/E3；
- 不进行第三轮超参/结构搜索，不转 MATRES，不增加外部语料。

## Handoff

无论 pass/failed/blocked，都交付可校验 bundle 和明确 evidence identity。D3 可以继续，但 E3 引用 A3 预测时必须
保留其 status，不能把 failed bundle 写成“改进后的关系图”。

## GPU

4090 单卡。先展示命令、`/data/TJK/ekg` 工作目录和预期 `runs/stages/a3/...`、checkpoint、log。
5090 仅在作者逐次授权后作备用，不跨机搬 checkpoint，除非作者另行决定。
