# DR-F：ESL / Causal-TimeBank 事件因果识别资格审查

## 给执行者的说明

请在一个新的 ChatGPT「深度研究」对话中执行本提示词。建议同时上传以下两个附件：

1. `D_angles_audit.md`
2. `SYNTHESIS_DECISION.md`

它们只提供已有边界；所有关键结论仍必须回到外部一手来源重新核实。

请将最终结果同时导出为：

- `F_eci_protocol.md`
- `F_eci_protocol.pdf`

Markdown 中每个来源都要保留可复制的完整原始 URL；PDF 用于在 Markdown 引用链接丢失时恢复来源。
完成后把两份文件放入项目的 `docs/replan/` 目录。

---

## 可直接复制给深度研究模型的提示词

你是一名严谨的 NLP 研究审计员。当前日期为 **2026-08-25**。你的任务不是设计新方法或论文章节，
而是判断以下候选能否作为硕士论文的公开可比主任务：

> **EventStoryLine（ESL）与 Causal-TimeBank（CTB）上的 Event Causality Identification（ECI）**

### 一、决策问题

请给出可审计的 **go / conditional go / no-go** 结论，回答：

1. 是否能锁定一个完全明确、公开可取得的 ESL/CTB 数据版本？
2. 是否能锁定可复现的 folds、pair generation、negative sampling 和 evaluator？
3. 是否至少有两个**作者团队独立、正式发表、2024–2026、同协议可比较**的方法可在本地复现？
4. 这些方法是否能在单张约 27GB 可用显存的 NVIDIA GPU 上训练或合理复现？

只有四项都有一手证据，才能判 go。不要因为问题有价值或论文数量多而放宽复现门槛。

### 二、必须核验的论文

至少逐篇核验以下论文；若论文题名、作者、代码链接或协议与这里不符，请直接更正：

1. **ICCL** — ACL Anthology ID `2024.emnlp-main.51`
2. **LKCER** — ACL Anthology ID `2025.coling-main.495`
3. **DICP** — ACL Anthology ID `2025.findings-emnlp.139`
4. **DECLV** — ACL Anthology ID `2025.emnlp-main.616`

其中 DECLV 与 LKCER 可能有作者重叠，不能自动算作第四个独立团队；请核作者集合。

优先使用 ACL Anthology 正式页/PDF、作者官方 GitHub、数据作者仓库、论文 supplementary material。
不要用博客、搜索摘要、Papers With Code 或二手排行榜替代原文。

### 三、数据版本审计

#### 3.1 EventStoryLine

请核实并制表：

- 官方/作者仓库中实际存在的 v0.9、v1.0、v1.2、v1.5，哪些是真实 release，分别包含什么；
- 每篇方法论文究竟使用哪一版，不接受只写“ESL”；
- expert、crowd、expert+crowd 标注是否混用；
- 每版的 topics/documents/event mentions/causal links，以官方文件实数或论文表格为准；
- 数据许可证及其适用范围；
- 原始文本是否随数据发布、是否需要额外下载或许可；
- 给出可下载入口、文件名、release/tag/commit；若能取得官方 checksum 则报告，不能就写未取得。

#### 3.2 Causal-TimeBank

请核实并制表：

- 官方/作者发布入口与精确版本；
- CAT/TimeML 等文件格式与实际可下载文件；
- documents/events/causal links/pairs 的统计口径；
- 是否有明确 LICENSE；“公开可下载”与“明确开放许可”必须分开写；
- 原始语料是否受 TimeBank/LDC 或其他上游许可约束；
- 是否存在官方固定 train/dev/test，还是后续论文自行做 10-fold；
- 给出完整原始 URL、仓库 commit/tag 和文件路径。

### 四、逐论文协议矩阵

对 ICCL、LKCER、DICP、DECLV 每篇建立一行，至少包含：

| 字段 | 必须回答的内容 |
|---|---|
| 正式身份 | 标题、作者、venue、ACL ID、DOI |
| 数据版本 | ESL/CTB 精确版本与实际文件 |
| gold 前提 | event mentions 是否给定；是否只分类给定 event pairs |
| pair universe | 如何生成候选对；是否限同句/跨句/窗口；是否包含方向反转 |
| labels | 正类、负类、方向性如何编码；是否把反向因果算负例 |
| negative sampling | ratio、策略、随机种子、train/eval 是否不同 |
| folds | ESL 5-fold、CTB 10-fold 的精确 topic/doc IDs；dev 如何选择 |
| aggregation | fold 内指标与跨 fold 汇总方式；mean、micro pooling 或其他 |
| evaluator | 官方/作者脚本 URL、文件路径、commit；若自实现须说明 |
| metric | P/R/F1 的 micro/macro、正类范围、是否含 negative class、阈值选择 |
| baseline 来源 | 同代码重跑、引用他文还是作者重新实现；三者分开 |
| 模型输入 | trigger、sentence、document、external knowledge、LLM 生成缓存等 |
| 训练资源 | GPU 型号/数量、显存、epoch、batch、max length；未声明就写未声明 |
| 代码闭环 | data preprocessing、train、evaluate、config、checkpoint 是否齐全 |

凡论文没有说明的字段，一律写 **未声明/未取得**，不要按常见做法补全。

### 五、严格比较审计

1. 找出哪些论文真的可以在同一 ESL 或 CTB 协议下比较。
2. 对任何性能数字，同时给出：论文 + 具体 Table/Appendix + corpus version + split/fold + evaluator +
   metric definition。
3. 不得把不同 ESL version、不同 fold IDs、不同 pair generator 或不同 negative sampling 的数字相减。
4. 区分：
   - 同一论文同代码重跑的 baseline；
   - 从旧论文复制的 reported-only 数字；
   - 当前可执行的官方代码；
   - 只有仓库但缺数据/命令/依赖的代码。
5. 若三篇都写“5-fold/10-fold”，仍要验证生成后的 fold/pair 是否真正相同；仅 fold 数相同不算同轴。

### 六、代码与复现资格

对所有官方仓库记录：

- 完整 URL、owner/repo、default branch、审计日 HEAD commit；
- license、archived 状态、最后 push、release；
- README 是否给环境、数据目录、预处理、训练、评测完整命令；
- requirements/lockfile 是否存在；
- 数据文件是否真的在仓库中，还是代码引用缺失路径；
- evaluator 是否可执行，是否能从 raw data 生成论文用 fold/pairs；
- checkpoint、log 或论文结果复现产物是否存在；
- issues 中是否有复现成功/失败报告。

“有 GitHub”不等于“能跑”。如果深度研究环境不能执行代码，请明确写“静态审计”，不要声称已运行。

### 七、选择两个 baseline

基于证据选择**最多两个**最值得本地复现的独立近期方法，并分别给出：

- 为什么它与冻结协议最接近；
- 需要下载的精确数据和代码；
- 从 raw data 到最终 F1 的最短命令链；
- 预期硬件与 27GB 风险；
- 缺失资产；
- 若无法选出两个，直接判该方向当前不满足学位论文门槛。

不要选择两个作者高度重叠的方法来伪造独立竞争密度。不要为了凑两个而使用 arXiv-only 工作。

### 八、Go/No-Go 门槛表

末尾必须逐项给出 PASS / CONDITIONAL / FAIL：

| 门槛 | 通过标准 |
|---|---|
| 数据 | 精确版本、文件、获取方式和许可边界可锁定 |
| Split | exact fold/topic/doc IDs 可重建 |
| Pair | candidate/negative generation 可重建并能计数校验 |
| Evaluator | 代码可取得，指标定义完整，可从预测文件跑到 P/R/F1 |
| 对手 | 至少两个独立 2024–2026 正式方法能在同一协议复现 |
| 算力 | 至少两个 baseline 有可信的 27GB 单卡路径 |

总判定规则：

- **GO**：六项全部 PASS；
- **CONDITIONAL GO**：只缺可在本地一次 CPU/小 GPU smoke 解决的运行性证据；
- **NO-GO**：数据/split/pair/evaluator 任一无法锁定，或不足两个独立同轴 baseline。

### 九、输出结构

按以下顺序写报告：

1. Executive verdict
2. Dataset/version map
3. Per-paper protocol matrix
4. Compatibility/conflict matrix
5. Repository reproducibility audit
6. Two-baseline recommendation（或无法选择的明确说明）
7. 27GB feasibility
8. Go/No-Go gates
9. 未能核实
10. 与已有判断冲突或出乎预期的事实
11. 一手来源清单

### 十、引用与禁止事项

- 每条关键事实必须紧邻一手来源，保留完整原始 URL；论文要给 section/table/page，代码要给文件路径。
- Markdown 不得只留下 `turnXsearchY`、`filecite` 等会话内部标记；若系统仍生成内部引用，句末另附原始 URL。
- 不设计论文章节，不提出新模型，不写职业前景，不讨论工业案例。
- 不按“谁分数低、容易超过”推荐；问题价值和可复现资格分开。
- 不把不同协议的数字并表相减，不把“未找到”写成“绝对不存在”。
- 不因为附件已有结论就跳过一手核验；附件若与一手来源冲突，以一手来源为准并单列更正。
