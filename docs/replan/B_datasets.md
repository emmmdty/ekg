# DR-B：公开事件类数据集、竞争密度与 MAVEN 资产残值

[下载完整可审计报告 `B_datasets.md`](sandbox:/mnt/data/B_datasets.md)

核验日期：**2026-08-25（Asia/Tokyo）**。本报告遵循附件中“数字必须回到一手来源、split/evaluator/指标三轴对齐、不能把竞赛页面存在等同于提交通道可用”的审计规则。fileciteturn0file0 对现有代码的讨论只引用 `LOCAL_ASSET_INVENTORY.md`，没有重新进行代码盘点。fileciteturn0file1

## 执行摘要

最重要的事实是：**公开事件类资源很多，但“有公开数据”与“有一个在 2026 年仍可稳定进行同口径 SOTA 比较的 benchmark”是两件不同的事。** MAVEN-ERE 是这一问题最典型的案例。官方仓库仍公开 train/valid 标注、官方 `evaluate.py` 和 test 输入，但 test 关系 gold 不公开。官方 CodaLab 竞赛页面截至核验日仍可访问，显示 `Competition Ends: Never`，公开榜单也能看到；然而未登录页面同时明确要求登录后才能参与竞赛，本次无法实际进入上传并运行 scorer 的操作。因此能审计成立的表述只能是：**“页面可访问，但提交能力未验证”**，不能写“通道仍活着”。citeturn26search1turn2view0turn3view2

更关键的是，2024–2025 年 MAVEN-ERE 文献已经形成至少三套彼此不能直接比较的 evaluation setting。第一类沿用原始 train/dev/hidden-test，例如 TacoERE 明确给出 2,913/710/857 文档的原始划分；第二类因为 test gold 不公开，把原始 train 再按 8:2 切分，并把**官方 valid 当作新的 test**；第三类进一步只从 MAVEN-ERE 抽取少量样本做 LLM/agent 评测。ACL 2024 的 Chen et al. 明确采用第二类方案，COLING 2025 的 LLMERE 又明确写明“Following Chen et al. (2024)”采用同一方案，因此已经取得了用户要求的**至少两篇一手 valid-as-test 先例**。citeturn20view0turn15view0

这直接意味着：**不能根据近年 MAVEN-ERE 论文的 headline F1 排出一条可靠的 SOTA 时间序列，也不能据此判定 benchmark 是否已经饱和。** TacoERE 的原始 test、LLMERE 的 original-valid-as-new-test、MMD-ERE 的 50-document sampled setting、KnowQA 的 causal sampled setting，都不是一个测试集合。citeturn14search3turn15view0turn14search10

MAVEN-ERE 的研究活动本身并未消失。2024–2025 已正式发表、明确使用 MAVEN-ERE 或其子任务的论文至少包括 TacoERE、*Improving Large Language Models in Event Relation Logical Prediction*、*Are LLMs Good Annotators for Discourse-level Event Relation Extraction?*、KnowQA、LLMERE、MMD-ERE，另有 2025 年 directional event causality 工作。citeturn14search3turn17search2turn14search12turn14search10 但 TacoERE、MMD-ERE 的作者与 MAVEN 原团队有明显重合；在把“原作者继续做 benchmark”与“独立团队跟进”区分后，本报告能保守确认的**独立团队使用下界为 ≥4**，而其中能作为“全量、同一 split、同一 evaluator”对手的数量远低于这个数字。

MAVEN-Arg 和 MAVEN-FACT 的情况不同。MAVEN-Arg 2024 数据论文给出 **98,591 events、290,613 arguments、162 event types、612 argument roles**；本轮取得 LC4EE 在 MAVEN-Arg 上做实验，但 LC4EE 作者包含 Lei Hou、Juanzi Li，与 MAVEN-Arg 数据集团队重合，因此没有计入独立团队跟进。citeturn14search4turn14search0 MAVEN-FACT 包含 **112,276 个 factuality-annotated events**，但本轮没有取得 2025–2026 独立方法论文构成活跃 benchmark 序列的证据；这里的“0”仅是本轮检索下界，不能反推“绝对没有论文”。citeturn28search3

2024 以后实际上出现了不少新的事件资源：MCECR、CLES、NarrativeTime/TimeBankNT、MultiVENT-G、CMNEE、DocEE-zh、OEE-CFC、DEIE、SPEED/SPEED++，以及 2025 的 EventRelBench、EcomScriptBench 和 2026 的 CausalSense、Vrittanta-EN。citeturn26search0turn26search2turn24search4turn26search8turn27search3turn27search2turn27search0turn27search12turn28search0 但在严格扣除“数据论文自己跑旧 baseline”“原团队后续论文”“arXiv-only”以及“只是引用而未真正跑 benchmark”以后，**本轮没有找到一个能够安全盖章为“2024 后发布且已经有 ≥2 篇独立正式方法论文跟进”的数据集**。这个空集本身是一个重要审计结果，而不是推荐判断。

另一个与常见认知不一致的事实是 **ACE05 的 event task 并非英/中/阿三语对等 benchmark**。LDC2006T06 的官方说明确实包含英语、普通话和标准阿拉伯语三种语料，但同时明确写道：除 event tasks 外其他任务覆盖三种语言，**event tasks evaluated in English and Chinese only**。此外 ACE05 需按 LDC User Agreement 获取，并非开放下载数据。citeturn23search4

风险类资源也需要区分两类。SPEED/SPEED++ 真正提供文本级事件抽取 gold，并把事件检测/论元抽取用于疫情预警；SPEED++ 有约 **5.1K tweets、4 种语言、4 种疾病以及 20 个 argument roles**。citeturn28search0turn28academia44 ACLED 这类资源则主要是结构化现实事件数据库：ACLED 当前官方访问方式要求注册账户，API 还需要认证 token。它具有风险监测应用价值，却并不天然提供一个 NLP event extraction 的 train/dev/test + evaluator。citeturn28search1turn28search4

算力方面，本轮取得的论文级硬件证据也说明不能简单把“7B/8B”视为单卡 27GB 已验证。KnowQA 主实验报告使用**单 RTX 3090**，Chen et al. 的 RoBERTa-large 实验报告单 V100；TacoERE 则报告训练和测试使用 **2×RTX 3090**；LLMERE 的 LoRA 设置使用 **A100 40GB**。因此只能说部分方法具备单卡先例，不能说原论文所有强配置均可在 27GB 原样复现。citeturn20view2

本地资产层面，“一旦不用 MAVEN，约一万行代码全部作废”与附件实测不符。现有 9,962 行代码中，约 **2,263 行 Tier-1** 是 calibration/evaluation/core/agent 等任务无关基础设施；真正与 MAVEN+SeDGPL 强绑定的 `succession/` 约 **2,148 行**。同时，CCKS 中文金融因果数据已经实际进入相同的 `EventNode/RelationEdge` schema，证明数据适配层至少已经做过一次跨数据集、跨语言验证。fileciteturn0file1

## 数据集总表

下表中的“独立跟进下界”只计本轮已经能够确认的**正式发表、数据论文之后、且与原数据团队不明显重叠的方法论文**；`0*` 表示“本轮没有取得可计数的一手证据”，而不是宣称不存在。对没有取得完整 evaluator/metric 定义的数字，本报告统一写“未取得严格可比最好结果”。

| 数据集 | 年份 / 语言 | 任务与 gold | 规模 / split | 获取与 test 状态 | 2024–26 独立跟进下界 | 严格可比结果 / 27GB | 关键风险 |
|---|---|---|---|---|---:|---|---|
| **MAVEN** | 2020 / en | event detection/type | 4,480 docs；118,732 event mentions；168 types citeturn0search4 | GitHub/云盘；MIT；官方 scorer；test 走 CodaLab citeturn0search0 | ≥1 | 近年 strict-best 未取得；encoder 级方法通常较轻，但具体方法需核 | hidden test；近年任务口径变化 |
| **ACE05** | 2006 / en, zh, ar corpus；event only en+zh | entity/relation/event | 官方 corpus en/zh/ar 规模见 LDC；社区 EE split 并非官方唯一 | LDC 许可，不是开放下载；无现代统一 leaderboard citeturn23search4 | 未系统核实 | 典型 encoder 可 | 许可、预处理和 split 高度碎片化 |
| **ERE / Rich ERE** | 多版本 | entity/relation/event | 本轮未取得统一 split | LDC/TAC 系列；旧评测通道未逐年实访 | 0* | 未取得 | “ERE”不是一个单一固定 benchmark |
| **TAC-KBP Event** | 多年 / 多语设置 | nugget/argument/linking | 不同年份不同 track | TAC/LDC 体系；当前 server 未逐届核 | 0* | 未取得 | 年份和 scorer 不能混并 |
| **RAMS** | 2020 / en | document EAE / argument linking | 9,124 events；官方 train/dev/test；常用 events 7,329/924/871 citeturn23search5turn23search1 | JHU RAMS 1.0 可直接下载，test gold 公开 | ≥1 | APSR 2024 有 test 数字，但 scorer 轴未完全取得，严格标不可比 | Span-F1 与 Head-F1、head/coref preprocessing |
| **WikiEvents** | 2021 / en | document EAE | docs 206/20/20；常用 events 3,241/345/365 citeturn23search0turn23search6 | train/dev/test 公开下载 | ≥1 | strict-best 未取得 | span/head 评测及数据处理版本 |
| **DocEE** | 2022 / en | document event classification + EAE | 27,485 docs；180,528 argument instances citeturn23search13 | 官方 GitHub；test/license 细节仍需核 | 0* | 原 Doc2EDAG 配置被 toolkit 标注为至少 4×V100 16GB；并非所有 baseline 单卡友好 citeturn23search3 | 老 PyTorch/DGL 依赖与多卡 baseline |
| **GLEN** | 2023 / en | large-schema general event extraction | 205K event mentions、3,465 types citeturn4search1 | download/license 未完成实访 | 0* | 未取得 | distant supervision 与人工 gold 不同 |
| **MAVEN-Arg** | 2024 / en | document EAE | 98,591 events；290,613 args；162 types；612 roles citeturn14search4 | official repo；test annotation hidden；CodaLab 指向存在，本轮未核提交；license 未取得 | **0** | 未取得 strict-best | hidden test；独立竞争证据不足 |
| **MAVEN-ERE** | 2022 / en | coref+temporal+causal+subevent | 4,480 docs；103,193 coref chains；1.216M temporal；57,992 causal；15,841 subevent citeturn26search1 | GPL-3.0；test hidden；CodaLab 页面可读、提交未验证 | **≥4** | **无法定义统一 strict-best** | hidden-test / valid-as-test / sampled 三套 setting |
| **EventStoryLine / ESC** | 2017 / en | causal+temporal/storyline | exact split 本轮未取齐 | 数据资源存在；当前统一 server 未核 citeturn24search12 | 至少有近年方法使用 | 不形成统一 SOTA 序列 | TacoERE 与 MMD-ERE 又使用不同采样设置 |
| **Causal-TimeBank** | 2014 / en | causal+temporal pair | 184 docs；6,813 events；7,608 pairs；原 corpus 无统一 train/dev/test citeturn20view0 | 学术语料；固定 server 不成立 | ≥1 使用 | 不适合直接形成官方 test 时间序列 | 后续论文普遍自行切分 |
| **MATRES** | 2018 / en | temporal relation | LLMERE 沿用 182/73/20 docs citeturn15view0 | gold 学术可用；本轮未核统一 leaderboard | ≥1 | LLMERE 有 Table 3，但 evaluator/negative 定义不全，严格不可比 | 多种历史 preprocessing |
| **TimeBank-Dense** | 2014 / en | dense temporal relations | 本轮未取齐 | 学术资源 | 0* | 未取得 | closure / label mapping 差异 |
| **NarrativeTime / TimeBankNT** | 2024 / en | fully dense timeline TLINK | 对 TimeBank-Dense 全量重标 citeturn24search4 | 论文称贡献 corpus+open tools；license/download 本轮未实访 | 0* | 数据论文 baseline | 新资源时间序列不足 |
| **TORQUE** | 2020 / en | temporal reading comprehension | 3.2K news snippets；21K questions citeturn24search0 | test 存在；当前 leaderboard 未实访 | 0* | 未取得 | QA metric 与 event-edge classification 不同 |
| **CRAB** | 2023 / en | real-world causal strength/reasoning | ~2.7K event pairs citeturn25search0 | data/code 公开；license/split 细节未全核 | 0 正式；ACCESS 2025 本轮仅取得 arXiv | 未取得 | 与文本 causal relation extraction 任务不同 |
| **ECB+** | 既有 / en | cross-document ECR | 本轮未从官方源取齐 | 本轮未完成官方 download/license 实访 | 至少有 2024 multimodal扩展使用 | 无统一 strict-best | oracle mention/topic clustering assumptions |
| **GVC** | 既有 / en | gun-violence cross-doc ECR | 未取得 | 未完成实访 | 0* | 未取得 | 专域、小规模 |
| **FCC** | 既有 / en | football cross-doc ECR | 未取得 | 未完成实访 | 0* | 未取得 | 专域 |
| **MEANTIME** | 既有 / 多语 | event/time/factuality/coref | 本轮未从一手源取齐 | 未完成实访 | 0* | 未取得 | 各论文使用语言/子集不同 |
| **CD²CR** | 既有 | cross-document/cross-topic ECR | 未取得 | 未完成实访 | 0* | 未取得 | 与 ECB+ setting 不同 |
| **MEE** | 2022 / 8 languages | multilingual triggers+arguments | >50K event mentions citeturn26search10 | 作者称公开；license/test 本轮未完成实访 | 0* | 未取得 | multilingual/zero-shot settings 易混 |
| **MINION** | **未能核实** | multilingual event resource 候选 | 未取得 | **未能取得唯一无歧义官方资源** | 0* | 未取得 | 名称/版本本轮检索不足，禁止猜测 |
| **MCECR** | 2024 / en, es, hi, tr, uk | multilingual cross-document ECR | 5,802 news articles citeturn26search0 | 数据论文称公开；具体 license/test 本轮未实访 | **0*** | 未取得 | 新资源，独立竞争尚未证明 |
| **DuEE** | 2020 / zh | event extraction | 社区常用 11,908/1,492/34,904 citeturn23search9 | Baidu competition；当前提交通道本轮未实访 | 0* | 未取得 | 老竞赛 hidden test |
| **DuEE-fin** | 2020 / zh | financial document EE | 社区常用 7,015/1,171/59,394 citeturn23search9 | Baidu competition；当前通道未核 | 0* | 未取得 | 比赛格式、多实体 argument |
| **FewFC** | 2021 / zh | few-shot EE | 常用 7,185/899/898 citeturn23search9 | 学术公开资源 | 0* | 未取得 | episode/split 定义 |
| **CCKS 事件系列** | 多年 / zh | 因果/金融/事件抽取等 | 不是一个统一 corpus | 必须指定年份与赛题 | 0* | 未取得 | 不能把“CCKS”作为单一 benchmark |
| **CMNEE** | 2024 / zh | military document EE | 17,000 docs；29,223 events；8 types；11 roles citeturn27search3 | 官方 GitHub 存在；license/test 细节未完全核 | 0* | 未取得 | 新专域 benchmark、独立跟进不足 |
| **DocEE-zh** | 2024 / zh | fine-grained document EAE | >36K events；>210K args citeturn27search2 | DocEE GitHub；test/license 需继续核 | 0* | 论文摘要的 45.88 F1 不满足本报告四轴，故不认 strict-best | 部分 DocEE baseline 多卡/旧依赖 |
| **OEE-CFC** | 2024 / zh | open EE / financial commentary | 17,469 events；44,221 args；21 roles citeturn27search0 | resource/license/test 本轮未全核 | 0* | 未取得 | 金融贴合但 open schema 与 typed EE 不同 |
| **DEIE** | 2024 / zh | event trigger/argument/summary/relation；emergency events | 20K docs；56K+ events；242K+ args；19 emergency types citeturn27search12 | 实际数据入口/license 未完成实访 | 0* | 未取得 | 很新；竞争/评测基础设施不足 |
| **MCNC** | 2016 / en | narrative cloze / next event | 本轮未重新核 | NYT-derived；许可/构造版本风险 | 0* | 未取得 | benchmark 老化、负样本生成敏感 |
| **CGEP-MAVEN** | 派生任务 | en | graph-conditioned event prediction | 本轮未重新核 | 论文处理版 | 0* | 本地已有 SeDGPL 资产 | 不是 MAVEN 官方标准任务 |
| **CGEP-ESC** | 派生任务 | en | graph-conditioned event prediction | 未核 | 派生资源 | 0* | 本地已有 raw | evaluator 社区统一性弱 |
| **NYT-SEG** | **未核** | en | script/event graph 候选 | 未取得 | **具体资源身份未一手确认** | 0* | 未取得 | 不以相似数据冒充 |
| **TORQUESTRA** | 既有 / en | temporal/event-graph QA | 原始规模本轮未取齐 | official page 未完成实访 | ≥1：TAG-EQA 2025 citeturn4search0 | 未取得 strict-best | 原始 split/scorer 仍需核 |
| **EcomScriptBench** | 2025 / en | e-commerce script benchmark | split/规模未全核 | ACL 2025；数据入口/license 未实访 | 0* | 未取得 | 发布较新 citeturn4search9 |
| **EventRelBench** | 2025 / en | coref/temporal/causal/super-sub relation QA | ~35K questions；EventRelInst ~48K citeturn5search9 | 论文宣称公开；license/test 未实访 | 0* | 未取得 | QA/instruction metric 不能直接与 MAVEN-ERE F1 相减 |
| **MAVEN-FACT** | 2024 / en | event factuality + evidence | 112,276 events citeturn28search3 | GitHub/Drive 在线；license/test 通道未全核 | **0*** | 未取得 | 2025–26 独立竞争证据不足 |
| **FactBank / UW / Unified Factuality** | 旧 / en | factuality | 本轮未逐项取得官方 split | 本轮未完成逐项实访 | 0* | 未取得 | label mapping 和 conversion evaluator 不统一 |
| **SPEED** | 2024 / en | epidemic event detection | 7 disease-agnostic event types；exact split 见项目数据图 | 官方项目页/Data 入口存在 | 0* | strict-best 未审；encoder 类方法 | Twitter/X 数据再分发和时间漂移 |
| **SPEED++** | 2024 / 4 annotated languages | epidemic event extraction | 5.1K tweets；4 diseases；20 roles citeturn28search0 | 官方项目页/Data 入口存在 | 0* | mPLM setting 大概率可训练，但未做 27GB 原配验证 | zero-shot cross-language/cross-disease setting 特殊 |
| **ACLED** | 持续 / global | structured conflict/political-violence events | N/A | 注册后 export/API；API 要认证 citeturn28search1turn28search4 | N/A | **不是 NLP benchmark** | 不能自行造 split 后称与已发表 IE 方法同口径 |
| **GDELT** | 持续 | automatically structured global events | N/A | 本轮未完成官方页许可实访 | N/A | 不是 gold IE benchmark | 自动抽取噪声、版本巨大 |
| **ICEWS** | 多 release | structured political events/TKG | N/A；学术常用 ICEWS14/18/05-15 | 本轮未完成当前官方入口实访 | N/A | TKG benchmark 要指定具体切分 | 原始数据库与学术 TKG split 不同 |
| **EM-DAT** | 持续 | structured disaster records | N/A | **官方许可/下载 UI 本轮未取得一手完整核验** | N/A | 不是 NLP extraction benchmark | 不包含天然文本抽取 gold |
| **CLES** | 2024 | cross-document EE | 20,059 docs；37,688 mention events；>70% cross-doc citeturn26search2 | resource/license 未实访 | 0* | 摘要“约72% F1”缺四轴，严格不可比 | 新 pipeline task |
| **MultiVENT-G** | 2024 | multimodal current events | 14.5h video + 1,168 docs + 22.8K entities citeturn26search8 | ACL Anthology 直接附 data.zip | 0* | 未取得 strict-best | 多模态算力/任务与纯文本图谱不同 |
| **CausalSense** | 2026 / en | joint EE + causal relation | >500K sentences citeturn5search0 | 论文称开源，repo/license 未实访 | 0* | 未取得 | news+ATOMIC+synthetic 混合 gold |
| **Vrittanta-EN** | 2026 / en | narrative trigger detection/classification | 11,272 event instances citeturn24search11 | 论文写 acceptance 后公开；**本轮没有验证实际数据仓库** | 0* | encoder baseline 可推测但不把推测当复现证据 | “承诺公开”不能写成“已下载” |

这张表中大量“未取得”是刻意保留的。特别是 ECB+、GVC、FCC、MEANTIME、CD²CR、FactBank、UW、Unified Factuality 等老数据，本轮检索资源优先用于 MAVEN 评测基础设施、2024–2026 新资源和风险数据；没有足够一手证据时，没有用二手榜单或记忆补数。

## test / leaderboard 实访日志

**MAVEN-ERE 官方仓库。** 官方 GitHub 在核验日可访问，包含关系类型目录、data、`evaluate.py` 和 GPL-3.0 license；README 明确说明 test annotations 不公开，需要 CodaLab 获取 test performance。citeturn26search1

**MAVEN-ERE CodaLab。** 实际访问 `MAVEN-ERE Event Relation Extraction Challenge` 页面后，页面可正常加载，并显示 `Competition Ends: Never`；公开 leaderboard 可读取，访问时顶部可见 55.42、54.01、52.45 等成绩。与此同时页面明确显示 **“You must be logged in to participate in competitions.”** Public Submissions 路由也能打开，但未登录视图无法完成实际上传，因此没有证据证明管理员仍允许 submission、上传后 scorer 仍会运行。结论严格记录为：**页面可访问、公开榜单可访问、提交能力未验证。** citeturn2view0turn3view2

这一点尤其重要，因为“竞赛页存在”“Ends: Never”“可以新建 submission”“submission 能成功运行 scorer”是四个不同层次的事实；本次只能核实前两个。

**MAVEN detection。** 官方 GitHub 的数据下载、MIT license、`evaluate.py` 仍存在，README 仍指向 CodaLab。citeturn0search0 但本轮没有完成该 detection challenge 的登录后上传操作，因此不能写其评测通道“仍在收提交”。

**MAVEN-Arg。** 官方 repo 明确说明 test annotations 不公开，需要通过 CodaLab evaluation；本轮没有完成该 CodaLab 的提交操作核验，且已读页面没有取得明确 dataset license。citeturn14search4

**MAVEN-FACT。** 官方 repo/Drive 入口仍可找到，数据论文确认公开 dataset/code 的计划与 112,276 个 event factuality annotations。citeturn28search3 本轮未取得其 test leaderboard/submission infrastructure 的一手证据，故不推测。

**RAMS。** JHU 官方页面仍直接提供 RAMS 1.0 下载，并明确说明数据由 train/dev/test 文件组成，每条实例带有 `gold_evt_links`；因此它与 MAVEN-ERE 最大的基础设施差别是：研究者能在本地拿到 test gold。citeturn23search5

**ACE05。** LDC catalog 当前可访问，但获取受 LDC User Agreement 和会员/非会员许可约束。它不是“点开 GitHub 即可完全开放下载”的类型。citeturn23search4

**SPEED/SPEED++。** 官方项目页当前可访问并公开 Paper/Data 入口和数据统计、跨语言实验设定。citeturn28search0 本轮没有逐文件验证数据包 license，也没有发现需要 online leaderboard 才能得到 test 分的证据，因此不能虚构其 submission server 状态。

**ACLED。** 官方 FAQ 说明数据可在注册后通过 export、curated files 或 API 获取；API documentation 又明确要求 myACLED account 和认证 token。citeturn28search1turn28search4 这属于**数据库访问通道**，不是 benchmark submission server。

最关键的 split 核验已经取得两个 MAVEN-ERE 一手先例：

> Chen et al., ACL 2024，Appendix E：MAVEN-ERE 只发布 train/valid，不公开 ground-truth test，因此将 train 随机按 8:2 分成 train/valid，并把 original valid 作为 new test。citeturn20view0

LLMERE, COLING 2025，Appendix C 又明确说明，由于 test set 不公开，**Following Chen et al. (2024)**，同样将 original train 按 8:2 切分、original valid 作为 new test。citeturn15view0

所以“valid-as-test 是不是只有项目内部临时做法”的答案已经能明确核实：**不是，至少已有两篇正式发表论文采用这一 setting。** 但这两篇的数不能与官方 hidden-test CodaLab 榜单直接相减。

## 重点候选的竞争密度与严格可比数字

MAVEN-ERE 是本轮唯一能同时证明“近年方法数量较多”与“评测口径严重分裂”的代表 benchmark。

| 论文 | 正式发表 | 独立团队计数 | 实际 evaluation set | 表中可定位数字 | 严格比较资格 |
|---|---|---|---|---|---|
| **TacoERE** | LREC-COLING 2024, `2024.lrec-main.1348` | 不计独立：多位 MAVEN 原团队作者 | 原始 2,913/710/857 docs；causal 合并 CAUSE+PRECONDITION | Table 1 causal：P 34.8 / R 32.4 / F1 34.1 citeturn14search3 | **不可比**：本轮未取得明确 official evaluator 声明与完整 micro/macro 定义 |
| **Improving Large Language Models in Event Relation Logical Prediction** | ACL 2024, `2024.acl-long.512`, DOI `10.18653/v1/2024.acl-long.512` | **计独立** | original train→8:2；original valid→new test；又从 new test 抽 500 个 ERE examples | 不把其 sampled LLM 数放入 full-test SOTA | **不可与 hidden test 比**；split 证据完整 citeturn17search2turn20view0 |
| **Are LLMs Good Annotators for Discourse-level ERE?** | Findings EMNLP 2024, `2024.findings-emnlp.1` | **计独立** | 明确研究 discourse ERE；LLMERE 引用其 MAVEN-ERE 5-shot 结果 | 本轮未打开到其主表完成四轴审计 | **数字未取得严格资格** citeturn14search12 |
| **KnowQA** | Findings EMNLP 2024, `2024.findings-emnlp.986` | **计独立** | MAVEN-ERE causal sampled subset；使用 MAVEN-Arg gold arguments | Table 2 有 ECI/CRC F1 | **不能与 full MAVEN-ERE 比**；主实验报告 single RTX 3090 citeturn14search10 |
| **LLMERE** | COLING 2025, `2025.coling-main.500` | **计独立** | original valid as new test | Table 2 Llama3-8B-base：Temporal F1 54.7、Causal 36.0、Subevent 28.2、Coref 90.9、Overall 52.5 citeturn16view2 | **不可比**：split 明确，但本轮未取得 evaluator 声明、negative-class 和 Overall F1 aggregation 完整定义 |
| **MMD-ERE** | COLING 2025, `2025.coling-main.460` | 不计独立：与 MAVEN 团队明显重合 | 每 relation 50 docs；MAVEN causal 605 instances、subevent 404 | Table 1 sampled causal F1 55.59、subevent 63.10 | **不可与 full 或 valid-as-test 比** |

这里最容易发生的错误，是看到 **34.1、52.5、55.59** 后把它们排列起来。这样做在本报告约束下是无效的：它们既不是同一个测试集，也不一定使用同一个 evaluator，更没有相同的任务输出空间。

LLMERE 自己也提供了一个有价值的“LLM 是否把任务拉平”的证据。其 Table 2 中，直接 few-shot 的 Llama2、ChatGPT、GPT-4 在 MAVEN-ERE 上明显弱于 task-specific 方法；论文的主要提升来自 fine-tuning 与 relation rationale，而不是直接 prompting。citeturn16view2 Chen et al. 的 ACL 2024 研究进一步发现，在其 MAVEN-ERE pilot 中，ChatGPT 会产生大量与事件关系逻辑约束冲突的预测，并据此研究 logic injection/retrieval/fine-tuning。citeturn22view0 因此，至少在 MAVEN-ERE 这种跨关系文档级任务上，一手结果并不支持“GPT-4 级模型已经 zero/few-shot 拉平监督方法”的判断。

MAVEN-Arg 的近年竞争则稀疏得多。数据论文是 ACL 2024 `2024.acl-long.224`。citeturn14search4 LC4EE（Findings ACL 2024，`2024.findings-acl.715`）确实在 ACE2005 与 MAVEN-Arg 上实验，但作者列表包括 Lei Hou、Juanzi Li，与 MAVEN-Arg 原团队重合，因此本报告只把它算作**benchmark 使用证据**，不算“独立团队跟进”。citeturn14search0

MAVEN-FACT 的 2024 数据论文不仅规模大，还明确报告 conventional fine-tuned models 与 LLM 都存在困难，并研究了 event arguments/relations 对 factuality 的帮助。citeturn28search3 然而，本轮没有取得 2025–2026 独立团队方法论文，可以构成“多个已发表近年方法同口径竞争”的证据。因此对它能说的是**竞争证据不足**，而不能说“已经饱和”。

RAMS/WikiEvents 至少有 2024 年继续工作的明确证据。APSR 论文 Table 2 给出 RAMS 3,194/399/400 docs 与 WikiEvents 206/20/20 docs，Table 3 给 RAMS test Span-F1 47.28、Head-F1 55.02。citeturn23search6 但本轮没有取得作者明确说明的 scorer 版本及所有 baseline 是否使用完全同一 head conversion，因此按照用户要求，这两个数只作为“论文表中存在的结果”记录，不认定为可直接作为 thesis target 的当前最好结果。

EDM3 在 *SEM 2024 正式发表，并评估 RAMS、WikiEvents、MAVEN 等事件数据。citeturn6search1 由于本轮没有进一步把其 table/split/scorer 全部取齐，未把摘要数字加入严格排名。这同样体现本报告采取“少报一个数字，也不拼错口径”的原则。

对 EventStoryLine，TacoERE 2024 和 MMD-ERE 2025 都继续使用 causal relation setting，但后者又是采样设置，因此同样不能据论文年份直接画出 SOTA 曲线。citeturn14search3

对 TORQUESTRA，本轮至少取得 TAG–EQA 在 *SEM 2025 正式发表并使用该 benchmark 的跟进证据。citeturn4search0 但没有完成 TORQUESTRA 原始 split/scorer 的一手审计，所以仍不能给 strict-best。

从“竞争成熟度”而不是性能强弱看，本轮证据可压缩成：

| 资源 | 2024–26 正式方法使用下界 | 独立团队下界 | 能否建立同 split+同 evaluator 时间序列 | 能否说“已饱和” |
|---|---:|---:|---|---|
| MAVEN-ERE | ≥6 | ≥4 | **不能** | **不能** |
| MAVEN | ≥1 | ≥1 | 本轮不能 | 不能 |
| MAVEN-Arg | ≥1 | 0 | 不能 | 不能 |
| MAVEN-FACT | 0* | 0* | 无序列 | **不能；只能说跟进证据不足** |
| RAMS | ≥1 | ≥1 | 尚未完整建立 | 不能 |
| WikiEvents | ≥1 | ≥1 | 尚未完整建立 | 不能 |
| ESC | ≥2 个近年使用证据 | 独立性和 setting 混杂 | 不能 | 不能 |
| TORQUESTRA | ≥1 | ≥1 | 未建立 | 不能 |
| MCECR / DocEE-zh / CMNEE / OEE-CFC / DEIE / SPEED++ | 0* | 0* | 尚无足够序列 | 不能称饱和 |

所以，“近两年分数是不是只涨小数点”这一问题，对绝大部分本轮候选不能合法回答。缺少同 split、同 evaluator 的序列时，最严谨的结论就是：**无法判断是否饱和。**

## MAVEN 系列残值

**MAVEN 本体。** 数据、MIT license 和官方 scorer 仍有公开入口。citeturn0search0turn0search4 本轮取得 2024 方法继续使用 MAVEN 的证据，但没有建立 2025–2026 官方 test 上的新方法时间序列。因此 MAVEN detection 的 benchmark 是否“还活跃”不能仅由仓库存在判断，也不能据搜索下界 0 判死。

**MAVEN-ERE。** 它在 MAVEN 系列里拥有最明显的“文献残值”，但同时拥有最严重的“评测残值折损”。2024–2025 明确出现多篇 ERE/LLM/agent 方法；官方数据和 scorer 仍在；CodaLab 页面仍可读取。citeturn26search1turn2view0 可是近年论文已经分叉为 hidden test、original-valid-as-test 和 sampled subset。Chen et al. 与 LLMERE 的 split 说明尤其清楚。citeturn20view0turn15view0

因此 MAVEN-ERE 的状态不能简化成“旧 benchmark 已饱和”或“leaderboard 仍活跃”中的任何一个。严格事实是：**数据与方法社区仍有残余活动，但统一公开比较基础设施已经成为明显风险。**

**MAVEN-Arg。** 作为 2024 的新 EAE 大资源，它拥有比传统 ACE 更大的 schema 和规模。citeturn14search4 但 hidden test + CodaLab 依赖仍存在，本轮又没有取得 ≥2 篇独立团队后续方法的证据。因而它的数据资产残值与竞争 benchmark 残值必须分开记账。

**MAVEN-FACT。** 112,276 event factuality annotations 的规模和 MAVEN 生态关系是实质资产。citeturn28search3 但是本轮 2025–2026 独立跟进下界为 0*，并没有证据支持“已经形成多人持续刷新榜单”的状态；同样也没有证据允许说它“饱和”。

单卡层面，已有的硬件证据可以形成几个明确边界。TacoERE 论文原配置使用两张 RTX 3090，因此**原样复现实验不是 27GB 单卡已验证方案**。LLMERE 的 7B/8B LoRA 实验使用 A100 40GB，也不能直接声称在 27GB 同 batch/sequence 设置下可原样跑。相反，KnowQA 报单 RTX 3090，Chen 的 RoBERTa-large 部分报单 V100，证明至少某些 relation/causal 方法已有 ≤24/32GB 级别单卡先例。citeturn20view2

本地代码的残值与以上外部 benchmark 残值是两个不同问题。附件实测给出的代码结构是：Tier-1 约 **2,263 行**基本任务无关，Tier-2 约 **2,612 行**方法可迁移但要换数据层，真正 MAVEN+SeDGPL 强绑定的 Tier-3 约 **2,148 行**；而且现有 29/73 个提及 MAVEN 的文件，其耦合主要集中在 loader。fileciteturn0file1 本地还已经让中文 CCKS 金融因果通过同一 EventNode/RelationEdge schema，这是一条真实的跨语言/跨数据集工程验证，而不是未来规划。fileciteturn0file1

所以 MAVEN 系列的四项残值可严格记录为：

| 资源 | 2025–26 方法下界 | test/evaluator 状态 | 饱和度 | 本地残值 |
|---|---:|---|---|---|
| MAVEN | 0*（2024 有活动证据） | hidden test；本轮未完成 submission 验证 | 无法判断 | detection/data/eval 通用部分可迁移 |
| MAVEN-ERE | ≥2 正式 2025 方法，另有 2025 causal work | CodaLab 页面可访问；submission 未验证；多种替代 split | **无法判断** | relation candidate/eval/consistency/calibration 高残值 |
| MAVEN-Arg | 0* | hidden test；CodaLab 本轮未验证 | 无法判断 | argument/schema 处理部分可迁移 |
| MAVEN-FACT | 0* | test/leaderboard 本轮未核 | 无法判断 | factuality/evidence 模块方法残值存在 |

## 2024 后新数据集且已有至少两篇独立跟进的专表

在本轮严格定义下，**没有一项可以被证明达到阈值**。

这里“严格定义”是：数据集发布于 2024 年或以后；数据论文自己的 baseline 不算；原作者/明显同团队继续做的方法不算独立；arXiv-only 不计正式方法；论文必须真正使用该 benchmark，而不是只引用它。

| 2024–2026 新资源 | 数据事实 | 本轮正式独立跟进下界 | 达到 ≥2？ |
|---|---|---:|---|
| **MCECR** | 2024；en/es/hi/tr/uk；5,802 articles；首个五语 cross-document ECR benchmark citeturn26search0 | 0* | **未证实** |
| **CLES** | 2024；20,059 docs；37,688 mention events；>70% cross-document citeturn26search2 | 0* | 未证实 |
| **NarrativeTime / TimeBankNT** | 2024；对 TimeBank-Dense 做 full timeline-based re-annotation citeturn24search4 | 0* | 未证实 |
| **MultiVENT-G** | 2024；14.5h video + 1,168 text docs；22.8K event-centric entities citeturn26search8 | 0* | 未证实 |
| **CMNEE** | 2024；17K Chinese military docs；29,223 events citeturn27search3 | 0* | 未证实 |
| **DocEE-zh** | 2024；>36K events；>210K arguments citeturn27search2 | 0* | 未证实 |
| **OEE-CFC** | 2024；17,469 financial-commentary events；44,221 args citeturn27search0 | 0* | 未证实 |
| **DEIE** | 2024；20K docs；56K+ events；含 19 emergency types citeturn27search12 | 0* | 未证实 |
| **SPEED/SPEED++** | 2024；epidemic ED/EE；SPEED++ 为四语四疾病 citeturn28search0 | 0* | 未证实 |
| **EventRelBench** | 2025；约 35K event-relation questions citeturn5search9 | 0* | 未证实 |
| **EcomScriptBench** | 2025；e-commerce script benchmark citeturn4search9 | 0* | 未证实 |
| **CausalSense** | 2026；>500K mixed-source sentences citeturn5search0 | 0* | 未证实 |
| **Vrittanta-EN** | 2026；11,272 narrative event instances；论文承诺 acceptance 后公开 citeturn24search11 | 0* | 未证实 |

MAVEN-Arg 和 MAVEN-FACT 如果把“2024 年以后”理解为“2024 年及以后”，也仍没有达到本轮审计的 ≥2 独立跟进标准。citeturn14search4turn28search3

这一结果不表示这些数据集“不值得研究”，更不表示“对手少所以容易”。它只回答用户要求的竞争密度事实：**本轮没有找到一个既新、又已经有至少两个独立正式团队形成可审计竞争链的新 benchmark。**

## 未能核实项与与预期不符的事实

**未能核实项。** 最大的缺口是 MAVEN-ERE CodaLab 的登录后 submission 状态。当前可以看到页面和榜单，但没有实际登录完成上传，因此无法判断管理员是否关闭新 submission、上传后 scorer 是否仍运行。citeturn2view0turn3view2

MAVEN detection 与 MAVEN-Arg 各自 CodaLab 的 2026 年实际 submission 状态也没有得到同等级别验证。本轮只验证了官方 repo 仍指向评测通道，不能把链接存在升级成“实际可提交”。citeturn0search0turn14search4

MAVEN-Arg、MAVEN-FACT 的明确 dataset license 没有在本轮已读官方页面中取得，因此保持“未核”，没有根据组织或代码 repo license 猜 dataset license。

MINION 和 NYT-SEG 是两个本轮没有获得足够一手定位的候选名称。报告没有用名称相近的资源替代，也没有凭记忆补充年份、规模或成绩。

ERE、TAC-KBP、CCKS 都不是一个稳定单一 benchmark 名称，而是一系列年份、track 或赛题。没有逐年份实访就把它们各写成一个 train/dev/test 数据集，会制造错误精度，因此总表只保留系列级信息。

ECB+、GVC、FCC、MEANTIME、CD²CR，以及 FactBank/UW/Unified Factuality 的官方下载许可和 2026 状态，本轮没有完成逐站一手实访。它们仍被覆盖在候选表中，但没有冒充已完成核验。

GDELT、ICEWS 和 EM-DAT 的当前官方许可页面，本轮也没有取得足以支持细粒度许可结论的一手证据；因此只把它们作为结构化事件数据库候选列出，没有采用二手页面给出的许可细节作为最终证据。

**与预期不符的事实。**

第一，**ACE05 event extraction 并非 en/zh/ar 三语对等。** 官方 LDC catalog 明确区分了三语 corpus 与 event task 的两语覆盖。citeturn23search4 这意味着把 ACE05 Arabic 直接放入“多语言事件抽取 gold benchmark”会高估它的 event annotation 覆盖。

第二，**“MAVEN-ERE CodaLab Ends: Never”不是 channel-alive 证据。** 它最多证明竞赛 metadata 没有设置结束日期；当前提交动作能否执行仍未验证。citeturn2view0

第三，**MAVEN-ERE 近年论文并没有一致使用官方 test。** 两篇正式论文已经明确建立 valid-as-test 先例。citeturn20view0turn15view0 因而项目过去遇到“官方 test 拿不到，只能退回 valid 自跑”的情况，并不是一个完全脱离学术实践的私有口径；问题在于必须明确声明它是另一套口径，而不是伪装成官方 test。

第四，**LLM 并没有在复杂 ERE 上直接消灭监督模型。** LLMERE 的 Table 2 显示 few-shot Llama2/ChatGPT/GPT-4 在 MAVEN-ERE relation extraction 上明显弱于专门训练的方法；LLMERE 要靠微调和 relation rationales 才进入有竞争力的范围。citeturn16view2 Chen et al. 还把 event-relation logical inconsistency 明确识别为 LLM 的问题。citeturn22view0

第五，**新事件数据集比预想得多，但“新数据集 + 已有多个独立对手”比预想得少。** 2024 一年就可以确认 MCECR、CLES、NarrativeTime、MultiVENT-G、CMNEE、DocEE-zh、OEE-CFC、DEIE、SPEED/SPEED++ 等新资源。citeturn26search0turn26search2turn24search4turn26search8turn27search3turn27search2turn27search0turn27search12turn28search0 但严格的独立 follow-up 门槛并没有随数据集数量同步满足。

第六，**风险数据库与风险 benchmark 并不等价。** ACLED 有持续、真实世界、结构化事件数据和当前 API，但没有天然对应一个事件抽取的主 F1 benchmark。citeturn28search1turn28search4 SPEED/SPEED++ 的特殊之处恰恰在于它把 risk/epidemic application 与事件级 NLP gold 联系起来。citeturn28search0

第七，本地资产“重开就损失整个一万行项目”的直觉并不成立。本地清点显示真正强 MAVEN/SeDGPL 绑定的 Tier-3 约 2,148 行，Tier-1 约 2,263 行基本可无损迁移，Tier-2 的主要成本是数据适配而不是方法全部作废。fileciteturn0file1

## 证据审计表

| 核心结论 | 一手来源 / ID | 表号或位置 | split / evaluator / metric 审计 |
|---|---|---|---|
| MAVEN：4,480 docs、118,732 event mentions、168 types | MAVEN, `2020.emnlp-main.129`, DOI `10.18653/v1/2020.emnlp-main.129` citeturn0search4 | dataset paper | 数据事实齐；非方法分数 |
| MAVEN repo：MIT、download、`evaluate.py` | THU-KEG/MAVEN-dataset citeturn0search0 | README/repo | evaluator 文件存在；submission 当前状态未核 |
| ACE05 event task only English+Chinese | LDC2006T06 citeturn23search4 | official catalog Introduction/Data | 数据任务范围证据齐 |
| RAMS 9,124 events，train/dev/test public | JHU RAMS official page citeturn23search5 | Data section | test gold 可得；模型 score 需另审 scorer |
| WikiEvents train/dev/test public download | gen-arg official repo citeturn23search0 | Datasets section | split 文件存在；dataset license 未定位 |
| DocEE 27,485 docs / 180,528 args | official DocEE repo citeturn23search13 | Statistics | 数据事实齐 |
| Doc2EDAG toolkit 要求至少 4×V100 16GB | DocEE toolkit citeturn23search3 | Reproduce Results | 硬件证据齐 |
| MAVEN-ERE 规模、relations、GPL repo、official evaluator | MAVEN-ERE official repo/paper citeturn26search1 | README / `evaluate.py` | dataset/test 事实齐 |
| MAVEN-ERE CodaLab 可访问但提交未验证 | official CodaLab competition citeturn2view0turn3view2 | live page | 页面/榜单已验；**submit 未验** |
| Chen 2024 valid-as-test | ACL 2024 `2024.acl-long.512`, DOI `10.18653/v1/2024.acl-long.512` citeturn17search2turn20view0 | **Appendix E** | split **完整**；与 hidden test 不可比 |
| LLMERE valid-as-test | COLING 2025 `2025.coling-main.500` citeturn15view0 | **Appendix C** | split **完整** |
| LLMERE MAVEN-ERE 52.5 Overall | `2025.coling-main.500` citeturn16view2 | **Table 2** | split 明确；evaluator、negative class、Overall 聚合未完整取得 → **不可比** |
| TacoERE causal F1 34.1 | LREC-COLING 2024 `2024.lrec-main.1348` citeturn14search3 | **Table 1** | split/relations/P-R-F1 可定位；evaluator及完整 metric definition 不全 → **不可比** |
| KnowQA 是 sampled causal + MAVEN-Arg argument | Findings EMNLP 2024 `2024.findings-emnlp.986`, DOI `10.18653/v1/2024.findings-emnlp.986` citeturn14search10 | Table 2 / experiment setup | sampled，不是 full benchmark |
| MAVEN-Arg 98,591 / 290,613 / 162 / 612 | ACL 2024 `2024.acl-long.224`, DOI `10.18653/v1/2024.acl-long.224` citeturn14search4 | Abstract / dataset section | 数据事实齐 |
| LC4EE 使用 MAVEN-Arg，但与数据团队作者重叠 | `2024.findings-acl.715`, DOI `10.18653/v1/2024.findings-acl.715` citeturn14search0 | author list / abstract | 只用于独立性计数 |
| MAVEN-FACT 112,276 events | `2024.findings-emnlp.651`, DOI `10.18653/v1/2024.findings-emnlp.651` citeturn28search3 | Abstract | 数据规模齐；follow-up 未取得 |
| MCECR 五语、5,802 articles | `2024.findings-naacl.245`, DOI `10.18653/v1/2024.findings-naacl.245` citeturn26search0 | Abstract | 数据事实齐；license/test 待补 |
| NarrativeTime / TimeBankNT | `2024.lrec-main.1054` citeturn24search4 | Abstract | full reannotation 事实齐；follow-up 不足 |
| OEE-CFC 17,469 events / 44,221 args / 21 roles | `2024.findings-emnlp.256`, DOI `10.18653/v1/2024.findings-emnlp.256` citeturn27search0 | Abstract | 数据事实齐；SOTA 四轴未审 |
| CMNEE 17K docs / 29,223 events | `2024.lrec-main.299` citeturn27search3 | Abstract | 数据事实齐 |
| DocEE-zh >36K events / >210K args | `2024.findings-emnlp.35`, DOI `10.18653/v1/2024.findings-emnlp.35` citeturn27search2 | Abstract | 摘要 45.88 F1 缺本报告要求四轴，不认 strict-best |
| DEIE 20K docs / 56K+ events / 19 emergency types | `2024.lrec-main.410` citeturn27search12 | Abstract | 数据事实齐；download/test 待补 |
| CLES 20,059 docs / 37,688 events | `2024.findings-acl.114`, DOI `10.18653/v1/2024.findings-acl.114` citeturn26search2 | Abstract | “~72 F1”只有摘要级信息，不作 strict-best |
| MultiVENT-G 数据随 ACL 附件发布 | `2024.findings-emnlp.934` citeturn26search8 | Abstract / Data attachment | 数据可得证据强；metric/split 仍需审 |
| SPEED/SPEED++ epidemic benchmark | official SPEED project citeturn28search0turn28academia44 | Dataset / Experimental Benchmarking | 任务/规模事实齐；当前 leaderboard 不适用 |
| ACLED 要注册，API 要认证 | ACLED official docs citeturn28search1turn28search4 | FAQ / Getting Started | 当前访问事实齐；非 NLP evaluator |
| CRAB ~2.7K causal pairs | `2023.emnlp-main.940`, DOI `10.18653/v1/2023.emnlp-main.940` citeturn25search0 | Abstract | 数据事实齐；ACCESS 本轮仅 arXiv，不计正式 follow-up |
| TORQUE 3.2K snippets / 21K questions | `2020.emnlp-main.88`, DOI `10.18653/v1/2020.emnlp-main.88` citeturn24search0 | Abstract | 数据规模齐；2026 leaderboard 未核 |
| EventRelBench ~35K / EventRelInst ~48K | `2025.findings-emnlp.482`, DOI `10.18653/v1/2025.findings-emnlp.482` citeturn5search9 | paper | follow-up threshold 未满足 |
| Vrittanta-EN “will be publicly released” | `2026.lrec-1.616` citeturn24search11 | Abstract | **实际 release 未验证**，故不写“已公开下载” |
| 本地代码残值 | `LOCAL_ASSET_INVENTORY.md` | §1–§4 | 9,962 LOC；Tier-1 2,263；Tier-3 2,148；本地实测 fileciteturn0file1 |

本轮证据能够稳健支持的最终事实不是“某个数据集最容易做”，而是：**事件类公开资源数量仍在增加，MAVEN-ERE 也仍有方法研究；但真正同时满足“数据公开、test 可得或评测通道可验证、近年有多个独立已发表方法、且这些方法在同 split/同 evaluator/同指标定义上可比较”的资源集合，要比单纯的数据集名单小得多。** MAVEN-ERE 尤其说明，竞争论文数量高并不能替代评测基础设施的可审计性；2024+ 新资源则表现出相反问题——数据新，但目前还难以证明形成了 ≥2 个独立团队的成熟可比竞争链。citeturn20view0turn15view0turn26search0turn27search2turn28search0