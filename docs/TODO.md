# EKG 实时状态

> 更新于 **2026-08-28**。本文件只记录当前位置、门状态、下一步和停止条件，不复制实验数字。
> 总纲见 [`SPEC.md`](SPEC.md)，活动契约见 [`phases/`](phases/README.md)，实验事实只认
> [`results/`](results/README.md)，G0 筛查见
> [`replan/G0_PROTOCOL_GATE_SCREENING.md`](replan/G0_PROTOCOL_GATE_SCREENING.md)。

## 当前结论

- 论文结构固定为 **三个方法章 + 一个系统评估章**：身份、关系、事实性、下游误差代价；
- 当前没有方法章完成“同协议多个 baseline + 三种子超过多个 + 机制消融”的最终验收；
- Ch3 历史 valid 分数不能与论文 hidden-test 分数直接相减，旧“已过线”判断作废；
- Ch4 的消费者依赖性仍是假设，只有同 query、同 serialization、同 backbone frozen-vs-finetuned 才能
  支持微调相关解释；
- P1 的 manifests、official evaluator、adversarial fixtures、stage bundle 和三个 Ch2 schema smoke 已闭合，
  `global_protocol_status=PASS`；没有发现课题级硬阻塞；
- P1.6 的 4090 历史 checkpoint load、最长 internal-dev 与 frozen 10-doc 真实前向均通过，
  `a3_entry_status=PASS`；允许进入 A3.0 同协议 baseline 实验，但尚未放行 A3 主方法三种子。
- 权威 P1 trust root 是 `p1-v6-20260829-r9` / `440516dc...a6d4fdc`；399 tests/ruff/smoke 全绿并独立复验。
  r7 解开了信任根与执行面的耦合：A3 materializer/launcher 已移出 `CODE_PATHS`，local gate 改为逐文件
  记录、只校验 P1 代码路径。**r7 因此是在当前脏工作树里直接建成并复验的，不再需要 detached clean
  worktree**；r1–r6 保留为不可变审计物。A3 plan 已按 r7 重新物化，三路 seed-13 no-execute 通过；
  尚未启动 GPU baseline（远端需用同一命令重新物化 plan）。
- P1 分开记录 `global_protocol_status` 与 `a3_entry_status`；只有全局协议失败阻塞全链，A3 baseline
  closure 失败只产生 A3 `blocked/executed=false` handoff，D3 仍可继续。

## 唯一执行顺序

> **P1 协议冻结 → A3 Ch2 → D3 Ch3 → C4 Ch1 → E3 Ch4 → H2 总体验收**

任一时刻只执行一条 phase。下一 phase 只能在收到前一 phase immutable bundle/status 后开始；前一阶段
pass/failed/blocked 均可完成 handoff；局部失败不阻断后续方法章或系统评估，但其产物必须保留原身份。

## 阶段状态

| Phase | 状态 | 当前含义 | 契约 |
|---|---|---|---|
| **P1** | **COMPLETED / PASS** | P1.1–P1.6、bundle reader 与本地 gate 全部闭合 | [`PHASE_P1`](phases/PHASE_P1_protocol_freeze.md) |
| **A3** | **ACTIVE / ENTRY PASS** | 先执行 A3.0 同协议 baseline，方法三种子仍受 promotion gate 约束 | [`PHASE_A3`](phases/PHASE_A3_relation_balanced.md) |
| **D3** | BLOCKED BY A3 HANDOFF | Ch3 evidence-conditioned 方法；不做跨数据集救火 | [`PHASE_D3`](phases/PHASE_D3_evidence_conditioned.md) |
| **C4** | BLOCKED BY D3 HANDOFF | Ch1 context-discriminative identity；不再跑非对称旧线 | [`PHASE_C4`](phases/PHASE_C4_context_identity.md) |
| **E3** | BLOCKED BY C4 HANDOFF | Ch4 本地重建 CGEP-MAVEN 协议的真实 factorial | [`PHASE_E3`](phases/PHASE_E3_factorial_consumers.md) |
| **H2** | BLOCKED BY E3 | 汇总三种子、消融、复现与论文表格反查 | [`PHASE_H2`](phases/PHASE_H2_thesis_acceptance.md) |

旧 A2/C2/C3/D2/E2/H 契约均已标 `SUPERSEDED`，只可阅读历史推导，不得执行。

## G0 已筛查事实

### PASS（P1 实测更新）

- MAVEN-ERE / MAVEN-FACT 主文件、hash、ID 唯一性与 train/valid 跨数据集集合对齐；
- 三份历史 710-doc prediction/dump 对 valid 零缺失、零重复；
- official evaluator 固定恢复路径/hash、710-doc gold-self、四类手算 adversarial fixtures 与严格拒绝路径；
- 显式 ERE/FACT train/internal-dev/final-valid manifests、supports、candidate/label digests 与 portable manifests；
- local pair、official single、official joint 的同一 10-doc official-schema smoke；
- stage bundle 四件套及坏 hash/重复/缺失 ID/未知 upstream 测试；
- 4090 上 Ch1/Ch2/Ch3/Ch4 历史 checkpoint/heads 在位；
- P1.6 4090 当前结构兼容 checkpoint 的 longest internal-dev/10-doc 真实前向、回传 hash 与 strict schema；
- 七个关键 CLI 的本地 CPU import/help smoke；
- 零新增人工标注与单卡 RoBERTa/SeDGPL 基础可行性。

### CONDITIONAL / PHASE-LOCAL

- Ch1 训练脚本缺 internal-dev 与 best checkpoint（C4-local，不阻塞 A3）；
- Ch3 训练脚本显式 manifest 适配留在 D3 前；Ch2 已支持显式 manifest；
- Ch3 强 baseline、Ch1 official baseline、Ch4 BART/consumer 尚未闭合，均为对应阶段前置；
- Ch4 缺完整 query 文件、事实性节点属性和 frozen consumer，均不阻塞 A3。

## 当前位置：A3.0 baseline 批次执行中

**协议**：P1 r9 `440516dc…0a6d4fdc`｜A3 plan r10 `36a38e4f…085d4d15`｜seed 13（作者定：单种子）｜
train 2,622 训练 + internal-dev 291 选模｜**final-valid 未访问**｜官方 `evaluate.py`｜三族全评。

| baseline | 状态 | 备注 |
|---|---|---|
| local_pair | ✅ 完成 | 数字见 [`results/PHASE_A.md`](results/PHASE_A.md)；首跑因冻结配方 α=0.0 使稀有族坍塌而作废，α=0.5 重跑 |
| official_joint | 🔄 运行中 | 官方 100 epochs，约 5.5 分钟/epoch，预计约 9 小时 |
| official_single | ⏸ 排队 | 契约要求 4090 每次只跑一个实验任务，不并发 |

主锚在三个 baseline 全部完成后、任何方法结果产生前解析并冻结。

### 已补齐的下游前置（不阻塞 A3，趁 GPU 排队时在 CPU 完成）

- `ekg.core.protocol` 成为唯一的 manifest 划分实现；Ch3 训练脚本已接入显式 split；
- Ch1 训练脚本接入 P1 manifest + best-epoch 选择，修掉一处**选模污染**：
  MAVEN-Arg 与 MAVEN-ERE 是同一批文档，训全量 Arg train 会把 291 篇 internal-dev 全部纳入训练
  （对 final-valid 无污染，历史 MUC 77.47 干净）；
- Ch2 的 trainer 暂不改用共享划分实现——它是 P1 绑定文件，A3 批次跑完再统一。

### temporal 已进入 Ch2 主贡献表（2026-08-29）

TIMEX 端点已闭环，候选按族分离（causal/subevent 纯 event、temporal 含 TIMEX，对应官方
`ignore_timex`）。三族各有预注册非劣护栏锚 = official joint。全语料 3,623 篇 / 20,827 个 TIMEX
零定位失败；推理侧预测边含 TIMEX 由 0% 升到 37.6%（gold 39%）。九个会让正式跑报废的缺陷由
一次 20 篇 pilot 抓出，逐条见 [`results/PHASE_P1.md`](results/PHASE_P1.md)。

## 全局停止条件

- 数据/manifest/evaluator hash 漂移：所有下游结果停止使用，回 P1；
- 同一 baseline 两个“诊断→补丁→同协议 smoke”工程轮仍不闭环：降背景并换预列候选；候选失败不等于
  任务或全篇 NO-GO；
- 核心方法两个完成实现/测试/协议 smoke 的设计周期仍未超过 gate：该章降为系统组件；二级机制失败只
  删除 claim，不触发整章止损；
- valid 被用于本轮选模：结果标 exploratory，不得进最终主表；
- 任何跨章 ID 缺失、重复或 schema 不一致：下游立即停止，不填默认值继续；
- 一个方法章 failed/blocked：由作者/导师决定是否正式改纲为“两方法章 + 一系统评估章”；
- 两个方法章 failed/blocked：v6 主线 NO-GO，另行重规划，不能包装成“两方法章”版本；
- Ch4 两类消费者都未通过图依赖正控：撤回独立消费者依赖性贡献，收缩为误差传播副章；
- 只有不同 backbone/数据的消费者可比：只报告描述性差异，不使用“微调导致”措辞。

## 资源状态

- 本地：只做 CPU、文档、实现、测试、manifest/hash 与缓存回放；
- 4090：主 GPU；cpolar 间歇性 banner timeout 后已用 ControlMaster 恢复，P1.6 在 GPU 0 完成；
- 5090：本轮未访问，后续每次单独授权；
- 不提交、不推送，除非作者明确要求。
