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
