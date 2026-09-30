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

## 3. 一手研究结论与取舍

| 线 | 一手依据 | 决策与原因 |
|---|---|---|
| Ch5 共指 | [Global-Local Topic（EMNLP 2022）](https://aclanthology.org/2022.emnlp-main.454/) 是独立发表的 ECR 方法；其官方 EasyECR 仓库已有 MAVEN-ERE loader、配置与 predict 路径，但原始 KBP 2017 要 LDC 许可 | **优先运行。** 以最小透明补丁在冻结 291-document unit 上产生 clusters，再用项目冻结的 MAVEN evaluator 重算 MUC/B³/CEAFe/BLANC。它是 FR-016(b) 统一协议行，能实质补齐独立发表方法族，且不把本项目机制当对手 |
| Ch4 关系 | [LLMERE（COLING 2025）](https://aclanthology.org/2025.coling-main.500/) 直接研究 MAVEN-ERE 的 causal relation；项目已核到其推理输出的退化根因和全量、无选择性修复方案 | **第二优先运行。** 仅按已冻结的 stop/约束解码方案全量重生成、用官方 evaluator 在 frozen internal-dev 打分。它仍是 FR-016(b)：验证其原文数值须读取封存 final-valid，且不做该读取；但能补一个近期、直接任务的同协议透明适配行 |
| Ch3 事实性 | [MAVEN-FACT（Findings 2024）](https://aclanthology.org/2024.findings-emnlp.651/) 的官方代码和本项目已完成的 EFD 对照，均无法取得原论文 test split | **不新增 G-3 supporting-word 重跑。** C-28 已给出官方 EFD 的透明适配与 gold/predicted 归因；再跑 source-paper 的 supporting-word 只增加同一论文内部变体，不能补独立方法族或原始 test 可比性 |
| Ch6 应用 | SeDGPL 的原 CGEP-MAVEN 派生 split/candidates 未发布；本地重建协议还实测出 document shortcut 与 KGC 冷启动不兼容 | **不再扩充对手。** 新的 BART/MCPredictor 行不会消除协议缺口，反而增加不可解释的透明适配。保留三层对照、图依赖正控和构建误差分析，明确它是本地重建协议的应用证据 |
| 新 C5 方法 | R1 已为 shortcut-invariance 冻结数据、功效与 100 条 blind-review gate，但 C-22 仍须生成和独立人工盲审 | **保留但不抢占可比性队列。** 它可能提高方法贡献，却不能在完成质量门前提供任何可比较结果；通过后仍先是单 seed 探索，不能替代当前的外部 baseline 补齐 |
| Ch3 五维 bottleneck | 是项目 base head 的诊断，非独立公开方法或新机制 | **不执行。** 它最多解释 baseline 欠额，不能提高外部可比性，也不能推翻 oracle 已否定的 D4 残差机制 |

## 4. 固定执行顺序与预期交付

1. **C-29（已完成）· 比较登记冻结。** 本文与 `BASELINE_ROSTER.md` 为每章固定 P/V/U 三层、状态和禁止论断；不改任何分数。
2. **G-19 · EasyECR / Global-Local Topic。** 先从 P1 的 2,622-document train manifest 用
   `sha256("g19-selection-v1:" + doc_id)` 的固定排序切出 291-document selection-dev，余下 2,331
   篇才可训练；P1 internal-dev 的 291 篇只生成无 gold 的 test shape，绝不参与选档或阈值选择。再在
   gpu-4090 的独立环境完成 import + one-batch smoke（C-2b）；只作三项已登记的透明补丁：vendor
   `SelfAttentiveSpanExtractor`、移除 upstream test-predict 对 gold `event_id` 的错误依赖，以及把 upstream
   初始化**之后**硬编码的 seed 42 改为在建模**之前**读取显式的固定 seed 13；保留 upstream 和补丁 hash。
   固定 seed 13 训练一次，用 selection-dev
   选档，预测冻结 evaluation unit，并用项目 official scorer 重算全部四个 coreference 指标。2,331 vs
   既有锚的 2,622 training documents 是必须披露的 U 层 input delta，故本行不作 superiority claim。
   任何路径/环境/ID/覆盖失败都停止，记录 FR-016(b) 不可运行障碍，不重写模型或改目标。
3. **G-20 · LLMERE-causal。** 对全部冻结生成请求实施一套固定 stop 规则；第一阶段全量生成后若仍有任何不可解析第一行，按预登记启动第二阶段的全量 constrained decoding，绝不补跑单条。prompt 等价、覆盖、转换和 candidate universe 全过后，才用项目 official evaluator 产生 causal P/R/F1 行。结果无论高低均标 FR-016(b) 透明适配、single-seed。
4. **C-30 · 表格和声称审计。** 从 raw predictions 独立重算主表；为每一行输出 P/V/U 状态和七项登记。只有 U 层、同一章、同一 unit 的行可列 delta；P 层永不进排序。此步完成后才重新评估 C-22 是否值得成为“提高方法贡献”的下一单章任务。

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
