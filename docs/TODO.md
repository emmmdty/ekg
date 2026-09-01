# EKG 实时状态

> 更新于 **2026-09-01**。只记录当前事实、唯一活动任务和停止条件；实验数字以
> [`results/`](results/README.md) 为准，新会话先读 [`HANDOFF.md`](HANDOFF.md)。

## 当前结论

| 章 | 同协议对手 | 我们当前结果 | 结论 |
|---|---|---|---|
| Ch1 身份消解 | official joint 80.98 MUC | 底座四种子 79.14；机制三种子 79.47 | 两个机制周期均未成立 |
| **Ch2 关系抽取** | official joint 33.17 causal | 第一周期三种子 33.27，护栏未过 | **第二周期 active** |
| Ch3 事实性 | CLS .5458 / DMRoBERTa .5423 | evidence .5554 | 点值最高，配对 CI 含 0 |
| Ch4 下游代价 | gold/rewired/no-graph | .1802/.1185/.0811 MRR | 图依赖正控与构建损失成立 |

论文结构仍是三个方法章 + 一个系统评估章。公开论文数字可进入背景表看量级，但不能替代最终的
同协议比较。周四汇报稿见 [`reports/2026-09-03_阶段性报告.md`](reports/2026-09-03_阶段性报告.md)。

## 唯一活动阶段：A3 Ch2（4090 工作点待核；5090 prototype 已封存）

4090 当前不可达；作者已授权的 5090 临时单种子探索已完成。plain 在 smoke 后止损，dependency 完整
训练后只通过两个族的门、未过 causal 主锚，整案已封存。5090 模型 cache 也未闭合正式内容 pin，
结果只作 exploratory；不得追加 seed、扫描本方案超参或写入正式主表。具体数字只见权威结果档。

### 已完成

- 跨句错误剖析：主要差在 precision（.1998 vs .2904），跨句过发 2.6×、同句 2.0×；
- 逐位置诊断上限 causal 33.80，高于 33.17 主锚，三族护栏可同时满足；
- `PairExample.position`、六桶 `WorkPointController` 和训练侧逐 row NONE offset 已实现；
- 推理仍为朴素 argmax，candidate/evaluator/final-valid 规则不变；
- 本地 447 passed / 16 expected skips、ruff 0、CPU smoke 与 P1 local gate 全绿；
- 代码提交 `91d32d8` 已推送；4090 clean 同步；
- 位置工作点使用的 P1 r12 与 A3 r13 preflight 均 PASS；4090 两 epoch行为 smoke 已 PASS；50 epoch seed-13 正式
  流水线已在 GPU0 启动，最后一次成功 SSH 确认到 epoch 15，official scorer 尚未产生结果。
- GPU1 已完成三个不同的单种子 Stage-1 检索诊断；r1/r2/r3 均未过预设 recall 门，检索近似变体线
  止损，不跑 r4、不接 Stage 2。r1/r2 见权威结果档，r3 待 SSH 恢复后补 artifact hash 再入档。

### 当前可信身份

| 项 | 值 |
|---|---|
| P1 bundle | `runs/stages/P1/p1-v6-20260901-r13/` |
| P1 protocol SHA-256 | `00e0943d32db9b5a2453c25c6d8adf8c33e456f9bff042bd134c23ae20b3447a` |
| A3 preflight | `runs/stages/A3/a3-v6-position-workpoint-r13/preflight/` |
| A3 plan SHA-256 | `b587b21d7aa74437d7144ecad76d87f4fe2253f39966d48bb23108e914ec1eda` |
| 主锚 | official joint causal 33.17 |
| 护栏 | subevent ≥28.75；temporal ≥50.63 |
| 模型 | `/data/TJK/models/local/roberta-base/71be7419a60dcce0fc276654c8f9213b41f8def71a0c3465d7fed2352c961ea9` |
| 划分 | train 2,622 / internal-dev 291 / final-valid 710（本轮未访问） |

### 行为 smoke 结果与下一步

- 4090 GPU0、seed 13、2 epoch 正常完成；训练器 macro .3178 → .3328；
- 六桶最终 offset 范围 [−.536, +.328]，12 条轨迹均有限、无串桶或指数发散；
- causal 跨句桶需要提高正例门槛，方向符合跨句 2.6× 过发的诊断；final-valid 未访问；
- 这是训练器行为证据，不含 official predictions/evaluator，不能与 33.17 主锚直接比较。

1. 当前唯一远端主任务是等待/监测 seed-13 50 epoch 流水线，结束后核 official 三族指标与
   same/cross 错误表；SSH 失败不得推断进程死亡；
2. seed-13 同时满足 causal >33.17、subevent ≥28.75、temporal ≥50.63，才把该方案标记为单种子过线；
3. seed-13 未过门则封存工作点线；并行完成的 r1–r3 retriever Stage-1 均未达到放行门，不能直接
   接 cross-encoder，也不再堆第四个近似变体；
4. 在所有待比方案的单种子都过 baseline/护栏且用户再次明确允许前，**禁止**
   seeds 17/42 或任何多种子；空闲 GPU 只并行不同方案/任务。
5. 5090 dependency seed13 已完成 official internal-dev 评分并未过三条线；这版 prototype 已停止，
   不扫 support 数、温度或 dependency 权重。下一候选必须是不同机制，并先冻结可证伪验收门。

## 周四前并行交付

- 汇报：逐章公开背景表、本地同协议表、低分归因、未来三天任务；
- Ch2：至少取得六桶 controller 的有效/无效结论；
- Ch3：冻结下一周期为 evidence-conditioned + 标签原型/分层判别，不盲跑大模型；
- Ch1：冻结下一周期为 event-aware metric + 相同触发词 hard-negative 对比学习；
- Ch4：只整理已有图依赖正控、构建损失和误差类型代价，不新增长训练；
- 文档：以 [`README.md`](README.md) 为唯一导航，不做历史文件搬家。

## 停止条件

- offset 出现 NaN/Inf、2 epoch 即数量级爆炸或位置映射错：立刻停止，不启动 50 epoch；
- 无论 seed-13 是否过线，没有用户新的明确授权都不得补跑 seeds 17/42；
- 两个有效核心设计周期仍未过 promotion：该章方法止损，保留负结果与系统组件身份；
- final-valid 被用于选模型、阈值或结构：该结果只能标 exploratory；
- manifest/candidate/evaluator/hash 漂移：停止实验并回 P1；
- SSH 失败只表示连接失败，不推断远端任务死亡。

## 后续阶段

活动链仍为 `A3 → D3 → C4 → E3 → H2`。严格串行约束的是不可变 handoff；在不改变科研口径且
GPU 空闲时，可并行同阶段独立 seeds/arms。D3/C4/E3 的现有科学结果可用于汇报，但正式 phase bundle
仍需在各自阶段完成。
