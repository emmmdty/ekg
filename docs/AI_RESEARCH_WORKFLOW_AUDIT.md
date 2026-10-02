# C-29.5 · AI 辅助科研流程审计与 G-20 执行就绪包

> **完成于 2026-10-02；C-29.6 只读复核随后补入。** 本文是一次流程纠偏，不是论文机制、实验结果或指标设计变更。
> 它不读取 final-valid、不改任何分数，也不授权 G-20 上卡。结论先行：**G-20 不执行；作者已取甲，
> 将它收口为 FR-016(b) 无可评分行。** 原因不是分数或算力，而是【协议】规定的 target-third-line stop
> 无法不用 internal-dev gold 实现。

## 1. 决策与边界

我们不把 G-19 的低分解释成“又一次试错失败”。它的正式运行已合格地收口为一条 FR-016(b) 透明适配：
raw output、覆盖、export 和官方 scorer 都可复算；近乎全 singleton 的输出是研究结果，不是应被修掉的 bug。
权威数字和禁止论断仍只见 `results/PHASE_R1.md` §25.28。

真正需要纠正的是**执行方式**：外部研究代码的隐含运行条件、项目数据的语义条件、输出副作用和论文有效性条件，
以前没有在同一张“执行就绪包”中被逐项证明。于是 agent 只能在运行报错后发现一个条件、修一个条件、再发现下一个；
这些修复大多是合理且透明的，但工作流看起来像是在边跑边决定研究。

本次采用以下决定：

1. AI 可以加速检索、源码追踪、清单比对和独立复算，**不能**因一个 smoke 分数、格式错误或正式结果自行改
   科研假设、阈值、backbone、数据切分或评价口径。
2. 每次新外部方法执行前先形成可审查的执行就绪包；每一项必须有“通过证据”或明确的
   【数据 / 协议 / 代码 / 算力 / 授权】阻断，不能用“应该能跑”代替。
3. G-20 前插入 **C-29.6：LLMERE 恢复推理静态契约核验**。它只读检查 target-independent stop 是否存在，
   不训练、不产生论文分数、不运行 GPU。它已判定 C-3 的当前 stop 规则不合法；本轮不启动 G-20。

这项流程的科研价值是保护 Ch4 U 层外部 baseline 的可追溯与有效性，避免工程调试意外变成结果导向调参；
它本身不为任何方法章增加“方法贡献”。在现有代码、日志和公开资料上可完成，不涉及数据、协议、算力或授权障碍。

## 2. 其他团队怎样把 AI 放进科研流程——可采纳的证据，而非照搬宣传

| 一手来源 | 已核实的做法 / 限制 | 本项目采用的窄结论 |
|---|---|---|
| [Google AI co-scientist 技术说明（2025）](https://research.google/blog/accelerating-scientific-breakthroughs-with-an-ai-co-scientist/) | 将 Generation、Reflection、Ranking、Evolution、Proximity、Meta-review 分成专职角色，由 Supervisor 分配任务；研究者可给约束和反馈。其自身也把系统定位为 collaborative tool，并列出 factuality checking、外部工具交叉核验和更大规模专家评估仍是限制。 | 借鉴“角色分离 + 反思/复核”，不采纳其自动 Elo 作为科研真值。项目中每个 AI 角色只交可验证产物，结论必须由原始数据/源码/official scorer 支撑。 |
| [PaperQA2 人机比较（2024）](https://arxiv.org/abs/2409.13740) | 文献检索、归纳、矛盾发现可由有引用的 agent 加速；作者同时明确科学使用对 factuality 和细节极敏感。其随机 biology 样本中所报矛盾仍需专家验证。 | AI 用于一手文献和代码的“候选证据定位”，交付 URL、表号/代码位置和适用口径；不能把模型摘要或引用列表当成已核实事实。 |
| [MLAgentBench（ICML 2024）](https://arxiv.org/abs/2310.03302) | agent 能读写文件、运行代码和检查输出，但最佳设置在 13 个 ML experimentation 任务上的平均成功率仅 37.5%，且作者点名长期规划和幻觉问题。 | 不允许单一 agent 连续地“读结果 → 改方案 → 再跑”。执行切成有输入/输出契约的短阶段，失败只能退回相应阶段。 |
| [MLE-bench（OpenAI，2024）](https://arxiv.org/abs/2410.07095) | 真实 ML engineering 比赛中，最佳 agent scaffold 达到至少 Kaggle 铜牌的比例为 16.9%。 | GPU 空闲不是交给 agent 自主探索的理由；先做静态预检和受限 smoke，正式运行只执行冻结配方。 |
| [Good enough practices in scientific computing（PLOS，2017）](https://doi.org/10.1371/journal.pcbi.1005510) 与 [research software robustness（PLOS，2017）](https://doi.org/10.1371/journal.pcbi.1005412) | 可复现计算要求保存原始/中间产物、记录处理步骤、明确依赖和版本；研究软件常含本机路径、未说明资源或过期依赖，导致“作者机器可跑”不等于可移植。 | AI 产生的动作也必须进入同一 provenance 链：输入 hash、上游/补丁 revision、命令、环境、输出、评分器和失败日志。对外代码先审隐式路径、全局状态、资源和输出副作用。 |

因此，别人的成熟形态并不是“把科研完全交给 AI”，而是**让 AI 做高吞吐的受约束子任务，再用独立证据门和
人的研究约束把它们接起来**。这也解释了为什么本项目应采用简单的执行就绪包，而不是增加一个会自行改设计的
“自动研究员”。

## 3. 对本项目反复试错的具体反思

### 3.1 G-19 中发生了什么

| 阶段 | 已观察事实 | 当时正确的处置 | 暴露出的流程缺口 |
|---|---|---|---|
| import 前 | EasyECR 在 `common_path.py` 把全局 `tempfile.tempdir` 写到不存在的 `/home/nobody/code/tmp/`；smoke-v1 在 CUDA 分配前失败。 | 只在 runner 进程中指向本次 immutable output 的 `temporary/`，不改模型或协议。 | 静态 preflight 未列“导入时修改的全局路径 / 目录须存在”这一副作用契约。 |
| 真实首 batch | smoke-v2 的一篇文档只产生 64 个 verb/entity 词，而发表实现固定 `dist_dim=500`；正式全量输入实际可达 500。 | 不把 `dist_dim` 调小；先用同一 upstream spaCy 规则对 train、selection、evaluation 审计，固定 16-document smoke。 | “小样本 smoke”只验证了控制流，没有先验证模型的全局统计前提；缩略数据不能任意抽。 |
| prediction 生命周期 | upstream predict 自行创建未配置的 Lightning Trainer，默认相对路径会把 `lightning_logs/` 写到 repo 根。 | runner 只在该调用期间切换 cwd，使日志随 immutable run 归档，退出恢复。 | training path 的配置审查没有覆盖 prediction path 的隐藏第二个 Trainer 与文件副作用。 |
| 正式分数 | fixed seed、独立 selection-dev 的 0.9 threshold、无标签 evaluation 和 official scorer 均按冻结口径完成；结果为 7,188 clusters，其中 7,181 singleton，MUC F1 1.379310。 | 报告负结果；不回调 threshold、不重训、不换 backbone。 | 这一项没有流程失效。科学判定和工程错误被正确分开，必须保留。 |

记录在 `HANDOFF.md` 的 smoke-v1/v2/v4、`COMPARABILITY_PLAN.md` 与 `results/PHASE_R1.md` §25.28 已足以
复核上表；对应提交链为 `4d2078e`（tempdir）、`81f8406`（词表审计）、`5f447f9`（prediction 日志隔离）、
`f483bda`（完整 smoke）和 `fc83112`（结果收口）。

### 3.2 根因不是“AI 不会科研”，而是缺一个明确的接口层

1. **外部代码被当作论文方法，而不是有隐藏接口的运行组件。** 文献/README 能证明方法存在，不能证明它的
   tempdir、固定词表宽度、第二个 Trainer、环境变量和相对输出路径在本项目成立。
2. **smoke 定义得太像“尽快跑到 GPU”，而不是“证明真实执行前提”。** 一篇文档能测到 CUDA，却不能满足
   `dist_dim=500` 的 corpus 级条件；因此反而引入了一个与正式运行无关的失败。
3. **训练、推理和评分被当作三个独立命令。** C5 首跑曾缺推理侧论元输入，LLMERE 的旧生成又缺与训练 target
   成对的终止语义；两者都说明“训练跑完”不是“推理配置正确”。
4. **AI 的权限边界没有显式写成状态机。** 在没有 packet 的情况下，模型自然会把报错理解为“下一步可以修”，
   而不是先判断该修复是否会改变方法、数据语义或论文口径。

这不是把所有调试都归为过失。G-19 的三类运行时条件有些只能在真实依赖栈中暴露，且每次修复均有隔离范围与
不可覆盖产物，最终没有污染结论。问题是这些必要的排障没有预先被**界定为有限的工程阶段**，从外部看便像无边界试错。

## 4. 今后固定的 AI 辅助科研状态机

每个外部方法或新机制只按以下顺序移动；后一步不得替前一步补理由。任何阶段的产物都写入计划/结果页或其链接，
不靠聊天记忆。

| 门 | AI 可以做什么 | 必须证明什么 | 通过后才可进入 |
|---|---|---|---|
| R0 研究卡 | 检索一手论文/代码，生成候选清单 | 科研价值、主表/门、P/V/U 身份；数据/协议/代码/算力/授权可行性 | R1 |
| R1 来源与静态契约 | 逐文件追踪 import、配置、数据 loader、训练/推理/评分调用 | 上游 revision、模型/数据/候选/评分器身份；输入形状/全局状态/相对路径/网络/磁盘副作用；训练—推理成对配置 | R2 |
| R2 真实数据 CPU 预检 | 在不读禁止 gold、不产生分数下跑 loader、converter、schema 检查 | 全量或经证明的最小前缀满足所有固定维度、ID、覆盖和候选前提 | R3 |
| R3 受限运行 smoke | 只执行冻结的一批真实 train、selection、无标签 predict 生命周期 | 真实 device、读写位置、checkpoint reload、prediction schema、无禁止信息流；不把分数用于选择 | R4 |
| R4 正式执行 | 仅执行 packet 中的命令；不解释和不改配方 | immutable raw output、完整 coverage、运行 manifest | R5 |
| R5 独立评分与声称审计 | 独立从 raw output export/score，检查 P/V/U 与差异 | official scorer、provenance、FR-016、禁止论断；结果高低如实写入 `docs/results/` | 收口 / 作者裁决 |

### 4.1 三类迭代的边界

- **允许的工程排障**：R1–R3 发现一个已证明不改变模型、数据语义、选择规则、候选全集或评分器的接口问题，
  可做一次最小修复，重跑**同一门**，并记录失败与前后 revision。
- **必须停下的不可行性**：无法证明修复不改变上述科学语义，或发现数据、协议、代码、算力、授权任一项不成立；
  必须明确类别、给一手证据并交作者裁决，不能自行“换一个近似实现”。
- **禁止的结果导向迭代**：看到 smoke/正式分数后改 threshold、prompt、backbone、训练量、切分、候选或 evaluator；
  以及只补失败样本、从多次运行中选好看结果。它们不是工程修复，而是污染 baseline/方法结论。

同一种工程类失败不会自动触发无数次修复：修复前先把“哪条契约被破坏、最小修复为何不触及科学语义、重跑哪一门”
写入 packet；无法给出这三项就停下。这用证据限制试错次数，而不武断地规定一个数字上限。

### 4.2 五个角色，五种不能互相替代的产物

| 角色 | 交付物 | 不拥有的权力 |
|---|---|---|
| 一手证据审查 | 论文/官方代码 URL、commit、表号/行号、适用 split 与指标 | 不从摘要或二手数字推出论文结论 |
| 协议红队 | 泄漏、P/V/U、candidate/evaluator、训练—推理信息流清单 | 不改实验假设或放宽 A 类有效性约束 |
| 集成审计 | import 图、输入形状、环境/路径/磁盘副作用、真实数据预检 | 不因运行失败重写外部方法 |
| 执行操作 | 一个冻结命令、immutable output、过程日志 | 不读结果后再选配方或补单条 |
| 独立结果审计 | 从 raw output 复算、覆盖/哈希/声称核验 | 不替执行操作修 bug，也不把诊断当主指标 |

同一个人或 AI 可以顺序扮演这些角色，但不能在同一轮中既根据结果修改配方，又认证修改后的结果。

## 5. G-20 执行就绪包（审计结论：未通过，作者取甲收口）

### 5.1 任务身份与冻结边界

- **目的**：给 Ch4 主表增加 LLMERE-causal 的 U 层透明适配行。它检验的是“在冻结 internal-dev、冻结官方
  evaluator 和项目侧可追溯适配下的 causal P/R/F1”，不是 LLMERE 原论文的 36.04，也不为已失败的 A4 翻案。
- **P/V/U**：P 只作 LLMERE COLING 2025 背景；V 是 FR-016(b)（验证发表数值会读取封存 final-valid，禁止）；
  U 才是本次可评分行，永远标 `single-seed / non-confirmatory`。
- **冻结输入**：P1 trust root `p1-v6-20260904-r15`，protocol SHA-256
  `1e31a9acef39261f776f7ed4069fd73f4531e8d12b55779bfc0fbd74c67f9655`；2,622 train 与 291-document
  `maven_ere_internal-dev`，causal converter 已实测为 48,365 training / 11,149 generation requests。
- **冻结方法身份**：LLMERE upstream `94d4ef2781ec7e071d38ac7fd8632a8fffbda798`，项目曾以 LLaMA-Factory
  + Llama-3-8B LoRA r64、lr `2e-4`、cosine、3 epoch、2048、seed 13 做透明适配。官方仓库无 trainer 或
  inference entry point，故任何项目侧 driver 必须显式披露、不可称官方复现。
- **不变量**：不读 official-valid/final-valid；不重训；不改训练 adapter；不改 upstream converter；不改
  candidate universe、official `evaluate.py` 或 291-document unit；不补跑单条；旧 raw generation 永久保留。

### 5.2 旧运行的已知故障及预注册恢复分支

旧 run 的 11,149 条生成全部存在终止语义缺失：输出中位 1,755 字符，95 条的第一行直接不可解析，另外 11,054 条
仅因污染在换行后才被 converter 忽略。它不是“95 条偶发格式错”。一手核验和既冻结的恢复规则见
`results/PHASE_R1.md` §23。

- C-3 原写法要求阶段 1 对**全部 11,149 条**使用第三个 target 行的结尾作显式 stop；若第一行 0 条不可解析，
  才进入 export/official score。
- 阶段 2：仅当阶段 1 的全量解析计数大于 0 时，使用 candidate-aware constrained decoding 对**全部 11,149 条**
  再生成；第一行须严格满足两个 relation label 各一次、event ID 属本 partition。保存到独立 `predict-r3/`。
- 两阶段都是预先规定的全量统一口径，旧 `predict/generated_predictions.jsonl` 不覆盖、不拼接、不拿来选行。

**C-29.6 的反证（只读 CPU，无模型加载）**：冻结 `test.json` 的每个 target 都有三行，但第三行不是固定文本：
11,149 条中有 **407** 种不同第三行，`Relevant reasoning information: none` 只有 10,743 条，另 406 条含有
instance-specific reasoning。故逐 request 从 `output` 取第三行来构造 stop condition 会读取 gold；固定成
`…none` 又会选择性错误。这个 stop 规则在当前协议下不可执行，具体计数与裁决写入 `results/PHASE_R1.md` §23.1。

### 5.3 就绪检查

| 条目 | 状态 | 审计证据 / 下一步 |
|---|---|---|
| 研究目的、P/V/U、FR-016 与禁止论断 | PASS | `COMPARABILITY_PLAN.md`、`BASELINE_ROSTER.md` §2、本文 §5.1 一致。 |
| 数据、manifest、converter 与官方 scorer身份 | PASS（使用时需重新 hash） | `prepare_llmere_causal_adapter.py` 固定 P1 hash、上游 commit/tree、48,365/11,149 count；converter / scorer 仍须在本次 run manifest 中复核。 |
| 旧结果的根因和全量恢复分支 | PARTIAL | `results/PHASE_R1.md` §23 证明全量/不覆盖边界；C-29.6 证明其中 target-third-line stop 不能合法执行。 |
| **target-third-line stop** | **FAIL【协议】** | 11,149 target 的第三行有 407 种值。逐行 stop 读取 gold；固定 `…none` 漏掉 406 条。这个前置问题未被解决前，不允许实现或运行新 driver。 |
| 历史 generation driver | FAIL-CLOSED | `resume_llmere_causal_prediction.sh` 已只保留为失败输出的可追溯入口，执行会拒绝；它的旧 `max_new_tokens: 512` 无 stop 配置绝不能重跑。 |
| prompt 等价 / 动态候选约束 | NOT STARTED | 只有作者批准 target-independent 新契约后才是正当工程任务；目前不应为一个非法 stop 规则写 driver。 |
| 输出副作用与不可覆盖语义 | PENDING | 新契约若获批准，才为新 namespace、conversion、score、日志和临时目录逐项钉住并测试。 |
| 100 条计时校准、GPU 空闲、磁盘与 remote venv | PENDING【算力/环境】 | 这是 driver 通过后的 R3/R4 项；尚未核卡或发任何 remote GPU 命令。 |

**判定**：G-20 `execution_ready = false`。这里的 FAIL 是具体的协议矛盾，而不是对 LLMERE 的科学否定；
也不能用旧 driver “先试 100 条”来绕过，因为它的已知配置本身不满足冻结恢复规则。作者随后选甲，
故本包永久作为可得性/阻断证据，不再等待新 driver 或 GPU。

## 6. 停止条件与作者裁决（已于 2026-10-02 取甲）

C-29.6 已完成它该做的事：在写任何新 driver 前发现 C-3 stop 规则要求隐藏 gold。按照本项目的可行性纪律，
此处没有自主改成 first-line-only，也没有做“先跑 100 条看看”。裁决时的互斥选项如下：

1. **(甲，建议)**：LLMERE 保留为 FR-016(b) 无可评分行；主表/可得性表说明“官方无 inference，已冻结的
   transparent-adaptation recovery 需要 target-dependent stop，故因协议禁止”。这是最保守且不改口径的收口。
2. **(乙)**：明确授权一个新、target-independent 的 first-line-only constrained decoding 契约。它必须重新写
   科研价值/可行性、信息流、全量 stage 规则、prompt 等价、candidate grammar、输出/评分和 smoke 门；随后才可
   实现并测试项目侧 driver，仍不代表官方复现。

**作者已选 1（甲）。** LLMERE 保留在 Ch4 可得性表，明确写“官方无 inference；已冻结的透明适配恢复需要
target-dependent stop，因协议禁止”，不产生 U 层数值。本项目不会实现或运行 first-line-only driver，也不会
因 4090 空闲恢复 generation。这个停止正是新流程的预期行为：把不合法的推理方案在花 GPU 前暴露出来，
而不是跑出数字后再解释它为什么不可用。其后的任务是 C-30 审计，和
[`AUTONOMOUS_RESEARCH_PROGRAM.md`](AUTONOMOUS_RESEARCH_PROGRAM.md) 中的 C-31 受约束研究回合。
