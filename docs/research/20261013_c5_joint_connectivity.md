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
算力边界是 ordered forest 的递推通常 O(n³) 时间/O(n²) 内存，给定类型可分块。
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

frozen null 控制实测已完成且未胜 strong control，停止该控制（§25.45）。当前先执行固定零训练 posterior-score 控制（§25.47）；推理分数对照不能替代监督创新的准入。拟议的最小判别是：
相同 frozen representations/head/input/预算下，ordinary null loss、root-marginal product
cluster-pair loss、exact joint cluster-pair loss，以及固定 ancestry shuffle 负控。
loss 或 decoder 只能择一作为单变量；不能同时换两者后把收益归给联合依赖。

目标效应、document-level MDE/≥80% power、具体训练 loss、无调参 endpoint、匹配强对照
与护栏尚未闭合。数学恒等式、toy 反例、文献差异都不替代部署主指标。
