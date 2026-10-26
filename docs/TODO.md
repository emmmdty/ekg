# EKG 实时状态

> 更新于 **2026-10-24**。新会话先读 [`HANDOFF.md`](HANDOFF.md)，再读唯一权威计划
> [`EXPERIMENT_PLAN.md`](EXPERIMENT_PLAN.md)；数字以 [`results/`](results/README.md) 为唯一事实源。

**最新：R109已闭合，接R110**：完整train零更新预测和另一实现计数完成，未重训或搬权重；
fit/dev落差和限制只见R1 §25.130。当前train-only词面对照×句距分层既有full/joint dev
预测，并核最近邻机制；范围见主表/R1 §25.131，不把诊断当新贡献。作者已说继续，工具
仍paused，按会话继续、不冒称自动active；O1–O4未完成。

**10-25验收/裁决**：三项完整训练及R107独立重载已过，全部classes/官方分数一致，
R108预定区间和错误交换及另一实现复核完成；无确认的主指标收益或新方法贡献（数字
只见PHASE_A末节）。固定三臂不重起/扫参/扩seed，Goal active、三个科学O未达。
当前同队接R109：原full冻结选中权重的train native三类拟合诊断；尚待薄入口/CPU门/
完整人口/预算与命令披露，不是已执行。依据R1 §25.129–§25.130与主表最新段。

**10-24三卡并行**：作者要求其他卡同步推进；R105原论文两项控制的CPU/CUDA/初始参数
同一性门已过，R106预算/对照/配置冻结后，卡0 complete_graph25466、卡2 gamma0
25461已进入完整seed13首epoch，卡1原full13841继续。详细状态/成本只见R1 §25.128，
下一各自完整20epoch及原机独立重载/official/paired分析；不增seed、不改原full、不拿已知
消融当创新。卡3留余量，未准入D4/C5不因空卡直接开训。

**10-24作者恢复4090**：实际核无compute-app，沿当前C41-A-R冻结主机独立成本配置/
合同，卡1/2/0并行原三个病例、两次lr0各例；不重做已闭合CPU准备，成本后仍须容量/
production/完整预算才能训练。R1 §25.125记录实际门/运行；此段覆盖下方旧资源出口。
Goal工具仍旧blocked，执行按作者继续指令，不声称工具active或创建替代目标。

**10-24完整训练接续**：R102成本与R103实际CUDA原函数/驻留最大dev均完成、exit0/
GONE，证据只见R1 §25.125–§25.126。R104预算与对照首评分前冻结（§25.127），当前
按4090正式合同接原ERGO完整seed13 baseline；full4096/float32/全候选/20epochs保持。
完成后原机独立重载官方核分/配对残余；不扩seed/机器/final-valid，不以已知方法算创新。
正式训练PID13841实核ALIVE、首epoch运行中；暂无完整epoch分数，勿重复启动（R1 §25.127）。

**10-19本轮出口**：当前独立CPU切片已收口，两机成功SSH实核仍无空卡、无本项目ERGO
worker或CUDA报告；本回合无新科研进展。相同资源阻断已跨三个Goal回合，阻断审计见
R1 §25.124，提交后按工具契约转blocked，最终返回认线程记录。C41-A-R/T087保持wip，
科学目标未完成；恢复时接既有成本，原许可保留，无自动等卡器。

**10-19续令已执行**：已把现在CPU可做与GPU恢复后的实验对照/依赖/护栏/失败分支写入
主表及[既有OKR卡](research/20261016_project_okr.md)，并完成R100 train冻结预测方向/
subtype分解与守恒复算（R1 §25.122）。不支持以纯方向/已输出边类别修复作为主要瓶颈
立项；不推广为held-out因果结论。Goal本线程已按授权建立、实核active；唯一C41-A-R
不变，CPU分析器可复用于ERGO结果，下一GPU仍既有成本合同。此续令覆盖下方10-18仅收尾，
不重跑封存CPU准备或自动等卡。

**10-19接续R101完成**：固定train原文案例及标注定义/直接机制邻居已核，结果R1 §25.123；
SemDI仅新增真实实现可得性，native输入/选模/成本未闭合，CaSR当前只公开部分数据。
不据类型表面异常/世界知识改gold，不将已知语义模块换名准入；无新分数/训练。当前独立
CPU切片收口，必要GPU动作保持。两机本轮SSH均通但有现存任务，无成本启动/等卡器。

**10-19质量与完成度核查**：作者要求最终质量、实验设计与结果优于四篇CAJ硕士论文。
原件转换/核心方法与主表核读已完成，参照、局限和当前差距见
[`质量对照与实验树`](research/20261019_thesis_quality_and_experiment_tree.md)、R1 §25.120–§25.121。
三个方法正向贡献仍均未过门，E3仅既有首轮/历史v5上游；不报无依据的完成百分比。
PPAT/iLIF固定源码静态核查和H2失效前提对齐已完成，不新增baseline运行、训练准入或
E3实验。当前唯一C41-A-R不变，下一实质执行仍是核空卡后既有ERGO成本合同。

**10-18阶段收尾**：作者确认无空卡并要求完成本轮收尾。CUDA preflight/选中checkpoint
独立复算的软件入口及非有限梯度范数fail-fast已落地，CPU验证/限制见R1 §25.116–§25.117；
真实CUDA和checkpoint重载尚未执行。新审查配置为`ergo_native_training_unadmitted_v2_close_20261018.json`，
三个admission仍false。当前C41-A-R/T087保持wip，已授权5090成本留待空卡后接续，许可无需重复问。
本轮结束不表示科学Goal完成，不启动等卡器或新研究任务。

**新窗口执行方式**：作者明确要求使用长期Goal。先按HANDOFF §0.0核本线程目标、
创建/接续并确认活动状态，再从C41-R连续推进；阶段汇报/提交/候选失败不结束总目标。
本线程已创建长期Goal；作者报告客户端active，工具仍返回usageLimited，按作者继续指令执行。C41-R/B/A/T/V已完成，C5固定exact候选科学门FAIL并停止（PHASE_C末节/§25.82）。D4当前绑定模板R1未准入；原train重放/输入可见性已闭合，未启动拟议方法训练（§25.83–§25.86）。当前正式C41-A-R，复用native多原因/coref重复与普通SupCon；ATLOP/DCL/None边界已核（§25.87），身份/MIL与原生邻接审查已闭合（§25.88）；全train原机CPU重放/双端official复算已完成、PID1657823核GONE（§25.91）；关闭当前目标模板准入回合；上下文诊断也已闭合（§25.93），ERGO全train容量/来源审查已闭合（§25.95），透明接口/原机权重及cache-global输入已闭合（§25.97），完整CPU短文已过（§25.99），PAD-only最大候选未过梯度门并停止（§25.102），原完整padding CPU形状已闭合（§25.105），internal-dev无标签输入已闭合，原函数toy及真实CPU trainer/最大dev smoke已闭合（§25.111/§25.114），v2入口默认未准入（§25.115）；本次5090成本已获许可且输入/权重就绪，空卡受阻；无epoch/新方法训练。
证据见R1 §25.68–§25.72；固定seed13五臂已准入，科学KR尚未达成，无新增资源授权。

**10-16最新覆盖**：作者确认4090恢复，要求整体目标→OKR→任务→证据的项目管理。
4090回主执行机；C41-R原机hash/源码与未跟踪保全完成，B实际成本/完整预算完成（§25.69），当前
A设计/生产/真实测试/正式合同完成（§25.72），T/V完整负结果及D4当前模板R1已裁决，当前A4-R。原5090迁移S deferred；
既有许可不变、不搬checkpoint。主表§3.9/§4为唯一队列，
[项目OKR](research/20261016_project_okr.md)给三章KR/时窗，事实R1 §25.66。
D4当前模板未准入，A4当前正式研究；E3不加实验，单seed/封存/资源边界保持。
下方历史工程记录不覆盖本段，不把准备完成当最终指标达成。

**本次接续（作者要求实际结果）**：固定双向、frozen-null、forest posterior-score、同head decision-unit与first-dummy适配五类控制均完整实测/独立复算，没有突破，固定动作全部停止（§25.44–§25.50）。原joint首提及dummy目标盲区真实存在，但修正适配没有部署收益；不扫预算挽救。当前C-41为exact joint结构学习R1：完整train机会、真实模型梯度、covariance分解与总概率量匹配rival已核（§25.49/§25.52），前瞻功效敏感性完成（§25.51）。数学/条件power不是MAVEN提分；原tokenization census与两组固定输入的完整四头CPU反向/checkpointing梯度等价均完成（§25.53–§25.54）；五臂loss/固定endpoint/最坏已观测噪声的条件power规划假设已绑定（§25.55）。本次已继续完成LOCAL隔离CPU的固定aux数值/求导边界与全train label/构造先验风险审查（§25.56–§25.57），均不构成模型提分。新增common-bias/逐候选审查与5090完整输入等价/原CPU重计算完成（§25.58–§25.60）；真实四aux的head/encoder梯度连通性及量级审查已完成（§25.61），参数未更新、尚未分辨exact独有收益。原架构两fixture CUDA parity/峰值已complete（§25.62）；结构目标/真实optimizer CUDA与accumulation4/全train保守预算现已完成（§25.69）；原CPU失败封存，正式生产/合同已完成（§25.72），method仅准入seed13探索，当前T/V，未获科学收益证据。以上为C5执行史；最新T/V已完成、固定候选停止（PHASE_C末节），D4当前模板R1也已拒绝准入，当前正式A4-R。

## 当前正式活动阶段

**当前任务是三个方法章的根因与效果改进。2026-10-08 作者已委托执行代理作科研裁决，作者只验收结果。**
C-35/C-36 完成；C-37 诊断选择、C-38 诊断实现完成，C-39 **D4 CUDA passed / C5 smoke passed、audit pending / A4 pending**。
G-22 D4 十折训练、CPU 配对汇总与对应 C-40 裁决已完成：linear 重现强对照，tanh5 退化，
不推进五维头；后续保留 linear 匹配控制。A4/C5 权重仍在 5090，C5 smoke 已执行，完整诊断仍待验证。
合同见 `phases/PHASE_recovery_validation_20261008.md`，启动身份见 §25.36，最终结果见 `results/PHASE_R1.md` §25.37。
ESC 退出本轮硬前置；不换 MAVEN 主任务、不重写旧失败数字、不开未准入 GPU 实验。
科研选择不再等待作者；5090/跨机 checkpoint/额外 seeds 的资源边界保持。
10-12 路线评估已入 `HANDOFF.md` §0.3.4：旧机制停止续修，有限诊断与新方法贡献分开；
作者随后明确要求逐章执行；主表 **C-41 / T087 为 wip，当前 A4-R（C5固定候选/D4当前模板已裁决）**，顺序 C5 → D4 → A4。
先核可靠控制与时间身份候选的信号可行性，再形成实质不同的方法合同；诊断不等于提分。
A4 GPU 待授权、C5 audit 等空卡不是文献/CPU 研究硬前置；尚无新机制准入或训练启动。
研究卡 `research/20261012_chapterwise_optimization.md`，证据 `results/PHASE_R1.md` §25.38 起。
C5 DATE 词面代理和已有强锚 BEFORE/coref 冲突两项 CPU 审查已完成，均不支持直接硬规则准入。
作者已具体批准 C5 原机 decoder smoke/audit 仅空卡执行；首试被 occupancy 门拦下，
重新空卡后的 smoke 已 complete、average parity/六文件 hash PASS；下一步完整 audit，不复跑 smoke。
有界空卡等待已结束，无遗留自动启动 watcher；接续核空卡后直接执行已授权 audit。
尚无新方法训练或创新贡献；C5 已知规则的控制提分见 §25.42。A4 的 5090 授权不在这次批准内。
作者要求持续推进至突破；C-41 保持活动。FACT/ERE train 事实性信号已审查，直接硬规则不准入；
仅 C5 train 的固定单 seed CPU 文本观测诊断已完成，覆盖低且稀有类别弱；
该早期审查见 §25.39；控制缓存与后续诊断现已完成，接续以 §25.40–§25.42 为准。
旧 D4 OOF 输入不能直接接入新 C5 consumer；这不改写 D4 自身的结果。
10-13 4090 原地 official-joint CPU 全量 cache 已通过 exact cluster parity，
重放预测与 frozen anchor byte-identical（§25.40）。当前弱 factuality observer 的部署覆盖与
连续几何未支持作用于真实错误，该 observer 路径停止、不调参（§25.41）。
known type-agreement stronger control 已完成固定 CPU 重放/双端评分与配对审查，共指四指标提高，
残余错误 profile 已完成；数字只见 §25.42。下一步据其两方向错误准入独立机制/输入/power；
控制改进尚不是方法创新，当前 C5 切片继续 wip。
新窗口承担科研负责人（PI）/方法审稿/实验执行责任，按 `HANDOFF.md` 角色与 §0.3.5
从 stronger control 的两方向残余错误做最近邻/输入/机制准入，沿用授权，不重跑完成的控制。

10-13 本次接续的最近邻矩阵、train-label scope 和 antecedent 决策/oracle 分解及独立评分已完成
（§25.43、实现 `a6d159d`）；null 边界是主要 gold-conditioned 修复覆盖，未证明部署改进。
普通 newness/singleton、删光 gold 前项→dummy、generic cluster loss 不准入创新；
下一步按 `research/20261013_c5_newness_admission.md` 审 train-only 文档隔离 error-state 输入、
selective/error-correction 最近邻和目标 power。方法训练尚未准入；C-41/T087 仍 wip。
10-14作者新增授权C-41在5090空卡做原joint成本验证及R1准入后五臂seed13训练，单任务≤一天；超过一天/跨机权重/额外seed仍另行授权。成功SSH核卡仍有他人任务，原audit与新CUDA成本均未启动；无等待启动器。


| 项 | 当前状态 | 下一道门 |
|---|---|---|
| G-19 · Ch5 外部 baseline | ✅ 已完成 FR-016(b) 透明适配：2,331 train / 独立 selection-dev / 无标签 291-doc evaluation 的 seed-13 运行，raw cluster、official export 与官方 scorer 的覆盖/候选/评测器闸门均通过；正式数字、singleton 崩塌形态、P/V/U 和禁止论断均在 `results/PHASE_R1.md` §25.28 | 不重跑、不事后调阈值或 backbone；KBP 2017 不可得，故不得以本行评价原论文 |
| C-29.5 · 流程审计 | ✅ 已完成。G-20 的旧配置已证实缺 stop/constrained driver，不能重跑 | `AI_RESEARCH_WORKFLOW_AUDIT.md` 给出角色分离、执行就绪包、工程排障/科研迭代边界与停止规则 |
| C-29.6 · 静态契约核验 | ✅ 已完成并阻断旧恢复规则。11,149 个 target 第三行有 407 种值；C-3 target-third-line stop 不能不用 gold 实现 | 【协议】；作者已取甲，不写/不跑 recovery driver |
| G-20 · Ch4 外部 baseline | ✋ 作者甲收口。LLMERE 保留为 `P 有 / V(b) / U 无分数` 的可得性行；它不是模型低分 | target-dependent stop 是命名协议障碍；不生成、转换或评分 |
| C-30 · 全章 | ✅ 已完成：G-19 raw export 经独立 official scorer 复算一致；LLMERE 无 U 分数已登记 | P/V/U、七项 provenance、FR-016 与 `single-seed / non-confirmatory` 审计见 `results/PHASE_R1.md` §25.29 |
| C-31 · 领域证据地图 | ✅ 第一轮完成：Trucidator、MMD-ERE、rationale-distillation ECR 三卡分别卡【数据+协议】、【协议+代码】、【数据+协议+新颖性】 | `results/PHASE_R1.md` §25.30；`no_admissible_candidate`，不启动 C-32/G-21 |
| C-31b · 外部 benchmark | ✅ 作者已授权一个、且只一个外部 benchmark；ESC v0.9 被 R0 选定为 E 层 causal-existence 验证 | `results/PHASE_R1.md` §25.31；只增外部证据，不替换 MAVEN 主表、不复活 A4 |
| C-32a · ESC 协议预检 | ❌ **`protocol_blocked`【协议】**：ICCL dev/seed/binary scorer 可得，但 document folds 不符 topic-disjoint E 合同，预处理输入未闭合；typed scorer 错误不能当作 binary scorer 不存在的依据 | `results/PHASE_R1.md` §25.32–§25.33；未启动 GPU、模型或 E 分数 |
| C-32b / G-21 | 不启动 | 本轮唯一 external benchmark 已按协议阻断收口；只有新的作者授权后重开 R0，才可形成新合同；单 seed 规则不变 |
| C-34 · 研究回合复盘 | ✅ 已完成：核实官方源码并收窄阻断依据，完成合成数据 CPU split 检查、下一轮检索约束与作者决策卡 | `results/PHASE_R1.md` §25.33；已按 10-08 委托回 MAVEN 根因与新机制队列，E 不再作硬前置 |
| D4 / A4 / C5 方法机制 | D4、A4、旧 C5 均已按契约收口或封存 | 不重开；C-22 继续暂停，不得因为本队列结束自动恢复 |

## 可比性口径（本队列的通过条件）

- P（原文参考）只能给出处、表号与原始协议背景，永不与项目数字相减或排序；
- V（原始基准保真度）要求在公开原始基准复现发表数值；当前两项若无法完成，逐项说明障碍并标 FR-016(b)；
- U（统一协议）才可直接比较：manifest、候选/mention 全集、official scorer、标签映射、训练/selection/evaluation
  隔离与推理输入逐项一致；
- 单 seed 仅能给出同协议描述性比较。document bootstrap 只能描述评测单位不确定性，不能替代跨初始化确认。

## 历史：C-13–C-21（2026-09-20，本地文献/CPU/代码）

- **C-13**：一手论文与官方代码矩阵完成；A4 被新颖性证据淘汰，D4/C5 保留为条件路线；
- **C-14**：FACT↔ERE 的 2,913 篇 / 73,939 mentions 对齐；现成 held-out relation prediction 只覆盖
  291 篇，且 causal-only incidence 是 5,270/7,195=73.25%，不是合并关系族的 95.57%；
- **C-15**：纠正 LLMERE k=30 的旧判断——direct pair 覆盖 48,562/48,562，受损的是 two-hop support
  （8,826/11,231 保留）；但 A4 因新颖性不足仍不准入；
- **C-16**：C5 同时量出 912/213 个高相似 false-merge 桶和 540/73 个低相似 gold/missed 方向；训练池
  17,014 + 4,430，`.233553 → .415` 的 exact test 在 n=42 时 power `.82012`；
- **C-17/C-18**：D4 五折 cross-fit 计划与 C5 100 条盲审 rubric 冻结，尚无真实模型输出；
- **C-19**：全候选 causal posterior adapter 完成；
- **C-20**：一次性请求构建、严格输出校验、classifier-blind review template 与冻结阈值评分器完成；
- **C-21**：generator config 固定到既有内容寻址 `Qwen/Qwen3-8B`，100 条 requests
  （SHA `74a23bf8…4f2fd`）和 no-repair GPU runner 冻结；当前完整门
  **694 passed / 29 skipped、ruff 0、smoke OK**。

## 下一步

1. C-35/C-36 完成：错误交换复算、A4 gold hash 恢复、远端 6 个测试和解析反例均收口；结果见 §25.34。
2. C5 smoke 已完成；核空卡后直接执行已授权的完整 audit。A4 仍须具体 5090 授权，
   不复跑 C5 smoke，不扩展旧机制续修。
3. 后续 C-41 / T087 从可靠强控制的错误出发研究实质不同的新机制，按 `HANDOFF.md` §0.3.4 准入；
   文献研究不依赖 GPU 诊断，但单活动任务、主表先行和新合同闸门保持。C5 切片已开工，方法训练未启动。

⛔ 仍禁止：未授权多种子、final-valid 选模、删除候选、事后修 prompt/阈值、用更大 backbone 掩盖机制失败，
以及把透明适配写成“胜过原论文”。

## 已完成：**G-11a · 表 6-2 的公开对手行**（2026-09-18 收口）

三项裁决 **2026-09-17 晚已按推荐落地**，队列重新有东西。完整说明在 [`HANDOFF.md`](HANDOFF.md) §0.3。

| # | 裁决 | 定的是什么 |
|---|---|---|
| **①** | **Gate 2 改纲** | **推迟到 Ch6 主表有数字之后再定**，不是停等——取 (乙) 后 Ch6 全线解锁，没有任何可执行任务被 ① 阻塞；改哪一种形态取决于 Ch6 交出什么 |
| **②** | **Ch6 的上游身份** | **取 (乙)**：`predicted` 沿用 v5 判别式抽取器在 valid 上的产物，**表头标明上游身份**（不是 C5/A4/D4）。E3.1 已据此闭合 |
| **③** | **C-3 / G-8** | **维持 (甲) 不执行**：它是 Ch4 主表的一行，Ch4 存废未定之前 `< 1 GPU·h` 也没有去处 |

**裁完当晚推完的 Ch6 一轮**（数字全在 `results/PHASE_E.md` 最后一节）：

- **修缺陷**：冻结 unit 有 **68 个 `instance_id` 撞号**（`cgep.py` 用的是每个 ECG 各自的节点下标，
  撞的是完全不同的两条 query）。query edge 改为自己命名自己，重新冻结
  **`e3-v61-20260917`（`f75e7e87…`）**——逐行零差异、candidate digest 不变，并表能力没丢；
- **E3.1 ✅** 三层上游接口闭合（identity 16,104 单例 / relation 217,694 边 / factuality 16,104 标签），
  `status=closed`；
- **E3.2 ✅** 描述性画像：predicted 拓扑边是 gold 的 **3.4 倍**、R2 query F1 **.0795**，
  而下游 MRR 只掉 **12.2%** ⇒ **R2↔MRR 又是一对不对齐**（此前只有 causal_scc↔R1 的 ρ=−0.064）；
- **表 6-2 四行**：random `.0143` / frequency `.0378` / **predicted `.1583`** / gold `.1802`，
  Hit@1/3/10/20/50 全列。`.1802` 与 `.1583` 逐位复现 2026-07-29。

**队首 = G-11a，2026-09-17 晚已开工**：四个公开对手（SimKGC / MCPredictor / CSProm-KG /
BART contrastive）**没有一个实现 CGEP**，适配代码要我们自己写 ⇒ 注定是 **(b) 透明适配**，
按基准率 **3–4 周**。当晚落地的适配层：

- `scripts/export_cgep_as_kgc.py` —— 冻结 unit → KGC 数据集（33,017 实体 / train 46,100 /
  test 1,908 + 每题 512 候选），**任何一条 query edge 漏进训练图就 fail-fast**；
- `scripts/patch_csprom_kg_for_cgep.py` —— CSProm-KG 第 6 处补丁，**只 dump 候选分数**，
  不动模型 / 损失 / 优化器 / 指标，前后 hash 已记；
- `scripts/score_kgc_opponent.py` —— 用**我们自己的** evaluator 打分（表 6-2 其余四行同一把尺）。

**🟢 21:2x 起两个对手在 4090 上并行训练**（各自 namespace，共用一个独立 venv，**没碰 ekg 的 venv**）：

| 卡 | 对手 | 设置 | 预计 |
|---|---|---|---|
| card 0 | **CSProm-KG** | `-epoch 60`，其余与 README 的 WN18RR 命令逐字相同 | 约 5.7 GPU·h |
| card 1 | **SimKGC** | `--batch-size 256`（1024/512 实测都 OOM），其余与 `train_wn.sh` 逐字相同 | 约 1.3 GPU·h |

端到端冒烟已过：训练 → 按 dev 切片选 checkpoint → test → **dump 恰好 1,908 行** →
`score_kgc_opponent.py` 用我们自己的 evaluator 收下。
backbone 走 **`hf-mirror.com`** 直接拉（推翻「权重只能本地下了再 scp」，见 `HANDOFF.md` §0.6）。

**✅ G-11a 第一轮 2026-09-18 凌晨收口，表 6-2 成形，三个公开对手到齐。**

| 方法 | MRR | Hit@1 | Hit@10 | Hit@50 |
|---|---:|---:|---:|---:|
| CSProm-KG（(b)，⚠️ 结构性不兼容） | .0028 | .0000 | .0000 | .0000 |
| random | .0143 | .0021 | .0241 | .0891 |
| frequency | .0378 | .0267 | .0372 | .1509 |
| SimKGC（(b)，batch 256，无 description） | .0563 | .0183 | .1279 | .3375 |
| **本文构建图（predicted）** | **.1583** | .1038 | .2563 | .5126 |
| **SeDGPL（(b)，自跑）＝ gold 上界** | **.1802** | .1143 | .3124 | .5823 |
| （协议证据）SimKGC + 候选句 | .6373 | .5079 | .8585 | .9308 |
| （协议证据）`same_document` | .8041 | .6567 | **1.0000** | 1.0000 |

🔴 **两个 KGC 对手朝相反方向失败，两种失败都不是关于事件预测的**（机制都已量出）：
SimKGC 带候选句的分数 **91% 是文档匹配**（清空 description 塌 11.3 倍，top-1 同篇率
78.20%→18.50%，均匀乱选 0.41%）；CSProm-KG 按实体嵌入表打分而**金标在训练图里 0/1,908 有边**
（有训练边的候选平均排名 195.0 / 没有的 399.7 / 乱排 255.5），
而同 checkpoint 在 dev 上 `val_mrr=0.2907` ⇒ 模型没坏、也不是训练不足。
⇒ **不得写「我们超过了 CSProm-KG / SimKGC」。**

**E3.5 ✅ 已写**（`results/PHASE_E.md`）：三条结论各自的「可写 / 必须同时写 / 不可写」，
Done-when 逐条核对——**只差 matched seeds**（须逐次授权，表 6-2 当前单 seed 并已标注）。

## 顺位 2（裁决之外唯一能动的）

1. `docs/reports/` 下一份周报：从 09-17 那份的第 4 节接着写，**不要照抄它的计划表**；
2. matched seeds 13/17/42 —— ⛔ 须逐次授权，是 Ch6 Done-when 唯一还差的一条；
3. MCPredictor / BART contrastive **维持 (b) 不跑**，三个对手已满足名册 §5。

**2026-09-17 当周完成的五项**（结论都已写进 `results/` 并 push）：

1. **G-4** A4.3 四臂收口：`full` causal 7.507508 低于自身消融臂 23.72 ⇒ 第一个设计周期失败（`ac0da34`）；
2. **G-5b** C5 差距归因：那 1.83 里**误合并占 72.7%**；`full` 的 MUC recall **已超主锚**，
   剩下的 1.084 全在 precision ⇒ 该压的是误合并，不是继续加 recall（`df8404b`）；
3. **G-4b** A4 误差分析：**坍塌是无差别的，不是「先丢难例」**——`full` 丢掉的 1,344 对
   （= `remove_core` 答对集合的 88.8%）在距离分布上与被保留的、与 gold 全体几乎逐格相同；
   损失集中在 PRECONDITION（占 gold 76.8%，召回只保留 7.9%）（`e258cc8`）；
4. **C-3** LLMERE 恢复方案：根因改写——不是「95 条格式错」，是**全部 11,149 条退化重复**
   （生成侧没有终止语义），95 条只是污染落进了第一行。成本 42 GPU·h → **< 1 GPU·h**（`339f974`）；
5. **E3.1 前置核查**：三个方法章的产物与 E3 unit 交集为 0 ⇒ 裁决 ②（`c2f0cbc`）；
   另 **G-11a** 核实为早已完成（障碍原文一直在 `BASELINE_ROSTER.md` §6.2b）。

**2026-09-20 三件套**（含 R1 v6.2 审计、C-19 posterior adapter 与 C-20/C-21 generation harness）：
**694 passed / 29 skipped、ruff 0、`ekg-smoke` OK**。

实验截止 **2027-02**；排期与估算基准率见主表 §3。

## 当前三端

- **local**：2026-10-02 三件套 **786 passed / 32 skipped**、ruff 0、`ekg-smoke` OK；R1 一致性审计
  **36/36 requirements mapped**；P1 r15
  `1e31a9ac…f9655`；
- **gpu-4090**：2026-09-30 SSH 可达；C-28 相关进程 GONE，10 个 run 全部完成，聚合报告已落盘；
  远端代码受控同步到 `8bc62b0` 后完成聚合，未清理 remote-only 产物。**本次未核 GPU 占用，后续用卡
  仍须先 `nvidia-smi`**；
- **gpu-5090**：**当前占用未核，使用前必须重新核卡**。A4.3 四臂
  2026-09-16 11:02–23:27 跑完（实测 12h25m），C5.3 pilot-r2 与 CSProm-KG WN18RR 推理 09-16 跑完。
  ⚠️ **外网是分域的**：gh-proxy 增量 fetch ✅ / 清华 PyPI ✅ / GitHub 直连 ❌ / 完整 clone ❌ /
  Google Drive ❌ / ModelScope ✅。⛔ 硬边界：EasyECR 的 torch 2.0.1 无 sm_120；SimKGC 的 batch 1024
  要 4×32 GB 装不下。
- ⚠️ **cpolar 隧道可能整条下线**：2026-09-30 本次可达，但历史上出现过 `Connection refused`。
  继续按三态判活，**ssh 失败不得判远端进程已死**。

## 禁止

- 未授权额外 seeds；使用 final-valid 选模；不同 candidate/evaluator/split 直接比较；
- 把 Ch1 event-level argument oracle 或 Ch3 gold-evidence oracle 当方法分；
- **看到某个选模规则能救分再改选模规则**（选模轴伪影，Phase C 教训）；
- 未询问就跨机搬 checkpoint、数据集或其他大文件；
- `rsync --delete`、远端 `git clean -fdx`、服务器 `uv run`/`uv sync`；
- 复活已封存方案（工作点、近似 retriever、prototype、ATLoss），或用更大 backbone 掩盖机制无效。

## 成功条件

Ch1–Ch3 各自在统一公开主指标上**超过冻结主锚**，主表另报多个已复现的公开方法族
（`SPEC.md` v1.1.0 QR-001：广度是报告要求，不是准入门；跑不了的进可得性表写明障碍）。
每个外部复现带 FR-016 保真度状态。所有结论必须可从结果表追溯到 commit、manifest、candidate、
evaluator、命令、checkpoint 和 hash。

**三种可接受的最终形态**（见 `EXPERIMENT_PLAN.md` §7.5）：三方法章 + 应用章（博士量级）／
两方法章 + 应用章（领域硕士标准形态）／≤1 方法章时由作者裁决改纲（导师不介入结构）。
**不自行降级**；旧机制失败后只有通过实质不同的方法家族才能重开，不能以换名、扫参或更大
backbone 绕过止损。每个家族允许**两个有效周期**——5 个月预算下第二周期是可负担的，
第一轮失败不等于该章结束。

**2026-10-26 R110闭合/接R111**：C41-A-R/T087仍wip。原dev完整词面×句距分层和独立12张native矩阵一致；最近邻裁决/数字见R1 §25.132。当前只原train同词面对异语境监督机会、去重复和最近邻审查（§25.133）；不是新方法准入，不重跑既有dev或模型。O1–O4未达。

**2026-10-26 R111闭合/接R112**：仍C41-A-R/T087；R111原train信号和独立SQL通过，普通匹配contrast创新表述因CNC最近邻被拒。主表下一为原作者内置unweighted CE已知强控制（R1 §25.134–§25.135），只一个固定配置，先CPU/实际CUDA/预算；无新训练/原创方法准入，无alpha/gamma/lr搜索或旧臂重起。

**2026-10-26 R112 CUDA闭合/接R113预算**：仍C41-A-R/T087。CE原机CPU/实际CUDA已过，exit0/GONE；当前仅已有成本入口一次cold/warm最大train lr0计时后裁完整预算（R1 §25.136/CE合同），不是新方法或训练已启动，不重复封存准备/旧三臂。

**2026-10-26 R113完整CE准入**：同C41-A-R/T087，实际CPU/CUDA/init/一次cost及完整预算都过（R1 §25.137）；下一按CE合同部署/全pin/空卡联核后执行唯一seed13/20epoch强控制。当前尚无epoch；不重复探针/旧臂或把已知CE当原创。完整后独立重载/五对照，O1–O4未满足。

**2026-10-26 CE实际CUDA运行中**：C41-A-R/T087唯一活动项；launcher1152477/train1152480，固定GPU1/seed13/20epoch。接续先核pipeline阶段/.exit/真实进程；成功后自动独立核分和五对照，失败即停，不重复启动。身份/快照/限制见R1 §25.138，当前未出完整分数，O1–O4未达。
