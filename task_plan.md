# Task Plan: v6 论文方向重审

## Goal

在可追溯证据和既有实验基础上，收敛并完成一条组件化的事件图谱构建硕士论文主线；各章可使用不同公开语料，但必须在各自主指标上统一重跑并超过多个方法。

## Current Phase

Phase 20（5090 临时单种子探索）进行中。4090 当前不可达，用户已明确授权使用 gpu-5090；优先探索能提高 Ch2 最终 official 三族指标的不同方案。禁止追加 seeds，只有单种子方案全部超过 baseline 与护栏且用户再次授权后才允许多种子。

## Phases

### Phase 1: 接管与上下文恢复

- [x] 从 `.claude-session-handoff.txt` 恢复原任务、已完成项、失败项和既定流程
- [x] 核对 Git 状态、未提交差异、持久化交接文件和最近提交
- [x] 保留并隔离与本次重审无关的 v5/Ch1 未提交成果
- **Status:** complete

### Phase 2: 五路证据探索

- [x] 按作者要求改为严格串行：A → B → C → D → E
- [x] A：领域地形与真实卡点（A1/A2/A3a 已完成；A3b 并入 DR-E）
- [x] B：公开数据集、竞争密度与 MAVEN 残值（PDF 来源恢复；高影响结论有条件通过）
- [x] C：LLM 方法范式、开源实现与单卡可行性（PDF 来源恢复；证据等级与仓库快照有条件通过）
- [x] D：跨语言、风险场景及其他切口可行性（PDF 来源恢复；α/β 排除与 ECI 候选有条件通过）
- [x] E：工业落地与人才市场信号（PDF 来源恢复；技术/产业/招聘边界有条件通过）
- [x] 将剩余高 Web 成本任务整理为 DR-B/DR-C/DR-D/DR-E 四份网页版深度研究提示词
- **Status:** complete

### Phase 3: 证据交叉核验

- [x] 核验决策关键论文/数据集/代码的一手来源；未穷尽项在各 audit 的验收边界列明
- [x] 核验决策关键指标的表号、split、评测脚本和指标定义；无法同轴者排除或降级
- [x] 抽样实访 test/leaderboard 通道及 GitHub 可运行性信号；访问失败如实记录
- [x] 对冲突、缺项或不可比内容在 B/C/D/E 独立 audit 层更正
- **Status:** complete

### Phase 4: 综合地形与项目决策

- [x] 汇总问题价值与竞争密度（两栏分离）
- [x] 形成事件图谱 vs 事理图谱选择依据
- [x] 给出重构 vs 重开的证据链、利弊和明确结论
- **Status:** complete

### Phase 5: 作者评审

- [x] 生成并提交综合报告和项目决策
- [x] 作者接受：事件图谱、重开论文主轴、ESL/CTB ECI 优先资格验证
- **Status:** complete

### Phase 6: ESL/CTB ECI 资格验证

- [x] 生成定向网页版 Deep Research 提示词与附件说明
- [x] 接收 `F_eci_protocol.md` 与 `F_eci_protocol.pdf`
- [x] 本地核验 corpus version / folds / pair generation / evaluator / license
- [x] 审计至少两个可复现的独立近期 baseline：ICCL 仅 ESC、DICP 仅 CTB，未形成同协议双 baseline
- [x] 完成 27GB 前置判定：DICP 有单张 RTX 3090 一手证据；对手门已失败，GPU smoke 无继续价值
- [x] 输出 `docs/replan/F_eci_protocol_audit.md`：当前 NO-GO，回到固定协议 MAVEN-ERE causal 资格审计
- **Status:** complete

### Phase 7: 固定协议 MAVEN-ERE causal 资格验证

- [x] 生成定向网页版 Deep Research 提示词与附件说明：`DR_G_MAVEN_ERE_CAUSAL_PROTOCOL_PROMPT.md`
- [x] 接收 `G_maven_causal_protocol.md` 与 `G_maven_causal_protocol.pdf`
- [x] 本地核验唯一公开 causal 协议轴、split/pairs/evaluator 与仓库执行闭环
- [x] 核验同轴近期方法：Chen candidate universe 不同，LLMERE 缺训练/推理 package，双 baseline 不足
- [x] 完成 CPU split/evaluator smoke；静态对手门失败，因此不进入 27GB GPU smoke
- [x] 输出 `docs/replan/G_maven_causal_protocol_audit.md`：exact-B 协议四门 PASS，主任务资格 NO-GO
- **Status:** complete

### Phase 7b: MATRES / TB-Dense 时间关系资格验证

- [x] 作者选择严格串行扩大候选池，并批准优先审查 MATRES / TB-Dense 时间关系
- [x] 生成网页版 Deep Research 提示词与附件说明：`DR_H_TEMPORAL_PROTOCOL_PROMPT.md`
- [x] 接收 `H_temporal_protocol.md` 与 `H_temporal_protocol.pdf`
- [x] 本地核验数据许可、split、pair/labels、evaluator、双 baseline 与 27GB 门槛
- [x] 输出 `docs/replan/H_temporal_protocol_audit.md`：annotation 协议可冻结，但数据许可、
  exact published baseline 与双对手门失败，维持 NO-GO
- **Status:** complete

### Phase 7c: ECB+ / GVC / FCC 事件共指资格验证

- [x] 作者同意按推荐继续，并保持严格串行
- [x] 生成网页版 Deep Research 提示词与最小附件清单：`DR_I_EVENT_COREF_PROTOCOL_PROMPT.md`
- [ ] 接收研究报告后，本地核验数据许可、split、mention/pair/cluster universe、evaluator、双 baseline 与 27GB 门槛
- **Status:** paused（作者要求先回到顶层论文分解，不执行 DR-I）

### Phase 7d: 顶层论文问题分解重构

- [x] 作者明确：全篇不限定同一语料类型，停止无限增加资格门
- [x] 从事件图谱构建文献、v5 四章与本地资产提炼统一总问题和组件地图
- [x] 确认唯一推荐骨架：身份 → 关系 → 事实性 → 下游消费者；不同章节允许不同语料
- [x] 区分硬约束、可本地统一重跑项与真正需要外部深度研究的缺口
- [x] 输出 `docs/replan/THESIS_COMPONENT_REFOCUS.md`
- **Status:** complete

### Phase 8: 章节设计与实施规划

- [x] 作者认可按事件图谱构建组件组织，不限定全篇语料类型
- [x] 将修订后的“公开可比”定义写入 `docs/SPEC.md`
- [x] 刷新 Ch2/Ch1/Ch3/Ch4 的 baseline 与最小实施矩阵
- [x] 严格串行恢复一条活线；启动任何远端 GPU 命令前单独列命令、目录和产物
- **Status:** complete

### Phase 8a: 独立可行性审查

- [x] 作者要求引入独立审查，不能由当前方案设计者自我验收
- [x] 独立审查本地代码/数据/结果、GPU 资源约束与四章方案
- [x] 核验无人工标注、学界公认指标、可重跑 baseline、方法贡献、工作量与逻辑闭环
- [x] 输出独立 verdict、硬阻塞项、可修订方案与建议实施顺序
- [x] 主代理仅在独立报告完成后交叉核验，不提前替其下结论
- **Status:** complete

### Phase 8b: 权威 SPEC 重写

- [x] 将独立审查结论写入 `docs/SPEC.md`，清除 Ch3 已胜出、Ch4 已证实等过期主张
- [x] 固定“三个方法章 + 一个系统评估章”的研究问题、输入输出、标准指标与跨章桥梁
- [x] 写明统一重跑 baseline、零新增人工标注、随机种子、统计检验和资源边界
- [x] 将 GPU 实验前必须通过的协议闸门写成可机械核验的验收条款
- **Status:** complete

### Phase 8c: Gate G0 本地静态筛查

- [x] 核验四章数据、manifest、evaluator、现有 baseline、缓存/权重和输出接口是否实际存在
- [x] 核验 Ch4 能否在同一 710 文档/1,908 queries 上接入 Ch1/Ch2/Ch3 真实产物
- [x] 核验零新增人工标注与 4090/5090 单卡可行性，区分 PASS / CONDITIONAL / BLOCKED
- [x] 生成可追溯的筛查报告；只运行 CPU/只读命令，不启动训练或 GPU
- **Status:** complete（总体 CONDITIONAL，未放行完整 GPU）

### Phase 8d: 严格串行阶段契约

- [x] 划分 G0 → Ch2 → Ch3 → Ch1 → Ch4 的输入、任务、产物、Done、Fail 与 Stop 条件
- [x] 每阶段限定最多两轮机制验证，禁止失败后扩大数据、换指标或无界扫参
- [x] 写明失败如何降级论断、哪些产物仍可供后续章节使用，避免错误累计
- [x] 更新 `docs/phases/README.md`、`docs/TODO.md` 与必要的活线契约
- **Status:** complete

### Phase 9: 文档与闸门验收

- [x] 检查 SPEC/TODO/phase/replan 之间无互相冲突的活动指令
- [x] 检查所有本地链接、Markdown whitespace、关键门槛与顺序断言
- [x] 因工作树含接管前的代码改动，运行 pytest、ruff 与 CPU smoke；三项全部通过
- [x] 给作者交付当前 PASS/CONDITIONAL/BLOCKED、下一条串行动作和远端命令前置说明
- **Status:** complete

### Phase 10: v6 独立反方审查

- [x] 完整读取用户指定的 13 份权威/阶段/结果索引文档，建立跨文档条款矩阵
- [x] 以论文原文、官方仓库、数据集与官方 scorer 核实任务、指标、baseline 与资源边界
- [x] 逐章判断可行性、贡献潜力、失败降级路径与资源成本
- [x] 逐阶段审计输入、promotion/Done/Stop 条件及局部失败传播
- [x] 给出仅含必要修订的可直接写回文本、执行顺序与最多 8 项首轮 GPU 放行条件
- **Status:** complete

### Phase 11: v6 审查整改落地

- [x] 修订 `SPEC.md`：主锚、matched seeds、文档簇统计、final-valid 封存与局部失败算术
- [x] 修订 `EXPERIMENTS.md`：必含/可选 baseline、核心/二级机制、Ch4 本地重建协议与统计族
- [x] 修订 P1/A3/D3/C4/E3/H2 契约：全局协议与阶段入口分离、客观 promotion/Stop、失败可继续路径
- [x] 同步 `TODO.md`、phase 索引与 G0 报告，消除活动文档冲突并标记历史审查边界
- [x] 运行链接、术语、门槛、whitespace 与文档一致性检查；不启动 GPU、不提交或推送
- **Status:** complete

### Phase 12: 执行 P1 协议冻结与 A3 准入

- [x] 盘点现有数据、脚本、baseline checkout/checkpoint 与 P1 已完成资产，建立缺口清单
- [x] 生成 ERE/FACT 显式 manifests、support counts、source/manifest hashes 与 Ch4 namespace/generator 约定
- [x] 持久化 evaluator 来源，补 gold-self/adversarial fixtures 与 ID/candidate 拒绝测试
- [x] 实现 stage bundle schema/validator，覆盖坏 hash、重复/缺失 ID 与 upstream identity
- [x] 闭合 local pair、official single、official joint 的同一 10-doc schema smoke 与 anchor-selection 预注册
- [x] 本地 pytest/ruff/ekg-smoke 全绿；4090 checkpoint/最长输入/10-doc 真实前向及回传 strict schema 通过
- [x] 重建并重读 P1 bundle，同步 P1/G0/TODO/result：`global_protocol_status=pass, a3_entry_status=pass`
- **Status:** complete（P1.1–P1.6 全部完成；A3.0 已放行）

### Phase 13: P1 独立反方复验

- [x] 复核活动 SPEC/EXPERIMENTS/P1/A3/TODO 与 bundle 状态无矛盾或越权放行
- [x] 从 raw data 独立重算 source hash、doc-ID split、ERE/FACT 对齐、supports 与 candidate digest
- [x] 从固定 official source 重放 evaluator gold-self/adversarial/rejection gates
- [x] 独立复核三个 baseline adapter 的 source/patch/schema/candidate population 与证据边界
- [x] 校验 stage bundle 四件套、artifact hashes、远端 prediction/log/checkpoint metadata 与 GPU claim
- [x] 重跑定向/全量测试，按 blocker/caveat/verified 给出最终复验裁决
- **Status:** complete（VERIFIED：底层证据；FAILED：自动闸门反例；最终裁决 CONDITIONAL）

### Phase 14: P1 闸门加固与重新放行

- [x] 升级 stage bundle schema/validator：可信 protocol hash、外部证据重哈希、严格状态/schema/hash 校验
- [x] 加固 P1 builder：完整 candidate/ledger 绑定、严格 remote/baseline/local/evaluator 证据校验
- [x] 修复 final-valid ledger 为 append-only、confirmatory count 单调不减
- [x] 加固 official scorer、submission/pair evaluator 与 strict rejection 回归测试
- [x] 建立 A3 正式 fail-fast baseline 输入 materializer/launcher，强制 manifests、candidate protocol 与 provenance
- [x] 生成新版本 P1 bundle，独立运行 tamper/fake-remote 反例和全套本地 gate
- [x] 同步 SPEC/TODO/P1/A3/G0/results 的实际状态与新 bundle 身份
- **Status:** complete（P1 r3 PASS；A3 execution-plan 已冻结；未启动 GPU 训练）

### Phase 15: A3.0 Git 同步与远端预检

- [x] 区分本轮 P1/A3 修改与进入本轮前已存在的无关工作树改动
- [x] 仅提交并推送本轮获授权的可信链、协议、测试与活动文档
- [x] 只读确认 `gpu-4090` 远端工作树/分支/运行状态，再按 runbook 同步代码
- [x] 通过 `scp`/`rsync` 与双端 SHA-256 传递 Git 不跟踪的 P1 r3 必要证据
- [x] 在 `/data/TJK/ekg` 重建 A3 CPU execution plan，并核对外部 plan SHA-256
- [x] 对三个 baseline 执行 no-execute launcher，保存准确 argv/cwd/预期产物
- **Status:** complete（P1 r4/remote plan/三路 no-execute PASS；未启动 GPU job）

### Phase 16: A3.0 GPU baseline 启动复核

- [x] 从 A3 契约确定首批必须运行的 baseline/seed 与主锚冻结顺序
- [x] 审计 launcher/训练脚本的同一任务多卡行为、日志与失败隔离
- [x] 只读核验远端模型路径、Python/CUDA 依赖、磁盘、GPU 空闲与现有进程
- [x] 判断哪些 baseline 可忠实使用同一任务 DataParallel，哪些必须维持单卡
- [x] 给出明确 GO/NO-GO、推荐首批调度表与启动前剩余修复
- **Status:** complete（当前计划局部 NO-GO；未启动训练）

### Phase 17: A3 路径、backbone 与放行术语纠偏

- [x] 通过作者可用的同一 `ssh gpu-4090` alias 只读核对 `/data/TJK/` 下项目、模型缓存与实际用户环境
- [x] 核对官方 baseline 绑定 RoBERTa-base 的一手代码/论文依据，区分忠实复现与主方法 backbone
- [x] 判断 v6 主实验是否需要现代 backbone 主表或迁移验证，避免以换大模型冒充方法增益
- [x] 重新裁定模型路径与 subevent guardrail 是否属于 NO-GO、启动 HOLD 还是可并行修复
- [x] 修订所有受影响的活动计划/契约文本并做一致性校验；不启动长 GPU 任务
- **Status:** complete（后续已推进到 P1 r11 / A3 r12，四章同协议对手线闭合）

### Phase 18: 周四总体计划、进展汇报与三日执行编排

- [x] 以 `docs/results/` 为唯一数字源，逐章核对 Ch1–Ch4 当前成立与不成立的结论
- [x] 核 ACL 一手论文主表，整理同数据集公开方法的大致指标与不可比边界
- [x] 修订 `docs/reports/2026-09-03_阶段性报告.md`，给每章补齐问题、方法、实证、缺口、周四预期
- [x] 形成 2026-08-31 至 2026-09-03 的日程、验收物、止损条件与汇报口径
- [x] 设计并落实最小文档索引与分类规则，保证历史证据不被误当活动指令；不做大规模搬家
- [x] 按先验证后训练的流程实现/核验 Ch2 逐族×逐位置控制器，并完成本地三件套
- [x] 只读审计 4090，重建 P1 r12 并物化 A3 r13 preflight
- [x] 展示准确命令后完成 Ch2 两 epoch行为 smoke：12 条轨迹完整、offset 有界、方向合理，放行完整 seed-13
- [x] 将 Ch2 两阶段检索器、Ch3 证据条件化+稀有类目标、Ch1 关系感知度量列为后续方法优先级，并给出实现/止损边界
- [x] 核对 Git、链接、权威来源和报告内数字，完成可回滚提交与交接
- **Status:** complete

### Phase 19: 单种子优先的 GPU 并行推进

- [x] 将“单种子全部过 baseline 且获得用户明确授权前，禁止多种子”写入根指令和活动契约
- [x] 核对 Ch2 r13 完整 seed-13 正式流水线、空闲 GPU、输出目录与 official evaluator 边界
- [ ] 在 GPU0 启动 Ch2 r13 完整 seed-13，持续监测并生成 official 三族指标（运行中，trainer PID 3907812）
- [ ] 只为不同方案/任务使用其他空闲 GPU，禁止 seeds 17/42 或任何其他多种子运行（Stage-1 retriever 已在 GPU1 运行，PID 3920963）
- [ ] 按单种子主指标与护栏判定：过线则保留，未过则封存并转 retriever→cross-encoder
- [ ] 更新结果、交接、进度与服务器产物身份
- Error log：两篇 ACL PDF 串行下载/抽取首次超过 30 秒工具返回窗口；原进程仍 ALIVE，Efficient DERE 已完整，TacoERE 正在下载。不重启重复下载，只监测原进程后续完成。
- Error log：新 retriever CLI 首次本地 `--help` 因 CPU 环境无 torch，顶层导入了只在 torch guard 下定义的 `encode_trigger_reps` 而失败。按现有 trainer 模式把该导入移入 `main()` 的 torch imports 之后；不安装本地 torch。
- **Status:** in_progress

## Key Questions

1. LLM 时代仍值得显式构建事件图谱/事理图谱的真问题是什么？
2. 哪些公开任务同时具备可得数据、活跃方法竞争、可核验 test 口径和单卡可复现性？
3. 跨语言与风险监测是实质性研究切口，还是缺少公开 benchmark 的包装？
4. 现有 MAVEN 资产是否足以支持重构，还是重开能得到更强且更闭环的 3–4 章体系？

## Decisions Made

| Decision | Rationale |
|---|---|
| 先探索、后给方案 | 作者已确认；避免把应由证据决定的方向变成拍脑袋选项 |
| 问题价值与竞争密度分栏 | 不能按“对手是否好打”选研究问题 |
| 五路报告直接落 `docs/replan/` | Claude 上轮因会话级 scratchpad 失效而丢失全部代理报告 |
| 严格串行执行 A → B → C → D → E | 作者要求降低并发额度消耗；每路完成并初核后才启动下一路 |
| B/C/D/E 与 A3b 优先转交网页版 GPT 深度研究 | 这些任务以大规模外部检索为主；本地 Codex 保留一手来源复核、口径审计与综合决策，避免重复消耗额度 |
| 暂不提交或修改 v5/Ch1 成果 | 用户未授权提交；且该批改动与 v6 重审相互独立 |
| 方向获作者认可前不写实现代码 | 继承 brainstorming HARD-GATE 和既有交接约束 |
| DR-B 保留原始输出，另写本地审计层 | 避免把深度研究原文与 Codex 更正混在一起；后续以 `B_datasets_audit.md` 覆盖冲突结论 |
| DR-C 保留原始输出，另写本地审计层 | 方法分类成立，但 sampled/非官方 split/不完整仓库不能混成严格公开主轴；后续以 `C_methods_code_audit.md` 覆盖 |
| DR-D 保留原始输出，另写本地审计层 | α/β 的 benchmark 断链成立；ESL/CTB 是最强条件性候选，但 version/fold/pair/license 未完全锁定，后续以 `D_angles_audit.md` 覆盖 |
| DR-E 保留原始输出，另写本地审计层 | 技术存在理由与工程技能信号成立，但工业/招聘/OSS 只能作条件性快照；后续以 `E_industry_audit.md` 覆盖 |
| 总本体选择 occurrence-level 事件图谱 | 公开标注、风险监测实例级问题与本地资产一致；事理/script 支线缺统一术语和近期共享 benchmark |
| 重开论文主轴、迁移工程资产 | v5 四章均未无保留满足公开同轴标尺；通用层、evaluator、数据流水线与方法学纪律仍可高比例复用 |
| ESL/CTB ECI 作为条件性主锚 | 至少三个独立近期正式团队、公开性较强、单卡可行；必须先冻结版本/folds/pairs/evaluator 并复现两个对手 |
| 作者批准先做 ECI 资格验证 | 只批准低成本协议与 baseline 闭环；不等于定下全篇，也不授权重型 GPU 实验 |
| ESL/CTB ECI 当前资格为 NO-GO | DR-F 有多项身份/仓库/硬件错误，但本地一手核验仍确认同协议双 baseline 门失败；不启动 GPU，转审固定协议 MAVEN-ERE causal |
| MAVEN-ERE causal 当前资格为 NO-GO | LLMERE-defined B 的数据/split/pairs/evaluator 已完整复现，但没有第二个独立近期同协议可执行 baseline；Chen 是 500-sample setting，Xiang 公开代码不是 MAVEN 管线，不启动 GPU |
| 扩大候选池时先审 MATRES/TB-Dense 时间关系 | 综合报告已将其列为第一储备；本地有 MATRES 原始资产，且 2024–2025 有多篇正式候选，但 split/labels/closure/evaluator 是否同轴仍需先审 |
| MATRES/TB-Dense 时间关系当前资格为 NO-GO | MATRES annotation split/pairs 可冻结，但完整 TML/许可不闭合；TCT 官方附件是重切分+Vneg 且不可原样执行；Roccabruna 论文 counts 与 formatter 冲突，无法形成两个 exact published baselines |
| 下一候选优先审事件共指 | ECB+、GVC、FCC 有固定语料与成熟 CoNLL coreference 评测谱系；必须先确认近年独立方法是否真的共享 mention setting、split 和 scorer，不能把 within-/cross-document 或 gold-/predicted-mention 数字混用 |
| DR-I 使用四个 Markdown 附件 | 综合决策、数据审计、方法审计与最近一次 H 审计足以提供标准和已知边界；不上传 PDF 或原始 F/G/H 报告，减少上下文与重复成本 |
| 暂停按单一语料逐项资格淘汰 | 作者纠正：论文应按事件图谱构建组件组织，各章可用不同公开语料；只要求每章在其公开主指标上实际超过多个方法并共同服务统一流水线 |
| 恢复并收敛 v5 四章 | 现有身份→关系→事实性→消费者已经是事件图谱构建的自然分解，且代码 schema/registry/评测资产均已贯通；无需因论文原 split 或作者包缺陷重开全篇 |
| baseline 以本地统一重跑为准 | 原论文 split 不同只禁止直接比较原数，不取消方法资格；允许透明工程修补或忠实复现，硬要求是同章同 test/evaluator、多个实际重跑、完整可追溯 |
| 四章方案必须通过独立可行性审查 | 作者要求从现有本地+gpu-4090+gpu-5090、无人工标注、标准指标、方法贡献、工作量与叙事闭环六方面作反方评审，避免主代理再次自设或自降门槛 |
| 采纳独立审查的有条件方案 | 结构固定为“三个方法章 + 一个系统评估章”；实验顺序改为协议冻结→Ch2→Ch3→Ch1→Ch4，Ch3 与 Ch4 先证伪关键假设，不靠加语料或堆模型补洞 |

## Errors Encountered

| Error | Attempt | Resolution |
|---|---:|---|
| 活动文档禁词正则把“旧线禁止执行/旧已过线判断作废”误报为仍在执行 | 1 | 根指令同步和本地链接已实际通过；改成正向断言唯一活线/顺序，并只在非否定句中检查旧指令 |
| 新文件 whitespace 检查把 `git diff --no-index` 的正常差异退出码 1 当失败 | 1 | 改为忽略 diff 状态、只检查 `--check` 输出；七份新增文档均无 whitespace 输出 |
| gold official-prediction 生成+scp+远端评分合并命令在 30 秒窗口只返回本地文件/hash，未返回评分 | 1 | 不推断 scp/评分是否完成；保留本地临时文件，下一步只核远端文件 hash，存在则单独运行 scorer，不重生成/重传 |
| 登记 evaluator smoke 时补丁 hunk 夹入多余 `@@`，语法校验失败 | 1 | 原子失败、无文件变化；拆除空 hunk 后重新提交单一合法补丁 |
| 把 labelled MAVEN-ERE raw JSONL 直接作为 official prediction 做 gold-self smoke，关系/共指非满分 | 1 | 输入 schema 错，不是 evaluator 失效；不重复原命令，转审 evaluator 与 converter，生成真正 official prediction shape 后再测 |
| SPEC 禁词检查把“不得复活成方法卖点”误命中为“净化卖点” | 1 | whitespace 与正向断言已通过；后续改为核查明确的旧肯定句，不再用缺少否定语境的宽泛正则 |
| `apply_patch` 拒绝在同一补丁中对 `docs/SPEC.md` 同时 Delete/Add | 1 | 原子失败、文件未变；改为先单独删除、再用第二个补丁新增完整 SPEC，不重复同一操作 |
| 独立审查补写回合被中断时报告文件处于先删后写窗口，`INDEPENDENT_THESIS_FEASIBILITY_REVIEW.md` 消失 | 1 | 前半报告仍在会话工具输出；不由主代理代写，要求同一审查者停止检索并用单次补丁重建最终文件，随后立即校验 |
| 登记独立报告丢失的首个补丁未匹配 task plan 上下文 | 1 | 补丁原子失败、无部分写入；读取实际 Phase 8a/Errors/进度片段后改用精确上下文 |
| 顶层策略一致性脚本要求显式 `Ch2 → Ch1 → Ch3 → Ch4`，正文原为编号列表 | 1 | 内容未缺失；补一行机器/人均可直接读取的顺序摘要后重跑 |
| `THESIS_COMPONENT_REFOCUS.md` whitespace gate 报末尾多一空行 | 1 | 删除额外空行，随后重跑文档一致性校验 |
| `session-catchup.py: permission denied` | 1 | 脚本无执行位；后续用 Python 解释器显式运行，不修改 skill 文件权限 |
| DR-G 接收登记补丁未匹配错误表结构 | 2 | 第一次重复声明同一文件，第二次猜错分隔行；读取实际小段后合并为单一精确补丁 |
| zsh 对不存在的 MAVEN 路径空 glob 报 `no matches found` | 1 | 不重复 glob；改用 `find -print0` 枚举实际文件并成功取得 stats/hash |
| LLMERE evaluator 在 shared tools Python 缺 `sklearn` | 1 | 不安装依赖、不原样重试；改用项目 `uv` 环境，并先处理 29,080 vs 29,079 row 差异 |
| `wc -l` 显示 LLMERE prediction 少 1 行 | 1 | 用 Python `splitlines()` 核对为 29,080 records；末行无 newline，非数据缺失；evaluator 随后成功重放 |
| G 收尾状态补丁未匹配 `findings.md` 的实际空格 | 1 | 补丁原子失败、无部分写入；读取实际尾部后改用精确上下文 |
| Web 工具直接打开 TCT ACL 页面/software.zip 返回空结果 | 1 | 不据空结果判断附件不可用；下一步改用 `curl` 下载官方 attachment 到 `/tmp` 并校验 ZIP |
| TCT software.zip 的 `curl` 超过 30 秒工具返回窗口 | 1 | 下载进程仍 ALIVE，已有 573,440-byte partial file；不重启第二份下载，改为监测原进程完成后校验 |
| 枚举 `/tmp/tct-audit.*` 时 `find` 触及 systemd-private 目录报 permission denied | 1 | 已取得目标目录；后续只检查显式 `/tmp/tct-audit.llIu7V`，不再广泛遍历 `/tmp` |
| Claude 五路探索均因会话额度耗尽终止，报告未落盘 | 1 | 本轮重跑并让每路直接写入持久化路径 |
| A 全块任务长期运行且两次落盘指令均未得到响应，目标文件仍不存在 | 1 | 中止大任务；同一代理改按 A1/A2/A3 小块串行，每块完成即持久化 |
| 对未跟踪报告运行 `git diff --check` 会空通过 | 1 | 改用 `git diff --no-index --check /dev/null <file>`；清理已发现的尾空格 |
| DR-B Markdown 导出保留 140 个会话内部 citation token，且无原始 HTTPS 来源 | 1 | 改查 ChatGPT 导出的 PDF；PDF 文本层和链接注释可恢复真实来源，暂不要求重跑/重写 DR-B |
| Web 工具对 CodaLab/ACL/LDC 的直接打开和定向搜索均返回空结果 | 1 | 不重复空调用；改用 `curl` 读取官方页面，并用 PDF 文本抽取核论文附录 |
| 用 `rg -h` 汇总 ACL HTML 元数据时触发帮助页（本机 `-h` 是 help） | 1 | 文件已下载成功；改用 `rg --no-filename`，不重复下载 |
| `paper-search` 的 Semantic Scholar 无 API key 检索触发 429 | 1 | Crossref/OpenAlex 仍返回结果；后续已知论文直接使用 ACL Anthology 官方页/PDF，不重试 Semantic Scholar |
| `B_datasets_audit.md` 首次 whitespace gate 报两处 Markdown hard-break 尾空格 | 1 | 改用空 blockquote 行分隔，再重跑完整校验 |
| DR-C 四篇 ACL PDF 批量下载/抽取在 30 秒边界内无输出 | 1 | 不原样重试；检查临时目录已完成文件，改为复用缓存并逐篇小批核验 |
| LLMERE clone 后串接 MMD-ERE PDF 下载再次触及 30 秒边界 | 1 | 保留已完成的 LLMERE 静态证据；不再下载 MMD PDF，改查现有文件/ACL HTML 元数据与报告边界 |
| MMD-ERE 残留 PDF 缺 trailer/xref，`pdftotext` 无法读取 | 1 | 不作第三次下载；以 ACL 官方元数据确认发表/作者，代码与硬件状态降为“未取得” |
| C 交付校验因命令包含清理临时文件的 `rm -f` 被安全策略拒绝 | 1 | 未执行删除；改用不创建临时文件的只读管道重跑完整校验 |
| C 外链校验复用了 zsh 只读特殊变量 `status` | 1 | 文档结构检查已通过；变量改名为 `http_code`，只重跑未完成的外链与 Git 状态检查 |
| C 的 11 条 ACL 外链串行校验在 30 秒边界只完成前 8 条 | 1 | 前 8 条均为 HTTP 200；不重跑，仅检查剩余 3 条和 Git 状态 |
| 剩余 ACL 外链续查遇到 `SSL unexpected eof while reading` | 1 | 不重复网络请求；三页已在本轮成功下载并解析官方元数据，改验本地页面完整性 |
| E 官方页面批量打开及定向检索均由浏览工具空返回 | 2 | 不据此判页面失效；改用轻量 HTTP 抽样，仍失败则降低时效性结论等级 |
| 审查整改的大补丁两次因目标段落实际换行与预期上下文不一致而拒绝 | 2 | 两次均原子失败、无部分变化；读取精确片段后缩小 hunk 并成功写入统计聚合、证据边界与 Ch4 跨 arm checkpoint 规则 |
| 跨文档策略断言未命中 Ch4 checkpoint 规则 | 1 | 文本规则实际存在，仅因 Markdown 换行拆开关键短语；调整换行后重跑原断言，不降低检查项 |
| 最终状态核对命令在双引号中包含 Markdown backticks | 1 | zsh 将其中 `failed|blocked` 误作命令并报 command not found；状态输出已足够，不重跑原命令，后续 shell regex 不放 backticks |
| 终局 legacy-token 检查误把修订前独立报告正文当 active policy | 1 | 历史报告已在顶部明确 superseded 边界；保留原始证据，改为仅对 SPEC/EXPERIMENTS/TODO/active phases/G0 扫旧指令 |
| 补写官方 loader 核验结论时 `findings.md` 上下文未命中 | 1 | 补丁原子失败；读取实际尾部后改用精确锚点，未丢失或覆盖既有记录 |
| 同时更新 findings/progress 时误判 `progress.md` 日期标题格式 | 1 | 补丁原子失败；读取实际尾部后用“执行 P1”段落精确追加，既有内容未变化 |
| 首次 freeze 在统计 temporal mention-pair support 时未把 TIMEX 加入 endpoint map | 1 | 脚本 fail-fast，尚未写 registry；仅在 temporal 支持统计局部加入 TIMEX singleton 后重跑，不改变 split 或候选协议 |
| 核官方 causal model 时猜错路径为 `causal/src/utils/model.py` | 1 | `sed` 只报该文件不存在，其余只读输出完成；后续按实际 `causal/utils/model.py` 路径读取，不改 source |
| 第二次仍把 causal shared model 猜成 `causal/utils/model.py` | 2 | `find` 证实 causal 子目录仅有 main/src；按 `sys.path.append('../')` 改查 checkout 顶层 `utils/model.py`，不再猜路径 |
| 首次应用 official compatibility patch 报 `corrupt patch at line 16` | 1 | `git apply --check` 原子失败、external source 未改；修正两处手写 unified-diff hunk 行数后再检查，不绕过 patch gate |
| 第二次 patch check 报 `corrupt patch at line 34` | 2 | external source 仍未改；用带行号视图核出 joint import hunk 实为 11 行并修正 header，继续保留 `git apply --check` 硬门 |
| 第三次 patch check 报 `corrupt patch at line 57` | 3 | external source 仍原子未改；两份 EventEncoder hunk 各为旧 10/新 6 行，修正 header 后再次检查；未绕过完整性验证 |
| 第四次 patch check 仍报 line 57 | 4 | 复算发现先前漏计 replacement 行：新 hunk 为 7 行而非 6；把两处 `+...,6` 更正为 7，source 仍未发生部分修改 |
| patch 语法通过后四个 hunk 均报 does not apply | 5 | `file` 核实官方三文件为 CRLF；`git apply --ignore-space-change --ignore-whitespace --check` 通过，应用器固定这两个仅处理换行/空白的参数，不使用 reject/模糊部分应用 |
| 首轮新增文件 ruff 定向检查报 11 项格式/未用 import | 1 | 31 个功能测试已通过；按 ruff 原报告逐项做纯机械修复，不改协议语义，随后重跑同一 gate |
| P1.6 首次 4090 只读资产核验在 SSH 握手阶段被 peer reset | 1 | 未建立会话、未运行任何远端命令，也不推断 GPU/进程状态；记录为连接失败，使用短 ConnectTimeout 原样重试一次只读核验 |
| P1.6 第二次 4090 只读 SSH 在 banner exchange 超时 | 2 | 仍无远端命令执行；不把全局协议降级，先完成 conditional P1 bundle 与最长 fixture，稍后再做第三次连接审计 |
| P1.6 第三次 4090 SSH 仍在 banner exchange 超时 | 3 | 本轮停止重复连接；保持 global=pass/A3=conditional，不访问需授权的 5090，不伪造远端 smoke；将唯一 remaining condition 写入 bundle/TODO |
| 作者确认可 SSH 后，Codex 环境首次恢复审计仍在 banner exchange 超时 | resumed-1 | 远端命令仍未执行；不机械重试，先只读核本环境 `ssh -G` 解析结果与目标端口连通性，比较是否为执行环境/隧道差异 |
| 分配真实 PTY 并放宽等待后仍在 kex 前被 cpolar peer reset | resumed-2 | 排除 exec 无 TTY/15 秒超时；不再重复同 endpoint 连接，转查本机 SSH 配置是否存在 4090 的备用 alias/跳板路径 |
| 恢复诊断记录补丁两次因猜测跨文件上下文未匹配 | 2 | 两次均原子失败；拆成单文件精确补丁，不影响实验/协议文件 |
| 活动 socket/DNS/SSH 配置对比未找到可复用会话或备用 4090 路径 | resumed-3 | 用户此前成功的 SSH 已结束且无 ControlMaster；DNS 仅有 `49.233.190.64`，唯一 alias 仍为 cpolar `:14147`；继续核 cpolar 单连接/短时抑制并尝试显式连接复用 |
| 显式 ControlMaster 前四次 banner timeout | resumed-4 | 第五次成功建连，证明 cpolar 入口间歇性丢 banner；后续命令固定复用 `/tmp/ekg-gpu4090-%C.sock`，避免重复握手 |
| P1.6 4090 只读资产核验 | pass | 4×RTX 4090 均空闲；`supervised_maven` checkpoint 三件套存在并取得 SHA-256，CUDA 可用；首选 `window_dist_20ep_macro` 不在本机，故只做兼容 smoke 并显式降级说明 |
| P1.6 远端代码/运行时核验 | pass | 远端与本地均为 commit `c642bb88`，远端工作树 clean；torch `2.8.0+cu128`、transformers `4.53.3`、CUDA available；CLI 支持 lexical coref + supervised relation checkpoint |
| P1.6 契约检索附带了不存在的 `baselines/summary.json` 路径 | 1 | `rg` 对现有契约/构建器的读取仍成功；不再猜文件名，后续按已知 fixture 文件与构建器 schema执行 |
| P1.6 fixture 传输与双端 hash | pass | 10-doc 与 longest fixture 已经由 ControlMaster `scp` 到 P1 remote_smoke/input；SHA-256 分别为 `1aafea51…` 与 `bafebc39…`，双端一致 |
| P1.6 真实 4090 checkpoint forward | pass | GPU 0 上 longest 1-doc（226 relations）与 frozen 10-doc（1,861 relations）均 strict-load/forward 成功，return code 0，无 skip/OOM；待回传并做本地 strict schema/hash 验证 |
| 首次 metadata hash verifier 遍历 `inference` 的全部 values | 1 | 把字符串配置项误当 run dict，触发 `TypeError`；bundle 构建与独立 reader 校验随后仍成功，下一次仅显式遍历 `ten_document`/`longest_internal_dev` 重验 hash |
| P1 bundle 重建与 reader 重读 | pass | `global_protocol_status=pass`、`a3_entry_status=pass`、`remaining_condition=null`，remote smoke pass 且 `scientific_scores_produced=false` |
| P1 最终一致性与本地三件套 | pass | bundle/registry/artifact hashes、活动阶段、链接与 whitespace 全部通过；pytest 364 passed/12 expected skips，ruff clean，ekg-smoke OK；ControlMaster 已正常关闭 |
| Phase 13 初始 bundle inventory 请求了 `hashes.json` | 1 | P1 契约是四件套，hashes 内嵌 `protocol.json`；前九份 JSON 均已读取，停止请求不存在的第五文件，不据此判 bundle 缺失 |
| pair-order/rejection audit 把 fixture ID 猜成 `d1` | 1 | pair-order 全量断言已先通过，但拒绝测试在 mutation 前 KeyError；读取真实 ID=`p1-fixture`，改为从 gold 动态取得 ID 后只重跑未完整输出的组合审计 |
| 临时 baseline replay 的 `cmp` 循环未启用 fail-fast，summary 差异后仍返回 0 | 1 | 十份 fixture/prediction/smoke 均静默 cmp 通过，仅 summary 在 byte 129 不同；不把整条命令误判为全同，下一步读取结构 diff 并以字段级比较判断是否仅临时绝对路径 |
| 首次跨 6 文档状态补丁在 G0 锚点写成 `static` 而非实际中文 `静态` | 1 | 整个补丁原子失败；拆成单文件补丁后完成 PHASE_P1、TODO、phase index、G0、AGENTS/CLAUDE 同步 |
| 端口诊断误用 Bash 的 `/dev/tcp` 于 zsh | 1 | SSH alias 已成功解析为 `18.tcp.vip.cpolar.cn:14147`；zsh 不支持该伪设备，不重复该方法，改用系统 `nc`/`timeout` 做 TCP 检查 |
| Phase 13 收尾合并 patch 猜错 task-plan 条目措辞 | 1 | patch 原子失败、findings/progress/task-plan 均未部分改写；先分离记录结论，再读取真实 Phase 13 段落后精确更新 |
| scorer provenance 首测把 10-doc fixture gold 与 full-split `gold_prediction.jsonl` 配对 | 1 | strict ID-set gate 正确拒绝；不放宽 scorer，改为从同一 10-doc gold 动态生成 gold-self prediction fixture |
| 记录上述错误时猜错 task plan 的错误章节大小写/位置 | 1 | patch 原子失败；用 `rg` 找到实际 `## Errors Encountered` 表格后精确追加 |
| gold-self scorer 测试对浮点 100 使用精确等号 | 1 | evaluator 打印为 100.00 但内部浮点有舍入尾差；改用 `pytest.approx(100.0)`，不修改指标实现 |
| A3 launcher 首次定向 ruff 命中 UP022 | 1 | GPU preflight 同时显式设置 stdout/stderr PIPE；改用等价的 `capture_output=True`，不改变执行语义 |
| 扩展 P1 `CODE_PATHS` 时依据先前截断输出误判 baseline metadata 有重复行 | 1 | 多文件 patch 原子失败；用 `rg` 确认实际仅一行后只修改真实需要的 builder 列表 |
| 更新 scorer 帮助示例时未匹配源文件中的双反斜杠字面量 | 1 | patch 原子失败；用 `sed -n l` 确认实际转义后改为不依赖反斜杠上下文的单行替换 |
| 首次全量 ruff 发现 candidate summary 内嵌函数闭包触发 B023 | 1 | 把 label expansion 提为显式参数的模块级 helper，消除对循环局部变量的迟绑定风险 |
| 协议重冻结后的首次 local gate 有 4 个 trainer 测试依赖 registry 已 PASS | 1 | 暴露了“测试要求 bundle 已建、builder 又要求测试先过”的循环；测试改用最小临时 ready-registry + 真实冻结 manifests/candidate，生产 validator 仍要求真实 PASS/v2 bundle |
| A3 本地 precheck 混用了远端 Python/CWD 与本地格式化的 run-dir | 1 | 不执行 GPU；把每个远端 run-dir 和 remote preflight 冻结进 execution plan，precheck 显示全远端自洽路径，`--execute` 额外要求实际 preflight 路径等于计划远端路径 |
| 路径回归测试把 `_commands()` 的子字典直接传给需要完整 plan 的 helper | 1 | 生产代码未失败；测试包装为 `{"commands": plan}` 后重跑，不改变 launcher API |
| 文档漂移 `rg` 命令在双引号模式中包含 Markdown 反引号导致 zsh 引号解析失败 | 1 | 命令未执行、无文件变化；改用多个单引号 `rg -e` 模式，避免 shell 解释 Markdown 字符 |
| 最终信任链复核发现 A3 plan 命令字段没有 bundle 外预期 hash | 1 | 无 GPU 运行受影响；materializer 改为打印 plan SHA-256，launcher 强制显式传入并同时要求 source/data 文件集合精确相等，随后重建 P1 trust root |
| Phase 14 builder 首轮定向 ruff 报 5 个 E501 | 1 | 均为新加严格证据断言的机械换行问题；不改验证语义，拆行后继续同一组定向检查 |
| 新 builder test 定向 ruff 报 I001 import order | 1 | 12 个功能测试已通过；仅对该测试运行 ruff 自动排序 import，不手改功能代码 |
| 首次选择性暂存把原始 Deep Research 导出一并纳入，`git diff --cached --check` 报保留的 Markdown hard-break 尾空格 | 1 | 不机械改写原始研究导出；将 raw reports 从提交边界移除，只保留经本地审计的决策文档和当前可执行契约 |
| 记录上述暂存错误时错误表锚点大小写不匹配 | 1 | 补丁原子失败、无文件变化；读取实际尾部后以精确中文行锚定 |
| Phase 15 证据解包/P1 validate 的首个 SSH 在 banner exchange 超时 | 1 | 远端命令未执行，不判解包或验证失败；改用唯一临时 socket 的显式 ControlMaster 有界建连，成功后通过复用连接执行原工作负载 |
| Phase 15 显式 ControlMaster 的 5 次有界握手均在 banner 前超时 | 5 | 停止继续重试同 endpoint；归档已在远端 `/tmp` 且代码已同步，转查可复用会话/socket 与 TCP/banner 状态，不访问 5090 |
| cpolar 冷却 45 秒后的单次 60 秒 ControlMaster 在 kex 前被 peer reset | 1 | 仍无远端命令执行；改为至少 55 秒间隔的低频监测式重连，成功即持久复用 socket，不再突发握手 |
| 远端 clean `53ce6f1` 解包 r3 后 `--validate-only` 报 `local tested file count drift` | 1 | protocol hash 正确；定位为 r3 local gate 绑定了本地 dirty 树的全局 Python 文件数，选择性提交后不可移植。不得夹带旧 Ch1 修补数字；改为绑定受控代码身份并在 clean 提交口径重建新 trust root |
| clean-worktree 数据依赖 `rg` 命令的嵌套单双引号不匹配 | 1 | zsh 在执行前拒绝，未读写文件；改用多个简单 `rg -e` 模式，不在一个 shell token 中嵌套两类引号 |
| 检查 r3 protocol 外部路径时错误假设顶层键为 `artifacts` | 1 | 只读脚本触发 `KeyError`、无文件变化；先打印实际 schema keys，再按 `artifact_hashes` 等正式字段枚举 |
| clean-worktree 前置检查错误假设本地存在远端 `a4090_ctrl_accum1` checkpoint | 1 | 只读 `du` 报路径不存在；确认 checkpoint 类不在 `local_hash_categories`，由 remote evidence snapshot 证明，不搬运或伪造本地权重 |
| 三路远端 no-execute 的 JS 命令组装错误拆分 `bash -lc` 参数 | 1 | 三路均在错误 cwd 立即报 `.venv/bin/python` 不存在，未启动进程；去掉多余 `bash -lc`，让 SSH 直接执行单引号内完整 `cd /data/TJK/ekg && command` |
| 收尾 `pgrep -af` 模式把包含该模式文本的审计 shell 自身列出 | 1 | GPU 仍 0% 且无产物；改用 argv 必须以项目 `.venv/bin/python` 开头的锚定模式，避免自匹配 |
| 在最终两文件远端状态记录提交前关闭了 ControlMaster | 1 | 远端只少纯文档提交、Python/产物不受影响；重新建立一次持久连接，仅 fetch/reset 到最终 docs HEAD 后关闭 |
| 最终 docs-only 远端同步的首次 ControlMaster 在 kex 前 reset | 1 | 无远端命令执行；因仅差文档 HEAD，采用最多两轮、55 秒间隔的低频重连，不触碰已验证产物 |
| Phase 16 首个复合 readiness 命令在 HEAD/clean 后 exit 1，但成功项无标签 | 1 | 只读且无进程启动；不能猜 run-dir 或 model 哪项失败，改为逐项打印 `PRESENT/MISSING` 与独立环境状态，不原样重试 |
| Phase 16 远端模型 cache 搜索在 kex 前被 cpolar reset | 1 | 远端命令未执行，不能把空输出判为无 cache；改用 55 秒冷却后的持久 ControlMaster，成功后复用同一连接完成搜索 |
| Phase 16 模型 cache 搜索的两轮低频 ControlMaster 仍在 kex 前 reset | 2 | 停止同 endpoint 重试；已知冻结路径缺失不变，转查本地 WSL 是否有完整 cache，准备可校验传输方案但不擅自下载/写远端 |
| 本地 PyTorch scatter 最小探针报 `ModuleNotFoundError: torch` | 1 | 项目本地环境按约束不承担 GPU 且未安装 torch；不临时污染依赖。改为逐行核对实际 wrapper 边界，确认非张量 spans/splits 不进入 DataParallel，后续只在远端做一批次真实 smoke |
| Phase 16 第二轮远端 cache 搜索仍在 banner exchange 超时 | 1 | 远端 `find` 未执行，不判断 cache 缺失；已知冻结的显式路径不存在已足以作当前 NO-GO，停止连接重试并将 cache 定位/模型固化列为修复任务 |
| Phase 17 本地 source 搜索包含不存在的 `data/protocols/v6/baseline_sources` | 1 | `rg` 对该单一路径报不存在，其余目标正常返回；实际 pinned source 位于 `data/protocols/v6/sources/MAVEN-ERE` 与 A3 preflight 副本，后续只使用已核实路径 |
| Phase 17 使用真实 TTY 的 `/data/TJK` 只读 SSH 仍在 kex 前 reset | resumed-1 | 精确 alias/user/port/key 已核对，远端命令未执行；不原样重试。检查本机现有 SSH process/socket，未发现可复用连接，故保留“隧道拒绝本执行环境新连接”基础设施状态，不将其升级为实验 NO-GO |
| clean r5 worktree 首次 `uv run pytest` 因新建最小 venv 缺 `networkx` 在 collection 失败 | 1 | 代码尚未进入测试，失败是 clean worktree 首次 uv 环境未同步项目所需 extra，不是实现回归；先读取 `pyproject.toml`/`uv.lock` 的既有依赖组，再用仓库约定的 uv 同步方式补齐，不用 pip |
| r5 跨文档身份更新补丁因 TODO 现有换行与预期不一致而原子失败 | 1 | 无文件产生部分修改；先读取六个目标文件的精确段落，再拆成小补丁，避免大补丁任一锚点失败影响全部同步 |
| Phase 18 首次同时更新三份 planning 文件时误用模板尾行作为 `findings.md` 锚点 | 1 | `apply_patch` 原子失败、三文件均未改变；改为先读取真实尾部，再拆分精确补丁。 |
| 4090 `hold-4090.sh` 首次握手未连上，工具在 30 秒先返回但脚本仍在后台重试 | 1 | 远端审计命令未执行；核对脚本与本地进程，确认它按 40 秒间隔有界重试且 TCP 可达。保留进程等待复用 socket，同时继续本地实现。 |
| Phase 20 首次同时更新三份 planning 文件时误用 `findings.md` 尾部锚点 | 1 | `apply_patch` 原子失败、三份文件均未变化；读取各文件真实尾部后拆分为精确补丁。 |
| Phase 20 首次 `gpu-5090` 只读核验被 `29.tcp.cpolar.top:12337` 拒绝 | 1 | SSH 明确返回 `Connection refused`，远端命令未执行；本机配置只有这一入口且无可复用会话。停止原样重试，继续本地方法筛选，等待入口恢复或用户提供新端口。 |
| prototype 定向 gate 并行运行时 CLI help 无法获取 uv cache lock | 1 | 测试与 ruff 已通过；失败是并行 uv 争用只读默认 cache，不是代码错误。仅用独立 `UV_CACHE_DIR=/tmp/ekg-prototype-uv` 重跑未完成的 CLI help。 |

## Authoritative Context

- 任务边界与中断状态：`docs/replan/HANDOFF.md`
- 探索问题与证据规则：`docs/replan/EXPLORATION_PROMPT.md`
- 本地资产盘点：`docs/replan/LOCAL_ASSET_INVENTORY.md`

## 独立审查阶段结论（2026-08-27）

- [x] 引入一名独立审查者，限定为只读审查与单一报告交付
- [x] 核验数据、指标、baseline、零人工标注、算力与跨章闭环
- [x] 生成 `docs/replan/INDEPENDENT_THESIS_FEASIBILITY_REVIEW.md`
- [x] 主代理用 `docs/results/` 对关键实测数字交叉核验
- [x] 按审查结论修订主方案的实施顺序、章节定位和阶段停止条件

**当前阶段：Phase 19 进行中 — 单种子优先、不同任务 GPU 并行；禁止未授权多种子。**

- [ ] GPU0：等待 r13 seed-13 完成，并以 official evaluator 核验三族主指标与护栏。
- [x] GPU1：Stage-1 retriever seed-13 完成，recall@15=.8691、跨句=.8273，未过门；停止 r1，不接 Stage 2。
- [x] GPU1：r2 marker-sentence seed-13 完成，recall@15=.8543、跨句=.8035，未过门；停止 r2。
- [x] GPU1：r3 最终 recall@15=.8749、跨句=.8299，未过门；停止 retriever 线，不跑 r4/额外 seed。
- [ ] 低频恢复 4090 SSH 后补核 r3 metadata/checkpoint hashes，并继续监测 GPU0 official 流水线。
- [x] 核对 Ch3 并行边界：D3 受 A3 immutable handoff 约束，当前不启动无法进入结论的正式 GPU 任务。
- [ ] 仅在两个单种子结果均核验后决定下一方案；未经用户再次授权，不运行任何多种子。

### Phase 20: 5090 临时单种子方法探索

- [ ] 只读核验 `/mnt/aidata/tongjiakai/ekg` 的 commit、工作树、GPU、磁盘、模型和数据资产。
- [ ] 对齐本地 P1 r12、A3 r13、冻结主锚与 5090 可复用资产；任何漂移先修复，不直接开跑。
- [x] 结合 Ch2 已测错误结构与一手论文，筛出最多两个互补方案；排除已证否方向和重复造轮子。
- [ ] 每个方案先写已知答案测试、变异/符号断言与 2 epoch CUDA smoke，验证机制确实按设计工作。（本地测试已完成；远端 mutation/CUDA smoke 待入口恢复。）
- [ ] 只运行冻结 seed 13；若 GPU 允许，可并行不同方案，但不得并行额外 seeds。
- [ ] 使用 official evaluator 报 causal/subevent/temporal，并与 33.17 / 28.75 / 50.63 门逐项核验。
- [ ] 将实测数字、命令、commit、checkpoint 所在服务器与负结果写入 `docs/results/PHASE_A.md`。
- **Status:** in_progress
