# PHASE P1 — v6 协议冻结与 Ch2 准入

> **COMPLETED / PASS。** 本文件保留为不可变阶段契约与执行记录。只读本文件、`AGENTS.md`、[`../SPEC.md`](../SPEC.md) 和
> [`../replan/G0_PROTOCOL_GATE_SCREENING.md`](../replan/G0_PROTOCOL_GATE_SCREENING.md) 即可执行。
> 本 phase 不做科研提分，不启动完整训练。

> **执行快照（2026-08-28）**：P1.1–P1.6 与本地三件套全部通过，bundle 为
> `runs/stages/P1/p1-v6-20260828-r4/`，可信 `protocol.json` SHA-256 为
> `09e7e392d807641bc0520f63c703299ee228a6a601fc85320afd73a95a85fc46`，
> `global_protocol_status=pass, a3_entry_status=pass`；详见
> [`../results/PHASE_P1.md`](../results/PHASE_P1.md)。P1 未产生科研 baseline 分数。

## Goal

把 `global_protocol_status` 与 `a3_entry_status` 分开收敛：前者固定数据/ID/evaluator/stage bundle，后者
证明 Ch2 三个必含 baseline 能在同一 candidate/scorer 协议下启动。只有全局协议失败阻塞全链；A3
入口失败只阻塞 A3，并须产生可审计的 `blocked` handoff。

## Inputs

- `data/processed/maven_ere/{train,valid}.jsonl`；
- `data/processed/maven_fact/{train,valid}.jsonl`，只用于验证跨章 ID 对齐；
- `scripts/score_maven_ere_official.py` 与 4090 固定 hash 的官方 evaluator；
- 4090 `runs/relations/*`、`runs/nodes/coref_supervised_6ep` 历史 checkpoint；
- [`../results/PHASE_A.md`](../results/PHASE_A.md) 只作历史事实，不从 Markdown 重建 metrics。

禁止输入：MAVEN hidden test 标签、人工筛选 ID、valid 上选出的新阈值/epoch、不同 split 的论文分数。

## Tasks（严格顺序）

### P1.1 冻结显式 manifests（CPU）

建立 `data/protocols/v6/`，至少包含：

- shared train/dev doc-ID manifests：ERE 与 FACT 共用同一批 IDs；
- ERE/FACT final-valid ID manifests；
- source file SHA-256、生成算法、生成代码 commit 和 manifest 自身 SHA-256；
- Ch4 共享 doc/event ID namespace、目标 query schema、生成器版本/来源 hash；完整 query/candidate
  manifest 在 E3.0 冻结，不是 P1/A3 前置。

内部 dev 采用固定 10% 文档（291 docs）。按 `sha256("ekg-v6:" + doc_id)` 排序取前 291，避免依赖 JSONL
原始顺序或运行时随机状态。所有训练脚本新增显式 manifest 参数；seed 只控制模型随机性，不再控制 split。

验证：ERE/FACT train/dev ID 集完全一致；train/dev/final-valid 两两不交；无重复；源 hash 与 G0 记录一致；
保存 ERE 各关系族与 FACT 五类/evidence 的 mention 数和 document support。固定 split 不因稀有类少而重抽；
当前支持数只用于披露和预注册护栏，禁止 split shopping。

对当前已核 source/hash，291-doc internal-dev 的 FACT 预期 mention supports 为 CT+ 6,835、CT- 129、PS+
198、PS- 19、Uu 14，PS-/Uu document supports 为 13/12。P1 必须从冻结源重新计算；不一致时停止并核
source/manifest，禁止为匹配预期数而改 split。

### P1.2 修复 manifest 可移植性（CPU）

移除或改正 `data/processed/maven_ere/manifest.json`、`maven_fact/manifest.json` 中旧 `Fin-EKG` 绝对路径。
manifest 只保存仓库相对路径、记录数、source hash 和获取说明；不引入环境相关默认路径。

### P1.3 冻结 evaluator 与 adversarial scorer fixtures（CPU/4090 CPU）

- 记录官方 evaluator 的 SHA-256、官方恢复来源和 4090 固定工具路径；不得只依赖 `/tmp`；
- 将 gold event relations 展开为 official mention-pair prediction 的过程固化成可测试脚本/fixture；
- 对 710-doc valid 做 gold-self，temporal/causal/subevent 与 B³/CEAFe/MUC/BLANC 全部必须满分；
- 增加可手算的非满分 fixtures：空预测、反向 causal edge、coref merge、coref split；分别断言精确预期分数；
- 重复 ID、缺失 ID、未知端点和 candidate population 漂移必须被 wrapper 明确拒绝；
- scorer hash 不同即拒绝复用旧 metrics，不能“差不多同一版”。

上述 gold-self/adversarial 访问在账本标 `purpose=protocol_fixture`，不算确认性模型评测，但不得省略记录。

### P1.4 固定 stage bundle schema（CPU）

实现或文档化 `runs/stages/<phase>/<bundle-id>/` 的四件套：

- `protocol.json`：data/manifest/candidate-ID/evaluator/config/code/checkpoint hashes、population counts、seed、
  `historical_final_access_disclosed` 与 v6 final-valid access ledger；
- `predictions.jsonl`：稳定 doc/instance ID 与逐实例输出；
- `metrics.json`：scorer 原始输出；
- `status.json`：`pass|conditional|failed|blocked`、`global_protocol_status`、phase/next-entry status、
  `primary_anchor_selection_rule`、已解析时的 `primary_anchor`、`historical_final_access_disclosed`、
  `final_valid_access_ledger`、`v6_confirmatory_eval_count`、是否 exploratory、upstream bundle IDs。

读取器必须由调用方传入可信 `protocol.json` SHA-256，不能用 bundle 自报 hash 自证；须重新散列 bundle
外部的 source/manifest/candidate/evaluator/config/code 证据及本地 remote-evidence snapshot，并检查完整
candidate protocol、access ledger、status 字段一致性、artifact hash、candidate-ID digest、population counts、
ID 集、重复和缺失。任一失败即停止；至少测试坏 artifact、错误可信根、外部文件篡改、伪造外部声明
hash、重复/缺失/多余 ID、未知 upstream 与矛盾 status。

### P1.5 Ch2 baseline closure（CPU/小样本）

持久化 baseline source/patch，而不是继续放 `/tmp`。最小集合：

1. 本地 sentence/pair classifier；
2. MAVEN-ERE official single；
3. MAVEN-ERE official joint；
4. RESIJ 只在公开实现或忠实复现闭环时作为可选结构对照，不是 A3 准入条件；另预列一个替代候选，
   但不能把失败候选临时换成更弱标准。

每个 baseline 都须记录 source commit、补丁、输入前提和 license；完成同一 10-doc fixture smoke，输出同一
official prediction schema。保存 candidate-ID digest 与 population counts。一个工程轮定义为一次有界诊断、
补丁和同协议 smoke，环境/路径/载入最多两轮；改变 candidate population 或 evaluator 不算修复，而是协议
失败。单个候选失败只移除候选，不升级为数据/任务 NO-GO。

在 baseline 运行前预注册 primary-eligible 强 roster（official single/joint）与 anchor 选择规则：默认取其中
合格 baseline 的 internal-dev causal mean 最高者，平分按 roster 顺序。本地 pair 不进入强锚 roster。另
预注册 matched seeds 13/17/42、document-cluster paired-bootstrap 10,000
次、subevent 非劣 margin 和 final-valid 解封规则。A3.0 在看到方法结果前解析并冻结同 split 主锚；主锚若
随机，必须与最终方法运行 matched seeds。

### P1.6 历史 checkpoint load smoke（4090 小样本）

在 `global_protocol_status` 必需项、P1.5 三个必含 baseline schema smoke 与本地三件套全过后，才允许
4090 对历史 Ch2 checkpoint 做最长文档前向/10-doc prediction smoke。只验证可加载、显存和 schema，
不训练、不调参、不覆盖历史产物。

开跑前向作者展示准确命令、`/data/TJK/ekg` 工作目录和预期 bundle/log；使用 `.venv/bin/python`。

## Promotion gate

### `global_protocol_status=pass`

- manifests/source hashes/ID 集验证 PASS；
- official evaluator 有固定恢复路径，gold-self、手算 adversarial fixtures 与拒绝路径全部通过；
- stage bundle schema 及坏 hash/重复/缺失 ID 测试通过。

### `a3_entry_status=pass`

- Ch2 candidate universe/labels/input assumptions/candidate-ID digest 冻结；
- local pair、official single、official joint 的同 schema 小样本 smoke 全部通过；
- primary-anchor selection rule、roster、matched seeds、document-cluster CI 与 guardrail margin 已预注册；
- 历史 checkpoint load/最长样本 smoke 通过；
- 本地 `pytest`、`ruff`、`ekg-smoke` 全绿，`historical_final_access_disclosed=true` 且
  `v6_confirmatory_eval_count=0`；gold-self 等协议访问已按 purpose 写入 ledger。

P1 不比较方法优劣，也不把小样本分数写成科研结论。

## Stop conditions

- 任一 source/manifest ID 有重复、缺失或 ERE/FACT 不对齐：立即停止，先修数据协议；
- official evaluator 无法恢复固定 hash，或 gold/adversarial scorer gate 失败：
  `global_protocol_status=blocked`，全链停止；
- 某 baseline 两次定向修补仍不能产同 schema 输出：降为背景，启用预先列出的替代；
- 替代后 local pair/official single/official joint 仍不能闭合：`a3_entry_status=blocked`，不启动 A3 主方法；
  同时写出 A3 `status=blocked, executed=false` 的 handoff，并记录可用的历史/本地 relation
  `fallback_component_bundle_id`（若无则显式为 `null`）；D3 可在自身前置闭合后继续；
- checkpoint load 改变 candidate/scorer 语义才可运行：拒绝兼容性 fallback，旧 checkpoint 只作历史缓存；
- 发现 valid 参与本轮 split/epoch/threshold 选择：相关 bundle 标 `exploratory`，不得进最终主表。

## Outputs

- `data/protocols/v6/*`；
- evaluator 恢复记录与 gold-self 可重放测试；
- Ch2 baseline source/patch/smoke bundles；
- P1 `protocol.json/metrics.json/status.json`，其中全局协议与 A3 入口状态分字段；
- A3 无法准入时的 `blocked/executed=false` status stub 及可用 fallback component 身份；
- Gate 结论追加到 `../replan/G0_PROTOCOL_GATE_SCREENING.md`，不把实验数字写进 phase 文件。

## GPU

默认无 GPU。唯一允许的是 P1.6 的 4090 小样本 load/显存 smoke；5090 不使用。任何完整 epoch 都属于
A3，P1 中禁止启动。
