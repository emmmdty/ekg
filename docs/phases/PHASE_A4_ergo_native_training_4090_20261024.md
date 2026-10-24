# ERGO native primary-4090执行合同（2026-10-24）

本合同只把[原科学/选模合同](PHASE_A4_ergo_native_training_20261018.md)从草案推进为
有证据的正式执行身份；不修改其科学参数、原源码或旧提案。C41-A-R/表4-3/FR-016(b)。
科研价值/可行性、真实成本/生产/容量和工期预算见R1 §25.125–§25.127。

正式配置：`configs/ergo_native_training_4090_20261024.json`，SHA
`5743397bd4f4f1d452a6e6ec9d692dba5c590ce1d58c27859681185806ee5f41`。
原Longformer/RGT/focal/legacy AdamW/train_epoch、4096/float32/全候选，seed13/20epochs/
每epoch完整internal-dev三类官方F1/严格大于及最早tie保持。R102三例、R103实际CUDA
production及驻留最大dev、R104预算/对照计划逐件钉进pins。启动时联核实际全部features/
MID/候选digest；不因预算而改epoch或事后早停。不扩seed、阈值、backbone或final-valid。

## 精确执行

主机`gpu-4090`，cwd `/data/TJK/ekg`，物理卡1，UUID
`GPU-45597c42-fba9-d40a-dccb-0c423b160150`，启动前成功SSH核无compute-app/低显存。
单条SSH只发一个后台任务，实际启动命令：

```bash
mkdir -p logs
setsid nohup env CUDA_VISIBLE_DEVICES=1 PYTHONPATH=src:scripts OMP_NUM_THREADS=12 TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 timeout --signal=TERM --kill-after=60s 173400s .venv/bin/python -u scripts/train_ergo_native.py --config configs/ergo_native_training_4090_20261024.json > logs/ergo-native-4090-20261024.log 2>&1 < /dev/null &
job_pid=$!
printf 'ERGO_TRAIN_WRAPPER_PID=%s\n' "$job_pid"
wait "$job_pid"
job_rc=$?
printf 'ERGO_TRAIN_EXIT=%s\n' "$job_rc"
exit "$job_rc"
```

预期：`runs/stages/A4/a4-ergo-native-20261024/seed-13/`下config/status、每epoch完整
predictions/classes、原子写入best.pt、完整20epoch report；日志见命令路径。内部预算
和外部启动/清理余量由R104固定。OOM/非有限值/超预算直接保留失败，不重试、不删doc或
改精度；SSH失败只记UNKNOWN，成功ps才可判GONE。checkpoint留4090，不跨机搬。

完成后在主机独立重载best.pt，先核完整classes逐值相同，再用冻结官方evaluator核causal；
执行前另披露验证命令。依R104预先固定的三对照进行配对doc分析及方向/subtype/FN/FP
交换，不能看完结果再换弱锚。选dev分数和区间是单seed探索性证据，不是确认。

ERGO是公开强rival的透明native适配；论文原基准数字尚未复现，仍FR-016(b)。
不同backbone/输入不能归因RGT；不以已知方法分数完成三个创新贡献。其他family为不适用，
占位不算护栏。后续科研路线以真实残余和最近邻证据回R1，旧失败家族不恢复。
