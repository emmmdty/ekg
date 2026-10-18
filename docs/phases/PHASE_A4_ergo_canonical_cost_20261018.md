# ERGO原完整padding的CPU形状成本合同（2026-10-18）

主表C41-A-R；科研价值/可行性与恢复原路线决定见R1 §25.102。R194 PAD-only最大候选
未过事前梯度门，该版本停止，不放宽容差、不覆盖失败、不拿通过病例替代全输入可行性。

R195恢复R193已跑通的原完整4096输入，原R192 cache-global特征三个序列数组**原样传递**，
不裁padding/真实词/marker/候选，不改encoder/RGT/focal/原HF4.11.3 AdamW类体。
CPU由R193四线程改为12线程是执行资源变化；它不能把R194改判PASS，也不是方法创新。

固定配置：`configs/ergo_native_canonical_cost_20261018.json`，schema v3，
`padding_policy=retain_all_4096`、`padding_parity_required=false`，仅这对匹配值有效。
入口保留v2以便诊断追溯，但**本活动合同只运行v3**；原v2结果重放仍须其冻结commit。
v3不需要也不声称PAD优化parity，报告`applied=false`；完整参数有限性、target独立性、
两个lr0 cold/warm API/数值参数不变与signed-zero字节单列、源码/权重前后hash规则沿用R193。

病例仍是预先固定的typical/worst/longest，具体ID/候选与token数见配置/结果页。
每项CPU12threads、float32、seed13、batch1，两次lr0、无epoch/held-out/效果或模型保存。
可依原机实际余量并行三项（CPU36threads、独占输出），每条SSH只起一个后台任务。
先本地三件套、原机真实相关tests、push，再执行；同主机CPU/RAM不够则降低并发，
不改数据或失败门、不挤GPU。CUDA未准入，不自动等卡、不使用5090或跨机搬运权重。

原机cwd `/data/TJK/ekg`，分别以`setsid nohup`、独占logs启动：

```bash
CUDA_VISIBLE_DEVICES=-1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  .venv/bin/python -u scripts/profile_ergo_native_cost.py \
  --config configs/ergo_native_canonical_cost_20261018.json --case cpu_typical
# 其余独立任务分别 --case cpu_worst / --case cpu_longest
```

预期`runs/stages/R1/r1-v95-ergo-canonical-cost-20261018/{case}/` report/status。
输出已存在即失败，不覆盖旧artifact。CPU峰RSS/forward-backward/原optimizer耗时如实记录，
并发导致的带宽/线程竞争需披露。结果仅支持原执行版的形状可行性与预算估算；不得从
三fixture承诺精确epoch耗时或CUDA峰值。完整CPU或GPU训练须另冻结预算/选模/manifest/
官方评测与保真度合同；未到该门不启动epoch，不把已知baseline当本项目创新。
