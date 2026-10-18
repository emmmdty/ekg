# ERGO PAD-only变长等价性与CPU形状预算（2026-10-18）

主表C41-A-R接续R1 §25.99；原R193、v1配置与`b4e0e16`源码均封存，不覆盖。
本合同替代当前成本入口，旧R193重放必须用其冻结commit。无baseline epoch/新方法训练。

**科研价值**：继续已选公开强rival表4-3/FR-016(b)的可运行性，保留完整任务而非弱化对手。
**可行性**：R193已跑通原完整模型，GPU被占；官方Longformer支持变长与window自动padding。
当前仅尝试移除显式已mask的尾部PAD；所有真实词、marker、全部有向候选/目标不变。
不改原encoder/RGT/focal/旧AdamW，不改变max context，不追加标注或外部数据。

## 预先冻结的实现与检查

- 配置`configs/ergo_native_padding_cost_20261018.json`，schema v2；输出R194独占namespace。
  使用同一个`profile_ergo_native_cost.py`新版本，全部原source/权重/R192特征身份继续钉定。
- CPU12threads/seed13/float32/batch1；当前只启动short病例。typical/worst/longest病例
  事前固定，用于短文门过后预算，不能按结果换ID。无CUDA准入/自动等卡/5090任务。
- 验证attention mask必须是连续nonpad前缀，尾部input_ids只能为PAD=1、global mask必须零。
  只切三个序列数组的尾部，其他全部字段保持；所有事件位置仍必须指向真实起始marker。
- 由原Longformer库自行补齐512window；不重写attention、不采样graph、不删词或候选。
- **同一个完整初始化模型、同线程**先在eval模式比较full4096与trimmed输入：logits、
  focal loss及全部非空参数梯度逐项`atol=1e-6, rtol=1e-4`；梯度集合/有限性必须一致。
  复用已验证`compare_gradients`，失败即停，不事后放宽容差。
- eval关闭dropout的parity**不证明train随机流相同**；变长会改变RNG消耗，这是透明适配
  的执行差异，不能声称原数字忠实复现(a)。未来若训练，训练/推理必须成对同padding policy。
- 通过后清除parity梯度/参考缓存，再做train-mode两次原AdamW lr0 cold/warm API；
  target独立性、数值不变/零符号字节变化、源码/权重前后hash及无epoch规则沿用R193。
- CPU线程和padding两处同时变化，因此不把与R193的耗时差全归因给PAD；此次验收是
  当前执行配置的实测成本，不是效率因果效应实验。GPU/epoch/效果仍需实际合同与证据。

CPU原机cwd `/data/TJK/ekg`，门通过/push后用独占`setsid nohup`启动一个短文任务：

```bash
CUDA_VISIBLE_DEVICES=-1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  .venv/bin/python -u scripts/profile_ergo_native_cost.py \
  --config configs/ergo_native_padding_cost_20261018.json --case cpu_short
```

预期`runs/stages/R1/r1-v94-ergo-padding-cost-20261018/cpu_short/` report/status，独占logs。
任一parity/数值/来源/完整性门失败，只给该配置失败与具体证据，保留原R193，不伪装原方法
无效。任何后续完整CPU或GPU执行要先写实际预算与正式合同；不把CPU短文PASS当全任务PASS。
