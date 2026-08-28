# A1 阶段报告：术语地图与 2024–2026 明示卡点

> 调研日期：2026-08-25
>
> 范围：仅对应 `EXPLORATION_PROMPT.md` 的 Block 1.1–1.2；不含榜单、顶会计数、数据集可得性或章节方案。
> 方法：先用 `paper-search` 检索，再回到论文 PDF、ACL Anthology、arXiv 或 DOI 页面核验。本文没有报告实验指标数字。

## 1. 术语地图

### 1.1 最关键的区分：节点表示“这一次发生”还是“通常会发生”

| 术语 | 文献中的典型对象 | 节点与边的典型语义 | 与其他术语的关系 | 对本课题命名的证据含义 |
|---|---|---|---|---|
| **event knowledge graph (EKG)** | 可识别的历史或现实事件实例 | 事件是一级节点，连到参与实体、时间、地点及事件间时间/因果等关系；常保留跨来源整合后的事件身份 | 通常是 **event-centric KG** 的具体实现；若强调时间，也会称 event-centric temporal KG | EventKG 把当代和历史事件及时间关系整合为规范表示；因此，若研究对象是“某次罢工/制裁/事故”及其来源、时间和参与方，这个名称最贴切。[EventKG, arXiv:1804.04526](https://arxiv.org/abs/1804.04526) |
| **event-centric KG** | 一种知识表示设计取向，而非单一任务 | 相对 entity-centric KG，把事件提升为一级对象，再组织实体、事件和时间关系 | 是上位/描述性名称；与 EKG 高度重叠，不宜据名称假定其一定由文本端到端抽取 | 该词强调“以事件为中心”，不自动承诺节点是实例还是抽象概念；必须继续检查 schema 与数据来源。EventKG 与 OEKG 都按此意义使用。[OEKG, arXiv:2302.14688](https://arxiv.org/abs/2302.14688) |
| **event graph** | 任何把事件表示成图的工作对象 | 可能是单文档图、显著事件图、时间/因果/子事件图，也可能是跨语料知识库 | **不是稳定同义词**；既可指实例图，也可指脚本/演化图。必须由节点定义和边类型消歧 | 例如 CALLMSAE 的 salient event graph 是长文档内显著事件及 before/causal/subevent 边；NEEG 的 event graph 则是跨语料抽象演化知识，两者不能仅凭名称合并。[CALLMSAE, ACL ID 2025.naacl-long.112](https://aclanthology.org/2025.naacl-long.112/)；[NEEG, DOI 10.24963/ijcai.2018/584](https://doi.org/10.24963/ijcai.2018/584) |
| **eventuality graph / eventuality knowledge graph** | 活动、状态和事件的语言模式及常识 | ASER 中 eventuality 由依存图表示，边来自浅层话语关系；侧重语料统计得到的常识和选择偏好，而非某个有时间锚的现实事件 | 与 script/event-logic 一支相邻；范围还包括 state/activity，不能直接等同 occurrence-level EKG | 若节点像“供应短缺导致涨价”这类可复用模式而非一条具体新闻事件，eventuality KG 是更准确的英文参照。[ASER, arXiv:2104.02137；DOI 10.1016/j.artint.2022.103740](https://arxiv.org/abs/2104.02137) |
| **event logic graph（中文常称“事理图谱”）** | 抽象事件之间的演化、因果、顺承或条件逻辑 | 常把抽象事件短语作为节点，以因果/顺承等“事理”关系连边，用于风险推演或后继事件预测 | 与 eventuality graph、script graph、NEEG 有显著交集；但英文 **event logic graph** 不是像 KG 那样稳定、统一的国际术语 | 中文“事理图谱”更接近“抽象事件模式 + 演化/因果逻辑”这一研究支系，而不是 EventKG 式历史事件库。未找到 2024–2026 权威英文 survey 给出统一定义，故不把它强行等同某一个英文标签。 |
| **script knowledge** | 某类情境中典型、反复出现的事件序列 | 事件通常按谓词—论元/参与者表示；关系表达常见次序、角色连续性或可预测后继 | 是知识内容/建模目标，不必以图存储；eventuality graph、narrative chain 和 NEEG 都可承载 script knowledge | 它回答“通常接下来发生什么”，不是“这条报道中的两次提及是否为同一现实事件”。叙事事件链的经典定义以共享主角组织事件。[Chambers & Jurafsky, ACL ID P08-1090](https://aclanthology.org/P08-1090/) |
| **narrative graph** | 故事/报道中的事件组织，或由大量叙事链汇聚出的演化图 | 可表示一篇叙事的局部结构，也可表示跨语料的典型演化模式 | 边界跨越 instance-level 与 pattern-level；单独看到该词不能判断是哪一支 | NEEG 明确把新闻中的 narrative event chains 汇成描述演化规律的知识库，用于 script event prediction；这更接近事理/脚本支系而非事件实例库。[arXiv:1805.05081](https://arxiv.org/abs/1805.05081) |

补充边界：**temporal knowledge graph** 常把带时间戳的事实三元组作为基本单元，并不必然存在事件节点。因此“有时间”不足以把 TKG 与事件图谱视为同义词；需要查看事件是否为一级对象。

### 1.2 哪些可以视作同一支，哪些不可以

- `event knowledge graph` 与 `event-centric KG` 在实际论文中经常重叠：前者更像产物名称，后者更像建模取向。二者都仍需检查事件节点到底是现实实例还是抽象类型。
- `eventuality graph`、`event logic graph/事理图谱`、`script knowledge`、一部分 `narrative graph` 处在相邻的**模式级**支系：共同关注可复用的活动/状态/事件规律、演化和常识，但节点语言结构、边集与推理任务并不统一，不能当作完全同义词。
- `event graph` 是最宽泛也最危险的标签。它既覆盖文档内具体事件图，也覆盖 NEEG 一类模式库；检索和综述必须附加 `instance/occurrence`、`salient/document-level` 或 `script/evolutionary` 等限定词。
- “事件抽取结果组成一张图”不自动等于“事件知识图谱”：若没有跨文档身份、规范化、时间/来源或可复用 schema，它更稳妥地只是 document event graph。

### 1.3 “事件图谱”与“事理图谱”二选一时应看的证据

这不是按竞争强弱做推荐，而是按**研究对象的本体承诺**做选择：

| 需要核实的问题 | 证据若回答“是”，更支持“事件图谱” | 证据若回答“否/改为通常规律”，更支持“事理图谱” |
|---|---|---|
| 节点是否指向可核验的一次现实发生？ | 需要事件身份、日期、地点、参与方、文档来源和跨文档共指 | 节点是去情境化的谓词—论元模式或事件类型 |
| 错误代价来自哪里？ | 把两次现实事件误合并、漏掉时间线关系、丢失来源会破坏风险监测 | 主要错误是演化规律、因果方向或后继事件预测不合理 |
| 下游问题问什么？ | “何时、何地、谁参与、哪些报道指向同一事件、其后发生了什么” | “这类情境通常如何发展、下一步可能是什么、有哪些常见因果链” |
| 所需证据能否追溯？ | 风险监测需要具体报道和事实来源的可审计链 | 目标是从大语料归纳总体常识或脚本，不要求逐条对应现实发生 |

就题目背景而言，“风险监测”本身不能替二者做决定：**事件级预警与溯源**需要 occurrence-level 事件图谱；**风险演化规律与后继推演**更接近事理图谱。最终名称应由公开 benchmark 的节点标注对象和下游问题来约束，不能先选中文名再把数据硬套进去。

## 2. 2024–2026 survey / position paper 明示的卡点

### 2.1 事件抽取：覆盖、泛化、效率和评测仍未解决

1. **生成范式没有只是“替换解码器”这么简单。** Simon et al. 的 2024 survey 在 §4 “Summary and Outlook” 明说：> “the field has yet to embrace generative approaches to EE fully.”（p. 81）

   作者随后主张，从 span/sentence-level 标注走向更抽象的 document-level 事件分析，并使评测更关注语义而非字符串匹配；但 §6 同时指出抽象生成会放大幻觉、非事实事件和英语数据偏置。这表明开放问题是**新任务定义 + 语义评测 + 事实约束**的组合，而不只是把既有抽取模板交给 LLM。[ACL ID 2024.futured-1.7；DOI 10.18653/v1/2024.futured-1.7](https://aclanthology.org/2024.futured-1.7/)

2. **统一 benchmark 之后，领域外泛化与类型覆盖仍是明示卡点。** TextEE 的 §6 写道：> “Most existing event extraction models focus on in-domain performance.”（p. 12812）

   同一节把开放问题具体化为：现有数据的事件类型覆盖窄；新事件概念上容易失效；高质量、广覆盖、细粒度角色数据难获得；枚举每个事件/角色类型造成多次推理，效率随 schema 扩大而恶化。其结论还将一致预处理、充分评测和可复现性列为基础设施问题。[ACL ID 2024.findings-acl.760；arXiv:2311.09562；DOI 10.18653/v1/2024.findings-acl.760](https://aclanthology.org/2024.findings-acl.760/)

3. **事件抽取的“比较不可比”不是附带问题。** 生成式 EE survey 的 §5 指出系统输出空间、数据处理和缺少 pipeline evaluation 会妨碍公平比较；TextEE 则直接以标准化数据处理和 split 回应这些问题。故“改进抽取”之前必须先固定任务口径，不能把不同预处理或字符串/语义评测混为一个榜单。

### 2.2 事件关系：因果方向、因果链、不确定性与联合抽取

Cheng et al. 的 2025 ECI survey 在 §8 集中列出未来方向：

- 因果识别往往只判断“是否有关系”，忽略方向；简单串接因果事件对会出现 context drift 和 threshold effect，因此可靠因果链不是 pairwise ECI 的自然副产品（§8.1–8.2，pp. 25–26）。
- 现实因果有置信度与条件性，但现有标注多为二/三值、缺少置信信息；建立这种数据本身又需要复杂标注（§8.3，p. 26）。
- 多数 ECI 假设事件 mention 已知，前置 EE 会传播错误；事件抽取与因果识别的联合建模仍更复杂（§8.4，p. 26）。
- 黑盒方法缺少可解释因果路径；多模态需要跨模态实体消歧和语义对齐；多关系联合模型要平衡 relation-specific 与 shared components；各数据集因因果定义和标注指南不统一而不可比（§8.5–8.6、§8.9–8.10，pp. 26–27）。
- 对 few/zero-shot LLM，原文明确指出：> “they still face the challenge of causal halluciantion and self inconsistency of LLMs.”（原文拼写如此；§8.7，p. 27）

这些卡点共同说明，事件关系的核心并未被“LLM 能生成一条因果解释”绕过：方向、长链一致性、置信表达、上游误差和统一标注仍是独立问题。[DOI 10.1145/3756009；arXiv:2411.10371](https://arxiv.org/abs/2411.10371)

### 2.3 时间关系/时间图：完整图、生成式结构输出和公共评测设施

Lee et al. 的 EMNLP 2025 review 在 Appendix F 给出四组未来方向：丰富 annotation framework、提高领域多样性、探索生成式方法、建立公共工具/benchmark 和面向人的时间线应用。

- 当前 TimeML 类框架常只形成时间实体与时间关系图；作者要求进一步纳入 entity relations 以及完整 event triggers/arguments，才能形成内容更完整的 temporal graph（§F.1，pp. 28838–28839）。
- 原文指出：> “The application of generative LLMs in the field of time expression identification, normalization, and temporal relation extraction remains underexplored.”（§F.2，p. 28839）
- LLM 擅长非结构文本，却需要专门的 input-output design 才能稳定输出结构化时间信息（§F.2）。
- 该 review 明示缺少易用的公共模型仓库，并提出建立**隐藏 test set 的公共 benchmark**；现有论文虽都报常见指标，具体纳入哪些关系标签却可能不同（§F.3，p. 28839）。
- 现有 temporal graph 可视化对人往往难以解释；面向 HCI 的时间线呈现与用户研究仍不足（§F.4）。

这组证据把“结构化关系抽取”与“可使用的事件时间图”区分开：完整 schema、稳定结构输出、统一隐藏测试和面向人的可解释呈现都还没有被单一关系分类任务覆盖。[ACL ID 2025.emnlp-main.1467；DOI 10.18653/v1/2025.emnlp-main.1467](https://aclanthology.org/2025.emnlp-main.1467/)

### 2.4 structured knowledge for LLM：互补性仍有条件

Pan et al. 的 2024 TKDE roadmap 不是事件专门综述，但对“为何 LLM 时代还讨论结构知识”给出直接边界：LLM 的参数化知识难以显式访问、会幻觉且更新困难；KG 可提供结构化事实、外部检索和推理支架。与此同时，KG 自身存在不完整、动态演化、构建维护成本和跨模态对齐问题。其 §7 将幻觉检测/缓解、黑盒 LLM 的知识注入、KG 结构理解、协同推理和统一 benchmark 作为后续问题（pp. 3595–3597）。因此文献论证的是**条件互补**，不是“图一定优于 LLM”，也不是“LLM 已使图失效”。[arXiv:2306.08302；DOI 10.1109/TKDE.2024.3352100](https://arxiv.org/abs/2306.08302)

### 2.5 script / narrative：本轮未取得合格的 2024–2026 survey/position 证据

本轮检索得到 2024–2025 的具体方法论文以及较早的 script/narrative 代表工作，但没有取得一篇满足以下三点的 2024–2026 一手综述/position 原文：以 NLP script learning 或 narrative event graph 为主体、明确汇总开放问题、并可稳定定位到原文段落。故这里不把 event prediction 方法论文的 limitation 冒充“领域共识”。已核实的较早定义证据仅用于上面的术语边界：Chambers & Jurafsky 的 narrative event chain，以及 Li et al. 的 NEEG。

## 3. 来源表

| 用途 | 一手来源与标识 | 本报告核验位置 |
|---|---|---|
| occurrence-level event-centric KG 定义 | Gottschalk & Demidova, *EventKG*, arXiv:1804.04526；DOI 10.1007/978-3-319-93417-4_18 | 摘要、§1–3；[arXiv](https://arxiv.org/abs/1804.04526) |
| 开放 event-centric KG 示例 | Gottschalk et al., *OEKG*, arXiv:2302.14688 | 摘要与 common schema；[arXiv](https://arxiv.org/abs/2302.14688) |
| eventuality 定义 | Zhang et al., *ASER*, arXiv:2104.02137；DOI 10.1016/j.artint.2022.103740 | 摘要、eventuality/dependency-graph 定义；[arXiv](https://arxiv.org/abs/2104.02137) |
| script / narrative chain 定义 | Chambers & Jurafsky, *Unsupervised Learning of Narrative Event Chains*, ACL ID P08-1090 | §2；[ACL Anthology](https://aclanthology.org/P08-1090/) |
| narrative evolutionary graph | Li, Ding & Liu, *Constructing Narrative Event Evolutionary Graph for Script Event Prediction*, arXiv:1805.05081；DOI 10.24963/ijcai.2018/584 | 摘要、§1–2；[IJCAI](https://doi.org/10.24963/ijcai.2018/584) |
| “event graph”语义依任务变化 | Tan et al., *Cascading Large Language Models for Salient Event Graph Generation*, ACL ID 2025.naacl-long.112；arXiv:2406.18449 | 摘要、任务定义；[ACL Anthology](https://aclanthology.org/2025.naacl-long.112/) |
| 生成式事件抽取 outlook | Simon et al., 2024, ACL ID 2024.futured-1.7；DOI 10.18653/v1/2024.futured-1.7 | §4 p.81；§5–6 pp.81–82；[ACL Anthology](https://aclanthology.org/2024.futured-1.7/) |
| EE 统一评测与明示未来问题 | Huang et al., *TextEE*, ACL ID 2024.findings-acl.760；arXiv:2311.09562；DOI 10.18653/v1/2024.findings-acl.760 | §6 p.12812；结论 p.12813；[ACL Anthology](https://aclanthology.org/2024.findings-acl.760/) |
| 事件因果 survey | Cheng et al., *A Survey of Event Causality Identification*, arXiv:2411.10371；DOI 10.1145/3756009 | §8.1–8.10 pp.25–27（作者稿分页）；[arXiv](https://arxiv.org/abs/2411.10371) |
| 时间 IE review | Lee et al., *Transformer-Based Temporal Information Extraction and Application: A Review*, ACL ID 2025.emnlp-main.1467；DOI 10.18653/v1/2025.emnlp-main.1467 | Appendix F pp.28837–28839；[ACL Anthology](https://aclanthology.org/2025.emnlp-main.1467/) |
| LLM–KG roadmap | Pan et al., *Unifying Large Language Models and Knowledge Graphs: A Roadmap*, arXiv:2306.08302；DOI 10.1109/TKDE.2024.3352100 | §7 pp.3595–3597；[arXiv](https://arxiv.org/abs/2306.08302) |

## 4. 未能核实

- **2024–2026 script learning / narrative graph 的综述或 position paper**：没有取得满足主题、年份和明确 future/open-problem 段落三项要求的原文；不能据个别方法论文推成领域共识。
- **“事理图谱 = event logic graph”的统一国际定义**：能核实中文/应用论文这样翻译和使用，但未找到由主流英文 survey 固化的一对一术语标准。报告因此只给概念支系对应，不声称严格同义。
- **2024–2026 专门的 event knowledge graph construction survey**：本轮找到的最接近系统综述是 Knez & Žitnik, *Event-Centric Temporal Knowledge Graph Construction: A Survey*, DOI [10.3390/math11234852](https://doi.org/10.3390/math11234852)，正式发表于 2023-12，超出指定年份窗口，故未把它列作 2024–2026 证据。
- **narrative graph 的唯一标准 schema**：该词同时用于单文档叙事结构和跨语料演化知识库；未发现统一 schema，必须逐论文判定。
- 本轮按任务收缩**没有**核查数据集下载/test 通道、复现实验、代码活性、单卡显存、2025–2026 论文计数或任何模型分数。

## 5. 我在探索中发现的、与预期不符的事实

1. `event graph` 不是能与“事件图谱”稳定一一对应的学术术语；同名工作可以分别研究文档内事件实例和跨语料脚本模式。
2. 中文“事理图谱”的最近邻不是 EventKG 式事件实例库，而是 eventuality/script/event-evolution 这一组彼此相邻却未统一的表示。
3. 2024 生成式 EE survey 并没有把未来概括为“用 LLM 提高 span F1”，反而要求重新考虑抽象、文档级任务与语义评测，同时警告幻觉和非事实事件。
4. EMNLP 2025 时间 IE review 仍把隐藏 test 的公共 benchmark、评测实现差异和公开模型仓库列为未来工作；这推翻了“成熟时间关系任务已有天然统一口径”的假设。
5. 指定年份内，script/narrative 与专门 event-KG construction 的高质量 survey 证据比事件抽取、因果和时间 IE 明显稀疏；不能为了凑齐术语而把老定义或单篇方法的 limitation 包装成 2024–2026 共识。

### 本块结论

- **已核实：**文献中存在一条 occurrence-level 的 event-centric KG 支系（EventKG/OEKG），以及一条 pattern-level 的 eventuality/script/narrative-evolution 支系（ASER、narrative event chains、NEEG）；二者在节点身份、时间/来源和下游问题上有可操作的边界。`event graph` 是跨两支的宽泛标签。（EventKG: arXiv:1804.04526；ASER: arXiv:2104.02137；NEEG: DOI 10.24963/ijcai.2018/584）
- **已核实：**2024–2025 一手综述/benchmark 明示的卡点包括：事件类型与领域覆盖、novel-event 泛化、schema 扩大时的效率、生成式抽取的任务与语义评测重构、幻觉/非事实事件、因果方向与链一致性、因果不确定性、上游 EE 误差传播、多关系联合、完整时间图 schema、结构化 LLM 输出、公共隐藏测试与评测口径。（ACL IDs 2024.futured-1.7、2024.findings-acl.760、2025.emnlp-main.1467；DOI 10.1145/3756009）
- **未能核实：**指定年份内 script/narrative 专项 survey、`event logic graph` 的统一英文定义，以及 2024–2026 专门 event-KG construction survey；本轮也未调查竞争密度、数据/test 可得性和单卡可行性。
- **对论文选题的含义：**“事件图谱 vs 事理图谱”首先决定研究对象是可追溯的现实事件实例，还是可迁移的抽象演化模式；风险监测可落入任一支，必须由公开数据的标注本体和下游问题决定。近年文献支持的真实问题集中在覆盖与泛化、关系/时间结构一致性、事实约束和统一评测，而不是笼统的“把 LLM 接到图谱上”。

## 6. 候选方向决策表（仅填本轮证据能支持的字段）

| 候选方向 | 问题价值（栏 A） | 竞争密度（栏 B） | 数据可得性 | test 可得性 | 单卡可行 | 与 LLM/Agent 技术栈的贴合度 | 关键风险 |
|---|---|---|---|---|---|---|---|
| occurrence-level 事件图谱 | 文献明示需要更广事件覆盖、领域外泛化、完整事件—时间—关系结构、可复现评测与事实约束 | 本轮未调查 | 本轮未调查 | 本轮未调查 | 本轮未调查 | 可结合 LLM 结构化抽取、检索与事实支架；贴合度本轮只做概念核实 | 上游误差累积；“文档图”冒充知识图谱；schema/评测不统一 |
| pattern-level 事理/演化图谱 | 因果方向、长链一致性、不确定性、解释路径和后继规律均是明示问题 | 本轮未调查 | 本轮未调查 | 本轮未调查 | 本轮未调查 | 可结合 LLM 归纳、因果链生成和图约束；贴合度本轮只做概念核实 | 中文/英文术语不统一；抽象生成产生非事实模式；指定年份的专项 survey 证据稀疏 |

# A2a 阶段报告：LLM 对事件子任务的实测冲击

> 范围：`EXPLORATION_PROMPT.md` Block 1.3。只判断直接 zero/few-shot LLM 与监督小模型的实测关系，以及 LLM 作为辅助组件的影响；不延伸到数据集选型、竞争密度或章节方案。
>
> 口径规则：下文只有标为“可比”的表可以作模型间判断。论文没有声明 split、评测脚本或 F1 聚合时，即使原论文把数字并排放置，本报告也标为“不可比”，不计算差值。

## 7. 有哪些系统评测

| 子任务 | 系统评测论文 | 模型与范围 | 能回答什么 | 重要边界 |
|---|---|---|---|---|
| 事件检测（ED）、事件论元抽取（EAE） | Huang et al., *TextEE: Benchmark, Reevaluation, Reflections, and Future Challenges in Event Extraction*, ACL ID `2024.findings-acl.760`, arXiv:2311.09562，Tables 6–7 | GPT-3.5-Turbo、Llama-2-13B/70B、Zephyr-7B、Mixtral-8x7B；跨 TextEE 多数据集 | 目前覆盖面最广的同一框架 LLM EE 评测 | 每数据集只抽样 250 documents；Tables 6–7 未交代样本来自五个重采样 split 中哪一个，也未声明 F1 的 micro/macro 聚合。因此数字只能作为论文内趋势，不能进入严格对标表。[原文](https://aclanthology.org/2024.findings-acl.760/) |
| ED、EAE；LLM 作数据标注器 | Chen et al., *Is a Large Language Model a Good Annotator for Event Extraction?*, DOI `10.1609/aaai.v38i16.29730`, Tables 1–4 | GPT-4、GPT-3.5-Turbo、PaLM；ACE 2005 与 MAVEN | 同时测试直接 zero/one-shot 抽取和 LLM 合成标注增强 | Tables 1–2 未明确写 train/dev/test split，未声明 micro/macro；论文只说采用 OmniEvent/ACE-DYGIE preprocessing。其与正文引用的既有监督数字不满足三轴对齐，故不可据此声称接近/超过。[AAAI 原文](https://ojs.aaai.org/index.php/AAAI/article/view/29730) |
| 文档级事件共指、时间、因果、子事件关系 | Wei, Gautam & Huang, *Are LLMs Good Annotators for Discourse-level Event Relation Extraction?*, ACL ID `2024.findings-emnlp.1`, arXiv:2407.19568，Table 2 | `gpt-3.5-turbo-16k`（闭源 API）、Llama-2-7B-chat（开放权重）；MAVEN-ERE | 四类关系在同一 full test 和官方 evaluator 下的直接 few-shot 对比 | GPT-4-1106-preview 只跑 first 10 validation documents（Table 11），不能与 full-test Table 2 混比。[原文](https://aclanthology.org/2024.findings-emnlp.1/) |
| 事件时间关系分类（TRC） | Roccabruna, Rizzoli & Riccardi, *Will LLMs Replace the Encoder-Only Models in Temporal Relation Classification?*, ACL ID `2024.emnlp-main.1136`, arXiv:2410.10476，Tables 2–3 | MATRES、TIMELINE、TB-Dense；七个开放/闭源 LLM 的 ICL，Llama-2-7B/13B LoRA，及 Llama-2/RoBERTa 编码器分类 | 目前找到的最完整“direct ICL / 监督 LoRA / 冻结特征编码器 / fully trained RoBERTa”同代码比较 | Table 2 的“fine-tuned zero-shot”是**无 demonstrations 的监督 LoRA**，不是无训练样本的 zero-shot；Table 3 的 frozen encoder 也训练分类层。[原文](https://aclanthology.org/2024.emnlp-main.1136/)；[官方代码](https://github.com/BrownFortress/LLMs-TRC) |
| 因果、子事件关系；压缩后抽取 | Guan et al., *TacoERE: Cluster-aware Compression for Event Relation Extraction*, ACL ID `2024.lrec-main.1348`, arXiv:2405.06890，Tables 1–2、5 | PLM 版：BERT 摘要器 + RoBERTa 预测器；LLM 版：Text-Davinci-003、ChatGPT、GPT-4 的 2-shot 多阶段 API pipeline | 证明 cluster-aware compression 可改善同一 LLM 的提示结果，也比较了 PLM 版和小模型 | LLM Table 5 仅为 MAVEN-ERE 随机 50 documents；小模型在 Tables 1–2 的完整 split/cross-validation，未在同表同样本重跑；不能跨表声称 LLM 超过小模型。论文、ACL 页和 arXiv 均未链接 TacoERE 官方代码。[原文](https://aclanthology.org/2024.lrec-main.1348/) |
| 跨文档事件共指（CDECR） | Min et al., *Synergetic Event Understanding*, ACL ID `2024.acl-long.164`, Tables 2、5 | GPT-4 direct zero/few-shot；GPT-4 摘要 + RoBERTa-large 协同；ECB+、GVC、FCC | 区分“LLM 直接替代”与“LLM 辅助监督模型” | GPT-4 为闭源 API；直接结构预测使用 `GPT-4-Turbo-Preview`，辅助摘要使用 `GPT-4-0613`。主表包含 singletons。[原文](https://aclanthology.org/2024.acl-long.164/) |
| GPT-4 生成事件图描述后做 CDECR | Ahmed et al., *Linear Cross-document Event Coreference Resolution with X-AMR*, ACL ID `2024.lrec-main.920`, Table 3 | GPT-4 与人工 X-AMR annotations | 说明 LLM 可作结构标注器，也暴露角色/嵌套事件缺失 | 只在 ECB+ `devsmall` 的 120 mentions 上用自定义图算法评估，不是标准 full-test 直接 LLM benchmark；本报告不把其数字与 test 结果合并。[原文](https://aclanthology.org/2024.lrec-main.920/) |

## 8. 三轴对齐的直接证据

### 8.1 MAVEN-ERE：时间、因果、子事件关系均明显落后

以下数字**可比**，均来自 Wei et al. Table 2：

- **出处与 split：**ACL ID `2024.findings-emnlp.1`，MAVEN-ERE **完整 test set（857 documents）**。提示样例来自 10 个 train documents；prompt 选择只用 10 个 validation documents。
- **评测脚本：**论文明确采用 Wang et al. (2022) 提供的 MAVEN-ERE evaluator；官方仓库 [`THU-KEG/MAVEN-ERE/evaluate.py`](https://github.com/THU-KEG/MAVEN-ERE/blob/main/evaluate.py) 以 `scikit-learn` 实现。该论文的 RoBERTa-base baseline 严格复现同一训练与评测过程。
- **指标定义：**对所有有序 event/TIMEX mention pairs 评估；时间关系包含 `BEFORE/OVERLAP/CONTAINS/SIMULTANEOUS/ENDS-ON/BEGINS-ON`，因果包含 `CAUSE/PRECONDITION`，子事件为一个正类。表中 P/R/F1 是**仅对正关系标签计算的 micro average**；`NONE` 为 label 0，明确排除在 micro 聚合之外。没有另设 negative-class F1。
- **模型可得性：**GPT-3.5 是 `gpt-3.5-turbo-16k` 闭源 API；Llama-2-7B-chat 是开放权重。Table 2 的 baseline 报 3 seeds 均值±标准差；LLM 行没有声明重复采样，视为单次 API/解码结果。

| 任务 | 模型 / prompt | P | R | micro-F1 | 结论边界 |
|---|---|---:|---:|---:|---|
| 时间关系 | GPT-3.5，10-shot iterative | 26.8 | 8.0 | 12.3 | 同一 full test、同一官方脚本 |
| 时间关系 | RoBERTa-base supervised | 57.3±0.6 | 54.5±0.1 | 55.8±0.2 | 同上；3 seeds |
| 因果关系 | GPT-3.5，10-shot iterative | 5.3 | 5.3 | 5.3 | 同一 full test、同一官方脚本 |
| 因果关系 | RoBERTa-base supervised | 34.2±0.1 | 29.3±1.0 | 31.6±0.6 | 同上；3 seeds |
| 子事件关系 | GPT-3.5，10-shot iterative | 1.7 | 2.8 | 2.1 | 同一 full test、同一官方脚本 |
| 子事件关系 | RoBERTa-base supervised | 29.5±2.5 | 25.4±2.6 | 27.2±0.9 | 同上；3 seeds |

这里不需要跨论文相减才能判断：同一论文、同一 test、同一 evaluator 中，GPT-3.5 few-shot 的三类正关系 micro-F1 都显著低于 RoBERTa-base。论文的错误分析进一步指出幻觉事件 mention、跨句长距离召回低、关系密集时性能下降，以及无法从示例学习时间传递律。

### 8.2 MAVEN-ERE：共指的 B³/CEAFe 高分不能单独解释为“接近”

以下也来自 Wei et al. Table 2，沿用上一节相同 full test 和官方 evaluator，因此**可比**。

- **指标定义：**MUC、B³、CEAFe、BLANC 均为标准 cluster-level event-coreference P/R/F1；官方脚本把未出现在系统 cluster 中的 gold event mention 补为 singleton。它们不是类别分类指标，因而没有 negative class。四个 F1 **没有再合成一个官方 CoNLL F1**，必须分别看。

| 模型 / prompt | MUC F1 | B³ F1 | CEAFe F1 | BLANC F1 | split / evaluator |
|---|---:|---:|---:|---:|---|
| GPT-3.5，whole-document one-example prompt | 23.2 | 92.5 | 90.1 | 56.9 | MAVEN-ERE full test；官方 `evaluate.py` |
| RoBERTa-base supervised | 81.7±0.7 | 98.1±0.1 | 97.8±0.1 | 89.7±0.6 | 同一 test/evaluator；3 seeds |

B³ 和 CEAFe 表面上较高，但 MUC 与 BLANC 同时暴露了严重的链接/区分失败；Llama-2 的 1/2/5-shot 更极端地得到 MUC F1 为 0，而 B³ F1 为 95.8。原因是系统大量保留 singleton 时，不同 coreference metric 的敏感性不同。故不能挑一个 B³ 或 CEAFe 数字宣布事件共指“已被拉平”。

### 8.3 CDECR：GPT-4 few-shot 只在 ECB+ 接近词面启发式，仍落后监督模型且跨语料崩溃

以下数字**可比**，来自 Min et al. Tables 2、5：

- **出处与 split：**ACL ID `2024.acl-long.164`；ECB+、GVC、FCC 的标准 **test splits**。Table 5 是 ECB+ test 的 GPT-4 zero/few-shot消融；Table 2 是三数据集 test 主结果。
- **评测脚本：**作者公开仓库 [`taolusi/SECURE`](https://github.com/taolusi/SECURE) 中的自实现 `src/models/coref_scorer.py` / `run_pairwise_classification.py`；不是数据集官方服务器。下表只比较作者在同一代码路径得到的 GPT-4、复现 baseline 与自身方法，不混入其他论文的 reported-only 行。
- **指标定义：**MUC、B³、CEAFe 为 cluster metrics；**CoNLL F1 是三者 F1 的算术平均**；主表包含 singletons，无 negative class。Table 5 只报 B³ P/R/F1。
- **模型：**direct 结构预测为闭源 `GPT-4-Turbo-Preview`，best setting 是 few-shot + mention-inclusive sentences；监督 baseline 是 RoBERTa-large。GVC/FCC 输入超过上下文/输出长度会直接截断，故这两项也测到了闭源模型的长度限制，而不只是语义能力。

| 数据集 | direct GPT-4 few-shot CoNLL F1 | reproduced RoBERTa-large baseline CoNLL F1 | 口径 |
|---|---:|---:|---|
| ECB+ | 76.8 | 85.2 | standard test；authors' scorer；含 singletons |
| GVC | 10.2 | 84.7 | 同上；长输入/输出被截断 |
| FCC | 6.1 | 71.7 | 同上；长输入/输出被截断 |

在 ECB+ Table 5 的 B³ F1 中，GPT-4 few-shot + mention-inclusive sentences 为 77.2，zero-shot 同设置为 68.3；非学习的 lemma-cluster heuristic 为 77.8，而 RoBERTa-large baseline 为 86.5。也就是说，找到的“正面”边界是 GPT-4 few-shot **接近词面启发式**，不是接近监督小模型；换到 GVC/FCC 后该现象不成立。

### 8.4 时间关系分类：LoRA 在 MATRES 接近，但 direct ICL 和监督 LoRA 均未超过 fully trained RoBERTa

Roccabruna et al. 是本轮遗漏后补入的高价值系统评测，数字口径如下：

- **任务与 split：**给定语料中已连接的两个 gold event triggers，预测一个时间关系。采用 MATRES、TIMELINE、TB-Dense 的官方 train/dev/test splits；Table 7 的 test event-pair 数分别为 724、685、789。MATRES/TIMELINE 评估 `BEFORE/AFTER/EQUAL`，TB-Dense 另含 `INCLUDES/IS_INCLUDED`；论文从三套评估数据中移除 `VAGUE`。
- **evaluator：**不是数据集官方服务器，而是作者公开仓库 `BrownFortress/LLMs-TRC` 的自实现脚本（本次核验 [commit `41eb1ed`](https://github.com/BrownFortress/LLMs-TRC/tree/41eb1ed036cd4b5741b17dc07f809311cc915016)）。`ICL_and_FT/utils/support.py` 与 `encoder_architecture/utils/support.py` 均调用 `sklearn.metrics.classification_report`；前者和后者是同一官方仓库的两条实现路径。Table 2 的 RoBERTa 是作者用同一 preprocessing/evaluation 重跑并放在同表的 supervised comparator，不是从他文抄录。
- **指标：**论文 §5.2 与 Tables 2–3 均声明 **micro-F1**。这是单标签多类分类，聚合覆盖上述全部非 `VAGUE` 时间类别；没有 `NONE`/negative 类。无法生成合法标签或 QA 回答矛盾的样例映射为 `VAGUE`，但 `VAGUE` 不在报告类别范围。
- **模型 setting：**Table 2 的 direct ICL 每类一个 demonstration，即 MATRES/TIMELINE 3-shot、TB-Dense 5-shot；从 train 随机抽五套 prompts 后平均。闭源模型为 `davinci-002` 与 `gpt-3.5-turbo-0125`。Table 2 的 Llama-2-7B/13B “fine-tuned zero-shot”是 train split 上的监督 LoRA（输入不带 demonstrations，五次训练均值），不可称为无标注 zero-shot。Table 3 则把 Llama-2/RoBERTa 放入同一判别式 encoder + classification-layer 架构，分别训练分类层（Frozen Encoder）或同时训练 encoder；Llama-2 encoder 更新使用 LoRA。
- **硬件：**RoBERTa 训练/测试使用 1×3090Ti 24GB；LLM 实验使用 4×A100 80GB，全部实验累计约一个月。闭源 ICL 走 OpenAI API，论文报告约 350 美元 API 支出。

以下为 Table 2 的**同表可比**结果；每个单元格均为对应 full test 的非 `VAGUE` 类 micro-F1：

| full-test 数据集 | 最佳 direct ICL LLM | 最佳监督 LoRA LLM | fully trained RoBERTa | 判断 |
|---|---:|---:|---:|---|
| MATRES | Llama-2-70B QA2，65.3 | Llama-2-13B QA2，84.3 | 87.6 | LoRA 已接近，但没有超过；direct ICL 仍远低 |
| TIMELINE | Llama-2-70B QA2，62.5 | Llama-2-7B QA1，76.9 | 87.9 | 两种 LLM setting 均未拉平 |
| TB-Dense | Llama-2-70B QA2，31.4 | Llama-2-13B P，55.4 | 83.1 | 类别更多时差距最大 |

Table 3 给出一个必须保留的窄正例：在 TIMELINE full test、同一 micro-F1 下，**冻结 Llama-2-70B + 训练分类层为 69.1，冻结 RoBERTa + 训练分类层为 65.7**；但 fully trained RoBERTa 为 87.9。因而可以说“大模型冻结表征在一个含大量 COVID-19 新词的语料上优于冻结小编码器表征”，不能说 direct/fine-tuned LLM 已超过监督 encoder-only 模型。该正例属于判别式特征编码器比较，不是 prompting；论文指出 train/test target sequences 中超过 30% 含 `covid-19/coronavirus/pandemic/vaccine` 等词，而 RoBERTa 预训练止于 2019，作为作者对例外的解释。

## 9. 正证据：LLM 有帮助，但证据指向“辅助组件”而非直接替代

Min et al. 同一 Table 2 提供了三轴对齐的正证据。其方法不是让 GPT-4 输出 coreference clusters，而是让闭源 `GPT-4-0613` 为每个 event mention 生成事件摘要，再把摘要与原文共同输入 RoBERTa-large 监督微调。split、作者 scorer 和 CoNLL 定义与 §8.3 完全相同。

| 数据集 | RoBERTa-large baseline CoNLL F1 | GPT-4 summaries + RoBERTa-large CoNLL F1 | 结论边界 |
|---|---:|---:|---|
| ECB+ test | 85.2 | 86.7 | 同一 test/scorer；含 singletons |
| GVC test | 84.7 | 87.4 | 同上 |
| FCC test | 71.7 | 78.7 | 同上 |

因此，LLM 对事件共指的**具体正面影响**已被三语料 test 证实：它能把分散上下文压成事件摘要，增强监督表示。但这不是 zero/few-shot LLM 超过监督模型；最终预测器仍是用任务标注微调的 RoBERTa-large，并依赖 GPT-4 闭源 API 生成摘要。

### 9.1 TacoERE：压缩提示改善同一 LLM，但没有形成“LLM 超过 RoBERTa”的合格比较

Guan et al. 包含两种不同范式，不能混称为同一个模型：

- **TacoERE (PLMs)：**K-means 文档聚类 + BERT/Transformer 学习式 cluster summarizer + RoBERTa relation predictor，以标注训练集联合训练；这是小模型组合，不含 LLM。Tables 1–2 分别评估 MAVEN-ERE / EventStoryLine 的因果关系与 MAVEN-ERE / HiEve 的子事件关系。MAVEN-ERE 为 2,913/710/857 documents 的 train/dev/test；EventStoryLine 最后 2 topics 作 dev、其余 20 topics 做 5-fold cross-validation；HiEve 为 60/20/20 documents。论文称每个训练/测试进程使用 2×RTX 3090。
- **TacoERE (LLMs)：**不做 SFT/LoRA；用闭源 `text-davinci-003`、`gpt-3.5-turbo`、`gpt-4` API 分别实现 clustering、summarization 和 pairwise relation prediction，Table 5 为 2-shot ICL。它从 MAVEN-ERE **随机抽 50 documents**，论文称得到 646 causal relations；没有声明随机种子或这些文档来自 train/dev/test 哪一部分。

Table 5 的论文内趋势是：同一 50-document sample、同一 GPT-4 API 下，直接输入 Document 得到 P/R/F1=27.1/41.5/32.8，而 TacoERE (LLMs) 得到 38.9/45.5/41.9。由于指标轴不完整，**这组数字整组标为“不可比/未能完全核实”，不作差值**；最多保留作者论文内的定性判断“compression-then-extraction 优于直接整文 prompting”，绝不能与小模型比较。原因有三：Table 5 没有 RoBERTa/BERT 行；Tables 1–2 的小模型运行在完整 split 或 5-fold CV，而非这 50 篇；论文只写“standard P/R/F1”与“overall score、不下采样 negative instances”，未声明 micro/macro、candidate-pair 构造和 negative 对聚合的精确定义。

本次核查还未在论文 PDF、ACL Anthology 页或 arXiv 条目中找到 TacoERE 官方代码链接；ACL 页也无附件代码。故 evaluator 只能标为**未声明、脚本未公开/未能核实**，Table 5 不能作为 direct LLM 或 LLM pipeline 超过 encoder-only 小模型的合格正证据。它只是“LLM 时代的输入压缩/分解可能带来收益”的论文内趋势证据。

Chen et al. AAAI-24 还报告 GPT-4 合成标注增强多种 ACE 2005 fine-tuned ED/EAE 模型，多数有提升；这支持“LLM 作标注/增广器”的方向。不过 Tables 3–4 没有完整声明 test split 与 micro/macro 聚合，本报告将其列为**支持性但不可用于严格差值**的正证据，不复述数字。

## 10. 有覆盖价值、但不满足本项目数字硬约束的结果

### 10.1 TextEE Tables 6–7：强烈负面信号，但 split/聚合未声明

TextEE 在同一框架中跨数据集评估 ED/EAE，论文结论是 LLM 明显落后。为了可追溯，下面保留原表值，但整表标记为**不可比/未能完全核实**：

| 任务与表号 | 监督行 | 最强 few-shot LLM 行 | 已核实口径 | 缺失轴，因此不得作差值 |
|---|---|---|---|---|
| ED，Table 6 | OneIE：TI 73.5、TC 69.5 | Mixtral-8x7B-Instruct，64-shot：TI 37.5、TC 14.6 | 每数据集 sampled 250 documents；TextEE evaluator；TI=trigger span exact match，TC=span+event type exact match | 样本来自哪个 train/dev/test split **未声明**；F1 micro/macro 与 negative 处理 **未声明**；跨数据集平均的权重 **未声明**。不可比 |
| EAE，Table 7 | TagPrime-CR：AI 73.3、AC 69.5、AI+ 71.9、AC+ 68.1 | Mixtral-8x7B-Instruct，32-shot：AI 35.1、AC 29.2、AI+ 32.0、AC+ 26.5 | 每数据集 sampled 250 documents；AI=argument span+event type，AC 再含 role；`+` 再要求 attached trigger offsets | split、micro/macro、negative 处理、跨数据集平均权重均未声明。不可比 |

这两表可用于回答“有没有系统评测”以及确定错误类型（false positives、span boundary、hallucination/paraphrase），但不能成为本项目将来对标数字的直接来源。

### 10.2 Chen et al. AAAI-24 Tables 1–2：直接 zero/one-shot 仍不能与引用的监督 SOTA 对齐

论文在 ACE 2005 上同时评估 GPT-4/GPT-3.5/PaLM 的 zero/one-shot ED/EAE，并使用 OmniEvent preprocessing。表中 strict ED 要求 event type 与 trigger 同时正确，loose ED 只要求 event type；EAE 在 gold event type/trigger 条件下作 span/role exact match。然而：Tables 1–2 未明确数字属于 dev 还是 test，未声明 P/R/F1 的 micro/macro与 negative-class 处理，且正文引用的监督“80%/60%”来自另两篇论文而非同一 evaluator 重跑。因此只能核实作者的定性结论“direct LLM 仍有明显差距”，不能把这些数字与监督模型相减。

## 11. 哪些被拉平，哪些没有

### 11.1 Direct zero/few-shot 未拉平；监督 LoRA 在一个语料接近；冻结表征有一个窄例外

- **ED/EAE：**覆盖面最广的 TextEE 给出强负面信号，但其 LLM 抽样表缺 split/聚合声明，严格数字结论只能写“未能完全核实”；AAAI-24 的直接评测也缺相同关键轴。没有合格证据显示直接 LLM 接近或超过监督 EE 模型。
- **时间关系：**EMNLP-24 的 MATRES/TIMELINE/TB-Dense 同表结果确认 direct ICL 全部落后 fully trained RoBERTa。监督 LoRA Llama-2-13B 在 MATRES 达 84.3、RoBERTa 为 87.6，可称“接近但未超过”；TIMELINE 与 TB-Dense 仍明显落后。唯一超过 encoder-only 行的是 Table 3 的 TIMELINE **冻结 Llama-2-70B 表征 + 分类层**相对**冻结 RoBERTa 表征 + 分类层**，但它仍远低于 fully trained RoBERTa，因此不是任务已被拉平。
- **因果/子事件关系：**MAVEN-ERE full test 同脚本结果明确落后，尤其召回极低。TacoERE 的 GPT-4 2-shot compression pipeline 虽优于同模型整文 prompting，却没有在同一 50-document sample 上重跑 RoBERTa，不能改变替代结论。
- **文档级事件共指：**MAVEN-ERE 的 B³/CEAFe 可能制造“已接近”观感，但 MUC/BLANC 否定了这一解释；跨文档 ECB+/GVC/FCC 中 direct GPT-4 均落后作者重跑的 RoBERTa-large，且在长语料上崩溃。
- **可确认的正面影响：**GPT-4 事件摘要 + 监督 RoBERTa-large 在三套 CDECR test 上均优于同口径 baseline；TacoERE 也显示 cluster-aware compression 改善同一 LLM。两者支持协同/任务分解，而非直接替代。

这里的“没有找到”只限定于本轮核验的高价值系统评测，不是声称文献宇宙中绝无某个单数据集 prompt 结果超过旧 baseline。任何此类主张仍需重新核对 split、evaluator 和标签聚合。

## 12. 未能核实

- TextEE Tables 6–7 的 250-document samples 来自五个重采样 split 中哪一个、F1 micro/macro、negative 处理和跨数据集平均权重，论文未声明；故不能据表中差距给出严格数值结论。
- Chen et al. AAAI-24 Tables 1–4 的明确 split 与 micro/macro 聚合未声明；OmniEvent 被说明用于 preprocessing/evaluation，但论文没有锁定具体 evaluator commit。数字不可与正文引用的外部监督结果比较。
- Wei et al. 的 GPT-4-1106-preview 只在 first 10 validation documents 上评测；没有 full-test GPT-4 结果，不能以这 10 篇文档替代 GPT-3.5/Llama full-test 结论。
- X-AMR 的 GPT-4 结果只覆盖 ECB+ `devsmall` 120 mentions，并经自定义 X-AMR 图聚类算法得到；没有标准 full-test direct GPT-4 数字。
- TacoERE Table 5 的 50 个 MAVEN-ERE documents 来自哪个 split、随机种子、全部 candidate-pair/negative 数、P/R/F1 的 micro/macro 聚合均未声明；没有相同样本上的小模型行。论文与官方索引未提供 TacoERE 代码，evaluator 无法核到实现或 commit。
- TacoERE 只给 `gpt-4`、`gpt-3.5-turbo`、`text-davinci-003` 名称，未声明 API snapshot/date、解码参数、调用成本或重复运行方差；Table 5 属闭源 API 单表结果。
- 本轮没有获得一个四轴齐全、显示直接 zero/few-shot LLM 超过当前监督小模型的 ED、EAE、ERE 或 ECR 结果。单数据集、reported-only 或宽松语义匹配的正面主张均未纳入。

## 13. 我在探索中发现的、与预期不符的事实

1. 事件共指上 B³/CEAFe 可以在模型几乎不建立有效链时仍显得很高；同一 Llama-2 结果甚至出现 MUC F1=0、B³ F1=95.8。只看一项 coreference F1 会得出相反结论。
2. 增加 demonstrations 并不稳定改善所有任务：Wei et al. 中 GPT-3.5 的 n-shot 增加有利于三类关系，却使 coreference 弱化；prompt supervision 不是单调收益。
3. GPT-4 direct CDECR 在 ECB+ 尚能接近 lemma heuristic，却在 GVC/FCC 因结构规模与截断骤降；“一个 benchmark 上能聚类”不能外推到跨文档事件共指已解决。
4. Llama-2-13B LoRA 在 MATRES 已逼近 RoBERTa，却不能把该现象外推到 TIMELINE/TB-Dense；即使使用 4×A100 80GB，三语料仍没有一个超过 fully trained RoBERTa。
5. 冻结 Llama-2-70B 表征确实在 TIMELINE 超过冻结 RoBERTa 表征，但一旦允许 RoBERTa encoder 监督更新，后者大幅领先。这个例外说明“大模型表征包含较新知识”，不等于“生成式 LLM 解决了 TRC”。
6. TacoERE Table 5 的 GPT-4 F1 表面高于其 Table 1 的 RoBERTa F1，但前者是随机 50 documents，后者是完整 test，且聚合/evaluator 未公开；这是一个不能进行跨表相减的典型陷阱。
7. 本轮最清晰的 LLM 正收益不是纯 prompting，而是信息压缩：GPT-4 摘要可辅助监督 RoBERTa，cluster-aware summaries 也可改善同一个 GPT-4 pipeline。LLM 的价值与任务专用小模型并非二选一。
8. 两篇看似系统的 EE 论文仍没有把 LLM 表的 split 与聚合方式写全；“论文同表并排”本身不足以满足本项目的公开可比标尺。

### 本块结论

- **已核实：**存在覆盖 ED/EAE 的 TextEE 与 AAAI-24 系统评测，覆盖 coreference/temporal/causal/subevent 的 MAVEN-ERE 系统评测，覆盖 MATRES/TIMELINE/TB-Dense 的 ICL/LoRA/encoder-feature TRC 评测，以及覆盖三套 CDECR 语料的 GPT-4 direct/hybrid 评测。（ACL IDs `2024.findings-acl.760`、`2024.findings-emnlp.1`、`2024.emnlp-main.1136`、`2024.lrec-main.1348`、`2024.acl-long.164`；DOI `10.1609/aaai.v38i16.29730`）
- **已核实：**在 MAVEN-ERE full test、官方正类 micro-F1 下，GPT-3.5 10-shot 的时间、因果、子事件关系均明显落后同表 RoBERTa-base；共指的 MUC/BLANC 也显示明显差距。跨文档共指中，direct GPT-4 在 ECB+/GVC/FCC test 均落后同代码重跑的 RoBERTa-large。（Wei et al. Table 2；Min et al. Table 2）
- **已核实：**TRC 的 direct ICL 与监督 LoRA 在三套 full test 上均未超过 fully trained RoBERTa；但 Llama-2-13B LoRA 在 MATRES 已接近。Table 3 还有一个严格限定的正例：冻结 Llama-2-70B 表征在 TIMELINE 优于冻结 RoBERTa 表征，仍不敌 fully trained RoBERTa。（Roccabruna et al. Tables 2–3）
- **已核实：**正面影响存在，最强合格证据是协同：GPT-4 生成事件摘要后辅助 RoBERTa-large，在 ECB+、GVC、FCC 同口径 test 上均改善 CoNLL F1。TacoERE Table 5 只提供压缩提示优于同一闭源 LLM 整文提示的论文内趋势，因指标/抽样/代码轴不全标为不可比；两者都不是 zero/few-shot LLM 超过监督模型。（Min et al. Table 2；Guan et al. Table 5）
- **未能核实：**没有取得四轴齐全、证明 direct zero/few-shot LLM 已接近或超过当前 fully trained 小模型的事件子任务；TextEE 与 AAAI-24 的 EE 数字因 split/聚合声明不全只能视为不可比趋势证据，TacoERE 因抽样、指标与代码缺口也不能与 RoBERTa 跨表比较，GPT-4 的 MAVEN-ERE full-test 结果不存在。
- **对论文选题的含义：**现有一手证据不支持把事件抽取、事件关系或事件共指视作已被通用 LLM 拉平；同时也不支持因此排除 LLM。可核实的冲击是 LLM 改变了信息压缩、标注增广与模型协同方式，而公开主指标仍需要任务专用训练和严格 evaluator。

# A2b 阶段报告：LLM 时代的新事件图任务是否可比

> 调研日期：2026-08-25
>
> 判定口径：“形成 benchmark”要求任务定义、可取得的标注 test 和可执行或至少充分声明的 evaluator；仅有论文自造问题、通用 QA/memory benchmark、私有语料或系统演示不计作**事件专门 benchmark**。“已发表方法”只计正式会议/期刊论文，arXiv-only 工作单列。本文不复述任何模型性能数字，避免在 split、evaluator 或指标聚合不全时制造不可比差值。

## 14. 五类任务的总判定

| 新任务形态 | event-specific 公开 benchmark + 已发表方法？ | 已发表的 event-specific 方法数最低可证下界 | 核心证据与边界 |
|---|---|---:|---|
| 事件图谱作为 LLM/agent 外部记忆 | **未核实成立** | 0 | LoCoMo 是公开长期对话记忆 benchmark，但 temporal event graph 用于生成/约束对话，不是参赛系统必须读写的外部记忆。AriGraph 已发表且使用 graph episodic memory，但图与 TextWorld/QA benchmark 都不是事件专门任务；Zep 是 temporal-KG memory 的 arXiv 方法，同样没有事件专门 benchmark。 |
| GraphRAG 的事件化/时间化变体 | **方法存在，事件专门 benchmark 不存在** | ≥1 | ACL 2025 EventRAG 是明确的 event-knowledge-graph RAG 方法；它在通用 MultiHop-RAG 的作者截取子集和论文自生成问题上评测。不能把 MultiHop-RAG 改名为 event-graph benchmark。 |
| 事件图用于长文档/多文档理解或时间线构建 | **仅部分满足，严格口径下未形成完整公开 benchmark** | ≥1 | NAACL 2025 CALLMSAE/NYT-SEG 是最接近的长文档显著事件图生成设置；EventRAG 覆盖多文档理解。但 NYT-SEG 的原始 train 文本受许可限制、官方仓库缺 HGS evaluator，当前 test 文件与论文许可声明又有矛盾；EventRAG 的问题集不是公开固定 event benchmark。 |
| 事件图作为可验证推理支架 | **事件专门任务与 gold graph 已存在；完整公开复现包仍不闭合** | ≥3（跨不同任务，不可直接比较） | EMNLP 2024 CGEP 用 gold event-causality graph 预测后继事件；*SEM 2025 TAG-EQA 用 TORQUESTRA 人标 event graph 回答事件问题；ACL 2025 CGEL 用 causal graph 生成似然解释。前两者只监督最终事件/答案，没有 gold proof trace；三者也没有共同数据或 evaluator。 |
| LLM/多智能体自动构建事件/因果图 | **已发表方法存在；没有统一的完整公开 benchmark** | ≥2 | CALLMSAE 是级联 LLM 显著事件图生成；CGEL 论文中的多专家协作模块生成 causal graph。两者对象、数据和 evaluator 不同，不能互为同一 benchmark 上的公开对手。 |

定向补核后，原先笼统的“没有 event-specific benchmark”必须收窄：**CGEP 与 TORQUESTRA/TAG-EQA 已构成事件图输入的固定下游任务证据**。但若“完整公开 benchmark”同时要求可下载的派生 split、gold、可执行 evaluator 和论文方法，五类仍没有一个无保留满足：CGEP 仓库缺 CGEP-MAVEN 派生数据且默认 loader 指向缺失文件，TAG-EQA 仓库未提交其派生 TORQUESTRA 输入，NYT-SEG 又缺 HGS evaluator。故正确结论是“任务和方法已经出现，完整复现包没有闭合”，而不是“事件图 benchmark 完全不存在”。

## 15. 已核实的直接候选

### 15.1 EventRAG：已发表的事件化 GraphRAG 方法，不是新的事件 benchmark

- **身份与任务。** EventRAG 是 ACL 2025 main 正式论文的方法：从多文档语料抽取事件、参与实体以及时间/逻辑关系，构建 EKG，再由 agent 迭代扩展知识和执行 multi-event reasoning。它属于 event-specific GraphRAG 方法，不是数据集或 benchmark。（ACL ID `2025.acl-long.830`，DOI `10.18653/v1/2025.acl-long.830`）
- **数据/test。** 生成实验用 UltraDomain 的三个语料和 bioprotocol，并由论文使用 LLM 为每个语料生成问题；没有固定的人工 event-graph test labels。推理实验使用公开 MultiHop-RAG，但 Appendix A.1.2 明确只取数据集开头一段问题作为 evaluation set，而非官方 split；MultiHop-RAG 本身是通用多跳 RAG benchmark。
- **评测口径。** 论文 §3.1/Figure 2 用 LLM pairwise judge 比较 Comprehensiveness、Diversity、Empowerment、Logic、Directness 和 Overall Winner；问题与 judge prompt 均由本论文设置。§3.2/Table 1 用 RAGAS 的 Answer Relevancy、Answer Correctness、Semantic Similarity；Appendix A.4 给出指标定义，但论文未锁定 RAGAS 版本、judge/embedding 的全部 evaluator 配置和评测随机性。因此这里不报告分数。
- **公开对手下界。** Table 1 同表重跑 NaiveRAG、Microsoft GraphRAG、LightRAG；这些是通用 RAG 方法，不是三个 event-specific 方法。正式发表的 event-specific 方法最低下界仍为 **1（EventRAG 本身）**。
- **代码状态。** 官方仓库 [Ryaang/EventRAG](https://github.com/Ryaang/EventRAG) 可取得方法核心、Neo4j/Milvus 配置和 `reproduce/Step_0.py`–`Step_4.py`（本次核查 commit `96a9de960bf4939c7b2d6e7350c5bbc95232517e`）。但脚本引用仓库外不存在的 `../RAG-Data/...`，仓库没有论文问题、输出或 RAGAS evaluator；且核心流程依赖闭源 `gpt-4o-2024-08-06` API。故是“方法代码公开”，不是“论文 benchmark 一键可复现”。

**判定：**EventRAG 证明“事件化 GraphRAG 已有正式方法”，但其评测资源不能被当成 event-specific public benchmark，也不能据通用 RAG 对手声称已有多个事件图方法可公开比较。

### 15.2 CALLMSAE 与 NYT-SEG：方法、数据集和 benchmark 候选必须分开说

- **CALLMSAE 是方法。** 它是 NAACL 2025 long 正式论文中的 cascading/sequential LLM pipeline：摘要得到显著事件，依次生成 hierarchical、temporal、causal graph，再用 hallucination grader 迭代修正；不是多智能体讨论系统，也不是 benchmark 名称。（ACL ID `2025.naacl-long.112`，DOI `10.18653/v1/2025.naacl-long.112`）
- **NYT-SEG 是数据集/benchmark 候选。** 训练部分是 CALLMSAE 从 Licensed Annotated NYT corpus 自动生成的 distant graphs；test 是人工标注的显著事件及 `is_subevent_of`、`happened_before`、`caused_by` 边。论文 §4 明确 train/test 构造；§5.3/Table 5 在人工 test 上比较方法。
- **test 与许可。** 官方仓库 [Xingwei-Tan/CALLMSAE](https://github.com/Xingwei-Tan/CALLMSAE) 的 `data/human_annotated_graphs.json` 当前可下载，包含 `document` 与 `target`；`data/nyt_seg_train.json` 仅含自动生成的 `relations`，README 仍要求用户另行准备 `NYT_annotated` 原语料。本次核查 commit 为 `4a0f093ecedfdb136a12c82a82a534084f662fca`。论文 Appendix A.7 却写明 NYT 许可不允许发布 original text、只发布 graph；这与当前 human-test JSON 中出现 `document` 字段不一致。报告只能记录现状，不能代替数据许可判断。
- **评测口径。** Table 5 的主指标是 Hungarian Graph Similarity：SFR-Embedding-Mistral 编码事件，只在相同关系类型内用 Hungarian assignment 对齐预测/目标边；`PHGS` 以预测边为分母，`RHGS` 以目标边为分母，`HGS` 按文档 gold-edge 数加权。split 是论文人工标注 test。官方仓库未包含 Hungarian matching/SFR evaluator 实现，故实现版本与精确脚本未能核实，本报告不复述分数。
- **公开对手下界。** Table 5 同一 test 中有 Han et al. (2019)、CAEVO、Madaan et al. (2021)、Tan et al. (2024)、CALLMSAE 等已发表命名系统，故“被作者适配并重跑的已发表系统”最低下界为 **≥5（含 CALLMSAE）**；但为 NYT-SEG/显著多关系图专门设计并正式发表的方法，最低下界只能确认 **≥1（CALLMSAE）**。尚未核实独立论文在同一公开 evaluator 上复现或改进 NYT-SEG。
- **代码状态。** 仓库提供生成 prompt、人工 test graph 和 distant train graph；没有 HGS evaluator、固定环境/完整结果包，fine-tuning 代码另指向另一仓库，完整 train 文本又需要 NYT 许可。因此它比系统 demo 更接近 benchmark，但不是无保留的端到端公开 benchmark。

**判定：**`CALLMSAE = 方法`，`NYT-SEG = 数据集兼 benchmark 候选`。若“public”只要求当前可下载的人工 test labels，它部分满足；若还要求许可清晰、完整 train 输入和官方 evaluator，它不满足。本轮证据不足以说它能稳定支撑“超过多个为该任务设计的方法”；只能说论文作者已把多个旧系统适配到同一 test。

### 15.3 CGEL：多专家 causal-graph 方法与 EEL 新任务，不是成熟 benchmark

- **身份与任务。** ACL 2025 论文先让 temporal、discourse、precondition、commonsense experts 多轮协作并由 causality judge 汇总 causal graph，再提出 Explainable Event Likelihood（EEL）：输入新闻与未明说的 query event，预测其可能/不可能，并输出因果解释链。`CGEL` 指 Causal Graph-based Event Likelihood 方法；既不是数据集名，也不是 benchmark 名。（ACL ID `2025.acl-long.1269`，DOI `10.18653/v1/2025.acl-long.1269`）
- **intrinsic graph 数据与口径。** §3.1 把 CRAB 的新闻事件对按文章组成图，以原 causality score 阈值化并把 causal pair 的反向加入 non-causal；论文未声明 train/dev/test split。Table 1 报 graph-level 与 pair-level Balanced Accuracy、causal/non-causal class F1、Macro-F1；graph-level 是逐图计算后平均，pair-level 汇总所有 pairs。作者明确称 causal graph generation 是 novel task，表中 Direct、Pairwise、Experts/Collab 是本论文设计的 prompt variants，不是多个既有任务方法；专门已发表方法下界为 **1**。evaluator 代码因官方仓库不可得而未能核实，故不报告分数。
- **EEL test 与口径。** §4.2/Appendix B.2 从 Annotated NYT 整理一个论文内 test，没有 train/dev；Appendix B.3 明说不存在 gold explanation-chain dataset。Table 4 用 GPT-4 对 Causality、Informativeness、Coherence 作 pairwise winner/tie 判断，人工只核验一个子集；这是一种论文评估设置，不是带 gold chain 的公开 benchmark。Table 5 的 ForecastQA 和 Table 6 的 narrative cloze 是既有下游 benchmark，但任务分别是 forecasting/next-event prediction，并不因 CGEL 使用 causal graph 就变成“事件图验证支架 benchmark”。
- **模型与代码状态。** graph builder 使用 GPT-4o 与 Llama-70B-instruct；EEL/CGEL 实验使用 API-based GPT-4。论文脚注给出 `https://github.com/StonyBrookNLP/causal-graphs`，但 2026-08-25 以 `git ls-remote` 核查返回 `Repository not found`。EEL 数据、prompt/evaluator 的可执行发布因此未能核实。

**判定：**CGEL 是“自动 causal graph + 图支撑事件推理”的正式方法正证据；EEL 是新任务/论文内 test，而不是已形成多方法竞争的公共 benchmark。它不能支撑超过多个同任务已发表方法。

### 15.4 CGEP / SeDGPL：不能遗漏的事件因果图后继事件预测任务

- **节点与任务。** Zhan et al. 将 Causality Graph Event Prediction（CGEP）定义为：输入文档内过去事件组成的有向 event causality graph、anchor event 与候选后继事件集合，选择 gold consequential event。节点包含 event mention 及其原句，边是有方向的 `cause`；这是 occurrence/event mention 级事件图，不是变量 DAG 或一般 KG。（ACL ID `2024.findings-emnlp.45`，arXiv `2409.17480`）
- **gold 监督对象。** CGEP-MAVEN 与 CGEP-ESC 从 MAVEN-ERE、EventStoryLine Corpus 的人工事件及因果关系标注构图，遮蔽 tail event 得到 gold answer，再从其他图采负例形成候选集。因此 gold 同时包含**输入图结构和最终后继事件**；任务不要求输出图，也没有 gold reasoning/proof chain。它是 graph-conditioned event ranking benchmark，而不是建图 benchmark。
- **split。** 论文 §5.1 对 CGEP-ESC 固定最后两个 topics 为 dev，并在其余 topics 上作 5-fold cross-validation、报告 fold average；CGEP-MAVEN 因原 test 不公开，改用 MAVEN-ERE 原 dev 作为 test，并从原 train 抽取 20% 作 dev。Table 2 的 CGEP-MAVEN/CGEP-ESC 结果对应这两个口径，二者不能与其他 MAVEN-ERE test 数字混用。
- **指标/evaluator。** Table 2 主指标为 MRR 与 Hit@k。Appendix B 定义：每实例按候选事件分数排序，MRR 是 gold rank 倒数的实例平均，Hit@k 是 gold 是否进入 top-k 的实例平均；官方 `tools.py::calculate` 实现同一口径。本文不复述 Table 2 分数。代码对并列分数使用排序后第一次出现的位置，属于实现细节，比较时需锁定该 scorer。
- **对手下界。** Table 2 在同一派生数据和指标下重跑 CSProm-KG、SimKG、BARTbase、MCPredictor 与 SeDGPL，故“作者适配到 CGEP 的已发表命名方法”最低下界为 **≥5（含 SeDGPL）**；Llama/GPT 行是模型基线，不另计为任务方法。只有 SeDGPL 是为 CGEP 专门提出的方法，独立 follow-up 仍未核实。
- **代码和数据状态。** 官方 [zhanchuanhong/SeDGPL](https://github.com/zhanchuanhong/SeDGPL)（本次核查 commit `265b19b69856428a63819c809572865b5faebf3f`）公开模型、训练循环、MRR/Hit scorer 及一个完整的 `ESCSubWoRe.npy` 派生图文件；但没有 README/环境锁，默认 `load_data.py` 硬编码读取仓库中不存在的 `data/MAVENSubWoRe.npy`，也没有数据构造脚本或可直接运行的 ESC fold 入口。因此 source corpora、CGEP-ESC 派生图和 evaluator 可取得，CGEP-MAVEN 的精确负采样实例与端到端运行仍未闭合。

**判定：**CGEP 是 2024 年正式发表、具有固定任务、公开来源 event-causality graph、同表多个适配对手和明确 ranking evaluator 的 benchmark 级任务；它属于 A2b 第四类“事件图作为推理输入”的直接证据，也可作为事件预测公开主指标任务。它不是 LLM 专属任务，主方法 SeDGPL 是 RoBERTa-based PLM，并且只验证最终后继事件而非推理链。它迫使本报告撤回“公开事件图推理任务不存在”的宽泛说法，但由于 CGEP-MAVEN 派生数据和仓库入口不完整，尚不能把它写成无条件的一键公开 benchmark package。

### 15.5 TAG-EQA / TORQUESTRA：gold 事件因果图上的 QA，但只验证最终答案

- **身份。** TAG-EQA 是 *SEM 2025 正式论文提出的 prompting/evaluation framework，不是新数据集名：它把 TORQUESTRA 的 causal graph verbalize 后，以 Text、Graph 或 Text+Graph 输入 LLM，并组合 zero-shot、few-shot、CoT。底层 benchmark/data 是 TORQUESTRA。（ACL ID `2025.starsem-1.24`）
- **节点本体。** 论文 §3.1 明确图可以是 instance graph 或 schema graph，节点是叙事事件/事件模式，边是 `ENABLES` 或 `BLOCKS`；样例还含 `Entity::...` 辅助节点。它是 event-specific causal graph，不是变量级 Bayesian network，也不是一般实体 KG，但不能全部称为 occurrence-level。
- **gold/test 监督对象。** §3.2 使用人类修订的 `TORQUESTRAhuman`，其 causal graphs 是 gold；论文把原 QA 转为 binary yes/no，并定义过滤后的 Full test 与成本受限 Small subset。模型拿到 passage、gold graph 或两者，gold 输出只有最终 yes/no；CoT trace 是提示构造内容，不是人工 proof annotation。因此它能评“gold event graph 是否帮助最终 QA”，不能评自动建图，也不能验证生成推理链是否忠于图。
- **指标/evaluator。** §4、Tables 2–5 的主指标是 binary classification accuracy，即正确 yes/no 占全部问题的比例；CoT 由正则抽取 `final answer`，缺失时退回第一个独立 yes/no。官方 `yes_no_*_prompt.py` 含这一 scorer，Tables 2–5 分别锁定 Full/Small 与模型/API 成本口径。本报告不复述任何分数，也不跨 Full 与 Small 比较。
- **方法与对手下界。** TAG-EQA 本身是一个正式发表方法框架，最低下界 **≥1**；同论文的九种配置是同一框架的 prompt variants，T5/Qwen/GPT 是模型行，不是多个独立 event-graph QA 方法。原 TORQUESTRA 是数据资源，不应计作另一方法。
- **代码/数据状态。** 官方 [MaithiliKadam4/TAG-EQA](https://github.com/MaithiliKadam4/TAG-EQA)（本次核查 commit `fa3b0b9ae8211da07e14ae344b0471d741c4feee`）公开 prompt builder、模型调用和 accuracy evaluator；但 `data/.gitignore` 排除全部数据，代码所需 `data/main_train_data_only.jsonl`、派生 prompts、Full/Small IDs 与论文 outputs 均未提交。故论文声称的“code and data available”在当前 commit 只能核到代码，不能核到固定派生 test。

**判定：**TAG-EQA 是 A2b 第四类的直接正证据，并证明 gold event graph 上的 LLM QA 已有正式评测方法；但 benchmark 名应写 TORQUESTRA/TAG-EQA setting，而不是把 TAG-EQA 当数据集。它同样把“完全没有 event-graph reasoning benchmark”的结论改为错误；不过当前官方发布缺派生数据，且 gold 只监督最终答案，所以不改变“没有完整公开、可验证 proof-trace benchmark”的严格结论。

## 16. 相邻工作为何不能冒充事件图 benchmark

| 相邻候选 | 已核实的公开性/发表状态 | 排除或降级理由 |
|---|---|---|
| LoCoMo | ACL 2024 正式论文；长期对话、QA、event summarization 数据/benchmark 公开（ACL ID `2024.acl-long.747`） | temporal event graph 是合成与人工编辑对话的结构支架，benchmark 没有要求参赛方法构建/查询事件图。它能评“长期记忆”，不能证明“事件图外部记忆”已有 benchmark。 |
| AriGraph | IJCAI 2025 正式论文；官方代码公开 | graph world model 融合 semantic/episodic memory，评测 TextWorld 与静态多跳 QA；节点/任务不是事件专门标注，不能计入 event-graph benchmark。 |
| Zep / Graphiti | arXiv `2501.13956` 与公开项目；在 DMR、LongMemEval 上评测 | temporal KG agent memory 方法存在，但截至本轮只核实 arXiv 状态；benchmark 是通用 agent memory，不要求 event graph。 |
| EventRAG 使用的 MultiHop-RAG | 数据与 QA ground truth 公开 | 通用 multi-hop RAG；EventRAG 只取论文自定子集。event/temporal query 类型不等于图结构有 gold 标注，也不等于 event graph construction benchmark。 |
| CGEL 使用的 ForecastQA / narrative cloze | 既有公开任务，论文给出下游结果 | gold 是答案/next event，不是 causal graph 或 proof graph。能做下游效用测试，不能直接比较图本身的正确性和可验证性。 |
| CausalGraphBench | ACL SRW 2025 正式 benchmark；官方 GitLab 提供 gold DAG JSON、论文 outputs、`evaluate_utils.py`（ACL ID `2025.acl-srw.16`） | 节点是 Bayesian-network **named variables**，任务是从变量名/metadata 恢复全部有向边。gold 监督变量 DAG 结构，主指标为 Table 2 的 edge-normalized SHD；不是文本事件、event occurrence 或事件图。 |
| CausalGraph2LLM | Findings of NAACL 2025 正式 benchmark；官方 GitHub 提供 synthetic/BNLearn 图生成下载与 query evaluator（ACL ID `2025.findings-naacl.110`） | 节点同样是 causal variables；gold 监督 source/sink/parent/child/mediator/confounder 等图查询的变量集合，或 intervention 最终答案。它是变量 DAG encoding/reasoning benchmark，不是 event graph reasoning。 |

**CausalGraphBench 的完整判定。** 它确实是 benchmark 兼统一评测框架，不是单一方法：公开集合中的每个条目包含变量名、metadata 和 gold Bayesian-network structure，受测系统从变量语义恢复边。论文没有常规 train/dev/test；所有 gold graphs 都随 benchmark 暴露，Table 2 在按图规模限定的集合上评测，fine-tune variant 才对“除当前目标图之外的 graphs”作 80/20 train/validation。主指标是 edge-normalized Structural Hamming Distance：把预测图变成 gold 图所需的加边、删边、反向操作数除以 gold edge 数，越低越好；Table 3 另给 FP/edge 与 FN/edge。官方仓库 [causal-graph-bench](https://gitlab.nl4xai.eu/nikolay.babakov/causal-graph-bench)（核查 commit `d4d6c45dc2cbf1b143e646e073b2ab5dc216dc60`）提供全部 benchmark JSON、论文输出、notebook 与基于 Causal Discovery Toolbox 的 scorer。因此它是“完整公开 benchmark”的正例，却由于节点是变量而不属于 A2b 五类中的事件图任务。

**CausalGraph2LLM 的完整判定。** 它也是 benchmark/evaluation framework，而非 causal graph construction 方法。数据由 synthetic DAG 与 BNLearn 的 Alarm/Insurance 变量图组成；代码从已知 gold DAG 自动生成 graph-level 和 node-level queries，没有自然语言事件 mention，也没有常规 held-out test split。Figure 4/Appendix Table 2 的 graph-level 主指标是集合答案的 F1（预测/真值节点集合得到 precision、recall、F1）；§3.3.1 的 intervention downstream task 用最终答案 accuracy。官方 [ivaxi0s/CausalGraph2LLM](https://github.com/ivaxi0s/CausalGraph2LLM)（核查 commit `30dd4907156bba2a3179f5fcb987fec7fa81da3b`）提供图生成、BNLearn 下载、query prompt 与 set-based evaluator。它能证明“变量 causal graph 的公开 LLM benchmark 已形成”，不能证明事件图 benchmark 已形成。

边界结论有两面：**方法内部使用事件图，不足以把原 benchmark 重新分类为事件图 benchmark；论文标题含 `CausalGraph` 也不足以把变量 DAG 纳入事件图。** 必须看节点是否为事件，以及 gold/test 究竟监督图结构、图上查询、还是只监督最终答案。CGEP 和 TAG-EQA 通过了“节点是事件、图是模型输入”这一步；CausalGraphBench 与 CausalGraph2LLM 没有。

## 17. 未能核实

- 未找到一个正式发表、event-specific 的 agent-memory benchmark，要求模型显式维护 occurrence-level event graph，并对写入、更新、冲突处理、时间查询分别提供公开 gold/test。
- 未找到一个公开 event-specific GraphRAG benchmark，带固定多文档语料、固定问题、event/temporal gold 与官方 evaluator；EventRAG 的公开代码不包含其完整评测包。
- 未核实 NYT-SEG 人工 test 文本当前发布是否符合 Annotated NYT 的再分发许可；论文 Appendix A.7 与仓库文件内容不一致。也未找到官方 HGS evaluator，因此不把 Table 5 分数当作可直接复用基线。
- 未核实有独立后续论文在 NYT-SEG 同一 test 和同一 HGS 实现上重跑；Table 5 的多系统比较目前只证明原论文作者做过适配实验。
- CGEL 官方代码链接当前不可访问；CRAB graph transformation 的明确 split、EEL 完整 test、GPT-4 judge 实现和模型 snapshot 均未能从可执行发布中核实。
- CGEP 官方仓库没有 CGEP-MAVEN 的 `MAVENSubWoRe.npy`、数据构造脚本或 README，默认 loader 因缺文件不能直接运行；已公开的 CGEP-ESC 派生图也没有与论文 5-fold protocol 对接的入口。精确 candidate sampling 与 MAVEN Table 2 的端到端复现因此未能核实。
- TAG-EQA 官方仓库未提交 `main_train_data_only.jsonl`、Full/Small IDs、派生 prompts 或论文 outputs；无法仅凭当前 commit 重建论文的固定 TORQUESTRA test。论文宣称“code and data available”，但本轮只核到代码与 scorer。
- 本轮未将 T-GRAG、DyG-RAG、TG-RAG、STAR-RAG 等 temporal GraphRAG arXiv-only 工作计作“已发表方法”；也未核实它们是否后来正式录用。即使录用，temporal KG/RAG 仍需逐篇证明 event nodes 与 event-specific gold，不能按名称自动纳入。
- 未找到“可验证 reasoning scaffold”的公共 gold proof graph：CGEP 只评后继事件 rank，TAG-EQA/EventRAG 只评最终答案，CGEL 评最终解释偏好，CALLMSAE 评图边相似度；这些 evaluator 不能互换，也没有一个监督模型生成的 proof trace 是否忠于图。

## 18. 我在探索中发现的、与预期不符的事实

1. CGEP 早在 EMNLP 2024 Findings 就把 occurrence-level event causality graph 变成固定的后继事件 ranking task；此前把 NYT-SEG 写成“最接近 benchmark 的唯一候选”是遗漏。CGEP 还有同表适配对手和确定性 scorer，只是发布包没有闭合。
2. TAG-EQA 的输入确实是 TORQUESTRA 人标 event graph，而不是论文临时生成的结构；它因此是 graph-supported event QA 的直接证据。但 gold 只判断最终 yes/no，没有验证 CoT 是否沿图推理。
3. 两篇名称最像事件图 benchmark 的 CausalGraphBench/CausalGraph2LLM，反而都是变量级 Bayesian/causal DAG；它们的数据和 evaluator 比多数事件图工作更完整，却不能因名称相似被纳入事件图。
4. EventRAG 已在 ACL 正式发表，却仍使用通用 MultiHop-RAG 的论文自定子集和自生成问题；“ACL 方法 + GitHub 仓库”不自动意味着新任务已有公开 benchmark。
5. CGEL 的 causal graph 可以改善既有下游任务，但新 EEL 没有 gold explanation chains，完整评估依赖 GPT-4 judge；“可解释”不等于“已有可验证的 proof benchmark”。
6. CALLMSAE 与 CGEL 合计至少给出两个正式发表的 LLM 自动建图方法，但两者没有共同数据、schema 或 evaluator；方法数量不能直接转化为公开竞争密度。
7. LoCoMo 确实包含 temporal event graphs，却把它们用于数据生成而非受测系统的显式记忆。只按摘要关键词检索会把 benchmark 的内部制作工具误认成任务对象。
8. “系统先出现、benchmark 后补”只适用于 event memory、eventized GraphRAG 与自动建图；graph-conditioned event reasoning 已有 CGEP/TORQUESTRA 两个数据传统，但它们的当前派生发布仍弱于变量 causal-graph benchmarks。

## 19. 对选题含义

- “事件图 benchmark”至少要分成三种 gold：NYT-SEG 监督输出图，CGEP 监督给定 gold 图后的后继事件，TAG-EQA 监督给定 gold 图后的最终 QA。三者回答的问题不同，不能合成同一榜单；其中后两者也没有 gold proof trace。
- CGEP 是本轮最明确的公开主任务形态：事件节点、固定 graph-conditioned ranking、Table 2 同口径适配对手、MRR/Hit scorer 均已定义。其“多个方法”证据是原论文统一改造并重跑，不是多个独立 CGEP follow-up；仓库缺失 MAVEN 派生数据又限制了复用确定性。
- TAG-EQA 证明 gold causal event graph 能作为 LLM QA 输入，但论文将其明确称作 clean-graph upper bound；它没有回答自动构图误差下是否仍有效，也没有把 reasoning trace 变成可检验 gold。
- EventRAG 与 CGEL 仍是“显式事件结构有用途”的存在性证据：前者用于跨文档检索/推理，后者用于因果解释与下游预测；它们自身没有提供成熟公共 benchmark。
- CausalGraphBench 与 CausalGraph2LLM 说明公开 benchmark/evaluator 的工程形态已经可行，但其变量 DAG 本体与事件 occurrence/schema 不同，只能作为邻近评测设计参照，不能填入 event-specific 竞争密度。
- general KG、temporal KG、GraphRAG、agent memory 的结果仍只能作为邻近证据。节点不是事件、test 不提供 event graph/graph-conditioned event query，任何一项成立都不能据名称纳入。

### 本块结论

- **已核实：**EventRAG、CALLMSAE、CGEL、SeDGPL/CGEP、TAG-EQA 分别覆盖 eventized GraphRAG、显著事件图生成、多专家 causal graph、event-graph-conditioned prediction、gold-event-graph QA。（ACL IDs `2025.acl-long.830`、`2025.naacl-long.112`、`2025.acl-long.1269`、`2024.findings-emnlp.45`、`2025.starsem-1.24`）
- **关键更正：**“没有 event-specific public benchmark”过强。CGEP 已定义公开来源事件因果图上的固定后继事件 ranking task，并在 Table 2 用统一 MRR/Hit evaluator 适配多个已发表系统；TORQUESTRA/TAG-EQA 也提供 gold event graph 上的固定 QA setting。
- **严格边界：**CGEP 与 TAG-EQA 都只监督最终后继事件/yes-no answer，不监督 proof trace；前者官方仓库缺 CGEP-MAVEN 派生数据和可直接运行入口，后者官方仓库缺派生 TORQUESTRA test。因此它们改变“任务不存在”的结论，但未推翻“没有无保留完整公开复现包”的结论。
- **已核实的邻近排除：**CausalGraphBench 与 CausalGraph2LLM 都是正式、公开且带 evaluator 的 benchmark，但节点是 named causal variables，gold 分别是变量 DAG 结构和变量图查询答案；它们不属于 event-specific 五类。
- **仍成立的负结论：**事件图外部记忆与 event-specific GraphRAG 仍未找到专门公共 benchmark；自动构图方向的 NYT-SEG/CGEL 仍有许可、数据或 evaluator 缺口；可验证推理方向仍没有 gold proof trace。
- **不能支撑的主张：**当前证据不能支撑“事件图外部记忆已有公开专门榜单”，不能支撑“CGEL/EEL 已有多个公开可比方法”，也不能把 CGEP 原论文内适配对手写成多个独立 follow-up，或把 TAG-EQA 的 gold-graph upper bound 外推到自动构图场景。

## 20. A2b 来源与复核入口

| 候选 | 一手论文标识 | 官方代码/数据 | 本轮核验位置 |
|---|---|---|---|
| EventRAG | [ACL Anthology `2025.acl-long.830`](https://aclanthology.org/2025.acl-long.830/)，DOI `10.18653/v1/2025.acl-long.830` | [Ryaang/EventRAG](https://github.com/Ryaang/EventRAG) | 论文 §§3.1–3.3、Appendix A.1–A.4、Table 1/Figure 2；仓库 reproduce scripts 与数据路径 |
| CALLMSAE / NYT-SEG | [ACL Anthology `2025.naacl-long.112`](https://aclanthology.org/2025.naacl-long.112/)，DOI `10.18653/v1/2025.naacl-long.112`，arXiv `2406.18449` | [Xingwei-Tan/CALLMSAE](https://github.com/Xingwei-Tan/CALLMSAE) | 论文 §§3.5、4、5.3、Appendix A.7、Table 5；仓库 README 与两个 data JSON |
| CGEL / EEL | [ACL Anthology `2025.acl-long.1269`](https://aclanthology.org/2025.acl-long.1269/)，DOI `10.18653/v1/2025.acl-long.1269`，arXiv `2506.06910` | 论文所列 [StonyBrookNLP/causal-graphs](https://github.com/StonyBrookNLP/causal-graphs)（核验日不可访问） | 论文 §§3.1–3.3、4.1–4.3、Appendices B–C、Tables 1/4–6 |
| CGEP / SeDGPL | [ACL Anthology `2024.findings-emnlp.45`](https://aclanthology.org/2024.findings-emnlp.45/)，DOI `10.18653/v1/2024.findings-emnlp.45`，arXiv `2409.17480` | [zhanchuanhong/SeDGPL](https://github.com/zhanchuanhong/SeDGPL) | 论文 §§3.1–3.2、5.1–5.3、Appendices A–B、Tables 1–2；仓库 ESC data、loader 与 `tools.py::calculate` |
| TAG-EQA / TORQUESTRA | [ACL Anthology `2025.starsem-1.24`](https://aclanthology.org/2025.starsem-1.24/)，DOI `10.18653/v1/2025.starsem-1.24` | [MaithiliKadam4/TAG-EQA](https://github.com/MaithiliKadam4/TAG-EQA) | 论文 §§3.1–4、Tables 2–5、§7；仓库 prompt builder、model scripts、empty/ignored data tree |
| CausalGraphBench（变量 DAG，排除） | [ACL Anthology `2025.acl-srw.16`](https://aclanthology.org/2025.acl-srw.16/)，DOI `10.18653/v1/2025.acl-srw.16` | [official GitLab](https://gitlab.nl4xai.eu/nikolay.babakov/causal-graph-bench) | 论文 §§3–4.3、Tables 1–3；仓库 benchmark JSON、outputs、SHD evaluator |
| CausalGraph2LLM（变量 DAG，排除） | [ACL Anthology `2025.findings-naacl.110`](https://aclanthology.org/2025.findings-naacl.110/)，DOI `10.18653/v1/2025.findings-naacl.110`，arXiv `2410.15939` | [ivaxi0s/CausalGraph2LLM](https://github.com/ivaxi0s/CausalGraph2LLM) | 论文 §§3.1–4.1、Appendices A–C；仓库 graph/query generation 与 set-based evaluator |
| LoCoMo | [ACL Anthology `2024.acl-long.747`](https://aclanthology.org/2024.acl-long.747/)，DOI `10.18653/v1/2024.acl-long.747` | 以论文/ACL 页所列公开资源为准 | 任务定义、temporal event graph 的数据生成角色、QA/event summarization 任务 |
| AriGraph | [IJCAI 2025 proceedings paper](https://www.ijcai.org/proceedings/2025/0002.pdf)，arXiv `2407.04363` | [AIRI-Institute/AriGraph](https://github.com/AIRI-Institute/AriGraph) | graph world model 定义与 TextWorld/QA 评测边界 |
| Zep | [arXiv `2501.13956`](https://arxiv.org/abs/2501.13956) | [getzep/graphiti](https://github.com/getzep/graphiti) | temporal KG memory 架构、DMR/LongMemEval；仅作 arXiv 相邻证据 |

# A3a 阶段报告：2025–2026 顶会活跃度

> 核查日：2026-08-25。本节只报告从官方目录逐篇回溯得到的**最低可证下界**，不把关键词命中数伪装成穷尽 bibliometrics。2026 日历年尚未结束；即使 ACL 2026 已有正式 proceedings，也不能把“截至 8 月的跨会总数”与完整 2024/2025 直接比较。

## 21. 可复核检索与纳入口径

### 21.1 两层定义

- **Tier EKG：**论文的中心研究对象必须是 event/eventuality/script/narrative/causal-event graph 的构建、补全、查询、推理或应用。节点需要是事件 occurrence、eventuality 或 script step；仅在模型内部用一张辅助图，不自动升级为 Tier EKG。
- **Tier structured-event：**事件抽取（含 argument extraction）、event relation/coreference、temporal/causal/subevent relation、script event prediction 等结构任务；输出可以不是持久图。纯 event detection、纯事件分类或只在应用背景里提到 event，不计入本层。
- **排除：**通用 KG、变量级 causal DAG、纯 temporal KG completion/forecasting、通用 GraphRAG/agent memory，以及“图仅用于生成数据、最终 benchmark 不要求读写事件图”的论文。

### 21.2 proceedings 边界与查找法

本轮用 `paper-search` 生成候选，再以 ACL Anthology 的官方 event/volume 页逐标题复核。纳入 main/long/short 与 Findings；排除 workshop、demo、industry、SRW、tutorial。LREC-COLING 2024 按 ACL Anthology 的 `2024.lrec-main.*` 联合卷记一次，不在 COLING 与 LREC 下重复计数。标题词族包括 `event extraction/argument/relation/coreference/causality/temporal`、`event graph/eventuality/script`、`event reasoning/prediction`；人工再按上述语义边界排除误报。因此下列数字是“固定词族可复核的语义筛选下界”，不是声称没有漏召回的全量计数。

对 AAAI/IJCAI/WWW/SIGIR/CIKM，本轮没有取得同等完整的官方逐篇审计清单；仅保留先前已经回到官方论文页的一篇 AAAI 2024 正例和 IJCAI 2025 反例，其他格一律写“未能核实”，不填零。

## 22. Tier EKG 逐篇清单

以下共 **2024 年 ≥5 篇、2025 年 ≥6 篇、2026 年截至核查日 ≥1 篇**；每一篇都可用 ACL ID 在官方目录重计。

### 2024（≥5）

1. **EMNLP/Findings** — *What Would Happen Next? Predicting Consequences from An Event Causality Graph*，`2024.findings-emnlp.45`：给定 occurrence-level event causality graph 做后继事件预测。
2. **NAACL** — *Set-Aligning Framework for Auto-Regressive Event Temporal Graph Generation*，`2024.naacl-long.214`：中心输出是 event temporal graph。
3. **NAACL** — *Sentence-level Media Bias Analysis with Event Relation Graph*，`2024.naacl-long.292`：event relation graph 是下游分析的中心结构。
4. **LREC-COLING** — *DocScript: Document-level Script Event Prediction*，`2024.lrec-main.458`：中心任务是 document-level script event prediction。
5. **LREC-COLING** — *EventGround: Narrative Reasoning by Grounding to Eventuality-centric Knowledge Graphs*，`2024.lrec-main.587`：eventuality-centric KG 是叙事推理支架。

### 2025（≥6）

1. **ACL** — *EcomScriptBench: A Multi-task Benchmark for E-commerce Script Planning via Step-wise Intention-Driven Product Association*，`2025.acl-long.1`：中心对象是 script step/planning。
2. **ACL** — *EventRAG: Enhancing LLM Generation with Event Knowledge Graphs*，`2025.acl-long.830`：event KG 是 RAG/生成的显式外部结构。
3. **ACL** — *Causal Graph based Event Reasoning using Semantic Relation Experts*，`2025.acl-long.1269`：生成/使用 causal event graph 做推理。
4. **ACL** — *Multi-document Summarization through Multi-document Event Relation Graph Reasoning in LLMs: a case study in Framing Bias Mitigation*，`2025.acl-long.1291`：event relation graph reasoning 是多文档摘要方法的中心。
5. **NAACL** — *Cascading Large Language Models for Salient Event Graph Generation*，`2025.naacl-long.112`：直接以 salient event graph generation 为任务。
6. **COLING** — *Semantic and Sentiment Dual-Enhanced Generative Model for Script Event Prediction*，`2025.coling-main.622`：中心任务是 script event prediction。

### 2026（部分年份，≥1）

1. **ACL/Findings** — *Memory Matters More: Event-Centric Memory as a Logic Map for Agent Searching and Reasoning*，`2026.findings-acl.1123`：event-centric memory/logic map 是 agent search 与 reasoning 的中心结构。

## 23. Tier structured-event 逐篇清单

标签 `EE/EAE`、`ECI`、`TR`、`coref`、`reason/predict` 分别表示事件/论元抽取、事件因果识别、时序关系、事件共指、事件推理或预测。它们解释归层理由，不是另造任务分类。

### ACL 2024（≥20）

1. `2024.acl-long.164` — *Synergetic Event Understanding: A Collaborative Approach to Cross-Document Event Coreference Resolution with Large Language Models*（coref）
2. `2024.acl-long.210` — *Identifying while Learning for Document Event Causality Identification*（ECI）
3. `2024.acl-long.224` — *MAVEN-ARG: Completing the Puzzle of All-in-One Event Understanding Dataset with Event Argument Annotation*（EAE resource）
4. `2024.acl-long.502` — *Hyperspherical Multi-Prototype with Optimal Transport for Event Argument Extraction*（EAE）
5. `2024.acl-long.512` — *Improving Large Language Models in Event Relation Logical Prediction*（event relation）
6. `2024.acl-long.647` — *LLMs Learn Task Heuristics from Demonstrations: A Heuristic-Driven Prompting Strategy for Document-Level Event Argument Extraction*（EAE）
7. `2024.acl-short.27` — *Generating Harder Cross-document Event Coreference Resolution Datasets using Metaphoric Paraphrasing*（coref）
8. `2024.findings-acl.89` — *ConTempo: A Unified Temporally Contrastive Framework for Temporal Relation Extraction*（TR）
9. `2024.findings-acl.114` — *Harvesting Events from Multiple Sources: Towards a Cross-Document Event Extraction Paradigm*（EE）
10. `2024.findings-acl.309` — *Scented-EAE: Stage-Customized Entity Type Embedding for Event Argument Extraction*（EAE）
11. `2024.findings-acl.328` — *Thinking about how to extract: Energizing LLMs’ emergence capabilities for document-level event argument extraction*（EAE）
12. `2024.findings-acl.378` — *ONSEP: A Novel Online Neural-Symbolic Framework for Event Prediction Based on Large Language Model*（predict）
13. `2024.findings-acl.487` — *ULTRA: Unleash LLMs’ Potential for Event Argument Extraction through Hierarchical Modeling and Pair-wise Self-Refinement*（EAE）
14. `2024.findings-acl.528` — *MEEL: Multi-Modal Event Evolution Learning*（event evolution）
15. `2024.findings-acl.531` — *EVIT: Event-Oriented Instruction Tuning for Event Reasoning*（reason）
16. `2024.findings-acl.535` — *Towards Better Question Generation in QA-based Event Extraction*（EE）
17. `2024.findings-acl.564` — *Beyond Single-Event Extraction: Towards Efficient Document-Level Multi-Event Argument Extraction*（EAE）
18. `2024.findings-acl.715` — *LC4EE: LLMs as Good Corrector for Event Extraction*（EE）
19. `2024.findings-acl.758` — *Argument-Aware Approach To Event Linking*（event linking）
20. `2024.findings-acl.760` — *TextEE: Benchmark, Reevaluation, Reflections, and Future Challenges in Event Extraction*（EE benchmark）

### ACL 2025（≥12）

1. `2025.acl-long.414` — *Revisiting Classical Chinese Event Extraction with Ancient Literature Information*（EE）
2. `2025.acl-long.1134` — *Employing Discourse Coherence Enhancement to Improve Cross-Document Event and Entity Coreference Resolution*（coref）
3. `2025.acl-long.1251` — *Temporal Relation Extraction in Clinical Texts: A Span-based Graph Transformer Approach*（TR；graph 是模型结构，故不升 Tier EKG）
4. `2025.acl-long.1386` — *Adverse Event Extraction from Discharge Summaries: A New Dataset, Annotation Scheme, and Initial Findings*（EE resource）
5. `2025.acl-long.1389` — *PIPER: Benchmarking and Prompting Event Reasoning Boundary of LLMs via Debiasing-Distillation Enhanced Tuning*（reason）
6. `2025.findings-acl.43` — *Evaluating Instructively Generated Statement by Large Language Models for Directional Event Causality Identification*（ECI）
7. `2025.findings-acl.94` — *Event Pattern-Instance Graph: A Multi-Round Role Representation Learning Strategy for Document-Level Event Argument Extraction*（EAE；graph 是方法内表示）
8. `2025.findings-acl.677` — *Instruction-Tuning LLMs for Event Extraction with Annotation Guidelines*（EE）
9. `2025.findings-acl.1000` — *How do LLMs’ Preferences Affect Event Argument Extraction? CAT: Addressing Preference Traps in Unsupervised EAE*（EAE）
10. `2025.findings-acl.1198` — *ETRQA: A Comprehensive Benchmark for Evaluating Event Temporal Reasoning Abilities of Large Language Models*（TR/reason）
11. `2025.findings-acl.1284` — *LegalCore: A Dataset for Event Coreference Resolution in Legal Documents*（coref resource）
12. `2025.findings-acl.1353` — *GEMS: Generation-Based Event Argument Extraction via Multi-perspective Prompts and Ontology Steering*（EAE）

### ACL 2026（部分年份，≥7）

1. `2026.acl-long.871` — *Suggest-Verify-Revise: A Three-Stage Document-Level Event Causality Identification with Narrative Consistency*（ECI）
2. `2026.acl-long.910` — *HTMR: Hybrid Token Masking Reinforcement Learning with Verifiable Rewards for Event Argument Extraction with Multi-Perspective Reasoning*（EAE）
3. `2026.acl-long.1345` — *Incorporating Temporal Coherence to Cross-Document Event Coreference Resolution*（coref）
4. `2026.acl-long.1426` — *Evaluation Pitfalls and Challenges in Multimedia Event Extraction*（EE）
5. `2026.acl-long.2173` — *Reframing Responsibility: Framing-Aware Event Causality Identification*（ECI）
6. `2026.findings-acl.978` — *CVRH: Cross-modal Variational Role Hypergraph Network via Semantic Enhancement for Multi-modal Event Argument Extraction*（EAE；hypergraph 是内部结构）
7. `2026.findings-acl.2126` — *SERE: Structural Example Retrieval for Enhancing LLMs in Event Causality Identification*（ECI）

### EMNLP 2024（Tier structured-event ≥14；另有 Tier EKG 1）

1. `2024.emnlp-main.51` — *In-context Contrastive Learning for Event Causality Identification*（ECI）
2. `2024.emnlp-main.87` — *Advancing Event Causality Identification via Heuristic Semantic Dependency Inquiry Network*（ECI）
3. `2024.emnlp-main.103` — *Event Causality Identification with Synthetic Control*（ECI）
4. `2024.emnlp-main.673` — *Explicit, Implicit, and Scattered: Revisiting Event Extraction to Capture Complex Arguments*（EE/EAE）
5. `2024.emnlp-main.720` — *SPEED++: A Multilingual Event Extraction Framework for Epidemic Prediction and Preparedness*（EE）
6. `2024.emnlp-main.816` — *Weak Reward Model Transforms Generative Models into Robust Causal Event Extraction Systems*（causal EE）
7. `2024.emnlp-main.1136` — *Will LLMs Replace the Encoder-Only Models in Temporal Relation Classification?*（TR）
8. `2024.findings-emnlp.1` — *Are LLMs Good Annotators for Discourse-level Event Relation Extraction?*（event relation）
9. `2024.findings-emnlp.35` — *DocEE-zh: A Fine-grained Benchmark for Chinese Document-level Event Extraction*（EE benchmark）
10. `2024.findings-emnlp.47` — *Temporal Cognitive Tree: A Hierarchical Modeling Approach for Event Temporal Relation Extraction*（TR）
11. `2024.findings-emnlp.58` — *Employing Glyphic Information for Chinese Event Extraction with Vision-Language Model*（EE）
12. `2024.findings-emnlp.256` — *OEE-CFC: A Dataset for Open Event Extraction from Chinese Financial Commentary*（EE resource）
13. `2024.findings-emnlp.381` — *MMUTF: Multimodal Multimedia Event Argument Extraction with Unified Template Filling*（EAE）
14. `2024.findings-emnlp.958` — *Debate as Optimization: Adaptive Conformal Prediction and Diverse Retrieval for Event Extraction*（EE）

### EMNLP 2025（≥15）

1. `2025.emnlp-main.205` — *Multimedia Event Extraction with LLM Knowledge Editing*（EE）
2. `2025.emnlp-main.616` — *Dynamic Energy-Based Contrastive Learning with Multi-Stage Knowledge Verification for Event Causality Identification*（ECI）
3. `2025.emnlp-main.871` — *SciEvent: Benchmarking Multi-domain Scientific Event Extraction*（EE benchmark）
4. `2025.emnlp-main.972` — *Multi-Document Event Extraction Using Large and Small Language Models*（EE）
5. `2025.emnlp-main.1440` — *Seeing the Same Story Differently: Framing-Divergent Event Coreference for Computational Framing Analysis*（coref）
6. `2025.emnlp-main.1550` — *Reflective Agreement: Combining Self-Mixture of Agents with a Sequence Tagger for Robust Event Extraction*（EE）
7. `2025.emnlp-main.1743` — *Towards Event Extraction with Massive Types: LLM-based Collaborative Annotation and Partitioning Extraction*（EE）
8. `2025.findings-emnlp.139` — *DICP: Deep In-Context Prompt for Event Causality Identification*（ECI）
9. `2025.findings-emnlp.419` — *Adaptive Schema-aware Event Extraction with Retrieval-Augmented Generation*（EE）
10. `2025.findings-emnlp.421` — *REAR: Reinforced Reasoning Optimization for Event Argument Extraction with Relation-Aware Support*（EAE）
11. `2025.findings-emnlp.428` — *GDLLM: A Global Distance-aware Modeling Approach Based on Large Language Models for Event Temporal Relation Extraction*（TR）
12. `2025.findings-emnlp.482` — *EventRelBench: A Comprehensive Benchmark for Evaluating Event Relation Understanding in Large Language Models*（event relation benchmark）
13. `2025.findings-emnlp.649` — *REGen: A Reliable Evaluation Framework for Generative Event Argument Extraction*（EAE evaluation）
14. `2025.findings-emnlp.1010` — *Consistent Discourse-level Temporal Relation Extraction Using Large Language Models*（TR）
15. `2025.findings-emnlp.1154` — *Rule-Guided Extraction: A Hierarchical Rule Optimization Framework for Document-Level Event Argument Extraction*（EAE）

### NAACL 2024（Tier structured-event ≥11；另有 Tier EKG 2）

1. `2024.naacl-long.63` — *A Rationale-centric Counterfactual Data Augmentation Method for Cross-Document Event Coreference Resolution*（coref）
2. `2024.naacl-long.101` — *TISE: A Tripartite In-context Selection Method for Event Argument Extraction*（EAE）
3. `2024.naacl-long.191` — *Event Causality Is Key to Computational Story Understanding*（event causality/reason）
4. `2024.naacl-long.218` — *Okay, Let’s Do This! Modeling Event Coreference with Generated Rationales and Knowledge Distillation*（coref）
5. `2024.naacl-long.252` — *MOKA: Moral Knowledge Augmentation for Moral Event Extraction*（EE）
6. `2024.naacl-long.312` — *Generating Uncontextualized and Contextualized Questions for Document-Level Event Argument Extraction*（EAE）
7. `2024.naacl-long.368` — *Separation and Fusion: A Novel Multiple Token Linking Model for Event Argument Extraction*（EAE）
8. `2024.findings-naacl.116` — *ZSEE: A Dataset based on Zeolite Synthesis Event Extraction for Automated Synthesis Platform*（EE resource）
9. `2024.findings-naacl.244` — *Getting Sick After Seeing a Doctor? Diagnosing and Mitigating Knowledge Conflicts in Event Temporal Reasoning*（TR/reason）
10. `2024.findings-naacl.245` — *MCECR: A Novel Dataset for Multilingual Cross-Document Event Coreference Resolution*（coref resource）
11. `2024.findings-naacl.275` — *Targeted Augmentation for Low-Resource Event Extraction*（EE）

### NAACL 2025（Tier structured-event ≥6；另有 Tier EKG 1）

1. `2025.naacl-long.49` — *ACCESS: A Benchmark for Abstract Causal Event Discovery and Reasoning*（causal event discovery/reason）
2. `2025.naacl-long.178` — *Beyond Benchmarks: Building a Richer Cross-Document Event Coreference Dataset with Decontextualization*（coref resource）
3. `2025.naacl-long.295` — *BEMEAE: Moving Beyond Exact Span Match for Event Argument Extraction*（EAE）
4. `2025.naacl-long.479` — *Soft Syntactic Reinforcement for Neural Event Extraction*（EE）
5. `2025.findings-naacl.42` — *Joint Learning Event-Specific Probe and Argument Library with Differential Optimization for Document-Level Multi-Event Extraction*（EAE）
6. `2025.findings-naacl.182` — *Extracting Military Event Temporal Relations via Relative Event Time Prediction and Virtual Adversarial Training*（TR）

### COLING 2025（Tier structured-event ≥8；另有 Tier EKG 1）

1. `2025.coling-main.85` — *A Compressive Memory-based Retrieval Approach for Event Argument Extraction*（EAE；memory 不是事件图 memory）
2. `2025.coling-main.274` — *Generation-Augmented and Embedding Fusion in Document-Level Event Argument Extraction*（EAE）
3. `2025.coling-main.294` — *Fusion meets Function: The Adaptive Selection-Generation Approach in Event Argument Extraction*（EAE）
4. `2025.coling-main.460` — *MMD-ERE: Multi-Agent Multi-Sided Debate for Event Relation Extraction*（event relation）
5. `2025.coling-main.495` — *Enhancing Event Causality Identification with LLM Knowledge and Concept-Level Event Relations*（ECI）
6. `2025.coling-main.500` — *Large Language Model-Based Event Relation Extraction with Rationales*（event relation）
7. `2025.coling-main.507` — *DEGAP: Dual Event-Guided Adaptive Prefixes for Templated-Based Event Argument Extraction with Slot Querying*（EAE）
8. `2025.coling-main.628` — *Dr. ECI: Infusing Large Language Models with Causal Knowledge for Decomposed Reasoning in Event Causality Identification*（ECI）

### LREC-COLING 2024（Tier structured-event ≥18；另有 Tier EKG 2）

1. `2024.lrec-main.139` — *A Semantic Mention Graph Augmented Model for Document-Level Event Argument Extraction*（EAE；mention graph 是内部表示）
2. `2024.lrec-main.217` — *BKEE: Pioneering Event Extraction in the Vietnamese Language*（EE）
3. `2024.lrec-main.299` — *CMNEE: A Large-Scale Document-Level Event Extraction Dataset Based on Open-Source Chinese Military News*（EE resource）
4. `2024.lrec-main.412` — *Demonstration Retrieval-Augmented Generative Event Argument Extraction*（EAE）
5. `2024.lrec-main.450` — *Distill, Fuse, Pre-train: Towards Effective Event Causality Identification with Commonsense-Aware Pre-trained Model*（ECI）
6. `2024.lrec-main.459` — *Document-Level Event Extraction via Information Interaction Based on Event Relation and Argument Correlation*（EE/event relation）
7. `2024.lrec-main.501` — *Emancipating Event Extraction from the Constraints of Long-Tailed Distribution Data Utilizing Large Language Models*（EE）
8. `2024.lrec-main.523` — *Enhancing Cross-Document Event Coreference Resolution by Discourse Structure and Semantic Information*（coref）
9. `2024.lrec-main.541` — *Enhancing Unrestricted Cross-Document Event Coreference with Graph Reconstruction Networks*（coref；graph 是模型结构）
10. `2024.lrec-main.586` — *Event Extraction in Basque: Typologically Motivated Cross-Lingual Transfer-Learning Analysis*（EE）
11. `2024.lrec-main.711` — *Hierarchical Selection of Important Context for Generative Event Causality Identification with Optimal Transports*（ECI）
12. `2024.lrec-main.920` — *Linear Cross-document Event Coreference Resolution with X-AMR*（coref）
13. `2024.lrec-main.1039` — *Multimodal Cross-Document Event Coreference Resolution Using Linear Semantic Transfer and Mixed-Modality Ensembles*（coref）
14. `2024.lrec-main.1061` — *Nested Event Extraction upon Pivot Element Recognition*（EE）
15. `2024.lrec-main.1171` — *QA-based Event Start-Points Ordering for Clinical Temporal Relation Annotation*（TR）
16. `2024.lrec-main.1253` — *Schema-based Data Augmentation for Event Extraction*（EE）
17. `2024.lrec-main.1348` — *TacoERE: Cluster-aware Compression for Event Relation Extraction*（event relation）
18. `2024.lrec-main.1551` — *Zero-Shot Cross-Lingual Document-Level Event Causality Identification with Heterogeneous Graph Contrastive Transfer Learning*（ECI；graph 是方法结构）

### AAAI 2024（最低下界；Tier structured-event ≥1）

1. *Is a Large Language Model a Good Annotator for Event Extraction?*，DOI `10.1609/aaai.v38i16.29730`（EE/EAE）；本轮只保留这一篇已从 AAAI 官方页核过的正例，不声称是 AAAI 2024 全量。

## 24. 可由清单重计的 venue/year 下界

| Venue | 2024 | 2025 | 2026（截至 2026-08-25） | 覆盖边界 |
|---|---:|---:|---:|---|
| ACL（main/short + Findings） | EKG ≥0；structured ≥20 | EKG ≥4；structured ≥12 | EKG ≥1；structured ≥7 | 2026 ACL 已有目录，但跨会日历年不完整 |
| EMNLP（main + Findings） | EKG ≥1；structured ≥14 | EKG ≥0；structured ≥15 | 不可比/尚无本轮完整目录 | 2024/2025 由官方 event 页逐条列出 |
| NAACL（main/short + Findings） | EKG ≥2；structured ≥11 | EKG ≥1；structured ≥6 | 未能核实 | 2024/2025 由官方 event 页逐条列出 |
| COLING | 与 LREC 2024 联合卷合计见下行，未重复计数 | EKG ≥1；structured ≥8 | 未能核实 | 2025 由官方 event 页逐条列出 |
| LREC / LREC-COLING | EKG ≥2；structured ≥18 | 不适用本轮年度比较 | 主会卷未能从 ACL Anthology 核实 | 2024 为 `lrec-main` 联合卷 |
| AAAI | 已核 EKG 正例 0；structured ≥1（**非穷尽**） | 未能核实 | 未能核实 | 只有上列 DOI 正例，不将“无命中”写成全会零篇 |
| IJCAI | 未能核实 | 未取得合格正例；**非穷尽** | 未能核实 | AriGraph 是已核 false positive，见 §25 |
| WWW | 未能核实 | 未能核实 | 未能核实 | 未取得完整官方逐篇审计清单 |
| SIGIR | 未能核实 | 未能核实 | 未能核实 | 未取得完整官方逐篇审计清单 |
| CIKM | 未能核实 | 未能核实 | 未能核实 | 未取得完整官方逐篇审计清单 |

注意：表中的 `EKG ≥0` 只表示本节保守清单没有收录该层论文，**不是**证明会场中绝对为零；跨 venue 求和也只能得到下界。可直接相加的已列清单是：2024 Tier EKG ≥5、2025 Tier EKG ≥6；Tier structured-event 在 ACL/EMNLP/NAACL 三个共同 venue 中分别 ≥45 与 ≥33。后一个差值不能解释为下降，因为这是标题词族下界，且两年 proceedings/任务命名与召回并不等价。

## 25. False positives 与层级降级

| 候选 | 处理 | 证据边界 |
|---|---|---|
| *A Unified Temporal Knowledge Graph Reasoning Model Towards Interpolation and Extrapolation*，`2024.acl-long.8` | 排除 | 纯 TKG reasoning；中心节点是时序 KG fact，不是文本事件图。 |
| *TeRDy: Temporal Relation Dynamics through Frequency Decomposition for Temporal Knowledge Graph Completion*，`2025.acl-long.473` | 排除 | 纯 TKG completion。标题中的 temporal relation 不是 event temporal relation extraction。 |
| *STK-Adapter: Incorporating Evolving Graph and Event Chain for Temporal Knowledge Graph Extrapolation*，`2026.acl-long.905` | 排除 | event chain 是 TKG extrapolation 的辅助信息，中心 benchmark 仍是 TKG。 |
| *Conformal Event Prediction with Temporal Knowledge Graph*，`2026.findings-acl.258` | 排除 | 以 TKG 上 entity-relation facts 的预测为中心；不因标题有 Event 就纳入。 |
| *CausalGraph2LLM: Evaluating LLMs for Causal Queries*，`2025.findings-naacl.110` | 排除 | gold graph 节点是 causal variables，不是 events；详见 A2b。 |
| *CausalGraphBench*，`2025.acl-srw.16` | 排除 | 变量级 Bayesian/causal DAG，且 SRW 不在本节 track 范围。 |
| *Evaluating Very Long-Term Conversational Memory of LLM Agents*，`2024.acl-long.747`（LoCoMo） | 排除 | temporal event graph 用于数据生成，受测系统不必维护或查询 event graph。 |
| *AriGraph*，IJCAI 2025 paper 0002 | 排除 | semantic/episodic graph world model 是通用 agent memory，节点与 benchmark 均非 event-specific。 |
| *TAG-EQA*，`2025.starsem-1.24` | 不进入计数 | 是 event-graph-supported QA 正例，但 *SEM 不在指定十个会议内。 |
| `2025.findings-acl.94`、`2025.acl-long.1251`、`2026.findings-acl.978` 等题名含 graph 的抽取论文 | 降为 Tier structured-event | graph/hypergraph 是模型内部表示，公开主任务与 gold 输出仍是 argument/span/relation，而非持久事件图。 |

## 26. “被什么标签吸收”与趋势边界

从清单本身可以看到的标签迁移，而非凭印象推断：

1. **RAG/LLM generation：**2025 的 EventRAG（`2025.acl-long.830`）直接把 event KG 包进 RAG；同年 `2025.findings-emnlp.419` 把 RAG 放进 schema-aware EE。事件结构并未消失，而是进入 retrieval/generation 标签。
2. **LLM/agent memory：**2026 的 `2026.findings-acl.1123` 已把 event-centric graph 改称 agent 的 “logic map”；这是 Tier EKG 在 agent-memory 标签下继续存在的直接例子。
3. **event reasoning / benchmark：**CGEP、CGEL、PIPER、ETRQA、EventRelBench、ACCESS 的标题从“建图”转向 graph-conditioned prediction、causal/temporal/event reasoning 与 LLM evaluation。
4. **document/multi-document IE 与 summarization：**`2025.acl-long.1291` 用 event relation graph 做 multi-document summarization；同年 ACL/EMNLP/NAACL 清单中仍有 multi-document EE、coreference、timeline-related work。事件结构被包装进 document-level IE 和 downstream understanding。
5. **temporal/causal relation：**2025 EMNLP 的 ECI/TR/EventRel 条目和 COLING 的 ERE/ECI 条目很多；研究活跃度更明显地落在 relation extraction/reasoning，而不总使用 “event graph” 名称。

因此，本轮证据不支持“事件图研究在 2025 已下降”。保守下界中 Tier EKG 从 2024 的 ≥5 到 2025 的 ≥6，量级相近；更明显的变化是**标签与消费场景迁移**：由 event temporal graph generation、eventuality KG grounding、script prediction，扩展到 EventRAG、LLM causal/event reasoning、多文档摘要和 agent memory。它同样不足以声称“显著上升”：下界只差 1，且会议覆盖不完全一致。

2026 只能说“ACL/Findings 已出现 1 篇 Tier EKG、7 篇 Tier structured-event”；EMNLP/AAAI/IJCAI/WWW/SIGIR/CIKM 等年度集合尚未被本轮完整核查。**不能用 2026 的部分年份数字判下降。**

### 本块结论

- **趋势判定：**截至可审计清单，2024→2025 的 Tier EKG 是稳定到轻微增加的下界（≥5→≥6），不足以证明统计意义上的增长，也反驳不了遗漏召回；最稳健的结论是“没有消失，正在被 LLM/RAG、event reasoning、document-level IE 与 agent memory 标签吸收”。
- **结构任务仍活跃：**仅 ACL/EMNLP/NAACL，2024 清单已有 Tier structured-event ≥45，2025 ≥33；因是保守词族下界，不能把 45→33 相减成降幅，但它证明 2025 仍有密集的 extraction/relation/coreference/temporal/causal 研究。
- **2026 不可作下降证据：**当前只有 ACL/Findings 可列出 EKG ≥1、structured-event ≥7；跨会年度尚未闭合。
- **最关键的标签变化：**2024 的 graph generation/grounding/prediction 在 2025–2026 变成 EventRAG、LLM event reasoning、multi-document graph reasoning 和 event-centric agent memory。这里的“吸收”逐项对应 §22–§23 的真实标题。
- **严格边界仍必要：**把 TKG、变量 causal DAG、通用 episodic memory 或模型内部 graph encoder 混进 Tier EKG，会人为制造增长；§25 已给出可复核反例。

## 27. 未能核实

- 未完成 AAAI/IJCAI/WWW/SIGIR/CIKM 2024–2026 官方 proceedings 的全量逐标题审计；这些 venue 的空白不能读作零篇。
- 未能从 ACL Anthology 取得 `2026.lrec-main` 主会卷；LREC 2026 因而不可计数。
- 未取得 2026 EMNLP 等尚未完整出刊会议的闭合 proceedings；不做跨会 2026 年度总计。
- 固定标题词族会漏掉标题不出现 event/script/temporal/causal、但正文实为事件结构任务的论文；因此所有数字都保留 `≥`。
- 本节没有做作者去重、研究团队去重、引用/录用率归一化，也没有把 Findings 与 main 分别赋权；它只能回答“正式目录中至少有多少直接命中”，不能回答领域份额。
- COLING 与 LREC 在 2024 为联合卷；本节不拆分其归属，也不与单独的 COLING 2025 做同比。

## 28. A3a 官方来源入口

| 目录 | 官方入口 | 本节使用范围 |
|---|---|---|
| ACL 2024/2025/2026 | [ACL 2024](https://aclanthology.org/events/acl-2024/) · [ACL 2025](https://aclanthology.org/events/acl-2025/) · [ACL 2026](https://aclanthology.org/events/acl-2026/) | main/short + Findings；按 ACL ID 回溯标题 |
| EMNLP 2024/2025 | [EMNLP 2024](https://aclanthology.org/events/emnlp-2024/) · [EMNLP 2025](https://aclanthology.org/events/emnlp-2025/) | main + Findings |
| NAACL 2024/2025 | [NAACL 2024](https://aclanthology.org/events/naacl-2024/) · [NAACL 2025](https://aclanthology.org/events/naacl-2025/) | main/short + Findings |
| COLING 2025 | [COLING 2025](https://aclanthology.org/events/coling-2025/) | main proceedings |
| LREC-COLING 2024 | [ACL Anthology `2024.lrec-main` volume](https://aclanthology.org/volumes/2024.lrec-main/) | 联合主会卷，只计一次 |
| AAAI 2024 定向正例 | [AAAI official article, DOI `10.1609/aaai.v38i16.29730`](https://ojs.aaai.org/index.php/AAAI/article/view/29730) | 仅该篇，不代表全会穷尽 |
| IJCAI 2025 定向反例 | [IJCAI 2025 paper 0002](https://www.ijcai.org/proceedings/2025/0002.pdf) | AriGraph 边界核验，不计正例 |
