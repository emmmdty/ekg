# ERGO真实原trainer接线/最大dev CPU smoke合同（2026-10-18）

C41-A-R；价值/可行性见R1 §25.112。仅原4090 CPU，原完整4096/float32/seed13/原模型与
损失不变，无dev gold/评分/预测或checkpoint保存，不处理完整native epoch。

入口`scripts/preflight_ergo_native.py`，配置`configs/ergo_native_cpu_preflight_20261018.json`。
新顶层native_train_batch供正式入口和本次smoke共用，严格batch1、原七字段及完整有向
候选/原criss-cross布尔mask。先对最大dev候选文档做两次eval/no-grad，目标全零与全一，
只验logits有限/逐值相同，不存预测；再用两个冻结train fixture，经真实原train_epoch、
原focal/legacy AdamW/原linear schedule，各一次lr0。全部参数数值不变，零符号字节变化
单列；gradient覆盖在optimizer前捕获，避免原函数zero_grad后误判全部参数未使用。

输出仅CPU容量/接线报告和status；两个pooler参数若无gradient如实列出，不修原模型。
CPU报告不能通过正式入口要求的CUDA成本/最大dev容量/production门；当前CUDA路径
明确拒绝，不暗用既有三例成本许可。未来GPU smoke是新身份/相应许可的独立任务。

本地三件套与原机实际tests通过并push后执行。cwd `/data/TJK/ekg`，只发一条后台任务：

```bash
setsid nohup timeout --signal=TERM --kill-after=30s 600s env \
  CUDA_VISIBLE_DEVICES=-1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  .venv/bin/python -u scripts/preflight_ergo_native.py \
  --config configs/ergo_native_cpu_preflight_20261018.json \
  > logs/ergo-native-preflight-r199-20261018.log 2>&1 < /dev/null &
```

预期`runs/stages/R1/r1-v99-ergo-native-preflight-20261018/cpu/`中capacity_report/
production_report/status JSON；输出存在即失败，不覆盖。600秒TERM/额外30秒KILL，
无自动重试；SSH失败UNKNOWN，只有成功读进程不存在才GONE。失败留traceback/已有产物，
不删最大文档/缩输入/改图层或放宽数值门。结果不能冒充ERGO科学效果或CUDA可行性。
