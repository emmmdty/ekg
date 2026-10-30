# 九张已发表方法成绩表

**2026-10-30 总审查覆盖**：[READINESS_AUDIT](READINESS_AUDIT.md)给出准备状态与
完整论文骨架；[PROJECT_BOUNDARY](PROJECT_BOUNDARY.md)建议后续独立轻量工程，
本轮没有创建。GVC0语义/非0敏感性评价、LEA实现与共同公共包已补；材料齐备不等于
公共接线、三章可编码设计和新范围规范已全部完成。原分/新审查事实见R1 §25.154。


2026-10-30，完整指标组版。当前只核论文与原分，不要求代码，不复现模型。
数字统一保存在[R1 §25.153](../../results/PHASE_R1.md)，本文件是逐表导航；§25.152单列主分的历史版保留。
共同主指标为完整共指系统的CoNLL F1。原表分数不当作阶段模块的单独收益。

| 研究章 | ECB+ | GVC | WEC-Eng |
|---|---|---|---|
| 第3章：候选覆盖 | [已发表方法成绩表](../../results/PHASE_R1.md#fullmetrics-ch3-ecb) | [已发表方法成绩表](../../results/PHASE_R1.md#fullmetrics-ch3-gvc) | [已发表方法成绩表](../../results/PHASE_R1.md#fullmetrics-ch3-wec) |
| 第4章：语义精判 | [已发表方法成绩表](../../results/PHASE_R1.md#fullmetrics-ch4-ecb) | [已发表方法成绩表](../../results/PHASE_R1.md#fullmetrics-ch4-gvc) | [已发表方法成绩表](../../results/PHASE_R1.md#fullmetrics-ch4-wec) |
| 第5章：簇级归并 | [已发表方法成绩表](../../results/PHASE_R1.md#fullmetrics-ch5-ecb) | [已发表方法成绩表](../../results/PHASE_R1.md#fullmetrics-ch5-gvc) | [已发表方法成绩表](../../results/PHASE_R1.md#fullmetrics-ch5-wec) |

各表列MUC、B³、CEAFₑ、CoNLL、LEA五组F1及原论文Table/PDF页；可跨章重复相同对手。
原文未报告的量写“—”，不靠其他论文/变体补齐。

[P/R/F1全量附表](../../results/PHASE_R1.md#fullmetrics-prf)统一按P/R/F1顺序。
[逐章指标规范](METRIC_SPEC.md)规定主辅判据、分母、候选与单例、消融和成本。
CD-DCE的ECB+非oracle原表存在分项均值与CoNLL列不符的问题，所有展开行标†；
保留原印值，不自行修正，不作唯一严格目标锚。
WEC表采用同任务的共同完整系统对照。Oracle、encoder、LLM辅助输入、原始selection
及均值/单次运行条件在结果页脚注和机器可读来源中保留。没有为填满单元拼接其他
数据或其他指标，也不因无公开仓库剔除近期论文。

完整指标收据：`runs/stages/R1/r1-v130-full-metric-preparation-20261030/`；
原主分与原版九表收据R129继续保留。
