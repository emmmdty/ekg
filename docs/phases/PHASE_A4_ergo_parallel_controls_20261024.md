# ERGO并行控制合同（2026-10-24）

C41-A-R，原论文已知控制，科研价值/可行性/证伪与来源见R1 §25.128。作者要求其他卡并行，
主表已先更新。原卡1 full训练不变；卡0 complete_graph、卡2 gamma0；卡3保留。

两项都复用[原训练/选模合同](PHASE_A4_ergo_native_training_20261018.md)完整设置，
只改变单个原组件。complete_graph保留RGT/所有参数/初始化和对角mask，将所有非对角
边放开；gamma0保持原graph/alpha=.75，仅将原focal gamma从2改0，为加权CE。
不加第四组合臂、阈值/seed/更大backbone，不将已知控制当新方法。原full已经启动的
时序按R1披露，不能声称整个比较早于原full运行。

训练/生产/独立验证均复用原项目入口，以精确AST在唯一LongformerCausalModel构造后
安装控制；原source文件不改，执行前保存原/派生源码SHA和派生源码。任何匹配歧义拒绝。
这只是配置/边界接线，原公开RGT/损失类/train_epoch均不重写。完成后checkpoint仍须
在相同控制下独立重载，完整classes逐值一致，再过官方causal scorer与预定doc配对分析。

先做本地测试/ruff/smoke及原机隐藏CUDA CPU测试，再分别原模型worst/longest两个train
病例lr0反传及驻留optimizer最大无标签dev两次shadow-target前向。每卡预检最多1200秒，
不读dev gold、无epoch/保存；参数初始身份必须与原full生产报告一致。通过后用各自
实测工期、固定完整20epoch、独占配置/输出放行，仍seed13。源/输入/hash不一致、非有限、
OOM、超时保留失败不重试，不缩doc/候选/精度。不会重复旧CPU模型准备。

正式完整训练各epoch完整internal-dev官方causal F1，strict >、最早tie；所有epoch预测/
classes/选择记录保存。相对full为两个各自单变量差值，保留原三对照主表，不挑最弱锚。
full/controls均是透明native适配FR-016(b)，无原基准数字复现；其他family不适用。
精确GPU命令、正式配置SHA、实测预算及实际产物在执行前补入R1与本合同，不凭本文
启动未经CUDA门的完整控制训练；final-valid/额外seed/5090/跨机checkpoint边界保持。

## CUDA production精确命令（先于完整训练）

主机`gpu-4090`，cwd `/data/TJK/ekg`；分别核空卡后各发一条SSH/一个后台任务：

```bash
setsid nohup env CUDA_VISIBLE_DEVICES=0 PYTHONPATH=src:scripts OMP_NUM_THREADS=12 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 timeout --signal=TERM --kill-after=30s 1200s .venv/bin/python -u scripts/run_ergo_native_control.py --operation preflight --config configs/ergo_control_complete_graph_preflight_20261024.json > logs/ergo-control-complete-graph-preflight-20261024.log 2>&1 < /dev/null &
```

```bash
setsid nohup env CUDA_VISIBLE_DEVICES=2 PYTHONPATH=src:scripts OMP_NUM_THREADS=12 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 timeout --signal=TERM --kill-after=30s 1200s .venv/bin/python -u scripts/run_ergo_native_control.py --operation preflight --config configs/ergo_control_gamma0_preflight_20261024.json > logs/ergo-control-gamma0-preflight-20261024.log 2>&1 < /dev/null &
```

配置SHA分别为`10c63ffb183b7dc140522d8c40327489c76674ce944d7e4757ac4374ed3c11f9`及
`33140aa24e4b2f86cceee0d4313fd16a9a9eab9f0f1d3a739b0ebef71c7b2dc2`。
预期各自`runs/stages/R1/r1-v105-ergo-parallel-production-20261024/{complete_graph,gamma0}/`
下production/capacity/status，旁侧各`*-execution/`存派生原入口和执行身份。初始参数数值SHA
须与R103 full一致；失败保留各自证据，不取消已启动的另一独立任务、不自动重试。

## R106正式训练（R105两项真实CUDA门通过后）

R1 §25.128给出实际CUDA及预算证据；两个新正式配置分别为
`configs/ergo_control_complete_graph_training_20261024.json`（SHA
`962af7b03839954eedacb1cdddddd8a98617918a9687b1d5efa4da5f938b6778`）和
`configs/ergo_control_gamma0_training_20261024.json`（SHA
`4d3d7425142518f8c954de2cd40a56717539ad49b80f0a76ab3e714c96743fac`）。
主机/cwd仍为gpu-4090 `/data/TJK/ekg`，先成功核卡0/2空卡，各独立一条SSH：

```bash
setsid nohup env CUDA_VISIBLE_DEVICES=0 PYTHONPATH=src:scripts OMP_NUM_THREADS=12 TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 timeout --signal=TERM --kill-after=60s 173400s .venv/bin/python -u scripts/run_ergo_native_control.py --operation train --config configs/ergo_control_complete_graph_training_20261024.json > logs/ergo-control-complete-graph-training-20261024.log 2>&1 < /dev/null &
```

```bash
setsid nohup env CUDA_VISIBLE_DEVICES=2 PYTHONPATH=src:scripts OMP_NUM_THREADS=12 TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 timeout --signal=TERM --kill-after=60s 173400s .venv/bin/python -u scripts/run_ergo_native_control.py --operation train --config configs/ergo_control_gamma0_training_20261024.json > logs/ergo-control-gamma0-training-20261024.log 2>&1 < /dev/null &
```

预期各`runs/stages/A4/a4-ergo-control-{complete-graph,gamma0}-20261024/seed-13/`
保存原训练器的config/status/20epoch预测classes/best.pt/完整report；旁侧seed-13-execution
保存本次原/派生入口身份。checkpoint留原机。SSH parent等待实际退出码，网络失败不推
任务死亡。真实完成后用同一wrapper `--operation verify`独立重载，不能用裸原入口漏装
control；执行前另披露验证命令。不根据较早分数缩预算/调参数；四卡不是必须全部填满。
