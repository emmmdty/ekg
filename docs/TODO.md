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

| 章 | 指标 | 同底座官方基线<br>(test) | 同输入 SOTA<br>RESIJ(Trigger)@test | 我们<br>(valid) | 表观缺口 |
|---|---|---|---|---|---|
| Ch1 | coref MUC F1 | **81.4** ±0.51（+joint 82.1） | 82.5 | **79.6** | −1.8 |
| Ch1 | 难例误合并率 | 无官方对标 | — | .767 → **.116** | ✅ 6.6×（自建基线） |
| Ch2 | causal pair F1 | **30.6** ±0.44（+joint 31.5） | 34.8 | **25.0** | −5.6 |
| Ch2 | subevent pair F1 | **26.7** ±1.34（+joint 27.5） | 30.8 | **21.3** | −5.4 |
| Ch2 | temporal pair F1 | 55.8 ±0.42 | 59.0 | 33.8 | 🛑 **不可比，见下** |
| Ch3 | 事实性 macro-F1 | DMRoBERTa **47.1** / RoBERTa+CLS 45.4 | DMBERT 47.6 | **48.2** | ✅ +1.1（跨 split） |
| Ch3 | evidence macro(3 类) | DMRoBERTa **45.4** | — | **61.4** | ✅ |
| Ch4 | CGEP-MAVEN MRR | 无可比（SeDGPL 的 MAVEN 构建未发布） | — | 自跑 .1836 | 只能自比 |

**「表观缺口」三个字是认真的——直接相减不成立，三条修正**（详见 [`EXPERIMENTS.md`](EXPERIMENTS.md) Ch2 段）：

1. 🛑 **temporal 两边不是同一个任务**：原始 MAVEN-ERE 的 temporal 有 **39% 触及 TIMEX**（事件–时间
   表达式），我们的 loader 因 `representative` 查不到 TIMEX id 而**静默丢弃**。causal/subevent 的
   TIMEX 占比是 0%，那两条口径干净。
2. ⚠️ **dev 明显低于 test**：RESIJ 自己 dev 比 test 低 causal −3.7 / temporal −6.4 / subevent −4.4 /
   MUC −4.5。**我们报 valid、官方报 test**，所以 −5.6 是被高估的；按同幅度外推 causal 实际约 −1.9
   （**外推，非实测**）。
3. ⚠️ **37.4 不是我们的天花板**：那是 RESIJ-One(**Full**)，用了 AMR 抽的跨句隐式论元；我们和 Ch4 的
   CGEP 都是纯触发词 ⇒ 同输入的 SOTA 是 **34.8**。

- 来源：Ch1/Ch2 官方基线 = MAVEN-ERE EMNLP 2022 Table 7/8；SOTA = IPM 2024 (103811) Table 2/4
  （**两处对官方基线的引用逐格一致，交叉验证通过**）；Ch3 = MAVEN-FACT 2407.15352 Table 3/4。三处均已回一手 PDF 核。

## 阶段状态

| 阶段 | 状态 | 一句话结论 | 档案 |
|---|---|---|---|
| P0 | ✅ | 主数据 hash/manifest 可核；扩展数据部分仅 raw | [`DATASETS.md`](DATASETS.md) |
| A | 🟢 | **根因=跨句表示隔离**（按句编码 vs 官方多句拼窗口）+ 漏配 warmup/decay；修复后 causal 23.91→**28.20**、temporal→**32.43**，与官方 31.37 差距 7.46→**3.17**；❌ subevent 反降至 19.65 | [`results/PHASE_A.md`](results/PHASE_A.md) |
| B | 🟡 | 结构违反**清零**✅，ECG 可重建率**无增益**❌；α=0.2 因召回上限**不可达** | [`results/PHASE_B.md`](results/PHASE_B.md) |
| C | ⚠️ | 难例误合并 6.6×✅、ECE ✅；MUC 79.6 **低于官方 81.4**；换底座三次全败 | [`results/PHASE_C.md`](results/PHASE_C.md) |
| D | 🟡 | 检测 **超官方同底座档**✅、预测图掉点 ±.0001 ✅；净化**结构+下游双负**❌ | [`results/PHASE_D.md`](results/PHASE_D.md) |
| E | 🟢 | 三图分解完成：构建损失 **−.0218 是唯一确凿效应**；图侧干预全在噪声地板内 | [`results/PHASE_E.md`](results/PHASE_E.md) |
| C2 | ⬜ | 跨文档泛化未开始（ECB+ raw 已有，CLES 未取） | [`phases/PHASE_C2_ch1_crossdoc.md`](phases/PHASE_C2_ch1_crossdoc.md) |
| F | ⬜ | 端到端预算；**暂缓**——风险地板 .2935 由 Ch2 召回决定，Ch2 不抬则 F 只是重述地板 | [`phases/PHASE_F_end2end_budget.md`](phases/PHASE_F_end2end_budget.md) |
| H | ⬜ | 多种子 + 消融 + 新颖性扫；**等一个值得背书的结果** | [`phases/PHASE_H_robustness_novelty.md`](phases/PHASE_H_robustness_novelty.md) |
| ~~G~~ | ❌ | 金融应用层 2026-07-27 移出 | [`ARCHIVE_INDEX.md`](ARCHIVE_INDEX.md) |

## 下一步

1. **⭐ 队首 = Phase A2：按官方配方重训 Ch2 抽取器**
   —— 契约与交接见 [`phases/PHASE_A2_ch2_official_recipe.md`](phases/PHASE_A2_ch2_official_recipe.md)。
   🛑 CodaLab 通道 2026-07-30 已关，官方 test 分拿不到，**不再产提交件**。
   唯一可比的尺是「**官方 `evaluate.py` 打 valid**」，脚本已就位（`scripts/score_maven_ere_official.py`）。
   我们的架构与官方基线本就是同一个（RoBERTa-base 成对分类）。**四条候选解释已逐条排除**
   （数字与推导全在 `results/PHASE_A.md`，此处只记结论）：
   - ❌ **训练配方**（负采样/类权重/学习率/epoch）：2026-08-02 50ep 全量跑完，causal 22.26 < 现役档。
   - ❌ **跨 split 假象 / 候选 population 不一致**：2026-08-02 跑**官方原版代码在我们同一份 valid**
     上得 **causal 31.37**（P31.03/R31.72，比论文 test 的 30.6 还高）⇒ 两条同时排除。
   - ❌ **`--neg-ratio 30` 的下采样**：2026-08-06 实测**它从未生效**（正例 20.44%，实际负正比 3.9:1
     < 阈值 30:1）⇒ neg30 与 inf 训练集逐行相同，契约「四处差异」的第一条**不存在**。
   - ❌ **架构**（span mean-pooling + MLP 头，`43e62df`）：2026-08-06 在现役档配方下做单变量对照，
     **causal 23.91→24.06（+0.15，噪声级）、subevent 24.03→22.56（−1.47）**⇒ **架构假设证伪**，
     与官方 31.37 的 **7.31 点差距仍未解释**。
   **⇒ ✅ 2026-08-07 找到真正的根因并修复：不在模型，在编码粒度。**
   克隆官方仓库逐行读 `causal/src/data.py` 发现：官方**把多句拼进一个 `<=max_length` 窗口一次前向**，
   我们是**每句独立一次前向** ⇒ **68.8% 的 causal / 85.8% 的 subevent 是跨句对**，
   它们的两个表示**从未在同一张 attention 图里出现过**。这解释了此前所有改动为何无效
   （缺陷在输入表示，改下游补不回来）。
   修复（`abbdbfd` 文档窗口编码）后，官方口径 valid：
   **causal 24.06→26.95（+2.89）、temporal 23.06→28.40（+5.34）**，与官方 31.37 的差距 **7.31→4.42**。
   **机制已验证**：分层诊断显示增益全在跨句（19.99→**24.11**，+4.12），同句 −1.13。
   **2026-08-07 续**：又查出**一直漏配官方的 warmup+linear decay**（`--warmup-steps` default 0，
   scheduler 只在 >0 时创建）——所有既有档都是恒定 lr。补上并对齐官方 lr（1e-5/1e-4）+ 20ep +
   held-out dev best 选择后：**causal 28.20 / temporal 32.43**，与官方差距 **7.46→3.17**。
   ⇒ **下一步（按证据排序）**：
   ① 🛑 **subevent 从 24.03 跌到 19.65 必须先解**——怀疑 dev 选择信号是三族合并 micro F1、
      被 temporal（pair 数 39×）主导，待验证的修法是按族选 checkpoint 或用宏平均信号；
   ② **跨句仍是主瓶颈**（24.17 vs 同句 38.07），且**窗口编码之后三轮优化都没能再推动它**；
   ③ 梯度累积已实现未验证（官方 batch 8，我们逐文档=batch 1；且这让 warmup 200 只等于 200 篇
      而非官方的 1600 篇）；④ 事件类型 embedding（⚠️ 词表须随 checkpoint 存）。
   ⛔ 已排除：负采样、类权重方向、span pooling/MLP 头、重叠滑窗（causal 仅 3.3% 跨窗）。
2. **我们在官方口径 valid 上的真实数字**（2026-07-30，官方 `evaluate.py`，710 篇）：
   **causal F1 23.91**（P 23.96 / R 23.86）、**subevent 24.03**（P 20.45 / R 29.14）、
   **temporal 22.25**（P 42.59 / **R 15.06** ← 缺 TIMEX 头的量化证据）、
   coref MUC 45.83（词形兜底档；supervised 档回传中）。
   ⚠️ 这组数**不能**直接跟官方论文的 test 数（30.6/26.7/55.8/81.4）相减 —— 见「对标与达成度」三条修正。
3. **Ch1 MUC 缺口同源**：缺口全在 recall（80.8 vs 84.0），官方归因于四关系联合建模。
   与第 1 条指向同一个技术动作，**做完 Ch2 再回头，不要并行开两条**。
4. **暂缓 Phase F 与 Phase H**（理由见阶段状态表）。
5. 每章开跑前照 [`EXPERIMENTS.md`](EXPERIMENTS.md) 定 baseline + 消融矩阵 + 评测档。
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
