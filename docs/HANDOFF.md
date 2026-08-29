# 交接文档 · 新会话从这里开始

> 生成于 **2026-08-29**。读完本文即可接手，不需要回溯对话。
> **冲突时的优先级**：`docs/results/PHASE_*.md`（已发生的事实）> `docs/SPEC.md`（研究约束）>
> 当前 active phase > `docs/TODO.md` > 本文。本文只做导航与状态快照，**不复制实验数字**。

---

## 0. 三十秒摘要

- 课题：**occurrence-level 事件图谱构建 + 构建误差的下游代价**，三个方法章 + 一个系统评估章。
- **最高优先级：2026-09-03（周四）交给导师的阶段性报告** → `docs/reports/2026-09-03_阶段性报告.md`
  （骨架已完成，数字随实验滚动填）。作者要求：重心是**方法设计 + 数字 + 时间表**，工程基建少写；
  **要让导师看到已经做出东西，不是刚开工**。
- Ch2 的对手已**同协议实测闭合并冻结主锚**；Ch1 的机制已有首轮消融结果；
  Ch3 的**指标判别力问题已解决**，可以动手实现机制；Ch4 主效应早已成立。
- 本地 `main` = `08b3054`，工作树干净，**421 passed / 12 skipped**；远端已同步、四卡空闲、无进程。

---

## 1. 作者定下的规矩（违反会被纠正，已写进 CLAUDE.md/AGENTS.md）

| 规矩 | 要点 |
|---|---|
| **约束分级** | 规则分 A 有效性 / B 可追溯 / C 操作性。判据：**不遵守它会让结论变错，还是只让进度变慢？** 前者不让步，后者按现场调整。**卡空着就并行**，别被契约里的操作性条款焊死。 |
| **跑训练前先冒烟** | 本地没装 torch ⇒ GPU 相关单测是 skip 的，"421 passed" 不代表能跑。新代码必须先做小规模 **train→save→load→score 往返**验证，且顺带回归旧路径。 |
| **先解决方法问题再跑训练** | 否则跑出来的数可能没有判别力。Ch3 就是靠这条避免了一轮无意义训练。 |
| **不重复造轮子** | GitHub 上有且可运行的实现直接用（官方 baseline 代码等），只在本地做适配；透明补丁要记 hash。 |
| **可自行提交/推送** | 条件是 git 整洁、按逻辑单元分次提交、内容不丢失、可回滚、不强推。 |
| **机制/规则别写死** | 布局与组件清单写进 checkpoint 并在加载时校验，让将来的变更**响亮失败**而不是静默读错数。 |
| **单种子** | 作者定：当前阶段所有实验只跑 seed 13。 |
| **靶子由对手定** | 不用自己的历史成绩当及格线，用对比方法的实测成绩。 |

---

## 2. 协议身份（跑任何 A3 命令都要显式传）

| 项 | 值 |
|---|---|
| P1 trust root | `runs/stages/P1/p1-v6-20260829-r9/` |
| `protocol.json` SHA-256 | `440516dcbe038c4b6f924db756fb8d0529e1139bb0a263cc720b6d0f0a6d4fdc` |
| A3 plan | `runs/stages/A3/a3-v6-baselines-r10/preflight/execution_plan.json` |
| plan SHA-256 | `36a38e4f7b833af49897c32e9a39e5d464441d55f4f39cf7ef40d5e2085d4d15` |
| 冻结主锚 | `runs/stages/A3/a3-v6-baselines-r10/primary_anchor.json`（sha256 `894b9bd2…185b3c12`）**权威** |
| 模型（内容寻址，非上游 revision） | `/data/TJK/models/local/roberta-base/71be7419a60dcce0fc276654c8f9213b41f8def71a0c3465d7fed2352c961ea9` |
| 划分 | train 2,622 / internal-dev 291 / final-valid 710｜**final-valid 全程未访问** |

> 信任根与执行面已解耦：`prepare_a3_baselines.py` / `run_a3_baseline.py` / 推理配置**不在** `CODE_PATHS`，
> 改它们只产生新的 plan hash，**不作废 P1**。改 `CODE_PATHS` 里的文件才需要重建 bundle：
> `run_p1_local_gate.py` → `build_p1_bundle.py --bundle <新版本>` → `prepare_a3_baselines.py`。

---

## 3. 各章现状与下一步（按优先级）

数字一律见 `docs/results/`，本节只说**状态与该做什么**。

### ① Ch3 事实性 —— 方法问题已解决，**可以直接动手实现**（最高优先，报告缺口最大）

- 已完成：主指标判别力分析（`scripts/report_factuality_metric_power.py`）。结论见
  `docs/results/PHASE_D.md` 末两节：**配对 bootstrap 的 MDE ≈ 5 个稀有类实例**，
  机制头寸是 PS− 上「证据找得对、标签判得错」的落差。判定规则已预注册。
- **下一步**：实现 evidence→label 软耦合——按预测 evidence 概率对 token 做软注意力池化，
  得到 evidence 向量，与 mention 表示拼接后进 label 头；对照组是现有的平行双头。
  代码在 `src/ekg/factuality/detection.py` 与 `scripts/train_factuality_detector.py`
  （后者已支持 `--train-manifest/--dev-manifest`）。
- ⚠️ **先冒烟再训练**；训练/推理口径必须成对（checkpoint 声明布局并在加载时校验，照 Ch1 的做法）。

### ② Ch1 身份消解 —— 有结果但有两个已知缺陷要修

- 已完成：`--components` 机制（`src/ekg/nodes/discriminative.py`）与 2×2 消融，MUC 见 `PHASE_C.md`。
- **两个必须修的**：
  1. **选模轴错了**：按 pair-level F1 选 epoch，而它与 MUC 方向不一致 ⇒ 四个臂停在不同 epoch，
     epoch 差异是**未控制的混淆**。要么把选模换成 MUC/其代理，要么固定 epoch 预算重跑四臂。
  2. **增益来自 recall 而非设计假设的 precision**；未验证的解释是「欠并里 92.8% 是跨句对」。
     消融数据已在，可据此验证，但**不要把预测错的假设事后改写**。
- Ch1 的同协议对手（official coref）**尚未重跑** ⇒ 目前只有内部对照，没有对外差距结论。

### ③ Ch2 关系抽取 —— 差最后一步

- 已完成：三条 baseline 同协议闭合、主锚冻结、复现底座（50 epoch，排掉了欠训混淆）。
- **下一步 A3.2**：关系族均衡机制，去补 causal 与主锚的最后差距。
  注意 official joint 已用手调固定任务权重，**固定权重/网格不算创新**，要非固定机制
  （归一化族风险 / 自适应梯度平衡等）。契约见 `docs/phases/PHASE_A3_relation_balanced.md`。
- subevent 已超主锚、temporal 过护栏线但很险（只高 0.15），**做 causal 时不能把它们弄掉线**。

### ④ Ch4 下游代价 —— 主效应已成立，缺一个正控

- 已完成：构建损失是唯一超噪声地板的效应；修复/净化/oracle 全在地板内；受控扰动曲线。
- **下一步**：frozen 消费者的图依赖正控（gold vs 打乱/无图）。**它不依赖前三章产物**，
  随时可跑，且决定 Ch4 是独立贡献还是收缩为副章。

---

## 4. 会让你白跑的坑（都实际发生过）

1. **口径三轴**：报差值前必须对齐 **评分器 · 文档集 · 校正**。同一个错在本项目犯过四次。
   论文原报在 hidden test、我们只能报 valid ⇒ **不可直接相减**。
2. **配对 vs 绝对**：比较两个系统看**配对差值**的 CI，不是各自绝对分的 CI（后者宽 2.8 倍）。
   跨 split 比较丢掉的正是配对 ⇒ **与论文数字比永远不可判别**，主表必须自跑 baseline。
3. **代理指标 ≠ 报数指标**：Ch1 的 pair-F1 说机制略差，MUC 说好 2 点。选模轴选错会得出反的结论。
4. **本地没有 torch**：涉及 GPU 的测试全是 skip，别拿"全绿"当能跑的证据。
5. **远端必须先 `git fetch && reset --hard origin/main`**：已经发生过"推了没同步、拿旧代码跑冒烟"。
6. **MAVEN-ERE 的三层文本视图**：原始 `sentences` / 分词且**小写**的 `tokens` / 字段自带的 mention 串，
   混用必错。详见 `docs/ENGINEERING_NOTES.md`。
7. **训练预算不对等会伪装成架构结论**：Ch2 光是 3→50 epoch 就值 causal +5.11。
8. **服务器禁 `uv run`/`uv sync`**（会卸掉 torch），一律 `.venv/bin/python`；
   禁 `rsync --delete` 与远端 `git clean -fdx`。

---

## 5. 怎么操作服务器

```bash
# 隧道（cpolar）经常抖，低频重连，别高频握手
~/.ssh/hold-4090.sh                    # 建立 ControlMaster：~/.ssh/cm-ekg4090
ssh -o ControlPath=~/.ssh/cm-ekg4090 gpu-4090 '...'

# 长任务：一条 ssh 只发一个后台任务
ssh ... 'cd /data/TJK/ekg && CUDA_VISIBLE_DEVICES=N setsid nohup .venv/bin/python -u <cmd> \
         > logs/<name>.log 2>&1 < /dev/null & echo launched'
```

- 4090 主力（`/data/TJK/ekg`，四张 24GB 卡）；**卡空着就并行**，不同卡/不同 run-dir/固定 seed 互不影响。
- 5090 备用（`/mnt/aidata/tongjiakai/ekg`），**每次使用须单独问作者**。
- 判活三态 ALIVE / GONE / ssh 失败；**ssh 失败 ≠ 远端进程死了**。
- 长任务耗时**不要用前几个 epoch 外推**（warmup 期慢得多，实际快很多）。

---

## 6. 本轮已交付（供快速定位）

| 产物 | 位置 |
|---|---|
| 阶段性报告骨架 | `docs/reports/2026-09-03_阶段性报告.md` |
| Ch1 机制与消融组件 | `src/ekg/nodes/discriminative.py`、`scripts/train_coref_scorer.py --components` |
| Ch2 关系错误剖析 | `scripts/report_relation_error_profile.py`（自带对官方评分器的强制交叉校验） |
| Ch3 指标判别力/功效分析 | `scripts/report_factuality_metric_power.py` |
| 唯一的 manifest 划分实现 | `src/ekg/core/protocol.py` |
| 主锚冻结记录 | `runs/stages/A3/a3-v6-baselines-r10/primary_anchor.json` |

**验证命令**（改代码后必跑）：

```bash
uv run pytest                          # 当前 421 passed / 12 skipped
uv run ruff check src tests scripts
uv run ekg-smoke
```
