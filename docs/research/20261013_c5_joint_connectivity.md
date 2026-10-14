# C-41 · C5 共享前件的联合同簇概率候选

状态：`candidate_under_review`，`method_admitted=false`。这是当前 C5 切片内的 R1 审查，
不是新队列；尚未形成 proposed training 合同，也没有提分或全面新颖性的结论。
数学审查产物与数字只见 `docs/results/PHASE_R1.md` §25.46。

## 科研价值与可行性

价值：表 5-3 的主指标取决于输出簇，而原训练逐 mention 学习前件；共享上游前件使
两个 mention 的簇身份相关。研究问题是：显式保留这个联合依赖，能否改善 strongest
given-type control 之后的错误，并胜过 ordinary null/anaphoricity 控制？
只改善概率一致性不能通过主表门；必须由官方 MUC、其他共指护栏、单变量消融与负控支持。

可行性：MAVEN train identity 可产生 pair identity，无新增标注；固定表示与原 head 的
权重留 4090，当前 null 控制导出的 current embedding 可以在原机重放其 pair MLP。
不需要把 baseline 的 in-sample 错误用作训练标签，也不需要新增 factuality/argument observer。
最终拟合/推理仍需 train/dev 隔离与 source/hash 闸门；本轮只有不读数据的数学检验。
算力边界是 ordered forest 的递推通常 O(n³) 时间；最终前向矩阵O(n²)，朴素autograd保存中间矩阵可达O(n³)内存，给定类型可分块。
实际 train 分块规模、autograd 时间与目标 power 仍须测定；不以“小规模证明通过”假装可训练。

## 可证伪的机制差异

给定文档后每个 j 独立选择 k<j 为 parent 或 self 为 dummy。注意独立的是 parent 抽样，
不是最终同簇标签。设 C_ij 为同一棵树的概率，则 C_ii=1，且对于 i<j：

`C_ij = Σ_{k<j} p_j(k) C_ik`，`C_ji=C_ij`。

理由：对 j 的 parent 条件化。j self 时不能与较早 i 同簇；j→k 时，j 和 i 同簇当且仅当
先前森林里的 k 和 i 同簇。parent_j 与先前森林独立，所以可将概率分解。后续节点只连
一个 parent，无法合并此前两个组件。输入若依赖实际抽样簇、允许前向边/环/多 parent，
这个证明就不适用；不能推广为任意共指图的精确边缘计算。

候选差异是以精确 C 的 cluster-pair supervision 训练，保留共享上游决定的梯度；
不是给普通 anaphoricity 头改名字，也不是声称发明 antecedent forest 或 soft-cluster loss。
具体 loss、matched heads、推理动作仍未冻结，不启动方法训练。

## 正文机制最近邻（不比较外部数字）

| 来源 | 已核的机制 | 与候选的边界 |
|---|---|---|
| [Rennie 2007 §3.5.1 Eq.3.13–3.14](https://people.csail.mit.edu/jrennie/papers/phd-thesis.pdf) | 独立 softmax antecedent 与 root-membership 递推，gold root likelihood | forest/root 递推很早已有；此处不能认作创新。候选区分的是两个标签的联合同簇概率 |
| [Le & Titov 2017 §3–4](https://aclanthology.org/K17-1039.pdf) | root-membership 递推；soft cluster 的 link 函数用两项 membership 的乘积，训练 B³/LEA | 其乘积是对硬指标的可微松弛，并未声称是 random-forest 联合边缘；不能把它“判错”。候选需比较同一 train loss 下 exact C 与 root-product，隔离相关性贡献 |
| [Samdani & Roth 2013 §4 Eq.7–8](https://aclanthology.org/D13-1057.pdf) | 独立 left-link 分布，已构造簇中 link 概率求和，greedy cluster assignment | 不是对全部随机先前森林的 pair 联合边缘；cluster probability 和聚合前件本身已有 |
| [Yang et al. 2015 §5.2 Eq.2、§5.3](https://aclanthology.org/Q15-1037.pdf) | sequential DDCRP customer links 导出 connected clusters；加入生成 likelihood 后 Gibbs posterior | 先行 forest/贝叶斯聚类；候选仅条件独立 backward choices 的闭合边缘，不解决其 coupled posterior |
| [Lee et al. 2018 §3 Eq.5–8](https://aclanthology.org/N18-2108.pdf) | antecedent attention 多跳细化 span embeddings | 多跳信息并非新；候选不更新 embeddings，而改变簇联合概率与监督，仍须实测差异 |
| [Wick et al. 2013 §3 Eq.2–4](https://maroo.cs.umass.edu/getpdf.php?id=1128) | partition distribution 下 query co-cluster confidence，MCMC 近似 | co-cluster probability 本身不是新指标；候选 restricted forest 的精确计算不适用于其一般 partition distribution |
| [Yadav et al. 2021 §3.1–3.3](https://aclanthology.org/2021.crac-1.11.pdf) | hierarchical cluster trees 编码不确定性，联合 entity/event Dasgupta cost | uncertainty/tree 联合建模已有；不重开旧 role/argument 家族，不用他们的任务差异抹掉先行性 |

本轮多轮一手检索尚未定位完全相同的 pair 递推及训练目标，但“不曾检索到”不能证明不存在。
已进一步核作者 official README 的实际 `compute_p_m_entity` / `compute_lea_lost`：root DP 与 `batch_matmul` membership product 与正文一致。固定 repo revision / 源码 hash 见结果页。尚须补其他全同机制先行工作及真实可训练性；只能称有具体差异的候选。

## 尚欠准入与判别实验

frozen null 控制实测已完成且未胜 strong control，停止该控制（§25.45）。固定零训练 posterior-score 控制已完成并否决（§25.47）；推理分数对照不能替代监督创新的准入。拟议的最小判别是：
从相同 pretrained 初始化的完整原模型、相同input/优化预算下，official marginal control、
root-marginal product cluster-pair loss、exact joint cluster-pair loss与固定 ancestry shuffle负控。
loss 或 decoder 只能择一作为单变量；不能同时换两者后把收益归给联合依赖。

目标效应、document-level MDE/≥80% power、具体训练 loss、无调参 endpoint、匹配强对照
与护栏尚未闭合。数学恒等式、toy 反例、文献差异都不替代部署主指标。

## 实测之后的路线裁决（§25.47–§25.49）

固定 posterior-score 解码控制已结束，没有可认定的主指标突破或精确联合优势；
同weights的二类decision-unit审查也失败。二者不重跑或扫参。下一个实质问题是学习
目标：不同函数是否改变wrong-link的监督，而不是继续改已拟合分数的排序/阈值。

构造反例在相同固定pair-F1 surrogate下确有误边梯度抵消的差异，且中心差分支持
autograd。该surrogate不是Le&Titov的原B³/LEA，也不是精确期望F1；不把反例写成
对他们完整方法的否定。数据集有效性/泛化仍未测试，toy不能替代power或指标。

拟议学习路线从相同pretrained initializer训练完整原架构，使结构目标有机会影响
早期不确定的parent distributions；不把已有饱和frozen-null的train输入当OOF错误标签。
输入仍是现有MAVEN text/spans/task-given types，监督是train gold identity。比较原
marginal、相同surrogate的root-product、exact joint与ancestry-shuffle；保留原强锚，
backbone/seed13不变。真实训练成本、具体合同、目标效应/≥80%document power尚未闭合。
这是候选研究路线，未准入训练、未形成章节创新贡献。

训练设计还须控制不同loss的量级/共享任务梯度预算与选择口径，避免把criterion替换
造成的重加权当作联合依赖的收益；root-product/exact须用相同surrogate/scale/decoder。
当前反例只测logit偏导，不能保证共享神经参数更新后每条误边都下降。

完整train的预声明结构机会与类型分块规模已全量测定，并经独立逐doc枚举一致；数字只见R1 §25.49。数据标签/递推规模可行，实际模型CPU梯度与预算审查仍须完成，不将标签覆盖当可修复率或power。

原joint `fill_expand` 与marginal loss接口的新观察须先做真实autograd反证：非单例簇首mention的dummy可能缺失。如确认，各结构臂均使用规范first-dummy监督，corrected marginal列为强对照；只修正已有目标不算创新。封存源代码不改写，实证见R1 §25.49。

已补核[READS, PVLDB 2017](https://home.cse.hkust.edu.hk/~raywong/paper/vldb17-SimRank.pdf) Eq.1/§3/§4.1：同时移动的双walk递推、等hop首次相遇、可合并walk/tree均属先行机制。候选是每个ordered mention一次parent选择下的同森林连接概率、mention特定dummy、condition later节点的训练目标；不以coalescence/递推/共享walk本身作创新。该有限对照不能证明全部同类图算法无先行性，源码快照与解释在 `learning_literature_audit/`。

## 依赖修正与整体概率膨胀的竞争解释

令Z为每个mention的随机one-hot root标签矩阵，Q=E[Z]，P为strict-lower parent概率，
A=(I−P)^{-1}。设ε_j=Z_j−E[Z_j|Z_<j]，则ε是按mention顺序的martingale差分，
不同j的交叉内积期望为0。条件均值为p_j Z_<j+dummy_j e_j，较早节点不可能root于j，
所以其残差能量v_j=1−dummy_j²−p_j C_<j p_jᵀ。由Z−Q=Aε，

`C−QQᵀ = A diag(v) Aᵀ`。

v是条件残差方差的期望，故非负；A=I+P+...+P^(n−1)逐项非负。因此covariance
修正既PSD又逐项非负。该分解是既有covariance/线性innovation思想的推导，不能
声称发明covariance factorization或coalescence。数值验证与限制只见R1 §25.52。

这也给出更强的竞争解释：exact C不仅改变局部归属，还增加所有pair的总体概率量。
正式候选除root-product、corrected marginal与ancestry-shuffle外，需考虑同总量rival：
在同doc/type合法strict-lower pairs上令α=Σ(C−Qdot)/Σ(1−Qdot)，以
`B=Qdot+α(1−Qdot)`匹配总体soft预测pair量。该α按输入确定、没有训练/dev选阈值；
不把B称为同parent forest的exact联合概率。零分母时D亦零，定义α=0。
它保留总体膨胀而移除pair-specific correction归属，能区分局部依赖价值与统一增分。
对照/aux loss/scale最终仍须在训练前冻结；toy保持总量不同TP不证明部署效果。

作者要求的突破目标已预声明为strongest control上有实质主指标改进，目标及前瞻性
noise敏感性只见R1 §25.51。location-noise功效是有假设的设计分析，不是预测真实改进
或未知full-model方差；方法仍未准入，最终绑定须等强对照与预算/损失合同闭合。

## 2026-10-13 固定的判别设计（仍待单卡预算，不启动训练）

科研价值/可行性与power绑定只见R1 §25.55；原full-model零更新成本验证见§25.54。
本节冻结目标与对照，取代上文“具体loss尚未选择”的待办；不是GPU执行合同。

输入仍是全文/给定mention spans/types，监督仅train gold identity，所有臂从同一个
pretrained initializer和seed13出发。公共项为typed parent distribution上的规范
first-dummy marginal（clamp-before-sum与原实现一致）。保留原三个关系头loss/权重。
类型只约束parent候选：每个mention的dummy与同类型更早mentions，零阈值扫描。

对每doc按type分块，从合法parent probabilities计算C与Q。只取合法strict-lower
pairs，令Y为gold same-cluster，T=ΣS_ij Y_ij、M=ΣS_ij、G=ΣY_ij。
固定辅助项 `L_pair(S)=1−(2T+1)/(M+G+1)`。先跨同doc的全部type blocks汇总
T/M/G，再平均documents；空pair doc的loss严格为0。不能按block平均过度加权
singleton types。它是soft pair-F1 surrogate，不是E[F1]、MUC或原Le&Titov B³/LEA。

固定五臂：

1. corrected-marginal：公共目标，不加aux。
2. root-product：公共目标+L_pair(QQᵀ)。
3. exact：公共目标+L_pair(C)。
4. mass-matched：公共目标+L_pair(B)，B=Qdot+α(1−Qdot)，α在每个
   doc/type block按§25.52合法pairs定义。α参与autograd，不stop-gradient；
   总量匹配在每次forward成立，不能把它称exact forest probability。
5. assignment-shuffle：公共目标+L_pair(ΠCΠᵀ)，每个doc/type block由
   SHA256(`seed13|doc_id|type|mention_id`)排序生成固定permutation，singleton恒等。
   它保留diag/合法type/pair score multiset/总量，打乱监督中的mention-pair归属；
   是aux assignment负控，并非只移除共享祖先的特殊分量，不夸大因果解释。

总目标固定为 `.4*(L_marginal+L_pair)+2*L_temporal+4*L_causal+4*L_subevent`；
第一臂L_pair=0。所有结构臂同surrogate/scale/decoder/候选/backbone/预算。
正控marginal与任何aux臂的差异只可解释为加入结构监督；exact对root/mass-matched
是联合依赖归因比较，exact对shuffle是pair-assignment有效性比较。
不依赖aux loss下降宣告MUC提分，不扫aux权重。

Endpoint固定为原100epochs预算的最后一步，所有臂不在internal-dev/final-valid
选checkpoint/epoch；内部291doc仅在各臂endpoint完成后导出一次统一评分。
原best-dev模型与新的fixed-endpoint控制具有不同选择过程，明确保留其旧强锚身份；
方法仍须胜过该typed强锚以及同预算的corrected marginal/root/mass对照，
不能靠新的控制欠拟合过门。优化器/梯度累积/scheduler沿原同架构实现；
选卡/训练批次chunk策略属于工程配置，必须空卡成本验证后按全部臂相同规则冻结。

正式合同与生产method实现仍待：实际单卡峰值/optimizer headroom/完整预算、
原架构与未来aux的开销边界，power绑定已经完成并采用明确的条件性规划假设（R1 §25.55）；仍不声称真实新训练方差已测。
当前method_admitted=false；资源等待不等于路线不可行，也不恢复已封存控制。

方法promotion/止损在结果前固定：exact的官方MUC须达到预声明突破目标，同时
超过原typed强锚与所有同预算正对照；其余三个官方共指指标B³/CEAF/BLANC
不得低于原typed强锚及corrected-marginal。exact-vs-root和exact-vs-mass是两个
预声明归因比较，需正的paired document差异及对应区间支持，shuffle需表现更弱；
辅助loss下降不能替代任一项。配对区间只作该单seed评测单位证据，未调整的
多个区间透明标探索性，不恢复旧Holm/24条件或冒充跨seed确认。
完整原joint三个关系任务同endpoint一并报告，区分aux的共指收益与共享任务代价。
任一关键比较失败则记录负结果并停止该固定配置，不改scale/endpoint/decoder
或加预算挽救；协议/实现错误需要单独TDD修复及新身份，不能静默覆盖结果。

2026-10-14：固定四aux的数值/空pair/确定性边界与差分检查、全train label/
uniform-parent先验审查完成（R1 §25.56–§25.57）。明确保留“概率整体膨胀后aux
可能使模型更保守，FP下降但FN增加”的竞争解释；当前只有密度/构造prior，
没有真实模型的update direction或收益。保持固定loss/scale/五臂/endpoint，
不以研究prototype通过解除单卡/实际结构预算与正式合同边界。
