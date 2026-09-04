# EKG 实时状态

> 更新于 **2026-09-04**。新会话先读 [`HANDOFF.md`](HANDOFF.md)；数字以
> [`results/`](results/README.md) 为唯一事实源。

## 唯一正式活动阶段

`A3 Ch2`。**工作点线已封存 FAILED**（两个核心设计周期用完）；近似 retriever 三片
（r1/r2/r3）Stage-1 三连未过门，同样封存；prototype、ATLoss 此前已止损。
当前不追加以上任何方案的 seed 或调参，也不做第三个工作点、第四个 retriever。

## 下一步

1. P1 r15、A3.6 r16 preflight 已双端 SHA-256 一致，4090 P1 `validate-only` PASS；
2. A3.6 四臂已于 2026-09-04 18:03（Asia/Taipei）用 GPU0–3 后台并行启动：local → rates-only →
   +coref aux → +per-family selection。任务使用 `setsid nohup`、独立 SID/run-dir/log，SSH 仅作观测；
   下一步按 ALIVE/GONE/SSH-failed 三态监控，成功观测 GONE 后校验并评分；
   ⚠️ 第 4 臂必须从头重跑，**不得回收 r13 的 `best_by_family` 曲线**；
3. A3 写入真实结果并导出 `status=failed` handoff；旧机制判定不因 v6.1 改写；
4. 并行开展 R1 中不读取 A3 待出结果的论文/代码矩阵、MAVEN-ARG 跨数据 ID 审计和 Ch1/Ch3
   MDE/power；A3 handoff 后完成 Ch2 因果链与整体准入。未通过对应 R1 门不启动 proposed GPU 实验；
5. 当前依赖计划：R1 后开展 C5 mention-local argument uncertainty、A4 full-candidate pair-evidence
   sufficiency 与 D4 typed-cue factuality；没有额外依赖时可重排或并行，三者 handoff 齐备后进入 E3。
   这是可修订 plan，不是 SPEC；
6. 4090 空卡可用于互不冲突的不同方案/任务并行；多种子仍须逐次授权。

## 当前三端

- local：`main`；P1 r15 为当前可信根（`1e31a9ac…f9655`），A3.6 r16 recipe plan 为
  `3f2f385d…c50be`；执行面提交 `96e2d64`，473 passed / 24 skipped、ruff 0、smoke OK；
- 4090：**已恢复**，启动前四卡全空、无进程、worktree clean，随后同步到 `ebb57da`；正式 backbone pin
  `71be7419…c961ea9` 在此；当前四张卡分别运行 A3.6 r16 的四个冻结臂，首轮观测显存
  4.38–4.54 GiB、训练日志均已到 epoch 0 / 500 docs，`final_valid_accessed=false`；
- 5090：`Connection refused`，需 `cpolar-ssh-update`；大产物（21 GB / 961 MB / 2.0 GB）原地保留。

## 禁止

- 未授权额外 seeds；使用 final-valid 选模；不同 candidate/evaluator/split 直接比较；
- 把 Ch1 event-level argument oracle 或 Ch3 gold-evidence oracle 当方法分；
- **看到某个选模规则能救分再改选模规则**（选模轴伪影，Phase C 教训）；
- 未询问就跨机搬 checkpoint、数据集或其他大文件；
- `rsync --delete`、远端 `git clean -fdx`、服务器 `uv run`/`uv sync`；
- 复活已封存方案（工作点、近似 retriever、prototype、ATLoss），或用更大 backbone 掩盖机制无效。

## 成功条件

Ch1–Ch3 必须在统一公开主指标上超过多个同协议方法；否则只能作为系统组件。所有结论必须可从
结果表追溯到 commit、manifest、candidate、evaluator、命令、checkpoint 和 hash。三方法章 + 一系统章
不预设降标；旧机制失败后只有通过 R1 的实质不同方法家族才能重开，不能以换名、扫参或更大 backbone
绕过止损。
