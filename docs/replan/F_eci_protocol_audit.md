# DR-F 本地一手审计：ESL/CTB ECI 资格判定

> 审计日期：2026-08-26（Asia/Taipei）
>
> 原始报告：`docs/replan/F_eci_protocol.md`
>
> 来源导出：`docs/replan/F_eci_protocol.pdf`

## 结论

原始 DR-F **不通过事实验收**，不能作为后续决策的权威来源。它发生了论文身份串线、仓库提交与许可
误判，并把不存在的一套 Shen et al. (2022) 公共工具链当作核心前提。其“当前不进入 GPU”这一动作结论
仍然成立，但理由需要改写。

本地最终资格判定为：**当前 NO-GO（对“立刻将 ESL/CTB ECI 升格为论文主轴并开始复现”）**。

唯一决定性的失败项是：截至本次审计，未取得两个独立近期正式方法在**同一个冻结数据集、fold、候选对、
采样和 evaluator**上的公开可执行实现。ICCL 公开代码只覆盖 ESC；DICP 公开代码只覆盖 CTB；两者完整
Git 历史也没有另一数据集入口。LKCER/DECLV 未取得官方代码，且属于同一作者团队族。按已批准的硬门槛，
这足以停止，不启动 GPU smoke。

这个 NO-GO 不等于 ECI 问题无价值，也不等于公开数据无法冻结。相反，数据和大部分协议组件比 DR-F
判断得更完整：ESC v0.9、CTB 官方 ZIP、候选对规则、随机种子和 evaluator 实现均有一手可恢复资产。
因此更准确的表述是“**当前双 baseline 门未通过**”，而不是“六项均不可恢复”。

## DR-F 的决定性事实错误

| 项目 | DR-F 写法 | 一手核验 | 影响 |
|---|---|---|---|
| ICCL 身份 | 将 `2024.emnlp-main.51` 写成另一题名和九人作者 | 官方论文为 *In-context Contrastive Learning for Event Causality Identification*，作者 Liang Chao、Wei Xiang、Bang Wang；PDF 直接链接 ICCL 仓库 | per-paper matrix 身份串线 |
| DICP 身份 | 将 `2025.findings-emnlp.139` 写成 “Dynamic Interval Contrastive Prompt” 及另一组作者 | 官方论文为 *DICP: Deep In-Context Prompt for Event Causality Identification*，作者 Lin Mu 等七人；官方仓库 README 同名 | 参数、硬件、方法描述串线 |
| DICP 硬件 | Tesla V100、batch 8、lr `1e-6`、30 epochs | 官方 PDF 明写单张 RTX 3090、batch 20；公开代码默认 BERT/RGCN lr `1e-5`、100 epochs | 27GB 判定依据错误 |
| EventStoryLine 许可 | GitHub/MIT | 当前官方根 `LICENSE.md` 明确为 CC BY 3.0；ECB+ 子目录亦有 CC BY 3.0 数据许可 | 数据许可误判 |
| Causal-TimeBank 许可 | README CC BY-NC-SA 3.0 | 当前仓库无 LICENSE，README 无许可声明 | 许可边界误判 |
| 仓库 HEAD | ESL `2b6f420a...`；CTB `9db986...` | 当前默认分支分别为 ESL `46edefee...`、CTB `43b593a6...` | 仓库快照不可复现 |
| Shen 2022 工具 | 三篇共同使用其公开 data processing tools | DPJL 正式论文只给纸面设置；脚注承诺录用后发代码，但 ACL 页面无链接，GitHub 精确检索无仓库 | DR-F 核心否决前提失实 |
| 协议代码 | folds/pairs/evaluator 均未取得 | ICCL 与 DICP 官方仓库均含可读的划分、候选对和 P/R/F1 代码 | 六门全 FAIL 过度判断 |

## 一手恢复出的数据与协议

### EventStoryLine / ICCL

- 论文与代码主表使用 ESC v0.9；官方仓库在 `annotated_data/v0.9` 保留 22 topics、258 个 XML 文档。
- ICCL `ESC_processor.py` 对每篇文档内事件做无序两两组合，任一方向存在 PLOT_LINK 即为正例。
- topics 37、41 固定为 dev；程序在读数据前固定 seed 209，剩余文档运行时打乱后切为 5 折。
- 仓库有训练和 positive-class P/R/F1 代码，但缺 requirements、运行命令、`train.npy` 与
  `event_mentions_extended`，并含作者机器绝对模型路径。
- ICCL 论文写在 NVIDIA 3090 级 GPU 上运行、batch size 16、平均约 5 GPU 小时；公开入口把
  `CUDA_VISIBLE_DEVICES` 固定为 `0`。这构成可信单卡路径的强间接证据，但论文原文使用复数 “GPUs”，
  不能冒充已经实测的峰值显存。

### Causal-TimeBank / DICP

- 官方 CAT ZIP SHA-256：
  `0bf4fed1206b273174a962913b8904b4cb069c9e24f60af38cef71a5bf7b4206`。
- 官方 TimeML ZIP SHA-256：
  `1b01b81a55890004b03a3051f4321b87249221bbe25f30e42bd56f73fa77b317`。
- CAT ZIP 独立 CPU 解析得到 183 documents、6811 events、318 CLINK、9721 个同句无序候选对、
  298 个同句正例；与 DICP 代码注释逐项一致。论文常写的 184/6813 是纸面统计差异，不是当前代码漏读。
- DICP 只保留同句事件对；seed 6688 打乱文档后做 10-fold KFold；训练正/负采样率默认 5/0.3；
  evaluator 为二分类 positive-class P/R/F1。
- 仓库有 requirements 和预处理链，但漏列直接依赖，README 指向不存在的通用入口，实际只提供 CTB
  训练脚本，且含作者机器绝对路径。当前训练入口还直接导入仓库中不存在的 `models.prompt4` 和
  `amr_data_loader`，所以不能按原仓库直接执行。

### DPJL（Shen et al., 2022）

- ACL Anthology ID 为 `2022.coling-1.200`。
- 论文规定 ESC v0.9、topics 37/41 dev、ESC 5-fold、CTB 10-fold、P/R/F1、三次独立实验均值和
  训练负采样率 0.5。
- 未提供 fold seed/manifest、候选对清单或实际代码地址。因此后续论文共享的是 protocol lineage，
  不能证明历史落盘 folds 完全相同。

## 修正后的 Go/No-Go 门

| 门槛 | 本地状态 | 依据 |
|---|---:|---|
| 数据版本/获取 | **可冻结** | ESC v0.9 可绑定官方提交和文件 manifest；CTB 两个官方 ZIP 已取得精确 SHA-256 |
| 许可边界 | **有条件** | ESC 为 CC BY 3.0；CTB 公开可下载但无显式 LICENSE，上游 TimeBank 权利不能扩张解释 |
| Split | **各自可重建，历史同轴未证明** | ICCL ESC 与 DICP CTB 都有代码/seed；DPJL 无历史 manifest |
| Pair / sampling | **各自可重建，跨实现未统一** | ICCL 全文档事件对；DICP 同句事件对；训练采样规则不同且只在各自数据线出现 |
| Evaluator | **实现可得，统一口径待冻结** | 两仓库均计算 positive-class P/R/F1，但未证明 fold aggregation 与论文表格完全一致 |
| 两个独立近期对手 | **FAIL** | ICCL 只公开 ESC；DICP 只公开 CTB；LKCER/DECLV 无已核实代码且为同团队族 |
| 27GB | **纸面高可行，执行闭环未通过** | DICP 正式论文实测单张 RTX 3090；ICCL 论文为 3090 级且代码固定 GPU 0，但原文 GPU 数量有歧义；两者均未在本项目实测峰值 |

## 决策与下一步

1. **不运行 GPU、不开始 baseline reproduction、不进入章节设计。** 双 baseline 门已经失败，继续做
   显存 smoke 不会改变该门槛。
2. 按既有综合决策，将 ESL/CTB ECI 从“条件性主锚”降为“协议资产可复用但当前未过资格”。
3. 回到已指定的第二候选：固定协议 MAVEN-ERE causal，先做同样的“同一公开 split + evaluator +
   至少两个独立可跑近期方法”静态资格审计；仍不先跑 GPU。
4. 若未来发现 LKCER/DECLV 或另一独立 2024–2026 ECI 方法的官方完整代码，可重新打开 ECI 门；
   重新审计必须要求它能在 ESC 或 CTB 之一与现有公开实现共享冻结协议，不能只引用论文表格数字。

## 一手来源入口

- [EventStoryLine 官方仓库](https://github.com/tommasoc80/EventStoryLine)
- [Causal-TimeBank 官方仓库](https://github.com/paramitamirza/Causal-TimeBank)
- [DPJL（COLING 2022）](https://aclanthology.org/2022.coling-1.200/)
- [ICCL（EMNLP 2024）](https://aclanthology.org/2024.emnlp-main.51/)
- [ICCL 官方代码](https://github.com/ChaoLiang-HUST/ICCL)
- [LKCER（COLING 2025）](https://aclanthology.org/2025.coling-main.495/)
- [DICP（Findings EMNLP 2025）](https://aclanthology.org/2025.findings-emnlp.139/)
- [DICP 官方代码](https://github.com/sj1071-cell/DICP)
- [DECLV（EMNLP 2025）](https://aclanthology.org/2025.emnlp-main.616/)

## 审计边界

- 本轮没有训练任何模型，没有运行 GPU，也没有把“代码可读”写成“结果已复现”。
- 本轮只对官方数据做只读 CPU 计数；临时克隆与论文 PDF 位于 `/tmp/ekg-f-audit.vjo1yq`，未写入项目代码。
- CTB 无显式许可证不妨碍记录其公开下载事实，但在数据再分发和公开派生包前必须另做权利核验。
- 对 GitHub “未检索到”只写检索下界，不宣称方法代码绝对不存在。
