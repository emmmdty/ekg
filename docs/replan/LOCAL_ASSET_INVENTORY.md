# 本地资产清点（「重构 vs 重开」的本地侧输入）

> 2026-08-25 实测统计。外部地形由五路探索代理并行调查，本文件只回答一个问题：
> **如果换方向，现有的东西有多少能带走？**
> 结论只陈述事实与迁移成本，**不做方向推荐**。

## 1. 代码分层与可迁移性

`src/ekg` 共 **73 个 .py / 9,962 行**。按「换方向后的命运」分三层：

### Tier 1 — 任务与数据集无关，几乎原样可带走（约 2,263 行）

| 模块 | 行数 | 内容 | 迁移成本 |
|---|---|---|---|
| `core/calibration/` | 974 | ACI / weighted CP / CRC / split conformal / 风险传播预算 | **零**。纯统计原语，不含任何事件/NLP 概念（唯一提到 event 的是 `propagation.py` 的注释） |
| `core/eval/` | 536 | MUC / B³ / CEAFe / BLANC 共指指标、关系 P/R/F1、一致性、ranking、faithfulness | **近零**。MUC 那套是标准共指指标，任何共指数据集通用；文件里 MAVEN 只出现在 docstring |
| `core/` 其余 | 577 | schema / io / graph / registry / config | **低**。`RelationType` 枚举写死了 MAVEN-ERE 的四关系族，换本体要改；其余通用 |
| `agents/` | 176 | Agent / Blackboard / Stage / Orchestrator / Verifier 基底 | **零**（阶段无关设计） |

> ⚠️ `agents/` 有 176 行但 **0 个测试**（`tests/agents/` 为空）。它是唯一没有测试覆盖的模块。

### Tier 2 — 方法可迁移，数据层要重写（约 2,612 行）

| 模块 | 行数 | 内容 | 迁移成本 |
|---|---|---|---|
| `nodes/` | 1,035 | 事件检测、共指判别（难例）、canonical 化、span 编码 | **中**。方法与 MAVEN 无关，但 loader 与本体绑定 |
| `factuality/` | 954 | 事实性检测、evidence 定位、指标 | **中**。5 类标签体系是 MAVEN-FACT 的 |
| `relations/` | 623 | 文档级候选对构造、判别式对分类、一致性解码、CRC 边准入 | **中**。`pairs.py` 的候选口径与关系族绑定 |

### Tier 3 — 与 MAVEN + SeDGPL 强绑定（2,148 行）

`succession/`（13 文件）：CGEP 实例重建、DsGL 线性化、EeCE/ScEP 模型、ECG 可重建率、
受控扰动库、三图接入点、跨阶段扫描。**换方向基本作废**，除非新方向仍做「事件图 → 后继事件预测」。
其中 `perturbation.py`（受控构建误差注入）与配套的配对 bootstrap 方法学是**思路可带走、代码要重写**。

### 数据层耦合面（实测）

29/73 个文件提到 MAVEN，但**集中度很高**：`relations/data/maven_*.py` 与 `succession/data/cgep.py`
四个文件占了 42 次提及中的大头，其余多是 docstring。**说明数据适配层是干净隔离的** ——
这一点已被 `relations/data/ccks_causal.py` 反向验证：中文 CCKS 金融因果数据被归一化进同一套
`EventNode` / `RelationEdge` schema，复用同一条关系流水线与指标。**跨数据集/跨语言的抽象是成立的、已跑通过。**

## 2. 数据资产（已下载并归一化，15 个 processed 数据集）

**这是被低估的一块** —— 下载、清洗、切分核验是以周计的工作量，且部分数据集获取有门槛。

| 数据集 | 体量 | 备注 |
|---|---|---|
| DocEE | 485M | 文档级事件抽取，**当前项目从未用过** |
| MAVEN-FACT / MAVEN-ERE / MAVEN-Arg | 164M / 132M / 109M | 主线在用 |
| Astock | 75M | 已判死路（股票预测） |
| ICEWS18 / 05-15 / 14 | 20M / 13M / 2.8M | 旧 TKG 线，已冻结 |
| CCKS 金融因果（中文） | 12M | **已归一化进主 schema，loader 在** |
| event_graph_zh | 9.5M | 仅 12 节点 stub，无效 |
| CMIN-CN（中文） | 7.2M | 未接线 |
| ModaFact | 4.7M | 事实性相关 |
| FinDKG / it_happened | 3.7M / 3.5M | |

`data/raw/` 另有 **ECB+、RAMS、WikiEvents、MATRES、SeDGPL-ESC** 等尚未全部归一化的原始数据。

> ⚠️ 上面每一条只是「文件在磁盘上」。**split 合规性、是否正版、计数是否正确未在本次清点中复核** ——
> 历史上这里出过问题（ICEWS14 必须用 timestamps 计数切分、Astock 计数 bug、event_graph_zh 是 stub）。
> 真要用哪个，须单独核。

## 3. 工程与方法学资产（与方向无关，最值得保留的一块）

- **354 passed / 12 skipped**，本次实跑确认（`exit=0`）。测试分布：succession 111 / relations 71 /
  core 61 / nodes 40 / scripts 40 / factuality 35 / **agents 0**。
- **25 个功能命名的 CLI 脚本**（build / train / evaluate / report 四类），含
  `score_maven_ere_official.py`（接官方评测器）与 `report_coref_error_profile.py`
  （自带对官方 `evaluate.py` 的双向强制交叉校验，不过就 `SystemExit`）。
- **文档制度**：单一事实源（数字只在 `docs/results/PHASE_X.md` 权威）、阶段契约、归档索引、
  三端流水线规范、工程坑记录。这套制度本身值钱 —— 它是四次口径混用事故换来的。
- **方法学纪律**（这批经验换方向也完全适用）：
  - canonical 序（实测纯重新序列化能造出 p=.02 的假效应）
  - 配对 bootstrap + 实测噪声地板（±.003–.004）作为「能不能下正面主张」的门槛
  - 强对照要求（修复类比随机等量删边、净化类比**度数匹配**随机剔除）
  - oracle 信号泄漏红线（不得用金标当在线门控信号）
  - no-op 起步（给已调好的编码器加新流必须 zero-init + 残差，否则指标腰斩）
  - 口径三轴对齐（评分器 / 文档集 / 校正），报差值前必须逐条核

## 4. 三条给决策用的事实

1. **通用层（Tier 1，2,263 行）与工程制度换方向零损耗**，这部分不构成"重开"的成本。
2. **真正会作废的是 Tier 3 的 2,148 行**（succession），以及 Tier 2 的数据适配层。
   即「重开」的实际代码损失约 **2,000–3,000 行**，不是 9,962 行。
3. **数据资产与 schema 抽象已被跨语言验证过一次**（CCKS 中文金融因果走通同一条流水线），
   这降低了换数据集的风险，但**不降低换任务的风险** —— 换任务作废的是 Tier 3 与全部实验结论。
