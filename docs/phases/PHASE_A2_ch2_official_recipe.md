# PHASE A2 — Ch2 按官方配方重训抽取器（关键路径）

> 单会话自包含契约 + 交接。`/clear` 后只读**本文件 + 自动载入的 `CLAUDE.md` + [`../SPEC.md`](../SPEC.md)**
> 即可执行。实测数字见 [`../results/`](../results/README.md)（单一事实源，本文件只引用不复制）。
> 建于 2026-07-31，仓库 HEAD 见 `git log -1`。

## 0. 先读：三条会让你白干的前提

1. 🛑 **CodaLab 通道已关**（2026-07-30 实测上传返回 `Submissions have been disabled by admins`）。
   竞赛页写「Ends: Never」只指没有截止日，**不等于在收提交**。
   ⇒ **不要再产提交 zip，产了也没法验**（作者 2026-07-31 明确停掉）。官方 test 分**拿不到**。
   `scripts/build_maven_ere_submission.py` 保留，但它现在唯一的用途是**把 valid 的预测写成官方
   格式，好让官方评测器打分**——那是评估，不是提交。
2. 🛑 **temporal 的数不能用**。官方 temporal 有 **39% 的对触及 TIMEX**（事件–时间表达式），
   我们的抽取器**没有 TIMEX 头**，官方口径下 recall 只有 15.06。这是实现范围问题，不是模型能力问题。
   **本 phase 只看 causal / subevent。**
3. ⚠️ **别拿我们的 valid 去比论文的 test**。该数据集 dev 明显低于 test（RESIJ 自测 causal −3.7 /
   temporal −6.4 / subevent −4.4 / MUC −4.5）。本 phase 的整个设计就是**把对标方也拉到 valid**。

## Goal（完成目标）

**用官方 baseline 的训练配方重训我们的 `supervised` 关系抽取器，在官方口径 valid 上把 causal 从
23.91 抬起来**，并据此回答一个具体问题：我们与官方基线的差距，有多少是**训练配方**造成的。

我们的架构与官方基线**本来就是同一个东西**（RoBERTa-base 成对分类），差的全是配方。
读官方源码（`THU-KEG/MAVEN-ERE/causal/src/data.py` + `main.py`）确认了四处差异——
**其中第一条 2026-08-06 被实测推翻，实际只有三处**：

| | 官方 baseline | 我们 Phase A | 已就位的开关 |
|---|---|---|---|
| ~~负样本~~ | ~~枚举全部 `n²−n` 有序对、零负采样~~ | 🛑 **`--neg-ratio 30` 从未生效，两边训练集逐行相同** | ~~`--neg-ratio inf`~~（空操作） |
| 损失 | `nn.CrossEntropyLoss(ignore_index=-100)`，**无类权重** | 逆频加权 α=0.5 | `--weight-alpha 0.0` |
| 学习率 | 两个优化器：encoder **1e-5** / 打分头 **1e-4** | 单一 2e-5 | `--lr` + `--head-lr` |
| 长度 / 训练量 | max_length **256**（**文档级**窗口）、**50 epochs**、batch 4 | 512（**句子级**）、6 epochs | `--epochs`；⛔ `--max-length` 见下 |

🛑 **「负样本」这条差异不存在**（2026-08-06 实测，推导见 [`../results/PHASE_A.md`](../results/PHASE_A.md)
末节）：`downsample_negatives` 是 `keep = min(len(negatives), int(len(positives) * ratio))`，
而 MAVEN-ERE 全量的**实际负正比只有 3.9 : 1**（正例 517,700 / 20.44%），阈值 30 : 1 **远高于它**
⇒ 全部负例都被保留，`--neg-ratio 30` 与 `--neg-ratio inf` **产生完全相同的训练集**。
⇒ **原「前两条同向叠加是 precision 崩塌首要嫌疑」的假设只剩类权重一条**；
`official_recipe_*` 系列以为在测「关负采样 + 关类权重」，**实际只测了后者 + 学习率 + warmup**。
⇒ 判断任何 `--neg-ratio` 改动前，**先看启动配置行的 rows 数变没变**——没变就是空操作。

⛔ **`--max-length` 这一项不可照搬，必须留 512**（2026-08-02 与 2026-08-06 各踩一次）。
官方的 256 是**文档级**窗口，我们的 `SupervisedRelationExtractor` 是**按句编码**——两个 256
不是同一个量。MAVEN-ERE 最长单句 322 token，设 256 会在触发词之前截断，
`locate_trigger_span` fail-fast 直接崩（**不是静默丢数据**，行为是对的）：

```
ValueError: trigger 'ceased' fell outside the tokenised span (truncated)
```

⚠️ 30 篇的 smoke 档**测不出这个**（短句全部通过），只有全量 2913 篇才撞得到——
别拿 smoke 跑通当全量能跑的证据。**这条差异消不掉**，除非把编码改成文档级；
所以「对齐官方配方」在长度这一项上本来就只能对齐到句子级的等价物。

## 依赖 / 产物

- 前置：Phase A 的数据与训练脚本（都在）；`runs/relations/supervised_maven` 是现役对照档。
- 产出：新 checkpoint `runs/relations/official_arch_*`（**留在训练它的那台**，见 `CLAUDE.md` 的
  checkpoint 规则）+ 官方口径评分 JSON 落 `runs/relations/`，数字回填
  [`../results/PHASE_A.md`](../results/PHASE_A.md)。

## 执行内容（Steps）

### 1. 短档探路（先做这个，别直接投满配方）

```bash
# 4090，先 nvidia-smi 核卡
CUDA_VISIBLE_DEVICES=<空卡> HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  .venv/bin/python -u scripts/train_supervised_relations.py \
    --train data/processed/maven_ere/train.jsonl \
    --model /data/TJK/models/roberta-base \
    --output runs/relations/official_recipe_6ep \
    --epochs 6 --neg-ratio inf --weight-alpha 0.0 \
    --lr 1e-5 --head-lr 1e-4 --warmup-steps 200 --max-length 512   # ⛔ 不是 256，见上
```

脚本启动会打印全部生效配置（行数 / 负样本策略 / 两个学习率 / warmup / max_length）——**先核对这一行**。

**规模（2026-08-06 实测更正）**：全量有序对 **2,532,394** 行 = 正例 517,700（20.44%）+ 负例
2,014,694。~~「neg30 档的 14 倍」~~ **是错的**——neg30 档也是 2,532,394 行，**1 倍**（见上方 🛑）。
训练循环**按文档走**，所以**优化器步数不变**（2913 步/epoch）。train 最大单篇 110 个 mention
→ 11,990 对 → pair 特征 0.15 GB，**不会 OOM**（251 那篇在 test，不参与训练）。
实测 6 epochs 在 5090 上约 **33 分钟**，两种 `--neg-ratio` 同样耗时（训练集本就相同）。

### 2. 官方口径评测（唯一可比的尺）

```bash
curl -o /tmp/maven_evaluate.py \
  https://raw.githubusercontent.com/THU-KEG/MAVEN-ERE/main/evaluate.py

# 用同一条链路把 valid 写成官方格式（--from-labeled 会把 valid 剥成 test 形状）
.venv/bin/python -u scripts/build_maven_ere_submission.py --from-labeled \
  --test data/processed/maven_ere/valid.jsonl \
  --coref-predictor supervised --coref-checkpoint runs/nodes/coref_supervised_6ep \
  --relation-checkpoint runs/relations/official_recipe_6ep \
  --relation-threshold 0.7 \
  --output runs/relations/valid_pred_official_recipe.jsonl

.venv/bin/python -u scripts/score_maven_ere_official.py --evaluator /tmp/maven_evaluate.py \
  --gold data/processed/maven_ere/valid.jsonl \
  --pred runs/relations/valid_pred_official_recipe.jsonl \
  --output runs/relations/official_recipe_6ep_scores.json
```

⚠️ **阈值 0.7 是 Phase A 在 valid 上选的**。换了配方后它未必是最优；**可以扫，但要在 valid 上扫并
声明**，不许拿任何 test 数据调（test 也没有标签，无从调）。

### 3. 看方向对不对，再决定投不投满

**判据不是 F1 涨没涨，是 P/R 结构有没有翻转**：官方是 **P 35.0 / R 27.2**（precision 主导），
我们现在是 **P 23.96 / R 23.86**。如果关掉双重补偿后 precision 明显上去了，方向就对，
再考虑往 50 epochs 投；如果 P/R 结构不动，说明差距不在配方，转第 4 步。

### 4. 若配方不解释差距

去跑官方自己的代码（`THU-KEG/MAVEN-ERE/causal/`，`main.py --eval_steps 500 --epochs 50 --batch_size 4`），
在**同一份 valid** 上出它的数。那才是真正的同 split、同评测器、同数据对照。
其 `src/data.py` 的数据构造已读过，接数据只需把我们的 jsonl 放到它期望的 `../data/MAVEN_ERE/` 布局。

**✅ 2026-08-02 已跑完，结论是决定性的**：官方原版代码在我们同一份 valid 上 **causal 31.37**
（比论文 test 的 30.6 还高）⇒ 同时排除「跨 split 假象」与「候选 population 不一致」两种解释，
**差距锁死在架构**。逐行核 `utils/model.py` 找到两处材质差异（数字与推导见 `../results/PHASE_A.md`）。

### 5. 对齐架构（当前队首）

第 4 步把「配方 vs 架构」分开后，唯一有实证支持的动作是**把两处材质差异补齐**——
代码已在 `43e62df` 落地（`src/ekg/relations/extractor/supervised.py`）：

| | 官方 `utils/model.py` | 我们（改前） | 改后 |
|---|---|---|---|
| 事件表示 | 触发词整个 span mean-pooling | 只取起始字符的单 token | `locate_trigger_span` → span 内 mean-pool |
| pair 分类头 | `Linear(·,150)→ReLU→Dropout(.2)→Linear→ReLU→Dropout(.2)→Linear` | 单层线性 | 同容量 2 隐层 MLP+Dropout |

```bash
# 5090（4090 够不着，见 ## GPU）；先 nvidia-smi 原子核卡
cd /mnt/aidata/tongjiakai/ekg && CUDA_VISIBLE_DEVICES=0 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
setsid nohup .venv/bin/python -u scripts/train_supervised_relations.py \
    --train data/processed/maven_ere/train.jsonl --model roberta-base \
    --output runs/relations/official_arch_6ep \
    --epochs 6 --neg-ratio inf --weight-alpha 0.0 \
    --lr 1e-5 --head-lr 1e-4 --warmup-steps 200 --max-length 512 \
    > logs/official_arch_6ep.log 2>&1 &
```

⚠️ **档名用 `official_arch_*` 而非 `official_recipe_*`**：后者是「只改配方、旧架构」那一档
（已止损，causal 22.26），两者是不同的实验对象，**别覆盖也别混报**。

评测照第 2 步，`--evaluator /mnt/aidata/tongjiakai/tools/maven_evaluate.py`
（5090 拉不到 GitHub，评测器已预置在那）。

**判据**：与官方原版代码的 **31.37** 比（同 split 同评测器的真对照），不是与论文 test 的 30.6 比。

#### 🛑 结果（2026-08-06）：**架构假设证伪，本 phase 的路线已走完**

两档都跑了，数字与推导见 [`../results/PHASE_A.md`](../results/PHASE_A.md) 末三节：

| 档 | 配方 | causal F1 | 说明 |
|---|---|---|---|
| `official_arch_6ep` | 官方配方·6ep | 8.10 | 与旧架构同档 8.56 同水平，**双方都在欠拟合平台，无分辨力** |
| `neg30_arch_6ep` | **现役档配方**·6ep | **24.06** | vs 现役档 23.91，**Δ +0.15（噪声级）**；subevent −1.47 |

⇒ 补齐 span mean-pooling + MLP 头后，与官方 31.37 的差距仍有 **7.31 点**。
**「差距在架构」这个由步骤 4 得出的诊断，被步骤 5 自己证伪了。**

⇒ **本契约的四条候选解释（配方 / 跨 split / 候选 population / 架构）已全部排除**，
`docs/TODO.md` 队首需要换成新的候选：① 单关系 vs 三族多头联合；② 优化器·调度·batch 构造；
③ pair 特征构造（`[e1;e2]` 1536 维 vs 我们 4 路 3072 维，本次**未动**）。
⛔ 负采样 / 类权重 / 学习率 / epoch 数**四类已全部排除，不要再扫**。

## Constraints

- 遵守 `CLAUDE.md` 全部硬约束。**只增不改**：新配方走命令行参数，**不要改默认值**
  ——`runs/relations/supervised_maven` 仍是 Phase A/B/D/E 一系列结果的依赖。
- **checkpoint 留在训练它的那台，不强制回传；要跨机搬运先问用户**（作者 2026-08-06 改）。
  **档在哪台记进 `../results/PHASE_A.md`。**
- 报数**如实**：降就说降。新旧两档都用**官方口径**报，别混用内部口径。
- ⚠️ Phase C 曾在打分头 `lr=1e-3` **发散**（loss 从 .428 升到 .646）。官方是 **1e-4**，
  比那个小一个量级且 encoder 压到 1e-5，**不能据 Phase C 那次否定 1e-4**。

## 验收标准（Done when）

- [ ] 短档跑通，启动日志确认四项配方全部生效。
- [ ] 官方口径 valid 上报出新档的 causal / subevent 的 **P / R / F1**，与现役档并列（`results/PHASE_A.md`）。
- [ ] **明确回答**：P/R 结构有没有从「召回主导」翻到「精度主导」；配方能解释多少差距。
- [ ] 校验命令全绿（`uv run pytest && uv run ruff check src tests scripts && uv run ekg-smoke`）。
- [ ] 结果回填 `docs/results/PHASE_A.md`，`docs/TODO.md` 只更新状态与下一步。

## GPU

重（全量有序对训练）。✅ **2026-08-07 4090 已恢复且四卡全空**（~~2026-08-06 隧道断线~~ 已解除）
⇒ **优先用 4090**（有空即可自用，无需逐次点头；card 3 故障需 NVML shim，**优先 card 1**）。
⚠️ **现役 checkpoint 大多在 5090**（`window_dist_20ep_macro` 等，见 `../GPU_RUNBOOK.md` 的
checkpoint 表）——**在 4090 起新训练前先确认要不要对照档**；跨机搬运约 70 分钟/档，**先问作者**。
5090 备用，**仍须逐次问作者**；两台都要开工前 `nvidia-smi` 原子核卡，不得挤占他人。

## 达不到怎么办（止损）

- 复刻官方配方后 causal 仍 <28（官方口径）：说明差距**不在类不平衡处理**，
  转去核**候选构造与评测人群是否一致**（是否同一 pair population），**不要继续扫超参**。
- 若第 4 步跑出的官方 baseline 在 valid 上也只有 ~24：那说明**「差 5.6 点」这个缺口本身就是
  跨 split 造成的假象**，Ch2 其实已经贴着基线——这同样是要如实写进论文的结论，且**比强行提分更值钱**。

## 已就位的资产（别重造）

| 资产 | 位置 | 说明 |
|---|---|---|
| 官方口径评测脚本 | `scripts/score_maven_ere_official.py` | 官方 `evaluate.py` **不进仓库**，用 `--evaluator` 传路径 |
| 预测→官方格式 | `scripts/build_maven_ere_submission.py` | `--from-labeled` 把 valid 剥成 test 形状；格式已验到金标自评 **100.0** |
| 格式不变量 | `tests/scripts/test_maven_ere_submission.py` | 7 条，锁住「mention 对 / 有序 / 单例免填」等语义 |
| 共指 checkpoint | 4090 + **5090** `runs/nodes/coref_supervised_6ep` | sha256 三端一致 |
| 关系 checkpoint（现役） | 4090 + **5090** `runs/relations/supervised_maven` | Phase A 交付档，作对照 |
| 现役档官方口径分 | 4090 `runs/relations/official_protocol_valid.json` | causal 23.91 / subevent 24.03 / MUC 77.47；**数字已在 `../results/PHASE_A.md`**，文件本身 4090 恢复前取不到 |
| 官方评测器 | **5090** `/mnt/aidata/tongjiakai/tools/maven_evaluate.py` | 5090 拉不到 GitHub，2026-08-06 从本地经 `gh-proxy.com` 传入，双端 sha256 一致 |
| MAVEN-ERE 训练数据 | **5090** `data/processed/maven_ere/train.jsonl` | 2026-08-06 传入，sha256 `6a5519fe…` / 2913 行 |

## 交接时踩过、别再踩的坑

- **带 timeout 的 scp 会静默留下半个文件**：本次取回预测文件被工具超时打断，得到 863 行
  （857 唯一 id + 6 行残留），而当时的校验是 `set(ids) == set(gold)`——**对重复行不敏感**，没查出来。
  一律用 `rsync` + **双端 sha256 + 行数/唯一性断言**。
- **rsync 只创建目标路径最后一级**：`runs/nodes/` 在 4090 不存在时直接报 code 11（Receiver file IO），
  先 `mkdir -p`。
- **`ls X 2>/dev/null` 会把「目录不存在」吞成「空目录」**，诊断时别这么写。
- **一条记录里两套坐标系**：共指按**字符**偏移池化进 `doc_text`（由原始 `sentences` 建），
  关系抽取器按 `sent_id` 索引行、且是在 `" ".join(tokens)` 视图下训练的。混用会让 `UNK`、
  标点触发词直接抛错。`build_maven_ere_submission.tokenised_view` 已处理。
