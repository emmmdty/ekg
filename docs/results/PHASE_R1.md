# Phase R1 · 方法设计准入审计

> 更新于 **2026-09-05**。本页只记录已实测的 R1 数字与审计结论。R1 仍是
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
- `status.json`：`24c2aac4ff31bba5997461b24e7a70c223d101c2369514b9c3b25963e887af07`。

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

只读取得并冻结五个官方仓库：

| 仓库 | commit | tree | 根 LICENSE |
|---|---|---|---|
| CorefPrompt | `47c60c04…3225` | `3fdc3010…b594` | 未发现 |
| MAVEN-FACT | `67544719…6847` | `e38f85c7…d184` | 未发现 |
| ModaFact | `ca8dea62…3867` | `78408509…be11` | 未发现 |
| TextEE | `567baa9b…5dd3` | `4f0fe960…7dd` | Apache-2.0 |
| OmniEvent | `ec72e727…cbac` | `35fb4c92…1a3b` | MIT |

- Ch1：CorefPrompt 官方预处理给出一条不读 cluster gold 的 mention-local 路线：OmniEvent EAE 只收句子、
  trigger 和 offset，再用公开固定表把 20 个角色归为 participant/place。但官方 EAE checkpoint 链接在审计日
  返回 `Link does not exist`，两台 GPU 服务器均无缓存。TextEE 的 RAMS/WikiEvents 路径分别覆盖 139/65 与
  50/59 个 event-type/role，但 PAIE/TagPrime 强依赖源 ontology prompt/map，仓库又无 checkpoint；直接套
  MAVEN event type 会成为新的未经验证 adapter，不能冒充官方 baseline。RESIJ 未取得官方代码；identity
  baseline/input 门仍 `blocked`。
- Ch2：official joint 可运行，但 2025 two-stage ERE、RESIJ、TacoERE 未取得官方实现，KnowQA 作者 URL
  当前不可得且是 sampled/gold-argument setting；relation baseline 门 `blocked`。
- Ch3：MAVEN-FACT 官方代码可得，但原 trainer 每 epoch 用 `test_data` 选 best、best checkpoint 保存被注释，且
  `RawBert` 调用签名不一致；本轮以透明 protocol patch 完成了泄漏隔离的 RoBERTa+CLS / DMRoBERTa 五折
  OOF。ModaFact 是意大利语 mT5-XXL 的不同任务，只作结构化对照。baseline 与 power blocker 已解除，但
  proposed 方法仍须通过 T022、T023、T024。

## 5. 当前方法裁决

- Ch1 草案改为 **predicted mention-local role posterior + missingness-aware uncertainty gate**；禁止使用
  MAVEN-ARG cluster gold。功效通过，但 baseline/input closure 未过。
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
