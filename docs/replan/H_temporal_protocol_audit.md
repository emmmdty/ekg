# DR-H 本地一手审计：MATRES / TB-Dense 时间关系资格判定

> ⚠️ **口径更新（2026-08-27）**：本文的数据/代码事实继续有效；“当前 NO-GO”是按现已撤销的
> “两个近期独立作者原包必须在完全相同原 split 上零修补闭环”资格门作出的历史结论。按当前论文规则，
> MATRES 可作为关系章节的候选 benchmark：本项目可自行冻结公开 manifest，在同一 split/evaluator 上
> 重跑 Roccabruna、TCT 或其他方法。Roccabruna 87.6 仍不能直接横比，但 split 冲突不再取消其方法资格。

> 审计日期：2026-08-27（Asia/Taipei）
>
> 原始报告：`docs/replan/H_temporal_protocol.md`
>
> 来源导出：`docs/replan/H_temporal_protocol.pdf`

## 结论

DR-H 的核心动作结论**通过本地事实验收**：当前不能把 MATRES 或 TB-Dense 时间关系分类升格为论文
主任务，也不应启动 GPU baseline reproduction。原报告正确识别了数据许可与近期双 baseline 两个硬门，
并正确把 TCT 官方附件列为最可能改变结论的最后一项静态检查。

本地审计完成了这项检查，结论比原报告更确定：**TCT 官方 `software.zip` 既不属于候选的固定
TimeBank/AQUAINT split，也不是先删除 VAGUE 的 724-pair VØ evaluator，而且代码包不能原样执行。**
因此它不能成为第二条同协议 baseline，继续做 CPU/GPU 模型 smoke 已无决策价值。

本地审计也补齐了原报告未完成的 annotation census。对当前 CogComp MATRES release，文档 split、
六列 relation rows、去 VAGUE 后的 pair/label universe 均已精确冻结，故这些门可从 CONDITIONAL 升为
PASS。但这不补齐模型实际需要的 TempEval TML 文本及其许可记录。

此外还发现一项原报告没有消解的论文—代码冲突：Roccabruna 2024 论文附录报告 MATRES
9,074/2,133/724，而作者 formatter 按 TimeBank/AQUAINT/Platinum 固定划分时，本地 annotation 应为
5,481/5,728/724。仓库没有发布处理后数据、预测、结果或 checkpoint，故论文的 87.6 不能直接登记为
候选固定 split 的公开可比成绩。

旧资格门下的结论为：**NO-GO**。当前项目决策为：**保留为可统一重跑的关系任务候选**；是否采用由
Ch2 的整体方法与实验成本决定，不再由作者原 split 是否完全一致一票否决。

## 原始报告与 PDF 验收

- Markdown 共 545 行、43,951 bytes；保留 101 个会话内部 citation token、51 个原始 URL 字面量，
  文末另有 plain-text source registry。
- PDF 共 17 页、1,080,000 bytes，可搜索、未加密，文本层约 29,069 characters；含 103 个 URI
  annotations、19 个唯一 URI。
- 原始 Markdown/PDF 均未修改；本审计以 Markdown 恢复完整论证，以 PDF 交叉确认正文和附件身份。

## 本地冻结的 MATRES annotation

项目内 `data/raw/matres/{timebank,aquaint,platinum}.txt` 与 CogComp/MATRES 审计提交
`2ca4c8c122899d3a1ea77ef805ed048f06c9047f` 的三个 Git blob 完全一致：

| split | rows | docs | label counts | 文件 SHA-256 |
|---|---:|---:|---|---|
| TimeBank / train | 6,336 | 182 | BEFORE 3,229 / AFTER 2,044 / EQUAL 208 / VAGUE 855 | `217c7a5b51c7fa5fe5feed36dd10c6feed5e3dfa4dd736d45ccb37bea21bcb09` |
| AQUAINT / dev | 6,404 | 73 | BEFORE 3,233 / AFTER 2,263 / EQUAL 232 / VAGUE 676 | `eb42b25d873809dfa0494ee0564da30f153942a2af663f5a74660928210a340b` |
| Platinum / test | 837 | 20 | BEFORE 424 / AFTER 269 / EQUAL 31 / VAGUE 113 | `346be061630c01e8ac2624e16ed46b24506bf152334b0dee275ada7943d70daa` |

三份文件均为每行恰好六个 TSV fields；没有 exact duplicate row，也没有重复 directed pair ID。
排序后的 doc-ID manifests 为：

| split | manifest SHA-256 |
|---|---|
| train | `853b2ddc2c3c2c95206d1844a35f55d7657442a4061209664ff503cf2a6f5063` |
| dev | `0ef1f5b96639bffdd584a3525a1cb6e278ebd9bb4dd251853abf7e0cbca7d8ac` |
| test | `61e8bca9cbc6e027357aef1cb096819ab1198d2f05d6d60d4a19cafaafefbf32` |

按原文件顺序删除 gold `VAGUE` 后，候选协议的三类 pair universe 为：

| split | pairs | label counts | ordered manifest SHA-256 |
|---|---:|---|---|
| train | 5,481 | BEFORE 3,229 / AFTER 2,044 / EQUAL 208 | `77d3d20c66ec4e8e059b8be785a239fffe1883d9f6a3f91da79a49f6f03b386c` |
| dev | 5,728 | BEFORE 3,233 / AFTER 2,263 / EQUAL 232 | `566526b29af875a342a9e9172da7e5549a49d3ec4c49feb64572db7c17ee19f9` |
| test | 724 | BEFORE 424 / AFTER 269 / EQUAL 31 | `14a707f2348d86c7c3611943ead3acc6e73402602da36a9fed0f10e307235be6` |

因此可以冻结 annotation-level 协议：

> `TimeBank=train / AQUAINT=dev / Platinum=test / gold directed main-axis verb-event rows /
> remove VAGUE before loading or scoring / {BEFORE, AFTER, EQUAL} / no closure / 724 test pairs`。

这只能证明 annotation 的 split 与 pair universe。项目内没有 `.tml` / `.timeml` TempEval source corpus，
也没有 LDC2006T08/TempEval archive 名、取得日期、许可回执或 archive SHA-256。Roccabruna formatter 必须
从 TML 的 `<TEXT>`、`<EVENT>`、`<MAKEINSTANCE>` 重建模型输入；六列 annotation 不能独立训练文本模型。

## TCT 官方 software.zip 静态审计

官方附件来自 [ACL Anthology](https://aclanthology.org/attachments/2024.findings-emnlp.47.software.zip)。
下载副本为 1,364,620 bytes，SHA-256：

`dbf11f4ad3cabd5b721bb18d8e37dcb51f5da0cc6878f3ff9522b87622160e4e`

ZIP 完整性校验通过，共 52 个文件、解压后约 32,999,033 bytes。它包含已处理的 MATRES/TB-Dense
JSON 和部分 BART 训练/测试模块，但没有 README、requirements/environment、LICENSE、统一入口、
参数构造器、原始数据预处理、checkpoint 或 Git 历史。

### 协议不兼容

| TCT 文件 | rows | label counts |
|---|---:|---|
| MATRES train | 10,888 | BEFORE 5,483 / AFTER 3,819 / EQUAL 359 / VAGUE 1,227 |
| MATRES val | 1,852 | BEFORE 942 / AFTER 662 / EQUAL 59 / VAGUE 189 |
| MATRES test | 837 | BEFORE 427 / AFTER 271 / EQUAL 30 / VAGUE 109 |

train+val 恰为 12,740，等于本地 TimeBank 6,336 + AQUAINT 6,404，说明 TCT 把二者合并后重新切成
10,888/1,852，而不是固定 `TimeBank=train, AQUAINT=dev`。test 虽同为 837 条，标签分布也与当前
CogComp Platinum 的 424/269/31/113 不同，且 JSON 不含 doc ID / event-instance ID，无法恢复 exact
pair manifest。

TCT 的 test evaluator 让四类共同参与预测，然后用
`classification_report(..., labels=[BEFORE, AFTER, EQUAL])` 排除 VAGUE 标签，并把其中的 micro avg
覆盖为最终 `micro_f1`。VAGUE gold 上的非 VAGUE 预测仍会造成 false positive，非 VAGUE gold 被预测为
VAGUE 仍会造成 false negative；这是 **VAGUE-as-negative（Vneg）**，不是先删除 113 个 VAGUE rows
后对 724 条做三分类 accuracy 的 **VØ**。

### 执行链不闭环

- `Classifier/dataset.py` 只定义 `BartDataset` 与 `SmallBartDataset`，但训练/测试模块导入不存在的
  `T5Dataset`。
- 多个模块还导入归档中不存在的 `Classifier.myModel`、`Classifier.soft_embedding`。
- 训练用 `torch.save(model.state_dict(), *.bin)` 保存权重，测试却把该 `.bin` 路径直接交给
  Hugging Face `from_pretrained`。
- 归档没有构造 `args` 的 caller，也没有创建 save directories 或给出可执行命令。

因此 TCT 不是“只差一次 smoke”的同协议对手，而是**协议、数据版本和执行闭环均不合格**。

## Roccabruna / LLMs-TRC 审计

官方仓库 [BrownFortress/LLMs-TRC](https://github.com/BrownFortress/LLMs-TRC) 审计提交为
`41eb1ed036cd4b5741b17dc07f809311cc915016`，最后提交时间 2024-10-22，代码许可证为 MIT。

### 能确认的部分

- `matres_opener.py` 把 TimeBank/AQUAINT/Platinum 分别映射为 train/valid/test，并从 MATRES rows 与
  TempEval TML event IDs 构造 relation instances。
- `main.py` 对 MATRES 默认令 train/dev/test 的 `skip_vague=True`；没有 closure。
- evaluator 对完整三类调用 sklearn `classification_report`。在每个 test item 恰有一个 gold 与一个
  prediction、三类全部计分时，micro precision = micro recall = micro-F1 = accuracy。
- 正式论文明确完全删除 MATRES VAGUE，并报告 RoBERTa 使用单张 NVIDIA 3090 Ti 24GB。

这些证据证明仓库**可以表达** `MATRES-N837-VØ`，并证明 RoBERTa 路径具有约 27GB 的可信纸面可行性。

### 不能确认的部分

- 论文附录列出的去 VAGUE MATRES train/dev/test 是 **9,074/2,133/724**；当前 formatter 加本地
  official rows 则应为 **5,481/5,728/724**。论文只称 official split，未给重切分 seed/manifest。
- 仓库的 `data/`、`outputs/`、`bin/` 均只有 `.keep`；没有处理后 pkl、实验 results、predictions 或
  checkpoint 可判断论文 87.6 使用了哪套 train/dev。
- README 推荐的 `run_exps.sh` 不能原样运行：三个 dataset 被写成一个数组元素；
  `model_name_large` 被注释却仍使用；引用的 large config 文件名在仓库中不存在。
- requirements 含 `torch==2.1.0.dev20230518` 等开发版/环境特定依赖；仓库也不包含上游 TML 数据。

所以 Roccabruna 是**代码级条件候选**，而不是一个已经有 exact fixed-split published score 的无条件
baseline。论文 87.6 只可在其论文自身 9,074/2,133/724 口径下引用，不能移植为本审计固定轴的对手线。

## 数据许可边界

- CogComp/MATRES annotation 仓库公开可下载，但当前没有显式 LICENSE；GitHub public 不等于允许任意
  再分发。LLMs-TRC 的 MIT 许可证只覆盖该仓库代码，不能扩张到上游新闻文本或 MATRES annotation。
- TimeBank 1.2 由 LDC 以 LDC2006T08 和用户协议分发；不是无需协议即可公开镜像的数据。
- TempEval/TimeML 页面说明 source texts 的版权属于各内容持有人并限定学术用途。
- 当前项目只有 annotation TSV，没有训练所需 source TML 和相应取得/许可/hash 记录。

因此“annotation protocol 可冻结”不等于“完整模型输入完全公开且可合法随实验包分发”。数据与许可门
继续 FAIL；本审计不作超出一手页面文字的法律解释。

## 修正后的 Go/No-Go 门

| 门槛 | 本地状态 | 依据 |
|---|---:|---|
| Annotation 获取与版本 | **PASS** | 三份 TSV 与 CogComp commit 的 Git blobs 完全一致，文件 hash 已冻结 |
| 完整数据与许可 | **FAIL** | annotation 无显式许可；TML 不在项目内，TimeBank/TempEval 有协议与版权限制 |
| Annotation split | **PASS** | 182/73/20 exact doc manifests 已排序并冻结 SHA-256 |
| Pair / labels | **PASS** | 六列 rows 无重复；VØ 后为 5,481/5,728/724，ordered manifests 已冻结 |
| Evaluator 定义 | **PASS** | 三类 single-label micro-F1 = accuracy；VØ 输入边界明确 |
| 已发表成绩的 exact split 可追溯性 | **FAIL** | Roccabruna 论文 9,074/2,133 与 formatter 5,481/5,728 冲突，且无结果产物 |
| 两个独立近期可执行对手 | **FAIL** | Roccabruna 仅为条件候选；TCT 是重切分+Vneg 且附件不闭环；其余候选不同轴或无闭环 |
| 单张约 27GB | **FAIL / 不进入** | Roccabruna RoBERTa 有 24GB 实证，但没有第二个合格同轴对手；GPU smoke 不能修复协议门 |

## 决策与下一步

1. **不运行 GPU、不训练 Roccabruna/TCT、不修改项目代码、不进入章节设计。**
2. 保留本轮冻结的 MATRES annotation manifests 作为协议资产；它们不代表 source text 许可已解决。
3. 不再为 `MATRES-N837-VØ` 修补 TCT。修补缺失模块或把 Vneg 改成 VØ 会成为我们的新实现，不能制造
   第二条作者 baseline。
4. 只有同时取得 source TML 的可审计使用依据，以及两个独立近期方法在同一 split/pair/evaluator 上的
   作者执行闭环与成绩，才重新打开本方向。
5. 若继续扩大候选池，应转向具有公开固定 split 与多个近年方法的事件共指基准，先做同样的静态资格
   审计；仍先查数据、对手和 evaluator，不先做 GPU。

## 一手来源入口

- [MATRES 官方 annotation 仓库](https://github.com/CogComp/MATRES)
- [TimeBank 1.2 / LDC2006T08](https://catalog.ldc.upenn.edu/LDC2006T08)
- [TimeML / TempEval resources](https://timeml.github.io/site/timebank/timebank.html)
- [Roccabruna et al. 2024](https://aclanthology.org/2024.emnlp-main.1136/)
- [Roccabruna 作者仓库](https://github.com/BrownFortress/LLMs-TRC)
- [TCT 2024](https://aclanthology.org/2024.findings-emnlp.47/)
- [TCT 官方 software.zip](https://aclanthology.org/attachments/2024.findings-emnlp.47.software.zip)

## 审计边界

- 本轮没有训练模型、没有运行 GPU、没有下载模型权重，也没有把静态代码阅读写成结果复现。
- TCT archive 与 LLMs-TRC 临时克隆位于 `/tmp`；项目内只新增本审计文档并更新规划记录。
- 本轮对数据许可只记录公开页面、仓库许可证与本地材料是否存在，不提供法律意见。
- 原始 DR-H 保留不改；发生冲突时，以本审计的本地 hashes、counts、代码与附件检查为准。
