# EKG TODO / 实时状态

> 更新于 **2026-07-29**。本文件只记录 v4 的当前执行位置、已验证证据和下一步；设计定义见
> [`SPEC.md`](SPEC.md)，阶段验收见 [`phases/`](phases/README.md)，历史路线的留档索引见
> [`ARCHIVE_INDEX.md`](ARCHIVE_INDEX.md)（正文已移出仓库）。

## 当前结论

- **唯一主线**：v4 四章可信事件图谱构建（身份 → 结构 → 事实 → 传播/下游），headline 是 Ch4
  **构建误差向下游的传播、归因与预算**。
  ⚠️ **2026-07-29 headline 已重定位**（作者拍板）：原「下游门控闭环修复」按自己的实测降级——
  门控可挽回的天花板实测 ≈**0.24%**，且「仅在下游改善时接受编辑」的一般命题已被
  Kintsugi(2605.09487)/DeepRefine/CauScientist 占先。修复**保留**为 Ch2 交付物与 Ch4 中
  **被精确测量、可归因的干预**，但不再声称它提升下游。依据与数字见下「文献驱动的两条探路」段与 SPEC §1。
- **关键路径进展**：Phase A ✅ 达标（causal F1 .250，召回 .4%→67.5%）→ Phase B 🟡 违反清零但下游无增益
  （止损）→ Phase C 🟢 MUC 79.6 vs 官方 81.4 基本达标 → Phase D 🟡 检测达标（valid macro-F1 .4823）、
  净化止损 → **Phase E 🟢 主结果已出**（2026-07-29）：三图误差分解完成，**构建损失 −.0218 MRR
  是唯一确凿的效应**，修复只值它的 5.1% 且与强对照不可分，**净化下游 = 0（oracle 亦然）**，
  端到端风险地板 α ≥ .2935。**关键路径转 Phase F（端到端预算）**；所有噪声级结论待 Phase H 多种子定论。
- **执行状态**：P0 数据完成；A/B/C/D 均已跑出真实数字（见下各节，升降如实）。
  **两个未决口径已于 2026-07-29 拍板**：① Ch4 headline 重定位为「误差传播、归因与预算」（见上）；
  ② Phase D 净化的下游价值仍由 E 判定，**E 必须正面回答、不得绕开**；若 E 也无增益，
  Ch3 按止损口径退为「事实性检测 + 预测图鲁棒性分析」独立成章。
  ⚠️ **新的发表阻断项**（SPEC §4.5）：只要论文出现任何「按下游信号接受/拒绝编辑」的实验档，
  **门控信号就不得直接用金标 MRR**（TACL 2406.01297 把 oracle 泄漏列为致命设计缺陷），
  必须二选一：在线可得的无标签代理，或显式定位为离线构建期质检工具。
- **旧线定位**：SeDGPL、M1/M2、CS-CRP 和受控 cross-stage 扫描保留为 Ch4 可靠性模块；
  **SARGE / Phase G 金融应用层已于 2026-07-27 移出主干**（快照取回见 [`ARCHIVE_INDEX.md`](ARCHIVE_INDEX.md)）；
  旧实体中心 TKG 只在 tag `frozen-tkg-line`。
- **2026-07-23 联网复核**（结论并入 [`EXPERIMENTS.md`](EXPERIMENTS.md) + SPEC §4.5/§5）：数据/SOTA/baseline/
  评测协议全部真实可得，方案可执行；三个必修点——① **Phase A** 唯一硬骨头（0.4%→SOTA 30–37，有文献路线）；
  ② **Ch4 门控 oracle 澄清**（SPEC §4.5）；③ **新竞品 DeepRefine 2605.10488** 收窄 headline（SPEC §5）。
  Ch4 baseline 已补 2025 方法（Semantic Relation Experts 2506.06910 / 现代 LLM），弃用旧 Llama3/GPT-3.5。

## 已完成并有证据

### 工程与数据

- 冻结 schema、I/O、registry、图算法、通用评测与 calibration 原语已实现。
- MAVEN-ERE / MAVEN-Arg / MAVEN-FACT 公开 train/valid 已处理并在 WSL 与 4090 就位；三套数据的
  doc-id 对齐关系已核验。官方 test 标签隐藏，不进入本地调参。
- DocEE、It-Happened、ModaFact 已有 processed manifest；MATRES、RAMS、WikiEvents、ECB+ 当前仅 raw
  就位，尚无项目 processed 输出，不能写成“已预处理”。详见 `DATASET_SURVEY.md`。
- 主干验证（2026-07-27 重构后）：`241 passed / 12 torch-skip`、Ruff 0 error、`ekg-smoke` 通过。
  ⚠️ 目录改名后 `.venv/bin/` 的第三方 console script shebang 会失效，须 `uv sync --extra dev --reinstall`
  才能用 `uv run pytest`（详见 [`ENGINEERING_NOTES.md`](ENGINEERING_NOTES.md)）。

### Phase A 实施（2026-07-23，代码层已完成）

- `@register("supervised")` 判别式抽取器：文档级候选与标签**复用 `relations/pairs.py`**、torch-lazy（CPU 可
  导入/实例化）、`extract` 产 evidence-grounded 边；训练脚本 `train_supervised_relations.py`（确定性负采样 +
  逆频类权重 + 加权 CE）；`configs/relations/supervised.yaml` 接**既有两段式评测**
  （`evaluate_relations --dump-predictions` → `evaluate_relation_pairs`，零新写评测脚本）。
  CPU 测试 10 passed + 1 torch-skip；全量 pytest / ruff / ekg-smoke 全绿。
- **修复触发词定位缺陷**：MAVEN-ERE `trigger_word` 是小写形式而句子保留原始大小写，句首/专名触发词精确
  `find` 必然失配（实测 train_smoke 6/919 = 0.65%、valid_smoke 4/637 = 0.63%）；改**大小写不敏感 + 词边界**
  后降为 **0.00%**。该问题由训练侧 fail-fast 暴露——loader 对同样失配是容忍的（记 `span=(0,0)`）。
- 全量训练完成（2913 docs × 3 epochs，loss 4.12 → 2.49 → 2.04 → 1.76）。**首轮 pair-classification
  评测（valid 710 篇）如实结果：**

  | 关系 | P | R | F1 | 调阈值后最佳 F1 | 目标 |
  |---|---|---|---|---|---|
  | causal | .049 | **.675** | .091 | **.167**(thr .9) | ≥.25 ❌ **未达标** |
  | subevent | .043 | **.881** | .082 | **.206**(thr .95) | ≥.20 ✅ |
  | temporal | .191 | .575 | .286 | .317(thr .5) | — |

  - **召回瓶颈已破**：causal recall **0.4% → 67.5%**、subevent **0% → 88.1%**，`hallucinated=0`
    （判别式不产生端点不存在的幻觉边，相对生成式的结构优势）。
  - **但 precision 崩**：阈值扫到 .99 时 causal P 仅 **.240** → 模型未学出判别边界，**不是决策规则问题**，
    阈值救不回来。
  - **诊断**：负采样 3:1 vs 真实候选分布约 63:1，再叠加逆频加权 CE = **双重补偿**，把模型教成宁滥勿缺。
  - **类不平衡消融（已完成一轮 α 扫描，各配置最佳阈值的 F1）：**

    | neg30 配置 | causal F1 | subevent F1 | temporal F1 |
    |---|---|---|---|
    | α=1.0（inverse） | .161 | .202 ✅ | .316 |
    | **α=0.5** | **.234** | **.221** ✅ | **.397** |
    | α=0.25 | .232 | .219 ✅ | .416 |
    | α=0.0（none） | .186 | .041 ❌ | .407 |
    | 目标 | ≥.25 | ≥.20 | — |

    - α 曲线**倒 U 形，最优在 0.25–0.5**；per-family α（给 causal 更高 α）**反而降 causal F1**
      （.234→.219→.205）→ causal 瓶颈不在权重强度。**neg-ratio 在 α=1 时几乎无效**（逆频权重抵消负采样）。
    - **✅ 达标（2026-07-24）**：`neg30 · α=0.5 · 6 epochs` —— **causal F1 .250 / subevent .213 /
      temporal .338**（阈值 0.7，micro .311，`hallucinated=0`）。3→6 epochs 是决定性一步（loss 1.25→0.92
      仍在降＝3ep 欠拟合），把 causal .234→**.250** 推到目标下沿。交付 checkpoint = `runs/relations/supervised_maven`。

### Phase B 实施（2026-07-25，W1–W4 代码完成 CPU 全绿）

在 Phase A 的边打分之上加三件（复用既有 consistency/admission/cgep/grounding，不重写）：

- **W1 可追溯修复**（`relations/consistency`）：`RepairEdit`/`RepairTrace` + `solve_with_trace`；
  `GreedyConsistencySolver` 发出每条 drop/add 审计（violation ∈ {causal_cycle, temporal_cycle,
  temporal_closure, coref_dedup, temporal_dedup, subevent_dedup}）与 before/after `consistency_report`
  快照。`_break_cycles`/`_dedup` 重构为 traced 版本，**`solve()` 输出逐字节不变**（新增默认锁测试
  `solve(g).edges == solve_with_trace(g)[0].edges`）；`identity` 自动 no-op。
- **W2 分层 FNR**（`relations/admission`）：`stratified_admission_report` 报**边际**（CRC 边界所在层）/
  **分族**（causal/temporal/subevent/coref 各自 recall→FNR）/**doc-macro**（按篇平均 FNR）+ 准入集大小；
  表述按 SPEC §5.5——交换性 + 固定后处理下的**边际期望 FNR**，不写「每篇/每类都保证」。不动 `admission_report`。
- **W3 ECG 可重建率**（新 `succession/reconstruction`，复用 `extract_ecgs` 口径）：**R1 query 边可达率**
  （召回义，= CS-CRP `run_cross_stage` 消费的 `reachable` 标志）+ **R2 query 边保真**（precision 义，
  修复去矛盾环后可升）。层级放 succession 侧避免 core→succession 倒置。
- **W4 离线编排**（`scripts/consistency_repair_report.py` + `configs/relations/supervised_dump.yaml`）：
  消费**原始边 dump**（GPU 端 `evaluate_relations --dump-predictions` + `consistency: identity` + 无准入）→
  每 doc 重建图 → `solve_with_trace` → CRC 准入（cal 分片校准、复刻 repair∘admit 固定映射）→ 分层 FNR +
  准入集大小 + before/after consistency + R1/R2 + 每 query `reachable` 标志。checkpoint 不下本地。

- **合成 dump 验证（CPU，如实）**：注入因果环 m1→m2→m4→m1（最弱边 conf 0.2），repair 后——
  `causal_cyclic_scc` **1→0**、`dropped=1`（violation=causal_cycle）；**R1 持平 1.0**（环不删除 query 边，
  召回不受影响）、**R2 f1 0→1.0**（环使 m4 出度 1、破坏 query 边保真，修复恢复）。**修复增益如实落在
  precision 义 R2、非召回义 R1**——与 PHASE_B 止损口径一致（R1 受 α_edge 约束可持平/略降）。
- **验证基线（两端不同不是回归）**：本地无 torch = **241 passed / 12 skipped**；服务器有 torch =
  **252 passed / 1 skipped**。ruff 0、ekg-smoke OK（只增不改）。交付当时是 269/12，2026-07-27 重构
  移除 SARGE/Phase G 测试后降到 241；**不得拿旧计数判断回归**。
### Phase B 真实图闭环（2026-07-28，首次跑通，**结果混合**）

dump 在 **gpu-5090** 上产出（4090 全天 4 卡被他人占满；5090 环境当日配好，见 `GPU_RUNBOOK.md` §−1）：
710 篇 / **242,869 条原始边**（342/篇）/ 62MB，sha256 双端一致。离线分析 497 篇 held-out test
（α=0.2、cal_ratio=0.3），产物 `runs/relations/consistency_repair_supervised.json`。

| 档 | causal_cyclic_scc | causal_cyclic_edges | temporal_cyclic_scc | temporal_cyclic_edges | temporal_closure_gap | R1 可达率 | R2 query f1 |
|---|---|---|---|---|---|---|---|
| raw（identity） | 752 | 2,290 | 614 | 36,523 | 83.78 | **0.7310** | **0.0622** |
| repaired | **0** | **0** | **0** | **0** | **0** | 0.7294 | 0.0620 |
| repaired + 准入 | 0 | 0 | 0 | 0 | 0 | 0.7294 | 0.0620 |

`repair_trace`：**dropped 8,119 / added 8,770**（补的闭包边多于删的矛盾边）。

- ✅ **一致性违反被清零**：752 个 causal 强连通分量、614 个 temporal 强连通分量（卷入 36,523 条边）
  全部消除，closure_gap 83.78→0。这一档是确凿的。
- ❌ **但 ECG 可重建率没有增益，两项都微降**：R1 0.7310→**0.7294**（-2 个 query）、R2 f1
  0.0622→**0.0620**（precision .1339→.1321）。**合成 dump 上 R2 0→1.0 的增益在真实图上没有复现。**
  机制上看得见原因：修复主要在**补闭包边**（added 8,770 > dropped 8,119），`n_pred` 381→386 而
  `tp` 恒为 51 —— 补进来的边没有命中 gold query，只稀释了 precision。
- ⚠️ **按 PHASE_B 止损口径这一条已触发**（「若 R2 增益也微弱 → 退 consistency-aware reranking /
  constrained decoding，仍成章，不换指标」）。**不粉饰、不换指标**：Ch2 的可讲点收缩为
  「可追溯修复把结构违反清零」+ 误差传播分析，**不再声称修复提升下游可重建性**。

**风控准入（分层 FNR，α=0.2）——目标不可达，原因是召回上限**：

| 层 | 数值 |
|---|---|
| 边际 | P .2675 / R .5258 / **FNR .4742** / F1 .3546 |
| 分族 FNR | coref **1.000**(n=2887，模型 n_pred=0) · temporal .4469(n=71549) · causal .5616(n=6599) · subevent .4065(n=2165) |
| doc-macro FNR | .4925 |
| 准入集 | 163,533（均值 329/篇），**τ=0.0** |

- **τ 校准出 0 = 准入退化为「全收」**，故 `repaired+准入` 与 `repaired` 逐项相同。
- 根因不是 CRC 实现，而是**可行域为空**：抽取器边际召回只有 .5258 → FNR 下界 .4742，**任何
  α < .474 的目标都不可能满足**，即使准入全部边。α=0.2 本身超出了这个 predicted 图的能力上限。
  后续要么放宽 α 到 >.48 报有意义的 τ，要么先抬 Phase A 召回。coref 一族 FNR=1.0 是因为
  supervised 抽取器在 valid 上 **coref 预测数为 0**（`n_pred=0`），不是准入把它筛掉的。

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

### Phase D 实施（2026-07-28，4090 card 2，**检测达标 / 净化负结果**）

代码（只增不改）：新包 `src/ekg/factuality/`（`detection` / `metrics` / `evidence` / `purification`）
+ `relations/data/maven_fact.py` + 脚本 `train_factuality_detector.py` / `evaluate_factuality.py`。
本地 **349 passed / 12 skipped**（基线 301/12）、ruff 0、`ekg-smoke` OK；4090 349 passed。

**★ 开工先核数据，三种 offset 口径并存于同一条记录**（交接文档只提示"要自己核"）：
mention `offset` 是 **token 级**（索引 `tokens[sent_id]`，91,719/91,719 精确回切）、`evidence_offset`
是 **`[sent_id, token_idx]` 对**、`arguments[].mentions[].offset` 是 **字符级**（74,008/74,008 命中）。
另实测 `document == " ".join(tokens)` 在 **3,623/3,623 篇**成立 ⇒ token→字符映射可精确计算，
直接复用 `nodes/encoding.py::encode_spans`，不引第二套坐标系。evidence offset 有官方标注噪声
（train 24/5,997、valid 6/1,296），**丢弃并计数**，不静默记成 span(0,0)。
字段名坑：MAVEN-FACT 是 `causal_relation`（**单数**），照 ERE 的复数名读会静默拿到 0 条因果边。

**★ 对标口径已回一手表格核**（arXiv 2407.15352，Phase C 教训）—— 交接文档的"靶 47.6"有三处需声明：
① **47.6 = DMBERT**（Table 3），同底座可比档是 **DMRoBERTa 47.1 / RoBERTa+CLS 45.4**，GPT-4+CoT 42.8；
② **官方数字在 test 上**，test 标签不公开，**我们只能报 valid，属不同 split**；
③ evidence 的官方口径是 **CT−/PS+/PS− 三类宏平均**（Table 4：DMRoBERTa 45.4），
与"全部 mention 的 pooled span F1"是两个量，故两个都报、互不顶替。

**主结果**（valid 全量 710 篇 / 17,780 mention，roberta-base · α=0.5 · lr 2e-5 · 6ep；
**协议 = train 内 90/10 doc 级切分选 epoch，valid 只报数**）：

| 系统 | 选中 epoch | macro-F1 | accuracy |
|---|---|---|---|
| 全预测 CT+ 平凡基线 | — | .1947 | **.9487** |
| lexicon 记忆基线 | — | .2233 | .9409 |
| no-structure 消融 | dev 最佳 ep4 | .4743 | .9482 |
| **本系统（gold 图输入）** | dev 最佳 ep5 | **.4823** | .9340 |
| （同一次训练的最后 ep6，**非按协议选出**） | ep6 | .4899 | .9456 |

- 每类 P/R/F1（本系统）：CT+ .9878/.9484/**.9677**｜PS+ .3298/.7566/**.4594**｜CT− .5576/.6432/**.5973**｜
  PS− .1912/.2500/**.2167**（n=52）｜Uu .1481/.2000/**.1702**（n=20）。
- ⚠️ **dev 与 valid 的排序是反的**：dev 最佳 ep5（.5916）在 valid 上 **.4823**，而 dev 只有 .5491 的 ep6
  在 valid 上反而 **.4899**。主表按协议报 **.4823** —— 事后挑 valid 上更好的那个等于**用 valid 调参**。
  这也说明 **dev 选择在本任务上不可靠**（小类方差主导），是本阶段的方法论限制，**单次运行、
  强结论须多种子（Phase H）**。
- **accuracy 无信息量的两处实证**：① lexicon 的 accuracy（.9409）**低于**平凡基线（.9487），macro-F1 却更高；
  ② no-structure 的 accuracy（.9482）**高于**本系统（.9340），macro-F1 却更低。
- evidence：**macro(CT−/PS+/PS−) .6144**（官方 Table 4 DMRoBERTa 45.4 @test），pooled F1 .3506。
  同句候选的**召回上界 .974** 已显式命名，未触顶。
- **结构特征净贡献 +.0080**（.4823 vs .4743，两边都用各自 dev 最佳）。**方向不一致**：
  全部增益来自小类 PS−（+.106）/ Uu（+.012），而在三个较大的类上**都更差**
  （CT+ −.008 / PS+ −.043 / CT− −.028）。量级属噪声级，**不宜作为卖点**。
  这与论文 Table 6「relation+argument 同时加反而掉点」的方向一致（我们拼 8 维计数而非 768 维表示，
  所以没掉、但也没赚到）。
- ⚠️ dev macro-F1 **非单调**（.5077/.5321/.4918/.5325/.5916/.5491），故训练改为**保留 dev 最佳 epoch**
  并落 `dev_curve.json`。同种子重训前 5 个 epoch 逐点可复现（ep6 .5491 vs .5380，GPU 非确定性算子）。
- ⚠️ **no-structure 消融的 ep5/ep6 训练崩溃**（macro-F1 塌到 .1941，四个非 CT+ 类全部归零，
  label loss 0.12→0.78）。按红线**作废不采用**，取其 dev 最佳 ep4；**不得据此说"结构特征有用"**。

**鲁棒性（本章 novelty 的一半）—— 结论是几乎不掉点**：

- 把 gold 图（126,486 边）换成 **Phase A 抽取器的预测图（231,530 边，1.8 倍）**，同一检测器、
  只改这一个输入：macro-F1 **.4823 → .4824（+.00013）**，17,780 个 mention 中**仅 8 个**标签改变。
  （ep6 档同样：.4899 → .4898，9 个标签变。**两个 checkpoint 上都复现**。）
- 解读（与消融不矛盾）：结构特征用的是**粗粒度度数统计**，gold 与 predicted 图的度数分布量级相近，
  经 log1p 压缩后特征位移极小，不足以翻转 argmax；而消融是把这 8 维**整个去掉**，差异自然更大
  —— 即便如此也只有 +.008。
- 对下游是**正面**结论：构建阶段的图错误**不传染**到事实性判定。但同一批证据也说明"结构感知"是
  **弱机制**（消融 +.008 且方向不一致），**不宜作为卖点**，**不得包装成"我们的方法鲁棒"而回避这一面**。
- ⚠️ 反过来说，这个"鲁棒"**没有被压力测试过**：Phase A 预测图与 gold 图的**度数分布量级相近**
  （1.8 倍边数，log1p 后位移很小）。真正的鲁棒性主张需要**受控地劣化图**（按比例删/加边扫一条曲线），
  当前只有"一个真实预测图"这一个点，**不能由此声称对任意图错误都鲁棒**。留给 Phase E 或 H。

**净化 —— ❌ 负结果，止损触发**：

预测图上按 CT− 剔节点 / PS−·Uu 降权（本系统档，剔 443 个节点）。
**加随机剔除同样数量节点的对照后，净化在每一项一致性指标上都不如随机**：

| 指标 | 净化前 | 净化后 | 随机剔同样数量节点 |
|---|---|---|---|
| n_edges | 231,530 | 223,962 | 220,389 |
| causal_cyclic_scc | 937 | 916 | **895.6** |
| temporal_cyclic_edges | 42,980 | 41,882 | **40,122** |

（ep6 档同样：剔 519 节点 → causal SCC 909 vs 随机 888.8、temporal cyclic edges 41,568 vs 39,779、
closure_gap .3691 vs .3648。**两个 checkpoint 上都复现，不是单点噪声**。）

- 归因（可解释）：**CT− 事件是低度数节点** —— ep6 档剔 519 个只带走 18.1 边/节点，随机则是 24.9。
  所以"违反变少"完全能由**图变小**解释，没有靶向效果。
- 该结论只否定"净化能改善**结构一致性**"。剔除被断言未发生的事件在**语义上仍是对的**，
  其真实价值必须由**下游后继预测（Phase E）**判定，**不能用一致性指标背书**。
- gold 图上净化剔 520 节点 / 5,995 边；gold 图本无结构违反，净化后仍全 0。

产物：`runs/factuality_valid_struct_best.json`（**主表来源**）、`runs/factuality_valid_6ep.json`、
`runs/factuality_valid_nostruct.json`（均已取回本地）；
checkpoint 与 **预测边 dump `runs/factuality/predicted_edges_valid.jsonl`（127M，Phase E 直接复用）**
留在 4090，不进 git。

### 文献驱动的两条探路（2026-07-28，回答"中间指标改善但下游不改善"怎么办）

联网复核后按作者拍板做了两个受控实验（均在 Phase D 的预测边 dump 上，710 篇 / 231,530 边，
497 篇 held-out test / 1,260 个 gold query），**两条都是负结果，且都比原先的猜测更干净**。

**① Ch4：修复对下游的影响可以精确归因，且量级极不对称**

| 档 | R1 可达 | R1 率 | R2 f1 | R2 tp | causal SCC(修后) |
|---|---|---|---|---|---|
| raw | 899 | .7135 | .0776 | 64 | 661 |
| 完整修复（破 causal 环） | 896 | .7111 | .0785 | 65 | **0** |
| **不破 causal 环** | **899** | **.7135** | **.0776** | **64** | 661 |

- ⚠️ **第一次探路测错了对象，如实记**：原假设「掉点源于补 temporal 闭包边稀释 precision」。
  实测补/不补闭包两档 R1/R2 **逐位相同**（开关确实生效：closure_gap 27.4 vs 0、added 1 vs 0）。
  原因是构造性的 —— **下游 ECG 重建只读 causal+subevent 拓扑**（`succession/data/cgep.py`），
  与 temporal 闭包**正交**。所以那个假设根本无法被那个实验检验。
- **改测 causal 环破除后结论清晰**：修复共 **6,888 删 + 8,079 补 ≈ 1.5 万次编辑**，其中
  **约 1.4 万次（temporal 相关）对下游按构造零影响**；真正动下游的只有 causal 环破除的 **858 条边**，
  代价是 **R1 掉 3 个 query（1,260 中，0.24%）**、收益是 R2 tp +1。
  **不破 causal 环时下游与 raw 逐位相同**，但保留 661 个 causal 强连通分量。
- ⇒ **这是一个真实但极不对称的权衡**：清零 661 个 causal 环的代价是掉 0.24% 的下游可达。
  它同时给出**门控的作用点**（只有 causal 环破除值得门控）与**门控的天花板**（最多挽回 0.24%）。
- ⚠️ 另一个更根本的限制：**R2 f1 只有 .078**（precision .164 / recall .051）。在这个绝对水平上，
  任何修复策略的差异都会被淹没 —— 下游可重建性的天花板由 **Phase A 抽取器质量**决定，不由修复决定。

**② Ch3：度数匹配对照排除了唯一的替代解释，净化负结果坐实**

原均匀随机对照对净化不公平（它多删了 3,573 条边）。新增**度数匹配**对照后（`degree_gap=0.000`，
边数 223,844 vs 净化 223,962，近似等量）：

| 指标 | 净化后 | 均匀随机 | **度数匹配随机** |
|---|---|---|---|
| n_edges | 223,962 | 220,389 | 223,844 |
| causal_cyclic_scc | 916 | 895.6 | **902.6** |
| causal_cyclic_edges | 2,535 | 2,470.6 | **2,496.2** |
| temporal_cyclic_scc | 883 | 871.8 | **865.8** |
| temporal_cyclic_edges | 41,882 | 40,122 | **41,659.6** |
| temporal_closure_gap | **.3701** | .3652 | .3708 |

- **移除等量图质量的前提下，净化在 6 项中 5 项仍不如随机**（唯一略胜的是 closure_gap）。
  ⇒ 排除「只是删了低度数节点」这一解释，**坐实事实性信号对结构一致性无靶向价值**。
- 但**不能**因此说净化无用：随机删边本身是强基线（DropEdge, ICLR'20，随机删边提升 GNN，
  典型率 10–30%，我们的对照正落此区间）；且 KG pruning 文献区分「删**错误**」与「删**无价值**」——
  我们删的是错误（CT− 断言未发生），下游关心的是有用，两者不重合。

**★ 两条合起来指向同一个更深的结论**：**结构一致性指标与"哪些节点/边该被移除"之间不存在对齐**。
净化按语义正确地删了 CT− 却减不了环；修复按结构正确地破了环却换不来下游。
这个「两次错位」本身就是 Ch3+Ch4 可讲的实证内容，且**比原来的正面主张更扎实**。

### Phase E 实施（2026-07-29，4090 card 2，**三图归因完成 / 图侧干预全部噪声级**）

代码（只增不改）：`succession/graph_context.py`（三图接入点）、`succession/perturbation.py`
（4 类受控构建误差 + 1 个结构零）、`scripts/evaluate_cgep_propagation.py`（一次训练多图打分 +
`--structural-only` CPU 通道）、`scripts/report_ch4_budget.py`、`scripts/report_ch4_contrasts.py`。
配套：`cgep.topology_triples` / `reconstruction.corpus_reconstruction` /
`purification.degree_matched_samples` / `predictor.rank_instances` 提为公开单一事实源；
`SeDGPL.set_edge_selector` / `save` / `load`；`evaluate_factuality --predicted-edges` / `--dump-labels`。
本地 **373 passed / 12 skipped**（基线 352/12）、ruff 0、`ekg-smoke` OK。

**★ 接入点设计与自检**（交接 §4 的方案 3）：query / candidates / label / 节点框架全部固定来自 gold，
只替换喂给模型的 template 边。两条不变量都是**从 gold 继承**而非新发明：① 答案绝不进 prompt
（gold 查询边 tail 出度 0 入度 1，构建图无此保证，故凡触及金标后继的边一律剔除并计数）；
② 节点框架为 gold，故 `<a_i>` 词表 / 句编码 / 候选集跨三图逐位相同。
**自检：gold 进 gold 出，1908/1908 实例逐位相同** ⇒ `gold` 档就是已发表基线本身，不是重新推导。

**★ 先钉死一个会毁掉整个归因的混淆：边序**。SeDGPL 按**存储序**截断前 20 条，于是同一张图
重新序列化就能改数。实测 `repaired_nobreak` 与 `predicted` 的模板边**集** 94/94 完全相同，
存储序却只有 36/94 相同。全量 1908 上的后果（`--template-order source` 档）：

| 对照（source 序） | Δ MRR | 95% CI | p |
|---|---|---|---|
| repaired − repaired_nobreak | **+0.0048** | [+0.0007, +0.0089] | **0.020** |
| repaired_nobreak − predicted（**边集完全相同**） | −0.0022 | [−0.0064, +0.0018] | 0.274 |

⇒ 纯重新序列化就能造出一个 p=0.02 的"效应"。改 canonical 序后 `repaired_nobreak` 与 `predicted`
**逐位相同**（Phase B「不破 causal 环则下游不动」的预测被确认），修复的表观收益从 +0.0026 回落到
+0.0011。**主表一律用 canonical 序**；source 序只用于锚定已发表基线。

**主结果**（valid 全量 710 篇 / **1908 实例**，一次 SeDGPL 训练 10ep 7912s，25 档 × 2 selector 打分；
`n_unscorable=1`，与 2026-07-11 基线一致）：

| 档 | MRR | Δ vs gold | R1 可达率 | 模板边/实例 |
|---|---|---|---|---|
| **gold** | **.1802** | — | 1.0000 | 15.9 |
| **predicted** | **.1583** | **−.0218** | .7018 | 24.0 |
| **repaired** | **.1595** | −.0207 | .7002 | 23.2 |
| repaired_noclose（不补闭包） | .1595 | −.0207 | .7002 | 23.2 |
| repaired_nobreak（不破 causal 环） | .1583 | −.0218 | .7018 | 24.0 |
| random_drop_matched（等量随机删 1,209 causal 边） | .1584 | −.0218 | .6824 | 23.2 |

**归因（配对 bootstrap，10,000 次重采样；同一模型答同一批 1908 题，故成对）**：

| 对照 | Δ MRR | 95% CI | p | 占构建损失 |
|---|---|---|---|---|
| gold − predicted（**构建损失**） | **+0.0218** | [+0.0109, +0.0327] | **0.000** | 100% |
| repaired − predicted | +0.0011 | [−0.0017, +0.0041] | 0.456 | +5.1% |
| repaired_nobreak − predicted | **+0.0000** | [0, 0] | — | 0%（逐位相同） |
| repaired_noclose − predicted | +0.0011 | 同 repaired | 0.456 | +5.1% |
| repaired − random_drop_matched（**强对照**） | +0.0011 | [−0.0028, +0.0051] | 0.595 | — |
| random_drop_matched − predicted | +0.0000 | [−0.0029, +0.0029] | 0.987 | +0.2% |

- **构建损失是唯一确凿的效应**：−0.0218 MRR（相对 −12.1%），CI 远离 0。
- **修复的全部效果 = causal 破环**：补闭包与其余 temporal 动作**按构造零影响**（`repaired_nobreak`
  与 `predicted` 逐位相同）。破环值 **+0.0011 = 构建损失的 5.1%**，且**与 0 不可分**（p=0.46），
  与等量随机删边**也不可分**（p=0.60）。⇒ 交接文档估的「门控天花板 ≈0.24%」量级正确，
  这里给出了 MRR 上的版本。
- **结构侧修复对上强对照是赢的**（`runs/cgep/ch4_structural.json`）：同样删 1,209 条 causal 边，
  修复把 937 个 causal SCC 清零、R1 .7002 / R2 f1 .0770；随机删只清掉 55 个环、R1 .6824 / R2 .0749。
  **修复的价值不是「比不修好」，是同样代价下选得准得多——但这份准确性换不来下游。**

**净化的下游判定（Goal ②，正面回答：❌ 无增益，且是天花板）**：

| 档 | MRR | Δ vs predicted | 95% CI | p |
|---|---|---|---|---|
| purified（Phase D detector 标签，可部署档） | .1583 | −0.0001 | [−0.0007, +0.0005] | 0.922 |
| purified − 度数匹配对照 | — | +0.0006 | [−0.0020, +0.0036] | 0.655 |
| purified − 均匀随机对照 | — | +0.0005 | [−0.0024, +0.0033] | 0.752 |
| **purified_oracle（gold MAVEN-FACT 标签 = 上界）** | .1583 | **−0.0000** | [−0.0015, +0.0014] | 0.966 |
| purified_oracle − 度数匹配对照 | — | +0.0021 | [−0.0002, +0.0048] | 0.076 |
| purified_oracle − 均匀随机对照 | — | −0.0035 | [−0.0072, +0.0001] | 0.059 |

- **用金标事实性标签也是零**。这不是「检测器还不够好」——**oracle 档就是天花板**，
  ⇒ 没有任何检测器改进能救活这条路。Ch3 按止损口径退为「事实性检测 + 预测图鲁棒性分析」。
- 净化只**略胜**度数匹配对照、**略负于**均匀随机对照，两者 CI 均含 0。均匀对照删掉 2.5 倍的边
  （1,614 vs 639）——它更像「把过密的预测图随机稀释」，不构成对净化的公平比较，故两个都报。
- 标签来源：`evaluate_factuality --predicted-edges`（复用已有 dump）重跑，macro-F1 .4823/.4824、
  8 个标签变，**与 Phase D 逐位复现**。

**受控扰动曲线（Goal ①，在 gold 图上单变量注入，嵌套采样保证曲线量的是幅度而非抽样运气）**：

| 误差类型 | 幅度 .05 | .1 | .25 | .5 | .75 | 1.0 |
|---|---|---|---|---|---|---|
| 删边（召回损失） | — | −.0056 | −.0081 | **−.0240** | **−.0446** | **−.0991** |
| 增边（精度损失） | — | — | −.0047 | **−.0098** | — | **−.0139** |
| 并节点（共指过并） | +.0018 | +.0024 | **−.0092** | — | — | — |
| 拆节点（共指欠并） | −.0040 | **−.0088** | **−.0184** | — | — | — |
| **打乱 temporal** | — | — | — | — | — | **+.0000**（CI [0,0]） |

（粗体 = 配对 bootstrap CI 不含 0。增边的 .5/1.0 列对应 rate .5/1.0。）

- **同幅度下最伤下游的是身份错误，不是关系错误**：rate .25 时拆节点 −.0184，是等幅删边（−.0081）的
  **2.3 倍**、等幅增边（−.0047）的 **3.9 倍**。而拆节点恰恰是**一致性机器完全看不见**的那一类
  （causal SCC = 0、拓扑边数与 gold **完全相同** 12,524）。
- 按**可达性损失归一**后更清楚（ΔMRR / ΔR1）：拆节点 −.0777、真实预测图 −.0731、并节点 −.0400、
  随机删边 −.0305。⇒ **可达性损失单独解释不了伤害**，精度损失与身份损失叠加在其上。
- **打乱 temporal 是结构零**：与 gold **逐位相同**（模板只读 causal+subevent）。这条从 Phase B
  的断言升级为可跑的证据。
- 并节点在低幅度（.05/.1）**略升**（+.0018/+.0024，CI 含 0）——不作正面主张。

**★ 核心论断已量化：一致性指标与可重建性不对齐**（25 个受控档位，`ch4_structural.json`）：
causal_scc vs R1 的 Spearman ρ = **−0.064**，temporal_closure_gap vs R1 ρ = −0.163，
拓扑边数 vs R1 ρ = −0.008；而 **R1 与 R2 之间 ρ = +0.783**（两个可重建视角彼此一致）。
两个干净反例：`split_nodes@0.25` 三项一致性指标全说健康而 R2 从 1.0 崩到 .365；
`add_edges@1` 说有 316 个 causal 环而 R1 是满分 1.0。
（25 档是**设计集不是抽样**，ρ 只作描述用。）

**误差预算（Goal ③，`ch4_budget.json`；CS-CRP 首次吃实测可达性掩码而非合成掩码）**：

- **可行性下限**：composed coverage 不可能超过可达率，故 `predicted` 图上
  **alpha_total < 0.2935 时任何方法都不可能达标**。这是 Phase A 抽取器给整条链路定的端到端风险地板。
- gold 图（无构建损失）上，条件回收档**恰好压在目标上**（α=.1/.2/.3 → .9036/.8040/.7055），
  而固定 50/50 划分**过度覆盖**（.9444/.8920/.8543）—— 一半预算浪费在不存在的可达性损失上。
- ⚠️ **发现一条库级限制并如实并列报告**：`allocate_budget_conditional` 用 `min(CP上界, alpha_edge)`
  收紧不可达率 u，这只在损失由它所约束的**准入**阶段产生时成立。Phase E 的损失来自**抽取**，
  没有 CRC 界覆盖它，于是收紧断言了不成立的上界、recycler 反而欠覆盖
  （α=.3 目标 .70：`cs_crp_cond` .5828 ❌）。去掉收紧的同一 recycler（`cs_crp_measured`）达标 .7065 ✅。
  **合成掩码看不出这一条，吃实测掩码才暴露。**未改库语义，两档并列报。

**预算策略（selector）不是损失的来源**：distance 选边在 gold 上 +0.0009（p=0.62）、在 predicted 上
−0.0008（p=0.63），均不可分于 0；只在**纯过密**的图上显著（`add_edges@1` +0.0063，p=0.003）。
⇒ 构建损失来自**边的内容**，不是 20 条预算的截断策略。

**★ 噪声地板已被两条独立证据测定**：① 配对 bootstrap 的 95% CI 半宽 ≈ **±0.003–0.004** MRR；
② 同配置重训一次，gold 从 2026-07-11 的 **.1836** 变为本次的 **.1807**（source 序，实例集已证逐位相同），
即 **fit 间波动 −0.0029**；同一次 fit 内 canonical 与 source 序只差 **−0.0005**。
⇒ **所有图侧干预（修复 +.0011、净化 −.0000、distance 选边 +.0009）都落在噪声地板之内**，
与 M1/M2 的历史量级一致。**多种子（Phase H）之前不得对任何图侧干预作正面主张。**

产物（均在本地 `runs/cgep/` 与 4090 同名路径）：`ch4_propagation.json` + `_ranks.json`（主表 50 档）、
`ch4_structural.json`（25 档结构侧）、`ch4_purified.json`（可部署净化档）、`ch4_source.json`（锚定档）、
`ch4_budget.json`、`ch4_contrasts*.json`；权重 `ch4_sedgpl.pt`（1.5G，留 4090，`--load-model` 可复用，
实测 load 后 `predicted` 复现 .1583 逐位一致）。

### Ch4 先行模块（来自 v3，降级复用）

- **SeDGPL 自跑基线**：CGEP-MAVEN 单折 MRR 0.1836 / strict 0.1265，n=1908。
- **M1 距离选边**：MRR 0.1889 / strict 0.1304；相对匹配重跑约 +0.002，属于噪声级，留作消融。
- **M2 结构编码**：MRR 0.1852 / strict 0.1290；无可信增益，留作负结果消融。
- **M3a 选择性预测**：ACI 各风险档覆盖达到目标；同覆盖下 SeDGPL 相比 frequency 的集合缩小
  约 43%–68%。
- **M3b 受控扫描**：真实 SeDGPL 排名下，naive coverage 随 reachability loss 下跌；预算方法在预留档
  更稳。它是受控证据，不等于真实 predicted/repaired 图闭环。

## v4 阶段状态

| 阶段 | 任务 | 当前状态 | 完成门槛 |
|---|---|---|---|
| P0 | 主数据与溯源 | ✅ 主干数据完成；扩展数据部分仅 raw | 主数据 hash/manifest 可核 |
| A | Ch2 判别式关系抽取 | ✅ **达标**（causal F1 .250 / subevent .213 / temporal .338；召回 .4%→67.5%） | causal F1 ≥25（目标 30–37），subevent ≥20 |
| B | 一致性、repair trace、风险准入 | 🟡 **真实图闭环已跑通**（2026-07-28）：violation **清零** ✅，但 **ECG 可重建率无增益（R1/R2 微降）❌ → 止损触发**；α=0.2 不可达（召回上限） | violation↓ ✅、分层 FNR ✅、ECG 可重建率↑ ❌ |
| C | Ch1 规范事件节点 | 🟢 **主结果已出且基本达标**（2026-07-28，5090，6ep）：难例误合并 .767→**.116** ✅、coref 族 FNR 1.000→**.220**（P .781）✅、ECE **.0056** ✅、**MUC 79.6 vs 官方基线 81.4（−1.8）** ≈达标（B³/CEAFe/precision 均平手）；仅检测比记忆基线 +1.7 ❌ | 检测 F1、**MUC ≥81.4**、误合并率、ECE |
| C2 | Ch1 跨文档泛化 | ⬜ 未开始；ECB+ raw 已有，CLES 未取 | ECB+/CLES 对比 SECURE/MEET/DIE-EC |
| D | Ch3 事实性与净化 | 🟡 **检测达标、净化止损**（2026-07-28，4090）：valid macro-F1 **.4823**（平凡 .1947 / lexicon .2233 / 官方 DMBERT 47.6@**test**，不同 split）✅；evidence macro(3类) **.6144**（官方 45.4）✅；**预测图掉点 ±.0001**（8/17,780 标签变）—— 鲁棒但结构消融只值 +.008 且方向不一致 ⚠️；**净化不如随机剔同样节点数 ❌ 止损** | macro-F1 ✅、预测图掉点 ✅、净化下游增益 ❌（转 Phase E 判定） |
| E | Ch4 三图误差传播与归因 | 🟢 **主结果已出**（2026-07-29，4090）：三图 gold .1802 → predicted **.1583（−.0218，唯一确凿效应）** → repaired .1595；损失已归因到具体动作（**修复效果 100% 来自 causal 破环 = 损失的 5.1%，且与 0 及等量随机删边均不可分**）；4 类受控扰动曲线 + temporal 结构零（逐位相同）；**净化下游增益 = 0，oracle 标签亦然（天花板）**；端到端风险地板 **α ≥ .2935**。⚠️ **图侧干预全部落在实测噪声地板 ±.003–.004 之内** | 三图误差曲线 ✅、损失可归因 ✅（每个干预附等量强对照）、净化正面回答 ✅（无增益）、误差预算 ✅ |
| F | 端到端误差预算 | 🟡 通用传播原语已有；真实三段预算未做 | 显式前提下的界、分层 FNR、naive 对照 |
| ~~G~~ | ~~金融应用层~~ | ❌ **2026-07-27 移出**（四章无依赖；快照取回见 `ARCHIVE_INDEX.md`） | — |
| H | 多种子、消融、新颖性 | ⬜ 等 A–F 主结果 | mean±std、完整消融、投稿前新颖性扫 |
| I | 写作 | ⬜ 等主实验 | 初稿与终辩材料 |

## 下一步

1. ~~Phase A 判别式抽取器~~ ✅ 达标。~~Phase B W1–W4 代码~~ ✅。~~Phase B 真实图闭环~~ ✅ 2026-07-28 跑通
   （violation 清零，但 R1/R2 无增益 → **止损已触发**，见上文「Phase B 真实图闭环」段）。
2. **Phase C 主结果已出**（2026-07-28，方向 A，5090 训练；见上文「Phase C 实施」）。
   3ep / 6ep / Longformer / roberta-large 四档都跑了，口径也核过了。**收口三件事**：
   ① **MUC 缺口的真相是对标数字错了** —— 官方 RoBERTa-base 基线是 **81.4**（不是 86，86.1 是
   2024 SOTA 联合图模型）；我们 79.6，**差 −1.8，基本达到基线**，B³/CEAFe/precision 全平手，
   缺口只在 recall（其中约 1.6 点是 Arg 人群的结构性损失）。**停止换底座**（长上下文 −2.5、
   大容量 −2.8 都是负结果），要再往上得走**四关系联合建模**，不是更大的编码器；
   ② 检测器加训后仍只比记忆基线 +1.7 → **明确降级为打底、不作为卖点**；
   ③ `node_confidence` 的表述按操作点说：**弃权带越宽、原始置信越偏、校准才有活干**
   （band .1 档 ECE .0382→.0056；band 0 档 raw 本就 .0062）。
3. **Phase D 主结果已出**（2026-07-28，4090 card 2；见上文「Phase D 实施」）。**收口三件事**：
   ① **检测达标**：valid macro-F1 **.4823**（按协议 = dev 最佳 ep5）vs 平凡 .1947 / lexicon .2233 /
   官方 DMBERT 47.6，evidence macro(3类) **.6144** vs 官方 45.4 —— 但**官方数字在 test、我们在 valid，
   属不同 split**，写作时必须显式声明，不能简写成"超过 47.6"。
   ⚠️ **dev 与 valid 排序相反**（ep6 在 valid 上是 .4899 却 dev 更低），主表坚持按协议报 .4823，
   不事后挑 valid 上更好的那个；
   ② **鲁棒性 = 几乎不掉点**（±.0001，8/17,780 标签变，两个 checkpoint 都复现）：
   对下游是好消息（构建误差不传染），但同一批证据也说明"结构感知"是**弱机制**
   （消融仅 +.008，且增益全在 PS−/Uu，三个大类反而更差）——**不得包装成"我们的方法鲁棒"而回避这一面**；
   且该鲁棒性**未经压力测试**（只有一个真实预测图这一个点，未做受控劣化曲线）；
   ③ **净化 = 负结果**：加随机剔除对照后，净化在每项一致性指标上都不如随机剔同样数量节点
   （因 CT− 本就是低度数节点）。**结构一致性这条路已封**，价值改由 Phase E 的后继预测判定。
4. **Phase E 主结果已出**（2026-07-29，4090 card 2；见上文「Phase E 实施」）。**收口四件事**：
   ① **headline 站得住，但站的是"损失"不是"修复"**：唯一确凿的效应是构建损失本身
   （gold .1802 → predicted .1583，−.0218 / −12.1%，CI [+.0109, +.0327]）。修复只值损失的 5.1%，
   且与 0（p=.46）及等量随机删边（p=.60）**都不可分**。正文要讲的是**损失怎么来的、归到谁头上**；
   ② **净化的下游判定已终结**：可部署档 −.0001（p=.92）、**oracle 金标档 −.0000（p=.97）**。
   oracle 就是天花板 ⇒ **没有任何检测器改进能救活这条路**。Ch3 按止损口径退为
   「事实性检测 + 预测图鲁棒性分析」独立成章，**不得再把净化写成图质量方法**；
   ③ **最贵的构建错误是身份错误，不是关系错误**：同幅度（rate .25）下拆节点 −.0184 是删边的
   2.3 倍、增边的 3.9 倍，而它恰恰**一致性指标完全看不见**（causal SCC 0、拓扑边数与 gold 相同）。
   这条给 Ch1 的重要性提供了下游量化依据，也是「一致性 ↮ 可重建性」（ρ = −0.064）的最强反例；
   ④ ⚠️ **噪声地板已实测，写作时必须显式给出**：配对 bootstrap CI 半宽 ±.003–.004，
   同配置重训一次 gold 波动 −.0029。**所有图侧干预都在地板之内** —— Phase H 多种子之前
   **不得对任何图侧干预作正面主张**。
   ⚠️ **方法学红线（新增）**：三图比较**必须用 canonical 模板序**。SeDGPL 按存储序截断，
   实测纯重新序列化就能造出 p=.02 的假效应（`repaired − repaired_nobreak` source 序 +.0048 显著，
   canonical 序下两图逐位相同）。任何沿用存储序的图对比表都不可信。
5. **⭐当前队首 = Phase F（端到端误差预算）**，E 已把实测输入备齐：
   `ch4_propagation_ranks.json` 提供每题真实秩与可达性掩码，`ch4_budget.json` 已给出
   **端到端风险地板 α ≥ .2935**（`predicted` 图）与三法覆盖曲线。F 要收口的是：
   (a) 把 Ch1/Ch2/Ch3 三段的校准不确定性接成显式前提下的端到端界，与 E 的实测曲线对齐；
   (b) ⚠️ **`allocate_budget_conditional` 的 `alpha_edge` 收紧只在损失由准入阶段产生时成立**
   —— E 实测抽取损失下它欠覆盖（α=.3 目标 .70 只到 .5828），去掉收紧才达标 .7065。
   F 要决定这是改库语义还是保持两档并列；
   (c) 分层 FNR 与 naive 对照照旧。
   之后 **Phase H 多种子（13/17/42）**是所有噪声级结论转为定论的前置。
5. 多种子和进一步调 M1/M2 放到 Phase H；主闭环未通前不扩张实验面。**Phase D 是单次运行**，
   PS−(52)/Uu(20) 两类样本量决定了 macro-F1 方差大，强结论须多种子。
6. 每章开跑前照 [`EXPERIMENTS.md`](EXPERIMENTS.md) 定 baseline（新老搭配）+ 消融矩阵 + 评测档；Ch4 主表
   纳入 2025 近期方法（Semantic Relation Experts / 现代 LLM），不再用旧 Llama3/GPT-3.5。
7. 闭环控制器**已不是 headline 必需项**（2026-07-29 重定位）。**若仍要做任何门控档**：
   先定死门控信号来源（SPEC §4.5：无标签代理 or 离线诊断定位，**禁金标 MRR**），
   且只施于 causal 环破除——其余修复动作对下游按构造零影响，门控它们是空转。

## 止损与人工判断

- Phase A causal F1 <10% 且类不平衡、候选范围、编码方式均排查无果：保留受控模拟，Ch2 收缩为
  一致性/修复/风控，Ch4 收缩为受控误差传播。
- Ch3 净化无下游收益：保留事实性检测与 predicted-input 鲁棒性分析，不宣称净化有效。
  **⚠️ 2026-07-28 已部分触发**：净化在**结构一致性**上不如随机剔同样数量节点（负结果，见 Phase D 段）。
  下游那一半待 Phase E 判定；若 E 也无增益，则本条完整触发，Ch3 按上述收缩口径成章。
- ~~Ch4 repaired 不优于 predicted：退为一致性重排 + 误差传播分析，不更换指标掩盖负结果。~~
  **✅ 2026-07-28 已完整触发，2026-07-29 据此重定位 headline**（见「当前结论」与 SPEC §1）：
  实测 repaired 不优于 predicted，且门控天花板仅 0.24%。已按本条退为**误差传播与归因**，
  未更换指标、负结果全部保留在正文。**本条止损到此执行完毕，不再是"待触发"。**
- Ch4 门控只能靠金标 MRR（无可用无标签代理）：显式改定位为「离线构建期质检工具」，不声称在线自愈（SPEC §4.5）。
- 发现 CS-CRP/reachability 组合有直接先例：重新限定或更换命名，不写“首次”。
