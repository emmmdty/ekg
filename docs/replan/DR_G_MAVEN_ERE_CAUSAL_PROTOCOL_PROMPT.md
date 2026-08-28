# DR-G：MAVEN-ERE causal 固定公开协议资格审查

## 给执行者的说明

请在一个新的 ChatGPT「深度研究」对话中执行本提示词。建议上传以下四个附件：

1. `B_datasets_audit.md`
2. `C_methods_code_audit.md`
3. `F_eci_protocol_audit.md`
4. `SYNTHESIS_DECISION.md`

它们只提供已知边界，不能代替外部一手核验。**不需要上传 B/C/F 的 PDF**；审计 Markdown 已包含本地
纠错与来源入口。

请将最终结果同时导出为：

- `G_maven_causal_protocol.md`
- `G_maven_causal_protocol.pdf`

Markdown 中每个来源必须保留可复制的完整原始 URL；PDF 只用于 Markdown 链接丢失时恢复来源。
完成后把两份文件放入项目的 `docs/replan/` 目录。

---

## 可直接复制给深度研究模型的提示词

你是一名严谨的 NLP benchmark 与代码复现审计员。当前日期为 **2026-08-26**。你的任务不是设计
新模型或论文章节，而是判断：

> **MAVEN-ERE 的 causal relation extraction/identification，能否冻结出一个完全公开、可在本地重跑、
> 拥有至少两个独立近期正式方法的硕士论文主指标协议？**

上一候选 EventStoryLine/Causal-TimeBank ECI 已因“同一协议下没有两个公开可执行独立 baseline”判
当前 NO-GO。本轮不能降低标准，也不能通过混合不同 MAVEN-ERE setting 凑对手。

### 一、先做身份校验，禁止缩写串线

对每篇论文，第一步必须从 ACL Anthology 正式页/PDF提取并列出：精确题名、全体作者、venue、年份、
ACL ID、DOI。然后再判断 GitHub 是否属于该作者团队。

至少核验：

1. MAVEN-ERE 数据论文：`2022.emnlp-main.60`
2. Chen et al. 2024：`2024.acl-long.512`
3. Wei et al. 2024：`2024.findings-emnlp.1`
4. TacoERE：`2024.lrec-main.1348`
5. KnowQA：`2024.findings-emnlp.986`
6. LLMERE：`2025.coling-main.500`
7. MMD-ERE：`2025.coling-main.460`
8. Xiang et al. directional ECI：`2025.findings-acl.43`

若某项名称与正式论文不一致，以 ACL PDF 为准并明确更正。不得只凭方法缩写匹配仓库，不得从搜索摘要
抄作者、硬件或训练参数。

### 二、必须严格分开的协议轴

至少分别建立以下三条轴，禁止混表：

#### A. 官方 hidden-test 轴

- 官方 train/dev/test 文件的可见范围；
- hidden test gold 是否公开；
- 官方 `evaluate.py`、prediction schema、CodaLab competition；
- 截至审计日，CodaLab 是否真的还能登录、提交并返回 scorer 结果；只看到页面或 “Ends: Never” 不算；
- 哪些论文数字来自此轴，哪些只是引用旧表。

如果 test gold 不公开且新提交未被真实验证，这条轴不能作为本地完全可审计主协议。

#### B. Chen / LLMERE original-valid-as-test 轴

- 是否确为 original train 按 8:2 重分、original valid 作为 test；
- exact split seed、document IDs、转换脚本与输出文件是否公开；
- Chen 与 LLMERE 是否真的使用相同的 8:2 manifest、schema 和 evaluator；
- 论文表中的旧 baseline 是在该 split 重跑，还是直接复制其他 setting 的数字；
- causal relation 的标签、方向、候选对、gold trigger/event mention 前提和 P/R/F1 定义。

#### C. Xiang causal-only 轴

- 是否为 original dev → test、original train 抽 10% → dev；
- exact seed/document IDs/生成脚本；
- 是否只做 causal，是否包含其他关系作为辅助训练；
- 方向性、负例、候选 pair universe 和 evaluator；
- 是否还有第二个独立近期正式方法在完全相同协议上有可执行代码。

若发现第四种 setting（如固定随机 sample 或 LLM 成本抽样），单独列轴，不能塞进 A/B/C。

### 三、数据与 evaluator 冻结

从 MAVEN-ERE 官方仓库开始，给出：

- 官方 URL、default branch、审计日 HEAD commit、license、release/tag；
- causal 所需的精确输入文件名、SHA-256（若环境可下载并计算）、文档数、event mention 数、causal
  relation 数；
- train/dev/test 中 causal pair 的逐 split 计数；
- event mentions/triggers 是否给定，模型是在 gold mentions 上分类还是还包含检测；
- causal labels 与方向编码，反向 pair 如何处理；
- candidate pair universe：同句/跨句/全篇、窗口、是否只枚举 gold relation candidates；
- prediction JSON schema；
- 官方 evaluator 的 commit/path、调用方式、micro/macro、positive class、跨文档/跨 fold 聚合方式；
- 官方 evaluator 能否只评 causal；如果需要适配，哪些是纯选择参数，哪些会改变指标。

必须区分“官方数据可下载”“hidden test gold 可见”“CodaLab 可提交”“本地 evaluator 可运行”四件事。

### 四、逐论文协议矩阵

每篇论文一行，至少包含：

| 字段 | 必须回答 |
|---|---|
| 正式身份 | 标题、作者、venue、ACL ID、DOI |
| 独立团队 | 与数据原团队及其他候选的作者交集 |
| 任务范围 | full ERE、causal-only、directional ECI 或其他 |
| 数据文件 | 精确 MAVEN-ERE 文件/版本 |
| split | 属 A/B/C/其他哪条轴；exact IDs/seed 是否可得 |
| gold 前提 | gold mentions/triggers/pairs 的使用方式 |
| pair/labels | 候选对、方向、负类与其他关系处理 |
| metric/evaluator | 代码、路径、commit、P/R/F1 口径 |
| baseline 来源 | 本代码重跑、作者重实现、还是 reported-only |
| repo | 官方 URL、HEAD、license、archived、release |
| 数据闭环 | raw → preprocess → train → predict → evaluate |
| 缺失项 | 文件、命令、依赖、checkpoint、API、私有缓存 |
| 硬件 | GPU 型号/数量/显存、batch、length、epoch |

论文未声明就写“未声明”；仓库未取得就写“未取得”。不要按常见做法补猜。

### 五、仓库必须检查实际文件，不得停在元数据

对每个候选官方仓库：

1. 检查完整 tree 和 Git 历史，确认关键文件不是曾经存在后被删除；
2. 阅读 README、requirements/environment、data conversion、split、train、predict、evaluator；
3. 检查 import 指向的本地模块是否真实存在；
4. 检查 README 命令引用的文件名是否真实存在；
5. 检查作者机器绝对路径、未发布数据、闭源 API、checkpoint、缓存；
6. 若环境不能 clone/执行，只能标“静态未验证”，不能写“可运行”；
7. “有 GitHub”不等于“完整复现包”。

### 六、寻找至少两个独立近期 baseline

目标是在**同一条 A/B/C 协议轴**上找到至少两个：

- 作者团队独立；
- 2024–2026 正式发表；
- 官方代码当前可取得；
- 能从同一公开输入跑到同一 evaluator；
- 不依赖不可取得的 hidden gold、私有 split、私有 GPT 缓存或 70B/多闭源 API；
- 有可信单张约 27GB GPU 路径。

原始 MAVEN-ERE RoBERTa baseline 可以作为工程 sanity baseline，但它是 2022 数据论文方法，不能单独替代
“两个独立近期正式对手”的门槛。KnowQA、MMD-ERE、TacoERE 与原数据团队存在作者重叠时，要明确记录，
不得重复计算独立团队。

最多推荐两个方法。对每个方法给出：

- 选择理由和独立性；
- 所属唯一协议轴；
- 精确数据、代码 commit 与依赖；
- raw data 到最终 causal F1 的最短命令链；
- 需要修补的内容，以及修补是否会变成“我们重写 baseline”；
- 27GB 风险；
- 预期用 CPU smoke 还是最小 GPU smoke 解决最后不确定性。

若找不到两个，直接判当前 NO-GO，不要用不同 split 的论文分数凑数。

### 七、与本项目现有本地结果的边界

本项目已有一条 MAVEN-ERE causal 本地记录：在全量 public valid 上用官方 evaluator，当前 causal F1
约 28.50；同代码官方原版在同一 valid 上约 31.37。**这两个数字只用于说明本地资产存在，不能与 hidden
test、Chen/LLMERE valid-as-test 或 Xiang causal-only 表格直接相减。**

深度研究报告不要复制更多本地实验数字，也不要提出修改本地方法。只判断哪条公开轴值得进入下一阶段。

### 八、27GB 与执行门槛

对候选逐项核：

- 论文实际 GPU 型号、数量和显存；
- repo 默认模型、precision、sequence length、batch、gradient accumulation；
- 是否可用 encoder/seq2seq 或 7B/8B PEFT；
- 是否依赖 A100 40/80GB、70B、多 GPU 或多闭源 API；
- 是否有预生成缓存可避免本地大模型推理；
- 论文硬件声明、代码静态估计和本地实测必须分开。

“7B 4-bit 通常装得下”不能算完整训练路径；“A100 40GB 跑过”也不能直接算 27GB PASS。

### 九、Go/No-Go 门槛

报告末尾逐项给 PASS / CONDITIONAL / FAIL：

| 门槛 | PASS 标准 |
|---|---|
| 公开协议 | 一条明确的 A/B/C 轴，所有 gold 与输入本地可得 |
| Split | exact document IDs/seed/manifest 可重建并 checksum |
| Pair/labels | causal candidate universe、方向、负类可重建并计数 |
| Evaluator | 同一可执行 scorer 从 prediction 到 causal P/R/F1 |
| 对手 | 至少两个独立 2024–2026 正式方法在该轴有公开执行闭环 |
| 算力 | 两个 baseline 均有可信 27GB 单卡路径 |

判定规则：

- **GO**：六项全 PASS；
- **CONDITIONAL GO**：只剩一次本地 CPU 或最小 GPU smoke 可解决的运行性证据；
- **NO-GO**：公开协议、split、pair/evaluator 任一不可锁，或不足两个独立同轴可执行 baseline。

### 十、输出结构

1. Executive verdict
2. Paper identity corrections
3. A/B/C protocol map
4. Frozen data/evaluator specification
5. Per-paper protocol matrix
6. Repository execution audit
7. Independent-team and compatibility matrix
8. Two-baseline recommendation（或明确无法选择）
9. 27GB feasibility
10. Go/No-Go gates
11. 未能核实与下一步最小本地检查
12. 一手来源清单

### 十一、引用与禁止事项

- 只用论文正式 PDF、作者官方仓库、数据官方仓库、官方 evaluator/CodaLab 等一手来源支撑关键判断。
- 每条关键事实紧邻完整原始 URL；论文注明 section/table/page，代码注明文件路径与 commit。
- Markdown 不得只留 `turnXsearchY`、`filecite` 等内部 token；即使系统生成内部引用，也要另附原始 URL。
- 不设计章节、不提新模型、不写实现代码、不按“谁分数低容易超过”推荐。
- 不把 reported-only 数字写成已重跑，不把不同协议数字并表相减，不把“未找到”写成“绝对不存在”。
- 附件与一手来源冲突时，以一手来源为准，并在 identity corrections 中明确列错在哪里。
