# EKG · 实时状态

> 更新于 **2026-07-29**。本文件**只记录当前位置、对标缺口、下一步、止损**，不存实测细节。
> 设计总纲 → [`SPEC.md`](SPEC.md)｜阶段契约 → [`phases/`](phases/README.md)｜
> **各阶段实测档案 → [`results/`](results/)**｜baseline 与消融矩阵 → [`EXPERIMENTS.md`](EXPERIMENTS.md)｜
> 归档索引 → [`ARCHIVE_INDEX.md`](ARCHIVE_INDEX.md)。
>
> **单一事实源规则**：每个实验数字**只在 `results/PHASE_X.md` 里权威**。本文件与 `EXPERIMENTS.md`
> 只引用不复制；发现两处不一致，以 `results/` 为准并立刻改另一处。

## 当前结论

- **唯一主线**：v4 四章可信事件图谱构建（身份 → 结构 → 事实 → 传播/下游），headline 是 Ch4
  **构建误差向下游的传播、归因与预算**（2026-07-29 作者拍板重定位；修复/门控降为**被测量的干预**）。
- **Phase A–E 已全部跑完**，唯一确凿的效应是**构建损失本身**（gold→predicted，ΔMRR −.0218）；
  修复、净化、M1、M2、选边策略在下游**全部落在噪声地板内**（实测 ±.003–.004）。
- **⚠️ 2026-07-29 核出的关键缺口**：我们**没有一章达到同底座官方基线**（见下「对标与达成度」）。
  Phase A 的「达标」是对着自设的 ≥.25，不是对着官方 RoBERTa-base 的 30.6。
- **多种子推迟**：多种子是给好结果背书的，不是给平结果盖章。**先做出超过官方基线的结果，再多种子**。

## 对标与达成度（★ 定方向唯一依据，数字须回一手表格核）

| 章 | 指标 | 同底座官方基线 | 公开 SOTA | 我们 | 缺口 |
|---|---|---|---|---|---|
| Ch1 | coref MUC F1 | **81.4** ±0.51（+joint 82.1） | 86.1 | **79.6** | **−1.8** |
| Ch1 | 难例误合并率 | 无官方对标 | — | .767 → **.116** | ✅ 6.6×（自建基线） |
| Ch2 | causal pair F1 | **30.6** ±0.44（+joint 31.5） | 37.4 | **25.0** | **−5.6** |
| Ch2 | subevent pair F1 | **26.7** ±1.34（+joint 27.5） | 32.9 | **21.3** | **−5.4** |
| Ch2 | temporal pair F1 | **55.8** ±0.42（+joint 56.0） | 60.7 | **33.8** | **−22.0** |
| Ch3 | 事实性 macro-F1 | DMRoBERTa **47.1** / RoBERTa+CLS 45.4 | DMBERT 47.6 | **48.2** | ✅ **+1.1**（⚠️ 官方 test / 我们 valid） |
| Ch3 | evidence macro(3 类) | DMRoBERTa **45.4** | — | **61.4** | ✅ |
| Ch4 | CGEP-MAVEN MRR | 无可比（SeDGPL 的 MAVEN 构建未发布） | — | 自跑 .1836 | 只能自比 |

- Ch1/Ch2 官方基线取自 **MAVEN-ERE 原论文 Table 7/8**（EMNLP 2022，RoBERTa-base，报在 **test**）；
  2026-07-29 已回一手 PDF 核，**替换了此前错误的「MUC ~86」验收线与缺数字的 causal 行**。
- Ch3 官方数取自 **MAVEN-FACT（arXiv 2407.15352）Table 3/4**，2026-07-28 已回一手核。
- ⏳ **待核**：SOTA 行（graph propagation，IPM 2024）的 split 未从一手确认（ScienceDirect 付费墙）。

## 阶段状态

| 阶段 | 状态 | 一句话结论 | 档案 |
|---|---|---|---|
| P0 | ✅ | 主数据 hash/manifest 可核；扩展数据部分仅 raw | [`DATASETS.md`](DATASETS.md) |
| A | ⚠️ | 判别式解了召回（causal .4%→67.5%、`hallucinated=0`），但 F1 **低于官方同底座基线 5.6 点** | [`results/PHASE_A.md`](results/PHASE_A.md) |
| B | 🟡 | 结构违反**清零**✅，ECG 可重建率**无增益**❌；α=0.2 因召回上限**不可达** | [`results/PHASE_B.md`](results/PHASE_B.md) |
| C | ⚠️ | 难例误合并 6.6×✅、ECE ✅；MUC 79.6 **低于官方 81.4**；换底座三次全败 | [`results/PHASE_C.md`](results/PHASE_C.md) |
| D | 🟡 | 检测 **超官方同底座档**✅、预测图掉点 ±.0001 ✅；净化**结构+下游双负**❌ | [`results/PHASE_D.md`](results/PHASE_D.md) |
| E | 🟢 | 三图分解完成：构建损失 **−.0218 是唯一确凿效应**；图侧干预全在噪声地板内 | [`results/PHASE_E.md`](results/PHASE_E.md) |
| C2 | ⬜ | 跨文档泛化未开始（ECB+ raw 已有，CLES 未取） | [`phases/PHASE_C2_ch1_crossdoc.md`](phases/PHASE_C2_ch1_crossdoc.md) |
| F | ⬜ | 端到端预算；**暂缓**——风险地板 .2935 由 Ch2 召回决定，Ch2 不抬则 F 只是重述地板 | [`phases/PHASE_F_end2end_budget.md`](phases/PHASE_F_end2end_budget.md) |
| H | ⬜ | 多种子 + 消融 + 新颖性扫；**等一个值得背书的结果** | [`phases/PHASE_H_robustness_novelty.md`](phases/PHASE_H_robustness_novelty.md) |
| ~~G~~ | ❌ | 金融应用层 2026-07-27 移出 | [`ARCHIVE_INDEX.md`](ARCHIVE_INDEX.md) |

## 下一步

1. **⭐ 队首 = Ch2 pair-classification 打到官方基线**（causal 25.0 → 30.6）。
   理由：它同时卡住 Ch2 自己的对标**和** Ch4 的天花板（R2 f1 仅 .077、风险地板 .2935 都是它的后果），
   而联合建模在官方表里只值 +0.9（30.6→31.5）——**先补上 5.6 的基线差，再谈联合建模**。
   线索：官方 **P 35.0 / R 27.2**（precision 主导），我们召回 67.5% 而 precision 崩；官方整篇编码后
   直接对事件对分类、**未做负采样**，我们用了 neg-ratio 30 + 逆频加权 CE(α=0.5)，方向正好相反。
   ⇒ 首个假设：**Phase A 的类不平衡处理就是 precision 崩的原因，那轮 α 扫描是在错误设定里找局部最优**。
   开跑前先核 SOTA 行的 split（见上「待核」），并按官方附录 C 对齐实现细节。
2. **Ch1 MUC 缺口同源**：缺口全在 recall（80.8 vs 84.0），官方归因于四关系联合建模。
   与第 1 条指向同一个技术动作，**做完 Ch2 再回头，不要并行开两条**。
3. **暂缓 Phase F 与 Phase H**（理由见阶段状态表）。
4. 每章开跑前照 [`EXPERIMENTS.md`](EXPERIMENTS.md) 定 baseline + 消融矩阵 + 评测档。
   **对标数字必须回一手表格核**——Phase C 因此白跑两轮、Phase A 的「达标」因此判错。

## 止损与人工判断

- **Ch2 打不到官方基线**：若复刻官方配方后 causal 仍 <28，说明差距不在类不平衡处理，
  转而核对候选构造与评测口径（是否同一 pair population），**不要继续扫超参**。
- ~~Ch3 净化无下游收益~~ **✅ 2026-07-29 完整触发**：可部署档 −.0001、**oracle 金标档 −.0000**
  （oracle 即天花板 ⇒ 检测器再好也救不活）。Ch3 已按口径退为「事实性检测 + 预测图鲁棒性分析」，
  **不得再把净化写成图质量方法**。
- ~~Ch4 repaired 不优于 predicted~~ **✅ 2026-07-28 触发，07-29 据此重定位 headline**：
  已退为误差传播与归因，未更换指标，负结果全部保留在正文。
- **图侧干预的正面主张**：噪声地板实测 ±.003–.004（配对 bootstrap）与 −.0029（重训波动）。
  **任何小于该量级的增益，多种子之前不得作正面主张。**
- **方法学红线**：图与图的下游对比**必须用 canonical 模板序**——SeDGPL 按存储序截断，
  实测纯重新序列化能造出 p=.02 的假效应。沿用存储序的图对比表一律不可信。
- **门控档（若还要做）**：信号**禁用金标 MRR**（SPEC §4.5 的 oracle 泄漏），且只施于 causal 环破除；
  其余修复动作对下游按构造零影响，门控它们是空转。
- **新颖性**：发现 CS-CRP/reachability 组合有直接先例时，重新限定或改名，**不写「首次」**。
