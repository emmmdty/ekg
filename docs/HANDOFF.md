# 交接文档 · 新窗口从这里开始

> 更新于 **2026-09-12**。本文是新窗口唯一必读入口；读完后再按本文链接打开所需文件，不回溯聊天记录。
> 本文只记录状态、决策、依赖与下一步，不复制实验表格。实验数字只认
> [`results/`](results/README.md)。

## ▶ 当前阶段（新窗口先看这张表）

| 项 | 值 |
|---|---|
| 正式阶段 | **方法实验期，Gate 1 已触发**。2026-09-12 跑完 v6.1 的**第一个真方法结果** D4.3，**失败**。按事先冻结的 Gate 1 分支：**不开第二个周期**，转去把 A4 与 C5 跑出来，到 Gate 2 再判还剩几个方法章。 |
| **⚠️ 这一轮最重要的一件事** | **Ch3（D4）的 typed-cue 家族已关闭**，以 `failed` 身份留档。full `.476515` 低于两个锚（`.553995` / `.545603`）**七倍地板**，消融 `.536788` 与负控 `.495260` **都赢过 full**，预注册中介**反向**，PS−/Uu 护栏双破。归因与「五维瓶颈」这个**未验证**的候选原因见 [`results/PHASE_D.md`](results/PHASE_D.md)；不可变 handoff `pilot/seed-13/status.json` `3b4dbba2…a46234`。 |
| **论文结构** | 第3章 事实性检测（D4，**本轮失败**）· 第4章 关系抽取（A4）· 第5章 身份消解（C5）· **第6章 事件图谱构建与下游事件预测应用（E3）**。原 24 条件 factorial / Holm / frozen-vs-finetuned **已撤销，不得恢复**。**章节存废在 Gate 2 判，执行代理不得自行改成两方法章。** |
| **⚠️ 唯一权威计划** | **[`EXPERIMENT_PLAN.md`](EXPERIMENT_PLAN.md)**。可执行实验只认它的 §4 主表与 §5 的 Gate；本文队列只是切片，**不得出现主表以外的新任务**。要偏离顺序**先改主表**。 |
| **活动任务** | **无。GPU 上没有任何我们的进程。** 新窗口从 §0.3 的队列开工。 |
| ⚠️ **gpu-4090** | 驱动已修好（580.178.04，`torch.cuda.is_available()=True`，G-0 完成），但 **2026-09-12 19:0x 起四张卡被用户 `Zhyw` 的 vllm 占满**（各约 20–22 GB）。**再用必须先 `nvidia-smi` 核卡，不得挤占。** |
| ✅ **gpu-5090** | 作者授权：**≤1 天的任务直接执行，不再逐次请示**（超过一天要问；拉模型/跨机搬运先问位置）。backbone 已就位 `2c7ff1f1…49736`（六件全部公开源）。硬边界：**EasyECR 跑不了**（torch 2.0.1 不支持 sm_120）。 |
| 截止与排期 | 实验须在 **2027-02** 前完成。排期与估算基准率见 `EXPERIMENT_PLAN.md` §3：顺利情形 2027-01 底收口、2 月缓冲；**两个以上方法章需第二设计周期则缓冲清零**。 |
| 完成后必须做什么 | 按 §6 五步回填：产物落地 → 写结果页 → 改队列行状态与 commit → 推进队列 → commit + **push** |

### 本次交接的已知工作树例外

交接提交后 `HEAD` 应等于 `origin/main`。唯一已知的未提交修改是作者本人维护的
`docs/reports/TEMPLATE_周报.md`：它是当前有效周报模板，**不得 stage、revert、clean 或混入任何实验提交**。
其他未说明的改动按异常处理。最新导师可读周报是
[`reports/2026-09-10_周报.md`](reports/2026-09-10_周报.md)。

## 0. 接手后先做什么

### 0.1 只读检查（三条，全过才开工）

```bash
cd /home/tjk/myProjects/masterProjects/ekg
git status -sb                      # 期望：main 与 origin/main 同步、工作树干净
git log -3 --oneline --decorate
uv run python scripts/audit_r1_consistency.py \
  --output runs/stages/R1/r1-v61-20260904/audit/cross_artifact_audit.json
                                    # 期望：PASS: 36 requirements mapped
```

工作树若出现未说明改动，**先查来源，不覆盖、不清理**。

### 0.2 按顺序读这三份（够了，不要重读整个仓库）

1. **[`EXPERIMENT_PLAN.md`](EXPERIMENT_PLAN.md)** —— 唯一权威计划。§4 主表挑任务，§3 看排期与
   5090 边界，§7 看每章最终要交的表长什么样；
2. **[`BASELINE_ROSTER.md`](BASELINE_ROSTER.md)** —— 四章的外部对手名册与 FR-016 保真度路径；
3. 本文 §E.0 的六条交接约束（HEAD 等于 origin/main、单队列、改计划先改文件、不开分支/worktree、
   活动任务独占产物、交接必须已 push）。

按需再读：对应章节的 `phases/PHASE_*.md` 契约、`results/PHASE_*.md`（数字唯一权威）。

### 0.3 下一个窗口执行什么（2026-09-12 冻结）

**Gate 1 的裁决是事先写死的，不要重议**：`EXPERIMENT_PLAN.md` §5 的 Gate 1「不过」分支写着
**不启动第二个周期，直接进 Gate 2 讨论结构**。D4.3 不过，所以 typed-cue 家族到此为止。
`PHASE_D4` 的 stop conditions 里那句「两个有效周期后封存」允许第二轮，但**主表的 Gate 1 更具体
且先于结果冻结，以主表为准**——Gate 存在的意义就是结果难看时不临时给自己加一次机会。

⛔ **因此下面这些一律不做**：D4 第二个周期、调 threshold、扫 epoch、换 split、加大 backbone、
用 seed 17/42 去捞 D4、把「五维瓶颈」当成已证结论去改设计。

**按这个顺序做，全部是 CPU，不占卡：**

| 次序 | 主表 ID | 做什么 | 完成判据 |
|---|---|---|---|
| **1** | **C-6** | **A4.0 实现 + 本地 gate**（Ch4 关系抽取，方法**一行都还没写**） | targeted tests + 三件套全绿；契约见 `phases/PHASE_A4_pair_evidence.md` |
| **2** | **C-5b** | C5 的四个入口脚本：`train_` / `evaluate_` / `prepare_*_preflight` / `smoke_`（C5.0 核心件 `role_uncertainty.py` 已于 `fc25777` 交付） | 同上；**照 D4 的四件套形状写，并把 pilot 入口一起写掉** |
| **3** | **C-9 的同类缺口** | **给 A4 与 C5 各写 pilot 入口**（`run_a4_*.py` / `run_c5_argument_uncertainty.py`） | 契约点名了它们；D4 就是因为这个缺口白等了一轮 |
| 4 | **C-7** | LLM 对照脚手架（三章各一个 CPU fixture） | 见主表 §4.1 |
| 5 | **C-8** | 第 2 章统一评测协议素材 → `docs/PROTOCOL_TABLE.md` | 每一格都能从 `results/` 或 `runs/` 反查 |

**GPU 泳道（等 1–3 做完，且核卡确认有空闲）**：G-4（A4.2 smoke → A4.3 pilot）、
G-5（C5.2 smoke → C5.3 pilot）。两者**写不同 namespace，可并卡**。跑完这两个就到 **Gate 2**。

#### 从 D4 这一轮学到、必须带进 A4/C5 的三件事

1. **先查契约点名的入口脚本在不在**。D4 的 `run_d4_typed_cue_oof.py` 从没被写过，
   却在契约的 GPU 命令里躺了很久。**A4/C5 现在就有同样的洞。**
2. **pilot 入口必须进 preflight 的 `code` 哈希集合**，否则那一跑是唯一钉不住的代码。
   D4 为此重建了 preflight（`preflight-r2`，`code_files=7`，旧的不覆盖）。
3. **报增益前先看噪声地板**。5090 的独立重建把 D4 anchor 的可复现地板量到约 **±.01**
   （见 `results/PHASE_D.md`）；小于这个量级的差不要当效应。

#### 环境既成事实（不用再查）

- 三个 gitignored JSON 已双端核对（`protocol.json` `f0b4702b…50829`、`t024_freeze.json` `9133a73c…587e7`、
  `cross_artifact_audit.json` `622d094b…f8467`；4090 旧档备份 `protocol.json.pre-e12-20260911`）；
- **gpu-5090 的 cpolar 端口 2026-09-12 18:00 换了：`13850` → `12528`**（`~/.ssh/config` 已是新端口）。
  新端口给出的指纹与作者确认过的**完全相同**（ED25519
  `SHA256:Jkfb9Tb14Z/SqsG6g9GedDjKZOcBl1DLW6zT0V1dkJY`），即同一台机换了端口、不是新指纹，
  故已把该确认过的 key 在新端口下写入 `known_hosts`，实测可连、卡空闲。
  **端口还会再变**：下次若指纹与上面这串不一致，**停下问作者，不得自行 TOFU**；
  一致则可照此在新端口下钉住；
- 两台机的 cpolar 隧道都会掉线。**ssh 失败 ≠ 远端进程死亡**，三态判活；长任务一律
  `setsid nohup` + `python -u` + 重定向 `logs/`，**一条 ssh 只发一个后台任务**。
  实测这样起的进程 PPID=1、独立 session，本机关机不影响。

### 0.4 2026-09-11~12 这两轮做完了什么（记录，不用再做）

| 主表 ID | 结果 |
|---|---|
| **C-1** D4.1 preflight | ✅ PASS。执行中修掉三个「本地绿灯、服务器上跑不起来」的缺陷：脚本自造目录摘要去比 P1 的内容地址（唯一的测试是拿算法和它自己对）、`acceptance.json` 的裁决键是 `acceptance` 不是 `status`、`oof_summary.json` 记的是仓库相对路径。三条都进了 `ENGINEERING_NOTES.md` |
| **C-2** EasyECR 核查 | ✅ 静态裁决 `conditionally_runnable`，仓库 `hqyang/EasyECR @ f6cd779f`（URL 此前项目里从没记过）。6 条阻断点名可数；allennlp 矛盾由求解器机器复现。KBP 2017 需 LDC 许可 → **FR-016 (b)**。**剩 C-2b**：活体 venv + import 冒烟 |
| **C-5** C5.0 核心件 | ✅ `src/ekg/nodes/role_uncertainty.py` + `role_compatibility` 组件，15 条测试（`fc25777`） |
| **C-9** D4 pilot 入口 | ✅ 新写 `scripts/run_d4_typed_cue_oof.py` 并纳入 preflight 哈希集合（`a90df4e`） |
| **G-0** 4090 驱动 | ✅ 已修（580.178.04）。**但四张卡现被他人占用** |
| **G-1** D4.2 smoke | ✅ CPU + CUDA 双半边，三臂产物**逐字节相同** |
| **G-2** D4.3 pilot | ❌ **失败**，见本文 §▶ 表与 `results/PHASE_D.md` |
| — | 5090 上用**全公开源** backbone（`2c7ff1f1…49736`）独立重建了 D4 的两条 anchor：CLS `.543514` / DMRoBERTa `.536622`，同一排序、绝对值低约 .010 → **可复现地板 ±.01** |

**D4 的两条 anchor 线并存，永不混表**：4090 线（`.553995` / `.545603`，backbone `71be7419…`，
有 preflight 与 acceptance）是主表用的；5090 线（`.543514` / `.536622`，backbone `2c7ff1f1…`）
是独立复现与备份。各自标明机器与 backbone 地址，**不相减**。

## 1. 当前裁决与状态

### 研究目标

课题仍是 occurrence-level 事件图谱：Ch1 身份消解、Ch2 关系抽取、Ch3 事实性检测、Ch4 构建错误的
下游代价。论文目标继续是**三个高质量方法章 + 一个系统评估章，不降标**。

旧机制失败不等于取消方法章：同一机制家族两个有效周期未过门就封存；新家族必须重新通过文献、
协议、因果链、功效和新颖性审查。执行代理不得自行改成两方法章。

### SDD 文档边界

| 层 | 权威文件 | 只负责 |
|---|---|---|
| 研究治理 | [constitution](../.specify/memory/constitution.md) | 不可妥协的有效性、可追溯性和修订原则 |
| 稳定需求 | [`SPEC.md`](SPEC.md) | WHAT/WHY、研究场景、质量底线、可验收结果 |
| 可迭代方案 | [`RESEARCH_PLAN.md`](RESEARCH_PLAN.md) | 候选方法、评测设计和当前依赖计划 |
| 可执行任务 | [`TASKS.md`](TASKS.md)、[`phases/`](phases/README.md) | 步骤、输入、门、停止条件和产物 |
| 运行状态 | [`TODO.md`](TODO.md)、本文 | 当前做到哪里、下一动作 |
| 实验事实 | [`results/`](results/README.md) | 数字、口径、产物和真实 PASS/FAIL |

SPEC **没有**固定 C5/A4/D4 的具体实现、baseline 名单、GPU、epoch 或执行顺序。当前候选中心假设是
evidence adequacy / uncertainty propagation；R1 若找到反证或更强设计，应改 plan，不应把候选方法硬塞回
SPEC。只有研究问题、范围或质量标准改变时才修订 SPEC。

### Git 与验证

- 协议代码整改：`23b4fad fix(protocol): centralize P1 manifest and hashing logic`；
- SDD/方法论整改：`c870ed7 docs(research): separate stable spec from adaptive methodology`；
- R1 审计代码/结果：`8e3eb7a feat(r1): add dataset and prospective power audits`、
  `4e893c1 docs(r1): record method design gate evidence`、`f1401bc feat(r1): freeze factuality
  cross-validation folds`、`32cfd46 feat(r1): close relation handoff and power gate`、
  `277b36f fix(r1): isolate factuality OOF training source`；
- 本文提交后以新的 `origin/main` HEAD 为准；
- 最新本地验证（2026-09-12，`8f17cd1`）：**560 passed / 26 expected skips**，ruff 0，`ekg-smoke` OK；
- local gate 的 `tested_tree_sha256`：
  `52c639ff79fb9401f71d42d4d1ecaec6abacf65701cecf72f1dcac7edb04f46e`（220 个文件；
  前值 `3bff2ac2…c701d3c` 对应 `886185e`）；
- A3.6 只运行了已授权 seed 13；R1 功效只读 train-derived internal-dev。跨数据 ID 审计按合同读取了
  public-valid 结构字段但未计算关系/事实性指标，访问已在 ledger 披露；没有搬运 checkpoint。

## 2. 已经成立和不得改写的事实

只从下列结果文档取精确数字：

| 主题 | 权威入口 | 当前结论 |
|---|---|---|
| Ch2 工作点与检索 | [`results/PHASE_A.md`](results/PHASE_A.md) | 工作点两个核心周期已用完；近似 retriever 三条均未过门；prototype/ATLoss 已封存 |
| Ch1 历史方法 | [`results/PHASE_C.md`](results/PHASE_C.md) | 旧方法未稳定胜出；event-level gold argument 只能作泄漏型 oracle |
| Ch3 历史方法 | [`results/PHASE_D.md`](results/PHASE_D.md) | 旧 D3：与强 baseline 未统计分开。**新 D4：typed-cue 家族 2026-09-12 失败并关闭**（Gate 1「不过」分支），消融与负控都赢过 full |
| Ch4 历史系统证据 | [`results/PHASE_E.md`](results/PHASE_E.md) | 图依赖正控与部分构建损失成立；正式同实例 factorial 尚未完成 |
| P1 可信根 | [`results/PHASE_P1.md`](results/PHASE_P1.md) | r15 是 A3.6 与当前 R1 的可信根；旧 A3 结果继续绑定各自历史根 |

A3.6 **官方训练配方分账已经完成**。它只分解 rates、coref auxiliary、per-family checkpoint selection
三个复现变量，不是论文创新。最高 causal F1 仍未越过冻结主锚，A3 以 `a3-v6-20260905-r17`（protocol
`c187bf03…9359e`）不可变 `failed` bundle 关闭；之后只由 R1 决定新的 Ch2 方法家族。

禁止：第三个工作点、第四个近似 retriever、继续 prototype/ATLoss、把 r13 已观察到的 by-family 曲线
回收成第 4 臂、用更大 backbone 或换 split 救旧机制。

## 3. 后续任务：按依赖执行

当前依赖图：

```text
P1 r15 ─→ A3 failed handoff r17 ─┐
R1 准备任务 ─────────────────────┴→ R1 baseline/input closure
                                                           ├→ C5 候选方法
                                                           ├→ A4 候选方法 ─→ E3 → H2
                                                           └→ D4 候选方法
```

C5/A4/D4 之间没有被 SPEC 固定顺序。R1 未发现真实数据/模型依赖时，可以重排或占不同 GPU 并行；E3
必须等待三类所需上游 handoff。多种子始终需作者再次明确授权。

### 任务 A：本地重建 P1 trust root（已完成）

本轮已创建新 bundle，未覆盖旧目录：`runs/stages/P1/p1-v6-20260904-r15/`；其
`protocol.json` SHA-256 为 `1e31a9acef39261f776f7ed4069fd73f4531e8d12b55779bfc0fbd74c67f9655`。
外部重哈希、`--validate-only` 与 registry 三方一致，状态 `pass/pass`；精确记录见
[`results/PHASE_P1.md`](results/PHASE_P1.md)。历史 A3 结果仍引用 r12，不重绑。

本轮实际执行命令如下，保留作复现记录：

```bash
cd /home/tjk/myProjects/masterProjects/ekg
uv run python scripts/run_p1_local_gate.py
```

三件套均通过，`data/protocols/v6/local_gate.json` 无身份漂移；随后确认目标目录不存在：

```bash
test ! -e runs/stages/P1/p1-v6-20260904-r15
```

创建并内部验证新 bundle：

```bash
uv run python scripts/build_p1_bundle.py \
  --bundle runs/stages/P1/p1-v6-20260904-r15
```

最后独立查看并验证身份：

```bash
sha256sum runs/stages/P1/p1-v6-20260904-r15/protocol.json
uv run python scripts/build_p1_bundle.py \
  --bundle runs/stages/P1/p1-v6-20260904-r15 \
  --validate-only
python3 -c "import json; p=json.load(open('data/protocols/v6/registry.json')); print(p['p1_bundle_id']); print(p['p1_bundle_protocol_sha256']); print(p['global_protocol_status'], p['a3_entry_status'])"
```

验收：

- bundle ID、外部 `protocol.json` SHA-256、registry 三者一致；
- `global_protocol_status=pass`、`a3_entry_status=pass`；
- code hash 集同时包含 `src/ekg/core/protocol.py` 与 `scripts/train_supervised_relations.py`；
- 新 bundle 与 r12/r14 并存，旧结果身份不被覆盖；
- 新根及其 hash 写入 [`results/PHASE_P1.md`](results/PHASE_P1.md)，其他文档只引用。

本次未发生旧 remote smoke 或 hash 漂移失败，也未重跑 4090 smoke。

### 任务 B：R1 准入闭环（进行中；**具体执行顺序看任务 E.2 队列，不要从本节自行挑任务**）

T012–T019 与 T022 已完成（T018 已在 A3 handoff 后补齐），精确数字、hash 和裁决见
[`results/PHASE_R1.md`](results/PHASE_R1.md)，产物根为 `runs/stages/R1/r1-v61-20260904/`，代码提交
`277b36f`。当前硬结论：ERE↔FACT 身份闭环；ERE↔ARG mention 仅约 95.4% 覆盖且共享 mention 有父簇
冲突，故 event-level arguments→mention 的 deployable 路线 blocked；Ch1 prospective power PASS，
argument-aware 同协议 runnable baseline 已由 `qwen3-argument-s13-r2` 闭合（§7），但它 MUC .803676
低于主锚 .809847，第二个不弱于主锚的方法族仍空缺；Ch2 prospective power PASS，但缺第二个独立同协议
runnable baseline；Ch3 的 291-document 设计 underpowered，但预冻结五折 OOF 已完成并验收，CLS anchor 与
2,913-document pooled power 均 PASS。精确数字与 acceptance hash 只见 [`results/PHASE_R1.md`](results/PHASE_R1.md)。

所在单位、学位类型、入学年份、学科与专业未知项均保持 `null`。**2026-09-07 纠正：原先冻结的同济校级来源
整体作废（作者不在同济）**，改按国内顶级 985（清北复交浙、中科大等）对标，已重新冻结学位法 + 清华 +
北大三份来源与 hash，`degree_requirements.json` 与 R1 `protocol.json` 均已重冻结，详见
[`results/PHASE_R1.md` §10](results/PHASE_R1.md)。行政线一律不得用来降低项目自定的更高科研硬门。文献矩阵已只读冻结 CorefPrompt、MAVEN-FACT、ModaFact、TextEE、OmniEvent
五个官方仓库 HEAD（E2 又冻结了第六个 LLMERE，记录在 `results/PHASE_R1.md` §4/§9，
`literature_matrix.json` 保持原哈希不动），但没有把不同数据/split/evaluator 的代码误记为同协议 baseline。Ch3 因果 brief 已
通过 T022 并绑定已验收 OOF/power；Ch2 brief 已由 E3 通过 T021 审查（**仅设计轴 PASS**，relation baseline
门仍 `blocked`）；Ch1 brief 已由 E4 通过 T020 审查（**仅设计轴 PASS**，第二方法族门仍 `blocked`，
等作者裁决）。**三份 brief 均未放行 proposed GPU 训练**。

两台服务器都没有可恢复的 OmniEvent/TextEE EAE checkpoint；OmniEvent 官方 checkpoint URL 已失效，
因此不得把随机初始化或跨 ontology 重训冒充官方 baseline。5090 的既有 Qwen 服务保持运行。

后续按 [`TASKS.md`](TASKS.md) 的 T020–T024 继续，但各章仍先补齐自身 blocker：

1. Ch3：T022 因果 brief 与 T023 跨产物审计均已通过；E6 可冻结 D4 phase contract，未冻结前不启动
   proposed GPU pilot；
2. Ch1：T020 brief 已 PASS；input/baseline blocker 已由 `qwen3-argument-s13-r2` 闭合，但按 §E.1b 的
   四条新措辞第二方法族仍空缺。**E10 已实测 ACCI 公开仓库全历史只有 README**，没有 trainer、模型、
   checkpoint、依赖或数据/评测接口，裁决 `not_runnable`；不得从论文重写后冒充透明移植，下一候选名单需作者
   按 §E.1b 另议。IP&M 2024 无公开代码、OmniEvent EAE checkpoint 失效、RESIJ 未取得；
3. Ch2：T021 brief 已 PASS；门已按 §E.1a 重新界定，第二个不同方法族由 **E8 的 LLMERE-causal**透明适配承担，保持完整候选全集；
4. 三份 brief 的 T020/T021/T022 审查与 T023 均已 PASS；下一步按 E6 冻结各自有充分输入的 T024
   phase contract。继续不看 final-valid、不写 proposed 训练代码。

上面四条是**依赖关系**，不是执行顺序；本周的实际执行顺序与判定标准以任务 E.2 的队列表为准。

产物进入 `runs/stages/R1/r1-v61-20260904/`，结构与完成门以
[`PHASE_R1_method_design_freeze.md`](phases/PHASE_R1_method_design_freeze.md) 为准。R1 准备可以部分完成，
但不能在 baseline/input closure 和跨产物一致性审计前标 PASS。

### 任务 C/D：A3.6 执行、评分与失败交接（已完成）

四臂于 2026-09-04 18:03 使用 GPU0–3 的独立 `setsid nohup` 后台启动，整个训练不依赖 SSH 会话。
2026-09-05 成功 SSH 观察到四个 trainer GONE、GPU 已释放；四臂 train/score return code 均为 0。
本地只同步官方预测、评分、metadata 与小型 selection 文件，双端 SHA-256 一致；checkpoint 全部留在
`gpu-4090:/data/TJK/ekg/runs/stages/A3/a3-v6-recipe-accounting-r16/`。

同一 P1 r15、manifest、候选、evaluator、backbone、epoch 与 seed 13 下，逐臂只改变 rates、coref aux、
per-family selection。四臂均未越过 causal 主锚，A3 已按预注册规则 `failed`；精确数字只见
[`results/PHASE_A.md`](results/PHASE_A.md)。交接 bundle：`runs/stages/A3/a3-v6-20260905-r17/`，protocol
SHA-256 `c187bf03978674edd29ac209658ccb62d457b744a209e864a0fef0e9eee9359e`。

不得新增 seed 17/42，不得把官方配方收益记成方法贡献。R1 只把 causal 最强臂当 prospective-power 与
下一新家族的 fallback 对照。

### 任务 E：交替推进协议与本周队列（2026-09-07 起）

#### E.0 统一约束：Claude 与 Codex 交替推进，不并行、不分叉

两个执行代理**轮流**持有同一条队列，任何时刻只有一个"活动任务"。约束只有六条，违反其一即视为交接失败：

1. **单队列**：任务顺序只认下面 E.2 的历史记录与 E.2a 的接续队列。要偏离顺序，**先改本表再执行**，不在会话里口头改计划。
2. **开工前对齐**：除 §0 的三条只读检查外，必须确认 `git rev-parse HEAD` 等于 `git rev-parse origin/main`；
   不相等就先 `git pull --rebase`，未对齐不开工。
3. **交接靠文件不靠记忆**：一项任务算完成，必须四件齐全——产物落地、数字写进对应
   `results/PHASE_*.md`、本表该行状态改为 `done` 并填 commit、**已 push 到 `origin/main`**。
   没 push 就没交接，下一个代理不得开工。
4. **不开分支、不开 worktree**：只在 `main` 上按逻辑单元提交。（2026-09-07 已删除
   `.worktrees/r1-t023-t024` 与已并入 main 的 `feat/r1-t023-t024`。）
5. **活动任务独占产物**：持有活动任务的代理独占该任务涉及的全部结果页与 `runs/` 目录；
   另一代理此时**只读**，不写任何 `results/`、`runs/`、`TASKS.md`。
   *唯一例外（2026-09-07 作者裁决）*：E8 的长训练只写 `baselines/relation/llmere-causal-*` 这一个
   namespace，持有队列的代理**可以先把它挂到后台再继续做文档行**；回填结果页时才需要重新独占。
   *第二例外（2026-09-09 作者明确授权）*：E8 generation 期间可推进不接触其 namespace 的 D4.0–D4.2。
   D4 在实现、本地 gate、immutable preflight 和 CPU/CUDA smoke 全部通过前不得启动 seed-13 pilot；其 pilot
   独占自己的 `runs/stages/D4/`，不得与 E8 共用 GPU0，也不得启动额外 seeds。
6. **未完成就交接**：把已做到哪一步、卡在什么证据上写进本表该行，状态标 `wip`，不留只有自己知道的上下文。

#### E.1 联网核实结论（2026-09-07，影响下面的排期）

- **Ch2 的第二 baseline 有官方实现，我们此前漏收了**：LLMERE（COLING 2025，
  [aclanthology.org/2025.coling-main.500](https://aclanthology.org/2025.coling-main.500/)）已开源，
  仓库 [github.com/HerbertHu/LLMERE](https://github.com/HerbertHu/LLMERE)，`main` HEAD
  `94d4ef2781ec7e071d38ac7fd8632a8fffbda798`，目录含 MAVEN-ERE / MATRES / HiEve。按"不重复造轮子"，
  **官方实现优先于我们自建的 TacoERE 适配**；`results/PHASE_R1.md` 第 4 节"未取得官方实现"的
  Ch2 结论需要按实测修订。TacoERE 仍无公开代码，本地适配档只能标注为**透明适配**，不得写成官方复现。
- **C5 的一般命题已被抢占**：ACCI（[arXiv 2506.01488](https://arxiv.org/abs/2506.01488)，
  Sci Rep 2026）已占"argument-centric + 结构因果图 + 后门调整 + counterfactual 模块"的事件共指命题，
  ECB+ 88.4 / GVC 85.2 CoNLL F1。它是**跨文档、ECB+/GVC**，我们是**文档内 MAVEN-ERE + 预测
  mention-local 论元 + 缺失感知不确定性门控（不用 gold 论元）**。T020 必须正面处理这条抢占，
  写清窄 delta，并核实 ACCI 用的是 gold 还是预测论元；不能再写"首次"。
- **A4 的一般命题同样被占，但组合仍有窄 delta**：CovEReD
  （[2024.findings-emnlp.672](https://aclanthology.org/2024.findings-emnlp.672/)）已做文档级关系抽取的
  counterfactual 一致性，SURE-RAG（[arXiv 2605.03534](https://arxiv.org/html/2605.03534v1)）已做
  evidence sufficiency + 不确定性弃答。T021 必须把两者写进 related work。
- **D4 暂无直接后续工作**：未检索到 MAVEN-FACT 上 typed cues / modality×polarity 因子化的跟进论文，
  这条赛道当前最干净。结合"Ch3 三个 blocker 全清、pooled power PASS、T022 已过"，
  **D4 是三章里最该先放行 pilot 的一章**。

#### E.1a 作者裁决（2026-09-07）：relation baseline 门重新界定，LLMERE 缩小并行

E3 把 QR-001 的名单问题交给作者后，作者当日裁决**采纳 (b) 的缩小并行版本**。要点：

1. **改门，不改章**：近期 MAVEN-ERE 方法**无一发布可跑的官方训练代码**（RESIJ / 2025 two-stage / KnowQA /
   TacoERE / LLMERE 全部缺），所以「第二个**官方实现**」这道门投入再多 GPU 也过不去——是我们自己的运行口径
   写错了。改回 SPEC `QR-001` 本身的措辞：**第二个不同方法族 · 我们在冻结协议下跑通 · fidelity 缺口写明 ·
   且不弱于主锚**。`SPEC.md` 不修订。
2. **不接受稻草人**：`taco-s13-r3` 只有 causal 32.01 < 主锚 33.17，赢它由赢主锚蕴含。只接受
   「主锚 + 透明适配」被否决。
3. **LLMERE 缩小成 causal-only**：48,365 训练 / 11,149 推理，约 joint 的 1/4；subevent/temporal 是**我们方法的
   护栏**而非 baseline 的义务（`official_single` 是既有先例）。**B2 不需要 Meta 许可**——用未设门镜像 + 披露
   权重 SHA-256。
4. **并行，不串行**：A4 pilot 只吃一张卡而 4090 有四张；第二 baseline 只在确认性 promotion 时生效，
   所以 **T024 照常冻结 A4 契约**，LLMERE-causal 以"已规格化、数字 pending"入 roster。
5. **接受的风险**：LLMERE 若高于主锚，Ch2 及格线抬高、A4 可能失败——**这正是现在跑它的理由**。
6. **明确不做**：拿 LLMERE 已发布的预测在 710 篇 official valid 上用我们的评测器重打分（那是封存的
   final-valid，不值这笔账）。

完整裁决与规格见 [`results/PHASE_R1.md` §13](results/PHASE_R1.md)；brief 的 roster/promotion 已按此修订并在
`amendments[0]` 保留原文（修订发生在任何 A4 数字存在之前）。

#### E.1b 作者裁决（2026-09-07）：Ch1 门同样重新界定，IP&M 口径核实前置到 E6 之前

E4 把两个问题交给作者后，作者当日给出两条裁决。完整依据见
[`results/PHASE_R1.md` §15](results/PHASE_R1.md)。

1. **Ch1 也改门，理由与 §E.1a 同构**：MAVEN-ERE 文档内共指上除主锚外**没有第二个公开可跑的方法**
   （IP&M 2024 无代码 · OmniEvent EAE checkpoint 失效 · TextEE 无 checkpoint · RESIJ 未取得 ·
   CorefPrompt 正依赖那个失效 checkpoint）。E.1a 给 Ch2 加「不弱于主锚」是为了挡稻草人，对 Ch2 有意义
   （LLMERE 真可能强）；对 Ch1 不成立——唯一有公开仓库的 ACCI 是跨文档方法，`ECB+ 88.4` 不保证过
   `.809847`，**大概率低于主锚**，维持原措辞会让移植的期望价值接近零。新措辞是四条同时成立：
   **独立发表工作的机制 · 在其原始基准上有强证据 · 我们在冻结协议下跑通 · 缺口逐表写明**。
   `SPEC.md` 不修订；`taco` 式自造弱变体仍被第 1 条挡住。
2. **顺序倒过来：先静态核查，再谈训练**（队列 E10）。理由是 E2 刚教过——**仓库有方法本体不等于有
   trainer**（LLMERE 全历史 5 个 commit 无训练代码）。核查成本近零却直接决定这条路通不通。
3. **`qwen3-argument-s13-r2` 角色重定义**：它低于主锚不是废数据，而是「**朴素把预测论元池化进编码器
   会掉点**」的注册负面对照，正是 C5 立论的直接证据。**不再充当第二方法族。**
4. **IP&M 2024 口径核实前置到 E6 之前**（队列 E9）：该文同时报 **causal 37.4** 高于 Ch2 主锚 33.17，
   而 E6 就要冻结 A4 契约——**先核实再冻结，别用一个可能已被超越的及格线冻结整章**。
   判据用 MAQInstruct 那把现成的尺子：**看它复现的 official joint baseline 与我们自跑官方码是否对齐**。
   三种处置（可比 / 口径不同 / 拿不到全文）见 §15.3。无论结果如何**它都不能进 roster**——无公开代码，
   按 FR-006 无法在我们协议下跑通。

#### E.2 历史队列（9/7 – 9/10；已完成行留作可追溯记录）

| 序 | 任务 | 前置 | 完成判定 | 状态 | commit |
|---|---|---|---|---|---|
| E1 | 关 Ch2 TacoERE 适配档的账：查清 `taco-s13-r2` 与 `taco-s13-r3` 差异来源 → **预注册**选档规则 → 评分正式档 → 三族官方 F1 写进 `results/PHASE_R1.md` → 更新 `status.json` | 已满足 | 差异有书面解释；选档规则在看分数前写定；结果页与 `status.json` 不再互相矛盾 | done | `91e818e` + `bc6b07e` |
| E2 | 取 LLMERE 官方实现做可运行性核查：冻结 commit/tree hash、核对 MAVEN-ERE 数据接口、base model、显存与是否 LoRA，裁决"能否在我们 2622/291 manifest 与官方 evaluator 下忠实重跑"；**本步不训练** | E1 | 裁决落到 `results/PHASE_R1.md` 第 4 节，并修订该节 Ch2 结论；能跑则排下周训练，不能跑则写明具体阻断点 | done | `8a8ac1a` |
| E3 | T021 Ch2 因果 design brief：写入 LLMERE/TacoERE 对照结构与 CovEReD、SURE-RAG 的一般命题，明确 A4 窄 delta | E2 | 审查 PASS，且推理保持完整候选全集 | done | `d584ca8` |
| E4 | T020 Ch1 因果 design brief：正面处理 ACCI 抢占，核实其论元来源，写清 C5 的窄 delta | 已满足 | 审查 PASS；不使用 MAVEN-ARG cluster gold；不出现"首次"表述 | done | `0210fba` |
| E5 | T023 跨产物一致性审计：实跑 `scripts/audit_r1_consistency.py`，修掉 `status.json` 与结果页的矛盾。**已有两条确凿输入证据**：`design_briefs.json` 与 `literature_matrix.json` 在 2026-09-06 15:27 被改动却没同步 `protocol.json`，哈希已漂移，且 matrix 把 relation/identity 门写成 `pass`（与自身 `global_decision`、`status.json`、结果页、E1 预注册判断四处矛盾），briefs 把三份 brief 全标 `accepted`。**必须先查明 09-06 改动来源，不得先改哈希让审计变绿**；漂移字节已由 E3 存档在 `runs/stages/R1/r1-v61-20260904/audit/design_briefs.drift-20260906T1527.json`，`briefs.relation` 已被 E3 的正式 T021 审查取代、`briefs.identity` 仍是 09-06 原样；详见 `results/PHASE_R1.md` §11 与 §11.1 | E3 + E4 + 已有 T022 | 输出 `cross_artifact_audit.json`；每条需求映射到任务/测试；两条漂移各有裁决 | done | `54a10cf` |
| E9 **（排在 E6 之前）** | 核实 IP&M 2024（Zhang et al., IP&M 61(5) 103811）的口径：取全文对照表，看**它复现的 MAVEN-ERE official joint baseline** 与我们自跑官方码是否对齐（MAQInstruct 判据）。订阅墙走作者主页 / ResearchGate / 机构库 / OpenAlex（作者 Junchi Zhang，dblp `153/2859`） | 已满足 | 三种处置之一落到 `results/PHASE_R1.md` §15.3；**无论结果都不进 roster**；若判定可比则 A4 及格线在 E6 前重估 | done | `03d972a` |
| E10 **（排在 E6 之前）** | ACCI 仓库静态核查（`github.com/era211/ACCI`），**复用 E2 对 LLMERE 的流程，不训练**：有无 trainer / checkpoint / 依赖清单，数据接口能否接我们 2622/291 manifest 与完整候选全集，跨文档→文档内需要哪些适配 | E9 | 裁决落到结果页；能跑则排单卡 seed-13 透明移植，不能跑则写明具体阻断点并按新措辞另议 Ch1 名单 | done | `9b43573` |
| E6 | T024 冻结 C5/A4/D4 phase contract。**A4 契约照常冻结**：roster 里 LLMERE-causal 已被完整指名与规格化，只有数字 pending；pilot 可先跑，确认性 promotion 不可 | E5 + E9 + E10 | 三份契约的输入、baseline、protocol hash、promotion/stop、bundle、GPU 命令齐全并落 hash；A4 的 pending baseline 有可执行规格而不是占位符；**A4 契约已由 E9 解锁、可冻结；C5 因 E10 `not_runnable` 仍缺第二方法族，先由作者另议名单，不得伪冻结**。⚠️ **E5 已查出契约内容本身与裁决矛盾**：A4 契约仍把 taco 适配写成 independent recent family（§13 已否）、C5 契约仍把 Qwen3 档写成 argument-aware strong baseline（§15 已改为负面对照），**必须改内容，不能只补哈希**；D4 契约与 T022 记录一致 | done | `1fcc7db` |
| E7 | 修可追溯性缺口：把 `src/ekg/relations/extractor/supervised.py` 纳入 relation run 的哈希集合（E1 发现：两档携带同一 trainer hash 却构造不同编码器输入）；**并把 `scripts/audit_r1_consistency.py` 纳入 R1 `protocol.json` 的 `code.files`**（E5 发现：同类脚本 `audit_r1_dataset_ids.py` 在集合内，它却不在，导致 T023 审计无法从冻结代码集复现） | E6 | 新增 hash 键不改动任何既有 hash；若动到 trainer 本身则须同时重建 P1 bundle 并重绑 | done | `1c922fd` |
| E8 **（可与 E4–E7 并行）** | LLMERE-causal 透明适配 baseline（`llmere-causal-s13`）：清 B1/B3/B4 → 用未设门镜像取权重并记 SHA-256 → converter **逐字不改**生成 causal 数据 → LoRA SFT → 用**我们冻结的 `evaluate.py`** 打分 → 数字写进 `results/PHASE_R1.md`。**先只跑 causal**（48,365 训练 / 11,149 推理，约 joint 的 1/4）；启动前按 §5 展示命令、cwd 与预期产物 | 已满足（裁决见 §E.1a） | 官方评测器下的 causal P/R/F1 落地；标注**透明适配**、披露 k=30 分区天花板与权重替换；relation 门按 §13 的新措辞判定 | wip（SFT 与 11,149 条 generation 已完成；`372a6e2` 解决 1 条精确重复引用，但全量扫描另有 95 条 malformed 输出，故官方评分不可运行。不得填 NONE、猜引用、只重生成 95 条或拼接；先完成 §E.2a 的恢复方案审查，获得作者明确授权后才能重生成） | `20be231` + `372a6e2` |
| E11 **（2026-09-09 作者授权与 E8 generation 并行）** | D4 typed-cue factuality 的 D4.0 implementation/local gate → D4.1 immutable preflight/baseline replay → D4.2 CPU/CUDA smoke。只在三道门全过且重新核卡后，按冻结 seed-13 命令启动 D4.3；GPU 选择按实时空闲卡，记录实际 `CUDA_VISIBLE_DEVICES`。 | E6/T024 frozen；作者明确授权 D4.0–D4.2 | 实现与 targeted tests、三件套、preflight 的 source/manifest/fold/OOF hash 重验和 smoke 均通过；不读取 final-valid、不改五折 rotation、不启动 seed 17/42。任何一项失败即停止，不占卡重试。 | wip（D4.0 `727ab02` + `310b5be`：factorization、typed-cue sidecar、文档内 permutation、confusion mediator、独立 train/eval/preflight/smoke 入口及 preflight 合同测试已完成；**534 passed / 26 expected skips、ruff 0、smoke OK**。D4.1 未启动；4090 隧道后来恢复，但作者要求先停下准备汇报，故无 preflight/smoke/pilot 产物） | `727ab02` + `310b5be` |

#### E.2a 上一批接续队列（2026-09-10 冻结；已被 §E.2b 取代，留作记录）

| 顺序 | 子任务 | 可否立即执行 | 通过 / 停止条件 |
|---|---|---|---|
| 1 | **E8.1：审查并冻结全量恢复方案**。只读现有 generation、prompt/预测格式、LLMERE 上游能力与当前 converter；提出覆盖全部 11,149 条的统一生成/约束解码和重新评分方案。 | 可以；不使用 GPU、不写 E8 运行产物。 | 通过：完整候选全集、同一规则、原始输出保留、fail-fast 和成本均明确；停止：方案需猜补关系、局部重生成或不能保持同一口径，则将本轮标为不可评分失败。**方案通过不等于获准重生成。** |
| 2 | **E11.1：D4 immutable preflight**。在 4090 以 `.venv/bin/python` 物化 `runs/stages/D4/d4-v61-typed-cues-r1/preflight/`，重验 R1/P1、五折 manifests、source、encoder、accepted OOF baseline 和 code hash。 | 可以；此前作者已授权 D4.0–D4.2；不使用 GPU、不读 final-valid。 | 通过：protocol `status=pass`，独立重算两条 accepted OOF baseline，所有 hash/覆盖/折隔离一致；停止：任何 hash、fold 或 final-valid ledger 不一致，不创建 smoke 或 pilot。 |
| 3 | **E11.2：D4 CPU/CUDA smoke**。仅在 E11.1 PASS 后，重新核卡并先向作者展示准确命令、cwd 与预期产物；在单张真正空闲的 4090 上跑 1 fold、10 个 train-only documents 的 full/remove-core/permutation 三臂。 | 依赖顺序 2；GPU 短任务，须重新核卡。 | 通过：三臂 loss/logits/spans 有限，sidecar/report 完整，evaluation IDs 未入 train/selection；停止：任一检查失败即不启动 pilot。 |
| 4 | **D4.3 seed-13 five-fold pilot**。 | **不可立即执行**；依赖顺序 3 PASS，且需作者在看到 preflight/smoke 结果后再次明确授权长 GPU 任务。 | 只有 author approval 后，按冻结命令、单 seed 13、五折三臂启动；不追加 seed 17/42。 |
| 5 | ~~**C5 第二方法族前置**~~ **（已被 E12 取代，2026-09-11）**：QR-001 v1.1.0 后 baseline 广度不再是准入门，C5 已转 `frozen`，可实现、preflight、smoke 与 pilot。 | ~~仅可做「补前置」~~ | ~~未收到名单时保持 `blocked_pre_admission`~~ |

#### E.2b 当前队列（2026-09-11 冻结，取代 E.2a）

> **本队列已降为 [`EXPERIMENT_PLAN.md`](EXPERIMENT_PLAN.md) 主表的当周切片。**
> 可执行实验只认那份主表；**本表不得出现主表以外的新任务**。要偏离顺序先改主表。

**排序原则**：先跑自己的方法，再补外部对手。E1–E11 十一个任务全部是协议、审计、文献与
baseline，v6.1 三份方法设计**一个都没跑过**；证明方法有没有价值才是实验质量的主要判据，统计门槛是
锦上添花（作者 2026-09-11）。

| 主表 ID | 子任务 | 可否立即执行 |
|---|---|---|
| — | **E12：SPEC v1.1.0 + FR-016 + 三契约重绑** | ✅ **已完成**（`results/PHASE_R1.md` §21） |
| — | **E13：E3 重定向为「事件图谱构建与下游事件预测应用」**（乙形态，作者 2026-09-11 选定）；24 条件 factorial / Holm / frozen-vs-finetuned 全部撤销 | ✅ **已完成**（`phases/PHASE_E3_graph_application.md`） |
| — | **E14：冻结 `EXPERIMENT_PLAN.md` 防漂移主表** | ✅ **已完成** |
| **C-1** | D4.1 immutable preflight | ✅ **done 2026-09-11**（`93f59f1`，见 `results/PHASE_D.md`） |
| **C-2** | EasyECR 可运行性实跑核查（不训练） | ⚠️ **静态部分 done 2026-09-11**（`conditionally_runnable`）；**C-2b 活体 import** 待 4090 隧道恢复 |
| **C-3** | E8.1 LLMERE 恢复方案冻结 | ✅ 纯文档 + 只读 |
| **C-4** | Ch6 对手名册调研与冻结 | ✅ 联网调研 |
| **C-5** | C5.0 实现 + 本地 gate | ⚠️ **核心件 done 2026-09-11**（`role_uncertainty.py` + `role_compatibility` 组件，15 测试，550 passed）；**C-5b 四个入口脚本**待做 |
| **C-6** | A4.0 实现 + 本地 gate | ✅ CPU |
| **C-7** | LLM 对照脚手架 | ✅ CPU |
| **C-8** | 第 2 章统一评测协议素材整理 | ✅ CPU |
| — | **E15：E3 重定向为「乙」形态 + 撤销 factorial** | ✅ **已完成** |
| — | **E16：`EXPERIMENT_PLAN.md` 时间线按项目自身基准率重估**（初版 3 周收口是错的，把 GPU 计算耗时当成了日历时间） | ✅ **已完成** |
| **G-0** | 修复 gpu-4090 驱动 | ✅ **done 2026-09-12** |
| **G-1** | D4.2 smoke | ✅ **done 2026-09-12**（CPU + CUDA 双半边，产物逐字节相同） |
| **C-9** | **写 `scripts/run_d4_typed_cue_oof.py`**（契约点名、仓库里没有） | ✅ CPU，**当前队首** |
| **G-2** | **D4.3 seed-13 五折 pilot** | ❌ 等 **C-9** + 作者授权长任务；4090 四卡可按折并行 |

完整主表（含 G-3…G-12、三个 Gate、GPU 预算与 phase 契约映射）见
[`EXPERIMENT_PLAN.md`](EXPERIMENT_PLAN.md)。

⚠️ **E12 改动了 `runs/` 下的三个 JSON，而 `runs/` 是 gitignored**（产物走 scp）。开工前必须把
`runs/stages/R1/r1-v61-20260904/protocol.json`、`phase_contracts/t024_freeze.json`、
`audit/cross_artifact_audit.json` **双端 SHA-256 同步到 gpu-4090**，否则远端 preflight 会因
契约 hash 不符而 fail-fast。本地值见 `results/PHASE_R1.md` §21.3。

**GPU 恢复后的队首是 D4.3**，不是 preflight 排队——它是唯一实现完成、power 过关、赛道无竞争的一章。
两卡可并行时：卡 A 跑 D4.3，卡 B 跑 A4.3 或 EasyECR 复现（namespace 不重叠）。

**仍打开的裁决**：LLMERE 的 FR-016 保真度路径与 §E.1a 第 6 条冲突，见 `results/PHASE_R1.md` §21.6
与名册 §2.1，建议记 (b) Unverifiable。

#### E.2a 的历史说明

E1 已完成（2026-09-07）：差异来源是 `3f02640` 换掉了 TacoERE 的 KMeans 初始化，全量实测 2,913 篇里
2,743 篇聚类归属改变，**是确定性的代码致输入变化，不是 GPU 非确定性**；旧初始化器还在同进程内对 5 篇
自相矛盾。选档规则在 `taco-s13-r3` 评分**之前**以提交 `91e818e` 预注册（按训练代码身份选，不看分数），
选中 `taco-s13-r3`，其官方三族 F1 为 causal 32.01 / subevent 28.80 / temporal 51.48，causal 未过主锚
33.17。taco 是**透明适配**，不关闭"第二个独立同协议 runnable baseline"门。全部证据见
[`results/PHASE_R1.md` §8](results/PHASE_R1.md)。

E2 已完成（2026-09-07，静态核查，未训练）：LLMERE 冻结在 commit `94d4ef27…a798` / tree `f0fd6928…a06f`，
LICENSE MIT。**E.1 里"官方实现优先于自建 TacoERE 适配"这条判断需要按实测收窄**：该仓库全历史 5 个
commit 只有数据构造、评测器与已发布预测，**没有训练/推理代码、配置、依赖清单、checkpoint，也没有出现
过任何 base model 名称**；训练细节只在论文里（LLaMA-Factory + LoRA r64 + lr 2e-4 + 3 epoch + len 2048 +
单张 A100-40G）。裁决 `conditionally_runnable`：能跑，但跑出来的是**我们对官方方法代码的透明适配**，
和 TacoERE 同类，**不关闭**"第二个独立官方同协议 runnable baseline"门；relation 门维持 `blocked`。
数据接口已实测兼容——用我们 2622/291 manifest 替掉上游的 8:2 随机切分后，四个 converter 与 `merge.py`
**逐字不改**跑通，得到 199,757 条 joint 训练样本与 internal-dev 上 49,156 次推理。四条待清阻断点
（无官方 trainer / Llama-3-8B 权重 gated 且无可用 token / `llamafactory` 未装且不得污染 cu128 `.venv` /
上游评测器不是组织方 `evaluate.py`）与成本估计见 [`results/PHASE_R1.md` §9](results/PHASE_R1.md)。
⚠️ 其发布的 causal 36.04 落在官方 valid 710 篇 + 自写评测器上，**与我们 internal-dev 291 篇的主锚 33.17
差两条轴，不得同表比较**。

E3 已完成（2026-09-07，纯文档与静态核查，未训练、未用 GPU）：T021 关系因果 brief 写入
`design_briefs.json` 的 `briefs.relation`，冻结链是 **逐对反事实证据充分性+必要性 → 跨句 causal 误报数
（注册中介）→ 官方 causal micro-F1**；三臂为 full / remove-core（关掉证据选择与两次反事实前向）/
`taco-s13-r3` cluster-context，负控是**等长非证据句替换**且必须抹掉中介改善。护栏含**完整候选全集不得被
弃答或检索裁剪**与 causal recall 不得低于主锚自身的 32.05。四条已被占的一般命题（TacoERE 上下文重构 ·
LLMERE 生成式范式 · CovEReD 反事实数据集 · SURE-RAG 选择性弃答）逐条写进 brief，窄 delta 定义为它们的
**交集**而非任一部件，**不写「首次」**。审查结论 **PASS（仅设计轴）**。
⚠️ **留给作者的决定**：QR-001 要求"主锚 + 另一个强的不同方法族"，而 `taco-s13-r3`（32.01）**低于主锚
33.17** 且是我们自己的透明适配，赢它由赢主锚蕴含。T024 冻结 A4 契约前必须二选一——(a) 接受"主锚 + 透明
适配"并在每张表披露 fidelity 缺口，或 (b) 清掉 LLMERE 的 B1–B4 后排训练（4090 整机数天 + 一个 Meta 许可
决定）。在决定前 relation baseline 门维持 `blocked`。
📎 **取证**：E3 写 `design_briefs.json` 前先把 09-06 的漂移字节原样存档为
`runs/stages/R1/r1-v61-20260904/audit/design_briefs.drift-20260906T1527.json`（`d5d6a61c…7986`，mtime 保留），
只重写 `briefs.relation` 一个子树，`protocol.json` **未**重冻结——E5 的漂移裁决不受影响。
全部证据见 [`results/PHASE_R1.md` §11.1/§12](results/PHASE_R1.md)。

E4 已完成（2026-09-07，纯文档与静态核查，未训练、未用 GPU）：T020 身份因果 brief 写入
`design_briefs.json` 的 `briefs.identity`（`81ad43a3…a382` → `cd40e664…4366`；兄弟子树与顶层字段逐字节未动，
`protocol.json` 仍未重冻结）。冻结链是 **mention-local 预测角色后验 + 显式缺失状态 → 高相似度误合并数
（注册中介）→ 官方 MUC F1**；三臂为 full / remove-core（detach 角色残差）/ `qwen3-argument-s13-r2`，
负控是**类型内角色后验置换**且必须抹掉中介改善。护栏含 **MUC recall 不得低于主锚自身 83.246073**、
B³ ≥ 97.04 / CEAF-e ≥ 96.73 / BLANC ≥ 88.88、四态抽取状态无静默默认、gold 论元与 gold identity 只作
标注过的 oracle、`EventNode` 零新增字段。
**ACCI 的论元来源已按要求核实（一手全文）**：它**根本不抽论元**——用 masking 把输入切成 trigger 子序列与
其补集 `X_arg = X \ X_trg`，没有角色类型、没有逐角色后验、也没有缺失状态；且是跨文档 ECB+/GVC、
候选对在 subtopic 内检索。所以答案既不是 gold 也不是 predicted，这一条必须写进论文的对照叙述。
另检出一条**更贴近的抢占**：IP&M 2024 `A graph propagation model with rich event structures`（Zhang et al.,
61(5) 103811）用 AMR 跨句隐式论元做 MAVEN-ERE 联合抽取，报 **MUC 86.1 / causal 37.4**，
但**无公开代码且 split/评测器未核实**，只作 context、**不得同表比较**；它对 Ch2 同样有影响，已登记为 E5 的待办。
四条已被占的一般命题（ACCI · IP&M 2024 · CorefPrompt · HGCN-ECR）逐条写进 brief，窄 delta 定义为它们的
**交集**，**不写「首次」**。审查结论 **PASS（仅设计轴）**。
⚠️ E4 留下的两个问题**已于同日由作者裁决**，见 [§E.1b](#e1b-作者裁决2026-09-07ch1-门同样重新界定ipm-口径核实前置到-e6-之前)
与 [`results/PHASE_R1.md` §15](results/PHASE_R1.md)：Ch1 门按四条新措辞重新界定、ACCI 移植改为
**先静态核查（E10）再谈训练**、`qwen3-argument-s13-r2` 重定义为注册负面对照、IP&M 口径核实（E9）
前置到 E6 之前。identity brief 的 roster / promotion / open_finding 已按裁决修订，
原文逐字保留在 `amendments[0]`（`cd40e664…4366` → `2220b86c…1999`），因果链、中介、三臂、负控、
护栏与 stop **未动**。全部证据见 [`results/PHASE_R1.md` §14/§15](results/PHASE_R1.md)。

E5 已完成（2026-09-07，纯文档与静态审计，未训练、未用 GPU）：`cross_artifact_audit.json` 已落地，
**审计 `pass`、`findings` 为 0**，SPEC 声明 35 条需求全部映射到任务与契约，六个 R1 产物身份全部 `frozen`，
三份 method phase 契约为 `pending_t024`（**预期状态**），P1 r15 与 A3 r17 信任根逐位一致。
**R1 仍未 PASS**——报告的 `r1_pass_blockers` 列出四条（status 非 pass + 三份契约待 T024）。
1. **先修了一个使 T023 无法在自己时点运行的循环依赖**：`audit_r1_consistency.py` 要求 `T023` 已打勾才继续，
   等于把这次审计写成它自己的前置，且第一个失败即 `raise`，永远产不出"列全问题"的报告。前置改为
   `TASKS.md` 实际声明的 **T012–T022**，findings 改为收集式，`pending_t024` 不再算不一致。
2. **09-06 漂移已溯源，证据是决定性的**：15:27 的改动属于 15:35 提交 `f6966a0` 的同一次会话，
   而该提交自己的正文只关闭 Ch1 的 **input/baseline blocker**、并明写 Ch2 仍缺第二 baseline。
   所以 identity 半是**把 blocker 关闭过度解读成审查通过**，relation 半**没有任何提交正文支持**且与同一提交矛盾；
   `literature_matrix.json` 的 `audit_date` 至今仍是 09-04，是"改了内容没重跑审计"的旁证。
3. **两条漂移走了不同的路**：`design_briefs.json` **原样重冻结**（磁盘字节已是 E3/E4 两次正式审查的产物，
   factuality 子树逐条比对 T022 记录一致）；`literature_matrix.json` **先把两个 `baseline_gate` 从 `pass`
   改回 `blocked` 再重冻结**，原值保留在其 `amendments[0]`，`methods` 与 `upstream_checkouts` 逐字节未动。
   `protocol.json` **最后**才重冻结（`fed98d2a…f619fc` → `497aae22…423155`）。**顺序就是要点：
   先溯源 → 再纠正内容 → 最后动哈希**，没有为让审计变绿而先改哈希。
4. ⚠️ **给 E6 的硬输入**：脚本不读契约内容，人工核对查出 **A4 与 C5 两份契约的 roster 与 §13/§15 裁决矛盾**，
   E6 必须改内容而不是只补哈希；D4 契约与 T022 记录一致。
5. 📌 **给 E7 的新缺口**：`scripts/audit_r1_consistency.py` 不在 `protocol.json` 的 `code.files` 里，
   而同类的 `audit_r1_dataset_ids.py` 在，本次审计因此无法从冻结代码集复现。本轮**不顺手修**，并入 E7。
全部证据见 [`results/PHASE_R1.md` §16](results/PHASE_R1.md)。

E9 已完成（2026-09-07，纯文献核实，未训练、未用 GPU）：**全文拿不到**——OpenAlex `oa_status = closed`
且无 repository 全文、Semantic Scholar `openAccessPdf = CLOSED`、无 preprint、12 篇引用文献（取回 10 条）
无一开放获取。预注册判据的原始形式（读它自己的对照表）**无法执行**，改用**等价路径**：
拿 MAVEN-ERE 官方论文（arXiv `2211.07342v1` Table 7/8，RoBERTa-base，5 次试验均值，官方 test）
与我们的主锚对照——**共指四指标全部在 ±0.4 内**（MUC 80.98 vs 82.1、B³ 98.04 vs 98.2、
CEAF-e 97.73 vs 97.9、BLANC 89.88 vs 90.2），causal 33.17 vs 31.5、subevent 29.75 vs 27.5 我们更高，
temporal 51.63 vs 56.0 低 4.4（方向与 `PHASE_A.md` 已记录的 TIMEX 头缺口一致，但**未做隔离实验，不作结论**）。
**结论：我们的官方 joint 复现忠实于官方发表口径。**
⚠️ **同时修正一处此前的推断**：§15.3 写「86.1 几乎必然含口径成分」是**不对的**——那里拿来比的 77.47 是
Phase A **我们自己的方法档**在 710 valid 上的分数，不是官方 joint 复现，混用它是错的。正确对照是官方
+joint 的 **82.1**，IP&M 高 **4.0**；causal +5.9、temporal +4.7、subevent +5.4，**四族齐涨 4–6 点**，
模式内部一致，**更像真实增益而非口径差**。未确证的仍有一环：它用 test 还是 valid、是否用组织方 `evaluate.py`。
✅ **对 E6 不阻塞，A4 契约可照常冻结**：它无公开代码 ⇒ 无法在冻结协议下运行 ⇒ 按 FR-006 进不了 roster；
A4 的及格线定义在**我们协议内的主锚与第二方法族**上，它改不了这条线；披露义务已由 §17 落地。
📌 它此前**根本不在** `literature_matrix.json` 里（与 E.1 的 LLMERE 漏收同类），已补两条 `no_public_code`
条目进 identity 与 relation 两章，**只追加不改既有条目**，随后按 E5 的顺序重冻结哈希。
全部证据见 [`results/PHASE_R1.md` §17](results/PHASE_R1.md)。

E10 已完成（2026-09-07，静态核查，未训练、未推理、未用 GPU）：ACCI 官方仓库冻结在 commit
`7f5bcd81…23fa` / tree `d4c8aa14…fe43`，全历史仅一个 commit、tree 仅一个 `README.md`，无 LICENSE、
release、trainer、推理入口、模型、checkpoint、配置、依赖、dataset reader、candidate builder 或 evaluator。
因此裁决 **`not_runnable`**：从论文散文重建会是我们新写的实现，不能叫官方复现或透明移植，故不排
single-card seed-13。冻结 MAVEN-ERE 输入的 2,622/291 manifest 全量 probe 验证 66,744/7,195 mention 可构造
`<m> trigger </m>` 输入、完整文档内候选对为 1,148,762/117,435；这只证明本地数据足供另写 adapter，
不构成对不存在上游接口的兼容。Ch1 第二方法族门保持 `blocked`，下一候选名单需作者按 §E.1b 四条措辞另议。
完整产物、hash 与裁决见 [`results/PHASE_R1.md` §18](results/PHASE_R1.md)。

E6 已完成（2026-09-07，T024 契约冻结，未实现、未训练、未推理、未用 GPU）：先改契约内容、再绑定 hash，
没有为使审计变绿而只补 hash。A4 的 `taco-s13-r3` 已降回固定透明适配对照，`llmere-causal-s13` 以
upstream / unmodified converter / causal-only 48,365 train + 11,149 internal-dev generations / LoRA 配方 /
frozen `evaluate.py` 完整规格化为 metrics-pending 的确认性 baseline；A4 seed-13 只在 A4.0–A4.2、local gate
与重新核卡后可跑，确认性 promotion 必须等待并超过 LLMERE（⚠️ **这一句已被 E12 取代，2026-09-11**：
确认性 promotion 不再以「等到 LLMERE 数字」为前置，见 `results/PHASE_R1.md` §21）。D4 与 T022 记录一致，冻结其 five-fold OOF
契约。C5 因 ACCI `not_runnable`、IP&M 无公开代码且无作者指定替代家族，记录为
`blocked_pre_admission`，**没有**将草案 hash 当作 phase contract binding；Qwen3 已改为注册负面对照，
非 roster 的 annealed-local-pair / hard-argument 臂已移除。R1 protocol SHA-256
`2fde1577c92d826d0ee12e722e6183b92421477ea38769e15144cdaa300c7094`，T024 artifact SHA-256
`3b44a2e2fdf402bfa55492d6527e642a7f75bb9301ad1c1e4098477ec7edd81b`；交叉审计 `pass`、0 findings、35/35
requirements mapped，A4/D4 `frozen`、C5 `blocked_pre_admission`。审计脚本现在明确区分该状态和
`pending_t024`，其自身 hash 仍由紧接的 E7 纳入冻结代码集。全部证据见
[`results/PHASE_R1.md` §19](results/PHASE_R1.md)。

E7 已完成（2026-09-07，可追溯性修复，未改 trainer、未重训、未评分、未用 GPU）：不把 r3 的源码身份
错误回填给 r2。`taco-s13-r2` 的 `supervised.py` 绑定训练提交 `d8fcd30` 的
`ffb40460…a1a25`，`taco-s13-r3` 绑定训练提交 `e796182` / 当前源码的 `9cdf54a…7ab7c`；两档只新增
`protocol_binding.hashes.supervised_extractor`，原 trainer `5c513bdb…d0f2c6`、checkpoint、预测和指标 hash
未动。对账 artifact `code_hash_reconciliation.json`（SHA-256 `833b3c4d…c5ebd`）已进入 R1 artifacts，审计会
重算两份 metadata digest 与该键。`audit_r1_consistency.py` 以 `f6fdc099…eef90` 加入 `code.files`，并自检其
自身 hash；后续脚本/metadata 漂移都会生成 finding。R1 protocol SHA-256
`199852a1f0b81e088f7568d9462d9fe226db15bdd21a78346b6d03bef80cf058`；审计 `pass`、0 findings、35/35
requirements mapped。P1 r15/A3 r17 不需重绑，R1 唯一余项仍是 C5 `blocked_pre_admission`。全部证据见
[`results/PHASE_R1.md` §20](results/PHASE_R1.md)。

E8 已于 2026-09-07 启动（仍在运行，**尚无指标或结论**）：首次任务 PID `1516155` 在独立
`.venv-llmere-causal-s13` 安装 CUDA PyTorch 时失败，日志是 `OSError: [Errno 28] No space left on device`。
只读诊断确认根分区 `/` 仅余 2.3GB（96%），而 `/data` 有 29TB 可用且 inode 充足；GPU0 当时仅驱动占用，
故这是 pip 默认 `/tmp` 临时目录的环境错误，不是 GPU、模型、数据或训练错误。未进入 LoRA SFT、未访问
final-valid、未产生预测/指标。修复提交 `b8b2352` 使 launcher 将 `TMPDIR` 与 `PIP_CACHE_DIR` 固定到
`/data/TJK/ekg/.tmp/llmere-causal-s13` 与 `/data/TJK/ekg/.cache/pip/llmere-causal-s13`，项目 `.venv` 未动。
在核实失败残留仅为 22MB 专用 venv 与 4KB 空 run root 后，删除这两个**确切的 E8 专用路径**，不触及数据、
既有 run 或 checkpoint；随后重新核卡、同步 `b8b2352` 并以 GPU0 PID `1518478` 重启唯一后台任务。命令的 cwd
是 `/data/TJK/ekg`，实际 launcher 是 `bash scripts/run_llmere_causal_adapter.sh /data/TJK/ekg 0`，其外层使用
`setsid nohup`、独立日志 `logs/llmere-causal-s13.log` 与 `PYTHONUNBUFFERED=1`。run root 是
`runs/stages/R1/r1-v61-20260904/baselines/relation/llmere-causal-s13/`；checkpoint/权重留在 4090，完成后只同步
generated/official predictions、metrics、metadata 和小型转换报告并做双端 SHA-256。重试启动后 PID ALIVE，
专用 tmp/cache 已写入 `/data` 且日志无 error；B3 仍在进行，不能把安装日志写成实验结果。任何完成、失败或
ssh 失败都按 §5 三态规则处理，并在本行和 `results/PHASE_R1.md` 如实回填。

重试 PID `1518478` 已成功安装 CUDA PyTorch（`.venv-llmere-causal-s13` 约 6.5GB，专用 pip cache 约 3.7GB），
但随后从 `https://github.com/hiyouga/LLaMA-Factory.git` 克隆固定 `v0.9.3` 时遇到
`GnuTLS recv error (-110): The TLS connection was non-properly terminated`，进程 GONE。该失败发生在模型下载、
converter、LoRA SFT 与评分之前，故没有实验产物。直接 HTTP/1.1 identity probe 在 30 秒内未完成；已验证
`https://gh-proxy.com/https://github.com/hiyouga/LLaMA-Factory.git` 的 `v0.9.3` tag 是预期
`ca75f1edf3cb50343ed1c98605141c3e22075b5f`。修复提交 `749d9b7` 使用此可访问源的**浅克隆**，仍 fail-fast
逐位检查该 commit；保留已验证的独立 CUDA 环境/cache，删除第二次失败的 run root 与 4KB tmp（无 model、
checkpoint 或结果），并在 final metadata 中新增 factory origin、commit、tree 与 dirty-state 记录。新任务 PID
`1534100` 已成功 clone 到该固定 detached commit，当前在独立 venv 安装 LLaMA-Factory，GPU0 仍无训练负载且
日志无 error。

PID `1540062` 随后完成固定 LLaMA-Factory 安装，并以 `https://hf-mirror.com` 下载
`NousResearch/Meta-Llama-3-8B@315b20096dc791d381d514deb5f8bd9c8d6d3061` 的全部 14 个文件（四个
`.safetensors` 分片合计约 15GB）。镜像底层 Xet 两个分片曾 read timeout，但 downloader 自动续传且最终
打印成功；这不是训练完成。接着 `prepare_llmere_causal_adapter.py` 因 4090 缺少
`runs/stages/R1/r1-v61-20260904/protocol.json` 而 fail-fast，进程 GONE；远端 P1 r15 协议仍为预期
`1e31a9ac…f9655`。因此尚未 clone LLMERE、运行 converter、进行 LoRA SFT、生成预测或计算指标，GPU0–3
均空闲。保留已验证的权重、专用环境、LLaMA-Factory 与 `base_model.json`，不重下也不删除。

恢复提交 `0c07ba5` 新增只接续该精确状态的脚本：它先验证上述已有目录、固定 LLaMA-Factory commit/洁净状态，
并拒绝覆盖任何 LLMERE checkout、train、predict 或 score 半成品；同时把 LLMERE 拉取改走已验证的
`gh-proxy` transport，但仍对 canonical URL 的固定 commit `94d4ef27…a798` 与 tree `f0fd6928…a06f` fail-fast
核对、并将二者写入 metadata。下一步仅同步本地已冻结的 8.7KB R1 protocol，双端 SHA-256 必须为
`199852a1f0b81e088f7568d9462d9fe226db15bdd21a78346b6d03bef80cf058`；通过后才以 GPU0 的后台续跑命令进入
converter 与单 seed-13 SFT。

该 R1 protocol 已于 2026-09-07 以 `scp` 传至 4090，双端 SHA-256 都是
`199852a1f0b81e088f7568d9462d9fe226db15bdd21a78346b6d03bef80cf058`；权重和 checkpoint 没有跨机移动。
续跑 PID `1566260` 先通过已有环境/权重/固定 LLaMA-Factory/无下游半成品的断点检查，随后经代理 clone
LLMERE 并核对到预期 `94d4ef27…a798`，split builder 生成 train/valid/test 为 2,622/291/291，未改动的
converter 已生成 48,365 train 行。它现在实际在 GPU0 运行单 seed-13 LoRA SFT（3 epoch、batch 1、累积 8、
18,138 steps，初始化时占约 16.5GiB）；GPU1–3 空闲。该记录只说明训练已开始，**不是指标、结果或门通过**；
训练完成后仍须生成 11,149 条 internal-dev 输出、严格转换、冻结 evaluator 评分和 metadata hash 才能回填结果页。

SFT 在 2026-09-08 13:37 成功走完 18,138/18,138 steps（3 epoch；`train_results.json` 的
`train_runtime=59233.9803`、`train_loss=0.25147225742685003`），最终 LoRA adapter
`train/adapter/adapter_model.safetensors` 为 671,149,168 bytes，final checkpoint 与 train metadata 均保留
在 4090。之后调用预测配置前，LLaMA-Factory 的依赖检查报
`PackageNotFoundError: ... jieba ... is required by this application`，进程 GONE；没有 `predict/` 或 `score/`
目录、生成预测或官方指标，因此 SFT 的训练 loss **不是**项目实验结果、不得写入结果页或作为门判断。

恢复提交 `b3615ee` 将缺失依赖固定为 `jieba==0.42.1`，并新增 prediction-only 续跑脚本。它验证 SFT 已完整
结束、adapter/metadata 均非空、LLMERE converter 的当前 SHA-256 仍等于准备时记录值、factory 与 upstream 的
固定 commit/tree 身份一致，且拒绝覆盖 `predict/` 与 `score/`；然后才安装该固定依赖并运行 prediction、严格
转换、冻结 `evaluate.py` 评分和最终 hash metadata。它不调用 SFT，所以不会重跑已完成的 16 小时训练。

第一次 prediction-only 续跑成功安装 `jieba==0.42.1`，但 LLaMA-Factory 随后按同一
`predict_with_generate` 的预检报缺 `nltk`，进程 GONE、GPU 未实际使用。查固定 `v0.9.3` 的
`hparams/parser.py` 与 `setup.py` 后确认，这个分支无条件要求整个 metrics extra：`jieba`、`nltk`、
`rouge-chinese`；此前的 `[torch]` 安装不含这三个包。恢复提交 `20be231` 将三项显式固定为
`jieba==0.42.1`、`nltk==3.9.1`、`rouge-chinese==1.0.3`，并在续跑前逐项 import 与版本核验。
这次修复仍只影响环境可追溯性，不触及既有 SFT adapter、上游 converter、预测/评分口径或 seed；完成后才以
GPU0 再启动 prediction-only 续跑。

完整 metrics extras 经重启前逐项 import/version 核验后，PID `1819697` 在 GPU0 成功加载 Llama-3-8B 与
`train/adapter`，并进入 11,149 条 internal-dev generation（batch size 1）。首次运行观察约 444/11,149 条、
约 13.5 秒/条，日志估计剩余约 39 小时；GPU0 约 77% / 17.8GiB，GPU1–3 空闲。LLaMA-Factory 的
`save_predictions` 会在 `trainer.predict` 结束后一次性写 `predict/generated_predictions.jsonl`，所以此阶段文件
尚未出现不表示停滞。当前没有 error、尚无任何可报告的 causal P/R/F1；generation 完成后才依序执行严格转换、
冻结 evaluator 评分和 final metadata。

2026-09-10 状态更新：E8 已完成 11,149/11,149 generation，`generated_predictions.jsonl`（59,336,796 bytes）
与 adapter 均留在原 4090 run root；成功 SSH 读取到外层/预测进程均 GONE、GPU0–3 空闲。`372a6e2` 的转换器
将第 107 条的精确重复合法 `PRECONDITION` 引用归并为一个 relation-set 成员，定向测试及本地三件套均通过
（534 passed / 26 skipped、ruff 0、smoke OK）。但同步到 4090 后的全量验证还发现 95 条不可无歧义解析的输出：
第 7,817 条 1 条，以及第 8,842–8,935 条连续 94 条（同一 47-event 文档的两个分区）。它们缺失标签、断裂事件
标记或混入自由文本；不得补 NONE、猜 event id 或局部重生成/拼接。固定 tokenizer 实测所有保存 prompt 均为
286–2,015 tokens、没有一条超过 2048，因此不能把根因臆断为截断。尚未生成 `score/official_predictions.jsonl`、
官方 metrics 或 final metadata，故**没有可报告的 causal P/R/F1**。完整失败记录与有效性边界见
[`results/PHASE_R1.md` §9.6](results/PHASE_R1.md#96-e8--llmere-causal-s13-生成输出有效性失败2026-09-10)。
要重取该 baseline 数字，必须先冻结一个完整、统一的推理/约束解码方案并取得作者授权，再重生成全 11,149 条；
不重训 LoRA adapter。

#### E.3 GPU 使用：按需求，不为占卡而占卡

本周真实 GPU 需求只有 E1 的一次评分（已于 2026-09-07 在 4090 GPU1 跑完，约 1 分钟）。E2 只做静态核查
不训练，E3（已完成，未用 GPU）–E7 全是文档与审计。
卡是公用资源，不得为了"看起来在跑"启动无准入的训练；但**卡空着也不要串行**。

**已排期的两笔真实 GPU 需求**（作者 2026-09-07 已同意，见 §E.1a）：

1. **E8 · LLMERE-causal**：现在就可以排，不必等 E4–E7。缩小到 causal-only 后约为原估计的 1/4，
   仍是 4090 上的长任务；`setsid nohup` + `python -u` + 独立日志，一条 ssh 只发一个后台任务，
   启动前按 §5 展示完整命令、cwd 与预期产物。权重走未设门镜像并记 SHA-256，**不必等 Meta 许可**。
2. **T024 放行后的第一个 seed-13 pilot**（按 E.1 的证据优先 D4）：只吃一张卡，与 E8 **并行**，
   不互相排队。

**Ch1 的 ACCI GPU 需求已取消**：E10 已判定其公开仓库 `not_runnable`；不得从论文散文重建后把它称作
透明移植。只有作者冻结一个满足 §E.1b 四条件的新名单后，才重新评估 Ch1 的 GPU 需要。

**5090 的新授权（作者 2026-09-11）**：4090 不可达期间，5090 可用于**临时性 GPU 任务**
（smoke、小规模 preflight、短时诊断），**主体实验仍回 4090**。
硬边界：**EasyECR 跑不了**（其栈 `torch==2.0.1` 不支持 Blackwell sm_120）；
**Qwen3-8B LoRA 装不下**（卡上既有服务约 17 GB，余量约 15 GB，8B bf16 需约 16 GB）；
**长任务 pilot 一律不放 5090**。每次使用仍须逐次取得作者授权；既有服务不得触碰。
完整边界见 [`EXPERIMENT_PLAN.md`](EXPERIMENT_PLAN.md) §3.5。多种子始终另行授权。

## 4. R1 后的候选方向：不是固定答案

以下只用于指导 R1 反证与对照设计，不能绕过 R1 直接实现：

- **Ch1/C5**：mention-local predicted argument-role posterior + uncertainty-gated clustering；gold event-level
  arguments 仅作 oracle；
- **Ch2/A4**：完整候选全集上的 pair evidence + sufficiency/abstention risk；retrieval/hard negatives 只能
  改变训练/evidence，不能裁评测候选；
- **Ch3/D4**：typed cue spans + known/unknown → modality → polarity；五类 macro-F1 仍是主门；
- **Ch4/E3**：三类真实上游的同实例 factorial；固定 queries/candidates/checkpoint，验证消费者预测有效性
  与图依赖后再解释主效应和交互。

R1 若证明上述候选与近期工作重复、数据不支持、功效不足或中介不可识别，应提出实质不同且更简单的
候选，并在 `RESEARCH_PLAN.md` 版本化记录。不要为了维护 v6.1 名称而维护错误方法。

## 5. 永久红线与服务器规则

- final-valid 不参与结构、超参、threshold、epoch、stop 或 claim 选择；历史访问继续披露；
- manifest、候选全集、evaluator、输入前提、TIMEX 开关必须成对一致；
- Ch1–Ch3 必须在统一公开主指标上超过主锚和另一强方法族，并通过 matched seeds、document-cluster
  paired CI、guardrails、核心消融和负控；辅助指标不能替代；
- oracle 明确标 non-deployable；缺 ID、未知端点、schema/hash 漂移立即 fail-fast；
- 数字下降、零结果、SSH/工具失败均如实记录；
- 本地禁止 GPU；4090 长任务启动前展示命令/cwd/产物；5090 每次单独取得授权；
- 服务器只用 `.venv/bin/python`，不得 `uv run`/`uv sync`；
- 不运行 `rsync --delete`、远端 `git clean -fdx`，不宽目录递归删除；
- checkpoint 训在哪留在哪；跨机搬运先问作者并做双端 SHA-256；
- 一条 SSH 只启动一个后台任务；长任务使用 `setsid nohup`、`python -u` 和独立日志；
- 改代码后必须运行 `uv run pytest`、`uv run ruff check src tests scripts`、`uv run ekg-smoke`。

## 6. 完成、回填与交接程序

一项任务走完下面五步才算完成；缺任何一步，下一个窗口都不得开工。

1. **产物落地**：命令、日志与 artifact 落到 `runs/stages/<PHASE>/<run root>/`；跨机产物双端 SHA-256 一致。
2. **写结果页**：数字只写进对应的 `results/PHASE_*.md`，升降如实、失败如实；其他文档只引用不复制。
3. **回填队列**：把任务 E.2 表里该行 `状态` 改成 `done`，`commit` 填短 hash；没做完改 `wip`
   并在该行写清卡在哪条证据上，不留只有自己知道的上下文。
4. **推进队列**：确认下一行前置已满足。**整条队列清空时**，由本次持有者按 §3 依赖图和
   [`TASKS.md`](TASKS.md) 生成下一批 E 队列写进本表，**先写表再开工**，并同步更新顶部当前阶段卡片。
5. **提交并推送**：按逻辑单元 commit，`git push origin main`。**没 push 就没交接。**

最终回复用这六行，不写长篇叙事：

```text
完成：<E 队列序号 / task ID>
身份：<commit / protocol hash / bundle ID>
验证：<实际命令与 PASS/FAIL>
结果：<只引用 docs/results/PHASE_*.md 位置>
状态：done | wip | blocked；原因
下一步：<E 队列里下一个 todo；是否需要 GPU / 多种子 / 作者授权>
```

长 GPU 任务启动前，仍须按 §5 向作者展示完整命令、cwd 与预期产物；5090 每次单独取得授权。
