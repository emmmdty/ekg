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

⇒ 按 `EXPERIMENT_PLAN.md` §5，落 **「≤1 章过」** 分支：**与导师共同决定改纲**。
⛔ 执行代理**不得**自行降级论文结构、开新机制家族、启动第二设计周期、调门槛护栏或跑 seed 17/42。

## 下一步

1. 🔴 **等作者对 Gate 2 的裁决**——两页结果已摆好：`results/PHASE_A.md`（A4）·
   `results/PHASE_C.md`（C5）· `results/PHASE_D.md`（D4）。**在拿到裁决前队列上没有可执行的方法实验任务**；
2. 📝 本周周报已生成：`reports/2026-09-17_周报.md`，第 4 节的下周 TODO 随裁决更新；
3. ✅ **A4.3 已收口**（09-17）：聚合 `status=pass`，四臂 `complete`、同 seed 13、`final_valid_accessed=false`、
   7 个代码哈希重校验通过；失败形态是**召回坍塌**（causal 预测 4,895→532，recall 31.55→4.17），
   且**在 dev 上就已塌**（0.0796 vs 0.3122）⇒ 不是评测或选点问题；
4. ✅ **C5.3 / CSProm-KG 已收口**（09-16）：C5 门未过；CSProm-KG WN18RR MRR 0.572682 vs 公布 0.572660
   ⇒ 名册第一个 FR-016 (a)；
5. 不阻塞的存量：SimKGC / BART contrastive / MCPredictor 维持 (b) 并写障碍（G-11a），4090 线 A4
   `preflight-r2 a3cc6c44…f73c` 保留可补跑。

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
两方法章 + 应用章（领域硕士标准形态）／≤1 方法章时与导师共同决定改纲。
**不自行降级**；旧机制失败后只有通过实质不同的方法家族才能重开，不能以换名、扫参或更大
backbone 绕过止损。每个家族允许**两个有效周期**——5 个月预算下第二周期是可负担的，
第一轮失败不等于该章结束。
