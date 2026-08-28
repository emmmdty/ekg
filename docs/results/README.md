# 实测档案索引

每个阶段一份，存**当时跑出的真实数字、口径、踩过的坑**。实时状态在 [`../TODO.md`](../TODO.md)。

**单一事实源**：实验数字**只在这里权威**。`TODO.md` / `EXPERIMENTS.md` / `phases/README.md`
只引用不复制。两处不一致时以本目录为准，并立刻改另一处。

| 档案 | 章 | 一句话结论 |
|---|---|---|
| [`PHASE_P1.md`](PHASE_P1.md) | 协议 | P1 r3 trust root 与 A3 plan-bound CPU preflight PASS；GPU baseline 尚未启动 |
| [`PHASE_A.md`](PHASE_A.md) | Ch2 | 长窗口与训练协议修正有效，但 causal 尚未超过统一 official anchor，subevent 仍回退 |
| [`PHASE_B.md`](PHASE_B.md) | Ch2 | 结构违反清零 ✅，ECG 可重建率无增益 ❌；α=0.2 因召回上限不可达 |
| [`PHASE_C.md`](PHASE_C.md) | Ch1 | official-valid 错误以过并为主；换底座失败，旧非对称方向被推翻 |
| [`PHASE_D.md`](PHASE_D.md) | Ch3 | valid 检测信号较强但尚无同 split 强基线胜出证明；净化结构/下游双负 |
| [`PHASE_E.md`](PHASE_E.md) | Ch4 | 构建损失 −.0218 是唯一确凿效应；图侧干预全在噪声地板内 |

## 读之前要知道的三条

1. **升降如实**：这些文件里的负结果不是待修复的 bug，是交付内容。不要为了让某个数好看而改口径。
2. **对标数字须回一手表格核**：Phase C 因为「MUC ~86」白跑两轮；Phase A 因为官方 causal 基线
   栏位漏填而把「达标」判错。引用任何外部数字前先确认出处、split 与口径。
3. **噪声地板 ±.003–.004 MRR**（Phase E 实测）：小于该量级的增益，多种子之前不得作正面主张。
