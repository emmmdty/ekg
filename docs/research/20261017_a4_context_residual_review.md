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
