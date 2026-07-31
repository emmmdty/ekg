# Phase A 实测档案 · Ch2 判别式关系抽取

> 本文件是 **Phase A 的实测档案**：当时跑出的真实数字、口径、踩过的坑。
> 实时状态见 [`../TODO.md`](../TODO.md)，阶段契约见 [`../phases/`](../phases/README.md)。
> **数字以本文件为准**：TODO 与 EXPERIMENTS 只引用、不复制。

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

---

## 官方口径复评（2026-07-30，Phase A 的 checkpoint 不变，只换评测器）

**为什么要重评**：我们的 `evaluate_relation_pairs` 与 MAVEN-ERE 官方 `evaluate.py` **不是同一个量**。
官方枚举文档内**全部有序 mention 对**、把每条簇级金标关系**展开到两簇间每一对 mention**、
temporal 还把 **TIMEX id 一并加入 mention 列表**，最后只对正类做 micro 平均。
拿我们的数去比论文里的数，此前一直不是同口径。

复现命令（`runs/relations/official_protocol_valid.json`）：

```bash
uv run python scripts/build_maven_ere_submission.py --from-labeled \
  --test data/processed/maven_ere/valid.jsonl --coref-predictor supervised \
  --coref-checkpoint runs/nodes/coref_supervised_6ep \
  --relation-checkpoint runs/relations/supervised_maven \
  --output runs/relations/valid_prediction.jsonl
uv run python scripts/score_maven_ere_official.py --evaluator <官方 evaluate.py> \
  --gold data/processed/maven_ere/valid.jsonl --pred runs/relations/valid_prediction.jsonl
```

| 指标 | 我们内部口径 | **官方口径 @valid** | 官方 RoBERTa-base @test |
|---|---|---|---|
| causal F1 | .250 | **23.91**（P 23.96 / R 23.86） | 30.6 ±0.44 |
| subevent F1 | .213 | **24.03**（P 20.45 / R 29.14） | 26.7 ±1.34 |
| temporal F1 | .338 | **22.25**（P 42.59 / **R 15.06**） | 55.8 ±0.42 |

- **causal 两个口径接近**（.250 vs 23.91），我们内部那把尺对 causal 基本可信。
- **subevent 官方口径反而更高**（21.3 → 24.03）：金标被展开到所有 mention 对，我们逐对预测因而多吃到真正例。
- 🛑 **temporal 不可比且这次量化了**：官方 recall 只有 **15.06** 而 precision 42.59 —— 缺 TIMEX 头
  （39% 的金标 temporal 对触及 TIMEX）的直接证据。**这个数不能用来下任何关于模型能力的结论。**
- ⚠️ 仍存的不可比处：**我们 valid、官方 test**，且该数据集 dev 明显低于 test（RESIJ 自测 causal −3.7）。
  CodaLab 通道 2026-07-30 已关，拿不到我们的 test 分 ⇒ **只能把对标方也拉到 valid**（见 `PHASE_A2`）。
