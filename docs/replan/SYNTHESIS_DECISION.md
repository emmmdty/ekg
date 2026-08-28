# v6 五路证据综合与项目决策

> ⚠️ **状态更新（2026-08-27）**：本文的一手证据与候选盘点继续有效，但“重开论文主轴、冻结 v5”
> 的决策已被作者撤回。该决策把“公开可比”过度收缩成完全相同的作者原 split、两个近期独立作者包、
> 零修补和可自由再分发数据，导致不断淘汰本可在本地统一协议上重跑的方法。当前权威决策是恢复
> `docs/SPEC.md` 的 v5 组件主线；各章可使用不同语料，详见 `THESIS_COMPONENT_REFOCUS.md`。

> 决策日期：2026-08-25（Asia/Taipei）
>
> 输入：A–E 五路探索、B–E 本地审计、当前 v5 权威实验结果与本地资产清单
>
> 本文只决定研究对象、主轴去留和下一阶段门槛；**不设计章节、不写实现计划**。

## 决策摘要

### 1. 事件图谱还是事理图谱

选择 **occurrence-level 事件图谱**，不选择事理图谱作为学位论文总本体。

这里的事件图谱指：节点对应一次可识别的现实发生，具有 mention/identity、参与者、时间、来源和
事件间关系中的一部分；不是把一般实体 KG、temporal KG、GraphRAG 或脚本模式统一改名为事件图。

选择依据不是“这个方向的对手更容易超过”，而是三项本体一致性：

1. 公开标注和当前可核主任务主要监督 occurrence/event mention 的身份、因果、时间与事实性；
2. 风险监测真正需要追问的是“发生了什么、是否为同一事件、何时发生、来源是什么”，而不是只归纳
   “这类情形通常如何演化”；
3. 本地 schema、loader、关系/共指 evaluator 和事实性模块都已围绕实例级事件运行。

事理图谱更接近 eventuality/script/narrative-evolution：节点是去情境化模式，目标是通常顺序、因果规律
或后继预测。该支系有研究价值，但 2024–2026 专项 survey、统一英文术语和共享公开竞争轴的证据都更
稀疏。不能先选“事理图谱”这个中文名，再把 occurrence-level 数据硬套进去。

### 2. 重构还是重开

如果必须二选一：**重开论文主轴**。

但这不是删除仓库、从零开发。准确动作是：

> **研究上重开，工程上迁移重构；冻结 v5 结论，不延长 v5 四章。**

不建议继续把 Ch1–Ch4 各补一点实验，因为四章当前都没有无保留满足“在公开同轴主指标上超过多个
已发表方法”的学位论文标尺。也不建议推倒 9,962 行代码，因为通用 evaluator、calibration、schema、
registry、数据流水线和实验纪律仍有高价值。

### 3. 新主轴的首要锚点

将 **EventStoryLine / Causal-TimeBank 上的事件因果识别（ECI）**作为下一阶段唯一的
**条件性主锚**，先完成协议闭环，再决定它能否承担正式方向。

原因是它目前是问题价值、近期独立竞争、公开性和单卡可行性的最佳交集：

- 2024–2025 至少三个作者不重叠的正式团队在 ESL/CTB 上实验：
  [ICCL](https://aclanthology.org/2024.emnlp-main.51/)、
  [LKCER](https://aclanthology.org/2025.coling-main.495/)、
  [DICP](https://aclanthology.org/2025.findings-emnlp.139/)；
- 三者都采用 ESL 5-fold、CTB 10-fold 的大框架并报告 P/R/F1；DICP 明确使用单张 RTX 3090；
- [EventStoryLine 官方仓库](https://github.com/tommasoc80/EventStoryLine)含数据与 eval 资产，并声明
  CC BY 3.0；
- 因果方向、链一致性、不确定性、上游误差传播与多关系联合是近年 ECI survey 明示的真问题，
  不是为了寻找弱对手而制造的任务。

它仍只是条件性候选：ESL 有 v0.9/v1.0/v1.2/v1.5 差异，fold IDs、pair generation、CTB license 与
各方法 evaluator 尚未完全同轴。在至少复现两个公开对手前，不写“主轴已验证”或“SOTA 轴已锁定”。

固定协议的 MAVEN-ERE causal 可作为第二候选和复用验证轴，但不能继续承担默认主轴。它有最多本地
资产和至少四组近年独立团队，却同时存在 official hidden test、valid-as-test、sampled LLM 与
causal-only 等至少四类 setting。除非把所有对手重新锁进同一公开 valid 协议，否则“论文很多”不等于
“可比较对手很多”。

## 证据如何推到这个结论

### 问题价值与竞争密度分栏

| 候选方向 | 问题价值（不按对手强弱判断） | 竞争与公开轴 | 27GB / 复用 | 本轮决策 |
|---|---|---|---|---|
| **ESL/CTB 事件因果识别** | 因果方向、长链一致性、不确定性和跨句推理仍未解决 | 至少 3 个独立近期正式团队；公开性较强，但协议细节待冻结 | BERT/RoBERTa 高可行；关系流水线可迁移 | **条件性主锚** |
| **固定协议 MAVEN-ERE causal** | 文档级跨句事件关系仍困难，LLM direct prompting 未拉平 | 使用论文多，但至少 4 类 setting 分裂；hidden test 不可靠 | 复用最高；encoder 高可行 | **第二候选/复用轴** |
| **MATRES / TB-Dense 时间关系** | 完整时间图、结构输出与统一评测仍是明示问题 | 有正式方法，但 preprocessing、label mapping、closure/evaluator 历史分裂 | 单卡高；时间关系代码部分可迁移 | **储备，先补协议审计** |
| **ECB+ / GVC / FCC 事件共指** | 跨文档身份是 occurrence-level 图的必要前提 | 2024 有正式 hybrid 正证据；本轮未闭合官方下载许可、统一 setting 与严格竞赛序列 | 本地 coref evaluator/模型复用高 | **储备，不能立即开工** |
| **MAVEN-FACT 事实性** | 非事实事件和 evidence grounding 仍是真问题 | 数据大，但本轮未取得多个独立近期同轴方法；test 通道未闭合 | 当前模型与数据资产强 | **保留资产，不作主竞争轴** |
| **CGEP / TORQUESTRA 图上推理** | 显式事件因果结构的下游价值成立 | CGEP 仅原论文统一适配对手；TORQUESTRA 派生 test 未发布完整 | CGEP 本地实现多，但发布包断链 | **应用/诊断验证** |
| **EventRAG / event-agent memory** | 跨文档组织、长期状态和结构化检索价值高 | 未找到完整 event-specific 公共 benchmark；repo/evaluator 不闭合 | 工程贴合 LLM/Agent | **不作学术主指标** |
| **跨语言事件身份** | 自然多语报道对齐是真问题 | 未找到成熟 language-mixed identity gold 与多个公开对手 | 工程可做、标注不可造 | **排除主轴** |
| **供应链/大宗商品风险** | 现实价值和工业需求都高 | 缺“固定 raw text + risk gold + evaluator + 多个方法”的公开闭环 | 可作场景展示 | **只作应用延伸** |
| **事理/脚本/演化图谱** | 通常规律和后继推演有价值 | 术语、schema、近年 survey 与共享 benchmark 更弱 | succession 思路可迁移，代码强绑定 | **不选总本体** |

这张表只找到一个“条件性主锚”，没有找到一套已经自然组成 3–4 章的方向。这个空缺必须诚实保留。
本轮提交的是方向决策，不是把证据不足的位置用自造章节填满。

## 为什么 v5 不应继续局部补洞

实验数字均取自 `docs/results/PHASE_*.md`，不采用 SPEC/TODO 中的复制值。

| v5 任务 | 当前最干净证据 | 与学位标尺的冲突 |
|---|---|---|
| Ch1 MAVEN-ERE 共指 | 全 710 valid、官方 evaluator：MUC **77.47** | 官方 RoBERTa 81.4 是 hidden test，不同 split；当前没有超过一个强 baseline，更没有超过多个方法。内部 497 篇口径的 79.6 不作 headline。 |
| Ch2 MAVEN-ERE 关系 | 同 valid、官方 evaluator：causal **28.50**；官方原版同 valid **31.37** | 仍低于同代码 baseline 2.87 点；subevent 又从 24.03 降到 21.05。结构修复只清环，不涨公开关系 F1。 |
| Ch3 MAVEN-FACT | valid macro-F1 **.4823** | 官方 47.1/47.6 在 hidden test，不能跨 split 宣称超过；2025–2026 多个独立同轴方法证据不足。净化的结构和下游主张均已被实验否定。 |
| Ch4 CGEP/误差传播 | gold→predicted 构建损失 **−.0218 MRR** 是确凿效应 | 修复 +.0011、净化近零、选边 +.0009 均落在噪声地板；CGEP-MAVEN 派生数据/对手包不公开，无法承担“超过多个方法”。 |

因此，v5 的问题不是再多跑几个种子就会消失。它同时存在：主指标低于 baseline、split 不可比、独立
竞争不足、公开派生包缺失和核心机制零效应。继续补洞会把时间花在不能兑现学位标尺的轴上。

需要特别更正一条旧认知：本地资产清单写“只有事实性检测超过公开方法”，这在数值表面上成立；经过
严格 split 审计后，**不能升级为公开同轴超过**。这不否定模型本身有价值，只否定当前证据足以满足
学位章节门槛。

## 重开后保留什么、冻结什么

### 原样或低成本迁移

- `core/calibration/`、`core/eval/`、schema/io/graph/registry/config；
- MUC/B³/CEAFe/BLANC、关系 P/R/F1、ranking、faithfulness evaluator；
- registry + lazy import、CPU 缓存回放和脚本化 build/train/evaluate/report 流程；
- paired bootstrap、噪声地板、canonical 序、强随机对照、oracle 泄漏红线、三轴口径审计；
- `relations/` 的文档级 pair、判别式抽取与一致性组件，在换 loader/label space 后迁移；
- `nodes/` 的 span 编码与 coref 基础、`factuality/` 的检测/evidence 实现，作为储备资产；
- 已下载数据只作为候选库存，选中后重新核 split、license 和计数。

### 冻结为负结果/诊断资产

- v5 Ch1–Ch4 的全部权威结果与止损结论；
- succession 受控扰动、三图归因、canonical-order 与噪声地板方法学；
- “结构一致性不等于下游收益”“事实性净化 oracle 仍为零”等反证；
- 生成式 SFT+GRPO causal 召回崩溃、Longformer/roberta-large 换底座负结果。

### 不再作为新主轴继承

- `succession/` 中与 MAVEN+SeDGPL 强绑定的约 2,148 行实现；
- v5 “构建质量的消费者依赖性” headline；
- 任何只在自造 R1/R2、结构违反数或内部难例指标上成立的章节论证；
- 通过 CRAB/叙事完形等不同数据和消费者拼接来补 CGEP 缺少公开对手的设计。

重开的真实代码损失约为 2,000–3,000 行强绑定实现，不是整个 9,962 行项目。通用层约 2,263 行，
再加 Tier 2 的方法骨架、数据资产和工程制度，足以支持在同一仓库内重构。

## LLM / Agent 在新方向里的位置

LLM/Agent 应是候选方法组件和工程能力，不是选题成立的理由。

- direct zero/few-shot 在 MAVEN-ERE、跨文档共指和时间关系上的严格证据总体仍落后监督 encoder；
- 监督 PEFT、LLM→SLM hybrid、cascade、RAG 和 true multi-agent 必须分开，不得统称“LLM 方法”；
- 优先级应是 encoder/seq2seq 强 baseline → 可复现 hybrid/7B PEFT → 必要时才引入 agent workflow；
- 70B、多闭源 API、缺数据/evaluator 的 CGEL/MMD-ERE 一类方案不作主复现依赖；
- 与就业价值最贴合的是 structured data engineering、hybrid retrieval、evaluation/observability、
  provenance 和 production pipeline，而不是强行让论文标题出现 Agent。

## 作者认可后才执行的四个门槛

这些是“进入章节设计前的 go/no-go”，不是本轮实施计划。

1. **协议门槛：**冻结 ESL corpus version、CTB 文件版本、fold IDs、pair generation、negative sampling、
   evaluator 与 checksum；CTB license 仍未取得时必须明确研究使用边界。
2. **对手门槛：**在同一冻结协议下至少本地复现两个独立近期正式方法；若只能引用论文数字或对不上
   fold/pairs，就不能把 ECI 宣布为正式主轴。
3. **算力门槛：**先做 CPU 数据闭环，再在 27GB 可用显存上做最小训练 smoke；不得从“BERT/6B”
   自动推断完整 recipe 可运行。
4. **全篇门槛：**只有 ECI 通过前三项后，才对 MATRES/TB-Dense、event coreference 和固定协议
   MAVEN-ERE 做针对性补审，并据此提出 2–3 套完整章节骨架。

若 ECI 在协议或双 baseline 复现上失败，立即降级，回到固定协议 MAVEN-ERE causal 作为备选；不通过
修改指标、改数据版本或自造 split 挽救。

## 明确不做

- 不把跨语言、供应链、大宗商品、GraphRAG 或 agent memory 的现实价值冒充公开 benchmark 成熟度；
- 不把不同 split/evaluator 的 headline 数字排成 SOTA 时间线；
- 不在 ECI 协议闭环前启动 GPU 大实验；
- 不删除 v5 负结果、不复活已经由 oracle/强对照否定的机制；
- 不在作者确认本决策前编写章节、设计新方法或修改实现代码；
- 不提交、不推送当前工作树。

## 决策置信度与未决项

- **事件图谱 > 事理图谱：高置信。** 本体、公开任务与本地资产三者一致。
- **重开论文主轴：高置信。** v5 四章与硬标尺的冲突来自权威结果和公开协议，不是主观偏好。
- **ESL/CTB ECI 为首要锚点：中高置信。** 三个独立近期团队和单卡证据成立，但 exact protocol 尚未闭合。
- **能否由该锚点形成 3–4 章：未决。** 五路证据没有自动给出完整章节链；必须等协议/对手门槛通过后
  再设计，不能在这里制造确定性。

## 审计输入

- [A：领域地形与术语](/home/tjk/myProjects/masterProjects/ekg/docs/replan/A_terrain.md)
- [B：数据与竞争审计](/home/tjk/myProjects/masterProjects/ekg/docs/replan/B_datasets_audit.md)
- [C：方法与代码审计](/home/tjk/myProjects/masterProjects/ekg/docs/replan/C_methods_code_audit.md)
- [D：跨语言、风险与替代切口审计](/home/tjk/myProjects/masterProjects/ekg/docs/replan/D_angles_audit.md)
- [E：工业与人才信号审计](/home/tjk/myProjects/masterProjects/ekg/docs/replan/E_industry_audit.md)
- [本地资产清单](/home/tjk/myProjects/masterProjects/ekg/docs/replan/LOCAL_ASSET_INVENTORY.md)
- [v5 权威实验结果索引](/home/tjk/myProjects/masterProjects/ekg/docs/results/README.md)
