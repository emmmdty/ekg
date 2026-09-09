# EKG 实时状态

> 更新于 **2026-09-07**。新会话先读 [`HANDOFF.md`](HANDOFF.md)；数字以
> [`results/`](results/README.md) 为唯一事实源。

## 当前正式活动阶段

`R1 方法设计准入`。A3 已用不可变 bundle `a3-v6-20260905-r17` 正式 `failed` 交接；工作点、近似
retriever、prototype、ATLoss 均封存，不追加 seed 或调参。R1 尚未放行任何 proposed GPU pilot。

## 下一步

1. P1 r15 仍是可信根；A3.6 四臂全部完成并通过 metadata、单变量、人口、evaluator、final-valid 与
   双端 artifact hash 校验。旧方法最高 causal F1 仍未过主锚，权威数字见
   [`results/PHASE_A.md`](results/PHASE_A.md)；
2. 当前 R1 三章状态：Ch1 power PASS，mention-local input/baseline blocker 已由 `qwen3-argument-s13-r2` 闭合，
   T020 因果 brief 已于 2026-09-07 由 E4 审查 PASS（仅设计轴）。**同日作者裁决把 Ch1 门按四条措辞重新界定**
   （独立发表机制 · 原始基准上强 · 我们冻结协议下跑通 · 缺口写明）。**E10 已核查 ACCI：官方仓库只有
   README，占位而非实现，故 `not_runnable`、不排训练或 GPU，Ch1 第二方法族门仍需作者另议**；
   `qwen3-argument-s13-r2` 重定义为「朴素池化论元会掉点」的注册负面对照；
   **IP&M 2024（MUC 86.1 / causal 37.4，无代码、口径未核实）的核实前置为 E9，排在 E6 之前**；Ch2 power PASS，自建
   TacoERE **透明适配**档 `taco-s13-r3` 已按预注册规则选定并评分（causal 32.01 未过主锚 33.17），但它不是
   官方复现；T021 因果 brief 已于 2026-09-07 由 E3 审查 PASS（仅设计轴）。**同日作者裁决重新界定 relation
   baseline 门**：近期方法无一发布可跑官方 trainer，故回到 QR-001 措辞「第二个不同方法族 · 我们跑通 ·
   缺口写明 · 不弱于主锚」，由 **E8 的 LLMERE-causal 透明适配**承担（缩小到 causal-only，与文档队列并行）；Ch3 五折 OOF baseline、pooled power 与 T022 因果 brief 均 PASS；
3. Ch3 RoBERTa+CLS / DMRoBERTa 的 10/10 个后台任务已完成，80 个产物重哈希、fold 互斥/覆盖、训练源
   隔离与独立指标重算均通过。远端 run root 为 `runs/stages/R1/r1-v61-factuality-oof-r2/`，精确数字与
   acceptance hash 只见 [`results/PHASE_R1.md`](results/PHASE_R1.md)；
4. **T023 已于 2026-09-07 由 E5 完成并 `pass`**（`findings` 0，35 条需求全部映射，六个产物身份全 `frozen`）。
   09-06 漂移已溯源到 `f6966a0` 同一会话并按「先溯源→再纠正内容→最后动哈希」裁决完毕。
   ⚠️ E5 另查出 **A4 与 C5 两份 phase 契约的 roster 与 §13/§15 裁决矛盾，E6 必须改内容不能只补哈希**。
   **E9 已证我们的官方 joint 复现忠实于官方发表口径**（共指四指标与官方论文 ±0.4 内），
   IP&M 2024 全文不可得、进不了 roster、不阻塞 A4 契约；**E6 已完成 T024 的获准 phase 冻结**：
   A4/D4 的契约均已 hash-bound，C5 因 ACCI `not_runnable` 与无替代作者名单而显式
   `blocked_pre_admission`、不绑定草案。A4/D4 仍须完成各自实现、本地 gate、preflight、CPU/CUDA smoke
   与重新核卡后才可启动 seed-13 pilot；**E7 已补齐 relation 与审计代码身份**：两档 TacoERE run 分别绑定
   各自训练时的 `supervised.py` hash，R1 protocol 已冻结 `audit_r1_consistency.py` 并由审计自检；
5. 当前依赖计划：R1 后开展 C5 mention-local argument uncertainty、A4 full-candidate pair-evidence
   sufficiency 与 D4 typed-cue factuality；没有额外依赖时可重排或并行，三者 handoff 齐备后进入 E3。
   这是可修订 plan，不是 SPEC；
6. 4090/5090 当前可用于互不冲突的**准入 baseline smoke/OOF**；长任务继续 `setsid nohup`，不依赖 SSH
   存活。多种子与跨机 checkpoint 搬运仍须另行授权。
7. **执行队列与交替推进约束见 [`HANDOFF.md`](HANDOFF.md) 任务 E**：~~E1 关 Ch2 TacoERE 适配档的账~~
   ~~→ E2 核查 LLMERE 官方实现~~（均 2026-09-07 `done`；E2 裁决 `conditionally_runnable`，
   LLMERE 无官方 trainer，**不关闭** Ch2 第二 baseline 门；~~E3 写 T021 Ch2 因果 brief~~ 同日 `done`，
   审查 PASS；~~E4 写 T020 Ch1 因果 brief~~ 同日 `done`，审查 PASS，并留下 Ch1 QR-001 名单裁决
   ；~~E5 跑 T023 跨产物审计~~ 同日 `done`，审计 `pass`；~~E9 核实 IP&M 口径~~ 同日 `done`，
   全文不可得、改用官方论文数字做等价对照，**A4 契约已解锁**；~~E10 ACCI 静态核查~~（同日 `done`，
   仓库全历史仅 README，`not_runnable`，不排 GPU；C5 baseline roster 需作者另议）→
   ~~E6 T024~~（A4/D4 已 hash-bound；A4 的 LLMERE-causal 以「已规格化、数字 pending」入 roster；
   C5 仍缺第二方法族，已明确 `blocked_pre_admission` 而非伪冻结）→ ~~E7~~（两档 relation run 已分别
   绑定历史 `supervised.py` 身份；审计脚本已纳入 R1 `code.files` 并自检）→ **E8**；
   **E8 LLMERE-causal generation** 只写自己的 namespace。作者已于 2026-09-09 明确授权，在其后台运行时并行推进
   **E11 D4.0–D4.2**（实现、本地 gate、immutable preflight、CPU/CUDA smoke）；未逐项通过前不得启动 D4 seed-13 pilot，
   不得启动额外 seeds。Claude 与 Codex **轮流**持有同一条队列，任何时刻只有一个活动任务，例外与实际排期以
   `HANDOFF.md` E.0/E.2 为准；
   开工前 HEAD 必须等于 `origin/main`，交接必须已 push。

## 当前三端

- local：`main`；P1 r15 `1e31a9ac…f9655`；A3 handoff protocol `c187bf03…9359e`；Ch3 OOF 训练提交
  `277b36f`，collector 已提交到 `6532264`；最近代码门 **520 passed / 24 skipped**、ruff 0、smoke OK；
- 4090：A3.6 与 Ch3 OOF 进程均已 GONE；E8 的专用 CUDA venv、固定 LLaMA-Factory 与约 15GB 的未设门
  Llama-3-8B 镜像权重已落在 `llmere-causal-s13` namespace，均未搬运也未污染项目 `.venv`。模型下载虽有
  Xet 自动续传，最终完整；R1 protocol 已双端验 SHA 后，E8 的 seed-13 LoRA SFT 已完成 18,138 steps，adapter
  留在原 namespace。prediction-only 第一次续跑安装 `jieba` 后仍因 LLaMA-Factory 生成预检缺 `nltk` 停止，未产生
  推理、评分或指标；已核实该版本需整个 metrics extra，并固定 `jieba/nltk/rouge-chinese` 三项。当前 PID
  `1819697` 已在 GPU0 执行 11,149 条逐条 generation（约 13.5 秒/条），结束后才一次性写预测文件、转换和评分；
  不会重训或覆盖半成品。2026-09-09 核卡：GPU1 空闲；GPU2–3 由既有 vLLM 服务占用，服务不得触碰。D4 只可在
  实现、preflight 与 smoke 全部通过后使用届时真正空闲的一张卡，checkpoint 与 OOF 既有产物仍留在各自远端 run root；
- 5090：可连接；既有 Qwen 与其他 Python 服务保持运行，使用前重新查询动态显存占用，服务不动、
  checkpoint 不搬。R1 尚未放行 proposed pilot；可在具体 baseline 命令和协议冻结后使用，不为占卡
  启动无效训练。

## 禁止

- 未授权额外 seeds；使用 final-valid 选模；不同 candidate/evaluator/split 直接比较；
- 把 Ch1 event-level argument oracle 或 Ch3 gold-evidence oracle 当方法分；
- **看到某个选模规则能救分再改选模规则**（选模轴伪影，Phase C 教训）；
- 未询问就跨机搬 checkpoint、数据集或其他大文件；
- `rsync --delete`、远端 `git clean -fdx`、服务器 `uv run`/`uv sync`；
- 复活已封存方案（工作点、近似 retriever、prototype、ATLoss），或用更大 backbone 掩盖机制无效。

## 成功条件

Ch1–Ch3 必须在统一公开主指标上超过多个同协议方法；否则只能作为系统组件。所有结论必须可从
结果表追溯到 commit、manifest、candidate、evaluator、命令、checkpoint 和 hash。三方法章 + 一系统章
不预设降标；旧机制失败后只有通过 R1 的实质不同方法家族才能重开，不能以换名、扫参或更大 backbone
绕过止损。
