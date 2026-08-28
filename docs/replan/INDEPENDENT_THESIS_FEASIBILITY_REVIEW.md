# 组件化事件图谱硕士论文：独立可行性审查

> **状态说明（2026-08-27 审查整改后）：** 本文是修订前的独立证据快照，不是当前执行契约。其
> `RESIJ-Trigger` 命名、query-level bootstrap、二级机制合取、P1 远期前置和“两个方法章失败后仍可收缩
> 为两方法章”的旧表述，已由 [`../SPEC.md`](../SPEC.md) 与 active phase 修正；执行时以二者为准。

## Verdict：CONDITIONAL（有条件可行）

**一句话理由：现有数据、代码和单卡算力足以完成“3 个方法章 + 1 个系统评估章”，但目前没有一章已经同时满足“同协议重跑多个 baseline、我们稳定超过其中多个、跨章产物被下游真实消费”。**

本报告由独立、对抗性审查角色完成，不继承主方案结论，也不因已有投入降低标准。证据以 [`../results/`](../results/) 的实验档案、实际代码和产物为准，高于 `SPEC/TODO/phase` 的计划表述。本次未运行 GPU、未训练、未 SSH，也未核验审查日实时卡占用。

## 逐章可行性

| 章 | 建议冻结的数据 | 主指标与 evaluator | baseline 成熟度 | 资源与主要风险 | 判定 |
|---|---|---|---|---|---|
| Ch1 身份消解 | MAVEN-ERE train 内划 dev；original valid 710 篇只作最终 test；gold mentions | **MUC F1 主指标**；B³/CEAFe/BLANC 全报；官方 `evaluate.py` | lexical、本地 RoBERTa 已跑；official single/joint、RESIJ-Trigger 需适配 | 20–40 单卡 GPU 小时；现档在 5090 跑过，24GB 峰值未记录 | **CONDITIONAL**：任务成立，方法未超过强同协议基线 |
| Ch2 关系抽取 | 同一 MAVEN-ERE manifest；组件表使用 gold mentions；只做 causal/subevent | **causal 正类 micro-F1 主指标**；subevent P/R/F1 强制副指标；官方 scorer | 本地 pair 与 official causal 已跑；official joint、RESIJ-Trigger 需适配 | 40–60 GPU 小时；subevent 持续退化是主要风险 | **CONDITIONAL，最接近完成** |
| Ch3 事实性与证据 | MAVEN-FACT train 内划 dev；public valid 710 篇只作最终 test | **5 类 macro-F1 主指标**；evidence 三类宏平均与 pooled span F1 | majority/lexicon、本地模型已跑；RoBERTa+CLS、DMRoBERTa/DMBERT 尚未同 split 重跑 | 15–30 GPU 小时；极少数类方差大 | **CONDITIONAL，方法论最弱** |
| Ch4 系统评估 | 同一 MAVEN valid 710 篇、同一 1,908 个 CGEP queries | **MRR 主指标**；strict MRR、Hit@k、成对 Δ、bootstrap CI、consumer×quality 交互 | SeDGPL/扰动已跑；random/frequency 有代码；BART/frozen consumer 未闭环 | 20–50 GPU 小时；frozen consumer 成本与显存未实测 | **CONDITIONAL，高风险** |

## 当前必须正视的结果

- **Ch1**：权威结果为 MUC **77.47**（P 72.98 / R 82.56），不是内部口径 79.6。过并 1,391 对（63.5%）高于欠并 801 对（36.5%），旧“缺口全在 recall”前提已被推翻。[`../results/PHASE_C.md`](../results/PHASE_C.md)
- **Ch2**：同 valid、同官方 evaluator，官方原版 causal **31.37**；本项目最好 causal **28.50**、subevent **21.05**，后者低于早期 24.03。[`../results/PHASE_A.md`](../results/PHASE_A.md)
- **Ch3**：valid macro-F1 **0.4823**；公开 47.6/47.1/45.4 来自隐藏 test，不能直接相减。gold→predicted graph 仅改变 17,780 mentions 中 8 个标签，结构增量很弱。[`../results/PHASE_D.md`](../results/PHASE_D.md)
- **Ch4**：gold→predicted 的 **−0.0218 MRR** 是确凿效应；repaired、purified、factuality oracle 多在约 ±0.003–0.004 噪声地板内。消费者依赖性仍是假设。[`../results/PHASE_E.md`](../results/PHASE_E.md)

所以，Ch3 不能写成“已经超过四个同协议方法”，Ch4 也不能写成“消费者依赖性已验证”。

## baseline 成熟度与冻结方式

状态含义：**已跑**＝项目内已有同协议结果；**代码存在需修**＝入口/数据接口需透明修补；**需忠实复现**＝按论文和公开材料实现；**仅论文数字**＝只能进背景表。

| 章 | 2–4 个候选 baseline | 当前状态 | 主表使用条件 |
|---|---|---|---|
| Ch1 | lexical/lemma；本地 RoBERTa pair；MAVEN-ERE official single/joint；RESIJ-Trigger | 前两者**已跑**；后两者**代码存在需修** | 全部改用同一 train/dev/valid、gold mentions 和官方 scorer |
| Ch2 | 本地 sentence-pair；official causal single；official joint；RESIJ-Trigger | 前两者**已跑**；后两者**代码存在需修** | causal/subevent 的 pair universe、输入信息与 evaluator 完全一致 |
| Ch3 | majority/lexicon；RoBERTa+CLS；DMRoBERTa；DMBERT | 下界**已跑**；其余**需忠实复现/仅论文数字** | 必须在 public valid 同协议重跑，隐藏-test 数只作背景 |
| Ch4 | random/frequency；SeDGPL；BART text/graph；frozen prompt consumer | SeDGPL**已跑**；下界有代码；后两项待复现/实现 | 同一 1,908 queries、候选集、图序列化和 scorer |

指标均为学界常用且可确定冻结：coreference 的 MUC/B³/CEAFe/BLANC，关系正类 micro P/R/F1，事实性 5 类 macro-F1 与 evidence span F1，CGEP 的 MRR/Hit@k。无需另造“难例率”“图一致性”等主指标；这些只能作诊断或机制证据。

## 无人工数据标注审计

**成立。主训练、选模和主指标不需要新增人工标注。**

1. Ch1–Ch3 使用已有 gold；Ch4 queries、候选、图版本和扰动由脚本自动构造。
2. train 内 dev、pair 枚举、label mapping、manifest 和图重建必须确定性生成。
3. hard-case、跨句、少数类和 evidence 分层均可由 gold/预测自动统计。
4. 人工阅读少量错误例子只能作可选定性分析，不参与训练、阈值选择或主指标。
5. 不新建人工 test、不人工判断“图更好”、不人工筛选有利案例，也不依赖付费 GPT-4 生成核心训练标注。

## 最小可成立的方法贡献

### Ch1：语境判别的 occurrence identity

只扫 hard-negative 比例、非对称 loss 或聚类阈值属于调参。最小方法应显式编码同词形/同类型事件的局部论元与跨句语境差异，再做校准聚类；必须同时降低同-trigger 过并、保住跨句 recall，并提升 MUC，且 B³/CEAFe/BLANC 不显著回退。

### Ch2：关系族平衡的长上下文建模

文档窗口、补 warmup/decay 和更多 epoch首先是复现纠偏。最小方法应在共享窗口表示上，对 causal/subevent 做关系族平衡联合优化并加入类型/方向约束；贡献由两族 P/R/F1、跨句分层和逐项消融证明。若只是固定权重或各挑最佳 checkpoint，仍是工程调参。

### Ch3：证据条件化的事实性判别

结构度数特征增量弱，净化又被 oracle 否定。最小方法应让 evidence 定位与 5 类标签互相条件化，而非两个并列 head；需通过无 evidence、仅文本、仅结构消融证明至少一个标准主指标稳定改善。否则 Ch3 应降为系统组件，不硬写方法章。

### Ch4：系统评估，不造第四个算法

其贡献应是 identity/relation/factuality 错误的边际代价、交互和消费者敏感性，以及严格的配对 CI 与零结果边界。若论文仍要求“每章必须超过多个方法”，应明确修订为“每个方法章”；否则系统评估章与该规则逻辑冲突。

## 跨章闭环：概念成立，当前未完全接通

应同时保留两层实验：

1. **组件隔离层**：每章使用 gold upstream，验证组件方法本身。
2. **端到端层**：同一 MAVEN valid 710 篇依次替换 Ch1 节点、Ch2 边、Ch3 状态，测真实传播。

当前有两个断点：Ch2 主评测仍主要基于 gold mentions；Ch3 目前只通过“删节点净化”进入 CGEP，而 factuality oracle 已证近零。外部叙事完形/CRAB 与本地 CGEP 的绝对分数也不能直接证明 consumer dependence。

Ch4 必做同实例 factorial bridge：

- identity：gold clusters / Ch1 predicted clusters；
- relations：gold edges / Ch2 predicted edges；
- factuality：gold / Ch3 predicted / masked node attributes；
- consumer：fine-tuned SeDGPL / frozen prompt consumer。

两 consumer 必须读取同一 1,908 queries、事件文本、候选集和 graph serialization。factuality 要作为节点属性进入，而不只靠删节点。不同 backbone 下只能声称“两个系统敏感性不同”；要声称“微调导致绕过图”，还需同 backbone 的 frozen-vs-finetuned 控制。

## 资源与工作量结论

- 实测锚：Ch2 6ep 在 5090 约 33 分钟；官方 50ep 在 4090 的训练+预测约 2 小时；Ch4 SeDGPL 10ep 为 7,912s。
- 规划总量约 **95–180 单卡 GPU 小时**，不含失败复现与环境修复；严格串行约 4–8 天持续 GPU 时间。
- 现有 RoBERTa/SeDGPL 路径已证明单卡可运行；Ch1 的 24GB 峰值和 frozen consumer 尚未实测，必须先做最长样本 smoke。
- 4090 是主资源；5090 仅经逐次授权备用。14B/70B、闭源多 agent 不是硬依赖。

工作量足够：三个方法问题、统一 baseline、三种子、消融和 Ch4 factorial 远大于单纯工程集成。代码复用不是不足；但若 Ch1–Ch3 最终只有换底座/调权重，Ch4 只有汇总结果，即使代码很多也不构成方法论文。

## 风险分级

### 硬阻塞

1. Ch1–Ch3 各自冻结 manifest、输入前提和 evaluator，并实际重跑多个 baseline。
2. 三个方法章各有一个机制性增量，三种子超过至少两个统一重跑 baseline。
3. Ch3 修正跨 split 结论并证明 evidence-conditioned 增量。
4. Ch4 在同一实例上真实消费 Ch1/Ch2/Ch3 产物。
5. 明确 Ch4 是系统评估章；若不允许调整“每章超 baseline”规则，则收缩为三章。

### 可工程解决

- official/joint/RESIJ 的接口与 checkpoint 修补；
- train 内 dev manifest、统一 runner、三种子结果 schema；
- Ch1 语境特征、Ch2 任务平衡、Ch3 evidence conditioning；
- Ch4 frozen consumer、节点属性序列化、factorial runner 与缓存；
- 最长样本显存 smoke 和 checkpoint 位置记录。

### 非必要加分项

ECB+/GVC/FCC、MATRES、FactBank/UW/MEANTIME、CRAB/ForecastQA、14B/70B、GPT-4o、多智能体、新人工标注、工业或专利包装。主章未完成前均不进入关键路径。

## 推荐最终结构与严格串行顺序

推荐结构：

1. **Ch1 方法章**：语境判别的事件身份消解；
2. **Ch2 方法章**：关系族平衡的长文档关系抽取；
3. **Ch3 方法章**：证据条件化的事件事实性；
4. **Ch4 系统评估章**：构建错误、消费者与下游代价。

推荐执行顺序：

> **协议冻结 → Ch2 → Ch3 → Ch1 → Ch4**

对主代理的 **Ch2 → Ch1 → Ch3 → Ch4**：**部分合理，但中间两步应推翻。** Ch2 第一正确，因为已有同-valid 31.37 强锚；Ch4 最后正确，因为依赖前三章。Ch3 不应继续被视为已过线，它的跨 split 和弱方法 claim 风险最大、训练又较轻，应在 Ch1 前尽早做 gate。论文写作顺序仍保持 Ch1→Ch2→Ch3→Ch4，不必与实验顺序相同。

## 各章 Done 与止损

- **协议冻结 Done**：所有 manifest、evaluator hash、主副指标和结果 schema 固定；baseline 完成小样本 smoke。两次定向修补仍不闭环的 baseline 降为背景，不无限修仓库。
- **Ch2 Done**：至少三个代表 baseline 同协议重跑；我们三种子超过至少两个且包含 official single；causal 提升、subevent 不低于 24.03；消融齐全。两项定向机制后 causal 仍低于 31.37 或 subevent 仍未恢复，即止损，不再扫超参。
- **Ch3 Done**：至少两个强 baseline 同 valid 重跑；evidence-conditioned 方法三种子超过至少两个 baseline，并有清晰消融。同 split 不领先或增量落入噪声，即降为组件，停止外部数据扩展。
- **Ch1 Done**：至少三个 baseline 同协议；我们超过至少两个且包含一个强外部实现；同-trigger 过并下降、跨句 recall 与其余指标无噪声外退化。上下文表示和校准聚类两轮后仍不超过 official valid，即止损，不用 ECB+ 换榜单救火。
- **Ch4 Done**：同一 1,908 queries 完成 factorial；两 consumer 各有 graph/no-graph 检查、噪声地板和配对 CI。frozen consumer 两次小样本验证仍不敏感，则撤回“消费者类型导致差异”，保留构建误差系统评估，不换任务硬凑。

## 最终意见

课题不需要继续缩窄语料资格，也不需要推倒重来。只要以 MAVEN 家族保住 710-doc 纵向桥梁、每个方法章只做一个可消融机制、统一重跑 baseline、允许 Ch4 如实报告零结果，方案在现有资源和无新增人工标注条件下可实现，工作量也足以支撑硕士论文。

若 Ch2 与 Ch3 两个前置 gate 均失败，应立即收缩为“两方法章 + 一系统章”的三章版本；不要通过增加语料、模型或限制来延长探索。
