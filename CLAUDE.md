# EKG · coding agent 上下文

> **`CLAUDE.md` 与 `AGENTS.md` 内容保持一致**（Claude Code 读 `CLAUDE.md`，Codex 读 `AGENTS.md`）。
> **改一份必须同步另一份。** 设计总纲 → `docs/SPEC.md`｜实时状态 → `docs/TODO.md`｜工程坑 →
> `docs/ENGINEERING_NOTES.md`｜服务器运维 → `docs/GPU_RUNBOOK.md`｜三端协作流水线 → `docs/PIPELINE.md`。
> **当前唯一研究主线是 v4 四章（身份 → 结构 → 事实 → 传播/下游）**；旧 TKG 线只在 tag
> `frozen-tkg-line` 保留，**SARGE / 金融应用层已于 2026-07-27 整体移出主干**（四章无一依赖；
> 历史留档正文已移出仓库，索引见 `docs/ARCHIVE_INDEX.md`）。出现冲突时以 `docs/SPEC.md` 为准。

## 校验命令（改代码后必跑）

```bash
uv run pytest          # 全绿（只增不改；旧 TKG 线已移出主干，见 tag frozen-tkg-line）
uv run ruff check src tests scripts   # 0 error，≤100 列
uv run ekg-smoke    # CPU 端到端冒烟
```

## 本地环境

- 工作区 `/home/tjk/myProjects/masterProjects/ekg`；WSL2 上 Ubuntu，zsh；Python 用 `uv`。
- **本地是 git 仓库**（分支 `main`）。提交/推送**仅在用户明确要求时**。

## GPU 服务器（两台，均多人共用）

| | **`gpu-4090`（主）** | **`gpu-5090`（备）** |
|---|---|---|
| 何时用 | 默认 | **仅 4090 不可用时，且须用户逐次许可** |
| 远端根 | `/data/TJK/ekg` | `/mnt/aidata/tongjiakai/ekg` |
| 卡 | 4×RTX 4090（card 3 故障需 NVML shim，优先 card 1） | **单卡** RTX 5090 32GB（无 card 可选） |
| GitHub | HTTPS 直连可用 | ⚠️ **443 不通**，remote 必须走镜像 `https://gh-proxy.com/https://github.com/emmmdty/ekg.git` |

- 两端 Python 环境**统一**：`.venv/bin/python` = CPython 3.10.20 + **torch 2.8.0+cu128** + transformers 4.53.3。
  cu128 是唯一同时覆盖两卡的栈：wheel 含 sm_120（5090 Blackwell，cu124 完全没有），4090（sm_89 Ada）
  走 sm_86 同 major 二进制兼容——**任何 PyTorch wheel 都不含 sm_89**，与版本新旧无关。
- **ssh 失败 ≠ 远端进程死亡**（两台都走 cpolar 隧道，间歇掉线）：三态判活（ALIVE / GONE / ssh 失败），
  只有成功 ssh 读到进程 GONE 才算结束。
- ⛔ **服务器上不要跑 `uv run` / `uv sync`**：会把环境对齐到你给的 extras 集合并**卸掉多余的**——
  4090 实测裸 `uv sync` 卸 165 个包（torch/vllm/trl 全没）、`--extra llm` 仍卸 109 个。
  一律用 `.venv/bin/python` / `.venv/bin/pytest`；非要用 uv 必须 `--no-sync`。
  （`uv pip install -e . --no-deps` 安全，改名/换路径后用它重建 editable 安装。）
- **代码同步走 git**：远端 `git fetch && git reset --hard origin/main` 拉 `github.com/emmmdty/ekg`
  （PUBLIC，免 token；5090 见上表镜像）；**数据/产物/大文件走 `scp` + `sha256` 双端核**（数据不进 git）。
  两台服务器之间不能直连，大文件**经本地中转**（cpolar 约 400KB/s，481M 的 checkpoint 单程约 20 分钟，
  用 `rsync -aP --append-verify` 断点续传，别用带 timeout 的 scp——会静默截断出半个文件）。**禁 `rsync --delete`
  与远端 `git clean -fdx`**（会删 `runs/`、`nvmlshim/` 等 remote-only 产物）。完整闭环见 `docs/PIPELINE.md`。
- 非交互 ssh 里 `python`/`jq`/`rg`/`tmux` 可能不在 PATH；用绝对路径 / `bash -lc` / `sed`·`grep`·`find`。

## GPU 运行约束

- **GPU 使用无限制，有空就可以去用**（作者 2026-07-17 授权、2026-07-27 再确认）：本地三件套全绿后
  可自行起训练/推理，**无需逐次点头**。⚠️ 该授权**只覆盖 4090**；用 5090 须逐次问用户。
- 选卡前 `nvidia-smi` 原子核卡（不隔启动复用），**不挤占他人正在跑的卡**。5090 是单卡机，
  没有「换一张卡」的余地——卡被占就只能等或回 4090。
- `uv run` 约 1 分钟才真正占显存，发射后轮询 VRAM 爬升再判「真在训」。
- 长训练用 `screen -dmS` / `nohup` + `python -u`，输出重定向 `logs/`。

## 硬约束（最易违反）

- 包/函数名**不得含 `ch1/ch2/ch3`**；新组件走 registry + lazy import；GPU 组件配 CPU 缓存回放。
- **`EventNode` schema 零新增字段**（扩展用 `metadata`）；`tests/core/test_propagation.py` 是测试锁。
- 报告结果**如实**（数字降就说降；ssh/工具失败不得伪装成结论）。**专利 / 论文写作不在计划范围。**
