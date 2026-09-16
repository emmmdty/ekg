# EKG 实时状态

> 更新于 **2026-09-16**。新会话先读 [`HANDOFF.md`](HANDOFF.md)，再读唯一权威计划
> [`EXPERIMENT_PLAN.md`](EXPERIMENT_PLAN.md)；数字以 [`results/`](results/README.md) 为唯一事实源。

## 当前正式活动阶段

**方法实验期，Gate 1 已判「不过」。** D4 的 typed-cue 家族 2026-09-12 跑完即失败
（full `.476515` 低于两条锚与负控），按预冻结分支**不开第二个周期**，转 A4/C5，到 **Gate 2** 判还剩几个方法章。

**2026-09-16：待裁决清零。** §0.5a 的五项已于 09-15 裁定；§0.5b 的第 6 项由作者 09-16 裁定
**(甲) A4 维持现状、原样跑 A4.3**（代码即「戊 in / A out」`5cfbeff`），**A4.3 出数字后不再接受变更**。

- **A4 三臂探测归因已清**：塌 subevent 的是那处 `retained` detach（根因 A，已回滚），不是 (戊)；
  但 `full` causal F1 9.77 仍低于同 backbone 的 `remove_core` 31.13 约 21 点 ⇒ 如实交 Gate 2；
- **C5.3 首跑的缺陷已修**（`a1e1509`+`a65f456`）：推理侧缺 `--argument-predictions`；
  冒烟补上推理路径，`predicted_arguments.py` 进 `CODE_FILES`（8→9），**preflight-r2 `7a56e451…b6b0`**；
- ⚠️ **Gate 2 的「3 章过」分支在 Gate 1 判不过那天就已经死了**——D4 已关闭，最多只剩 2 个方法章。

## 下一步

1. ✅ **C5.3 pilot-r2 跑完**（09-16）：`full` MUC **79.90115** > `remove_core` 79.15966 > 负控 78.83333，
   **臂序第一次是对的**；但比主锚 80.98472 低 **1.08** ⇒ **门未过**。数字见 `results/PHASE_C.md`；
2. ✅ **CSProm-KG 复现成功**（09-16）：WN18RR MRR **0.572682** vs 公布 0.572660，四项全在容差内
   ⇒ **名册第一个 FR-016 (a)**。数字与五处透明补丁见 `results/PHASE_E.md`；
3. 🟢 **A4.3 四臂在 5090 上跑**（2026-09-16 11:02 起，作者：「4090 不可行就使用 5090」），
   契约 `11e4343a…490c`，**实测 10–13 小时**（早先写的 4–5 小时是错的），预计 09-17 凌晨收尾。
   **收口照 `HANDOFF.md` §0.3.1 的六步走**；⛔ 跑完前不要动 A4 契约钉住的 7 个文件
   （`--aggregate` 会重新校验哈希）。中间核查已做：本跑 dev 轨迹与 09-15 探测逐点重合 ⇒ 跑是有效的，
   **预期复现探测的失败形态**（causal 9.77 vs 判定线 33.17/32.10/32.01，subevent 破护栏）；
4. Gate 2：两个输入齐了再判。**「3 章过」分支已随 Gate 1 失效**，C5 门未过、A4 预期门未过
   ⇒ 现实区间「1 章过甚至 0 章过」。执行代理**不得**自行降级结构、开新家族或启动第二周期。

实验截止 **2027-02**；排期与估算基准率见主表 §3。

## 当前三端

- **local**：`main` 与 `origin/main` 同步、工作树干净；三件套 **639 passed / 29 skipped**、ruff 0、
  `ekg-smoke` OK；审计 `PASS` / 36 requirements。P1 r15 `1e31a9ac…f9655`；
- **gpu-4090**：GPU 已修好（580.178.04），但**四卡自 09-10 起被他人 vllm 占满**（09-16 复核
  19,15x MiB / 24,564 MiB，35–63% util），已第 7 天。ssh 与 CPU 全程可用；
  **作者 2026-09-15：不要因为它拖慢进度**；
- **gpu-5090**：**现为主力机，09-16 起同卡并行两个任务**：C5.3 pilot-r2（约 3.4 GB）与
  CSProm-KG WN18RR 推理。CSProm-KG 为跑通打了四处**透明补丁**（nltk 离线、checkpoint
  `map_location`、`add_safe_globals`、PL2 钩子迁移）并把该 venv 的 transformers 降到 4.57.6
  （作者原 pin 是 4.16.2；5.x 删掉了 `get_extended_attention_mask`）——前后 hash 记在
  `results/PHASE_E.md`。
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
