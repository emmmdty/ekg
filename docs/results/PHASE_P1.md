# Phase P1 实测档案：v6 协议冻结与 Ch2 准入

> 执行日期：2026-08-27—2026-08-31。P1 不产出科研 baseline 分数；本文件记录协议 gate 的真实结果。

## 当前裁决

- `global_protocol_status=pass`；
- `a3_entry_status=pass`；
- P1 phase/status 为 `pass`，P1.1–P1.6 全部闭合；
- 允许进入 A3.0 baseline 解析与同协议 GPU 实验；D3/C4/E3 的章节本地前置仍按各自契约后置。

当前权威 bundle：`runs/stages/P1/p1-v6-20260831-r12/`；可信 `protocol.json` SHA-256 为
`0bd33e87e67c1e4b36afb335270cbd511377c412d16e87b835a3503f0aa58497`。其四件套已由
`ekg.core.stage_bundle.validate_stage_bundle` 使用该外部可信根重读通过。先建的 r1 因 A3 precheck 发现
本地/远端 run-dir 混用而失效；r2 因缺少 execution-plan 外部 hash 而失效；r3 在 clean 远端复验时暴露
local gate 绑定了本地 dirty-tree Python 文件数，不能代表已推送提交。r4 在 detached clean `53ce6f1` 上
重跑门禁后生成。r9–r12 依次绑定 temporal、trainer、balance controller 与逐位置实现；旧 bundle 均保留
作审计，未被覆盖或继续选用。

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

- `uv run pytest`：380 passed、12 skipped；skip 均为本地无 torch 的 GPU tests；
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

clean commit CPU 已生成 `runs/stages/A3/a3-v6-baselines-r9b/preflight/execution_plan.json`：重新验证 r4 trust root、
2,622 train + 291 internal-dev manifests/candidate/label digests，物化官方代码期望的 train/valid/test 形状，
并明确 `final_valid_accessed=false`。official source 的 model path 适配仅作用于隔离副本，逐文件保存前后
hash 与替换次数。plan SHA-256 为
`0694c2b5ec13afe6b0a2a4c927e003c99f62a93948f48331c063abc9ab11fb1f`；launcher 强制由调用方传入，
并拒绝 source/data 文件集合的增删。local pair、official single、official joint 的 seed-13 launcher 均以 no-execute 模式通过，
输出的 Python、cwd、run-dir 与预期产物全部位于 `/data/TJK/ekg`。同一物化命令随后在 clean 远端
`1d38dce` 重跑，得到相同 population、`final-valid not accessed` 与逐字相同 plan SHA-256；三路远端
no-execute 也全部 PASS，检查后四张 4090 仍为 0% 利用率且无项目 Python 进程。尚未启动 A3 GPU 训练。

## 结论

全局数据、评测器、错误隔离协议和 4090 真实 checkpoint 前向均已通过，故
`global_protocol_status=pass, a3_entry_status=pass`。P1 完成；本阶段没有产生科研 baseline 分数，下一步按
A3 契约解析 strong anchor 并运行同协议 baseline。

## r6/r7 · 解开信任根与执行面的耦合（2026-08-28）

**动机（实测代价）**：r1→r5 共五个信任根，21 天，0 个 GPU 小时。根因是两处过紧耦合，不是协议本身：

1. `scripts/build_p1_bundle.py` 的 `CODE_PATHS` 收了 `prepare_a3_baselines.py` 与 `run_a3_baseline.py`
   ——A3 的 materializer/launcher。改一行模型默认路径就作废整个 P1 bundle。
2. `_validate_local_gate` 用 `rglob("*.py")` 重算 **src/tests/scripts 全树**并要求与当前工作树逐字节相等。
   任何无关文件（例如未提交的 Ch1 `report_coref_error_profile.py`）都会让 bundle 失效——这正是 r3
   的 `local tested file count drift`，也是 r4 必须开 detached clean worktree 才能生成的原因。

**改动**：

- A3 执行面移出 `CODE_PATHS`。其身份改由两处更贴切的粒度承载：`execution_plan.json` 新增
  `execution_surface`（materializer/launcher 的 SHA-256），launcher 本就在每个 run 的
  `run_metadata.json` 里写 `launcher_sha256`。**改执行面只产生新的 plan hash，不作废协议。**
- local gate 升 `ekg.p1_local_gate.v2`：新增 `tested_file_sha256` 逐文件哈希；`tested_tree_sha256` /
  `tested_file_count` 保留为**留痕**，不再回算比对。校验改为「gate 记录的 `CODE_PATHS` 哈希 == 当前值」
  ＋ `tree_changed_during_gate` 必须为假。断言的仍是「三件套跑在与现在逐字节相同的 P1 代码上」。
- `--bundle` 默认改为跟随 registry 选中的 bundle（原先写死 `...-r3`，每次 supersede 都变成过期地雷）。

**未放宽的部分**（明确记录，防止后人误读为降低标准）：数据 / manifests / candidate / evaluator /
preregistration / P1 代码本身的哈希绑定一律不变；stage bundle 的外部可信 protocol hash、证据重哈希、
坏 hash 与重复/缺失 ID 的 fail-fast 全部保留。放弃的只有「无关文件不得变动」这一条——它约束的是
仓库卫生，不是协议正确性。

**回归锁**（`tests/scripts/test_build_p1_bundle.py`，+5 tests）：无关文件改动**不得**作废 gate；P1 代码
哈希漂移**必须**被拒；A3 执行面**不得**出现在 `CODE_PATHS`；v1 schema 与 `tree_changed_during_gate`
必须被拒。

**结果**：

| 项 | 值 |
|---|---|
| 本地三件套 | **399 passed / 12 skipped**（+5 回归锁）、ruff 0、`ekg-smoke` OK |
| 权威 bundle | `runs/stages/P1/p1-v6-20260829-r9/` |
| `protocol.json` SHA-256 | `440516dcbe038c4b6f924db756fb8d0529e1139bb0a263cc720b6d0f0a6d4fdc` |
| A3 plan | `runs/stages/A3/a3-v6-baselines-r9b/preflight/execution_plan.json` |
| plan SHA-256 | `0694c2b5ec13afe6b0a2a4c927e003c99f62a93948f48331c063abc9ab11fb1f` |
| 物化计数 | 2,622 train + 291 internal-dev；`final_valid_accessed=false` |
| launcher 预检 | `official_joint` seed-13 no-execute PASS，打印 r7 路径，无进程启动 |

**验证解耦生效**：在 `scripts/` 下临时新建一个无关文件后 `--validate-only` 仍 **PASS**，删除后再次
**PASS**。r7 全程在**含 Ch1 未提交改动的当前工作树**中构建与复验，未使用 detached worktree。

r5 生成时的 v1 gate 已另存为 `runs/stages/P1/p1-v6-20260828-r5.local_gate.v1.json`，保持 r5 可回溯。
r6 是同一修复的中间版本（`--bundle` 默认值尚未修），保留不覆盖。

## r9 · temporal 归队 + pilot 验证全链（2026-08-29）

**为什么重冻**：r1–r8 冻结的 Ch2 候选全集是纯 event、只有 causal/subevent。但 MAVEN-ERE 有 TIMEX 与
6 类 temporal 关系，官方 `joint`/`temporal` 都评它（`joint/src/data.py`：temporal 用
`ignore_timex=False`、causal/subevent 用 `ignore_timex=True`）。按「靶子由对手定」的口径必须做。

候选**按族分离**，因此 causal/subevent 的六个 digest **逐位未变**（可证明加 temporal 没污染原口径）：

| split | causal/subevent 有序对 | temporal 有序对 | TIMEX | temporal 正例 |
|---|---|---|---|---|
| train | 2,297,524 | 3,315,358 | 14,969 | 800,375 |
| internal-dev | 234,870 | 348,632 | 1,719 | 84,319 |
| final-valid | 613,706 | 904,226 | 4,139 | 208,300 |

**交叉校验**：loader→`pair_examples` 路径与协议摘要路径各自独立实现，六个 temporal 子类正例
逐位一致（84,319 = 84,319），含双向的 `SIMULTANEOUS`/`BEGINS-ON`。

### Pilot 抓到的 9 个问题（20 篇 / 1 epoch，成本约 3 分钟）

先 pilot 后冻结，是这一轮唯一的方法论改动。它抓到的每一条都会让正式 baseline 报废：

| # | 问题 | 若不修的后果 |
|---|---|---|
| 1 | `rep()` 查不到 TIMEX，`if rh and rt` 静默丢弃 | **40% gold 时间关系消失**，与官方不是同一任务 |
| 2 | TIMEX `mention` 是分词形式，doc_text 用原始 `sentences` | 多 token TIMEX 定位失败 → 训练直接崩 |
| 3 | MAVEN-ERE `tokens` 是小写的 | 句首 TIMEX 定位失败 |
| 4 | 语料含字面 `UNK` token | 3 篇文档无法加载 |
| 5 | 推理侧 loader 没开 TIMEX | 预测边含 TIMEX **0%** |
| 6 | 抽取器在 TIMEX 对上吐 causal 边 | 官方校验拒绝（未知端点） |
| 7 | 归一化层硬编码拒绝 temporal | temporal 永远是空 |
| 8 | plan 的 `--families` 只有两族 | 正式跑仍不含 temporal |
| 9 | 推理配置（一致性模式 + TIMEX 开关）不在 plan 哈希内 | 科学输入可静默漂移 |

修完实测：全语料 **3,623 篇 / 20,827 个 TIMEX，零失败**；预测边含 TIMEX **0% → 37.6%**（gold 39%）。
全链贯通：train → infer → normalize → 官方评分，三族均出分（20 篇 1 epoch 的分数无意义）。

### 模型 pin 改为内容寻址

服务器已有完整 roberta-base 快照但**无 revision 元数据**。不声称未经核实的上游 commit，改用
五个文件 SHA-256 的规范摘要作为目录名与 `revision`（`revision_kind=local_content_digest`）：
`/data/TJK/models/local/roberta-base/71be7419…c961ea9`（硬链接，零额外磁盘）。
加载自检：124.6M 参数 / hidden 768 / 12 层 / vocab 50265 / tokenizer 往返正确。

| 项 | 值 |
|---|---|
| 本地三件套 | **408 passed / 12 skipped**、ruff 0、smoke OK |
| P1 bundle | `runs/stages/P1/p1-v6-20260829-r9/` |
| `protocol.json` SHA-256 | `440516dcbe038c4b6f924db756fb8d0529e1139bb0a263cc720b6d0f0a6d4fdc` |
| A3 plan | `runs/stages/A3/a3-v6-baselines-r9b/preflight/execution_plan.json` |
| plan SHA-256 | `0694c2b5ec13afe6b0a2a4c927e003c99f62a93948f48331c063abc9ab11fb1f` |
| 三路 no-execute | PASS（`--families causal subevent temporal`） |

⚠️ **模型路径修复没有作废 r9**——`prepare_a3_baselines.py` 已移出 `CODE_PATHS`，只产生了新的 plan
hash。这是本轮解耦的直接回报：过去这类修复要重建整个信任根。

## r12 · Ch2 逐族×位置控制器准入（2026-08-31）

**为什么重冻**：第二核心周期把 pair row、工作点控制器和 trainer 从逐族扩展到逐族×同/跨句位置。
这三个文件均在 P1 受控代码面；数据、manifest、candidate、evaluator 和冻结主锚没有改变。

本地在提交 `91d32d8` 上通过：447 passed / 16 expected skips、ruff 0、`ekg-smoke` OK，
`scripts/run_p1_local_gate.py` PASS。上传的 `local_gate.json` SHA-256 为
`5531149eb611f9ee6e379a07f27bffb7cedadaa68ceb52254bda6ba96393ac24`。

4090 端 clean `91d32d8` 上重建并独立读取：

| 项 | 值 |
|---|---|
| P1 bundle | `runs/stages/P1/p1-v6-20260831-r12/` |
| `global_protocol_status` / `a3_entry_status` | `pass` / `pass` |
| `protocol.json` SHA-256 | `0bd33e87e67c1e4b36afb335270cbd511377c412d16e87b835a3503f0aa58497` |
| A3 preflight | `runs/stages/A3/a3-v6-position-workpoint-r13/preflight/` |
| A3 plan SHA-256 | `b587b21d7aa74437d7144ecad76d87f4fe2253f39966d48bb23108e914ec1eda` |
| 物化计数 | 2,622 train + 291 internal-dev |
| final-valid | 未访问 |
| GPU 状态 | 审计时 4×RTX 4090 空闲，无项目训练进程 |

P1 r12 构建本身只完成协议与 CPU preflight，没有产生科研分数。随后的 r13 2 epoch GPU
行为 smoke 见 [`PHASE_A.md`](PHASE_A.md)；它同样未调用 official evaluator，不改变 P1 的结论边界。
