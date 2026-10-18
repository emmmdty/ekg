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


## 10-18接续裁决

来源/全train容量审查已闭合，数字/hash/原缓存tiny数值障碍仅见R1 §25.95。
选择FR-016(b)透明适配路径，尚非已复现/成绩行。保留全部ordered pairs、原RGT/focal
与diagonal mask；native类别0=NONE/1=PRECONDITION/2=CAUSE，映射必须fixture锁定。
原ESL无序二类/CV、native有向三类/固定manifest、metric、依赖、模型checkpoint可得性
逐项披露；不修原mask来冒充原基准成功。Longformer与旧RoBERTa锚的差异不能归因于graph。

当前允许最小接口实现与CPU tiny类体测试、原4090镜像权重获取（原机存留、不跨机）。
先冻结成本合同，再独立裁决encoder/CUDA预算；目前仍不运行encoder/optimizer/GPU/训练。
透明接口负责MIDs→marker位置、完整候选/标签、dtype/全邻居mask与official export，
不改原模型/损失类体，不恢复未发布BERT模型。性能与新颖性仍未验收。


公开cache进一步核查发现BOS/EOS两处global与正文BOS-only不同（R1 §25.96）。原CLS-only
准备已保留于af5c656及原config/output，不运行encoder；后续用独立cache-global配置/
输出匹配真实cache，测试锁定EOS处于最后nonpad位置。原机已直下官方Longformer权重并
核LFS SHA，未跨机搬运。接口CPU准备完成不等于真实完整模型成本通过。


## 透明输入阶段出口与成本阶段（10-18）

新cache-global输入/全量差异审计完成，原机真实测试通过，完整封存见R1 §25.97。
初始“不运行encoder/optimizer”的范围到此闭合；主表下一允许**合同冻结/门通过后**
原4090 CPU完整原模型成本：短文fixture、原类及原legacy AdamW，两次lr0 cold/warm
API，数值参数不变并区分signed-zero字节变化，无epoch/held-out/效果。
GPU须另核空卡/披露/CPU门通过；当前四卡有他人任务，不运行CUDA、不造等卡启动器。
baseline训练仍未放行，未来新方法更须独立差异/强对照/power合同。


CPU短文完整成本已过（R1 §25.99），原模型/optimizer类体真实执行，参数数值不变而
零符号字节变化如实保留。固定4096 padding的CPU成本不宜直接外推，主表下一为独立
PAD-only变长parity/CPU预算合同；真实词/marker/候选保留、原类不改，源Longformer
自动补齐window。不以eval梯度parity声称train随机流一致。CPU baseline训练仍待预算/
合同；GPU未启动。
