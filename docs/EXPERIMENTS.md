# EKG 实验协议（EXPERIMENTS）

> **实验设计的单一权威**：评测协议 + 每章 baseline 矩阵 + 消融矩阵 + 报数规范。
> Phase A–I **照此跑**；主表/消融/协议声明**遵循已发表论文写法**。设计定义见
> [`SPEC.md`](SPEC.md)（§1 四章 + §5 新颖性）；实时状态见 [`TODO.md`](TODO.md)；
> 阶段验收见 [`phases/`](phases/README.md)。**本文件与 SPEC 冲突时以 SPEC 为准。**
> 更新于 2026-07-23（据一轮联网 baseline/竞品/评测协议核实建立）。

## 0. 总原则（每章都要满足才算"可信服"）

1. **主表 + 消融表 + 多种子**，缺一不可：
   - **主表**：本章方法 vs baseline（同数据、同划分、同指标）。
   - **消融表**：本章每个"环节"各做一次 `±`，证明它单独有效（对应一个可信度维度）。
   - **多种子**：seeds 13/17/42，报 `mean±std`（放 Phase H，主结果先单种子）。
2. **baseline 光谱**（避免"只跟老方法比"被审稿人打）：每章至少覆盖
   **① dataset 原文/经典 baseline（参照点）② 近 1–2 年代表方法（≥1 个方法族不同者）
   ③ 通用 LLM（zero/few-shot，作下界或上界参照）**。
3. **报数如实**：数字降就说降；受控实验不冒充真实图结果；不换指标掩盖负结果（`CLAUDE.md` 硬约束）。
4. **协议声明**：论文里显式写清训练/选模/报数用的 split（见 §1），像 SeDGPL 那样说明"为何这样切"。

## 1. 评测协议：test 无 gold 怎么办（有先例，非自娱自乐）

MAVEN 四件套官方 **test 标签隐藏**，走 CodaLab。这是该领域**常态**，处理方式有三档，v4 每章对号入座：

| 档 | 做法 | 先例 | v4 落到哪章 |
|---|---|---|---|
| **A. 官方 test（CodaLab 提交）** | 预测 `results.jsonl`→zip→提交竞赛拿官方分；开发/消融用 valid | MAVEN 检测 / MAVEN-ERE 均有永久竞赛 | **Ch1 检测、Ch2 关系** 主表首选 |
| **B. dev/valid 当 test** | 无官方 test 时，用 development set 当 test 报数并**显式声明** | **SeDGPL 本人**："因 MAVEN-ERE 未发布 test，用 dev 当 test" | **Ch4 后继预测**（CGEP 派生任务无官方 test） |
| **C. train 调参 / valid 报数** | 只发 train/valid 时，train 选模、valid 报最终 | MAVEN-FACT（只发 train/valid） | **Ch3 事实性**；Ch1 论元(MAVEN-Arg) |

**硬规矩**：
- **官方 test 一次性**：CodaLab 提交次数有限，**严禁**拿 test 反复调参。所有超参/早停/模型选择只用 valid。
- **Ch4 可比性红线**：SeDGPL 的 MAVEN 版重建数据**未公开**（论文承诺 review 后发，实际只发 ESC 的 `.npy`），
  其公开 MRR **27.9 不可比**。Ch4 主表**必以我们自跑的 SeDGPL 为基线**（当前单折 MRR 0.1836 / strict 0.1265），
  引用 27.9 须标注"原论文数据构建，非同数据可比"。
- **ESC 必 topic 交叉验证**（EventStoryLine topic），文档级切分泄漏（实测 topic-CV 0.0599 vs doc-split 0.1802）。
- **词表 transductive 要主动交代**：`<a_i>` token 清单覆盖 train+test，与 SeDGPL `to_add.json` 一致，
  只 token 清单跨切分、无标签/图/梯度泄漏——论文里显式说明，不留把柄。

## 2. 每章 baseline 矩阵（新老搭配 · 已核实真实）

> 角色标注：**⛳经典/原文**（参照点）｜**🆕近期代表**（2024–2026）｜**🤖通用 LLM**（zero/few-shot）｜**★我们**。
> "靶"= 该数据集当前公开最强，是本章要打平或超过的目标。**具体选哪几个进主表，按 Phase 当时可复现性再定；本表是候选池。**

### Ch1 身份 —— 事件检测 / 共指 / 论元

| 方法 | 年 | 方法族 | 角色 | 参考数字（MAVEN 系） |
|---|---:|---|---|---|
| DMBERT / MOGANED / BiLSTM+CRF | 2020 | 判别式序列标注 | ⛳ | 检测 F1 ~66–68 |
| CLEVE / 对比预训练 | 2021 | 事件对比预训练 | ⛳ | — |
| APEX-Prompt / 类型特定 prompt | 2022 | prompt tuning | 🆕 | 监督 +≈4 F1 |
| TextEE（重评测基准） | 2023 | 统一评测框架 | 🆕 | 校准各法可比性 |
| Context-Aware Encoder + LoRA | 2024/25 | PLM+LoRA 长尾 | 🆕 | Macro-F1 长尾↑ |
| DiCoRe（发散-收敛推理） | 2025 | LLM zero-shot ED | 🤖 | zero-shot 参照 |
| **规范事件节点（难例判别+校准）** | — | 判别式+不确定性 | ★ | 检测 F1 ~68 靶 |

共指候选：**MAVEN-ERE RoBERTa-base 官方基线（⛳，这才是同底座对标线）**｜HGCN-ECR 超图卷积（🆕2024）｜
X-AMR 线性共指（🆕LREC-COLING 2024）｜反事实数据增强（🆕2024）｜Synergetic+LLM（🤖2024）。
论元候选：MAVEN-Arg 官方 baseline（⛳2024）｜多答案 QA 式论元抽取（🆕）。

### Ch2 结构 —— 事件关系抽取（本章关键路径）

| 方法 | 年 | 方法族 | 角色 | 参考 F1（MAVEN-ERE）|
|---|---:|---|---|---|
| **RoBERTa-base + pair 分类头（单任务）** | 2022 | 判别式成对分类 | ⛳（**官方基线，也正是 Phase A 复现的架构 → 这是我们的对标线**） | **temporal 55.8 / causal 30.6 / subevent 26.7 / MUC 81.4** |
| **同上 +joint（四任务联合训练）** | 2022 | 判别式 + 联合 | ⛳ | **temporal 56.0 / causal 31.5 / subevent 27.5 / MUC 82.1** |
| ProtoEM | 2023 | 原型增强匹配 | 🆕 | 多关系联合 |
| TacoERE | 2024 | 聚类感知压缩 | 🆕 | 长文档关系 |
| **graph propagation（富事件结构）** | 2024 | 联合+图传播 | 🆕（**当前公开 SOTA**） | **temporal 60.7 / causal 37.4 / subevent 32.9 / MUC 86.1** |
| MAQInstruct | 2025 | 指令式统一 ERE | 🆕 | 生成式统一 |
| LLMERE（带 rationale, O(n)） | 2025 | LLM 生成 + rationale | 🤖/🆕 | 降 O(n²)→O(n) |
| Llama3 / GPT-4（few-shot） | 2024 | 通用 LLM | 🤖 | 下界参照 |
| **判别式 supervised + 一致解码 + CRC 准入** | — | 判别式+全局解码+风控 | ★ | **先打到官方单任务基线（causal 30.6），再谈联合** |

> **口径（2026-07-29 回一手 PDF 核，MAVEN-ERE EMNLP 2022 Table 7/8）**：上面两行官方数字是
> RoBERTa-base 在 **test** 上 5 次随机试验的均值（causal 30.6 ±0.44 / subevent 26.7 ±1.34 /
> temporal 55.8 ±0.42；MUC 81.4 ±0.51）。**我们只能报 valid，属不同 split，写作须声明。**
> ⚠️ 此前本表把官方基线那行的 F1 栏写成「causal/subevent 偏低」**没填数字**，导致 Phase A 只对着
> 自设的 ≥.25 判「达标」——实际低于官方 5.6 点。与 Phase C 的「MUC ~86」是同一类错误。
> ⏳ SOTA 行（graph propagation, IPM 2024）的 split **未从一手确认**（付费墙），引用时须标注。

> Phase A 现状对照：**生成式 SFT+GRPO 探针 causal 召回 0.4%（3/810）/ subevent 0%（0/139）**——
> 文献已证"文档内事件多时生成长度受限、覆盖不全"是生成式通病，**判别式成对分类召回一致更高**，故换判别式打底。

#### Phase A 判别式抽取器实测（2026-07-23/24，RoBERTa-base pair-classification，valid 710 篇）

**判别式确实解了召回瓶颈**：causal 召回 **0.4% → 67.5%**、subevent **0% → 88.1%**，`hallucinated=0`
（判别式不产生端点不存在的幻觉边）。瓶颈随之从"抽不出来"转为"precision 偏低"。

类不平衡消融（`neg-ratio × weight-alpha`，F1 取阈值扫描最优）：

| 配置 | causal F1（P/R） | subevent F1 | temporal F1 |
|---|---|---|---|
| neg3 · α=1.0（首轮基线） | .167（.14/.22） | .206 | .317 |
| neg30 · α=1.0 | .161 | .202 | .316 |
| **neg30 · α=0.5** | **.234（.20/.27）** | **.221** | **.397** |
| neg30 · α=0.25 | .232 | .219 | .416 |
| neg30 · α=0.0 | .186（.27/.14） | .041（被淹没） | .407 |
| per-family c=.7/t=.25/s=.5 | .219 | .222 | .410 |
| per-family c=.8/t=.3/s=.6 | .205 | .211 | .410 |
| **官方 RoBERTa-base 单任务（同底座对标线）** | **30.6** | **26.7** | **55.8** |
| ~~PHASE_A 自设目标~~（**已作废，见下**） | ~~≥.25~~ | ~~≥.20~~ | — |

**结论**（如实）：① **α 曲线倒 U，全局 α=0.5 最优**，causal F1 从 .167 提到 **.234（+40%）**；
② **给 causal 更高 α 反而降 F1**（.234→.219→.205）——瓶颈不在权重强度；③ 逆频权重会抵消负采样，
故 neg-ratio 在 α=1 时近乎无效。

⚠️ **2026-07-29 推翻当时的方向判断**：那句「成对分类触及架构上限、超过 .25 要靠全局一致解码」
是**对着自设的 .25** 说的。真正的同底座官方基线是 **30.6**，而我们最终只有 .250 —— **差 5.6 点，
不是「架构上限」，是没复现到基线**。且 Phase B 的全局一致解码已跑完，只清环、不涨 F1，
那条替代路已被自己的实验排除。
**线索**：官方是 **P 35.0 / R 27.2**（precision 主导）且整篇编码后直接对事件对分类、**未做负采样**；
我们 recall 冲到 67.5% 而 precision 崩，用的是 neg-ratio 30 + 逆频加权 CE(α=0.5) —— 方向正好相反。
⇒ 首个假设是**类不平衡处理本身就是 precision 崩的原因**，整轮 α 扫描是在错误设定里找局部最优。

#### Phase B 全局一致解码 + 可追溯修复 + 风险受控准入（2026-07-25，W1–W4 代码 + CPU 验证）

**方法**（复用 consistency/admission/cgep，不重写）：`solve_with_trace` 发结构化 `RepairTrace`
（每条 drop/add + violation + before/after `consistency_report`，`solve()` 默认逐字节不变）；
`stratified_admission_report` 分层 FNR（边际 / 分族 / doc-macro + 准入集大小，按 SPEC §5.5 报边际期望、
不写每篇每类保证）；`succession/reconstruction` 出 ECG 可重建率 **R1 可达**（=CS-CRP `reachable` 桥）+
**R2 query 保真**。离线编排 `consistency_repair_report.py` 消费 GPU 端原始边 dump（`supervised_dump.yaml`：
supervised + identity + 无准入），本地 CPU 跑 repair+trace → CRC 准入（复刻 repair∘admit 固定映射）→ 三档轨迹。

**合成 dump 受控验证（CPU，如实）**——注入因果环（最弱边 conf 0.2 闭合 m1→m2→m4→m1）：

| 档 | causal_cyclic_scc | R1 可达率 | R2 query f1 | 准入集 |
|---|---|---|---|---|
| raw（identity 无修复） | 1 | 1.0 | **0.0** | — |
| repaired（solve_with_trace） | **0** | 1.0 | **1.0** | — |
| repaired + CRC 准入（α=.2, τ=.9） | 0 | 1.0 | 1.0 | 5/5（FNR 0） |

- **修复增益如实落在 precision 义 R2（0→1.0）、非召回义 R1（持平 1.0）**：环不删除 query 边故召回不动，
  但环使 tail 出度 1 破坏 query 边判定、R2 崩，破环后恢复。**与 PHASE_B 止损口径一致**——R1 受 α_edge
  约束本就可持平/略降，修复靠 violation/cycle↓ 与 R2↑ 讲，不换指标掩盖负结果。
- `dropped=1`（violation=causal_cycle）、`reachable_flags=[True]`（可直接喂 `run_cross_stage`）；
  交付时 269 passed / 12 torch-skip、ruff 0、smoke OK（2026-07-27 移除 SARGE/Phase G 测试后
  当前主干 = 241 passed / 12 torch-skip）。

**真实 predicted 图三档轨迹（2026-07-28，gpu-5090，497 篇 held-out test，α=0.2/cal_ratio 0.3）**
—— dump 710 篇 / 242,869 条原始边，产物 `runs/relations/consistency_repair_supervised.json`：

| 档 | causal_cyclic_scc | temporal_cyclic_scc | temporal_cyclic_edges | closure_gap | R1 可达率 | R2 query f1 |
|---|---|---|---|---|---|---|
| raw（identity） | 752 | 614 | 36,523 | 83.78 | **0.7310** | **0.0622** |
| repaired | **0** | **0** | **0** | **0** | 0.7294 | 0.0620 |
| repaired + 准入（τ=0） | 0 | 0 | 0 | 0 | 0.7294 | 0.0620 |

`repair_trace`：dropped 8,119 / added 8,770。分层 FNR（α=0.2）：边际 **.4742**、doc-macro .4925、
分族 coref 1.000 / temporal .4469 / causal .5616 / subevent .4065；准入集 163,533（329/篇）。

**如实结论（含负结果）**：① 结构违反被**清零**（752+614 个环状分量、36,523 条卷入边 → 0），这一档确凿；
② **R1/R2 均无增益、微降**（R1 .7310→.7294、R2 f1 .0622→.0620），**合成 dump 上 R2 0→1.0 的增益在真实图
上没有复现**——修复以补闭包边为主（added>dropped），`n_pred` 381→386 而 `tp` 恒为 51，补进来的边没命中
gold query，只稀释 precision；③ **PHASE_B 止损条件已触发**，Ch2 收缩为「可追溯修复清零结构违反」+ 误差
传播，**不声称修复提升下游可重建性、不换指标**；④ τ 校准出 **0（准入退化为全收）**，根因是**可行域为空**：
抽取器边际召回 .5258 ⇒ FNR 下界 .4742，α<.474 在这个 predicted 图上不可满足——要报有意义的 τ，得放宽
α 到 >.48 或先抬 Phase A 召回。coref FNR=1.0 源于抽取器 coref `n_pred=0`，非准入所致。

### Ch3 事实 —— 事件事实性检测 + 图净化

| 方法 | 年 | 方法族 | 角色 | 参考（MAVEN-FACT macro-F1）|
|---|---:|---|---|---|
| DLGRN（有向标注图递归网络） | 2021 | 图递归网络 | ⛳ | 早期依存结构法 |
| MAVEN-FACT 官方 fine-tuned | 2024 | PLM + 论元/关系 | ⛳ | **DMBERT 47.6**（原文最佳）｜**同底座 DMRoBERTa 47.1 / RoBERTa+CLS 45.4** |
| MAVEN-FACT 官方 GPT-4 | 2024 | 通用 LLM | 🤖 | **42.8**（劣于 fine-tuned）|
| ModaFact | 2025 | 情态+事实联合 | 🆕 | 跨语言 bonus 参照 |
| **结构感知检测 + 事实性净化** | — | PLM+结构 → 净化算子 | ★ | 检测已达（48.2@valid）；**净化已止损** |

> **口径（2026-07-28 回一手核，arXiv 2407.15352 Table 3/4）**：官方数字在 **test**，我们只能报
> **valid**，属不同 split，**不得简写成「超过 47.6」**。evidence 的官方口径是 **CT−/PS+/PS− 三类
> 宏平均**（45.4），与「全部 mention 的 pooled span F1」是两个量，两个都报、互不顶替。
>
> **novelty 落点（2026-07-29 按实测收窄）**：检测「打底=复现」（用结构非新，MAVEN-FACT 已证）。
> 原先主张的两个 delta 里——① **gold vs 预测图掉点**（±.0001）**成立**，保留；
> ② ~~净化后下游 MRR 增益~~ **已证为零**（可部署档 −.0001、oracle 金标档 −.0000，见
> [`results/PHASE_E.md`](results/PHASE_E.md)），**不得再作为 delta 主张**。

### Ch4 传播 —— 后继事件预测（headline）

| 方法 | 年 | 方法族 | 角色 | 参考（CGEP-MAVEN，SeDGPL 自建数据）|
|---|---:|---|---|---|
| MCPredictor | — | 脚本事件预测 | ⛳ | script chain 参照 |
| CSProm-KG / SimKG | 2023 | KG embedding 补全 | ⛳/🆕 | 图补全式 |
| BART-base | 2020 | 生成式 seq2seq | ⛳ | SeDGPL 最强 baseline **24.7 MRR** |
| Llama3-8B / GPT-3.5-turbo | 2024 | 通用 LLM | 🤖 | 下界参照 |
| **SeDGPL（DsGL+EeCE+ScEP）** | 2024 | 图 prompt learning | ⛳（**基座，自跑基线**）| 论文 27.9（不可比）/ **自跑 0.1836** |
| **三图误差分解与归因 + CS-CRP 误差预算** | — | 误差传播+conformal | ★ | **归因表 + 误差传播曲线（升降如实）**；~~repaired > predicted~~ 已作废（2026-07-29，门控天花板实测 0.24%） |

## 3. 每章消融矩阵（每个环节 = 一个可信维度的因果证据）

| 章 | 消融项（`±`） | 证明什么 | 观测指标 | 现状 |
|---|---|---|---|---|
| Ch1 | ± 难例判别（同类型近义触发词负采样） | 身份不误合并 | **相似事件误合并率** | ⬜ 待建 |
| Ch1 | ± 不确定性感知聚类 | 置信可下游消费 | `node_confidence` **ECE** | ⬜ |
| Ch2 | 判别式 vs 生成式 SFT+GRPO | 判别式解召回 | causal/subevent **P/R/F1**（对照 0.4%） | ⬜ Phase A |
| Ch2 | ± 类不平衡处理（加权CE/focal/负采样） | 稀疏关系可学 | causal recall | ⬜ |
| Ch2 | ± 全局一致解码（闭包/破环/对称） | 结构自洽 | **violation / cycle 率** | 🟡 求解器 + RepairTrace，CPU 验证；真实图待 GPU |
| Ch2 | ± CRC 边准入 | 关键边不漏 | **分层 FNR** + 准入集大小 | 🟡 CRC + 分层 FNR，CPU 验证；真实图待 GPU |
| Ch2 | raw→repaired→+准入 三档可重建 | 修复帮到结构 | **ECG R1 可达 / R2 保真** | 🟡 `succession/reconstruction`，CPU 验证；真实图待 GPU |
| Ch3 | gold 输入 vs 预测图输入 | 预测图鲁棒性（delta①） | macro-F1 **掉点** | ⬜ Phase D |
| Ch3 | ± 结构（论元+关系）特征 | 结构对检测的作用 | macro-F1 | ⬜ |
| Ch3 | ± 事实性净化 | 净化换下游增益（delta②） | 下游 **MRR** 前后 | ⬜ |
| Ch4 | gold / predicted / repaired 三图 | 误差传播 + 修复有效 | **MRR/Hits** 三图对比 | 🟡 受控扫描有、真实图待A/B |
| Ch4 | ± 下游门控（只在MRR↑才接受编辑） | 治 self-refine 掉点 | vs 无门控 self-refine | ⬜ 控制器待建 |
| Ch4 | M1 / M2 / M3 逐个 | 各机制增量 | ΔMRR / risk-coverage | ✅ M1/M2/M3a 已跑 |
| Ch4 | naive vs 预算法 vs 条件回收 | reachability 预算价值 | 覆盖 + 集大小 | ✅ 受控扫描已跑 |

> 已跑结论（如实、含负结果）：**M1（BFS 选边）+0.005 噪声级；M2（reach_anchor）−0.0015 持平=负结果；
> M3a 同覆盖集缩 43–68%（有价值）；M3b 受控扫描预算法守覆盖**。真实三图闭环待 Phase A/B 解堵。

## 4. 报数规范（主表/消融统一口径）

- **指标**：Ch1 检测 micro-F1、共指 MUC/B³/CEAFe/CoNLL、论元 F1、`node_confidence` ECE；
  Ch2 per-relation P/R/F1 + doc-macro-F1、violation/cycle 率、分层 FNR；
  Ch3 5 类 macro-F1 + evidence span F1；Ch4 **MRR/Hit@k**（同报乐观[SeDGPL 口径]与 `mrr_strict`）+ risk-coverage。
- **多种子**：seeds 13/17/42，主结果先单种子跑通，`mean±std` 放 Phase H。
- **协议声明模板**（每章方法部分必写）：数据集 + split 来源 + 报数用 test/valid（引用本文件 §1 对应档）
  + 是否 CodaLab + 词表/切分泄漏澄清。
- **产物落盘**：`runs/<域>/<方法>_<配置>.json`，含配置、指标、n、种子；写入 `TODO.md`。

## 5. 防审稿：与最近竞品的显式区分（详见 SPEC §5）

投稿相关工作**必逐条区分**下列已核实竞品（否则"具体组合"的窄 delta 立不住）：

| 竞品 | 编号 | 它做了什么 | v4 的区分点 |
|---|---|---|---|
| PASC | 2605.18812 | pipeline 联合覆盖，统一 nonconformity | **不碰** reachability/异质保证/drift/条件回收（四点全无）|
| SCRC | 2512.12844 | 单模型 selective + CRC | 不碰 pipeline/跨阶段；**只撞名 → CS-CRP 须改名** |
| C-RAG | 2402.03181 | RAG 生成风险 conformal 上界 | 生成风险非"构建边准入 recall + 下游 reachability" |
| CASCADE | 2605.20468 | 两阶段临床区间，上游不确定性传播 | 医疗回归区间，非事件图/reachability |
| **DeepRefine** | **2605.10488** | **下游导向 KB 精化 + 无 gold GBD 奖励 RL + downstream gains** | **通用 KB 非事件因果图；RL 无覆盖保证；无 reachability/三图误差分解**（★最近威胁，2026-05）|
| MedCEG | 2512.13510 | 结构/因果图作 RLVR 奖励 | 结构作奖励**非新** → RL-reward 仅作消融、**不写"首次"** |

**口径**：一律"据我们所知"+显式区分先例，不写全球首创；headline claim 收窄为
**"事件因果图上、带 reachability 与 conformal 误差预算的下游门控修复"**（区别于 DeepRefine 的通用 KB RL 精化）。
