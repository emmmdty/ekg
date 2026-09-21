# EKG 实时状态

> 更新于 **2026-09-21**。新会话先读 [`HANDOFF.md`](HANDOFF.md)，再读唯一权威计划
> [`EXPERIMENT_PLAN.md`](EXPERIMENT_PLAN.md)；数字以 [`results/`](results/README.md) 为唯一事实源。

## 当前正式活动阶段

**活动队列只剩 Ch3/D4。** 作者要求按第一性原理拆到最终目标、必达门和中间指标，一次只推进一个章节。
目标树与阶段结果在 `results/PHASE_R1.md` §25；执行顺序是
`C-23 → C-24 → G-15 → G-16 → C-25 → C-25R → C-25R2 → C-26 → C-27 → G-17 → G-18`。
旧 typed cues 继续封存；失败的是机制家族，不是 D4 整章。

| 章 | R1 v6.2 结论 | 当前门 |
|---|---|---|
| Ch3 · D4 | **唯一活动章**：predicted causal uncertainty residual | C-25R 温度周期正式失败（Brier `.064155 > .041427`）；当前只做 C-25R2 class-weight analytic correction 的 selection-only 可行性门，C-26 仍冻结 |
| Ch4 · A4 | **不立项**：rationale + graph + counterfactual 宽命题已被近邻论文覆盖 | 新颖性阻断；不是继续调参或换 backbone 能解决的问题 |
| Ch5 · C5 | **暂停排队，不取消** document-complete asymmetric shortcut invariance | C-22 保持未启动；D4 队列完成前不切章 |

## D4 目标与当前阶段结果

- 最低过线：pooled five-class macro-F1 严格高于 `.553995`；
- 论文有效目标：当前 **≥ `.583995`**，且 full 同时超过 base/rewired、配对 bootstrap CI 下界 `>0`；
- 稀有类护栏：PS− F1 ≥ `.352456`，Uu F1 ≥ `.166850`；
- 输入门：2,913 docs / 2,532,394 ordered pairs 恰好一次，causal F1 ≥ `.300`，Brier 优于 no-skill；
- 阶段成果：S0 目标/文献闭合；S1 hash-bound train→causal-checkpoint→posterior runner 已完成并通过
  **703 passed / 29 skipped、ruff 0、smoke OK**；C-25 汇总器已在看到五折分数前冻结，当前全门
  **707 passed / 29 skipped、ruff 0、smoke OK**；
  S2 原始五折输入已完成并由 C-25 判定：coverage 全过，causal F1 **`.308141`** 过线；但 Brier
  **`.068750`** 劣于 no-skill **`.041427`**，故当前是概率校准修复阶段，仍没有 D4 新方法分数。

## ✅ 已完成：C-13–C-21（2026-09-20，本地文献/CPU/代码）

- **C-13**：一手论文与官方代码矩阵完成；A4 被新颖性证据淘汰，D4/C5 保留为条件路线；
- **C-14**：FACT↔ERE 的 2,913 篇 / 73,939 mentions 对齐；现成 held-out relation prediction 只覆盖
  291 篇，且 causal-only incidence 是 5,270/7,195=73.25%，不是合并关系族的 95.57%；
- **C-15**：纠正 LLMERE k=30 的旧判断——direct pair 覆盖 48,562/48,562，受损的是 two-hop support
  （8,826/11,231 保留）；但 A4 因新颖性不足仍不准入；
- **C-16**：C5 同时量出 912/213 个高相似 false-merge 桶和 540/73 个低相似 gold/missed 方向；训练池
  17,014 + 4,430，`.233553 → .415` 的 exact test 在 n=42 时 power `.82012`；
- **C-17/C-18**：D4 五折 cross-fit 计划与 C5 100 条盲审 rubric 冻结，尚无真实模型输出；
- **C-19**：全候选 causal posterior adapter 完成；
- **C-20**：一次性请求构建、严格输出校验、classifier-blind review template 与冻结阈值评分器完成；
- **C-21**：generator config 固定到既有内容寻址 `Qwen/Qwen3-8B`，100 条 requests
  （SHA `74a23bf8…4f2fd`）和 no-repair GPU runner 冻结；当前完整门
  **694 passed / 29 skipped、ruff 0、smoke OK**。

## 下一步

1. 实现 C-25R2 selection-only audit：从每折冻结 train counts 重算 class weights，解析逆校准，无参数拟合；
2. 只在 selection-dev 判 pooled F1/Brier；不过线就记录根因并设计第三个实质周期，不碰 evaluation；
3. 只有第二周期 selection 门与另行冻结的 formal gate 都通过才解锁 C-26；C5/A4/Ch6 不插队。

⛔ 仍禁止：未授权多种子、final-valid 选模、gold 关系输入、删除候选、事后修 prompt/阈值、用更大
backbone 掩盖机制失败。本轮没有新增方法指标，不能写成“D4/C5 已有效”。

## 已完成：**G-11a · 表 6-2 的公开对手行**（2026-09-18 收口）

三项裁决 **2026-09-17 晚已按推荐落地**，队列重新有东西。完整说明在 [`HANDOFF.md`](HANDOFF.md) §0.3。

| # | 裁决 | 定的是什么 |
|---|---|---|
| **①** | **Gate 2 改纲** | **推迟到 Ch6 主表有数字之后再定**，不是停等——取 (乙) 后 Ch6 全线解锁，没有任何可执行任务被 ① 阻塞；改哪一种形态取决于 Ch6 交出什么 |
| **②** | **Ch6 的上游身份** | **取 (乙)**：`predicted` 沿用 v5 判别式抽取器在 valid 上的产物，**表头标明上游身份**（不是 C5/A4/D4）。E3.1 已据此闭合 |
| **③** | **C-3 / G-8** | **维持 (甲) 不执行**：它是 Ch4 主表的一行，Ch4 存废未定之前 `< 1 GPU·h` 也没有去处 |

**裁完当晚推完的 Ch6 一轮**（数字全在 `results/PHASE_E.md` 最后一节）：

- **修缺陷**：冻结 unit 有 **68 个 `instance_id` 撞号**（`cgep.py` 用的是每个 ECG 各自的节点下标，
  撞的是完全不同的两条 query）。query edge 改为自己命名自己，重新冻结
  **`e3-v61-20260917`（`f75e7e87…`）**——逐行零差异、candidate digest 不变，并表能力没丢；
- **E3.1 ✅** 三层上游接口闭合（identity 16,104 单例 / relation 217,694 边 / factuality 16,104 标签），
  `status=closed`；
- **E3.2 ✅** 描述性画像：predicted 拓扑边是 gold 的 **3.4 倍**、R2 query F1 **.0795**，
  而下游 MRR 只掉 **12.2%** ⇒ **R2↔MRR 又是一对不对齐**（此前只有 causal_scc↔R1 的 ρ=−0.064）；
- **表 6-2 四行**：random `.0143` / frequency `.0378` / **predicted `.1583`** / gold `.1802`，
  Hit@1/3/10/20/50 全列。`.1802` 与 `.1583` 逐位复现 2026-07-29。

**队首 = G-11a，2026-09-17 晚已开工**：四个公开对手（SimKGC / MCPredictor / CSProm-KG /
BART contrastive）**没有一个实现 CGEP**，适配代码要我们自己写 ⇒ 注定是 **(b) 透明适配**，
按基准率 **3–4 周**。当晚落地的适配层：

- `scripts/export_cgep_as_kgc.py` —— 冻结 unit → KGC 数据集（33,017 实体 / train 46,100 /
  test 1,908 + 每题 512 候选），**任何一条 query edge 漏进训练图就 fail-fast**；
- `scripts/patch_csprom_kg_for_cgep.py` —— CSProm-KG 第 6 处补丁，**只 dump 候选分数**，
  不动模型 / 损失 / 优化器 / 指标，前后 hash 已记；
- `scripts/score_kgc_opponent.py` —— 用**我们自己的** evaluator 打分（表 6-2 其余四行同一把尺）。

**🟢 21:2x 起两个对手在 4090 上并行训练**（各自 namespace，共用一个独立 venv，**没碰 ekg 的 venv**）：

| 卡 | 对手 | 设置 | 预计 |
|---|---|---|---|
| card 0 | **CSProm-KG** | `-epoch 60`，其余与 README 的 WN18RR 命令逐字相同 | 约 5.7 GPU·h |
| card 1 | **SimKGC** | `--batch-size 256`（1024/512 实测都 OOM），其余与 `train_wn.sh` 逐字相同 | 约 1.3 GPU·h |

端到端冒烟已过：训练 → 按 dev 切片选 checkpoint → test → **dump 恰好 1,908 行** →
`score_kgc_opponent.py` 用我们自己的 evaluator 收下。
backbone 走 **`hf-mirror.com`** 直接拉（推翻「权重只能本地下了再 scp」，见 `HANDOFF.md` §0.6）。

**✅ G-11a 第一轮 2026-09-18 凌晨收口，表 6-2 成形，三个公开对手到齐。**

| 方法 | MRR | Hit@1 | Hit@10 | Hit@50 |
|---|---:|---:|---:|---:|
| CSProm-KG（(b)，⚠️ 结构性不兼容） | .0028 | .0000 | .0000 | .0000 |
| random | .0143 | .0021 | .0241 | .0891 |
| frequency | .0378 | .0267 | .0372 | .1509 |
| SimKGC（(b)，batch 256，无 description） | .0563 | .0183 | .1279 | .3375 |
| **本文构建图（predicted）** | **.1583** | .1038 | .2563 | .5126 |
| **SeDGPL（(b)，自跑）＝ gold 上界** | **.1802** | .1143 | .3124 | .5823 |
| （协议证据）SimKGC + 候选句 | .6373 | .5079 | .8585 | .9308 |
| （协议证据）`same_document` | .8041 | .6567 | **1.0000** | 1.0000 |

🔴 **两个 KGC 对手朝相反方向失败，两种失败都不是关于事件预测的**（机制都已量出）：
SimKGC 带候选句的分数 **91% 是文档匹配**（清空 description 塌 11.3 倍，top-1 同篇率
78.20%→18.50%，均匀乱选 0.41%）；CSProm-KG 按实体嵌入表打分而**金标在训练图里 0/1,908 有边**
（有训练边的候选平均排名 195.0 / 没有的 399.7 / 乱排 255.5），
而同 checkpoint 在 dev 上 `val_mrr=0.2907` ⇒ 模型没坏、也不是训练不足。
⇒ **不得写「我们超过了 CSProm-KG / SimKGC」。**

**E3.5 ✅ 已写**（`results/PHASE_E.md`）：三条结论各自的「可写 / 必须同时写 / 不可写」，
Done-when 逐条核对——**只差 matched seeds**（须逐次授权，表 6-2 当前单 seed 并已标注）。

## 顺位 2（裁决之外唯一能动的）

1. `docs/reports/` 下一份周报：从 09-17 那份的第 4 节接着写，**不要照抄它的计划表**；
2. matched seeds 13/17/42 —— ⛔ 须逐次授权，是 Ch6 Done-when 唯一还差的一条；
3. MCPredictor / BART contrastive **维持 (b) 不跑**，三个对手已满足名册 §5。

**2026-09-17 当周完成的五项**（结论都已写进 `results/` 并 push）：

1. **G-4** A4.3 四臂收口：`full` causal 7.507508 低于自身消融臂 23.72 ⇒ 第一个设计周期失败（`ac0da34`）；
2. **G-5b** C5 差距归因：那 1.83 里**误合并占 72.7%**；`full` 的 MUC recall **已超主锚**，
   剩下的 1.084 全在 precision ⇒ 该压的是误合并，不是继续加 recall（`df8404b`）；
3. **G-4b** A4 误差分析：**坍塌是无差别的，不是「先丢难例」**——`full` 丢掉的 1,344 对
   （= `remove_core` 答对集合的 88.8%）在距离分布上与被保留的、与 gold 全体几乎逐格相同；
   损失集中在 PRECONDITION（占 gold 76.8%，召回只保留 7.9%）（`e258cc8`）；
4. **C-3** LLMERE 恢复方案：根因改写——不是「95 条格式错」，是**全部 11,149 条退化重复**
   （生成侧没有终止语义），95 条只是污染落进了第一行。成本 42 GPU·h → **< 1 GPU·h**（`339f974`）；
5. **E3.1 前置核查**：三个方法章的产物与 E3 unit 交集为 0 ⇒ 裁决 ②（`c2f0cbc`）；
   另 **G-11a** 核实为早已完成（障碍原文一直在 `BASELINE_ROSTER.md` §6.2b）。

**2026-09-20 三件套**（含 R1 v6.2 审计、C-19 posterior adapter 与 C-20/C-21 generation harness）：
**694 passed / 29 skipped、ruff 0、`ekg-smoke` OK**。

实验截止 **2027-02**；排期与估算基准率见主表 §3。

## 当前三端

- **local**：三件套 **694 passed / 29 skipped**、ruff 0、`ekg-smoke` OK；P1 r15
  `1e31a9ac…f9655`。`docs/HANDOFF.md` 有本轮开始前已存在的用户编辑，不纳入本轮提交；
- **gpu-4090**：GPU 已修好（580.178.04），但**四卡自 09-10 起被他人 vllm 占满**（09-16 复核
  19,15x MiB / 24,564 MiB，35–63% util），已第 8 天；**09-17 隧道 `Connection refused`，状态未知**。
  **作者 2026-09-15：不要因为它拖慢进度**；
- **gpu-5090**：**主力机，现已空闲**（09-17 核卡 276 MiB / 32,607 MiB，0% util）。A4.3 四臂
  2026-09-16 11:02–23:27 跑完（实测 12h25m），C5.3 pilot-r2 与 CSProm-KG WN18RR 推理 09-16 跑完。
  ⚠️ **外网是分域的**：gh-proxy 增量 fetch ✅ / 清华 PyPI ✅ / GitHub 直连 ❌ / 完整 clone ❌ /
  Google Drive ❌ / ModelScope ✅。⛔ 硬边界：EasyECR 的 torch 2.0.1 无 sm_120；SimKGC 的 batch 1024
  要 4×32 GB 装不下。
- ⚠️ **cpolar 隧道会整条下线**：09-17 `ssh gpu-4090` 直接 `Connection refused`（不是端口变动）。
  按三态判活，**ssh 失败不得判远端进程已死**。

## 禁止

- 未授权额外 seeds；使用 final-valid 选模；不同 candidate/evaluator/split 直接比较；
- 把 Ch1 event-level argument oracle 或 Ch3 gold-evidence oracle 当方法分；
- **看到某个选模规则能救分再改选模规则**（选模轴伪影，Phase C 教训）；
- 未询问就跨机搬 checkpoint、数据集或其他大文件；
- `rsync --delete`、远端 `git clean -fdx`、服务器 `uv run`/`uv sync`；
- 复活已封存方案（工作点、近似 retriever、prototype、ATLoss），或用更大 backbone 掩盖机制无效。

## 成功条件

Ch1–Ch3 各自在统一公开主指标上**超过冻结主锚**，主表另报多个已复现的公开方法族
（`SPEC.md` v1.1.0 QR-001：广度是报告要求，不是准入门；跑不了的进可得性表写明障碍）。
每个外部复现带 FR-016 保真度状态。所有结论必须可从结果表追溯到 commit、manifest、candidate、
evaluator、命令、checkpoint 和 hash。

**三种可接受的最终形态**（见 `EXPERIMENT_PLAN.md` §7.5）：三方法章 + 应用章（博士量级）／
两方法章 + 应用章（领域硕士标准形态）／≤1 方法章时由作者裁决改纲（导师不介入结构）。
**不自行降级**；旧机制失败后只有通过实质不同的方法家族才能重开，不能以换名、扫参或更大
backbone 绕过止损。每个家族允许**两个有效周期**——5 个月预算下第二周期是可负担的，
第一轮失败不等于该章结束。
