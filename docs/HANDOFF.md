# 交接文档 · 新窗口从这里开始

> 更新于 **2026-09-17**。本文是新窗口唯一必读入口；读完后再按本文链接打开所需文件，不回溯聊天记录。
> 本文只记录**状态、决策、依赖、下一步**，不复制实验表格——数字只认 [`results/`](results/README.md)。
> 已完成的轮次与已裁定的决策菜单在**文末附录**，按需查证，不必通读。

## ▶ 当前阶段（新窗口先看这张表）

| 项 | 值 |
|---|---|
| 正式阶段 | **方法实验期已跑完三章的第一个周期**。Gate 1 判「不过」（D4，2026-09-12 关闭）。**Gate 2 的两个输入 2026-09-17 到齐，实测 0 个方法章过门**（C5 −1.08 MUC；A4 −25 causal F1，且低于自身消融臂 23.72）⇒ 落 **「≤1 章过」** 分支：**等作者裁决改纲**（导师只要结果，不管章节结构）。 |
| **⚠️ 开工前必读** | 每个新任务先答「科研价值 / 可行性」两问（`CLAUDE.md`「开工自审」节）。不可行**必须点名是数据 / 协议 / 代码 / 算力 / 授权哪一条**，附一手证据，**停下交作者裁决**，不得自行换题绕开。 |
| **活动任务** | ⚪ **无。三条方法线的第一个周期全部收口完毕，队列停在 Gate 2 等裁决。** A4.3 四臂 2026-09-16 23:27 跑完、09-17 聚合 `status=pass` 并已写进 `results/PHASE_A.md`。**没有作者裁决之前不要开新任务**——不开第二设计周期、不换机制家族、不跑 seed 17/42。 |
| ✅ **A4 的 7 文件红线已解除** | `pilot_summary.json` 已落地、`--aggregate` 已通过（7 个哈希重校验 PASS），那 7 个文件不再被在跑的任务锁住。但**改它们之前仍要有裁决**：A4 的第二设计周期未获批准。 |
| **本周的三件结果** | ⓪ **A4.3 四臂跑完（09-17 收口）**：`full` causal F1 **7.507508** vs 同机无机制参照 `remove_core` **31.224848**（低 23.72），三条判定线 33.17 / 32.097314 / 32.009563 全部未过，subevent 22.911283 破护栏、temporal 52.457177 过 ⇒ **A4 第一个设计周期失败**（`results/PHASE_A.md`）。 |
| **2026-09-16 的两件结果** | ① **C5.3 跑完**：`full` MUC **79.90115** > `remove_core` **79.15966** > 负控 **78.83333**（**臂序第一次是对的**，MUC 与 BLANC 同向），**但比主锚 80.98472 低 1.08、比注册对照 80.36759 低 0.47 ⇒ 门没过**（`results/PHASE_C.md`）。② **CSProm-KG 复现成功**：WN18RR MRR **0.572682** vs 公布 0.572660，四项全在事前登记容差内 ⇒ **名册第一个 FR-016 (a)**（`results/PHASE_E.md`）。 |
| **最重要的一件事** | **Gate 2 到了，而且是 0 章过。** 三章的第一个周期都跑完了、都没过门：D4 负控赢过 full；C5 臂序对但低于主锚 1.08；A4 机制低于自身消融臂 23.72。**这是要摆给导师的事实。**⛔ 执行代理不得自行降级论文结构、开新机制家族或启动第二周期。 |
| （09-15 的归因，仍成立） | **A4 三臂把 subevent 塌陷归因干净了**：塌的是那个 `retained` detach（根因 A），**不是 (戊)**。(戊) 单独三族全部持平或上升；**但 `full` causal F1 9.77 仍低于同 backbone 的 `remove_core` 31.13 约 21 点** ⇒ 机制层面的问题没解决。**已停下交裁决（§0.5b），不打第三次补丁。** 数字见 §0.4a 与 [`results/PHASE_A.md`](results/PHASE_A.md)。 |
| **第二重要的一件事** | ✅ **C5.3 的根因已修并已重跑**（`a1e1509`+`a65f456`）：提交脚本加 `--argument-predictions`、冒烟补上推理路径、`predicted_arguments.py` 进 `CODE_FILES`（8→9）、**preflight-r2 `7a56e451…b6b0`** 重建。修复先用首跑遗留的 `full` checkpoint 在真实 291 篇上重放 predict 验过（291/291，251 簇）。详见 [`results/PHASE_C.md`](results/PHASE_C.md)。 |
| **待作者裁决** | 🔴 **一项：Gate 2 的改纲决定**（`EXPERIMENT_PLAN.md` §5「≤1 章过」分支）。两页结果已摆好：`results/PHASE_A.md`（A4）· `results/PHASE_C.md`（C5）· `results/PHASE_D.md`（D4）。**改纲只关乎章节形态，不阻塞第 6 章复现、两章的离线归因与文档审查**（§0.3 队列 1–4 项照跑）。 |
| 论文结构 | 第3章 D4 事实性（**本轮失败**）· 第4章 A4 关系 · 第5章 C5 身份 · 第6章 E3 图谱构建与下游应用。原 24 条件 factorial / Holm / frozen-vs-finetuned **已撤销，不得恢复**。**章节存废在 Gate 2 判，执行代理不得自行改成两方法章。** |
| **⚠️ 唯一权威计划** | **[`EXPERIMENT_PLAN.md`](EXPERIMENT_PLAN.md)** 的 §4 主表与 §5 Gate。本文队列只是当周切片，**不得出现主表以外的新任务**；要偏离顺序**先改主表**。 |
| **gpu-4090** | ⛔ 四卡自 09-10 起被他人 vllm 占满（09-15 复核 19,25x / 24,564 MiB），已第 6 天。**ssh 与 CPU 全程可用，纯 CPU 任务照常跑。** 作者 2026-09-15：**不要因为 4090 拖慢进度，先在能用的卡上推进，4090 以后再补。** |
| ✅ **gpu-5090** | 🟢 **主力机**。C5 整条、A4 全部探测都在这台机上。⛔ 硬边界：EasyECR 的 torch 2.0.1 无 sm_120；SimKGC 的 batch 1024 要 4×32 GB 装不下；**外网是分域的**（§0.6 的表）。 |
| 截止与排期 | 实验须在 **2027-02** 前完成；排期与估算基准率见 `EXPERIMENT_PLAN.md` §3。 |
| 完成后必须做什么 | 按 §6 五步回填：产物落地 → 写结果页 → 改队列行状态与 commit → 推进队列 → commit + **push** |

> **工作树状态**：2026-09-16 起**没有已知例外**，`git status` 应当干净、`HEAD` 等于 `origin/main`。
> （旧交接里那条「`docs/reports/TEMPLATE_周报.md` 未提交」已随 `5a7b581` 失效，不要再照它预期一个脏树。）
> 最新导师可读周报是 [`reports/2026-09-10_周报.md`](reports/2026-09-10_周报.md)，**下一份周报欠着**。

## 0. 接手后先做什么

### 0.1 只读检查（三条，全过才开工）

```bash
cd /home/tjk/myProjects/masterProjects/ekg
git status -sb                      # 期望：main 与 origin/main 同步、工作树干净
git log -3 --oneline --decorate
uv run python scripts/audit_r1_consistency.py \
  --output runs/stages/R1/r1-v61-20260904/audit/cross_artifact_audit.json
                                    # 期望：PASS: 36 requirements mapped
```

工作树若出现未说明改动，**先查来源，不覆盖、不清理**。

> **2026-09-17 之后的新窗口**：§0.3.1 的收口清单**已全部做完**（判活 → 聚合 → 写结果页 → 回填 → Gate 2），不必重做。当前状态是**等作者对 Gate 2 的裁决**，见 §0.3。

### 0.2 按顺序读这三份（够了，不要重读整个仓库）

1. **[`EXPERIMENT_PLAN.md`](EXPERIMENT_PLAN.md)** —— 唯一权威计划。§4 主表挑任务，§3 看排期与
   5090 边界，§7 看每章最终要交的表长什么样；
2. **[`BASELINE_ROSTER.md`](BASELINE_ROSTER.md)** —— 四章的外部对手名册与 FR-016 保真度路径；
3. 本文 §E.0 的六条交接约束（HEAD 等于 origin/main、单队列、改计划先改文件、不开分支/worktree、
   活动任务独占产物、交接必须已 push）；
4. **`CLAUDE.md` 的「开工自审」节**——每个新任务先答科研价值 / 可行性两问，不可行必须点名
   是数据 / 协议 / 代码 / 算力 / 授权哪一条并交作者裁决。

按需再读：对应章节的 `phases/PHASE_*.md` 契约、`results/PHASE_*.md`（数字唯一权威）。

### 0.3 下一个窗口执行什么

**队列不卡在决策上，卡在一处待修的代码和一张被占的卡。** 顺序如下；
偏离顺序先改 [`EXPERIMENT_PLAN.md`](EXPERIMENT_PLAN.md) 的主表。

| 次序 | 主表 ID | 做什么 | 卡在什么 |
|---|---|---|---|
| ✅ | **G-5** | ~~修 C5 推理侧口径 → 重建 `preflight-r2`~~ → **已完成 2026-09-16**（§0.4b） | — |
| ✅ | **G-5** | ~~C5.3 pilot-r2 三臂~~ → **2026-09-16 跑完并聚合**，门未过，数字见 `results/PHASE_C.md` | — |
| ✅ | **G-11a** | ~~CSProm-KG WN18RR 推理~~ → **(a) 已取得**，四项全在容差内，见 `results/PHASE_E.md` | — |
| ✅ | **G-4** | ~~A4.3 收口~~ → **2026-09-17 六步全部做完**：判活（GONE，四臂 `arm.json` 齐）→ `--aggregate` `status=pass` → 数字写进 `results/PHASE_A.md` → 主表 G-4/Gate 2 行回填 → Gate 2 摆给作者。`full` causal **7.507508**，低于自身消融臂 **23.72** 点 ⇒ **A4 第一个设计周期失败** | — |
| **1** | G-11a | **第 6 章外部对手复现**：SimKGC / BART contrastive / MCPredictor 各自取 (a) 或写明障碍维持 (b) | 🟢 **不依赖 Gate 2**，5090 已空 |
| **2** | G-5b | **C5 差距归因**（离线、不训练、不占卡）：把 `remove_core` 79.15966 与主锚 80.98472 之间的 1.83 拆到漏合并 / 误合并 / 单例判定上，写回 `results/PHASE_C.md` | 🟢 产物全在，**不是第二周期** |
| **3** | C-3 | LLMERE 恢复方案审查（纯文档、只读） | 🟢 主表排 09-17 起 3 天 |
| **4** | G-4b | **A4 误差分析**：四臂召回坍塌砍掉了哪些 causal 类型、砍的是不是难例，写回 `results/PHASE_A.md` | 🟢 `edge_predictions.jsonl` 四臂齐全 |
| 🔴 | — | **改纲决定由作者裁决**（导师只看结果、不管论文结构）。**它只关乎章节形态，不阻塞上面四项** | 待作者 |
| 2 | G-11a | SimKGC / BART contrastive / MCPredictor 维持 (b)，按名册写障碍即可，不再投入复现 | 不阻塞 |
| 4 | G-4 | A4 第二设计周期（**仅当** Gate 2 判它继续） | 不在本轮范围，Gate 2 之前不启动 |

**⛔ 一律不做**：D4 第二个周期、调 threshold、扫 epoch、换 split、加大 backbone、用 seed 17/42
去捞 D4、把探测数字写进主表或与 33.17 / 32.10 相减、为了让 C5.3 跑通去放宽那条 fail-fast。

### 0.3.1 ✅ A4.3 收口清单（**2026-09-17 已全部执行完毕，留作记录**）

> 2026-09-16 离线前写好，09-17 照此执行完毕：进程 GONE、四臂 `arm.json` 齐、`--aggregate` `status=pass`、数字已写进 [`results/PHASE_A.md`](results/PHASE_A.md)、主表与本文已回填、Gate 2 已摆给作者。
> **下面六步不必再做**；命令留着是为了将来 4090 线补跑时照抄（4090 线 `preflight-r2 a3cc6c44…f73c` 仍有效）。

#### 第 1 步 · 判活（三态，ssh 失败 ≠ 进程死亡）

```bash
ssh gpu-5090 'ps -eo pid,etime,cmd | grep "[r]un_a4_pair_evidence" | grep -v "bash -c"'
ssh gpu-5090 'ls /mnt/aidata/tongjiakai/ekg/runs/stages/A4/a4-v61-pair-evidence-5090-r1/pilot/'
```

- 有进程 ⇒ **ALIVE**，等；四个臂目录各有 `arm.json` ⇒ **跑完**；
- 无进程且缺 `arm.json` ⇒ **中途死了**，看日志尾部定位（⚠️ `logs/a4_pilot_5090.log` **前段被截断过**，
  原因见 `results/PHASE_A.md`；权威产物是各臂 `arm.json`，不受影响）；
- ssh 连不上 ⇒ **只是隧道**，重试，**不得判进程已死**。

#### 第 2 步 · 断了就只补没跑完的臂（不要重跑全部）

驱动器拒绝覆盖已存在的臂目录，所以补跑要点名：

```bash
ssh gpu-5090 'cd /mnt/aidata/tongjiakai/ekg && setsid nohup .venv/bin/python -u \
  scripts/run_a4_pair_evidence.py \
  --contract runs/stages/A4/a4-v61-pair-evidence-5090-r1/preflight/protocol.json \
  --output runs/stages/A4/a4-v61-pair-evidence-5090-r1/pilot \
  --arms length_matched,no_constraint \
  > logs/a4_pilot_5090_resume.log 2>&1 < /dev/null &'
```

⚠️ **启动类命令不要套 `for … && break` 重试循环**——ssh 后台启动返回非零码，重试会把同一条命令
发第二次；第二条虽被守卫挡住，但**会截断第一条的日志**（2026-09-16 连犯两次）。

#### 第 3 步 · 聚合（这一步会重新校验 7 个代码哈希）

```bash
ssh gpu-5090 'cd /mnt/aidata/tongjiakai/ekg && .venv/bin/python -u \
  scripts/run_a4_pair_evidence.py \
  --contract runs/stages/A4/a4-v61-pair-evidence-5090-r1/preflight/protocol.json \
  --output runs/stages/A4/a4-v61-pair-evidence-5090-r1/pilot --aggregate'
```

通过即写出 `pilot_summary.json` 并打印四臂官方 causal F1。它同时断言：四臂 `status=complete`、
同 seed、`final_valid_accessed=false`、同 candidate digest、候选对数完全相同、每臂都带 checkpoint 哈希。

#### 第 4 步 · 对着这张表读数（**预期已经知道，偏离才是信号**）

`full` 臂几乎肯定复现 09-15 (戊) 探测的形态——本跑 dev 轨迹与探测**逐点重合**（`results/PHASE_A.md`
的「在跑中的三项核查」）。探测的官方分是 causal **9.77** / subevent **23.55** / temporal **52.08**。

| 判据 | 线 | 探测所在位置 |
|---|---|---|
| causal（主指标） | 须**严格超过** 33.17 / 32.10 / 32.01 | 9.77 ⇒ **差约 22 点** |
| subevent 护栏 | ≥ **28.75** | 23.55 ⇒ **破** |
| temporal 护栏 | ≥ **50.63** | 52.08 ⇒ 过 |
| `remove_core`（同机无机制参照） | — | G-13 实测 **31.13** |

⇒ **预期结论：A4 第一个设计周期失败**，且失败形态是「机制比自己的消融臂低约 21 点」。
**若实际数字与上面相差很远（比如 causal 突然 30+），先怀疑跑错了契约或选错了 checkpoint，
不要先相信它。**

⛔ 读数纪律：**四臂互比干净**（同机、同 backbone、同候选全集、同 evaluator、同 seed）；
与 33.17 / 32.10 / 32.01 的比较**跨机器**（那三条线训在 4090 backbone 上，G-13 实测偏移约 1 个
causal F1 点）⇒ **只陈述限制，不做算术校正**。

#### 第 5 步 · 写回（五步回填见 §6）

1. 数字写 [`results/PHASE_A.md`](results/PHASE_A.md)（**唯一权威**），带契约 `11e4343a…490c`、
   四臂官方分、mediator、`revised_rows`、各 checkpoint 哈希、**机器偏移限制**；
2. 主表 `EXPERIMENT_PLAN.md` 的 **G-4 行**改状态；`HANDOFF.md` 首表与 §0.3 队列改状态；
3. `TODO.md` 同步；commit + **push**。

#### 第 6 步 · Gate 2（两个输入齐了才判）

| 输入 | 状态 |
|---|---|
| C5.3 | ✅ 2026-09-16：`full` MUC **79.90115**，臂序对但**低于主锚 1.08** ⇒ **门未过** |
| A4.3 | ✅ 2026-09-17：`full` causal **7.507508**，低于三条判定线约 25 点、低于同机消融臂 `remove_core` **31.224848** 达 23.72 ⇒ **门未过** |
| **⇒ Gate 2 实际落点** | **0 个方法章过门**（D4 已关闭 · C5 −1.08 · A4 −25）⇒ 走 **「≤1 章过」** 分支：**由作者裁决改纲**。执行代理已停在此处等裁决。 |

判法见 [`EXPERIMENT_PLAN.md`](EXPERIMENT_PLAN.md) §5。**先把两条事实摆清楚再判**：

- ⚠️ 「**3 章过**」分支在 Gate 1 判不过那天就已失效（D4 已关闭），最多只剩 2 个方法章；
- C5 门未过；A4 预期门未过 ⇒ **现实区间是「1 章过甚至 0 章过」**。

⛔ **Gate 2 上执行代理不得自行做的事**：降级论文结构、开新机制家族、启动第二设计周期、
调门槛或护栏、跑未授权的 seed 17/42。**「≤1 章过」的分支写得很死：由作者裁决改纲**（导师只看结果，结构是我们自己定的，所以「等导师拍板」不是一个可以停在那里的状态）。
把两页结果摆给作者，等裁决。

### 0.4 三章现状

#### 0.4a Ch4（A4 pair evidence）：归因已清，但机制仍输给消融臂

**三臂探测，同机（5090）、同 backbone（`2c7ff1f1…`）、同臂（`full`）、同 seed，相邻两臂只差一处改动。
探测数字不进主表、不与 33.17 / 32.10 相减。**

| 臂 | base 判正 | causal F1 | cP | cR | **subevent** | temporal | FP | 跨句 FP |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| dry-run（无 A、无戊） | 766 | 8.00 | 37.26 | 4.48 | 23.05 | 51.86 | 362 | 332 |
| **戊-only（现行代码）** | **904** | **9.77** | **42.20** | **5.53** | **23.55** | **52.08** | 363 | 334 |
| A + 戊 | 1,711 | 12.51 | 26.04 | 8.24 | **0.00** | 49.87 | 1,122 | 1,077 |

**三条结论**：

1. **(戊) 是一次干净的小改善**——三族全部持平或上升，precision 不降反升（37.26 → 42.20），
   FP 几乎没动（362 → 363）。**保留**。
2. **那个 `retained` detach（根因 A）是一笔糟糕的交易**——买来 recall，代价是 precision 崩 16 点、
   FP 涨 3 倍、**subevent 整族归零**。**已回滚（`5cfbeff`），代码里留了注释：没有隔离测量之前
   不得再 detach 一次。** 这次是实测归因，不是推理。
3. ⚠️ **但大局没变**：`full` 9.77 仍低于 G-13 实测的 `remove_core` **31.13** 约 21 点。
   真正压住 causal recall 的是**证据流本身**（那条 revised CE 在用残缺输入训练 encoder），
   而对它的两种处理各有代价：留着 ⇒ recall 塌；detach ⇒ subevent 塌。**⇒ §0.5b 交裁决。**

**代码与产物**：现行 = 戊 in / A out（`5cfbeff`）。
probe 契约 `3a256a1c…d0e2`（A+戊）与 `f85f5e72…3f44`（戊-only），
产物在 `gpu-5090:runs/stages/A4/probe-5090-20260915-{domain,wuonly}/`。

⚠️ **这一段已被作者 2026-09-16 的裁定改写**（「4090 不可行就使用 5090」）：A4.3 现在**跑在 5090**。
原因不是那个混淆消失了，而是**权衡变了**——4090 被占第 7 天，Gate 2 只差这一跑。
代价被如实标注而不是被抹掉：判定线 33.17 / 32.10 / 32.01 都是 4090 backbone 上训出来的，
G-13 实测机器偏移约 **1 个 causal F1 点**；**四臂互比干净，与那三条线的比较带限制说明，绝不相减**。
详见 [`results/PHASE_A.md`](results/PHASE_A.md) 的「A4 改走 gpu-5090 线」节。
另外 `run_a4_pair_evidence.py` 等 4 个被契约钉住的文件都改过，**A4.2 之前必须重建 `preflight-r2`**
（4090 纯 CPU），旧 `preflight/` 不覆盖。

#### 0.4b Ch5（C5 argument uncertainty）：5090 线已建好，首跑的缺陷已修，pilot-r2 在跑

**已成立**（详见 [`results/PHASE_C.md`](results/PHASE_C.md)）：

- **C5.1 preflight PASS**（5090 线）：`protocol.json` **`a3f21f97…8141`**，`code_files=8`，
  `final_valid_accessed=false`，候选 digest `15a3b1a5…10910`；
- **两条 baseline 在 5090 上独立重算，与 4090 线逐位相同**（主锚 MUC **80.98471986**）
  ⇒「这组 baseline 与 backbone 无关」从论证变成实测，这也正是 **C5 可以搬而 A4 不可以**的依据；
- **C5.2 CPU / CUDA 双半边 PASS**（契约四条断言两边都过）。

**C5.3 首跑失败 → 已修复并重跑**（2026-09-16）。失败是 `full` 臂训练跑完、倒在 predict 步：
`role_compatibility` 在推理时读不到 `argument_prediction_status`，fail-fast 触发。
**数据一侧清白**（73,939 条全带 `status`）；根因是 `build_maven_ere_submission.py` 的 CLI
**根本没有 `--argument-predictions`**，推理侧物理上拿不到论元层——与 C5.2 冒烟抓到的
「训练/推理口径不成对」**同族**，换了条路径复发。逐层核查表见 [`results/PHASE_C.md`](results/PHASE_C.md)。

修了四处，**fail-fast 一字未动**（没有默认 state、没有放宽断言）：

| 改动 | 为什么 |
|---|---|
| 提交脚本加 `--argument-predictions` | 推理读训练绑的**同一个产物** |
| `apply_predicted_arguments` 加 `allow_extra` | 推理只标注 2,913 篇里的 291 篇；**missing 仍致命**，只放开 extra。⚠️ 反过来裁文件会让两侧拿到**不同产物** |
| pilot 两条命令改走 `train_command` / `predict_command` | 配对关系**无需 GPU 即可断言**（新增 targeted test） |
| 冒烟补上推理路径 | 它从不跑提交脚本，所以抓不到；现在每臂训完跑一次，且故意让预测文件**宽于**被标注的文档集 |

**先验证再重训**：拿首跑遗留的 `full` checkpoint 重放那条原样失败过的命令 ——
**291/291 篇、251 个非平凡簇、exit 0**，在真实规模上验过，不是靠推理。该产物只做验证、不进表。

**preflight-r2**（旧 `preflight/` 不覆盖）：`protocol.json` **`7a56e451…b6b0`**，`code_files` **9**
（补钉 `src/ekg/nodes/predicted_arguments.py`——它决定每个 mention 拿到什么 argument state，
此前没被哈希钉住），候选 digest 与 gold 与 r1 同哈希，两条 baseline 重算仍是
**80.98471986417657 / 80.36758563074353**。

**重跑结果（2026-09-16 当天跑完）**：`pilot-r2/`，三臂全部重训（不复用 r1 契约下的 checkpoint——
一个产物只挂一个契约）。**291 篇 / 8,914 mention 全覆盖，重复 0、陌生 0。**

| 臂 | MUC F1 | vs 主锚 80.98472 | vs 注册对照 80.36759 | BLANC F1 |
|---|---:|---:|---:|---:|
| **full** | **79.90115** | **−1.084** | **−0.466** | 90.2893 |
| remove_core | 79.15966 | −1.825 | −1.208 | 89.6895 |
| permutation（负控） | 78.83333 | −2.151 | −1.534 | 89.5839 |

**臂序第一次是对的**（full > 消融 > 负控，MUC 与 BLANC 同向）——7 个机制里第一个。
**但门没过**：`gate.above_anchor=false`、`above_registered_control=false`。
根子和 D4 同形：`remove_core` 本身就比锚低 1.83，**我们这条监督共指 head 整体低于官方 joint**，
机制把它抬了 0.74 但没抬过线。⚠️ **+0.742 先别当效应**——这个 split/指标的噪声地板还没量过。
⛔ 不跑 seed 17/42（未授权，且两项 gate 皆 false 本就不满足前置）。详见
[`results/PHASE_C.md`](results/PHASE_C.md)。

#### 0.4c Ch6（E3 / G-11a）：CSProm-KG **已复现，落 (a)**

| 项 | 值 |
|---|---|
| evaluation unit | **已冻结**（C-10）：`runs/stages/E3/e3-v61-20260913/`，1,908 实例 |
| 仓库 | `gpu-5090:/mnt/aidata/tongjiakai/baselines/CSProm-KG`，commit `9a8072951beda3e5…ca28`（**在 ekg 仓库之外**，不受远端 `git reset` 波及） |
| 独立 venv | 同目录 `.venv`（`uv venv` 建，**不碰 ekg 的 venv**——那个 venv 里连 pip 都没有）：torch 2.8.0 / PL 2.6.6 / transformers 5.17.0 |
| backbone | `baselines/bert-large-uncased`，**从 ModelScope 直下**，1,344,997,306 B，sha256 `be24b235…6993` |
| checkpoint | `checkpoint/WN18RR/WN18RR-epoch=425-val_mrr=0.5664.ckpt`，1,689,462,973 B，sha256 `27e40718…e695`，**双端核对一致** |
| **(a) 容差已事前登记** | WN18RR **MRR 0.572660 ±0.005**、H@1/3/10 各 ±0.5 点（README 的 Pretrained Checkpoint 表）。紧于 D4 的 ±1.0，因为**纯推理重放没有训练方差** |

✅ **2026-09-16 跑完**（纯推理 9 秒 / 25 batch，墙钟时间全花在排障上）：

| | 实测 | 公布 | 容差 |
|---|---:|---:|---|
| **MRR** | **0.572682** | 0.572660 | ±0.005 ✅ |
| H@1 / H@3 / H@10 | 52.06 / 59.03 / 67.77 | 52.06 / 59.00 / 67.79 | 各 ±0.5 ✅ |

⇒ **名册里第一个 FR-016 (a)**。为跑通打了**五处透明补丁**（nltk 离线、checkpoint `map_location`、
`add_safe_globals`、PL2 钩子迁移、`np.float`）并把该 venv 的 transformers 降到 **4.57.6**——
⚠️ 上一版交接写的「transformers 5.x 只用 BertTokenizer/BertModel 所以没问题」**是错的**，
作者自写的 `BertModelForLayerwise` 要 4.x 的 `get_extended_attention_mask`。
前后 hash 全在 [`results/PHASE_E.md`](results/PHASE_E.md)。

⚠️ **四个对手在我们的重建协议上仍是 (b)**——它们没有一个实现 CGEP；(a) 只在各自原基准上成立。
保真度逐行状态见 [`BASELINE_ROSTER.md`](BASELINE_ROSTER.md) §6.2b。

### 0.5a ✅ 作者裁决（2026-09-15）：五项全部裁定，队列解锁

> 原话：「按照你的推荐进行，允许使用 5090。后续 4090 可以补，现在先在能使用的 GPU 上进行后续的任务，
> 不要因为 4090 拖慢进度，优先下载而不是跨 GPU 搬运（需要采取时间短的方式），注意网络环境存在问题时
> 采用镜像或者其他替补方法。」

| 编号 | 裁决 | 已执行到哪 |
|---|---|---|
| **③ A4 recall 塌陷** | **(戊)**：`sufficiency` 改为与 `necessity` 同作用面（`positive & scoreable`） | ✅ 代码已落（`2d125cd`），5090 单臂探测 **运行中**，见下 |
| **④ Ch6 改序** | **先做 CSProm-KG**；SimKGC 落 (b)，障碍写「原配置需 4×32 GB」 | ✅ 仓库已 clone（`9a807295…ca28`）并传到 5090；WN18RR checkpoint 本地下载中 |
| **③′ C5 走哪条线**（本轮新增） | **C5 整条搬到 5090**；A4.3 仍留 4090 | ✅ **C5.1 preflight + C5.2 双半边全部 PASS**，见 `results/PHASE_C.md` |
| **② LLMERE 保真度** | **记 (b) Unverifiable**，不碰封存的 final-valid | 待写进名册 §2.1 |
| **① A4 决策 3** | **维持 (A) 两段式**，不改 | 无需动作 |
| **⑤ SeDGPL 的 ESC (a)** | **不再为 (a) 投入**，落 (b) 并写清 .0599 vs .196 的差距与两处未公开自由度 | 待写进名册 §6.2 |

⚠️ **⑤ 与上一版交接的建议相反**：C-4b 已在原文**声明的** topic 级 5 折 CV 口径下实测到 3 倍差距，
再投一次是「重复确认一次失败」。**有证据的 (b) 比拿不到的 (a) 更结实。**

#### ⚠️ 作者 2026-09-16 追加裁定：**A4 也搬 5090**

> 「4090 不可行就使用 5090，这我之前说过。」

下面这张表**记录的是搬家前的技术差异，仍然成立**，但它不再是「A4 不搬」的理由——
差异改为以**限制说明**的形式随结果一起报。执行状态见 §0.3 第 1 行。

#### 为什么 C5 搬家无损而 A4 搬家有代价（技术差异，仍然成立）

| | 能搬？ | 依据 |
|---|---|---|
| **C5** | ✅ | 两条 baseline 是**预测文件 + 官方 evaluator 打分**，与我们的 encoder 无关。5090 上重算得 MUC **80.98471986**，与 4090 线**逐位相同** ⇒ 从论证变成实测 |
| **A4** | ❌ | 判定线含 A3 fallback **32.10**，那是在 4090 pin 上训的；G-13 实测同一臂在 5090 backbone 上 **31.13**。换机就是混淆 |

#### (戊) 探测的读法（结果未到，先把判据写死，免得事后挑）

**判据是 `base 判正数`，不是 F1。** 参照：dry-run 的 `full` 766 / `no_constraint` 1,385 /
`remove_core` 4,355。**回到 4,000 量级 = (戊) 成立**；仍在 1,000 以下 = 机制在这个数据上无效，
按契约走 (甲) 如实交 Gate 2，**不打第三次补丁**。
产物 `gpu-5090:runs/stages/A4/probe-5090-20260915-domain/`，probe 契约
`3a256a1c2e6621f08b08db261d5162b7f7bf456b0200c0dfb44d61603ba5d0e2`（7 个 `CODE_FILES` 里只有
`pair_evidence.py` 与 `smoke_a4_pair_evidence.py` 重哈希，`train_a4_pair_evidence.py` 原样
⇒ 根因 A 的 detach 仍在，本跑测的是 **A+戊**）。
**第二臂（戊-only，撤掉 A）用来隔离根因 A，排在 C5.3 之后**——A4.3 反正要等 4090，不急。

### 0.5b ✅ 作者裁决（2026-09-16）：A4 第一个周期取 (甲)，原样跑 A4.3

**为什么要在这里做选择**：§0.4a 的三臂已经证明 `full`（证据流 + 一致性）在同 backbone 下
比消融臂 `remove_core` 低约 **21** 个 causal F1 点，而压住它的是**证据流本身**那条 revised CE
（它在用「只留 trigger span」的残缺输入训练 encoder——恰恰是 A4 自己论证为不可能的任务）。
对它的两种处理各有代价：**留着 ⇒ causal recall 塌；detach ⇒ subevent 整族塌**。
这不是参数问题，动它就是动冻结的四臂矩阵语义，**执行代理不自行决定**。

| | 做什么 | 对实验 | 对论文 |
|---|---|---|---|
| **(甲) 推荐：维持现状，跑 A4.3** | 代码就是现行的「戊 in / A out」，四臂按契约在 4090 跑完，如实交 Gate 2 | 12–17 GPU·h，等一张 4090 空卡 | 第一个周期如实结账；**phase 的成败必须由契约那一跑判定，不能拿探测数字宣布失败**（D4 的 Gate 1 也是这么判的） |
| (乙) | 把 revised CE 移进 `if flags.consistency_loss:` 分支 | ⚠️ **它救不了 `full`**——`full` 的 `consistency_loss=True`，那条 CE 照样在。它只让第 8 臂 `no_constraint` 名副其实（「只有证据表示、零约束」），**改的是归因臂的语义** | 需要重新论证第 8 臂定义，且不能事后改 |
| (丙) | 现在就判 A4 第一周期失败，省下那 12–17 GPU·h | 省算力 | ⚠️ **拿探测数字给 phase 判死刑**，与 D4 的先例不一致，Gate 2 上站不住 |

**推荐 (甲)** 的两条理由：① (乙) 不改变 `full` 的命运，只改归因臂，**这一轮花在它上面不值**；
② 探测是探测，**契约那一跑才有资格判 phase 成败**。若 Gate 2 判 A4 继续，第二设计周期再动
证据流的训练目标（届时要按新家族重新过文献、因果链与功效）。

> **作者 2026-09-16 裁定：按推荐执行 ⇒ (甲)。** 代码维持「戊 in / A out」（`5cfbeff`），
> 四臂按契约在 4090 跑完，如实交 Gate 2。**变更窗口到此关闭**：A4.3 出任何数字之后不再接受
> (乙)/(丙)，执行代理也不得以「探测分数不好看」为由提前宣布 A4 失败。
> 上卡前仍要做的两件事：重建 A4 的 `preflight-r2`（4 个被钉文件都改过，4090 纯 CPU），
> 以及核到一张真正空闲的 4090 卡。

### 0.6 从 D4 学到、必须带进 C5（以及任何新机制）的三件事

1. **先查契约点名的入口脚本在不在**。D4 的 `run_d4_typed_cue_oof.py` 从没被写过，
   却在契约的 GPU 命令里躺了很久。**A4 的洞已在 C-6b 补上；C5 的还在**——
   `phases/PHASE_C5_argument_uncertainty.md` 点名的入口，开工第一件事就是核对它存不存在。
2. **pilot 入口必须进 preflight 的 `code` 哈希集合**，否则那一跑是唯一钉不住的代码。
   D4 为此重建了 preflight（`preflight-r2`，`code_files=7`，旧的不覆盖）。
3. **报增益前先看噪声地板**。5090 的独立重建把 D4 anchor 的可复现地板量到约 **±.01**
   （见 `results/PHASE_D.md`）；小于这个量级的差不要当效应。

#### 环境既成事实（不用再查）

- ⚠️ **「没有外网」这句话太粗，2026-09-15 按域名逐个实测后改成这张表**（gpu-5090）：

  | 目标 | 结果 | 影响 |
  |---|---|---|
  | `gh-proxy.com` 镜像上的**增量 `git fetch`** | ✅ | ekg 仓库本轮就是这样同步的；**远端代码不必走 scp** |
  | 同一镜像上**完整 `git clone`** | ❌ `fetch-pack: unexpected disconnect`（`--depth 200` 也断） | 外部仓库改为**本地 clone → tar → scp** |
  | `pypi.tuna.tsinghua.edu.cn` | ✅ **HTTP 200** | **服务器能装包**：CSProm-KG 升 torch、C-2b 的 EasyECR 活体 venv 都因此可行 |
  | `github.com` / `huggingface.co` 直连 | ❌ | 与 09-14 记录一致 |
  | `drive.google.com` | ❌ | 公开 checkpoint 只能本地下载后 scp |

  **带走的纪律**：粗粒度的「没外网」把**能装包**和**能拉 checkpoint** 混成了一件事，
  直接影响了两项任务的可行性判定。按域名测，别按感觉写。
  ⇒ **外部仓库、预训练权重、公开 checkpoint 一律本地下载后 `scp`**，没有第二条路。
  实测带宽约 **0.4 MB/s**（50 MB > 2 分钟）——`CLAUDE.md` 那句「单程约 70 分钟」就是这么来的。
  这条影响**每一个**外部对手复现（CSProm-KG 的公开 checkpoint、BART contrastive 的 NEEG 数据同理），
  排期时先把搬运算进去。**不要再在服务器上试 `git clone` 或 `from_pretrained` 拉模型。**
- 三个 gitignored JSON 已双端核对（`protocol.json` `f0b4702b…50829`、`t024_freeze.json` `9133a73c…587e7`、
  `cross_artifact_audit.json` `622d094b…f8467`；4090 旧档备份 `protocol.json.pre-e12-20260911`）；
- ⚠️ **2026-09-15 新增：cpolar 有两种不同的失效，别用同一套动作去修。**
  作者的 `~/.local/bin/cpolar-ssh-update` 只能治第一种：

  | 症状 | 更新脚本的输出 | 该做什么 |
  |---|---|---|
  | **端口变了**（常态） | `matched: tcp://…` 然后改写 `HostName`/`Port` | 跑一次脚本即可 |
  | **通道整个下线** | `ERROR [gpu-5090] no tunnel named 'ssh' and none with local='127.0.0.1:22'` | **脚本无能为力**——面板上那条隧道不在了。只能等它回来，**期间按三态判活，不得判定远端进程已死** |

  2026-09-15 12:5x 就是第二种：`Connection refused` + 上面那条 ERROR，同一时刻 `gpu-a6000` 的隧道正常。
  **当时 5090 上正跑着 A4 探测（`setsid nohup`、PPID=1、独立 session），按记录它不受本机断连影响。**
  一次 1.69 GB 的 rsync 在 34 分钟后被这次断连打断（`Broken pipe`）——**所以大文件一律带 `--partial`**，
  回来续传而不是重头再来。

- ⚠️ **gpu-5090 / gpu-a6000 的 cpolar 端口每天都会变，这是常态，不是故障**。作者自己的
  `~/.local/bin/cpolar-ssh-update` 由 systemd user timer（`cpolar-ssh-update.timer`，每日 00:00 +
  开机后）登录 cpolar 面板抓新端口，**只重写 `~/.ssh/config` 里对应 Host 块的 `HostName` 与 `Port`
  两行**，块内其他行原样保留。**不要把端口变化当异常去排查，也不要去改那个脚本。**
- 2026-09-12 已一劳永逸修掉由此引起的 `Host key verification failed`：给 `Host gpu-5090` 加了
  **`HostKeyAlias gpu-5090`**（`gpu-a6000` 块本来就有），host key 改按固定别名查找，端口再换也不影响，
  **且校验一点没放弃**。别名下钉的就是作者确认过的那把 ED25519
  `SHA256:Jkfb9Tb14Z/SqsG6g9GedDjKZOcBl1DLW6zT0V1dkJY`，实测可连。
  该行在 Host 块内且不是 `HostName`/`Port`，**不会被每日脚本覆盖**；改动前的 config 备份为
  `~/.ssh/config.before-hostkeyalias-20260912`。
  今后**只有指纹本身与上面这串不一致时才算异常**——那意味着隧道后面换了机器，**停下问作者，不得自行 TOFU**；
- ⚠️ **gpu-5090 上的 `runs/stages/R1/r1-v61-20260904/protocol.json` 是 09-04 18:30 的旧档**
  （`67a36354…c1c8`，`phase_contracts` 是**空的**），所以 `tests/scripts/test_prepare_d4_typed_cue_preflight.py`
  在 5090 上必然 FAIL（`R1 protocol has no factuality phase contract`）。**这不是代码问题**，是
  §E.2b 那三个 gitignored JSON 只被要求同步到 4090、5090 从没同步过。2026-09-12 用 5090 跑全量
  pytest 时实测到这一条；其余用例全过。要在 5090 上跑任何 D4/A4 preflight，先同步这三个 JSON
  并双端核 SHA-256（本地值见 `results/PHASE_R1.md` §21.3）——**同步动作本身请作者点头**，
  因为它会成为那台机上的信任根。
- 两台机的 cpolar 隧道都会掉线。**ssh 失败 ≠ 远端进程死亡**，三态判活；长任务一律
  `setsid nohup` + `python -u` + 重定向 `logs/`，**一条 ssh 只发一个后台任务**。
  实测这样起的进程 PPID=1、独立 session，本机关机不影响。

### 0.7 纪律清单（每条都是花代价买来的，开工前扫一遍）

1. **一次只变一处。** 09-14 把发散归给 B（同跑还带着 A）是错的；09-15 的探测同时带 A 与 (戊)，
   于是 subevent 塌陷**归不了因**，只能再花 5 小时跑第三臂。**重哈希 probe 契约时数一下
   「几个文件变了」——只该有 1 个。**
2. **判据写在跑之前，跑完不许挑。** (戊) 的判据事前写的是「4,000 量级＝成立 / <1,000＝无效」，
   实测 1,711 **两个分支都不落**，就如实记为「都不落」，不往任何一边圆。
   CSProm-KG 的 (a) 容差同理，**已在跑之前登记**。
3. **ssh 失败 ≠ 远端进程死亡。** 09-15 12:5x 隧道整个下线时，5090 上的探测照常跑完
   （`setsid nohup`、PPID=1）。三态 ALIVE / GONE / ssh 失败，**只有成功 ssh 读到进程 GONE 才算结束**。
4. **冒烟没覆盖的路径等于没测。** C5.3 死在 `build_maven_ere_submission.py` 上，而冒烟从不跑它。
   新机制的冒烟要覆盖**正式 pilot 会走的每一个子进程**。
5. **粗粒度的环境判断会把可行的任务判成不可行。** 「两台机都没外网」这句话把**能装包**和
   **能拉 checkpoint** 混成一件事；按域名逐个测之后（§0.6 的表），C-2b 与 CSProm-KG 的可行性都变了。
6. **改了被契约钉住的文件，就必须重建 preflight**，旧的不覆盖。D4 的 `preflight-r2`、
   C5 的 `preflight-r2` 都是这么来的；A4 的还欠着。
7. **大文件传输一律 `--partial`。** 一次 1.69 GB 的 rsync 在 34 分钟处被隧道打断；带了 `--partial`
   就是续传，不带就是重来。
8. **报增益前先看噪声地板**（D4 anchor 实测 ±.01），小于它的差不要当效应。

## 1. 当前裁决与状态

### 研究目标

课题仍是 occurrence-level 事件图谱：Ch1 身份消解、Ch2 关系抽取、Ch3 事实性检测、Ch4 构建错误的
下游代价。论文目标继续是**三个高质量方法章 + 一个系统评估章，不降标**。

旧机制失败不等于取消方法章：同一机制家族两个有效周期未过门就封存；新家族必须重新通过文献、
协议、因果链、功效和新颖性审查。执行代理不得自行改成两方法章。

### SDD 文档边界

| 层 | 权威文件 | 只负责 |
|---|---|---|
| 研究治理 | [constitution](../.specify/memory/constitution.md) | 不可妥协的有效性、可追溯性和修订原则 |
| 稳定需求 | [`SPEC.md`](SPEC.md) | WHAT/WHY、研究场景、质量底线、可验收结果 |
| 可迭代方案 | [`RESEARCH_PLAN.md`](RESEARCH_PLAN.md) | 候选方法、评测设计和当前依赖计划 |
| 可执行任务 | [`TASKS.md`](TASKS.md)、[`phases/`](phases/README.md) | 步骤、输入、门、停止条件和产物 |
| 运行状态 | [`TODO.md`](TODO.md)、本文 | 当前做到哪里、下一动作 |
| 实验事实 | [`results/`](results/README.md) | 数字、口径、产物和真实 PASS/FAIL |

SPEC **没有**固定 C5/A4/D4 的具体实现、baseline 名单、GPU、epoch 或执行顺序。当前候选中心假设是
evidence adequacy / uncertainty propagation；R1 若找到反证或更强设计，应改 plan，不应把候选方法硬塞回
SPEC。只有研究问题、范围或质量标准改变时才修订 SPEC。

### Git 与验证

- 协议代码整改：`23b4fad fix(protocol): centralize P1 manifest and hashing logic`；
- SDD/方法论整改：`c870ed7 docs(research): separate stable spec from adaptive methodology`；
- R1 审计代码/结果：`8e3eb7a feat(r1): add dataset and prospective power audits`、
  `4e893c1 docs(r1): record method design gate evidence`、`f1401bc feat(r1): freeze factuality
  cross-validation folds`、`32cfd46 feat(r1): close relation handoff and power gate`、
  `277b36f fix(r1): isolate factuality OOF training source`；
- 本文提交后以新的 `origin/main` HEAD 为准；
- 最新本地验证（2026-09-15，`5cfbeff`）：**635 passed / 29 expected skips**，ruff 0，`ekg-smoke` OK；
- ⚠️ **本地三件套全绿不代表能在服务器上跑**：本地没有 torch，所有 torch 用例都是 `skip`。
  **任何 torch 相关改动，推之前先 ssh 到 5090 跑一次对应的测试文件**（`.venv/bin/python -m pytest <file>`）；
- local gate 的 `tested_tree_sha256`：
  `52c639ff79fb9401f71d42d4d1ecaec6abacf65701cecf72f1dcac7edb04f46e`（220 个文件；
  前值 `3bff2ac2…c701d3c` 对应 `886185e`）；
- A3.6 只运行了已授权 seed 13；R1 功效只读 train-derived internal-dev。跨数据 ID 审计按合同读取了
  public-valid 结构字段但未计算关系/事实性指标，访问已在 ledger 披露；没有搬运 checkpoint。

## 2. 已经成立和不得改写的事实

只从下列结果文档取精确数字。⚠️ **这张表用的是旧章号**（Ch1 身份 / Ch2 关系 / Ch3 事实性 /
Ch4 应用），与现行章序（**第3章 D4 事实性 · 第4章 A4 关系 · 第5章 C5 身份 · 第6章 E3 应用**）
不是同一套编号；**按结果页认，不按章号认**。


| 主题 | 权威入口 | 当前结论 |
|---|---|---|
| Ch2 工作点与检索 | [`results/PHASE_A.md`](results/PHASE_A.md) | 工作点两个核心周期已用完；近似 retriever 三条均未过门；prototype/ATLoss 已封存 |
| Ch1 历史方法 | [`results/PHASE_C.md`](results/PHASE_C.md) | 旧方法未稳定胜出；event-level gold argument 只能作泄漏型 oracle |
| Ch3 历史方法 | [`results/PHASE_D.md`](results/PHASE_D.md) | 旧 D3：与强 baseline 未统计分开。**新 D4：typed-cue 家族 2026-09-12 失败并关闭**（Gate 1「不过」分支），消融与负控都赢过 full |
| Ch4 历史系统证据 | [`results/PHASE_E.md`](results/PHASE_E.md) | 图依赖正控与部分构建损失成立；正式同实例 factorial 尚未完成 |
| P1 可信根 | [`results/PHASE_P1.md`](results/PHASE_P1.md) | r15 是 A3.6 与当前 R1 的可信根；旧 A3 结果继续绑定各自历史根 |

A3.6 **官方训练配方分账已经完成**。它只分解 rates、coref auxiliary、per-family checkpoint selection
三个复现变量，不是论文创新。最高 causal F1 仍未越过冻结主锚，A3 以 `a3-v6-20260905-r17`（protocol
`c187bf03…9359e`）不可变 `failed` bundle 关闭；之后只由 R1 决定新的 Ch2 方法家族。

禁止：第三个工作点、第四个近似 retriever、继续 prototype/ATLoss、把 r13 已观察到的 by-family 曲线
回收成第 4 臂、用更大 backbone 或换 split 救旧机制。

## 3. 后续任务：按依赖执行

当前依赖图：

```text
P1 r15 ─→ A3 failed handoff r17 ─┐
R1 准备任务 ─────────────────────┴→ R1 baseline/input closure
                                                           ├→ C5 候选方法
                                                           ├→ A4 候选方法 ─→ E3 → H2
                                                           └→ D4 候选方法
```

C5/A4/D4 之间没有被 SPEC 固定顺序。R1 未发现真实数据/模型依赖时，可以重排或占不同 GPU 并行；E3
必须等待三类所需上游 handoff。多种子始终需作者再次明确授权。

### 任务 E：交替推进协议与本周队列（2026-09-07 起）

#### E.0 统一约束：Claude 与 Codex 交替推进，不并行、不分叉

两个执行代理**轮流**持有同一条队列，任何时刻只有一个"活动任务"。约束只有六条，违反其一即视为交接失败：

1. **单队列**：任务顺序只认下面 E.2 的历史记录与 E.2a 的接续队列。要偏离顺序，**先改本表再执行**，不在会话里口头改计划。
2. **开工前对齐**：除 §0 的三条只读检查外，必须确认 `git rev-parse HEAD` 等于 `git rev-parse origin/main`；
   不相等就先 `git pull --rebase`，未对齐不开工。
3. **交接靠文件不靠记忆**：一项任务算完成，必须四件齐全——产物落地、数字写进对应
   `results/PHASE_*.md`、本表该行状态改为 `done` 并填 commit、**已 push 到 `origin/main`**。
   没 push 就没交接，下一个代理不得开工。
4. **不开分支、不开 worktree**：只在 `main` 上按逻辑单元提交。（2026-09-07 已删除
   `.worktrees/r1-t023-t024` 与已并入 main 的 `feat/r1-t023-t024`。）
5. **活动任务独占产物**：持有活动任务的代理独占该任务涉及的全部结果页与 `runs/` 目录；
   另一代理此时**只读**，不写任何 `results/`、`runs/`、`TASKS.md`。
   *唯一例外（2026-09-07 作者裁决）*：E8 的长训练只写 `baselines/relation/llmere-causal-*` 这一个
   namespace，持有队列的代理**可以先把它挂到后台再继续做文档行**；回填结果页时才需要重新独占。
   *第二例外（2026-09-09 作者明确授权）*：E8 generation 期间可推进不接触其 namespace 的 D4.0–D4.2。
   D4 在实现、本地 gate、immutable preflight 和 CPU/CUDA smoke 全部通过前不得启动 seed-13 pilot；其 pilot
   独占自己的 `runs/stages/D4/`，不得与 E8 共用 GPU0，也不得启动额外 seeds。
6. **未完成就交接**：把已做到哪一步、卡在什么证据上写进本表该行，状态标 `wip`，不留只有自己知道的上下文。

#### E.1a 作者裁决（2026-09-07）：relation baseline 门重新界定，LLMERE 缩小并行

E3 把 QR-001 的名单问题交给作者后，作者当日裁决**采纳 (b) 的缩小并行版本**。要点：

1. **改门，不改章**：近期 MAVEN-ERE 方法**无一发布可跑的官方训练代码**（RESIJ / 2025 two-stage / KnowQA /
   TacoERE / LLMERE 全部缺），所以「第二个**官方实现**」这道门投入再多 GPU 也过不去——是我们自己的运行口径
   写错了。改回 SPEC `QR-001` 本身的措辞：**第二个不同方法族 · 我们在冻结协议下跑通 · fidelity 缺口写明 ·
   且不弱于主锚**。`SPEC.md` 不修订。
2. **不接受稻草人**：`taco-s13-r3` 只有 causal 32.01 < 主锚 33.17，赢它由赢主锚蕴含。只接受
   「主锚 + 透明适配」被否决。
3. **LLMERE 缩小成 causal-only**：48,365 训练 / 11,149 推理，约 joint 的 1/4；subevent/temporal 是**我们方法的
   护栏**而非 baseline 的义务（`official_single` 是既有先例）。**B2 不需要 Meta 许可**——用未设门镜像 + 披露
   权重 SHA-256。
4. **并行，不串行**：A4 pilot 只吃一张卡而 4090 有四张；第二 baseline 只在确认性 promotion 时生效，
   所以 **T024 照常冻结 A4 契约**，LLMERE-causal 以"已规格化、数字 pending"入 roster。
5. **接受的风险**：LLMERE 若高于主锚，Ch2 及格线抬高、A4 可能失败——**这正是现在跑它的理由**。
6. **明确不做**：拿 LLMERE 已发布的预测在 710 篇 official valid 上用我们的评测器重打分（那是封存的
   final-valid，不值这笔账）。

完整裁决与规格见 [`results/PHASE_R1.md` §13](results/PHASE_R1.md)；brief 的 roster/promotion 已按此修订并在
`amendments[0]` 保留原文（修订发生在任何 A4 数字存在之前）。

#### E.1b 作者裁决（2026-09-07）：Ch1 门同样重新界定，IP&M 口径核实前置到 E6 之前

E4 把两个问题交给作者后，作者当日给出两条裁决。完整依据见
[`results/PHASE_R1.md` §15](results/PHASE_R1.md)。

1. **Ch1 也改门，理由与 §E.1a 同构**：MAVEN-ERE 文档内共指上除主锚外**没有第二个公开可跑的方法**
   （IP&M 2024 无代码 · OmniEvent EAE checkpoint 失效 · TextEE 无 checkpoint · RESIJ 未取得 ·
   CorefPrompt 正依赖那个失效 checkpoint）。E.1a 给 Ch2 加「不弱于主锚」是为了挡稻草人，对 Ch2 有意义
   （LLMERE 真可能强）；对 Ch1 不成立——唯一有公开仓库的 ACCI 是跨文档方法，`ECB+ 88.4` 不保证过
   `.809847`，**大概率低于主锚**，维持原措辞会让移植的期望价值接近零。新措辞是四条同时成立：
   **独立发表工作的机制 · 在其原始基准上有强证据 · 我们在冻结协议下跑通 · 缺口逐表写明**。
   `SPEC.md` 不修订；`taco` 式自造弱变体仍被第 1 条挡住。
2. **顺序倒过来：先静态核查，再谈训练**（队列 E10）。理由是 E2 刚教过——**仓库有方法本体不等于有
   trainer**（LLMERE 全历史 5 个 commit 无训练代码）。核查成本近零却直接决定这条路通不通。
3. **`qwen3-argument-s13-r2` 角色重定义**：它低于主锚不是废数据，而是「**朴素把预测论元池化进编码器
   会掉点**」的注册负面对照，正是 C5 立论的直接证据。**不再充当第二方法族。**
4. **IP&M 2024 口径核实前置到 E6 之前**（队列 E9）：该文同时报 **causal 37.4** 高于 Ch2 主锚 33.17，
   而 E6 就要冻结 A4 契约——**先核实再冻结，别用一个可能已被超越的及格线冻结整章**。
   判据用 MAQInstruct 那把现成的尺子：**看它复现的 official joint baseline 与我们自跑官方码是否对齐**。
   三种处置（可比 / 口径不同 / 拿不到全文）见 §15.3。无论结果如何**它都不能进 roster**——无公开代码，
   按 FR-006 无法在我们协议下跑通。

#### E.3 GPU 使用（2026-09-16 重写，旧边界已被两次裁决取代）

卡是公用资源，**不得为了「看起来在跑」启动无准入的训练**；但**卡空着也不要串行**
（约束分级的 C 类，见 `CLAUDE.md`）。

| 机器 | 现行规则 |
|---|---|
| **gpu-5090** | 🟢 **主力机**。作者 2026-09-11 第二次裁决 + 2026-09-15 追认：**≤1 天的任务直接执行，不必逐次请示**；超过一天、拉模型、跨机搬运仍须先问。**长任务 pilot 可以放这里**——C5 整条就在这台机上。 |
| **gpu-4090** | 有空即可自用（本地三件套全绿后无需逐次点头）；**不挤占他人正在跑的卡**。当前四卡被他人占满第 6 天。**A4.3 必须在这台机上**，因为它的判定线含在 4090 pin 上训出来的 32.10（§0.4a）。 |
| 两台通用 | 选卡前 `nvidia-smi` 核卡；长任务 `setsid nohup` + `python -u` + 重定向 `logs/`，**一条 ssh 只发一个后台任务**；checkpoint 训在哪留在哪；**多种子始终另行授权**。 |

⛔ **已被推翻、不要再照着执行的旧条款**（原文留在附录）：「主体实验仍回 4090」「长任务 pilot 一律
不放 5090」「5090 每次使用须逐次授权」「Qwen3-8B 装不下 5090」——最后一条在 2026-09-13 实测作废
（那个约 17 GB 的服务早已不在，卡上只有 197–209 MiB 常驻）。

⛔ **仍然成立的硬边界**：EasyECR 跑不了 5090（`torch==2.0.1` 不支持 sm_120）；
SimKGC 的 `--batch-size 1024` 要 4×32 GB，两台机都装不下（§0.5a ④）。

**Ch1 的 ACCI GPU 需求已取消**：E10 判定其公开仓库 `not_runnable`；不得从论文散文重建后称作透明移植。

## 4. R1 后的候选方向：不是固定答案

以下只用于指导 R1 反证与对照设计，不能绕过 R1 直接实现：

- **Ch1/C5**：mention-local predicted argument-role posterior + uncertainty-gated clustering；gold event-level
  arguments 仅作 oracle；
- **Ch2/A4**：完整候选全集上的 pair evidence + sufficiency/abstention risk；retrieval/hard negatives 只能
  改变训练/evidence，不能裁评测候选；
- **Ch3/D4**：typed cue spans + known/unknown → modality → polarity；五类 macro-F1 仍是主门；
- **Ch4/E3**：三类真实上游的同实例 factorial；固定 queries/candidates/checkpoint，验证消费者预测有效性
  与图依赖后再解释主效应和交互。

R1 若证明上述候选与近期工作重复、数据不支持、功效不足或中介不可识别，应提出实质不同且更简单的
候选，并在 `RESEARCH_PLAN.md` 版本化记录。不要为了维护 v6.1 名称而维护错误方法。

## 5. 永久红线与服务器规则

- final-valid 不参与结构、超参、threshold、epoch、stop 或 claim 选择；历史访问继续披露；
- manifest、候选全集、evaluator、输入前提、TIMEX 开关必须成对一致；
- Ch1–Ch3 必须在统一公开主指标上超过主锚和另一强方法族，并通过 matched seeds、document-cluster
  paired CI、guardrails、核心消融和负控；辅助指标不能替代；
- oracle 明确标 non-deployable；缺 ID、未知端点、schema/hash 漂移立即 fail-fast；
- 数字下降、零结果、SSH/工具失败均如实记录；
- 本地禁止 GPU；4090 长任务启动前展示命令/cwd/产物；5090 每次单独取得授权；
- 服务器只用 `.venv/bin/python`，不得 `uv run`/`uv sync`；
- 不运行 `rsync --delete`、远端 `git clean -fdx`，不宽目录递归删除；
- checkpoint 训在哪留在哪；跨机搬运先问作者并做双端 SHA-256；
- 一条 SSH 只启动一个后台任务；长任务使用 `setsid nohup`、`python -u` 和独立日志；
- 改代码后必须运行 `uv run pytest`、`uv run ruff check src tests scripts`、`uv run ekg-smoke`。

## 6. 完成、回填与交接程序

一项任务走完下面五步才算完成；缺任何一步，下一个窗口都不得开工。

1. **产物落地**：命令、日志与 artifact 落到 `runs/stages/<PHASE>/<run root>/`；跨机产物双端 SHA-256 一致。
2. **写结果页**：数字只写进对应的 `results/PHASE_*.md`，升降如实、失败如实；其他文档只引用不复制。
3. **回填队列**：把任务 E.2 表里该行 `状态` 改成 `done`，`commit` 填短 hash；没做完改 `wip`
   并在该行写清卡在哪条证据上，不留只有自己知道的上下文。
4. **推进队列**：确认下一行前置已满足。**整条队列清空时**，由本次持有者按 §3 依赖图和
   [`TASKS.md`](TASKS.md) 生成下一批 E 队列写进本表，**先写表再开工**，并同步更新顶部当前阶段卡片。
5. **提交并推送**：按逻辑单元 commit，`git push origin main`。**没 push 就没交接。**

最终回复用这六行，不写长篇叙事：

```text
完成：<E 队列序号 / task ID>
身份：<commit / protocol hash / bundle ID>
验证：<实际命令与 PASS/FAIL>
结果：<只引用 docs/results/PHASE_*.md 位置>
状态：done | wip | blocked；原因
下一步：<E 队列里下一个 todo；是否需要 GPU / 多种子 / 作者授权>
```

长 GPU 任务启动前，仍须按 §5 向作者展示完整命令、cwd 与预期产物；5090 每次单独取得授权。

---

## 附录 · 历史记录（按需查证，不必通读）

> 下面三块是 2026-09-11 → 09-15 的过程记录：旧队列、已裁定的决策菜单、逐轮做了什么。
> **结论都已上提到本文前半部分或写进 `results/`，这里只保留推导过程与当时的一手证据。**

<details><summary><b>附录 A · 旧队列与 Ch4 的三段追因（原 §0.3 / §0.3a / §0.3b / 旧 §0.4）</b></summary>

### （历史）0.3 旧队列 · 2026-09-15 版

> **五项裁决已全部裁定（§0.5a），队列不再卡在决策上，卡的是那一张卡。** 现在的顺序是：

| 次序 | 主表 ID | 做什么 | 状态 |
|---|---|---|---|
| 1 | **G-4 探测** | A4 (戊) 单臂 `full`（5090） | 🟢 **运行中**，预计 2026-09-15 ~16:40 收。判据写在 §0.5a，**是 `base 判正数`不是 F1** |
| 2 | **G-5** | **C5.3 seed-13 pilot（三臂）**，5090 线 | ⏳ 等第 1 项让出卡。preflight `a3f21f97…8141` 与双半边 smoke 都已 PASS，命令只要 `--contract` + `--output` |
| 3 | **G-11a** | CSProm-KG：解包 → 装 torch（清华镜像可用）→ 用 WN18RR checkpoint 跑一次推理取 (a) | ⏳ 代码已在 5090，checkpoint 本地下载中。**只需推理，不训练** |
| 4 | **G-4 探测 2** | A4 戊-only（撤掉根因 A 的 detach），隔离 A | ⏳ 排在 C5.3 之后；A4.3 反正要等 4090，不急 |
| 5 | **G-4** | A4.2 smoke → A4.3 pilot | ⏳ **必须在 4090**（backbone pin，见 §0.5a 的表）；且要先重建 `preflight-r2` |
| 6 | 名册回填 | LLMERE 记 (b)、SeDGPL 的 ESC 记 (b) | ⏳ 纯文档，随时可做 |

**⛔ 仍然一律不做**：D4 第二个周期、调 threshold、扫 epoch、换 split、加大 backbone、用 seed 17/42
去捞 D4、把「五维瓶颈」当成已证结论去改设计。

<details><summary>2026-09-13 的旧队列（已完成的九项，留作记录）</summary>

**Gate 1 的裁决是事先写死的，不要重议**：`EXPERIMENT_PLAN.md` §5 的 Gate 1「不过」分支写着
**不启动第二个周期，直接进 Gate 2 讨论结构**。D4.3 不过，所以 typed-cue 家族到此为止。
`PHASE_D4` 的 stop conditions 里那句「两个有效周期后封存」允许第二轮，但**主表的 Gate 1 更具体
且先于结果冻结，以主表为准**——Gate 存在的意义就是结果难看时不临时给自己加一次机会。

⛔ **因此下面这些一律不做**：D4 第二个周期、调 threshold、扫 epoch、换 split、加大 backbone、
用 seed 17/42 去捞 D4、把「五维瓶颈」当成已证结论去改设计。

**上一轮已完成，不要重做**：**C-6**（`790c35a`）与 **C-6b**（`65cf64b` → `323fd7a`）——
A4 的机制 `src/ekg/relations/pair_evidence.py` + `pair_evidence` 头 + 五个入口脚本
（`train_` / `evaluate_` / `prepare_*_preflight` / `smoke_` / `run_a4_pair_evidence.py`），
44 条 targeted tests，**592 passed / 28 skipped、ruff 0、smoke OK**，5090 四臂开发冒烟 pass。
设计变更与三个被冒烟抓到的缺陷见 §0.4 与 `results/PHASE_A.md`。

**CPU 队列，按这个顺序做，全部不占卡：**

| 次序 | 主表 ID | 做什么 | 完成判据 |
|---|---|---|---|
| ~~1~~ | ~~**C-5b**~~ | ✅ **已完成 2026-09-13**（含原第 2 行的 pilot 入口）。缺口比这里原本写的小：`train_`（`train_coref_scorer.py`）、`evaluate_`（`score_maven_ere_official.py`）与预测器（`build_maven_ere_submission.py`）**本来就有**，只缺三个脚本加一个开关。执行中抓到三个真缺陷，其中一个是 A 类（permutation 臂训练/推理口径不成对）。详见 [`results/PHASE_C.md`](results/PHASE_C.md) | 608 passed / 28 skipped、ruff 0、smoke OK |
| ~~2~~ | ~~C-9 同类缺口~~ | ✅ 并入上一行：`scripts/run_c5_argument_uncertainty.py` 已存在并进了 preflight 的 `CODE_FILES`（8 个文件） | — |
| ~~3~~ | ~~**C-7**~~ | ✅ **已完成 2026-09-13**。三章 CPU fixture 各自被**该章自己的 evaluator** 打出分；配置移进 `configs/`（`data/protocols` 是 gitignored，hash 在 git 外没有追溯价值）。详见主表 §4.1 |
| ~~4~~ | ~~**C-10**~~ | ✅ **已完成 2026-09-13**（纯 CPU，2.6 s）。`runs/stages/E3/e3-v61-20260913/`：1,908 实例，`queries.jsonl` `e92629bd…5aecf`、candidate-ID digest `93915ae3…f27ee`、生成器 tree `588c02c0…8abf`。**n 与 2026-07-29 那批已发表数字一致**，G-11a 的四个对手现在有同一把尺可用。`--verify` 可随时重建三比对。详见 [`results/PHASE_E.md`](results/PHASE_E.md) |
| ~~5~~ | ~~**C-4b**~~ | ✅ **已完成 2026-09-13**（一手核查，纯 CPU 未训练）。裁决 `conditionally_runnable`；**切分口径 = 原文 §5.1 声明的 topic 级 5 折 CV**（最后两 topic 作 dev），**不是**文档切分。⚠️ **推翻了「19.6 是泄漏值」这条记载**——原文声明的就是非泄漏口径，我们只是在该口径下复现不到（.0599 vs .196）。三个透明补丁（自写 loader / 用它自己的 `collect_mult_event` 重建 ESC 词表 / 把 `util.py` 被注释掉的 assert 加回去，否则半数候选静默错打分）与两处未公开自由度见 [`results/PHASE_E.md`](results/PHASE_E.md)。**建议只为 SeDGPL 走 (a)，其余四个维持 (b)** —— 待作者裁决，不阻塞 G-11a |
| **6** | **G-11a** | **Ch6 四个外部对手复现（跑 5090）** | ⏳ **第一刀 done 2026-09-13**（纯 CPU）：四个仓库已 clone 并核到 commit/数据/依赖。**结构性事实——四个对手没有一个实现 CGEP**，SeDGPL 作者做的适配从未发布 ⇒ 四行在我们的重建协议上注定 (b)，(a) 只能在各自原基准上取得。**MCPredictor 数据需 LDC2011T07 许可 → (b)**。⏳ **第二刀 2026-09-14 起步即受阻**：SimKGC 已搬到 5090、环境无 torch 版本墙、预处理 PASS、AdamW 透明补丁已记 hash，**但训练要 4×32 GB，两台机器都装不下**（它自己 README 第 18/111/116 行）。⚠️ **第一刀把 SimKGC 排「最便宜」是漏算了训练显存**；建议改序先做 CSProm-KG（**有公开 checkpoint，(a) 靠一次推理**）——**等裁决 ④**。详见本节下方与 [`results/PHASE_E.md`](results/PHASE_E.md) |
| ~~7~~ | ~~**C-8**~~ | ✅ **已完成 2026-09-13**：[`PROTOCOL_TABLE.md`](PROTOCOL_TABLE.md)，四章三轴 + 计数 + 指标定义 + final-valid 台账 + 信任根，每节带重算命令。本地重算核对：候选 digest `15a3b1a5…` 与 291/7,195/1,719/234,870 逐项吻合。⚠️ 顺带修掉 `CLAUDE.md`/`AGENTS.md` 里过期的 P1 可信根（r12 → **`p1-v6-20260904-r15` / `1e31a9ac…f9655`**） |

**为什么这么排（不是按主表编号，是按"卡住谁"排）**：Ch6 是**唯一不依赖任何方法章成败的一章**
（§7.5 下行情形里它照样成立），也是耗时最长的一项。Gate 2 判的是还剩几个方法章，判完之后再启动
Ch6 就来不及了。C-8 是纯整理、随时可做，所以垫后。

> ## ⚪ 2026-09-14 收盘：**队列全部停在裁决上，不是停在算力上**
>
> 主表 §4.1 的九项 CPU 泳道任务早已全部 done。本轮又把三件不占卡的做完了
> （dry-run 收尾、smoke 报错信息、SimKGC 搬运与预处理）。**现在剩下的每一件要么等卡、要么等裁决：**
>
> | 泳道 | 状态 | 挡住它的是什么 |
> |---|---|---|
> | **G-4（A4）** | ⛔ **等裁决** | recall 塌陷的设计选择（§0.3a）。**且无论选哪条，都要先重建 `preflight-r2`**——四个被契约钉住的文件都改过了。裁决前重建会重建两次 |
> | **G-5（C5）** | 🟡 **等卡即可，无裁决阻塞** | C5.2 的 CUDA 半边 → C5.3 pilot。⚠️ 跨机契约问题：preflight 产物在 4090，5090 的 R1 protocol 是空 `phase_contracts` 旧档（§0.6） |
> | **G-11a（Ch6）** | ⛔ **等裁决** | SimKGC 训练要 **4×32 GB**，5090 单卡装不下（**硬件，补丁解决不了**）。建议改序做 CSProm-KG——见下 |
>
> **5090 现在完全空闲。** 如果要在裁决之前用掉这张卡，**唯一不需要裁决的是 G-5 的 C5.2 CUDA 半边**；
> 其次是 §0.3a 建议的**单跑一臂隔离根因 A**（约 1 小时，纯诊断，不改设计）。

#### G-11a 第二刀的进展与建议改序（2026-09-14）

**已完成、不必重做**：四个对手仓库的静态核查（第一刀）；**SimKGC 已搬到
`gpu-5090:/mnt/aidata/tongjiakai/baselines/`**（ekg 仓库之外，不受远端 `git reset` 波及），
双端 sha256 一致、commit `97cc43e488f19ca5…` 已复核；环境无 torch 版本墙；
**WN18RR 预处理 PASS**（test n=**3,134**，与结果页此前重算其已发布预测的计数逐位一致）；
**AdamW 透明补丁**已打并记前后 hash。

⛔ **但 SimKGC 训练卡在「算力」**（一手证据是它自己的 README）：
第 18 行 **"All experiments are run with 4 V100(32GB) GPUs"**，第 116 行**不支持 DDP**，
第 111 行对 OOM 的回答就是「资源不够请减 batch」。冻结的 `--batch-size 1024` 要 **4×32 GB = 128 GB**；
5090 单卡 32 GB、4090 四卡 96 GB **都不够**。
**减 batch 不算绕开**——SimKGC 是对比学习，**batch size 就是 in-batch 负样本数**（名字里的 IB），
减了按定义就复现不出 66.6。

**⇒ 建议改序：CSProm-KG 提到 SimKGC 之前。** 第一刀把 SimKGC 排「最便宜」，依据是
数据随仓库 / 预测已发布 / 依赖无上限——**三条都对，但没有一条是显存**：

| 方法 | (a) 怎么取得 | 显存 | 版本墙 |
|---|---|---|---|
| **CSProm-KG** | **公开 checkpoint + 推理**（README §33） | `-batch_size 128`，**且只需推理** | 有（`torch==1.11.0+cu113`，升版=透明补丁） |
| SimKGC | **必须训练**（已发布预测缺 `rank`，省不掉） | **4×32 GB** | 无 |

**补丁能解决版本墙，解决不了硬件。** ⚠️ CSProm-KG 的 checkpoint 在 **Google Drive**，
而两台服务器都没有外网（§0.6）⇒ 仍要本地下载后 scp。

⚠️ **第三堵版本墙，形态与前两堵相反**：CSProm-KG / mcnc 是 `torch` **太旧**跑不了新卡（sm_86），
SimKGC 是 `transformers` **太新**删掉了它用的 `AdamW`。名册 §6.2a 那句「SimKGC 依赖无上限、
不受影响」**只对 torch 成立**。⇒ **核依赖不能只看下限，要核它用的符号在新版本里还在不在。**

</details>

### （历史）0.3a Ch4 当时卡在哪：一次 dry-run、一次失败的修复、一个待裁决的设计问题

三件事按时间顺序，**证据全部在 [`results/PHASE_A.md`](results/PHASE_A.md) 末三节**，这里只留结论。

#### ① 四臂 dry-run（2026-09-14 03:07 完成）：pipeline PASS，抓到两个 Bundle 缺件

12.5 小时跑完 50 epoch × 4 臂 + aggregate，`status=pass`，契约隔离守住
（`contract_sha256 7731f0d1…` 是 probe 契约，非 A4.1 的 `321309ac…`）。
按契约 Bundle 清单逐项核，**少两样**，已补（`d595439`）：

- **checkpoint hashes**——`artifact_sha256` 只覆盖产物、不覆盖产出它们的权重。现每臂带
  `checkpoint_content_sha256`，`aggregate` 拒绝没有它的臂；
- **`fallback_component_bundle_id`**——四份 phase 契约都点名，**全仓库从未实现**。现从契约的
  `baselines.a3_fallback.predictions_sha256` 取，无 fallback 时显式 `null`。

⚠️ **命名**：契约与本节原文写的 `pilot.json` / `status.json`，实际是 **`pilot_summary.json` / `arm.json`**。
⚠️ **一个会骗人的计数**：顶层 `candidate_pairs` **348,632 不是**候选全集 **234,870**
（前者含 TIMEX 参与的对）。**写表一律引 `mediator["pairs"]`**，已记进 `ENGINEERING_NOTES.md`。

#### ② 四臂读数与真正的病灶（**探测 backbone，不进主表、不与 33.17 / 32.10 相减**）

| 臂 | evidence_stream | consistency_loss | **base 判正** | 修正后 | causal R | causal F1 |
|---|:--:|:--:|---:|---:|---:|---:|
| `remove_core` | ✗ | ✗ | — | **4,355** | 29.80 | **31.23** |
| `no_constraint` | ✓ | ✗ | 1,385 | 908 | 6.61 | 11.12 |
| `full` | ✓ | ✓ | 766 | 577 | 4.48 | 8.00 |
| `length_matched` | ✓ | ✓(+替代控制) | 179 | 125 | 1.52 | 2.97 |

**推理修正只砍掉 24.7%–34.4%，base 判正数本身差 5.7 倍** ⇒ **塌陷在训练侧**，
且就算关掉推理修正，`full` 的 recall 上限也只有约 16%。

#### ③ 按此修梯度路径 → **训练发散，修复失败并回滚**（`24b3924`）

| epoch | dry-run | 修改后 |
|---:|---:|---:|
| 0 | 2.6729 | **5.4948** |
| 1 | 1.3228 | **15.27** |
| 16 | — | **2213.87** |

`dev macro_f1` 17 个 epoch 恒为 `0.0000`，2h29m 后人工中止。

**为什么失败**：`sufficiency` 对 `gold_base` 的 +1 梯度**确实是**退化解（「span 足够」可靠压低完整
上下文满足），**但它同时是这个损失唯一的阻尼**——`necessity` 对 `gold_base` 是 −1，两者等大反向。
摘掉压低那侧 ⇒ necessity 自由推高 `gold_base` ⇒ sufficiency 推高 `gold_retained` ⇒
两者**共享 encoder 与 head 参数** ⇒ 正反馈无界。
已把这次测量写进 `sufficiency_necessity_loss` 的注释与一条新测试（断言两项梯度等大反向），
**免得下一个窗口再 detach 一次**。

#### ⇒ 真正的问题（交裁决，不再自行打补丁）

base 判正塌陷**不是退化解污染训练**，而是这对约束的**平衡点偏保守**，原因是**两项作用面不同**：

| | 作用面 | 对 `gold_base` |
|---|---|---|
| `necessity` | 仅 `positive & scoreable`（两触发句之间**有 interior** 的行） | 推高 |
| `sufficiency` | **所有** `positive` 行 | 压低 |

⇒ **相邻句与同句正例只有压低的力**。这是「触发句 protected、短距离不是误差所在」那条设计决定的
直接后果——短距离对被排除出 necessity，**却没有被排除出 sufficiency**。

| | 做什么 | 风险 |
|---|---|---|
| **(戊) 推荐** | 把 `sufficiency` 也限制在 `positive & scoreable` | 最小改动、恢复每行上的制衡；但缩小作用面，机制强度未知 |
| (己) | 给短距离正例补对称项 | 等于新增机制，要重新论证 |
| (甲) | 原样跑 A4.3，如实交 Gate 2 | 契约已预判失败（recall collapse 是明列 stop condition） |

⚠️ **根因 A 仍无结论**：失败那跑**同时带着 A 和 B**，把发散归给 B 是数学推理不是实测。
A（`cf["retained"].detach()`，阻止 encoder 被残缺输入训练）**仍在代码里、未回滚**。
**建议先单跑一臂 `full` 约 1 小时**，一次回答两件事：不带 B 会不会发散、A 单独能否把 766 抬起来。
命令与 ② 的 dry-run 同形，只需 `--arms full` 与一个新 probe 契约（重哈希脚本见下）。

#### 重跑前必须知道的两件事

1. **改了被契约钉住的代码就必须重建契约。** 那四个文件都在 `CODE_FILES`（7 个）里，
   probe 契约同样钉它们——第一次启动被
   `PilotError: bound code hash drift: scripts/run_a4_pair_evidence.py` 挡下，**这是对的，别绕**。
   探测用的重哈希脚本已验证可用（只改 `code` 与 `probe_note`，其余原样）；
   **正式的 `preflight-r2` 仍要在 4090 上用 `prepare_a4_pair_evidence_preflight.py` 重建。**
2. ⚠️ **本地三件套全绿不代表能跑。** 本地无 torch ⇒ 新的梯度断言在本地是 `skip`，
   **第一次上 5090 就 FAIL**（测试自身写错，`4e9b0bd` 修）。**任何 torch 相关改动，
   推之前先 ssh 到 5090 跑一次那个测试文件。**

### （历史）0.3b 4090 被占时的方针（作者 2026-09-13 定，仍适用）

> 原话："你不要老是说 4090 不行，4090 不行，就去 5090 上去，把后面的探测性方法先搞好，
> 确保我们后续在 4090 上跑就是有效的。"

**把"等 4090"换成"把能先验的先验完"。** 判断一件事该不该在 5090 上先做，只问一句：
**它能不能减少那一次正式跑白跑的概率？**

| 在 5090 上**该**做 | 在 5090 上**不该**做 |
|---|---|
| 端到端 dry-run：入口脚本、产物清单、中介统计、aggregate 断言 | 拿探测分数去调设计、挑参数、改阈值——**那才是污染** |
| 实现地板诊断（G-13 那类：消融臂能不能训到该到的量级） | 把探测数字写进主表，或与契约 backbone 的数字相减 |
| 依赖关系与数据可用性核查、外部对手的环境与 import 冒烟 | 用探测结果替代正式 pilot，或据此宣布过门/未过门 |

**已经这样做过并有效的两次**：G-13（实现地板，排除了 D4 那类"机制上场前就输了"的失败原因）、
本次四臂 dry-run。**5090 单臂实测 56 分钟**，算力从来不是瓶颈。

**GPU 泳道**：
- **G-4：A4.1 ✅ 已 PASS（2026-09-13，纯 CPU）**；**四臂 dry-run ✅ 已完成并收尾（2026-09-14，见 §0.3a）**。
  本行现在是 **preflight-r2 重建（4090 纯 CPU，等裁决）→ A4.2 smoke → A4.3 pilot**，
  后两者等 ① 一张空闲卡 ② 作者授权长任务。⚠️ **A4.2 必须带 `preflight-r2` 的 `protocol.json`**，
  不是原 `preflight/`——`run_a4_pair_evidence.py` 与 `smoke_a4_pair_evidence.py` 都在那 7 个
  `CODE_FILES` 里，`d595439` 改了前者。**A4.2 可以现在就在 5090 上跑**（§3.5 授权 ≤1 天任务，
  实测 5090 完全空闲：209 MiB / 32,607 MiB、24 核 load 0.05），**它不必等 4090**。
  A4.2 必须带 `--contract runs/stages/A4/a4-v61-pair-evidence-r1/preflight/protocol.json`；
  `gpu-5090:runs/stages/A4/dev-smoke-20260912/` 那份开发冒烟**不算 A4.2**。
  ⚠️ 注意 5090 上 `r1-v61-20260904/protocol.json` 是 09-04 的旧档（`phase_contracts` 为空），
  preflight 产物本身在 4090，跨机跑 A4.2 前先想清楚契约文件从哪读。
- **G-5（C5.2 smoke → C5.3 pilot）**：✅ **C5.1 preflight 已 PASS（2026-09-13，4090，纯 CPU）**，
  `protocol.json` **`9402e880…e4319`**、`code_files=8`、`final_valid_accessed=false`；两条 baseline 用官方
  evaluator 独立重算得 **主锚 MUC 80.98472 / 注册对照 80.367586**，与 C-5b 的本地预验逐位一致。
  ⚠️ **自物化的 internal-dev gold `403b69a8…` 与 A4.1 那份同哈希** ⇒ Ch4/Ch5 站在同一候选全集上。
  上一轮写的阻塞理由是**错的**：那份合并论元预测一直在 4090，只是**结果页只记了哈希没记路径**，
  实际位置是 `runs/stages/R1/r1-v61-baseline-closure-r3/ch1/qwen3-full-r3/merged/predictions.jsonl`
  （由注册对照 `metrics.json` 的 `scorer_path` 指出来）。本轮另把主锚与对照的预测 scp 到 4090 并双端核过。
  ✅ **C5.2 的 CPU 半边也已 PASS**（4090，`CUDA_VISIBLE_DEVICES=`）：`smoke.json` `30bae362…89b0`，
  三臂 config 两两不同、permutation 种子 13 往返 checkpoint 成功、四种 CPU fixture 形状全过。
  冒烟抓到两个真缺陷：① smoke 只 subset 了语料没 subset 论元预测（`extra predictions=73497`），
  已修（`886a440`，根因在 subset 的一方，**不是**去放宽 trainer 的 fail-fast）；
  ② 改了被契约钉住的 smoke 脚本 ⇒ 按 D4 先例**新建 `preflight-r2/`**
  （`8a5ed864dea501a067339c3031bdcd750c598e900d54fdf9c2448ce13ccb7868`），旧 `preflight/` 不覆盖；
  重建顺带证明两条 baseline 分数逐项可复现。
  **下一步：C5.2 的 CUDA 半边（去掉 `CUDA_VISIBLE_DEVICES=`，比对两半边产物）→ C5.3 pilot，都要一张空闲卡。**
- 两者**写不同 namespace，可并卡**。跑完这两个就到 **Gate 2**。

### （历史）0.4 Ch4 设计自审与 A4.1 收尾

#### 设计已按证据自审改过一轮（`f90c8cd` / `3019dd3` / `323fd7a`）

初版用**连接词词表**排序候选句去选证据。**被本项目自己的数据否掉**：`results/PHASE_A.md`
2026-08-30 的分层测量只差 .008（同句）/ .064（跨句），当时的结论就是「不做连接词感知的上下文表示」；
本轮补测（60 篇 / 109,234 对）显示词表把 **79.3%** 的对判成有线索，长跨度上排不出先后。
**引用了结果页的假设却没读结果页的结论，是同一类错误的第五次。**

现行设计（细节与三个冒烟缺陷见 `results/PHASE_A.md` 的 A4 节）：

1. **证据是「定义」不是「选择」**：一对的证据 = 两触发句之间的 interior。不排序、不打分、
   无预算、无阈值。necessity = 去掉 interior；sufficiency = 只留该对 span。对齐 causal 误差结构
   （FP 占 83.6%、跨句 FP 78.4%、59.4% 长距离、precision .1998 而 recall 只差 .062），
   误差剖析自己写的下一步就是「evidence/context 选择」。MAVEN-ERE 无证据标注（已核），
   所以 EIDER/SAIS/DREEAM 的监督式证据用不了，**DREEAM 的 self-training 记为升级路径**。
2. **注册中介不变**：`cross_sentence_false_positives`，无需干预即可算。细分改为**行为量**
   （去掉 interior 后 logit 掉幅 < 冻结 margin），自带「被测到的」分母。
3. **推理修正所有 base 判正的行**，每篇 16 对的 cap **只用于训练**（反向要保活活化值）；
   第二段训练分布**一半金标正例 + 一半当前假正例**，否则它会一律说 NONE（实测过）。
4. **触发句 protected**：同句/相邻对没有 necessity 项——这是如实的，短距离不是误差所在。

**DREEAM 替代方案已核并否掉**（2026-09-13，静态核查，未训练未占卡，详见 `results/PHASE_A.md`）：
仓库完整（`476a7004…f291`，MIT）但**两条证据监督路径都要人工证据标注**（`sent_labels` 或
`teacher_attns`，而教师本身训在人工证据上），MAVEN-ERE 一处标注都没有，也没有 distant 语料；
其评测增益还依赖 dev 选阈值（契约禁）。**一手数字**：在「无 distant 数据」这一格里，
它比自己的 backbone ATLOP 只高 **+0.33 F1**，且低于 EIDER 与 SAIS；headline SOTA 来自
10 万篇远监督自训练那一格。⇒ `not_runnable`，且**这条核查反过来把 A4 的立论写强了**：
EIDER/SAIS/DREEAM 整条证据线都要标注，MAVEN-ERE 上封死，而反事实是**无标注条件下**
取得证据式行为的路，自带验证协议。**A4 第一个周期维持 interior 定义式，不改。**


</details>

<details><summary><b>附录 B · 已裁定的决策菜单（原 §0.5；裁决结果见 §0.5a）</b></summary>

### （历史）0.5 四项决策菜单（已由 §0.5a 裁定）

> 写法要求（作者 2026-09-13）：**不要只说「需要裁决」。** 每一项都要说清为什么要在这里做选择、
> 每条路各自的问题、对**论文**和对**实验**分别是什么后果、以及**同行是怎么做的**，然后给出推荐。

#### ⚠️ ③（**阻塞 G-4**，2026-09-14 新增）：A4 的 recall 塌陷怎么办

**完整分析在 §0.3a**，此处只留一句：塌陷是 `sufficiency` 与 `necessity` **作用面不同**导致的
平衡点偏移，不是 bug；已经试过改梯度路径，**训练发散**。
**推荐 (戊)**——把 `sufficiency` 也限制在 `positive & scoreable`，与 `necessity` 作用面对齐。
**并建议先花 1 小时单跑一臂隔离根因 A**（纯诊断、不改设计、不需要这项裁决就能做）。

#### ⚠️ ④（**阻塞 G-11a**，2026-09-14 新增）：Ch6 是否改先做 CSProm-KG

**完整分析在 §0.3 的 G-11a 行**。SimKGC 训练要 **4×32 GB**，两台机器都装不下，
**减 batch 会按定义复现不出它的数**（batch size 就是它的 in-batch 负样本数）。
CSProm-KG 有**公开 checkpoint**，(a) 靠一次推理即可。**推荐改序。**
若作者仍要先做 SimKGC，那就只能走 **(A) 减 batch + 如实标注**，该行落 **(b) 透明适配**，
障碍写「原配置需 4×32 GB」。

#### ①②：以下两项是旧的，**不阻塞任何队列**
（⑤ 在 §0.3 队列第 5 行：是否只为 SeDGPL 走 ESC 的 (a)，其余四个维持 (b)。同样不阻塞。）

#### 决策 ①：A4 推理时机制动不动手（决策 3）

**为什么这是个必须现在定的选择**：它改的不是实现细节，而是**被评分的那条规则**。A4.3 一旦跑出数字
再换，那一轮直接作废——因为四臂的可比性建立在"推理口径一致"上，换了口径就不是同一个实验。

| | **(A) 两段式修正（现状，已实现已冒烟）** | (B) 只作训练目标 |
|---|---|---|
| 推理 | base 判正的行用证据残差重打分 | 四臂推理口径完全一致，反事实只作测量 |
| 机制作用通道 | 两条（encoder 表示 + 修正头） | 一条（只有 encoder 表示） |
| 冻结矩阵第 8 臂 | 原样（"证据表示保留、约束关闭"） | **含义改变**，等于动冻结矩阵 |
| 归因 | 第 8 臂负责分离"修正头的功劳"与"一致性的功劳" | 天然无此问题，但也失去这条信息 |

**同行怎么做——两条路都有先例，但分属不同条件**：

- **EIDER**（Xie et al., ACL Findings 2022）与 **SAIS**（Xiao et al., NAACL 2022）属 (A) 类：
  抽出证据后**在推理时重构输入再预测一次**，然后融合两次结果。
- **DREEAM**（Ma et al., EACL 2023）属 (B) 类：证据只作 attention 的监督信号，**推理时不做二次修正**。

⚠️ **但 DREEAM 那条路我们走不了，这已经核实过**（`results/PHASE_A.md`，`b52d506`）：它的证据监督要
人工证据标注或一个训在人工标注上的教师，MAVEN-ERE 一处标注都没有。**能让 (B) 成立的那个前提，我们不具备。**
而 EIDER 的融合要一个 blend 超参，我们的契约禁扫参——所以我们取的是 (A) 里**不含可调融合权重**的窄形态。

**对实验的影响**：D4 刚刚演示过单通道机制的下场——full 低于 remove-core 6.0 个点，
连负控都赢过 full，**机制在 encoder 一条通道上没能把信号传出来**。(B) 把 A4 放回同一个结构里。

**对论文的影响**：A4 的立论是"**反事实**证据充分性/必要性"——去掉 interior 后 logit 掉多少。
这本质上是一个**推理时的量**。选 (B) 等于承认这个量只配当训练信号，立论会被削弱到
"我们加了一个辅助损失"，那和 §7.2 主表想讲的故事不是一回事。
(A) 的可质疑点是"推理时二次打分是否用了额外信息"——契约已封死这一条：修正只读 base 自己的预测和
文本 interior，**不读金标**，第 8 臂 `no_constraint` 专门用来分离两个通道各自的贡献。

**推荐：维持 (A)，不改。** 它与立论一致、与可行的文献先例一致、已实现已冒烟，且改动成本是重新冻结矩阵。
**若作者仍倾向 (B)，必须在 A4.3 出数字之前说**，此后不再接受变更。

#### 决策 ②：LLMERE 的保真度路径（C-3 / 名册 §2.1）

**为什么要选**：FR-016 要求每个外部复现自证正确。LLMERE 发布了它在 official valid 710 篇上的预测，
所以最直接的验证是用官方 `evaluate.py` 给它打分、看能否复现其 causal 36.04。
**但 710 篇就是我们封存的 final-valid**，而 `HANDOFF` §E.1a 第 6 条（作者 2026-09-07）明确写着不做这件事。
两条规则互相抵触，这是冲突本身要求的选择，不是可以拖的事项。

| | 问题 | 对论文 | 对实验 |
|---|---|---|---|
| **① 记为 (b) Unverifiable**，障碍写明"验证需读封存 final-valid，按 A 类红线放弃" | 少一个"已验证"的对手 | Ch4 主表该行标 (b) 并列出障碍——**QR-001 v1.1.0 本来就允许** | 成本零，不碰 final-valid |
| ② 只做一次**评分性**读取，记入 ledger | 在 A 类红线上开口子 | 能把该行升到 (a) | 一次读取不选模，但"只读一次"这条边界日后很难守 |
| ③ 放弃 LLMERE，另找关系方法族 | 成本最高 | 需要重新复现，按基准率 4–9 天且首次多半失败 | 挤占 Gate 2 之前的时间 |

**同行怎么做**：在 test 标签不可得时（MAVEN-ERE 的 CodaLab 提交通道**已关闭**，已核），
同协议重跑并声明口径是通行做法；**MAQInstruct（2025）就用 valid 当 test**，我们已核过这个先例
（`ekg-maqinstruct-same-split`）。也就是说，(b) 状态在这个数据集上不是硬伤，是常态。

**推荐：选 ①。** Ch4 主表已有 official joint (a) + TacoERE (b) + A3 fallback + LLM 对照，
对手广度满足 QR-001 的**报告要求**；而 ② 换来的一个 (a) 标记，代价是动 final-valid 这条 A 类红线——
**这笔账不划算，且一旦开口，"只读一次"在后面几个月里守不住。**

#### 已自审完毕、不再挂起的两点

（理由见 `results/PHASE_A.md`）契约字面写"实现 evidence selector"而这里是按 span 定义的证据集
（冻结因果链未动）；一致性项只跑 causal 族（causal FP 占 causal 误差 83.6%，
temporal 每篇 573 个正例、subevent 每篇 5.3 个，功效不足）。

**另外两点已自审完毕、不再挂起**（理由见 `results/PHASE_A.md`）：契约字面写「实现 evidence
selector」而这里是按 span 定义的证据集（冻结因果链未动）；一致性项只跑 causal 族
（causal FP 占 causal 误差 83.6%，temporal 每篇 573 个正例、subevent 每篇 5.3 个功效不足）。

#### ~~A4.1 下次开工需要的两样东西~~ → ✅ **A4.1 已 PASS（2026-09-13）**

**这一节的前提是错的，连同它导致的两天阻塞一起记录在案。** `prepare_a4_pair_evidence_preflight.py`
**没有任何 torch / cuda 引用**——`--model` 只传给 `model_content_digest()`（对目录内每个文件 sha256
后再 digest），**从不加载模型**。整个脚本＝哈希校验 + 用官方 `evaluate.py` 重算两条 baseline，
**是 CPU 任务，不是 GPU 任务**。而 4090 被占的是 **GPU**，不是文件系统：ssh 全程正常，
CPU 64 核 load 12.9、内存 439 GB 可用。「GPU 被占」被当成了「文件拿不到」。

实际执行：4090 `git reset --hard origin/main` → `1761d47`，11 项输入里 10 项原地 sha256 匹配，
唯一缺件 A3 handoff bundle `a3-v6-20260905-r17/`（9.8 MB）从本地 `scp -r` 过去、双端核对一致，
然后纯 CPU 跑完 → **PASS**。protocol `321309ac…d65451`，`code_files=7`，
候选 digest `15a3b1a5…dac10910`（291 篇 / 7,195 mentions / 234,870 对）。
完整记录、两条 baseline 的重算数字、以及「A4 没有 D4 式 head 退化风险」的逐行核查见
[`results/PHASE_A.md`](results/PHASE_A.md) 末节。

**带走的纪律**：阻塞理由要逐条验证到代码，不能靠转述。判断一项任务是不是 GPU 任务，
只问一句——**它自己 import torch 吗？** 已写进 `EXPERIMENT_PLAN.md` §4.1。

以下是原文，保留作记录：

~~preflight 脚本已写好并在本地验到能验的部分，`prepare_a4_pair_evidence_preflight.py` 的必填参数里
只有两项本地闭合不了，都在 gpu-4090：~~

1. `--model`：契约钉的内容寻址 encoder 目录（`71be7419…c961ea9`）。5090 上的公开 backbone 是
   `2c7ff1f1…49736`，**digest 不同，脚本会 fail-fast，这是对的**——两条线的数字不混表；
2. `--fallback-predictions` / `--taco-predictions`：A3 fallback（`rates_coref_family_selection`）与
   taco 适配 `taco-s13-r3` 的**官方形状预测文件**。preflight 会用冻结的
   `score_maven_ere_official.py` 重算它们的三族 P/R/F1（契约 A4.1 要求「独立重算」）。
   路径要在 4090 的 `runs/stages/A3/a3-v6-recipe-accounting-r16/` 与 R1 的 taco namespace 下确认，
   **别拿本地 `a3-v6-20260905-r17/predictions.jsonl` 当 fallback 预测顶替**，那是 handoff bundle 的
   prediction 文件，先核对它的口径再决定能不能用。

开发冒烟产物在 `gpu-5090:/mnt/aidata/tongjiakai/ekg/runs/stages/A4/dev-smoke-20260912/`，
`smoke.json` `0b92a24fbbf156dd5ac277efad20c14026e7b628a0eb68faa2f4a9db337640de`；
**它不是 A4.2**（无 preflight 绑定、非冻结 backbone、非官方评测器），A4.2 要带 `--contract` 重跑。
四臂读数与三个被抓到的缺陷见 `results/PHASE_A.md`；**表里没有可引用的数字**。


</details>

<details><summary><b>附录 C · 2026-09-11 ~ 09-14 各轮做了什么（原 §0.7a / §0.7）</b></summary>

### （历史）0.7a 2026-09-14 这一轮做了什么

| 做了什么 | 结果 | commit |
|---|---|---|
| **A4 四臂 dry-run 收尾** | pipeline PASS；按契约 Bundle 清单核出**两个缺件**（checkpoint hashes、`fallback_component_bundle_id`——后者四份契约都点名却**从未实现**），均已补 | `d595439` |
| **口径陷阱入账** | 顶层 `candidate_pairs` 348,632 **≠** 候选全集 234,870（前者含 TIMEX 对）。写表引 `mediator["pairs"]` | `d595439` |
| **recall 塌陷追因** | 推翻第一版归因：**不在推理修正，在训练侧**（base 判正 4,355→766，推理只砍 24.7%） | `8bddb73` |
| **梯度修正 → 失败** | 训练发散（5.49→2214，17 epoch 中止），⇒ 被摘的梯度**同时是阻尼**；已回滚并把测量写进代码注释与新测试 | `2b8bbdf` → `24b3924` |
| **smoke 报错信息** | 「证据流一行都没改」读起来像机制失效，实为 base 没判出正类；改文案并写明**不得放宽成 pass** | `5b3fcb8` |
| **SimKGC 搬到 5090** | 双端 sha256 一致、commit 已复核、预处理 PASS（test n=3,134 与结果页此前计数吻合）、AdamW 透明补丁记 hash | `f88cc76` |
| **SimKGC 训练受阻** | **算力**：要 4×32 GB。顺带发现第一刀的成本排序漏算显存，建议改序 CSProm-KG | `c18fa8f` |
| — | ⚠️ **两台服务器都没有外网**（实测），已提升到 §0.6 环境既成事实 | `5b3fcb8` |

**这一轮最该带走的三条纪律：**

1. **两个计数并排放才看得出归因错没错。** 只看 `causal F1` 会把塌陷归给推理修正；
   把 `revised_rows` 与 `predicted_causal` 并排，病灶立刻换了位置。
2. **一个"退化解"可能同时是稳定机制。** 摘掉它之前先问：**是什么在平衡它？**
   这次没问，代价是 2.5 小时 GPU 和一次回滚。
3. **核依赖不能只看下限。** `transformers>=4.15` 没有上限，但 4.53 删掉了它用的 `AdamW`——
   **第三堵版本墙，是依赖太新而不是太旧。**

### （历史）0.7 2026-09-11~13 这三轮做了什么

| 主表 ID | 结果 |
|---|---|
| **C-1** D4.1 preflight | ✅ PASS。执行中修掉三个「本地绿灯、服务器上跑不起来」的缺陷：脚本自造目录摘要去比 P1 的内容地址（唯一的测试是拿算法和它自己对）、`acceptance.json` 的裁决键是 `acceptance` 不是 `status`、`oof_summary.json` 记的是仓库相对路径。三条都进了 `ENGINEERING_NOTES.md` |
| **C-2** EasyECR 核查 | ✅ 静态裁决 `conditionally_runnable`，仓库 `hqyang/EasyECR @ f6cd779f`（URL 此前项目里从没记过）。6 条阻断点名可数；allennlp 矛盾由求解器机器复现。KBP 2017 需 LDC 许可 → **FR-016 (b)**。**剩 C-2b**：活体 venv + import 冒烟 |
| **C-5** C5.0 核心件 | ✅ `src/ekg/nodes/role_uncertainty.py` + `role_compatibility` 组件，15 条测试（`fc25777`） |
| **C-9** D4 pilot 入口 | ✅ 新写 `scripts/run_d4_typed_cue_oof.py` 并纳入 preflight 哈希集合（`a90df4e`） |
| **G-0** 4090 驱动 | ✅ 已修（580.178.04）。**但四张卡现被他人占用** |
| **G-1** D4.2 smoke | ✅ CPU + CUDA 双半边，三臂产物**逐字节相同** |
| **G-2** D4.3 pilot | ❌ **失败**，见本文 §▶ 表与 `results/PHASE_D.md` |
| — | 5090 上用**全公开源** backbone（`2c7ff1f1…49736`）独立重建了 D4 的两条 anchor：CLS `.543514` / DMRoBERTa `.536622`，同一排序、绝对值低约 .010 → **可复现地板 ±.01** |
| **C-6** A4.0 实现 | ✅ `790c35a`。`pair_evidence.py` + `pair_evidence` 头（零初始化证据残差，四臂同参数） |
| **C-6b** A4 入口脚本 | ✅ `65cf64b` → `323fd7a`。五个入口齐全，pilot 入口已进 preflight 的 `CODE_FILES`（7 个文件）；5090 四臂开发冒烟 pass |
| — | **A4 设计按证据自审改了一轮**（`f90c8cd`）：连接词选择器被本项目自己的测量否掉，改为 interior 定义式 |
| — | **冒烟连抓三个真缺陷**（`0615596` / `3019dd3` / `323fd7a`）：nan 损失照样 PASS、训练 cap 用在推理上、修正头把 causal 正类抹光 |
| — | **DREEAM 静态核查 `not_runnable`**（`b52d506`）：两条证据监督路径都要人工标注，且无 distant 语料；一手数字显示其证据机制在我们这格只值 +0.33 F1 |
| — | ⚠️ **发现 P1 r15 的 `--validate-only` 从 2026-09-05 起一直失败**（`d8fcd30` 改了被 r15 钉住的 trainer）。记录的数字不受影响，但「三方一致」这句今天不成立；**不要为了变绿去改 r15** |

**D4 的两条 anchor 线并存，永不混表**：4090 线（`.553995` / `.545603`，backbone `71be7419…`，
有 preflight 与 acceptance）是主表用的；5090 线（`.543514` / `.536622`，backbone `2c7ff1f1…`）
是独立复现与备份。各自标明机器与 backbone 地址，**不相减**。


</details>

<details><summary><b>附录 D · 已完成的任务 A/B/C/D（P1 信任根、R1 准入闭环、A3.6 收口）</b></summary>

### 任务 A：本地重建 P1 trust root（已完成）

本轮已创建新 bundle，未覆盖旧目录：`runs/stages/P1/p1-v6-20260904-r15/`；其
`protocol.json` SHA-256 为 `1e31a9acef39261f776f7ed4069fd73f4531e8d12b55779bfc0fbd74c67f9655`。
外部重哈希、`--validate-only` 与 registry 三方一致，状态 `pass/pass`；精确记录见
[`results/PHASE_P1.md`](results/PHASE_P1.md)。历史 A3 结果仍引用 r12，不重绑。

本轮实际执行命令如下，保留作复现记录：

```bash
cd /home/tjk/myProjects/masterProjects/ekg
uv run python scripts/run_p1_local_gate.py
```

三件套均通过，`data/protocols/v6/local_gate.json` 无身份漂移；随后确认目标目录不存在：

```bash
test ! -e runs/stages/P1/p1-v6-20260904-r15
```

创建并内部验证新 bundle：

```bash
uv run python scripts/build_p1_bundle.py \
  --bundle runs/stages/P1/p1-v6-20260904-r15
```

最后独立查看并验证身份：

```bash
sha256sum runs/stages/P1/p1-v6-20260904-r15/protocol.json
uv run python scripts/build_p1_bundle.py \
  --bundle runs/stages/P1/p1-v6-20260904-r15 \
  --validate-only
python3 -c "import json; p=json.load(open('data/protocols/v6/registry.json')); print(p['p1_bundle_id']); print(p['p1_bundle_protocol_sha256']); print(p['global_protocol_status'], p['a3_entry_status'])"
```

验收：

- bundle ID、外部 `protocol.json` SHA-256、registry 三者一致；
- `global_protocol_status=pass`、`a3_entry_status=pass`；
- code hash 集同时包含 `src/ekg/core/protocol.py` 与 `scripts/train_supervised_relations.py`；
- 新 bundle 与 r12/r14 并存，旧结果身份不被覆盖；
- 新根及其 hash 写入 [`results/PHASE_P1.md`](results/PHASE_P1.md)，其他文档只引用。

本次未发生旧 remote smoke 或 hash 漂移失败，也未重跑 4090 smoke。

### 任务 B：R1 准入闭环（**已于 2026-09-11 收口**，见 `results/PHASE_R1.md` §21）

T012–T019 与 T022 已完成（T018 已在 A3 handoff 后补齐），精确数字、hash 和裁决见
[`results/PHASE_R1.md`](results/PHASE_R1.md)，产物根为 `runs/stages/R1/r1-v61-20260904/`，代码提交
`277b36f`。当前硬结论：ERE↔FACT 身份闭环；ERE↔ARG mention 仅约 95.4% 覆盖且共享 mention 有父簇
冲突，故 event-level arguments→mention 的 deployable 路线 blocked；Ch1 prospective power PASS，
argument-aware 同协议 runnable baseline 已由 `qwen3-argument-s13-r2` 闭合（§7），但它 MUC .803676
低于主锚 .809847，第二个不弱于主锚的方法族仍空缺；Ch2 prospective power PASS，但缺第二个独立同协议
runnable baseline；Ch3 的 291-document 设计 underpowered，但预冻结五折 OOF 已完成并验收，CLS anchor 与
2,913-document pooled power 均 PASS。精确数字与 acceptance hash 只见 [`results/PHASE_R1.md`](results/PHASE_R1.md)。

所在单位、学位类型、入学年份、学科与专业未知项均保持 `null`。**2026-09-07 纠正：原先冻结的同济校级来源
整体作废（作者不在同济）**，改按国内顶级 985（清北复交浙、中科大等）对标，已重新冻结学位法 + 清华 +
北大三份来源与 hash，`degree_requirements.json` 与 R1 `protocol.json` 均已重冻结，详见
[`results/PHASE_R1.md` §10](results/PHASE_R1.md)。行政线一律不得用来降低项目自定的更高科研硬门。文献矩阵已只读冻结 CorefPrompt、MAVEN-FACT、ModaFact、TextEE、OmniEvent
五个官方仓库 HEAD（E2 又冻结了第六个 LLMERE，记录在 `results/PHASE_R1.md` §4/§9，
`literature_matrix.json` 保持原哈希不动），但没有把不同数据/split/evaluator 的代码误记为同协议 baseline。Ch3 因果 brief 已
通过 T022 并绑定已验收 OOF/power；Ch2 brief 已由 E3 通过 T021 审查（**仅设计轴 PASS**，relation baseline
门仍 `blocked`）；Ch1 brief 已由 E4 通过 T020 审查（**仅设计轴 PASS**，第二方法族门仍 `blocked`，
等作者裁决）。**三份 brief 均未放行 proposed GPU 训练**。

两台服务器都没有可恢复的 OmniEvent/TextEE EAE checkpoint；OmniEvent 官方 checkpoint URL 已失效，
因此不得把随机初始化或跨 ontology 重训冒充官方 baseline。5090 的既有 Qwen 服务保持运行。

后续按 [`TASKS.md`](TASKS.md) 的 T020–T024 继续，但各章仍先补齐自身 blocker：

1. Ch3：T022 因果 brief 与 T023 跨产物审计均已通过；E6 可冻结 D4 phase contract，未冻结前不启动
   proposed GPU pilot；
2. Ch1：T020 brief 已 PASS；input/baseline blocker 已由 `qwen3-argument-s13-r2` 闭合，但按 §E.1b 的
   四条新措辞第二方法族仍空缺。**E10 已实测 ACCI 公开仓库全历史只有 README**，没有 trainer、模型、
   checkpoint、依赖或数据/评测接口，裁决 `not_runnable`；不得从论文重写后冒充透明移植，下一候选名单需作者
   按 §E.1b 另议。IP&M 2024 无公开代码、OmniEvent EAE checkpoint 失效、RESIJ 未取得；
3. Ch2：T021 brief 已 PASS；门已按 §E.1a 重新界定，第二个不同方法族由 **E8 的 LLMERE-causal**透明适配承担，保持完整候选全集；
4. 三份 brief 的 T020/T021/T022 审查与 T023 均已 PASS；下一步按 E6 冻结各自有充分输入的 T024
   phase contract。继续不看 final-valid、不写 proposed 训练代码。

上面四条是**依赖关系**，不是执行顺序；本周的实际执行顺序与判定标准以任务 E.2 的队列表为准。

产物进入 `runs/stages/R1/r1-v61-20260904/`，结构与完成门以
[`PHASE_R1_method_design_freeze.md`](phases/PHASE_R1_method_design_freeze.md) 为准。R1 准备可以部分完成，
但不能在 baseline/input closure 和跨产物一致性审计前标 PASS。

### 任务 C/D：A3.6 执行、评分与失败交接（已完成）

四臂于 2026-09-04 18:03 使用 GPU0–3 的独立 `setsid nohup` 后台启动，整个训练不依赖 SSH 会话。
2026-09-05 成功 SSH 观察到四个 trainer GONE、GPU 已释放；四臂 train/score return code 均为 0。
本地只同步官方预测、评分、metadata 与小型 selection 文件，双端 SHA-256 一致；checkpoint 全部留在
`gpu-4090:/data/TJK/ekg/runs/stages/A3/a3-v6-recipe-accounting-r16/`。

同一 P1 r15、manifest、候选、evaluator、backbone、epoch 与 seed 13 下，逐臂只改变 rates、coref aux、
per-family selection。四臂均未越过 causal 主锚，A3 已按预注册规则 `failed`；精确数字只见
[`results/PHASE_A.md`](results/PHASE_A.md)。交接 bundle：`runs/stages/A3/a3-v6-20260905-r17/`，protocol
SHA-256 `c187bf03978674edd29ac209658ccb62d457b744a209e864a0fef0e9eee9359e`。

不得新增 seed 17/42，不得把官方配方收益记成方法贡献。R1 只把 causal 最强臂当 prospective-power 与
下一新家族的 fallback 对照。


</details>

<details><summary><b>附录 E · 历史队列 E.1 / E.2 / E.2a / E.2b（已被 EXPERIMENT_PLAN 主表取代）</b></summary>

#### E.1 联网核实结论（2026-09-07，影响下面的排期）

- **Ch2 的第二 baseline 有官方实现，我们此前漏收了**：LLMERE（COLING 2025，
  [aclanthology.org/2025.coling-main.500](https://aclanthology.org/2025.coling-main.500/)）已开源，
  仓库 [github.com/HerbertHu/LLMERE](https://github.com/HerbertHu/LLMERE)，`main` HEAD
  `94d4ef2781ec7e071d38ac7fd8632a8fffbda798`，目录含 MAVEN-ERE / MATRES / HiEve。按"不重复造轮子"，
  **官方实现优先于我们自建的 TacoERE 适配**；`results/PHASE_R1.md` 第 4 节"未取得官方实现"的
  Ch2 结论需要按实测修订。TacoERE 仍无公开代码，本地适配档只能标注为**透明适配**，不得写成官方复现。
- **C5 的一般命题已被抢占**：ACCI（[arXiv 2506.01488](https://arxiv.org/abs/2506.01488)，
  Sci Rep 2026）已占"argument-centric + 结构因果图 + 后门调整 + counterfactual 模块"的事件共指命题，
  ECB+ 88.4 / GVC 85.2 CoNLL F1。它是**跨文档、ECB+/GVC**，我们是**文档内 MAVEN-ERE + 预测
  mention-local 论元 + 缺失感知不确定性门控（不用 gold 论元）**。T020 必须正面处理这条抢占，
  写清窄 delta，并核实 ACCI 用的是 gold 还是预测论元；不能再写"首次"。
- **A4 的一般命题同样被占，但组合仍有窄 delta**：CovEReD
  （[2024.findings-emnlp.672](https://aclanthology.org/2024.findings-emnlp.672/)）已做文档级关系抽取的
  counterfactual 一致性，SURE-RAG（[arXiv 2605.03534](https://arxiv.org/html/2605.03534v1)）已做
  evidence sufficiency + 不确定性弃答。T021 必须把两者写进 related work。
- **D4 暂无直接后续工作**：未检索到 MAVEN-FACT 上 typed cues / modality×polarity 因子化的跟进论文，
  这条赛道当前最干净。结合"Ch3 三个 blocker 全清、pooled power PASS、T022 已过"，
  **D4 是三章里最该先放行 pilot 的一章**。

#### E.2 历史队列（9/7 – 9/10；已完成行留作可追溯记录）

| 序 | 任务 | 前置 | 完成判定 | 状态 | commit |
|---|---|---|---|---|---|
| E1 | 关 Ch2 TacoERE 适配档的账：查清 `taco-s13-r2` 与 `taco-s13-r3` 差异来源 → **预注册**选档规则 → 评分正式档 → 三族官方 F1 写进 `results/PHASE_R1.md` → 更新 `status.json` | 已满足 | 差异有书面解释；选档规则在看分数前写定；结果页与 `status.json` 不再互相矛盾 | done | `91e818e` + `bc6b07e` |
| E2 | 取 LLMERE 官方实现做可运行性核查：冻结 commit/tree hash、核对 MAVEN-ERE 数据接口、base model、显存与是否 LoRA，裁决"能否在我们 2622/291 manifest 与官方 evaluator 下忠实重跑"；**本步不训练** | E1 | 裁决落到 `results/PHASE_R1.md` 第 4 节，并修订该节 Ch2 结论；能跑则排下周训练，不能跑则写明具体阻断点 | done | `8a8ac1a` |
| E3 | T021 Ch2 因果 design brief：写入 LLMERE/TacoERE 对照结构与 CovEReD、SURE-RAG 的一般命题，明确 A4 窄 delta | E2 | 审查 PASS，且推理保持完整候选全集 | done | `d584ca8` |
| E4 | T020 Ch1 因果 design brief：正面处理 ACCI 抢占，核实其论元来源，写清 C5 的窄 delta | 已满足 | 审查 PASS；不使用 MAVEN-ARG cluster gold；不出现"首次"表述 | done | `0210fba` |
| E5 | T023 跨产物一致性审计：实跑 `scripts/audit_r1_consistency.py`，修掉 `status.json` 与结果页的矛盾。**已有两条确凿输入证据**：`design_briefs.json` 与 `literature_matrix.json` 在 2026-09-06 15:27 被改动却没同步 `protocol.json`，哈希已漂移，且 matrix 把 relation/identity 门写成 `pass`（与自身 `global_decision`、`status.json`、结果页、E1 预注册判断四处矛盾），briefs 把三份 brief 全标 `accepted`。**必须先查明 09-06 改动来源，不得先改哈希让审计变绿**；漂移字节已由 E3 存档在 `runs/stages/R1/r1-v61-20260904/audit/design_briefs.drift-20260906T1527.json`，`briefs.relation` 已被 E3 的正式 T021 审查取代、`briefs.identity` 仍是 09-06 原样；详见 `results/PHASE_R1.md` §11 与 §11.1 | E3 + E4 + 已有 T022 | 输出 `cross_artifact_audit.json`；每条需求映射到任务/测试；两条漂移各有裁决 | done | `54a10cf` |
| E9 **（排在 E6 之前）** | 核实 IP&M 2024（Zhang et al., IP&M 61(5) 103811）的口径：取全文对照表，看**它复现的 MAVEN-ERE official joint baseline** 与我们自跑官方码是否对齐（MAQInstruct 判据）。订阅墙走作者主页 / ResearchGate / 机构库 / OpenAlex（作者 Junchi Zhang，dblp `153/2859`） | 已满足 | 三种处置之一落到 `results/PHASE_R1.md` §15.3；**无论结果都不进 roster**；若判定可比则 A4 及格线在 E6 前重估 | done | `03d972a` |
| E10 **（排在 E6 之前）** | ACCI 仓库静态核查（`github.com/era211/ACCI`），**复用 E2 对 LLMERE 的流程，不训练**：有无 trainer / checkpoint / 依赖清单，数据接口能否接我们 2622/291 manifest 与完整候选全集，跨文档→文档内需要哪些适配 | E9 | 裁决落到结果页；能跑则排单卡 seed-13 透明移植，不能跑则写明具体阻断点并按新措辞另议 Ch1 名单 | done | `9b43573` |
| E6 | T024 冻结 C5/A4/D4 phase contract。**A4 契约照常冻结**：roster 里 LLMERE-causal 已被完整指名与规格化，只有数字 pending；pilot 可先跑，确认性 promotion 不可 | E5 + E9 + E10 | 三份契约的输入、baseline、protocol hash、promotion/stop、bundle、GPU 命令齐全并落 hash；A4 的 pending baseline 有可执行规格而不是占位符；**A4 契约已由 E9 解锁、可冻结；C5 因 E10 `not_runnable` 仍缺第二方法族，先由作者另议名单，不得伪冻结**。⚠️ **E5 已查出契约内容本身与裁决矛盾**：A4 契约仍把 taco 适配写成 independent recent family（§13 已否）、C5 契约仍把 Qwen3 档写成 argument-aware strong baseline（§15 已改为负面对照），**必须改内容，不能只补哈希**；D4 契约与 T022 记录一致 | done | `1fcc7db` |
| E7 | 修可追溯性缺口：把 `src/ekg/relations/extractor/supervised.py` 纳入 relation run 的哈希集合（E1 发现：两档携带同一 trainer hash 却构造不同编码器输入）；**并把 `scripts/audit_r1_consistency.py` 纳入 R1 `protocol.json` 的 `code.files`**（E5 发现：同类脚本 `audit_r1_dataset_ids.py` 在集合内，它却不在，导致 T023 审计无法从冻结代码集复现） | E6 | 新增 hash 键不改动任何既有 hash；若动到 trainer 本身则须同时重建 P1 bundle 并重绑 | done | `1c922fd` |
| E8 **（可与 E4–E7 并行）** | LLMERE-causal 透明适配 baseline（`llmere-causal-s13`）：清 B1/B3/B4 → 用未设门镜像取权重并记 SHA-256 → converter **逐字不改**生成 causal 数据 → LoRA SFT → 用**我们冻结的 `evaluate.py`** 打分 → 数字写进 `results/PHASE_R1.md`。**先只跑 causal**（48,365 训练 / 11,149 推理，约 joint 的 1/4）；启动前按 §5 展示命令、cwd 与预期产物 | 已满足（裁决见 §E.1a） | 官方评测器下的 causal P/R/F1 落地；标注**透明适配**、披露 k=30 分区天花板与权重替换；relation 门按 §13 的新措辞判定 | wip（SFT 与 11,149 条 generation 已完成；`372a6e2` 解决 1 条精确重复引用，但全量扫描另有 95 条 malformed 输出，故官方评分不可运行。不得填 NONE、猜引用、只重生成 95 条或拼接；先完成 §E.2a 的恢复方案审查，获得作者明确授权后才能重生成） | `20be231` + `372a6e2` |
| E11 **（2026-09-09 作者授权与 E8 generation 并行）** | D4 typed-cue factuality 的 D4.0 implementation/local gate → D4.1 immutable preflight/baseline replay → D4.2 CPU/CUDA smoke。只在三道门全过且重新核卡后，按冻结 seed-13 命令启动 D4.3；GPU 选择按实时空闲卡，记录实际 `CUDA_VISIBLE_DEVICES`。 | E6/T024 frozen；作者明确授权 D4.0–D4.2 | 实现与 targeted tests、三件套、preflight 的 source/manifest/fold/OOF hash 重验和 smoke 均通过；不读取 final-valid、不改五折 rotation、不启动 seed 17/42。任何一项失败即停止，不占卡重试。 | wip（D4.0 `727ab02` + `310b5be`：factorization、typed-cue sidecar、文档内 permutation、confusion mediator、独立 train/eval/preflight/smoke 入口及 preflight 合同测试已完成；**534 passed / 26 expected skips、ruff 0、smoke OK**。D4.1 未启动；4090 隧道后来恢复，但作者要求先停下准备汇报，故无 preflight/smoke/pilot 产物） | `727ab02` + `310b5be` |

#### E.2a 上一批接续队列（2026-09-10 冻结；已被 §E.2b 取代，留作记录）

| 顺序 | 子任务 | 可否立即执行 | 通过 / 停止条件 |
|---|---|---|---|
| 1 | **E8.1：审查并冻结全量恢复方案**。只读现有 generation、prompt/预测格式、LLMERE 上游能力与当前 converter；提出覆盖全部 11,149 条的统一生成/约束解码和重新评分方案。 | 可以；不使用 GPU、不写 E8 运行产物。 | 通过：完整候选全集、同一规则、原始输出保留、fail-fast 和成本均明确；停止：方案需猜补关系、局部重生成或不能保持同一口径，则将本轮标为不可评分失败。**方案通过不等于获准重生成。** |
| 2 | **E11.1：D4 immutable preflight**。在 4090 以 `.venv/bin/python` 物化 `runs/stages/D4/d4-v61-typed-cues-r1/preflight/`，重验 R1/P1、五折 manifests、source、encoder、accepted OOF baseline 和 code hash。 | 可以；此前作者已授权 D4.0–D4.2；不使用 GPU、不读 final-valid。 | 通过：protocol `status=pass`，独立重算两条 accepted OOF baseline，所有 hash/覆盖/折隔离一致；停止：任何 hash、fold 或 final-valid ledger 不一致，不创建 smoke 或 pilot。 |
| 3 | **E11.2：D4 CPU/CUDA smoke**。仅在 E11.1 PASS 后，重新核卡并先向作者展示准确命令、cwd 与预期产物；在单张真正空闲的 4090 上跑 1 fold、10 个 train-only documents 的 full/remove-core/permutation 三臂。 | 依赖顺序 2；GPU 短任务，须重新核卡。 | 通过：三臂 loss/logits/spans 有限，sidecar/report 完整，evaluation IDs 未入 train/selection；停止：任一检查失败即不启动 pilot。 |
| 4 | **D4.3 seed-13 five-fold pilot**。 | **不可立即执行**；依赖顺序 3 PASS，且需作者在看到 preflight/smoke 结果后再次明确授权长 GPU 任务。 | 只有 author approval 后，按冻结命令、单 seed 13、五折三臂启动；不追加 seed 17/42。 |
| 5 | ~~**C5 第二方法族前置**~~ **（已被 E12 取代，2026-09-11）**：QR-001 v1.1.0 后 baseline 广度不再是准入门，C5 已转 `frozen`，可实现、preflight、smoke 与 pilot。 | ~~仅可做「补前置」~~ | ~~未收到名单时保持 `blocked_pre_admission`~~ |

#### E.2b 当前队列（2026-09-11 冻结，取代 E.2a）

> **本队列已降为 [`EXPERIMENT_PLAN.md`](EXPERIMENT_PLAN.md) 主表的当周切片。**
> 可执行实验只认那份主表；**本表不得出现主表以外的新任务**。要偏离顺序先改主表。

**排序原则**：先跑自己的方法，再补外部对手。E1–E11 十一个任务全部是协议、审计、文献与
baseline，v6.1 三份方法设计**一个都没跑过**；证明方法有没有价值才是实验质量的主要判据，统计门槛是
锦上添花（作者 2026-09-11）。

| 主表 ID | 子任务 | 可否立即执行 |
|---|---|---|
| — | **E12：SPEC v1.1.0 + FR-016 + 三契约重绑** | ✅ **已完成**（`results/PHASE_R1.md` §21） |
| — | **E13：E3 重定向为「事件图谱构建与下游事件预测应用」**（乙形态，作者 2026-09-11 选定）；24 条件 factorial / Holm / frozen-vs-finetuned 全部撤销 | ✅ **已完成**（`phases/PHASE_E3_graph_application.md`） |
| — | **E14：冻结 `EXPERIMENT_PLAN.md` 防漂移主表** | ✅ **已完成** |
| **C-1** | D4.1 immutable preflight | ✅ **done 2026-09-11**（`93f59f1`，见 `results/PHASE_D.md`） |
| **C-2** | EasyECR 可运行性实跑核查（不训练） | ⚠️ **静态部分 done 2026-09-11**（`conditionally_runnable`）；**C-2b 活体 import** 待 4090 隧道恢复 |
| **C-3** | E8.1 LLMERE 恢复方案冻结 | ✅ 纯文档 + 只读 |
| **C-4** | Ch6 对手名册调研与冻结 | ✅ 联网调研 |
| **C-5** | C5.0 实现 + 本地 gate | ⚠️ **核心件 done 2026-09-11**（`role_uncertainty.py` + `role_compatibility` 组件，15 测试，550 passed）；**C-5b 四个入口脚本**待做 |
| **C-6** | A4.0 实现 + 本地 gate | ⚠️ **核心件 done 2026-09-12**（`790c35a`）；**剩 C-6b** 入口脚本 |
| **C-7** | LLM 对照脚手架 | ✅ CPU |
| **C-8** | 第 2 章统一评测协议素材整理 | ✅ CPU |
| — | **E15：E3 重定向为「乙」形态 + 撤销 factorial** | ✅ **已完成** |
| — | **E16：`EXPERIMENT_PLAN.md` 时间线按项目自身基准率重估**（初版 3 周收口是错的，把 GPU 计算耗时当成了日历时间） | ✅ **已完成** |
| **G-0** | 修复 gpu-4090 驱动 | ✅ **done 2026-09-12** |
| **G-1** | D4.2 smoke | ✅ **done 2026-09-12**（CPU + CUDA 双半边，产物逐字节相同） |
| **C-9** | **写 `scripts/run_d4_typed_cue_oof.py`**（契约点名、仓库里没有） | ✅ CPU，**当前队首** |
| **G-2** | **D4.3 seed-13 五折 pilot** | ❌ 等 **C-9** + 作者授权长任务；4090 四卡可按折并行 |

完整主表（含 G-3…G-12、三个 Gate、GPU 预算与 phase 契约映射）见
[`EXPERIMENT_PLAN.md`](EXPERIMENT_PLAN.md)。

⚠️ **E12 改动了 `runs/` 下的三个 JSON，而 `runs/` 是 gitignored**（产物走 scp）。开工前必须把
`runs/stages/R1/r1-v61-20260904/protocol.json`、`phase_contracts/t024_freeze.json`、
`audit/cross_artifact_audit.json` **双端 SHA-256 同步到 gpu-4090**，否则远端 preflight 会因
契约 hash 不符而 fail-fast。本地值见 `results/PHASE_R1.md` §21.3。

**GPU 恢复后的队首是 D4.3**，不是 preflight 排队——它是唯一实现完成、power 过关、赛道无竞争的一章。
两卡可并行时：卡 A 跑 D4.3，卡 B 跑 A4.3 或 EasyECR 复现（namespace 不重叠）。

**仍打开的裁决**：LLMERE 的 FR-016 保真度路径与 §E.1a 第 6 条冲突，见 `results/PHASE_R1.md` §21.6
与名册 §2.1，建议记 (b) Unverifiable。

#### E.2a 的历史说明

E1 已完成（2026-09-07）：差异来源是 `3f02640` 换掉了 TacoERE 的 KMeans 初始化，全量实测 2,913 篇里
2,743 篇聚类归属改变，**是确定性的代码致输入变化，不是 GPU 非确定性**；旧初始化器还在同进程内对 5 篇
自相矛盾。选档规则在 `taco-s13-r3` 评分**之前**以提交 `91e818e` 预注册（按训练代码身份选，不看分数），
选中 `taco-s13-r3`，其官方三族 F1 为 causal 32.01 / subevent 28.80 / temporal 51.48，causal 未过主锚
33.17。taco 是**透明适配**，不关闭"第二个独立同协议 runnable baseline"门。全部证据见
[`results/PHASE_R1.md` §8](results/PHASE_R1.md)。

E2 已完成（2026-09-07，静态核查，未训练）：LLMERE 冻结在 commit `94d4ef27…a798` / tree `f0fd6928…a06f`，
LICENSE MIT。**E.1 里"官方实现优先于自建 TacoERE 适配"这条判断需要按实测收窄**：该仓库全历史 5 个
commit 只有数据构造、评测器与已发布预测，**没有训练/推理代码、配置、依赖清单、checkpoint，也没有出现
过任何 base model 名称**；训练细节只在论文里（LLaMA-Factory + LoRA r64 + lr 2e-4 + 3 epoch + len 2048 +
单张 A100-40G）。裁决 `conditionally_runnable`：能跑，但跑出来的是**我们对官方方法代码的透明适配**，
和 TacoERE 同类，**不关闭**"第二个独立官方同协议 runnable baseline"门；relation 门维持 `blocked`。
数据接口已实测兼容——用我们 2622/291 manifest 替掉上游的 8:2 随机切分后，四个 converter 与 `merge.py`
**逐字不改**跑通，得到 199,757 条 joint 训练样本与 internal-dev 上 49,156 次推理。四条待清阻断点
（无官方 trainer / Llama-3-8B 权重 gated 且无可用 token / `llamafactory` 未装且不得污染 cu128 `.venv` /
上游评测器不是组织方 `evaluate.py`）与成本估计见 [`results/PHASE_R1.md` §9](results/PHASE_R1.md)。
⚠️ 其发布的 causal 36.04 落在官方 valid 710 篇 + 自写评测器上，**与我们 internal-dev 291 篇的主锚 33.17
差两条轴，不得同表比较**。

E3 已完成（2026-09-07，纯文档与静态核查，未训练、未用 GPU）：T021 关系因果 brief 写入
`design_briefs.json` 的 `briefs.relation`，冻结链是 **逐对反事实证据充分性+必要性 → 跨句 causal 误报数
（注册中介）→ 官方 causal micro-F1**；三臂为 full / remove-core（关掉证据选择与两次反事实前向）/
`taco-s13-r3` cluster-context，负控是**等长非证据句替换**且必须抹掉中介改善。护栏含**完整候选全集不得被
弃答或检索裁剪**与 causal recall 不得低于主锚自身的 32.05。四条已被占的一般命题（TacoERE 上下文重构 ·
LLMERE 生成式范式 · CovEReD 反事实数据集 · SURE-RAG 选择性弃答）逐条写进 brief，窄 delta 定义为它们的
**交集**而非任一部件，**不写「首次」**。审查结论 **PASS（仅设计轴）**。
⚠️ **留给作者的决定**：QR-001 要求"主锚 + 另一个强的不同方法族"，而 `taco-s13-r3`（32.01）**低于主锚
33.17** 且是我们自己的透明适配，赢它由赢主锚蕴含。T024 冻结 A4 契约前必须二选一——(a) 接受"主锚 + 透明
适配"并在每张表披露 fidelity 缺口，或 (b) 清掉 LLMERE 的 B1–B4 后排训练（4090 整机数天 + 一个 Meta 许可
决定）。在决定前 relation baseline 门维持 `blocked`。
📎 **取证**：E3 写 `design_briefs.json` 前先把 09-06 的漂移字节原样存档为
`runs/stages/R1/r1-v61-20260904/audit/design_briefs.drift-20260906T1527.json`（`d5d6a61c…7986`，mtime 保留），
只重写 `briefs.relation` 一个子树，`protocol.json` **未**重冻结——E5 的漂移裁决不受影响。
全部证据见 [`results/PHASE_R1.md` §11.1/§12](results/PHASE_R1.md)。

E4 已完成（2026-09-07，纯文档与静态核查，未训练、未用 GPU）：T020 身份因果 brief 写入
`design_briefs.json` 的 `briefs.identity`（`81ad43a3…a382` → `cd40e664…4366`；兄弟子树与顶层字段逐字节未动，
`protocol.json` 仍未重冻结）。冻结链是 **mention-local 预测角色后验 + 显式缺失状态 → 高相似度误合并数
（注册中介）→ 官方 MUC F1**；三臂为 full / remove-core（detach 角色残差）/ `qwen3-argument-s13-r2`，
负控是**类型内角色后验置换**且必须抹掉中介改善。护栏含 **MUC recall 不得低于主锚自身 83.246073**、
B³ ≥ 97.04 / CEAF-e ≥ 96.73 / BLANC ≥ 88.88、四态抽取状态无静默默认、gold 论元与 gold identity 只作
标注过的 oracle、`EventNode` 零新增字段。
**ACCI 的论元来源已按要求核实（一手全文）**：它**根本不抽论元**——用 masking 把输入切成 trigger 子序列与
其补集 `X_arg = X \ X_trg`，没有角色类型、没有逐角色后验、也没有缺失状态；且是跨文档 ECB+/GVC、
候选对在 subtopic 内检索。所以答案既不是 gold 也不是 predicted，这一条必须写进论文的对照叙述。
另检出一条**更贴近的抢占**：IP&M 2024 `A graph propagation model with rich event structures`（Zhang et al.,
61(5) 103811）用 AMR 跨句隐式论元做 MAVEN-ERE 联合抽取，报 **MUC 86.1 / causal 37.4**，
但**无公开代码且 split/评测器未核实**，只作 context、**不得同表比较**；它对 Ch2 同样有影响，已登记为 E5 的待办。
四条已被占的一般命题（ACCI · IP&M 2024 · CorefPrompt · HGCN-ECR）逐条写进 brief，窄 delta 定义为它们的
**交集**，**不写「首次」**。审查结论 **PASS（仅设计轴）**。
⚠️ E4 留下的两个问题**已于同日由作者裁决**，见 [§E.1b](#e1b-作者裁决2026-09-07ch1-门同样重新界定ipm-口径核实前置到-e6-之前)
与 [`results/PHASE_R1.md` §15](results/PHASE_R1.md)：Ch1 门按四条新措辞重新界定、ACCI 移植改为
**先静态核查（E10）再谈训练**、`qwen3-argument-s13-r2` 重定义为注册负面对照、IP&M 口径核实（E9）
前置到 E6 之前。identity brief 的 roster / promotion / open_finding 已按裁决修订，
原文逐字保留在 `amendments[0]`（`cd40e664…4366` → `2220b86c…1999`），因果链、中介、三臂、负控、
护栏与 stop **未动**。全部证据见 [`results/PHASE_R1.md` §14/§15](results/PHASE_R1.md)。

E5 已完成（2026-09-07，纯文档与静态审计，未训练、未用 GPU）：`cross_artifact_audit.json` 已落地，
**审计 `pass`、`findings` 为 0**，SPEC 声明 35 条需求全部映射到任务与契约，六个 R1 产物身份全部 `frozen`，
三份 method phase 契约为 `pending_t024`（**预期状态**），P1 r15 与 A3 r17 信任根逐位一致。
**R1 仍未 PASS**——报告的 `r1_pass_blockers` 列出四条（status 非 pass + 三份契约待 T024）。
1. **先修了一个使 T023 无法在自己时点运行的循环依赖**：`audit_r1_consistency.py` 要求 `T023` 已打勾才继续，
   等于把这次审计写成它自己的前置，且第一个失败即 `raise`，永远产不出"列全问题"的报告。前置改为
   `TASKS.md` 实际声明的 **T012–T022**，findings 改为收集式，`pending_t024` 不再算不一致。
2. **09-06 漂移已溯源，证据是决定性的**：15:27 的改动属于 15:35 提交 `f6966a0` 的同一次会话，
   而该提交自己的正文只关闭 Ch1 的 **input/baseline blocker**、并明写 Ch2 仍缺第二 baseline。
   所以 identity 半是**把 blocker 关闭过度解读成审查通过**，relation 半**没有任何提交正文支持**且与同一提交矛盾；
   `literature_matrix.json` 的 `audit_date` 至今仍是 09-04，是"改了内容没重跑审计"的旁证。
3. **两条漂移走了不同的路**：`design_briefs.json` **原样重冻结**（磁盘字节已是 E3/E4 两次正式审查的产物，
   factuality 子树逐条比对 T022 记录一致）；`literature_matrix.json` **先把两个 `baseline_gate` 从 `pass`
   改回 `blocked` 再重冻结**，原值保留在其 `amendments[0]`，`methods` 与 `upstream_checkouts` 逐字节未动。
   `protocol.json` **最后**才重冻结（`fed98d2a…f619fc` → `497aae22…423155`）。**顺序就是要点：
   先溯源 → 再纠正内容 → 最后动哈希**，没有为让审计变绿而先改哈希。
4. ⚠️ **给 E6 的硬输入**：脚本不读契约内容，人工核对查出 **A4 与 C5 两份契约的 roster 与 §13/§15 裁决矛盾**，
   E6 必须改内容而不是只补哈希；D4 契约与 T022 记录一致。
5. 📌 **给 E7 的新缺口**：`scripts/audit_r1_consistency.py` 不在 `protocol.json` 的 `code.files` 里，
   而同类的 `audit_r1_dataset_ids.py` 在，本次审计因此无法从冻结代码集复现。本轮**不顺手修**，并入 E7。
全部证据见 [`results/PHASE_R1.md` §16](results/PHASE_R1.md)。

E9 已完成（2026-09-07，纯文献核实，未训练、未用 GPU）：**全文拿不到**——OpenAlex `oa_status = closed`
且无 repository 全文、Semantic Scholar `openAccessPdf = CLOSED`、无 preprint、12 篇引用文献（取回 10 条）
无一开放获取。预注册判据的原始形式（读它自己的对照表）**无法执行**，改用**等价路径**：
拿 MAVEN-ERE 官方论文（arXiv `2211.07342v1` Table 7/8，RoBERTa-base，5 次试验均值，官方 test）
与我们的主锚对照——**共指四指标全部在 ±0.4 内**（MUC 80.98 vs 82.1、B³ 98.04 vs 98.2、
CEAF-e 97.73 vs 97.9、BLANC 89.88 vs 90.2），causal 33.17 vs 31.5、subevent 29.75 vs 27.5 我们更高，
temporal 51.63 vs 56.0 低 4.4（方向与 `PHASE_A.md` 已记录的 TIMEX 头缺口一致，但**未做隔离实验，不作结论**）。
**结论：我们的官方 joint 复现忠实于官方发表口径。**
⚠️ **同时修正一处此前的推断**：§15.3 写「86.1 几乎必然含口径成分」是**不对的**——那里拿来比的 77.47 是
Phase A **我们自己的方法档**在 710 valid 上的分数，不是官方 joint 复现，混用它是错的。正确对照是官方
+joint 的 **82.1**，IP&M 高 **4.0**；causal +5.9、temporal +4.7、subevent +5.4，**四族齐涨 4–6 点**，
模式内部一致，**更像真实增益而非口径差**。未确证的仍有一环：它用 test 还是 valid、是否用组织方 `evaluate.py`。
✅ **对 E6 不阻塞，A4 契约可照常冻结**：它无公开代码 ⇒ 无法在冻结协议下运行 ⇒ 按 FR-006 进不了 roster；
A4 的及格线定义在**我们协议内的主锚与第二方法族**上，它改不了这条线；披露义务已由 §17 落地。
📌 它此前**根本不在** `literature_matrix.json` 里（与 E.1 的 LLMERE 漏收同类），已补两条 `no_public_code`
条目进 identity 与 relation 两章，**只追加不改既有条目**，随后按 E5 的顺序重冻结哈希。
全部证据见 [`results/PHASE_R1.md` §17](results/PHASE_R1.md)。

E10 已完成（2026-09-07，静态核查，未训练、未推理、未用 GPU）：ACCI 官方仓库冻结在 commit
`7f5bcd81…23fa` / tree `d4c8aa14…fe43`，全历史仅一个 commit、tree 仅一个 `README.md`，无 LICENSE、
release、trainer、推理入口、模型、checkpoint、配置、依赖、dataset reader、candidate builder 或 evaluator。
因此裁决 **`not_runnable`**：从论文散文重建会是我们新写的实现，不能叫官方复现或透明移植，故不排
single-card seed-13。冻结 MAVEN-ERE 输入的 2,622/291 manifest 全量 probe 验证 66,744/7,195 mention 可构造
`<m> trigger </m>` 输入、完整文档内候选对为 1,148,762/117,435；这只证明本地数据足供另写 adapter，
不构成对不存在上游接口的兼容。Ch1 第二方法族门保持 `blocked`，下一候选名单需作者按 §E.1b 四条措辞另议。
完整产物、hash 与裁决见 [`results/PHASE_R1.md` §18](results/PHASE_R1.md)。

E6 已完成（2026-09-07，T024 契约冻结，未实现、未训练、未推理、未用 GPU）：先改契约内容、再绑定 hash，
没有为使审计变绿而只补 hash。A4 的 `taco-s13-r3` 已降回固定透明适配对照，`llmere-causal-s13` 以
upstream / unmodified converter / causal-only 48,365 train + 11,149 internal-dev generations / LoRA 配方 /
frozen `evaluate.py` 完整规格化为 metrics-pending 的确认性 baseline；A4 seed-13 只在 A4.0–A4.2、local gate
与重新核卡后可跑，确认性 promotion 必须等待并超过 LLMERE（⚠️ **这一句已被 E12 取代，2026-09-11**：
确认性 promotion 不再以「等到 LLMERE 数字」为前置，见 `results/PHASE_R1.md` §21）。D4 与 T022 记录一致，冻结其 five-fold OOF
契约。C5 因 ACCI `not_runnable`、IP&M 无公开代码且无作者指定替代家族，记录为
`blocked_pre_admission`，**没有**将草案 hash 当作 phase contract binding；Qwen3 已改为注册负面对照，
非 roster 的 annealed-local-pair / hard-argument 臂已移除。R1 protocol SHA-256
`2fde1577c92d826d0ee12e722e6183b92421477ea38769e15144cdaa300c7094`，T024 artifact SHA-256
`3b44a2e2fdf402bfa55492d6527e642a7f75bb9301ad1c1e4098477ec7edd81b`；交叉审计 `pass`、0 findings、35/35
requirements mapped，A4/D4 `frozen`、C5 `blocked_pre_admission`。审计脚本现在明确区分该状态和
`pending_t024`，其自身 hash 仍由紧接的 E7 纳入冻结代码集。全部证据见
[`results/PHASE_R1.md` §19](results/PHASE_R1.md)。

E7 已完成（2026-09-07，可追溯性修复，未改 trainer、未重训、未评分、未用 GPU）：不把 r3 的源码身份
错误回填给 r2。`taco-s13-r2` 的 `supervised.py` 绑定训练提交 `d8fcd30` 的
`ffb40460…a1a25`，`taco-s13-r3` 绑定训练提交 `e796182` / 当前源码的 `9cdf54a…7ab7c`；两档只新增
`protocol_binding.hashes.supervised_extractor`，原 trainer `5c513bdb…d0f2c6`、checkpoint、预测和指标 hash
未动。对账 artifact `code_hash_reconciliation.json`（SHA-256 `833b3c4d…c5ebd`）已进入 R1 artifacts，审计会
重算两份 metadata digest 与该键。`audit_r1_consistency.py` 以 `f6fdc099…eef90` 加入 `code.files`，并自检其
自身 hash；后续脚本/metadata 漂移都会生成 finding。R1 protocol SHA-256
`199852a1f0b81e088f7568d9462d9fe226db15bdd21a78346b6d03bef80cf058`；审计 `pass`、0 findings、35/35
requirements mapped。P1 r15/A3 r17 不需重绑，R1 唯一余项仍是 C5 `blocked_pre_admission`。全部证据见
[`results/PHASE_R1.md` §20](results/PHASE_R1.md)。

E8 已于 2026-09-07 启动（仍在运行，**尚无指标或结论**）：首次任务 PID `1516155` 在独立
`.venv-llmere-causal-s13` 安装 CUDA PyTorch 时失败，日志是 `OSError: [Errno 28] No space left on device`。
只读诊断确认根分区 `/` 仅余 2.3GB（96%），而 `/data` 有 29TB 可用且 inode 充足；GPU0 当时仅驱动占用，
故这是 pip 默认 `/tmp` 临时目录的环境错误，不是 GPU、模型、数据或训练错误。未进入 LoRA SFT、未访问
final-valid、未产生预测/指标。修复提交 `b8b2352` 使 launcher 将 `TMPDIR` 与 `PIP_CACHE_DIR` 固定到
`/data/TJK/ekg/.tmp/llmere-causal-s13` 与 `/data/TJK/ekg/.cache/pip/llmere-causal-s13`，项目 `.venv` 未动。
在核实失败残留仅为 22MB 专用 venv 与 4KB 空 run root 后，删除这两个**确切的 E8 专用路径**，不触及数据、
既有 run 或 checkpoint；随后重新核卡、同步 `b8b2352` 并以 GPU0 PID `1518478` 重启唯一后台任务。命令的 cwd
是 `/data/TJK/ekg`，实际 launcher 是 `bash scripts/run_llmere_causal_adapter.sh /data/TJK/ekg 0`，其外层使用
`setsid nohup`、独立日志 `logs/llmere-causal-s13.log` 与 `PYTHONUNBUFFERED=1`。run root 是
`runs/stages/R1/r1-v61-20260904/baselines/relation/llmere-causal-s13/`；checkpoint/权重留在 4090，完成后只同步
generated/official predictions、metrics、metadata 和小型转换报告并做双端 SHA-256。重试启动后 PID ALIVE，
专用 tmp/cache 已写入 `/data` 且日志无 error；B3 仍在进行，不能把安装日志写成实验结果。任何完成、失败或
ssh 失败都按 §5 三态规则处理，并在本行和 `results/PHASE_R1.md` 如实回填。

重试 PID `1518478` 已成功安装 CUDA PyTorch（`.venv-llmere-causal-s13` 约 6.5GB，专用 pip cache 约 3.7GB），
但随后从 `https://github.com/hiyouga/LLaMA-Factory.git` 克隆固定 `v0.9.3` 时遇到
`GnuTLS recv error (-110): The TLS connection was non-properly terminated`，进程 GONE。该失败发生在模型下载、
converter、LoRA SFT 与评分之前，故没有实验产物。直接 HTTP/1.1 identity probe 在 30 秒内未完成；已验证
`https://gh-proxy.com/https://github.com/hiyouga/LLaMA-Factory.git` 的 `v0.9.3` tag 是预期
`ca75f1edf3cb50343ed1c98605141c3e22075b5f`。修复提交 `749d9b7` 使用此可访问源的**浅克隆**，仍 fail-fast
逐位检查该 commit；保留已验证的独立 CUDA 环境/cache，删除第二次失败的 run root 与 4KB tmp（无 model、
checkpoint 或结果），并在 final metadata 中新增 factory origin、commit、tree 与 dirty-state 记录。新任务 PID
`1534100` 已成功 clone 到该固定 detached commit，当前在独立 venv 安装 LLaMA-Factory，GPU0 仍无训练负载且
日志无 error。

PID `1540062` 随后完成固定 LLaMA-Factory 安装，并以 `https://hf-mirror.com` 下载
`NousResearch/Meta-Llama-3-8B@315b20096dc791d381d514deb5f8bd9c8d6d3061` 的全部 14 个文件（四个
`.safetensors` 分片合计约 15GB）。镜像底层 Xet 两个分片曾 read timeout，但 downloader 自动续传且最终
打印成功；这不是训练完成。接着 `prepare_llmere_causal_adapter.py` 因 4090 缺少
`runs/stages/R1/r1-v61-20260904/protocol.json` 而 fail-fast，进程 GONE；远端 P1 r15 协议仍为预期
`1e31a9ac…f9655`。因此尚未 clone LLMERE、运行 converter、进行 LoRA SFT、生成预测或计算指标，GPU0–3
均空闲。保留已验证的权重、专用环境、LLaMA-Factory 与 `base_model.json`，不重下也不删除。

恢复提交 `0c07ba5` 新增只接续该精确状态的脚本：它先验证上述已有目录、固定 LLaMA-Factory commit/洁净状态，
并拒绝覆盖任何 LLMERE checkout、train、predict 或 score 半成品；同时把 LLMERE 拉取改走已验证的
`gh-proxy` transport，但仍对 canonical URL 的固定 commit `94d4ef27…a798` 与 tree `f0fd6928…a06f` fail-fast
核对、并将二者写入 metadata。下一步仅同步本地已冻结的 8.7KB R1 protocol，双端 SHA-256 必须为
`199852a1f0b81e088f7568d9462d9fe226db15bdd21a78346b6d03bef80cf058`；通过后才以 GPU0 的后台续跑命令进入
converter 与单 seed-13 SFT。

该 R1 protocol 已于 2026-09-07 以 `scp` 传至 4090，双端 SHA-256 都是
`199852a1f0b81e088f7568d9462d9fe226db15bdd21a78346b6d03bef80cf058`；权重和 checkpoint 没有跨机移动。
续跑 PID `1566260` 先通过已有环境/权重/固定 LLaMA-Factory/无下游半成品的断点检查，随后经代理 clone
LLMERE 并核对到预期 `94d4ef27…a798`，split builder 生成 train/valid/test 为 2,622/291/291，未改动的
converter 已生成 48,365 train 行。它现在实际在 GPU0 运行单 seed-13 LoRA SFT（3 epoch、batch 1、累积 8、
18,138 steps，初始化时占约 16.5GiB）；GPU1–3 空闲。该记录只说明训练已开始，**不是指标、结果或门通过**；
训练完成后仍须生成 11,149 条 internal-dev 输出、严格转换、冻结 evaluator 评分和 metadata hash 才能回填结果页。

SFT 在 2026-09-08 13:37 成功走完 18,138/18,138 steps（3 epoch；`train_results.json` 的
`train_runtime=59233.9803`、`train_loss=0.25147225742685003`），最终 LoRA adapter
`train/adapter/adapter_model.safetensors` 为 671,149,168 bytes，final checkpoint 与 train metadata 均保留
在 4090。之后调用预测配置前，LLaMA-Factory 的依赖检查报
`PackageNotFoundError: ... jieba ... is required by this application`，进程 GONE；没有 `predict/` 或 `score/`
目录、生成预测或官方指标，因此 SFT 的训练 loss **不是**项目实验结果、不得写入结果页或作为门判断。

恢复提交 `b3615ee` 将缺失依赖固定为 `jieba==0.42.1`，并新增 prediction-only 续跑脚本。它验证 SFT 已完整
结束、adapter/metadata 均非空、LLMERE converter 的当前 SHA-256 仍等于准备时记录值、factory 与 upstream 的
固定 commit/tree 身份一致，且拒绝覆盖 `predict/` 与 `score/`；然后才安装该固定依赖并运行 prediction、严格
转换、冻结 `evaluate.py` 评分和最终 hash metadata。它不调用 SFT，所以不会重跑已完成的 16 小时训练。

第一次 prediction-only 续跑成功安装 `jieba==0.42.1`，但 LLaMA-Factory 随后按同一
`predict_with_generate` 的预检报缺 `nltk`，进程 GONE、GPU 未实际使用。查固定 `v0.9.3` 的
`hparams/parser.py` 与 `setup.py` 后确认，这个分支无条件要求整个 metrics extra：`jieba`、`nltk`、
`rouge-chinese`；此前的 `[torch]` 安装不含这三个包。恢复提交 `20be231` 将三项显式固定为
`jieba==0.42.1`、`nltk==3.9.1`、`rouge-chinese==1.0.3`，并在续跑前逐项 import 与版本核验。
这次修复仍只影响环境可追溯性，不触及既有 SFT adapter、上游 converter、预测/评分口径或 seed；完成后才以
GPU0 再启动 prediction-only 续跑。

完整 metrics extras 经重启前逐项 import/version 核验后，PID `1819697` 在 GPU0 成功加载 Llama-3-8B 与
`train/adapter`，并进入 11,149 条 internal-dev generation（batch size 1）。首次运行观察约 444/11,149 条、
约 13.5 秒/条，日志估计剩余约 39 小时；GPU0 约 77% / 17.8GiB，GPU1–3 空闲。LLaMA-Factory 的
`save_predictions` 会在 `trainer.predict` 结束后一次性写 `predict/generated_predictions.jsonl`，所以此阶段文件
尚未出现不表示停滞。当前没有 error、尚无任何可报告的 causal P/R/F1；generation 完成后才依序执行严格转换、
冻结 evaluator 评分和 final metadata。

2026-09-10 状态更新：E8 已完成 11,149/11,149 generation，`generated_predictions.jsonl`（59,336,796 bytes）
与 adapter 均留在原 4090 run root；成功 SSH 读取到外层/预测进程均 GONE、GPU0–3 空闲。`372a6e2` 的转换器
将第 107 条的精确重复合法 `PRECONDITION` 引用归并为一个 relation-set 成员，定向测试及本地三件套均通过
（534 passed / 26 skipped、ruff 0、smoke OK）。但同步到 4090 后的全量验证还发现 95 条不可无歧义解析的输出：
第 7,817 条 1 条，以及第 8,842–8,935 条连续 94 条（同一 47-event 文档的两个分区）。它们缺失标签、断裂事件
标记或混入自由文本；不得补 NONE、猜 event id 或局部重生成/拼接。固定 tokenizer 实测所有保存 prompt 均为
286–2,015 tokens、没有一条超过 2048，因此不能把根因臆断为截断。尚未生成 `score/official_predictions.jsonl`、
官方 metrics 或 final metadata，故**没有可报告的 causal P/R/F1**。完整失败记录与有效性边界见
[`results/PHASE_R1.md` §9.6](results/PHASE_R1.md#96-e8--llmere-causal-s13-生成输出有效性失败2026-09-10)。
要重取该 baseline 数字，必须先冻结一个完整、统一的推理/约束解码方案并取得作者授权，再重生成全 11,149 条；
不重训 LoRA adapter。


</details>
