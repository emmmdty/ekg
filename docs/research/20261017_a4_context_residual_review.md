# A4上下文交互与表示残余问题（2026-10-17，诊断闭合）

执行入口认EXPERIMENT_PLAN §4的C41-A-R；10-15目标模板的当前准入回合已关闭，
本卡提出下一可检验问题，不代表已选新模型。三个科学Objective仍未完成。

**科研价值**：对准表4-3/KR3.1–3.2。强锚全train真实残余、原目标分解与ordinary priors
见R1 §25.87–§25.91；不再预设多原因single-winner问题。下一判断原256窗口中两端的
共同语境/跨窗口信息通路是否构成具体机会，并排除sentence距离、subtype及mention重复
的解释。该事实若成立也不等于发明跨窗口attention：ATLOP/ERGO/GC等邻居保持必审。

**可行性**：复用R188完整classes/无label输入和固定train gold，使用原source/tokenizer
重放预处理，不运行encoder/optimizer，不读held-out/final-valid选规则，不搬权重。
schema/hash、文档/mention/pair全集必须与R188一致；未知/空span或ID错配直接失败。

一次合并诊断包括：

- 用原tokenize的实际event spans映射每个endpoint到原窗口，核完整可见性；原source
  encoder在各窗口内编码，再拼接事件表示，跨窗口时没有同一次token-level attention。
  这不证明pair scorer无法结合两个局部表示，更不把它称信息论不可能。
- 对完整native causal候选按同句/异句同窗口/跨窗口报告原3×3混淆、P/R及机会数，
  不忽略None误报，不把更低positive base rate当模型机制。
- 在同一个gold event-edge内部，比较其不同mention-pair context，保留subtype与
  原生identity，并另列相同精确sentence-distance的配对，核是否有同时覆盖多个context
  类别的真实机会。它仍是观察性对照，
  mention措辞/位置并未随机化，不把原始差异作为处理效应。
- 分开one-distinct/single-mention、one-distinct/coref与multiple-distinct组；复用既有
  完整残余，不为每个切片重跑模型，也不凭一个小slice选择threshold/新模块。

若跨窗口/配对机会不足或不能排除竞争解释，记录具体数据/识别障碍，不训练新模块。
若存在机会，下一必须定义相对最近方法的实质变化及可证伪对照，闭合power/预算后
才能进入A-A。普通cross-attention、pooling、loss reweighting或旧aux迁移不自动准入。

**实际裁决**：R1 §25.93已闭合。全trigger完整可见；同event-edge/精确句距配对的区别
有限且有选择/文本混淆，当前不准入窗口新方法；没有证明所有未来窗口方法无效。
当前诊断不复跑，下一[ERGO强rival native可行性卡](20261017_a4_ergo_native_review.md)。

## 2026-10-27 R117/R118覆盖：硬结构版本停止，接R119

旧窗口诊断、ERGO/CE训练及R109–R111均已完成，数字只认结果页，不能由本卡旧接续
重起。新来源与原train可行性见R1 §25.141；SERE真实代码现已定位，普通检索/因果
pattern先行机制不能换名；硬chain/fork/collider蕴含native边的版本有原生反例而停止。

下一只有R119机制候选：预测结构证据中，同见证两条关系的联合可靠性是否能提供
超出边缘乘积和普通联合分类的干预。拟研究量为`q(r_uw,r_wv|text)`，不能从全局
标签共现、oracle gold或“9类比两个3类更复杂”推导独立贡献。推理不得读gold边/
identity，保护原文本通路/完整候选。若只能归入已知概率图/三元监督/单边entropy，
拒绝当前表述，不编码泛化模块；实质差异/强替代/power/成本闭合前无新训练准入。

### R119收窄的候选计算（研究候选，不是方法准入）

在给定完整文本/mention的同一原模型内，对distinct mention三元组(i,w,j)和四种
有向两腿形态，预测原生三类×三类的联合分布Q。训练监督只取原train两条边的原生
标签；推理没有gold其他边、gold coref或新标注。四种形态为正/反chain、fork、collider，
不把任何形态解释成一定有待判边。标签NONE只指原注释。

具体待验delta为`D=Q-row(Q)⊗col(Q)`，其行/列和为零。通过同容量的类型兼容读出，
比较联合读出`sum(Q*K)`与乘积读出`sum((row(Q)⊗col(Q))*K)`，差恰为`sum(D*K)`。
保留原三类绝对判别loss及完整文本通路；不让组内相对目标替代NONE校准。
这里不声称最终待判边的边缘分布保持不变；若保持所有输出单边边缘再用相同argmax，
本来就不会改变预测。也不把D当世界因果效应、真实后验或已校准不确定性。

需要的强比较是：相同联合监督/参数预算下的乘积读出；去掉关系修正、只留辅助监督；
破坏修正向量与待判事件对归属、保留doc内总量的负控。负控不能只重排同一(i,j)内部
的w，因为均值读出对这种置换不变。未来完整方法还必须胜冻结joint与已跑ERGO/CE
强对照，适用其他关系及召回护栏不得借“causal-only”自动记通过。

SERE/iLIF/ERGO的pattern/图传播、CopulaLSP的edge correlation、SPEECH的类别能量
均属已有机制。上述差异仅使这个具体候选可接受进一步原train信号/可识别性审查，
不是“首次联合概率/协方差/高阶推理”的论断。组合是否有独立研究价值仍待强对照
和原R1完整门；没有在文献边界外声称无先行性。R120只核原生联合标签/重复/输入
和规模，不能从计数推出正向效果或用更多审计代替完整方法比较。


### R120/R121裁决后的候选边界

完整监督/规模/独立复核与精确代数结果只见R1 §25.143–§25.144，不能从数据可得
准入方法。固定预测标签处Q可以预报共同正确，但D是有正负的关联修正，未校准；
one-hot为零不是所有软推理不可行的证明。纯加性K被D消掉，未来须显式检验交互项。

**拒绝普通full-Q读出直接报新颖性的版本**。现仅保留待裁问题：原绝对判别旁的
D-only修正，是否比full-Q、product、aux-only及有效pair归属shuffle更能泛化。
full-Q必须成为强替代，不得只把full-Q与product比较后声称排除了普通联合辅助。
五臂Q监督/参数/初始化/训练预算应相同；不调用gold边/coref，不通过采样排除NONE。

下一设计裁决认主表R122及R1 §25.145；不是新训练准入。先核此计算相对已有机制的
实质变化与可识别比较，若只是普通联合head/已有概率图移轴就停止。UAIGR仍未核到
完整公式/官方运行实现，记录缺口，不能写成已排除近邻。禁止继续重做已完成计数/
toy或冻结模型前向；尚无新的主指标效果，power/预算/完整合同仍欠。
