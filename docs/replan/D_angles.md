# NLP 研究方向可行性审计：跨语言事件图谱、风险事件与替代切口

## α 可行性报告

**总判定：切口 α 作为“跨语言/多语言事件图谱”整体主轴，目前不满足你的硬约束。** 问题本身有明确研究价值，但证据链在“多语言抽取 → 跨语言同一现实事件对齐 → 统一事件节点/图 → 固定下游评测”中间发生了断裂。现有公开资源最成熟的是**多语言事件抽取和 zero-shot 迁移**；“不同语言的独立报道是否指向同一现实事件节点”的 gold 数据则极少。MCECR 尤其容易被误读：它是 multilingual cross-document ECR，但其相关报道检索被限制在**与 seed article 相同的语言**，因此不能拿它冒充跨语言事件节点对齐数据。citeturn17view1turn5view3turn6view8

这里把“2024–2026 独立方法数”解释为**截至 2026-08-25 本轮能够以一手论文确认的保守下界**；“独立 follow-up”与“数据论文自己适配若干 baseline”分开。你已有的数据审计也指出，任何 `0*` 都只能写作“本轮严格检索未发现”，不能写成全领域绝对零。fileciteturn0file0

| α 子类 | 可核公开资源及 gold | 语言与规模 | test / evaluator | 2024–2026 竞争密度 | 27GB | 审计结论 |
|---|---|---|---|---|---|---|
| 多语言事件抽取、论元、关系 | **MEE**：entity mention、event trigger、event argument；并不是 event-event relation 数据。MEE 共 8 种语言，统一 ACE 衍生 schema。citeturn15search12turn5view0 **MINION**：event detection，仅 trigger，不含 argument graph。**EusIE** 是 2024 年 Basque 扩展。citeturn15search3 **SPEED++** 是 2024 EMNLP 的多语言疫情 EE。citeturn19search3 | MEE：en/es/pt/pl/tr/hi/ko/ja；31,226 个五句 segment、50,011 个 trigger、38,748 个 argument。citeturn5view0 MINION 同 8 语，31,226 segments、约 50.9K triggers。citeturn2search2turn6view3 EusIE：Basque，300 segments，作为 MEE schema 的评测扩展。citeturn15search3 SPEED++：4 语、约 5.1K tweets。citeturn19search3 | MEE 论文使用按语言 80/10/10 划分，同一原文章节不跨 split；主结果是 entity/event/argument P/R/F1，正确性要求 span/type 等条件匹配。citeturn6view0turn5view1 **但本轮没有成功取得 MEE/MINION 当前官方数据仓库和一个可执行、版本锁定的 scorer，因此当前只给“论文 protocol 已核、现行测试资产待核”。** EusIE 论文明确说数据与代码公开。citeturn15search3 | 宽泛“multilingual EE”至少有 EusIE、SPEED++ 等正式工作；TransFusion 2025 还做 cross-lingual IE，但其 ACE05 部分不满足开放数据硬约束。citeturn10search5turn24search0 **真正对 MEE/MINION 做独立、同 benchmark 的 2024–2026 follow-up，本轮只明确找到 EusIE 这一条，未形成多个独立方法的严格时间线。** | MEE/MINION/EusIE 的 mBERT/XLM-R 类方案属于低风险；encoder 训练显著低于 27GB 门槛。TransFusion 的论文 recipe 是 7B QLoRA 且使用 2×A40 48GB，不是 27GB 实测。citeturn14view1 | **局部可做，但不满足“每章多个近年正式方法同口径”这一最严格要求。** |
| zero-shot 跨语言迁移 | MEE 原论文有 English→other-language zero-shot；EusIE系统研究了跨语言 transfer；SPEED++ 做 English COVID → 其他语言/疾病；2024 还有 zero-shot cross-lingual document-level ECI。citeturn6view1turn6view2turn15search3turn19search3turn22search10 | MEE target 覆盖另外 7 语；EusIE 把 Basque 加入，并做大量 source-target 对；SPEED++ 的人工 gold 是 4 语，模型进一步在更多语言上部署，但这些部署语言并不等价于都有 gold test。citeturn15search3turn19search3 | MEE Table 7 的定义是 English train → 其他语言 test；这是**迁移**，不是跨语言事件节点融合。citeturn6view1turn6view2 各论文任务、schema 和 test 不同，因此不能把它们的 F1 横排成一个排行榜。 | 宽泛 zero-shot cross-lingual event 方向至少有 3 个独立正式实例可确认：EusIE、SPEED++、cross-lingual document ECI；另有 TransFusion，但后者的重要 ACE 部分受 LDC 许可约束。citeturn15search3turn19search3turn22search10turn24search0 **同一个开放 benchmark 上的近期独立方法密度仍不足。** | encoder-based transfer 很合适；7B translation/fusion 方法需要单独显存探针。 | **问题有价值，工程可行；benchmark 成熟度不足以自动升级成最终主切口。** |
| 多语言联合训练 | MEE 的统一 schema 理论上允许 pooled multilingual training；EventKG 等资源也具有多语言统一表示，但它们回答的是不同任务。citeturn15search12turn16search7 | MEE 8 语；EventKG 聚合多语 Wikipedia/Wikidata/DBpedia 等来源。citeturn16search7 | **本轮没有找到 2024–2026 形成固定“multilingual pooled train → fixed multilingual test → common evaluator”赛道的 MEE/MINION 独立论文链。** 自己把 MEE 8 语 pool 在一起当然能实验，但那会成为自定义 protocol，而不是已存在 benchmark。 | 严格 follow-up 下界：`0*`，即本轮未取得满足“多个正式独立方法、相同 pooled protocol”的证据。 | XLM-R/mBERT 联合训练本身容易落在 27GB 内。 | **算力没有问题，缺的是公开比较制度。** |
| 跨语言事件对齐 / 跨文档共指 | **MEANTIME** 确实有 cross-document entity/event coreference，并通过英文与西/意/荷翻译间的投射得到 cross-lingual coreference。citeturn15search7 **MCECR** 有 5 语、5,802 篇新闻和 event/coreference gold。citeturn17view1 | MEANTIME：480 文档，即 120 篇英文 Wikinews 及其西/意/荷译文。citeturn15search7 MCECR：en/es/hi/tr/uk，5,802 docs。citeturn17view1turn5view3 | MEANTIME 的核心问题是它主要是**平行翻译版本**，不是“不同语言媒体独立报道同一现实事件”。citeturn15search7 更关键的是 MCECR：论文的数据收集过程明确将 related-article 搜索限制为 seed article 的**相同语言**；其 cross-lingual 实验实际是“English train → 另一语言 test”，而不是把英语报道和土耳其语报道聚成同一 event node。citeturn5view3turn6view8 | **2024–2026 真正符合“不同语言报道 → 同一现实事件节点 gold”定义的独立正式方法，本轮严格检索为 `0*`。** MCECR 原论文不能算，因为它的 gold cluster 不是跨语言混合 cluster。 | MCECR 的 XLM-R 级模型技术上可在单卡运行；但算力无助于解决 gold 缺失。 | **这是 α 的致命瓶颈。公开数据稀缺，应当直说。MCECR 不能替代该任务。** |
| 多语言 event graph 的统一 schema / 构建 / 下游 | EventKG 是真正的 multilingual event-centric KG，融合 Wikidata、DBpedia、YAGO、Wikipedia Current Events 等，并提供统一 RDF 表示与公开 SPARQL。citeturn16search7 但它不是“从多语言独立新闻报道抽取并对齐同一事件节点”的 supervised NLP benchmark。 | EventKG 支持多语源，并存在构图 pipeline；其配置还需要源属性映射及语言时间表达规则。citeturn16search7 | 没有找到一个 2024–2026 成熟 benchmark 同时提供“多语 raw text → event extraction → cross-language node resolution → graph relation gold → downstream fixed test/evaluator”。EventKG 更像资源/基础设施，而不是这条链路的固定 benchmark。 | 本轮为 `0*` 个满足全部条件的成熟近年赛道。LEMONADE 的公开仓库提供 20 语 abstractive EE，但它仍是 event extraction，而不是上述跨语言 node-fusion graph benchmark；其正式 venue 本轮也未锁定，因此不能补这个缺口。citeturn16search1 | 使用现成 EventKG 做图查询容易；从大规模 dumps 重建图需要 CPU/RAM/存储，GPU 27GB 不是主要瓶颈。citeturn16search7 | **不建议把“多语言资源存在”表述成“跨语言事件图融合 benchmark 已成熟”。二者不是一回事。** |

MEE 本身是 α 中最容易被高估的资源。它确实非常适合研究**同一 schema 下的多语言 ED/EAE 与 transfer**：8 个语言共享 8 个 coarse event types、16 个 subtypes 和 23 个 argument roles，并且论文专门给了 English→target 的 cross-lingual 表。citeturn5view0turn6view1 但它没有给“英语 `earthquake` mention 和西语另一篇新闻里的 `terremoto` mention 属于现实世界同一次地震”的跨文档、跨语言 node identity gold。因此，用 MEE 做多语言 EE 后再自己 entity/event-link 到一张图，是一个**新实验协议**，不是现成“跨语言事件图谱”公开 benchmark。citeturn15search12

MINION 更窄：它解决 multilingual event detection，而不是 arguments、event relations 或 cross-language coreference；所以它可以支撑 trigger transfer，却不能补 α 后半段。citeturn2search2

MCECR 是本次核查中最重要的反直觉结果。它标题中的 “Multilingual Cross-Document Event Coreference Resolution” 很容易让人推断出 language-mixed clusters；实际并非如此。其五种语言分别构建主题集合，相关文档搜索限定为 seed 的语言；所谓 cross-lingual setting 是在一种语言训练、另一种语言测试模型泛化。citeturn5view3turn6view8 此外其 coreference annotation 还混合了自动高置信标注与人工标注，作者报告了抽检质量，但这仍是做 label-quality 审计时应保留的 provenance 信息。citeturn5view4

ACE05 也不能救 α。LDC 官方条目明确写明整个 ACE 2005 Multilingual Training Corpus 包含 English、Mandarin Chinese、Arabic，但 **event evaluation 只在 English 和 Chinese 上进行**；同时数据受 LDC User Agreement 和会员/非会员许可约束，不符合这里“公开数据、无需购买或机构授权”的硬条件。citeturn24search0

**因此 α 应拆成两个判断。** “多语言/zero-shot EE”是真实、可运行的方向；“跨语言不同报道的同一现实事件对齐 + unified event graph”则当前缺公开 gold 和成熟近期比赛口径。不能因为前者资源丰富，就宣称后者已经具备 benchmark 条件。

## β 可行性报告

**总判定：β 的问题价值很高，但作为“供应链中断/大宗商品/经济风险事件 → 风险传播/预警”的公开 NLP benchmark 主切口，目前同样没有闭合证据链。** 与 α 不同，β 的问题不是完全没有领域数据，而是已有资源分散在三个互不等价的层面：领域事件抽取数据、结构化风险事件数据库、以及少量应用型早期预警案例。它们目前没有自然拼成一个有多个独立正式方法、固定时间切分和公开 evaluator 的统一 benchmark。

### 领域事件抽取资源

真正命中“大宗商品”的资源是 **CrudeOilNews**。LREC 2022 论文将其定义为 English crude-oil news event extraction corpus：425 篇新闻、约 11K annotated events，最初 175 篇人工标注，其中 25 篇作为 adjudicated reference test。citeturn21view0 它的 event ontology 也确实包含供应、短缺、供给增加/下降、需求变化、制裁、贸易紧张、宏观经济、价格变动等，对“大宗商品风险事件”比 MAVEN 之类通用语料语义上自然得多。当前 GitHub 仓库仍公开，仓库许可证元数据为 MIT。fileciteturn4file0L1-L2

但这里发现了一个**高影响硬伤**：当前官方仓库 README 明确说明，因版权问题，原始 commodity news **不提供正文，只提供原新闻 URL 及相应 annotation；只有 augmented data 能完整提供原文**。fileciteturn6file0L1-L2 当前仓库顶层能看到 annotation、annotation guideline、README 和 license，但没有一个类似成熟 shared task 的 public evaluator / leaderboard 结构。fileciteturn5file0L1-L2 这意味着 CrudeOilNews 在“公开 gold annotation”意义上存在，在你要求的“任何人今天即可拿到同一 raw input + gold test + scorer”意义上却是**不完整公开**。而且本轮未找到 2024–2026 多个独立正式 follow-up 在其 25-document reference test 上形成统一主指标，因此不能把它称作当前成熟 commodity benchmark。citeturn21view0

2024 年出现了若干金融 EE 数据，但它们不能被偷偷改名成“供应链风险 benchmark”。**OEE-CFC** 是 Chinese financial commentary open event extraction，包含 17,469 events 和 44,221 arguments，强调复杂论元、共享论元和开放 event template；其 gold 目标是金融文本的事件结构，不是中断传播或预警。citeturn18search0 **FINEED** 则面向 Chinese Financial Text-to-Event extraction，关注从 raw financial text 中直接抽取事件；同样是 EE，而不是 supply-chain disruption forecasting。citeturn18search1 **EFSA** 做的是 event-level financial sentiment，公开任务输出 company/industry/event/sentiment 等结构，但风险传播和中断并不是其 gold target。citeturn18search3

**FORCE** 比上述资源更接近“风险事件”：它从 2011–2023 新闻中抽 foodborne outbreak 与 recall，作者明确把食品安全事件放在 food supply chain 语境，并强调 contamination origin/pathway 对 prevention 和 mitigation 的价值。citeturn21view1 然而论文只说 dataset “will be publicly released”；本轮对 GitHub 的精确仓库检索没有取得官方 release，ACL 页面也没有当前下载入口，因此应记为**发表身份已核、现行数据/test 未取得**，而不是“公开 benchmark 已验证”。citeturn21view1

因此在**供应链中断 / commodity / financial-risk EE**层面，目前能确认的是“资源有”，不能确认“有一个满足最终章硬约束的成熟赛道”。CrudeOilNews 语义最贴近，但原始文本版权和近期对手密度不足；OEE-CFC/FINEED/EFSA 更公开、更新，但任务语义不是中断传播；FORCE 语义接近，却没有核到完整当前公开 benchmark 包。citeturn21view0turn18search0turn18search1turn21view1

### 通用事件数据库不能自动变成“风险 benchmark”

| 通用资源 | 实际 gold / 数据性质 | 能否直接称“经济/供应链风险 benchmark” | 许可与风险 |
|---|---|---|---|
| MAVEN / MAVEN-ERE | Wikipedia 文档上的通用 event type / event relation annotations；MAVEN-ERE 有 coreference、temporal、causal、subevent 等统一关系。官方 repo 当前仍包含 data、各子任务代码与 `evaluate.py`。citeturn16search10 | **不能。** 本轮未取得一手正式论文把一个固定的 supply-disruption / commodity-risk event-type 子集定义成公开、固定、带 evaluator 的 benchmark。自己筛几个事件类型只能叫自定义实验子集。 | MAVEN-ERE 本身公开且工程资产较完整；但 evaluation protocol 在 2024–2025 已经分裂，详见后文。fileciteturn0file0 |
| ACE05 | 人工高质量 entity/relation/event corpus。citeturn24search0 | 既没有本轮核到固定 risk subset，而且**数据本身就不符合开放获取硬约束**。 | LDC User Agreement；event task 仅 en/zh。citeturn24search0 |
| ACLED | 结构化冲突、抗议、政治暴力等事件数据库；ACLED 官方明确说其数据实际被用于 risk assessment 和 early-warning initiatives。citeturn24search18 | 可以作为**风险应用数据**，但这不等于 NLP event extraction 的 gold test，也不等于 commodity/supply-chain risk label。若自行选择某些 ACLED event types 作为“经济风险”，就是新定义。 | 当前使用受 2025-07-08 版 EULA、Content Usage Terms 与 attribution policy 约束，需要注册并遵守用途限制。citeturn24search5turn24search15 |
| GDELT | 大规模 machine-coded global event stream / GKG；官方称整个数据库 100% free and open，可下载或 BigQuery。citeturn24search4 | **不是 gold event extraction benchmark。** 机器编码记录可以作弱监督、外部知识或时间序列输入，但没有本轮核到固定“供应链风险 target + human gold + evaluator”的赛道。 | 数据开放是优势；标签噪声与事件重复/聚合策略必须作为实验变量，而不能把机器编码记录直接称 gold。后一句是本审计的质量边界，而非官方质量保证。citeturn24search4 |
| EM-DAT | 经过验证的 disaster event / impact 数据，而非文本 EE corpus。官方文档称 public data 更新并提供 validated figures。citeturn24search14 | 可以做灾害 outcome / external event registry；**不是文本中的供应链中断 gold**。把新闻事件连接到 EM-DAT 再定义预警，是一个新 benchmark 构造问题。 | Public portal 需注册，非商业使用免费；官方推荐的 Archive 为 CC-BY-NC-ND。citeturn24search1turn24search6 |
| SPEED（Cline） | 这里应指 **Social, Political and Economic Event Database Project**；其 societal-stability protocol 包含 impact、consequence、reaction、subsequent events 等数百项 event-specific queries。citeturn19search7 | 从语义上非常“风险事件化”，但本轮没有核到一个公开 NLP train/test/evaluator 包，也没取得 commodity-risk fixed subset 的近期正式方法链。 | 数据发布/许可/test 当前没有完成核验，因此不能标“硬条件通过”。 |
| ICEWS | 结构化政治事件资源。 | 本轮没有完成当前官方 distribution、license、2024–2026 risk-subset benchmark 与 evaluator 的一手审计，因此**不作通过判定**。 | 记入“未核实”，不凭历史印象补结论。 |

这里有一个名称冲突必须避免：用户列表里的 **SPEED** 很可能是 Cline Center 的 *Social, Political and Economic Event Database*；而 NLP 领域 2024 还有另一个 **SPEED/SPEED++**，后者是 epidemic event extraction / early warning。两者完全不是同一数据集。Cline SPEED 的官方页面是社会政治经济事件编码项目；SPEED++ 则是 EMNLP 2024 多语言疫情 EE 工作。citeturn19search7turn19search3

### “事件 → 风险/传播/预警”有没有公开任务先例

答案不是“完全没有”，而是**有应用先例，但与你要的经济/供应链 benchmark 不同域，而且通常没有多个独立方法共享同一 evaluator**。

最明确的一手先例是 **SPEED++: A Multilingual Event Extraction Framework for Epidemic Prediction and Preparedness**，EMNLP 2024，Anthology ID `2024.emnlp-main.720`。它从社交媒体抽取 epidemic events，再将事件随时间聚合用于 early warning；论文把 zero-shot cross-lingual / cross-disease EE 直接连到 epidemic preparedness。citeturn19search3 这证明“event extraction → time aggregation → warning”本身是一个真实、可发表的问题，而不是虚构应用；但它不证明“供应链风险预警已有公开 benchmark”。其 warning 部分更接近 application validation，而不是一个多个团队反复提交的 shared evaluator。citeturn19search3

ACLED 也有明确的 risk-analysis / early-warning 使用价值，但官方自己同时强调其空间、时间粒度和用途边界。citeturn24search18 因而它适合被视为**external event/outcome source**，不应直接被改写成“事件抽取 → 风险预测”的监督标签体系。

在本轮证据中，没有取得这样一个同时满足下列条件的公开经济/供应链任务：新闻中的 event gold；固定的 disruption/risk outcome；严格 time cutoff；公开 train/dev/test；公开 lead-time / propagation evaluator；至少两个独立 2024–2026 正式方法。**因此 β 不能靠把 MAVEN/ACLED/GDELT/EM-DAT 中“看起来像风险”的类型筛出来来解决 benchmark 缺口。**

### 泄漏与时间切分是 β 的一级风险

β 比普通 EE 更容易产生“看起来很高但无效”的结果，因为输出带有未来含义。严格预警实验至少需要保证：输入文档的 publication timestamp 在预测 cutoff 之前；任何 outcome registry 的后续修订不能进入 feature；同一现实事件的后续复盘报道不得随机落入 train 而早期报道落入 test；同一新闻转载、聚合稿、近重复文本必须防跨时间 split 泄漏；lead-time 必须以首次可观测输入与真实 outcome 时间定义，而不是以事后选出的“最早相关报道”倒算。这些是要把“预警”解释为真正 prospective evaluation 必须满足的实验条件。

CrudeOilNews 尤其存在额外问题：其原始新闻正文因版权不随仓库发布，只留下 URL 和 annotation；随着网页失效、修改或 paywall 变化，未来复现实验得到的 raw input 可能不一致。fileciteturn6file0L1-L2 所以即使不做价格预测，它也不是一个理想的长期固定 test artifact。

**β 的最终审计结论是：问题价值通过，公开 benchmark 成熟度不通过。** 大宗商品并不是你的硬约束，因此没有必要为了保留“大宗商品”而接受一个原文不完整、近期严格对手不足的 benchmark。更合理的定位是把风险监测保留为应用延伸，而主研究问题使用已有稳定 gold 的 event reasoning / relation task；这不是“因为风险方向对手少”，而是因为当前证据无法满足你自己规定的公开 test 与同口径正式比较条件。

## 替代切口证据表

本轮真正从 2024–2026 证据里筛出两个比 α 整体和 β 整体更自然的切口。没有强塞第三个：NYT-SEG/CALLMSAE、CGEP/SeDGPL、TORQUESTRA/TAG-EQA 等新 event-graph 任务都有真实研究价值，但现阶段各自存在许可、派生数据、fixed test 或 evaluator 缺口；你已有本地审计也明确指出它们尚不能无保留满足“公开完整复现包 + 多独立近年方法 + 统一 evaluator”。fileciteturn0file0

| 替代切口 | 栏 A：真问题价值 | 栏 B：竞争密度与同口径基础 | 数据与 test 可得性 | 单卡可行性与关键风险 |
|---|---|---|---|---|
| **可验证的文档级事件因果识别 / event causality reasoning**，以 EventStoryLine + Causal-TimeBank 为成熟主 test，MAVEN-ERE causal 作为规模扩展 | 2024 NAACL long paper *Event Causality Is Key to Computational Story Understanding* 明确把 event causality 视为 story understanding 的关键缺失，并报告还有大量未被利用的潜力；这是“真问题价值”而不是竞争稀疏性论证。citeturn22search3 2024 ACL 的 document ECI 和 EMNLP 的 synthetic-control ECI 继续把长上下文、因果方向和虚假相关性作为核心难点。citeturn22search4turn22search1 | 至少可以确认 **3 个互相独立的 2024–2025 正式团队**在 ESL/CTB 这组成熟数据上继续做方法：ICCL/EMNLP 2024 的 in-context contrastive ECI；COLING 2025 的 LLM-knowledge/concept-level ECI；EMNLP 2025 的 DICP。citeturn22search9turn23search10turn22search7 DECLV 2025 也是正式方法，但与 Su et al. 2025 有作者团队重叠，因此不把它虚增为额外独立团队。citeturn22search8 **这里不报任何 performance 数字**，因为不同论文的具体 fold 文件、negative-pair generation 和 evaluator 尚未逐项锁定。 | Causal-TimeBank 当前官方/作者 GitHub 可下载，含 6,811 EVENT 与 318 CLINK 等 annotation。citeturn23search2 PPAT 与 MAVEN-ERE 官方代码都直接提供/引用 ESL、CTB 数据处理；MAVEN-ERE 官方 causal README 明确规定 CTB 10-fold CV、ESL 5-fold CV，并提供运行入口。citeturn23search0turn23search6 DICP 官方仓库也直接链接两数据并公开 preprocessing/run 流程。citeturn23search8 **主要剩余核查点是不同论文是否使用完全同一 fold ID 与 pair-generation，而不是数据拿不到。** | PPAT 是 BERT-base 级模型；DICP 增加 AMR preprocessing，但并不要求 70B 模型。citeturn23search0turn23search8 因而单 27GB 卡是高可行性候选。关键风险不是显存，而是 ECI 文献的 negative sampling、direction/existence 定义和 CV folds 可能不完全统一；必须锁定协议后才报严格 SOTA。 |
| **固定协议的文档级统一事件关系抽取 / event graph relation reasoning**，以 MAVEN-ERE 为核心，而不是再包一层“多语言图谱” | MAVEN-ERE 原始动机正是既有 ERE 数据规模小、关系类型割裂，导致模型无法利用 coreference/temporal/causal/subevent 之间的交互；其 4,480 documents 同时注释这几类关系。citeturn16search10turn23search13 TacoERE 2024 又明确把 long-range dependency 与 document information redundancy 作为现实难点。citeturn23search9 这使研究问题直接落在“event structure/reasoning”，无需人为附会一个风险 domain。 | 2024–2025 正式论文使用 MAVEN-ERE/子任务的保守下界至少包括 TacoERE、Chen et al.、Wei et al.、KnowQA、LLMERE、MMD-ERE、Xiang et al.，但不能把它们全放进一个 leaderboard，因为 protocol 已分裂。经作者重叠更正后，本地审计确认独立团队下界仍 **≥4**。fileciteturn0file0 Chen 2024 与 LLMERE 2025 都采用“original train 8:2；original valid → test”，所以至少存在两篇正式独立工作共享这一大框架；但 LLMERE 论文中旧 baseline 是否全部在同一 split 重跑仍未锁死，因此还不能直接抄 headline F1 排序。fileciteturn0file0 | 官方 GitHub 仍公开 data、coreference/temporal/causal/subevent/joint 代码以及 `evaluate.py`。citeturn16search10 官方 CodaLab 页面在本地审计时仍可打开，显示永久竞赛/历史 submissions，但**未登录做真实新提交，因此不能宣称 2026-08-25 scorer 仍接受新 submission**。fileciteturn0file0 当前最大风险是至少四种 eval setting 共存：官方 hidden test、Chen/LLMERE valid-as-test、sampled LLM setting、Xiang causal-only setting。fileciteturn0file0 | encoder / seq2seq 方法风险低；MAVEN-ERE 的公开 baseline 工程规模适合单卡。LLMERE 论文则用了 A100 40GB、LoRA rank 64、max length 2048，所以它不能被当成“8B 已证明可在 27GB 训练”。fileciteturn0file1 7B/8B QLoRA 仍可作为工程候选，但必须 smoke-test；70B、多闭源 agent 不适合作为硬依赖。fileciteturn0file1 |

第一个替代切口比 α 的“跨语言 event graph”自然之处，不是因为“对手好打”，而是**研究对象、gold、指标和近期文献说的是同一个东西**：两个事件是否有因果关系、方向是什么。EventStoryLine/Causal-TimeBank 还有一个现实优势：不同近期方法继续沿用这些 benchmark，官方/作者代码生态也已经把 5-fold/10-fold protocol 显式固化。citeturn23search6turn23search8 风险监测可以自然成为因果结构的应用检查，但不需要先自造“风险 event type”。

第二个替代切口的优势则是把已有 MAVEN-ERE 的真实研究活跃度直接利用起来。需要强调：它是**有条件通过**，不是无条件通过。你已有 B/C 审计最重要的发现就是近期 MAVEN-ERE evaluation setting 已经裂成多支；如果把 headline F1 混排，会违反你自己要求的“paper title + ID + table + split + evaluator + metric definition”。fileciteturn0file0

本轮没有把 CALLMSAE/NYT-SEG、CGEP/SeDGPL、TAG-EQA/TORQUESTRA 作为第三替代切口。CALLMSAE 的 human test graph 可下载但 train text 依赖 Annotated NYT，且仓库缺 Hungarian Graph Similarity evaluator；SeDGPL 有 ESC 派生图与 scorer，但缺 MAVEN 派生文件/构图入口；TAG-EQA 缺论文所用派生数据与 fixed Full/Small test。fileciteturn0file0 它们证明“event graph 下游”是有价值的新问题，却还不满足你的最终 benchmark 硬条件。

## 问题价值与竞争密度分栏决策表

这张表刻意把“问题价值”与“竞争密度”分开。**竞争低不是拒绝理由；真正拒绝的是无法满足固定公开比较条件。**

| 候选 | 问题价值 | 近期竞争密度 | 严格公开比较成熟度 | 决策 |
|---|---|---|---|---|
| α：完整“跨语言事件图谱” | **高。** 多语言 EE 长期受高质量非英语资源不足影响；MCECR 2024 也明确指出 multilingual cross-document ECR 数据不足。citeturn17view0turn17view1 | **低到中，且分布在不同任务。** Multilingual EE/transfer 有新工作，但跨语言同事件 node alignment 基本断层。citeturn15search3turn19search3turn22search10 | **低。** 缺 natural multilingual reporting 的 cross-language event identity gold；MCECR 不是这个任务。citeturn5view3turn6view8 | **整体不通过。** 不是因为“对手少”，而是 benchmark 定义链不闭合。 |
| α 的窄版：zero-shot multilingual EE | **高。** EusIE 直接说明 typological transfer 仍有明显未解决因素。citeturn15search3 | **中。** EusIE、SPEED++、TransFusion 等说明持续活跃，但不共享 benchmark。citeturn15search3turn19search3turn10search5 | **中低。** MEE 自身很好，但 2024–2026 同一公开 split 上独立方法链偏薄；ACE又受许可限制。citeturn24search0 | **条件性可行，不足以据现证据确认最终主轴。** |
| β：供应链/commodity/economic-risk EE | **高。** CrudeOilNews、FORCE 乃至金融 EE 的持续数据建设都说明领域需求真实。citeturn21view0turn21view1turn18search0 | **低。** 资源多数是新数据论文或单项目，未形成近期独立方法序列。 | **低。** CrudeOilNews raw text 版权缺失；FORCE 当前 release 未核；金融数据又不等于 disruption benchmark。fileciteturn6file0L1-L2 citeturn21view1 | **作为主 benchmark 不通过；作为应用延伸有价值。** |
| β 的“generic event types → 自定义 risk subset” | 取决于风险定义，现实价值可以高。 | MAVEN/MAVEN-ERE 等原 benchmark 本身竞争很高。fileciteturn0file0 | **不通过。** 没有已发表固定 risk-subset 先例时，自筛类型不是公开 benchmark。 | **禁止包装成已有 risk benchmark。** |
| 替代：EventStoryLine/CTB 文档级 ECI | **高。** 近期论文明确把因果关系视为事件理解中的核心不足。citeturn22search3turn22search4 | **高于 α/β 的关键环节。** 至少 3 个独立 2024–2025 正式团队可明确确认继续使用 ESL/CTB。citeturn22search9turn23search10turn22search7 | **中高。** 数据和代码实际可访问，5/10-fold tradition 明确；尚需锁定 fold 文件、pair generation 和 evaluator 才能达到“严格”。citeturn23search2turn23search6turn23search8 | **目前证据最自然。** |
| 替代：固定协议 MAVEN-ERE | **高。** unified relation modeling、long-range dependency 都有一手证据。citeturn23search13turn23search9 | **高。** 2024–2025 正式使用论文很多，独立团队保守下界 ≥4。fileciteturn0file0 | **中。** 数据/evaluator 强，但 split 分裂严重、hidden submission 未实测。fileciteturn0file0 | **有条件通过；必须先冻结一个已有 protocol。** |

因此，“α/β vs 替代切口”的真正分界不是“哪个方向人少”，而是：

**α** 有较好的 upstream EE，却没有可靠的 cross-language node-level gold；  
**β** 有丰富现实风险信号，却没有固定 event→risk benchmark；  
**ECI** 已经同时拥有明确研究问题、公开 gold 和多个近期正式方法；  
**MAVEN-ERE** 已拥有规模、关系结构和近期方法，只剩 protocol fragmentation 需要治理。citeturn22search9turn23search6turn16search10

## 数据、test 与代码可得性日志

“公开”在这里拆成五个不同层次：论文可读、annotations 可下载、raw input 可下载、fixed test 可重建、evaluator 可执行。任何一层缺失都不自动写“公开 benchmark”。

| 资源 | 本轮实际访问状态 | fixed test | evaluator / leaderboard | 许可/文本 | 当前判定 |
|---|---|---|---|---|---|
| MEE | ACL 论文/PDF 已实际核，含数据统计、80/10/10 和 cross-lingual 表。citeturn5view0turn6view0turn6view1 | 论文 protocol 有；当前官方数据仓库未成功定位 | 当前 scorer 未实测 | 论文称数据公开；现行 distribution/license 未独立取得。citeturn17view0 | ⚠️ |
| MINION | 原论文/PDF 已核，multilingual ED 统计与 transfer 表已取得。citeturn2search2turn6view5 | 论文 split 可读；当前 artifact 未独立取得 | 未实测 | 当前 repo/license 未锁定 | ⚠️ |
| EusIE | 2024 LREC-COLING 正式论文已核；论文明确 dataset+code public。citeturn15search3 | 有 dev/test 设计 | 代码存在性由论文确认；本轮未运行 | Basque eval resource | ✅/⚠️ evaluator 未跑 |
| MCECR | 2024 Findings 论文/PDF已核；5-language statistics 与 data collection 已读。citeturn17view1turn5view3 | 论文 evaluation 有；当前 data package 未实际下载 | 当前 scorer 未取得 | 最关键的是 topics 不是 language-mixed | ⚠️；对 cross-language alignment 为 ❌ |
| MEANTIME | 正式 LREC 2016 一手页面已核。citeturn15search7 | 历史 corpus 有 | 当前固定 test/evaluator 未实测 | 平行翻译 corpus | ⚠️；自然跨语言报道任务为弱匹配 |
| ACE05 | LDC 官方 catalog 已访问。citeturn24search0 | 官方 evaluation 历史存在 | 非开放 shared submission | LDC User Agreement；需机构/付费许可路径 | ❌ 对“公开数据” |
| SPEED++ | EMNLP 2024 正式论文和项目页已核。citeturn19search3turn19search2 | 自有数据/实验 | 未取得持续 leaderboard | epidemic domain | ⚠️ 可作先例，不是 α/β 统一 benchmark |
| EventKG | 官方 GitHub 已访问，SPARQL 与 extraction pipeline 可见。citeturn16search7 | 没有对应 α 的 fixed supervised test | 无统一 cross-language alignment scorer | Open-data graph；构建有手工 mapping 配置 | ⚠️ resource，不是目标 benchmark |
| CrudeOilNews | 正式 LREC 论文 + 当前 GitHub repo 均实际访问。citeturn21view0 fileciteturn4file0L1-L2 | 论文定义 25-document adjudicated reference test | 顶层仓库未见正式 evaluator/leaderboard。fileciteturn5file0L1-L2 | Repo MIT，但**原新闻正文因 copyright 不分发，只给 URL；augmented text 例外**。fileciteturn6file0L1-L2 | ❌ 对严格 raw-data reproducibility |
| OEE-CFC | EMNLP 2024 正式论文已核。citeturn18search0 | paper experiment 有 | 当前 scorer/test 包未实际跑 | 财经 commentary EE | ⚠️ |
| FINEED | LREC-COLING 2024 正式论文已核。citeturn18search1 | paper experiment 有 | 当前 scorer/test 包未核 | Chinese financial EE | ⚠️ |
| FORCE | SMM4H 2024 正式论文已核。citeturn21view1 | paper cross-validation | 当前官方仓库未找到 | paper 说“will be publicly released” | ❌/待取得 |
| ACLED | 官方 2025 Terms/EULA/FAQ 已访问。citeturn24search5turn24search15turn24search18 | event records，不是 NLP fixed test | 无本文任务 scorer | 注册/许可和 attribution 条件 | ⚠️ external outcome/event data |
| GDELT | 官方站实际访问；100% free/open。citeturn24search4 | 大规模持续事件流，不是 gold test | 无 risk-gold scorer | 开放 | ⚠️ weak/external data |
| EM-DAT | 官方 documentation 已访问。citeturn24search1turn24search14 | validated event archive | 无 NLP extraction scorer | 非商业免费注册；archive CC-BY-NC-ND。citeturn24search6 | ⚠️ outcome registry |
| MAVEN-ERE | 当前官方 GitHub 实际访问；data + subtask code + `evaluate.py` 可见。citeturn16search10 | official hidden 与多个 local protocols 并存 | CodaLab 页面可访问，但新提交未登录验证。fileciteturn0file0 | Repo GPL-3.0，数据/evaluator 资产完整度较高。fileciteturn0file1 | ✅ 数据；⚠️ protocol |
| EventStoryLine / Causal-TimeBank | CTB 当前作者 GitHub可访问；PPAT/MAVEN-ERE/DICP 均明确给出下载/预处理路径。citeturn23search0turn23search2turn23search8 | CTB 10-fold、ESL 5-fold convention 在 MAVEN-ERE causal code 明确。citeturn23search6 | 各方法仓库有运行代码，但未证明所有论文 fold IDs 完全相同 | 公共研究资源路径可取得 | **本轮最接近硬条件** |

对 MAVEN-ERE 的可得性必须保留你已有审计里的四分法。Chen et al. 2024 将 original train 再按 8:2 分，original valid 充当新 test；LLMERE 2025 明确 following Chen。Xiang et al. 2025 的 causal-only 又是 original dev → test、原 train 的 10% → dev；此外还有 sampled LLM protocol。fileciteturn0file0 因此即便都写“MAVEN-ERE F1”，也不能不看 split 就比较。

同理，方法代码可用也不等于显存可用。你的 C 审计已经核到：LLMERE 用 A100 40GB、LoRA rank 64、max length 2048；CGEL 代码链接 404 且依赖 GPT-4o / Llama-3.1-70B；MMD-ERE 没取得完整官方代码/hardware/evaluator。fileciteturn0file1 所以本报告只把 encoder/seq2seq 标成 27GB 低风险，把 7B/8B PEFT 标成“需 smoke-test”，没有把模型参数量直接等同于可训练证明。

## 未能核实

**MEE/MINION 当前官方 distribution。** 原论文中数据、split、指标和 cross-lingual setup 可以核，但本轮没有定位到一个能够确认“截至 2026-08-25 当前仍由作者维护、test 全部下载、license 明示、scorer 可执行”的官方仓库。因此不能把“论文说公开”提升成“当前公开 test/evaluator 已实际跑通”。citeturn17view0turn2search2

**MCECR 当前下载与 scorer。** 数据论文的 annotation 设计和关键“same-language retrieval”已通过 PDF 核实，但没有实际下载其当前完整 release，也没有运行标准 coreference scorer。所以这里关于它“不属于 language-mixed event alignment”的结论是强结论，关于“现行 benchmark package 完整性”的结论则保持未核。citeturn5view3turn6view8

**MEANTIME 的 2026 当前镜像、固定 test 与 evaluator。** 论文对 480 文档、四语平行结构和 cross-lingual coreference 的描述已核；但没有把历史 NewsReader distribution 在本轮完整拉取、checksum、执行。citeturn15search7

**MECI 的原始数据版本、规模与 official split。** 2024 cross-lingual document ECI 正式论文以及近期方法代码都证明 MECI 是现实使用的 multilingual ECI 资源，DiffusECI 等仓库还直接指向 `nlp-uoregon/meci-dataset`。citeturn22search10turn23search1 但本轮没有取得 MECI 原始数据论文/仓库的完整版本审计，因此没有在 α 表里擅自填写 event-pair 总数或严格 test 数字。

**ICEWS。** 本轮没有完成当前官方 distribution、许可条款、历史版本修订机制，以及一个 2024–2026“event→economic-risk”正式 benchmark 的一手核查。故这里既不说它“不可用”，也不把它算作已通过。

**ACLED / GDELT / EM-DAT 的具体 risk-subset 论文先例。** 本轮没有取得一篇满足你规则的正式一手论文，同时定义固定 commodity/supply/economic-risk subset、固定 split、公开 evaluator 并被多个独立后续方法采用。所以结论只能是**“没有核到 qualifying precedent”**，不是“从来没有论文筛过这些类型”。ACLED 确实广泛用于 risk assessment / early warning，这一点官方自己承认，但那仍不构成 NLP benchmark。citeturn24search18

**FORCE 的实际 release。** ACL 正式论文已取得，但作者当时仅承诺随论文公开；截至本轮没有通过精确 GitHub 检索取得官方数据仓库。citeturn21view1

**2026 年全年竞争密度。** 当前日期是 2026-08-25；2026 年尚未结束。所有“2024–2026 方法数”都只能是截至今天的检索下界，不能外推到完整 2026 年。

**公开 leaderboard 的提交可用性。** MAVEN-ERE CodaLab 页面可访问、历史 submission 页面可见且页面写 `Competition Ends: Never`，但没有登录账户上传一个合法 submission。因此本报告只能说“页面/历史榜单存在”，不能说“2026-08-25 新提交 scorer 已实测可用”。fileciteturn0file0

**所有性能 headline 分数。** 本报告有意没有抄写 SOTA 数字。原因不是缺结果，而是你的规则要求每个分数同时绑定 paper title、ID、table、split、evaluator 和指标定义。比如 TextEE 的 direct-LLM Tables 6–7 只抽样每数据集 250 documents，sampling seed/split 和 micro/macro 定义存在缺口；LLMERE 虽有 headline 分数，但使用 Chen-style valid-as-test，且旧 baseline 是否同 split 重跑未锁定。fileciteturn0file1 在没有完成逐表 evaluator 审计前，把它们写成一列“SOTA F1”反而违反你的数字规则。

## 与预期不符事实

**最重要的反预期事实是：MCECR 不是你定义的“跨语言事件对齐”。** 它的“multilingual”是五种语言都有 CD-ECR 数据；它的“cross-lingual experiment”是训练语言和测试语言不同；它没有把不同语言的报道共同组成 gold coreference cluster。citeturn5view3turn6view8 因而 α 最有辨识度的那一步——same-real-event cross-language node fusion——恰好没有被 MCECR 补上。

**MEANTIME 倒是真有 cross-lingual event coreference，但它靠的是平行译文。** 120 篇 English Wikinews 被翻译成 Spanish/Italian/Dutch，非英语 annotation 很大程度通过英文 annotation projection 和人工 alignment 获得。citeturn15search7 对语言表示对齐很有用，却比“Reuters 英文稿与 El País 西文独立报道是否同一现实事件”简单得多，因此不能把它当成 natural cross-lingual news alignment 的充分代理。

**ACE05 的“multilingual”也比标题暗示的窄。** corpus 确有 English、Chinese、Arabic，但 LDC 官方明确说 event tasks 当年仅 English/Chinese；Arabic 不是 ACE05 event evaluation language。citeturn24search0 再加上 LDC 许可，它在本项目中不能当开放 multilingual event benchmark。

**CrudeOilNews 的 domain fit 很好，却恰恰在公开性上有硬伤。** 它不是一个泛金融数据：ontology 直接包含 oversupply、shortage、supply increase/decrease、trade tension、sanctions 等，非常贴合 commodity disruption。fileciteturn6file0L1-L2 但同一个 README 又明确说因为 copyright 不发布原始新闻正文，只给 URL。fileciteturn6file0L1-L2 因此“最贴领域”的资源反而不是“最满足公开复现硬约束”的资源。

**β 中真正已有“event → warning”先例的是疫情，而不是大宗商品。** SPEED++ 2024 是正式 EMNLP 工作，把 multilingual event extraction 接到 epidemic preparedness/early warning；这说明应用范式成立。citeturn19search3 但它也侧面说明：若风险监测只是应用延伸，没有必要强行让 commodity 变成主 benchmark domain。

**SPEED 是重名。** Cline Center 的 SPEED 是 Social, Political and Economic Event Database；EMNLP 2024 的 SPEED++ 是 epidemic event extraction。citeturn19search7turn19search3 若文献表不拆开，这两个资源很容易被错误合并。

**MAVEN-ERE 不是“没对手”，而是“对手很多但协议裂了”。** 这是与“找一个竞争不激烈 benchmark”完全不同的风险。2024–2025 有至少七篇正式论文使用其数据/子任务，独立团队保守下界 ≥4；问题是 hidden test、valid-as-test、sampled setting 和 causal-only split 至少四类，headline F1 无法合法排成单一 SOTA 时间线。fileciteturn0file0

**近期 event causality 的竞争密度比跨语言 event graph 更健康。** 2024 EMNLP 的 ICCL、2025 COLING 的 knowledge/concept ECI、2025 EMNLP 的 DICP 都继续在 EventStoryLine/Causal-TimeBank 上评测，而作者代码生态仍公开这两个资源及 CV 过程。citeturn22search9turn23search10turn22search7turn23search6 这并不意味着“题目容易”；恰恰相反，2024 NAACL 仍把 causal event understanding 视为 story understanding 的重要未解成分。citeturn22search3

**“LLM 越大越适合事件图”也没有证据支持。** 你的方法审计中，direct prompting 与 supervised/hybrid/cascade/multi-agent 被证明必须分开；TextEE 的 sampled direct-LLM evidence 不能视为严格主指标，而 SECURE 的 GPT-4→SLM hybrid 在同 scorer 下更有正证据。fileciteturn0file1 同时 CGEL 依赖 GPT-4o / Llama-3.1-70B 且代码不可得，MMD-ERE 也缺完整复现资产。fileciteturn0file1 对 27GB 约束而言，encoder、可控的 PEFT 和 hybrid 才是现实工程包络，而不是“多智能体”本身。

## 证据审计表

| 关键结论 | 一手证据 | 证据等级 | 可否进入最终可行性判断 | 主要边界 |
|---|---|---:|---:|---|
| MEE 是 8-language unified-schema EE，含 trigger/argument，但不是 cross-language event identity | EMNLP 2022 MEE 正式论文、PDF tables/splits。citeturn15search12turn5view0turn6view0 | A | 是 | 当前 repo/test artifact 未重新取得 |
| MINION 是 multilingual ED，而非 argument/coreference/graph | NAACL 2022 MINION 正式论文/PDF。citeturn2search2turn6view5 | A | 是 | 当前官方 repo 未锁 |
| EusIE 证明 MEE-style zero-shot transfer 仍有 2024 正式研究活动 | LREC-COLING 2024。citeturn15search3 | A | 是 | 单篇 follow-up 不足以构成多人近期赛道 |
| MCECR 五语、5,802 docs | Findings NAACL 2024。citeturn17view1 | A | 是 | 无 |
| MCECR 不含 language-mixed same-event clusters | MCECR PDF collection protocol + cross-lingual experiment。citeturn5view3turn6view8 | **A+，决定性** | **是** | 直接否定“拿 MCECR 代替跨语言事件对齐” |
| MEANTIME 有 cross-lingual event coreference | LREC 2016 正式资源论文。citeturn15search7 | A | 是 | 主要由平行翻译/annotation projection 得到，不等价于独立跨语报道 |
| ACE05 Arabic 不是 event task language，且数据非开放 | LDC2006T06 官方 catalog。citeturn24search0 | **A+** | **是** | 直接触发公开数据硬约束 |
| EventKG 是 multilingual event KG 但非目标 supervised benchmark | 官方 EventKG GitHub/pipeline。citeturn16search7 | A | 是 | resource ≠ cross-language news alignment benchmark |
| CrudeOilNews 的 commodity ontology 与规模确实匹配 β | LREC 2022 正式论文 + 官方 repo README。citeturn21view0 fileciteturn6file0L1-L2 | A | 是 | 近期 follow-up 密度低 |
| CrudeOilNews raw original text 因 copyright 不发布 | 当前官方 GitHub README。fileciteturn6file0L1-L2 | **A+，决定性** | **是** | annotations/URLs 公开 ≠ fixed raw corpus 完整公开 |
| OEE-CFC/FINEED 是金融 EE，但不是 supply-risk propagation benchmark | EMNLP 2024 / LREC-COLING 2024 正式论文。citeturn18search0turn18search1 | A | 是 | 不能因 domain=finance 就改叫“经济风险” |
| FORCE 是 food-supply incident EE | SMM4H 2024 正式论文。citeturn21view1 | A | 是 | 当前 release 未取得 |
| SPEED++ 是 event extraction → warning 的真实正式先例 | EMNLP 2024。citeturn19search3 | A | 是 | epidemic，不是 commodity；warning 也非多人 shared benchmark |
| ACLED 确实用于 risk/early warning，但不是 NLP extraction gold | ACLED 官方 FAQ/EULA/Terms。citeturn24search18turn24search15 | A | 是 | 自定义 risk subset 不自动成为 benchmark |
| GDELT 全库开放 | GDELT 官方站。citeturn24search4 | A | 是 | openness 不等于 gold quality |
| EM-DAT 可用于外部 disaster outcomes | 官方 EM-DAT docs。citeturn24search1turn24search14 | A | 是 | 非文本 EE benchmark；许可有非商业条件 |
| MAVEN-ERE 当前 repo 仍有 data/evaluator assets | 官方 GitHub。citeturn16search10 | A | 是 | hidden submission 未实测 |
| MAVEN-ERE 2024–2025 至少四种 evaluation setting | 用户 B 数据审计对论文 appendix / CodaLab 的一手交叉核验。fileciteturn0file0 | A- | **是，决定是否可排 SOTA** | 不能混表 |
| MAVEN-ERE 独立近期团队下界 ≥4 | 同一审计，已更正 KnowQA 等作者重叠。fileciteturn0file0 | A- | 是 | 是检索下界，不是穷尽 |
| Direct prompting、PEFT、hybrid、cascade、RAG、multi-agent 不能混称同范式 | 用户 C 方法/代码审计。fileciteturn0file1 | A- | 是 | 影响方法可行性，不直接决定研究问题价值 |
| LLMERE 论文 recipe 未证明 27GB | C 审计核到 A100 40GB、rank 64、2048 max length。fileciteturn0file1 | A- | 是 | 7B/8B 仍可另做 QLoRA smoke test |
| ESL/CTB 有持续 2024–2025 独立正式方法 | ICCL 2024、COLING 2025、DICP EMNLP 2025。citeturn22search9turn23search10turn22search7 | **A** | **是** | 同 fold IDs/evaluator 仍需最终锁定 |
| CTB/ESL data 与 CV protocol 可实际取得 | CTB 作者 GitHub、MAVEN-ERE causal README、DICP repo。citeturn23search2turn23search6turn23search8 | **A+** | **是** | 不同 paper 的 negative pair construction 仍要逐篇核 |
| “2024+ 新 event graph 数据绝对没有独立 follow-up” | 本轮与 B 审计都只能证明未发现。fileciteturn0file0 | C | **不可写成绝对结论** | 只能使用 `0* / strict-search lower bound` |

综合所有硬条件后，证据支持的可行性排序不是“哪里对手少”，而是**哪里存在真实问题，同时 benchmark 的公共性和比较制度最完整**。按这一标准，完整 α 被 cross-language node gold 卡住，β 被 raw-data / risk-target / evaluator 链条卡住；**EventStoryLine/Causal-TimeBank 上的可验证事件因果识别目前证据最闭合，固定协议的 MAVEN-ERE 其次但必须先解决评测分裂。** 这两个替代切口都能保留“事件结构 → 风险监测”的应用延伸，而不需要把多语言或大宗商品人为升级为研究主问题。citeturn22search3turn23search6turn16search10