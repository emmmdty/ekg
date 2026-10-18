# ERGO native训练与选模契约草案（2026-10-18，未准入执行）

C41-A-R/表4-3/FR-016(b)；科研价值与可行性见R1 §25.109。这是已知公开强对手的透明
native适配，不是独立创新。GPU成本/最大dev容量/正式执行配置尚未闭合，**不启动epoch**。
5090已有许可仅覆盖本次成本suite，不能据此启动本草案训练；4090仍须空卡和生产闸门。

## 固定科学与输入口径

- 外部ERGO revision `afa3d347ec360242c01d15a34b1f1ae63714c789`，原Longformer/RGT/focal
  类体保持；只调用真实公开`train_epoch`，不重写公开训练数学，不重建未发布BERT-window。
- P1 r15、v6 train/internal-dev两个manifest、完整有向event mention候选、官方evaluator
  均保持。train特征/独立targets使用R192 cache-global冻结文件；dev使用R196完整无标签
  特征。权威身份及容量只见R1 §25.97/§25.108；不得截断真实词、marker、padding或候选。
- 全长4096，cache的真实BOS/EOS global policy；正文CLS-only差异保持披露。没有给定
  event type、gold关系或cluster身份输入模型。TIMEX保持ID口径，不额外造causal TIMEX对。
- 标签NONE=0/PRECONDITION=1/CAUSE=2；训练监督与R192已核原生Cartesian展开一致。
  不改标签、负采样、阈值、类别权重或原图层以规避成本/效果失败。

## 训练设置

固定seed13，float32、batch1、accumulation1、20epochs；lr2e-5、原HF4.11.3 AdamW、
eps1e-8、weight decay0.01（bias/LayerNorm排除）、clip1；linear schedule/warmup10%。
后者按真实公开代码，论文8%差异逐条记录；不按dev在两者间选择。一次原train全量为一
完整epoch，原三类focal alpha0.75/gamma2、heads4、dropout_att0.1/dropout_emb0.3。
两个新增marker采用旧HF式独立初始化，显式mean_resizing=False；不启AMP/TF32/PAD优化/
额外重计算或多seed。若未来必须改工程执行版，另冻身份和数值/有效性门，不静默替换。

保留原`train_epoch`函数体；missing processor_esl等环境依赖由只提取真实函数解决。
日志原binary compute_f1可用经过逐值回放的前缀累计实现，保持原返回值、只避免重复扫描；
它把正例子类型交换算对，**只作为上游binary训练日志，不能做native选模或主指标**。
日志适配不改变forward/loss/backward/clip/optimizer/scheduler顺序。tiny回放必须核参数、
optimizer、scheduler与原始函数相同；这不替代完整真实模型/epoch生产smoke。

## 官方选模与独立核算

只用internal-dev官方三类causal micro F1，每epoch一次完整预测，argmax三类、不扫阈值；
相等分数保留最早epoch（与现本地A4严格`>`一致，列为对原`>=`的透明差异）。gold路径是
原A3 preflight的`data/MAVEN_ERE/valid.jsonl`，该文件是internal-dev，而非官方final-valid。
其SHA由已封存A3官方报告钉住；当前准备不读取新gold内容或生成分数。不得拿public valid
或final-valid选档，也不按train F1/原binary scorer选档。

dev模型forward只接无标签特征，原forward所需target以全零placeholder提供；已做target
独立性验证，gold只交给独立官方scorer。完整保存各epoch预测/三类classes、选模轨迹、
选中epoch及其源码/配置/输入hash。完成后独立从选中checkpoint重算完整官方causal分数/
逐doc counts与配对误差，对照冻结主锚和既有完整强对手；主锚不重选、不抹旧负结果。

ERGO只有causal head，其他family占位不是护栏效果，主表应标不适用，不将其零分当实测
退化或声称通过跨family门。未来方法的护栏与同backbone对照仍须独立冻结。

## 生产前必须补齐

1. 有效GPU成本报告、相应显存/工期预算；最大internal-dev无标签病例no-grad容量。
2. 原机完整模型生产smoke、thin loader/原函数真实测试、三件套及源码/配置部署身份。
3. 独占输出与预算闸门都已通过的正式执行配置。执行主机/物理卡/确切命令与预期产物另冻，
   启动前披露并核空卡；5090完整训练须另获许可，不能套成本suite许可。
4. checkpoint留训练原机；不跨机搬本项目checkpoint。不创建等卡、自动重试或多seed任务。

OOM/非有限值或超预算如实保留，不删最大文档、缩候选、降backbone或放宽数值门救分。
完整预算未闭合不承诺完工时间，单seed分数也不完成本项目创新/确认KR；科学门如实裁决。

完整入口已实现于`scripts/train_ergo_native.py`，审查配置为
`configs/ergo_native_training_unadmitted_20261018.json`。默认三个admission=false，且设备/
预算/容量/生产smoke均待实际证据；运行该提案会在读数据/载模型前拒绝。未来使用另冻
正式配置，不能只翻flag；入口要求三件完整CUDA costs（固定原full4096、两次lr0且参数
数值不变）、最大dev的CUDA no-grad/target独立性、原epoch真实CUDA生产smoke与相应
pinned身份。CPU/toy记录不能代替这些门。5090 full20epoch权限由独立scope记录核验，
既有20分钟cost授权不匹配该scope。

训练前实际输入/成本联核已进入v2入口：当前审查配置为
`configs/ergo_native_training_unadmitted_v2_20261018.json`，仍默认不可执行。旧v1提案
及其源码b6cdde8保持追溯。正式运行前须逐篇核完整4096/BOS/EOS padding、所有候选位置/
MID顺序与固定train/dev digest，并将实际训练features/targets SHA与成本config输入SHA
相等联核；同内容路径变化可接受，改变内容需要重新通过相应门。此版本增加有效性门，
不改变原模型/训练数学，R199真实CPU smoke仍用其冻结e7de4fa重放。


## 10-18阶段收尾补充（不准入执行）

当前源码对应审查配置另存`configs/ergo_native_training_unadmitted_v2_close_20261018.json`；
旧v1/v2提案保留各自固定源码身份。三个admission均false，未来另冻正式配置。
新`preflight_ergo_native.py` v2可产出CUDA容量/production报告：原函数两次lr0后保持
optimizer状态驻留再测最大dev；CUDA路径尚未实测，不能将接口存在当作报告通过。
R199 CPU v1重放仍用e7de4fa，不用新入口冒充旧证据。

原函数加载另加透明fail-fast绑定：`clip_grad_norm_(error_if_nonfinite=True)`，在有限
元素的全局范数溢出时拒绝静默清零；健康数学路径仍调用同一Torch函数，旧结果不改写。
独立复算入口`scripts/verify_ergo_native_checkpoint.py`只接受完整20epoch report和配置/
checkpoint SHA身份，通过完整三类classes逐值对齐后交官方scorer核分；当前未有真实
checkpoint可复算。checkpoint留原训练机，5090还须新许可明确覆盖独立验证。

作者本轮要求阶段收尾，现仅交付软件与CPU验证，证据及限制见R1 §25.116–§25.117。
已授权三例成本尚未执行；无新增训练/推理许可、无自动等卡器。
