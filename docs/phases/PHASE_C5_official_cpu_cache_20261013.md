# C-41：官方 joint 强锚的远端 CPU score cache

本合同只导出既有冻结 checkpoint 的分数并验证 parity，不训练新方法、不复跑旧 C5 家族。
不改 5090 decoder 诊断的合同或空卡条件。当前任务仍为 C-41 C5 切片。

## 科研价值与可行性

价值：对准表 5-3 的 strongest official-joint anchor，用真实逐对 antecedent 分数与 dummy
支持后续噪声兼容性、因果控制与功效审查；硬 clusters 不能恢复被抛弃的分数。
证据入口为 R1 §3 的强锚、A3 r10 immutable baseline metadata 和 R1 §25.39 的信号审查。
模型复现不算方法贡献，不能用新 decoder 或新标签规则改善 parity。

可行性：4090 上原地 checkpoint、官方适配源码与原始 test-shape input 均可读，机器有 CPU 余量。
原官方 `to_cuda` 明确在 CUDA 不可见时保留 CPU；原模型在 CPU 上的完整行为尚待 smoke。
强制 `CUDA_VISIBLE_DEVICES=-1`，Torch CPU-only、最多 4 threads，不占任何 GPU，不搬任何权重。
CPU/GPU 数值差异可能改变 argmax，必须逐文档验证，不设宽松 metric 容差绕过。

## 冻结干预与输出

- 直接使用原 baseline workspace 的 tokenizer、dataset、encoder、coref scorer 与 cluster utility；
  不重写公开网络或连链算法，不修改该 workspace 的源码与输入。
- 使用固定 seed 13、原 max_length=256 / batch_size=8 / shuffle=false，`model.eval + no_grad`。
  只运行同一 checkpoint 的 encoder/coref scorer，跳过与共指无关的三个关系头；不产生关系指标。
- 只读无 cluster labels 的原 `test.jsonl`：P1 internal-dev，不访问 final-valid。
  保存完整 event-only antecedent 候选及 dummy、原始 pair logits和概率；不按 type 删候选。
- smoke 为原顺序第一批，full 为全部 frozen manifest。full 依赖同 config SHA 的 smoke complete
  与产物 hashes；每份输出使用新 namespace，不覆盖旧输出。
- 每个文档的 non-singleton clusters 必须与 frozen official prediction 完全一致，mention coverage
  必须一致。若失败停止，不调 threshold、order、checkpoint 或 dtype 来追求 parity。
- 成功只说明此 cache 可作为复现控制，不能叫同协议新方法胜出或论文创新。

原机 cwd `/data/TJK/ekg`。唯一参数/hash 清单将在执行前固定到
`configs/c5_official_cpu_cache_20261013.json`；源码、checkpoint、预训练内容与 prediction SHA
均从旧 metadata 核实后绑定，不猜路径。
新根 `runs/stages/R1/r1-v63-c5-20261013/official_joint_cpu/{smoke,full}/`。
预期 cache、原 decoder prediction、metadata、status；完整原始 checkpoint 保留 4090。

本合同不授权 proposed coreference training、额外 seeds、5090 新任务、checkpoint 跨机搬运或新指标。
