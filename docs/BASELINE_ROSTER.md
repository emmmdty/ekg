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
| 3 | LLMERE-causal（COLING 2025） | MAVEN-ERE official valid 710 篇，自写评测器，causal 36.04 | ⚠️ 有数据构造/评测器/**已发布预测**，无 trainer | 见 §2.1 | **本轮生成失败**（退化重复） |
| 4 | A3.6 fallback | — | 本文 | **不适用**：本文前期方法，`failed` 身份须在表头标明 | 已有 |
| 5 | LLM 对照（Qwen3-8B 等） | — | 自建 | **不适用** | 待建 |

**不可运行，进可得性表**：RESIJ、KnowQA、2025 two-stage ERE、MAQInstruct（口径可引用但无同协议复现）。

### 2.1 LLMERE 的保真度路径存在一处与既有裁决的冲突，须作者裁定

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
  再以同一份代码转到我们的 MAVEN 重建协议。**这条路要先验证 ESC 重建是否可行**。
  ⚠️ 已知坑：我们此前实测 ESC 的 19.6 依赖切分泄漏（topic-CV 0.0599 vs doc-split 0.1802），
  重建时必须先确认原文用的是哪种切分，否则复现出来的「一致」是假的。

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
