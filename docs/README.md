# 文档入口与分类规则

从本页进入项目文档。读者不需要在同类历史文件之间猜哪个更新。

## 项目目录速览

```text
ekg/
├── .specify/memory/constitution.md  # 不可妥协的研究与开发原则
├── src/ekg/          # 可复用的领域代码与 registry 组件
├── scripts/          # 训练、评测、协议物化和诊断入口
├── tests/            # 单元、协议反例与回归测试
├── data/             # 原始/处理数据、manifest、protocol（多数不进 Git）
├── runs/             # checkpoint、prediction、metrics、stage bundle（不作代码源）
├── logs/             # 远端/长任务日志
├── docs/             # 规范、状态、结果、报告和归档
├── AGENTS.md         # Codex 每会话硬约束
└── CLAUDE.md         # 与 AGENTS.md 同步的 Claude Code 约束
```

代码按功能命名，不按 `ch1/ch2/ch3` 命名；实验身份由 `runs/stages/<phase>/<run-id>/` 表达。
`data/` 与 `runs/` 是产物区，不能反向成为代码或文档的隐式事实源。

## 当前工作入口

1. [`HANDOFF.md`](HANDOFF.md)：新会话先读，记录最新状态、可信根和下一步。
2. [`SPEC.md`](SPEC.md)：稳定的 WHAT/WHY、研究场景、需求与可量化成功条件，不指定具体方法。
3. [`RESEARCH_PLAN.md`](RESEARCH_PLAN.md)：可随证据修改的 HOW、候选假设、架构与评测设计。
4. [`TASKS.md`](TASKS.md)、[`phases/`](phases/README.md)：由 plan 派生的任务与阶段契约。
5. [`TODO.md`](TODO.md)：只记录当前运行状态和最近动作。
6. [`results/`](results/README.md)：实验数字唯一权威来源。

## 按用途分类

| 类别 | 位置 | 内容 | 是否可作当前指令 |
|---|---|---|---|
| 研究治理 | `.specify/memory/constitution.md` | 不可妥协原则、修订规则、SDD 分层 | 是，最高治理层 |
| 稳定需求 | `SPEC.md` | WHAT/WHY、场景、需求、成功条件、边界 | 是，不含实现方案 |
| 可迭代设计 | `RESEARCH_PLAN.md`、`PIPELINE.md`、`EXPERIMENTS.md` | HOW、候选方法、架构、评测设计 | 是，受 SPEC 约束 |
| 活动状态 | `HANDOFF.md`、`TODO.md` | 当前事实、优先级、阻塞 | 是，但不能修改需求 |
| 任务清单 | `TASKS.md` | 从 plan 派生、可独立验证的任务 | 是 |
| 阶段契约 | `phases/` | 每阶段准入、命令、验收 | 仅 active phase |
| 实测结果 | `results/` | 数字、口径、负结果、产物位置 | 数字权威，不是任务队列 |
| 汇报材料 | `reports/` | 按日期冻结的对外叙述 | 否；以文件日期为准 |
| 研究重规划 | [`replan/`](replan/README.md) | 文献审计、方向论证、历史决策 | 否；只提供依据 |
| 工程与运维 | `ENGINEERING_NOTES.md`、`GPU_RUNBOOK.md` | 已知坑、服务器操作 | 是 |
| 历史归档 | `ARCHIVE_INDEX.md` | 被替代路线与索引 | 否 |

## 命名与单一事实源

- 稳定 SPEC 不记录 phase 状态、具体模型或执行顺序；这些分别进入 plan、tasks 和 handoff。
- 阶段契约使用 `PHASE_<代号>_<主题>.md`；索引必须区分确认性运行、准备性任务和真实证据依赖。
- 结果使用 `results/PHASE_<代号>.md`；数字只能在这里被修订，其他文档只引用。
- 对外报告使用 `YYYY-MM-DD_<主题>.md`，文件日期之后的进展不得倒填成当时已完成。
- 原始论文检索和方向审计放 `replan/`，不得把研究建议直接当成活动实验指令。
- 被替代内容保留证据但标 `SUPERSEDED`，并从 `HANDOFF`/`TODO` 的活动入口移除。

活动目录只保留当前可执行契约。被取代的一次性执行文档从工作树移除，但必须在
[`ARCHIVE_INDEX.md`](ARCHIVE_INDEX.md) 记录精确 Git 取回点；实验结果和封存 bundle 不随文档归档而删除。
