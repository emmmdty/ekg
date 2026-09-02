# 交接文档 · 新会话从这里开始

> 更新于 **2026-09-02**。读完本文即可接手，不需要回溯对话。
> 冲突优先级：`docs/results/PHASE_*.md`（事实）> `docs/SPEC.md`（约束）>
> active phase > `docs/TODO.md` > 本文。本文只给状态、证据入口和下一步，不另造结果口径。

---

## 0. 三十秒摘要

- 课题仍是 occurrence-level 事件图谱：Ch1 身份消解、Ch2 关系抽取、Ch3 事实性、Ch4 下游代价。
- 当前唯一正式 active phase 仍是 `docs/phases/PHASE_A3_relation_balanced.md`。工作点第一周期、检索近似、
  prototype 与 ATLoss 已按门封存；第二周期的 4090 最终状态待核。
  **下一正式动作是先核 4090 遗留任务，再做 Ch2 官方训练配方分账**。
- 本轮修正了三个关键判断：Ch1 历史方法漏掉论元；Ch2 剩余 gap 混有官方训练协议差异；Ch3 即使
  提供 gold evidence，现有 pooling/head 仍解决不了 PS−/Uu。细节只见对应结果档末节。
- 本轮研究代码与结果已闭合到 **`f75c711`**（其后的提交只更新交接状态）。代码验证：
  **469 passed / 24 expected skips**、ruff 0、CPU smoke OK。
- final-valid 未访问；没有新增 seed；没有跨机传 checkpoint、数据集或其他大文件。
- 5090 已与 GitHub `main` 对齐，tracked worktree clean，当前无训练/评估进程。
- 4090 于 2026-09-02 仍在 SSH banner 阶段超时；它的 Git 和旧进程状态均为 **UNKNOWN**，不得写成结束。
- 根目录 `AGENTS.md`、`CLAUDE.md`、`findings.md`、`progress.md`、`task_plan.md` 有用户既存修改；
  **保留，不覆盖、不提交。本轮用户明确说不用 planning-with-files。**

---

## 1. 新窗口按这个顺序继续

### P0：先闭合三端状态，不跑新训练

1. 连接 4090；只有成功 SSH 后才检查 `git status`、HEAD、`ps`、`nvidia-smi` 和旧 A3 r13 流水线产物。
2. 若旧 50-epoch position-workpoint 已结束，先核 return code、official evaluator、candidate/manifest/hash，
   如实写入 `docs/results/PHASE_A.md`；无 official 产物就不能推断分数。
3. 远端存在 tracked 修改时先停下审计，不能直接 reset；clean 时才可
   `git fetch origin main && git reset --hard origin/main`。绝不运行 `git clean -fdx` 或 `rsync --delete`。
4. 代码只走 Git。数据、checkpoint、`runs/`、模型 cache 不自动跨机；任何大文件传输先报告
   源/目标/大小/用途并询问作者。

### P1：Ch2 先分账复现协议，再改方法

当前 trainer 已新增三个独立开关：

- `--family-loss-rates`：官方 temporal/causal/subevent = 2/4/4；
- `--coref-aux-rate`：官方 coreference auxiliary rate = .4；
- `--save-best-by-family`：三族分别选择 checkpoint。

5090 CUDA smoke 已证明接线和落盘正确，但 1 epoch 分数没有研究含义。因为 trainer 属于 P1
`CODE_PATHS`，正式运行前必须基于当前 HEAD 重建 P1 trust root，核实唯一差异是预期代码，然后用
同一 seed 13、同一候选全集依次运行：

1. 当前本地 recipe；
2. rates-only；
3. rates + coref auxiliary；
4. rates + coref auxiliary + per-family checkpoint selection。

这四臂只分解剩余 official gap，属于**复现修正，不是论文创新**。先确认各变量贡献，才能把剩余差距
归给表示。正式主指标继续用 official evaluator；trainer macro、smoke 分数和不同 split 论文数字不能代替。

### P2：协议差异清零后，Ch2 才进入新方法

现有诊断把 causal 剩余错误锁定为跨句 false positives：precision 明显低于同句，而 recall 差较小。
下一候选应是 **pair-conditioned evidence sentence selection + family×position hard-negative balance**，要求：

- official candidate universe 保持完整，selection 不能偷偷改评估候选；
- 同时报告 evidence recall@k、候选压缩率、same/cross precision/recall 和 official 三族 F1；
- 先用手造样例验证 pair-specific 选择与位置桶，再 2–3 epoch 行为 smoke；
- 不再复活连接词、句距、窗口覆盖、第四个近似 retriever、prototype 或 ATLoss 调参。

retriever→cross-encoder 已有文献，不能单独当创新。可争取的新颖点是：在**完整候选口径**下联合约束
pair-specific evidence sufficiency、跨句误报风险与 relation-family balance。

### P3：Ch1 做真正可部署的完整版本

历史负结果只否定“context pooling + confusability”，没有测试冻结设计要求的论元输入。5090 的
event-level gold argument oracle 证明有上限，但该标注复制给同 event 的每个 mention，泄漏 cluster
身份，绝不能进入方法表。

下一实现必须使用 **mention-local predicted arguments**：

1. 复用公开 EAE/SRL 实现，不重写成熟抽取器；
2. 对两个 mention 做 role-aware 对齐，同时显式建模缺失、冲突和 argument confidence；
3. 保留 joint pair context，但论元和上下文做独立消融；
4. singleton-only 文档恢复实验按 optimizer steps/tokens 对齐，并固定 hard-negative 数量；
5. pair CE 与 cluster-risk objective 共用完全相同的 encoder/sampler，避免把训练量当机制收益。

“加入论元”“pair joint encoding”“cluster regularization”都已有先例。论文新颖点应落在
**不可靠 mention-local arguments 如何传播成 cluster-level 连边风险，以及怎样用不确定性抑制污染**。

### P4：Ch3 不再单独堆 evidence extractor

gold-evidence oracle 的名义提升小于 internal-dev 的可检测差，而且 PS−/CT−没有同步改善，Uu 仍接近零。
这已把瓶颈从“找不到 evidence”进一步定位到“证据被压成一个向量后，标签头无法表达语义结构”。

下一候选是 typed cue + sufficiency：

- 分开表示否定、可能性、条件、来源承诺与作用域，不再把所有 token sigmoid 加权平均；
- 用 evidence-sufficiency / unknown gate 单独判 Uu，再在信息充分条件下判 polarity×modality；
- arguments/relations 只作为内容输入与对照，不能声称它们本身是创新；
- internal-dev 稀有类功效不足，必须保留 document-cluster paired CI，并同时报告样本更多的 evidence 轴。

---

## 2. 本轮新证据入口

| 主题 | 权威入口 | 当前可用结论 |
|---|---|---|
| Ch1 采样×论元 2×2、locality | `docs/results/PHASE_C.md` 的 C4-r4 | 历史完整方法未被测试；event-level oracle 只作上限；local arguments 仍有信号 |
| Ch2 official recipe 开关 smoke | `docs/results/PHASE_A.md` 末节 | 接线通过；正式分账尚未跑，不能报分 |
| Ch3 gold evidence oracle | `docs/results/PHASE_D.md` 末节 | evidence 定位不是剩余主瓶颈；oracle 不可部署 |
| Ch4 下游代价 | `docs/results/PHASE_E.md` | 图依赖正控已经成立，后续按 SPEC 扩完整 factorial |

相关实现：

- Ch1：`scripts/train_coref_scorer.py`、`src/ekg/nodes/discriminative.py`、
  `scripts/report_coref_argument_locality.py`；
- Ch2：`scripts/train_supervised_relations.py` 的 recipe 开关与 by-family checkpoint；
- Ch3：`src/ekg/factuality/detection.py`、`scripts/train_factuality_detector.py` 的
  `gold_evidence_oracle`；
- 测试：`tests/scripts/test_node_training_scripts.py`、`tests/relations/`、`tests/factuality/`。

本轮提交谱系：

```text
c45eb71  Ch1 sampling repair + argument oracle
7ac24a3  Ch1 oracle 对齐冻结 manifests
7840b5f  Ch2 official recipe variables
a1d4ae6  Ch3 explicit gold-evidence oracle
0db7923  Ch1 sampling diagnostics wording
5e40b62  Ch1 official predictions export
618f5ec  Ch1 mention-local argument audit
b2ab8a7  Ch2 official recipe CUDA smoke record
f75c711  Ch3 gold-evidence upper-bound record
```

---

## 3. 三端 Git 与文件状态（2026-09-02）

### 本地 WSL

- 路径：`/home/tjk/myProjects/masterProjects/ekg`
- branch：`main`，与 `origin/main` 一致；本轮研究代码/结果截至 `f75c711`。
- 用户既存 dirty 文件：`AGENTS.md`、`CLAUDE.md`、`findings.md`、`progress.md`、`task_plan.md`。
- 本轮 Ch1 locality 小结果约 12 KB，位于
  `runs/stages/C4/c4-v6-rootcause-r4/exploratory/`；不需要从服务器搬模型。

### gpu-5090

- 路径：`/mnt/aidata/tongjiakai/ekg`
- branch：`main`，与 `origin/main` 一致；tracked worktree clean；无训练/评估进程。
- Ch1 2×2 唯一模型存档：`runs/stages/C4/c4-v6-rootcause-r4/exploratory/2x2/`，约 **21 GB**。
- Ch3 oracle：`runs/stages/D3/d3-v6-evidence-oracle-r1-exploratory/`，约 **961 MB**。
- Ch2 recipe smoke：`runs/stages/A3/a3-v6-recipe-accounting-r1-exploratory/`，约 **2.0 GB**。
- 上述目录均已在对应 `docs/results/` 记录日志/报告 hash；**原地保留，不传输、不删除**。
- 5090 cpolar 会断。长任务必须 `setsid nohup`、独立 log/rc，一条 SSH 只发一个后台任务。
- 5090 每次新 GPU 使用仍须逐次向作者说明命令、cwd、预计产物并取得允许。

### gpu-4090

- 路径：`/data/TJK/ekg`。
- 2026-09-02 检查在 SSH banner 阶段超时；HEAD/worktree/进程/产物状态全部 UNKNOWN。
- 上次已知有 A3 position-workpoint seed-13 50-epoch 流水线，但当前不能声称仍在跑或已经结束。
- 恢复连接后先只读核验；若发现 remote-only 产物或 tracked 修改，先记录再决定同步。

### 禁止的“整理”方式

- 不运行 `rsync --delete`、远端 `git clean -fdx`、宽目录递归删除；
- 不为了三端目录看起来相同而复制 `runs/`、数据集、模型 cache；
- checkpoint 训在哪就留在哪。跨机搬运前必须先问作者；
- data/protocol 小文件确需复制时，用 `scp`/`rsync` 后做双端 SHA-256；
- 服务器不运行 `uv run`/`uv sync`，只用 `.venv/bin/python`。

---

## 4. 有效性红线与运行门

1. final-valid 不参与选模、阈值、结构或 stop decision；
2. manifest、候选全集、official evaluator、训练/推理 TIMEX 开关必须成对一致；
3. 单种子先过 baseline 和护栏；未经作者新的明确授权，不增加 seeds 17/42；
4. 训练前先纯逻辑测试、变异/方向测试、CPU/小样本 smoke，再做 GPU 2–3 epoch probe；
5. 数字只写对应 `docs/results/PHASE_*.md`；HANDOFF/TODO 只引用结论和位置；
6. oracle 必须标为 non-deployable upper bound，不能进入公开方法比较；
7. SSH 失败是第三态，不等于远端进程结束；
8. 任何低于同协议多个强 baseline 的 Ch1–Ch3 方案都不能作为方法章贡献。

改代码后必须跑：

```bash
uv run pytest
uv run ruff check src tests scripts
uv run ekg-smoke
```

---

## 5. 新颖性边界（面向 2027-06 毕业）

已有工作已经覆盖：显式 event arguments、两个 mention 的 joint encoding、cluster regularization、
retriever→cross-encoder、普通 arguments/relations factuality augmentation、modality/factuality 联合建模。
因此不要把组件名当创新。

当前较连贯的论文主线是：

> **Evidence adequacy and risk-aware event graph construction**：Ch1 处理 argument uncertainty→cluster
> risk，Ch2 处理 pair-specific evidence→cross-sentence FP，Ch3 处理 typed cues→unknown sufficiency，
> Ch4 量化这些构建错误对消费者的代价。

时间纪律：先在 2026 年内分别用一个冻结 seed 证伪/保留这三个机制；没有清晰主指标增益就及时降级，
不要继续扩 backbone、数据集或无穷消融。由于毕业前文献仍会更新，正式锁定 novelty claim 前必须再做
一次 2026–2027 一手论文检索。
