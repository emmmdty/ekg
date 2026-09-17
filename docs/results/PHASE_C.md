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

---

## 官方口径复评（2026-07-30，checkpoint 不变，只换评测器）

`runs/nodes/coref_supervised_6ep` 在**全 710 篇 valid** 上、由官方 `evaluate.py` 打分
（复现命令同 [`PHASE_A.md`](PHASE_A.md) 末节）：

| | MUC P | MUC R | **MUC F1** | B³ F1 | CEAFe F1 | BLANC F1 |
|---|---|---|---|---|---|---|
| **本项目（官方评测器 @valid 全量）** | 72.98 | 82.56 | **77.47** | **97.51** | **97.09** | 87.15 |
| 本项目（内部口径，497 篇子集 + ERE 人群校正） | 78.4 | 80.8 | 79.6 | 97.8 | 97.3 | — |
| 官方 RoBERTa-base 单任务 @test | 79.2 | 84.0 | **81.4** ±0.51 | 98.1 | 97.7 | 89.8 |

- **应以 77.47 为准**：全量、官方评测器、无自定校正，口径最干净；79.6 是子集 + 人群校正的内部数。
- 与官方基线的差距 **−3.9 MUC**（对 test 数），B³/CEAFe **几乎持平**（−0.6）。
- 缺口仍全在 **MUC recall**（82.56 vs 84.0），与此前结论一致。
- ⚠️ 我们 valid、官方 test，仍非同 split；CodaLab 已关闭，历史协议说明见
  [`ARCHIVE_INDEX`](../ARCHIVE_INDEX.md)。
- 📌 **checkpoint 已于 2026-07-30 回传 4090**（`runs/nodes/coref_supervised_6ep`，sha256 `3cf5b7c4…`），
  三端字节数与 sha256 一致。

---

## 欠并/过并错误分布（2026-08-07，官方口径，`PHASE_C3` 步骤 1）

`77.47` 只是三个比率，说不出**每个方向各错了多少次**。本节把它拆成计数，作为非对称权重比的依据。
**纯 CPU，不训练，checkpoint 未动**（仍是 `runs/nodes/coref_supervised_6ep`）。

**口径**：710 篇全量 valid + 官方 `evaluate.py` + 无校正，与上一节的 77.47 同一份预测文件
（`runs/submission/valid_prediction_sup.jsonl`）。⛔ 79.6 那档（497 篇 + 内部评测器 + ERE 人群校正）
**不参与本节任何计算**。

```bash
curl -o /tmp/maven_evaluate.py \
  https://raw.githubusercontent.com/THU-KEG/MAVEN-ERE/main/evaluate.py
uv run python scripts/report_coref_error_profile.py \
    --evaluator /tmp/maven_evaluate.py \
    --gold data/processed/maven_ere/valid.jsonl \
    --pred runs/submission/valid_prediction_sup.jsonl \
    --output runs/coref_error_profile_valid.json
```

脚本**自带两条强制交叉校验**，不过就 `SystemExit`：① 我们聚合的 MUC P/R 必须等于官方
`evaluate_coreference` 的 `muc_*`；② 我们的成对计数必须等于逐文档调官方 `blanc()` 累加出的
`(rc, wc, wn)`（整数全等）。实跑输出 `✔ cross-checked (MUC F1 77.47, BLANC F1 87.15)`
——**这张表不可能漂离 77.47**。

### ★★ 主表：过并是多数，不是欠并（推翻 `PHASE_C3` 契约的前提）

| 错误方向 | 成对（mention pair） | 占错误总量 | MUC 链 | 占错误总量 |
|---|---|---|---|---|
| **欠并**（该合未合） | **801** | **36.5%** | **258** | **36.3%** |
| **过并**（不该合却合） | **1,391** | **63.5%** | **452** | **63.7%** |
| 欠并/过并比值 | **0.58×** | | **0.57×** | |

- 分母：gold 共指对 **4,029** / 预测共指对 **4,619**；gold 链 **1,479** / 预测链 **1,673**。
  成对 P/R = **.6989 / .8012**；MUC P/R = **.7298 / .8256**（后者与官方评测器逐格一致）。
- 规模：710 篇、**17,780** gold mention、16,301 个 gold 簇（**15,719 单例 = 96.4%**、582 个多例簇）。
- ✅ **两种 currency 结论一致**（36.5/63.5 vs 36.3/63.7）⇒ 不是「大簇产生平方级对数」造成的计数假象。
- ❗ **过并是欠并的 1.74 倍**。契约里「缺口全在 recall＝欠并、所以要加重欠并」的前提**在官方口径下不成立**。

### ★ 为什么会判反：又一次口径混用（第四次）

按官方口径与官方基线**逐项相减**：

| | MUC P | MUC R | MUC F1 |
|---|---|---|---|
| 官方 RoBERTa-base 单任务 @test | 79.2 | 84.0 | 81.4 |
| **本项目（官方评测器 @valid 全量）** | **72.98** | **82.56** | **77.47** |
| 差 | **−6.22** | **−1.44** | −3.9 |

**缺口的大头在 precision，不在 recall。** 旧结论「缺口全在 MUC recall」成立于**内部口径**
（497 篇 + ERE 人群校正：P 78.4 vs 79.2 = −0.8、R 80.8 vs 84.0 = −3.2，见本文件上一节表）。
2026-07-30 换官方评测器时 P 掉了 5.4、R 涨了 1.8，**排序整个翻转，但那句结论被原样搬进了
`TODO.md` 与 `PHASE_C3` 契约**。⚠️ 这是 `ekg-internal-vs-official-protocol-trap` 记的同一个错的第四次。

⚠️ 逐项相减这一条**仍是 valid vs test**（RESIJ 实测 dev 系统性低于 test），所以只用它判**方向**，
不用它判幅度。而**主表的 63.5% / 36.5% 完全是我们自己的预测在自己的 split 上的内部分解，
不涉及任何跨 split 外推**——那一条是干净的。

### 结构：错误集中在哪

| 量 | 值 |
|---|---|
| gold 多例簇 | 582（占全部 gold 簇 3.57%） |
| 　其中完整保住（p(G)=1） | **368（63.2%）** |
| 　其中**整簇全散**（p(G)=\|G\|，一条链都没捞到） | **118（20.3%）** |
| 预测多例簇 | 685 |
| 　其中纯净（g(P)=1） | 335（48.9%） |
| 　其中**混进 ≥2 个 gold 事件** | **350（51.1%）** |

- p(G) 被拆成几片：`{1: 368, 2: 182, 3: 26, 4: 3, 5: 1, 6: 1, 7: 1}`
- g(P) 混进几个 gold 簇：`{1: 335, 2: 281, 3: 52, 4: 10, 5: 2, 6: 3, 8: 2}`
- 欠并对按 gold 簇大小：2 元簇只占 **109/801（13.6%）**，size ≥10 的大簇占 **287（35.8%）**
  ⇒ 欠并的对数被少数大簇的平方项放大；**MUC 链那一列才是它对 77.47 的真实贡献**。

### 词形与距离：哪一半够得着

| | 欠并（n=801） | 过并（n=1,391） |
|---|---|---|
| trigger **完全相同** | 356（44.4%） | **721（51.8%）** |
| trigger 相似度 ≥ .8（`HARD_SIMILARITY`） | 389（48.6%） | 798（57.4%） |
| trigger 相似度 < .2 | **208（26.0%）** | 301（21.6%） |
| **跨句** | **743（92.8%）** | 1,190（85.5%） |

- **过并的一半以上是 trigger 一模一样的对** —— 正是 `nodes/coref.py` 定义的那类难负例
  （"attacked" vs "attack" 的两次不同攻击）。⚠️ 与「难例误合并率 .116」**不可相减**：那是
  497 篇 + 内部评测器口径下 3,077 个难例对的比率，本表是 710 篇官方口径的计数。
- **欠并里 44.4% 也是 trigger 完全相同的对** ⇒ 这部分模型看见了却没敢合，**阈值/权重够得着**；
  但另有 26% 相似度 <.2，**重加权救不了**。
- 两个方向都 **85%+ 跨句** ⇒ 与 Ch2 的跨句瓶颈同源（`PHASE_A.md`：跨句 25.00 vs 同句 38.18）。

### 对 `PHASE_C3` 步骤 2/3 的三条约束（是推论，未验证）

1. ⛔ **不得把 2.3–3.9 当权重比**。那是 Phase E 的**下游单位代价比**（拆节点 −.0184 vs 增边 −.0047），
   本表给的是**错误频率比 0.58×（过并占多数）**。两者方向相反，相乘后净倾斜只剩约 **1.3–2.2×**,
   远小于 2.3–3.9。**权重比要从这个净值起扫，不是从 2.3 起扫。**
2. ⚠️ **加重欠并 = 往 recall 推**，而 recall 距官方只差 1.44、precision 差 6.22。
   按契约原方向调很可能**用 6 点的短板换 1.4 点的长板**。
3. ✅ **仍有可做的**：过并的 51.8% 是 exact-trigger 对，欠并的 44.4% 也是——**同一批词形相同的对里，
   模型两个方向都在错**。这说明问题不在决策阈值的对称性，而在**词形相同时的判别力**
   （契约止损节说的「候选生成」之外的第三种可能）。**这条比非对称权重更值得先验。**

产物：`runs/coref_error_profile_valid.json`（全部计数与直方图）。
代码：`scripts/report_coref_error_profile.py` + `ekg.core.eval.muc_link_errors`（MUC 的原始链计数；
既有 `muc()` 只返回比率）。测试 `tests/core/test_metrics.py` + `tests/scripts/test_coref_error_profile.py`。
校验：**354 passed / 12 skipped**（基线 342/12）、ruff 0、`ekg-smoke` OK。

---

## ⚠️ SUPERSEDED · v6 · C4 首次机制对照：上下文判别 vs 只读触发词（2026-08-29，4090 GPU1/GPU2）

> **本节及其下的 2×2 消融已被 2026-08-30 的 C4-r2 全曲线推翻**（见本文件末节）：
> 四个数在对应 epoch 上逐点复现，但它们来自四个不同 epoch，而对照臂自身的 epoch 间
> 波动就有 8.55 个 MUC 点。**保留原文只作推导记录，其差值不得再被引用。**

**协议**：P1 r9 manifests（train 2,622 / internal-dev 291）｜MAVEN-Arg 训练源（与 MAVEN-ERE
同一批文档、不同标注层）｜gold mentions｜官方 `evaluate.py`｜seed 13｜**final-valid 未访问**。
两组唯一变量是 `--context-discriminative` 开关，其余逐位相同（10 epochs / neg-ratio 10 /
hard-fraction 0.5 / 同一内容寻址 roberta-base 快照）。

### 主表（官方 evaluate.py @ internal-dev）

| 组 | MUC P | MUC R | **MUC F1** | B³ F1 | CEAFe F1 | BLANC F1 |
|---|---|---|---|---|---|---|
| 对照（只读触发词向量） | 78.08 | 70.86 | 74.29 | 97.50 | 97.14 | 84.92 |
| **机制（上下文判别）** | 76.86 | **75.92** | **76.38** | **97.68** | **97.27** | **87.57** |
| Δ | −1.22 | **+5.06** | **+2.09** | +0.18 | +0.13 | **+2.65** |

四项 coreference 指标三项改善、无一退化。**单种子，未做配对检验，不得写成已确认胜出。**

### ⚠️ 两条必须如实记的

**① 选模指标与报数指标不对齐，而且方向相反。** 两个 checkpoint 都按预注册规则选
「internal-dev 完整候选对全集上的 pair-level F1 最好那轮」：

| | 最好 pair-F1 | 轮次 | **MUC F1** |
|---|---|---|---|
| 机制 | 0.8012 | ep3 | **76.38** |
| 对照 | **0.8046** | ep7 | 74.29 |

**pair-F1 说机制略差（−0.0034），MUC 说机制好 2.09。** 两组用的是同一条选择规则，
所以这个对照本身成立；但**规则选错了轴**——pair-level 决策与聚类后的链结构不是一回事。
后续必须把选模指标换成 MUC 或与之更接近的代理，并重跑；本表在换轴前只能算探索性证据。

**② 增益来自 recall，不是设计时假设的 precision。** 机制的动机是过并占 63.5%、
其中 51.8% 同词形，预期收益在 precision。实测是 **recall +5.06 / precision −1.22**。

合理解释（**尚未验证，不得当结论**）：欠并里 **92.8% 是跨句对**，句子级语境向量恰好给了
跨句链接所需的信号，于是先兑现在 recall 上。**不把预测错了的机制事后改写成"本来就是要提召回"**
——设计假设是 precision，实测是 recall，两者都记，验证留给下一轮定向实验。

### 与历史数字的关系

历史 MUC **77.47** 是在 **710 篇 final-valid** 上测的，本表是 **291 篇 internal-dev**，
**不可直接相减**。Ch1 的同协议对手（official single/joint 的 coref 头）尚未重跑，
因此本章目前只有「机制 vs 无机制」的内部对照，**还没有对外的差距结论**。

产物：`runs/stages/C4/{ctx_discriminative,control_trigger_only}/seed-13/`
（checkpoint、coref_prediction.jsonl、coref_metrics.json）。

### 2×2 消融：两个组件单独更好，合起来互相干扰（2026-08-29）

同协议、同 seed、同选择规则，唯一变量是启用哪些组件（官方 `evaluate.py` @ internal-dev）：

| 臂 | MUC P | MUC R | **MUC F1** | B³ F1 | BLANC F1 | vs 对照 |
|---|---|---|---|---|---|---|
| 对照：只读触发词 | 78.08 | 70.86 | 74.29 | 97.50 | 84.92 | — |
| **+ 语境池化** | 76.20 | 80.45 | **78.27** | 97.77 | 88.79 | **+3.98** |
| **+ 混淆度特征** | 74.38 | 83.60 | **78.72** | 97.73 | 88.87 | **+4.43** |
| + 两者（原设计的完整机制） | 76.86 | 75.92 | 76.38 | 97.68 | 87.57 | +2.09 |

**★ 设计假设被推翻**：我按"两个组件互补"设计，实测是**互相干扰**——完整机制低于任一单组件
约 2.3 点。因此**不得把"完整机制 +2.09"作为本章结论**；当前最好的配置是单组件。

**三个臂的收益方向一致：全部来自 recall**（+9.6 / +12.7 / +5.1），precision 全部小幅下降。
这与"欠并里 92.8% 是跨句对"一致，也再次说明本机制的实际作用是**跨句链接**，
而不是设计时假设的抑制同词形过并。

⚠️ **限制（三条，都会影响能不能写成结论）**：
1. **单种子**，无配对检验；
2. **选模轴仍是 pair-level F1**，而它与 MUC 方向不一致（pair-F1 排序为
   混淆度 0.8124 > 语境 0.8052 > 对照 0.8046 > 完整 0.8012，与 MUC 排序不同），
   各臂因此停在不同 epoch（ep10 / ep5 / ep7 / ep3），**epoch 差异是未控制的混淆**；
3. 同协议对手（official coref）尚未重跑，**目前没有对外差距结论**。

下一轮定向实验：把选模轴换成 MUC 或其代理，固定 epoch 预算重跑四臂，再谈机制贡献。

---

## ★★ v6 · C4-r2：消掉 epoch 混淆后，**上一节的机制增益不成立**（2026-08-30，4090 四卡）

**协议**：与上一节逐位相同（P1 r9 manifests、MAVEN-Arg 训练源、gold mentions、seed 13、
10 epochs / neg-ratio 10 / hard-fraction 0.5、同一内容寻址 roberta-base、官方 `evaluate.py`
@ internal-dev 291 篇、final-valid 未访问）。**唯一改动是 `--save-every-epoch`**：
留下每个 epoch，再用官方评分器逐个打分，于是选模轴与报数轴由构造变成同一个。

### 先确认这不是"另一次跑出别的数"

上一节四个数在本轮对应 epoch 上**逐点复现**：

| 臂 | 上一节报的 | 它当时停在 | 本轮该 epoch 的 MUC |
|---|---|---|---|
| 对照 | 74.29 | ep7 | **74.29** |
| +语境池化 | 78.27 | ep5 | **78.27** |
| +混淆度 | 78.72 | ep10 | **78.72** |
| +两者 | 76.38 | ep3 | **76.38** |

⇒ 数字没错，**错的是把四个不同 epoch 的数放进同一张表比较**。

### MUC F1 全曲线（官方 `evaluate.py` @ internal-dev）

| ep | 对照 | +语境池化 | +混淆度 | +两者 |
|---|---|---|---|---|
| 1 | 71.75 | 73.27 | 70.60 | 67.37 |
| 2 | **80.30** | **78.54** | **80.58** | 77.87 |
| 3 | 78.66 | 77.81 | 79.06 | 76.38 |
| 4 | 76.48 | 76.80 | 76.92 | 75.58 |
| 5 | 79.84 | 78.27 | 79.34 | 78.18 |
| 6 | 78.82 | 78.38 | 79.55 | **78.25** |
| 7 | 74.29 | 75.45 | 74.68 | 70.99 |
| 8 | 74.70 | 77.13 | 74.96 | 76.91 |
| 9 | 76.18 | 77.06 | 75.74 | 74.98 |
| 10 | 75.66 | 74.72 | 78.72 | 75.77 |
| **10 epoch 均值** | **76.67** | **76.74** | **77.01** | **75.23** |

### ★ 结论：机制的效应量落在自身噪声里

| 臂 | 均值 Δ vs 对照 | 逐 epoch 配对差的 sd | 正号 |
|---|---|---|---|
| +语境池化 | **+0.07** | 1.40 | 5/10 |
| +混淆度 | **+0.35** | 1.11 | 7/10 |
| +两者 | **−1.44** | 1.85 | 2/10 |

**对照臂自己在 10 个 epoch 之间就波动 71.75–80.30，跨度 8.55 点、sd 2.73。**
三个臂与对照的均值差全部在 ±0.4 以内（"两者"是 −1.44，方向为负），
**没有一个接近这个噪声地板**。上一节报的 +3.98 / +4.43 / +2.09 是
**pair-F1 选模轴把对照送进 ep7 这个低谷、把消融臂送上各自高点**造成的。

四个指标一致，不是 MUC 独有（10 epoch 均值）：

| 臂 | MUC | MUC P | MUC R | B³ | CEAFe | BLANC |
|---|---|---|---|---|---|---|
| 对照 | 76.67 | 75.29 | 78.60 | 97.66 | 97.20 | 87.80 |
| +语境池化 | 76.74 | 75.00 | 78.80 | 97.65 | 97.20 | 87.96 |
| +混淆度 | 77.01 | 76.22 | 78.60 | 97.69 | 97.26 | 87.66 |
| +两者 | 75.23 | 73.93 | 77.17 | 97.52 | 97.04 | 86.64 |

**上一节"增益全部来自 recall"的说法同样不成立**：epoch 均值上四臂 recall 是
78.60 / 78.80 / 78.60 / 77.17，基本持平。那个 recall +5.06 也是同一个选模伪影。

### 因此，上一节作废

上一节（`## v6 · C4 首次机制对照` 与 `### 2×2 消融`）的**表格与结论均标记为
SUPERSEDED**，保留原文只作推导记录，**不得再引用其差值**。上一节自己列出的限制②
（"选模轴仍是 pair-level F1，各臂停在不同 epoch，epoch 差异是未控制的混淆"）
正是本轮验证出来的东西——那条限制不是保守措辞，是结论级问题。

### 另外两条实测事实

1. **10 epoch 是过训**：四臂都在 **ep2** 附近达到最好，之后震荡下行。
   下一轮预算应该缩到 3–4 epoch 并加密早期采样，而不是继续加长。
2. **单 epoch 的点估计在本任务上不可靠**：8.55 点的 epoch 间跨度远大于任何机制效应，
   任何"单 checkpoint 对比"的 Ch1 结论都要按这个尺度重读，包括历史的 MUC 77.47。

### 产物与复现

`runs/stages/C4/r2/{control_trigger_only,ablate_context_only,ablate_confusability_only,ctx_discriminative}/seed-13/epochs/epoch-{1..10}/`
各含 checkpoint、`coref_prediction.jsonl`、`coref_metrics.json`（内嵌完整 `command_argv`
与 evaluator/gold/pred 的 sha256）。训练与打分脚本：`runs/stages/C4/r2/launch_arms.sh`、
`runs/stages/C4/r2/score_epochs.sh`；日志 `logs/c4r2_*.log`。
候选全集 digest `15a3b1a5…dac10910`，291 篇 / 7,195 mention，四臂完全一致。

### 下一步（Ch1 目前没有可写的机制贡献）

- 机制在同预算下**不优于只读触发词的对照**。按契约这算一个已完成的核心设计周期，
  结果是**未过门**；不得把上一节的数字拿去写章节贡献。
- 若要继续：预算缩到 ep1–4、多种子（epoch 噪声这么大，单种子无意义）、
  并且**先解决"为什么 ep2 之后一路掉"**——那可能才是真正的问题。
- Ch1 的同协议对手（official coref）**仍未重跑**，所以本章依然没有对外差距结论。

---

## ★★ v6 · C4-r3 复现底座：Ch1 一直缺一条**学习率调度**（2026-08-30，4090 四卡）

上一节（C4-r2）的全曲线暴露了一个此前看不见的事实：**四个臂全部在 epoch 2 见顶，
之后八个 epoch 掉 4–8 个 MUC 点**。查下来原因不在机制——
`train_coref_scorer.py` 用的是**常数学习率、没有任何调度、编码器与 head 同一个 lr、
没有梯度累积**。而 `train_supervised_relations.py` 三样都有，且本项目 2026-08-07 就把
「warmup + linear decay」记为**一直漏配的官方成分**，Ch2 光靠补齐配方就值 causal +5.11。

⇒ **Ch1 此前所有结论都建立在一个从未建过复现底座的配方上。**

### 配方研究：只跑对照臂，唯一变量是补哪几件

官方 `evaluate.py` @ internal-dev 291 篇，逐 epoch 打分，seed 13，其余逐位相同。

| 配方 | 均值 | 最好 | 最好@ep | **末轮** | **极差** |
|---|---|---|---|---|---|
| **A** 旧配方（常数 lr 2e-5，无调度） | 76.67 | 80.30 | 2 | 75.66 | **8.55** |
| **B** ＝ A + warmup 200 + 线性衰减 | **78.45** | 79.51 | 10 | **79.51** | **3.36** |
| **C** ＝ B + head-lr 1e-4 | 76.42 | 77.94 | 2 | 77.18 | 4.55 |
| **D** ＝ C + 梯度累积 8 | 76.55 | 80.00 | 2 | 77.70 | 6.82 |
| **E** ＝ C + 20 epoch | 77.27 | 79.33 | 2 | 77.82 | 5.81 |
| 同协议对手 official_joint | — | **80.98** | — | — | — |

### 三条结论

1. **缺的就是学习率调度这一件。** B 相对 A：均值 **+1.78**，且**末轮就是峰值**——
   过训衰减完全消失。而 head-lr 1e-4（C）与梯度累积 8（D）**都是负作用**，
   不能因为官方 relation 配方里有就照搬。
2. **比 +1.78 更重要的是噪声降了 2.5 倍**（极差 8.55 → 3.36）。C4-r2 里三个机制臂与
   对照的均值差是 +0.07 / +0.35 / −1.44，全部埋在 8.55 点的抖动里——
   **在旧配方上，任何 1 点量级的机制效应按构造就测不出来**。稳定底座是机制可测的前提，
   不是锦上添花。
3. **仍低于对手 1.47**（79.51 vs 80.98）。底座修好之后差距从"均值 −4.3"收窄到"峰值 −1.47"，
   但**没有消失**，不得写成已追平。

### ⚠️ 与 C4-r2 的关系

C4-r2 的四臂结论（机制效应在噪声内）**在旧配方下依然成立且不作废**；本节说明的是
那个噪声本身有一半以上来自配方缺陷。机制在 B 底座上的重测正在进行，**结果另行报告**——
不得用"底座修好了"去追认 r2 里任何一个被否掉的机制主张。

### C4-r3 机制重测：底座修好后，**机制依然无效**（2026-08-30）

在配方 B（warmup + 线性衰减）上重跑三个机制臂，与**同种子底座**逐 epoch 配对：

| 臂 | 均值 Δ vs 底座 | sd | 正号 |
|---|---|---|---|
| + 语境池化 | **−0.23** | 1.12 | 3/10 |
| + 混淆度 | **−0.15** | 0.91 | 7/10 |
| + 两者 | **−0.71** | 2.27 | 4/10 |

**同配方换种子（seed17 − seed13）的逐 epoch 差**：
`[−6.9, −3.7, −1.0, +1.8, +2.0, +0.4, +2.0, +1.3, +0.2, +0.1]`

⇒ **三个机制效应的绝对值全部小于种子噪声。** C4-r2 的否定结论在修好的底座上**依然成立**，
且这次带着噪声尺子，不是靠"看起来很小"。**Ch1 的机制到此为止：两个核心设计周期都未过门。**

### ★ 但退火终点是稳的 —— 这给了 Ch1 一条正确的报数规则

种子噪声不是均匀的，它**集中在训练早期**：第 1 个 epoch 差 6.9 点，而最后两个 epoch
只差 **0.2 / 0.1**。这正是线性衰减该有的行为（学习率归零，两条轨迹收敛到同一个盆地）。

| 臂 | ep10（退火终点） |
|---|---|
| + 混淆度 | **79.94** |
| 底座 seed17 | 79.58 |
| 底座 seed13 | 79.51 |
| + 语境池化 | 79.00 |
| + 两者 | 78.48 |
| 对手 official_joint | **80.98** |

⇒ **报退火终点，不报"选出来的最好 epoch"。** 这一条同时消掉两个问题：
epoch 选择混淆（不需要选）与种子不稳定（终点跨种子 0.07–0.2）。
它也是 C4-r2 那个 4 点假增益**在方法层面的根治**，而不只是事后发现。

⚠️ 终点上 `+混淆度` 高出底座 **+0.36~0.43**，当时看约为终点种子噪声的 2 倍。
**单对种子不足以判定**，多种子配对验证进行中，结果另报——
在拿到多个种子的一致符号之前，**不得把这 +0.4 写成机制有效**。

> **⛔ 上面这段的前提已被下一节推翻**：「终点跨种子 0.07」是两个种子碰巧撞上的，
> 4 个种子下底座终点的 sd 是 **1.02**、极差 **1.80**。保留原文只作推导记录。

### ★★ 多种子验证：+0.4 **不重现**，且"终点稳定"这条也站不住（2026-08-30）

退火终点（ep10）的官方 MUC，`+混淆度` 与**同种子底座**逐种子配对：

| seed | 底座 | + 混淆度 | **Δ** |
|---|---|---|---|
| 13 | 79.51 | 79.94 | **+0.43** |
| 17 | 79.58 | 79.22 | **−0.35** |
| 42 | 77.78 | 79.25 | **+1.47** |
| **均值** | **78.95** | **79.47** | **+0.52**（sd 0.92，正号 **2/3**） |

**① 符号翻转，效应不重现。** 三个种子里 seed 17 为负；均值 +0.52 的标准误是
0.92/√3 ≈ 0.53，即**离零约一个标准误**。按预注册的判据（多种子符号一致），
**机制判定为无效**，`+0.4` 不得写入任何表格。

**② 我上一节写的「退火终点跨种子只差 0.07」是错的，在此更正。**
底座终点四个种子是 79.51 / 79.58 / **77.78** / 79.68 —— **sd 1.02、极差 1.80**。
n=2 的一致是运气。**终点比训练中期稳（中期极差 6.9 → 终点 1.80），但不是"稳到 0.1"**，
仍不足以判定 1 点以下的效应。「报退火终点」作为**报数规则**依然成立
（它消掉 epoch 选择混淆），但**不能当成噪声已经消失**。

**③ 与对手的距离**：底座终点四种子均值 **79.14**，对手 official_joint **80.98**，
差 **1.84**。

⇒ **Ch1 到此结束两个核心设计周期，机制无效。** 按契约本章降为系统组件，
方法贡献为零；可写的是配方修复（+1.78 均值、消除过训衰减）与两条方法学结论
（选模轴伪影、种子噪声的 epoch 结构）。

## C4-r4 根因复核：历史机制漏掉论元，gold event-level 只作上限（2026-09-02）

本节是 **gpu-5090 / seed 13 / internal-dev 291 篇的 exploratory 诊断**；final-valid 未访问，
不改变上一节的正式 phase 状态。训练提交 `7ac24a3`，官方预测导出/评估提交 `5e40b62`；
候选 digest `15a3b1a548625624642130190b39411e6346866ff8594c2af2020cfbdac10910`。
四臂共同使用 warmup 200、线性衰减、10 epochs、lr 2e-5 和同一 P1 manifests。

### 2×2：负文档采样 × event-level argument oracle

`argument_pooling_oracle` 明确读取 MAVEN-Arg 的 event-level gold arguments。该标注按 event 存储并
复制给簇内每个 mention，属于信息上限，**不得作为可部署方法分**。根 checkpoint 按完整 dev
pair-F1 选 epoch；下表固定官方阈值 0.7，用官方 `evaluate.py` 评同一 ERE mention population：

| 采样 | 论元 | pair-best epoch | pair-best MUC P/R/F1 | epoch-10 MUC P/R/F1 |
|---|---|---:|---|---|
| 历史采样 | 无 | 9 | 77.27 / 84.82 / **80.87** | 77.08 / 83.94 / **80.37** |
| 补全 all-negative docs | 无 | 2 | 83.99 / 74.17 / **78.78** | 78.23 / 80.28 / **79.24** |
| 历史采样 | gold event-level | 5 | 85.08 / 90.58 / **87.74** | 82.85 / 90.23 / **86.38** |
| 补全 all-negative docs | gold event-level | 2 | 89.56 / 82.37 / **85.82** | 42.39 / 89.01 / **57.43** |

事实边界：

1. event-level argument oracle 的提升在 pair-best（+6.87 MUC）和固定 epoch-10（+6.01）两种读法下
   都成立，证明历史 `context_pooling + confusability` 负结果**没有测试冻结设计所要求的论元输入**。
2. 补全负文档把无论元模型推向更高 precision / 更低 recall，但没有稳定提高 MUC；不能把“恢复
   singleton-only 文档”本身写成提分机制。
3. 补全后每 epoch 的文档更新数从 1,555 增到 2,508（+61%）。与 event-level oracle 联用时 epoch 2
   pair-F1=.8721，此后塌成近全正预测，epoch-10 MUC=.5743。权重全为有限值，但 head 范数从
   1.06 持续增到 2.56；这是捷径过拟合与 compute budget 混杂，不是 NaN，也不能反推负文档有害。
   下一次采样消融必须按 optimizer steps/tokens 对齐，并保存 representation/head norm。

### 去掉 event-level 复制泄漏后的局部信号

脚本 `scripts/report_coref_argument_locality.py` 用 MAVEN-ERE `tokens` 恢复句边界；2,913/2,913 篇的
展平 token 文本与 MAVEN-Arg `document` 字符级完全一致。涉及 Arg-only mention 的 pair 显式排除：
internal-dev 对齐 6,859/6,875 mentions，排除 14 个 exact-trigger pairs。

| internal-dev exact-trigger same-type pair | 正 pair（n=828）不同率 | 负 pair（n=1,220）不同率 |
|---|---:|---:|
| event-level signature | **0.00%** | **80.98%** |
| mention 同句 local signature | **63.77%** | **84.18%** |

因此“正 pair 签名 100% 相同”是 event-level 复制的构造结果；裁成 mention-local 后仍保留
**20.41 点**区分差，但强度远小于 gold oracle。可部署方法必须预测/抽取 mention-local arguments，
并学习角色对齐与缺失鲁棒性，不能把 event-level gold pooling 改名后当作完整方法。

本地报告：`runs/stages/C4/c4-v6-rootcause-r4/exploratory/argument_locality_{train,internal_dev}.json`，
SHA-256 分别为 `e66b14eb…3cb4` / `23fe74e9…3b3e`。远端四份训练日志 SHA-256 前缀：
`fb0d9396` / `ac0c7330` / `8ce6343c` / `924f85aa`；完整 checkpoint、逐 epoch 权重、阈值曲线和
official metrics 留在 `gpu-5090:/mnt/aidata/tongjiakai/ekg/runs/stages/C4/`
`c4-v6-rootcause-r4/exploratory/2x2/`。

## ★★ C-5b · C5 入口齐全：三个新脚本 + permutation 臂接线（2026-09-13，本地 CPU）

**状态**：C5.0 的实现侧到此闭合。契约点名的 `scripts/run_c5_argument_uncertainty.py` 从**不存在**变为存在，
另加 `prepare_c5_argument_uncertainty_preflight.py` 与 `smoke_c5_argument_uncertainty.py`，
并把矩阵第 6 臂（permutation 负控）接进 trainer 与**推理侧**。
三件套：**608 passed / 28 skipped、ruff 0、`ekg-smoke` OK**（前值 592/28）。

### 先纠正缺口的规模：`train_` 与 `evaluate_` 本来就有

`HANDOFF.md` §0.3 把 C-5b 写成「C5 的四个入口脚本：`train_` / `evaluate_` / `prepare_*_preflight` / `smoke_`」。
核到代码后**缺口只有三个脚本加一个开关**：

| 契约要的 | 实况 |
|---|---|
| `train_` | ✅ **`scripts/train_coref_scorer.py` 已有**（478 行），`role_compatibility` 早已注册进 `discriminative.py` 的组件表，`--components role_compatibility` 即 full 臂。只缺 permutation 开关 |
| `evaluate_` | ✅ **`scripts/score_maven_ere_official.py` 已有**，官方 `evaluate.py` 同时评 coreference 与 relations，`muc/b_cubed/ceaf/blanc` 的 P/R/F1 全部输出（A4.1 当天刚用过同一个包装） |
| 预测器 | ✅ **`scripts/build_maven_ere_submission.py` 已有**，`--from-labeled` + `--relation-predictor none` 就是注册负面对照那条线用的路径 |
| `prepare_*_preflight` / `smoke_` / `run_c5_*` | ❌ 三个都要新写 |

**这与 A4.1 那次是同一类问题**：任务描述没有核到代码，于是把工作量与阻塞都估错了。
**写进队列的缺口，开工第一件事是逐个去仓库里找一遍。**

### 执行中抓到三个真缺陷（两个会让臂跑错，一个是 A 类）

1. **`role_compatibility` 会被自己的参数校验挡住。** 它读 `node.argument_evidence` 与
   `metadata["argument_prediction_status"]`，二者都由 `apply_predicted_arguments` 注入，所以 full 臂必须传
   `--argument-predictions`；而原校验是 `--argument-predictions requires argument_pooling_predicted`，
   full 臂**根本起不来**。
2. **`--argument-predictions` 同时决定语料。** 传了走 `load_maven_ere`，不传走 `load_maven_arg`。
   remove-core 若按「不需要论元就不传」来写，就会**换一个语料训练**，直接破坏契约的
   「2 与 4–6 的 pair population 逐位一致」。
   ⇒ 校验方向改成单向：**消费组件必须有预测文件，预测文件不要求有消费者**（remove-core 传它只为对齐语料）。
3. **⚠️ A 类：训练与推理口径不成对。** permutation 臂训练在置换后的 role 向量上，但
   `SupervisedCoreferenceScorer` 不知道这回事，推理会用**真实**向量——评的是一个从没被训练过的模型。
   修法是让 seed 随 checkpoint 走：`coref_config.json` 记 `role_permutation_seed`，
   `src/ekg/nodes/coref.py` 读到就在推理侧做同一置换（`random.Random(seed)` 独立实例，跨进程可复现）。
   **因此 `coref.py` 进了 preflight 的 `CODE_FILES`**——置换发生在推理侧，它就是被冻结机制的一部分。

另加一条 fail-fast：`--permute-role-features` 而组件里没有 `role_compatibility` 直接拒绝，
否则跑出来的是一个**挂着负控标签的 remove-core 数字**。

### 两条 baseline 的官方口径已实测（为 C5.1 预先验证，非新结果）

C5.1 要用官方 evaluator 重算主锚与注册负面对照。写 preflight 前先手工验了一遍，
用本地从 `manifest + source` 物化的 291 篇 internal-dev：

| baseline | 官方 MUC F1 | B³ | CEAFe | BLANC | 来源 |
|---|---:|---:|---:|---:|---|
| MAVEN-ERE official joint（主锚） | **80.9847** | 98.0399 | 97.7316 | 89.8801 | `anchors/identity/official_joint_prediction.jsonl` |
| Qwen3 论元池化（注册负面对照） | **80.3676** | 97.9515 | 97.6166 | 89.8015 | `baselines/identity/qwen3-argument-s13-r2/predictions.jsonl` |

两点都对上了：主锚 `.809847` 与 `EXPERIMENT_PLAN.md` §7.3 一致；负面对照与
`PHASE_R1.md` 那句「同次 cross-check 的 MUC 为 80.37」「BLANC 89.80」一致。

⚠️ **顺带排掉一个口径陷阱**：`qwen3-argument-s13-r2/metrics.json` 是**内部 scorer**（`scorer: supervised`）
写的，与主锚的官方 evaluator 不是一个东西。差点按「内部 vs 官方混表」报出去——
结果页早已交叉核验过两者一致，**核到底才发现不是问题**。这正是 `ENGINEERING_NOTES` 那条
「报差值前对齐评分器·文档集·校正三条轴」要防的。

另一条实测：anchor 的分数是拿 `.../a3-v6-baselines-r10/preflight/data/MAVEN_ERE/valid.jsonl`
（SHA-256 `bb8c6b48…`）打的，而 preflight 会自己物化 internal-dev（A4.1 那份是 `403b69a8…`）。
**两个文件 hash 不同**，所以不能假设同分——实测：自物化的 gold 打出 **80.9847**，与 anchor 记录**逐位相同**。

### 冻结的训练预算来自对照本身，不是这里选的

契约要求矩阵 4–6 与注册对照的预算逐位一致，所以 `FROZEN_TRAINING` 读自
`gpu-4090:.../ch1/qwen3-argument-s13-r2/checkpoint/coref_config.json`：
`lr 2e-5`、`head_lr 2e-5`、`warmup_steps 200`、`accum_steps 1`；epochs 10、固定 endpoint epoch 10、
threshold `.7`、band `0` 来自该次运行的 `metrics.json`。**没有一个数字是本轮挑的。**

### 产物

- `scripts/run_c5_argument_uncertainty.py` —— 三臂驱动，`--arms` 可分卡、`--aggregate` 单独汇总；
  coverage 直接对 gold 计数（官方 scorer 会静默补 singleton，丢 mention 会**得分**而不是失败），
  gate 只**报告**不裁决；
- `scripts/prepare_c5_argument_uncertainty_preflight.py` —— `CODE_FILES` **8 个**（含 `coref.py` 与
  `build_maven_ere_submission.py`），断言注册对照必须低于主锚，Global-Local Topic 未复现时
  写 `status: not_reproduced` + 障碍，**不静默省略**（QR-001 v1.1.0）；
- `scripts/smoke_c5_argument_uncertainty.py` —— 契约点名的四种 fixture 形状（空角色 / 多 filler /
  重复字符串 / 全 singleton）纯 CPU 实跑通过（5 对、13 维特征、全 singleton 时中介全零），
  并做 **permutation seed 的 export→reload 往返断言**；
- 16 条 targeted tests（`tests/scripts/test_train_coref_scorer_permutation.py` 5 条 +
  `tests/scripts/test_c5_entrypoints.py` 11 条）。

### 下一步

C5.1 preflight 还差一样东西：`--argument-predictions` 指向的**完整 mention-local 论元预测**
（合并产物 SHA-256 `855906d3…7142a`，在 4090）。其余输入本地全部 sha256 匹配。
C5.2 smoke 与 C5.3 pilot 需要 GPU 与授权。

## ★ C5.1 immutable preflight —— **PASS**（2026-09-13，gpu-4090，**纯 CPU，未占任何 GPU**）

### 开工自审

1. **科研价值**：C5.1 是 G-5 泳道的门，卡着 C5.2 smoke 与 C5.3 pilot；跑不过它，Ch5 在 Gate 2
   之前拿不出任何方法结果。对准 `EXPERIMENT_PLAN.md` §7.3 的表 5-3。
2. **可行性**：`prepare_c5_argument_uncertainty_preflight.py` 及其 `ekg.*` 依赖**一处 torch / transformers
   都不 import**（本轮用 AST 遍历实测，4 个文件），所以它和 A4.1 一样是 **CPU 任务**——4090 四张卡被
   他人占满**不构成阻塞**。

### 上一轮的阻塞判断是错的：那份产物一直在 4090

交接与 `PHASE_R1.md` 只记了合并产物的 SHA-256，**没记路径**，于是「在 4090」被当成了线索。
按文件名找 `*argument*` 全场落空（命中的全是无关的 DEE 项目），一度以为产物已丢。
真正的位置由**注册负面对照自己的 `metrics.json`** 指出来——它的 `scorer_path` 写着
`runs/stages/R1/r1-v61-baseline-closure-r3/ch1/...`，顺着那条线找到：

```
/data/TJK/ekg/runs/stages/R1/r1-v61-baseline-closure-r3/ch1/qwen3-full-r3/merged/predictions.jsonl
sha256 855906d39e71d5cef838c3a72515ef837803afd6a43c88e6879274bf72e7142a   73,939 行   24,671,891 B
```

**与 `PHASE_R1.md` §7 记录的哈希逐位相同。** 带走的纪律：**产物只记哈希不记路径，等于没记**——
下次写结果页时哈希与路径一起写。

### 本轮补齐的两样输入（双端 sha256 一致）

主锚与注册负面对照的预测此前只在**本地**，4090 上没有；已 `scp` 过去并双端核对：

| 文件 | SHA-256 | 大小 |
|---|---|---:|
| `anchors/identity/official_joint_prediction.jsonl` | `66ff04bac5a11ab179ef50eeca51d56dbb613b7b04eaa04b749dd99ea82ffc42` | 7,274,278 B |
| `baselines/identity/qwen3-argument-s13-r2/predictions.jsonl` | `87c089ca7b78383f0e83721671c02b7430fa28fae6a67ce1fe361dfdfe9e340c` | 108,540 B |

### 结果

`gpu-4090:/data/TJK/ekg/runs/stages/C5/c5-v61-argument-uncertainty-r1/preflight/`

| 项 | 值 |
|---|---|
| `protocol.json` SHA-256 | **`9402e88000c84627cf3bfa2ac65cb39435364a5e012e07bf83264b06430e4319`** |
| status / seed / final_valid_accessed | `pass` / 13 / **false** |
| `code_files` | **8** |
| 候选 digest | `15a3b1a548625624642130190b39411e6346866ff8594c2af2020cfbdac10910`（291 篇 / 7,195 mentions） |
| 自物化 internal-dev gold | `403b69a8a9c83e2be41e0c366fed7edcd7e00796dbd14ec6f07df7e560507e81` |
| 信任根 | P1 `1e31a9ac…f9655`（r15）· R1 `f0b4702b…50829` · t024 `9133a73c…587e7` · evaluator `32919e86…59598` |

**两条 baseline 用冻结的官方 evaluator 独立重算**（不是抄来的）：

| baseline | MUC F1 | B³ F1 | CEAFe F1 | BLANC F1 |
|---|---:|---:|---:|---:|
| MAVEN-ERE official joint（主锚） | **80.98472** | 98.039866 | 97.731576 | 89.880089 |
| Qwen3 论元池化（注册负面对照） | **80.367586** | 97.951454 | 97.61658 | 89.801549 |

- 与本文件上方 C-5b 的本地预验 **80.9847 / 80.3676 逐位一致**；
- 与 `PHASE_R1.md` 的 BLANC 89.80 一致；
- 契约断言「注册对照必须低于主锚」通过（80.3676 < 80.9847）。

**自物化的 internal-dev gold `403b69a8…` 与 A4.1 那份是同一个哈希** ⇒ 第 4 章与第 5 章确实站在
同一个候选全集上，口径三轴（manifest · 候选全集 · evaluator）跨章一致，不是各自声称的一致。

`global_local_topic` 按 QR-001 v1.1.0 记为 `not_reproduced` 并写明障碍（EasyECR
`conditionally_runnable`、KBP 2017 需 LDC 许可 → FR-016 (b)），**不静默省略**；C-2b 关掉后
用 `--global-local-predictions` 补进来即可。

### 下一步

**C5.2 smoke（10 篇、单卡一次 forward/backward/export/reload）→ C5.3 seed-13 pilot**，两者都要卡。
4090 四张卡仍被他人 vllm 占满；5090 正在跑 A4 四臂 dry-run。

## ★ C5.2 smoke · **CPU 半边 PASS**（2026-09-13，gpu-4090，`CUDA_VISIBLE_DEVICES=` 强制 CPU）

4090 四张卡仍被他人 vllm 占满，所以先跑契约点名的 **CPU 半边**（D4.2 的先例：CPU + CUDA 两半边，
产物应逐字节相同）。**CUDA 半边仍欠一张卡。**

### 冒烟抓到一个真缺陷（这正是它的用处）

首跑在训练开始前就死了：

```
ValueError: missing predictions=0 extra predictions=73497
```

`apply_predicted_arguments` 要求预测文件**不多不少**覆盖它拿到的语料，而 smoke 会把文档
subset 成 10 train + 10 internal-dev，却把**全语料**的论元预测原样递给 trainer——于是其余
73,497 个 mention 全成了「extra」。

**根因不在那个 guard**：对跑全语料的 pilot 来说，对不齐就是拿错了文件，这条 fail-fast 是对的。
**subset 的那一方才该 subset 两个输入。** 修法是 `_subset_predictions`（按 `doc_id` 过滤，
与既有 `_subset` 同形），并把全量产物的 sha256 记进 `smoke.json`，因为那才是契约钉住的身份。
提交 `886a440`，配一条测试。

### 第二个缺陷：改了被契约钉住的文件 ⇒ 必须重建 preflight，不覆盖旧的

修完 smoke 脚本后再跑，立刻被自己的契约拦下：

```
SmokeError: bound code hash drift: scripts/smoke_c5_argument_uncertainty.py
```

`scripts/smoke_c5_argument_uncertainty.py` 在 preflight 的 `CODE_FILES`（8 个）里。按 D4 的先例
**新建 `preflight-r2/`，旧的 `preflight/` 原样保留**：

| | `preflight/` | `preflight-r2/` |
|---|---|---|
| `protocol.json` SHA-256 | `9402e880…e4319` | **`8a5ed864dea501a067339c3031bdcd750c598e900d54fdf9c2448ce13ccb7868`** |
| 差异 | — | 只有 `code` 里 smoke 脚本一项，外加 `path` 字段 |
| 两条 baseline 分数 | — | **逐项相同**（`official_joint` / `qwen3_argument_pooling` / `global_local_topic` 三项 `scores` 全等） |
| internal-dev gold | `403b69a8…07e81` | **同哈希**，候选 digest 与 population counts 全等 |

⇒ 重建 preflight 顺带给了一次**免费的可复现性检查**：换一个输出目录重跑，官方口径的两条 baseline
分数一位不差。

### 结果

`gpu-4090:/data/TJK/ekg/runs/stages/C5/c5-v61-argument-uncertainty-r1/smoke-cpu/`

| 项 | 值 |
|---|---|
| `smoke.json` SHA-256 | `30bae362ceabbab549f279876d5cb91f49ad132233e89ef68f43e9c4d64589b0` |
| status / seed / final_valid_accessed | `pass` / 13 / **false** |
| 绑定契约 | `8a5ed864…b7868`（`preflight-r2`），`contract_status=pass`，8 个 code 文件逐个重哈希 |
| 论元产物 | `855906d3…7142a`（全量身份） |
| 文档 | train 10 / internal-dev 10（按 manifest 顺序取前 10，trainer 自己的 split guard 照常生效） |
| 三臂 config SHA-256 | full `1d3a4aab…` · remove_core `48a2481e…` · permutation `3b279b11…`，**两两不同** |
| permutation 种子往返 | checkpoint 里 `role_permutation_seed=13`，full/remove_core 为 `None` ✅ |
| CPU fixture | 四种形状（空角色 / 多 filler / 重复字符串 / 全 singleton）特征有限、宽度一致、全 singleton 时中介归零 |

训练侧读数（**仅证明跑得通，不是结果**）：8/10 篇有对、245 个训练对（64 正 / 77 hard negative）；
三臂各 1 epoch 均正常收敛并导出、重载。

### 下一步

**C5.2 的 CUDA 半边**（同命令去掉 `CUDA_VISIBLE_DEVICES=`，断言与 CPU 半边产物一致）→ **C5.3 pilot**。
两者都要一张空闲卡。

## ★★★ C5 改走 gpu-5090 线：preflight 与 CPU/CUDA 双半边全部 PASS（2026-09-15）

### 开工自审

1. **科研价值**：C5.3 是 Gate 2 要等的两跑之一（另一跑是 A4.3），对准 `EXPERIMENT_PLAN.md` §7.3
   的表 5-3。4090 四张卡自 2026-09-10 起被他人 vllm 占满，到本日已第 6 天，Gate 2 再等就滑出排期。
2. **可行性**：成立，且**只对 C5 成立**——它的两条 baseline 是**预测文件 + 官方 evaluator 打分**
   （主锚 MUC 80.98472 / 注册对照 80.367586），**与我们的 encoder 无关**；换到 5090 后三臂同机、
   同 backbone、同 manifest，口径三轴天然一致。**A4 不能这样搬**：它的判定线含 A3 fallback 32.10，
   那是在 4090 pin 上训出来的（G-13 实测同一臂在 5090 backbone 上 31.13），换机就引入混淆。

### 作者裁决（2026-09-15）

> 「按照你的推荐进行，允许使用 5090。后续 4090 可以补，现在先在能使用的 GPU 上进行后续的任务，
> 不要因为 4090 拖慢进度。」

### backbone pin 的更换（`45c2bbf`）

`prepare_c5_argument_uncertainty_preflight.py` 的 `EXPECTED_MODEL_SHA256`
由 4090 线 `71be7419a60dcce0…` 改为 5090 线
`2c7ff1f10496f2df54ed5590693c38c6bc2385bebf29e37b26e4833407349736`。

⚠️ **两个 pin 装的是同一份权重**：5090 的六个文件里五个与 4090 pin 逐字节相同（含 476 MB 的
`pytorch_model.bin`），只有 `tokenizer_config.json` 不同（公网三个源都不提供 4090 那份）。
**同权重、不同内容地址 ⇒ 必须 pin，不能假定相等。** 4090 的 preflight（protocol `9402e880…e4319`）
保持不变、仍然有效，本轮**另建**一份，不覆盖。

### 搬到 5090 的输入（双端 sha256 全部一致）

| 文件 | SHA-256（前 20） | 大小 | 来源 |
|---|---|---:|---|
| `runs/stages/R1/r1-v61-20260904/protocol.json` | `f0b4702b258ef612` | 8,792 B | 本地（5090 旧档 `67a36354…` 已备份为 `protocol.json.pre-c5-20260915`） |
| `…/phase_contracts/t024_freeze.json` | `9133a73c46d7e277` | 3,499 B | 本地（5090 原本没有） |
| `…/baselines/identity/qwen3-argument-s13-r2/predictions.jsonl` | `87c089ca7b78383f` | 108,540 B | 本地 |
| `runs/stages/P1/p1-v6-20260904-r15/protocol.json` | `1e31a9acef39261f` | 8,545 B | 本地（5090 只有 r13/r14） |
| `…/qwen3-full-r3/merged/predictions.jsonl` | `855906d39e71d5cef838` | 24,671,891 B / **73,939 行** | **gpu-4090**（全项目唯一副本），经本地中转 |

`anchors/identity/official_joint_prediction.jsonl`（`66ff04ba…`）与 evaluator（`32919e86…`）5090 上
本来就有且哈希一致，未重传。合并论元预测单程实测 **3 分 10 秒 / 24.7 MB ≈ 130 KB/s**。

### C5.1 preflight（5090 线）

| 项 | 值 |
|---|---|
| `protocol.json` SHA-256 | **`a3f21f971caec14f39338b649fd586df1604f3ea46c887d83f68315fcb148141`** |
| 位置 | `gpu-5090:/mnt/aidata/tongjiakai/ekg/runs/stages/C5/c5-v61-argument-uncertainty-5090-r1/preflight/` |
| status / seed / `final_valid_accessed` | `pass` / 13 / **false** |
| `code_files` | 8 |
| 候选 digest | `15a3b1a548625624642130190b39411e6346866ff8594c2af2020cfbdac10910` |
| backbone | `2c7ff1f10496f2df…`（5090 线） |

**两条 baseline 在 5090 上用同一个冻结 evaluator 独立重算，与 4090 线逐位相同**：

| baseline | MUC F1 | B³ F1 | CEAFe F1 | BLANC F1 |
|---|---:|---:|---:|---:|
| MAVEN-ERE official joint（主锚） | **80.98471986417657** | 98.03986586953673 | 97.7315760306983 | 89.88008897647808 |

⇒ **这组数与 backbone 无关这件事，从论证变成了实测**。`global_local_topic` 仍记
`not_reproduced` 并带障碍文本（EasyECR `conditionally_runnable`、KBP 2017 需 LDC 许可 → FR-016 (b)）。

### C5.2 CPU / CUDA 双半边：都 PASS

| 半边 | 产物 | 三臂 best dev pair-F1（10 篇 / 1 epoch） |
|---|---|---|
| CPU（`CUDA_VISIBLE_DEVICES=`） | `…/smoke-cpu` | full 0.2222 → permutation 0.2469 |
| CUDA | `…/smoke-cuda` | permutation 0.2273 |

契约（`phases/PHASE_C5_argument_uncertainty.md` §C5.2）要求的四条断言两边都过：logits/loss/uncertainty
有限、每个 mention 恰好一个 cluster、完整候选未变、gold argument 未被读取。
⚠️ **契约没有要求 CPU 与 CUDA 产物逐字节相同**（那是 D4 的形态），本轮也**确实不同**——
10 篇 / 1 epoch 下 permutation 臂 CPU .2469 vs CUDA .2273。**如实记，不当缺陷处理**；
这两个数是冒烟的健康指示，不是结果。

### 下一步

**C5.3 seed-13 pilot（三臂）**，命令只需 `--contract …/preflight/protocol.json` 与 `--output`，
其余参数全部来自契约。按 A4 单臂实测速度（2,622 篇 × 6 分钟/epoch）粗估 3 臂 × 10 epoch ≈ 3–6 小时，
在 5090 的「≤1 天」授权内。

## ★ C5.3 首跑失败 → 根因修复 → preflight-r2 → 重跑（2026-09-16，gpu-5090）

### 首跑怎么死的

`full` 臂**训练跑完 10 epoch**，倒在 predict 步：

```
ValueError: 7028d05b…::bbbd0de0…: argument state is None, expected one of ('ok','empty','partial','rejected')
  role_uncertainty.py:69 mention_argument_state
  ← discriminative.py:253 pair_head_inputs ← coref.py:385 score
  ← build_maven_ere_submission.py:112 predict_coreference
```

逐层核到的事实（数据一侧全部清白）：

| 核查点 | 结论 |
|---|---|
| 论元预测文件 | ✅ 73,939 条**全部**带 `status`，取值就是契约要的四种（ok 72,183 / empty 1,123 / partial 591 / rejected 42） |
| `mention_argument_state()` | 读 `node.metadata["argument_prediction_status"]`（`role_uncertainty.py:47,67`） |
| 谁写这个键 | 只有 `predicted_arguments.py`，而**推理路径从没调过它** |
| pilot 的两条命令 | 训练带 `--argument-predictions`，predict **不带** |
| `build_maven_ere_submission.py` | **CLI 里根本没有这个选项** ⇒ 推理侧物理上拿不到论元层 |
| 冒烟为什么没抓到 | 它 train/export/reload 全做，**从不运行 `build_maven_ere_submission.py`** |

**与 C5.2 冒烟抓到的 A 类缺陷同族**（「训练/推理口径不成对」），换了条路径复发。

### 修法（`a1e1509` + `a65f456`）

- 提交脚本加 `--argument-predictions`，在遍历前一次性绑定；
- `apply_predicted_arguments` 加 `allow_extra`：推理只标注 2,913 篇里的 291 篇，**missing 仍然致命**，
  只放开 extra。⚠️ 反过来做（把文件裁到 291 篇）会让训练与推理拿到**两个不同的产物**——正是这条绑定
  要防的东西；
- pilot 的两条命令改由 `train_command` / `predict_command` 生成，**配对关系无需 GPU 即可断言**；
- **冒烟补上推理路径**（每臂训完跑一次提交脚本，且故意让预测文件宽于被标注的文档集）；
- ⛔ fail-fast **原样未动**：没有默认 state，没有放宽断言。

**4 条新 targeted tests，639 passed / 29 skipped（原 635）、ruff 0、`ekg-smoke` OK。**

### 修复验证：用首跑遗留的 `full` checkpoint 重放 predict（先冒烟再训练）

不重训，直接拿 `pilot/full/checkpoint/epochs/epoch-10` 跑那条**原样失败过**的命令 + 新选项：

```
291/291 documents, 251 non-singleton clusters, exit 0
runs/scratch/c5_predict_fixcheck/predictions.jsonl
```

⇒ 修的是对的那处，且在真实的 291 篇 / 7,195 mention 规模上验过，**不是靠推理**。
这份产物只用于验证，**不进任何表**。

### preflight-r2（旧 `preflight/` 不覆盖）

改了 3 个被契约钉住的文件，按 D4/C5 先例重建；同时补上一个真缺口——
`src/ekg/nodes/predicted_arguments.py` **决定每个 mention 拿到什么 argument state，却没被哈希钉住**，
现已进 `CODE_FILES`（8 → 9）。

| 项 | 值 |
|---|---|
| `protocol.json` SHA-256 | **`7a56e451d45436d3160488bc301fe244384332a423131b5b2ccb93cd6c75b6b0`** |
| `code_files` | **9**（旧 r1 = 8） |
| status / seed / `final_valid_accessed` | `pass` / 13 / **false** |
| 候选 digest | `15a3b1a5…dac10910`（与 r1 同） |
| 自物化 internal-dev gold | 与 r1 **同哈希** |
| 两条 baseline 独立重算 | MUC **80.98471986417657** / **80.36758563074353**，与 r1、与 4090 线**逐位相同** |

（中途踩了一个小坑：`--output` 是 **protocol.json 的文件路径**，不是目录；第一次传成目录名，
把 `baselines/`、`data/` 写到了 stage 根下。误写的三样当场删除，`preflight/` 与 `pilot/` 未被触碰。）

### 重跑

`runs/stages/C5/c5-v61-argument-uncertainty-5090-r1/pilot-r2/`，契约 `7a56e451…b6b0`，
三臂全部重训——**不复用 r1 契约下训出来的 `full` checkpoint**：一个产物只挂一个契约，
省那一小时不值得在结果页上加一条例外脚注。

## ★★★ C5.3 seed-13 pilot-r2（三臂）：**机制方向对了，但整条 head 仍低于主锚**（2026-09-16，gpu-5090）

产物 `gpu-5090:…/c5-v61-argument-uncertainty-5090-r1/pilot-r2/`，契约
**`7a56e451d45436d3160488bc301fe244384332a423131b5b2ccb93cd6c75b6b0`**（preflight-r2，`code_files=9`），
seed 13，`final_valid_accessed=false`。覆盖断言三臂全过：**291 篇 / 8,914 gold mention，
重复 0、陌生 0**（8,0xx 个是合法单例——官方 scorer 自动补单例，所以覆盖按 gold population 数，
不从指标反推）。

### 主表（官方 evaluator，internal-dev 291 篇）

| 臂 | **MUC F1** | vs 主锚 `80.98472` | vs 注册对照 `80.36759` | B³ F1 | CEAFe F1 | BLANC F1 | 入簇 mention |
|---|---:|---:|---:|---:|---:|---:|---:|
| **full**（role-compatibility 残差） | **79.90115** | **−1.084** | **−0.466** | 97.9177 | 97.5374 | **90.2893** | 891 |
| remove_core（无残差，同语料同预算） | 79.15966 | −1.825 | −1.208 | 97.9034 | 97.4814 | 89.6895 | 856 |
| permutation（负控，文档×事件类型内打乱） | 78.83333 | −2.151 | −1.534 | 97.8301 | 97.4640 | 89.5839 | 879 |

**`gate.above_anchor=false`、`gate.above_registered_control=false`**（driver 只报不判，判在这一页）。

### 三条读法

1. **臂序第一次是对的**：`full` > `remove_core` > `permutation`，**MUC 与 BLANC 两个指标同向**
   （+0.742 / +1.068 与 +0.600 / +0.706）。这是本项目 7 个机制里**第一个负控最低、消融居中的**
   ——D4 是负控赢过 full，A4 是消融赢过 full 21 点。**机制本身不是噪声或反向。**
2. ⚠️ **但门没过**：`full` 比冻结主锚低 **1.08** MUC，比注册负面对照也低 **0.47**。
   Ch5 的成功条件是「在统一公开主指标上超过冻结主锚」，**seed 13 上没有做到**。
3. **B³ / CEAFe 三臂几乎不动**（97.83–97.92 / 97.46–97.54）：8,914 个 mention 里 8,0xx 是单例，
   这两个指标被单例主导，**区分度在 MUC 与 BLANC 上**。报 Ch5 时别拿 B³ 的「三臂都 97.9」当稳健性证据。

⚠️ **+0.742 这个差先别当效应**：本 split / 本指标的**可复现地板还没量过**（D4 的 ±.01 是
macro-F1 的地板，不能搬过来）。要把臂序写成结论，得先有 MUC 的噪声地板或配对统计——
**这属于 Gate 2 之后的事，本轮不据此改设计**。

### 与 D4 的对照：同一个形状，不同的位置

D4 的 `remove_core .536788` 就已经低于锚 `.553995` ⇒ **整个 head 低于基线**，机制上场前已经输了。
C5 是同一形状：`remove_core 79.16` 低于锚 **1.83**，机制把它抬回 **79.90**，**抬了但没抬过线**。
⇒ 差距的主要来源不是「role-compatibility 有没有用」，而是**我们这条监督共指 head 本身比官方 joint 低**。
这条留给 Gate 2，**不在本轮改**（改了就是看到分数再改设计）。

### 下一步

Gate 2 的两个输入现在到了一个（C5.3 ✅ / A4.3 仍等 4090 空卡）。**Gate 2 之前不启动 C5 第二周期**，
也不跑 seed 17/42（未授权，且 `gate` 两项皆 false 本就不满足 matched-seeds 的前置）。

---

## ★★ G-5b C5 差距归因：**那 1.83 的主体是误合并，不是漏合并**（2026-09-17，本地纯 CPU，未训练、未占卡）

### 开工自审

1. **科研价值**：C5.3 判出「`remove_core` 本身就比主锚低 1.83 ⇒ 输的是主干不是机制」，但**没说清
   这 1.83 是什么错误**。不拆开，Gate 2 的改纲裁决就只有一个「低了 1.83」的标量；拆开之后，
   「C5 该不该有第二周期、第二周期该改什么」才有事实依据。对准的是 `EXPERIMENT_PLAN.md` §5 Gate 2
   的「≤1 章过」分支与 §7.3 的表 5-3。证据来源是本页 C5.3 节那三行数字 + 契约登记的主锚预测。
2. **可行性**：三臂预测、主锚预测、gold、官方 evaluator **全部已存在且哈希已登记**；
   工具 `scripts/report_coref_error_profile.py` 仓库里**本来就有**（它正是为「MUC 只给三个比率、
   不给两个方向各自多少个决策」写的）。纯 CPU、分钟级、不训练、不改代码 ⇒ **五个方面全部可行**。

⛔ **这不是 C5 的第二设计周期**：没有改代码、没有重训、没有调任何阈值，只读已冻结的产物。

### 怎么算的（四条命令，可重跑）

工具复用 `scripts/report_coref_error_profile.py`（未改动）。它把错误质量拆成两个方向、两种货币，
并且**在打印任何数字之前先用官方 `evaluate.py` 交叉验证一遍**——四个系统的交叉验证分依次是
**80.98 / 79.90 / 79.16 / 78.83**，与本页 C5.3 主表和契约 `baselines.official_joint.scores`
**逐位相同**，所以这一节的分解与主表口径同轴。

```bash
R=runs/stages/C5/c5-v61-argument-uncertainty-5090-r1
for pred in $R/pilot-r2/full $R/pilot-r2/remove_core $R/pilot-r2/permutation; do
  uv run python scripts/report_coref_error_profile.py \
    --evaluator data/protocols/v6/tools/maven_ere_evaluate.py \
    --gold $R/preflight-r2/data/MAVEN_ERE/internal-dev.jsonl \
    --pred $pred/predictions.jsonl --output $R/gap-analysis-20260917/$(basename $pred).json
done
# 主锚（本地早有，见本页「本轮补齐的两样输入」）
uv run python scripts/report_coref_error_profile.py \
  --evaluator data/protocols/v6/tools/maven_ere_evaluate.py \
  --gold $R/preflight-r2/data/MAVEN_ERE/internal-dev.jsonl \
  --pred runs/stages/R1/r1-v61-20260904/anchors/identity/official_joint_prediction.jsonl \
  --output $R/gap-analysis-20260917/official_joint.json
```

**输入哈希（本地 ⇄ 5090 双端一致，本轮 rsync 回本地时重核）**：
契约 `7a56e451…b6b0`、gold `internal-dev.jsonl` `403b69a8…07e81`（= 契约 `internal_dev_gold.sha256`）、
evaluator `32919e86…59598`（= 契约 `evaluator.sha256`）、主锚预测 `66ff04ba…7f642`（= 契约
`baselines.official_joint.predictions_sha256`）。产物落 `$R/gap-analysis-20260917/`（`runs/` 不进 git）。

### 主表：四个系统的错误方向（官方 MUC 口径，291 篇 / 7,195 gold mention）

| 系统 | MUC F1 | MUC P | MUC R | **漏合并**（missing links） | **误合并**（spurious links） | 被完全打散的 gold 簇 | 预测多 mention 簇 |
|---|---:|---:|---:|---:|---:|---:|---:|
| **主锚 official_joint** | 80.98472 | **0.788430** | 0.832461 | **96** | **128** | 55 | 225 |
| **full**（机制） | 79.90115 | 0.756630 | **0.846422** | **88** | 156 | **49** | 250 |
| remove_core | 79.15966 | 0.763371 | 0.821990 | 102 | 146 | 56 | 239 |
| permutation（负控） | 78.83333 | 0.754386 | 0.825480 | 100 | 154 | 51 | 252 |

pairwise 口径（pair 分类器实际训练的货币）同向：误合并 394 / 419 / 398 / 397，漏合并 222 / 184 / 229 / 235。

### 1.825 拆到哪里去了（反事实分解：只把一个分量搬到主锚水平）

| 反事实 | MUC F1 | 相对 `remove_core` | 占那 1.825 的 |
|---|---:|---:|---:|
| `remove_core` 实测 | 79.15966 | — | — |
| **只把 precision 搬到主锚水平**（误合并 146 → 128） | **80.48600** | **+1.326** | **72.7%** |
| 只把 recall 搬到主锚水平（漏合并 102 → 96） | 79.64204 | +0.482 | 26.4% |
| 主锚实测 | 80.98472 | +1.825 | 100% |

⇒ **我们这条监督共指主干输给官方 joint，主要是「把不该合并的合并了」，不是「该合并的没合并」。**
误合并多 18 条链（146 vs 128，+14%），漏合并只多 6 条（102 vs 96，+6%）。

### 机制（`full`）实际做的事，与它剩下的 1.084 在哪

机制换来的是 **漏合并 102 → 88（−14）**，付出的是 **误合并 146 → 156（+10）**——
买 recall、卖 precision，净 +0.742 MUC。两个副作用与之一致：被完全打散的 gold 簇 56 → **49**
（**比主锚的 55 还少**），预测多 mention 簇 239 → 250。

由此得到本节最要紧的一条：

> **`full` 的 MUC recall 0.846422 已经超过主锚的 0.832461（+0.0140）。
> 它与主锚剩下的 1.084，100% 落在 precision 上（0.756630 vs 0.788430，−0.0318）。**

反事实推算：若 `full` 的误合并率压到主锚水平而 recall 不变，MUC F1 为 **81.640**，**超锚 +0.655**。
⚠️ **这是算术推演，不是实测，不得当作结果引用**；它的用处只是给出一个有量纲的靶子。

### 可检验的假设（供 Gate 2 裁决参考，本轮不执行）

**H1｜误合并集中在「trigger 长得像」的跨句对上，而这正是 role-compatibility 本该拦住的一类。**
`full` 的 419 个误合并 pair 里 trigger 相似度 ≥0.8 的占 **58.0%**（243 个），主锚只占 **51.5%**；
跨句比例两边都在 88–91%。即：机制在表面相似度高的对上**没有起到抑制作用**，甚至被带偏。
可检验方式：按 trigger 相似度分层报 `full` 与 `remove_core` 的误合并增量，若增量集中在 ≥0.8 桶，
H1 成立，则第二周期该改的是**把角色相容性接到抑制侧**（当前它只作为正残差抬分），而不是继续加 recall。

**H2｜B³/CEAFe 在本 split 上无鉴别力，别拿它们写稳健性。** 7,195 个 gold mention 里
**6,386 个是单例簇**（88.8%），只有 236 个多 mention 簇。已在 C5.3 节写过，这里给出计数依据。

### 限制（三条，都要随结论一起报）

1. **+0.742 仍不是已确证的效应**——本 split / 本指标的噪声地板**至今没量过**（D4 的 ±.01 是
   macro-F1 的地板，不能搬）。本节只解释差距的**构成**，不把臂序升格为结论；
2. 反事实分解是 **F1 对 P/R 的代数分解**，假设搬动一个分量时另一个不变。真实系统上压误合并
   通常会同时掉一点 recall ⇒ 上表的 72.7% / 26.4% 是**归因权重，不是可兑现的增益**；
3. 单例由官方 scorer 自动补齐，本节所有计数都在官方 mention population 上算，与主表同轴。

### 下一步

本节**不触发**任何执行动作：C5 第二设计周期是否开、以什么形态开，属于 Gate 2 的改纲裁决。
H1 的分层验证若获批，是纯离线分析（现有四份 `gap-analysis-20260917/*.json` 已含相似度桶，
逐对清单需要小改脚本输出）。
