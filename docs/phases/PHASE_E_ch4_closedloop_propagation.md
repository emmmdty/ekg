# Phase E — Ch4 构建误差向下游的传播、归因与预算（headline）

> 单会话自包含契约。硬约束/校验命令见自动载入的 `CLAUDE.md`；设计见 `docs/SPEC.md` §1（Ch4）/§4。
> **这是全篇 headline。**
>
> ⚠️ **2026-07-29 本契约已按实测重写。** 原 headline 是「下游门控闭环修复」，验收线是
> 「repaired MRR > predicted MRR」。**该主张已被我们自己的实验否定并作废**（见 §0），
> 不得照旧执行。改动经作者拍板。

## 0. 先读：三条已经测出来的事实（决定本阶段怎么做）

1. **修复不提升下游，且天花板已被测出。** Phase B 真实图上 repaired 使 ECG 可重建率微降
   （R1 .7310→.7294、R2 f1 .0622→.0620）。2026-07-28 归因实验进一步定位：修复的
   **1.5 万次编辑中约 1.4 万次（temporal 相关）对下游按构造零影响** —— ECG 重建只读
   **causal+subevent** 拓扑（`succession/data/cgep.py`），与 temporal 闭包**正交**；真正动下游的
   只有 causal 环破除的 **858 条边**，代价 **R1 掉 3/1260（0.24%）**、收益 R2 tp +1。
   **不破 causal 环时下游与 raw 逐位相同**（但保留 661 个 causal SCC）。
   ⇒ 门控可挽回的上限 ≈ **0.24%**，撑不起 headline；**门控只对 causal 环破除有意义**，
   门控其余动作是空转。
2. **下游天花板由 Ch2 抽取器决定，不由修复决定**：R2 f1 绝对值仅 **.078**（P .164 / R .051）。
   这个水平上任何图侧策略差异都会被淹没。
3. **图侧干预在 SeDGPL 上普遍只有噪声级效应**：M1（距离选边）ΔMRR +0.005、M2（结构 bit）
   ΔMRR −0.0015/+0.0009，与修复归因同量级。**这是要被解释的现象，不是要被新机制撞开的墙。**

## Goal（完成目标）

① **三图误差分解与归因（headline 正文）**：在 **gold / predicted / repaired** 三张图上跑同一个 SeDGPL，
   把下游损失拆开，并**归因到具体的构建与修复动作**——哪类 node/edge/factuality 错误最伤 reachability、
   各自值多少下游损失。§0 的 causal-vs-temporal 归因是这套做法的样板，本阶段把它做全。
② **净化的下游判定（正面回答 Ch3 留下的问题）**：事实性净化（剔 CT− / 降权 PS−·Uu）对后继预测
   有无增益。**不得绕开**；无增益就如实报，Ch3 按止损口径退为「检测 + 预测图鲁棒性分析」。
③ **误差预算**：把各阶段校准不确定性经 union bound + 可达性合成端到端预算
   （`core/calibration/propagation.py`），与实测的三图损失曲线对照。

## 依赖 / 产物
- 前置：**Phase A·B**（真实预测图，已有）、**Phase C**（节点）、**Phase D**（事实性信号，已有）。
- **预测边 dump 已就位**：4090 `runs/factuality/predicted_edges_valid.jsonl`（710 篇 / 231,530 边，127M），
  **直接复用，不必重跑 GPU 抽取**。
- 产出：三图对比 + 归因表 + 误差传播曲线，落 `runs/cgep/ch4_propagation_*.json`。

## Context（复用 / 新建）
- **复用（大部分已建）**：`succession/`（`sedgpl.py`/`model.py`/`encode.py`/`linearize.py`/`selective.py`/
  `structure.py`/`predictor.py`/`metrics.py`/`reconstruction.py`）；`succession/cross_stage.py`
  （`induce_reachability:38`、`cross_stage_sweep:64`）；`core/calibration/propagation.py`；
  `scripts/evaluate_cgep*.py`、`build_cgep.py`、`consistency_repair_report.py`
  （**已带 `--no-close-temporal` / `--no-break-causal-cycles` 两个归因开关**）；
  `factuality/purification.py`（**已带 `random_drop_control` / `degree_matched_drop_control`**）。
- **新建**：三图评测编排；`cross_stage.py` 补 **3 类真实扰动生成器**（删/增因果边、并/拆节点、
  扰乱时序——现仅 reachability 掩码），用于画"哪类错误最伤下游"的曲线。

## 执行内容（Steps · TDD）
1. **三图 SeDGPL 评测**：gold / predicted / repaired 各跑一遍，报 MRR/Hits + R1/R2。
2. **归因**：用已有的两个开关（temporal 闭包 / causal 破环）+ 新增扰动生成器，把下游损失
   拆到具体动作上。**每个干预都要有等量强对照**（见 Constraints）。
3. **净化下游档**：purified-predicted 图上再跑一遍，回答 Goal ②。
4. **误差预算对照**：`propagation.py` 的解析预算 vs 实测曲线。

## Constraints
- 遵守 `CLAUDE.md` 硬约束；`tests/core/test_propagation.py` 测试锁不可改语义。
- **强对照是硬要求**（SPEC §4.5，来自 TACL 2406.01297 的实验 checklist）：删边类干预必须与
  **随机等量删边**比（随机删边本身是强基线，DropEdge ICLR'20）；剔点类干预必须与
  **度数匹配**的随机剔除比（均匀随机对低度数策略不公平，Ch3 实测差 3,573 条边）。
- **若保留任何门控实验档**：门控信号**不得直接用金标 MRR**（oracle 泄漏是致命设计缺陷），
  必须二选一——在线可得的无标签代理，或显式定位为离线构建期质检工具（SPEC §4.5）。
  且门控**只施于 causal 环破除**。
- 与 CFEP（TKG 纯预测）、self-healing KG（规则非下游验证）、**DeepRefine（2605.10488）**、
  **Kintsugi（2605.09487，verifier-gated KB editing + 保护性回归检查，"仅在下游改善时接受编辑"的
  直接先例）**、CauScientist（2601.13614）显式区分（SPEC §5）——**不得主张"下游门控接受"为新**；
  我们的 delta 是事件因果图 + reachability/conformal 预算 + **三图误差分解与归因**。

## 验收标准（Done when）— ✅ 2026-07-29 全部达成，数字见 `docs/TODO.md`「Phase E 实施」
- [x] **三图（gold/predicted/repaired）下游指标 + 误差传播曲线产出**，如实报（升降都报）。
      gold .1802 / predicted .1583 / repaired .1595；4 类受控扰动各一条曲线 + temporal 结构零。
- [x] **下游损失可归因到具体构建/修复动作**，每个干预附等量强对照。
      修复效果 100% 来自 causal 破环（= 损失的 5.1%），与 0 及等量随机删边**均不可分**。
- [x] **净化的下游增益正面回答**：**无增益**，可部署档 −.0001（p=.92）、oracle 档 −.0000（p=.97）。
- [x] 校验命令全绿（373 passed / 12 skipped、ruff 0、smoke OK）；结果落 `runs/cgep/` + 已回填 `docs/TODO.md`。
- [ ] ~~repaired MRR > predicted MRR~~ **已作废**：实测不成立且门控天花板仅 0.24%，
      不再作为门槛。**若 E 中出现该比较，只作为如实报告的一行，不作为成败判据。**

## GPU
重（SeDGPL 训练/推理）。选卡前 `nvidia-smi`；4090 标准授权，5090 须逐次问作者。

## 达不到怎么办（止损）
- **预期就是噪声级**（§0 第 3 条），所以"没有增益"不是失败，**是本阶段要交付的结论之一**——
  headline 是把误差**说清楚、归因清楚、预算对上**，不是把某个数推高。
- 若三图差异本身也小到无法归因 → 退**受控扰动版**（按可控幅度注入三类错误，画损失曲线），
  仍能回答"构建误差如何影响下游"，这是 headline 的合法退路。
- ⛔ **不得**为了让某个数变好而更换指标、放宽对照、或复活已作废的门槛。
