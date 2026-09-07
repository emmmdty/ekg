# Phase R1 · 方法设计准入审计

> 更新于 **2026-09-07**（E1 补 §8、E2 补 §9）。本页只记录已实测的 R1 数字与审计结论。R1 仍是
> `preparation_partial_blocked`，没有方法获得 GPU pilot 准入。

## 1. 产物与代码身份

- 根目录：`runs/stages/R1/r1-v61-20260904/`；
- 代码提交：`277b36f94cf88c8584fe60f83470a965d4d849ef`；
- P1 绑定：r15 / `1e31a9acef39261f776f7ed4069fd73f4531e8d12b55779bfc0fbd74c67f9655`；
- `id_coverage.json`：`ca481ecf3b899cacf553f258992f6603f8fa417a97cd25ee94176e3f313bb2e6`；
- `power_analysis.json`：`0e137ae52d06c03a2bd5f1bcf0c8ed55b36e2218fdb70c6318b3cf2ee99ab3df`；
- `literature_matrix.json`：`64874f4c07a3d057240f2716f33eea018e4cf49bdebf0bf2aa5369d3bf442476`；
- `design_briefs.json`：`3dfbb8810fa041983f246d7aac1a251b0fc240583582a48fd03027228c570731`；
- `factuality_cv/factuality_cv.json`：
  `3a724cf77a2a34bb11f40d225725504b176e4d62e916c5b34c92f9d10a52c5c4`；
- `protocol/degree_requirements.json`：
  `ceeb581bc1ff2c22ea0dd94811c892d0c91a4e4bca8c3c7aedfd4c5f6f2da47e`；
- `protocol.json`：`cc80e066deb6b5ff735e15defe54ddb9c68384a626685cc516897440543575dc`；
- `status.json`：`c6ee4826e569ec0044ff5f8805be9213abc194825b31d8d83aae84004ecbee5e`
  （E2 加入 `llmere_feasibility` 块、改写 relation 门与 next_actions；E1 值 `099b7aaf…30e4`，
  再前一版 `24c2aac4…87af07`。`protocol.json` 的 artifacts 哈希集合不含 `status.json`，无身份漂移）。

代码门：489 passed / 24 expected skips，ruff 0，`ekg-smoke` OK。

## 2. 跨数据身份审计

数据源 SHA-256：

| 数据 | train | public valid |
|---|---|---|
| MAVEN-ERE | `6a5519fe…638b7` | `6faea0e4…c6153` |
| MAVEN-ARG | `a94f92c6…4761` | `e6890265…b73` |
| MAVEN-FACT | `190522b4…88bab7` | `396fcf07…cff` |

ERE↔FACT 的 doc/event/mention/parent/trigger/offset 在 train 与 public-valid 全部一致。ERE↔ARG 文档集合一致，
但事件与 mention 并不保持同一身份：

| split | ERE / ARG events | ERE / ARG mentions | ERE 缺失 mention | ARG 额外 mention | parent 不一致 | ARG 覆盖 ERE mention |
|---|---:|---:|---:|---:|---:|---:|
| train | 67,984 / 64,923 | 73,939 / 70,775 | 3,334 | 170 | 550 | .954909 |
| public valid | 16,301 / 15,556 | 17,780 / 16,996 | 822 | 38 | 147 | .953768 |

ARG 的 143 个训练 role key 已冻结；全量检查通过 76,882 / 18,040 个 entity reference 和
113,597 / 28,418 个 content span（train / public-valid），未发现未知 entity、未知 role、坏 offset 或 trigger
drift。

**裁决**：把 MAVEN-ARG event-cluster arguments 复制给 ERE mention 会同时产生静默缺失和身份泄漏，
因此该 deployable 输入线 `blocked`。合法方向只能是与 cluster gold 独立的 predicted mention-local extractor，
或放弃 argument 输入。

访问披露：本审计按 R1 合同读取了 public-valid 的 ID、trigger offset、event type 与 argument role；没有计算或
查看关系/事实性指标，也没有用这些标签选择模型或方法。

## 3. 前瞻性功效

固定 RNG `260904`，每个注入点 200 次模拟、2,000 次 document-cluster paired bootstrap，目标 power .80；
只使用 train 派生的 291-document internal-dev。模拟系统仅纠正冻结 anchor 的既有错误，不是 proposed 结果。

| 章 | anchor / 主指标 | 预设最小有意义效应 | 80% power MDE | 裁决 |
|---|---|---:|---:|---|
| Ch1 | official joint / MUC .809847 | +.010 | 纠正 5 个错误文档，Δ 中位数 +.007174，power 1.00 | **PASS** |
| Ch2 | A3.6 fallback / causal F1 .320973 | +.010 | 纠正 5 个跨句误报文档，Δ 中位数 +.002002，power 1.00 | **PASS** |
| Ch3（291-doc internal-dev） | RoBERTa+CLS / macro-F1 .545765 | +.030 | 纠正 5 个 PS−/Uu 错例，Δ 中位数 +.059213，power .99 | **UNDERPOWERED** |
| Ch3（2,913-doc 五折 OOF） | RoBERTa+CLS / macro-F1 .553995 | +.030 | 纠正 5 个 PS−/Uu 错例，Δ 中位数 +.004556，power 1.00 | **PASS** |

Ch3 的首行是合法补强前的历史裁决：在 3 个纠正错例、Δ 中位数 +.0370 时 power 仍为 0，检测门在约
+.059 才打开，因此不能在单一 internal-dev 上把 +.03 左右差异解释为胜出。预先冻结的五折 OOF 补强完成
后，第二行成为当前裁决；FactBank/UW 标签空间不同，仍只能作为单列外部有效性表。

### Ch3 五折 OOF 补强与验收

只读取 MAVEN-FACT public train 的 2,913 篇文档（69,782 CT+、2,262 PS+、1,492 CT−、285 PS−、
118 Uu），固定 seed `260904` 做五组文档级平衡。每轮以 3 组训练、下一组选择 checkpoint、剩余
1 组纯评估；五轮汇总后每篇文档恰好产生一次 out-of-fold 预测，评估组从不参与选模。

| 每个 evaluation fold | 最小 | 最大 |
|---|---:|---:|
| 文档 | 582 | 583 |
| CT+ mentions | 13,920 | 14,002 |
| PS+ mentions | 450 | 455 |
| CT− mentions | 296 | 301 |
| PS− mentions | 56 | 58 |
| Uu mentions | 23 | 25 |

4090 上的 seed 13 后台队列已完成 10/10 个训练与评估任务。验收重哈希 80 个声明产物，逐折确认
train / selection-dev / evaluation 互斥、training source 不含 evaluation 文档，五个 evaluation fold 恰好覆盖
2,913 篇、73,939 个 mention 一次；public valid / final-valid 未读取、未入折。

| baseline | 五折 selected epochs | pooled accuracy | pooled macro-F1 | CT+ | PS+ | CT− | PS− | Uu |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| RoBERTa+CLS | 7 / 5 / 4 / 8 / 5 | .949161 | **.553995** | .975305 | .552612 | .662753 | .382456 | .196850 |
| DMRoBERTa dynamic-multi | 12 / 7 / 3 / 7 / 2 | .950216 | .545603 | .976054 | .539288 | .671224 | .374150 | .167300 |

按预冻结“pooled 五类 macro-F1 最高者”规则选择 RoBERTa+CLS 为 anchor。dynamic-multi − CLS 为
−.008392，2,000 次 document-cluster paired bootstrap 的 95% CI 为 [−.022869, .006978]；两者没有统计分开，
但这不改变事前冻结的点估计 anchor 规则。

以 CLS OOF anchor、RNG `260904`、2,000 次 document bootstrap、每个注入点 200 次模拟重算 prospective
power；269 个 PS−/Uu 错例可用于预注册注入。首次达到 80% power 的点是纠正 5 个错例：Δ macro-F1
中位数 +.004556、95% CI 下界中位数 +.000647、power 1.00。MDE 小于预设最小有意义效应 +.030，故
**Ch3 pooled power PASS**。这只证明设计有检出力，不代表 proposed 方法成立，也不授权额外 seed。

可追溯身份：

- 远端产物根：`gpu-4090:/data/TJK/ekg/runs/stages/R1/r1-v61-factuality-oof-r2/`；
- 训练代码提交：`277b36f94cf88c8584fe60f83470a965d4d849ef`；
- `oof_summary.json`：`21e7e50596aa773f54037b95146c37838c68c250e579ae955b2730db6fe88165`；
- `acceptance_audit.py`：`2e6355a9d98ef1c3494081bbc8fdf6ac82a003a2a9956fd68ad674b315db87ef`；
- `acceptance.json`：`7de7177f9eb4e837c5c4eb8ff6822d103a9b0cb022065bf1d2ae34ce367e58af`；
- collector Git blob：`97cc743f710ed08a65a82109a10e5de3a80bcc0c`；CV/source SHA-256 与本页第 1 节一致。

Ch2 anchor 来自不可变 A3 failed handoff `a3-v6-20260905-r17`（protocol
`c187bf03…9359e`）：按冻结 P1 主锚规则选择四臂中 causal F1 最高的 per-family-selection 配方。
该锚有 9,490 个 causal FP、2,065 个 FN，其中 274 篇文档共 7,115 个 FP 是跨句。功效模拟对抽中的
错误文档删除全部跨句 causal FP，不改变 TP、FN、标签或候选全集；80% power MDE 小于 +.01，故 T018
通过。这只证明设计能检测预设效应，不代表新方法成立。

## 4. 文献/代码可运行性

只读取得并冻结六个官方仓库（LLMERE 由 E2 于 2026-09-07 补入）：

| 仓库 | commit | tree | 根 LICENSE |
|---|---|---|---|
| CorefPrompt | `47c60c04…3225` | `3fdc3010…b594` | 未发现 |
| MAVEN-FACT | `67544719…6847` | `e38f85c7…d184` | 未发现 |
| ModaFact | `ca8dea62…3867` | `78408509…be11` | 未发现 |
| TextEE | `567baa9b…5dd3` | `4f0fe960…7dd` | Apache-2.0 |
| OmniEvent | `ec72e727…cbac` | `35fb4c92…1a3b` | MIT |
| LLMERE | `94d4ef27…a798` | `f0fd6928…a06f` | MIT |

- Ch1：CorefPrompt 官方预处理给出一条不读 cluster gold 的 mention-local 路线：OmniEvent EAE 只收句子、
  trigger 和 offset，再用公开固定表把 20 个角色归为 participant/place。但官方 EAE checkpoint 链接在审计日
  返回 `Link does not exist`，两台 GPU 服务器均无缓存。TextEE 的 RAMS/WikiEvents 路径分别覆盖 139/65 与
  50/59 个 event-type/role，但 PAIE/TagPrime 强依赖源 ontology prompt/map，仓库又无 checkpoint；直接套
  MAVEN event type 会成为新的未经验证 adapter，不能冒充官方 baseline。RESIJ 未取得官方代码；identity
  baseline/input 门仍 `blocked`。
- Ch2（**2026-09-07 按 E2 实测修订**）：official joint 可运行。此前写的“LLMERE 未取得官方实现”不准确，
  真实情况是**官方实现只覆盖方法本体，不覆盖训练**——仓库全历史（5 个 commit）含数据构造、评测器与
  已发布预测，但**没有任何训练/推理代码、配置、依赖清单、checkpoint 或 base model 名称**。逐条证据、我们
  2622/291 manifest 上的转换实测与四条阻断点见 [§9](#9-e2--llmere-官方实现可运行性核查)。裁决
  `conditionally_runnable`：真跑出来的将是**对官方方法代码的透明适配**，与 TacoERE 同类（缺口小得多），
  因此**不关闭**“第二个独立近期同协议 runnable baseline”门。RESIJ、2025 two-stage ERE 仍未取得官方实现，
  KnowQA 作者 URL 当前不可得且是 sampled/gold-argument setting；relation baseline 门维持 `blocked`。
  TacoERE 无公开代码这一条已由自建**透明适配**档补上同协议对照，正式档、选档预注册与官方三族 F1 见
  [§8](#8-e1--ch2-tacoere-适配档的选档预注册)。
- Ch3：MAVEN-FACT 官方代码可得，但原 trainer 每 epoch 用 `test_data` 选 best、best checkpoint 保存被注释，且
  `RawBert` 调用签名不一致；本轮以透明 protocol patch 完成了泄漏隔离的 RoBERTa+CLS / DMRoBERTa 五折
  OOF。ModaFact 是意大利语 mT5-XXL 的不同任务，只作结构化对照。baseline 与 power blocker 已解除，但
  proposed 方法仍须通过 T022、T023、T024。

## 5. 当前方法裁决

- Ch1 草案改为 **predicted mention-local role posterior + missingness-aware uncertainty gate**；禁止使用
  MAVEN-ARG cluster gold。Qwen3 mention-local input 与 independent argument-aware baseline 已在后续 T020
  闭环；proposed pilot 仍等待 T023/T024。
- Ch2 草案避开已失败的 retriever/weighting 家族，改查 **full-candidate counterfactual evidence
  sufficiency/necessity**；A3 error profile 与功效门已支持该中介，但仍缺第二个独立同协议强 baseline。
- Ch3 已冻结 **typed cues + known/unknown→modality→polarity factorization + cue-conditioned residual** 因果
  brief；它不把“找准 evidence span”当主要贡献。五折 OOF baseline、pooled power 与 T022 均 PASS；T023
  跨产物审计和 T024 phase contract 未完成前不启动 proposed GPU pilot。

三者均未获 promotion；5090/4090 的空闲本身不能替代 R1 准入证据。

## 6. T022 事实性因果 design brief

T022 的 constitution/spec traceability review 为 **PASS**，但这只是设计准入，不是方法 promotion。冻结链为：

`typed cues + known/unknown→modality→polarity factorization`
→ `unknown / modality-only / polarity-only confusion`
→ `pooled five-class macro-F1`。

主结果始终是五类 macro-F1。三类 confusion、evidence、calibration、accuracy 与逐类指标只能作为中介诊断
或护栏，不能替代主结果。full、同输入同预算 flat-head remove-core、DMRoBERTa strongest-alternative 与
document-internal cue permutation negative-control 已写入 `design_briefs.json`；若 full 不改善注册中介、
cue permutation 保留同样中介改善，或主指标未胜出，机制 claim 即失败。

seed-13 pilot 仍须等待 T023 与 T024，并先通过本地门和 CPU/CUDA smoke。额外 seeds 未授权；确认性门保留
matched seeds 13/17/42、相对主锚均值至少 +.030、至少 2/3 delta 为正、document-cluster paired-bootstrap
95% CI 下界大于 0、超过 DMRoBERTa，以及 evidence/稀有类护栏。T023 仍受未完成 T020/T021 阻塞，故
R1 总状态保持 `preparation_partial_blocked`。

## 7. T020 Ch1 mention-local argument baseline/input closure

本节只记录已完成的 public-train/internal-dev baseline 闭环；不是 proposed C5 结果，也不授予额外 seed。
ModelScope `Qwen/Qwen3-8B@8188480f040c5f1606a1bb3556abf14b31975155` 在每个 MAVEN-ERE mention 的原文
上下文中抽取 participant/place。输入只允许源文本中可唯一映射的连续字符 span；`ok`、`empty`、`partial` 和
`rejected` 全部显式保留，绝不以 MAVEN-ARG event-cluster argument 或缺失值回填。

四个独立 Qwen 分片均 `rc=0`、各自 prediction SHA-256 与 metadata 一致，合并后恰有 73,939 个唯一
mention，且 ModelScope snapshot/source/manifest binding 相同。状态为 72,183 `ok`、1,123 `empty`、591
`partial`、42 `rejected`；717 个 rejected filler 均随原始响应和原因保留。merged prediction SHA-256 是
`855906d39e71d5cef838c3a72515ef837803afd6a43c88e6879274bf72e7142a`，没有 final-valid access。

在同一 2,622-train / 291-internal-dev manifest、RoBERTa-base、seed 13、10 epochs、固定 endpoint epoch 10、
threshold `.7`、band `0` 和 calibration ratio `0` 下，使用 learned predicted-argument span pooling 的 local
pair baseline 得到：

| baseline | MUC F1 | B³ F1 | CEAFe F1 | CoNLL F1 | 291-doc coverage |
|---|---:|---:|---:|---:|---:|
| Qwen3 mention-local argument pooling | .803676 | .979515 | .976166 | .919785 | 7,195 / 7,195 |

上表中的 BLANC 由组织方 `evaluate.py` 交叉核验为 89.80（报告须使用完整精度 artifact，而非本表四舍五入）。
同次 cross-check 的 MUC 为 80.37，与本地 MUC 精确一致；pairwise P/R 为 .7596/.8420，MUC P/R 为
.7708/.8394。该 baseline 低于冻结 official-joint MUC `.809847`，所以只作为可运行的 independent
argument-aware input/baseline，**不**作为性能胜出或 C5 mechanism claim。

先前 r1 在第 600 个训练文档处因一个 source-verbatim leading-whitespace filler（例如 `' Sabha'`）没有
tokenizer token 而 fail-fast；r2 只在 encoder anchor 处转向该 span 的第一个非空白 source character，保留
原始 span、状态和拒绝记录。全量 local gate 随修复通过（520 passed、24 skipped；ruff 0；CPU smoke OK）。
`report_coref_error_profile.py` 对 291 个 internal-dev gold documents 的 official-shape predictions 交叉核验
通过；小型证据已双端 SHA-256 一致，checkpoint 与完整 sidecar 保留在
`gpu-4090:/data/TJK/ekg/runs/stages/R1/r1-v61-baseline-closure-r3/ch1/qwen3-argument-s13-r2/`。

边界保持不变：Qwen adapter 不是 CorefPrompt 或 OmniEvent EAE 的官方复现；官方 EAE checkpoint 不可取得。
NuExtract 的 remote-code/generation compatibility 两轮修复后仍不能完成预测，OneKE 的 ModelScope snapshot
只完成部分下载，因此均未进入 deployable baseline。T020 的 runnable input/baseline blocker 由 Qwen artifact
关闭；C5 proposed pilot 仍必须等待 T023/T024。

## 8. E1 · Ch2 TacoERE 适配档的选档预注册

**本节在 `taco-s13-r3` 被评分之前提交**，提交本身即为预注册时间戳。产物：
`runs/stages/R1/r1-v61-20260904/baselines/relation/checkpoint_selection_rule.json`
（SHA-256 `7eca646f38dbd4e77179e05b24c92f03007ed0a52ef93b3586eb968263c59abe`）。

### 8.1 两档差异的来源：代码身份，不是 GPU 非确定性

`taco-s13-r2` 与 `taco-s13-r3` 的 `configuration`、`protocol_binding` 与 `hashes.trainer`
（`5c513bdb…d0f2c6`）**逐字节相同**，dev 曲线却不同（`best_epoch` 5 vs 7；causal by-family
`best_epoch` 5 vs 40）。差异来自服务器端的代码身份切换：

| 档 | 训练时服务器 HEAD | 含 `3f02640` | 训练窗口 |
|---|---|---|---|
| `taco-s13-r2` | `d8fcd30` | 否 | 2026-09-05 23:56 → 2026-09-06 14:18 |
| `taco-s13-r3` | `e796182` | 是 | 2026-09-06 14:27 → 21:20（`rc=0`） |

`3f02640` 改的是 `src/ekg/relations/extractor/supervised.py::cluster_sentence_ids`：把
`KMeans(n_init=10, random_state=seed)` 换成显式播种初始中心 + `n_init=1` + `algorithm="lloyd"`。
该函数的输出决定 TacoERE 把哪些句子编进同一段上下文（`cluster_pair_groups` → `pair_trigger_embeddings`），
因此**换的是编码器输入本身**。CPU 复算（脚本
`runs/stages/R1/r1-v61-20260904/baselines/relation/audit_cluster_context_divergence.py`，SHA-256
`51faffc6f6581b756a84cf0eb808fcf831ef4cbaadee4c4b70a3e9034ea024f2`；结果
`cluster_context_divergence.json`，SHA-256 `c347f6fa200666fb0fceeb5ecd5fbdab9b8b7e3a4dc96913e322ef0836d5ba39`；
sklearn 1.7.2 / numpy 2.2.6）在 `maven_ere/train.jsonl` 全部 2,913 篇上实测：

| 项 | 全量 2,913 篇 | 预注册时的 200 篇 pilot |
|---|---:|---:|
| 聚类结果改变的文档数 | **2,743**（94.2%） | 196 |
| 改变归属的句子数 / 总句子数 | **15,627 / 32,431**（48.2%） | 1,414 / 2,776 |
| 旧代码在同一进程内自相矛盾的文档数 | **5** | 1 |

结论：r2/r3 的差距是**确定性的代码致输入变化**，GPU 非确定性不是主因；且旧初始化器连同进程内自洽
都做不到，`taco-s13-r2` 在当前 HEAD 上无法复现。

### 8.2 预注册的选档规则

> **按训练代码身份选档，不看分数。** 记入正式记录的是训练期 relation 代码与冻结仓库 HEAD 一致的那一档，
> 使训练与推理重建的是同一套 TacoERE 上下文；训练代码已被取代的档保留为 superseded 产物，且不在新代码下重新评分。

据此：`taco-s13-r3` 为正式档，`taco-s13-r2` 为 superseded。**披露**：`taco-s13-r2` 的官方分数在
2026-09-06 已算出并在仓库产物中（本节写定时已知）；`taco-s13-r3` 在本节写定时**没有任何分数**。
选择只由上表的代码身份得出，与两档分数无关。

评分口径要求：`taco-s13-r3` 必须在含 `3f02640` 的提交下评分（HEAD `1f3daaa` 相对服务器 `95e37bd`
未改动 `src/`、`scripts/` 任一文件），以满足"训练与推理口径成对"。

### 8.3 可追溯性缺口（记录，不在 E1 修）

`run_metadata.protocol_binding.hashes` 只哈希 `scripts/train_supervised_relations.py`，**不含**
`src/ekg/relations/extractor/supervised.py`。这就是两档携带同一 trainer hash 却构造出不同编码器输入的原因。
把 relation extractor 模块加进哈希集合不会改动任何既有 hash，但改动 trainer 本身会打断 P1 r15 的
external evidence hash（`taco-s13` 首跑即因此 fail-fast），须单独排期。

### 8.4 正式档 `taco-s13-r3` 的官方三族 F1（2026-09-07，gpu-4090 GPU1）

评分命令（cwd `/data/TJK/ekg`，服务器 HEAD `91e818e` = 预注册提交，相对 `95e37bd` 只改 docs）：

```bash
CUDA_VISIBLE_DEVICES=1 setsid nohup .venv/bin/python -u scripts/score_a3_arm.py \
  --run-dir runs/stages/R1/r1-v61-baseline-closure-r3/ch2/taco-s13-r3 \
  --gold runs/stages/A3/a3-v6-recipe-accounting-r16/preflight/data/MAVEN_ERE/valid.jsonl \
  --candidate-digest 15a3b1a548625624642130190b39411e6346866ff8594c2af2020cfbdac10910 \
  --per-family-checkpoints > logs/r1_taco_s13_r3_score.log 2>&1 &
```

口径与 A3.6 四臂逐条相同：internal-dev 291 篇 / 7,195 mentions / 234,870 pairs / 1,719 TIMEX，候选
digest `15a3b1a5…10910`、evaluator `32919e86…59598`、gold `bb8c6b48…ce7e3`、source lock
`d0d7d848…89231`；`final_valid_accessed=false`、`device=cuda`、`confirmation_eligible=true`。

| 系统 | causal P / R / F1 | subevent P / R / F1 | temporal P / R / F1 |
|---|---:|---:|---:|
| promotion / guardrail | — / — / **>33.17** | — / — / **≥28.75** | — / — / **≥50.63** |
| **`taco-s13-r3`（正式档）** | 23.48 / 50.25 / **32.01** | 19.46 / 55.39 / **28.80** | 43.81 / 62.42 / **51.48** |
| `taco-s13-r2`（superseded） | 23.16 / 55.40 / **32.67** | 22.04 / 47.17 / **30.04** | 43.11 / 63.32 / **51.30** |
| 冻结主锚 official_joint | 34.37 / 32.05 / **33.17** | — / — / 29.75 | — / — / 51.63 |

精确值（正式档）：causal `32.00956302297782`、subevent `28.798318346373936`、
temporal `51.48427815831971`。

判定：**causal 32.01 低于主锚 33.17，未过 promotion 门**；subevent 28.80 与 temporal 51.48 只是压线
过护栏（余量 +0.05 / +0.85）。TacoERE 式聚类上下文同样没有把 Ch2 抬过主锚，与 A3 的 `failed` 结论一致。

**预注册规则选中的是三族里 causal 与 subevent 更低的那一档**（−0.66 / −1.24），这本身就是规则未被分数
驱动的证据。

⚠️ 同次评分的共指栏 MUC 0.00 / B³ 95.85 / CEAFe 94.21 / BLANC 49.69 按构造必然（本档不训练 coref 头，
`n_pred=0`），**不得作为 Ch1 数字引用**。

⚠️ **不存在单变量的 document-context 双胞胎**：`taco-s13-r3` 是 rates 1/1/1 + coref aux 0 + 逐族选模 +
taco 上下文，而 A3.6 的 `local recipe 1/1/1` 是同 rates 但 **macro 选模 + document 上下文**。两者差两个轴，
因此**不得**把差值写成"taco 上下文的增益"。

### 8.5 对 relation baseline 门的影响

TacoERE 至今没有公开代码，`taco-s13-r3` 是我们自建的**透明适配**，不是官方复现，因此它
**不关闭**"第二个独立近期同协议 runnable baseline"这道门。它的定位是：与主锚同口径的可运行同协议
对照、A4 的 error-profile 输入，以及 causal 高召回/低精度工作点的又一个证据点。官方实现方向由队列
E2（LLMERE）裁决。

本地产物：`runs/stages/R1/r1-v61-20260904/baselines/relation/taco-s13-r3/`，与
`gpu-4090:/data/TJK/ekg/runs/stages/R1/r1-v61-baseline-closure-r3/ch2/taco-s13-r3/` 双端 SHA-256 一致：

| 文件 | SHA-256 |
|---|---|
| `official_metrics.json` | `4bf12d77e864dd68b4afe419d140714d6dfa1fc7836f8ef9dea88519e31f0cfb` |
| `official_predictions.jsonl` | `d410fdeb3b3308f7b8bb682eff5a1effefb24da6d6571e31f782a3f72a1ed911` |
| `run_metadata.json` | `a611e3bfbc28a0717b79692529f31e78d05682532dfa373c9f11f0a2b9e85b57` |
| `score.log` | `b3e2c11b962bc409f00b45f8b65eb1a5422a1e85f7e82d4febc78ee28fac5a08` |
| `train.log` | `506d75141a6a046e78e69cb45bb04a797cb944f861508720b2c83945db6da30f` |
| `native_metrics.causal.json` | `f46ba392a9da5e2353e9eeaa143f357812b33de00200e8dc8747318d81e757ad` |
| `native_metrics.subevent.json` | `0bbe2f86b95ae785c2a52b5921f6c62609e28821ebd944c30f91d63123abd0f1` |
| `native_metrics.temporal.json` | `e0d45f4e7702bbc0022375607907a06e6020538fa79b8e341ab862d6058675fe` |

checkpoint 留在 4090 原地，未跨机搬运。

## 9. E2 · LLMERE 官方实现可运行性核查

**本节只做静态核查与转换实测，未训练、未推理、未访问 final-valid 指标。** 产物：
`runs/stages/R1/r1-v61-20260904/baselines/relation/llmere_feasibility/`。

| 文件 | SHA-256 |
|---|---|
| `feasibility.json` | `311f9ad8dbd3f077e5c527368c6f1350784f0b1b4774e34a97185c50001204dc` |
| `build_llmere_splits.py` | `ba928dc78dc192e54bf091b0f410a2923e1005a8f0f2539681bb5fa90709fb96` |

冻结的只读克隆：`runs/stages/R1/r1-v61-20260904/upstream/llmere`，commit
`94d4ef2781ec7e071d38ac7fd8632a8fffbda798`（2025-02-01），tree
`f0fd6928ac8bad89efa76ea47b8237fb1b8fa06f`，LICENSE MIT。
`literature_matrix.json` 是 T013 的冻结产物，**不回改**（其哈希见第 1 节）；LLMERE 的矩阵字段记在
本节与 `feasibility.json` 里。

### 9.1 仓库实际提供什么：方法本体有，训练没有

| 组件 | 官方仓库 | 我们能否忠实运行 |
|---|---|---|
| 数据构造（prompt 模板 · 文档分区 · 负采样 · rationale/多跳链构造） | ✅ `data_handle_MAVEN_ERE/` | ✅ 已在我们 2622/291 manifest 上**实跑通过**（§9.3） |
| 评测器 | ⚠️ `eval/MAVEN_ERE/`，是**自写复现**，非组织方 `evaluate.py` | ⚠️ 需另写 predictions→官方提交格式的转换 |
| 训练代码 / 推理代码 / 配置 / 依赖清单 | ❌ **全历史 5 个 commit 均无** | ❌ 只能按论文散文用 LLaMA-Factory 复搭 |
| checkpoint / base model 名称 | ❌ 仓库内不存在任何模型名 | — |
| 超参 | ✅ 论文给全 | ✅ |
| 已发布预测与分数 | ✅ `output/predict`、`output/eval` | ✅ 可作外部校准 |

论文（COLING 2025，[2025.coling-main.500](https://aclanthology.org/2025.coling-main.500/)）实现细节：
LLaMA-Factory 框架；backbone Llama2-7b-base/chat 与 Llama3-8b-base/instruct（最好是 Llama3-8b-base）；
**LoRA rank 64**（PEFT，非全参）；max seq len 2048；每篇标注事件阈值 k=30；lr 2e-4 + cosine；
MAVEN-ERE 训 **3 epoch**；**单张 NVIDIA A100 40GB**；正负样本比 temporal 4:1 / causal 1:1 /
subevent 2:3 / coref 2:3；切分（Appendix C）为官方 train 按 8:2 切 train/valid，官方 valid 当 test。

**代码与论文的三处出入**（记录，不影响裁决方向）：`convert_causal.py` 实际留 `neg = 1.5×pos`（2:3），
与论文写的 causal 1:1 不符；`convert_temporal.py` 对训练集有未写进论文的硬截断 `keep_num = 100000`；
`merge.py` 把 subevent 训练集复制两份（`expansion_ratio = 2`），论文亦未写。

### 9.2 已发布预测确实落在官方 valid 上（对齐已实测）

`output/predict/MAVEN_ERE_causal/generated_predictions.jsonl` 实有 **29,080** 条（文件末尾无换行，
`wc -l` 只报 29,079）。用其分区规则在**我们这份**官方 valid（710 篇）上重算 `doc_split_num`，
总和恰为 **29,080**，与预测条数逐条对齐。故其 test 集即官方 valid，且分区可从我们的数据复现。
其自带评测器给出 causal 36.0440 / subevent 28.2240 / temporal 54.7063 / coref mean 90.9207，
与论文 Llama3-8b-base 行（36.0 / 28.2 / 54.7 / 90.9）一致，可确认发布的就是该档。

⚠️ **这 36.04 不得与我们的冻结主锚 causal 33.17 相比**：两者差**两条轴**——文档集不同
（官方 valid 710 篇 vs 我们 internal-dev 291 篇）、评分器不同（其自写复现 vs 组织方 `evaluate.py`）。
把它写进同一张表就是[内部口径混进对外表格]那个已经犯过四次的错。

### 9.3 在我们 2622/291 manifest 上的转换实测（CPU，本地）

用 `build_llmere_splits.py` 以我们的 manifest 覆盖上游 `split_data.py` 的 8:2 随机切分
（train = 2,622 篇，valid/test = internal-dev 291 篇），随后**逐字不改**跑上游四个 converter 与
`merge.py`，全部成功：

| 子任务 | 训练正例 | 负例池 | 保留负例 | 训练样本 | internal-dev 推理样本 |
|---|---:|---:|---:|---:|---:|
| temporal | 100,080 | 48,428 | 25,020 | **100,000**（触发硬截断） | 15,709 |
| causal | 19,346 | 88,220 | 29,019 | 48,365 | 11,149 |
| subevent | 5,036 | 102,530 | 7,554 | 12,590 | 11,149 |
| coreference | 10,485 | 97,081 | 15,727 | 26,212 | 11,149 |
| **合并 joint** | — | — | — | **199,757**（subevent 计两份） | **49,156** |

split 文件 SHA-256：train `8b6c9c21…a4fe`，valid/test（同一 291 篇）`e8dc33e4…1b0d`。
转换产物约 1.7 GB，在 seed 42 下确定性可重生成，**不入库**；排训练时在 GPU 机上现生成。

结论：**数据接口完全兼容，不需要改上游一行代码。**

### 9.4 环境实测（gpu-4090，2026-09-07，只读）

4 张 RTX 4090 24GB 查时全空；`torch 2.8.0+cu128`、`transformers 4.53.3`、`peft`/`trl`/`accelerate`/
`bitsandbytes` 均在；**`llamafactory` 未安装**，`deepspeed`、`vllm` 不在（vllm 是既定移除）。
`/data/TJK` 下无任何 Llama 权重，HF 缓存仅 9.6 MB。`HF_HOME=/data/.cache/huggingface` 存在但其
`token` 文件我们的账号读不到（权限不够）。`meta-llama/Meta-Llama-3-8B` 为 `gated: manual`，
未认证取 `resolve/main/config.json` 返回 **401**；`NousResearch/Meta-Llama-3-8B` 未设门，返回 200。

### 9.5 裁决与阻断点

**裁决 `conditionally_runnable`；不关闭 relation baseline 门。** 训练/推理代码整体缺失意味着即使跑出
数字，那也是**我们对官方方法代码的透明适配**，与 TacoERE 同类（只是缺的是标准 LoRA SFT，不是方法本体），
**不得写成官方复现**。排训练前须先清掉四条：

| 编号 | 阻断点 | 处理 |
|---|---|---|
| B1 | 无官方 trainer/推理代码 | 由我们按论文散文写 LLaMA-Factory LoRA SFT 配置，产物必须标注为透明适配 |
| B2 | Llama-3-8B 权重 gated，两台机均无可用 token | 需作者接受 Meta 许可并提供 token，或改用未设门镜像并记录权重 SHA-256 作为披露的替换 |
| B3 | `llamafactory` 未装，且**不得** pip 进已钉死的 cu128 `.venv` | GPU 机上单开一个 venv，单独记 hash |
| B4 | 上游评测器是自写复现 | 写 `generated_predictions.jsonl` → 官方提交格式的转换后用我们冻结的 `evaluate.py` 打分；上游 eval 代码里已有 `e{n}` → event id 映射可复用 |

成本（未实测，供作者决策）：joint 训练集 199,757 条 × 3 epoch × 最长 2048 token，论文用单张 A100-40G；
8B bf16 + LoRA r64 在 24GB 上预计**需要 gradient checkpointing**才装得下，本步未验证。推理侧 49,156 次
生成且栈里没有 vllm。合起来是 4090 整机数天级占用，**须先取得作者同意再排期**。
