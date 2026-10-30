# 论文框架的外部条件审查

**2026-10-30 指标准备补充**：[完整九表](NINE_TABLES.md)现列标准分项，
[P/R/F1及原文异常](../../results/PHASE_R1.md#fullmetrics-prf)在R1 §25.153；
[METRIC_SPEC](METRIC_SPEC.md)为三章共同主辅指标、局部分母、人口/单例、消融与成本
的最新前瞻定义。旧主分简版保留；不启动模型复现。

**作者随后确认的当前任务：[九张已发表成绩表](NINE_TABLES.md)**。当前只锚定每章/
每语料的论文与原分，不要求代码；下文的必需运行包取舍用于将来执行，不阻止
CohTP/CD-DCE等在文献成绩表中收录。本轮未开展baseline复现。

2026-10-30。作者确认范围：先确定框架中公开数据、对手、指标、实现和资源的条件，
本轮采用官方与已发表论文资料，不复现baseline、不运行模型；自有方法的效果不是
此次资料审查的验收项。实核数字/原表定位统一见[R1 §25.151](../../results/PHASE_R1.md)。

## 1. 裁决

**维持跨文档事件共指消解方向；采用三个递进方法章；采用LLM辅助的混合研究框架。**
主语料维持ECB+、GVC、WEC-Eng，三章均检验完整事件身份分区。问题链维持候选覆盖、
语义混淆、簇级错误连锁。数据/标注、标准评价、可用公共方法、开放基础权重已经有
明确来源，主方案不等待新人工标注、私有语料、闭源API、额外实体/时间关系gold，
也不等待未发布的最新SOTA代码或checkpoint。

“外部条件具备”包含下面已明示的接口适配工作，不等于把任意作者脚本直接启动。
特别是**没有一套近期作者仓库同时发布了三主语料的全部LLM辅助输入和原分**：
不能把SECURE的FCC列换名成WEC，也不能给WEC补上虚构原分。
WEC使用其官方基线与现有多语料公开实现作比较基础，新增LLM条件使用同一开放教师
与相同生成流程；换教师/跨语料的版本按透明适配命名，不冒充原作者方法原设定。

## 2. 每章的公开对手能否配齐

| 章/问题 | 必备比较包 | 直接来源与实现 | 外部输入是否可得 |
|---|---|---|---|
| 第3章：词面差异下的候选覆盖 | lemma/训练集同义lemma筛选、DCT表示检索、SECURE语义增强检索；固定后续精判/归并 | [DCT](https://aclanthology.org/2021.emnlp-main.106/)、[LemmaECR](https://aclanthology.org/2023.findings-acl.100/)、[SECURE](https://aclanthology.org/2024.acl-long.164/)；原代码及EasyECR多语料pipeline/config确实存在 | 原文/给定提及/训练身份簇；ECB+/GVC的SECURE原摘要全量实读并与原件ID对齐；WEC的新LLM列走开放教师适配，不依赖缺失GPT文件 |
| 第4章：相似语境不同事件的精判 | 原文cross-encoder、SECURE增强cross-encoder、固定开放LLM直接判别；保留同教师/同encoder对照 | DCT/SECURE官方训练和预测代码；CDLM公开预训练权重和cross-encoder代码；ROEC+CKD/LLM-RCDA为直接训练机制近邻 | 主包只要原文与训练gold身份；LLM使用公开权重。CKD的缺失GVC成品档、RCDA缺失的默认主实验增强CSV不成为主线前提 |
| 第5章：局部错误的簇级连锁 | CC、average-link、适用的single/complete-link、DCT/SECURE簇级合并判别 | WEC官方average-link、EasyECR公开聚类器；SECURE的`is_cluster_merge`/`transitive_closure_merge`真实实现；CohTP等作全局机制文献近邻 | 固定seed候选、同一冻结pair scorer及公开提及；不需要新增gold簇约束、论元或时间标签 |

所有章节另保留共同完整pipeline作为系统级比较。召回率、pair F1和簇错误统计用于
解释，完整CoNLL F1及其分项为共同最终结果。后章不仅与前章累计系统比较，还与
公共共同pipeline比较；适用时逐项单独替换，区分各层贡献。

第5章的公共聚类对手不只普通CC。SECURE源码先按pair分数排序，再在合并两个簇时
调用冻结cross-encoder对簇间提及对重新评分并检查平均支持。因而这里应固定的是
**pair评分函数、初始候选和额外查询权限/预算**，不能强迫它只读最初稀疏候选边、
把未评分边自动当负例，再称比较原方法。新增查询计入成本，所有decoder可访问相同
允许集合；只读缓存图的比较单列。原实现有抽样上限及归一化细节，适配时逐项记录。

## 3. 名册取舍：把缺失条件移出必需路径

| 方法 | 实际发布状态 | 本框架用途与执行前已有工作项 |
|---|---|---|
| DCT，EMNLP2021 | 作者链接的Helw150仓库有candidate generator/cross-encoder/config/scorer；根README仍是早期Barhom说明，不能只照根README选入口 | 经典主对照；采用对应新入口，WEC可借用EasyECR现成配置，属于跨语料透明适配 |
| LemmaECR，Findings ACL2023 | 原启发式/训练/预测及CoVaL存在；EasyECR有ECB+/GVC/WEC配置 | 主对照用non-oracle LH与可负担的Dsmall；Dlong论文训练使用大显存，不作为单卡主包必需项；oracle行不入有效主比较 |
| SECURE，ACL2024 | 真实检索/判别/簇合并/评测代码，GPL-3.0；ECB+/GVC/FCC已发布原处理件和GPT摘要；成品checkpoint与摘要生成脚本未发布 | 近期LLM主比较来源；ECB+/GVC可复用已发布摘要，无需重新购买GPT输出。WEC换开放教师/数据接口单独标识 |
| WEC原模型，NAACL2021 | 原pair训练、average-link、CoNLL输出代码，Apache-2.0；HF有实际`wec_model`大文件记录 | WEC原任务锚和聚类来源，补齐第三语料的官方比较基础；不要求重做RoBERTa预训练 |
| CDLM，Findings EMNLP2021 | HF公开预训练权重和tokenizer；作者仓库有cross-encoder训练/预测 | 文档语义控制，复用预训练权重，不把重新预训练作为论文条件 |
| ROEC+CKD，NAACL2024 | 有真实模型；ECB成品权重及线性/投影层存在；GVC链接仓库只有`.gitattributes`；部分入口保留未填路径并有语法占位 | 已发表LLM蒸馏近邻与背景分数；从必备直接运行包移出。需要时用原代码/公开材料做显式接线，不能称当前开箱可运行 |
| LLM-RCDA，NAACL2024 | MIT；真实训练/推理/处理件和若干增强CSV；默认main配置指定的三份`train_aug.csv`不在Git树，README另指Google Drive | 词面偏差/反事实增强的直接近邻；原分可报告；Drive主增强件未实得，暂不列已齐备的强制执行项 |
| CD-DCE，ACL2025 | 原论文有non-oracle成绩；官方CDCR仓库只有README/占位 | 近期语义/篇章近邻与公开原表，不等作者补代码，也不从正文重写后冒称复现 |
| CohTP，ACL2026 | 原文机制和主表已核；官方仓库只有`Comming soon` | 最新时间一致性近邻及原分背景；不作为运行前提，不把整套时间图/NLI/GPT条件强加本论文 |
| X-AMR，LREC-COLING2024 | Apache-2.0；图归并代码和ECB部分公开标注存在；另有GPT/PropBank/人工标注工具路径 | 图式身份推理近邻；gold X-AMR并非三语料共同输入，不列统一主表的必备对照 |

公开源没有根LICENSE的情况记录在凭证，不写成已获得某种开源授权；不把数据/模型/
代码三者许可证相互替代。此表是资料/源完整性审查，运行保真度以后按FR-016另记。

## 4. 原数据、官方指标和论文比较协议

1. 三语料原件及划分采用上一轮固定来源；不重新随机划分，不跨章改变给定提及人口。
2. ECB+遵循发布的句子过滤；GVC遵循已发表incident划分；WEC明确使用命名的原train
   和人工验证dev/test。GVC簇ID0跨split事实保留，不宣称所有身份均跨split未见。
3. 主结果采用公认CoNLL定义和各分项，统一比较的实现锚选官方
   [Reference Coreference Scorer v8.01](https://github.com/conll/reference-coreference-scorers)
   固定revision；按公开WEC等方法把跨文档身份置于同一评价分区。所有方法使用相同
   given mentions并输出全部提及；保留单例，去单例仅为明确声明的附加报告。
4. 主pipeline采用DCT/SECURE已有的全局候选方式，不依赖gold主题/子主题阻断。
   原论文使用预测文档分组、不同上下文或其他条件的行，保留原设定说明，不把原分
   当统一协议下的直接排名。SECURE原native scorer结果可作兼容报告，不以二者中
   较高者临时改主列。原文CoNLL/B³/Pairwise列分别记录，不互换。
5. 第一阶段允许替换检索器；第二阶段固定共同候选；第三阶段固定scorer及查询规则。
   为评价公正进行的共用适配记为适配；目标/源设定的差异不由“同一数据集名”抹平。
6. 本轮只建立**已发表结果表**；缺少原结果的单元留空。后续同协议实验另建表，
   不将自有成绩插入混协议原表就声称同条件超过全部方法。
7. 方法选择只看train/dev；公开test元数据/已发表分数用于此次条件审查，不用于
   新方法选型。所有最终预测固定后再评价，不沿用作者脚本的每轮test日志。

这套方案使用公开任务和评分器，没有新增人为评分指标。相同原划分是可比的必要
条件，输入/候选/主题/单例/decoder/selection也一起写进后续运行合同。

## 5. LLM采用裁决与学术依据

**采用LLM，但职责限定为文本语义增强及有明确预算的判别对照。**

- 主研究实现优先采用公开、ungated的`Qwen/Qwen3-8B`作冻结教师/语义辅助；三个
  数据集使用同一模型revision和输入规则。只输入文本与给定提及，不在测试提示中
  放gold簇/关系。生成的是模型辅助特征，不构造新的人工gold数据集。
- 主干仍是任务训练的encoder/事件对判别器，最终由结构化归并输出合法身份分区。
  原文、原文加LLM辅助、固定LLM直接pair判别均保留为对照，避免把增益仅归因于
  多了一个教师。LLM原输出和原文依据须能追溯，生成内容不自动当事实。
- SECURE证明“LLM理解＋任务模型”是同任务已发表路线；ROEC+CKD则说明训练期
  蒸馏、推理期不输入解释也有公开研究基础。两者用途不同，不混称同一种LLM方法。
- 不采用“让LLM一次生成全语料所有簇”作为唯一主干：公开论文记录了长输入/输出
  截断和结构覆盖问题；完整给定提及分区是我们的评价对象。按提及生成、有限候选
  精判和明确decoder更贴合这一研究对象。只声称减少LLM逐对调用，不把精确FAISS
  搜索或整个算法错误描述为线性复杂度。
- [ARR官方审稿指南](https://aclrollingreview.org/reviewerguidelines)的H7/H8/H14反对
  以方法简单、没有采用个人偏好的范式或无关闭源模型比较来否定研究。它支持的是
  问题与证据驱动的选型，不能解读成“学界统一要求每篇都用LLM”，也不解除本项目
  的主指标/强对照要求。CD-DCE2025使用BERT/Longformer的已发表实践可作为非LLM
  架构仍被接受的直接领域例证；本框架仍主动纳入LLM相关比较。

## 6. 外部依赖清单与预定处理

| 已识别事项 | 已核依据 | 后续处理，避免临场换方向 |
|---|---|---|
| GVC摘要字段不同 | 原JSON字段为`coref_elaboration_date`，代码按`elaboration-entityCoref_date`取；全部内容可得 | 内容不变，仅显式字段映射；旧文件hash保留；不以空字符串补缺 |
| ECB+/GVC提及ID规范不同于原始坐标 | ECB+的plus句号偏移、CSV尾空白；GVC的DCT/NEWLINE及保留token坐标均已定位；全部摘要ID与原标注对齐 | 只用有来源的确定映射；禁止原坐标拼接后按数量相等就宣称对齐 |
| 旧模型环境与新LLM环境冲突 | SECURE固定torch/CUDA/transformers旧版本；Qwen3官方要求更新的transformers | 独立环境，通过带mention ID的JSON/缓存交换；不把两套强塞同一环境；GPU只在已授权远端使用 |
| 有的方法没成品checkpoint | SECURE暂无；CKD的GVC链接为空；WEC/CDLM/基础encoder有真实权重文件记录 | 主包保留完整训练来源与公共预训练权重，不把必须拿到某作者best档设为条件；本轮不训练 |
| 大显存原版本 | Lemma Dlong原文用大显存A100；Dsmall原文用单卡RTX3090 | 不以Dlong为必需运行条件；主包用可解释的单卡版本，原分和不同backbone设定分列 |
| 开放LLM模型文件与预算 | Qwen3-8B五个权重分片及参数量在官方HF可查 | 冻结教师、短上下文、有限输出与小batch；不全参训练8B，不启动私有API，不以新购机器为前提；实际运行时做通常的显存/成本校验 |
| WEC缺少某作者GPT摘要/原成绩 | SECURE/CKD/RCDA原语料不含WEC | 官方WEC模型与现有多语料实现支撑主列；同开放教师条件是透明扩展。原表缺失记空，不能伪造“原版三列齐全” |

## 7. 本轮完成后的接续

框架资料审查按本文件定稿：三主语料、三递进问题、标准主指标、近期LLM比较和必备
公共实现均有路径；已知不完整发布件移出必须等待的链路。逐章模块设计在这一公共
框架内推进，不能随意更换任务、划分或评价对象。只建立本研究目录，不新开工程/
仓库/分支/worktree；正式父SPEC修订沿现有版本化流程办理。

本轮未执行baseline或模型。来源证据见
`runs/stages/R1/r1-v128-external-readiness-20261030/`；这份审查不把运行保真度写成已完成。
