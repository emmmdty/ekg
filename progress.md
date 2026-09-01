# Progress Log: v6 论文方向重审

## Session: 2026-08-25

### Phase 1: 接管与上下文恢复

- **Status:** complete
- Actions taken:
  - 先读 `.claude-session-handoff.txt` 末尾，再按需读取原始用户任务部分。
  - 核对 `git status`、工作区差异、暂存区、最近提交和 `docs/replan/` 产物。
  - 确认 Claude 停在五路代理全部因额度失败、尚无外部报告的位置。
  - 确认暂存区为空，v5/Ch1 未提交成果仍完整存在且不属于本轮重审。
- Files created/modified:
  - `task_plan.md`（本轮持久化执行计划）
  - `findings.md`（本轮持久化发现索引）
  - `progress.md`（本文件）

### Phase 2: 五路证据探索

- **Status:** complete
- Actions taken:
  - 最初启动 A/B/C 后，作者要求改为串行以避免额度不足。
  - 已立即中止 B、C；两路尚未写出文件，仅保留 A 继续运行。
  - 后续顺序固定为 A → B → C → D → E，每路完成并初核后才启动下一路。
  - A 全块连续多轮未落盘且未响应两次阶段回报；已中止并缩为 A1/A2/A3，当前只运行 A1。
  - A1 已写入 `docs/replan/A_terrain.md`（134 行）；TextEE、生成式 EE survey、ECI survey、
    temporal IE review 的关键来源与定位已抽查通过。
  - A2a 已追加；补核两篇遗漏论文后完成更正，结论收窄为“direct ICL 未拉平；LoRA 在 MATRES
    接近；冻结表征有一个窄正例；混合/压缩协同有正收益”。
  - 修正对未跟踪报告误用 `git diff --check` 的验证盲点；后续改用 `git diff --no-index --check`。
  - A2b 已追加并完成四个遗漏候选补核；撤回“事件图推理 task 不存在”的过强结论，保留“完整
    公开复现包与 gold proof trace 尚未闭合”的严格结论。
  - A3a 已追加：完成 ACL-family 可审计清单和跨 venue 下界；对未穷尽 venue/2026 部分年份保留
    不可比较标记，未制造伪精确趋势。
  - 作者要求先整理适合网页版 GPT 深度研究的任务；已中止正在运行的 A3b，不再启动本地探索代理。
  - 已生成 `docs/replan/DEEP_RESEARCH_PROMPTS.md`，包含可直接执行的 DR-B/DR-C/DR-D/DR-E，
    以及统一回传核验说明。A3b 并入 DR-E。
  - 收到 `B_datasets.md` 并开始核验；发现网页版内部引用标记不可移植，当前报告暂不进入综合。
  - 统计为 140 个内部 citation token、1 个失效 sandbox Markdown link、0 个原始 URL；已生成
    `docs/replan/DR_B_CITATION_REPAIR_PROMPT.md`，等待同一深度研究会话重导出。
  - 作者改为回传 `B_datasets.pdf`。按 PDF 流程检查后确认它有可搜索文本层和可解析链接注释：
    19 页、237 个 URI 注释、43 个唯一 URI；剔除 ChatGPT 首页和 sandbox 下载后为 41 个真实来源。
  - 决定以 Markdown 恢复未截断表格、以 PDF 恢复引用链接，撤销“必须先修复 Markdown 才能审计”
    的阻塞；接下来直接核验 B 的高影响结论，仍不提前启动 DR-C。
  - Web 工具直接打开与四条定向检索均无可见返回；按既有错误记录不再重复该路径，改用官方 URL
    的 `curl`/PDF 文本抽取完成一手核验。
  - ACL 元数据汇总命令误把 `rg -h` 当成“隐藏文件名”，实际触发帮助页；已记录并改用
    `rg --no-filename`，下载到临时目录的官方页面无需重做。
  - 官方 PDF 已确认 Chen 2024 Appendix E 与 LLMERE 2025 Appendix C 是两篇同一
    valid-as-test 设置的一手先例；CodaLab 页面边界和 ACE05 event-task 语言范围也已确认。
  - 作者集合交叉核对发现 DR-B 把 KnowQA 错计为独立团队：KnowQA 的 Zimu Wang 是 MAVEN-ERE
    数据论文作者。现有六篇清单只能确认 3 个独立团队；正在追查报告提到但未给清晰 ID 的 2025
    directional causal 工作，决定能否恢复到 4。
  - `paper-search` 的 Semantic Scholar 无 key 请求触发 429；Crossref/OpenAlex 有返回，后续改走已知
    ACL ID 的官方页面/PDF，不再消耗重试。
  - 找到并核实 Findings ACL 2025 `2025.findings-acl.43`：这是报告未给清楚 ID 的 independent
    directional causal work。故 `≥4` 数字保留，但把错误计入的 KnowQA 替换为 Xiang et al.；同时将
    MAVEN-ERE 近年 evaluation setting 从至少三类更正为至少四类。
  - 已完成 `docs/replan/B_datasets_audit.md`。DR-B 状态改为有条件通过；原始 MD/PDF 不改，所有冲突
    由审计文件覆盖。B 阶段完成，可以按严格串行顺序进入 DR-C。
  - 首次交付校验发现审计文件标题块有两处 Markdown hard-break 尾空格；已改成空 blockquote 行，
    等待同一校验命令重跑确认。
  - 交付校验重跑通过：审计/计划/发现/进度四个 Markdown 文件均无 whitespace error；审计文件
    98 行、14 个 HTTPS 链接、0 个内部 citation/sandbox token；A/B 计划项均已标完成。
  - 收到 `C_methods_code.md` 与 `C_methods_code.pdf`，C 阶段进入本地交叉核验；D/E 暂不启动。
  - 初检：MD 326 行、46,337 bytes、100 个内部 citation token；PDF 19 页、171 个 URI 注释、
    24 个可恢复真实 Web 来源。导出形态与 B 相同，可组合审计，不需要打回重导。
  - 完成 C 正文结构初审：方法分型与 A 基本一致；发现 TextEE Tables 6–7 被标成严格 A 级证据，
    与 A 已确认的 sample split/聚合缺口冲突，待降级。GitHub 审计也未完全达到原 prompt 的 exact
    SHA/逐命令检查要求，现转入高价值 repo 定向复核。
  - 尝试批量下载/抽取 TextEE、LLMERE、SECURE、CGEL、Wei 五篇官方 PDF，30 秒边界内无输出；
    已停止该方式，后续先识别已落地缓存，再逐篇小批核验，不重复整批请求。
  - 复用缓存完成 TextEE/LLMERE 定向核验：TextEE 同表趋势成立但 sample protocol 不能升为公开严格
    主轴；LLMERE 的指标、split、A100 40GB 配置成立，但 baseline 是否在新 split 重跑与 evaluator
    实现仍未被论文明确锁定。
  - 当前 GitHub API/HEAD 核验五个关键仓库：TextEE、SECURE、SeDGPL 的报告元数据基本准确；CGEL
    仍 404；发现 C 漏报的 `HerbertHu/LLMERE` 仓库实际存在（HEAD `94d4ef27...`，MIT）。
  - clone LLMERE 后确认仓库缺训练入口/环境锁/checkpoint，但有数据转换、evaluator 和示例输出。
    同一命令随后下载 MMD-ERE PDF 再次触及 30 秒边界；已停止该下载路线，不原样重试。
  - MMD-ERE 残留 PDF 缺 trailer/xref，无法 `pdftotext`；ACL HTML 只确认正式发表与作者，未提供官方
    代码入口。按三次失败前止损原则不再下载，代码/硬件/复现结论全部降级为未取得。
  - 完成其余 7 个官方 GitHub 的 API + HEAD 核验；C 对 CALLMSAE、EventRAG、TAG-EQA 的
    star/pushed_at 及 OmniEvent SHA 有错误。已保存准确 HEAD/动态快照，后续 C 审计文件覆盖原表。
  - 由 ACL Anthology 官方页面核对 IEPile、ADELIE、KnowCoder、KnowCoder-X、ASEE 的标题、venue
    与年份；形式身份均与 C 一致，但 C 未完成它们的主表/硬件/commit 级审计。
  - 已完成 `docs/replan/C_methods_code_audit.md`。DR-C 状态改为有条件通过：方法分类和资源候选排序
    可进入后续调研；TextEE、LLMERE、CGEL/MMD-ERE 的证据等级已降级，错误 GitHub 动态元数据与
    SHA 由本地快照覆盖。D/E 仍未启动。
  - 收到 `D_angles.md` 与 `D_angles.pdf`，D 阶段进入本地交叉核验；E 暂不启动。初检确认 Markdown
    208 行、51,646 bytes，含 173 个内部 citation token 和 0 个 HTTPS URL；PDF 19 页、有文本层，
    将用于恢复真实来源链接。
  - 从 D PDF 恢复 37 个真实唯一 URL；读完方法/数据判定后锁定三组优先审计对象：MCECR/MEANTIME
    的跨语言 identity 边界、CrudeOilNews 的 raw text 版权缺口、ESL/CTB 近期 ECI 方法链及其 fold/
    evaluator 可比性。D 的替代方向排序在这些核验完成前不进入最终综合。
  - 官方 MCECR PDF 已直接确认 same-language article retrieval；其 topic/gold chain 不混合语言，故 D
    对跨语言现实事件 identity 缺口的核心判断成立。同时记录约 65% pair 自动标注、10% 自动标注抽检
    的 provenance。CrudeOilNews 正式身份、规模与官方 GitHub 入口也已由 ACL 页确认。
  - CrudeOilNews README 已确认 original news text 因版权不发布，D 对 β 公开 benchmark 不闭合的判断
    成立。ECI 方法身份出现潜在混计：ACL `2025.emnlp-main.616` 是 DECLV 而非 DICP；正在核 DICP
    仓库对应发表身份后再判断“至少 3 个独立近期团队”是否成立。
  - DICP 已确认是 Findings EMNLP 2025 `2025.findings-emnlp.139`，且与 ICCL、Ya Su 团队独立；
    因此 ECI 的 3 个独立近期团队下界成立。下一步核三篇 paper 的 fold、样本构造和指标，决定只能
    说“活跃 benchmark”还是可升到“严格同口径主轴”。
  - ICCL/LKCER/DICP 均明确 ESL 5-fold、CTB 10-fold、P/R/F1，DICP 还沿用 ICCL 采样传统并在单张
    RTX 3090 上实验。可确认方向活跃且硬件可行；exact fold IDs/pair generation 尚未统一锁定，故仍按
    条件性候选而非已完成严格 SOTA 轴处理。
  - ESL 官方仓库已确认 CC BY 3.0、含 annotated/test/eval scripts；但 v0.9/v1.0/v1.2/v1.5 并存。
    CTB 两套 ZIP 可下载但仓库无显式 LICENSE。D 的 ECI 替代切口可保留，须新增 corpus version、fold
    IDs、pair generation 与 CTB 许可未锁定四项边界。
  - ACL 官方页确认 MEE/MINION/EusIE/SPEED++ 的任务边界与 D 一致：它们支撑多语言 EE/迁移，
    不提供 natural cross-language event identity gold。完整 α 的不通过结论可保留。
  - MEANTIME 论文确认其跨语数据来自英文及三语翻译/annotation projection；SPEED++ 确认疫情领域
    event→warning 是真实应用先例。D 的 α/β 主 benchmark 不通过结论现有足够一手证据支撑。
  - 已完成 `docs/replan/D_angles_audit.md`。DR-D 状态改为有条件通过：α/β 的 benchmark 断链确认；
    ECI 的三个独立近期团队、5/10-fold 传统和单卡可行性确认，但 ESL version、exact fold/pair、CTB
    license 尚未锁定。D 不提前决定最终方向，E 仍未启动。
  - D 交付校验通过：审计稿 147 行、16 个 HTTPS 一手入口、0 个内部 citation/sandbox token，审计/
    计划/发现/进度文件均无 whitespace error；A/B/C/D 已标完成、E 保持未启动。D PDF 为 19 页、
    未加密且文件非空。文档审计未运行代码测试或 GPU。
- Files created/modified:
  - `docs/replan/A_terrain.md`
  - `docs/replan/B_datasets.md`（网页版原始输出）
  - `docs/replan/B_datasets.pdf`（网页版 PDF 来源导出）
  - `docs/replan/B_datasets_audit.md`（本地有条件验收与更正）
  - `docs/replan/C_methods_code.md`（网页版原始输出）
  - `docs/replan/C_methods_code.pdf`（网页版 PDF 来源导出）
  - `docs/replan/C_methods_code_audit.md`（本地有条件验收与更正）
  - `docs/replan/D_angles.md`（网页版原始输出）
  - `docs/replan/D_angles.pdf`（网页版 PDF 来源导出）
  - `docs/replan/D_angles_audit.md`（本地有条件验收与更正）
  - `docs/replan/DEEP_RESEARCH_PROMPTS.md`

## Test Results

| Check | Expected | Actual | Status |
|---|---|---|---|
| `git diff --staged` | 无暂存改动 | 空 | ✓ |
| 接管时工作区核对 | 与交接记录一致 | v5/Ch1 改动 + `docs/replan/` 均存在 | ✓ |
| Claude 已记录的代码校验（未在本轮重跑） | pytest/ruff/smoke 通过 | 354 passed / 12 skipped；ruff 0；smoke OK | 交接证据 |
| D 文档交付校验 | 无 whitespace/内部 citation；计划状态正确 | 147 行、16 个 HTTPS、0 citation/sandbox；A–D 完成、E 未启动 | ✓ |
| E 文档交付校验 | 无 whitespace/内部 citation；关键边界齐全 | 164 行、19 个 HTTPS、0 citation；E 有条件通过 | ✓ |

## Error Log

| Timestamp | Error | Attempt | Resolution |
|---|---|---:|---|
| 2026-08-25（上轮） | Claude 五路探索因 session limit 全部提前终止 | 1 | 本轮直接持久化输出后重跑 |
| 2026-08-25（本轮） | 并行探索不符合作者的额度控制要求 | 1 | 中止 B、C，改为严格串行；无部分报告落盘 |
| 2026-08-25（本轮） | A 全块任务长时间运行、两次催促落盘仍无文件 | 1 | 中止大任务并缩为 A1/A2/A3，每个小块完成即写文件 |
| 2026-08-25（本轮） | 外部 Web 调研持续消耗本地代理额度 | 1 | 按作者指示暂停代理，将剩余四路改写为网页版深度研究提示词 |
| 2026-08-25（本轮） | C 交付校验命令因含 `rm -f` 被安全策略拒绝 | 1 | 没有执行删除；改用无临时文件的只读管道校验 |
| 2026-08-25（本轮） | C 外链校验使用 zsh 只读变量 `status` 而中止 | 1 | 已完成的文档结构检查保留；改名 `http_code` 后重跑剩余检查 |
| 2026-08-25（本轮） | 11 条 ACL 外链串行校验在 30 秒边界仅完成 8 条 | 1 | 已完成 8 条均为 200；仅续查剩余 3 条，不重复请求 |
| 2026-08-25（本轮） | 剩余 ACL 外链续查出现 TLS unexpected EOF | 1 | 本轮已有三页成功下载与元数据解析结果；停止重试并用本地页面验收 |

## 5-Question Reboot Check

| Question | Answer |
|---|---|
| Where am I? | Phase 4：综合地形与项目决策 |
| Where am I going? | 综合地形与重构/重开决策 → 作者评审 |
| What's the goal? | 用一手证据为 v6 论文方向做可执行决策 |
| What have I learned? | 见 `findings.md` 和 `docs/replan/LOCAL_ASSET_INVENTORY.md` |
| What have I done? | 完成接管核对并建立持久化计划 |
## 2026-08-25：开始审计 DR-E

- 已确认原始报告：`docs/replan/E_industry.md`、`docs/replan/E_industry.pdf`。
- 初检：Markdown 181 行；PDF 21 页、A4、可搜索、未加密。
- 下一步：恢复 PDF 链接，逐节审计技术、产业案例、岗位与开源活跃度证据。
- 已从 PDF 恢复 240 个链接注释、45 个唯一 URL；已通读可见正文并确定高风险核验项。
- 已补读招聘、OSS、未核实项与证据审计表；进入高影响一手来源抽样核验。
- 浏览工具两轮官方页面抽样均空返回；已记录异常，改走轻量 HTTP 抽样。
- HTTP 抽样：Altana 公告与两个 Outreach 岗位页为 200；Altana schema SSL 失败；GitHub API 403。
- 已读三份官方 HTML：确认 Altana/CBP 部署及 Outreach 的事件检测—时间建模—KG—生产监控技能链；
  已用 A/C 审计复核 event-specific repo 快照。
- 已生成 `docs/replan/E_industry_audit.md`，验收为有条件通过；校验结果为 0 个内部 citation token、
  19 个 HTTPS 来源入口、无 whitespace 错误。
- Phase 2 五路探索与 Phase 3 决策关键交叉核验完成；当前进入 Phase 4 综合地形与项目决策。
- 已完成 B/C 审计与本地资产清单的交集分析，形成 ESL/CTB、固定协议 MAVEN-ERE、event coreference
  三个候选轴，并将“主轴重开”与“代码推倒重来”分离。
- 已复核 A 的术语和任务地形：总题应选 occurrence-level 事件图谱，不选缺统一 benchmark/术语的
  事理图谱；图上新任务暂不具备单独支撑章节的公开竞争闭环。
- 已将 v5 SPEC/TODO 与结果索引对照：Ch1/Ch2 未达公开线，Ch3 结果最强但 split 未闭合，Ch4 图侧
  效应全部落在噪声地板；主轴重开的证据已显著强于继续局部补洞。
- 已逐读 Phase A/C/D/E 权威结果并纠正 README 的 Ch1 口径冲突：最终综合使用 MUC 77.47，
  确认 v5 无一章当前无保留满足“公开同轴超过多个方法”。
- 已完成候选任务矩阵：ESL/CTB ECI 为唯一条件性主锚，固定协议 MAVEN-ERE 为第二候选；其余只列
  储备或应用验证。尚未、也不应在作者认可前拼装 3–4 章。

### Phase 4: 综合地形与项目决策

- **Status:** complete
- 已生成 `docs/replan/SYNTHESIS_DECISION.md`（185 行，13,688 bytes）。
- 决策：选 occurrence-level 事件图谱；重开论文主轴但迁移当前工程资产；ESL/CTB ECI 作为条件性主锚。
- 验证：0 个内部 citation token；四个 v5 决策数字均回 `docs/results/PHASE_*.md`；本地链接存在；
  Markdown whitespace gate 通过。
- 当前 Phase 5：等待作者评审；未设计章节、未修改实现代码、未运行 GPU。

### Phase 5: 作者评审

- **Status:** complete
- 作者接受 occurrence-level 事件图谱、重开论文主轴、ESL/CTB ECI 优先资格验证。

### Phase 6: ESL/CTB ECI 资格验证

- **Status:** in_progress
- 已生成 `docs/replan/DR_F_ECI_PROTOCOL_PROMPT.md`，供网页版 GPT 深度研究执行。
- 建议附件：`D_angles_audit.md`、`SYNTHESIS_DECISION.md`。
- 期望回传：`F_eci_protocol.md`、`F_eci_protocol.pdf`。
- 当前未启动本地 Web 深搜、代码复现或 GPU 实验。
- 2026-08-26 已收到 `F_eci_protocol.md/.pdf`；初检为 Markdown 474 行、PDF 17 页可搜索。
- 已进入本地协议与来源审计；F 原文件保持不改。
### 2026-08-26：DR-F 全文初读完成

- 已逐节读完 `docs/replan/F_eci_protocol.md`；报告结论为 NO-GO。
- 已定位需本地复核的关键缺口：Shen et al. (2022) 工具链未被识别，以及 D/F 两轮报告的硬件和许可证冲突。
- 下一步：按“官方论文 → 官方代码仓库 → 数据版本/划分/候选对/evaluator”的顺序做一手交叉核验；此阶段不启动 GPU、不复现实验。
- 已提取 F PDF 全部链接：62 个注释、11 个唯一 URL；确认关键仓库与 Shen 2022 工具入口未进入 PDF 链接证据链。
- 已开始逐仓库核验；EventStoryLine 官方仓库已克隆到临时目录 `/tmp/ekg-f-audit.vjo1yq/EventStoryLine`，未修改项目仓库。
- 已完成 EventStoryLine 与 Causal-TimeBank 的第一轮仓库/许可核验：F 的两项许可证结论均与当前一手仓库冲突，且记录的 HEAD 均不匹配；已保存证据，继续审计基线仓库与协议文件。
- 已克隆并初查 ICCL、DICP 官方仓库：两者均实际包含划分/样本生成/评估代码，F 的“协议组件完全缺失”表述需要修正。下一步逐行核对数据生成规则、论文实验口径和算力声明。
- 已细读两仓库的数据生成规则：ICCL 明确实现 ESC 全文档事件对与 5 折；DICP 明确实现 CTB 同句事件对与 seed 6688 的 10 折。也确认二者都有依赖、路径和数据缺失，暂不具备双 baseline 同协议直接复跑条件。
- 已核验四篇 ACL 官方论文：确认 DICP 使用单张 RTX 3090（F 的 V100 说法错误），并发现 DICP 论文与代码在 CTB 文档/事件计数上不一致。已识别 Shen 2022 为 DPJL，继续追其官方协议工具链。
- 已从 COLING 2022 官方索引定位 DPJL 的 ACL Anthology ID：`2022.coling-1.200`。
- 已完成 DPJL 官方论文与代码入口核验：论文有纸面协议但无 fold seed/manifest，承诺的代码链接未出现，也未检索到官方仓库；F 所称“Shen 2022 共用工具链”缺乏事实基础。
- 已完成公开数据 CPU 只读计数：CTB 官方 ZIP 的 183/6811/318 与 DICP 代码完全一致；ESC v0.9 可从官方仓库明确冻结。数据可得性/版本门由 F 的绝对失败上调为可解决。
- 已检查 ICCL/DICP 完整 Git 历史：确认不是当前分支漏文件，而是两仓库从未提供同一数据集上的双实现。当前不满足“两支独立 baseline 同协议可跑”，停止在静态/CPU 资格审计阶段，不启动 GPU。
- 已生成 `docs/replan/F_eci_protocol_audit.md`：DR-F 因论文身份串线、仓库/许可/硬件错误不通过事实验收；本地独立结论仍为当前 NO-GO，决定性原因仅为同协议双 baseline 门失败。Phase 6 已完成，不运行 GPU。
- 已补充官方元数据、ICCL seed/评估及 DICP 缺失 import 核验，并同步修正审计文档的 27GB 结论：纸面高可行，但执行闭环未过。
- 已做交付前结构校验：`F_eci_protocol_audit.md` 为 101 行/7,815 bytes，无 ChatGPT 内部 citation token；项目无 staged changes，既有代码改动均保持未触碰。下一步整理 DR-G 提示词，不自行展开高 Web 成本检索。
- 已生成 `docs/replan/DR_G_MAVEN_ERE_CAUSAL_PROTOCOL_PROMPT.md`，把官方 hidden test、Chen/LLMERE valid-as-test、Xiang causal-only 强制分轴，并要求先核论文身份、再查仓库实际文件。Phase 7 等待用户交给网页版深度研究执行。
- 首次机械校验仅发现 DR-G 小节标题少“至少”二字（正文门槛未缺）；已统一为“寻找至少两个独立近期 baseline”，待重跑校验。进程列表中的 5090 任务属于其他项目，不是本轮启动，未触碰。
- 修正后已重跑交付校验并通过：F 本地审计 113 行/8,496 bytes，DR-G 提示词 227 行/10,762 bytes，task plan 130 行/9,720 bytes；三者结构、内部引用残留、tab、尾随空白和结尾换行检查全通过。无 staged changes，无 ICCL/DICP 训练任务运行。
### 2026-08-26：DR-G 接收与审计启动

- 已确认 G Markdown/PDF 文件存在并进入 Phase 7 本地核验。
- planning-with-files 的 `session-catchup.py` 直接执行时报 `permission denied`；原因是脚本无执行位，后续使用 Python 解释器调用，不重复直接执行。
- 首次落盘补丁因同一 patch 中重复声明 `task_plan.md` 而被拒绝；第二次因猜错错误表分隔行而被拒绝；两次均未产生部分修改，读取实际结构后第三次精确落盘。
- 未修改原始 G 报告，未启动 GPU 或训练。
- 已用 Python 解释器成功运行 session catchup；无额外输出，未发现待同步提示。
- 已完成 G Markdown/PDF 的结构与链接盘点：PDF 可搜索，但仓库链接证据主要只能依赖 Markdown。
- 已逐行读完 G Markdown。报告结论为 NO-GO，初步逻辑自洽；已定位 valid causal 9,698 vs 本地权威 6,599 的高影响口径冲突，下一步先用本地官方数据/evaluator核验。
- 首次本地数据枚举因 zsh 对不存在的 `data/MAVEN_ERE/*.jsonl` 空 glob 报错而提前终止；改用 `find -print0` 后成功完成。
- 已确认本地三 split 数据及 SHA-256、官方 evaluator、LLMERE split/evaluator 均可用；开始重算 causal 计数口径。
- 已用本地 JSONL + 官方 evaluator 逻辑重算 causal 统计，确认 G 的 full-valid 9,698 与本地 497-subset 6,599 无冲突，并锁定 full-valid mention 展开正例/候选总数。
- 已在 `/tmp` 成功执行 LLMERE seed42 split 并记录三份文件/ID manifest SHA-256；B split 门本地通过。发现发布仓库缺 evaluator 的两个输入辅助文件，继续检查 converter 能否完整重建与分数是否一致。
- LLMERE evaluator 首次 smoke 未完成：shared tools venv 缺 `sklearn`；同时发现当前 converter 预期 29,080 rows、发布预测仅 29,079 rows。已记录，改用项目 uv 环境并先定位差异。
- 改用项目 `uv` 环境后 evaluator 成功重放 F1 36.04399；“少一行”确认为末行无换行的 `wc` 计数假象。B 协议四项（data/split/pair/evaluator）本地闭合。
## 2026-08-26：G 审计继续

- 已定位 G 对 Chen/LLMERE 的全部关键论证；下一步只核验 Chen 作者仓库与论文附录中的 candidate universe、split/cache 可恢复性和输出粒度。
- 尚未启动任何 GPU 任务；若 Chen 不能构成第二个 exact-B baseline，将直接停止在 baseline gate，不做无效显存 smoke。
- Chen 作者仓库已在 `/tmp/chen-audit.xKtypg/Teach-LLM-LR` 完整克隆并完成 tree/history 初检；接下来检查 `src/data.py` 的采样逻辑与两份 MAVEN cache 的覆盖范围。
- Chen cache 覆盖范围已核验：test=500 prompts/302 docs/1,000 directed pairs，且完全排除双向四轴全空样本；与 exact-B 的 613,706 all-ordered pairs 明确不兼容。
- Chen cache 的 302 个 test 文档全部映射到 official valid；正在补纸面 Appendix E 的原文核验与 repo 历史检查。
- Chen Appendix E 与完整 git 历史核验完成：论文主动定义 500-sample sentence-level testbed，仓库历史从未发布 all-pairs 生成/训练/预测链。Chen 不能作为 exact-B 第二 baseline。
- LLMERE 完整 5-commit 历史也已核验，确认从未发布训练/推理 package；开始编写最终 `G_maven_causal_protocol_audit.md`。
- Xiang 公开代码 task mismatch 与 KnowQA 当前 404 已复核；静态候选穷尽未发现 exact-B 第二个独立可执行方法。
- 已写入并初检 `docs/replan/G_maven_causal_protocol_audit.md`；Phase 7 标记 complete，Phase 8 保持 pending，当前进入作者决策检查点。
- 收尾前按 verification-before-completion 要求开始 fresh verification：将重新核对数据/split 哈希、evaluator 输出、文档结构与工作树范围后再交付结论。
- fresh verification 已完成：原 evaluator 再次输出 613,706 candidates、P=34.98446、R=37.16970、F1=36.04399、support=13,624；official 三文件与 B 三 split 的 SHA-256 全部匹配审计文档。
- 最终文档/计划 gate 通过：audit 必需结论齐全、无 ChatGPT 内部 citation token、无尾随空格，Phase 7 complete、Phase 8 pending；全局工作树中既有 v5/Ch1 代码改动未被触碰，staged 为空。

## 2026-08-26：启动 DR-H 时间关系资格审查

- 作者批准按推荐方案严格串行扩大候选池：先审 MATRES / TB-Dense，不与事件共指、事实性并行混审。
- 已生成 `docs/replan/DR_H_TEMPORAL_PROTOCOL_PROMPT.md`，目标是让网页版深度研究先映射协议轴，再只深挖最可能通过的 exact protocol。
- 未运行新的 Web 检索、训练或 GPU；下一步等待作者在网页版执行并导入 H Markdown/PDF。

## 2026-08-27：接收 DR-H

- 已发现 H Markdown/PDF 及两份 `Zone.Identifier` sidecar，并将 Phase 7b 的接收项标记为完成、核验保持 in progress。
- 尚未修改原始 H 报告，尚未运行训练或 GPU。
- 已完成 Markdown/PDF 结构与来源恢复检查，并逐段读取 H Markdown；中心结论和协议分轴逻辑初步自洽。
- 下一步严格串行：先核本地 MATRES relation 文件和许可边界，再取得 TCT software.zip 与 Roccabruna 仓库做静态兼容性审计。
- 已完成本地 MATRES annotation 只读 census/hash：182/73/20 docs、6336/6404/837 raw pairs、5481/5728/724 VAGUE-drop pairs；Git blobs 与 CogComp 指定 commit 完全一致。
- annotation-level split/pair manifests 已可冻结；下一步检查本地是否有合法 source TML 与许可记录，然后审计 TCT archive。
- 已确认项目内没有 TempEval `.tml` source 文件或 LDC/TempEval license/hash 记录；annotation 在位不等于模型输入闭环。
- TCT Web open 返回空，已记录错误；下一步改用 `curl` 取得官方 software.zip，不重复空调用。
- TCT `curl` 已启动但超过 30 秒返回窗口，进程仍存活且部分文件在增长；进入单进程监测，不做重复请求。
- 同一 TCT 下载进程已自然结束，最终文件 1,364,620 bytes；未启动第二份下载，开始校验 archive。
## 2026-08-27：H / TCT 官方附件初步审计

- 已从 ACL Anthology 下载并校验 TCT `software.zip`（SHA256：
  `dbf11f4ad3cabd5b721bb18d8e37dcb51f5da0cc6878f3ff9522b87622160e4e`）。
- 附件有效且含处理后数据和部分训练/评测代码，但缺 README、环境、许可、入口、预处理、权重与版本历史；
  已发现若干缺失导入及疑似存取格式不一致，尚不足以构成可执行闭环。
- 当前动作：继续核对 MATRES JSON 标签口径与 evaluator；仍未运行训练、GPU 或修改项目代码。

### TCT 聚焦复核完成

- 确认训练/验证是 TimeBank+AQUAINT 合并后的 10,888/1,852 重切分，不是固定 train/dev；
  测试标签分布也与本地 CogComp Platinum 不同。
- 确认测试保留 VAGUE，并只在 `classification_report` 的标签集合中排除它，属于 Vneg，
  不等于候选的 VØ/724-pair accuracy。
- 确认缺失导入和 checkpoint 载入方式冲突；TCT 官方附件无法原样执行。
- 已据此判定 TCT 不能提供第二条同口径 baseline；继续串行静态核对 Roccabruna，仍不运行 GPU。

- Roccabruna 官方仓库的临时只读克隆已完成；固定审计提交
  `41eb1ed036cd4b5741b17dc07f809311cc915016`。仓库有 README、requirements、LICENSE 和主要代码目录；
  进入 MATRES 数据/评分/入口的静态核验，不下载模型、不推理。

- 已确认 Roccabruna 的 MATRES split、VAGUE 删除方式和三分类 accuracy 与候选协议一致，可保留为
  第一条 baseline；同时确认 README 所指 `run_exps.sh` 不能原样执行，需要手工构造单实验命令。
- 当前只剩报告数字/配置与数据许可的终审；由于第二 baseline 已失败，不会进入 GPU。

- 终审发现论文附录的 MATRES train/dev/test 为 9,074/2,133/724，与仓库 formatter 在本地
  CogComp annotation 上应得到的 5,481/5,728/724 冲突；仓库又没有处理后数据/预测/结果/权重。
- 因此已把 Roccabruna 87.6 从“可直接引用的同口径 baseline”降为“仅测试集与标签口径相同、
  train/dev 不可核实的条件候选”。H 的 baseline 门槛比原报告判断更差，NO-GO 不变。

## 2026-08-27：H 本地审计完成

- 已新增 `docs/replan/H_temporal_protocol_audit.md`，原始 H Markdown/PDF 保留不改。
- MATRES annotation 的版本、182/73/20 split、5,481/5,728/724 VØ pairs 与 hashes 均已冻结；
  完整 TML/许可仍失败。
- TCT 官方附件已确定为重切分、Vneg 且执行链不闭环；Roccabruna 论文 split counts 与 formatter 冲突。
- 最终为 NO-GO；未运行训练/GPU，未修改项目代码。下一候选等待作者确认。
- 交付前已重新计算全部 MATRES hashes/counts，并完成纯 CPU evaluator 恒等式检查；全部通过。
- 最终文档结构、空白、必备结论、TCT archive SHA/counts 与 Phase 7b 状态检查均通过；工作树中的
  既有 v5/Ch1 代码改动保持未触碰。

## 2026-08-27：I / 事件共指提示词准备启动

- 作者批准按推荐继续审 ECB+ / GVC / FCC，并要求保持严格串行。
- 当前仅准备网页版 Deep Research 提示词与最小附件清单；尚未检索、下载或运行实验。
- 已复核既有 H/G 提示词格式和综合报告中的事件共指边界；确定使用 4 个 Markdown 附件、输出 I 的
  Markdown+PDF，重点审计 SECURE 协议轴及多个独立近期方法，而不是按分数拼表。
- 已生成 `docs/replan/DR_I_EVENT_COREF_PROTOCOL_PROMPT.md`；Phase 7c 进入等待网页版报告状态。
- 已检查四个附件均存在、提示词 Markdown 结构与 whitespace gate 通过；未触碰既有代码改动。

## 2026-08-27：顶层方向纠偏

- 作者否决继续按单一语料资格门逐项淘汰候选，要求抓住“把事件图谱构建论文拆成完整硕士论文”的
  本质，且不限定全篇语料类型。
- 已暂停 DR-I 的执行建议；下一步读取现有 SPEC、v5 四章活线、综合报告和本地资产，直接提出统一
  构建流水线下的章节分解，并区分真正硬约束与可工程解决的问题。
- 已完成对 `SPEC.md`、`TODO.md`、A2/C3/D2/E2 phase 契约和 `EXPERIMENTS.md` 的核对：现有 v5 四章
  已经是合适的组件化论文骨架，问题在于后续资格标准过度收紧，而非缺少论文主线。
- 已将修订后的“公开可比”定义写入 `SPEC.md`，并新增 `THESIS_COMPONENT_REFOCUS.md`。
- 已标记 `SYNTHESIS_DECISION.md` 的“重开 v5”决策为历史结论、H 的 NO-GO 为旧口径结论、DR-I 为暂停。
- Task plan 已转入 Phase 8：刷新四章实施矩阵后，按 Ch2 → Ch1 → Ch3 → Ch4 严格串行恢复实验。

## 2026-08-27：独立可行性审查启动

- 作者要求引入独立审查，覆盖资源、无人工标注、标准指标、方法贡献、工作量与论文叙事闭环。
- 将只启用一名独立审查者并串行等待，避免并发额度消耗；审查者不得运行 GPU、不得修改实验代码。
- 独立审查者已完成有实质内容的前半报告，但补写回合因中断命中先删后写窗口，文件暂时消失；已记录，
  将由同一审查者直接重建最终文件，主代理不代写 verdict。

## 2026-08-27：独立审查完成

- 独立审查报告已完成：`docs/replan/INDEPENDENT_THESIS_FEASIBILITY_REVIEW.md`。
- 审查采用现有仓库实测数字，未启动本地/远端 GPU，未运行 ssh，未改动实验代码。
- 已用权威结果文件交叉核对 Ch1/Ch2/Ch3 与 Ch4 样本量关键数字；`git diff --check` 与审查报告单文件 whitespace check 均无报错。
- 审查结论为 CONDITIONAL：资源与工作量可行，但需先冻结协议，并按 Ch2 → Ch3 → Ch1 → Ch4 的实验顺序执行阶段闸门。
- 已据审查修订 `THESIS_COMPONENT_REFOCUS.md`：收敛三个最小方法贡献、Ch4 同实例 factorial、
  95–180 单 GPU 小时预算，以及各阶段 Done/止损条件；`TODO.md` 顶部增加覆盖说明，防止继续引用
  “Ch3 已过线”的跨 split 旧判断。
- 最终一致性检查通过：两份新增方案文档 whitespace clean；关键顺序、资源预算、1,908-query 桥梁与
  CONDITIONAL verdict 均可从独立报告、收敛方案和实时状态交叉定位；旧 `Ch2 → Ch1 → Ch3 → Ch4`
  顺序已不再出现在收敛方案的执行指令中。

## 2026-08-27：SPEC 与后续闸门落地启动

- 作者要求写好权威 SPEC，并实际执行后续资格筛查，同时把阶段任务和终止条件固化，防止上游错误继续
  传播到后续章节。
- 本轮保持严格串行：先重写 SPEC，再做纯 CPU/只读 Gate G0 静态筛查，随后按筛查事实写阶段契约；
  不启动本地或远端 GPU，不并行引入新代理。
- 已将 `docs/SPEC.md` 从 319 行历史混合稿重写为 271 行 v6 执行总纲，固定四章、两层评测、跨章契约、
  G0–G5 串行闸门、两轮修补上限、stage bundle 和错误不累计规则；whitespace 检查通过。
- 首次禁词正则因缺少否定语境误报“不得复活成方法卖点”；未把误报当文档错误，已记录并改用明确旧句
  检查。当前转入 Gate G0 静态筛查。
- Gate G0 本地数据/产物初筛完成：四个主数据文件 hash 与 ID 对齐已验证；三份 710-doc 历史预测产物
  与 valid 零缺失/零重复；七个关键 CLI 的 CPU import/help smoke 通过。
- 初筛同时确认四个缺口：官方 evaluator 本地缺失、Ch1 无 internal-dev 选模、Ch2/Ch3/SeDGPL 权重
  未全部本地就位、Ch4 缺冻结 query manifest/事实性节点属性/frozen consumer。尚未启动 GPU。
- 按预先展示的命令完成 4090 只读资产核验：四章历史 checkpoint/权重路径与官方 evaluator 均存在，
  Ch3 dump 双端 hash 一致；未访问 5090、未占用 GPU。官方 evaluator 仍在 `/tmp`，目录内容与恒等
  scorer smoke 继续列为 G0 待核项。
- 第二轮 4090 静态清单确认各 checkpoint 必需文件在位。第一次 official evaluator gold-self smoke 因把
  labelled raw 当 prediction schema 而失败；已如实记录，不重复原命令，下一步按 evaluator 实际输入格式
  构造可重放的 gold prediction。
- 已生成正确 mention-pair 展开的临时 gold prediction 并记录 hash；生成+传输+评分合并命令在 30 秒窗口
  内未返回评分，下一步只核远端临时文件并单独评分，不重复已完成部分。
- 已核远端临时文件 hash 后单独运行 official scorer，全部关系与共指 P/R/F1 均为 100，evaluator 语义
  smoke 通过。随后核查 baseline checkout：official/RESIJ/Ch3 强基线/BART 均未持久化，G0 baseline
  closure 保持 CONDITIONAL。
- 已生成 `docs/replan/G0_PROTOCOL_GATE_SCREENING.md`，逐项给出全局与 Ch1–Ch4 的
  PASS/CONDITIONAL、放行条件、修复顺序和停止条件。总体 G0=CONDITIONAL，明确不准直接开完整 GPU；
  当前转入新 phase 契约与实时状态重写。
- 已重写 phase 索引与 TODO，新增 P1/A3/D3/C4/E3/H2 六份可执行契约；每份均含输入、任务、promotion、
  Done、Stop、bundle handoff 和 GPU 边界。六份 v5 契约已标 `SUPERSEDED`，不删除历史结果。
- 已同步更新 `AGENTS.md` 与 `CLAUDE.md` 的 v6 主线摘要，并重写 `EXPERIMENTS.md` 为 v6 baseline/消融/
  统计/schema 协议。根指令逐字同步、本地链接检查已通过；禁词检查仅因否定句误报，已记录并改判据。
- Phase 9 文档 gate 通过：13 份活动/权威文档本地链接全存在，根指令逐字同步，唯一活线/顺序/G0
  CONDITIONAL/旧契约 SUPERSEDED 的正向断言全部通过，tracked 与新增文档 whitespace clean。
- 本地 `uv run pytest` 通过：354 passed、12 skipped（均为本地无 torch 的预期 GPU skip）。
- 本地 `uv run ruff check src tests scripts` 通过：`All checks passed!`。
- 本地 `uv run ekg-smoke` 通过：CPU 端到端冒烟正常完成。
- 本轮未启动 GPU 训练/推理，未访问 gpu-5090，未提交或推送。
# 2026-08-27：v6 独立反方审查

- 已读取 planning-with-files 全部说明并执行 session catchup。
- 已确认工作树存在大量用户既有未提交改动；本轮将保持只读，除工作记忆文件外不覆盖任何现有修改。
- 已将审查加入 Phase 10；下一步完整读取 13 份目标文档并建立一致性矩阵。
- 已完整读取 `docs/SPEC.md` 与 `docs/EXPERIMENTS.md`，记录首批跨文档门槛冲突与指标核实项。
- 已完整读取其余 11 份指定文档，并抽查权威历史结果中与 Ch1/Ch3/Ch4 归因直接相关的段落。
- 已形成阶段级初判：P1 有 Ch4 过度前置；D3 双向机制过严；E3 消费者 sanity 与零效应假设冲突；全篇收缩规则需修正。
- 已从 ACL Anthology 论文和官方 GitHub 核实 MAVEN-ERE、MAVEN-FACT、CGEP 的任务、官方指标、公开代码与已披露硬件；开始追查具体 baseline 身份。
- 已核实 RESIJ 论文身份但未找到官方代码；并发现 Ch2 固定 loss weighting、Ch3 label→evidence pipeline 都已存在于一手基线，需相应收紧创新表述。
- 已实算 ERE/FACT 三层 ID 完全对齐；审计 291-doc internal-dev 稀有类支持数，并确认统计重采样单位需从 query/mention 改为 document cluster。
- 已核实 CGEP 原论文的 20% dev/original-valid test 与随机候选构造；本地 1,908-query 协议可作统一重跑轴，但不应冒充可逐项核对的官方派生发布。
- 已完成逐章、逐阶段、错误传播与创新性裁决；最终为 `ACCEPT WITH REQUIRED REVISIONS`。
- 已整理可直接写回的必要条款与 8 项以内首轮 GPU 放行条件；本轮未修改 13 份被审文档，未启动 GPU、训练、提交或推送。

# 2026-08-27：v6 审查整改落地

- 已恢复 session 并确认工作树含大量用户既有改动；整改范围限定为 v6 权威文档和本轮规划记录。
- 已登记 Phase 11，下一步依次修订总纲/实验协议、阶段契约、实时状态和 G0 解释，再做全局一致性验收。
- 已完成 `SPEC.md` 与 `EXPERIMENTS.md` 第一批修订：主锚/matched seeds/document-cluster CI、final-valid
  访问账本、核心/二级机制、Ch4 predictive validity/graph sensitivity 和全局失败算术已写入。
- 已同步所有 active phase、TODO 和 G0：P1 只前置 A3 最小条件，RESIJ 改可选，D3/C4 二级机制不再合取，
  E3 完整本地重建 manifest 留在 E3.0，H2 的一个/两个方法章失败算术已修正。
- 一次跨三文件补丁因 E3 目标文本与实际换行不匹配而原子失败，无文件部分变化；读取精确上下文后拆成
  可匹配补丁，补入三种子 delta 聚合、Ch4 CI 判据和一手证据边界。
- 第一轮验收通过：12 份整改文档的本地 Markdown 链接全部存在；tracked 与新增 phase 文件均通过
  whitespace 检查。
- 第二次大补丁也因 Markdown 实际换行与预期上下文不一致而原子失败；精确读取后已成功补入护栏 CI
  公式与 Ch4 checkpoint 跨 arm 复用规则，无部分丢失。
- 已复核 `docs/results/README.md`：其内容是历史实测单一事实源，观察到的噪声地板与旧阶段结论没有被
  规划修订覆盖；无需改动。最新一轮全部整改文档 whitespace 仍 clean。
- 完整复读 SPEC/EXPERIMENTS/P1/E3/H2 后修正了三处执行歧义：组件失败 arm 的 Ch4 身份、P1.6 的真实
  前置项、gold-self 与 confirmatory final-valid 访问计数分离。
- 终局跨文档策略审计通过：24 项 required checks 全部命中，5 类旧规则全部缺席；12 份整改文档再次
  通过 whitespace 与本地链接检查。
- Phase 11 已关闭：规划层 REQUIRED REVISIONS 全部写回；本轮未改实验数字、未启动 GPU、未访问 5090、
  未提交或推送。G0 仍为 CONDITIONAL，下一步是执行 P1 而不是直接开完整 baseline 训练。
- 最终复核再次通过：active policy 无旧规则，历史独立报告有明确 superseded 边界，全部目标文档
  whitespace/local links clean。

# 2026-08-27：执行 P1

- 作者明确授权执行 P1；已重新读取 planning-with-files、恢复 session 并确认工作树仍含大量既有改动。
- 本轮将只修改 P1 所需代码/测试/协议产物/状态文档；不覆盖无关 dirty changes，不启动完整 GPU 训练。
- 远端 4090 只允许最后的 checkpoint/最长输入小样本 smoke，执行前必须先展示准确命令、目录和产物。
- 已读取 active P1 并完成第一轮文件盘点：完整数据在位；显式 v6 protocol、persistent evaluator、bundle
  validator 与三个 baseline closure 仍需逐项核实/实现。
- 已确认两份 processed manifest 含旧绝对路径；official evaluator 仅在 `/tmp`，official single/joint
  baseline 源码未在项目目录持久化。
- 已确认 relation trainer 尚不支持显式 dev manifest；官方 GitHub 的浏览器直开无返回，转用 Git/curl
  固定一手 source commit，不把空返回误判为仓库失效。
- 已用 Git/curl 固定 official repo commit 与 evaluator hash；下一步实现可重复 fetch/freeze 脚本并生成
  `data/protocols/v6/`。
- 已核 ERE/FACT 真实 schema、local candidate enumeration 与 official scorer mention-pair semantics，足以
  定义稳定 candidate digest/population counts。
- P1 Ch2 候选协议第一批实现完成：官方 cluster→mention expansion、显式 train/dev manifests、train/dev
  污染修复和相应 CPU tests 已落地；定向测试 `17 passed`。
- P1.3 scorer gate 完成：新增严格 wrapper、gold converter 与四个固定 adversarial fixtures；20 个相关单测
  通过，710-doc gold-self/四 fixture 官方评分全部通过，产物写入 `data/protocols/v6/evaluator/` 与 access ledger。
- P1.1/P1.2 freeze 脚本已运行成功：六份显式 manifests、支持数、Ch2 candidate/label digests、Ch4 namespace/
  generator contract、预注册规则和 portable processed manifests 已生成；首次 temporal support 统计漏 TIMEX
  时按 fail-fast 修复后才生成 registry。
- P1.4 bundle validator 已实现并通过 4 类故障测试；同时统一 scorer/manifest candidate-ID 编码，final-valid
  digest 两端一致。相关定向测试共 7 passed，gold-self 重放仍通过。
- P1.5 official source lock 已增强：tracked compatibility patch 可重复应用，source diff clean、四个入口/模型
  文件均可编译；来源 commit、license、patch/evaluator hash 写入 `source_lock.json`。
- P1.5 三个必含 baseline 的统一 10-doc schema smoke 已通过；全部产物/metadata 写入
  `data/protocols/v6/baselines/`，并明确 constant-NONE/schema-only 边界，尚未把 A3 entry 判 pass。
- P1 本地三件套全绿并持久化：364 passed/12 expected GPU skips、ruff clean、CPU smoke OK。
- 已进入 P1.6 准备：本地前置均已满足；下一步先做 4090 checkpoint 文件只读解析，再展示并运行唯一的
  真实模型 load/最长文档+10-doc inference 命令。
- 首次 4090 只读 SSH 在 key exchange 阶段被 peer reset，远端命令未执行；尚未把 checkpoint 或 GPU 状态
  判为缺失/占用，按 runbook 保持“SSH 失败”状态。
- 第二次 4090 SSH 在 banner exchange 超时；同时本地 P1 bundle 已闭合并验证，状态正确拆为 global=pass、
  A3 entry=conditional。最长 internal-dev fixture 已冻结，待连接恢复只跑 load/forward。
- 第三次 4090 SSH 仍在 banner exchange 超时；停止同轮重复连接。P1 本地/全局交付继续收尾，A3 不放行，
  等隧道恢复后原样补 P1.6 并重建同 bundle 即可。
- 已新增 `docs/results/PHASE_P1.md` 并同步 TODO、phase index、P1 contract 与 G0 覆盖说明；所有文档都明确
  global PASS/A3 conditional，未把 schema-only smoke 或历史 checkpoint 清单冒充真实模型 forward。
- 最终本地全链重放与 hash/link/whitespace 审计全部通过；当前没有未处理的本地 P1 缺口。唯一待办仍是
  外部 4090 隧道恢复后的 P1.6，完成前不启动 A3。
- 2026-08-28 作者确认其终端已可 `ssh gpu-4090`；恢复 P1.6，先重复已展示的只读 GPU/checkpoint 清单，
  成功后才选择并展示真实前向命令。
- Codex 环境的首次恢复连接仍在 banner exchange 超时；作者侧成功与当前工具侧结果不一致，远端命令没有
  执行。下一步只诊断本环境 SSH alias/端口，不重复同一连接命令。
- 本地 TCP 到 cpolar 端口可建立，但 10 秒无 SSH banner；已把故障定位到端口接入后的转发/SSH 服务响应，
  尚未进入 key 认证。继续检查是否存在作者已建立的本地 SSH/control socket 可复用。
- 发现作者侧成功连接仍作为普通交互 `ssh gpu-4090` 活着，且没有可复用 control socket；为避免干扰作者
  shell，不注入其 PTY。需作者先退出该测试 session，Codex 才能重试独立连接。
- 按作者要求由 Codex 自行排障：使用真实 PTY、hostname 和 60 秒窗口的新连接仍在 key exchange 前被 peer
  reset，确认不是非交互/短 timeout 所致。下一步搜索已经配置的备用 4090 入口或跳板。
- 显式 ControlMaster 有界重连在第 5 次成功；4 张 4090 均空闲，远端与本地 commit 一致且 CUDA 可用。
- 选择与当前 architecture 严格同形、有训练日志的历史 `a4090_ctrl_accum1` 做兼容 smoke；未搬运 5090 上
  的历史最佳档，也未把 internal-dev 日志分数写成 v6 baseline 证据。
- GPU 0 上 longest internal-dev 1-doc 与 frozen 10-doc 真实前向均成功，无 OOM/skip；prediction/log 回传后
  双端 hash 一致，并通过本地 strict ID/endpoint/subtype/candidate-digest 验证。
- `remote_smoke.json` 与重建 bundle 均通过；最终状态为 `global_protocol_status=pass,
  a3_entry_status=pass, remaining_condition=null`，confirmatory count 仍为 0。
- P1 权威结果、TODO、phase index、G0、AGENTS/CLAUDE 已同步，唯一活动阶段切换到 A3.0；本轮未启动 A3
  训练、未访问 5090、未提交或推送。
- 最终状态审计与本地三件套重跑通过：364 passed/12 expected no-torch skips、ruff clean、ekg-smoke OK；
  为本轮建立的 SSH ControlMaster 已正常关闭，服务器无遗留运行任务。

# 2026-08-28：P1 独立反方复验

- 作者要求再次独立审查所有组件；启用 planning-with-files 与 analysis validation 流程，先只读重算，不把
  当前 PASS 当作前提。
# 2026-08-28 · P1 独立复验追加进度

- 核对了 A3 本地训练器与 MAVEN-ERE 官方 causal/joint 数据入口。
- 确认正式 baseline 的冻结 split 适配仍需 A3.0 入口级验证；P1 的 schema smoke 不能替代 full-run 输入适配。
- 阅读了 A3 契约和两个官方入口；确认 A3.0 还没有可直接执行的 official baseline full-run launcher。
- 审阅了 stage-bundle 验证器、P1 builder 与全部相关测试；定位到外部证据哈希未验证、P1.6 仅凭顶层 status 放行的闸门缺口。
- 在临时目录成功复现两种误放行：外部哈希篡改仍通过 validator；伪 remote pass 仍把 A3 放行为 PASS。
- 对照 SPEC、P1 契约、G0、TODO、phases README 和 P1 结果档，确认状态文本一致但与实际 validator 能力不一致。
- 检查 preregistration、access ledger 与本地 gate；发现 scorer fixture 重放会无条件把 confirmatory count 重置为 0。
- 确认 protocol freezer 也会重置同一计数；记录当前 dirty worktree 边界，未覆盖用户已有改动。
- 审阅 baseline smoke adapter、strict wrapper 和正式 scorer CLI；发现正式评分未强制 pinned evaluator/candidate digest，且结果 JSON 缺 provenance。
- 审阅 protocol freezer 与本地关系训练器；确认 freezer 的 raw-ID 检查成立，但 trainer 没有执行其自述的 v6 required flag，也不验证 frozen hashes/digests。
- 继续检查 trainer checkpoint、submission builder 和 pair evaluator；发现 run provenance 缺失、推理 skip 仍返回成功、辅助 pair scorer 对 ID 不 fail-fast。
- 重跑全套本地门：364 passed / 12 expected skips，ruff PASS，CPU smoke PASS。
- 完成 Phase 13 独立复验；裁决为 P1/A3 entry 暂时 CONDITIONAL，修复范围有界且不推翻现有数据/evaluator/remote smoke。
- 追加核对 remote clean commit 与 local dirty diff；未发现会推翻既有 forward 证据的推理语义差异。
- 一次合并工作记忆 patch 因 task-plan 上下文不匹配失败；已记录，未影响仓库生产文件。

# 2026-08-28 · Phase 14 P1 闸门加固

- 作者明确要求解决独立复验发现的全部问题；开始完整实现，不启动 GPU、不访问 5090、不覆盖旧 P1 bundle。
- 成功标准：两类已证实误放行均变为失败，A3 正式入口可在 GPU 前完成 CPU 机械验收，新版本 bundle 与活动文档一致。
- 完成 Phase 14 计划恢复与远端命令证据检索；确认须以“可重放命令”修补旧 smoke provenance，不能补造原始 argv。
- stage bundle schema 升至 v2：validator 现在强制可信 protocol hash、仓库外部证据重哈希、哈希格式、状态一致性与 remote evidence snapshot；新增 tamper/status 反例测试。
- 两处 access-ledger 更新改为保留既有 confirmatory count，并新增 count=3/4 不回滚的单测；baseline smoke 补齐显式 input assumptions。
- P1.6 metadata 诚实补充 reproduction commands 与既有 wall times，明确原始 argv 未持久化，不冒充 executed command。
- 定向测试：stage bundle + ledger 共 10 passed。
## 2026-08-28 — Phase 14 continuation

- Re-inspected the evaluator, submission-builder, and strict-wrapper tests after tightening their production interfaces.
- Confirmed the remaining counterexample-test gaps before touching the A3 training/launcher path.
- Added and passed 18 targeted tests covering evaluator document-set equality, duplicate documents, submission skip policy, and strict official-schema counterexamples.
- Added and passed official-scorer provenance tests for a matching gold-self population and tampered evaluator rejection.
- Hardened the local supervised trainer with a pre-torch v6 binding check and immutable run metadata; 13 targeted CPU tests pass, including final-valid substitution and label-population drift rejection.
- Added the first complete A3 preflight/materializer and one-job launcher skeleton with isolated official workspaces, transparent model-path adaptation, official README recipes, exact argv/cwd/expected outputs, and explicit no-execute default.
- Full unit suite passed before regeneration: 391 passed, 12 torch-dependent skips; full ruff passed.
- Revalidated external source/evaluator, re-froze all six manifests and candidate protocol, replayed gold-self/adversarial scorer fixtures, and rebuilt three baseline schema smokes. Registry is intentionally conditional pending the new local gate/bundle.
- Superseded r1 after its A3 path precheck exposed mixed local/remote paths; rebuilt all local gates and selected immutable P1 r2. r2 validates independently and its A3 preflight/three launcher checks pass without starting a GPU process.
- Added an external trust root for the A3 execution plan and exact source/data file-set validation; superseded r2, reran the full gate (392 passed, 12 skips), and selected final P1 r3. Generated r3 plan and verified three no-execute paths plus wrong-plan-hash rejection.
- Closed Phase 14 planning state after a final authority-document read: P1 r3 and the A3 contract agree on both external hashes, remote rematerialization, and the no-GPU-yet boundary. Final executable gates are being replayed once more before handoff.
- Final replay passed: 392 tests + 12 expected no-torch skips, ruff clean, CPU smoke OK, P1 `--validate-only` PASS, 20 targeted trust tests PASS, root instructions synchronized, and active docs free of r2/old-hash drift. Registry selection was rechecked under its actual `p1_bundle_id` field and points to r3.

## 2026-08-28 · Phase 15 A3.0 remote handoff

- 作者明确授权上一条所请求的提交与推送。执行边界解释为：提交/推送本轮修复并完成 4090 远端 CPU 物化和 no-execute 预检；不自动启动长时间 GPU 训练。
- 开始前本地权威门禁保持 392 passed / 12 expected skips、ruff/smoke/P1 validate 全绿；下一步先隔离进入本轮前的无关 dirty changes，避免一并提交。
- 已确认不能 `git add -A`：工作树混有旧 Ch1/v5 改动。Git 提交将只包含 P1/A3 代码、测试、协议 patch/fixture 与必要活动文档；忽略的 20 MB P1 evidence+r3 bundle 另做校验传输，100 MB 本地 A3 preflight 不复制、在远端重建。
- 首次选择性暂存把若干原始 Deep Research Markdown 导出带入，cached whitespace gate 正确报其原有 hard-break 尾空格。不会改写这些原始档来凑门禁；改为从提交中排除 raw reports，只保留审计/决策与执行文档。首次记录该错误的补丁因锚点大小写不匹配原子失败，已按实际行补记。
- 最终暂存边界为 55 个 P1/A3/v6 文件；70 个 staged Markdown 本地链接全可在 index 中解析，cached whitespace clean，且明确排除了 planning scratch、旧 Ch1 `PHASE_C`、coreference metric/profile 代码与 raw Deep Research 导出。
- 已创建并推送提交 `53ce6f1 feat(protocol): harden P1 and prepare A3 baseline gate`；fetch 后确认只领先 origin 一提交，非强推成功把远端 main 从 `c642bb8` 推进到 `53ce6f1`。
- 4090 端只读核验为 clean `c642bb8`、无项目训练、4 卡空闲；按 runbook fetch/reset 后 clean HEAD=`53ce6f1`。
- 已把 `data/protocols/v6` + P1 r3 打成 1.9 MiB evidence archive，明确排除本地 A3 preflight；`scp` 后双端 SHA-256 同为 `65cc5854…932a1a`。
- 首次解包+P1 validate SSH 在 banner exchange 超时，远端命令没有执行；保持基础设施失败状态，转用显式 ControlMaster 有界建连，不原样重试。
- ControlMaster 的 5 次有界握手也全部在 banner 前超时；停止同路径重试。当前安全断点：远端代码已是 `53ce6f1`，evidence archive 已上传并核 hash，但尚未解包或运行远端 validate。
- 只读诊断确认没有可复用用户 SSH 进程/socket；alias 未变化，TCP connect 成功，但 15 秒原始读取收不到任何 SSH banner。阻塞点在 cpolar→sshd 转发阶段、早于认证与任何远端命令。
- 冷却 45 秒后的一次长窗口 ControlMaster 仍在 kex 前被 peer reset；不改变科研状态，进入低频监测重连，避免突发握手加剧 tunnel 故障。
- 低频第 2 轮成功建立 ControlMaster；解包后的 r3 protocol hash 正确，但远端 `--validate-only` 真实失败为 `local tested file count drift`。根因是 r3 local gate 绑定本地 dirty 树的全部 Python 文件数，而 clean Git 提交刻意不含旧 Ch1 改动；开始修复该错误耦合并重建可移植 trust root，不用复制旧代码绕过。
- 复读 validator/local-gate 后确认不应放宽生产规则：三件套确实覆盖全部 src/tests/scripts，必须绑定精确测试树。修复改为在 detached clean `53ce6f1` worktree 重跑 gate 并生成 r4；只复制必要 ignored evidence，不复制 4.8 GB 整个 data tree。
- 数据盘点把 clean-worktree 初始复制范围压到 fixtures + MAVEN-ERE processed + P1 protocol + 4.6 MB ESC 测试文件。一次进一步 `rg` 因嵌套引号被 zsh 执行前拒绝，未产生文件变化，改用简单多模式检索。
- 测试路径确认直接依赖范围；一次 protocol 只读诊断误猜顶层 `artifacts` 键而 `KeyError`，无改动，改为先枚举正式 schema 后确定是否需要 FACT。
- 实际 `hashes` 枚举确认需要 ERE/FACT train+valid 与历史 checkpoint 三件套。临时 clean worktree 将物理复制 20 MB v6 protocol，受控 symlink 大型只读 source/checkpoint，保持相同仓库相对身份并由 validator 重哈希。
- 修正：本地不存在远端 checkpoint 属于预期行为；checkpoint category 不在 local hashes，由回传 remote snapshot 约束。本轮不跨机搬权重，clean worktree 只接入 ERE/FACT processed、v6 protocol 与测试数据。
- detached clean `53ce6f1` 三件套通过（380 passed/12 expected skips、ruff/smoke PASS），据此构建并独立验证 P1 r4；protocol SHA-256=`09e7e392…5fc46`。
- clean r4 CPU materializer 通过：2,622 train + 291 internal-dev、final-valid 未访问，plan SHA-256=`4935bd2f…f8f3444`。
- 三个 r4 seed-13 no-execute launcher 全部通过；clean 生成的 local gate/registry、r4 bundle 和 r4 preflight 已复制回本地 ignored 权威区，registry 选中 r4 且 global/A3 PASS。
- 活动文档仍有 7 个文件引用 r3 和旧 392 计数；将只改 Markdown/root instructions，并在命令中显式指定 r4 `--output`/`--preflight`，不改 Python 树从而保持 r4 gate 有效。
- 7 个权威文件已同步 r4/clean 380+12/new plan hash，P1 结果保留 r3 portability failure；A3 命令显式传入 r4 output/preflight，AGENTS/CLAUDE 同步且 whitespace clean。
- 补齐 phases/results 两处索引后，9 文件纯文档提交 `1d38dce docs(protocol): promote clean P1 r4 trust root` 已非强推到 origin；Python tree 未变化，r4 clean gate 仍有效。
- 远端同步到 `1d38dce`，r4 evidence archive 路径安全且双端 hash 一致；P1 r4 在 clean 远端 `--validate-only` PASS。
- 远端 CPU materializer PASS：2,622 train + 291 internal-dev、final-valid 未访问，plan SHA-256 与本地 clean 产物逐字一致为 `4935bd2f...f8f3444`。
- 首次三路 no-execute 因本地 JS 错拆 `bash -lc` 参数，远端 `cd` 未生效并立即报 `.venv/bin/python` 不存在；无进程启动、无产物变化。改为 SSH 直接执行完整 `cd && command`。
- 修正 wrapper 后三路 seed-13 no-execute 全部 PASS，打印的 argv/cwd/产物均为 r4 路径且明确 no process started。
- 收尾 Git/hash/P1 validate/GPU 审计通过；宽泛 `pgrep` 仅自匹配当前审计 shell，改用锚定项目 Python argv 做最终零进程确认。
- 锚定检查确认 A3 project Python processes=none，随后关闭 ControlMaster。将远端物化/no-execute 实测写入 TODO/P1 结果并提交推送 `132d69f`；因 socket 关闭早于该纯文档提交，需再同步一次远端 HEAD，不重跑实验。
- 最终 docs-only 同步的首次新 ControlMaster 在 kex 前被 cpolar reset，无远端命令执行；转最多两轮低频重连。
- 低频第 2 轮建立 socket，远端最终同步到 clean `132d69f` 后关闭。Phase 15 完成：P1 r4、远端 plan、三路 seed-13 no-execute 全部 PASS，无 A3 project Python 进程、未启动 GPU baseline。
- 已移除生成 r4 用的 detached `/tmp` worktree；最终 HEAD=origin=`132d69f`、index empty、whitespace/instruction sync/r4 registry+hash assertions 全部 PASS。旧 Ch1 与研究/planning 未跟踪文件原样保留、未提交。

## 2026-08-28 · Phase 16 A3.0 GPU baseline readiness review

- 作者询问下一个任务并允许多 GPU；本轮先独立复核可执行性，不启动训练。重点区分“多个独立单卡 run 并发”与会改变公开 recipe/优化轨迹的 DDP。
- A3 契约与 launcher 审计确认：下一任务先完成三 baseline×matched seeds 的 train/internal-dev 表并冻结主锚，不是直接做新方法；九个 run-dir 可并行。
- 作者澄清多卡是加速同一任务，不是并发不同实验。修正策略：official single/joint 使用其原生 `nn.DataParallel` 的同一 run 多卡；local pair 因单文档 batch=1 保持单卡，不做会改变协议的临时 DDP 改造，也不跨 seed 并发。
- 代码复核确认 official DataLoader 的 batch 4/8 是全局 batch；原生 DataParallel 仅接收并切分 token tensor，事件 spans/splits 在 backbone 输出按原序 gather 后才处理，因此不会发生元数据错配，也不需改 LR/accum。local pair encoder 输入 batch=1，多卡不会实质提速。
- 首个远端复合 readiness 检查在 HEAD/clean 后 exit 1，因成功项没有标签无法区分 run-dir/model 前置；命令只读且未启动进程，改成逐项可观测检查。
- 逐项远端检查：9 个 run-dir 全 absent，/data 可用 32T，torch/CUDA/transformers 正常识别 4×4090，四卡空闲；唯一硬失败是计划模型路径 `/data/MODELS/roberta-base` 不存在。当前不得 `--execute`，先定位同一模型 cache 并透明重物化 plan。
- 首次模型 cache 搜索在 SSH kex 前被 cpolar reset，远端命令未执行；不据空输出判断无模型，转低频 ControlMaster 后继续。
- 两轮低频 ControlMaster 也在 kex 前 reset，停止本轮同 endpoint 重试。先查本地 WSL cache，若完整则可在 tunnel 恢复后用双端 hash 传输；当前仍未启动训练。
- 为直接观察 PyTorch scatter 行为而做的本地最小探针因项目环境未安装 `torch` 报 `ModuleNotFoundError`；未安装依赖、未改代码。随后回到实际调用边界逐行复核，确认 DataParallel 只包住 backbone，非张量元数据根本不会进入 scatter，故该探针不是多卡正确性的必要前置。
- 新一轮只读 cache 搜索仍在 SSH banner exchange 超时，远端 `find` 未执行；SSH 配置仍解析为 `TJK@18.tcp.vip.cpolar.cn:14147`，当前 DNS 为 `49.233.190.64`。不把连接失败伪装成无 cache。
- 发现 P1 预注册的 subevent 非劣参照有歧义：causal-only official single 可能成为 causal primary anchor，却没有可用 subevent 分数。正式分数出现前须把 subevent guardrail anchor 固定为 official joint，causal anchor 选择规则保持不变。
- 多卡最终口径：official single/joint 只在同一 workload 的 1 卡 vs 4 卡短时吞吐 smoke 确认加速后用 4 卡；global batch/LR/accum 不变。local pair 保持 1 卡，不并发其他 run。
- Phase 16 启动复核完成，当前裁决为局部 NO-GO：模型路径缺失 + subevent guardrail 参照需修订；A3 方向与 P1 数据/evaluator 准入不降级，未启动任何完整 GPU baseline。

## 2026-08-28 · Phase 17 路径/backbone/放行术语纠偏

- 作者指出 RoBERTa-base 年代、`/data/TJK/` 根目录和反复 NO-GO 三个问题；本轮重新打开结论，不为旧判断辩护。
- 本地活动配置核对确认项目 root 从未漂移：4090 一直是 `/data/TJK/ekg`。错误的是 A3 materializer 把上游 joint 代码的机器私有 `/data/MODELS/roberta-base` 继承成统一默认；这不是项目根路径，也不应继续使用。
- pinned MAVEN-ERE official source 明确使用 RoBERTa tokenizer/768-d encoder，因此 official single/joint 保留 RoBERTa-base 是忠实复现要求；是否给主方法增加现代 backbone transfer 仍待一手文献与资源复核。
- 重新分类状态：模型路径和 subevent 护栏参照属于 `EXECUTION HOLD / REQUIRED PRE-FLIGHT FIX`，不构成 A3 或全篇 NO-GO。P1 global/A3 entry 的 PASS 不撤销。
- 按作者终端口径用 `ssh -tt gpu-4090`、30 秒握手和 `/data/TJK` 只读命令重试，仍在 kex 前被 `49.233.190.64:14147` reset；远端命令未运行，不能更新服务器目录事实。
- 本地进程、TCP 连接和 socket 核对未发现作者当前终端的可复用 SSH master/session；`ssh -G` 仍解析为 `TJK@18.tcp.vip.cpolar.cn:14147`、同一 ed25519 key、无 ProxyJump/ProxyCommand/ControlMaster。差异发生在 cpolar 对新连接的处理，不是项目工作目录。
- 一手来源核验完成：MAVEN-ERE 是 EMNLP 2022 官方任务，论文/官方代码的 baseline 确实使用 RoBERTa_BASE；因此它只应保留为忠实复现轴。
- ModernBERT-base 官方模型卡确认 149M 参数、8,192 原生上下文、Apache-2.0、Transformers>=4.48；与远端已核实的 4.53.3 纸面兼容。初步建议把它作为 A3 的对称 backbone transfer，而非替换官方 baseline 或冒充方法增益；远端模型加载/显存/吞吐仍未核实。
- 已从两个官方 Hugging Face Git 端点解析当前精确 revision：RoBERTa-base `e2da8e2...ac7b`、ModernBERT-base `8949b909...0c8`。建议统一放 `/data/TJK/models/<name>/<revision>/` 并按 revision+文件 hash 固化。
- 定位到必须修改的生成源：subevent 规则来自 `scripts/freeze_v6_protocol.py`，模型默认来自 `scripts/prepare_a3_baselines.py`。不能只手改 JSON/执行计划；需生成器、测试、协议产物和新 trust root 同步。
- 本地 relation trainer 已使用 AutoTokenizer/AutoModel/动态 hidden size，ModernBERT transfer 可走同一实现；首个 transfer 必须把 reproduction/proposed 两边都固定 max_length=512，避免把长上下文变化混入 backbone 效应。8k 上下文另作二级长度消融。
- 已修改 prereg 生成器/产物、A3 materializer/launcher、定向测试和五份活动契约：模型默认改为 `/data/TJK/models/FacebookAI/roberta-base/<revision>`；causal/subevent 两个锚分离；ModernBERT 仅作对称迁移。定向 20 tests 与 ruff 全部通过。
- 当前主工作树有进入本轮前的 Ch1/coreference 改动，不能直接据此构建可移植 trust root。已从 clean HEAD `132d69f` 建立 detached worktree `/tmp/ekg-r5-clean.h5vJgx`，下一步只应用本轮受控 patch、复制最小 ignored evidence并重跑三件套。
- clean worktree 首次 `uv run pytest` 创建了仅 16 包的最小环境，因缺 networkx 在 collection 阶段失败（46 个导入错误、没有测试执行）。这不是代码失败；后续按 pyproject 现有依赖组补齐该 worktree 环境后重跑，不引入新包定义。
- 核对 pyproject 后用既有 `dev` optional extra 执行 `uv sync --extra dev --locked`；clean r5 三件套现已通过：382 passed/12 expected no-torch skips、ruff PASS、ekg-smoke OK。比 r4 多 2 个测试，正是本轮新增的路径/guardrail 回归锁。
- `scripts/run_p1_local_gate.py` 在同一 clean tree 再次完整通过并写出新 local gate SHA `563558e6...b89f`，tested tree 不含主工作树的 Ch1 改动。
- clean tree 已构建并独立 validate P1 r5：`global_protocol_status=pass, a3_entry_status=pass`，protocol SHA `03df9c16...a71c`。r4 不被覆盖；r5 只重绑本轮 prereg/code/local gate，复用且重哈希不变的 data/evaluator/remote smoke。
- A3 r5 CPU materializer PASS：2,622 train + 291 internal-dev、final-valid untouched，plan SHA `f7010432...b681b`；三路 seed-13 no-execute 均打印 `/data/TJK/ekg` repo/run 与 pinned `/data/TJK/models/.../e2da8e2...` model path 并 PASS。生成的 r5 protocol/bundle/preflight 已按 hash 复制回主工作区。

## 2026-08-31 · Phase 18 周四汇报与三日执行编排

- **Status:** in_progress
- 读取并遵循 `planning-with-files`；恢复既有三份 planning 文件，未覆盖历史工作记忆。
- 阅读 `docs/HANDOFF.md` 与 `docs/reports/2026-09-03_阶段性报告.md`；确认报告存在早期叙述与 08-30 最新实证并存的内部漂移。
- 将 Phase 17 按后续事实关闭，新增 Phase 18；后续以 `docs/results/`、`docs/SPEC.md`、active phase、`docs/TODO.md` 的优先级继续核验。
- 当前交付目标：周四总体计划/逐章进展/三日任务表、文档分类规则与最小目录整理、4090 A3.2 安排及完整验证记录。
- 已读 `SPEC`、`TODO` 与 A3/D3/C4/E3 契约；识别到 A3 契约的 r9 身份和 TODO 前半状态均落后于 08-30 handoff，需要在实验前修正活动文档，而不能靠读者自行选择后半段。
- 已回查四份结果权威档和 Ch2 控制器/训练数据流；确认第二周期可用 3×2 位置化 offset 做单变量实现，且不改变推理规则、候选全集或评分器。
- 已展示并尝试 4090 只读审计命令；ControlMaster 尚未建立，远端审计尚未执行。本地连接脚本仍在有界重试，TCP 端口可达。
- ControlMaster 后续成功，4090 只读审计确认 r11/r12 身份、无项目任务且四卡空闲。
- 完成 Ch2 第二周期实现：pair row 显式同/跨句位置，controller 维护 family×position 六个独立 offset，训练按 row 移动 NONE logit，推理仍为朴素 argmax；定向 34 tests 与关系域测试通过。
- 完整本地门与 `run_p1_local_gate.py` 通过：447 passed / 16 expected skips、ruff 0、CPU smoke OK；代码/测试提交 `91d32d8` 已推送，planning 与报告未混入该提交。
- 远端 clean `91d32d8` 上完成新信任根和执行计划：P1 r12 PASS（protocol `0bd33e87…58497`），A3 r13 preflight PASS（plan `b587b21d…1eda`）；未启动 GPU 训练。
- 按用户最新优先级完成第一轮论文主表核验：MAVEN-ERE 原论文、TacoERE、LLMERE、Efficient DERE、MAVEN-FACT 与 event-aware coreference 的 ACL 官方页面/PDF已核；已形成 Ch1 关系感知度量、Ch2 检索器+精判别器、Ch3 证据条件化+稀有类目标三条方法映射。
- 重写周四汇报为 248 行的答案优先版本：公开背景表与本地同协议表分开，每章包含当前指标、低分原因、文献方法和止损条件；旧的“训练中”与已被推翻的结论已移除。
- 新增 `docs/README.md` 项目结构/文档分类规则和 `docs/reports/README.md`；不移动历史文件。同步精简 `TODO`、更新 HANDOFF、active A3 契约、P1/results 索引和 AGENTS/CLAUDE 到 r12/r13 身份。
- 按远端规则展示完整命令后，在 4090 GPU0 启动 r13 seed-13 两 epoch 行为 smoke；启动时 commit/registry/output absence/GPU 空闲检查均通过，PID 3893093，未升级长训练。
- r13 两 epoch 行为 smoke 已正常结束：trainer macro .3178→.3328，六桶最终 offset 位于
  [−.536,+.328]，12 条 trajectory 完整，run status complete、final-valid 未访问。causal 跨句桶的
  最优 shift 连续为正，符合跨句过发诊断。该入口未运行 official evaluator，因此仅判行为 PASS，
  未启动 50 epoch 长训练。
- 完成交付前校验：所有改动 Markdown 相对链接有效，`git diff --check` 通过，
  `AGENTS.md`/`CLAUDE.md` 仍逐字节一致。Phase 18 收口，下一科研执行点是 A3 完整 seed-13。

## 2026-08-31 · Phase 19 单种子优先的 GPU 并行推进

- **Status:** in_progress
- 用户明确改规则：探索阶段不需多种子；所有待比方案的单种子都超过各自 baseline/护栏之后，仍必须再获得用户明确允许才能跑多种子。
- 用户已授权继续 GPU 执行和并行任务；并行只用于不同方案/任务，不得用 seeds 17/42 占用其他卡。
- 重读 `planning-with-files` 并执行 session catch-up；工作树从上一提交干净继续。
- 已起草同步根指令、HANDOFF、TODO、A3 契约和周四报告的新多种子授权门；历史三种子数字保留为已发生事实。
- 核对 r13 plan 与正式 scorer：本轮不使用 preflight 中的 3-epoch baseline launcher；将按已过 smoke 的
  50-epoch trainer 参数运行 seed-13，随后用 `score_a3_arm.py` 生成 official 三族指标。
- 新多种子规则已以提交 `84ffac0` 推送，远端同步到该 HEAD。准入核对确认 plan SHA
  `b587b21d…1eda`、目标 run-dir 不存在、4 卡空闲、无项目 Python 训练进程。
- 已在 GPU0 启动 r13 `adaptive_workpoint` 完整 seed-13：50 epoch trainer 成功后将自动串行
  `score_a3_arm.py` official 评分。外层 PID 3907809，trainer PID 3907812；日志
  `logs/a3_position_workpoint_r13_full_s13.log`。未启动任何其他 seed。
- 首次运行监测正常：GPU0 约 3.9GB/24%，trainer 存活且已完成 2,913 文档/3,315,358 rows 数据物化；GPU1–3 继续空闲。
- 开始为不同方案的 GPU1 并行任务做可运行性门：ACL 官方页面已确认两阶段 retriever→cross-encoder
  的直接适配性，但搜索尚未发现 Efficient DERE/TacoERE 官方代码；先查 PDF 中的 code URL，不盲目占卡。
- `pdf` skill 指导的 ACL PDF 抽取正在进行；首次批处理超过工具 30 秒返回窗口，但原下载进程仍活着，故不重复启动。
- GPU0 训练第二次监测正常：epoch 0 已到 2,000/2,622 docs，约 6.3GB，无 NaN/异常退出；GPU1–3 仍空闲。
- 两篇 PDF 与文本抽取现已完整落到 `/tmp/ekg-retriever-papers.iPhGNJ/`，下一步直接检索代码声明和方法参数，不重复下载。
- PDF 核验完成：两篇均无官方实现链接。并行路线不重写 TacoERE 的摘要+RL 全栈，改为
  Efficient DERE 文献启发的最小 Stage-1 门：bi-encoder、top-k/事件、评估 positive-pair
  recall@5 和 candidate compression；通过才启动 GPU1 的 cross-encoder 方案。
- 完成 retriever 接入面定位：仅过滤 causal 候选，subevent/temporal 不动；先做 gold oracle@5
  结构上限，通过后再新增 bi-encoder 训练/评测竖片。这保持与当前三族护栏的单变量边界。
- oracle@5 实测不足：mention-level dev recall .7832/压缩 84.7%；cluster-first 展开后 recall .8032/压缩约 83.4%。不启动 GPU1 top-5 训练；先找到在冻结候选口径下能达 oracle recall .95 的最小 k。
- oracle grid 确定 mention-level k=15：dev 上限 recall .9810，candidate compression 55.8%。选它而不是 cluster k=10，避免把 gold/predicted coreference 质量混入 Ch2 Stage-1 诊断。
- 已新增纯 CPU retrieval 工具与 4 个单测，以及协议绑定的 Stage-1 训练/评测 CLI；定向测试和 ruff 通过。
  首次 CLI help 暴露 CPU 顶层 torch-only 符号导入，已改为与现有 trainer 一致的 lazy import，未污染本地依赖。
- lazy-import 修正后 CLI `--help`、4 个定向测试、新文件 ruff 和 whitespace gate 全部通过。
- GPU0 r13 训练已到 epoch 3 中段；trainer macro 依次 .3170→.3495→.3773，epoch 2 三族为
  causal .328 / subevent .293 / temporal .510。这仍是 trainer 分不是 official 分；offset 有限，GPU0 约 6.7GB，无异常。
- retriever 竖片完整本地门通过：451 passed / 16 expected torch skips，ruff 0，`ekg-smoke` OK。
  新文件仅是 exploratory Stage-1 诊断，不在 P1 `CODE_PATHS`，不改变正在运行的 r13 信任根或模型结论。
- retriever 提交 `c7c8e9f` 已推送并安全同步到远端；同步前已确认 GPU0 所用 trainer/scorer/
  config 在两提交间零差异。远端 4 tests 和 CLI help 通过，GPU0 进程未中断。
- 已在 GPU1 启动不同方案的 Stage-1 top-15 retriever，冻结 seed 13，trainer PID 3920963，
  日志 `logs/a3_retriever_r1_stage1_s13.log`。启动前 GPU1 18MiB/0%，未创建任何额外 seed run-dir。
- 核对 D3 契约后决定不启动第三个正式 GPU 任务：D3 仍以 A3 immutable handoff 为有效性输入，当前并行
  授权只用于彼此独立的方案，不足以让未绑定 A3 输出的 Ch3 数字进入结论。GPU2/3 保留空闲。
- 最新健康检查：GPU0 workpoint 已完成 epoch 4、最佳 trainer macro=.3823；GPU1 retriever epoch 0
  已过 2,000/2,622 文档。两边存活且无 NaN；未启动 seeds 17/42。
- 完成 Stage-2 CPU 接线审计：候选全集和 scorer 可保持不变，潜在改动仅限 causal family 的训练 ignore
  与推理 NONE gate；在 Stage-1 门未通过前不实现、不启动。
- Retriever epoch 0 完整指标为 recall@15=.8455、跨句=.7947、压缩=.5580，暂未过 .90/.85 门；
  冻结 3-epoch 任务继续到终点，不做运行中调参。GPU0 同时已进入 epoch 5。
- epoch 0 明细已核：同句 1,350/1,392=.9698，跨句 2,705/3,404=.7947，确认短板是跨句排序；
  epoch 1 已完成 2,500/2,622 文档，等待同一门槛复核。
- epoch 1 完整指标为 recall@15=.8638、跨句=.8231，仍未过门。复核实现与论文后明确：r1 复用
  窗口 trigger mean pooling，是论文启发的竖片而非 `<m>` marker-sentence 忠实表示；若最终失败，
  下一机制优先修正表示层，不做 k/seed 追分。
- 已从 PDF 方法段核实 Stage 2：全正例 + 检索 hard negatives，推理只分类检索 pair。项目适配时仍需
  向原 official scorer 提交完整候选结构，未检出的 causal pair 只能显式 NONE，不能删分母。
- GPU1 r1 已自然结束并完成三态/产物核验：best epoch 2 overall=.8691、cross=.8273、same=.9713、
  compression=.5580，未过 .90/.85 门；metadata complete、final-valid=false、hashes match。
  已将负结果写入 `docs/results/PHASE_A.md`，r1 不接 Stage 2、不追加 seed。
- GPU0 workpoint 仍存活，epoch 5 trainer macro=.3825 创新高，epoch 6 已完成训练文档循环；仍等
  50 epochs 后的 official evaluator，当前 trainer 数字不进入主表。
- 开始 r2 的 CPU 实现审计：确认冻结 JSONL 提供 mention token offset；4,080/73,939 mentions 的句子
  存在同形 trigger，多数不能靠当前 first-match span 区分。r2 将用 token offset 原位插 marker，
  不触碰 `EventNode` schema/P1 loader；每篇最多 110 mentions，编码采用有界小批量。
- r2 marker-sentence 竖片已实现：原 r1 表示仍为默认；新模式注册 marker special tokens、按原始 token
  offset 构造句子、batch-size 16 编码并复用既有 top-15 loss/evaluator。新增 6 个 marker 回归用例。
- r2 本地全门通过：457 passed / 16 expected torch skips、ruff 0、CPU smoke OK；73,939 个上下文
  与 loader mention ID 集完全一致，每条恰有一对 marker。diff/AGENTS-CLAUDE 一致性检查通过。
- r1 负结果+r2 实现已提交并推送为 `0842304`；远端 fetch 前无法解析新 revision 的只读 diff
  返回 128，fetch 后核实正式 workpoint 的 trainer/scorer/config 四路径零差异，再安全 reset 到新 HEAD；
  远端 10 个 retriever tests 通过，GPU0 trainer 全程存活。
- GPU1 r2 marker-sentence seed-13 已启动：wrapper PID 3927850、trainer PID 3927858，输出
  `runs/stages/A3/a3-v6-retriever-r2/stage1/seed-13/`，日志
  `logs/a3_retriever_r2_stage1_s13.log`。启动前目标不存在、GPU1 18MiB/0%，未新增其他 seed。
- r2 首个 500-doc checkpoint loss=5.9421，GPU1 约 6.25GiB/23%，进程存活、尚无 NaN/OOM。
  周四报告中“50ep 尚未启动/四卡空闲”和“9/2 并行正式 Ch3”已按实际状态修正：D3 必须等待
  A3 immutable handoff，当前只准备输入清单。
- r2 epoch 0 已过 1,000/2,622 文档，running loss 降至 3.5997，GPU1 约 7.1GiB；GPU0/GPU1
  两进程均存活。报告更新通过 whitespace gate，当前 dirty 仅报告与 planning 文件。
- r2 epoch 0 已过 2,000/2,622，loss=2.3188，GPU1 约 8.1GiB；一次远端 50 秒 grep 等待在
  工具 30 秒窗口返回空输出，随后成功 SSH 明确读到 PID ALIVE 和新增日志，未误判完成/失败。
- GPU0 workpoint 当前 best trainer macro=.3876（epoch 7：causal .328 / subevent .310 /
  temporal .524），epoch 10 运行中。该值仍是 checkpoint selection signal，不是 official 主表分。
- r2 epoch 0 完整结果：overall=.8159、same=.9720、cross=.7521、compression=.5580，低于 r1 同轮，
  暂未过门。主要退化仍在跨句，证明 marker 单句表示未解决文档级语义；继续冻结后两轮，不中途改参。
- 在本地新增但未启动 `topk_pairwise` objective：全正例对抗每个 head 的 top-15 hardest negatives，
  保留 trigger-mean 表示和默认 sampled BCE 兼容路径。定向 10 tests、ruff、CLI help、whitespace PASS；
  仅当 r2 最终失败才考虑远端单种子 r3。
- r3 候选的完整本地门也通过：457 passed / 16 expected skips、ruff 0、CPU smoke OK；尚未提交/
  同步远端，所以正在运行的 r2 继续使用冻结 `0842304`。当前 dirty 仅报告、planning 与该候选脚本。
- r2 epoch 1 已过 2,000/2,622 文档，loss=.8667，进程存活；尚未产生第二个 recall 点。
- r3 ranking objective 的训练覆盖已核：2,546/2,622 个 train docs 有 causal signal，共 48,562 个
  mention-expanded positive pairs，最大单文档 250；只跳过 76 个无正例文档，不是小样本技巧。
- r2 epoch 1 训练循环已到 2,500/2,622，loss=.8572；等待评估。GPU0 epoch 11 同时运行中，
  当前 best checkpoint 仍为 epoch 7 trainer macro=.3876。
- r2 epoch 1 评估为 overall=.8451、cross=.7911，仍未过门且未追平 r1。r3 数据审计发现 9 个
  有正例但无可比负 tail 的文档，已把 ranking objective/scheduler 的有效训练集合改为 2,537 篇，
  避免远端运行中才 crash。
- r3 metadata 增加 train/dev/objective-doc/positive-pair 计数并在启动时打印 representation/objective，
  便于失败时也能追溯实际信号集合；定向 ruff/CLI/whitespace 通过。r2 epoch 2 已过 1,000 文档。
- 上述 r3 最终形态重新通过完整本地门：457 passed / 16 expected skips、ruff 0、CPU smoke OK。
  r2 epoch 2 已过 2,000/2,622 文档，loss=.7651，仍存活。
- r2 已自然结束并封存：best epoch 2 overall=.8543、same=.9784、cross=.8035、compression=.5580，
  未过门且低于 r1；metadata complete/final-valid=false、hashes match，成功 SSH 确认进程 GONE、
  GPU1 18MiB。负结果已写入 `docs/results/PHASE_A.md`，周四报告同步为 r1/r2 均判负。
- r3 排序目标与 r2 结果提交 `e0ef69d` 已推送；远端 fetch 后核实正式 workpoint 四个活动路径零差异，
  安全同步并通过 10 retriever tests/CLI，GPU0 trainer 全程存活。
- GPU1 真实 CUDA smoke PASS：28 mentions/36 positives，loss=1.0007、finite=true、encoder grad
  norm=.4067；未写实验产物。随后启动 r3 `topk_pairwise` seed-13，wrapper PID 3936535、trainer
  PID 3936542，目标 `runs/stages/A3/a3-v6-retriever-r3/stage1/seed-13/`，没有其他 seed。
- r3 启动日志确认 trigger_mean/topk_pairwise、2,537 objective train docs + 291 dev；首个
  500-doc loss=.6660，GPU1 约 4.2GiB/34%，数值有限。GPU0 r13 同时存活。
- r3 epoch 0 已过 1,000/2,537，loss=.5757。GPU0 workpoint trainer best 更新为 epoch 12
  macro=.3891（causal .332 / subevent .327 / temporal .508），当前 epoch 14；仍非 official 分。
- r3 epoch 0 已过 2,000/2,537，ranking loss=.4718，进程存活、数值继续下降；等待首个 recall。
- r3 epoch 0 完整评估：overall=.8595、same=.9828、cross=.8090、compression=.5580；比 r1 同轮
  overall/cross 各高约 .014，但仍未过门。后两轮按冻结配置继续，不改 k/损失/seed。
- r3 epoch 1 首个 500-doc loss=.2505。GPU0 workpoint 当前 epoch 15，best 仍为 epoch 12
  trainer macro=.3891；两进程均存活。
- r3 epoch 1 已过 1,500/2,537，running ranking loss=.2580；无发散或异常退出。
- r3 epoch 1 完整评估：overall=.8703、cross=.8237、compression=.5580，仍未过门；overall 仅略高于
  r1 final，cross 反而略低。冻结 epoch 2 继续；若仍失败，停止 retriever 近似变体而非继续占卡。
- r3 最终日志：overall=.8749、cross=.8299、compression=.5580，未过门；成功 SSH 已读到 final log
  且 PID 3936542 GONE，因此停止检索线、不跑 r4。随后的 metadata/hash 复核因旧 control socket reset、
  新连接 banner timeout 未执行；不据 SSH 失败推断 GPU0 状态，待低频重连后补齐权威结果档。
- 后续两个不同 ControlPath 的低频新连接仍在 banner exchange 超时，远端命令均未执行；停止继续
  轰击入口。HANDOFF/TODO/A3 契约已把过时的“四卡空闲/50ep 未启动”改为实际状态，并明确 GPU0
  最后成功确认到 epoch 15、之后状态未知，r1–r3 检索线止损。

## 2026-09-01 · Phase 20：5090 临时单种子探索

- 用户明确授权使用 `gpu-5090`，用于 4090 不可达期间探索提高最终指标的方法。
- 冻结边界：优先 Ch2；不同方案可并行；只跑 seed 13；不启动任何额外 seeds；不访问 final-valid。
- 首步为只读核验远端代码、GPU、磁盘与资产，不在核验完成前启动训练。
- 首个只读 SSH 返回 `Connection refused`；远端零执行。已核实本机只有
  `29.tcp.cpolar.top:12337` 这一入口，无备用 alias/会话；不原样重试，转入本地方案筛选。
- 完成 Ch2 接入面复核：距离、文档窗口、全候选、位置工作点和三种 retriever 近似都已覆盖；下一方案
  必须针对表示判别力或结构约束，不再重复阈值/句距/检索近似。
- 完成首轮论文/官方仓库筛选：淘汰 MAVEN-ERE causal 明显偏低的 SPEECH 和代价过高的通用 ProtoRE；
  保留“最小原型对比”与“可微结构一致性”两类候选，继续核一手公式、代码与本任务适配面。
- 一手核验确定主候选为 ProtoEM-inspired：其论文 valid 三族 54.17/33.93/30.55，唯一同时越过当前
  三条线的方向；无官方代码，后续以透明最小适配实现，不冒充官方复现。结构约束降为第二优先级。
- 代码接入审计完成：当前三族头彼此独立，适合用“prototype distance head”作单变量替换；第二臂仅增加
  prototype dependency，保留同一 encoder、pair feature、训练预算、candidate 和 official scorer。
- 排除 SEAG（无向/合并 subtype）及当前不可闭环的多代理/LLM 方法；继续对 GraphERE 做一次官方代码门，
  无即用实现则停止扩散，进入 ProtoEM-inspired 竖片实现。
- GraphERE 官方代码门未过且依赖面过大，已停止扩散。进入 prototype head 的 registry/config 设计与
  已知答案测试；旧线性 head 和旧 checkpoint 必须逐位保持兼容。
- 已定位训练保存、推理加载、P1 hash 与现有测试接入点；准备先写纯 Python 的 config/依赖矩阵测试，
  再写 torch 形状/梯度/零漂移测试，最后改训练循环。
- 已新增 pair-head registry/config 与 prototype 模块骨架，并把两个新源文件纳入 P1 code hash；下一步接
  trainer 的 train-only support 初始化和 checkpoint 保存，再补测试。
- prototype trainer、train-only support 初始化和 checkpoint identity 已接通；定向测试与 ruff PASS。
  CLI help 因并行 uv cache lock 未运行，改用独立 `/tmp` cache 只重跑这一项。
- CLI help PASS；冻结 train 全量 support/adjacency 审计 PASS。发现 dependency 图的 NONE 共现可能淹没
  PRECONDITION 语义邻居，先量化 raw positive co-occurrence，再冻结图构造，不直接烧 GPU。
- raw 共现确认 causal 正类主要连 BEFORE/CONTAINS，已将 dependency 图收紧为正类共现；定向门复跑 PASS。
- 项目完整门 PASS：461 passed / 18 skips、ruff clean、CPU smoke OK。下一步重建 P1 local gate；远端
  仍必须先跑 torch 测试和 2 epoch CUDA smoke。
- P1 local gate PASS。检查确认无 5090 备用入口脚本；当前只缺远端入口恢复、CUDA gate 和新 P1/A3
  信任根。准备在 active A3 phase 中预注册 prototype 两臂与停止条件，再提交代码供远端同步。
- active A3 phase 已预注册两臂、单种子 promotion 与停止条件；实现提交为 `7128151`。
- 已按用户给定的 `cpolar-ssh-update` 恢复 5090 SSH 入口，端口为 10201；恢复后只读探测成功。
  远端尚未同步本地新提交，也尚未启动任何 GPU 任务；先核查 6.5 GiB 显存占用归属。
- 已确认 6.5 GiB 是长期运行的 Qwen embedding 服务，不做干预；5090 剩余显存足以进行单臂
  RoBERTa-base 训练，先同步代码并跑远端测试/CUDA smoke，再决定是否并行两个不同方案。
- 远端代码已同步至 `5fbf2d67`，prototype/supervised 定向测试全过；下一步做显式 CUDA forward /
  backward smoke 和反号负向控制，再重建 P1 远端证据。
- 显式 5090 CUDA forward/backward smoke 已通过；下一步只做一个错误距离符号的负向控制，随后
  进入 P1 remote smoke/信任根重建。
- 距离反号负向控制 PASS。P1 remote evidence 验证器发现硬编码 4090 身份，需先做小范围白名单改动并
  补测试，保持原 4090 规则兼容，再在 5090 生成真实 remote smoke。
- 复核后确认无需改 P1 验证器：复用原 4090 interface smoke，新 prototype 的实际执行资格由本轮 5090
  测试补足。准备按既有机械流程生成新的 P1 bundle 和 A3 plan。
- 新 P1 目标确认空闲；远端缺少 gitignored 的 remote-smoke evidence，当前构建尚未执行。下一步核清
  remote-smoke 引用的 fixture/prediction/log 缺件，按最小集合传输并校验哈希。
- 5090 的 protocol/P1 目录为空；本地 protocol 根仅 20 MiB。改为先本地构建 r13，再同步 protocol +
  r13 bundle 到 5090并做双端哈希，减少远端缺件导致的反复失败。
- 本地 P1 r13 构建及二次验证 PASS，新 trust-root hash 为 `00e0943d…b3447a`。下一步同步完整 protocol
  根和 r13 bundle 到 5090并核哈希，再物化 prototype 两臂 execution plan。
- P1 证据同步和双端哈希已完成。现有 baseline materializer 不适合 prototype 探索（固定三种 seeds /
  3 epochs），下一步从既有 A3 50ep 单种子计划提取准确超参，生成只含两个 prototype 臂的计划。
- 本地未持有 4090 上的位置工作点 r13 计划；active phase 已给出冻结预算与门。继续核对 PHASE_A 的
  50ep 配方、现存 run metadata 和 5090 的模型/数据资产，随后生成独立、只 seed13 的 prototype plan。
- 冻结配方和 5090 训练源均已确认；当前只缺定位内容寻址 RoBERTa-base 快照。找到并核哈希后即可
  生成/同步单种子 prototype plan，先每臂 2ep smoke。
- 已找到 5090 的 roberta-base HF cache；正在按 P1 的五文件 canonical-map 定义复算内容摘要，核准后
  将以实际 snapshot 路径写入新 plan。
- 唯一 snapshot 已定位，正在复算“排除 tokenizer.json 的五文件”与“全部六文件”两种 canonical digest；
  仅当其中之一精确等于冻结摘要才放行。
- 两种紧凑 JSON 摘要均不匹配；Git 历史未记录具体序列化命令。下一步枚举常见稳定编码并查是否存有
  原始五文件哈希表，避免因 canonical 编码差异误判模型内容。
- 常见编码枚举仍不匹配；当前不能证明 5090 cache 与正式内容 pin 逐字节相同。遵循用户“先探索再补
  严格可比”的优先级，可继续 exploratory smoke，但所有分数必须明确排除出正式主表，待 4090 恢复复跑。
- 首个 `prototype` 2ep smoke 已在 5090 启动（PID 962618）；先确认初始化、support、显存和早期 loss
  正常，再等待完成。dependency 臂严格等首臂 smoke 结束/释放显存后再启动。
- 首臂在 P1 预检时提前退出，GPU 训练零执行；缺件为 Maven-Fact train 源。下一步枚举 P1 data 清单，
  仅同步 5090 缺失且本地哈希匹配的文件，然后改用新的 retry-1 目录，保留这次失败证据。
- P1 源清单已缩小到四个 JSONL；准备远端逐项 SHA 检查并同步缺件，避免搬运无关数据。
- 远端仅缺 164 MiB 的 MAVEN-Fact 两文件；准备 rsync（无 `--delete`）并做双端哈希，之后以 retry-1
  新目录重启 prototype smoke。
- MAVEN-Fact 同步与双端哈希完成，5090 P1 validate-only PASS。现在可在 retry-1 新目录重启同一
  prototype seed13 smoke；上次失败目录和日志原样保留。
- retry-1 prototype smoke 已 ALIVE（Python PID 963306），support 覆盖和早期 loss 正常，GPU 增量显存
  约 4.3 GiB。继续监测至 epoch0/epoch1 dev 完成；dependency 臂尚未启动。
- prototype epoch0 数值稳定但三族 dev F1=0，早期效果异常低。继续等冻结的第 2 epoch，不中途改参数；
  若仍为零则不启动 prototype 50ep，转跑同预算 dependency smoke。
- 一手论文复核确认简化实现缺少 NONE 文本原型与 event-agnostic context connotation；若两臂 smoke 均
  全零，将按契约停止这版 prototype，后续方案必须按论文机制重设计，不能靠扫温度/support 数补洞。
- plain prototype smoke 已以 macro=.0242 失败止损，不投 50ep；dependency smoke 已启动（wrapper
  PID 963770），等待确认真实 Python PID和早期曲线。
- dependency 已 ALIVE（Python PID 963774）。同时准备在本机 3ep baseline predictions 上做 causal→
  temporal 一致性诊断；仅用于选择下一机制，不写入正式主表。
- 结构诊断因本机没有任何 Ch2 prediction artifact 而停止；未生成派生分数。优先等 dependency smoke，
  不重跑旧 baseline 占用 5090。
- dependency smoke 完成（macro=.1656，三族 .075/.167/.255），较 plain 显著恢复且仍上升。按资源优先级
  只晋级 dependency 到单 seed13 50ep；plain 不跑 full，额外 seeds 仍禁止。
- dependency 50ep 已 ALIVE（Python PID 964175）；下一步在训练期间回填 PHASE_A/HANDOFF/TODO，并
  定期记录 dev 曲线。训练结束后先做 official internal-dev scorer，再判断是否达到三条门。
- 文档已回填 P1 r13、smoke 与 50ep 运行态；50ep epoch1 macro 已到 .2469。已定位官方评分链和唯一
  需要补到 5090 的 9.8 MiB internal-dev valid 文件，准备按哈希同步。
- valid 文件同步及哈希完成，official postprocess 命令面已核清。下一步更新规划文件、验证文档 diff并
  提交；训练继续后台运行。
- 状态文档提交 `52c6721` 已推送。50ep epoch3 macro=.3198，Python PID 964175 继续 epoch4；等待更
  后段曲线并准备完成后立即跑三步 official 后处理。
- dependency 50ep 已完成 50/50 epoch，最佳 epoch30 trainer macro=.3812；run metadata 为
  `status=complete`、`device=cuda`、`final_valid_accessed=false`。
- internal-dev GPU inference、候选归一化和封存 official evaluator 均成功；official
  causal/subevent/temporal=29.80/32.64/51.81。因 causal <33.17，方案未过整体验收，停止本版本
  prototype，不追加 seed、不扫 support/temperature/dependency 权重。
- 权威结果档、A3 phase、HANDOFF、TODO 和周四汇报稿已同步为失败封存状态；checkpoint 留在 5090，
  产物路径与哈希已记录，未跨机搬运。
- 提交 `3070617` 已推送。开始 Phase 21：用新 official predictions 做 causal 误报结构诊断，再决定
  是否启动一个完全不同的单 seed13 方法；不延伸简化 prototype 超参。
- 5090 CPU error profile 已完成并通过官方分数自校验：causal FP 占错误 83.6%，其中 78.4% 为跨句；
  方向反转仅 29。下一步只筛能直接降低跨句高分负例的方法。
- 一手论文初筛把 ATLOP localized context + adaptive threshold 列为首选，ATGL loss 为可选增强；先核
  官方实现和本地 encoder 接线成本，不直接启动训练。
- 本地接线审计后，faithful localized context 被窗口边界阻断，短期不做伪适配；ATLOP ATLoss 能以
  NONE=index0 的单标签特例透明接入且不改推理。下一步核 ATGL 官方 loss 后二选一。
- ATGL 因论文明确警告会提高 FP 而淘汰。继续比较 ATLOP ATLoss 与本地可实现的跨句 online hard
  negative loss；选择标准是能否直接降低 causal FP 且保持同协议三族护栏。
- OHEM 因需要新增采样比例而暂缓；冻结 ATLOP ATLoss 单变量方案并开始本地实现。未经 smoke 不启动
  50ep，未经用户新授权不增加种子。
- 已定位 trainer 单一 loss 接线点和 P1 CODE_PATHS；开始实现 objective registry、ATLoss、CLI 身份和
  CPU/Torch 变异测试。
- ATLoss 实现与本地 gate 完成：461 passed / 22 skips、ruff 0、CPU smoke OK；P1 local gate PASS。
  准备新建 P1 bundle，再提交代码并同步 5090 跑 Torch/CUDA gate。
- P1 r14 已构建并 validate-only PASS，protocol SHA `a2b83f66…0a6974`。下一步审阅差异、提交推送，
  然后同步 5090 跑 4 项 Torch 公式测试与显式 CUDA backward。
- ATLoss 代码提交 `d4bee5c` 已推送；权威结果档与 A3 phase 已在看结果前冻结 objective、2ep 行为门、
  50ep official 门和 seed13-only 约束。
- 5090 同步与 gate 完成：4/4 Torch、P1 r14、CUDA backward 均 PASS。2ep smoke Python PID 967723
  ALIVE，epoch0 已到 500/2622；等待两轮 dev，不改配置。
- ATLoss 2ep 已 complete，但 causal/subevent 两轮均为 0，未过行为门；停止 full/official/额外 seed。
  远端日志、metadata、heads hash 已固定并写入 PHASE_A。
- AFL/ATGL/NCRL 一手机制复核后均与当前 FP 主因不匹配，不再开第三个 loss GPU 任务。Phase 21 转入
  结果封存与周四汇报；后续技术路线冻结为 pair-specific evidence/长文共同上下文重构。
