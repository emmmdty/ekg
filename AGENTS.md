# EKG · coding agent 上下文

> `CLAUDE.md` 与 `AGENTS.md` 内容一致（Claude Code 读前者，Codex 读后者）。**改一份必须同步另一份。**
> 本文件每次会话都入上下文，**只放「删掉就会出错」的东西**；细节一律放下面的文档，按需读。

**新会话只读 `docs/HANDOFF.md`** 作为交接入口（状态快照 · 规矩 · 坑 · 下一步优先级）。
Claude 与 Codex **交替推进同一条队列**：开工前按 `HANDOFF.md` 任务 E.0 的六条约束对齐（HEAD 必须等于 `origin/main`、单队列、改计划先改文件、不开分支/worktree、活动任务独占产物、交接必须已 push）。
根目录不再维护 `task_plan.md`、`findings.md`、`progress.md`；阶段完成、出现新证据或关键决策时直接
写回 `docs/HANDOFF.md`，不要恢复 planning-with-files 工作流。

研究宪章 `.specify/memory/constitution.md`｜稳定需求 `docs/SPEC.md`｜可迭代设计 `docs/RESEARCH_PLAN.md`｜
可执行任务 `docs/TASKS.md`｜**完整实验规划（防漂移主表）`docs/EXPERIMENT_PLAN.md`**｜**对手名册与复现保真度 `docs/BASELINE_ROSTER.md`**｜实时状态 `docs/TODO.md`｜**实测数字 `docs/results/`**｜
baseline 与消融 `docs/EXPERIMENTS.md`｜工程坑 `docs/ENGINEERING_NOTES.md`｜
服务器运维 `docs/GPU_RUNBOOK.md`｜三端流水线 `docs/PIPELINE.md`｜归档索引 `docs/ARCHIVE_INDEX.md`。

**当前论文结构（2026-09-11 作者选定）**：第3章 事件事实性检测（D4）· 第4章 事件关系抽取（A4）·
第5章 事件身份消解（C5）· **第6章 事件图谱构建与下游事件预测应用（E3，带公开对手的应用章）**。
章序按把握度排，不按依赖。**Ch6 不要求胜过任何方法章**；原 24 条件 factorial、Holm 校正家族与
frozen-vs-fine-tuned 同 backbone 对照**已撤销，不得恢复**。
**可执行实验只认 `docs/EXPERIMENT_PLAN.md` 的防漂移主表**，`HANDOFF.md` 的 E 队列只是它的当周切片；
要偏离顺序先改主表。三个 Gate（D4.3 出结果 / A4.3+C5.3 出结果 / Ch6 名册冻结）是预先安排的
重规划时刻，Gate 之外不重排计划。
**SPEC v1.1.0**：QR-001 把 baseline 广度由准入门改为**主表报告要求**；FR-016 要求每个外部复现带
保真度状态——(a) 在其原始基准复现出已发表数字（容差事前定），或 (b) 点名障碍、标「透明适配」、
逐条列差异。名册见 `docs/BASELINE_ROSTER.md`。
**实验质量的主要判据是证明方法有价值**（主表对手、消融、负控、误差分析），统计检验是锦上添花；
不要先去调效应量门槛或 seed 数。
旧 D3/C4 以及 A2/C3/D2/E2 禁止继续执行。
> P1 唯一可信根：`runs/stages/P1/p1-v6-20260831-r12/`，其 `protocol.json` SHA-256 为
> `0bd33e87e67c1e4b36afb335270cbd511377c412d16e87b835a3503f0aa58497`；A3 命令必须显式传入。
> ⚠️ **学位论文标尺**：Ch1–Ch3 必须在统一重跑的公开主指标上超过多个方法；低于 baseline 时方法章
> 贡献为零。Ch4 使用公认 MRR/Hit@k 与配对统计，进入结论的消费者必须超过多个同协议对照，但
> consumer×quality 效应允许为正、零或负。自造辅助指标只能诊断，不能代替主指标。
> 所有 phase 先过 manifest/evaluator/baseline 闸门；单次高分、不同 split 论文数字或代码存在均不算过线。
> 旧机制两个周期失败只封存该机制家族，不自动取消方法章；新家族必须回 R1 证明文献差异、因果链、
> ≥80% 目标 power 与单变量消融，禁止换名、扫参或更大 backbone 绕过止损。

旧 TKG 线在 tag `frozen-tkg-line`；SARGE/金融层（2026-07-27）、生成式抽取+RL 线（2026-07-29）、
v4/v5 旧 phase 已归档或标 `SUPERSEDED`。治理冲突认 constitution，需求冲突认 SPEC，技术方案认
RESEARCH_PLAN，运行事实认 `docs/results/`；不得用下层文档改写上层含义。

## 校验命令（改代码后必跑）

```bash
uv run pytest                          # 全绿，只增不改
uv run ruff check src tests scripts    # 0 error，≤100 列
uv run ekg-smoke                       # CPU 端到端冒烟
```

## 硬约束

- **单一事实源**：实验数字只在 `docs/results/PHASE_X.md` 里权威，别处只引用不复制。
  引用**外部**对标数字前必须回一手表格核实出处、split、口径——Phase C 因此白跑两轮、
  Phase A 因此把「达标」判错。
- 报告结果**如实**：数字降就说降；ssh/工具失败不得伪装成结论；负结果是交付内容，不是待修的 bug。
- 包/函数名**不得含 `ch1/ch2/ch3`**；新组件走 registry + lazy import；GPU 组件配 CPU 缓存回放。
- **`EventNode` schema 零新增字段**（扩展用 `metadata`）；`tests/core/test_propagation.py` 是测试锁。
- 代码简洁、fail-fast，**不加掩盖问题的 fallback / 默认值**。
- **专利与论文写作不在计划范围。**
- 本地是 git 仓库（分支 `main`）。**可自行提交/推送**（作者 2026-08-29 解除旧约束）；要求是 git 整理干净、内容不丢失、可回滚：按逻辑单元分次提交、写清改了什么、不强推。

## 开工自审：每个新任务先答两个问题（作者 2026-09-13 定）

拿到任何新任务、或准备写任何新机制之前，**先把这两条答出来并写进交接/结果页**，不要边做边想：

1. **科研价值**：这件事做成了能支撑什么论断？对准的是哪张主表、哪个门？
   证据在哪（结果页的哪张表、文献的哪个数字）？**不得拿「成本低 / 快」当选型理由。**
   引用文献时必须核到**机制本身**（代码或正文），不是摘要措辞——DREEAM 的 "without evidence
   annotations" 与 `crosssentence.py` 的动机段都是在这一步栽过的。
2. **可行性**：能不能在我们的数据、协议、机器上真的跑出来？

**可行性一旦不成立，必须点名是哪一方面，然后停下交作者裁决，不得自己换题绕开**：

| 不可行的方面 | 判据 | 例 |
|---|---|---|
| **数据** | 需要的标注/语料我们没有，且拿不到 | DREEAM 要人工证据标注 + 10 万篇 distant 语料，MAVEN-ERE 两样都没有 |
| **协议** | 做法与冻结口径冲突 | 它的增益靠 dev 选阈值，而 A4 契约禁扫 threshold |
| **代码** | 没有可运行实现，重写就不叫复现 | ACCI 全历史只有 README |
| **算力/时间** | 超出预算或排期 | 每对逐句留一法 ≈ 千万次前向 |
| **授权** | 需要作者点头的机器、多种子、跨机搬运 | 5090 超过一天的任务、seed 17/42 |

写法：**「X 不可行，卡在【数据/协议/代码/算力/授权】的哪一条 + 一手证据 + 我建议的替代」**，
然后等裁决。把「可行性」笼统写成「有难度」不算完成这一步。

## 约束分级：限制该限制的，别把整个系统焊死

规则不是一律同权。执行前先判断它属于哪一类，判据只有一句：
**不遵守它，是会让结论变错，还是只会让进度变慢？**

**A 类 · 有效性（绝不为进度让步）** —— 违反则跑出来的数字无意义或已被污染：
final-valid 封存且不用于选模｜主锚在看到方法结果前冻结｜口径三轴（manifest · 候选全集 ·
evaluator）完全一致｜训练与推理口径成对（如 TIMEX 开关）｜不拿更弱的对手充数｜
配对统计与噪声地板｜跨章 ID 对齐、缺失即 fail-fast｜数字只在 `docs/results/` 且升降如实。

**B 类 · 可追溯（形式可调，实质不可弃）** —— 能从论文表格反查到 commit、hash、命令、
checkpoint 位置。哪些文件进哈希集合、bundle 长什么样、信任根怎么组织，**都可以改**；
「别人能复现这张表」不可以丢。

**C 类 · 操作性（按现场情况调整，不必照章办事）** —— 并发还是串行、用哪张卡、先跑哪个
baseline、epoch 预算、何时止损、任务怎么排。**由实际资源与成本决定**。
例：**卡空着就并行**，不要因为某个契约里写过「每次只跑一个实验任务」而让三张 GPU 闲置——
那句话保护的是资源不打架，不是结论正确性。

⚠️ 已犯过的错：把 C 类当 A 类照章执行，把 11 小时的工作串成一条线，而三张卡全空。
把哈希集合解耦了却没有解耦自己的判断，等于没解耦。

## 不重复造轮子

GitHub 上已有且可运行的实现**直接用**（官方 baseline 代码、公开方法实现、成熟库）。
我们只在本地对**自己的项目**做适配、接线与优化；不要重写别人已经发布的东西。
允许为跑通做透明补丁（环境、路径、数据接口、checkpoint 载入），但必须记录补丁与前后 hash。

## 服务器（`gpu-4090` 主 `/data/TJK/ekg`｜`gpu-5090` 备 `/mnt/aidata/tongjiakai/ekg`）

- **GPU 授权**：4090 有空即可自用，本地三件套全绿后无需逐次点头；**5090 须逐次问用户**。
  选卡前 `nvidia-smi` 核卡，不挤占他人正在跑的卡。
- **多种子必须逐次授权**：探索阶段每个方案只跑一个冻结 seed。只有本轮所有待比方案的单种子都超过
  各自 baseline 和护栏，且用户再次明确允许后，才可启动额外 seeds。GPU 并行只用于不同方案/任务，
  不得用于未授权的多种子。
- **checkpoint 训在哪就留在哪，不强制回传**（作者 2026-08-06 改；原「一律回传 4090」
  在 4090 隧道断掉时反而卡死工作）。**要跨机搬运先问用户**——单程约 70 分钟，值不值得由用户定。
  档在哪台**必须记进 `docs/results/`**；失败/发散档只留数字，权重不必留。
- ⛔ **服务器上不要跑 `uv run` / `uv sync`**——会按 extras 卸包（实测卸 165 个，torch 全没）。
  一律 `.venv/bin/python`；非用 uv 不可时加 `--no-sync`。
- ⛔ **禁 `rsync --delete` 与远端 `git clean -fdx`**（会删 `runs/`、`nvmlshim/` 等 remote-only 产物）。
- **ssh 失败 ≠ 远端进程死亡**（cpolar 隧道会掉线）：三态判活 ALIVE / GONE / ssh 失败，
  只有成功 ssh 读到进程 GONE 才算结束。判活看 `ps -eo etime` 或 `nvidia-smi`，别靠对时间的感觉。
- 代码走 git（远端 `git fetch && git reset --hard origin/main`），**数据/产物走 `scp`/`rsync` + 双端 `sha256`**。
- 长任务用 `setsid nohup` + `python -u`，输出重定向 `logs/`；**一条 ssh 只发一个后台任务**。
- 非交互 ssh 里 `python`/`jq`/`rg`/`tmux` 可能不在 PATH，用绝对路径或 `bash -lc`。
