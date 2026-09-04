# EKG v6 实验协议

> 本文是可修订的实验设计层，不是稳定 SPEC，也不是结果单一事实源。表中的候选方法与 baseline roster
> 必须经 R1 文献/代码/协议审查后才能冻结；历史分数与 PASS/FAIL 只认 [`results/`](results/README.md)。

> 本文件只定义 baseline、消融、统计和结果 schema。研究约束以 [`SPEC.md`](SPEC.md) 为准，活动顺序以
> [`phases/`](phases/README.md) 为准，实验数字只写入 [`results/`](results/README.md)。

## 1. 全局协议

### 1.1 数据与 split

- Ch1/Ch2 使用 P1 冻结的 MAVEN-ERE train/internal-dev/final-valid manifests；
- Ch3 使用相同 doc-ID 划分的 MAVEN-FACT manifests；
- P1 只冻结 Ch4 的 ID namespace、query 生成器版本/来源 hash 与 schema；E3 开始前冻结完整的本地重建
  CGEP-MAVEN query/candidate manifest；
- internal dev 只负责结构、epoch、阈值和 promotion；final valid 在 config/code/checkpoint/threshold hashes
  与访问账本冻结后单次解封，解封后重调的运行一律标 `exploratory`；
- baseline 与方法的 final-valid 结果在同一个 sealed evaluation batch 中解封；不得先看 baseline final-valid
  再设计方法。只有未返回任何指标且 hashes 完全一致的基础设施失败可原样重试，且必须记入访问账本；
- test 标签隐藏且提交通道不可用，不进入本地主表；论文必须披露 valid-as-final 与历史探索使用边界；
- 所有方法使用同一 candidate population、gold/predicted input setting 和 evaluator。

### 1.2 两层表

| 表 | 上游输入 | 回答的问题 | 是否决定方法章成立 |
|---|---|---|---|
| 组件主表 | gold upstream | 本章方法是否优于 baseline | 是 |
| 端到端副表 | frozen predicted upstream | 误差如何传播 | 否；进入 Ch4 |

不得用端到端容错掩盖组件方法失败，也不得用 gold proxy 冒充 predicted 闭环。

### 1.3 报数规范

- Pilot：seed 13，internal dev，仅作 promotion 决策；
- Final：seeds 13/17/42，报告每种子、mean、sample std；
- 确认性 paired bootstrap 以 document 为 cluster 重采样，保留文档内全部实例；相对主锚至少 10,000
  次，95% CI 下界大于 0 才计胜出；
- 随机主锚与完整方法用 matched seeds 13/17/42；Ch4 的预注册确认性 contrasts 使用 Holm 校正；
- 多关系/多类别全报 per-family/per-class P/R/F1；
- 所有逐实例 predictions/ranks 随 metrics 保存，不能只留汇总；
- 论文原分数若 split/输入/scorer 不同，只进背景表，标明不可直接比较。

## 2. Baseline 准入规则

一个 baseline 进入主表前必须有：

1. 论文/官方说明与 source commit；
2. 数据、输入字段、candidate population 与 label universe；
3. evaluator 与输出转换；
4. 透明 patch 及其不改变科研语义的说明；
5. 10-doc 或等价小样本 smoke；
6. stage bundle、candidate-ID digest/population counts 和可回放命令。

一轮工程修复是一次有界诊断、补丁和同协议 smoke。环境、路径、checkpoint 载入最多两轮；改变
candidate/evaluator/label 才能运行的方法不属于同协议。第三轮不再修，该候选降为背景并只可换预列候选；
候选失败不等于任务失败。不能等看到主方法结果后再替换成更弱 baseline。

每章在 baseline 运行前冻结强 roster 与选择规则：默认取合格强 baseline 中 internal-dev 主指标 mean
最高者，平分按预登记 roster 顺序；在看到方法结果前冻结同 split `primary anchor` 身份。最终方法主指标
均值须高于主锚和另一不同方法族的强 baseline，至少 2/3 matched seeds 的差值为正，且相对主锚的
document-cluster paired-bootstrap 95% CI 下界大于 0。每次 bootstrap 对三个 seed 分别重算指标，再对
seed-level delta 取均值。主表
baseline 纳入数量与必须胜过数量分别报告。

## 3. Ch2：关系抽取

### 3.1 主指标

- headline：causal positive-class micro P/R/F1；
- mandatory guardrail：subevent 与 temporal P/R/F1；
- diagnostics：同句/跨句分层、方向/类型违反；
- candidate universe：三族输入口径和 TIMEX 开关成对冻结，任何方法不得在评测时裁掉候选。

### 3.2 Baseline 矩阵

| 候选方法族 | 角色 | R1 必核条件 |
|---|---|---|---|
| 本地 sentence/pair classifier | 经典可执行底座 | gold mentions、全候选、三族训练/推理开关一致 |
| MAVEN-ERE official single | 原文单任务复现 | 官方输入、checkpoint、pair 与 scorer 忠实度 |
| MAVEN-ERE official joint | 联合结构强锚候选 | 四任务输入、官方配方和 scorer 忠实度 |
| 2025 two-stage document ERE | 近期 evidence/retrieval 强方法族 | 采样子集与本项目完整候选协议的差异；需统一重跑 |
| RESIJ | rich structure / graph propagation | 官方实现可得性；无法忠实复现时不可伪装成已运行对照 |
| TacoERE / KnowQA | compression / structure QA 对照候选 | 输入前提、关系覆盖和 scorer 可比性 |

R1 冻结至少多个可运行、机制不同的强方法族以及 primary-anchor selection rule。论文不同 split 分数只进
背景表；所有主表方法必须完成推理→official schema→固定 evaluator。official recipe 修正、fixed family
weights 或 checkpoint 选族只算 reproduction，不算本项目方法贡献。

### 3.3 我们的方法与消融

| 候选变体 | 目的 | 单变量要求 |
|---|---|---|
| protocol-aligned base | 全候选、正确 official recipe | reproduction，不算创新 |
| `+ pair evidence` | 为每个 pair 选择可核证 evidence | 不能移除评测候选 |
| `+ sufficiency/abstention risk` | 对证据不足和跨句误报显式建模 | 核心候选；evidence 表示冻结 |
| random/window evidence | 检验是否只是增加 token/窗口 | mediator negative control |
| `- relation-aware constraint` | 检验结构约束的独立作用 | 二级单变量消融 |
| backbone/context transfer | 检验机制迁移性 | base/proposed 对称；不计核心创新 |

该矩阵只是 R1 的起点。A3 已失败的 family workpoint、近似 retriever、prototype 与 ATLoss 不得换名复活；
检索/hard negatives 可作为训练或 evidence 实现，但单独不构成新方法。R1 必须证明新 treatment 能改变
预注册的跨句 causal FP/sufficiency 中介，同时保持 recall、subevent 与 temporal 护栏。

## 4. Ch3：事实性与证据

### 4.1 主指标

- headline：五类 macro-F1；
- mandatory：每类 P/R/F1，尤其 PS-/Uu；
- evidence：CT-/PS+/PS- 三类宏平均 + pooled span P/R/F1；
- accuracy 只作诊断，不能作为主指标。

### 4.2 Baseline 矩阵

| 候选方法族 | 角色 | R1 必核条件 |
|---|---|---|
| majority / lexicon | 解释性下界 | 不计强对手 |
| RoBERTa+CLS | 同底座强 baseline | 五类同 split 主指标和选模忠实度 |
| DMRoBERTa / 合法预登记替代 | 表示学习强方法族 | 官方实现、输入与 scorer 忠实度 |
| MAVEN-FACT official pipeline | label→evidence 公开对照 | 五类与 evidence 两轴完整复现 |
| ModaFact / 结构化模态方法 | modality/factuality 结构对照候选 | 数据标签映射、代码和同协议可运行性 |

最终 roster 由 R1 依据公开实现和协议忠实度冻结。majority/lexicon 不计强对手，隐藏-test 论文数字不参与
胜负判断；无法运行的方法必须注明 fidelity 边界并由另一强方法替代，不能降为只胜简单下界。

### 4.3 我们的方法与消融

| 候选变体 | 条件路径 | 用途 |
|---|---|---|
| flat five-class head | pooled 表示直接分类 | 同底座 base |
| `+ typed cue spans` | 显式否定、模态、条件、来源与作用域 | 证据表示候选 |
| `+ known/unknown sufficiency` | 先判断是否有足够证据 | Uu/证据中介候选 |
| modality→polarity factorization | 分解结构化标签决策 | 核心候选；输出仍映射公共五类 |
| no/random cues | 移除语义或保持 token 数 | mediator negative control |
| parallel evidence/label heads | 无结构耦合 | strongest local alternative |

gold-evidence oracle 已表明单纯换 evidence locator 不是充分解释，旧 pooled evidence 双头仅保留为对照。
R1 可替换上述候选，但必须保留五类 macro-F1 主门、完整 evidence 轴、稀有类支持数与前瞻性功效设计；
任何中介指标都不能替代主结果。

## 5. Ch1：事件身份消解

### 5.1 主指标

- headline：MUC P/R/F1；
- mandatory：B³、CEAFe、BLANC P/R/F1；
- diagnostics：same-trigger 过并/欠并、cross-sentence recall、cluster-size 分层；
- 难例误合并率不能替代公开 coreference 指标。

### 5.2 Baseline 矩阵

| 候选方法族 | 角色 | R1 必核条件 |
|---|---|---|
| lexical/lemma | 可解释下界 | 不计强对手 |
| 本地 pair classifier | 同底座复现 | gold mentions、同 split/scorer、选模规则 |
| MAVEN-ERE official single/joint | 原文强锚候选 | 官方输入、coreference scorer 与 checkpoint 忠实度 |
| CorefPrompt | argument/type-aware 强方法族 | 数据/输入映射、官方代码和同协议可运行性 |
| RESIJ | rich event structure 对照候选 | 公开实现可得性和同协议 fidelity |

R1 冻结多个机制不同且可运行的强方法族与主锚；简单 lexical 不因可执行而计作强对手。论文数字只作
背景，所有胜负来自统一重跑。

### 5.3 我们的方法与消融

| 候选变体 | 目的 | 单变量要求 |
|---|---|---|
| pair base | trigger/type/pair 表示 | reproduction |
| `+ mention-local predicted arguments` | 提供不泄漏 occurrence 的局部语义 | gold event-level arguments 仅 oracle |
| `+ role-aligned posteriors` | 比较 pair/cluster 的论元角色兼容性 | 相对 hard labels 单变量 |
| `+ uncertainty-gated clustering` | 阻止低可信局部预测污染整簇 | 核心候选；阈值/聚类规则冻结 |
| shuffled/posterior-confidence control | 检验是否只是额外特征或置信度 | mediator negative control |

旧 context pooling/confusability 结果保留为失败证据，不作为当前 full method。R1 必须先证明 MAVEN-ARG
与 ERE mention IDs/offsets 可无歧义对齐；否则停止这条输入线并重做候选设计。主门仍是 MUC，B³、CEAFe、
BLANC 与跨句行为只作 mandatory guardrail/机制诊断。

## 6. Ch4：同实例系统评估

### 6.1 主指标与评价单元

- E3 在看 consumer 结果前冻结完整 queries、candidate IDs、labels、事件文本、生成器/seed/source hashes
  与 canonical graph serialization；实际 population count 只在结果与 manifest 中记录；
- 公开 headline：MRR、Hit@1/3/10/20/50；strict MRR、strict correctness、unscorable 与 factorial effect/CI
  是本项目副指标/诊断，不冒充 CGEP 官方 headline；
- 每个 condition 保存同 query ranks，严禁按 arm 丢题。

### 6.2 消费者与可信度对照

| 消费者/下界 | 作用 | 必须检查 |
|---|---|---|
| random | 排名地板 | candidate manifest 一致 |
| frequency | 非图强下界 | train-only 统计 |
| BART/text-only | 必含非图公开锚 | 与 graph consumer 同候选/文本 |
| SeDGPL/fine-tuned graph | 必含强 graph 锚 | 预测有效性、graph 正控、重训噪声 |
| same-backbone frozen variant | 实验消费者因子 | 同 serialization/architecture；不要求胜过全部公开方法 |

预测有效性与图敏感性分开：fine-tuned graph anchor 在 MRR 上相对 BART/text-only 与 frequency 的
document-cluster paired 95% CI 下界必须均大于 0；至少一个 consumer 必须通过预注册的 gold/permuted 或
graph/no-graph 正控，其预注册方向的 document-cluster paired 95% CI 不跨 0。frozen arm 可以不敏感，这
本身是允许的 consumer×quality 结果；两者都不敏感则 Ch4 收缩为错误传播副章。CSProm-KG、SimKG、
MCPredictor 可选。

随机消费者使用 matched seeds 13/17/42。每个 consumer/seed 只训练一次，并在全部 12 个 quality arms
复用完全相同的 checkpoint；quality 只改变 final-valid 的输入图，不得逐 arm 重训。frozen-vs-fine-tuned
共享初始化、训练数据/训练图、scoring architecture 与预算，只改变 encoder 是否更新。

### 6.3 Factorial

| 因子 | 水平 |
|---|---|
| identity | gold / predicted |
| relation | gold / predicted |
| factuality | gold / predicted / masked |
| consumer | frozen / fine-tuned |

基础设计 24 条件。identity 只改变 graph grouping，不改变 mention-level query/candidates；factuality 必须作为
节点属性输入，删节点只保留为历史 perturbation 副表。

确认性统计以 document 为 cluster 做至少 10,000 次 paired bootstrap；随机消费者在每次抽样中分别重算
三个 matched-seed effect 再取均值。在看到结果前预注册有限主 contrasts，同一确认性家族作 Holm 校正，
其余标 exploratory。报告三个主效应、预注册交互、consumer×quality 与每消费者噪声地板。不同
backbone 只能支持描述性差异；同 backbone 才可讨论微调相关机制。

## 7. Stage bundle 与结果 schema

### `protocol.json`

必填：phase/bundle/status schema 版本、source/manifests/candidate-ID/evaluator/config/code/checkpoint hashes、
population counts、seed、输入设置、upstream bundle IDs、final-valid 访问记录、是否 exploratory。

### `predictions.jsonl`

必填：稳定 doc/instance/mention IDs、gold/pred label、原始 probabilities/scores、无法评分原因。禁止静默丢弃。

### `metrics.json`

必填：scorer 原始字段、样本数、主副指标、per-class/family、seed。不得从 Markdown 反向生成。

### `status.json`

必填：`pass|conditional|failed|blocked`、`global_protocol_status`、阶段与下一阶段入口状态、primary-anchor
selection rule、已解析时的 primary anchor、historical-final-access disclosure、带 purpose 的 final-valid
access ledger、v6 confirmatory eval count、promotion 条件逐项、stop 是否触发、是否 exploratory、允许
下游如何引用。

任何 hash/ID/schema 不一致都在读取时 fail-fast。reader 必须接收 bundle 外提供的可信 `protocol.json`
SHA-256，并重新散列其声明的外部证据；不能用 bundle 自报 hash 自证。修复后新建 bundle ID，不覆盖旧结果。

## 8. 资源与停止规则

- 当前证据依赖为 P1→A3→R1→{C5,A4,D4}→E3；花括号内无真实依赖时可重排或并行，操作顺序不属于 SPEC；
- baseline 两个“诊断→补丁→同协议 smoke”工程轮失败即换预列候选；候选失败不等于任务失败；
- 核心方法最多两个完成实现/测试/协议检查的设计周期；二级机制失败不重置或消耗核心预算；
- 每个二级机制另限一次实现 + 一次定向修订；失败即删对应 claim，不继续扩展；
- 先 internal dev pilot，过 promotion 才跑三种子/final valid；
- 4090 为主，5090 每次授权；本地禁止 GPU；
- 失败后不换数据、final split、主指标、底座规模或删除难例；
- 负结果与 stop 状态是正式交付，不是待隐藏 bug。

## 9. 一手证据与未核边界

- **VERIFIED**：MAVEN-ERE 论文与官方 evaluator 定义关系 micro-F1、MUC/B³/CEAFe/BLANC；official joint
  使用固定任务 loss factors，因此固定权重不是本章新机制：
  [论文](https://aclanthology.org/2022.emnlp-main.60/)｜
  [官方 evaluator](https://github.com/THU-KEG/MAVEN-ERE/blob/main/evaluate.py)。
- **VERIFIED**：MAVEN-FACT 定义五类 factuality 与 supporting evidence，并包含 label→evidence pipeline：
  [论文](https://aclanthology.org/2024.findings-emnlp.651/)｜
  [官方仓库](https://github.com/THU-KEG/MAVEN-FACT)。
- **VERIFIED**：CGEP 公开指标为 MRR 与 Hit@1/3/10/20/50；公开论文使用 original valid 作 test、train 的
  20% 作 dev。**VERIFIED/UNRELEASED BOUNDARY**：SeDGPL 仓库存在，但当前未核到可逐项恢复 MAVEN
  派生 candidates 的完整 builder/data，因此本项目只声称“本地重建协议”：
  [论文](https://aclanthology.org/2024.findings-emnlp.45/)｜
  [官方仓库](https://github.com/zhanchuanhong/SeDGPL)。
- **VERIFIED/UNVERIFIED CODE**：RESIJ 论文存在并在 MAVEN-ERE 研究 joint ERE；公开可执行代码仍未核实，
  因而始终是可选 baseline：[DOI](https://doi.org/10.1016/j.ipm.2024.103811)。
