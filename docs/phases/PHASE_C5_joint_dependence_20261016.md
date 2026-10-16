# C5 joint-dependence：固定seed13五臂生产合同

冻结时`design_admitted=true`、`method_admitted=false`；最终准入只认本合同配置绑定的
admission.json及真实测试证据。设计裁决见research/20261016_c5_design_admission.md，
R1 §25.70；预算及局限见§25.69。此合同独立于封存role家族，不改旧bundle。

## 问题、可行性与固定干预

对准表5-3/KR1.1–1.2：相同typed parent模型与soft pair-F1下，保留共享前件joint
依赖的监督是否胜过root-product及总量匹配？最近邻、输入/监督边界、假设与竞争解释、
条件power及敏感性沿joint brief/R1 §25.55，科学阈值不在此改写。
官方Model/data/utils/dump_result以固定hash原样接入；本项目目标抽取到
core.joint_connectivity，registry名forest_pair，torch惰性导入、CPU概率cache回放。
不声称忠实复现Le & Titov原B³/LEA完整系统；root臂是其关键机制的同surrogate强对照。

全臂text/spans/task-given types相同；监督仅冻结train identity及三个关系标签。
parent候选为dummy或同type较早mention；全部原完整评测ID保留，类型策略逐表披露。
训练/推理TIMEX及候选规则沿原joint：共指仅event mentions，关系encoder保留TIMEX，
temporal输出含TIMEX，causal/subevent不输出TIMEX pairs；不裁评测全集。

## 固定五臂与执行

arm=marginal/root/exact/mass/shuffle；分别是规范first-dummy marginal、加pair-F1(QQᵀ)、
加pair-F1(C)、加pair-F1(mass-matched)、加pair-F1(assignment-shuffle)。数学/聚合/
alpha求导/空pair/shuffle种子串沿已冻结brief与research probe，不调aux权重。
总loss=.4*(marginal+auxiliary)+2*temporal+4*causal+4*subevent。
parent型约束/原dummy logit0、argmax parent decoder与tie rule全部同臂；不扫阈值。

全部同规范initializer、seed13、FP32、原四头架构、max_length256、batch8、accumulation4、
100epochs末步。scorer Adam lr3e-4→encoder AdamW lr2e-5→encoder scheduler；
两optimizer各自默认betas/eps/weight_decay沿原source与已核torch栈。
encoder scheduler warmup200/num_training_steps32800，实际8200次update；不静默修正。
梯度跨epoch保留原global-step规则，最终无残余；无clipping、无zero-LR hook、无AMP。
启用已经验证loss/梯度等价的nonreentrant checkpointing、preserve_rng_state。
不同臂单卡并行，最多现有空4090卡0/1/2，CPU4线程/臂；GPU3历史故障不自动解除。

所有臂不在dev/final-valid选checkpoint/epoch；每臂仅末步保存模型/双optimizer/
scheduler与身份。末步后一次完整291doc未标注internal-dev预测，raw logits、typed parent
probabilities、官方共指/三个关系结构齐全。**全部五臂endpoint完成后**统一官方评分，
无训练中dev指标、无提前看一臂选设计。checkpoint留4090，不跨机搬运。

## 生产门与独占产物

- parity：远端CPU隐藏CUDA，固定peak8 train全四头、五臂分别对封存research loss/
  所有参数梯度核验；同loss/term严格相等，梯度沿原rtol1e-4/atol1e-6，参数不更新。
- smoke：同配置hash且parity完整后，五臂各一个真正非零LR optimizer周期，按
  peak/worst/relation-envelope/structure-envelope四个8doc微批；不读dev/final-valid。
  只将peak8 train转换为去identity/relation金标、保留given-type/span的未标注输入，
  用同production导出完整关系与共指、CPU cache/source-decoder逐doc parity；不计算分数。
- train：真实torch测试、本地三件套、parity与五臂CUDA smoke全部通过后，冻结
  admission.json（config/code/证据SHA、P1/evaluator/输入身份）。入口逐项重核后才可执行。

根runs/stages/C5/c5-joint-dependence-20261016；parity/all、smoke/<arm>、train/<arm>
均exclusive-create；已有路径绝不覆盖。status含PID/commit/config、失败保留error/log，
独立日志，setsid nohup；每条SSH只启动一个任务，不建等卡/自动重试启动器。
源码/输入漂移、缺ID、nonfinite、OOM或parity失败立即停止，先查工程原因并另建身份；
不得偷偷缩batch、更换initializer、扫scale或用失败log当科学结论。

## 结果、归因、护栏与止损

exact必须达到原预声明相对strongest control的突破目标、胜旧typed强锚及所有同预算
正对照；B³/CEAFe/BLANC不得低于typed强锚和corrected marginal。两个主要归因比较
exact-root、exact-mass需正的paired document差异及区间支持，shuffle须更弱。
单seed未调整区间透明标探索性，训练方差未知，不恢复撤销的Holm/24条件。
原baseline与外部名册的已知协议/FR-016身份继续报告，不能用弱对手冒充强竞争方案。

独立官方MUC/P/R/F1及其他共指指标、三关系主指标、pair错误交换与missing/spurious
完整报告，原预测均可复算。只胜marginal不能声称joint-dependence归因；辅助loss/
概率一致性/成本PASS不能代替主指标。关键科学比较失败即停固定配置，不改scale/
endpoint/decoder/预算挽救；如实保留负结果并按主表有证据回R1，不结束长期Goal。
额外seed、final-valid合法封存及跨机checkpoint搬运仍须各自前置/授权，不由本合同放开。
