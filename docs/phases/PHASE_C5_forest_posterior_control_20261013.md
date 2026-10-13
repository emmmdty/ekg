# C-41 · forest posterior-score 固定控制

科研价值、可行性与结果前动作见 R1 §25.47，数学候选见 §25.46。
本合同仅准许零训练的 derived controls；不准入 proposed 方法训练或创新结论。

原 291-doc 无标签 score/input/manifest/P1 evaluator 与 stronger given-type control 不变。
原合法 antecedent raw logits 和 dummy logit0 做稳定 softmax，typed original/cache 与
合法归一化后的 baseline decoder 都要求全量 exact parity，失败即停止。

固定三个 score 臂：exact joint connectivity、root-marginal product、ancestry shuffle。
C diagonal1 服务递推，decoder diagonal仍为原 dummy probability；real score为 C_ij。
root 递推 Q_j=Σ_{k<j}p_j(k)Q_k，Q_jj=p_j(dummy)，real score 为 Q_i·Q_j。
负控每个 j 在同类型组同步置换较早 exact C 的行/列，保留 diagonal1，然后乘原 p_j。
每 doc RNG13，当前 direct parent scores 不改；不递归使用负控作为后续真实 C。

不用 train/dev gold 做拟合、选档、选动作或扫参。不换 head/encoder；不扫描 cluster
linkage/温度/null threshold；原官方 argmax decoder、全 mention IDs 与关系字段保持。
pair posterior events 可重叠，row sum 不要求1，不宣称这些 scores 是 antecedent 分布。

本地三件套与原机 CPU Torch 对应用例通过后，原机 CPU 执行全量 cache 重放，CUDA隐藏、
四线程；不加载 neural checkpoint。新输出 `forest_posterior_control/` 已存在即拒绝覆盖。
各臂与 baseline 用冻结 evaluator/candidate digest 独立复算 MUC/B³/CEAFe/BLANC、配对区间。
未胜 strongest control/护栏退化即停止此部署规则；未胜 matched product/负控不归因给
精确共享前件。结果如实封存，单 seed/exploratory，不替代方法 novelty/input/power 门。
