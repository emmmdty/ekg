# DR-D 本地交叉核验

> 核验日期：2026-08-25（Asia/Taipei）
>
> 原始报告：`docs/replan/D_angles.md`
>
> 来源导出：`docs/replan/D_angles.pdf`

## 结论

DR-D 可作为后续综合输入，本轮验收状态为：**有条件通过**。

报告的两项否决均有一手证据支持：完整“跨语言事件图谱”缺少自然多语独立报道间的现实事件节点
identity gold；供应链/大宗商品风险虽然问题价值高，但现有资源没有闭合为“固定 raw text + risk target +
evaluator + 多个独立正式方法”的公开 benchmark。二者都可以保留为应用或窄任务，不应直接升级为论文
主轴。

报告提出的 EventStoryLine/Causal-TimeBank 事件因果识别是目前更闭合的候选：至少三个独立
2024–2025 正式团队继续使用 ESL/CTB，公开数据与单卡工程路径也比 α/β 完整。不过“ESL 5-fold、
CTB 10-fold”还不足以证明所有方法严格同轴；语料版本、fold IDs、pair generation、CTB license 与
evaluator 仍需在最终实验契约中锁定。因此它是**当前最强候选**，不是已经完成的方向决策。

固定协议 MAVEN-ERE 可保留为第二候选，但继续受 B 已确认的至少四类 evaluation setting 分裂约束。
本文件不提前给章节骨架；最终重构/重开判断仍需等待 E 和五路综合。

## PDF 来源恢复

- Markdown 共 208 行、51,646 bytes，保留 173 个 ChatGPT 内部 citation token，且没有原始 HTTPS
  URL。
- PDF 共 19 页，由 WeasyPrint 生成，有可搜索文本层；含 246 个 URI 注释、38 个唯一 URI，剔除
  ChatGPT 首页后可恢复 37 个真实来源。
- 表格与完整正文以 Markdown 为准，引用 URL 由 PDF 注释恢复；不需要重跑或重新导出 DR-D。

## α：跨语言/多语言事件图谱

| DR-D 结论 | 核验结果 | 必须保留的边界 |
|---|---|---|
| MEE 是多语言 trigger/argument EE，不是跨语言 event identity | **确认** | MEE 正式论文提供 8 语 entity/event trigger/argument annotation；没有自然多语报道的 language-mixed node cluster。 |
| MINION 更窄，只做 multilingual event detection | **确认** | 可支撑 trigger transfer，不能支撑 argument、relation、coreference 或图融合。 |
| EusIE/SPEED++ 证明 multilingual transfer 仍活跃 | **确认** | 它们证明问题价值与工程可行性，不构成同一开放 benchmark 上的多个严格对手。 |
| MCECR 不能冒充跨语言现实事件节点对齐 | **决定性确认** | 官方 PDF 明写 Google 相关文章只保留与 seed article 相同语言的结果；cross-lingual experiment 是 train/test 跨语迁移，不是 language-mixed gold cluster。 |
| MEANTIME 有 cross-lingual coreference，但主要是平行翻译 | **确认** | 480 docs 是 120 篇英文 Wikinews 及西/意/荷翻译，非英语 annotation 主要由英文投射并人工对齐；不是独立媒体报道。 |
| ACE05 不能补开放多语 event benchmark | **沿用 B 确认** | LDC 许可不满足开放获取，且 event task 只覆盖 English/Chinese，不含 Arabic event evaluation。 |
| 完整 α 不满足当前硬约束 | **确认** | 可以写“本轮严格检索未找到成熟赛道”，不能写成领域永久不存在；窄版 multilingual EE/transfer 仍有研究价值。 |

MCECR 还需增加一条数据 provenance：论文约 65% event pairs 由预训练模型以高置信度自动标注，对
自动标注只抽样 10% 人工核验。论文报告该抽检准确率至少 97%，但最终报告仍应把“人工 + 自动”写清，
不能笼统称全部 pair 人工 gold。

## β：供应链、大宗商品与经济风险

| DR-D 结论 | 核验结果 | 必须保留的边界 |
|---|---|---|
| CrudeOilNews 语义上高度贴合 commodity risk | **确认** | LREC 2022：175 篇人工 seed、25 篇 adjudicated reference test，扩展后 425 篇、约 11K events；ontology 包含供给、短缺、制裁、贸易紧张等。 |
| CrudeOilNews 原始正文不完整公开 | **决定性确认** | 作者 README 明写因版权只提供 original news URL 与 annotation，不提供原新闻正文；只有 augmented data 完整提供文本。 |
| 当前仓库不是成熟 shared-task 包 | **确认** | 顶层可见 annotation、guideline、license、README 和示意图，未见固定 evaluator/leaderboard；论文 reference test 存在不等于今天可完整重建 raw input。 |
| ACLED/GDELT/EM-DAT 等不能自动称 NLP risk benchmark | **分类确认** | 它们可作结构化事件流、外部 outcome 或弱监督；没有固定 human-gold extraction/risk target 与共同 scorer 时不能改名包装。 |
| SPEED++ 是 event→warning 的正式先例 | **确认** | EMNLP 2024 证明 multilingual epidemic EE 可支持 early warning；它是疫情应用验证，不证明 commodity/supply-risk 已形成多人 benchmark。 |
| β 作为主 benchmark 不通过 | **确认** | 结论来自公开 test/evaluator 链不闭合，不是因为对手少或现实价值低。风险监测仍适合作为应用延伸。 |

OEE-CFC、FINEED、EFSA、FORCE 等条目可保留为候选资源地图，但 D 没有对它们全部完成当前 scorer、
license、固定 test 和独立 follow-up 审计。它们不能单独改变 β 的总体判定。关于“没有 qualifying
precedent”的表述一律是本轮检索下界，不是对全部论文的存在性证明。

## 替代切口核验

### EventStoryLine / Causal-TimeBank 事件因果识别

近期竞争密度的保守下界成立：

1. ICCL：EMNLP 2024 `2024.emnlp-main.51`，作者 Liang Chao、Wei Xiang、Bang Wang；
2. LKCER：COLING 2025 `2025.coling-main.495`，Ya Su 等；
3. DICP：**Findings EMNLP 2025** `2025.findings-emnlp.139`，Lin Mu 等。

三组作者互不重叠，三篇都在 ESL/CTB 上正式实验，并明确使用 ESL 5-fold、CTB 10-fold、P/R/F1。
DICP 还明写 follow ICCL 的 protocol，使用 BERT-base、单张 RTX 3090；因此“至少三个独立近期正式
团队 + 27GB 高可行”可以进入综合。

但必须覆盖原报告的以下精度边界：

- DICP 是 Findings EMNLP，不应只模糊写成 EMNLP main；其正式 ID 不是 `2025.emnlp-main.616`。
- `2025.emnlp-main.616` 是 DECLV。DECLV 与 COLING 2025 方法共享 Ya Su 等作者，不能再计一个
  独立团队；D 的独立团队数没有因此下降，因为 DICP 是另一组作者。
- EventStoryLine 官方仓库同时有 v1.0 expert、v1.2 crowd、v1.5 expert+crowd；PPAT README 又写
  v0.9。最终必须固定 corpus version，不能只写“ESL”。
- ICCL 固定 last two topics 为 dev、其余 20 topics 5-fold；DICP 采用相同大框架并对 CTB 设置正/负
  sampling rates 5/0.3。尚未取得三篇完全相同的生成后 fold/pair checksum。
- EventStoryLine 仓库含 annotated data、evaluation-format test、baseline/eval scripts，许可证为
  CC BY 3.0；Causal-TimeBank 的 CAT/TimeML ZIP 可直接下载，但仓库未见显式 LICENSE。后者只能写
  “公开可下载研究资源”，不能称许可已完全审计通过。
- ICCL 仓库有源代码但 README 缺环境、数据、fold 和运行命令；仓库存在不等于端到端复现完成。

因此本轮等级是：**活跃、公开性较强、单卡可行的条件性主候选**。在锁定 version/folds/pairs/evaluator
并至少复现两个对手前，不写“严格 SOTA 轴已经确认”。

### 固定协议 MAVEN-ERE

D 对 MAVEN-ERE 的判断与 B/C 审计一致：数据和 evaluator 资产有残值、近期正式使用多，但 official
hidden test、Chen/LLMERE valid-as-test、sampled LLM、Xiang causal-only 至少四种 setting 不能混表。
它可以进入综合候选，但“冻结一个已有 protocol”必须同时回答：该 protocol 下有哪些独立正式对手、
baseline 是否同 split 重跑、test 是否公开、evaluator 是否完全一致。CodaLab 页面存在仍不等于新提交
能力已实测。

## 27GB 单卡边界

- DICP 论文明确单张 RTX 3090、BERT-base，PPAT 也是 BERT-base 级工程，支持 ESL/CTB 路线的
  单卡高可行性判断。
- LKCER 使用 RoBERTa-base 并调用 ChatGLM-6B 生成知识；这仍需固定生成缓存/API/模型版本，不能只凭
  “6B”推断整套 recipe 已在目标卡复现。
- MAVEN-ERE 的 encoder/seq2seq baseline 风险较低；LLMERE 的 A100 40GB recipe 仍不是 27GB 证明。
- 本轮未运行 GPU、未训练模型，也未把估算写成实测。

## 可交给 DR-E 的稳定输入

- 跨语言和风险监测都有真实价值，但当前不具备完整公开 benchmark 闭环；E 不应把工业需求反推成
  学术主轴已经成立。
- 事件因果识别是当前公开性、近期竞争与单卡可行性最均衡的候选，仍需锁定 ESL/CTB 协议。
- MAVEN-ERE 是可利用本地残值的第二候选，但 protocol fragmentation 是一级风险。
- 风险监测可作为 event causality / event relation 的应用验证，不必把“大宗商品”设成主数据域。
- 任何通用 GraphRAG、agent memory 或结构化事件流案例都不能自动证明 event graph benchmark 成熟。

## 一手来源入口

- [MEE](https://aclanthology.org/2022.emnlp-main.652/)
- [MINION](https://aclanthology.org/2022.naacl-main.166/)
- [EusIE](https://aclanthology.org/2024.lrec-main.586/)
- [MCECR](https://aclanthology.org/2024.findings-naacl.245/)
- [MEANTIME](https://aclanthology.org/L16-1699/)
- [SPEED++](https://aclanthology.org/2024.emnlp-main.720/)
- [CrudeOilNews 论文](https://aclanthology.org/2022.lrec-1.49/)
- [CrudeOilNews 作者仓库](https://github.com/meisin/CrudeOilNews-Corpus)
- [ICCL](https://aclanthology.org/2024.emnlp-main.51/)
- [LKCER](https://aclanthology.org/2025.coling-main.495/)
- [DICP](https://aclanthology.org/2025.findings-emnlp.139/)
- [DECLV](https://aclanthology.org/2025.emnlp-main.616/)
- [EventStoryLine 官方仓库](https://github.com/tommasoc80/EventStoryLine)
- [Causal-TimeBank 作者仓库](https://github.com/paramitamirza/Causal-TimeBank)
- [DICP 官方仓库](https://github.com/sj1071-cell/DICP)
- [MAVEN-ERE causal README](https://github.com/THU-KEG/MAVEN-ERE/blob/main/causal/README.md)

## 验收边界

本轮没有穷尽 2024–2026 每个多语言或风险数据集的 citation graph，没有真实运行 ECI 仓库，也没有为
ESL/CTB 三篇近期方法生成统一 checksum。MEE/MINION 当前 distribution、FORCE 当前 release、ICEWS
许可与各风险数据库的所有应用论文仍保持未核。上述缺口不妨碍把 D 作为“切口排除 + 条件性替代候选”
的合格输入，但会阻止“跨语言/commodity benchmark 绝对不存在”“ESL/CTB 已经完全同轴”或“最终方向
已经确定”的强结论。
