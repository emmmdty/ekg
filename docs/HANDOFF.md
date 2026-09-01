# 交接文档 · 新会话从这里开始

> 更新于 **2026-09-01**（取代 08-31 状态快照）。读完本文即可接手，不需要回溯对话。
> **冲突时的优先级**：`docs/results/PHASE_*.md`（已发生的事实）> `docs/SPEC.md`（研究约束）>
> 当前 active phase > `docs/TODO.md` > 本文。本文只做导航与状态快照，**不复制实验数字**。

---

## 0. 三十秒摘要

- 课题：**occurrence-level 事件图谱构建 + 构建误差的下游代价**，三个方法章 + 一个系统评估章。
- 5090 执行提交为 **`5fbf2d6`**；prototype pair-head 生产提交为 `7128151`。完整本地门为
  **461 passed / 18 skipped**、ruff 0、CPU smoke；P1 r13 local/remote validate 均 PASS。
  4090 上 2 epoch 行为 smoke 已 PASS；50 epoch seed-13 已在 GPU0 启动，最后成功确认到 epoch 15。
  此后 SSH 在 banner 前失败，**不得据此推断远端进程死亡**。
- GPU1 的三个不同单种子 Stage-1 retriever 诊断均未过召回门，已停止该近似变体线；没有 seeds
  17/42，也未启动 Stage 2。r1/r2 已入 `results/PHASE_A.md`，r3 等 SSH 恢复后补 hash。
- 4090 不可达后，作者已授权本轮临时使用 5090 探索；`cpolar-ssh-update` 已恢复入口。ProtoEM-inspired
  两臂已闭合：plain smoke 止损，dependency 完整单 seed13 只过两个族的门，因 causal 未过主锚而
  整案封存；未启动额外种子或超参扫描。具体数字只见 `results/PHASE_A.md`；5090 模型身份未闭合
  正式 pin，结果均标 exploratory。
- **四章的对手线现已全部同协议实测闭合**，没有一栏引用论文原报数字。这是本阶段最大的进展；
  代价是其中两章的结论是「没有超过」。

| 章 | 同协议对手 | 我们 | 状态 |
|---|---|---|---|
| **Ch1** 身份消解 | official joint **80.98** MUC | 底座终点 4 种子均值 **79.14** | ❌ **机制两个周期均无效**，按契约降为系统组件 |
| **Ch2** 关系抽取 | official joint **33.17** causal | 机制三种子均值 33.27（未过门） | 🔵 **止损已被推翻，第二周期有明确目标** ← **下一步在这里** |
| **Ch3** 事实性 | CLS **.5458** / DMRoBERTa **.5423** | .5554 | ⚠️ 配对 CI 含 0，**不可区分** |
| **Ch4** 下游代价 | —（系统章） | 正控通过 | ✅ **唯一明确成立的一章** |

---

## 1. 下一步：Ch2 A3.2 第二个核心设计周期（实现与准入已完成）

**为什么第一轮注定失败，以及为什么第二轮不是重复劳动**：

- 第一轮的止损理由是「工作点余量已被吃干净：事后校准上限 33.15 ≈ 机制 33.27」，
  而 **33.15 是单一全局切点下的上限，低于主锚 33.17** —— 任何工作点机制当时都过不了门；
- 2026-08-30 的跨句剖析发现：same/cross 的 F1 差**主要是精度差**（.290 vs .200，召回只差 .062），
  跨句过发 **2.6 倍**、同句 **2.0 倍**；
- 按位置分别设阈后，**causal 天花板 33.80 > 主锚 33.17**，且三族护栏可同时满足。
  ⇒ 前提条件反转了。全部推导见 `results/PHASE_A.md` 末节。

**已完成**：`adaptive_workpoint` 控制器已从「逐族」扩到「**逐族 × 逐位置**」；同句候选与跨句候选
各自维护 NONE-logit 偏移。生产改动为 `pairs.py`、`balance.py` 和 relation trainer，提交 `91d32d8`。

- 控制器的**符号已在 08-30 修正**并有收敛测试钉住（`tests/relations/test_balance.py`）；
- 仍只加在**训练**损失、推理保持朴素 argmax（Menon et al. ICLR 2021），
  这样增益不可能被说成测试期调阈值；
- P1 r12 与 A3 r13 preflight 已重建并通过；4090 上 **2 epoch 行为 smoke 已 PASS**：训练器 macro
  .3178 → .3328，六个最终 offset 均在 [−.536, +.328]，12 条轨迹完整、final-valid 未访问。
  causal 跨句桶连续两轮测得正的最优 NONE shift（需要更高正例门槛），符合“跨句过发”诊断。
  该分数不是 official evaluator 结果；seed-13 50 epoch 正式流水线已启动，下一步是等它完成后核
  official evaluator 产物，而不是再开新 seed 或 retriever 变体。

**已被证否、不要再试的方向**（都已实测，见 `PHASE_A.md`）：
重叠滑窗（causal 跨窗仅 3.3%）｜连接词感知的上下文表示（有/无线索召回只差 .008）｜
长距离专用建模（句距分层平坦）｜`normalized_risk` 单用（负作用）｜固定权重/网格。

---

## 2. 作者定下的规矩

| 规矩 | 要点 |
|---|---|
| **⭐ 先验证方法正确再跑** | 2026-08-30 作者要求，起因是一个符号错烧掉四卡三小时。**流程见 §5，必须照做。** |
| **约束分级** | A 有效性 / B 可追溯 / C 操作性。判据：不遵守它会让结论变错，还是只让进度变慢？**卡空着就并行。** |
| **跑训练前先冒烟** | 本地没 torch ⇒ GPU 单测是 skip 的，全绿不代表能跑。 |
| **先解决方法问题再跑训练** | 本项目所有真正的进展都来自"先测量"：工作点诊断、配方诊断、跨句剖析。 |
| **不重复造轮子** | GitHub 上有且可运行的实现直接用，只做适配；透明补丁记 hash。 |
| **可自行提交/推送** | 条件是 git 整洁、按逻辑单元分次提交、可回滚、不强推。 |
| **多种子需用户再授权** | 每个方案先只跑冻结单 seed；所有待比方案单种子均超 baseline/护栏后也不自动补 seeds。GPU 并行只跑不同方案/任务。 |
| **机制/规则别写死** | 布局与组件清单写进 checkpoint 并在加载时校验，让变更**响亮失败**。 |
| **靶子由对手定** | 不用自己的历史成绩当及格线。 |
| **负结果是交付内容** | 不是待修的 bug。数字降就说降。 |

---

## 3. 协议身份（跑任何 A3 命令都要显式传）

| 项 | 值 |
|---|---|
| **当前 P1 trust root** | `runs/stages/P1/p1-v6-20260901-r13/` |
| `protocol.json` SHA-256 | `00e0943d32db9b5a2453c25c6d8adf8c33e456f9bff042bd134c23ae20b3447a` |
| 位置工作点 A3 plan（绑定 P1 r12） | `runs/stages/A3/a3-v6-position-workpoint-r13/preflight/execution_plan.json` |
| plan SHA-256 | `b587b21d7aa74437d7144ecad76d87f4fe2253f39966d48bb23108e914ec1eda` |
| **冻结主锚（权威，勿动）** | `runs/stages/A3/a3-v6-baselines-r10/primary_anchor.json`（sha256 `894b9bd2…185b3c12`） |
| 门 | causal **> 33.17**｜subevent **≥ 28.75**｜temporal **≥ 50.63** |
| 模型（内容寻址） | `/data/TJK/models/local/roberta-base/71be7419a60dcce0fc276654c8f9213b41f8def71a0c3465d7fed2352c961ea9` |
| 划分 | train 2,622 / internal-dev 291 / final-valid 710 |

**信任根谱系**：r9（`440516dc…`，08-29）→ r10（`1cf68b20…`，改 trainer）→
r11（`22ddb933…`，纳入 `balance.py`）→ r12（`0bd33e87…`，逐位置）→ r13
（`00e0943d…`，纳入 prototype pair-head）。
**这些版本的 data / manifests / candidate / evaluator / checkpoint 逐项零差异**，已核对，
所以**主锚跨版本仍可比、baseline 不需要重跑**。

**改 `CODE_PATHS` 里的文件后必须走的流程**（已跑通两次，机械但不可跳）：

```bash
# 1) 本地（服务器不能跑 uv）
uv run python scripts/run_p1_local_gate.py
# 2) data/ 被 gitignore，local_gate.json 走 scp + 双端 sha256
scp data/protocols/v6/local_gate.json gpu-4090:/data/TJK/ekg/data/protocols/v6/
# 3) 远端重建 bundle 并重新物化 plan
.venv/bin/python scripts/build_p1_bundle.py --bundle runs/stages/P1/<新版本> \
    --remote-smoke data/protocols/v6/remote_smoke.json
.venv/bin/python scripts/prepare_a3_baselines.py --output runs/stages/A3/<新批次>/preflight \
    --p1-protocol-sha256 <新 hash>
# 4) 逐项核对新旧 bundle 的差异面，确认只有你改的那几个文件变了
```

`CODE_PATHS` 定义在 `scripts/build_p1_bundle.py`，现含 18 个文件，
其中与方法相关的是 `train_supervised_relations.py`、`src/ekg/relations/balance.py`、
`extractor/supervised.py`、`pairs.py`、`maven_ere_official.py`。
Ch1/Ch3/Ch4 的训练脚本**不在**其中，改它们不触发重建。

---

## 4. 各章现状与可写的东西

数字一律见 `docs/results/`，本节只说**状态**。

### Ch1 身份消解 —— 机制两个周期均无效，**方法贡献为零**

- C4-r2：留下每 epoch 并用官方评分器逐个打分，证明 08-29 那张「机制 +4.43 MUC」的表是
  **选模轴伪影**（对照臂自身 epoch 间波动 8.55 点）；旧节已标 SUPERSEDED。
- C4-r3：发现 trainer **从来没有过学习率调度**，补齐 warmup + 线性衰减后均值 +1.78、
  过训衰减消失、**噪声降 2.5 倍**（极差 8.55 → 3.36）。head-lr 与梯度累积**都是负作用**。
- 在修好的底座上重测三个机制臂：Δ −0.23 / −0.15 / −0.71，**全部小于种子噪声**。
- 多种子验证：唯一存活的线索（终点 +0.4）**符号翻转不重现**（+0.43 / −0.35 / +1.47）。
  ⚠️ 我一度写下的「退火终点跨种子只差 0.07」是 n=2 的运气，n=4 下 sd 1.02，**已在档案里更正**。
- **可写的**：配方修复；两条方法学结论（选模轴能造 4 点假增益；种子噪声集中在训练早期，
  退火终点是正确的报数点）。**不可写**：任何机制增益。

### Ch2 关系抽取 —— 见 §1，**这是下一步**

- 三条 baseline 同协议闭合、主锚冻结；复现底座量化了欠训混淆（仅预算就值 causal +5.11）。
- A3.2 第一轮：机制按设计工作（causal 精度 22.15 → 26–30），但三条线都差一点，
  且「把校准放进目标函数并不比事后再切一刀更好」（相对事后校准只 +0.12，种子 sd 0.82）。
- ⚠️ 第一轮曾因**控制器符号写反**发散到 1e7（`b ← b − s` 才对，不是 `+`），
  已修正 + 收敛测试钉住。这是"先验证再跑"这条规矩的由来。

### Ch3 事实性 —— 对手闭合，**不可区分**

- 五个同协议系统的 macro 全落在 **.528–.555**，而该 split 的配对 **MDE 是 ±.05**。
  三组配对检验全部平局，**连"我们的底座输给对手"都不可判别**。
- 本章最硬的一块是方法论结论：**这个基准在这个规模上无法区分任何两个方法**，
  论文原报 45.4/47.1/47.6 之间 2.2 点的差距同样落在噪声内，与我们的实测互相印证。
- 下一步（若继续）：**改判定轴到证据侧**（1,276 个 gold span，支持数是标签轴的 18 倍），
  或承认只能给描述性对比。**不要换数据集绕过去。**

### Ch4 下游代价 —— **成立**

- 图依赖正控通过且顺序正确：gold .1802 / rewired .1185（−34%）/ no_graph .0811（−55%）。
  消费者用的是边的**正确性**而非存在性。
- 它排除了「消费者不看图」这个致命替代解释，并给全章一把标尺：整张图值 **.0991 MRR**，
  故构建损失 −.0218 = **图对下游全部价值的 22%**。
- 下一步：扩到完整 factorial（正控已过、标尺已建）。

---

## 5. ⭐ 「先验证方法正确再跑」的执行流程

作者 2026-08-30 明确要求，**不是建议**。起因：一个更新符号写反，四卡跑了三小时才发现发散。
2026-08-30 下半场按此流程做跨句诊断，**在零 GPU 消耗下否掉了两个错误假设**。

1. **纯逻辑进模块**，不要埋在脚本里（`src/ekg/relations/crosssentence.py` 是范例）；
2. **用手造的、已知答案的样例写测试**，不是只测形状和往返；
3. **做变异检验**：把关键行故意写反，确认测试会红。带方向/反馈的机制**必须**有收敛或
   符号断言，否则测试抓不到 A3.2 那类 bug；
4. **小规模验证跑**（如 `--limit 5`），把中间量打出来**人工核一遍**；
5. **内置自校验**：让 baseline 配置（如阈值 0、组件全关）**按构造必须复现已知数字**，
   不复现就立刻停（逐位置扫描的 `(0,0)` 格就是这么用的）；
6. **长跑前先短探针**（2–3 epoch）+ 显式断言中间量按设计在动。A3.2 那次十分钟就能看出发散。

---

## 6. 会让你白跑的坑（都实际发生过）

1. **⚠️ pyc 陷阱**：同长度、同一秒内的改动，Python 会**复用旧字节码**（失效判据是 mtime+size）
   —— **文件是对的、跑的是旧的**。做变异检验时务必让改动长度不同，或先
   `find src tests -name __pycache__ -type d -exec rm -rf {} +`。
2. **口径三轴**：报差值前对齐 **评分器 · 文档集 · 校正**。同一个错在本项目犯过四次。
3. **配对 vs 绝对**：比较两个系统看配对差值的 CI。跨 split 比较丢掉的正是配对。
4. **代理指标 ≠ 报数指标**：Ch1 的 pair-F1 与 MUC 方向相反，选模轴选错造出 4 点假增益。
5. **单点估计不可靠**：Ch1 epoch 间波动 8.55 点、种子间 1.8 点；**n=2 的一致是运气**。
6. **本地没有 torch**：GPU 相关测试全 skip。
7. **远端必须先 `git fetch && reset --hard origin/main`**。
8. **`data/` 被 gitignore**：`local_gate.json` 等必须 scp + 双端 sha256。
9. **服务器禁 `uv run`/`uv sync`**（会卸掉 torch），一律 `.venv/bin/python`；
   禁 `rsync --delete` 与远端 `git clean -fdx`。
10. **训练预算/配方不对等会伪装成架构结论**：Ch2 光是 3→50 epoch 值 causal +5.11；
    Ch1 光是补学习率调度值 +1.78 且噪声降 2.5 倍。

---

## 7. 怎么操作服务器

```bash
~/.ssh/hold-4090.sh                    # 建 ControlMaster；cpolar 每隔一两小时会断，重跑即可
ssh -o ControlPath=~/.ssh/cm-ekg4090 gpu-4090 '...'

# 长任务：一条 ssh 只发一个后台任务
ssh ... 'cd /data/TJK/ekg && CUDA_VISIBLE_DEVICES=N setsid nohup .venv/bin/python -u <cmd> \
         > logs/<name>.log 2>&1 < /dev/null & echo launched'
```

- ⚠️ **一条 ssh 里连发两个后台任务，第二个会被吞掉**（实测）。一条一个。
- ⚠️ **本地 `timeout` 掐掉 ssh 客户端会报 exit 124，但远端 `setsid` 的任务照跑**。
  判活三态 ALIVE / GONE / ssh 失败，只有成功 ssh 读到进程 GONE 才算结束。
- 4090 主力（`/data/TJK/ekg`，四张 24GB）；卡空着就并行，不同卡/不同 run-dir/固定 seed 互不影响。
- 5090 备用（`/mnt/aidata/tongjiakai/ekg`），**每次使用须单独问作者**。
- ⚠️ 服务器**没有外网**：测试里不要 `from_pretrained("hf-internal-testing/...")`，
  它不会失败而是**挂住**。用 stub。

---

## 8. 本轮已交付（供快速定位）

| 产物 | 位置 |
|---|---|
| **阶段性报告（周四交导师）** | `docs/reports/2026-09-03_阶段性报告.md`（已用当前数字整节重写，含「诚实的总账」一节） |
| Ch2 工作点诊断 | `scripts/report_relation_operating_point.py`（`--position-split` 逐位置扫描，`(0,0)` 自校验） |
| Ch2 跨句剖析 | `scripts/report_relation_crosssentence_profile.py` + `src/ekg/relations/crosssentence.py` |
| Ch2 族均衡机制 | `src/ekg/relations/balance.py`、`train_supervised_relations.py --balance-components` |
| Ch2 一键打分 | `scripts/score_a3_arm.py`（checkpoint → 官方分，三步不漂移） |
| Ch3 耦合机制与容量对照 | `src/ekg/factuality/detection.py`、`--evidence-pooling {none,uniform,evidence}` |
| Ch3 公开对手线 | `src/ekg/factuality/baselines.py`、`--detector baseline --pooling {cls,dynamic_multi}` |
| Ch3 两系统配对检验 | `report_factuality_metric_power.py --predicted-labels-b` |
| Ch1 配方与逐 epoch 存档 | `train_coref_scorer.py --warmup-steps/--head-lr/--accum-steps/--save-every-epoch` |
| Ch1 逐 epoch 官方打分 | `runs/stages/C4/score_epochs_dir.sh`、`score_endpoint.sh` |
| Ch4 图依赖正控 | `evaluate_cgep_propagation.py` 的 `no_graph` / `rewired` 两臂 |

**验证命令**（改代码后必跑）：

```bash
uv run pytest                          # 当前 445 passed / 16 skipped
uv run ruff check src tests scripts
uv run ekg-smoke
```
