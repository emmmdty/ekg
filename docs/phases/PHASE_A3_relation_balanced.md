# PHASE A3 — 关系族×位置自适应的事件关系抽取

> **ACTIVE。** 位置工作点沿用启动时冻结的 P1 r12 / A3 r13 plan；prototype 新代码使用 P1 r13。
> A3.0 baseline、A3.1 复现底座和
> A3.2 第一核心周期均已完成；当前只执行第二核心周期。历史数字见
> [`../results/PHASE_A.md`](../results/PHASE_A.md)。

## Goal

在冻结的 MAVEN-ERE gold-mention 协议上验证：为 causal/subevent/temporal 的同句与跨句候选分别学习
训练侧 NONE-logit 工作点，能否改变模型的原始 argmax 边界，并在不牺牲 subevent/temporal 的前提下
稳定超过 causal 主锚。

该周期是对第一周期“逐族一个工作点”的单变量扩展。若仍失败，不进行第三轮工作点调参；下一方法方向
改为文献支持的 retriever→cross-encoder，工作点线结束。

## Inputs

| 输入 | 冻结身份 |
|---|---|
| P1 trust root（位置工作点） | `runs/stages/P1/p1-v6-20260831-r12/` |
| P1 protocol SHA-256（位置工作点） | `0bd33e87e67c1e4b36afb335270cbd511377c412d16e87b835a3503f0aa58497` |
| P1 trust root（prototype） | `runs/stages/P1/p1-v6-20260901-r13/`，`00e0943d…b3447a` |
| A3 preflight | `runs/stages/A3/a3-v6-position-workpoint-r13/preflight/` |
| A3 plan SHA-256 | `b587b21d7aa74437d7144ecad76d87f4fe2253f39966d48bb23108e914ec1eda` |
| 主锚 | `a3-v6-baselines-r10/primary_anchor.json`，causal 33.17 |
| 护栏 | subevent ≥28.75；temporal ≥50.63 |
| 数据 | train 2,622；internal-dev 291；final-valid 710 封存 |
| backbone | 内容寻址 roberta-base `71be7419…c961ea9` |

禁止改变 manifest、候选全集、official evaluator、训练/推理 TIMEX 对称性或 final-valid 访问规则。
诊断阈值只用于提出机制，不能作为测试期后处理进入方法分数。

## 已完成事实

### Baseline closure

- official single、official joint、local pair 已在同协议闭合；主锚在方法结果前冻结；
- 50 epoch 复现底座 causal 31.42，subevent 30.62，temporal 50.78；
- 第一周期 `both` 三种子 causal 均值 33.27，但 temporal 50.61 低于护栏且仅 1/3 causal 为正；
- 第一周期相对事后逐族校准只有 +.12，低于 seed sd .82，判定未通过。

### 第二周期设计依据

- causal 同句 precision .2904 / recall .5841；跨句 precision .1998 / recall .5223；
- 跨句预测数是 gold 的 2.6×，同句为 2.0×；
- 逐位置诊断上限 causal 33.80 > 33.17，且三族各自位置阈值可同时满足护栏；
- 连接词、句距和跨窗口覆盖已被实测否定为当前主因。

### 实现与本地 gate

- pair row 显式携带 `same_sentence|cross_sentence`；缺少 `sent_id` 时 fail-fast；
- controller 维护 3 family × 2 position 的六个独立 offset；
- 训练按 row 只移动对应 NONE logit，推理不读取 offset、仍为原始 argmax；
- 位置映射、相反控制方向、闭环收敛和 no-op 行为已有测试；
- 447 passed / 16 expected skips、ruff 0、CPU smoke 与 P1 local gate 全绿；提交 `91d32d8` 已推送。

## Tasks

### A3.2-r13.1：2 epoch 行为 smoke

在 `/data/TJK/ekg`、GPU0、seed 13 运行训练器级 2 epoch 行为 smoke。必须保存：

- `family_balance.json` 中六组 offset 与逐 epoch trajectory；
- checkpoint、训练配置与训练器 internal-dev dev curve；
- 完整 argv、commit、P1/plan hash、日志和 return code。

Smoke PASS 条件：

1. 六组均有观测，不缺桶、不串桶；
2. loss、logits、measured shift 和 offset 全部有限；
3. offset 不出现第一周期错误符号造成的指数发散；
4. 关闭机制的已有 control 身份不被覆盖，candidate/doc IDs 与 preflight 一致；
5. final-valid 未访问。

该命令不单独调用 inference/official evaluator。2 epoch 的训练器 dev 分只用于行为检查，
不作为方法结论；正式 seed-13 流水线再产生 predictions 与 official metrics。

**2026-08-31 状态：PASS。** GPU0 seed 13 正常结束，训练器 macro .3178 → .3328；六桶最终
offset 范围 [−.536, +.328]，12 条 trajectory 完整且全部有限，`run_metadata.status=complete`，
`final_valid_accessed=false`。产物见
`runs/stages/A3/a3-v6-position-workpoint-r13/smoke/seed-13/checkpoint/`；日志见
`logs/a3_position_workpoint_r13_smoke_s13.log`。该 PASS 只放行 r13.2，不构成指标提升结论。

### A3.2-r13.2：seed-13 完整训练

只在 smoke PASS 后，以完全相同的输入、机制和 seed 运行 50 epoch。报告每个 epoch 的三族 P/R/F1、
same/cross 分层、六组 offset 和选择 epoch。不得因中途分数调整 damping、loss、候选或 epoch 预算。

单种子方案保留必须同时满足：

- seed-13 causal > 33.17；
- subevent ≥28.75，temporal ≥50.63；
- 对复现底座 causal 的 document-cluster paired-bootstrap 95% CI 下界 >0；
- 提升不只是 test-time 阈值或 candidate population 改变；
- 跨句 precision 的改善方向与设计一致。

**2026-08-31 运行状态：进行中。** GPU0、seed 13 的 50-epoch trainer 已启动，完成后由同一外层
流水线自动调用 official scorer。最后一次成功 SSH 监测到 epoch 15；其后 cpolar 入口在 banner 前
超时，因此当前只能写“远端状态待恢复核验”，不能把 SSH 失败写成任务结束。trainer dev curve 不进入主表。

### A3.2-r13.3：单种子封存与多种子授权门

seed-13 通过后只封存为“单种子过线候选”，**不自动补 seeds 17/42**。只有本轮所有待比
方案的单种子均超过各自 baseline 和护栏，且用户再次明确允许后，才可建立额外 seed run-dir。
在此之前，空闲 4090 只可并行不同方案/任务，不得并行同一方案的不同 seeds。

只有代码/配置/threshold identity 全部冻结后，才在 sealed batch 中评 final-valid；final-valid 不反馈到
模型、epoch、offset 或结构选择。基础设施失败只有在没有返回指标且 hashes 完全一致时才能原样重试。

### A3.3：若位置工作点失败

不再增加第三个工作点或扫连续阈值。保留 r13 负结果，转做新的核心方法候选：

1. bi-encoder/S-BERT 高召回检索相关事件对；
2. cross-encoder 只在检索候选和 hard negatives 上精分类；
3. 用 recall@k、候选压缩率和 official relation F1 同时验收。

该路线必须另建协议与核心周期，不能事后并入 r13 冒充同一机制。

**并行 exploratory 诊断（不构成 A3.3 正式启动）：** 在用户允许不同方案 GPU 并行后，已用同一个
seed 13 依次测试 trigger-mean sampled BCE、marker-sentence、top-k hard-negative ranking 三个
Stage-1 竖片；三者均未达到事先冻结的 overall≥.90 / cross≥.85 召回门，故均未接 Stage 2，且不再
增加第四个近似变体。具体数字与 artifact 见 `../results/PHASE_A.md`；r3 hash 待 SSH 恢复补齐。

### A3.4：ProtoEM-inspired 原型匹配探索（2026-09-01，单种子 FAIL，已封存）

4090 不可达期间，作者逐次授权使用 5090 做提高最终指标的方法探索。检索线已止损，不跑 r4；新路线
改动 pair-scoring geometry，而不是继续调阈值、句距或候选近似。

一手依据是 [ProtoEM](https://arxiv.org/html/2309.12892)：它同样使用文档窗口、trigger pooling、
event-pair FNN，再以关系原型匹配和训练集标签依赖建模三族关系。论文公开 valid 值只说明方向，因 split
与本项目不同，**不得直接作为胜出证据**。未找到作者官方代码，因此以下是透明的本地适配，不称复现：

1. `prototype`：冻结 train manifest 每类确定性取 32 个 support，初始化共享 pair projection 后的关系
   原型；输出为实例到各原型的负欧氏距离，仍按每族原始 argmax 推理；
2. `prototype_dependency`：在相同原型头上增加由 train 正关系共现构造的残差传播；NONE 只保留自环，
   因全量审计显示 causal 正类与 subevent-NONE 的稀疏性共现会淹没真实的 causal→temporal 依赖；
3. 两臂唯一差异是 dependency residual；其 neighbor 权重零初始化，故两臂初始 prototype logits 必须
   逐位相同。工作点组件关闭，candidate、TIMEX、evaluator、manifest 和训练预算全部不变。

执行门：先在 5090 跑 torch 单测与每臂 2 epoch CUDA smoke；support 必须全部来自 train，12 类均非空，
loss/logits/prototype/gradient 全部有限，关闭新 head 时旧 linear checkpoint 严格加载。通过后每臂只跑
冻结 seed 13，可在不同空闲 GPU 并行。未经作者新的明确授权，禁止任何额外 seed。

单种子 promotion 仍使用本文件既有门：causal > 33.17、subevent ≥ 28.75、temporal ≥ 50.63，并用
official evaluator。任一臂未过则如实封存；两臂都未过则停止 prototype 线，不扫 support 数、embedding
宽度、距离温度或 dependency 权重。final-valid 不参与 support、选模或判定。

**封存状态**：`cpolar-ssh-update` 已恢复 5090；P1 r13（`00e0943d…b3447a`）远端 validate-only
PASS。两臂 2ep smoke 均数值/覆盖合格，plain prototype 止损；dependency 完成冻结 50ep seed13 和
official internal-dev 评分，只通过两个族的门，causal 未超过主锚，故整案 FAIL。具体数字只见
`../results/PHASE_A.md`。plain full、额外 seeds 和超参扫描均未启动，final-valid 未访问。5090 模型
cache 尚无法闭合正式内容 pin，本轮结果保持 exploratory；失败方案无需在 4090 重跑。

### A3.5：ATLOP adaptive-threshold objective（2026-09-01，预注册）

prototype 失败后的 error profile 将主因锁定为跨句 causal FP，而非方向反转。下一不同机制只采用
ATLOP 官方 `ATLoss`：每族 NONE=index0 是 pair-dependent threshold；正行排序
`gold > NONE > other`，负行排序 `NONE > positive subtypes`。linear head、全候选、三族、训练预算、
原始 argmax 推理均不变；外部 class weight 关闭，且禁止与 prototype/balance 组件混用。

代码 `d4bee5c`；P1 r14 `a2b83f66…0a6974`。先在 5090 完成 Torch/公式负控、CUDA backward、P1
validate-only，再跑 seed13 2ep smoke；行为门与完整 official promotion 门只见
`../results/PHASE_A.md`。本方案不实现 ATLOP localized context pooling，也不运行会增加 FP 的 ATGL；
未经作者新授权禁止额外种子。

## Done when

- r13 smoke 和 seed-13 单种子判定有不可变产物；
- seed-13 过线时封存为候选；失败时明确封存 `failed` handoff 并转两阶段方案；
- 未获得用户新的明确授权时，无任何额外 seed 产物或运行目录；
- `docs/results/PHASE_A.md` 追加本周期真实结果和产物位置；
- 本地 pytest、ruff、`ekg-smoke` 全绿，远端 checkpoint/log 可追溯。

## Stop conditions

- smoke 中任一 offset/logit/loss 非有限、位置桶错映射或明显指数发散：立刻停止；
- seed-13 causal 不超过主锚或任一护栏失败：封存工作点线并转两阶段方案；
- 无论 seed-13 是否过线，未经用户明确允许不得启动 seeds 17/42；
- 两个有效工作点核心周期仍未通过：工作点方法线结束，不开第三轮；
- manifest/evaluator/candidate hash 漂移：停止并回 P1；
- final-valid 用于选模：结果标 exploratory，不得进入最终主表；
- 不用更大 backbone、额外语料或换数据集补洞。

## GPU

4090 项目目录 `/data/TJK/ekg`，服务器只用 `.venv/bin/python`。启动前向作者展示准确命令、cwd 与
预期输出，先用 `nvidia-smi` 选空卡。长任务使用 `setsid nohup` 与独立日志；一条 SSH 只发一个后台任务。
5090 仍需逐次授权；作者已对 2026-09-01 这轮临时探索明确授权。入口不可达时先运行
`cpolar-ssh-update` 再重试；本轮 dependency seed13 已结束，当前不应再启动本方案任务。不跨机搬
checkpoint，除非作者另行决定。
