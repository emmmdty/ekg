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

1. **⭐ 队首 = 提交 CodaLab 拿官方 test 分**（操作说明见 [`CODALAB.md`](CODALAB.md)）。
   理由：现在**缺口有多大根本不知道**——我们报 valid、官方报 test，而这个数据集 dev 比 test 低
   3.7–6.4 点。不先把口径拉平，「补 5.6 点」这个目标本身就可能是假的。主表本来也要这个数
   （[`EXPERIMENTS.md`](EXPERIMENTS.md) §1 档 A：Ch2 关系主表首选官方 test）。
   ⚠️ 提交需要先补两件代码：**test 只给扁平 `event_mentions`、不给共指簇**，所以要把 Ch1 的共指
   与 Ch2 的关系抽取**首次端到端接起来**；且 temporal 要预测 event–TIMEX 对，我们的抽取器没有这个头
   —— **temporal 分会很低且不冤**，causal/subevent 才是这次要拿的数。
2. **然后才是 Ch2 打到官方基线**（causal 25.0 → 30.6，或 test 口径下的真实目标）。
   线索：官方 **P 35.0 / R 27.2**（precision 主导）、整篇编码后直接对事件对分类、**未做负采样**；
   我们召回 67.5% 而 precision 崩，用了 neg-ratio 30 + 逆频加权 CE(α=0.5)，方向正好相反。
   ⇒ 首个假设：**类不平衡处理本身就是 precision 崩的原因**，那轮 α 扫描是在错误设定里找局部最优。
   RESIJ 代码公开（`github.com/zjcerwin/RESIJ`）可对照实现细节；但其消融显示增益是 1–2 点的累加，
   **没有便宜的单点技巧可抄**。
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
