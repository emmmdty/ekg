# 完整实验规划（防漂移主表）

> 冻结于 **2026-09-11**。服务 `SPEC.md` v1.1.0。
> **这份文件取代「每周想一遍下周做什么」。** 每周不再重新排任务，只从 §3 的主表里取下一个
> 未完成项。要偏离顺序，**先改本文件再执行**；口头改计划一律无效。
> 数字仍只写进 `results/PHASE_*.md`，本文件不复制任何实验数字。

## 0. 防漂移的四条规则

1. **单一主表**：可执行实验只认 §3。`HANDOFF.md` 的 E 队列只是主表的**当周切片**，不得包含
   主表以外的新任务。
2. **两条泳道并行**：§3 分 **CPU 泳道**与 **GPU 泳道**。GPU 不可用时，CPU 泳道照常推进，
   **不得**把「等 GPU」写成停工理由，也**不得**为了填时间发明主表外的任务。
3. **决策点是排期的一部分**：§4 的三个 Gate 是预先安排的重规划时刻。**只在 Gate 上改计划**；
   Gate 之间出现的新想法记进 §6 候补区，不插队。
4. **完成判据写在表里**：每一项的「完成 =」列就是验收标准。没达到就标 `wip` 并写清卡在哪条证据，
   不得口头声称完成。

## 1. 论文目标结构（作者 2026-09-11 选定「乙」形态）

```
第1章 绪论
第2章 相关工作与统一评测协议
第3章 事件事实性检测            ← D4    方法 + 3.4 实验（对比/消融/负控/案例）
第4章 事件关系抽取              ← A4    方法 + 4.4 实验
第5章 事件身份消解              ← C5    方法 + 5.4 实验
第6章 事件图谱构建与下游事件预测应用 ← E3  带公开对手的应用章
第7章 总结与展望
```

章序按**把握度**排，不按依赖：D4 赛道无竞争、power 六倍余量、实现已完成，放第 3 章先做；
C5 最没把握，放第 5 章。Ch6 不要求胜过任何方法章。

**每个方法章的实验节固定四件**（照钱子杰/宁婉廷/李璐的一致体例）：

```
X.4.1 数据集、评价指标与实验设置
X.4.2 对比模型          ← 逐个介绍每个 baseline
X.4.3 总体实验结果及分析  ← 主表：公开方法[ref] ×≥3 + LLM 对照 + 本文前期方法 + 本文最终方案（末行）
X.4.4 消融实验 + 负控
(X.4.5 参数/案例/错误分析)
```

主表形态与 FR-016 保真度规则见 [`BASELINE_ROSTER.md`](BASELINE_ROSTER.md)。

## 2. 当前状态基线

| | 状态 |
|---|---|
| v6.1 三份方法设计 | **一个都没跑过**。C5/A4 未实现，D4 只完成 D4.0 实现与本地 gate |
| 各章主锚 | Ch1 MUC `.809847`；Ch2 causal F1 `33.17`；Ch3 pooled 5 类 macro-F1 `.553995` |
| Ch6 已有资产 | 图依赖正控**已通过**（gold .1802 / rewired .1185 / no_graph .0811）；构建损失 −.0218＝整图价值 22.0%；受控扰动曲线已测 |
| gpu-4090 | **CUDA 完全不可用**（驱动内核模块与用户态库版本不符，需 root 修复，机器共用） |
| gpu-5090 | 可连，但 host key 待确认、剩约 15GB、须逐次授权 |

## 3. 实验主表

### 3.1 CPU 泳道（GPU 不可用时照常推进）

| ID | 实验 | 依赖 | 完成 = | 产物 |
|---|---|---|---|---|
| **C-1** | D4.1 immutable preflight | 无 | protocol `status=pass`；独立重算两条 accepted OOF baseline；全部 hash/覆盖/折隔离一致 | `runs/stages/D4/d4-v61-typed-cues-r1/preflight/` |
| **C-2** | EasyECR 可运行性实跑核查（不训练） | 无 | 裁决 `runnable`/`conditionally_runnable`/`not_runnable` 落 `results/PHASE_R1.md`；KBP 2017 可得性判定写进名册 §1.1，定下 FR-016 状态 (a) 还是 (b) | 名册 §1.1 + 结果页 |
| **C-3** | E8.1 LLMERE 恢复方案冻结 | 无 | 方案覆盖全部 11,149 条、同一规则、原始输出保留、fail-fast 与成本明确。**通过≠获准重生成** | 结果页 §9.x |
| **C-4** | Ch6 对手名册调研与冻结 | 无 | 名册 §6 填满或明确判定「不足 3 个公开对手」；每个候选带代码可得性与 FR-016 路径 | 名册 §6 |
| **C-5** | C5.0 实现 + 本地 gate | 无（QR-001 修订后已解锁） | targeted tests + 三件套全绿 | 代码 + 测试 |
| **C-6** | A4.0 实现 + 本地 gate | 无 | 同上 | 代码 + 测试 |
| **C-7** | LLM 对照脚手架（提示模板、LoRA 配置、评分接线） | 无 | CPU fixture 能跑通三章各自的输入/输出格式 | 代码 + 测试 |
| **C-8** | 第 2 章「统一评测协议」素材整理 | 无 | manifest/划分/评测器/口径三轴一次讲清，可直接写进论文 | `docs/` |

CPU 泳道**全部 8 项都不依赖 GPU，现在就能做**，且彼此无强依赖，可任意顺序并行。

### 3.2 GPU 泳道（全部阻断在 G-0）

| ID | 实验 | 依赖 | 粗估 | 完成 = |
|---|---|---|---|---|
| **G-0** | **修复 gpu-4090 驱动**（重启或重载 nvidia 模块） | **作者联系机主，我们无 root** | — | `nvidia-smi` 正常且 `torch.cuda.is_available()` 为真 |
| **G-1** | D4.2 CPU/CUDA smoke（1 fold / 10 docs / 三臂） | C-1 + G-0 | 分钟级 | 三臂 loss/logits/spans 有限；evaluation ID 未入 train/selection |
| **G-2** | **D4.3 seed-13 五折 pilot（三臂）** ← **GPU 恢复后的队首** | G-1 + 作者授权长任务 | ~1.5 GPU·day | 2,913 篇 / 73,939 mention 各恰好一次 OOF 预测；逐实例概率/cue/evidence/三级 logits/confusion 落盘 |
| **G-3** | D4 supporting-word baseline 五折重建 | C-1 + G-0 | ~1 GPU·day | 先在官方划分复现官方数字（容差事前定 ±1.0 macro-F1）→ FR-016 状态 (a)；再转五折 OOF |
| **G-4** | A4.2 smoke → **A4.3 seed-13 pilot（四臂）** | C-6 + G-0 + 授权 | ~2–3 GPU·day | 完整候选逐位不变；逐实例 evidence 与三种 counterfactual logits 落盘 |
| **G-5** | C5.2 smoke → **C5.3 seed-13 pilot（三臂）** | C-5 + G-0 + 授权 | ~1 GPU·day | 291 篇 / 7,195 mention 全覆盖；false-merge 中介与 calibration 落盘 |
| **G-6** | EasyECR Global-Local Topic 复现 | C-2 判定可跑 + G-0 | ~1–2 GPU·day + 调试 | 若 KBP 2017 可得则先复现其发表数字（(a)）；否则直接跑 MAVEN-ERE 并标 (b) + 列差异 |
| **G-7** | LLM 对照 ×3 章（Qwen3-8B LoRA） | C-7 + G-0 | ~1 GPU·day/章 | 三章主表各加 1–2 行；披露 backbone/revision/微调方式/提示模板 |
| **G-8** | E8.2 LLMERE 全量重生成 + 官方评分 | C-3 + **作者明确授权** | 42 GPU·h（批量化后 3–5 h） | 11,149 条同一规则重生成；官方 evaluator 打分；或如实记为不可评分失败 |
| **G-9** | matched seeds 13/17/42（**仅对已过 seed-13 门的章**） | G-2/G-4/G-5 过门 + **逐次授权** | 各 ~2× pilot | mean delta、2/3 为正、10,000 次配对 bootstrap CI 下界 > 0 |
| **G-10** | sealed final-valid ×1（**仅对已过 confirmation 的章**） | G-9 + 配置完全冻结 | 小时级 | 一次性评测，写入 final-valid ledger |
| **G-11** | Ch6：E3.0 → E3.1 → E3.2 → E3.3 → E3.4 → E3.5 | C-4 + 至少一章的 bundle/fallback + G-0 | ~1–2 GPU·day | 见 `phases/PHASE_E3_graph_application.md` 的 Done when |
| **G-12** | H2 全篇复现验收（默认 CPU/cache） | G-11 | ~CPU | 见 `phases/PHASE_H2_thesis_acceptance.md` 七项审计 |

**GPU 预算粗估**：不含 matched seeds 约 **10–14 GPU·day**；三章都过门并跑 matched seeds + final-valid
则合计约 **25–30 GPU·day**。两卡并行且 namespace 不重叠时可对半。

**两卡并行的合法组合**（G-0 修复后）：卡 A 跑 G-2（D4，写 `runs/stages/D4/`），
卡 B 跑 G-4（A4，写 `runs/stages/A4/`）或 G-6（EasyECR，独立 venv 与 namespace）。
**不得**用并行跑同一方案的多个 seed——多种子始终另行授权。

## 4. 三个决策点（预先安排的重规划时刻）

| Gate | 触发时点 | 要判什么 | 分支 |
|---|---|---|---|
| **Gate 1** | G-2（D4.3）出结果 | typed-cue 机制有没有价值：full 是否高于 CLS 与 DMRoBERTa；full vs remove-core 是否降低注册 confusion；permutation 是否消除该改善 | **过** → 继续 G-4/G-5，三章结构保留。**不过** → **不启动第二个周期**，直接进 Gate 2 讨论结构 |
| **Gate 2** | G-4 与 G-5 都出结果 | 还剩几个方法章 | **3 章过** → 博士量级，按原结构写。**2 章过** → 正好是领域硕士标准形态（2 方法章 + 1 应用章），按此写。**≤1 章过** → 与导师共同决定改纲，**不得**自行降级或再开新机制家族 |
| **Gate 3** | C-4（Ch6 名册）冻结 | Ch6 能否凑够 ≥3 个公开对手 | **能** → 按 E3.3 做带对手的应用章。**不能** → Ch6 降为描述性构建与应用章（保留构建流程、统计、可视化、构建损失与扰动曲线），**这是允许的收缩，不是失败** |

Gate 之外不重排计划。Gate 上的裁决必须写回本文件与 `HANDOFF.md`。

## 5. 与 phase 契约的映射

| 主表 ID | 契约 | 契约内任务号 |
|---|---|---|
| C-1, G-1, G-2, G-3 | `phases/PHASE_D4_typed_cue_factuality.md` | D4.1 / D4.2 / D4.3 / D4.1b |
| C-6, G-4 | `phases/PHASE_A4_pair_evidence.md` | A4.0–A4.4 |
| C-5, G-5 | `phases/PHASE_C5_argument_uncertainty.md` | C5.0–C5.4 |
| C-2, C-4, G-6, G-7 | `BASELINE_ROSTER.md` §1/§2/§3/§6 | FR-016 判定 |
| C-3, G-8 | `results/PHASE_R1.md` §9.6 / §21.6 | E8 恢复 |
| G-11 | `phases/PHASE_E3_graph_application.md` | E3.0–E3.5 |
| G-12 | `phases/PHASE_H2_thesis_acceptance.md` | 七项审计 |

## 6. 候补区（Gate 之间产生的想法放这里，不插队）

- LLMERE 保真度路径与 `HANDOFF.md` §E.1a 第 6 条冲突，待作者裁决（见 `results/PHASE_R1.md` §21.6）；
- CorefPrompt 若以我方 Qwen3 论元替代失效的 OmniEvent 论元文件，可作 Ch1 第二个 (b) 状态对手；
- Ch3 是否在主表增报 3 类 macro-F1 与 micro-F1 两列（领域惯例，需在 D4 任何结果出现前登记）。

## 7. 不做的事

- 不恢复 24 条件 factorial、Holm 校正家族、frozen-vs-fine-tuned 同 backbone 对照；
- 不为「看起来在跑」启动无准入的训练；
- 不在未授权时启动额外 seeds；
- 不用更大 backbone、换 split、扫参或改选模规则来救已止损的机制；
- 不用 LLM 为主评测生成标注（只作 baseline 行与训练侧增强）。
