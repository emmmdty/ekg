# PHASE C · 交接（Ch1 证据感知规范事件节点）

> **给新会话**：`/clear` 后只读本文件 + 自动载入的 `CLAUDE.md` + [`../SPEC.md`](../SPEC.md) 即可执行。
> 原始 phase 契约见 [`PHASE_C_ch1_canonical_nodes.md`](PHASE_C_ch1_canonical_nodes.md)（Goal/Steps 的权威）；
> 本文件补充**上一阶段的真实结论、环境现状、以及开工前必须先确认的方向决策**。
> 交接时间 2026-07-28，仓库 HEAD `d429c1a`。

---

## 0. 开工前：先跟作者确认方向（**不要直接开跑**）

Phase B 已跑通并**触发止损**（详见 §2），这改变了后续优先级。开工第一件事是把下面这个选择摆给作者：

| 选项 | 内容 | 依据 |
|---|---|---|
| **A. 进 Phase C（本文件，推荐）** | 按关键路径 A→B→**C**→D→E 推进 Ch1 规范节点 | C 是 E（Ch4 headline）的硬依赖，且**当前最大空洞正是节点身份**——Ch2 抽取器在 valid 上 coref `n_pred=0`、该族 FNR=**1.000**（2,887 条 gold 全丢）。Ch1 正是解这一层 |
| B. 回头抬 Phase A 召回 | 继续调判别式抽取器的召回/precision | 能同时松开两个约束（R2 增益、准入可行域）；但 Phase A **已达标**（causal F1 .250 ≥ 目标下沿），继续调优收益不确定，且不补 C/D 的缺口 |
| C. 先重定位 Ch4 headline | 因 B 的负结果，重新界定「闭环修复」的主张 | 风险真实（见 §2 ④），但**无论如何都要先有 Ch1/Ch3 才能做 E**，可与 C 并行推进而非阻塞 |

**推荐 A，并把 C 记为待决问题**（不阻塞）。理由：E 依赖 C·D 齐；B 已止损、不该继续纠缠修复策略。

---

## 1. 现状快照（前置阶段的真实数字）

### Phase A — ✅ 已达标（2026-07-24）

判别式 `supervised` 抽取器，配置 `neg30 · α=0.5 · 6 epochs`，阈值 0.7：
**causal F1 .250 / subevent .213 / temporal .338**，召回 0.4%→67.5%，`hallucinated=0`。
交付 checkpoint = `runs/relations/supervised_maven`（481M，两台服务器均在位，**不在 git**）。

⚠️ **已知空洞**：该抽取器**不预测 coreference**（valid 上 `n_pred=0`）——这正是 Phase C 要补的层。

### Phase B — 🟡 跑通但**止损触发**（2026-07-28，首次真实 predicted 图闭环）

dump 在 **gpu-5090** 产出：710 篇 / **242,869 条原始边**（342/篇）；离线分析 497 篇 held-out test，α=0.2、cal_ratio 0.3。
产物 `runs/relations/{supervised_dump.jsonl, consistency_repair_supervised.json}`（**不在 git**，需要就重跑或找作者要）。

| 档 | causal_cyclic_scc | temporal_cyclic_scc | temporal_cyclic_edges | closure_gap | R1 可达率 | R2 query f1 |
|---|---|---|---|---|---|---|
| raw（identity） | 752 | 614 | 36,523 | 83.78 | **0.7310** | **0.0622** |
| repaired | **0** | **0** | **0** | **0** | 0.7294 | 0.0620 |
| repaired + 准入（τ=0） | 0 | 0 | 0 | 0 | 0.7294 | 0.0620 |

① ✅ **结构违反清零**（这一档确凿）；② ❌ **R1/R2 无增益、双双微降**——**合成 dump 上 R2 0→1.0 的增益在真实图
上没有复现**；机制可见：修复以补闭包边为主（added 8,770 > dropped 8,119），`n_pred` 381→386 而 `tp` 恒为 51，
补的边没命中 gold query，只稀释 precision。③ ⚠️ **止损已触发**：Ch2 收缩为「可追溯修复清零结构违反」+ 误差传播，
**不得声称修复提升下游可重建性，不得换指标掩盖**。④ ⚠️ **准入 τ 校准出 0（退化为全收）**，根因不是 CRC 实现而是
**可行域为空**：抽取器边际召回 .5258 ⇒ FNR 下界 .4742，**α<.474 不可满足**——要报有意义的 τ，得放宽 α 到 >.48
或先抬召回。分族 FNR：coref **1.000** / temporal .4469 / causal .5616 / subevent .4065；doc-macro .4925。

**新会话注意**：引用 Phase B 时**必须同时报清零与微降两面**，不要只挑好的说。

---

## 2. 环境（2026-07-28 已就绪，两端统一）

| | **`gpu-4090`（主）** | **`gpu-5090`（备）** |
|---|---|---|
| 何时用 | 默认 | 仅 4090 不可用，**且须作者逐次许可** |
| 远端根 | `/data/TJK/ekg` | `/mnt/aidata/tongjiakai/ekg` |
| 卡 | 4×RTX 4090（card 3 故障，优先 card 1） | 单卡 RTX 5090 32G（`CUDA_VISIBLE_DEVICES=0`） |
| 验证基线 | `254 passed / 1 skipped` | `252 passed / 3 skipped`（多 2 个是 ESC 数据未传，**非回归**；两端 total 均 255） |

- **两端栈一致**：CPython 3.10.20 + **torch 2.8.0+cu128** + transformers 4.53.3 + peft 0.15.2。
  本地无 torch：`243 passed / 12 skipped`。**三处计数不同都不是回归**，别拿来判断退化。
- ⛔ **服务器禁 `uv run` / `uv sync`**（会按 extras 卸包）；一律 `.venv/bin/python`，装包用 `uv pip install <包>`。
- ⚠️ **5090 是 cpolar 免费动态地址，host:port 会变**（实测 `29.tcp.cpolar.top:11517` → `1.tcp.cpolar.cn:22282`）。
  报 `Connection refused` / `Host key verification failed` 时先跟作者要新地址，接上后**先核对是不是同一台机器**
  （`whoami` + `nvidia-smi` 名称 + 项目目录 + `git log -1`）再操作。
- 5090 **连不上 `github.com:443`**，其 remote 走镜像 `https://gh-proxy.com/https://github.com/emmmdty/ekg.git`。
  ⚠️ 仓库已迁 **`emmmdty/ekg`**，旧的 `emmmdty/dee-fin` **已废弃**。
- **两台服务器之间不能直连**，跨机大文件经本地中转，用 `rsync -aP --append-verify`（带 timeout 的 scp 会静默截断）。

---

## 3. Goal（要的结果）

照 [`PHASE_C_ch1_canonical_nodes.md`](PHASE_C_ch1_canonical_nodes.md) 的 Goal：构建**去重、可溯源、身份统一**的
canonical event nodes —— 事件检测 → 相似事件难例判别 → 不确定性感知规范化聚类 → 簇级证据/置信聚合 → 挂 MAVEN-Arg 论元。
产出的 `node_confidence` 必须是**下游可消费的校准置信**（喂 Ch4 误差预算），这是与普通事件共指的关键差异。

**本阶段额外要回答的一个问题**（来自 Phase B 的空洞）：Ch1 产出的 canonical nodes 能否把 coref 一族的
FNR 从 **1.000** 拉下来——这是 Ch1 对下游最直接、最可量化的贡献，值得单独报一个数。

---

## 4. Steps

执行步骤以 [`PHASE_C_ch1_canonical_nodes.md`](PHASE_C_ch1_canonical_nodes.md) §执行内容为准（4 步，TDD）。
开工前先确认数据：

```bash
ls data/raw/maven_arg/ data/processed/maven_ere/       # MAVEN-Arg 原始 + ERE processed
uv run pytest && uv run ruff check src tests scripts && uv run ekg-smoke   # 本地基线 243 passed
```

⚠️ `DATASET_SURVEY.md` 记载 MAVEN-Arg 已有 processed manifest，但**开工时要自己核实文件真在**，
别假设——Phase A 就吃过「loader 容忍失配、训练侧才 fail-fast」的亏。

GPU 需求：**轻**（检测可复用小模型 fine-tune）。4090 空卡直接跑；要用 5090 先问作者。

---

## 5. Constraints / 红线

- `EventNode` schema **零新增字段**，扩展一律走 `metadata`；`tests/core/test_propagation.py` 是测试锁。
- 包/函数名**不得含 `ch1/ch2/ch3`** 等章节编号；新组件走 registry + lazy import；GPU 组件配 CPU 缓存回放。
- 代码走 git、**数据/产物/大文件走 scp**（`runs/` 已在 `.gitignore`）；**禁 `rsync --delete` / 远端 `git clean -fdx`**。
- **报数如实**：降就说降；ssh/工具失败不得伪装成结论。**专利 / 论文写作不在计划范围。**
- 提交/推送**仅在作者明确要求时**（本仓库惯例）。
- coref 主干是**复现、不主张新颖**；创新点在难例判别 + 下游可消费校准置信 + 证据冲突消解。

---

## 6. Done when（验收）

- [ ] 检测 micro-F1 ~60+；coref MUC ~86 可比区间；**相似事件误合并率显著↓**；`node_confidence` 报出 ECE。
- [ ] 额外：报出 canonical nodes 对 **coref 族 FNR（当前 1.000）** 的改善幅度。
- [ ] `uv run pytest && uv run ruff check src tests scripts && uv run ekg-smoke` 全绿（**只增不改**）。
- [ ] 结果落 `runs/ch1_nodes_*.json` + 如实回填 `docs/TODO.md`（升降都报）。

---

## 7. 已知风险与止损

- **Ch1 本身**（原契约）：evidence 对齐评测难设计 → 优先可自动计算指标 + 小规模人工核验；
  退「canonical table + 难例判别」仍成章。
- **Ch4 headline 的连带风险（待决，不阻塞本阶段）**：Phase B 证明「修复提升下游可重建性」在真实图上不成立，
  而 SPEC 的 headline 是 Ch4 下游门控闭环修复。**做 E 之前必须跟作者重新界定这个主张**，
  可选方向：退为「一致性重排 / 受控误差传播分析」，或改用 R1（可达率 .7310，CS-CRP 的桥，目前健康）
  而非 R2 作为下游度量。**不要在 E 里换指标掩盖 B 的负结果。**
- **别重蹈的两个坑**（`ENGINEERING_NOTES.md` 有详录）：① 稠密图上**不要枚举简单环**（已改 SCC 度量，
  有复杂度回归哨兵）；② 换 torch 必须连 torchvision/torchaudio 一起换，否则崩溃会伪装成
  `SKIPPED: needs torch`——**判据看 pytest 计数，不是 `import torch` 成功**。
