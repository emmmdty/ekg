# C41 mass 的独立数值修复合同

科研价值：恢复表5-3/KR1.2的预声明总量控制，不是新科学候选。可行性：原公式在
合成有限float32 logits复现分母0/非零delta（R1 §25.75）；只改等价数值计算，
保留旧失败身份。此合同先做数值/生产准入，不因文档存在就启动训练。

## 等价式与边界

令E=1-C为同一forest的不连通概率，R=1-QQᵀ为两个独立forest根不同的概率。
原score=QQᵀ+[(C-QQᵀ)之和/(1-QQᵀ)之和]*(1-QQᵀ)
恒等于score=1-sum(E)*(R/sum(R))。沿原type block内严格下三角求和；alpha梯度
完全保留，不detach、不加epsilon、不clip或回退root。E按正数递推
E[j,i]=p[j,dummy]+sum(k<j)p[j,k]E[k,i]、E[i,i]=0；R用根边缘中
不同根的非负乘积和，按exclusive prefix/suffix累加，避免1-q的消减。
sum(R)=0时只接受sum(E)=0，score=1-R为全确定同根的数学边界；异常仍fail-fast。
无pair返回原空pair零aux，混合type分块规则不变。

canonical marginal及四头/参数/optimizer仍原FP32；仅mass auxiliary的typed softmax、
正数递推和聚合使用float64，梯度回传原FP32 logits。精度变化须在表下注明，不能称
原float32五臂实现完整；它不改变理想实数目标，但有限精度训练轨迹可能不同。
不以此宣称任何效果/新颖性，也不把合成反例称原训练batch重放。

## 准入与执行

原code/config/failed train/mass不可修改。新registry组件/入口复用原官方Model、
loader、joint loss、训练循环、export/CPU decoder；需为目标注入复制少量已冻结fit
接线，不修改封存入口。新config绑定base config、phase、代码与CPU数学证据。

1. 先TDD：饱和反例、24forest独立穷举、一般点值/梯度、极端分数与type分块；
   新生产测试真实torch执行；本地pytest/ruff/ekg-smoke全通过。
2. 4090 CPU固定peak8原完整四头，legacy mass与新实现的loss/所有221参数梯度
   按既定rtol1e-4/atol1e-6比较（不调宽）；全模型参数digest前后不变。
   此门失败不继续训练，先回排障，不用dev论证等价。
3. 单卡空闲后一个真实optimizer周期，沿原四个8doc fixture及原train-only无标签
   export/CPU replay；报告峰值/state/实际更新，失败保留。不复跑其余四臂smoke。
4. 通过后外部文档锚住新admission/hash，才从同initializer固定seed13重跑mass的
   100epoch/8200updates；非resume，lr/optimizer/scheduler/batch/accumulation/decoder
   与原合同相同。独占根runs/stages/C5/c5-mass-repair-20261016，checkpoint留4090。

既有其他四臂的源码/训练/endpoint身份原样复用；不重跑未受影响臂，不读dev选修复。
全部有效臂endpoint后才评分；原评分目标/阈值/区间/护栏不改，独立evaluation overlay
仅将mass路径映射至新身份，并钉住其他四臂原endpoint及原eval config。旧mass明确FAIL。
若修复后的关键科学比较失败即停候选，不扫描精度/公式/权重救分。单seed探索性、
final-valid封存、额外seed与跨机checkpoint边界均沿原合同。
