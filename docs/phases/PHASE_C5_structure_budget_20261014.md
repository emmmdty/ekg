# C-41 固定五臂结构/optimizer成本合同

仅R1成本审查，method_admitted=false，不评测/训练epoch、不读取dev/final-valid。
科研价值/可行性与预声明认R1 §25.63；原四头CUDA验证认§25.62。

目标/候选/权重认研究brief的冻结五臂，head raw logits经已封存typed_probabilities，
规范first-dummy marginal +固定doc聚合pair-F1；exact/root/mass/shuffle复用已核矩阵，
mass的alpha参与autograd，shuffle按seed13|doc|type|mention SHA排序。
第一臂aux=0，固定0.4/2/4/4；不扫scale、threshold、budget或seed。

本机源码与pretrained2c7ff1…、完整train/P1/manifest、原两fixture/cuda报告、helper
和矩阵SHA锁定。原71be…不改写，weights不跨机；新pin5文件与原权重相同，
规范25byte metadata替代旧错误JSON。GPU前本地完整门、远端真实CPU测试和实际
CPU完整exact fixture必须通过；仍先披露CUDA命令并核空卡。

固定peak/worst两个8doc病例，各五臂、seed13。nonreentrant checkpoint=true，
torch cuDNN deterministic=true/enabled=false；原架构FP32，不用AMP/梯度裁剪。
encoder AdamW/scorers Adam沿官方实现，严格lr=0，cold/warm两个真实step，
各optimizer两次（共4 API调用），真实moment状态及temporaries实测，参数SHA
前后相等。无scheduler/权重更新，不称正常训练步时间或epoch实测。
参数不等、非finite、输入漂移、OOM均FAIL，独占输出保留且不覆盖。

输出新R1根structure_budget/<cpu|cuda>/<fixture>/<arm>/，report与manifest。
记录allocated/reserved峰值、同步forward/backward/optimizer timing、真实state bytes，
code/config/input/initializer与参数digest，完整loss分项。GPU进程必须只有一张
明确选择的空卡（memory<512MiB且无compute PID）。不同arm/fixture可并行，
不得把不同seed伪装成成本任务。成本PASS不自动准入方法。
