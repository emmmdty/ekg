# 三方法章恢复：一手机制与可证伪诊断

本页是 C-37 的研究卡，不是模型结果页。实测计数、验证状态和 artifact hash 只认
[`../results/PHASE_R1.md`](../results/PHASE_R1.md) §25.34。
代理按作者委托选择：先建立强 baseline 的匹配控制与真实损失诊断，后判断新机制。
当前没有新机制准入合同，不能把本页当 G-22 训练许可。

## C-37 开工自审

科研价值：避免将失败臂的错误归因继续带入新机制，对准三章 frozen 主表与强 baseline。
一手机制须核正文/源码，不用关键词、新论文年份或低成本代替因果链与新颖性。
可行性：已有官方源码与模型资产、冻结预测可做 CPU 审计；A4 正式 checkpoint 在 5090，
本轮不为诊断跨机搬权重，先查训练态梯度及相同实现的 CPU fixture。
4090 可用作远端 CPU 测试，四卡占用期间不启动 GPU；资源事实不等于科学路线不可行。

## A4：共享参数干扰仍是待测解释

一手来源：Du et al., [Adapting Auxiliary Losses Using Gradient Similarity](https://arxiv.org/html/1812.02224v2)，
§2–3 与 Algorithm 1：共享参数的主/辅梯度夹角判别负迁移。
Shamsian et al., [Auxiliary Learning as an Asymmetric Bargaining Game](https://arxiv.org/html/2301.13501)，
§4：主辅任务地位不对称；作者 [AuxiNash](https://github.com/AvivSham/auxinash/tree/2e411c9053ed1907fed3cc3e7c94dbdfeced9366)
`methods/weight_methods.py` 的 `GCS.get_grad/get_weighted_loss` 实现 gradient cosine gate。
GCS 是该作者仓库中的公开对照实现，不冒称 Du 论文官方代码。

本项目 `train_a4_pair_evidence.py` 同时让完整文档 CE、retained CE 和 hinge 更新同一编码器。
`no_constraint` 只移除 hinge，仍保留 retained CE，不能单独排除这条路径。
旧“两个 hinge 在 base logit 上反向”结论正确，但它不推导共享参数上的抵消。

代理选择：先量主 CE、retained CE、hinge 各自在共享 encoder/head 上的梯度夹角、范数与组合方向，
检查真实训练行的分布；现有 fixture 只测试上述推论是否成立。
若真实梯度解释失败，下一检查转向训练/推理 revision 行分布和 backbone parity，不能继续凭故事改 loss。
如果要做 GCS 工程对照，直接使用公开实现、记录透明适配与 hash；
**GCS/PCGrad/改 loss 权重本身不构成本项目新机制**。不复跑 detach 修复，旧实验已否定它。

## C5：目标与解码的差异须先匹配

一手来源：Wang et al., [MAVEN-ERE](https://aclanthology.org/2022.emnlp-main.60/)，
官方仓库固定到 P1 同一 revision
[`ac81a9711a69f43f55bfbc50b3bb573fd11c64b0`](https://github.com/THU-KEG/MAVEN-ERE/tree/ac81a9711a69f43f55bfbc50b3bb573fd11c64b0)。
核读 `coreference/src/model.py:PairScorer`、`coreference/main.py` training loop、
`coreference/src/utils.py:get_predicted_clusters` 与 `joint/src/model.py:CorefPairScorer`：
antecedent 候选加 dummy、按 mention 的 antecedent 集 softmax、金 antecedent 概率求和取负 log、argmax 连链。
不能只读 README 的 pair-classification 概括。

本项目 `train_coref_scorer.py` 使用独立 pair CE，submission 的 `predict_coreference` 调
`canonicalize` 做平均链接与固定阈值。即使候选和官方 scorer 相同，训练目标与解码也不同；
这证明“对照完全匹配”的说法不成立，**尚不证明分数缺口全部由该差异造成**。

代理选择：复用已有 P1 官方 checkout/joint pipeline，先建目标/解码匹配控制；
核角色机制到底修复哪些错误、又制造哪些错误。sampler 改动已有反证，不继续扫 neg_ratio/threshold。
金标 event-level arguments 存在身份信息，只作 oracle；不移入可部署模型。
ACCI 已审计为缺可运行实现，不重写他人方法冒充复现。
若做同目标新信号，必须另给机制差异、可获得推理输入、单变量消融和负控，旧 role 家族仍封存。

## D4：输入、分类头与结构信号分别判断

一手来源：Li et al., [MAVEN-FACT](https://aclanthology.org/2024.findings-emnlp.651/)，
现有官方 `baselines/maven_fact/trainEFD/model.py` 的 `RawBert/DMBert`：
文本编码后分类，relation 模式分别编码 causal/precondition 文本并拼入特征。
这和本项目 causal logit residual 接法不同，不能拿原论文结构增益替本接法背书。
原文效果不在此处引用为统一协议数字。

本地 strongest CLS control 用 marked sentence；旧 typed-cue 臂使用不同输入/池化及五维 tanh bottleneck。
两者存在源码差异；不能跳过 matched intervention 把失败唯一归因给 bottleneck。
旧 causal-residual gold oracle 已反驳“只需更好边”的解释。

代理选择：先按 strongest CLS 的相同输入、打包、头与训练目标建立 parity；
再分别测试输入差异或决策头差异，不同时改变。严格区分基线恢复和方法贡献。
不复活旧因果 residual；若考察来源/模态 scope，先验证数据与预测 cue 信息，
不能用 gold supporting words 或 oracle 关系充当可部署输入。

三个诊断的预测、竞争解释、证伪和不确定结果已写
[`method_recovery_predictions.csv`](method_recovery_predictions.csv)，
由项目安装的 hypothesis-generation validator 检查结构；PASS 不证明假设成立或准入。

本轮一手代码快照及哈希清单：
`runs/stages/R1/r1-v61-20260904/audit/c37-primary-20261008/`。
源码路径最初按 `coreference/model.py` 猜测返回 404，随后根据 `main.py` 的实际 import
定位到 `coreference/src/model.py`；这是路径查找失败，不是实现缺失。


## C-38/C-39 开工自审与本轮范围

科研价值：三项验证分别隔离 head 参数化、共享梯度和 cluster 解码，检验上面的竞争解释；
对准 D4 macro-F1、A4 causal/subevent 与 C5 MUC 的强对照差距。证据入口是
`results/PHASE_R1.md` §25.34 和以上固定 revision 源码；不把诊断变好当作方法章通过。
可行性：D4 复用既有 OOF trainer/evaluator；A4 checkpoint 留在 5090 做 train-only 梯度读取；
C5 在原 checkpoint 所在机器导出 pair scores 后可 CPU 重放。数据和训练/推理函数已有，
无新增标注、final-valid、seed 或权重跨机搬运。GPU 空闲只影响 CUDA smoke/计算，不妨碍本轮实现。
本轮不做 GPU 训练/真实大模型推理；CPU 微型训练仅验证接口，不把 official antecedent training 宣称为已复现。
