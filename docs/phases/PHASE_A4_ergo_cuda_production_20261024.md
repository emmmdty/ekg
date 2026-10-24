# ERGO原函数CUDA生产与驻留最大dev容量（2026-10-24）

C41-A-R/表4-3/FR-016(b)。R102完整4090三病例成本已闭合；本合同补实际原训练函数/
native collate及驻留容量，不能直接放行20epoch。科研价值/可行性见R1 §25.126。

配置`configs/ergo_native_cuda_preflight_20261024.json`，原v2入口，server gpu-4090、
cwd `/data/TJK/ekg`，GPU1/`GPU-45597c42-fba9-d40a-dccb-0c423b160150`。原CPU配置及
旧R199结果保持；R102三报告/config与输入SHA钉入新配置，不改原模型/类体/损失/图。

固定两个train病例：worst 11772 pairs、longest 10302 pairs；原`train_epoch`各一batch、
总两次lr0调用。原HF AdamW、clip1及调度保持，完整4096 float32/seed13/全部候选，
不启AMP/TF32/额外重计算/PAD裁切。原zero-lr数值身份与signed-zero报告保持。

模型和真实optimizer state保留驻留，再对最大无标签internal-dev（11990 pairs，1411
nonpad）完整forward两次，target分别全0/全1，要求logits逐值一致/有限。dev仅从R196
无标签特征读取，不读gold/评分，不保存预测或checkpoint。两次train批次不算完整epoch。

启动前核全部pins、真实CPU相关单测、输出新命名空间、实际GPU空闲（无compute-app、
显存<512MiB）。单任务1200秒TERM、30秒清理后KILL，失败保留原状态/log、无自动重试。

确切命令（cwd如上）：

```bash
setsid nohup timeout --signal=TERM --kill-after=30s 1200s env \
  CUDA_VISIBLE_DEVICES=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  .venv/bin/python -u scripts/preflight_ergo_native.py \
  --config configs/ergo_native_cuda_preflight_20261024.json \
  > logs/ergo-cuda-production-r103-20261024.log 2>&1 < /dev/null &
```

预期`runs/stages/R1/r1-v103-ergo-cuda-production-20261024/`内status、production_report、
capacity_report，以及上述log/PID记录。通过后依据实际两最大原生批次总耗时、驻留容量、
训练/评测完整人口和IO估计完整20epoch预算，另冻正式单seed训练合同/配置；不得只翻旧
admission flag。OOM/非有限值/target依赖或身份漂移即失败，不缩输入/放宽条件救过线。
