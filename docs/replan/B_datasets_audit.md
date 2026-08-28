# DR-B 本地交叉核验

> 核验日期：2026-08-25（Asia/Taipei）
>
> 原始报告：`docs/replan/B_datasets.md`
>
> 来源导出：`docs/replan/B_datasets.pdf`

## 结论

DR-B 可作为后续调研输入，但必须带着本文件的更正使用。它的主要方向性结论成立：公开事件资源很多，
同时满足公开数据、可核 test、多个近年对手和统一口径的成熟 benchmark 很少；MAVEN-ERE 仍有研究活动，
但近年评测设置已经分裂，不能把不同论文的 headline F1 排成 SOTA 时间线。

本轮给 DR-B 的验收状态是：**有条件通过**。不修改原始深度研究输出；下列“已确认”可以进入综合，
“更正/降级”必须覆盖原报告对应说法。

## PDF 来源恢复

- PDF 共 19 页，由 WeasyPrint 生成，有可搜索文本层，不是扫描件。
- 可见表格右侧有截断，因此表格正文仍以原 Markdown 为准。
- PDF 中有 237 个 URI 注释、43 个唯一 URI；剔除 ChatGPT 首页和失效的内部下载链接后，
  可恢复 41 个唯一真实 Web 来源。
- 组合审计方式为：**Markdown 取完整正文/表格，PDF 取引用编号与真实 URL**。不需要重跑 DR-B。

## 高影响结论核验表

| DR-B 结论 | 核验结果 | 本地更正或边界 |
|---|---|---|
| MAVEN-ERE CodaLab 页面和榜单可访问，但 submission/scorer 未验证 | **确认** | 页面当前返回完整竞赛 HTML，显示 `Competition Ends: Never`、参与需登录、Public Submissions 路由和历史 submission chart。未登录状态不能证明新上传和 scorer 仍实际运行。官方 README 称其为 permanent competition，也不能替代一次真实提交。 |
| Chen 2024 与 LLMERE 2025 均采用 original valid as new test | **确认** | Chen et al. Appendix E 明写 original train 按 8:2 重分；LLMERE Appendix C 明写 `Following Chen et al. (2024)` 采用同一设置。两篇均不能与官方 hidden test 分数直接比较。 |
| 近年 MAVEN-ERE 至少有三类 evaluation setting | **确认，但分类不完整** | 除 official hidden test、8:2 + original-valid-as-test、随机 sampled LLM setting 外，Xiang et al. 2025 的 causal-only setting 还以 original dev 作 test、从 train 抽 10% 作 dev。后续至少按四类记录。 |
| 2024–2025 至少有 6 篇正式论文使用 MAVEN-ERE/子任务 | **确认保守下界** | 已确认 TacoERE、Chen et al.、Wei et al.、KnowQA、LLMERE、MMD-ERE，以及 Xiang et al. 2025 directional ECI，共至少 7 篇；但任务、split 和 evaluator 不统一。 |
| 独立团队使用下界 ≥4 | **数字可保留，成员必须更正** | 原报告把 KnowQA 计为独立是错误的：KnowQA 作者 Zimu Wang 同时是 MAVEN-ERE 数据论文作者。可确认的四个独立团队应为 Chen et al. 2024、Wei et al. 2024、LLMERE 2025、Xiang et al. 2025；TacoERE、KnowQA、MMD-ERE 均有原团队作者重叠。 |
| ACE05 corpus 有英/中/阿，但 event task 仅英/中 | **确认** | LDC2006T06 官方 catalog 原文如此，且数据受 LDC User Agreement 约束，不是开放下载 benchmark。 |
| 2024+ 新事件资源中，本轮未找到已有 ≥2 个独立正式 follow-up 的数据集 | **仅接受为检索下界** | 可以写“本轮未找到”或 `0*`，不能写成对全部文献的存在性证明。它表示竞争成熟度不足，不表示问题价值低，也不表示没有可比较的旧 baseline。 |
| 不能判断 MAVEN-ERE 是否饱和 | **确认** | 原因是 evaluation setting 分裂，而不是“分数涨幅小”。没有同 split、同 evaluator、同指标定义的时间序列，不能合法判断饱和度。 |

## 必须覆盖原报告的更正

1. **KnowQA 不计独立团队。** MAVEN-ERE 原论文作者包括 Zimu Wang；KnowQA 也由 Zimu Wang 署名。
2. **独立下界仍为 ≥4，但第四组来自 Xiang et al. 2025。** 该论文为 Findings ACL 2025 正式论文，
   作者不与 MAVEN-ERE 数据论文重叠，实际在 MAVEN-ERE 的 causal 子任务上实验。
3. **评测设置至少四类。** Xiang et al. 的 `original dev → test; 10% original train → dev` 与 Chen/LLMERE
   的 `original train 8:2; original valid → test` 不同，不能合并。
4. **“2024+ 新数据集没有 ≥2 独立跟进”只是一轮严格检索的未发现。** 后续报告不得把 `0*` 简写为
   已证明的绝对零，也不得据此按“对手少”推荐或否定课题。

## 与 A_terrain 的交叉补全

DR-B 对下列事件图候选标成“未核/未重新核”，应以已经完成一手审计的 `A_terrain.md` 为准：

- **NYT-SEG / CALLMSAE：**人工 test graph 当前可下载，但许可说明与仓库 `document` 字段存在矛盾；
  完整 train 文本依赖 Annotated NYT，官方仓库缺 Hungarian Graph Similarity evaluator。原论文适配多个旧
  系统不等于已有多个独立 NYT-SEG follow-up。
- **CGEP / SeDGPL：**CGEP 是 graph-conditioned next-event ranking 任务，指标为 MRR/Hit@k；论文在同一
  设置适配多个对手，但独立 follow-up 未核实。仓库有 ESC 派生图和 scorer，缺 MAVEN 派生文件与数据构造
  入口，不能写成一键复现 benchmark。
- **TORQUESTRA / TAG-EQA：**TAG-EQA 是 *SEM 2025 正式方法，底层数据是 TORQUESTRA human-revised
  gold event graph；gold 只监督最终 yes/no，仓库又缺论文使用的派生数据和固定 Full/Small test。

这些候选证明事件图下游任务已经存在，但目前都不足以无保留满足“公开复现包完整 + 多个独立近年方法 +
统一 evaluator”的学位论文硬约束。

## 可交给 DR-C 的稳定输入

- MAVEN-ERE 仍值得纳入方法/代码审计，因为 2024–2025 正式使用论文不少、本地 relation/evaluator 资产
  残值高；但任何方法表必须逐行注明属于 hidden test、Chen/LLMERE valid-as-test、sampled setting，还是
  Xiang causal-only setting。
- 对 DR-C 最有价值的方法集合至少包括：Wei et al. 的 full-test direct LLM 对照、TacoERE 的压缩/混合
  流程、Chen et al. 的 logic injection、LLMERE 的 LoRA/rationale、KnowQA 的 causal sampled setting、
  MMD-ERE 的 multi-agent sampled setting、Xiang et al. 的 directional causal setting，以及 A 报告中的
  CGEP/SeDGPL、CALLMSAE、EventRAG、CGEL、TAG-EQA。
- 硬件与 GitHub 可复现性只在 B 中做了零散核查；应由 DR-C 统一复核，不能把“7B/8B”自动等同于
  27GB 单卡已验证。

## 一手来源入口

- [MAVEN-ERE 官方仓库](https://github.com/THU-KEG/MAVEN-ERE)
- [MAVEN-ERE 官方 CodaLab](https://codalab.lisn.upsaclay.fr/competitions/8691)
- [MAVEN-ERE 数据论文](https://aclanthology.org/2022.emnlp-main.60/)
- [Chen et al. 2024](https://aclanthology.org/2024.acl-long.512/)
- [Wei et al. 2024](https://aclanthology.org/2024.findings-emnlp.1/)
- [TacoERE](https://aclanthology.org/2024.lrec-main.1348/)
- [KnowQA](https://aclanthology.org/2024.findings-emnlp.986/)
- [LLMERE](https://aclanthology.org/2025.coling-main.500/)
- [MMD-ERE](https://aclanthology.org/2025.coling-main.460/)
- [Xiang et al. directional ECI](https://aclanthology.org/2025.findings-acl.43/)
- [ACE 2005 Multilingual Training Corpus](https://catalog.ldc.upenn.edu/LDC2006T06)
- [CGEP / SeDGPL](https://aclanthology.org/2024.findings-emnlp.45/)
- [CALLMSAE / NYT-SEG](https://aclanthology.org/2025.naacl-long.112/)
- [TAG-EQA](https://aclanthology.org/2025.starsem-1.24/)

## 验收边界

本轮没有登录 CodaLab 做真实提交，没有为 2024+ 每个新数据集进行穷尽式 citation graph 审计，也没有
重复 DR-C 应负责的全部仓库/显存核查。这些缺口不妨碍把 B 作为“数据与竞争地形”的有条件合格输入，
但会阻止任何“通道确定可提交”“新数据集绝对没有跟进”或“某 7B 方法确定可在 27GB 原样训练”的强结论。
