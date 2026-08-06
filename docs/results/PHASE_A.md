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

---

## Phase A2 · 架构对齐短档（2026-08-06，6 epochs，**5090**，`runs/relations/official_arch_6ep`）

**改动**：在官方配方短档（上面 2026-07-31 那节）基础上**只换架构**——`43e62df` 的
span mean-pooling + 2 隐层 MLP 头。配方、epochs、`max_length` 与那一档**全部相同**，
所以两档唯一的变量就是架构。**checkpoint 留在 5090**（4090 自 2026-08-06 够不着）。

6 epoch loss **0.771 → 0.479**（对照：旧架构同档 0.809 → 0.487）。官方口径评测
（`runs/relations/official_arch_6ep_scores.json`，官方 `evaluate.py`，710 篇 valid）：

| 关系 | 现役档（neg30·α0.5） | 旧架构·官方配方·6ep | **新架构·官方配方·6ep** |
|---|---|---|---|
| causal F1 | 23.91（P23.96/R23.86） | 8.56（P50.04/R4.68） | **8.10（P46.64/R4.43）** |
| subevent F1 | 24.03（P20.45/R29.14） | 1.00（P39.24/R0.51） | **0.00（P0/R0）** |
| temporal F1 | 22.25（P42.59/R15.06） | 15.34（P57.96/R8.84） | **17.25（P58.56/R10.11）** |
| MUC | 77.47 | — | **77.47**（共指档未换，链路自证） |

**结论：这一档不能用来判断架构升级有没有用。**

- 新旧两档**落在同一水平**（causal 8.10 vs 8.56，loss 曲线几乎重合），而两者**都还在
  「几乎全预测 NONE」的欠拟合区**——这正是 2026-07-31 那节已经诊断过的状态，
  当时的结论就是「6 epoch 远不足……下一步合理动作是投满 50 epochs，而非在 6ep 短档上下结论」。
  ⇒ **架构效果被欠拟合掩盖了，6ep 短档对「配方 vs 架构」没有分辨力。**
- subevent 从 1.00 掉到 0.00（一个正类都不预测，sklearn 报 `no predicted samples`）不构成
  「新架构更差」的证据：两个数都在"基本不预测正类"的同一状态里，差异无意义。
- MUC 与现役档**逐位相同**（77.47）——共指档没换，这是评测链路正确性的自证。
- **唯一能回答架构问题的对照是 50 epochs**：与 `official_recipe_50ep`（旧架构·同配方·50ep，
  causal **22.26**）对比，才是干净的单变量实验；判据仍是官方原版代码同 split 的 **31.37**。

⚠️ **流程教训**：契约步骤 1 的 6ep 短档 2026-07-31 已经跑过并已下过「6ep 无分辨力」的结论，
本次换架构后又重跑了一遍同样的短档，**等于把一个已知无分辨力的实验做了第二次**。
换单一变量做对照时，**对照档的 epochs 必须落在原实验已证明有分辨力的区间**，
否则拿到的只是同一个欠拟合平台。

---

## ⚠️ 更正（2026-08-06 实测）：`--neg-ratio 30` 从未真正下采样过

跑「现役档配方 + 新架构」对照时，两档的启动配置行都打印 **2,532,394 rows**——
而 `--neg-ratio inf` 档明确标注 `all (no downsampling)`。同数即同集，遂实测：

```
total     = 2,532,394
positives =   517,700  (20.44%)
negatives = 2,014,694
pos * 30  = 15,531,000  >>  negatives = 2,014,694
=> keep = min(negatives, pos*30) = negatives  ⇒ 全部负例保留
```

`downsample_negatives` 的逻辑是 `keep = min(len(negatives), int(len(positives) * ratio))`。
MAVEN-ERE 全量的**实际负正比只有 3.9 : 1**，而阈值要的是 30 : 1
⇒ **`--neg-ratio 30` 与 `--neg-ratio inf` 在这份数据上产生完全相同的训练集**，
下采样这条代码路径**从未触发过**。

**被推翻的结论（必须改）**：

1. `PHASE_A2_ch2_official_recipe.md` 的「四处差异」表里，第一条**「负样本：零负采样 vs `--neg-ratio 30`」
   实际不存在**；「前两条同向叠加是 precision 崩塌首要嫌疑」这个工作假设**只剩类权重一条**。
2. 契约里「全量有序对 2,532,394 行（**neg30 档的 14 倍**）」**是错的**：neg30 档就是 2,532,394 行，
   1 倍。该句标着「规模已核，不必再算」，但与实测不符 —— 已更正。
3. 因此 `official_recipe_*` 系列（2026-07-31 的 6ep、2026-08-01/02 的 50ep）**以为自己在测
   「关掉负采样 + 关掉类权重」，实际只测了「关掉类权重 + 分离学习率 + warmup」**。
   那两档的数字本身仍然有效（配置行如实记录了生效参数），但**归因描述要按本条重写**。
4. Phase A 现役档 causal recall 67.5% 是在**全量负例**下达到的，不是「因为下采样了负例才召回高」。

**不影响**：本次「现役档配方 + 新架构」对照仍是干净的单变量实验——
现役档与本档都传 `--neg-ratio 30`，两边同样不下采样，唯一变量仍是架构。

### 附：training loss **不能**跨档比（2026-08-06 教训）

比新架构时曾拿现役档「loss 1.25→0.92」当参照读出「轨迹重合＝架构没差别」，**该结论已撤回**。三条理由：

1. **参照档的 config 行拿不到**：`supervised_maven` 是 2026-07-24 在 **4090** 训的，其训练日志
   不在 5090，4090 又够不着 ⇒ 它的 rows / `weight_alpha` **只有文档二手描述，无一手记录**。
2. **loss 尺度由 `weight_alpha` 与负例混合主导，不由架构主导**——本 session 的一手对照：
   `official_arch_6ep`（rows 2,532,394 / α=**0.0**）loss 0.771→0.479；
   `neg30_arch_6ep`（rows **同为** 2,532,394 / α=**0.5**）loss 1.726→1.192。
   **同数据、只改 α，loss 尺度差一倍多。**
3. **Phase A 内部各档尺度本就不一致**：本文件 §首轮记 3ep 为 4.12→2.49→2.04→**1.76**，
   §达标档记 3→6ep 为 **1.25**→0.92——若同配置连续训练，两者不可能衔接。

⇒ **排名一律只用官方口径评测分（downstream）**，training loss 只用于看单档自身是否还在降（欠拟合判据）。
⇒ 跨档比 loss 前，先并列两档的 `[train] ... rows (negatives ...), weight_alpha=...` **一手配置行**；
   拿不到一手行就**不要比**。
⇒ 比较必须**同 epoch index 对齐**（曾拿 ep2 对 ep3）。

---

## Phase A2 · 架构升级的单变量对照（2026-08-06，**5090**，`runs/relations/neg30_arch_6ep`）

**设计**：在**现役档配方**（`--neg-ratio 30 --weight-alpha 0.5 --lr 2e-5 --epochs 6 --max-length 512`，
不带 head-lr / warmup）下**只换架构**（`43e62df` 的 span mean-pooling + MLP 头）。
选这个配方而不是官方配方，是因为现役档 causal 23.91 **不在欠拟合平台上**，有分辨力；
上一节的 6ep 官方配方档双方都塌在「几乎全预测 NONE」，读不出架构效果。
训练 loss 1.726→0.997。评测阈值 **0.7**（沿用现役档选值，保持单变量）。

官方口径（`runs/relations/neg30_arch_6ep_scores.json`，官方 `evaluate.py`，710 篇 valid）：

| 关系 | 现役档（旧架构·同配方） | **新架构·同配方** | Δ | 官方原版代码@同 valid |
|---|---|---|---|---|
| causal F1 | 23.91（P23.96/R23.86） | **24.06（P22.17/R26.31）** | **+0.15** | **31.37** |
| subevent F1 | 24.03（P20.45/R29.14） | **22.56（P17.27/R32.53）** | **−1.47** | — |
| temporal F1 | 22.25（P42.59/R15.06） | 23.06（P43.55/R15.68） | +0.81 | —（缺 TIMEX 头，口径不可比） |
| MUC | 77.47 | **77.47** | 0 | — |

**结论：契约步骤 4 的「差距在架构」诊断被证伪。**

- causal **+0.15** 是噪声级，subevent **−1.47** 反而降；补齐 span mean-pooling + MLP 头之后，
  与官方原版代码的差距仍有 **31.37 − 24.06 = 7.31 点**。**架构解释不了它。**
- **P/R 结构没有朝官方走**：官方 P35.0/R27.2 是 precision 主导，本档 P22.17/R26.31 反而比现役档
  更偏召回（P 23.96→22.17、R 23.86→26.31）。预测量从现役档量级涨到 **102,011 对**
  （同流程下 α=0.0 的 `official_arch_6ep` 只有 36,952 对）——**α 才是预测量与 P/R 结构的主控开关**。
- MUC 逐位相同（77.47），共指档未换 ⇒ 评测链路正确性自证，掉/涨都发生在关系侧。

**两条必须写明的局限**（否则这个"单变量"是假的）：

1. ⚠️ **现役档的配方是二手的**：`supervised_maven` 训练日志在 4090（够不着），
   其 `[train] ... rows / weight_alpha` **一手配置行拿不到**，本档配方是照 `EXPERIMENTS.md` 与
   契约对照表复原的。若现役档实际配方与此有出入，"唯一变量是架构"就不成立。
2. ⚠️ **架构只对齐了两处中的两处，还有第三处没动**：官方 pair 特征是**简单拼接 `[e1;e2]`（1536 维）**，
   我们仍是**工程化 4 路 `[h_i;h_j;h_i⊙h_j;|h_i−h_j|]`（3072 维）**。`43e62df` 只换了头的容量与
   触发词池化，**没有换特征构造**。（4 路含交互项通常更强，不像是我们更差的原因，但它是未控变量。）

**下一步的候选解释（按可疑度排）**：

1. **单关系训练 vs 多头联合**：官方 `causal/` 子目录训的是**只出 causal 的模型**；我们是
   temporal+causal+subevent **三族共享一个 encoder 联合训练**，存在多任务干扰。
   官方论文的 "+joint" 是它自己的联合方式（causal 30.6→31.5，联合更好），**与我们的联合实现不是一回事**。
2. 优化器 / 调度 / batch 构造的其余细节（官方 batch_size 4、按文档成批的方式）。
3. pair 特征构造（上面局限 2）。

⛔ **不要再在负采样比例 / 类权重 / 学习率 / epoch 数上找**——这三类已分别被
2026-08-01/02（50ep）、2026-08-06（本节 + neg30==inf 更正）排除。

---

## ★ Phase A2 · 真正的根因：跨句表示隔离（2026-08-06/07，`runs/relations/neg30_window_6ep`）

前面四条解释（配方 / 跨 split / 候选 population / 架构）全部排除后，把官方
`THU-KEG/MAVEN-ERE` 克隆下来**逐行读 `causal/src/data.py`**，找到了真正的差异——
**不在模型，在编码粒度**：

| | 官方 baseline | 我们（改前） |
|---|---|---|
| 编码单位 | **多句拼进一个 `<= max_length` 窗口**（CLS 开头、句间 SEP），**一次前向** | **每句一次独立前向** |
| 后果 | 窗口内所有事件在同一张 attention 图里，彼此可见 | **跨句事件对的两个表示从未交互过** |

**这不是细节，是主因**——实测 valid 的跨句占比：

| 关系 | 同句 | **跨句** |
|---|---|---|
| causal | 31.2% | **68.8%** |
| subevent | 14.2% | **85.8%** |

⇒ 我们有 **68.8% 的 causal / 85.8% 的 subevent** 的 pair，分类头只能靠两个**互相没见过面**
的向量硬猜。**这解释了为什么改配方、改头容量、改 span pooling 全部无效：缺陷在输入表示，
下游怎么改都补不回来。**

### 修复与结果（单变量：配方逐项相同，只换编码）

`encode_trigger_reps` 改为窗口打包（`abbdbfd`）。官方口径 valid：

| 关系 | 按句编码 `neg30_arch_6ep` | **窗口编码 `neg30_window_6ep`** | Δ | 官方原版代码@同 valid |
|---|---|---|---|---|
| causal F1 | 24.06（P22.17/R26.31） | **26.95（P28.18/R25.83）** | **+2.89** | 31.37（P31.03/R31.72） |
| temporal F1 | 23.06（P43.55/R15.68） | **28.40（P51.70/R19.58）** | **+5.34** | —（缺 TIMEX 头，不可比） |
| subevent F1 | 22.56（P17.27/R32.53） | **22.97（P20.74/R25.73）** | +0.41 | — |
| MUC | 77.47 | **77.47** | 0 | —（共指档未换，链路自证） |

⇒ 与官方的差距 **7.31 → 4.42**；P/R 结构也朝官方靠（P 22.17→28.18，官方 31.03）。

### 机制验证：增益全部落在跨句（分层诊断）

`tools/stratified_eval.py` 复现官方口径（同一套 mention 对枚举与展开），只按句距分层；
`all` 行与官方评测器**逐位一致**，证明口径正确：

| causal | 按句编码 | 窗口编码 | Δ |
|---|---|---|---|
| **跨句**（gold_pos 10,237） | 19.99 | **24.11** | **+4.12** ✅ |
| 同句（gold_pos 3,387） | 36.61 | 35.48 | −1.13 |
| all | 24.06 | 26.95 | +2.89 |

**预测的效应方向与位置都对上了**：修的是跨句隔离，涨的就是跨句。同句略降，是窗口引入更多
上下文噪声的代价，净效应为正。subevent 同样跨句涨（21.95→22.41）。
同句/跨句差距 **16.62 → 11.37**，落进文献公认区间。

### 文献印证（一手核过）

- **KnowQA**（arXiv 2410.04752）实测：MECI 上 intra-sentence F1 77–78%，**inter-sentence 掉到 12.5–40%**
  ——跨句因果抽取难一个数量级，与我们的分层结果同构。
- 该文用 **Flan-T5-Large 在 MAVEN-ERE causal 上只有 26.2**，**低于官方 RoBERTa-base 的 30.6**
  ⇒ 30.6 不是"基础水位"而是相当强的数字，**校准我们的预期**。
- 文档级 RE 综述口径：inter-sentence F1 长期比 intra-sentence 低 **10–15 点**。

### 下一步（跨句仍是主战场）

跨句占 **75% 的正例**却只有 24.11（同句 35.48）。若把 cross 提到 same 水平，总分约 35，
**将超过官方 31.37**。已识别的抓手：
1. **`PairExample.distance` 已算好但分类头从未使用**（mention 序距）——文献里的 location
   information，接进去几乎零成本。
2. 13.3% 的文档仍需 >1 窗口，那些 pair 依旧隔离（可用重叠滑窗）。
3. 事件类型 embedding（`EventNode.event_type` 已有 151 种）——⚠️ 需把类型词表随 checkpoint
   保存，否则 train/inference 间 id 错位会**静默降分**。

### 残余隔离审计：重叠滑窗不值得做（2026-08-07，`tools/window_split_audit.py`）

窗口编码修好了「同窗口内的跨句对」，但**跨窗口的对依旧隔离**。在动手做重叠滑窗之前先量化了它
（CPU 重放打包逻辑，不跑 encoder）——`max_length=512`、valid 710 篇、共 820 个窗口（1.15/篇，
13.8% 的文档需要 >1 窗口）：

| 关系 | gold pairs | 同窗 | **跨窗（仍隔离）** |
|---|---|---|---|
| causal | 9,698 | 96.7% | **3.3%** |
| subevent | 2,826 | 92.7% | 7.3% |
| temporal | 109,933 | 81.1% | **18.9%** |

⇒ **causal 的重叠滑窗收益上限只有 3.3%，不做**。窗口编码已吃掉这个方向的绝大部分红利。
⇒ temporal 有 18.9% 跨窗，滑窗对它才有意义——但 temporal 口径本就不可比（缺 TIMEX 头），优先级低。
⇒ **causal 的剩余 4.42 点差距必须从别处找**，不在窗口切分。

## Phase A2 · 距离流（2026-08-07，`runs/relations/neg30_window_dist_6ep`）

把**已算好却从未进过分类头**的 `PairExample.distance`（`mention_order` 序距）接进 pair 头：
确定性分桶（`distance_bucket`，无学习词表 ⇒ 两端 id 不可能错位）+ `nn.Embedding(11, 32)`，
**zero-init 起步为 no-op**（默认 `N(0,1)` 的新流会在学到东西前淹掉已调好的特征路径）。
配方与 `neg30_window_6ep` **逐字符相同**，唯一变量是距离流。

| 关系 | 窗口编码 | **窗口 + 距离流** | Δ |
|---|---|---|---|
| causal F1 | 26.95（P28.18/R25.83） | **27.60（P29.68/R25.79）** | **+0.65** |
| temporal F1 | 28.40 | 28.59 | +0.19 |
| subevent F1 | 22.97（P20.74/R25.73） | 22.26（P21.77/R22.77） | **−0.71** |
| MUC | 77.47 | 77.47 | 0（共指档未换） |

分层（机制**与预期相反**）：

| causal | 窗口 | 窗口+距离流 | Δ |
|---|---|---|---|
| 同句 | 35.48 | **37.02** | **+1.54** |
| 跨句 | 24.11 | 24.42 | +0.31 |

- 预期是「距离信息帮助远距离推理」⇒ 跨句该涨；**实测增益主要在同句**。
  合理的解释是：距离流的实际作用是让模型学到 **bucket 0（同句）这个强先验**，而不是长程推理。
- **⚠️ 效应量不足以作正面主张**：causal +0.65 / subevent −0.71，方向不一、量级均 <1 点，
  单种子分不清真实效应与噪声。**多种子之前不得写成「距离流有效」。**
- 之所以在后续长训练里保留它：causal 是口径最干净的主指标，且其 precision 28.18→29.68
  朝官方的 31.03 靠。**这是工程取舍，不是已验证的结论。**
