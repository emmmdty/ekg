# MATRES / TimeBank-Dense event temporal relation 主指标协议复现与许可审计

## 执行结论与身份校正

**Executive verdict：NO-GO。**

截至 **2026-08-27**，在不降低你给定标准的前提下，我没有找到 MATRES 或 TimeBank-Dense 上一条能够同时满足以下条件的冻结主指标轴：

> **完全公开且许可可证明的数据输入 + exact split / pair manifest / label / evaluator 可冻结 + 至少两个互相独立的 2024–2026 正式方法拥有当前可取得的作者执行闭环 + 两者均有可信单张约 27GB GPU 路径。**

目前最接近的是 **MATRES 的 Ning/CogComp 扩展版、TimeBank/AQUAINT/Platinum 文档角色、gold MATRES event-pair classification、test 中移除 `VAGUE`、三类 `BEFORE/AFTER/EQUAL`、micro-F1/accuracy 轴**。其中 Roccabruna et al. 2024 的 **RoBERTa 路径**是一个很强的第一基线候选：正式 EMNLP 2024 论文、作者代码公开、MATRES/TB-Dense 预处理和 encoder 训练代码存在，而且论文明确报告 RoBERTa 实验使用 **单张 RTX 3090 Ti 24GB**；但同一论文的 LLM 实验使用 **4×A100 80GB**，两条路径不能合并判定。citeturn26search3turn11view0turn13view1

问题在于**第二个同轴、独立、近期、公开执行闭环**仍未锁定：

| 候选 | 与最优 MATRES `VAGUE`-drop 轴 | 作者执行闭环 | 约 27GB 证据 | 能否计第二对手 |
|---|---|---|---|---|
| Roccabruna et al. 2024 RoBERTa | 高度匹配 | 有，但 wrapper 有小缺陷 | **论文实证 24GB** | **可计第一候选** |
| ConTempo 2024 | **不匹配**：`VAGUE` 留在评测中作为 negative | 当前作者 GitHub 未取得 | GPU 未声明 | 否 |
| TCT 2024 | 论文口径较接近：排除 `VAGUE` | ACL 有 software.zip，但本轮未能取得/审计其 tree、history、license | GPU 未声明 | **不能计** |
| LLMERE 2025 | **不匹配**：生成式候选/evaluator 保留 `VAGUE` gold 为 negative background | repo 缺训练入口 | A100 40GB | 否 |
| GDLLM 2025 | 论文口径较接近：排除 `VAGUE` | 未取得官方 repo | A800 80GB | 否 |

因此，即使暂时搁置数据许可问题，**“两个独立近期同轴可执行 baseline”这一门已经 FAIL**。再加上 MATRES 与 TB-Dense 都需要回到 TimeBank/TempEval 来源文本，而 TimeBank 当前通过 LDC 协议分发，MATRES annotation 仓库本身又没有显式 license，严格意义上的“完全公开数据”也不能判 PASS。TimeBank 1.2 当前 LDC 目录明确列出 `LDC User Agreement for Non-Members`，而 TimeML 页面对 TempEval source text 明确提醒文本版权属于各内容持有人、仅供 academic purposes。citeturn27search1turn27search3

所以本轮不是 **CONDITIONAL GO**。剩余缺口不只是一次 CPU/GPU smoke：它还包括**数据许可、第二基线代码闭环和第二基线 27GB 证明**。按照你的判定规则，必须是 **NO-GO**。

这里还需要先纠正几个容易造成“看起来已经有两个对手”的身份/协议混淆。

**MATRES 2018 论文和今天常用的 275-document MATRES 不是同一个实验协议。** 数据论文 *A Multi-Axis Annotation Scheme for Event Temporal Relations* 的正式身份是 Qiang Ning, Hao Wu, Dan Roth，ACL 2018，ACL ID `P18-1122`，DOI `10.18653/v1/P18-1122`。论文最初在 36 个 TB-Dense documents 上做 pilot，并沿 TB-Dense 的 22/5/9 train/dev/test 角色实验；后来作者把 MATRES 扩展到整个 TempEval-3 的 TimeBank/AQUAINT/Platinum 集合。当前官方仓库 README 自己明确区分了这两件事。citeturn26search1turn25view1turn25view4  
官方仓库：`https://github.com/CogComp/MATRES`；当前审计 commit：`2ca4c8c122899d3a1ea77ef805ed048f06c9047f`。仓库 README 明说当前 release 分成 `timebank.txt`、`aquaint.txt`、`platinum.txt`，并且 MATRES 只包含 verb events、只保留 main-axis relations。fileciteturn12file0

**MATRES 也不是只有一个“official test”。** ConTempo Appendix C 明确指出 Ning 官方 GitHub 版本的 Platinum test 有 **837 relations**，另一个 Wang et al. 系谱版本为 **818**；ConTempo 选择前者。当前 CogComp `platinum.txt` 本轮也静态确认最后一个非空数据行为第 837 行。citeturn14view1 fileciteturn15file0 fileciteturn16file0

**ConTempo 不能和 Roccabruna 仅凭“都用 MATRES、都报 F1”就放在一列。** ConTempo §4.1 明确说 MATRES 和 TBD 的 `VAGUE` **保留在 evaluation 中并作为 negative label**；Roccabruna §5.2 则把 `VAGUE` 从 MATRES/TB-Dense 实验数据中完全移除。前者的 `VAGUE` gold pair 仍能通过 false-positive/false-negative 影响 micro-F1，后者这些 pair 根本不进入 test list，所以 scorer 输入已经不同。citeturn14view0turn11view0

**`2025.findings-emnlp.1010` 不是 MATRES/TB-Dense baseline。** Yi Fan 与 Michael Strube 的 *Consistent Discourse-level Temporal Relation Extraction Using Large Language Models* 使用的是 TDD-Man、MAVEN-ERE 和 **TimeBank**；论文只是借用了 TB-Dense 的 partition strategy，并把 TimeBank relation schema 简化为类似 TB-Dense 的标签，不等于使用 TB-Dense 数据本体。它必须从本轮候选中排除。citeturn28search2turn13view8

**TB-Dense 本体也不是天然的“纯 event-event pair classification”。** 官方 CAEVO 页面定义它为 36 个 TimeBank documents、约 12,000 个 event/time-expression temporal links；annotation universe 包括同句和相邻句中的 TimeBank events **以及 timex entities**。Roccabruna 的实际 `tbdense_opener.py` 更进一步把 `TIMEX3` 直接包装为与 events 同层的 `Event` 对象。因此这条公开代码路径的 TB-Dense headline setting 不能直接冒充你要求的“event-event only”轴。citeturn27search0 fileciteturn58file0

前一轮方法工程交叉核验对 LLMERE 40GB、encoder/seq2seq 风险低于 7B/8B PEFT 等判断与本轮一手材料一致；但本报告没有沿用它的资格结论，而是重新从论文、官方仓库和 scorer 建立。fileciteturn0file3

## MATRES 与 TB-Dense 协议地图

### MATRES protocol map

MATRES 至少需要拆成以下几条轴，不能只写一个“MATRES”。

| 轴 | Gold / split | `VAGUE` | Test / evaluator 特征 | 本轮判断 |
|---|---|---|---|---|
| **M-Pilot** | 2018 paper，36 TB-Dense docs，22/5/9 | 四类 | 原始数据论文实验 | 历史 sanity，不是现代 275-doc 轴 |
| **M-Ning837-VØ** | CogComp 扩展 MATRES；TimeBank/AQUAINT/Platinum | **删除** | 三类 B/A/E；Roccabruna 风格 | **最合资格轴** |
| **M-Ning837-Vneg** | 同 Ning test 版本 | **保留为 negative** | positive-class micro-F1 | ConTempo/LLMERE 风格；与 VØ 不兼容 |
| **M-Wang818** | Wang/JCL 系谱 test | 依方法 | test gold 少 19 pairs | 独立版本 |
| **CleanMATRES** | ConTempo 重标 test | test 无 `VAGUE`，且修订 gold | 新 gold test | 独立 benchmark，不可代替原 MATRES |

MATRES 当前官方 annotation 仓库在 commit `2ca4c8c...` 中包含 `timebank.txt`、`aquaint.txt`、`platinum.txt` 与若干 raw annotation CSV；Git tree 显示三份主文件的 Git object IDs 分别为：

| 文件 | Git blob object |
|---|---|
| `timebank.txt` | `0896639b276423e188aefdb59cde407ec8082189` |
| `aquaint.txt` | `e07080ddc627521f9f4a53c4463efa8f0cae227e` |
| `platinum.txt` | `e9861807cc1098553d75a22b60e09b8cc1e9af69` |

这些是 Git object IDs，**不是 SHA-256**。本轮工具能读取 GitHub content，但没有把三份 raw bytes 落到本地 sandbox，因此我没有伪造 SHA-256；这是最终冻结前必须做的一次本地小检查。仓库 tree 及文件对象可在这里核对：`https://github.com/CogComp/MATRES/tree/2ca4c8c122899d3a1ea77ef805ed048f06c9047f`。fileciteturn13file0

公开 relation 文件的格式是：

`docid  verb1  verb2  eiid1  eiid2  relation`

并且 README 明确说明 eiid 与 TempEval-3 对齐、只包含 verb events、只保留 main-axis relations。换言之，**MATRES 不是“枚举全文所有 event pairs”数据集**：最稳妥的 candidate universe 是 annotation 文件明确列出的 gold-linked event pairs。fileciteturn12file0

标签原始全集为 `BEFORE / AFTER / EQUAL / VAGUE`。例如当前 `platinum.txt` 开头同时出现 `VAGUE`、`BEFORE`，末尾仍包含 `AFTER`；所以把 MATRES 描述成天然三类是不准确的，三类是后续 evaluation preprocessing 的结果。fileciteturn14file0 fileciteturn15file0

在数据来源方面，四个概念必须分开：

| 问题 | MATRES 结论 |
|---|---|
| annotation 当前可下载 | **是** |
| annotation 有明确开源许可证 | **没有证据**；GitHub API 当前 `license: null` |
| raw source text 可无条件公开下载 | **否** |
| 本项目本地已有 annotation | **是，但不改变前两项** |
| source text 可随项目再分发 | **没有依据判定可以** |

CogComp/MATRES 当前 GitHub metadata 的 `license` 为 `null`，因此“仓库 public”不能自动升级成“annotation 可任意再分发”。fileciteturn57file0

原文文本来自 TempEval-3 系谱中的 TimeBank、AQUAINT、Platinum。TimeBank 1.2 当前 LDC catalog 明确是 183 篇 English news articles、`LDC2006T08`，许可项是 **LDC User Agreement for Non-Members**，并提供 members/non-members licensing instructions；这不是“无需账号/协议即可公开镜像”的数据。citeturn27search1turn27search2

TimeML 官方页面又明确说 AQUAINT TimeML 有 73 个 news reports 并有 1.0 download；同时对 TempEval corpus 的 source data 提醒版权属于不同内容持有者，只能用于 academic purposes。citeturn27search3

因此，**MATRES annotation 可下载 ≠ MATRES 训练文本完全公开**。Roccabruna 的实际 preprocess 也证明模型确实需要这些 source TML，而不是只需要六列 relation 文件：它从 `original_data/TempEval/TimeBank`、`AQUAINT`、`te3-platinum` 中读 TML `<TEXT>`、`EVENT` 和 `MAKEINSTANCE`，再和 MATRES eiid 关联。fileciteturn18file0  
代码位置：`https://github.com/BrownFortress/LLMs-TRC/blob/41eb1ed036cd4b5741b17dc07f809311cc915016/data_formatter/matres_opener.py`

split 方面，Roccabruna 的作者代码明确：

- `timebank.txt → train`
- `aquaint.txt → valid`
- `platinum.txt → test`

而且最后按上述 membership 输出 `train.pkl / valid.pkl / test.pkl`。fileciteturn18file0 fileciteturn20file0

现代论文常见的文档统计为约 **182 / 73 / 20**，总计 275；这与 TimeBank source 本身的 183 docs 之间存在一个需要通过 exact manifest 解释的差额。本轮没有把三份 relation 文件的 `unique(docid)` 导出、排序并 SHA-256，因此我不会把“182/73/20”升级成已经 checksum 锁死的 split。LLMERE 论文也报告 182/73/20，这支持统计口径，但不能替代逐 ID manifest。citeturn12view9turn13view5

尤其不要直接拿 Roccabruna Appendix 中经过模型 preprocessing 后的 instance counts 当 raw pair counts：作者代码在 dataset construction 中还有 label filtering/可能的方向处理；真正的冻结 pair manifest 应该从 official annotation rows 直接建立，然后再验证模型 loader 对它有没有 duplication。当前官方 Platinum raw relation row 可静态锁为 **837**；TimeBank 文件本轮静态确认最后非空行为第 **6336** 行；AQUAINT 总 relation-row count 本轮没有完成，所以全 split exact annotated-pair census 仍标 **未完成**。fileciteturn46file0

### TB-Dense protocol map

TimeBank-Dense 的协议分叉反而更多。

正式数据论文身份可以用 Nathanael Chambers、Taylor Cassidy、Bill McDowell、Steven Bethard 的 *Dense Event Ordering with a Multi-Pass Architecture* 锚定：TACL 2014，ACL ID `Q14-1022`，DOI `10.1162/tacl_a_00182`。citeturn26search2  
论文：`https://aclanthology.org/Q14-1022/`  
官方数据/CAEVO：`https://www.usna.edu/Users/cs/nchamber/caevo/`

官方 CAEVO 页面目前明确区分四份 TB-Dense release：

- full annotation over TimeBank entities；
- full annotation + fine-grained `VAGUE`；
- **filtered for TempEval-3 entities**，这是 Chambers et al. 2014 published experiments 所用版本；
- filtered + fine-grained `VAGUE`。citeturn27search0

这已经说明“TB-Dense official”本身不是一个足够精确的协议名字。

官方页面同时说明 corpus 约 **12,000 temporal links / 36 TimeBank documents**，pair generation 覆盖同句与相邻句 event/timex entities；原始 split 为 train/dev/test，dev/test docs 位于官方 evaluate code 变量中。citeturn27search0

对于本轮目标，TB-Dense 有一个更严重的边界问题：**原始 task universe 包括 event–timex links**。Roccabruna 当前代码读取 `TimebankDense_annotation.txt` 后把 label `v/a/b/ii/i/s` 映射为六类，并把 `TIMEX3` 直接放进 `events` 集合；所以其 headline TB-Dense 数据处理并不是纯粹“given two event mentions → event-event relation”。fileciteturn58file0

如果我们现在自己过滤成 E–E-only，那已经产生一个新的 `TB-Dense-E-E` 子轴，必须重新锁 test pair IDs 和 evaluator；不能说它和论文原始 headline 数字同协议。

此外近期论文又产生两个不兼容口径：

**Roccabruna 2024** 默认 `skip_vague=True`，即 train/dev/test 均跳过 `VAGUE`。其 TB-Dense source 又来自 Han 的 `TEDataProcessing` 派生链，而非直接读取 CAEVO 原始 release。fileciteturn25file0

**ConTempo 2024** 明确把 `VAGUE` 留在 F1 输入中作 negative；论文的数据描述还给出与官方 36-doc 表述不一致的 article statistic，因此在没有 exact manifest 对齐之前不能假设它和 CAEVO/Roccabruna 是同一 test list。citeturn14view0turn27search0

**TCT / GDLLM** 都在论文层面称采用 prior-study split、micro-F1 并排除 `VAGUE`，但本轮没有取得足以证明 exact pair manifest 的作者 repository pipeline。citeturn13view4turn13view7

综合后，TB-Dense 不仅没有比 MATRES 更容易冻结，反而还多了 **entity-type universe（E–E vs E–T/T–T）** 这一额外协议轴，因此不进入最终推荐轴。

## 最合资格 exact protocol 与冻结规格

如果只问“哪一轴最值得留下做最终一次本地验尸”，答案是：

> **MATRES-Ning837 / TimeBank→train, AQUAINT→dev, Platinum→test / gold annotated main-axis verb-event pairs / remove VAGUE before scoring / labels {BEFORE, AFTER, EQUAL} / no closure / sklearn single-label classification metric**

以下简称 **`MATRES-N837-VØ`**。这是描述已有 Roccabruna-style setting 的审计代号，不是新 benchmark。

### 数据冻结

Annotation：

`https://github.com/CogComp/MATRES`  
commit：`2ca4c8c122899d3a1ea77ef805ed048f06c9047f`

当前 repository metadata 没有 explicit license，因此在论文主协议真正“冻结”时不能只存 Git commit；还必须保存使用依据/许可记录。fileciteturn57file0

Raw text：

`TimeBank 1.2 / LDC2006T08`  
`https://catalog.ldc.upenn.edu/LDC2006T08`

`AQUAINT TimeML / TempEval resources`  
`https://timeml.github.io/site/timebank/timebank.html`

必须保留：原始 archive 名、取得日期、许可/用户协议状态、archive SHA-256。TimeBank 不是可以随论文代码包公开重分发的“普通开源语料”，这正是当前**数据与许可门不能 PASS**的原因。citeturn27search1turn27search3

### Split 冻结

唯一允许的 split definition 应直接由 annotation manifests 导出：

`train = unique(docid in timebank.txt)`  
`dev = unique(docid in aquaint.txt)`  
`test = unique(docid in platinum.txt)`

而不是从论文中的 “182/73/20” 三个数字反向猜 IDs。Roccabruna 官方 preprocess 正是按这三个文件进行 split。fileciteturn18file0turn20file0

冻结产物至少要是三份排序后的 `docid` manifest + SHA-256，以及 test pair manifest：

`(docid, eiid1, eiid2, relation)`

这一项本轮由于没有执行本地 manifest 导出，仍是 **CONDITIONAL**。

### Gold、candidate universe 与 labels

Gold event mentions 是 TempEval/TimeML 里的既有 event mentions；MATRES relation 文件负责指定哪两个 main-axis verb-event instances 构成 gold pair。MATRES README 明确只包含 verb events/main-axis relations。fileciteturn12file0

`MATRES-N837-VØ` 的 test universe 应是 **official annotation test rows 去除 gold `VAGUE` 后的 exact rows**，而不是：

- 全文枚举 all event pairs；
- 只枚举同句 pair；
- 自己增加邻句 window；
- closure-expanded pairs；
- 把 inverse pair 当新的 test examples；
- 用 CleanMATRES 取代 original Platinum；
- 把 Wang 818-pair 版本混进来。

原始标签全集是 `BEFORE / AFTER / EQUAL / VAGUE`；冻结轴去掉 `VAGUE` 后为三个 target labels。Roccabruna 的 `main.py` 默认 `is_skip_vague_train/dev/test=True`；只有显式 `--not_skip_vague` 才改变行为，而且 MATRES 特例甚至仍然保持 test 跳过 `VAGUE`，因此命令行 flag 必须记录。fileciteturn25file0

本轮检查到的 Roccabruna MATRES formatter 没有执行 temporal transitive closure：它只是将 MATRES relation row 映射回 TML events，并把 relation objects 写入 split pickle。fileciteturn20file0

### Evaluator 冻结

Roccabruna encoder evaluator 位于：

`encoder_architecture/utils/support.py`  
commit `41eb1ed036cd4b5741b17dc07f809311cc915016`  
`https://github.com/BrownFortress/LLMs-TRC/blob/41eb1ed036cd4b5741b17dc07f809311cc915016/encoder_architecture/utils/support.py`

它收集每个 gold example 的单标签 prediction，然后调用：

`sklearn.metrics.classification_report(... labels=range(len(mapping)), output_dict=True, zero_division=0)`。fileciteturn23file0

对于**所有 test items 恰好一个 gold label、恰好一个 prediction，并且三类全部列入 scorer**的标准 single-label multiclass classification，micro precision = micro recall = micro-F1 = accuracy。因此论文称 “micro-F1” 而代码结果对象使用 `accuracy` 并不自动意味着协议不同；这两个量在这个具体条件下数学上相同。

但只要像 ConTempo/LLMERE 那样把 `VAGUE` pair 留在输入、仅从 target label list 中排除，micro-F1 就**不再等于在三类子集上的普通 accuracy**，因为 VAGUE gold 上预测成正类仍会造成 FP，而正类预测成 VAGUE 会造成 FN。这正是为什么不能用“都是 micro-F1”把它们合并。

Roccabruna `main.py` 还用 dev `accuracy` 选 best checkpoint，然后在改善时评 test，并按 `config["runs"]` 保存每次 report。fileciteturn26file0 当前尚未本地 replay `print_tab.py/stat_reader.py` 来确认论文 headline 是“每 run 后取均值”还是某个特定输出字段，所以最终 scorer aggregation 仍有一个小的 CPU-level closure 缺口。

## 逐论文审计记录

**MATRES 数据论文 — *A Multi-Axis Annotation Scheme for Event Temporal Relations*.**  
正式身份：Qiang Ning, Hao Wu, Dan Roth；ACL 2018；ACL ID `P18-1122`；DOI `10.18653/v1/P18-1122`；pages 1318–1328。citeturn26search1  
协议：论文是 36-doc pilot，不等于后来 GitHub 的 entire-TempEval3 release。其核心标签定义围绕 event start-points，含 `BEFORE/AFTER/EQUAL/VAGUE`。citeturn25view4  
repository：`https://github.com/CogComp/MATRES`，master HEAD `2ca4c8c...`，当前无 repository license。fileciteturn57file0  
missing：原始文本许可不由这个仓库解决；没有官方现代统一 evaluator。  
资格：**数据 annotation 身份锚，可用；不能拿 2018 pilot score 充近期 baseline。**

**TimeBank-Dense 数据论文 — *Dense Event Ordering with a Multi-Pass Architecture*.**  
正式身份：Nathanael Chambers, Taylor Cassidy, Bill McDowell, Steven Bethard；TACL 2014；ACL ID `Q14-1022`；DOI `10.1162/tacl_a_00182`。citeturn26search2  
官方数据：`https://www.usna.edu/Users/cs/nchamber/caevo/`，36 TimeBank docs、约 12k temporal links，并公开区分 full、fine-grained VAGUE、TempEval-3-filtered 等版本。citeturn27search0  
repository：CAEVO public GitHub 为 `https://github.com/nchambers/caevo`；本轮静态看到 master 当前最新 commit `86af3c584d7cc70ee09ef851971f055c568246a9`。  
scope：原始 link universe 包含 events 与 time expressions，并不天然满足本轮纯 E–E 限制。  
资格：**数据/历史 scorer 身份锚；不是 2024–2026 对手。**

**Roccabruna, Rizzoli, Riccardi 2024 — *Will LLMs Replace the Encoder-Only Models in Temporal Relation Classification?*.**  
正式身份：EMNLP 2024；ACL `2024.emnlp-main.1136`；DOI `10.18653/v1/2024.emnlp-main.1136`；pages 20402–20415。citeturn26search3  
独立性：三位作者与 MATRES 数据论文 Qiang Ning/Hao Wu/Dan Roth 无作者交集。  
数据轴：MATRES 与 TB-Dense；MATRES 最接近 `M-Ning837-VØ`。  
split：MATRES formatter 明确 TimeBank→train、AQUAINT→valid、Platinum→test。fileciteturn18file0  
gold/candidates：从 MATRES annotation rows 和 TimeML event IDs 构造 relation instances；source text 是真实 TempEval TML，不是仓库自造 sample。fileciteturn18file0  
labels：论文 §5.2 明确去除 `VAGUE`；代码 default 也跳过 train/dev/test 的 `VAGUE`。citeturn11view0 fileciteturn25file0  
metric：论文 micro-F1；代码用 sklearn `classification_report`，完整三类条件下 headline 等于 accuracy。fileciteturn23file0  
baseline provenance：RoBERTa 是本仓库实跑路径，不是 copied-only。  
repository：`https://github.com/BrownFortress/LLMs-TRC`；main；HEAD `41eb1ed036cd4b5741b17dc07f809311cc915016`；MIT；最后 push 2024-10-22。fileciteturn3file0  
execution closure：preprocess、encoder train/test、result dump 都存在。README 也明确把 repository 分为 formatter、encoder、ICL/FT、XAI 四部分。fileciteturn8file0  
**静态缺陷**：README 指向 `run_exps.sh` 作为 rerun 入口，但脚本当前把 `"TB-DENSE MATRES TIMELINE"` 写成一个 array element，并且 `model_name_large` 定义被注释、后面仍引用它；所以 wrapper 不能被我标成“原样一键可跑”。直接调用 `main.py --dataset=MATRES --model_name=roberta-base ...` 的路径仍完整，这属于 shell-wrapper 修补，而不是 baseline 重实现。fileciteturn27file0  
environment：requirements pin 了 `transformers==4.37.2`、`scikit-learn==1.3.2`、`peft==0.10.0` 等，但 torch 是 `2.1.0.dev20230518`，README 还写明可能需要 additional packages，因此环境不能判 fully locked。fileciteturn61file0  
hardware：RoBERTa = **1×3090 Ti 24GB**；LLM = **4×A100 80GB**。citeturn13view1  
结论：**唯一可以留下作为第一近期基线的候选是论文的 RoBERTa 路径；LLM 路径不能共享 27GB PASS。**

**Niu et al. 2024 — ConTempo.**  
正式身份：Jingcheng Niu, Saifei Liao, Victoria Ng, Simon De Montigny, Gerald Penn；Findings ACL 2024；ACL `2024.findings-acl.89`；DOI `10.18653/v1/2024.findings-acl.89`；pages 1521–1533。citeturn28search0  
独立性：与 MATRES 原团队、Roccabruna 团队无作者交集。  
数据：MATRES、TimeBank-Dense、另有 CleanMATRES。  
关键协议差异：§4.1 明说 MATRES/TBD 的 `VAGUE` 被计算进 F1 input、作为 negative labels；所以不是 `M-Ning837-VØ`。citeturn14view0  
版本：Appendix C 使用 Ning 837-relation MATRES test，而不是 Wang 818 版本。citeturn14view1  
CleanMATRES：作者重新纠正 test annotations，属于新 gold，不能拿它代替原 MATRES test。citeturn12view5  
训练：Appendix A 使用 RoBERTa-large、batch 64、20 epochs、dev selection；GPU 未声明。citeturn14view1  
repository：论文给出的作者 URL 为 `https://github.com/frankniujc/contempo`；本轮动态 GitHub 审计未取得该仓库，不能写当前可运行。  
结论：**协议本身就与 Roccabruna 不同，因此即便仓库恢复，也不能成为 `M-Ning837-VØ` 的第二基线。**

**Ning et al. 2024 — Temporal Cognitive Tree.**  
正式身份：Wanting Ning, Lishuang Li, Xueyang Qin, Yubo Feng, Jingyao Tang；Findings EMNLP 2024；ACL `2024.findings-emnlp.47`；DOI `10.18653/v1/2024.findings-emnlp.47`；pages 855–864。citeturn28search3  
数据：TB-Dense、MATRES。  
split：论文称采用与 prior studies 相同划分，但没有在正文列出可 checksum 的 pair manifest。  
labels/eval：论文 Experimental Setup 使用 micro-F1 并排除 `VAGUE`，因此**论文层面**最接近 Roccabruna 的协议。citeturn13view4  
model：BART-large；TCT 的两个组成模型用于 temporal judgment / inference；batch 32、Adafactor、最多 50 epochs。citeturn13view4  
code：ACL Anthology 当前确实挂有官方 `software.zip`：  
`https://aclanthology.org/attachments/2024.findings-emnlp.47.software.zip`。citeturn28search3  
但本轮环境没有成功取得 ZIP 内容，也没有定位到可审计的作者 GitHub repository；因此无法给出 default branch、HEAD、license、Git history、imports、absolute paths、raw→train→predict→evaluate chain。论文也没有声明 GPU。  
结论：**这是最可能成为第二基线的“纸面候选”，但当前证据不足以计入门槛。** 注意它缺的不仅是一次 GPU smoke，而是代码包内容和协议 manifest 的静态验尸。

**Hu et al. 2025 — LLMERE.**  
正式身份：Zhilei Hu, Zixuan Li, Xiaolong Jin, Long Bai, Jiafeng Guo, Xueqi Cheng；COLING 2025；ACL `2025.coling-main.500`；ACL Anthology 当前页面未列 DOI；pages 7484–7496。citeturn26search0  
独立性：与上述数据团队/Roccabruna/TCT 无作者交集。  
方法不是普通 pair-wise classifier：论文和作者实现把 ERE 变成“给一个 event，一次生成所有有关联 events”的多答案 QA，以把 pairwise O(n²) 改成 O(n)。citeturn26search0  
split：论文报告 MATRES 182/73/20。citeturn13view5turn12view9  
candidate/labels：作者 `convert_temporal.py` 把 `AFTER(e1,e2)` canonicalize 成 reversed `BEFORE(e2,e1)`，并为 `EQUAL`/`VAGUE` 加 inverse；生成 target 实际只要求 `EQUAL` 与 `BEFORE`，同时按 candidate-event list 做 document partitioning，shuffle seed 42。fileciteturn52file0  
evaluator：gold 端先枚举 document 中所有 ordered event pairs，非 annotated pairs 标 `-100` 并最后过滤；**annotated VAGUE pair 没被从 gold pair universe 删除**。预测缺失关系默认映射为 `VAGUE`；`classification_report` 的 target labels 则排除 `VAGUE/NONE`。fileciteturn53file0 fileciteturn54file0  
因此它是 `VAGUE-as-negative-background` 风格，而不是 Roccabruna 的 VØ test manifest。  
repository：`https://github.com/HerbertHu/LLMERE`；main；HEAD `94d4ef2781ec7e071d38ac7fd8632a8fffbda798`；MIT；last push 2025-02-01。fileciteturn56file0  
tree：有 MATRES converter、evaluator、一些 output/eval artifacts，但当前 tree **没有模型训练入口、环境文件或 checkpoint**。fileciteturn35file0 README 也只有论文引用，没有复现命令。fileciteturn55file0  
hardware：论文使用 A100 40GB、LoRA rank 64、max sequence length 2048；这不能当成 27GB 实证。citeturn13view6  
结论：**既不同轴，又缺训练闭环，又无 27GB 论文实证；不能计第二基线。**

**Zhao et al. 2025 — GDLLM.**  
正式身份：Jie Zhao, Wanting Ning, Yuxiao Fei, Yubo Feng, Lishuang Li；Findings EMNLP 2025；ACL `2025.findings-emnlp.428`；DOI `10.18653/v1/2025.findings-emnlp.428`；pages 8080–8091。citeturn28search1  
独立性：它与 TCT **共享 Wanting Ning、Yubo Feng、Lishuang Li**，因此 TCT+GDLLM 本身也不能作为“两个独立团队”。  
数据：MATRES/TB-Dense。  
metric：论文 micro-F1，排除 `VAGUE`；split 称 follow previous studies。citeturn13view7  
repository：正式 PDF 未给出本轮可取得的官方代码仓库；截至审计日 GitHub exact-title/method 搜索也未取得作者 repo，所以代码闭环为 **未取得**，不能把论文数字当可复现 baseline。  
hardware：论文实验使用 **NVIDIA A800 80GB**；7B/8B + LoRA 的存在只说明参数高效训练范式，不证明论文 recipe 能在 27GB 上复现。citeturn13view7turn15search0  
结论：**不计。**

**Fan & Strube 2025 — *Consistent Discourse-level Temporal Relation Extraction Using Large Language Models*.**  
正式身份：Yi Fan, Michael Strube；Findings EMNLP 2025；ACL `2025.findings-emnlp.1010`；DOI `10.18653/v1/2025.findings-emnlp.1010`；pages 18605–18622。citeturn28search2  
数据：不是 MATRES/TB-Dense，而是包括 TimeBank 在内的其他 setting；借 TB-Dense split strategy 不等于用 TB-Dense gold。citeturn13view8  
结论：**范围排除。**

## 仓库执行闭环与兼容矩阵

最终轴上唯一值得完整检查的是 Roccabruna 作者仓库。

### Roccabruna 仓库静态执行审计

**Repository metadata**

`https://github.com/BrownFortress/LLMs-TRC`

default branch：`main`  
HEAD：`41eb1ed036cd4b5741b17dc07f809311cc915016`  
license：MIT  
最后 push：2024-10-22。fileciteturn3file0

历史中一个看起来可疑的 commit `fc0b21d...` message 是 `del ds`，但实际 diff 只是删除若干 `.DS_Store` 并把 `.DS_Store` 加入 `.gitignore`，并没有证据显示 MATRES/TB-Dense 数据文件曾公开后被删。fileciteturn5file0

**Raw → preprocess**

作者 README 要求先预处理原始 corpus；MATRES link 指向 MATRES repository，TB-Dense 则同时指向 Han preprocessing repo 与 Chambers 官方页面。fileciteturn17file0

MATRES formatter 实际依赖：

`original_data/TempEval/TimeBank/*.tml`  
`original_data/TempEval/AQUAINT/*.tml`  
`original_data/TempEval/te3-platinum/*.tml`  
`original_data/MATRES/{timebank,aquaint,platinum}.txt`

所以仓库**没有把所有训练输入公开打包**；需要用户自行合法取得 TempEval/TimeBank source text。fileciteturn18file0

formatter 对 event token/offset 有多处 assert，并最终输出三个 pickle；这至少能检测一部分 tokenization mismatch，而不是无声对齐。fileciteturn20file0

**Train → predict → evaluate**

`encoder_architecture/main.py` 加载三个 pickle，默认跳过 `VAGUE`，构造 RoBERTa/BERT dataset，训练后直接在 dev/test 上调用 `eval_loop`，并把 report 与 predictions dump 到 outputs。fileciteturn25file0turn26file0

所以**核心 Python 闭环存在**。问题是作者推荐的 `run_exps.sh` wrapper 当前静态有明显错误，不能写“一键运行 PASS”。fileciteturn27file0

最短的**作者代码路径**可描述为：

```text
data_formatter/matres_opener.py
    ↓
data/MATRES/{train,valid,test}.pkl
    ↓
encoder_architecture/main.py
    --dataset MATRES
    --model_name roberta-base
    --config_file configs/word_conf_linear_dual.json
    ↓
utils/support.py::eval_loop
    ↓
outputs/results.json + dump_results.pkl
```

这不是重新实现 baseline；真正需要修的只是 shell wrapper/路径和可能的现代环境兼容性。但因为本轮没有实际 clone + CPU/GPU execution，所以状态应写 **“静态闭环存在，运行未验证”**，不能写“已经跑通”。

### Independent-team and compatibility matrix

| 方法 | 团队独立 | Ning837 | 同一 `VAGUE` | exact scorer/pairs | 作者 train code | 可计 |
|---|---|---:|---:|---:|---:|---:|
| Roccabruna 2024 RoBERTa | 是 | 是 | **VØ** | 高，待 replay | **是** | 第一候选 |
| ConTempo 2024 | 是 | 是 | **Vneg** | 否 | 当前未取得 | 否 |
| TCT 2024 | 是 | 似是 | **VØ** | **未锁** | ZIP 未审计 | 否 |
| LLMERE 2025 | 是 | 似是 | **Vneg** | 否 | **无训练入口** | 否 |
| GDLLM 2025 | 与 TCT 不独立 | 论文称同系 | **VØ** | 未锁 | 未取得 | 否 |

最重要的不是“最近论文很多”，而是：**在同一个 exact MATRES-Ning837-VØ test pair manifest 上，公开证据目前只够把 Roccabruna RoBERTa 放进 executable 候选栏；TCT 只到 paper-compatible/artifact-present，尚不足 executable；其余全部因为 protocol 或代码闭环先被排掉。**

因此不能采用以下看似容易的“凑两个”办法：

`Roccabruna + ConTempo`：`VAGUE` scorer 输入不同。  
`Roccabruna + LLMERE`：candidate representation/evaluator 和 `VAGUE` 处理不同。  
`TCT + GDLLM`：作者团队有三人重叠，且 GDLLM 没有取得代码闭环。  
`MATRES 一个 + TB-Dense 一个`：数据协议不同。  
`Roccabruna RoBERTa + Roccabruna Llama`：同一论文/同一团队，且硬件条件不同。

## 基线选择、27GB 可行性与 Go/No-Go

### Two-baseline recommendation

**无法合法推荐两个。**

现阶段最多只推荐一个“进入最后本地 smoke 队列”的方法：

**Roccabruna et al. 2024 — RoBERTa path**

选择理由是它同时有：

正式 EMNLP 2024 身份；citeturn26search3  
独立于 MATRES 数据原作者；  
MATRES official-file-driven preprocessing；fileciteturn18file0  
明确的 `VAGUE`-drop setting；fileciteturn25file0  
公开 encoder train/eval code；fileciteturn23file0turn26file0  
作者论文的 **3090 Ti 24GB 单卡实证**。citeturn13view1

但即使它也只能标作**静态合资格 + 待 smoke**，不是当前“实跑 PASS”，因为：

- raw TML 许可/版本尚未在本地 hash-bound；
- `run_exps.sh` 需要小修；
- requirements 含较旧/开发版 dependency；
- split/pair manifest 尚未导出 checksum；
- 本轮未做 GPU memory measurement。

**TCT 不能作为第二推荐。** 它只是最有价值的下一检查对象：paper metric 与 `VAGUE` 处理看起来相容，ACL Anthology 也确实托管 software archive，但 archive 内容、license、raw data paths、evaluator、checkpoint、GPU 信息都未取得。citeturn28search3turn13view4 在这些内容被静态审计以前，把它列成“second executable baseline”会直接违反你的门槛。

### CPU smoke 与最小 GPU smoke

对 Roccabruna，**CPU smoke 不需要训练**。它应该只回答四件事：

一是当前合法取得的 TempEval TML 能否通过 `matres_opener.py` 全部 offset/assert；二是实际输出 unique doc IDs 是否恰为论文声称的 split；三是把每个 test relation row 生成 canonical `(docid, eiid1, eiid2, gold)` manifest 后，删除 `VAGUE` 的 pair count/hash 是多少；四是给一份人工 prediction 或已知 prediction，确认 `classification_report` 的 headline field 与论文 micro-F1 定义一致。作者 preprocess/evaluator 路径均已静态取得。fileciteturn20file0turn23file0

**最小 GPU smoke**只需一个极小训练配置验证：RoBERTa forward/backward、optimizer step、test evaluator、`torch.cuda.max_memory_allocated`，并确认没有隐藏多卡依赖；它不是启动完整论文训练。因为论文已经有 24GB 3090 Ti 实证，这一步主要是验证 2026 本地软件栈，不是在猜显存。citeturn13view1

### 27GB feasibility

| 方法路径 | 论文硬件证据 | 代码静态证据 | 本地实测 | 27GB 门 |
|---|---|---|---|---|
| Roccabruna RoBERTa | **1×3090 Ti 24GB** | 单 `cuda:0` path | 未跑 | **PASS（硬件层面）** |
| Roccabruna LLM | **4×A100 80GB** | Llama/LoRA code 有 | 未跑 | **FAIL 作为论文 recipe** |
| ConTempo | 未声明 | repo 当前未取得 | 未跑 | CONDITIONAL/不足 |
| TCT | 未声明 | BART-large，software 未审计 | 未跑 | CONDITIONAL/不足 |
| LLMERE | **A100 40GB** | LoRA r=64、2048；repo 缺 trainer | 未跑 | **FAIL 作为已证明路径** |
| GDLLM | **A800 80GB** | repo 未取得 | 未跑 | **FAIL 作为已证明路径** |

尤其不能把“LLMERE 是 LoRA”推导成“27GB PASS”。作者实际 recipe 是 A100 40GB、rank 64、2048 token，而公开 repo 甚至没有训练入口；把它改成 QLoRA 4-bit、缩 batch/length 会变成我们自己的新工程 recipe，不是当前公开 baseline closure。citeturn13view6

同理，GDLLM 使用 Qwen2.5-7B/Llama-3.1-8B 不意味着 27GB 自动成立，因为论文实测环境是 A800 80GB，而且没有取得公开 config 来证明 quantization、precision、optimizer states、gradient accumulation 等。citeturn13view7turn15search0

### Go/No-Go gates

针对最合资格的 `MATRES-N837-VØ`：

| 门槛 | 状态 | 审计理由 |
|---|---|---|
| 数据与许可 | **FAIL** | annotation public 但 repo 无 explicit license；训练所需 TimeBank source 受 LDC agreement，TempEval source 有 content-holder 限制；本地已有 annotation 不能补这个洞 |
| Split | **CONDITIONAL** | TimeBank/AQUAINT/Platinum rule 已公开，但 exact sorted ID manifests + SHA-256 尚未本地导出 |
| Pair/labels | **CONDITIONAL** | gold annotated-pair + VØ 规则清楚，但最终 test pair checksum 和 loader 是否产生 training-only inverse duplication尚未 replay |
| Evaluator | **CONDITIONAL** | Roccabruna sklearn scorer 已取得；headline aggregation 尚待一次 CPU replay 锁定 |
| 对手 | **FAIL** | 只有一个近期独立 baseline 达到公开 train/eval + 同轴候选强度；TCT 尚不能计 executable |
| 算力 | **FAIL** | Roccabruna RoBERTa 有 24GB 实证，但第二个同轴 baseline 没有合格的 ≤27GB 证明 |

根据你的规则：

> **最终判定：NO-GO。**

这不是因为 MATRES “没人做”——恰恰相反，2024–2025 有 ConTempo、TCT、LLMERE、GDLLM 等多篇正式论文。问题是它们分布在不同 `VAGUE` semantics、不同 generative/pair formulation、不同 test/evaluator 细节和不同代码可得性状态上；**论文密度没有转化成两个可审计的同协议 executable baselines。**

TB-Dense 的结论更弱：除了同样的 TimeBank 许可问题和近期 baseline 闭环问题，它还带有 official release variants 和 event/timex candidate universe，使得它不比 MATRES 更适合当前硕士论文主指标轴。citeturn27search0

## 未能核实项与最小后续本地检查

本轮仍有几项明确写作“未核实”，不能默认为常见做法。

**MATRES raw hashes 未取得。** 已锁 Git commit 和三个 Git blob objects，但不是 SHA-256。最终只需对合法取得的 annotation 和三套 TempEval source archive 各做一次 SHA-256；不需要训练。

**AQUAINT raw relation-row 总数和三 split exact unique doc-ID manifest 本轮没有完整导出。** Platinum 已静态确认 837 raw relations，TimeBank 当前文件最后非空行为 6336；但不能因此猜 AQUAINT。最终以程序化 manifest 为准。fileciteturn46file0turn15file0

**182/73/20 中 TimeBank “183 source docs → 182 MATRES docs”的具体缺失文档 ID 未锁。** LDC source 的确是 183 docs，而现代 MATRES 论文常报告 train 182；必须由 annotation `unique(docid)` 与 source basename intersection 给出答案，不能凭常识猜。citeturn27search1turn12view9

**TCT software.zip 内容未取得。** ACL Anthology 一手页面证明 archive 存在，但本轮下载环境未能把 ZIP 落地，所以没有检查 imports、README 命令、license、private paths、checkpoint、evaluator、历史。citeturn28search3 这是最值得做的下一项**静态**检查；只有它真的出现完整 author pipeline，才值得进入 CPU/GPU smoke。

**ConTempo 作者 repo 当前未取得。** 因为它无论如何属于 `VAGUE-as-negative` 轴，这不会改变 `M-Ning837-VØ` 的 NO-GO；没有必要为了凑对手把它强行修成另一轴。

**Roccabruna 完整训练未运行。** 当前能说的是“论文 24GB 实证 + 作者 Python pipeline 静态存在”，不能说本机已经跑通。`run_exps.sh` 的 wrapper 缺陷也应在复现实验记录中明确保存，而不是静默修改。fileciteturn27file0

因此，真正能改变结论的最小检查序列不是“大规模训练”，而只有：

**TCT software archive 静态验尸 → MATRES source license/hash 绑定 → exact split/pair manifest CPU replay → Roccabruna 单 batch GPU smoke → 若且仅若 TCT 确实同轴且闭环，再做 TCT 最小 GPU smoke。**

如果 TCT archive 缺训练入口、缺 exact data construction、使用不同 MATRES variant、保留 `VAGUE`、或没有可信 27GB path，其中任何一项成立，当前 MATRES 主指标轴就维持 **NO-GO**，不值得再启动完整训练。

### Plain-text Source Registry

```text
MATRES data paper
https://aclanthology.org/P18-1122/
https://aclanthology.org/P18-1122.pdf

MATRES official/current audited repository
https://github.com/CogComp/MATRES
https://github.com/CogComp/MATRES/tree/2ca4c8c122899d3a1ea77ef805ed048f06c9047f

TimeBank 1.2 / LDC
https://catalog.ldc.upenn.edu/LDC2006T08
https://catalog.ldc.upenn.edu/docs/LDC2006T08/timebank.html

TimeML corpus page / AQUAINT / TempEval
https://timeml.github.io/site/timebank/timebank.html

TimeBank-Dense data paper
https://aclanthology.org/Q14-1022/
https://aclanthology.org/Q14-1022.pdf

TimeBank-Dense / CAEVO official data and code page
https://www.usna.edu/Users/cs/nchamber/caevo/

CAEVO GitHub
https://github.com/nchambers/caevo

Roccabruna et al. 2024
https://aclanthology.org/2024.emnlp-main.1136/
https://aclanthology.org/2024.emnlp-main.1136.pdf
https://github.com/BrownFortress/LLMs-TRC

Roccabruna MATRES formatter
https://github.com/BrownFortress/LLMs-TRC/blob/41eb1ed036cd4b5741b17dc07f809311cc915016/data_formatter/matres_opener.py

Roccabruna encoder evaluator
https://github.com/BrownFortress/LLMs-TRC/blob/41eb1ed036cd4b5741b17dc07f809311cc915016/encoder_architecture/utils/support.py

Roccabruna encoder training entry
https://github.com/BrownFortress/LLMs-TRC/blob/41eb1ed036cd4b5741b17dc07f809311cc915016/encoder_architecture/main.py

Roccabruna experiment wrapper
https://github.com/BrownFortress/LLMs-TRC/blob/41eb1ed036cd4b5741b17dc07f809311cc915016/encoder_architecture/run_exps.sh

ConTempo
https://aclanthology.org/2024.findings-acl.89/
https://aclanthology.org/2024.findings-acl.89.pdf
https://github.com/frankniujc/contempo

Temporal Cognitive Tree
https://aclanthology.org/2024.findings-emnlp.47/
https://aclanthology.org/2024.findings-emnlp.47.pdf
https://aclanthology.org/attachments/2024.findings-emnlp.47.software.zip

LLMERE
https://aclanthology.org/2025.coling-main.500/
https://aclanthology.org/2025.coling-main.500.pdf
https://github.com/HerbertHu/LLMERE

LLMERE MATRES conversion
https://github.com/HerbertHu/LLMERE/blob/94d4ef2781ec7e071d38ac7fd8632a8fffbda798/data_handle_MATRES/convert_temporal.py

LLMERE MATRES evaluator
https://github.com/HerbertHu/LLMERE/blob/94d4ef2781ec7e071d38ac7fd8632a8fffbda798/eval/MATRES/eval_temporal.py

GDLLM
https://aclanthology.org/2025.findings-emnlp.428/
https://aclanthology.org/2025.findings-emnlp.428.pdf

Consistent Discourse-level Temporal Relation Extraction Using Large Language Models
https://aclanthology.org/2025.findings-emnlp.1010/
https://aclanthology.org/2025.findings-emnlp.1010.pdf

Han TEDataProcessing used by the Roccabruna TB-Dense formatter
https://github.com/rujunhan/TEDataProcessing
```