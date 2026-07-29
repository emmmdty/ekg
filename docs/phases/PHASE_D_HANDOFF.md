# PHASE D · 交接（Ch3 事实性检测与图净化）

> **给新会话**：`/clear` 后只读本文件 + 自动载入的 `CLAUDE.md` + [`../SPEC.md`](../SPEC.md) 即可执行。
> 原始 phase 契约见 [`PHASE_D_ch3_factuality_purification.md`](PHASE_D_ch3_factuality_purification.md)（Goal/Steps 的权威）；
> 本文件补充**上一阶段的真实结论、实测环境（与 runbook 有出入的地方）、以及开工要先核的数据事实**。
> 交接时间 2026-07-28，仓库 HEAD `0411747`。

---

## 0. 方向已定：进 Phase D（不是 LLM 基线）

作者 2026-07-28 问过「先做 LLM 基线还是转 Phase D」。**结论是 Phase D**，理由按分量：

1. 项目自己的规矩：`TODO.md` 写着「多种子和进一步调 M1/M2 放到 Phase H；**主闭环未通前不扩张实验面**」。
   LLM 基线正是实验面扩张。
2. **基线属于 Phase H**：基线是方法冻结后跑一次的对照。现在只为 Ch1 跑，等 Ch3/Ch4 协议一变还得重跑。
3. **competitiveness 的疑虑已答掉大半**：文献侧 CRAC 2025 shared task（《Can LLMs Dethrone Traditional
   Approaches?》）结论是编码器仍领先、事件共指上 LLM 显著更差；我们这侧已核实**贴着官方基线**（见 §1）。
4. **D 是一整章缺口且在关键路径上**：E（Ch4 headline）依赖 A·B·C·D 齐。
5. LLM 基线放到 Ch3/Ch4 时做**反而更值** —— 事实性与下游推理才是 LLM 真有可能赢的地方。

⚠️ **另一个仍挂着的待决问题（不阻塞 D，但做 E 之前绕不过）**：Phase B 证明「修复提升下游可重建性」
在真实图上不成立，而 SPEC 的 headline 是 Ch4 下游门控闭环修复。**做 E 之前必须跟作者重新界定这个主张**，
不得在 E 里换指标掩盖 B 的负结果。

> ✅ **2026-07-29 更新：本条已解决。** 作者已拍板把 Ch4 headline 重定位为「构建误差向下游的传播、归因与预算」，修复降为**被测量的干预**；依据是实测的门控天花板 ≈0.24%。权威表述见 `docs/SPEC.md` §1 与重写后的 `PHASE_E_ch4_closedloop_propagation.md`。


---

## 1. 现状快照（前置阶段的真实数字）

### Phase A — ✅ 达标（2026-07-24）
判别式 `supervised` 抽取器（`neg30 · α=0.5 · 6 epochs`，阈值 0.7）：
**causal F1 .250 / subevent .213 / temporal .338**，召回 0.4%→67.5%，`hallucinated=0`。
交付 checkpoint `runs/relations/supervised_maven`（481M，两台服务器均在位，**不在 git**）。

### Phase B — 🟡 跑通但**止损触发**（2026-07-28）
710 篇 / 242,869 条原始边；497 篇 held-out test，α=0.2、cal_ratio 0.3。
**结构违反全部清零**（causal/temporal 强连通分量 752/614 → 0，closure_gap 83.78 → 0）✅；
**但 ECG 可重建率无增益、双双微降**（R1 .7310→.7294、R2 f1 .0622→.0620）❌ → **止损已触发**：
Ch2 收缩为「可追溯修复清零结构违反」+ 误差传播，**不得声称修复提升下游可重建性**。
准入 τ 校准出 0（可行域为空：边际召回 .5258 ⇒ FNR 下界 .4742，α<.474 不可满足）。

### Phase C — 🟢 主结果已出、基本达标（2026-07-28）

新包 `src/ekg/nodes/`（detection / coref / canonical / metrics / encoding）+ `relations/data/maven_arg.py`
+ 新核心原语 `core/calibration/probability.py`。系统档 = **roberta-base 6 epochs**，
checkpoint 在 **5090** `runs/nodes/coref_supervised_6ep`。

- ✅ **难例误合并率 .767 → .116**（n=3077 难例对）
- ✅ **coref 族 FNR 1.000 → .220**，precision .414 → .781（两面都涨）
  —— 原来的 1.000 是**结构性缺失**：`relations/extractor/supervised.py` 的 `FAMILY_SUBTYPES`
  只有 temporal/causal/subevent，抽取器**根本没有 coreference 头**
- ✅ `node_confidence` ECE .0382 → **.0056**（弃权带越宽原始置信越偏，校准才有增益；band 0 档 raw 本就 .0062）
- ✅ **coref MUC 79.6 vs 官方 RoBERTa-base 基线 81.4，差 −1.8** —— B³/CEAFe/precision 全平手，缺口只在 recall
- ❌ 检测器只比纯记忆 lexicon 高 1.7（.7048 vs .6875）→ **已降级为打底，不作为卖点**

**★ 三条必须继承的方法论教训（Phase C 花了整轮 GPU 才买到）**：

1. **对标数字必须回到一手表格核**。原验收线「coref MUC ~86」是**错的** —— MAVEN-ERE 原论文
   （arXiv 2211.07342）Table 7 的官方 RoBERTa-base 基线是 **81.4（单任务）/ 82.1（+joint）**；
   86.1 是 2024 年一个联合图模型的 SOTA。照错线走把「基本达标」误判成「差很远」，
   **直接诱发了两轮无效的换底座实验**。
2. **换底座三次全败，别再试**：base 3ep .789 → base 6ep **.806（系统档）**；
   Longformer-4096（长上下文）**.781（−2.5）**；roberta-large（容量）**.778（−2.8）**。
   已贴着 base 基线天花板，再往上要靠**四关系联合建模**（论文自测 +joint 只给 +0.7）。
3. **比较必须锚在同一操作点**。阈值会挪动模型的置信标度，直接比阈值等于拿阈值挪动冒充增益；
   Phase C 一律按**同一难例误合并率**对齐后再比。

---

## 2. 环境（2026-07-28 实测，**有两处与 runbook 记载不符**）

### GPU 选择：**推荐 4090 的 card 2**

决定性因素是**数据在哪**：

| | **`gpu-4090`（推荐）** | `gpu-5090` |
|---|---|---|
| 远端根 | `/data/TJK/ekg` | `/mnt/aidata/tongjiakai/ekg` |
| **MAVEN-FACT** | ✅ `data/processed/maven_fact/` 已就位 | ❌ **没有**，需从本地传 |
| 空闲卡 | **card 2**（card 0/1 被他人占 ~100%，**card 3 故障需 NVML shim**） | 单卡 32GB，空闲 |
| 授权 | ✅ 标准授权，训练/推理**无需逐次点头** | ⚠️ **须逐次问作者** |
| ModelScope | ✅ 200 | ✅ 200 |
| huggingface.co | ❌ 不通（cache 也是空的） | ❌ 不通（`hf-mirror.com` 通） |
| github.com | ⚠️ **本次实测不通**（见下） | ❌ 不通，remote 走 gh-proxy 镜像 |

⚠️ **两处与 `GPU_RUNBOOK.md` 记载不符，开工先自己复测一遍**：

1. **4090 的 GitHub 直连本次不通**：`curl https://github.com` 空返回，`git fetch origin` 没拉到新 commit
   （`origin/main` 仍停在 `d429c1a`，而真实 HEAD 是 `0411747`）。若仍不通，把 remote 改成镜像
   `https://gh-proxy.com/https://github.com/emmmdty/ekg.git`（5090 一直这么用）。
2. **4090 的 HF cache 是空的**（`~/.cache/huggingface/hub` 无内容）→ 底座模型**必须从 ModelScope 下**。

### 模型下载

- **一律走 ModelScope**（作者 2026-07-28 指定，比 HF 镜像快）：`pip install modelscope` 后
  `modelscope download --model <id> --local_dir models/<模型名>`，或 `snapshot_download`。
- **模型放项目目录下的 `models/<模型名>/`**（作者 2026-07-28 指定，针对 5090；4090 沿用同一约定
  以免两端不一致）。该目录**两端当前都还不存在**，需新建；`models/` **已在 `.gitignore` 第 27 行**，
  权重不会误入 git。
- 训练脚本的 `--model` 直接吃本地路径，不需要改代码。

### 其他

- 两端 Python **统一**：`.venv/bin/python` = CPython 3.10.20 + **torch 2.8.0+cu128** + transformers 4.53.3。
- ⛔ **服务器上不要跑 `uv run` / `uv sync`**（会按 extras 卸包）；一律 `.venv/bin/python`。
- 本地无 torch 基线：**301 passed / 12 skipped**、ruff 0、`ekg-smoke` OK。**三端计数不同都不是回归。**
- **ssh 失败 ≠ 任务死亡**：三态判活（ALIVE / GONE / ssh 失败），只有成功 ssh 读到进程 GONE 才算结束。
  5090 是 cpolar 免费动态地址，换址用本地 `cpolar-ssh-update`，接上后**先核对是不是同一台机器**
  （`whoami` + `nvidia-smi` + 项目目录 + `git log -1`）。
- **后台发射的正确姿势**（Phase C 踩过）：`A && B && C > log 2>&1 &` 会把**整条链**后台化、`cd` 落在子 shell 里。
  用 `setsid nohup env CUDA_VISIBLE_DEVICES=N .venv/bin/python -u <script> ... > logs/x.log 2>&1 < /dev/null &`。
- **`pgrep -f` 会自匹配**你自己的命令行；判活优先看 `nvidia-smi` 的 compute-apps 或 checkpoint 文件是否落地。
- 大文件跨机传输实测 **~85KB/s（未压缩）**，JSON 类务必 `rsync -aPz --append-verify`；**禁 `rsync --delete`
  与远端 `git clean -fdx`**（会删 `runs/`）。

---

## 3. Goal（要的结果）

照 [`PHASE_D_ch3_factuality_purification.md`](PHASE_D_ch3_factuality_purification.md)：

① **结构感知事实性检测打底** —— MAVEN-FACT 5 类 macro-F1 **打平/超 47.6**；
② **预测图鲁棒性** —— 量化在 Phase A/B 的**预测图（有错）**上的掉点（MAVEN-FACT 原文全用 gold 输入）；
③ **事实性驱动图净化** —— 剔除/降权非事实事件及其边，接下游后继预测（Phase E）。

**novelty 落点**：不主张「用结构检测事实性」新（MAVEN-FACT 已证），新在 **预测图鲁棒性 + 净化下游**。

---

## 4. Steps（4 步，TDD）

执行步骤以原契约 §执行内容为准。**开工前先核数据**：

```bash
ls data/processed/maven_fact/            # 4090 上已确认有 manifest/train/valid/*_smoke
uv run pytest && uv run ruff check src tests scripts && uv run ekg-smoke   # 本地基线 301 passed
```

### 已核实的 MAVEN-FACT 事实（2026-07-28 在 4090 上实测，可直接用）

- valid：**710 篇 / 17,780 个 event mention**（与 MAVEN-ERE 的 mention 数**完全一致**，doc id 同一批）。
- 标签在 `events[].mention[].factuality`，5 类分布**极度不平衡**：

  | CT+ | PS+ | CT− | PS− | Uu |
  |---|---|---|---|---|
  | 16,868（**94.9%**） | 456 | 384 | 52 | 20 |

- **只有 843 个 mention 带 `evidence_word`**（4.7%）—— evidence span F1 的分母就这么大，别按全量算。
- 记录字段：`id / title / tokens / sentences / events / TIMEX / temporal_relations / subevent_relations /
  has_arguments / document / causal_relation`。
- ⚠️ **offset 口径要自己核**：mention 的 `offset` 看起来是 **sent_id + token 偏移**（ERE 约定），
  但记录里**同时**有 `document` 字段（Arg 约定是字符偏移）。**开工第一件事就是核 `evidence_offset`
  和 mention `offset` 各自落在哪个坐标系**，别假设 —— Phase A 和 Phase C 都在 offset 上吃过亏
  （ERE loader 的 `find` 是容错的，失配会静默记成 span(0,0)；MAVEN-Arg 的字符 offset 则是 0 失配）。

### ★ 门槛判据：**必须报 macro-F1，不能报 accuracy**

全部预测 CT+ 的**平凡基线**就能拿到 **accuracy .9487**，但 **macro-F1 只有 .1947**。
所以：**accuracy 在这个任务上毫无信息量**；目标 47.6 是 macro-F1，报数一律 macro-F1 + 每类 P/R/F1。

### 类不平衡怎么调（直接继承 Phase A 的实测结论，别重新试错）

- 逆频加权 CE 的 **α 曲线是倒 U 形，最优在 0.25–0.5**；α=1.0（纯逆频）会教出「宁滥勿缺」。
- **负采样 + 逆频加权是双重补偿**，叠加会崩掉 precision。
- **per-family / per-class 更高的 α 反而更差**（Phase A 实测 causal 从 .234 掉到 .205）。
- **训练轮数是决定性变量**：Phase A 3→6 epochs 把 causal F1 从 .234 推到 .250（loss 仍在降＝欠拟合）。

### 复用清单（不要重写）

- `relations/data/maven_ere.py`：加载器写法的范本（token offset + sent_id 路线）。
- `relations/data/maven_arg.py`：**字符 offset + fail-fast 校验**的范本，含 entity 引用解析。
- `nodes/encoding.py`：`locate_span_token`（纯 Python、CPU 可测、fail-fast）+ `encode_spans`
  （滑窗 / 长上下文自适应 + `global_attention_mask` 能力检查 + 形状哨兵）。
- `nodes/detection.py`：**多类别 + 极端不平衡** 的检测器骨架（registry + torch-lazy + 词表记忆基线），
  Ch3 的事实性检测器结构上就是它的近亲，**照抄骨架**。
- `core/calibration/probability.py`：isotonic 概率校准 + `reliability_curve`（held-out 拟合）。
- `core/eval/relation.py::PRF`、`core/eval/faithfulness.py::expected_calibration_error`。
- `scripts/train_event_detector.py` / `scripts/build_canonical_nodes.py` / `scripts/sweep_canonical_nodes.py`：
  训练 / 端到端报告 / 操作点扫描（带打分缓存）的三件套范式。

### 训练超参的已知坑

- **encoder 和 head 用同一个 lr**。Phase C 给线性头单独 lr=1e-3 **发散**（loss .428→.646，
  高于常数先验最优）；改回与 `train_supervised_relations.py` 一致的单一 **2e-5** 才收敛。
- **roberta-large 在 lr 2e-5 下会训练崩溃**（epoch 2 塌到 .62 后五个 epoch 不动），必须 **1e-5**。
  崩掉的跑**不能当成「large 没用」的结论** —— Phase C 差点犯这个错。

**GPU 需求**：轻（小模型 fine-tune）。4090 card 2 直接跑。

---

## 5. Constraints / 红线

- `EventNode` schema **零新增字段**，扩展一律走 `metadata`；`tests/core/test_propagation.py` 是测试锁。
- 包/函数名**不得含 `ch1/ch2/ch3`** 等章节编号；新组件走 registry + lazy import；GPU 组件配 CPU 缓存回放。
- 代码走 git、**数据/产物/大文件走 scp**（`models/`、`runs/`、`logs/` 均已在 `.gitignore`）。
- **报数如实**：降就说降；**ssh/工具失败不得伪装成结论**；训练崩溃的跑必须作废并留证，不得当结果用。
- **明说打底检测为复现**，novelty 在鲁棒性 + 净化下游；投稿前做新颖性扫。
- 提交/推送**仅在作者明确要求时**。**专利 / 论文写作不在计划范围。**
- 开发和选模型只用 **train**；本地最终报告用 **valid**（官方 test 不公开）。

---

## 6. Done when（验收）

- [ ] 5 类 **macro-F1 ≥ 47.6**（打平/超，如实报；同时给每类 P/R/F1）；evidence span F1 报出
      （注意分母只有 843 个带 evidence 的 mention）。
- [ ] **gold-input vs predicted-input 掉点量化**（用 Phase A/B 的预测图；这是本章 novelty 的一半）。
- [ ] 净化前后**图质量变化** + 下游（接 E）增益报出。
- [ ] `uv run pytest && uv run ruff check src tests scripts && uv run ekg-smoke` 全绿（**只增不改**）。
- [ ] 结果落 `runs/factuality_*.json` + 如实回填 `docs/TODO.md`（升降都报）。

---

## 7. 已知风险与止损

- **净化收益小** → 退「事实性检测 + 预测图鲁棒性分析」，仍成独立章（原契约止损口径）。
- **PS−(52) / Uu(20) 两类样本太少**：macro-F1 会被这两类的方差主导。**先报单次结果，
  但结论要标注方差风险**；真要下强结论得多种子（Phase H）。
- **Ch4 headline 待重定位**（见 §0）：不阻塞 D，但做 E 之前必须先跟作者拍板。
- **别重蹈的坑**：① 稠密图上不要枚举简单环（已改 SCC 度量，有复杂度回归哨兵）；
  ② 换 torch 必须连 torchvision/torchaudio 一起换，判据看 pytest 计数而非 `import torch` 成功；
  ③ 对标数字先核一手表格再定验收线（Phase C 的教训，见 §1）。
