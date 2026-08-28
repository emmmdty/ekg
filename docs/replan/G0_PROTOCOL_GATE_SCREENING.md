# Gate G0：协议与资产静态筛查（2026-08-27）

## 静态结论（2026-08-27；已由下方 P1 执行更新取代）

**当时判定为 `global_protocol_status=CONDITIONAL`、`a3_entry_status=CONDITIONAL`；这不是当前门状态。**

主数据、跨数据集 doc-ID 桥、官方 scorer 语义、现有 710-doc 预测产物、4090 历史 checkpoint 和零新增
人工标注要求已经通过。全局协议尚缺可移植显式 manifests、adversarial scorer fixtures 和统一 bundle；
A3 入口尚缺 Ch2 三个必含 baseline 与最长输入 smoke。Ch1 选模、Ch3 baseline、Ch4 节点属性/consumer
均是对应阶段前置，不阻塞 A3。没有发现数据、算力或许可证层面的课题级硬阻塞。

本筛查只运行本地 CPU/只读文件检查、关键 CLI `--help`、4090 只读 SSH 和远端 CPU official scorer。
未调用 GPU，未访问需逐次授权的 5090，未训练，未改实验代码。

## P1 执行更新（2026-08-28）

静态 G0 之后已实际完成 P1.1–P1.6：六份显式 manifests/supports、portable processed manifests、固定
official source/evaluator、710-doc gold-self、四类手算 adversarial fixtures、strict rejection wrapper、stage
bundle reader/writer、三个 Ch2 10-doc schema adapters 与本地三件套均通过。因此当前覆盖静态结论为：

- `global_protocol_status=PASS`；
- `a3_entry_status=PASS`；
- P1 v2 bundle/status 为 PASS，权威 bundle 是 `p1-v6-20260828-r3`，可信 protocol SHA-256 为
  `e449e7313c2b0b9235b413f3292877f1a842e4ed85be4d7ba020d28601c4f84f`；允许进入 A3.0。

4090 隧道初始握手失败后，经有界 ControlMaster 重连恢复；历史 checkpoint 的 longest internal-dev 与
10-doc 真实 forward、回传 hash 和 strict schema 均通过，未访问 5090。权威实测与 bundle 见
[`../results/PHASE_P1.md`](../results/PHASE_P1.md)；下文保留的是
2026-08-27 静态筛查快照，不再代表当前未闭合项清单。

P1 反方复验后又补齐了外部可信 protocol hash、外部证据重哈希、完整 candidate/ledger 绑定、严格 remote
evidence 与伪 PASS/tamper 反例。A3 CPU materializer 已验证 train/internal-dev-only 数据与三条远端命令，
但未启动完整 GPU baseline；这一区分不把“入口可执行”误写成“baseline 已重跑”。

## 判定规则

- **PASS**：关键文件/接口存在，且已用当前工作树或固定 hash 产物机械复核；
- **CONDITIONAL**：缺口可由明确的至多两次定向修补关闭；
- **全局 BLOCKED**：主数据/标签/scorer、共享 ID/schema 或 bundle 完整性不可取得；
- **阶段入口 BLOCKED**：对应章必含 baseline/接口不能闭环；只阻塞该章并交付 `blocked` handoff；
- 历史文档写“已跑”但代码/命令/权重不能重放时，不得判 PASS。

## 全局协议门

| 项目 | 判定 | 已核证据 | 放行前缺口 |
|---|---|---|---|
| MAVEN-ERE / FACT 数据 | PASS | train/valid 记录数、SHA-256、ID 唯一性实算；ERE/FACT 两 split 的 ID 集合完全一致 | 修正 manifest 中旧绝对路径 |
| original valid 对齐 | PASS | 三份历史 prediction/edge dump 均覆盖 710 IDs、无重复、无缺失/多余 | 后续 bundle 加 source hash/status |
| official evaluator 语义 | CONDITIONAL | 固定 SHA-256；正确 mention-pair gold prediction 在 710 docs 上所有关系和共指 P/R/F1 均为 100 | 固化来源/工具路径；补空预测、反向边、coref merge/split 与重复/缺失 ID fixtures |
| train-internal-dev | CONDITIONAL | Ch2/Ch3 代码已内部划 dev；valid 未用于其 checkpoint 选择逻辑 | 保存显式 doc-ID manifest 与 support counts；Ch1 修复留到 C4 前 |
| baseline checkout | PHASE-LOCAL | 历史 checkpoint/result 在位；独立审查已列可复现候选 | 当前只闭合 Ch2 local pair/official single/official joint；其余留到对应 phase |
| 历史 checkpoint | PASS | 4090 上 Ch1/Ch2/Ch3/Ch4 权重及任务 heads 文件清单在位 | 阶段开始时再作 load smoke 与 hash bundle |
| 入口与 CPU import | PASS | 七个关键 CLI 的 `--help` 全部成功 | 新组件继续遵守 lazy import |
| 零新增人工标注 | PASS | 主线监督全部来自公开 gold；代码未发现人工打标/API gold 依赖 | 定性案例不得参与训练/选模/主指标 |
| 单卡资源 | PHASE-LOCAL | 既有 RoBERTa/SeDGPL 已在单卡跑通，权重在 4090 | A3 前只做 Ch2 checkpoint/最长输入 smoke；其余对应阶段再做 |
| stage bundle | CONDITIONAL | 指标、dump、权重分别存在 | 尚无统一四件套及坏 hash/重复/缺失 ID 拒绝测试 |

## 逐章准入

### G1 / Ch2：CONDITIONAL，最接近放行

已通过：公开 gold、official scorer、现有本地模型代码、4090 checkpoint、710-doc predictions/dump、
train-internal-dev 代码路径。

未通过：

1. internal-dev 只由 seed/数量运行时生成，没有显式 ID manifest；
2. official single/joint checkout 未持久化，无法与本地 pair 形成三个必含 baseline；RESIJ 不属准入条件；
3. 历史现役 checkpoint 与当前代码存在 head 兼容性债务，必须做 load smoke；
4. 当前方法的 subevent 回退尚未恢复，方法闸门不能只看 causal。

**放行条件**：修复 manifest；冻结 candidate-ID digest/population；持久化并同一 10-doc smoke local pair、
official single、official joint；预注册 anchor selection rule/matched seeds/document-cluster CI；checkpoint 最长输入 load；写好
stage bundle schema。完成前只做 CPU/小样本 smoke，不开完整训练。

### G2 / Ch3：CONDITIONAL，方法论前置闸门

已通过：MAVEN-FACT 数据与 ERE IDs 完全对齐；训练脚本有 train-internal-dev、best checkpoint、label/evidence
heads；4090 两档完整 checkpoint 与 prediction edge dump 在位。

固定 291-doc hash internal-dev 已核得 FACT mention supports：CT+ 6,835、CT- 129、PS+ 198、PS- 19、Uu 14；
PS-/Uu 仅覆盖 13/12 docs。该事实要求稀有类用 collapse + document-cluster 非劣护栏，不允许据此重抽 split。

未通过：

1. internal-dev manifest 未显式保存；
2. RoBERTa+CLS、DMRoBERTa 尚未在同协议重跑；DMBERT 仅是 DMRoBERTa 两轮修复失败后的替代；
3. 当前代码是共享 encoder + 并行 heads，尚未实现 evidence-conditioned 方法；
4. 没有逐 mention factuality/evidence prediction bundle，不能向 Ch4 交付节点属性。

**放行条件**：先闭合 RoBERTa+CLS 与 DMRoBERTa、冻结主锚和稀有类护栏；再做 evidence→label/联合软
耦合单种子 pilot。label→evidence/bidirectional 是二级机制。跨数据集
扩展不在放行条件中，也不能用于绕过同 split 主表。

### G3 / Ch1：CONDITIONAL，训练协议必须先修

已通过：gold mentions、official coreference scorer、lexical 与本地 RoBERTa 历史结果、完整 4090/本地
checkpoint、710-doc prediction、同-trigger 错误剖析。

未通过：

1. `train_coref_scorer.py` 对全部输入固定 epoch，缺 internal-dev、best checkpoint 和显式 manifest；
2. official single/joint checkout 未持久化；RESIJ 代码闭环仍 UNVERIFIED，只可选；
3. 现有 phase 的非对称代价方向已被错误剖析推翻；
4. 尚无 v6 规定的 context-discriminative 表示核心消融；校准聚类是二级机制。

**放行条件**：先修选模协议，再闭合至少三个 baseline；不得直接继续旧非对称权重/阈值扫描。

### G4 / Ch4：CONDITIONAL，高风险但非当前阻塞项

已通过：同一 710 docs、当前本地重建 1,908 queries 的 SeDGPL/canonical 三图与受控扰动结果存在；random/frequency/
SeDGPL registry、paired bootstrap、噪声地板和 4090 SeDGPL 权重在位。

未通过：

1. 本地重建 query IDs 只在运行时生成，没有来源/生成器/seed/candidate digest 完整 manifest；
2. `CgepNode` 不含 factuality/evidence metadata，现有 factuality 只通过删节点进入；
3. 没有逐 mention Ch3 prediction bundle；
4. 没有 BART/text-only 或 frozen consumer，也没有同 backbone frozen-vs-finetuned 控制；
5. Ch1/Ch2/Ch3 v6 真实产物尚未冻结。

**放行条件**：前三章只需先约定 ID namespace、query 生成器 hash 与接口，不要求现在实现 Ch4；E3 开始
前再冻结完整本地重建 query/candidate manifest、节点属性序列化、BART/text-only、SeDGPL/fine-tuned 和
matched frozen factor。预测有效性与图依赖正控分开；不同 backbone 不得支持“微调导致”措辞。

## G0 修复顺序与终止条件

严格串行，只关闭当前阶段所需缺口：

1. **P0a manifest 冻结（CPU）**：写出 ERE/FACT train/internal-dev/final-valid、supports 与 Ch4 ID namespace/
   query 生成器来源 hash；不生成完整 Ch4 query manifest。
2. **P0b scorer/tool 冻结（CPU）**：记录 evaluator hash/恢复来源，固化 gold-self 与 adversarial fixtures。
3. **P0c Ch2 baseline closure（CPU/小样本）**：持久化 local pair/official single/official joint 并同 schema smoke；
   RESIJ 可选。
4. **P0d Ch2 checkpoint/schema smoke（4090 小样本）**：只在前三项通过后申请完整 G1。
5. Ch3、Ch1、Ch4 的 phase-local 缺口在轮到该阶段时处理，不提前并行开发。

终止条件：

- 同一 baseline 两次定向修补后仍无法产生同 candidate/scorer 输出，降为背景并换已列候选；
- 无法形成 Ch2 三个必含 baseline 时，A3 入口保持 BLOCKED，写 `executed=false` handoff 后允许 D3 继续；
- manifest/scorer 任一 hash 漂移，所有下游 bundle 立即失效，先重建协议，不继续累加结果；
- 任何阶段发现 valid 被用于该次模型/阈值选择，结果只可标 exploratory，不能进入最终主表；
- 不因 Ch4 远期接口未实现而阻塞 Ch2，但 Ch4 不得在接口未闭合时声称端到端完成。

## 已执行命令类别

- 本地 JSONL 记录数、SHA-256、ID 唯一性/集合对齐；
- 历史 prediction/dump 的记录数、SHA-256、ID 完整性；
- 七个训练/评测入口的 CPU `--help` smoke；
- 4090 checkpoint/evaluator 文件清单与 hash；
- official evaluator 源码核验；
- gold event-level 关系展开为 mention-pair official prediction 后的 710-doc 恒等评分。

所有完整实验数字仍只见 [`../results/`](../results/README.md)。本报告只记录资格门事实，不取代结果档案。
