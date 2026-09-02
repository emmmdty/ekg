# EKG — 事件图谱构建及其下游评估

EKG 面向文本事件图谱，研究事件身份消解、事件关系抽取、事件事实性检测，以及构建错误对下游消费者的影响。
所有进入结论的结果都必须绑定固定 manifest、候选全集、评测器、配置、代码和产物身份。

当前研究设计为 **v6 四章**：三个方法章加一个系统评估章。权威设计见
[`docs/SPEC.md`](docs/SPEC.md)，实时状态与唯一下一步见 [`docs/HANDOFF.md`](docs/HANDOFF.md) 和
[`docs/TODO.md`](docs/TODO.md)。历史路线、旧 phase 和重规划材料不构成当前执行指令。

## 研究结构

| 章 | 任务 | 主要数据 | 主指标 | 代码域 |
|---|---|---|---|---|
| Ch1 | 事件身份消解 | MAVEN-ERE | MUC F1；B³/CEAFe/BLANC 副报 | `ekg.nodes` |
| Ch2 | 事件关系抽取 | MAVEN-ERE | causal micro-F1；subevent/temporal 强制副报 | `ekg.relations` |
| Ch3 | 事件事实性与证据联合检测 | MAVEN-FACT | macro-F1 与 evidence span F1 | `ekg.factuality` |
| Ch4 | 构建错误的下游代价与消费者依赖性 | CGEP-MAVEN | MRR、Hit@k 与配对效应 | `ekg.succession` |

阶段严格按 [`docs/phases/README.md`](docs/phases/README.md) 的唯一活动链推进。实验数字只在
[`docs/results/`](docs/results/README.md) 中维护，其他文档只引用，不复制为新的事实源。

## 目录

```text
src/ekg/          可复用领域代码与 registry 组件
scripts/          训练、评测、协议冻结和诊断入口
tests/            单元、协议反例与回归测试
configs/          独立评测样例与历史兼容配置；状态见 configs/README.md
data/             原始/处理数据与冻结协议（多数不进 Git）
runs/             checkpoint、prediction、metrics、stage bundle（不进 Git）
docs/             规范、状态、结果、报告和归档索引
```

文档分类和阅读顺序见 [`docs/README.md`](docs/README.md)。旧金融/TKG、生成式抽取/RL 等已退出主线的内容
只通过 [`docs/ARCHIVE_INDEX.md`](docs/ARCHIVE_INDEX.md) 和 Git 历史追溯。

## 本地验证

```bash
uv sync --extra dev
uv run pytest
uv run ruff check src tests scripts
uv run ekg-smoke
```

本地只做 CPU 验证。GPU 任务的授权、环境和启动规则见
[`docs/GPU_RUNBOOK.md`](docs/GPU_RUNBOOK.md)；服务器不得运行 `uv run` 或 `uv sync`。

许可：MIT
