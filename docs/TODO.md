# EKG 实时状态

> 更新于 **2026-09-04**。新会话先读 [`HANDOFF.md`](HANDOFF.md)；数字以
> [`results/`](results/README.md) 为唯一事实源。

## 唯一正式活动阶段

`A3 Ch2`。**工作点线已封存 FAILED**（两个核心设计周期用完）；近似 retriever 三片
（r1/r2/r3）Stage-1 三连未过门，同样封存；prototype、ATLoss 此前已止损。
当前不追加以上任何方案的 seed 或调参，也不做第三个工作点、第四个 retriever。

## 下一步

1. 提交当前脏树；4090 `git fetch && git reset --hard origin/main`（已确认 clean 且 HEAD 为祖先）；
2. **先做代码整改**：trainer 改用 `ekg.core.protocol` 的权威切分实现（并把该文件加进
   `build_p1_bundle.py` 的 `CODE_PATHS`）、收敛重复的 `sha256_file`；
3. 再基于当前 HEAD **重建 P1 trust root**（trainer 属 `CODE_PATHS`，顺序反了要重建两次）；
4. 用冻结 seed 13 分账 official recipe：local → rates-only → +coref aux → +per-family selection；
   ⚠️ 第 4 臂必须从头重跑，**不得回收 r13 的 `best_by_family` 曲线**；
5. 分账清零后，Ch2 最后一个核心周期候选 = pair-conditioned evidence + 跨句 hard-negative balance；
6. Ch1 只做 mention-local predicted arguments + uncertainty/cluster-risk；
7. Ch3 只做 typed cue + evidence-sufficiency/unknown gate；
8. 4090 四卡全空 —— 不同方案/任务可并行（C 类），多种子仍须逐次授权。

## 当前三端

- local：`main`；470 passed / 24 skipped、ruff 0、smoke OK；planning-file 清理与两份报告待提交；
- 4090：**已恢复**，四卡全空、无进程、worktree clean、HEAD 为 `origin/main` 祖先；正式 backbone pin
  `71be7419…c961ea9` 在此，只有绑定它的结果能进正式主表；
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
结果表追溯到 commit、manifest、candidate、evaluator、命令、checkpoint 和 hash。
