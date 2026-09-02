# EKG 实时状态

> 更新于 **2026-09-02**。新会话先读 [`HANDOFF.md`](HANDOFF.md)；数字以
> [`results/`](results/README.md) 为唯一事实源。

## 唯一正式活动阶段

`A3 Ch2`。工作点、近似 retriever、prototype、ATLoss 已完成或封存；当前不追加这些方案的 seed 或调参。

## 下一步

1. 恢复 4090 连接后，先核验遗留 position-workpoint 50-epoch 任务、official 产物和 Git 状态；
2. 当前 relation trainer 已改变，先重建 P1 trust root；
3. 用冻结 seed 13 分账 official recipe：local → rates-only → +coref aux → +per-family selection；
4. 协议差异清零后，再决定是否启动 pair-conditioned evidence + 跨句 hard-negative 新方法；
5. Ch1 后续只做 mention-local predicted arguments + uncertainty/cluster-risk；
6. Ch3 后续只做 typed cue + evidence-sufficiency/unknown gate。

## 当前三端

- local：`main` 与 origin 一致；研究代码/结果截至 `f75c711`；五个用户既存文件 dirty，必须保留；
- 5090：`main` 与 origin 一致、tracked clean、无任务；大产物原地保留；
- 4090：SSH banner timeout，Git/任务状态 UNKNOWN；不得根据失联推断任务死亡。

## 禁止

- 未授权额外 seeds；使用 final-valid 选模；不同 candidate/evaluator/split 直接比较；
- 把 Ch1 event-level argument oracle 或 Ch3 gold-evidence oracle 当方法分；
- 未询问就跨机搬 checkpoint、数据集或其他大文件；
- `rsync --delete`、远端 `git clean -fdx`、服务器 `uv run`/`uv sync`；
- 复活已封存方案，或用更大 backbone 掩盖机制无效。

## 成功条件

Ch1–Ch3 必须在统一公开主指标上超过多个同协议方法；否则只能作为系统组件。所有结论必须可从
结果表追溯到 commit、manifest、candidate、evaluator、命令、checkpoint 和 hash。
