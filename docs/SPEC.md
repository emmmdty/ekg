# EKG 学位论文与工程总纲（v6，独立审查修订版）

> 生效日期：**2026-08-27**。这是当前研究设计与开发约束的单一权威。
> 当前动作与状态见 [`TODO.md`](TODO.md)，实验数字只认 [`results/`](results/README.md)，
> baseline 与消融见 [`EXPERIMENTS.md`](EXPERIMENTS.md)，阶段准入见
> [`phases/`](phases/README.md)，工程和服务器规则见
> [`ENGINEERING_NOTES.md`](ENGINEERING_NOTES.md) 与 [`GPU_RUNBOOK.md`](GPU_RUNBOOK.md)。
> 本文件不复制实验结果；历史方案只从 [`ARCHIVE_INDEX.md`](ARCHIVE_INDEX.md) 查取。

## 1. 研究目标与边界

课题研究 occurrence-level 事件图谱的自动构建与下游使用：

> **如何分别降低事件身份、事件关系和事件事实性错误，并在同一批实例上量化这些错误对不同图谱
> 消费者造成的边际与交互代价？**

论文采用“三个方法章 + 一个系统评估章”。统一性来自同一 `EventGraph` 契约和一条可执行的数据流，
不要求各章使用同一种语料。MAVEN-ERE 与 MAVEN-FACT 负责三章组件评测；MAVEN 文档交集与
CGEP-MAVEN 负责端到端桥接。

边界如下：

- 不新增人工标注，不使用人工重标、人工偏好或人工筛选样本作训练、选模或主指标；
- 可使用公开可取得或依协议合法用于研究的数据，不要求把受限原始语料随仓库再分发；
- 不依赖闭源模型、14B/70B 模型、多 GPU 或多智能体系统才能完成主线；
- 不把金融应用、专利、旧 TKG、生成式抽取/RL 或跨数据集扩展放入关键路径；
- 允许修复 baseline 的环境、路径、数据接口和 checkpoint 载入，但必须记录补丁与命令；
- 论文原分数若 split、输入前提或 scorer 不同，只能放背景表，不能与本地分数直接相减。

修订前独立可行性审查结论为 **CONDITIONAL**，见
[`replan/INDEPENDENT_THESIS_FEASIBILITY_REVIEW.md`](replan/INDEPENDENT_THESIS_FEASIBILITY_REVIEW.md)。
本轮反方裁决为 **ACCEPT WITH REQUIRED REVISIONS**；必要修订已写入本版总纲和 active phases。研究设计
因此可接受，但实验放行仍保持 `G0=CONDITIONAL`，直到 P1 机械验收通过。代码存在或单次高分不等于
章节成立。

## 2. 四章结构与可检验贡献

| 章 | 研究任务 | 冻结主数据 | 公认主指标 | 最小贡献 |
|---|---|---|---|---|
| Ch1 方法章 | 事件身份消解 | MAVEN-ERE，gold mentions | MUC F1；B³/CEAFe/BLANC 全报 | 上下文判别的 occurrence identity；聚类校准为二级机制 |
| Ch2 方法章 | causal/subevent 关系抽取 | MAVEN-ERE，组件表用 gold mentions | causal 正类 micro-F1；subevent P/R/F1 强制副报 | 非固定的关系族风险/梯度平衡与长上下文建模 |
| Ch3 方法章 | 事实性与证据联合检测 | MAVEN-FACT，gold mentions | 五类 macro-F1；evidence 宏平均与 pooled span F1 | evidence→label 或联合软耦合；label→evidence 为二级机制 |
| Ch4 系统评估章 | 构建错误的下游代价与消费者依赖性 | 同一 710 文档上的本地重建 CGEP-MAVEN 协议 | MRR、Hit@1/3/10/20/50；配对效应与 CI | 同实例 factorial 与消费者依赖性的成立边界 |

### 2.1 公开可比的操作定义

“公开可比”同时满足：

1. 同一主表使用同一 test manifest、输入前提、候选全集和 evaluator；
2. 多个代表方法由本项目实际运行，不能只抄不同 split 的论文数字；
3. split、数据 hash、baseline 修补、命令、checkpoint、seed 和结果可追溯；
4. 每个方法章在 baseline 运行前预注册强 roster 与 `primary_anchor_selection_rule`；默认规则是从合格强
   baseline 中选 internal-dev 主指标 mean 最高者，平分按预登记 roster 顺序裁决。锚点身份须在看到本章
   方法结果前冻结，不得按方法结果事后更换；
5. 随机性 `primary anchor` 与最终方法均用 matched seeds 13/17/42。章节 PASS 要求方法主指标均值同时
   高于该主锚和另一不同方法族的强统一重跑 baseline，且相对主锚的 document-cluster paired-bootstrap
   95% CI 下界大于 0，且至少 2/3 matched seeds 的差值为正；确定性下界可只运行一次；
6. Ch1/Ch2 主表至少含三个代表 baseline，Ch3 至少含两个强 baseline；“主表纳入数”与“必须胜过数”
   分开计算，majority、random、frequency、lexical 等简单下界不计作强对手；
7. 改善须落在该章主指标上，难例率、结构违反数、可重建率只能作诊断或副指标。

Ch4 也不豁免公开对照，但分开检验两件事：预测有效性要求强的 fine-tuned graph consumer 在同一本地
重建协议上可信地超过 BART/text-only 与 frequency 下界；图敏感性要求至少一个消费者通过预注册的
gold/permuted 或 graph/no-graph 正控。frozen arm 是消费者类型因子，不预设必须超过所有公开消费者，也
不预设必须对图敏感。consumer×quality 交互允许为正、零或负；若两个消费者都未通过图依赖正控，Ch4
收缩为错误传播副章，不作独立的消费者依赖性贡献。

### 2.2 章节最小方法与必要消融

**Ch1：语境判别身份消解。** 核心机制是对同 trigger、同类型的高混淆候选联合编码局部论元、句内
语境与跨句语境；校准聚类是可独立删除的二级机制。至少消融：去局部论元、去跨句语境、去校准聚类。
核心上下文表示过线而校准失败时，删除校准贡献表述并保留全局阈值，不否定整章。成功要求 MUC 上升，
且 B³、CEAFe、BLANC 和跨句 recall 满足阶段预注册的非劣界。非对称 loss 或阈值只能作为
baseline/消融，不能在错误方向已被推翻后继续充当主方法。

**Ch2：关系族均衡的长上下文抽取。** 在共享文档窗口表示上联合建模 causal 与 subevent。核心机制必须
是区别于 MAVEN-ERE official joint 固定任务权重的非固定方法，例如归一化 family risk、自适应梯度平衡
或等价的可证伪机制；固定权重网格、手调常数或仅按 checkpoint 选族不算贡献。类型/方向约束是二级
机制，失败时删除对应主张，不阻断核心 family balance。至少消融：句级替代长窗口、去关系族平衡、去
类型/方向约束。补齐 warmup、epoch、梯度累积或官方输入格式属于复现修正，不单独算方法贡献。
temporal 在 TIMEX 输入闭环前不进入主贡献表。

**Ch3：证据条件化事实性。** 核心机制是 evidence→label 或证据与标签的联合软耦合，必须区别于共享
编码器后的平行双头。公开 MAVEN-FACT 已包含先预测标签再定位证据的 label→evidence pipeline，因此该
方向只作 reproduction、二级机制或消融，不能单独主张创新；双向耦合失败也不否定已过线的
evidence→label 核心。至少消融：平行双头、去 evidence→label、去可选 label→evidence。现有 valid
分数与论文隐藏 test 分数不可直接比较；必须先在同一 valid 上重跑强 baseline。事实性净化的下游零
效应保留为 Ch4 证据，不得复活成方法卖点。

**Ch4：构建误差系统评估。** 不再提出第四个抽取算法。固定 queries、候选集、事件文本和 canonical
graph serialization，构造 identity、relation、factuality 三因子的 gold/predicted/masked 或受控档，
由可信的 fine-tuned 与 frozen 消费者读取。若要声称“微调导致绕过图”，必须使用同 backbone 的
frozen-vs-finetuned 控制；不同 backbone 只能支持“两个系统敏感性不同”。

## 3. 冻结评测协议

### 3.1 数据、选模与 final-valid 解封

- Ch1/Ch2：MAVEN-ERE train 用于训练并按显式 ID manifest 划出内部 dev；original valid 作为统一最终
  报数集。test 无 gold 且官方提交通道不可用，不进入主表。
- Ch3：MAVEN-FACT train 同样按显式 ID manifest 划内部 dev；public valid 作为统一最终报数集。
- P1 只冻结 Ch4 的共享 doc/event ID namespace、query 生成器版本/来源 hash 与目标 schema；完整
  query/candidate manifest 在 E3 开始前生成并冻结，不得阻塞 A3/D3/C4。
- Ch4 的完整轴称为“冻结的本地重建 CGEP-MAVEN 协议”；所有 arms 和消费者必须逐 query 对齐，不能
  各自丢弃难例，也不得声称它逐项复现公开论文未发布的候选构造。
- 从 v6 生效起，模型结构、超参、epoch 和阈值只能看 train-internal-dev。每章首次解封 final-valid 前
  必须写入 config/code/checkpoint/threshold hashes、主锚、种子和访问账本；解封后不得回调结构、超参或
  阈值。若解封后重调，该次及后续相关运行只能标 `exploratory`，不能进入确认性主表。
- baseline 的 final-valid 分数也不得先行解封用于方法设计。每章应在方法配置冻结后，用一个 sealed batch
  一并评估冻结 baselines、主锚和方法三种子；只有在没有返回任何指标且 hashes 完全一致的基础设施失败时
  才可原样重试，并在账本记录。任何看过部分指标后的重跑都不恢复确认性身份。
- 历史工作已经查看过 valid，论文须披露此前探索使用，并以统一 baseline 重跑、matched seeds、冻结
  访问账本降低偏差，不得宣称严格 blind test。
- 访问账本分开保存 `historical_final_access_disclosed=true`、逐次 `final_valid_access_ledger`（含 purpose）与
  v6 生效后的 `v6_confirmatory_eval_count`；gold-self 标 `protocol_fixture`，不得用确认性计数为 0 掩盖
  历史或协议访问。
- manifest 必须保存 doc/query IDs、生成脚本参数、源文件 SHA-256 和 manifest 自身 SHA-256；随机划分
  不得只保存 seed。

### 3.2 两层评测，防止上游错误污染方法结论

每个方法章都分两层：

1. **组件隔离层**：使用 gold upstream 输入，回答本章方法本身是否优于 baseline；这是 Ch1–Ch3 主表。
2. **端到端层**：使用冻结的上游预测产物，回答误差如何传播；组件层通过的产物可作 validated-method
   arm，未通过的产物只能作现实构建器/负结果 arm。

端到端结果不能反过来替代组件主指标；上游失败也不能被下游容错掩盖。某章未过线时，其预测仍可作为
“现有构建器”或负结果输入 Ch4，但必须带 `baseline/failed-gate` 身份，不能标作已验证方法产物。

### 3.3 统计、护栏与报数

- 单种子 pilot 只负责决定机制是否值得继续；不得写成最终胜出；
- 最终 Ch1–Ch3 的方法与随机主锚使用 matched seeds 13/17/42，报告 mean、sample std、每种子原值；
- 所有确认性 paired bootstrap 都以 document 为 cluster 重采样，并在一次抽样中保留该文档的全部
  mention/pair/query；Ch1–Ch3 每次抽样对三个 matched seeds 分别重算主指标，再对 seed-level delta 取均值；
  相对主锚至少 10,000 次，95% CI 下界大于 0 才算胜出；
- Ch4 预注册有限的主 contrasts，对同一确认性家族作 Holm 校正；未预注册的多重比较标 `exploratory`；
- 每章在看到方法结果前为 mandatory guardrails 预注册非劣 margin 和方向。稀有类支持过小时不用单点
  per-class F1 作硬门，改用“anchor 非零时不得崩为零”与稀有类合并的 document-cluster 非劣 CI；
- 对 higher-is-better 护栏，方法减主锚的 95% CI 下界必须 `>= -margin`；对 lower-is-better 护栏，95% CI
  上界必须 `<= margin`。要求“改善”的机制诊断则用预注册方向的 CI 严格越过 0，不得混用非劣判据；
- 多类别/关系族必须同时报告各族 P/R/F1，不允许宏平均掩盖 subevent 或稀有事实类别崩塌；
- 所有数字只写入对应 `docs/results/PHASE_*.md`；SPEC、TODO、phase 只链接，不复制。

## 4. 跨章数据契约

```text
gold mentions
    └─ Ch1: mention → occurrence cluster
          └─ Ch2: cluster/mention pairs → typed directed edges
                └─ Ch3: event node → factuality + evidence
                      └─ Ch4: fixed query + serialized graph → ranked successor candidates
```

冻结工程类型为 `EventNode → RelationEdge / EventGraph → CgepInstance → Prediction`。

- `EventNode` schema 零新增字段；cluster confidence、factuality、evidence 与阶段状态写入 `metadata`；
- Ch1 必须导出 mention-to-cluster 映射、doc IDs、confidence 和源 checkpoint/manifest hash；
- Ch2 必须导出原始概率、关系族、方向、端点 IDs 与 source mention/cluster IDs；
- Ch3 必须导出五类概率、预测标签、evidence spans 和 source mention/node IDs；
- Ch4 必须验证四章 doc/query ID 集合一致、无重复、无静默丢失，并使用同一候选集和模板序；
- factuality 在 Ch4 中必须作为节点属性被消费者读取；仅删节点不是事实性输入的替代实现；
- 任何映射失败、未知端点或缺失输出都 fail-fast，禁止填默认标签、空边或启用掩盖问题的 fallback。

## 5. 严格串行闸门

全局执行顺序固定为：

> **G0 协议冻结 → G1 Ch2 → G2 Ch3 → G3 Ch1 → G4 Ch4 → G5 总体验收**

论文写作顺序仍为 Ch1 → Ch2 → Ch3 → Ch4，不与实验顺序混淆。

### G0：协议与资产冻结（CPU/只读优先）

P1 分开维护 `global_protocol_status` 与 `a3_entry_status`。只有前者失败才阻塞全篇；A3 baseline closure
失败只阻塞 A3，必须交付 `blocked` handoff 后允许 D3 继续。第一轮 A3 GPU baseline 前的最小条件只有：

1. ERE/FACT train/internal-dev/final-valid manifests、source hashes、ID 集合和支持数冻结；
2. evaluator 持久化 source/hash，gold-self 与手算 adversarial fixtures（空预测、反向边、coref
   merge/split、重复/缺失 ID 拒绝）通过；
3. Ch2 candidate universe、labels、输入前提、candidate-ID digest 与 population counts 冻结；
4. local pair、official single、official joint 完成同 schema 10-doc smoke；RESIJ 不属 A3 必需项；
5. baseline roster、primary-anchor 选择规则、matched seeds、document-cluster CI/guardrail 规则预注册；
6. stage bundle 四件套通过外部可信 protocol hash、外部证据重哈希及坏 hash、重复/缺失/多余 ID、矛盾
   status fail-fast 测试；完整 candidate protocol 与 append-only access ledger 均被绑定；
7. 4090 完成 checkpoint/最长输入加载显存 smoke；远端命令须先展示；
8. 本地 pytest/ruff/CPU smoke 通过，且当前选模未访问 final-valid。

`global_protocol_status` 的 **PASS/CONDITIONAL/BLOCKED** 只由 1、2、6 及共享 ID/schema 完整性决定；
`a3_entry_status` 由 3、4、5、7、8 决定。Ch1/Ch3 baseline 与完整 Ch4 query/consumer 是对应阶段前置，
不是 P1 全局阻断。

### G1：Ch2 方法闸门

1. baseline closure：local pair、official single、official joint 同协议运行；RESIJ 仅在公开实现或忠实复现
   闭环时可选纳入；
2. anchor freeze：看到方法结果前冻结同 split `primary anchor`、guardrail margins 与 matched seeds；
3. core pilot：seed 13，最多两个 family-balance 核心设计周期；固定权重/网格不计有效机制；
4. promotion：pilot 主指标高于 seed-matched anchor 且 subevent 过预注册非劣界，才跑三种子；
5. final PASS：满足 §2.1 主锚 + 不同方法族胜出规则；type/direction 二级机制失败只删除对应 claim；
6. export：无论 pass/failed 都冻结身份明确的 Ch2 产物并 handoff。

**立即停止**：两个有效核心设计周期后仍不领先主锚或 subevent 过不了非劣界；停止无界扫参，保留长
上下文复现与关系族冲突诊断，降级为系统组件。A3 失败不阻塞 D3。

### G2：Ch3 方法闸门

1. baseline closure：RoBERTa+CLS 与 DMRoBERTa 在同一 split 重跑；DMBERT 仅在 DMRoBERTa 两轮工程
   修复仍不闭环时作预登记替代；
2. anchor freeze：看到方法结果前冻结同 split `primary anchor`、稀有类支持数/非劣规则与 matched seeds；
3. core pilot：比较 evidence→label/联合软耦合与平行双头，seed 13，最多两个核心设计周期；
4. promotion/final：按 §2.1 胜出且 evidence/稀有类过预注册护栏；label→evidence/bidirectional 失败只
   删除二级 claim；
5. export：无论 pass/failed 都冻结节点属性与 evidence 输出供 Ch4，不先做外部数据扩展。

**立即停止**：两个有效核心设计周期后同 split 不领先，或增量只来自多数类并越过护栏；本章降级为
系统组件，停止 FactBank/UW/MEANTIME 扩展，不复活净化路线。D3 失败不阻塞 C4。

### G3：Ch1 方法闸门

1. baseline closure：lexical/lemma、local pair、official single、official joint 同协议运行；RESIJ 仅在公开
   实现或忠实复现闭环时可选纳入；
2. anchor freeze：看到方法结果前冻结同 split `primary anchor`、多指标非劣 margin 与 matched seeds；
3. core pilot：上下文判别表示 seed 13，最多两个核心设计周期；校准聚类是二级机制；
4. promotion/final：按 §2.1 胜出并守住 B³/CEAFe/BLANC 与跨句 recall；校准失败时保留全局阈值并删除
   校准 claim；
5. export：无论 pass/failed 都冻结 mention-to-cluster 与 confidence 产物供端到端层。

**立即停止**：两个有效核心设计周期后仍不超过同 split 主锚，或增益只是越过护栏的 precision/recall
交换；停止换 backbone、非对称权重扫描和 ECB+ 换榜单，保留错误剖析并降级为系统组件。C4 失败不阻塞 E3。

### G4：Ch4 系统评估闸门

1. protocol freeze：E3 冻结本地重建 query/candidate manifest、生成器/seed/source hashes 和 candidate-ID digest；
2. bridge：同一 queries 真正读取 Ch1 clusters、Ch2 edges 和 Ch3 node attributes；
3. predictive validity：必含 random、frequency、BART/text-only、SeDGPL/fine-tuned graph；强 graph arm
   相对 BART/text-only 与 frequency 的 document-cluster paired 95% CI 下界均大于 0，frozen variant 仅作
   消费者因子；
4. graph dependence：至少一个消费者通过 gold/permuted 或 graph/no-graph 正控；
5. factorial/inference：固定输入、候选集、序列化和 scorer，按 document cluster 报预注册主效应、交互、
   Holm 校正、噪声地板与失败边界。

Ch4 的 quality arms 只改变评测时输入图。同一 consumer/seed checkpoint 必须跨全部 quality arms 复用，
不得为 gold/predicted/masked arm 分别重训；随机消费者使用 matched 13/17/42，并在每次 document-cluster
bootstrap 内先重算各 seed effect 再取均值。frozen-vs-fine-tuned 除 encoder update 开关外，初始化、训练
数据/训练图、scoring architecture 与预算必须一致。

**立即停止或收缩**：

- graph 正控在所有消费者上均失败且两次定向实现修补后仍失败：不作消费者依赖性独立贡献，收缩为
  错误传播副章；
- frozen 不敏感但 fine-tuned 通过正控：保留其为允许的 consumer×quality 零/差异结果，不判实现失败；
- 只有不同 backbone 对照：不得使用“微调导致”措辞；
- Ch1–Ch3 任一输出缺失或 ID 不对齐：禁止用 gold proxy 冒充真实端到端闭环。

### G5：总体验收

必须同时满足：三方法章各自有统一协议主表、超过多个 baseline、三种子和机制消融；Ch4 消费者可信、
同实例 factorial 与统计完整；所有负结果和降级均保留；代码、配置、数据 manifest、命令、checkpoint
位置和结果文档可从论文表格反查。

若一个方法章 `failed|blocked`，可由作者/导师明确改纲为“两方法章 + 一系统评估章”；若两个方法章
`failed|blocked`，v6 主线 NO-GO，必须另行重规划，不能在 H2 内把一个方法章包装成“两方法章”版本。任何阶段 pass/failed/blocked
都必须交付 handoff；局部失败不会自动阻塞后续方法阶段或系统评估，但会降低对应产物的证据身份。

`blocked` 阶段应记录最佳可用 historical/local `fallback_component_bundle_id`；若没有则显式为 `null`。
这不阻塞后续方法章，但 E3 不得用 gold proxy 补 predicted arm；缺少任一可校验 component 时只阻塞 Ch4
独立 factorial，不反向否定其他已成立方法章。

## 6. 防止错误累计

每个阶段必须交付一个不可变的 stage bundle：

- `protocol.json`：数据/manifest/evaluator/config/代码 commit 的 hashes；调用方必须从 bundle 外传入可信
  `protocol.json` SHA-256，reader 重新散列所有本地外部证据，不允许内部自证；
- `predictions.*`：逐实例预测与稳定 ID；
- `metrics.json`：scorer 原始输出，不由文档手抄重建；
- `status.json`：`pass | conditional | failed | blocked`、`global_protocol_status`、本阶段/下一阶段入口状态、
  `primary_anchor_selection_rule`、已解析时的 `primary_anchor`、`historical_final_access_disclosed`、
  `final_valid_access_ledger`、`v6_confirmatory_eval_count`、`exploratory`、失败原因和可供下游使用的身份；
- 对应 `docs/results/PHASE_*.md`：命令、机器、checkpoint 位置与诚实结论。

下游读取 bundle 前必须验证 hashes、ID 集合、重复数、缺失数和 schema。校验失败就停止，不允许继续跑
并在最后解释。修复后的 bundle 使用新版本号，不能覆盖产生论文结果的旧 bundle。

工程修复轮定义为“一次有界诊断 → 补丁 → 同协议 smoke”，同一 baseline 最多两轮；失败只移除该候选，
不否定任务。机制轮只在实现、单测与协议检查均通过后计数，每个**核心机制**最多两个设计周期；二级机制
另有最多“一次实现 + 一次定向修订”的独立预算；失败时删除 claim，不消耗或重置核心机制预算，也不
阻断核心 promotion。下列动作不计作新机制，也不能重置预算：

- 环境、路径、checkpoint 载入和字段名修复；
- 为忠实复现补齐论文明确给出的预处理；
- 修复共享协议中会改变 candidate population、gold 标签或 scorer 定义的 bug：不计机制轮，但必须使全部
  受影响 bundle 失效、升协议版本并退回 P1，不能伪装成普通 baseline 适配。

两轮后仍失败时不得开始第三轮；将 baseline 降为背景并换一个已列候选。主方法失败时不换指标、
不换 final split、不删难例、不扩大模型来绕过停止条件。

## 7. 工程不变量

- 代码按功能域命名，包/函数名不得含 `ch1/ch2/ch3`；新组件走 registry + lazy import；
- `EventNode` 零新增字段；扩展只用 `metadata`；`tests/core/test_propagation.py` 是测试锁；
- CPU core 不依赖 torch；GPU 组件必须支持 CPU 缓存回放；
- 不添加掩盖错误的 fallback 或默认值，输入不完整时 fail-fast；
- 现有结果数字下降就如实记录；ssh/工具失败不能写成远端进程或科研结论；
- checkpoint 训在哪就留在哪，位置和 hash 写入结果文档；跨机搬运必须先问作者；
- 提交和推送只在作者明确要求时执行。

代码域：`ekg.nodes`（身份）、`ekg.relations`（关系）、`ekg.factuality`（事实性）、
`ekg.succession`（CGEP 消费者），共享 `ekg.core.schema/io/eval/registry`。

## 8. 资源与执行规则

- 本地 WSL：文档、实现、lint、单测、CPU scorer、manifest/hash 和缓存回放；禁止本地 GPU 训练/推理；
- `gpu-4090`：主 GPU，单卡训练与推理；正式运行前先展示准确命令、工作目录和预期产物；
- `gpu-5090`：备用 GPU，每次使用均须作者明确授权；
- 服务器只用 `.venv/bin/python`，禁止 `uv run`/`uv sync`；不挤占他人任务；
- 规划总量为 95–180 单 GPU 小时，严格串行；任何超出预算的新增任务必须先替换而非叠加；
- 远端长任务使用 `setsid nohup`、`python -u` 和独立日志；判活遵守三态 ALIVE/GONE/SSH 失败。

主线所需监督全部来自公开 gold。LLM 可作不参与标注的推理 baseline，但主线不能依赖人工或闭源 API
生成新 gold。人工阅读仅允许做不参与训练/选模/主指标的少量定性案例分析。

## 9. 验证与文档优先级

改代码后必须运行：

```bash
uv run pytest
uv run ruff check src tests scripts
uv run ekg-smoke
```

文档冲突优先级：

1. `docs/results/PHASE_*.md`：已经发生的实验事实；
2. 本 SPEC：当前研究和工程约束；
3. 当前 active phase：本阶段操作步骤与停止条件；
4. TODO：实时位置；
5. EXPERIMENTS：候选 baseline 与实验矩阵；
6. replan/旧 phase/归档：证据与历史，不得覆盖当前指令。

任何新 phase 开始前必须先确认 SPEC、active phase 和结果单一事实源无冲突。若冲突，先修文档再开跑。
