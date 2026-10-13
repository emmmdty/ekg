# C-41 · C5 决策边界的机制准入审查（2026-10-13）

本卡承接 `HANDOFF.md` §0.3.5，不建立新任务、不改变 C5 → D4 → A4 顺序。
科研价值：对准表 5-3 与新家族准入，区分 scorer 的前项排序错误与 dummy/首提及判定错误；
避免依据旧弱控制的 lexical 画像选择机制。可行性：已有 type-control/cache/无标签类型输入/
identity gold/官方 evaluator 可在 CPU 完成诊断。实测只见
[`PHASE_R1.md` §25.43](../results/PHASE_R1.md)，不是新方法提分。

## 一手检索边界

截止 2026-10-13，检索 ACL Anthology、作者 GitHub、正式出版正文与官方 preprint。
查询覆盖 event coreference + counterfactual / temporal coherence / cluster consistency /
anaphoricity / singleton detection / differentiable metrics；并以 `site:aclanthology.org`
补查 antecedent pruning / dummy / gold antecedents。初次泛化的 counterfactual 查询混入条件句
研究，已改为 coreference 限域；无关结果不进入证据。此次不是穷尽综述。
源码快照、PDF SHA、tree 与工具失败日志在结果页指定的 `neighbor_audit/`，没有运行外部 trainer。

| 邻居与正文位置 | 已核机制与实质边界 | 代码 / 在 MAVEN 上的裁决 |
|---|---|---|
| [RCA / LLM-RCDA, NAACL 2024](https://aclanthology.org/2024.naacl-long.63.pdf) §4.2 Algorithm 1、§5.1、Appx A.2 | 依据原 pair label，改 trigger 与事件句；生成非共指或共指 pair，后者还改周边上下文。训练 cross-encoder，KNN 候选与 cluster merge。ECB+/FCC/GVC、B³ 选模及 CoNLL 等评分均非 MAVEN 全候选协议 | [官方仓库](https://github.com/Danield21/Rationale4CDECR) `f88572fac4f50595abee730dfcf14ac8cfa916aa`、MIT。有 trainer、数据构造 helper 与部分增强 CSV，不能写成 README-only。主 ECB enhanced 配置的 train CSV 不在 git tree，README 指向 Drive。静态审查通过不等于 runtime/fidelity PASS；没有 MAVEN 增强数据，不直接导入外部语料。普通 counterfactual port 不准入创新 |
| [ACCI, Scientific Reports](https://www.nature.com/articles/s41598-025-32765-6) Eq.7–14 | trigger-only bias 分支、去 trigger 的整个 context 分支、factual 分数加减。context 不是独立抽取的 typed-role 后验；不把任务不同当机制不存在 | [仓库](https://github.com/era211/ACCI) `7f5bcd81e0a352f15263a5c7e7c4853b9e3023fa`，最新 tree 仍仅 README；没有 trainer/LICENSE/checkpoint。卡【代码】，不重建后冒称复现；mask+分支本身不能作为新贡献 |
| [CohTP, ACL 2026](https://aclanthology.org/2026.acl-long.1345.pdf) §3–4、Appx C | temporal graph、EA-GNN 的一致性约束、冲突纠正、分区与跨时间恢复，再做共指；含 GPT-4 路径。跨文档 ECB+/GVC 等，与当前全候选文档内控制不同 | [仓库](https://github.com/chenxinyu-nlp/CohTP) `3843ad0a4dcdb9f4761f134894b935d4ed74d19b`，tree 仅 `Comming soon`，无可运行方法。卡【代码】，硬分区也不符合本轮完整候选边界。不引入闭源纠正服务，不把不能复现当新颖性证据 |
| [Lu & Ng, NAACL 2021](https://aclanthology.org/2021.naacl-main.356.pdf) §4.1 Eq.5、C1/C3/C4 | prefix+span 的 anaphoricity 分支；类型及 anaphoricity 与 dummy/non-dummy 一致性 penalty，另有 realis/argument 任务。KBP 的六任务模型不是本项目给定类型控制 | 本轮只审正文，不声称找到或运行其完整实现。给定类型规则、普通首提及辅助头和软约束均有先行机制，不准入创新 |
| [Lu & Ng, ACL 2017](https://aclanthology.org/P17-1009.pdf) §3.2.1.3、§3.3 | 从 event clusters 派生首提及/后续提及监督，joint trigger/coreference/anaphoricity；NULL 特征使用前文句数与 mention 数 | 派生监督和加入计数特征本身已有先行工作；没有建立新的 runnable/fidelity 行 |
| [C2F-SD, NAACL 2024](https://aclanthology.org/2024.naacl-short.19.pdf) §3 | antecedent-aware span attention、singleton BCE、独立专家/共享表示；singleton scores 参与连链并执行 mention pruning。singleton 与“此处没有先前同事件 mention”不是同一标签 | [论文指定仓库](https://github.com/XiyuanZou/C2F-SD)本次 web 失败、git 经现有代理要求凭据，可用性 UNKNOWN，不写成仓库不存在。不能照搬 mention pruning 到固定 mention 全集，普通分头不是创新 |
| [StructECR, ACL 2021](https://aclanthology.org/2021.acl-long.374.pdf) §3.3–3.4 | antecedent 模型；gold/predicted cluster 的 intra/inter/set centroid 一致性正则；KBP predicted mentions | cluster consistency 本身已有机制。不把 scorer/decoder 恢复或附加 centroid loss 称新方法；本轮没有 runnable 复现结论 |
| [Le & Titov, CoNLL 2017](https://aclanthology.org/K17-1039.pdf) §2–3 | 用 root-membership posterior 放松 clustering metrics；实际训练目标为 B³/LEA，正文明确没有优化 MUC | “优化主指标而非 pair CE”这个总想法已有先行工作；不能误称本文已提出 MUC loss，也不能以改指标名字自动取得新颖性 |
| [Lee et al., EMNLP 2017](https://aclanthology.org/D17-1018.pdf) §6 | marginal antecedent likelihood；gold antecedents 全被 prune 时 gold target 为 dummy | “删光 gold predecessor 并翻转到 dummy”的普通候选可用性监督已存在，不能单靠该操作立项 |

RCA 的公开 classifier 可供未来透明适配复用；这不同于直接借用外部生成训练语料。
正文机制差异与 runnable/fidelity 分开记录。此次没有搬论文数值来替换统一主表。

## 残余错误 → 假设 → 区分性实验

| 待修错误（数值只见结果页） | 假设 / 竞争解释 | 下一项可证伪检查 |
|---|---|---|
| rank-correct false dummy 与 first-mention false link | null 决策的语义判别不足；竞争解释是得分校准、类别先验、类型/位置捷径、train/eval 打包差异 | 在 train-derived 文档隔离输入上比较预测 newness 与“保留当前决策”的风险，分两方向报告；按同类型、相近位置/候选机会数做负控，不能仅提高总体 accuracy |
| false dummy rank-wrong / wrong real antecedent | 需要前项排序/具体 occurrence 证据；newness 一头无法修复 | 将“是否存在前项”与“当前最强前项是否可信”监督分开，不能用第一个目标代替第二个 |
| oracle 可以修复、部署信号未证明 | gold-conditioned 分解只是可修复覆盖，不是模型因果解释 | 若 train-only held-out 预测不能识别上述错误，停止该具体 observer；不将 oracle 分数作为方法效应或 power 输入 |

## 候选设计 brief：条件决策风险（candidate，未准入）

**研究问题**：给定相同 official scorer、全部 mentions、给定类型 policy，能否用独立文本证据
区分当前决策应保持、改为 dummy、或连到当前最强合法 real antecedent？目标先修 null 边界，
排序错误完整报告并作护栏；不允许用 gold 动态选择执行动作。

**拟议监督变化**：从“直接预测身份/是否 anaphoric”转为预测 frozen scorer 的决策错误状态。
训练 target 来自文档隔离 scorer 的预测与 identity labels；inference 只读原文本、类型、合法
antecedent 分数与预测 clusters。需要区分不存在同事件前项和已有前项但候选不可信，不能合并为
singleton label。该 target 与训练过程是否构成独立贡献**尚未成立**；selective prediction、
learning-to-defer / error correction 是新增必审最近邻，不能只与上表前四篇比较。

**强比较与消融**：保留 frozen anchor/type-control；同 backbone、目标与部署类型 policy 的普通
anaphoricity 分头作为 strongest alternative；候选 full 与仅 newness、仅分数校准/同参数容量
error detector 分开。核心干预一项一变，不拿 `remove_core` 的旧 pair CE 作为新 strongest control。
拟议负控是 train 文档内匹配 type/position/opportunity 的状态标签或证据配对打乱，留住类别先验；
具体匹配规则和 randomization 单位还未冻结，所以当前不能执行方法实验。

**可证伪预测**：full 应改善两类 null 错误的真实纠正/误伤交换，而非只提高全体多数标签准确率；
若 ordinary anaphoricity 或 calibration 控制获得相同收益，则不能归因于条件决策风险。
若配对打乱证据仍获得同样改善，语义机制解释不成立。即使 mediator 改善，未胜 stronger
type-control 的官方 MUC 或损害 B³/CEAFe/BLANC，仍不通过。

**输入/可行性审查**：原 train 的首提及标签可派生，证据结果页 train scope audit；但当前
cache 仅 internal-dev，尚没有新的 train-only、文档隔离 official scorer error-state cache。
不能拿已探索 dev 训练 detector，也不能把原 scorer 对自己训练文档的错误冒充 OOF target。
因此**当前部署输入与训练 target 尚未闭合**，不是标签无法取得；须先审 existing OOF/scorer
适配条件，并按原 main 协议生成新的 train 资产才可能进入冻结合同。

**power 与停止**：目标 ≥80% document-level power 必须针对最终干预、当前 stronger alternative
及预声明主指标效应重算；本轮 gold oracle、旧 hard pools 和旧 exact-pair power 均不能替代。
目标效应、最小可检测效应、具体 action rule 与 power 未冻，所以 `method_admitted=false`。
原探索 dev 不能改称确认数据；没有授权额外 seed/外部语料/5090 新任务。
若最近邻已覆盖实质监督/决策差异、所需 OOF 输入不能闭合、或无泄漏预测不能检出错误，
停止该具体候选，回同一 C-41 选择有证据路线，不复活 sealed role/weak factuality 家族。

**本轮裁决**：继续聚焦 occurrence/null 决策的可部署证据与错误状态监督审查；不投入 plain
counterfactual、ordinary singleton/newness 头或 generic cluster loss 的“创新”实验。
这是一份待过门候选 brief，尚不是新方法合同，C5 贡献门未过，D4/A4 尚未接队。
