# DR-I：ECB+ / GVC / FCC 事件共指固定协议资格审查

> ⛔ **暂停执行（2026-08-27）**：作者要求停止按单一语料不断增加资格门，先恢复事件图谱构建的
> 组件化论文主线。本文保留为历史提示词草案，当前不要提交给网页版 Deep Research；后续若需要事件共指
> 外部检索，将改写为“为 Ch1 补充可统一重跑的方法与数据”，而不是用零修补作者闭环做 GO/NO-GO。

## 给执行者的说明

请在一个新的 ChatGPT「深度研究」对话中执行本提示词。**只上传以下四个 Markdown 附件：**

1. `SYNTHESIS_DECISION.md`
2. `B_datasets_audit.md`
3. `C_methods_code_audit.md`
4. `H_temporal_protocol_audit.md`

四个文件都位于项目的 `docs/replan/` 目录。附件只提供已知边界、既有纠错和验收标准，不能代替外部
一手核验。**不需要上传任何 PDF，也不需要上传 F/G/H 的原始深度研究报告。**

请将最终结果同时导出为：

- `I_event_coref_protocol.md`
- `I_event_coref_protocol.pdf`

如果界面不能生成带可点击链接的 Markdown，不要因此省略来源：在报告末尾建立
“Plain-text Source Registry”，每个来源单独一行写完整 `https://...` URL。PDF 表格容易截断，正文
表格最多五列；逐论文长字段改用小标题和项目列表，不要制作横向超宽表。

完成后把两份文件放入项目的 `docs/replan/` 目录，再回到本地 Codex 会话。不要在网页版对话中继续
设计模型、章节或启动实验。

---

## 可直接复制给深度研究模型的提示词

你是一名严谨的 NLP benchmark、数据许可、coreference evaluator 与代码复现审计员。当前日期为
**2026-08-27**。你的任务不是设计新模型或论文章节，而是判断：

> **ECB+、Gun Violence Corpus（GVC）或 Football Coreference Corpus（FCC）上的 cross-document
> event coreference resolution，能否冻结出一条完全公开、可在本地重跑、拥有至少两个互相独立的
> 2024–2026 正式方法、且两个方法均可在单张约 27GB GPU 上复现的硕士论文主指标协议？**

此前依次审计的 EventStoryLine/Causal-TimeBank ECI、MAVEN-ERE causal、MATRES/TB-Dense temporal
均因数据许可或同协议双 baseline 不足而判 NO-GO。本轮不得降低标准，也不得通过混合数据集、mention
setting、topic setting、singleton policy 或 evaluator 凑对手。

本轮允许最终只选择 ECB+、GVC、FCC 中的一套数据轴；**两个合格方法必须落在同一 exact axis**。
不能用“一个方法在 ECB+、另一个方法在 GVC”拼成两个对手，也不能把同一论文的模型与消融算成两个
独立方法。

## 一、先固定任务边界与正式身份

### 1. 任务边界

目标任务是 cross-document event coreference resolution（CDECR/CD-ECR）：给定一组相关或待检索的
documents，将指向现实中同一 event occurrence 的 event mentions 聚成 clusters。

以下任务必须排除或单列，不能与目标主指标混表：

- within-document event coreference；
- entity coreference、entity linking 或 event argument coreference；
- event detection/trigger identification 与端到端 event extraction，除非能拆出完全相同的 gold-mention
  clustering 主指标；
- MAVEN-ERE、ACE、KB event linking、event schema induction、script/eventuality clustering；
- cross-lingual transfer 或 multilingual coreference，除非使用同一 ECB+/GVC/FCC test manifest；
- ECB+ `devsmall`、随机 sample、人工 X-AMR 子集或闭源 API 成本抽样；
- 只做 pairwise event similarity/classification、但没有按同一 clustering pipeline 和 scorer 生成最终
  clusters 的 setting；
- topic detection、document retrieval 或 candidate pruning 单项指标，除非最终还在完整 gold test
  universe 上报告同一 coreference 主指标。

### 2. 正式论文与仓库身份

对每篇论文先从 ACL Anthology、正式 proceedings 或出版方 PDF 提取：精确题名、全体作者、venue、
年份、论文 ID、DOI。之后再判断仓库是否由作者团队发布，不得只按方法缩写匹配 GitHub。

至少筛查并核实：

1. ECB+ 数据论文、官方语料页及实际下载/许可来源；
2. GVC 数据论文、官方语料页及实际下载/许可来源；
3. FCC 数据论文、官方语料页及实际下载/许可来源；
4. `2024.acl-long.164`：*Synergetic Event Understanding for Cross-document Event Coreference
   Resolution*，以及作者 SECURE 仓库；
5. `2024.lrec-main.920`：*Linear Cross-document Event Coreference Resolution with X-AMR*；
6. 2024–2026 ACL、EMNLP、NAACL、EACL、COLING、LREC-COLING、TACL、CL、AAAI、IJCAI 等正式发表、
   实际使用 ECB+/GVC/FCC 的其他 CDECR 方法；
7. 被近期论文实际重跑的旧监督方法，只作为工程 sanity 和 protocol lineage，不代替“两个独立
   2024–2026 正式对手”的门槛。

若论文只引用 ECB+/GVC/FCC 旧表、只在小样本上评测、只发布 pairwise 结果或根本未使用这些语料，
必须明确排除理由。

## 二、先建立 protocol map，禁止先比较分数

分别建立 ECB+、GVC、FCC 的 protocol map。每个数据集内部若存在不同 preprocessing/evaluator setting，
继续拆为 A/B/C 子轴。至少核验以下项目。

### 1. 数据版本、原文与许可

- 官方 URL、版本/tag/release、下载方式、许可文件或用户协议；
- raw documents、event mentions、event clusters 分别由哪个 release 提供；
- 是否需要申请、登录、签署协议、LDC/其他付费许可，或只能取得 annotation 而没有原文；
- 仓库中的 derived JSON/pickle/token cache 是否含可再分发的新闻原文；其许可证是否覆盖上游文本；
- 精确 topics、subtopics、documents、event mentions、clusters、singletons 数量及逐 split 统计；
- duplicate documents、同文异名、空 cluster、跨 topic cluster、token/span mismatch 如何处理；
- 下载环境允许时，记录 archive/release SHA-256；否则写明未计算，不得猜测。

必须区分：annotation 可下载、raw text 可下载、本地研究使用获准、允许公开再分发。GitHub public 或代码
MIT/Apache 许可证不能自动扩张到新闻原文和数据 annotation。

### 2. Split 与 topic/document universe

- train/dev/test 的 exact topic IDs、subtopic IDs、document IDs 和生成脚本；
- ECB+ 常见 topic split、topic 1–35/36–45 等写法是否在各论文中完全一致；
- 是否排除某些 topics、只用 selected subtopics、`devsmall` 或重新随机划分；
- GVC/FCC 的 official split 是否真实存在，还是由各方法自行切分；
- 文档是按 gold topic 分组后独立聚类，还是系统还要预测 topic/document grouping；
- test 时是否使用 gold topics、predicted topics、retrieved document sets 或 all documents；
- preprocessing 后的 test mention IDs 是否能够逐个映射回 official annotation；
- seed、文件顺序、manifest 和 checksum 是否公开可重建。

“都写 standard split”不等于 split 相同。只要 test document/mention manifest、topic grouping 前提或
excluded topics 不同，就拆成不同协议轴。

### 3. Gold mentions、clusters 与 singleton policy

- test 时 event mentions 是 gold-given、predicted，还是 gold triggers + predicted spans/arguments；
- gold mention 类型和 span 定义：action、state、reporting、time/location 等是否全部纳入；
- mention alignment 是 exact span、head match、token overlap 还是作者映射表；
- 系统只聚类 gold mentions，还是允许 missing/extra predicted mentions；
- gold singleton clusters 是否存在、是否进入训练、预测和评测；
- singleton 是预先删除、由 scorer 忽略，还是系统漏掉 mention 后由 evaluator 自动补 singleton；
- pairwise classifier 的 candidate universe 是同 topic all pairs、句/文窗口、retrieval top-k 或启发式
  pruning；test gold pairs 是否可能被 pruning 删除；
- clustering 使用 connected components、agglomerative clustering、best-first、correlation clustering
  或其他解码；threshold 是否在 dev 固定；
- event arguments、time/location、LLM summaries、AMR/X-AMR 是输入特征还是改变 gold 定义。

gold mentions vs predicted mentions、with-singletons vs without-singletons、gold-topic vs predicted-topic
必须视为不同 setting。不得只因最后都输出 clusters 就合并。

### 4. Evaluator 与 headline metric

- 官方或作者 scorer 的 URL、commit、文件路径、版本和最短运行命令；
- 使用官方 CoNLL-2012 Perl scorer、`reference-coreference-scorers`、coval、作者自实现，还是其他代码；
- MUC、B³、CEAF_e、CEAF_m、BLANC、LEA、CoNLL F1、pairwise F1 各自如何定义；
- headline CoNLL F1 是否严格为 MUC/B³/CEAF_e 三个 F1 的算术平均；
- metric 是先对所有 topics 拼接统计，还是逐 topic/fold 算后 macro average；
- singleton、missing mention、extra mention、empty system cluster、duplicate mention 如何计分；
- scorer 是否自动把系统遗漏的 gold mentions补为 singleton；
- predicted mentions 是否先经过 mention matching；matching 是否影响 coreference score；
- 多 seed/fold 是 mean±std、best dev seed，还是一次 run；论文表格使用哪个字段；
- 同一论文中的 B³-only prompting 表是否能与主表 CoNLL F1 比较。

“都报告 CoNLL F1”仍不够；必须证明 scorer version、mention manifest、singleton policy 与 topic aggregation
相同。不得用单项 B³/CEAF_e 高分代替聚类 headline。

## 三、优先核验 SECURE 轴，但不得预设它合格

现有附件已指出 SECURE 在 ECB+/GVC/FCC 的同一作者代码路径中比较 direct GPT-4、RoBERTa-large 和
GPT-4 event summaries + RoBERTa-large。请把它作为第一个 protocol anchor，逐项确认：

- 论文 Table 2、Table 5 的 exact split、gold mentions、singletons 和 scorer；
- SECURE 仓库 official URL、default branch、审计日 HEAD、license、release/tag；
- `src/models/coref_scorer.py`、`run_pairwise_classification.py` 及真实入口/配置是否存在；
- 数据下载、预处理、train、predict、cluster、evaluate 是否闭环；
- GPT-4 summaries 是可公开取得的静态 artifact，还是必须重新调用闭源 API；
- summary cache 是否覆盖全部三数据集与所有 split，是否包含不可再分发原文；
- RoBERTa-large baseline 是作者在同一 pipeline 重跑，还是 copied-only；
- direct GPT-4 的截断、输出解析、invalid clusters 与 API snapshot 如何处理；
- 论文的 85.2/84.7/71.7 和 86.7/87.4/78.7 等数值分别属于哪一 setting，必须回一手表格核实，
  不得从附件直接复制。

SECURE 的 RoBERTa baseline、SECURE hybrid 和 direct GPT-4 均来自同一论文/团队，**不能计作三个独立
近期对手**。闭源 GPT-4 API 也不能仅凭“本地 GPU 不承担生成”就算作单张 27GB 自包含路径。

## 四、逐论文审计记录

不要制作会在 PDF 中截断的超宽表。每篇候选论文用一个小标题，按以下字段列项目：

- 正式身份：标题、作者、venue、年份、论文 ID、DOI；
- 独立性：与数据原团队、SECURE 团队和其他候选的作者交集；
- 数据轴：ECB+/GVC/FCC 的哪个精确 version/setting；
- split/topics：exact manifests、gold/predicted topic 前提；
- mentions/clusters：gold/predicted mentions、singleton policy、candidate pruning、cluster decoder；
- metric/evaluator：scorer、commit、CoNLL 构成、aggregation；
- baseline provenance：本仓库实跑、作者重实现，还是 reported/copied-only；
- repository：官方 URL、default branch、HEAD、license、release、最后更新时间；
- execution closure：raw → preprocess → train → predict → cluster → evaluate；
- missing items：数据、脚本、配置、checkpoint、LLM cache、API、私有 retrieval/index；
- hardware：GPU 型号/数量/显存、precision、batch、max length、epochs、运行时间。

论文未声明就写“未声明”；仓库/文件未取得就写“未取得”，不要按常见做法补猜。

## 五、仓库必须检查实际 tree 与完整历史

对最可能落在最终轴的每个作者仓库：

1. 记录 default branch、HEAD commit、license、release/tag、最后更新时间；
2. 检查完整 tree 与 Git 历史，确认关键数据、配置、checkpoint 或 evaluator 不是曾存在后删除；
3. 阅读 README、requirements/environment、download/preprocess、split、train、predict、cluster、evaluate；
4. 检查 imports、README 命令、config/checkpoint/cache 路径是否真实存在；
5. 搜索作者机器绝对路径、私有数据、未发布 mention map、topic cache、LLM output、API key；
6. 检查 published predictions/checkpoints 是否能映射到目标 test mention manifest；
7. 检查 scorer 是否为真正执行路径，而不是未被 caller 使用的孤立文件；
8. 若环境不能 clone/执行，只能标“静态未验证”，不能写“可运行”；
9. 只有 evaluator、processed data 或 prediction artifact，不等于完整训练闭环。

如果 archive 只有代码快照而无 Git 历史，也必须如实写明，不能虚构 default branch/HEAD。

## 六、寻找两个独立的 2024–2026 baseline

目标是在**同一个冻结数据集与 exact protocol axis**上找到至少两个同时满足以下条件的方法：

- 2024–2026 正式发表；
- 作者团队互相独立，作者重叠逐人核对；
- 作者官方代码当前可取得；
- 使用相同 data version、split/topic manifest、test mention IDs、singleton policy 和 evaluator；
- 从公开输入走到最终 clustering headline；
- 不依赖不可取得数据、私有 topic/mention cache、70B、多 GPU 或必须重新调用的闭源 API；
- 有可信单张约 27GB GPU 路径。

旧方法可以作为 sanity baseline，也可以被近期论文在同一 pipeline 中重跑，但不能替代两个独立近期
方法。最多推荐两个真正最合格的 baseline，并分别给出：

- 选择理由与团队独立性；
- 所属唯一协议轴；
- 精确数据、commit、environment、checkpoint/prediction；
- raw data 到最终 CoNLL/其他 headline 的最短命令链；
- 必要修补及其是路径/版本修复，还是已变成重新实现；
- CPU smoke 与最小 GPU smoke分别要验证什么；
- 27GB 风险及证据等级：论文声明、代码静态估算、本地实测必须分开。

若找不到两个，直接判当前 NO-GO。不得用以下方式凑数：

- ECB+ 与 GVC/FCC 各取一个方法；
- gold mentions 与 predicted mentions；
- with-singletons 与 without-singletons；
- gold topics 与 predicted/retrieved topics；
- full test 与 `devsmall`/随机 sample；
- CoNLL F1 与 B³-only、LEA-only 或 pairwise F1；
- 同一论文的 baseline、hybrid、prompt 或消融；
- 同一作者团队的连续论文；
- 作者表中 copied-only 数字冒充当前可执行 baseline。

## 七、27GB 与闭源依赖门槛

逐候选核验：

- 论文实际 GPU 型号、数量、显存和训练时间；
- encoder、Longformer、cross-encoder、graph encoder 或 seq2seq 的精确 backbone；
- precision、sequence length、pair batch、gradient accumulation、epochs、pair/cache 规模；
- 是否需要把全 topic event pairs 同时驻留 GPU，还是可离线编码/分批聚类；
- 是否有作者 checkpoint/predictions，可先做 CPU scorer replay；
- 是否依赖 GPT-4/Claude 等闭源 API、未发布 summaries/embeddings 或 70B outputs；
- 若使用 LLM-generated summaries，公开 cache 是否足以重放，生成成本与预测模型成本必须分开；
- “RoBERTa-large 通常能放入 27GB”只能算静态高可行，不能代替论文配置或本地 smoke。

如果一个候选的公开闭环必须重新调用闭源 API，它不能作为本项目要求的自包含 27GB baseline；若作者
公开了完整、合法可用、与 test manifest 绑定的固定 cache，则单独评价“artifact replay”与“从 raw
input 完整复现”，不能混写。

## 八、Go/No-Go 门槛

报告末尾逐项给 PASS / CONDITIONAL / FAIL：

| 门槛 | PASS 标准 |
|---|---|
| 数据与许可 | annotation、raw documents、mentions/clusters 均可合法取得并绑定版本/hash |
| Split/topics | exact topic/document/mention manifests 与 gold/predicted topic 前提可重建 |
| Mentions/clusters | gold/predicted mention、singleton、candidate pruning、cluster decoder 可重建 |
| Evaluator | 同一 scorer/version 可从 clusters 到公开 headline，并锁定 aggregation |
| 对手 | 至少两个独立 2024–2026 方法在该 exact axis 有作者公开执行闭环 |
| 算力 | 两个 baseline 均有可信单张约 27GB 自包含路径 |

判定规则：

- **GO**：六项全 PASS；
- **CONDITIONAL GO**：只剩一次本地 CPU 或最小 GPU smoke 可以解决的运行性证据；
- **NO-GO**：数据许可、split/topics、mentions/clusters、evaluator 任一不可锁，或不足两个独立同轴
  可执行 baseline。

“我们可以自己统一重写所有 baseline”、重新生成 GPT summaries、重划 split 或改 singleton/scorer
policy，均不能把 NO-GO 改成 GO。

## 九、最小停止规则

按以下顺序工作，以避免无效检索：

1. 先锁三个数据集的许可、版本和 exact split；
2. 再锁 SECURE 的真实 setting 与 scorer；
3. 搜索并核验是否存在第二个独立 2024–2026 同轴、公开完整方法；
4. 若第二方法不存在、不同 setting 或代码不闭环，立即给 NO-GO；
5. 只有双 baseline 门仍可能 PASS 时，才深入硬件与最短命令链；
6. 不启动任何训练或大模型调用。

不要为了写长报告而继续深挖已确定不兼容的分支。负结果是有效交付。

## 十、输出结构

1. Executive verdict
2. Identity corrections and scope exclusions
3. ECB+ protocol map
4. GVC protocol map
5. FCC protocol map
6. Most-qualified exact protocol
7. Frozen data/split/mention/cluster/evaluator specification
8. Per-paper audit records
9. Repository execution audit
10. Independent-team and compatibility matrix（窄表）
11. Two-baseline recommendation（或明确无法选择）
12. 27GB and closed-dependency feasibility
13. Go/No-Go gates
14. 未能核实与下一步最小本地检查
15. Plain-text Source Registry

## 十一、引用与禁止事项

- 关键判断只用正式论文 PDF、作者官方仓库、数据官方页面/release、官方/实际 scorer 等一手来源。
- 每条论文事实注明 section/table/page；代码事实注明 commit 和文件路径。
- 每个关键来源在正文附近给出完整 URL，并在 Source Registry 再列一次 plain-text URL。
- Markdown 不得只留 `turnXsearchY`、`filecite` 等内部 token；若系统强制生成内部引用，仍必须另附 URL。
- 不设计章节、不提出新模型、不写本项目实现代码、不运行或建议立即启动大规模训练。
- 不按“谁分数低容易超过”推荐，不把不同 protocol 的 headline 数字排成 SOTA 时间线。
- 不把“论文使用某数据集”写成“当前代码可复现”，不把“未找到”写成“绝对不存在”。
- 附件与一手来源冲突时，以一手来源为准，并在 identity corrections 中明确更正。
