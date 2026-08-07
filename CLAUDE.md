# EKG · coding agent 上下文

> `CLAUDE.md` 与 `AGENTS.md` 内容一致（Claude Code 读前者，Codex 读后者）。**改一份必须同步另一份。**
> 本文件每次会话都入上下文，**只放「删掉就会出错」的东西**；细节一律放下面的文档，按需读。

设计总纲 `docs/SPEC.md`｜实时状态 `docs/TODO.md`｜**实测数字 `docs/results/`**｜
baseline 与消融 `docs/EXPERIMENTS.md`｜工程坑 `docs/ENGINEERING_NOTES.md`｜
服务器运维 `docs/GPU_RUNBOOK.md`｜三端流水线 `docs/PIPELINE.md`｜归档索引 `docs/ARCHIVE_INDEX.md`。

**当前主线是 v5 四章**（2026-08-07 重设）：Ch1 事件身份消解 · Ch2 事件关系抽取 · Ch3 事件事实性检测 ·
**Ch4 构建质量的下游代价与消费者依赖性（headline）**。活线 = `docs/phases/` 的 A2 / C3 / D2 / E2。
> ⚠️ **这是学位论文的标尺**：每章都必须在**公开可比的主指标**上**超过多个（不是一个）**方法。
> 「不用超 SOTA」**不等于**「不用超 baseline」。低于 baseline 时方法章的贡献为零。
> ⇒ 章节按**「有公开对手的任务」**组织，**不按自造的辅助指标**（难例误合并率 / ECG 可重建率 /
> 结构违反数都只有我们自己在测，撑不起对比）。v4「可信度四维」脊柱与六个自研机制的方法卖点
> 均已作废，零效应结论**保留为 Ch4 的归因证据**。

旧 TKG 线在 tag `frozen-tkg-line`；SARGE/金融层（2026-07-27）、生成式抽取+RL 线（2026-07-29）、
v4 六份 phase 契约（2026-08-07）已移出仓库。冲突时以 `docs/SPEC.md` 为准。

## 校验命令（改代码后必跑）

```bash
uv run pytest                          # 全绿，只增不改
uv run ruff check src tests scripts    # 0 error，≤100 列
uv run ekg-smoke                       # CPU 端到端冒烟
```

## 硬约束

- **单一事实源**：实验数字只在 `docs/results/PHASE_X.md` 里权威，别处只引用不复制。
  引用**外部**对标数字前必须回一手表格核实出处、split、口径——Phase C 因此白跑两轮、
  Phase A 因此把「达标」判错。
- 报告结果**如实**：数字降就说降；ssh/工具失败不得伪装成结论；负结果是交付内容，不是待修的 bug。
- 包/函数名**不得含 `ch1/ch2/ch3`**；新组件走 registry + lazy import；GPU 组件配 CPU 缓存回放。
- **`EventNode` schema 零新增字段**（扩展用 `metadata`）；`tests/core/test_propagation.py` 是测试锁。
- 代码简洁、fail-fast，**不加掩盖问题的 fallback / 默认值**。
- **专利与论文写作不在计划范围。**
- 本地是 git 仓库（分支 `main`）。**提交/推送仅在用户明确要求时。**

## 服务器（`gpu-4090` 主 `/data/TJK/ekg`｜`gpu-5090` 备 `/mnt/aidata/tongjiakai/ekg`）

- **GPU 授权**：4090 有空即可自用，本地三件套全绿后无需逐次点头；**5090 须逐次问用户**。
  选卡前 `nvidia-smi` 核卡，不挤占他人正在跑的卡。
- **checkpoint 训在哪就留在哪，不强制回传**（作者 2026-08-06 改；原「一律回传 4090」
  在 4090 隧道断掉时反而卡死工作）。**要跨机搬运先问用户**——单程约 70 分钟，值不值得由用户定。
  档在哪台**必须记进 `docs/results/`**；失败/发散档只留数字，权重不必留。
- ⛔ **服务器上不要跑 `uv run` / `uv sync`**——会按 extras 卸包（实测卸 165 个，torch 全没）。
  一律 `.venv/bin/python`；非用 uv 不可时加 `--no-sync`。
- ⛔ **禁 `rsync --delete` 与远端 `git clean -fdx`**（会删 `runs/`、`nvmlshim/` 等 remote-only 产物）。
- **ssh 失败 ≠ 远端进程死亡**（cpolar 隧道会掉线）：三态判活 ALIVE / GONE / ssh 失败，
  只有成功 ssh 读到进程 GONE 才算结束。判活看 `ps -eo etime` 或 `nvidia-smi`，别靠对时间的感觉。
- 代码走 git（远端 `git fetch && git reset --hard origin/main`），**数据/产物走 `scp`/`rsync` + 双端 `sha256`**。
- 长任务用 `setsid nohup` + `python -u`，输出重定向 `logs/`；**一条 ssh 只发一个后台任务**。
- 非交互 ssh 里 `python`/`jq`/`rg`/`tmux` 可能不在 PATH，用绝对路径或 `bash -lc`。
