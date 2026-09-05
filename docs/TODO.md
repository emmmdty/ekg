# EKG 实时状态

> 更新于 **2026-09-05**。新会话先读 [`HANDOFF.md`](HANDOFF.md)；数字以
> [`results/`](results/README.md) 为唯一事实源。

## 当前正式活动阶段

`R1 方法设计准入`。A3 已用不可变 bundle `a3-v6-20260905-r17` 正式 `failed` 交接；工作点、近似
retriever、prototype、ATLoss 均封存，不追加 seed 或调参。R1 尚未放行任何 proposed GPU pilot。

## 下一步

1. P1 r15 仍是可信根；A3.6 四臂全部完成并通过 metadata、单变量、人口、evaluator、final-valid 与
   双端 artifact hash 校验。旧方法最高 causal F1 仍未过主锚，权威数字见
   [`results/PHASE_A.md`](results/PHASE_A.md)；
2. T018 Ch2 prospective power 已通过；当前 R1 三章状态：Ch1 power PASS 但 mention-local input/强 baseline
   blocked，Ch2 power PASS 但缺第二个独立同协议强 baseline，Ch3 五折 OOF 已冻结但 baseline OOF/power
   仍 blocked；
3. Ch3 RoBERTa+CLS / DMRoBERTa 五折 OOF 已在 4090 四卡后台排队运行，run root
   `runs/stages/R1/r1-v61-factuality-oof-r2/`；每卡先跑一个 CLS fold，再自动接后续任务。首轮四卡均已
   进入 epoch 1，SSH 断开后仍存活。等待期间继续寻找 Ch1/Ch2 强 baseline，不写 proposed 方法；
4. 当前依赖计划：R1 后开展 C5 mention-local argument uncertainty、A4 full-candidate pair-evidence
   sufficiency 与 D4 typed-cue factuality；没有额外依赖时可重排或并行，三者 handoff 齐备后进入 E3。
   这是可修订 plan，不是 SPEC；
5. 4090/5090 当前可用于互不冲突的**准入 baseline smoke/OOF**；长任务继续 `setsid nohup`，不依赖 SSH
   存活。多种子与跨机 checkpoint 搬运仍须另行授权。

## 当前三端

- local：`main`；P1 r15 `1e31a9ac…f9655`；A3 handoff protocol `c187bf03…9359e`；R1 最新代码提交
  `277b36f`，488 passed / 24 skipped、ruff 0、smoke OK；
- 4090：A3.6 四臂已 GONE 且 GPU0–3 空闲；checkpoint 均留在
  `/data/TJK/ekg/runs/stages/A3/a3-v6-recipe-accounting-r16/`，未搬运；
- 5090：可连接，HEAD `4e893c1`；R1 JSON/逐实例 anchor 双端 SHA-256 一致。32,607 MiB 中约
  12,222 MiB 被既有 Qwen rerank/embed 服务占用，服务不动、checkpoint 不搬。R1 尚未放行 proposed
  pilot；可在具体 baseline 命令和协议冻结后使用，不为占卡启动无效训练。

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
