# 交接文档 · 新窗口从这里开始

> 更新于 **2026-09-07**。本文是新窗口唯一必读入口；读完后再按本文链接打开所需文件，不回溯聊天记录。
> 本文只记录状态、决策、依赖与下一步，不复制实验表格。实验数字只认
> [`results/`](results/README.md)。

## ▶ 当前阶段（新窗口先看这张表）

| 项 | 值 |
|---|---|
| 正式阶段 | `R1 方法设计准入`；状态 `preparation_partial_blocked`，**未放行任何 proposed GPU 训练** |
| 当前队列 | 任务 E.2，共 E1–E7（E1、E2 已 `done`） |
| **下一个要做的任务** | **E.2 表里第一个 `状态 = todo` 的行**（当前是 **E3：T021 Ch2 因果 design brief**） |
| 开工前读什么 | 本文 §0 只读检查 → 任务 E.0 六条约束 → E.1 联网核实结论 → E.2 队列表；其余按需 |
| 完成后必须做什么 | 按 §6 五步回填：产物落地 → 写结果页 → 改 E.2 该行状态与 commit → 推进队列 → commit + **push** |

新窗口不要问“接下来做什么”，也不要重读整个仓库：只读检查通过后，直接开 E.2 里第一个 `todo`。

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
3. 已关闭的 A3 契约与交接：[`phases/PHASE_A3_relation_balanced.md`](phases/PHASE_A3_relation_balanced.md)；
4. 当前 R1 准入契约：
   [`phases/PHASE_R1_method_design_freeze.md`](phases/PHASE_R1_method_design_freeze.md)。

只读检查通过后，**直接执行任务 E.2 表中第一个 `状态 = todo` 的行**；不要重跑已 `done` 的行，
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
  `4e893c1 docs(r1): record method design gate evidence`、`f1401bc feat(r1): freeze factuality
  cross-validation folds`、`32cfd46 feat(r1): close relation handoff and power gate`、
  `277b36f fix(r1): isolate factuality OOF training source`；
- 本文提交后以新的 `origin/main` HEAD 为准；
- 最新本地验证：489 passed / 24 expected skips，ruff 0，`ekg-smoke` OK，P1 local gate PASS；
- local gate 的 `tested_tree_sha256`：
  `3bff2ac2b5366ed06ebe81c9b2e549f0949216c832ad8e6098a6782e0c701d3c`；
- A3.6 只运行了已授权 seed 13；R1 功效只读 train-derived internal-dev。跨数据 ID 审计按合同读取了
  public-valid 结构字段但未计算关系/事实性指标，访问已在 ledger 披露；没有搬运 checkpoint。

## 2. 已经成立和不得改写的事实

只从下列结果文档取精确数字：

| 主题 | 权威入口 | 当前结论 |
|---|---|---|
| Ch2 工作点与检索 | [`results/PHASE_A.md`](results/PHASE_A.md) | 工作点两个核心周期已用完；近似 retriever 三条均未过门；prototype/ATLoss 已封存 |
| Ch1 历史方法 | [`results/PHASE_C.md`](results/PHASE_C.md) | 旧方法未稳定胜出；event-level gold argument 只能作泄漏型 oracle |
| Ch3 历史方法 | [`results/PHASE_D.md`](results/PHASE_D.md) | 与强 baseline 未统计分开；gold evidence 不支持“只换 locator”作为主要解法 |
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
冲突，故 event-level arguments→mention 的 deployable 路线 blocked；Ch1 prospective power PASS，但缺
argument-aware 同协议 runnable baseline；Ch2 prospective power PASS，但缺第二个独立同协议 runnable
baseline；Ch3 的 291-document 设计 underpowered，但预冻结五折 OOF 已完成并验收，CLS anchor 与
2,913-document pooled power 均 PASS。精确数字与 acceptance hash 只见 [`results/PHASE_R1.md`](results/PHASE_R1.md)。

学位类型、入学年份、学科与专业未知项均保持 `null`；同济校级标准来源/date/hash 已冻结，未知项不影响
项目自定的更高科研硬门。文献矩阵已只读冻结 CorefPrompt、MAVEN-FACT、ModaFact、TextEE、OmniEvent
五个官方仓库 HEAD（E2 又冻结了第六个 LLMERE，记录在 `results/PHASE_R1.md` §4/§9，
`literature_matrix.json` 保持原哈希不动），但没有把不同数据/split/evaluator 的代码误记为同协议 baseline。Ch3 因果 brief 已
通过 T022 并绑定已验收 OOF/power；Ch1/Ch2 brief 仍为 blocked/draft，**未放行 proposed GPU 训练**。

两台服务器都没有可恢复的 OmniEvent/TextEE EAE checkpoint；OmniEvent 官方 checkpoint URL 已失效，
因此不得把随机初始化或跨 ontology 重训冒充官方 baseline。5090 的既有 Qwen 服务保持运行。

后续按 [`TASKS.md`](TASKS.md) 的 T020–T024 继续，但各章仍先补齐自身 blocker：

1. Ch3：T022 因果 brief 已通过；T023 是全局跨产物审计，仍等待 T020/T021 随各自 blocker 关闭，之后
   才能生成 T024 D4 phase contract；未冻结前不启动 proposed GPU pilot；
2. Ch1：继续寻找可忠实运行的 mention-local argument-aware baseline/checkpoint；没有 checkpoint 时只做
   adapter 与 fixture，不把跨 ontology 重训冒充官方复现；
3. Ch2：取得或透明适配第二个独立近期同协议 baseline，保持完整候选全集；
4. 对满足 blocker 的剩余 brief 做 T020/T021 审查，再做 T023 跨产物一致性审计；只有通过者才能生成 T024
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

1. **单队列**：任务顺序只认下面 E.2 的编号表。要偏离顺序，**先改本表再执行**，不在会话里口头改计划。
2. **开工前对齐**：除 §0 的三条只读检查外，必须确认 `git rev-parse HEAD` 等于 `git rev-parse origin/main`；
   不相等就先 `git pull --rebase`，未对齐不开工。
3. **交接靠文件不靠记忆**：一项任务算完成，必须四件齐全——产物落地、数字写进对应
   `results/PHASE_*.md`、本表该行状态改为 `done` 并填 commit、**已 push 到 `origin/main`**。
   没 push 就没交接，下一个代理不得开工。
4. **不开分支、不开 worktree**：只在 `main` 上按逻辑单元提交。（2026-09-07 已删除
   `.worktrees/r1-t023-t024` 与已并入 main 的 `feat/r1-t023-t024`。）
5. **活动任务独占产物**：持有活动任务的代理独占该任务涉及的全部结果页与 `runs/` 目录；
   另一代理此时**只读**，不写任何 `results/`、`runs/`、`TASKS.md`。
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

#### E.2 本周队列（9/7 – 9/9；写代码由 Claude/Codex 承担，故时间成本压在决策与 GPU 上）

| 序 | 任务 | 前置 | 完成判定 | 状态 | commit |
|---|---|---|---|---|---|
| E1 | 关 Ch2 TacoERE 适配档的账：查清 `taco-s13-r2` 与 `taco-s13-r3` 差异来源 → **预注册**选档规则 → 评分正式档 → 三族官方 F1 写进 `results/PHASE_R1.md` → 更新 `status.json` | 已满足 | 差异有书面解释；选档规则在看分数前写定；结果页与 `status.json` 不再互相矛盾 | done | `91e818e` + `bc6b07e` |
| E2 | 取 LLMERE 官方实现做可运行性核查：冻结 commit/tree hash、核对 MAVEN-ERE 数据接口、base model、显存与是否 LoRA，裁决"能否在我们 2622/291 manifest 与官方 evaluator 下忠实重跑"；**本步不训练** | E1 | 裁决落到 `results/PHASE_R1.md` 第 4 节，并修订该节 Ch2 结论；能跑则排下周训练，不能跑则写明具体阻断点 | done | `8a8ac1a` |
| E3 | T021 Ch2 因果 design brief：写入 LLMERE/TacoERE 对照结构与 CovEReD、SURE-RAG 的一般命题，明确 A4 窄 delta | E2 | 审查 PASS，且推理保持完整候选全集 | todo | — |
| E4 | T020 Ch1 因果 design brief：正面处理 ACCI 抢占，核实其论元来源，写清 C5 的窄 delta | 已满足 | 审查 PASS；不使用 MAVEN-ARG cluster gold；不出现"首次"表述 | todo | — |
| E5 | T023 跨产物一致性审计：实跑 `scripts/audit_r1_consistency.py`，修掉 `status.json` 与结果页的矛盾 | E3 + E4 + 已有 T022 | 输出 `cross_artifact_audit.json`；每条需求映射到任务/测试 | todo | — |
| E6 | T024 冻结 C5/A4/D4 phase contract | E5 | 三份契约的输入、baseline、protocol hash、promotion/stop、bundle、GPU 命令齐全并落 hash | todo | — |
| E7 | 修可追溯性缺口：把 `src/ekg/relations/extractor/supervised.py` 纳入 relation run 的哈希集合（E1 发现：两档携带同一 trainer hash 却构造不同编码器输入） | E6 | 新增 hash 键不改动任何既有 hash；若动到 trainer 本身则须同时重建 P1 bundle 并重绑 | todo | — |

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

#### E.3 GPU 使用：按需求，不为占卡而占卡

本周真实 GPU 需求只有 E1 的一次评分（已于 2026-09-07 在 4090 GPU1 跑完，约 1 分钟）。E2 只做静态核查
不训练，E3–E7 全是文档与审计。
因此 **9/7–9/9 期间 4090 大面积空闲是正常的**；卡是公用资源，不得为了"看起来在跑"启动无准入的训练。
真实的大 GPU 需求在下周：T024 放行后的第一个 seed-13 pilot（按 E.1 的证据，优先 D4）。
LLMERE 同协议重跑**暂不排期**——E2 裁定为 `conditionally_runnable` 但有四条未清阻断点，且是 4090 整机
数天级占用，须先清阻断点并取得作者同意。5090 单卡有既有 Qwen 服务约 17 GB，使用前仍须逐次取得作者授权。

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
