# 交接文档 · 新会话从这里开始

> 更新于 **2026-09-04**。读完本文即可接手，不需要回溯对话。
> 冲突优先级：`docs/results/PHASE_*.md`（事实）> `docs/SPEC.md`（约束）>
> active phase > `docs/TODO.md` > 本文。本文只给状态、证据入口和下一步，**不另造结果口径、不复制数字**。

---

## 0. 三十秒摘要

- 课题仍是 occurrence-level 事件图谱：Ch1 身份消解、Ch2 关系抽取、Ch3 事实性、Ch4 下游代价。
- 唯一正式 active phase 仍是 `docs/phases/PHASE_A3_relation_balanced.md`。
- **2026-09-04 关键变更**：4090 入口恢复，上一轮「状态 UNKNOWN」的两个远端结果已只读核验并入档：
  - **A3.2-r13 逐族×位置工作点 50ep = FAIL**（temporal 跌破护栏；且相对 r12 几乎无增量）
    ⇒ **工作点线两个核心设计周期用完，按契约封存，不开第三轮**；
  - **A3 检索竖片 r3 = Stage-1 FAIL**（此前从未入档）⇒ 近似 retriever 三连未过门，**不做第四个**。
- 因此 **A3 的下一正式动作不是新方法，而是 A3.6 官方配方分账**（rates / coref-aux / per-family selection）。
  剩余 official gap 里仍混着三个未拆开的训练协议变量；分账前上新机制会把协议差异记成方法功劳。
- **执行顺序有个硬依赖**：分账前必须基于当前 HEAD 重建 P1 trust root；而下面 §2 的两处代码整改
  会改动 `CODE_PATHS` 里的文件 —— **先整改、后重建、再跑分账**，否则要重建两次。
- 代码验证（本地，2026-09-04）：**470 passed / 24 expected skips**、ruff 0、CPU smoke OK。
- final-valid 未访问；没有新增 seed；没有跨机传 checkpoint、数据集或其他大文件。

---

## 1. 新窗口按这个顺序继续

### P0：入档与同步（无需 GPU，可直接执行）

1. **【已完成 2026-09-04】** r13 与 retriever r3 的真实数字、判定与 artifact hash 已写入
   `docs/results/PHASE_A.md` 末两节；`PHASE_A3` 契约的 A3.2-r13.2 / A3.3 已改为 FAIL 封存状态。
2. 提交当前工作树。脏文件为上一轮的 planning-file 清理（`task_plan.md`、`findings.md`、
   `progress.md`、`.claude-session-handoff.txt` 删除）＋ `AGENTS.md`/`CLAUDE.md`/本文同步
   ＋ `docs/reports/` 两份阶段性报告。按逻辑单元分次提交，不强推。
3. 4090 代码同步（**已确认安全**：worktree clean，HEAD `e0ef69d` 是 `origin/main` 的祖先）：

   ```bash
   ssh gpu-4090 'cd /data/TJK/ekg && git fetch origin main && git reset --hard origin/main'
   ```

   ⛔ 不运行 `git clean -fdx`、不运行 `rsync --delete`、不在服务器运行 `uv run`/`uv sync`。
4. 5090 入口当前 `Connection refused`（cpolar 换端口）。需要它时先跑 `cpolar-ssh-update` 再重试；
   **5090 每次使用仍须逐次向作者取得授权**。它上面的大产物原地保留：
   C4 2×2 约 21 GB、D3 oracle 约 961 MB、A3 recipe smoke 约 2.0 GB。

### P1：代码整改（无需 GPU，**必须在重建 P1 trust root 之前完成**）

两处都属 B 类可追溯性，不改结论但会让「别人能复现这张表」更硬。详见 §4。

1. `scripts/train_supervised_relations.py:267,278` 有 `load_manifest_ids` /
   `split_docs_by_manifests` 的**逐字影子拷贝**，没有 import `src/ekg/core/protocol.py`；
   而 coref / factuality / retriever 三个训练器都是正经导入的。改为导入权威实现。
   **⚠️ 连带动作**：改完必须把 `src/ekg/core/protocol.py` 加进
   `scripts/build_p1_bundle.py:25` 的 `CODE_PATHS`，否则 bundle 钉住了 trainer 却没钉住它
   依赖的切分逻辑 —— 正是该常量上方注释警告的失败形态。
2. `sha256_file` / `_sha256` 在 scripts 下重复定义 **12 次**，而
   `src/ekg/core/stage_bundle.py:27` 已有权威实现（`train_supervised_relations.py:33` 甚至
   已从 `stage_bundle` 导入别的符号）。至少把 `CODE_PATHS` 覆盖到的文件收敛到一份实现。

验证：`uv run pytest`（≥470 passed）、`uv run ruff check src tests scripts`、`uv run ekg-smoke` 全绿。
行为必须逐位不变：整改只允许删重复，不允许改语义。

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

### P3：分账清零后，Ch2 才进入最后一个核心周期

现有诊断把 causal 剩余错误锁定为跨句 false positives（FP 占全部 causal 错误 83.6%，其中
78.4% 跨句；方向反转只占漏报 1.4%）。下一候选是
**pair-conditioned evidence sentence selection + family×position hard-negative balance**，要求：

- official candidate universe 保持完整，selection 不能偷偷改评估候选；
- 同时报告 evidence recall@k、候选压缩率、same/cross precision/recall 和 official 三族 F1；
- 先用手造样例验证 pair-specific 选择与位置桶，再 2–3 epoch 行为 smoke；
- **不再复活**：连接词、句距、窗口覆盖、第四个近似 retriever、prototype、ATLoss 调参、
  第三个工作点。

retriever→cross-encoder 已有文献，不能单独当创新。可争取的新颖点是：在**完整候选口径**下
联合约束 pair-specific evidence sufficiency、跨句误报风险与 relation-family balance。
⚠️ 难度警告：跨句 causal 漏报在冻结主锚上同样是 70.2%，KnowQA 的跨句 F1 也只有 12.5–40%
（见 `docs/results/PHASE_A.md` 与 `docs/replan/G_maven_causal_protocol_audit.md`）——
这是任务硬核，攻下来是真贡献，但不要低估。

### P4：Ch1 做真正可部署的完整版本

历史负结果只否定“context pooling + confusability”，没有测试冻结设计要求的论元输入。5090 的
event-level gold argument oracle 证明有上限，但该标注复制给同 event 的每个 mention，泄漏 cluster
身份，**绝不能进入方法表**。下一实现必须使用 **mention-local predicted arguments**：

1. 复用公开 EAE/SRL 实现，不重写成熟抽取器；
2. 对两个 mention 做 role-aware 对齐，同时显式建模缺失、冲突和 argument confidence；
3. 保留 joint pair context，但论元和上下文做独立消融；
4. singleton-only 文档恢复实验按 optimizer steps/tokens 对齐，并固定 hard-negative 数量；
5. pair CE 与 cluster-risk objective 共用完全相同的 encoder/sampler。

“加入论元”“pair joint encoding”“cluster regularization”都已有先例。论文新颖点应落在
**不可靠 mention-local arguments 如何传播成 cluster-level 连边风险，以及怎样用不确定性抑制污染**。

### P5：Ch3 不再单独堆 evidence extractor

gold-evidence oracle 的名义提升小于 internal-dev 的可检测差，PS−/CT− 没有同步改善，Uu 仍近零。
瓶颈已从“找不到 evidence”定位到“证据被压成一个向量后标签头无法表达语义结构”。下一候选是
typed cue + sufficiency：分开表示否定 / 可能性 / 条件 / 来源承诺 / 作用域；用
evidence-sufficiency / unknown gate 单独判 Uu，再在信息充分条件下判 polarity×modality；
arguments/relations 只作内容输入与对照。internal-dev 稀有类功效不足，必须保留 document-cluster
paired CI，并同时报告样本更多的 evidence 轴。

### P6：并行是允许的，别把三张空卡晾着

4090 四张卡当前全空。`CLAUDE.md` 的 C 类条款明确：**卡空着就并行**，「每次只跑一个实验任务」
保护的是资源不打架，不是结论正确性。P2 的四臂是串行分账（占一张卡），
P4 / P5 是不同方案，可在其余空卡并行。
⛔ **但 GPU 并行只用于不同方案/任务，不得用于未授权的多种子**；启动任何远端 GPU 命令前，
必须先向作者展示确切命令、cwd 与预期产物。

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

1. **单一事实源被破坏（P1 已排期）**：`scripts/train_supervised_relations.py` 影子实现了
   `src/ekg/core/protocol.py` 的切分逻辑。今天两份行为等价（影子版多一个 isinstance 检查），
   **未污染已有数字**，但该模块 docstring 写明「三份同样的实现正是 split drift 的起点」。
2. **`sha256_file` 12 份重复定义（P1 已排期）**：哈希是 B 类可追溯的地基。
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

当前较连贯的论文主线是：

> **Evidence adequacy and risk-aware event graph construction**：Ch1 处理 argument uncertainty→cluster
> risk，Ch2 处理 pair-specific evidence→cross-sentence FP，Ch3 处理 typed cues→unknown sufficiency，
> Ch4 量化这些构建错误对消费者的代价。

现状是**四章无一在主指标上超过多个同协议公开方法**，Ch4 的图依赖正控结论最硬。
时间纪律：先在 2026 年内分别用一个冻结 seed 证伪/保留 Ch1–Ch3 三个机制；没有清晰主指标增益
就及时降级，不要继续扩 backbone、数据集或无穷消融。正式锁定 novelty claim 前必须再做一次
2026–2027 一手论文检索（§2 已有的审计可复用，不必从零重做）。
