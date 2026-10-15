# 4090不可用后的创新方案升级与任务设计（2026-10-15）

作者本次确认4090不可用、修复时间未知，要求优先检索最新论文、升级创新方案。
本卡是主表C-41/T087的研究裁决与接续说明；执行顺序只认
[`EXPERIMENT_PLAN.md` §3.8/§4](../EXPERIMENT_PLAN.md)，保留C5→D4→A4。
不改论文结构、不追加E3实验、不复活封存机制，不因新卡可用直接准入训练。

## 研究价值与可行性

**科研价值**：对准C5表5-3、D4表3-3、A4表4-3。把“增加模块”升级为能排除竞争解释的
监督设计，分别回答联合依赖、事件与证据的归属、正例与竞争关系的区分是否有独立价值。
这些是候选问题，不是三个已成立的方法贡献。项目结果依据R1 §25.37、§25.42、
§25.49–§25.63；本轮取舍与资源核查事实只见R1 §25.65。

**可行性**：C5在5090已有本机initializer、官方source、train与manifest，存在性已核；
执行前仍须逐项hash。训练输入不需要新增标注或4090 checkpoint。D4现有loader可读取
mention级factuality及supporting-word offsets，不能假设有source/scope gold；A4已有训练关系标签，
不能假设有人工causal evidence。新候选先用现有train做无模型审查，再评估生产实现与GPU预算。
本次只检索、静态检查与规划，没有产生新模型效果或运行训练。

## 检索边界与新证据

检索截至2026-10-15，覆盖2025–2026的ACL/Findings/CODI/RepL4NLP、IJCAI、arXiv及作者仓库；
补查早期直接机制邻居，而不以年份新旧替代机制比较。多轮查询包括event factuality、
event coreference、MAVEN-ERE/FACT、antecedent forest/pair marginals、scope/contrastive、
近期两个月发现检索及官方source复核。日期以正文/官方提交为准，不把抓取时间当发表日期。
结构化出处、revision及未验证项见
[`20261015_literature_sources.json`](20261015_literature_sources.json)。这是有边界的审查，非穷尽综述。

| 新近工作与核查位置 | 已核机制 | 对本项目的裁决 |
|---|---|---|
| [UERLens，ACL2026](https://aclanthology.org/2026.acl-short.38.pdf) §2.1–2.3、Appx A/B；[官方代码](https://github.com/ncepu-eai/UERLens/tree/ded7586c99a94da0d7a80848488be69f241eee86) | 反事实句对→SAE特征→干预或SVM；附录用GPT-5构造反事实 | “反事实特征/干预”已有。其UERBench不是冻结完整候选主表，不搬其分数；外部改写的文档来源/切分未闭合，不导入训练 |
| [Suggest–Verify–Revise，ACL2026](https://aclanthology.org/2026.acl-long.871.pdf) §3.1–3.3/Eq.1–4 | LLM/共指hypergraph建议、Topological Hawkes验证、事件/事件对双层contrast与迭代图修正 | “叙事一致性+图验证+contrast”已有；未在本次检索定位官方可运行release，状态UNKNOWN，不据正文重建后冒称复现。temporal/coref来源须核，不能视为免费推理输入 |
| [Meta-Factivity，ACL2026](https://aclanthology.org/2026.acl-short.7.pdf) §4/Limitations | recognition/reasoning/regulation的理论框架与诊断主张 | 可启发检查shortcut，但作者明确完整benchmark仍待建设；不是可直接接入MAVEN的trainer，也不替代五类主指标 |
| [CohTP，ACL2026](https://aclanthology.org/2026.acl-long.1345.pdf) §3–4；[官方树](https://github.com/chenxinyu-nlp/CohTP/tree/3843ad0a4dcdb9f4761f134894b935d4ed74d19b) | NLI时间图、EA-GNN、GPT-4纠错、时间分区与恢复 | “时间一致性共指”已有。当前tree仍只有占位文件，复现卡【代码】；闭源纠错/分区也不纳入当前完整候选路线 |
| [Generating Effective CoT Traces，Findings ACL2026](https://aclanthology.org/2026.findings-acl.264.pdf) §3.1–3.3/§4.1 | 大teacher示例→长CoT→目标模型改写并按答案/PPL筛选；报告CHR等 | 不能把CHR当official causal F1。新建大teacher语料不进入本轮；未核到runnable release，不用“small model”措辞推导预算可行 |
| [Debate with Myself，IJCAI2026](https://www.ijcai.org/proceedings/2026/0674.pdf) §3–4 | 相同LLM不同角色提供支持/反驳证据，仲裁与验证 | “双向证据+竞争解释+辩论”已有，不能把多轮LLM流程换名当A4创新；本轮不增加此类推理任务 |
| [BeyondAtoms/CARVE，作者2026公开release](https://github.com/lzy248/beyondatoms/tree/172dced0a1e98a8544101ecd48754bb7bd8c4659) README/verification source | claim/evidence关系图、锚点匹配、结构差异、NLP及LLM验证 | 关系事实核验与MAVEN mention五类事实性不同。代码可读，runtime/LICENSE未闭合；未读其PDF，不凭README声称conference acceptance已独立核实 |
| [ECPO，2026 preprint](https://arxiv.org/html/2605.21993v1) §3.1–3.4 | 同时输出候选ranking与evidence certificate，证据可复算性进入policy utility | 研究单位为ranking/certificate，不能把MAVEN名字或榜单数字当ERE同协议结果；本轮不重开旧生成/RL或E3路线 |
| [Zero-Shot Belief，CODI2025](https://aclanthology.org/2025.codi-1.10.pdf) §3–4 | 作者与嵌套source的belief预测、事件/来源识别与标签 | 要区别作者承诺、来源承诺与世界真值；MAVEN-FACT不能凭空增加source标签或改成FactBank任务 |
| [Efficient ERE，RepL4NLP2025](https://aclanthology.org/2025.repl4nlp-1.7.pdf) §2 | retriever筛候选、cross-encoder分类与hard negatives | 取其训练分布问题作邻居；冻结评测全集不裁剪，不以更少候选换得效率/分数 |

UERLens源码审查具有实质限制：`svm.py`默认多卡、固定layer→vector IDs，
`train_svm()`默认空texts、示例标签；当前公开SVM入口未展示将论文筛选的features绑定成
完整训练资产的流程。`analyzer.py`按FRC排序，原文Eq.1–2描述latent effect；二者对应关系
仍须核。故分类是“真实代码存在、静态缺口明确、runtime/fidelity未验证”，不是README-only，
也不是已完整复现。不得为让它运行而重写后悄悄继承论文身份。

早期直接机制边界仍不可越过：

- [Le & Titov2017 §3–4](https://aclanthology.org/K17-1039.pdf)已有root-membership递推与
  soft-cluster metric训练；C5不能声称发明森林或结构loss。
- [SDIN2023 §3/Table1](https://aclanthology.org/2023.findings-acl.879.pdf)的support/refute等
  标签来自同一事件的句级/文档级事实性；不能把不同事件的不同标签照表当蕴含/反驳。
- [Jiang & de Marneffe2021](https://aclanthology.org/2021.tacl-1.64.pdf)已系统讨论表面模式与语用
  失败。其§2还说明embedding环境的效果不能一概而论；“删一个否定词就翻转factuality”不成立。
- scope、evidence、contrast已有先行研究；本轮没有完整核CoDE正文，故它是D4下一轮
  必审邻居，不能凭二手提及或论文标题就声称候选已排除重合。

## 升级一：C5联合依赖监督，保留为当前主候选

**问题与独立变量**：在相同parent分布、输入和解码下，精确同森林pair概率C所保留的
共享前件依赖，是否比root-membership乘积更适合监督？当前证据使该问题可检验，
没有证明它一定提分，也没有在本次检索证明全面新颖。

保留已冻结的corrected-marginal/root/exact/mass/shuffle、surrogate、scale与endpoint，
不因新论文新增模块或把新训练改成解码扫参。最强竞争解释分别是普通结构监督、
总pair概率增加、pair标签对齐和新控制训练不足。exact必须按原brief胜过匹配强控制并
守住护栏，才能讨论其价值；仅胜marginal不能支撑联合依赖论断。

**升级重点**从“继续验证小性质”转为“有限必要门→决定性训练”：

1. C41-S：5090原地核资产/源码delta/输入与评测非权重证据，建立独立成本配置和合同。
   不从4090取checkpoint；现r2硬编码4090，不能改封存脚本放行。
2. C41-B：在对应任务许可明确且空卡时完成五臂真实optimizer成本及完整累积/shape预算。
   原CUDA通过不抵扣另一机器的成本；本机shape与scheduler配置须冻结。
3. C41-A/T：预算/R1闭合后冻结生产实现并执行五臂。主指标目标、归因与停止条件认旧brief，
   不按第一臂分数改变其余臂。旧typed强锚保留历史身份；干净归因以5090同机匹配臂为主。

若缺的是授权或单任务预算，只判该执行方案卡【授权/算力】，不判数学机制已被证伪。
若完整实验关键比较失败，停止该固定候选，记录竞争解释；不扫scale/epoch救它。

## 升级二：D4事件锚点与承诺证据绑定（待准入候选）

**研究问题**：在相同语境中，模型能否把承诺证据分配给正确的事件，而不只读出句中
是否存在否定/模态词？这是事件条件化的监督问题，不声称观察到的错误已被此机制唯一解释。

**拟议变化**：保留marked-CLS完整文本→五类flat head通路，在train中利用原生多事件标签
及可靠supporting-word对齐，研究同语境不同锚点的配对区分监督。正/负关系由真实训练标注
定义，不制造“删词后新label”；缺少证据不是负作用域，Uu不是没有cue的同义词。
这里尚未冻结具体loss，也不把普通supervised contrastive方法自动认成贡献。

与封存家族的边界：不以预测evidence池化拼接作为推理输入（D3），不压缩成typed cues或
分解头（旧D4），不从causal边传播残差。若最终实现实质仍是这些机制，拒绝立项。

**下一准入任务**：只读冻结train统计同句多事件的可用对照、稀有类机会和evidence offsets；
区分真实差异与来源/标注噪声，不查看evaluation来选规则。核CoDE、scope方法、SDIN、
普通supcon与反事实训练正文，写明是否有尚未覆盖的监督差异。

**最小判别设计（候选，非执行合同）**：同输入linear强控制、普通类平衡/普通supcon强竞争臂、
event–evidence配对监督、保持类别/文本与机会数但打乱归属的负控。若需要额外头，匹配容量。
主指标仍是冻结五类macro-F1；按同协议完整五折与既有强对照评价，不用训练pair accuracy替代。
数据依赖的配对规则、effect/power、loss/预算必须在proposed结果前冻结。

**证伪/拒绝条件**：训练机会不足以支持稀有类、标注不能区分归属、差异只剩普通contrast/
类别重加权、或者需要不存在的source/scope gold，则停止该具体设计。若负控同样有效，
不支持绑定机制。该候选当前`method_admitted=false`，没有D4新GPU许可或效果结论。

## 升级三：A4目标事件条件下的多正例关系区分（待准入候选）

**研究问题**：在完整候选中，如何区分同一目标事件的真实原因/前提与相关但未标注关系的
事件，同时保留多个真实原因？此处评估的是数据集关系识别，不从文本对比推断世界因果效应。

**拟议变化**：研究以固定目标事件及方向/subtype组织训练监督；保留多个gold正例，
与机会匹配的无关系候选作条件区分。它改变训练监督的比较单位，不改变评测全集、
不让“更保守预测全部None”获得机制奖励，也不将多个真实原因softmax成唯一原因。
这不是现已证明新颖的loss；若只实现hard-negative mining/普通多正例contrast，则不立创新项。

与封存A4的边界：不做masked/retained文本删除，不训练“删去证据则必须否定”的hinge，
不把当前checkpoint的局部梯度符号当历史训练原因。保留全部CAUSE/PRECONDITION监督
和三个关系任务护栏；不能只筛容易正例或缩候选后报更高F1。

**下一准入任务**：train-only核同目标多正例及matched无关系组、方向/标签合法性；
核SVRECI事件/事件对contrast、已有listwise/multi-positive loss和LLM-SD的实质重合。
明确false-negative标注/共因/叙事先后竞争解释，不把BEFORE直接当CAUSE。

**最小判别设计（候选，非执行合同）**：同机同预算官方/匹配监督强控制、普通hard-negative/
普通多正例contrast竞争臂、候选条件监督、保持标签比例但打乱目标归属的负控。
独立复算official causal P/R/F1与两关系护栏；同时报告恢复与损失的正例。
若只降低FP却继续丢失大量正确正例、不胜普通contrast或负控未失效，则机制失败。
novelty、输入、power和5090本机预算仍须闭合；当前没有准入或新增GPU授权。

## Codex近期任务与时间边界

| 次序 | 工作与交付 | 结束点 |
|---|---|---|
| 本次 | 完成新近文献矩阵、源码缺口与三章候选取舍，主表去除近期4090依赖 | 文献卡/出处清单/results/状态一致并push；不以“看了论文”声称机制通过 |
| 下一工作回合 | C41-S：5090自足资产清单、source/input hashes、新成本适配设计与可审命令 | 可审查合同与明确的资源/科学缺口；不重复原控制/CPU小性质 |
| 随后一个必要门 | C41-B/A：实际成本与R1裁决 | 各臂实测后才给训练时长；不预承诺五臂几小时完成，超时限不擅自延长或缩预算 |
| 准入后 | C41-T：同seed五臂、统一评分及归因裁决 | 完整证据后决定该候选去留，负结果原样交付 |
| 后续章节切片 | 先D4配对机会/最近邻准入卡，再A4条件监督准入卡 | 每个候选首轮静态审查以一个工作日为时间盒；欠关键证据则列具体缺口，不写成训练就绪 |

时间盒用于阻止准备无限增长，不是实验正结果承诺，也不替代文献/有效性要求。
候选不适合时按主表记录并替换，不能为赶时间放宽对照或连续试参。

## 资源与有效性边界

5090为近期唯一已知可访问GPU机器；本轮只核C5资产存在性，没有重新核空卡或执行模型。
沿用10-14具体C5许可，不把本次规划当新GPU授权。结构成本迁移须核原joint成本许可覆盖；
若范围无法确证，先交付合同/确切命令，不直接发任务。D4/A4新GPU、超过一天任务、
额外seed与跨机checkpoint搬运保持原边界。原C5 decoder audit是独立有限诊断，
可以按既有许可收口，但不阻断上述创新审查或替代五臂训练。

同pretrained pin不保证跨机numerical parity；新机器上匹配control/treatment、
记录来源与选模差异。final-valid封存、完整候选、官方evaluator与单seed13不变。
本地只轻量CPU；新实现须TDD、完整本地门与远端真实测试，不能拿local torch skip充当通过。

过程方法来源沿用[项目科研skills说明](../RESEARCH_SKILLS.md)，其中
[Scientific Agent Skills](https://arxiv.org/abs/2609.00065)只提供程序性审查方法，
不作为本项目方法效果或创新证据。本轮没有安装技能、训练外部模型或调用生成teacher。
