# EKG 实时状态

> 更新于 **2026-10-02**。新会话先读 [`HANDOFF.md`](HANDOFF.md)，再读唯一权威计划
> [`EXPERIMENT_PLAN.md`](EXPERIMENT_PLAN.md)；数字以 [`results/`](results/README.md) 为唯一事实源。

## 当前正式活动阶段

**当前优先级是公开论文可比性与受约束自驱动研究，而非重开失败机制。** 保持单 seed；已完成
`C-29 → G-19 → C-29.5 → C-29.6（协议阻断）→ G-20（作者甲，不执行）→ C-30`，现在进入
`C-31 第一轮（no_admissible_candidate）→ 作者授权一个 external benchmark → C-31b（ESC v0.9）✅ →
C-32a CPU 协议预检 → C-32b 新机制合同 → G-21（仅合同通过后）→ C-33 独立审计`。
完整决策、科研价值、可行性、一手依据、预期结果和停止条件见
[`COMPARABILITY_PLAN.md`](COMPARABILITY_PLAN.md)；可执行行只认 `EXPERIMENT_PLAN.md` §4。

| 项 | 当前状态 | 下一道门 |
|---|---|---|
| G-19 · Ch5 外部 baseline | ✅ 已完成 FR-016(b) 透明适配：2,331 train / 独立 selection-dev / 无标签 291-doc evaluation 的 seed-13 运行，raw cluster、official export 与官方 scorer 的覆盖/候选/评测器闸门均通过；正式数字、singleton 崩塌形态、P/V/U 和禁止论断均在 `results/PHASE_R1.md` §25.28 | 不重跑、不事后调阈值或 backbone；KBP 2017 不可得，故不得以本行评价原论文 |
| C-29.5 · 流程审计 | ✅ 已完成。G-20 的旧配置已证实缺 stop/constrained driver，不能重跑 | `AI_RESEARCH_WORKFLOW_AUDIT.md` 给出角色分离、执行就绪包、工程排障/科研迭代边界与停止规则 |
| C-29.6 · 静态契约核验 | ✅ 已完成并阻断旧恢复规则。11,149 个 target 第三行有 407 种值；C-3 target-third-line stop 不能不用 gold 实现 | 【协议】；作者已取甲，不写/不跑 recovery driver |
| G-20 · Ch4 外部 baseline | ✋ 作者甲收口。LLMERE 保留为 `P 有 / V(b) / U 无分数` 的可得性行；它不是模型低分 | target-dependent stop 是命名协议障碍；不生成、转换或评分 |
| C-30 · 全章 | ✅ 已完成：G-19 raw export 经独立 official scorer 复算一致；LLMERE 无 U 分数已登记 | P/V/U、七项 provenance、FR-016 与 `single-seed / non-confirmatory` 审计见 `results/PHASE_R1.md` §25.29 |
| C-31 · 领域证据地图 | ✅ 第一轮完成：Trucidator、MMD-ERE、rationale-distillation ECR 三卡分别卡【数据+协议】、【协议+代码】、【数据+协议+新颖性】 | `results/PHASE_R1.md` §25.30；`no_admissible_candidate`，不启动 C-32/G-21 |
| C-31b · 外部 benchmark | ✅ 作者已授权一个、且只一个外部 benchmark；ESC v0.9 被 R0 选定为 E 层 causal-existence 验证 | `results/PHASE_R1.md` §25.31；只增外部证据，不替换 MAVEN 主表、不复活 A4 |
| C-32a · ESC 协议预检 | **当前**：source hash、topic split、candidate universe、label folding 与 scorer 的 CPU-only materialization | `COMPARABILITY_PLAN.md` §2.1；任一歧义按【数据/协议】收口，不开 GPU |
| C-32b / G-21 | 尚未准入 | 只有 C-32a 与新的研究卡都通过，才可写冻结合同；单 seed 规则不变 |
| D4 / A4 / C5 方法机制 | D4、A4、旧 C5 均已按契约收口或封存 | 不重开；C-22 继续暂停，不得因为本队列结束自动恢复 |

## 可比性口径（本队列的通过条件）

- P（原文参考）只能给出处、表号与原始协议背景，永不与项目数字相减或排序；
- V（原始基准保真度）要求在公开原始基准复现发表数值；当前两项若无法完成，逐项说明障碍并标 FR-016(b)；
- U（统一协议）才可直接比较：manifest、候选/mention 全集、official scorer、标签映射、训练/selection/evaluation
  隔离与推理输入逐项一致；
- 单 seed 仅能给出同协议描述性比较。document bootstrap 只能描述评测单位不确定性，不能替代跨初始化确认。

## 历史：C-13–C-21（2026-09-20，本地文献/CPU/代码）

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

1. C-32a：对 ESC v0.9 做 CPU-only source/split/candidate/evaluator 预检，产出 immutable preflight；不下载近邻论文的预处理黑箱、不运行模型。
2. C-32b：仅在 E 层 protocol PASS 后，寻找一个能同时回答 MAVEN 主表价值和 ESC 外部可迁移性的全新机制卡；不以预期分数、低成本或空闲 GPU 排序。
3. G-21/C-33：只有冻结合同、exact command 和所有前门通过后才运行单 seed；由独立审计者复算，结果不支持即封存而非调参。

⛔ 仍禁止：未授权多种子、final-valid 选模、删除候选、事后修 prompt/阈值、用更大 backbone 掩盖机制失败，
以及把透明适配写成“胜过原论文”。

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

- **local**：2026-10-02 三件套 **786 passed / 32 skipped**、ruff 0、`ekg-smoke` OK；R1 一致性审计
  **36/36 requirements mapped**；P1 r15
  `1e31a9ac…f9655`；
- **gpu-4090**：2026-09-30 SSH 可达；C-28 相关进程 GONE，10 个 run 全部完成，聚合报告已落盘；
  远端代码受控同步到 `8bc62b0` 后完成聚合，未清理 remote-only 产物。**本次未核 GPU 占用，后续用卡
  仍须先 `nvidia-smi`**；
- **gpu-5090**：**当前占用未核，使用前必须重新核卡**。A4.3 四臂
  2026-09-16 11:02–23:27 跑完（实测 12h25m），C5.3 pilot-r2 与 CSProm-KG WN18RR 推理 09-16 跑完。
  ⚠️ **外网是分域的**：gh-proxy 增量 fetch ✅ / 清华 PyPI ✅ / GitHub 直连 ❌ / 完整 clone ❌ /
  Google Drive ❌ / ModelScope ✅。⛔ 硬边界：EasyECR 的 torch 2.0.1 无 sm_120；SimKGC 的 batch 1024
  要 4×32 GB 装不下。
- ⚠️ **cpolar 隧道可能整条下线**：2026-09-30 本次可达，但历史上出现过 `Connection refused`。
  继续按三态判活，**ssh 失败不得判远端进程已死**。

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
