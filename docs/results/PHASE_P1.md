# Phase P1 实测档案：v6 协议冻结与 Ch2 准入

> 执行日期：2026-08-27—2026-08-28。P1 不产出科研 baseline 分数；本文件记录协议 gate 的真实结果。

## 当前裁决

- `global_protocol_status=pass`；
- `a3_entry_status=pass`；
- P1 phase/status 为 `pass`，P1.1–P1.6 全部闭合；
- 允许进入 A3.0 baseline 解析与同协议 GPU 实验；D3/C4/E3 的章节本地前置仍按各自契约后置。

权威 bundle：`runs/stages/P1/p1-v6-20260828-r3/`；可信 `protocol.json` SHA-256 为
`e449e7313c2b0b9235b413f3292877f1a842e4ed85be4d7ba020d28601c4f84f`。其四件套已由
`ekg.core.stage_bundle.validate_stage_bundle` 使用该外部可信根重读通过。先建的 r1 因 A3 precheck 发现
本地/远端 run-dir 混用而失效；r2 又因缺少 execution-plan 外部 hash 而失效。两者均保留作审计，未被
覆盖或继续选用。

## P1.1/P1.2：manifest 与 source

冻结源文件：

| 语料/split | docs | SHA-256 |
|---|---:|---|
| MAVEN-ERE train | 2,913 | `6a5519fe7c30448690adb13d49217c50d474fc57480eae10aecb29df7eb638b7` |
| MAVEN-ERE valid | 710 | `6faea0e4e16b4a2d5d9631e09ef6e1c6bac6e3f912490bfc48eeaceaf98c6153` |
| MAVEN-FACT train | 2,913 | `190522b44f0702af030161924d7cb94c4a06bd5d6e2b40d79f8f1eaa5886bab7` |
| MAVEN-FACT valid | 710 | `396fcf0779b67f0229f2cdaad4df0771682d9238a94b082d61659059b8dc7cff` |

按 `sha256("ekg-v6:" + doc_id)` 冻结为 2,622 train、291 internal-dev、710 final-valid；ERE/FACT
共享 ID 集，三者无重叠、无重复。FACT internal-dev 重新计算的 mention support 为 CT+ 6,835、CT- 129、
PS+ 198、PS- 19、Uu 14，PS-/Uu document support 为 13/12，与契约预期一致，未重抽 split。

两份 processed manifest 已移除旧 `Fin-EKG` 绝对路径，改为仓库相对路径、逐 split records 与 SHA-256。
六份显式 manifest 的文件 SHA-256 由 `data/protocols/v6/registry.json` 外部登记，避免“文件内自 hash”循环。

Ch2 train/internal-dev/final-valid population 分别为 66,744/7,195/17,780 event mentions 和
2,297,524/234,870/613,706 ordered mention pairs。final-valid pair digest 在 manifest/scorer 两端独立重算均为
`b551c033b4c265a72619f52fc0585e122328a78ed16f40e35264fff8e2a6d4e6`。

## P1.3：official evaluator gate

官方 MAVEN-ERE source 固定在 commit
`ac81a9711a69f43f55bfbc50b3bb573fd11c64b0`；evaluator SHA-256 为
`32919e86d98c6fafae6aa9505579e2c356caee12c32c1a8c719910acec359598`。恢复地址、GPL-3.0 license、
本地路径和透明 compatibility patch hash 均在 `data/protocols/v6/source_lock.json`。

710-doc gold→official mention-pair prediction 经固定 evaluator 重放，temporal/causal/subevent 与
B³/CEAFe/MUC/BLANC 的 P/R/F1 全部为 100。四个固定手算 fixture 也通过：

| fixture | 关键预期 |
|---|---|
| empty | 三关系 F1=0；B³/CEAFe/MUC/BLANC F1=66.67/44.44/0/40 |
| reverse causal | causal F1=0，其余任务保持 100 |
| coref merge | B³/CEAFe/MUC/BLANC F1=66.67/44.44/80/25 |
| coref split | B³/CEAFe/MUC/BLANC F1=66.67/44.44/0/40 |

严格 wrapper 另以单测确认会拒绝缺失/多余/重复 document ID、未知 endpoint、自环、重复/冲突 pair、
subtype schema 缺失与 candidate digest 漂移。所有 valid gold 访问在 ledger 标为 `protocol_fixture`；
`v6_confirmatory_eval_count=0`。

## P1.4：stage bundle

stage schema 升为 `ekg.stage_bundle.v2`。reader 不再信任 bundle 自报协议 hash：调用方必须给出可信
`protocol.json` SHA-256；reader 重新散列外部 source/manifests/candidate/evaluator/config/code 和本地保存的
remote evidence snapshot，并绑定完整 `ch2_candidate_protocol.json` 与 append-only access ledger。

反例覆盖坏 artifact、错误可信根、外部文件篡改、同时改 protocol 声明仍伪造外部 hash、重复/缺失/多余
prediction ID、未知 upstream 与 status 字段矛盾。builder 另拒绝只有顶层 `status=pass` 的伪 remote JSON，
并交叉检查 checkpoint/input/prediction/log hashes、严格 schema、真实 wall time 与“原 argv 未保存”的诚实披露。

## P1.5：baseline closure

同一 frozen 10-doc fixture（232 event mentions、6,508 ordered pairs，candidate digest
`313ec48e657374bc5afb7d09df9282c32f1d7a3acfdbfe1bc35435765042df3c`）上：

| baseline | source adapter | schema smoke |
|---|---|---|
| local pair | `ekg.relations.pairs.pair_examples` | PASS |
| official single | official `causal/src/dump_result.py` | PASS |
| official joint | official `joint/src/dump_result.py` | PASS |

三路都经 strict wrapper 验证完整 official prediction schema。此次给 adapter 的是 constant-NONE label vectors，
因此产物强制标 `schema_only=true, model_execution=false`，不计算、不记录 baseline 科研分数。

官方 source compatibility patch 只做两类当前栈适配：AdamW 改从 torch 导入；旧 BertConfig 继承判断改为
AutoModel。没有改 data loader、candidate、labels、dump adapter 或 evaluator；四个受影响文件均通过
`py_compile` 和 source `git diff --check`。

已预注册 official single/joint 强 roster、按 internal-dev causal mean 选主锚、平分按 roster 顺序、matched
seeds 13/17/42、document-cluster paired bootstrap 10,000 次、subevent 1.0 F1 point 非劣 margin 和 sealed
final-valid 解封规则。`primary_anchor=null` 是正确状态：P1 未运行 baseline 训练，主锚在 A3.0 解析。

## 本地验证

- `uv run pytest`：392 passed、12 skipped；skip 均为本地无 torch 的 GPU tests；
- `uv run ruff check src tests scripts`：PASS；
- `uv run ekg-smoke`：PASS。

命令、return code 与 stdout/stderr 保存在 `data/protocols/v6/local_gate.json`。

## P1.6：4090 历史 checkpoint 真实前向

cpolar 入口先后出现 banner timeout/reset；显式 ControlMaster 有界重连在第 5 次成功。该连接故障只影响
基础设施可达性，没有被记成模型失败，也没有转用需逐次授权的 5090。

4090 上 4 张 RTX 4090 均空闲。当前代码无法 strict-load 旧 150,004-byte `supervised_maven` head，这一已知
架构差异已记录在 `ENGINEERING_NOTES.md`；因此选择与当前 `PairClassifier` state dict 同形、且有训练日志的
历史档 `runs/relations/a4090_ctrl_accum1` 做兼容性 smoke。该档 internal-dev 日志只用于确认 provenance，
不作为 v6 baseline 科研证据；5090 上历史最佳 `window_dist_20ep_macro` 未搬运。

checkpoint 三件套 SHA-256：

| 文件 | SHA-256 |
|---|---|
| `config.json` | `907d8b4e1c5501df2c1a3edc856d6912a0a25d712cfda4fb02533edeabb29ecd` |
| `heads.pt` | `9a1baba9c5e5636d04067a2880a42727a7e526d572437cdfad254830df1e66a3` |
| `model.safetensors` | `57aa8566964a675cf7209f2407dcb6f1a2d7d9a3a273803ff374b089b5529213` |

GPU 0（RTX 4090，24,564 MiB）上的两次 frozen inference 均 return code 0、无 OOM、无 skipped document：

| fixture | docs | event mentions | ordered candidates | predicted relation pairs | strict schema |
|---|---:|---:|---:|---:|---|
| 10-doc | 10 | 232 | 6,508 | 1,861 | PASS |
| longest internal-dev | 1 | 47 | 2,162 | 226 | PASS |

最长文档为 `c5e2a4e212ab534072d53d07101c1b75`（1,723 source tokens）。两份输入经 `scp` 后双端
SHA-256 一致；两份 prediction 回传后由 strict wrapper 验证完整 ID、endpoint、subtype、重复/冲突 pair 与
candidate digest。原始 metadata/predictions/log 在 `data/protocols/v6/remote_smoke.json` 和
`data/protocols/v6/remote_smoke/`。峰值显存未采样，只能声称真实前向无 OOM，不能声称精确峰值。
当时未持久化实际 argv，故 metadata 明确记录 `executed_command_available=false`，只给出可重放命令及
实测 wall time（10-doc 6.7 s、最长样本 11.2 s）；不得把重放命令冒充逐字原命令。A3 launcher 从现在起
强制保存实际 argv、cwd、return codes 与产物 hashes。

## A3 正式入口预检

本地 CPU 已生成 `runs/stages/A3/a3-v6-baselines-r3/preflight/execution_plan.json`：重新验证 r3 trust root、
2,622 train + 291 internal-dev manifests/candidate/label digests，物化官方代码期望的 train/valid/test 形状，
并明确 `final_valid_accessed=false`。official source 的 model path 适配仅作用于隔离副本，逐文件保存前后
hash 与替换次数。plan SHA-256 为
`9ea3aa84acc1e781256aadc45cf3078775952f91a71ba78526718356f2a18bdf`；launcher 强制由调用方传入，
并拒绝 source/data 文件集合的增删。local pair、official single、official joint 的 seed-13 launcher 均以 no-execute 模式通过，
输出的 Python、cwd、run-dir 与预期产物全部位于 `/data/TJK/ekg`；尚未启动 A3 GPU 训练。

## 结论

全局数据、评测器、错误隔离协议和 4090 真实 checkpoint 前向均已通过，故
`global_protocol_status=pass, a3_entry_status=pass`。P1 完成；本阶段没有产生科研 baseline 分数，下一步按
A3 契约解析 strong anchor 并运行同协议 baseline。
