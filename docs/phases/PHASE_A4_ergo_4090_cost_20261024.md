# ERGO原完整输入4090成本合同（2026-10-24）

C41-A-R/表4-3/FR-016(b)；执行前科研价值/可行性见R1 §25.125。作者明确恢复4090后续
任务，沿用主机空卡权限；不是5090迁移执行，不改原5090配置/结果，不授权新方法训练。

## 固定身份与预算

- 配置`configs/ergo_native_4090_cost_20261024.json`，原v3主机路径；固定原R192完整
  train feature/target、原ERGO类体、完整4096 float32及BOS/EOS globals、全部候选。
- 三病例与旧CPU/5090提案一致：cuda_typical在卡1、cuda_worst在卡2、cuda_longest在卡0。
  原机`4090-1`，cwd `/data/TJK/ekg`；UUID分别钉启动快照并在结果核验。卡3保留。
- 每例seed13、原legacy AdamW两次lr0 cold/warm API；原target独立性、完整有限梯度、
  范数有限、数值参数不变及signed-zero字节变化报告保持。最多六次，失败前实数如实计。
- 不启AMP/TF32/重计算、裁PAD/候选、负采样、换backbone或改图/损失/容差；无epoch、
  性能评分、dev/final-valid访问或模型保存。
- 单例1200秒TERM、另30秒KILL；三卡独立并行，不因兄弟失败自动重试或覆盖产物。
  当前CPU/输入证据已有，不重新跑原全模型CPU准备。成本通过不等于完整预算/训练准入。

## 启动前

本地三件套、原机相关CPU单测、全部config pins/预训练file-set、tracked clean与Git祖先
关系均核后再执行。remote-only cache/venv/build/logs保留，不清理。代码通过Git；每条SSH
仅启动一个后台任务。实际启动前每张卡无compute-app且显存<512MiB，否则该例停止。

三条确切命令的cwd均为`/data/TJK/ekg`，分别执行：

```bash
setsid nohup timeout --signal=TERM --kill-after=30s 1200s env \
  CUDA_VISIBLE_DEVICES=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  .venv/bin/python -u scripts/profile_ergo_native_cost.py \
  --config configs/ergo_native_4090_cost_20261024.json --case cuda_typical \
  > logs/ergo-4090-r102-cuda_typical-20261024.log 2>&1 < /dev/null &

setsid nohup timeout --signal=TERM --kill-after=30s 1200s env \
  CUDA_VISIBLE_DEVICES=2 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  .venv/bin/python -u scripts/profile_ergo_native_cost.py \
  --config configs/ergo_native_4090_cost_20261024.json --case cuda_worst \
  > logs/ergo-4090-r102-cuda_worst-20261024.log 2>&1 < /dev/null &

setsid nohup timeout --signal=TERM --kill-after=30s 1200s env \
  CUDA_VISIBLE_DEVICES=0 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  .venv/bin/python -u scripts/profile_ergo_native_cost.py \
  --config configs/ergo_native_4090_cost_20261024.json --case cuda_longest \
  > logs/ergo-4090-r102-cuda_longest-20261024.log 2>&1 < /dev/null &
```

预期各自`runs/stages/R1/r1-v102-ergo-4090-cost-20261024/<case>/report.json`、
`status.json`及上述log。另记PID/启动卡快照，成功SSH核GONE后再作终止审计；OOM或
异常保留原running status/log，以单独完成审计记录失败，不改旧输出掩盖失败。

## 完成后裁决

核实际GPU/UUID、峰值与cold/warm耗时、API数、数值参数不变及全部输入SHA；同时核
失败进程及原输出。三fixture不能自动外推全epoch，也不涵盖更大的internal-dev候选。
全部成本通过后接既有真实CUDA容量/原trainer production门和完整预算，再另冻正式
训练配置；不只翻admission flag。若当前原执行版不可行，点明实现/算力证据，先改主表
再选合法工程执行版或下一公开强rival；不把资源失败说成ERGO科学效果FAIL。
