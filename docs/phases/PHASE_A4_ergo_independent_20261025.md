# ERGO完成后的独立重载合同（2026-10-25）

科研价值/可行性见R1 §25.129。复用原R104/R106科学/选模/比较规则，不启动新训练、
seed或最终留出评测；旧训练报告/预测/checkpoint不修改。主机gpu-4090，cwd `/data/TJK/ekg`。
成功ps核三原worker GONE、卡空后，在各原物理卡独立运行，确切核心命令如下：

```bash
CUDA_VISIBLE_DEVICES=1 PYTHONPATH=src:scripts OMP_NUM_THREADS=12 TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 timeout --signal=TERM --kill-after=60s 1800s .venv/bin/python -u scripts/verify_ergo_native_checkpoint.py --config configs/ergo_native_training_4090_20261024.json --report runs/stages/A4/a4-ergo-native-20261024/seed-13/report.json --output runs/stages/R1/r1-v107-ergo-independent-20261025/full --device cuda
```

```bash
CUDA_VISIBLE_DEVICES=0 PYTHONPATH=src:scripts OMP_NUM_THREADS=12 TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 timeout --signal=TERM --kill-after=60s 1800s .venv/bin/python -u scripts/run_ergo_native_control.py --operation verify --config configs/ergo_control_complete_graph_training_20261024.json --report runs/stages/A4/a4-ergo-control-complete-graph-20261024/seed-13/report.json --output runs/stages/R1/r1-v107-ergo-independent-20261025/complete_graph --device cuda
```

```bash
CUDA_VISIBLE_DEVICES=2 PYTHONPATH=src:scripts OMP_NUM_THREADS=12 TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 timeout --signal=TERM --kill-after=60s 1800s .venv/bin/python -u scripts/run_ergo_native_control.py --operation verify --config configs/ergo_control_gamma0_training_20261024.json --report runs/stages/A4/a4-ergo-control-gamma0-20261024/seed-13/report.json --output runs/stages/R1/r1-v107-ergo-independent-20261025/gamma0 --device cuda
```

实际每条独立SSH用setsid nohup，日志分别`logs/ergo-{full,complete_graph,gamma0}-verify-20261025.log`，
SSH parent等待实际退出码；连接失败只记UNKNOWN，不重起。输出各report/classes/predictions，
两个control另有旁侧`*-execution`派生入口与control身份。拒绝任何类序/人数/候选/源/hash/
分数不一致，无覆盖修复原产物。checkpoint只在4090重载，不回本地。

三项通过后实例化R106预定full/controls预测身份（来自完整报告的选中epoch和独立parity），
复用原比较入口作同doc pooled causal F1/10000bootstrap/rng13和方向/subtype/FN/FP
交换。external joint/A3/Taco仍认原冻结SHA；其他family占位不算护栏。单seed选中dev
区间不含训练随机性，不触发额外seed或方法贡献验收。代码未变，不重做旧GPU训练/准备。
