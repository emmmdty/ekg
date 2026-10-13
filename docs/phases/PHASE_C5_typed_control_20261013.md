# C-41：冻结 scorer 的类型一致性控制

科研价值：对准表 5-3，检验当前最强 official-joint control 未使用任务给定类型时的遗漏，
防止未来把既有 type agreement 的收益误归因给新机制。Lu & Ng (NAACL 2021) §4.1 C1/Eq.11
已有类型一致性成本；这里是给定类型的固定硬约束，非其六任务模型复现，非论文创新。
可行性：§25.40 已在原机 CPU 完整重现 scorer/decoder，291 文档缓存与原预测 byte-identical；
无标签 test input 已提供 mention types。仅 CPU 缓存重放，零模型训练、零额外 seed、零权重搬运。

预测前冻结：同一完整 scores/input/manifest/evaluator/candidate digest；先无约束重放 exact parity，
再将不相同类型的 antecedent ranking entries 标为官方 padding 值 -1000，dummy 与全部同类型分数
保持不变，复用原 checkpoint workspace 的 get_predicted_clusters。没有阈值或 penalty sweep。
保存所有原 mention IDs、完整输入候选 SHA 与 explicit constraint policy；有效可选边由已知约束改变，
不得说与原 baseline 的 decoder policy 相同。关系字段只复制；不声称关系头改变。

生产推理不读取任何 gold cluster/type 标签文件，类型仅来自冻结无标签 test input；
独立 official scorer 使用原 internal-dev ERE gold、P1 source_lock 与 candidate digest。
原 anchor/封存结果不重绑、不改写。本行标 exploratory derived control；即使提高，也不替代方法准入、
≥80% power、消融/负控或多个强对照胜出。新方法必须明确处理此 control 的比较口径。

cwd gpu-4090:/data/TJK/ekg，CPU/CUDA 隐藏、threads=4，源码/输入/hash/config 在执行前冻结。
唯一新输出根 runs/stages/R1/r1-v63-c5-20261013/type_control/，已存在即停止，不覆盖。
