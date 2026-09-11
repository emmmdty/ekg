# EKG 实时状态

> 更新于 **2026-09-11**。新会话先读 [`HANDOFF.md`](HANDOFF.md)，再读唯一权威计划
> [`EXPERIMENT_PLAN.md`](EXPERIMENT_PLAN.md)；数字以 [`results/`](results/README.md) 为唯一事实源。

## 当前正式活动阶段

**方法实验准备期**。R1 准入已于 2026-09-11（E12）收口。**可执行实验只认
[`EXPERIMENT_PLAN.md`](EXPERIMENT_PLAN.md) 的 §4 主表**；`HANDOFF.md` 的 E 队列只是它的当周切片。

- `SPEC.md` 升 **v1.1.0**：QR-001 把 baseline 广度由准入门改为**主表报告要求**；新增 **FR-016**
  复现保真度（(a) Verified / (b) Unverifiable 二选一）。
- **C5 已由 `blocked_pre_admission` 转 `frozen`**，A4 的确认性 promotion 不再等 LLMERE；
  三章契约 hash 已重绑，审计 `PASS` / 36 requirements。
- 论文结构定为：第3章 D4 事实性 · 第4章 A4 关系 · 第5章 C5 身份 · **第6章 E3 图谱构建与
  下游事件预测应用**。原 24 条件 factorial、Holm 校正家族、frozen-vs-fine-tuned 同 backbone 对照
  **已撤销，不得恢复**。
- **v6.1 三份方法设计一个都没跑过**：C5/A4 未实现，D4 只完成 D4.0 实现与本地 gate。

## 下一步

CPU 泳道八项全部可立即开工（4090 的 GPU 死了但文件系统可 ssh）。建议起手
**C-2 EasyECR 核查 → C-1 D4.1 preflight → C-5/C-6 实现**，逐项判据见主表 §4.1。

长任务 GPU pilot 全部阻断在 **G-0（修 4090 驱动，需机主，我们无 root）**。
**gpu-5090 已获授权作临时顶替**，只跑 smoke 与小任务，逐次授权，边界见主表 §3.5。

实验截止 **2027-02**；排期与估算基准率见主表 §3，顺利情形 2027-01 底收口、2 月缓冲。

## 当前三端

- **local**：`main`；三件套 **534 passed / 26 skipped**、ruff 0、`ekg-smoke` OK；
  审计 `PASS` / 36 requirements。P1 r15 `1e31a9ac…f9655`；A3 handoff protocol `c187bf03…9359e`；
  三份 phase 契约与 R1 protocol 的最新 SHA-256 见 [`results/PHASE_R1.md`](results/PHASE_R1.md) §21.3；
- **gpu-4090**：⛔ **CUDA 完全不可用**（2026-09-11 驱动内核模块 580.173.02 与用户态库 580.178.04
  版本不符，需 root 重启或重载模块，机器共用）。**文件系统仍可 ssh 访问**，纯 CPU 任务照常。
  我方无进程在跑；E8 的 17G 产物、专用 CUDA venv 与 Llama-3-8B 镜像权重均留在原 namespace。
  远端 git 落后于本地，开工前 `git fetch && git reset --hard origin/main`；
  **`runs/` 下 E12 改过的三个 JSON 须双端 SHA-256 同步**，否则远端 preflight 会 fail-fast；
- **gpu-5090**：✅ **已授权作 4090 不可达期间的临时顶替**（smoke 与小任务，逐次授权，
  主体实验回 4090）。硬边界：EasyECR 跑不了（torch 2.0.1 不支持 sm_120）、Qwen3-8B LoRA 装不下
  （余量约 15GB）、长任务 pilot 不放这里。host key 不在 `known_hosts`，指纹
  ED25519 `SHA256:Jkfb9Tb14Z/SqsG6g9GedDjKZOcBl1DLW6zT0V1dkJY`，**须作者确认后再写入**。

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
