# 交接文档 · 新窗口从这里开始

> 更新于 **2026-09-04**。本文是新窗口唯一必读入口；读完后再按本文链接打开所需文件，不回溯聊天记录。
> 本文只记录状态、决策、依赖与下一步，不复制实验表格。实验数字只认
> [`results/`](results/README.md)。

## 0. 接手后先做什么

先执行只读检查：

```bash
cd /home/tjk/myProjects/masterProjects/ekg
git status -sb
git log -3 --oneline --decorate
git merge-base --is-ancestor 23b4fad HEAD
```

预期：本地 `main` 与 `origin/main` 同步、工作树干净，协议代码提交 `23b4fad` 是当前 HEAD 的祖先。
若工作树出现未说明改动，先查来源，不覆盖、不清理。随后只需按任务读取：

1. 当前执行状态：[`TODO.md`](TODO.md)；
2. 可执行任务与依赖：[`TASKS.md`](TASKS.md)；
3. 当前确认性实验：[`phases/PHASE_A3_relation_balanced.md`](phases/PHASE_A3_relation_balanced.md)；
4. 可并行的研究设计准备：
   [`phases/PHASE_R1_method_design_freeze.md`](phases/PHASE_R1_method_design_freeze.md)。

不要先重读整个仓库，也不要直接进入旧 D3/C4。

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
  `4e893c1 docs(r1): record method design gate evidence`；
- 两个提交均已推送 `origin/main`；本文提交后以新的 `origin/main` HEAD 为准；
- 最新本地验证：481 passed / 24 expected skips，ruff 0，`ekg-smoke` OK，P1 local gate PASS；
- local gate 的 `tested_tree_sha256`：
  `3bff2ac2b5366ed06ebe81c9b2e549f0949216c832ad8e6098a6782e0c701d3c`；
- A3.6 仍只运行已授权 seed 13；R1 功效只读 train-derived internal-dev。跨数据 ID 审计按合同读取了
  public-valid 结构字段但未计算关系/事实性指标，访问已在 ledger 披露；没有搬运 checkpoint。

## 2. 已经成立和不得改写的事实

只从下列结果文档取精确数字：

| 主题 | 权威入口 | 当前结论 |
|---|---|---|
| Ch2 工作点与检索 | [`results/PHASE_A.md`](results/PHASE_A.md) | 工作点两个核心周期已用完；近似 retriever 三条均未过门；prototype/ATLoss 已封存 |
| Ch1 历史方法 | [`results/PHASE_C.md`](results/PHASE_C.md) | 旧方法未稳定胜出；event-level gold argument 只能作泄漏型 oracle |
| Ch3 历史方法 | [`results/PHASE_D.md`](results/PHASE_D.md) | 与强 baseline 未统计分开；gold evidence 不支持“只换 locator”作为主要解法 |
| Ch4 历史系统证据 | [`results/PHASE_E.md`](results/PHASE_E.md) | 图依赖正控与部分构建损失成立；正式同实例 factorial 尚未完成 |
| P1 历史可信根 | [`results/PHASE_P1.md`](results/PHASE_P1.md) | r12 是旧 A3 正式结果的可信根；本轮代码变化要求创建新可信根 |

当前确认性实验仍是 A3.6 **官方训练配方分账**。它只分解 rates、coref auxiliary、per-family checkpoint
selection 三个复现变量，不是论文创新。无论分账结果如何，A3 旧方法身份保持 `failed`，之后由 R1
决定新的 Ch2 方法家族。

禁止：第三个工作点、第四个近似 retriever、继续 prototype/ATLoss、把 r13 已观察到的 by-family 曲线
回收成第 4 臂、用更大 backbone 或换 split 救旧机制。

## 3. 后续任务：按依赖执行

当前依赖图：

```text
本地新 P1 trust root ─→ A3.6 四臂 ─→ A3 failed handoff ─┐
R1 无依赖准备任务 ─────────────────────────────────────┴→ R1 promotion
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

### 任务 B：R1 准备工作（可与任务 A/A3.6 并行，默认 CPU）

T012–T017、T019 已于 2026-09-04 完成，精确数字、hash 和裁决见
[`results/PHASE_R1.md`](results/PHASE_R1.md)，产物根为 `runs/stages/R1/r1-v61-20260904/`，代码提交
`8e3eb7a`。当前硬结论：ERE↔FACT 身份闭环；ERE↔ARG mention 仅约 95.4% 覆盖且共享 mention 有父簇
冲突，故 event-level arguments→mention 的 deployable 路线 blocked；Ch1 prospective power PASS，但缺
argument-aware 同协议 runnable baseline；Ch3 的 291-document 五类 macro-F1 设计 underpowered，必须先
冻结 repeated-split/cross-validation 补强；Ch2 T018 等 A3 handoff。

学位类型、入学年份、学科与专业未知项均保持 `null`；同济校级标准来源/date/hash 已冻结，未知项不影响
项目自定的更高科研硬门。文献矩阵已只读冻结 CorefPrompt、MAVEN-FACT、ModaFact 三个官方仓库 HEAD，
但没有把不同数据/split/evaluator 的代码误记为同协议 baseline。三个 design brief 均为 blocked/draft，
**未放行 proposed GPU 训练**。

5090 已同步到 `4e893c1`，上述 R1 JSON 与小型逐实例 anchor 已用不带 `--delete` 的 rsync 复制，双端逐文件
SHA-256 完全一致；既有 Qwen rerank/embed 服务保持运行，未启动 GPU 任务。

按 [`TASKS.md`](TASKS.md) 的 T012–T019 执行，但只做不读取 A3 待出结果的部分：

1. 记录学位类型、入学年份、学科标准；不知道的字段写 `null`，不猜；
2. 为 Ch1/Ch2/Ch3 建一手论文与官方代码矩阵，明确 split、候选全集、evaluator、输入前提和代码 fidelity；
3. 审计 MAVEN-ERE/ARG/FACT 的 doc/event/mention/offset/role 对齐；缺失或歧义 fail-fast；
4. 用冻结逐文档 anchor 输出做 Ch1/Ch3 前瞻性 MDE/power；Ch2 最终分析等待 A3 handoff；
5. 不写 proposed 训练代码，不看 final-valid，不把论文不同 split 数字放进本地主表。

产物进入 `runs/stages/R1/r1-v61-20260904/`，结构与完成门以
[`PHASE_R1_method_design_freeze.md`](phases/PHASE_R1_method_design_freeze.md) 为准。R1 准备可以部分完成，
但不能在 A3 handoff 和跨产物一致性审计前标 PASS。

### 任务 C：同步 4090 并执行已冻结 A3.6 四臂（运行中）

上次观测 4090 可连、worktree clean、四卡空闲，但这是历史快照，开跑前必须重新检查：

```bash
ssh gpu-4090 'cd /data/TJK/ekg && git status --short && git branch --show-current && git rev-parse HEAD && nvidia-smi --query-gpu=index,name,memory.used,utilization.gpu --format=csv,noheader'
```

只有远端 `main` 且 worktree clean 时才同步：

```bash
ssh gpu-4090 'cd /data/TJK/ekg && git fetch origin main && git reset --hard origin/main'
```

T008 已物化四臂 execution plan：

- preflight：`runs/stages/A3/a3-v6-recipe-accounting-r16/preflight/`；
- base plan SHA-256：`ea377af87afa37fac86d267501c0c8c6a9bb97cd7b8614d4fb875a0e8fce5a82`；
- recipe plan SHA-256：`3f2f385dbf010e33ad67c9c24ba8aafaadce01000108655f53258b971e3c50be`；
- P1 binding：r15 / `1e31a9acef39261f776f7ed4069fd73f4531e8d12b55779bfc0fbd74c67f9655`。
- execution-surface commit：`96e2d64`；完整本地门 473 passed / 24 expected skips、ruff 0、smoke OK。

2026-09-04 18:03（Asia/Taipei）已在 GPU0–3 分别启动四臂。启动前四卡均 0%，P1 远端
`validate-only` PASS，r15/r16 传输前目标不存在且双端逐文件树 hash 一致。四任务均使用独立
`setsid nohup`、SID、run-dir 与日志，已与 SSH 会话解耦；首轮观测四个 trainer 均 ALIVE，日志均到
epoch 0 / 500 docs，`device=cuda`、`final_valid_accessed=false`。

四臂固定：

1. local recipe；
2. rates-only：temporal/causal/subevent = 2/4/4；
3. rates + coref auxiliary rate 0.4；
4. rates + coref auxiliary + per-family checkpoint selection。

四臂必须显式绑定任务 A 产生的新 P1 bundle ID 和 protocol SHA-256，并保持 seed 13、manifest、候选全集、
official evaluator、backbone pin、训练预算及除目标开关外的所有配置一致。第 4 臂必须从头训练。

启动前已向作者展示并核对：

- 每一臂的完整 `.venv/bin/python ...` 命令；
- cwd `/data/TJK/ekg`；
- 选择的 GPU 与最新 `nvidia-smi`；
- `runs/stages/A3/...` 输出目录和 `logs/...` 日志；
- 预计时长、checkpoint、predictions、official metrics、metadata；
- 单变量差异审计。

不要在交接阶段猜 launcher 参数。以当前 CLI、P1 hash 和冻结 execution plan 生成完整命令并审查后再
提交。用户明确要求启动后，若四张 4090 都空闲，四个已冻结、互不写同一路径的 arms 可以各占一张卡
并行；这属于 C 类调度，不改变科研协议。一条 SSH 只发一个 `setsid nohup` 后台任务。

### 任务 D：A3.6 评分与失败交接

只有成功 SSH 观察到进程 GONE 才认为任务结束；SSH 失败只是第三态。每臂完成后：

1. 校验 run metadata、配置单变量差异、P1 binding、checkpoint/log hash 和 `final_valid_accessed=false`；
2. 对同一 internal-dev 候选全集运行 official evaluator；trainer macro 不能代替官方分数；
3. 将真实结果只追加到 [`results/PHASE_A.md`](results/PHASE_A.md)，升降如实；
4. 输出 A3 `status=failed` handoff 和 relation fallback bundle；
5. 不因官方配方提高分数而给旧方法记创新贡献；
6. 完成后更新 TODO/HANDOFF/TASKS，并让 R1 做最终 promotion 审查。

未经作者新授权，不启动 seeds 17/42。

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

## 6. 新窗口的完成汇报格式

每完成一项，用以下格式更新本文和最终回复：

```text
完成：<task ID / phase>
身份：<commit / protocol hash / bundle ID>
验证：<实际命令与 PASS/FAIL>
结果：<只引用 docs/results/PHASE_*.md 位置>
状态：pass | failed | blocked；原因
下一步：<真实依赖；是否需要 GPU/多种子/用户授权>
```

新窗口不要先问宽泛的“接下来做什么”。若工作树和依赖检查正常，直接执行任务 A，并可同时推进任务 B；
到任务 C 的长 GPU 命令时，再按规则向作者展示完整命令和预期产物。
