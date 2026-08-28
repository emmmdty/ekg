# DR-H：MATRES / TB-Dense 时间关系固定协议资格审查

## 给执行者的说明

请在一个新的 ChatGPT「深度研究」对话中执行本提示词。建议只上传以下四个附件：

1. `SYNTHESIS_DECISION.md`
2. `B_datasets_audit.md`
3. `C_methods_code_audit.md`
4. `G_maven_causal_protocol_audit.md`

附件只提供已知边界与审计标准，不能代替外部一手核验。**不需要上传这些文档的 PDF，也不需要上传
F/G 原始深度研究报告。**

请将最终结果同时导出为：

- `H_temporal_protocol.md`
- `H_temporal_protocol.pdf`

如果界面不能生成可点击的 Markdown 链接，不要因此省略来源：在报告末尾建立“Plain-text Source
Registry”，每个来源单独一行写完整 `https://...` URL。PDF 表格容易截断，因此正文表格最多五列；
逐论文长字段改用小标题和项目列表，不要制作横向超宽表。

完成后把两份文件放入项目的 `docs/replan/` 目录。

---

## 可直接复制给深度研究模型的提示词

你是一名严谨的 NLP benchmark、数据许可与代码复现审计员。当前日期为 **2026-08-27**。你的任务
不是设计新模型或论文章节，而是判断：

> **MATRES 或 TimeBank-Dense（TB-Dense）上的 event temporal relation classification/extraction，能否
> 冻结出一条完全公开、可在本地重跑、拥有至少两个独立 2024–2026 正式方法、且可在单张约 27GB
> GPU 上复现的硕士论文主指标协议？**

前两个候选已经失败：EventStoryLine/Causal-TimeBank ECI 没有两个同协议公开可执行 baseline；
MAVEN-ERE causal 虽已锁定公开协议，但仍没有第二个同协议 baseline。本轮不得降低标准，也不得把
MATRES、TB-Dense、TIMELINE、HiEve、MAVEN-ERE temporal、clinical temporal relation extraction 或
temporal knowledge graph completion 的数字混在一起凑对手。

本项目本地已有 MATRES annotation 文件，但这只证明文件存在，**不证明来源文本许可、版本、split、
pair universe 或 evaluator 已合规**。所有资格结论仍需从一手来源重新建立。

## 一、先做范围与身份校验

### 1. 任务边界

本轮目标是从文本和给定/检测到的 event mentions 预测 event-event temporal relations。必须排除或单列：

- temporal knowledge graph completion/reasoning；
- time expression identification/normalization；
- clinical temporal relation extraction，除非它使用本轮同一 MATRES/TB-Dense 数据和 evaluator；
- temporal QA、event ordering 或 timeline generation，除非能证明其主指标就是同一 pair classification；
- MAVEN-ERE temporal、HiEve、TIMELINE、NarrativeTime/TimeBankNT 等不同数据协议；
- 只在自造 sample、private split 或闭源 API 输出上评测的 setting。

### 2. 正式论文身份

对每篇论文先从 ACL Anthology/正式 proceedings PDF 提取：精确题名、全体作者、venue、年份、ACL ID、
DOI。再判断仓库是否属于作者团队，不得只凭方法缩写或搜索摘要匹配。

至少筛查并核实以下候选；若其实际不使用 MATRES/TB-Dense，必须明确排除理由：

1. MATRES 数据论文及其官方数据/代码来源；
2. TimeBank-Dense 数据论文及其官方数据/代码来源；
3. `2024.emnlp-main.1136`：*Will LLMs Replace the Encoder-Only Models in Temporal Relation Classification?*；
4. `2024.findings-acl.89`：ConTempo；
5. `2024.findings-emnlp.47`：Temporal Cognitive Tree；
6. `2025.coling-main.500`：LLMERE（只审其 temporal/MATRES 路径，不沿用 causal 结论）；
7. `2025.findings-emnlp.428`：GDLLM；
8. `2025.findings-emnlp.1010`：*Consistent Discourse-level Temporal Relation Extraction Using Large
   Language Models*；
9. 你从 2024–2026 ACL/EMNLP/NAACL/COLING/EACL/Findings 等正式论文中找到的其他 event temporal
   relation 方法。

旧方法可以作为工程 sanity 或论文对比来源，但不能替代“至少两个独立 2024–2026 正式方法”的门槛。

## 二、先画协议轴，禁止先排分数

分别建立 MATRES 和 TB-Dense 的 protocol map。若同一数据集内部仍有多个 preprocessing/evaluator
setting，继续拆成 A/B/C 子轴。至少回答：

### 1. 数据与文本来源

- annotation 官方 URL、版本/tag、release 文件、SHA-256（环境允许下载时）；
- underlying documents 来自 TimeBank、AQUAINT、Platinum、TempEval 或其他来源中的哪些部分；
- annotation 可下载是否等于原始文本也可合法取得；是否需要 LDC/付费/单独协议；
- 仓库内若带 reconstructed text、tokenized text 或 derived CSV，其许可是否允许本项目使用和再分发；
- 精确文档数、event mentions 数、annotated pairs 数及逐 split 计数；
- duplicate、intersection、缺文档、改名、tokenization mismatch 的处理。

必须区分“annotation 公开”“raw text 公开”“本地已有副本”“可再分发”四件事。若最终训练输入需要
不可合法公开取得的 source text，公开数据门直接 FAIL，不得用本地碰巧存在的文件掩盖。

### 2. Split

- train/dev/test 的精确 document IDs 或 pair IDs；
- MATRES 常见的 TimeBank/AQUAINT/Platinum 角色到底如何对应 train/dev/test；
- 论文所写 182/73/20 documents 等统计是否能由公开文件逐 ID 重建；
- TB-Dense 的官方 document split、cross-validation 或其他历史 split；
- 是否存在把 train/dev 合并、重新随机划分、删除文档或只取 intersection 的变体；
- seed、manifest、生成脚本、文件顺序是否公开；
- 同名 “official split” 是否真的产生相同 test pair IDs。

### 3. Gold 前提与 candidate universe

- gold event triggers/mentions 是否给定；是否还包含 event detection；
- 是只分类 gold annotated/linked pairs，还是枚举句内、邻句、窗口或全文 all pairs；
- train/dev/test 是否使用相同 candidate generation；
- 是否删除 `VAGUE/NONE`，删除发生在训练、评测还是两者；
- temporal labels 的完整集合以及 `BEFORE/AFTER`、`INCLUDES/IS_INCLUDED`、`EQUAL/SIMULTANEOUS` 的
  方向与映射；
- 是否把逆关系 canonicalize 为单向 pair；是否交换事件顺序做 augmentation；
- 是否使用 temporal transitive closure、closure-expanded gold、graph consistency repair；
- 是否只评 intra-sentence、cross-sentence 或二者；是否分开报告。

只要 test pair IDs、label mapping、`VAGUE` 处理或 closure 规则不同，就不能视为同一协议。

### 4. Evaluator 与主指标

- evaluator 的官方/作者仓库 URL、commit、文件路径和最短命令；
- micro-F1、macro-F1、accuracy、per-class F1 或 temporal-awareness score 中哪个是论文 headline；
- micro-F1 是否包含全部标签，是否排除 `VAGUE/NONE`；
- 单标签多类 micro-F1 是否数学上等于 accuracy，论文是否混称；
- fold/seed 的聚合方式：先拼 predictions 再算、fold macro、还是多 seed mean±std；
- invalid output、unknown label、missing pair 如何计分；
- scorer 是否使用 closure/reduced graph，prediction 是否先做一致性修复；
- 不同仓库的 sklearn `classification_report` 是否输入完全相同的 label list 与 pair list。

“都报告 micro-F1”不等于同 evaluator；必须比较 scorer 输入的 exact pair manifest 和 labels。

## 三、优先核验最可能通过的轴

先用轻量证据筛选所有协议轴，再只对最可能通过的一条做完整仓库闭环审计。优先顺序不是按分数低，
而是：

1. 所有 test input 和 gold 本地可合法取得；
2. exact split/pair/label/evaluator 可公开重建；
3. 至少两个独立 2024–2026 方法确实共享该协议；
4. 两个方法都有作者代码和可信单卡路径。

若 MATRES 某一轴满足这些条件，就不必为凑篇幅深挖必然不兼容的 TB-Dense 轴；但仍要用简短排除表
说明 TB-Dense 为什么没有成为最终轴。反之亦然。

## 四、逐论文审计记录

不要使用会在 PDF 中截断的超宽表。每篇论文用一个小标题，按以下字段列项目：

- 正式身份：标题、作者、venue、年份、ACL ID、DOI；
- 独立性：与数据原团队及其他候选的作者交集；
- 数据与协议轴：MATRES/TB-Dense 哪个精确 setting；
- split：exact IDs/seed/manifest 是否公开；
- gold/candidates：trigger 和 pair 前提；
- labels/closure：映射、`VAGUE`、inverse、closure；
- metric/evaluator：代码路径、commit、聚合方式；
- baseline provenance：本仓库实跑、作者重实现，还是 copied/reported-only；
- repository：官方 URL、default branch、审计日 HEAD、license、release/archive；
- execution closure：raw → preprocess → train → predict → evaluate；
- missing items：数据、脚本、checkpoint、配置、私有缓存、API；
- hardware：GPU 型号/数量/显存、precision、batch、length、epochs。

论文未声明就写“未声明”；仓库/文件未取得就写“未取得”，不要按常见做法补猜。

## 五、仓库必须检查实际 tree 与历史

对最终轴的每个候选作者仓库：

1. 记录 default branch、HEAD commit、license、release/tag、最后更新时间；
2. 检查完整 tree 与 Git 历史，确认关键文件不是曾存在后删除；
3. 阅读 README、requirements/environment、preprocessing、split、train、predict、evaluator；
4. 检查 imports 指向的本地模块、README 命令和配置文件是否真实存在；
5. 搜索作者机器绝对路径、未发布 raw text、private pair cache、checkpoint、闭源 API；
6. 检查 published predictions 或 checkpoints 是否真的属于目标 test manifest；
7. 若环境不能 clone/执行，只能标“静态未验证”，不能写“可运行”；
8. 仅有 evaluator、预处理或 prediction artifact 不等于完整训练闭环。

## 六、寻找两个独立近期 baseline

目标是在**同一个冻结协议轴**上找到至少两个同时满足以下条件的方法：

- 作者团队互相独立，且与数据原作者的重叠如实记录；
- 2024–2026 正式发表；
- 作者官方代码当前可取得；
- 使用相同 raw/derived data、split manifest、test pair IDs、labels 和 evaluator；
- 能从公开输入走到最终主指标；
- 不依赖不可取得 source text、private split/cache、70B 或多个闭源 API；
- 有可信单张约 27GB GPU 路径。

最多推荐两个方法。对每个方法给出：

- 选择理由与作者独立性；
- 所属唯一协议轴；
- 数据、代码 commit、environment/checkpoint；
- raw data 到最终指标的最短命令链；
- 必要修补及其是否只是路径/版本修复，还是已变成重新实现 baseline；
- CPU smoke 和最小 GPU smoke 各自需要验证什么；
- 27GB 风险与预计峰值证据等级（论文声明、静态估算、本地实测分开）。

如果找不到两个，直接判当前 NO-GO。不得用以下方式凑数：

- MATRES 与 TB-Dense 各取一个方法；
- 同一论文的两个模型或两个 prompt；
- 同一作者团队的连续论文冒充独立团队；
- 一个 official split 与一个重新随机 split；
- 一个删除 `VAGUE`、另一个保留 `VAGUE`；
- 一个 pair classification、另一个 closure/timeline score；
- reported-only 数字冒充当前代码可复现结果。

## 七、27GB 与执行门槛

逐候选核验：

- 论文实际 GPU 型号、数量、显存和总训练时间；
- repo 默认模型、precision、sequence length、batch、gradient accumulation、epochs；
- encoder/seq2seq 是否存在单卡训练路径；
- 7B/8B PEFT 是否有实际配置，而不只是论文笼统提到 LoRA；
- 是否依赖 4×A100 80GB、70B、GPT API 或不可发布 generation cache；
- 是否有作者 checkpoint/prediction 可先做 CPU evaluator replay；
- 论文硬件声明、代码静态可行性和真实 27GB smoke 必须分列。

已知 Roccabruna et al. 的 RoBERTa 路径据论文使用单张 3090 Ti 24GB，而其 LLM 实验使用
4×A100 80GB；请回到正式 PDF 和作者代码核实，不能直接把整个方法统一判为 27GB PASS 或 FAIL。

## 八、Go/No-Go 门槛

报告末尾逐项给 PASS / CONDITIONAL / FAIL：

| 门槛 | PASS 标准 |
|---|---|
| 数据与许可 | annotation 与模型所需 source text 均可合法取得并绑定版本/hash |
| Split | exact document/pair IDs、seed/manifest 可重建并 checksum |
| Pair/labels | gold 前提、candidate universe、方向、`VAGUE`、closure 可重建 |
| Evaluator | 同一 scorer 可从 prediction 到公开主指标 |
| 对手 | 至少两个独立 2024–2026 方法在该 exact 轴有公开执行闭环 |
| 算力 | 两个 baseline 均有可信单张约 27GB 路径 |

判定规则：

- **GO**：六项全 PASS；
- **CONDITIONAL GO**：只剩一次本地 CPU 或最小 GPU smoke 可以解决的运行性证据；
- **NO-GO**：数据许可、split、pair/evaluator 任一不可锁，或不足两个独立同轴可执行 baseline。

“我们可以自己统一重写所有 baseline”不算公开执行闭环，也不能把 NO-GO 改成 GO。

## 九、输出结构

1. Executive verdict
2. Identity corrections and scope exclusions
3. MATRES protocol map
4. TB-Dense protocol map
5. Most-qualified exact protocol
6. Frozen data/split/pair/evaluator specification
7. Per-paper audit records
8. Repository execution audit
9. Independent-team and compatibility matrix（窄表）
10. Two-baseline recommendation（或明确无法选择）
11. 27GB feasibility
12. Go/No-Go gates
13. 未能核实与下一步最小本地检查
14. Plain-text Source Registry

## 十、引用与禁止事项

- 关键判断只用正式论文 PDF、作者官方仓库、数据官方仓库、官方 release/evaluator 等一手来源。
- 每条论文事实注明 section/table/page；代码事实注明 commit 和文件路径。
- 每个关键来源在正文附近给出完整 URL，并在 Source Registry 再列一次 plain-text URL。
- Markdown 不得只留 `turnXsearchY`、`filecite` 等内部 token；若系统强制生成内部引用，仍必须另附 URL。
- 不设计章节、不提出新模型、不写本项目实现代码、不运行或建议立即启动大规模训练。
- 不按“谁分数低容易超过”推荐，不把不同 protocol 的 headline 数字排成 SOTA 时间线。
- 不把“论文使用某数据集”写成“当前代码可复现”，不把“未找到”写成“绝对不存在”。
- 附件与一手来源冲突时，以一手来源为准，并在 identity corrections 中明确更正。
