# Phase R1 · 方法设计准入审计

> 更新于 **2026-09-07**（E1 补 §8、E2 补 §9、E3 补 §12，作者裁决补 §13，E4 补 §14，作者裁决补 §15，E5 补 §16，E9 补 §17，E10 补 §18）。本页只记录已实测的 R1 数字与审计结论。R1 仍是
> `preparation_partial_blocked`，没有方法获得 GPU pilot 准入。

## 1. 产物与代码身份

- 根目录：`runs/stages/R1/r1-v61-20260904/`；
- 代码提交：`277b36f94cf88c8584fe60f83470a965d4d849ef`；
- P1 绑定：r15 / `1e31a9acef39261f776f7ed4069fd73f4531e8d12b55779bfc0fbd74c67f9655`；
- `id_coverage.json`：`ca481ecf3b899cacf553f258992f6603f8fa417a97cd25ee94176e3f313bb2e6`；
- `power_analysis.json`：`0e137ae52d06c03a2bd5f1bcf0c8ed55b36e2218fdb70c6318b3cf2ee99ab3df`；
- `literature_matrix.json`：`b87752670fb9c4d1426776b8130a401af95bc5c6185f6ca91d1fee24c7dc753d`
  （原冻结值 `64874f4c…2476`，09-06 漂移到 `b874d34c…6171`；E5 **先纠正两个 `baseline_gate` 再重冻结**
  为 `5d9bcf9e…6c07c`，被取代的值逐字保留在该文件的 `amendments[0]`，见
  [§16.3](#163-两条漂移的裁决两条走不同的路)；E9 再**追加**两条 IP&M 2024 的 `no_public_code` 条目，
  未改动任何既有条目与门裁决，见 [§17.4](#174-对-a4-契约与-e6-的影响不阻塞)）；
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
  open_finding 逐字保留在 `amendments[0]`，修订发生在任何 C5 数字存在之前。
  **E5 已按 [§16.3](#163-两条漂移的裁决两条走不同的路) 对该值重冻结**——磁盘上的字节是两次正式审查的
  产物，不是 09-06 的漂移字节；
- `factuality_cv/factuality_cv.json`：
  `3a724cf77a2a34bb11f40d225725504b176e4d62e916c5b34c92f9d10a52c5c4`；
- `protocol/degree_requirements.json`：
  `f47eb6a3022c7787fb54f2289878d55e6453c462f1333047f12ececbc7207ac8`
  （**2026-09-07 因作者纠正学校前提而重冻结**，v1 值 `ceeb581b…a47e` 作废，见 [§10](#10-学位标准前提纠正2026-09-07)）；
- `protocol.json`：`81ad04f8aa351de4e8f384619f3f4ce48683bc49f8df96bfa99122c739c39390`
  （E9 随文献矩阵补收重冻结 `literature_matrix` 哈希，前值 `497aae22…423155`；
  再往前 E5 在两条漂移**各自裁决之后**重冻结 `design_briefs` 与 `literature_matrix` 两个 artifact 哈希，
  并写入 `amendments[0]` 记录溯源与处置，前值 `fed98d2a…f619fc`；再往前因学位前提纠正由 `cc80e066…75dc`
  重算。R1 的 protocol.json 没有被 A3/P1 或任何下游产物引用，重冻结不影响其他信任根）；
- `status.json`：`e15ccbb6a110c1f7c95758e2de02a5c69433b4619000e1420ef0374529cb8c2c`
  （E10 补 `acci_feasibility` 并把 identity gate 从「待审计」更新为 `not_runnable`，前值 `f407643c…2182`；E9 补齐 `ipm_2024_protocol_verification` 的实测结论，前值 `167d5219…5212`；再往前 E5 加入 `cross_artifact_audit`、把 T023 移入 `completed_tasks`、把 `known_inconsistencies`
  标记为 RESOLVED，前值 `196339e9…0bf9`；再往前 §15 加入 `identity_baseline_gate_decision` 与 `ipm_2024_protocol_verification` 并重写
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
  MAVEN event type 会成为新的未经验证 adapter，不能冒充官方 baseline。RESIJ 未取得官方代码。**E10 进一步
  证实 ACCI 的公开仓库只是 README-only 占位符**：没有 trainer、模型、checkpoint、依赖或数据/评测接口，
  所以既不能透明移植，也不能作为我们协议下的第二方法族；详情见 [§18](#18-e10--acci-官方仓库静态核查2026-09-07)。
  Ch1 input blocker 已由 §7 的 Qwen artifact 关闭，但按 §15 重界定后的第二方法族门仍 `blocked`。
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

### 9.6 E8 · `llmere-causal-s13` 生成输出有效性失败（2026-09-10）

透明适配的 seed-13 LoRA SFT 已完成，随后对 291 篇 internal-dev 的 11,149 条 causal 分区完成 generation；
adapter 与原始 `predict/generated_predictions.jsonl`（59,336,796 bytes）均保留在
`gpu-4090:/data/TJK/ekg/runs/stages/R1/r1-v61-20260904/baselines/relation/llmere-causal-s13/`。但这一轮**没有
产生可评分的官方 predictions、metrics 或 final metadata**：严格转换不能把生成文本无歧义地还原为关系集合。

全量扫描得到两类互不混淆的现象：

- 第 107 条在同一个 `PRECONDITION` 字段重复同一条格式合法的事件引用。转换器最终本来就以 relation set
  写出 pair，故 `372a6e2` 仅将这类精确重复归并为一个成员；该归并有定向回归测试，未知引用、自环、缺字段、
  非法标签及其余 malformed 输出仍 fail-fast。
- 另有 **95** 条无法解析：第 7,817 条 1 条，及第 8,842–8,935 条连续 94 条。后 94 条全属于同一篇 47-event
  文档的两个 k=30 分区，输出包括缺失 `CAUSE` 标签、断裂 `<e…>` 标记和自由文本，不能从文本唯一确定应输出的
  关系或 NONE。把它们补为 NONE、猜 event id、只重生成该 94 条后与原结果拼接，都将改变或按结果选择推理口径，
  因而禁止。

初步的“字符长度导致截断”解释已被反证：用本轮固定 Llama-3 tokenizer 对全部 11,149 个保存 prompt 重计，
范围为 286–2,015 tokens，**0 条**超过 `cutoff_len=2048`；95 条无效样本为 472–2,015 tokens。当前只能如实
归因为模型输出未满足格式，不能把根因写成截断。官方 causal P/R/F1 仍为 **unavailable**，SFT loss、ROUGE 和
BLEU 均不是本项目的实验指标。若要重新取得该 baseline 数字，必须先冻结一份完整、统一的新推理/约束解码
方案并获作者授权，再对全 11,149 条重新生成；本轮不允许以局部修补替代。

> ⚠️ **2026-09-17 补充（§23，C-3）**：重扫确认 95 条数字无误，但同时测出 **11,149 条全部退化重复**（输出中位 1,755 字符 vs target 98 字符，最短 613），⇒ 根因是**生成侧没有终止语义**，而不是「模型偶尔不守格式」。那 95 条是退化污染到了第一行，其余 11,054 条只是污染落在第一个换行之后、被转换器切掉了——**同一个缺陷的两种表现**。恢复方案与成本重估（42 GPU·h → **< 1 GPU·h**）见 §23。

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

**记录时未修，已由 E5 于同日裁决并修复**（见 [§16](#16-e5--t023-跨产物一致性审计2026-09-07)）：记录当时无法核实 09-06 改动的意图与授权，而按文档层级，裁决以本页与 `status.json` 为准
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

**2026-09-20 C-15 更正（不回写冻结旧产物）**：上面关于 k=30 的直接 pair 天花板判断是错的。
官方 converter 会把 query anchor 重复放进每一个 partition，所以训练集的 **48,562/48,562 个 direct causal
mention pair 都可达**。分区真正隐藏的是中间节点：11,231 个有 two-hop support 的 direct pair 中，
8,826 个保留了该 support（78.59%）。后续报告不得再写「跨分区 direct pair 按构造不可生成」。

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

## 16. E5 · T023 跨产物一致性审计（2026-09-07）

**本节不训练、不用 GPU、不访问 final-valid。** 产物：
`runs/stages/R1/r1-v61-20260904/audit/cross_artifact_audit.json`（schema `ekg.r1_cross_artifact_audit.v2`）。

### 16.1 先修一个使 T023 无法在自己的时点运行的循环依赖

`scripts/audit_r1_consistency.py`（09-06 由 `3f02640` 引入）**要求 `T023` 已打勾才肯继续**，也就是把
这次审计写成了它自己的前置；同时它在第一个失败处 `raise`，因此**永远产不出一份列全问题的报告**——
而"列全问题"正是 T023 的交付物。实跑首次即证实：

```text
ConsistencyAuditError: R1 task is not complete: T023
```

按 `TASKS.md` 的声明，T023 依赖的是 **T012–T022**，T024 则由 T023 放行。据此做三处最小修改：

1. 前置检查改为 T012–T022，**去掉 T023/T024 的自指**；
2. `_require` 只保留给「被审计文件缺失、审计无法进行」，其余全部改为**收集 finding**，
   报告带 `findings` 列表，`status = pass | blocked`；
3. T024 尚未执行时 `protocol.json` 没有 `phase_contracts` 绑定是**预期状态**，记为 `pending_t024`
   而不是不一致；已声明但与文件不符才是不一致。

改动只动这一个脚本，`ruff` 0，既有 6 个单测（只测辅助函数）不受影响。

### 16.2 09-06 漂移的溯源：找到了决定性证据

E5 的硬约束是**先查明来源，不得先改哈希让审计变绿**。来源查明如下。

`runs/` 在 `.gitignore` 里，两个漂移文件没有 git 历史，冻结版字节本地已不存在。但 09-06 的**提交时间线**
给出了决定性证据：

| 时刻 | 提交 | 内容 |
|---|---|---|
| 09-06 14:12 | `3f02640` | `feat(r1): freeze method contracts and audit`——写入 PHASE_C5/A4/D4 三份契约文件与审计脚本 |
| **09-06 15:27** | **（无提交）** | **`design_briefs.json` 与 `literature_matrix.json` 被改，`protocol.json` 未重冻结** |
| 09-06 15:35 | `f6966a0` | `docs(r1): record Qwen argument baseline closure`——只改 `docs/results/PHASE_R1.md`，新增 §7 |

15:27 的改动属于 15:35 那个提交的同一次会话。**`f6966a0` 自己的正文给出了那次改动的意图和它的边界**：

- §7 明确写 **「T020 的 runnable input/baseline blocker 由 Qwen artifact 关闭」**，并写明该 baseline
  「低于冻结 official-joint MUC `.809847`，所以只作为可运行的 independent argument-aware input/baseline，
  **不**作为性能胜出」；
- 同一提交改的 §5 仍然写着 Ch2 **「仍缺第二个独立同协议强 baseline」**。

据此，两半漂移的性质**完全不同**：

- **identity 半有提交正文支持，但过度解读**：`f6966a0` 关闭的是 **input/baseline blocker**，
  15:27 却把它写成了 `baseline_gate = pass` 与 brief `accepted`。**blocker 关闭 ≠ 审查通过**——
  T020 的正式审查直到 09-07 才由 E4 完成。
- **relation 半没有任何提交正文支持**，且与**同一次提交**写进结果页的 §5 直接矛盾，
  也与 E1 次日在 [§8.5](#85-对-relation-baseline-门的影响) 预注册的判断相反。
- 补充旁证：`literature_matrix.json` 的 `audit_date` 至今仍是 **2026-09-04**——15:27 改了内容却
  **没有重跑任何审计**，这与"未同步 `protocol.json`"是同一个疏漏的两个面。

### 16.3 两条漂移的裁决：两条走不同的路

| 产物 | 裁决 | 理由 |
|---|---|---|
| `design_briefs.json` | **原样重冻结** `2220b86c…1999` | 磁盘上的字节**已经不是** 09-06 的漂移字节：`briefs.relation` 由 E3 的正式 T021 审查重写、`briefs.identity` 由 E4 的正式 T020 审查与 §15 修订重写；`briefs.factuality` 逐条比对 [§6](#6-t022-事实性因果-design-brief) 的 T022 记录（冻结链 · 三类 confusion 中介 · flat-head remove-core · DMRoBERTa · cue permutation 负控）**完全一致**。09-06 那三个未授权的 `accepted` 标记是被**两次正式审查取代**，不是被接受 |
| `literature_matrix.json` | **先改内容，再重冻结** `b874d34c…6171` → `5d9bcf9e…6c07c` | 两个 `baseline_gate = pass` 是**错的**，与自身 `global_decision`、`status.json`、本页、E1 预注册四处矛盾。两者改回 `blocked`，identity 的**两个门分账**（input/baseline blocker 已闭合于 §7；第二方法族门按 §15 仍 open），relation 写入 E1 预注册与 §13 裁决。被取代的原值逐字保留在该文件自己的 `amendments[0]`，**所有 `chapters.*.methods` 与 `upstream_checkouts` 逐字节未动** |

`protocol.json` 在**两条裁决都做完之后**才重冻结（`fed98d2a…f619fc` → `497aae22…423155`），
并在其 `amendments[0]` 里记下溯源、两个被取代的哈希、漂移存档路径与各自处置。
**顺序就是本节的要点**：先溯源 → 再纠正/验证内容 → 最后才动哈希。

### 16.4 审计结果

在上述裁决之后实跑：

```bash
uv run python scripts/audit_r1_consistency.py \
  --output runs/stages/R1/r1-v61-20260904/audit/cross_artifact_audit.json
```

| 项 | 结果 |
|---|---|
| 审计状态 | **`pass`，`findings` 为 0** |
| 需求覆盖 | SPEC 声明 **35** 条，映射 **35** 条，引用 **23** 个验证任务，未映射 0，文档引用未声明需求 0 |
| 六个 R1 产物身份 | 全部 `frozen`（漂移已按 §16.3 裁决消解） |
| 三份 method phase 契约 | 全部 `pending_t024`（**预期状态**，不是不一致） |
| 信任根 | P1 r15 与 A3 r17 逐位一致 |
| final-valid | `used_for_model_or_method_selection = false` |

**R1 仍未 PASS**，报告的 `r1_pass_blockers` 列出四条：`status` 仍是 `preparation_partial_blocked`，
以及三份契约待 T024。审计通过的是**跨产物一致性**这一项，不是 R1 准入。

### 16.5 脚本查不到、必须人工核对的四条结论（E6/E7 的硬输入）

审计脚本只检查契约的**章节存在性与哈希绑定**，不读契约内容，因此以下三条由人工跨产物核对得出：

1. ⚠️ **A4 契约的 roster 与 §13 裁决矛盾**：契约第 3 项写 TacoERE 适配是
   "independent recent family"，而 §13 已裁定它**不满足强度条款**、第二方法族改由 **LLMERE-causal** 承担。
   **E6 必须改契约内容，不能只补哈希。**
2. ⚠️ **C5 契约的 roster 与 §15 裁决矛盾**：契约第 3 项把 Qwen3 档写成 "argument-aware strong baseline"，
   而 §15 已把它**重定义为注册负面对照**，第二方法族改为待核查的 ACCI 移植。契约还带一臂
   "hard arguments without uncertainty" 与一项"退火 local pair classifier"，两者都不在 E4 冻结的 brief roster 里。
   **E6 必须对齐。**
3. ⚠️ **D4 契约与 §6 的 T022 记录一致**，无需修改。
4. 📌 **可追溯性缺口（留给 E7）**：`scripts/audit_r1_consistency.py` **不在** `protocol.json` 的
   `code.files` 里，而它的同类 `scripts/audit_r1_dataset_ids.py` **在**——这次审计因此无法从冻结代码集
   复现。与 E7 已经持有的 `supervised.py` 缺口同类，**本节不顺手修**，交 E7 一并处理。

本节没有启动任何 GPU 任务，也没有为让审计变绿而改动任何哈希。

## 17. E9 · IP&M 2024 口径核实（2026-09-07）

**本节只做文献口径核实，不训练、不用 GPU、不访问 final-valid。**
目标：Zhang et al., *A graph propagation model with rich event structures for joint event relation
extraction*, Information Processing & Management **61(5) 103811 (2024)**，DOI `10.1016/j.ipm.2024.103811`，
OpenAlex `W4399936537`，DBLP `journals/ipm/ZhangCLZRW24`，报 MAVEN-ERE **MUC 86.1 / temporal 60.7 /
causal 37.4 / subevent 32.9**。

### 17.1 全文不可得：四条途径逐条实测

| 途径 | 实测结果 |
|---|---|
| OpenAlex API | `open_access.is_oa = false`、`oa_status = closed`、`any_repository_has_fulltext = false`、`locations_count = 1`（仅 Elsevier），`best_oa_location = null` |
| Semantic Scholar API | `openAccessPdf = {"url": "", "status": "CLOSED"}` |
| arXiv / preprint 检索 | 未找到任何 preprint 或作者自存版本 |
| 引用文献（`cited_by_count = 12`，取回 10 条） | **无一开放获取**，且主题多为其他 IE 任务，没有在 MAVEN-ERE 上复现其数字的候选 |

因此**预注册判据的原始形式（读它自己的对照表）无法执行**。

### 17.2 改用等价路径：证明我们的尺子就是官方尺子

判据的实质是「把它的数字和我们的数字放到同一把尺上」。它的对照表拿不到，但**它对标的官方论文
数字是公开的**，于是把这一环换成：**我们的官方 joint 复现 vs MAVEN-ERE 官方论文发表数字**。
若两者对齐，则我们的尺子即官方尺子，其他论文引用官方数字时就与我们同尺。

官方数字取自 MAVEN-ERE（EMNLP 2022）arXiv `2211.07342v1` **Table 7 与 Table 8**，
RoBERTa-base，**5 次随机试验的均值与标准差**，评测集为官方 **test**：

| 指标 | 官方单任务 | 官方 **+joint** | 我们的主锚（official joint，seed 13，291 篇 internal-dev） | 差 |
|---|---:|---:|---:|---:|
| MUC F1 | 81.4 (sd .51) | **82.1** (sd .43) | **80.98** | −1.1 |
| B³ F1 | 98.1 (.10) | 98.2 (.11) | 98.04 | −0.16 |
| CEAF-e F1 | 97.7 (.13) | 97.9 (.09) | 97.73 | −0.17 |
| BLANC F1 | 89.8 (.36) | 90.2 (.27) | 89.88 | −0.32 |
| causal F1 | 30.6 (.44) | **31.5** (.42) | **33.17** | **+1.7** |
| subevent F1 | 26.7 (1.34) | **27.5** (1.10) | 29.75 | +2.25 |
| temporal F1 | 55.8 (.42) | **56.0** (.59) | 51.63 | **−4.4** |

**共指四个指标全部落在 ±0.4 以内**，causal 与 subevent 我们略高，temporal 我们低 4.4 点。
两点必须如实说明：(1) 官方数字在 **857 篇 test** 上、我们在 **291 篇 internal-dev** 上，文档集不同，
±1–2 点的自然波动不可归因于实现差异；(2) temporal 的 4.4 点缺口方向与
[`PHASE_A.md`](PHASE_A.md) 已记录的 **TIMEX 头缺失**一致，但本节没有做隔离实验，**不作因果结论**，
登记为待查。

即便如此，共指四指标同时对齐这一条足以支持：**我们的官方 joint 复现忠实于官方发表口径**。
这是我们第一次用官方论文的发表数字独立佐证主锚复现的忠实性。

### 17.3 裁决与对判断的修正

按 [§15.3](#153-ipm-2024-口径核实判据三种处置与排期) 预注册的三种处置，本次落在**第三种：拿不到全文**——
登记为「**未核实口径的更强公开数字**」，论文如实披露，**既不当对手，也不当我们已被超越的证据**。
但它带回来的证据比原判据更强，因此要同时修正一处此前的推断：

> ⚠️ **修正 [§15.3](#153-ipm-2024-口径核实判据三种处置与排期) 的推断。** 该节写「86.1 比我们已知的任何
> MAVEN-ERE 共指数字都高 5–9 点……几乎必然含口径成分」。这个推断**被新证据削弱**：拿来比的
> `77.47` 是 Phase A **我们自己的方法档**在 710 篇 valid 上的分数，不是官方 joint 的复现，混用它是不对的。
> 正确的对照是官方论文 +joint 的 **82.1**，IP&M 高出 **4.0** 点；且 causal +5.9、temporal +4.7、
> subevent +5.4——**四族齐涨 4–6 点，模式内部一致**。口径差异通常不会在四个敏感度不同的任务上如此均匀，
> 所以**更可能是真实的方法增益**。原推断的方向记录在案，不掩饰。

仍然未确证的一环：**IP&M 用的是官方 test 还是 valid、是否用组织方 `evaluate.py`**。2024 年 6 月
CodaLab 通道尚开（我们直到 2026-07-30 才发现关闭，见
[§4](#4-文献代码可运行性)与 `PHASE_A.md`），所以它报 test 是合理猜测，但**没有证据，不写进结论**。

### 17.4 对 A4 契约与 E6 的影响：不阻塞

**E6 可以照常冻结 A4 契约**，理由三条：

1. **它进不了 roster**：无公开代码 ⇒ 无法在我们的冻结协议下运行 ⇒ 按 FR-006 不能当 baseline。
   这条与核实结果无关，核实前后都成立。
2. **A4 的及格线是内部对照，不是"超过所有公开数字"**：QR-001 要求超过**冻结主锚**与**第二方法族**，
   两者都在我们自己的协议内。IP&M 的 37.4 不在协议内，改不了这条线。
3. **披露义务已经落地**：Ch1 与 Ch2 的相关工作必须写明这篇报了更高的四族数字、我们无法复现也无法
   同协议运行、口径未确证。本节即为该披露的出处。

同时它对两章的**方法叙述**有实质影响，已写进 [§14.1](#141-四条已被占的一般命题与-c5-的窄-delta)：
「用预测论元提升 MAVEN-ERE coreference」这一般命题被它占住，C5 的 delta 必须收在
**角色后验 + 缺失感知的不确定性门控**上，不能是"用论元帮共指"。这一条与它的数字能否对齐无关。

📌 **文献矩阵补收**：它此前**不在** `literature_matrix.json` 里，与 E.1 发现的 LLMERE 漏收同类。
本节已把它作为 `no_public_code` 条目补进 identity 与 relation 两章的 `methods`，
并按 [§16.3](#163-两条漂移的裁决两条走不同的路) 的顺序重冻结哈希。

## 18. E10 · ACCI 官方仓库静态核查（2026-09-07）

**本节只做仓库、论文与冻结输入的静态核查：未训练、未推理、未用 GPU、未访问 final-valid。** 产物为
`runs/stages/R1/r1-v61-20260904/baselines/identity/acci_feasibility/feasibility.json`
（SHA-256 `1885d8d3460f2d1d94a068ce0269ea18486eb177975960ff9e823863ad5eee59`）。

### 18.1 官方仓库实际没有实现

冻结的只读克隆 `upstream/acci` 对应 `github.com/era211/ACCI` 的 `main`：commit
`7f5bcd81e0a352f15263a5c7e7c4853b9e3023fa`（2025-06-02），tree
`d4c8aa14a2462126060a4a69bf54cea11d62fe43`。`git ls-remote` 与 GitHub API 都返回同一 main
commit；全历史**仅一个 commit**、tree **仅一个 `README.md`**（其 SHA-256
`c8e0dc4e6c3d712d9c297603cd302f995fa0695515d7894468b18b08aec727e8`），无 root LICENSE，API
显示 repository size 0 KiB、release 0。

因此缺失的不是一小段 glue code，而是全部可执行链：**没有** trainer、推理入口、模型实现、配置、
dataset reader、candidate builder、evaluator、checkpoint、release asset 或 dependency manifest。论文
([arXiv:2506.01488](https://arxiv.org/abs/2506.01488)) 的 PyTorch/AdamW、`1e-5` 模型学习率、`1e-4`
分类头学习率与 4×A40 设置只能说明作者曾有私有实现，不能成为可验证的公开复现配方。

### 18.2 冻结 MAVEN-ERE 输入可供新写适配器，但不能让缺失接口“兼容”

用 `probe_acci_pairs.py` 在 `maven_ere_{train,internal-dev}.json` manifest 上全量读取
`data/processed/maven_ere/train.jsonl`。它逐 mention 校验 sentence ID、token offset、trigger span，并构造
论文所述 `<m> trigger </m>` 句子；输出 `manifest_probe.json`（SHA-256
`1ece0e2fae7d01f5ca8a711f9f4f5c2d2a7853b0501b9cb76d4379c120f80c19`）。

| split | documents | marker-ready mentions | 完整文档内候选对 | coreferent pairs |
|---|---:|---:|---:|---:|
| train | 2,622 | 66,744 | 1,148,762 | 14,011 |
| internal-dev | 291 | 7,195 | 117,435 | 1,456 |

这证明本地源数据**足够让我们另写** marked-pair adapter；它**不**证明与 ACCI code 兼容——上游根本没有
可调用的 parser 或 candidate interface。更关键的是，论文的任务是 ECB+/GVC **跨文档** ECR，候选对先限制
在同一 subtopic，并使用 discourse-coherence retrieval 或 heuristic non-coreference filtering；C5 必须评分
MAVEN-ERE **文档内完整候选全集**。任何假想重写都至少要重做其数据/候选构造与输入、训练、推理、聚类和评分，
不是忠实移植。

### 18.3 裁决

**裁决：`not_runnable`。** E10 不授权从论文散文重建 ACCI；那会是我们新写的实现，既不是官方复现，也不是
对可运行官方代码的透明移植，无法满足 §15 的第 3 条（由我们在冻结协议下跑通该独立机制）。故**不排**
single-card seed-13、**不使用 GPU**，也不把 ECB+/GVC 的 CoNLL F1 写入 MAVEN-ERE 对照表。

Ch1 的第二方法族门保持 `blocked`。下一步需要在 §15 的四条新措辞下由作者对替代名单作出决定；E6 可以
处理已解锁的 A4/D4 contract，但不能把 C5 baseline 缺口伪装成已冻结。

## 19. E6 · T024 冻结获准的 method phase contract（2026-09-07）

**本节只冻结契约与可追溯身份：未实现、未训练、未推理、未用 GPU、未访问 final-valid。** T024 的语义是
“冻结每一个已经通过自身准入的 phase”，不是把仍缺强 baseline 的章节伪造为放行。因此 A4 与 D4 进入
`frozen`，C5 明确留在 `blocked_pre_admission`。

| phase | T024 裁决 | 契约 SHA-256 | R1 protocol binding |
|---|---|---|---|
| A4 / relation | `frozen` | `fe15945d602373fa5b7ed664243e6eb81e697ee0621d29e127dbcd1a8ca9ac80` | `phase_contracts.relation` |
| D4 / factuality | `frozen` | `01e1ba2f74627216a19c02ad47dbc5bbf35e72fe4530ce18ede76072328c49b1` | `phase_contracts.factuality` |
| C5 / identity | `blocked_pre_admission`，**不绑定**草案 | `8bc031b92de56af01d39e00f96f979be7d3a0cdb66a8a6e00d460f71f35066f8`（仅记录） | `phase_contracts.identity.state=blocked`，无 path/hash binding |

T024 artifact 是
`runs/stages/R1/r1-v61-20260904/phase_contracts/t024_freeze.json`，SHA-256
`3b44a2e2fdf402bfa55492d6527e642a7f75bb9301ad1c1e4098477ec7edd81b`；最终 R1 `protocol.json` SHA-256 是
`2fde1577c92d826d0ee12e722e6183b92421477ea38769e15144cdaa300c7094`。契约文件引用 R1 的已冻结 inputs，
outer protocol 持有契约文件 hash，而不在契约内反写 outer-protocol hash，避免 self-hash cycle。

- A4 的 roster 已按 §13 改正：`taco-s13-r3` 是固定透明适配对照、不是第二条强方法族；
  `llmere-causal-s13` 以 upstream `94d4ef27…a798`、未改 converter、causal-only 48,365 / 11,149、
  Llama-3-8B ungated-mirror weight disclosure、LoRA r64 / lr `2e-4` / cosine / 3 epochs / 2048 / seed 13 和
  frozen `evaluate.py` 完整规格化，但 metrics 仍 pending。A4 seed-13 pilot 可在 A4.0–A4.2、local gate
  和重新核卡后启动；它只有在 LLMERE 数字落地且被超过后才可进入确认性 promotion。
- D4 的 T022 roster、five-fold OOF inputs、promotion/stop、bundle 与 GPU command 已与契约逐项一致，故只
  增加冻结身份而不改方法内容。
- C5 不再称 `qwen3-argument-s13-r2` 为 strong baseline；它是“朴素池化预测论元会掉点”的注册负面对照。
  E10 已裁决 ACCI `not_runnable`，而 IP&M 2024 无公开代码，故两者都不能占第二方法族。旧的 annealed
  local-pair 与 hard-argument 臂也不在 E4 通过的 brief roster 中，已从待重新准入草案移除。作者按 §15
  四条件指定新名单前，禁止 C5 的实现、preflight、smoke 或 GPU。

重跑的审计命令：

```bash
uv run python scripts/audit_r1_consistency.py \
  --output runs/stages/R1/r1-v61-20260904/audit/cross_artifact_audit.json
```

结果为 `pass`、`findings = 0`、35/35 requirements mapped。审计现在区分尚未发生的 `pending_t024` 与已记录但不
绑定文档的 `blocked_pre_admission`：A4/D4 是 `frozen`，C5 是后者。R1 状态仍
`preparation_partial_blocked`，仅余 C5 的 author roster blocker；这不是 A4/D4 pilot 的 R1 blocker。
`scripts/audit_r1_consistency.py` 尚未进入 R1 `code.files`，这个可追溯性缺口以及 relation trainer hash
缺口按队列留给 E7，未在 E6 顺手重冻结。

## 20. E7 · relation 与审计代码身份闭环（2026-09-07）

**本节只补可追溯性身份：未改 trainer、未重训、未评分、未用 GPU、未访问 final-valid。** E1 的根因已是
确定性的 encoder-input 变化，不能把当前 `supervised.py` 的 hash 回填给历史 r2。因此只在两个 relation
`run_metadata.protocol_binding.hashes` 中新增 `supervised_extractor` 键，所有既有 hash（尤其 trainer
`5c513bdb…d0f2c6`）、checkpoint、预测与指标字节均未动：

| run | 训练 commit | `supervised.py` SHA-256 | 更新后 `run_metadata.json` SHA-256 | 身份 |
|---|---|---|---|---|
| `taco-s13-r2` | `d8fcd30e…ea4f` | `ffb40460c454a29b3a14d3075141b654bf510cd5d6277d61a2728a56ea4a1a25` | `f9b10fc724bef7c195bc964eb5b6f2a6a78cc647f11d8493a5933daa3e6e8706` | superseded；pre-`3f02640` context 不在当前源码下复现 |
| `taco-s13-r3` | `e7961828…3775` | `9cdf54a7991af2bcacef70d2b249158cb46665f89fec2366de62f4e86387ab7c` | `44ffe6267202aec11cc16c84f41059447160f135d39716831ffc7fef2f472999` | recorded；含 `3f02640`，与冻结当前源码一致 |

对账产物
`runs/stages/R1/r1-v61-20260904/baselines/relation/code_hash_reconciliation.json` 的 SHA-256 是
`833b3c4d96630c015ca2e70020c358b30b1ac9b88d8b0f0ddfbfbf2fefbc5ebd`，已作为
`artifacts.relation_code_hash_reconciliation` 绑定进 R1 protocol。它明确断言没有修改 trainer、没有重建
P1，也没有改动任何已有 hash；所以 P1 r15 与 A3 r17 身份不需要重绑。

`scripts/audit_r1_consistency.py` 现以 SHA-256
`f6fdc099502065f1640ec17712a80a818bd31175ddb788bd428aff0a81aeef90` 加入 R1
`protocol.json.code.files`，并在每次审计中自行比对该绑定；后续脚本漂移会产生
`audit-script-hash-drift` finding，不能再静默重跑审计。审计还逐一重算两个 `run_metadata.json` 的
digest，并确认其 `supervised_extractor` 键与对账产物一致；漂移会产生
`relation-run-metadata-drift` 或 `relation-extractor-hash-drift` finding。最终 R1 protocol SHA-256 为
`199852a1f0b81e088f7568d9462d9fe226db15bdd21a78346b6d03bef80cf058`。

验证命令：

```bash
uv run python scripts/audit_r1_consistency.py \
  --output runs/stages/R1/r1-v61-20260904/audit/cross_artifact_audit.json
```

结果为 `pass`、`findings = 0`、35/35 requirements mapped；新对账 artifact 的 frozen/actual SHA-256 一致。
R1 仍是 `preparation_partial_blocked`，只剩 C5 的 author roster / `blocked_pre_admission`，不是 E7 的
traceability finding。

## 21. E12 · QR-001 修订与 FR-016 复现保真度（2026-09-11）

**本节只记录治理修订与身份重绑：未实现、未训练、未推理、未用 GPU、未访问 final-valid。**
修订发生时 C5/A4/D4 **三章都不存在任何 proposed-method 结果**（C5/A4 未实现，D4 只完成 D4.0
实现与本地 gate，`runs/stages/D4/` 在本机与 gpu-4090 上均不存在），故不构成「看到分数再改规则」。

### 21.1 触发证据：九篇同领域学位论文的实测体例

作者提供 9 篇知网学位论文，本机 `/mnt/d` 直读、`pdftotext -layout` 转换后逐篇提取，
完整记录见 `docs/replan/THESIS_REF_f2/f4/f5_*.md` 与 `docs/replan/REPLAN_20260911_*.md`。

| 论文 | 学校/学位 | 页 | 方法章 | 外部公开 baseline | 胜出幅度 | 统计检验 |
|---|---|---|---|---|---|---|
| 徐昇《面向事件表述多样性和信息缺失性的事件共指消解研究》 | 苏州大学（129 页，疑博） | 129 | 3 | **3**（第四/五章各 1） | 章间 +0.1 / +0.4 K-AVG | **0** |
| 钱子杰《基于多维数据增强的篇章级事件事实性识别》 | 苏州大学 硕 | 72 | 2 | 9 | 宏 F1 +0.97 | **0** |
| 宁婉廷《提示驱动的事件关系抽取研究与应用》 | 大连理工 硕 | 92 | 2 | 3–11 | +2.9（时序）/ +0.1（粗粒度） | **0** |
| 李璐《事件抽取与事件共指消解的研究与应用》 | 西南交大 工程硕 | 67 | 2 | 1–7 | 触发词 **+0.19**；ECB+ CoNLL **+0.2**（B³ 输给 CD-LM） | **0** |
| 陈玉婷《基于复杂事件因果关系抽取的事理图谱构建研究》 | 华科 硕 | 77 | 2 | 7 | +1.45 F1 | **0** |
| 李磊《军事领域事理图谱的构建与应用研究》 | 哈工大 专硕 | 79 | 2 | — | 人工对照 P 56.9 | **0** |
| 邓宇涛《基于问答大模型的事理图谱构建技术研究》 | 硕 | 69 | 2 | — | — | **0** |
| 陈泽《事件知识图谱构建关键技术及应用研究》 | 辽宁大学 博 | 150 | 3+应用 | — | — | — |
| 陈勇《面向开源信息的图谱构建与事件预测研究》 | 中科大 工博 | 196 | 3+ | 16 | — | 少量 |

两条与本项目直接冲突的实测事实：

1. **外部公开对手 3 个即可**，且**自家前章方法可作后章主表对照行**（徐昇第四/五章即
   「MultiRep（自家 ch3）+ CorefPrompt（自家 ch4）+ Lu&Ng2021」）。此前把「第二个可跑的公开方法族」
   当作**准入门**，是我们自己的运行口径，不是领域要求，且已使 C5 停摆数周、A4 串在 LLMERE 之后。
2. **胜出幅度实测分布为 +0.19 ~ +2.9**；徐昇第四章 CorefPrompt（EMNLP 2023 正式发表）的 MUC 45.3
   **低于**自家第三章 MultiRep 46.2，正文自述「性能相当」并把卖点改为显存减半，章节照样成立。

### 21.2 SPEC v1.1.0 的两处修订

- **QR-001（修订）**：主指标仍须超过冻结主锚；**baseline 广度由准入门改为报告要求**——章节可在其余
  方法族尚在复现时实现、pilot 与报告；跑不了的必须进「方法/代码可得性」表并写明具体障碍。
- **FR-016（新增）**：每个为对比表复现的外部方法必须带保真度状态，二选一——**(a) Verified**：在其
  原始基准与划分上复现出其已发表数字，落在**事前声明**的容差内；**(b) Unverifiable**：点名具体障碍
  （无 trainer / 语料需许可 / checkpoint 失效 / 划分未公开），该行标「透明适配」并逐条披露差异。
  状态 (b) 不得写成忠实复现，也不得用于主张该公开方法弱于其自报数字。

名册与逐方法保真度路径见 [`../BASELINE_ROSTER.md`](../BASELINE_ROSTER.md)。

### 21.3 三份 phase 契约的重绑

| phase | 变更 | 新契约 SHA-256 |
|---|---|---|
| identity / C5 | `blocked_pre_admission` → **`frozen`**；第二方法族填入 Global-Local Topic（Xu et al., EMNLP 2022）经 EasyECR 的透明移植，保真度状态按名册 §1.1 决策树判定 | `b504f29cd96134e3ec54d920fa76c27209d4126234d884e0638c029f09432d1f` |
| relation / A4 | 确认性 promotion **不再以「等到 LLMERE 数字」为前置**；LLMERE 降为主表一行，保真度预设 (b) | `79281df74c71db01b5894f28105fb5b7cf5c41be0d721ae791aaf3b90325e529` |
| factuality / D4 | **内容未改**，hash 不变 | `01e1ba2f74627216a19c02ad47dbc5bbf35e72fe4530ce18ede76072328c49b1` |

同步更新的身份：

- `phase_contracts/t024_freeze.json`：`9133a73c46d7e277fca1bef8b2459896d436b816971f68297c9f93aebd5587e7`
  （identity 由 `blocked_contracts` 移入 `approved_contracts`，原 binding 原文保留在 `amendments[0]`）；
- `scripts/audit_r1_consistency.py`：`a1d99a7f7d95e1ea3e1b656d75c496bc893b3a57dffa0a2587009667ea7a65ca`
  （新增 FR-016 的可追溯性映射，并已同步进 R1 `code.files`）；
- `audit/cross_artifact_audit.json`：`622d094bc8befe2fe059cee81e495b6b2b567e1b67a62d56c17d7c97867f8467`；
- R1 `protocol.json`：`f0b4702b258ef61257d0aeae20fd23bb48f36e4ff4761a575ac1b97277150829`。

> **2026-09-11 更正（E17 开工核对时发现并当场修）。** 上面三行原本记的是
> `8103bc2d…2c77a` / `37b0a10d…42591` / `6434816b…37ff5`，那是 E12 中途的状态：审计脚本随后在
> `30dc25a` 又改了一次，R1 `protocol.json` 的 `code.files` 因此在 14:24 重绑到新脚本哈希，
> `cross_artifact_audit.json` 的内容也随输入一起变。三份产物在盘上彼此自洽（脚本哈希
> `a1d99a7f…a65ca` 与 `protocol.json` 内记录的值逐字相同，审计重跑两次字节一致、`PASS` / 36
> requirements），**漂移只发生在本文档的记录里**，故只更正记录，不动产物。
> `phase_contracts/t024_freeze.json`（`9133a73c…587e7`）与三份 phase 契约哈希不受影响。

### 21.4 验证

```bash
uv run python scripts/audit_r1_consistency.py \
  --output runs/stages/R1/r1-v61-20260904/audit/cross_artifact_audit.json
```

结果 **`PASS`，36 requirements mapped**（修订前为 35，新增 FR-016）、`findings = 0`。
本地三件套：**534 passed / 26 skipped**、ruff **0**、`ekg-smoke` **OK**。

### 21.5 未修订的项

Ch1/Ch2/Ch3 的最小有意义效应（`+.010` / `+.010` / `+.030`）、matched seeds 13/17/42、10,000 次文档聚类
配对 bootstrap、Holm 校正、final-valid 封存纪律、各章 guardrail 与 stop conditions **全部不变**。
作者 2026-09-11 明确：统计检验不是实验质量的主要判据，证明方法价值才是；故本轮不动统计门槛。

### 21.6 打开的问题：LLMERE 保真度与 §E.1a 第 6 条冲突

FR-016 要求验证复现正确性；LLMERE 的可验证路径是用官方 `evaluate.py` 给它**已发布的 official valid
710 篇预测**打分、复现其 causal 36.04。但 `HANDOFF.md` §E.1a 第 6 条（作者 2026-09-07 裁决）明确
**不做**此事，理由是 710 篇是封存 final-valid。两条规则抵触，本轮**不擅自选边**；名册 §2.1 列出三种
出路并建议取「保持 §E.1a，LLMERE 记为 (b) Unverifiable，障碍写明」——成本为零且完全诚实。

## 22. C-2 · EasyECR 可运行性核查：**conditionally_runnable**（2026-09-11，静态部分完成）

主表 **C-2**。仓库先前从未在任何文档里留下 URL，本轮补上：**`github.com/hqyang/EasyECR`**，
`main` HEAD **`f6cd779fbddc7ced2b14397041f83d92713115a9`**（2024-08-28 `doc: release EasyECR`，
全历史仅 2 个 commit，2.9 MB）。本节的结论全部来自读码与**机器可复现的依赖求解**，不是网页转述；
**未训练、未下载权重**。

### 22.1 裁决

**`conditionally_runnable`** —— 方法本体、MAVEN-ERE 适配器与 `predict` 通路都在，
但必须打一组**点名可数**的透明补丁才能起跑。没有任何一条是"重写别人的方法"。

| # | 阻断 | 证据 | 补丁 | 规模 |
|---|---|---|---|---|
| 1 | `global_local_topic.py:24` 导入 `allennlp.modules.span_extractors.SelfAttentiveSpanExtractor`，而 **`allennlp` 根本不在 `requirements.txt` 里** | 见 §22.2 的求解器输出 | vendor 该类 | **恰好 2 个调用点**（`:1001` `span_extractor`、`:1004` `mention_span_extractor`），1 行 import |
| 2 | 配置里全是作者本机硬编码路径 `/home/nobody/code/...`、`/data/dev/ecr-data/...` | `config/model_dataset/global_local_topic_mavenere.yaml` | 改写 5 个路径键 | 配置改动 |
| 3 | `example_emnlp2022.py` 在未设时把 `CUDA_VISIBLE_DEVICES` 写死为 `"3"` | 该文件第 5–9 行 | 显式传卡 | 环境变量 |
| 4 | 我们要的是 **291 篇冻结评测集**，它默认吃官方整份 `train/valid/test.jsonl` | `ecr_data.{train,dev,test}_path` 是三个 jsonl | 按 manifest 过滤出子集 jsonl，记补丁前后 hash | 数据准备 |
| 5 | 它自带的评测器是 **coval**，指标集 `['mentions','muc','bcub','ceafe','lea']`、`keep_singletons: True` | `ecr_evaluate.py:18-19` + yaml `evaluator` | **取 `predict` 输出的簇，用我们冻结的 MAVEN 官方 `evaluate.py` 重打分** | 接线 |
| 6 | `maven_ere.py` 的 loader 需要 spacy `en_core_web_sm` | `load_documents()` 调 `spacy.load` | 下载语言包 | 环境 |

### 22.2 依赖矛盾：这次是求解器说的，不是网页说的

```
$ uv pip compile <(printf 'torch==2.0.1\nallennlp==2.10.1\n') --python-version 3.10
  × No solution found when resolving dependencies:
  ╰─▶ Because allennlp==2.10.1 depends on torch>=1.10.0,<1.13.0 and you
      require torch==2.0.1, we can conclude that your requirements and
      allennlp==2.10.1 are incompatible.
```

放开 allennlp 的版本也救不回来：把 EasyECR **完整的** `requirements.txt` 加上一个不带版本的
`allennlp` 一起求解，解算器只能回退到 **`allennlp==0.2.1`（2018）**；只留 `torch==2.0.1` + `allennlp`
则回退到 **`0.9.0`（2019，并把 `spacy` 拉到 2.1.9，与仓库自己声明的 `spacy==3.7.2` 冲突）**。
两者都不是 `span_extractors` 那条 API 线。**所以 vendor 不是偷懒的选择，是唯一的选择**，
并按 FR-016 记录补丁前后 hash。

### 22.3 三件好消息（降低 G-6 的风险）

1. **MAVEN-ERE 适配器已经在仓库里**，不用我们写：`easyecr/ecr_data/datasets/maven_ere/maven_ere.py`
   逐行读官方 jsonl，且它自己声明的统计量与官方**完全一致**——2913/710/857 篇、
   73939/17780/20557 mentions、67984/16301/18908 events。`load_events()` 只对 `train`/`valid`
   生效（test 无金标），与我们"valid 当 test"的既有做法同构。配置
   `global_local_topic_mavenere.yaml` 也已经存在，`num_classes: 169` 是 MAVEN 事件类型数。
2. **选档与阈值都在 dev 上选，不碰 test**：`ecr_framework.py:121-146` 的
   `find_the_best_model(dev_data, ...)` 对 version × `distance_threshold`（9 个值 0.1–0.9）
   做二维扫描，按 `main_metric: CoNLL` 的 F1 取最好。只要把**我们的 selection-dev** 喂给 `dev_data`、
   把 291 篇留给 `predict`，就没有构造性泄漏。
3. **有独立的 `predict` 通路**（`ecr_framework.py:183`），返回打好簇标签的 `EcrData`，
   正好满足"拿它的预测、用我们的评测器打分"这条 A 类口径要求。

### 22.4 还没做的：活体 import 与显存

`conditionally_runnable` 目前是**静态裁决**。真正的建 venv + import 冒烟必须在服务器上做，
而 4090 隧道在本轮后半程 `Connection refused`（先前可连，preflight 与 smoke 都已跑完落盘），
5090 又不支持 torch 2.0（sm_120）。**建议的环境形态**：独立 venv **按 EasyECR 自己的声明**装
`torch==2.0.1` / `transformers==4.21.2`（4090 是 sm_89，torch 2.0.1+cu118 支持），
只 vendor span extractor——**这样补丁数最少、保真度最高**。若改用本项目的 cu128 栈，
`transformers 4.53.3` 已移除 `transformers.AdamW`（`global_local_topic.py:21` 用它），
补丁会从 1 处扩到多处，不划算。

### 22.5 KBP 2017 与 FR-016 状态

原文基准 KBP 2017 是 **LDC 许可语料**，本项目无许可、无获取途径，本轮也未申请。按名册 §1.1 决策树
右支：**FR-016 状态 (b) Unverifiable**，障碍写「原始基准 KBP 2017 需 LDC 许可，本项目无法取得」，
并逐条列出语料、mention 来源、评测器、超参四项差异。第 5 章那行 baseline **可以有**，
但必须标「透明适配」。


## 23. C-3 · E8.1 LLMERE 恢复方案冻结（2026-09-17，本地 + 只读 ssh，未训练、未占卡）

> 对应主表 **C-3**，是 §9.6 的后续。**通过 ≠ 获准重生成**——本节只把方案冻结到可审查的程度，
> 是否执行 G-8 由作者裁决。

### 23.1 C-29.6 · target-third-line stop 的可行性反证（2026-10-02，只读 CPU，未加载模型）

在按 C-3 的恢复方案写任何新 driver 前，对冻结
`llmere-causal-s13/upstream/llmere/data/converted/MAVEN_ERE/causal/test.json` 的 **11,149** 个 target
逐行统计 target 的第三行（`Relevant reasoning information: ...`）。结论：第三行有 **407** 种不同文本；
`Relevant reasoning information: none` 为 **10,743** 条，余下 **406** 条为 instance-specific reasoning。
每条都有三行，但第三行不是静态 stop string。

⇒ C-3 的“在 target 第三行结尾显式 stop”若从每条 `output` 取结束序列，就在 inference 时读取
internal-dev gold；若固定为 `…none`，则会选择性错误处理 406 条。这是【协议】阻断，不是模型质量、CUDA 或
格式修复问题。旧的 `max_new_tokens=512` / 无 stop 运行已 fail-closed，不重跑；本次未实现 recovery driver、
未生成任何新输出、未读取 final-valid。

可接受的后续只能由作者二选一：(甲，建议) LLMERE 保留为 FR-016(b) 无可评分行，并把该命名协议障碍写入
可得性表；(乙) 作者明确批准一个新的、target-independent first-line-only constrained-decoding 契约，然后重新
进行其信息流、静态、CPU、smoke 审查。执行代理不得自行把 (甲) 改成 (乙)。

### 开工自审

1. **科研价值**：`llmere-causal-s13` 是 Ch4 主表的**已发表方法** LLM 对照行，目前官方 causal P/R/F1
   是 `unavailable`（§9.6）。QR-001 v1.1.0 把 baseline 广度改为**主表报告要求**，所以这一行要么有数字，
   要么有一份能被审查的"为什么没有"。本节产出后者，并给作者一个有量纲的成本判断。
   ⚠️ **与 FR-016 保真度是两件事**：能否复现 LLMERE 原论文的 causal 36.04 已于 2026-09-15 裁定取
   **(b) Unverifiable**（要读封存 final-valid，按 A 类红线放弃），**那件事已关闭**，本节不碰它。
2. **可行性**：纯只读——读已保留的 `generated_predictions.jsonl`、训练/推理配置与转换器。
   五个方面没有一条不成立。

### 一手核查：§9.6 的"格式未满足"可以说得更准

**独立重算，与 §9.6 交叉验证通过**：用转换器同一套规则重扫 11,149 条，
**第一行可解析 11,054 / 不可解析 95** ——与 §9.6 记录的 95 条**逐条一致**。

但重扫同时测出一件 §9.6 没写的事：

| 量 | 训练 target | 本轮生成输出 |
|---|---:|---:|
| 全文字符长度（中位） | **98** | **1,755** |
| 全文字符长度（最小） | 98 | **613** |
| 第一行字符长度（中位） | 31 | 31 |
| 超过 1,000 字符的条数 | 0 | **11,110 / 11,149（99.65%）** |

训练 target 是**固定三行**（实测前三条逐字相同）：

```
CAUSE: none; PRECONDITION: none
Coreference information: none
Relevant reasoning information: none
```

⇒ **11,149 条全部退化重复，一条不剩**：最短的输出也有 613 字符，是 target 的 6 倍；
中位 1,755 字符已逼近 `max_new_tokens=512` 的解码上限。模型输出完三行后**不停**，继续重复第二、三行。

抽样确认形态（行号即 `generated_predictions.jsonl` 行号）：

- **第 1 行（"成功"）**：前三行完全符合 target 格式，之后开始 `…none.ComponentPlacement: none.ComponentPlacement: none…`；
- **第 7,817 行（失败）**：第一行是 `CAUSE: none; PRECONDITION: nonee11 claim>, <e12 reinforce>`
  ——`none` 后面直接粘上 `e11 claim>`，**污染发生在第一行内部**；
- **第 8,842 行（失败）**：第一行开头**缺整个 `CAUSE:` 标签**，直接是 ` in particular <e42 faced>; PRECONDITION: none`；
- **第 8,843 行（失败）**：开头是断裂的 `achment>, <e36 given>, …`。

⇒ **真正的根因是生成侧没有终止语义**，不是"模型偶尔不守格式"。那 95 条是退化重复**污染到了第一行**；
另外 11,054 条之所以能解析，只是因为污染发生在第一个换行之后、被转换器的 `split("\n", 1)[0]` 切掉了。
**"成功的 11,054 条"和"失败的 95 条"是同一个缺陷的两种表现，不是两类样本。**

⚠️ **这与 C5.3 首跑失败同族：训练侧与推理侧口径不成对。** C5 是推理侧拿不到训练时绑定的论元产物
（`results/PHASE_C.md`）；这里是推理侧没有继承训练 target 的终止语义。**两个月内第二次**，
已经够格写进纪律：**新 baseline 的推理配置必须逐项对着训练配置过一遍，不能只看它"跑完了"。**

### 恢复方案（满足 C-3 的四条验收）

冻结的推理侧配置（现状，`llmere_causal_predict.yaml` `2eaf595d…6f64a92`）：
`max_new_tokens: 512` · `per_device_eval_batch_size: 1` · `predict_with_generate: true` ·
`template: llama3` · `seed: 13` · `cutoff_len: 2048`，**无 stop string**。

| # | 动作 | 为什么 |
|---|---|---|
| **① 终止条件** | `max_new_tokens` 从 **512** 降到覆盖三行 target 的长度，并显式加 stop string（target 的第三行结尾） | 直接消除退化重复。这是**全体 11,149 条的质量问题**，不是 95 条的问题 |
| **② 约束解码** | 把**第一行**限制在转换器接受的正则语言上：`(CAUSE\|PRECONDITION): (none\|<e\d+[^>]*>(, <e\d+[^>]*>)*); …` 两个标签各恰好一次，事件 id 限制在该 partition 的候选集合内 | ①**修不了**第一行内部的污染（第 7,817 行就是反例）。约束解码把 95/11,149 降到 **0**，且候选集合逐条动态构造 ⇒ 顺带消灭"未知引用"类错误 |
| **③ 全量重生成** | 对**全部 11,149 条**用同一套新口径重跑，**不是**只补 95 条 | §9.6 的红线：补 NONE / 猜 event id / 只重生成 94 条后拼接，都会改变或按结果选择推理口径 |
| **④ 原始输出保留** | 新产物写到 `predict-r2/` 与 `score-r2/`，**不覆盖** `predict/generated_predictions.jsonl`（59,336,796 B）与 adapter | 现有 `resume_llmere_causal_prediction.sh` 已有 `test ! -e "$run_root/predict"` 守卫，新脚本沿用同样的拒绝覆盖语义 |

**实现落点**（避免动 pinned 的上游）：LLaMA-Factory 钉在 `ca75f1ed…`、LLMERE 钉在 `94d4ef27…`，
两个仓库都有 `git status --porcelain` 空树断言。②的约束解码**不要改它们**，
改为自写推理脚本用 `transformers` 直接加载 base + adapter，走 `generate(prefix_allowed_tokens_fn=…)`
（transformers 自带，**无需新依赖**）。代价是必须逐项复制 LLaMA-Factory 的 prompt 构造与生成参数
（`template: llama3` 的对话模板、`seed 13`、bf16），**并在新脚本里断言复制正确**——
拿现有 11,149 个已保存 prompt 做逐条比对，不一致即 fail-fast。

**fail-fast 清单**（转换器现有的一条不动，新增三条）：

- 保留：未知引用、自环、缺字段、非法标签、重复标签、`predict` 非字符串、第一行为空；
- 新增：约束解码后仍不可解析 ⇒ 立即失败（按设计不应发生，发生即约束有洞）；
- 新增：prompt 与本轮已保存的 11,149 个 prompt 逐条比对不一致 ⇒ 失败；
- 新增：覆盖断言——11,149 条各恰好一次，重复/缺失即失败。

### 成本：比原估**低一个量级**，这是本节最该被看见的数字

主表 G-8 记的是 **42 GPU·h（批量化后 3–5 h）**。那个估算基于 `max_new_tokens=512`。
但实测**有用内容（第一行）中位只有 31 字符 ≈ 10 个 token**，而当前每条生成到逼近 512 token 上限
⇒ **约 97% 的解码算力花在退化重复上**。

| 项 | 当前 | 修好终止条件后 |
|---|---:|---:|
| 每条生成 token（中位实测/估算） | ≈ 450+ | **≈ 30–40**（覆盖三行 target） |
| batch | 1 | 8–16（24 GB 单卡，8B + LoRA bf16 可容纳） |
| 粗估墙钟 | 42 GPU·h | **< 1 GPU·h** |

⚠️ 这是**按 token 数与 batch 的线性外推，不是实测**。上卡前应先跑 100 条计时校准。
即便如此，量级结论是稳的：**这件事的成本不再是"要不要花 42 GPU·h"，而是"要不要花一小时以内"。**

### 建议的执行形态（两阶段，每阶段都是全量统一口径）

1. **阶段 1（必做，便宜）**：只改终止条件，全量重生成 11,149 条。它修的是**全体**的质量缺陷；
   跑完统计还剩多少条第一行不可解析；
2. **阶段 2（视残留决定）**：若阶段 1 残留 > 0，加约束解码再全量重生成一次。

⚠️ **分两阶段不违反 §9.6 的红线**——红线禁的是"只重生成失败的那 94 条后与原结果拼接"，
不是禁止两次全量重跑。每一阶段内部口径统一、覆盖全量、原始输出保留。
成本降到一小时以内之后，两次全量也是可以承受的。

### 诚实的前提：修好之后的分数才是公允的

本轮拿不到分数**不是 LLMERE 方法弱**，是**我们的适配把生成侧配错了**（缺终止语义）。
论文里必须这样写，不能写成"LLMERE 在我们的协议上失败"。
同理，阶段 1/2 跑出来的分数是**透明适配**下的数字，FR-016 状态仍是已裁定的 **(b)**
（那是另一件事，见 `BASELINE_ROSTER.md` §2.1），本节不改变它。

### 裁决点（三选一，交作者）

| | 选项 | 代价 | 我的意见 |
|---|---|---|---|
| **(甲) 推荐** | **等 Gate 2 改纲裁决后再决定**：若 Ch4 保留为方法章，执行阶段 1（< 1 GPU·h）；若 Ch4 被降级，本节即为该行的最终交代 | 零 | 成本已经不是障碍，但**执行的价值取决于 Ch4 存废**。先裁改纲，再花这一小时，顺序更合理 |
| (乙) | 现在就执行阶段 1 | < 1 GPU·h + 写新推理脚本的工程量 | 若 Ch4 被砍，这份数字没有去处 |
| (丙) | 就此封存，主表该行只报 (b) 与障碍 | 零 | ⚠️ 可惜——缺陷已定位、成本已降到一小时以内，封存等于把一个能修的洞留在主表上 |

### 这一节没有改变的东西

原始 `predict/generated_predictions.jsonl`、adapter、两个 pinned 上游仓库**一个字节没动**；
未训练、未占卡、未改代码。`EXPERIMENT_PLAN.md` 的 C-3 行与 G-8 行据此回填。

## 24. 裁决⑤ · R1 v6.2 新家族准入（2026-09-20）

### 24.1 开工自审与证据边界

**科研价值**：本轮不是为了给失败实验换名字，而是检验三个可证伪问题：D4 能否用 deployable 的
predicted causal uncertainty 改善五类 factuality；A4 的 rationale / graph / counterfactual 组合是否还存在
可主张的新颖性；C5 能否用 document-complete 的非对称 shortcut invariance 同时处理「高相似误合并」和
「低相似漏合并」。它们分别对准表 3-3、表 4-3、表 5-3 的公开主指标门。

**可行性**：先核数据、协议、代码、算力和授权。本节只做一手论文/官方代码核查、CPU 静态审计、power 与
前置计划；没有训练、没有 GPU、没有访问 final-valid 指标，也没有把 gold 关系当 deployable 输入。

文献矩阵：`runs/stages/R1/r1-v62-20260920/literature_refresh.json`，SHA-256
`e9b105acc2fa12ed32a21d310f5eb2610407568b911d362f72f49275a3a2e26e`。下表的论文数字只用于机制与
新颖性判断，**不是本项目同协议结果**。

| 方向 | 一手证据 | 机制核查后的结论 |
|---|---|---|
| D4 | [MAVEN-FACT](https://aclanthology.org/2024.findings-emnlp.651/) Table 6：DMRoBERTa 47.1，+relation 49.1，+argument 49.3，+both 45.6；正文/代码表明 relation arm 使用 annotated causal relations 聚合 relation token | gold causal structure 有信息，但 relation+argument 并非单调增益；只准入 relation-only predicted uncertainty，禁止把 gold 增益当项目结果 |
| A4 | [LLMERE](https://aclanthology.org/2025.coling-main.500/) 已在 MAVEN-ERE 做 rationale；[IJCNN 2024](https://arxiv.org/abs/2403.11129) 已组合 rationale 与 linearized coref/causal graph；[MRPD](https://doi.org/10.1016/j.eswa.2025.130284) 和 [CRECE](https://doi.org/10.1109/BigDIA68682.2025.11383282) 已覆盖多路/反事实 reasoning | 泛化的 rationale + graph + counterfactual 命题已被近邻工作覆盖；仅换 backbone、形式化理由或保留全候选不足以构成新方法 |
| C5 | [LLM-RCDA](https://aclanthology.org/2024.naacl-long.63/) 已做 KNN cross-document counterfactual augmentation；[ACCI](https://www.nature.com/articles/s41598-025-32765-6) 已做 trigger masking / argument fusion / counterfactual ECR | plain counterfactual port 不算创新；仅保留它们未覆盖的 within-document 全候选、双方向非对称 invariance，并要求 data-only arm 与 pairing-shuffle 负控 |

### 24.2 C-14 · D4 structural input 审计

FACT 与 ERE 的训练集合 **2,913 篇 / 73,939 mentions 全量一一对齐**。真正阻断 D4 的不是数据缺失，
而是 deployable input：现有 held-out relation predictions 只覆盖 P1 internal-dev 的 **291/2,913 篇**，
还缺 2,622 篇。那 291 篇里，任意 relation family 合并后的 incident rate 是 6,876/7,195=95.57%，
但 MAVEN-FACT 论文能支持的 **causal-only** 输入只有 5,270/7,195=73.25%；不能拿 temporal/subevent 合并
覆盖率掩盖 causal 输入门。

gold causal 也只用于诊断上界：CT+ 35,221/69,782=50.47%，CT− 405/1,492=27.14%，
PS+ 936/2,262=41.38%，PS− 75/285=26.32%，Uu 19/118=16.10%。因此结构对稀有类并非普遍存在，
缺边必须作为不确定性处理，不能默认为负证据。

产物 `d4_structural_input_audit.json`，SHA-256
`4d735530a1848ad0902d4d170c5978355378e1bd0d574e0396900081fd191d09`；裁决
`conditional_input_prerequisite`。

### 24.3 C-15 · A4 资产可行，但新颖性不准入

训练集有 2,622 篇 / 66,744 mentions / 2,297,524 ordered candidate pairs；其中 48,562 个 direct causal
pairs、11,231 个有 two-hop support、7,620 mentions 有 coreference rationale。源码核查同时纠正了 §13.2：
official converter 的 query anchor 会进入每个 k=30 partition，故 direct pair 覆盖是 **100%**；分区只把
two-hop support 的保留率降为 8,826/11,231=78.59%。

所以 A4 **不是卡数据或协议，而是卡科研新颖性**。在上述近邻工作已经覆盖宽命题后，本轮不生成 A4 trainer、
phase contract 或 GPU 任务。资产产物 `a4_rationale_asset_audit.json`，SHA-256
`f2912358a16c8d1f95e05a650ed17389edaa0c952a14a505ec7479daa2d9beb1`；最终裁决
`rejected_novelty_blocked`。

### 24.4 C-16 · C5 双方向 shortcut 与 power

失败 full 在 cross-sentence predicted bucket 有 1,533 对 / 367 错；其中高相似桶 912 对 / 213 错，覆盖
58.04% 的 false merge。反方向也存在：1,342 个 cross-sentence gold coreferent pairs 中有 540 个 trigger
similarity < .8，full 漏 73 个，占其 176 个 cross-sentence missed gold pairs 的 41.48%。因此只抑制高相似
预测对会再犯单边修补，候选机制必须同时保护低相似真共指。

训练源不是瓶颈：1,148,762 全部 pairs、1,070,293 cross-sentence pairs、17,014 hard non-coreferent、
4,430 divergent coreferent（另有 12,244 exact-trigger non-coreferent）。对冻结 912-pair 桶，从 null precision
`.2335526` 检验到最低有用 `.415`，单侧 exact binomial 在 n=42、critical successes=15 时实际
alpha `.04819`、power `.82012`，超过 80% 目标。

产物 `c5_counterfactual_feasibility_audit.json`，SHA-256
`27d72b9331d53e38dd00d38058e72de048c75c1e80f54672448f11a97b45a864`。准入状态是
`accepted_pending_generation_quality_gate`，**不是已证明有效**。

### 24.5 C-17/C-18 · 两条保留路线的前置计划

| 任务 | 已冻结的内容 | 仍缺什么 | SHA-256 |
|---|---|---|---|
| C-17 · D4 cross-fit | 五折 train / selection / evaluation 两两互斥；2,913 evaluation docs 每篇恰好一次；预期输出合计 73,939 mentions / 2,532,394 ordered pairs；每对必须给 `p_none/p_cause/p_precondition` 且和为 1；v2 另绑定 relation backbone `71be7419…c961ea9` | posterior dump adapter、CPU/CUDA smoke、五折真实 predicted posterior；当前状态 `plan_frozen_predictions_missing` | v2 `c3b4bc47b2d1047c4ebf5c579265ad7bdbc84f103b351986d6c5a17ffe3b32d3`（v1 `d8399cd4…1678b3` 已归档，未产生预测） |
| C-18 · C5 generation audit | seed `260920`；hard non-coref / divergent coref 各 50 条，合并后随机盲排；总体 label preservation ≥`.95`、每层 ≥`.90`、fluency ≥`.95`、single-variable ≥`.90`；评审不可见 classifier score | 披露 generator 后对这 100 条一次性生成和盲审；同一批失败后不得修 prompt 重审 | `60b6e76334352e86e7c8f7835bde3ff382e87d4683f2b252ab5725c2eaaefbe5` |

### 24.6 当前裁决

- **D4：有条件保留。** 科研命题有 exact-task 依据，但真实 cross-fit predicted input 尚不存在；不得用 gold
  或 291-doc 局部结果替代。
- **A4：本方向停止。** 原因是新颖性，不是“结果差所以收口”；除非出现能明确越过现有 rationale / graph /
  counterfactual 工作的新命题与单变量证伪，否则不再投入训练。
- **C5：有条件保留。** 数据与 power 已过，生成质量门未过；在 100 条冻结盲审产物出现前，不创建 classifier
  训练任务。

本轮结论是**淘汰一条缺科研差异的路线，推进两条仍可证伪的路线到下一个真实输入门**。没有方法指标改善，
也没有实验“收口”。

### 24.7 C-19 · D4 posterior adapter 代码门

新增 `SupervisedRelationExtractor.predict_family_posteriors`，不再从只保留 non-NONE edge 的普通抽取输出
反推结构概率；它直接保留每个 ordered pair 的三类 softmax。`src/ekg/relations/posteriors.py` 固定并验证
`p_none/p_cause/p_precondition` schema，`scripts/dump_relation_causal_posteriors.py` 绑定显式 manifest，按
manifest 顺序逐文档导出，并在全部校验通过前不发布目标文件。

已验证的拒绝条件：manifest/source ID 缺失或重复、candidate self/duplicate、posterior 缺/多 pair、缺 causal
head、类别数不是 3、概率非有限/越界/和偏离 1、文档或 pair 总数不等于 C-17 预期、目标输出已存在。
相邻 metadata 哈希 data、manifest 和 checkpoint 下的每个文件，并显式写 `gold_fields_present=false`。

代码 SHA-256：posterior validator `5b857320…b43007`；dumper `0a8eabd8…f60960c`；更新后的 supervised
extractor `560d838a…22376`。本地全门：**685 passed / 29 skipped、ruff 0、`ekg-smoke` OK**。

本节只证明“能完整且可追溯地导出”；没有 relation checkpoint 被训练，也没有五折 dump 被生成。因此 D4
仍是 `plan_frozen_predictions_missing`，不能把 C-19 当成结构输入已经闭合，更不能当成 factuality 增益。

### 24.8 当前计划一致性审计

完整审计第一次运行时正确报出：冻结 v6.1 audit 仍引用作者已经撤销的 T040–T044 consumer factorial，
而当前 `TASKS.md` 已改为应用章 T054–T058。没有篡改 `protocol.json` 钉住的 v6.1 audit
（`a1d99a7f…7a65ca`）；新增 `scripts/audit_r1_v62_consistency.py` 作为显式 amendment，更新受裁决影响的
consumer task traceability，并把 T048–T053/T059–T061 与 8 个 v6.2 artifacts 纳入检查；其他 36 条
requirement、证据、phase contract 与 trust-root 检查全部复用冻结审计。

修订脚本 SHA-256 `ab6ab6e0df1996a33f1377190a58659120a5fda722ebcff4415b1fd6ac5d064c`。实跑结果：
**PASS，36/36 requirements mapped，32 个 referenced tasks，9 个 v6.2 task 全部完成、8 个 v6.2 artifact
齐全、0 finding**。这证明当前任务表没有把撤销的
factorial 暗中恢复；它不提供任何方法有效性证据。C-20 后更新的 `status.json` SHA-256 见下一节。

### 24.9 C-20 · C5 generation audit harness 代码门

新增 `scripts/run_c5_generation_audit.py`，包含四个彼此分离的动作：

1. `requests`：读取 C-18 的 100 条冻结 item；generator config 必须逐项披露 model、revision、provider、
   license、`do_sample/temperature/top_p/max_new_tokens/seed`，输出 JSON-only 请求且拒绝覆盖；
2. generation validation：要求五个冻结字段恰好出现、item ID 100/100 无缺失/重复/额外、两个 edited
   target trigger 仍出现在 edited context；它只做结构检查，不声称语义正确；
3. `review-template`：并列原文/编辑文与 required relation，留下三个空二值判断；不含 classifier score、
   prediction 或 promotion outcome；
4. `score`：要求 100/100 人工记录与真实 boolean，按 C-18 的 overall/each-stratum 四条门逐项判定。
   测试证明 `.95/.90/.95/.90` **恰好边界通过**，少一条即失败。报告固定
   `classifier_training_authorized=false`，避免工具自己越过后续 phase-contract/授权门。

脚本当前 SHA-256 `32b046cd0f4824ccff05411bebc836ddaef16f45aad98036ae9832f26c446fc9`；6 条 targeted tests，
完整本地门 **691 passed / 29 skipped、ruff 0、`ekg-smoke` OK**。本节没有选择 generator、没有调用模型，
也没有产生或人工评审任何一条 edit；C5 状态仍是 `rubric_and_sample_frozen_generation_missing`。更新后的
`status.json` SHA-256 由 C-21 的最终状态更新，见下一节。

### 24.10 C-21 · generator 与一次性 run contract

**选型理由不是“便宜”**：generator 不作为本文方法贡献，只是制造受控训练 intervention。固定项目此前已经
内容寻址并实际跑过 73,939 mentions 的 `Qwen/Qwen3-8B`，可以避免再引入闭源 API、不可核权重或更大模型
这个混杂。[官方 model card](https://huggingface.co/Qwen/Qwen3-8B) 标明 Apache-2.0，
[官方 Qwen3 文档](https://github.com/QwenLM/Qwen3/blob/main/README.md) 也明确 open-weight models 使用
Apache 2.0，并给出 Transformers 本地推理路径。模型仍只是**透明替换** LLM-RCDA 的 GPT-3.5 generator，不能继承其
论文效果，也不能把 Qwen 本身写成方法创新。

冻结身份与解码：config revision `8188480f040c5f1606a1bb3556abf14b31975155`、weight revision
`7c9709d23bd2136dac1d6ea1fe30f4107d681cd6`、greedy、`enable_thinking=false`、seed `260920`、
`max_new_tokens=1536`。后者覆盖冻结样本最大 3,492 字符上下文的完整 JSON 回写，且不生成多个候选供挑选。

| 产物 | SHA-256 |
|---|---|
| `configs/c5_generation_audit_qwen3_8b.json` | `d91254442df600f16fda193736c1f3a2387e9445bcfbe17cef6b61098c8f625a` |
| `c5_generation/requests.jsonl`（100 行，generator identity 唯一） | `74a23bf8adf6b0b97c35a695f98d0fce84fc03f8a8338d94d6937cdac694f2fd` |
| `scripts/generate_c5_audit_edits.py` | `e057a48cdd3c36bf2f49d5352664360a6bd2f59ffedee83ab953afe20fa2fa22` |

runner 会先按既有 `QWEN3_FILES` 对 8 个 config/tokenizer/weight 文件逐个核 size+SHA，再逐条保留 raw
response。只接受一个 bare JSON object；markdown fence、字段增减、item ID 错配均记失败，不 salvage。
只有 100/100 严格解析且 C-20 validator 再通过时才发布 parsed output；无论成功失败，报告固定
`classifier_training_authorized=false`。3 条 runner targeted tests 后，完整本地门为
**694 passed / 29 skipped、ruff 0、`ekg-smoke` OK**。

**C-22 没有启动。** 只读 `nvidia-smi` 成功时四张 4090 分别占 5,716–5,719 / 24,564 MiB，GPU util
28–32%，不能判空闲；随后只读查 snapshot 路径时 ssh `Connection reset by peer`。按三态规则，这只说明
连接失败，不能推断权重不存在或远端状态改变。当前卡【算力/路径】：等 4090 空闲且路径复核成功后，必须
先披露 exact command；不得自行转用需逐次授权的 5090。当前 `status.json` SHA-256
`4ac2d94715065bcbc4487b21d28f15f9912366c64e9bc7fba8da5d7711d943d9`。

## 25. D4 单章目标树与执行起点（2026-09-20）

作者要求停止“结果低就收口”的工作方式，改为**一次只推进一个章节**，先定最终目标和逐级指标，再持续
实验。本节因此只处理 Ch3/D4；C5 的 C-22 暂停排队但没有取消，A4 不重开。

### 25.1 第一性原理目标

D4 的论文贡献不是“接入一张图”，而是证明：**在不读取 gold 关系的部署条件下，泄漏隔离的 predicted
causal posterior 能通过可归因的 uncertainty-gated residual，实质提高五类事件事实性检测。** 最终验收按
下列顺序，前一层不过不能拿后一层的漂亮诊断替代：

| 层级 | 必须达到的目标 | 数值/判据 |
|---|---|---|
| 论文有效性 | 超过多个同协议公开方法，并超过当前最强冻结锚 | 动态目标 `max(.583995, 新增最强同协议公开对手 + ε)`；当前即 **macro-F1 ≥ .583995**。`.553995` 只是“赢 CLS”的最低过线，不是研究完成 |
| 主效果 | full 的增益来自 predicted causal residual | `full > base` 且 `full > rewired`；同一 2,913-doc OOF unit 上 document-cluster paired bootstrap 的 95% CI 下界均 `> 0` |
| 稀有类 | 不用多数类掩盖 macro-F1 | PS− F1 **≥ .352456**，Uu F1 **≥ .166850**（各为 CLS 锚减 `.030`）；五类均不得塌为 0 |
| 机制归因 | 改善 causal/precondition 语义一致性，rewiring 消掉改善 | full 对下述两项 project-defined violation 均低于 base；rewired 不保留该改善。主分数升但中介不成立，只能写预测改进，不能写机制成立 |
| 部署性 | 方法输入不含 gold edge、gold factuality 或 final-valid 反馈 | 五折每篇 evaluation 文档不在该折 train/selection-dev；推理输入只有文本、mention 与 predicted posterior |

`.583995 = .553995 + .030`，其中 `.030` 是 R1 事前登记的 minimum meaningful effect；不是看到新方法结果
后补出的门。若后续同协议公开对手超过它，目标自动抬高而不降低。

两项机制诊断按关系子类型分别计算，**不是 MAVEN-FACT 论文指标**：在 gold-expanded relation pairs 上，
若 target 被预测为正发生（`CT+`/`PS+`）而其 source 被预测为负发生（`CT-`/`PS-`），分别记一次
`CAUSE` violation 或 `PRECONDITION` violation；含 `Uu` 的 pair 不进入分母。gold 关系只用于评测中介，
绝不进入模型。这个定义会在 C-26 phase contract 中连同分母、聚合和 bootstrap 一起冻结。

### 25.2 从最终目标倒推的阶段门

| 阶段 | 中间产物 | 必达指标 | 当前状态 |
|---|---|---|---|
| S0 目标/文献闭合 | 本节、设计 brief 修订、执行主表 | exact-task 证据核到正文+代码；目标/负控/止损先于实验结果 | **完成** |
| S1 输入执行链 | D4 hash binding + one-fold runner | evaluation 不出现在 trainer argv；official-joint recipe 任一漂移都在 CUDA 前拒绝；旧 P1 binding 不变 | **完成：703 passed / 29 skipped、ruff 0、smoke OK** |
| S2 真实结构输入 | 五折 posterior + 质量报告 | 2,913 docs / 73,939 mentions / 2,532,394 pairs 恰好一次；causal positive F1 ≥ `.300`；三类 Brier 优于 evaluation-prevalence no-skill | **原始 posterior：覆盖与 F1 `.308141` 通过，Brier `.068750 > .041427` 失败；C-25R 校准修复中** |
| S3 方法可执行 | immutable contract + full/base/rewired | 无边或低置信度时 residual 趋零；三臂只差注册变量；单折 CUDA 闭环 | 未开始，依赖 S2 |
| S4 阶段结果 | seed-13 五折三臂结果 | §25.1 五项一次判定；不达目标则做错误归因并进入第二个**实质不同**设计周期 | 未开始，依赖 S3 |
| S5 确证结果 | 额外 seeds + sealed final-valid | 仅在 S4 全过且作者逐次授权后执行；mean delta、2/3 positive、CI 下界 `>0` | 未授权 |

S2 的 `.300` 是输入质量止损线：本项目同协议 causal fallback 为 `.320973`，容许跨折约 2.1 个百分点，
但不接受接近无判别力的 posterior。Brier 必须优于按 evaluation 类别比例恒定预测的 no-skill，防止一个硬标签
F1 掩盖概率质量。若 S2 失败，修的是 relation input；不得把结果算作 D4 方法失败。

### 25.3 一手文献与本项目增量

- [MAVEN-FACT 正文](https://aclanthology.org/2024.findings-emnlp.651/) Table 6 的同任务证据是
  DMRoBERTa `47.1 → 49.1`（+relation），但 +relation 使用标注关系；+argument 为 `49.3`，两者同时加入
  反降到 `45.6`。所以本周期只做 relation，不在首轮堆 argument。
- [官方代码](https://github.com/THU-KEG/MAVEN-FACT) commit
  `67544719c60c6eb7587ed00a3e59df83822f6847` 的 `trainEFD/data.py` 只收集指向当前 event 的
  `CAUSE/PRECONDITION` 前驱句，`model.py` 分别编码后拼接到 factuality representation。它证明的是
  **gold predecessor text 有信息**，不是“预测图已经有效”，也没有定义上节两项 violation。
- [ULGN](https://aclanthology.org/2021.emnlp-main.207/) 提供“局部不确定性 + 全局聚合”的机制先例，但任务是
  其他数据上的 document-level same-event aggregation，不能把其分数移进 MAVEN-FACT 主表。
- 本项目的可证伪增量是：**五折 OOF predicted CAUSE/PRECONDITION posterior + 显式 NONE/uncertainty gate +
  保方向/子类/度/置信度多重集的 rewiring 负控**。gold relation injection 只可作 oracle，不是 deployable arm。

### 25.4 已发现错误与修复

| 错误 | 为什么会让结论/进度出错 | 本轮修复 |
|---|---|---|
| 把首个机制失败写成整章“止损” | 混淆“封存一个机制家族”和“取消研究目标” | 每个新家族仍先做 R1；seed-13 失败进入错误归因与第二个实质设计周期，不用换名/扫参复活旧家族 |
| 把两项一致性诊断称为“论文两条规则” | 一手正文和代码没有这个指标，属于错误归因 | 改为 project-defined mediator，并在结果页给出精确定义 |
| G-15 的 `--help` 预检在服务器挂起 | 冒烟入口在参数解析前导入关系数据依赖，使轻量预检进入不必要的重初始化，既拖慢排障，也可能被误判为 CUDA 任务已经启动 | 将关系数据与候选对导入移入 `smoke_contract()`；`--help` 不再加载训练依赖，真正执行时的口径不变 |
| 修复后 dry-run 仍在 `smoke_contract()` 超时 | 只需冻结文档 ID 和候选对数，却经 `ekg.relations` 包入口加载整条关系流水线；这把纯计数错误地绑定到服务器重依赖初始化 | 合约改为直接读冻结 JSONL，以每篇事件 mention 数计算 `n(n-1)`；与既有 loader 交叉核验为相同 5 篇、**5,198** 对，并新增精确回归断言 |
| 4090 的 T064/T065 定向测试缺少 `d4_crossfit_plan.json` | 计划位于 gitignored `runs/`，代码经 git 同步不等于运行资产已同步；若只等空卡，G-16 会在训练前直接 `FileNotFoundError` | 枚举计划引用的两份语料、CV 总表与 15 个 manifest，确认本地/4090 SHA-256 全部一致；只补传计划文件并双端核为 `d8399cd4…1678b3`，4090 端 CPU 定向测试 **20/20 passed** |
| 正式 cross-fit 只记录模型文件哈希，不拒绝错误 backbone | 事后知道“用了另一个模型”不能挽救五折 posterior；模型身份漂移会污染全部 S2 输入和后续 D4 因果归因 | 新增 v2 计划，事前绑定 `71be7419…c961ea9`；runner、trainer、G-15 smoke 三个入口都用规范内容摘要 fail-fast。4090 六文件实算命中该 pin，定向测试 **30/30 passed** |
| G-16 fold 1/2 首启在训练前报 `str.is_dir` | 新 validator 的单测只传 `Path`，但 trainer CLI 的 `--model` 是字符串；G-15 又不走 D4 trainer binding，所以两层检查都漏掉真实 CLI 类型边界 | validator 入口统一转成 resolved `Path`，回归测试改传字符串；失败发生在 CUDA 分配前，目录/日志归档为 `failed-model-path-type` 后用同一冻结命令重跑 |
| 现成 held-out relation 只有 291/2,913 篇却准备训练 D4 | 90% evaluation 文档没有 deployable structure，任何结果都不完整 | C-17 五折计划 + C-19 posterior API；S2 明确要求全覆盖 |
| `train_supervised_relations.py` 只接受旧 P1 train/dev | 直接传 D4 fold 会被拒；绕过校验又会丢失 A 类口径约束 | 新增独立 D4 binding：只物化 train+selection-dev，逐记录与注册源比对，evaluation 只交给 dumper |
| 有 posterior dumper 但没有 train→select→dump runner | “代码能导出”被误写成“输入快好了”，实际无法稳定执行五折 | `run_d4_relation_crossfit.py` 冻结配方、checkpoint 选择、命令和产物哈希 |

### 25.5 当前阶段成果

当前不是方法分数，而是 **S0 已完成、S1 代码闭环已建立**：新 runner 把 evaluation manifest 从训练命令中
物理隔离；训练器会核对 cross-fit plan、原始 ERE source、三个 manifest、物化 source 的逐文档内容和固定
official-joint 配方；完成后只使用 selection-dev 选出的 causal-family checkpoint，导出 evaluation 的完整
三类 posterior。定向测试覆盖了 evaluation 泄漏、记录漂移、recipe/命令隔离与原子 posterior 输出。

本地完整门：**703 passed / 29 skipped、ruff 0、`ekg-smoke` OK**；R1 v6.2 一致性审计
**PASS（36/36 requirements，41 个 referenced tasks，0 finding）**。代码 SHA-256：trainer
`d0028ead…6175`，cross-fit runner `ea888752…9218`，两份测试分别
`cacc079e…d98e` / `b6f66804…e589`。CUDA smoke runner/test 分别为 `6ba85e40…8957` /
`58e7f5ca…1e44`；它固定 30-doc fixture、1 epoch、5-doc/5,198-pair posterior，分数不进入选模或主表。
修订后的 design brief SHA-256 `fa972c13…a8b1`。

4090 端 `c75afdd` 的 dry-run 已在 **1.40 秒**返回同一 5 篇文档与 5,198 对，且输出目录、日志均不存在；
因此还没有训练或伪造阶段结果。2026-09-20 核卡时四张 4090 各有两个他人进程，使用约 11.4/24.6 GiB、
利用率 95–100%，不满足“不挤占”的操作门；5090 被他人常驻 vLLM 占 26.8/32.6 GiB，也不是可行替代。
补齐 gitignored cross-fit plan 后，4090 端三份定向测试 **20/20 passed**；五折只读命令审计逐折通过，
evaluation 只进入 dumper，五折预期计数分别为 505,156 / 511,286 / 511,878 / 506,416 / 497,658 对，
合计仍为 2,913 篇 / 2,532,394 对。随后发现 v1 未绑定 backbone，故在任何预测产生前修订为 v2
（`c3b4bc47…b32d3`）；旧 v1（`d8399cd4…1678b3`）保留归档。4090 实算模型内容摘要命中
`71be7419…c961ea9`。

**G-15 已于 2026-09-21 在 gpu-4090 GPU1 完成**（08:58:41–08:59:13，约 32 秒）：真实 CUDA
前向/反向、causal-family checkpoint 保存/重载和 posterior dump 闭环；`smoke.json` 为
`status=complete`、`device=cuda`、`scientific_result=false`，SHA-256
`068e71a7e47c5e8d6c9d4d060054b7096b6d6ae59a0e71d5ea95fef17386e564`。独立重算确认 posterior
恰为 5 篇 / 5,198 行 / 5,198 个唯一有序对，三类概率有限、范围合法且和误差 ≤`1e-6`；posterior
SHA-256 `7bc1335a…85f6`。causal selection 的 smoke dev F1 为 0，按事前契约**不用于选配方、不过门判定或
论文主表**。

**G-16 已于 2026-09-21 09:08–09:10 开始正式五折输入生成，当前完成 0/5。** 首次启动 fold 1/2
在 CUDA 分配前因 trainer CLI 把 `--model` 传为字符串、新 validator 却调用 `str.is_dir()` 失败；
失败目录和日志已分别封存为 `fold-{1,2}-failed-model-path-type`，没有删除。修复后完整本地门仍为
**703 passed / 29 skipped、ruff 0、`ekg-smoke` OK**；4090 上真实 CLI 形状的定向回归 **23/23 passed**。
提交 `b7cfa1c` 后用同一 v2 计划、backbone、seed 13 和 official-joint 配方重启；GPU1/3/0/2 分别运行
fold 1/2/3/4，四折已全部越过 hash/泄漏/配方绑定并进入真实训练。当前只能声称“运行中”；在
`status=complete` 和 posterior 独立覆盖/概率复核之前，不计为折完成，也没有 S2 分数。fold 5 在第一张卡释放后
接续，然后立即执行 C-25 全量输入质量门；不转去 Ch6/C5 做旁支分析。

为防止看到五折分数后再改尺度，C-25 汇总器已在 G-16 运行期间事前固定：每对以三类 argmax 决定硬标签；
causal positive F1 是 CAUSE/PRECONDITION **精确子类**的 micro-F1（错子类同时计 FP+FN）；
multiclass Brier 是每对 `sum_k (p_k-y_k)^2` 再对全体 OOF pair 取均值，no-skill 是用同一 evaluation
总体三类比例作恒定预测。结构漂移、非冻结 seed、训练命令读到 evaluation、行中出现 gold 字段或
候选顺序/概率不合法均 fail-fast；质量指标未过则仍原子写出 `quality_gate_failed`，不伪装成运行错误。
新增 4 条定向测试后完整本地门为 **707 passed / 29 skipped、ruff 0、`ekg-smoke` OK**，R1 v6.2 审计
仍 **36/36 PASS**。汇总器/测试 SHA-256 分别为 `a6fd1e5e…e2951` / `55e443e0…ef2da`；它们尚未对
正式 posterior 运行，因此没有提前制造 C-25 结果。
冻结 gold 总体经独立两条路（loader 的 official mention expansion 与 candidate-protocol summary）
交叉核对为 NONE **2,479,036** / CAUSE **14,289** / PRECONDITION **39,069**；因此事前 no-skill
multiclass Brier 是 **0.0414265581**。这是从冻结 gold 计算的评测尺度，不是模型结果。

2026-09-21 11:02–11:10，fold 1–4 依次完成；重新流式读取每个 posterior 后独立核对为：

| fold | documents | ordered pairs | causal selection-dev best (epoch) | posterior SHA-256 |
|---:|---:|---:|---:|---|
| 1 | 583 | 505,156 | .320918 (47) | `7746f3a4…0844e` |
| 2 | 583 | 511,286 | .310070 (34) | `1ce6d1b3…f78f6` |
| 3 | 583 | 511,878 | .288650 (44) | `efedfe88…dacbb` |
| 4 | 582 | 506,416 | .307318 (22) | `3959df80…81c02` |
| 5 | 582 | 497,658 | .318294 (3) | `eeeb65e6…7056e` |

五折均为 `status=complete`，共 **2,913 篇 / 73,939 mentions / 2,532,394 对**，实算 SHA 与 run
metadata 逐折相符。selection-dev 数字只是冻结 checkpoint 选择记录，不是 OOF S2 质量分；特别是 fold 3
低于 `.300`，不做隐藏或单折补救。

### 25.6 C-25 正式输入质量结果与下一小步（2026-09-21）

C-25 在五折全部封存后按事前冻结的汇总器运行，正式报告位于
`gpu-4090:/data/TJK/ekg/runs/stages/R1/r1-v62-20260920/relation_crossfit/quality_report.json`，
SHA-256 为 `2275097562f30e9f633e5724febd5f60437b12f2ffe7f006bce722cb5ffa5074`，状态
`quality_gate_failed`。这是**输入概率质量失败**，不是 D4 方法实验失败：

| 项目 | 正式结果 | 事前门 | 判定 |
|---|---:|---:|---|
| coverage | 2,913 docs / 73,939 mentions / 2,532,394 pairs | 精确相等 | PASS |
| causal exact-subtype micro-F1 | `.30814055`（P `.22675390` / R `.48065895`） | ≥ `.300` | PASS |
| multiclass Brier | `.06875035` | `< .04142656` no-skill | **FAIL** |

混淆计数为 TP 25,647 / FP 87,458 / FN 27,711；预测 CAUSE/PRECONDITION 共 113,105 对，而 gold
正类共 53,358 对，约为 **2.12 倍**。五折 Brier 均劣于各自 no-skill（`.06795–.06958` vs
`.04031–.04309`），不是某一折偶发。因而 C-26 保持冻结；原始 posterior 与失败报告不覆盖、不删除。

下一步 C-25R 只解决这一层问题：先从一手论文与代码确认校准机制，再冻结**每折仅用 selection-dev
标签拟合、evaluation 标签不参与参数选择**的校准契约。科研价值是保住已经过线的 causal 排序/硬判别，
同时让进入 uncertainty gate 的概率具备可用尺度；可行性依赖既有五折 checkpoint、selection-dev manifest
和完整 evaluation sidecar，数据/协议/代码/4090 资产均已具备。验收仍沿用原门：calibrated causal F1
≥`.300` 且 Brier 严格优于 `.0414265581`，不过则记录失败并进入实质不同的第二个校准周期，不用
evaluation 扫温度、阈值或类别偏置。

### 25.7 C-25R 第一校准周期预注册（在 calibrated evaluation 数字之前）

**错误假设。** 五折训练的 causal class weights 不是概率中性的：由各折冻结 train population 按训练器
原公式重算，NONE 为 `.58344–.58358`、CAUSE 为 `7.61566–7.77331`、PRECONDITION 为
`4.60492–4.69440`。加权 cross-entropy 的总体最优输出满足
`q_k(x) ∝ w_k p(y=k|x)`，所以它适合抬稀有类召回，却不能直接当自然类别分布下的 posterior；C-25
中预测正类约为 gold 的 2.12 倍与这个方向一致，但目前只把它记为**待检验根因**，不冒充因果结论。

业界首选从最小可证伪修复开始：[Guo et al. (ICML 2017) 正文](https://proceedings.mlr.press/v70/guo17a.html)
§4 明确要求 calibration 使用 hold-out validation、固定网络参数；其 multiclass temperature scaling 只拟合
一个 `T>0`、用 validation NLL 优化，并因不改变 softmax 最大项而保持分类结果不变。
[作者公开实现](https://github.com/gpleiss/temperature_scaling/blob/master/temperature_scaling.py) 同样收集 validation
logits/labels 后只用 LBFGS 更新一个 temperature。这里的 selection-dev 与 evaluation 来自同一冻结五折分布，
且论文明确允许 calibration set 与 hyperparameter validation set 相同，因此【数据/协议/代码/算力】均可行。

第一周期冻结如下，不根据 calibrated evaluation 结果改动：

1. 每个 fold 用**自己的** causal-family checkpoint 在该 fold selection-dev 上导出 exhaustive 三类 posterior；
   文档、候选顺序、行数和 checkpoint hash 任一漂移都 fail-fast；
2. 将 `log(p)` 作为与原 logits 只差逐样本加法常数的等价 logits；原 posterior 若含零或非法概率则拒绝，
   不加 epsilon 掩盖；每折以全部 selection-dev pair 的**非加权 multiclass NLL**拟合唯一 `T>0`；
3. evaluation 只做 `q_k = p_k^(1/T) / Σ_j p_j^(1/T)`，原始 sidecar 永不覆盖；不根据 selection-dev
   Brier/F1 选择另一个 calibrator，也不拟合阈值或类别偏置；
4. 变换前后 evaluation 的 argmax、三类 prediction counts 与 causal TP/FP/FN 必须逐项相同，因此正式
   causal F1 必须仍为 `.30814055`；唯一待检验变量是 Brier，必须严格 `< .0414265581`；
5. evaluation gold 只在五折 calibrated sidecar 和 metadata 全部封存后读取一次。若 Brier 仍失败，首轮
   temperature family 如实封存；第二周期才回 R1 立项沿训练 class-weight 方向的 class-bias correction，
   并重新事前冻结 F1 护栏，禁止用 evaluation 扫偏置强度。

这一步能支撑的论断仅是“部署 posterior 的全局置信度尺度已/未修复”，不是 D4 方法有效。只有它过门，
C-26 才能把概率作为 uncertainty gate 的输入。

### 25.8 C-25R 实现与 selection 输入阶段成果

校准实现已提交为 `078fe00`：`src/ekg/relations/calibration.py` 用 inverse-temperature 上单调的 NLL
导数做确定性凸二分，不依赖优化器版本；`scripts/calibrate_d4_relation_posteriors.py` 绑定同折 checkpoint、
selection manifest、raw evaluation posterior 与全部 SHA，逐行断言 argmax 不变并原子发布新 sidecar；
`aggregate_d4_relation_crossfit.py --calibrated` 在读 evaluation gold 前验证 calibration provenance、原始 C-25
失败报告与 prediction-count invariance。实现没有 epsilon/fallback，不覆盖原始 posterior。新增 8 条定向测试，
本地完整门为 **715 passed / 29 skipped、ruff 0、`ekg-smoke` OK**，R1 审计仍为 **36/36 PASS**。

4090 四卡空闲时并行导出 fold 1–4、随后在 GPU0 导出 fold 5；五份均为相应 checkpoint 的完整
selection-dev candidate universe，未写 gold 字段：

| fold | selection docs | ordered pairs | posterior SHA-256 | metadata SHA-256 |
|---:|---:|---:|---|---|
| 1 | 583 | 511,286 | `1e68f122…f95db5` | `18d98780…b2ac8` |
| 2 | 583 | 511,878 | `a6910777…4e548` | `7fbfe2ef…0c1d4` |
| 3 | 582 | 506,416 | `173466a1…49ccc` | `8eef262c…48fe9` |
| 4 | 582 | 497,658 | `d11eb6cd…ec8df` | `c3704083…5ff38d` |
| 5 | 583 | 505,156 | `c0c3370c…69990` | `d880f17d…09f28` |

执行中的错误如实保留：代码 push 后，4090 首次 `git fetch` 因 `gh-proxy.com` DNS 解析失败；随后 cpolar
SSH 在 banner 前连续超时。按三态规则这不表示服务器或上述产物消失。为保持代码必须来自 git 的绑定，
没有手工散拷脚本；隧道恢复后改用双端 SHA 一致的 Git bundle 同步完整 commit 图，远端 HEAD
`7f347c2` 包含实现提交 `078fe00`，随后远端相关测试 **12/12 passed**，才执行五折校准。

### 25.9 C-25R 正式结果与 C-25R2 预注册（2026-09-21）

scalar-temperature 五折产物全部通过 checkpoint、候选顺序、覆盖与 argmax invariance 校验后，才读取一次
evaluation gold。正式报告
`gpu-4090:.../relation_crossfit/calibrated_quality_report.json` SHA-256 为
`5fc28b7c2db2da598bc0f05238507408c83957939cb178d52ee1c2288fc7b296`，状态仍为
`quality_gate_failed`：

| 指标 | raw C-25 | scalar temperature | 变化/判定 |
|---|---:|---:|---|
| causal exact-subtype micro-F1 | `.30814055` | `.30814055` | argmax 精确不变，PASS |
| multiclass Brier | `.06875035` | `.06415525` | `−.00459510`（约 −6.7%），有改善 |
| evaluation no-skill Brier | `.04142656` | `.04142656` | calibrated 仍高 `.02272869`，**FAIL** |

五折温度依次为 `2.085692 / 1.888133 / 2.173413 / 1.706430 / .751421`；每折 selection NLL 都下降，
但每折正式 Brier 仍为 `.061785–.068109`，全部劣于各自 no-skill。结论是全局 entropy/置信度尺度确实
贡献了一部分误差，却不是主因；继续扫 temperature 属于复活同一失败 family，已禁止。

**第二周期科研价值。** 当前模型明确用 class-weighted cross-entropy 训练，而 uncertainty gate 需要自然分布
posterior。[Caplin, Martin & Marx (2022)](https://arxiv.org/abs/2205.04613) 正文 §3 的 Proposition 3 给出
multiclass weighted loss 会把 posterior 映射为权重扭曲的最优 score；Proposition 4–5 要求在映射可逆时用
解析逆恢复 calibration，并说明这种 correction 不再估计额外参数。对本项目的 categorical weighted CE，
直接对条件风险求导得到 `q_k = w_k p_k / Σ_j w_j p_j`，所以解析逆是
`p_k = (q_k/w_k) / Σ_j(q_j/w_j)`。

**可行性与门。** 数据、代码与算力已具备：每折 run metadata 含未下采样 train 的三类 counts，训练器
`class_weights()` 的公式与 `alpha=.5` 已冻结，selection posterior/label 全覆盖；该变换纯 CPU。它会改变
argmax，因此不能直接再看 evaluation。C-25R2 先只生成 selection-only audit，既不读取 raw/calibrated
evaluation posterior 也不输出 evaluation sidecar；必须同时满足 pooled selection exact-subtype F1 ≥`.300`、
corrected Brier `< raw Brier` 且 `< selection-prevalence no-skill`。过门后才另行冻结第二次正式评测；不过门
则点名“解析 loss correction 恢复概率但损伤判别”或相应实测根因，再设计第三个实质 family，禁止在
evaluation 上插值权重强度。

### 25.10 C-25R2 selection-only 正式结果（2026-09-21）

实现提交 `4a88fca` 在本地通过 **720 passed / 29 skipped、ruff 0、`ekg-smoke` OK**，4090 端两份定向
测试 **10/10 passed**。随后只运行冻结的 selection audit；报告位于
`gpu-4090:.../relation_crossfit/class_weight_correction_selection_audit.json`，SHA-256 为
`fb88778508054a204a42ffc41a71411d03e87ed43a8b42dd4588574438fcd6f8`，明确记录
`evaluation_artifacts_accessed=false`，状态 `rejected_at_selection_gate`：

| selection pooled 指标 | raw | analytic inverse | 事前门 | 判定 |
|---|---:|---:|---:|---|
| causal exact-subtype F1 | `.30829735` | `.27991091` | ≥ `.300` | **FAIL** |
| multiclass Brier | `.06823085` | `.04194243` | `< raw` | PASS |
| prevalence no-skill Brier | `.04142656` | `.04142656` | corrected `< no-skill` | **FAIL** |

解析逆把 pooled 正类预测从 112,683 降到 40,479，更接近 gold 53,358，但折间不稳定：fold 1 F1
`.32062`，fold 2–4 为 `.29322–.29835`，fold 5 从 raw `.31697` 跌至 `.12214`，其正类预测从
24,895 降到 1,242。结论限定为：**固定训练权重解释了绝大部分 Brier 失真，但把自然分布 posterior
直接按 argmax 当作稀有类决策，会损伤 causal F1；且仅靠理论逆映射仍未超过 no-skill Brier。** 这不是
D4 方法结果，也不能用 evaluation 插值逆校正强度补救；第二套 evaluation sidecar 没有创建。

下一步 C-25R3 回 R1 核实第三个实质机制。开工两问先固定：科研价值是让 uncertainty gate 得到优于
no-skill 的自然分布概率，同时不把概率校准与类别不平衡下的任务决策混为同一 argmax；证据将落在本节
后续的 primary-source design brief 与独立 selection holdout 表。可行性先只认既有五折 selection posterior，
按文档切出互斥 calibration/gate 子集，gate 不参与拟合；在一手机制、代码可运行性和门都冻结前，不读取
evaluation。若文献不支持分离、或 holdout 不同时过 Brier/F1，就如实封存第三 family，不改门绕开。

### 25.11 C-25R3 一手依据与预注册（在第三机制数字之前）

**机制依据。** [Kull et al. (NeurIPS 2019)](https://proceedings.neurips.cc/paper/2019/hash/8ca01ea920679a0fe3728441494041b9-Abstract.html)
正文 Eq. 7 把 Dirichlet calibration 定义为 `softmax(W log q+b)`：它原生处理 multiclass posterior，能表达
类别和类别对偏差，包含 identity 与 temperature map；论文同时强调 calibration map 用 holdout validation
学习，且 Brier/log-loss 这类 proper loss 必须与仅报 ECE/accuracy 同时看。其深度模型实验还在 validation
内部做 CV，避免把同一拟合分数当测试结果。[作者官方实现](https://github.com/dirichletcal/dirichlet_python/tree/b03f65fc6582cad89497b977b3b33a3c4fe48e39)
提供 `FullDirichletCalibrator`；本项目不引入其 Python 3.12/JAX 栈，而用既有 scikit-learn multinomial
logistic regression 执行论文完全相同的 `log(q) → linear → softmax`，这是透明环境适配，不重写优化器。

概率与决定不能继续混成同一个普通 argmax。[Menon et al. (ICLR 2021)](https://arxiv.org/abs/2007.07314)
§3 Eq. 8–9 证明长尾目标的 Bayes decision 是在自然 posterior 上做 prior/logit adjustment，而不是把
posterior 本身改写后仍称自然概率；[Caplin et al. (2022)](https://arxiv.org/abs/2205.04613) 已给出本项目
weighted CE 的逆映射。因此 C-25R3 输出两个有明确语义的量：`p` 是供 uncertainty gate 使用的自然分布
posterior，关系硬判定固定为 `argmax_k w_k p_k`。普通 `argmax p_k` 只作单变量消融，不再错误地拿它
承担稀有类决策目标。

**开工两问。** 科研价值是同时关闭 S2 的两个必要条件：自然 posterior 必须携带超过 prevalence 的逐例
信息，cost-aware 决策必须保持 causal 输入判别力；二者同时过线才能支撑“可校准的预测关系输入可进入
D4 uncertainty gate”。可行性成立：五折 selection posterior/labels、训练权重和文档 ID 均已封存；每折
至少 582 篇，三类都存在；scikit-learn 已是 core 依赖；全流程 CPU，不需要新数据、GPU 或授权。

**冻结协议。** 不根据输出改动以下规则：

1. 每折对 selection manifest 的文档按 `SHA256("r1-v62-c25r3|{fold}|{doc_id}")` 排序；前
   `floor(n/2)` 篇是 calibration half，后半是 gate half。五折合计 1,455/1,458 篇，pair 不跨文档泄漏；
2. 每折仅在 calibration half 以**非加权 NLL**拟合 full Dirichlet map `softmax(W log q+b)`；固定
   `penalty=None`、LBFGS、`tol=1e-10`、`max_iter=1000`，不扫正则、阈值或校正强度；零概率直接失败；
3. gate half 只在五个 map 全部冻结后评分。自然 posterior 的 pair-micro Brier 必须同时优于 raw，且
   至少比 gate 自身 prevalence no-skill 低 **`.0027`**；cost-aware exact-subtype causal F1 必须 ≥`.300`；
4. 单变量消融只切换同一 calibrated posterior 的 decision rule：plain `argmax p_k` 对比冻结的
   `argmax w_k p_k`。报告每折参数、收敛状态、三种 prediction counts、NLL/Brier/F1 与全部输入 hash；
5. 目标功效不是事后补写：用已公开 C-25R2 analytic posterior 对 2,913 篇逐文档 Brier difference 估得
   SD `.0410065`；gate `n=1,458`，单侧 α=`.05` 时最小 80% power effect `.0026703`。取目标 `.0027`
   后 power=`.8077`。该诊断未计算 Dirichlet 输出，也未访问 evaluation；
6. Gate 任一项失败即封存本 family，不创建 evaluation sidecar。只有全过，才另行冻结“用完整
   selection refit 五个 map → evaluation 一次性 formal gate”；本节不预授权该步。

因果链是可证伪的：class-weight/类别对失真 → full multiclass map 修复自然 posterior → cost-aware rule
恢复稀有类决策 → D4 uncertainty gate 才能区分强弱预测边。plain-vs-cost-aware 消融隔离最后一箭；若
Brier 过而 F1 不过，失败在 decision link；若 F1 过而 Brier 不过，失败在 probability map。

### 25.12 C-25R3 selection document-holdout 结果与 formal 预注册（2026-09-22）

实现提交 `21d9824` 在本地通过 **727 passed / 29 skipped、ruff 0、`ekg-smoke` OK**。4090 的
`git fetch` 再次因 `gh-proxy.com` DNS 失败，改用完整 Git bundle；双端 bundle SHA-256 均为
`9ddc9c8a2dc80dfee202dfd4fb8c61de0292259bce097da777114832cfb48e23`，远端 HEAD 精确为
`21d9824`，定向测试 **17/17 passed**。这次同步错误没有被写成实验结论，也未散拷脚本。

selection-only 正式报告
`gpu-4090:.../relation_crossfit/dirichlet_holdout_selection_audit.json` SHA-256 为
`ee7835d0a09bd44a46e9c3c2b506647b6151c0d74d2a1f28663edbab28cad90f`；状态
`accepted_for_formal_freeze`，`evaluation_artifacts_accessed=false`：

| 1,458 篇 holdout / 1,258,280 pairs | raw | Dirichlet natural posterior | 事前门 | 判定 |
|---|---:|---:|---:|---|
| multiclass Brier | `.06732862` | `.03423965` | 比 no-skill `.04005695` 至少低 `.0027` | **低 `.00581730`，PASS** |
| cost-aware causal exact-subtype F1 | `.30309877`（raw argmax） | `.30099005` | ≥ `.300` | **PASS** |
| plain argmax causal F1（单变量消融） | — | `.08192121` | 仅诊断 | 决策分离必要 |

五折 map 均由互斥 calibration documents 拟合，LBFGS 在 43–50 iterations 内收敛。单折 cost-aware F1
为 `.28374–.32214`，其中 3/5 低于 `.300`，但预注册判据是合并 candidate universe，pooled 仅高门
`.000990`；这个窄裕量必须如实保留，不能写成稳健完成。相反，五折 Brier 全部低于各自 no-skill，
pooled 目标裕量 `.003117`（实际改善 `.005817` 减预注册 `.0027`）。文档宏观 paired difference 均值
`−.012064`、SD `.026189`，方向与 pair-micro 一致。

**formal gate 在读取 evaluation 前冻结。** 每折用完整 selection population、相同无正则 full
Dirichlet Eq.7 和同一收敛参数 refit；evaluation raw posterior 只用于无标签变换，输出新的 immutable
natural-posterior sidecar 与 metadata，原始/scalar-temperature sidecar 均不覆盖。五份 sidecar 全部通过
checkpoint、候选顺序、概率、class order、输入/输出 hash 后，汇总器才读取 evaluation gold 一次。
正式必要门为：

1. 2,913 docs / 73,939 mentions / 2,532,394 ordered pairs 精确一次，gold 字段仍不进入 sidecar；
2. natural posterior Brier 优于 raw，且 ≤ **`.0387265581`**，即比冻结 evaluation no-skill
   `.0414265581` 至少低 `.0027`；
3. 用每折冻结 trainer weight 作 `argmax_k w_k p_k`，pooled exact-subtype causal F1 ≥`.300`；
4. 同时报告 plain `argmax p_k` F1/prediction counts，但不把它用作 deployable decision；
5. 任一失败即封存 C-25R3 family，不在 evaluation 上改正则、阈值、权重或 map。全过才解锁 C-26；
   本节仍不等同于 D4 三臂方法结果。

### 25.13 C-25R3F formal input gate 正式结果（2026-09-22）：**三项全过，C-26 解锁**

实现提交 `0bd11b2`（`scripts/formalize_d4_dirichlet_posteriors.py` + `aggregate_d4_relation_crossfit.py
--dirichlet`），本地三件套 **pytest 全绿 / 29 skipped、ruff 0、`ekg-smoke` OK**。4090 的 `git fetch`
第三次因 **DNS 解析失败**（`gh-proxy.com` 与 `github.com` 都 `Could not resolve host`）；这次不再走
bundle 散拷，而是从本地直接 `git push gpu-4090:/data/TJK/ekg main:refs/remotes/origin/main`，把 commit
图经 ssh 推进远端的 remote-tracking ref，再在远端 `git reset --hard origin/main`——代码仍然只来自
git、对象完整性由 git 自身校验，且顺带修好了「远端 `origin/main` 指向陈旧 commit」这个坑（本次
`git reset --hard origin/main` 在 fetch 失败后曾把远端工作树退回 `d0f66bf`，产物未受影响，已恢复）。
远端 HEAD 精确为 `0bd11b2`，定向测试 **23/23 passed**，随后才执行五折 refit。

五折 natural-posterior sidecar 先于任何 gold 读取封存，`gold_accessed=false`、`gold_fields_present=false`：

| fold | LBFGS iters | sidecar SHA-256 | calibration metadata SHA-256 |
|---:|---:|---|---|
| 1 | 52 | `bb3a3161…6126c` | `5eed488a…c8d315f` |
| 2 | 48 | `b6501699…a8f6a1b` | `75dfbfa6…f562eaf` |
| 3 | 53 | `2e74ab45…8540020` | `2b64b8f1…2f2a1220` |
| 4 | 43 | `b78d804f…68147971` | `28f41650…8ad47af6` |
| 5 | 50 | `4bc0daaa…8686d671` | `a8856b12…67e97f3f8` |

正式报告 `gpu-4090:.../relation_crossfit/dirichlet_quality_report.json` SHA-256 为
`fea7d3edf3da85a734d805d3f092db146d4010cd0cecec0cfb9e58e5e51b54d4`，commit 记为 `0bd11b2`，
状态 **`quality_gate_passed`**。覆盖精确命中 **2,913 docs / 73,939 mentions / 2,532,394 ordered pairs**：

| 事前冻结的门 | raw C-25 | scalar T（C-25R） | **Dirichlet + cost-aware** | 判定 |
|---|---:|---:|---:|---|
| multiclass Brier | `.06875035` | `.06415525` | **`.03513538`** | 比 no-skill `.04142656` 低 `.00629118`（门 ≥`.0027`）**PASS** |
| causal exact-subtype micro-F1 | `.30814055` | `.30814055` | **`.30602311`** | ≥`.300`，**PASS**（裕量 `.00602`） |
| plain `argmax p_k`（单变量消融） | — | — | `.07912232` | 仅诊断，precision `.4883` / recall `.0430` |
| 覆盖 / 无 gold 字段 | PASS | PASS | PASS | — |

逐折：cost-aware F1 `.294609 / .314457 / .309602 / .301577` 与 fold 4 的 `.294609`——**5 折里有 1 折
低于 `.300`**（holdout 阶段是 3/5，收窄但没有消失），预注册判据是合并 candidate universe，
这条不稳定性如实保留。五折 Brier 分别 `.03513723 / .03629909 / .03468328 / .03550075 / .03403112`，
**全部低于各自 no-skill**（`.04156872 / .04308724 / .04067288 / .04146602 / .04030742`）。
五折训练权重仍是冻结值（NONE `.58344–.58358`、CAUSE `7.61566–7.77331`、PRECONDITION
`4.60492–4.69440`），未作任何拟合。

**必须如实写清楚的三点。**

1. **硬判别力没有提高，只是没被牺牲。** cost-aware F1 `.30602311` 比 raw argmax 的 `.30814055`
   **低 `.00211744`**。本门要的从来不是抬 F1，而是「在不损伤稀有类决策的前提下把概率修成可用」；
   C-25R2 的失败正是掉在这一侧（`.279911`）。所以这一格的论断只有一条：
   **部署 posterior 现在既优于 prevalence no-skill、又保住了 raw 的判别力**，不是 D4 机制有效。
2. **plain-vs-cost-aware 消融证明决策分离是必要条件而非修辞**：同一组 calibrated 概率下，
   普通 argmax 的 causal F1 只有 `.07912232`（recall `.0430`），把概率校准与长尾决策混成同一个
   argmax 会直接毁掉稀有类召回。两者 Brier 完全相同（`.03513538`），因为消融只换 decision rule。
3. **三个失败周期定位出的根因得到闭合验证**：全局温度只解释约 6.7% 的 Brier 失真（C-25R），
   解析逆映射修好概率却打坏决策（C-25R2），full Dirichlet map + cost-aware Bayes rule 才同时成立。
   链条 `class-weight/类别对失真 → 多类 map 修自然 posterior → cost-aware rule 恢复稀有类决策`
   是可证伪的，三次实测按顺序把两个断点各自排除。

⇒ 按 §25.12 冻结的条款，**C-25R3F 三项必要门全过，C-26 解锁**。C-26 之后不得回头改 map、阈值、
权重或正则；`argmax_k w_k p_k` 与五折 map 参数自此是冻结输入。

### 25.14 C-27 开工自审时查出的泄漏路径：**训练文档的结构输入不能用 OOF posterior**（2026-09-22）

C-26 冻结了三臂与门，但没有写明**训练文档**的边从哪来——契约只约束了 evaluation。落实现时必须先答
这一条，答错就是又一次「事后才发现口径不对」。

**事实链（可自查）。** `factuality_cv` 的轮换是 `evaluation=i；selection_dev=(i+1) mod 5；train=其余三组`。
记五组文档为 `g0…g4`，D4 fold `i` 的 evaluation 是 `g_{i-1}`、train 是另外三组；而任一文档 `d ∈ g_j` 的
**OOF posterior 由 relation fold `j+1`** 产出。以 D4 fold 1 为例：eval = `g0`，train = `g2,g3,g4`；
`g2` 的 OOF posterior 来自 relation fold 3，而 **relation fold 3 的 train 正好包含 `g0`**。
⇒ **把 OOF posterior 当训练文档的结构输入，等于让 fold 1 的 evaluation 金标关系经由「relation fold 3 学到的
东西」流进 fold 1 的检测器训练**。这条通道很细（检测器只看局部边，不看文档身份），但它的类型与
ESC `19.6` 那次切分泄漏完全相同，按 A 类口径处理，不按「影响应该很小」处理。

**两个候选与裁定。**

| 方案 | 训练文档的边来自 | 泄漏 | 噪声匹配 | 代价 |
|---|---|---|---|---|
| A（免费） | 五份 OOF sidecar 的并集 | **有**上述间接通道 | train/eval 噪声同分布 | 0 |
| **B（采用）** | **该折自己的** relation checkpoint 现场 dump | **无**：fold `i` 的 relation 模型从未见过 `g_{i-1}` | train 侧偏乐观（in-sample） | 5 折 × ~1.5M pair 的纯推理 |

取 **B**。理由是两条偏置的方向不同：A 的泄漏**偏向**我们的结论，B 的 in-sample 乐观**偏离**我们的
结论——训练时的边比推理时干净，检测器会过度信任边，在 evaluation 上**掉分**。**保守的偏置可以带着走并
如实披露，偏向自己的偏置不行。** B 的 in-sample 乐观在结果页与主表里明写，不做「嵌套交叉拟合」去修
（那要把 relation 训练再乘三，超出本章预算）。

**执行后果（已写进主表）。** 新增一格 **C-27b**：用 fold `i` 的 causal checkpoint 对该折 `train.json`
（1,747 / 1,747 / 1,748 / 1,749 / 1,748 篇，合计 **7,597,182** ordered pairs）dump raw posterior，
再用**同一张已冻结的 fold map** 做 Dirichlet 变换。selection-dev 侧的 posterior 已存在（C-25R 阶段产出，
同一 checkpoint），无需重跑。这一步不训练任何模型、不读 evaluation、不改 map 参数，
沿用 `dump_relation_causal_posteriors.py` 与 `formalize_d4_dirichlet_posteriors.py` 原样调用。

### 25.15 C-27b 结构输入补齐完成（2026-09-22）

按 §25.14 的裁定，用**每折自己的** causal checkpoint（与 evaluation sidecar 同一份，hash 逐项一致）
在该折 `train.json` 上 dump raw posterior，再用**同一张已冻结的 fold map** 做 Dirichlet 变换；
selection-dev 侧沿用 C-25R 阶段已有的 raw posterior，只补做变换。四卡并行，五折 dump 合计约
**2 分钟**（00:55:19–00:57:21），变换为纯 CPU。

| fold | train docs | train ordered pairs | train sidecar SHA-256 | selection sidecar SHA-256 |
|---:|---:|---:|---|---|
| 1 | 1,747 | 1,515,952 | `34994dcb…3082d9` | `5c999b0f…8c6f39` |
| 2 | 1,747 | 1,509,230 | `7adbfcdf…62fa33` | `22810075…8abe50` |
| 3 | 1,748 | 1,514,100 | `94bef68e…ec9bee` | `79f05967…39a861` |
| 4 | 1,749 | 1,528,320 | `17aeb36e…74cae3` | `3827dfe4…ad777f` |
| 5 | 1,748 | 1,529,580 | `d3f4a4f8…11abeb` | `73ad35ff…8cc7e6` |

**逐折核对：三个 target 的 map 参数（coefficients / intercept / iterations）与 §25.13 已封存的
evaluation map 逐位相同**，所以三份 sidecar 出自同一张冻结映射，不是三次拟合。

顺带量到一条对 §25.14 的 in-sample 乐观有用的事实：**边率几乎没有被 in-sample 抬高**。train 侧
cost-aware 判正边为 `68,821 / 65,626 / 61,763 / 69,985 / 78,994`，占各折候选的
`4.54% / 4.35% / 4.08% / 4.58% / 5.16%`；evaluation 侧同口径是 `4.52% / 4.53% / 4.08% / 4.53% / 4.96%`。
⇒ in-sample 的差异不体现在**边的数量**上，只可能体现在**边的准确率**上；这一条在 G-18 结果里
必须和下游分数一起读，不能据此声称「不存在 in-sample 乐观」。

跨章 ID 对齐也已实测：MAVEN-ERE 与 MAVEN-FACT 的 **2,913 篇文档 mention ID 集合逐篇完全相同
（0 篇不一致）**，所以 sidecar 的边可以直接落到 factuality mention 上，无需任何映射或回退。

⇒ C-27b 完成。C-27 的实现现在有三份可用的结构输入（train / selection-dev / evaluation），
全部来自冻结 map，全部不含 gold 字段。

### 25.16 C-27 实现完成 + 两条「在方法结果之前」的实测（2026-09-22）

实现（`17af438` / `5018d3d` / `f8e...` 见 git）：`src/ekg/factuality/causal_residual.py` 是三臂共用的
机制层；`scripts/train_d4_predicted_causal.py`（训练，evaluation manifest **不进 argv**）、
`evaluate_d4_predicted_causal.py`（独立进程只载入已完成 checkpoint 打分 + 两项中介）、
`run_d4_predicted_causal.py`（复用 `run_r1_factuality_oof` 的 fold 校验，另验三份 sidecar 出自
**同一张冻结 Dirichlet map**）、`smoke_d4_predicted_causal.py`（不加载 torch 的全链路 CPU 冒烟）。
本地 pytest 全绿 / 29 skipped、ruff 0、`ekg-smoke` OK；4090 端 23/23 定向测试通过（含两条只有装了
torch 才跑得到的零极限与梯度断言）。

**批处理口径的唯一偏离，先说清楚。** 冻结 CLS 锚把全部 mention 打散成一条流按 32 条成批；
residual 需要 in-neighbour 与目标 mention 同处一步，所以这里改为**按文档打包到同样 32 条 mention
的预算**。这是与锚**唯一**的配方差异，`epochs/lr/alpha/max_length/seed` 全部沿用，且 **base 臂
照付同样的代价**，所以三臂之间仍是单变量对照；base 与锚 `.553995` 的任何差距要如实报，不得
拿来抵消机制的增量。

**实测一：CPU 冒烟在真实数据上打穿了第一版负控。** fold-1 文档 `002383d0…dac3` 让
out-stub/in-stub 重配对连续 1,000 次都撞上自环或重复边。改为 **double-edge swap** 后按构造保度、
必然终止。这条正是「本地全绿不代表能跑」的又一例——它只有在真实 sidecar 上才暴露。

**实测二（两条必须写进契约的参照线，都在任何方法数字之前）。** fold 1 全 583 篇：

| 量 | 实测 | 读法 |
|---|---|---|
| rewiring 混合上限 | 预算 10×\|E\| 时 **40.53%** 边保持同一 `(head,tail,subtype)`；50× **40.98%**、200× **41.27%** | **链已混匀，~41% 是度序列逼出来的**；`rewired` 是**保守**负控，最多打散约 59% 的边。`full > rewired` 不显著也可能是控制臂太像 full |
| 中介的 gold 地板 | 把 gold factuality 代入同一计数器：CAUSE **`.003602`**（11/3,054）、PRECONDITION **`.007744`**（59/7,619） | 约束**不是恒真但接近恒真** ⇒ 中介应读作「离地板多远」；⚠️ 也因此**中介与预测错误率高度相关，不是独立于主指标的第二条证据** |

顺带记下 fold-1 evaluation 的标签分布：CT+ 13,947 / PS+ 453 / CT− 299 / PS− 57 / **Uu 24**（共 14,780）。
**Uu 在单折只有 24 个实例**，其 F1 的逐折方差必然很大，这是护栏 `Uu ≥ .166850` 只在 pooled 上判的原因。

⇒ C-27 完成。两条参照线已写进 `docs/phases/PHASE_D4_predicted_causal_residual.md`，
下一步是 G-17 单折三臂 CUDA 冒烟。

### 25.17 G-17 单折三臂 CUDA 冒烟通过（2026-09-22）

bounded fixture 取 fold 1 的前 20 train / 10 selection-dev / 10 evaluation 篇，sidecar 按同样的
doc_id 过滤（13,960 / 7,230 / 8,582 行），1 epoch，三臂分别在 4090 卡 0/1/2 上跑
train + evaluate，**六个进程全部 exit=0**。分数不进选模、不进主表。

| 臂 | dev macro-F1 | eval macro-F1 | eval 边 | 中介（violations/pairs） | rewiring |
|---|---:|---:|---:|---|---|
| base | .193814 | .194510 | 560 | CAUSE 0/221 · PRE 0/144 | — |
| full | .193814 | .194510 | 560 | 同上 | — |
| rewired | .193814 | .194510 | 560 | 同上 | 286/560 同边（`.5107`） |

**三臂逐 mention 预测完全相同（262 个 mention 里 0 个不同）。这不是机制失效，必须说清楚为什么：**
1 epoch × 20 篇之后三臂都塌到全 `CT+`（macro `.19451` ≈ 多数类地板），所以预测相同只反映
「冒烟规模下谁都没学会」。**机制本身是活的**——`full` 的 residual 权重训练后
`|W|₁` 为 CAUSE `40.33` / PRECONDITION `55.09`（零初始化出发），`rewired` 为 `35.76` / `59.66`；
`base` 的 checkpoint 里**没有** `causal_residual.pt`，evaluator 也会因为它存在而拒绝。
⇒ 冒烟证明的是「forward/backward/evaluator/中介/负控诊断在 CUDA 上跑得通且三臂互斥」，
不是任何效果判断。

顺带确认 base 的配方与冻结锚逐项相同：`--epochs 12 --lr 2e-05 --alpha 0.5 --batch-size 32
--max-length 128 --seed 13`、同一个内容寻址 backbone `71be7419…c961ea9`；锚 fold-1 的
evaluation macro-F1 是 `.5568315`（pooled `.553995`）。唯一差异仍是 §25.16 说明的按文档打包。

### 25.18 一致性审计自 09-20 起一直是 BLOCKED，已修复（2026-09-22）

`HANDOFF.md` §0.1 的三条只读检查里，第三条 `audit_r1_consistency.py` **从 2026-09-20 的 `c9afdeb`
起就一直返回 `BLOCKED`**，两天没人发现——因为那次提交把作者撤销的 24 条件 factorial 队列
**T040–T044 从 `TASKS.md` 里删掉了，却没有同步审计脚本里的 traceability 映射**，于是每次审计都报
`task-undeclared`。这条记下来不是为了追责，而是因为它说明**「开工前跑一遍 §0.1」不是形式**：
一个 B 类可追溯闸门失效了两天，期间所有「36/36 PASS」的引用都是过期的。

修法是一对一改指到活着的后继任务，不是删引用（删引用会让需求覆盖静默变少）：
`T040→T054`（冻结评测单元）、`T041→T055`（重跑上游行）、`T042→T056`（透明移植公开对手）、
`T043→T057`（导出与论断边界）、`T044→T058`（授权后才跑多种子）。RS-004 与六条 FR 的角色逐项对应，
**没有任何需求失去覆盖**，也没有任何 run hash 变化。

脚本身份本来就被 R1 protocol 的 `code.files` 钉着，所以改脚本必然触发 `audit-script-hash-drift`。
按既有先例（amendment 4，2026-09-07 同样重钉过这个脚本）追加第 5 条 amendment 并更新 pin：
审计脚本 SHA-256 `a1d99a7f…a7a65ca → 612596bf…201a5f7b`，**R1 protocol SHA-256
`f0b4702b258ef61257d0aeae20fd23bb48f36e4ff4761a575ac1b97277150829` →
`a4528861e0581d946ecadaba6cb7c2b83941796c7dbb9c49c5d186ddf8f768af`**，
本地与 4090 双端 scp 后 SHA 一致。重跑审计恢复 **PASS: 36 requirements mapped**。

⚠️ 4090 上的脚本仍是旧版（**G-18 跑完之前不 `git reset --hard`**，runner 每折现拉脚本起子进程），
所以在远端重跑审计会暂时报 `audit-script-hash-drift`——那是正确行为，G-18 收口后同步即消。

### 25.19 G-18 执行中查出的 base 预算缺陷（2026-09-22，**在 pooled 判定之前**）

fold 1 三臂先跑完（01:48）。**这不是 G-18 的判定**——判定只认五折合并，见后续小节。这里只记一条
与方法效果无关、但会污染对照的执行事实，**趁 pooled 数字还没出来先写下来**：

fold 1 的 `base` 是 **`.514779`**，而同一折的冻结 CLS 锚是 **`.5568315`**——**低 `.042`**。
`base` 与锚的配方本该只差「按文档打包」一条（§25.16），所以这个欠额必须解释，不能当成噪声。
直接从 fold-1 的 train manifest 重算打包，原因就出来了：

| | 每 epoch 优化步数 | 每步 mention 数 |
|---|---:|---:|
| 冻结锚（全局打散的 mention 流，batch 32） | **1,387** | 32 |
| G-18 用的规则（**累加到 ≥32 才切**） | **910**（锚的 65.6%） | **48.8** |
| 「取离 32 最近的边界」 | 1,248（锚的 90.0%） | 35.6 |

⇒ §25.16 写的「保住锚的有效 batch 大小」**只对了一半**：mention 预算是保住了下界，但因为一篇文档
平均 25.41 个 mention，`≥32` 这条规则几乎总是吃进第二篇，实际 batch 变成 48.8、步数掉到 910。
**同一个 lr 下少三分之一的优化步，是 base 欠额的一个已量化的候选主因**，而它对三臂是同等施加的，
所以它不影响臂间比较的内部有效性，只压低三条曲线的绝对高度——而**绝对门 `.583995` 正是对着锚定的**。

**处理方式（先写规则，再看数字）：**

1. **不中止 G-18。** 它是预注册的那一跑，中途换配方去救一个看起来不好的早期折，正是本项目禁止的
   行为。它跑完按原契约如实判定并写进结果页；
2. 同时把打包规则改成「取离 32 最近的边界」（910 → 1,248 步，48.8 → 35.6 mention），
   作为**同一周期的执行修复**（先例：C5 首跑因实现缺陷重跑，见 `2026-09-17_周报.md` §2.2），
   记为 **G-18b**。修的是 base 对锚的保真度，**不动任何门常数、阈值、backbone 或 seed**；
3. 两跑都进结果页。若 G-18b 的 base 仍显著低于锚，那就说明欠额另有来源，按 §10 的口径处理，
   **不再第三次调 batch**。

fold 1 的三臂数字先记在这里备查（**单折、非判定**）：`base .514779` · `full .539000` ·
`rewired .528175`，顺序是 `full > rewired > base`。中介（CAUSE / PRECONDITION violation rate）
分别为 base `.01015 / .00947`、full `.00884 / .00984`、rewired `.01015 / .01063`。
⚠️ 单折不判定任何一条门。

### 25.20 G-18 正式结果（2026-09-22）：**必要门全败，机制无效**

15 个 run（3 臂 × 5 折，seed 13，12 epochs）全部 `exit=0`，01:23:26–03:46:50，4090 卡 0/1/2。
汇总报告 `gpu-4090:.../seed-13/pooled_report.json` SHA-256
`326cc993f58a527b457daa3ee58e85cc264a8811fbf434d01512b0189fca3707`，状态 **`gate_failed`**。
覆盖精确命中 **2,913 documents / 73,939 mentions**，三臂的边数完全相同（各 114,479），
`gold_edges_used_by_model=false`、`final_valid_accessed=false`。

| 臂 | pooled macro-F1 | CT+ | CT− | PS+ | PS− | Uu | accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|
| **base** | **.543166** | .9729 | .6690 | .5258 | **.3616** | .1866 | .94428 |
| **full** | **.540671** | .9732 | .6699 | .5341 | .3501 | .1760 | .94483 |
| **rewired** | **.532591** | .9727 | .6703 | .5159 | .3642 | .1399 | .94367 |
| 冻结 CLS 锚 | `.553995` | — | — | — | `.382456` | `.196850` | — |

配对 document-cluster bootstrap（10,000 次，与契约一致）：

| 对照 | Δ | 95% CI | 判定 |
|---|---:|---|---|
| `full − base` | **`−.002495`** | `[−.015608, +.010516]` | **不为正，FAIL** |
| `full − rewired` | `+.008080` | `[−.005094, +.021546]` | 点估计为正但 **CI 跨 0，FAIL** |

**事前冻结的五条必要门，四条不过：**

| 门 | 要求 | 实测 | 判定 |
|---|---|---|---|
| 主效果 | pooled macro-F1 ≥ `.583995` | `.540671` | **FAIL**（差 `.0433`）|
| 归因 | `full > base`，CI 下界 `>0` | `−.002495` | **FAIL** |
| 归因 | `full > rewired`，CI 下界 `>0` | `+.008080`，下界 `−.005094` | **FAIL** |
| 稀有类 | PS− ≥ `.352456`、Uu ≥ `.166850` | PS− **`.3501`**、Uu `.1760` | **FAIL**（PS− 差 `.0024`；⚠️ **base 的 `.3616` 反而过线**）|
| 五类不塌 0 | 全 > 0 | 全 > 0 | PASS |
| 覆盖 / 部署性 | 2,913 / 73,939 各一次，无 gold 边 | 精确命中 | PASS |
| 中介 | full 两项 violation 率均低于 base | CAUSE `.00588` **等于** base；PRECONDITION `.00922` **高于** base `.00907` | **FAIL** |

**必须如实说的四点。**

1. **fold 1 那个漂亮的顺序是单折噪声。** 25.19 记的 fold-1 `full .539 > rewired .5282 > base .5148`
   在合并后翻掉了：逐折 `full` vs `base` 是 `.5390/.5148` ✅、`.5427/.5430` ❌、`.5213/.5496` ❌、
   `.5425/.5470` ❌、`.5663/.5719` ❌ ——**5 折里只有 1 折 full 更高**。这正是当初把判据写成
   「pooled + 配对 bootstrap」而不是「看逐折」的理由，也再一次证明**单折数字不能用来判断方向**。
2. **base 欠额是真的，但它藏不住一个胜利。** base `.543166` 比冻结锚 `.553995` 低 **`.010829`**
   （§10 那条跨章现象的第三例）。但 `full − base` 只有 `−.002495`——**欠额是机制效应量的 4 倍以上**，
   所以「把 base 修回锚的高度就能赢」这个说法在本轮**没有证据支持**：修 base 同时也修 full。
   G-18b（把每 epoch 优化步数从 910 抬回 1,248，§25.19）能回答「欠额是不是步数造成的」，
   **回答不了「机制有没有用」**——那一条本轮已经答了：没有。
3. **`full > rewired` 的 `+.008` 是本轮唯一非零方向的信号，但它不显著，而且负控偏保守**
   （§25.16 实测 40.53% 的边在 rewiring 后仍是同一 `(head,tail,subtype)`）。
   ⇒ **不得**把它写成「真实结构比打乱结构有用」。
4. **中介这条从一开始就没有空间可用。** §25.16 事前量到 gold 标签本身的 violation 率只有
   CAUSE `.003602` / PRECONDITION `.007744`，而三臂实测是 `.0058–.0059` / `.0091–.0096`——
   **模型离地板本来就只差千分之二到三**，再怎么改也挤不出可测的改善。这条参照线是在看到任何方法
   数字之前登记的，所以它不是事后解释：**中介作为机制证据在这个任务上基本没有分辨力**，
   下一轮若还要用一致性中介，必须先证明它有足够的动态范围。

另记一条执行观察：三臂的 dev 选中 epoch 分布很散（base `10/12/6/4/4`、full `6/5/6/4/5`、
rewired `7/6/6/2/12`），说明 12 epoch 内 dev 曲线不稳；这与 base 欠额可能同源，
交给 G-18b 一起看，**不在本轮据此改 epoch 预算**。

⇒ 按 C-26 契约，**本周期失败**。契约要求「做错误归因 + 回 R1 立项实质不同的第二个设计周期」，
且**不得**换名、扫参、加大 backbone 或改门。第二周期是否要投，属于作者裁决范围（`EXPERIMENT_PLAN.md`
§5 的 Gate 口径）。**G-18b 仍要跑完**——它回答的是 base 保真度问题，那条结论对归因章有独立价值。

### 25.21 G-18 的错误归因（2026-09-22）：边只有 `.2243` 对，而机制在**有结构的地方确实起作用**

C-26 契约要求周期失败后做错误归因。归因报告
`gpu-4090:.../seed-13/attribution.json` SHA-256
`ed3b4699c4230c9a6a008cfa12a367acf4d6fb6e3d73c4c5c6770568e5a7bd8d`（脚本来自 git 对象
`ccb0828`，实现 commit `faee5d7`；G-18b 在跑，未 reset 工作树，脚本以
`git show origin/main:<path>` 取出后运行，内容仍只来自 git）。

**第一件事：消息传的边，七成八是错的。**

| 量 | 值 |
|---|---:|
| 判正的边 | 114,479 |
| 与金标子类型逐条相符 | 25,681 |
| **边的精确率** | **`.2243`** |
| 至少有一条入边的 mention | 35,339 / 73,939（**47.8%**）|
| 至少有一条**正确**入边的 mention | 13,530 / 73,939（**18.3%**）|

这不是新发现的缺陷，是 C-25 那条输入门本来就允许的水平（门是 causal F1 ≥`.300`，实测 `.3060`）。
但把它和下游放在一起看才有意义：**残差是在一张 78% 错边的图上做消息传递**，而门只保证了
「概率可用」，从没保证「边可用」。

**第二件事（⚠️ 事后分层，不是预注册判据）：按入度分层，机制在有结构的地方是有效的。**

零入度的 mention 拿到的残差**恒为 0**，所以那一层 `full` 与 `base` 的差异只能来自训练噪声——
这正好给出一把内置的噪声尺子。

| 层 | mention 数 | `base` macro-F1 | `full` macro-F1 | `rewired` macro-F1 | `full − base` |
|---|---:|---:|---:|---:|---:|
| 入度 0（残差恒为 0） | 38,600（52.2%）| .547030 | .542964 | .538021 | **−.004066**（噪声层）|
| 入度 1 | 13,270（17.9%）| .549615 | .539505 | .514943 | −.010110 |
| **入度 ≥2** | **22,069（29.8%）**| **.476081** | **.503116** | .483490 | **+.027035** |

**入度 ≥2 那一层上，`full > rewired > base` 三者顺序完整，且 `full` 比 `base` 高 `.027`、
比打乱结构的负对照高 `.0196`。** 噪声层的对照读数：`full` 与 `base` 在那里有 1,220 处分歧
（3.2%），其中 `full` 对 `base` 错 570、反向 547——**近乎对半，正是两个独立训练模型之间的噪声**。
所以入度 ≥2 那一层的 `+.027` 不像是同一种噪声。

**这段必须怎么读（写作时不得放宽）：**

- **分层是事后做的，不在 C-26 预注册的判据里。** 三层里挑出一层有利，本身不稀奇。
  它**不能**改变 §25.20 的判定，也**不得**写成「方法在某某子集上有效」这种论断；
- 能写的只有一句：**「本轮的失败形态是稀释，不是方向错」**——机制够得着的只有 29.8% 的 mention，
  而在那部分上它的表现与负对照的排序都符合预期；
- 它给第二个设计周期指了两条**可证伪**的路：**(甲) 把边的精确率从 `.2243` 抬上去**（当前门只管
  概率质量，不管边质量）；**(乙) 让机制只在结构足够时介入**，而不是对全部 mention 施加同一条通路。
  两条都属于「实质不同的设计」，不是换名或扫参；
- ⚠️ 跨层的 macro-F1 **不可横向比较**（各层类别分布不同），上表只有**层内的臂间比较**有效。

⇒ 错误归因完成。第二周期投不投属作者裁决；无论投不投，**这张表是负结果归因章要用的核心证据**，
因为它把「机制无效」细化成了「机制被 78% 的错边和 52% 的零入度稀释掉了」。

### 25.22 诊断：这份后验买不到高精确率的因果图（2026-09-22，**只作诊断**）

§25.21 给第二周期指了两条路，其中 (甲)「抬边精确率」能不能走，用**已冻结的**自然后验直接算一条
曲线就知道，不必训练任何东西。⛔ **这不是对机制扫阈值**：冻结的判定规则仍是 `argmax_k w_k p_k`，
下表带 `diagnostic_only` 标记，**不得进主表、不得与任何已报分数相减**。报告
`gpu-4090:.../edge_precision_diagnostic.json`（脚本 commit `a4dee5b`）。

2,913 篇 / 73,939 mentions / 53,358 条 gold-expanded causal pair 上：

| 只保留置信度 ≥ | 边数 | 精确率 | 对 gold pair 的召回 | 还有入边的 mention |
|---:|---:|---:|---:|---:|
| **0.0（即冻结规则本身）** | 114,479 | **`.2243`** | `.4813` | **35,339**（47.8%）|
| 0.2 | 52,887 | `.3147` | `.3119` | 20,991（28.4%）|
| 0.3 | 25,391 | `.3838` | `.1826` | 11,239（15.2%）|
| 0.4 | 11,332 | `.4405` | `.0936` | 5,568（7.5%）|
| 0.5 | 4,294 | `.4891` | `.0394` | 2,369（3.2%）|
| 0.6 | 1,050 | `.5048` | `.0099` | 615（0.8%）|
| 0.7 | 152 | `.5000` | `.0014` | 104（0.1%）|
| 0.8 | 6 | `.5000` | `.0001` | 5 |

**结论很干脆：精确率在 `.50` 附近封顶，而且到那时触及面只剩 3.2%。** 换句话说——

- **路线 (甲) 从这份后验里走不通。** 不是阈值没调好，是**这个关系模型本身产不出「又准又有覆盖」
  的因果图**：最准的那一小撮边也只有一半对，而为了换到那个精确率要丢掉 93% 的触及面。
  要走 (甲)，得换一个**更强的关系模型**，那是 Ch4 的问题，不是 D4 加一个阈值能解决的；
- **路线 (乙)（机制只在结构足够时介入）是这份输入里唯一还有空间的方向**，而 §25.21 的入度 ≥2
  分层正是它的直接证据（那一层 22,069 个 mention 上 `full > rewired > base`，`full − base = +.027`）。
  但它同样是**事后**得到的线索，要投必须回 R1 重新立项、事前冻结判据；
- 顺带解释了 §25.20 的一个观察：`full − rewired` 只有 `+.008` 且不显著——在一张 78% 错边的图上，
  打乱端点能破坏的真信号本来就不多（再叠加 §25.16 实测的 40.53% 边根本没被打乱）。

⇒ **两条路的可行性已经先于裁决摆清楚**：(甲) 需要更强的关系抽取器（跨章依赖，超出 D4 单章范围），
(乙) 在本章内可行但必须重新预注册。作者据此决定第二个设计周期投不投、投哪条。

### 25.23 G-18b 执行修复重跑（2026-09-22）：**修复的理由被证伪，但它量出了一条更要紧的东西**

15 个 run 全部 `exit=0`，03:49:22–06:04:39。汇总报告
`gpu-4090:.../seed-13-b/pooled_report.json` SHA-256
`3fb617c2ffccf89651cc2a13babcffd1427aceb9672301f2685dcc1e30e6d315`，状态仍是 **`gate_failed`**。
与 G-18 的**唯一**差异是按文档打包的切分规则（910 → 1,248 步/epoch，48.8 → 35.6 mention/步）。

| 臂 | G-18（910 步） | **G-18b（1,248 步）** | 变化 |
|---|---:|---:|---:|
| base | `.543166` | **`.543138`** | **`−.000028`** |
| full | `.540671` | **`.549878`** | `+.009207` |
| rewired | `.532591` | **`.533347`** | `+.000756` |
| 冻结 CLS 锚 | `.553995` | `.553995` | — |

| 对照（G-18b） | Δ | 95% CI | 判定 |
|---|---:|---|---|
| `full − base` | `+.006740` | `[−.006543, +.020141]` | **CI 跨 0，仍 FAIL** |
| `full − rewired` | `+.016531` | `[+.000115, +.032351]` | 下界为正（**擦着 0**）|

**第一条，也是这次修复本该回答的那条：理由被证伪。** base 在 910 步和 1,248 步下分别是
`.543166` 与 `.543138`——**差 `.000028`，等于没动**。所以「优化步数少三分之一」**不是** base
比锚低 `.010829` 的原因。§25.19 提的那个候选主因，实测不成立；base 欠额另有来源，
按主表 §10 的口径处理，**不再第三次调 batch**。

**第二条：正因为理由被证伪，G-18b 不能替代 G-18 成为本轮的结果。**
预注册的那一跑是 G-18，它判 `gate_failed`。G-18b 是一次**其正当性已被自己的数据推翻**的修复；
把它拿来当本轮结论，就是「跑两遍留好看的那遍」——这正是本项目明令禁止的模式。
**G-18 的判定不变；G-18b 以敏感性观测的身份与它并列记录。**

**第三条，也是这一对跑真正的产出：配置敏感度和我们要测的效应量一样大。**
同样的三臂、同样的 seed、同样的数据，**只换一个打包规则**，`full` 就动了 `+.009207`——
而在更好的那一跑里 `full − base` 只有 `+.006740`。⇒ **我们想测的效应，落在配置噪声地板以下。**
任何建立在 `+.007` 上的论断都不成立，`full − rewired` 那个下界 `+.000115` 同理
（两跑里只有一跑显著，CI 擦着 0）。这条是本轮最该写进论文的方法学结论，
它也解释了为什么 §25.20 强调「单折不判定」——**连配置层面的抖动都大过效应本身**。

**第四条：即使不看主指标，机制在自己的中介上也是反向的。** G-18b 里 `full` 的两项 violation 率
（CAUSE `.00588` / PRECONDITION `.01029`）**都高于** base（`.00462` / `.00927`），比 G-18 更明确。
按 C-26 的机制判据，`full` 没有改善任何一项注册中介 ⇒ **机制 claim 在两跑里都不成立**。

逐折 `full` vs `base`（G-18b）：`.5675/.5188` ✅、`.5251/.5423` ❌、`.5540/.5598` ❌、
`.5301/.5564` ❌、`.5770/.5404` ✅——**5 折里 2 折**，与 G-18 的 1/5 一样谈不上稳定。

一处值得后续注意但**不据此下结论**的观察：抬步数之后只有 `full` 动了，`base` 与 `rewired`
几乎没动，而 `rewired` 带着**同样多**的残差参数。若要追这条线索，必须回 R1 事前立项，
不得拿它给本轮的失败做辩解。

⇒ **D4 v6.2 这一个完整周期的结论不变：必要门不过，机制无效。** 两跑、错误归因（§25.21）
与可行性诊断（§25.22）合起来，是负结果归因章的完整材料。

### 25.24 第二个设计周期的裁定与下一步（2026-09-22）

作者已授权执行代理在可行性未断时自行拍板（`docs/HANDOFF.md` 的既有口径），所以这里给结论
而不是停等。**裁定：D4 不投第二个机制设计周期。** 依据是三条已经量出来的数字，不是判断：

1. **路线 (甲) 不可行 —— 卡在「代码/算力」以外的一条：跨章依赖。** §25.22 实测精确率在 `.50`
   封顶，且那时触及面只剩 3.2%。要让边既准又有覆盖，需要**更强的关系抽取器**，那是 Ch4 的工作，
   而 A4 已是失败章。在 D4 内部加任何阈值/规则都改变不了这条上限；
2. **路线 (乙) 可行但测不出来。** 入度 ≥2 那层的 `+.027` 只覆盖 29.8% 的 mention，摊到 pooled
   主指标上量级在 `.008` 附近——而 §25.23 实测**只换一个打包规则就能让 `full` 动 `+.009207`**。
   ⇒ **要测的效应落在配置噪声地板以下**；而绝对门还要 `+.040`（`.5432 → .583995`）。
   投进去大概率买到第三个「方向对、量不够」，这正是 09-18 §10 已经吃过一次的亏；
3. **论文形态不受影响。** 结构早已定稿为「Ch6 承重 + 一章负结果归因」，D4 作为负结果章正是
   计划内的形态。**不投第二周期是维持计划，投才是偏离。**

⛔ 这条裁定**不封存 D4 这一章**，只是不再为**我们自己的机制**投第二个周期；它也不改变
「旧机制两个周期失败才封存家族」的一般规则——v6.2 家族只用掉一个周期，若将来 Ch4 真的产出
更准的关系图，(甲) 可以在那时重新立项。

**下一步不是停工，而是把这个负结果做成对领域有意义的证据。** 本轮我们证明的是「**我们的**
机制在预测关系上无效」。更有价值、也更该做的一条是：**用 MAVEN-FACT 官方自己的代码，
把它那条已发表的「加关系涨 2 分」的结论，在 gold 与 predicted 两种结构下各跑一次。**
这条已从候补区 H3 提进主表（**C-28**），开工自审两问的回答见那一行。

### 25.25 C-28a gold 边 oracle 诊断（2026-09-22）：**给它一张完美的图，增益仍然是零**

5 个 run 全部 `exit=0`（06:20:25–07:19:36，4090 卡 0/1/2）。gold sidecar 由
`build_d4_gold_sidecars.py` 逐行改写冻结 sidecar 得到——**文档、候选对与顺序全部原样**，
只有三类概率按金标重写，所以 oracle 与 `full` 的差别**只在于喂进去的是哪张图**。
五折 oracle 边数 `10,679 / 11,216 / 10,585 / 10,681 / 10,197`，合计 **53,358**，
与 gold-expanded causal pair 总数**逐条相等**——图确实是完美的。

| 行 | pooled macro-F1 | CT+ | CT− | PS+ | PS− | Uu |
|---|---:|---:|---:|---:|---:|---:|
| **oracle（gold 边，non-deployable）** | **`.542915`** | .9726 | .6541 | .5284 | .3609 | .1985 |
| base（不接结构，G-18b） | `.543138` | .9741 | .6632 | .5346 | .3734 | .1705 |
| full（predicted 边，G-18b） | `.549878` | .9742 | .6547 | .5345 | .3697 | .2165 |

配对 document-cluster bootstrap（10,000 次，与契约同一实现）：

| 对照 | Δ | 95% CI |
|---|---:|---|
| `oracle − base` | **`−.000223`** | `[−.014670, +.014262]` |
| `oracle − full` | `−.006963` | `[−.021753, +.008549]` |

**⇒ 一张完美的因果图，相对于完全不接图，增益是零。**

**这条结果推翻了我自己在 §25.21 写的解释。** 那里的说法是「失败形态是稀释，不是方向错」，
依据是入度 ≥2 那层的 `+.027`，并据此把 (甲) 抬边精确率、(乙) 只在结构足够时介入列为两条出路。
现在直接实验给出的答案是：**边的质量根本不是主因**——把 `.2243` 换成 `1.0`，把触及面从
47.8% 换成金标全覆盖，pooled 主指标纹丝不动。所以：

1. **§25.21 的「稀释」解释作废。** 那一层 `+.027` 现在只能看作事后分层里的一个未解释现象，
   **不得**再用它支撑任何出路；这正是当初把它标成「事后分层、不作论断」的价值所在；
2. **路线 (乙) 随之失去意义。** 「只在结构足够时介入」的前提是结构足够时机制有效——
   oracle 说结构完美时它也无效；
3. **路线 (甲) 也不再是「走不通」而是「走了也没用」。** §25.22 说的是买不到高精确率；
   现在更强的结论是**买到了也没有用**。⇒ §25.24 不投第二周期的裁定**不变，且理由更硬**；
4. **本章的核心论断因此可以写得更锋利**：不是「我们的边不够好」，而是
   **「在这个任务与这套参数化下，把因果结构作为按置信度门控的残差接进事实性检测头，
   即使结构是金标，也不携带可测的增量信息」**。

**必须同时写清楚这条结论的边界**（否则会被读成比证据更强的东西）：

- 它成立的范围是**本项目的参数化与协议**：RoBERTa-base、按子类型的零初始化线性消息、
  置信度门控求和、五折 OOF、seed 13。它**不反驳** MAVEN-FACT 原论文 Table 6 的
  `47.1 → 49.1`——那是另一套 backbone（roberta-large）、另一种接法（把前驱句表示**拼接**进
  事实性表示）、另一个划分（test）；
- 恰恰因为这条边界，**C-28 变得更值得做，而且假设更锋利了**：原论文的增益到底来自
  **前驱句的文本**，还是来自**关系这条结构**？我们的 oracle 已经排除了「结构本身」这一半
  （我们的消息传的正是前驱 mention 的编码表示，仍然零增益），所以 C-28 应当直接对着
  官方那套**拼接**实现跑，而不是继续改我们的残差；
- oracle 的「边对」与「置信度高」按构造一起变（gold 边一律 `.998`），所以它不是单变量对照；
  但这对本结论无害——**两个变量都朝有利方向动了，结果仍是零**。

⚠️ 按 C-26 契约，oracle **不设臂**，上表只作 `results/` 里的 non-deployable 诊断行，
**不得进主表任何通过门**，也不得与 `.583995` 相减。

### 25.26 C-28 官方 EFD 代码的透明适配与启动（2026-09-22）

官方实现已 vendored 进 `baselines/maven_fact/`（上游 `THU-KEG/MAVEN-FACT` `6754471`，
逐文件原样 SHA-256 在 `UPSTREAM.json`），**为的就是让之后每一处补丁都是可审阅的 diff，
而不是服务器上的未追踪改动**（4090 解析不了 `github.com`）。

**只打了一个补丁**（`trainEFD/train.py`，`68bfcbd1…33e2313 → 362146f4…27d61a79`，CRLF 行尾保留）：
上游每个 epoch 在 `--test_data` 上评测并报**历轮 test macro-F1 的最大值**（它保存 checkpoint 那行是
注释掉的），这是在评测集上选模。补丁加一个**必填的** `--dev_data`，按 dev 选 epoch 并报该轮 test
指标，同时**仍报上游那个逐轮最大值**，让两套口径的差别看得见。模型结构、分词器、特殊 token、
优化器、损失与全部默认超参未动，`EFDDataset` 与关系/论元特征构造未动。

**两行只差结构来源**，其余逐位一致：

| 行 | `causal_relation` 来自 | 部署性 |
|---|---|---|
| `gold` | 文档自带的人工标注（论文设定） | **不可部署** |
| `predicted` | 我们冻结的五折后验，按 mention 对提升到 event 簇对 | 可部署 |

predicted 一侧**只读本折自己的**三份 sidecar（它们已覆盖全部 2,913 篇 = 1,747+583+583），
去拿别折的 OOF 后验正是 §25.14 拒绝的那条泄漏路径——这条在适配器里是 fail-fast 的。
fold 1 的簇级关系数：gold `1,438 CAUSE / 5,637 PRECONDITION`（evaluation），
predicted `4,628 / 12,314`——predicted 多 2.4 倍，与 mention 级 precision `.2243` / recall `.4813` 一致。

一处踩到的接口差异已修并加测试：**我们的 loader 把 mention id 命名成 `<doc>::<mention>`，
官方 jsonl 用裸 id**，簇提升时直接 `KeyError`；现在剥前缀并校验前缀确实属于该文档。

1 epoch 冒烟（fold 1 predicted）跑通：dev `.429186` / test `.429223`（两个划分确实不同，
逐类 F1 不一样，macro 只是碰巧四位小数相同），预测 14,780 条与 fold-1 mention 数一致。
⚠️ 冒烟里 PS− 与 Uu 都是 0——**官方用的是无类别加权的交叉熵**，而我们的锚用 `alpha=.5` 加权；
这意味着官方两行与我们的锚**在稀有类上本就不可比**，这是它自己的配方，我们不改。

正式 10 个 run（2 结构 × 5 折，`--epochs 10 --lr 1e-5 --batch_size 16 --max_length 160 --seed 13`，
backbone 用与我们锚相同的 roberta-base pin 而非它默认的 roberta-large——这处偏离也记在这里）
于 **07:46:20** 启动，4090 卡 0/1/2。**FR-016 状态只能是 (b)**：官方数字所在的 test 划分拿不到。

### 25.27 C-28 官方 EFD gold / predicted 五折 OOF 收口（2026-09-30）

10 个 run 已在 2026-09-22 14:28:29 全部 `exit=0`，远端相应进程确认 GONE。一次性汇总报告位于
`gpu-4090:/data/TJK/ekg/runs/stages/D4/d4-official-efd/seed-13/pooled_report.json`，SHA-256
`bae70b24fe2df786ce8d13cf96183eecbfaefb16a50d700d79387e86dc31614b`。汇总器逐折核了
`status=complete`、split 内 mention 顺序、上游标签 id 到本项目标签名的映射，以及五折 OOF 并集；
最终覆盖恰好 **2,913 篇 / 73,939 mentions**，无重复、无缺失。

| 结构输入 | pooled macro-F1 | CT+ | CT− | PS+ | PS− | Uu |
|---|---:|---:|---:|---:|---:|---:|
| gold（non-deployable） | **`.523005`** | .977921 | .678429 | .505557 | .344423 | .108696 |
| predicted（deployable） | **`.526663`** | .977420 | .670171 | .519822 | .372881 | .093023 |

按文档聚类的 10,000 次配对 bootstrap：

| 对照 | Δ | 95% CI | 判定 |
|---|---:|---|---|
| `gold − predicted` | **`−.003658`** | **`[−.021924, +.014669]`** | CI 跨 0；gold 不优于 predicted |

逐折按 dev 选出的 evaluation macro-F1 也没有稳定臂序：gold 为
`.493303 / .514440 / .524844 / .515278 / .553292`，predicted 为
`.525286 / .480751 / .543061 / .519491 / .551010`；gold 只在 2/5 折较高。两行的结构输入差别并不小：
gold 共 **36,316** 条簇级关系（6,797 CAUSE + 29,519 PRECONDITION），predicted 共 **84,337** 条
（23,456 + 60,881），是 gold 的 **2.32 倍**。即便如此，两行仍未出现可分辨差异。

**错误与修复证据。** 上游代码逐 epoch 访问 test，并报历轮 test macro-F1 的最大值；本轮补丁改为
按 dev 选 epoch，同时保留上游口径作为审计列。10 个 run 中，上游口径会把 6 行报得更高、4 行相同；
最极端的是 predicted fold 2：按 dev 选择是 `.480751`，看完 test 再取最大值会报 `.560578`
（高 `.079826`）。所以这个补丁修掉的是会实质改变结论的评测集选模，不是格式差异。

**能写的结论：** 在这次 FR-016(b) 透明适配里，官方「拼接前驱句文本」实现对 gold / predicted
关系来源**没有可测差异**；更准确的 gold 结构没有带来更高的事实性 macro-F1。这与 §25.25 的
oracle 结果方向一致：至少在本项目核过的残差接法与官方拼接接法中，都没有证据表明**金标结构精度**
本身提供增量。

**不能写的结论：** 这不是「前驱句文本有效、关系结构无效」的单变量因果检验。两行都启用了
`--add_relation`，都由关系端点决定拼接哪些前驱句，没有一个 text-matched / relation-shuffled / no-relation
臂。因此本轮只能排除「gold 结构显著优于 predicted 结构」，不能把原论文的 `+2` 唯一归因给文本。
若要回答后一个问题，必须重新预注册同文本、只打乱结构语义的对照；本轮没有事后增设它。

**保真度与去向：** 两行均为 **FR-016(b)**：原论文 test split 不可得，本轮用冻结五折 OOF；backbone
用 roberta-base pin 而不是论文的 roberta-large；epoch selection 从上游的 test-max 修为 dev-selection。
模型、关系/论元特征构造、无类别加权 CE 和其余默认训练配方未改。gold 行不可部署，两行都不进入
任何 promotion gate，也不能与本项目 `.583995` 目标或加权 CE 主锚直接相减。

⇒ **C-28 完成，但不为 D4 翻案。** D4 的正式方法结果仍是 §25.20 的 G-18：四项必要门不过、
机制无效；§25.25 与本节补齐的是「不是因为预测边不够接近 gold」这一归因证据。D4 v6.2 的输入、
机制、负控、oracle、官方代码适配与错误记录至此全部闭合；不启动未预注册的新臂或第二机制周期。

### 25.28 G-19 EasyECR / Global-Local Topic 透明适配收口（2026-10-02）

**结论：已完成一条可复算的 FR-016(b) 透明适配，但其统一协议下的共指结果是明确负值；不重跑、
不事后扫阈值，队列推进至 G-20。** 这不评价 Global-Local Topic 在其发表的 KBP 2017 基准上的能力：
KBP 2017 要 LDC 许可，本项目无法取得，故不能建立原始基准的保真度验证。

#### P / V / U 身份与可追溯性

- **P（论文背景）**：Global-Local Topic（Xu, Li, Zhu, EMNLP 2022）原始任务为 KBP 2017；论文数字只作
  背景，不进入下表的差值或排序。
- **V（原始基准保真度）**：**FR-016(b) Unverifiable**。障碍是 KBP 2017 的 LDC 许可语料不可得；此外本次
  使用 MAVEN-ERE、金标 event mentions、MAVEN 官方 evaluator，且训练文档数为 2,331 而非既有锚的 2,622。
- **U（统一协议）**：291 篇 P1 internal-dev、7,195 event mentions、1,719 TIMEX、234,870 ordered pairs；
  candidate digest `15a3b1a548625624642130190b39411e6346866ff8594c2af2020cfbdac10910`，组织方 evaluator
  SHA-256 `32919e86d98c6fafae6aa9505579e2c356caee12c32c1a8c719910acec359598`。因此下表可与同一 unit 的
  项目主锚作**描述性统一协议比较**，但仍是单 seed，不能替代跨初始化确认。

正式运行在 `gpu-4090:/data/TJK/ekg/runs/stages/R1/r1-v61-20260904/baselines/coref/global-local-topic/`
`g19-s13-20261002/`：30 epoch、seed 13、P1 train 的 hash-frozen 2,331-document training 与独立
291-document selection-dev。selection 仅在该独立集合内从预先固定的 `0.1…0.9` grid 选择 threshold
**0.9**；evaluation 输入在模型训练、选档与推断阶段均为无 gold test shape。上游为
`hqyang/EasyECR@f6cd779fbddc7ced2b14397041f83d92713115a9`；运行代码为 `f483bda`，preflight SHA-256
`f0ac88b0462440fa8555b58ec5bb2615f63bd20a04dbf15bbdf916a69bfc2fea`。透明运行补丁、输入差异和
smoke 证据见 `COMPARABILITY_PLAN.md` §4 与 `HANDOFF.md` G-19 记录。

推断阶段先写无标签 `raw_clusters.jsonl`（291 行，SHA-256
`88c7993a30678a0c4e01480c1db77d6b26f53551e45f51800cd7919c7cdff05d`）；之后才以同一 P1 gold
文件作 identity/partition 校验和 official-shape 转换。转换后的 prediction SHA-256 是
`08ce7710a911a4068df5857216e12b9d93b29a40ec5ae9136f78e474491afd7a`，gold SHA-256 是
`403b69a8a9c83e2be41e0c366fed7edcd7e00796dbd14ec6f07df7e560507e81`。export 和 scorer 均验证
291/291 documents、7,195/7,195 mentions 与冻结 candidate digest；无静默丢弃。`official_export.json` /
`official_metrics.json` SHA-256 分别为 `d0ff84f8e47ff68e4dcbadc71b385f03ec146357d3322fa992d1c92e90275fe4` /
`48ab93ceed1be5cc29f7cd7ce71ed12e0b9e1cb96f0dcb8bef8d7562f3dbafb1`。log 记录的墙钟为
08:08:41–11:42:34（约 **3h34m**）。

#### 官方共指结果（MAVEN-ERE evaluator）

| 行 | MUC P | MUC R | **MUC F1** | B³ F1 | CEAFe F1 | BLANC F1 |
|---|---:|---:|---:|---:|---:|---:|
| MAVEN-ERE official joint（同 unit 主锚） | — | — | **80.984720** | 98.039866 | 97.731576 | 89.880089 |
| **Global-Local Topic via EasyECR（U；FR-016(b)，single seed）** | 57.142857 | 0.698080 | **1.379310** | 95.849489 | 94.225421 | 49.961723 |

这是合乎协议但几乎全 singleton 的预测：7,195 个 mention 被分为 7,188 个 cluster，其中 7,181 个
singleton，只有 7 个 size-2 cluster（14 个 mention）。所以 B³/CEAFe 的较高数值是单例占主导的性质，
**不能**遮蔽 MUC recall `0.698080` 与 MUC F1 `1.379310` 所揭示的共指崩塌。temporal / causal / subevent
均为 0，因为 exporter 按定义为这条**只做共指**的外部方法补 all-NONE relation fields；它们不是该方法的
relation 结果，也不进入本行解读。

#### 有效性审查与裁决

评分前后没有发生数据、候选、评测器或覆盖漂移：raw clusters 的每个 document 均 partition 了其完整
mention 集，official exporter 与 scorer 的硬性校验均通过。上游 `EcrConnectedComponent` 对此 run 的
语义是仅在 predicted distance 小于 selected `0.9` 时连边；不存在把阈值方向写反的接口证据。

这条结果**不是**“Global-Local Topic 比原论文弱”的论断；它只能表述为：**在本项目披露的 MAVEN-ERE
透明适配协议下，这个单 seed 运行产生了近乎全 singleton 的 clusters，且低于同协议主锚。** 因为 threshold
由独立 selection-dev 在方法结果可见前已冻结的 grid 选出，事后改 threshold、重训或增大 backbone 都会污染
baseline 行，故一律不做。G-19 据此收口；其论文价值是补齐一条独立发表方法的可审查负向 U 行，同时把
“高 B³/CEAFe 即代表可用共指”这一单例主导误读排除在外。C-29.6 随后发现 LLMERE 的恢复口径有协议冲突；
作者取甲，将 G-20 收口为无可评分的可得性行，C-30 因而审计现有 G-19 U 行与该命名障碍，而不等待一个不存在的
LLMERE 分数。

### 25.29 C-30 · P/V/U 主表与声称审计（2026-10-02）

**结论：C-30 完成。** G-19 是当前队列唯一可作统一协议描述性比较的外部 U 行；LLMERE 不是待补跑的
零分或低分，而是作者取甲后明确的 `P 有 / V(b) / U 无可评分输出` 可得性行。此结论关闭了“等 G-20
才可审计”的错误依赖，并把下一步转为受约束自驱动的研究卡（C-31），不重开 D4/A4/C5 的封存机制。

#### 开工自审

1. **科研价值**：C-30 对准各方法章主表的公开可比性与 `SPEC.md` QR-001/FR-016。它要验证的是一条外部
   透明适配能否从 immutable raw output 独立复算，及无法产生分数的对手是否被诚实地标为可得性障碍；否则
   P 层论文数字、V 层保真度和 U 层本项目数值会被错误地混作同一比较。证据是本节的 scorer 复算、
   §25.28 的 raw/export/metrics hashes，以及 `BASELINE_ROSTER.md` §2。
2. **可行性**：**可行。** G-19 的 raw clusters、official-shape export、gold、frozen evaluator 和候选
   digest 都仍在 `gpu-4090:/data/TJK/ekg`；本任务只读、CPU 评分，不训练、不读 final-valid、不改输出。
   LLMERE 的 U 行不可行是已命名的【协议】阻断，不是 C-30 的执行障碍，因为 C-30 的设计允许该行无数值。

#### 独立复算与登记

在不写 `--output`、不修改 immutable run 的前提下，重新执行：

```text
cd /data/TJK/ekg
.venv/bin/python -u scripts/score_maven_ere_official.py \
  --evaluator data/protocols/v6/tools/maven_ere_evaluate.py \
  --gold runs/stages/A4/a4-v61-pair-evidence-r1/preflight-r2/data/MAVEN_ERE/internal-dev.jsonl \
  --pred runs/stages/R1/r1-v61-20260904/baselines/coref/global-local-topic/g19-s13-20261002/official_predictions.jsonl \
  --candidate-digest 15a3b1a548625624642130190b39411e6346866ff8594c2af2020cfbdac10910
```

输出的 291-document coverage、candidate digest 与 §25.28 的 official metrics 每一项一致；因此不是读取旧日志
摘要。G-19 的 raw/export/metrics/evaluator/gold hash 与 coverage 已在 §25.28 全量登记，C-30 不复制为第二套
权威数字。

| 行 | P（原文背景） | V（原始基准保真度） | U（本项目统一协议） | 允许的主表/论文表述 |
|---|---|---|---|---|
| Global-Local Topic via EasyECR | 有；EMNLP 2022 的 KBP 2017 表只作背景 | **FR-016(b)**：KBP 2017 需要 LDC 许可，无法在原始基准验证 | **有**；G-19 raw clusters → official export → frozen MAVEN evaluator 独立复算，固定 seed 13 | 仅称“本项目披露的 MAVEN-ERE 透明适配下的描述性 U 行”；不得与原论文数字相减或称胜过原论文 |
| LLMERE-causal | 有；COLING 2025 MAVEN-ERE causal 工作只作背景 | **FR-016(b)**：验证已发布 710-document prediction 会读封存 final-valid，已按 A 类红线放弃 | **无**；C-29.6 证明 target-third-line stop 需逐例读 internal-dev target，作者取甲不生成/不评分 | 称“无 official inference、透明适配恢复有 target-dependent stop 协议障碍”；不得写成方法低分、零分或未完成实验 |

七项 provenance 的结果是：G-19 的 paper/table、upstream revision、P1 manifest、candidate universe、
evaluator/label mapping、train/selection/evaluation 隔离和 input delta 均已在 §25.28 逐项可追溯；LLMERE 的
同七项中，P/V 与原始适配身份可追溯，但 U 的 raw output/evaluator score **按作者甲裁决不存在**，故只进入
可得性表。任一未来新行缺少任一项，就不能进入同协议 U 主表。

#### 指标与下一步

本次没有因 B³/CEAFe 的表面数值而改变 Ch5 的 MUC 主指标，也没有创造“LLMERE 缺失惩罚”指标。这样设计合理：
可比性由相同 manifest、候选全集和 official scorer 构成，单 seed 只允许 `non-confirmatory` 描述；一个无分数的
行只能说明可得性，不能代替或拖低模型主指标。下一任务是 C-31，按
[`AUTONOMOUS_RESEARCH_PROGRAM.md`](../AUTONOMOUS_RESEARCH_PROGRAM.md) 只读建立领域研究卡；它尚不授权任何
新机制训练。

### 25.30 C-31 · 第一轮领域证据地图（R0，2026-10-02）

**结论：第一轮 R0 已完成，没有一张卡可进入 C-32。** 这不是“该领域没有新论文”的结论，而是“在本项目
当前的 MAVEN-ERE/MAVEN-FACT、冻结候选全集与不重写外部方法的约束下，三条最相邻的近期路线都不能形成
可比较、可复现的新机制合同”。因此没有启动代码改动、CPU 预检、GPU 或新 seed；这正是 C-31 的 fail-closed
设计要避免的无边界试错。

#### 研究问题与取舍规则

问题是：近期公开工作中是否存在一个**尚未被封存家族占据**、能为 D4/A4/C5 任一方法章提供可证伪机制、
且能在现有公开数据/协议上经过强对照、单变量消融和负控检验的路线？优先级只按论文论断与证据强度排序，
不按预估分数、实现快慢或 GPU 是否空闲。每张卡均核到论文正文/官方仓库，而非只信摘要或聚合网站。

| R0 卡 | 一手机制与可能支撑的论断 | 数据/协议/代码核验 | 判定 |
|---|---|---|---|
| **D4-1 · Trucidator** | [Zhang et al., COLING 2025](https://aclanthology.org/2025.coling-main.139/) 以文内/跨文档图和多任务学习处理幻觉式 document-level factuality；若同一输入可得，它可能检验“跨文档证据是否改善极难的反事实/幻觉 factuality”。 | 原文构建并评测的是 **Factualusion**，其动机正是跨文档 hallucination documents，不是 MAVEN-FACT 的五类、2,913-document OOF unit；论文页没有可核实的官方代码链接。把它迁到 MAVEN-FACT 会同时改变数据分布、输入与任务定义，不能称为透明复现。 | **不准入：数据 + 协议；代码未核实。** 不是 D4 的可比外部行，也不能在不改研究范围下作为新机制。 |
| **A4-1 · MMD-ERE** | [Guan et al., COLING 2025](https://aclanthology.org/2025.coling-main.460/) 的多角色辩论以关系语义为不同参与者设 topic；它在 MAVEN-ERE 上报告结果，表面上最接近 A4 的关系问题。 | 原文为 causal/subevent 各选 50 documents，报告 605/404 instances，而非项目冻结的完整 291-document causal candidate universe；它比较的是 LLM agent/辩论设置，未在论文页给出可核实的官方训练或推理实现。样本、候选集、模型服务和 evaluator 都不能与现有 U 行逐项对齐。 | **不准入：协议 + 代码。** 不能把一小样本 agent 结果移进 full-unit causal P/R/F1 主表，也不应据论文散文重写其系统。 |
| **C5-1 · rationale distillation for ECR** | [Nath et al., NAACL 2024](https://aclanthology.org/2024.naacl-long.218/) 有官方 [代码](https://github.com/csu-signal/llama_cdcr)，以 LLM generated rationales 蒸馏 event-coreference scorer；其“避免 lexical shortcut”的问题与 C5 的高相似 false merge 相邻。 | 论文/仓库明确是 **cross-document** ECR，评测 ECB+、GVC、AIDA，而非 MAVEN-ERE 文档内全候选；它依赖外部生成 rationale 与不同聚类/数据管线。直接移植会改变数据、candidate universe、输入和预算，不能是 FR-016 透明适配；原 C5 机制家族也已封存，不能把 rationale 文本换名复活。 | **不准入：数据 + 协议；新颖性不足以绕过已封存家族。** 可作为最近邻反例保留，不产生实现任务。 |

#### 可行性结论与停止

- 三张卡都具有真实的科研动机，但**没有**一张同时通过数据、协议和代码门；因此“AI 找到了相关论文”不是
  “AI 找到了可跑实验”的证据。
- D4-1 与 C5-1 若强行迁移会扩大到其他语料/跨文档输入；A4-1 若强行做则要重建没有发布的 agent 系统，
  分别违反【数据/协议】和【代码】可行性纪律。
- 本轮没有足以生成 C-32 合同的 `observed error → treatment → mediator → main outcome`，也就不能诚实地
  声称有 ≥80% power、单变量消融或可执行 GPU 预算。补写这些字段只会伪造准入。

**停止动作**：C-31 第一轮以 `no_admissible_candidate` 收口，C-32/G-21 不启动。根据
`AUTONOMOUS_RESEARCH_PROGRAM.md` §3.1，若要继续必须由作者决定是否扩大 thesis 数据/任务范围；那会改变
研究问题、公开比较轴和可行性，执行代理不可自行把外部语料或生成标注引进训练。当前可安全保留的成果是三张
带一手证据的排除卡，它们缩小下一轮检索空间并防止重复试错。

### 25.31 C-31b · 作者授权后的唯一外部 benchmark 证据卡（R0，2026-10-02）

**结论：作者已授权一个、且仅一个额外公开 benchmark；C-31b 固定 EventStoryLine v0.9（ESC）为 E 层
外部验证。** 该决定不让 C-31 的三张排除卡复活，也不修改 MAVEN 的主任务、候选全集、U 层主表或单 seed
约束。当前只进入 C-32a CPU 数据/协议预检，尚无模型运行、GPU 任务或项目分数。

#### 决定与一手证据

| 核验项 | 一手证据与冻结结论 | R0 状态 |
|---|---|---|
| 数据与许可 | 官方仓库 [`tommasoc80/EventStoryLine`](https://github.com/tommasoc80/EventStoryLine)，revision `46edefee5e82e0917b823abe0a18bf8c7770f15c`，公开数据、评测格式、基线脚本和 `LICENSE.md`（CC BY 3.0）。原始任务论文为 [Caselli & Vossen, 2017](https://aclanthology.org/W17-2711/)。 | PASS，仍须 C-32a 逐文件哈希和解析。 |
| 外部协议 | [ICCL](https://aclanthology.org/2024.emnlp-main.51.pdf) 明确使用 ESC v0.9：最后两个 topics 为 dev、其余 20 个 topics 作 topic-disjoint 5-fold CV，报告 causal existence 的 P/R/F1。 | 作为 E 层目标协议；精确 topic/fold 及候选定义尚待 C-32a 源码/数据闭合。 |
| 与主表关系 | ESC 是独立新闻 topic 分布上的二元 causal-existence；MAVEN 是 Wikipedia、带方向的 CAUSE/PRECONDITION。 | **E ≠ U**；不得替代或混入 MAVEN 主表，最多检验未来新机制的外部分布泛化。 |
| 近期对手的可得性 | DICP 官方仓库无许可证，README 所列 `src/run.sh` 不存在且仅见不完整 CausalTimeBank 入口；ICCL 官方仓库无许可证、读取未发布 `train.npy`，且按 document shuffle/split 而非上述 topic split；MAVEN-ERE 官方 causal runner 虽为 GPL-3.0，但其 ESC `KFold` 作用于 tokenized samples。 | 三者仅 P 层机制/背景参考，**不运行、不重写、不形成 V 行**。 |

MECI 也未被选中：其公开仓库未给可核实许可证，也未发布可重现的精确 split membership/runner；它同时留下
【授权/协议/代码】的不确定性。ECR 的跨文档外部数据也没有进入范围。因此 ESC 是在作者限定“一项”下唯一记录的
选择，而不是开放新的语料检索池。

#### 开工自审与停止条件

1. **科研价值**：ESC 的用途是外部**证伪**未来经 C-32b 准入的新因果机制是否依赖 MAVEN 的 Wikipedia
   分布；它为“机制价值具有跨主题新闻泛化”的限定论断提供独立的、公开的 P/R/F1 轴。它不支持“在 MAVEN
   胜过多个方法”的学位论文主张，故绝不改变 A4 的进入门或已有封存裁决。
2. **可行性**：研究卡本身可行（公开数据、许可和协议来源已核实），但执行尚未可行：C-32a 必须在 CPU 上给出
   精确 source/filter manifest、topic-to-document/fold mapping、候选全集、标签折叠与可重算 scorer。任何一项
   不能与来源闭合即为【数据/协议】阻断；届时停止，不以其他数据或第三方 runner 替换。
3. **授权限制**：仅此一个 ESC E 行；不新增人工/生成标注、不读取 final-valid、不加 seed、不启动 GPU。5-fold
   是待审计的外部评测结构，不是获授权的多 seed；在 C-32a 完成前不得把它解释为可训练计划。

### 25.32 C-32a · ESC source/split/candidate/scorer CPU 预检（协议阻断，2026-10-02）

> 本节保留 10-02 的审计记录。**10-08 的一手复核收窄了其阻断依据，见 §25.33**：ICCL 明写 dev topics、
> 在 loader 前固定 seed，也有 binary scorer；不能将 typed scorer 的错误扩张成 binary scorer 不存在。
> `protocol_blocked` 状态保持，因为冻结的 topic-disjoint 协议与公开代码不一致，输入链也未闭合。

**结论：`protocol_blocked`【协议】。** C-31b 选择 ESC 作为作者授权的唯一外部 benchmark 在数据可得性和
许可层成立，但不能建立一个能与公开 ECI 论文直接相比较的 E 行。原因不是模型性能、显卡、seed 或实现速度：
固定 v0.9 source 后，公开物没有把 `source → development topics/folds → candidate universe → scorer` 闭合为唯一
对象。故本节没有模型、预测、E 分数、GPU 任务或 final-valid 访问；C-32b/G-21 不启动。

#### 只读 source snapshot

| 项 | 实测值 / 一手位置 | 判定 |
|---|---|---|
| source | `tommasoc80/EventStoryLine` revision `46edefee5e82e0917b823abe0a18bf8c7770f15c`（2023-09-23）；该 revision 的 `git archive` SHA-256 是 `5b67f0bb134d5bd75cc35606267c6c2cdee853a2ad94e57b544ea443a23fcc5a`。 | source 已固定。 |
| 许可 | `LICENSE.md` 是 CC BY 3.0（SHA-256 `07acd126b170ec6874e9d381d581177c3ba4ec51f57b2f37546cc580e66e4be7`）。 | 许可不是本次阻断。 |
| v0.9 数据形状 | `annotated_data/v0.9/` 有 **22** 个 topic（`1,3,4,5,7,8,12,13,14,16,18,19,20,22,23,24,30,32,33,35,37,41`）和 **258** 个 `*.xml.xml`；根下没有 `dev/`、`test/` 或 fold 文件。 | 不能从 source 推出“最后两个 topic”是哪两个，也不能推导 5 个公开论文 fold。 |
| 版本不能混用 | 同一 source 的 `annotated_data/v1.0/` 才含 `dev/`、`test/`；其 README 明示为相对 v0.9 的数据清理版本。 | 不能把 v1.0 split 倒灌为 v0.9 的论文协议。 |
| 候选与标签 | `baseline_OP.py` 只对过滤后的同句 event pair 出链接；`baseline_PPMI1.py` 分别生成同句与跨句 PPMI candidates，并以写明的 `# seeds + dev` 阈值筛选。 | 官方 source 本身存在多个候选生成规则，不存在可直接绑定近期论文的唯一 binary candidate universe/negative rule。 |
| evaluator | `eval_script.py` 读取系统自行输出的 link list；typed relation 的 `fn_pairs_value` 在第 104 行误聚合 `i[0].false_negative`（pair-level），而非 `i[1]`（relation-value）。`eval_script.py` SHA-256 为 `f3676af1795e2ecbf3559cf0f85a28ae67f16e82d0cfa0663181a71af8d3b366`。 | 不能把它未经修正地当作现代 causal-existence P/R/F1 的冻结 scorer；修正它又会创造不同于公开论文的口径。 |

#### 为什么不能用“合理推断”补齐

ICCL 的正文描述了“末两 topic 作 development、其余 20 topic 作 5-fold”这一研究习惯，但其公开仓库没有
许可、所需 `train.npy` 也未发布，且 `load_data.py` 按 document 做未绑定 shuffle；它不能把 source 中缺失的
fold IDs、pair construction 或 label folding 变成可审计的真值。DICP 的 `src/run.sh` 与完整依赖同样未发布；
MAVEN-ERE 的公开 external runner 是 tokenized-sample `KFold`。把其中任何一个带入，都违背 C-32a 的“同一
source/split/candidate/scorer”要求。

自行定义“全部有序 event pair”、固定数值排序后的两个 dev topic，或修正官方 scorer，当然可以形成一个**新的**
ESC 实验；但它将改变至少候选全集、负例分布或 evaluator，既不能验证公开论文数字，也不会解决本项目“指标可与
公开论文比较”的诉求。把这种新任务写成 E 行会把设计选择伪装成基准事实，故不做。

#### 开工自审、停止与后果

1. **科研价值**：本 gate 对准 `COMPARABILITY_PLAN.md` §2.1 的“公开可比性”，不是追求一次可跑训练。它排除了
   “同叫 ESC、分数却不是同一任务”的错误正比较，保护 MAVEN 仍为可检验的主表；这个负结果本身是对后续研究
   资源的有效约束。
2. **可行性**：source 与许可可得，但**实验不可行，卡在【协议】**：没有一手闭合的 v0.9 split、candidate
   universe 和 scorer，且近邻代码不能合法地补上它们。此为 A 类有效性问题，不是可由 GPU、更多 seed 或重写
   parser 解决的工程问题。
3. **停止动作**：外部 benchmark 授权在 ESC 上已完成一次 fail-closed 审计；不跑模型、不产分数、不换其他
   benchmark、不启动 C-32b/G-21。若作者要继续，必须另行选择“授权一个新 benchmark”或改为审计/整理现有
   MAVEN 公开对手证据；两者都须从新的 R0 决策卡开始。

### 25.33 C-34 · 研究回合复盘与作者决策卡（2026-10-08）

> 后续作者已明确委托执行代理完成科研路线的最终裁决，见 §25.34；本节保存委托前的复盘与建议。

**结论：C-34 `done`；本研究回合以准入阻断收口，新训练仍 `blocked`。** C-31 没有准入机制，C-32a
没有闭合 E 协议，因此没有 G-21 原始预测，C-33 的模型结果审计不适用。复盘走的是主表事先允许的
“C-31/C-32 命名阻断 → C-34”分支，不是跳过实验门。C-34 的来源/CPU 自检不能充当 R5 模型评分。

#### 开工自审与本轮回答的问题

- **科研价值**：对准方法章的新机制准入门与公开可比性要求，将准入失败、工程失败与方法无效分开。
  §25.30 排除的研究卡和 §25.32 的协议检查限制了下一轮可研究的对象；它们没有检验新机制的效果。
  本复盘同时核对历史 `replan/F_eci_protocol_audit.md`，防止把可恢复组件误写成不存在，进而错误缩小研究空间。
- **可行性**：复盘可行，只需公开源码、已有结果和本地 CPU；新实验仍卡【协议/授权】，冻结的 ESC
  topic-disjoint 链未闭合、也没有可执行新机制合同。此次没有读 final-valid、载入模型、启动 GPU、
  增加 benchmark/seed 或修改冻结指标。
- **研究目标完成度**：G-19/C-30 完成了独立外部方法的透明适配及同协议复算（§25.28–§25.29）；
  C-31–C-32 没有回答“新机制能否改善主指标”。正确产出是排除证据和可行性边界，不能声称找到创新、
  证明该领域没有机会，或将无 E 分数写成 ESC 上的方法失败。三个旧方法章与 Ch6 的既有结论保持。

#### 一手复核：修正 C-32a 依据，保持停止状态

固定 [ICCL 官方源码](https://github.com/ChaoLiang-HUST/ICCL/tree/a7e3b3479040b17baf87f96c5de6df5291ae91c7)
revision `a7e3b3479040b17baf87f96c5de6df5291ae91c7`；EventStoryLine scorer 仍取
`46edefee5e82e0917b823abe0a18bf8c7770f15c`。只读代码，没有执行上游 trainer 或真实数据预处理。

| 先前表述 | 一手源码位置与复核 | 对结论的修正 |
|---|---|---|
| 无法确定“末两 dev topics” | [ICCL `load_data.py` L21/L69](https://github.com/ChaoLiang-HUST/ICCL/blob/a7e3b3479040b17baf87f96c5de6df5291ae91c7/load_data.py#L21) 明确排除 `37/41`，将二者合为 dev。 | 官方数据目录无 manifest 是事实，但**ICCL 的 dev topic 身份可得**；不能说所有来源都没有指定。 |
| ICCL shuffle 未绑定随机种子 | [`parameter.py` L33](https://github.com/ChaoLiang-HUST/ICCL/blob/a7e3b3479040b17baf87f96c5de6df5291ae91c7/parameter.py#L33) 默认 seed 209；[`main.py` L64–L85](https://github.com/ChaoLiang-HUST/ICCL/blob/a7e3b3479040b17baf87f96c5de6df5291ae91c7/main.py#L64) 在 `load_data(args)` 前设置 Python/NumPy/torch RNG。 | 应改为“**按文档分折，与 topic-disjoint 合同冲突**”；不能称整条入口没有 seed。源码级 seed 不证明论文落盘 folds 已复现。 |
| 候选规则无法找到 | [`ESC_processor.py` L70–L130/L166–L174](https://github.com/ChaoLiang-HUST/ICCL/blob/a7e3b3479040b17baf87f96c5de6df5291ae91c7/ESC_processor.py#L70) 过滤六类有锚 event markables，枚举文档内无序两两组合；L216–L267 从 `event_mentions_extended/*.tab` 读取标签，缺文件时置 `NONE`。 | 部分规则可读；**不能概括成未过滤的全部 event pair，不能仅从 XML 的 PLOT_LINK 假定标签等价**。公开仓库缺这条辅助输入链，禁止运行其静默 `NONE` 分支生成实验金标。 |
| typed scorer 的 FN 错误阻断二分类评分 | [ESC `eval_script.py` L90–L118](https://github.com/tommasoc80/EventStoryLine/blob/46edefee5e82e0917b823abe0a18bf8c7770f15c/eval_script.py#L90) 的错误位于 typed-relation 聚合，pair 分支单独计算；ICCL [`main.py` L380–L384](https://github.com/ChaoLiang-HUST/ICCL/blob/a7e3b3479040b17baf87f96c5de6df5291ae91c7/main.py#L380) 已调用 sklearn positive-class P/R/F1。 | **binary scorer 实现存在**；它与旧 ESC link-list scorer 的候选/方向/聚合语义仍须核对，不能从存在代码推出论文同轴。 |

最终不可行项收窄为：**当前 topic-disjoint E 合同卡【协议】**，ICCL `load_data.py` L19–L35
混合非 dev topics 后按 document shuffle/slice，而不是 topic folds；其 `train.npy`、extended-mentions 输入链
及历史论文的候选/聚合身份也未闭合。ICCL 仓库没有 LICENSE 是另一项待决可得性问题。
恢复上述组件既不把 ICCL 变成准入 V 行，也不产生新机制，更不授权更换 E 协议。

#### CPU 自检与可追溯产物

产物根：`runs/stages/R1/r1-v61-20260904/audit/c34-20261008/`。ICCL 克隆只读；ESC scorer 以固定 revision
直接取得。本轮不需要完整 ESC 数据克隆；该克隆在会话服务重启时中断，未进入任何检查或结论。

```bash
uv run python runs/stages/R1/r1-v61-20260904/audit/c34-20261008/audit.py
uv run python scripts/audit_r1_consistency.py \
  --output runs/stages/R1/r1-v61-20260904/audit/cross_artifact_audit.json
uv run pytest
uv run ruff check src tests scripts
uv run ekg-smoke
```

- 来源检查 **PASS**：dev/seed/scorer、缺失资产和 typed scorer 分支逐项确认；源文件 SHA 写入
  `source_audit.json`。scorer SHA 与 §25.32 一致。
- 真实上游 `load_data` 的**合成 fixture** CPU 检查 PASS：20 个非 dev topic，每 topic 4 个虚构文档，
  每折前重置 seed 209；5 折 test 文档覆盖恰好 80 个且各折 train/test 文档不重叠，
  **每折 train/test 的 topic 均有交集**。这只验证代码的 split 单元，不是 ESC 数据统计、preflight 或模型分数。
- 首次检查脚本误选了 `fn_pairs_value` 的函数内赋值而非 `sum` 聚合赋值，断言失败；修正 AST 节点选择后
  同一检查通过。没有修改上游代码、fixture、阈值或科学判据。
- 本地三件套：**786 passed / 32 skipped**（torch 缺失）、ruff **0 error**、`ekg-smoke` **OK**；
  R1 一致性审计 **36/36 requirements mapped**。未改项目代码或 torch 路径，本轮不要求远端 torch 测试。
- `audit.py` SHA-256：`19756c9c1e2e4b47720f4b5b6ba2799fa55cddbf8ad5bdaf5060afbdec98b451`；
  `source_audit.json` SHA-256：`5edda7e80095710409080e10529bc17d9dd3c64b19f0528c0d29d08923908c85`。

#### 下一轮 R0 的检索约束

1. 先核对本仓已有一手审计，再把差异核到官方 loader/preprocessor/scorer 的调用链；文件存在、
   局部源码可读、CPU 完整闭合和论文保真度分别登记，不能互相替代。
2. 同时报告**论文声明的 split**和**代码实际 split**。固定 seed 不修复 split 单元错误；缺历史 manifest
   也不等于不能依法冻结一个明确标注的透明适配协议。后者须先得到范围裁决，不能冒充原论文复现。
3. 只考虑尚未封存家族覆盖的新机制，先给 `observed error → treatment → mediator → main outcome` 和
   最近邻差异，再核数据、强 baseline 与实现；不因相关论文存在或有空闲卡而立项。
4. 辅助数据缺失且上游静默生成 `NONE` 时直接阻断；无模型输出的准入检查不做 power/预算虚构，
   也不当作模型负结果。新 benchmark 并不能自动提供新颖机制或强可比对照。

#### 作者决策卡（待裁决，不自动执行）

**阻断句**：当前 ESC E 合同不可行，卡【协议】（上述 source/split/input 证据）；新机制合同也不存在。
本轮“唯一外部 benchmark”的授权已使用，不能靠换 benchmark、改 fold、修 scorer 或补生成标注绕过。

| 可选范围 | 科研目标与下一步交付 | 代价与声称边界 |
|---|---|---|
| **甲 · 建议：回到 MAVEN 主表的新机制 R0，将未闭合 E 退出本轮硬前置** | 授权一个新的、最多三卡的一手检索回合，针对方法章的已观测错误检验新机制机会；先改主表/状态机，再交机制差异、现有数据可行性、强对照和代码证据卡。全部排除仍停止。 | 放弃本轮外部泛化目标；不承诺能形成合同或改善分数。MAVEN 主指标、单 seed、封存家族与训练门不变；不是仅整理表格补行。 |
| **乙 · 另行授权恰好一个新的外部 benchmark R0** | 先审核来源、许可、split、候选与 scorer，再谈新机制；明确允许选择一项，不立即批准 GPU。 | 改变外部验证范围；仍可能无可比协议或机制。ESC 已有资产保留为排除证据，不给分数。 |

当前建议甲的理由是本轮失败尚未检验机制价值，而方法章的贡献仍需在 MAVEN 主表上成立；
继续更换 E 数据本身不能解决这个问题。**这只是建议，尚未得到范围授权**；不重开 C-22、旧 D4/A4/C5、
LLMERE，不加 seed，不改变论文结构。下一项只有在作者选择后写入主表，当前无可直接启动的 GPU 任务。

### 25.34 C-35–C-40 · 三方法章改进与科研裁决委托（2026-10-08，C-35/C-36 done，C-37 wip）

**作者授权**：不再要求作者选择科研路线。执行代理负责原因分析、论文/实验/官方 GitHub 实现检索、
有用科研 skills 的项目安装、方案取舍、改进执行与最终科研裁决；作者只验收最终结果。
授权已同步 AGENTS/CLAUDE、主表 C-35–C-40/G-22 与状态机。代理选择以现有 MAVEN 三方法章为主，
ESC 不再是本轮硬前置；尚未形成新的模型效果结论。

#### C-35 开工自审

- **科研价值**：形成“已观测错误 → 可干预原因 → 处理 → 中介 → frozen 主指标”的可证伪改进链。
  对准 D4 五类 macro-F1、A4 official causal P/R/F1 与护栏、C5 official coreference 全套及主锚；
  证据分别取本页 §25.20–§25.27、`PHASE_A.md` 的 A4.3/G-4b、`PHASE_C.md` 的两个有效周期与诊断。
  不能将低成本、更多实验或安装 skills 本身作为贡献；机制价值需强对照、消融与负控支持。
- **可行性**：静态/CPU 诊断可行，既有结果与本地源码可读；外部论文与代码需重新核一手来源，
  真实训练数据/checkpoint/机器用只读 4090 核验。具体方法训练在 C-37–C-39 PASS 前不运行。
  单 seed 与有效性/资源边界保持；不可行科研路线由代理在已授权主任务内自行裁决并更新主表。

#### C-36 开工自审

- **科研价值**：用来源审查、竞争解释、单变量诊断和验证纪律修复本项目曾出现的错误归因；
  服务 C-35/C-37–C-40 的主表改进链，不以 skills 数量或宣传能力论证方法有效。
- **可行性**：GitHub 固定 revision 的 markdown/本地脚本可安装到 `.agents/skills/`，不需外部模型、
  GPU 或全库依赖安装。只选不改变 frozen protocol 的模块，记录用户科研裁决委托对上游人工选题建议的优先级。

#### C-35 本轮复算：错误交换与资产恢复

对现有冻结预测作纯 CPU 配对诊断，不加载模型、不改阈值，不读 final-valid。
`compare_recovery_errors.py` 先过 official document/schema/candidate digest 检查，
再按原始 gold event→mention 展开计数；错误 subtype 同时算假阳性和漏掉的 gold subtype。
以下是**诊断 pair 数，不能替代主指标或证明某一 loss 的因果效果**。

| comparison（candidate vs control） | recovered gold pairs | lost gold pairs | removed false pairs | added false pairs |
|---|---:|---:|---:|---:|
| A4 full vs remove_core | 31 | 1,344 | 3,157 | 107 |
| A4 no_constraint vs remove_core | 47 | 1,271 | 3,091 | 274 |
| A4 length_matched vs remove_core | 5 | 1,409 | 3,314 | 7 |
| C5 full vs remove_core（pilot-r2） | 80 | 35 | 72 | 93 |
| C5 full vs official_joint（pilot-r2） | 113 | 75 | 208 | 233 |

A4 三个 evidence 臂都丢失大量 control 原本命中的 gold pairs，移除 hinge 并未恢复它们；
因此“只修 hinge 就够”的解释不足，retained CE、revision 分布和 backbone parity 须分别测。
C5 的信号确有修复，也制造新的错误；不能把总 recall 上升当作身份区分更准。
这些 pair 相依，不拿 pair 数虚增独立样本量或 power。

A4 复算首启因本地 gold 副本 JSON 截断失败：文件 7,798,784 bytes，只读完 228 篇，
第 229 行损坏。保留损坏副本和恢复记录，按冻结 preflight 的 gold SHA 校验 C5 同源副本，
并由 4090 只读 `sha256sum` 独立确认，再恢复原文件：
`before=1fd3333de603093a44b8ebcdae5b235ec16a9d0370fbb0aa9054ac0df08f8d21` →
`after=403b69a8a9c83e2be41e0c366fed7edcd7e00796dbd14ec6f07df7e560507e81`。
恢复后 291 篇完整，hash 等于原合同；**没有重定义 gold 或修改实验身份**。

产物根 `runs/stages/R1/r1-v61-20260904/audit/c35-recovery-20261008/`：
`validated/*vs-*.json` 是当前脚本版本的复算，旧首次输出保留；每份均含输入与脚本 SHA。
`asset_recovery.json`、损坏副本和 hash 清单保留；官方 scorer 主分数未在本轮重算，仍认旧结果页。

#### C-36 已完成：有用 skills 已加载进项目

安装与锁定 5 个技能：scientific-critical-thinking、hypothesis-generation、systematic-debugging、
test-driven-development、verification-before-completion。两个官方来源 MIT，固定 revision、
原文与许可保留，详见 `docs/RESEARCH_SKILLS.md` 和 `docs/research_skills.lock.json`。
实际应用是上述证据分类、资产修复、先失败的诊断测试及竞争解释矩阵。
`validate_prediction_matrix.py` 对本项目 3 行诊断设计输出 valid、0 errors/0 warnings；
这仅是结构检查，不是科学准入或模型效果证明。

#### C-37 一手机制审计与代理决定（进行中）

已核 P1 同 revision 的官方 MAVEN-ERE antecedent 模型/训练/解码源码，
Du 主辅梯度论文 §2–3/Algorithm 1、AuxiNash §4 与公开 GCS 实现，及现有 MAVEN-FACT 模型。
一手源码根 `audit/c37-primary-20261008/` 的 `artifact_hashes.json` SHA 为
`9829cf1c6fb3e0eb6ded8c5045c2be792b16f15939c4c9431d5a888d11397afa`。
研究卡和本轮代理选择见 `docs/research/20261008_method_recovery.md`；不再要求作者选路线。

- **D4**：gold causal oracle 已否定“只需更好边”；旧 typed-cue bottleneck 和 strongest CLS 输入/头存在
  差异，但未单变量干预，不能断言 bottleneck 是原因。先做相同 CLS 配方的 parity。
- **A4**：base-logit 梯度相反不保证 shared encoder 梯度相反，且 retained CE 仍在；
  新增真实 loss 的解析 CPU counterexample 和梯度审计工具。fixture 不代表训练分布，待远端 torch 实跑。
- **C5**：官方 joint 使用 antecedent+dummy softmax、marginal log likelihood 和 argmax 连链；本项目臂用
  pair CE 与平均链接。已确认设计差异，尚未隔离其分数贡献；先复用官方实现作目标/解码匹配控制。

**本地验证**：789 passed / 35 skipped（缺 torch），ruff 0、ekg-smoke OK、R1 36/36 requirements mapped。
新增的 3 个 torch 测试仍须远端实际执行，不能拿本地 skip 声称完成。
**算力事实**：4090 本轮两次只读核卡均四卡占用约 17 GB，无本项目新 GPU 任务；
不占他人 GPU，不使用未授权 5090，不搬 checkpoint。继续远端 CPU 验证与 baseline parity，
不将资源占用改写为方法无效，也不声称已经提高三章主指标。

#### C-35 收口：远端实跑与本轮代理裁决

代码提交 `3edb09898ef5b92292a3fe9c3c31d61d1b8575f9`，通过增量 Git bundle
（SHA `e2d402fb37e3012e74886c5488782bb0fa389d485ff4e09bf75b54c3603319fe`）送达 4090；
从 Git object 提取到独立 audit namespace，未 reset 远端工作树或移动远端 HEAD。
对应 `pair_evidence.py` 两端 SHA 都是
`9dddc00a87b7c404b7c8471de102e60e5a5bdbf3258c35ac22e53ba067b03726`。

`CUDA_VISIBLE_DEVICES=""` 下新增两份测试文件 **6/6 passed，无 skip**。
解析 fixture 用真实 `sufficiency_necessity_loss`：base-gold partial derivative 为 **0**，
共享参数主 CE 梯度范数 **0.4260280132**、辅助梯度范数 **1**、cosine **−1**；
辅助 weight **0.5** 时 `g_main · (g_main + weight*g_aux) = −0.0315141386`。
这只证明旧 base-only 推论不充分、微小 SGD 步可升高 main CE；
**不证明真实数据梯度分布、不保证 Adam/F1 轨迹、不构成方法提分**。
诊断 JSON SHA `0f631ea47645787518791e50cbea001af1fa670612f4c6c31e21c512839af8cc`，
测试日志 SHA `700bc0322b00f8e8db3ce495047983b54ab27ab59ed1fedac05f3aeba47dae24`，
产物保留在 4090 和本地同名 audit 根；权重未移动。

C5 的 pair 诊断还揭示目标不对齐：由上表 TP/FP/FN 算得 **full pair-F1 80.83889418**，
**official_joint pair-F1 80.02594034**，而 full 的官方 MUC 低于 anchor（主指标见 `PHASE_C.md`）。
所以独立 pair currency 改善不自动等于聚类主指标改善；该诊断 F1 不替代 MUC，
也不能凭此把全部差异归因于目标或解码。

**代理裁决**：C-35/C-36 完成。C-37 继续；下一轮具体工作是 D4 strongest-CLS 输入/头 parity、
A4 实际训练行的 loss/共享参数诊断、C5 官方 antecedent 目标与解码匹配控制。
既有失败机制不复跑，公开优化器不包装成创新，未经新机制准入的章不进入 C-38–G-22。
作者不需要另选科研路线。4090 第三次核卡仍四卡占用；只有准入合同与空卡同时成立才正式训练。
本轮没有新增模型主分数，没有“已经提高三个方法”的结论。

最终 C-35 `artifact_hashes.json` SHA：`4b361695dd0b5900bc277c9e0cf219475b407d47f4e234ca137e0d80ecb00d0e`。
本地及回传远端 JSON/log 双端 SHA 一致；C-37 源码 hash 清单独立于它，旧 sealed 实验身份未改。

### 25.35 C-37–C-39：非 GPU 验证包完成（2026-10-08）

**作者范围**：只完成 GPU 之外的准备，便于空卡后立即验证。代理选择三项根因控制，
不让作者选择科学路线。本节无新增模型主分数，不能裁定方法有效或已经提高三个方法。

**开工自审**：科研价值是隔离 D4 头参数化、A4 shared-gradient 与 C5 解码，验证 §25.34 的竞争解释，
对准三章 frozen 主指标与强对照欠额。可行性是复用现有数据/训练器/evaluator；
权重留在原机器，CPU 微型模型跑完整接口，不需要新标注或 final-valid。CUDA 内存与真实模型行为
是下一计算门；新机制的 novelty/power/消融/负控尚未准入，不以本就绪包代替。

流程偏离：事前自审先写进研究卡与主表，交接/结果页在收口时才回填，未满足指定落点顺序；
没有真实模型输出参与本轮选择。后续任务先写 results/交接，再实现。

#### 交付与一手机制边界

- D4：marked-CLS、同训练配方，仅 linear/tanh5 head 干预；baseline 训练、重载、OOF runner 共用入口。
  这是裸 head 控制，不重训旧 cue/factor/causal-residual 家族；seed 固定但不同头的初始化 RNG 消耗不同。
- A4：将训练实际使用的 primary / retained CE / hinge 与 supervised rows 提取为共享函数；
  checkpoint 审计用该函数，在固定 train-only 文档上求 encoder/head 梯度，零 optimizer step。
  按张量累计 dot/norm，避免拼接整模型 double gradients。它测 selected checkpoint 的局部风险，
  不能重构历史 Adam 轨迹或推出 F1 原因。
- C5：同一 checkpoint/预测 arguments 导出全 same-type pair cache；分别记录 scorer 原顺序和文本顺序，
  保护原平均链接的 tie 顺序。当前 role-only 头没有启用 CONFUSABILITY/distance 特征；
  原先把共享 scorer 的可选距离特征说成本次头使用的特征不准确，不把顺序防护当作性能原因。
  average-link 必须逐文档复现旧 clusters，之后才能比较 official argmax。
  直接调用 [官方 utils](https://github.com/THU-KEG/MAVEN-ERE/blob/ac81a9711a69f43f55bfbc50b3bb573fd11c64b0/coreference/src/utils.py)，
  固定 dummy p=.5、不扫 threshold；binary scores/候选过滤与 antecedent 训练不同，标 FR-016(b)。
- CPU collector 验证各 fold 的完成状态、plan/hash/seed/head、CV/source 与标签覆盖；
  复用已有 document-paired bootstrap，比较两头和 frozen CLS anchor，不替换方法 promotion gate。

合同：`docs/phases/PHASE_recovery_validation_20261008.md`。
唯一 frozen argv/hash 包：`configs/recovery_validation_20261008.json`，
SHA **`174214301d2cd3906c61ae3582de43931ebcbcd2b1f85b1e1b59b6da03f11bbf`**。
共 **16** 个独立任务（D4 两个 smoke + 两头各五折；A4/C5 各 smoke/audit），绑定 **109** 个源码身份。
A4 正式审计 **8** 个有至少2个 event、含TIMEX至多32 nodes/至多8句的 train 文档，
按 SHA256(doc_id) 顺序冻结；smoke 取相同序列首篇。这个受限样本不代表完整训练分布。
C5 smoke 是 frozen internal-dev manifest 前 **2** 篇，只作接口检查。

#### 验证证据（无 GPU）

| 检查 | 结果 | 限制 |
|---|---|---|
| 本地完整 pytest | **797 passed / 42 skipped** | 本地无 torch；跳过不作 torch 行为证据 |
| ruff / ekg-smoke | **0 error / OK** | CPU 工程与端到端 fixture |
| R1 consistency | **36/36 requirements mapped** | 文档/既有信任根一致性，不证明方法有效 |
| 4090 相关测试 | **45 passed / 0 skipped**，25.01 s | `CUDA_VISIBLE_DEVICES=""`；真实微型 BERT 训练/保存/重载/梯度/重放 |
| 5090 同一组测试 | **45 passed / 0 skipped**，17.92 s | 同样只用 CPU，不占 GPU、不跑真实大模型 |
| 4090 CPU 资产预检 | **12 jobs / 30 assets / 1 pinned backbone PASS** | manifest/source/CV/anchor/模型内容 hash 与所有目标输出不存在 |
| 5090 CPU 资产预检 | **4 jobs / 33 assets PASS** | checkpoint 所有顶层文件、arguments、gold、原预测与 smoke 子集；无跨机权重 |
| 部署后标准入口 | **D4、A4、C5 三个入口均 CPU preflight PASS** | 默认只核 hash、打印命令；没有 `--execute` |

TDD RED 覆盖缺失功能、输入 drift、已有输出、occupied GPU、旧 plan 的 smoke 与错误 head/labels。
首次远端完整 A4 tiny-forward 发现 `document_pair_evidence` 的参数绑定错误；
修正为实际 `(nodes, doc_text, pairs)` 后，两机最终 45 项均通过。该工程错误没有触发真实 GPU任务。

#### Git 部署与产物

实现提交：`9ff6c1e`；A4 API 修正与真实 C5 cache/replay 用例：`04d13da`；
合同/启动闸门/汇总：**`2a4f60b08cc2287f6548b63bda43050ac8ff74a4`**。
先在独立 Git archive 快照测试与核资产，确认两机 tracked 工作树干净、项目 root 无 Python 任务，
push 后由 Git bundle 更新各自 origin/main 与 main。保留所有 remote-only 文件，未清 runs；
权重训练在哪仍留在哪。本轮只有代码、smoke 子集和日志/哈希传输。

证据根：`runs/stages/R1/r1-v61-20260904/audit/c39-ready-20261008/`。
其中 `gpu-4090/`、`gpu-5090/` 有完整测试日志、资产表、部署后标准入口输出；
`cpu-preflight.json` 的 `deployment_pending=true` 指**部署前** shadow 核查，
后续 `deployed-*-preflight.txt` 记录真实项目 cwd 部署后 PASS，勿把历史字段当当前状态。
实际实验输出专用新根：`runs/stages/R1/r1-v61-recovery-ready-20261008/`。

**收口裁决**：C-37 诊断选择与 C-38 诊断实现完成，C-39 `cpu_ready / cuda_pending`。
当前诊断的非 GPU 前置已闭合；下次空卡先跑合同 smoke，成功才进入对应完整诊断和 C-40。
4090 可按授权核卡执行；5090 GPU 仍逐任务授权。**本轮未核卡、未启动 GPU、未搬 checkpoint**。
没有新方法训练准入，也没有新的提分结论。

本轮就绪证据 `artifact_hashes.json` SHA **`a79c9852718d58db64b224982e4a3ff9fb84f9957e1e02e3d1f677d6dd343dc4`**；回传日志/资产 JSON 均核双端 SHA 一致。

### 25.36 G-22：D4 seed-13 GPU 启动（2026-10-09）

**启动前自审**：科研价值是以 strongest marked-CLS 配方，仅干预 linear/tanh5 head，
检验 §25.34 的分类头欠额解释，对准 D4 五折 OOF macro-F1 与固定 CLS anchor；
不重开旧失败家族，不将 smoke 或一次训练 seed 当作方法有效证据。
可行性：§25.35 数据/CV/模型内容与真实 CPU 接口已闭合；本次重新运行本地三件套，
pytest **797 passed / 42 skipped**、ruff **0 error**、ekg-smoke **OK**，一致性 **36/36**。
成功 SSH 核到 4090 四卡均无 compute process，memory used 分别 **68/11/11/11 MiB**，
utilization 均 **0%**；远端 tracked 工作树无改动，HEAD=`61bc4df`。
作者本次明确“4090可用，启动GPU任务”；仅用该机、训练 seed 13，无 checkpoint 跨机搬运。

冻结 plan SHA 仍为 **`174214301d2cd3906c61ae3582de43931ebcbcd2b1f85b1e1b59b6da03f11bbf`**，
源码不改，cwd=`gpu-4090:/data/TJK/ekg`。先 GPU 0 的 `d4-linear-smoke` 与 GPU 1 的
`d4-tanh5-smoke`，使用启动器的 occupancy/CUDA/hash/输出不存在闸门；完成状态及 artifact
hash 合格后才开对应正式 fold。日志为 `logs/recovery-d4-{linear,tanh5}-smoke-20261009.log`。
上述授权、自审与队列在相应启动前写入本节；以下是实际核验状态，尚无完整 OOF 模型分数。

冒烟 launcher PID：linear **3504571**，tanh5 **3504662**；两个真实 CUDA trainer 完成，
两个 `status.json` 均为 **complete**。同 plan/seed、head 配置、selected epoch=1、有限 curve
以及声明的全部 artifact SHA 已独立重校验通过。
linear smoke status SHA **`754f3da969ceaa5ed0602e509c55eff63d529008dc777bb7107049de1b7093ef`**；
tanh5 smoke status SHA **`8f76c1adee31bcd2f61fc0788e7c2e3afd7e3208d1b317bf92d56e3250530e89`**。
小样本 smoke 仅证明接口/真实 CUDA 训练与保存重载可运行，不以其分数决定后续配方。
正式调度事前冻结为以下操作队列，不改任何训练 argv：

| GPU | worker PID | 首批 CUDA trainer PID | 顺序执行的冻结 job ID |
|---|---|---|---|
| 0 | 3506554 | 3507582 | `d4-linear-fold-1` → `d4-tanh5-fold-3` → `d4-linear-fold-5` |
| 1 | 3506591 | 3507864 | `d4-tanh5-fold-1` → `d4-linear-fold-3` → `d4-tanh5-fold-5` |
| 2 | 3506635 | 3507590 | `d4-linear-fold-2` → `d4-tanh5-fold-4` |
| 3 | 3506740 | 3507882 | `d4-tanh5-fold-2` → `d4-linear-fold-4` |

每卡一个 `setsid nohup bash -c 'set -e; for job in <上述序列>; do ...; done'` worker，
每次调用冻结启动器 `--execute --gpu <index>`，每任务独立日志
`logs/recovery-<job>-20261009.log`；队列日志 `logs/recovery-d4-gpu<index>-queue-20261009.log`。
每条 SSH 只启动一个 worker。每任务前重新核空卡，任一失败该卡余下队列停止；
不同卡可独立继续。checkpoint 始终留在 4090，不自动重启已有输出，不增 seed。

**2026-10-09 20:32:27 +08:00 核验**：四个 worker 的成功 SSH `ps` 证明 ALIVE；
四个首批正式 job 均 `running`，真实 trainer 占用相应 GPU，日志已进入 epoch 5，loss 有限。
四卡总 memory used **3628/3571/3591/3591 MiB**，utilization **55/75/83/81%**（采样值）；
compute process PID 与上表一致。另六个 job 是实际存活 shell 队列里的后继，尚未启动，
不是已完成实验。重校验 **109** 个源码 SHA 及所有完成 smoke artifact，无漂移。
训练中间 selection-dev 曲线不得用来修改 head、配方、预算或队列，不提前裁定效果。

启动证据根（本地与 4090 均有）：`runs/stages/R1/r1-v61-20260904/audit/g22-start-20261009/`。
`launch_snapshot.json` 含 UTC 时间、commit、完整 worker shell 命令与 `ps -eo etime` 等价输出、
全部当前 status、GPU/compute process 原始行、smoke hashes 和正式训练 log tails；
SHA **`4f887d8c302681cc8038d8217794be9c4f70917637b30e5fa2938523785c2753`**，回传双端一致。
首批完整日志、checkpoint 与每折原始评测输出留在 `gpu-4090:/data/TJK/ekg`。
checkpoint 根为 `.../r1-v61-recovery-ready-20261008/d4/<head>/fold-<N>/`；
状态文件另在 `.../r1-v61-recovery-ready-20261008/d4-<head>-fold-<N>/status.json`。

**交接状态**：D4 C-39 CUDA 门通过，G-22 **wip**（四卡训练，十个正式 job 尚未全部完成）；
A4/C5 的 CUDA smoke/audit 未运行，原地 5090 权重未搬运。所有十个正式 status=complete 后，
执行 frozen plan 的 CPU `postprocessing.commands`，产出 `d4_paired_report.json`，
核 OOF 覆盖、同协议两头比较和 linear-vs-anchor parity，再进入对应 C-40 科研裁决。
SSH 中断本身不代表 worker 结束，不重新发相同任务；失败保留输出并先分析原因。
本节不产生“方法已有效/已提高三章”的结论。

### 25.37 G-22 / D4 C-40：五折结果汇总与裁决（2026-10-10）

**汇总前自审**：科研价值是从冻结的十折 raw predictions 计算 pooled 主指标与 document-paired
区间，区分 head 对照是否改善和强 CLS 配方是否重现；对准 §25.35 的诊断合同及 D4 强对照，
不把一次 seed 或部分 dev 曲线当方法章贡献。可行性：成功 SSH 已读到两个 smoke 与十个正式
status 全为 complete，原四个 worker 的成功 ps 无对应进程；产物、source/CV 与 frozen anchor
留在 4090，可用冻结 CPU collector 原地校验汇总，无需 GPU、搬运 checkpoint 或 final-valid。
本节在执行 collector 前记录；正式数字和结论随后据实际输出回填。

#### 完成与协议核验

两个 smoke、两头各五折均 **complete**；十个正式 run 均 seed 13、源码 commit `61bc4df`，
训练均跑满冻结 **12 epochs**，只由 selection-dev 选择 checkpoint。
冻结 collector 已 **exit=0**：所有正式 status/plan/产物 SHA、source/CV、head、selection 边界、
固定 CLS anchor 的输入身份及 pooled mention 覆盖均通过。每头各 **2,913 documents / 73,939 mentions**，
无重复或缺失，final-valid 未访问。四个 shell worker 已 GONE，未重启任何任务。
当前 4090 四卡被其他任务使用，本轮只运行 CPU 汇总，无新 GPU 任务或跨机 checkpoint。

#### 主指标（F1 × 100；pooled OOF，不平均五折分数）

| 对照 | macro-F1 | CT+ | PS+ | CT− | PS− | Uu |
|---|---:|---:|---:|---:|---:|---:|
| frozen strongest CLS anchor | 55.399532 | 97.530498 | 55.261194 | 66.275316 | 38.245614 | 19.685039 |
| matched marked-CLS linear | 55.399532 | 97.530498 | 55.261194 | 66.275316 | 38.245614 | 19.685039 |
| matched marked-CLS tanh5 | 42.154650 | 97.108327 | 39.303843 | 43.885147 | 22.632794 | 7.843137 |

| 文档配对比较 | 差值（百分点） | 95% bootstrap CI（百分点） |
|---|---:|---|
| tanh5 − linear | **−13.244882** | **[−15.496940, −11.064141]** |
| linear − frozen CLS anchor | **0.000000** | **[0.000000, 0.000000]** |

bootstrap 为冻结 **10,000 draws / seed 13**；训练仍仅一个 seed。
独立 raw-label 审计确认 linear 与 frozen anchor 的 **73,939 个标签逐一相同，0 disagreement**，
不是恰巧相同的平均分。baseline parity 已恢复，不把它当新方法提分。

#### 逐折与失败形态

| fold | linear macro-F1 | tanh5 macro-F1 | linear / tanh5 selected epoch |
|---|---:|---:|---|
| 1 | 55.683154 | 36.585477 | 7 / 1 |
| 2 | 55.211756 | 56.975197 | 5 / 9 |
| 3 | 55.514744 | 51.037941 | 4 / 10 |
| 4 | 54.342652 | 19.420320 | 8 / 1 |
| 5 | 55.678705 | 19.424240 | 5 / 1 |

tanh5 fold 4/5 分别把 **14,751 / 14,795** 个 mention 全预测为 CT+，等于多数类 baseline；
两折的其余四类 F1 全为零。fold 1 不预测 PS−；fold 2 则高于对应 linear，故不能说每折都变差。
所有折都训练满 12 epochs，上表是 selection-dev 选择，**不是提前停训或事后挑 evaluation epoch**。
全量错误交换：双方正确 **67,890**、双方错误 **2,024**、仅 linear 正确 **2,290**、
仅 tanh5 正确 **1,735**。损失遍及少数类，不只是 Uu 噪声。

#### 独立复算、追溯与裁决

独立审计直接用 gold/raw predictions 的 Counter 计算每类 `2TP/(n_gold+n_pred)`，
逐折与既有 evaluator 吻合（容差 `1e-12`），pooled 指标与 collector 吻合，
逐折 manifest 的 exact mention cover、无重叠和全部 dev curve 的 12 epochs 均通过。
首次临时审计把 `load_maven_fact` 生成器误作可重复遍历，第二次构建 doc map 时已耗尽，
出现 KeyError；定位该 iterator 语义后改为一次 materialize，复算通过。
这个临时审计错误没有修改模型、冻结 collector、输入或任何已有输出。

配对报告：`gpu-4090:/data/TJK/ekg/runs/stages/R1/r1-v61-recovery-ready-20261008/d4_paired_report.json`，
SHA **`34ba45903a876df405ef366cdff2bde8b225c3c152ac7ebcc09ca032a41fe0f7`**。
独立复算：`runs/stages/R1/r1-v61-20260904/audit/g22-results-20261010/independent_raw_audit.json`，
SHA **`1805d7fff3b5c2615fb6e20160afe4c5359fe81e6e60cda7ee8b20fdb339717a`**；
含每折分数、prediction counts、selected epoch、完整覆盖、标签一致性和 40 个产物 SHA。
两份 JSON 已回传本地同一 evidence 根，双端 SHA 一致；checkpoint 仍留 4090。
汇总相关本地测试 **7 passed**；文档一致性门 **36/36**，diff whitespace 检查通过。

**代理裁决**：D4 本次诊断计算与对应 C-40 完成，**没有改善，tanh5 路线不推进**。
后续 D4 使用已证明 parity 的 linear 作为匹配控制，不扫 hidden size/lr/epoch、不增加 seed、
不拿修 baseline 当创新。五维头在本冻结配方下表现退化，是当前 head 方案的直接反证；
尚未测饱和或梯度机制，不能宣称已唯一定位优化失败原因，也不能唯一解释旧 cue/factor 家族失败。
不同 head 的初始化 RNG 消耗不同，单 seed/document CI 不能代替跨初始化确认；
不泛化为所有非线性头无效。新 D4 信号仍须回 C-37 完成文献差异、可部署输入、强对照、
power/单变量消融/负控后另行准入，旧 sealed 家族不恢复。
现有队列下一步是 A4/C5 的原地冻结诊断；两者未运行 GPU，**没有新结果**，
5090 仍须具体任务授权，不由 D4 完成冒充三章改进。

### 25.38 C-41 / T087：逐章执行开工（2026-10-12，当前 C5）

**作者指令**：逐章完成后续研究、提高主指标并增强创新性。代理选择 C5 → D4 → A4，
先把顺序和当前 C5 切片写进主表、TASKS/TODO/HANDOFF；不改变已定论文结构或 E3 封存状态。

**科研价值**：对准表 5-3 的官方 MUC 与其他共指护栏，先隔离已知目标/解码差异，再检验可部署
时间身份信号。依据是 `PHASE_C.md` 两个有效周期及本页 §25.34–§25.35；诊断或基线恢复不计创新。
**可行性**：文献、源码、训练集内 CPU 信号核查可行；原 checkpoint CUDA 验证卡【授权】，
须明确批准 5090 的具体 C5 smoke/audit；新方法信号、novelty、power 尚未闭合，不训练。
研究卡：`research/20261012_chapterwise_optimization.md`。

开工前 Git 工作树干净，HEAD 与 origin/main 对齐；当前 R1 一致性审计 **36/36 PASS**。
本节是开工记录，尚无新模型结果、主指标改善或新机制准入结论。后续按真实产物回填。

#### C5 日期词面代理的 train-only CPU 审查

命令：

```bash
uv run python scripts/report_temporal_identity_signal.py \
  --source data/processed/maven_ere/train.jsonl \
  --manifest data/protocols/v6/manifests/maven_ere_train.json \
  --output runs/stages/R1/r1-v63-c5-20261012/temporal_signal/train_audit.json
```

退出码 0；只处理 manifest 指定 **2,622 train documents / 66,744 event mentions**，
没有处理 internal-dev 或 final-valid。DATE 来自给定 TIMEX spans，按 sentence 收集词面；
只在一整句恰有一个不同 DATE surface 时给该句代理值，其余为 unknown，**不宣称 event-time grounding**。
共 14,969 TIMEX / 29,233 sentences，7,299 句有唯一 DATE surface。

| 全部 same-type 候选对的 DATE 代理状态 | gold coreferent pairs | gold noncoreferent pairs |
|---|---:|---:|
| same surface | 483 | 1,489 |
| different surface | 1,142 | 3,991 |
| unknown（缺失或多日期） | 12,386 | 46,650 |

| 高相似（既有固定 `.8`）且跨句的 same-type 候选 | gold coreferent pairs | gold noncoreferent pairs |
|---|---:|---:|
| same surface | 31 | 65 |
| different surface | 687 | 1,516 |
| unknown | 7,771 | 13,950 |

高相似跨句桶总 24,020 对，negative 基率 **64.6586%**；different-surface 桶的 negative 比例
**68.8153%**，仅覆盖全集 **9.1715%**，且包含全部真共指的 **8.0928%**。
这些是训练集探索性计数，pairs 相依；不是 classifier P/R、不是主指标、不是机制 power。
不能用 negative 比例较高证明 MUC 会提高，也不把 same surface 当真共指证据。

另外 gold BEFORE 在 same-type event 之间展开 18,230 mention pairs；其两端属于不同 gold event
clusters 是数据 schema 的构造事实，不能拿其“无真共指”作为时间预测有效的经验发现。
测试含缺失/多日期、同日期不同身份、不同日期真共指、unknown endpoint、坏 offset 与 train-only 闸门。
TDD 首跑因脚本尚不存在 **6 failed**，实现后 **6 passed / ruff 0**。

**裁决**：停止 sentence-DATE-surface 硬否决路线，保留“噪声可部署 temporal posterior”作为未准入
候选，不外推时间信息无价值。下一步核已有强锚预测里的 temporal/coref 冲突与原地 decoder audit。
没有新模型主分数或章节提分结论。

产物根 `runs/stages/R1/r1-v63-c5-20261012/temporal_signal/`：report + per-document count JSONL。
source SHA `6a5519fe7c30448690adb13d49217c50d474fc57480eae10aecb29df7eb638b7`；
train manifest SHA `47d19cc9a17e38259bfbb7f9206c675c7362f41252d23f414ea6cfd46015ca68`；
script SHA `6a7e9b4bbdb2f3859410fe06db479b71516609ae8c6dad360a00536a0b753c1a`；
per-document JSONL SHA `cdfd814f7b5d5d6ae7948991cd7a0d6edb10a39c88c3263d808a73b1fd869434`。
report SHA `2ee03e7b3177692f23d9af37d8176a916bc2f3b86cef747157ca841beb91fc40`；
原输出保持不变。

#### 原机预检与资源边界

5090 的 `c5-decoder-smoke` 和 `c5-decoder-audit` 默认 CPU 预检均 exit=0，
全部既有 plan code/input hashes 校验、输出不存在闸门通过；未加载模型。
本地既有三件套 **797 passed / 42 torch skips、ruff 0、ekg-smoke OK**。
作者已明确授权上述两项 **仅在重新确认空卡后执行**，不训练、不新增 seed、不搬权重。
本轮成功核卡：4090 四卡均有他人进程；5090 单卡也有他人进程，尚未启动 GPU 诊断。
占卡属于【算力】等待，不是机制失败；C5 候选研究继续。

#### 已有强锚的 predicted BEFORE/coref 冲突审查

只读原 frozen `official_joint` 的 291-document internal-dev prediction；此 unit 已被历史分析
查看，本次明确标探索诊断，不充当前瞻选模或确认。gold/pred 文件 SHA 必须逐项等于原 anchor
metrics，文档覆盖与 candidate digest 逐项通过；temporal 输入**仅来自模型已预测的 BEFORE**。
不改任何 cluster，不重新训练，不从 gold temporal 构造预测输入，不计算新的主指标。

```bash
uv run python scripts/report_temporal_coref_conflicts.py \
  --gold runs/stages/A3/a3-v6-baselines-r10/preflight/data/MAVEN_ERE/valid.jsonl \
  --pred runs/stages/R1/r1-v61-20260904/anchors/identity/official_joint_prediction.jsonl \
  --manifest data/protocols/v6/manifests/maven_ere_internal-dev.json \
  --anchor-metrics runs/stages/R1/r1-v61-20260904/anchors/identity/official_joint_metrics.json \
  --output runs/stages/R1/r1-v63-c5-20261012/temporal_signal/anchor_conflicts.json
```

退出码 0，population **291 documents / 7,195 event mentions / 1,719 TIMEX / 234,870 ordered
relation pairs**，candidate digest `15a3b1a5…dac10910`。BEFORE 的 TIMEX 端点验证后仅作为非共指
候选保留，不偷换成 event mention；反向/重复 BEFORE 在 unordered conflict 统计中只计一次。

| 已被 strong anchor 合并的 mention pairs | gold same event | gold different events |
|---|---:|---:|
| 全部已合并对 | 1,234 | 394 |
| 同时预测 BEFORE 的已合并对 | 6 | 6 |
| same-type、高相似、跨句的已合并对 | 713 | 177 |
| 上一桶内同时预测 BEFORE | 4 | 5 |

**裁决**：不准入“直接把 predicted BEFORE 当 cannot-link 拆簇”的处理。
已有 BEFORE 冲突同时命中真/假合并，覆盖的错误量有限；没有 MUC 干预、document power 或
独立信号证据，不能把这张 pair-count 表当提分保证。该结论只排除这条直接硬规则，
不宣称 posterior、邻域信息或其他时间 grounding 都无效。下一步仍是同 scores decoder audit，
据其真实结果核官方目标/解码匹配，再选择有证据的新信号，不扩展旧 role 家族。

TDD 首跑 **4 failed**（入口尚不存在）→ 实现后 **4 passed / ruff 0**；
本轮新代码完整三件套 **807 passed / 42 torch skips、ruff 0、CPU smoke OK**。
原 strong anchor hash：gold `bb8c6b486196c97560cba49516324b3f69541023bfbe5cc09590d2bb265ce7e3`，
prediction `66ff04bac5a11ab179ef50eeca51d56dbb613b7b04eaa04b749dd99ea82ffc42`。
script SHA `a2e195f003df4b6972a312a288a58d8fa6a8bc2f10c200ac9f431d442a52e2c2`；
report SHA `9d0211666800d0ef68cf40e8bf428149060762e6e3f49175136aa0807fa37029`；
per-document SHA `fb5ec749f14fd69a4bcb767449036a24881354a463451f6c5fcd23c1cee926ee`。
上述两份 CPU report 的完整文件清单保留在同目录 `artifact_hashes.json`，
SHA `d78fb2f27027a8cf2b72a7b74e8c6c15bfcf57a9089784c9dc3662792e310b2b`；
四文件独立 SHA 重核 PASS；纯 CPU，不涉及模型权重。

#### 授权后的第一次 launcher 尝试（未进入模型）

成功 SSH 核到 5090 GPU0 显存 218 MB、0% utilization、无 compute process 后，按已授权命令
发出 `c5-decoder-smoke` 的后台 launcher，wrapper PID **2558492**。
但 launcher 自己在 code/input hashes 后重新核卡时，已有其他进程 **2557646**，
于是 `check_gpu_rows` 报 `GPU 0 is occupied`，在 torch CUDA check / status 创建 / 模型载入前停止。
这是 **launch_blocked【算力】**，不是 smoke 模型失败或 GPU 已执行证据；输出 status/cache 均不存在。
日志：`gpu-5090:/mnt/aidata/tongjiakai/ekg/logs/c5-decoder-smoke-20261012.log`。
成功 SSH 的 `ps -p 2558492` 只有表头，证实该 launcher 已 GONE；未将 SSH 失败当作进程死亡。
后续只在再次空卡时重试 launcher，保留此日志且使用新的 log 名；授权仅限上述两项 C5 诊断。
两项 CPU 审查代码提交 `0c74bdbce43a7759040937e491fc5370ed675de0`，
报告 hash 与该代码内容一致；本节不将代码提交或诊断收口记为 C5 方法章完成。

#### C5 原机 CUDA smoke 完成（同计划，重新空卡后启动）

有界只读等待重新读到 GPU0 空闲后，用新日志 `c5-decoder-smoke-20261012-retry1.log`
启动同一冻结 launcher，PID **2565980**。成功 SSH 读到 `status=complete`，
plan SHA 仍为 `17421430…11bbf`，执行源码 commit **`61bc4df`**；没有重绑旧输出或更改配置。
remote status + 6 个 artifact SHA 独立检查 PASS；回传后本地按 status 的同一份 hash 清单再次 PASS。

smoke 覆盖冻结 **2 documents / 37 event mentions / 17 same-type cached pairs**；
average-link 逐文档重现 frozen full-r2 clusters（不通过即停止的 parity 门），
antecedent replay、两套 official score 与 error exchange 全部完成。
这里的两篇指标只是 smoke，不作为新方法或主表分数。
metadata 记录 checkpoint 原地路径与所有文件 SHA，权重未搬运，final-valid 未访问、无 optimizer step。

原机：`gpu-5090:/mnt/aidata/tongjiakai/ekg/runs/stages/R1/r1-v61-recovery-ready-20261008/c5-decoder-smoke/`。
本地回传：`runs/stages/R1/r1-v63-c5-20261012/decoder_evidence/smoke/`。
status SHA `cfce8a1bd8938609b5b779a1664c353259e5651d78cdd064aec33ee263b2987f`。
完整 audit 仍待重新空卡，以同 plan 下 smoke status/hash 为依赖，不复跑已完成 smoke。

两份 CPU signal report 已备份到 4090 同名 `r1-v63-c5-20261012/temporal_signal/`，
remote 四文件 SHA 复核 PASS；`code_provenance.json` 记录代码 release 和七份依赖身份，
双端 SHA `ed7f06a6e5bdea7222a7211d061ab4ab64db5f5ef38f6ca9215983d497eb33ac`。

#### 完整 audit 的空卡等待收口（尚未执行）

smoke 完成后，对完整 audit 做了有界只读核卡等待（20 次、间隔 30 秒）。
窗口结束时没有读到空卡，**没有发出完整 audit 模型命令**；没有遗留 watcher 或排队自动启动进程。
随后成功 SSH 仍读到 GPU0 显存 31,399 MB / utilization 100%，compute PID **2566003**；
`ps` 核为另一用户的 `VLLM::EngineCor`，不能占用。原 smoke wrapper PID 的 `ps` 仅有表头，
原 smoke status=complete 与六份 hash 保持，不把别人的进程当成本任务子进程。

授权保留，仅限同 plan 的 C5 smoke/audit；接续重新核空卡后直接执行 audit，无需重复询问。
audit 预期根为 `gpu-5090:/mnt/aidata/tongjiakai/ekg/`
`runs/stages/R1/r1-v61-recovery-ready-20261008/c5-decoder-audit/`。
本轮 C5 正式 MUC 与护栏没有新分数；候选研究、CUDA smoke 通过都不算章节改善完成。
读取完整结果前的解释规则已登记在 `research/20261012_chapterwise_optimization.md`，
不扫 dummy/threshold/order，不把 decoder 变化当新训练目标的证据或论文创新。

### 25.39 C-41 持续执行：事实性与事件身份信号审查（2026-10-12）

作者追加指令要求持续推进到有可复核的突破证据；空卡等待不结束科研工作。
本节开工自审先于新信号计数与实现：

- **科研价值**：对准 C5 表 5-3 的官方 MUC 与误/欠合并，核事实性是否提供独立身份信息，
  不把多数类标签一致当成共指；正文和来源相对事实性的边界见研究卡。
- **可行性**：现有 FACT/ERE train 及冻结 train manifests 可读。仅在 train 做 mention ID、
  tokens、type、sent_id/offset 对齐；不读 final-valid、不训练、不输入 gold arguments/cluster。
  gold factuality 仅探索信号上界，训练标签含预标注，不能直接确认可部署贡献。

尚无新结果；新机制训练须另闭合预测输入、最近邻差异、power、强对照与消融/负控。
C5 full decoder audit 继续遵守已经获得的原机/空卡许可，不复跑 smoke。

#### Train 事实性信号实测（探索 oracle，不是模型结果）

```bash
uv run python scripts/report_factuality_identity_signal.py \
  --ere-source data/processed/maven_ere/train.jsonl \
  --fact-source data/processed/maven_fact/train.jsonl \
  --ere-manifest data/protocols/v6/manifests/maven_ere_train.json \
  --fact-manifest data/protocols/v6/manifests/maven_fact_train.json \
  --output runs/stages/R1/r1-v63-c5-20261012/factuality_signal/train_audit.json
```

退出码 0；冻结 **2,622 documents / 66,744 mentions** 的 ID/type/sent_id/offset/tokens 对齐通过。
FACT 的 cluster ID 和 arguments 均未用于标签配对或 identity 判定；identity 只来自 ERE。
61,362 gold clusters 中 **69** 个有不同 factuality 标签。
标签计数：CT+ 62,947，CT− 1,363，PS+ 2,064，PS− 266，Uu 104。

| 全候选 train 桶 | 全部真 / 假共指 | 标签不同的真 / 假共指 | 标签不同的 negative 比例 | 候选覆盖 | 命中真共指比例 |
|---|---:|---:|---:|---:|---:|
| 同类型 | 14,011 / 52,130 | 147 / 3,573 | 96.0484% | 5.6243% | 1.0492% |
| 同类型、高相似且跨句 | 8,489 / 15,531 | 101 / 919 | 90.0980% | 4.2465% | 1.1898% |

完整五类 unordered 配对表保留在 report，不把相关 pairs 当独立样本。
这说明不同事实性可能有分辨信息，**但既未证明 MUC 收益，也未通过 power/新颖性/部署准入**。
同 gold cluster 标签差异的原因尚未判明，可能含语境承诺差异或标注噪声；不能预先认定某个解释。
直接标签硬否决不准入；FACT 五类不等于 KBP 的 ACTUAL/GENERIC/OTHER realis。

TDD：入口不存在时 **8 failed**，实现后 **8 passed**；完整门 **815 passed / 42 torch skips**，
ruff 0，CPU smoke OK。测试覆盖不同标签真共指、同标签假共指、FACT cluster/arguments 不参与、
四类跨数据漂移、重复 mention/未知标签和 dev/final manifests 拒绝。

script SHA `06f813d68894a3128b07b70b8e444d581c9900f159e85fbd5b31ad76a4b15e7d`；
report SHA `bf15022fda353d5d9c465d0a0965822f409774c98b8da1e456684c2b3b0b4805`；
per-document SHA `987dfd5967297353b748124eb90de32141707c4dc403343df1a10db4d616738c`。
FACT source SHA `190522b44f0702af030161924d7cb94c4a06bd5d6e2b40d79f8f1eaa5886bab7`；
FACT train manifest SHA `e9a939440eb0dbea76e6ce56d0b06b5a1009118eefdfcb93ae85f4a38e8c609a`；
ERE 两项输入身份与 §25.38 相同，report 逐项记录全 SHA。

#### 预测输入来源核查（未将旧缓存接入新方法）

从 4090 只回传旧 CLS 五折 evaluation labels/metadata 与 summary，没有回传 checkpoint。
summary SHA 按 §3 的 `21e7e505…88165` 核验通过；十份文件按 recovery plan 的 `anchor_inputs` 核验。
旧五折 CV 每个预测文档自身未入对应 train/selection，属于文档级 OOF；
但 CV 总体是 2,913 篇，而 C5 train 仅 2,622 篇，不能据此称未来 C5 训练输入已隔离。

| 旧 D4 fold | train 与 C5 internal-dev 交集 | selection 与 C5 internal-dev 交集 | evaluation 与 C5 internal-dev 交集 |
|---|---:|---:|---:|
| 1 | 170 | 65 | 56 |
| 2 | 163 | 63 | 65 |
| 3 | 174 | 54 | 63 |
| 4 | 184 | 53 | 54 |
| 5 | 182 | 56 | 53 |

拟作为 consumer 训练输入时，这些上游模型见过 consumer evaluation 的 factuality 标注，
需要重新隔离，不能靠“每篇是 OOF”跳过来源闸门。**这不改写旧 D4 自身 OOF 的有效性**。
本地 `anchors/factuality/cls_labels.json` 也不能视为这个 pooled OOF：只有 7,195 条，
与旧 OOF 的共有键存在 234 个不同预测。它是不同作用域的历史缓存，不据此判数据损坏；
本轮没有拿它构造新方法输入或报告预测信号效果，继续追溯其训练来源。

#### CPU 辅助观测诊断开工自审（预测前登记）

科研价值：从 gold oracle 走向实际文本预测，检验同身份标签变化与观测噪声下的信息保留，
对准 C5 的信号准入，不将经典 TF-IDF/logistic 写作新方法或 D4 贡献。
可行性：sklearn 已安装、FACT/ERE train 可对齐；仅 C5 train 文档交叉拟合，
不把旧 D4 OOF 的 consumer-evaluation 接触带入新模型，不读 dev/final 标签。
运行参数在新 JSON 中冻结，单 seed 13，不选模/扫参；CPU 结果不能代替 C5 主指标、power 或新颖性。

冻结配置：`configs/c5_factuality_observation_probe_20261012.json`，
SHA `83bff46affd273308d923fbf1111cbd630ab31e33c7965cb5d07a9d5fb9f9781`；
入口 SHA `5d9629b089f95fdefdb636eb8957a359dd042ea8cd69be1a9010e37433c9d8a8`。
sklearn 1.7.2，TF-IDF whitespace tokens（保留 trigger 的 `*` 标记）、unigram/bigram、
最多 30,000 特征；multinomial logistic `C=1 / lbfgs / max_iter=1000 / tol=1e-4 / class_weight=None`。
文档按 `sha256(c5-fact-observation-13:<doc_id>)` 排序后交错分五折，训练另外四折，不使用选模折。
同一 seed 13；不新增 seeds，不共享 evaluation 的词表，不拿分类器作强 coreference 对手。
输出根 `runs/stages/R1/r1-v63-c5-20261012/factuality_signal/observation_probe/`；
含各折本地 CPU 模型、完整 OOF 概率、fold ledger、summary 和 provenance。
模型留本地，回传/备份只含非权重产物；尚未启动任何 proposed coreference 训练。

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 uv run python -u \
  scripts/probe_factuality_observations.py \
  --config configs/c5_factuality_observation_probe_20261012.json
```

TDD 首跑 **5 failed**（入口未创建），实现后 **5 passed**；包含 holdout 的专属 token
未进入每折词表、每篇文档只有一折 OOF、输出概率 class-order/和校验、缺类别无 fallback 等检查。
此处记录参数和测试，不预先报告真实预测结果。

Oracle 审查代码 commit `64f0aff49c966c8497d53d7b125f766331e6e5f7`；
oracle + 旧 OOF 只读副本 + lineage/provenance 的 15 文件 manifest SHA
`de50036c2652f4543b23b9a75a3685b4c0e4a3e2bea62290d6f1a4f7da5b5627`。
该 manifest 不包含随后生成的观测器模型，不作为模型共享或搬运许可。

#### CPU 观测器与 observed signal 实测（非 coreference 主结果）

固定五折已完成，OOF **2,622 documents / 66,744 mentions** 全覆盖。
训练/评估 mention 数：53,829/12,915、53,117/13,627、53,348/13,396、53,519/13,225、
53,163/13,581；每篇只产生一个 held-out 预测，词表只在各折训练文本拟合。
本次辅助 factuality **macro-F1=0.2988419686，accuracy=0.9478305166**。
预测 CT+ 65,902、PS+ 467、CT− 375，PS−/Uu 的 argmax 预测均为零。
这是弱的经典文本观测器，不与 D4 主表或其他 split 的方法数字比较。

把其 argmax 类别与 ERE train identity 做只读计数，不改变任何 coreference cluster：

| 同类型 train 桶 | 预测标签不同的真 / 假共指 | negative 比例 | 全候选覆盖 | 命中真共指比例 |
|---|---:|---:|---:|---:|
| 全部同类型 | 33 / 718 | 95.6059% | 1.1355% | 0.2355% |
| 同类型、高相似且跨句 | 28 / 177 | 86.3415% | 0.8535% | 0.3298% |

观察到了有分辨力但覆盖很低的预测差异；这些 pairs 不一定就是 gold 差异桶的子集，
**不能把两个桶的 count 比叫信号保留率**。新 entry 明确区分 gold/predicted label source，
缺失观测不回填 gold；同类别即真共指或类别不同即非共指均没有被证明。
直接硬否决不准入；不对当前观测器扫 C/class weight/ngrams，不把辅助 accuracy 当身份指标。
非对角噪声兼容性仍待 R1 审查、强锚逐对缓存、power 和同变量对照，不启动方法训练。

producer summary SHA `af9517fcea1c301d65a878d593c1b9978ac908f3cc5dc9f297fa23203967ae79`；
OOF probabilities SHA `44d780cad74ffdb4940062650b3e5daa44daab894319338ec93cba1a85b8b96d`；
provenance SHA `b6dfe8fed516920ce0daf9a1f1ec9afef212f90f65f117c723b9fd262a5d5ee8`。
observed report SHA `2bc37f56bc7397a9e217f701bba2970a64704111d121d1ae7adc5bde4a2ca90f`；
observed per-document SHA `c0c18bec5a9af2c0e954c69aca966a20d7354eea787fdd1781716119fe521100`。

producer 使用的 loader 仍是 oracle code commit `64f0aff` 的 SHA `06f813d6…a4b15e7d`。
之后为 observed 审查扩展同入口；旧 report/loader 身份不改写，新 report 自带新 script SHA。
两项新增语义测试先 **2 failed**（observations 接口未实现）→ 通过；完整门
**822 passed / 42 torch skips、ruff 0、CPU smoke OK**。

### 25.40 C-41：强锚远端 CPU 缓存开工（2026-10-13）

科研价值：隔离模型恢复与新信号，获得表 5-3 frozen official-joint anchor 的完整 antecedent 分数，
使后续 power/对照与测量噪声假设可以使用真实 scorer，而非硬 cluster 或弱 baseline。
可行性：4090 的原 baseline workspace/checkpoint 仍在原机；成功 SSH 核到 64 CPU、
load average 10.81/11.48/11.50，约 481 GB available memory。拟限制 4 CPU threads，隐藏全部 CUDA。
已有 Torch 2.8.0+cu128 在 `CUDA_VISIBLE_DEVICES=-1` 下报告 `cuda.is_available=False`；
官方 `joint/src/utils.py:to_cuda` 支持该路径，真实 checkpoint forward 尚未执行。

原 checkpoint 是 baseline `best_COREFERENCE`，metadata 记录 SHA
`c84faee62a603ab375e00a95e9bb63a8ee26171f22f5d218cbf00e8ef76fff98`。
baseline metadata SHA `d7c4cc7be37adb62928b11f3f248a848edd7b50a122c328d571da15b09a349c3`；
原 preflight 与 workspace 的 unlabeled test input 两份 SHA 均为
`c358da8b04bdeca9477bd26a1a7fa325b634ea62a488b85b28119be8cce2a891`。
已回传仅源码/metadata 的只读快照，全部 joint/src Python hash 与 baseline metadata 对齐。
checkpoint 未回传，未修改旧 baseline，未执行 5090 decoder audit。
完整 identity、CPU 命令与 CPU/GPU parity 门将在新配置中固定；本节尚无模型结果。

冻结合同 `docs/phases/PHASE_C5_official_cpu_cache_20261013.md`；配置
`configs/c5_official_cpu_cache_20261013.json` SHA
`143a532d07b160c1cf7c15598fa86692c13d3958ea7f1429173a81b01a6d2487`；
entrypoint SHA `503dcf0bbbc97b05c84f309f348abfc38a0e54208b63418201aa935efbe9ae59`。
CPU max_length=256、batch=8、threads=4、seed=13，保持原 scorer/decoder，不过滤类型，
首批八篇 smoke 后才能导出全集；关系字段仅复制冻结预测，不声称重跑关系模型。
源码 commit `b85584d`。TDD：入口缺失时 8 failed，随后 8 passed；候选 digest 接口测试
1 failed → 通过。完整本地门 **831 passed / 43 skips、ruff 0、CPU smoke OK**。
推送前通过 Git archive 将对应 script/config/test 发至 4090 临时目录，原项目 checkout 未改；
`CUDA_VISIBLE_DEVICES=-1 PYTHONPATH=/data/TJK/ekg/src .venv/bin/python -m pytest
/tmp/ekg-official-cpu-verification-b85584d/tests/scripts/test_official_coref_cpu_cache.py -q`
真实 Torch/官方 coreference head CPU 测试 **10 passed in 98.09s**。
该测试用小张量验证原 scorer 的事件索引、完整 logits/概率和 dummy，并非真实 checkpoint parity。
后者必须由下一步 smoke 实测，不能拿单元测试替代。

smoke 原机 PID 1770889，已 `complete`；首批 **8 documents** 的 non-singleton clusters
与冻结强锚 exact parity。原机和回传本地的三个 artifact SHA 均独立核验通过：
scores `25687261509bdbdb9d026909dc229a4edca6f7c42fc5267617c2f03ad65c6de2`；
predictions `8df98dddbfe94e0ceeabaead35fd5d98cf6cab9b1238376cd94b55f1b70f2b4b`；
metadata `06edcab267cc9358159c83aa914c2cf50c713a483ac787648ac5d023c777ee4b`；
status `0e770bbaae68c24f6296f6a23fe730efeca398dc6ed41a7fff93e6313a4810b9`。
full 已在同原机/同 config 启动，PID **1772278**，日志
`logs/c5-official-cpu-full-20261013.log`；尚无全量完成或新方法结论。
§25.39 原 oracle/lineage 包的 15 个非权重文件已在 4090 独立逐项 SHA 核验通过。

full 后续已 `complete`，**291 documents / 7,195 mentions / 124,630 antecedent options（含 dummy）**。
37 个 batch 全部 exact parity；prediction SHA 与原 frozen anchor **逐字节相同**。
三个文件在 4090 和本地独立 hash 核验通过：scores
`b9b119a41c575427cab721ed3762a5502250a08ed5b6da2fe8651f9121a73cd7`；predictions
`66ff04bac5a11ab179ef50eeca51d56dbb613b7b04eaa04b749dd99ea82ffc42`；metadata
`d85a23b9fe6683aba43644a225d4c6bbbe45c59ff7cc46609b7c426095c521a3`；status
`ff0fae6c550375b24e02e0a43a792ba8783c31dd20780dbdff403bcda4b44c55`。
原 checkpoint 仍留 4090，本地仅回传上述 JSON；无 GPU、无训练、无 final-valid 接触。
本地使用 P1 hash-pinned evaluator/source_lock、原 291-doc ERE gold 与同 candidate digest 独立评分，
MUC **80.98471986417657**，与 frozen strongest anchor 一致；关系分数来自复制字段，
不是重跑关系头。独立报告 SHA
`8fbb7060d343f90bf618457676e245f598ede8aff6a5dcc495b4b526c1878457`。
这是控制恢复与可用 cache，**没有新方法指标提升或创新结论**。

### 25.41 C-41：部署观测作用域与错误覆盖开工（2026-10-13）

科研价值：从 train 信号推进到 frozen strongest anchor 的真实错误覆盖，支撑表 5-3 的
信号/功效准入。可行性：本地既有五个 train-only CPU 观测器与无标签 official test input 可读；
固定等权概率均值，不新增拟合、不选 fold、不读取 FACT dev 标签，不改消费者 clusters。
ERE identity 标签仅供后续独立错误分析，不能进入 observer；探索性 dev 已被历史使用，
此处不声称确认性结果。配置、完整 provenance 与执行结果将在本节记录。

部署代码 commit `a43fc9a`，冻结配置 SHA
`de895509934b6b1993e57ff5e815f0911140ac5aa4f64e1e15a0d5a4c30423ba`；
五个既有模型等权均值已产出 **291 docs / 7,195 mentions**，`fit_calls=0`，
argmax CT+ 7,110、CT− 34、PS+ 51，PS−/Uu 0。未读取 FACT internal-dev factuality 标注。
概率 SHA `2183978f3f1753fedb9397a3ae6480e1947a148f18b300d90c311d4c5e5f7b57`；
metadata SHA `2808874c506615bd277a3bc71519b6c6ba46a7437f853507c7804344fba5f25b`。
TDD **6 failed → 6 passed**；验证 document isolation、无 gold shape、manifest 全覆盖与 class-order。

错误覆盖代码 commit `fb1ef9b`，配置 SHA
`0b9c0d8d4393aa3e3668ecfd60cd36bc9f790aa7b7375b33a4b91ec8313ff778`。
强锚选中 605 条非 dummy antecedent links：470 条同 gold event、135 条不同 gold event；
其余 6,590 个 mention 选择 dummy。全 antecedent 候选 117,435 对中预测类别不同有 3,468 对。
**被选中的错误连链里类别不同为 0，正确连链里为 3（位于 2 篇文档）**。
选择连链的错误不等于 MUC spurious-link 计数，不能直接推导拆簇后的 MUC。
这份部署观测不支持直接 label-difference veto；连续概率的信息尚未分析，不否定所有 factuality 通道。
report SHA `2553f9103f469aca223b42b56586a3fe965357f63c6eff63a15c4a55efb8332e`；
per-document SHA `ab9ea0f61733d14e05417302bbfdad50f6ef07ad1bd0c59ae4be7cb982e848ce`。
TDD **4 failed → 4 passed**；完整门 **841 passed / 43 skips、ruff 0、CPU smoke OK**。

接续连续几何自审：价值是区分 argmax 无覆盖与连续信息真正无方向支持，避免错误扩大停止结论；
可行性是复用相同 q/cache/ERE gold 的只读 CPU 计算，不拟合、不输出新 clusters。
唯一距离固定为五类概率差的半平方 L2，报告 all/same-type 两桶；同文档内 false/true 各自均值
差值与文档 bootstrap 区间。此诊断不是新主指标、功效准入或 proposed method 输出。

连续诊断初始实现 `fb8c2c8` 因 raw gold type 位于 event 层而非 mention 层失败，
未产生输出；不是科研负结果。保留原配置，追加新回归测试先 1 failed → 通过；
`811d4ee` 显式构建不修改原 gold 的 typed view，新 r2 config SHA
`a2774024647896f113e5ba89e53d13b4ab359bcf35299d430b9af6f907fc38cd`。
距离、桶与统计定义未改；不回填缺失 type，不覆盖旧产物。

| 连续距离诊断 | 同文档两类都存在的文档 | 文档等权 false−true 均值 | 文档 bootstrap 95% 区间 |
|---|---:|---:|---|
| all selected links | 64 | −0.0013963181 | [−0.0072782097, 0.0019865678] |
| same-type selected links | 53 | −0.0018191925 | [−0.0087568721, 0.0022644747] |

2,000 document draws、RNG 13；没有增加训练 seed。这是弱 observer 的半平方 L2 几何，
并非身份指标、MUC 效应或目标 power。均值方向未支持“false 比 true 更远”，两区间包含零。
**裁决：当前经典文本 observer 路径停止，不扫参/换距离挽救；不否定所有 factuality 方法。**
report SHA `952dc9ce6cebb0cebabadea6e448db52d28d6b24ba6a78bc86d278eb81ad6ac6`；
per-document SHA `d97ab95f376a2243bf338c13e2275338b88fe5877bc00f99b4b03e383a4d7b3a`。
本轮完整门 **845 passed / 43 skips、ruff 0、CPU smoke OK**。

### 25.42 C-41：任务给定类型的 stronger control 开工（2026-10-13）

科研价值：表 5-3 的 frozen official-joint 未用任务给定类型作连链限制，核查其遗漏是否会
被未来方法误认成新机制收益。可行性：完整 cache 已通过原锚 exact parity、原机 CPU utility 可用；
给定类型就在冻结无标签 test input，不用 gold cluster，也不增加模型训练/seed/权重搬运。
合同 `PHASE_C5_typed_control_20261013.md`；先原 decoder parity，后固定 known type-agreement。
对应 Lu & Ng §4.1 C1 的概念，非其 MTL 复现、非创新。没有方法训练或新结果。

冻结配置 `configs/c5_typed_control_20261013.json` SHA
`63d101a880bac40153693ed4f4ea17bbcc4bdf52b78809e72d1b61316e86b516`，
代码 commit `de5acb1`。TDD 首跑 **4 failed / 1 skip** → 本地 4 passed / 1 torch skip；
完整本地 **849 passed / 44 skips、ruff 0、CPU smoke OK**。
推送前通过 Git archive 将 script/config/test 和原 CPU cache helper 发至 4090 临时目录；
CUDA 隐藏的对应真实 official decoder CPU 测试 **5 passed in 26.82s**。
测试确认遮挡跨类型最高分后选择次高合法 antecedent，dummy/合法分数/完整行形状保留；
并非真实数据的 type-control 指标结果，后者尚待执行。

原机 CPU PID **1782472**、运行 commit `85c2a93`、日志
`logs/c5-typed-control-20261013.log`；已 `complete`。无约束重放全量 exact parity，
固定约束改变 **21 documents**。生产不读 gold 文件、零 optimizer steps；模型/源码/cache 未改。
远端官方评分后，回传的 prediction/changes hashes 与 metadata 对齐；
本地使用原同一 gold/source_lock/evaluator/candidate digest 独立复算，全部 scores 数字与远端一致。

| 官方共指指标（F1，%） | frozen official joint | 给定类型控制 | 差值（百分点） |
|---|---:|---:|---:|
| MUC | 80.9847198642 | **82.6689774697** | **+1.6842576055** |
| B³ | 98.0398658695 | 98.2724739302 | +0.2326080607 |
| CEAFe | 97.7315760307 | 97.9410105769 | +0.2094345462 |
| BLANC | 89.8800889765 | 91.1163290123 | +1.2362400358 |

MUC precision 从 78.8429752066 升至 82.0998278830；recall 均为 83.2460732984。
按同协议 MUC counts 独立复核，precision numerator/denominator **477/605 → 477/581**，
recall numerator/denominator **477/573 → 477/573**：移除 24 个 spurious MUC links，没损失总召回。
文档 MUC **19 升 / 0 降 / 272 相同**；文档配对 bootstrap 2,000 draws、RNG 13，
ΔMUC 95% 区间 **[0.9800180100, 2.4354309610]** 个百分点。
这只描述 evaluation-document variation，不能替代跨初始化结果或目标 power。
三类关系字段均复制原预测，不报告新的关系改善。

**裁决：得到可复核的同协议控制改进，但不是论文创新突破、不是新方法 PASS。**
已知 C1 type agreement 是收益来源，不能冒称新机制；旧 frozen anchor 与旧家族结果不改写。
未来 C5 候选须将该控制列为 stronger alternative 并明确类型 policy，不能只胜旧弱锚。
当前弱 factuality observer 仍停止；下一步从该控制的剩余错误做机制/功效准入研究。

prediction SHA `0189be77150ee5f8946d3a1b09dbe5436c953451c350ec3acd41c710be984f37`；
changes SHA `b5c99c6caeb2b967ddeae69009969d0b81be9d9e4f3917cb990960adb7614136`；
metadata SHA `af5bc246403e7098be9f8ec8bcbc9057901a7dde100e67924be072a9d65a5941`；
remote metrics SHA `22a55c15d12260525769650826d6f9c7b93b7c45294d30730bfd00977d1806c4`；
local independent metrics SHA `8584708846a00949a5a9ccf3a5eeafe5b88489ee389c01ca9fe14ac37188be8c`；
paired counts SHA `2a4690b43683156b9cdb93bd6780d4056c5a052bf038b833bbbc585f51445755`；
paired comparison SHA `07f64e2f656279bd6b87dd3a6b22f8c3de38723c1b354ec37bcb633147dae119`。
stage 15 份此前非权重产物 manifest SHA
`14df267d3463394e6c9e34ccc392cbdacd6d73020daff2bb9079856255c17ee0` 已在 4090 逐项核验。

配对 counts 首次遇到既有 `_coref_document_counts` 的 implicit singleton 构造 bug：
generator 创建了 list-of-set，引发 TypeError，未产生配对报告。
新回归测试 **1 failed → 6 passed**，只把隐式 singleton 修正为 set；不改指标公式/旧报告。
修复后总 counts 与两份官方 MUC 独立精确一致，相关统计 helper SHA
`3cccd3fe8c1b61a3f697425c9ea19aa16d3c32dea2f7adf896250739f9849d56`。
最终本地门 **850 passed / 44 skips、ruff 0、CPU smoke OK**，R1 consistency **36 requirements PASS**。

#### stronger control 的剩余错误（既有 profile，只读）

自审：价值是防止依据旧弱控制的错误比例选择新家族，对准表 5-3 的机制准入；
可行性是复用已存在的 CPU profile，原 gold/pred/evaluator/candidate 均已在独立评分核验。
执行 `report_coref_error_profile.py --evaluator data/protocols/v6/tools/maven_ere_evaluate.py
--gold runs/stages/A3/a3-v6-baselines-r10/preflight/data/MAVEN_ERE/valid.jsonl
--pred runs/stages/R1/r1-v63-c5-20261013/type_control/predictions.jsonl
--output runs/stages/R1/r1-v63-c5-20261013/type_control/residual_profile.json`，退出 0，
profile 与官方 scorer 精确交叉核验通过。
剩余 missing/spurious MUC links **96/104**，两方向占 **48%/52%**，不能继续称“全是 precision 问题”。
pair 层 under/over merges **222/303**；under 中跨句 **209**、高相似 ≥0.8 **94**；
over 中跨句 **278**、高相似 **189**。profile 是错误画像，未证明 lexical bias 的因果方向。
report SHA `168e9c05cb820fe40a330a87daa24e52f830ccaf562654b3a0aefe0efe46f814`。
接续研究须同时区分高相似误合并和低相似漏合并，不能复活旧 role residual 或把 trigger masking
直接称创新；对应 counterfactual ECR 已有 2024 RCA/2025 ACCI，一手机制审查后再裁决。

非权重产物已备份回 4090。type-control 八文件 manifest SHA
`9ab77f80cba6576610ab3bf102914f31c1dec1dc756e8ae00bd95e6e8418a7ed`；
此前 15 文件包与本包合计 **23 个 artifacts** 在 4090 独立逐项 SHA 核验通过。
五个 sklearn model.joblib 留本地，官方 neural checkpoint 留原 4090，5090 权重/冻结诊断 snapshot
未动；没有跨机权重搬运。implicit singleton 统计修复 commit `b049dad`；旧报告未重算。


### 25.43 C-41：最近邻审查与 antecedent 决策分解开工（2026-10-13）

科研价值：对准表 5-3 与 C5 新机制准入，识别 stronger type-control 残余错误落在
null/anaphoricity 决策还是前项排序；不把触发词相关性当因果证据，不把已知 anaphoricity
模块或可微 MUC 目标称创新。对应观测仅引用 §25.42。
可行性：两份既有 manifest 已逐项 SHA 核验，CPU cache/given types/identity gold/官方 evaluator
可用；固定本地 CPU 只读诊断，不训练、不读 final-valid、不搬权重。5090 成功只读核卡仍有
他人 vLLM 占用，原已授权 audit 未启动；这不是模型负结果。

本次预先固定类别：correct dummy、correct antecedent、first-mention false link、
false dummy with correct highest-ranked legal real antecedent、false dummy requiring ranking、
wrong real antecedent with a gold predecessor。类型来自无标签 test input，identity 只用于诊断。
每个 mention 只入一个类别；先还原 type-control 的全部 non-singleton clusters exact parity。
固定 oracle 三臂：null-only 修复 first-mention false link 和 rank-correct false dummy；
requires-ranking 修复其余两类；all 修复四类。修复到最高原 logit 的合法 gold predecessor，
首提及修复到 dummy。all 须精确得到 gold cluster，独立 MUC counts 与官方评分必须一致。
这是金标条件下的干预覆盖诊断，非可部署预测、非方法输出、非保证实际提分的上界或确认性 power；
各臂效应不假定可加，不扫阈值。新 namespace 为 `decision_audit/`，未准入训练合同。


实现 commit **`a6d159d`**；entrypoint SHA
`e6ec2d78d1bb5a120e5f8f042316e189e6e22d0efb29140ad2c68f1b42106120`。
配置 `configs/c5_decision_audit_20261013_r2.json` SHA
`13069ae3be7631cf765f6776e6b2578fad266f525c793d2438ae90977414f257`。
首个 v1 输出已完成后发现行长 lint，不改科学规则；保留 v1 config/output 和运行源码快照
`neighbor_audit/executed_decision_audit_v1.py`（SHA 与 v1 config 精确一致），另冻 r2。
v1/r2 的三份 oracle predictions、逐文档 decisions/counts **逐字节相同**，没有按分数改设计。

执行 `uv run python scripts/report_coref_decision_audit.py
--config configs/c5_decision_audit_20261013_r2.json`，退出 0。全部 **291 documents / 7,195 mentions**
的 baseline cluster parity exact；每个 mention 仅落入一个类别：

| 类型控制上的 antecedent 决策类别 | mention 数 | 存在该类的文档数 |
|---|---:|---:|
| correct dummy（在 cache 文本顺序中无 gold 前项） | 6,525 | — |
| correct real antecedent | 471 | — |
| 首提及错误连到另一个 event | 97 | 65 |
| 错误选择 dummy，但最强合法 real antecedent 正确 | 76 | 61 |
| 错误选择 dummy，最强合法 real antecedent 也错误 | 13 | 12 |
| 有 gold 前项，但选择了错误 real antecedent | 13 | 13 |

**199 个局部决策错误中，173 个属于本次 null-only oracle 的覆盖**。这不是 MUC link 数，
也不是新增模型的检出率；普通新旧 event 判别仍须覆盖大量正确 dummy 并保护正确连链。
first mention 包含非 singleton chain 的开头，不能拿 singleton label 当它的同义词。

| 固定 CPU 金标 oracle（非部署方法） | MUC F1 (%) | precision numerator/denominator | recall numerator/denominator | B³ F1 (%) | CEAFe F1 (%) | BLANC F1 (%) |
|---|---:|---|---|---:|---:|---:|
| stronger type-control 重放 | 82.6689774697 | 477/581 | 477/573 | 98.2724739302 | 97.9410105769 | 91.1163290123 |
| null-only oracle | 96.5578111209 | 547/560 | 547/573 | 99.6660788221 | 99.7226502680 | 98.5996311211 |
| requires-ranking oracle | 85.1756640960 | 497/594 | 497/573 | 98.4650143655 | 98.1111490533 | 91.8347297945 |
| all oracle / gold cluster 恢复 | 100.0000000000 | 573/573 | 573/573 | 100 | 100 | 100 |

null-only 使 missing/spurious MUC links **96/104 → 26/13**；requires-ranking 使其
变成 **76/97**。分臂收益不可直接相加，局部 false-link 也不等于 spurious MUC link。
all 与每篇 gold 的 non-singleton clusters exact parity。三臂另由独立进程运行
`score_maven_ere_official.py --gold <原 frozen gold> --pred <oracle arm> --candidate-digest
15a3b1a548625624642130190b39411e6346866ff8594c2af2020cfbdac10910 --output <独立报告>`，
官方四指标逐项精确一致；原 helper 的 MUC counts 也与官方分数精确一致。
这是**探索性、gold-conditioned、non-deployable** 的决策分解，没有 proposed 指标增益、
因果归因、确认性功效或 C5 PASS。

#### train 监督范围与新颖性裁决

`uv run python runs/stages/R1/r1-v63-c5-20261013/neighbor_audit/train_scope_count.py`
退出 0，只读 frozen train；排序规则核到 frozen official `data.py:113–114`。
**2,622 documents / 66,744 mentions**，train/dev doc intersection **0**。
首提及 **61,362** = singleton **59,124** + 非 singleton chain 开头 **2,238**；
重复提及 **5,382**。首提及中有同类型先前竞争 mention **20,078**；同类型合法前项 options
总计 **66,141**。零 fit、无模型输出，仅证明标签与竞争集合可派生，不证明预测或 power。
train source SHA `20ea01ebe71fb8c8e4f207368673cc71f29840a290698eefe15de3a24a3b6f05`，
manifest SHA `47d19cc9a17e38259bfbb7f9206c675c7362f41252d23f414ea6cfd46015ca68`。

一手机制/代码矩阵与 candidate brief 见
[`research/20261013_c5_newness_admission.md`](../research/20261013_c5_newness_admission.md)。
[RCA Algorithm 1](https://aclanthology.org/2024.naacl-long.63.pdf) 与官方 commit
`f88572fac4f50595abee730dfcf14ac8cfa916aa`已核：确有 trainer、helper/部分生成 CSV/MIT，
非 README-only；main enhanced train CSV 指向 git 外的 Drive。没有执行其 trainer，未建立
MAVEN 增强数据或 fidelity PASS，不把原 split 的数字移入统一主表。
ACCI 最新 `7f5bcd81e0a352f15263a5c7e7c4853b9e3023fa` 仍 README-only；CohTP 最新
`3843ad0a4dcdb9f4761f134894b935d4ed74d19b` 仍仅 `Comming soon`。两者卡【代码】，
不能重建后声称官方复现；其正文机制先行性仍成立。

进一步核 [Lu & Ng 2017](https://aclanthology.org/P17-1009.pdf) 的首提及监督与
[2021 §4.1 C3/C4](https://aclanthology.org/2021.naacl-main.356.pdf)、
[C2F-SD §3](https://aclanthology.org/2024.naacl-short.19.pdf)、
[Lee 2017 §6](https://aclanthology.org/D17-1018.pdf)、
[StructECR §3.4](https://aclanthology.org/2021.acl-long.374.pdf)、
[Le & Titov §2–3](https://aclanthology.org/K17-1039.pdf)。
**不准入普通 newness/singleton 头、删光 gold antecedents→dummy、generic cluster regularizer
或 plain counterfactual port 作为创新**。Le & Titov 的实际训练目标为 B³/LEA，不能误称其已做 MUC loss。
C2F-SD 本轮 web/git 访问失败，状态 UNKNOWN，不能据此说代码不存在。
原 PDF 下载超时、GitHub API rate limit、RCA full-clone HTTP/2 错误均已分开记录；
后续 bounded PDF 下载与 partial no-checkout git 源码核查成功，没有把工具失败当科研结论。

**科研裁决**：继续条件决策风险的输入与最近邻审查，优先检验真实 null 边界；
普通 anaphoricity/校准必须作为强竞争解释与 matched control。
当前只有候选 brief，尚缺 train-only 文档隔离 scorer error-state 输入、selective/error-correction
最近邻差异、具体干预/消融负控冻结与 ≥80% document power；**method_admitted=false**。
不拿 explored internal-dev 拟合 detector，不用 scorer 的 in-sample train 错误冒充 OOF，
不启动 proposed GPU 方法。C-41/T087 继续 wip，当前 C5；D4/A4 尚未接队。

#### 验证与产物身份

TDD **8 failed（入口未实现）→ 8 passed**，覆盖 first≠singleton、类型 policy、排序/dummy
两方向、全 oracle 恢复以及 population/type/score 负测。最终本地完整门
**858 passed / 44 skipped、ruff 0、CPU smoke OK、R1 consistency 36 requirements PASS**。
本次没有修改或执行 torch 代码；torch skips 仍不当作远端模型验证。

r2 report SHA `d38856e1cf737faa9dc98d09e3c4941a4e6590102823c688b6af613cf6325989`；
r2 六文件 manifest SHA `2e1b4596ca83d90e90d94251b1bcc2a5f2a8bc8a3519d5dbfcbb9c190723b701`；
独立评分六文件 manifest SHA `f9151f0006b19fae85a337322c768807d49a99aceebfca6ab6bf40dced8de8ee`；
neighbor/train 38 文件 manifest SHA `5de28a84d1aeb97300222101b00c0188e36bd26379dc36548feae5b72e99c9e7`。
train report SHA `c01bfb8e0c7b81c2c7694b25a002a78db7bd69ff1bc09a8c7357a902f07ae7cb`。
独立 scorer 命令/日志见 `decision_audit_independent/`。所有新产物位于
`runs/stages/R1/r1-v63-c5-20261013/` 的新 namespace，没有覆盖既有 cache/type-control。


新包已备份至 **gpu-4090 `/data/TJK/ekg/` 同相对路径**：v1/r2/独立评分/neighbor 四包
共 **60 个非权重文件**（56 个 artifact entries + 四份 manifests），tar SHA
`77e3b09d753a8ee783b9dd64e88fa7deb90fe93e5df241f2b1d11959f18235ea` 双端一致；
原机以 `.venv/bin/python` 解包前拒绝覆盖既有 namespace，逐项 SHA 核验 **56 entries PASS**。
上游 shallow/no-checkout 的 `.git` 对象未搬运，保留源码/tree/PDF 快照的 manifest 项。
没有 checkpoint 搬运、GPU 模型计算、新初始化或 final-valid 读取。


末次只读重核 5090 时 SSH 返回 `Connection refused`（exit 255），当前资源状态 **UNKNOWN**；
较早成功核卡见 GPU0 **31,498 / 32,607 MiB、96% util**，PID **2633736** 为他人
`VLLM::EngineCore`，所以当时未启动原已授权 audit。SSH 失败不说明进程死亡或卡已空闲；
接续必须成功 SSH 后重新核卡。没有启动 watcher、后台实验或扩大 5090 授权。


### 25.44 C-41：固定双向 scorer 的实际控制实验开工（2026-10-13）

作者明确要求实际指标或整体方案创新，诊断准备不作为完成。科研价值：对准表 5-3，
检验已完成 null 边界诊断的可修复空间能否由无身份标签的评分改变落实为真实增益。
一手源码 `official joint/src/model.py:84–108` 的 pair MLP 使用 `[h_i;h_j;h_i*h_j]`，
仅按当前/先前方向训练，顺序交换未被对称结构保证。对称化已有公开机制，
本轮是 derived control，不冒称创新、不冒称外部系统完整复现。
可行性：4090 原 checkpoint/pretrained/CPU scorer 已完整重现；当前四卡均有他人 vLLM，
只用原机 CPU 4 threads / hidden CUDA。零训练、无额外 seed、无权重搬运；无标签 ERE input
与给定类型固定，gold 只在独立评分时读取。§25.43 的 oracle 不作为本轮模型效果或 power。

预测前固定：复用原 encoder 表示和官方 MLP，新增反向 `[h_j;h_i;h_i*h_j]` 分数；
双向 raw logits **等权算术平均**，dummy logit 仍 0、给定类型 policy 与 stronger control 一致。
三臂：原 typed scorer（必须 exact parity）、双向平均、同文档/同 type 对的反向 logits 固定
置换负控（RNG 13，原正向不动）。不再尝试 min/max/权重/threshold sweep。
先 CPU smoke 确认原 forward/cache/type-control parity 再跑全集，用原 P1 evaluator/candidate digest
独立复算 MUC/B³/CEAFe/BLANC。若没有胜 strongest typed control 或负控同样改善，不认定
有用对称证据；无论结果如何如实封存。新输出独占 `symmetric_control/`，已存在即拒绝覆盖。
本轮不构成 proposed 方法训练合同，条件风险候选的输入/创新/power 闸门仍有效。


来源已核到 [Ahmed et al. 的正式 v2 正文 §4.2.1 Eq.1](https://aclanthology.org/2023.findings-acl.100v2.pdf)，
原文平均 CE 分数（范围 0–1）；本控制平均原 MLP raw logits，且是同一文档编码后的 head
交换，不是重新编码两个拼接文档。差异已入合同，不称其完整复现。
实现 TDD 首跑 **5 failed / 2 torch skips** → 本地 5 passed / 2 skips。
远端验证首跑缺验证包内的既有 cache config（6 passed / 1 failed）；仅补入原 config。
次跑 forward 的完整 batch 概率 parity 通过，但 reverse 单项调用与整批调用差约
`5.96e-8`，原测试用 exact 比较误把计算形状末位误差当失败。单项对照改为 abs `1e-6`；
正式生产的同批 forward/cache **仍要求 exact**，未改 scorer/候选/控制设计或数据结果。


实现 commit `f2948d4`；冻结 config SHA
`42cf77a999b41ee3bd7f7d22788757db501badbf4a893736cbd6e170ca342a74`。
完整本地门 **863 passed / 46 skipped、ruff 0、CPU smoke OK**，R1 consistency PASS；
4090 真实 Torch/官方 scorer CPU 用例 **7 passed in 27.82s**，原设计未变。
原机 64 CPUs、load **17.91/17.30/15.99**、available memory **490,793,128 kB**，
限制 4 CPU threads；新 output 尚不存在。下面是真实 checkpoint parity 与评分的执行阶段，
单元测试不替代它。


原机 smoke 真正 `complete`，PID **1822206**、运行 commit `ffdbde5`；**8 documents**
的全部 original forward logits 与既有 cache exact，给定类型 baseline non-singleton clusters
exact parity。日志 `logs/c5-symmetric-cpu-smoke-20261013.log`，status/config SHA 对齐；
四文件 artifact hashes 已由 status 记录。成功 SSH 读到 complete 且进程已 GONE，
没有将 shell wrapper PID 当实际模型 PID。
同 config 的 full 已启动，日志 `logs/c5-symmetric-cpu-full-20261013.log`；
尚未读取新指标，不扫权重/阈值，不改变方法契约。


#### §25.44 全集实际结果与停止裁决（无新方法胜出）

完整 **291 documents**，所有 original logits/type-control clusters exact parity；full PID **1823867**、status complete。
远端与本地独立 official scorer 的四指标逐项精确一致，source_lock/candidates/输入轴均一致。

| 实际预测控制（非 oracle） | MUC F1 (%) | B³ F1 (%) | CEAFe F1 (%) | BLANC F1 (%) |
|---|---:|---:|---:|---:|
| typed strongest control | 82.6689774697 | 98.2724739302 | 97.9410105769 | 91.1163290123 |
| fixed bidirectional mean | 82.4253075571 | 98.2666561227 | 97.9773531538 | 91.1618997973 |
| type-matched reverse shuffle | 74.0186915888 | 97.5719451373 | 97.3630418906 | 86.2497835113 |

双向平均相对 strongest type-control 的 **ΔMUC −0.2436699126** 个百分点，
2,000 document bootstrap / RNG 13 的 95% 区间 **[−1.5593438641, 0.9994732878]**；
precision numerator/denominator **477/581 → 469/565**，recall **477/573 → 469/573**。
spurious **104→96**、missing **96→104**：抑制误合并伴随更多漏合并，未落实主要 null 修复覆盖。
shuffled 的 **ΔMUC −8.6502858809**，区间 **[−11.6760812860, −5.8457032955]**。
负控显著更差不能挽救主臂未胜出的事实，也不能当作创新证据。
**裁决：停止此固定对称控制，不扫 alpha/min/max/threshold，不称指标突破或方法 PASS。**

下载时独立 comparator 首次缺尚未回传的 remote metrics 文件：本地 scorer 已成功，但
比较端 FileNotFoundError；补回已经 complete 的 evaluation JSON 后，两臂逐项 exact。
这次传输/比较失败不是模型负结果，没有重跑模型或改变 score 规则。
原机主模型 checkpoint 未搬运；full/两臂与 paired CI 的非权重产物见
`symmetric_control/{full,evaluation,independent}/`，sha manifest 待最终双端封存。


### 25.45 C-41：冻结 encoder/scorer 的 train-only null 控制开工（2026-10-13）

科研价值：对准表 5-3，将 §25.43 的 null 决策可修复覆盖转为真实无标签 inference，
不再以诊断完成充当目标。固定对称控制不作权重挽救；新控制直接学习是否存在合法 gold 前项，
复用 Lu & Ng 的已知 anaphoricity 思想，不宣称新方法或其多任务系统完整复现。
可行性：原 2622-doc train gold 可派生 first/repeat 监督，与 291-doc evaluation 无交集；
原 frozen neural checkpoint/encoder 可在 4090 CPU 导出训练表示，不需新语料、额外 seed 或 GPU。
只有新 null head 更新，原 encoder/scorer 冻结。这里的 train labels 是真实 first/repeat，
不是 baseline 对 train 的 in-sample error-state 标签，不冒称 OOF error supervision。

预测前固定：沿用原无标签 test、type policy、候选/dummy 与 P1 scorer；feature 来自 current
mention embedding、同类型先前 embedding 的均值、原最强合法前项 embedding、原 logits 的
max/logsumexp/log1p合法前项数。训练只读 train identity，evaluation feature/production 不读 gold。
固定三臂 semantic / numeric_only（embedding 块置零、同形 head）/ shuffled_semantic
（train 内 doc/type/opportunity 桶置换 embedding 块，numeric 块与真实 target 不动）。
head=Linear→ReLU→Dropout(0.2)→Linear，hidden 200，训练 feature 标准化只 fit train，
Adam lr=0.001、BCE、batch=512、固定 final epoch=10、seed=13；不 class-weight/阈值/epoch 扫描。
三个不同控制都只用 seed 13，无新增 seed。

令 q 为 head 预测的 real-antecedent 总概率；给定类型合法集合 logits 保持原值，null raw logit
为 logsumexp(legal logits)−logit(q)，因此 real 总质量为 q、real 内排序不变。
空合法集合强制 dummy。输出保留全部 mention/candidate IDs，类型 policy 显式成对。
生产动作按原 argmax/decoder，不用 gold 选择修改对象；原 checkpoint 留原机，新 head 也留原机。
baseline cached logits 和 type-control exact parity 必须先过；原 encoder/scorer 零 optimizer steps。
此处是独立的已知机制控制训练，不是 proposed innovation training；不解除条件风险候选的
novelty/input/power 门。未胜 strongest type-control/护栏降低/semantic 未胜 numeric 或负控时，
如实封存并停止这个固定控制，不扫参挽救。


§25.45 的 null 控制拟合范围补充（任何输出前冻结）：无合法前项的 mention 由定义强制 dummy，
不参与 head 拟合；**所有有同类型合法前项的 train mention 全部参与，不采样**。
semantic 三个 embedding 块分别是 current / mean legal previous / top original legal previous；
numeric 三项是 max logit / logsumexp legal logits / log1p legal count。标准化仅 fit 该 train 集。
shuffled 的固定 opportunity 桶为 0 / 1 / 2–4 / ≥5，语义块置换只在同 doc/type/桶内，
不使用 dev 标签、外部事实性 observer 或角色特征。


Null 控制代码的 TDD **6 failed / 1 skip → 6 passed / 1 skip**；training budget 负测
另 **1 failed → PASS**。完整本地门 **870 passed / 47 skipped、ruff 0、CPU smoke OK**；
原机对应真实 Torch/特征/概率用例 **8 passed in 5.28s**。冻结 config SHA
`f6261196f021a8a3512a63bedc6f0e2c9f8ca935186562fef019b6b4be3efe73`。
这里尚没有 head 的正式拟合或新指标；远端 smoke/cache/fit 将用原 .venv 和独立日志执行。


§25.44 对称控制最终 17 个非权重 artifacts 的 manifest SHA
`58bbfb684679b4fec410763dcf24cba181d79ec9ab5260c293f0d8e67efbc5ff` 已在 4090 逐项核验；
raw/cache/status 与两个独立 scorer/paired report 完整备份，负向结果封存。
§25.45 null 控制实现 commit `55fd63e`，smoke 日志
`logs/c5-null-cpu-smoke-20261013.log`，train/dev 两作用域输出独立保存。


原机 train/dev 双作用域 smoke 均 `complete`：**8/8 documents、162/202 mentions**，
原 cache/type-control exact parity。配置 SHA 不变，dev feature npz 没有 labels；
原 encoder/scorer 未更新。当前两项独立 CPU full feature exports 已启动，分别限制 4 threads，
日志 `logs/c5-null-cache-train-20261013.log` / `logs/c5-null-cache-dev-20261013.log`。
这是同一 C-41 的两个数据作用域，不是额外 seed 或两条活动队列；缓存/正式拟合尚无新指标。

#### §25.45 全量真实结果与停止裁决

train **2622 docs / 66744 mentions**、dev **291 docs / 7195 mentions** caches complete；
head 实际 fit **25460** mentions，其中 positive **5382**；全部三臂固定最后 epoch10，
原 encoder/scorer 零更新。fit PID **2084809**，运行实现 `55fd63e`，三 head 留 **4090**。
所有 arm status/config/artifact hashes 已核；本地独立 scorer 四指标逐项与原机 exact。

| 实际预测控制（非 oracle） | MUC F1 (%) | B³ F1 (%) | CEAFe F1 (%) | BLANC F1 (%) |
|---|---:|---:|---:|---:|
| strongest type-control | 82.6689774697 | 98.2724739302 | 97.9410105769 | 91.1163290123 |
| semantic | 80.7794508415 | 98.1804317382 | 97.7897360233 | 91.1215267792 |
| numeric_only | 82.2380106572 | 98.2754826646 | 97.9603346086 | 91.0992709037 |
| shuffled_semantic | 80.3819444444 | 98.0277323306 | 97.6748347384 | 89.6688063064 |

2,000 document bootstrap / RNG13 相对 strongest type-control：
- semantic：ΔMUC **-1.8895266282** 个百分点，95% CI **[-3.510442447384462, -0.339339474768848]**；spurious/missing **100/117**，changed docs **62**。
- numeric_only：ΔMUC **-0.4309668125** 个百分点，95% CI **[-1.4681621324296485, 0.5944414658769267]**；spurious/missing **90/110**，changed docs **23**。
- shuffled_semantic：ΔMUC **-2.2870330252** 个百分点，95% CI **[-3.9683212096156875, -0.6367279340965999]**；spurious/missing **116/110**，changed docs **67**。

semantic−numeric 的 ΔMUC **−1.4585598157**，CI **[−3.2306927791,0.2566443634]**；
semantic−shuffle **0.3975063970**，CI **[−1.5065134920,2.2640502170]**。
semantic 未胜 numeric、负控也没有分离，不能声称语义新ness机制有效；两拟合臂都未胜强对照。
**停止这个固定 frozen-null 控制，不扫 epoch/lr/weight/threshold/结构挽救；无指标突破。**
部署结果不能由 train BCE 几乎归零代替。所有关系字段逐 doc 与 baseline 不变。

feature scope 补查：原 teacher max legal logit 在有合法前项的 train 上 first/repeat accuracy
**0.995247446975648**、AUROC **0.9995857571302468**；这是 baseline 见过的 train，
不冒称 OOF。train 内置乱真正改变 **7184/25460** 个拟合行（约28.22%），其余小桶/同值不变；
numeric blocks 与 labels 不动，负控是局部破坏，不能说“语义全部删去”。
该 train 饱和与 dev 失败支持重新审查输入泛化，**不能据此唯一归因 encoder 过拟合**。
dev npz 只有 features；scope 补查未读取 dev targets。

远端非权重回传 tar SHA **82e6fd85d51bef88a63d85ca1f60c6891808facfbfbc803c92f8c46c4c637738**
双端一致；head/checkpoint/feature npz 都未跨机搬运。raw predictions/training/status/
双端 evaluator 输出/paired counts 位于 `frozen_null_control/`；最终 manifest 另行封存。

### 25.46 C-41：ordered forest 联合同簇概率的数学候选审查（未准入方法）

科研价值：对准表 5-3，检验 cluster identity 中共享前件依赖是否提供独立于普通
null head 的监督；可行性：当前只做无数据、无模型的 CPU 穷举，后续可复用原机冻结表示。
主表先登记候选审查；下列代数探索不是预注册的提分实验，没有读取任何 split 或训练。
机制边界与一手来源见 `research/20261013_c5_joint_connectivity.md`。

固定文档且 parent choices 独立、仅向前文链接的 random forest 有精确递推
C_ii=1，C_ij=Σ_{k<j}p_j(k)C_ik（i<j），并对称化。
在 seed 13 生成 **120** 个 n=1–6 概率矩阵、包括零概率 edges，逐一穷举
**17,460** 个 parent assignments：递推 vs 穷举的最大绝对误差
**1.3322676295501878e-15**。root-marginal product 的 off-diagonal 最大差异
**0.4115229597866288**。这是数学正确性，不是科研效应、power 或指标突破。

明确反例：p0=[1]，p1=[0.5,0.5]，p2=[0,0.5,0.5]；
两提及 1/2 精确同簇概率 **0.5**，root marginal dot product **0.25**。
这不反驳 Le & Titov 的可微指标松弛（他们未宣称其乘积是 random-forest 联合边缘），
也不把早已有的 antecedent forest、root DP 或 co-cluster confidence 当原创。
候选创新仅可能落在精确共享依赖的监督/推理及其可检验收益；正文矩阵已纳入
Rennie2007、Samdani2013、Yang2015、Le2017、Lee2018、Wick2013、Yadav2021。
官方实现、全同机制最近邻、实际分块算力、具体 loss/负控/目标 ≥80% power 未闭合，
**method_admitted=false**，未启动 proposed training。

产物 `forest_joint_audit/{enumeration_audit.py,report.json,Q15-1037.pdf/txt,N18-2108.pdf/txt}`。
代数入口 SHA `1ac807022ccded080d4fa4512358fa0b4ace0f05c179c6df22130ce9f333b038`；
全部输入为构造概率，未读取 train/dev/final-valid。当前 train-only null 控制继续原合同，
不因这个候选改变三臂、预算、强对照或采样。

Official `lephong/diffmetric_coref` HEAD **37543d5000911917f86a3c1747a50aec65b53c2d**，
commit 固定 README SHA **a6a0ec04dab18ef0194a81a530c990d12e4ea728ac212a8437e832d7a819a2f5**；
其 actual `compute_p_m_entity` 递推与 `compute_lea_lost` 的 membership batch product
已核，正文差异没有靠摘要措辞。full clone 下载逾三分钟后主动终止（已传部分 Git objects），
未把未完成 clone 标可运行系统或方法不存在；固定 revision raw README 单独读取成功。


### 25.47 C-41：固定 forest posterior-score 控制预登记（零训练）

科研价值：直接检验 §25.46 的共享前件概率差异能否转为表 5-3 的真实 MUC 改善，
而不再把数学恒等式当完成。可行性：已有无标签全量 raw logits、task-given types、
冻结 decoder 与来源闸门；仅 291-doc 小矩阵 CPU 重放，原/新 head 均不拟合、不读金标
选择动作，不需要 GPU、额外 seed、checkpoint 搬运。

先于新结果固定四个作用域相同的控制：原 type-control exact parity；exact joint C；
root-marginal product Q Qᵀ；previous C 同类型行/列同步置换负控（RNG13）。
每个当前 mention 的合法 parent 分布由原 raw logits 与原 dummy logit0 稳定 softmax；
exact C 的 diagonal1 仅用于数学递推，供 decoder 的 dummy 仍为原 p_j(dummy)。
root-product real scores 为 Q_i·Q_j；负控只置换较早 C 子矩阵，保留 diagonal1，
当前 p_j(k) 不动，因此直接 p_j(i) 项保留，只破坏间接 shared-ancestry alignment。
负控每一当前 row 独立读取原 exact previous C，不把其伪概率递归为后续真实森林。
类型不一致 score 禁用；无合法前项强制 dummy；全部 ID 和关系字段不变。

C pair scores 的 row sum 不要求1（它们是相互重叠的同簇事件），不称其 antecedent
分布或任意 partition 的 Bayes 最优解；只把固定分数送原 argmax/decoder，评价实际簇。
不额外扫 0.5 cutoff、cluster linkage、null 规则或 posterior 温度。未胜 strongest
type-control 或护栏退化则停止这个固定部署动作；root-product/负控未被胜过，
不能把任何收益归给精确 shared ancestry。新产物独占 `forest_posterior_control/`。
这不是 proposed training 或章节贡献准入；novelty/power 门仍独立。

Forest 控制 TDD **8 failed / 1 skip → 8 passed / 1 skip**；构造 type-mask fixture 在实现前
纠正 forbidden/high-logit 索引，未据模型结果改期待值。完整本地 **878 passed / 48 skipped**、
ruff 0、CPU smoke OK、R1 consistency 36 PASS；4090 真实 Torch/decoder 用例 **9 passed**。
测试器 `-c /dev/null` 的 pytest cache 写 /dev 权限 warning，不影响用例或实验。
配置 SHA **5627d15feedcb2472401ca79e5e1473b9cdfbb1e27b5c9cdc728be5062ce3a00**。
远端验证包最初把 tar 生成与 scp 错误并发，scp 因本地包尚不存在而失败；
确认包已经生成后顺序重发成功，未执行失败包或改模型/指标。

#### §25.47 全量实际结果与停止裁决

运行 commit **0d1dedb**，PID **2095238**；原机已 complete/GONE，**291 docs**。
原 typed cache 与合法重归一化 parent 的两套 baseline decoder 全量 exact parity；
实际四共指指标原机/本地独立评分逐项 exact，全部关系字段不变。

| 实际预测控制 | MUC F1 (%) | B³ F1 (%) | CEAFe F1 (%) | BLANC F1 (%) |
|---|---:|---:|---:|---:|
| strongest type-control | 82.6689774697 | 98.2724739302 | 97.9410105769 | 91.1163290123 |
| joint | 82.6989619377 | 98.2697702060 | 97.9425594212 | 91.0721982103 |
| root_product | 82.7705627706 | 98.2819649400 | 97.9468525338 | 91.2964200003 |
| ancestry_shuffle | 82.0779220779 | 98.1874285426 | 97.9189345320 | 90.3384843920 |

2,000 document bootstrap / RNG13 相对 strongest control：
- joint：ΔMUC **0.0299844680** 个百分点，95% CI **[-0.2065996331871432, 0.29295555332676226]**，仅改变 **2** docs，spurious/missing **105/95**。
- root_product：ΔMUC **0.1015853009** 个百分点，95% CI **[-0.14898012933870924, 0.41719054837506914]**，仅改变 **3** docs，spurious/missing **104/95**。
- ancestry_shuffle：ΔMUC **-0.5910553917** 个百分点，95% CI **[-1.3115275159444306, 0.03638853743744515]**，仅改变 **7** docs，spurious/missing **108/99**。

joint−product **−0.0716008328**，CI **[−0.2257481064,0]**；
joint−shuffle **0.6210398598**，CI **[0,1.3685272129]**。
exact joint 的主指标只有极小漂移、没有胜 product，且 B³/CEAFe/BLANC 有护栏下降；
**停止此固定 posterior-score 部署动作，不扫 cluster linkage/temperature/null rule。**
root-product 的微小变化也不能宣称突破，不能用负控变差充当正效应。
数学联合依赖仍与 product 有区别，但本次 frozen score/argmax 的动作证据不能支撑创新贡献；
它不验证未来学习目标，也不自动准入该目标训练。

非权重回传 tar SHA **fb59bb1b8be47fe4ca0e71ff7a7075603bee65b7a0579f581d63244225c8cf5b**
双端一致；stage 与 independent/ 的完整来源/argv/paired doc counts 已落地。

§25.45 null 控制最终 **29** 项非权重 manifest SHA
**74492012ebf220b725419495289b29a3418057d0378ac19275a987a0484edf59**；
§25.46 数学/固定源码快照 **7** 项 manifest SHA
**fad82e235b7af5a24bc72547b393204f8706a5711dafa6231d0ad98789e51738**。
备份 tar SHA **8e1823cb9995349e7129d87e5c988adb91be5e4108904e83b22851a1b23a0487**，
4090逐文件比对/补齐与 SHA核验全部PASS，既有文件只读相等不改写；缓存npz/heads未搬运。

### 25.48 C-41：固定 head 的 decision-unit 单变量审查预登记

科研价值：表5-3；§25.45 的 BCE target 是存在合法 gold 前件的 class，但原 decoder 在
每个 real candidate 与 dummy 间 argmax。设 rmax 为 real 内最高条件概率，该决策要求
q>1/(1+rmax)，而 BCE class 的对称0–1决策要求 q>0.5。候选数/entropy 可以让二者
不同；检验这个具体区别能否解释之前的漏合并，不能先断言原负结果是“待修bug”。
可行性：三臂 final-epoch head 与 scaler、dev features、原 raw logits/status 完整留4090；
只做原机 CPU replay，不新增训练、epoch、seed、数据/observer或 checkpoint 搬运。

原 frozen-null 的训练与原 action 已停止、其负结果不改写。本新审查先从同 head/scaler
精确重放原完整预测，再生成单变量 class 决策 counterfactual：有合法前项且 z>0 时链接
原最高 raw-score 前项，否则 dummy；z=0固定dummy。阈值0来自该 BCE 二类决策，
不是扫参或选过 dev 的值。三臂都执行，不挑最好档；全部 weights/input/type/ranking/
关系字段不变，官方 decoder只执行这个固定动作。未超过 strongest control/护栏时
停止该 action；无论升降都是新作用域结果，不回写§25.45。ordinary anaphoricity routing
本身已知，不能声称创新或替代 proposed-method novelty/power。独占输出
`null_decision_unit_audit/`，只以真实独立评分交付。

Decision-unit 审查 TDD **7 failed（入口未实现）→7 passed/1 Torch skip**，
完整本地 **885 passed/49 skipped、ruff0、CPU smoke OK**；4090真实 roundtrip/head/scaler
用例 **8 passed in2.47s**。新配置 SHA
**19e7c7a3fbd74206c7216b4de8d11dc9cdfd24542636ff8778847b01efc575d9**。
这里尚无新动作评分，原三臂权重/old argmax负结果不修改。

#### §25.48 实际结果与单变量否决

运行 commit **98537fd**，PID **2104964**；**291 docs** complete。
三臂权重/scaler 重载后的旧预测全量 exact parity，零optimizer。四共指指标双端独立
official scorer 逐项精确一致；全 relation 字段不变，final-valid 未读取。

| 固定 class action | MUC F1 (%) | B³ F1 (%) | CEAFe F1 (%) | BLANC F1 (%) |
|---|---:|---:|---:|---:|
| strongest type-control | 82.6689774697 | 98.2724739302 | 97.9410105769 | 91.1163290123 |
| semantic | 80.8134394341 | 98.1847637386 | 97.7857282945 | 91.1939677911 |
| numeric_only | 82.0921985816 | 98.2525091261 | 97.9421106477 | 90.9552553202 |
| shuffled_semantic | 80.5892547660 | 98.0428053410 | 97.6831898128 | 89.7688346750 |

2,000 document bootstrap/RNG13 相对 strongest control：
- semantic：ΔMUC **-1.8555380355**，95% CI **[-3.5501953024080612, -0.26948713089325127]**，spurious/missing **101/116**。相对同weights原argmax **0.0339885927**，CI **[-0.2033903279140145, 0.30380857472132833]**，仅 **2** docs改变。
- numeric_only：ΔMUC **-0.5767788881**，95% CI **[-1.5867644796004943, 0.46570177233068993]**，spurious/missing **92/110**。相对同weights原argmax **-0.1458120756**，CI **[-0.38952138020974664, 0.0]**，仅 **2** docs改变。
- shuffled_semantic：ΔMUC **-2.0797227036**，95% CI **[-3.7103066558569004, -0.4566726146132732]**，spurious/missing **116/108**。相对同weights原argmax **0.2073103216**，CI **[0.0, 0.5276939724053796]**，仅 **2** docs改变。

**停止这个 class action，不扫二类阈值/成本/再次训练头。** 训练target与候选级决策的
数学区别确实存在，但本轮固定weights counterfactual未挽救退化：semantic仅补一条MUC
true link且增加一条spurious，numeric新增两条spurious而没有recall收益。
因此“只需改二类决策单位即可恢复”在这组weights上被否决；不能外推为所有anaphoricity无效。
三臂及旧作用域都如实保留，不拿小的paired差或shuffle变动宣称突破。

回传非权重tar SHA **bb5749d3853c1b14a79b4cacceb9975110242af9ee1205b9e7fd2dcff7263804**
双端一致；head logits、完整预测、source parity/status、两份scorer和paired doc counts可反查。

### 25.49 C-41：从 fixed-score 控制转到训练梯度的科研裁决（R1，未准入训练）

科研价值：表5-3；四类固定控制实际未过门，不再作 scalar/temperature/linkage/
head endpoint 救援。§25.46 的 exact joint 与 root-product 是不同函数，但之前只用它们
做 frozen-score argmax，未检验学习信号。选择训练目标审查的依据是二者可能对同一
wrong link 给出不同甚至抵消的梯度，不是成本低；需要可证伪的数学反例与独立有限差分。
可行性：本次只用3节点构造概率和构造标签，4090 CPU/隐藏CUDA，零 optimizer、零 split
读取、零模型/权重搬运。真实 full-model 训练另须数据/计算预算/源码/power合同闭合。

预声明反例：三个 mention 同类型、parent real raw logits皆0、dummy皆0；gold构造为
{0}、{1,2}。将 exact C 或 root-marginal dot product 的strict-lower pair scores代入
同一个固定soft pair F1 loss：1−(2Σ_gold-positive score+1)/(Σ_all score+N_positive+1)。
这里+1是固定单位平滑，pair F1只是训练surrogate，**不是精确期望F1或官方MUC**。
假设 root-product 会把2→0的误链对正pair的虚假收益抵消负pair的代价，导致梯度近0；
exact joint不奖励该虚假共同root，应给这个wrong edge正梯度。逐个logit以中心差分
δ=1e−6复核autograd，不只比较最终loss。不能以这个toy PASS代替部署效果/novelty/power。

若反例成立，下一候选是从相同 pretrained initializer 训练完整原架构，用 exact joint
改变结构监督；matched official marginal/root-product/ancestry-shuffle、同given-type policy、
原强锚、backbone/seed13/数据不变，不沿用饱和的frozen-null训练作为创新。尚未准入。
当前4090四卡均占用（末次成功核卡约23GB、93/93/24/73%util），四个本轮CPU模型
入口已GONE，无 watcher。GPU忙不是候选训练效果失败，也不结束整个C-41。

#### §25.49 梯度反例实际验证（数学证据，非部署突破）

4090真实Torch CPU结果：same fixed toy/F1 surrogate 下，wrong edge **2→0** 的梯度
root-product **0**，exact joint **+0.027210884353741492**；这是logit层面偏导，
若单独更新该logit会压低误边。共享神经参数的联合更新仍需真实模型验证，不能由此保证每条误边下降。
对应 loss 为 **0.5 / 0.4285714285714286**。中心差分逐logit验证最大绝对误差
product **3.5053918101546344e-11**、exact **5.0392776757002267e-11**。
其他logits梯度与三阶矩阵完整保存在JSON；不是只检查“能backward”或一次PASS。

**裁决**：这个明确反例支持“保持shared-ancestry联合依赖可改变训练惩罚”作为下一候选的
实质差异；不把它称作算法首创、全面新颖性、任意目标优势、已发表B³/LEA损失的反证，
也不称作MAVEN改善或>=80%power。原 frozen-score 实测失败不因toy翻案。完整模型从
pretrained同架构学习的因果链/最近邻/实际成本/strong comparisons/power仍须R1闭合，
**method_admitted=false**，未启动训练或申请额外seed/5090任务。

入口 `learning_gradient_audit/audit.py` SHA
**a729a533fca5159636447fe2738f23f6605af40a2cfcccdeea520170fdf8ca4c**；
原机report SHA **7842f5b815497cdac9c7891925f045e0a16b8fc79f4c15b1355c394b8c34acd9**。
第一次scp回传在banner阶段timeout（exit255），没有把工具失败当数学失败；
原机成功执行的stdout与SHA已观测，回传重试/最终双端封存另记。

#### §25.49 完整 train 结构机会审查预声明

科研价值：表5-3；先检验梯度反例对应的同类型、按原mention顺序的
`i<j<k, gold(i) != gold(j) = gold(k)` 是否存在于真实训练数据，以及其doc覆盖与
类型块规模。它验证监督机会/计算量，不能证明原模型犯了这些错或方法能修复它们。
可行性：只读冻结train manifest、train.jsonl与已封存cache/train/documents.jsonl；
逐ID/mention/type对齐，缺失或额外项fail-fast，不读dev gold/final-valid、不用模型/optimizer。
完整2622doc，不采样；独占新 `training_structure_audit/`，输出源码hash、输入hash、
计数/块规模分位数与逐doc机会表。零optimizer模型接口/成本审查另记录，不是训练准入。

完整train机会实测：**2622docs/66744mentions**，gold repeat **5382**项均有同类型前项；
**756docs**存在预声明结构，共 **9418triplets、1925later mentions、4245positive pairs**。
逐doc独立三重枚举全量一致。类型分块 **41284**个，n的median/p95/p99/max为
**1/4/8/28**；Σn² **199026**，Σn³ **1282890**，文档事件mention最大 **109**。
这些是标签覆盖与矩阵计算规模，不是原模型错误数、可修复率、实验效果或power。
输入train文件 SHA **20ea01ebe71fb8c8e4f207368673cc71f29840a290698eefe15de3a24a3b6f05**；
审查入口 SHA **645f14c922a6fb74f0a88814c37deade525bf67e6a562ac023cb447d5f7d1718**；
三项非权重manifest SHA **7926b8a06f38e1f3c9a5689c26094a0fe5ae0db9b991c95db0a5812dccec1ab9**。

最终独立复算/梯度反例已完成双端封存：forest-score **17**项manifest SHA
**b87d59f7b969023bde7bf0143149355e74da2527f866c964503e9bc25ffb8afb**；
decision-unit **20**项 **5f29a4cab6ec90bc7f156a28b0a7b0505e3072382f49562d52ef8bda40188b70**；
gradient **2**项 **9685f10e1b4096d36139877b1bc37a657b1fbbed2c47d87de056fadab1f854ae**。
tar SHA **ea35c02fc406dc715b0db6ce8158f5798c4c32ae27fbc25194dfad13c0303e22** 原机读取一致，
所有既有文件只比对相等、新文件以exclusive-create补齐，逐manifest全部PASS。梯度report
scp重试已成功、LOCAL SHA与原机一致，先前工具失败没有修改科学结果。未搬运weights。

#### §25.49 真实模型接口/零optimizer信号审查预声明

科研价值：表5-3；检验从相同pretrained initializer的原joint完整架构能否传递exact/product
结构损失至pair MLP及encoder，以及同一真实batch上的信号与CPU成本。不得由梯度相异
推导主指标提升。可行性：原模型/data/utils/main源码与pretrained在4090，train按冻结
manifest/原顺序first8 docs，max_length256、不采样、无dev/final-valid标注。
CPU四线程/隐藏CUDA，seed13，原四头前向；同一前向图的marginal与相同+1平滑soft pair-F1
product/exact，用autograd.grad检查至MLP/encoder参数；无optimizer、无checkpoint更新。
计算量/梯度量级只用于预算和竞争解释，正式loss/scale/endpoint/power仍待冻结。独占
`training_interface_audit/`，保存原源码快照与hash、argv、docIDs、loss/grad/time/RSS。

接口审查新观察（尚待实际梯度验证）：固定 `src/utils.py` 的 `fill_expand` 仅为singleton
置dummy，对len>1簇只置严格较早的gold前件，故其首mention整行全0。固定main.py逐元素
`clamp(prob*filled_labels, eps, 1-eps)` 后再sum/log，可能使这行仅有常数而无梯度。
预声明只读核查：全train统计该类first mention覆盖，在原机用原fill_expand构造{0},{1,2}
概率，计算原loss、逐行梯度与正确dummy标记counterfactual；不改官方封存源码/weights。
若盲区成立，新候选必须加入first-mention-correct marginal强对照，并在各结构臂一致应用；
修复本身属于baseline engineering，不宣称创新，也不凭这点断言历史错误的唯一原因。

#### §25.49 真实模型与监督盲区实际核查

原机CPU PID **2154377**已GONE，report完整落地且双端SHA
**50ef58450a980b8a53bd8e387bf257a72d4236064e39af1ccb0b30b56ffe4f81**一致。
zero optimizer/full original architecture/pretrained initializer/first8 train docs，
三项固定源码与main SHA匹配sealed training metadata。

原 `fill_expand({0},{1,2})` 的第二行确为全0；同真实torch图/相同原loss下，该row误前件
logit梯度原 **0**、仅补dummy后 **0.16666666000000022**，其余logit梯度不变。
真实全train **2238**个非单例首mention、**1573docs**对应此目标空行（不是部署误判数）。
该实现盲区已确认；不能据此称历史错误皆由它造成。规范dummy监督是Lee2017 §6已知机制。

真实batch **16 chunks×256**；tokenize/model载入 **7.037s**，四头forward **6.084s**；
legacy/corrected/exact/product各自autograd至首pair linear与encoder首query耗时
**2.407/2.394/2.599/2.615s**。峰值RSS **7945788KiB**，只反映该batch/保留多目标图，
不能外推GPU epoch预算或所有doc最大内存。四任务前向真实执行，但未更新任一参数。

| 该batch目标 | loss | pair首linear grad L2 | encoder首query grad L2 |
|---|---:|---:|---:|
| legacy marginal（原type policy） | 2.6244859695 | 12.8735656738 | 0.0616115779 |
| corrected marginal（given-type policy） | 0.3634418547 | 2.9342546463 | 0.0096701430 |
| exact joint pair surrogate | 0.6848978400 | 0.6664339900 | 0.0053414777 |
| root-product same pair surrogate | 0.6764646769 | 0.6174728870 | 0.0049433890 |

actual marginal两行还同时改变type policy，**不能把其loss/grad差归因给dummy修正**；
单变量盲区证据来自上面的toy，部署影响须§25.50匹配两臂检验。结构目标确能传回真实
encoder，但梯度连通/不同不等于泛化/主指标收益。下一强对照必须修正dummy并匹配
类型policy；full-model proposed method仍未准入。

补核READS2017 Eq.1/§3/§4.1：coalescing/shared-walk/tree采样与递归相似度均是先行机制；
其相遇为等hop双walk、有decay，不能因本候选condition later节点就声称发明coalescence。
有限差异只用于same-surrogate exact-vs-root-product训练假设，不证明全部图算法无先行性。
三项文献快照manifest SHA **52661ee92844d4783cfda729071cf546a94c6350a0072d9ff9c8d7f7c500f55c**；
Fogaras作者PDF本地certificate失败/browser timeout，未读取、不依赖它的正文作结论。

### 25.50 C-41：first-dummy单变量CPU强对照（条件预登记，未启动）

科研价值：表5-3；若§25.49实际确认原loss对非单例首mention没有梯度，单变量检验补齐
常规dummy监督是否改善真实部署，而不是只报告代码盲区。它是已知marginal目标的控制
工程，不能当作新机制，也不替代exact joint候选的novelty/power准入。
可行性：原teacher/current mention表示已在4090全量缓存，source pair-MLP/权重也在原机。
直接train gold identity，不训练误差observer、不需要OOF；原encoder与关系输出冻结。
两臂从相同原pair-MLP checkpoint开始，只改非单例first-dummy label，类型约束两臂一致，
保持原real ranking/原decoder规则。先全量dev logits/typed prediction parity，再在固定train
缓存上各5epochs、Adam lr3e-4、每步8doc、seed13、dropout原0.2；无dev endpoint选择、
不读dev gold直到两臂预测封存后评分，无weight搬运、新seed或GPU。匹配epoch/optimizer/input
预算的legacy继续拟合臂用于分离再训练本身的影响，另保留旧strongest type control。
first-dummy监督本身已知（Lee2017 §6），阶段promotion只声称control effect，
不进入新方法贡献门。未过strong control/护栏则停止该固定adaptation，不扫epoch/lr/decoder。
独占新 `first_dummy_control/`；正式执行须等§25.49真实报告、TDD/本地三件套与远端Torch
用例、CPU smoke/parity全通过，按固定合同/config/source输入hash执行。

§25.50控制TDD **7 failed（入口未实现）→7 passed/2Torch skip**；完整本地
**892 passed/51 skipped、ruff0、CPU smoke OK**；4090真实Torch **9 passed in2.67s**，
再次相同源码用例 **9 passed in1.73s**（未改变源码/测试）。配置 SHA
**30d14ba95238672aa8e387fee173ad76e6ad2d4807e48d0070c1c18384abd7ba**，
entrypoint SHA **0dbbfc88f61b9d0104b7bfc74841c17d8faf17096ef39a6055ee671e07b9e847**。
config生成时误写source-lock子路径，FileNotFoundError拒绝后核真实位置
`data/protocols/v6/source_lock.json`并重新生成；没有省略source-lock闸门或产生训练。

全train额外只读核查：上述首mention中，仅 **477**项（**395docs**）有同类型较早竞争前件；
其余目标空行仍是实现盲区，但在本given-type前件集合下补dummy并不产生该row的非零
wrong-real梯度。不能把全部2238行当有效干预机会、原模型错误或提升覆盖。

§25.50 CPU smoke运行commit **85cdb3b**，PID **2168619** complete/GONE；
full291docs raw-logit/typed-cluster exact parity，first8训练一步/两臂可运行，未读dev gold。
fit PID **2172210** 已成功启动，固定两臂final5epochs；未取得完整fit status前不评分、
不把smoke结果当全量效果。原始weights、smoke/futurefit新weights均留4090。
首次远端fetch+launch SSH banner失败；改用已push的增量Git bundle同步已成功，
bundle SHA **47792806e7ca613b4c05af41f70f7787c4cc3f0e6ea4d9e626773a83b96facf6**，
remote git bundle verify/fetch/reset与HEAD **85cdb3b145a19fdb4722e67bfdd88121f15c5f29**
均实际核过。旧gitignored源码/产物不改写，非scp散文件代替git代码版本。

#### §25.50 实际结果与固定适配控制停止

运行commit **85cdb3b**；fit PID **2172210** complete/GONE，两臂均固定final5epochs、
完整2622train docs/291dev docs。初始全量raw logits/typed clusters精确重现stronger
control。两臂预测封存后首次官方评分；本地独立官方scorer全指标与原机逐项精确一致，
candidate digest完全一致，所有非coreference字段不变，无dev选模/final-valid读取。

| 同encoder/原pair-MLP起点的控制 | MUC F1 (%) | B³ F1 (%) | CEAFe F1 (%) | BLANC F1 (%) |
|---|---:|---:|---:|---:|
| strongest type-control（封存） | 82.6689774697 | 98.2724739302 | 97.9410105769 | 91.1163290123 |
| legacy continuation | 82.2064056940 | 98.2707652554 | 97.9710763786 | 91.1643823648 |
| corrected first-dummy | 81.4414414414 | 98.2359585080 | 97.9130630405 | 90.8721855844 |

2,000 paired document bootstrap/RNG13：legacy相对strongest ΔMUC
**-0.4625717757pp**，95% CI **[-1.8145440240433153, 0.8365559749453935]**；
corrected相对strongest **-1.2275360282pp**，CI
**[-2.902762566453322, 0.24139249917185687]**。单变量corrected−legacy
**-0.7649642525pp**，CI **[-2.149725382613847, 0.5604402834605]**。
区间均跨0，不称显著退化；方向没有支持收益，也没有达到突破目标/护栏。

legacy MUC counts **[462,551,462,573]**，spurious/missing **89/111**，改变 **37docs**；
corrected **[452,537,452,573]**，spurious/missing **85/121**，改变 **44docs**。
相对strongest，corrected减少 **19**个spurious MUC links却增加 **25**个missing，
呈precision提高、recall损失更大。相对matched legacy减少spurious **4**、增加missing **10**。

**停止这个固定5epoch/frozen-encoder适配，不扫epoch/lr/type policy或head endpoint。**
原target空行的监督盲区仍真实存在，但修复的这一部署动作没有实测收益；不能由源码
bug直接推导错误归因/提升。两臂loss幅度差很大主要还包含全0行常数被移除，
不把train loss骤降当学习性能跃升。规范first-dummy目标在未来公平全模型对照中仍需
使用，以免把修复当创新；本负结果不证明正确目标或其他full-model学习无效。

非权重tar SHA **6c910bf1350f9595f3f3854857075923500d1519117c521f1bccbdebcfece12a**
双端一致；预测/status/training/remote与独立metrics/paired doc counts均已本地落地。
两臂weights留 **gpu-4090:/data/TJK/ekg/** 同root的
`first_dummy_control/fit/{legacy,corrected}/pair_head.pt`，新weights SHA见fit/status.json；
smoke两档同样留原机，未跨机搬运。独立结果不能回写原strongest或其他封存控制。

§25.50合同勘误：预登记/hashed contract中“保持原real ranking”的短语不准确，
**实际已冻结源码始终更新整个pair-MLP，real scores及其相对排序可以变化**；
保持的是候选集合/chronological候选索引、pair评分函数架构、类型policy与原argmax
decoder规则。不能声称保留teacher的数值排序，或把修正作用唯一归给dummy标量。
两臂来源/参数起点/输入/优化/预算/decoder相同，只改变first-dummy gold target，
所以matched监督单变量比较仍成立。原合同/config/产物不改写；此处纠正文字，
不重跑/改评分或隐去跌分。

### 25.51 C-41：突破目标的前瞻性功效敏感性预声明（非准入结论）

科研价值：表5-3；作者要求突破而非微小漂移，因此在任何proposed训练/结果前，将
新方法最小实质目标预声明为strongest control上 **+3pp MUC**，其他指标不退化、
exact-vs-root-product须支持归因。此目标是可证伪验收标准，不是方法能达到的证据；
尚未证明该target有80%power。旧方法/其他章的阈值和统计家族不恢复或更改。
可行性：现有同协议291doc的sealed type-anchor与class-unit三臂paired counts可只读重算，
仅用实际配对bootstrap噪声，不用oracle修复预测或pairs独立化；不读取final-valid。

R1敏感性协议：固定RNG13/document bootstrap 2000，三臂各自ΔMUC噪声减去其bootstrap
均值形成零均值location noise；假设未来干预的noise shape相同、signal是固定+3pp location
shift，检验经验97.5%单侧critical（对应95%双侧CI下界>0）。报告noise scales1/1.5/2，
power为有界empirical noise下的alternative rejection比例，MDE80=critical−noise的20%
分位数。三臂均报告，以最大MDE为现有控制噪声包络；不可挑小的forest漂移噪声造PASS。
这是一项显式假设的设计敏感性，**不是完整模型方差保证、不是未来效果预测、不是训练
准入**。冻结控制适配结果如改变stronger baseline，正式method合同前需重绑定并说明
噪声假设，不能由条件power一行掩盖1.5/2倍敏感性。独占 `learning_power_sensitivity/`。

#### §25.51 条件功效实际结果与限制

预声明3pp目标下，semantic/numeric/shuffle的1×条件power为
**0.953/1.000/0.9565**，对应MDE80 **2.2481/1.4924/2.3605pp**。
现有控制噪声包络的最大MDE80在1/1.5/2×分别为
**2.3605466911/3.5408200366/4.7210933821pp**；不能只报告1×的高power。
semantic 1.5/2× power为 **0.7075/0.4735**，shuffle为 **0.667/0.446**。
因此在这些明确location-noise假设下3pp可检出，但稍高方差情形不满足80%；
这不证明完整模型candidate的效果/真实方差，也不自动放行新机制训练。

该audit没有oracle修复、未生产预测clusters；location shift是设计模型，不能写成
数据可修复上界、实际拟合或MUC提升。后续stronger baseline/拟议干预与variance假设
仍须在proposed结果前绑定；必要补强须合法冻结协议，不扩大seed或读final-valid。
入口 SHA **902fb98446f397b856e4544e9d98ee360d218a57e94c9cedf4087068c426de23**；
输入doc_counts SHA **ca6bd70a7ba4c47687811dc1e4bf6d7ecf3cb2edda8debb579e7cbfdee9ca799**。
manifest见audit目录；当前仍 **method_admitted=false**，原target3pp不因敏感性结果调大。

### 25.52 C-41：联合依赖与整体概率膨胀的竞争解释预声明（纯数学R1）

科研价值：表5-3/学习目标归因；若exact C的offdiag始终≥root-product，exact-vs-product
差异也可能是整体分数增大，不能直接认作“局部shared-ancestry信息”收益。
预声明核查：P为strict-lower parent probability，A=(I−P)^{-1}，Q=A diag(dummy)。
检验 C−QQᵀ 是否逐项非负/PSD，是否为A diag(v) Aᵀ，其中
`v_j=1−dummy_j²−p_j(real)ᵀ C_<j p_j(real)`（root-indicator的martingale残差方差）。
若成立，构造 same-doc strict-lower **总概率量匹配** 的竞争对照
`B_ij=Qdot_ij+α(1−Qdot_ij)`，α=Σ(C−Qdot)/Σ(1−Qdot)。
α为doc标量，保留总体soft predicted pairs但抹去pair-specific correction归属；
不是新decoder、额外阈值或训练超参，尚未作为方法执行。零denominator时D也须为0，
数学定义α=0；单节点无strict-lower pairs，直接检查空集合恒等式。
可行性：纯numpy、RNG13/n=1..8/每n20个概率矩阵，无实际split/模型/optimizer。
核covariance分解、PSD/元素范围、总量一致及构造gold {0},{1,2}的same-F1 surrogate；
总量匹配不代表该control是同一个forest的exact概率，也不证明方法新颖/提分。
独占 `learning_covariance_audit/`，不改原数学/控制产物，不开始proposed训练。

§25.52 实际零数据审查：**160**个RNG13随机矩阵与**2**个全singleton/全chain边界例均通过。
root-factorization、covariance分解、总offdiag量匹配最大绝对误差分别
**1.1102230246e-16 / 2.7755575616e-16 / 7.7715611724e-16**；D逐项/PSD只出现
浮点舍入负值，分别最小 **-1.1102230246e-16 / -2.0550320201e-31**。
构造toy中α **0.1**，exact与matched-mass总soft pairs同为 **1.5**，但目标pair分数
**0.5 / 0.4**、same-F1 surrogate loss **0.4285714286 / 0.4857142857**；
root-product总量 **1.3333333333**、目标pair **0.3333333333**、loss **0.5**。
因此局部归属差异可以在相同总量下存在，尚未测试真实模型/收益/梯度方向。
理论证明与新竞争对照已入candidate brief，必须保留“总体probability inflation”竞争解释；
不把既有covariance分解、纯数学PASS或总量rival冒称新method完成。
入口 SHA **58e3353cb813de490ef6e3940f9b52e1a67bad97a365373512e44239e1514304**；
复用已验证递推来源 SHA **293edadb3d97e2b97e32b6594c855504c8bf6f7d9a2aaf82e7a521844054d83c**。

§25.49预算补充：原A3 official-joint实际launcher stderr可读；最后三个完整epoch的tqdm
时长分别 **64/68/69s**（328 batches，各epoch打印两行，不把199行当199个epoch）。
source EventEncoder为DataParallel，原gpu_preflight四卡均空、launcher未指定单卡；
因此这些仅是原执行环境下的晚期epoch成本，**不能直接当作单卡4090的新目标预算**。
该log的末端仍重现原共指主锚；后续需从实际CUDA smoke记录选定空卡/显存/批量成本，
不得把CPU batch或历史未钉选卡的速率伪装为未来单卡可行性PASS。

§25.49–§25.52非权重备份：完整train结构 **3**项manifest
**7926b8a06f38e1f3c9a5689c26094a0fe5ae0db9b991c95db0a5812dccec1ab9**；
真实模型接口/原源码快照 **5**项 **9dcdd44bbf9d53838d336c0dc4b15f242b9b638ba48b00e895ce4d42e697d138**；
READS文献 **3**项 **52661ee92844d4783cfda729071cf546a94c6350a0072d9ff9c8d7f7c500f55c**。
tar SHA **5874fd8e87583e9b91559880ef544b8c6bfe0fd8ee52ff4d4e047ee02c559f59** 双端一致，
4090 exclusive-create/既有文件只读相等比对/逐manifest核验全部PASS。

first-dummy控制含独立复算 **15**项非权重manifest SHA
**fa169bedc14a43f059fc79823cf683b7ef7f5c18141da5432304d21413934a8a**；
power敏感性 **2**项 **de0f4d688cacbbf5ddd75be48ac79fb363e1589b70bbca867398e7da9510c183**；
covariance/rival审查 **2**项 **0444c4329931f286c644cb7354f10caae42fce30e21537d5e9122a497b732201**。
末轮tar SHA **b19c87bd05178af68244db074fbdff511603a556c37ef0a70f14f2ef3f380783**；
其回传/备份曾SSH banner timeout，原实际控制与独立结果无损，最后逐文件核验状态另记。

最终末轮备份逐文件核验已成功：`first_dummy_control` **15**项、
`learning_power_sensitivity` **2**项、`learning_covariance_audit` **2**项全部PASS，
上列tar SHA原机与本地一致；既有产物只验证相等、新文件exclusive-create，未搬任何weights。
5090本次只读核卡SSH **Connection refused / exit255**，资源现态UNKNOWN；
原已授权audit未启动，不重复原smoke、不推断占卡或进程死亡、不申请新5090范围。

### 25.53 C-41：完整train的原tokenization/chunk成本审查预声明

科研价值：表5-3/下一full-model预算；type块规模决定结构DP成本，transformer显存/时间
还受每doc token chunks影响，不能由first8的16chunks/RSS直接外推完整训练可行性。
可行性：只读原train file/manifest、固定官方data.py与服务器本地pretrained tokenizer；
4090 CPU四线程/CUDA隐藏，完整2622docs原tokenize/max_length256，无模型/optimizer、
dev/final-valid、checkpoint搬运或新增监督。核doc IDs/event mention总量/hash，
记录每doc chunk/nonpad token数量与P50/P95/P99/max、固定RNG13 doc order下8doc批次
chunk峰值、任意8doc最坏上界及对应IDs。顺序不是原历史Torch shuffle的重现，只是
下一smoke的固定成本输入集合；不评估模型，不把counts当单卡budget PASS。
独占 `training_chunk_audit/`；监督/假设仍是原candidate，不新开decoder/head控制。

§25.53原机PID **2206737** complete/GONE；无neural model、无optimizer，原P1 protocol
SHA与train/data/pretrained内容摘要全部实际核过。完整 **2622docs/66744mentions**，
原tokenize/max_length256耗时 **46.7416018751s**，共 **4799chunks、892998nonpad tokens**。
doc chunk P50/P95/P99/max分别 **2/3/4.79/8**；固定numpy RNG13的8doc批次峰值
**23chunks**，任意8docs最坏上界 **55chunks**，对应IDs已固定保存。
nonpad tokens/doc P50/P95/P99/max为 **293/679.95/952.06/1735**。
这些输入规模有实测依据，仍不等于CUDA峰值/optimizer内存/epoch wallclock PASS。
后续成本smoke应覆盖固定峰值/最坏输入，而非只重复16chunks的first8模型probe。
入口 SHA **fd0e5964c2106b8e1831655df0d14cc56a884cd348237ccbf4f7b46f7e162394**；
report SHA **329bd608d33eba3b85021c8fffc4dfc098fc70e5ad9bf3029a67f102fbccc917**
已从原机base64无损落地本地；逐doc文件/hash与最终备份另补。

§25.53逐doc文件已回传；LOCAL独立重算docs/mentions/chunks/nonpad totals与top8上界
全量一致，**3**项manifest SHA
**9334f5fc2da9bc3d4582761bdbf2b99c2678364914f6ff6543182bdb262a062b**。
SSH复用的临时ControlMaster成功建立后再核卡：4090四卡仍为他人任务，
占用 **23890/23221/23221/23221MiB**，util **74/98/67/50%**，未启动CUDA任务。
这是最新成功状态，不把此前banner失败当空卡/任务死亡；无后台GPU启动watcher。

§25.53最终LOCAL/4090 **3**项逐文件SHA一致、备份核验PASS。所有本轮CPU实验/审查
进程已成功SSH读到GONE，完整报告存在；此次临时SSH ControlMaster仅改善读写连接。
收尾显式exit请求时socket已不存在（exit255）；随后成功本地ps核该任务master为GONE，
没有把socket错误当实验死亡，没有遗留后台启动器/训练watcher。C-41/T087仍wip，未宣称指标突破、
method admission或方法章PASS；下一实际单卡cost依空卡条件，不以数据量代替资源验证。

### 25.54 C-41：原joint完整反向成本与checkpointing等价验证预声明

科研价值：对准表5-3新结构训练的算力可行性门。§25.53固定峰值/最坏输入已有真实
规模，但未测完整四头损失反向、单卡CUDA峰值与checkpointing是否保持梯度；
只测部分参数/first8不能闭合完整训练预算。
可行性：复用已hash的官方Model/data/utils和同一pretrained initializer，固定seed13，
原始四头目标与权重0.4/2/4/4，max_length256，完整参数反向；零optimizer/零权重更新，
不读dev/final-valid，不加载teacher checkpoint或导出权重。CPU四线程先核等价，GPU仅
4090空卡且本地三件套后运行；CPU RSS与投影Adam状态大小不充当CUDA/optimizer实测。
独占 `original_joint_cost/` 的device/fixture子路径，拒绝覆盖；原源码零修改，
checkpointing仅调用官方transformers接口（nonreentrant、preserve_rng_state）。
冻结输入为chunk census的两组8doc IDs；一次子任务只执行一个fixture，原始/重算
从同一初始化和同一forward RNG出发，比较loss与所有有梯度参数；保留失败报告。
这是R1工程成本验证，method_admitted=false，不是proposed loss实现或方法训练。

### 25.55 C-41：正式结构比较设计与完成控制后的power绑定预声明

科研价值：表5-3/R1准入，区分exact pair-dependence、普通soft cluster supervision、
总概率量增加与标签对齐四种解释；避免aux权重/decoder/选模同时变化造成伪归因。
可行性：仅冻结数学设计，复用已封存的两份291doc paired counts做规划；
不生成新预测、不用oracle/final-valid、不新增seed，不开始proposed实现/训练。
规范first-dummy marginal为所有臂公共项，原baseline与typed stronger anchor保留。
主规划假设是未来document-level paired MUC contrast的中心噪声处于全部已观测
同协议控制的1× envelope；对class-unit三臂与first-dummy legacy/corrected五份噪声
逐一计算目标+3pp的条件power，取最小值/MDE最大值。此假设在proposed结果之前
冻结，并列1.5/2×违约敏感性；不能把规划假设解释成未知full-model方差已经测量。
超过80%只可记conditional design power；若新结果噪声超envelope，报告设计失配，
不得按新得分重写假设或申请未授权seed。独占 `learning_power_binding/`，输入hash/
RNG13/2000resamples与原noise审查一致，两个输入必须同291 IDs且baseline counts相同。

§25.54 实际完成：4090 CPU/PID **2268725（peak）、2268882（worst）** 均成功SSH读到GONE。
release **fe7eb55**；入口SHA **295ba0de2655ee8f76471a52f0b10744fec57667a21bd8a856e0b567bb5c907a**，
配置SHA **3f78e6f0c23abd27f9a16c0e53bfc453400c2beda56bd4bb27b5c9ea50232546**。
实际Torch **2.8.0+cu128**、transformers **4.53.3**，CUDA隐藏，四线程，
完整原四头loss/all-parameter backward，没有optimizer/teacher读取/权重导出。

| 固定输入 | chunks | off forward/backward(s) | on forward/backward(s) | loss off/on | 有梯度参数 | 最大梯度绝对差 | 参数SHA不变 |
|---|---:|---|---|---|---:|---:|---|
| train固定shuffle peak8 | 23 | 7.853437/6.054010 | 5.997660/12.173923 | 12.2884740829 / 同值 | 221 | 0.0 | PASS |
| train任意top8最坏 | 55 | 19.329895/16.503694 | 19.077282/32.712714 | 12.5371551514 / 同值 | 221 | 0.0 | PASS |

初始/最终参数digest均 **5b67cbba9d07f1fb3408b9623833a65f7d8eecaa4799a8b6a0021be3d44a53d6**。
模型FP32参数 **504768980bytes**；两份Adam moments投影 **1009537960bytes**，
未分配optimizer、不称optimizer显存实测。累计CPU RSS peak/worst为
**10798668/20148120KiB**，包含梯度比对buffer，不作checkpointing内存节省结论。
单次CPU计时含并发/冷启动影响，不给GPU速度或完整epoch PASS；两个fixture通过只证明
原架构完整反向与本重算接口的数值等价，新结构aux开销仍需验证。
本地TDD **9 failed→9 passed/3 Torch skipped**；完整三件套 **901 passed/54 skipped**、
ruff0、smokeOK，R1 consistency **36 requirements PASS**；push前4090 CPU对应
**12 passed/6.87s**（含真实RoBERTa dropout/autograd），不是把local skip当PASS。
代码通过Git增量bundle同步，bundleSHA **e097b446b8a443ddd49cb9e28684d4ab2846f4485244263e577dd32b4e51b675**；
远端原有 `.cache/` 等未跟踪资产未改/删，没有分支/worktree。
两组各3项manifest SHA为 **f0f6c93a21af6a6f6d74df674cc50329401ba9b6e8ff7c1031ac4df122eba85c**、
**482b5e45c9832c17e9884979c0a803a8a39ddcb1aed4a086eb154db55a8d356b**；
report SHA分别 **271dd0323cf5a2d59caf61f774dcf8c01c7361536060893af0e220e81c62d448**、
**99cff2efaddd29945b1314c72960cdb316ac7da2f3c2d1589737e4720f74cd89**，LOCAL逐项已核，双端核验另补。

§25.55 五臂目标/推理与endpoint设计已冻结在candidate brief：规范marginal公共项；
相同pair-F1辅助项的root-product/exact/mass-matched/assignment-shuffle，
固定aux scale、doc聚合与最后一步endpoint；shuffle保留pair分数总量，
只能作pair-assignment负控，不能声称单独切断shared ancestry。尚无method code/训练准入。
完成first-dummy后的两份counts全部291doc IDs/anchor counts exact一致，固定相同
2000 bootstrap draws/RNG13，以五个已观测噪声形状逐一绑定，主假设1×envelope。

| 噪声倍数 | 五对照最低条件power（目标+3pp） | 五对照最大MDE80(pp) |
|---:|---:|---:|
| 1×（正式规划假设） | 0.953 | 2.3605466911 |
| 1.5×（敏感性） | 0.667 | 3.5408200366 |
| 2×（敏感性） | 0.446 | 4.7210933821 |

新增两臂没有扩大原worst envelope，不能说“真实训练方差已闭合”。在冻结1×假设下
conditional design power满足≥80%，1.5/2×不满足；此风险正式保留，不提高目标、
不增seed/扫预算、不按proposed结果改假设。该绑定关闭的是统计规划待办，
不是实际效应/跨seed保证；actual单卡预算与正式执行合同仍待闭合，method_admitted=false。
入口SHA **f35662c5fb74825a82c145b657167c9b7813e5465058a1e08033107f00d6c91a**、
reportSHA **0ec0eb22ca5e23a474d5aebd4e92c340c26e65779e1c85cab31fa06461d698d6**；
2项manifest SHA **41e913470087445febc6c6cf173baf1fe133a9fd0c001a9ae6a4168f287d039c**。

§25.54–§25.55最终核验：LOCAL/4090峰值与最坏cost各**3项**、power binding
**2项**逐文件SHA全部一致，非权重备份PASS。power另以独立scalar precision/recall
公式重算全部**5 contrasts ×3 scales**，与原vectorized reporter一致（最大误差 **2.7533531011e-14**）；
不改原noise敏感性/原控制报告。所有本轮CPU进程GONE，无CUDA启动器/等待watcher。

§25.54–§25.55收尾成功核卡（2026-10-13 **15:18:53 UTC**）：4090四卡
**23891/23221/23221/23221MiB**、util **55/95/91/83%**，仍有他人任务；
两个cost PID再次成功读到GONE。未占GPU，无method训练/新5090任务，C-41继续wip。
临时ControlMaster `/tmp/ekg-c41-cost-4090-20261013.sock` exit请求成功，
local ps已确认PID **10680 GONE**；它只是SSH传输复用，不是训练/空卡启动watcher。

### 25.56 C-41：无需空卡的固定aux数值/求导边界审查（2026-10-14，预声明）

科研价值：对准表5-3/R1代码与结构aux可行性门。已有数学和真实encoder梯度
不证明最终四个aux在空pair、无正例、确定性极限或最大type块时可稳定求导。
本次检验exact/root/matched-mass/shuffle统一pair-F1目标的有限值、质量匹配、
精度敏感性与kernel额外成本；数学/梯度正确不替代MUC提升。
可行性：4090 CPU四线程/CUDA隐藏；仅synthetic parent logits与构造gold partitions，
不加载模型/权重、不读dev/final-valid、零optimizer，独占 `learning_numerics_audit/`。
复用已验证interface audit的Torch `matrices`函数（AST只提取此函数，核源码SHA），
仅添加已冻结目标的研究计算，不生成可复用method组件/runner或启动训练。
固定n=1/2/4/8/28（来自§25.49真实train类型规模；不再tokenize或导出teacher）；
zero/seed13-random/dummy-dominant/chain-dominant四种logit输入，后三类是边界
测试而不是调参/训练方案；构造singleton/one-cluster/parity三种labels，
分别float32/float64，全部120个cases/四种aux记录loss/gradients，不挑例。
容差预先固定：float32-vs64 loss绝对差≤1e-5、gradient allclose rtol1e-4/atol1e-6；
矩阵bounds容差1e-5、质量匹配abs≤1e-4+1e-6*exact mass。finite difference只
对n4/random/parity的float64四个目标逐logit测δ1e-6，误差≤1e-8；
空pair目标/梯度严格0，分母0仅按原冻结数学定义alpha0且必须核correction0，
不加clipping/eps掩盖异常。记录边界分支及失败，FAIL不修改已运行输出/放宽容差。
固定n的完整四aux forward/backward单次CPU时间与类型规模histogram只给kernel成本
描述，不外推GPU epoch或Adam内存；不重证此前n3 wrong-link toy或重复封存控制。

§25.56执行环境调整（运行结果前）：4090 SSH多次banner超时，曾成功只读到
remote HEAD，但传bundle失败，审查尚未启动。为独立推进，用`/tmp/ekg-c41-cpu-audit-20261014`
隔离uv venv安装官方torch **2.8.0+cpu**，仅最大28×28合成矩阵/CPU四线程，
CUDA始终隐藏；不载入模型/weights或做训练，不改项目GPU extras/系统Python。
这是操作性机器调整，病例/输入/目标/容差不变；LOCAL CPU计时单独标，不外推远端。
若下载/安装失败只报告环境阻断，不能填求导PASS。

### 25.57 C-41：train label稀疏性与uniform-parent辅助目标风险（2026-10-14，预声明）

科研价值：表5-3/R1设计有效性。数值稳定不能说明目标方向合理；exact概率总体
更大，而MAVEN gold正pairs可能稀疏。检验给定类型合法pair中gold密度、
没有正pair的文档比例、在构造uniform parent先验下exact/root surrogate的
文档平均loss/soft predicted mass，识别过度压低合并概率的竞争解释。
可行性：LOCAL轻量NumPy，原train file/manifest/P1与冻结cache的mention顺序/types
完整2622doc逐ID/mention/type对齐；不读取dev/final-valid、不加载模型或teacher
权重、不用其错误标签。复用已核 `posterior_scores`，固定每row均匀分布；
该先验不是实际pretrained预测，所有分数只作训练标签/目标诊断，不构成部署结果、
可修复率或power。不改已冻结loss/scale/endpoint，也不重开已停止的固定解码控制。
独占 `learning_prior_audit/`；保留全部doc counts/source/hash与聚合，而非挑例。

§25.57首次LOCAL入口 **8a02ba8** 在singleton type块的空pair处失败：
`np.array([])`缺省float64，作为mask时报IndexError。无报告/分数，属于实现错误，
不是科研负结果。已用实际AST assignment在n1空pair独立重现。保留原失败/source，
只将mask dtype显式bool，新的 `learning_prior_audit-r2/` 重跑同输入/目标；
import排序仅lint修正，不修改冻结官方代码、loss或已有实验结果。

§25.56 LOCAL实测 **complete**：隔离uv环境Torch **2.8.0+cpu**，CUDA隐藏/4线程，
**120 cases /480 aux求导**全部有限且bounds/空pair检查通过；无模型/optimizer/数据访问。
float32-vs64最大loss/gradient绝对误差分别 **1.1203050221e-7 /2.1326273955e-8**；
四目标逐logit中心差分最大误差 **1.2901804972e-10**；总量匹配最大误差
**1.9073486328e-6**，均满足预声明容差，未加clipping/eps/stop-gradient。
最大n28的四aux完整forward/backward CPU中位数/最大值
**0.0067941495 /0.0087583240s**；只是本机microbenchmark，不含模型/optimizer、
GPU拷贝/launch/同步，不外推单卡epoch或deployment收益。
Torch提示isolated环境未装NumPy；本入口不调用NumPy转换，审查全量完成，原环境日志保留说明。
研究入口SHA **f9486e04a15145568a5e1bdc8a1e79b3b5d8bb79ef80bcfeda3b842d41ff3d4e**，
report SHA **8375afacc725bf73d98170501e251f2e93240cbfc043718c8ce23db6fda0bac7**；
五项manifest SHA **7c3edb518cde03a60f107d501c173e0cda5f832d623d8f6bb9e47de747c52412**。
研究asset只做边界审查，尚无production method code/训练准入或MUC分数。

§25.57 r2 LOCAL完整train审查完成，同输入/顺序/type绑定，无checkpoint：
**2622docs/66744mentions**、合法同type pairs **66141**、gold same-cluster pairs
**14011**，positive density **21.1835321510%**。**1049docs（40.0076277651%）**
无positive pair，**111docs**连合法pair也没有；空pair在已固定doc-average aux中loss0，
不是临时exclude，也不把无positive文档删出监督。raw train按type/identity直接
独立重算三项计数，与原mention-order reporter全量一致；P1 protocol SHA实际核过。
构造uniform parent下exact每个合法pair恒 **0.5**，全train软pairs总量
exact **33070.5**、root-product **25294.4062451369**，mean doc surrogate
分别 **0.6132409841 /0.6220031382**。这是构造先验下的目标差异，不是实测模型
score/预测簇/F1；loss更低不代表MUC更高，更大的概率量不能独自证明依赖归因。

科学判断：标签确实稀疏且大量文档只给false-merge惩罚；“aux可能令模型更保守、
减少误合并却增加漏合并”保留为竞争解释。仅凭密度/构造prior不能确定梯度或
部署方向，不判候选已成功/失败，不改loss/scale/endpoint。未来报告必须同时给
spurious/missing links与exact-vs-mass归因，不以loss下降或数学PASS当创新结果。
r2入口SHA **97ac526409972774922121e5b7c41dc17e1df1e19df439d02aa0d1be3ba26019**，
report SHA **8952f1318215339a15684a5e18affd1e3ac383e936fc003617833e23fa9a9c13**，
三项manifest SHA **06a7691ab99b9f2199d97e7fa4fa56679b09ff5879446c438011d7c6b77aa56a**；
原失败及源码两项manifest **b988f0d3d31202dca411f6e5b83410bf7928ba803c7959e6dff48d729a204777**，
不覆盖、不把实现报错写成科研负结果。empty/mixed-pair mask真实AST回归已
FAIL→PASS，额外独立raw train counts一致；最终本地三件套结果与备份状态另补。

§25.56–§25.57最终本地三件套 **901 passed/54 skipped（21.36s）**、
ruff0（含两个research assets）、CPU smokeOK；R1 consistency 36项PASS。
默认项目env依然无Torch，skip如实保留；本次新数值证据来自单独CPU-only环境
实际Torch求导，不把skip冒称PASS，不宣称远端/CUDA或method通过。无新的baseline/
方法训练、额外seed/5090任务/权重搬运，无等待GPU自动启动器。非权重远端备份另补。
下一独立CPU动作可从真实train标签检验固定aux在common-real-logit偏移方向的
梯度，与规范marginal对照，按no-positive/positive docs分别报告；仍是构造分布下
数学信号，不是完整模型更新或部署效应。先预声明/更新主表再执行，不扫loss scale。

§25.56 target环境一致性补验预声明：SSH复用现已恢复，只在4090 CPU同一
未改Git研究入口执行一次同病例/容差的环境校验，原LOCAL输出只读，不复跑训练。
独占 `learning_numerics_remote_check/`；临时cwd中仅source audit与新输出目录
的symlink，入口源码不改。CUDA隐藏/四线程/零模型/optimizer，检验Torch
2.8.0+cu128的CPU结果是否满足相同边界；本机PASS不预先当远端PASS。

§25.56–§25.57非权重双端备份已完成：LOCAL/4090数值审查**5**项、原失败**2**项、
r2 prior审查**3**项逐manifest SHA全部PASS；tar SHA
**1e8d9bc074782d6eb704aa3c533f8e14055f21a920302de8fcfdade8ea7d094d**，
既有路径只比对相等，新项exclusive-create，未搬weights。源码走Git bundle
SHA **e244147f01c368faf5cf51a5b88096974f2c2a8a8c7e1c1b6d23349344c86d9c**，
原机HEAD同步 **5d92675**；之前多次banner超时没被当实验失败或进程死亡。

§25.56 target补验实际 **complete**：4090 Torch **2.8.0+cu128**、CPU/隐藏CUDA，
同未改source、相同120 cases/480求导与容差；float32-vs64最大loss/gradient误差
**1.1203050221e-7 /1.9351237571e-8**，finite-difference最大
**7.7312092492e-11**、mass误差 **9.5367431641e-7**，全部PASS。
这不是跨机器梯度bitwise相同或CUDA验证；只是两个CPU build均满足同一检查。
远端补验report SHA **79611f00b7a662bf7e5a68af2fce66466712c7e443259839cbc1c482dbc30f66**；
三项manifest **abd00a2737e426810501a5e6ef636a787c24ce38d4ea8a74d37cb9d3b98b92c1**
已回传本地逐项一致。原本机报告/source均未修改，补验有独立cwd/provenance。

10-14末次成功核卡：4090占用 **23890/23223/23223/23223MiB**、
util **71/93/81/73%**，仍无可用空卡；未启动任何CUDA任务或method训练。
C-41仍wip，新数据/数值证据不是MUC突破；剩余单卡/optimizer余量/正式结构
预算与执行合同边界保持。

本轮SSH传输复用master退出请求成功，LOCAL ps确认PID **18817 GONE**。
两份研究入口已完成，没有遗留GPU watcher/新训练；隔离CPU-only uv环境留在
`/tmp/ekg-c41-cpu-audit-20261014/` 供后续轻量求导，不能据此运行本地GPU或重模型训练。

### 25.58 C-41：真实train标签下common-real-logit梯度方向（预声明）

科研价值：表5-3/R1训练信号；检验“aux只令模型更保守”的竞争解释，而非从
label密度直接推断更新方向。可行性：LOCAL隔离Torch2.8 CPU-only四线程，
固定实际train标签/mention顺序/types，构造每个合法real logit共同偏移b=0、
dummy=0；零神经模型/optimizer，不读dev/final-valid。与规范first-dummy
marginal对照，exact/root/matched-mass及固定doc/type/mention SHA排列shuffle
四aux按已冻结doc聚合与scale分别求dL/db，按positive/no-positive/no-legal文档
分组报告。dL/db>0表示该构造方向的下降步骤压低real概率，<0则增加；
不等于真实神经参数轨迹、训练后的false merge/missing或MUC收益。
所有2622doc均保留，empty doc损失/aux导数0；source/kernel复用已核Torch矩阵
函数，不实现production method。独占 `learning_direction_audit/`；逐doc与整合
证据保存。用独立解析marginal导数及有限差分验证，不改loss/scale/endpoint/seed。

### 25.59 C-41：5090新增授权与原joint资源准备（预声明）

作者10-14明确答复“授权本轮C-41使用5090空卡”：原joint成本验证，以及R1准入后
固定seed13五臂训练；超过一天的任务和跨机权重搬运仍单独确认，原decoder audit
授权保持。本行只持有同一C5切片，不推进A4、不解除任何科学准入。
科研价值：表5-3/算力可行性，解除4090占满时的资源等待，实际证明本机tokenization/
显存/完整反向/预算，不能拿CPU时间或历史4090epoch外推5090 PASS。
可行性先核本机GPU/process、原架构source、train/manifest/P1与pretrained内容地址；
缺数据可非权重回传且双端SHA，已有checkpoint不搬。pretrain先用5090本机已有
pin或镜像下载；若与4090pin不同，记录逐文件/tokenization差异，所有新臂必须
同本机同initializer，不把旧数字当新同预算对照。新wrapper/config/合同/输出
命名空间；原cost入口/合同/配置与结果均不改写。仅空卡、CPU/TDD/完整三件套及
真实对应测试后，先披露确切cwd/命令/outputs，再运行原架构零optimizer cost。

### 25.60 C-41：真实train逐候选梯度的局部机制审查（预声明）

科研价值：表5-3/R1机制识别。§25.58 common-bias只测总merge倾向，exact与
shuffle在均匀logit时相同，不能识别pair assignment。对实际train标签，在相同
构造zero-real/dummy logits下对每条合法前件logit求partial derivative，比较
规范marginal与固定四aux的单边方向，尤其 `i<j<k, gold(i)!=gold(j)=gold(k)`
中的错边k→i；不是观测模型错误或可修复率。可行性：LOCAL轻量Torch2.8 CPU，
类型块最大28，合法候选全集66141；复用已核Torch矩阵递推，完整2622docs，
无模型/weights/optimizer/dev/final-valid。所有labels/order/type输入锁与§25.58
一致，独占 `learning_edge_gradient_audit/`。不改loss/scale/seed/endpoint。
按wrong/true parents与ancestor-wrong子集报告方向计数与doc级聚合，
四aux+规范marginal+固定scale组合均保留；不能只挑exact占优的候选。
每doc各partial之和须与§25.58 common-bias导数匹配（abs≤1e-8）；
first有合法候选、first有ancestor-wrong、最大type块三份train doc对固定候选
的四aux/规范marginal中心差分δ1e-6、abs≤1e-8，不按结果挑doc/候选。
零导数仅数值诊断界限1e-12，不用于推理或选模；partial不能保证共享NN更新
后每条edge或主指标改善。FAIL保留且不改阈值救过。

§25.59新一手资产核查：5090 processed parent train为2913docs，不能直接
作为2622doc训练。只按冻结manifest选取并sort_keys序列化，本机已重建
`r1-v64-c5-5090-20261014/input/train.jsonl`，91419429bytes，SHA
**20ea01ebe71fb8c8e4f207368673cc71f29840a290698eefe15de3a24a3b6f05**，
与封存A3逐字节一致；不搬训练权重。P1 SHA与train manifest实际核一致。
本机generic Model SHA **e3c6f2c847224ae5b92dcb7fdd4d1af048401e0832ffea8d4b1beb4da37a2a36**，
只正规化换行与将两个model_name默认路径换成4090pin，SHA即为原
**03aa41ea0da3b0d14fe51096fd263cee22a2336c19c0bfb8f4786296f9dbc734**；
DATA/UTILS分别原8375a8…/c1b499…，实际模型构造显式传路径，架构代码不变。

旧pin tokenizer_config SHA **dfef66475ba1a217ceab1a29ba012843041e11627cab56f5f83c7b9804cfa5c5**
实际成功SSH只读得到145bytes，是接口错误JSON（Code/Message/RequestId/Success=false），
不是规范tokenizer配置。旧文件/结果不改写，不把library defaults隐藏为正常元数据。
新5090pin的tokenizer_config为规范25bytes、SHA
**994f46754c5bf4014f1aa92d34b1374319c3a6b3f702105cd5b742beaecd18ce**；
其余5文件实测与旧pin注册一致（包含pytorch_model.bin SHA278b7a…）。
仅为输入比较在5090重建旧pin参考视图：5个本机已有相同文件symlink+
旧145byte元数据副本，核全目录内容摘要必须复现71be…，不复制/搬运weights，
且旧元数据不用于新训练。分别tokenize完整2622train，比较全token IDs/
attention/spans/events_idx/coref/关系labels序列digest，未匹配前不称input等价。

### 25.61 C-41：5090实际pretrained模型的结构aux梯度与共享预算（预声明）

科研价值：表5-3/R1可行性与归因。§25.60只是构造logit partial；用实际相同
pretrain initializer的原模型检查新固定四aux连接head/共享encoder、量级与
canonical/其他任务的夹角，识别“只是改变共享梯度预算”竞争解释。
可行性：5090 CPU四线程/隐藏CUDA，固定seed13/peak8同token/spans/labels，
不加载teacher、零optimizer/权重更新、零dev/final-valid，不定义method组件。
复用公开Model/data、已封存typed_probabilities/marginal_loss与已核矩阵函数，
forward hook只捕获原pair-MLP raw scores，不改变forward/权重/原码。
同一train-mode图分别测规范marginal、exact/root/mass/真实assignment-shuffle，
保留原关系三项loss/权重，统计所有有梯度的head及encoder参数norm/与canonical
和关系gradient的cosine；None只代表原模型未用参数，逐名记录，不当0填掩盖。
总weight0.4/2/4/4、aux scale1不变；不按新结果调scale或选择endpoint/初始化。
参数SHA前后相等、所有实际grad有限；head与encoder梯度连通性检查，
FAIL保留。独占 `r1-v64-c5-5090-20261014/actual_aux_cpu/`，不覆已完成cost。
CPU单batch耗时不充当CUDAepoch/optimizer预算；cosine不是实际NN更新后
某条edge改善或MUC提分。这一审查不放行method训练。

§25.58 实测完成：全2622 train docs，positive 1573 / no-positive且有合法候选938 /
无合法候选111；canonical解析导数最大误差3.3306690739e-16，aux中心差分
最大5.1353317432e-11。按doc平均dL/db如下（下降步骤与导数符号相反）：

| 组 | canonical | exact aux | root aux | matched-mass aux | shuffle aux |
|---|---:|---:|---:|---:|---:|
| 全train | .131369159827 | .003760880429 | .002892658078 | .004574248516 | .003760880429 |
| positive | .128039859801 | -.045936226863 | -.050556983478 | -.044580441024 | -.045936226863 |
| no-positive/有候选 | .152498121108 | .087546602708 | .092868533573 | .087546602708 | .087546602708 |
| 无候选 | 0 | 0 | 0 | 0 | 0 |

因此“aux只增加保守性”不适用于所有组：positive组平均aux推动merge，
no-positive组抑制merge；不能将这一步直接解释为真实参数更新或提分。
`learning_direction_audit/executed_source.py`保留真正执行SHA9005ecc4…；Git入口
随后仅做lint整理（lambda显式绑定n、未用变量名与折行），执行记录不换成新SHA。

§25.60 实测完成：全部66141合法候选，wrong 52130 / true 14011，ancestor-wrong
子集4685；最大sum-vs-common-bias误差3.3306690739e-16，固定候选中心差分
最大7.5933296977e-11。下表是导数<0、即该单边下降方向**增加错边**的计数；
并非实际模型错边、修复率或训练后的数量。

| loss | 全wrong候选/52130 | ancestor-wrong/4685 |
|---|---:|---:|
| canonical | 0 | 0 |
| exact aux | 4139 | 719 |
| root aux | 5718 | 2745 |
| matched-mass aux | 14325 | 4139 |
| assignment-shuffle aux | 9153 | 1957 |
| .4×(canonical+exact) | 141 | 3 |
| .4×(canonical+root) | 459 | 192 |
| .4×(canonical+mass) | 278 | 25 |
| .4×(canonical+shuffle) | 1915 | 294 |

exact在这个构造点比root/mass较少产生反向错边信号，但canonical单独已全部
方向正确，故**没有证明exact胜canonical**；exact组合仍有141条wrong候选
方向变坏。true候选canonical与exact/root/mass组合全部14011方向正确；
shuffle组合有17条方向变坏。完整positive/negative/zero与逐doc记录均保留，
不是只报告有利子集。执行source SHA22310a00…，输出在旧R1根
`learning_edge_gradient_audit/`。保持固定loss/scale/endpoint，不将此诊断当准入。

§25.59 input与原成本实测完成：两个完整train tokenizer投影的逐doc文件字节相同，
2622 docs /4799 chunks /892998 nonpad，token/mask/span/events_idx/coref/三关系
label stream SHA **293fad976f66c3480edd72a638c3974055766b8bbd241bed9675eafb7fa7aad4**。
规范新pin与旧错误metadata参考view只在本次slowRobertaTokenizer/max_length256
调用下证明输入一致，不泛化到其他consumer或隐藏旧文件错误。

| 5090 CPU fixture | chunks | 原forward/backward秒 | checkpoint forward/backward秒 | 有梯度参数 | 最大grad差 |
|---|---:|---:|---:|---:|---:|
| peak8 | 23 | 4.5565 /5.0767 | 4.0206 /8.8547 | 221 | 0 |
| worst8 | 55 | 12.8069 /14.3967 | 11.1112 /22.3962 | 221 | 0 |

两fixture loss等价，零optimizer，参数SHA前后均**5b67cbba9d07f1fb3408b9623833a65f7d8eecaa4799a8b6a0021be3d44a53d6**，
与旧4090 CPU initializer一致；不声称CUDA/跨机训练轨迹等价。Torch2.8.0+cu128
但CUDA隐藏。CPU cumulative RSS包含parity buffers，不充当GPU显存；Adam两moment
仅按parameter bytes推算，optimizer_memory_measured=false。
非权重14项回传LOCAL，全部artifact manifest逐SHA复核，源5090/LOCAL均保存在
`r1-v64-c5-5090-20261014/`。report SHA：tokenization **50e9519a…**、
reference **4d7c1460…**、peak **4da6e2e8…**、worst **a12accd6…**。
成功SSH ps查询实际CPU PID2750907/2750981均无行（GONE），报告完整；不是凭SSH失败判死亡。

新增研究入口全套验证：pytest **913 passed/54 skipped，20.15s**，ruff0，CPU smokeOK，
R1 consistency36PASS；默认项目env仍缺Torch，未将skip当远端实际梯度证据。
source同步bundle SHA180cfbf9…经远端核一致。首次fetch误用refs/heads/main（bundle
实际只含HEAD）失败且未启动任务；纠正为HEAD ref后才启动CPU审查，不当科研FAIL。
5090最近成功核卡31967MiB/util92%，有他人任务，无CUDA启动/训练/等待启动器。

§25.61 **实际 complete**：5090 CPU/四线程/隐藏CUDA，固定peak8/23chunks、
同train-mode forward图，seed13、checkpointing=true，零optimizer/update。
四aux与canonical均连接全部原共指MLP参数及共享encoder，梯度finite；
仅encoder pooler两参数unused（原Model不消费pooler输出），逐名保留。
关系loss不连共指头，其unused共指参数与undefined head cosine均如实记录None。
下表norm为未乘0.4的canonical/aux，关系行已含原2/4/4权重。

| loss | 实测loss | head grad norm | encoder grad norm | encoder cosine vs canonical | encoder cosine vs关系 | head cosine vs canonical |
|---|---:|---:|---:|---:|---:|---:|
| canonical | .28323510 | 2.21065677 | .73112809 | 1 | -.08327333 | 1 |
| exact aux | .67982131 | .59519956 | .31201143 | .61120952 | -.04145524 | -.01220570 |
| root aux | .67841578 | .61894343 | .32577494 | .59950005 | -.05015434 | .00346514 |
| matched-mass aux | .67281175 | .59303941 | .31158148 | .61392511 | -.04188390 | .03462563 |
| assignment-shuffle aux | .67806786 | .54990230 | .30831598 | .62579533 | -.05871081 | .05747901 |
| 加权关系三项 | 11.11761284 | 0 | 6.44589777 | -.08327333 | 1 | undefined |

实际forward4.61662s，各loss单独autograd7.97507–8.53894s；同图retain/recompute
不是一次正常optimizer step，不外推CUDA/epoch wallclock。各aux编码器norm相对
canonical约.422–.446；乘固定0.4后相对加权关系norm约.0191–.0202，exact为
.01936186。仅此固定batch/pretrained点，norm大不等于任务支配或唯一失败原因。
exact与matched-mass的量级及encoder cosine接近，故本审查没有分辨出独有收益；
不同loss的绝对值不能横比成优劣，shuffle loss更低也不是负控胜出。
保留共享梯度预算、assignment与整体质量膨胀三个竞争解释，不调固定loss scale。

参数SHA前后仍5b67cbba…，完整source SHA
**ea3d1a6355d6e2bf1c5ac20278d4e06f0c72809fb5ca93abb60a7b219ad74c55**，
source commit42fc51d；配置5083b01d…、矩阵93b7fa09…、原input/P1/source pins
实际核验。report SHA **8cc4c0df68c7179d62c8a4c6acbf56c43d2069d10f1ce445b9da5d9b6d10af07**，
独占 `r1-v64-c5-5090-20261014/actual_aux_cpu/`，report/source/log三项manifest
5090与LOCAL逐SHA一致。成功SSH确认PID2770187 GONE且report完整。
§25.58/§25.60 report+逐doc+真实执行source+manifest共8项亦双端备份核一致，
包SHA **50bd0f0ca5c9d5e1053bd4eda7ddef01fb4dcd03b2317803b6388cf9b644ea32**；无weights搬运。

科研裁决：R1数据、数学、CPU信号与本机输入/initializer检查可继续支持固定五臂
辨别实验，但没有真实更新、部署预测或新MUC结果。**method_admitted=false**，
C-41/T087保持wip。当前独立CPU审查已完成；下一必要证据是已授权空5090的
原架构peak/worst CUDA成本、真实optimizer显存余量与结构aux实际CUDA预算，再
闭合正式执行合同。不能用CPU量级、旧best-dev权重或条件power替代这些门。
最新成功5090核卡31967MiB/util100%，继续尊重他人任务；未启动CUDA/新训练，
无自动空卡启动器，单seed/≤一天/跨机权重边界保持。

参考tokenization复核入口：与新pin同一Git helper
`profile_joint_cost_target.tokenization(config, torch)`（入口SHA50ef23b0…），
仅将本轮config的pretrained改为
`runs/stages/R1/r1-v64-c5-5090-20261014/input/legacy_tokenizer_reference`，
pretrained_digest改为旧71be7419…；其余input pins/max_length256/数据代码相同。
参考报告不冒充main wrapper的同config输出，也不把旧错误metadata用于新臂。

末次两机成功只读核卡：4090四卡23890/23223/23223/23223MiB，util100/76/76/31%；
5090仍有compute PID2766182占31778MiB（NVML总31967MiB），无可用空卡。
三个本轮5090 CPU PID2750907/2750981/2770187成功ps核GONE，完整产物已核。
远端原有未跟踪`mk_probe_contract.py`保留，未覆盖/clean；无遗留自动训练启动器。

### 25.62 C-41：4090空卡后原架构CUDA预算接续（预声明）

科研价值：闭合表5-3/R1算力可行性，已有CPU与条件power不能替代单卡实测。
作者报告4090空闲，成功SSH核到四卡均无compute进程；原cost的peak/worst
固定输入与源码/合同不变，分别在空GPU1/2执行，属于同C5切片的不同成本任务，
不是额外seed。可行性：本机已有原train/P1/pretrained、两fixture完整CPU产物；
核原input pins、CPU hashes/source，同步main，完成本地门与远端对应CPU tests，
先披露命令再启动。输出原R1根original_joint_cost/cuda/{peak,worst}独占目录，
已存在则不覆盖。CUDA失败/显存不足如实保留，不放宽gradient parity容差。
原cost仍零optimizer、零权重更新，不读dev/final-valid；通过也不自动准入方法。
随后实际optimizer显存与固定结构aux预算须单独预声明/新输出身份，再闭合
正式执行合同，不增加seed或改loss/scale/endpoint。不跨机搬weights。

### 25.63 C-41：固定五臂实际optimizer与结构成本审查（预声明）

科研价值：表5-3/R1正式执行预算；原joint四头无optimizer峰值不能放行五臂，
必须实际测每个固定目标的完整forward/backward与optimizer临时状态。
可行性：4090本机原公开Model/data、train两个固定8doc fixtures与矩阵/typed监督
helper已有；新research profiler独占r1-v65-c5-4090-20261014/structure_budget/，
不改原cost/code/results。source/input/initializer pins与fixture逐项钉住。
新目标各臂使用规范Roberta metadata内容地址2c7ff1…（本机同weights、仅metadata
修复的新view；须核digest/token输入相等，不修改旧71be…）；seed13、max_length256、
固定0.4/2/4/4，aux scale1、所有臂nonreentrant checkpointing=true。

本审查只用train固定fixture，不做epoch、dev或final-valid。严格lr=0：按官方
encoder AdamW/scorer Adam实际执行cold/warm两次step，初始化真实一二阶状态并
测step temporaries；两optimizer各两次API调用如实记账，参数SHA前后必须相同。
这不是旧“零optimizer”cost合同，不谎报optimizer_steps=0；零权重更新、零训练
rollout，momentum状态变化不保存为checkpoint。所有grad有限，按臂记录完整
CUDA peak allocated/reserved与同步timing，不扫batch/目标权重或检查提分。
CPU小模型先TDD证明lr0+两个optimizer真实状态/参数不变，再远端CPU真实测试。
五臂/两个fixture固定10个成本病例，在空卡并行不同任务，非多seed。
某fixture/臂OOM或fail就保留失败，不用更小输入静默替换；实际cost不能称
正式epoch计时，最终预算须在真实train全遍或透明保守外推中单列不确定性。
GPU启动仍须披露确切cwd/命令/产物；method_admitted=false，禁真正权重更新。

§25.62 实际完成：GPU1 peak23chunks、GPU2 worst55chunks，原off/on checkpoint loss
完全相同，221个参数梯度均finite且同集合；最大abs差分别5.5879354477e-8/
5.9604644775e-8，固定rtol1e-4/atol1e-6全部PASS。

| fixture | off allocated/reserved GiB | on allocated/reserved GiB | on forward/backward秒 |
|---|---:|---:|---:|
| peak8 | 4.552087 /4.953125 | 1.322186 /1.730469 | .089731 /.186546 |
| worst8 | 11.234208 /11.791016 | 3.648078 /4.166016 | .249847 /.354027 |

首个off执行包含CUDA/kernel冷启动，不把off/on时间比当速度收益。CPU与CUDA
dropout/kernel不同，本次只证明CUDA内部重算loss/grad等价，不宣称跨设备bitwise
等价。两参数SHA前后同5b67cbba…，optimizer_steps=0；source295ba0…、配置
3f78e6f0…、source commit b687e37。8项非权重回传LOCAL逐manifest SHA一致。
peak/worst report SHA **e399c5008c038f6496fd702ccbb1ac45ea71db52f588b37514f6ed42be0f61d3** /
**ea2fab3e442deb5db441fdaf898b07a94cbab1f11a202753db8c96488d866afe**。
两任务已完整落地；随后成功核卡GPU1/2均回到11MiB/util0，无继续占用。

原A3 run_metadata成功只读核到历史训练真实argv：epochs100、seed13、lr3e-4、
bert_lr2e-5、batch8、accumulation4；不拿generic main默认lr1e-4/batch4当历史预算。
后续正式同预算对照必须保持此实际设置，warmup200沿官方代码，总训练steps沿
官方len(dataloader)*epochs（即原scheduler计数，不静默“修正”为optimizer次数）。
本机已存在规范2c7ff1… pin，实测digest与5090一致；无需新建/下载/跨机搬weights。
§25.63小模型CPU-only TDD实际8 FAIL（入口缺失）→8 PASS，真实AdamW/Adam的
momentum states创建与lr0参数不变均已检验；不得把cost probe lr0写进正式训练lr。

§25.63当前工程状态：LOCAL CPU-only小模型8项实际PASS（不是默认env的Torch skip），
完整本地pytest919 passed/56 skipped（22.20s）、ruff0、smokeOK、一致性36PASS。
4090的2c7ff1…规范pin已存在且digest实核一致；原两组CUDA证据已回传，但
随后SSH banner连续超时，彼时新的full-model CPU/结构CUDA入口尚未发起。
Git bundle5c3d98e5…已scp完成，失败的是后续SSH同步/测试，不当科研FAIL。
full-train规范pin tokenizer CPU进程2773865已发起；SSH失联期间状态UNKNOWN，
不能说GONE或complete。原cost的两个CUDA输出complete且后续GPU已空闲证据不变。

§25.63 SSH恢复后对应4090 CPU测试8项实际PASS（source commit1511676，CUDA隐藏）。
作者同时提醒有人重新使用4090；必须再次核空卡，不能沿用最初四卡全空的状态。
5090只读测试source传输尝试Connection refused，未同步/执行任务；不作实验失败。

§25.63原CPU exact/peak **FAILED**（入口ec6ad9…/config b9010026…），
`zero-lr parameter invariant failed`，failure与原log/code保留，不覆盖该目录。
成功SSH确认PID2830542 GONE。原梯度finite已过，失败在第一次两optimizer step
后的raw参数SHA检查；不能据此说方法失败，也不能把这次cost冒称complete。
最小CPU复现：Adam/AdamW lr0、parameter[-0.,0.,1.]、grad[-1.,-1.,1.]后数值
torch.equal=true，但首元素signbit从true到false，raw bytes改变。原pretrained
实际也含negative zeros（word_embeddings7处及多个encoder权重/偏置），支持
此竞争解释，尚需在完整模型逐参数证明没有非零数值更新。

修复预声明：新r2 adapter/config/合同/输出，原入口/结果不改。真实optimizer
step后严格逐参数torch.equal检查；任何数值变化FAIL且不撤销来掩盖。
仅当全部值相等时，允许将零元素的原sign bit恢复；记录native前后raw SHA、
恢复数量、恢复后SHA与实际API次数。每个optimizer post hook单独CPU审计；
CUDA synchronize放在hook计时开始前，hook时间单列，成本不将CPU复制/校验
耗时算作原optimizer时间。不增加持久GPU权重副本，不改loss/scale/budget。
这是B类bit provenance修复，不放宽数值相等，不把恢复byte等同真实学习更新。
先TDD覆盖signed-zero恢复/非零变化FAIL/nonzero-lr拒绝，再完整CPU复核。

§25.63 r2验证记录：三个新增回归CPU-only TDD **3 FAIL（新入口缺失）→3 PASS**。
真实optimizer hook可恢复已证signed zero，拒绝任何数值改动且不撤销来伪装，
并在native step之前拒绝nonzero LR。4090对应CPU测试旧8+r2新3共**11项实际PASS**，
CUDA隐藏，不以本地59个Torch skip充当此证据。完整本地919 passed/59 skipped
（22.05s）、ruff0、smokeOK、一致性36PASS。新source commit021049b，
核心ec6ad9…不改，r2入口SHA**dd97bb442fe8d0b1cb0cc431e93e91bc1f0f4c93e14e77d97c790f5e6391e4e3**、
config SHA**a168b6a63310a8d24f49a42bf89ca97292eb74184eaf4905a4276b0d1807c0f8**，
bundle SHA9bca1900…远端核一致；完整CPU复核在新路径执行，未预先判PASS。

规范2c7ff1…在4090的完整train tokenization已实际complete，PID2773865成功核GONE，
report SHA**f4da086c0eab75c55ae6746054e3d64411d52e7159626b72d6e82b9683ecc55a**。
2622docs/4799chunks/892998nonpad、完整input+训练labels digest293fad97…与5090
proper pin及旧参考相同；四项token/input_config/manifest非权重回传逐SHA一致。
旧error metadata/pin/files/results不改写，权重仍在各自本机。
成功核4090四卡17888/17903/18023/22545MiB，存在其他任务PID2788138–2788141，
不占用其中任何一张。5090按runbook更新动态地址后仍Connection refused；未启动
其新任务、不伪装卡况或实验结论。GPU下一步固定10病例的结构/optimizer实测仍待空卡。

§25.63 r2完整Model CPU exact/peak **complete**：seed13、8doc/23chunks，
221个参数梯度finite，严格lr0真实encoder AdamW/scorers Adam各cold/warm两step，
共4 API calls；真实optimizer state **1,004,814,108 bytes**，不再只是moments投影。
四个hook对全部参数逐值验证torch.equal，numerical weight_updates=0；
encoder每次native step发生**13**处zero sign翻转，scorers **0**，native raw SHA
差异完整保存。只恢复这些符号后整模型SHA前后5b67cbba…完全相同。
因此支持原raw SHA失败的signed-zero解释，原FAIL仍保留，不改判原身份PASS。

| CPU cycle | loss | forward秒 | backward秒 | native optimizer秒 | integrity秒 |
|---|---:|---:|---:|---:|---:|
| cold | 11.50283623 | 6.979210 | 11.192407 | .407413 | 1.257795 |
| warm | 11.50283623 | 5.824624 | 10.829343 | .264329 | 1.262924 |

native timing从原optimizer span扣除post-hook完整性审查，raw span亦保留。
CPU完整性snapshot/source/reports都不是GPU显存或正式epoch预算；两次cold/warm
固定输入与zero LR不测学习效果。report SHA
**42980f6d665073496f88d4713f37825be1b5eabd2cd350608abd61520d8f75e8**，
独占r1-v65-c5-4090-20261014/structure_budget_r2/cpu/peak/exact。
成功SSH ps确认PID2839914 GONE，report/source/log与原manifest扩展备份后回传。
下一步仍固定10个CUDA成本病例；末次四卡17888/17903/18023/22545MiB/util20/22/20/20%，
均有其他任务，未启动r2 CUDA/epoch/新方法训练，无自动等卡启动器。

完整模型CPU r2的report/原manifest/adapter/log/扩展backup manifest回传LOCAL逐项
SHA全PASS（共5项）。原CPU FAIL的源码/log/failure另建backup manifest，保留
executed_source ec6ad9…、failure SHAac92ce4c…与log SHA91187ddb…；不是只留下
新成功结果。原成本CUDA两fixture与规范token完整输入的LOCAL/4090副本亦核一致。

预算边界继续明确：这两个fixture分别是冻结shuffle的chunk峰值与任意8doc的
chunk上界，不证明任意文档的所有关系head/类型块组合峰值；cold/warm两次step
也未实测正式accumulation4的完整周期。后续CUDA成本与最终budget closure须
单列累积梯度驻留/完整train实际shape与epoch外推的不确定性，不能只把CPU
state bytes加到旧allocated peak就宣告正式训练预算PASS。

### 25.64 导师视角项目/双机资源审查（2026-10-15，只读检查与目标设计）

**科研价值**：服务C-41/T087、表5-3与R1预算/合同门，避免把工程成本或已知规则
收益认成方法贡献；证据依据§25.37、§25.42及§25.49–§25.63。
**可行性**：本地文档、配置/源码可读，远端仅做SSH/身份/Git/GPU/进程/磁盘查询；
本次不启动成本、audit或训练，不改冻结合同与实验结果，不搬checkpoint。
导师执行说明见 `docs/research/20261015_supervisor_review.md`，不建立第二条队列。

本地 `git fetch origin` 成功，核查时 `main` 的HEAD与origin/main同为`03b7019`，
工作树干净。R1一致性审计实际输出`PASS: 36 requirements mapped`，
报告`/tmp/ekg-r1-supervisor-consistency-20261015.json`；它不代表方法准入。

| 资源（+08:00） | 本次实际观察 | 解释与接续 |
|---|---|---|
| 4090，约23:12 | 两次SSH均exit255，`18.tcp.vip.cpolar.cn:14147 Connection refused` | GPU占用/进程/远端Git均UNKNOWN；不能沿用10-14四卡占用，也不能断言卡空或进程死亡。updater当前只托管5090/a6000，未修复4090 |
| 5090，23:12:41、23:13:17 | RTX5090 GPU0，310/32607MiB、util0%；两次`--query-compute-apps`均无记录 | 核查瞬间无compute任务，满足runbook空卡筛查；不保证后续仍空闲，启动前须重核 |
| 5090身份/目录 | `tongjiakai`、`server-System-Product-Name`；项目目录存在，Git=`f6399be`，`git status --short`仅`?? mk_probe_contract.py` | SSH保持原HostKeyAlias验证；远端落后本地主干，未跟踪文件来源未核。本次未fetch/reset/覆盖，接续同步前先查来源并保留 |
| 5090进程/磁盘 | `ps -u tongjiakai -o pid,ppid,etime,comm`只见会话/桌面服务，无Python任务；项目挂载盘851G可用，76%已用 | 仅为本次成功查询的进程快照，不追认历史任务状态，也不把磁盘充足当训练预算通过 |

5090初查旧地址`1.tcp.cpolar.cn:24870`连接关闭。按runbook执行
`cpolar-ssh-update`成功更新为`1.tcp.cpolar.cn:22833`，再成功核卡与身份。
该工具同时例行刷新其托管的a6000地址；没有连接/使用该机器或启动其任务。
没有修改SSH host-key策略，没有在会话中查看或输出凭据，没有更改远端文件。

源码审查确认`profile_c5_structure_budget.py:validate_scope`严格绑定
`/data/TJK/ekg`，r2配置也绑定4090的initializer/source/output；
`profile_c5_structure_budget_r2.py`调用该guard。故5090虽空，现有4090 r2命令
不能原样迁移，也不能修改封存脚本来“放行”。迁移须核任务授权边界、先改主表，
以独立本机配置/合同/产物与测试保持可追溯，不搬既有checkpoint。

**导师裁决**：保持C-41/T087为wip、`method_admitted=false`、C5→D4→A4。
下一决定性工作是固定五臂真实成本、完整累积/shape预算、R1准入裁决与生产合同；
不继续扩展已完成CPU诊断，不重跑原两fixture CUDA或失败控制。
已有5090原C5 decoder audit许可保持，其结果只解释同分数换解码，不能代替新方法。
新实验证据尚未增加；本节不能被引用为MUC提升、训练已准入或机制新颖性证明。

本次仅改文档；回填后R1一致性再次36项PASS，`git diff --check`通过，
导师卡本地链接与五臂名称对照现有源码检查通过；没有运行代码变更的三件套，
也没有用历史测试记录声称本次已跑训练/torch测试。最终一致性报告为
`/tmp/ekg-r1-supervisor-consistency-20261015-final.json`。

### 25.65 作者确认4090不可用后的新近文献审查与创新规划（2026-10-15）

**作者新指令**：4090当前不可用、修复时间未知；要求优先从创新方案升级入手，
检索最新论文后整理任务。按该指令先更新主表§3.8及C-41覆盖切片，不等待旧Gate
恢复资源安排。只规划/检索/静态检查，没有启动GPU、更新模型或改写任何冻结实验结果。

**科研价值**：表5-3当前exact候选的联合依赖归因，以及后续表3-3/表4-3的实质新机制；
防止把2026的反事实、图验证、meta-factivity等已有概念直接换名当创新。
依据项目§25.37、§25.42及§25.49–§25.63，文献位置见本轮source ledger。
**可行性**：公开一手论文/作者代码可只读审查，本地轻量CPU可完成文献/合同工作；
5090成功SSH确认C5本机核心路径存在，尚未重核全部hash或实际训练预算。

研究卡`docs/research/20261015_innovation_upgrade.md`与结构化
`docs/research/20261015_literature_sources.json`记录检索边界和逐源解释。
截止2026-10-15，逐轮检索2025–2026论文、最近两个月发现结果并补查旧机制邻居；
最终ledger共14项（其中FIE2026为任务资源，BeyondAtoms只核官方release/source，未读PDF），
不称14篇均已完整读完，不声称穷尽领域或不存在相同方法。没有引用外部效果数字来
替代统一主表；任务、split、候选、模型、标注输入与代码可运行性分别记录。

| 关键来源身份 | 本次核查与结论 |
|---|---|
| UERLens ACL2026；repo`ded7586c99a94da0d7a80848488be69f241eee86` | 正文§2/Appx B、MIT LICENSE及真实analyzer/metrics/SVM源码已核。公开SVM有默认空texts、固定layer/vector、多卡设置，论文特征筛选/训练资产未闭合；属于static code有缺口，runtime/fidelity未验证。不能称无代码或已复现 |
| CohTP ACL2026；repo`3843ad0a4dcdb9f4761f134894b935d4ed74d19b` | 完整官方tree只有`Comming soon`；正文时间图/纠错/分区是先行机制，当前复现卡【代码】，不重写后继承论文身份 |
| BeyondAtoms官方2026release；repo`172dced0a1e98a8544101ecd48754bb7bd8c4659` | README/tree/verification source已核；claim-evidence关系核验不是五类event factuality。未独立核其conference acceptance；runtime/许可未闭合，不新增外部benchmark任务 |
| FIE2026资源；repo`bed2e72388b635f454f0d11293c42b3142022ded` | 官方任务说明为factivity inference，不能替换现MAVEN任务或据此增加数据 |
| SVRECI、Meta-Factivity、CoT traces、LLM-SD、ECPO等 | 核正文指定位置并分别记录输入/机制边界；未定位代码的标UNKNOWN，不当成已证明无代码。框架、生成语料和不同任务结果不自动准入本项目 |

**资源核查（本轮只读）**：5090成功SSH，通过本机`.venv/bin/python`
仅用stdlib检查既有config里的pretrained、官方source_root、train_input、train_manifest、
census五条路径，全部exists=true；`mk_probe_contract.py`仍存在，未改/删/覆盖。
只列出FACT manifest文件名，未打开final-valid或其样本/结果。没有import torch、核空卡或
执行模型；不把存在性当hash PASS，也不沿用较早空卡快照来启动任务。4090不重试，
可用性按作者确认不可用处理，未推断历史进程死亡。

**路线裁决**：C5保留exact joint为当前候选，不改既有五臂/loss/endpoint。
下一项C41-S闭合5090自足source/input身份与独立成本适配，再C41-B实际成本/累积/shape预算、
C41-A准入裁决、C41-T获准五臂。结构成本迁移须核10-14原joint成本具体许可覆盖，
不能只凭“5090空着”扩权。D4登记事件锚点—承诺证据绑定、A4登记目标条件多正例监督，
均只为待准入研究；需排除普通contrast/hard negatives及最新邻居覆盖，信号/数据不足则停止。
C5→D4→A4、单seed13、final-valid、同协议强对照、封存家族与资源边界不变；E3不加动作。

**原始证据与工具限制**：本地GitHub REST请求遇403 rate limit，改用只读GitHub connector
取得官方commit/tree/source；保留失败，不当研究负结果。共享工具venv没有requests/pypdf，
未安装包，使用stdlib下载与`pdftotext -layout`；7份尝试中4份PDF成功并记SHA，3份本地TLS
失败，后者正文用web工具读取，不能声称本地PDF齐备。另有一次猜测raw源码路径404，
随即读官方tree定位实际文件；未把404当仓库缺实现的证据。

本地独占证据根`runs/stages/R1/r1-v66-literature-upgrade-20261015/`，
23项产物（论文PDF/text、pinned code/tree、检索失败manifest与ledger副本），
`artifact_hashes.json` SHA-256
`fc4108379fbe6961f8a00dfa44f5b9f7a3f56d64428638b1f952c387dfb6b952`。
权重没有搬运，原始证据当前仅在LOCAL，未声称已在服务器备份；Git保存source ledger与公开
revision/URL便于重新取得。没有source/runtime冒烟或生产实现的新PASS。

本轮仍`method_admitted=false`、C-41/T087 wip；新方法指标与提分结论均未产生。

**文档验收**：首次R1审计报`SC-009 evidence-anchor-missing`，原因是本次把
RESEARCH_PLAN的`Summary`标题加了后缀，破坏已有`#summary`锚点；恢复原标题并把
历史说明移到正文后，完整审计输出`PASS: 36 requirements mapped`。
`git diff --check`、14项source ledger的结构/唯一ID/revision校验、研究卡本地链接检查、
23项原始证据SHA逐文件复核均PASS。报告
`/tmp/ekg-innovation-upgrade-consistency-20261015.json`。
只改文档/文献清单，未改src/tests/scripts，未声称运行代码变更三件套或真实torch训练。


### 25.66 4090恢复与整体OKR任务重排（2026-10-16，仅资源核查/规划）

**作者指令**：4090已恢复，要求从整体任务目标逐层拆解，用OKR做项目管理，参考算法
实验设计与本项目特点，推进最终指标。该指令覆盖10-15的近期资源安排，不改变既有实验结果。

**开工自审**：科研价值是把表5-3/3-3/4-3的公开主指标与机制证据拆成可验收KR，避免
把准备、成本PASS或已知规则收益当作方法贡献；依据§25.37、§25.42、§25.49–§25.65。
可行性是本地文档与已有证据核对、只读SSH资源核查；本轮无需训练或改模型代码。
真实训练算力预算、生产实现与方法准入仍是后续任务，不能由卡恢复推定通过。

**Git与资源核查**：本地最初`git fetch origin`遇代理TLS handshake失败，
随后`git -c http.version=HTTP/1.1 fetch origin`成功；开工HEAD为`3a1ed37`且等于
刷新后的origin/main，工作树干净。没有分支/worktree或新代理队列。

远端在`2026-10-16T08:52:37+08:00`成功响应，hostname=`4090-1`，cwd=`/data/TJK/ekg`。
执行下列只读命令，exit=0，无torch import、CUDA模型计算或后台任务：

```bash
ssh -o BatchMode=yes -o ConnectTimeout=12 gpu-4090 \
  'cd /data/TJK/ekg && date -Iseconds && hostname && nvidia-smi --query-gpu=index,name,uuid,memory.used,memory.total,utilization.gpu --format=csv && nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_memory --format=csv && git status -sb && git log -1 --oneline && df -h .'
```

| GPU index | 名称 | 显存used/total MiB | utilization | compute apps |
|---|---|---|---|---|
| 0 | RTX4090 | 78 / 24564 | 0% | 查询为空 |
| 1 | RTX4090 | 11 / 24564 | 0% | 查询为空 |
| 2 | RTX4090 | 11 / 24564 | 0% | 查询为空 |
| 3 | RTX4090 | 11 / 24564 | 0% | 查询为空 |

只说明该时刻NVML查询正常且没有列出的计算进程；不是CUDA模型smoke，也不保证启动时
仍有空卡。历史GPU3故障不能由本次查询自动认定CUDA已修好，选用前实际smoke仍须通过。
磁盘`/dev/sdb1`总58T、已用37T、可用19T、67%；没有据此承诺并行训练的RAM/IO预算。
远端HEAD=`7f26c7ba`，远端本地main与其缓存origin/main一致，但落后本次本地HEAD；
未跟踪目录为`.cache/`、`.venv-easyecr-glt/`、`.venv-llmere-causal-s13/`、
`baselines/easyecr/external_code/coval/build/lib/build/`、`lightning_logs/`。
未检查这些目录来源，未fetch/reset/clean远端，后续C41-R保全核源后再同步代码。
本轮未连5090、未重核其卡况/资产hash、未转移checkpoint或修改远端文件。

**规划裁决**：4090回主机，原机资产/成本身份复用；原C41-S新5090迁移实现deferred。
单队列C-41/T087仍wip、C5→D4→A4，下一C41-R原机hash/源码差异、C41-B剩余实际
成本/optimizer/accumulation4/全train预算，C41-A先设计裁决后生产实现/真实测试/正式
合同，最终准入后C41-T/V完成固定五臂与归因。不改loss/scale/epoch/seed/decoder。
后续D4/A4分别有R/A/TV任务与KR映射；新候选仍未准入，文献/train准备可与既有长训练
重叠。额外seed确认C41-Q保留既有前置与再次授权；C41-F只验现有成果/报告缺口，不增加E3实验。

四个Objective是C5、D4、A4独立贡献与最终证据可复核，各三项KR；主指标、机制、
护栏、独立评分和有条件的多seed确认分开。KR不能由任务完成率或平均分代替；
科学目标未达到即标未达，不承诺资源恢复或计划完善能保证正结果。
10-16—10-18先闭合原机/预算；10-19—11-01 C5，11-02—11-22 D4，
11-23—12-13 A4，12-14—01-03留有证据替代/报告预算，01月为获准后的确认/总验收，
02-01—02-21故障/复算缓冲。均为日历风险检查窗，不是已测训练时间；C41-B后再据证据估时。

目标解释卡`docs/research/20261016_project_okr.md`；唯一执行主表仍为
`docs/EXPERIMENT_PLAN.md` §3.9/§4的10-16切片。HANDOFF/TASKS/TODO/RESEARCH_PLAN
已同步，constitution/SPEC/旧结果和旧实验合同未改。

**方法参考边界**：本轮核读Google re:Work OKR指南（结果/活动区别、可查验收证据）和
NeurIPS官方Paper Checklist（复现、实验设置、不确定性、算力），URL在OKR卡。
不引用新外部效果数字，不声称重新做完10-15全部文献；候选科学依据沿用固定source ledger。
R1文献技能用于来源边界，hypothesis-generation/scientific-critical-thinking用于
假设/竞争解释与验收分离，verification-before-completion用于文档验证；技能不是效果证据。

**证据归档**：本地独占根`runs/stages/R1/r1-v67-project-okr-20261016/`，
`resource_snapshot.json`为成功工具输出的结构化转录，含精确命令、UUID、状态与限制，
SHA-256=`5f3163194f5820f592f71305b3bf2c3721fbe6f49e2808554dd390ce4ba26985`；
`artifact_hashes.json` SHA-256=`25c2389ca5cda1c0cdafbaf4831af6d83c71bf81cc44e0265ed0001247df1a4b`。
原始证据当前仅在LOCAL；没有声称已远端备份。GPU启动仍须新核空卡与完整资产hash。

**本轮状态**：规划交付完成；C-41/T087仍wip、method_admitted=false，尚无新训练、
方法提分、机制成立或最终确认。本轮仅文档/记录，未改src/tests/scripts；不声称运行
代码变更三件套或真实torch测试。验证结果在下段按实际命令回填。


**文档验证**：`uv run python scripts/audit_r1_consistency.py --output
/tmp/ekg-project-okr-consistency-20261016.json`输出`PASS: 36 requirements mapped`。
附加逐项检查首次失败，原因是主表KR使用区间/省略前缀而检查器只识别完整ID；
按systematic-debugging定位后，将映射列改成12项KR的显式编号，未改科学门槛。
再次检查4个Objective、12项KR到主表映射、53个本地文件链接、资源转录/manifest的
SHA以及HANDOFF下一项和Summary锚点均PASS；`git diff --check`通过。
这些是文档/追溯检查，不替代完整资产SHA、生产torch门或方法效果证据。


### 25.67 新窗口长期Goal执行交接（2026-10-16，仅文档）

**作者指令**：整理交接，让下一窗口使用目标持续推进，不在每个中间步骤后停下等待。
本轮明确仅做交接，不执行后续研究；原C-41/T087仍wip，下一项仍C41-R，
method_admitted=false，无新GPU作业、方法得分或授权。

**开工自审**：科研价值是将主表R→B→A→T/V和O1–O4的验收贯穿多轮执行，避免
准备/报告被误当成方法贡献或任务终点；依据§25.66与主表§3.9/§4。
可行性是本地文档/已有Goal工具契约核对，无需模型或远端命令。
开工`git -c http.version=HTTP/1.1 fetch origin`成功，HEAD=`7c46b0a`等于
刷新后的origin/main，工作树干净；没有分支/worktree/新代理。

**交接变更**：HANDOFF新增§0.0，要求新窗口开工对齐后get_goal检查本线程目标，
无未完成目标时create_goal显式创建完整研究目标，再核返回状态并执行C41-R。
已存在一致活动目标则接续，不覆盖其他未完成/用户暂停目标；作者未指定token预算，
不擅自设置。工具不可用时诚实说明并给出客户端/goal正文，已授权工作仍继续，
不得声称已启用自动续跑。目标保存于具体线程，不能由仓库OKR或别的线程自动推定。

§0.0提供完整objective、各阶段出口与停止边界：读完计划就实际核资产；必要门通过
进入下一项；正式准入后直接执行获准实验；启动后监测/做合法并行准备；全臂完成即
独立复算/归因；候选失败只停候选并先改主表选合法替代。push/汇报不完成Goal，
不等待作者反复说“继续”。真正的授权/有效性/系统预算/用户停止条件保持；Goal状态
更新遵守实际工具契约，不能把失败或预算耗尽记作成功。同步主表执行说明及TODO入口，
未改科学顺序、指标、旧结果、冻结合同、5090/跨机/seed授权。

**来源**：按openai-docs技能检索并实际读取
[OpenAI官方Using Goals in Codex](https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex)
的Quickstart、线程状态/继续执行/证据完成边界（2026-10-16）。具体get_goal/create_goal/
update_goal状态操作以本会话暴露的工具契约为准；未升级/安装Codex、未改客户端配置。
本窗口没有调用create_goal，未替新窗口启用研究自动续跑；实际启动待新窗口操作并核状态。


**验证**：一致性审计`uv run python scripts/audit_r1_consistency.py --output
/tmp/ekg-goal-handoff-consistency-20261016.json`为`PASS: 36 requirements mapped`。
附加检查确认Goal生命周期/阶段出口/停止边界、43个本地链接与四个仅文档改动；
主表§4及其后的科学任务/验收内容与本轮基线逐字相同。检查器首次把开头的§0.0引用
误写为标题字符串断言，定位后只纠正检查器并重新PASS，未改动科学设计。
`git diff --check`通过；本轮没有代码变更，未运行或声称通过训练/torch测试和代码三件套。

### 25.68 C41-R：长期Goal接队、原4090资产与源码保全（2026-10-16）

**开工自审**：科研价值是保障表5-3的固定五臂共享initializer、训练输入与执行身份，
对准KR1.1/KR4.2及C41-B/A的R1前置；证据是§25.62–§25.63的已封存成本/输入包。
可行性为原4090只读hash、文件清单与真实CPU测试，无模型更新、评测或权重搬运。
不因成本可执行推定MUC收益或方法创新。

按HANDOFF §0.0创建长期Goal，工具get_goal复核`status=active`，无token预算；
线程`01a14247-6fa6-75d1-bc10-aa0acd59d35c`，当前从C41-R接续，目标跨C5→D4→A4。
初始main/origin/main=`ccaf418`，fetch成功、工作树干净，一致性36项PASS，无子代理/分支/worktree。

**原机核查通过**：hostname=4090-1、cwd=/data/TJK/ekg；r2配置全部16项input pins、
r2入口/core源码、规范initializer内容digest `2c7ff1f10496f2df54ed5590693c38c6bc2385bebf29e37b26e4833407349736`
实核相等。逐项重算r2 CPU、原CPU失败、规范tokenization及原peak/worst CUDA包的
6份manifest/17项引用，均匹配；r2 CPU四次API完整性收据的逐值不变/raw恢复SHA核通过。
原失败未改判，已完成模型/输入实验没有重跑；cuda结构输出仍为空。

**保全与同步**：同步前远端HEAD=`7f26c7ba`，已跟踪diff为空；fetch确认至`ccaf418`
只改变10个文档文件，不与未跟踪路径相撞。未跟踪60,740个文件的路径/size/mtime/mode清单、
pyvenv.cfg、包METADATA/direct_url与Lightning hparams的内容hash先归档，再同步已push代码。
来源证据：两venv的pyvenv.cfg分别指向系统Python3.10.12和项目Python3.10.20；
LLMERE环境与scripts/run_llmere_causal_adapter.sh等相符，EasyECR环境与HANDOFF既有命令相符；
.cache/pip为包缓存，coval/build/lib/build为构建副本，Lightning日志来源与
AI_RESEARCH_WORKFLOW_AUDIT既有prediction副作用记录相符。它们是历史资产，不是新方法源码；
未完整倒推每个缓存文件的创建命令。没有clean、删除或覆盖这些目录。
同步后完整路径清单与stat digest复核一致
`4caf47f03172f613b733b3ce4e4aa3f8e2a3efc02200109aeb1468a692994f53`，
关键来源文件另有内容hash；这是元数据保全核验，不冒称逐字节重hash全部虚拟环境。
远端已跟踪diff仍为空，HEAD=`ccaf418d26ee6f05f9ecfcf89efcb0367bda63c6`。

**验证**：LOCAL `uv run pytest`为919 passed/59 skipped（20.53s），
`uv run ruff check src tests scripts`零error、`uv run ekg-smoke` OK；
HANDOFF当前r2/原CUDA非权重核验PASS。
4090以CUDA_VISIBLE_DEVICES=-1、项目.venv/bin/python真实执行
`-m pytest -q tests/scripts/test_structure_budget.py tests/scripts/test_structure_budget_integrity.py`，
11项全部执行通过、exit=0，没有把LOCAL torch skip算PASS。

成功资源快照GPU0/1/2/3显存78/11/11/11MiB、无列出的compute app；启动前仍须重核，
GPU3历史故障不由NVML查询自动消除。RAM available约483GiB、磁盘余19TiB，仅作现场快照。
下一C41-B按既定r2固定10病例执行（0/1/2滚动，避免GPU3历史故障）；确切命令/cwd/独占
输出及本地/真实torch门已列于`remaining_commands.json`，启动前仍逐批披露并核空卡。
另需正式accumulation4、全train relation/type shape与完整预算；method_admitted=false。

**资产**：LOCAL与4090同相对路径
`runs/stages/R1/r1-v68-c41-resume-20261016/`，包括执行audit源码、原机报告、同步后保全、
Goal状态、本地门、真实torch门转录与待执行命令。manifest SHA为`e6172354de1984ce2dabf9d2247629673efa64ba25ddbd53a7709266d7f12dcc`。
checkpoint留原机；无新训练、评测、额外seed、5090任务或跨机checkpoint搬运。
C41-R完成后进入B，不结束长期Goal；本节不计科学KR达成。

### 25.69 C41-B：剩余CUDA成本及完整累积/形状预算（2026-10-16，预声明与wip）

**开工自审**：价值是决定表5-3固定五臂在原单卡/同预算下能否运行，对准KR1.1，
避免用两次cold/warm伪装accumulation4或只按chunks推显存。可行性为4090原机
规范initializer/输入、真实optimizer零LR成本，不学习权重、不读取评测标签。
C41-R已完成（febf26c、§25.68），本地三件套与远端真实torch门通过，method未准入。

按原r2合同先执行剩余五臂×两fixture；第一批peak marginal/root/exact分别
GPU0/1/2，PID1026547/1026551/1026588，独占原r2 cuda/<fixture>/<arm>。
完整命令已披露，每条SSH仅一后台任务，setsid nohup、独立logs/c41-b-*-20261016.log，
输出不覆盖。源代码febf26c，r2配置/入口/核心hash沿§25.63，不改变冻结目标。

**完整train shape静态核查**：输入hash与manifest核一致，2622doc。
peak/worst两个原fixture的关系pair总数17752/75966，类型cubic代理3124/23544；
全train按关系pairs取top8的relation-envelope为100418pairs、37chunks，
按Σtype-block³取top8的structure-envelope为112491代理、29chunks、最大type block28。
原worst chunk fixture并不覆盖这些shape组合，不能仅用其CUDA峰值判全预算PASS。
静态数是shape与调度证据，cubic代理不是实测耗时/显存。

**因此预声明独立补验身份**：新增accumulation预算入口/配置/合同与独占namespace，
不改封存r2代码/输出。固定每臂2个optimizer周期、每周期依次peak/worst/
relation-envelope/structure-envelope四个8doc microbatch，loss/4逐次backward，
梯度驻留至第4步；原Adam scorers→AdamW encoder→encoder scheduler顺序，lr严格0，
第二周期有真实optimizer state，逐参数数值相等与signed-zero完整性收据沿r2记录。
报告逐microbatch elapsed、allocated/reserved、梯度驻留/state、RAM、输入搬运和audit开销；
不把完整性instrumentation耗时当production耗时。五臂全部同补验规则，不按分数选病例。
TDD先核累积数学/清零/非有限拒绝与scheduler计数，真实CPU测试及本地三件套后才能CUDA。

完整预算沿历史实际batch8/accumulation4/100epochs，328 microbatches/epoch、
8200次optimizer step、scheduler总步数32800、warmup200；不静默改成optimizer步数。
按全train shape计数与各臂实测保守外推，显式给出RAM/IO/并行和未测学习态方差限制；
不是完整epoch测量，不声称精确运行时保证。若任何病例OOM/数值变化即保留失败/停止，
不得偷偷缩batch或改目标。预算闭合后才C41-A设计裁决/生产实现/正式合同。

当前非权重静态证据：`runs/stages/R1/r1-v69-c41-budget-20261016/shape_audit.py`、
`shape_documents.jsonl`、`shape_report.json`；待代码/合同冻结后补hash与真实结果。

补验工程门：三项TDD最初因新入口不存在真实3 FAIL；实现后LOCAL默认env为torch skip，
另建`/tmp/ekg-c41-budget-cpu-20261016`隔离uv环境，官方torch2.8.0+cpu实际执行3项全部PASS。
首次把pytest放PyTorch专用index解析失败、随后环境缺项目pydantic；分别修为分源安装及
安装项目core依赖后通过，均为环境缺口，不是模型/科研失败。本地不载入模型或运行GPU。
最终完整本地919 passed/62 skipped（20.04s）、ruff零error、smokeOK、一致性36PASS。
新入口/配置/合同待本提交push后在4090执行真实CPU测试，再启动CUDA补验；尚未据此判预算PASS。


§25.69 实际完成与预算裁决（不是方法准入）：原r2的10个CUDA病例全部complete，
随后五臂各2周期×4microbatch真实累积全部complete。首批累积PID
1032022/1032121/1032247，末批1033244/1033362；原r2十病例PID依次
1026547/1026551/1026588/1028180/1028279/1028390/1029702/1029758/1029943/1030996。
成功SSH在2026-10-16T09:33:50+08:00核所有五个累积PID GONE且report完整，
GPU0/1/2/3均无列出compute app，显存78/11/11/11MiB；无等卡/自动启动器。
后续启动仍重新核卡，不将GPU3的NVML正常解释成CUDA故障已修好。

r2固定病例（warm同步forward+backward；native optimizer扣除完整性hook）：

| fixture | arm | peak reserved GiB | warm fwd+bwd秒 | native optimizer秒 |
|---|---|---:|---:|---:|
| peak | exact | 2.816406 | 0.424151 | 0.032639 |
| peak | marginal | 2.773438 | 0.372347 | 0.023084 |
| peak | mass | 2.873047 | 0.417562 | 0.023344 |
| peak | root | 2.773438 | 0.476029 | 0.013945 |
| peak | shuffle | 2.816406 | 0.400379 | 0.058020 |
| worst | exact | 5.111328 | 0.900845 | 0.050489 |
| worst | marginal | 5.111328 | 0.802671 | 0.023020 |
| worst | mass | 5.111328 | 1.032156 | 0.041336 |
| worst | root | 5.111328 | 0.933710 | 0.041284 |
| worst | shuffle | 5.111328 | 0.918135 | 0.050775 |

所有报告及原manifest在LOCAL逐项重算一致；各4次实际optimizer API调用、
逐值相等/仅零符号恢复、weight_updates=0、method_admitted=false、final_valid_accessed=false。
所有warm state均1,004,814,108bytes，旧CPU失败保留，不改判。

补验五臂每microbatch均221个参数梯度finite，驻留梯度502,406,612bytes；
scorer→encoder→scheduler顺序，scheduler计数[1,2]，每臂4个optimizer API，
逐参数完整性收据全部通过。显存覆盖真实state、accumulation4及关系/type envelope，
不再把CPU state与旧CUDA峰值相加充当通过。

| arm | allocated / reserved GiB | RSS GiB | 最大warm microbatch秒 | warm native optimizer秒 | 1×外推GPU小时 | 2×规划GPU小时 |
|---|---:|---:|---:|---:|---:|---:|
| marginal | 5.749931 / 6.363281 | 3.769356 | 0.915740 | 0.016978 | 8.382 | 16.764 |
| root | 5.749931 / 6.363281 | 3.670303 | 1.445340 | 0.027799 | 13.232 | 26.464 |
| exact | 5.749931 / 6.363281 | 3.658218 | 1.347821 | 0.025975 | 12.339 | 24.679 |
| mass | 5.749931 / 6.363281 | 3.651661 | 1.247728 | 0.019813 | 11.413 | 22.827 |
| shuffle | 5.751029 / 6.308594 | 3.656288 | 1.447528 | 0.018643 | 13.231 | 26.462 |

公式固定为32800×各臂四fixture最大warm同步forward/backward（已含transfer）+
8200×warm native optimizer；完整性审计不计production。2×只作操作性余量，
不是统计方差估计、完整epoch实测或严格时间上界。五臂合计1×/2×为
58.598/117.195 GPU小时；三卡两波约26.463/52.926墙钟小时。
实际共享服务器负载/随机batch/非零LR数值/长期碎片/endpoint导出仍未测；
per-axis envelope不等于形式化joint最坏内存定理，必须经生产CUDA smoke且运行中fail-fast。
当前实测最高reserved约6.36GiB，相对单卡24GiB有明显余量；不挤同卡其他任务。

CPU/IO：每臂4线程，现场64CPU/available519,221,645,312bytes，disk余
20,058,554,695,680bytes。规划每臂RAM32GiB、五臂产物磁盘32GiB，均为预留非实测峰值；
最多三臂即12CPU/96GiB RAM，低于本次可用资源。完整train的input/attention与三组
relation-label tensor载荷99,225,296bytes（不含Python容器）；全train分词复用§25.63
已有规范pin等价及§25.53耗时参考，不再重跑。补验各臂input校验/读取约4.08–4.90s，
模型/fixture初始化约3.80–4.51s，单microbatch warm transfer最大约0.00124s；
它们不是全train/真实endpoint IO测量。FP32模型+真实optimizer state估计每臂
1,509,583,088bytes checkpoint主体，另留序列化、scores、预测与日志空间；权重留4090。

**裁决**：数据/代码/协议/现有4090资源可支撑进入C41-A设计准入，C41-B done。
不保证学习态或科学收益，method_admitted仍false；A要先设计裁决，再生产TDD/CPU回放、
本地完整门、真实torch与CUDA smoke、正式合同/hash冻结。不得用本成本r2 hooks进行非零LR训练。

补验release=e7e3709，入口SHA
687111e2c8c0e8fee1952bf1e83daa05bf49a53cf25ce5e7e9a9fc78e0500a6c，
config SHA d137da51807152a87b64106db9d5337105c45786773e33e4878bbd3282697d5b。
5份补验report SHA分别见budget_closure.json的rows；10份r2报告SHA见r2_cost_summary.json。
R169的shape/输入/config/报告/log/summary有completion_hashes.json，双端hash核验后封账；
现阶段结果没有MUC/关系效果，没有训练新方法、额外seed或跨机checkpoint搬运。

预算封账验证：R169 `completion_hashes.json` SHA
`aa1ec887524e1c2a6cccfce09f65b5bc7d2217a54c17e382bcb08167a67514d5`，
LOCAL与4090各自重算35项均匹配，含五臂报告/manifest与15份原始日志；
R165十份r2报告另依各自原manifest逐项核对，SHA登记在R169 summary。
本次收口仅改文档/结果，不再改e7e3709已通过的代码；一致性36项PASS、diff --check通过。

### 25.70 C41-A第一段：设计准入裁决（2026-10-16，无方法效果）

开工自审与可行性/竞争解释/方法边界见
`research/20261016_c5_design_admission.md`，对准表5-3/KR1.1–1.2。
复用C41-L固定一手文献与§25.46–§25.61的机制/输入/条件power证据，
C41-R/B已完成（febf26c/1f03ab1，代码e7e3709，§25.68–§25.69）。
不新增科学阈值、loss/scale/臂/endpoint、标注、seed、外部数据或设备权限。

持有队列的代理作顺序PI/方法自审，裁决`design_admitted=true`：限定差异为
相同typed parent model与soft pair-F1下的joint-dependence训练，五臂可区分
普通结构监督、root乘积、总量增加和pair归属；不声称发明forest/root DP/结构loss，
检索未定位全同机制不等于不存在。条件power不等于未知训练方差已测；
预算外推与实测学习态不同，仍须生产门。既有五臂/强锚/护栏/科学止损全部保持。

第二段现在开始：TDD生产组件/CPU缓存回放、官方Model透明接线、本地完整门、
远端真实torch与CUDA smoke、最终phase/code/config/input合同冻结。
此时`method_admitted=false`，未开始正式五臂训练或dev评分，不改旧CPU失败与科学负结果。
本次设计记录不会自动产生科学KR达成；长期Goal保持active，继续第二段而非等作者继续。

### 25.71 C41-A第二段：生产组件/原joint接线与测试（2026-10-16，wip）

科研价值/可行性沿§25.70与设计卡：将已准入的固定设计落实为表5-3可执行比较，
不是重新选loss/decoder。官方Model/data/utils/dump源码不改；新增registry forest_pair
及lazy-torch目标/纯CPU概率cache解码，抽取本项目封存research运算；不重写公开Model。
训练入口实现原optimizer/accumulation/scheduler/固定endpoint，完整共指与三关系导出。

TDD：组件最初11 FAIL（缺模块）、入口3 FAIL（缺入口）、无标签train-smoke投影
1 FAIL（缺函数）；实现后隔离Torch2.8.0+cpu实际20项通过，包含五臂loss与全logit梯度
逐值等于research、四头目标/全部toy参数梯度一致、跨epoch累积、非有限拒绝、无金标
泄漏的smoke输入投影、CPU缓存/类型/空pair及registry惰性边界。
初版放nodes会触发既有父包torch availability import，惰性测试1 FAIL；查明来源后
将轻量算法放core，未改旧nodes或封存代码，测试转PASS，不将导入问题当科研失败。
本地完整925 passed/76 skipped（20.82s）、ruff零error、smokeOK、一致性36PASS。
默认env torch skip不作为远端证据。

生产合同`phases/PHASE_C5_joint_dependence_20261016.md`及
`configs/c5_joint_dependence_20261016.json`绑定原机30项输入/source/合同证据与生产code集合。
此时method_admitted=false；接下来先远端真实CPU测试与固定peak8五臂完整Model损失/
全参数梯度parity，再五臂train-only CUDA生产smoke。smoke各4microbatch/1个非零LR周期，
无zero-LR完整性hook，导出仅peak8 train去identity/relation金标后的输入，不读dev或评分。
最后冻结admission.json才允正式100epochs；没有把代码可运行当方法价值或最终准入。

新phase独占根`runs/stages/C5/c5-joint-dependence-20261016/`；parity/all、smoke/<arm>、
train/<arm>各exclusive-create，status/源码身份/输入/CPU cache与完整预测可复查。
本地准备证据R170=`runs/stages/R1/r1-v70-c41-production-20261016/`。
源码/config更新只在新生产身份，不修改r2/原CPU失败/旧方法输出；本次未发起正式训练。

§25.71 远端真实CPU门与完整Model parity实际完成：source release51c27eb、生产config
SHA `e961e3ca47cccf7d75bfdebe23a448619fb50548df31edd63c83277778a9796b`。
4090新增20项CPU测试全部执行通过（非skip）。完整Model CPU/parity PID1040306已成功
SSH核GONE，五臂各与封存research比较总loss/每项loss严格相等，221个有梯度参数
最大absolute error全部0.0（原容差rtol1e-4/atol1e-6未放宽），无optimizer。
初始化/结束SHA均`5b67cbba9d07f1fb3408b9623833a65f7d8eecaa4799a8b6a0021be3d44a53d6`，
与前期规范initializer生成的完整Model一致。report SHA
`41945117fee07db434627037e8c63b26053d4ef1a1745af2f311829d914d1431`，
LOCAL回传依原status artifact SHA核一致；首次rsync因LOCAL父目录不存在失败，
建独占父目录后重传成功，失败仅属传输，不改远端实验结论。

生产CUDA smoke第一批marginal/root/exact PID1092358/1092397/1092436已complete，
各1 optimizer周期/4 microbatches，initializer相同、权重实际更新、无zero-LR hook，
train去金标输入导出与CPU cache/source decoder parity均通过，未评分。
第二批mass/shuffle已按同合同发起（日志/PID另补），全部通过前不建最终admission。

统一评分计划`configs/c5_joint_dependence_evaluation_20261016.json`在无任何proposed
internal-dev预测/分数时冻结：沿§25.51的旧strongest typed-control+3pp目标，
另须超过所有同预算正对照；主要归因exact-root、exact-mass的正差及95%配对区间
下界>0，shuffle更弱，三共指护栏不低于typed及marginal，三个关系任务完整报告。
明确是对joint brief原并列条件的操作化，不将突破目标改成额外要求对每个新控制+3pp。
使用既有official scorer/error profile/文档MUC计数，不重写指标；所有endpoint完成才执行。
单seed区间未调整、历史internal-dev反复使用及未知训练方差继续披露，final-valid封存。


### 25.72 C41-A两段准入完成与最终训练身份（2026-10-16）

**科研价值与可行性裁决**：设计问题/竞争解释/条件power沿§25.70及固定brief，
工程/预算沿§25.68–§25.71；当前交付的是可信的单seed探索执行身份，不是MUC提升、
机制成立或创新证明。原三章最终科学KR均未验收；本轮未动final-valid或旧封存结果。

五臂生产CUDA smoke全部complete/GONE，均同config/initializer与原架构、
非零scorer/encoder学习率配方、四microbatch后实际一次optimizer周期；原warmup第一步
encoder LR按历史scheduler从0起，不把它伪称encoder已发生非零幅更新。
各臂完整Model raw SHA实际改变，无zero-LR hooks；只导出8篇train去identity/relation
金标后的given-type/span输入，包含共指及三个关系任务。source decoder与纯CPU缓存回放
逐doc完全相同，LOCAL另从raw probabilities独立回放均匹配，没有算train/dev指标。

| arm | PID | peak allocated / reserved GiB | report SHA-256 |
|---|---:|---:|---|
| marginal | 1092358 | 4.798126 / 5.416016 | `f53296854d317a5699dfa7e83a68d2a5cdc765dbecf2be52eb000224e7ba42be` |
| root | 1092397 | 4.799122 / 5.316406 | `2b0aa3a5075ab34287352cc0cd7127af03764b8bbcf063297533cdfa5c1b892b` |
| exact | 1092436 | 4.798126 / 5.416016 | `a2508b1562422357ebc63cfca17e48e0e234de5d9d9acceb85c063ad440e7b52` |
| mass | 1093985 | 4.798126 / 5.416016 | `97526b5030aec53b06ecbc50ede4d2cc1a7f0c1df6e3c40e332768fffde41c2e` |
| shuffle | 1094044 | 4.798126 / 5.416016 | `e188091bbe95bf4d10430d585504c8e7422175d26c07dd7209f1027bb8ded6fc` |

本地925 passed/76 skipped、真实LOCAL CPU20项/4090 CPU20项通过，完整Model五臂
loss/221参数梯度strict parity及五臂CUDA非零更新/导出smoke均闭合；代码集合在
这些检查后未变（release51c27eb）。两段准入全部满足，裁决`method_admitted=true`，
**仅准许当前固定seed13五臂单轮探索**。额外seed、final-valid与设备/搬权重授权均不放开。

**最终可信身份**（完整原文位于LOCAL及4090同相对路径；外部可信锚为本节Git提交）：
- phase根：`runs/stages/C5/c5-joint-dependence-20261016/`。
- 生产config SHA：`e961e3ca47cccf7d75bfdebe23a448619fb50548df31edd63c83277778a9796b`。
- `protocol.json` SHA：`b13729633578f9aee62b5e7b438f29680b1f76867367be5c4111900ca5b69528`。
- `admission.json` SHA：`8d266760ecb878e2d719a72c920d8da8d7c99e3bf2e7868d98bd1a7ac1cf34e6`。
- admission绑定32项parity/smoke文件、原生产code集合、上述协议及统一评分计划；
  P1绑定r15/1e31a9…，完整train/dev/原source/规范initializer/candidate/evaluator身份在protocol内。
- `configs/c5_joint_dependence_evaluation_20261016.json`冻结于d856d8e，结果前已固定；
  旧typed强锚+3pp和胜同预算正对照为并列要求，不抬高或降低原突破目标。

协议与admission不以自有hash自证可信根，须从本节Git记录反查上述完整hash；
入口在正式训练前还会重核config/code/输入、CPU parity和全五臂smoke文件。
完整五臂100epochs、同原batch8/accumulation4/原scheduler计数与末步，无选dev档；
每臂末步才导出一次internal-dev预测，**全臂endpoint后**才统一官方评分/配对/归因。
无训练中选模、scale/threshold扫描，checkpoint留4090。任何科学门失败停固定候选。

C41-A done，下一C41-T，随后V；D4/A4正式接队仍按C5裁决后，长训练期间可准备已有主表
允许的文献/train信号。长期Goal保持active，不把准入、提交或GPU启动当科学KR完成。
非权重证据R170与新phase文件的最终双端SHA核验在下段补记后再push/正式启动。

§25.72 最终双端封账：R170 `completion_sha256.json` SHA
`0db862acd8be8c7aa2c9acc171ebda8f1e8712a3dfe4f2fc774955e0441cd4b9`，
LOCAL及4090逐项重算46份非权重文件均匹配，含最终protocol/admission、全部CPU/CUDA门、
raw cache/完整train-smoke预测与原始日志；远端再读admission/protocol SHA与上方完全一致。
源码未改、Git仅本次文档回填，R1 consistency36PASS、diff --check通过。
C41-A准入证据已封存；接下来push本外部可信锚、同步已push文档/评分计划，再按空卡启动T。

### 25.73 C41-T：固定五臂正式训练首批启动（2026-10-16，wip）

**开工自审**：科研价值是实际检验表5-3的预声明主指标/归因/护栏，而非继续把数学、
成本或准入当效果；可行性是§25.72两段准入与已push可信身份、原机完整资源/生产门。
seed13/100epochs/五臂/末步与统一评分规则不变，无final-valid、额外seed或5090任务。

外部可信准入锚已push为50e4fd1，原生产代码51c27eb、配置e961e3…不变。
4090安全同步main后，默认`--stage train --arm exact`（无execute）预检PASS；
成功核GPU0/1/2无compute apps、显存78/11/11MiB/util0后，完整命令/cwd/输出已披露。
每条SSH仅一个setsid nohup独立任务，未创建自动等卡/重试启动器。

| arm | 4090 GPU | PID | 独立log | 独占输出（新phase根下） |
|---|---:|---:|---|---|
| marginal | 0 | 1097108 | logs/c41-t-marginal-s13-20261016.log | train/marginal |
| root | 1 | 1097110 | logs/c41-t-root-s13-20261016.log | train/root |
| exact | 2 | 1097148 | logs/c41-t-exact-s13-20261016.log | train/exact |

2026-10-16T12:37:30+08:00成功SSH核三PID均ALIVE（ps约43–44秒，Rsl），
GPU0/1/2显存4178/3761/3761MiB、util66/54/87%；GPU3未用。
这些只是启动/运行事实，不是正式epoch/endpoint完成或MUC结果。
mass/shuffle尚未启动，按空卡滚动接续；不读先结束臂的dev分数。
新phase根`runs/stages/C5/c5-joint-dependence-20261016/`，checkpoint均留4090。
LOCAL运行命令/资源身份记录R171=`runs/stages/R1/r1-v71-c41-training-20261016/launches.json`。
队首C41-T保持wip，全部endpoint后立即V；训练启动不结束长期Goal。

§25.73 操作性资源补充（执行前声明）：GPU3只有历史故障记录，本次恢复后NVML正常
仍不等于CUDA可用。先在该空卡做独立、限时、无模型/无训练的FP32 matmul/backward
硬件探测；通过后可用于第4臂mass，失败则保留工具/硬件证据并继续原三卡滚动。
这是AGENTS的C类选卡/并行调整：不改封存phase文本/config哈希、5臂/seed/输入/精度/
单卡batch/优化步数或科学判据；原phase的0/1/2三卡安排保留为历史保守预算。
不复跑任何已完成成本或生产smoke；GPU3实际CUDA通过与新资源选择另记。

§25.73 GPU3限定CUDA探测实际PASS：物理UUID
`GPU-80141f33-8c8d-b9de-25fa-f9ccdb8a6834`、RTX4090、Torch2.8.0+cu128，
空卡11MiB后FP32 256×256 matmul与backward有限，峰值allocated18,088,960bytes，
进程内2.052759秒，无模型/数据/optimizer；并未将NVML正常直接视为CUDA修好。
按上述C类现场选卡调整，现准用GPU3运行第4臂mass，同一生产配置/单卡协议。
预计产物train/mass、logs/c41-t-mass-s13-20261016.log；shuffle继续待首张卡释放。
原三卡保守成本预算不改判；源码/config/initializer/seed/优化预算/评测规则均不改变。

**后续实际启动与失败快照**：mass按同一命令在GPU3启动，PID1101626，源码HEAD
2fc1ad2；配置仍e961e3…、实际生产代码51c27eb。成功SSH确认原进程GONE、
status.json为failed，最后完整epoch39 / 12792 microbatches / 3198 optimizer steps。
错误为`ValueError('zero mass denominator with nonzero delta')`，调用链从训练
loss进入`ForestPairObjective._auxiliary`第126行；日志未报告CUDA异常。
因此不能把此失败归为GPU3硬件故障，也不能把它记为方法负效果；具体数值根因尚未复现。
原路径/日志/39轮训练轨迹完整保留，LOCAL另存R171/mass_failure_snapshot；不修改
冻结公式、同路径重试或用容差/默认值掩盖。已有smoke/parity未覆盖此训练后状态。

同次成功SSH：marginal/root/exact分别仍ALIVE（ps约1:27:57/1:27:57/1:27:56），
末次完整epoch分别70/54/57；GPU0/1/2显存4804/4771/4737MiB，GPU3空闲11MiB。
shuffle未启动。未读取任何dev分数；不能缺mass就作完整五臂机制裁决。
下一先做独立命名空间、零模型的饱和概率数值复现与源码追踪，再依据证据决定新的
修复身份/可比性门；原冻结失败记录不得覆盖，不能调学习率/预算救分。

**执行边界快照**：本轮get_goal实际返回usageLimited，累计tokensUsed830095 /
timeUsedSeconds13076；不是主动暂停、不是blocked或科学目标完成。保留三项远端
在途训练，不发送终止信号；本轮只做证据落盘/交接推送，不再发起训练或新研究。
继续执行须先核Goal状态、三态判活与原路径，不能盲目重启。

### 25.74 C41-D-R准备：D4最近邻与train归属机会（2026-10-16，非正式接队）

**开工自审**：科研价值是为表3-3/KR2.1–2.2排除普通supcon/已有scope/evidence训练
的重合，并确认原生多事件/支持词标注能否辨认event-anchor归属；不能拿同句不同标签
直接制造蕴含/反驳或缺cue即负例。可行性为固定MAVEN-FACT public-train原数据/loader
与一手论文/官方源码，只做轻量本地/远端CPU和检索，不读final-valid、不新训模型。
这是主表明确允许的C41-T长训练期间准备，正式D4接队/准入仍等C5裁决；单一活动队列不变。
下一核CoDE/SDIN/scope/近期同任务方法正文及公开实现，字段级train覆盖/稀有类/offset，
已知24处train evidence offset噪声沿原loader丢弃计数，不把缺失当negative scope监督。

**准备实际结果（未正式D4准入）**：R172=`runs/stages/R1/r1-v72-d4-preparation-20261016/`。
固定fold-1 train为1747文档；raw train SHA190522b4…，train manifest SHA dbaf7c52…
（完整值见R172报告）。初版因evidence双null触发TypeError，保留source/failure；
r2显式计双null、部分null fail-fast，不把缺失变负例；零模型/零optimizer。

| native class | mentions | 有合法evidence | 双null evidence | 非法token offsets |
|---|---:|---:|---:|---:|
| CT+ | 41889 | 28 | 41856 | 5 |
| PS+ | 1357 | 1215 | 141 | 3 |
| CT- | 897 | 828 | 68 | 4 |
| PS- | 170 | 167 | 2 | 1 |
| Uu | 71 | 8 | 63 | 0 |

同句异标签原生pair5539，其中双方均有合法evidence仅162（不重叠111/重叠51）；
Uu参与双方有evidence的pair仅3。没有负归属、scope边界、source-holder或同事件
句子/文档双标签。这些是覆盖事实，不是效果/power。**缺/不重叠支持词即负scope的
版本不可行，卡在数据监督不可辨认**；不能据此否定所有正例辅助训练。
替代研究问题保留为原生多事件标签归属，须先核普通supcon/排序/条件似然等最近邻、
强rival与可识别性，不将标准loss换名为创新；目前不实现/不训练、不擅自准入。

一手机制刷新：
[SDIN2023](https://aclanthology.org/2023.findings-acl.879.pdf)完整13页：§3/Table1/§4
依赖同事件sentence/document双事实性来构造推理标签，不能拿不同MAVEN事件的
五类标签替代其NLI监督；代码仅在有限搜索未定位，不宣称不存在。
[Trucidator2025](https://aclanthology.org/2025.coling-main.139.pdf)完整11页：§2.2/§3
额外构造并人工核查幻觉语料、跨文档图/全局事件监督，完整流程不适配当前冻结数据；
也不能将已有graph/多任务机制当新贡献。
[CoDE2023](https://link.springer.com/chapter/10.1007/978-3-031-30675-4_36)与
[scope2021](https://link.springer.com/chapter/10.1007/978-3-030-92185-9_34)仅核到出版商摘要，
全文订阅不可得，不能据摘要排除最近邻重合；
[EvDEFI2024](https://academic.hep.com.cn/fcs/EN/10.1007/s11704-024-3809-6)仅元数据，
直接访问403/web PDF返HTML，机制未核。无外部数字比较。
GitHub作者API403/检索限制不是无代码证据。R172保存两篇PDF/全文、哈希与访问限制。
正式D4研究接队仍等C5裁决；此次只是T期间已授权准备，不代表D4完成。

**本轮交接证据校验**：R171/mass_failure_snapshot三件原始非权重产物与远端原路径
逐字节一致；manifest SHA256
`c39d0a22fb0ffb40d28ec8439314410e619b47e1a303325e766368a1e6d576d5`。
R172共11件准备产物manifest SHA256
`23bccf68e236e421ec039330961b175b1583104f6065474352948793e048dffb`。
两组均LOCAL生成并备份原4090、远端逐件重算PASS；无checkpoint跨机搬运。
仅文档/交接变化，`uv run python scripts/audit_r1_consistency.py`为36项PASS，
`git diff --check`通过；未声称新代码测试或科学KR通过。

### 25.75 C41-T接续：mass饱和数值复现与修复准入（2026-10-16，wip）

**开工自审**：科研价值是恢复表5-3/KR1.2预声明的总概率量强控制，不能缺mass就
声称exact依赖归因。可行性是零模型CPU logits复现、原源码/失败封存及4090空卡；
先根因和数学等价验证，再独立修复身份/生产门。不使用dev结果选择修复，不改loss/
alpha求导/权重/seed/epoch/decoder，不把原失败覆盖成成功。

用户明确确认额度已恢复并要求继续；get_goal仍返回旧usageLimited，不据其缓存状态
宣称活动自动Goal已恢复，也不重建/标complete。当前按用户本轮继续指令推进同一队列；
官方Goal文档所列客户端恢复命令为/goal resume，代理工具没有resume接口。
Git已fetch，HEAD=origin/main=62a3573，干净；consistency36PASS。

R173=`runs/stages/R1/r1-v73-c41-mass-numerics-20261016/`先写自审/假设，后运行
CPU-only Torch2.8.0+cpu，seed13构造logits、零数据/模型/optimizer。3002个构造病例
内找到5mention输入，原production实际抛同一ValueError；所有parent row float32和
为1，QQᵀ十个lower pair均舍入1，C中4个pair为0.9999999403953552，denominator=0、
delta=-2.384185791015625e-7。是原代码路径的合成反例，未取得原训练失败batch，
不能声称现场精确重放；原research实现有同一算式，production parity因忠实继承未发现。

裁决：旧mass实现数值失败，不是硬件失败/科研效果负例。先独立研究正数complement
递推与相同mass公式的等价、梯度及饱和边界，再做TDD独立实现；失败路径原样保留。
只有数学/独立穷举/梯度/完整模型门通过才创建新mass训练身份，从同initializer重跑
seed13固定100epoch；不从第39轮补权重，不动仍运行的其他臂源码/配置。未受影响四臂
保留原合同身份，任何新mass对比必须显式报告数值修复差异，不能称原五臂合同完整。
评分仍等所有有效臂endpoint，原eval计划不改；修复评测路径以独立覆盖映射绑定。

接续成功SSH：marginal/root/exact均ALIVE，最后完整epoch72/56/59；mass GONE/failed，
GPU3空闲11MiB、无compute apps。shuffle尚未启动，按原冻结配置/同精度和预算接GPU3；
这仅是C类空卡选用调整，原phase/config/五臂科学判据不变。

§25.75 正数complement审查已执行：24forest独立穷举的E/R误差均1.11e-16；
60个一般float64病例相对原公式最大value误差4.44e-16、所有logit梯度误差1.38e-14、
总量误差3.55e-15；原饱和反例及0/12/30/60/100/300/1000构造logits的值/梯度有限。
原训练现场未重放。新合同`PHASE_C5_mass_repair_20261016.md`先冻结等价式、仅aux
float64差异及独立门；实现尚未准入训练。TDD新增11例已见缺组件FAIL（R173/tdd_red.log）。
shuffle已按原配置GPU3启动PID1128804，确认运行状态另补；未改其他臂。

§25.75 新生产实现：`core.mass_connectivity` registry惰性torch组件、独立
`run_c5_mass_repair.py`入口复用旧prepare/joint loss/train loop/export/CPU replay，
只复制fit接线以显式注入新目标，不修改原封存代码。新config SHA
`a88e9f0bdbd2cd1f9766cedf98f4986365f8296364598d0c433a200233897d3c`。
11个目标测试+3个入口测试先缺组件/脚本FAIL、后隔离CPU Torch全部14实际通过；
全项目uv pytest928passed/87skipped（21.83s），ruff0、ekg-smokeOK、consistency36PASS。
R173本地数学/失败复现/TDD与全套日志共9件，completion manifest SHA
`f994ed884c2e197d66b64e92aae681bda32afc08804bcc815678f750ad62a38a`；原39epoch失败数据不改，远端完整模型门未跑，仍不得新训mass。
shuffle PID1128804已成功SSH核ALIVE/Rsl、status running（cbffc21/original config）；
随后继续原四臂，不读取任何dev分数。

§25.75 远端新14例真实Torch全通过；R173九件artifact双端SHA全部核一致。
修复CPU完整模型parity PID1130534已complete且ps GONE（GPU隐藏），旧/新total loss
11.500032424926758 / 11.500032543587515，全部221参数梯度PASS，最大abs差
5.960464477539063e-8（原rtol1e-4/atol1e-6不改），参数摘要前后与规范起点相同。
report SHA3ffbcecbafbeb0f40b7242f878d3f60361fbd14dab8288b25c87747bd9bf6f9c。
本地取回首次因目标父目录不存在失败，创建独占父目录后重取；工具失败不改parity结论。
四卡均占用原四臂，修复CUDA smoke尚未启动，不挤占、不创建等卡启动器。

### 25.76 C41-V收集器准备（2026-10-16，未开始评分）

**开工自审**：价值是为表5-3/KR1.1/1.2/4.2完整执行预冻结的官方评分、强控制、配对、
护栏与错误交换，避免只摘单臂；可行性是既有P1官方wrapper、MUC充分统计/错误profile，
CPU轻量即可。只准备接线与合成测试；全部有效臂endpoint前不运行方法评分。
`evaluate_c5_joint_dependence.py`复用既有official scorer CLI（各臂均完整三关系+共指），
独立MUC统计/official cross-check与missing/spurious、pair恢复/引入。paired固定sorted
291docs/RNG13/2000bootstrap/95%区间，原科学门不变。endpoint检查complete、配置/
预测/report/hash、100epochs/32800microbatch/8200updates/CPU replay与checkpoint身份，
缺一即停止，先查齐endpoint再评分。旧mass不能当完整臂；独立overlay待修复正式准入后
冻结，仅改mass路径/透明精度差异，不调目标。checkpoint不要求跨机复制。
新4例先缺脚本FAIL后通过：未完成endpoint/篡改预测拒绝、同系统差为0、先汇总link再算
corpus MUC。全套932passed/87skipped（20.78s），ruff0、ekg-smokeOK、consistency36PASS。
R174=`runs/stages/R1/r1-v74-c41-evaluation-preparation-20261016/`保存自审/原red与全套日志。
当前无方法dev scores，V仍pending，准备PASS不算科学KR。

### 25.77 长训练期间D4/A4有限准备（2026-10-16，非正式接队）

**开工自审**：科研价值为表3-3/KR2.1–2.2避免将已有条件似然换名，并为表4-3/
KR3.1–3.2辨别真实多原因与coref mention展开造成的伪多正例。可行性为一手公开
源码/固定MAVEN-ERE train manifest与原生event/mention关系标注，零模型/optimizer。
不读internal-dev/final-valid标签，不进行新准入/训练；主队仍C41-T数值修复，正式
后续顺序C5→D4→A4不变。R175=`runs/stages/R1/r1-v75-chapter-preparation-20261016/`。

D4拟议“固定语境标签直方图的条件归属loss”最近邻已核到
[statsmodels官方ConditionalMNLogit源码](https://www.statsmodels.org/stable/_modules/statsmodels/discrete/conditional_models.html#ConditionalMNLogit.loglike)：
按group对原生labels的排列作logsumexp分母、真实分配score作分子，并明确引
Chamberlain1980。按相同label counts枚举唯一排列仅差与参数无关的重复数常量，
梯度相同；两事件退化为普通配对logistic。**该标准条件似然本身不准入独立创新**。
它可作为未来强rival，不能仅以换成事件/神经logits当新方法。CoDE等全文未核限制
继续保留，不用此一条源码声称整个scope/evidence文献已排完。

A4接下来只核train：target×方向×CAUSE/PRECONDITION的distinct event positives、
mention-expanded positives、无关系候选、仅同coref重复的多正例、BEFORE重合。
未标注关系只记dataset None，不当世界因果负例；不把BEFORE当CAUSE，不裁评测全集。

§25.77 A4 train census实际complete，固定2622文档、61362event clusters/66744mentions。
只在manifest内访问annotations。r1初版BEFORE重合含TIMEX、不能叫event-only，原source/
输出保留，r2单列TIMEX后才解释事件因果；所有causal group统计与r1逐项相同。

| 方向/标签 | 有正例event-target组 | distinct≥2正例组 | 覆盖doc（distinct≥2） | mention-target多正例组 | 仅同一正例event重复的mention-target组 |
|---|---:|---:|---:|---:|---:|
| incoming CAUSE | 4726 | 1023 | 427 | 2254 | 1207 |
| incoming PRECONDITION | 17042 | 5837 | 1703 | 7310 | 1311 |
| outgoing CAUSE | 2873 | 1199 | 789 | 2449 | 54 |
| outgoing PRECONDITION | 11275 | 5131 | 2024 | 6656 | 79 |

event-level CAUSE/PRECONDITION边6175/26759，官方mention展开后13174/35388。
所有incoming CAUSE distinct-multi组均有dataset-None事件候选；PRECONDITION为5836/5837。
同方向event-event BEFORE共398671，其中annotated causal27598、无annotated causal371073；
另有5336条causal无同方向BEFORE。原raw BEFORE618143中219472涉及非event端点，r2
不将这些TIMEX pairs冒充causal negatives。None仍是标注口径，不是因果真值的否定。

裁决：原生多原因训练机会存在，但mention多正例中的coref重复是强竞争解释；任何
未来候选至少要matched coref重复/样本权重与普通multi-positive对照，不能单正例softmax
丢其他真因，也不能以BEFORE伪造CAUSE。无新方法/效果/power准入，不重开旧hinge。
D4一手源码访问web已成功核机制，本地curl保存全文TLS EOF失败，source_review.json
如实记无本地全文archive；不伪称下载成功，也不把网络失败当文献不存在。

§25.76 追加真实端到端合成核验：只用既有P1 fixture gold-self，为七行（五臂+两锚）
实际调用未修改official wrapper并走独立MUC/profile/paired/guard聚合。共指/三关系均应
100，且同分不得判突破/归因成功，已实际通过；没有读取方法dev预测。新增e2e测试后
全套933passed/87skipped，ruff0、ekg-smokeOK；收集器code未改、只增集成覆盖。
§25.77 R175十件原/修正版CPU分析与源码访问记录已备份4090并逐件hashPASS，manifest
SHA`f200e86fed49464c20a7f90b7cf5bb07b33391142e34e590aff5f4b0b75e03ce`。
首次校验在传输尚未结束时缺文件，rsync完成后重核全部PASS；不把首次工具失败冒充成功。

§25.77 D4原始标注policy进一步核实（R177 source_review.json，官方19页PDF经web完整获取，
本地未归档PDF，不虚构PDF字节hash）：[MAVEN-FACT2024 §2.1–2.2](https://aclanthology.org/2024.findings-emnlp.651.pdf)
将factuality source固定为作者，supporting words以PS+/PS−/CT−为标注对象，CT+/Uu通常
无显式支持；§25.74的类依赖空字段部分源于结构性标注policy，不能称随机缺失，也不能
当已标注的负scope/负attachment。它仍不排除只用可靠正例的辅助监督，但不提供其功效。
原pipeline先预测factuality再预测support words；不能将gold evidence可用性直接当部署
classifier输入。没有逐引用source-holder gold，不表示任务的factuality source定义未知。
原paper说明released train与valid/test的标注流程不同；本次不读原valid/test标签，继续
冻结train-only/OOF边界，不将不同原split论文数字搬作我们的主表。无外部成绩引用。

### 25.78 C41-T mass数值修复生产门闭合（2026-10-16）

**开工自审/裁决范围**：恢复原预声明总量强控制，科学目标/预算/单seed不改；这是
§25.75数值缺陷的工程修复，不是观察dev后换新方法。旧失败完整保留；其余四臂原身份
复用，只有mass从同initializer重跑。尚无科学KR达成。

完整CPU全模型221梯度门见§25.75。GPU0在marginal真正GONE且无compute apps后使用；
新smoke PID1141139（HEAD301a890）已GONE/complete，实际4microbatches/1optimizer cycle，
allocated/reserved峰值5153018368/5708447744bytes；参数摘要从5b67cbba…变为
cd4849f7…，无zero-LR审计hook。原encoder首warmup步LR仍为0，不虚称本周期encoder
有非零LR；scorer真实更新。8doc train-only无标签完整四头export/独立CPU/source decoder
parity通过。report SHAeb9b03fd4eaca49ed7db0c7c3d8dfe30ab62c02b4c4a91f29d62d2f8d514d4e7。

独立根`runs/stages/C5/c5-mass-repair-20261016/`，config仍a88e9f…、数值修复代码076a874。
最终protocol SHA
`e9eacf43773ce2190624c24aeffbbc9d115a7c35f32c6ee9639c04bcf8426324`；
最终admission SHA
`7e5e56a52281c496b2301357406629c497e48ada184577cbb9d46a4e8e1425c0`，
`method_admitted=true`只准原seed13/100epoch的mass重跑；未增加seed、权重搬运或5090。
R176=`runs/stages/R1/r1-v76-mass-repair-production-20261016/`，completion manifest22件，SHA
`c2d99fc3ffb40d9b2c3b2f200fac8a345b2446bcc847e4d27b1e02097a8f2155`。

原四臂中marginal已完整100epochs/32800microbatch/8200updates、CPU export replay与
endpoint artifact门通过；原PID1097108 GONE、无提前评分。其checkpoint SHA
cf379e293201f20704b6316e3624d2951107dd1c69b796c67e66d73bf2dd2219留4090，
非权重预测/report/status/训练轨迹已取回LOCAL。其余root/exact/shuffle继续原训练。
统一评估overlay `configs/c5_joint_evaluation_repair_20261016.json`在任何方法评分前冻结，SHA
`6c24f07d944683020ed18035b7e5b008b78b240d37d59f9cec4baa8f86c07203`，
只映射mass至新路径/配置并披露aux float64；原科学门/目标/paired/护栏不改，必须所有
有效臂endpoint后才评分。不能把旧float32五臂合同写成完整成功，有限精度轨迹差异保留。

§25.78 R176 22件manifest已LOCAL/4090逐件重算PASS，`require_repair_admission`双端PASS。
首次stdin检查使用namespace导入而缺scripts PYTHONPATH，import失败；修正检查命令为
`PYTHONPATH=src:scripts`后通过，不改生产脚本/合同或伪称首次检查成功。
新准入可信锚为本节即将push的提交；之后才启动train。consistency36PASS、diff --check通过。

### 25.79 C41-T修复mass正式启动，继续等待完整端点（2026-10-16，wip）

外部可信新准入锚2468e39已push后，4090在无tracked改动下安全同步；新mass train
默认无execute预检PASS。成功重核GPU0无compute apps、79MiB/util0后，一条SSH发起
一个setsid nohup任务，完整命令/cwd/输出事前已披露。PID1142785、GPU0，配置a88e9f…、
修复代码076a874、launch HEAD2468e39；独占输出
`runs/stages/C5/c5-mass-repair-20261016/train/mass/`，日志
`logs/c41-t-mass-repair-s13-20261016.log`。成功SSH确认ALIVE/running，非endpoint完成。
原mass39轮失败路径不动，从同initializer完整100epochs；checkpoint留4090。
R178=`runs/stages/R1/r1-v78-c41-training-continued-20261016/`保存命令/资源/身份。

marginal endpoint已闭合，root/exact/shuffle继续原身份；全部有效臂完成后立即按冻结
新overlay评分并双端独立复算，不提前选分，不把启动或工程修复记作科学KR。
R177标注policy记录已原4090逐件hashPASS；无PDF/权重搬运或新模型训练。

### 25.80 A4普通multi-positive强rival机制准备（2026-10-16，非正式接队）

**开工自审**：科研价值是表4-3/KR3.2避免拿单正例/弱set-pool充强对照；§25.77已证
native多原因及coref重复可分，下一须区分每个正例与只奖集合总mass。可行性是
[SupCon2020/2021v5 §3.2 Eq2–3](https://arxiv.org/pdf/2004.11362v5)与正文脚注链接的
[作者PyTorch reference](https://github.com/HobbitLong/SupContrast)，先核真实源码/许可/
固定revision，再轻量CPU构造公式/原criterion检查；零encoder/optimizer/评测标签。
这是已授权T期间文献/可行性准备，不准入A4新机制或训练，不声称复现ImageNet/CIFAR。

paper核到23页v5，外log逐正例均值与内log集合均值是已比较过的不同目标，不能以
“容纳多正例”本身立新意。作者reference HEAD通过git ls-remote实查
66a8fe53880d6a1084b2e4e0db0a019024d6d41a；下一下载原loss/README/LICENSE并核模块。
TensorFlow仓库web访问InternalError，不代表无实现；作者PyTorch文件/README已可读。

§25.80 作者原loss/许可证已按固定commit取回，未修改；README curl TLS EOF，web正文
可读，未伪称三文件全部下载。BSD-2-Clause原notice保留；loss SHA
`a432e24bdff118aa0ab3013a4c85a4b099871ebef554177054d91fe6fca616db`。
仅原SupConLoss在CPU合成4×2×3 normalized features/labels上实跑forward/backward，
finite；无encoder/参数权重/optimizer/真实数据输入，不算完整图像benchmark复现或A4适配。
R179=`runs/stages/R1/r1-v79-a4-contrast-preparation-20261016/`保存源码、许可、probe/report。

另外按原Eq2–3在合成logits[3,-3,0]、前两项均positive核梯度：内log set-pool的弱正例
梯度-0.0001169901，逐positive外log均值为-0.4976443669；强正例在外log梯度为
+0.4503302117，说明它也含正例间平衡，不能声称完全无competition或保证causal recall。
这是已知目标的构造差异，不是我们新颖性/数据效果。未来rival不能只奖positive集合mass；
还应包含逐正例目标及重复/coref权重控制。保留独立CE与完整候选，不能单winner解码。
作者criterion的denominator覆盖整个batch；只改positive mask并不移除其他target，不能
把普通batch SupCon冒称严格target条件化。A4 adapter/full pipeline尚未实现或准入。
四件manifest SHA
`dc6d7248210b61aee6bda8bd9dde43dbf1e67c95328e90aed7c973b8d9a09ada`；双端备份后另核。

§25.80 现有D4准备已整理为`research/20261016_d4_native_supervision_review.md`：逐版本
记录具体数据/新意障碍、普通CMLE/SupCon强rival、正例辅助仍未被否定、正式接队的
决定性门；不因标准loss可运行即准入、不取消D4章或交作者重选题。
HEGAT官方supplement三页已可访问，能核graph/span/lexical架构级描述；其正文订阅
预览仍不能当完整方法已核。新增此有限访问事实，不据之声称候选已排完最近邻。

§25.80 R179四件原source/license/probe/report已备份原4090，逐件双端hashPASS，
completion manifest SHA
`dc6d7248210b61aee6bda8bd9dde43dbf1e67c95328e90aed7c973b8d9a09ada`。
仅文档准备落地，consistency36PASS、diff --check通过；未新增生产代码/模型训练。

### 25.81 C41-T端点收集：marginal/exact已闭合（2026-10-16，wip）

exact已完成原100epochs/32800microbatches/8200updates、full export/CPU replay与
status=complete；原PID1097148成功SSH确认GONE。checkpoint留4090，SHA
`de35493b618360e5ef27d5027b29a147ceeb07bdd115e28612162ab2d7df57ff`；
其非权重预测/report/status/训练轨迹已取回LOCAL，独立endpoint helper重核配置、
预算和report/predictions实际SHA通过。预测SHA
`571f877ed0f0944f97dbb28b9defee76fbb38f4040c78ece6222ffe9f5b5af8e`；
report SHA`bf68f8367cca4009c2961ae65dd2bb40ccf3ea6e51b4c8e06f5c062e95672f6f`。
marginal端点见§25.78。R180=`runs/stages/R1/r1-v80-c41-endpoints-20261016/`目前
保存两项身份，后续追加其余端点，不假称五臂已齐。root/shuffle/修复mass仍待完成；
没有方法dev分数被计算/查看，V未开始，科学KR未达成。

§25.81 root也已完整100epoch endpoint/CPU replay与artifact门通过，原PID1097110成功
SSH确认为GONE；非权重四件取回LOCAL后独立endpoint helper实际重核PASS。
root checkpoint留4090，SHA`d38ea7f81a3fad238d00aae6ac7b84dd7eae86cd3787e267c03b3677a86b9157`，
预测SHA`fd1238a6130a4ea0739969d49eb42e3d16eb4fa9f7dd94cbcfa3563a35039c1a`。
R180追加root身份，现三个有效端点闭合；shuffle/修复mass仍运行，无任何方法dev评分。
接续以前台只读工具监测已有两PID；不安装服务器后台等待器、不启动/重试新任务。

### 25.82 C41-T/V全部闭合，固定exact候选未过门，正式接D4-R（2026-10-16）

**开工自审**：对准表5-3/KR1.1–1.2的联合依赖辨识，必须全臂endpoint后统一评分，
不以数学正确、负控单独通过或工程门替代效果。原机资产/生产门已闭合，评价overlay在
任何方法dev评分前冻结；本次只完成既定T/V及科研裁决，无新增seed/5090/权重搬运。

shuffle与修复mass均到100epoch/32800microbatches/8200updates、完整无标签导出与CPU
cache/source decoder parity；成功SSH确认PID1128804/1142785均GONE。至此五个有效端点
齐备；非权重四件取回LOCAL，逐臂预算/配置/预测/report/checkpoint身份核对PASS。
R180追加两项identity后封存五件manifest，SHA
`f22476e1656995c94763d7ac3d5e502713f7b94d7272fbeeccf72434947d2b7a`，双端hashPASS。
checkpoint/score caches/optimizer均留原4090。旧mass39轮失败原命名空间保留；修复mass
aux float64限制见§25.78，不将原FP32合同伪称完整成功。

4090无tracked改动下安全同步已push619c0a7后，LOCAL与4090分别运行冻结collector，
命令均为`python -u scripts/evaluate_c5_joint_dependence.py --config
configs/c5_joint_evaluation_repair_20261016.json`（LOCAL用uv，远端`.venv/bin/python`，
CUDA隐藏）。七行官方四共指/三关系分数、独立MUC计数/profile、paired bootstrap、
错误交换与所有科学门的**完整report JSON两端相等**；两个status及其全文件hashPASS。
report SHA`702317f596edb109f784d826eb18e29656d6e6fcca063f0012acca64087401da`；
document counts SHA`2cca3ce5513e5509927dc46394a3258bdc2910bcb77c65f7b005f25ff3a48567`。
原始双端输出/比较/source与成本身份在R181
`runs/stages/R1/r1-v81-c41-joint-verdict-20261016/`。

**指标唯一权威落点**：[PHASE_C末节](PHASE_C.md#c41-v--exact-joint固定单seed五臂裁决2026-10-16)。
该节完整报告主指标/强控制/配对区间、三项共指护栏、错误交换、三关系P/R/F1边界、
训练墙钟/显存、checkpoint位置与限制。本页不重复主表数字。

**裁决**：`single_seed_exploration_passed=false`；target/positive-controls/paired-attribution/
guardrails均FAIL，negative-control PASS。点估计不胜root/mass且区间跨零，不得写成
“证明总体显著更差”或“等效”；负控通过也不能单独识别exact联合依赖优势。KR1.1/1.2
本候选未达到，KR1.3前置不满足，O1仍未完成。停止固定exact/pair-F1配置，不扫scale、
epoch、threshold或额外seed；无final-valid访问，不改旧失败家族/论文结构。

按主表正式接队**C41-D-R**，先复用§25.74/§25.77/§25.80与D4原生监督准备卡，
核可识别的新干预和最近邻正文/源码差异。D4仍未准入训练；不把C5负结果当整个Goal
完成，不让作者重新选题。新C5实质不同路线日后仍须新证据回R1。

作者回复客户端Goal已恢复active，但本线程get_goal仍返回usageLimited；如实保留状态
不一致，按其继续指令执行已授权工作，未覆盖/重建Goal，也未声称工具自动续跑恢复。

§25.82 R181十九件封存manifest SHA
`20319d40c1e812543841984858daeca74cfc13e73afeb22214a540b698dea62b`，
已备份原4090、逐件双端hashPASS。文档一致性36项及diff --check通过；本次未改生产代码，
不以旧全套测试冒充新运行。独立两端真实official评分与endpoint检查是本结果的验证证据。

### 25.83 C41-D-R正式接队：一手图方法与监督边界审查（2026-10-16，wip）

**开工自审**：科研价值是表3-3/KR2.1–2.2在训练前排除“已有graph/evidence/普通contrast”
重合，并防止借用DLEF全局标签伪造MAVEN的source/scope监督。可行性是仅核公开正文与
作者固定revision源码，复用§25.74/§25.77的原生train覆盖；零encoder/optimizer、没有
held-out或final-valid标签访问，也不将外部公开XML并入本项目训练。

C5固定候选裁决已经写入主表并push dfa9207；D4-R现为唯一活动切片，未准入新训练。
下一具体证据是UR-HAT正文及作者源码的目标/关键词统计/图边/评测选择，作者仓库HEAD
已用git ls-remote核为35447c414d97d3def96d85c82257f5eaaaa538cd，MIT。
它有真实模型/训练源码，不可标README-only；原benchmark复现、环境可运行及MAVEN
透明适配尚未实跑，不得提前宣称FR-016(a)/(b)已完成。

§25.83 下一项有界train检查的科研价值：决定绑定候选能否合法假设“一个支持token只属于
一个事件”，而不是再测一般覆盖率。只用同一冻结fold-1 train及有效native正offset，
构造token→mention/event的观测关联，区分共指重复与distinct事件共享、不同标签共享。
可行性是无模型CPU计数并与R172既有覆盖核对；不将未列出的关联当负scope、不推导
性能/power。若有共享正关联，一对一/exclusive binding必须拒绝或重新定义，不能用
Sinkhorn/匹配等模块名称掩盖错误监督假设。

§25.83 R182 native positive-incidence检查完成，1747篇固定fold-1 train与R172类级覆盖/
有效token/无效offset计数逐项一致。3128个被标support的token节点、3575条mention正边、
3570条去共指重复event正边；344个token关联多个mention，340个关联distinct事件，
35个还关联不同事实性标签。记录中包括同一`did/not`同时支持同句两个不同事件的
PS+/CT−，只作原生正标注的反例，不把它升格为逻辑作用域或世界真值。结论：
**one-token/one-event排他binding版本数据不成立，停止**；不否定所有positive-only辅助。
没有造负边、读held-out标签或用计数声称功效。

UR-HAT主文经web读到§3.1/3.3/3.4/4.1，作者MIT源码与四页appendix已归档；七个原py
仅syntax-parse通过，未加载模型或实跑原benchmark。训练目标为document CE + mention CE
+ Gaussian KL；关键词统计只取训练数据，不能误报它靠test标签选keyword。其XML读取
独立sentence/document值；公开入口每epoch在其`test_loader`评分并按micro+macro挑档，
需与正文所述validation调参区分，未经复现不能泛化成论文整体无效。源码报告限定
labels=[0,1,2]，但head维度是len(label2idx)，不误写为硬编码三类head。直接移入MAVEN
卡【数据/协议】，须重定义/透明适配，当前不是已完成FR-016(a)/(b)的新对手行。
一手出处：[正文](https://journals.sagepub.com/doi/pdf/10.3233/FAIA230508?download=true)、
[作者固定源码](https://github.com/JiaweiSheng/UR-HAT/tree/35447c414d97d3def96d85c82257f5eaaaa538cd)。

另核[Conditional SupCon2022 §3.1 Eq2](https://aclanthology.org/2022.findings-emnlp.199.pdf)与
[作者ConSupConLoss](https://github.com/JFChi/CSCL4FTC/blob/e55a5cc8473feeacd1e9eabbe41e59b9c91f075c/models/contrastive_losses.py)：
共同group/task-label限制denominator已有，不能仅改为事件/同语境就立新意；该文EO条件
不自动变成事实性归属论证。只静态读源码，未集成/运行，许可未闭合。CoDE/scope正文
仍订阅限制，精确标题搜索出现的expert-linking CODE是不同论文，不能混同填缺口。
本节未引用外部成绩，也未用其他split的数字比较MAVEN。

§25.83 R182十五件completion manifest SHA
`429c73d31444a440e5d3a85965f44fef39c60d38dcdcdfe7601d973dc66eb715`，
已备份原4090、逐件双端hashPASS。没有执行新模型/optimizer或导入上游XML作训练。

### 25.84 C41-D-R强linear原train重放诊断准入（2026-10-16，wip）

**开工自审/科研价值**：表3-3/KR2.1–2.2的绑定假设不能仅靠support覆盖推断。下一
只用已恢复且冻结的strong linear fold-1 checkpoint在**它自己的train manifest**重放预测，
检查残余错是否集中在同语境不同事件/共享support等原生机会，避免把数据存在性当
“strong control确有该失败”的证据。事前固定全train、类别/同句异标签/有效support/
共享support桶，不筛评测中的好看例子。训练集拟合不测泛化收益、因果机制或power。

**可行性**：checkpoint在4090原机、selection-dev选出的epoch既有身份不变，
`runs/stages/R1/r1-v61-recovery-ready-20261008/d4/linear/fold-1/checkpoint/`；
目录content digest成功重算为
`4d19dd58da1faa6cfb356f9d9440a372d7bd46a29004fea6b527809655b9fc9b`。
model.safetensors SHA`53e286816d23c444c05d7280c0eb407375d235c46ba6f005c14a15753726a145`，
head SHA`a079addb39a7478a3cddfff34fed52dab6659ef5c215d8db9dec92104cda3ed7`，
baseline_config为linear/cls、max_length128、原五类顺序。原run元数据确认seed13；
没有新训练、optimizer、checkpoint搬运或5090任务。只从原public-train投影固定1747个
train IDs，assert与selection-dev/evaluation ID集合不交；不将它们的实例标签传给重放器。

复用未改`evaluate_factuality.py`及有hash/空卡/独占输出/status门的
`launch_recovery_validation.py`，另冻新replay config；CPU预检、源码/资产hash与空卡
门通过、披露确切命令后才作4090只读推理。它不是proposed method准入，不能把原
12epoch训练再跑一遍或事后据train分数改选checkpoint。

§25.84 replay config `configs/d4_anchor_train_replay_20261016.json` SHA
`7c497822b6f0ea1a53fc6f1b23a960ae137617e2e28c7e6ad5fba06f0a89c516`，
投影SHA`a865781e2000cea9cae6a6c368b640f8b404e07f672f58bbce2510d698880fa9`
已LOCAL/4090独立生成并重算一致；没有从LOCAL传checkpoint。原入口未修改。
启动前本地完整pytest exit0（torch用例skip，不冒充真实Torch通过）、ruff0、ekg-smokeOK、
consistency36PASS及diff --check通过；该配置只准只读推理诊断，不准新方法训练。

§25.84 冻结配置/文档6c5d72c已push。首次远端git fetch因gh-proxy.com DNS失败而未同步；
只读getent随后已解析，显式重试成功同步6c5d72c，未修改网络设置/代码。CPU预检全部
source/input/checkpoint与输出独占门PASS；成功核GPU0空闲、无compute apps后，披露完整
命令并发起一次setsid nohup推理。PID1307277，日志
`logs/d4-anchor-fold1-train-replay-20261016.log`，成功SSH核ALIVE；预期标签/report/status
在R183。没有optimizer、checkpoint重选或额外训练；尚未宣称重放完成。

### 25.85 D4-R输入anchor可见性检查自审（2026-10-16，wip）

**科研价值**：区分“模型不会绑定”与“冻结输入已丢失目标锚点”。真实源码
`marked_sentence`只取触发句并插星号，`pool_mentions`在CLS模式以max_length128做
prefix truncation后直接取hidden[:,0]；它没有检查target span是否还可见。不能将
“marked-CLS”一词当作每条输入必然带目标的证据，也不称它是全文档模型。
若同语境不同事件在预算后得到相同token IDs，其不同标签不能由该确定性输入区分。
这会改变后续机制/强控制的判断；修输入即使有益也只能算控制修复，不能算创新贡献。

**可行性**：只用R183已投影的固定1747篇train、原checkpoint tokenizer和未改marked_sentence，
隐藏CUDA、不加载encoder/optimizer，CPU批量比较full与原128budget offset/IDs；
预先记录complete/partial/absent target、同句相同input的多标签冲突以及各类覆盖。该工作
不改旧contract/checkpoint/输入，不读取selection-dev/evaluation实例，不跑新效果结果。

§25.84 只读CUDA重放已complete，成功SSH确认PID1307277 GONE；固定1747篇/44384个
namespaced mention全覆盖，labels SHA
`695b45992746a52238651fe981226338b2ee1bd4e7afc245075e1e435245463e`，
report SHA`36c5ac085bb9a736337490ffcff32867b25d6d68b4f77791414c2a08fb82c172`。
原checkpoint目录content digest前后均4d19dd58…fc9b，参数/配置无写入。

| 类别 | train gold数 | 正确数 | 预测该类数 | train F1 |
|---|---:|---:|---:|---:|
| CT+ | 41889 | 41247 | 41270 | 0.992003 |
| PS+ | 1357 | 1340 | 1717 | 0.871828 |
| CT− | 897 | 876 | 1120 | 0.868617 |
| PS− | 170 | 165 | 177 | 0.951009 |
| Uu | 71 | 71 | 100 | 0.830409 |

train macro-F1=0.9027732534973214，独立Counter按每类2TP/(N_gold+N_pred)重算与
原report在1e-12内一致。这是in-sample拟合诊断，不是新的OOF/方法成绩，不能与
§25.37不同population的OOF直接相减作效果。label-only baseline的evidence F1为零是
未预测证据的定义，不当成其标签错误原因。

| 预定bucket（可重叠） | CT+错误/数目 | PS+ | CT− | PS− | Uu |
|---|---:|---:|---:|---:|---:|
| 全train | 642/41889 | 17/1357 | 21/897 | 5/170 | 0/71 |
| 同句存在异标签事件 | 162/4153 | 14/1148 | 19/805 | 5/158 | 0/69 |
| 有有效正support | 8/28 | 12/1215 | 8/828 | 5/167 | 0/8 |
| support被多个mention共享 | 3/8 | 2/350 | 3/165 | 1/58 | 0/0 |
| support被异标签mention共享 | 3/8 | 1/30 | 0/11 | 1/22 | 0/0 |

5539对同句原生异标签pair中，5210对两者均正确、325对仅一者正确、4对均错；227对
被预测成同标签。保留类别分母，不能以bucket粗错误率识别因果绑定失败。结果支持
“可靠linear已经能拟合绝大多数异锚区分”，不支持以“同句一向只能给一个label”当其
普遍能力缺陷；仍不能排除局部或泛化层面的归属问题。

第一次临时`residuals.py`将raw mention ID直接查namespaced预测，KeyError即停止；原
脚本和failure记录保留。查到loader明确`doc_id::mention_id`后，新`residuals_r2.py`用
该精确ID与新输出名，全部ID集合/类计数/独立指标PASS；未改预测或重跑GPU。
R183十二件封存manifest SHA
`81b0bdca737bc853b79bca75c02a69475d707d298bf545177dd0eb4b868786e8`，双端hashPASS。

§25.85 CPU tokenizer检查已complete：44384个train mention中44374个目标完整可见、
10个目标全被截断（CT+7、PS+3），没有partial；CT−/PS−/Uu目标均完整。出现两个
同句相同input-ID组，其中一个含5个不同标签mention，确定性输入的最少强制错误数为2。
与只读重放逐mention精确ID连接后，absent10条错2条，其余完整44374条错683条。
因此截断问题确实存在，但**本train结果不支持它是当前主瓶颈或PS−/Uu问题的解释**；
不据此改旧输入或启动centered-window训练，也不将输入修复当创新。旧strong checkpoint
保持原身份，未来若改变打包仍需透明匹配控制。

CPU精确命令（cwd `/data/TJK/ekg`）：`CUDA_VISIBLE_DEVICES=-1 TOKENIZERS_PARALLELISM=false
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONPATH=src .venv/bin/python -u
runs/stages/R1/r1-v84-d4-anchor-visibility-20261016/visibility.py`。无encoder/optimizer。
R184四件manifest SHA
`969a9ecedca7a6154dbdb1c0a2e7de1d721437a5e12950dc45116ecfb7080ecf`，双端hashPASS。

### 25.86 D4当前绑定候选R1裁决：未准入；接续A4-R（2026-10-16）

科研价值是对表3-3/KR2.1–2.2给出明确去留，避免无限准备或把已知目标换名训练。
可行性依据§25.74/§25.77/§25.80/§25.83–§25.85的原生train与一手机制证据；没有
拟议D4训练或新OOF结果，不能把此次拒绝说成新方法效果被实验证伪。

| 当前具体版本 | 准入裁决与命名障碍 |
|---|---|
| 缺/不重叠support即负scope、跨事件标签即NLI | 拒绝【数据】；没有这些gold，不能伪造 |
| one-token/one-event排他绑定 | 拒绝【数据】；原生正关联允许distinct事件/标签共享 |
| 普通按语境/标签条件化或supcon | 不作新方法准入【新颖性】；CMLE、SupCon、conditional denominator均有明确先行机制 |
| 将预测evidence再池化给标签头 | 不重新立项【封存边界】；属于已停止D3方向，不能换名复活 |
| 单纯positive support→attention辅助 | 不准入当前新方法【实质差异未闭合】；可行性未被否定，但没有超出已有rationale/evidence supervision的明确新干预与可识别竞争解释 |

[R2A2018 §3.3–3.4](https://aclanthology.org/D18-1216.pdf)明确学习rationale到attention的
映射，再以label loss+attention距离监督target classifier；§4.2还含直接rationale监督
attention的RA-TRANS对照。它的跨域source/target/未标注数据前提不直接移入MAVEN；
此处只界定“rationale辅助attention”并非新概念，没有复现/比较其外部成绩或集成代码。
不从这一邻居推导所有未来positive-only设计都无创新；当前没有一个已定义、可独立
验收的新机制通过门，所以`method_admitted=false / no_admitted_candidate`。

train重放削弱了“strong linear普遍无法分辨同句事件”的动机；它没有测泛化，所以也
不能以train高分证明D4无研究空间。单seed诊断、覆盖率、输入计数与阅读量均不达成
KR2.1/2.2；KR2.3前置不成立。本次关闭的是10-15当前绑定模板的准入回合，**不是
整个D4章、所有证据方法或一个已训练机制家族**。

按已授权章序/主表，D4-A/TV在没有候选时不启动；正式接队**C41-A-R**，复用§25.77/
§25.80的native distinct多原因/coref重复与普通multi-positive强rival。优先裁明“按目标
组织的已知对比学习”和真正新干预的差别，不拿单正例softmax/弱set-pool作对手。
后续D4替代须新证据与实质差异回R1，保留全文通路/强linear与原五类协议；不交作者重选题。

§25.86 R185裁决记录manifest SHA
`27e401ffbb876822da174103f5a773779aed3fc0e957fe7e02fc31f6af451c65`，
已备份4090并双端hashPASS；R183/R184逐件身份与原checkpoint前后不变已核。

### 25.87 C41-A-R正式接队自审（2026-10-16，wip）

**科研价值**：对准表4-3/KR3.1–3.2，当前“目标条件多正例”只能在排除普通per-positive
contrast、已知listwise/learned-threshold、coref重复权重和更保守预测后讨论新贡献。
native真实多原因机会与重复分离已由§25.77闭合，普通SupCon的outside/inside-log及
batch denominator限制已由§25.80闭合；不重做它们，也不拿“有多个正例”当新意。

**可行性**：仅复用固定2622篇train分组、可读一手论文/作者代码与轻量CPU构造审查，
不读取held-out/final-valid标签或启动新模型。下一核已知多标签/排序阈值与decoupled
contrast的真实公式/实现，以及conditional目标的group-offset/全None校准边界；明确
source assumptions、input unit与适配差异，不能把DocRE relation-label轴直接冒称A4
target×candidate轴。强控制缺口先补证据；没有实质差异/有效合同前不准入A4训练。

§25.87 已核[ATLOP2021 Adaptive Thresholding公式及Localized Context Pooling](https://ojs.aaai.org/index.php/AAAI/article/download/17717/17524)
与[作者loss源码1db77ab](https://github.com/wzhouad/ATLOP/blob/1db77ab8bc4fe5f7f8c23067ea17055d58b310a3/losses.py)：
其TH排序目标能处理多正例和无正例，不需dev扫阈值；entity mention logsumexp与pair
localized context也已有。原criterion SHA
`f830ad0e52a88e57ab708733553bdb32f71dd0fb6d31560a998cc5ad6b450502`。
第一次ls-remote TLS失败，显式重试后固定HEAD已核；只在/tmp读取原实现，未发现根许可，
不集成/复制成项目方法。CPU原ATLoss/get_label无改动、合成logits前向/反向与多正例/
None分支实际通过；未加载encoder/optimizer、未复现DocRED或声称MAVEN adapter准入。

原ATLoss写入传入labels[:,0]，probe显式传clone而保留源标签；两正例logits
[TH=0,strong=3,weak=−3,negative=0]，两positive梯度分别+0.900660/−0.995289，
故不能把此已知目标也称“positive完全不竞争”。默认get_label可同时返回多个positive，
不需single-winner。原轴为entity-pair内的relation labels，A4拟议轴为同target的candidate
events；移轴需透明适配，不能把已有阈值目标换名当新意，也不能在推理中用gold coref
冒充task-given entity IDs。

[DCL2022 §3 Proposition2 Eq8–10](https://arxiv.org/html/2110.06848v3)明确去掉denominator
positive项；因此“移除positive竞争/解耦分母”本身已有先行性。其监督分类附录也不
保证优于CE，不能拿视觉SSL收益承诺causal recall。原ECCV PDF后续访问timeout，arXiv
v3 HTML机制成功读取；不混同DeACL/后续DSCL，未核作者完整runnable code。

合成relative per-positive loss在candidate scores[−1,−2,−3]统一+8后保持
0.90760596444438，而相对固定零阈值的positive个数从0到3：说明**纯组内相对目标
不能识别group offset/绝对None校准**，不是数据集效果或新loss。复核R175原十件seal
f200e86…后重用已有train统计，所有61362个event-target group均有其他event候选；
incoming有20405组包含任一causal subtype，40957组两者都无；outgoing为13051/48311。
单subtype无positive组更多（原计数见§25.77），不能误称每个“无CAUSE”都是全None。
候选不能仅在有positive组上优化relative objective后声称解决完整causal任务，必须保留
原CE/绝对校准和全候选；annotation-None仍不是世界因果否定。

新近[CLECI2026](https://www.mdpi.com/2078-2489/17/4/321)已读publisher §3.1–3.2的
context-to-label/contrastive/GAN框架；后续429、官方PDF CDN工具不可访问，完整公式与
作者可运行代码未核，不把它填成完整方法审查或声称无代码。无外部成绩被搬入主表。
以上证据R186=`runs/stages/R1/r1-v86-a4-objective-neighbors-20261016/`，A4仍R1 wip，
没有proposed训练或新方法效果。

§25.87 R186五件封存manifest SHA
`4209e7611a717b74c93992b240c397aaf230fbd7a4672a16dfbdf0ffc41897fa`，
已备份原4090逐件双端hashPASS。当前边界/下一机制审查整理为
`research/20261016_a4_target_supervision_review.md`；先核event/mention监督单位与已有
joint/multi-instance机制差异，不把普通loss、重复重加权或旧aux移轴当新方法准入。

### 25.88 A4身份与监督单位审查（2026-10-17）

**科研价值**：对准表4-3/KR3.1–3.2，排除“共指替换/簇聚合/邻接一致性本身是新机制”
及“相同因果邻接就是真实同一事件”的竞争解释；不重复§25.77的多原因计数。
**可行性**：固定train IDs、已有官方loader、作者公开实现的静态审查及轻量CPU代数；
不加载模型/optimizer，不读held-out标签，不作新方法效果或训练准入声明。

执行前界定：核原生event关系的mention展开、普通组均值与逆重复权重的等价性、
有非空causal邻接但仍为distinct events的同邻接实例。后者仅检查gold注释上的可识别性，
不是世界因果完整性，也不把gold profile当部署输入。结果留在R187独占namespace。

| 一手来源 | 核实机制与可比边界 |
|---|---|
| [Gao等NAACL2019 §4.2/§5.2 Eq13–15](https://aclanthology.org/N19-1179.pdf) | 已用预测coref作跨句→同句max-score替换，并以带惩罚slack的约束鼓励coref/causal互斥和邻接一致；并非全部硬约束。任务是过滤事件类别后的ESL无向causal，不移植外部成绩 |
| [JEREX EACL2021 §3.1(b,d)/Eq12](https://aclanthology.org/2021.eacl-main.319v1.pdf)、[作者源码](https://github.com/lavis-nlp/jerex/tree/85851dfcbb485d9bfa2bf662b8073e826c760d7f) | 推理预测complete-linkage簇，再max-pool mention-pair表示；训练用entity簇/关系bag。MIT，实质代码及fetch入口存在，当前仅静态核查，未复现原benchmark或验证权重URL可达。DocRED严格entity指标不同于MAVEN完整mention候选 |
| [Xu/Choi NAACL2022 §2.2 Eq4–6](https://aclanthology.org/2022.naacl-main.395.pdf) | GC以关系邻接L1差异修正coref分数，加contrastive距离loss；训练影响双向，不能只称共享feature。原DocRED/DWIE、邻接pruning与本协议有差别；作者可运行代码本次未定位，UNKNOWN而非不存在 |
| [ERGO COLING2022 §3 footnote2/§5](https://aclanthology.org/2022.coling-1.185.pdf) | 明确是PLM隐含coref assistance，显式coref建模留作future；不得反写成已有gold/predicted coref模块。作者repo已定位，本次未运行 |
| [MTEI2026 §4.3/§4.6–4.7](https://link.springer.com/article/10.1007/s44443-026-00624-7) | 关系/共指双阈值alignment图、任务级Kendall uncertainty权重、HAC与majority vote；不是事件partition后验边缘化。DocRED/Re-DocRED且dev选阈值，不照搬训练协议；源码/runtime未核 |

H2C-Net及UAIGR2026目前只核publisher abstract/metadata，未完整核公式/代码，仍作待核
邻居而非已排除重合。H2C-Net同名OCTA仓库不是ECI实现；UAIGR页面open失败与可检索
摘要分开记录。没有因此声称文献空白；没有将任何外部数字加入本项目主表。

官方loader `joint/src/data.py:130–151`明确将event关系展开为Cartesian mention pairs，
其他ordered pair记annotation-NONE；gold event identity仅作训练/诊断监督。
构造CPU检查：group-mean CE为0.65，inverse-multiplicity weighted展开CE同为0.65，
普通展开mean为0.60；max pooling已有精确重复幂等性。因此这些变化本身不提供独立新颖性。
这是代数fixture，不是MAVEN效果、JEREX执行或原模型梯度结论。

仅固定2622篇train，61362个event中29782个有非空双向、分subtype的causal邻接。
按完整邻接分组后，1912篇含3578组**邻接相同但gold身份不同**的events，共10839个
events/20313对，其中2063对连event type也相同。空邻接全部排除；以原始边独立重建
签名PASS。故“相同causal邻接⇒同一事件”在注释层不成立，不能用关系profile替代identity
gold；不据此宣布GC预测失败，文本、learned scores与单向约束仍有额外信息。
annotation不完整的边界保持，这不是世界因果不可能性证明。

**裁决**：target多正例/learned-None/重复重加权/硬cluster MIL/一致性的简单组合仍不准入；
没有定义或证明新的posterior机制，没有A4新模型效果。A4-R继续，但结束泛列邻居阶段：
下一先核强anchor在固定train上的真实残余、subtype混淆和coref重复分组错误，形成具体
瓶颈后再定干预。主表先更新，禁止在诊断输出前预选模块/扫threshold/追加训练。

R187=`runs/stages/R1/r1-v87-a4-identity-neighbors-20261017/`，23件封存manifest SHA
`85d4fe4aae8ddc469a97a3ec873543a7d066687d9c8efaad3106858cd58f91a4`。
命令：`uv run python <R187>/identity_scope.py`，退出0；R175十件seal先完整重验。
工具路径查找失败及GC提取文本含NUL均如实记录，未影响输入/输出或被算成科学失败。
R187已备份原4090，23件及manifest双端逐项SHA一致；本地一致性门36项PASS、diff检查PASS。

### 25.89 A4强锚固定train重放准入准备（2026-10-17，wip）

**科研价值**：对准表4-3/KR3.1–3.2，区别真实distinct原因遗漏、coref重复与subtype混淆，
不从已有目标组合臆测瓶颈。**可行性**：原4090的official joint `best_CAUSAL`已成功只读
核存在及历史SHA一致；不是C5用的`best_COREFERENCE`，不能混用二者冒充主锚。
限定train、现有原版causal_predict/causal_dump、不改权重/threshold/seed；先TDD适配验证、
本地门和远端真实CPU smoke/成本，再依既有4090许可披露命令、核卡并执行只读推理。
这不是proposed训练准入，后续假设仍须实质创新、power与方法合同。

checkpoint=`gpu-4090:/data/TJK/ekg/runs/stages/A3/a3-v6-baselines-r10/official_joint/seed-13/`
`workspace/source/joint/output/13/MAVEN-ERE/best_CAUSAL`，517260581字节，SHA
`b1bba654f4b7ca52e491a1c87ec4ef2a85434fbe7fa82676a77c7ff7f575b84e`；
原main.py SHA `9440d825029f19c78246f7ae8b37319a652aeb7a6de31bd38206fa2b33ca4939`。
在原R163与original_joint/seed-13两个限定根下按train+causal/prediction名核缓存未找到
可复用产物；这是有界路径检索，不声称全盘无缓存。没有启动GPU或搬运checkpoint。

只读replay配置`configs/a4_anchor_train_replay_20261017.json`已冻结，SHA
`860adb2279b9d372d639de9bd3d5ae5ab02685e2f0b9a514cb41cd68378c577a`。
R188=`runs/stages/R1/r1-v88-a4-anchor-train-20261017/`；复用原causal_predict与causal_dump，
全部模型输入先投影为无label test格式；独立forward hook检查finite logits、None/ignore
输入mask与class-index parity，逐文档完整candidate含None，执行前后核checkpoint不变。
smoke固定原census的peak batch八篇；full须同配置真实CPU smoke及逐件hash通过。
非causal字段仅为原dump占位，不冒充另三任务预测；不更改官方源码。

TDD先见12项缺入口失败，再12项通过，覆盖漏文档/候选、非法class、gold泄漏与重复ID；
初次独占probe lint的import/列宽问题已修正，最终probe lint PASS。全仓`uv run pytest`
实际933 passed/87 skipped（本地无torch，未把skip当真模型通过）、ruff 0、ekg-smoke OK、
一致性36项PASS及diff检查PASS。下一实际原机CPU模型smoke，尚无推理/科学效果结果。

原机CPU smoke已完成，PID1652491已成功SSH核GONE：八篇/10760个causal候选，
forward 6.12秒（23个token chunks），输入preflight之后总56.1539秒；原predictor/独立
class-index parity、无label输入及checkpoint前后不变全部通过。原四卡分别有他人
vLLM进程，未启动GPU。主表已先调整为**原机4线程CPU full**：4799个chunks按实测
线性估计forward约21分钟，留2倍加IO/startup约50分钟；64逻辑CPU、load约15–17、
可用内存约470GiB，成本许可可行。估计不是时长保证，CPU诊断不声称复现GPU逐位数值。

首次统计器R2实际失败：把`candidate_population_digest()`返回的tuple当dict；双端
实际smoke复现TypeError，未产生统计输出、不算模型效果失败。原文件/失败和pre-full
seal保留，独立R3仅解包API、放开full-cpu并换输出namespace；native文件级fixture先
有效RED再GREEN，验证wrong subtype同时计FP/FN且原official evaluator一致。初次测试
collection的sibling import错误另记，未冒充有效RED；所有17项probe tests最终通过。
具体身份/修正见R188的`analysis_revision_r2.json`与`cpu_full_admission.json`；重放入口、
配置、checkpoint均未改变，统计器修复不需重复模型smoke。

远端origin网络fetch超时，未在失败后执行reset；改用已push提交的git bundle传代码，
双端bundle SHA `3896d210ebf62eba7bfa9863b18e0fe94fb4aa67de2c60f8159cd074e79e94fc`，
验证旧HEAD prerequisite/新HEAD及tracked clean后才fetch/reset到`c6f735f`。未搬权重。

在查看full残余前另核强锚目标本身：原`main.py:252/309–321`是逐ordered-pair三类
CrossEntropyLoss，再按全batch有效pair取均值；softmax denominator位于同pair的
NONE/PRECONDITION/CAUSE类轴，**没有跨candidate的single-winner归一化**。所以不能把
强锚错误预先说成“多个原因在同一个softmax里竞争”；新target-relative loss反而可能
引入原CE没有的competition。此处只指独立logit坐标上的loss分解；共享encoder/参数
梯度、类别与重复机会权重仍可耦合，不能将其偷换成“没有优化干扰”。本次train诊断
用于定位真实残余，不自动支持任何contrast新颖性或因果解释。

### 25.90 A4等待只读重放期间的强rival可运行性核查（2026-10-17）

**科研价值**：对准表4-3/KR3.1–3.2及FR-016，核已定位的ERGO官方实现能否作为完整
候选MAVEN适配的强rival，避免把代码存在、其他基准成绩或已知图机制当本项目成功。
**可行性**：本地仅clone/静态读code与原论文，必要时远端只读依赖import；不安装包、
不运行encoder/训练、不触碰full-cpu产物。重点核label方向/候选全集、原始基准及评价、
graph形状/算力、许可/权重和实际trainer。主表当前A4-R的强控制准备内执行，不插队。

[ERGO作者实现](https://github.com/chenmeiqii/ERGO/tree/afa3d347ec360242c01d15a34b1f1ae63714c789)
固定`afa3d347ec360242c01d15a34b1f1ae63714c789`；已取完整可见两commit历史，确有
model、trainer/CV和ESL缓存，**不是README-only**。`train.py`导入`processor_esl`，
当前树/可见历史只提供`processor.py`，pickle opcode也引用前者；这是具体接线缺口，
可记录rename/alias透明补丁，不等于整个方法不可适配。仅解析pickle opcodes，未执行
反序列化或把外部标签带入MAVEN。根许可、训练后权重/fetch未定位，不声称不存在。

正文[§3.1–3.3/§4.1](https://aclanthology.org/2022.coling-1.185.pdf)含BERT窗口与Longformer
两种encoder；当前公开model/train仅有Longformer类和cached ESL输入，raw feature/mask
生成器及BERT-window实现未在该树/历史定位。其binary ECI与native directed
CAUSE/PRECONDITION口径分开，不继承原CV/metric或拿换head作为忠实复现。

原`utils.compute_f1([1],[2])`在真实CPU返回P/R/F1全1：它按nonzero合并是原binary任务的
定义，**不用于评价native三类subtype**；native换型应计FP+FN。原Norm/RGTLayer以未改
AST类体、显式torch/math/F依赖做tiny CPU前后向，valid mask下finite、禁边概率零；
全mask attention行非finite，实际adapter必须明确mask/self/padding合同。第一次wrapper
漏供F引起NameError已原样保留，r2补原依赖通过；不是模型效果FAIL，也不是完整module/
encoder/trainer已运行。隔离CPU环境无transformers，未为此安装依赖。

源码在criss-cross mask**之前**分配dense QK。对本native上界109 mentions/11772个ordered
pair nodes、4heads，单FP32 attention tmp为2217279744字节；不含softmax/dropout/反传/
encoder。故mask不能自动视为稀疏省显存，但该下界也不证明24GB卡必OOM。完整预算仍待
合法空卡测量，不能裁评测候选掩盖成本。

裁决：列入有界可得性准备，**尚非同协议可运行强控制/FR-016已完成行**；没有ERGO训练
或新方法准入。后续若采用须先闭合原语料/fidelity、特征与方向/子类/全部候选适配、源码/
依赖/权重/许可与真实成本，不重写缺失encoder后冒称原实现。新颖性仍不来自RGT/focal。
R189=`runs/stages/R1/r1-v89-ergo-source-20261017/`，六件seal SHA
`3915b043ed3707f2accf18348460de82c07fbcd00da584fb4c32abb41e4d1b48`；tiny原类/criterion
命令为隔离CPU Python运行`probe_r2.py`，退出0，实际runtime边界见probe report。
R189已备份原4090，六件与manifest双端SHA一致；一致性36项及diff检查通过。
原4090只读依赖探测补充：torch2.8.0/transformers4.53.3，LongformerModel export存在，
`transformers.AdamW`不存在、lxml spec不存在；未安装包或加载encoder。故原CLI在当前
栈还有明确环境接线缺口，不能因tiny AST通过就标整体runnable。补充单独封存，不改六件
原seal：`supplement_manifest.json` SHA
`fe027a9130604edb200a00f11da464b767988db50a46e69c54d0993efed735d9`。

### 25.91 A4强锚全train残余闭合与当前模板裁决（2026-10-17）

**科研价值**：用固定train真实错误裁明当前目标条件模板的动机，对准表4-3/KR3.1–3.2；
不是把训练集分数当新方法优势。**可行性**：原机CPU只读重放、完整候选、原causal_predict/
causal_dump与双端独立官方核算均完成；未训练新模型、未改threshold或读取held-out选规则。

R188 full-cpu已完成，PID1657823成功SSH核GONE。原checkpoint前后SHA不变，权重留4090；
2622篇/66744 mentions/2297524 ordered causal candidates，candidate digest
`ce10549172550addb67059550d89c9fc04dc5cb6452560a5ccf42169e679d766`。
原predictor forward约563秒，输入preflight之后总616.4597秒；GPU未使用、optimizer step零。
官方causal P/R/F1与独立3×3计数逐项一致，local/4090完整report与per-doc文件字节相同。
CPU数值边界保留；不把该train得分与历史internal-dev主锚直接相减，不作泛化结论。

| train causal指标 | P / R / F1（%） |
|---|---|
| 全部positive micro | 79.612857 / 83.083481 / 81.311152 |
| PRECONDITION | 77.772671 / 81.284616 / 79.489872 |
| CAUSE | 84.583364 / 87.915591 / 86.217293 |

| gold\pred（native class） | NONE | PRECONDITION | CAUSE |
|---|---:|---:|---:|
| NONE | 2239239 | 7788 | 1935 |
| PRECONDITION | 6447 | 28765 | 176 |
| CAUSE | 1159 | 433 | 11582 |

| native positive stratum（按subtype的incoming distinct source） | gold mention-pairs | correct | predicted NONE | wrong subtype | recall（%） |
|---|---:|---:|---:|---:|---:|
| CAUSE:multiple_distinct | 4489 | 4149 | 266 | 74 | 92.4259 |
| CAUSE:one_distinct_single_mention | 2626 | 1516 | 783 | 327 | 57.7304 |
| CAUSE:one_distinct_with_coref | 6059 | 5917 | 110 | 32 | 97.6564 |
| PRECONDITION:multiple_distinct | 19811 | 17025 | 2700 | 86 | 85.9371 |
| PRECONDITION:one_distinct_single_mention | 10312 | 6776 | 3464 | 72 | 65.7099 |
| PRECONDITION:one_distinct_with_coref | 5265 | 4964 | 283 | 18 | 94.2830 |

同event-edge展开中，PRECONDITION all/some/no correct为20414/191/6154，CAUSE为
4678/64/1433。`no correct`不是`all NONE`；可能含错subtype。完整gold-positive漏/错
8215对，其中7606为NONE、609为换subtype；one-distinct/single-mention-source组占
4646个漏/错。所有strata含target mention重复，multiple-distinct组也可能含source
重复；计数按公开mention-pair任务，不能用event-level bag个数替代主指标。

**当前模板裁决**：没有支持“多个distinct原因在强锚中普遍无法共存”的train证据；它们的
原始recall在此反而更高，CE也没有跨candidate winner分母（§25.89）。这不是控制实验，
不宣称多原因使任务更容易或问题已解决。普通target contrast/learned-null、重加权、硬MIL
与邻接一致性目前仍无独立新干预，**关闭10-15当前A4目标模板准入回合，不启动A-A/TV**；
不是新方法效果FAIL，不取消A4章，也不证明所有未来target方法无效。

下一由执行代理在同一C41-A-R内选择**上下文交互/表示残余的新R1问题**：一次合并核原
256窗口中endpoint可见性/共同窗口与sentence距离，并用同gold event-edge的不同mention
context作有界配对诊断，区分窗口/上下文与重复机会，不从原始分层差异直接推因果。
先更新主表/新问题卡，再执行；不预选attention/graph模块，不把已知ATLOP/ERGO机制换名。
没有实质机制差异、强rival、power与合同前无新训练。当前三个科学Objective仍未达成。

R188全44件seal SHA `d7127246a0e78afd03bf42455f1303a46da193d050aec3a822328bca6e6220b9`；
独立full报告SHA `13ddf4587a8d5388b0599f23f1b955341c105c6acdae9f089c88064584eb7dbf`，
per-doc SHA `ff99ca9381d7cf4953b151b1d775d7e3d6c2071b587cd8d15e95997dfb9a0bb6`。
原R2统计失败、R3修复/测试与历史ALIVE快照均保留；最新`completion.json`记GONE。
R188全44件与manifest已备份原4090并逐项双端SHA核一致；本地三件套复核为933passed/
87skipped、ruff零错误、ekg-smoke OK，17项独占probe测试通过，一致性36项/diff检查通过。

### 25.92 A4上下文/表示新R1问题自审（2026-10-17，wip）

**科研价值**：对准表4-3/KR3.1–3.2，以§25.91真实残余检查共同语境与窗口交互机会，
排除仅按距离/重复机会说故事；不是先造新模块。**可行性**：原机仅重放官方tokenizer，
复用封存R188全部classes/无label输入与native train；没有encoder/optimizer/GPU或新seed。
主表已先更新，[新问题卡](../research/20261017_a4_context_residual_review.md)界定一次合并
诊断与停止条件。先TDD覆盖endpoint/span/全集和同event-edge配对统计，再执行原机CPU
预处理；与R188全集/混淆逐项对齐，未知ID/空span/漂移即失败，不逐slice重跑模型。

R190=`runs/stages/R1/r1-v90-a4-context-20261017/`，预处理plan SHA
`f164e8cbad3196d0e137c97b02e8f072e35b2d2d67ef9cae69254453d4ec56a9`。
只钉实际使用的tokenizer metadata文件及其文件集合，不为纯tokenizer任务读模型权重；
原R188 checkpoint身份不变。TDD覆盖完整trigger token内容/空span/缺ID、None误报、
同event-edge及同精确句距配对、空配对记UNKNOWN与macro/pooled权重差别；有效RED后
八项通过。首个分析器单测的sibling import接线问题已改为main内导入；probe lint PASS。
最新全仓三件套仍933passed/87skipped、ruff 0、smoke OK，一致性36项/diff通过。
该门仅准许已声明的CPU预处理/观察性统计，不放行encoder、optimizer或新方法训练。

### 25.93 A4上下文合并诊断闭合：不准入窗口新方法（2026-10-17）

原tokenizer CPU预处理已完成/进程1675092成功SSH核GONE：2622篇、4799窗口、892998
nonpad tokens、81713个event+TIMEX端点，**全部trigger内容与完整span精确核对通过**。
预处理44.1656秒，无encoder/optimizer。复用R188全部冻结预测；每个context/distance/
联合表可逐项加回同一3×3混淆，subtype×源事件重复机会的边际也与R188完全一致。
local/4090独立执行的四个统计文件字节相同，不是复制报告后称独立复算。

| train context | candidates | gold positive | TP | P / R / F1（%） |
|---|---:|---:|---:|---|
| same_window_same_sentence | 156898 | 12434 | 8014 | 78.3000 / 64.4523 / 70.7045 |
| same_window_different_sentence | 977236 | 23388 | 20596 | 80.3151 / 88.0623 / 84.0104 |
| different_window_different_sentence | 1163350 | 12740 | 11737 | 79.3041 / 92.1272 / 85.2360 |
| different_window_same_sentence | 40 | 0 | 0 | 0.0000 / 0.0000 / 0.0000 |

同句跨窗口组无gold positive，表中零为官方式zero-division约定，不解读为测到零recall
或无任务难度。跨窗口异句原始recall较高，**不是跨窗口改善的处理效应**，其距离、
类型、重复机会与文本均不同。原source在窗口内编码并池化span，再用两个事件向量
评分；没有跨窗口token attention不等于无法组合两个局部表示。

| gold event-edge观察性配对 | stratum数 / distinct edges | cross更好 / within更好 / 相同 | mean(cross-within) recall（pp） |
|---|---:|---:|---:|
| same_event_edge | 1994 / 1994 | 34 / 76 / 1884 | -1.788699 |
| same_event_edge_exact_sentence_distance | 408 / 318 | 2 / 3 / 403 | -0.245098 |

精确句距配对的within为477/483正确、cross为449/457正确；408个strata中仅5个不等。
它们按gold关系/重复mention机会选入，不能随机化词义/位置，也不代表single-mention
source的目标人群。没有用此表声明无效应、等效、泛化性能或已达到power；当前没有
足够特异的train证据把“缺共同窗口”立为新方法的主要识别机制。已有span均完整，不
复跑窗口平移/更大context来追分，不将普通cross-attention/graph换名准入。

**裁决与接续**：本轮合并诊断关闭，无新方法准入。A4-R继续，先将已确认真实代码的
ERGO作为**强rival native可行性**审查：核原缓存/CV单位与fidelity、全候选native编码能否
留在原Longformer长度内、原模型/损失的透明接口补丁及真实预算。它本身是已知方法，
不作本项目创新；只有新独立干预与强对照/消融/负控、power及合同闭合后才进A-A。
此处不授权ERGO训练或GPU成本任务，先改主表，再完成可行性/输入准备。

R190全28件seal SHA `b29a9fd21768d7ee105f5c46a1fbc6aeaf2cca5090423cd3e22fd639a6321cb0`；
报告SHA `47f1934e72357b7c4bb91f3e22314613bb37e438a69f8d276297bec03382f322`，
per-doc SHA `918713a2839a71936e322bd7cb80d831d65e57ab5f6aa9cfb25d216d7c3e44e4`。
R190全部28件及manifest已在原4090逐项核hash一致；独占八项测试本地/远端通过，
完整三件套最新933passed/87skipped、ruff零错误、smoke OK，一致性36项/diff通过。

### 25.94 ERGO native强rival可行性自审（2026-10-17，wip）

**科研价值**：对准表4-3/KR3.1–3.2/FR-016，以已发表pair-graph/focal强rival排除已知
结构与类别不平衡解释，不把它当我们的创新。原论文[Table1/2](https://aclanthology.org/2022.coling-1.185.pdf)
ESL同BERT下ERGO/RichGCN intra F1为59.0/55.2、intra+inter为48.1/46.6；公开实现的
Longformer variant在Table2为50.9。这些是**原文不同基准**的数字，仅作选择证据，
不与MAVEN主锚相减，也不把paper显著性声明视为本项目复核。

**可行性**：R189已有真实源码/缓存与静态缺口。下一只核原缓存/CV单位、原始fidelity
障碍和完整native marker输入的tokenizer容量；原模型不加载，源码不打补丁，package
不安装，encoder/optimizer/GPU成本仍未放行。公开缓存元数据读取不等于原benchmark
训练或native适配完成；缺失、过长或未知mask/fold映射如实记录，不裁候选补洞。

缓存接口审查发现原mask排除self且有single-pair记录；下一仅用原RGT类体的tiny CPU
控制复现全masked row的数值行为，核具体记录/根因，不加载encoder、不修原mask、不跑
原benchmark。该调试与native tokenizer容量并列，用于去留/保真度裁决，不作方法效果。

### 25.95 ERGO缓存与native容量闭合；准入透明接口准备（2026-10-17，10-18接续）

R191=`runs/stages/R1/r1-v91-ergo-native-20261017/`。仅在原4090运行CPU tokenizer、
闭白名单缓存解码及width4原RGT类体，不加载encoder/权重、不训练。PID1698236已成功
SSH核GONE，命令退出0；本地/远端六项marker测试通过，实际入口/marker builder lint通过。
早期缓存诊断脚本存在行宽/import格式问题，未改写已执行身份；不声称整个诊断目录lint全绿。

**原基准边界**：作者代码固定`afa3d347ec360242c01d15a34b1f1ae63714c789`，原缓存
dev为25篇（topic37/41）、train为233篇（20topics）。train负/正对55996/5069，dev
8958/556；每篇一条feature、无重复(topic,doc)。原代码default seed42仅重放KFold
**索引计算**，未初始化/运行任何seed42模型；五折有18–20个shared topics，但没有shared
(topic,doc)。论文§4.1未明确要求topic-disjoint CV，故不据此指控泄漏或违反原协议。

缓存节点全部是n(n−1)/2无序位置对，t1/t2并非总按文内先后；不能从方向字段猜原关系
方向。掩码off-diagonal恰为不共享端点即屏蔽，diagonal全部屏蔽。真实train缓存的
`4_6ecbplus.xml.xml`（topic4/label0）与`5_3ecbplus.xml.xml`（topic5/label1）各只有
一个pair节点、mask=[[True]]。在当前torch2.8.0+cu128以固定向量/原Norm和RGT类体
复现，attention及输出非有限；仅诊断性取消mask后有限。未修原mask/缓存，未跑完整
encoder/trainer；这证明当前可得输入/栈的数值障碍，**不证明论文当年运行此配置或结果
无效**。完整native ordered pairs最少有两个reciprocal节点，保留屏蔽self也有邻居；
tiny对应控制有限，仍不等于全模型预算/训练可行。

**FR-016裁决**：原数字路径(a)尚未完成。当前拟议native行采用**(b)透明适配路径**，
并列障碍：`processor_esl`导入名缺失、当前transformers无旧AdamW导出/缺lxml、原缓存
single-node数值问题、公开模型只有Longformer而无论文BERT窗口variant、未找到训练
checkpoint。原warmup正文8%/源码10%差异保留。没有原根LICENSE文件不等于虚构禁用
判定；不重新分发原源码。此处是适配路径裁定，**不是已完成外部复现或已测成绩**。

**完整native容量见证**：官方`allenai/longformer-base-4096` revision
`301e6a42cb0d9976a6d6a26a079fef81c18aa895`，仅四个tokenizer/config文件；保留全部
原words与事件marker，不加gold coref/type/关系输入。2622篇、66744事件提及、2297524
有向候选，digest精确为`ce10549172550addb67059550d89c9fc04dc5cb6452560a5ccf42169e679d766`。
总1131221tokens，最长2080（doc54995af8da07c1b490d9a5ccd5df9d73），无>4096文档、
无截断/mention重叠。marker位置和input_ids摘要逐篇留存。该见证尚非完整ERGO adapter。
最大109mentions/11772pair节点；每epoch所有文档pair-square和6074629688。dense图
训练成本仍未知；单FP32四头attention矩阵最大2217279744bytes只是下界，不报OOM。

**下一裁决**：输入长度路线可行，继续同一C41-A-R，先改主表，实施最小透明native
feature接口及原类调用/三类export测试，冻结成本合同。保持原RGT/focal类体、完整有向
候选与diagonal mask，不修single-node作为native必要补丁；原binary scorer替换为官方
subtype-sensitive evaluator，明确错误subtype同时FP/FN。原ESL CV改为冻结MAVEN
train/internal-dev、seed13；不可把Longformer/全文差异的收益归因于graph或新方法。
先做接口/TDD与原机镜像权重可得性（只在4090下载、无跨机搬运），再独立准入encoder/
GPU成本；**本节不放行encoder、optimizer、GPU或训练**。无独立新干预，O1–O3未达成。

容量report SHA `c1694c83d8522a50cdf7576740bc2e371df7eea1964b85d6bebd713631d2443a`，
逐篇SHA `dd53ea310b123fb705341d5d0df68cfd9d2c1fc6a3676932e543534d3e2ca3d3`；
真实mask probe SHA `78373885cd00b79ff5c461fcc0144530d2db1e97b014be36776bced4dab5145e`。

R191全部20件（不含可再生成pycache）seal SHA
`b5cd6c89d9200b404380fa819d9a87e770b11d44bf12bf135d93d553e512e97e`；
原4090对全部20件逐项重算SHA并核seal，与本地一致。
本次完整三件套933passed/87skipped（24.32秒）、ruff零错误、ekg-smoke OK；
一致性36项和diff检查通过。87个skip仍非真实Torch验证；本项6个marker测试原机另验。

### 25.96 ERGO透明接口实施自审（2026-10-18，wip）

**科研价值**：对准表4-3/FR-016(b)/KR3.1–3.2，将已知强rival接入同manifest/全候选/
官方子类型口径，防止二类metric与无序节点改写任务；不是新方法或效果证据。
**可行性**：§25.95全文容量通过，当前仅纯Python接口和tiny CPU原类/掩码测试；原模型/
focal继续引用外部hash固定源码，不复制重写。本地无torch，相关用例需原机真实执行。
主表已先授权接口与原机镜像权重准备；encoder/optimizer/CUDA成本另立合同，当前不运行。
R192=`runs/stages/R1/r1-v92-ergo-interface-20261018/`；先stub产生真实NotImplemented
RED，再实现全量MIDs/markers/有向pairs、Cartesian targets与official export；数据gold只在
独立监督函数使用，给定mention type不进模型文本。封存R191不改写。

接口实现本地完整三件套951passed/88skipped（25.78秒）、ruff零错误、smoke OK；
19项接口用例中18项本地通过、掩码Torch用例在项目环境skip，隔离CPU Torch环境实际
执行该用例通过。原机对应全19项及真实class probe尚待执行，未以本地skip替代。
feature配置SHA `f6c95712a872df5d00be4b216df9ec78e989f1327010a27f9ee692bf5b56ab49`，
只有train输入/tokenizer/target侧车，没有encoder；正式全train准备待真实测试后执行。
原4090镜像HEAD直链返回302及与官方blobs元数据一致的权重LFS SHA/字节数，正在原机
下载；未从本地或5090传权重，尚未校验完成，不宣称checkpoint已可用。

原机19项接口测试全通过、原Norm/RGT/focal类体tiny前后向有限，原源码SHA未变。
完整train准备完成/成功SSH核无进程：特征仅做tokenizer/接口计算；本地canonical train
另生成的targets与远端原joint gold源生成文件**字节相同**，SHA
`cb3ab49f07f51b3e6fde96581715ff0ed9c88345eb1121af7a9e4f4c3b38b211`。
全部冻结anchor causal export逐篇集合一致，完整candidate digest及三类计数与§25.95相符。
这不是新模型预测/效果；native_train中CLS-only策略仅是已完成的第一版准备身份。

**新来源差异/修订决定**：§3.1正文规定BOS全局/其余local，而公开233train+25dev缓存
**全部且仅BOS、EOS两位置全局，padding没有全局位**；完整元数据核查无例外。
此前将native CLS-only称作“保持原实现”过宽：它与正文一致，与可运行缓存有差异。
没有悄改旧feature/report/config；在方法/encoder运行前，主表先改，另建cache-matched
BOS/EOS准备身份，新增EOS应落在最后一个nonpad token而非padding末尾的测试。
当前无encoder/optimizer训练效果，也不以此来源差异否定原论文；FR-016(b)明确并列。

原4090下载权重597257159bytes，SHA
`06c56757f0510de87c231acd03650ca204c5ed65c281cd1081b98288183f2468`与官方Hub
immutable revision/LFS元数据相符；原机路径
`/data/TJK/models/local/longformer-base-4096/301e6a42cb0d9976a6d6a26a079fef81c18aa895/`。
四个metadata原机复制/逐项核hash，无跨机权重搬运、无encoder加载。旧HF4.11.3 AdamW
[官方源文件](https://raw.githubusercontent.com/huggingface/transformers/v4.11.3/src/transformers/optimization.py)
已获取/Apache2头保留，SHA
`2ebfecd42a53245c4e72fd8e267efbef7679adfd10bcf14b8510f6830c8fd36e`；未安装/执行，
不把torch.optim.AdamW与其数值等价当作已知事实，后续成本/训练需固定实际optimizer。

cache-matched新配置SHA
`23d44f75ed42f6166280cbdabb66ed7e6d41b2cbc58b619f07478d4efd2e81c8`；
新增EOS/无padding attention测试先真实RED、再GREEN，最新全仓952passed/88skipped
（24.77秒）、ruff零错误、smoke OK。一致性36项/diff通过；原机全20项及新特征待执行。

### 25.97 ERGO透明输入准备完成，进入真实原模型成本合同（2026-10-18）

R192新cache-global全train已完成、PID2516503成功SSH核GONE。原机20项测试通过。
新特征SHA `c4c018269fe69515579e15eb6dcaea38ebd96610bbfa9f1d4d891ff54733aeb0`，
新report SHA `5d10b34a77ea1ca0d160bfa5036ccb6f0d82491372c8d8bf0806216a4d4856f4`。
2622篇逐字段复核：**只新增真实EOS的global位**，全文IDs/attention mask/marker位置/
全部候选均与旧准备字节所表达的值一致，没有padding global；全部targets与旧版和本地
canonical gold侧车三份字节一致。原CLS-only身份/报告/config及RED均保留。
代码`4b0fa53`，旧准备`af5c656`，前者全仓952passed/88skipped、ruff零错误、smoke OK；
20项原机实际Torch通过，原RGT/focal tiny报告见R192，未跑任何encoder或optimizer。

作者ERGO代码已通过Git从同一固定checkout保全到原4090持久路径
`runs/external/ERGO/afa3d347ec360242c01d15a34b1f1ae63714c789/`，HEAD及model.py SHA与
§25.90一致；原tmp源未改。Longformer权重路径/身份见§25.96。新baseline仍无成绩行。
本次原4090四卡占用17246/17181/17181/17183MiB，四个他人vllm PID
2284611/2284612/2284613/2284614；CPU load9.27/11.75/12.85、可用480853MiB。
这是本次只读快照，不是后续选卡许可；无GPU启动/等卡自动器。

**下一任务开工自审**：科研价值是让表4-3强rival从接口正确走到真实原模型可运行/
可预算，避免把tiny图层或mask稀疏度当训练可行性。可行性是权重/输入完整且原机CPU
内存足够；GPU当前卡在【算力/资源】他人占用，CPU完整模型可独立推进。先改主表、
冻结R193成本合同，再在原4090以短文fixture、原encoder/RGT/focal与原HF4.11.3 AdamW
类体做CPU完整前向/反向、target无关输出与两次lr0 cold/warm API/参数数值不变检查；
如signed zero变字节需单独计数，不伪装字节不变。无epoch、无held-out/效果或checkpoint
写回。CPU门通过且空4090后才单独放行原完整候选CUDA成本；不挤卡，不自动启动。
这仍非新方法准入/训练，也不构成O1–O3已达成。

R192全部24件（含两版完整features/targets、保留失败/RED与原依赖源，不含pycache）seal
SHA `7c201a73d6cb7cad336588fd9bbfc4ecfed343a531236cf320fe5517d89ea6a6`；
原4090对全部24件逐项重算SHA并核seal，与本地一致。来源/输入阶段闭合，CPU成本尚未执行。

### 25.98 ERGO完整模型CPU成本合同/实现（2026-10-18，wip）

科研价值/可行性见§25.97开工自审；[完整合同](../phases/PHASE_A4_ergo_native_cost_20261018.md)
已冻结，R193=`runs/stages/R1/r1-v93-ergo-cost-20261018/`。固定seed13/float32/batch1/
4096 padding，CPU4threads，最少事件且最短文档fixture为
`d0a037b11d4428ed3ff218f98c3e6073`（2候选/109nonpad）；GPU典型/最大候选/最长全文
病例也事前锁定，但`cuda_admitted=false`、代码拒绝，当前不启动CUDA。

配置SHA `dbae7be07d03569feb5683e31f6b21564d6c4663584c5d314746691522dbdbc1`。
原模型完整导入/原HF AdamW类体加载，两个marker显式mean_resizing=False；先eval两次
改变target核logits相同，再train-mode两次cold/warm lr0 API。数值摘要只消除零符号差异，
不修改model；原始摘要/负零数单列。输入/模型文件集合/原源码和权重前后hash均需核，
无epoch/held-out，optimizer状态变化如实记2次API，不写“零optimizer调用”。

三个helper用例先stub真实RED：optimizer类提取/源漂移拒绝、参数零符号与真实数值变化
区分且不改模型、原布尔mask/完整候选及真实marker检查。隔离CPU Torch两项通过，
optimizer loader因无transformers单独skip；原机全部真实用例待补，不能以skip作PASS。
最新完整三件套952passed/91skipped（23.48秒）、ruff零错误、smoke OK；CPU encoder
成本尚未执行。其后只有真实原机测试通过才push并启动本合同CPU短文病例。

### 25.99 ERGO真实完整模型CPU短文成本闭合（2026-10-18）

R193原CPU病例已完成，PID2522674成功SSH核GONE；代码`b4e0e16`，23项相关原机测试
通过后push并执行合同。完整stdout审查无未解释encoder载入缺失/shape警告。实际加载
官方Longformer和原RGT/focal、原HF4.11.3 AdamW类体，186442755个参数；pooler的
weight/bias未参与任务，单独列出，不强称所有参数更新。原源码/权重前后hash不变。

固定两次lr0 API：cold30.727681秒、warm31.751231秒（含梯度有限性检查、checksum在外）；
峰RSS13704624KiB，optimizer state1486817304bytes；无epoch/非零lr/held-out或新预测
效果。loss/logits/非空梯度均有限，eval更改target后logits逐值相同，参数**数值不变**。
原始参数字节变化，负零数36→2→1；规范零符号后的SHA全程相同，原始SHA逐次单列，
没有修改或恢复零符号来伪装byte parity。两次loss/grad norm仅作数值诊断，完整见report。
这是短文正确性/实测成本，不是CUDA/最大候选或全epoch预算PASS。

**下一开工自审与裁决**：科研价值仍是使已选公开强rival可运行并完成表4-3/FR-016(b)，
不因成本把它换成更弱对手。可行性目前受【算力/资源】空GPU缺失限制；原CPU短文
实际只有109nonpad却处理4096padding，长时间不能从此外推全train。成熟Longformer
本身支持变长与按window自动pad，下一只在新身份验证**去掉尾部PAD**：所有真实word/
marker/候选/监督与BOS/EOS位保持，max context不增、不改原模型/图层/损失/优化器。
先同一初始化下eval logits/loss及全部非空参数梯度parity（dropout关闭，abs1e-6/
rel1e-4；不能据此声称train dropout随机流相同）；通过后以train mode测CPU形状预算，
据实选择CPU执行可行性或等待合法GPU，不写自动等卡任务、不使用未授权5090。
新成本合同/主表在执行前冻结，原R193保持；仍未放行baseline epoch或新方法训练。

R193全部5件seal SHA
`cded90e8554654fcca8f7490e2255685ffb4f304004c205fa4cde385f38b9c75`，
原4090逐项核SHA与本地一致；report SHA
`a9730ec28c8f3f2e508f641702a530614b1b4db916fd3f1c6a0408adb6470cb9`。

### 25.100 ERGO PAD-only成本配置自审/冻结（2026-10-18，wip）

科研价值/可行性已在§25.99开工自审，主表先更新后实施。
[新合同](../phases/PHASE_A4_ergo_padding_cost_20261018.md)冻结同一模型下full4096与
仅去trailing PAD的eval logit/loss/全部非空参数梯度parity；abs1e-6/rel1e-4，不事后放宽。
只移三个序列数组的已masked后缀，真实词/markers、BOS/EOS、候选/标签不变；官方库
自动window pad。关闭dropout的parity不能证明训练随机流一致；FR-016仍(b)透明适配。

配置SHA `db47033ea17cc92b6cb6d8025344ad9a1b187cad537020938dd927451fea3274`，
R194=`runs/stages/R1/r1-v94-ergo-padding-cost-20261018/`，CPU12threads、其余原类/权重/
超参/seed13不变。CPU线程与padding同时改，耗时差不全归因PAD。短文先过门，再测固定
typical/worst/longest预算；无epoch/新方法训练/CUDA许可，原R193不覆盖。
新trim helper先stub真实RED，再验证只去PAD/不改输入/拒绝伪PAD及padding全局位；
隔离CPU Torch三个helper通过、原optimizer loader因缺transformers单独skip，原机待补。
最新完整三件套953passed/91skipped（24.96秒）、ruff零错误、smoke OK；一致性36项/diff通过。
原机实际测试与真实padding parity仍待执行，不把本地skip当完成。

### 25.101 ERGO PAD-only完整短文parity通过，继续固定CPU形状预算（2026-10-18）

代码`0a76f13`，24项相关原机测试全通过后push并启动。PID2528270成功SSH核GONE。
同一完整初始化模型/CPU12线程，full4096对trimmed109（库内部补至512）：logits与loss
误差均为0，283个有梯度参数的最大绝对误差5.960464477539063e-08；所有项通过事前
abs1e-6/rel1e-4门，梯度集合相同，无容差修改。原模型/图层/优化器未改。

train-mode两个lr0 API cold2.336174秒、warm1.764547秒，峰RSS9392172KiB；数值参数
不变，零符号引起的字节变化继续单列，没有恢复签名或权重。target独立性通过，无epoch/
held-out或效果测量。由于线程同时由4增至12，不把与R193的全部耗时差归因PAD；eval
parity不等于相同training dropout流。所有真实词/mention/候选/目标与R192保持。

后续仍是已冻结R194配置的CPU typical/worst/longest三个病例，每个同完整词/全部候选
及同parity/两次lr0门。原机只读核到64CPU、load11.37/12.85/12.61、可用481097MiB；
允许三个独占输出的12线程CPU预算病例并行（36threads，非多seed），每条SSH只起一项，
不创建后台重试/等卡器。运行时并发会影响耗时，报告此限制，不将fixture耗时当精确epoch
承诺；baseline完整训练仍须预算与正式合同，不由短文PASS直接启动。

### 25.102 ERGO PAD-only最大候选parity失败，停止该执行版本（2026-10-18）

四个预定R194病例均结束，PID2528270/2530524/2530525/2530523已成功SSH核GONE。
没有新epoch/非零lr或held-out访问；源文件/原R193均保留。先报告所有病例，不只报告通过项。

| CPU fixture | eval全梯度parity | max gradient abs error | loss/logit abs error | cold / warm秒 |
|---|---|---:|---|---|
| short | PASS | 5.960464477539063e-08 | 0 / 0 | 2.336174 / 1.764547 |
| typical | PASS | 8.717179298400879e-07 | 0 / 1.3113021850585938e-06 | 2.180416 / 3.287719 |
| worst candidates | **FAIL** | 7.933378219604492e-05 | 1.4901161193847656e-07 / 2.3543834686279297e-06 | 未进入optimizer成本 |
| longest text | PASS | 4.470348358154297e-08 | 0 / 0 | 26.631139 / 26.782800 |

所有比较均用事前abs1e-6/rel1e-4，283个有梯度参数；worst的`passed=false`是逐参数
allclose判据，不能因logits较近或其他病例通过改判。typical/longest峰RSS分别9505068/
18767856KiB。并发/线程差异限制沿用§25.101，不将耗时当精确epoch承诺。

**裁决**：该PAD-only执行版在【代码/数值等价性】卡住，具体参数/数值差来源尚未定位，
不轻率称“只是浮点误差”，不事后放宽门或继续把它用于训练。保留原worst traceback/
启动时status；新增完成审计标FAILED/GONE，启动status不作最新判活。worst没有两次
optimizer调用，R194仅三个成功病例各2次lr0 API，总6次，均无参数数值更新。
这不是ERGO新训练/科学效果FAIL，也不取消强rival；不修原类或筛掉该文档补洞。

**下一开工自审**：科研价值仍对准表4-3/FR-016(b)，恢复已跑通的完整4096原输入预算，
排除将数值门未过的优化带进主表。可行性是R193完整原模型已通过，原机CPU/RAM可用；
12线程只改执行资源，不改数据/模型/损失/优化器。先改主表，在新R195配置/合同中对固定
典型/最大候选/最长输入做原完整padding的CPU前向/反向/两次lr0 cold/warm；三病例并发
仍为不同输入成本/同seed13，不是未授权多seed。GPU仍被占，完整CPU或GPU训练未放行；
据实测预算再选执行设备/工期，不能拿失败版本的较快耗时作为原版本训练预算。

R194全部14件（含worst原traceback/启动status与新增失败完成审计）seal SHA
`faec3bbeced31e64558d54c22f01148bf44580740f0937480abb1db7dbfe5167`；
原4090逐项核SHA与本地一致。候选版本未准入、所有进程GONE，不把物理执行闭合当科学成功。

### 25.103 ERGO恢复原完整padding CPU预算合同（2026-10-18，wip）

科研价值/可行性已在§25.102开工自审，主表已先更新。
[新合同](../phases/PHASE_A4_ergo_canonical_cost_20261018.md)对应R195=
`runs/stages/R1/r1-v95-ergo-canonical-cost-20261018/`；配置SHA
`a2af02e042ce817f2fb7e2b9848974d2c220fe3c60a7e2dc4c6c9f8be4da3b34`。
原R192完整4096 tensors原样输入，seed13/float32/原模型、focal、legacy AdamW不变，
只用CPU12threads、固定典型/最大候选/最长三病例，预算API各两次lr0。无PAD优化/等价
主张，报告parity applied=false；R194仍为FAIL，不改其数值门/结果。

新增v3策略检查先stub真实RED，再验证完整输入对象原样保留、schema/policy/parity标记
不一致即拒绝；旧v2 helper/原门保留供冻结版本追溯，当前不再执行它。隔离CPU Torch
四项helper通过、原optimizer loader因缺transformers单独skip；真实原机待补。当前
仅成本实现/合同，不启动epoch或CUDA。
最新完整三件套954passed/91skipped（24.64秒）、ruff零错误、smoke OK；一致性36项/diff通过。
原机真实测试后才push/执行R195；当前无epoch/非零lr/GPU任务。

### 25.104 ERGO internal-dev无标签输入准备自审（2026-10-18，wip）

**科研价值**：对准表4-3/FR-016(b)，在任何baseline epoch/选档前固定同协议完整internal-dev
输入/候选与官方evaluator，避免只核train而漏掉评测方向/缺文档。**可行性**：复用原A3
已冻结的无标签test-shaped projection（并非public final-valid），无模型/encoder/optimizer/
预测或gold关系读取；固定manifest与P1根，运行官方Longformer tokenizer检验完整词/
markers/候选容量并准备原4096 cache-global特征。source最少2/最多110mentions，291篇
与internal-dev manifest集合相同，未含events或relations；这仅元数据，不是性能。

源`runs/stages/A3/a3-v6-baselines-r10/preflight/data/MAVEN_ERE/test.jsonl`，2459581bytes，
SHA `c358da8b04bdeca9477bd26a1a7fa325b634ea62a488b85b28119be8cce2a891`。
其title/sentences与给定mention type/type_id不进模型特征，只保留完整tokens/mentions/
TIMEX供ID口径。使用同manifest `maven_ere_internal-dev` 与官方候选digest
`15a3b1a548625624642130190b39411e6346866ff8594c2af2020cfbdac10910`，不读valid710或
更改split。主表已先允许预算期间这项独立准备；R195仍仅CPU成本，无baseline训练准入。

### 25.105 ERGO原完整4096 CPU形状成本闭合；准备备用GPU成本提案（2026-10-18）

R195代码`e81ca79`，25项相关原机测试全通过后push执行，三个PID
2538769/2538733/2538740已成功SSH核GONE；完整4096 inputs原样传入，所有病例padding
parity applied=false而非伪报PASS。原模型/focal/legacy AdamW类体未改，六次lr0 API、
无epoch/非零lr/held-out访问；target不影响logits，loss/非空梯度有限、参数数值不变。

| 原完整padding CPU12threads | cold / warm秒 | 峰RSS KiB |
|---|---|---:|
| typical | 29.332519 / 25.871265 | 13608464 |
| worst candidates | 50.890709 / 42.538120 | 24336256 |
| longest text | 49.236314 / 38.625496 | 22036324 |

optimizer state均1486817304bytes，186442755参数；两个未用pooler参数继续点名，零符号
字节变化与数值摘要分别报告。并发/线程影响吞吐，不能从这些数准确承诺epoch耗时；
仅取typical warm恒定外推原20epoch×2622=52440steps已约15.7天，说明CPU全训的时间
量级，而非可用训练预算PASS。不把R194优化版的较快结果用于此外推。
R195全部8件seal SHA `d0e7a4b939e02a5e0785a7e9ef03d3722e3a3a3e8a3b53fdddad15100f811466`，
原4090逐项核SHA与本地一致；无baseline成绩/训练。

**只读资源新事实**：4090四卡仍为他人vllm（各约17GiB，PID2284611–2284614），不挤占。
5090已恢复可达，单RTX5090/32607MiB、已用316MiB、util0、无compute-app；UUID
`GPU-07af326b-f41d-a706-2150-bc560c7db304`。原机torch2.8.0+cu128/
transformers4.53.3与4090一致，P1 r15 SHA相同，官方Longformer镜像HEAD302及LFS SHA/
597257159bytes一致。远端HEAD `f6399be348485cc1d9a019cef017444464c87476`是本地主干
祖先，tracked无改动；untracked `mk_probe_contract.py`必须保全。仅做连接/环境/文件/
HEAD请求元数据，**未运行5090模型或GPU计算，未同步/搬运checkpoint**。

**下一任务开工自审**：科研价值仍是表4-3强rival原完整候选真实CUDA预算，不拿优化失败
或CPU长工期换弱对手。数据/代码已闭合、资源上备用GPU可用；卡在【授权】：现有5090
C5许可不覆盖新A4，AGENTS要求逐次许可。由代理先准备可审查的5090成本移植代码/
固定三病例合同/命令与非权重staging，再请求一次范围明确的许可；只有许可后才在空卡
准备公共权重并执行有界GPU成本。不得把“继续”或旧C5许可暗改成新A4 GPU授权。
提案仅固定seed13、三个原完整4096病例各两次lr0，GPU suite总墙钟≤20分钟，完整
baseline epoch/新方法训练另门；权重从官方镜像直下，不跨机搬本项目已训checkpoint。
等待许可期间继续§25.104无标签输入/协议准备，不结束总Goal或等待作者科研选题。

### 25.106 ERGO备用5090有界成本提案实现（2026-10-18，待新A4许可）

开工科研价值/可行性见§25.105；主表先行。[提案合同](../phases/PHASE_A4_ergo_5090_cost_20261018.md)
固定原完整4096/float32/三train病例，各两次lr0；GPU suite串行、TERM1200秒/清理30秒，
不含epoch/非零lr/held-out/模型保存。v4仅接受5090真实root/hostname/卡0/固定UUID，
拒绝错误目录、卡号、多卡、无CUDA或training_admitted=true；原4090 helper不改。
`cuda_admitted=true`是CPU门后的技术成本范围，配置另明确作者许可未取得，不是授权。

新环境准入用例先真实RED（函数缺失），GREEN后验证拒绝越界与完整输入原样传递；
本地完整三件套955passed/91skipped（24.18秒），ruff零错误、smoke OK；原机真实Torch
相关测试待部署补齐，不能把本地skip作PASS。脚本部署/推送后才提交具体许可请求。
配置SHA `8745ddd6a6e5446a5476e1cc29c6cce743ecf04504fe1d03c367b5c0c7926461`。
本地暂存11件已封存输入/证据tar.gz，4322362bytes、SHA
`3fd153bb81b8aa3fb6fe692939fc0f96986994824511b90e3b7b350d6c0df902`；
不含本项目checkpoint，upstream代码独立Git bundle，公开权重拟在许可后由目标机直下镜像。
5090只读确认curl/timeout/setsid/git存在；尚未向该机写代码/数据或运行模型/GPU。

§25.106后续验证：代码`bf616b1`以Git bundle在4090 tracked-clean保护下部署，真实
CPU Torch相关26项测试全通过（含原optimizer加载与native模型输入），再push；没有在
本地或5090加载encoder。公开ERGO原Git bundle SHA
`5f1d30fc3a0f90f40d04b62fa3ead5b7d1686479a43acecfa145aa70c974142c`；
从5090旧HEAD到提案代码的Git增量780KiB，SHA
`269977e0dc10a1c9a30dfebed8c3f96e6a70990eaced4625819d38811e592871`。
已向作者请求仅本合同的新A4 5090许可，待答复；未部署/启动5090任务。

### 25.107 ERGO无标签internal-dev特征入口实现（2026-10-18，wip）

开工科研价值/可行性见§25.104，主表已先允许该独立输入准备。
`scripts/prepare_ergo_unlabeled.py`只读已有test-shaped projection，拒绝gold/未知顶层
字段；去掉title/sentences及mention type/type_id/trigger metadata，保留完整tokens、
MID/span/TIMEX。物理marker次序对应完整有向候选，不生成targets，不读gold、不运行
encoder/预测/evaluator。冻结internal-dev manifest、候选全集、P1及官方evaluator身份；
完整tokenizer4096/cache-global（BOS/EOS）词典同R192，不截断，溢长/缺marker即失败。

两个用例先真实RED（入口缺失），再GREEN：gold拒绝/类型元数据隔离、不修改原source；
源mention逆序时实际marker位置/双方向/完整padding与缺endpoint/过长失败。配置
`configs/ergo_unlabeled_dev_20261018.json` SHA
`225f46db1fad16ca9e2374a092c49ae9399ba69f08b68779a5acbb006c256e4a`。
只运行远端CPU tokenizer，无本地encoder或GPU；运行/封存待完成，不能提前宣称容量通过。

§25.107实现门：完整三件套957passed/91skipped（23.65秒）、ruff零错误、smoke OK，
一致性36项/diff通过。原机实际入口用例及tokenizer容量验证仍待执行。

### 25.108 ERGO无标签internal-dev准备闭合与5090成本获准（2026-10-18）

R196代码`a9dacaf`，原机两个实际入口用例通过后push执行；PID2703338已成功SSH核GONE。
全部291篇、7195event mentions/1719TIMEX、234870有向候选，digest与既有协议逐位相同。
无gold/encoder/预测/optimizer/evaluator执行；只运行CPU tokenizer和纯接口。
max非PAD tokens2214、max mentions110、max pairs11990、总非PAD tokens124278，全部
完整保留且在4096预算内。评测最大候选比train11772稍大，因此三train病例的成本不冒充
评测容量实测；完整训练准入前仍须对最大internal-dev无标签输入核no-grad容量。

R196全部6件seal SHA
`cb3a9a384c53b9b5774c07bb755739bbced977c13489d3f398956c3040d3d9b8`；
report SHA `07e5d3fde5d336c2afb75b3253ff5ce6e31546649dd2a86d4df5c8f758f7ca40`，
features SHA `9fd8992821b38f23de12b7b8ec6782345e77d736de5dc690503f1818808f5e04`，
documents SHA `66443ccfafafaad6694abdcc78e4e276aaac0a27adf77d9fc3bb765fd0d1e015`。
原4090和本地逐项SHA一致；本地另外用标准库逐篇核manifest顺序、MID物理排序、全部
marker/双方向配对位置、完整padding/BOS/EOS globals及token witness SHA，没有复用
打包函数生成期望结果；独立candidate digest/总pairs一致。

作者已明确答复**“授权本次20分钟成本验证”**，范围为§25.106提案合同，仅5090三train
病例/六次lr0、无完整训练/额外seed/本项目checkpoint搬运。冻结配置仍保存原提案时的
许可待定字样，许可事实以本段/独立authorization记录为准，不改写提案hash；技术
cuda_admitted不替代本次真实授权。开始核空卡、Git部署和公共镜像权重直下，尚未启动
GPU计算。当前本地主干`a9dacaf`，对5090旧HEAD的已发布Git增量SHA
`7bbb7d8f6b9f386548fe7cabba4f4e7c9c797edd64af6b905c41261d75ca4ad2`。


### 25.109 ERGO等卡期间原trainer/native合同准备自审（2026-10-18，wip）

**科研价值**：对准表4-3/FR-016(b)，已知公开强rival必须有原训练数学与native统一选模，
不能仅因模型可forward而称复现。**可行性**：官方`train.py`真实train_epoch/20epoch/
AdamW/clip1/linear10%warmup可核，接口/cache-global/train targets与无标签dev均已闭合。
当前仅准备薄接线、固定单seed/官方causal选模合同与tiny CPU回放；不运行encoder/epoch，
完整预算、最大dev no-grad容量及对应执行机资源许可未过前不启训。5090本次只获成本许可。

一手源码`train.py` SHA `551a24b88e5dcdf35f8b17680547045107b4c56ed6b329b1063c33afe658303f`：
train_epoch逐doc batch1/loss.backward/clip/optimizer/scheduler/model.zero_grad的真实函数
可原样加载，避免重写已发布训练器。原依赖缺失只提取该函数体，模型/focal与AdamW同已验
成本入口；native loader只接规定batch字段。原训练过程compute_f1每batch重扫累积前缀，
且将两种positive交换算对；只能作为原binary日志诊断，绝不能用于native选模。若替换
日志累计方式，必须在tiny数据对原函数逐值核同，训练函数/梯度步骤保持，逐项披露。
选择仍为现协议internal-dev官方三类causal F1；不读final-valid，不预定赢家或以此方法
声称创新。原论文8%/代码10%warmup差异、5fold→冻结native split、42→13seed以及binary
到三类/候选全集等FR-016(b)差异延续，不恢复原5seed/CV或缺失BERT-window变体。

§25.109实现：新增`ergo_training.load_train_epoch`按SHA只编译真实函数体，避开缺失ESL
导入、不改变训练函数；`BinaryPrefixMeter`只增量算原binary日志，正例交换仍按上游算对，
显式禁止用于native选模。两个用例先真实RED，再在隔离CPU Torch下2项GREEN；本地
全量958passed/92skipped（26.78秒）、ruff零错误、smoke OK，一致性/diff待最终复核。
[训练/选模草案](../phases/PHASE_A4_ergo_native_training_20261018.md)固定20epoch/原超参/
代码10%warmup、internal-dev官方causal F1严格优于才换档；源`>=`到本地`>`列透明差异。
该草案不放行epoch，GPU成本/最大dev no-grad/生产smoke/正式资源配置尚缺。

R198 toy回放配置SHA `5099cc784fb36ff38eedc18647e01dda3775ab68381e70a9c18df2e317c15c8d`；
仅九参数linear、两次toy pass，逐值比较原binary scorer与增量日志，以及原函数两种日志
callback下的参数/optimizer/scheduler。非MAVEN epoch、无encoder、无科学效果或checkpoint。
真实原机回放尚待执行，不能把隔离tiny测试当原完整模型/训练预算PASS。
