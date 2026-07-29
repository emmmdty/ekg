# EKG 项目总纲（SPEC）

> **单一权威的开发驱动文档。** 讲清「做什么、怎么组织、当前机制、定位约束、实验设计」。
> 动态内容分流：**当前在做/待办/止损条件** 见 [`TODO.md`](TODO.md)；**工程坑** 见
> [`ENGINEERING_NOTES.md`](ENGINEERING_NOTES.md)；**服务器运维** 见 [`GPU_RUNBOOK.md`](GPU_RUNBOOK.md)；
> **三端协作流水线** 见 [`PIPELINE.md`](PIPELINE.md)；
> **baseline/消融/评测协议** 见 [`EXPERIMENTS.md`](EXPERIMENTS.md)；**数据与切分** 见
> [`DATASETS.md`](DATASETS.md)。历史设计/交接稿正文已移出仓库，索引见
> [`ARCHIVE_INDEX.md`](ARCHIVE_INDEX.md)（勿作依据）。

## 1. 主线与任务（v4 · 2026-07-21 重设）

课题主线 = **可信事件图谱的自动化构建与下游可靠应用**。学位论文 **4 章脊柱 = 可信度四维**
（身份 → 结构 → 事实 → 传播/下游），代码按功能域组织、**名字不含 `ch1/ch2/ch3`**（章节↔代码映射见 §3）。
> 本文件已吸收 2026-07-21 批准计划中的问题、贡献、防审稿定位和执行路线，**取代旧 3 章脊柱**；
> 不依赖仓库外的会话计划文件才能解释当前设计。

| 章 | 可信维度 | 任务 | 主数据（公开 gold） | 代码域 |
|---|---|---|---|---|
| Ch1 | 身份可信 | 证据+不确定性的规范事件节点（带论元） | MAVEN 检测 + MAVEN-Arg + ERE-coref | `ekg.core`(schema/eval) + 新建规范化 |
| Ch2 | 结构可信 | 风险受控全局一致多关系边 + 可追溯修复 | MAVEN-ERE | `ekg.relations` |
| Ch3 | 事实可信 | **构建图上**事实性检测 + 事实性驱动图净化 | MAVEN-FACT | 新建 factuality + `core/calibration` |
| **Ch4** | **传播可信/可用（headline）** | **构建误差向下游的传播、归因与预算 + 可靠后继预测**（修复降为**被测量的干预**） | CGEP-MAVEN / ESC，基座 SeDGPL | `ekg.succession` + `agents` |

**全篇统一创新（headline = Ch4）** = **面向下游的构建误差传播、归因与预算**：每阶段量化校准不确定性 →
union bound + 可达性合成端到端误差预算（`core/calibration/propagation.py`）→ 在 **gold / predicted /
repaired 三图**上把下游后继预测的损失**分解并归因到具体的构建与修复动作**。
**CS-CRP / conformal（§4.3）由头条降级为 Ch4 的可靠性模块。**

> ⚠️ **2026-07-29 重定位（依据是实测，不是设想）**：原 headline 是「下游门控闭环修复」，即
> 「修复控制器**仅在下游后继预测改善时接受编辑**」。**该主张已被自己的实验否定，故降级**：
> ① Phase B 真实图上修复使 ECG 可重建率**微降**（R1 .7310→.7294、R2 f1 .0622→.0620）；
> ② 2026-07-28 归因实验进一步定位——1.5 万次修复编辑中约 **1.4 万次（temporal 相关）对下游按构造零影响**
> （ECG 重建只读 causal+subevent 拓扑，与 temporal 闭包正交），真正动下游的只有 causal 环破除的 858 条边，
> 代价是 R1 掉 3/1260（**0.24%**）、收益 R2 tp +1；**不破 causal 环时下游与 raw 逐位相同**。
> ⇒ **门控能挽回的天花板已被测出 ≈ 0.24%**，撑不起 headline；且 R2 f1 绝对值仅 .078，
> 下游天花板由 **Ch2 抽取器质量**决定而非由修复决定。
> ⇒ 同时「仅在下游改善时接受编辑」的**一般命题已被 Kintsugi(2605.09487) 等占先**（见 §5）。
> **修复仍然保留**（它是 Ch2 的交付物，且能把 causal SCC 661→0），但在 Ch4 里的身份从
> 「headline 方法」变为**「被精确测量、可归因的干预」**——这恰是新 headline 的实证内容。
> **不得在 E 中换指标把该负结果重新包装成正面主张。**

贯穿属性 = **evidence-grounded / verifiable**：节点挂 evidence provenance、边带 repair trace、预测带
`evidence_chain`。验证器跨阶段「货币」三身份：**门控 · 奖励 · 风险控制器（带有限样本保证）**。

> ⚠️ 旧「实体中心中文金融事件图谱 + TKG 外推」（re_gcn/path_rl/hybrid）**已从主干移除**（见 git tag
> `frozen-tkg-line`，消融时从 tag 取）；Astock 与 entity-mode 是已证死路。**金融应用层
> （Phase G / SARGE）已于 2026-07-27 整体移出主干**——v4 四章无一依赖，结果快照的取回路径见
> [`ARCHIVE_INDEX.md`](ARCHIVE_INDEX.md)。
> ⚠️ 数据看**公开可下载性**：MAVEN 四件套（检测/Arg/ERE/FACT）全 THU-KEG 公开 gold、同 4480 文档、
> test 隐藏走 CodaLab；截至 2026-07-22，MAVEN-ERE / Arg / FACT 的公开 train/valid 已在 WSL 与 4090
> 就位。扩展数据的 raw/processed 边界以 `DATASET_SURVEY.md` 为准。

## 2. 架构不变量（升级=加实现，不返工）

三条机制保证「把某阶段从 baseline 升到 full method 只是**加一个实现**」：

1. **冻结的跨阶段契约**（`ekg.core.schema`）：v4 主链类型
   `EventNode → RelationEdge / EventGraph → CgepInstance → Prediction`；`TemporalQuad / ForecastQuery`
   仅为旧 TKG 兼容类型，不再驱动主线。
   规则：**只加可选字段，绝不复用/改义既有字段**。`EventNode` schema 零新增字段（扩展走
   `metadata`）；`CgepNode` 是 succession 自己的类型、可加字段。
2. **插件式 registry**（`ekg.core.registry`）：可换组件各自注册，config 按名选择。加方法 =
   `@registry.register("name")` + 写实现，pipeline/config schema/调用方零改动。
3. **CPU/GPU 惰性分层**：`core` + 启发式 baseline 无 torch，可在纯 CPU 机导入整包；神经代码
   （LLM/PyG/SeDGPL）**lazy import torch**，只有实例化才需 `llm`/`gnn` extra。故本地
   `uv run pytest` / `ekg-smoke` 全绿，GPU 路径在服务器跑。GPU 组件必须配 CPU 缓存回放。

**不可违反的纪律**：包/函数名不得含 `ch1/2/3`；新组件走 registry + lazy import；报告结果如实
（数字降就说降；观察失败如 ssh/工具，不得伪装成被观察对象的结论）。不可改的测试锁见
`tests/core/test_propagation.py`。

## 3. 代码地图（chapters ↔ code）

```
src/ekg/
├── core/          冻结契约: schema, io, graph, registry, config,
│                  calibration/(split·aci·weighted·crc·propagation), eval/(faithfulness·指标)
├── succession/    ★Ch4 CGEP 后继事件预测(SeDGPL 基座 + selective/structure/cross_stage)
│   ├── data/cgep.py     从 MAVEN-ERE 重建 CGEP 实例(ECG 抽取/anchor 选取/候选采样)
│   ├── data/esc.py      官方 ESCSubWoRe.npy 白名单 Unpickler + topic 交叉验证切分
│   ├── linearize.py     DsGL 图线性化 + EventVocabulary(<a_i> token) + 距离选边
│   ├── metrics.py       MRR/Hit@k, 乐观(SeDGPL)+strict 两套 tie-break
│   ├── predictor.py     SuccessorPredictor ABC + registry + random/frequency + UnscorableInstance
│   ├── model.py         EeCE 两级门控 + ScEP 对比头(torch 守卫, CPU 可导入)
│   ├── encode.py        批编码(保「第 i 个事件 token ↔ 第 i 个句子」不变量)
│   ├── structure.py     reach_anchor 结构特征(zero-init embedding + 门控残差)
│   ├── selective.py     推理侧选择性 conformal 头(risk-coverage 曲线)
│   ├── cross_stage.py   受控 reachability 扫描(CS-CRP 组合)
│   ├── reconstruction.py  ECG 可重建率 R1(query 边可达)/R2(query 边保真)
│   └── sedgpl.py        SeDGPLPredictor: linearize→encode→model, 纳入统一 evaluate
├── relations/     Ch2 关系抽取+图构建: data/·pairs.py(文档级候选与标签口径)·
│                  extractor/(heuristic·llm·supervised 判别式对分类)·grounding/·
│                  consistency/(全局一致解码 + RepairTrace)·admission.py(CRC 边准入 + 分层 FNR)·
│                  rl/(GRPO-RLVR)·agents/·pipeline
├── agents/        多智能体基底: Agent/Blackboard/Stage/Orchestrator/Verifier(阶段无关)
├── rl/            RL 基底(阶段无关): 组合奖励·组相对优势·势塑形·课程
└── cli.py         ekg-smoke 入口(CPU 端到端冒烟)
scripts/           功能命名 CLI: build_cgep·evaluate_cgep·profile_cgep_step / evaluate_* / train_*
configs/relations/   YAML 实验配置
tests/{core,succession,relations,agents,rl,scripts}/   单测 + CPU 冒烟
```

## 4. Ch4 已有基线与可靠性模块（CGEP）

### 4.1 基座 SeDGPL（自跑基线）
监督式 prompt learning，三组件：**DsGL**（距离敏感图线性化，按存储顺序取前 20 条边，最短路距离
只用于排序幸存边）+ **EeCE**（事件富集因果编码，两级门控）+ **ScEP**（语义对比事件预测头）。
CGEP 只消费 (事件类型, 触发词, 所在句子)，**不用论元**。词表 **transductive**（覆盖 train+test 的
`<a_i>` token 清单，与 SeDGPL 的 `to_add.json` 一致，只 token 清单跨切分、无标签/图/梯度泄漏）。

### 4.2 我们的三个机制（加在已完成的自跑 SeDGPL 基线之上；状态见 TODO.md）
**M1/M2/M3a 与 M3b 受控扫描均已实现并完成单折实验；真实构建图上的 M3b 仍被 Ch2 抽取召回卡住。**
这些结果是 Ch4 的先行可靠性证据，不等于 v4 的三图误差分解已经完成。
⚠️ 注意 M1 与 M2 的 A/B 都落在**噪声级**（ΔMRR ≈ ±0.002），与 §1 记的修复归因结果一致 ——
**在 SeDGPL 这个下游上，图侧的干预普遍只有噪声级效应**。这本身是新 headline 要解释的现象之一，
不要反复用新机制去撞同一堵墙。代码：
- **M1 风险感知线性化**（✅ CPU + 测试 + GPU A/B）：`linearize.select_nearest_edges` 按**全图 BFS
  距离**保留离 query 最近的 budget 条边，替换 SeDGPL「按存储序取前 20」的任意切片。registry
  `edge_selectors`（`sedgpl` 默认 / `distance`）+ `evaluate_cgep.py --edge-selector` flag，**默认关闭**
  保基线逐字节一致（测试锁全绿）。**发力面实测 = 22.83% 实例触发预算**（触发时平均丢 17 条）。
  定位：gold ECG 无 confidence → 主表用**距离（structure-aware）**；admission 打分留给构建版 ECG / CS-CRP。
- **M2 结构感知编码**（✅ CPU + 测试 + GPU A/B；**噪声级、入消融**）：EeCE 加第四路 = 每事件 token 的
  **`reach_anchor` bit**（是否经有向因果边可达 anchor＝是否为预测的上游证据），经 **zero-init `nn.Embedding(2,768)`
  + 门控残差** `h3=h2+g·struct` 融入（`succession/structure.py` + `model.py`）。默认关、baseline 逐字节一致。
  **信号收敛依据**（真实数据 CPU 预筛）：结构解释真实 SeDGPL 难度的 5 折 CV R² **≤5%**、`reach_anchor` 是**唯一**带
  出样本信号的 per-token 特征（加度/proximity 出样本 R² 反降）→ 从 4 维收为 1 bit。**GPU A/B（单折 10ep）**：
  ON MRR 0.1852/0.1290 vs OFF 0.1867/0.1281 = **持平**（ΔMRR −0.0015 乐观 / +0.0009 strict、hits@10 +0.010）→
  与 M1 同类，噪声级、如实入消融附录。⚠️初版「插值门 + 默认 `nn.Embedding`」曾 MRR 腰斩（0.088）：默认 N(0,1)
  embedding 范数 ~28 碾压 `h2` ~8，init 扰动事件表示 185%、lr=1e-6 救不回；根因修复＝no-op 起步（诊断见 ENGINEERING_NOTES）。
- **M3 = CS-CRP 选择性头**（✅ M3a + GPU 曲线；✅ M3b 受控扫描；真实构建图待 Phase A/B）：`succession/selective.py`
  把预测器候选分数经 `core/calibration` 桥成 conformal 预测集，产 **risk-coverage 曲线 + 覆盖保证**（gold
  ECG `reachable` 全 True → 退化为推理侧选择性预测器）。跨阶段 reachability 预算（§4.3）由 M3b
  受控扫描验证；真实 predicted/repaired ECG 留给 Phase A/B/E。机制见 §4.3。

### 4.3 CS-CRP（跨阶段漂移鲁棒 conformal 风险传播）——Ch4 可靠性模块
代码 `core/calibration/propagation.py`。把两个**异质**保证在单一预算 α_total=α_e+α_p 下组合成
端到端选择性预测器：
1. **构建阶段**：CRC 边准入，**召回**保证 FNR≤α_e（`relations/admission.py`，Angelopoulos CRC）。
2. **推理阶段**：**漂移自适应覆盖**保证 miss≤α_p（`core/calibration` 的 ACI/weighted 流式校准器）。
3. **关键**：边准入**移除候选** → 丢金标边使答案**不可达**（推理校准器看不到的 miss）。为此单列
   reachability 预算，union bound：P(miss) ≤ P(unreachable)+P(reason miss|reachable) ≤ α_e+α_p。
4. **条件回收**（`allocate_budget_conditional`）：用 held-out 准入结果证不可达率上界 u
   （Clopper-Pearson，CRC 界收紧），推理侧跑修正水平 **α_p'=(α_total−u)/(1−u)**，收紧预测集。
5. 推理侧**非可交换**（漂移自适应），区别于可交换 pipeline-CP。

**实现状态**：通用原语已实现并测试（`core/calibration` 的 aci/weighted/crc/propagation + `relations/admission`
的 CRC 边准入；`propagation.py::compare_cross_stage_methods` 是其头号实验）。**M3a（推理侧选择性头）已接入
CGEP**（`succession/selective.py`：候选分数→gold 排名→`run_cross_stage`，产 risk-coverage 曲线 + 覆盖保证）。
**SeDGPL 主表曲线已跑**（GPU，954/954）：覆盖保证成立（aci 每档 ≥1−α），**同覆盖下集大小 SeDGPL≪frequency**
（90%覆盖 243 vs 425/−43%、70% 99 vs 313/−68%）——强 ranker 价值=覆盖保证下的集收缩、不依赖 MRR。
**M3b（跨阶段 reachability）：真实构建版 ECG 曾被 Ch2 生成式抽取器堵死**——SFT+GRPO LoRA causal 召回
**0.4%（3/810）、subevent 0%（0/139）**，构建版 ECG 退化（reachability 损失 ~1.0，非可扫描范围）。
**Phase A（2026-07-24）已用判别式抽取器解此瓶颈**（causal 召回 67.5%、F1 .250 / subevent .213，`hallucinated=0`；
见 EXPERIMENTS §Ch2），真实 predicted ECG 的 reachability 待 Phase B/E 接入。故 M3b 此前落为
**受控 reachability 扫描**（`succession/cross_stage.py` + `scripts/evaluate_cgep_cross_stage.py`）：真 SeDGPL 推理排名 +
受控 reachability 损失。**真 SeDGPL 排名实证**（954，α_total=0.2）：naive 覆盖崩(0.80→0.56)、集恒~140（忽略剪枝）；
cs_crp 守覆盖到预留档(loss≤0.1)、集恒~270；**cs_cond 同覆盖下自适应更紧集**(loss=0: 152 vs 272，−44%)——原语的
"tighter sets"兑现。离散排名+无漂移下 cs_cond 覆盖在 loss=0.15/0.20 微欠 target。抽取器 0.4% 作诚实数据点；
强抽取器诱导真实损失待 Phase A/B 完成后补齐。**这是继 M1(MRR 噪声级) 后第二个经验墙 → 价值靠方法讲干净、非端到端数字。**

### 4.4 验证器即奖励（RL-reward，**降级为机制之一/消融**）
`ekg/rl` + `relations/rl`（GRPO-RLVR：format+grounding+consistency+F1）。path RL（旧 TKG 线）已随
主干移除（tag `frozen-tkg-line`）。**定位收缩**：新颖性复核表明「结构作 RLVR 奖励」是红海（见 §5），故 RL-reward
不作头条卖点，仅作机制/消融。历史全设计（`RL_DESIGN.md`）已移出仓库，取回见
[`ARCHIVE_INDEX.md`](ARCHIVE_INDEX.md)。

### 4.5 下游门控的信号来源（方法论约束，防 oracle 陷阱）
**适用范围（2026-07-29 收窄）**：门控已不是 Ch4 的 headline（见 §1），但只要论文里**出现任何**
「按下游信号接受/拒绝编辑」的实验档，本约束就适用，且**已从待办升级为发表阻断项**。

self-correction 的收益常来自 **oracle label**（Huang et al. 2310.01798：intrinsic self-correction 掉点、
收益多源于金标）；TACL 自纠综述（2406.01297）把 **oracle 信号泄漏**列为致命实验设计缺陷。故门控信号
来源**必须二选一**并在论文写清：**(a) 在线可得的无标签代理**（自一致性/校准置信/约束满足度，部署可算）；
或 **(b) 显式定位为「离线诊断/构建期质检工具」**（用 held-out 金标算 MRR delta，交付前一次性修图，
不声称在线自愈）。**⛔ 不得用金标 MRR 直接当门控信号而不作 (b) 定位。**
DeepRefine（2605.10488）的 Gain-Beyond-Draft 无金标奖励即为绕开 oracle 的先例（见 §5）。

⚠️ 同一 checklist 的另外两条也适用于 Ch4 的实验表：**不得与人为削弱的初始图比**（初始构建必须用上
修复档能用的全部资源）；**必须有强对照**——修复类干预要与「随机等量删边」比（随机删边本身是强基线，
DropEdge ICLR'20），净化类干预要与**度数匹配**的随机剔除比（均匀随机对低度数策略不公平，
实测差 3,573 条边）。Ch3 的净化负结果正是靠后者才站得住（见 `TODO.md`）。

## 5. 新颖性定位约束（硬约束，投稿安全）

复核证据底稿（`NOVELTY_A1_2026-07-11.md` / `NOVELTY_CSCRP_2026-07-11.md`）已移出仓库；
**投稿前重扫新颖性时须按 [`ARCHIVE_INDEX.md`](ARCHIVE_INDEX.md) 取回**。

> **v4 重定位（2026-07-21 立，2026-07-29 按实测修订）**：全篇创新是**组合式 + 系统集成 + 窄 delta**，
> headline = **Ch4 构建误差向下游的传播、归因与预算**（非单个颠覆算法）。逐章防审稿
> = 最近邻 / 精确 delta / 质疑→反驳：Ch1 下游可消费校准置信 + 难例判别；Ch2 风险目标是**下游可达性损失**
> 而非泛化 FNR（**改名避 SCRC 2512.12844**）；Ch3 novelty = **预测图鲁棒性**（净化的下游主张见下）；
> Ch4 = **三图（gold/predicted/repaired）误差分解 + 把下游损失归因到具体构建/修复动作**
> （区分 CFEP/self-healing KG）。
> ⚠️ **两处主张已按实测收回，写作时不得复活**：
> ① Ch4 **不再主张「下游目标门控接受能治 self-refine 掉点」**——门控天花板实测 ≈0.24%，
> 且一般命题被 Kintsugi/DeepRefine/CauScientist 占先；
> ② Ch3 **不再主张「净化下游」**——净化在结构一致性上**不如度数匹配的随机剔除**（6 项中 5 项），
> 下游那一半若 Phase E 也无增益，则按止损口径退为「事实性检测 + 预测图鲁棒性分析」。
> **两条负结果都要正面写进论文**，它们是「一致性指标与『该删什么』不对齐」这一发现的证据。
> 权威缺口引用用**事件领域文献**（EKG 综述 2112.15280 / EE 综述 2512.19537 / MAVEN-FACT），不靠通用 LLM-KG 综述。
> 下列 A1/CS-CRP 结论仍成立（作 Ch4 可靠性模块的护栏）：

- **A1（RLVR 奖励）**：❌ **不得写「首次把结构/事理当 RLVR 奖励」**。MedCEG(2512.13510) 直接先例
  （gold 推理图路径作可验证奖励），另 Structure-R1/GraphThinker/K2V。VeriGate(2605.30451)/
  Faithful GRPO(2604.08476) 已排除不抢先。注：2409.17480=SeDGPL 本体（监督、无 RL），是 base 非竞品。
- **CS-CRP**：一般命题「cross-stage/selective conformal（甚至 under drift）」也非新（C-RAG 2402.03181/
  PASC 2605.18812/SCRC 2512.12844/CASCADE 2605.20468）；但**具体组合**（召回⊗漂移自适应覆盖 +
  上游剪枝致不可达的 reachability 预算 + 条件回收）**未见先例**——**比 RL 线干净**，作为 Ch4
  可靠性模块的窄 delta，不再单独充当章节 headline。
  相关工作须逐条区分上述四篇；**reachability 预算**是最硬差异点。
- **DeepRefine（2605.10488，2026-05）★最近威胁，前次复核未覆盖**：下游导向的 agent-compiled KB 精化，用无金标
  **Gain-Beyond-Draft 奖励**端到端 RL，报「downstream gains」——与 Ch4「下游导向修图」高度重叠。**故 headline
  claim 收窄**：不主张「首次做下游导向图修复」，只主张 **事件因果图上、带 reachability 与 conformal 误差预算
  （覆盖保证）的下游门控修复 + gold/predicted/repaired 三图误差分解**。DeepRefine 是通用 KB、RL 无覆盖保证、
  无 reachability/三图分解——逐点区分。门控信号来源须按 §4.5 交代。投稿前重扫一次同类新论文（此域 2026 增长快）。
- **Kintsugi（2605.09487，2026-05-10）★★2026-07-28 联网复核新发现，此前完全未覆盖**：
  「确定性验证门**仅当**候选通过类型检查、KB 可执行、且聚焦验证成功率或轨迹健康度**改善而不违反
  保护性回归检查**时才接受编辑」——这是 Ch4「下游门控接受」的**直接先例**，且带形式化接受规则。
  ⇒ **「只在下游改善时才接受修改」这个一般命题已被占，不得主张为新**。
  可区分处：Kintsugi 在**可执行 KB / agent 策略**域（下游是 agent 任务成功率与轨迹健康度），
  非事件因果图；无 conformal 覆盖保证，无 reachability 预算，无 gold/predicted/repaired 三图分解。
  另 **CauScientist（2601.13614）** 也是「仅当 BIC 提升才接受编辑 + 记录被拒编辑」的同类接受规则。
  连同 DeepRefine，**下游导向修复这一族已相当拥挤**，Ch4 的 delta 只能落在
  「事件因果图 + 覆盖保证 + reachability 预算 + 三图误差分解」，且须逐篇区分。
- **支持我们立场的两条**（2026-07-28 查到，写作时引用）：**KGrEaT（CIKM'23, 2308.10537）** 明确指出
  KG 精化研究「以下游会提升为动机，但**这几乎从不被评估**」，且实测 KG 效用因任务剧烈变化、
  更全的 KG 未必更好 —— 我们做了这步评估并拿到否定答案，属于填该缺口；
  **TACL 自纠综述（2406.01297）** 结论「无可靠外部反馈的自我修复不改善甚至掉点，有可靠外部反馈才有效」，
  与 Phase B（无门控修复掉点）一致 —— 但其 checklist 同时把 **oracle 信号泄漏**列为致命设计缺陷，
  故 §4.5 的「门控信号来源」**从待办升级为发表阻断项**：不得用金标 MRR 当门控信号。
- ⚠️ **CS-CRP 与 SCRC(2512.12844) 撞名**，建议改名（突出 reachability-budgeted/recall-coverage 组合），
  待定；改名涉及 docs/代码多处，须统一。
- 置信度：结构作 RLVR 奖励非新=HIGH；CS-CRP 具体组合未占=MEDIUM（投稿前须做一次穷尽 pipeline-CP 扫）。
- 口径：不 claim 全球首创；一律「据我们所知」+显式区分先例。**专利已归档、不再安排专利写作。**

## 6. 数据与切分（要点，详见 DATASETS.md / ENGINEERING_NOTES.md）

- **CGEP-MAVEN 重建口径**（`succession/data/cgep.py` 权威）：ECG = 文档内 **causal(CAUSE+PRECONDITION)
  +subevent** 无向连通分量、**节点≥4**；时序 BEFORE **不进拓扑**（只作 M2 结构特征）；查询边 =
  **出度 0 且入度 1**；候选 512、同 split 均匀采样。验收：2994 文档 / 8.82 节点·ECG / 13.21 边·ECG。
- **ESC 必须 topic 交叉验证**（EventStoryLine topic）；**文档级切分会泄漏**（同 topic 同一故事）。
  实测：SeDGPL 公开的 **ESC 19.6 依赖切分泄漏**（topic-CV 0.0599 vs doc-split 0.1802≈复现 0.196）。
- **MAVEN 版数据未发布**（SeDGPL 只发 ESCSubWoRe.npy）→ 论文 CGEP-MAVEN 27.9 **不可比**；主表**必须以
  我们自跑的 SeDGPL 为基线**，公开数字标「原论文数据构建，非同数据可比」。
- ICEWS14/FinDKG 仅作冻结旧 TKG 线的兼容数据；若从 tag 复现实验，ICEWS 必须用 timestamps 计数切分，
  不得把旧结果混入 v4 主表。

## 7. 实验设计

> **完整 baseline 矩阵（新老搭配）+ 消融矩阵 + 评测协议见 [`EXPERIMENTS.md`](EXPERIMENTS.md)。** 要点：
> 每章 = 主表(vs baseline) + 消融表(每环节 ±) + 多种子；baseline 覆盖**经典/原文 + 近 1–2 年代表 + 通用 LLM**；
> test 无金标按 EXPERIMENTS §1 三档（Ch1/2 走 CodaLab、Ch4 valid 当 test 有 SeDGPL 先例、Ch3 valid 报数）。

- **主表基线**：自跑 SeDGPL 在 CGEP-MAVEN（Phase 2，单折 10ep ≈ 2.5h）。M1/M2/M3 都挂它上。
- **协议**：ESC 报 **topic 交叉验证**（`--split-mode document` 只作「论文数字来源解释」，绝不当协议）；
  tie-break 同报 `mrr`（乐观/SeDGPL）与 `mrr_strict`。
- **既有受控实验**：真实构建版 ECG 此前被 Ch2 生成式抽取器堵死（causal 召回 0.4%），故先做**受控
  reachability 扫描**（真 SeDGPL 排名 + 受控损失，`cross_stage.py`）。**Phase A 判别式抽取器已解召回瓶颈
  （causal F1 .250），可产真实 predicted ECG**；v4 Phase E 必须在 Phase B 后补 gold/predicted/repaired
  三图闭环，受控扫描不能替代真实图结果。
- **旧 TKG 线**：re_gcn/hybrid/path_rl **已移出主干**（git tag `frozen-tkg-line`），不在当前测试/CI。
- **多种子最后**：seeds 13/17/42，报 mean±std。

## 8. 复现（本地 CPU 冒烟；GPU 训练在服务器）

```bash
uv sync --extra dev && uv run pytest && uv run ruff check src tests scripts   # 本地：契约/评测/冒烟全绿
uv run python scripts/build_cgep.py --split train+valid --report-stats         # CGEP 重建验收
# 服务器 CGEP 训练(screen/nohup; ⛔ 用 .venv/bin/python, 不要 uv run — 见 GPU_RUNBOOK §0):
#   CUDA_VISIBLE_DEVICES=<空卡> HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
#   .venv/bin/python -u scripts/evaluate_cgep.py --dataset maven --predictor sedgpl \
#     --model-path <roberta-base> --epochs 10 --output runs/cgep/maven_sedgpl.json
```
