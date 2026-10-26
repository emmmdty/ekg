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
