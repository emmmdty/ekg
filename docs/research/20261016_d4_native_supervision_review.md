# D4原生监督边界与接队准备（2026-10-16）

这是C41-T期间的文献/数据准备卡；正式D4-R仍在C5裁决后，训练未准入。
可执行顺序只认EXPERIMENT_PLAN §4，不产生第二条队列。

## 科研价值与可行性

对准表3-3/KR2.1–2.2：判断事件锚点归属是否有可识别的原生训练信号，排除
普通contrast/重加权/已有条件似然的解释。已有可靠linear与五维头控制裁决见
R1 §25.37；本轮监督覆盖/最近邻/标注policy事实只见§25.74、§25.77。
可行工作限于public-train、固定fold-1 train manifest和一手正文/代码；没有打开
held-out实例标签来挑配对，没有新encoder/optimizer、额外seed或final-valid访问。
本文不把可运行criterion、构造性质或标签覆盖当作方法效果/功效。

## 原生任务提供什么

[MAVEN-FACT原文 §2.1–2.2](https://aclanthology.org/2024.findings-emnlp.651.pdf)
将factuality source定为作者；它不是逐条引述的source-holder监督。
支持词有特定类别的标注policy，字段为空不能当随机缺失，也不自动构成
“该词不属于该事件”的negative attachment。稀有类和有效offset机会见R1 §25.74。
原文的support-word任务是EFD之后的预测pipeline，不能把gold support可用性当部署输入。

可以使用：同一原生语境中各事件各自的五类标签、可靠的正support offsets，
以及训练manifest内的ID/位置。不能制造：scope边界、引用者身份、同事件
sentence/document双factuality、删词后必翻转的标签或不同事件之间的NLI关系。

## 已作出的具体裁决

| 版本 | 证据与裁决 | 可保留的用途 |
|---|---|---|
| 缺cue/与另一事件support不重叠即负scope或负attachment | 数据监督不能辨认该负标签；R1 §25.74/§25.77。停止这个版本 | 原生正例覆盖与缺失policy诊断 |
| 不同事件factuality标签直接映射support/refute | [SDIN §3/Table1](https://aclanthology.org/2023.findings-acl.879.pdf)的标签来自同事件句级/文档级双监督，我们没有该字段；停止映射版本 | 以其推理机制作最近邻，不照抄标签 |
| 同语境按label-count条件化，枚举标签分配 | [ConditionalMNLogit真实源码](https://www.statsmodels.org/stable/_modules/statsmodels/discrete/conditional_models.html#ConditionalMNLogit.loglike)已有同组标签排列归一化。单把标准估计器换成事件/神经logits不构成独立创新 | 后续条件监督候选必须面对的普通强rival |
| 普通supcon、cue/类别重加权 | 不是新颖机制；[SupCon §3.2](https://arxiv.org/pdf/2004.11362v5)与[作者代码](https://github.com/HobbitLong/SupContrast)已核，criterion CPU可运行范围见R1 §25.80 | 匹配训练机会、样本/类别权重与容量的竞争解释 |
| 正例support辅助监督 | 当前证据没有否定其可行性，但“加入evidence/span/graph”已有先行研究，尚无可识别新差异 | 保留为待研究问题，不能直接生成训练合同 |

拒绝某个版本不等于取消D4方法章，也不等于所有事件条件监督均不可行。
旧cue/causal-residual及已失败家族不因此复活；不通过扫权重、更大backbone或
更换seed绕过止损。

## 最近邻已核范围与剩余缺口

- SDIN完整方法已核，所需双监督不能伪造；新问题不能只把它改名。
- [Trucidator §2.2/§3](https://aclanthology.org/2025.coling-main.139.pdf)额外生成/人工核查
  hallucination语料并做跨文档图推理，不能直接移入冻结MAVEN数据/口径。
- [CoDE](https://link.springer.com/chapter/10.1007/978-3-031-30675-4_36)、
  [scope方法](https://link.springer.com/chapter/10.1007/978-3-030-92185-9_34)只核到
  出版商摘要及访问限制；未核全文机制，不能宣称排除了重合。
- [HEGAT/EvDEFI](https://link.springer.com/article/10.1007/s11704-024-3809-6)正文为订阅预览。
  已访问官方三页supplement，能看到graph/span/lexical的架构级描述，不能代替正文公式。
- 代码搜索/下载的403、TLS或InternalError均是工具事实，不是方法/实现不存在的证据。
  访问边界与原始文件hash见R172/R175/R177/R179及对应结果段。

## 正式接队后要解决的决定性问题

必须先给出超出上述普通目标的实质差异及竞争解释，再判断准入；不能因为
原生异标签pair存在，就把归属机制当作已被唯一识别。保留现有marked-CLS主通路、
原token预算与可靠linear强控制，所有新增输入在推理时必须可得。

若继续正support方向，明确未标注字段如何处理、为何不会强迫错误的负scope、
共享support能否合法同时指向多个事件，以及如何与已有evidence模型区分。
若继续原生同语境标签方向，先说明新干预比普通CMLE/配对排序/supcon增加了什么；
不以标准归一化公式本身立贡献。两者都须包含样本机会匹配、普通重加权/容量对照、
核心消融与原生归属负控，并对所有五类宏指标和稀有类护栏负责。

条件power须来自合法冻结锚的配对不确定性与事前效应假设；不能由train机会数、
toy梯度、缺失率或“criterion跑通”推出。只有实质差异、数据/协议、功效/预算与
生产门闭合后才训练。科研路线裁决由持有队列的代理在现MAVEN授权内推进，
不把这些待解问题退回作者选题。
