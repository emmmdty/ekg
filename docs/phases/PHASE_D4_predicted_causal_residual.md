# PHASE D4 — predicted-causal uncertainty-gated residual 的事件事实性检测

> **FROZEN（2026-09-22，C-26）。** 本文在**任何方法结果存在之前**冻结三臂、中介、护栏、推断与
> 停止条件。上游输入门 C-25R3F 已于同日通过（`docs/results/PHASE_R1.md` §25.13），其 map、
> 训练权重、决策规则与五份 sidecar 自此**不可再改**。
> 旧 typed-cue 家族（[`PHASE_D4_typed_cue_factuality.md`](PHASE_D4_typed_cue_factuality.md)）已封存，
> 本文是**另一个机制家族**，不得混表、不得复用其臂名或诊断。
> 本文冻结后不因方法结果修改；要改必须先改 [`../EXPERIMENT_PLAN.md`](../EXPERIMENT_PLAN.md) §4 主表
> 并记录理由，且改动只能发生在**看到方法结果之前**。

## Goal

检验：**在不读取任何 gold 关系、gold factuality 或 final-valid 反馈的部署条件下，泄漏隔离的
predicted causal/precondition posterior 经显式 uncertainty gate 形成的 residual，能否实质提高
MAVEN-FACT 五类事件事实性检测，并同时改善两项按 CAUSE/PRECONDITION 语义事前定义的一致性违反。**

主分数上升但中介不成立时，只能写“预测有改进”，**不得**写“机制成立”。

Specification coverage：RS-003、FR-001、FR-003–FR-007、FR-009–FR-016、QR-001–QR-004、QR-006–QR-007、
SC-001–SC-002、SC-006–SC-009。

## Inputs（全部已冻结，本阶段只读）

- P1 信任根：`runs/stages/P1/p1-v6-20260904-r15/protocol.json`，SHA-256
  `1e31a9acef39261f776f7ed4069fd73f4531e8d12b55779bfc0fbd74c67f9655`；
- 五折切分：`runs/stages/R1/r1-v61-20260904/factuality_cv/factuality_cv.json`，SHA-256
  `3a724cf77a2a34bb11f40d225725504b176e4d62e916c5b34c92f9d10a52c5c4`；15 个 manifest 的 SHA-256 由
  cross-fit plan 逐项绑定；
- cross-fit plan：`runs/stages/R1/r1-v62-20260920/d4_crossfit_plan.json`，schema
  `r1-v62-d4-crossfit-plan-v2`，backbone pin `71be7419a60dcce0fc276654c8f9213b41f8def71a0c3465d7fed2352c961ea9`
  （RoBERTa-base 内容寻址目录）；
- MAVEN-ERE train：SHA-256 `6a5519fe7c30448690adb13d49217c50d474fc57480eae10aecb29df7eb638b7`；
  MAVEN-FACT train：SHA-256 `190522b44f0702af030161924d7cb94c4a06bd5d6e2b40d79f8f1eaa5886bab7`；
- **结构输入 = 五份 immutable natural-posterior sidecar**
  `runs/stages/R1/r1-v62-20260920/relation_crossfit/fold-{k}/dirichlet_causal_posteriors.jsonl`：

  | fold | sidecar SHA-256 | CAUSE weight | NONE weight | PRECONDITION weight |
  |---:|---|---:|---:|---:|
  | 1 | `bb3a316154617139f6bf2e7a923226d5b0826f2747a223c3b8240b378fe6126c` | 7.695400460634976 | 0.5834365142779171 | 4.694399765188356 |
  | 2 | `b65016994c2084396ccf67dc8740237f5320fc4ca6d6351750f2a76d5a8f6a1b` | 7.615657047491473 | 0.5834826118751584 | 4.688788109565318 |
  | 3 | `2e74ab450de6ff9a6c4abcdd27380c7fb368804dc1cd9052e72d5661d8540020` | 7.681701310058411 | 0.5835678778070893 | 4.630444124194695 |
  | 4 | `b78d804fd505abf699efd310bf686590a5dd869030dee53d04b75c3768147971` | 7.665880048785466 | 0.583584770263806  | 4.625489541711555 |
  | 5 | `4bc0daaaeb47ab877e2b3339a49fe32ec59a267920d3d47d200c8a7f8686d671` | 7.7733050341731715 | 0.5835799409499864 | 4.604920227443102 |

- 输入门报告：`.../relation_crossfit/dirichlet_quality_report.json`，SHA-256
  `fea7d3edf3da85a734d805d3f092db146d4010cd0cecec0cfb9e58e5e51b54d4`，`quality_gate_passed`；
- 主锚 OOF 标签：`cls_oof_labels.json`，SHA-256
  `f375e8a58c21c22cc0cc4b7d968df4c75fe1458f083814859bb66d7d1f4e9737`（macro-F1 `.553995`）；
  DMRoBERTa OOF 为第二条 accepted baseline（`.545603`）。

⛔ 禁止进入模型的输入：gold CAUSE/PRECONDITION 边、gold factuality 标签、final-valid 的任何反馈、
MAVEN-ARG 论元。gold 关系**只**用于计算 §Mediators 的两项中介，且在评测阶段读取。

## 边的构造（冻结，不得再调）

1. 每折只用**该折自己的** sidecar；候选全集与顺序必须与 sidecar 逐行一致，任何漂移 fail-fast；
2. 硬判定固定为 `argmax_k w_k p_k`，`w` 取上表冻结的训练权重；判为 `NONE` 即无边；
   判为 `CAUSE` / `PRECONDITION` 即建一条**有向**该子类型边；
3. 边置信度固定为该边被判子类型的自然后验 `p_k*(e) ∈ (0,1)`，**不做任何 threshold、temperature、
   top-k 或校正强度的扫描**；
4. uncertainty gate 的唯一约定是：`residual(v) = Σ_{e→v} p_k*(e) · m(e)`，因此
   **无边时 residual 恒为 0，置信度趋 0 时 residual 趋 0**。`m(e)` 的参数化由 C-27 实现，
   但必须保证这条零极限在数值上严格成立（单测覆盖）。

## Arms（恰好三臂，只差一个注册变量）

| 臂 | 定义 | 与 full 的唯一差异 |
|---|---|---|
| **full** | 冻结 base + 上述 uncertainty-gated causal residual | — |
| **base** | 不改动的 full-context base head（RoBERTa + CLS 口径），不接任何结构信息 | 去掉 residual 通路 |
| **rewired** | 负控：在**同一文档内**用 **double-edge swap**（`a->b` + `c->d` → `a->d` + `c->b`，不产生自环与重复对才接受，预算 10×\|E\|）重连端点，严格保持每个节点的**入度、出度、边方向**，随后整体置换 **(子类型, 置信度)** 多重集 | 只把真实端点换成保结构的随机端点 |

三臂的 encoder、mention 全集、优化器步数、batch/预算、seed（13）、评测器与聚合必须**逐位一致**；
⚠️ **打包规则的执行修正（2026-09-22，在 pooled 判定之前）**：批次按「取离 mention 预算最近的边界」
切，不是「累加到 ≥预算才切」。后者在平均 25.41 mention 的文档上实际跑成 48.8 mention / 910 步每
epoch，而冻结锚是 32 / 1,387；同一 lr 下少三分之一的步数会整体压低三条曲线，**而绝对门是对着锚定
的**。修正后是 35.6 / 1,248。G-18 用的是修正前的规则，**其数字照样如实报**；G-18b 是同一周期的
执行修复，**不动任何门常数、阈值、backbone 或 seed**。依据与算术见 `../results/PHASE_R1.md` §25.19。

rewiring 的随机源固定为 `SHA256("d4-v62-rewire|{fold}|{doc_id}")`，与 seed 无关，可独立重算。
⚠️ **负控的混合上限已实测（fold 1 全 583 篇 / 22,839 条边，在任何方法结果之前）**：
交换预算 10×\|E\| 时 **40.53%** 的边保持同一 `(head, tail, subtype)`，预算抬到 50× / 200× 也只到
**40.98% / 41.27%** ⇒ **链已经混匀，这 ~41% 是度序列本身逼出来的，不是预算不够**。因此
`rewired` 是一个**保守**负控：它最多只能打散约 59% 的边（且那 41% 里多数边的置信度已被置换，
所以 41% 是「完全未变」的上界）。**读 `full > rewired` 时必须带上这条**——不显著也可能是因为
控制臂保留了过多真实结构。预算固定为 10×\|E\|，不因结果调整。

oracle（gold 边）**不设臂**；若为诊断而跑，只能写进结果页的 non-deployable 行，不进入任何胜出门。

## Mediators（project-defined，非 MAVEN-FACT 论文指标）

在 gold-expanded relation pairs 上逐子类型统计：

- **分子**：`target` 被预测为正发生（`CT+` 或 `PS+`）而其 `source` 被预测为负发生（`CT-` 或 `PS-`）
  的 pair 数，按边子类型分别记为 `CAUSE violation` / `PRECONDITION violation`；
- **分母**：该子类型下**两端预测均不为 `Uu`** 的 gold-expanded pair 数；含 `Uu` 的 pair 不进分母也不进分子；
- **聚合**：先按 2,913 篇 OOF 文档合并为 pooled 比率（pair-micro），再报逐折值；
- gold 关系只在此处读取，**不进入模型任何一臂**；
- **参照线（在任何方法结果之前实测，fold 1 全 583 篇 / 10,679 gold-expanded pairs）**：把 gold
  factuality 标签代入同一计数器，CAUSE violation 率是 **`.003602`**（11 / 3,054）、PRECONDITION 是
  **`.007744`**（59 / 7,619）。⇒ 这条约束在数据里**不是恒真但接近恒真**，所以中介应当读作
  「离这条地板还有多远」。⚠️ 也正因为地板接近 0，**中介与预测错误率高度相关，不是与主指标独立的
  第二条证据**；写作时不得把中介下降单独当成机制成立的证明，必须与 rewired 对照一起读。

## Promotion gate（先于任何方法数字冻结）

1. **主效果**：pooled five-class macro-F1 ≥ **`.583995`**（`= .553995 + .030`，`.030` 是 R1 事前登记的
   minimum meaningful effect）。若届时名册中出现更强的同协议公开对手，目标自动抬高为
   `max(.583995, 该对手 + ε)`，**只升不降**；`.553995` 只是“赢 CLS”的最低过线，不等于研究完成；
2. **归因**：`full > base` 且 `full > rewired`，两者在同一 2,913-doc OOF unit 上做
   **10,000 次 document-cluster paired bootstrap**，95% CI 下界均 `> 0`；
3. **稀有类护栏**：PS− F1 ≥ **`.352456`**、Uu F1 ≥ **`.166850`**（各为 CLS 锚 `.382456` / `.196850`
   减 `.030`）；五类**均不得**塌为 0；
4. **中介**：full 的两项 violation 比率**均**低于 base，且 rewired **不**保留该改善；
5. **覆盖与部署性**：恰好 2,913 documents / 73,939 mentions 各一次；每篇 evaluation 文档不在该折
   train/selection-dev；推理输入只有文本、mention 与冻结 posterior。

1–3 任一不过即本周期失败；4 不过时只能写“预测改进、机制未证”，不得改写成机制结论。

## Stop conditions

- 用 gold 边 / gold factuality / final-valid 反馈改善任何一臂：立即停止，结果作废；
- 在看到方法结果后修改 §边的构造、§Arms、§Mediators、§Promotion gate 的任一条：立即停止；
- 用更大 backbone、扫 epoch/threshold、换 split、换 seed 去捞分数：立即停止（多种子须逐次授权）；
- rewired 与 full 无差别，或 rewired 同样改善中介：机制 claim 失败，按 §25.1 只写预测层结论；
- 本周期失败 ⇒ 做**错误归因**并回 R1 立项**实质不同**的第二个设计周期；**不得**换名、扫参或
  更大 backbone 复活同一家族。两个有效周期后封存该家族（与 C5 契约同条款），但**不自动取消 D4 章**。

## Bundle

`runs/stages/D4/d4-v62-predicted-causal-r1/` 必含 `protocol.json`（preflight 冻结的全部输入/代码/命令
哈希）、逐文档三臂预测、逐折与 pooled 五类指标、两项中介的分子/分母、paired bootstrap 的
sufficient statistics、rewiring 的可重算种子与实际多重集校验、checkpoint 哈希与 `status.json`。
**数字只追加到 [`../results/PHASE_D.md`](../results/PHASE_D.md)**，别处只引用不复制。

## GPU command

preflight 与实现（C-27）完成、本地三件套全绿、核卡确认空闲后，固定入口为：

```bash
cd /data/TJK/ekg
CUDA_VISIBLE_DEVICES=<free card> setsid nohup .venv/bin/python -u \
  scripts/run_d4_predicted_causal.py \
  --contract runs/stages/D4/d4-v62-predicted-causal-r1/preflight/protocol.json \
  --arm <full|base|rewired> --fold <1..5> --seed 13 \
  --output runs/stages/D4/d4-v62-predicted-causal-r1/seed-13/<arm>/fold-<k> \
  > logs/d4_v62_<arm>_fold<k>.log 2>&1 < /dev/null &
```

脚本或 preflight 不存在、当前 commit 未过本地 gate、或卡上有他人进程时不得启动；
一条 ssh 只发一个后台任务，三臂/五折之间的并行属操作性决定，按空卡情况定。
