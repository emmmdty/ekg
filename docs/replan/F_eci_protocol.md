# EventStoryLine / Causal-TimeBank 上 Event Causality Identification 的硕士论文主任务可复现性审计

## Executive verdict

**审计日期：2026-08-25。最终结论：NO-GO。**

这里的 NO-GO 不是说 Event Causality Identification（ECI）没有研究价值，而是说：**按你给出的“公开可比主任务”标准，目前不能把 ESL/CTB + ICCL/LKCER/DICP/DECLV 这条实验线冻结成一个已经被一手证据完全锁定、可由第三方独立重建的 benchmark protocol。**

本次核验中，最关键的事实是：

| 决策问题 | 结论 | 核心原因 |
|---|---|---|
| 能否锁定完全明确、公开可取得的 ESL/CTB 数据版本？ | **FAIL** | ESL 官方仓库存在多个版本；被审计方法论文通常只写 “EventStoryLine”，没有把论文实验绑定到一个可核验的 release/tag/commit/file set。CTB 有作者仓库，但公开下载、README 许可声明和上游 TimeBank 文本权利不能混为一谈。 |
| 能否锁定 folds、pair generation、negative sampling、evaluator？ | **FAIL** | ICCL、LKCER、DICP 都明确写沿用 Shen et al. (2022) 的 data processing tools，并写 ESL 5-fold、CTB 10-fold；但**仅有 fold 数量和共同引用不足以证明 exact fold IDs、candidate pairs、负样本及 evaluator 完全相同**。已核验论文正文没有给出这些完整对象。 citeturn6view0turn6view1turn6view2 |
| 是否至少有两个独立团队、2024–2026 正式发表、同协议、当前可本地复现的方法？ | **FAIL** | ICCL 与 DICP 确实是两个独立正式团队，且都有可识别的 GitHub 仓库；但是“同协议”与 raw-data→pairs→fold→prediction→F1 的闭环尚未被证明。LKCER/DECLV 又不能增加两个独立团队：DECLV 四位作者全部出现在 LKCER 作者集合中。 citeturn0search3turn0search2turn0search0turn0search1 |
| 是否有至少两个 baseline 的可信单张约 27GB GPU 路径？ | **FAIL** | DICP 论文明确报告 Tesla V100，但没有在已核验信息中锁定其 V100 显存容量和完整单卡内存峰值；ICCL 的可验证硬件配置没有取得。LKCER/DECLV 又缺少已核实的公开执行闭环。因此不能把“模型看起来应该塞得下”当成 PASS。 citeturn2find9turn6view2 |

因此，这不是“只需本地 smoke test 就能消除的最后一点不确定性”。当前缺口位于你定义的硬门槛本身——**版本、split、pair universe/evaluator、以及两个独立同轴 baseline**——所以不能判 CONDITIONAL GO。

另一个重要结论是：**不能把论文里的 F1 排名直接当成可比较排行榜。** 三篇论文都写 “5-fold on ESL / 10-fold on CTB” 甚至引用同一 Shen et al. (2022) preprocessing，仍不能证明其落盘后的 folds、pairs、negative samples 和 evaluator 一致。按你的规则，在这些对象被 checksum/count/fold-ID 级别锁定前，不应进行跨论文分数相减。 citeturn6view0turn6view1turn6view2

本报告是**静态审计**：核查论文正式页/PDF、公开仓库元数据及公开代码入口；**没有声称实际运行过训练、预处理或 evaluator**。

## Dataset/version map

### EventStoryLine

EventStoryLine 的第一方入口是 Tommaso Caselli 的作者仓库：

`https://github.com/tommasoc80/EventStoryLine`

本次取得的仓库元数据显示 default branch 为 `master`、GitHub 未标记 archived、仓库级 license 被 GitHub 识别为 MIT。审计时 `master` HEAD 可锁到：

`2b6f420a619a013fbfadbc6f5a41b125e74bb595`

对应 GitHub API：

`https://api.github.com/repos/tommasoc80/EventStoryLine/commits?per_page=1`

该 HEAD 的提交信息明确写有：

> corpus updated to version 1.5，并加入 `incompatibilities_to_handle.md`

而递归 tree 中可以直接看到 `1.0/` 目录；仓库 README 的搜索结果又明确自称 “EventStoryLine corpus 0.9”。因此至少可以确认：**这个作者仓库不是一个单一不可变数据集，而是一个存在版本演进的数据源。** 官方入口：`https://github.com/tommasoc80/EventStoryLine`。 citeturn7search0

但严格按你的版本审计标准，本次取得的一手证据不足以把四个版本全部填写成“精确文件集合 + 统计数字 + checksum”：

| ESL 标识 | 本次能一手确认的内容 | topics / docs / event mentions / causal links | annotation composition | release/tag/commit | 审计结论 |
|---|---|---|---|---|---|
| **v0.9** | 作者仓库 README 明确把自身称为 “EventStoryLine corpus 0.9” | **未取得足够的版本专属原始文件计数证据** | expert/crowd 的版本专属组成 **未锁定** | README 存在；未取得独立 GitHub release/tag | 真实版本标识可确认，但不能作为本次论文实验的已锁定版本 |
| **v1.0** | 作者 repo tree 中存在 `1.0/` | **未取得足够证据** | **未取得** | `1.0/` tree 已确认；具体 release/tag 未取得 | 真实版本目录可确认 |
| **v1.2** | 本次已保留的一手抓取结果不足以完整证明其文件树、统计及 release 语义 | **未取得** | **未取得** | **未取得** | **不能在本报告中冒充已锁定** |
| **v1.5** | 作者仓库 HEAD commit message 明确称 corpus updated to version 1.5 | **未取得足够版本专属计数证据** | **未取得** | `master` HEAD `2b6f420a619a013fbfadbc6f5a41b125e74bb595` | 版本存在性有强证据，但论文实验并未因此自动等于 v1.5 |

这一点对 ICCL/LKCER/DICP/DECLV 非常重要：**不能用论文发表年份去推断它使用当时仓库 HEAD，也不能通过论文数据表的近似统计反推出 release。** 用户要求的是“论文究竟用了哪一版”；在论文只写 “EventStoryLine” 而没有给 release/tag/file hash 的情况下，严格答案只能是 **未声明**。

#### Expert、crowd 与 expert+crowd

EventStoryLine 的版本历史涉及 expert/crowd annotations；但是对本审计真正决定性的问题不是“ESL 历史上有没有这些标注”，而是**每一篇方法实际把哪一组标注送入 Shen-style preprocessing**。已核验的 ICCL、LKCER、DICP 实验描述没有把这一点绑定到某个版本文件集合。因此，本报告不会把不同 release 的 expert/crowd 数量倒推到这些方法上。

尤其 ICCL 与 DICP 还明确提到 ESL 训练时使用 additional/known causal event pairs，这进一步意味着“官方 corpus 中有哪些 links”与“最终训练 fold 中有多少 positive pairs”是两个不同计数口径。ICCL 明确写在 ESL 上把 known causal event pairs 加入训练集；DICP 也写随机选择 known causal event pairs 并拼接到已有训练数据。 citeturn2find0turn2find9

这正是为什么**仅比较官方 ESL causal-link 总数不能验证论文 pair 数。**

#### ESL 许可证与文本

GitHub API 将 `tommasoc80/EventStoryLine` 的仓库 license 识别为 MIT；仓库入口为：

`https://github.com/tommasoc80/EventStoryLine`

MIT 文件路径：

`https://github.com/tommasoc80/EventStoryLine/blob/master/LICENSE`

但一个严谨的数据许可结论必须把两件事分开：

**repository license** 可以确认；  
**其中涉及的新闻原文/第三方文本是否全部由该 MIT 声明重新许可**，本次没有取得足够的一手权利链文件，因此不能扩张解释。

同样，本次没有取得作者发布的版本级 checksums，所以 checksum 一栏应是：

**官方 checksum：未取得。**

### Causal-TimeBank

Causal-TimeBank 的作者仓库是：

`https://github.com/paramitamirza/Causal-TimeBank`

它明确说明语料是在 **TimeBank events 上增加 causal information**，并提供 **CAT 与 TimeML** 两种格式；README 同时给出 Creative Commons Attribution-NonCommercial-ShareAlike 3.0 的发布声明。作者仓库是核验这个事实的一手来源：

`https://github.com/paramitamirza/Causal-TimeBank`

本次取得的 `master` HEAD：

`9db986739937b894ded84c708c2d15bab3f8078d`

API：

`https://api.github.com/repos/paramitamirza/Causal-TimeBank/commits?per_page=1`

但有一个容易被忽略的重要区别：**GitHub API 的 repository `license` 字段为 null，而 README 自身写有 CC BY-NC-SA 3.0。** 因此准确表述应是：

> 作者 README 有明确 CC BY-NC-SA 3.0 发布声明；本次未发现由 GitHub license detector 识别出的独立 LICENSE 文件。

这不等于“没有许可”，但也不能把 README 声明、GitHub LICENSE 文件和上游 TimeBank 权利混为同一层。

| CTB 审计项 | 结果 |
|---|---|
| 第一方入口 | `https://github.com/paramitamirza/Causal-TimeBank` |
| exact repository revision | `master` HEAD `9db986739937b894ded84c708c2d15bab3f8078d` |
| 格式 | 作者 README 明确称有 CAT 和 TimeML |
| 与 TimeBank 的关系 | 明确是在 TimeBank events 上加入 causal information |
| standalone LICENSE | GitHub API 未识别；README 有 CC BY-NC-SA 3.0 声明 |
| “公开下载” | **是，作者仓库公开** |
| “无上游权利问题的开放语料” | **不能由上述事实推出** |
| 原始 TimeBank 文本的权利边界 | **本次未独立锁定，因此不能宣称 CC 声明覆盖所有上游文本权利** |
| 官方固定 train/dev/test | 本次未取得作者原始 release 中的固定 train/dev/test 证据 |
| 后续方法的 split | ICCL/LKCER/DICP 均写 follow Shen et al. (2022) 做 CTB 10-fold |
| 官方 checksum | **未取得** |
| version-specific documents/events/CLINK/pair counts | **未取得足以满足本审计标准的完整第一方计数表** |

ICCL、LKCER、DICP 对 CTB 的共同描述只是“10-fold cross-validation”并使用 Shen et al. (2022) processing tools。它不能被重新表述为“Causal-TimeBank 官方提供 10-fold split”。 citeturn2find0turn2find5turn2find9

### 数据层最关键的审计结论

即使 ESL 与 CTB 都能找到作者公开仓库，仍然存在三个不同层次：

**raw corpus release → preprocessing input → paper-specific fold/pair files。**

当前证据只足以证明 raw-corpus 入口存在，并不足以证明四篇论文使用的中间产物可以唯一重建。

所以，对你的第一个硬问题，答案不是“GitHub 能下载所以 PASS”，而是：

> **Data gate 不能 PASS。**

## Per-paper protocol matrix

### 正式身份与数据声明

| 方法 | 正式身份 | ESL / CTB 精确版本 | 一手证据 |
|---|---|---|---|
| **ICCL** | *Learning Instruction-Following and Contextual-Causal Collaboration for Event Causality Identification*. Chao Liang, Yangning Li, Shimin Tao, Xiangrong Zeng, Hailong Yuan, Zhengcong Fei, Hao Zhou, Fei Li, Donghong Ji. EMNLP 2024, ACL `2024.emnlp-main.51`, pp. 886–901. DOI `10.18653/v1/2024.emnlp-main.51` | **未声明 release/tag/file set**；正文写 ESL / CTB | 正式页 `https://aclanthology.org/2024.emnlp-main.51/`；PDF `https://aclanthology.org/2024.emnlp-main.51.pdf`。 citeturn0search3turn6view0 |
| **LKCER** | *Enhancing Event Causality Identification with LLM Knowledge and Concept-Level Event Relations*. Shan Su, Xia Yao, Yong Xie, Yu Zhang, Keqing He, Meina Song. COLING 2025, ACL `2025.coling-main.495`, pp. 9892–9902. DOI `10.18653/v1/2025.coling-main.495` | **未声明 release/tag/file set** | `https://aclanthology.org/2025.coling-main.495/`；`https://aclanthology.org/2025.coling-main.495.pdf`。 citeturn0search2turn6view1 |
| **DICP** | *Identify Event Causality with Knowledge and Preference via Dynamic Interval Contrastive Prompt*. Jing Su, Changlong Yu, Jun Ma, Wenge Rong, Zhang Xiong. Findings of EMNLP 2025, ACL `2025.findings-emnlp.139`, pp. 2641–2653. DOI `10.18653/v1/2025.findings-emnlp.139` | **未声明 release/tag/file set** | `https://aclanthology.org/2025.findings-emnlp.139/`；`https://aclanthology.org/2025.findings-emnlp.139.pdf`。 citeturn0search0turn6view2 |
| **DECLV** | *Dynamic Energy-Based Contrastive Learning with Multi-Stage Knowledge Verification for Event Causality Identification*. Shan Su, Yong Xie, Keqing He, Meina Song. EMNLP 2025, ACL `2025.emnlp-main.616`, pp. 12149–12161. DOI `10.18653/v1/2025.emnlp-main.616` | 在本次成功取得的一手页面证据中 **未能锁定精确 release/file set** | `https://aclanthology.org/2025.emnlp-main.616/`；PDF URL `https://aclanthology.org/2025.emnlp-main.616.pdf`，但本次 PDF renderer 未成功取得正文，因此正文协议项不以猜测补齐。 citeturn0search1 |

这里顺便更正一个“团队独立性”问题。LKCER 作者是：

Shan Su / Xia Yao / Yong Xie / Yu Zhang / Keqing He / Meina Song。

DECLV 作者是：

Shan Su / Yong Xie / Keqing He / Meina Song。

也就是说 **DECLV 的四位作者全部属于 LKCER 作者集合**。因此在你要求的“独立作者团队”意义下，LKCER + DECLV **绝对不能按两支独立近期竞争团队计算**。正式作者表见各自 ACL 页面。 citeturn0search2turn0search1

### Pair、negative、fold 与 evaluator

| 方法 | gold premise | pair universe / direction | labels | negative sampling | folds / dev | aggregation | evaluator / metric |
|---|---|---|---|---|---|---|---|
| **ICCL** | 已核验实验段落不足以锁定“给定 event mentions”到文件级定义；**不补猜** | exact candidate generator、句内/跨句窗口、direction reversal：**未声明/未取得** | exact class encoding：**未取得** | 正文明确 ESL 加入 known causal event pairs；ratio、seed、train/eval 是否采用同策略：**未取得** | **ESL 5-fold，CTB 10-fold，follow Shen et al. (2022)**；exact topic/doc IDs、dev selection：**未取得** | **未声明/未取得** | 报告 P/R/F1，但当前取得段落不能锁定 micro/macro、negative class treatment 及一个可执行 evaluator 文件 |
| **LKCER** | **未取得完整定义** | **未取得** | **未取得** | **未取得** | **ESL 5-fold，CTB 10-fold，follow Shen et al. (2022)**；exact IDs/dev：**未取得** | **未取得** | 一个具有 commit/path 的可执行 evaluator：**未取得** |
| **DICP** | **未取得完整定义** | **未取得** | **未取得** | ESL 明确随机选择 known causal event pairs 并拼接到已有 training data；ratio/seed/eval sampling：**未取得** | **ESL 5-fold，CTB 10-fold；same Shen et al. tools，并称 each CV 使用相同 test set**；但 exact IDs：**未取得** | **未取得** | 可执行 evaluator 的路径/commit 与完整 metric definition：**未取得** |
| **DECLV** | **未取得** | **未取得** | **未取得** | **未取得** | 本次未成功取得正文协议，不从其他三篇外推 | **未取得** | **未取得** |

ICCL 的论文实验部分明确说遵循 Shen et al. (2022)，ESL 做 5-fold、CTB 做 10-fold，并为 fair comparison 使用 Shen et al. 提供的相同 data processing tools；同时在 ESL 中把 known causal event pairs 加入训练数据。见论文 §4 experimental setup，PDF 约 p.5。`https://aclanthology.org/2024.emnlp-main.51.pdf`。 citeturn2find0turn6view0

LKCER 同样明确写 follow Shen et al. (2022) 做 ESL 5-fold 和 CTB 10-fold，并使用相同 processing tools。`https://aclanthology.org/2025.coling-main.495.pdf`。 citeturn2find5turn6view1

DICP 的措辞甚至更明确：它写了使用 Shen et al. (2022) 的 same data processing tools 和 each cross-validation 的 same test set；ESL 还随机选取 known causal event pairs 拼接训练数据。**但是 same test set 不等于我们已经拥有其 exact document IDs，也不等于负例顺序、随机样本和最终 pair files 有可验证 hash。** `https://aclanthology.org/2025.findings-emnlp.139.pdf`，实验设置及 Table 2 邻近页面。 citeturn2find9turn6view2

### 模型输入、资源与代码闭环

| 方法 | 模型/额外输入 | 训练资源中一手可确认部分 | data→train→eval 闭环 |
|---|---|---|---|
| **ICCL** | instruction-following 与 contextual-causal collaboration；详细缓存/外部资产是否能从公开 repo 全部再生成，本次未锁定 | batch size 16，LR `1e-5`，warmup ratio `0.1`；**已取得证据中 GPU 型号/数量/显存未声明** | 官方 GitHub 可识别，但本次未取得足以证明 raw ESL/CTB→exact pairs→fold→evaluator 的完整闭环 |
| **LKCER** | 论文题名及方法明确依赖 LLM knowledge 与 concept-level event relations；这些知识的生成/缓存可复现资产 **未取得** | **未取得充分硬件声明** | 本次精确标题/作者搜索 **未查得可确认的作者官方代码仓库**；“未查得”不等于绝对不存在 |
| **DICP** | knowledge/preference + dynamic interval contrastive prompt | AdamW，LR `1e-6`，batch 8，max generation length 30，30 epochs；论文明确写 **Tesla V100 GPU**，但未在已取得证据中给出显存容量和 GPU 数量 | 官方 GitHub 可识别；但 exact preprocessing/evaluator 闭环仍未证明 |
| **DECLV** | dynamic energy-based contrastive learning + multi-stage knowledge verification | **未取得正文资源明细** | 本次未查得可确认的作者官方代码仓库；且与 LKCER 团队高度重叠 |

DICP 的这些训练参数来自论文实验设置，而不是二手榜单。 citeturn2find9turn6view2

### Baseline 来源审计

这是当前最不应该混在一起的一项。四篇论文的结果表可能同时含：

**本论文模型；作者重新实现的 baseline；直接引用旧论文的 reported results。**

在没有逐个读取结果表脚注、代码 config 和 logs 的情况下，不能把表里出现一个 baseline 名字解释成“当前 paper repository 可以执行这个 baseline”。本次没有为所有 baseline 取得足够的 table-note / source-code 对照，因此一律不把它们升级为“同代码重跑”。

也正因为如此，**本报告刻意不制作 ICCL/LKCER/DICP/DECLV F1 的跨论文差值表**。这不是遗漏：在 corpus version、exact folds、pair generator、negative sampling、evaluator 尚未同时锁定的情况下，给出 “A 比 B 高 x.x F1” 会违反你的审计规则。

## Compatibility/conflict matrix

### 严格同轴判断

| 论文对 | 独立团队？ | 两边都声称 ESL 5-fold / CTB 10-fold？ | 是否引用 Shen et al. processing？ | exact split/pair/evaluator 已证明一致？ | 可作为严格同轴数字比较？ |
|---|---:|---:|---:|---:|---:|
| ICCL ↔ LKCER | **是** | **是** | **是** | **否** | **NO** |
| ICCL ↔ DICP | **是** | **是** | **是** | **否** | **NO** |
| LKCER ↔ DICP | **是** | **是** | **是** | **否** | **NO** |
| LKCER ↔ DECLV | **否，作者高度重叠** | DECLV 本次正文未完整锁定 | 未锁定 | **否** | **NO** |
| ICCL ↔ DECLV | 是 | DECLV 未完整锁定 | 未锁定 | **否** | **NO** |
| DICP ↔ DECLV | 是 | DECLV 未完整锁定 | 未锁定 | **否** | **NO** |

前三篇关于 5/10 folds 与 Shen preprocessing 的共同表述是一致的。 citeturn6view0turn6view1turn6view2

但是严格比较中：

\[
\text{same number of folds}
\;\not\Rightarrow\;
\text{same folds}
\]

进一步，

\[
\text{same preprocessing citation}
\;\not\Rightarrow\;
\text{same generated pair files}
\]

尤其当实验还引入 “known causal event pairs” 或随机选择这些 pairs 时，真正需要冻结的是：

\[
(\text{raw release},\ \text{document IDs},\ \text{candidate generator},\
\text{random augmentation},\ \text{labels},\
\text{prediction format},\ \text{evaluator})
\]

当前没有一手证据把整个元组唯一化。

### 哪些结果暂时只能称为“表面兼容”

ICCL、LKCER、DICP 是最接近同轴的一组，因为三篇都明确声称沿用 Shen et al. (2022) processing，并明确使用 ESL 5-fold / CTB 10-fold。 citeturn2find0turn2find5turn2find9

但在你设定的审计门槛下，其状态只能是：

> **protocol lineage apparently shared, executable protocol identity not established。**

所以不能把这三篇论文表格中的 ESL/CTB F1 做横向减法。

### DECLV 不能提供第四支独立竞争团队

这是整个候选池里最明确的冲突之一。

DECLV 的四位作者：

> Shan Su, Yong Xie, Keqing He, Meina Song

均属于 LKCER 的六人作者集合：

> Shan Su, Xia Yao, Yong Xie, Yu Zhang, Keqing He, Meina Song.

因此即便二者 protocol 与代码未来都完全取得，**按“作者团队独立”的规则，它们也至多贡献一个团队族。** citeturn0search2turn0search1

## Repository reproducibility audit

### 数据仓库

| Repo | 第一方 URL | default branch / HEAD | license | archived | 静态审计结论 |
|---|---|---|---|---|---|
| EventStoryLine | `https://github.com/tommasoc80/EventStoryLine` | `master`; `2b6f420a619a013fbfadbc6f5a41b125e74bb595` | GitHub 识别 MIT | false | 数据版本历史真实存在，但不能把方法论文无版本的 “ESL” 自动绑定到 HEAD |
| Causal-TimeBank | `https://github.com/paramitamirza/Causal-TimeBank` | `master`; `9db986739937b894ded84c708c2d15bab3f8078d` | GitHub license field null；README 有 CC BY-NC-SA 3.0 声明 | false | CAT/TimeML 与公共下载入口可确认；上游 TimeBank 权利边界与 exact experimental split 仍未冻结 |

EventStoryLine API：

`https://api.github.com/repos/tommasoc80/EventStoryLine`

CTB API：

`https://api.github.com/repos/paramitamirza/Causal-TimeBank`

### 方法仓库

| 方法 | 官方仓库核验 | branch / metadata | license | README→预处理→训练→评测 | requirements / lock | checkpoint/log | issue reproduction evidence |
|---|---|---|---|---|---|---|---|
| **ICCL** | **有可识别作者仓库**：`https://github.com/ChaoLiang-HUST/ICCL` | default `main`; repo created 2024-10-02；GitHub metadata `pushed_at` 2025-01-08；未 archived | MIT | **未取得足够证据证明完整闭环** | 本次未完整锁定 | **未取得** | repo 有 open issues，但本次未逐 issue 核实成功/失败报告 |
| **LKCER** | **本次未查得可确认的作者官方 repo** | — | — | — | — | — | — |
| **DICP** | **有可识别仓库**：`https://github.com/sj1071-cell/DICP` | default `master`; created 2025-10-14；`pushed_at` 2025-11-11；未 archived | GitHub metadata 未识别 license | **尚未证明 raw data 到 F1 闭环** | 本次未完整锁定 | **未取得** | 元数据显示 0 open issues；这不能作为复现成功证据 |
| **DECLV** | **本次未查得可确认的作者官方 repo** | — | — | — | — | — | — |

ICCL 仓库入口也可由论文名/作者仓库搜索对应到：

`https://github.com/ChaoLiang-HUST/ICCL`。 citeturn8search3

DICP 的公开仓库：

`https://github.com/sj1071-cell/DICP`。 citeturn8search1

对 LKCER 与 DECLV，本次用论文精确标题、方法名和作者组合搜索，没有取得一个能可靠归属作者团队的 GitHub repo；因此准确措辞是**“未查得官方仓库”**，而不是“官方仓库绝对不存在”。LKCER 的论文 PDF 在本次检索到的相关段落中也没有给出一个已核实 GitHub 地址。 citeturn0search2turn0search1

### 为什么“有 GitHub”仍然不够

ICCL 和 DICP 是最有希望的两个候选，但这里的资格要求不是：

> paper + GitHub = reproducible.

而必须是：

> raw official corpus  
> → documented preprocessing  
> → exact fold files  
> → deterministic/seeded candidate & negative generation  
> → train command/config  
> → prediction file  
> → exact evaluator  
> → paper metric.

本次静态审计没有为任一个候选取得这个全链条的充分证据。因此不能因为仓库存在就把 Split/Pair/Evaluator gate 改判 PASS。

另外，ICCL/DICP/LKCER 把公平比较依据指向 Shen et al. (2022) tools，意味着那个**上游 preprocessing artifact 实际上是 benchmark specification 的关键组成部分**。本次没有取得足以把该工具的 exact repo commit、fold-ID manifest、candidate counts、negative generation、evaluator 全部冻结的一手闭环。这不是旁支缺失，而是本次 NO-GO 的中心证据之一。 citeturn2find0turn2find5turn2find9

## Two-baseline recommendation 与 27GB feasibility

### 严格意义上无法批准两个 baseline

按照你指定的规则，本报告**不批准两个“已经合格”的 baseline**。

最接近的两个候选确实是 **ICCL + DICP**，而不是 LKCER + DECLV：

| 候选 | 为什么是最接近的 | 为什么现在仍不能批准 |
|---|---|---|
| **ICCL** | EMNLP 2024 正式发表；作者团队独立；有公开 GitHub；明确 follow Shen 2022 processing；ESL 5-fold / CTB 10-fold | ESL exact version、exact fold IDs、candidate pair generator、negative protocol、evaluator path/commit 未被完整锁定 |
| **DICP** | Findings EMNLP 2025 正式发表；与 ICCL 作者独立；公开 GitHub；明确 same Shen processing/same test set；有 V100 实验硬件证据 | 同样缺 exact protocol artifacts；ESL 又含随机选择 known causal pairs，seed/ratio 等若未冻结会直接改变训练数据；单卡显存条件不完整 |

ICCL 第一方论文：`https://aclanthology.org/2024.emnlp-main.51.pdf`。 citeturn0search3turn2find0

DICP 第一方论文：`https://aclanthology.org/2025.findings-emnlp.139.pdf`。 citeturn0search0turn2find9

两者至少满足“**两支真正独立的近期正式团队**”这一部分；问题在于尚未满足“**同轴且当前可执行**”这一部分。

### 从 raw data 到 F1 的最短命令链

对一个合格 baseline，这里本应能写成类似：

`download exact release → preprocess with pinned command → generate fold N → train config X → predict → evaluator predictions gold`

但对 ICCL 与 DICP，**本次没有取得足以逐字符给出并验证这些命令、路径和 commit 的证据**。

因此正确写法不是凭 README 风格自己补一套命令，而是：

**ICCL：可审计最短命令链未取得。**

需要补齐的资产至少包括：
`ESL/CTB exact input files + Shen preprocessing commit + exact fold manifests + pair counts + ICCL train/eval config + evaluator entry point`。

**DICP：可审计最短命令链未取得。**

需要补齐：
`exact corpus input + Shen pipeline revision + ESL known-pair augmentation seed/ratio + fold manifests + DICP config + prediction/evaluation command`。

这正是“仓库存在但还没有复现资格”与“代码完全不存在”的区别。

### 单张约 27GB GPU

DICP 是四篇中目前硬件证据最明确的一篇：论文实验部分报告使用 **Tesla V100 GPU**，batch size 8，学习率 `1e-6`，max generation length 30，训练 30 epochs。`https://aclanthology.org/2025.findings-emnlp.139.pdf`。 citeturn2find9turn6view2

但 V100 存在不同显存规格，而已取得论文证据没有把 “V100” 进一步绑定到一个足以证明 **≤27GB peak VRAM** 的容量，也没有提供本地测得峰值。因此：

> DICP：**27GB plausible，但不能 PASS。**

对 ICCL，已取得的论文实验信息包括 batch size 16、learning rate `1e-5`、warmup ratio `0.1`，但没有取得可审计的 GPU 型号/数量/显存声明。 citeturn2find0turn6view0

因此：

> ICCL：**27GB 未证明。**

LKCER/DECLV 又缺少本次可确认的官方执行闭环，因此不能靠降低 batch size 的一般经验替它们补证据。

最终的 27GB 结论是：

> **目前没有两个 baseline 同时满足“独立 + 同轴 + 代码闭环 + 有可信 27GB 单卡路径”。所以算力门槛 FAIL。**

需要强调，这不是说它们“一定跑不进 27GB”，而是按照你的审计标准，**没有证据就不能判 PASS**。

## Go/No-Go gates

| 门槛 | 通过标准 | 审计状态 | 理由 |
|---|---|---:|---|
| **数据** | 精确版本、文件、获取方式和许可边界可锁定 | **FAIL** | ESL 多版本存在，但四篇实验与 exact ESL release/file set 未建立可验证映射；CTB 公开仓库与 README CC 声明可确认，但上游 TimeBank 文本权利边界没有完全锁定 |
| **Split** | exact fold/topic/doc IDs 可重建 | **FAIL** | ICCL/LKCER/DICP 只足以确认 ESL 5-fold / CTB 10-fold + Shen 2022 lineage；未取得 exact fold manifests/IDs |
| **Pair** | candidate/negative generation 可重建并能计数校验 | **FAIL** | candidate universe、方向反转、负例采样完整规则/seed/count 未锁定；ICCL/DICP 的 additional/known causal pairs 又引入额外训练数据处理 |
| **Evaluator** | 代码可取得、指标完整、prediction→P/R/F1 可执行 | **FAIL** | 尚未取得一个被证明与这些 paper results 同轴的 evaluator file/path/commit + metric definition |
| **对手** | 至少两个独立 2024–2026 正式方法可在同一协议复现 | **FAIL** | ICCL+DICP 是两个独立正式候选，但“同一可执行协议”未证明；LKCER+DECLV 又不是独立团队 |
| **算力** | 至少两个 baseline 有可信 27GB 单卡路径 | **FAIL** | DICP 只有 V100 级别证据但容量未锁；ICCL 未取得 GPU 资源声明；不足两个可认证路径 |

### 总判定

**NO-GO。**

而且不是边缘性的 NO-GO。按你定义的规则，Data/Split/Pair/Evaluator 四个 benchmark-specification gate 中目前至少后三个明确没有被锁住；Opponent gate 也不能 PASS。

因此不能降格为 CONDITIONAL GO。

**只有下面这种情况才可能把结论升级为 CONDITIONAL GO：** raw data、exact folds、generated pairs 和 evaluator 都已经静态锁定，仅剩“在你本地跑一下脚本看看依赖是否还能启动”。当前不是这种状态。

**未能核实**

以下信息本次没有取得足够第一方证据，全部明确保留为“未取得”，不以常见 ECI 做法推断：

1. ESL v0.9/v1.0/v1.2/v1.5 每版的完整 topics、documents、event mentions、expert CLINK、crowd CLINK、expert+crowd CLINK 精确实数及其统计脚本。
2. ESL v1.2 的完整官方 release/tree 证据，以及四个版本的独立 release/tag 语义。
3. ESL 各版本的作者发布 checksum。
4. 四篇方法具体使用哪个 ESL release，以及具体输入 XML/CAT 文件集合。
5. CTB 两种格式的本次逐文件文件名清单、版本级 checksum、精确 docs/events/causal-links/pair counts。
6. CTB README 的 CC BY-NC-SA 3.0 声明与上游 TimeBank/LDC 文本许可之间的完整权利链。
7. Shen et al. (2022) preprocessing tools 的 exact repository revision、fold manifest、pair generator、negative sampling 和 evaluator 的完整冻结状态。
8. 四篇论文生成后的 exact ESL 5-fold / CTB 10-fold document/topic IDs。
9. 每个 fold 的正负 pair 数，以及由这些 pair counts 对论文结果进行 checksum-like validation。
10. ICCL/DICP repo 当前 HEAD commit、requirements/lockfile、checkpoint/log、README 完整命令链的逐文件静态审计；已取得的是仓库存在性及部分 metadata，而不是运行成功。
11. LKCER/DECLV 的作者官方代码仓库；本次是“未查得”，不是“证明不存在”。
12. DECLV 正文的完整 protocol matrix。本次 ACL 正式页面可核，但 PDF renderer 没有成功取得正文，因此没有从 LKCER 或其他论文反推其细节。
13. 所有论文 P/R/F1 是否明确采用 positive-class micro、macro、micro pooling across folds 或 fold-wise arithmetic mean，以及 negative class 是否计入 F1。
14. 两个合格 baseline 的真实 peak VRAM。

其中第 4、7、8、9 项尤其关键：它们不是“论文写得不够漂亮”的小问题，而是直接决定 benchmark 是否同轴。

**与已有判断冲突或出乎预期的事实**

最值得警惕的不是“论文少”，而恰恰是**论文看起来非常像同一 benchmark**。

ICCL、LKCER、DICP 三篇都使用 ESL 5-fold / CTB 10-fold，并都把处理依据指向 Shen et al. (2022)。 citeturn2find0turn2find5turn2find9

乍看之下，这很容易被写成：

> “Following prior work, all methods use the same 5-fold/10-fold setting.”

但目前的一手证据只允许写：

> “All three papers state the same fold counts and cite the same preprocessing lineage.”

两句话的证据强度完全不同。

第二个出乎预期之处是 **DECLV 并不能明显增加独立竞争密度**。它不是与 LKCER 无关的第四个团队；DECLV 全部四位作者都属于 LKCER 作者集合。 citeturn0search2turn0search1

第三个容易产生错误乐观判断的地方是 **Causal-TimeBank 的“公开可下载”**。作者 GitHub 可以公开访问，README 也有 CC BY-NC-SA 3.0 声明；但语料本身明确构建在 TimeBank events 上。于是“下载不需要登录”与“所有底层文本都有无歧义的开放许可”是不同命题。对硕士论文内部实验而言，这可能是可管理问题；对你提出的“完全公开、许可边界可审计 benchmark”则不能直接 PASS。

第四个事实是 DICP 的硬件描述比其他候选更有帮助：V100、batch size 8 等信息确实提升了它成为本地 baseline 的可信度。 citeturn2find9turn6view2 但 **“V100 跑过”仍不能逻辑上推出“你的约 27GB 单卡已被证明足够”**，因为 V100 的显存规格和论文实际配置没有在本次证据中锁死。

第五个事实是，**有两个独立近期正式方法这一表面条件其实接近满足**：ICCL 与 DICP 的作者集合独立，均为 2024–2025 正式 ACL 系列论文，并各有可识别 GitHub。真正把结论推到 NO-GO 的不是“没有两篇论文”，而是：

> **没有证明这两篇论文现在能够落到同一被冻结的数据/split/pair/evaluator 轴上。**

这比“竞争方法数量不足”更根本。

**一手来源清单**

论文：

- ICCL ACL Anthology 正式页：`https://aclanthology.org/2024.emnlp-main.51/`；PDF：`https://aclanthology.org/2024.emnlp-main.51.pdf`；DOI：`https://doi.org/10.18653/v1/2024.emnlp-main.51`。 citeturn0search3
- LKCER ACL Anthology 正式页：`https://aclanthology.org/2025.coling-main.495/`；PDF：`https://aclanthology.org/2025.coling-main.495.pdf`；DOI：`https://doi.org/10.18653/v1/2025.coling-main.495`。 citeturn0search2
- DICP ACL Anthology 正式页：`https://aclanthology.org/2025.findings-emnlp.139/`；PDF：`https://aclanthology.org/2025.findings-emnlp.139.pdf`；DOI：`https://doi.org/10.18653/v1/2025.findings-emnlp.139`。 citeturn0search0
- DECLV ACL Anthology 正式页：`https://aclanthology.org/2025.emnlp-main.616/`；PDF：`https://aclanthology.org/2025.emnlp-main.616.pdf`；DOI：`https://doi.org/10.18653/v1/2025.emnlp-main.616`。 citeturn0search1

数据：

- EventStoryLine 作者仓库：`https://github.com/tommasoc80/EventStoryLine`。 citeturn7search0
- EventStoryLine repository API：`https://api.github.com/repos/tommasoc80/EventStoryLine`
- EventStoryLine audit HEAD query：`https://api.github.com/repos/tommasoc80/EventStoryLine/commits?per_page=1`
- EventStoryLine MIT file：`https://github.com/tommasoc80/EventStoryLine/blob/master/LICENSE`
- Causal-TimeBank 作者仓库：`https://github.com/paramitamirza/Causal-TimeBank`
- Causal-TimeBank repository API：`https://api.github.com/repos/paramitamirza/Causal-TimeBank`
- Causal-TimeBank audit HEAD query：`https://api.github.com/repos/paramitamirza/Causal-TimeBank/commits?per_page=1`

代码：

- ICCL：`https://github.com/ChaoLiang-HUST/ICCL`。 citeturn8search3
- ICCL repository API：`https://api.github.com/repos/ChaoLiang-HUST/ICCL`
- DICP：`https://github.com/sj1071-cell/DICP`。 citeturn8search1
- DICP repository API：`https://api.github.com/repos/sj1071-cell/DICP`

**审计底线结论：** 截至 **2026-08-25**，ESL/CTB ECI 可以作为一个有连续论文谱系的研究问题，但在你给出的严格定义下，尚不能被认证为一个**已冻结、公开、第三方可独立重建、拥有至少两个独立近期可复现 baseline、且已有可信 27GB 单卡路径的硕士论文公开可比主任务**。故总判定保持 **NO-GO**。