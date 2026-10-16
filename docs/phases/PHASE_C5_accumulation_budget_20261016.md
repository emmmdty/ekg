# C41-B：固定四microbatch的累积/全train形状成本补验

目的：补足r2两步未测的真实gradient accumulation4，以及chunk最坏输入未覆盖的
关系head与type-block组合。仅科研准入成本，不是production训练或效果检验。

固定seed13、规范2c7ff1…initializer、原四头架构、given-type parent policy、五臂loss/
scale沿joint brief及r2配置，不修改封存代码/数据/结果。CPU测试证明平均梯度与实际
optimizer状态/步频、拒绝nonfinite loss/nonzero LR/残余梯度后，真实远端CPU门及
本地三件套通过才能CUDA；每项空卡单卡，GPU3历史故障不自动解除。

新入口profile_c5_accumulation_budget.py复用封存core.objective及r2完整性hook。
每臂固定2周期，每周期依次peak、worst、relation-envelope、structure-envelope。
后两fixture只按完整train shape选取，与标签值/模型分数无关；相应doc IDs/hash在
config绑定的shape_report内固定。前两fixture沿旧census不变。每microbatch8doc，
loss/4后backward并释放图，4次反向后scorer Adam→encoder AdamW→encoder scheduler。
zero_grad(set_to_none=True)仅在周期末；不清中间梯度。第二周期测真实moment state驻留。
encoder scheduler总步数32800/warmup200，probe LR全程严格0，不承诺学习态轨迹。

各microbatch记录同步forward/backward时间（包含本次transfer）、transfer时间单列，
allocated/reserved、梯度bytes/参数数；周期记录实际optimizer state、API span与去掉
r2 CPU完整性hook后的native时间、RSS、scheduler计数。finite-gradient审查及参数
hash属于审计，不能作为production时间。API两optimizer×2周期=4；逐值相等且只恢复
已证零符号，记录native变化与收据；非零数值更新失败，不恢复来掩盖。

所有臂相同fixture、预算和zero-LR规则；不做epoch/dev/final-valid/权重导出。
输出exclusive-create：r1-v69-c41-budget-20261016/accumulation/<cpu|cuda>/<arm>/。
失败failure.json与log保留；不得缩batch/改scale/改fixture去救结果。

实测用于透明保守外推328microbatches×100epochs/8200optimizer steps，分别说明
每臂time/峰值/RAM/IO/并行总预算，不能称实测完整epoch或严格最坏界。全train的不同
shape组合、学习态数值/未知运行方差仍披露；必要性裁决不能被成本PASS替代。
方法仍须C41-A两段准入，任何成本结果都不构成方法MUC或创新证据。
