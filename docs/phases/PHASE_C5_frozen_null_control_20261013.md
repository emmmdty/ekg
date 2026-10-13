# C-41 · frozen representation + train-only null 控制

科研价值/可行性见 R1 §25.45。针对首提及误连与错误 dummy 的实际覆盖，
复用已知 anaphoricity/calibration 思想训练强控制；不是新方法贡献，不替代 R1 准入。
原官方 encoder/scorer/checkpoint 冻结在 4090；仅新 head 学习。原/新权重均留原机。

冻结 train/internal-dev manifests 不相交。train source 为原 baseline 的 train.jsonl；
dev 使用原无标签 test.jsonl。特征导出时只把 token/span/splits/attention 传给原 encoder，
identity 只在 train 特征之外派生 supervision，不作为 encoder/scorer 输入。
dev feature cache 必须不含 labels，全部原 logits/type-control clusters 必须 exact parity。
两套特征 cache 与训练/预测 metadata 均保留独立 namespace，不覆盖旧产物。

全合法候选 policy 与 stronger type-control 成对：类型只从 task-given 输入取得。
无同类型前项时按定义强制 dummy，不拟合；所有其余 train mentions 参与，零负例采样。
监督是当前 mention 是否有任何同 gold event 的先前 mention，不是 singleton 标签，
也不是原 baseline 的错误状态。这里不把 in-sample teacher 表示冒称 OOF error supervision。

三个 embedding 块：current、mean same-type prior、top original legal prior。
三个 numeric 项：max original legal logit、logsumexp legal logits、log1p legal count。
三臂固定为 semantic、numeric_only（embedding 块置零）、shuffled_semantic
（只在 train 的 doc/type/opportunity 桶内置换 embedding 块）；opportunity 桶为
0 / 1 / 2–4 / ≥5，置换 RNG 13。标准化仅 fit train，推理只 transform，无 dev 拟合。
shuffle 小桶可能不产生改变，负控能力必须如实说明。

head 为 Linear→ReLU→Dropout(0.2)→Linear，hidden 200；Adam lr=0.001、BCE、
batch=512、固定最后 epoch=10、seed=13。各控制同形 head、相同初始化/训练预算。
不读 dev target、不选 epoch、不扫 class weight/阈值/结构。不是额外 seeds。

令 head 输出 z=logit(q)，原合法前项 raw logits s 不改；dummy raw logit
d=logsumexp(s)−z，使所有 real 的总质量为 q，real 之间的条件排序保持不变。
原官方 argmax/decoder 输出 cluster。没有合法前项时 q 不用于连链，完整 mention IDs 保留。
关系字段只复制，encoder/scorer 零 optimizer steps，原标签文件不进生产推理。

本地三件套 → 4090 真实 CPU Torch 测试 → 双作用域 smoke → 完整 train/dev cache
→ 三臂固定 endpoint fit → 官方独立评分/配对复算。GPU 全隐藏，CPU threads=4、
encoder batch=8/max_length=256。新根为
`runs/stages/R1/r1-v63-c5-20261013/frozen_null_control/`，既有 output 拒绝覆盖。
checkpoint 不回传；非权重 report/predictions 双端核 SHA 后交接。

报告 MUC 与 B³/CEAFe/BLANC，保持 frozen anchor/type-control；semantic 还须对照
numeric_only 与 shuffled。若主指标未胜或护栏损失，停止该固定控制，不事后调整。
赢过某个消融但没胜 type-control 不算有价值的指标提升。任何正结果仍标 single-seed /
exploratory；不能以已知控制收益宣称机制新颖性、R1 power PASS 或章节贡献 PASS。
