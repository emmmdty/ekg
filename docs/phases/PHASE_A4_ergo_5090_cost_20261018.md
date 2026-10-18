# ERGO 5090原完整输入成本提案（2026-10-18，待作者许可）

主表C41-A-R；科研价值/可行性与资源证据见R1 §25.105。用于表4-3公开强rival的
FR-016(b)透明适配预算，不是新方法或baseline训练准入。现有C5许可不覆盖此任务；
AGENTS规定“5090须逐次问用户”。本合同/配置是可审查提案，未获新A4许可不得执行。
配置的`cuda_admitted=true`只表达通过CPU后的技术成本范围，不表示作者已经授权。

固定配置`configs/ergo_native_5090_cost_20261018.json`（v4），原完整4096 float32输入/
Longformer/RGT/focal/HF4.11.3 AdamW类体不变；无PAD裁切、AMP、TF32、activation
checkpointing、降候选或重写原图层。R194失败保持，不能采用其较快耗时。

仅三个事前固定train病例typical/worst/longest，每例固定seed13、两次lr0 cold/warm API，
总六次；同一个seed用于不同成本输入，不是多seed实验。全参数数值不变、零符号字节
变化分开报告，target独立性/完整梯度有限性照旧。无epoch、非零lr、dev/final-valid、
性能评分或模型保存。完整baseline训练仍需其预算、协议、正式合同与另行资源许可。

目标cwd `/mnt/aidata/tongjiakai/ekg`，host `server-System-Product-Name`，卡0/RTX5090。
v4单独核该root/hostname/卡号与固定UUID；不伪装4090、不修改旧共享成本helper。
每例启动前必须无compute-app且显存<512MiB，型号/UUID不符即失败，不等待或重试。
只在作者明确许可后重新核空卡，原机实际CPU相关tests通过再运行。

准备资产已在本地暂存`/tmp/ekg-r197-5090-proposal/inputs.tar.gz`，仅11件已封存输入/
证据文件，包含原R192完整train features/targets、原optimizer来源和成本封存身份；没有
本项目训好checkpoint。upstream ERGO原Git bundle与本项目Git增量独立传输并双端核SHA；
代码只走Git。部署前核远端tracked干净及祖先关系，保全untracked `mk_probe_contract.py`。
不得覆盖已有输入：若同路径存在先核同SHA，否则停止。

官方公开Longformer权重须在5090从`hf-mirror.com/allenai/longformer-base-4096/resolve/`
的冻结revision `301e6a42cb0d9976a6d6a26a079fef81c18aa895`直接下载五文件；写`.part`，
按配置逐件SHA核对后原子rename到`/mnt/aidata/tongjiakai/models/local/longformer-base-4096/`
该revision目录，file-set必须准确。不是跨机搬运本项目checkpoint。镜像失败则停止，
不自动转scp已有权重。数据/代码/公共预训练下载不计GPU计算墙钟，均在许可后执行。

许可后仅发一条后台任务，确切命令（cwd如上）：

```bash
setsid nohup timeout --signal=TERM --kill-after=30s 1200s bash -c '
set -e
for case in cuda_typical cuda_worst cuda_longest; do
  CUDA_VISIBLE_DEVICES=0 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
    .venv/bin/python -u scripts/profile_ergo_native_cost.py \
    --config configs/ergo_native_5090_cost_20261018.json --case "$case"
done
' > logs/ergo-5090-cost-r197-20261018.log 2>&1 < /dev/null &
```

整个GPU suite串行三例，总墙钟到1200秒发TERM，最多另30秒清理后KILL；任一失败即停止
后续病例，不缩输入、放宽数值门或换优化器重试。timeout/PID仅是进程监测，不建等卡器。
预期`runs/stages/R1/r1-v97-ergo-5090-cost-20261018/{cuda_typical,cuda_worst,cuda_longest}/`
各report/status；log如上；若OOM/超时则保留stdout/已有报告与新的失败完成审计。
不覆盖原status/产物，SSH失败只记UNKNOWN，成功核GONE后才落完成审计。

报告实际CUDA峰值与冷/热API耗时；三fixture不能保证全epoch耗时，最大train候选也不
自动证明internal-dev更大候选已测。完成后另裁完整预算/训练与评测容量；无科学主表
成绩，不以工程PASS声称KR3.1或创新性达成。等待许可时继续既有无标签internal-dev准备。
