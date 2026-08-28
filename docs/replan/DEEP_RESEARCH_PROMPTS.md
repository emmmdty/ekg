# v6 方向重审：网页版 GPT 深度研究提示词

> 日期基线：2026-08-25。
>
> 推荐严格串行执行：**B 数据集 → C 方法/代码 → D 切口 → E 技术价值/工业/人才**。
> 每完成一份就下载为对应文件名，放入 `docs/replan/`，再交给 Codex 做一手来源与口径复核。
> 不建议一次并发四份：B/C 的结果会提高 D/E 的判断质量，也能避免重复搜索。

---

## DR-B：公开数据集、竞争密度与 MAVEN 残值

**建议附件：**

- `docs/replan/EXPLORATION_PROMPT.md`
- `docs/replan/LOCAL_ASSET_INVENTORY.md`

**输出文件名：**`B_datasets.md`

```text
你是一名严谨的 NLP 学术调研员。当前日期是 2026-08-25。请为一篇硕士论文的方向重审做“公开事件类数据集、竞争密度与 MAVEN 资产残值”深度研究。不要设计论文章节，也不要推荐“容易打败的对手”；你的产物是可审计的证据报告。

背景与硬约束：
- 主题候选是事件图谱或事理图谱的构建及风险监测应用。
- 只用公开数据，不做人工标注。
- 后续实验只有单卡 RTX 5090，约 27GB 可用显存。
- 最终每个方法章都必须在公开可比主指标上超过多个已发表方法。
- 跨语言与风险监测都是待评估提议，不是既定方向。

请执行以下任务。

一、建立候选数据集总表
至少覆盖并核实这些类别和候选，同时补充你找到的 2024–2026 新数据集：
1. 事件检测/抽取：MAVEN、ACE05（en/zh/ar）、ERE、TAC-KBP、RAMS、WikiEvents、DocEE、GLEN、MAVEN-Arg；
2. 事件关系：MAVEN-ERE、EventStoryLine/ESC、Causal-TimeBank、MATRES、TimeBank-Dense、TORQUE、CRAB；
3. 事件共指：ECB+、GVC、FCC、MEANTIME、CD²CR；
4. 多语言/跨语言：MEE、MINION、MCECR、MEANTIME、ACE05 多语言部分及 2024–2026 新资源；
5. 中文：DuEE、DuEE-fin、FewFC、CCKS 系列、CMNEE、DocEE-zh、OEE-CFC 及新资源；
6. 事件预测/脚本/事件图：MCNC、CGEP-MAVEN、CGEP-ESC、NYT-SEG、TORQUESTRA、EcomScriptBench 及新任务；
7. 事实性：MAVEN-FACT、FactBank、UW、MEANTIME、Unified Factuality；
8. 风险/危机/社会事件：SPEED/SPEED++、ACLED、GDELT、ICEWS、EM-DAT、灾害/疫情/供应链相关资源。

总表每行至少包含：
数据集｜年份｜语言｜任务与 gold 对象｜规模（分 train/dev/test）｜许可证/下载入口｜test 标签是否公开｜若不公开则当前提交通道是否实际可用｜2024–2026 独立跟进方法数下界｜可同口径比较的当前最好结果｜单卡 27GB 可行性｜关键风险。

二、严格核查 test 与评测口径
- 必须实际访问官方数据页、GitHub、CodaLab/EvalAI/leaderboard；不能只转述论文说“可提交”。
- 若通道需要登录而你无法实际提交，写“页面可访问，但提交能力未验证”，不要写“通道活着”。
- 近两年论文实际报 train/dev/test 哪个 split？如果把 valid 当 test，请列出至少两篇一手论文先例；找不到就写未取得。
- 对任何模型分数，必须同时记录：论文标题与 DOI/arXiv/ACL ID、具体表号、split、评测脚本（官方/自实现/未声明）、指标定义（micro/macro、negative class、F1 聚合）。四项缺一，该数字标“不可比”，不得拿来相减或排序。

三、竞争密度与成熟度
- 对每个高潜数据集，列出 2024–2026 已正式发表的方法论文清单；arXiv-only 单列，不计入“已发表方法数”。
- 特别标出：2024 年以后发布且已有至少 2 篇独立后续方法论文的数据集。
- 区分“原数据论文把旧 baseline 适配到新任务”与“后来有独立团队跟进”；两者不能混计。
- 判断饱和度时只能依据同 split、同 evaluator 的时间序列；口径不齐则写“无法判断是否饱和”。

四、MAVEN 系列残值
核查 MAVEN、MAVEN-ERE、MAVEN-Arg、MAVEN-FACT 在 2025–2026 的新方法、独立跟进数、评测通道和饱和度。实际访问 MAVEN-ERE CodaLab，记录核验日期、页面状态、能否进入提交操作，以及不能验证的边界。若附件中有 LOCAL_ASSET_INVENTORY.md，只把它用于本地代码残值，不要重做代码盘点。

五、输出结构
1. 执行摘要（只写事实，不推荐方向）；
2. 数据集总表；
3. test/leaderboard 实访日志；
4. 重点候选的 2024–2026 方法清单与严格可比数字表；
5. MAVEN 残值；
6. “2024 后新数据集且已有 ≥2 独立跟进”的专表；
7. 未能核实项；
8. 与预期不符的事实；
9. 证据审计表：每条核心结论 → 一手 URL/论文 ID → 表号/章节 → split/evaluator/指标是否齐全。

硬性禁止：
- 不给章节骨架；
- 不按“对手弱、容易超越”推荐方向；
- 不把搜索摘要、二手博客或 Papers With Code 单独当最终证据；
- 不把不同 split/evaluator 的数并排相减；
- 不把页面存在写成提交通道可用；
- 不知道就明确写“未能核实”，不要补猜。
```

---

## DR-C：LLM 方法范式、开源代码与单卡可行性

**建议附件：**

- `docs/replan/EXPLORATION_PROMPT.md`
- 可选：完成后的 `B_datasets.md`

**输出文件名：**`C_methods_code.md`

```text
你是一名同时熟悉 NLP 论文复现与 GitHub 审计的研究工程师。当前日期是 2026-08-25。请为一篇事件图谱/事理图谱硕士论文做“LLM 时代的方法范式、开源实现与单卡可行性”深度研究。产物是证据报告，不是章节方案。

约束：只用公开数据；后续实验限单卡 RTX 5090、约 27GB 可用显存；每个方法章必须能与多个已发表方法在公开主指标上同口径比较。

一、方法范式地图
调查并归类 2024–2026 正式发表的事件类方法：
- instruction tuning / unified IE：IEPile、InstructUIE、KnowCoder、ADELIE、TextEE 生态及后续；
- code-style / schema-guided / constrained generation；
- retrieval-augmented、demonstration retrieval、知识增强；
- LLM 生成摘要/标注/候选 + 小模型判别；
- agent/multi-agent 分解与自动建图；
- 事件关系、时序、因果、共指、event-graph reasoning 的 LLM/LoRA/混合方法。

二、关键事实核查
重点回答：
1. 在事件检测/论元抽取、事件关系（时序/因果/子事件）和事件共指上，direct zero/few-shot、监督 LoRA/SFT、LLM+小模型混合分别是否超过 fully trained RoBERTa/DeBERTa 级方法？
2. 必须同时找正证据和反证据；区分 direct prompting、LoRA/SFT、冻结 LLM 表征、闭源 API 辅助器，不可统称“LLM 方法”。
3. 每个用于判断的数字必须给论文标题+ID+表号+split+evaluator+指标定义；轴不齐则标不可比，不做差值。
4. 检查是否已有独立方法在同一新 benchmark 上竞争，而不只是数据论文自己重跑旧 baseline。

三、multi-agent / agent 建图
除 CGEL（ACL 2025，arXiv:2506.06910）外，寻找正式发表的 LLM/多智能体事件图、因果事件图、显著事件图构建方法。区分：真正多个 agent 协作、级联多阶段 pipeline、单模型多 prompt；不要都叫 multi-agent。记录数据、gold、指标、对手和代码。

四、GitHub 可复现性审计
至少覆盖：TextEE、OmniEvent、UIE/DeepKE 类统一框架、MAVEN-ERE、SeDGPL、SECURE、CALLMSAE、EventRAG、CGEL（若链接失效也记录）、TAG-EQA，以及你发现的高价值 2024–2026 官方实现。

每个 repo 必须记录（核验日期 2026-08-25）：
- 官方 URL、commit SHA、最后 commit 日期、star 数、是否 archived；
- 是否有完整训练脚本、数据预处理、官方 evaluator、环境锁、checkpoint；
- README 命令引用的文件是否真的在仓库；
- issue 中是否有独立用户复现成功/失败的证据；
- 依赖是否仍可安装；
- 论文训练硬件与显存；若未声明就写未声明。

“有 GitHub”绝不能自动写成“能跑”。不要实际执行不可信代码或下载大模型；做静态审计即可。

五、27GB 单卡可行性
- 对 7B LoRA、7B QLoRA、14B QLoRA、encoder-only/seq2seq 方法分别给出可行性判断。
- 显存与训练时长必须引用官方文档、论文硬件或可复现实测；没有来源不要凭经验报精确 GB。
- 明确区分：可训练、只能推理、需要梯度累积/量化、必须多卡、依赖闭源 API。
- 若方法原论文用 4×A100 80GB，不可因为“理论上可量化”就写单卡已验证；写“需改造，未实证”。

六、输出结构
1. 方法范式总览；
2. direct prompting / LoRA / hybrid 与小模型的严格可比证据表；
3. agent/multi-agent 建图表；
4. GitHub 审计表；
5. 27GB 单卡可行性矩阵；
6. 官方评测基础设施清单；
7. 未能核实与不可比项；
8. 与预期不符事实；
9. 证据审计表。

禁止：不给章节方案；不按对手弱推荐；不引用二手榜单替代论文表；不把不同 split/evaluator 混比；不把 arXiv-only 写成已发表；不把“代码存在”写成“可复现”。
```

---

## DR-D：跨语言、风险场景及替代切口可行性

**建议附件：**

- `docs/replan/EXPLORATION_PROMPT.md`
- 强烈建议附上完成后的 `B_datasets.md` 与 `C_methods_code.md`

**输出文件名：**`D_angles.md`

```text
你是一名负责研究方向可行性审计的 NLP 研究员。当前日期是 2026-08-25。请评估两个作者提出的切口，并从证据中提出 2–3 个替代切口。只做可行性核查，不给论文章节骨架，也不要按“对手容易打”做推荐。

共同约束：公开数据、零人工标注、单卡 RTX 5090 约 27GB；最终每章必须能在公开主指标上与多个正式发表方法同口径比较。风险监测是应用延伸，大宗商品不是硬约束。跨语言只是待评估提议。

切口 α：跨语言/多语言事件图谱
请分开调查：
1. 多语言事件抽取/论元/关系；
2. zero-shot 跨语言迁移；
3. 多语言联合训练；
4. 跨语言事件对齐/跨文档共指：不同语言报道的同一现实事件是否能对齐为同一节点；
5. 多语言 event graph 的统一 schema/构建/下游。

对每类列公开数据集、语言、规模、gold 对象、test 可得性、2024–2026 独立方法数、严格可比主指标、代码和 27GB 可行性。重点核 MEE、MINION、MEANTIME、MCECR、ACE05 多语言部分及新资源。如果“跨语言事件对齐”公开数据稀缺，必须直说，不能用一般 multilingual EE 冒充。

切口 β：供应链中断/大宗商品/经济风险事件
调查：
1. 是否有公开供应链中断、大宗商品、经济风险的事件抽取/事件图数据；
2. 通用数据（MAVEN/ACE/ACLED/GDELT/ICEWS/EM-DAT/SPEED 等）是否有论文先例把特定事件类型作为风险子集；没有先例就不能称公开 benchmark；
3. 是否有“事件 → 风险/中断/传播/预警”的公开事件层面下游任务，优先事件链补全、传播路径、时间线、预警提前量，不把高噪声价格预测默认成主任务；
4. 数据许可证、标签质量、泄漏风险、时间切分与公开 evaluator。

自主替代切口
基于你实际取得的 2024–2026 证据提出 2–3 个可能比 α/β 更自然的切口。每个必须按四栏独立陈述：
- 栏 A：真问题价值（survey/limitation/position 的一手证据）；
- 栏 B：竞争密度（独立发表方法、同口径主指标）；
- 数据与 test 可得性；
- 单卡可行性与关键风险。

候选可从但不限于以下方向发现：document/multi-document event structure、event graph reasoning、低资源/跨域泛化、可验证因果/时间推理、LLM+小模型协同、风险事件时间线。不要为了迎合列表而强提。

数字规则
任何分数都必须有论文标题+ID+表号+split+evaluator+指标定义；任一缺失标不可比。独立 follow-up 与原论文适配旧 baseline 分开计数。arXiv-only 单列。实际访问数据/test/leaderboard；不能验证提交就写边界。

输出：
1. α 可行性报告；
2. β 可行性报告；
3. 2–3 个替代切口证据表；
4. 问题价值与竞争密度分栏决策表；
5. 数据/test/代码可得性日志；
6. 未能核实；
7. 与预期不符事实；
8. 证据审计表。

禁止：不给章节方案；不把“多语言”自动说成跨语言图融合；不自造风险评测子集；不因对手少就否定问题价值；不凭二手来源或搜索摘要报数字。
```

---

## DR-E：显式图的技术价值、工业落地与人才市场

**建议附件：**

- `docs/replan/EXPLORATION_PROMPT.md`
- 可选：`A_terrain.md`、`B_datasets.md`、`C_methods_code.md`

**输出文件名：**`E_industry.md`

```text
你是一名兼顾学术证据、工业系统和招聘市场的技术调研员。当前日期是 2026-08-25。请研究 LLM 时代显式事件图谱/事理图谱的存在理由、工业落地与人才市场信号。不要给论文章节方案，不要写行业宣传稿。

背景：作者希望职业技术栈偏 LLM/Agent 工程，但不要求硬凑；论文主题仍须由真问题与公开 benchmark 证据决定。风险监测是应用延伸。

一、显式事件图的技术存在理由与反证
按以下能力逐栏研究：
- 可审计/来源追溯；
- 时效与增量更新；
- 长时程/跨文档组织；
- 结构化检索与 GraphRAG；
- 因果/时间一致性；
- 幻觉/事实约束；
- 低成本推理或 LLM+小模型协同；
- agent 长期记忆。

每栏严格区分：
1. 论文 motivation 声称；
2. 实验真正验证；
3. event-specific 证据还是一般 KG/GraphRAG 邻近证据；
4. 仍未验证的外推。

优先核 EventRAG、CALLMSAE、CGEL、CGEP/SeDGPL、TAG-EQA、LoCoMo、AriGraph、Zep/Graphiti，以及 LLM-KG roadmap。必须找反方/边界证据：纯 LLM/text-only 与 graph 方法相当或更好、图质量噪声抵消收益、构建/维护成本、错误传播、闭源 judge 造成不可复现等。若找不到正式论文明确主张“LLM 时代不再需要图”，如实写未取得，不能把自己的推论冒充反方。

任何实验结果若出现数字，必须给论文+ID+表号+split+evaluator+指标定义；否则只写定性表号，不报数。

二、工业落地
调查 2024–2026 可验证的事件图谱、时序/因果 KG、GraphRAG、agent memory 在以下场景的真实系统：风控、舆情/情报、供应链、金融、安全、灾害。证据优先级：公司官方技术博客/文档/开源仓库/会议工程论文 > 可靠采访 > 二手媒体。每项注明：公司/项目、实际问题、图中是否真有 event nodes、是否生产使用还是 demo、公开规模/指标、更新时间、开源状态。一般 KG 或向量 RAG 不能冒充事件图。

三、人才市场信号
用当前仍可访问的招聘页面、公司岗位描述、官方技术栈公告与活跃开源项目回答：与本课题相邻的实际技能需求是什么？至少分：
- GraphRAG / KG-RAG；
- agent memory / tool use / workflow；
- 信息抽取与数据管道；
- LLM 微调、评测与可观测性；
- KG/图数据库/实体解析；
- temporal/causal modeling；
- 风控/情报领域工程。

每类记录至少若干可验证职位或官方信号，注明公司、岗位、地区、抓取日期、原始 URL、必须/加分技能。职位页面失效则写失效，不用聚合站缓存冒充当前岗位。不要用职位数量做全市场统计，除非采样方法可复核；更适合报告“最低可证需求形态”。

四、开源活跃度
对关键项目记录 2026-08-25 快照：star、最后 commit、release、贡献者/issue 活性、是否 archived。star 只作社区信号，不等于工业采用。优先官方 GitHub。

五、输出结构
1. 技术存在理由：已实验验证 / 仅 motivation / 反证与边界三栏表；
2. 工业案例表；
3. 招聘与技能信号表；
4. 开源活跃度表；
5. 对“LLM/Agent 工程人才价值”的含义（只做证据解释，不反推学术选题）；
6. 未能核实；
7. 与预期不符事实；
8. 证据审计表。

禁止：不给章节骨架；不把营销页写成生产证据；不把通用 GraphRAG/agent memory 自动称事件图；不以 star 或少量职位推断整个市场；不凭二手摘要报学术数字；不隐去图构建成本与负结果。
```

---

## 回传给 Codex 时附带的统一说明

每次把网页版深度研究结果交回时，请同时告诉 Codex：

```text
这是 DR-B / DR-C / DR-D / DR-E 的原始深度研究输出，尚未经本地交叉核验。
请先保存到 docs/replan/<对应文件名>，再检查：
1. 一手来源是否真的支持对应结论；
2. 每个数字的表号、split、evaluator、指标定义是否齐全；
3. test/leaderboard “页面存在”是否被误写成“仍可提交”；
4. 已发表、arXiv-only、原论文适配 baseline、独立 follow-up 是否混计；
5. 与 A_terrain.md 或其他报告是否矛盾。
违反证据规则的条目先降级为“未能核实”，不要直接进入综合结论。
```
