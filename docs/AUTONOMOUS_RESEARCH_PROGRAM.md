# 受约束自驱动研究计划

> 作者于 **2026-10-02** 要求将后续研究与实验改造成自驱动闭环。本文件定义这个闭环的权限、
> 交付物和停止规则；它不是新的论文方法、不是自动调参系统，也不改变 `SPEC.md`、冻结指标或
> 已封存机制。可执行队列仍以 `EXPERIMENT_PLAN.md` §4 为唯一主表，实验数字仍只写入
> `docs/results/`。

## 1. 要解决的问题与成功标准

项目此前的低效不在于“没有多跑几次”，而在于外部代码的运行接口、数据/评测协议和科研决策没有在
上卡前拆开验证。G-19 的透明适配已经说明：必要的工程排障可以与结果导向调参严格区分；LLMERE
则说明：在花 GPU 前发现协议冲突，正确动作是停止而不是另写一个看似可行的 driver。

因此这里的“自驱动”有一个窄、可验证的含义：AI 可自行把一项研究问题从一手资料检索推进到
**证据卡 → 准入审计 → 冻结实验合同 → 单 seed 执行 → 独立评分**；每一步都必须产出可检查文件，
且只能按预先写明的状态转换。它不表示 AI 可因分数不佳而自行换指标、换数据、扫参数或创造新叙述。

这一轮的科研目标是：为事件事实性、关系和身份消解三个方法章寻找并严格验证**尚未被封存家族覆盖、
能在现有数据与公开比较协议下成立的贡献机会**。成功不是“启动更多训练”，而是至少形成一份：

1. 对准一张方法章主表、一个公开强对照和一个可证伪因果链的候选研究卡；
2. 有一手论文、官方实现/数据/许可和 P/V/U 口径的逐项证据；
3. 通过数据、协议、代码、算力、授权和前瞻 power 的全部准入门，才产生一个冻结的单 seed 合同；
4. 由 raw output 独立复算的主指标、最强对照、单变量消融和负控共同支持或否定该机制。

若没有候选能过第 2–3 条，结论是“本轮未找到可成立的新机制”，而不是把旧家族改名重开。作者若已授权 E 层，
E 层通过只说明外部验证协议可审计，**绝不**等价于新机制通过。

## 2. 为什么不是“完全自动的 AI 科学家”

可借鉴的不是宣传语，而是已经可核验的能力边界：

| 一手资料 | 对本项目的含义 |
|---|---|
| [PaperQA2（2024）](https://arxiv.org/abs/2409.13740) | 有引用检索 agent 能显著加快文献定位、综合和矛盾发现；每张研究卡仍须把结论落到原文表格、正文或官方源码的确切位置。 |
| [MLAgentBench（2024）](https://arxiv.org/abs/2310.03302) | ML 实验 agent 的最佳平均成功率只有 37.5%，且长期规划与幻觉是主要障碍；因此不能让一个 agent 看结果后无限制地改配方。 |
| [MLE-bench（2024）](https://arxiv.org/abs/2410.07095) | 最佳 scaffold 在真实 ML 比赛中达到至少铜牌线的比例为 16.9%；GPU 空闲不是无约束探索的理由。 |
| [AILA / AFMBench（2025）](https://www.nature.com/articles/s41467-025-64105-7) | 多角色和安全协议能改善复杂实验工作流，但模型会在工具协调和轻微指令变化上失稳；本项目采用不可互相认证的角色与 fail-closed 门。 |
| [Autonomous chemical research with LLMs（2023）](https://www.nature.com/articles/s41586-023-06792-0) | 可将规划、文档检索、代码/工具调用分开；在计算研究中相应地把文献、协议、集成、执行和评分拆开。 |

所以，AI 负责高吞吐、可回溯的子任务；结论有效性来自冻结的 manifest、候选全集、official scorer、
独立审计和作者明确保留的权限边界。`AI_RESEARCH_WORKFLOW_AUDIT.md` 已将这一原则应用到 G-19/G-20。

## 3. 自驱动状态机与角色分工

```text
研究问题
  → R0 证据卡 → R1 来源/协议红队 → R2 真实数据 CPU 预检
  → R3 受限 smoke → R4 冻结单 seed 正式运行 → R5 独立评分/声称审计
                         │                         │
                         └──任一硬门不通过──→ 命名阻断 / 作者决策卡
```

| 角色 | AI 可自主完成的动作 | 交付物 | 不能决定的事 |
|---|---|---|---|
| 证据研究员 | 检索一手论文、官方仓库、数据/许可与公开表格 | `research card`：来源链接、定位、研究空缺和反例 | 不能以摘要、二手博客或模型记忆认定新颖性/数字 |
| 协议红队 | 比对 split、候选全集、标签、evaluator、训练—推理信息流 | P/V/U 表、leakage 与差异清单 | 不能放宽 A 类有效性规则 |
| 集成审计员 | 静态追踪 import、loader、模型、路径、副作用；运行无分数 CPU 预检 | 运行接口清单、输入/输出 hash、可行性结论 | 不能在失败时重写外部方法或替换数据 |
| 执行员 | 在通过 R3 后执行唯一冻结命令、写 immutable output、监视运行 | command、manifest、日志、raw output | 不能依据中途/正式分数改超参、prompt、阈值或样本 |
| 独立审计员 | 重新 export/score、核覆盖/哈希与允许论断 | result audit、P/V/U 与 FR-016 登记 | 不能修运行代码或替执行员选择较好输出 |

同一人或同一个 AI 可以依次承担角色，但一个 run 内不得同时“按结果改配方”又“认证改后结果”。

### 3.1 可自动通过与必须停止的条件

AI 可不再询问作者而自行推进的范围是：只读检索、源码/数据静态核验、文档更新、CPU 预检、受限 smoke、
4090 空闲时已经通过所有门的**单一冻结 seed-13**命令，以及独立复算。启动任何远端 GPU 命令前仍需在
工作记录中先给出确切命令、cwd 和预期产物。

下列事件强制生成“作者决策卡”，不得自行绕行：数据或许可拿不到；协议需要改变；官方代码不存在而重写会
不再是复现；计算/排期不可行；额外 seed、5090、跨机 checkpoint 搬运；新标注、final-valid、指标/主锚/论文
结构的改变；或全部候选在 R1 前被否定。决策卡固定写“卡在哪一类 + 一手证据 + 可选后果”，不以“有困难”
含混代替。

## 4. 后续队列（主表的 C-31 起）

| 阶段 | 科研问题与交付 | 自动推进条件 | 通过 / 停止 |
|---|---|---|---|
| **C-31 · 领域证据地图** | 围绕 MAVEN-ERE/MAVEN-FACT 事件理解，建立最多三个候选研究卡；每卡必须核论文机制、最近邻重叠、公开代码/数据、P/V/U、可证伪因果链与预算。 | C-30 完成；只用公开资料与本地只读资产。 | 至少一张卡有可验证的科学价值与全项可行性 → C-32；全部不成立 → 作者决策卡，不开训练。 |
| **C-31b · 授权后的外部 benchmark 卡** | 作者明确许可时，选定至多一个与主任务相邻、已有公开标注和许可的 external-validation benchmark；固定其 E 层声称边界及不相容的公开实现。 | 作者已授权该范围；MAVEN 主表、指标、封存家族均不变。 | source/data/license PASS → C-32a；否则按【数据/协议】收口，不以“常被引用”代替可审计性。 |
| **C-32a · 外部协议准入** | CPU-only materialize source hash、topic/split、candidate universe、label mapping、scorer 与无模型覆盖审计。 | C-31b source card 完整。 | 全项 PASS 仅建立 E 层 baseline protocol → C-32b；任一歧义或不一致停止，不能借用相近论文 runner。 |
| **C-32b · 准入与冻结合同** | 对排名第一、尚未被否定的**新机制**卡执行 R1.1–R1.6：在 MAVEN 主表与 E 层分别写精确数据/候选/evaluator、强对照、power、单变量消融、负控、最小 smoke 和 stop 条件。 | C-32a 及候选卡的每项一手证据可复核。 | 全部 PASS → 把唯一具体候选写入主表并生成 phase contract；任一不可行按类别收口，不以近似方法替代。 |
| **G-21 · 合同绑定的单 seed 实验** | 只运行 C-32b 已冻结的一个正式方案；训练、selection、evaluation 和 raw 输出隔离。 | exact command、MAVEN manifest、ESC E protocol、evaluator/baseline、R2/R3 都 PASS，4090 空闲。 | 不论高低，覆盖/哈希/评分完成 → C-33；工程失败只在同一门、证明不改变科学语义后做最小修复。 |
| **C-33 · 独立结果与论文价值审计** | 由非执行角色从 raw output 复算主指标、最强对照、消融、负控与错误簿；报告 P/V/U/FR-016 与单 seed 边界。 | G-21 immutable output 完整。 | 机制、对照和护栏共同通过才可提出额外 seed 的作者请求；否则封存该家族并记录负结果。 |
| **C-34 · 研究回合复盘** | 检查本回合是否回答原始研究问题，而非只解决工程问题；将失败类型反馈到下一轮 C-31 检索约束。 | C-33 完成。 | 只在既定 Gate/作者决策卡处重排；不从结果倒推新假设。 |

“最多三个候选”只限制一次检索回合的审计负荷，不构成科研筛选门。候选排序先看能否支撑新的、可证伪的
论文论断和与强对照的差异，再看数据/代码/协议可行性；**从不按预估分数、运行便宜或 GPU 恰好空闲排序**。

## 5. 研究卡与决策记录的最小字段

每一张 C-31 卡必须有下列字段，写入 `docs/results/PHASE_R1.md` 的本轮结果节并在 `HANDOFF.md` 摘要链接：

```text
question / target chapter / target main table and gate
primary paper + official implementation + data/licence evidence (exact table/section/file)
claimed mechanism / nearest work and concrete difference / disconfirming evidence
P/V/U status; dataset, split, candidate universe, evaluator, input and backbone
causal chain: observed error → treatment → mediator → main outcome
strong baselines / one-variable ablation / negative control / power or MDE
data, protocol, code, compute, authorization feasibility (each PASS or named blocker)
R0–R5 state, immutable artifact locations/hashes, allowed claim and stop rule
```

这张卡就是 AI 的长期记忆和交接载体：下一轮 agent 必须从卡与原始产物继续，不能把聊天总结当证据。

## 6. 指标与效果的审查标准

该闭环不新增“AI 成功率”或“跑了多少实验”作为论文指标。论文层仍只承认冻结公开主指标：Ch3 的五类
macro-F1，Ch4 的 causal P/R/F1 与 Hit@k，Ch5 的 MUC/B³/CEAFe/BLANC，Ch6 的 MRR/Hit@k；辅助/诊断指标
不能替代它们。外部行均采用 P/V/U 与 FR-016，单 seed 一律标 `non-confirmatory`。

流程层只监控会影响有效性的离散事实：每道门是否有产物、是否发生禁止信息流、是否保留 raw output、失败是否
被正确分类。它们衡量的是“这次结论能否审计”，不是拿流程分数证明模型更好。这样设计是合理的：论文含金量
来自主指标上对强对照的价值、消融和负控，而不是 AI 运行次数；但没有这些流程门，再高的单次数字也无法可信比较。
