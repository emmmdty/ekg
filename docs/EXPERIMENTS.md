# EKG v6 实验协议

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
- mandatory guardrail：subevent P/R/F1；
- diagnostics：同句/跨句分层、方向/类型违反；
- temporal：TIMEX 输入闭环前只作诊断，不进入贡献主表。

### 3.2 Baseline 矩阵

| 方法 | 角色 | 输入要求 | v6 状态 |
|---|---|---|---|
| 本地 sentence/pair classifier | 经典可执行底座 | gold mentions、触发词/句子 | 已有代码；P1 重跑 |
| MAVEN-ERE official single | 原文强锚 | gold mentions、官方 pair/scorer | checkout/patch/schema smoke 已闭合；A3 GPU 待跑 |
| official joint | 联合学习必含对照 | 同四任务输入 | checkout/路径适配/schema smoke 已闭合；A3 GPU 待跑 |
| RESIJ | 结构/图传播可选对照 | 仅在公开实现或忠实复现闭环时纳入 | 论文存在；公开代码 UNVERIFIED |

P1 必须闭合本地 pair、official single、official joint；主表至少三个代表方法。A3 的 primary-eligible 强
roster 是 official single/joint，本地 pair 只作代表底座。RESIJ 是可选多样性对照，不阻塞 A3。
official joint 已使用手调固定任务 loss factors，因此 fixed-weight/grid search 不能作为 family balance 创新。
本地 pair 的 v6 确认性 loss 与 checkpoint selection 只覆盖 causal/subevent；generic extractor 必须读取
checkpoint `run_metadata.json` 的 active families，禁止未训练 temporal head 产生预测。三个 baseline 都须经
完整推理→official schema 归一化→固定 evaluator；只有 checkpoint 或 upstream raw output 不算闭环。

### 3.3 我们的方法与消融

| 变体 | 目的 | 单变量要求 |
|---|---|---|
| reproduction base | 共享长窗口 + 正确训练协议 | 不算创新 |
| `+ adaptive family balance` | 归一化族风险、自适应梯度或等价非固定机制 | 核心；其余配置冻结 |
| `+ type representation` | 使用事件类型信息 | 二级；类型词表随 checkpoint |
| `+ direction constraint` | 抑制不合法方向 | 二级；candidate population 不变 |
| 句级替代窗口 | 证明长上下文必要性 | 同训练预算 |

两个有效核心设计周期只计已经过实现/测试/协议 smoke 的 family-balance 设计。type/direction 失败时删除
对应 claim，不阻断核心 promotion。promotion 同时看 causal 与 subevent 的预注册非劣界；只提升 causal、
持续牺牲 subevent 不算通过。

## 4. Ch3：事实性与证据

### 4.1 主指标

- headline：五类 macro-F1；
- mandatory：每类 P/R/F1，尤其 PS-/Uu；
- evidence：CT-/PS+/PS- 三类宏平均 + pooled span P/R/F1；
- accuracy 只作诊断，不能作为主指标。

### 4.2 Baseline 矩阵

| 方法 | 角色 | v6 状态 |
|---|---|---|
| majority / lexicon | 下界 | 已有代码/结果；不计强对手 |
| RoBERTa+CLS | 必选同底座强 baseline | 待 internal-dev 闭合；sealed final 后跑 |
| DMRoBERTa | 动态多池化必含强 baseline | 待忠实复现并先闭合 internal-dev |
| DMBERT | 预登记替代 | 仅在 DMRoBERTa 两轮工程修复失败时启用 |
| GenEFD | 生成式架构可选对照 | 非主表闭合前置 |

主表必含 RoBERTa+CLS 与 DMRoBERTa 两个强机制对照；DMRoBERTa 不能闭环时才按预登记规则替换为
DMBERT。最终须按主锚规则胜出；majority/lexicon 不计强对手，隐藏-test 论文数字不参与胜负判断。

### 4.3 我们的方法与消融

| 变体 | 条件路径 | 用途 |
|---|---|---|
| parallel heads | 无相互条件 | reproduction/消融 base |
| evidence → label | evidence 条件化五类预测 | Mechanism 1 |
| label → evidence | label posterior 条件化 span | 公开 pipeline reproduction/二级机制 |
| bidirectional | 双向条件耦合 | 可选扩展，不是章节成立前提 |
| no structure | 去关系/论元输入 | 结构副消融 |

核心 full method 是 evidence→label 或联合软耦合；label→evidence/bidirectional 失败时删除对应 claim，
不得否定已过线的核心。跨数据集与事实性净化均不在主表关键路径。PS-/Uu 支持数必须随 manifest 报告；
稀有类护栏采用“anchor 非零时不得崩为零”与合并稀有类的 document-cluster 非劣 CI，不按单点 F1 阻断。

## 5. Ch1：事件身份消解

### 5.1 主指标

- headline：MUC P/R/F1；
- mandatory：B³、CEAFe、BLANC P/R/F1；
- diagnostics：same-trigger 过并/欠并、cross-sentence recall、cluster-size 分层；
- 难例误合并率不能替代公开 coreference 指标。

### 5.2 Baseline 矩阵

| 方法 | 角色 | v6 状态 |
|---|---|---|
| lexical/lemma | 可解释下界 | 已有代码/结果 |
| 本地 RoBERTa pair | 同底座底座 | 已有 checkpoint；需修 dev 选模重跑 |
| MAVEN-ERE official single | 必含原文单任务锚 | 共享 checkout/patch 已由 P1 固定；C4 全协议重跑待执行 |
| MAVEN-ERE official joint | 必含原文联合锚 | 共享 checkout/patch 已由 P1 固定；C4 全协议重跑待执行 |
| RESIJ | 结构可选对照 | 仅在公开实现或忠实复现闭环时纳入；代码 UNVERIFIED |

最终主表纳入 lexical/lemma、local pair、official single、official joint 四个必含 baseline；其中
primary-eligible 强 roster 是 official single/joint，简单 lexical 与 local pair 不因可执行而自动算强锚。
RESIJ 不阻塞 C4。主锚在同 split baseline 完成后、方法结果产生前冻结。

### 5.3 我们的方法与消融

| 变体 | 目的 | 通过护栏 |
|---|---|---|
| pair base | trigger/type/pair 表示 | reproduction |
| `+ local arguments` | 区分同 trigger occurrence | same-trigger 过并方向只作 claim 诊断 |
| `+ cross-sentence context` | 增强跨句判别 | cross-sentence recall 不退 |
| `+ calibrated clustering` | 把 pair 分数转稳定簇 | 二级；多指标不作阈值交换 |

核心是 local arguments + cross-sentence context 的上下文判别表示。校准失败时保留预注册全局阈值并删除
校准 claim，不阻断核心 promotion。非对称 loss/阈值只可作为历史诊断，不再是 full method。

## 6. Ch4：同实例系统评估

### 6.1 主指标与评价单元

- E3 冻结完整 queries、candidate IDs、labels、事件文本、生成器/seed/source hashes 与 canonical graph
  serialization；当前 1,908 是本地重建规模，若重建校验改变数量须在看 consumer 结果前冻结并披露；
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

- 严格串行 P1→A3→D3→C4→E3；
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
