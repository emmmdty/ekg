# EKG TODO / 实时状态

> 更新于 **2026-07-27**。本文件只记录 v4 的当前执行位置、已验证证据和下一步；设计定义见
> [`SPEC.md`](SPEC.md)，阶段验收见 [`phases/`](phases/README.md)，历史路线的留档索引见
> [`ARCHIVE_INDEX.md`](ARCHIVE_INDEX.md)（正文已移出仓库）。

## 当前结论

- **唯一主线**：v4 四章可信事件图谱构建（身份 → 结构 → 事实 → 传播/下游），headline 是 Ch4
  下游门控闭环修复与构建误差传播。
- **关键路径进展**：Phase A **已达标**（2026-07-24）——判别式 `supervised` 抽取器在金标节点上把 causal
  召回 0.4%→67.5%、causal F1 达 .250、subevent .213、temporal .338（`hallucinated=0`）。**当前关键路径转向
  Phase B**（全局一致解码 + repair trace + CRC 风控准入），并用 Phase A 的 predicted 图做真实图闭环。
- **执行状态**：P0 数据完成；**Phase A 代码完成并冒烟验证通过**（判别式 supervised 抽取器 + 训练脚本 +
  评测接线，CPU 测试全绿），全量训练进行中、**真实 F1 未出**。Phase B–E 的真实图实验依赖 A。
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

**下一步应查口径，不是查模型**（照本项目已有教训：ESC 切分泄漏、闭包 no-op 都是口径问题）。
最具体的一条可疑点：**我们的 coref 评测跑在 MAVEN-Arg 的 mention population 上（16,996），
而对标的 ~86.1 是 MAVEN-ERE 的 population（17,780，多 4.3%）**。predicted 与 gold 在我们这边
是自洽的，但**和公开数字不是同一个人群**。把规范化改跑在 ERE mention 上复评一次即可判定，
**只需推理、不需再训练**。

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
| C | Ch1 规范事件节点 | 🟡 **主结果已出**（2026-07-28，5090，6ep 最优点）：难例误合并 .767→**.116** ✅、coref 族 FNR 1.000→**.220**（P .781）✅、CoNLL **.919** ✅、ECE **.0056** ✅；但 **MUC .806 仍未到 ~86** ❌、检测仅比记忆基线 +1.7 ❌ | 检测 F1、CoNLL、误合并率、ECE |
| C2 | Ch1 跨文档泛化 | ⬜ 未开始；ECB+ raw 已有，CLES 未取 | ECB+/CLES 对比 SECURE/MEET/DIE-EC |
| D | Ch3 事实性与净化 | ⬜ 未开始；MAVEN-FACT train/valid 已就位 | macro-F1、预测图掉点、净化下游增益 |
| E | Ch4 闭环与三图传播 | 🟡 SeDGPL/受控扫描已有；闭环控制器未做 | repaired > predicted，三图误差曲线 |
| F | 端到端误差预算 | 🟡 通用传播原语已有；真实三段预算未做 | 显式前提下的界、分层 FNR、naive 对照 |
| ~~G~~ | ~~金融应用层~~ | ❌ **2026-07-27 移出**（四章无依赖；快照取回见 `ARCHIVE_INDEX.md`） | — |
| H | 多种子、消融、新颖性 | ⬜ 等 A–F 主结果 | mean±std、完整消融、投稿前新颖性扫 |
| I | 写作 | ⬜ 等主实验 | 初稿与终辩材料 |

## 下一步

1. ~~Phase A 判别式抽取器~~ ✅ 达标。~~Phase B W1–W4 代码~~ ✅。~~Phase B 真实图闭环~~ ✅ 2026-07-28 跑通
   （violation 清零，但 R1/R2 无增益 → **止损已触发**，见上文「Phase B 真实图闭环」段）。
2. **Phase C 主结果已出**（2026-07-28，方向 A，5090 训练；见上文「Phase C 实施」）。
   3ep / 6ep / Longformer / roberta-large 四档都跑了。**收口三件事**：① MUC .806 vs ~86 的缺口
   **不是底座问题** —— 长上下文 −2.5、大容量 −2.8，两次换底座都是负结果，**停止换底座**；
   下一步查**评测口径**（最可疑：我们跑在 MAVEN-Arg 的 16,996 个 mention 上，公开数字是
   MAVEN-ERE 的 17,780 个，不是同一人群），只需推理不需训练；
   ② 检测器加训后仍只比记忆基线 +1.7 → **明确降级为打底、不作为卖点**；
   ③ `node_confidence` 的表述按操作点说：**弃权带越宽、原始置信越偏、校准才有活干**
   （band .1 档 ECE .0382→.0056；band 0 档 raw 本就 .0062）。
3. C 之后进 D（Ch3 事实性）；E（Ch4 闭环 headline）依赖 A·B·C·D 齐。
   ⚠️ **做 E 前必须先重定位 Ch4 headline**：Phase B 已证明「修复提升下游可重建性」在真实图上不成立
   （见 `PHASE_C_HANDOFF.md` §7），不得在 E 里换指标掩盖该负结果。
4. 多种子和进一步调 M1/M2 放到 Phase H；主闭环未通前不扩张实验面。
5. 每章开跑前照 [`EXPERIMENTS.md`](EXPERIMENTS.md) 定 baseline（新老搭配）+ 消融矩阵 + 评测档；Ch4 主表
   纳入 2025 近期方法（Semantic Relation Experts / 现代 LLM），不再用旧 Llama3/GPT-3.5。
6. 实现 Ch4 闭环控制器前，**先定死门控信号来源**（SPEC §4.5：无标签代理 or 离线诊断定位），别默认用金标 MRR。

## 止损与人工判断

- Phase A causal F1 <10% 且类不平衡、候选范围、编码方式均排查无果：保留受控模拟，Ch2 收缩为
  一致性/修复/风控，Ch4 收缩为受控误差传播。
- Ch3 净化无下游收益：保留事实性检测与 predicted-input 鲁棒性分析，不宣称净化有效。
- Ch4 repaired 不优于 predicted：退为一致性重排 + 误差传播分析，不更换指标掩盖负结果。
- Ch4 门控只能靠金标 MRR（无可用无标签代理）：显式改定位为「离线构建期质检工具」，不声称在线自愈（SPEC §4.5）。
- 发现 CS-CRP/reachability 组合有直接先例：重新限定或更换命名，不写“首次”。
