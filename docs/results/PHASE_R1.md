# Phase R1 · 方法设计准入审计

> 更新于 **2026-09-04**。本页只记录已实测的 R1 数字与审计结论。R1 仍是
> `preparation_partial_blocked`，没有方法获得 GPU pilot 准入。

## 1. 产物与代码身份

- 根目录：`runs/stages/R1/r1-v61-20260904/`；
- 代码提交：`8e3eb7a57ef5f6a0c6dbb03d97e7d6cbef468ac8`；
- P1 绑定：r15 / `1e31a9acef39261f776f7ed4069fd73f4531e8d12b55779bfc0fbd74c67f9655`；
- `id_coverage.json`：`ca481ecf3b899cacf553f258992f6603f8fa417a97cd25ee94176e3f313bb2e6`；
- `power_analysis.json`：`1e1ed4b954902ea1a201cc3ba6a6c7eee5e5439ca93da60d57abed924bf67ca8`；
- `literature_matrix.json`：`65536445d1f2764dbcab5bf27c4771ebc3f4a0fb3eb47d7bc1613721e89fe1fc`；
- `design_briefs.json`：`bd300111f3f63472a763a0d2dc7020f8c001279bf6471364474387624c4a754f`；
- `protocol/degree_requirements.json`：
  `ceeb581bc1ff2c22ea0dd94811c892d0c91a4e4bca8c3c7aedfd4c5f6f2da47e`。

代码门：481 passed / 24 expected skips，ruff 0，`ekg-smoke` OK。

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
| Ch2 | A3.6 handoff | — | — | **BLOCKED**：不得用中途曲线代替 |
| Ch3 | RoBERTa+CLS / macro-F1 .545765 | +.030 | 纠正 5 个 PS−/Uu 错例，Δ 中位数 +.059213，power .99 | **UNDERPOWERED** |

Ch3 在 3 个纠正错例、Δ 中位数 +.0370 时 power 仍为 0；检测门在约 +.059 才打开。因此不能在单一
internal-dev 上把 +.03 左右差异解释为胜出。合法补强是**预先冻结**保留 PS−/Uu 支持的 repeated splits 或
cross-validation；FactBank/UW 标签空间不同，只能作为单列外部有效性表。

## 4. 文献/代码可运行性

只读取得并冻结三个官方仓库：

| 仓库 | commit | tree | 根 LICENSE |
|---|---|---|---|
| CorefPrompt | `47c60c04…3225` | `3fdc3010…b594` | 未发现 |
| MAVEN-FACT | `67544719…6847` | `e38f85c7…d184` | 未发现 |
| ModaFact | `ca8dea62…3867` | `78408509…be11` | 未发现 |

- Ch1：CorefPrompt 的代码闭环是 licensed TAC KBP + Longformer/RoBERTa-large + OmniEvent arguments，不能直接
  记作 MAVEN-ERE 同协议对手；RESIJ 未取得官方代码；identity baseline 门 `blocked`。
- Ch2：official joint 可运行，但 2025 two-stage ERE、RESIJ、TacoERE 未取得官方实现，KnowQA 作者 URL
  当前不可得且是 sampled/gold-argument setting；relation baseline 门 `blocked`。
- Ch3：MAVEN-FACT 官方代码可得，但 trainer 每 epoch 用 `test_data` 选 best、best checkpoint 保存被注释，且
  `RawBert` 调用签名不一致；需要透明 protocol patch。ModaFact 是意大利语 mT5-XXL 的不同任务，只作结构化
  对照。factuality baseline 工程可继续，但不因此放行 proposed 方法。

## 5. 当前方法裁决

- Ch1 草案改为 **predicted mention-local role posterior + missingness-aware uncertainty gate**；禁止使用
  MAVEN-ARG cluster gold。功效通过，但 baseline/input closure 未过。
- Ch2 草案避开已失败的 retriever/weighting 家族，改查 **full-candidate counterfactual evidence
  sufficiency/necessity**；必须等 A3 handoff 和 error profile 后再决定是否成立。
- Ch3 草案改为 **certainty/polarity factorization + cue-conditioned residual**；它不把“找准 evidence span”
  当主要贡献。先解决 repeated-split 功效，再谈 GPU pilot。

三者均未获 promotion；5090/4090 的空闲本身不能替代 R1 准入证据。
