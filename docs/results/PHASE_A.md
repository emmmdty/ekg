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

---

## Phase A2 · 官方配方短档探路（2026-07-31，6 epochs，`runs/relations/official_recipe_6ep`）

**改动**：`--neg-ratio inf --weight-alpha 0.0 --lr 1e-5 --head-lr 1e-4 --warmup-steps 200`（四项官方配方
开关中的三项）。**`max_length` 未能按契约改到 256**：`SupervisedRelationExtractor` 按句编码，MAVEN-ERE
最长单句 322 token，256 会在触发词之前截断，`locate_trigger_token` fail-fast 报错（非静默丢数据）——
这是代码既有的已知约束（类 docstring 已写明），不是本次新增缺陷。改用 512（与 Phase A 现役档一致）后
正常训练，6 epoch loss 0.809→0.487（仍在降，未收敛）。

官方口径评测（`runs/relations/official_recipe_6ep_scores.json`）：

| 关系 | Phase A 现役档（neg30·α0.5） | **本档（official recipe·6ep）** | 官方 RoBERTa-base@test |
|---|---|---|---|
| causal F1 | 23.91（P23.96/R23.86） | **8.56**（P**50.04**/R**4.68**） | 30.6 |
| subevent F1 | 24.03（P20.45/R29.14） | **1.00**（P**39.24**/R**0.51**） | 26.7 |
| temporal F1 | 22.25（P42.59/R15.06） | **15.34**（P**57.96**/R**8.84**） | 55.8 |

- **方向判据成立**：precision 全面大涨（causal 24.0→50.0、subevent 20.5→39.2、temporal 42.6→58.0），
  证实"负采样+逆频类权重同向叠加是 precision 崩塌的首要嫌疑"这一假设——去掉两者后确实从"召回主导"
  翻回"精度主导"，方向与官方一致。
- **但 F1 全面更差**：recall 崩得比 precision 涨得更狠（causal R 23.9%→4.7%、subevent 29.1%→0.5%），
  三个 F1 都低于现役档、也远低于官方基线。诊断：零下采样+等权重的全量数据（250万+行，NONE 占绝大多数）
  下，6 epoch 远不足以把决策边界从"几乎全预测 NONE"挪开——loss 仍在下降即是欠拟合的直接证据。
  官方配方本身跑的是 **50 epochs**，不是 6。
- **结论**：不能据此判定"配方解释不了差距"（契约止损条件的前提是**跑过官方 epoch 量级**后仍 <28）。
  按契约步骤 3，方向已验证为对，下一步合理动作是投满 50 epochs，而非在 6ep 短档上下结论。

---

## Phase A2 · 官方配方 50 epochs 全量（2026-08-01/02，`runs/relations/official_recipe_50ep`）

训练：loss 0.8098（epoch0）→ 0.0841（epoch49），收敛良好，无发散。阈值 0.7（沿用现役档选值）下
官方口径评测：causal F1 **19.27**（P33.83/R13.48）、subevent F1 **7.87**（P31.75/R4.49）、
temporal F1 **25.86**（P43.17/R18.46）。

**阈值扫描**（同一 checkpoint，只重跑推理+打分，不重训；0.1/0.15/0.2/0.3 四点结果完全相同，
说明该 checkpoint 的置信度分布在低段有平台，继续降阈值不再新增预测；0.3 是本次扫描的最佳点）：

| 阈值 | causal F1 (P/R) | subevent F1 (P/R) | temporal F1 (P/R) |
|---|---|---|---|
| 0.7 | 19.27 (33.83/13.48) | 7.87 (31.75/4.49) | 25.86 (43.17/18.46) |
| 0.6 | 20.81 (31.57/15.52) | 9.02 (28.90/5.35) | 27.12 (41.93/20.04) |
| 0.5 | 22.10 (29.84/17.55) | 10.55 (26.99/6.56) | 28.08 (40.69/21.43) |
| **0.3(=0.2=0.15=0.1)** | **22.26 (29.45/17.89)** | **10.55 (26.99/6.56)** | **28.17 (40.36/21.64)** |

**三档官方口径总对照（都是 valid，都用官方 `evaluate.py`）：**

| 关系 | 官方 RoBERTa-base@test | Phase A 现役档 neg30·α0.5 | **官方配方 50ep（最佳阈值0.3）** |
|---|---|---|---|
| causal F1 | 30.6（P35.0/R27.2） | 23.91（P23.96/R23.86） | **22.26（P29.45/R17.89）** |
| subevent F1 | 26.7 | 24.03（P20.45/R29.14） | **10.55（P26.99/R6.56）** |
| temporal F1 🛑不可比 | 55.8 | 22.25（P42.59/R15.06） | **28.17（P40.36/R21.64）** |

**如实结论（不理想，触发契约预定的止损条件）**：
- precision 方向的假设**部分兑现**：causal/subevent 的 precision 在最佳阈值下仍高于现役档
  （29.45>23.96、26.99>20.45），"负采样+类权重双重补偿推高 precision 崩塌"这个机制是真实存在的。
- 但**换配方不是净改进**：causal F1 22.26 < 现役档 23.91（更差），subevent F1 **10.55 < 现役档 24.03**
  （腰斩），只有 temporal（不可比口径）从 22.25 升到 28.17。零下采样+等权重换来的 precision 提升，
  不足以抵消 recall 的损失（causal R 23.86%→17.89%、subevent R 29.14%→6.56%）——**尤其 subevent，
  50 epochs 仍学不出足够的正类判别力**，该关系的正例在全量数据里最稀疏。
- **causal F1 22.26 < 28**，触发 `PHASE_A2_ch2_official_recipe.md` 里预先写好的止损条件：
  "复刻官方配方后 causal 仍 <28（官方口径）：说明差距不在类不平衡处理，转去核候选构造与评测人群
  是否一致（是否同一 pair population），不要继续扫超参"。**不再投入更多 epoch / 学习率等超参扫描**。
- 已排除的解释：不是 6 epoch 欠拟合（50ep loss 已收敛到 0.084）；不是阈值没调对（已扫描到平台区间）。
- **未排除的解释（待下一步核实）**：候选 pair population 是否与官方一致（官方是否用了不同的候选
  构造规则、mention 粒度、或文档切分方式）；也可能确凿差距本身有跨 split 成分（valid 结构性低于 test）
  ——**契约步骤 4（跑官方原版代码在同一 valid 上出对照数）**是目前唯一能把这两种解释分开的办法。

---

## Phase A2 · 契约步骤 4：官方原版代码同 split 对照（2026-08-02）

**做法**：克隆 `THU-KEG/MAVEN-ERE`（causal/ 子目录），核实我们的 `data/raw/maven_ere/*.jsonl`
与官方原始 schema **逐字段一致**（`events`/`causal_relations`/`event_mentions`，无需任何格式转换），
软链到官方代码期望路径 `data/MAVEN_ERE/`。2022 年的代码在当前 transformers 4.53.3 下有两处
兼容性问题，做了最小化必要补丁（均在 `/tmp/MAVEN-ERE-official/`，未改动我们自己的代码库）：
- `transformers.AdamW` 已被移除（当年是 `torch.optim.AdamW` 的薄封装）→ 改从 `torch.optim` 导入。
- `RobertaConfig` 新版不再继承 `BertConfig`，原有 `isinstance` 分支判断失效 → 放宽 isinstance 检查。
- 官方 `dump_result.py` 只认匿名无标签的 test 格式，读不了有金标的 valid → 新写 `dump_valid.py`，
  复用官方 `data.py` 里构造标签用的同一个 `Document` 类，保证预测的 pair 顺序与训练时labels对齐。
以 2% 采样 + 1 epoch 冒烟测试跑通全链路（含新补丁）后，正式跑官方 README 原始命令
`python -u main.py --eval_steps 500 --epochs 50 --batch_size 4`（4090 卡0，训练+双路 predict 共约2小时）。

**结果（官方 `evaluate.py`，同一 `data/raw/maven_ere/valid.jsonl`，同一评测协议）：**

| 关系 | 官方 RoBERTa-base@test（论文） | **官方原版代码@我们的valid（本次）** | 我们自己复现（最佳档） |
|---|---|---|---|
| causal F1 | 30.6（P35.0/R27.2） | **31.37（P31.03/R31.72）** | 22.26（P29.45/R17.89） |

（temporal/subevent/coref 这次不构成有效对照——`causal/` 子目录的模型只产 causal 预测，
`score_maven_ere_official.py` 对缺失字段优雅降级为 0，不是真实的模型能力，忽略。）

**结论（关键，解开了 Phase A2 一直没解开的疑点）**：
- **官方原版代码在我们完全相同的 valid split、完全相同的评测器上，跑出 31.37**——比论文 test 集
  的 30.6 还略高。这**排除了"差距是跨 split 造成的假象"这个假设**：不需要 CodaLab、不需要外推，
  同一份 valid 数据本身就能喂出对得上论文数量级的分数。
- **也基本排除了"候选 pair 构造/评测人群不一致"这个假设**——用的是同一个 `score_maven_ere_official.py`
  评测同一份数据，唯一变量是训练代码本身。
- **真正的差距来源是模型架构，不是训练配方超参**。读 `utils/model.py` 逐行核对，找到两处与我们自己
  实现材质不同的地方（不是超参，是结构）：
  1. **事件表示**：官方对触发词整个 span 做 **mean-pooling**（`doc_embed[j][span[0]:span[1]].mean(0)`，
     跨多个 BPE token 取平均）；我们的 `locate_trigger_token` 只取**触发词起始字符对应的单个 token**。
  2. **pair 分类头**：官方是 **2 层隐藏的 MLP + Dropout**（`Linear(1536,150)→ReLU→Dropout(.2)→
     Linear(150,150)→ReLU→Dropout(.2)→Linear(150,3)`，输入是简单拼接 `[e1;e2]`）；我们是**单层
     线性层**直接输出（`nn.Linear(hidden_size*4, n)`，输入是工程化的 4 路特征
     `[h_i;h_j;h_i⊙h_j;|h_i-h_j|]`）——容量、非线性、正则化三者都更弱。
- **这推翻了 Phase A2 之前"差距在训练配方（负采样/类权重/学习率）"的工作假设**：那些改动方向是对的
  （precision 确实回升）但从未触及真正的瓶颈——**分类头容量不足 + 触发词表示过于粗糙**，才是我们
  的复现落后官方 9 个 F1 点的主因。契约步骤 4 的对照实验把"配方 vs 架构"这两种解释干净地分开了。
- **待办（若要真正追平官方基线）**：把我们的 `PairClassifier` 换成同容量的 MLP+Dropout 头，
  把 `encode_trigger_reps` 从单 token 改成 span mean-pooling，是目前唯一有实证支持、值得投入的
  下一步——而不是继续在负采样比例/学习率/epoch 数上找。
