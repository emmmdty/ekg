# C41-A第一段：joint-dependence候选设计准入

日期2026-10-16。持有队列的执行代理作顺序PI/方法自审，依作者既有委托裁决；
不是独立同行评审。`design_admitted=true`，`method_admitted=false`。
当前唯一任务仍C-41/T087，第二段生产实现/真实测试/合同未完成，不能启动正式五臂。

## 科研价值与可行性

表5-3/KR1.1–1.2的问题是：同一个typed parent模型的共享前件依赖，在**训练目标**中
保留精确joint pair概率，是否较相同surrogate的root-product和总量匹配更有用？
数学、求导、train机会与NN梯度证据认R1 §25.46/§25.49/§25.52/§25.56–§25.61；
它们未证明新训练会赢。原固定decoder、null及first-dummy适配控制失败仍封存。

数据：只用冻结MAVEN训练监督与task-given spans/types，无新语料、来源/scope gold、
论元预测或teacher错误标签。train/dev与候选/ID门沿当前P1，final-valid封存。
协议：保持manifest、完整候选、官方evaluator、TIMEX训练/推理成对、seed13与原架构。
代码：官方Model/data/utils不改，复用本项目已核目标，以生产组件接线，记录抽取来源。
算力：C41-R/B原机身份、完整CUDA结构/真实state/accumulation及保守预算已经闭合
（R1 §25.68–§25.69）；未知学习态/运行时方差仍需生产smoke与运行中fail-fast。
授权：4090空卡可用；此设计不调用5090、增加seed或跨机搬checkpoint。

## 最近邻与贡献边界

复用C41-L及joint brief中已核的正文机制/固定官方源码，来源身份见R1 §25.46及
10-15 source ledger；本次不把同一批检索重新包装为新综述。
Le & Titov已有root-membership递推、membership乘积和可微cluster指标；Rennie/
Samdani/Yang/Lee/Wick/Yadav已有forest、link聚合、多跳或cluster uncertainty。
候选不声称发明这些机制，也不否定Le & Titov原B³/LEA目标。具体差异限定为
ordered independent backward-parent forest下，以保留共同随机祖先依赖的C替代
root-product，进入**同一soft pair-F1 surrogate**的训练；推理仍用原typed argmax parent。
检索边界内未定位完全相同训练设计，不是普遍不存在证明或已成立创新。
最近邻公开完整系统的运行障碍/不同任务见既有roster，不用方法名冒称忠实复现。

## 可辨认的固定比较

沿20261013 brief、R1 §25.55冻结的五臂/loss/scale/endpoint，完全不加第六臂：
corrected marginal、root-product、exact、mass-matched、assignment-shuffle。
全部同pretrained/seed/原head/full-text/typed parent policy/decoder与优化预算。

- exact只胜marginal：最多支持加结构监督，不能支持joint-dependence归因。
- exact须胜root与mass：分别排除普通soft cluster目标、整体pair概率量增加的充分解释。
- shuffle须更弱：支持正确pair assignment的作用。shuffle同时扰动局部与间接对齐，
  不能声称只切掉共享祖先这一中介。
- 原typed stronger anchor保留历史best-dev身份，新控制使用固定endpoint；必须同时超过
  旧强锚与新同预算控制，控制训练不足不构成方法收益。所有外部主表身份继续透明披露。

主要结果/突破目标、B³/CEAFe/BLANC更严格护栏、关系任务完整报告及stop原样沿brief。
独立官方计分与document bootstrap/错误交换沿既有evaluator；主要两个归因比较分别报告
区间，单seed未调整区间标探索性，不称跨seed确认。没有结果驱动的阈值/scale/epoch选择。
全臂endpoint完成才统一internal-dev评分，训练期间不看dev/final-valid曲线。

既有强控制的pair-error/过合并和漏合并交换按预先已用的报告器完整给出，不只挑高相似
子集或变化最多的例子。pair改善是诊断，不能代替MUC、归因比较及护栏。
功效认R1 §25.55的冻结条件规划与敏感性：未知训练方差未测，不能承诺观测差异显著；
新噪声若违背原envelope，报告设计失配，不按新结果改规划或擅自增加seed。

## 第二段的可执行交付

1. 以TDD把本项目目标从research入口抽取为registry+lazy-torch生产组件，封存research
   源码不改；CPU缓存回放核全部臂的loss/梯度/类型/空pair边界和源实现parity。
2. 接线官方Model与原batch8/accumulation4/optimizer顺序/历史scheduler语义，固定末步；
   无zero-LR完整性hook进入production训练，所有臂使用同打包/精度/线程/单卡规则。
3. 本地三件套、远端真实CPU全参数parity与受限train-only CUDA smoke后，冻结phase/
   code/config/input/evaluator/checkpoint lineage与smoke证据，最终method admission。
4. 正式准入后空4090滚动运行五臂；独占输出、失败保留、不创建自动等卡/重试启动器。
   全臂完成立即V，不以训练启动、阶段提交或单项PASS结束长期Goal。

**设计裁决**：当前证据足以进行有边界、可证伪的完整同预算实验，故准许第二段生产实现。
这不是创新或效果PASS；若实现/协议门失败，先保留工程失败并独立修复；若正式关键科学
比较失败，停止固定候选，按既有授权有证据回R1而不扫参救它。科研技能仅辅助组织审查，
不作科学结论；来源与授权关系沿RESEARCH_SKILLS.md。
