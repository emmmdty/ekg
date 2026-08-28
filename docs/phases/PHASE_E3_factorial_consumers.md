# PHASE E3 — 同实例构建误差与消费者 factorial

> **BLOCKED BY C4 HANDOFF。** 必须同时读取 A3/D3/C4 的 immutable bundle/status。
> 历史三图事实见 [`../results/PHASE_E.md`](../results/PHASE_E.md)；旧 E2 不同语料消费者契约不得执行。

## Goal

在冻结的本地重建 CGEP-MAVEN queries 上量化 identity、relation、factuality 三类构建误差的边际与交互
代价，并检验消费者对图质量的敏感性是否随冻结/微调方式改变。正、零、负效应均可接受，前提是消费者
可信且同实例。

## Inputs

- P1 冻结的 ID namespace、query 生成器版本/来源 hash 和目标 schema；
- A3 relation、D3 factuality/evidence、C4 cluster bundles 及各自 status；若阶段 blocked，则只可读取其显式
  `fallback_component_bundle_id`；
- 4090 SeDGPL 权重、random/frequency、历史 paired-rank caches；
- MAVEN valid gold 仅作 factorial reference，不得冒充 predicted arm。

禁止：不同 queries/候选集间比较绝对分数；用删节点代替 factuality 属性；不同 backbone 下写“微调导致”；
丢弃某 arm 不可评分的样本后再比较；沿用 source/stored edge order。

## Tasks

### E3.0 重建并冻结不可变 evaluation unit

按公开 CGEP-MAVEN 任务定义和已记录生成器，冻结完整 query/candidate manifest、随机 seed、source/generator
hashes、candidate-ID digest 与 population counts。该轴明确标为“本地重建协议”，不能声称逐项复现论文
未公开的派生 split/candidates；当前 1,908 仅是预期规模，若重建校验导致变化，须在看 consumer 结果前冻结
并披露原因。

每个 query 固定 `instance_id/doc_id/anchor mention/gold mention/candidate mention IDs/label`。identity arm 只改变
mentions 如何聚合成 graph nodes，不改变 evaluation IDs、候选集或 gold label。无法映射的 arm fail-fast，
不得删题。

### E3.1 闭合三类真实输入接口

- identity：gold/pred mention-to-cluster，通过稳定 mention IDs 重建 node grouping；
- relation：gold/pred typed directed edges，保留原始概率与 source IDs；
- factuality：gold/pred/masked 五类概率与 evidence，以 node-attribute sidecar 或 `metadata` 序列化；
- 所有 arms 使用同一事件文本、candidate IDs、canonical edge order 和 scorer。

先做 20-query CPU fixture，断言 24 个基础条件的 ID 集完全一致、无重复/缺失。

### E3.2 预测有效性与图依赖正控

必含 random、frequency、BART/text-only 与 SeDGPL/fine-tuned graph。强 fine-tuned graph arm 必须有稳定 rank
输出，并在 MRR 上相对 BART/text-only 与 frequency 的 document-cluster paired 95% CI 下界均大于 0，
证明 predictive validity。CSProm-KG、SimKG、MCPredictor 可选；same-backbone frozen variant 是 factorial
consumer 因子，不要求胜过全部公开方法。

图依赖另设正控：至少一个消费者在预注册 gold/permuted 或 graph/no-graph 对照上出现超过自身噪声地板，
且预注册方向的 document-cluster paired 95% CI 不跨 0。frozen arm 可以图不敏感，这不是实现失败；只有
两个消费者都未通过正控，才收缩独立 consumer-sensitivity claim。

因果措辞使用同 backbone 控制：相同 graph serialization、encoder 与 scoring architecture，一档冻结 encoder
只训练/校准轻量 scoring head，一档允许 encoder fine-tune。若另加 in-context 模型，只作外部泛化，不能
替代同 backbone 控制。

随机消费者使用 matched seeds 13/17/42；每个 consumer/seed 在预注册的同一训练数据/训练图上只训练
一次，并在全部 12 个 quality arms 复用相同 checkpoint。quality 只改变 final-valid 输入图；不得为
gold/predicted/masked arm 分别重训。frozen-vs-fine-tuned 共享初始化、训练数据/训练图与预算，并使用相同
scoring architecture，只改变 encoder update 开关。

每个消费者先做小样本 graph/no-graph 与最长输入显存 smoke。一轮工程修复是有界诊断、补丁和同协议
smoke；两个消费者均在各自两轮后仍无正控信号，则收缩 Ch4，不把零敏感误写成实现必然失效。

### E3.3 全 factorial

最小设计：

- identity：gold / predicted；
- relation：gold / predicted；
- factuality：gold / predicted / masked；
- consumer：frozen / fine-tuned。

共 24 条基础条件，另保留历史 repaired/controlled perturbations 作归因副表。所有条件逐 query 保存 ranks，
训练数据、candidate manifest、模板序和 scorer 固定。

### E3.4 统计推断

- 公开主指标 MRR、Hit@1/3/10/20/50；strict MRR/strict correctness/unscorable 是本项目副指标；
- 以 document 为 cluster 做 paired bootstrap 至少 10,000 次，每次保留文档内全部 queries，报告 effect
  size、95% CI 与 p；
- 随机消费者在每次抽样中分别重算三个 matched-seed effect，再对 seed-level effect 取均值；
- 在看结果前预注册有限主 contrasts；同一确认性家族用 Holm 校正，其余比较标 `exploratory`；
- 报预注册的 identity/relation/factuality 主效应、交互和 consumer×quality；
- 每个消费者独立测噪声地板；小于地板的效应不作正面主张；
- `status=failed` 的上游 arm 仍可进入“现实系统”分析，但方法身份必须在表头标明。

### E3.5 叙事闭环

只允许三种结论：

1. 同 backbone frozen 比 fine-tuned 对质量更敏感：支持有限的微调依赖解释；
2. 两者敏感性相近：撤回消费者类型解释，保留误差代价排序；
3. 两者都未通过图依赖正控：收缩为错误传播副章，停止消费者依赖性因果解释。

不能从不同语料、不同 backbone 或不同 queries 的绝对分数推出消费者因果机制。

## Done when

- 冻结的本地重建 manifest 与 24 条基础条件 ID 集逐位一致；
- identity/relation/factuality 都读取真实 A3/D3/C4 bundles，未用 proxy 替代；
- fine-tuned graph arm 通过预测有效性门，至少一个消费者通过图依赖正控；
- factorial、逐 query ranks、document-cluster paired CI、Holm 校正、噪声地板和交互分析完整；
- 结论按证据选择成立/撤回/无法判断，不预设正结果；
- 结果追加到 `docs/results/PHASE_E.md` v6 小节；
- 本地三件套全绿，远端权重/log/bundles 可追溯。

## Stop conditions

- query/candidate/label 在任何 arm 漂移：立即停止，回 E3.0，不运行消费者；
- factuality 仍只能通过删节点进入：E3 BLOCKED，不把净化结果冒充属性消费；
- 任一 blocked phase 没有可校验 fallback component bundle：对应 predicted arm 不成立，E3 不得用 gold
  proxy 补位；独立 factorial 章 BLOCKED，但不追溯否定其他方法章；
- fine-tuned graph arm 两个工程轮后仍不优于 BART/text-only 与 frequency：预测有效性失败，Ch4 不作独立章；
- frozen 与 fine-tuned 都未通过图依赖正控：撤回“消费者类型导致差异”，收缩为错误传播副章；
- 仅 frozen 不敏感而 fine-tuned 通过正控：保留为 consumer×quality 的允许结果，不判 phase 失败；
- 只有不同 backbone 或不同数据可跑：只写描述性差异，不写“微调导致”；
- 不更换 ForecastQA/CRAB/叙事完形来救主结果，不扩大到 14B/70B/闭源模型。

## Handoff

E3 完成后进入 H2。H2 只补缺失的三种子/消融/复现检查，不重新设计方法或打开已止损路线。

## GPU

4090 为主；5090 每次逐次授权。先跑 20-query/最长输入 smoke，再估算完整 24 条件时间；命令、
`/data/TJK/ekg`、预期 `runs/stages/e3/...`、权重和 log 必须先展示。总预算超出 SPEC 时删非必要扩展，
不叠加任务。
