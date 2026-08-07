# EKG · 实时状态

> 更新于 **2026-08-07**。本文件**只记录当前位置、对标缺口、下一步、止损**，不存实测细节。
> 设计总纲 → [`SPEC.md`](SPEC.md)｜阶段契约 → [`phases/`](phases/README.md)｜
> **各阶段实测档案 → [`results/`](results/)**｜baseline 与消融矩阵 → [`EXPERIMENTS.md`](EXPERIMENTS.md)｜
> 归档索引 → [`ARCHIVE_INDEX.md`](ARCHIVE_INDEX.md)。
>
> **单一事实源规则**：每个实验数字**只在 `results/PHASE_X.md` 里权威**。本文件与 `EXPERIMENTS.md`
> 只引用不复制；发现两处不一致，以 `results/` 为准并立刻改另一处。

## 当前结论

> **2026-08-07 作者重定标尺**：这是**学位论文**，及格线不是「超过 SOTA」，是**每一章都要在公开可比的
> 主指标上超过多个（不是一个）经典或近年方法**。「不用超 SOTA」≠「不用超 baseline」——
> 超过 baseline 就是「我的方法有效」这句话唯一的兑现方式。

- **按新标尺，现状是 1/4 过线**：Ch3 事实性 48.2 已超四个公开方法（DMBERT 47.6 / DMRoBERTa 47.1 /
  RoBERTa+CLS 45.4 / GPT-4 42.8）；Ch1 共指 77.47、Ch2 causal 28.50 / subevent 21.05 **均低于**
  同底座官方基线与 2025 年方法。**低于四年前的基线时，方法章的贡献为零。**
- **六个自研机制在下游全部零效应**（一致解码修复 / CRC 准入 / 事实性净化 / 图侧选边 / M1 / M2），
  且是**构造性的零**而非没调好：净化用金标 oracle 标签仍 −.0000、`repaired_nobreak` 与 `predicted`
  逐位相同。⇒ 它们**不再作为方法卖点**，全部降级为 Ch4 归因章的证据。
- **★ 项目当前最有价值的资产 = 一个与 ACL 2025 正面冲突的严谨负结果**：Koupaee et al.（ACL 2025）
  证明「更好的因果图 → 下游大幅提升」（叙事完形 13.0→55.0），我们实测「更好的图 → 下游零变化」。
  **可检验的解释：图质量的下游收益依赖消费者类型**——他们是 in-context LLM（图即推理基底），
  我们是微调 SeDGPL（会学会绕过图噪声）。这是 Ch4 的核心命题，**是假设不是结论**。
- **多种子推迟**：多种子是给好结果背书的，不是给平结果盖章。**先做出超过公开基线的结果，再多种子**。

## 对标与达成度（★ 定方向唯一依据，数字须回一手表格核）

| 章 | 指标 | 同底座官方基线<br>(test) | 同输入 SOTA<br>RESIJ(Trigger)@test | 我们<br>(valid) | 表观缺口 |
|---|---|---|---|---|---|
| Ch1 | coref MUC F1 | **81.4** ±0.51（+joint 82.1） | 82.5 | **77.47** | −3.9 |
| Ch1 | 难例误合并率 | 无官方对标 | — | .767 → **.116** | ✅ 6.6×（自建基线） |
| Ch2 | causal pair F1 | **30.6** ±0.44（+joint 31.5） | 34.8 | **28.50** | **−2.87**（对 31.37，见下★） |
| Ch2 | subevent pair F1 | **26.7** ±1.34（+joint 27.5） | 30.8 | **21.05** ⚠️ | 仍低于起点 24.03，见 `results/PHASE_A.md` |
| Ch2 | temporal pair F1 | 55.8 ±0.42 | 59.0 | 31.55 | 🛑 **不可比，见下** |
| Ch3 | 事实性 macro-F1 | DMRoBERTa **47.1** / RoBERTa+CLS 45.4 | DMBERT 47.6 | **48.2** | ✅ +1.1（跨 split） |
| Ch3 | evidence macro(3 类) | DMRoBERTa **45.4** | — | **61.4** | ✅ |
| Ch4 | CGEP-MAVEN MRR | 无可比（SeDGPL 的 MAVEN 构建未发布） | — | 自跑 .1836 | 只能自比 |

★ **Ch2 那三行 2026-08-07 换成了官方 `evaluate.py` 口径**（此前是 Phase A 的内部口径
25.0/21.3/33.8，与官方口径**不可比**，属口径混用，已更正）。**Ch2 真正可比的尺不是表里的
test 列，而是「官方原版代码在我们同一份 valid 上」跑出的 causal 31.37**——同 split、同评测器、
同数据，唯一变量是训练代码。所以 causal 的真实缺口是 **−2.87**，不是对 test 的 −2.1。

★★ **Ch1 那行 2026-08-07 从 79.6 改为 77.47（同一类口径混用，晚了一轮才发现）**。
79.6 是**内部评测器 + 497 篇 valid 子集 + ERE 人群校正**的数，拿它去和官方评测器 @test 的 81.4
相减，三条轴同时不同。权威口径见 [`results/PHASE_C.md`](results/PHASE_C.md) 第 219 行原文
「**应以 77.47 为准**：全量、官方评测器、无自定校正」。**79.6 此后只许出现在内部消融，
不得进任何对外表格。**

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

### ★ 首个同 split 外部对照：MAQInstruct（2026-08-07 回一手核）

`MAQInstruct`（arXiv 2502.03954，2025）原文写 **"since MAVEN-ERE does not have an open test set,
we chose to use the validation set for testing"** —— 与我们同 split。这条同时说明
**「valid 当 test」有 2025 年的先例**，不只是 SeDGPL 一家，写作时不再是把柄。

| 方法 | split | coref MUC | temporal | causal | subevent |
|---|---|---|---|---|---|
| BertERE（判别式基线） | valid | 79.8 | 52.1 | 30.9 | 23.7 |
| MAQInstruct-Llama2 | valid | 80.2 | 53.8 | **32.5** | **25.2** |
| **我们（`window_dist_20ep_macro`）** | valid | 77.47 | 31.55🛑 | **28.50** | **21.05** |

**分栏裁决（必须遵守，两栏可信度不同）**：

- ✅ **关系栏可用**：论文未声明评测脚本，但有独立佐证——我们自跑**官方原版代码**在同一份 valid 上得
  causal **31.37**，其 BertERE 得 **30.9**，两个对同一官方基线的独立复现差 0.5 ⇒ 协议大概率一致。
  **同 split 缺口：causal −4.0 / subevent −4.2（对 MAQInstruct-Llama2）。**
- 🛑 **共指栏不可用，不得进主表**：指标定义已核清是 **MUC 单指标**（原文 B³/CEAFe/MUC/BLANC 四列分列），
  但**评测脚本、mention 来源（gold 还是预测）、valid 篇数全部未声明**。且有反证：按 RESIJ 实测
  「dev 比 test 低 4.5 MUC」外推，dev 应在 **76.9** 左右——**我们的 77.47 恰好落在外推值上，
  他们的 79.8 高出近 3 点** ⇒ 两边协议大概率不同。Ch1 的锚仍是官方 81.4@test。

## 阶段状态

| 阶段 | 状态 | 一句话结论 | 档案 |
|---|---|---|---|
| P0 | ✅ | 主数据 hash/manifest 可核；扩展数据部分仅 raw | [`DATASETS.md`](DATASETS.md) |
| A | 🟢 | **两个根因：跨句表示隔离 + 漏配 warmup/decay**（均由读官方一手代码定位）；causal 23.91→**28.50**、temporal→**31.55**，与官方 31.37 差距 7.46→**2.87**；⚠️ subevent 21.05 仍低于起点 24.03 | [`results/PHASE_A.md`](results/PHASE_A.md) |
| B | 🟡 | 结构违反**清零**✅，ECG 可重建率**无增益**❌；α=0.2 因召回上限**不可达** | [`results/PHASE_B.md`](results/PHASE_B.md) |
| C | ⚠️ | 难例误合并 6.6×✅、ECE ✅；MUC **77.47** 低于官方 81.4（缺口全在 recall＝欠并）；换底座三次全败 | [`results/PHASE_C.md`](results/PHASE_C.md) |
| D | 🟡 | 检测 **超官方同底座档**✅、预测图掉点 ±.0001 ✅；净化**结构+下游双负**❌ | [`results/PHASE_D.md`](results/PHASE_D.md) |
| E | 🟢 | 三图分解完成：构建损失 **−.0218 是唯一确凿效应**；图侧干预全在噪声地板内 | [`results/PHASE_E.md`](results/PHASE_E.md) |
| **A2** ⭐ | 🟢 | **Ch2 队首**；及格线改为超 MAQInstruct 32.5/25.2，剩梯度累积/类型 embedding/TIMEX 头 | [`phases/PHASE_A2_ch2_official_recipe.md`](phases/PHASE_A2_ch2_official_recipe.md) |
| **C3** | ⬜ | **Ch1 新建**：非对称代价修欠并（欠并比过并贵 2.3–3.9×，实测） | [`phases/PHASE_C3_ch1_asymmetric_cost.md`](phases/PHASE_C3_ch1_asymmetric_cost.md) |
| **D2** | ⬜ | **Ch3 新建**：跨数据集泛化，堵「冷门数据集」质疑 | [`phases/PHASE_D2_ch3_cross_dataset.md`](phases/PHASE_D2_ch3_cross_dataset.md) |
| **E2** | ⬜ | **Ch4 新建（headline）**：加 in-context 消费者臂，验消费者依赖性 | [`phases/PHASE_E2_ch4_consumer_dependence.md`](phases/PHASE_E2_ch4_consumer_dependence.md) |
| C2 | ⬜ | 跨文档泛化未开始（ECB+ raw 已有，CLES 未取）；**Ch1 可选加分项，不在关键路径** | [`phases/PHASE_C2_ch1_crossdoc.md`](phases/PHASE_C2_ch1_crossdoc.md) |
| ~~F~~ | ❌ | 端到端预算；v5 中**并入 E2 的可靠性模块**，独立 phase 取消 | [`ARCHIVE_INDEX.md`](ARCHIVE_INDEX.md) |
| H | ⬜ | 多种子 + 消融 + 新颖性扫；**等各章过线** | [`phases/PHASE_H_robustness_novelty.md`](phases/PHASE_H_robustness_novelty.md) |
| ~~G~~ | ❌ | 金融应用层 2026-07-27 移出 | [`ARCHIVE_INDEX.md`](ARCHIVE_INDEX.md) |

> A–E 五行是**已完成/已止损的 v4 阶段**，契约已归档，实测数字仍以 `results/` 为准。
> A2/C3/D2/E2 是 **v5 的四条活线**，**A2/C3/D2 可并行**（不共享代码域）。

## 下一步

1. **⭐ 队首 = Ch2 关系抽取（`PHASE_A2` 续）**——推导与全部数字见
   [`results/PHASE_A.md`](results/PHASE_A.md)「Phase A2 总账」，本表只记状态与动作。
   **两个根因已定位并修复**（都靠读官方一手代码，都不是超参）：① 跨句表示隔离（我们按句编码、
   官方多句拼窗口）；② 漏配 warmup + linear decay。causal **23.91→28.50**，缺口 7.46→**2.87**。
   ⛔ **已排除、不要再扫**：负采样、类权重、学习率、epoch 数、span pooling/MLP 头、
   重叠滑窗（causal 仅 3.3% 跨窗）、跨 split 假象、候选 population。
   ⇒ **剩余动作（按证据排序）**：
   ① **梯度累积**（已实现未验证，唯一有机制论证的剩余官方差异：官方 batch 8 / 我们逐文档=batch 1，
      这让 warmup 200 只等于 200 篇而非官方的 1600 篇）；
   ② ⚠️ **subevent 21.05 仍低于起点 24.03**，且低于 MAQInstruct 25.2 —— **本章过线的硬约束**；
   ③ **跨句仍是主瓶颈**（25.00 vs 同句 38.18，只被窗口编码推动过一次）；
   ④ 事件类型 embedding（⚠️ 词表须随 checkpoint 存）；⑤ TIMEX 头（否则 temporal 永远是空格）。
   **及格线不再是追平 31.37**（那只是追平官方基线＝零贡献），是**超过 MAQInstruct-Llama2 的
   causal 32.5 / subevent 25.2**（2025，同 split）。
2. **Ch1 队列（`PHASE_C3`，与第 1 条可并行——两条不共享代码域）**：缺口全在 MUC recall
   （82.56 vs 84.0）＝**欠并**。抓手是**非对称代价**：Phase E 实测拆节点 −.0184 是等幅删边
   （−.0081）的 2.3 倍、等幅增边（−.0047）的 3.9 倍 ⇒ 欠并比过并贵 2.3–3.9 倍，
   损失与聚类阈值**不该对称**。⛔ 不再换底座（longformer −2.5 / large −2.8 已实测）。
   及格线 77.47 → 追平官方 81.4 口径，目标 82+。
3. **Ch3 队列（`PHASE_D2`）**：本章**已过线**（48.2 超四个公开方法），缺的是**跨数据集验证**
   （FactBank / UW / MEANTIME）以回应「MAVEN-FACT 竞品少、超过它意义存疑」。
   ⛔ 净化线已止损，不得复活。
4. **Ch4 队列（`PHASE_E2` 消费者依赖性）**：给现有三图对比**加一条 in-context 消费者臂**，
   与微调 SeDGPL 臂并列，检验「图质量收益依赖消费者类型」这个假设。
   对标收敛到**叙事完形**（ELM 46.0 / EGELM 50.0 / QGELM 46.0 / one-shot 13.0 / CGEL 55.0，
   Koupaee et al. ACL 2025 Table 6）+ **CRAB** 图质量内在评测。
   🛑 **不碰 ForecastQA**——需 MDS 摘要流水线 + GPT-4o，我们跑不动，硬比是不公平对照。
   ⚠️ 消费者模型受 5090 单卡限制（Qwen/Llama 7–14B 量级），**不与 GPT-4o 档直接相减**。
5. 每章开跑前照 [`EXPERIMENTS.md`](EXPERIMENTS.md) 定 baseline + 消融矩阵 + 评测档。
   **对标数字必须回一手表格核**——Phase C 白跑两轮、Phase A「达标」判错、
   2026-08-07 Ch1 对标行混用 79.6/77.47，**三次都是同一个错**。

## 止损与人工判断

- ~~**Ch2 打不到官方基线**（原线：causal 仍 <28 则转核候选构造）~~ **✅ 2026-08-07 已越过**
  （28.50）。**新止损线**：若梯度累积 + 事件类型 embedding 两项做完 causal 仍 <31.37，
  说明剩余差距不在「官方有我们没有」的成分里，**停止 diff 官方实现**，转而承认追平不可达、
  把本章的贡献收缩到**跨句分层诊断框架**（那是我们独有、且别人没分层报过的东西）。
- **★ Ch4 消费者依赖性假设的止损**：若 in-context 消费者臂上图质量干预**同样**落在噪声地板内，
  则「收益依赖消费者类型」这个解释被证伪。**那时不得改指标硬凑**——正确的落点是转向
  「图精化的下游收益在何种条件下不存在」的边界刻画，并**如实报告与 ACL 2025 冲突且我们无法解释**。
  这仍是可发表的结论（KGrEaT CIKM'23 正是在呼吁这类评估），但必须停止把它当正面主张。
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
