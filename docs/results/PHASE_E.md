# Phase E 实测档案 · Ch4 构建误差的传播、归因与预算

> 本文件是 **Phase E 的实测档案**：当时跑出的真实数字、口径、踩过的坑。
> 实时状态见 [`../TODO.md`](../TODO.md)，阶段契约见 [`../phases/`](../phases/README.md)。
> **数字以本文件为准**：TODO 与 EXPERIMENTS 只引用、不复制。

### Phase E 实施（2026-07-29，4090 card 2，**三图归因完成 / 图侧干预全部噪声级**）

代码（只增不改）：`succession/graph_context.py`（三图接入点）、`succession/perturbation.py`
（4 类受控构建误差 + 1 个结构零）、`scripts/evaluate_cgep_propagation.py`（一次训练多图打分 +
`--structural-only` CPU 通道）、`scripts/report_ch4_budget.py`、`scripts/report_ch4_contrasts.py`。
配套：`cgep.topology_triples` / `reconstruction.corpus_reconstruction` /
`purification.degree_matched_samples` / `predictor.rank_instances` 提为公开单一事实源；
`SeDGPL.set_edge_selector` / `save` / `load`；`evaluate_factuality --predicted-edges` / `--dump-labels`。
本地 **373 passed / 12 skipped**（基线 352/12）、ruff 0、`ekg-smoke` OK。

**★ 接入点设计与自检**（交接 §4 的方案 3）：query / candidates / label / 节点框架全部固定来自 gold，
只替换喂给模型的 template 边。两条不变量都是**从 gold 继承**而非新发明：① 答案绝不进 prompt
（gold 查询边 tail 出度 0 入度 1，构建图无此保证，故凡触及金标后继的边一律剔除并计数）；
② 节点框架为 gold，故 `<a_i>` 词表 / 句编码 / 候选集跨三图逐位相同。
**自检：gold 进 gold 出，1908/1908 实例逐位相同** ⇒ `gold` 档就是已发表基线本身，不是重新推导。

**★ 先钉死一个会毁掉整个归因的混淆：边序**。SeDGPL 按**存储序**截断前 20 条，于是同一张图
重新序列化就能改数。实测 `repaired_nobreak` 与 `predicted` 的模板边**集** 94/94 完全相同，
存储序却只有 36/94 相同。全量 1908 上的后果（`--template-order source` 档）：

| 对照（source 序） | Δ MRR | 95% CI | p |
|---|---|---|---|
| repaired − repaired_nobreak | **+0.0048** | [+0.0007, +0.0089] | **0.020** |
| repaired_nobreak − predicted（**边集完全相同**） | −0.0022 | [−0.0064, +0.0018] | 0.274 |

⇒ 纯重新序列化就能造出一个 p=0.02 的"效应"。改 canonical 序后 `repaired_nobreak` 与 `predicted`
**逐位相同**（Phase B「不破 causal 环则下游不动」的预测被确认），修复的表观收益从 +0.0026 回落到
+0.0011。**主表一律用 canonical 序**；source 序只用于锚定已发表基线。

**主结果**（valid 全量 710 篇 / **1908 实例**，一次 SeDGPL 训练 10ep 7912s，25 档 × 2 selector 打分；
`n_unscorable=1`，与 2026-07-11 基线一致）：

| 档 | MRR | Δ vs gold | R1 可达率 | 模板边/实例 |
|---|---|---|---|---|
| **gold** | **.1802** | — | 1.0000 | 15.9 |
| **predicted** | **.1583** | **−.0218** | .7018 | 24.0 |
| **repaired** | **.1595** | −.0207 | .7002 | 23.2 |
| repaired_noclose（不补闭包） | .1595 | −.0207 | .7002 | 23.2 |
| repaired_nobreak（不破 causal 环） | .1583 | −.0218 | .7018 | 24.0 |
| random_drop_matched（等量随机删 1,209 causal 边） | .1584 | −.0218 | .6824 | 23.2 |

**归因（配对 bootstrap，10,000 次重采样；同一模型答同一批 1908 题，故成对）**：

| 对照 | Δ MRR | 95% CI | p | 占构建损失 |
|---|---|---|---|---|
| gold − predicted（**构建损失**） | **+0.0218** | [+0.0109, +0.0327] | **0.000** | 100% |
| repaired − predicted | +0.0011 | [−0.0017, +0.0041] | 0.456 | +5.1% |
| repaired_nobreak − predicted | **+0.0000** | [0, 0] | — | 0%（逐位相同） |
| repaired_noclose − predicted | +0.0011 | 同 repaired | 0.456 | +5.1% |
| repaired − random_drop_matched（**强对照**） | +0.0011 | [−0.0028, +0.0051] | 0.595 | — |
| random_drop_matched − predicted | +0.0000 | [−0.0029, +0.0029] | 0.987 | +0.2% |

- **构建损失是唯一确凿的效应**：−0.0218 MRR（相对 −12.1%），CI 远离 0。
- **修复的全部效果 = causal 破环**：补闭包与其余 temporal 动作**按构造零影响**（`repaired_nobreak`
  与 `predicted` 逐位相同）。破环值 **+0.0011 = 构建损失的 5.1%**，且**与 0 不可分**（p=0.46），
  与等量随机删边**也不可分**（p=0.60）。⇒ 交接文档估的「门控天花板 ≈0.24%」量级正确，
  这里给出了 MRR 上的版本。
- **结构侧修复对上强对照是赢的**（`runs/cgep/ch4_structural.json`）：同样删 1,209 条 causal 边，
  修复把 937 个 causal SCC 清零、R1 .7002 / R2 f1 .0770；随机删只清掉 55 个环、R1 .6824 / R2 .0749。
  **修复的价值不是「比不修好」，是同样代价下选得准得多——但这份准确性换不来下游。**

**净化的下游判定（Goal ②，正面回答：❌ 无增益，且是天花板）**：

| 档 | MRR | Δ vs predicted | 95% CI | p |
|---|---|---|---|---|
| purified（Phase D detector 标签，可部署档） | .1583 | −0.0001 | [−0.0007, +0.0005] | 0.922 |
| purified − 度数匹配对照 | — | +0.0006 | [−0.0020, +0.0036] | 0.655 |
| purified − 均匀随机对照 | — | +0.0005 | [−0.0024, +0.0033] | 0.752 |
| **purified_oracle（gold MAVEN-FACT 标签 = 上界）** | .1583 | **−0.0000** | [−0.0015, +0.0014] | 0.966 |
| purified_oracle − 度数匹配对照 | — | +0.0021 | [−0.0002, +0.0048] | 0.076 |
| purified_oracle − 均匀随机对照 | — | −0.0035 | [−0.0072, +0.0001] | 0.059 |

- **用金标事实性标签也是零**。这不是「检测器还不够好」——**oracle 档就是天花板**，
  ⇒ 没有任何检测器改进能救活这条路。Ch3 按止损口径退为「事实性检测 + 预测图鲁棒性分析」。
- 净化只**略胜**度数匹配对照、**略负于**均匀随机对照，两者 CI 均含 0。均匀对照删掉 2.5 倍的边
  （1,614 vs 639）——它更像「把过密的预测图随机稀释」，不构成对净化的公平比较，故两个都报。
- 标签来源：`evaluate_factuality --predicted-edges`（复用已有 dump）重跑，macro-F1 .4823/.4824、
  8 个标签变，**与 Phase D 逐位复现**。

**受控扰动曲线（Goal ①，在 gold 图上单变量注入，嵌套采样保证曲线量的是幅度而非抽样运气）**：

| 误差类型 | 幅度 .05 | .1 | .25 | .5 | .75 | 1.0 |
|---|---|---|---|---|---|---|
| 删边（召回损失） | — | −.0056 | −.0081 | **−.0240** | **−.0446** | **−.0991** |
| 增边（精度损失） | — | — | −.0047 | **−.0098** | — | **−.0139** |
| 并节点（共指过并） | +.0018 | +.0024 | **−.0092** | — | — | — |
| 拆节点（共指欠并） | −.0040 | **−.0088** | **−.0184** | — | — | — |
| **打乱 temporal** | — | — | — | — | — | **+.0000**（CI [0,0]） |

（粗体 = 配对 bootstrap CI 不含 0。增边的 .5/1.0 列对应 rate .5/1.0。）

- **同幅度下最伤下游的是身份错误，不是关系错误**：rate .25 时拆节点 −.0184，是等幅删边（−.0081）的
  **2.3 倍**、等幅增边（−.0047）的 **3.9 倍**。而拆节点恰恰是**一致性机器完全看不见**的那一类
  （causal SCC = 0、拓扑边数与 gold **完全相同** 12,524）。
- 按**可达性损失归一**后更清楚（ΔMRR / ΔR1）：拆节点 −.0777、真实预测图 −.0731、并节点 −.0400、
  随机删边 −.0305。⇒ **可达性损失单独解释不了伤害**，精度损失与身份损失叠加在其上。
- **打乱 temporal 是结构零**：与 gold **逐位相同**（模板只读 causal+subevent）。这条从 Phase B
  的断言升级为可跑的证据。
- 并节点在低幅度（.05/.1）**略升**（+.0018/+.0024，CI 含 0）——不作正面主张。

**★ 核心论断已量化：一致性指标与可重建性不对齐**（25 个受控档位，`ch4_structural.json`）：
causal_scc vs R1 的 Spearman ρ = **−0.064**，temporal_closure_gap vs R1 ρ = −0.163，
拓扑边数 vs R1 ρ = −0.008；而 **R1 与 R2 之间 ρ = +0.783**（两个可重建视角彼此一致）。
两个干净反例：`split_nodes@0.25` 三项一致性指标全说健康而 R2 从 1.0 崩到 .365；
`add_edges@1` 说有 316 个 causal 环而 R1 是满分 1.0。
（25 档是**设计集不是抽样**，ρ 只作描述用。）

**误差预算（Goal ③，`ch4_budget.json`；CS-CRP 首次吃实测可达性掩码而非合成掩码）**：

- **可行性下限**：composed coverage 不可能超过可达率，故 `predicted` 图上
  **alpha_total < 0.2935 时任何方法都不可能达标**。这是 Phase A 抽取器给整条链路定的端到端风险地板。
- gold 图（无构建损失）上，条件回收档**恰好压在目标上**（α=.1/.2/.3 → .9036/.8040/.7055），
  而固定 50/50 划分**过度覆盖**（.9444/.8920/.8543）—— 一半预算浪费在不存在的可达性损失上。
- ⚠️ **发现一条库级限制并如实并列报告**：`allocate_budget_conditional` 用 `min(CP上界, alpha_edge)`
  收紧不可达率 u，这只在损失由它所约束的**准入**阶段产生时成立。Phase E 的损失来自**抽取**，
  没有 CRC 界覆盖它，于是收紧断言了不成立的上界、recycler 反而欠覆盖
  （α=.3 目标 .70：`cs_crp_cond` .5828 ❌）。去掉收紧的同一 recycler（`cs_crp_measured`）达标 .7065 ✅。
  **合成掩码看不出这一条，吃实测掩码才暴露。**未改库语义，两档并列报。

**预算策略（selector）不是损失的来源**：distance 选边在 gold 上 +0.0009（p=0.62）、在 predicted 上
−0.0008（p=0.63），均不可分于 0；只在**纯过密**的图上显著（`add_edges@1` +0.0063，p=0.003）。
⇒ 构建损失来自**边的内容**，不是 20 条预算的截断策略。

**★ 噪声地板已被两条独立证据测定**：① 配对 bootstrap 的 95% CI 半宽 ≈ **±0.003–0.004** MRR；
② 同配置重训一次，gold 从 2026-07-11 的 **.1836** 变为本次的 **.1807**（source 序，实例集已证逐位相同），
即 **fit 间波动 −0.0029**；同一次 fit 内 canonical 与 source 序只差 **−0.0005**。
⇒ **所有图侧干预（修复 +.0011、净化 −.0000、distance 选边 +.0009）都落在噪声地板之内**，
与 M1/M2 的历史量级一致。**多种子（Phase H）之前不得对任何图侧干预作正面主张。**

产物（均在本地 `runs/cgep/` 与 4090 同名路径）：`ch4_propagation.json` + `_ranks.json`（主表 50 档）、
`ch4_structural.json`（25 档结构侧）、`ch4_purified.json`（可部署净化档）、`ch4_source.json`（锚定档）、
`ch4_budget.json`、`ch4_contrasts*.json`；权重 `ch4_sedgpl.pt`（1.5G，留 4090，`--load-model` 可复用，
实测 load 后 `predicted` 复现 .1583 逐位一致）。

### Ch4 先行模块（来自 v3，降级复用）

- **SeDGPL 自跑基线**：CGEP-MAVEN 单折 MRR 0.1836 / strict 0.1265，n=1908。
- **M1 距离选边**：MRR 0.1889 / strict 0.1304；相对匹配重跑约 +0.002，属于噪声级，留作消融。
- **M2 结构编码**：MRR 0.1852 / strict 0.1290；无可信增益，留作负结果消融。
- **M3a 选择性预测**：ACI 各风险档覆盖达到目标；同覆盖下 SeDGPL 相比 frequency 的集合缩小
  约 43%–68%。
- **M3b 受控扫描**：真实 SeDGPL 排名下，naive coverage 随 reachability loss 下跌；预算方法在预留档
  更稳。它是受控证据，不等于真实 predicted/repaired 图闭环。

---

## ★★ Ch4 图依赖正控：消费者**确实在读图**（2026-08-30，4090 GPU2）

`scripts/evaluate_cgep_propagation.py --load-model runs/cgep/ch4_sedgpl.pt --only-arms gold
no_graph rewired`。**冻结消费者**（Phase E 拟合好的 SeDGPL 权重，不重训、不选任何东西），
同一批 710 篇 / 1,908 个测试实例、同 canonical 模板序、seed 209。
`gold` 复现 Phase E 的 **0.1802**（原表 0.18019），确认权重与词表加载正确。

| 臂 | MRR | Hits@1 | Hits@10 | reach | **Δ MRR vs gold** |
|---|---|---|---|---|---|
| **gold** | **.1802** | .1143 | .3124 | 1.000 | — |
| **rewired**（边数/类型/子类型全同，端点随机重挂） | .1185 | .0666 | .2112 | .031 | **−.0617（−34.2%）** |
| **no_graph**（删光所有边） | .0811 | .0398 | .1473 | .000 | **−.0991（−55.0%）** |

### ★ 正控通过，而且顺序是对的

两条臂都远超本章的 ±.003–.004 噪声地板（差了一到两个数量级）。三者严格有序
`gold > rewired > no_graph`，且 `rewired` 落在中间——**消费者用的是边的正确性，不只是边的存在**：
在边数、类型、子类型完全不变的前提下只打乱端点，就吃掉整张图价值的
**62%**（.0617 / .0991）。一个只会数边的消费者过不了这一关。

### 由此重读本文件此前的全部零结果

Phase E 此前的「修复 / 净化 / oracle 净化全在噪声内」有两个互斥解释，旧表分不开：
干预太小，还是**消费者根本不看图**。正控把后者排除了。

⇒ 那些零结果是**关于那些干预**的，不是关于消费者的。**Ch4 的消费者依赖性主张不必撤回。**

### 它同时给了本章所有效应一把标尺

整张图对下游值 **.0991 MRR**。据此重读已有效应：

| 效应 | ΔMRR | **占整张图价值的比例** |
|---|---|---|
| 构建损失（gold → predicted 图） | −.0218 | **22.0%** |
| 拆节点（身份错误，同幅度里最伤） | −.0184 | 18.6% |
| 结构修复 / 事实性净化 / oracle 净化 | ≈ 0 | ≈ 0% |

「−.0218」原本是个孤立数字，现在是**"构建阶段丢掉了图对下游全部价值的两成"**。
这才是可以写进论文的表述。

### ⚠️ final-valid 访问披露

本次运行在 **710 篇**上，即 v6 协议的 final-valid。这不是新开的口子：Phase E 整张表本就
在这批文档上（`protocol.json` 的 `historical_final_access_disclosed=true`），且本次是
**冻结权重 + 固定三个臂**，**没有选择任何模型、epoch、阈值或结构**。
按 A 类红线「final-valid 封存且不用于选模」，此次访问不构成选模。**在此显式记录。**

## ★ v6.1 · E3.0 冻结 Ch6 的不可变 evaluation unit（C-10，2026-09-13，本地纯 CPU）

### 开工自审（作者 2026-09-13 要求，先答再做）

1. **科研价值**：对准的是 `EXPERIMENT_PLAN.md` §7.4 的**表 6-2**。那张表要把四个外部 CGEP 对手、
   random/frequency 两个平凡对照、以及本文构建图（predicted / gold）**放在同一批 query 上**比较，
   而这些臂之间隔着几周、跨两台机器。unit 不落成带 digest 的文件，就等于每个臂各自
   `build_cgep()` 一次——一旦 query / candidate / label 漂移，先跑的臂全部作废
   （`phases/PHASE_E3_graph_application.md` 的 stop condition 第 1 条，A 类三轴一致性）。
   证据：本文件上方的 `.1802 / .1583 / .1185 / .0811` 全部测在这批 1,908 实例上，冻结让新对手的
   数字**能和这几行并表**。理由不是「成本低」——它是 G-11a（四个对手复现，按 §3.1 基准率 3–4 周）
   的真正前置。
2. **可行性**：纯 CPU、**2.6 秒**、无授权项。源数据本地就有
   （`data/processed/maven_ere/valid.jsonl`），生成器在仓库内，`build_cgep` 给定文档序与 seed
   即确定。数据 / 协议 / 代码 / 算力 / 授权五条**没有一条不成立**。

### 冻结产物

`runs/stages/E3/e3-v61-20260913/`（`runs/` 是 gitignored，产物走 scp）：

| 项 | 值 |
|---|---|
| `queries.jsonl` SHA-256 | `e92629bd84677e88549e6fbeeaf2e21afb0a8e050722bede45c19ccfa4b5aecf`（67,988,838 B） |
| query-ID digest | `7b958d5d989b7d884d76ac31082aad715623edec593421837b084a156926cd9e` |
| candidate-ID digest | `93915ae3d4a8d0205f45748cdd33ab455e0078d1067623cd1aab18cee83f27ee` |
| source | `data/processed/maven_ere/valid.jsonl` `6faea0e4…c6153` |
| generator tree | `588c02c05737a5245efcccdf62177b8221be5c8ef8cbd6fb0906e1953eb78abf`（3 个文件） |
| 生成参数 | seed **209**（SeDGPL 的）· `min_nodes=4` · `include_subevent=true` · `n_candidates=512` |

**population**：**1,908 实例** / 437 篇有实例（源 607 篇有事件图）/ 761 个 ECG /
候选池 6,892 个事件节点 / 每实例 512 候选 / 平均可判别答案 358.56。
**1,908 与本文件上方 2026-07-29 主结果的 n 一致**，即这次冻结的就是那批已发表数字所用的 unit，
不是重新推导出来的另一批题。

每行固定六个字段：`instance_id / doc_id / anchor / relation / gold / label / candidates`，
且 `candidates[label] == gold`（有测试锁）。

### 口径声明：这是**本地重建协议**，不是复现 SeDGPL 的 split

`MAVENSubWoRe.npy` 从未发布，所以论文的 CGEP-MAVEN 数字（SeDGPL 27.9 等）**不得进表 6-2**，
只能在正文作背景引用并写明不可比。这句话已写进 `manifest.json` 的 `protocol` 字段，
不是只写在文档里。

### 漂移怎么被发现

`scripts/freeze_e3_evaluation_unit.py --verify <dir>` 从源数据重建一遍，比三件事：
源 sha256、盘上 `queries.jsonl` 的 sha256、重建出来的 sha256。**实测 PASS**（2.3 s）。
生成器文件变了单独报为 `provenance only`，**不判 FAIL**——生成器可以改注释，
只要产出的 unit 逐字节不变；判 FAIL 的只有 unit 本身动了。
实例数与 1,908 不符时 `freeze` 直接 `SystemExit`，要求先冻结并披露原因再往下走
（E3.0 原文的要求）。

### final-valid 访问披露

unit 建在 MAVEN-ERE public valid 上，即 v6 协议的 final-valid——**与本文件 2026-08-30 那次同一个口子，
不是新开的**。本次只读事件 mention、causal/subevent 金标边与文档文本来**定义题目**，
没有训练、没有打分、没有选择任何模型/epoch/阈值。已写进 `manifest.json` 的 `final_valid_ledger`。

### 本地闸门

`631 passed / 28 skipped`、`ruff` 0、`ekg-smoke` OK。新增 4 条测试
（`tests/scripts/test_freeze_e3_evaluation_unit.py`）：干净往返无漂移、六字段齐全且
`candidates[label] == gold`、改一行候选顺序即被抓、源变了导致实例数不符则 fail-fast。

## ★ v6.1 · C-4b：CGEP-ESC 重建可行性裁决与切分口径确认（2026-09-13，本地纯 CPU，未训练）

### 开工自审

1. **科研价值**：对准名册 §6.2 的 FR-016 判定。Ch6 主表的五个外部对手**默认全部落 (b)**
   （原论文 CGEP-MAVEN 派生数据未发布）；唯一可能升到 (a) 的路是「在公开的 CGEP-ESC 上复现其
   已发表数字」。这一条成不成立，直接决定 Ch6 主表有没有一个**自证正确**的复现锚点，
   而不是一整列「透明适配」。证据要核到**机制本身**（原文 §5.1 与仓库代码），不是摘要措辞。
2. **可行性**：纯 CPU、只读。`ESCSubWoRe.npy` 本地已有，SeDGPL 仓库公开可 clone，论文 PDF 公开。
   五条（数据/协议/代码/算力/授权）没有一条不成立。

### 一手证据（全部本机核实，不是转述）

- 仓库 `zhanchuanhong/SeDGPL`，**全历史只有一个 commit** `265b19b69856428a63819c809572865b5faebf3f`
  （"Add files via upload"）。
- 仓库里的 `ESCSubWoRe.npy` 与我们本地 `data/raw/sedgpl_esc/ESCSubWoRe.npy`
  **SHA-256 完全相同**：`8ec791fb609cadf2ba1c8589d3f18ce1fac95b50c57203f1b25472d8438e5026`。
- 该文件结构：**22 个 topic → 244 篇文档 → 1,192 个实例**，候选集 256。论文 Table 1 报
  **243 篇 / 1,191 实例 / 256 候选**——**各差 1**，即这份公开件就是论文那份 CGEP-ESC。
- **没有 `train`/`valid`/`test` 键**；而 `load_data.py` 写死 `np.load('data/MAVENSubWoRe.npy')`
  并取 `['train']/['valid']/['test']`。**仓库里没有 MAVENSubWoRe.npy，也没有任何 ESC 代码路径。**

### ⚠️ 切分口径确认：原文写的是 **topic 级 5 折 CV**，不是文档切分

论文 §5.1 原文（`aclanthology.org/2024.findings-emnlp.45.pdf`）：

> "Following the standard data splitting of the underlying ESC (Caselli and Vossen, 2017) corpus,
> we use the last two topics as development set and conduct **5-fold cross-validation on the
> remaining 20 topics**. The average results of each fold are adopted as performance metrics."

**这推翻了本项目此前的一条记载。** 名册 §6.2、`ENGINEERING_NOTES.md`、`DATASETS.md` 与
`scripts/evaluate_cgep.py` 的 docstring 都写着「SeDGPL 公开的 19.6 就是泄漏值」——那是从
**产物**（npy 没有切分键）反推出来的，原文其实**明确声明了不泄漏的那一种切分**。

如实的表述应当是：

- 原文声明 **topic 级 5 折 CV**（+ 最后两个 topic 作 dev），这是 ESC 的标准非泄漏口径；
- **我们的复现在声明的口径下差得很远**：我们的 topic-CV 得 **MRR .0599 ± .0138**，
  原文报 **.196**；只有换成文档切分才得到 **.1802 ± .0089**，接近其数字；
- 因此这是**在声明口径下的复现缺口**，**不是**「作者用了泄漏切分」的证据。两者对 FR-016 的
  后果完全不同：(a) 要求的正是「在声明口径下复现出它的数字」。
- 另外，我们的 topic-CV **也不是它的 topic-CV**：`topic_folds` 对**全部 22 个 topic**做轮转 5 折，
  **没有**把最后两个 topic 留作 dev，也就没有 dev 上的 epoch 选择。我们的 .0599 只能说是
  *一种* topic-CV 的结果。

同一节还确认了一件对 Ch4 有用的事——**SeDGPL 自己也拿 MAVEN-ERE 的 valid 当 test**：

> "Since the underlying MAVEN-ERE corpus did not release the test set, following (Tao et al., 2023),
> we use the original development set as our test set and sample 20% of the data from the original
> training set to form the development set."

⇒ 继 MAQInstruct 之后的**第二个先例**，且是 Ch6 基座论文本身。

### 裁决：`conditionally_runnable`——能跑，但要三个透明补丁，且有两处未公开的自由度

| # | 阻断点 | 一手依据 | 补法 |
|---|---|---|---|
| 1 | **无 ESC 代码路径**：loader 写死 MAVEN 且要 `train/valid/test` 键，ESC 件是 topic 键 | `load_data.py:13`；npy 22 topic 键 | 自写 loader + 按 §5.1 切分（**透明补丁**，口径有原文可依） |
| 2 | **词表不覆盖 ESC**：公开 `reverse_event_dict.json` 4,307 条，只覆盖 ESC 998 个不同 mention 串的 **49.5%**（原样匹配 **0%**，因为 ESC 的 mention 带尾空格） | 本机实测 | 取消注释 `main.py:95` 的 `collect_mult_event`，用**它自己的代码**为 ESC 重建词表 |
| 3 | **不覆盖时会静默错**：`util.py:98` 的 `assert data[i][5] in reverse_event_dict` **被注释掉**，改成 `if ... in`，未命中的 mention 原样留在句子里 | `util.py:96-107` | 必须把 assert 加回去；否则半数候选被静默错打分而不报错 |
| — | 自由度 A：「最后两个 topic」是哪两个（npy 键序给出 `'37'`/`'41'`） | 原文未点名 | 按 npy 键序取，并在结果里写明 |
| — | 自由度 B：剩下 20 个 topic 的**折分配**未发布（其代码 `random.seed(209)`） | `load_data.py:5` | 用 209 复现并声明 |

**成本**：RoBERTa-base、`len_arg=200`、`batch_size=1`、ESC 上 15 epoch（`parameter.py` + 附录 B），
全集只有 1,192 实例（每折 train ≈ 950），另加每折的 event-centric 预训练。量级是**小时**，不是天。

### 建议（交作者裁决，不阻塞队列）

**只为 SeDGPL 一个方法走 ESC 的 (a) 路，其余四个对手维持 (b) 并写明障碍。**
理由：① SeDGPL 是 Ch6 的基座，也是唯一训练代码齐备的那个，它的数字最需要自证；
② Table 2 虽然五个方法都有 ESC 列，但另外四个的 ESC 数字同样是 SeDGPL 作者做的适配，
为它们各自再走一遍 ESC 复现，等于把 G-11a（已估 3–4 周）再翻一倍；
③ QR-001 v1.1.0 已把 baseline 广度降为**报告要求**，(b) + 点名障碍是合规的。
**若 SeDGPL 的 ESC 复现也对不上**（我们自己的重实现在声明口径下差 3 倍，这个风险是实的），
则如实记 (b)，障碍写「原文声明 topic 级 5 折 CV，但公开件不含折分配与 dev topic 名单，
按声明口径复现未达其报告值」——这依然是**有证据的** (b)，比现在这种从产物反推的说法结实得多。

## ★ v6.1 · G-11a 第一刀：四个外部对手的可得性与可运行性（2026-09-13，本地纯 CPU，未训练）

### 开工自审

1. **科研价值**：表 6-2 要 ≥3 个公开对手带 FR-016 状态，四个仓库此前**一个都没 clone**，
   按 §3.1 基准率整项 3–4 周。先做**静态可得性 + 可运行性**这一刀，是为了在花掉那几周之前
   知道每条路的障碍在哪——EasyECR / DREEAM / LLMERE 三次都是这样在零 GPU 成本下拿到裁决的。
2. **可行性**：clone + 读代码 + 用 python 重算已发布预测，纯 CPU、只读。

### 五个仓库的一手清单（commit 与内容均本机核实）

| 方法 | commit / 日期 | LICENSE | 训练码 | 原基准数据 | 依赖 pin | 关键障碍 |
|---|---|---|---|---|---|---|
| **SeDGPL**（基座） | `265b19b6…` 单 commit | **无** | ✅ | CGEP-MAVEN **未发布**；CGEP-ESC 已发布 | 未 pin torch | 无 ESC 代码路径，见 C-4b |
| **BART contrastive**（`zhufq00/mcnc`） | `e895ed38…` 2023-12-25 | **无** | ✅ 两阶段 | ✅ NEEG MCNC **随仓库发布**（115 MB） | `torch==1.7.1` + **apex** | 版本墙（见下）+ 任务不同 |
| **CSProm-KG** | `9a807295…` 2023-07-18 | **无** | ✅ | ✅ WN18RR/FB15k-237/ICEWS14/ICEWS05-15 **随仓库**，另有公开 checkpoint | `torch==1.11.0+cu113`、`pytorch_lightning==1.9.3` | 版本墙 + 任务不同 |
| **MCPredictor** | `a3245516…` 2022-06-29 | **无** | ✅ | ❌ **只有一个 stopwords 文件**；需 **LDC2011T07 Gigaword**（许可）+ python2.7 预处理链（C&C / OpenNLP / Stanford postagger） | `transformers==3.5.1` | **数据不可得 → 原基准 (a) 封死** |
| **SimKGC** | `97cc43e4…` 2022-12-24 | **无** | ✅ | ✅ WN18RR/FB15k237 随仓库 + **已发布预测** | `torch>=1.6`、`transformers>=4.15`（**无上限**） | 最友好 |

**五个仓库没有一个带 LICENSE 文件**——与 LLMERE（MIT）、DREEAM（MIT）不同，这一条要在论文里如实写。

### ⚠️ 结构性事实：四个对手**没有一个实现 CGEP**

它们各自实现的是自己的原任务——mcnc / MCPredictor 是 **MCNC 五选一**，CSProm-KG / SimKGC 是
**知识图谱补全**。名册 §6.1 早写了「它们的 CGEP 数字是 SeDGPL 作者自己做的适配」，而那份适配
**从未发布**。⇒ **表 6-2 的每一行都要我们自写适配器**，四行在我们的重建协议上**注定是 (b) 透明适配**，
与 TacoERE 同类。(a) 只能在**各自的原基准**上取得，用来证明「我们把它们的方法跑对了」。

**由此得到的 FR-016 地图**（这是本刀最有用的产出）：

| 方法 | 原基准 (a) 可达？ | 依据 |
|---|---|---|
| SimKGC | ✅ **最便宜** | 数据随仓库、预测与 metrics 已发布、依赖无上限 |
| CSProm-KG | ✅ | 数据随仓库、有公开 checkpoint；需升 torch/lightning |
| BART contrastive | ✅ 但最贵 | 数据随仓库，但要两阶段预训练 + 过 apex/torch 1.7.1 的版本墙 |
| MCPredictor | ❌ → **(b)**，障碍=**LDC2011T07 需许可** | 与 EasyECR 的 KBP 2017 同类 |
| SeDGPL | 只能走 ESC | 见 C-4b |

⇒ **三个 (a) + 一个有名障碍的 (b)**，广度满足 QR-001 v1.1.0 的报告要求。

### 版本墙：pin 的 torch 在我们两台卡上都跑不了

`torch==1.7.1`（mcnc）与 `torch==1.11.0+cu113`（CSProm-KG）最高只到 **sm_86**；
**4090 是 sm_89、5090 是 sm_120**，两台都不在范围内。这与 EasyECR 撞的是同一堵墙
（`ENGINEERING_NOTES`：torch 2.0.1 不支持 sm_120）。⇒ 这两个复现**必须升 torch**，
属于「为跑通做的透明补丁」，**必须记补丁与前后 hash**。SimKGC 的 pin 无上限，不受影响。

### 实测：SimKGC 的已发布预测**不足以重算它的主指标**

`predictions/README.md` 写明每行有 `rank` 字段，**实际文件里一行都没有**（四个文件的字段集
恒为 `correct / head / pred_score / pred_tail / relation / tail / topk_score_info`）。
`topk_score_info` 只给 top-3，所以 **MRR / H@3 / H@10 无法从已发布预测重算**，只有 Hit@1 能。

能重算的那一个**逐位对上了**（本机 CPU 重算 vs 其 `metrics.json`）：

| 数据集 | 方向 | n | 重算 Hit@1 | 其 metrics.json |
|---|---|---:|---:|---:|
| WN18RR | forward | 3,134 | **.6308** | .6308 |
| WN18RR | backward | 3,134 | **.5421** | .5421 |
| FB15k237 | forward | 20,466 | **.3373** | .3373 |
| FB15k237 | backward | 20,466 | **.1609** | .1609 |

而其 `metrics.json` 的 average 与**原文 Table 3 的 SimKGC_IB+PB+SN 行逐项吻合**
（一手核到 `aclanthology.org/2022.acl-long.295.pdf` 的表，不是凭记忆）：

| | MRR | H@1 | H@3 | H@10 |
|---|---:|---:|---:|---:|
| WN18RR 原文 | 66.6 | 58.7 | 71.7 | 80.0 |
| WN18RR 其 metrics.json | 66.55 | 58.65 | 71.65 | 80.01 |
| FB15k-237 原文 | 33.6 | 24.9 | 36.2 | 51.1 |
| FB15k-237 其 metrics.json | 33.55 | 24.91 | 36.23 | 51.06 |

⇒ **它的已发布件与它的论文自洽**，我们的评分轴读对了。但**这还不是 (a)**——
(a) 要求我们自己跑它的代码复现出这四个数，而 `rank` 缺失意味着**那一步不能靠打分现成预测省掉**。

### 下一步（G-11a 的第二刀，需要卡）

按成本从低到高：**SimKGC →（原基准 (a)）→ CGEP 适配器 → 我们的冻结 unit**，
再 CSProm-KG（先升 torch/lightning），再 BART contrastive（最贵），
MCPredictor 直接进 (b) 并写明 LDC 障碍。四个适配器共用 `runs/stages/E3/e3-v61-20260913/queries.jsonl`
（C-10 已冻结）作为唯一的题面。

## G-11a 第二刀 · SimKGC：搬运、环境与预处理（2026-09-14，gpu-5090）

### 开工自审

1. **科研价值**：表 6-2 要 ≥3 个公开对手在冻结的同一把尺（`e3-v61-20260913/queries.jsonl`，1,908 实例）
   上出数，且带 FR-016 状态。第一刀已把地图画清：**SimKGC 是四个对手里唯一依赖无版本墙、
   数据随仓库、原基准 (a) 最便宜的那个**。Ch6 是唯一不依赖任何方法章成败的一章，
   也是耗时最长的一项——Gate 2 判完再启动就来不及（`HANDOFF` §0.3 的排序理由）。
2. **可行性**：五条（数据/协议/代码/算力/授权）逐条核过，**卡在「数据」的一个变体上并已解除**：
   见下。

### ⚠️ 新的既成事实：**两台服务器都没有外网**

实测（`curl`/`wget`/`git` 都在，连接超时；本地 `python urllib` 对同一 URL 返回 200）：

| 机器 | huggingface.co | github.com |
|---|---|---|
| gpu-5090 | ❌ timeout | ❌ timeout |
| gpu-4090 | ❌ timeout | ❌ timeout |
| 本地 | ✅ 200 | ✅ 200 |

⇒ **外部仓库与预训练权重只能本地下载再 scp**，没有第二条路。这条此前没有记在任何文档里，
而它影响**每一个**外部对手复现（CSProm-KG 的公开 checkpoint、BART contrastive 的 NEEG 数据同理）。
实测带宽约 **0.4 MB/s**（50 MB 传输 > 2 分钟），这正是 `CLAUDE.md` 那句「单程约 70 分钟」的来源。

### 搬运（作者 2026-09-14 批准）

| 件 | 大小 | 本地 sha256 | 5090 sha256 |
|---|---:|---|---|
| `SimKGC.tar.gz` | 32 MB | `7dcc7586…2d93da` | **逐位一致** |
| `bert.tar.gz` | 389 MB | `f6988623…a8c4e0` | **逐位一致** |

落地 `gpu-5090:/mnt/aidata/tongjiakai/baselines/`（**ekg 仓库之外**，不受远端 `git reset --hard` 波及）：
`SimKGC/` 85 MB、`bert-base-uncased/` 421 MB。
远端复核 `git -C SimKGC rev-parse HEAD` = **`97cc43e488f19ca5b0f6fbf60ffefd2ee56c0693`**，与名册 §6.2a 记的
`97cc43e4…` 一致。`bert-base-uncased` 只取 5 个必需文件（config / vocab / tokenizer×2 / model.safetensors），
**未取 tf / flax / rust 权重**，省约 1 GB。

### 环境：无版本墙，确认

`torch 2.8.0+cu128`、`transformers 4.53.3`，`torch.cuda.is_available() = True`。
SimKGC 的 pin 是 `torch>=1.6` / `transformers>=4.15`（**无上限**），⇒ **不需要任何版本补丁**
——与 CSProm-KG（`torch==1.11.0+cu113`）和 mcnc（`torch==1.7.1`）那堵 sm_86 的墙不同。

⚠️ **一个 import 形态要记下来**：`config.py` 在 **import 时**就解析 argparse 并 assert，
所以 `import models` 之类的裸 import 必然报
`AssertionError: One of args.model_dir and args.eval_model_path should be valid path`。
**这不是缺陷，是它的全局 args 设计**——冒烟只能通过真实入口（`preprocess.py` / `main.py`）做。

### 预处理：PASS（纯 CPU）

```bash
cd /mnt/aidata/tongjiakai/baselines/SimKGC
/mnt/aidata/tongjiakai/ekg/.venv/bin/python -u preprocess.py --task WN18RR \
  --train-path ./data/WN18RR/train.txt --valid-path ./data/WN18RR/valid.txt \
  --test-path ./data/WN18RR/test.txt
```

（唯一的偏离是解释器：`scripts/preprocess.sh` 写死 `python3`，而 5090 的系统 python3 没有 torch；
换用 `.venv/bin/python` 调同一个脚本、同样参数，**不改仓库一个字节**。）

产出 40,943 实体 / 11 关系 / train **86,835** · valid **3,034** · test **3,134**。
⇒ **test 3,134 与本页上一节记的「WN18RR forward n=3,134」逐位一致**，
独立印证我们重算其已发布预测时读的就是同一份 test split。

### 下一步：训练（等 GPU）

5090 当前在跑 A4 的梯度修正验证跑（见 `results/PHASE_A.md`），单卡，SimKGC 训练排在其后。
目标是复现原文 Table 3 的 **MRR 66.6 / H@1 58.7 / H@3 71.7 / H@10 80.0**；README 写 < 3 小时。
冻结命令（`scripts/train_wn.sh` 的参数，两处透明替换：解释器 + 本地权重路径）：

```bash
cd /mnt/aidata/tongjiakai/baselines/SimKGC
setsid nohup /mnt/aidata/tongjiakai/ekg/.venv/bin/python -u main.py \
  --model-dir ./checkpoint/wn18rr/ \
  --pretrained-model /mnt/aidata/tongjiakai/baselines/bert-base-uncased \
  --pooling mean --lr 5e-5 --use-link-graph \
  --train-path ./data/WN18RR/train.txt.json --valid-path ./data/WN18RR/valid.txt.json \
  --task WN18RR --batch-size 1024 --print-freq 20 --additive-margin 0.02 \
  --use-amp --use-self-negative --pre-batch 0 --finetune-t \
  --epochs 50 --workers 4 --max-to-keep 3 > logs/simkgc_wn18rr.log 2>&1 &
```

**取得 (a) 之后**才写 CGEP 适配器打我们的 `queries.jsonl`；两步不可颠倒——
先证明「我们把它跑对了」，再谈「它在我们协议上是多少」。

### ⛔ SimKGC 训练：**「算力」不可行**（2026-09-14 实测，停下交裁决）

透明补丁打完、数据就绪后启动训练，**OOM**：

```
torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 76.00 MiB.
GPU 0 has a total capacity of 31.35 GiB of which 32.06 MiB is free.
```

**一手证据（它自己的 README，不是推断）**：

- 第 18 行：**"All experiments are run with 4 V100(32GB) GPUs."**
- 第 111 行（FAQ「我遇到 CUDA OOM」）：**"We run experiments with 4 V100(32GB) GPUs,
  please reduce the batch size if you don't have enough resources."**
- 第 116 行：**不支持 DDP**——"Some input masks require access to batch data on all GPUs"；
  `trainer.py:197` 用的是 `torch.nn.DataParallel`。

⇒ `train_wn.sh` 冻结的 `--batch-size 1024` 需要 **4×32 GB = 128 GB**。我们有
**5090 单卡 32 GB**；4090 是 4×24 = 96 GB，**仍然不够**，且已被他人占 5 天。

**为什么不能直接减 batch**：SimKGC 是对比学习，**batch size 就是 in-batch 负样本数**
（`IB` 正是它命名里的那一项）。把 1024 减到单卡装得下的量级，改的是方法的核心超参，
**跑出来的数按定义就不是它发表的那个数**，(a) 也就不成立。README 自己把减 batch 写成
「资源不够时」的退路，而 66.6 是 1024 下的结果。

⇒ 按 `CLAUDE.md` 开工自审表格，这卡在**算力**一条。**不自行换题，交作者裁决。**

### 由此发现：第一刀的成本排序把训练显存漏掉了

本页上一节把 SimKGC 排为「最便宜」，依据是**数据随仓库 / 预测已发布 / 依赖无版本墙**——
三条都对，**但没有一条是显存**。把显存算进去，排序变了：

| 方法 | (a) 怎么取得 | 显存 | 版本墙 |
|---|---|---|---|
| **CSProm-KG** | **公开 checkpoint + 推理**（README §33「Pretrained Checkpoint」，下载到 `./checkpoint/` 跑 evaluation） | WN18RR/FB15k-237 `-batch_size 128`，**且只需推理** | 有（`torch==1.11.0+cu113`，须升版并记补丁） |
| SimKGC | **必须训练**（已发布预测缺 `rank`，省不掉） | **4×32 GB** | 无 |

⇒ **建议把 CSProm-KG 提到 SimKGC 之前**：用公开 checkpoint 取 (a) 只要一次推理，
**不需要 128 GB，也不需要等 4090**。它的版本墙是升 torch，属于已经做过多次的透明补丁；
而 SimKGC 的障碍是硬件，补丁解决不了。
⚠️ 其 checkpoint 在 **Google Drive**，而两台服务器都没有外网 ⇒ 仍要本地下载后 scp（见本节开头）。

### SimKGC 三条可选路（未实施，等裁决）

| | 做什么 | 后果 |
|---|---|---|
| **(A)** | 单卡减 batch（1024 → 单卡装得下的量），如实标注偏离 | 拿不到 (a)；该行落 **(b) 透明适配**，障碍写「原配置需 4×32 GB」。**成本约 3 小时** |
| **(B)** | 等 4090 四卡（96 GB） | 仍 < 128 GB，还是要减 batch；且要等一张被占 5 天的卡 |
| **(C)** | **先做 CSProm-KG 的 checkpoint 推理**，SimKGC 推迟到 4090 可用时再议 | **推荐**。用一次推理换一个 (a)，不赌硬件 |

### 已完成的部分（不必重做）

搬运、环境、预处理、透明补丁均已落地，**SimKGC 随时可训**，只差显存或一个减 batch 的裁决。

**透明补丁 1**（`trainer.py`，2026-09-14）：`transformers 4.53.3` 已移除 `AdamW`
（`ImportError: cannot import name 'AdamW' from 'transformers'`）。改为 `torch.optim.AdamW`，
并在调用处**显式钉 `eps=1e-6`**——torch 的默认是 `1e-8`，而 `transformers.AdamW` 是 `1e-6`，
原调用只传了 `lr` 与 `weight_decay`，不钉就会静默换掉一个优化器超参。

| | sha256 |
|---|---|
| `trainer.py` 补丁前 | `570383f3ba98af2d0fd986d71babb178a8038e4e0efa92730d9566c78c07f7d2` |
| `trainer.py` 补丁后 | `cf856dc302e9a4069b9fed6111fb7b194e68a2a37dad398319b83f77f15978c9` |

⚠️ **这是第三堵版本墙，形态与前两堵不同**：CSProm-KG / mcnc 撞的是 `torch` 太旧跑不了新卡（sm_86），
SimKGC 撞的是 **`transformers` 太新删掉了旧 API**。名册 §6.2a 记的「SimKGC 依赖无上限、不受影响」
**只对 torch 成立，对 transformers 不成立**——`transformers>=4.15` 没有上限，但 4.53 移除了它用的符号。

## ★ G-11a 第三刀：改序执行，CSProm-KG 就位（2026-09-15）

### 作者裁决（2026-09-15）

批准 §「SimKGC 三条可选路」的 **(C)**：**先做 CSProm-KG**，SimKGC 落 **(b) 透明适配**、
障碍写「原配置需 4×32 GB，减 batch 会改变其 in-batch 负样本定义」。
另批「优先下载而不是跨 GPU 搬运，网络有问题时用镜像或替补方法」。

### 本轮把网络的真实形状测清楚了（此前只记了「两台机都没有外网」，那句话太粗）

| 目标 | gpu-5090 | 说明 |
|---|---|---|
| `github.com` 直连 | ❌ | 与 09-14 记录一致 |
| **`gh-proxy.com` 镜像** | ✅ **增量 `git fetch` 可用** | ekg 仓库本轮就是这样从 `4297fdb` 同步到 `45c2bbf` 的 |
| 同一镜像上 **完整 `git clone`** | ❌ | 两次都断在 `fetch-pack: unexpected disconnect`（含 `--depth 200`） |
| **`pypi.tuna.tsinghua.edu.cn`** | ✅ **HTTP 200** | ⇒ **服务器能装包**。CSProm-KG 要升 `torch`、EasyECR 的 C-2b 活体 venv 都因此可行，不必本地下 wheel 再搬 |
| `drive.google.com` | ❌ 超时 | ⇒ 公开 checkpoint 只能本地下载后 scp |

**带走的纪律**：「没有外网」是个太粗的判断，它把**能装包**和**能拉 checkpoint** 混成了一件事。
按目标域名逐个测，结论才有用——这一条直接改变了 C-2b 与 CSProm-KG 两项的可行性判定。

### 已落地的产物

| 项 | 值 |
|---|---|
| 仓库 commit | `9a8072951beda3e5c609bd121c900b153466ca28`（与名册 §6.2a 记录一致） |
| 本地 clone | 132 MB（`.git` 28 MB + `data/` 104 MB） |
| 传输形态 | `tar czf` → **53.6 MB**，scp 到 `gpu-5090:/mnt/aidata/tongjiakai/baselines/`（**ekg 仓库之外**，不受远端 `git reset --hard` 波及） |
| 公开 checkpoint | Google Drive 文件夹共 4 个（FB15k-237 / ICEWS14 / ICEWS05-15 / **WN18RR**）；**只取 WN18RR** 一个（`WN18RR-epoch=425-val_mrr=0.5664.ckpt`，file id `1o6jxtFya6cl8pbeVW5uHy4O06CxiXpkW`） |

**为什么只取 WN18RR**：(a) 的作用是自证「我们把别人的代码跑对了」，一个基准足够；
FB15k-237 那份单文件就 617 MB，而两台服务器都要经本地中转。

### ⚠️ 不变的结构性事实（改序没有改变它）

四个对手在**我们的重建协议**上仍然注定 **(b)**——它们没有一个实现 CGEP，SeDGPL 作者的适配从未发布。
CSProm-KG 的 (a) 只在 **WN18RR** 上取得。**改序不减少主表内容，只是把「能自证的那个」先拿到手。**

### CSProm-KG 的 (a) 验证：**容差事前登记（2026-09-15，跑之前写死）**

复现目标取自仓库 README 的「Pretrained Checkpoint」表（与论文 Table 2 同源），**WN18RR 一个基准**：

| 指标 | 原文/README 值 | 事前容差 | 判据 |
|---|---:|---|---|
| MRR | **0.572660** | **±0.005 绝对** | 超出 ⇒ 不给 (a)，按差异排查并如实记 |
| Hit@1 | 52.06% | ±0.5 点 | 同上 |
| Hit@3 | 59.00% | ±0.5 点 | 同上 |
| Hit@10 | 67.79% | ±0.5 点 | 同上 |

**为什么这条容差比 D4 的 ±1.0 紧**：这是**纯推理重放公开 checkpoint**，没有训练方差，
唯一的误差源是库版本差异。**松容差在这里是给自己留后门。**
checkpoint `WN18RR-epoch=425-val_mrr=0.5664.ckpt`，1,689,462,973 B，
sha256 `27e40718319480e9601ae695…`（本地下载后 rsync 到 5090，双端核对）。

### 透明补丁清单（环境侧，2026-09-15）

原 pin `torch==1.11.0+cu113` 最高 sm_86，5090 是 sm_120 ⇒ **必须升版**。独立 venv 建在
`gpu-5090:/mnt/aidata/tongjiakai/baselines/CSProm-KG/.venv`（**不碰 ekg 的 venv**，那个 venv 里
连 pip 都没有、且此刻正跑着 A4 探测），装包走**清华 PyPI 镜像**：

| 包 | 原 pin | 实装 | 备注 |
|---|---|---|---|
| torch | `1.11.0` | **2.8.0** | 项目统一栈，sm_120 必需 |
| pytorch_lightning | `1.9.3` | **2.6.6** | 代码用的是 `devices`/`accelerator` 写法，PL 2.x 认；`ModelCheckpoint`/`load_from_checkpoint`/`trainer.test` API 未变 |
| transformers | `4.16.2` | **5.17.0** | 只用 `BertTokenizer`/`BertModel` |
| numpy / pandas / nltk / tqdm | 1.21.5 / 1.4.3 / 3.7 / 4.64.0 | 2.5.3 / 3.0.5 / 3.10.3 / 4.70.1 | py3.12 上旧版装不了（服务器只有 python3.12，且无 root 装 `python3.12-venv`，venv 由 `uv venv` 建） |

backbone `bert-large-uncased` **直接在 5090 上从 ModelScope 下载**（`AI-ModelScope/bert-large-uncased`，
1,344,997,306 B，sha256 `be24b235c46198938ac26993…`），**没走隧道**——这一条就是「优先下载、
用镜像」的实际收益：1.3 GB 本地中转要约 3 小时，服务器直下是分钟级。

## ★★★ G-11a 收口 · CSProm-KG WN18RR **复现成功，落 FR-016 (a)**（2026-09-16，gpu-5090）

### 开工自审

1. **科研价值**：Ch6 主表（`EXPERIMENT_PLAN.md` §7.4）要求带公开对手；CSProm-KG 是四个对手里
   **唯一有公开 checkpoint**的，(a) 只需一次纯推理。证据是它 README 的 Pretrained Checkpoint 表
   （MRR 0.572660 / H@1 52.06 / H@3 59.00 / H@10 67.79），容差 **09-15 事前登记**为
   MRR ±0.005、H@k ±0.5 点（紧于 D4 的 ±1.0，因为纯推理重放没有训练方差）。
2. **可行性**：仓库、独立 venv、backbone、checkpoint 四样 09-15 已就位且双端 sha256 一致；
   单卡推理，与 C5.3 并卡（C5.3 只吃 3.4 GB）。

### 结果：四项全部落在事前登记的容差内

| | 本次实测（5090） | README 公布 | 差 | 容差 | 判定 |
|---|---:|---:|---:|---|---|
| **MRR** | **0.572682** | 0.572660 | **+0.000022** | ±0.005 | ✅ |
| H@1 | 52.06% | 52.06% | 0.00 | ±0.5 | ✅ |
| H@3 | 59.03% | 59.00% | +0.03 | ±0.5 | ✅ |
| H@10 | 67.77% | 67.79% | −0.02 | ±0.5 | ✅ |

分向明细（论文只给 mean 一行，这里一并留档）：

| 方向 | MRR | MR | H@1 | H@3 | H@10 |
|---|---:|---:|---:|---:|---:|
| tail ranking | 0.658188 | 287.046267 | 59.80% | 68.41% | 77.73% |
| head ranking | 0.487176 | 630.361838 | 44.32% | 49.65% | 57.82% |
| **mean** | **0.572682** | 458.704052 | **52.06%** | **59.03%** | **67.77%** |

⇒ **CSProm-KG 在其原始基准上的 FR-016 状态由 (b) 升为 (a)**，是名册里第一个 (a)。
⚠️ **这不改变它在我们重建协议上的状态**：它没有实现 CGEP，进 Ch6 主表时仍是 (b)，
`BASELINE_ROSTER.md` §6.2b 逐行分开记。

推理耗时 **9 秒 / 25 batch**（40,943 实体 × 11 关系，batch 128）；总墙钟时间几乎全在数据预处理与
排障上。产物：`gpu-5090:/mnt/aidata/tongjiakai/baselines/CSProm-KG/logs/csprom_wn18rr_eval.log`。

### 五处透明补丁（前后 hash 全记，`-n_lar 8` 等超参一个没动）

⚠️ **上一节「transformers 5.17.0 只用 BertTokenizer/BertModel」这句话是错的**——作者自写的
`BertModelForLayerwise` 继承 transformers 的 BertModel 并调 `get_extended_attention_mask`，
**5.x 把它删了**。教训与 C-4b 那条同源：**只看 import 不看子类实现，会把「能跑」判早**。

| # | 文件 / 环境 | 症状 | 补丁 | before → after sha256 |
|---|---|---|---|---|
| 1 | `helper.py` | `nltk.download('stopwords')` 在无外网的机器上**永久挂起**（ESTAB 到 raw.githubusercontent，不返回） | 语料经 gh-proxy 预装到 `~/nltk_data`（`stopwords.zip` sha256 `48c0e52d…946b`，english 198 词），`download` 改为**仅在 `nltk.data.find` 失败时**调用 | `e4f5c20d…1863` → `ece65eb8…6daa` |
| 2 | `main.py` | checkpoint 存自 **CUDA device 5**，本机单卡，torch 拒绝反序列化 | `load_from_checkpoint(..., map_location='cpu')`，PL 随后自行搬到 trainer 设备 | `48f62ed6…0242` → `d801ac93…d1a8` |
| 3 | `main.py` | torch ≥ 2.6 默认 `weights_only=True`，checkpoint 里有 `argparse.Namespace` / `collections.defaultdict` | 模块层 `add_safe_globals([...])`（**保留 `weights_only=True`**，不是全局关掉校验） | → `102e2acc…cc96` |
| 4 | `models/P_model.py` | PL ≥ 2.0 删了 `validation_epoch_end` / `test_epoch_end`，且**定义了就拒绝运行**；又要求那个参数**名叫** `dataloader_idx` | 逐批 ranks 改在 `validation_step` 里累积，指标计算仍是作者原方法（改名 `_ekg_epoch_end`）；参数改名，函数体内保留作者原变量名 | `18dcab1d…d429` → `7ff9426a…51bb` |
| 5 | `helper.py` | `np.float` 在 numpy 2 已删（作者 pin 1.21.5） | 换成内建 `float`（numpy 自己的 removal note 说是同一语义） | → `2e409e71…6b3b` |

另加一处**环境**改动：该 venv 的 `transformers` **5.17.0 → 4.57.6**（作者原 pin 4.16.2；
4.16.2 在 py3.12 上装不了，4.57.6 是仍保留 `get_extended_attention_mask` 的最后一条 4.x 线）。
torch 2.8.0 / PL 2.6.6 **不动**（sm_120 必需）。

**载入完整性**：`strict=False` 下唯一的多余键是 `plm.embeddings.position_ids`
（新版 transformers 去掉的 buffer），**没有任何 missing key** ⇒ 没有哪一层是随机初始化的。
这一条要和分数一起看：数字对得上，且不是靠半个随机模型对上的。

---

## ★★ E3.1 前置核查：**三个上游 phase 里两个没有 `fallback_component_bundle_id`，而且补不回去**（2026-09-17，本地 + 只读 ssh，未训练、未占卡）

### 开工自审

1. **科研价值**：`phases/PHASE_E3_graph_application.md` 的 Inputs 与 Done when 都写死了同一条——
   identity/relation/factuality 三类上游「读真实 bundle，**或读其显式 `fallback_component_bundle_id`
   并在表头标明身份**」；Stop conditions 更写明「任一 blocked phase 既无 bundle 也无可校验 fallback
   component bundle：**该 predicted arm 不成立**」。Gate 2 之后 D4 已关闭、C5/A4 门未过，
   三类上游**全部要走 fallback 路径**。Ch6 是当前唯一还能产正结果的章（`EXPERIMENT_PLAN.md` §7.5 下行情形），
   这个字段缺失会直接让 E3.3 的 predicted arm 不成立。
2. **可行性**：纯读——读三份冻结契约与三份 pilot summary，本地 + 只读 ssh，分钟级 ⇒ 可行。

### 实测结论（这一条推翻了本轮开工时的判断）

开工时以为这是「给两个 runner 各补一个字段」的小改。**核完代码与契约，不是。**

| phase | 状态 | pilot summary 里有 `fallback_component_bundle_id` 吗 | 产出它的 runner 在契约 `code` 哈希集合里吗 |
|---|---|---|---|
| **A4**（relation） | 门未过 | ✅ **有**（`d595439` 在 A4.3 上卡**之前**补的，取 `baselines.a3_fallback.predictions_sha256`） | 是（7 个文件之一） |
| **C5**（identity） | 门未过 | ❌ **无**（`pilot-r2/pilot.json` 无此键） | **是**——`scripts/run_c5_argument_uncertainty.py`，9 个文件之一 |
| **D4**（factuality） | Gate 1 关闭 | ❌ **无**（`pilot/seed-13/pilot_summary.json` 无此键） | **是**——`scripts/run_d4_typed_cue_oof.py`，7 个文件之一 |

**为什么改 runner 补不回来**（三步都堵死，任一步都够）：

1. 这个字段只在 `--aggregate` 那一步写进 summary，而 C5/D4 的 pilot **都已经收口了**；
2. 两个 runner **都在各自契约的 `code` 哈希集合里** ⇒ 一改，契约立即失效，按纪律必须重建 preflight
   （`HANDOFF.md` §0.7 第 6 条），旧的不覆盖；
3. 就算重建成 preflight-r3，各臂 `status.json` / `fold.json` 里钉的 `contract_sha256` 仍是 r2，
   `aggregate()` 的 `_require`（C5: "arms ran under different contracts"；D4: 逐折 `contract_sha256`）
   **会直接拒绝**。要让新字段落地只能重跑 pilot = **重训**（C5 ~1 GPU·day、D4 ~1.5 GPU·day）+ 逐次授权，
   而 Gate 2 之前不启动任何重跑。

⇒ **A4 那条路（先改 runner、再重建 preflight、再跑 pilot）对 C5/D4 已经关闭**，它当初能走通，
只因为 `d595439` 落在 A4.3 上卡之前。**顺序决定了可行性**，这是本次最该带走的一条。

### 因此 E3.1 的前置约束改成这样（不是本轮执行，是写死给 E3.1）

**E3.1 必须自己登记这三个 fallback 身份，不得指望从 phase summary 里读到统一字段。**
登记动作属于 E3.1 本身（「闭合三类真实上游输入接口」），**不是**对已冻结 phase 产物的回填——
已冻结的 summary 一个字节都不动。

三份 fallback 的候选身份与 content hash 如下。
⚠️ **但「E3.1 开工直接用」这句话已被同日下午的实测否掉**——三者的文档集与 E3 unit **交集为 0**，
见本页下一节《E3.1 实测阻塞》。下表只保留「哪个 id 是合规的 fallback 身份」这一层结论，
**不再表示它们能直接喂给 E3.1**：

| 上游 | 可用 fallback | content-addressed id（= 契约登记的 hash） | 出处 |
|---|---|---|---|
| **identity**（C5） | MAVEN-ERE **official joint** 共指预测 | `66ff04bac5a11ab179ef50eeca51d56dbb613b7b04eaa04b749dd99ea82ffc42` | C5 契约 `baselines.official_joint.predictions_sha256`；文件 `runs/stages/R1/r1-v61-20260904/anchors/identity/official_joint_prediction.jsonl`（7,274,278 B，本地与 5090 双端一致） |
| **relation**（A4） | A3 fallback 预测 | A4 `pilot_summary.json` 的 `fallback_component_bundle_id`（取自契约 `baselines.a3_fallback.predictions_sha256`） | 已由 A4.3 aggregate 写出，**直接读** |
| **factuality**（D4） | `cls` OOF labels（macro-F1 **0.5539953**，D4 的主锚） | `f375e8a58c21c22cc0cc4b7d968df4c75fe1458f083814859bb66d7d1f4e9737` | D4 契约 `accepted_oof.baselines.cls.labels_sha256`；文件 `gpu-4090:/data/TJK/ekg/runs/stages/R1/r1-v61-factuality-oof-r2/cls_oof_labels.json` |

⚠️ **identity 的 fallback 不得取 `qwen3_argument_pooling`**（`87c089ca…e340f`）：它是 C5 契约登记的
**负面对照**，`PHASE_C5` 的 Stop conditions 明文禁止把它冒充公开方法族。
⚠️ **factuality 备选**是 `dynamic_multi`（`1aeb8ec6…ff33c`，macro-F1 0.545603），比 `cls` 低，
只在 `cls` 不可用时取，且**取哪个必须在表头标明**（E3 Inputs 的硬要求）。

### 限制

- 本节**只登记身份，不代表 E3.1 已做**：三份 fallback 的 ID 对齐（E3 的 1,908 实例 ⇄ 各 fallback 的
  mention/doc 命名空间）**尚未验证**，那是 E3.1 的第一项工作，缺失即 fail-fast（A 类：跨章 ID 对齐）；
- D4 的 `cls_oof_labels.json` 目前**只在 4090 上**，本地与 5090 都没有；E3.1 若在 5090 跑要先 scp + 双端核 hash。

### 下一步

不触发执行。本节的产出是 **E3.1 的前置条件收紧了**：它必须自带 fallback 登记步骤。
G-11 排期时把这一步算进去（纯 CPU，小时级以内）。

---

## 🔴 E3.1 实测阻塞：**三个方法章的产物与 E3 evaluation unit 文档集交集为 0**（2026-09-17，本地纯 CPU）

### 开工自审

1. **科研价值**：4090 空出来后，唯一不依赖 Gate 2 改纲结果的活线是 Ch6（`EXPERIMENT_PLAN.md` §7.5
   明写「Ch6 的构建损失、图依赖正控与不对齐发现**不依赖任何方法章成功**」）。要把 4090 用在 Ch6 上，
   路径是 E3.1 → E3.2（契约写明都是 CPU）→ E3.3（GPU 主表）。本节做的是 E3.1 的第一项断言。
2. **可行性**：纯 CPU、读已冻结产物 ⇒ 本节本身可行。**但它测出 E3.1 后续步骤不可行，见下。**

### 实测：五个文档集两两对照（全部现算，不是推断）

E3 unit（`runs/stages/E3/e3-v61-20260913/queries.jsonl`，1,908 实例）覆盖 **437 篇**文档、6,892 个节点 id。
节点 id 形如 `<doc_id>::<mention_id>`。

| 产物 | 文档集 | 与 E3 unit 437 篇的交集 |
|---|---:|---:|
| **C5** `pilot-r2/full/predictions.jsonl` | 291 篇 | **0** |
| **A4** `pilot/full/edge_predictions.jsonl` | 291 篇 | **0** |
| **D4** OOF 语料 `maven_fact/train.jsonl` | 2,913 篇 | **0** |
| `maven_ere/train.jsonl`（C5/A4 的 internal-dev 从这里切） | 2,913 篇 | **0** |
| `maven_ere/valid.jsonl`（E3 unit 的源） | 710 篇 | **437（全覆盖）** |
| `maven_fact/valid.jsonl` | 710 篇 | **437（全覆盖）** |

⇒ **E3 unit 建在 valid 上，三个方法章全部跑在 train 的切片上（291 / 291 / 2,913 篇），
没有一个 doc_id 能对上。** 这不是 id 命名口径不一致，是**文档集本身不相交**。

### 因此 E3 契约的 fallback 机制在这里闭合不了

`phases/PHASE_E3_graph_application.md` 的 Inputs 假设：phase `failed`/`blocked` 时读它
**显式的 `fallback_component_bundle_id`**，就能拿到该类上游。但三个已登记的 fallback
（identity=official_joint 预测、relation=A3 fallback 预测、factuality=`cls` OOF labels）
**全部是"另一个 split 上的预测文件"，不是能在 valid 上再推理一次的模型**。
把它们搬到 E3 unit 上没有任何映射可走——目标文档根本不在它们的覆盖里。

⚠️ 顺带确认历史 `predicted` 档的真实来源：`scripts/evaluate_cgep_propagation.py:14` 的注释写着
`predicted` is our **Phase A extractor's**——2026-07-29 那批 `.1802 / .1583` 用的上游是
**v5 时代的判别式抽取器在 valid 上的产出**，本来就不是 C5/A4/D4。

### 可行性判定：卡在【数据】与【协议】两条

- **数据**：E3 unit 需要的是 valid 437 篇上的 identity / relation / factuality 预测。
  三个 fallback 覆盖的是 train 的切片，**实测交集 0**，拿不到；
- **协议**：E3 契约把 fallback 定义成「可直接读的 component bundle」，而 P1/A4/C5/D4 四份契约实际
  登记的 fallback 都是「某个 split 上的预测产物」。两边对 fallback 是什么东西的假设不一致，
  **这个缺口在契约层，执行代理不能自行选一个补法**。

⛔ 按 `CLAUDE.md` 的开工自审规则，**停在这里交作者裁决，不自行换题绕开**。

### 三个替代，附推荐

| | 做法 | 代价 | 风险 |
|---|---|---|---|
| **(乙) 推荐** | **沿用历史 `predicted` 图**（Phase A 抽取器在 valid 上的产物，`.1583` 已发表），表 6-2 的表头**标明上游身份 = v5 判别式抽取器，不是 C5/A4/D4** | **零**——产物已在，`ch4_sedgpl.pt` 实测 load 后复现 `.1583` 逐位一致 | Ch6 的构建层与三个方法章脱钩。但 E3 契约本就不要求 Ch6 胜过方法章，§7.5 也明写 Ch6 的发现不依赖方法章成功 |
| (甲) | 用 C5/A4/D4 的 checkpoint 在 valid 710 篇上**重新推理**，产出新的 predicted 层 | GPU 小时级（4090 可做）+ 要先裁决**取哪个臂**（`full` 是没过门的机制臂，`remove_core` 是无机制臂）；D4 是五折 OOF，valid 上没有对应的单一模型，还要再定一个口径 | ⚠️ **让 Ch6 的构建层挂在三个没过门的机制上**——反而削弱当前唯一的活线 |
| (丙) | 把 E3 unit 重建到 internal-dev 上 | 违反 E3.0 冻结（1,908 实例已冻结） | **丢掉与 `.1802 / .1583` 并表的能力**，不可取 |

**推荐 (乙)** 的理由：① 它是唯一零成本且不依赖任何失败机制的路径；② Ch6 现在是唯一能产正结果的章，
把它的构建层绑到三个刚失败的机制上，是拿活线去赌已经判负的东西；③ 表头如实标明上游身份，
本来就是 E3 契约 Inputs 的要求（「**并在表头标明该臂的上游方法身份**」），(乙) 满足它。

### 这一节没有改变的东西

E3.0 冻结的 unit 一个字节没动；三个 phase 的产物只读未写；没有训练、没有占卡。
`EXPERIMENT_PLAN.md` 的 G-11 行已写死这条前置，改纲裁决与本项**互不阻塞**。

---

## ★★ 裁决落地 + E3.1 / E3.2 完成 + 表 6-2 四行到手（2026-09-17，本地 CPU + gpu-4090 card 0）

### 开工自审

1. **科研价值**：对准 `EXPERIMENT_PLAN.md` §7.4 的**表 6-2**。Gate 2 实测 0 章过门后，
   Ch6 是唯一还能产正结果的章（§7.5 明写它的发现不依赖任何方法章成功），而它整章卡在
   E3.1 的契约缺口上。裁完缺口 → E3.1 → E3.2 → 表 6-2 的自有行，是唯一一条不依赖
   任何已判负机制的推进路径。证据：本页上方 `.1802 / .1583 / .1185 / .0811` 四行已在这批
   1,908 实例上测过，缺的是 Hit@k 全列与两个平凡对照。
2. **可行性**：五条全部成立。数据在本地与 4090；协议就是已冻结的 unit；代码在仓库内；
   算力＝4090 四张卡全空且 `--load-model` 只需分钟级；授权＝CLAUDE.md「4090 有空即可自用」，
   本地三件套已全绿（644 passed / 29 skipped、ruff 0、smoke OK）。

### 裁决：三项按推荐落地

| 裁决 | 落点 | 依据 |
|---|---|---|
| ② **Ch6 上游身份** | **取 (乙)**：`predicted` 条件沿用 v5 判别式抽取器在 valid 上的产物 | 零成本、不依赖任何判负机制，且表头标明上游身份本就是 E3 契约 Inputs 的要求 |
| ① **Gate 2 改纲** | **推迟到 Ch6 主表有数字之后再定**，不是「停等」 | 取 (乙) 之后 Ch6 全线解锁，**没有任何可执行任务被 ① 阻塞**；而改纲该选哪一种形态，取决于 Ch6 交出什么。在 Ch6 数字之前定稿是用更少的信息做更大的决定 |
| ③ **C-3 / G-8** | **维持 (甲) 不执行** | 它是 Ch4 主表的一行；Ch4 存废未定之前，`< 1 GPU·h` 也没有去处 |

### ⚠️ 先抓到一个缺陷：冻结 unit 里有 68 个 `instance_id` 撞号

`e3-v61-20260913/queries.jsonl` 1,908 行里只有 **1,840 个不同的 `instance_id`**。
根因在 `cgep.py`：id 是 `{doc_id}::{head_idx}-{tail_idx}`，而**节点下标是每个 ECG 各自的**，
同一篇文档的两个 ECG 于是撞号——撞的两条是**完全不同的 query**（anchor、relation、gold、
候选集全不同）。没有任何地方报错。

- **影响面**：任何按 `instance_id` 做的逐实例跨臂 join 会静默合并它们；
  `predictor.py:102` 已经拿它当 `random` 基线的确定性哈希键 ⇒ **表 6-2 的 random 行受影响**；
- **不影响已发表数字**：`.1802 / .1583 / .1185 / .0811` 用的是 sedgpl 预测器，且 ranks 是**按位置**
  存的（`ch4_propagation_ranks.json` 是列表不是字典）；
- **修法**：query edge 自己命名自己（`{head_node_id}-{SUBTYPE}->{tail_node_id}`），`ab4ace0`，
  实测 1,908/1,908 唯一，并留了一条双 ECG 文档的回归测试。

**重新冻结为 `runs/stages/E3/e3-v61-20260917/`**（旧目录一个字节没动，保留）。
按 E3.0「若重建校验导致变化，须在看任何 consumer 结果前冻结并披露原因」——本次正是那个窗口。

| 轴 | 20260913 | 20260917 |
|---|---|---|
| instances / documents / ecgs / candidate_pool | 1908 / 437 / 761 / 6892 | **完全相同** |
| `candidate_id_digest` | `93915ae3…f27ee` | **完全相同** |
| `source.sha256` | `6faea0e4…6153` | **完全相同** |
| 逐行比对（doc_id / anchor / relation / gold / label / candidates） | — | **1,908 行零差异** |
| `query_id_digest` | `7b958d5d…6cd9e` | `3b700acc…15f6d` |
| `unit.sha256` | `e92629bd…5aecf` | **`f75e7e87272d718d68cb408163314519e906c50e90b3ba3a829a241a6baa11e6`** |

⇒ **只有 id 字符串变了**，与 `.1802 / .1583` 并表的能力一点没丢。
4090 上独立重建得到同一个 `f75e7e87…`（跨机复现），`--verify` PASS。

### E3.1 ✅ 三类上游接口已闭合（gpu-4090，纯 CPU）

`scripts/close_e3_upstream_inputs.py`。它**登记并校验，不复制**——消费者已经从 `--dump` 读那份边，
再落一份就是两个要同步的文件。断言两种静默失败：层没覆盖到的文档、落在 unit 节点框架外的端点。

| 层 | `gold` | `predicted`（上游身份 = v5 判别式抽取器） |
|---|---|---|
| identity | MAVEN-ERE released coref，**14,736 簇** | **16,104 个单例**——抽取器在 valid 上**没有预测任何共指**（`valid_prediction_sup.jsonl` 710 篇全是 `coreference: []`，dump metrics `n_pred=0`）。这是关于 v5 抽取器的事实，如实登记而不是就地补一个没人训练过的第四个方法 |
| relation | 119,831 条 | **217,694 条**，源 `runs/factuality/predicted_edges_valid.jsonl`（`77dd9acc…177e`） |
| factuality | MAVEN-FACT valid，16,104 条标签 | Phase D 检测器 `predicted_labels_valid.json`（`b5fd0bc9…ebdc`） |

⚠️ **`--relation-dump` 故意没有默认值**：本地 `runs/relations/supervised_dump.jsonl`
（`f0a73e8c…f31ff`，65 MB）与 `.1583` 背后那份 `predicted_edges_valid.jsonl`（133 MB）**是两份不同的
dump**（同一天、不同时刻），边数 228,305 vs 217,694。留默认值等于静默登记错上游。

产物 `runs/stages/E3/e3-v61-20260917/upstream_registry.json`（`f2685e10…6e9e`），`status=closed`。

### E3.2 ✅ 两个条件的描述性画像（gpu-4090，纯 CPU，无新依赖）

`scripts/report_e3_graph_profile.py`，607 篇（unit 候选池覆盖的全部文档）：

| | 节点 | 总边 | 拓扑边(causal+subevent) | 连通分量 | 平均拓扑度 | **R1 可达率** | **R2 query F1** |
|---|---:|---:|---:|---:|---:|---:|---:|
| **gold** | 16,104 | 119,831 | 12,115 | 8,888 | 1.5046 | 1.0000 | 1.0000 |
| **predicted** | 16,104 | 217,694 | **41,218** | 4,120 | **4.7455** | **0.7018** | **0.0795** |

边的细分（coreference 只有 gold 侧有，见上）：

| | causal/CAUSE | causal/PRECONDITION | subevent/SUBEVENT_OF | coreference |
|---|---:|---:|---:|---:|
| gold | 1,584 | 7,746 | 2,785 | 3,773 |
| predicted | 7,749 | 19,864 | 13,605 | **0** |

事实性分布（五类）：

| | CT+ | CT− | PS+ | PS− | Uu |
|---|---:|---:|---:|---:|---:|
| gold | 15,299 | 339 | 401 | 48 | 17 |
| predicted（Phase D 检测器） | 14,709 | 403 | 908 | 59 | 25 |

**★ 一条新的不对齐证据**：`predicted` 的 **R2 query F1 只有 .0795**，而它的下游 MRR 是
`.1583`，只比 gold 的 `.1802` 低 **12.2%**。结构侧「几乎全错」与下游「只掉一成」同时成立
⇒ 本页此前 causal_scc–R1 的 ρ=−0.064 那条不对齐，现在多了 **R2↔MRR** 这一对。
机制上说得通：拓扑边多了 3.4 倍而模板预算只有 20 条（实测 `tmpl` gold 15.9 → predicted 24.0），
消费者读到的是被预算截断后的一小撮，R2 那种逐边精确匹配的严苛度传不到下游。

子图图示：`runs/cgep/e3_graph_profile_1398d109_{gold,predicted}.dot`（Graphviz DOT，6 节点框架，
不引入绘图依赖）。

### 表 6-2 · 已到手的四行（冻结 unit `f75e7e87…`，n=1,908，**本地重建协议**）

平凡对照本地 CPU（`scripts/evaluate_cgep.py --dataset maven`，torch-free）；
自有两行 gpu-4090 card 0，**冻结权重 `ch4_sedgpl.pt` + `--load-model`，不重训、不选任何东西**，
canonical 模板序，seed 209。

| 方法 | MRR | Hit@1 | Hit@3 | Hit@10 | Hit@20 | Hit@50 |
|---|---:|---:|---:|---:|---:|---:|
| random | .0143 | .0021 | .0089 | .0241 | .0414 | .0891 |
| frequency | .0378 | .0267 | .0273 | .0372 | .0718 | .1509 |
| **本文构建图（predicted 上游 = v5 判别式抽取器）** | **.1583** | .1038 | .1530 | .2563 | .3580 | .5126 |
| 本文构建图（gold 上游，**上界**） | .1802 | .1143 | .1782 | .3124 | .4114 | .5823 |

严格口径（ties 全部判负）同表并存于产物：gold `mrr_strict .1252`、predicted `.1089`、
frequency `.0124`、random `.0122`。

- **`gold .1802` 与 `predicted .1583` 逐位复现** 2026-07-29 的两行 ⇒ 权重、词表与重新冻结的 unit
  三者对齐无误；本次新增的是 Hit@3/20/50 三列（原表是「待测」）；
- **任务不平凡**：`.1802 ≫ .0378 ≫ .0143`，两个平凡对照相差一个数量级以上；
- **`n_unscorable=1`**：1,908 里有 1 个实例 sedgpl 侧无法打分，两臂同一个，已随产物记录。

产物（双端 sha256 已核，本地与 4090 一致）：`runs/cgep/e3_main_ours.json`（`74b9273d…2aa7`）、
`e3_main_ours_ranks.json`（`99fb8ed1…83fe`，逐实例 rank + reachability，现在按唯一 id 键得住）、
`e3_graph_profile.json`（`2f4a6b5b…5227`）、两个 `.dot`、`upstream_registry.json`。

### ⚠️ final-valid 访问披露

与 2026-08-30 那次同性质：跑在 710 篇（v6 协议的 final-valid）上，**冻结权重 + 固定两个臂，
没有选择任何模型、epoch、阈值或结构**；平凡对照更是 torch-free 的确定性打分。
按 A 类红线不构成选模。**在此显式记录。**

### 表 6-2 还缺什么

四个公开对手行（SimKGC / MCPredictor / CSProm-KG / BART contrastive）。
`BASELINE_ROSTER.md` §6.2a 的结构性事实没有变：**它们没有一个实现 CGEP**，SeDGPL 作者的适配
从未发布 ⇒ 这四行在我们的重建协议上注定是 **(b) 透明适配**，适配代码要我们自己写。
CSProm-KG 已在 WN18RR 上取得 (a)（本页上方），那证明的是「我们把它跑对了」，不是它在 CGEP 上的分。
按 §3.1 基准率这是 3–4 周量级的 G-11a，**不是本轮能收口的**。

---

## ★ G-11a 第一个对手：CSProm-KG 的 CGEP 适配（2026-09-17 晚，本地 CPU + gpu-4090 落地）

### 开工自审

1. **科研价值**：表 6-2 的 §Baselines 第 1 类要求**不少于 3 个公开方法**，现在是 **0 个**
   （四行全是「待测」）。CSProm-KG 是名册里唯一取得 FR-016 **(a)** 的对手
   （WN18RR MRR 0.572682 vs 公布 0.572660），也是四个里与 CGEP 映射最短的一个——
   CGEP 的 query 就是 KGC 的 `predict_tail`。做成了就是表 6-2 的第一行外部对手。
2. **可行性**：五条逐个查。**数据**＝冻结 unit + train 图，都在；**协议**＝冻结 unit，在；
   **代码**＝仓库在 5090（含我们 09-16 的五处环境补丁），可搬；
   **算力**＝4090 四张卡空闲；**授权**＝`CLAUDE.md`「4090 有空即可自用」，本地三件套全绿。
   ⇒ 没有一条不成立。

### ⚠️ 先量出来一条决定「这一行该怎么读」的事实

CGEP 的 query edge 规则是**尾节点 outdeg 0、indeg 1**（`query_edge_indices`），
也就是说**金标后继在自己的 ECG 里只有这一条边**。而任何 triple 级切分都必须把这 1,908 条
query edge 从训练图里拿掉 ⇒ **金标后继在训练图里全部变成孤立点**。实测：

| | 数量 | 在训练图里有边的 |
|---|---:|---:|
| anchors | 593 | 484 |
| **golds（正确答案）** | **1,908** | **0** |
| 候选池（干扰项） | 6,892 | **4,863** |

**这不是我们这一版映射的毛病，是 CGEP 任务与 KGC 模型的结构性错配**：CSProm-KG 的输出层就是
实体嵌入表，**每一个正确答案的嵌入都没被训练过，而 70.6% 的干扰项被训练过** ⇒ 结构那一半
系统性地把概率推离正确答案。SeDGPL 不吃这个亏——它按 **token id** 打分，词表跨 train/test 建。

⇒ **这一行的数字低不等于 CSProm-KG 弱**，写进表时必须带这条解释；同时也不能因为「不好看」
就换一个映射去凑分数。数字照报，解释照写。

### 已落地的东西

**数据导出** `scripts/export_cgep_as_kgc.py`（本地 CPU，可重跑）：
`runs/stages/E3/kgc/CGEP-MAVEN/`，**33,017 实体 / 3 关系 / train 46,100 / dev 1,425 / test 1,908**，
候选文件 `test_candidates.txt` 每行 512 个实体 id。
dev 是**训练三元组的种子切片**，1,908 个 CGEP query **从不参与选 checkpoint**（A 类）。

**训练图怎么定的**：SeDGPL 看到的是每个实例自己的 gold ECG **减掉那一条 query edge**，
所以 valid 侧 gold 结构在本协议下对消费者是可见的；静态 KG 的等价物就是把它们放进图里，
**然后 1,908 条 query edge 必须全部拿掉**——同一个 ECG 里，A 实例的 query edge 就是 B 实例的
上下文，单张静态图做不到逐实例排除。导出时有断言：任何一条 query edge 漏进训练图就 fail-fast。

**逐条列出的差异**（FR-016 (b) 要求，已写进 `export_manifest.json`）：

1. 对手的已发表任务是 KGC 不是 CGEP，这套映射是我们做的；
2. valid 侧上下文边会**训练** KGC 嵌入，而 SeDGPL 只在推理时读它们——**这一条对对手有利**；
3. 没进任何训练三元组的 valid 实体保持初始化嵌入，只有文本那一半替它说话；
4. 打分被 mask 到每个 query 的 512 个具名候选，而不是整张实体表；
5. KGC 的 dev 是训练三元组的种子切片。

**代码搬运**：5090 的工作副本按 `git archive HEAD` + `git diff` 搬（只带源码与补丁，不带
6.6 GB 的 venv 与 1.6 GB checkpoint）。双端 sha256 已核：
`csprom_src.tgz` `b303620d…44a8`、`csprom_patches.diff` `017ea3c8…bd37`、
`cgep_kgc.tgz` `840c2332…a316f`。落点 `gpu-4090:/data/TJK/baselines/CSProm-KG`。
上游 commit `9a80729`，09-16 的五处环境补丁（numpy 2 的 `np.float`、nltk 离线、
torch≥2.6 的 `weights_only`、checkpoint 的 `map_location`、PL≥2.0 的 hook 改名）原样重放。

**第 6 处补丁（CGEP）** `scripts/patch_csprom_kg_for_cgep.py`，**不动模型、损失、优化器与指标**，
只加一个 dump。前后 sha256：

| 文件 | before | after |
|---|---|---|
| `main.py`（两个新选项） | `102e2acc…cc96` | `f5f29b8f…afdc`（`f5f29b8f4728e024170cd86d4b672ff0019cc624e047c0a97c2c3685ab0afd2c`） |
| `models/P_model.py`（读候选 + 每轮清空 dump） | `7ff9426a…51bb` | `8f01b996…fd8ce`（`8f01b996e7b623ad88dd39cb3a38066ec1cb9cdcb99975d60d3976a7963ff5ce`） |
| `models/P_model.py`（写候选分数） | `8f01b996…fd8ce` | `26cd8e54…d97c`（`26cd8e54e4d101c961eb5f68fa8a6df089473da70349cb91615af94c41e9d97c`） |

**为什么只 dump 分数、不要它的指标**：`docs/PROTOCOL_TABLE.md` 把 Ch6 的 evaluator 钉死在
`succession/metrics.py`。对手自带的 `get_performance` 把 head prediction 一起平均、并且用的是
另一套平局约定，**两样 CGEP 都不要**。所以补丁只在 `logits.detach()` 之后、在作者自己的
filtered-ranking mask **之前**，把那 512 个候选的原始分数写出来；排序、平局与 Hit@k 交给
`scripts/score_kgc_opponent.py`，走的是 gold / predicted / random / frequency 同一个 evaluator。
该脚本拒绝任何对不上的 dump：行号错位、候选集漂移、分母变小（漏打分的 query 是错误，不是可丢的行）。

### 环境已建、冒烟已过、正式跑已起（gpu-4090 card 0）

**环境**（独立 venv，**没碰 ekg 的 venv**）：`gpu-4090:/data/TJK/baselines/CSProm-KG/.venv`，
python **3.12.13**（用 uv 已下好的解释器建 venv，**没有跑 `uv run` / `uv sync`**），
装的是 5090 上那套实测可用的 **torch 2.8.0+cu128 / transformers 4.57.6 / pytorch_lightning 2.6.6 /
numpy 2.5.3 / nltk 3.10.3**。`torch.cuda.is_available()=True`，RTX 4090，矩阵乘实测通过。
nltk stopwords 走 gh-proxy 装到 `~/nltk_data`，sha256 `48c0e52d…946b` **与 09-16 那次逐位相同**。

⚠️ **backbone 直接从 `hf-mirror.com` 拉下来**（`bert-large-uncased`，1,344,951,957 字节，
24 层 / hidden 1024，实测 `AutoConfig` 能载）。**这推翻了「公开 checkpoint 只能本地下载后 scp」**
——旧结论测的是 `huggingface.co` 与 `drive.google.com`，**没人测过镜像**。
同一个教训第二次：**按域名测，别按感觉写**。已写进 `CLAUDE.md` / `AGENTS.md` 与 `HANDOFF.md` §0.6。

#### 第 7 处补丁：LAR 的 margin loss **在新 torch 上从来没跑过**

09-16 那次 (a) 是**纯推理**，所以 `-n_lar 8` 这条训练路径一次都没被执行过。第一个 training step 就炸：

```
File ".../torch/nn/functional.py", line 5503, in triplet_margin_with_distance_loss
    p_dim = positive.ndim
AttributeError: 'tuple' object has no attribute 'ndim'
```

作者把 `(embedding, bias)` 元组当 `positive`/`negative` 传给 `nn.TripletMarginWithDistanceLoss`，
由他们自己的 `distance_function=lambda x, y: score_fn(x, y[0], y[1])` 拆包；
**新版 torch 在调 distance_function 之前先校验 `positive.ndim`**。
补丁把 `TripletMarginWithDistanceLoss` **自己的公式**写开——
`relu(d(a,p) − d(a,n) + margin).mean()`，reduction `mean`、`swap=False`——
用的是**他们的** distance_function 与**他们的** margin（`configs.gamma`），**损失是同一个量**。
`models/P_model.py` `f137f34c…0096` → **`8da3ac0310eece26b8052cbd060ba1257ec875e140ab6e27f1b396d7c189e2be`**。

⚠️ 顺带修掉自己的一个洞：dump 必须 `self.trainer.testing` 才写。
`val_dataloader` 喂的是 **dev** 三元组、`test_dataloader` 才是 CGEP query，而 `test_step` 委托给
`validation_step` ⇒ 不加这个 guard 就会**拿 test 的行号去索引 dev 的行**，每条分数都配错 query。
打分器的 gold 校验会抓到，但要等训练跑完才抓到。

#### 冒烟：端到端通了

`-epoch 1` 全流程：`trainer.fit` → 按 `val_mrr` 选 checkpoint → `trainer.test` →
**dump 恰好 1,908 行** → `scripts/score_kgc_opponent.py` 用**我们自己的 evaluator** 收下。
1 epoch 的数字 **MRR 0.0066 / H@1 0.0010**（`runs/cgep/e3_csprom_smoke.json`）——
**这不是结果**，是「管道通了」的证据；模型基本没训。
⚠️ 确认了一条 A 类事实：`ModelCheckpoint(monitor='val_mrr')` 选的是 **dev 切片**，
**1,908 个 CGEP query 不参与选 checkpoint**。

#### 正式跑（进行中）

`-epoch 60 -check_val_every_n_epoch 3`，其余超参**与 README 的 WN18RR 命令逐字相同**
（batch 128 / bert-large / desc 40 / lr 5e-4 / prompt 10 / alpha 0.1 / n_lar 8 /
label_smoothing 0.1 / embed_dim 144 / k_w 12 / k_h 12 / alpha_step 1e-5）。
**只有 epoch 数不是 WN18RR 的**：WN18RR 用默认 500（实测 721 step/epoch、约 5.7 分钟/epoch
⇒ 约 52 小时），我们取 **60**——那是**作者自己给 FB15k-237 的 epoch 数**，
不是我们在本任务上调出来的。约 **5.7 GPU·h**，记为第 6 条差异。
日志 `logs/cgep_r1.log`，产物 `logs/cgep_r1/scores.jsonl`。

### 上一版状态（已被上面取代）：环境未建，**训练未开始**

4090 的 cpolar 隧道 2026-09-17 20:09 左右掉线（`Connection timed out during banner exchange`）。
作者的 `cpolar-ssh-update` **管不了这台**——它的 tunnels.conf 只有 `gpu-5090` 与 `gpu-a6000`，
4090 在另一个 cpolar 主机（`18.tcp.vip.cpolar.cn`）上。按三态判活，**这只是 ssh 失败**；
当时 4090 上没有任何任务在跑，补丁已落盘，**没有东西处于风险中**。

隧道回来之后的下一步，按顺序：

1. 建独立 venv（**不要动 ekg 的 venv**）：目标版本照 5090 那套实测可用的
   **torch 2.8.0+cu128 / transformers 4.57.6 / pytorch_lightning 2.6.6 / numpy 2.5.3 / nltk 3.10.3**
   （`requirements.txt` 写的 torch 1.11 + numpy 1.21.5 在 sm_89 上跑不了，这正是那五处补丁的由来）；
   4090 实测 `pypi.tuna.tsinghua.edu.cn` 返回 200，装得了包；
2. 先用 `-dataset CGEP-MAVEN` 跑一次**小步冒烟**（几十步 + 一次 test），确认 dump 行数 = 1,908
   且 `score_kgc_opponent.py` 能收下；
3. 再正式训练 + `trainer.test`，产出 `csprom_scores.jsonl` → 我们的 evaluator → 表 6-2 那一行。

⚠️ **`-cgep_scores` 的 dump 只在 `dataloader_idx == 0`（predict_tail）写**，predict_head 不是
CGEP 的问题，原样放过。

### 第二个对手 SimKGC 也已上卡（gpu-4090 card 1，与 CSProm-KG 并行）

**为什么值得跑，尽管它的已发表 CGEP 数字最低（9.3）**：见名册 §6.2c——它是**文本双编码器**，
实体表示由名字与描述文本编码而来，对未见实体是**归纳式**的，因此上面那条
「金标后继在训练图里 0/1,908 有边」几乎伤不到它，而 CSProm-KG 的实体嵌入表正面吃这一刀。
**两个对手放在一起，正好把「输出层依不依赖已训练的实体嵌入」这个变量单独测出来。**

搬运与补丁同 CSProm-KG 一路：`git archive HEAD` + `git diff` 从 5090 搬，双端 sha256 已核
（`simkgc_src.tgz` `850f9c3a…d6b0`、`simkgc_patches.diff` `a4391579…afcbc`、
`cgep_simkgc.tgz` `7b598cee…e4ab`）；上游 commit `97cc43e`，09-14 的一处环境补丁
（`transformers>=4.40` 删了 `AdamW`，改用 `torch.optim.AdamW` 并**显式钉 `eps=1e-6`**，
因为 transformers 的默认是 1e-6 而 torch 是 1e-8）原样重放。

**CGEP 补丁**（`scripts/patch_simkgc_for_cgep.py`，**不动模型、损失、打分函数**）：

| 文件 | before | after |
|---|---|---|
| `config.py`（task 白名单加 `cgep-maven` + 两个 dump 选项） | `ce6bf58a…28dd` | `3d273304c51b10266fdce82d57a86cf6b3a3d85bc0a59d502e15a6c5b2853c9d` |
| `evaluate.py`（模块状态 + dump + 只在 forward 方向装弹） | `bd423034…a98f` | `080c0e5524a7093e4ab9e6591026b84ea64e2dcf52b4a3b67dc92c9811c8f695` |

- `task` 字符串只到两个地方（`doc._parse_entity_name` 的 WordNet 后缀剥离、`rerank` 里一条
  wiki5m 断言），所以 `cgep-maven` 走的是**通用分支**——对我们的纯触发词正是对的那条；
- dump 放在 `rerank_by_graph` **之后**（那是 SimKGC 的方法组成部分）、known-triplet 过滤
  **之前**（那是 KGC 的 filtered 协议，CGEP 不用，我们的打分器也不需要）；
- **只在 forward 方向装弹**：backward 问的是「哪个头能解释这个尾」，不是 CGEP 的问题，
  而且它的行号会和 forward 的撞在同一个 dump 里。

#### ⚠️ batch 1024 实测装不下，**512 也装不下**

名册 §6.2b 记的障碍是「原配置 `--batch-size 1024` 需 4×32 GB」——那是从 README 推的。
现在有本机实测了（单张 4090，23.52 GiB）：

| batch | 结果 |
|---:|---|
| 1024 | **OOM**（差 300 MiB；加 `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` 再试，仍 OOM） |
| 512 | **OOM**（第一个 forward 就炸，差 38 MiB） |
| **256** | ✅ 稳定，实测 **19.9 GB**，360 step/epoch、约 3.8 step/s |

⇒ **取 256**，其余超参与 `scripts/train_wn.sh` 逐字相同（bert-base-uncased / pooling mean /
lr 5e-5 / additive-margin 0.02 / use-amp / use-self-negative / pre-batch 0 / finetune-t /
epochs 50 / use-link-graph）。
⚠️ **这一条必须和分数一起写**：in-batch 负样本从 1024 降到 256，**而对比学习的增益正是从负样本量来的**
⇒ **表 6-2 的 SimKGC 行是它的下界，不是它的发表设置**。不得用这一行说「SimKGC 弱」。

Epoch 0 结束时 dev（我们的训练三元组切片）`Acc@1 67.6 / Acc@3 85.5` ⇒ 训练本身是健康的。

#### 并行状态（两张卡，各自 namespace，不互相写）

| 卡 | 任务 | 进度（记录时） |
|---|---|---|
| card 0 | CSProm-KG `-epoch 60` | epoch 4/60，约 5.7 min/epoch ⇒ 约 5.7 GPU·h |
| card 1 | SimKGC `--epochs 50 --batch-size 256` | epoch 1/50，约 1.6 min/epoch ⇒ 约 1.3 GPU·h |
| card 2 / 3 | 空 | — |

评测是**另一次调用**（`evaluate.py --valid-path .../test.txt.json --cgep-*`），
所以训练期间 checkpoint 只按 dev 切片选，**1,908 个 CGEP query 全程不参与选模**。

#### 顺手买到的两条纪律

1. **重试封装不能套在非幂等命令上**。隧道会在远端**已经执行完**之后才断，
   重试于是把同一条命令又跑了一遍——这一轮就这样让一个补丁脚本跑了两次，
   第二次报「已应用」，把我引去查一个不存在的 anchor 问题。**重试只给只读/幂等命令用。**
2. **哨兵字符串必须是「只有这一处改动才会引入」的文本**。CSProm 那边用共享 marker，
   第二处改动一落地第三处就被判成「已应用」；SimKGC 这边用 `_CGEP_STATE['active']` 当哨兵，
   而它正是上一处改动写进去的。**同一个形状的错，隔一个文件又犯一次。**

---

## ★★★ SimKGC 收口，并测出一条**关于评测单元本身**的事实（2026-09-17 晚，gpu-4090 card 1）

### 先说结论

**表 6-2 这个单元有 80% 可以靠「候选是不是和 anchor 同一篇文档」猜出来。**
这不是某个对手的问题，是 `build_cgep` 的负采样口径决定的，而它决定了**哪些行之间可以比**。

### 怎么发现的

SimKGC 训完 50 epoch，用**我们自己的 evaluator** 打分得 **MRR 0.6253**——是 gold 档 `.1802` 的
**3.5 倍**。这个数字不可信，所以先不写表，去查它从哪来。

查的第一件事就命中：**候选是全语料采的（607 篇的 6,892 个节点里抽 512 个），而 ECG 从不跨文档**
⇒ **金标后继永远和 anchor 同篇，而 512 个候选里平均只有 2.1 个同篇。**
于是加了一个平凡对照 `same_document`（只看「是不是同篇」，同分按 `random` 那套种子哈希打破）：

| 对照 | MRR | Hit@1 | Hit@3 | **Hit@10** | Hit@20 | Hit@50 |
|---|---:|---:|---:|---:|---:|---:|
| random | .0143 | .0021 | .0089 | .0241 | .0414 | .0891 |
| frequency | .0378 | .0267 | .0273 | .0372 | .0718 | .1509 |
| **`same_document`（只看文档归属）** | **.8041** | .6567 | .9596 | **1.0000** | 1.0000 | 1.0000 |

**Hit@10 = 1.000**：金标必在同篇的那两三个候选里。`mrr_strict` 0.7934，同量级。
（`scripts/evaluate_cgep.py --dataset maven --predictor same_document`，
产物 `runs/cgep/e3_same_document.json`；predictor 已进 registry，带一条 targeted test。）

### 这条事实把表 6-2 劈成两族

| 族 | 能不能用这条捷径 | 为什么 |
|---|---|---|
| **读候选文本的**（SimKGC，以及任何文本编码 KGC） | **能** | 我们给每个实体的 description 就是它触发词所在的**那句话**，同篇候选的上下文词天然重合 |
| **按 mention token id 打分的**（SeDGPL ⇒ 本文 gold / predicted 两行） | **不能** | 文档身份根本进不了 prompt——它渲染的是 `<a_i>` 图模板 |

⇒ **跨族比较在这个单元上不是在比事件预测。**
`.1802` 与 `.1583` **不受影响**（SeDGPL 结构上看不见文档），但**任何高于 `.8041` 参考线的行都得先解释清楚它读了什么**。

⚠️ 顺带解释了一件原本不好解释的事：SeDGPL 原文给 SimKGC 的 CGEP-MAVEN 只有 **9.3**，
远低于它自己的 27.9。**这说明他们的 SimKGC 适配大概率没给候选 description**。
他们的适配从未发布，我们无从核对，所以**两种都跑**（见下）。

### SimKGC 实测三行（同一个 checkpoint，我们自己的 evaluator，n=1,908）

| 档 | MRR | Hit@1 | Hit@3 | Hit@10 | Hit@20 | Hit@50 |
|---|---:|---:|---:|---:|---:|---:|
| description = 触发词所在句，`--neighbor-weight 0.05`（他们的默认） | **.6253** | .4874 | .7364 | .8585 | .8926 | .9308 |
| 同上，**关掉图重排**（`--neighbor-weight 0.0`） | **.6373** | .5079 | .7395 | .8585 | .8926 | .9308 |
| description 全部清空（训练中，见下） | 待测 | — | — | — | — | — |

两条已测的读法：

1. **两档都低于 `same_document` 的 .8041** ⇒ SimKGC 在部分地吃这条捷径，**而且还没吃满**；
2. **关掉图重排反而高 +.0120** ⇒ 印证了名册 §6.2c 的预测：`rerank_by_graph` 按训练 link graph 的
   n-hop 邻居给候选加分，而**金标后继在训练图里 0 条边**（本页上一节），加分只落到干扰项上。
   **同一个 checkpoint、两次前向，不是调参**——它把「编码器 vs 重排器」这个变量单独测出来了。

**第三档正在 card 1 上训**（`data/cgep-maven-nodesc`，`entity_desc` 全部为空串，其余逐字相同，
约 1.3 GPU·h）。它要回答的是：**去掉文档上下文之后，SimKGC 还剩多少？**
dev 侧已有迹象——带 description 的 epoch 0 是 `Acc@1 67.6`，不带的 epoch 1 只有 `57.0`。

### 这一节改变了什么、没改变什么

- **没改变**：冻结 unit 一个字节没动（`f75e7e87…`）；`.1802 / .1583 / .1185 / .0811` 不受影响；
  E3.0 的口径与并表能力都还在；
- **改变了表 6-2 的读法**：`same_document` 从此是**必须并列**的一行，不是可选的消融。
  E3 契约 §Baselines 第 2 类要的就是「确认任务本身不平凡」——`random`/`frequency` 说它不平凡，
  这一行说它**在某一个方向上恰恰是平凡的**，而那个方向正好是文本类对手站的位置；
- **可写的发现多了一条**：本地重建的 CGEP-MAVEN 协议里，负采样跨文档而 ECG 不跨文档，
  两者叠加出一条 Hit@10=1.000 的捷径。原论文的派生数据未发布，**我们无法判断它是否也有这条**，
  只能如实说「我们的重建协议有」。

⚠️ **纪律**：这一轮差一点就把 `.6253` 当成「SimKGC 胜出 3.5 倍」写进表。
拦住它的是「**数字不合常理就先查口径，别先写表**」——本项目在这个形状上已经栽过五次
（Phase C 白跑两轮、Phase A 判错达标、Ch1 的 79.6 vs 77.47、C3 方向搞反、A4 拿被证伪的假设当依据）。
这次是第六次遇到、**第一次在写表之前拦住**。

### ★★★ description 消融收口：SimKGC 的 91% 来自那条捷径

**判据是在看到任一数字之前写下的**（本页上一节与名册 §6.2c）：两个导出存在的理由就是
「把事件预测和文档匹配分开」，而 `same_document` 的 `.8041` 已经独立地证明了这条捷径存在。
所以下面这张表不是事后挑档，是按事先写好的问题读出来的。

| 档（同一套超参、同一 evaluator、n=1,908） | MRR | Hit@1 | Hit@3 | Hit@10 | Hit@20 | Hit@50 | **top-1 是同篇文档的比例** |
|---|---:|---:|---:|---:|---:|---:|---:|
| description = 触发词所在句，重排 0.05（他们的默认） | .6253 | .4874 | .7364 | .8585 | .8926 | .9308 | — |
| description = 触发词所在句，**关重排** | **.6373** | .5079 | .7395 | .8585 | .8926 | .9308 | **78.20%** |
| **description 全部清空，关重排** | **.0563** | .0183 | .0430 | .1279 | .2013 | .3375 | **18.50%** |

- **MRR 塌了 11.3 倍（.6373 → .0563）** ⇒ **SimKGC 那个分数的约 91% 来自候选句带来的文档上下文，
  不是事件预测**；
- top-1 同篇率 **78.20% → 18.50%** 把机制直接摆出来了。作为标尺：均匀乱选的同篇率是
  **2.1/512 = 0.41%**——两档都远高于它，带 description 那档几乎是在**直接做文档匹配**；
- **`.0563` 与原论文给 SimKGC 的 `9.3` 同一量级**（不可同表，候选构造不同），
  这反过来印证了上一节的推断：**SeDGPL 作者的 SimKGC 适配大概率也没给候选 description。**

### 因此表 6-2 的 SimKGC 主行取「无 description」档

理由**不是**它更低，而是：① 它和 SeDGPL 族站在同一条轴上——**两边都读不到文档身份**；
② 判据事先写好；③ `same_document` 的 `.8041` 独立证明了另一档在测别的东西。
带 description 那档**照样入表**，标成「吃捷径档」，和 `.8041` 挨着放——它是本章关于
**评测协议**的证据，不是关于 SimKGC 能力的证据。

### 表 6-2 当前实测（冻结 unit `f75e7e87…`，n=1,908，全部走 `succession/metrics.py`）

| 方法 | MRR | Hit@1 | Hit@3 | Hit@10 | Hit@20 | Hit@50 |
|---|---:|---:|---:|---:|---:|---:|
| random | .0143 | .0021 | .0089 | .0241 | .0414 | .0891 |
| frequency | .0378 | .0267 | .0273 | .0372 | .0718 | .1509 |
| **SimKGC**[Wang+ 2022]（(b) 适配，batch 256，无 description） | **.0563** | .0183 | .0430 | .1279 | .2013 | .3375 |
| CSProm-KG[Chen+ 2023]（(b) 适配） | 训练中（card 0，22/60） | | | | | |
| **本文构建图（predicted 上游 = v5 判别式抽取器）** | **.1583** | .1038 | .1530 | .2563 | .3580 | .5126 |
| **SeDGPL**[Zhan+ 2024]（(b) 适配，本项目自跑）＝ gold 上界 | **.1802** | .1143 | .1782 | .3124 | .4114 | .5823 |
| —— 以下两行测的**不是**事件预测，只作协议证据 —— | | | | | | |
| SimKGC（同上，**+ 候选句** ⇒ 吃捷径档） | .6373 | .5079 | .7395 | .8585 | .8926 | .9308 |
| `same_document`（只看文档归属的平凡对照） | .8041 | .6567 | .9596 | **1.0000** | 1.0000 | 1.0000 |

**在两边都读不到文档身份的那条轴上：本文构建图 `.1583` 是 SimKGC `.0563` 的 2.8 倍**，
且高于 frequency `.0378` 与 random `.0143`。
⚠️ 这是**单 seed**、且 SimKGC 的 batch 被显存压到 256（in-batch 负样本 1024→256，对比学习的
增益正从这里来）⇒ **这一行仍是 SimKGC 的下界**，结论要连着这条限制写。

### 这一轮真正买到的东西

一条**关于本地重建 CGEP-MAVEN 协议**的发现，它不依赖任何方法章成功，也不依赖 Ch6 胜出：

> 负采样跨文档而 ECG 不跨文档，两者叠加出一条 **Hit@10 = 1.000** 的捷径。
> 一个方法能不能用它，完全取决于它**读不读候选文本**——而这与它建不建模事件关系无关。
> ⇒ 在这个协议上跨族比较 MRR，比的可能根本不是事件预测。

原论文的派生数据未发布，**我们无法判断它是否也有这条**；只能如实说「我们的重建协议有，
而且我们把它量出来了」。这正好是 Ch6 作为**应用章 + 协议章**该交的东西。

---

## ★★★ CSProm-KG 收口：**结构性不兼容，不是能力差**（2026-09-18 凌晨，gpu-4090 card 0）

60 epoch 跑完（实测约 5.7 h，721 step/epoch），最佳 checkpoint 在 **epoch 53、`val_mrr=0.2907`**，
`trainer.test` dump 恰好 1,908 行。用我们自己的 evaluator 打分：

| 方法 | MRR | Hit@1 | Hit@3 | Hit@10 | Hit@20 | Hit@50 |
|---|---:|---:|---:|---:|---:|---:|
| **CSProm-KG（(b) 适配，60 epoch）** | **.0028** | **.0000** | **.0000** | **.0000** | **.0000** | **.0000** |
| （参照）random | .0143 | .0021 | .0089 | .0241 | .0414 | .0891 |

**每一个 Hit@k 都恰好是 0** ——512 个候选里金标**从来没进过前 50**。
乱猜的 Hit@50 是 50/512 ≈ 9.8% ⇒ 这**远低于随机，是系统性的**，不是噪声。

### 机制是量出来的，不是推的

上一节（E3.1 导出）事先预测过：**金标后继在训练图里 0/1,908 有边，而 6,892 个候选里 4,863 个有**，
而 CSProm-KG 的**输出层就是实体嵌入表**。逐候选统计证实了这条：

| 候选 | 平均排名（512 里，0 最好） | 数量 |
|---|---:|---:|
| **在训练图里有边的** | **195.0** | 688,136 |
| **没有边的** | **399.7** | 288,760 |
| **金标**（按构造 100% 属于后者） | **373.1** | 1,908 |

（乱排的期望是 255.5。）⇒ 见过的实体被系统性抬高约 **205 个名次**，
而**每一个正确答案都是没见过的**，于是被按住在后半程，Hit@50 恒为 0。

**内部对照证明模型本身没坏**：同一个 checkpoint 在 dev 切片上 **`val_mrr=0.2907`**，
而那是在**全部 33,017 个实体**里排——候选集大 64 倍，分数高 100 倍。
两者唯一的结构差别是：**dev 的尾实体在训练图里有边，测试集的金标没有。**

⚠️ **这不是训练不足**：没进任何训练三元组的实体**只作为负样本收梯度**（CE 覆盖全实体表），
所以**训多几个 epoch 只会把差距拉大**，不会缩小。`val_mrr` 从 ep2 的 .0011 → ep20 .0201 →
ep29 .0634 → ep53 .2907 一路在涨，而测试侧仍然是 0 —— 这两件事同时成立，正是上面那条机制。

### 因此这一行该怎么写

**「CSProm-KG 在 CGEP 上拿 .0028」是关于任务与模型族的结构性事实，不是关于 CSProm-KG 的质量。**
CGEP 的 query edge 规则要求尾节点 **outdeg 0 / indeg 1**，所以金标在自己的 ECG 里只有那一条边；
任何 triple 级切分都必须把它拿掉 ⇒ **任何通过「已学习的每实体嵌入」打分的方法，
在 CGEP 上都注定被推离正确答案**，与它在 KGC 上多强无关（它在 WN18RR 上有我们自测的 (a)：
MRR 0.572682）。论文里必须这样写，不得简写成「我们超过了 CSProm-KG」。

### 两个 KGC 对手朝相反方向失败，而**两种失败都不是关于事件预测的**

| 对手 | 分数 | 失败形态 | 根因（已量） |
|---|---:|---|---|
| **CSProm-KG** | **.0028** | 远低于随机，Hit@50 恒 0 | 按实体嵌入表打分；金标嵌入 0/1,908 被训过，只作为负样本收梯度 |
| **SimKGC（无 description）** | **.0563** | 高于随机、低于本文 | 文本双编码器，对未见实体归纳 ⇒ **不吃**上面那一刀 |
| SimKGC（+ 候选句） | .6373 | 看似大胜 | **91% 来自文档匹配**（top-1 同篇率 78.20%，均匀乱选 0.41%） |

⇒ 这一对正好把「输出层依不依赖已训练的实体嵌入」这个变量单独测了出来：
**同一个任务、同一批 query、同一个 evaluator，只换这一条，分数差 20 倍。**

### 表 6-2 · 本轮全部实测（冻结 unit `f75e7e87…`，n=1,908，全部走 `succession/metrics.py`）

| 方法 | MRR | Hit@1 | Hit@3 | Hit@10 | Hit@20 | Hit@50 |
|---|---:|---:|---:|---:|---:|---:|
| CSProm-KG[Chen+ 2023]（(b) 适配，⚠️ 结构性不兼容，见上） | .0028 | .0000 | .0000 | .0000 | .0000 | .0000 |
| random | .0143 | .0021 | .0089 | .0241 | .0414 | .0891 |
| frequency | .0378 | .0267 | .0273 | .0372 | .0718 | .1509 |
| SimKGC[Wang+ 2022]（(b) 适配，batch 256，无 description） | .0563 | .0183 | .0430 | .1279 | .2013 | .3375 |
| **本文构建图（predicted 上游 = v5 判别式抽取器）** | **.1583** | .1038 | .1530 | .2563 | .3580 | .5126 |
| **SeDGPL**[Zhan+ 2024]（(b) 适配，本项目自跑）＝ gold 上界 | **.1802** | .1143 | .1782 | .3124 | .4114 | .5823 |
| —— 以下两行测的**不是**事件预测，只作协议证据 —— | | | | | | |
| SimKGC（同上，**+ 候选句** ⇒ 吃捷径档） | .6373 | .5079 | .7395 | .8585 | .8926 | .9308 |
| `same_document`（只看文档归属的平凡对照） | .8041 | .6567 | .9596 | **1.0000** | 1.0000 | 1.0000 |

**三个公开方法到齐**（SeDGPL / CSProm-KG / SimKGC），满足名册 §5 的「不少于 3 个」；
三个都是 **(b) 透明适配**，差异逐条列在 `export_manifest.json` 与本页。

⚠️ **这张表能支持的论断，和不能支持的**：
- **能**：本文构建图在这批 query 上高于两个公开 KGC 对手与两个平凡对照；
  **而且两个对手的落后各有已量出的结构性解释**，不是「我们更强」；
- **不能**：任何「本文方法优于 CSProm-KG/SimKGC」的一般性陈述。
  它们没有一个实现 CGEP，适配是我们做的，两条失败路径都由**任务与模型族的错配**决定；
- **限制**：单 seed；SimKGC 的 batch 被显存压到 256（负样本 1024→256，是它增益的来源）；
  CSProm-KG 的 epoch 取 60（作者给 FB15k-237 的数，非本任务调出）。

### 产物与双端 sha256（本地与 4090 一致）

| 文件 | sha256 |
|---|---|
| `runs/cgep/e3_csprom.json` | `44fdaa80cafc2c37fdec28915c80fdc90fc8de12335425df01e5c457fbb5bc03` |
| `runs/cgep/e3_simkgc_nodesc.json`（主行） | `018a13a931e0fcd53dc4aea955be8bb68c42061924972fb22723901623d3a328` |
| `runs/cgep/e3_simkgc_nw000.json`（带候选句，关重排） | `48d2ff3e2a221ff09b31213e3a2f21dc17085aa9bc75fcdae5706df56c15b38f` |
| `runs/cgep/e3_simkgc_nw005.json`（带候选句，默认重排） | `b933f6ba31b56bac1d1851b954fd36a34e75982d513cf2cdbf04f87891892016` |
| `runs/cgep/e3_same_document.json` | 本地生成，`scripts/evaluate_cgep.py --predictor same_document` 可重跑 |

每份 JSON 都带 `fidelity`、`unit.sha256`、`evaluator` 与
`differences_from_the_published_setting` 全表——**表 6-2 的每一行都能反查到这五样**。
checkpoint 留在 4090（`CSProm-KG/logs/cgep_r1/`、`SimKGC/checkpoint/cgep_r1|cgep_nodesc/`），
按 `CLAUDE.md`「训在哪就留在哪」不回传。

---

## ★ E3.5 叙事闭环（2026-09-18，纯文字，无新实验）

E3 契约要求结论**只在证据范围内**表述。三条各自对应哪份证据，写在这里备查。

### 结论 1 · 本文构建图相对公开对手的位置

**可写**：在冻结的 1,908 个 query 上、由同一个 evaluator（`succession/metrics.py`）打分，
本文构建图（predicted 上游）**MRR .1583** 高于两个公开 KGC 对手
（SimKGC .0563 / CSProm-KG .0028）与两个平凡对照（frequency .0378 / random .0143）；
gold 上界 .1802 同时是 SeDGPL 自跑档。

**必须同时写**：两个对手的落后**各有已量出的结构性解释，都不是能力差**——
CSProm-KG 按实体嵌入表打分而金标在训练图里 0/1,908 有边；SimKGC 在允许读候选句时能到 .6373，
但那 91% 是文档匹配。**三个对手全是 (b) 透明适配，CGEP 不是它们任何一个的原任务。**

**不可写**：任何「本文方法优于 CSProm-KG / SimKGC」的一般性陈述。
**限制**：单 seed；SimKGC batch 1024→256；CSProm-KG epoch 60（作者给 FB15k-237 的数）。

### 结论 2 · 构建误差的下游代价，以及哪一类错误最伤

**可写**：`gold − predicted = −.0218`，占整张图全部下游价值（`gold − no_graph = .0991`）的
**22.0%**——「构建阶段丢掉了图对下游全部价值的两成」。
同幅度受控扰动下**拆节点（身份错误）−.0184 最伤** > 删边（召回损失）−.0081 >
增边（精度损失）−.0047；**打乱 temporal 恒为 0，且那是结构零而不是实测零**
（ECG 拓扑只读 causal+subevent，温度计上就没有这一格）。

**支撑它的正控**：`gold .1802 > rewired .1185 > no_graph .0811`，三者严格有序，
差距是本章噪声地板（±.003–.004）的一到两个数量级 ⇒ **消费者读的是边的正确性，不只是边的存在**。

**不可写**：把任何小于 ±.004 的图侧干预当效应（修复 +.0011、净化 −.0000、distance 选边 +.0009
全在地板内）。

### 结论 3 · 一致性 / 可重建性 / 下游三者不对齐——现在有**三对**

| 对 | 数字 | 含义 |
|---|---|---|
| **causal_scc ↔ R1** | ρ = **−0.064**（而 R1 ↔ R2 ρ = +0.783） | 一致性指标与可重建性几乎无关 |
| **R2 ↔ MRR**（本轮新测） | predicted 的 R2 query F1 只有 **.0795**，下游 MRR 却只掉 **12.2%** | 逐边精确匹配的严苛度传不到下游——拓扑边多 3.4 倍而模板预算只有 20 条（tmpl 15.9 → 24.0） |
| **协议层 ↔ 能力**（本轮新测） | `same_document` = .8041 / Hit@10 1.000 | 在这个协议上得分高，可能只说明它读了候选文本 |

⇒ 合起来是一句可以写进结论的话：**"图谱一致、可重建、下游有用"是三件不同的事，
我们分别量了它们，并且量出它们彼此不对齐。** 这条不依赖任何方法章成功。

### 本章新增的一条协议性发现（Ch6 作为应用章 + 协议章交的东西）

> 本地重建的 CGEP-MAVEN 里，**负采样跨文档而 ECG 从不跨文档**，两者叠加出一条
> **Hit@10 = 1.000** 的捷径。一个方法能不能用它，取决于它**读不读候选文本**，
> 与它建不建模事件关系无关。⇒ 在这个协议上跨族比较 MRR，比的可能根本不是事件预测。

原论文的派生数据（`MAVENSubWoRe.npy`）从未发布，**我们无法判断它是否也有这条**；
只能如实说「我们的重建协议有，而且我们把它量出来了，并给出了不受影响的比较轴」。

### Done when 逐条核对（`phases/PHASE_E3_graph_application.md`）

| 契约要求 | 状态 |
|---|---|
| evaluation unit manifest 冻结，gold/predicted 两档 ID 集逐位一致 | ✅ `f75e7e87…`，`upstream_registry.json` `status=closed` |
| identity/relation/factuality 读真实 bundle 或显式 fallback **并在表头标明身份** | ✅ 裁决 ② 取 (乙)，上游身份 = v5 判别式抽取器，已写进表头与 registry |
| 公开对手 ≥3，每个标 (a)/(b) 并列差异 | ✅ SeDGPL / CSProm-KG / SimKGC，全 (b)，差异逐条在 `export_manifest.json` |
| 平凡对照 + 无图/扰动对照 | ✅ random / frequency / **same_document（本轮新增）** / no_graph / rewired |
| 主表报 MRR 与 Hit@1/3/10/20/50 | ✅ 全部六列 |
| 构建损失 + 扰动曲线 + 配对 bootstrap + 噪声地板 | ✅ 已有实测，本轮直接引用 |
| 结论只在证据范围内 | ✅ 本节逐条写了「可写 / 必须同时写 / 不可写」 |
| **matched seeds 13/17/42** | ⛔ **未做**——多种子须逐次授权。**表 6-2 当前是单 seed，必须如实标注** |
