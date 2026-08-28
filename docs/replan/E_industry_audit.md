# DR-E 本地交叉核验

> 核验日期：2026-08-25（Asia/Taipei）
>
> 原始报告：`docs/replan/E_industry.md`
>
> 来源导出：`docs/replan/E_industry.pdf`

## 结论

DR-E 可作为后续综合输入，本轮验收状态为：**有条件通过**。

报告最重要的边界成立：显式事件图在 LLM 时代是 **conditional infrastructure**，不是所有任务上的
普遍赢家。现有 event-specific 直接实验证据主要支持跨文档事件组织/检索、长文档事件结构生成，
以及给定事件因果或时间图后的下游推理；逐事实 provenance、自动增量更新、最终生成降幻觉和
event-specific 降本仍主要是设计动机、一般 KG/GraphRAG/agent-memory 邻近证据或未闭合问题。

工业证据可以证明 graph、entity resolution、实时风险数据与调查工作流有商业价值，也能取得至少一个
带 event-like transaction node 的生产案例；但它不能证明 NLP 意义上的 occurrence-level event graph
已经广泛生产部署，更不能补上 D 已确认缺失的供应链/大宗商品公开 benchmark 闭环。

招聘证据可以证明一组贴近本课题的 production structured-AI 技能确实同时出现于在招岗位，但不是
市场统计。对作者最有价值的是 event/entity resolution、temporal/provenance modeling、graph/vector
hybrid retrieval、agent/tool workflow、evaluation/observability 和可维护数据管道，而不是把
“事件图谱”包装成职业标签。

E 不引入新的论文主 benchmark，也不改变 D 的候选排序。它提供的是“为什么条件性值得做”以及
“哪些工程能力可迁移”的外部边界，不能单独决定重构还是重开。

## PDF 来源恢复

- Markdown 共 181 行、51,985 bytes，保留 170 个 ChatGPT 内部 citation token，同时含 17 个原始
  HTTPS URL。
- PDF 共 21 页，由 WeasyPrint 生成，有可搜索文本层；含 240 个 URI 注释、45 个唯一 URI。
- 本轮以 Markdown 保留完整表格和正文，以 PDF 注释恢复论文、公司、招聘与项目的一手 URL。
  原始 Markdown/PDF 均未修改。
- PDF 是否有视觉表格截断不影响本轮审计，因为表格内容以 Markdown 为准；没有用 PDF 版式恢复
  任何实验数字。

## 技术存在理由核验

| DR-E 主张 | 核验结果 | 必须保留的边界 |
|---|---|---|
| 跨文档事件组织与结构化检索有直接证据 | **确认** | EventRAG 是 event-specific 方法，但公开仓库缺论文问题、输出与 evaluator；它证明方法存在，不构成完整公开 event-GraphRAG benchmark。 |
| 给定事件因果/时间图可参与下游推理 | **确认** | CGEP、TAG-EQA、CGEL 覆盖 ranking、最终 QA 与 graph-supported reasoning；gold graph/最终答案收益不能外推为自动构图端到端净收益。 |
| 长文档显著事件图能够自动生成 | **确认** | CALLMSAE/NYT-SEG 有直接图生成实验；缺 HGS evaluator、许可与训练输入边界，且不能证明最终 QA/RAG 必然受益。 |
| “有图”即可审计来源、降低幻觉 | **不成立，报告已正确否决** | 现有优先论文没有独立 gold provenance-chain correctness；自动抽取/合并/补边还可能把错误固化为结构。 |
| event graph 天然支持低成本推理 | **未核实，报告已正确降级** | 一般 GNN-RAG、LazyGraphRAG 或工程构图成本证据不能替代 event-specific cost-quality 对照。 |
| 动态 graph memory 证明 occurrence-level event graph 增量维护已解决 | **不成立，报告已正确区分** | Graphiti/Zep、AriGraph 是重要邻近证据，但没有统一监督新增、合并、修正、失效事件/边的 event-specific protocol。 |
| GraphRAG 的边界证据等于“图已经无用” | **不成立，报告未作此夸张** | 更稳健的结论是收益依赖 query distribution、图质量、评测设计与索引复用；不是 vector RAG 的普遍胜利。 |

上述论文身份、任务、表格口径与仓库缺口已在 `A_terrain.md`、`B_datasets_audit.md` 和
`C_methods_code_audit.md` 逐项核验，本轮没有重复下载全部论文。E 对这些既有证据的转述没有发现会
改变综合决策的冲突。

## 工业案例核验

### Altana：最强但仍需限定的严格案例

- [Altana 2024 美国政府公告](https://altana.ai/resources/altana-atlas-now-available-to-u-s-government-agen)
  在本轮返回 HTTP 200，正文明确称平台已部署于美国政府多个场景，包括 U.S. Customs and Border
  Protection。故“生产部署存在”可以确认。
- [Altana Product Network schema 文档](https://docs.altana.ai/concepts/altana-product-network/article.html)
  是 PDF 恢复的一手入口。原始 E 据此将 shipment 识别为 graph node；本轮读取该页遇到 SSL
  unexpected EOF，因此不把“shipment-as-node”写成二次独立闭合，只按可追溯的一手文档引用保留。
- Altana 当前页面还含 5,000+ CBP agents 等规模描述。它是公司自报快照，不是第三方效果评估，
  不进入论文方向或方法优劣判断。
- shipment 可以视为现实 transaction/event-like node，但它不是 NLP event mention schema；Altana
  不能成为“事件抽取 benchmark 已工业验证”的证据。

### 其他 graph 风险平台

Quantexa、Recorded Future、CrowdStrike 的官方产品材料足以支持“graph/KG + entity/contextualization
+ streaming risk/security data 是真实商业系统”，但公开 schema 不足以确认 occurrence-level
event-as-vertex。报告把它们保留为邻近生产证据而非严格事件图，这一分类通过。

AWS Bedrock Knowledge Bases GraphRAG/Neptune 可证明一般 GraphRAG 基础设施已产品化；fraud 或
suspicious-transaction 参考场景不等于已核实的 event-node 客户生产 schema。Neo4j 日本地震 KG
只作为会议工程展示/demo，不作为生产灾害响应证据。两项边界均保留。

因此，工业案例支持的是：动态风险系统愿意为结构化关联、身份、时间、上下文与调查工作流付费；
它不支持“严格 NLP 事件图已经普及”，也不补足公开学术比较轴。

## 招聘信号核验

原始表有 15 个技能分类条目，其中 Inca Digital 同一岗位出现两次，约对应 14 个独立职位。该集合没有
抽样框、历史序列或全市场分母，只能报告“抓取日最低可证需求”，不能变成职位占比或增长趋势。

本轮重点复核了最贴题的两份 Outreach 官方职位页：

- [Staff Applied Scientist — Knowledge Graphs & AI](https://jobs.lever.co/outreach/4ef30219-4dd5-4f40-b3b8-76c3c2277ebb)
  返回 HTTP 200；正文同时出现 entity resolution、temporal modeling、coreference/relation extraction、
  event detection、KG reasoning、production monitoring 与 data drift。
- [Director of Applied Science and Engineering — Knowledge Graphs & AI](https://jobs.lever.co/outreach/dc29c7f1-d7ef-431f-a35a-173dac2a4138)
  返回 HTTP 200；正文同时出现 entity resolution、temporal reasoning、event detection、KG
  architecture、evaluation 与 research-to-production pipeline。

这两页足以确认一条高度贴题的技能组合真实存在，但不能证明“事件图岗位很多”。其余 LangChain、
Recorded Future、Inca Digital、Mem0、Samba TV、GHX、Hadrian、Sentra、Airbnb 等条目保留为报告的
一手页面快照，本轮没有逐页二次抓取。Airbnb 的统计因果岗位尤其不能用于支持 event causality 市场。

综合时只采用以下招聘结论：

1. 市场购买的是完整的 structured-AI production pipeline，不是“会画事件图”的标签；
2. agent 工程已包含 tool/workflow/evaluation/latency/cost，而不只是模型调用；
3. KG 更常作为 RAG、agent、risk-data 或 contextual AI 的 substrate；
4. 这些事实支持技能建设，不构成论文选题证据。

## 开源活跃度核验

- C 的本地仓库审计已独立确认 EventRAG 21★、CALLMSAE 4★、SeDGPL 5★、TAG-EQA 0★及其当前
  commit/发布包缺口；E 与 C 的更正版本一致。
- 本轮对 Microsoft GraphRAG、Graphiti 的 GitHub API 访问返回 403。不能把 403 当仓库失效，
  也不再重复网络请求。E 中精确 stars、release 与最近提交只保留为 2026-08-25 快照。
- 后续综合不依赖 GraphRAG/Graphiti 的精确 star 数，只保留弱得多但合理的定性结论：通用
  GraphRAG 与 agent temporal-memory 项目呈现持续工程化生态，event-specific 仓库更像论文资产。
- stars、issues、release 或 commit 均不能证明企业采用率、论文质量、研究价值或职业需求规模。

## 可进入五路综合的稳定输入

1. **直接技术价值：**跨文档事件组织/检索、显式事件因果/时间结构参与下游推理；
2. **尚未闭合的价值：**provenance correctness、事件级增量更新、最终生成降幻觉、同质量降成本；
3. **统一边界：**显式图是依 query、图质量和复用成本而定的条件性基础设施；
4. **工业信号：**risk/intelligence/supply-chain 系统需要关联、身份、时间、来源和增量数据，但公开
   event benchmark 并未随之成熟；
5. **人才信号：**最可迁移的是 structured data engineering、hybrid retrieval、agent/tool workflow、
   evaluation/observability 和 LLM+小模型/数据系统协同；
6. **对候选方向的影响：**E 不新增主 benchmark，不改变 D 中 ESL/CTB ECI 为最强条件性候选、
   固定协议 MAVEN-ERE 为第二候选的排序。

## 不进入最终决策的内容

- 公司自报的精确图规模、events/day、样本量或用户数；
- 未公开 schema 的平台是否存在 occurrence-level event node；
- 14 个职位样本的数量、地区分布或所谓市场占比；
- GitHub stars 的绝对差值及由此推导的采用率；
- general KG/GraphRAG/agent-memory 的收益对 event graph 的直接外推；
- “工业需求强，所以风险监测应成为论文主 benchmark”的反向论证。

## 一手来源入口

- [EventRAG](https://aclanthology.org/2025.acl-long.830/)
- [CALLMSAE](https://aclanthology.org/2025.naacl-long.112/)
- [CGEL](https://aclanthology.org/2025.acl-long.1269/)
- [CGEP / SeDGPL](https://aclanthology.org/2024.findings-emnlp.45/)
- [TAG-EQA](https://aclanthology.org/2025.starsem-1.24/)
- [LoCoMo](https://aclanthology.org/2024.acl-long.747/)
- [AriGraph](https://www.ijcai.org/proceedings/2025/0002.pdf)
- [Zep / Graphiti paper](https://arxiv.org/abs/2501.13956)
- [Microsoft GraphRAG research](https://www.microsoft.com/en-us/research/publication/from-local-to-global-a-graph-rag-approach-to-query-focused-summarization/)
- [Altana government deployment](https://altana.ai/resources/altana-atlas-now-available-to-u-s-government-agen)
- [Altana Product Network schema](https://docs.altana.ai/concepts/altana-product-network/article.html)
- [Outreach Staff KG & AI role](https://jobs.lever.co/outreach/4ef30219-4dd5-4f40-b3b8-76c3c2277ebb)
- [Outreach Director KG & AI role](https://jobs.lever.co/outreach/dc29c7f1-d7ef-431f-a35a-173dac2a4138)
- [Microsoft GraphRAG repository](https://github.com/microsoft/graphrag)
- [Graphiti repository](https://github.com/getzep/graphiti)

## 验收边界

本轮没有穷尽 2024–2026 的所有工业案例、公司 schema、招聘页或 GitHub 历史，也没有独立审计公司
自报规模的真实性。Altana schema 页未成功二次读取，Microsoft GraphRAG/Graphiti 的 GitHub API
因 403 未闭合精确快照；其余招聘条目也没有逐一重复抓取。这些缺口不妨碍把 E 作为“技术存在理由
+ 工业/人才边界”的合格输入，因为最终综合不依赖这些精确数字；但它们会阻止“事件图广泛生产”、
“岗位市场正在增长”或“OSS star 等于采用率”等强结论。
