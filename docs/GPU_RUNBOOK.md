# EKG v4 · GPU 服务器运行手册

> 适用于 `gpu-4090:/data/TJK/ekg`（主）与 `gpu-5090:/mnt/aidata/tongjiakai/ekg`（备，**每次使用须用户
> 许可**）。只覆盖 v4 主线与仍在主干的 Ch4 可靠性模块。旧 temporal GNN、RE-GCN、Path-RL、hybrid
> 命令已失效；复现需从 tag `frozen-tkg-line` 单独建工作区，**不得在当前主干照抄旧命令**。
> 代码/数据同步的权威是 [`PIPELINE.md`](PIPELINE.md)（代码走 git、产物走 scp）。

## −1. 两台服务器速查

| | **`gpu-4090`（主）** | **`gpu-5090`（备）** |
|---|---|---|
| 何时用 | 默认 | 仅 4090 卡满/不可用，**且用户逐次许可** |
| 远端根 | `/data/TJK/ekg` | `/mnt/aidata/tongjiakai/ekg` |
| 用户 | `TJK` | `tongjiakai` |
| 卡 | 4×RTX 4090 24G（card 3 故障需 NVML shim，优先 card 1） | **单卡** RTX 5090 32G，`CUDA_VISIBLE_DEVICES=0` |
| Python | `.venv/bin/python` 3.10.20 | 同（uv 装的 CPython 3.10.20） |
| torch | 2.8.0+cu128 | 2.8.0+cu128 |
| GitHub | HTTPS 直连 | ⚠️ **443 不通**，remote 走 `https://gh-proxy.com/https://github.com/emmmdty/ekg.git`（SSH 22 也通，可作备选） |
| 其他用户 | 多人共用 | 多人共用；单卡机**没有换卡余地** |

**为什么两端都是 cu128**：5090 是 Blackwell `sm_120`，cu124 wheel 完全没有它的 kernel；而
torch 2.8.0+cu128 的 `arch_list` = `[sm_70, sm_75, sm_80, sm_86, sm_90, sm_100, sm_120]`，
4090（`sm_89` Ada）走 `sm_86` 的同 major 二进制兼容。**没有任何 PyTorch wheel 含专门的 sm_89**
（2.6/2.8/2.11 实测都跳过），所以这不是版本新旧问题，升级换不来原生 sm_89；且 matmul/conv 走
cuBLAS/cuDNN，那两个库内部有独立的 sm_89 路径，实际损失很小。

## 0. ⛔ 头号红线：服务器上不要跑 `uv run` / `uv sync`

`uv run` 与 `uv sync` 会把环境**对齐到你给出的 extras 集合，多出来的一律卸载**——两台服务器装的
都不是「裸 core」，所以两端都中招。4090 实测（2026-07-27 `--dry-run`，当时装的是
`llm+serve+rl+gnn+dev` 全套 = torch 2.6.0+cu124 / vllm 0.8.5 / trl 0.18.2 / ray / xformers；
2026-07-28 升 cu128 后 vllm/xformers/torchvision/torchaudio 已卸，见 §1.5，但结论不变）：

| 命令 | 后果 |
|---|---|
| `uv sync` / `uv run …`（不带 extra） | **卸 165 个包** —— torch、transformers、vllm、trl、peft、bitsandbytes 全没 |
| `uv sync --extra llm` / `uv run --extra llm …` | **仍卸 109 个** —— vllm、trl、ray、xformers、torchvision、torch-geometric |
| 全套 `--extra llm --extra serve --extra rl --extra gnn --extra dev` | 只卸 `patchelf`/`setuptools` 构建残留（安全，但没必要） |

恢复要重下数 GB。**因此服务器上一律直接用项目 Python**：

```bash
# 4090
/data/TJK/ekg/.venv/bin/python -u scripts/<x>.py ...        # ✅ 标准姿势
/data/TJK/ekg/.venv/bin/pytest                              # ✅
# 5090
/mnt/aidata/tongjiakai/ekg/.venv/bin/python -u scripts/<x>.py ...
# 非要用 uv 就必须加 --no-sync：
uv run --no-sync python -u scripts/<x>.py ...
```

`uv pip install -e . --no-deps`（只装本项目、不碰依赖）是安全的，改名/换路径后用它重建 editable 安装。
`uv pip install <具体包名>` 也安全（只加不减）——**5090 环境就是这么一包一包装出来的，没碰过 `uv sync`**。

## 1. 当前状态（2026-07-27）

- **Phase A 已达标**：判别式 `supervised` 抽取器 causal F1 .250 / subevent .213 / temporal .338，
  召回 0.4%→67.5%，`hallucinated=0`。交付 checkpoint = `runs/relations/supervised_maven`。
- **关键路径 = Phase B 真实图闭环**：代码 CPU 全绿，只差「GPU 产 dump → scp 回本地 → 离线分析 →
  回填」。Phase B 的实测结果见 [`results/PHASE_B.md`](results/PHASE_B.md)。
- **5090 于 2026-07-27 配好并验证**（`250 passed / 3 skipped`、ruff 0、`ekg-smoke` OK、sm_120 实算通过）。
  多出的 2 个 skip 是 `ESCSubWoRe.npy` 未传（ESC 数据，Phase B 用不到），**不是回归**——两端 total 都是 253。
  4090 当日全天 4 卡被他人占满（15–21G @ 99–100%），Phase B dump 因此改在 5090 跑。
- 已有 GPU 证据：SeDGPL 基线、风险感知选边 / 结构编码 A/B、选择性预测 risk-coverage、受控 cross-stage。
  准确数字以 [`TODO.md`](TODO.md) 与 `runs/` 为准。

## 1.5 两端升到统一栈 cu128（2026-07-28 **已完成**）

作者选的是「先验证再原地升级」：5090 先用 torch 2.8.0+cu128 把 Phase B dump 完整跑通，再把 4090
主 `.venv` 原地升到同一套。实际执行的命令（**顺序不能反**）：

```bash
# 1) vllm 0.8.5 硬 pin torch==2.6.0，先装 torch 会直接撞版本冲突 → 必须先卸
# 2) torchvision/torchaudio 是 vllm 拖进来的，为 torch 2.6.0 编译，换 torch 后 ABI 必碎 → 一起卸
ssh gpu-4090 'bash -lc "cd /data/TJK/ekg && \
  uv pip uninstall --python .venv/bin/python vllm xformers torchvision torchaudio && \
  uv pip install --python .venv/bin/python torch==2.8.0 && \
  .venv/bin/python -c \"import torch;print(torch.__version__, torch.cuda.get_arch_list())\" && \
  .venv/bin/pytest"'
```

- ⛔ 仍然**不许 `uv sync`**（见 §0）；升级只用 `uv pip install <包>`（只加不减）+ 显式 `uninstall`。
- **vllm 必须卸**：它硬 pin 精确 torch，0.10.2 起还要 `transformers>=4.55.2`，**没有任何版本能与
  torch 2.8.0 + transformers 4.53.3 共存**（4.53.3 正是写出 Phase A checkpoint 的版本）。
  `pyproject.toml` 的 `serve` extra 已随之移除；v4 四章无一依赖 vLLM。
- ⚠️ **torchvision/torchaudio 的 ABI 坑（实际踩过）**：只换 torch 会留下为旧 torch 编译的
  `torchvision 0.21.0` / `torchaudio 2.6.0`，导入即报 `operator torchvision::nms does not exist` /
  `undefined symbol: _ZNK5torch8autograd4Node4nameEv`。**要命的是它不会直接报错退出**——`peft`
  在 `constants.py` 里 `from transformers import BloomPreTrainedModel`，transformers 的 lazy
  `__getattr__` 因 torchvision 崩溃而把它报成 `ModuleNotFoundError`，最终表现为
  **10 个测试静默降级成 `SKIPPED: needs torch`**（252 passed → 242 passed，而 `import torch` 和
  GPU 实算都正常）。v4 不用视觉/音频栈，直接卸掉即可，5090 本来就没装。
- **验证必须看 pytest 计数，不能只看 `import torch` 成功**：升级后 4090 = `254 passed / 1 skipped`、
  ruff 0、`ekg-smoke` OK，`cap (8,9)` 上真实 matmul 通过。5090 = `252 passed / 3 skipped`
  （多出的 2 个 skip 是 `ESCSubWoRe.npy` 未传，非回归；两端 total 都是 255）。
- 回滚：`uv pip install --python .venv/bin/python torch==2.6.0`（cu124 index），vllm 0.8.5 另装。

## 2. 环境

- SSH `ssh gpu-4090` / `ssh gpu-5090`（都走 cpolar 隧道，间歇掉线）；远端根见 §−1。
- 🛑 **2026-08-06 起 4090 整机够不着，唯一可用的卡是 5090**。诊断（别重做）：
  DNS 正常；`1.tcp.vip.cpolar.top:12644` **`Connection refused`**（连测 5/5 一致，不是超时也不是
  reset）；**同一个 IP 上 a6000 的 14462 端口正常握手** ⇒ cpolar 边缘节点本身健康，
  是 **4090 那侧的隧道后端没起**（机器关了 / cpolar 客户端挂了 / VIP 保留端口到期被释放），
  **客户端无解**。`~/.config/cpolar/tunnels.conf` **只托管 5090 与 a6000 两个账号**，
  4090 的隧道挂在第三个账号上 ⇒ `cpolar-ssh-update` 管不到它，也查不到它的状态。
  ⇒ 恢复要作者去 cpolar 控制台看那个账号的 `ssh` 隧道，或到机器本地重启 cpolar。
- ⚠️ **5090 是 cpolar 免费动态地址，host:port 会变**（症状：`Connection refused` /
  `Host key verification failed` / `kex_exchange_identification: Connection reset`）。
  **本地有 `cpolar-ssh-update` 命令可更新 `~/.ssh/config` 里的 5090 隧道地址**（作者 2026-07-28 提供）；
  换址后**先核对连上的是不是同一台机器**再操作：`whoami`（应为 `tongjiakai`）+ `nvidia-smi` 名称 +
  项目目录存在 + `git log -1`。4090 是 vip 固定域名，但同样会间歇性 reset ——
  **ssh 失败是工具失败，不得当成卡况或任务结论**。
- ⚠️ **5090 连不上 `huggingface.co`（超时），但 `hf-mirror.com` 可达（200）、pypi 可达**。
  拉底座模型必须带 `HF_ENDPOINT=https://hf-mirror.com`（2026-07-28 实测 roberta-base 走镜像成功）。
- 跨机传输实测 **~85 KB/s（未压缩）**，比先前记的 400KB/s 慢得多；JSON 类数据**务必加 `-z`**
  （`rsync -aPz --append-verify`，实测显著加速）。
- 项目 Python 见 §0；uv 在 4090 是 `/home/TJK/.local/bin/uv`、5090 是 `/home/tongjiakai/.local/bin/uv`
  （5090 的 `~/.local/bin` 已在非交互 PATH 首位，直接 `uv` 即可）。
- 非交互 SSH 里 `python`/`uv`/`jq`/`rg`/`tmux` 可能不在 PATH；用绝对路径或 `bash -lc`。
  5090 上**没有 `gcc`/`nvcc`**（`~/bin` 只有别的项目留的 `cc-sarge` 包装），需要编译扩展的包装不上——
  纯 wheel 装得上，这也是不用源码编译 torch 的实际约束之一。
- 选卡：4090 **card 3 故障**需 NVML shim（`nvmlshim/`，remote-only），card 0/2 常被别人占，优先 card 1；
  5090 只有一张卡（`CUDA_VISIBLE_DEVICES=0`），**被占就只能等或回 4090，没有换卡余地**。
  两台都要**每次启动前重新 `nvidia-smi` 原子核卡**（检查结果不隔启动复用）。
- 判活：首次加载约 1 分钟才占显存；**SSH 失败 ≠ 任务死亡**，三态 ALIVE / GONE / ssh 失败，
  只有成功 SSH 读到进程 GONE 才算结束。
- ⚠️ **`pgrep`/`pkill` 自匹配**：`pgrep -f "uv pip install"` 会匹配到**你自己这条命令的命令行**，
  写成 `until ! pgrep -f "uv pip install"; do sleep 10; done` 的等待循环会永远等自己、假装任务没结束；
  `pkill -f "<模式>"` 同理会杀掉自己的 SSH 会话。**一律用括号打断**：`pgrep -af '[u]v pip install'`。
  （2026-07-27 实测两次踩中：安装其实早已完成，循环空转了十几分钟。）
- 远端仓库外备份 `/data/TJK/ekg-backup-20260727/`（4090，历史 docs 残留等，不进 git）。

## 3. 同步协议

**两台服务器都是 git 仓库**（`main` 跟踪 `origin/main`），日常同步各一条：

```bash
ssh gpu-4090 'bash -lc "cd /data/TJK/ekg && git fetch origin && git reset --hard origin/main"'
ssh gpu-5090 'bash -lc "cd /mnt/aidata/tongjiakai/ekg && git fetch origin && git reset --hard origin/main"'
```

5090 的 `origin` 指向镜像 `https://gh-proxy.com/https://github.com/emmmdty/ekg.git`（它连不上
`github.com:443`，见 [`PIPELINE.md`](PIPELINE.md) §3）——命令写法不变，只是 URL 不同。

- 数据/产物/大文件**不在 git**，走 `scp`/`rsync` + 两端 `sha256sum` 核对。**两台服务器之间不能直连**，
  跨机搬运经本地中转，用 `rsync -aP --append-verify`（可续传；带 timeout 的 scp 会静默截断）。
- **禁 `rsync --delete` 与 `git clean -fdx`**（会删 `runs/`、`nvmlshim/`、`data/raw/` 等 remote-only 产物）。
- 目录改名或换路径后：venv 里 console script 的 shebang 与 editable `.pth` 都写死绝对路径，
  **必须修**（做法见 [`ENGINEERING_NOTES.md`](ENGINEERING_NOTES.md) 环境/工具链节）。

完整三端闭环见 [`PIPELINE.md`](PIPELINE.md)。

## 4. 启动纪律

**4090 的 GPU 使用无限制，有空就可以去用**（作者授权），无需逐次点头。
⚠️ **该授权不覆盖 5090**——5090 每次使用都要先问作者。两台都仍须：

- 本地三件套先全绿；选卡前 `nvidia-smi` 原子核卡；**不挤占他人正在跑的卡**
  （判据：`memory.used ≤ 2500` 且 `utilization ≤ 20`；4090 跳过 card 3，5090 只有 card 0）。
- 长任务用 `nohup` / `screen -dmS` + `python -u`，日志重定向 `logs/`，**不得用前台 SSH 承载长任务**。
- 报数如实：升降都报；ssh/工具失败不得伪装成被观察对象的结论。

## 5. v4 GPU 路线

| Phase | GPU | 当前可运行性 | 远端产物 |
|---|---|---|---|
| A 判别式关系抽取 | 重 | ✅ 已达标，checkpoint 在位 | `runs/relations/supervised_maven` + `pair_eval_FINAL.json` |
| B 一致性/修复/风控 | 轻 | ✅ 只差产 dump（见 §6）；修复/CRC 全在本地 CPU | `runs/relations/supervised_dump.jsonl` |
| C 规范节点 | 轻 | ⬜ 依赖 MAVEN-Arg loader/模型实现 | `runs/nodes/*.json` |
| D 事实性/净化 | 轻 | ⬜ MAVEN-FACT 数据就位，代码未实现 | `runs/factuality/*.json` |
| E 闭环/三图传播 | 重 | 🟡 SeDGPL 可复用；真实闭环依赖 A/B/C/D | `runs/cgep/*closedloop*.json` |
| H 多种子 | 重 | ⬜ 只在 A–F 主结果稳定后执行 | 各主表 seed 13/17/42 |

新 phase 的命令必须从实际 CLI `--help` 与配置生成，不能照抄旧命令。

## 6. 当前队首命令：Phase B 真实图 dump

卡空闲时——**4090**（`<card>` 优先 1、跳 3）：

```bash
cd /data/TJK/ekg
CUDA_VISIBLE_DEVICES=<card> HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  .venv/bin/python -u scripts/evaluate_relations.py \
  --config configs/relations/supervised_dump.yaml \
  --dump-predictions runs/relations/supervised_dump.jsonl \
  --output runs/relations/supervised_dump_metrics.json \
  > logs/phaseB_dump.log 2>&1
```

**5090**（单卡，须用户许可后再跑）——只有根路径和卡号不同：

```bash
cd /mnt/aidata/tongjiakai/ekg
CUDA_VISIBLE_DEVICES=0 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  .venv/bin/python -u scripts/evaluate_relations.py \
  --config configs/relations/supervised_dump.yaml \
  --dump-predictions runs/relations/supervised_dump.jsonl \
  --output runs/relations/supervised_dump_metrics.json \
  > logs/phaseB_dump.log 2>&1
```

两端跑前都要确认 `runs/relations/supervised_maven`（checkpoint，481M）与
`data/processed/maven_ere/valid.jsonl`（710 篇）在位——它们不在 git 里，换机器必须 scp/rsync 过去
（**两台服务器之间不能直连，经本地中转**）。

卡忙时可用服务器端待机脚本（等空卡**自动开跑**，288×5min≈24h 窗口）——
**当前状态：已修好并验证可用，但按作者指示处于停止态**（`status` 末行 `STOPPED-BY-USER`）。
它会在无人值守时启动 GPU 任务，**只在你确实想要无人值守跑的时候才起**：

```bash
ssh gpu-4090 'bash -lc "cd /data/TJK/ekg && nohup bash runs/phaseB_dump_wait.sh >/dev/null 2>&1 &"'
ssh gpu-4090 'tail -3 /data/TJK/ekg/runs/relations/phaseB_dump.status'   # 轮询进度
```

`status` 末行读法：`DONE rc=0 dump_lines=NNN` = 成功；`DONE rc≠0` = 读 `logs/phaseB_dump.log`；
`TIMEOUT` / `STOPPED-BY-USER` / 进程已死 = 没抢到卡，按需重起。

⚠️ **停它要按三态判活**：脚本卡在 `sleep 300`，SIGTERM 被 bash 挂起到 sleep 返回才生效，kill 后仍会
再写 1–2 条 `WAIT`。判死的决定性依据是 **`status` 文件是否还在按 5min 增长**，不是单次 `pgrep`。

## 7. 仍可复现的 Ch4 基线

```bash
cd /data/TJK/ekg
CUDA_VISIBLE_DEVICES=<空卡> HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  .venv/bin/python -u scripts/evaluate_cgep.py \
  --dataset maven --predictor sedgpl --model-path <roberta-base-path> --epochs 10 \
  --output runs/cgep/maven_sedgpl.json
```

单折 10ep ≈ 2.5h。仅复现既有 Ch4 基线，**不代表 Phase E 闭环完成**。

## 8. 监控与结束判定

- 进程：用不会匹配探针自身的模式，如 `pgrep -af '[e]valuate_relations'`。
- 显存：`nvidia-smi`；**进程与显存同时符合预期**才判 ALIVE。
- 日志：`tail` 任务自己的日志，不用 SSH 连通性推断训练状态。
- 结束：成功 SSH 确认进程 GONE → 查退出码与产物完整性；**文件存在不等于训练成功**。
- 回传：指标 JSON、必要日志、manifest 定向 scp；checkpoint 只在明确需要时传。

## checkpoint 留存策略（2026-08-06 作者改）

**训在哪就留在哪，不强制回传；要跨机搬运先问用户。**
原策略是「4090 是主力，所有 checkpoint 必须回传 4090」（2026-07-30 定）。2026-08-06 4090 的
cpolar 隧道后端挂掉、整台机器够不着，**那条规则反而把工作卡死**（新档没处放、旧档取不出）
⇒ 改为按需搬运。

**搬运代价是实测的**：5090 走免费版 cpolar，实测 **130 KB/s**；4090 是 vip 隧道，约 450 KB/s。
一个 roberta-base 档（476 MB）两跳（5090 → 本地 → 4090）**约 70 分钟**——这就是要先问的原因。

**但不搬的代价也是实测的**：Phase C 的共指 checkpoint 因为只在 5090，直接导致 2026-07-30 的
CodaLab 提交先跑了一版词形兜底档。所以放弃回传不等于放弃记账——
**档在哪台必须记进 `docs/results/` 的对应 PHASE 文件**，别让下一个窗口去猜。

| checkpoint | 在哪 | 说明 |
|---|---|---|
| `runs/relations/supervised_maven`（Phase A 系统档） | 4090 + 5090 | 现役对照档 |
| `runs/factuality/struct_best`·`supervised_6ep`（Phase D） | 4090 | 4090 恢复前取不到 |
| `runs/cgep/ch4_sedgpl.pt`（Phase E，1.5G） | 4090 | 同上 |
| `runs/nodes/coref_supervised_6ep`（Phase C 系统档） | 4090 + 5090 | 2026-07-30 已回传，sha256 三端一致 |
| `runs/nodes/detector_supervised_6ep`（Phase C 检测头） | 5090 | 不再要求回传 |
| `runs/relations/official_arch_6ep`（A2 新架构·官方配方） | 5090 | 2026-08-06 训；欠拟合平台，无分辨力 |
| `runs/relations/neg30_arch_6ep`（A2 新架构·现役配方） | 5090 | 2026-08-06 训；架构证伪的对照档，causal 24.06 |
| `runs/relations/neg30_window_6ep`（**文档窗口编码**） | 5090 | 2026-08-07 训；causal 26.95 / temporal 28.40 |
| `runs/relations/neg30_window_dist_6ep`（窗口+距离流） | 5090 | 2026-08-07 训；causal **27.60** / temporal 28.59；subevent −0.71 |
| `runs/relations/window_dist_20ep_best`（+20ep+best 选择） | 5090 | 2026-08-07 训；held-out dev 200 篇选最佳 epoch |
| `coref_large`·`coref_longformer`·`coref_*_diverged_*`（换底座失败档 / 发散档） | 5090 | **不搬**：数字已在 `docs/results/PHASE_C.md`，权重无复现价值 |

⚠️ 两跳都用 `rsync -aP --append-verify`（可断点续传），**别用带 timeout 的 scp**——会静默截断出半个文件。
落地后核 `sha256` 或至少核字节数。
