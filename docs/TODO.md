# EKG 实时状态

> 更新于 **2026-09-17**。新会话先读 [`HANDOFF.md`](HANDOFF.md)，再读唯一权威计划
> [`EXPERIMENT_PLAN.md`](EXPERIMENT_PLAN.md)；数字以 [`results/`](results/README.md) 为唯一事实源。

## 当前正式活动阶段

**方法实验期的第一个周期全部跑完。Gate 2 的两个输入 2026-09-17 到齐，实测 0 个方法章过门。**

| 章 | 机制 | seed-13 契约跑的结果 | 判 |
|---|---|---|---|
| Ch3 · D4 | typed cues | full `.476515` < remove-core `.536788` < 两条锚；负控也赢过 full | ❌ Gate 1，家族已关闭（09-12） |
| Ch5 · C5 | role-compatibility 残差 | full MUC **79.90115**，臂序对（> 消融 > 负控），但低于主锚 **1.08** | ❌ 门未过（09-16） |
| Ch4 · A4 | pair evidence + 一致性约束 | full causal **7.507508**，低于三条判定线约 25 点，**低于自身消融臂 23.72 点** | ❌ 门未过（09-17） |

⇒ 按 `EXPERIMENT_PLAN.md` §5，落 **「≤1 章过」** 分支。**2026-09-17 裁决：改纲推迟到 Ch6 主表有数字之后再定。**
⛔ 执行代理**不得**自行降级论文结构、开新机制家族、启动第二设计周期、调门槛护栏或跑 seed 17/42。

## 下一步：**G-11a · 表 6-2 只剩四个公开对手行**

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

**队首 = G-11a**：四个公开对手（SimKGC / MCPredictor / CSProm-KG / BART contrastive）
**没有一个实现 CGEP**，适配代码要我们自己写 ⇒ 在我们的重建协议上注定是 **(b) 透明适配**，
按基准率 **3–4 周**。四个的障碍各不相同，**逐个答可行性两问**（见 `HANDOFF.md` §0.3 的表）。

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

✅ **上一条可追溯缺口已补**：`a65f456` / `791a03a` 之后的三件套记录 —— 2026-09-17 晚全量重跑
**644 passed / 29 skipped、ruff 0、`ekg-smoke` OK**（含本轮新增的 cgep 撞号回归与 E3.1 的三条断言测试）。

实验截止 **2027-02**；排期与估算基准率见主表 §3。

## 当前三端

- **local**：`main` 与 `origin/main` 同步、工作树干净；三件套 **639 passed / 29 skipped**、ruff 0、
  `ekg-smoke` OK；审计 `PASS` / 36 requirements。P1 r15 `1e31a9ac…f9655`；
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
