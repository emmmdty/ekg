# PHASE H2 — 全篇稳健性与复现验收

> **BLOCKED BY E3。** 本 phase 只验收，不设计新方法、不重开止损路线、不承担论文写作。

## Goal

证明 C5/A4/D4/E3 的表格、逐实例产物、三种子、消融和跨章接口可从冻结 bundle 独立反查，并形成
明确的 pass/failed/blocked 章节清单。

## Inputs

- P1 manifests/evaluator/stage bundle schema；
- C5/A4/D4/E3 immutable bundles、旧 A3/D3/C4 failed evidence 与 `docs/results/PHASE_*.md`；
- 当前代码 commit、环境锁和远端 checkpoint 位置。

## Tasks

1. **Bundle audit**：逐章复算 source/manifest/candidate/evaluator/config/code/checkpoint hashes、population
   counts、ID 集、schema、upstream status 与 exploratory 标记；
2. **Main-table audit**：主表每个数字能反查到 `metrics.json` 和 scorer，baseline 输入前提一致；
3. **Seed/statistics audit**：方法与随机主锚的 matched 13/17/42 原值、mean、sample std、document-cluster
   paired CI 齐全；Ch4 主 contrasts/Holm 校正齐全；
4. **Ablation audit**：每个 claim 有单变量消融，负/零结果未删除；
5. **Reproduction audit**：随机选一个 baseline 与一个 full method，用缓存或允许的单卡命令重放 scorer；
6. **Cross-stage audit**：E3 引用的 C5/A4/D4 bundle IDs/status 与真实文件一致，旧 A3/D3/C4 身份未被
   覆盖，无 gold proxy 冒名；
7. **Access/claim audit**：核 final-valid config/code/checkpoint/threshold hashes、
   `historical_final_access_disclosed`、`final_valid_access_ledger` 与 `v6_confirmatory_eval_count`；删除所有跨
   split 胜出、解封后回调、
   不同 backbone 因果、噪声内正增益、“首次”及把本地重建 CGEP 协议冒充官方派生轴的表述。

## Done when

- 三个方法章分别明确 `pass`、`failed` 或 `blocked`，不存在“差一点算过”的中间状态；`blocked` 在论文
  结构算术中按方法章失败计；
- pass 方法章均满足“primary anchor + 另一不同方法族强 baseline”胜出规则，至少 2/3 matched-seed delta
  为正，CI 与核心消融齐全；
- E3 消费者可信、同实例 factorial/CI 完整，或按 stop 条件收缩并撤回相应主张；
- 所有论文候选表格都能从 bundle → metrics → scorer → manifest 反向追踪；
- 本地三件套全绿，文档链接/whitespace/单一事实源检查通过；
- `docs/TODO.md` 更新最终验收状态，不复制实验数字。

## Stop conditions

- 缺 seed/消融/强 baseline：退回对应 phase 补既定矩阵，不在 H2 发明新机制；
- bundle hash/ID 不一致：相关章节立即失效，先修复来源，不允许只改文档；
- 复现分数超出已记录噪声且无法解释：相关结果标 stale，重新跑 scorer/必要最小训练；
- 任一方法章 failed/blocked：不得在 H2 自动降为两方法章；退回 R1 做实质不同的方法家族重规划；
- 只有文献、数据、功效或资源证据证明合理范围内不可实现时，才由作者与导师共同决定是否改纲；
- E3 假设被证伪：保留零结果与边界，不替换消费者/任务追正结果；
- 超出已批准 GPU 预算：删除非必要加分项，不能叠加预算。

## Outputs

- 全篇 bundle/provenance 验收表；
- 章节 `pass/failed/blocked` 总表与撤回 claim 清单；
- 可复现命令清单和环境/checkpoint 定位；
- 更新后的 TODO/结果索引；不生成论文正文。

## GPU

默认只用 CPU/cache。只有 reproduction audit 确有必要时使用 4090 单卡；命令、目录、产物先展示。
5090 每次单独授权。
