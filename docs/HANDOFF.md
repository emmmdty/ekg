# 交接文档 · 新会话从这里开始

> 更新于 **2026-09-04**。读完本文即可接手，不需要回溯对话。
> 文档分工：`.specify/memory/constitution.md` 管不可妥协原则，`docs/SPEC.md` 管 WHAT/WHY，
> `docs/RESEARCH_PLAN.md` 管可迭代 HOW，`docs/TASKS.md`/active phase 管执行；实验事实只认
> `docs/results/PHASE_*.md`。下层文档不得改写上层含义。本文只给状态与入口，**不复制数字**。

---

## 0. 三十秒摘要

- 课题仍是 occurrence-level 事件图谱：Ch1 身份消解、Ch2 关系抽取、Ch3 事实性、Ch4 下游代价。
- 唯一在跑确认性实验的 phase 仍是 `docs/phases/PHASE_A3_relation_balanced.md`，但已进入**终局分账与
  失败交接**，不再设计 Ch2 新方法；R1 中不读取 A3 待出结果的准备性任务可并行。
- **2026-09-04 关键变更**：4090 入口恢复，上一轮「状态 UNKNOWN」的两个远端结果已只读核验并入档：
  - **A3.2-r13 逐族×位置工作点 50ep = FAIL**（temporal 跌破护栏；且相对 r12 几乎无增量）
    ⇒ **工作点线两个核心设计周期用完，按契约封存，不开第三轮**；
  - **A3 检索竖片 r3 = Stage-1 FAIL**（此前从未入档）⇒ 近似 retriever 三连未过门，**不做第四个**。
- 因此 **A3 的下一正式动作不是新方法，而是 A3.6 官方配方分账**（rates / coref-aux / per-family selection）。
  剩余 official gap 里仍混着三个未拆开的训练协议变量；分账前上新机制会把协议差异记成方法功劳。
- A3.6 无论分数高低都只回答复现差距来自哪里，不恢复已耗尽的旧机制预算；完成后 A3 以
  `status=failed` 交给 R1 完成方法准入。原计划中的 pair-conditioned evidence 不在 A3 内继续执行。
- **质量目标不降**：稳定 SPEC 保留“三方法章 + 一系统评估章”和原主指标/强基线/三种子/CI 硬门；
  具体方法已移到可迭代的 `docs/RESEARCH_PLAN.md`，不再由 SPEC 框死。失败的是旧机制，不是方法章。
- **执行顺序有个硬依赖**：分账前必须基于当前 HEAD 重建 P1 trust root；而下面 §2 的两处代码整改
  会改动 `CODE_PATHS` 里的文件 —— **先整改、后重建、再跑分账**，否则要重建两次。
- 代码验证（本地，2026-09-04）：**470 passed / 24 expected skips**、ruff 0、CPU smoke OK。
- final-valid 未访问；没有新增 seed；没有跨机传 checkpoint、数据集或其他大文件。

---

## 1. 新窗口按这个顺序继续

### P0：入档与同步（无需 GPU，可直接执行）

1. **【已完成 2026-09-04】** r13 与 retriever r3 的真实数字、判定与 artifact hash 已写入
   `docs/results/PHASE_A.md` 末两节；`PHASE_A3` 契约的 A3.2-r13.2 / A3.3 已改为 FAIL 封存状态。
2. **【已完成 2026-09-04】** 上一轮 planning-file 清理、上下文同步与两份阶段报告以 `574f51d` 收口；
   本轮目标/SDD 审计与 P1 可追溯性整改随后按逻辑单元提交并推送，确切身份以当前 `git log` 为准。
3. 4090 代码同步（**已确认安全**：worktree clean，HEAD `e0ef69d` 是 `origin/main` 的祖先）：

   ```bash
   ssh gpu-4090 'cd /data/TJK/ekg && git fetch origin main && git reset --hard origin/main'
   ```

   ⛔ 不运行 `git clean -fdx`、不运行 `rsync --delete`、不在服务器运行 `uv run`/`uv sync`。
4. 5090 入口当前 `Connection refused`（cpolar 换端口）。需要它时先跑 `cpolar-ssh-update` 再重试；
   **5090 每次使用仍须逐次向作者取得授权**。它上面的大产物原地保留：
   C4 2×2 约 21 GB、D3 oracle 约 961 MB、A3 recipe smoke 约 2.0 GB。

### P1：代码整改（无需 GPU，**已实现且全量 gate PASS**）

两处都属 B 类可追溯性，不改结论但会让「别人能复现这张表」更硬。详见 §4。

1. trainer 已改为导入 `ekg.core.protocol` 的权威 manifest/split 实现；权威 helper 同时保留原 trainer
   对非字符串 ID 的 fail-fast 行为，并增加回归测试。
2. `src/ekg/core/protocol.py` 已加入 P1 `CODE_PATHS`；P1 受控 scripts 中的重复文件哈希 helper 已统一
   导入 `ekg.core.stage_bundle.sha256_file`。

验证：`uv run pytest` = 470 passed / 24 skipped，ruff 0，`uv run ekg-smoke` OK；P1 local gate PASS，
`tested_tree_sha256=3bff2ac2b5366ed06ebe81c9b2e549f0949216c832ad8e6098a6782e0c701d3c`。整改未改实验口径。

### P2：重建 P1 trust root，再做 Ch2 官方配方分账（需 GPU）

trainer 属于 P1 `CODE_PATHS`，P1 完成整改后必须基于当前 HEAD 重建 trust root，核实唯一差异
是预期代码。随后用**同一 seed 13、同一候选全集、同一训练预算**依次运行四臂：

1. 当前本地 recipe（对照底座）；
2. `--family-loss-rates`（官方 temporal/causal/subevent = 2/4/4）only；
3. rates + `--coref-aux-rate 0.4`；
4. rates + coref auxiliary + `--save-best-by-family`。

这四臂只分解剩余 official gap，属**复现修正，不是论文创新**。主指标继续用 official evaluator；
trainer macro、smoke 分数和不同 split 的论文数字都不能代替。

> ⚠️ **不得回收 r13 的既有曲线来「补」第 4 臂。** r13 的 `best_by_family` 里 temporal 恰好
> ≥ 护栏，但那是 macro 选模之外的另一根轴；看到某个选模规则能救分再改规则＝Phase C 已经
> 付过学费的「选模轴伪影」。第 4 臂必须从头完整重跑，其正当性来自 THU-KEG 官方配方本身。

### P3：完成 A3 失败交接，解除 R1 最终准入阻塞

A3.6 四臂完成后只做三件事：把真实结果写入 `docs/results/PHASE_A.md`；导出带
`status=failed`、可供 E3 消费的 relation bundle；允许 R1 完成 Ch2 brief 与跨产物准入。不得因任何一臂名义
超过主锚而把官方配方修正写成方法贡献，也不得继续 pair-conditioned evidence、第三个工作点或第四个
retriever。R1 按 `docs/replan/METHODOLOGY_REDESIGN_20260904.md` 冻结三章最近方法矩阵、ID 对齐、误差
因果图、MDE/power、最小有意义效应、消融和 protocol hash；缺任何一项都不进入 GPU 实现。

### P4：Ch1 / C5 当前候选方法

历史负结果只否定“context pooling + confusability”，没有测试方法所需的论元输入。5090 的
event-level gold argument oracle 证明有上限，但该标注复制给同 event 的每个 mention，泄漏 cluster
身份，**绝不能进入方法表**。下一实现必须使用 **mention-local predicted arguments**：

1. 复用公开 EAE/SRL 实现，不重写成熟抽取器；
2. 对两个 mention 做 role-aware 对齐，同时显式建模缺失、冲突和 argument confidence；
3. 保留 joint pair context，但论元和上下文做独立消融；
4. singleton-only 文档恢复实验按 optimizer steps/tokens 对齐，并固定 hard-negative 数量；
5. pair CE 与 cluster-risk objective 共用完全相同的 encoder/sampler。

“加入论元”“pair joint encoding”“cluster regularization”都已有先例。论文新颖点应落在
**不可靠 mention-local arguments 如何传播成 cluster-level 连边风险，以及怎样用不确定性抑制污染**。

### P5：Ch2 / A4 当前候选方法

A3 已否定 family workpoint 和三个近似 retriever，不得复活。A4 保持 official 全候选全集，为每个 pair
学习 evidence spans 与 sufficiency/abstention risk；检索和 hard negatives 只改变训练/evidence，不在推理
时裁掉候选。核心中介是跨句 causal FP 下降且 recall 非劣；2025 two-stage ERE、RESIJ/KnowQA/TacoERE
须按代码可得性和协议忠实度进入 baseline 矩阵，不能把不同 split 的论文数字直接当对手。

### P6：Ch3 / D4 当前候选方法与 E3 依赖

gold-evidence oracle 没有显示足以解释主指标差距的上限，下一方法不再单独堆 evidence extractor，而是
typed cue spans + `known/unknown → modality → polarity` 结构化分解。五类 macro-F1 仍是硬门，evidence、
校准和稀有类只作机制/护栏；internal-dev 功效不足先用预冻结 repeated split 或外部公开数据补强，不降 CI。

随后才进入 E3。历史 SeDGPL 正控证明“至少一个消费者确实读图”，但 E3 仍缺：冻结的本地重建 manifest、
三类真实 upstream bundle 接口、BART/text-only 与 frequency 的预测有效性门、同 backbone
frozen/fine-tuned 对照和完整 24 条件 factorial。因此 Ch4 当前是**部分证据成立，正式 phase 未开始**。

当前依赖计划为 `{A3 closure, R1 preparation} → R1 promotion → {C5, A4, D4} → E3`。花括号内按真实
数据依赖和资源动态排程，不属于 SPEC；不读取 A3 待出结果的文献/ID/功效审计、互不冲突的四臂或
工程 smoke 可以并行。不能绕过真实证据依赖提前产生
确认性结果；多种子仍须逐次授权。启动任何远端 GPU 命令前，必须先向作者
展示确切命令、cwd 与预期产物。

---

## 2. 证据入口

| 主题 | 权威入口 | 当前可用结论 |
|---|---|---|
| Ch2 工作点线终局 | `docs/results/PHASE_A.md` 的 A3.2-r13.2 节 | FAIL；两个核心周期用完；含「不得事后改判」警告 |
| Ch2 检索竖片 r1/r2/r3 | `docs/results/PHASE_A.md` 的 r1/r2/r3 三节 | Stage-1 三连 FAIL；瓶颈是跨句排序不是 k 容量 |
| Ch2 冻结主锚与复现底座 | `docs/results/PHASE_A.md` 的 A3.0 / A3.1 节 | 主锚 = 本地重跑的 official_joint；训练预算一项就值 causal +5.11 |
| Ch2 official recipe 开关 smoke | `docs/results/PHASE_A.md` 末节 | 接线通过；正式分账尚未跑，不能报分 |
| Ch1 采样×论元 2×2、locality | `docs/results/PHASE_C.md` 的 C4-r4 | 历史完整方法未被测试；event-level oracle 只作上限；local arguments 仍有信号 |
| Ch1 机制判定 | `docs/results/PHASE_C.md` 的 C4-r3 多种子节 | +0.4 不重现、符号翻转；本章方法贡献为零 |
| Ch3 同协议强 baseline | `docs/results/PHASE_D.md` 的 D3.0 节 | 五系统两两全平局；配对 MDE ≈ ±.051 |
| Ch3 gold evidence oracle | `docs/results/PHASE_D.md` 末节 | evidence 定位不是剩余主瓶颈；oracle 不可部署 |
| Ch4 下游代价 | `docs/results/PHASE_E.md` | 图依赖正控成立；构建损失是唯一确凿效应；图侧干预在噪声地板内 |
| 对手 split 口径审计 | `docs/replan/A_terrain.md`、`B_datasets.md`、`G_maven_causal_protocol_audit.md` | TacoERE/KnowQA/ProtoEM/GraphERE/RESIJ/LogicERE/MAQInstruct/LLMERE 已逐条核过，**不必重做综述** |

相关实现：

- Ch1：`scripts/train_coref_scorer.py`、`src/ekg/nodes/discriminative.py`、
  `scripts/report_coref_argument_locality.py`；
- Ch2：`scripts/train_supervised_relations.py` 的 recipe 开关与 by-family checkpoint、
  `scripts/train_relation_retriever.py`、`src/ekg/relations/balance.py`；
- Ch3：`src/ekg/factuality/detection.py`、`scripts/train_factuality_detector.py` 的
  `gold_evidence_oracle`；
- Ch4：`scripts/evaluate_cgep_propagation.py`、`src/ekg/succession/perturbation.py`；
- 测试：`tests/scripts/test_node_training_scripts.py`、`tests/relations/`、`tests/factuality/`。

---

## 3. 三端 Git 与文件状态（2026-09-04）

### 本地 WSL

- 路径：`/home/tjk/myProjects/masterProjects/ekg`，branch `main`。
- 470 passed / 24 expected skips、ruff 0、`ekg-smoke` OK。
- 24 个 skip 全部是 torch 缺失导致 —— **本地全绿不代表能在 GPU 上跑**，训练前必须小规模 GPU 往返验证。

### gpu-4090（主）

- 路径：`/data/TJK/ekg`。2026-09-04 **连通**，四张卡全空（0% util，各 18 MiB）。
- worktree clean；HEAD `e0ef69d` 是 `origin/main` 的祖先 ⇒ `git reset --hard origin/main` 安全。
- 当前**无 EKG 训练/评估进程**。r13 与 retriever r1/r2/r3 产物齐全，已入档。
- 正式 backbone 内容 pin：`/data/TJK/models/local/roberta-base/71be7419…c961ea9`。
  **只有绑定这个 pin 的结果才有资格进正式主表**；5090 上的结果一律 exploratory。
- P1 bundle 目录含 r12（当前可信根，`protocol.json` SHA-256 `0bd33e87…58497`）及历史 r3/r4/r9/r10/r11。

### gpu-5090（备）

- 路径：`/mnt/aidata/tongjiakai/ekg`。2026-09-04 `Connection refused`，需 `cpolar-ssh-update`。
- 上次已知：与 `origin/main` 一致、tracked clean、无进程。
- 大产物原地保留、不传输、不删除：C4 2×2 约 21 GB、D3 oracle 约 961 MB、A3 recipe smoke 约 2.0 GB。
- **每次新的 GPU 使用仍须逐次向作者说明命令、cwd、预计产物并取得允许。**

### 禁止的“整理”方式

- 不运行 `rsync --delete`、远端 `git clean -fdx`、宽目录递归删除；
- 不为了三端目录看起来相同而复制 `runs/`、数据集、模型 cache；
- checkpoint 训在哪就留在哪，跨机搬运前必须先问作者（单程约 70 分钟）；
- data/protocol 小文件确需复制时，用 `scp`/`rsync` 后做双端 SHA-256；
- 服务器不运行 `uv run`/`uv sync`，只用 `.venv/bin/python`。

---

## 4. 代码质量现状（2026-09-04 审计）

**整体偏高**：ruff（E/F/I/UP/B）全绿；`src/` 里零处用 `assert` 做校验；只有一个带 `noqa` 的宽
except；RNG 全部显式播种；无死模块；`EventNode` schema 未增字段；`tests/core/test_propagation.py`
测试锁在；`src/` 覆盖率 79%。已知问题按严重度：

1. **【本轮已整改】manifest split 单一事实源**：relation trainer 已删除影子实现并导入
   `src/ekg/core/protocol.py`；该依赖已加入 P1 `CODE_PATHS`，且非字符串 ID 继续 fail-fast。
2. **【本轮已整改受控面】文件哈希单一事实源**：P1 `CODE_PATHS` 覆盖到的 scripts 已统一导入
   `src/ekg/core/stage_bundle.py`。执行面和非 P1 报告脚本中的剩余重复不影响本次 trust root，后续只在
   修改对应脚本时顺手收敛，不为此扩大改动。
3. **出数字的脚本最没测试**：`scripts/` 覆盖率仅 **23%**，且这些是 0%：
   `report_relation_error_profile.py`、`report_ch4_budget.py`、`report_ch4_contrasts.py`、
   `evaluate_cgep_propagation.py`、`report_factuality_metric_power.py`、`evaluate_factuality.py`、
   `evaluate_relations.py`、`run_p1_local_gate.py`、`train_relation_retriever.py`。
   这类脚本出 bug 不会崩，会**产出一个看起来合理的错数字** —— Phase C 白跑两轮、Phase A 判错达标、
   Phase E 边序造出 p=0.02 假效应，都是这个形态。**给它们补黄金样例回归测试是最高杠杆的质量投入。**
   （好消息：最关键的 `scripts/score_maven_ere_official.py` 覆盖率 90%。）
4. **函数过长**：`train_supervised_relations.py:424 main()` 758 行，内嵌
   `save_checkpoint`/`dev_f1`/`rebuild_offsets` 三个闭包；`train_coref_scorer.py:109 train()` 16 个参数；
   全仓 35 个函数 ≥80 行或 ≥12 参数。ruff 未开 C901 故查不出。**不紧急**，但分账四臂最容易在这里出错。
5. **小事**：`scripts/report_ch4_budget.py`、`report_ch4_contrasts.py` 文件名带章节编号，与
   2026-07-27「代码内编号命名全改语义」的清理不一致；硬约束只点名 ch1/ch2/ch3，故不算违规。

---

## 5. 有效性红线与运行门

1. final-valid 不参与选模、阈值、结构或 stop decision；
2. manifest、候选全集、official evaluator、训练/推理 TIMEX 开关必须成对一致；
3. 单种子先过 baseline 和护栏；**未经作者新的明确授权，不增加 seeds 17/42**；
4. 训练前先纯逻辑测试、变异/方向测试、CPU/小样本 smoke，再做 GPU 2–3 epoch probe；
5. 数字只写对应 `docs/results/PHASE_*.md`；HANDOFF/TODO 只引用结论和位置；
6. oracle 必须标为 non-deployable upper bound，不能进入公开方法比较；
7. **SSH 失败是第三态，不等于远端进程结束**；只有成功 ssh 读到进程 GONE 才算结束；
8. 任何低于同协议多个强 baseline 的 Ch1–Ch3 方案都不能作为方法章贡献；
9. **看到某个选模/报数规则能救分再去改规则 = 用 dev 调参**，一律不允许（Phase C 教训）。

改代码后必须跑：

```bash
uv run pytest
uv run ruff check src tests scripts
uv run ekg-smoke
```

---

## 6. 新颖性边界（面向 2027-06 毕业，剩约 9 个月）

已有工作已经覆盖：显式 event arguments、两个 mention 的 joint encoding、cluster regularization、
retriever→cross-encoder、普通 arguments/relations factuality augmentation、modality/factuality 联合建模。
因此不要把组件名当创新。

v6.1 的研究主线是：

> **Evidence adequacy and risk-aware event graph construction**：Ch1 处理 argument uncertainty→cluster
> risk，Ch2 处理 pair evidence→relation sufficiency，Ch3 处理 typed cues→unknown/modality/polarity，
> Ch4 量化三种风险对消费者的边际与交互代价。

### 目标一致性裁决

- **理想目标与 v6.1 交付目标一致**：均为三个高质量方法章 + 一个系统评估章，不预设降为两方法章。
- **不一致发生在旧机制层**：Ch2 的 workpoint/retriever、Ch1 未实现的本地论元、Ch3 pooled evidence
  表示没有覆盖中心假设；继续原路线才会在有时间的情况下主动降低论文质量。
- **解决方式**是保留硬门并重开方法论设计：A3 失败身份不变；R1 冻结真正不同的新方法家族。一个新
  家族两周期失败仍要止损，但先回 R1 寻找有文献和错误证据支撑的替代机制；只有证明合理范围内不可实现
  时，才由作者和导师决定是否改纲，执行代理不得自动降标。

时间纪律：时间用于文献忠实复现、功效设计、可证伪方法和必要消融，不用于更大 backbone 掩盖机制或
无穷扫参。联网与学校标准审计已写入 `docs/replan/METHODOLOGY_REDESIGN_20260904.md`；R1 继续维护到
2026–2027 的一手论文增量。
