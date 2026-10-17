# A4目标条件监督的准入审查（2026-10-16，wip）

C5固定配置及D4当前绑定模板裁决后，正式接队C41-A-R。可执行动作认主表，
本卡不放行训练。科研价值对准表4-3/KR3.1–3.2：判断改变比较单位是否有独立机制，
排除普通multi-positive/listwise、阈值校准与coref重复权重的解释。

可行性限于冻结train、现有非权重证据、一手正文/源码与轻量CPU；没有读取
held-out/final-valid标签选组，没有新encoder/optimizer/seed或额外5090授权。
所有实测/分母只见R1 §25.77、§25.80、§25.87，不在此复制数字。

## 已确定的原生监督边界

- 同target确有多个distinct原因/前提；mention展开的多正例也可能只是同一个原因的
  coref重复。只改变展开权重不能冒称识别出新的多原因机制。
- CAUSE/PRECONDITION按原方向/标签处理，dataset-None表示未标注，不变成世界因果否定。
  BEFORE既不定义CAUSE，也不构成可靠因果负标签。
- 大量有其他candidate的target没有任一causal subtype；只训练有positive组的相对loss
  没有覆盖完整任务。保留原CE/绝对校准及全部评测候选，完整报告P/R和失去的正例。
- gold event clusters可用于训练监督/诊断分组；部署不得冒充已知正确的event identity。
  不缩candidate全集，不从评测挑组，不将不同方向/subtype混为一个winner。

## 已知强rival与新颖性边界

| 目标/机制 | 一手位置与已核范围 | 对当前候选的要求 |
|---|---|---|
| 普通per-positive与set-pool contrast | [SupCon §3.2](https://arxiv.org/pdf/2004.11362v5)，作者criterion CPU范围见R1 §25.80 | 不能只比弱set-pool；报告coref重复/机会匹配，不能称所有positives互不竞争 |
| group-restricted contrast denominator | [Conditional SupCon Eq2](https://aclanthology.org/2022.findings-emnlp.199.pdf)与作者实现，R1 §25.83 | 按target限制denominator本身已有；明确其与native候选单位的关系 |
| 多正例、learned TH与None排序 | [ATLOP Adaptive Thresholding](https://ojs.aaai.org/index.php/AAAI/article/download/17717/17524)、[作者ATLoss](https://github.com/wzhouad/ATLOP/blob/1db77ab8bc4fe5f7f8c23067ea17055d58b310a3/losses.py)；原criterion CPU前后向/decoder见§25.87 | “空原因+多正例”不足以立新意；原relation-label轴与A4 target-candidate轴不同，适配须披露，不直接叫同任务复现 |
| 去掉positive denominator项 | [DCL §3 Proposition2](https://arxiv.org/html/2110.06848v3) | 解耦分母是已知机制，不保证causal recall；不能靠新名字排除普通rival |
| entity mention logsumexp、pair-localized context | ATLOP Eq2、Eq6–7及作者model | 多mention pooling/条件context已有；gold coref输入前提与MAVEN mention任务分开核 |
| 双层contrast/共指hypergraph/Hawkes验证 | [SVRECI §3](https://aclanthology.org/2026.acl-long.871.pdf)，10-15来源卡 | “identity-aware/graph一致性”也非空白；官方runnable release未定位是UNKNOWN，不据正文重写冒称复现 |
| context-to-label contrast/GAN | [CLECI2026](https://www.mdpi.com/2078-2489/17/4/321)已读§3.1–3.2，完整公式/作者代码仍未核 | 当前访问受限，不能写全面排除重合或借其外部split成绩 |

ATLOP原criterion可运行仅指CPU合成logits；没有原benchmark复现、完整MAVEN adapter
或新方法准入。作者源码未发现根许可，当前只读研究，不集成成项目实现。

## 当前模板裁决（2026-10-17）

**关闭10-15当前目标监督模板的准入回合，未准入新方法；不是新方法效果FAIL。**
普通target-group contrast、positive分母改写、learned-null/重加权/硬MIL的简单组合没有
独立差异；完整原train残余与当前裁决见R1 §25.91。整个A4章与总Goal仍未完成。

上述机制审查已落地R1 §25.88：Gao2019的coref替换/软约束、JEREX预测簇MIL、GC2022
显式邻接兼容、ERGO隐含coref与MTEI任务级uncertainty已区分。普通重复重加权与
max-pool幂等性已有；同causal邻接也不能反推identity。它们不构成当前候选的独立差异。

原strong-anchor全train只读重放已完成，双端独立official/计数复算完全一致，原checkpoint
不变/进程GONE（R1 §25.89/§25.91）。它不提供held-out新效果，也没有独立证明任一机制。
同章下一问题见[上下文/表示残余卡](20261017_a4_context_residual_review.md)，先写主表再执行；
不改threshold、不预选模块，实质新假设通过R1才进入方法实现。

原strong-anchor的CE按pair分解，归一化在同pair的三类轴；没有跨原因candidate的
single-winner denominator。因此不得预先把错误归因为该不存在的竞争。共享参数的
梯度干扰与机会权重仍可能存在，需真实证据，不能用logit loss分解替代参数因果分析。

准入仍须最近邻机制差异、输入可行性、同协议强控制/核心消融/归属负控、条件power与
预算，再进入TDD生产门。现阶段没有新A4模型效果，也没有满足确认或额外seed前置。
