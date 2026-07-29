# Phase C 实测档案 · Ch1 规范事件节点

> 本文件是 **Phase C 的实测档案**：当时跑出的真实数字、口径、踩过的坑。
> 实时状态见 [`../TODO.md`](../TODO.md)，阶段契约见 [`../phases/`](../phases/README.md)。
> **数字以本文件为准**：TODO 与 EXPERIMENTS 只引用、不复制。

### Phase C 实施（2026-07-28，CPU 全链路跑通，**神经档待 GPU**）

**★ 先修正一个归因**：Phase B 报的 coref 族 FNR=1.000 **不是"模型没学会"，是结构性缺失** ——
`relations/extractor/supervised.py` 的 `FAMILY_SUBTYPES` 只覆盖 temporal/causal/subevent，
**抽取器根本没有 coreference 头**，`n_pred=0` 是按构造必然的。Ch1 正是补这一层。

代码（只增不改）：

- **MAVEN-Arg 加载器** `relations/data/maven_arg.py`：字符 offset 逐条校验 fail-fast
  （valid 全量 **0 失配**：16,996 触发词 / 46,458 论元 / entity 引用全解析），mention id 与
  MAVEN-ERE 共享（实测 99.78%），两套数据直接 join 无需映射表。
- **新包 `src/ekg/nodes/`**：`detection`（lexicon 记忆基线 + supervised 神经档）/ `coref`
  （同类型候选 + **难例负例**判别 + 采样）/ `canonical`（不确定性感知聚类 + 簇级证据/论元聚合 +
  簇置信）/ `metrics`（误合并率）/ `encoding`（滑窗字符 offset 池化；**定位逻辑纯 Python、CPU 可测**，
  堵住 Phase A 那类静默定位错）。
- **新核心原语** `core/calibration/probability.py`：isotonic 概率校准 + `reliability_curve`
  （既有 calibration 只有 conformal 风险控制，没有"分数→概率"的校准器）。
- 脚本：`build_canonical_nodes.py`（端到端报告）、`train_event_detector.py`、`train_coref_scorer.py`。
- 验证：**296 passed / 12 skipped**（基线 243/12）、ruff 0、`ekg-smoke` OK（新增 `[nodes]` 段）。

**CPU 基线真实数字**（lexical 触发词相似度判别器 + lexicon 检测器；valid 710 篇按 **Phase B 同一切分**
213 cal / 497 test —— gold 计数逐项与 Phase B 表相同：coref 2887 / temporal 71549 / causal 6599 /
subevent 2165，同一把尺）：

| 指标 | 值 | 目标 | 判定 |
|---|---|---|---|
| 检测 typed micro-F1 | **.687**（identification .781） | ~60+ | ⚠️ 见下方口径说明 |
| coref MUC / CoNLL | **.502 / .771**（最佳档） | MUC ~86 可比区间 | ❌ 差距大 |
| 误合并率 | **.582**（最佳档） | 显著↓ | ⚠️ 这是待打败的基线 |
| **难例**误合并率 | **.767**（n=3077 难例对） | 显著↓ | ⚠️ 同上 |
| coref 族 FNR | **1.000 → .398**（recall .602，天花板 .984）；**但 precision 仅 .389** | ↓ | ✅ 带代价 |
| `node_confidence` ECE | **.2477 → .0039**（校准后，n=9319 节点） | 报出 ECE | ✅ |

- ⚠️ **检测 .687 不等于达标**：这是 **候选分类口径**（MAVEN 直接给 gold 触发词 + `negative_triggers`
  候选集），比端到端触发词检测容易；且它只是**纯记忆 lexicon 基线**。说明 "~60+" 这个目标是照更难的
  口径定的。**神经检测器必须先超过这条记忆线才算有贡献**，不得拿 .687 宣称 Ch1 检测达标。
- ⚠️ **coref 族 FNR 的天花板是 .9837**：MAVEN-Arg 缺 1.63% 的 ERE gold coref 对（mention 不在 Arg 里），
  FNR 下界 .0163，报改善幅度时必须带这个天花板。
- ⚠️ **FNR 降下来是有代价的，两面都要报**：词形基线产 4,462 条 coref 边对 2,887 条 gold，
  **P .3893 / R .6017 / F1 .4727** —— 召回义的 FNR 改善真实，但 precision 很差。弃权带 .05 把
  P 抬到 .4144（R .5882、F1 .4863），是同一档里 F1 更优的点。**不得只报 FNR 不报 precision。**
- ✅ **弃权带（不确定性感知）按设计交易，且可测**：thr .90 下 band 0→0.05，难例误合并
  **.886→.780**、误合并 .611→.586，代价是 coref FNR .398→.412（215 次弃权）。thr 1.0 + band .05
  是退化角（全部弃权、FNR 回到 1.0），行为正确。
- 触发词相似度基线在所有阈值档误合并率都 ≥ .582、难例误合并 ≥ .767 —— **词形匹配做不了相似事件判别**，
  这正是本章要解的问题，现在有量化基线了。

**神经档真实数字**（2026-07-28 在 **gpu-5090** 训练，作者当日逐次授权；4090 四卡被他人占满 80–100%
util 且 ssh 间歇 reset，未挤占）。`roberta-base` 底座（5090 连不上 huggingface.co，走 `hf-mirror.com`），
两个头各 3 epochs：

- **coref 判别器** `runs/nodes/coref_supervised`：1730/2913 篇含正例，53,743 训练对
  （15,163 正 / 12,243 难负，`hard_fraction=0.5`），loss .3809→.2628→**.2036**。
- **检测器** `runs/nodes/detector_supervised`：全候选 plain CE，loss .5168→.2789→**.2369**。
- ⚠️ **踩坑（已修，写进脚本注释）**：初版给线性头单独 lr=1e-3（encoder 2e-5）**发散** ——
  loss 在 epoch 1 内从 .428 升到 .646 并平台，**高于 1:10 常数先验最优 ~.305**。
  改回与 `train_supervised_relations.py` 一致的**单一 lr 2e-5**后正常收敛。

**词形基线 → 神经档**（同一 497 篇 test，各自最优档；完整 9 格权衡表在 `runs/canonical_nodes_sweep_*.json`）：

| 指标 | lexical 基线 | **supervised** | 目标 | 判定 |
|---|---|---|---|---|
| coref MUC | .502 | **.782** | ~86 可比区间 | ❌ **未达**（差 ~8 点） |
| coref CoNLL（B³ .975 / CEAFe .969） | .771 | **.909** | — | — |
| 误合并率 | .582 | **.244** | 显著↓ | ✅ |
| **难例**误合并率（n=3077） | .767 | **.138** | 显著↓ | ✅ **5.6×** |
| coref 族 FNR | .398 | **.215**（天花板 .0163） | ↓ | ✅ |
| coref 族 P / F1 | .414 / .486 | **.756 / .770** | — | ✅ 两面都涨 |
| 合并 P / R / F1 | .389 / .635 / .483 | **.756 / .829 / .791** | — | — |
| 检测 typed micro-F1 | .687 | **.699**（ident .802） | ~60+ | ⚠️ 见下 |
| `node_confidence` ECE | .248 → **.004** | .0062 → **.0076** | 报出 | ⚠️ 见下 |

- ❌ **coref MUC .782 没到 ~86**：这是本阶段唯一明确未达标项，不粉饰。B³/CEAFe 高（.975/.969）是
  MAVEN 96% 单例簇的结构性结果，**MUC 才是判别力所在**，要按 MUC 报。
- ⚠️ **神经检测器只比纯记忆 lexicon 高 1.2 个点**（.6994 vs .6875，ident .8015 vs .7812）。
  候选分类口径下 "~60+" 这条线**记忆基线就能过**，所以**不能说 Ch1 检测有实质贡献**——
  这是一条弱结果，如实记。
- ⚠️ **神经档的 isotonic 校准反而让 ECE 略变差（.0062 → .0076）**：簇级"最弱内部连边"原始置信
  **本来就已校准**，校准器在这里没有增益。校准的价值出现在词形基线（.2477 → .0039）。
  **不得只报"ECE 降了 63 倍"而不说神经档这一档没降。**
- ✅ **弃权带的交易在神经档同样成立且更划算**：thr .5 下 band 0→0.1 使难例误合并 **.137→.116**、
  coref precision **.756→.791**，代价 FNR .215→.251（236 次弃权）；thr .9 + band .1 是退化角
  （2219 次弃权、全单例）。
- 产物：`runs/canonical_nodes_supervised.json`（+ `.jsonl` 10,389 个 canonical node，
  exact-cluster 准确率 **.9492**）、`runs/canonical_nodes_sweep_{lexical,supervised}.json`；
  **checkpoint 留在 5090 不下本地**（`runs/nodes/{coref_supervised,detector_supervised}`）。

**3→6 epochs 加训（2026-07-28，照 Phase A「3→6 是决定性一步」的经验复跑）—— 有效但不决定性**：

coref loss .2036→**.1056**、detector loss .2369→**.1507**（均未平台，仍在降）。
阈值提高了模型的置信标度，所以**必须在同一难例误合并率上比**，否则就是拿阈值挪动冒充增益：

| 同一 hard-misM = .116 | 3 epochs | **6 epochs** |
|---|---|---|
| 操作点 | thr .5 / band .1 | thr .7 / band .1 |
| coref MUC | .789 | **.806** |
| coref CoNLL | .913 | **.919** |
| coref 族 FNR | .251 | **.220** |
| coref 族 F1 | .769 | **.781** |
| coref 族 precision | .791 | .781（基本持平，略降） |
| 误合并率 | .209 | .219（略升） |

- ✅ **同一难例误合并率下 MUC/CoNLL/FNR/F1 四项都涨**，precision 基本持平 —— 是真增益，不是阈值挪动。
- ❌ **但没有复现 Phase A 那种量级**：MUC 距 ~86 的缺口从 ~8 点收到 **~5.4 点**，**仍未达标**。
  loss 还在降，说明可以再加 epoch，但收益递减，不宜继续在这条线上砸时间。
- ❌ **检测器加训基本无用**：typed F1 .6994→**.7048**（ident .8015→.8111），仍只比纯记忆
  lexicon 高 **1.7 点**。**结论不变：Ch1 检测不作为卖点。**
- ⚠️ **校准是否有增益取决于操作点**：6ep 最优点（band .1）raw ECE **.0382 → 校准后 .0056**（有增益）；
  3ep 的 band 0 点 raw 本就是 .0062（无增益）。**弃权带越宽，原始簇置信越偏，校准才有活干** ——
  要按操作点说，不能一句「校准有效/无效」了事。
- 6ep 最优点完整数字（thr .7 / band .1）：MUC **.8055** / B³ .978 / CEAFe .9732 / CoNLL **.9189**；
  误合并 .2191（难例 **.1157**）；合并 P/R/F1 .7809/.8238/.8018；coref 族 FNR **.2196**
  （P/R/F1 .7809/.7804/.7807）；10,458 个 canonical node，exact-cluster **.9538**，147 次弃权。
  产物 `runs/canonical_nodes_supervised_6ep.json` + `runs/canonical_nodes_sweep_supervised_6ep.json`。

**换长上下文底座（Longformer-4096）— ❌ 负结果，已止损**

起因是一个**实测的真缺陷**（不是推测）：`encode_spans` 在 max_length=512 下把长文档切成重叠窗口，
落在不同窗口的两个 mention **从未共享编码上下文**。MAVEN-Arg valid 实测 **13.1%**（93/710）的文档
需要 >1 窗口，其中 **34.7%（336 条）gold coref 对跨窗口分裂**；而全部 710 篇都 ≤4096 token
（最长 2186），所以长上下文能把分裂**彻底**消除。代码修复已落地并单独验证
（最长文档 2186 token/107 mention 在 4096 下单窗口，512 下要 6 窗口）。

但**换底座本身没换来收益，反而全面变差**（同为 6 epochs、同一扫描口径；loss .1090 vs base .1056，
基本持平 ⇒ 不是欠拟合，是泛化更差）：

| 同一 hard-misM ≈ .12 | **roberta-base 6ep** | Longformer-4096 6ep |
|---|---|---|
| 操作点 | thr .7 / band .1（hardM .116） | thr .9 / band 0（hardM .122） |
| coref MUC | **.806** | .781 |
| coref CoNLL | **.919** | .909 |
| coref 族 FNR | **.220** | .251 |
| coref 族 precision | **.781** | .766 |
| coref 族 F1 | **.781** | .758 |

- **每一项都输**，不是权衡换位置。**保留 roberta-base 6ep 作为系统档**。
- 机制上的解释（**是假设，未做消融**）：文档 token 中位数只有 **278**，≈87% 的文档**根本不需要**
  长上下文；换底座是在 100% 的文档上付代价，去修一个只出现在 13% 文档里的缺陷。
- ⚠️ **归因有混淆**：底座（预训练不同）与上下文（512 滑窗 → 4096 单窗 + 全局注意力）**同时变了**，
  无法把损失单独归给哪一个。要干净归因需要额外消融，**当前不值得为此花 GPU**。
- ✅ **代码修复保留**（`global_attention_positions` + 能力检查 + 形状哨兵）：它本身是对的，
  且是将来做跨文档/更长文档的前提；只是**当前 MAVEN-Arg 这个语料用不上它**。
- 📌 **注意 Longformer-base 与 roberta-base 容量相同**（均 12 层 / 768 维），所以这一轮
  **根本没有测到「容量」这个变量** —— 容量测试是 roberta-large，见下。

**换大容量底座（roberta-large）— ❌ 也是负结果**

- ⚠️ **第一次跑作废，不是结论**：lr 2e-5（base 用的值）下 **roberta-large 训练崩溃** ——
  epoch 1 还在学（loss ~.48），epoch 2 塌到 **.6239** 后五个 epoch 纹丝不动（.6251/.6228/.6237/.6223），
  远高于 1:10 常数先验最优 ~.305。roberta-large 微调不稳是已知问题，本脚本又无 warmup/调度器。
  **该 checkpoint 保留为 `runs/nodes/coref_large_diverged_lr2e5` 作证，不参与任何结论。**
- 重跑 `--lr 1e-5`（roberta-large 标准配方，零代码改动）后**正常收敛**：
  loss .3614→.2714→.2074→.1698→.1406→**.1120**（比 base 的 .1056 略高，同量级）。
- 但**仍不如 roberta-base**：最优 MUC **.778**（thr .7 / band 0，hardM .159、cF1 .765）
  vs base 6ep 的 **.806**。按同一 hard-misM ≈ .16 对齐：base（thr .5/band .05）MUC **.796** /
  cF1 **.786** / cFNR **.141**，large MUC .778 / cF1 .765 / cFNR .213 —— base 全面更好
  （只有 precision 略输 .724 vs .744）。

**★ 三次干预的合并结论：MUC 的差距不在底座**

| 干预 | 变量 | 最优 MUC | 相对 base 6ep |
|---|---|---|---|
| roberta-base 3ep | — | .789 | 基准前身 |
| **roberta-base 6ep** | 训练时长 | **.806** | **系统档** |
| Longformer-4096 6ep | 上下文长度 | .781 | **−2.5** |
| roberta-large 6ep (lr 1e-5) | 模型容量 | .778 | **−2.8** |

加训只给了 +1.7；长上下文与大容量**都是负的**。**停止换底座**——继续在这条线上花 GPU 没有依据。

**★★ 口径核对（2026-07-28）—— 「MUC ~86」这条验收线是错的，一直在跟错误的数字比**

分两步核，第一步的假设被证伪、第二步找到了真原因：

1. **人群差异（假设，已证伪）**：把规范化的簇投影到 MAVEN-ERE 的 mention 人群上复评
   （未覆盖的 ERE mention 按单例计，诚实计法）：MUC **.8055 → .7960**，覆盖率 95.68%
   （11,515/12,035）。**只值 −0.95 点，解释不了差距。**
2. **对标数字本身错了（真原因）**：翻 MAVEN-ERE 原论文（arXiv 2211.07342）Table 7，
   **官方 RoBERTa-base 基线的 coref MUC F1 是 81.4 ±0.51（单任务）/ 82.1 ±0.43（+joint）**，
   不是 86。那个 86.1 是 **2024 年一个联合图模型的 SOTA**，不是基线。

**按真实基线重新对齐（我们 = roberta-base 6ep，ERE 人群，valid 子集 497 篇）**：

| | MUC P | MUC R | **MUC F1** | B³ F1 | CEAFe F1 |
|---|---|---|---|---|---|
| 官方 RoBERTa-base 单任务（test） | 79.2 | 84.0 | **81.4** | 98.1 | 97.7 |
| 官方 RoBERTa-base +joint（test） | 81.4 | 82.8 | **82.1** | 98.2 | 97.9 |
| **本项目** | 78.4 | **80.8** | **79.6** | 97.8 | 97.3 |

- ✅ **B³ / CEAFe 基本平手**（−0.3 / −0.4）；**precision 也基本平手**（78.4 vs 79.2，−0.8）。
- ❗ **缺口全在 MUC recall**：80.8 vs 84.0（**−3.2**）。其中约 **1.6 点是结构性的** ——
  我们跑在 MAVEN-Arg 人群上，ERE gold coref 对里有 1.63% 两端不全在 Arg 里，天然拿不到。
- ✅ **总差距 = −1.8 MUC F1（对单任务基线）/ −2.5（对 joint）**，**不是先前以为的 −6.4**。
  Ch1 的共指主干**基本达到官方基线水平**（本就是「复现、不主张新颖」的定位）。
- 📌 **这也解释了为什么三次换底座都没用**：我们已经贴着 RoBERTa-base 基线的天花板，
  而官方基线本身就是 roberta-base 的 81.4；再往上的 ~4.7 点要靠**四种关系联合建模 + 更丰富的
  结构**（论文自己测的 +joint 只给 +0.7），**不是靠更大或更长的编码器**。
- ⚠️ 剩余不可比处（如实记）：官方数字在 **test**（标签藏在 CodaLab），我们在 **valid 的 497 篇
  子集**（另 213 篇做校准）；官方是 5 次随机重跑的均值±标准差，我们是单次。
