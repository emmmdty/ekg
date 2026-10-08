# C-37–C-39：三章根因验证就绪合同（2026-10-08）

本合同冻结 **diagnostic-only / seed 13 / non-confirmatory** 控制，不准入新方法。
它不改旧 D4/A4/C5 sealed 身份或结果，不恢复旧家族，不访问 final-valid。
科研选择由执行代理负责；本轮作者要求只做非 GPU 工作。

## 科研价值与可行性

证据与竞争解释见 [`../research/20261008_method_recovery.md`](../research/20261008_method_recovery.md)，
已有实测只认 `results/PHASE_R1.md` §25.34。本轮分别隔离分类头、辅助损失梯度和聚类解码，
辨别强 baseline 欠额的来源；不以诊断指标替代方法章的公开主指标。

D4 数据/CV/训练器/evaluator 已有，复用原 CLS 配方与 pretrained 内容身份；
A4/C5 权重原地留在 5090，数据、输入预测和原输出均可核 hash，无跨机权重搬运。
CPU 微型模型可验证训练/重载/梯度/重放接口；真实 pretrained 的 CUDA 内存和行为必须等空卡 smoke。
新机制的最近邻差异、≥80% power、单变量消融和负控不由此合同替代。

## 三项冻结比较

| 项 | 唯一干预与控制 | 固定项 | 不允许推导的结论 |
|---|---|---|---|
| D4 | `linear` vs `tanh5`：五维 tanh 隐层，再输出五类；非旧 typed-cue 的 factor/cue 机制 | marked sentence、CLS、完整五折 OOF、seed 13、class weight alpha=.5、AdamW lr=2e-5、batch=32、length=128、12 epochs、selection-dev 选模；pretrained 内容 `71be7419…c961ea9` | head 结果不能唯一解释旧机制失败；输入/池化、cue residual 与 factorization 未参与此干预 |
| A4 | 同一 full checkpoint：主 CE / retained CE / hinge 分解；各 family 对组合辅助梯度；encoder 与 heads 分开报告 | train-only 固定样本、旧 supervised_rows/损失函数、训练态 dropout、seed 13、checkpoint 原 weight/max_length；**零 optimizer step** | selected checkpoint 的局部梯度不是历史优化轨迹；负 dot 只说明无穷小 SGD 主损失风险，不证明 Adam 或 F1 原因 |
| C5 | 同一 binary pair probabilities：旧 average-link(.7, band=0) vs 官方 antecedent argmax(dummy p=.5) | 完整 same-type 候选、gold event types、同一预测 arguments、原 scorer mention 顺序；另存文本 antecedent 顺序 | FR-016(b) 透明适配，未复现官方 antecedent 训练；不是官方 baseline 或旧 role 家族的第三周期 |

C5 直接调用固定 `MAVEN-ERE ac81a971…` 的 `coreference/src/utils.py:get_predicted_clusters`，
SHA `5c04f989…a773406`；不重写连链算法。binary p 的 argmax 与 logit(p) 加零 dummy 的 argmax 同序，
但训练目标、候选过滤与官方不同。p=.5 的 tie 按官方 torch argmax 选最早 antecedent，不调 dummy。
原 average-link 必须逐文档复现冻结 full-r2 clusters；否则停止，不能归因到 decoder。

D4 的 seed 控制沿用原实现；不同头初始化会消耗不同随机数，不能把一次差值作确定性因果效应。
五折 pooled macro-F1、每类 F1 和 document-paired bootstrap 都报告，仍只有一个训练 seed。

## 输入与机器绑定

唯一命令/hash 清单：[`../../configs/recovery_validation_20261008.json`](../../configs/recovery_validation_20261008.json)。
它绑定所有项目 src Python 与实际入口，P1 trusted protocol、冻结 manifest、source、evaluator、
每个 checkpoint 的顶层文件、预测 arguments 与旧 prediction。每条命令用服务器 `.venv/bin/python`。

| 机器 | cwd | 就绪任务 |
|---|---|---|
| gpu-4090 | `/data/TJK/ekg` | `d4-linear-smoke`、`d4-tanh5-smoke`，以及两头各 fold 1–5 |
| gpu-5090 | `/mnt/aidata/tongjiakai/ekg` | `a4-gradient-smoke/audit`、`c5-decoder-smoke/audit`；仍须对应 GPU 授权 |

A4 从 train 文档中按 SHA256(doc_id) 排序取前 8 个符合 **至少2个 event、至多32个含TIMEX的 nodes、
至多8句** 的文档；smoke 取同样排序的第1个。这个受限样本不代表全 train 分布，不作统计总体声称。
C5 smoke 取 frozen internal-dev manifest 前2篇，只作接口验证；audit 用完整 internal-dev。
smoke 子集输入在新 namespace `runs/stages/R1/r1-v61-recovery-ready-20261008/preflight/c5-smoke/`。

## 空卡时的入口（本轮不执行）

先同步已 push 的代码，保留所有 remote-only 产物；无 tracked 修改时才按 GPU_RUNBOOK 的 git 路径更新。
不运行 uv，不跨机取权重，不删除旧 runs。数据子集用 scp/rsync 并核双端 SHA。

CPU preflight（不加载模型）：

```bash
.venv/bin/python scripts/launch_recovery_validation.py \
  --plan configs/recovery_validation_20261008.json --job d4-linear-smoke
```

5090 同样入口先分别用 `--job a4-gradient-smoke` 与 `--job c5-decoder-smoke` 检查。
已取得对应机器任务授权且核到空卡后，实际启动格式为：

```bash
mkdir -p logs
setsid nohup .venv/bin/python -u scripts/launch_recovery_validation.py \
  --plan configs/recovery_validation_20261008.json --job a4-gradient-smoke \
  --execute --gpu 0 > logs/recovery-a4-gradient-smoke-20261008.log 2>&1 < /dev/null &
```

这是 5090、cwd `/mnt/aidata/tongjiakai/ekg` 的首条候选命令；输出是新 stage 的
`a4-gradient-smoke/gradients.json` 与 `status.json`。这段展示不构成资源授权。
4090 首条对应 `d4-linear-smoke`，GPU index 用当时核实的空卡，输出 checkpoint/config/head/dev_curve/status。
C5 首条 `c5-decoder-smoke` 输出 pairs cache、两套预测、official metrics、error exchange 与 provenance。
每条 ssh 只启动一个后台任务；不同独立任务可在不同空卡并行，不能增加 seed。

启动器默认只校验并打印完整 argv；`--execute` 才查询 GPU、核 occupancy/CUDA、运行。
formal job 要求本计划 hash 下 smoke status=complete 且 artifact hashes 有效；不是看到 PASS 字样就放行。
输入/hash 漂移、输出已存在、进程/显存占用、无 CUDA、loss 非有限或覆盖不符均 fail-fast。
SSH 失败按三态判活处理，不能直接重开任务。部分失败产物保留，修复另开 namespace/合同身份。

## 汇总与裁决

C5 入口已串联 official scorer 与 paired error exchange；relation 字段是空占位，**只解释 coreference 指标**。
A4 输出 loss、活跃/选中行和各参数组梯度，不生成“模型得分”。若 hinge 不活跃，记录零梯度而非假造冲突。
D4 两头五折都完成后执行计划 `postprocessing.commands` 的 CPU 汇总：先验证所有 run status/hash/身份，
复用既有 document-cluster bootstrap，比 tanh5 vs linear，并核 linear vs 固定 CLS anchor。

代理下一步裁决以这些证伪结果选择实质修复；只有另闭合新机制的文献差异、输入可部署性、
强对照、power/消融/负控门，才可进入方法验证。**本合同不产生方法有效或已提分的结论。**
