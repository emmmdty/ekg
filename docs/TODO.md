# EKG 实时状态

> 更新于 **2026-09-15**。新会话先读 [`HANDOFF.md`](HANDOFF.md)，再读唯一权威计划
> [`EXPERIMENT_PLAN.md`](EXPERIMENT_PLAN.md)；数字以 [`results/`](results/README.md) 为唯一事实源。

## 当前正式活动阶段

**方法实验期，Gate 1 已判「不过」。** D4 的 typed-cue 家族 2026-09-12 跑完即失败
（full `.476515` 低于两条锚与负控），按预冻结分支**不开第二个周期**，转 A4/C5，到 **Gate 2** 判还剩几个方法章。

**2026-09-15：五项待裁决全部裁定**（详见 `HANDOFF.md` §0.5a），队列不再卡在决策上：

- **A4** 取 **(戊)**（`sufficiency` 与 `necessity` 同作用面），5090 单臂探测已起；判据是 `base 判正数`；
- **C5 整条改走 gpu-5090 线**：preflight `a3f21f97…8141` 与 CPU/CUDA 双半边 smoke 全部 PASS，
  5090 重算主锚 MUC **80.98471986** 与 4090 线逐位相同；**A4.3 仍留 4090**（judgement line 含 32.10）；
- **Ch6 改序**：先做 CSProm-KG（公开 checkpoint，(a) 靠一次推理），SimKGC 落 (b)「原配置需 4×32 GB」；
- **LLMERE** 记 (b) Unverifiable；**SeDGPL 的 ESC (a) 不再投入**，落 (b) 并写清 .0599 vs .196 的差距。

## 下一步

1. A4 (戊) 探测收尾 → 读 `base 判正数`（回到 4,000 量级＝成立；仍 <1,000 ＝按契约走 (甲) 交 Gate 2）；
2. **C5.3 seed-13 pilot（三臂）**，5090，估 3–6 小时；
3. CSProm-KG WN18RR 推理取 (a)，容差已事前登记（MRR ±0.005）；
4. A4 戊-only 一臂，隔离 `train_a4_pair_evidence.py:349` 那处未验证的 detach；
5. A4.2/A4.3 等 4090 空卡，且要先重建 `preflight-r2`。

实验截止 **2027-02**；排期与估算基准率见主表 §3。

## 当前三端

- **local**：`main` 与 `origin/main` 同步、工作树干净；三件套 **635 passed / 29 skipped**、ruff 0、
  `ekg-smoke` OK；审计 `PASS` / 36 requirements。P1 r15 `1e31a9ac…f9655`；
- **gpu-4090**：GPU 已修好（580.178.04），但**四卡自 09-10 起被他人 vllm 占满**（09-15 复核
  19,25x MiB / 24,564 MiB），已第 6 天。ssh 与 CPU 全程可用；**作者 2026-09-15：不要因为它拖慢进度**；
- **gpu-5090**：**现为主力机**。C5 整条在这台机上（preflight + 双半边 smoke 已 PASS）；
  CSProm-KG 代码与独立 venv（torch 2.8.0 / PL 2.6.6）已就位，bert-large 从 ModelScope 直下。
  ⚠️ **外网是分域的**：gh-proxy 增量 fetch ✅ / 清华 PyPI ✅ / GitHub 直连 ❌ / 完整 clone ❌ /
  Google Drive ❌ / ModelScope ✅。⚠️ **cpolar 通道 2026-09-15 12:5x 整个下线**（不是端口变动，
  更新脚本治不了），期间按三态判活，不得判远端进程已死。

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
