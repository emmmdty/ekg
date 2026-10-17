# A4 ERGO强对照native可行性（2026-10-17，R1 wip）

只执行EXPERIMENT_PLAN §4当前C41-A-R的准备步骤；不放行encoder、训练或GPU成本任务。

**科研价值**：对准表4-3/KR3.1–3.2及FR-016/QR-001，用独立发表、已核真实模型/trainer的
pair-graph + focal方法约束未来创新归因。R1 §25.91–§25.93不支持原目标模板或普遍窗口
瓶颈，不继续以这些动机直接造模块；已知ERGO机制的得分不能当本项目创新。

**可行性**：R189已固定作者revision、真实RGT/Longformer类与native三类metric差异。
当前只读原缓存元数据/正文与固定MAVEN train，核Longformer tokenizer的真实长度和
全部mention候选可表示性；不载入encoder、不新增包/seed/5090任务、不搬checkpoint。

输入与保真度要闭合：

- 回原论文表格/设置、可见原缓存和CV代码，核evaluation unit/方向/标签、fold membership
  与原始数字可验证性。未知先标UNKNOWN，尚无FR-016完成状态；不据binary scorer的
  nonzero合并评价native CAUSE/PRECONDITION。
- 复用原Longformer模型与原RGT/focal实现，native特征仅适配已有接口；不重写未发布的
  BERT窗口模型后冒称官方复现。processor模块名、optimizer/import依赖及native metric
  差异若需补丁，必须给前后hash和binary等价/native错subtype测试，当前不实施补丁。
- 全文、全部event mentions与每个ordered pair都保留；训练gold event labels只用于官方
  Cartesian监督，推理无gold coref。只核原Longformer容量内可表示性，不裁候选或token
  来使路线看似可行。原文档上限若不容纳native输入，则点名【协议/数据】停止该执行版本。
- graph的dense mask不等于稀疏预算；R189仅给单buffer下界。真实完整候选成本必须在
  另一个明确准入的成本合同/本地门/合法空4090上测，当前不启动它。

此项若可行，只支持后续强rival适配/预算合同；baseline训练与新方法训练均未获本卡
放行。若不可行，记录具体类别与一手证据，再由执行代理先改主表选择下一公开强rival。
原A3 ATLoss、A4 masked/retained及其他封存结果身份保持；所有科学KR仍待验收。
