# PHASE D3 — 证据条件化的事件事实性检测

> **BLOCKED BY A3 HANDOFF。** 不要求 A3 必须成功，但必须先收到不可变 bundle/status，保持严格串行。
> 历史事实见 [`../results/PHASE_D.md`](../results/PHASE_D.md)；旧 D2 跨数据集契约不得执行。

## Goal

在同一 MAVEN-FACT public-valid 协议上回答：evidence→label 或联合软耦合能否稳定优于平行双头和预注册
主锚，并在证据与稀有类护栏内成立。label→evidence/bidirectional 是二级假设，不是章节成立前提。

## Inputs

- P1 共享 train/internal-dev/final-valid manifests 与 source hashes；
- MAVEN-FACT gold mentions、五类标签和 evidence annotations；
- 历史并行双头 checkpoint/结果，只作 reproduction base；
- A3 bundle/status，用于记录上游身份；组件主表仍使用 gold structure/mentions。

禁止：把 hidden-test 论文数字与 valid 直接相减；先做跨数据集；复活事实性净化；用 accuracy 掩盖 macro-F1。

## Tasks

### D3.0 scorer 与 baseline closure

- 固定五类 macro-F1、每类 P/R/F1、evidence 三类宏平均和 pooled span F1；
- baseline 运行前预注册 primary-eligible roster（RoBERTa+CLS、DMRoBERTa）与默认最高 internal-dev
  macro-F1 mean 的 anchor 规则，平分按 roster 顺序；
- 先只用 train/internal-dev 闭合 RoBERTa+CLS 与 DMRoBERTa；只有 DMRoBERTa 两个工程修复轮仍无法闭环，
  才按预登记规则替换为 DMBERT；
- majority/lexicon 只作下界，不计入“超过多个强方法”；
- 每个 baseline 先做 loader/label/evidence 10-doc smoke；一轮工程修复是有界诊断、补丁和同协议 smoke，
  两轮失败即换预列候选；候选失败不等于任务失败；
- 在任何方法结果产生前冻结同 split primary anchor、随机主锚 matched seeds 13/17/42、document-cluster
  CI、evidence 非劣 margin，并保存五类 mention/document supports。

### D3.1 reproduction base

在显式 internal-dev manifest 上重跑共享 encoder + 平行 label/evidence heads，确认 best checkpoint、五类标签
顺序、evidence recall ceiling 与历史链路一致。该模型是消融基线，不是创新。

### D3.2 Mechanism 1：evidence-conditioned label

先由 evidence distribution/representation 条件化五类 label head；evidence head 保持与 base 同定义。
seed 13 internal-dev 单变量 pilot。必须报告五类和 evidence，不得只报 macro-F1。

若增益只来自 CT+ 或 evidence 越过预注册非劣界，允许第二个核心设计周期；只有实现、测试和协议 smoke
均通过才计周期，第二次仍失败即停止，不扫 loss weight 网格。

### D3.3 二级机制：label→evidence / 双向条件耦合

公开 MAVEN-FACT 已采用“先预测 factuality，再定位 supporting words”的 label→evidence pipeline，因此该
方向只作 reproduction/二级扩展。仅当 D3.2 有信号时才测试双向耦合；不得同时换 encoder、采样、标签
权重或数据。二级机制最多一次实现 + 一次定向修订；失败时删除对应 claim，不消耗或重置 D3.2 核心
预算，也不阻断 promotion。

### D3.4 Promotion 与三种子

只有 internal-dev 同时满足以下条件才跑 seeds 13/17/42：

- 五类 macro-F1 高于 seed-13 primary anchor；
- evidence 宏平均/pooled F1 通过预注册非劣 margin；
- primary anchor 对 PS-/Uu F1 非零时不得崩为零，且合并稀有类通过 document-cluster 非劣 CI；
- evidence→label 相对平行双头的 macro-F1 document-cluster 95% CI 下界大于 0。

冻结 config/code/checkpoint/threshold hashes 与 final-valid access ledger 后，baseline/主锚/方法三种子在
同一个 sealed batch 中运行 final valid；不用 valid 返调结构、weight、epoch 或阈值。只有未返回指标且
hashes 完全一致的基础设施失败可原样重试；否则返调/重跑只能标 `exploratory`。

### D3.5 节点属性导出

导出逐 mention：五类概率、预测标签、evidence spans、doc/mention/node IDs、manifest/checkpoint hashes。
提供映射到 `EventNode.metadata` 和 `CgepNode` 序列化视图的 CPU 测试；不得只导出净化后的边 dump。

## Done when

- 至少两个强 baseline 在同一 valid 重跑；
- 我们三种子 macro-F1 均值高于 primary anchor 和另一不同方法族强 baseline，且相对主锚的
  document-cluster paired-bootstrap 95% CI 下界大于 0，至少 2/3 matched-seed delta 为正；证据与稀有类
  护栏通过；
- 平行双头与 evidence→label 核心消融完整；实际保留的 label→evidence/bidirectional claim 才要求对应消融；
- 逐 mention factuality/evidence bundle 可被 E3 读取且 ID 零缺失；
- 结果追加到 `docs/results/PHASE_D.md` v6 小节；
- 本地三件套全绿，4090 checkpoint/log/bundle 可追溯。

## Stop conditions

- 两个有效 evidence→label 核心设计周期后同 split 不领先主锚：方法章失败，降为系统组件；
- 增益只来自多数类、evidence 越过非劣界、稀有类崩为零或标签映射变化：不得 promotion；
- 任一 baseline 只能通过改变 label universe/scorer 才运行：不纳入主表；
- DMRoBERTa 与预登记 DMBERT 替代均无法闭合、导致不足两个强 baseline：D3 `status=blocked`，记录最佳
  可用 historical/local factuality `fallback_component_bundle_id` 后交接；C4 仍可继续；
- failed 后停止 FactBank/UW/MEANTIME、LLM baseline 和净化扩展，不用外部数据换榜单；
- 无论 pass/failed/blocked，均导出诚实 status；D3 局部失败不阻塞 C4，E3 可以消费该 predictor，但必须
  保留 evidence identity。

## Handoff

交付 D3 bundle 后才进入 C4。若 failed/blocked，C4 不受方法结论阻塞；E3 中 factuality 维度标为“现有
系统预测”而不是“经验证改进”。

## GPU

4090 单卡，预计轻于 A3。先展示命令、工作目录和预期 `runs/stages/d3/...`、checkpoint、log。
5090 每次单独授权。本 phase 不启动跨数据集额外训练。
