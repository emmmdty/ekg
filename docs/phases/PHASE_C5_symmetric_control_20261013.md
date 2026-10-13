# C-41 · frozen scorer 的双向等权控制（2026-10-13）

价值与可行性见 `results/PHASE_R1.md` §25.44。本轮产出可部署输入上的实际分数，
不是将 oracle 提升称为方法结果。对称化概念来自
[Ahmed et al., Findings ACL 2023 §4.2.1 Eq.1](https://aclanthology.org/2023.findings-acl.100v2.pdf)。
其原模型是 cross-encoder，本次只复用既有 MAVEN official joint head，并固定平均 **raw logits**；
不是其完整训练/检索系统复现，也不是新方法贡献。

冻结单位、P1 evaluator、候选 IDs 与 checkpoint 完全沿用已完成 official-joint CPU cache。
任务给定类型 policy 沿用 type-control，各臂成对一致；原 frozen anchor 保留。
生产只读无标签 test.jsonl，零 gold、零训练，seed 13 仅约束既有初始化/随机置换。
原 checkpoint 留 4090，CPU 4 threads，CUDA 隐藏，batch 8、max_length 256。

固定三臂：

1. typed forward control：所有 logits 与完整既有 cache exact parity，类型控制 clusters exact parity。
2. symmetric：对 `[h_i;h_j;h_i*h_j]` 与 `[h_j;h_i;h_i*h_j]` 原 MLP 输出等权平均。
3. shuffled：原正向不变，反向在每篇/同类型合法 pair 桶内用 RNG 13 固定置换后等权平均。

dummy raw logit 始终为 0；候选形状与全集不改，给定类型约束显式披露。
shuffle 不使用 identity 标签；小桶/重复值可能不改变所有条目，不能把其当完美因果隔离。
encoder 与 checkpoint 不动，关系字段复制，不运行关系头。

先首批 smoke 验证 forward logits/type-control parity，再以同 config 跑 full。
新根 `runs/stages/R1/r1-v63-c5-20261013/symmetric_control/`；既有 output 即拒绝覆盖。
每个 scope 保存两份 predictions、directional_scores、metadata/status/hash。
独立 scorer 读取 frozen internal-dev gold，并核 source_lock/candidate digest；不接触 final-valid。

如未胜 stronger type-control 的 MUC、护栏降低或 shuffled 获得同样改善，不认定这条对称证据
支持目标改进；保留负结果，不扫平均权重、阈值、min/max、epoch 或额外 seed。
文档配对 counts/CI 只描述评测单位变化，不当跨初始化确认或新方法 power。
条件决策风险候选的新颖性/无泄漏输入/power 仍未准入；本控制不绕过该门。
