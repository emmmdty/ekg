# ERGO冻结权重的native训练拟合诊断（2026-10-25）

同队C41-A-R/R109，科研价值与可行性见R1 §25.130。只诊断已有full选中checkpoint，
不用结果重选epoch/阈值或调训练参数，不把in-sample数字当主表/held-out成绩。

## 固定身份与范围

- 完整20epoch原full报告及其选中checkpoint（R107已独立核过）；原配置
  `configs/ergo_native_training_4090_20261024.json` SHA
  `5743397bd4f4f1d452a6e6ec9d692dba5c590ce1d58c27859681185806ee5f41`。
- 仅原train2622doc/2297524候选，R192 cache-global features/targets及原train manifest/
  candidate digest保持。独立targets仅在forward外计数，输入中的target永远为零placeholder。
- 原公开Longformer/RGT/focal类/原full权重，FP32/full4096/原BOS-EOS mask/完整候选保持；
  eval/no-grad/argmax三类，TF32关闭；无optimizer/backward/新训练/seed/阈值搜索。
- native三类定义NONE/PRECONDITION/CAUSE；错subtype同时计FP/FN。先核真实官方scorer
  toy与已有R107/R108 dev混淆的P/R/F1相等，不能拿原binary train log代替。
- 新增独立`diagnose_ergo_native_fit.py`薄入口，复用原checkpoint loader、数据对齐、
  full feature digest及model_inputs；所有旧pinned文件不改。schema为`ekg.ergo_native_fit.v1`。

## 软件与资源门

本地TDD、全仓pytest/ruff/smoke后，原机隐藏CUDA补跑新增11项CPU测试；不得因本地
Torch skip便冒充该门已过。通过后另冻正式配置、源/输入/预算与CPU证据pins，再成功
核卡1空卡才执行。无需重做旧完整模型smoke，原模型/最大train的真实CUDA与R107选中
权重重载已闭合；新增路径为同一模型在原train前向，CPU测试专查标签隔离和计数。

工期用R103最大dev两次forward均时乘2622（最大dev图比最大train候选更多），再乘1.5，
加模型加载/原数据及权重identity读盘共1200秒余量，向上取3600秒内部总预算。外部
3660秒后TERM、60秒清理后KILL。只是fixture proxy，不是所有文档工期或显存保证。
OOM/非有限/身份或人口不一致/超预算保留失败，不删doc/裁候选或自动重试。

主机`gpu-4090`，cwd `/data/TJK/ekg`，物理卡1、UUID
`GPU-45597c42-fba9-d40a-dccb-0c423b160150`。正式配置在真实CPU门后冻结，启动前补
精确命令/配置SHA；当前本文不冒称GPU已经执行。checkpoint只在原主机加载，不传回。

预期输出`runs/stages/R1/r1-v109-ergo-train-fit-20261025/`下config/status/classes/counts/
report；status原子更新，每100doc报进度；最终保留全部2622doc分类与逐doc混淆以便
CPU独立计数核算。开始/结束均核源、输入及checkpoint/config SHA；无final-valid访问。

## 预先解释边界

训练fit与dev均使用同native三类定义，数据人口分开报告，无可相减的泛化置信保证。
训练fit高而dev低时支持优先研究泛化/部署可用信号；训练fit也低时先查优化/表示；两种
结果都不能唯一识别原因，或自动准入某个语义模块。原训练日志binary指标不可跨口径
对比。诊断不为任何新机制提供创新、power、核心消融/负控或确认seed准入。

## 正式执行身份（真实CPU门之后冻结）

原机隐藏CUDA的11项CPU测试全部通过、零skip，真实dev混淆对照官方结果亦通过；详证据
见R1 §25.130。正式配置`configs/ergo_native_train_fit_20261025.json`，SHA
`851ee47723d1be6fa8634eaa7692f0f0d4b2135740b546488260c16e77f888e9`。
CPU证明/预算单独封存于`runs/stages/R1/r1-v109-ergo-fit-admission-20261025/`，seal
`025b7f6990ace490d5274bc841fea5fd60d7806f6020554ef6f6f12bc3048e67`。

主机`gpu-4090`，cwd `/data/TJK/ekg`，实际启动前再核卡1及UUID，命令为：

```bash
setsid nohup env CUDA_VISIBLE_DEVICES=1 PYTHONPATH=src:scripts OMP_NUM_THREADS=12 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 timeout --signal=TERM --kill-after=60s 3660s .venv/bin/python -u scripts/diagnose_ergo_native_fit.py --config configs/ergo_native_train_fit_20261025.json > logs/ergo-native-train-fit-20261025.log 2>&1 < /dev/null &
```

单条SSH只发一个后台任务，parent保存PID并wait其真实退出码。SSH失败只记UNKNOWN，
用成功ps/实际报告判活，不重启。预测结束后以冻结targets和落盘classes/逐doc矩阵做
CPU独立重计数，再过源、人口与checkpoint身份门，结果才可用于研究裁决。
