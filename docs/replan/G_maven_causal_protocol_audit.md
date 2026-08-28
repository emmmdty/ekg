# DR-G 本地一手审计：MAVEN-ERE causal 资格判定

> 审计日期：2026-08-26（Asia/Taipei）
>
> 原始报告：`docs/replan/G_maven_causal_protocol.md`
>
> 来源导出：`docs/replan/G_maven_causal_protocol.pdf`

## 结论

DR-G 的核心结论**通过本地事实验收**：当前不能把 MAVEN-ERE causal 升格为论文主轴，也不应启动
GPU baseline reproduction。原报告正确识别了四种互不等价的评测 setting，并正确指出最容易混淆的
Chen 2024 与 LLMERE 2025 并不共享 candidate universe。

本地审计补齐了原报告未能执行的 CPU 闭环，因此需要作一项重要升级：**LLMERE-defined B 的数据、
seed-42 split、pair/labels 和 evaluator 均已从 CONDITIONAL 升为 PASS**。这条协议可以作为可复用的
公开资产冻结。

最终资格仍为：**当前 NO-GO（对“立刻将 MAVEN-ERE causal 作为论文主任务并开始复现”）**。

唯一决定性的失败项是：截至本次审计，没有两个独立的 2024–2026 正式方法同时在这个 exact-B
协议上提供公开可执行闭环。LLMERE 是唯一能精确定义并重放该协议的方法，但其完整 Git 历史从未发布
训练/推理 package；Chen 只发布 500 个 relation-bearing 句子级样本；Xiang 的公开代码实际是
EventStoryLine 管线。按论文“必须在公开可比主指标上超过多个方法”的硬门槛，这已足以停止。

## 冻结的 exact-B 协议

### 数据与 split

官方 v1.0 数据已经完整存在于本项目，raw 与 processed 副本哈希一致：

| 原始文件 | 文档数 | SHA-256 |
|---|---:|---|
| `train.jsonl` | 2,913 | `6a5519fe7c30448690adb13d49217c50d474fc57480eae10aecb29df7eb638b7` |
| `valid.jsonl` | 710 | `6faea0e4e16b4a2d5d9631e09ef6e1c6bac6e3f912490bfc48eeaceaf98c6153` |
| `test.jsonl`（无 gold） | 857 | `aa34be601fc6397fec8256d796c4f73bd868f1230dea96e31675c18563f05bd7` |

exact-B 采用 LLMERE 作者代码的固定操作：`random.seed(42)` 后 shuffle 原始 train，前 80% 为 train、
后 20% 为 dev，原始 valid 原样作为 test。本地执行原脚本得到 2,330 / 583 / 710 篇文档：

| B 文件 | SHA-256 |
|---|---|
| train | `1d80e35db423df87e8a87261fbb4ce576bb45dc3aa9b4db43845dc3aa1f6a` |
| dev | `961abc25c81e571182849d8388c5dd39c81a5f182c1a16512515aca45856a550` |
| test | `6faea0e4e16b4a2d5d9631e09ef6e1c6bac6e3f912490bfc48eeaceaf98c6153` |

为避免依赖 JSON 序列化细节，文档 ID manifest 另行冻结：

| B manifest | SHA-256 |
|---|---|
| train IDs | `3884af697000d854f95f77b297c3ca686d56e3973e505b5a31aff7fba60a925a` |
| dev IDs | `8a2dfe00ff4fcaf12e1b6eb11492b43f5ec3bc9a312b6090bbe7e20275b8f3bd` |
| test IDs | `6c3fa23a4b2d1349aa16e61be245017cd1ae3a5e12f71eeebf85e4e004af7870` |

### Candidate universe、labels 与 evaluator

test 是完整 public-valid 710 篇文档。对每篇文档内所有不同的 gold event mentions 枚举有序 pair；
event-cluster 级 `CAUSE` / `PRECONDITION` 通过 mention cross-product 展开，其余 pair 标为 `NONE`。
最终指标是正类 `[PRECONDITION, CAUSE]` 的 micro precision / recall / F1。

本地独立计数为：16,301 个 event clusters、17,780 个 mentions、613,706 个有序候选 pair、9,698 条
event-level causal relations；展开后有 13,624 个 positive mention pairs，其中 `PRECONDITION=10,347`、
`CAUSE=3,277`。

这也消解了项目既有数字 6,599 与 DR-G 的 9,698 冲突：9,698 是完整 710-doc public-valid 上的
event-level causal relation 数；6,599 是此前把 public-valid 再切成 213 calibration + 497 test 后，
仅 497-doc 子集上的数。二者 split 不同，都不能移作同一口径。

### Evaluator 重放

审计 commit 为 LLMERE `94d4ef2781ec7e071d38ac7fd8632a8fffbda798`。使用作者发布的 causal
prediction artifact 和原始 `eval/MAVEN_ERE/eval_causal.py`，本地重放得到：

| Precision | Recall | F1 | Positive support |
|---:|---:|---:|---:|
| 34.98446 | 37.16970 | 36.04399 | 13,624 |

结果与仓库预计算指标实质完全一致。JSON 仅有本地 scikit-learn 版本导致的末位浮点表示及 support
整数/浮点序列化差异。prediction 文件有 29,080 个逻辑 JSON records，但末尾没有换行，所以
`wc -l` 显示 29,079；这不是缺失记录。

## 为什么仍然没有第二个 exact-B baseline

### Chen et al. 2024 不是同协议

作者正式论文 Appendix E 明确规定：原始 train 随机 8:2、原始 valid 作 test；但 ERE 随后在
sentence level 采样，排除两个 events 在四个关系轴上均无关系的样本，并从新 test 随机抽 500 个
examples 作为 testbed。因此它只是与 exact-B 共享粗粒度 split policy，不共享评测样本。

作者仓库 HEAD `58de425c88ccb4d98aaaf0f8ad24a4c2ba066dfb` 的公开 cache 定量如下：

| Chen cache | prompts | 唯一文档 | 定向 pairs | 文档来源 |
|---|---:|---:|---:|---|
| train | 500 | 401 | 1,000 | 全部来自 official train |
| test | 500 | 302 | 1,000 | 全部来自 official valid |

test cache 的 causal 标签仅为 `NO_CAUSAL=877 / PRECONDITION=61 / CAUSE=62`。500 条 prompt 中没有
一条满足“两方向四轴全部为 NO”，直接印证 relation-bearing sampling。它与 exact-B 在 710 篇文档上
枚举的 613,706 个有序 pair 不可比较。

仓库 evaluator 对四个关系轴分别调用 sklearn `classification_report`，不生成官方 MAVEN prediction
dump。完整 7-commit 历史也从未出现 split/cache generator、训练入口、checkpoint 或完整预测产物。
仓库中的 `src/data.py` 虽有另一个 document-level 数据类，但没有任何已发布的训练/推理闭环，不能把
作者的 500-sample 主实验追溯改造成 all-pairs baseline。

### LLMERE 自身只有协议与结果资产

LLMERE 完整历史只有 5 个 commit。所有历史路径均限于 data conversion、evaluators、published
predictions/results 和极简 README；从未出现 trainer、LLaMA-Factory config、inference entrypoint、
requirements/environment 或 checkpoint。因此它能作为 exact-B 的协议参考实现和结果 artifact，
不能被描述为 raw→train→predict→evaluate 的完整复现包。

公开代码还存在训练口径冲突：论文写 causal positive:negative 为 1:1，而
`convert_causal.py` 实际用 `neg_num = int(len(examples_pos) / 2 * 3)`，即 2:3。它不影响本次 test
scorer 重放，但阻止“完整复现论文训练设置”的无歧义声明。

### 其他候选不能补入 B

- **A official hidden-test**：官方 causal scorer 可得，但 857-doc test gold 不公开；Wei 2024 与
  TacoERE 的相关表格属于该轴，不能移入 public-valid-as-test 的 B。
- **Xiang 2025 / C**：作者仓库 HEAD `742f311094b1d87e126364a531a883d292d0b25e` 只有 2 个
  commit；`load_data.py` 读取未发布的 `train.npy`、排除 topics 37/41 并做 5-fold，实际是
  EventStoryLine 结构。仓库没有论文所写 MAVEN-ERE split、converter、manifest 或 evaluator。
- **KnowQA、TacoERE LLM、MMD-ERE / D**：均为各自 sampled setting，不能移入 B。KnowQA 论文给出的
  GitHub Web URL 在审计日返回 404；这只说明当前未取得，不作“代码绝对不存在”的过度结论。

## 修正后的 Go/No-Go 门

| 门槛 | 本地状态 | 依据 |
|---|---:|---|
| 数据版本/获取 | **PASS** | 官方 v1.0 train/valid/test 已落盘并冻结 SHA-256 |
| Split | **PASS** | LLMERE 原始 seed-42 脚本本地执行成功，文件与 ID manifest 均已冻结 |
| Pair / labels | **PASS** | all ordered gold mention pairs；`NONE/PRECONDITION/CAUSE`；独立计数与代码一致 |
| Evaluator | **PASS** | 原作者 prediction + 原 evaluator 本地重放，F1=36.04399 |
| 两个独立近期对手 | **FAIL** | 只有 LLMERE 落在 exact-B；Chen candidate universe 不同，其他方法属于 A/C/D |
| 公开训练/推理闭环 | **FAIL** | LLMERE 与 Chen 完整 Git 历史都没有可对应 exact-B 的完整链条 |
| 单张约 27GB | **不进入** | 静态 baseline 门已失败；GPU smoke 无法制造第二个同协议对手 |

## 决策与下一步

1. **不运行 GPU、不开始 baseline reproduction、不进入章节设计。**
2. 保留 exact-B 的数据、split、pair 与 evaluator 作为可复用协议资产，但不将其包装成已经具备论文
   竞争闭环的主任务。
3. 只有发现第二篇独立 2024–2026 方法确实在 exact-B 上发布可执行训练/预测链后，才重新打开该门；
   仅有相似 split 文字、引用表格数字或另一个 sampled setting 均不够。
4. ECI 与 MAVEN-ERE 两个优先候选都因同一硬条件失败。下一步若继续选题，应先由作者决定是扩大
   benchmark 候选池，还是调整“双独立公开 baseline”资格规则；在此之前不自动生成章节方案。

## 一手来源入口

- [MAVEN-ERE（EMNLP 2022）](https://aclanthology.org/2022.emnlp-main.60/)
- [MAVEN-ERE 官方仓库](https://github.com/THU-KEG/MAVEN-ERE)
- [Chen et al.（ACL 2024）](https://aclanthology.org/2024.acl-long.512/)
- [Teach-LLM-LR 作者仓库](https://github.com/chenmeiqii/Teach-LLM-LR)
- [LLMERE（COLING 2025）](https://aclanthology.org/2025.coling-main.500/)
- [LLMERE 作者仓库](https://github.com/HerbertHu/LLMERE)
- [Wei et al.（Findings EMNLP 2024）](https://aclanthology.org/2024.findings-emnlp.1/)
- [Xiang et al.（Findings ACL 2025）](https://aclanthology.org/2025.findings-acl.43/)
- [GLM4ECI 作者仓库](https://github.com/zhanchuanhong/GLM4ECI)

## 审计边界

- 本轮没有训练模型，没有运行 GPU，也没有把 published prediction replay 写成模型复现。
- 临时作者仓库、拆分结果与论文 PDF 均位于 `/tmp`；项目内只新增本审计文档和既有规划记录。
- GitHub 404、未检索到作者仓库等结论只按审计日访问下界表述，不宣称未来不可恢复。
- 原始 DR-G 保留不改；发生冲突时，以本审计中已本地执行的 split、计数、哈希和 evaluator 结果为准。
