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

## 阶段依赖图（关键路径 A→B→C→D→E）

```
P0 主数据 ✅ ───────────────────┐
                                ▼
[A] Ch2 判别式抽取器 ──▶ [B] Ch2 一致性+修复+CRC ──┐
                                                    ▼
        [C] Ch1 规范节点 ──▶ [C2] Ch1 跨文档泛化    │
              │                                     ▼
              └──────────────▶ [D] Ch3 事实性+净化 ─▶ [E] Ch4 闭环+误差传播 ─▶ [F] 端到端预算
                                                         │
                                                         └─▶ [H] 稳健化(多种子+消融+新颖性扫) ─▶ [I] 写作
```

## 阶段索引（一句话 Goal + 验收 + 依赖）

| Phase | 章 | Goal（一句话） | 状态 | 依赖 | GPU |
|---|---|---|---|---|---|
| **A** | Ch2 | 判别式 `supervised` 关系抽取器 | ⚠️ 召回已解，F1 低于官方同底座基线 → [`results/PHASE_A.md`](../results/PHASE_A.md) | P0 | 重 |
| **A2** ⭐ | Ch2 | 按**官方 baseline 配方**重训（关下采样 / 无类权重 / 分离 LR） | ⬜ **当前队首** —— 契约与交接见 [`PHASE_A2_ch2_official_recipe.md`](PHASE_A2_ch2_official_recipe.md) | A | 重 |
| **B** | Ch2 | 全局一致解码 + 可追溯修复 + CRC 风控准入 | 🟡 违反清零、下游无增益（止损已触发）→ [`results/PHASE_B.md`](../results/PHASE_B.md) | A | 轻 |
| **C** | Ch1 | 证据+不确定性规范事件节点 | ⚠️ 难例误合并大幅改善，MUC 未到官方基线 → [`results/PHASE_C.md`](../results/PHASE_C.md) | P0 | 轻 |
| **C2** | Ch1 | 跨文档泛化（ECB+/CLES） | ⬜ 未开始；对比 SECURE/MEET/DIE-EC | C | 轻 |
| **D** | Ch3 | 构建图上事实性检测 + 事实性驱动净化 | 🟡 检测达标、净化止损 → [`results/PHASE_D.md`](../results/PHASE_D.md) | P0(+B) | 轻 |
| **E** | Ch4 | 构建误差的传播、归因与预算（headline） | 🟢 已完成 → [`results/PHASE_E.md`](../results/PHASE_E.md) | A·B·C·D | 重 |
| **F** | 跨章 | 端到端误差预算（union bound+可达性） | ⬜ **暂缓**：风险地板由 Ch2 召回决定，Ch2 不抬则只是重述地板 | B·C·D·E | 轻 |
| **H** | 全篇 | 多种子 + 消融补齐 + 投稿前新颖性扫 | ⬜ **等一个值得背书的结果**（多种子不给平结果盖章） | A–F | 重 |
| **I** | — | 论文写作（非代码 phase） | ⬜ 等主实验 | 全部 | — |

> **数字不在本表**：一律见 [`../results/`](../results/README.md)（单一事实源）。当前队首见
> [`../TODO.md`](../TODO.md)「下一步」。

> 后段（C2/F/H）细节随前段真实结果再细化——文件先给 Goal/Steps 骨架，执行前按当时产物补全。
> 编号 A–I **刻意不重排**（大量文档引用字母编号）；G 已于 2026-07-27 整体移除，无对应 phase 文件。
