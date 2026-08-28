# 事件图谱构建硕士论文主线收敛（2026-08-27）

## 决策

**不再重开一个孤立的新任务，也不再寻找覆盖全篇的万能语料。恢复并收敛现有 v5 四章主线。**

独立、对抗性可行性审查给出 **CONDITIONAL**，详见
[`INDEPENDENT_THESIS_FEASIBILITY_REVIEW.md`](INDEPENDENT_THESIS_FEASIBILITY_REVIEW.md)。它确认现有数据、
代码和单卡资源足以支撑“三个方法章 + 一个系统评估章”，同时要求先冻结协议，并把 Ch3 与 Ch4 的
未验证主张前置为闸门。下文已吸收该审查，不把已有结果误写成已达标。

事件图谱构建本来就由多个可独立评测的环节组成。不同环节使用不同公开语料是正常实验设计；论文的
统一性来自同一个 event graph schema、连续的构建流水线和共同研究问题，而不是四章共享一个数据文件。

全篇总问题收敛为：

> **如何从多源文本构建可消费的 occurrence-level 事件图谱，并识别、降低和解释身份、关系与事实性
> 错误对不同下游消费者的影响？**

## 为什么此前越做越窄

探索阶段混淆了三件事：

1. “论文原数字能否直接比较”与“论文方法能否作为本地 baseline”；
2. “数据能否随代码自由再分发”与“研究者能否合法取得并复现实验”；
3. “作者仓库能否零修改运行”与“方法能否根据论文和公开代码忠实复现”。

正确做法是统一重跑，而不是继续淘汰：选定本章 benchmark 后，由我们冻结 split/evaluator，把多个方法
拉到同一主表。原论文使用不同 split 时只把原数字放背景表；本地主表只放统一重跑结果。

## 推荐的唯一四章骨架

| 章 | 构建问题 | 主评测与可选扩展 | 章间交付 |
|---|---|---|---|
| Ch1 方法章 | 事件身份消解：哪些 mentions 属于同一 occurrence | MAVEN-ERE coref；MUC F1 主报，B³/CEAFe/BLANC 全报 | 规范事件节点、cluster confidence、evidence mentions |
| Ch2 方法章 | 事件关系抽取：节点之间是什么关系 | MAVEN-ERE causal/subevent；causal F1 主报，subevent 强制副指标 | 带类型、方向、置信和来源的关系边 |
| Ch3 方法章 | 事件事实性与证据：事件是否真实发生 | MAVEN-FACT；5 类 macro-F1 主报，evidence 指标强制副报 | factuality label、evidence span、节点状态 |
| Ch4 系统评估章 | 构建错误如何影响不同消费者 | 同一 MAVEN valid 710 篇、同一 1,908 个 CGEP queries | 组件误差的边际/交互代价、消费者依赖性的成立边界 |

这四章不是四篇互不相干的小论文：Ch1 产节点，Ch2 产边，Ch3 给节点加事实状态与证据，Ch4 消费
前三章的 gold/predicted/repaired graph 并量化错误代价。MAVEN 家族提供全链路集成桥梁，其他语料只用于
验证某一组件的泛化，不要求强行转换成同一 annotation schema。

## 每章如何满足“超过多个方法”

### Ch1：语境判别的身份消解

- 当前已定位的真实瓶颈不是换大底座，而是同 trigger 字面的不同事件容易过并，同时相似上下文又会欠并。
- 方法应围绕**上下文判别表示 + 校准聚类/阈值**，而不是继续做无证据的 asymmetric loss 扫描。
- 主表在冻结的 MAVEN-ERE valid 上统一重跑：词形/lemma 启发式、RoBERTa pair、官方 single/joint、
  RESIJ-Trigger 和我们的模型。经典与近期方法都可计，重点是同一 scorer 下实际重跑。
- 最小方法增量是给同 trigger、同类型候选加入局部论元与跨句语境表示，再做校准聚类；必须同时降低
  同-trigger 过并，并保持跨句 recall 与 B³/CEAFe/BLANC 不出现噪声外退化。
- ECB+/GVC/FCC 是跨文档泛化扩展，不是 Ch1 成立前必须通过的独立资格门。

### Ch2：关系族均衡的长上下文关系抽取

- 保留 causal/subevent 的 MAVEN-ERE 主线；当前已有官方原版代码在同一 valid 的 31.37 对照，工程链完整。
- 方法空间收敛到共享长窗口表示、causal/subevent 关系族平衡的联合优化，以及类型/方向约束；窗口、
  warmup、epoch 等复现修正不单独算方法贡献。
- 主表统一重跑本地 pair classifier、官方 causal single、official joint、RESIJ-Trigger 和我们的模型。
- MATRES 可作为 temporal 扩展：自行冻结 split 后重跑 Roccabruna/TCT 等方法；论文原 87.6 只作背景，
  不要求复制原 split 才能使用该方法。

### Ch3：证据条件化的事实性检测

- 现有 valid macro-F1 48.23 与论文隐藏 test 的 47.6/47.1/45.4 **不是同协议胜利**，本章当前未过线。
- 最小方法增量是让 evidence localization 与五分类标签相互条件化，而不是两个平行 loss；净化零效应
  保留为 Ch4 的误差传播证据，不复活成方法卖点。
- 主表先在同一 valid 重跑 RoBERTa+CLS、DMBERT/DMRoBERTa 等至少两个强对照和我们的模型。
  FactBank/UW/MEANTIME 仅在同协议主表成立后作为泛化加分项，不用于换榜单救火。

### Ch4：构建质量的系统代价与消费者依赖性

- 已有稳定事实：gold→predicted graph 有明确损失，但修复、净化和选边在微调 SeDGPL 消费者上近零。
- 与 ACL 2025 的 in-context 图消费者显著获益形成直接科学问题：**图质量收益是否依赖消费者使用图的
  方式？**
- Ch4 不提出第四个抽取算法，而是在同一 1,908 个 queries 上做 factorial：identity gold/pred、relation
  gold/pred、factuality gold/pred/masked，并由微调与 frozen 两类消费者读取完全相同的事件文本、候选集
  和 graph serialization。factuality 必须作为节点属性进入，不能只靠删节点替代。
- 主指标为 MRR，辅报 strict MRR/Hit@k、成对 Δ、bootstrap CI 和 consumer×quality 交互。只有同 backbone
  的 frozen-vs-finetuned 控制成立，才可声称“微调导致绕过图”；否则只报告两个系统敏感性不同。
- Ch4 可保留负结果。若 frozen 消费者同样不敏感，就撤回消费者类型解释，保留构建误差的系统评估，
  不更换任务或指标硬凑正结果。

## 修订后的 baseline 与数据规则

### 硬要求

1. 同一章主表中的方法使用同一 test manifest、输入前提和 evaluator。
2. 至少多个代表方法由本项目实际运行；不拿不同 split 的论文原数直接相减。
3. 所有 split、方法修补、命令、checkpoint、随机种子与结果可追溯。
4. 三个方法章中，我们的方法必须在该章公开主指标上超过多个实际重跑 baseline；Ch4 是系统评估章，
   以公认下游指标、多个可信消费者、配对统计和可复现实验设计成立，不伪装成第四个算法贡献。

### 不再作为一票否决

- 四章使用不同语料；
- 论文原 split 与本地统一 split 不同；
- 作者代码需要环境、路径、数据接口或 checkpoint 载入修补；
- 论文只有足够详细的方法描述，需要忠实复现；
- 数据需申请/协议后研究使用、不能随代码再分发；
- baseline 年份较早或作者团队有交集。

这些因素影响证据等级和写作披露，但不自动取消任务或方法资格。

## 严格串行实施顺序

严格串行主顺序：**协议冻结 → Ch2 → Ch3 → Ch1 → Ch4**。

1. **先冻结协议**：固定 train 内 dev、最终 valid、输入前提、evaluator hash、主副指标和结果 schema；
   baseline 先做小样本 smoke，不把环境修补升级成无限期仓库考古。
2. **先完成 Ch2**：工程链最完整、同 valid 官方 baseline 31.37 已重跑，最快检验方法主线能否过线。
3. **前置 Ch3 gate**：训练较轻但当前“已胜出”结论不成立，尽早检验 evidence-conditioned 增量，避免把
   跨 split 数字带到论文后期。
4. **再完成 Ch1**：复用当前错误剖析，围绕同词形事件的上下文判别力设计方法，不再换底座。
5. **最后做 Ch4 集成**：前三章产出稳定后，在同一 1,908 queries 上比较消费者与误差交互。

严格串行仍保留，但串行的是章节实施，不再是一个个语料的 GO/NO-GO 淘汰。

## Done 与止损

- **协议冻结 Done**：manifest、输入层级、evaluator hash、主副指标与结果 schema 固定；候选 baseline
  完成小样本 smoke。某 baseline 两次定向修补仍不闭环，降为背景，不无限修仓库。
- **Ch2 Done**：至少三个代表 baseline 同协议重跑；我们三种子超过至少两个且包含 official single；
  causal 提升且 subevent 不低于历史 24.03。两项机制后 causal 仍低于 31.37 或 subevent 未恢复即止损。
- **Ch3 Done**：至少两个强 baseline 同 valid 重跑；evidence-conditioned 方法三种子超过至少两个，
  且消融证明条件耦合有效。无同 split 领先或增量落入噪声即降为系统组件，不扩外部数据救火。
- **Ch1 Done**：至少三个 baseline 同协议；我们超过至少两个且包含一个强外部实现；同-trigger 过并下降，
  跨句 recall 和其他 coreference 指标无噪声外退化。两轮机制验证仍不过线即止损，不用 ECB+ 换榜单。
- **Ch4 Done**：同一 1,908 queries 的 factorial 完整；两类消费者均有 graph/no-graph、噪声地板、配对 CI。
  两次小样本验证后 frozen consumer 仍不敏感，则撤回消费者类型主张，保留系统评估。

资源预算按独立审查估算为 **95–180 单 GPU 小时**，约 4–8 天连续串行 GPU；4090 为主，5090 仅在
逐次授权后备用。主线不依赖 14B/70B、闭源模型、多智能体或新增人工标注。

## 外部深度研究只做什么

现有 A–H 报告足以决定主线。后续网页版 Deep Research 只接受**窄而直接服务实现**的任务，例如：

- 为 Ch1 列出可在我们冻结协议上忠实重跑的 3–5 个代表方法及关键模块；
- 为 Ch2 核对联合学习/跨句关系抽取的最小可实现 baseline；
- 为 Ch3 整理 FactBank/UW/MEANTIME label mapping 与公开 loader；
- 为 Ch4 核对消费者敏感性实验和公开叙事完形数据。

不再让深度研究模型决定某一语料“够不够资格成为整篇论文”。
