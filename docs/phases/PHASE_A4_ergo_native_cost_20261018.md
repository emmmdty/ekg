# ERGO原模型/native完整候选成本合同（2026-10-18）

执行依据：EXPERIMENT_PLAN §4 C41-A-R，输入/来源出口R1 §25.97。
本合同是外部强rival的工程可行性门，不是新方法准入、效果实验或已发表数字复现。

**科研价值**：让表4-3/FR-016(b)强对照使用真实原encoder/RGT/focal和完整有向候选，
判断其能否正确接线及真实训练成本；tiny图层、文件存在或attention mask不能替代此门。
**可行性**：原4090持久官方源码、官方Longformer权重和cache-matched全部train特征
均已固定；短文CPU病例在该机运行，CPU内存足够，GPU当前有他人任务，不自动等卡启动。

## 固定身份与范围

- 配置：`configs/ergo_native_cost_20261018.json`，schema `ekg.ergo_native_cost.v1`。
- 源码：作者ERGO revision `afa3d347ec360242c01d15a34b1f1ae63714c789`，从原Git
  checkout保全至原机`runs/external/ERGO/`；完整原模型类导入，不改encoder/RGT/focal类体。
- 依赖：使用原HF4.11.3 `AdamW`类体，固定原官方源文件hash，所需名字绑定当前Torch/
  typing与真实版本检查函数，不执行其余模块、不安装旧栈、不以torch.optim.AdamW替代。
- 权重：官方Longformer immutable revision，原机镜像直下，具体路径/字节/SHA见R1
  §25.96及R192 model_acquisition；不跨机搬运，不写回权重。新增两个marker embedding
  显式`mean_resizing=False`，保持旧版独立初始化策略；本栈仍非原论文旧Torch/Transformers。
- 输入：R192 `native_train_cache_global`；全文/全部事件提及/全部ordered pairs、原4096
  padding、真实BOS/EOS global，目标独立侧车；三个类索引为NONE/PRECONDITION/CAUSE。
  不使用gold coref/type作为模型文本或推理输入；gold只做原生Cartesian训练监督。
- 原源码超参：4heads、attention dropout0.1、embedding dropout0.3、focal alpha0.75/
  gamma2；batch1、float32、seed13、CPU4threads。无采样/截断/AMP/checkpointing替换。
- 每个病例恰两次旧AdamW cold/warm调用，**lr=0、无epoch**，原分组weight_decay0.01/
  bias及LayerNorm零decay、epsilon1e-8、clip norm1。optimizer状态会变化，不能写零API。

## 病例与准入

固定病例ID、原生候选数和nonpad长度只见配置/结果页；选择规则是最少事件短文、
最接近输入中位数、事件数最大且最长的文档、全文最长文档，事前固定而非按结果选。

1. **当前仅CPU短文**：真实模型eval两次，改变target必须不改变logits；再以train mode
   做两次前向/反向/clip/lr0旧AdamW，检查loss/logits/所有非空梯度有限、参数数值不变。
2. 字节与数值分别报告：只允许零符号位改变字节，必须由逐参数数值规范化摘要证明
   所有其他值不变；不修改或恢复原模型参数，不掩盖真实更新，源文件/权重末尾再核hash。
3. 完整记录参数数、无梯度参数名、optimizer状态字节、CPU峰RSS、两次耗时；checksum
   开销在计时外，梯度有限性检查在计时内。pooler如未参与任务须说明，不能强称全参数更新。
4. 检查完整载入日志：预期新增marker/任务头及未用pooler独立初始化要披露；任何未解释
   的encoder缺失/形状问题不得放行后续成本/训练。GPU当前`cuda_admitted=false`，代码拒绝。
5. CPU通过后先回填结果与主表，再以新准入身份核空4090、披露exact command/cwd/
   output、测固定GPU病例。不得把CPU RSS/耗时换算成CUDA峰值或epoch PASS。

CPU命令（远端cwd `/data/TJK/ekg`，完整门/源码同步后执行）：

```bash
CUDA_VISIBLE_DEVICES=-1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  .venv/bin/python -u scripts/profile_ergo_native_cost.py \
  --config configs/ergo_native_cost_20261018.json --case cpu_short
```

生产启动用单个`setsid nohup`任务、独占日志/输出；无自动等卡/重试器。产物位于
`runs/stages/R1/r1-v93-ergo-cost-20261018/cpu_short/`的report/status，stdout入独占logs。
已有输出即拒绝；错误/失败/旧身份保留，SSH失败记UNKNOWN，只有成功查询进程缺席才GONE。

## 阶段出口

CPU PASS只表示该fixture正确接入；CUDA/全train预算、baseline训练、native效果、
FR-016完成状态及新方法创新均未验证。OOM或非有限值先记录具体【算力/代码】证据，
不能删候选、换更大encoder、悄改原类或事后重选fixture来补洞。科学KR仍未完成。
