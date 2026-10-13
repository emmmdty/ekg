# 逐章指标与机制改进（2026-10-12）

作者要求执行后续工作，逐章提高指标与创新性。主表 C-41 / T087 当前持有 C5 切片，
后续 D4 → A4；不改变已定论文结构，E3 不追加实验。候选失败只停止该机制，不宣布章节改善完成。
结果与运行数字唯一入口是 `../results/PHASE_R1.md` §25.38 起。

## C5 开工自审

科研价值：对准 `EXPERIMENT_PLAN.md` 表 5-3 的官方 MUC 和 B³/CEAFe/BLANC 护栏。
已有两个角色机制周期未过主锚；独立 pair-F1 与 MUC 排序不一致，官方 antecedent 目标/解码
与项目 pair CE/平均链接不同。先核可靠控制，再检验时间信息能否区分同类事件的不同发生实例。
证据认 `PHASE_C.md` 的 pilot-r2/r3 和 R1 §25.34–§25.35，不把恢复基线当创新。

可行性：训练集、官方源码、现有评测与冻结诊断入口可读；新信号静态/CPU 核查不需要新语料。
现有 decoder checkpoint 在 5090，须对具体 smoke/audit 得到授权，不跨机搬权重。
新机制的数据覆盖、可部署预测、最近邻差异和 power 尚未通过，当前不启动方法训练。

## 执行与停止边界

1. 核既有 decoder 合同、输入 hash 与原机 CPU 预检；具体资源授权后先 smoke 再 audit。
   相同 scores 的 decoder 比较不等于复现官方 antecedent 训练目标。
2. 在冻结 train 内审计 temporal 标注、mention/事件/TIMEX 身份、候选覆盖及与真/假共指的关系。
   gold 只作信息上界，不作为可部署输入；不因标注缺失推断时间不相容。
3. 核公开最近邻正文/源码，明确同任务控制和不同信号的处理；不重写未公开外部系统冒充复现。
4. 写竞争解释、前瞻预测与候选停止规则。若 gold 方向无潜力、可部署覆盖不足或预测误伤无法保护
   recall，则停止该时间路线，保留证据并另选现有 MAVEN 范围内路线。
5. 只有信号、novelty、power、control/消融/负控闭合后，才把新合同与单 seed GPU 行加入主表。

不得扫 sampler/threshold/loss weight/epoch、不得追加旧 role 家族周期、不得读 final-valid。
所有探索分析明确标探索，已看过的 internal-dev 不能重新称前瞻数据。
文档级重采样，不把相关 event pairs 视为独立样本制造 power。

## 首个候选（待审查，非准入）

问题：时间不相容性是否能减少高触发相似度误合并，同时保护真共指召回？
处理候选：在官方训练目标与完整候选下保留 temporal uncertainty，不使用硬分区删候选。
竞争解释：时间信号只编码句距/事件类型；gold 信息含身份标签；提升来自目标或解码恢复而非信号；
预测时间噪声将真共指判为 BEFORE 并伤 recall。
拟议消融/负控：目标/解码一致的无时间控制、候选处理、文档内匹配条件下打乱时间输入。
exact 处理和负控匹配条件须在训练前冻结；当前没有方法效果或创新性结论。

最近邻待归档复核：[CohTP, ACL 2026](https://aclanthology.org/2026.acl-long.1345.pdf)，
正文 §3–§5 含 temporal graph/partition、cross-time recovery 与 GPT-4。
作者[仓库](https://github.com/chenxinyu-nlp/CohTP)在上轮检索仅见占位文件，当前须再次核 revision。
其任务为跨文档共指，不能搬用其数字或 test-driven 纠正步骤；借鉴问题定义不是官方复现。

## 训练集审查后的裁决

`report_temporal_identity_signal.py` 已在冻结 train 完成 CPU 审查，数字只见 R1 §25.38。
**停止“同句 DATE 词面不同就禁止合并”这一代理路线**：该输入不是事件的时间锚，
存在真共指误伤，缺失/多日期句必须是 unknown；不能从弱词面代理外推所有时间关系无效。
gold BEFORE 的两个事件端点本来就是不同 gold clusters，直接 oracle 分类含身份循环，
不作为可部署信号准入依据。
现有冻结强锚的 BEFORE/coreference 冲突审查也已完成，数字只见 R1 §25.38。
**不准入直接 predicted-BEFORE cannot-link**：冲突同时命中真/假合并且覆盖有限，
没有 MUC 效应、document power 或独立信号证据。不能用这两个弱代理否定全部时间机制。
下一步是原地同 scores decoder audit，再判断官方目标匹配与其他信号；方法合同未准入前不训练。
作者已具体授权 C5 两项诊断仅空卡执行，第一次 launcher 被新的他人进程拦下，未加载模型。
重新空卡后的真实 checkpoint CUDA smoke 已 complete，average parity/产物 hash 通过；
完整 audit 仍待重新空卡，旧 smoke 不复跑。

## 完整 decoder 结果的解释规则（读取前登记）

比较只改变冻结 binary scores 的连簇方式，不能评价 antecedent marginal likelihood 训练。
先核完整覆盖、输入身份和 average parity，再读官方 MUC 与 B³/CEAFe/BLANC，最后读配对错误交换。
若 antecedent 提高 MUC，也只说明该 checkpoint 存在解码恢复空间；未超过强锚、未过护栏或
未隔离训练目标时，不准入方法贡献。若下降，停止“只换 decoder 即修复”的解释，保留原控制，
不扫描 dummy、阈值或 mention 顺序。错误交换只用于区分欠合并与误合并，不替代主指标。
即使两种 decoder 都失败，也不能据此否定官方训练目标或所有结构方法。
下一候选必须从真实错误与可部署输入出发，点名最近邻机制差异；控制重现不能占创新项。

## 补充最近邻边界（2026-10-12）

- [PairwiseRL, *SEM 2022](https://aclanthology.org/2022.starsem-1.6.pdf) §3：两个事件所在句
  联合编码，trigger 表征互相条件化，显式论元比较是另一组件。它证明“pair-conditioned encoding”
  不是我们的新颖性；可作为强对照方向，但尚未取得并审查该方法的可运行官方代码/许可/资产链。
  论文脚注的 [CogComp 页面](https://cogcomp.seas.upenn.edu/page/publication_view/979)
  本轮只返回 Angular 模板；作者主页仅列论文。检索失败不等于代码不存在，不据散文重写复现。
- [FRECO, EMNLP 2025](https://aclanthology.org/2025.emnlp-main.1440.pdf) §3.1/§4.2
  使用该类 cross-encoder，但其目标是“共指且框架不同”，**同一事件但框架不变也属负类**。
  [公开仓库](https://github.com/jinzhao3611/freco) README 列的是 Llama SFT/DPO 和 mining，
  本轮未核到 CDEC encoder 路径；不能把 FRECO 的 binary 输出当作 MAVEN 的 identity 输出。
  新语料、生成偏好、阈值校准与该 adapter 均不进入本轮。该检索只限定最近邻差异，不生成新的训练许可。

## 持续推进与下一项独立审查（作者追加指令）

作者要求推进到突破证据再停止。资源等待不结束 C-41，记录负结果后继续选择实质不同路线；
突破只认同协议官方主指标胜过强锚、护栏与机制消融/负控支持，不保证科研一定出正结果。
既有 5090 许可仍只覆盖两项 decoder 诊断，不扩为训练、额外 seeds 或搬权重。

**科研价值**：检验事实性是否携带事件发生实例的独立分辨信息，对准表 5-3 的误合并与欠合并。
[MAVEN-FACT](https://aclanthology.org/2024.findings-emnlp.651.pdf) §2 按 mention 标注五类事实性；
[FactBank 官方说明](https://catalog.ldc.upenn.edu/LDC2009T23)明确同一事件可有来源相对的不同事实性。
故“标签不同就不同事件”不是可直接成立的规则。先在冻结 train 统计完整标签配对与真/假身份，
检查同 gold cluster 内的 label diversity；不把 gold 标签输入可部署 coreference 模型。

**可行性**：本地 FACT/ERE train 与两个冻结 train manifests 可读；按 mention ID、type、offset、
tokens 对齐，禁止用 FACT 的 cluster/arguments 信息构造预测。训练集标签含 LLM 预标注，
故标签一致性不能作为独立的身份真值或确认性机制证据。可部署预测、最近邻差异与 power 尚未闭合，
本步骤仅 CPU 信号审查，不准入训练。若没有潜在独立分辨力，停止本候选而继续找下一机制。
竞争解释包括：事实性只是多数类先验；同源标注使标签与身份相关；不同来源对同一事件有不同承诺；
实际分类器噪声消除 oracle 信号。禁止从 gold oracle 计数直接写 MUC 增益。

Train 审查已完成，数字只见 R1 §25.39。标签差异具有探索分辨力，但其覆盖有限且命中真共指；
直接硬否决不准入。MAVEN-FACT §2.1 的标签来源是 author，不能把它描述成带 source 标注的 FactBank。
按 doc/event ID 排序读取的首批混合标签簇包含尝试/拒绝、引述与否定语境，也可能有标注噪声；
目前没有人为重标注，不能把其中任一解释认成真相。

最近邻新增：[Lu & Ng, NAACL 2021](https://aclanthology.org/2021.naacl-main.356.pdf)
§4.1 的 C5/C6 已将 realis 一致性接入 antecedent score，并通过 Eq.13 的软 penalty 改连链倾向；
§4.2 联合训练、§5.3 做 realis 消融。**简单加事实性、改成 soft penalty、换五类标签均不够新颖**。
其 ACTUAL/GENERIC/OTHER 与 FACT 五类也不能直接映射。

下一待证候选是“测量噪声下的非对角兼容性”：同身份允许不同 factuality 观测，
使用预测观测的噪声模型与 train 内 identity/标签联合分布，而非强制 label equality。
这只是机制假设，尚未证明最近邻差异或可检出的 MUC 效应；不把换信号的旧 role residual 当新家族。
竞争解释是加入多数类先验/容量产生表面提升、同源标注诱导循环或类别噪声抹去收益。
需匹配相同文本 scorer/decoder 的无信号与现有 realis-penalty 强对照，以及文档内同类型打乱的负控。

输入来源检查发现旧 D4 的文档级 OOF 不等于 C5 consumer 级隔离：部分上游训练/选择文档
属于 C5 internal-dev，不能将其并集接入新的 consumer 训练。旧 D4 OOF 自身结论保持；
本地 internal-dev CLS cache 与旧全量 OOF 作用域不同，未把 cache 当作全量预测或数据损坏。
若继续该候选，须重新闭合不接触 consumer evaluation 标注的训练/预测路径，再核 power。

下一项独立 CPU 观测诊断：固定 TF-IDF + multinomial logistic regression，只在 C5 的 FACT train
做按文档交叉拟合；借助已有 sklearn，不重写外部方法，不作为 D4 的创新或对手。
科研价值是用独立于 gold identity 的真实文本预测，测量上述 oracle 信号在观测噪声下是否仍存在，
以及它和同身份标签变化能否区分；“机器空闲/成本低”不是选型理由。
可行性：sklearn 已安装，已核 train 2622 文档对齐；marked sentence 不读 evidence/arguments/cluster，
每次只用其他文档拟合词表与分类器，同一冻结 seed，不调 C/class weight/ngrams 或看 dev 选模。
折分、词表和分类器参数在运行前由独立 JSON 冻结；收敛警告、标签缺失和 hash 漂移即停止。
弱观测器失败只否定该观测路径，不否定事实性全部信息；即使成功，仍不是 coreference 方法提分。
该诊断已经完成：真实 OOF 与只读 observed signal 数字见 R1 §25.39，覆盖很低，稀有类别很弱。
不对它扫参，不准入直接拆簇，也不把辅助指标当论文贡献。

### 10-13：部署观测与强锚错误对齐（诊断，未准入方法）

科研价值：检验训练集中的预测差异是否能覆盖冻结强锚的真实 identity 错误，
对准表 5-3 的信号/功效准入；只读分数和观测，不修改 cluster，不报告 proposed MUC。
可行性：五个已训练 CPU 观测器都只接触 C5 train，各折 ledger 与 consumer dev 不相交；
本地原 official-joint 无标签 test input 的 SHA 与远端一致。复用五个固定模型概率的等权均值，
不增加训练、不选 fold、不改类别权重/阈值；模型留本地，严格不读取 FACT dev factuality 标签。
消费者标签只能在之后独立的 identity 错误分析使用，不能进入 observer。
输出为完整 mention 概率、模型/input hashes 与角色/作用域 provenance。
与 score cache 对齐后只做预先登记的分类差异覆盖及文档分布；差异计数不能替代 MUC 收益或 power。
若缺实际部署信号/错误覆盖，不调当前观测器，停止这一观测路径；不据此否定所有事实性机制。

最近邻补查：[Yadav et al., CRAC 2021](https://aclanthology.org/2021.crac-1.11.pdf)
§3.3–§3.7 已用 event/entity cluster trees、LCA linkage/order 的关系相似性与交替推理表示不确定性。
这与 factuality 测量通道不等价，但足以排除泛称“首个不确定性共指模型”；
噪声兼容性的新颖性仍未闭合，不能只凭改 auxiliary attribute 或改 soft penalty 准入。

部署 argmax 诊断已完成，错误覆盖见 R1 §25.41；不能支持直接差异 veto。
下一项只读诊断固定连续距离 `0.5 * sum_k (q_i[k]-q_j[k])**2`，不选距离/阈值。
预测：若该观测器仍有连续分辨信息，同文档内被选中 false links 的平均距离应高于 true links。
竞争解释：类别多数先验、trigger/类型差异与同句相关噪声造成总体差异；因此报告 all 与同类型
两套预先指定桶、每篇两类均存在的文档等权差值，以及按文档 bootstrap 的区间。
不将 pairs 独立化，不据此声称 MUC 增益、目标 power 或噪声通道的新颖性。
若均值差没有方向支持，停止当前弱文本 observer 路径，不通过扫参或更换距离挽救。

连续诊断完成，未支持预设方向，证据 R1 §25.41：当前弱文本观测器路径停止，不调参。
下一项是 known type-agreement 控制，非新方法：同 frozen official-joint scores/decoder，
只用无标签任务输入给定的类型限制连链。先重放原强锚 parity，再做一次固定约束的 official 评分。
价值是识别未使用已知类型规则的 baseline 欠额，避免未来虚报新机制收益；可行性是 CPU 全量 cache
和官方 utility 已可用，零训练/权重搬运。合同 `PHASE_C5_typed_control_20261013.md`。
Lu & Ng §4.1 C1 已提出 semantic-type 一致性；硬约束给定类型是透明控制，不当作该 MTL 复现或创新。

控制已完成且官方共指四个指标均提高，配对/复算/可追溯证据只见 R1 §25.42。
原锚不重绑，当前新方法仍未准入；未来候选须胜过该 stronger alternative，不能把已知约束收益
当新机制的收益。下一步复用既有 `report_coref_error_profile.py` 核该控制的残余错误。
科研价值是从真实剩余 false/missed merges 寻找独立干预点，对准表 5-3 的新家族准入；
可行性是同 P1 input/prediction/evaluator 的本地 CPU 只读 profile，无训练/新预测/阈值改变。
诊断完成不等于 C5 章完成；新机制仍需文献差异、部署输入、目标 power、消融与负控。

残余 profile 已完成，数字见 R1 §25.42，两类 MUC 错误均须解释；不能仅凭 trigger 相似度
推断其因果作用。最近邻继续核到正文：
[ACCI preprint (2025)](https://arxiv.org/abs/2506.01488) 及
[正式正文](https://www.nature.com/articles/s41598-025-32765-6) 的 counterfactual ECR 部分
已构造 trigger-only bias 分支、masked-trigger context 分支，并以 Eq.14 的加权加减修正 factual
预测。因此“mask trigger + context/bias 分支”本身不能立项为创新；当前其 runnable code 障碍仍在，
代码不可得不能抹掉其机制先行性。
[RCA (NAACL 2024)](https://aclanthology.org/2024.naacl-long.63/) 是另一直接邻居，
已定位论文，接续还须审其生成数据/官方实现、正文机制与 MAVEN 内适配条件，不能只凭摘要准入。

## 10-13 接续：null 决策覆盖与新颖性门

最近邻正文/官方代码、固定 antecedent 决策分解及 oracle 的独立评分、train 派生监督范围
已完成，数值只见 R1 §25.43。原 cache/type-control/weak observer 不重跑。
后续完整机制矩阵、错误→假设→实验映射与未准入 candidate brief 见
[`20261013_c5_newness_admission.md`](20261013_c5_newness_admission.md)。
null 边界有主要 gold-conditioned 修复覆盖，但 ordinary anaphoricity/singleton 头已有先行工作，
不能把这份诊断当新方法增益。继续核 train-only 文档隔离 scorer error-state 输入与
selective/error-correction 最近邻；power/干预/负控未冻，不形成方法训练合同。

## 本轮使用的研究工具来源

使用已安装的 hypothesis-generation 区分候选、竞争解释、预测与实测，不把技能校验当科学结论。
来源核验：Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026).
*Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*.
[arXiv:2609.00065](https://doi.org/10.48550/arXiv.2609.00065)。
