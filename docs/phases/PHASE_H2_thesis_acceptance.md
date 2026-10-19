# PHASE H2 — 全篇稳健性与复现验收

> **最终验收待方法贡献与合法确认；不是等待E3首轮实验。** 本 phase 只验收，不设计新方法、
> 不重开止损路线、不承担论文写作。2026-10-19按作者既有裁决对齐历史文案：E3首轮已收口，
> factorial/Holm及C5/A4/D4直接接E3的旧依赖已撤销，不得恢复；依据见EXPERIMENT_PLAN §1/§7.5、
> PHASE_E3契约及R1 §25.120。此次未修改科学门或授权额外实验。

## Goal

证明 C5/A4/D4/E3 的表格、逐实例产物、适用的确认结果、消融和真实上游接口可从冻结 bundle
独立反查，并形成明确的 pass/failed/blocked 章节清单。尚无确认授权或证据时如实标未完成。

## Inputs

- P1 manifests/evaluator/stage bundle schema；
- C5/A4/D4/E3 immutable bundles、旧 A3/D3/C4 failed evidence 与 `docs/results/PHASE_*.md`；
- 当前代码 commit、环境锁和远端 checkpoint 位置。
- 作者提供的四篇硕士论文质量参照及逐项差距：
  `docs/research/20261019_thesis_quality_and_experiment_tree.md`、R1 §25.121。
  作者要求最终质量、实验设计与结果证据优于这些论文；H2据此核实际证据，不采用跨任务分数
  排序、LLM质量打分或以可追溯性替代方法优势，不降低冻结门、不自行加实验授权。

## Tasks

1. **Bundle audit**：逐章复算 source/manifest/candidate/evaluator/config/code/checkpoint hashes、population
   counts、ID 集、schema、upstream status 与 exploratory 标记；
2. **Main-table audit**：主表每个数字能反查到 `metrics.json` 和 scorer，baseline 输入前提一致；
3. **Seed/statistics audit**：进入方法优势结论的行按有效合同核matched seeds、mean、sample std和
   document-cluster paired CI；额外seed只在其前置和再次明确授权后执行。E3保留现有单seed身份，
   不为H2恢复已撤销的factorial/Holm家族或启动新增应用章实验；
4. **Ablation audit**：每个 claim 有单变量消融，负/零结果未删除；
5. **Reproduction audit**：随机选一个 baseline 与一个 full method，用缓存或允许的单卡命令重放 scorer；
6. **Cross-stage audit**：E3引用实际upstream_registry的v5判别式抽取器身份，不冒称当前C5/A4/D4
   的同实例下游收益；核该registry与真实文件一致，旧A3/D3/C4身份未覆盖，无gold proxy冒名；
7. **Access/claim audit**：核 final-valid config/code/checkpoint/threshold hashes、
   `historical_final_access_disclosed`、`final_valid_access_ledger` 与 `v6_confirmatory_eval_count`；删除所有跨
   split 胜出、解封后回调、
   不同 backbone 因果、噪声内正增益、“首次”及把本地重建 CGEP 协议冒充官方派生轴的表述。

## Done when

- 三个方法章分别明确 `pass`、`failed` 或 `blocked`，不存在“差一点算过”的中间状态；`blocked` 在论文
  结构算术中按方法章失败计；
- pass 方法章均满足“primary anchor + 另一不同方法族强 baseline”胜出规则，至少 2/3 matched-seed delta
  为正，CI 与核心消融齐全；
- E3既有公开对手、图依赖正控、构建损失/扰动及配对统计可追溯；单seed、重建协议、对手不对齐和
  文档捷径限制随结论报告，不要求已撤销的factorial，不将首轮完成冒充所有确认完成；
- 所有论文候选表格都能从 bundle → metrics → scorer → manifest 反向追踪；
- 本地三件套全绿，文档链接/whitespace/单一事实源检查通过；
- `docs/TODO.md` 更新最终验收状态，不复制实验数字。

## Stop conditions

- 缺适用seed/消融/强baseline：指出对应科学缺口，按主表与合法授权补充；不在H2发明新机制，
  不因历史合同列有seed而自动启动，不在E3新增实验；
- bundle hash/ID 不一致：相关章节立即失效，先修复来源，不允许只改文档；
- 复现分数超出已记录噪声且无法解释：相关结果标 stale，重新跑 scorer/必要最小训练；
- 任一方法线failed/blocked：不得以工程完成或负结果冒充方法优势；后续实质不同路线按当前主表回R1。
  已有作者确定的论文结构保持，H2不自行改纲；
- 只有文献、数据、功效或资源证据证明合理范围内不可实现时，才由**作者**决定是否改纲（导师只看结果，不介入章节结构）；
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
