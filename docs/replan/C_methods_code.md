# 事件图谱/事理图谱硕士论文：LLM 时代的方法范式、开源实现与 RTX 5090 单卡可行性证据报告

> **核验日期：2026-08-25。**  
> 本报告只把“同一数据版本、同一 split、同一 evaluator、同一指标定义”视为严格可比。只要其中一项不一致，就标为**不可比**，不计算提升值。尤其是 MAVEN-ERE：官方 hidden-test、Chen/LLMERE 的 train 8:2 + original-valid-as-test、LLM 抽样评测、因果-only 重划分等实际上是不同实验轴，不能混成一张排行榜。TextEE 同样需要区分完整五折/五随机划分结果与专门抽取的 250-document LLM 评测。citeturn15view0turn21view0turn22view1

## 方法范式总览

2024–2026 年事件类研究中，真正发生的变化不是“RoBERTa 被 LLM 全面替代”，而是形成了几条彼此非常不同的范式。**direct prompting、参数高效监督微调、LLM 作为辅助器、RAG、代码生成、agent 协作必须分开讨论**；把它们统一写成“LLM-based method”会掩盖最关键的实验事实。

| 范式 | 2024–2026 代表正式论文 | 方法实质 | 对事件图谱论文的意义 |
|---|---|---|---|
| Schema-conditioned instruction tuning / unified IE | **IEPile**, ACL 2024 Short, `2024.acl-short.13`; **ADELIE**, EMNLP 2024, `2024.emnlp-main.419` | 把多 IE 数据集统一成 schema-conditioned instruction/SFT 数据；ADELIE进一步做 IE alignment | 适合把 ED/EAE/RE 等统一为生成任务，但“统一”本身不保证超越专用监督模型。IEPile 汇集 33 个既有 IE 数据集、约 0.32B tokens。citeturn24search7turn23search1 |
| Code-style IE | **KnowCoder**, ACL 2024, `2024.acl-long.475`; **KnowCoder-X**, Findings ACL 2025, `2025.findings-acl.748` | 将 schema 写成 Python class/type，模型生成结构化代码而非自然语言 | 比普通自由生成更接近 schema-constrained generation；KnowCoder-X 把这一范式扩展到多语言、大规模 benchmark。citeturn23search0turn24search1 |
| EE 统一实验基础设施 | **TextEE**, Findings ACL 2024, `2024.findings-acl.760` | 统一 16 个 EE 数据集、标准化 preprocessing/splits/evaluator，并重跑大量经典 EE 模型与 LLM | **非常适合作为论文 ED/EAE 主实验底座**，因为它专门解决“不同论文 preprocessing 导致指标不可比”的问题。citeturn14search1turn15view0 |
| Retrieval / schema retrieval | **ASEE**, Findings EMNLP 2025, `2025.findings-emnlp.419` | schema paraphrasing + schema retrieval augmented generation，并建立 MD-SEE | 属于 retrieval-augmented EE，而不是单纯 few-shot prompting。citeturn24search0 |
| Supervised LoRA + rationale | **LLMERE**, COLING 2025, `2025.coling-main.500` | 对 Llama-2/Llama-3 做 LoRA；利用 relation rationale 进行 ERE | 是目前“监督 LoRA 在 MAVEN-ERE 某一明确重划分轴上超过强分类 baseline”的重要正证据。citeturn15view3turn17view3 |
| LLM 生成信息 + SLM 判别 | **SECURE**, ACL 2024, `2024.acl-long.164` | GPT-4 生成 event summary，任务专用小模型学习 summary + 原文联合表示 | 是“**LLM 辅助器有效，但 direct GPT-4 不有效**”最清楚的反直觉实例之一。citeturn14search0turn21view4 |
| Compression / selective context + extraction | **TacoERE** | 压缩与 cluster-aware context selection 后再做关系抽取 | 属于 hybrid/context engineering；不能仅因论文使用 GPT 系列实验就把所有配置称为 LLM 方法。citeturn15view2turn17view2 |
| 真 multi-agent relation reasoning | **MMD-ERE**, COLING 2025, `2025.coling-main.460` | 多 agent 分组讨论、debate/audience 式协作解决 ERE | 是 true multi-agent，但任务是 ERE，不是完整 event-graph generation。 |
| 真 multi-agent causal graph reasoning | **CGEL**, ACL 2025, `2025.acl-long.1269`, arXiv:2506.06910 | temporal/discourse/precondition/commonsense 等专家 agent 独立判断、通信，再由 judge 汇总 | 真正符合“多个 agent 协作”，而不是多 prompt。citeturn26search0turn27view0 |
| Cascade graph generation | **CALLMSAE**, NAACL 2025, `2025.naacl-long.112` | LLM 摘要/显著事件识别 → iterative code refinement → salient event graph | 是多阶段 cascade，**不是 multi-agent**。citeturn26search1turn27view1 |
| Event-KG + RAG | **EventRAG**, ACL 2025, `2025.acl-long.830` | EE → semantic node merging → relation expansion → event KG → iterative retrieval/inference | 是 pipeline/RAG；论文主要用下游 RAG QA 证明价值，而不是在 gold event-graph extraction benchmark 上竞争。citeturn26search9turn27view2 |
| Graph-assisted prompting | **TAG-EQA**, *SEM 2025, `2025.starsem-1.24` | zero/few/CoT × text/graph/text+graph 多种 prompting configuration | **单模型多 prompt，不是 multi-agent**；本质是 event/causal graph 辅助 QA。citeturn26search7turn27view3 |
| Event-centric agent memory | **CompassMem**, Findings ACL 2026, `2026.findings-acl.1123` | 用 event-centric graph 组织 agent memory 以支持长程 reasoning | 图是 agent memory 的组织结构，不等同于传统监督事件图谱抽取 benchmark。citeturn13search3 |
| 轻量 event-relation reasoning | **UERLens**, ACL 2026 Short, `2026.acl-short.38` | 挖掘 event relation 内部特征并结合轻量分类器 | 说明 2026 年趋势并非全走“大模型端到端生成”，轻量判别器仍然活跃。citeturn13search8 |
| Commonsense-enhanced joint EE/relation | **CausalSense**, LREC 2026, `2026.lrec-1.604` | commonsense/LLM 信息增强联合事件与关系分类 | 属于 knowledge-enhanced/hybrid，而非 direct LLM replacement。citeturn13search1 |

有两个分类上的重要纠偏。

第一，**InstructUIE 不应计入“2024–2026 正式发表方法”数量**。公开记录对应 arXiv:2304.08085/CoRR，它非常重要，是后续 instruction-based unified IE 的前驱，但本次检索未确认 2024–2026 ACL/EMNLP/NAACL/COLING 等正式 proceedings 版本；因此只能放在生态背景中。其公开实现提供 Flan-T5 类训练脚本与 checkpoint，但“代码公开”与“正式发表”是两个维度。citeturn25academia30turn25search4turn25search3

第二，2024–2026 的 evidence 并不支持“事件任务进入 LLM 后，端到端生成取代专用模型”的简单叙述。相反，更稳定的路线是：**结构约束 + retrieval/context selection + PEFT + 小模型判别/验证 + 官方 evaluator**。TextEE、LLMERE、SECURE 和 CGEL 的结果共同支持这一判断。citeturn21view1turn17view3turn17view1turn27view0

## 严格可比证据：direct prompting、LoRA/SFT 与 hybrid 对小模型

### Event detection 与 argument extraction

目前最干净的直接比较来自 TextEE。它不是从不同论文抄数，而是在统一 preprocessing/evaluator 下重跑经典模型和 LLM，并为 LLM 评测从各数据集抽取固定规模样本。TextEE 明确定义：ED 中 **TI** 要求 trigger span/offset 正确，**TC** 进一步要求 event type 正确；EAE 的 **AI** 要求 argument span 与 event type 正确，**AC** 再要求 role type 正确；AI+/AC+ 进一步把 argument 绑定到具体 trigger。citeturn21view0

| 任务与证据 | 论文 / ID / 表 | split 与 evaluator | 方法 | 主指标 | 严格结论 |
|---|---|---|---|---|---|
| ED | **TextEE: Benchmark, Reevaluation, Reflections**, `2024.findings-acl.760`, **Table 6** | 每数据集抽取 250 docs 的统一 LLM evaluation subset；TextEE evaluator；表内同口径 | OneIE | TI 73.5 / TC 69.5 | 基准 |
| 同上 | 同一 Table 6 | **完全相同** | TagPrime-C | 72.5 / 69.5 | 基准 |
| 同上 | 同一 Table 6 | **完全相同** | Llama-2-13B, 2-shot | 23.5 / 9.3 | direct prompting 显著未达到监督模型 |
| 同上 | 同一 Table 6 | **完全相同** | Llama-2-70B, 6-shot | 32.2 / 12.4 | 增大模型与 demonstrations 仍未超过 |
| 同上 | 同一 Table 6 | **完全相同** | Mixtral, 64-shot | 37.5 / 14.6 | 未超过 |
| 同上 | 同一 Table 6 | **完全相同** | GPT-3.5, 16-shot | 35.2 / 12.3 | 闭源 API direct prompt 也未超过 | 

以上数字均来自同一表、同一抽样 protocol，因此可直接比较；TextEE 作者也明确指出 ED 上 LLM 与 task-specific baselines 仍有很大差距。citeturn19view0turn21view1

EAE 的证据甚至更一致：

| 论文 / ID / 表 | 方法 | AI | AC | AI+ | AC+ |
|---|---:|---:|---:|---:|---:|
| TextEE `2024.findings-acl.760`, Table 7 | TagPrime-CR | 73.3 | 69.5 | 71.9 | 68.1 |
| 同表 | PAIE | 72.0 | 68.9 | 71.3 | 68.1 |
| 同表 | GPT-3.5, 8-shot | 34.9 | 26.9 | 31.8 | 24.7 |
| 同表 | Mixtral, 32-shot | 35.1 | 29.2 | 32.0 | 26.5 |
| 同表 | Zephyr, 8-shot | 29.7 | 25.2 | 27.7 | 23.5 |
| 同表 | Llama-2-70B, 4-shot | 30.1 | 23.6 | 28.3 | 22.3 |

这些数字也是统一的 250-doc LLM evaluation setting，因此构成对“few-shot LLM 已经超过 fully trained ED/EAE model”的**直接反证**。citeturn19view0turn21view1

但这里存在一个很重要的禁止比较项：TextEE **Table 5 的完整五划分 EAE 结果不能和 Table 7 的 250-doc LLM 抽样结果计算差值**。它们用途不同；论文同时指出 ACE05/RichERE 等数据访问与 preprocessing 差异能够使结果发生数个 F1 点的变化，所以从旧论文排行榜直接拼数字尤其危险。citeturn17view0turn15view0

**因此 ED/EAE 的判断是：**

**Direct zero/few-shot：否。** 在目前最严格的 TextEE 同口径证据中，甚至 70B/闭源 GPT-3.5 都远未超过 OneIE、TagPrime、PAIE 等 fully trained models。citeturn19view0turn21view1

**Supervised LoRA/SFT：本报告没有找到足以在 TextEE 同一公开主轴上证明“普遍超过最佳 fully trained ED/EAE baseline”的数字证据。** IEPile、ADELIE、KnowCoder、ASEE 等确实证明 instruction/schema/code/RAG 范式有效，但它们的数据组合、训练 corpus、zero-shot/generalization 设定与 TextEE 专用监督主轴并不天然一致；因此不能拿这些论文的 headline numbers 与 TextEE Table 5/6/7 直接做差。citeturn24search7turn23search0turn23search1turn24search0

### Event relations：temporal / causal / subevent

这里最重要的事实是：**MAVEN-ERE 看起来像“同一个 benchmark”，实际上至少存在数条互不对齐的实验轴。**

Wei et al., **Are LLMs Good Annotators for Discourse-level Event Relation Extraction?**, Findings EMNLP 2024, `2024.findings-emnlp.1`，使用完整 **official MAVEN-ERE test，857 documents**，按 Wang et al. 原官方 evaluator 与单独训练的 RoBERTa-base relation classifiers 对比。其 Table 2 是少数真正能回答“direct LLM vs fully trained RoBERTa”的严格证据。citeturn2search0turn5view1turn6view1

| 方法 | Prompt/训练类型 | Temporal F1 | Causal F1 | Subevent F1 | Overall F1 | split / evaluator |
|---|---|---:|---:|---:|---:|---|
| RoBERTa-base | fully supervised classifier | 55.8 | 31.6 | 27.2 | 51.6 | MAVEN-ERE official test, 857 docs, official evaluator |
| GPT-3.5 whole-document | direct closed API | 7.2 | 2.8 | 1.6 | 19.3 | 同上 |
| GPT-3.5 10-shot | few-shot closed API | 12.3 | 5.3 | 2.1 | 20.4 | 同上 |
| Llama-2 whole-document | direct open LLM | 5.2 | 4.5 | 4.4 | 18.9 | 同上 |

Table 2 还同时报告 coreference；例如 RoBERTa baseline 的 MUC/B³/CEAF\(_e\)/BLANC 为 81.7/98.1/97.8/89.7，而 GPT-3.5 whole-document 为 23.2/92.5/90.1/56.9。这里最值得注意的是 B³/CEAF 单项可能看似很高，但这并不意味着整体 coreference 好，因为 event clustering 极易受 singleton/cluster structure 影响，论文因此使用完整的一组 coreference metrics。citeturn5view1

同一论文还做了 **Llama-2-7B SFT + 4-bit quantization + LoRA**。Figure 3 的结论是：随着训练数据增加，监督 SFT 大幅优于 direct prompting，但仍没有稳定超过 RoBERTa，并且需要更多训练数据；论文报告 200 docs、3 epochs 的 LLM 微调约需 72 小时，而 RoBERTa 训练约 1 小时。由于这是 **Figure 3 而非带精确数字的表格**，按本报告的证据规则不抄图估算 F1，只把它作为“监督 LoRA 仍未证明全面胜出”的定性证据。其 Appendix A 明确使用 Llama-2-7B-chat-hf、3 epochs、4-bit、LoRA rank 64、dropout 0.1、learning rate \(2\times10^{-4}\)，但**没有声明具体 GPU 型号**。citeturn6view1turn7view3

这构成非常强的反证：**“用了 LoRA”并不自动意味着比 RoBERTa 强。**

另一方面，LLMERE 给出了相反方向的正证据。**Large Language Model-Based Event Relation Extraction with Rationales**, COLING 2025, `2025.coling-main.500`, Table 2：

| 方法 | Temporal F1 | Causal F1 | Subevent F1 | Coref avg F1 | Overall F1 |
|---|---:|---:|---:|---:|---:|
| ProtoERE | 53.8 | 31.8 | 27.9 | 89.8 | 50.8 |
| LLMERE Llama-2-chat LoRA | — | — | — | — | 51.1 |
| LLMERE Llama-2-base LoRA | — | — | — | — | 51.9 |
| LLMERE Llama-3-instruct LoRA | — | — | — | — | 51.7 |
| **LLMERE Llama-3-base LoRA** | **54.7** | **36.0** | **28.2** | **90.9** | **52.5** |
| Doc-SFT Llama-2-7B-base | — | — | — | — | 39.4 |

LLMERE 对 temporal/causal/subevent 使用 micro P/R/F1，coreference 使用 MUC、B³、CEAFe、BLANC 的平均 F1。表内 LLMERE 与 ProtoERE 因而可以比较，并给出了**监督 LoRA 超过该表 fully trained classification baselines 的正证据**。citeturn17view3turn22view2

但是它**绝不能与上面的 Wei official-test 51.6 做数值差**。原因不是模型，而是 split：LLMERE Appendix C 明确指出官方 test 不可访问，所以跟随 Chen et al. 的设置，把原 MAVEN-ERE train 做 **8:2 train/validation**，再把原 original validation 当作新的 test。citeturn22view1

因此关系抽取的准确结论不是“LoRA 赢了”或“LoRA 输了”，而是：

**Direct prompting：有严格负证据。**

**Supervised LoRA：混合证据。** Wei 的 official-test 轴没有证明 Llama-2-7B LoRA 超过 RoBERTa；LLMERE 的另一个公开重划分轴则证明 rationale-aware LoRA 可以超过该轴上 ProtoERE 等强分类器。两者**不可跨轴做差**。citeturn5view1turn17view3turn22view1

同时，MAVEN-ERE 已经不是“数据论文作者自己重跑旧 baseline、没有别人竞争”的状态。2024–2025 年已有 Wei、LLMERE、TacoERE 等不同方法论文使用该生态；问题恰恰变成了**研究团队很多，但 split/evaluator 不够统一**。TacoERE 例如在 subevent extraction 表中报告 MAVEN-ERE RoBERTa F1 27.5、SIEF 28.7、TacoERE(PLMs) 30.6，但这一 subevent-specific setup 不应和 Wei/LLMERE 的 joint overall F1 混排。citeturn17view2

### Event coreference

事件共指目前最强的“LLM 正证据”其实不是 direct prompting，而是 **LLM + SLM hybrid**。

SECURE，**Synergetic Event Understanding: A Collaborative Approach to Cross-Document Event Coreference Resolution with Large Language Models**, ACL 2024, `2024.acl-long.164`，让 GPT-4 产生 event-level summary，再由训练后的 task-specific small model 联合编码原始事件与 summary。它不是 GPT-4 zero-shot classifier，也不是 GPT-4 LoRA。citeturn14search0turn21view4

论文 Table 2 使用 MUC、B³、CEAFe、CoNLL F1 和 LEA，其中 CoNLL F1 是 MUC/B³/CEAFe 的平均：

| 数据集 | 方法 | CoNLL F1 | LEA F1 | 角色 |
|---|---|---:|---:|---|
| ECB+ | GPT-4 few-shot | 76.8 | 67.4 | direct closed LLM |
| ECB+ | task-specific baseline | 85.2 | 77.2 | fully trained SLM |
| ECB+ | **SECURE hybrid** | **86.7** | **79.3** | GPT-4 summary + SLM |
| GVC | GPT-4 | 10.2 | 7.6 | direct LLM |
| GVC | baseline | 84.7 | 78.4 | SLM |
| GVC | **SECURE** | **87.4** | **83.2** | hybrid |
| FCC | GPT-4 | 6.1 | 0.0 | direct LLM |
| FCC | baseline | 71.7 | 58.7 | SLM |
| FCC | **SECURE** | **78.7** | **71.5** | hybrid |

这些是同一 Table 2、同一 dataset/evaluator 的结果，所以正负证据都非常干净：**direct GPT-4 没有胜过小模型；GPT-4 作为 summary generator 后与小模型结合，反而在三个数据集上都胜过对应 baseline。** GVC/FCC 上 direct GPT-4 的极低结果还受到上下文截断等因素影响，这正说明“闭源 LLM 能做这件事”与“直接拿 API prompt 可以替代任务模型”完全是两回事。citeturn17view1turn18view4turn18view5

综合三个任务族，可以给出当前最稳妥的回答：

| 方法类型 | ED/EAE | Event relation | Event coreference | 证据结论 |
|---|---|---|---|---|
| Direct zero/few-shot | TextEE 明确落后 | Wei official test 明确落后 | SECURE direct GPT-4 多数落后 | **没有“普遍超过 fully trained RoBERTa/专用模型”的证据；反证很强** |
| Supervised LoRA/SFT | 严格统一轴证据仍不足 | **有正有负**：LLMERE 重划分轴正；Wei official-test 轴负/未胜 | 本轮未找到同样干净的 LoRA 主轴 | **不能笼统称胜出** |
| Frozen/LLM-generated representation + SLM | 有若干新 hybrid 路线，但本轮无足够同轴数字 | compression/knowledge 辅助有潜力 | **SECURE 是明确正证据** | **这是目前最可信的“LLM 增益”范式之一** |
| 闭源 API 辅助器 | 不能与 direct API 混为一类 | 可作 rationale/context provider | SECURE 明确有效 | **可提高任务模型，但引入成本和不可完全公开复现问题** |

## Agent、多智能体与自动事件图构建

“multi-agent”是这一方向最容易被滥用的术语。按实际计算图分类，本报告只把**存在多个独立角色/模型实例，各自产生中间判断，并发生显式信息交互或 aggregation/judging**的系统列为 true multi-agent。

| 工作 | 正式发表 | 实质分类 | 数据 / gold | 主要指标 | 对手 | 代码状态 |
|---|---|---|---|---|---|---|
| **CGEL** | ACL 2025 `2025.acl-long.1269` | **True multi-agent**：temporal、discourse、conditional/precondition、commonsense 专家 → communication → final judge | CRAB，约 2.7k event pairs；构造 causal/non-causal graph scenarios | Balanced Accuracy；causal/non-causal F1；Macro-F1，graph-level 对 scenario 聚合 | Direct、Pairwise、experts without collaboration | 论文给 `StonyBrookNLP/causal-graphs`；2026-08-25 静态检查返回 404，因此按**链接失效/不可取得**处理。citeturn26search0turn27view0 |
| **MMD-ERE** | COLING 2025 `2025.coling-main.460` | **True multi-agent debate** | event relation benchmark，包含 MAVEN-ERE 类设置 | relation metrics | 单模型/既有 ERE 方法 | 是关系抽取，不是完整图生成 |
| **CALLMSAE** | NAACL 2025 `2025.naacl-long.112` | **Cascade multi-stage pipeline，不是 multi-agent** | NYT-SEG；distant-supervision train + human annotated test | graph similarity 类评估 | graph-generation baselines | 官方 repo 存在，但本轮静态材料显示 Hungarian Graph Similarity evaluator 未完整随仓库交付；完整 train text 还依赖 Annotated NYT。citeturn26search1turn27view1 |
| **EventRAG** | ACL 2025 `2025.acl-long.830` | **Event extraction → graph → RAG pipeline** | 构建 event KG 后在 UltraDomain/MultiHopRAG 等下游任务验证 | 主要是 downstream retrieval/QA metrics | RAG baselines | 官方 repo 为 `Ryaang/EventRAG`；不是 gold event-graph extraction leaderboard。citeturn26search9turn27view2 |
| **TAG-EQA** | *SEM 2025 `2025.starsem-1.24` | **单模型多 prompt** | TORQUESTRA causal/event graph；text/graph QA | QA accuracy | zero/few/CoT × input modality | 公开 repo 存在；本轮审计未发现可独立重建固定 Full/Small derived test 的完整数据入口。citeturn26search7turn27view3 |
| **CompassMem** | Findings ACL 2026 `2026.findings-acl.1123` | agent + event-centric graph memory | agent-memory reasoning | 下游 reasoning | memory baselines | **不是传统“文本→gold event graph” benchmark**。citeturn13search3 |

CGEL 的内部 ablation 很有价值，因为它真的验证了“协作”而不仅是“用了更多 prompt”。其 Table 1：

| Backbone / variant | Graph-level Balanced Accuracy | Graph-level Macro-F1 |
|---|---:|---:|
| Llama Direct | 63.08 | 61.39 |
| Llama Experts without collaboration | 71.24 | 69.67 |
| Llama Collaborative | 73.69 | 72.49 |
| GPT-4o Direct | 70.86 | 71.48 |
| GPT-4o Pairwise | 73.93 | 72.68 |
| GPT-4o Experts without collaboration | 74.92 | 74.22 |
| **GPT-4o Collaborative** | **79.27** | **79.21** |

同一表中 GPT-4o collaborative 的 pair-level Balanced Accuracy/Macro-F1 为 77.12/77.51。这里允许比较，因为数据、scoring protocol 和 table 相同；它确实证明了**专家分解 + communication**优于 direct 和无协作 experts。citeturn27view0

但从硕士论文的实验约束看，CGEL 又有三个明显障碍：论文使用 Llama-70B-Instruct/GPT-4o 类 backbone；GPT-4o 是闭源 API；Llama-70B 显然不是“原方案按 27GB 单卡训练”路线；而论文中的官方 GitHub 链接在本次核验时又已经无法访问。citeturn27view0

因此，**真正满足“正式发表 + true multi-agent + event/causal graph construction/reasoning + gold quantitative evaluation + 代码可复现”的交集非常小**。大量看似 agentic 的工作实际上分别属于 cascade、RAG pipeline、single-LLM role prompting 或 graph-assisted QA，而非多 agent 建图。这是本轮检索最明显的“文献数量比关键词搜索结果少得多”的现象。citeturn27view0turn27view1turn27view2turn27view3

## GitHub 静态复现审计

这里严格区分三个层次：

**代码仓库存在 ≠ 训练代码完整 ≠ 可以在 2026 年原样复现论文数字。**

此外，本轮遵守“只做静态审计、不执行不可信代码、不下载大模型”的限制，因此“依赖可安装”只在有明确锁文件/现代依赖信息时才能给出静态判断，**没有实际 pip/conda install 的仓库一律不写“已验证可安装”**。

| 项目 | 官方仓库与 2026-08-25 元数据 | 训练 / preprocessing / evaluator / env / checkpoint | README 路径核验与 issue 复现证据 | 静态结论 |
|---|---|---|---|---|
| **TextEE** | `https://github.com/ej0cl6/TextEE`；61★；非 archived；latest commit **`567baa9bf8461daf9d53c8afc5bbf3938b365dd3`**, 2025-05-07 | 仓库树确认存在 `TextEE/`, `config/`, `data/`, `docs/`, `pattern/`, `scripts/`, `env.yml`, `requirements.txt`；覆盖 OneIE、PAIE、TagPrime、DyGIE++、EEQA 等大量实现 | README 所依赖的主要目录结构实际存在；本轮没有取得足以证明“第三方完整复现全部 16 datasets”的 issue 证据 | **本批中最强的 EE 实验基础设施之一；但部分数据本身受许可证限制，因此不是所有 benchmark 都可从 repo 直接得到。** fileciteturn9file0 |
| **OmniEvent** | `https://github.com/THU-KEG/OmniEvent`；410★；非 archived；latest commit **`130efae9ac3ea45eb0d87a292e03ed20c983ed32`**, 2024-12-18 | 面向 event detection/extraction 等统一任务；代码公开 | 本轮未逐一静态解析所有 README command 到文件级；不能声称全路径已验证 | **框架价值高，但仓库主要代码活跃期早于当前日期；需先做版本适配再作为 2026 主基线。** fileciteturn12file0 fileciteturn21file0 |
| **DeepKE** | `https://github.com/zjunlp/DeepKE`；4471★；非 archived；GitHub API `pushed_at` 2026-07-13 | 大型统一 KG/IE 框架，覆盖 RE/NER/EE 等；MIT | 本轮没有取得 latest-commit SHA，也没有逐命令核验 EE 子目录 | **维护活跃度远高于许多论文一次性 repo，但“DeepKE 整体活跃”不能替代某个 EE recipe 的逐路径复现审计。** fileciteturn13file0 |
| **MAVEN-ERE** | `https://github.com/THU-KEG/MAVEN-ERE`；92★；非 archived；`pushed_at` 2023-08-26 | benchmark/data/evaluation 资源为核心 | 本轮未得到 latest commit SHA；官方 hidden test 与后来重划分实验轴需要明确区分 | **适合保留为 evaluator/data source，但不能把后来论文不同重划分结果直接拼榜。** fileciteturn14file0 |
| **SeDGPL** | `https://github.com/zhanchuanhong/SeDGPL`；5★；非 archived；`pushed_at` 2026-03-25；API 未声明 license | CGEP 是 ranking formulation，公开 ESC-derived graph/scorer | 本轮静态材料未确认 MAVEN-derived 文件及完整 data-construction entry；未取得独立用户完整复现成功证据 | **“repo 有 scorer”不等于“两个数据来源都能从原始公开数据完整重建”。** fileciteturn15file0 |
| **SECURE** | `https://github.com/taolusi/SECURE`；12★；非 archived；`pushed_at` 2025-09-19；GPL-3.0 | 任务模型代码公开，但核心增强依赖 **GPT-4-generated summaries** | 即使训练脚本完整，闭源 API 生成物/模型版本仍会影响可重复性；本轮未取得独立 issue 成功复现证据 | **代码可研究，但严格端到端公开复现不是“纯公开模型方案”。** fileciteturn16file0 |
| **CALLMSAE** | `https://github.com/Xingwei-Tan/CALLMSAE`；2★；非 archived；API `pushed_at` 2026-07-03；GPL-3.0 | 图生成代码存在 | 静态材料显示论文所需 Hungarian Graph Similarity evaluator 未完整随 repo 交付；完整 NYT training text 还涉及 Annotated NYT 数据条件 | **不能写成开箱即复现。主要障碍是 evaluator/data dependency，而不是“有没有 Python 文件”。** fileciteturn17file0 |
| **EventRAG** | 官方 parent `https://github.com/Ryaang/EventRAG`；21★；非 archived；`pushed_at` 2025-07-17；API 未声明 license | Event KG + RAG pipeline 代码公开 | 网络上也存在 fork；应引用 parent 而非误把 fork 当官方实现；本轮未做每条 README command 的文件级审计 | **可作为 graph→RAG 方向实现参考，但它不是标准 gold event-graph extraction evaluator。** fileciteturn19file0 |
| **CGEL** | 论文给出 `https://github.com/StonyBrookNLP/causal-graphs` | — | **2026-08-25 GitHub API 返回 404** | **按“官方链接失效/当前不可取得”记录；不能写成“代码公开可复现”。** citeturn27view0 |
| **TAG-EQA** | `https://github.com/MaithiliKadam4/TAG-EQA`；本轮 API 快照为约 1★、非 archived，2025-06-22 前后有 push | prompting/evaluation implementation 公开 | 静态审计未确认 repo 包含可由原始 TORQUESTRA 一步重建论文固定 Full/Small derived evaluation set 的完整 recipe | **可审代码，不宜在未重建 test set 前声称复现论文数值。** citeturn26search7turn27view3 |
| **InstructUIE** | 官方实现公开 | Flan-T5 类 SFT scripts/checkpoint | 生态价值高 | **适合作为 predecessor baseline；但论文出版状态不符合本报告“2024–2026 正式发表方法”筛选。** citeturn25search3turn25search4 |

有几项用户要求本轮**没有足够证据完成到可以填“是/否”**，因此故意留空而不猜：

* DeepKE、MAVEN-ERE、SeDGPL、SECURE、CALLMSAE、EventRAG、TAG-EQA 的 **exact latest commit SHA** 没有全部在本轮可引用快照中保留下来；上表只使用已核实的 `pushed_at`，不把它伪装成 latest-commit date。
* 除 TextEE 外，本轮没有完整完成所有 repo 的“README 中每条命令引用的文件逐路径 exists check”。
* issue tracker 中“**独立第三方完整复现成功**”的证据整体很弱；没有看到证据就写“未找到”，而不是推断“没人成功”。
* 依赖均未实际安装，所以没有任何项目被标为“2026-08-25 已实测 pip/conda 可安装”。

这几项不完整性比给出虚假的绿色勾更重要。

## RTX 5090 约 27GB 单卡可行性矩阵

这里采用比普通“模型参数量估显存”更严格的标准：**没有论文硬件、官方框架文档或公开实测支持，就不报精确 GB。** “理论上可量化”也绝不等于“原论文在单卡 27GB 上已验证”。

最关键的已核实硬件证据来自 LLMERE：论文对 LoRA 配置使用 **NVIDIA A100 40GB**，max sequence length 2048、LoRA rank 64、learning rate \(2\times10^{-4}\)，MAVEN-ERE 3 epochs；因此其论文配置**不能直接写成已被 27GB 单卡验证**。citeturn22view1

Wei et al. 的 Llama-2-7B SFT 明确采用 4-bit quantization + LoRA rank 64，但论文 Appendix A **没有声明 GPU 型号**；这只证明方法采用了显存节省技术，不证明“RTX 5090 27GB 已验证”。citeturn7view3

| 方法族 | 27GB 单卡判断 | 需要的改造 | 可以据此声称什么 | 不能声称什么 |
|---|---|---|---|---|
| **Encoder-only：RoBERTa/DeBERTa/BERT 类 ED/ERE classifier** | **高可行性，首选严格 baseline** | 长文档 relation task 可能需要 windowing、gradient accumulation | 可作为 fully-trained strong baseline；TextEE/Wei 等已有成熟 evaluator | 不应因参数少就降低其对手地位；现有证据反而显示它们经常打败 direct LLM。citeturn19view0turn5view1 |
| **中小型 seq2seq / generation：PAIE、TagPrime/类似 TextEE 方法** | **高到中等可行性** | batch size、beam、document length 需按 benchmark 调整 | 可在 TextEE 标准协议下与多个已发表方法同轴比较 | 不能拿不同 preprocessing 的旧论文数字直接当复现值。citeturn15view0turn17view0 |
| **7B full-precision LoRA** | **候选可行，但本报告不标“27GB 已实证”** | gradient accumulation、activation checkpointing、降低 max length/batch 可能必要 | 可作为工程实验候选 | 不能从“LoRA 只训练少量参数”推导出某个具体显存数字 |
| **7B 4-bit QLoRA** | **最现实的 7B 训练路径之一；但具体论文 recipe 仍需单独验证** | 4-bit base + PEFT；必要时 checkpointing/gradient accumulation | Wei 已证明 ERE 中存在 Llama-2-7B 4-bit+LoRA 正式实验 recipe。citeturn7view3 | 不能说 Wei 在 27GB/5090 上验证过，因为硬件未声明 |
| **14B full-precision LoRA** | **不应作为“无条件可训练”承诺** | 通常需要更激进显存优化；上下文/optimizer/activation 决定是否越界 | 只能标“需预实验验证” | 没有来源就不能报“需要 X GB” |
| **14B QLoRA** | **工程上有希望，但本报告证据等级为“需改造、未在目标硬件实证”** | 4-bit、small micro-batch、gradient accumulation/checkpointing | 可以作为上限探索项 | 不能因理论上量化可行就把它写成论文可复现主线 |
| **LLMERE 原论文 recipe** | **需改造，未实证** | 从 A100 40GB recipe 向 27GB 收缩；可能涉及 batch/context/checkpointing | 方法思想适合 PEFT | **不能写“单 5090 可原样复现”**。citeturn22view1 |
| **Wei Llama-2-7B 4-bit LoRA** | **有 PEFT recipe，但 27GB 状态未知** | 保持 4-bit；实测确定 micro-batch | 是单 7B PEFT 的重要参考 | GPU 未声明。citeturn7view3 |
| **CGEL Llama-70B** | **原方案不属于本论文 27GB 单卡训练范围** | 若换 7B/14B，已成为方法改造而非原方案复现 | 可以复现 agent protocol 的思想 | 不能把 70B 论文数字当 7B 实现预期。citeturn27view0 |
| **CGEL GPT-4o** | **闭源 API，仅推理调用** | API cost/version control | 可作为 auxiliary/upper-bound | 不能视作公开单卡模型。citeturn27view0 |
| **SECURE** | **SLM 部分单卡友好；完整方法依赖闭源 GPT-4 auxiliary generation** | 可预生成 summaries，再训练 SLM | 很适合作为“LLM-generated evidence + small discriminator”的范式证据 | 不是纯 RTX 5090 self-contained pipeline。citeturn21view4 |
| **CALLMSAE** | **计算不是唯一障碍；数据/evaluator 才是主要复现风险** | 需先解决 NYT 与 evaluator | 可做 pipeline 思想研究 | 不能只做显存评估就判“可复现” |
| **EventRAG** | **可拆成多个单卡阶段，但整体取决于采用的 generator/embedder** | 向量库、EE、merge、generation 分阶段运行 | 不必端到端训练一个巨大模型 | 其主结果不是传统 event graph extraction 主指标。citeturn27view2 |

因此，针对“27GB 单卡 + 论文需要多个公开已发表对手”的约束，**证据最稳定的技术区间不是 14B+ agent，而是 encoder/seq2seq strong baseline + 7B PEFT/hybrid augmentation**。这不是按“对手弱不弱”做推荐，而是因为同轴 benchmark/evaluator 与硬件风险同时决定了实验能否形成可信证据。

尤其需要避免一句常见但错误的写法：

> “原论文用了 A100 40/80GB，不过 QLoRA 理论上省显存，所以 RTX 5090 可以复现。”

正确写法应是：

> **“原论文硬件为 A100 40GB（或更多）；目标 27GB 方案需要量化/梯度累积等改造，尚无该目标硬件的原论文实证，因此状态为‘需改造，未实证’。”**

LLMERE 正属于后一种情况。citeturn22view1

## 官方评测基础设施清单

对事件图谱硕士论文而言，“一个很新颖的方法”往往没有“一个不可争议的 evaluator”重要。下面几套基础设施的价值不同。

| 基础设施 | 能评什么 | 是否适合直接形成同轴主表 | 关键风险 |
|---|---|---|---|
| **TextEE** | ED/EAE，16 datasets；TI/TC/AI/AC/AI+/AC+ | **非常适合**。框架统一 preprocessing、五个 splits 与大量 baselines。citeturn21view0 | ACE05/RichERE 等并非全部自由公开；不能宣称整个 suite 都满足“只用公开数据”。citeturn15view0 |
| **MAVEN-ERE official evaluator** | temporal / causal / subevent / coreference | **适合，但必须冻结具体 split 轴** | 官方 hidden-test 与后续 original-valid-as-test 等协议已经分叉。citeturn5view1turn22view1 |
| **SECURE / standard CDECR metrics** | MUC、B³、CEAFe、CoNLL、LEA | 适合 event coreference | 数据集各自许可条件不同；GPT-4 summary generation 又增加闭源依赖。citeturn21view4 |
| **CGEL/CRAB evaluator** | causal graph pair-/graph-level BAcc、Macro-F1 | 论文内部非常清楚 | 官方代码链接当前 404，使 scorer 独立复核风险上升。citeturn27view0 |
| **SeDGPL/CGEP scorer** | MRR / Hit@k ranking | 适合 causal event prediction / graph completion | **不是 relation classification F1**，绝不能与 MAVEN-ERE F1 拼表 |
| **CALLMSAE graph similarity** | salient event graph similarity | 理论上适合完整图生成 | 本轮静态审计未确认论文 Hungarian Graph Similarity evaluator 完整交付 |
| **TAG-EQA** | graph/text assisted event QA accuracy | 适合 event-graph reasoning | QA accuracy 不能被当成 graph extraction quality。citeturn27view3 |
| **EventRAG downstream evaluation** | RAG / multihop retrieval & generation | 适合证明事件图对 RAG 的效用 | 不回答“生成的 event graph 与 gold graph 有多像”。citeturn27view2 |

对于**只用公开数据**这一硬约束，TextEE 需要进一步筛 dataset 子集，而不能整套照搬。论文明确讨论了 ACE05/RichERE 等数据获取和 preprocessing 问题，这也是为什么 TextEE 重跑后的结果有时会和历史论文相差数个 F1。citeturn15view0

MAVEN-ERE 则是另一种风险：不是 evaluator 不存在，而是**同名 benchmark 的实验 protocol 已经发生分叉**。如果未来主实验采用 LLMERE 的划分，就必须同时重跑 ProtoERE/RoBERTa/自己的 baseline 在该划分上；如果采用 Wei 的 official-test setting，就不能把 LLMERE Table 2 的 52.5 当作对手数值直接放进去。citeturn5view1turn17view3turn22view1

这也解释了为什么 SeDGPL/CGEP、CALLMSAE、TAG-EQA 很难直接成为同一“事件图谱 leaderboard”：一个是 ranking MRR/Hit@k，一个是 whole-graph similarity，一个是 graph-assisted QA accuracy，**它们研究对象相关，但 evaluator 定义完全不同。**

## 未核实、不可比与与预期不符的事实

本轮最值得保留的不是“最好的模型”，而是以下几项会直接改变论文实验设计的事实。

**InstructUIE 不满足“2024–2026 正式发表方法”过滤条件。** 它是 unified IE instruction-tuning 生态的重要前驱，但本轮可核实的 bibliographic status 是 arXiv/CoRR，而不是把它重新包装成 ACL 2024–2026 正式论文。citeturn25academia30turn25search4

**Direct LLM prompting 在事件抽取和事件关系上并没有击败 fully trained 小模型。** TextEE 的统一 ED/EAE 表和 Wei 的 MAVEN-ERE official test 都给出了非常清楚的负证据；这比二手 leaderboard 更可信，因为竞争方法在同一 evaluator 下被实际重跑。citeturn19view0turn5view1

**“7B LoRA > RoBERTa”不是普遍事实。** Wei 的 7B 4-bit LoRA 实验没有建立这个结论；LLMERE 则在另一个 MAVEN-ERE 重划分轴上建立了正结果。因此真正的结论是 **training recipe + rationale + split + task formulation 都重要**，不能只按 parameter scale 解释。citeturn7view3turn17view3turn22view1

**LLM+小模型 hybrid 的证据反而比 direct LLM 更强。** SECURE 是最典型实例：同一个 GPT-4，直接做 CDECR 明显落后，而把它限制为 event-summary generator 后，让监督小模型做最终判别，三个 benchmark 均超过 baseline。citeturn17view1turn18view5

**“Multi-agent event graph”正式论文数量没有关键词检索看起来那么多。** CGEL 符合真正的多 agent 专家协作；MMD-ERE 是 true multi-agent 但属于 event relation extraction；CALLMSAE 是 cascade；EventRAG 是 pipeline/RAG；TAG-EQA 是单模型多 prompt；CompassMem 是 agent memory graph。把后四者统称“multi-agent 建图”是不准确的。citeturn27view0turn27view1turn27view2turn27view3turn13search3

**有 GitHub 最不等于能复现。** 本轮最鲜明的例子是 CGEL：正式 ACL 论文明确给出 GitHub 地址，但到 2026-08-25 静态核验时该地址已经返回 404。CALLMSAE 则是另一种失败模式：仓库活着，但关键数据/evaluator dependency 并没有因此自动消失。citeturn27view0turn27view1

**MAVEN-ERE 已经有独立方法竞争，不是只有数据论文作者重跑旧 baseline；但这没有解决可比性问题。** Wei、LLMERE、TacoERE 等确实形成了方法生态，问题从“没有竞争者”变成“竞争者没有全在一个 split/evaluator axis”。citeturn2search0turn15view3turn15view2

**完整 event-graph generation 的官方 evaluator 基础设施明显弱于 ED/EAE/ERE。** TextEE 与 MAVEN-ERE 已形成比较成熟的 span/relation scoring；相比之下，CALLMSAE、CGEL、TAG-EQA、EventRAG 分别使用 graph similarity、causal graph classification、QA accuracy、downstream RAG evaluation，尚未形成一个像 TextEE 那样统一的 event-graph benchmark/evaluator。citeturn21view0turn27view0turn27view1turn27view2turn27view3

需要明确保留为**未核实**的还有：

* 2026-08-25 时各 repo 的全部 exact latest commit SHA，本轮只有 TextEE 与 OmniEvent 获得了可可靠引用的 SHA；其余不得把 `pushed_at` 冒充 commit date。
* 除 TextEE 外，并未对每一个 README command 做完逐文件存在性检查。
* 没有执行 pip/conda，因此“dependency still installable”只能写**未运行验证**。
* 未看到 issue 并不等于“没有人复现”；只能写“本轮未找到独立成功/失败证据”。
* CALLMSAE 的 full NYT-based reconstruction、SeDGPL 的 MAVEN-derived graph construction、TAG-EQA 的固定 derived test reconstruction，在当前静态证据下都不够完整。
* CGEL 的原官方代码如果后来迁移到其他仓库，本轮没有证据确认；因此状态只能是“论文给出的 URL 当前失效”，不能推断“作者永久删除代码”。

## 证据审计与最终判断

把本报告中影响论文决策的证据按强度重新审计，可得到下面的排序。

| 判断 | 证据等级 | 原因 |
|---|---|---|
| **TextEE 上 direct few-shot LLM 的 ED/EAE 明显未超过 fully trained baselines** | **A：严格同轴** | 同一论文 Table 6/7、同一抽样数据、同一 evaluator、同一指标定义。citeturn19view0 |
| **MAVEN-ERE official test 上 direct GPT-3.5/Llama-2 明显未超过 RoBERTa** | **A：严格同轴** | Wei 2024 Table 2；857-doc official test；官方 evaluator。citeturn5view1turn6view1 |
| **LLMERE LoRA 在其 MAVEN-ERE 重划分轴超过 ProtoERE 等分类 baseline** | **A：论文内部严格同轴** | LLMERE Table 2；同 split/evaluator；Llama-3-base 52.5 vs ProtoERE 50.8。citeturn17view3turn22view2 |
| **LLMERE 52.5 与 Wei RoBERTa 51.6 谁高** | **禁止比较** | test split 不同：LLMERE 用 original-valid-as-test；Wei 用 official 857-doc test。citeturn5view1turn22view1 |
| **SECURE hybrid > task-specific SLM，而 direct GPT-4 < SLM** | **A：严格同轴** | ACL 2024 Table 2，ECB+/GVC/FCC 同 evaluator；CoNLL/LEA。citeturn17view1turn21view4 |
| **CGEL multi-agent collaboration > direct / no-collaboration** | **A：论文内部严格同轴** | ACL 2025 Table 1，graph-level BAcc/Macro-F1。citeturn27view0 |
| **CGEL 是可复现代码项目** | **反证** | 论文 GitHub URL 在 2026-08-25 核验时不可取得；不能从“论文写了 URL”推导“现在能跑”。 |
| **CALLMSAE 是 multi-agent** | **错误分类** | 论文计算流程是 cascading stages/code refinement，没有多个协作 agent 的必要结构。citeturn27view1 |
| **EventRAG 是 event-graph extraction SOTA 对手** | **不可成立** | event KG 是 RAG 中间表示，主要 evaluation 为 downstream retrieval/generation，不是统一 gold graph extraction score。citeturn27view2 |
| **TAG-EQA 是 multi-agent graph constructor** | **错误分类** | 它是 zero/few/CoT 与 text/graph modalities 的 single-model prompting matrix，evaluation 是 QA。citeturn27view3 |
| **7B 4-bit LoRA 在 ERE 已有正式论文实现** | **A** | Wei Appendix A 明确 Llama-2-7B、4-bit、LoRA rank 64。citeturn7view3 |
| **上述 recipe 已在单 RTX 5090 27GB 验证** | **未核实** | Wei 未声明 GPU；不能推导。 |
| **LLMERE 原配置可以在 27GB 原样复现** | **未核实且不应假定** | 原论文明确用 A100 40GB；转到 27GB 是新工程改造。citeturn22view1 |
| **InstructUIE 属于 2024–2026 正式发表论文** | **反证** | 本轮可核实记录为 arXiv/CoRR；应作为前驱而非正式发表样本计数。citeturn25academia30turn25search4 |
| **GitHub 存在即可记“可复现”** | **明确否定** | CGEL 的失效 URL、CALLMSAE 的 evaluator/data dependency、MAVEN-ERE 的 split fragmentation 都直接反驳这一做法。citeturn27view0turn27view1turn22view1 |

由这些证据可以形成一个相当稳定的总体结论：

**在事件检测和论元抽取上，2024–2026 的严格证据仍支持 fully trained 专用模型，而不支持 direct LLM prompting 已成为更强范式。** TextEE 是这里最重要的共同坐标系。citeturn19view0turn21view1

**在事件关系上，监督 LoRA 已经出现真正超过强分类器的正结果，但这种优势高度依赖训练协议；MAVEN-ERE 目前不能用一个“LLM SOTA 数字”概括。** official-test 的 Wei 结果与 LLMERE 的重划分结果必须分别保留。citeturn5view1turn17view3turn22view1

**在事件共指上，目前最令人信服的 LLM 增益来自 hybrid，而不是 direct prompting。** SECURE 的同表结果清楚说明“大模型做知识/摘要生成，小模型做任务判别”能够超过 fully trained baseline，同时 direct GPT-4 本身并不强。citeturn17view1turn18view5

**在 event graph / causal graph 上，真正的 multi-agent 方法已经出现，但可复现生态远不如 ED/EAE/ERE 成熟。** CGEL 提供了漂亮的内部协作 ablation，却面临 70B/闭源 backbone 与当前官方 GitHub 链接失效；CALLMSAE、EventRAG、TAG-EQA 又分别属于 cascade、RAG 和 graph-assisted QA，因此不能拿它们构造一个虚假的“multi-agent event graph leaderboard”。citeturn27view0turn27view1turn27view2turn27view3

**对于约 27GB 的单 RTX 5090，最有证据支撑的实验空间是强 encoder/seq2seq baseline 加 7B 级 PEFT、retrieval 或 LLM→SLM hybrid，而不是把 14B/70B/闭源 multi-agent 系统假定为可训练主线。** 7B 4-bit LoRA 已有正式事件关系论文 recipe，但目标 5090 的实际显存与训练时间仍必须重新实测；14B QLoRA 只能标“工程候选、目标硬件未实证”；LLMERE 的 A100 40GB recipe 则必须明确写成“**需改造，未实证**”。citeturn7view3turn22view1

最后，若评价“哪类方法最符合这篇硕士论文要求的**公开数据、同指标多对手、27GB 单卡、LLM 时代方法价值**”，证据并不指向“挑一个最巨大的 LLM 做 end-to-end generation”，而指向一个更具体的事实：**今天最可靠的研究增量通常发生在结构化 schema / retrieval / rationale / generated evidence 与强任务模型之间的接口处；模型尺寸本身不是足够的创新变量，也不是可靠的性能变量。** TextEE 的 direct-prompt 反证、LLMERE 的监督 LoRA 正证据、SECURE 的 hybrid 正证据以及 CGEL 的 agent ablation，四组互相独立的结果共同构成了这一判断的主要依据。citeturn19view0turn17view3turn17view1turn27view0