# 公开论文可比性提升计划

> 决策于 **2026-09-30**。执行作者的方向：在**单 seed**约束下，优先提高论文的可比证据与外部对手覆盖，不把周报、失败机制重开或低价值的表格补行当作当前工作。本文定义执行顺序；实测数字仍只写入 `docs/results/`。

## 1. 目标与边界

目标不是把不同论文的数字强行排成名次，而是让每个可写的比较都能回答：

1. 是否与公开方法使用同一数据、split、候选/mention 全集、标注和 evaluator；
2. 若没有，差异是什么，是否已在原作者基准上验证过代码；
3. 单 seed 的结果究竟能证明“同协议下的描述性比较”，还是能证明“跨随机初始化仍成立”。

**决策 C0：保留单 seed。** 它允许运行一个冻结的外部 baseline 或一个新方法的探索周期；它**不**满足 `SPEC.md` QR-002 的三 seed 确认条件。因此所有新行必须标 `single seed / non-confirmatory`，不能仅凭 document bootstrap 把初始化随机性说成已确认。这个限制不降低同一冻结 unit 内的可比性，但限制论文的因果强度。

不做：重开 D4/C5 的已封存机制；用更大 backbone、阈值/epoch 扫描或 final-valid 选模救分；增加 MCPredictor、BART contrastive 等已核实不可运行的 Ch6 对手；把论文原始分数抄进本项目主表。

## 2. 三层比较契约（所有表格强制采用）

| 层 | 必须相同 / 必须记录 | 允许的论断 |
|---|---|---|
| **P · 原文参考** | 原论文的 dataset、split、candidate/mention universe、evaluator、输入、backbone 与表号 | 只作领域背景；**不**与本项目数字相减或排序 |
| **V · 原始基准保真度** | 在该方法自己的公开基准上，跑前冻结容差并复现发表数字 | FR-016(a) 表示代码路径已验证；不自动使它与本项目主表可比 |
| **U · 统一协议行** | 项目的 manifest、候选/mention universe、official scorer、标签映射、训练/selection/evaluation 隔离与推理输入逐项一致 | 与本项目行可做直接比较；若原始基准无法验证则标 FR-016(b)“透明适配”，只能比较**适配版本**，不得说胜过原论文方法 |

每个 U 行必须随产物登记以下七项：`paper/table`、`upstream revision/license/checkpoint`、`manifest/split`、`candidate universe`、`evaluator/label mapping`、`train-dev-evaluation selection`、`input/protocol deltas`。任一项缺失即不进主结果表，只进入可得性表。所有比较值必须由冻结 raw predictions 重算，不能引用日志里的摘要值。

### 2.1 E · 受限外部验证层（作者授权，2026-10-02）

作者授权的范围是：**MAVEN 仍是所有方法章的主表；仅增加一个已有公开标注的 benchmark，作为外部可迁移性验证。**
它不改 `SPEC.md`，不允许新人工/生成标注、final-valid、额外 seed、跨机搬 checkpoint 或已封存机制复活。

| 字段 | 冻结决定与依据 |
|---|---|
| Benchmark | **EventStoryLine (ESC) v0.9**，仅评估 causal-existence。官方仓库 revision `46edefee5e82e0917b823abe0a18bf8c7770f15c` 同址发布 v0.9 标注、evaluation format、baseline/evaluator，并以 CC BY 3.0 许可。原始 benchmark 论文是 [Caselli & Vossen (2017)](https://aclanthology.org/W17-2711/)；这不是新增标注。 |
| 科研价值 | ESC 的 news-topic 分布与 MAVEN 的 Wikipedia 文档不同，且公开 ECI 文献把最后两个 topic 留为 development、对其他 20 个 topic 作 5-fold cross-validation，报告 positive-class P/R/F1；它可检验一项未来的 causal-relation 机制是否只在 MAVEN 有效。它**不能**证明 MAVEN 的方向性 `CAUSE/PRECONDITION` 主表结论，也不能替代该表。见 [ICCL 的原文 §4.1](https://aclanthology.org/2024.emnlp-main.51.pdf) 与 [RichGCN 的 cross-topic 设定](https://aclanthology.org/2021.naacl-main.273.pdf)。 |
| E 的声称边界 | `E` 是独立 benchmark 的冻结 protocol 行，不是 `U`：只有同一 ESC source hash、topic split、候选全集和 scorer 的 E 行可以互比；不和 MAVEN U 行相减、排序或替门。每个正式 E 行仍标 `single-seed / non-confirmatory`。 |
| 已排除的捷径 | ICCL 原文确实声明 ESC v0.9、最后两 topic development、其余 topic 5-fold，但其公开仓库没有许可证、没有生成所需 `train.npy` 的闭环，且 `load_data.py` 对 document 而非 topic 作未绑定 `random.shuffle`。DICP 同样没有许可证；README 指向未发布的 `src/run.sh`，实际源码只有 Causal-TimeBank 的 `main_ctb.py` 且缺被 import 的文件。二者均只能作为 P 参考，不能作为 V 行。MAVEN-ERE 官方仓库是 GPL-3.0 且公布 ESC 预处理/命令，但它的 `main_other.py` 对 tokenized samples 直接 `KFold`，也不是本 E 层的 topic-disjoint protocol。 |
| 当前可行性 | **C-31b 的 R0 可行；C-32a 尚未通过。** 数据与许可来源已明确，CPU 静态审计即可开始；确切 event filter、candidate universe、fold membership、标签折叠与独立 scorer 仍必须从 source snapshot 实测生成。未完成前没有模型、分数或 GPU 任务。 |

因此这不是“再找一个能跑的数字”：先让公开 benchmark 的**数据、split、候选与 evaluator**闭合，再寻找没有被 A4/旧机制占据的新研究合同。若 C-32a 发现 source 版本或标准 protocol 无法同时唯一确定，就按【数据/协议】收口；不得以 ICCL/DICP/MAVEN-ERE 的相近但不同 runner 代替。

## 3. 一手研究结论与取舍

| 线 | 一手依据 | 决策与原因 |
|---|---|---|
| Ch5 共指 | [Global-Local Topic（EMNLP 2022）](https://aclanthology.org/2022.emnlp-main.454/) 是独立发表的 ECR 方法；其官方 EasyECR 仓库已有 MAVEN-ERE loader、配置与 predict 路径，但原始 KBP 2017 要 LDC 许可 | **优先运行。** 以最小透明补丁在冻结 291-document unit 上产生 clusters，再用项目冻结的 MAVEN evaluator 重算 MUC/B³/CEAFe/BLANC。它是 FR-016(b) 统一协议行，能实质补齐独立发表方法族，且不把本项目机制当对手 |
| Ch4 关系 | [LLMERE（COLING 2025）](https://aclanthology.org/2025.coling-main.500/) 直接研究 MAVEN-ERE 的 causal relation；项目静态核验发现已冻结恢复方案的 stop 需要读取 internal-dev target | **不运行，作者已取甲收口。** 它留作 FR-016(b) 可得性行：原文保真度仍不读封存 final-valid；本项目 U 层也无分数，因为 target-dependent stop 会造成 gold leakage。此项是命名协议障碍，不能评价 LLMERE 方法能力 |
| Ch3 事实性 | [MAVEN-FACT（Findings 2024）](https://aclanthology.org/2024.findings-emnlp.651/) 的官方代码和本项目已完成的 EFD 对照，均无法取得原论文 test split | **不新增 G-3 supporting-word 重跑。** C-28 已给出官方 EFD 的透明适配与 gold/predicted 归因；再跑 source-paper 的 supporting-word 只增加同一论文内部变体，不能补独立方法族或原始 test 可比性 |
| Ch6 应用 | SeDGPL 的原 CGEP-MAVEN 派生 split/candidates 未发布；本地重建协议还实测出 document shortcut 与 KGC 冷启动不兼容 | **不再扩充对手。** 新的 BART/MCPredictor 行不会消除协议缺口，反而增加不可解释的透明适配。保留三层对照、图依赖正控和构建误差分析，明确它是本地重建协议的应用证据 |
| 新 C5 方法 | R1 已为 shortcut-invariance 冻结数据、功效与 100 条 blind-review gate，但 C-22 仍须生成和独立人工盲审 | **保留但不抢占可比性队列。** 它可能提高方法贡献，却不能在完成质量门前提供任何可比较结果；通过后仍先是单 seed 探索，不能替代当前的外部 baseline 补齐 |
| Ch3 五维 bottleneck | 是项目 base head 的诊断，非独立公开方法或新机制 | **不执行。** 它最多解释 baseline 欠额，不能提高外部可比性，也不能推翻 oracle 已否定的 D4 残差机制 |

## 4. 固定执行顺序与预期交付

1. **C-29（已完成）· 比较登记冻结。** 本文与 `BASELINE_ROSTER.md` 为每章固定 P/V/U 三层、状态和禁止论断；不改任何分数。
2. **G-19 · EasyECR / Global-Local Topic（✅ 2026-10-02 收口）。** 先从 P1 的 2,622-document train manifest 用
   `sha256("g19-selection-v1:" + doc_id)` 的固定排序切出 291-document selection-dev，余下 2,331
   篇才可训练；selection-only 文件物理名固定为 `selection-valid.jsonl`，因为上游 MAVEN loader 仅据该
   `valid` 标记构建有标签 Event container；P1 internal-dev 的 291 篇只生成无 gold 的 test shape，绝不参与
   选档或阈值选择。再在
   gpu-4090 的独立环境完成 import + one-batch smoke（C-2b）；只作三项已登记的透明补丁：vendor
   `SelfAttentiveSpanExtractor`、移除 upstream test-predict 对 gold `event_id` 的错误依赖，以及把 upstream
   初始化**之后**硬编码的 seed 42 改为在建模**之前**读取显式的固定 seed 13；保留 upstream 和补丁 hash。
   EasyECR 还会把全局 Python temporary directory 写死到未创建的 `/home/nobody/code/tmp/`；G-19 runner 在导入
   Lightning 前将其进程内重定向到本次不可覆盖 run output 的 `temporary/`，仅修复运行路径，不改上游源码。
   上游 predict 另行新建未配置的 Lightning Trainer；runner 只在该调用期间切入本次 run output，令其默认
   `lightning_logs/` 也归档于该 run，退出即恢复工作目录。这同样不触及模型、数据、训练或推断计算。
   固定 seed 13 训练一次，用 selection-dev
   选档，预测冻结 evaluation unit，并用项目 official scorer 重算全部四个 coreference 指标。2,331 vs
   既有锚的 2,622 training documents 是必须披露的 U 层 input delta，故本行不作 superiority claim。
   任何路径/环境/ID/覆盖失败都停止，记录 FR-016(b) 不可运行障碍，不重写模型或改目标。正式运行的
   raw clusters、official export 与评分均完成；它在统一协议下是近乎全 singleton 的负向结果，完整数字、
   provenance 与禁止论断唯一见 `results/PHASE_R1.md` §25.28。不得以这一结果回调 threshold、重训或改 backbone。
3. **C-29.5 · AI 辅助科研流程审计与 G-20 执行就绪包（✅ 2026-10-02）。** 先从 G-19 的
   真实运行史追溯反复试错的边界，再核验一手 AI-for-science 与可复现研究工作流资料。交付
   `AI_RESEARCH_WORKFLOW_AUDIT.md`：AI 与人各自能决定什么、何时必须独立复核、如何把静态代码/数据/副作用
   契约和真实受限 smoke 连接起来。它必须为 G-20 列出冻结输入、禁止信息流、环境和磁盘副作用、命令、产物、
   预检、停止条件和独立结果审计者；在该包完整前，**不运行 G-20**。这项工作不产生分数、不读 final-valid、
   不重新选择方法或指标。审计确认旧 LLMERE prediction config 是已知无终止语义的 512-token 配置，因而不能直接使用。
4. **C-29.6 · LLMERE 恢复推理静态契约核验（❌ 2026-10-02 阻断）。** 只读审计实测 11,149 个 target 的第三行
   有 407 种值，固定 `Relevant reasoning information: none` 只覆盖 10,743；而逐条读 target 构造 stop string
   会把 internal-dev gold 引进 inference。故 C-3 的“第三行结尾 stop”当前不可执行，既不写 driver、也不跑 GPU。
   这是【协议】而非模型质量或算力障碍；不得用局部补行或宽松 prompt 绕开。
5. **G-20 · LLMERE-causal（✋ 作者 2026-10-02 取甲，不执行）。** C-29.6 证明 target-third-line stop 逐例读取
   internal-dev gold，固定 `none` 又选择性错误；作者选择保留 FR-016(b) 无可评分行并报告该命名协议障碍。
   不实现 first-line-only driver、不生成、不评分，也不把该未运行状态写成方法低分。
6. **C-30 · 表格和声称审计。** 从可用的 G-19 raw predictions 独立重算主表；为每一行输出 P/V/U 状态和七项登记，
   并明确 LLMERE 为“P 有 / V(b) / U 无分数”的可得性行。只有 U 层、同一章、同一 unit 的行可列 delta；P 层永不进排序。
7. **C-31b → C-32a · 外部验证协议闭合（当前）。** 在作者授权的唯一额外 benchmark 上，先将 ESC v0.9 的
   source revision、topic split、candidate universe、label folding 与 scorer materialize 为无分数 CPU preflight。
   不运行 ICCL/DICP/MAVEN external runner；它们各有已登记的 license/input/protocol 断点。C-32a PASS 只说明
   external validation 可以被诚实执行，**不**说明有新机制、也不解锁 GPU。
8. **C-32b 起 · 受约束自驱动研究回合。** C-32a 后才按
   [`AUTONOMOUS_RESEARCH_PROGRAM.md`](AUTONOMOUS_RESEARCH_PROGRAM.md) 的研究卡、准入合同、单 seed 执行和
   独立审计，寻找能够同时经 MAVEN 主表与 ESC E 层检验、且不属于封存家族的候选。任何数据/协议/代码/算力/授权阻断按类别停下，不用试错绕行。

## 5. 成功、失败与论文效果

成功不以任何 baseline 分数高低判定，而以：两条独立发表方法在各自冻结 unit 上有可复算的输出、所有协议差异可逐项追溯、每章主表能区分 P/V/U、所有单 seed 限制可见。

预期效果是把“自家方法 vs 自家消融”的负结果章，提升为“公开主锚 + 独立公开方法透明适配 + 机制消融/负控 + 失败归因”的可审查证据链。若外部方法较低，论文只能说“在本项目的透明适配协议下较低”；若较高，则如实抬高目标或记录本方法未达标。两种结果都增加可信度，不能把 baseline 当作可调的靶子。

## 6. 指标审查

- Ch5 使用官方 MUC/B³/CEAFe/BLANC 全套；MUC 保持主锚，但任一单指标不允许替代全套报告。
- Ch4 使用 official causal P/R/F1，subevent/temporal 留作护栏；LLMERE 只报告它实际覆盖的 causal，不伪造其他关系族数值。
- Ch3 继续使用五类 macro-F1 和逐类 F1；官方 EFD 的非加权 CE 与项目主锚的加权 CE 不相减。
- Ch6 继续使用 MRR/Hit@k，但只在消除 document shortcut 后的同轴行内解释相对差异；跨族 raw ranking 与原论文 CGEP-MAVEN 数字均不作 superiority claim。
- document-cluster bootstrap 描述 evaluation-unit 不确定性；单 seed 仍只代表一个训练随机性实现。

因此指标的可比性来自**口径对齐与声称边界**，不是来自把更多不同论文的数值放进一张表。
