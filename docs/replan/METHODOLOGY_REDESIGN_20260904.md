# EKG v6.1 方法论与学位目标审计

> 日期：2026-09-04。性质：前瞻性研究设计修订，不改写任何已完成实验的协议或 PASS/FAIL。
> 项目实测只引用 [`../results/`](../results/README.md)，不在本文复制数字。

## 1. 裁决

**论文质量目标不降，三方法章 + 一系统评估章保留；旧文档体系与候选方法需要重构。**

旧设计的主要问题不是统计要求过严，而是：

1. 三章分别围绕局部技巧立项，中心科学假设不够强，容易变成三个 benchmark trick 的拼盘；
2. Ch2 把 family loss balance 当核心，但项目实测已经否定其主要变体，且近期工作已把竞争前沿推进到
   rich event structure、pair retrieval/evidence 与 cross-relation reasoning；
3. Ch1 的冻结方案要求 mention-local arguments，实际核心实验却没有实现这一输入；event-level gold
   argument oracle 又泄漏 cluster identity，不能回答可部署方法问题；
4. Ch3 的 evidence 双头把否定、模态、条件、来源与 unknown 压成一个 pooled vector，oracle 结果说明
   单纯换 evidence extractor 不是主要瓶颈；
5. 旧“两周期”被错误解释成“一个章节永久停止”。正确边界应是：停止一个已被证伪的机制家族，重新
   立项必须经过文献、因果链、功效与新颖性审查，不能换名字继续调参；
6. 原计划没有把 statistical power 放在实验设计之前，导致小 internal-dev 上的零结果难以区分“机制
   无效”和“可检测效应过大”。解决方式是先提高研究设计的功效，不是降低显著性标准。

新的统一命题是：

> **Evidence adequacy and uncertainty propagation for occurrence-level event graphs**：显式表示
> mention/pair/node 的局部语义证据、充分性与不确定性，是否能减少三类构建错误，并使风险能够解释
> 同实例下游消费者的性能损失？

这条命题能让三章拥有独立方法贡献，同时由 Ch4 做真正的系统级反证，而不是只靠统一 schema 串联。

## 2. 学位质量标准核对

同济大学 2026 基本要求规定：学术型硕士应具备学术研究能力；学位论文应具有系统性、完整性和学术性，
论点、结论和建议具有一定学术或实践价值；成果应具有学术性和创新性，论文是承载创新成果的主要载体。
学校同时要求各学科按类型制定标准，且适用版本通常取决于入学年份。

- [同济大学学位授予标准基本要求（2026）](https://gs.tongji.edu.cn/info/1063/4179.htm)
- [同济大学博士硕士学位授予标准制定规定（2026）](https://gs.tongji.edu.cn/info/1063/4170.htm)
- [同济大学学位授予工作细则](https://xxgk.tongji.edu.cn/index.php?classid=3112&newsid=12169&t=show)
- [计算机学院硕士论文盲审说明与评价表入口](https://cs.tongji.edu.cn/info/1037/3502.htm)

这些文件没有规定“每个方法章必须 SOTA”或固定方法章数量；但这不构成降低本项目标准的理由。本项目
自定的更高质量目标继续是：三个方法均在统一重跑的公开主指标上超过冻结强基线，并由 matched seeds、
document-cluster paired CI、机制消融和端到端风险传播共同支撑。需要修正的是研究问题和实验方法，
不是把失败章节改名为经验章。

尚缺一项事实：作者的学位类型、入学年份和对应学科版授予标准未在仓库冻结。它只影响行政验收矩阵，
不影响上述更高科研目标；R1 前应把正式文件版本补入 provenance。

## 3. 领域研究如何做，以及对本项目的约束

### 3.1 统一事件关系不是三个独立分类器

[MAVEN-ERE](https://aclanthology.org/2022.emnlp-main.60/) 的建库动机就是 coreference、temporal、causal、
subevent 之间存在交互，原论文以统一数据、联合学习、四组公认 coreference 指标与关系 P/R/F1 评测。
因此本项目只做每族 loss balance 不足以覆盖任务结构；方法必须利用可验证的语义或逻辑交互。

[RESIJ](https://www.sciencedirect.com/science/article/pii/S0306457324001705) 把事件类型、描述文本、跨句论元
与角色组成 rich event structure，再做图传播和三元关系约束。它说明强方法的关键不是多加一个 loss
weight，而是事件表示和关系间约束是否携带了正确结构。

[MAVEN-ARG](https://aclanthology.org/2024.acl-long.224/) 为相同 MAVEN 家族补充文档级 event arguments，
为 mention-local 语义提供了公开监督。使用它必须先做 ID/覆盖率审计；评测时使用预测 arguments，gold
arguments 只做 oracle，才能避免身份泄漏。

### 3.2 长文档关系抽取的近期路线

[Efficient Document-level Event Relation Extraction](https://aclanthology.org/2025.repl4nlp-1.7/) 使用带事件
marker 的 sentence encoding、fine-tuned bi-encoder top-k 和 cross-encoder hard negatives，并同时分析
效率、encoding、k 与 coreference chains。论文在 MAVEN-ERE 上采用了采样子集，因此其论文分数不能与
本项目完整候选协议直接相减；但它必须成为协议对齐的强方法族 baseline。

[TacoERE](https://aclanthology.org/2024.lrec-main.1348/) 走 cluster-aware compression；
[KnowQA](https://aclanthology.org/2024.findings-emnlp.986/) 把 event structure 与 binary QA 结合以处理文档级
因果关系和 hallucination。这些工作共同表明“长上下文”本身不是创新，pair-specific 信息选择、事件结构
和错误拒判才是可以检验的方法变量。

本项目的 Ch2 新方法因此不再是“再做一个 retriever”。它在完整 candidate universe 上保留所有 pair，
学习 pair-specific evidence spans 和 evidence-sufficiency/abstention risk；retrieval/hard negatives 只改变
训练与 evidence 选择，不改变 evaluator 的候选全集。预注册中介是跨句 causal false positives 下降，
同时 causal recall、subevent 与 temporal 不越过非劣界。

### 3.3 身份消解必须区分语义帮助与标签泄漏

[CorefPrompt](https://aclanthology.org/2023.emnlp-main.954/) 明确利用 event type 与 argument compatibility，
并用多组 coreference 指标和消融论证。它支持“论元兼容性重要”，却不能证明把 event-level gold argument
复制到每个 mention 是合法输入。

Ch1 应学习 mention-local argument-role posterior，并让 role alignment 与 predictive uncertainty 共同控制
pair score 和 clustering。关键对照是：无 arguments、hard argument labels、posterior without uncertainty、
full risk-aware method；只有 full 的主指标和聚类风险同时改善，才能把贡献归因于不确定性门控。

### 3.4 事实性应显式表示模态、极性与 unknown

[MAVEN-FACT](https://aclanthology.org/2024.findings-emnlp.651/) 使用五类 macro-F1 和 supporting evidence，
并显示 arguments 与 relations 可以提供信息，但简单组合会因过拟合反而变差。
[ModaFact](https://aclanthology.org/2025.coling-main.425/) 也把 modality 与 factuality 的联合理解作为核心问题。

Ch3 应从平行双头改为 typed cue span 与结构化决策：先判断 evidence 是否充分及 known/unknown，再判断
modality，最后判断 polarity。五类 macro-F1 仍是不可替代的主门；evidence F1、Brier/ECE、逻辑违反率和
Uu recall 只用于证明机制为何有效，不能拿来替换主指标。

### 3.5 统计显著不等于研究设计充分

[With Little Power Comes Great Responsibility](https://aclanthology.org/2020.emnlp-main.745/) 指出 NLP 中
小测试集的低功效会同时增加漏检与夸大效应风险；
[NLPStatTest](https://aclanthology.org/2020.aacl-demo.7/) 建议把前瞻性功效、假设检验和效应量组成完整流程；
[Hitchhiker's Guide](https://aclanthology.org/P18-1128/) 强调统计检验必须匹配任务、指标和依赖结构。

本项目保留 document-cluster paired bootstrap 和三 matched seeds，同时新增：

1. 用冻结 anchor 的逐文档输出，在看新方法结果前模拟 MDE 与 power curve；
2. 登记最小有意义效应，不只看 CI 是否刚过零；
3. internal-dev 功效不够时，优先使用预冻结 repeated split / cross-validation 做选模稳定性，并把 public
   valid 作为一次 sealed final evaluation；
4. final-valid 历史访问继续披露；新 protocol 不能声称严格 blind test；
5. 稀有类不以单点 F1 硬判，但必须有合并后的非劣 CI、支持数和错误类型；主 macro-F1 不降标。

## 4. 三章方法蓝图

| 章 | 已被证伪或未完成的旧机制 | v6.1 核心机制 | 必须成立的中介 | 主结果硬门 |
|---|---|---|---|---|
| Ch1 | context pooling；泄漏型 event-level argument oracle | role-aligned mention-local argument posterior + uncertainty-gated clustering | 高混淆/跨句 false merge 下降，置信度与错误风险单调 | MUC 胜出；B³/CEAFe/BLANC/AVG 非劣；matched seeds + paired CI |
| Ch2 | family workpoint、近似 retriever、prototype、ATLoss | full-candidate pair evidence + sufficiency/abstention gate + relation-aware constraints | 跨句 causal FP 下降且 recall 保持 | causal micro-F1 胜出；subevent/temporal 非劣；matched seeds + paired CI |
| Ch3 | pooled evidence 双头；只换 evidence extractor | typed cue spans + known/unknown→modality→polarity factorization | modality-only、polarity-only、Uu 混淆按预注册方向下降 | 五类 macro-F1 胜出；evidence/稀有类非劣；matched seeds + paired CI |
| Ch4 | 历史 graph 正控与零散干预 | 三类上游 risk 的同实例 factorial + same-backbone consumer sensitivity | 输入风险预测下游损失，交互可正/零/负 | MRR/Hit@k、预测有效性、图依赖正控、paired CI/Holm |

每章都需要一个同 backbone 的最小因果矩阵：`anchor / strongest published-family baseline / proposed /
-core / mediator-negative-control`。更大 backbone 只能在机制通过后做对称迁移，不能救主表。

## 5. 执行路线

### 立即完成：G0 与 A3 诚实闭环

1. 本轮 P1 代码单一事实源整改及本地 full gate 已完成；
2. 基于最终代码重建 P1 trust root；
3. 运行 A3.6 official recipe 四臂，完成协议分账；
4. 无论 A3.6 分数如何，A3 的旧方法身份保持 failed，导出 relation fallback bundle。

### R1：不占 GPU 的研究设计审查

1. 建立 2022–2026 一手论文矩阵：任务、输入、公开代码、split、candidate、scorer、主指标、模型规模、
   消融、显著性与可复现风险；
2. 拉取并只读验证可运行官方实现，记录 upstream commit 与透明补丁；
3. 审计 MAVEN-ARG↔MAVEN-ERE↔MAVEN-FACT ID、argument role 和文档交集；
4. 从现有逐文档 predictions 生成三章 power/MDE 报告；
5. 不依赖 A3 待出结果的准备可与 A3.6 并行；对应证据齐备后再冻结 design brief 和 phase contract，
   之后才允许实现该方法。

### 当前确认性依赖计划（可由 R1 证据修订）

`R1 → {Ch1/C5, Ch2/A4, Ch3/D4} → Ch4/E3 → H2`。花括号内不是固定顺序：若 R1 未识别出
相互依赖，可按数据准备和算力并行或重排；E3 只要求三类真实上游 handoff 齐备。

每章先运行 baseline fidelity 与 CPU/CUDA smoke，再运行一个 seed-13 pilot。只有主指标和全部 mandatory
guardrails 过 promotion 才请求额外 seeds；三种子与消融在 final-valid 解封前整批冻结。一个机制家族失败
两轮就回 R1，不允许在 phase 内无界迭代；时间用于提出更好的可证伪机制，而不是增加随机搜索。

## 6. “不降标”的可操作定义

以下规则不得为了进度修改：

- 同 manifest、candidate universe、evaluator、输入前提与 backbone 的公平主表；
- 主指标超过冻结 primary anchor 和另一不同方法族强 baseline；
- matched seeds 13/17/42、document-cluster paired 95% CI 下界大于 0、至少 2/3 seed delta 为正；
- 主指标以外的校准、效率、难例或一致性指标不能替代胜出；
- full method、去核心机制、最强替代、负控和端到端风险传播完整；
- 失败和下降全部报告，final-valid 不用于选模，表格可反查到代码/数据/命令/checkpoint/hash。

可以调整且不构成降标的是：方法假设、模型结构、训练预算、phase 顺序、强 baseline roster，以及在新
protocol 冻结前增加合法公开数据或 repeated splits 来提高统计功效。任何调整必须前瞻性登记，不能根据
新方法结果追改。

## 7. 尚待确认的外部条件

1. 作者的学术/专业学位类型、入学年份和适用的同济计算机学科授予标准版本；
2. 2025 two-stage ERE 与 RESIJ 是否有可获取的官方代码/checkpoint；找不到时要明确 reproduction fidelity；
3. MAVEN-ARG 与当前 P1 数据版本的稳定 ID 交集和许可；
4. public valid 之外是否存在可合法提交的 hidden test；若没有，论文必须披露历史访问并加强 repeated-split
   稳定性与外部数据验证，不能声称严格 blind。

这些问题会影响实施方式，不改变论文质量目标。
