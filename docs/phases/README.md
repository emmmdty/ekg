# EKG v4 · 阶段化执行手册（单会话自包含 phase）

> 把批准的 v4 四章计划拆成**互相隔离、单个 Claude Code / Codex 会话可完成**的 phase，避免长会话上下文互相污染。
> 权威设计见 [`../SPEC.md`](../SPEC.md)（§1 四章 + §5 防审稿创新点）与批准计划稿；实时状态见 [`../TODO.md`](../TODO.md)。

## 方法论（据官方最佳实践）

- **自包含契约（Spec-Driven Development）**：每个 phase 是一份"super-prompt"，**只读该 phase 文件 + 自动载入的
  `CLAUDE.md`/`AGENTS.md` + `SPEC.md` 即可执行，无需翻聊天记录或别的 phase**。
- **Codex 四要素**（每个 phase 文件的骨架）：**Goal**（要的结果、不是步骤）· **Context**（涉及文件/数据/前置产物）·
  **Constraints**（约定与安全）· **Done when**（可验证的结束态）。
- **Claude Code 纪律**：plan 优先；`CLAUDE.md` 开局入上下文并全程保留；**把每个会话当一次性的——进度落文件、频繁提交**；
  phase 之间 `/clear`；能 TDD 就 TDD。
- 参考：[Claude Code best practices](https://code.claude.com/docs/en/best-practices) ·
  [Codex best practices](https://developers.openai.com/codex/learn/best-practices) ·
  [Spec-driven development (GitHub)](https://github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit/)。

## 每个 phase 文件的模板
`Goal / 依赖·产物 / Context(复用·新建) / 执行内容(Steps) / Constraints / 验收标准(Done when) / GPU / 达不到怎么办`

## 如何在新会话跑一个 phase

**Claude Code**：进仓库 → `/clear` → 输入：
> 读 `docs/phases/PHASE_X_*.md` 并执行。遵守 `CLAUDE.md` 硬约束与 `docs/SPEC.md` 设计。走 plan 模式先规划，能 TDD 就 TDD。完成后按该文件「验收标准」逐条自检，跑 `uv run pytest && uv run ruff check src tests scripts && uv run ekg-smoke`，把实测数字写进 `docs/results/PHASE_X.md`、状态更新到 `docs/TODO.md`。

**Codex**：仓库根有 `AGENTS.md`（与 `CLAUDE.md` 同步）→ 让 Codex 读 `docs/phases/PHASE_X_*.md`，用其 Goal/Context/Constraints/Done-when 执行，跑校验命令验收。

**收尾协议（每个 phase 结束都做）**：① 校验命令全绿（`pytest` 只增不改 / `ruff` 0 / `smoke` 绿）；
② 产物落 `runs/`；③ **实测数字写进 `docs/results/PHASE_X.md`**（单一事实源，如实：降就说降），
`docs/TODO.md` 只更新状态与下一步；④ 需要提交时才提交（作者要求）。

## 阶段依赖图（v5 · 2026-08-07 重设）

> **v5 的组织原则**：章节按**「有公开对手的任务」**划分，每章都要在公开可比的主指标上
> **超过多个**方法（见 [`../SPEC.md`](../SPEC.md) §1）。v4 的「可信度四维」并列脊柱作废；
> 六个自研机制的零效应结论**保留为 Ch4 的归因证据**，不再作方法卖点。

```
P0 主数据 ✅
   │
   ├─▶ [A→A2]  Ch2 事件关系抽取     ⭐队首   对手: 官方/+joint/BertERE/MAQInstruct/RESIJ
   ├─▶ [C→C3]  Ch1 事件身份消解              对手: 官方/+joint/RESIJ
   ├─▶ [D→D2]  Ch3 事件事实性检测   ✅已过线  对手: DMBERT/DMRoBERTa/RoBERTa+CLS/GPT-4
   │
   └─▶ [E→E2]  Ch4 下游代价与消费者依赖性(headline)  对手: ELM/QGELM/EGELM/one-shot
              ▲  │
              │  └─ 产出「误差代价排序」决定 Ch1/Ch2/Ch3 各自优化方向
              └──── Ch1/Ch2/Ch3 的真实构建图回灌，闭合实测因果链
                                    │
                                    └─▶ [H] 多种子+消融+新颖性扫 ─▶ [I] 写作
```

⇒ **A2 / C3 / D2 三条可并行**（不共享代码域）；**E2 依赖它们产出真实图**，但步骤 1（in-context 臂
自检）可提前独立做。

## 阶段索引（一句话 Goal + 状态 + 依赖）

| Phase | 章 | Goal（一句话） | 状态 | 依赖 | GPU |
|---|---|---|---|---|---|
| **A2** ⭐ | Ch2 | 关系抽取超过 MAQInstruct（causal 32.5 / subevent 25.2） | 🟢 **队首**；两根因已修 causal 28.50，剩梯度累积/类型 embedding/TIMEX 头 → [`PHASE_A2_ch2_official_recipe.md`](PHASE_A2_ch2_official_recipe.md) | P0 | 重 |
| **C3** | Ch1 | 非对称代价修欠并，MUC 77.47 → 超官方 81.4 | ⬜ **新建** → [`PHASE_C3_ch1_asymmetric_cost.md`](PHASE_C3_ch1_asymmetric_cost.md) | P0 | 中 |
| **D2** | Ch3 | 跨数据集泛化，堵掉「冷门数据集」质疑 | ⬜ **新建**；本章检测已超四个公开方法 → [`PHASE_D2_ch3_cross_dataset.md`](PHASE_D2_ch3_cross_dataset.md) | P0 | 轻 |
| **E2** | Ch4 | 加 in-context 消费者臂，验消费者依赖性假设 | ⬜ **新建（headline）** → [`PHASE_E2_ch4_consumer_dependence.md`](PHASE_E2_ch4_consumer_dependence.md) | A2·C3·D2 | 重 |
| **C2** | Ch1 | 跨文档泛化（ECB+/CLES） | ⬜ 未开始，**Ch1 的可选加分项**，不在关键路径 | C3 | 轻 |
| **H** | 全篇 | 多种子 + 消融补齐 + 投稿前新颖性扫 | ⬜ 等各章过线 | A2·C3·D2·E2 | 重 |
| **I** | — | 论文写作（非代码 phase） | ⬜ 等主实验 | 全部 | — |

**已完成/已止损、契约已归档**（正文在 `../../../ekg-backup-20260727/phase_contracts_20260807/`，
**实测数字全部保留在 [`../results/`](../results/README.md)**）：

| Phase | 归档理由 |
|---|---|
| A | Ch2 判别式抽取器；已完成，后续动作并入 A2 |
| B | 一致解码+修复+CRC；**止损已触发**（违反清零但下游无增益），降为 Ch4 归因证据 |
| C | Ch1 规范节点；已完成，后续动作并入 C3 |
| D | Ch3 事实性+净化；检测达标、**净化止损**（oracle 亦为零），后续动作并入 D2 |
| E | Ch4 三图传播；已完成，其结论是 E2 的**输入** |
| F | 端到端预算；v5 中并入 E2 的可靠性模块，独立 phase 取消 |
| ~~G~~ | 金融应用层，2026-07-27 整体移出 |

> **数字不在本表**：一律见 [`../results/`](../results/README.md)（单一事实源）。当前队首见
> [`../TODO.md`](../TODO.md)「下一步」。
> 编号 **刻意不重排**（大量文档引用字母编号）；新 phase 用 `<原字母><序号>` 派生（C→C3、D→D2、E→E2）。
