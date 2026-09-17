# 外部对手名册与复现保真度计划

> 建立于 **2026-09-11**，服务 `SPEC.md` v1.1.0 的 **QR-001**（baseline 广度是报告要求，不是准入门）
> 与 **FR-016**（每个外部复现必须带保真度状态）。
> 本文件只定义**名册与验证路径**；任何实测数字只写进 `results/PHASE_*.md`。

## FR-016 fidelity states

（FR-016 的两种合法状态）

| 状态 | 判据 | 论文表里怎么写 |
|---|---|---|
| **(a) Verified** | 在该方法**自己的原始基准与划分**上复现出其**已发表数字**，落在**事前声明**的容差内 | `方法名[ref]` |
| **(b) Unverifiable** | 验证不可能，且**点名具体障碍**（无 trainer / 语料需许可 / checkpoint 失效 / 划分未公开） | `方法名[ref]（透明适配）` + 脚注逐条列出与原设定的差异 |

**红线**：状态 (b) 的行**不得**写成"忠实复现"，**不得**用来主张"该公开方法比它自己报的弱"。
容差必须在跑之前写定；跑完再定容差等同于没有验证。

## 1. Ch1 · 事件身份消解（MAVEN-ERE 文档内共指；MUC/B³/CEAFe/BLANC，官方 `evaluate.py`）

| # | 方法 | 原始基准 | 代码 | 保真度路径 | 状态 |
|---|---|---|---|---|---|
| 1 | MAVEN-ERE official joint（主锚） | MAVEN-ERE | ✅ 官方 | **已验证**：四个共指指标与官方论文 ±0.4 内（E9，`PHASE_R1.md` §17.2） | **(a) 已完成** |
| 2 | **Global-Local Topic**（Xu, Li, Zhu, EMNLP 2022） | KBP 2017 | ✅ EasyECR `example_emnlp2022.py` + `global_local_topic_mavenere.yaml`（1,715 行 Lightning trainer）；仓库 `github.com/hqyang/EasyECR` @ `f6cd779f…115a9` | **(b)**：KBP 2017 需 LDC 许可，不可得（`PHASE_R1.md` §22.5） | **conditionally_runnable**（C-2，2026-09-11，静态裁决；活体 import 待 4090） |
| 3 | CorefPrompt（Xu et al., EMNLP 2023） | KBP 2017 | ⚠️ EasyECR 有实现，但配置依赖 OmniEvent 预测论元文件（checkpoint 已失效） | 若以我方 Qwen3 论元替代 → 必为 (b)，须列差异 | **降级候选** |
| 4 | Qwen3 mention-local 论元池化 `qwen3-argument-s13-r2` | — | 自建 | **不适用**：本文自建的注册负面对照，非外部方法 | 已有 |
| 5 | LLM 对照（Qwen3-8B，LoRA/prompt） | — | 自建 | **不适用**：同上 | 待建 |

**不可运行，进可得性表**：ACCI（`era211/ACCI` 全历史仅 README）、IP&M 2024（无公开代码，全文不可得，E9）、
RESIJ（未取得）、OmniEvent EAE checkpoint（失效）、TextEE（无 checkpoint）。

### 1.1 Global-Local Topic 的保真度决策树

```
能否取得 KBP 2017（LDC 许可语料）？
├─ 能 → 在 KBP2017 上跑 EasyECR，对照原文 K-AVG/MUC/B³/CEAFe/BLANC
│        容差事前定为 ±1.0 K-AVG  →  落入则 (a) Verified
└─ 不能 → (b) Unverifiable，障碍写「原始基准 KBP 2017 需 LDC 许可，本项目无法取得」
           须逐条列出差异：语料（KBP2017→MAVEN-ERE）、mention 来源（预测→金标）、
           评测器（TAC→MAVEN 官方 evaluate.py）、超参是否沿用原配置

**C-2 已走右支（2026-09-11）**：本项目无 LDC 许可、无获取途径，也未申请 →
**FR-016 状态 (b) Unverifiable**，四项差异按上面逐条列。第 5 章那行 baseline 可以有，
但表里必须标「透明适配」。
```

⚠️ 交叉参考：徐昇学位论文表 3-2 给出该方法在 KBP 2017 上的 K-AVG 51.2 / MUC 46.2，
可作为容差比对的第二来源（见 `replan/THESIS_REF_f5_徐昇_事件共指.md`）。

### 1.2 EasyECR 本身的已知差异（无论 (a)/(b) 都必须披露）

仓库**无 LICENSE**（需联系作者或在论文中声明用途）；`requirements.txt` 声明 `torch==2.0.1 /
transformers==4.21.2`，与本项目 cu128 栈互斥，须独立 venv 且只能上 4090（5090 sm_120 不支持 torch 2.0）；
配置内路径为作者本机硬编码，需改写。

✅ **C-2 实测补充（2026-09-11，见 `results/PHASE_R1.md` §22）**：MAVEN-ERE 适配器与配置**仓库里已有**，
其自报计数与官方完全一致（2913/710/857 篇）；选档与 9 个聚类阈值都在 **dev** 上扫，不碰 test；
另有独立 `predict` 通路，可取它的簇用我们冻结的官方 `evaluate.py` 重打分。
阻断项共 6 条、全部点名可数，其中 vendor `SelfAttentiveSpanExtractor` **恰好 2 个调用点**。
建议独立 venv 按其自身声明装 `torch==2.0.1`（4090 sm_89 支持），补丁数最少。

⚠️ **依赖自相矛盾（2026-09-11 联网核实，同日由求解器机器复现，见 `PHASE_R1.md` §22.2）**：`global_local_topic.py` 从
`allennlp.modules.span_extractors` 导入 `SelfAttentiveSpanExtractor`，而 **allennlp 最后一个发行版是
2.10.1，其依赖约束为 `torch (<1.13.0,>=1.10.0)`**——与仓库自己声明的 `torch==2.0.1` **不可能同时满足**。
因此 `pip install allennlp` 这条路在该仓库的声明环境下走不通。
**结论：必须 vendor `SelfAttentiveSpanExtractor`**（约 50 行自注意力加权 span 池化），
作为 FR-016 必须披露的透明补丁之一，并记录补丁前后的文件 hash。这不是可选项，是 C-2 的必做项。

## 2. Ch2 · 事件关系抽取（MAVEN-ERE；causal/subevent/temporal P/R/F1，官方 `evaluate.py`）

| # | 方法 | 原始基准 | 代码 | 保真度路径 | 状态 |
|---|---|---|---|---|---|
| 1 | MAVEN-ERE official joint（主锚） | MAVEN-ERE | ✅ 官方 | **已验证**（E9） | **(a) 已完成** |
| 2 | TacoERE `taco-s13-r3` | — | ❌ 无公开代码 | 不可能 → **(b)**，障碍＝「论文未发布实现」 | **(b) 已成立** |
| 3 | LLMERE-causal（COLING 2025） | MAVEN-ERE official valid 710 篇，自写评测器，causal 36.04 | ⚠️ 有数据构造/评测器/**已发布预测**，无 trainer | **(b) Unverifiable**（作者 2026-09-15 裁决），障碍＝「保真度验证需读取封存 final-valid，按 A 类红线放弃」 | **(b) 已成立**；本项目自跑的生成本轮失败（退化重复），主表该行只报 (b) 与障碍 |
| 4 | A3.6 fallback | — | 本文 | **不适用**：本文前期方法，`failed` 身份须在表头标明 | 已有 |
| 5 | LLM 对照（Qwen3-8B 等） | — | 自建 | **不适用** | 待建 |

**不可运行，进可得性表**：RESIJ、KnowQA、2025 two-stage ERE、MAQInstruct（口径可引用但无同协议复现）。

### 2.1 ✅ LLMERE 的保真度路径已裁定（作者 2026-09-15）：取 (b) Unverifiable

**裁决**：保持 `HANDOFF.md` §E.1a 第 6 条，**不为一个 (a) 标记去读封存的 final-valid**。
该行在 Ch4 主表标 **(b) 透明适配 / Unverifiable**，障碍原文写：
「其已发布预测落在 official valid 710 篇上，而该 710 篇是本项目封存的 final-valid；
按 A 类红线不做评分性读取，故无法复现其 causal 36.04。」

**这不是硬伤**：MAVEN-ERE 的 CodaLab 提交通道已关闭（已核），同协议重跑并声明口径是通行做法，
MAQInstruct（2025）就用 valid 当 test（已核先例）。QR-001 v1.1.0 把 baseline 广度降为**报告要求**，
(b) + 点名障碍是合规的。**一旦开了「只读一次」这个口子，后面几个月守不住。**

<details><summary>裁定前的三条出路（留作记录）</summary>

FR-016 要求验证复现正确性。LLMERE **发布了自己在 official valid 710 篇上的预测文件**，
因此最直接的验证是：用官方 `evaluate.py` 给它的已发布预测打分，看能否复现其 causal 36.04。

但 `HANDOFF.md` §E.1a 第 6 条（作者 2026-09-07 裁决）明确写着**不做**这件事，理由是
「710 篇是封存的 final-valid，不值这笔账」。

⚠️ **两条规则现在互相抵触，本文件不擅自选边。** 三种出路：
1. 保持 §E.1a，LLMERE 直接记为 **(b) Unverifiable**，障碍＝「保真度验证需读取封存 final-valid，
   按 A 类红线放弃验证」——**成本为零，且完全诚实**；
2. 只做一次**评分性**读取（不选任何模型/阈值/结构），按 Phase E 的先例记入 final-valid ledger；
3. 放弃 LLMERE，改用其他关系方法族。

**建议取 1。** 它不花 GPU、不碰 final-valid，且 (b) 状态本来就允许它留在主表。

</details>

## 3. Ch3 · 事件事实性检测（MAVEN-FACT；五类 macro-F1，2,913 篇五折 OOF）

| # | 方法 | 原始基准 | 代码 | 保真度路径 | 状态 |
|---|---|---|---|---|---|
| 1 | RoBERTa+CLS（主锚） | MAVEN-FACT | ✅ | 已在预冻结五折 OOF 上验收（80 产物重哈希、折隔离、覆盖核对） | 已完成 |
| 2 | DMRoBERTa dynamic-multi | MAVEN-FACT | ✅ | 同上 | 已完成 |
| 3 | **MAVEN-FACT supporting-word pipeline** | MAVEN-FACT 官方划分 | ✅ `THU-KEG/MAVEN-FACT` | **可验证**：先在官方划分上复现官方论文数字（容差事前定 ±1.0 macro-F1），再转本项目五折 OOF | **(a) 可达，待做** |
| 4 | LLM 对照 | MAVEN-FACT 论文自带 LLM 结果 | 自建 | 可与论文 LLM 行对读 | 待建 |

Ch3 是三章里保真度最容易做实的一章：官方仓库、官方划分、官方数字三者齐备。

## 4. LLM 对照的定位（作者 2026-09-11 授权）

LLM **只作 baseline 行与训练侧数据增强**，**不得**为主评测生成标注（`SPEC.md` Scope Boundaries 禁止
新标注进入训练、选模或主评测；MAVEN 三件套本就有官方金标）。

先例：陈玉婷主表 7 个对手里 3 个是 LLaMA2-7B / Baichuan2-7B / ChatGLM3-6B 的 LoRA 微调；
钱子杰用 ChatGPT 做跨语言数据增强（训练侧）。

本项目现成资源：gpu-4090 已有 Qwen3-8B 权重（C5 契约内容寻址目录）与 `.venv-llmere-causal-s13`
里的 LLaMA-Factory。**这是我们能拿到的最便宜的主表宽度。**
LLM 行属自建对照，不适用 FR-016 的保真度验证，但须披露 backbone、权重 revision、微调方式与提示模板。

## 6. Ch6 · 下游事件预测应用（本地重建 CGEP-MAVEN；MRR 与 Hit@1/3/10/20/50）

> C-4 调研已完成（2026-09-11，联网核实）。**Gate 3 判定：能凑够 ≥3 个公开对手，Ch6 按带对手的
> 应用章执行。** 保真度路径见 §6.2，尚未冻结的是各对手在**我们重建协议**上的实跑。

基座论文：**SeDGPL** —《What Would Happen Next? Predicting Consequences from An Event Causality
Graph》，**Findings of EMNLP 2024**，Chuanhong Zhan，[aclanthology.org/2024.findings-emnlp.45](https://aclanthology.org/2024.findings-emnlp.45.pdf)，
代码 [github.com/zhanchuanhong/SeDGPL](https://github.com/zhanchuanhong/SeDGPL)（含 `main.py`/`model.py`/`load_data.py`/`run.sh`，训练代码齐备）。

### 6.1 候选对手（全部是 SeDGPL 论文自己比过的 CGEP 对手，均有公开训练代码）

原论文 **CGEP-MAVEN（512 候选）** 表，MRR / Hit@1 / @3 / @10 / @20 / @50：

| 方法 | 出处 | 原文 CGEP-MAVEN 数字 | 代码 | 训练代码 |
|---|---|---|---|---|
| **SeDGPL** | Findings of EMNLP 2024 | **27.9 / 21.9 / 28.9 / 40.8 / 48.1 / 57.9** | [zhanchuanhong/SeDGPL](https://github.com/zhanchuanhong/SeDGPL) | ✅ |
| **BART contrastive** | Zhu et al., AAAI 2023 | 24.7 / 19.5 / 24.5 / 34.8 / 42.6 / 53.6 | [zhufq00/mcnc](https://github.com/zhufq00/mcnc) | ✅ 两阶段训练命令齐备 |
| **CSProm-KG** | Chen et al., Findings of ACL 2023 | 22.3 / 18.1 / 23.2 / 31.0 / 38.4 / 50.7 | [chenchens190009/CSProm-KG](https://github.com/chenchens190009/CSProm-KG) | ✅ |
| **MCPredictor** | Bai et al., EMNLP 2021 | 18.1 / 13.0 / 18.4 / 27.3 / 32.0 / 43.2 | [waltbai/MCPredictor](https://github.com/waltbai/MCPredictor) | ✅ |
| **SimKGC** | Wang et al., ACL 2022 | 9.3 / 4.5 / 9.2 / 18.0 / 25.3 / 35.0 | [intfloat/SimKGC](https://github.com/intfloat/SimKGC) | ✅ |

四个非 SeDGPL 对手的原任务都不是 CGEP（CSProm-KG/SimKGC 是知识图谱补全，BART contrastive 与
MCPredictor 是五选一的 MCNC），**它们的 CGEP 数字是 SeDGPL 作者自己做的适配**，并非其原论文结果。

### 6.2 ⚠️ 保真度的硬约束：原文数字不可直接入我们的表

**原论文的 CGEP-MAVEN 派生数据（512 候选）从未发布**，我们用的是**本地重建协议**（1,908 实例）。
因此上表的 27.9 等数字与我们自跑的 gold `.1802` **不可同表比较**——候选集规模与构造方式都不同。

FR-016 判定：

- **我们必须在自己的重建协议上重跑这五个方法**，重跑结果才是 Ch6 主表的行；
- 保真度状态取决于能否复现它们的已发表数字。由于 MAVEN 侧派生数据未发布，
  **默认落 (b) Unverifiable，障碍写「原论文 CGEP-MAVEN 派生 split/candidates 未公开」**；
- **可能升到 (a) 的一条路**：原论文同时报 **CGEP-ESC（256 候选）**，而 EventStoryLine 是公开语料。
  若能按原文描述重建 CGEP-ESC 并复现其 ESC 列数字（容差事前定），则保真度在 ESC 上取得 (a)，
  再以同一份代码转到我们的 MAVEN 重建协议。
  ✅ **C-4b 已核（2026-09-13，一手，见 `results/PHASE_E.md`）：`conditionally_runnable`。**
  切分口径确认——原文 §5.1 声明的是 **topic 级 5 折 CV**（最后两个 topic 作 dev，其余 20 个做 5 折），
  **不是**文档切分。公开的 `ESCSubWoRe.npy`（与我们本地同一 SHA-256 `8ec791fb…5026`）
  就是论文那份数据（22 topic / 244 篇 / 1,192 实例 vs Table 1 的 243 / 1,191），
  但**不含切分键、不含折分配，仓库也没有任何 ESC 代码路径**（loader 写死 MAVEN）。
  ⚠️ **此前「19.6 是泄漏值」的记载已被原文推翻**：原文声明的就是非泄漏口径。
  真实情况是**我们在声明口径下复现不到它**（我们的 topic-CV .0599 vs 原文 .196；
  文档切分才到 .1802），这是复现缺口，不是作者泄漏。三个透明补丁与两处未公开自由度见结果页。

### 6.2b ✅ 保真度路径已裁定（作者 2026-09-15）

| 方法 | FR-016 状态 | 障碍原文 |
|---|---|---|
| **SeDGPL**（基座） | **(b)** | 「原论文 CGEP-MAVEN 派生数据未发布；其 CGEP-ESC 一列按原文 §5.1 声明的 topic 级 5 折 CV 复现只得 MRR .0599 vs 原文 .196，公开件不含折分配与 dev topic 名单，另有两处未公开自由度」 |
| **CSProm-KG** | ✅ **(a) 已实测取得（2026-09-16）**：WN18RR **MRR 0.572682** vs 公布 0.572660（容差 ±0.005），H@1/3/10 = 52.06 / 59.03 / 67.77 vs 52.06 / 59.00 / 67.79（各 ±0.5），**四项全落容差内**；数字、五处透明补丁与前后 hash 见 [`results/PHASE_E.md`](results/PHASE_E.md)。⚠️ 在我们的重建协议上**仍是 (b)** | 「未实现 CGEP；SeDGPL 作者的适配未发布」 |
| **SimKGC** | **(b)** | 「原配置 `--batch-size 1024` 需 4×32 GB（其 README 第 18/111/116 行），5090 单卡 32 GB、4090 四卡 96 GB 均不足；减 batch 会改变其 in-batch 负样本数，按定义即非其发表设置」。**2026-09-17 已从推断升为本机实测**（单张 4090 / 23.52 GiB）：1024 OOM（差 300 MiB，加 `expandable_segments` 仍 OOM）、**512 也 OOM**（第一个 forward 就炸）、**256 稳定**（19.9 GB）⇒ 取 256，in-batch 负样本 1024→256。**表 6-2 的 SimKGC 行是它的下界，不是发表设置**，不得据此说它弱 |
| **BART contrastive** | **(b)** | 「`torch==1.7.1` + apex 版本墙；另需两阶段预训练」 |
| **MCPredictor** | **(b)** | 「需 LDC2011T07 Gigaword 许可 + python2.7 预处理链」 |

⚠️ **⑤ 的裁决与上一版建议相反，理由写在这里**：原先建议「只为 SeDGPL 走 ESC 的 (a)」。
C-4b 已在原文**声明的**口径下实测出 3 倍差距，再投一次小时级训练只是**重复确认一次失败**。
**有证据的 (b)**（差距数字 + 两处未公开自由度点名）比一个拿不到的 (a) 更结实，也比
「从产物反推它泄漏」这种旧说法诚实。若日后找到那两处自由度的答案，再回头取 (a)。

### 6.2c G-11a 第二刀：CGEP 适配本身（2026-09-17，详见 `results/PHASE_E.md`）

**已落地**：CGEP → KGC 的数据导出（`scripts/export_cgep_as_kgc.py`）、CSProm-KG 的第 6 处补丁
（只 dump 候选分数，前后 hash 已记）、以及用**我们自己的 evaluator** 打分的
`scripts/score_kgc_opponent.py`。CSProm-KG 的源码与数据已落到 `gpu-4090:/data/TJK/baselines/`。
**环境未建、训练未开始**（4090 隧道 09-17 20:09 掉线，其端口不在作者的 cpolar 更新脚本管辖内）。

⚠️ **一条决定「KGC 对手这两行该怎么读」的实测事实**：CGEP 的 query edge 规则要求尾节点
**outdeg 0、indeg 1**，所以金标后继在自己的 ECG 里只有那一条边；任何 triple 级切分把 query edge
拿掉之后，**1,908 个金标后继在训练图里全部是孤立点，而 6,892 个候选里有 4,863 个不是**。

| 对手 | 受这条影响吗 | 为什么 |
|---|---|---|
| **CSProm-KG** | **重** | 输出层就是**实体嵌入表**（ConvE 那一半），没训过的实体拿不到有意义的分数 ⇒ 结构那一半系统性偏离正确答案 |
| **SimKGC** | **轻，但不是零** | **编码器那一半免疫**：文本双编码器，实体表示由名字与描述编码而来，对未见实体是归纳式的 ⇒ **反而可能是更适配 CGEP 的那个 KGC 对手**，尽管其已发表 CGEP 数字最低（9.3）。**但它的 `rerank_by_graph` 不免疫**——那一步按训练 link graph 的 n-hop 邻居给候选加分（`--neighbor-weight 0.05`），而金标后继在训练图里没有边 ⇒ 加分只会落到干扰项上。⇒ **评测跑两遍**：`0.05`（他们的默认，进主表）与 `0.0`（关掉重排，作解释性消融）。同一个 checkpoint、两次前向，**不是调参**，是把这个变量单独测出来 |
| SeDGPL（基座） | 不受 | 按 **token id** 打分，`<a_i>` 词表跨 train/test 建 |

⇒ 这两行的数字**低不代表方法弱**，写进论文时必须带这条结构性解释；反过来也不得为了「好看」
换一个映射去凑分数。**并且这本身是一条可写的发现**：把 KGC 方法搬到 CGEP 上，
输出层是否依赖已训练的实体嵌入，决定了它还剩多少能力。

### 6.2a G-11a 第一刀：可得性与可运行性（2026-09-13 一手核实，详见 `results/PHASE_E.md`）

**结构性事实：四个对手没有一个实现 CGEP。** 它们实现的是各自原任务（mcnc/MCPredictor = MCNC
五选一；CSProm-KG/SimKGC = 知识图谱补全），SeDGPL 作者做的 CGEP 适配**从未发布**。
⇒ **表 6-2 的四行在我们的重建协议上注定是 (b) 透明适配**；(a) 只能在**各自的原基准**上取得，
用来证明我们把方法跑对了。**五个仓库全部没有 LICENSE 文件**，论文里如实写。

| 方法 | commit | 原基准数据 | FR-016 (a) 可达？ | 关键障碍 |
|---|---|---|---|---|
| SimKGC | `97cc43e4…` | ✅ 随仓库 + 已发布预测 | ✅ **最便宜** | 已发布预测**缺 `rank` 字段**（README 写了但文件里没有），只能重算 Hit@1，**不能靠打分现成预测省掉训练** |
| CSProm-KG | `9a807295…` | ✅ 随仓库 + 公开 checkpoint | ✅ | `torch==1.11.0+cu113` / `pytorch_lightning==1.9.3` 最高 sm_86，**4090(sm_89)/5090(sm_120) 都跑不了**，须升版并记补丁 |
| BART contrastive | `e895ed38…` | ✅ NEEG 随仓库 115 MB | ✅ 但最贵 | `torch==1.7.1` + **apex**，同一堵版本墙；另需两阶段预训练 |
| MCPredictor | `a3245516…` | ❌ 需 **LDC2011T07 Gigaword**（许可）+ python2.7 预处理链 | ❌ → **(b)** | 与 EasyECR 的 KBP 2017 同类 |

**已验证的评分轴**：SimKGC 的 `metrics.json` 与原文 Table 3 逐项吻合（WN18RR 66.6/58.7/71.7/80.0，
FB15k-237 33.6/24.9/36.2/51.1），且我们独立重算其 Hit@1 在四个文件上逐位相同。

### 6.3 不可入表

- **MCNC 五选一方法**（PMI/Bigram、Event-Comp、PairLSTM、SGNN、SAM-Net、HeterEvent、GraphBERT
  的原始设定）：多选准确率与「候选列表排序」口径不同，只能作背景引用，不得同表比较；
- 代码或协议不可核实者：DocScript、Relational Transformer、CEEG、Pred-ID、TimeEchain/MPF
  ——进可得性表。

### 6.4 另加对照

random / frequency（平凡对照）；`no_graph` / `rewired`（图依赖正控，**已通过**：
gold .1802 / rewired .1185 / no_graph .0811，见 `results/PHASE_E.md`）。

## 5. 主结果表的目标形态

```
| 方法                          | 指标… |
| 公开方法 A[ref]                |       |   ← (a) 或 (b)，(b) 加「透明适配」标注
| 公开方法 B[ref]                |       |
| 公开方法 C[ref]                |       |
| LLM 对照（Qwen3-8B LoRA）       |       |   ← 自建对照
| 本文前期方法（failed 身份标明）    |       |   ← 徐昇 ch4/ch5 先例：自家上一章方法入表
| **本文最终方案**                |       |   ← 末行
```

外部公开方法**不少于 3 个**（徐昇全篇即 3 个，第四/五章各 1 个；李璐 ECB+ 章 7 个；钱子杰 9 个）。
跑不了的**必须**进可得性表并写明具体障碍，不得静默省略。
