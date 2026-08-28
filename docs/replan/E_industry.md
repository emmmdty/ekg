# LLM 时代显式事件图谱/事理图谱的技术存在理由、工业落地与人才市场信号

本报告按 **2026-08-25** 快照核查。这里把“显式事件图”严格限定为：事件 occurrence、eventuality/script step，或明确的事件型 transactional record 是一级节点，并具有时间、因果、参与者、来源或跨事件关系中的至少一部分；**一般实体 KG、普通 temporal KG、GraphRAG、agent episodic memory 不因“有图”就自动算事件图**。这一口径与前置术语/benchmark 审计一致：EventRAG、CALLMSAE、CGEP、TAG-EQA 属直接事件结构证据；LoCoMo、AriGraph、Zep/Graphiti 更多属于相邻长期记忆证据。fileciteturn0file0 风险监测同样只作为应用延伸；现有供应链/大宗商品公开资源的 benchmark 闭环不足，不能由工业价值反推学术主轴。fileciteturn0file1

总体判断是：**显式事件图在 LLM 时代没有被证明为普遍必需，但也远未被“长上下文 + RAG + Agent”消解。最扎实的直接存在理由集中在跨文档事件组织、结构化检索和给定事件因果/时间结构后的推理；可审计、实时增量、幻觉约束和低成本推理则目前主要是 motivation、一般 KG/GraphRAG 邻近证据，或工程系统证据。** EventRAG 直接针对跨来源的事件中心推理；CGEP、TAG-EQA、CGEL直接测试事件因果图参与推理；而 GraphRAG 的公平评测和图质量研究又表明，图的收益强烈依赖问题类型、图质量和评测设计。citeturn24search1turn24search3turn25search0turn24search0turn26academia33turn26search0

## 技术存在理由：已实验验证、仅 motivation、反证与边界

下表中 **[E]** 表示 event-specific 直接证据，**[A]** 表示一般 KG/GraphRAG/agent-memory 邻近证据，**[X]** 表示尚未验证、不能从已有实验自动外推的主张。学术实验部分刻意**不复述性能数字**；涉及实验时给论文 ID、表/评测位置和 evaluator 口径，以遵守“没有完整实验轴就不报数”的约束。

| 能力 | 已实验验证 | 仅 motivation / 设计主张 | 反证与边界 |
|---|---|---|---|
| **可审计 / 来源追溯** | **没有取得 [E] 的直接实验闭环**：优先论文中没有一个把“从最终回答回溯到原文来源事件/边的正确率”作为独立公开主指标。EventRAG 的实验验证的是生成、RAG 与多跳推理质量，而不是 provenance-chain correctness；其生成评估包含 Figure 2 的 LLM pairwise judge，以及 Table 1 的 RAGAS 类回答指标。citeturn24search1 | **[A]** LLM-KG roadmap 的核心论点之一正是参数化知识难显式访问，而外部 KG 能提供显式结构和可解释事实支架；这是架构 motivation，不等于来源链已经被验证。前置审计同样发现 EventRAG、CGEL 等没有 gold proof/source chain。citeturn2search0 fileciteturn0file0 | **[X] “有图 = 可审计”不成立。** 如果节点、边本身由 LLM 自动抽取、合并或补边，可审计性只是把不可见错误变成了“可见但可能错误的结构”。CGEL 的解释链没有 gold explanation-chain 数据，部分解释质量依赖闭源 LLM judge；因此“能展示一条因果链”不等于“链已被事实审计”。citeturn24search0 |
| **时效与增量更新** | **[A] 部分成立。** Zep/Graphiti 一支把长期记忆建模成动态 temporal KG，AriGraph 则在 agent 探索过程中持续构造和更新 semantic + episodic graph；这证明“动态显式结构可被实现并参与长期任务”，但没有隔离测量事件身份合并、陈旧事实失效、冲突更新本身的正确率。citeturn1academia36turn25search3 | **[A]** LLM-KG roadmap 把动态知识更新视为参数化 LLM 与 KG 互补的重要理由；Graphiti 的工程定位也是实时更新 agent knowledge graph。其官方仓库截至 2026-08-25 仍持续开发。citeturn2search0 fileciteturn3file0 | **[X] 尚无足够 event-specific 证据**证明“显式事件图在高频新闻/风险流里比重新检索文本更准确、更便宜”。增量图还引入 event identity、去重、版本、边失效、关系重算与 schema migration 等维护成本；这些不是长上下文自动解决的问题，但也尚未形成统一 event benchmark。 |
| **长时程 / 跨文档组织** | **[E] 这是最强直接证据之一。** EventRAG 明确从多文档抽事件、合并语义等价事件节点并扩充事件关系，再进行迭代检索与推理；论文在 UltraDomain 与 MultiHopRAG 设置中验证该结构有下游作用。ACL ID `2025.acl-long.830`；论文 Figure 2 为 LLM pairwise judge，Table 1 为 RAGAS 类回答评测。citeturn24search1 CALLMSAE 则在长文档上直接验证 salient-event graph 的构建质量，NAACL ID `2025.naacl-long.112`，主要 graph-generation 结果见 Table 5 的 Hungarian Graph Similarity；但这只验证“能构图”，不等于证明图比 text-only 更利于下游长文档理解。citeturn24search2 | LoCoMo 的数据生成过程本身用 temporal event graphs 来保持几十个会话中的事件连续性，表明“事件结构是组织长时叙事的一种自然表示”。citeturn25search1 | **LoCoMo 不是 event-graph memory benchmark。** 其参赛系统的 gold 任务是 QA、事件总结和对话生成，不要求模型显式维护事件图。因此不能用“LoCoMo 是 event-graph 数据生成的”推出“图式 agent memory 已被 LoCoMo 验证”。citeturn25search1 AriGraph 也证明结构化 episodic memory 可行，但它是一般 agent world model，不是 occurrence-level 新闻事件图。citeturn25search3 |
| **结构化检索 / GraphRAG** | **[E] EventRAG 是目前最直接的证据。** 它不是把通用实体 KG 换个名字，而是构造 EKG、跨文档合并事件节点、编码 temporal/logical event relations，再迭代检索。citeturn24search1 **[A]** Microsoft GraphRAG 的原始研究则验证了 entity-KG + community summaries 对 corpus-global sensemaking 的价值，是事件图的强邻近证据，但不是 event-specific。citeturn26search3 | 显式结构允许“按实体—事件—时间—因果关系”筛选候选路径，而不只依赖 embedding 相似度；这是 EventRAG、CGEP 一类方法共同的结构性 motivation。citeturn24search1turn24search3 | **反证很重要。** 2025 的 unbiased GraphRAG evaluation 指出 unrelated questions 和 LLM-evaluation bias 会夸大 GraphRAG 增益，重新评估后的收益更温和。citeturn26academia33 Microsoft 自己的 LazyGraphRAG 也专门减少昂贵的 upfront graph summarization，说明完整预构图并非所有 query workload 的必要条件。citeturn26search5turn26search10 |
| **因果 / 时间一致性** | **[E] 直接证据较强，但主要是“给定或构得图之后是否有用”。** CGEP/SeDGPL（Findings EMNLP 2024，ID `2024.findings-emnlp.45`）输入 event causality graph 预测后继事件；主结果 Table 2 用 MRR/Hit@k，对应 gold 后继事件 ranking，不验证 proof trace。citeturn24search3 TAG-EQA（`2025.starsem-1.24`）在 TORQUESTRA 的人类因果 event graph 上系统比较 text-only、graph-only、text+graph，Tables 2–5 用最终二分类 accuracy；说明 graph context **在一部分模型/提示下**有帮助。citeturn25search0 CGEL（`2025.acl-long.1269`）同时测试 causal graph generation 与 graph-supported downstream event reasoning；intrinsic graph 见 Table 1，下游见 Tables 4–6。citeturn24search0 | 显式 BEFORE/CAUSE/ENABLE/BLOCK 等关系使“必须满足哪些局部结构条件”可表达，这是因果/时间 event graph 比纯文本上下文更明确的 motivation。citeturn24search0turn25search0 | **不能把 gold-graph upper bound 外推成 end-to-end 优势。** TAG-EQA 的图来自人标 TORQUESTRA，而不是先自动抽图再问答；CGEP 也是 graph-conditioned ranking。且 TAG-EQA 原文明确性能依模型/配置而变，并非每个设置都支持“graph > text”。前置逐表审计进一步记录了 text-only 与 graph 方法相当或更优的局部配置。citeturn25search0 fileciteturn0file0 |
| **幻觉 / 事实约束** | **[E] 只有部分证据。** CALLMSAE 的 iterative code-refinement 明确用于去掉 hallucinated relations、恢复遗漏边；但人标 test 的主评估是整体图相似度，不是独立的“幻觉率/事实一致率”，因此不能把 Table 5 解读成“已证明事件图降低最终 LLM 幻觉”。citeturn24search2 | **[A]** LLM-KG roadmap 把 external structured facts 作为缓解 hallucination、改善知识访问的重要方向，这是一般 KG motivation。citeturn2search0 | **错误会从生成端迁移到图端。** ReGraphRAG 明确指出从非结构化文本由 LLM 构出的 KG 往往出现 fragmented/disconnected subgraphs，破坏 inferential coherence；所以错误图不只是“没帮助”，还可能把错误变成可重复传播的结构约束。citeturn26search0 |
| **低成本推理 / LLM + 小模型协同** | **[A] 有明确邻近证据，[E] event-specific 证据弱。** GNN-RAG 在 KGQA 中展示“图检索器 + 较小语言模型”能够形成有效的 multi-hop 推理组合，是小模型/图协同的直接一般 KG 证据，但不是事件图。citeturn26search4 Microsoft 的 dynamic community selection 和 LazyGraphRAG 则表明，可让较便宜模型承担筛选/相关性判断，把高价模型留给最终生成。citeturn26search8turn26search10 | 显式图的一项工程假设是：一次构造后可反复查询、把 traversal/filter/ranking 交给数据库或小模型，从而减少每次让大模型“重新理解整段历史”的成本。 | **[X] 还不能说事件图天然更便宜。** EventRAG、CALLMSAE 等本身要支付事件抽取、实体/事件合并、关系补全和 LLM 调用成本。SAP 的 GraphRAG 工程研究甚至专门用非 LLM dependency pipeline 构图来解决 LLM graph construction 的成本/延迟问题。citeturn26academia32 是否划算取决于索引复用频率、更新频率和 query 类型。 |
| **Agent 长期记忆** | **[A] 证据已经很强，但 event-specific 仍是新支系。** AriGraph 在 IJCAI 2025 将 semantic 与 episodic memory 整合到持续更新的 KG world model，并在交互环境/静态多跳 QA 上实验。citeturn25search3 Zep/Graphiti 将 temporal KG 用于动态 agent memory，也在长期记忆 benchmark 上评估。citeturn1academia36 2026 的 event-centric agent-memory 工作已开始把 experiences 分割为事件并链接成 logic map，说明“event-centric memory”正在从邻近证据变成直接研究对象。citeturn3search0 | 长期 agent 的 history 会持续增长；显式 entity/event/episode identity、时间关系和状态变更能够支持“旧事实何时成立、后来是否被覆盖”这一类结构化 memory operation，这是 Graphiti/AriGraph 一支的核心设计动机。citeturn25search3turn1academia36 | **图不是长期记忆的必要条件。** LoCoMo 只证明长时记忆困难，并不要求 graph solution。citeturn25search1 AriGraph、Zep 也属于一般 episodic/temporal KG；把它们直接称为“事件图 benchmark 胜利”会扩大证据范围。 |

由这八栏可以把“存在理由”再压缩成三个证据等级。

**已经有较直接 event-specific 实验支持的理由**是：跨文档事件组织与检索、显式事件因果/时间结构参与下游推理，以及长文档事件结构生成本身。EventRAG、CGEP、TAG-EQA、CGEL、CALLMSAE分别覆盖这些位置。citeturn24search1turn24search3turn25search0turn24search0turn24search2

**目前更多只是合理 motivation 或邻近证据的理由**是：逐事实 provenance 审计、真正实时的 occurrence-level event graph 增量维护、直接降低最终生成幻觉、以及 event-specific 小模型降本。这些方向不能从“KG 有结构”“agent memory 有图”直接推出。

**正式反方的情况也要说清楚**：本轮没有取得一篇正式论文以“LLM 时代已经不再需要显式图”为明确立场。取得的是更有价值的**边界证据**：TAG-EQA 的图收益随模型/提示配置变化；GraphRAG 的公平重评得到更温和的收益；LLM 构图会碎片化；以及 Microsoft 自身用 LazyGraphRAG 减少完整预索引成本。它们支持的是“**graph is conditional infrastructure, not a universal winner**”，而不是“图已失效”。citeturn25search0turn26academia33turn26search0turn26search10

## 工业案例

这里特别区分“**系统中真的有 event-like nodes**”“只是一般 KG/graph analytics”“生产系统还是 demo”。工业规模数字均是**公司官方披露**，不视作独立第三方审计。

| 场景 | 公司 / 项目 | 实际问题 | 图中是否真有 event nodes | 生产使用还是 demo | 公开规模 / 指标 | 更新与开源状态 |
|---|---|---|---|---|---|---|
| **供应链 / 风控 / 海关** | **Altana — Supply Chain Graph / Altana Atlas** | 全球多层供应链追踪、贸易合规、forced-labor/fentanyl 风险、供应链中断与边境审查。citeturn27search3turn27search10 | **是，证据最明确。** 官方 schema 文档明确写 companies、facilities、products、**shipments** 以及它们之间关系都作为 graph nodes/edges；shipment 可以合理视为一次现实运输 transaction/event，但它不是 NLP event mention schema。citeturn27search1 | **生产。** 2024 官方公告明确称平台已部署于美国政府场景，包括 CBP；当前公司页面称 5,000+ CBP agents 日常使用。后者是公司自报。citeturn27search3turn27search21 | 当前文档称图持续更新；平台强调 proprietary logistics、public/commercial records 和 customer data 的融合。citeturn27search10 | 闭源 SaaS/平台；官方文档持续更新至本轮抓取日。 |
| **金融 AML / 风控** | **Quantexa — Decision Intelligence / AML Transaction Monitoring** | 将内部和外部数据通过 entity resolution 与 KG 聚合，用于 AML transaction monitoring、investigations、KYC 与风险识别。citeturn27search2turn27search7 | **未核实。** 官方材料明确有 entity resolution + KG，但没有取得公开 schema 证明“transaction/event”是一级 event node，而不是 relationship/fact/property。不能把它升级为事件图。 | **商业生产产品。** 2024/2025 官方材料均将其描述为金融机构使用的 AML/KYC 平台能力。citeturn27search2turn27search7 | 本轮没有取得可审计的 event-node 规模或与 text-only 系统同轴指标。 | 闭源商业系统。 |
| **舆情 / 情报 / 网络安全** | **Recorded Future — Intelligence Graph / Malware Intelligence** | 将开放网、暗网、技术 feed、customer telemetry 与威胁研究连接成可查询 threat context，用于 actor、infrastructure、vulnerability、malware 与 campaign 关联和实时情报。citeturn27search14turn27search4 | **事件一级节点未公开核实。** 公开材料确认 malware、actors、infrastructure、vulnerabilities、campaign context 被连接，但没有足够 schema 证据证明 occurrence-level attack/event 必为 vertex。 | **生产平台。** Intelligence Graph 是 Recorded Future 核心商业平台；2025 Malware Intelligence 明确由其驱动。citeturn27search4turn27search14 | 官方称索引 **100 万+ sources**；2025 Malware Intelligence 称每日识别 **150 万+ unique malware samples**。均为公司披露。citeturn27search14turn27search4 | 闭源。公开威胁研究持续发布，属于实战情报系统而非 benchmark。 |
| **安全** | **CrowdStrike — Threat Graph / Falcon** | 将 endpoint、identity、workload、IT 资产、安全 telemetry 和 threat intel 实时关联，用于检测、调查与 response。citeturn27search17 | **未核实 event-as-vertex。** 官方明确说处理/correlate security events，但同时公开“vertices”规模；没有取得公开 vertex-type schema，不能据“events/day”推成“每个安全事件都是 event node”。 | **生产。** Threat Graph 是 Falcon 商业平台核心数据/分析层。citeturn27search17 | 当前官方页称每日处理 **1 万亿+ events**、图跨 **2 万亿 vertices**、分析 15+ PB 数据；这是 CrowdStrike 自报规模。citeturn27search15turn27search16 | 闭源商业系统。 |
| **GraphRAG 基础设施 / 金融风险邻近** | **AWS Bedrock Knowledge Bases GraphRAG + Neptune Analytics / GraphRAG Toolkit** | 把实体关系图与向量检索结合，为复杂企业文档、fraud/suspicious-transaction 等参考场景提供 graph traversal + RAG。官方服务在 2025 进入 GA，并提供 GraphRAG 工具链。citeturn9search0turn9search2turn9search3 | **否，默认不能算事件图。** AWS 公开方案核心是一般 entity/relation graph；fraud transaction 示例不等于生产 schema 中存在 event nodes。 | **GraphRAG 服务本身是 GA 生产基础设施；具体 fraud 示例是 reference/example，不应冒充已核实名客户生产事件图。** citeturn9search0turn9search2 | 未公开 event-specific 生产规模。 | AWS 服务闭源；GraphRAG Toolkit 有官方开源组件。citeturn9search3 |
| **Agent 长期记忆** | **Zep / Graphiti** | 持续摄取 agent conversation、facts 与关系，维护可随时间变化的 temporal KG，为长期 agent 提供检索上下文。论文与项目定位均明确是动态 memory graph。citeturn1academia36 | **相邻而非严格事件图。** Graphiti 有 episode/temporal memory 语义，但研究与工程对象是一般 agent memory KG，不应自动重命名为 occurrence-level event graph。 | **开源基础设施 + 商业产品；本轮未取得可独立核验的外部命名客户“生产 event graph”案例。** | GitHub 社区规模和开发活跃度很高，但 star 不是生产采用证据。fileciteturn3file0 | Graphiti Apache-2.0；2026-07-27 发布 v0.29.3，2026-08-21 仍有提交。fileciteturn11file0 |
| **灾害** | **Neo4j 社区 / NODES 2024 — Earthquake Knowledge Graph in Japan** | 将日本地震相关知识组织为 KG，用于图查询/展示。citeturn9search12 | 本轮未把其 schema 核到“每次地震 occurrence 必为一级 event node”的程度。 | **会议工程展示 / demo 证据，不是生产灾害响应系统证据。** citeturn9search12 | 未取得生产规模/响应效果指标。 | 不能用该案例声称灾害事件图已规模化生产部署。 |

工业证据最值得注意的并不是“图已经到处替代 LLM”，而是**结构化实时系统的边界很清楚**。Altana 是本轮最强的严格案例：其公开文档确实把 shipment 作为 node，并且有政府生产部署证据。citeturn27search1turn27search3 Quantexa、Recorded Future 和 CrowdStrike 则都证明了“graph + entity resolution/contextualization + streaming risk data”具有真实商业价值，却**没有足够公开 schema 证明它们是学术意义上的 event graph**。citeturn27search2turn27search14turn27search17

这一区分对“风险监测”尤其重要：工业部门确实需要动态风险数据、时间、关联、provenance、实体消歧和调查工作流，但你已有的专项审计仍显示，供应链/大宗商品方向没有同步形成“固定 raw text + event/risk gold + evaluator + 多个独立公开方法”的成熟 NLP benchmark 闭环。fileciteturn0file1

## 招聘与技能信号

以下不是职位数量统计，也不用于推断“整个市场多少岗位需要 KG”。它只回答**截至 2026-08-25，能够从仍可访问的一手招聘页证明哪些最低需求形态确实存在**。同一岗位可能跨多个类别；这里尽量选择能直接暴露实际工程要求的职位。抓取日均为 **2026-08-25**。

| 技能类 | 公司 / 岗位 / 地区 | 必须或核心技能信号 | 加分 / 邻近技能 | 原始 URL 与状态 |
|---|---|---|---|---|
| **GraphRAG / KG-RAG** | **Outreach — Director of Applied Science & Engineering, Knowledge Graphs & AI — Hyderabad, India / Remote** | KG、entity resolution、temporal reasoning、event detection/linking、production graph roadmap；还负责实验和 evaluation。citeturn17view2 | KG+LLM RAG、agents、MCP 属明确邻近/加分方向。citeturn17view2 | `https://jobs.lever.co/outreach/dc29c7f1-d7ef-431f-a35a-173dac2a4138`；2026-08-25 可访问。 |
| **GraphRAG / KG-RAG** | **Causa Prima — Senior AI/LLM Agent Engineer** | Neo4j、entity extraction、GraphRAG、provenance、LLM agent orchestration、data pipelines。citeturn11search10 | 多 LLM evaluation/fallback、金融领域经验。 | `https://jobs.ashbyhq.com/causaprima/5b4c9051-ea41-4ddb-bf0b-53ca7fa78047/`；本次检索可访问；检索摘要未明确地区。 |
| **Agent memory / tool use / workflow** | **Recorded Future — Product Manager, AI Agents & MCP Tools — Boston** | 设计、评估和上线 agents / MCP tools；要求关注 tool success、quality regressions、latency、cost。citeturn14view1 | 网络安全/情报领域知识。 | `https://job-boards.greenhouse.io/recordedfuture/jobs/8691951002`；2026-08-25 可访问。 |
| **Agent memory / tool use / workflow** | **LangChain — AI Engineer, Enablement** | 强 Python、production agents、LangGraph/LangChain、LangSmith eval/tracing。citeturn10search8 | Cloud/Kubernetes/production deployment。 | `https://jobs.ashbyhq.com/langchain/b8dead31-212a-4b92-82a7-c42df16ae877`；本次检索可访问。 |
| **Agent memory / tool use / workflow** | **Mem0 — Backend Engineer — San Francisco Bay Area** | REST/API backend、关系数据库与 graph database/Neo4j，直接服务 production memory platform。citeturn11search3 | LLM/memory infrastructure experience。 | `https://jobs.ashbyhq.com/mem0/5ffae625-efc1-4add-8f6d-86d0186cc3c9/`；本次检索可访问。 |
| **信息抽取与数据管道** | **Outreach — Staff Applied Scientist, Knowledge Graphs & AI — Hyderabad, Remote** | Python；KG representation/reasoning；entity resolution、coreference、relation extraction、**event detection**、temporal modeling；生产部署与 drift/monitoring。citeturn17view0 | GNN、relational embeddings、link prediction。 | `https://jobs.lever.co/outreach/4ef30219-4dd5-4f40-b3b8-76c3c2277ebb`；2026-08-25 可访问。 |
| **信息抽取与数据管道** | **Inca Digital — Senior Data Engineer, Blockchain Data and/or NLP Pipelines — United States** | batch/incremental ETL、social/web text、entity/claim extraction、dedup/enrichment、Neo4j/关系存储；明确要求 provenance/versioning/freshness。citeturn17view3 | OSINT、dark-web / risk-data experience。 | `https://job-boards.greenhouse.io/incadigitalinc/jobs/4335954009`；2026-08-25 可访问。 |
| **信息抽取与数据管道** | **GHX — Senior AI Engineer — Hyderabad, India** | LLM document understanding、classification、structured extraction、workflow orchestration；先建 ground truth/evaluation 再 agent 化。citeturn16search5 | Agentic workflows。 | `https://job-boards.greenhouse.io/globalhealthcareexchangeinc/jobs/4694489005`；本次检索可访问。 |
| **LLM 微调、评测与可观测性** | **LangChain — Senior Backend Software Engineer, LangSmith** | tracing、monitoring、evaluation workflow、存储/query performance、testing、monitoring、alerting。citeturn10search4 | LLM developer tooling。 | `https://jobs.ashbyhq.com/langchain/f07c1416-f126-4925-8606-5dd7c5a90f6f`；本次检索可访问。 |
| **LLM 微调、评测与可观测性** | **Hadrian — Machine Learning Engineer, LLMs** | fine-tuned language models、document classification、information extraction、multi-page reasoning、annotation、active learning、synthetic data、evaluation。citeturn16search16 | production ML system experience。 | `https://jobs.ashbyhq.com/hadrian-automation/9675f96c-f161-444e-8d97-14690fbe5ab9`；本次检索可访问；摘要未取到地区。 |
| **KG / 图数据库 / 实体解析** | **Samba TV — Ontology Engineer, Knowledge Graph & Identity** | RDF/RDFS/OWL、SPARQL、SHACL、Python、entity resolution。citeturn11search16 | 生产 ontology / graph ecosystem。 | `https://jobs.lever.co/sambatv/7810c712-4c27-4161-9c1b-96353a210421`；本次检索可访问；摘要未取到地区。 |
| **KG / 图数据库 / 实体解析** | **Samba TV — Senior Ontologist, Knowledge Graph & Identity** | production triplestores，如 Neptune/Stardog/GraphDB/Jena；SHACL、entity resolution、数据建模。citeturn11search17 | PySpark/Databricks、GNN。 | `https://jobs.lever.co/sambatv/24ff7e8b-bec7-453e-9356-3e5ff843431a`；本次检索可访问。 |
| **Temporal / causal modeling** | **Outreach — Senior Applied Scientist, Knowledge Graphs & AI — Hyderabad, Remote** | temporal modeling/reasoning、event detection、entity resolution、graph traversal/link prediction、production pipelines。citeturn17view1 | KG + LLM 应用。 | `https://jobs.lever.co/outreach/cc0715d3-8bbf-4a5c-bd32-7d12c243e2c9`；2026-08-25 可访问。 |
| **Temporal / causal modeling** | **Airbnb — Staff Data Scientist, Causal Inference — US remote eligible** | causal inference、observational modeling、SQL/Python/R、产品实验/决策。citeturn15search11 | AI/ML。 | `https://careers.airbnb.com/fr/positions/9373891/`；本次检索可访问。注意：这是统计因果推断需求，不是 event-causality graph 岗位。 |
| **Temporal / causal modeling** | **Sentra — ML Research Scientist — San Francisco/Bay Area, on-site** | temporal/causal memory、大量 micro-events、把观测抽取成 entity-relation representations。citeturn16search8 | 长时程 agent/structured memory。 | `https://jobs.ashbyhq.com/sentra/03976429-eb79-48df-8439-29f0cdaba859/`；本次检索可访问。 |
| **风控 / 情报领域工程** | **Recorded Future — Principal Data Engineer — Boston** | 将多源数据摄取/融合进 Intelligence Graph；Python、Kafka/RabbitMQ、MongoDB、Neptune/Neo4j、Elasticsearch、cloud；production ETL。citeturn14view0 | Kubernetes/Prefect；把 LLM outputs 产品化。 | `https://job-boards.greenhouse.io/recordedfuture/jobs/8652561002`；2026-08-25 可访问。 |
| **风控 / 情报领域工程** | **Inca Digital — Senior Data Engineer, Blockchain Data and/or NLP Pipelines — US** | provenance-preserving risk data pipeline、NLP extraction、incremental ETL、graph/relational storage。citeturn17view3 | OSINT、dark web、金融/风险数据。 | `https://job-boards.greenhouse.io/incadigitalinc/jobs/4335954009`；2026-08-25 可访问。 |

这组职位没有资格被转换成“市场占比”，但可以支持一个很具体的**最低可证需求形态**：

**第一，招聘市场并不主要购买“会画事件图”这一标签，而是在购买一整条 production structured-AI pipeline。** Outreach 的三个在招层级把 entity resolution、event detection、temporal modeling、KG、生产 deployment/drift monitoring 连在一起；Inca 又把 incremental ETL、NLP extraction、provenance、freshness 和 Neo4j 连在一起。citeturn17view0turn17view1turn17view2turn17view3

**第二，Agent 工程需求已经明显把“模型调用”扩展成 tool/workflow/evaluation infrastructure。** Recorded Future 的当前岗位直接写 AI Agents & MCP Tools，并要求 success/latency/cost/evaluation；LangChain 岗位将 LangGraph 与 LangSmith tracing/evals 放在同一个 production 技能栈里。citeturn14view1turn10search8turn10search4

**第三，KG 本身没有消失，但它更常作为 AI system substrate 出现。** Neo4j/SPARQL/OWL/SHACL、entity resolution、graph traversal 与 LLM/RAG/agent 常出现在同一岗位，而“纯 KG research”与“纯 prompt engineering”都不是这些职位的完整画像。citeturn17view0turn11search16turn11search17

## 开源活跃度

以下是 **2026-08-25 GitHub API 快照**。`star` 仅表示社区关注；**绝不等同生产采用、论文质量或职业需求规模**。对论文型仓库，少 star 或无 release 很常见，因此也不能反推研究价值。

| 项目 | 2026-08-25 star | 最近提交 / 推送 | 最新 release | 贡献者 / issue 活性 | Archived | 解读 |
|---|---:|---|---|---|---|---|
| **Microsoft GraphRAG** `microsoft/graphrag` | **35,672** | 2026-08-24；另核到最新 commit `f40e9a26…`。仓库 GitHub API `pushed_at` 为 2026-08-24。fileciteturn2file0 | **v3.1.2，2026-08-21**。fileciteturn10file0 | 36 open issues；近期持续 commit/release，属于明显活跃维护。fileciteturn2file0 | 否 | 通用 GraphRAG 工程生态信号很强；不是 event-specific adoption 证据。 |
| **Zep / Graphiti** `getzep/graphiti` | **30,292** | 2026-08-21；核到最新 commit `993e081a…`。fileciteturn3file0 | **v0.29.3，2026-07-27**。fileciteturn11file0 | 490 open issues；v0.29.3 release notes 含大量 PR 与多名 new contributors，显示活跃外部贡献。fileciteturn11file0 | 否 | Agent temporal/graph memory 社区信号非常强，但它是一般 memory KG，不是 event graph 使用量统计。 |
| **AriGraph** `AIRI-Institute/AriGraph` | **173** | GitHub `pushed_at`：2024-09-10。fileciteturn8file0 | GitHub Releases API 返回空列表。fileciteturn17file0 | 2 open issues；当前没有近期 push。fileciteturn8file0 | 否 | 更接近论文代码快照，而非持续维护的平台项目。 |
| **EventRAG** `Ryaang/EventRAG` | **21** | `pushed_at`：2025-02-16。fileciteturn5file0 | 无 GitHub release。fileciteturn13file0 | 0 open issues；仓库体量较小。fileciteturn5file0 | 否 | 论文方法代码信号；不能据 star 推断 ACL 方法工业采用。 |
| **SeDGPL / CGEP** `zhanchuanhong/SeDGPL` | **5** | `pushed_at`：2026-03-25。fileciteturn6file0 | 无 GitHub release。fileciteturn15file0 | 2 open issues。fileciteturn6file0 | 否 | 2026 仍有 push，但前置审计发现 MAVEN 派生数据/完整 runnable entry 仍不闭合。fileciteturn0file0 |
| **CALLMSAE** `Xingwei-Tan/CALLMSAE` | **4** | `pushed_at`：2025-02-02。fileciteturn4file0 | 无 GitHub release。fileciteturn14file0 | 1 open issue。fileciteturn4file0 | 否 | 典型论文仓库；前置审计还发现 HGS evaluator 与 NYT 数据许可/发布包存在缺口。fileciteturn0file0 |
| **TAG-EQA** `MaithiliKadam4/TAG-EQA` | **0** | `pushed_at`：2025-11-09。fileciteturn7file0 | 无 GitHub release。fileciteturn16file0 | 0 open issues。fileciteturn7file0 | 否 | 代码存在不等于 benchmark 包闭合；前置审计发现派生 TORQUESTRA data 未随 repo 提交。fileciteturn0file0 |
| **CGEL 官方代码** | — | — | — | 论文曾给出官方 repo，但前置审计在 2026-08-25 未能访问该仓库，故本轮不制造 star/commit 快照。fileciteturn0file0 | 未核 | “论文说 code available”与“当前仍可复现”必须分开。 |

这个快照出现了非常明显的分层：**通用 GraphRAG 和 agent temporal-memory 工具正在形成持续工程项目，而 EventRAG、CALLMSAE、CGEP、TAG-EQA 目前更像论文代码资产。** Microsoft GraphRAG 和 Graphiti 在 2026 年仍有 release、近期 commit 和大量社区互动；event-specific 学术 repo 的 star、release 和持续维护都弱很多。fileciteturn2file0 fileciteturn3file0 fileciteturn10file0 fileciteturn11file0

这只能解释**工程生态成熟度差异**，不能解释“event graph 学术上没价值”。尤其不能把 3 万 star 与几十 star 的差距写成工业采用率或职业市场份额。

## 对 LLM/Agent 工程人才价值的含义

对职业技术栈而言，证据支持的不是“为了就业一定要研究事件图”，而是一个更细的结论：**事件图相关研究可以自然暴露一组 LLM/Agent 工程真正需要的系统问题，但就业价值主要来自这些可迁移能力，而不是论文主题标签本身。**

最直接的第一层价值是 **structured AI data engineering**。当前 Outreach 岗位几乎把本课题相邻技能写成了一条完整链：entity resolution → coreference/relation extraction → event detection → temporal modeling → KG → graph reasoning → production monitoring；Inca 又补上 incremental ETL、provenance、versioning 和 freshness。citeturn17view0turn17view3 这意味着，做显式事件结构时真正有迁移价值的部分，是能够把“不稳定文本”变成**有身份、有时间、有版本、有来源、可查询的数据对象**。

第二层是 **RAG / agent retrieval engineering**。EventRAG 学术上把事件节点用于跨源检索；Microsoft GraphRAG、LazyGraphRAG 则说明工业级结构检索要认真处理索引成本、retrieval mode、query routing 与 token budget；Graphiti 又把同类问题推到长期 agent memory。citeturn24search1turn26search3turn26search10 fileciteturn3file0 因此，对 LLM/Agent 工程职位更可迁移的能力不是“掌握某一种 EventRAG prompt”，而是能够判断**何时走 vector、何时走 graph traversal、何时检索 episode、何时升级到 LLM reasoning，以及如何测 recall/latency/cost**。

第三层是 **evaluation 与 observability**。LangChain 当前职位把 tracing、evaluation、monitoring、alerting 直接当产品能力；Recorded Future 的 agent/MCP 岗位也要求 tool success、regression、latency 与 cost。citeturn10search4turn14view1 这一点反而与事件图学术论文的薄弱处形成互补：EventRAG/CGEL 还依赖 LLM judge，TAG-EQA/CGEP 只验证最终答案，CALLMSAE 的图 evaluator 发布也不完整。fileciteturn0file0 对工程人才而言，**构造可重复 eval harness、gold trace/provenance check、failure taxonomy 和 online monitoring** 很可能比再封装一次 Agent API 更有长期价值。

第四层是 **LLM + 小模型 / 数据系统协同**。GNN-RAG 一类一般 KG 证据表明，graph retriever 与较小 LM 可以形成有效组合；Microsoft 又把 relevance filtering 下沉给更便宜模型；SAP 的 GraphRAG 工作直接尝试用传统 NLP 构图来避免昂贵 LLM indexing。citeturn26search4turn26search8turn26academia32 这支持一种实际工程技能：会训练/部署 encoder、reranker、IE model、GNN 或规则组件，并让它们与 LLM 协作，而不是默认所有步骤都交给最大的生成模型。

第五层是 **temporal / causal 的职业价值需要拆开看**。Outreach 的 temporal reasoning、event detection 与 KG 是高度贴近本课题的“结构化事件”需求；Airbnb 的 causal inference 则是统计因果/实验决策需求，两者都叫 causal/temporal，但技能体系并不相同。citeturn17view1turn15search11 因此不能因为“因果岗位多”就推断“事件因果图岗位多”，也不能反过来认为研究 event causality 对所有 causal-inference 职位都有直接映射。

最后，风险/情报领域确实给这些技能提供了很自然的工程出口：Recorded Future、Altana、Quantexa、CrowdStrike 都在做实时数据关联、风险发现、实体/关系上下文与调查工作流。citeturn27search3turn27search2turn27search14turn27search17 但这仍然**不构成学术选题论证**。你已有的独立审计恰恰表明，供应链/commodity risk 的公开 benchmark 不闭合；因此比较稳健的关系仍是“公开 benchmark 决定论文问题，风险监测作为应用验证”，而不是反过来。fileciteturn0file1

## 未能核实

**没有核实到 event-specific provenance benchmark。** 本轮没有找到公开任务同时给出原始多文档、事件节点/边、最终回答、source citation/proof trace gold，并单独评价“最终结论追溯到正确来源”的准确性。EventRAG、CGEL 等能展示结构，但现有主 evaluator 不等于 provenance evaluator。citeturn24search1turn24search0

**没有核实到 occurrence-level event graph 的标准增量更新 benchmark。** Graphiti/Zep、AriGraph 等证明动态 graph memory 是活跃技术方向，但“新文档到达后应该新增、合并、修正、失效哪些事件/关系”仍没有本轮取得的统一 event-specific gold protocol。citeturn1academia36turn25search3

**没有核实到 event-specific 的“图显著降低最终 LLM hallucination”干净因果实验。** CALLMSAE 验证图生成改进，但没有把最终生成 hallucination 单独作为 event-graph-vs-text 主指标；一般 KG roadmap 的 factual grounding 论点仍主要是邻近证据。citeturn24search2turn2search0

**没有核实到 event-specific 的低成本推理优势。** 能取得的强证据主要来自 GNN-RAG、LazyGraphRAG 和企业 GraphRAG construction，而不是 EventRAG/CGEP/TAG-EQA 同轴的 cost-quality benchmark。citeturn26search4turn26search10turn26academia32

**没有取得一篇正式论文明确主张“LLM 时代不再需要图”。** 因此不能把本报告关于成本、噪声和 text-only competitive settings 的综合判断包装成一个不存在的“反图学派”。真正取得的是 conditional-benefit 证据。citeturn25search0turn26academia33turn26search0

**没有核实灾害领域 2024–2026 一个同时满足“生产运行 + 一级 event nodes + 官方规模/指标公开”的案例。** 取得的日本 Earthquake KG 是工程会议/demo 级证据，不能冒充生产系统。citeturn9search12

**Quantexa、Recorded Future、CrowdStrike 的公开材料都不足以确认 event-as-node schema。** 它们能确认 graph/KG 和风险/安全生产用途，却不能仅因处理 transactions、campaigns 或 trillions of events 就重新分类成事件图。citeturn27search2turn27search14turn27search17

**Zep/Graphiti 的外部命名生产客户采用未在本轮以一手公开工程材料闭合。** 因而报告只把它记为高活跃 agent-memory OSS/产品信号，不写成“某大型企业已生产使用事件图”。fileciteturn3file0

**部分学术复现包仍不闭合。** EventRAG 的公开仓库不含完整论文评测包；CALLMSAE 缺官方 HGS evaluator 且有 NYT 发布/许可边界；CGEP 缺部分 MAVEN 派生运行资产；TAG-EQA 当前仓库未闭合派生 TORQUESTRA 数据；CGEL 论文所列代码仓库此前审计时不可访问。fileciteturn0file0

**招聘证据只是抓取日快照。** 本报告只采用 2026-08-25 检索时仍可访问的一手职位页/官方技术信号，不把职位数做成市场统计，也不保证页面在未来仍开放。

## 与预期不符事实

**最强的“显式事件图存在理由”并不是可审计或防幻觉，而是跨文档组织和结构化事件推理。** EventRAG、CGEP、TAG-EQA、CGEL 对这一点的直接实验链明显比 provenance、freshness、hallucination 的 event-specific 实验证据完整。citeturn24search1turn24search3turn25search0turn24search0

**“图能让回答更可靠”与“自动构出来的图本身可靠”是两个不同问题。** TAG-EQA 的 gold causal graph 能帮助部分 reasoning setting，但这并未回答真实 pipeline 中自动事件抽取、共指、时间关系和因果边错误叠加后是否仍有收益；ReGraphRAG 恰好说明自动 LLM-KG 的 fragmentation 会削弱图检索优势。citeturn25search0turn26search0

**GraphRAG 的反证不是“vector RAG 必胜”，而是“评测和成本会改变结论”。** 公平重评发现一些原先较大的收益缩小；Microsoft 自己又推出 LazyGraphRAG 避免昂贵 upfront summarization。这比一个笼统的“图没用”结论更重要，因为它直接表明 architecture choice 必须考虑 query distribution 和 amortization。citeturn26academia33turn26search10

**工业界最严格的 event-node 生产证据反而来自 supply-chain transaction graph，而不是 NLP 公司。** Altana 明确把 shipments 作为节点，并有美国政府部署证据；安全/情报平台虽然图规模更大，公开 schema 反而不足以确认 occurrence-level event nodes。citeturn27search1turn27search3turn27search14turn27search17

**Agent memory 的工程生态信号比 event-specific GraphRAG 论文生态明显强。** Graphiti 与 Microsoft GraphRAG 在 2026 年仍持续 release/commit，star 达数万级；EventRAG、CALLMSAE、CGEP、TAG-EQA 更像论文代码发布。这个事实只支持“工程生态成熟度不同”，不能支持“event graph 学术上不值得做”。fileciteturn2file0 fileciteturn3file0 fileciteturn5file0 fileciteturn4file0

**招聘页确实出现了一个高度贴近“事件结构 + LLM/KG 工程”的真实技能组合，而不需要硬凑。** Outreach 当前岗位明确同时写 event detection、temporal modeling/reasoning、entity resolution、KG、graph traversal、production monitoring，并在更高层岗位把 RAG/agents/MCP列为相邻能力。citeturn17view0turn17view1turn17view2 这比用“知识图谱工程师”这一过宽岗位名推市场需求更有信息量。

**但 causal 的市场信号并不自动支持 event causality。** Airbnb 的当前岗位证明 causal inference 是生产技能，却属于统计/实验决策；Outreach 的 temporal/event/KG 才更接近 event-structure modeling。citeturn15search11turn17view1

**风险监测工业需求强，并没有同步产生一个适合论文主轴的公开 benchmark。** Altana、Recorded Future、Quantexa 等都显示风险领域愿意为关联、实时更新、调查上下文付费；但前置专项审计仍发现供应链/commodity NLP benchmark 缺少可复核闭环。citeturn27search3turn27search14turn27search2 fileciteturn0file1 这正是“工业问题价值”和“论文 benchmark 可做性”必须分开的现实例子。

## 证据审计

| 证据 | 类型 / 一手性 | 能支持什么 | **不能**支持什么 | 可复现 / 偏差风险 | 本报告置信度 |
|---|---|---|---|---|---|
| **EventRAG**, ACL 2025，ID `2025.acl-long.830` | 正式论文 + 官方代码 | event-specific 跨文档 EKG、事件节点合并、temporal/logical retrieval；验证 eventized RAG 的存在性。citeturn24search1 | 不能证明所有 GraphRAG/query 都需要事件图；不能直接证明 provenance、incremental update 或成本优势。 | 论文含 LLM pairwise judge/RAGAS；前置审计发现完整评测资源未随 repo 闭合。fileciteturn0file0 | **高**：任务/方法；**中**：可复现精确收益。 |
| **CALLMSAE / NYT-SEG**, NAACL 2025，ID `2025.naacl-long.112` | 正式论文 + 官方 repo | 长文档 salient event graph 自动生成；hierarchical/temporal/causal relations；Table 5 人标 test 图质量。citeturn24search2 | 不能证明 event graph 提升最终 QA/RAG；不能把“去 hallucinated relation”写成最终 LLM hallucination 已解决。 | HGS evaluator、NYT text/license 与完整 train package 存在缺口。fileciteturn0file0 | **高/中**。 |
| **CGEL**, ACL 2025，ID `2025.acl-long.1269` | 正式论文 | 生成 causal event graph，并用于 forecasting、timeline/event reasoning、explainable event prediction。citeturn24search0 | 不能证明 explanation chain faithful；没有 gold proof chain。 | 部分 explanation quality 依赖闭源 judge；前置审计时官方 repo 不可访问。fileciteturn0file0 | **高**：论文结论；**中低**：完整复现。 |
| **CGEP / SeDGPL**, Findings EMNLP 2024，ID `2024.findings-emnlp.45` | 正式论文 + repo | occurrence/event-mention causality graph 作为后继事件 ranking 输入；Table 2 的 MRR/Hit@k 构成明确 graph-conditioned task。citeturn24search3 | 不验证自动构图；不验证 gold reasoning trace。 | MAVEN 派生数据和完整运行入口不闭合。fileciteturn0file0 | **高**：任务；**中**：端到端复现。 |
| **TAG-EQA / TORQUESTRA**, *SEM 2025，ID `2025.starsem-1.24` | 正式论文 + repo | 人工 causal event graph 对 LLM event QA 的 conditional utility；系统比较 text/graph/text+graph。citeturn25search0 | 不能证明自动 event graph pipeline 的净收益；不能说所有配置 graph 都优于 text。 | 只评 final answer，不评 proof fidelity；前置审计发现派生数据未随 repo 闭合。fileciteturn0file0 | **高**。 |
| **LoCoMo**, ACL 2024，ID `2024.acl-long.747` | 正式 benchmark | 长时对话确实存在长期时间/因果记忆困难；temporal event graph 在数据生成/一致性控制中发挥作用。citeturn25search1 | 不能证明 event graph memory 优于其他 memory architecture；受测系统不要求显式图。 | benchmark 本身公开、概念边界清楚。 | **高**。 |
| **AriGraph**, IJCAI 2025 | 正式论文 + repo | semantic + episodic graph memory 可在 agent 中持续更新并参与 planning。citeturn25search3 | 不能当 event-specific benchmark，也不能外推到新闻事件身份/来源审计。 | 任务是 text-world/general KG 邻近。 | **高**：邻近证据。 |
| **Zep / Graphiti** | arXiv 方法 + 官方活跃 OSS | temporal KG agent memory 的工程可行性、实时更新系统和社区活跃度。citeturn1academia36 fileciteturn3file0 | 不能证明 occurrence-level event KG 是 agent memory 的必要形式；不能以 star 替代工业采用。 | OSS 很活跃，但 benchmark 是一般 memory，event-specific 程度有限。 | **高**：工程信号；**中**：学术外推。 |
| **LLM–KG roadmap**, TKDE 2024 | Survey/roadmap | 系统梳理 LLM 参数知识难访问/更新、KG 结构与外部知识的互补，以及 KG 不完整、动态和维护成本。citeturn2search0 | **不是实验。** 不能用它声称 KG/事件图一定优于 LLM。 | position/survey evidence。 | **高**：motivation 层。 |
| **Microsoft GraphRAG / LazyGraphRAG** | Microsoft Research 一手研究 + OSS | 证明一般 graph retrieval 在 global sensemaking 上有价值，同时直接暴露 upfront indexing/query cost 问题。citeturn26search3turn26search10 | 不是 event-specific。 | 部分评估使用 LLM judge；微软自己的成本优化也说明不存在单一固定最佳模式。 | **高**：一般 GraphRAG 邻近证据。 |
| **Unbiased GraphRAG Evaluation** | 2025 原始研究预印本 | 对 GraphRAG 既有评测中的 unrelated-question、judge bias 提出反证，并报告重评后更温和收益。citeturn26academia33 | 不能据一篇重评宣布所有 GraphRAG 无效。 | 尚属预印本；但作为“边界证据”直接相关。 | **中高**。 |
| **ReGraphRAG**，Findings EMNLP 2025 | 正式论文 | LLM 构 KG 会 fragment/disconnect，图质量会直接破坏 inferential coherence。citeturn26search0 | 不能证明 text-only 永远优于 graph。 | 正式论文，边界明确。 | **高**。 |
| **Altana** | 官方 schema 文档 + 生产部署公告 | shipment 明确为 graph node；动态供应链图；美国政府/CBP 使用。citeturn27search1turn27search3 | 公司自报规模不能视为第三方审计；shipment graph ≠ NLP benchmark。 | 产品证据强，效果指标公开性有限。 | **高**：是否生产/是否有 shipment node。 |
| **Quantexa / Recorded Future / CrowdStrike** | 公司官方产品/技术材料 | 风险、AML、情报、安全领域真实使用 graph/KG/contextual analytics。citeturn27search2turn27search14turn27search17 | 公开 schema 不足，不能称 strict event graph。 | 商业材料可能选择性披露；规模数字由公司自报。 | **高**：产品存在；**中**：内部图语义。 |
| **当前招聘页** | 公司一手 careers/Greenhouse/Lever/Ashby | 能证明具体技能组合在 2026-08-25 有最低可证需求：KG、event detection、temporal reasoning、agents/MCP、eval、provenance、IE pipeline 等。citeturn17view0turn17view2turn14view1turn17view3 | 不能做整个就业市场职位占比或趋势统计。 | 页面会失效；因此只作为抓取日 snapshot。 | **高**：岗位文本；**低**：任何全市场外推。 |
| **GitHub API 快照** | 官方 GitHub metadata/releases | star、最近 push、release、open issues、archived 状态。fileciteturn2file0 fileciteturn3file0 | 不能证明公司使用量、论文质量或就业需求。 | 数值随时间变化；本报告锁定 2026-08-25。 | **高**。 |
| **前置 terrain / benchmark 审计** | 用户提供的逐论文、repo、evaluator 交叉审计 | 补足 EventRAG/CALLMSAE/CGEP/TAG-EQA 发布包边界，以及 event graph 与 general KG/memory 的分类。fileciteturn0file0 | 不是新的独立第三方实验。 | 适合作为本报告的证据审计底稿。 | **高**：已核边界。 |
| **风险方向交叉核验** | 用户提供的独立本地 audit | 支持“供应链/commodity risk 有问题价值但 benchmark 不闭合；风险监测不应反推学术主轴”。fileciteturn0file1 | 不能证明该领域永久不存在 benchmark。 | 明确限定为截至 2026-08-25 的严格检索结果。 | **高**：当前决策边界。 |

综合全部证据，最稳健的技术表述不是“LLM 需要事件图”，也不是“LLM 已经让图过时”，而是：

**当任务需要把很多分散文本中的“发生了什么、何时发生、是否为同一事件、先后/因果如何、后续如何更新”变成可反复检索和操作的长期状态时，显式事件结构有已经被实验和工业系统部分验证的价值；当任务只是局部问答、一次性生成、图质量差或索引无法复用时，这一价值会下降甚至被构图成本与噪声抵消。** EventRAG、CGEP、TAG-EQA、CGEL提供前半句的 event-specific 证据；GraphRAG 公平重评、ReGraphRAG、LazyGraphRAG和产业成本优化提供后半句的边界证据。citeturn24search1turn24search3turn25search0turn24search0turn26academia33turn26search0turn26search10

而对 LLM/Agent 工程人才价值，当前可证的信号更加明确：**值得积累的是事件/实体解析、temporal/provenance data modeling、graph/vector hybrid retrieval、agent/tool workflow、evaluation/observability 和可维护的数据管道这些组合能力；“事件图谱”本身不需要被硬凑成职业标签，更不应由招聘或风险产业需求反向决定论文的学术问题。** 当前招聘页与风险 benchmark 审计同时支持这个边界。citeturn17view0turn17view2turn14view1turn17view3 fileciteturn0file1