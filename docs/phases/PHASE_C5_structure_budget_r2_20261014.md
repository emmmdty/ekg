# C-41 结构成本审查 r2：严格数值不变与signed-zero字节完整性

§25.63原CPU失败/source/config/output均封存。r2复用不可改的原成本入口与
同五臂/fixture/数据/initializer/seed/loss/scale/optimizer API设置；本合同只新增
可追溯的完整性instrumentation，不更换方法或放宽数值相等。

真实AdamW/Adam step前pre-hook验证lr严格0，创建CPU参数快照，不新增GPU权重副本。
每次post-hook逐参数torch.equal必须成立；非零数值更新FAIL，且不撤销更新来掩盖。
只恢复经过验证的零元素sign bit，保存native前/后/恢复后的raw digest及数量。
最终原Model参数SHA须与initializer相同；不能将native raw digest变化隐藏。
API两optimizer×cold/warm仍共4次，momentum状态真实变化，权重没有数值学习更新。

GPU native step完成后先synchronize，再开始完整性hook计时；单列CPU复制/严格比较/
SHA/signed-zero恢复的耗时，raw optimizer span与扣除audit后的native时间均保存。
报告allocated/reserved包含很小的稀疏zero-sign恢复buffer，作为成本上界；
不把CPU完整性快照或恢复操作当production优化器的一部分。

r2执行CPU完整exact/peak必须complete，再同环境空卡运行固定10个CUDA病例。
原架构两fixture CUDA重算parity与full-train规范pin token/labels必须一致。
独占structure_budget_r2/<cpu|cuda>/<fixture>/<arm>；fail保留，不覆盖。
source/core/config/input pins实际复核，本地完整门与远端真实CPU tests必须通过。
method_admitted=false；依然不做epoch、checkpoint导出、dev/final-valid或参数训练。
