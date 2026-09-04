# EKG v6 阶段化执行手册

> 权威研究约束见 [`../SPEC.md`](../SPEC.md)，实时位置见 [`../TODO.md`](../TODO.md)，实验事实只认
> [`../results/`](../results/README.md)。本目录中的 active phase 是单会话可执行契约；历史 phase 只作证据。

## 唯一活动链

```text
P1 协议冻结
  └─ A3 Ch2 baseline 与方法
       └─ D3 Ch3 baseline 与方法
            └─ C4 Ch1 baseline 与方法
                 └─ E3 Ch4 同实例 factorial
                      └─ H2 全篇三种子/消融/复现验收
```

严格串行是研究纪律，不是“上阶段必须 PASS”。任何时刻只能有一个 active phase；每个阶段必须先交付
`pass|failed|blocked` 的不可变 handoff，下一阶段才可开始。局部失败不自动阻塞后续章，但后续必须保留
其 evidence identity；全局协议失败才阻塞全链。论文写作仍按 Ch1→Ch2→Ch3→Ch4。

## 阶段索引

| Phase | 作用 | 当前状态 | GPU | 契约 |
|---|---|---|---|---|
| **P1** | 冻结 manifests、scorer、baseline smoke 与 stage bundle | **COMPLETED / PASS；r12；global=PASS，A3 entry=PASS** | 4090 协议前向已完成 | [`PHASE_P1_protocol_freeze.md`](PHASE_P1_protocol_freeze.md) |
| **A3** | Ch2 关系族×位置工作点及后续判别机制 | **ACTIVE；工作点线与近似 retriever 均已 FAILED 封存，下一步是 A3.6 官方配方分账** | 4090 | [`PHASE_A3_relation_balanced.md`](PHASE_A3_relation_balanced.md) |
| **D3** | Ch3 evidence-conditioned 事实性 | BLOCKED BY A3 handoff | 4090 | [`PHASE_D3_evidence_conditioned.md`](PHASE_D3_evidence_conditioned.md) |
| **C4** | Ch1 语境判别身份消解 | BLOCKED BY D3 handoff | 4090 | [`PHASE_C4_context_identity.md`](PHASE_C4_context_identity.md) |
| **E3** | Ch4 本地重建 query 协议的消费者 factorial | BLOCKED BY C4 handoff | 4090；5090 逐次授权 | [`PHASE_E3_factorial_consumers.md`](PHASE_E3_factorial_consumers.md) |
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
- 一个核心方法设计周期只在实现、测试和协议 smoke 均通过后计数，最多两个；两周期都未过 promotion
  才触发该 phase 止损；
- 二级机制失败只删除对应 claim，不消耗或重置核心预算；环境/路径/scorer/candidate bug 修复也不算
  科研机制；每个二级机制自身最多一次实现 + 一次定向修订；
- 失败后不得换 final split、删难例、换主指标、扩大模型或增加语料来逃避停止条件。

## 运行方式

新会话只需：

> 读取 `AGENTS.md`、`docs/SPEC.md` 和当前唯一 active phase，按 Tasks 顺序执行；先核 bundle/hashes，
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
