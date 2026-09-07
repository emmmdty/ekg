# Phase R1 · 方法设计准入审计

> 更新于 **2026-09-07**（E1 补 §8、E2 补 §9、E3 补 §12，作者裁决补 §13，E4 补 §14，作者裁决补 §15）。本页只记录已实测的 R1 数字与审计结论。R1 仍是
> `preparation_partial_blocked`，没有方法获得 GPU pilot 准入。

## 1. 产物与代码身份

- 根目录：`runs/stages/R1/r1-v61-20260904/`；
- 代码提交：`277b36f94cf88c8584fe60f83470a965d4d849ef`；
- P1 绑定：r15 / `1e31a9acef39261f776f7ed4069fd73f4531e8d12b55779bfc0fbd74c67f9655`；
- `id_coverage.json`：`ca481ecf3b899cacf553f258992f6603f8fa417a97cd25ee94176e3f313bb2e6`；
- `power_analysis.json`：`0e137ae52d06c03a2bd5f1bcf0c8ed55b36e2218fdb70c6318b3cf2ee99ab3df`；
- `literature_matrix.json`：`64874f4c07a3d057240f2716f33eea018e4cf49bdebf0bf2aa5369d3bf442476`
  ⚠️ **磁盘上的文件已不是这个值**（实为 `b874d34c…6171`），见 [§11](#11-审计发现两个-r1-产物的哈希已漂移且内容自相矛盾2026-09-07-记录未修)；
- `design_briefs.json`：`3dfbb8810fa041983f246d7aac1a251b0fc240583582a48fd03027228c570731`
  ⚠️ **已多次改变**：先在 2026-09-06 未同步地漂移到 `d5d6a61c…7986`（见 [§11](#11-审计发现两个-r1-产物的哈希已漂移且内容自相矛盾2026-09-07-记录未修)，
  原字节已存档为 `audit/design_briefs.drift-20260906T1527.json`），再由 E3 写入 T021 关系 brief 后成为
  `f421436d…9f6c`，再由 §13 的作者裁决修订 roster 与 promotion 后成为
  `81ad43a3…a382`，再由 E4 写入 T020 身份 brief 后成为 `cd40e664…4366`，
  再由 §15 的作者裁决修订 identity 的 roster / promotion / open_finding 后成为
  `2220b86cac83939c36d16b502f063111ac48af9ab0981d4a3dc6994a3fa11999`
  （见 [§12](#12-e3--t021-ch2-关系因果-design-brief2026-09-07)、[§13](#13-relation-baseline-门的重新界定作者裁决2026-09-07)、
  [§14](#14-e4--t020-ch1-身份因果-design-brief2026-09-07)、
  [§15](#15-identity-baseline-门的重新界定与-ipm-口径核实排期作者裁决2026-09-07)）。
  identity brief 的因果链、中介、三臂、负控、护栏、power 绑定与 stop **未被修订**，原 roster / promotion /
  open_finding 逐字保留在 `amendments[0]`，修订发生在任何 C5 数字存在之前；
  `protocol.json` **未**随之重冻结，漂移裁决仍归 E5；
- `factuality_cv/factuality_cv.json`：
  `3a724cf77a2a34bb11f40d225725504b176e4d62e916c5b34c92f9d10a52c5c4`；
- `protocol/degree_requirements.json`：
  `f47eb6a3022c7787fb54f2289878d55e6453c462f1333047f12ececbc7207ac8`
  （**2026-09-07 因作者纠正学校前提而重冻结**，v1 值 `ceeb581b…a47e` 作废，见 [§10](#10-学位标准前提纠正2026-09-07)）；
- `protocol.json`：`fed98d2a20e281d1d037eaf46e523e17fb9a24358a0c98e3b6f456a170f619fc`
  （随上一条重算；旧值 `cc80e066…75dc`。R1 的 protocol.json 没有被 A3/P1 或任何下游产物引用，
  重冻结不影响其他信任根）；
- `status.json`：`196339e92e3616e49edd42682714cc60aa233da79ed0e7027ba7c600b2a50bf9`
  （§15 加入 `identity_baseline_gate_decision` 与 `ipm_2024_protocol_verification` 并重写
  `blocking_gates.identity`，前值 `bd7e87f3…fa6a`；再往前 E4 加入 `identity_design_brief`、把 T020 移入
  `completed_tasks` / `accepted_not_promoted`、清空 `drafted_not_promoted`，E4 前值 `0dcd7d98…6f42`；
  再往前 §13 加入 `relation_baseline_gate_decision` 并重写 `blocking_gates.relation`，前值 `6f26538e…623c`；
  再往前 E3 加入 `relation_design_brief` 并把 T021 移入 `completed_tasks` / `accepted_not_promoted`，
  E3 前值 `904cb5fc…ce37d`；再往前：由 E2 加入 `llmere_feasibility`（`c6ee4826…ee5e`），由 §10/§11 加入
  `degree_requirements_correction` 与 `known_inconsistencies`；E1 值 `099b7aaf…30e4`，
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

## 10. 学位标准前提纠正（2026-09-07）

R1.1 / T012 在 2026-09-04 冻结的 `degree_requirements.json` v1 把**四份同济大学文件**当作适用的学位授予
标准。**作者本人不在同济**，因此整套行政来源指向了错误的机构，必须作废——这不是措辞问题，是前提错误。

作者当日给出的替代口径：**按国内顶级 985（清华、北大、复旦、上交、浙大、中科大等）的毕业要求做项目
约束，且不得借此降级项目。** 据此把 v1 的四条同济来源整体删除，重新只读取得并哈希三份可核实文件：

| 来源 | URL | 发布 | 取得 | SHA-256 |
|---|---|---|---|---|
| 中华人民共和国学位法 | `gov.cn/.../content_6947841.htm` | 2024-04-26 | 2026-09-07 | `7facb7c0…2c59` |
| 清华大学学位授予工作实施办法 | `tsinghua.edu.cn/info/1236/124249.htm` | 2026-02-05（2025-12-10 审议通过） | 2026-09-07 | `31985e84…970b` |
| 北京大学学位授予工作实施办法 | `dean.pku.edu.cn/web/rules_info.php?id=59` | 未标注 | 2026-09-07 | `15738c38…5af1` |

**实读结论（不是转述）**：学位法第二十条（硕士）只要求“掌握坚实的基础理论和系统的专门知识”与
“具有从事学术研究工作的能力”，**并不要求创新性成果**；第二十一条（博士）才追加“在学术研究领域做出
创新性成果”；第二十二条把**各学科的具体标准**下放给学位授予单位。清华实施办法第十一至十三条逐条
复刻该三条，并由第十四条把具体标准交给学位评定分委员会；北大实施办法第七、十条同样把具体标准交给
学位分会。

因此这一层的顶级 985 校级规则**是统一而笼统的：没有任何一家在校级文件里写论文数或期刊会议清单**。
真正卡人的学术门槛在下一层——作者所在单位的学科分委员会标准，而**作者所在单位当前未知**。结论是：
**没有任何行政文件能提供本项目的质量底线，也没有任何行政文件可以被用来降低它。**

`personal_fields` 现在显式包含 `institution: null`，与 `degree_type`、`admission_year`、`discipline`、
`program` 一样保持未知，不猜。顶级 985 只作为**雄心的地板**：行政最低线与顶级 985 的学科惯例冲突时，
项目取更严的一侧。章节结构（三个方法章 + 一个系统评估章）与逐章门槛**不因机制失败、对手强或行政线更低
而下调**。

身份变更：`degree_requirements.json` v1 `ceeb581b…a47e` → v2 `f47eb6a3…7ac8`（`schema_version`
`ekg.r1_degree_requirements.v2`，新增 `institution`、`correction`、`reference_bar` 三块，v1 哈希与被删来源
都记在 `correction` 里）；R1 `protocol.json` 随之 `cc80e066…75dc` → `fed98d2a…19fc`。
R1 的 `protocol.json` 不被 A3 handoff、P1 r15 或任何下游产物引用，重冻结不影响其他信任根。

## 11. 审计发现：两个 R1 产物的哈希已漂移且内容自相矛盾（2026-09-07 记录，未修）

在为 §10 重冻结 `protocol.json` 时按 artifacts 表逐个重算哈希，发现**两个我本轮没有触碰的产物**与冻结
记录不符。两者的 mtime 都是 **2026-09-06 15:27**，早于本会话，说明是上一个会话改了文件却没有同步
`protocol.json`、`status.json` 与本页。

| 产物 | `protocol.json` 记录 | 实际 | 结论 |
|---|---|---|---|
| `design_briefs.json` | `3dfbb881…0731` | `d5d6a61c…7986` | **漂移** |
| `literature_matrix.json` | `64874f4c…2476` | `b874d34c…6171` | **漂移** |
| `degree_requirements.json` | `f47eb6a3…7ac8` | 同 | 一致（§10 本轮重冻结） |
| `factuality_cv/factuality_cv.json` | `3a724cf7…52c4` | 同 | 一致 |
| `id_coverage.json` | `ca481ecf…bb2e` | 同 | 一致 |
| `power_analysis.json` | `0e137ae5…3df3` | 同 | 一致 |

漂移后的内容与本页、`status.json` 三处冲突，其中一处是**文件内部自相矛盾**：

1. `literature_matrix.json` 的 `chapters.relation.baseline_gate` 与 `chapters.identity.baseline_gate` 现在都是
   **`pass`**，理由是透明 TacoERE 适配与 Qwen mention-local baseline 已闭合协议；但**同一个文件**的
   `global_decision` 仍写着 “R1 literature gate remains blocked for identity and relation”。
2. 该 `pass` 与本页 §4、§5 和 `status.json` 的 `blocked` 相反，也与 E1 在 [§8.5](#85-对-relation-baseline-门的影响)
   预注册的判断相反——**透明适配不是官方复现，不关闭该门**。
3. `design_briefs.json` 现在把 identity / relation / factuality **三份 brief 全部**标成
   `accepted_pending_t023_t024`；但 `status.json` 仍把 T020/T021 列在 `drafted_not_promoted`，
   E.2 队列里 E3（T021）与 E4（T020）也仍是 `todo`。

**本轮不修**：我无法核实 09-06 那次改动的意图与授权，而按文档层级，裁决以本页与 `status.json` 为准
（`docs/results/` 是运行事实的唯一权威）。据此，relation 与 identity 门**仍是 `blocked`**，
E3/E4 仍需按队列执行。哈希与语义的对账是 E5（T023 跨产物一致性审计）的份内事，本节即为它的输入证据；
E5 必须查明 09-06 改动的来源，再决定是重冻结 `protocol.json` 还是回退这两个文件——**不得先改哈希
让审计变绿**。

### 11.1 E3 写入前的取证存档（2026-09-07）

E3 必须写 `design_briefs.json`（T021 关系 brief 的法定位置），而该文件正处于争议状态。为了不让 E5 失去证据，
写入前先把漂移版本**原样**存档（`cp -p` 保留 mtime）：

| 项 | 值 |
|---|---|
| 存档路径 | `runs/stages/R1/r1-v61-20260904/audit/design_briefs.drift-20260906T1527.json` |
| SHA-256 | `d5d6a61c4bfdda38ab2a835814d695da6d7e8eb4d95025bb45f664509b037986` |
| 原 mtime | 2026-09-06 15:27:24.592885782 +0800 |

`runs/` 在 `.gitignore` 里，**该文件从未进过 git**，所以没有可回溯的提交历史；冻结版本 `3dfbb881…0731`
的字节在本地已不存在（全仓 `find` 只有一份 `design_briefs.json`）。这是 E5 追溯 09-06 改动时能拿到的
全部本地证据，剩下的线索只有 4090 上是否留有副本。

E3 只重写了 `briefs.relation` 一个子树，`briefs.factuality`、`briefs.identity` 与三个顶层字段
**逐字节未动**（已用 JSON 对比确认）。因此 identity brief 上那条 09-06 未授权的 `accepted_pending_t023_t024`
仍原样留给 E4/E5；relation 那一条则被本轮正式的 T021 审查取代。`protocol.json` 仍**未**重冻结——
E5 的规则不变：先查明 09-06 来源，再决定重冻结还是回退，不得先改哈希让审计变绿。

## 12. E3 · T021 Ch2 关系因果 design brief（2026-09-07）

**本节只做设计准入，不训练、不访问 final-valid。** 产物是 `design_briefs.json` 的 `briefs.relation` 子树
（写入后全文件 SHA-256 `f421436ded8c5bb33f2c5bcfb8c586f75154eca9b6dc701a4f8a1142a3f49f6c`）。

冻结的因果链是：

`pair-specific counterfactual evidence sufficiency + necessity`
→ `跨句 causal 误报数（注册中介）`
→ `官方 causal 正类 micro-F1`。

- **可干预原因**：pair 分类器读整篇文档却不必指出「哪段文本让这条关系成立」，跨句对可以只靠共现被判正；
  目标函数里没有任何东西区分「拿掉自己声称的证据后仍然成立」与「拿掉就不成立」的预测。
- **treatment**：每个 pair 选一段 claimed rationale，再做两次对照前向——移除该证据、以及等长的非证据替换；
  充分性与必要性共同监督 pair 置信度。**证据只改表示与置信度，绝不删候选。**
- **三臂**：full ｜ remove-core（同编码器/输入/预算/参数量，关掉证据选择与两次反事实前向）｜
  strongest-alternative（`taco-s13-r3` 的 K=3 cluster-conditioned context，同口径）。
- **负控**：把选中的 rationale 换成选择器没选中的等长句子，前向次数、序列长度、参数量不变。
  **负控必须抹掉 full−remove-core 的中介改善**；抹不掉就说明收益来自多一次前向或正则化，
  即使 causal F1 上升也判机制失败。
- **中介检验**：同一 291 篇 / 7,195 mention / 234,870 pair 候选全集上，用 2,000 次 document-cluster
  paired bootstrap（RNG `260904`，与 power 审计同配置）比较跨句 causal 误报数。功效审计注入的正是这条中介
  （见 [§3](#3-前瞻性功效)：锚 .320973、9,490 FP / 2,065 FN、其中 274 篇共 7,115 个跨句 FP、
  最小有意义效应 +.010、5 篇纠正即达 power 1.00）。

护栏（全部预注册）：推理枚举完整候选全集，任何检索/分区/聚类/弃答都不得删候选；causal recall 不得低于
冻结主锚自身的 **32.05**，且 P/R/F1 必须同时报告，防止把纯精度移动写成机制胜出；subevent ≥ 28.75、
temporal ≥ 50.63；训练与推理在 TIMEX 等每条轴上成对；superseded 的 `taco-s13-r2` 分数与 final-valid
一律不进选择。

### 12.1 四条已被占的一般命题与 A4 的窄 delta

| 工作 | 一般命题（已被占） | 其范围 | A4 的 delta |
|---|---|---|---|
| TacoERE（LREC-COLING 2024） | 按事件聚类重构上下文能提升 ERE | 改「编码器读什么」，不改「模型要为什么负责」；无公开代码 | A4 不动上下文与候选全集，只干预逐对证据归因；同口径实测 cluster context 只有 causal **32.01**，低于主锚，故它是对照臂不是机制 |
| LLMERE（COLING 2025） | 把文档级 ERE 变成事件分区上的生成式指令微调（模板 + 负采样 + rationale/多跳链）胜过判别式 | 范式与规模：Llama-3-8B + LoRA r64 + 2048 token + 每区 k=30 事件；其 causal 36.04 落在官方 valid 710 篇 + 自写评测器 | A4 保持冻结 RoBERTa-base 判别式与完整候选全集；贡献是反事实证据目标，不是更大 backbone。**LLMERE 的 rationale 是生成产物、从不被反事实检验；A4 的证据主张被自己的移除前向证伪** |
| CovEReD（Findings of EMNLP 2024） | 文档级 RE 依赖实体与外部知识的伪信号；用实体替换生成反事实数据可暴露并修复不一致 | Re-DocRED 的实体关系，反事实作用在**实体表面形式**，产出是 Re-DocRED-CF 数据集 | A4 在冻结的 MAVEN-ERE 语料内扰动**单个 pair 的证据集合**，不造数据集、不替换实体，主指标是官方 causal micro-F1 而非一致性率。共享的只有「反事实扰动能暴露无支撑抽取」这一句，被扰动对象、任务与结果指标三者都不同 |
| SURE-RAG（arXiv 2605.03534） | 相关 ≠ 充分；把逐 passage 的 claim-evidence 关系聚合成集合级 coverage / relation strength / uncertainty / retrieval 特征，给出 support/refute/insufficient 与选择性弃答 | 选择性 RAG 问答（HotpotQA-RAG、HaluBench），**弃答就是交付物** | 冻结 ERE 协议下弃答不能是交付物：每个候选必须给判定，过滤即静默裁剪评测全集、违反 RS-002 场景 1。A4 把充分性降为对全部 234,870 对的置信度整形，弃答风险只作诊断；并且**多一条必要性**——SURE-RAG 给手上的证据打分，A4 打的是「把证据拿走会怎样」 |

窄 delta 是**交集**而不是任一部件：*逐候选对的反事实证据充分性与必要性目标 · 在冻结的完整候选全集事件关系
协议内 · 以跨句误报率作预注册中介 · 且明令弃答不得裁剪候选*。**不写「首次」**。

### 12.2 审查结论与仍然打开的问题

审查结论 **PASS（仅设计轴）**，逐条对照：R1.5 十二个必填字段齐全；FR-005 机制可证伪（remove-core 是核心
消融、非证据替换是负控，各只差一个注册变量）；FR-006 名单内 baseline 同 manifest / 候选 / 输入假设 / 评测器，
LLMERE 的 36.04 明确只作 context（差文档集与评分器两条轴）；FR-011 A4 是实质不同的干预而非失败家族改名；
FR-012 公开实现能用则用、fidelity 缺口写明；RS-002 场景 1 落成硬护栏；QR-003 三族护栏 + recall 下界；
QR-007 中介改善而主指标不胜出时保留为负结果、不促章。

⚠️ **仍打开、且需要作者决定**：QR-001 要「主锚 + 另一个强的不同方法族」。`taco-s13-r3` 字面满足，但它
**低于主锚**（32.01 < 33.17）且是我们自己的透明适配，赢它由赢主锚蕴含，几乎不构成对抗压力。T024 冻结 A4
契约前必须二选一：

- **(a)** 接受「主锚 + 透明适配」，并在每张表里披露 fidelity 缺口；
- **(b)** 排 LLMERE 适配：先清 [§9.5](#95-裁决与阻断点) 的 B1–B4，代价是 4090 整机数天级占用 + 一个
  Meta 许可决定。

**该问题已于同日由作者裁决为 (b) 的缩小并行版本，见 [§13](#13-relation-baseline-门的重新界定作者裁决2026-09-07)**；
brief 的 roster 与 promotion 已按裁决修订（`amendments[0]` 保留被取代的原文，修订发生在任何 A4 数字存在之前）。
本节没有启动任何 GPU 任务：E3 全程是文档与静态核查。

## 13. relation baseline 门的重新界定（作者裁决，2026-09-07）

### 13.1 为什么改门而不是改章

Ch2 的近期方法逐个核过：RESIJ 无公开代码、2025 two-stage（RepL4NLP）无公开代码、KnowQA 仓库审计日 404
且是 sampled + gold-argument 设定、TacoERE 无公开代码、LLMERE 有方法本体但**全历史 5 个 commit 无 trainer**
（[§9.1](#91-仓库实际提供什么方法本体有训练没有)）。**没有任何一个近期 MAVEN-ERE 方法发布了可跑的官方训练
代码**，只有 2022 的 official joint 有。因此「第二个**官方实现**的同协议 baseline」这道门，投入再多 GPU 也
不可能通过——这是我们自己写的运行口径出了问题，不是章的质量出了问题。

裁决：回到 SPEC `QR-001` 本身的措辞——**第二个不同方法族 · 由我们在冻结协议下跑通 · fidelity 缺口写明 ·
且不弱于冻结主锚**。`SPEC.md` 无需修订（它本来就是这么写的），改的只是我们自己更严的运行措辞。

按新措辞门**仍然打开**：`taco-s13-r3` 是不同方法族、同口径，但 causal **32.01 < 主锚 33.17**，赢它由赢主锚
蕴含，不构成对抗压力。**只接受「主锚 + 透明适配」= 拿稻草人当对手，不采纳。**

### 13.2 采纳的方案：LLMERE-causal，缩小 + 并行（队列 E8）

| 项 | 决定 |
|---|---|
| 范围 | **先只跑 causal**：训练 48,365 条、internal-dev 推理 11,149 次，约为 joint（199,757 / 49,156）的 1/4。subevent/temporal 是**我们方法的护栏**，不是 baseline 的义务；`official_single` 是 causal-only baseline 的既有先例 |
| B2 权重 | **不需要作者接受 Meta 许可**：用 E2 实测返回 200 的未设门镜像，权重 SHA-256 作为**披露的替换**记录 |
| B1 / B3 / B4 | 由我们按论文散文写 LLaMA-Factory LoRA SFT 配置（**标注透明适配**）；GPU 机上单开 venv、单独记 hash；写 `generated_predictions.jsonl` → 官方提交格式的适配器，用**我们冻结的 `evaluate.py`** 打分 |
| 配方 | LoRA r64 / lr 2e-4 / cosine / 3 epoch / max len 2048 / seed 13；converter 侧沿用上游 seed 42 的确定性转换，**逐字不改**（含 `convert_causal.py` 实际 neg = 1.5×pos 与论文 1:1 不符这一条，照实保留、不"修好"） |
| 排程 | **与文档队列并行，不排在 A4 pilot 前面**。pilot 只吃一张卡而 4090 有四张；第二 baseline 只在**确认性 promotion** 时才生效 |
| 对 T024 的影响 | A4 契约**照常冻结**：roster 里 LLMERE-causal 已被完整指名与规格化（upstream commit、converter 身份、backbone、LoRA 配置、评分口径），**只有它的数字 pending**。这不违反 T024 的"baselines 必须 exact"——主锚的数字同样先于契约存在 |

**必须披露的天花板**：LLMERE 的 k=30 事件分区使**跨分区的对按构造不可能被生成**。这些对在评分时计为漏报，
因此比较仍然公平，但天花板落在 baseline 自己身上，不是落在评测上。这条要写进它的每一次报告。

### 13.3 接受的风险与明确不做的事

**接受的风险**：若 LLMERE-causal 在我们轴上高于主锚，Ch2 的及格线就抬高，A4 可能失败。**这正是现在跑它的
理由——九月发现比写作时发现便宜。** 另外 8B LoRA 对 RoBERTa-base 存在 backbone 尺度错配；真输了，诚实的
结论是"A4 的机制必须在可比规模上证明，或移植到 LLM 设定"，那是结果不是灾难。

**明确不做**：把 LLMERE 已发布的预测转成官方格式、用我们的 `evaluate.py` 在 710 篇 official valid 上重打分。
它便宜且诱人，但 official valid 就是封存的 final-valid，会毁掉 [§2](#2-跨数据身份审计) 那句干净的
"没有计算或查看关系/事实性指标"；而其自写评测器对 causal 的定义（正类 micro、排除 TIMEX、全序对枚举）
本来就接近组织方口径，重打分的信息增量抵不上这笔账。

## 14. E4 · T020 Ch1 身份因果 design brief（2026-09-07）

**本节只做设计准入，不训练、不用 GPU、不访问 final-valid。** 产物是 `design_briefs.json` 的
`briefs.identity` 子树；写入前 `81ad43a3…a382`，写入后全文件 SHA-256
`cd40e664934fdab97a6c5668cb10dcc322da46c1b84c6fe4f39cc7e5f0ca4366`。只重写 `briefs.identity` 一个子树，
`briefs.relation`、`briefs.factuality` 与三个顶层字段**逐字节未动**（写入脚本内以 JSON 对比断言）；
`protocol.json` 仍**未**重冻结，09-06 漂移的裁决仍归 E5。

冻结的因果链是：

`mention-local 预测角色后验 + 显式缺失状态`
→ `高相似度误合并数（注册中介）`
→ `官方 MUC F1`。

- **observed error**：两个可运行系统在冻结 internal-dev 上都是**误合并主导**。`qwen3-argument-s13-r2`
  有 618 个 pairwise 错误，其中 over-merge 388（62.8%）对 under-merge 230（37.2%）；MUC 层面 143 条多余
  链接（60.9%）对 92 条缺失（39.1%）；pairwise precision .759603 明显低于 recall .842033。误合并集中在
  trigger 表面形式最无区分力的地方：388 个 over-merge 里 **251 个 trigger 相似度 ≥ .8、232 个恰好等于
  1.0、333 个跨句**。主锚同样受限于精度（MUC P 78.842975 vs R 83.246073）。
- **可干预原因**：pair 打分器只把论元 span 当池化上下文，模型内部没有「这个 span 充当哪个角色」
  「该角色判定有多确信」「这个 mention 根本没有抽到角色」这三件事的表示。于是「同 trigger + 参与者冲突」
  与「同 trigger + 参与者一致」在模型看来一样，分数被 trigger 表面形式主导；目标函数里也没有任何东西
  让决策对角色冲突**非对称**，更没有区分「未观察到冲突」与「没有角色证据」。
- **treatment**：冻结的 mention-local 抽取器给出每个 mention 的 participant/place 角色后验与**显式抽取状态**
  （ok / empty / partial / rejected）；role-alignment 残差加在既有 pair 分数上，并由该对齐的不确定性门控——
  只有当两端都带着高置信且互相冲突的角色时残差才推开这一对，任一端角色证据缺失或低置信时门关向零。
  **残差只改分数，绝不删候选，也绝不读 cluster 身份。**
- **三臂**：full ｜ remove-core（同编码器/输入/候选全集/seed/预算/参数量，把 role 残差 detach，退回论元池化
  pair 分类器）｜ strongest-alternative（`qwen3-argument-s13-r2`，同 manifest/候选/评测器）。
  remove-core **不是** `qwen3-argument-s13-r2` 的替代品，两者都要报。
- **负控**：在 event type 与文档内置换 role posterior，保持角色密度、缺失状态分布与置信度分布，
  前向次数、序列长度、参数量不变。**负控必须抹掉 full−remove-core 的中介改善**；抹不掉就说明收益来自
  多出来的残差容量或其正则效应，即使 MUC 上升也判机制失败。
- **中介检验**：在同一 291 篇 / 7,195 mention 冻结候选全集上，用 2,000 次 document-cluster paired bootstrap
  （RNG `260904`，与 power 审计同配置）比较 full 与 remove-core 的高相似度误合并数。
  ⚠️ **口径分账**：中介的基线画像取自 `qwen3-argument-s13-r2`（251 / 1,774 hard pair，hard mis-merge rate
  .141488），而 power 注入基于 **official joint anchor** 的逐文档 MUC——两者是不同产物，中介检验只做
  **同一实现在同一实例集上的内部比较**，任何时候都不把 baseline 的中介数直接从主锚数字里减。

护栏（全部预注册）：推理枚举 7,195 个 mention 上的完整 coreference 候选全集，不确定性门只改置信度，
不得丢弃/过滤/弃答任何候选对；**MUC recall 不得低于主锚自身的 83.246073**，且 MUC P/R/F1 必须同时报告，
防止把纯精度移动写成机制胜出；B³ F1 ≥ 97.04、CEAF-e F1 ≥ 96.73、BLANC F1 ≥ 88.88（主锚减 1.0 margin）；
每个 mention 必须带显式 ok/empty/partial/rejected 状态，无静默默认后验、无 MAVEN-ARG cluster gold 进入
可部署臂；gold event-level 论元与 gold identity 只作**标注为 non-deployable 的 oracle**；导出保持一个
mention 对应唯一可追溯 cluster 并通过 `metadata` 暴露校准置信度，**`EventNode` 零新增字段**
（RS-001 场景 3）。

功效绑定如实记录：`power_analysis.json#identity` 主锚 .8098471986，评价单元为 document cluster，
291 篇中 125 篇可纠正，最小有意义效应 +.010，RNG `260904`，2,000 次 bootstrap，200 次模拟。
**5 篇纠正时 power 已达 1.00，但中位效应只有 +.007174（CI 下界 +.001185），低于最小有意义效应**；
+.010 目标对应约 **8 篇**纠正（中位效应 +.011839、CI 下界 +.003613、power 1.00）。
注册的目标是**效应量**，不是"最小的能把 power 顶到 1.00 的纠正数"。

### 14.1 四条已被占的一般命题与 C5 的窄 delta

| 工作 | 一般命题（已被占） | 其范围 | C5 的 delta |
|---|---|---|---|
| **ACCI**（arXiv 2506.01488 / Sci Rep） | 跨文档事件共指过度依赖 trigger 词面；结构因果图 + 后门调整 + 反事实 trigger 扰动 + 论元增强模块可端到端去偏 | 跨文档 ECB+（25/8/10 topic，574/196/206 篇）与 GVC；gold 事件 mention；候选对**在 subtopic 内检索**（沿用其主 baseline 的 heuristic 数据构造，算法输入含 gold/clustered topics）；RoBERTa-base/large cross-encoder，lr 1e-5 + 分类头 1e-4，4×A40；消融 w/o TBM −0.6、w/o CAE −0.8 CoNLL F1；代码在 `github.com/era211/ACCI`（我们未做可运行性审计） | **已按 E.1 要求核实其论元来源：ACCI 根本不抽论元。** 它用 masking 把输入切成 trigger 子序列 `X_trg` 与上下文子序列 `X_arg = X \ X_trg`，所谓"论元语义"就是 trigger 的补集——没有角色类型、没有逐角色后验、也不存在"角色证据缺失"这个状态。C5 消费的是**显式抽取的、带角色类型的 mention-local 后验 + 四态抽取状态**，门控的是**角色对齐的不确定性**而不是 trigger 偏差。任务与协议也不同：C5 是**文档内 MAVEN-ERE + 完整冻结候选全集、无检索步骤**。其 88.4 / 85.2 CoNLL F1 **不得与我们的 MUC 同表** |
| **IP&M 2024 graph propagation**（Zhang et al., 61(5) 103811） | 用 AMR 图抽**跨句隐式论元**，把 trigger 与角色在 structure-aware encoder 里聚合，再over事件关系子图传播 + triadic contrastive loss，联合提升含 coreference 的四族关系抽取 | MAVEN-ERE 联合抽取；报 **MUC 86.1** 与 temporal 60.7 / causal 37.4 / subevent 32.9；2026-09-07 检索**未找到公开代码仓库** | **这是最贴近的抢占：「用预测论元提升 MAVEN-ERE coreference」这一般命题已被占。** delta 在论元作用的位置与被测量的对象：它把论元喂进联合文档表示并在关系图上传播，一次改动四族；C5 不动编码器输入也不动候选全集，只在既有 pair 分数上加一条**由角色不确定性与缺失门控的残差**，预注册高相似度误合并数为中介，主指标只有 MUC。⚠️ **对标轴未核实**：无公开代码，其 86.1 落在哪个 split、用哪个评测器**尚未建立**，只作 context，**不得同表比较** |
| **CorefPrompt**（EMNLP 2023） | 把预测的 participant/place 兼容性做成 prompt 辅助任务，与事件类型兼容性一起提升逐对事件共指 | TAC KBP 2015-2017，候选对**欠采样**；Longformer-large selector + RoBERTa-large prompt 模型；AVG-F over MUC/B³/CEAF-e/BLANC；论元来自 OmniEvent EAE，其 checkpoint URL 在 2026-09-04 返回 `Link does not exist` | C5 把论元信号留在 prompt 之外、编码器输入之外：它是带显式缺失状态的**校准后验**，以**非对称残差**作用，并在 MAVEN-ERE 完整候选全集与官方 scorer 上评测，而不是欠采样的 TAC KBP 对。冻结的 20→participant/place 角色归并**沿用 CorefPrompt 已发布的映射并如实署名**；正因为它依赖的 OmniEvent EAE checkpoint 不可得，我们的抽取器才是 Qwen 适配并标注为适配 |
| **HGCN-ECR**（Information Fusion 115:102769, 2025） | 用 SRL 输出搭多文档 trigger 中心事件超图，超图卷积 + 多头注意力捕获高阶语义，做跨文档共指 | 跨文档 ECR，BiLSTM-CRF SRL 前端 + 超图卷积网络（转引自 ACCI 相关工作，我们未审计其代码） | 共享的只有「抽取出的角色结构能帮事件共指」这一句。HGCN-ECR 造图并做图上推理；C5 不加任何图结构、不改编码器输入、不动候选全集，贡献是**角色对齐上的不确定性门控**，包括对"没抽到角色"的 mention 的显式处理 |

窄 delta 是**交集**而不是任一部件：*带显式缺失状态的 mention-local 预测角色后验 · 作为既有 pair 分数上的
**非对称**不确定性门控残差 · 在完整候选全集与官方 scorer 均不受触碰的冻结文档内 MAVEN-ERE 协议里 ·
以高相似度误合并数作预注册中介 · 且 gold event-level 论元被限制在标注过的 oracle 内*。**不写「首次」**。

### 14.2 审查结论与仍然打开的问题

审查结论 **PASS（仅设计轴）**，逐条对照：R1.5 十二个必填字段齐全；FR-005 机制可证伪（remove-core 只
detach 注册残差、类型内角色置换是负控，各只差一个注册变量）；FR-006 名单内两个可运行 baseline 同
manifest / mention / 候选 / 输入假设 / 评测器，ACCI 的 ECB+/GVC 分数与 IP&M 的 MUC 86.1 只作 context 并
写明差异轴；FR-011 Phase C 的 context/confusability 机制保留其失败身份，C5 是实质不同的干预而非改名；
FR-012 公开实现能用则用、fidelity 缺口写明（OmniEvent EAE checkpoint 不可得，故抽取器明确是 Qwen 适配）；
QR-003 B³/CEAF-e/BLANC 非劣护栏 + MUC recall 下界，正对"抑制合并"这类机制最容易犯的纯精度交易；
QR-007 中介改善而主指标不胜出时保留为负结果、不促章；RS-001 三条场景逐条落成护栏（同实例同评测器 ·
不读 gold identity 的预注册机制诊断 · 唯一可追溯 cluster + 校准置信度且 `EventNode` 零新增字段）。

⚠️ **仍打开、且需要作者决定：Ch1 的 QR-001 名单，与作者 2026-09-07 为 Ch2 关掉的那个洞结构完全相同。**
`qwen3-argument-s13-r2` 在完全相同的协议下是一个够格的对照臂，但 MUC **.803676 低于主锚 .809847**，
且是我们自己的透明适配，赢它由赢主锚蕴含。本轮检索没有找到可运行的替代：IP&M 2024（MUC 86.1）
**无公开代码**且口径未核实、RESIJ 始终未取得、OmniEvent EAE checkpoint 已失效。
二选一：

- **(a)** 接受「主锚 + 更弱的自建适配」，并在每张表里披露 fidelity 缺口；
- **(b)** 把 **ACCI 的 TBM/CAE 透明移植**到文档内 MAVEN-ERE 协议，作为第二个不同方法族。

**推荐 (b)**，理由是它比 Ch2 那笔账便宜得多：ACCI 有公开仓库、backbone 是 RoBERTa 量级、
**没有 gated 权重、没有许可决定、没有 8B LoRA 的多天整机占用**；而且它的方法族（trigger 偏差反事实去偏）
与我们的（角色不确定性门控）确实不同，正好把当前最强的抢占工作变成对照臂。
代价是我们要为一个跨文档方法写文档内适配层，且必须标注为透明适配而非官方复现。
**本 brief 不替作者决定**；T024 冻结 C5 契约前必须先有这个裁决。

📌 **给 E5/E6 的输入证据（不在本节裁决）**：IP&M 2024 那一篇同时报 **causal 37.4**，高于 Ch2 冻结主锚
33.17。它与 MUC 86.1 一样口径未核实（无公开代码、split/评测器未建立），因此**既不能当作 Ch2 已被超越的
证据，也不能当作可比对手**；但 T023 的跨产物审计应把"是否存在我们尚未核实口径的更强公开数字"
作为一条待办登记，而不是留在会话记忆里。

本节没有启动任何 GPU 任务：E4 全程是文档与静态核查，未训练、未访问 final-valid。

## 15. identity baseline 门的重新界定与 IP&M 口径核实排期（作者裁决，2026-09-07）

E4 把两个问题交给作者后，作者当日给出两条裁决。本节记录裁决本身与其依据；**两条都在任何 C5 数字
存在之前作出**。

### 15.1 为什么 Ch1 也改门而不是改章

Ch1 的候选逐个核过：IP&M 2024 graph propagation **无公开代码**（2026-09-07 检索未命中仓库）；
OmniEvent EAE checkpoint URL 在 2026-09-04 返回 `Link does not exist`，两台服务器均无缓存；
TextEE 无 checkpoint 且强依赖源 ontology prompt；RESIJ 始终未取得；CorefPrompt 在 TAC KBP 且正是依赖
那个失效的 EAE checkpoint。**MAVEN-ERE 文档内共指上，除主锚外没有第二个公开可跑的方法**——
与 [§13.1](#131-为什么改门而不是改章) 对 Ch2 的结论逐条同构。

E.1a 给 Ch2 加的「**且不弱于冻结主锚**」是为了挡住 `taco-s13-r3` 那种我们自造的弱变体当稻草人。
对 Ch2 坚持它有意义：LLMERE 是 2025 的生成式范式，**真有可能强过主锚**。对 Ch1 不成立：唯一有公开
仓库的近期工作 ACCI 是**跨文档 ECB+/GVC** 方法，移植到文档内 MAVEN-ERE 后 `ECB+ 88.4` 完全不保证
能过 `.809847`，**大概率低于主锚**。若维持原措辞，这次移植的期望价值接近零——跑完低于主锚，门照样
关不上，等于第二个「投入再多 GPU 也过不去」的门。

### 15.2 采纳的措辞与执行顺序

裁决：**按 Ch1 现实调整门措辞**。防稻草人的等效标准改为四条同时成立——

1. 是**独立发表工作的机制**，不是我们自造的变体或主锚的再调参；
2. 在**其原始基准上有强证据**（发表时的 SOTA 级结果）；
3. 由我们在**冻结协议**（同 manifest / mention / 候选全集 / 官方 evaluator）下跑通；
4. fidelity 缺口逐表写明，标注**透明适配**而非官方复现。

`SPEC.md` 不修订——QR-001 原文本就是 "another strong, distinct method family under one protocol"，
"strong" 修饰的是 family，不是"必须强过 anchor"；改的只是我们自己更严的运行措辞。
按新措辞 `taco-s13-r3` 式的自造弱变体仍被挡住（不满足第 1 条），而 ACCI 满足第 1、2 条。

执行顺序**倒过来**：**先做静态核查，再决定训练**。

| 步 | 动作 | 为什么在这个位置 |
|---|---|---|
| 1 | ACCI 仓库静态核查（队列 E10），复用 E2 对 LLMERE 的流程，**不训练** | E2 刚教过：**仓库有方法本体不等于有 trainer**（LLMERE 全历史 5 个 commit 无训练代码）。成本近零却直接决定这条路通不通，必须在任何 GPU 决定之前做 |
| 2 | 核查通过 → 透明移植 + 单卡 seed 13；不通过 → 记录阻断点，Ch1 名单按新措辞另议 | RoBERTa-base 量级、无 gated 权重、无许可决定，成本远低于 E8 |

**`qwen3-argument-s13-r2` 的角色同时被重新定义**：它低于主锚（.803676 < .809847）不是废数据，而是
「**朴素把预测论元池化进编码器会掉点**」的负面对照——正是 C5「论元不是加了就有用，要角色对齐 +
不确定性门控」这一立论的直接证据。它以这个角色留在名单里，**不再充当第二方法族**。

### 15.3 IP&M 2024 口径核实：判据、三种处置与排期

裁决：**排在 E6 之前**（队列 E9）。理由是 IP&M 2024 同时报 **causal 37.4**，高于 Ch2 冻结主锚 33.17，
而 E6 就要冻结 A4 契约——**先核实口径再冻结，避免用一个可能已被超越的及格线冻结整章**。

**判据用现成的**：取该文的对照表，看**它复现的 MAVEN-ERE official joint baseline 数字**，与我们自跑
官方码的数字对齐。这正是 MAQInstruct 那次用过的尺子（我们自跑官方码 causal 31.37，它报 BertERE 30.9，
两者对上 → 关系栏可用；共指栏因协议未声明且比 dev 外推值高 3 点 → 不可用）。

| 核实结果 | 处置 |
|---|---|
| 它的 baseline ≈ 我们自跑官方码 | 口径可比，86.1 / 37.4 是真差距。Ch1 论文里正面承认；A4 及格线重估后再冻结契约 |
| 它的 baseline 也高一截 | 口径不同，只进 related work，**不进对照表**，我们的主锚不动 |
| 拿不到全文 | 登记为「**未核实口径的更强公开数字**」，论文如实披露，**既不当对手，也不当我们已被超越的证据** |

获取途径：ScienceDirect 有订阅墙，先试作者主页 / ResearchGate / 机构仓库 / OpenAlex
（作者 Junchi Zhang，dblp `153/2859` 已定位）。成本是一次检索。

**为什么不能就这么放着**：这是[「内部口径混进对外表格」](#4-文献代码可运行性)那个已犯过四次的错的**镜像**。
前四次是我们把内部数字当对外数字用；这次的风险是反过来——要么把别人未核实口径的数字当同表对手
（吓退自己），要么假装没看见（送审时被审稿人拿出来）。两个方向都错，唯一出路是核实口径。

**为什么它仍不能进 roster**：无公开代码 → 无法在我们协议下跑通 → 按 FR-006 不能当 baseline。
核实的价值是「知道自己站在哪里、论文里那句话怎么写」，不是找到一个新对手。
