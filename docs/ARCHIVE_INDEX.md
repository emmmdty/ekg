# 归档索引（历史留痕 · 正文已移出仓库）

> 这里只留**索引**：归档了什么、为何归档、去哪找。**正文一律不在仓内**，避免旧口径污染检索面
> 与 agent 上下文。当前权威见 [`SPEC.md`](SPEC.md)（总纲）与 [`TODO.md`](TODO.md)（实时状态）。

**正文位置**：仓库外 `../ekg-backup-20260727/`（与本仓同级，不入 git）。
git 历史中最后一次含正文的提交是 `3390363`，可用 `git show 3390363:docs/archive/<文件>` 取回。

| 备份子目录 | 内容 |
|---|---|
| `phase_contracts_20260807/` | **v4 时代的六份 phase 契约**（A/B/C/D/E/F）；已完成或止损，实测数字仍在 `docs/results/`。 |
| `rl_line_20260729/` | **生成式抽取 + RL 线整条**（见下） |
| `phase_handoffs_20260729/` | Phase B/C/D/E 的四份交接稿（682 行）；实测数字已进 `docs/results/`，交接稿只是当时的一次性冷启动材料 |
| `docs_archive/` | 下表全部 `.md` + `specs/`（三份历史设计稿） |
| `docs_archive_large/` | `midterm/`（中期报告 38M）· `patent/`（旧专利交底书）· `chapter1/`（SARGE 图表证据）· `projects/`（答辩 PPT 工程 79M） |
| `docs_orphans/` | `事件图谱构建研究进展.md`（v3「两章」时代综述，与 v4 四章冲突）· `OVERVIEW.html`（课题总览，内容与 SPEC 重叠） |

## 归档清单与理由

| 文档 | 为何归档 |
|---|---|
| `ARCHITECTURE.md` `RESEARCH_MAP.md` `RISK_CONTROL_DESIGN.md` `RL_DESIGN.md` | 架构 / 代码映射 / CS-CRP / verifier-as-reward 设计；活内容已并入 `SPEC.md`，金融口径过时。 |
| `HANDOFF_2026-07-10.md` `HANDOFF_2026-07-11.md` | 冷启动交接稿；状态与计划并入 `SPEC.md` + `TODO.md`。 |
| `NOVELTY_A1_2026-07-11.md` `NOVELTY_CSCRP_2026-07-11.md` | 新颖性复核证据表；结论并入 `SPEC.md §5`。**投稿前重扫新颖性时需从备份取回。** |
| `OUTLINE.md` `THESIS_DESIGN.md` `THESIS_REDESIGN_2026-07-10.md` `UPGRADE_PROMPT_2026-07-09.md` | 旧顶层主线 / outline / 提案 / 升级提示，均已被推翻。 |
| `CLOSED_LOOP.md` `BENCHMARK_SURVEY.md` `MIDTERM_HANDOFF.md` `SERVER_W3-4_RUNBOOK.md` | 旧闭环 / 竞品 / 中期交接 / 运维稿，均过时。 |
| `SETUP.md` | 环境安装，已并入根 `README.md`。 |
| `SARGE_RESULTS_SNAPSHOT.md` | SARGE 主结果数字快照 + 源仓与取回路径；2026-07-27 从主干移除时留档。 |
| `PHASE_G_financial_layer.md` | 旧 Phase G（金融应用验证层）契约。四章无一依赖，题目本无「金融」→ 整体移除。 |
| `phase_contracts_20260807/PHASE_{A,B,C,D,E,F}_*.md` | **v4 六份 phase 契约**，2026-08-07 v5 重设时归档。A/C/E 已完成；**B/D 的机制线止损**（一致解码修复、事实性净化在下游均为构造性零，含 oracle 档）；F 并入 E2。后续动作分别并入 **A2 / C3 / D2 / E2**。⚠️ 取回前先读 `TODO.md`——这六份里的对标口径部分已过时。 |
| `docs/phases/PHASE_{A2,C2,C3,D2,E2,H}_*.md` | v5 契约，已被 v6 的 A3/D3/C4/E3/H2 取代并从活动目录移除。清理前精确快照为 Git commit `f8f1c9ee99eee8951c99d01a3b3b32fea615c2d2`；历史结果仍以 `docs/results/` 为准。 |
| `docs/CODALAB.md` | MAVEN-ERE CodaLab 通道关闭后的提交手册；从 commit `f8f1c9ee99eee8951c99d01a3b3b32fea615c2d2` 取回，不再作为活动操作入口。 |
| `docs/replan/HANDOFF.md`、`DEEP_RESEARCH_PROMPTS.md`、`DR_*_PROMPT.md` | v6 重审过程的一次性交接和网页研究提示词；从 commit `f8f1c9ee99eee8951c99d01a3b3b32fea615c2d2` 取回。审计结论已保留在 `docs/replan/*_audit.md`、`SYNTHESIS_DECISION.md` 与当前 `SPEC/HANDOFF`。 |
| `scripts/evaluate_cgep_{cross_stage,selective}.py`、`profile_cgep_step.py`、`recompute_relation_metrics.py`、`convert_ccks_tianchi.py` | 无活动文档或调用方的一次性 v4 入口；其中关系重算脚本不是 v6 官方 evaluator，CCKS 转换又与统一预处理器重复。从 commit `f8f1c9ee99eee8951c99d01a3b3b32fea615c2d2` 取回。底层受测统计原语和历史结果未删除。 |
| `specs/` | 三份历史设计稿（2026-06-16 评测口径 · 2026-07-17 结构感知编码 · 2026-07-20 四章重设）。 |

## 生成式抽取 + RL 线（2026-07-29 移出，`rl_line_20260729/`）

| 移出内容 | 说明 |
|---|---|
| `src/ekg/rl/` → `src_ekg_rl/` | 阶段无关 RL 原语：组合奖励·组相对优势·势塑形·课程 |
| `src/ekg/relations/rl/` → `src_relations_rl/` | GRPO-RLVR 数据集/奖励/trainer/TRL 适配 |
| `scripts/train_relation_grpo.py`·`train_relation_extractor.py`·`_patch_vllm_nvml.py` | GRPO 训练、生成式 SFT 训练、vllm NVML 垫片 |
| `configs/relations/grpo_rlvr*.yaml`·`ablation_grpo_*.yaml`（8 个） | GRPO 实验配置 |
| `tests/rl/`·`tests/relations/test_{grpo_dataset,rl_rewards}.py` | 41 条测试随之移出（373 → 332） |
| `pyproject` 的 `rl` extra（trl） | 无 v4 章节依赖 |

**为何移出**：四章无一依赖。Phase A 的判别式抽取器已取代生成式那条线（生成式探针 causal 召回
**0.4%**、subevent **0%**，判别式做到 67.5%/88.1%），SPEC §5 又表明「结构作 RLVR 奖励」是红海。
留在仓内只增加检索面与上下文污染。**`relations/extractor/llm.py` 保留**（仍在 registry 里并被
`llm_*` 历史兼容配置使用）。旧 multi-agent YAML 因未接入正式评测入口而移除；多智能体实现只保留
直接 API、测试和 smoke，不得冒充 v6 实验方法。

## 时间线

- **2026-07-11**：文档体系重构，设计 / 交接 / 新颖性 / 专利类旧稿统一归档；旧「实体中心中文金融 + TKG
  外推」主线整体作废（代码在 tag `frozen-tkg-line`）。
- **2026-07-27**：SARGE 与 Phase G 金融应用层移出主干；项目改名 `Fin-EKG` → `ekg`；归档正文与两份
  孤儿文档一并移出仓库，仓内只留本索引页。
- **2026-07-29**：生成式抽取 + RL 线整条移出（上表）；同日 `docs/TODO.md` 的历史实测拆入
  `docs/results/`，TODO 收为纯状态板。
