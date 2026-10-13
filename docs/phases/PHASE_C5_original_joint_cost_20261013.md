# C5 / C-41 原 joint 零更新成本合同（2026-10-13）

目的：闭合完整架构反向与计算重算的等价性；不是 proposed method 准入或效果实验。
科研价值/可行性预声明见 `results/PHASE_R1.md` §25.54；主表 C-41。

复用锁定官方 Model/data/utils、P1可信根、原train manifest与pretrained内容地址，
seed13，max_length256，原始四头loss与权重0.4/2/4/4。不修first-dummy目标、
不加类型mask，不改变候选或loss；成本结论只用于该架构，不外推新目标开销。
不读dev/final-valid，不加载teacher checkpoint。零optimizer/更新/权重导出。

每个fixture从同一初始化/forward RNG执行checkpointing off/on；nonreentrant、
preserve_rng_state=True。loss绝对差≤1e-6，所有有梯度参数同集合、有限值，
allclose rtol1e-4/atol1e-6；逐参数SHA不变。FAIL保留，不能事后放宽容差。
输入为§25.53原tokenization census两组固定8doc IDs，重算shape必须匹配原chunks。
CPU四线程/隐藏CUDA；GPU仅在4090成功核空卡后选单卡，且启动前披露命令。
GPU入口自动拒绝有compute process或memory.used≥512MiB的卡。

记录各臂完整forward/backward时间、梯度误差、原始参数hash、真实chunk数；
CUDA peak allocated/reserved仅CUDA执行记录。CPU RSS是进程累计峰值，包含
parity缓冲，不能用于checkpointing内存对比。两份FP32 Adam moments大小
仅投影；无optimizer实测，也不能把单batch时间称完整epoch预算PASS。

原源码与完成产物不可改；输出 `original_joint_cost/<device>/<fixture>/`
exclusive-create。配置pin入口、原源码、train/P1/census/合同SHA与pretrain内容摘要。
失败后如需改代码，必须新身份/新namespace，不覆盖已运行路径。
