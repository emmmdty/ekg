# 每章对标、公开实现与多语料审查

状态：一手来源前置审查；不是已复现排行榜。外部数字及精确表格位置只见R1 §25.146。
**续查已覆盖本页部分未知项**：新增ICGR/CRFIE/堆叠图学习全文、DiffusECI作者源码、
MECI英文完整train与文章级split元数据；原B已否决为独立贡献，UAIGR新定位同名
README而非模型实现。新增机制、版本、指标出处与判读边界见
[续查报告](FOLLOWUP_EVIDENCE.md)、R1 §25.147及`followup_sources.json`；原来源记录不覆写。

## 一、每章必须回答的文献问题

| 章节候选 | 科学问题 | 必须比较的机制/方法 | 为什么这些对照不可省 |
|---|---|---|---|
| 方法A：文本条件联合关系判别 | 两条关系的联合信息能否提供边缘概率和普通辅助监督之外的判别收益 | official joint、ERGO及CE控制；PPAT；普通full-Q/product/aux-only；EHNEM、SVRECI、CopulaLSP等直接近邻审查 | “多事件交互/高阶/联合”均不是新概念；必须排除普通联合分类和图传播解释 |
| 方法B：带噪预测结构纠错 | 不正确的输入边和缺失边如何影响后续关系决策，能否同时改善误报与漏检 | ERGO、PPAT；匹配的普通结构修正/置信度控制；UCGraph、SVRECI、iLIF等机制邻居 | “先高置信边、再迭代推理”“图补全”“结构一致性”已经存在，不能换名 |
| 构建验证 | 在相同节点/文档/候选上，两方法独立与组合的构建质量是否改善 | 固定基础pipeline、A-only、B-only、A+B；相同固定其他组件 | 不把不同上游、不同split或无输入能力的KGC模型硬放成同协议胜利 |

## 二、已核的一手方法与代码

下表中的“可借鉴”仅表示实际源码存在且相关；不等于安装、训练、复现或预算通过。
原论文数字不填进统一重跑表；代码缺失仍作为新颖性邻居保留。

| 论文 / 年份 | 方法实质与核查位置 | 作者代码/实际文件 | 可复用性与本轮裁决 |
|---|---|---|---|
| [ERGO / COLING 2022](https://aclanthology.org/2022.coling-1.185.pdf) | event-pair relational graph、RGT、focal；正文§3–4 | [chenmeiqii/ERGO](https://github.com/chenmeiqii/ERGO)，真实`model.py/processor.py/train.py/utils.py`和ESL缓存；固定revision见sources | 本项目MAVEN native透明适配与CE控制已跑完。原发布缺`processor_esl`命名接线/原特征生成与BERT实现；CTB独立输入仍需接线，不冒称原CLI即插即用 |
| [PPAT / IJCAI 2023](https://www.ijcai.org/proceedings/2023/0572.pdf) | 先句内再句间的渐进pair attention；§3、表1–4 | [HITsz-TMG/PPAT](https://github.com/HITsz-TMG/PPAT)，BERT/Longformer各有dataset/model/framework/graph_builder；发布ESC/CTB折 | 真实可复用图模型与训练器。源码因果矩阵对称赋值；MAVEN native有向子类型不能原样导入。CTB原入口test兼作dev，发布一个折存在源文档交集；统一重跑须更正选模并声明适配 |
| [SemDI / EMNLP 2024](https://aclanthology.org/2024.emnlp-main.87.pdf) | 共享编码、cloze生成token、语义依赖查询；§3、§5.1、表2–4 | [hrlics/SemDI](https://github.com/hrlics/SemDI)，MIT；真实model/train/utils/脚本、processed数据及checkpoint路径 | 语义判别强邻居；原test-fold F1选best不能继承。ESC*不是第三语料；原逐pair句子输入与document输入能力须区分。主表和消融的CTB行不一致，不能取较高行当主结果 |
| [HOTECI / LREC-COLING 2024](https://aclanthology.org/2024.lrec-main.711.pdf) | T5、层级句/词选择、OT、RL、ConceptNet背景；§2–3/表1–3 | [hieum98/HOTECI](https://github.com/hieum98/HOTECI)，真实`run.py`、readers/preprocessor、HOTEERE/generator/selector/sinkhorn | 可复用raw readers和真实训练组件；额外背景知识、检索依赖、预算与native适配未验收，不以“有仓库”列已跑分数 |
| [ICCL / EMNLP 2024](https://aclanthology.org/2024.emnlp-main.51.pdf) | 标签平衡in-context示例＋mention/prompt contrast；§3、表1–2 | [ChaoLiang-HUST/ICCL](https://github.com/ChaoLiang-HUST/ICCL)，有真实model/main/load_data | 当前loader需要`train.npy`，该文件不在当前发布树；默认只接ESC。代码真实但输入链不完整，暂不列即跑baseline。普通in-context/contrast不作本文创新 |
| [LLMERE / COLING 2025](https://aclanthology.org/2025.coling-main.500.pdf) | 按目标一次回答多个关系、分块、coref/transitive rationales；§3/表2 | [HerbertHu/LLMERE](https://github.com/HerbertHu/LLMERE)，本项目既有发布物审查见R1 §9及名册 | 已有结论不重复审计：训练/推理恢复及本项目final-valid保真度边界未闭合；不读取其封存集预测来选方案 |
| [BT-ESupCL / Neurocomputing 2025](https://doi.org/10.1016/j.neucom.2024.129232) | 复合回译、事件级对比采样、噪声与类不平衡目标；出版方摘要/引言 | [Ewillingfly/BT-ESupCL](https://github.com/Ewillingfly/BT-ESupCL)，本次tree只有README | 未取得可运行官方实现，正文完整表格未核全；不引用其摘要增益作为本项目门或把它算已跑对手 |
| [EHNEM / Computer Speech & Language 2025](https://doi.org/10.1016/j.csl.2024.101752) | 潜在边→同cause/effect超边→hypergraph学习；出版方方法说明 | 找到[yuu-hub-fuu/EHNEM](https://github.com/yuu-hub-fuu/EHNEM)，README明确自称尝试复现且有处理差异 | 该仓库不能当作者实现；当前官方实现未定位，完整原表未取得。它覆盖普通相关cause/effect建模动机，新颖性不能因代码缺失而忽略 |
| [SERE / Findings ACL 2026](https://arxiv.org/abs/2605.03701) | ConceptNet路径、依存树距离、因果pattern筛选示例；§3/表2–3 | [DMIRLAB-Group/SERE](https://github.com/DMIRLAB-Group/SERE)，真实sere/retriever/syntactic/preprocess | 依赖GPT API、Neo4j、ConceptNet和外部处理数据；无本轮API支出/上传许可，不执行。不得把检索/pattern/高精度低召回直接称本文新机制 |
| [SVRECI / ACL 2026](https://aclanthology.org/2026.acl-long.871.pdf) | LLM/超图建议、Topological Hawkes验证、动态修正与双层contrast；§3/表1–3 | 正文及GitHub精确名检索未找到作者运行实现；有界未定位，非“证明不存在” | 当前不重写冒称复现。它已经覆盖一般叙事一致性和迭代降噪，方法B必须给出更具体差异 |
| [UCGraph / IJCAI 2021](https://www.ijcai.org/proceedings/2021/533) | 时间图mask预训练与certain-first推理 | 作者论文指向Event_Temp；本轮只复核机制，不声称新完成运行审计 | 时间关系不是因果任务的直接分数对手；用于否定“不确定性引导图补全”这一宽泛创新表述 |

两方法章的**共同核心可运行候选**优先ERGO/PPAT/SemDI＋匹配编码器分类基线。
其中只有既有ERGO MAVEN档已有本项目运行证据，其他都是源码/数据前置候选。
ICCL输入缺失不能靠自己重造`train.npy`后声称忠实复现；HOTECI可作为追加方法族，
但必须先闭合真实依赖/输入/成本。最终名册要包含直接强邻居，不能专挑较弱旧模型。

### 代码公开与开放许可分开记

SemDI的当前发布树有MIT许可证。ERGO、PPAT、HOTECI、ICCL、SERE本次所核完整
发布树未见独立LICENSE文件，应标“代码公开、许可未明”，不能统一写成“开放许可
已核通过”。LLMERE沿用既有名册身份，本轮未新增完整许可审计。EHNEM定位件是
第三方尝试，BT-ESupCL定位件无模型代码。后续采用/发布任何适配时，逐项保留许可
身份和源码补丁，不能把公开访问与运行/复现/许可四种状态混成一个“开源PASS”。

A的CopulaLSP/SPEECH机制核查继承R1 §25.142的固定来源和边界，不重复计算；
UAIGR仍是未核完整公式的最近邻缺口，不能因访问失败而认定没有机制重合。

## 三、数据前置审查

| 语料 | 已有可得性证据 | 原生任务/协议边界 | 冻结前还缺什么 |
|---|---|---|---|
| MAVEN-ERE | 现有train/manifest/official evaluator和native强对照；不新读final-valid | 有向NONE/PRECONDITION/CAUSE，完整有序候选；已冻结internal-dev，反复开发历史须披露 | 新方法不得改旧候选/锚；跨语料新规范不回写旧裁决 |
| ESC v0.9 | 作者repo原XML路径、公开许可；本次raw XML和PPAT train JSON实际取得并解析 | 新闻、topic结构、句内/跨句；公开实现常将因果转二类对称关系，必须显式声明；版本不能混用 | 完整source→候选→fold→独立dev/evaluator身份；topic外推与文档CV的主张不能混淆 |
| CTB | 作者CAT ZIP实际取得，全量XML/引用完整性已查；PPAT train/test格式已读 | 原CLINK有方向；通行SECI多为句内二类；不能把CTB成绩当跨句推理效果 | 文档分组、独立selection、固定完整句内候选与negative policy；不能照搬test选模 |
| MECI-English（备用） | 作者repo固定版本有train/dev/test路径，本次英文train原TSVX已取得；HOTECI有真实reader | 文档级、有显式事件与关系记录，不与MAVEN任意拼接；语言不是独立数据集 | 全量候选的未标注边含义、许可/使用说明、原生evaluator、当前强对手输入与完整运行均未闭合 |

### 不能从“有数据”推导的方法可行性

R122需要同一实例内两条关系的联合监督。已在发布的ESC/CTB训练件核到事件span、
原文、正边及多事件实例；但二类无向表述不支持直接复用四种有向pattern或三类Q。
候选若保留，必须写明`C_dataset`、监督可识别性及二类退化版本，且不把无标注边
自动解释成世界无因果。CTB非零联合监督较少，不能套用旧MAVEN单删FP的power。

### 最近数据的取舍

EventRelBench(2025)是关系选择题，且复用了MAVEN/ESC，不是独立同任务完整候选主表。
MiGUE-Bench(2026)公开任务与结构归纳候选答案可读，但自动标注、schema和任务不同。
NYT-SEG(2025)公开标注图而原新闻文本另需取得。H²EPR(2026)参考图需申请访问。
本轮不把它们临时加成“已完成第三数据集”；近期性由对标方法与问题界定体现，
新数据必须满足同样的完整输入和可比性标准后才能替换主语料。

## 四、对比表怎样成立

同一张表按MAVEN/ESC/CTB分列，每列内的所有方法必须共享完整候选、split、输入条件
和评分器；不同列保留原生标签/方向说明，**不把不同列分数直接相减或作总平均**。
原论文数字单列“来源与协议背景表”，统一主表只放重新运行且身份清楚的结果。
只适用于句内的SemDI若未有正文支持的跨句适配，不填ESC整体列；不填空占位冒充胜利。

## 五、检索边界

本次按任务/精确方法名/官方链接，覆盖图推理、语义判别、prompt/contrast、
生成/检索和结构纠错邻居，并追查2025–2026直接方法。八篇开放PDF已取得并提取，
部分主表已本地渲染目视核对；两篇出版方页面只有部分全文。GitHub以官方链接优先，
精确名检索用于缺失实现；不把第三方榜单、第三方复现或README承诺当原代码。
不是穷尽所有ECI论文，未取得的全文/官方实现明确留缺，不能宣布最近邻排除已闭合。
