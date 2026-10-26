# ERGO内置unweighted CE已知强控制（2026-10-26）

唯一队首C41-A-R/T087。价值/可行性/限制认PHASE_R1 §25.134–§25.135及主表最新覆盖。
原三臂已封存，本轮只一个固定unweighted_ce，非第四个graph×gamma组合、alpha/gamma/lr
扫描或本项目原创。作者原`model.py`已有`ce_loss`及`loss_type`分支；只在唯一模型构造
后选`loss_type='ce'`，focal对象/graph/参数/原train_epoch/AdamW均保持，原文件零改动。

gamma0保留[.25,.75,.75]权重，并非普通CE。CE与该加权目标还有loss scale/优化路径差别，
故比较回答一个已知训练替代是否更强，不能把差值全部归因于alpha或已清除词面偏置。
普通matching/contrast创新表述在CNC最近邻前未成立，不借其增加额外训练臂。

薄入口`run_ergo_ce_control.py`把冻结`run_ergo_native_control.py`当库执行，配置同时pin
两文件；独立namespace仅换控制白名单及installer，runner记录本extension SHA，原helper
另受pin。原训练/预检/独立核分入口仍通过既有唯一构造点AST安装，不重写模型或评测。
独立重载必须同CE selector；不可用裸verify入口漏装干预。

先本地三件套，再原机隐藏CUDA实际8项相关CPU测试：包含原官方forward/RGT/loss、
替换为tiny encoder的损失选择/逐值logits与state不变/反传有限检查；不称它为原大encoder
实际训练。真实CPU测试不许skip，源码/配置身份和XML检查后再放行CUDA。

CUDA生产/容量只在空4090 GPU1；同既有worst/longest最大train两个病例，原函数lr0反传，
驻留optimizer最大无标签dev两次shadow target前向，full4096/float32/完整候选保持。
必须初始参数与原full生产报告一致、有限、lr0值不变、target不影响logits。无epoch/dev gold/
checkpoint输出；超时/OOM/漂移原样留证，不缩输入或自动重试。CUDA门过后才裁正式预算。

主机`gpu-4090`，工作目录`/data/TJK/ekg`。CPU门和正式config pins实证闭合后、执行前再次
核卡并披露下列GPU命令；当前写命令不表示已启动：

```bash
setsid nohup env CUDA_VISIBLE_DEVICES=1 PYTHONPATH=src:scripts OMP_NUM_THREADS=12 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 timeout --signal=TERM --kill-after=30s 1200s .venv/bin/python -u scripts/run_ergo_ce_control.py --operation preflight --config configs/ergo_ce_preflight_20261026.json > logs/ergo-ce-preflight-20261026.log 2>&1 < /dev/null &
```

预期`runs/stages/R1/r1-v112-ergo-ce-production-20261026/ce/`含production/capacity/status，
旁侧`ce-execution/`含execution/派生入口/身份。CPU门在`r1-v112-ergo-ce-admission-20261026/`。
完整训练另冻结`ergo_ce_training_20261026.json`与实测预算；当前无训练准入。

拟议正式训练仍原seed13/20epoch/4096float32/原batch1和optimizer，完整同轴native数据。
每epoch完整internal-dev官方causal F1、strict >、最早tie；原/CE全部端点如实报告，不据
早期分数减epoch、扫threshold或挑弱对手。三项既有full/gamma0/joint及A3/Taco作为既定
对照，选中checkpoint在4090独立重载、classes逐值/official分数/配对复核后才验收。
控制即便提高公开指标仍是FR-016(b)已知透明适配，不抵三个独立方法贡献。权重原机留存，
final-valid、额外seed、5090和跨机checkpoint权限不扩大。

原机真实CPU门已完成、0 skip，证据见R1 §25.135。正式CUDA配置已冻结：
`configs/ergo_ce_preflight_20261026.json` SHA
`00e184864c55699e426dde28f30b708db8718aa163324b285e88bd4b5ab64073`。
CPU-only清单SHA `42c90d03731d1532e99371c81c7a444d38dbe6edba621727a61344686c3cb6dc`。
下一部署/核卡后执行上列固定GPU1命令；该段不构成完整训练准入。

## 一次已有成本入口的cold/warm核验

R112实际CUDA已过；两个production batch含首批成本，与旧gamma0短测差异较大，
R1 §25.136记录为何尚不能直接预算。原`profile_ergo_native_cost.py`本来支持
`model_args.loss_type`，故直接使用CE配置，不写新cost脚本或改旧入口。
只一个最大train病例、两个lr0 call，timeout1200/kill30，不是epoch或新增seed。

配置`configs/ergo_ce_steady_cost_20261026.json`，SHA
`4872d658af229a1b0617e7b3e43c4f947bce301fea0301f25a6013dd78aa5e3b`。
再次核空GPU1并在执行前披露：

```bash
setsid nohup env CUDA_VISIBLE_DEVICES=1 PYTHONPATH=src:scripts OMP_NUM_THREADS=12 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 timeout --signal=TERM --kill-after=30s 1200s .venv/bin/python -u scripts/profile_ergo_native_cost.py --config configs/ergo_ce_steady_cost_20261026.json --case cuda_worst > logs/ergo-ce-steady-cost-20261026.log 2>&1 < /dev/null &
```

主机/cwd仍gpu-4090 `/data/TJK/ekg`，预期
`runs/stages/R1/r1-v113-ergo-ce-steady-cost-20261026/cuda_worst/{report,status}.json`。
完成后合并原机完整run实际工时/本次warm计时作正式预算，预算前不启动完整训练。

## R113实际门通过后的正式训练

实测与保守预算见R1 §25.137，CPU/CUDA/init/成本/资源/原guard均闭合。
正式配置`configs/ergo_ce_training_20261026.json` SHA
`c52cac10be678bc4840bd9ee91e5f643e1c5183a1a2d525a1ba39b6f0edf6e9f`，
budget SHA `bf2b9f57bf8423a45bb1adef864daa02d9b30db3570d8eb15edc285a1bcfa136`。
只准一个已知CE、seed13、20epoch；epoch范围/数据/graph/float32/selection全部保持。
粗估7–9h，首个真实epoch后校正；wall48h只是保守操作预算，非保证。原R102 cost作为
旧架构证据，实际CE生产/稳态来自本轮，不混称为新的三份CE cost。

主机`gpu-4090`，cwd `/data/TJK/ekg`；先部署/严格核pins/空GPU1，执行前披露：

```bash
setsid nohup env CUDA_VISIBLE_DEVICES=1 PYTHONPATH=src:scripts OMP_NUM_THREADS=12 TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 timeout --signal=TERM --kill-after=60s 173400s .venv/bin/python -u scripts/run_ergo_ce_control.py --operation train --config configs/ergo_ce_training_20261026.json > logs/ergo-ce-training-20261026.log 2>&1 < /dev/null &
```

预期`runs/stages/A4/a4-ergo-control-unweighted-ce-20261026/seed-13/`有config/status、
全部20epoch classes/predictions、原机best.pt及完整report；旁侧`seed-13-execution/`
保存派生入口/selector/init/源码身份。失败/断线按真实ps/日志三态核查，不重复启动。
完整训练后同CE wrapper原机独立重载及五项同轴配对，之后才验收分数。本文不表示
epoch已开始或有科学收益；实际运行事实后补R1/HANDOFF。

## 有限三步执行入口（覆盖上方单独启动方式）

同一个已准入实验按依赖执行：训练成功→同CE wrapper原机独立重载→核验成功后的
五项CPU比较；失败即停，不自动重跑/调参/选新方案。不是等卡器或常驻科研服务。
新增`scripts/run_ergo_ce_pipeline_20261026.sh`，SHA
`568a677314bf26c39ebf5954c8cab33cac3f8ab1b83f991c5be0b4c762593135`。
原模型/selector/训练配置SHA保持不变；本shell只串接三个已验证接口，Git/launch audit
另外记录其身份。四项TDD用stub命令检查成功链、两种失败中断与旧日志保全，非真实GPU证明。

主机/cwd仍为gpu-4090 `/data/TJK/ekg`，严格核预算、五对照文件与空GPU1后执行前披露：

```bash
setsid --wait nohup bash scripts/run_ergo_ce_pipeline_20261026.sh > logs/ergo-ce-pipeline-20261026.log 2>&1 < /dev/null &
```

`--wait`让launcher可返回真实子任务退出码；训练/独立重载/CPU比较分别受173400/3600/300s
及kill60约束。原逐项命令在shell中完整保存，GPU阶段固定1、CPU比较显式隐藏CUDA。
附加预期输出：`runs/stages/R1/r1-v114-ergo-ce-independent-20261026/ce/`和
`runs/stages/R1/r1-v115-ergo-ce-comparison-20261026/report.json`、pipeline `.exit`状态。
只做这个固定控制的完整验收；即使exit0仍须科学解释，不能当原创/毕业门通过。
