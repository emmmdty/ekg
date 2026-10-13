# C-41 · 固定 null head 的决策单位审查

科研价值/可行性/预登记认 R1 §25.48。本次是 ordinary anaphoricity routing 的单变量
counterfactual，不是新方法。保留 §25.45 的封存负结果，不重训、不换 head、不扫参数。

沿用同一 train-only final-epoch10/seed13 三臂 head、train-only scaler、无标签 dev features
和原 legal real ranking/type policy。权重留4090；原 decoder 的逐 candidate argmax 先从
同 head 精确重放所有旧预测，失败即停止。Scaler 使用原 float32 transform 顺序，
不改为先转float64再缩放以免改变重放数值。全部源文件、heads、缓存由 SHA 固定。

有合法前项且 z>0 时取最高 raw legal score 前项，否则dummy；z=0固定dummy。
二类阈值0对应该 BCE class 的等代价决策，不用 dev选阈值/epoch/动作。
三臂全部执行，输入/候选/关系字段与官方 decoder 成对，原 encoder/scorer零更新。
保存完整 head logits 以便反查两个动作的区别；不读取 dev gold/targets或final-valid。

本地三件套→4090真实CPU对应用例→正式重放→冻结 P1 scorer 独立复算四指标/paired counts。
输出独占 `null_decision_unit_audit/`，已存在拒绝覆盖，CPU四线程/CUDA隐藏。
未胜 strongest type-control或护栏损失即停止该 action；正结果也只能算已知机制控制，
不回写原§25.45，不视作创新或 R1 power通过。后续候选不据此自动启动方法训练。
