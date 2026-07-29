# PHASE E · 交接（Ch4 构建误差的传播、归因与预算）

> **给新会话**：`/clear` 后只读本文件 + 自动载入的 `CLAUDE.md` + [`../SPEC.md`](../SPEC.md) 即可执行。
> 原始 phase 契约见 [`PHASE_E_ch4_closedloop_propagation.md`](PHASE_E_ch4_closedloop_propagation.md)
> （Goal/Steps 的权威，**已于 2026-07-29 整体重写**）；本文件补充上一阶段的真实结论、
> 实测环境、以及开工前必须知道的技术决策。
> 交接时间 2026-07-29，仓库 HEAD `ae44bca`。

---

## 0. ⚠️ 先读：headline 刚被重定位，**不要照旧执行**

作者 2026-07-29 拍板：**Ch4 headline 从「下游门控闭环修复」改为「构建误差向下游的传播、归因与预算」**。
修复**保留**（仍是 Ch2 交付物，仍能把 causal SCC 661→0），但身份从「headline 方法」变为
**「被精确测量、可归因的干预」**。

**依据是我们自己的实测，不是设想调整**：

1. Phase B 真实图上 repaired 使 ECG 可重建率**微降**（R1 .7310→.7294、R2 f1 .0622→.0620）。
2. 2026-07-28 归因实验：修复的 **1.5 万次编辑中约 1.4 万次（temporal 相关）对下游按构造零影响**
   —— ECG 重建只读 **causal+subevent** 拓扑，与 temporal 闭包**正交**；真正动下游的只有
   causal 环破除的 **858 条边**，代价 **R1 掉 3/1260（0.24%）**、收益 R2 tp +1；
   **不破 causal 环时下游与 raw 逐位相同**。
   ⇒ **门控天花板实测 ≈0.24%**，撑不起 headline。
3. 「仅在下游改善时接受编辑」的一般命题已被 **Kintsugi(2605.09487)** / DeepRefine / CauScientist 占先。

**⛔ 三条禁令**：① 不得复活 `repaired > predicted` 作为验收线（已作废）；
② 不得换指标把负结果重新包装成正面主张；③ 不得用金标 MRR 直接当门控信号（见 §5）。

---

## 1. 现状快照（A/B/C/D 的真实数字，升降如实）

| 阶段 | 状态 | 关键数字 |
|---|---|---|
| **A** Ch2 抽取 | ✅ 达标 | causal F1 **.250** / subevent .213 / temporal .338；召回 .4%→67.5%；`hallucinated=0`。checkpoint `runs/relations/supervised_maven`（4090 在位） |
| **B** 一致性修复 | 🟡 止损触发 | 结构违反**清零**（causal/temporal SCC 752/614→0，closure_gap 83.78→0）✅；但 R1/R2 **双双微降** ❌。准入 τ 校准出 0（召回 .5258 ⇒ FNR 下界 .4742，α<.474 不可达） |
| **C** Ch1 节点 | 🟢 基本达标 | coref **MUC 79.6 vs 官方 RoBERTa-base 基线 81.4**（−1.8）；难例误合并 .767→**.116**；ECE .0382→**.0056**。换底座三次全败（长上下文 −2.5、大容量 −2.8）——**别再试** |
| **D** Ch3 事实性 | 🟡 检测达标/净化止损 | valid macro-F1 **.4823**（平凡 .1947 / lexicon .2233 / 官方 DMBERT 47.6@**test**）；evidence macro(3类) **.6144**；**预测图掉点 ±.0001**（8/17,780 标签变）；**净化不如度数匹配随机剔除**（6 项中 5 项）❌ |

**★ 贯穿 A–D 的一条结论（Ch4 要解释的现象）**：**结构一致性指标与「哪些节点/边该被移除」不对齐** ——
净化按语义正确地删了 CT− 却减不了环；修复按结构正确地破了环却换不来下游。
且 **图侧干预在 SeDGPL 上普遍只有噪声级效应**：M1 ΔMRR +0.005、M2 −0.0015/+0.0009、修复归因 −0.24%，
三次同量级。**这是要被解释的现象，不是要被新机制撞开的墙。**

**SeDGPL 自跑基线**（Ch4 主表挂它）：CGEP-MAVEN 单折 **MRR 0.1836 / strict 0.1265**，n=1908，
单折 10ep ≈ **2.5h**。

---

## 2. 环境（2026-07-28/29 实测）

### GPU
- **4090（主，标准授权无需逐次点头）**：远端根 `/data/TJK/ekg`。⚠️ **card 2 已不再空闲**（Phase D 期间
  被他人占 ~7GB），**开工必须重新 `nvidia-smi` 核卡**，别照抄 Phase D 的结论。card 3 故障需 NVML shim。
- **5090（备）**：`/mnt/aidata/tongjiakai/ekg`，单卡 32GB，**须逐次问作者**；cpolar 免费动态地址会变。
- Phase E 是**重 GPU**（SeDGPL 训练 2.5h/折），排队要提前算。

### 已解决的坑（不用再踩）
- **4090 的 GitHub 直连不通** → remote **已永久改为镜像** `https://gh-proxy.com/https://github.com/emmmdty/ekg.git`，
  现在 `git fetch && git reset --hard origin/main` 直接可用。
- **底座模型在 `/data/TJK/models/`**（4090 的约定，非项目内 `models/`）。roberta-base 已下好并验证可加载。
  ⚠️ `modelscope` **包未装**，用 HTTP 直链下载：
  `curl -sL -o <file> "https://www.modelscope.cn/api/v1/models/<id>/repo?Revision=master&FilePath=<file>"`
  （避免 pip 动环境）。5090 的约定是项目内 `models/<模型名>/`，两端不同。

### 仍会咬人的
- ⛔ 服务器上**不要跑 `uv run` / `uv sync`**（会按 extras 卸包）；一律 `.venv/bin/python`。
- **后台发射**：`ssh host 'cd X && setsid nohup ... &'` 里，`cd X && A &` 会把**整条链**后台化 ——
  多条命令串在一个 `ssh` 里时，第二条的 cwd 会掉回 home（本次踩过，日志重定向直接失败）。
  **一条 ssh 只发一个后台任务。**
- **ssh 往返耗时容易低估**：我曾据"刚发射 3 秒"判定日志异常，实际进程已跑 4 分钟。
  **判活看 `ps -eo etime` 或 `nvidia-smi`，别靠自己对时间的感觉。**
- 三端 pytest 计数不同**都不是回归**：本地 352 passed / 12 skipped、4090 有 torch 计数更高。

---

## 3. Goal（照重写后的契约）

① **三图误差分解与归因（headline 正文）**：gold / predicted / repaired 三图上跑同一个 SeDGPL，
   把下游损失拆开并**归因到具体的构建与修复动作**。
② **净化的下游判定**：事实性净化对后继预测有无增益，**正面回答、不绕开**。
③ **误差预算**：`core/calibration/propagation.py` 的解析预算 vs 实测三图损失曲线。

---

## 4. ★ 开工第一件事：三图评测的接入点（本阶段最核心的技术决策）

**现状缺口**：`scripts/evaluate_cgep.py` **没有**接受外部图的参数，它只从 gold 构建 CGEP 实例。
`build_cgep(docs)` 吃 `RelationDocument`，`extract_ecgs(doc)` 从 **`doc.gold_edges`** 抽 ECG。

**三种可能设计，选第 3 个**：

1. ❌ 在预测图上重建 ECG 与 query —— 预测错的图会产生**错的 query**，与 gold 无法比较。
2. 🟡 固定 gold query、只看图能否重建 —— 这就是 **Phase B 已实现的 R1/R2**
   （`succession/reconstruction.py`），可直接复用作为**辅助**口径，但它不经过 SeDGPL，量不到 MRR。
3. ✅ **推荐**：**CGEP 实例的 query / candidates / label 全部固定来自 gold，只把喂给模型的
   图上下文（`CgepInstance.edges` 里的 template 部分）换成 predicted / repaired 的边。**
   这样 MRR 跨三图可比，且**隔离了"图质量"这一个变量** —— 正是误差归因需要的受控设计。

实现提示：`CgepInstance.edges = (*template, query)`，template 是同 ECG 内除 query 外的边。
接入点就是在 `build_cgep` 之后、按 doc_id 把 template 边替换为预测图中对应的边（gold 节点 id 与
预测边端点 id 同属 `{doc_id}::{mention_id}` 空间，**已验证可直接 join**）。

### 已就位、直接可用的资产
- **预测边 dump**：4090 `runs/factuality/predicted_edges_valid.jsonl`（710 篇 / **231,530 边** / 127M）。
  格式 `{doc_id, edges:[{head_id,tail_id,relation_type,subtype,directed,confidence,...}]}`，
  与 `consistency_repair_report.py` 的 `_edges_from_dump` 兼容。**不必重跑 GPU 抽取。**
- **两个归因开关**（`scripts/consistency_repair_report.py`）：`--no-close-temporal`（不补闭包边）、
  `--no-break-causal-cycles`（不破 causal 环）。已用它们做出 §0 的归因结论。
- **两个强对照函数**（`factuality/purification.py`）：`random_drop_control`（均匀）、
  `degree_matched_drop_control`（度数匹配，带 `degree_gap` 自检）。
- **已有产物**（本地 `runs/`）：`relations_repair_{close,noclose,nocausalbreak}.json`、
  `factuality_valid_{struct_best,6ep,nostruct,matched}.json`。
- 复用：`succession/{sedgpl,model,encode,linearize,selective,structure,predictor,metrics,reconstruction}.py`、
  `succession/cross_stage.py`、`core/calibration/propagation.py`、`scripts/evaluate_cgep*.py`、`build_cgep.py`。
- **待新建**：`cross_stage.py` 的 **3 类真实扰动生成器**（删/增因果边、并/拆节点、扰乱时序；
  现仅 reachability 掩码），用于画"哪类错误最伤下游"的曲线。

### 复现命令（SeDGPL 基线）
```bash
CUDA_VISIBLE_DEVICES=<空卡> HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  .venv/bin/python -u scripts/evaluate_cgep.py --dataset maven --predictor sedgpl \
  --model-path /data/TJK/models/roberta-base --epochs 10 --output runs/cgep/maven_sedgpl.json
```
`--limit-train` / `--limit-test` / `--max-folds` 可做冒烟。

---

## 5. Constraints / 红线

- **强对照是硬要求**（SPEC §4.5，源自 TACL 2406.01297 的实验 checklist）：
  删边类干预必须比**随机等量删边**（DropEdge ICLR'20 证明随机删边是强基线）；
  剔点类必须比**度数匹配**的随机剔除（均匀随机对低度数策略不公平，Ch3 实测差 3,573 条边）。
- **门控信号禁用金标 MRR**（oracle 泄漏是致命设计缺陷）。若保留门控档，二选一：在线可得的无标签代理，
  或显式定位为离线构建期质检工具。且门控**只施于 causal 环破除**（其余动作对下游按构造零影响）。
- **竞品逐点区分**（SPEC §5）：Kintsugi(2605.09487) / DeepRefine(2605.10488) / CauScientist(2601.13614)
  —— **不得主张「下游门控接受」为新**。我们的 delta = 事件因果图 + reachability/conformal 预算 +
  **三图误差分解与归因**。
- `EventNode` schema **零新增字段**（扩展走 `metadata`）；`tests/core/test_propagation.py` 是测试锁。
- 包/函数名**不得含 `ch1/ch2/ch3`**；新组件走 registry + lazy import；GPU 组件配 CPU 缓存回放。
- 代码走 git、数据/产物走 scp；**报数如实**（降就说降；ssh/工具失败不得伪装成结论；
  训练崩溃的跑必须作废并留证）。提交/推送**仅在作者明确要求时**。**专利/论文写作不在计划范围。**

---

## 6. Done when（验收）

- [ ] **三图（gold/predicted/repaired）下游指标 + 误差传播曲线**产出，升降如实报。
- [ ] **下游损失可归因到具体构建/修复动作**，每个干预附等量强对照。
- [ ] **净化的下游增益正面回答**（有或无都如实）。
- [ ] `uv run pytest && uv run ruff check src tests scripts && uv run ekg-smoke` 全绿（只增不改）。
- [ ] 结果落 `runs/cgep/` + 如实回填 `docs/TODO.md`。
- [ ] ~~repaired MRR > predicted MRR~~ **已作废**，若出现只作为如实报告的一行，不作成败判据。

---

## 7. 已知风险与止损

- **预期就是噪声级**（§1）：所以"没有增益"**不是失败，是本阶段要交付的结论之一**。
  headline 是把误差**说清楚、归因清楚、预算对上**，不是把某个数推高。
- **三图差异可能小到无法归因** → 退**受控扰动版**（按可控幅度注入三类错误，画损失曲线），
  仍能回答"构建误差如何影响下游"，这是合法退路。
- **R2 f1 绝对值仅 .078**（P .164/R .051）：下游天花板由 **Ch2 抽取器质量**决定。
  若要抬天花板，那是回头改 Phase A，不是在 E 里想办法。
- **别重蹈的坑**：
  ① **改算子前先确认该算子作用的边族是否进入下游口径** —— 本次第一轮探路就栽在这
  （以为掉点源于补 temporal 闭包边，实则 ECG 只读 causal+subevent，两者正交，那个实验根本
  检验不了那个假设）；
  ② 对标数字先核**一手表格**再定验收线（Phase C 因此白跑两轮，Phase D 靠这条纠正了 47.6 的口径）；
  ③ 稠密图上不要枚举简单环（已改 SCC 度量）；
  ④ dev 选择在小类任务上不可靠（Phase D 实测 dev 与 valid 排序相反），**多种子留 Phase H**。
