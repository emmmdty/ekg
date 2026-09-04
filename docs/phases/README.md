# EKG v6.1 阶段化执行手册

> 权威研究约束见 [`../SPEC.md`](../SPEC.md)，实时位置见 [`../TODO.md`](../TODO.md)，实验事实只认
> [`../results/`](../results/README.md)。本目录中的 runnable phase 是单会话可执行契约；历史 phase 只作证据。

## 当前依赖图（计划层，可修订）

```text
P1 协议冻结 ─→ A3 旧机制分账与失败交接 ─┐
           └→ R1 无依赖准备任务 ─────────┴→ R1 方法设计准入
                                            ├─ C5 Ch1 候选方法
                                            ├─ A4 Ch2 候选方法 ─→ E3 → H2
                                            └─ D4 Ch3 候选方法
```

这张图表达证据依赖，不是不可修改的研究路线。R1 的最终准入必须消费 A3 失败交接，但不读取 A3 待出
结果的文献、ID 和功效准备可先做；E3 必须等待
三个真实上游 handoff。C5/A4/D4 之间若 R1 没有识别出数据或模型依赖，可按资源并行或重排；文献审计、
ID 审计、CPU smoke 也可并行。每个 phase 仍须交付 `pass|failed|blocked` 的不可变 handoff，局部失败不自动
阻塞其他章，但后续必须保留其 evidence identity；全局协议失败才阻塞受影响的结论。

## 阶段索引

| Phase | 作用 | 当前状态 | GPU | 契约 |
|---|---|---|---|---|
| **P1** | 冻结 manifests、scorer、baseline smoke 与 stage bundle | **COMPLETED / PASS；r12；global=PASS，A3 entry=PASS** | 4090 协议前向已完成 | [`PHASE_P1_protocol_freeze.md`](PHASE_P1_protocol_freeze.md) |
| **A3** | Ch2 旧机制终局分账与失败交接 | **ACTIVE；下一步 A3.6，随后 `failed` handoff** | 4090 | [`PHASE_A3_relation_balanced.md`](PHASE_A3_relation_balanced.md) |
| **R1** | 三方法章的文献、ID、因果链、power 与 protocol 审查 | PREPARATION ACTIVE；promotion blocked by A3 handoff | CPU | [`PHASE_R1_method_design_freeze.md`](PHASE_R1_method_design_freeze.md) |
| **C5/A4/D4** | v6.1 三个新方法家族 | BLOCKED BY R1；契约由 R1 的冻结产物生成 | 4090 | 见 [`../replan/METHODOLOGY_REDESIGN_20260904.md`](../replan/METHODOLOGY_REDESIGN_20260904.md) |
| **D3/C4** | v6 旧方法契约 | **SUPERSEDED FOR FUTURE EXECUTION**；历史结果仍有效 | 不再执行 | [`PHASE_D3_evidence_conditioned.md`](PHASE_D3_evidence_conditioned.md)、[`PHASE_C4_context_identity.md`](PHASE_C4_context_identity.md) |
| **E3** | Ch4 本地重建 query 协议的消费者 factorial | BLOCKED BY C5/A4/D4 handoffs | 4090；5090 逐次授权 | [`PHASE_E3_factorial_consumers.md`](PHASE_E3_factorial_consumers.md) |
| **H2** | 汇总三种子、消融、复现与论文表格反查 | BLOCKED BY E3 | 视缺口 | [`PHASE_H2_thesis_acceptance.md`](PHASE_H2_thesis_acceptance.md) |

G0 实际筛查见
[`../replan/G0_PROTOCOL_GATE_SCREENING.md`](../replan/G0_PROTOCOL_GATE_SCREENING.md)。

## 每个 phase 的固定结构

每份契约必须包含：

1. **Goal**：可证伪的阶段问题；
2. **Inputs**：固定文件、hash、上游身份与禁止输入；
3. **Tasks**：按顺序执行的小任务，每项有验证命令或产物；
4. **Promotion gate**：何时允许从单种子 pilot 升三种子/完整实验；
5. **Stop conditions**：何时立即停止，失败后保留什么；
6. **Bundle**：`protocol/predictions/metrics/status` 与结果文档；
7. **GPU**：确切资源与开跑前置条件。

## 错误隔离与交接

每阶段交付不可变 bundle：

```text
runs/stages/<phase>/<bundle-id>/
├── protocol.json
├── predictions.jsonl    # 无逐实例预测的阶段可改为约定格式
├── metrics.json
└── status.json          # pass | conditional | failed | blocked
```

交给下一阶段前检查：

- bundle 外可信 protocol hash、source/manifest/candidate-ID/evaluator/config/code/checkpoint 外部重哈希与
  population counts；
- doc/query IDs 的数量、集合、重复和缺失；
- schema version 与 upstream status；
- `global_protocol_status`、primary anchor、结果是否 exploratory、final-valid 访问次数/是否曾用其选模；
- `metrics.json` 是否是 scorer 原始输出，而非从 Markdown 反抄。

失败 bundle 可以作为 baseline/negative-evidence 输入 Ch4，但必须保留 `failed` 身份。禁止把 gold proxy
改名为 predicted，禁止填空标签/空边让流水线继续，禁止覆盖旧 bundle。

## 两轮上限

- 一个 baseline 工程轮是一次有界“诊断→补丁→同协议 smoke”，最多两轮；第三轮不再修，候选降为背景
  并换预先列出的候选，候选失败不等于任务失败；
- 一个核心方法设计周期只在实现、测试和协议 smoke 均通过后计数；同一机制家族最多两个，两周期未过
  promotion 就封存该家族。章节若重开，必须回 R1 证明是实质不同的方法家族并冻结新 protocol；
- 二级机制失败只删除对应 claim，不消耗或重置核心预算；环境/路径/scorer/candidate bug 修复也不算
  科研机制；每个二级机制自身最多一次实现 + 一次定向修订；
- 失败后不得换 final split、删难例、换主指标、扩大模型或增加语料来逃避停止条件。

## 运行方式

新会话从 `docs/HANDOFF.md` 开始，再按其中链接读取当前 plan、tasks 和 runnable phase：

> 按 Tasks 与真实依赖执行；先核 bundle/hashes，
> 完成后逐项核 Promotion/Done/Stop，并将实验数字只写入对应 `docs/results/PHASE_*.md`。

改代码后统一运行：

```bash
uv run pytest
uv run ruff check src tests scripts
uv run ekg-smoke
```

启动任何远端 GPU 命令前，必须先向作者展示命令、工作目录和预期产物；4090 空闲可用，5090 每次单独
授权。服务器使用 `.venv/bin/python`，不得运行 `uv run`/`uv sync`。

## 被取代的契约

v5 的 A2/C2/C3/D2/E2/H 契约已从活动目录移除，避免文件名被误认为待执行任务。移除清单和精确 Git
取回点见 [`../ARCHIVE_INDEX.md`](../ARCHIVE_INDEX.md)。历史实测不因契约归档而作废，仍只以
[`../results/`](../results/README.md) 为准。
