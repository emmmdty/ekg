# PHASE C4 — 语境判别的事件身份消解

> **BLOCKED BY D3 HANDOFF。** 历史错误事实见 [`../results/PHASE_C.md`](../results/PHASE_C.md)。
> 旧 C3 非对称代价契约不得继续执行；其错误剖析保留为本 phase 的诊断输入。

## Goal

在冻结 MAVEN-ERE gold-mention 协议上回答：局部论元与跨句语境能否区分同 trigger/同类型但不同
occurrence 的事件，并在公开共指标护栏内超过预注册主锚。校准聚类是可删除的二级机制。

## Inputs

- P1 的 manifests、official evaluator、stage bundle schema；
- Ch1 历史 lexical/RoBERTa checkpoint、710-doc prediction 与错误剖析；
- D3 bundle/status，仅用于跨章追溯；Ch1 组件主表不读取 D3 预测；
- MAVEN-ERE gold mentions 与 cluster labels。

禁止：继续旧非对称 loss/阈值主线；换 Longformer/large；用 ECB+/GVC/FCC 换榜单；用难例率代替 MUC。

## Tasks

### C4.0 修复训练/选模协议

`train_coref_scorer.py` 必须读取 P1 显式 train/internal-dev manifests，按 internal-dev MUC 主指标选 best
checkpoint，并保存每 epoch 曲线。不得再对全部输入固定 epoch 后直接报 valid。

### C4.1 baseline closure

baseline 运行前预注册 primary-eligible roster（official single/joint）与默认最高 internal-dev MUC mean 的
anchor 规则，平分按 roster 顺序。

同一 gold-mention/candidate/evaluator 协议至少运行：

1. lexical/lemma；
2. 本地 RoBERTa pair；
3. MAVEN-ERE official single；
4. MAVEN-ERE official joint；
5. RESIJ 仅在公开实现或忠实复现闭环时可选纳入，不是 C4 准入条件。

先只用 train/internal-dev 完成训练、选模和主锚选择，不得提前查看新 baseline 的 final-valid 分数。记录
MUC P/R/F1，并全报 B³、CEAFe、BLANC；同时冻结 same-trigger 与 cross-sentence 诊断集合、
candidate-ID digest/population counts。在任何方法结果产生前冻结同 split primary anchor、随机主锚 matched
seeds 13/17/42、document-cluster CI 与各 mandatory metric/cross-sentence recall 的非劣 margin。

### C4.2 Mechanism 1：context-discriminative pair representation

只改变 pair representation：加入局部论元、句内语境和跨句语境，使同 trigger 候选不再仅靠词形相似。
至少有去局部论元、去跨句语境两个消融。seed 13 internal-dev pilot；只有实现、测试和协议 smoke 均通过
才计一个核心设计周期，最多两个。

判断核心机制有效要求 MUC 相对 reproduction base 的 document-cluster 95% CI 下界大于 0，且
cross-sentence recall 与 B³/CEAFe/BLANC 通过预注册非劣界。same-trigger 过并必须报告；只有其预注册
方向 CI 越过 0 时才主张被降低，不作为独立 promotion 硬门。只改变 candidate sampling 或阈值不算表示贡献。

### C4.3 Mechanism 2：校准聚类

在 C4.2 冻结分数上学习/校准聚类决策，只用 internal dev。比较未校准聚类、全局阈值与校准聚类；
固定 candidate population。该机制失败时保留预注册全局阈值并删除 calibration claim，不消耗或重置
C4.2 核心预算，也不阻断核心 promotion；最多一次实现 + 一次定向修订。

### C4.4 Promotion 与三种子

只有 internal-dev 满足以下条件才跑 seeds 13/17/42：

- MUC 高于 seed-13 primary anchor；
- cross-sentence recall、B³、CEAFe、BLANC 通过预注册非劣 margin；
- C4.2 上下文表示相对 reproduction base 的 MUC document-cluster 95% CI 下界大于 0；
- same-trigger 过并必须报告；只有预注册方向 CI 越过 0 时才主张其被降低，但该辅助诊断不单独否决章节。

冻结 config/code/checkpoint/threshold hashes 与 final-valid access ledger 后，baseline/主锚/方法三种子在
同一个 sealed batch 中运行 final valid；不允许据其结果再挪阈值或 band。只有未返回指标且 hashes 完全
一致的基础设施失败可原样重试；否则返调/重跑只能标 `exploratory`。

### C4.5 导出

输出逐 mention-to-cluster 映射、pair confidence、cluster confidence、doc/mention IDs、manifest/checkpoint
hashes。投影到 Ch2/E3 时必须保留 source mention IDs，映射失败 fail-fast。

## Done when

- lexical/lemma、local pair、official single、official joint 四个 baseline 同协议完整；
- 我们三种子 MUC 均值高于 primary anchor 和另一不同方法族强 baseline，且相对主锚的 document-cluster
  paired-bootstrap 95% CI 下界大于 0，至少 2/3 matched-seed delta 为正；全部公开 coreference 护栏与
  same-trigger/cross-sentence 诊断完整；
- context/argument 核心消融完整；实际保留 calibration claim 时才要求 calibration 消融为正；
- mention-to-cluster bundle 与 E3 schema/ID 校验 PASS；
- 结果追加到 `docs/results/PHASE_C.md` v6 小节；
- 本地三件套全绿，4090 checkpoint/log/bundle 可追溯。

## Stop conditions

- 两个有效上下文核心设计周期后仍不超过同 split primary anchor：停止方法主张；
- 增益只是 precision/recall 阈值交换，或 same-trigger 改善伴随护栏越界：不得 promotion；
- optional external baseline 两个工程轮失败：移除该候选；official single/joint 任一无法闭合则 C4 BLOCKED，
  记录最佳可用 historical/local identity `fallback_component_bundle_id`，不阻塞 E3 使用现有 predictor；
- failed 后停止非对称权重、阈值网格、换 backbone 和跨文档数据扩张；
- 保留错误剖析与当前 predictor，标 `status=failed|blocked` 供 E3 误差传播，不写成改进方法。

## Handoff

交付 C4 bundle 后进入 E3。E3 必须同时保留 A3/D3/C4 的 status；任何 failed/blocked 产物只能作为现实
系统或负结果输入，不能称为“前三章优化后的图”。

## GPU

4090 单卡。正式命令、`/data/TJK/ekg`、预期 `runs/stages/c4/...`、checkpoint 和 log 先展示。
先做最长文档显存 smoke；5090 每次单独授权。
