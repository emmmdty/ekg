# Findings & Decisions: v6 论文方向重审

## Requirements

- 目标为 3–4 章硕士论文，主题是事件图谱或事理图谱的构建及风险监测应用。
- 只用公开数据集，不做人工标注；单卡 RTX 5090，约 27GB 可用显存。
- 每章须有独立方法贡献，并在公开可比主指标上超过多个经典及近两年已发表方法。
- 全篇须闭环、自洽；职业倾向 LLM/Agent 工程，但不能为迎合而硬凑。
- 跨语言和供应链/大宗商品风险均为待证据评估的提议，不是既定约束。
- 先完成证据探索与项目决策，之后才能提出章节方案。

## Research Findings

### Phase 13 independent P1 re-validation (2026-08-28)

- Scope is frozen to six layers: active policy, raw data/manifests, official evaluator, baseline adapters, immutable
  stage bundle/remote evidence, and the exact A3 handoff. Existing PASS fields are treated as claims to recompute.
- Initial policy/bundle inventory is internally aligned on `global=pass`, `A3 entry=pass`, `primary_anchor=null`, and
  `v6_confirmatory_eval_count=0`. A3.0 is permitted, but method pilot/three-seed/final-valid execution is not yet allowed.
- P1's four-file bundle intentionally has no separate `hashes.json`; hashes are nested in `protocol.json`. An audit
  command incorrectly requested a fifth file and failed only on that nonexistent path; this is not a bundle defect.
- Highest-risk checks for the next pass are: recompute every source/manifest/candidate hash outside the generator,
  verify whether the bundle reader checks current external files or only stored artifacts, and prove the 10-doc/longest
  remote fixtures belong to frozen internal-dev rather than final-valid.
- Raw schemas support an independent audit: ERE and FACT each expose stable document IDs and event mentions; FACT adds
  per-mention factuality/evidence. The frozen manifests persist full ID lists, source path/hash/count, deterministic split
  rule, and generation-script hash; support counts cover ERE relation/coreference and FACT label/evidence populations.
- The first manifest inventory was too verbose and tool output was truncated, but files were not modified. Subsequent
  checks will load JSON programmatically and print only mismatches/summaries rather than full ID arrays.
- Independent raw-data recomputation PASS: all four source hashes, unique IDs, ERE/FACT train+valid alignment, train vs
  final-valid disjointness, deterministic 291/2,622/710 split, six manifest contents/self-hashes, processed-manifest
  portability, all ERE/FACT support counts, and all three candidate/label digests exactly match stored records.
- Fixture provenance PASS: all frozen 10-doc IDs are internal-dev-only, their gold records equal raw ERE train records,
  and the 1,723-source-token longest document is independently reselected from the same 291-doc dev set.
- Material automation gap: `validate_stage_bundle` verifies only the three in-bundle artifact hashes and prediction IDs;
  it does not resolve/re-hash the data, manifest, evaluator, config, code, or checkpoint entries declared under
  `protocol.hashes`. `build_p1_bundle` also treats any remote JSON with top-level `status=pass` as P1.6 PASS without
  validating its schema, local prediction/log hashes, fixture provenance, return codes, or skip counts. Current evidence
  remains factually valid because this audit recomputed it independently, but the automated gate is weaker than SPEC/P1.
- Official-source provenance currently checks out: checkout HEAD is the frozen `ac81a971…`; only the four declared
  compatibility-patch files are modified; patch diff is limited to AdamW import and AutoModel loading; checkout and
  persistent evaluator files share the frozen `32919e86…` hash; patch hash matches source lock and source diff is clean.
- Existing scorer tests cover gold expansion, missing/duplicate IDs, unknown endpoints, duplicate/conflicting pairs, and
  candidate digest drift. The strict validator implementation also rejects self-pairs and exact subtype-schema drift,
  but those latter paths need explicit test coverage to satisfy the written P1 rejection roster mechanically.
- Independent scorer replay PASS in a fresh temp directory: 710-doc gold-self, four adversarial fixtures, and candidate
  digest reproduced; generated gold predictions and both metrics files are byte-identical to the frozen P1 artifacts.
- Baseline adapter audit found a latent observability risk: official dump scripts order mentions by `(sent_id, offset[0])`,
  while the frozen local candidate protocol adds `mention_id` as a tie-breaker. Because P1 feeds constant-NONE vectors,
  all three outputs are empty and strict schema validation cannot detect an ordering mismatch. The next check must count
  tied trigger starts and compare full official/local pair order; any mismatch is an A3 pre-training blocker even though
  it does not falsify the empty-schema output itself.
- Full 3,623-document order audit resolves that risk for the frozen corpus: zero documents contain tied event-trigger
  starts, so official `(sent_id, offset)` and frozen `(sent_id, offset, mention_id)` orders are identical in train,
  internal-dev, and final-valid. Explicit self-pair, missing subtype, extra document, and repeated-coref tests all reject.
- Three-adapter replay in a copied protocol root PASS. All fixtures, predictions, and per-adapter smoke files are
  byte-identical; `smoke_summary.json` differs only because `compiled_entrypoints` truthfully records the temp absolute
  paths. Removing that environment-dependent field yields exact structural equality. This path field is diagnostic and
  not part of candidate/scorer semantics.
- Current bundle-to-local-evidence reconciliation PASS for all resolvable artifacts: internal artifact hashes, registry
  pointer, four raw sources, six manifests, evaluator, preregistration, twelve code files, source lock, returned remote
  predictions/logs, strict schema, and logged doc/relation counts all match.
- Handoff completeness defect confirmed: the P1 bundle's `hashes.candidate` and top-level `population_counts` describe
  only the 10-doc smoke (`313ec48e…`, 10 docs/6,508 pairs). The full A3 train/dev/final-valid candidate protocol hash
  (`2102c325…`) and per-split digests/counts exist only in the mutable registry/file and are absent from the immutable
  bundle. The access ledger likewise is referenced by path but not hash-bound. This violates the stated downstream
  handoff guarantee and should make A3 entry CONDITIONAL until fixed/rebundled, although the underlying files recompute.
- Local gate evidence is complete and reproducible (full command arrays, stdout/stderr, return codes); current code hash
  matches its bundle declaration. The ledger hash gap is not a false result today, but it prevents detecting later edits
  to the referenced access history from the P1 bundle alone.
- Fresh remote read-only recheck PASS after two banner timeouts and a successful third ControlMaster attempt: remote git
  commit/worktree, all three checkpoint hashes, both input hashes, both prediction hashes, both log hashes, and GPU 0
  UUID/driver/24,564-MiB identity exactly match `remote_smoke.json`. No model load/inference was rerun; socket closed.

### P1.6 resumed 4090 audit (2026-08-28)

- A bounded explicit ControlMaster loop reached `gpu-4090` on attempt 5 after four SSH banner timeouts. The public
  cpolar endpoint is intermittent; the established socket `/tmp/ekg-gpu4090-%C.sock` is now reused for all commands.
- The server exposes four idle RTX 4090 GPUs. Remote and local code are both commit `c642bb88`; the remote worktree is
  clean, torch is `2.8.0+cu128`, transformers is `4.53.3`, and CUDA is available.
- `runs/relations/supervised_maven` exists; its config/heads/model SHA-256 values begin `907d8b4e`, `f2de4bc8`, and
  `7b520c26`. The preferred historical `runs/relations/window_dist_20ep_macro` directory is absent on this machine,
  so a successful smoke can establish only interface/resource compatibility, not best-model quality.
- The 4090 also has `a4090_accum8` and `a4090_ctrl_accum1` heads of 5,876,280 bytes, matching the current two-layer
  distance-aware `PairClassifier` scale. By contrast `supervised_maven` is a 150,004-byte legacy head; the existing
  engineering note already states it cannot strict-load under the current architecture. P1.6 must select a compatible
  historical head rather than intentionally exercising the known-incompatible legacy checkpoint.
- Both `a4090_*` heads strict-match the current state-dict schema, including `distance.weight [11,32]` and the three
  2-layer family heads. `a4090_ctrl_accum1` has an auditable training log and the stronger recorded internal-dev macro-F1
  (0.3275 vs 0.3109), so it is the selected 4090 compatibility-smoke checkpoint. This selection is not a new tuning run
  and its score is not promoted as a v6 baseline result.
- Real GPU forward passed on RTX 4090 GPU 0 with the frozen longest internal-dev document (1 doc, 226 predicted relation
  pairs, 11.2 s wall time) and the frozen 10-doc fixture (10 docs, 1,861 pairs, 6.7 s). Both runs strict-loaded
  `a4090_ctrl_accum1`, emitted no skipped-document warning, returned zero, and left no persistent GPU allocation.
- The four remote outputs/logs were copied back with matching SHA-256. The 10-doc prediction has 10 JSONL records
  (`3edc90df…`); the longest prediction has 1 (`cb6ed24e…`). Checkpoint weights remain on the 4090 as required.
- Local strict validation passed for both outputs: the 10-doc candidate digest is the frozen
  `313ec48e657374bc5afb7d09df9282c32f1d7a3acfdbfe1bc35435765042df3c` with 10 docs/232 event mentions/6,508
  ordered relation candidates; the longest digest is `35971064…` with 1 doc/47 mentions/2,162 candidates. Both logs
  contain no skipped-relation warning. These are schema/resource checks, not scored baseline results.
- The rebuilt P1 bundle passes the real reader with `global_protocol_status=pass`, `a3_entry_status=pass`, and no
  remaining condition. It retains `v6_confirmatory_eval_count=0` and `scientific_scores_produced=false`; P1 completion
  therefore authorizes A3 baseline execution without claiming any new model result.
- Active-state documents now mark P1 completed and A3 active. The original G0 conditional verdict is retained only as
  an explicitly superseded 2026-08-27 static snapshot; current authority is the PASS P1 bundle/result record.

- Claude 已完成的本地盘点表明：现有约一万行代码中，真正随任务重开而基本作废的约 2,000–3,000 行，而非全部代码。
- `core/calibration/`、`core/eval/` 等任务无关统计与评测资产可迁移；CCKS 中文因果适配已验证 schema 的跨数据集/跨语言复用性。
- 磁盘上已有 15 个归一化数据集，但 split 合规性和计数尚未复核，不能据此直接选题。
- `agents/` 仅 176 行且无测试；若选择 LLM/Agent 路线，现有工程基础接近从零开始。
- Claude 上轮 A–E 外部探索均未完成，当前没有可用于方向决策的外部证据报告。

## Technical Decisions

| Decision | Rationale |
|---|---|
| 使用论文一手来源、官方数据页/评测器和官方 GitHub 为主 | 避免口径混用与二手转述造成方向性误判 |
| 所有数字必须记录表号、split、评测脚本和指标定义 | 项目曾四次因评测口径不一致而误判 |
| 严格串行执行 A → B → C → D → E | 作者要求避免并发造成额度不足；已中止 B、C，仅保留 A |
| 将 B/C/D/E 与 A3b 改写为四份网页版深度研究任务 | 大范围论文/数据/招聘/代码网页搜索适合深度研究；Codex 负责回收后的严格核验与本地资产映射 |

## Issues Encountered

| Issue | Resolution |
|---|---|
| 上轮代理产物写入会话级 scratchpad，额度中断后丢失 | 本轮每路独占一个 `docs/replan/*.md` 持久化文件 |
| A 路一次覆盖 Block 1 + 7.1 时长期无工具边界、无落盘 | 将每路进一步拆成可独立验收的小子块，优先交付证据而非追求一次性覆盖 |
| `HANDOFF.md` 中保留“4090 不可达”的旧时点背景，而仓库 `AGENTS.md` 记载 4090 已恢复 | 当前阶段不运行 GPU；后续任何 GPU 动作以最新 `AGENTS.md` 和实测 `nvidia-smi` 为准，5090 逐次询问 |

## Resources

- `docs/replan/HANDOFF.md`
- `docs/replan/EXPLORATION_PROMPT.md`
- `docs/replan/LOCAL_ASSET_INVENTORY.md`
- `.claude-session-handoff.txt`
- `docs/replan/DEEP_RESEARCH_PROMPTS.md`

## Browser Findings

- A1 报告已落盘；ACL Anthology 页面确认 TextEE 为 Findings of ACL 2024、页码 12804–12825、
  DOI `10.18653/v1/2024.findings-acl.760`，摘要明确说明其统一 16 个数据集、14 个方法，评测
  5 个 LLM 且表现不理想，并把泛化、事件覆盖和效率列作未来挑战。A1 对该来源的用途与元数据一致。
- 首轮直接 `open` 多个 URL 的工具调用没有返回可见正文；改用定向搜索后取得 ACL Anthology
  一手页面。后续抽查采用“定向搜索定位 → 打开官方 PDF/页面”的方式，不重复空返回做法。
- 官方 PDF 抽查确认 A1 对 Simon et al. 2024 §4 的引文、文档级/语义评测主张和英文数据偏置
  定位准确；Lee et al. 2025 Appendix F 确实提出生成式 temporal IE 仍欠探索、结构化输出需专门
  设计、公共隐藏 test benchmark 和评测实现差异等问题。
- 使用共享 PDF 工具环境直接读取 arXiv `2411.10371` 后，确认 ECI survey §8.7 原文确实写有
  `causal halluciantion and self inconsistency of LLMs`（含原文拼写错误），A1 的章节、页码和
  “原文拼写如此”说明准确。
- A2a 初稿对 Wei et al. `2024.findings-emnlp.1` 和 Min et al. `2024.acl-long.164` 的定性结论
  与 ACL 原文一致：前者同表显示 LLM 全面落后监督 baseline，后者明确把 GPT-4 作为摘要器与
  RoBERTa-large 协同，且 GPT-4 direct 在 GVC/FCC 受输入/输出截断。
- 但主代理检索发现 A2a 未纳入两篇标题直接相关的论文：`2024.emnlp-main.1136`
  *Will LLMs Replace the Encoder-Only Models in Temporal Relation Classification?* 与
  `2024.lrec-main.1348` TacoERE。它们可能提供 fine-tuned LLM 或混合方法的正证据，必须补核后
  才能接受“没有被拉平子任务”的结论。
- 定向补核后，结论被收窄但未推翻：TRC 的 direct ICL 和监督 LoRA 在 MATRES/TIMELINE/TB-Dense
  均未超过 fully trained RoBERTa；Llama-2-13B LoRA 在 MATRES 接近。冻结 Llama-2-70B 表征只在
  TIMELINE 胜过冻结 RoBERTa 表征，仍远低于 fully trained RoBERTa。TacoERE 只证明压缩流程改善
  同一闭源 LLM，因随机 50 篇来源、聚合/evaluator 和代码缺失，不能跨表与小模型比较。
- `git diff --check` 对未跟踪文件不会检查内容；主代理改用 `git diff --no-index --check /dev/null <file>`
  才发现三处 Markdown hard-break 尾空格。已改成空 blockquote 行，消除尾空格；后续新报告统一用
  `--no-index --check` 验证。
- A2b 初稿核实 EventRAG/CALLMSAE/CGEL 确为 2025 正式方法，并正确区分通用 QA/memory benchmark
  与 event-specific graph benchmark；但主代理抽查发现遗漏 CGEP（`2024.findings-emnlp.45`，本项目
  SeDGPL 的原始任务）、CausalGraphBench、CausalGraph2LLM、TAG-EQA。后三者可能不是事件图任务，
  但必须显式核实和排除；CGEP 至少应进入事件因果图下游任务边界。
- A2b 补核后的准确边界：CGEP 是 occurrence-level event-causality graph 上的固定后继事件排序任务，
  TAG-EQA 是 TORQUESTRA gold event graph 上的 QA setting；二者证明 graph-conditioned event reasoning
  任务确已存在，但只监督最终事件/答案、缺 gold proof trace，且官方发布分别缺派生数据。
  CausalGraphBench/CausalGraph2LLM 虽有完整公开 evaluator，但节点是 causal variables，不属事件图。
- A3a 的可审计标题下界为 Tier EKG 2024 ≥5、2025 ≥6，只支持“稳定/轻微增加”，不能声称显著
  升降；2026 仅 ACL/Findings 为部分年份。清单显示主题正被 EventRAG、LLM event reasoning、
  multi-document event-relation graph summarization 与 event-centric agent memory 等标签吸收。
- A3a 未完成 AAAI/IJCAI/WWW/SIGIR/CIKM 全量官方目录审计，因此这些 venue 只能标未核实；
  structured-event 的年度下界也不可相减为降幅。TKG、变量 causal DAG、通用 episodic memory 和
  内部 graph encoder 已作为 false positives 明确排除。
- DR-B 原始报告已回传为 `docs/replan/B_datasets.md`（284 行）。初检发现正文大量保留网页版
  内部 `cite…` / `filecite…` 标记，离开原会话无法解析；顶部 `sandbox:/mnt/data/...`
  链接也不可移植。内容需先恢复为实际 URL/论文 ID，才能满足一手证据审计要求。
- 作者补充导出了 `docs/replan/B_datasets.pdf`（19 页，WeasyPrint 生成）。PDF 的可见表格虽有
  右侧截断，但不是扫描件：正文文本层完整保留，引用转成编号脚注；链接注释共 237 个，含 43 个
  唯一 URI，其中排除 ChatGPT 首页和失效 sandbox 下载链接后有 41 个唯一真实 Web 来源。
- 因此 B 可采用“原 Markdown 提供未截断表格和完整正文 + PDF 注释提供真实 URL/引用映射”的组合
  审计，不必让深度研究模型重做或重写报告。`DR_B_CITATION_REPAIR_PROMPT.md` 仅保留为备选，不再
  是启动 DR-C 前的硬阻塞。
- MAVEN-ERE 的两篇 `original valid as new test` 先例已由官方 PDF 原文复核：Chen et al.
  ACL 2024 Appendix E 明写 original train 按 8:2 重分并以 original valid 作新 test；LLMERE
  COLING 2025 Appendix C 明写 `Following Chen et al. (2024)` 采用相同设置。B 的这项核心结论成立。
- B 的 MAVEN-ERE 独立团队计数存在至少一处明确错误：KnowQA 作者 Zimu Wang 同时是 2022
  MAVEN-ERE 数据论文作者，不能按报告定义计作独立团队。当前六篇清单中可直接确认独立的只有
  Chen 2024、Wei et al. 2024、LLMERE 2025 三组；TacoERE、KnowQA、MMD-ERE 均与原团队
  作者重叠。因此 `独立团队 ≥4` 尚不成立，可信下界暂为 `≥3`，除非另述 2025 directional causal
  论文经正式发表、实际使用数据、作者不重叠三项复核后可补为第四组。
- MAVEN-ERE 官方 CodaLab 页面当前仍返回完整 HTML，显示 `Competition Ends: Never`、Participate
  页要求登录、Public Submissions 路由以及历史 submission chart；官方 README 也称其为 permanent
  competition。但未登录无法证明新上传和 scorer 实际运行，所以 B 的“页面/榜单可访问、提交能力
  未验证”边界准确。
- LDC2006T06 官方 catalog 明确写 corpus 有英/中/阿三语，但 event tasks 仅英/中评测，并受 LDC
  User Agreement 约束；B 对 ACE05 语言范围与非开放许可的结论成立。
- 进一步取得 Findings ACL 2025 `2025.findings-acl.43`：Xiang et al. 作者与 MAVEN-ERE 原团队无
  重叠，正式使用 MAVEN-ERE 因果子任务。因此 B 的独立团队数 `≥4` 可保留，但必须用它替换错误计入
  的 KnowQA。该论文又采用 original dev 作 test、train 抽 10% 作 dev，说明评测口径至少四类。
- 已生成 `docs/replan/B_datasets_audit.md`，以“原始 Markdown + PDF 来源 + 本地更正”完成 B 的
  有条件验收。A 对 NYT-SEG、CGEP、TORQUESTRA 的一手审计强于 B，冲突处以后者的未核条目降级、
  以前者的明确边界为准。
- DR-C 原始报告已回传为 `docs/replan/C_methods_code.md`（326 行、约 46 KB）和 19 页 PDF。
  Markdown 仍含 100 个 ChatGPT 内部 citation token，但自身已有 10 个 URL；PDF 有 171 个 URI
  注释、25 个唯一 URI，排除 ChatGPT 首页后可恢复 24 个真实 Web 来源。继续采用“MD 完整表格 +
  PDF 来源链接”的组合审计，不要求重跑 C。
- C 的核心方法分型总体与 A 一致：direct prompting、监督 PEFT、LLM→SLM hybrid、cascade、RAG、
  true multi-agent 必须分开；SECURE 是 hybrid，CALLMSAE 是 cascade，EventRAG 是 graph→RAG，
  TAG-EQA 是单模型多 prompt，不能统称 multi-agent 建图。
- C 对 TextEE Tables 6–7 的证据等级疑似过高。A 的既有 PDF 审计已记录：250-document samples
  来自五个重采样 split 中哪一个、F1 micro/macro 聚合均未声明。因此表内差距可保留为强烈论文内
  趋势，但按本项目四轴规则不应标成“A：严格同轴/公开主轴”；需在 C 审计层降级。
- C 的 GitHub 部分诚实披露：除 TextEE/OmniEvent 外大多没有 exact SHA，也未逐条检查 README
  路径或第三方复现；这没有完全满足 DR-C 原提示的 repo 审计深度。下一步只对影响路线的 10 个官方
  仓库做当前 API 元数据与关键缺文件复核，不把报告中的 `pushed_at` 当 commit date。
- LLMERE 官方 PDF确认：Table 2 定义 temporal/causal/subevent 为 micro P/R/F1、coreference 为
  MUC/B³/CEAFe/BLANC 平均 F1；Appendix C 是 8:2 + original-valid-as-test；LoRA rank 64、max
  length 2048，训练用 A100 40GB。论文把 LLMERE 52.5 与 ProtoERE 50.8 放在同表，但正文未明确
  说明 baseline 是从报告值搬入还是在新 split 重跑，且未指明可执行 evaluator/commit；故“论文内部
  正证据”可保留，暂不升级成项目所需的完全公开可复现实验轴。
- 当前 GitHub 一手快照确认：TextEE `567baa9b...`/61★/Apache-2.0，SECURE `f1f53275...`/12★/
  GPL-3.0，SeDGPL `265b19b...`/5★/无声明 license，CGEL 论文 URL 仍 404。C 遗漏的 LLMERE
  官方仓库实际存在：`HerbertHu/LLMERE`，HEAD `94d4ef27...`、9★、MIT、2025-02-01 最后 push；
  后续需检查其训练/evaluator/data 是否完整。
- LLMERE 仓库 tree 已静态核到：有 MAVEN-ERE/MATRES/HiEve 数据转换脚本、各任务 evaluator、
  示例 prediction/result；当前未见训练入口、依赖/环境锁、checkpoint，README 未提供可检索的运行
  命令。故它是“数据处理 + evaluator + 输出示例公开”，不是论文 LoRA 训练的端到端复现包。
- MMD-ERE 可由 ACL 官方元数据确认是 COLING 2025 正式论文、作者为 Yong Guan/Hao Peng/Lei Hou/
  Juanzi Li；官方 ACL 页面未给项目代码入口。本地残留 PDF 下载不完整、无法抽取，按不重复失败原则
  不再拉取。因此只保留“true multi-agent ERE 方法存在”，代码、硬件、完整数据/evaluator 统一标未取得；
  它也与 MAVEN-ERE 原团队重叠，不能作为独立团队证据。
- 第二批 GitHub 当前快照纠正 C 的多项动态元数据：OmniEvent HEAD 是 `ec72e727...`（不是报告的
  `130efaea...`）；CALLMSAE 是 4★、`pushed_at=2025-02-02`（不是 2★/2026-07-03）；EventRAG
  是 `pushed_at=2025-02-16`（不是 2025-07-17）；TAG-EQA 是 0★、`pushed_at=2025-11-09`
  （不是约 1★/2025-06-22）。DeepKE、MAVEN-ERE 的 star/pushed_at 与 C 一致。star 是动态信号，
  但错配的 pushed_at/HEAD 说明 C 的 repo 快照不能原样作为审计记录，必须由本地表覆盖。
- 已取得其余准确 HEAD：DeepKE `77083bf1...`、MAVEN-ERE `ac81a971...`、CALLMSAE
  `4a0f093e...`、EventRAG `96a9de96...`、TAG-EQA `fa3b0b9a...`、InstructUIE `052a536a...`；
  OmniEvent 为 `ec72e727...`。这些只证明仓库 HEAD，不证明 recipe 可运行。
- ACL Anthology 官方元数据确认 C 中五个通用 IE 方法条目的正式身份无误：IEPile 为 ACL 2024
  short、ADELIE 为 EMNLP 2024、KnowCoder 为 ACL 2024 long、KnowCoder-X 为 Findings ACL 2025、
  ASEE 为 Findings EMNLP 2025。C 对这些条目仍缺逐项 split/主表/硬件/commit 审计，只能保留为
  候选方法地图。
- 已生成 `docs/replan/C_methods_code_audit.md`，对 DR-C 作有条件验收：分类边界和方法工程包络可用；
  TextEE 降为 sampled 同论文趋势，LLMERE 降为非官方 split 下的论文内部正证据，SECURE 保留为
  严格 hybrid 正例；CGEL/MMD-ERE 不作为成熟可复现 benchmark。原 GitHub 表由准确 HEAD 与缺件
  清单覆盖。
- DR-D 原始报告已回传为 `docs/replan/D_angles.md`（208 行、约 52 KB）和 19 页 PDF。Markdown
  含 173 个 ChatGPT 内部 citation token、0 个可移植 HTTPS URL；PDF 是 WeasyPrint 生成的可搜索
  文本 PDF。后续沿用“Markdown 取完整正文/表格 + PDF 注释恢复真实 URL”的组合审计，不修改原文。
- D 的 PDF 共 246 个 URI 注释、38 个唯一 URI，剔除 ChatGPT 首页后可恢复 37 个真实来源；主要是
  ACL Anthology、数据许可页和官方 GitHub，来源形态足以进行定向一手复核，不需要重跑 DR-D。
- D 的待核高影响结论有三组：① MEE/MINION 是多语言 EE/迁移而非跨语言现实事件节点 identity，
  MCECR 的相关报道检索限制在 seed 同语言，MEANTIME 则主要是平行翻译；② CrudeOilNews 虽贴合
  大宗商品事件，但官方仓库因版权只发 URL/annotation 而不发原新闻正文，现有结构化风险数据库也
  未形成固定 NLP event→risk benchmark；③ EventStoryLine/Causal-TimeBank 上的 ECI 被报告列为
  当前最闭合替代，固定协议 MAVEN-ERE 次之。三组均需在 D 审计中逐项核一手 protocol/仓库和独立性。
- MCECR 官方 PDF 对 D 的决定性边界给出直接证据：各语种从 language-specific Wikinews dump 取 seed，
  Google 相关报道结果明确限制为与 seed article 相同语言（PDF p.3/抽取行 147–170），所以每个 topic/
  gold chain 不做 language-mixed same-event clustering；cross-lingual 是 train/test 跨语言迁移。另有约
  65% event pairs 由预训练模型自动高置信标注，只对自动标注抽样 10% 人工核验，应保留为数据质量
  provenance。D 对“不能用 MCECR 冒充跨语言现实事件节点对齐”的结论确认。
- ACL 官方页同时确认 CrudeOilNews 是 LREC 2022 正式资源：175 篇人工 seed、25 篇 adjudicated
  reference test，扩展后 425 篇/约 11K events，并链接作者官方 GitHub。正文公开性和 scorer 状态仍需
  继续查仓库 README，不能只凭论文的“made available”判断 raw text 完整。
- CrudeOilNews 作者仓库 README 已确认 D 的决定性公开性判断：因版权，original commodity news
  仅提供 URL 和对应 annotation、不提供正文；只有 augmented data 完整提供文本。仓库顶层当前只见
  annotations、guideline、license、README 和示意图，未见成熟 shared-task evaluator/leaderboard。
  因此它语义贴近 β，但不满足固定 raw input 的严格公开复现要求。
- ECI 正式身份复核发现待纠错点：ICCL 是 EMNLP 2024 `2024.emnlp-main.51`，LLM-knowledge/concept
  方法是 COLING 2025 `2025.coling-main.495`，而 `2025.emnlp-main.616` 的正式标题是 DECLV
  (*Dynamic Energy-Based Contrastive Learning with Multi-Stage Knowledge Verification*)，不是 DICP。
  D 报告同时把“DICP EMNLP 2025”和“DECLV 2025 同团队”分列，必须先查清 DICP 是否另有正式论文，
  否则独立近期团队下界可能被虚增。
- DICP 已由 ACL Anthology 确认为 Findings EMNLP 2025 `2025.findings-emnlp.139`，作者 Lin Mu 等与
  ICCL 的 Liang Chao/Wei Xiang/Bang Wang、COLING 2025 的 Ya Su 团队均不重叠；官方仓库也明确
  链接 EventStoryLine 与 Causal-TimeBank，并给出 preprocess/AMR/run 流程。因此 D 的“至少 3 个
  独立 2024–2025 正式团队”保守下界成立。表述上应将 DICP 精确写成 Findings EMNLP；DECLV
  `2025.emnlp-main.616` 与 COLING 方法共享 Ya Su 等作者，按 D 原意不能再计一个独立团队。
- PPAT 官方仓库包含 ESL v0.9/CTB 数据目录和 `stack5`/`ctb_stack10` 运行入口；ICCL 官方仓库存在，
  但 README 没有环境、数据下载、fold 或运行命令，仅有源文件。仓库存在性不能代替三篇近期方法的
  fold IDs、negative-pair generation 与 evaluator 一致性核验。
- ICCL、LKCER（COLING 2025）和 DICP 三篇 PDF 均明确使用 ESL 5-fold、CTB 10-fold，并报告 P/R/F1；
  ICCL 对 ESL 还固定 last two topics 为 dev，其余 20 topics 做 5-fold，CTB 只做 intra-sentence。
  DICP 明写 follows Liang et al. 2024，CTB 正/负采样 rates 为 5/0.3，并报告单张 RTX 3090、BERT-base。
  因此“近期独立方法持续使用同一 benchmark tradition + 27GB 高可行”成立，但尚未证明三篇使用完全
  相同 fold IDs/生成后的 pair 文件；D 将严格可比成熟度写成“中高、仍需锁协议”是合适的。
- EventStoryLine 作者仓库确有 annotated data、evaluation-format test、baseline/eval scripts，许可证为
  CC BY 3.0；但仓库同时区分 v1.0 expert、v1.2 crowd、v1.5 expert+crowd，而 PPAT README 写使用
  v0.9。故“ESL 公开”成立，“所有近期方法天然同一 corpus version/fold”不成立，最终实验契约必须
  固定 version、20-topic fold IDs 与 pair generation。
- Causal-TimeBank 作者仓库公开 CAT/TimeML 两个完整 ZIP（约 871 KB/相应 TimeML 包）并说明来源为
  TempEval-3 TBAQ-cleaned，含 6,811 EVENT/318 CLINK；但顶层未见显式 LICENSE。可以写“公开可下载
  研究资源”，不宜写成“许可已完全审计通过”。这使 D 对 ESL/CTB 的推荐继续保持有条件而非无条件。
- α 的正式资源身份复核与 D 一致：MEE `2022.emnlp-main.652` 是 8 语 entity/event trigger/argument
  EE；MINION `2022.naacl-main.166` 只做 multilingual event detection；EusIE
  `2024.lrec-main.586` 与 SPEED++ `2024.emnlp-main.720` 证明 multilingual transfer/EE 仍有正式活动。
  这些资源均不提供不同语言独立报道间的 same-real-event node identity gold，不能反驳完整 α 的断链。
- MEANTIME `L16-1699` 的摘要直接确认 480 docs 是 120 篇 English Wikinews 及其 Spanish/Italian/
  Dutch translations，非英语 annotation 主要从英文自动投射并基于人工 alignment；它有 cross-lingual
  coreference，但不是自然多语独立报道的 node resolution benchmark。SPEED++ 正式摘要则确认
  multilingual EE 可产生疫情早期 warning（中文微博、比全球讨论早 3 周）的应用验证；这证明
  event→warning 范式真实，不证明 commodity/supply-risk 已有多人共享 benchmark。
- 已生成 `docs/replan/D_angles_audit.md`，对 DR-D 作有条件验收：完整 α 因 natural cross-language
  event identity gold 缺失而不通过；β 因 fixed raw text/risk target/evaluator 链不闭合而不通过；
  ESL/CTB ECI 是当前最强条件性候选，固定协议 MAVEN-ERE 次之。DICP 精确更正为 Findings EMNLP
  `2025.findings-emnlp.139`；ESL 版本、exact folds/pairs、CTB license 作为后续硬边界。
## 2026-08-25：DR-E 原始报告接收

- 已收到 `docs/replan/E_industry.md`（181 行，51,985 字节）与
  `docs/replan/E_industry.pdf`（21 页，927,447 字节）。
- Markdown 含 170 个 ChatGPT 内部引用标记、17 个原始 HTTPS URL；PDF 可搜索且未加密。
  后续以 Markdown 正文为主、PDF 注释链接为引用恢复手段，原始文件保持不改。
- 当前只审计 E；E 通过后才进入 A–E 五路综合。

### 初读后的审计框架

- 报告的核心判断合理：event-specific 直接证据主要支持跨文档事件组织、结构化检索，
  以及给定事件因果/时间结构后的推理；provenance、增量更新、降幻觉、降成本仍主要是
  motivation 或一般 KG/GraphRAG/agent-memory 邻近证据。
- 报告主动区分 strict event graph 与一般 KG、GraphRAG、agent memory，也没有用工业价值
  反推学术 benchmark 可做性；这一边界与 A–D 审计相容。
- 需要重点复核三类易变证据：公司生产部署与规模自报、2026-08-25 招聘页面是否真实在岗、
  GitHub stars/releases/最近提交。它们最多支持“存在性/工程生态快照”，不能支持市场份额或趋势。
- 需要补读的正文中段：招聘样本表、开源项目快照表及其来源；PDF 共有 45 个唯一链接，
  其中包括论文一手页、公司官方页、招聘系统页和 GitHub/项目证据。

### E 中段补读结果

- 招聘表给出 15 个岗位条目，但 Inca Digital 同一职位重复用于两个技能类，故独立职位约 14 个；
  这不是市场抽样框，只能证明若干技能组合在抓取日存在。
- 最贴题的最小证据不是 Airbnb 的统计因果岗位，而是 Outreach 三个 KG/AI 岗位中共同出现的
  entity resolution、event detection、temporal modeling/reasoning、graph reasoning 与 production
  monitoring；若这些页面仍在线，可保留为“最低可证需求形态”。
- OSS 快照把 Microsoft GraphRAG、Graphiti 与 EventRAG/CALLMSAE/SeDGPL/TAG-EQA 分层；解释边界
  正确：stars/commit/release 只能表示工程生态与维护快照，不能替代生产采用率或研究价值。
- E 主结论暂定“有条件通过”：论文技术边界大体已由 A/C 复核，接下来只做少量高影响、
  一手来源抽样，不对 45 条链接逐条重复深搜。

### 在线抽样异常

- 浏览工具对 6 个官方直链批量打开、4 个定向官方域名检索均返回空结果；未据此把任何页面
  判成失效，也不把工具空返回伪装成核验成功。
- 后续改用轻量 HTTP 头/正文抽样；若网络仍不可用，则以 PDF 已恢复的一手 URL 和报告的
  保守限定为准，并将时效性数字降级而不是重复消耗检索额度。

### 官方页面可达性抽样

- Altana 美国政府公告返回 HTTP 200；Outreach 的 Staff 与 Director 两个贴题岗位页均返回
  HTTP 200。它们可以支持“官方页面在审计日存在”，但仍需从正文抽取关键词才能支持具体描述。
- Altana schema 文档遇到 SSL unexpected EOF，不能据此判失效；E 中“shipment 是 node”只能按
  PDF 已恢复的官方文档引用保留，并注明本地未二次读取正文。
- GitHub API 对 GraphRAG、Graphiti 均返回 403，属于 API 访问限制而非仓库失效；不重复请求。
  具体 stars/releases 作为 2026-08-25 报告快照保留，综合时不依赖精确数字。

### 官方正文与既有审计交叉结果

- Altana 2024 官方公告正文明确写平台已部署于美国政府多个场景，包括 CBP；因此“生产部署存在”
  可以确认。页面同时含当前公司自报的 5,000+ CBP agents，但该数字不是第三方效果审计，
  只可作为公司快照。
- Outreach Staff 页面正文确认 `entity resolution`、`temporal modeling`、`coreference resolution`、
  `relation extraction`、`event detection`、production monitoring/drift；Director 页面确认
  `temporal reasoning`、`event detection`、KG architecture、research-to-production evaluation。
  因而 E 对“存在一条高度贴题的 structured-AI 技能链”的表述成立。
- A/C 本地审计独立确认 E 表中的 EventRAG 21★、CALLMSAE 4★、SeDGPL 5★、TAG-EQA 0★及
  对应 commit/发布包缺口。E 没有漏掉 C 的关键更正，也没有把 stars 当采用率。
- Microsoft GraphRAG/Graphiti 的精确 stars、release 和日期未在本轮二次闭合；这些数字从最终
  选题决策中剔除，只保留“通用 GraphRAG/agent-memory 工程生态显著强于论文型 event repo”
  的定性快照，并明确不是学术价值判断。

### DR-E 最终验收

- `docs/replan/E_industry_audit.md` 已生成并通过结构/空白门禁：164 行、11,937 bytes、
  0 个 ChatGPT 内部引用 token、19 个 HTTPS 来源入口。
- 判定：**有条件通过**。E 提供技术存在理由与工业/人才边界，不提供新的主 benchmark，
  不改变 D 的候选排序。
- A–E 五路原始探索与决策关键交叉核验现已齐备；下一步进入五路综合与“重构 vs 重开”决策。

## 2026-08-25：五路综合初始交集

- 硬约束不是“方向看起来新”，而是每个方法贡献都要落在公开数据、固定 test/evaluator、多个正式
  对手和 27GB 可行的交集；C 已明确没有任何单一 LLM 方法自动满足这个交集。
- 当前最强主任务候选仍是 ESL/CTB 上的事件因果识别：问题价值明确，2024–2025 至少三个独立
  正式团队，同为 encoder-base 级工程；但 ESL version、exact folds/pairs、CTB license/evaluator
  必须先形成冻结协议。
- 固定协议 MAVEN-ERE 的优势是本地数据、loader、官方 evaluator、关系流水线和近年论文数量；
  致命风险是至少四种 evaluation setting 已分裂。它适合保留为复用资产或第二验证轴，不能再把
  不同 setting 的 headline 数拼成统一 SOTA 线。
- event coreference 值得进入最终候选表：SECURE 给出同代码、同 scorer 的 hybrid 正证据；本地已有
  MUC/B³/CEAFe/BLANC 与节点/共指模块，且 `data/raw/` 已有 ECB+。仍需用 A 的公开性/竞争证据限定。
- “重开”不等于丢掉近万行代码：Tier 1 的 2,263 行与工程制度几乎零损迁移，真实高耦合损失主要是
  succession 的 2,148 行及部分数据适配。最终决策应把“论文主轴重开”与“工程仓库推倒重来”分开。
- 初步方向倾向事件图谱而非事理图谱：现有公开任务、评测器和本地 schema 都围绕 occurrence/event
  mention 的身份、关系、事实性；eventuality/script/事理支线的共享 benchmark 与近期统一竞争轴更弱。
  该倾向仍需用 A 的术语与任务地形复核后定案。

### A 地形复核后的本体选择

- **事件图谱**节点承诺是可核验的一次现实发生，研究问题落在事件身份、参与者、时间、来源和事件间
  关系；**事理图谱**更接近 eventuality/script/narrative-evolution 的去情境化模式与通常后继。
- 2024–2026 一手综述明示的活跃卡点集中在事件抽取泛化、因果方向/链/不确定性、上游误差传播、
  完整时间图和统一评测；同窗口未取得合格的 script/narrative 专项 survey 或统一英文定义。
- 因而最终术语选择可以定为 **事件图谱（occurrence-level event graph）**：不是因“对手更弱”，
  而是它与公开标注本体、风险监测的实例级溯源需求和可复用代码一致。事理图谱不宜作为学位论文
  总题目，可保留为 CGEP/后继推理中的邻近表示背景。
- A 同时否决了把 EventRAG、CALLMSAE、CGEL、TAG-EQA 直接升为章节主轴：它们分别缺专门公开
  benchmark、许可/evaluator、公开代码或派生 test。CGEP 任务最接近公开 graph-conditioned 主轴，
  但只有原论文统一适配对手、缺独立 follow-up 且发布包不闭合。
- 这使“图上应用”更适合做统一研究闭环的后端验证，而论文的可比方法贡献仍应首先落在成熟的
  occurrence-level 构建子任务上，避免为了标题里的“图”自造主指标。

### 当前 v5 与外部硬约束的第一次对照

- Ch1 当前共指 MUC 曾距目标约 5–8 点，长上下文底座等路线已出现负结果；不能以 B³/CEAFe 高分或
  自造难例指标替代公开共指主轴。
- Ch2 判别式抽取解决了生成式召回崩溃，但最新记录的官方口径 causal 仍低于公开 RoBERTa/近年方法；
  全局一致修复可清零结构违反，却没有提升关系 F1 或下游可重建率。
- Ch3 事实性检测是现有结果最强的保留资产，但当前主结果在 valid、官方对手在 hidden test，
  “已经超过多个公开方法”的严格声明仍需同 split 复跑或可用 test 通道；图净化下游收益已止损。
- Ch4 的核心图侧干预全部落入 ±.003–.004 MRR 噪声地板；CGEP-MAVEN 公开派生数据又未发布，
  v5 用 CRAB/叙事完形补公开对手会混入不同模型规模、数据与消费者，不足以修复主轴。
- 因此“继续按 v5 四章补实验”与 A–E 地形冲突。更合理的候选决策是：**重开论文问题脊柱，
  保留并迁移代码/数据/方法学资产**，而不是在原四章上继续局部重构，也不是删除仓库重新开发。
  最终结论仍需逐读 `docs/results/` 的权威数字后确认。

### 权威结果复核后的 v5 判定

- Ch2 权威终点是 MAVEN-ERE valid、官方 evaluator 下 causal **28.50**，同一 valid 上官方原版
  RoBERTa 为 **31.37**；同时 subevent 从 24.03 降到 21.05。尚未达到一个强 baseline，更不满足
  “超过多个方法”。
- Ch1 权威、最干净的档是全 710 valid + 官方 evaluator 的 MUC **77.47**；79.6 是 497 篇子集加
  人群校正的内部口径，不应作为 headline。`docs/results/README.md` 的“一句话结论”写 MUC 79.6，
  与 `PHASE_C.md` 的权威口径冲突，综合一律采用后者。官方 test 基线 81.4 仍不同 split。
- Ch3 的规范主结果是 valid macro-F1 **.4823**；官方 DMRoBERTa 47.1 / DMBERT 47.6 在 hidden test，
  因而只能说“超过同底座官方数字的表面值/强候选”，不能据不同 split 宣称严格超过多个方法。
  事实性净化对结构和下游均为负结果，oracle 也为零。
- Ch4 唯一确凿正效应是 gold→predicted 的构建损失 −.0218 MRR；修复 +.0011、净化近零、距离选边
  +.0009 均落在噪声地板且无公开同轴 CGEP-MAVEN 对手包。它可作诊断性研究资产，不再适合作为
  “每章超多个方法”的 headline 章。
- 结论确认：**v5 四章没有一章在当前证据下无保留满足学位论文硬标尺**。应重开论文主轴；
  Phase D/Ch4 的负结果、所有 evaluator/loader/统计纪律继续保留为研究资产与止损证据。

### 候选任务矩阵的稳定排序

1. **ESL/CTB 事件因果识别：条件性主锚。** 至少三个独立 2024–2025 正式团队，公开 ESL 数据与
   eval 资产、共同 5/10-fold 大框架、BERT/RoBERTa 单卡可行；尚欠 version、fold IDs、pair
   generation、CTB license 与至少两个 baseline 的本地复现。
2. **冻结协议 MAVEN-ERE causal：复用型第二候选。** 近年论文和本地资产最多，但至少四套
   setting 分裂、hidden test 通道未实测；只能选定一种公开 valid 协议并把所有对手在同一代码路径
   重跑，不能引用混合排行榜。
3. **MATRES/TB-Dense 时间关系与 ECB+/GVC/FCC 跨文档共指：储备候选。** 问题与方法价值都在，
   但本轮没有完成统一 preprocessing/split/evaluator、官方下载许可和 2026 状态审计，不能与 ECI
   同等级进入立即实施。
4. **MAVEN-FACT：强保留资产、弱竞争主轴。** 数据规模和已有模型有价值，当前跟进方法下界不足且
   test/leaderboard 未闭合；更适合作为保留实验或图节点属性，不宜承担必须超多个方法的主任务。
5. **CGEP/TORQUESTRA/NYT-SEG/EventRAG：图上应用或存在性证据。** 各自缺独立 follow-up、派生包、
   evaluator、许可或专门 benchmark，暂不承担公开竞争 headline。
6. **跨语言事件身份、大宗商品/供应链风险、event-specific agent memory/GraphRAG：应用验证池。**
   问题价值可以很高，但公开 benchmark 闭环不足；不由工业需求反推学术主轴。
- 决策上必须承认：五路探索只找到了**一个**达到“条件性主锚”级别的任务，而不是已经拼出 3–4 章。
  所以本轮应提交“方向与重开决策”，作者认可后再做章节设计和针对性协议闭环，不能现在伪装成完整
  论文方案已经确定。

### 五路综合最终决策

- 已生成 `docs/replan/SYNTHESIS_DECISION.md`。
- 事件图谱 vs 事理图谱：选 **occurrence-level 事件图谱**。
- 重构 vs 重开：若二选一，选 **重开论文主轴**；工程上在当前仓库迁移重构，不推倒重写。
- 首要锚点：**ESL/CTB 事件因果识别**，状态是条件性主锚；固定协议 MAVEN-ERE causal 为第二候选。
- 风险监测保留为应用延伸，LLM/Agent 保留为方法与工程组件；二者都不反推公开学术主轴。
- 当前没有证据足以直接拼出 3–4 章；等待作者认可后，先过协议/双 baseline/27GB 三道门槛，
  再提出 2–3 套章节骨架。

## 2026-08-25：作者批准 ECI 资格验证

- 作者接受三个方向性决定，并同意先做低成本资格验证，不直接押注完整论文或启动重型 GPU。
- 外部检索部分继续交给网页版 Deep Research；本地只负责一手来源复核、协议静态/运行审计与
  go/no-go，保持严格串行。
- 已生成 `docs/replan/DR_F_ECI_PROTOCOL_PROMPT.md`，要求锁定 ESL/CTB 精确版本、folds、pairs、
  evaluator、license、两个独立近期 baseline 和 27GB 路径。

## 2026-08-26：DR-F 原始报告接收

- 已收到 `docs/replan/F_eci_protocol.md`（474 行、36,375 bytes）与
  `docs/replan/F_eci_protocol.pdf`（17 页、947,788 bytes）。
- PDF 由 WeasyPrint 68 生成，可搜索、未加密，含 62 个 URI 注释、11 个唯一 URL；Markdown
  含 85 个 ChatGPT 内部引用标记和 44 个可见 HTTPS URL。
- 后续以 Markdown 取完整正文/表格，以 PDF 注释与 Markdown 原始 URL 交叉恢复来源；原始文件不改。
- 报告标题和目录完整，已经覆盖 dataset/version、per-paper protocol、compatibility、repo、
  two-baseline、27GB 与 go/no-go；当前尚未接受其最终判定。
### 2026-08-26：DR-F 全文初读结论（待一手核验）

- `docs/replan/F_eci_protocol.md` 的正式结论是 **NO-GO**；当前仅记录该报告的判断，尚未接受为本地最终结论。
- 报告的核心否决依据主要是：未获得 Shen et al. (2022) 共用预处理工具的精确仓库/版本、fold manifest、候选对生成器和 evaluator；这属于“静态证据链缺失”，尚不等于已经证明四篇工作使用了不兼容协议。
- 报告没有识别 Shen et al. (2022) 的具体论文、仓库或工具入口，却把该工具链缺失作为主要否决理由；这是本轮本地审计首先要补的环节。
- F 与此前 D 审计存在三处必须用一手材料消解的冲突：
  1. DICP 训练硬件：D 记为单张 RTX 3090，F 记为 Tesla V100；
  2. EventStoryLine 许可：D 记为 CC BY 3.0，F 只识别到仓库 MIT；
  3. Causal-TimeBank 许可：D 记为无显式 LICENSE，F 称 README 为 CC BY-NC-SA 3.0。
- ICCL 与 DICP 是独立团队且都有公开仓库；若仓库实际包含准备好的数据、fold、候选对和统一 evaluator，F 的静态 NO-GO 可能需要上调。下一步直接检查官方论文与仓库内容，不改写原始 F 文件。

### 2026-08-26：DR-F 来源与 EventStoryLine 仓库初核

- PDF 共 62 个链接注释，但去重后只有 11 个 URL；其中没有 EventStoryLine、ICCL、DICP 的仓库链接，也没有 Shen et al. (2022) 的论文或工具入口。F 的正文虽然写出部分仓库地址，PDF 可追溯来源仍不足以支撑其最关键的工具链否决。
- 从官方 EventStoryLine 仓库新做的浅克隆显示，当前公开 HEAD 为 `46edefee5e82e0917b823abe0a18bf8c7770f15c`，不是 F 记录的 `2b6f420a...`；需进一步检查两者提交时间/历史，避免把动态 HEAD 差异误判为报告错误。
- 仓库根目录同时可见 `LICENSE.md`，数据子目录还包含 `COPYING-CC.TXT` 与 `LICENSEDATA.TXT`。因此“GitHub 识别为 MIT”只能描述仓库代码许可，不能替代数据内容许可审计。

### 2026-08-26：两个数据仓库的一手许可核验

- EventStoryLine 当前官方仓库 `README.md` 明确列出 v1.0、v1.2、v1.5 及其评测含义；根 `LICENSE.md` 的标题和全文均为 **Creative Commons Attribution 3.0 Unported**，ECB+ 子目录的 `LICENSEDATA.TXT` 也明确为 CC BY 3.0。F 报告将其写成 MIT 不符合当前官方仓库内容；此前 D 审计的 CC BY 3.0 记录正确。
- Causal-TimeBank 当前官方仓库 HEAD 为 `43b593a6bb0dde2dc2e4da7a07bb174f2f7c06ad`（2021-02-19），不是 F 记录的 `9db986...`。仓库只有两个数据 ZIP 与 `README.md`，没有 LICENSE；README 也没有 `license`、`Creative Commons` 等授权声明。F 所写 CC BY-NC-SA 3.0 无法在当前官方仓库复现；此前 D 的“无显式 LICENSE”更准确。
- EventStoryLine 当前 HEAD 为 2023-09-23 的 `46edef...`。F 给出的两个数据仓库 HEAD 均与实际默认分支不符，且许可证判断有实质错误，故 F 的仓库证据表不能直接采信。

### 2026-08-26：ICCL 与 DICP 官方代码初核

- ICCL 官方仓库当前 HEAD 为 `a7e3b3479040b17baf87f96c5de6df5291ae91c7`（2024-10-15）。仓库没有附数据或 requirements，但不是“无协议代码”：`ESC_processor.py`、`load_data.py`、`main.py`、`tools.py` 分别覆盖 ESC 数据转换、5 折划分、训练/测试与 P/R/F1 计算。
- ICCL `ESC_processor.py` 硬编码读取 `EventStoryLine/annotated_data/v0.9`；`load_data.py` 将文档名分成连续 5 段，`get_fold_data` 会排序文档名，训练折调用 `negative_sampling_fold`，测试折保持未采样。这比 F 所称“没有 fold manifest/pair/evaluator”更具体，但仍需核对原始 `doc_name` 的生成顺序、候选对规则和论文表格口径。
- DICP 官方仓库当前 HEAD 为 `44307f2ec42bce2d11da239e485ddca393888c49`（2025-09-02）。仓库包含 `requirements.txt`、完整预处理目录、训练入口和评估实现；`split_topic.py` 明确使用 `KFold(n_splits=10)` 生成 CTB 的 `train_{fold}.pkl`/`test_{fold}.pkl`，`framework.py` 用二分类 precision/recall/F1（乘 100）评测。
- DICP 的 README 给出 EventStoryLine/Causal-TimeBank 原始仓库和预处理顺序，但当前训练入口、参数与脚本只明显覆盖 CTB；还需核对是否缺失 ESC 训练路径、数据目录创建步骤、AMR 模型及可执行依赖。
- 因此，F 关于“两个独立公开实现不存在 fold/pair/evaluator”的绝对说法不成立；更准确的问题是两套代码是否能在同一个冻结协议下完整重跑，以及各自缺失项能否低成本补齐。

### 2026-08-26：ICCL/DICP 协议细读

- ICCL 的 ESC 候选对不是未定义：`ESC_processor.py` 对每篇文档内所有事件做无序两两组合，并把任一方向存在 PLOT_LINK 的组合标为正例；其余为 `NONE`。代码硬编码 ESC `annotated_data/v0.9`，固定 dev topics 为 37、41，剩余文档先 `random.shuffle` 后分 5 折；训练负例采样参数默认 `sample_rate=0`，即默认不删负例。
- ICCL 仓库的可复现性仍有明显缺口：README 没有安装/运行命令，仓库无 requirements、无 `train.npy`、无 `event_mentions_extended`，模型路径是作者机器绝对路径。5 折没有导出 manifest，而是运行时随机生成；必须确认 `main.py` 是否在载入数据前固定 seed，才能判断折划分是否稳定。
- DICP 的 CTB 候选对也有明确实现：只保留同句事件的无序两两组合，任一方向 CLINK 都标正；代码注释给出 183 篇、6811 events、9721 pairs、298 positive（原始 CLINK 318）。文档列表以 seed 6688 打乱后使用 10-fold KFold，能从代码重建精确折。
- DICP 当前公开仓库并非开箱即用：README 指向不存在的 `arguments.py`/`run.sh`，实际只有 CTB 的 `arguments_ctb.py`/`run_ctb.sh`；requirements 漏列代码直接导入的 `spacy`、DGL 等依赖，模型和项目路径含作者机器绝对路径，README 虽列 ESC 数据但仓库没有明显 ESC 训练入口。
- 当前证据支持“CTB 协议可由 DICP 代码重建、ESC 协议可由 ICCL 代码重建”，但尚不支持“ICCL 与 DICP 在同一个数据集和同一冻结协议上都是两条可直接复跑的独立 baseline”。

### 2026-08-26：四篇官方论文的协议/硬件核验

- 已从 ACL Anthology 官方 PDF 下载并转文本核验 ICCL（EMNLP 2024）、LKCER（COLING 2025）、DICP（EMNLP Findings 2025）、DECLV（EMNLP 2025）。
- DICP 官方论文明确写明实验在 **单张 NVIDIA RTX 3090** 上完成，batch size 20；F 的“Tesla V100、型号不明，故 27GB 不通过”是错误取证。27GB RTX 4090 至少在显存类别上不弱于论文实测设备，但真正的显存峰值仍需最小 smoke 才能确认。
- DICP 论文明确使用 ESC v0.9；ESC 固定最后两个 topics（37、41）为 dev、其余做 5-fold；CTB 做 10-fold；P/R/F1 为主指标。它还声明 CTB 正负样本采样率分别为 5 与 0.3，与公开代码默认参数一致。
- DICP 论文和代码存在新的内部冲突：论文写 CTB 有 184 documents、6813 event mentions、318 causal pairs；公开 `generate_sample.py` 的作者注释写实际读到 183 documents、6811 events、318 CLINK、9721 同句 pairs/298 positive。该 1 文档/2 事件差异必须用实际原始 ZIP 跑 CPU 预处理定位，否则不能把代码输出与论文表格视为完全同协议。
- Shen et al. (2022) 已被识别为 **Event Causality Identification via Derivative Prompt Joint Learning (DPJL)**，COLING 2022，页 2288–2299。F 未识别该论文是其工具链审计的关键遗漏；下一步查 DPJL 官方论文与代码入口。
- ACL Anthology 官方条目已进一步定位为 `2022.coling-1.200`（PDF/正文页均可访问）。此前 Deep Research 搜索未返回入口，但 COLING 2022 官方事件索引直接给出了该 ID。

### 2026-08-26：DPJL（Shen et al., 2022）一手核验

- DPJL 官方论文规定：ESC v0.9（258 docs/4316 sentences/1770 causal pairs）、CTB（184 docs/6813 events/318 causal pairs）；ESC 最后两个 topics 作为 dev；ESC/CTB 分别 5-fold/10-fold；P/R/F1；结果为三次独立实验均值；训练负采样率 0.5、batch size 16。
- 论文没有给出 fold seed、fold manifest、候选对清单或数据 checksum。它的源码脚注仅写“论文录用后将发布代码链接”，没有实际 URL；ACL 官方页面也没有附件/软件链接。
- GitHub repository API 按论文全名、`DPJL causality` 和作者组合搜索均返回 0 个仓库。因此目前没有证据表明存在 F 所假定的“Shen et al. (2022) 共用预处理工具”。后续论文更可能只是沿用了 DPJL 的**纸面实验设置/划分口径**，而非调用同一公开工具。
- 这修正了 F 的核心论证：缺失的不是一个已知工具包的版本号，而是该研究线从源头就没有公开历史 fold manifest。历史论文表格可作为近似同口径对标，但若要求严格可审计的精确比较，必须由我们冻结新 manifest 并在同一实现上重跑至少两个独立 baseline。

### 2026-08-26：公开数据的 CPU 计数与冻结可行性

- Causal-TimeBank 官方仓库两个 ZIP 的 SHA-256：CAT `0bf4fed1206b273174a962913b8904b4cb069c9e24f60af38cef71a5bf7b4206`；TimeML `1b01b81a55890004b03a3051f4321b87249221bbe25f30e42bd56f73fa77b317`。
- 两个 ZIP 均实际只有 **183** 个文档。对 CAT ZIP 用独立只读 XML 解析复核得到：6811 events、318 CLINK、9721 个同句无序候选对、298 个同句正例；与 DICP 代码注释完全一致。因此此前“论文 184/6813 vs 代码 183/6811”的差异来自论文/研究线沿用的语料统计，不是 DICP 当前预处理漏文件。
- EventStoryLine 官方仓库同时保留 v0.9/v1.0/v1.5；v0.9 实际为 22 topics、258 XML documents、5334 个有 token anchor 的 action events。ICCL/DICP/DPJL 的主表明确用 v0.9，因此版本可以固定为官方仓库指定提交下的 `annotated_data/v0.9`，无需在 v1.2/v1.5 之间猜测。
- 结论上，数据版本门并非 F 所判的绝对 FAIL：ESC v0.9 与 CTB CAT ZIP 都能以官方提交 + 文件级 SHA-256 manifest 冻结。尚未解决的是历史 fold 的精确复原和两个独立 baseline 在我们冻结 manifest 上的共同重跑。

### 2026-08-26：ICCL/DICP 完整 Git 历史核验

- DICP 完整历史只有 18 个提交，首次代码上传至今仅出现 `arguments_ctb.py`、`main_ctb.py`、`run_ctb.sh` 和 CTB 专用预处理；没有任何历史版本包含 ESC、通用 `arguments.py`/`run.sh` 或 README 所描述的双数据集入口。
- ICCL 完整历史只有 4 个提交，首次上传即为当前 8 个 Python 文件；从未包含 CTB、requirements、运行脚本、预处理输入 `train.npy` 或 `event_mentions_extended`。
- 因此不能用“仓库旧版本可能含另一数据集实现”来补齐兼容性：ICCL 只提供 ESC 线，DICP 只提供 CTB 线。虽然两者各自协议可部分重建，但不存在两个独立团队在**同一数据集 + 同一冻结协议**上的直接公开可跑路径。
- 这项失败足以阻止当前进入 GPU baseline reproduction。下一步应形成正式本地审计结论，并区分：`当前不能执行` 与 `是否值得另立低成本协议修复任务`，避免把 F 的错误取证等同于路线本身永久不可行。

### 2026-08-26：官方身份、seed 与执行入口终核

- ACL 官方元数据确认 ICCL 为 *In-context Contrastive Learning for Event Causality Identification*（Liang Chao、Wei Xiang、Bang Wang），DICP 为 *DICP: Deep In-Context Prompt for Event Causality Identification*（Lin Mu 等七人）。F 的两项方法身份均串线。
- ICCL 在 `load_data()` 前调用 `setup_seed(209)`，故运行时 5-fold 打乱在相同输入和 Python 行为下可重建；评测明确为 positive-class P/R/F1，并分别输出 intra/cross/combined。
- ICCL 官方论文写 3090 级 GPU、batch 16、平均约 5 GPU 小时，代码固定 `CUDA_VISIBLE_DEVICES=0`；DICP 官方论文明确单张 RTX 3090、batch 20。27GB 属高可行而非 F 所写的证据缺失，但仍未本地测峰值。
- DICP 当前 `main_ctb.py` 导入仓库不存在的 `models.prompt4` 与 `amr_data_loader`，另有绝对保存路径；因此即使 CTB 数据协议可重建，官方训练实现也无法原样启动。双 baseline 可执行门的失败进一步坐实。

### 2026-08-26：交付前核验状态

- `docs/replan/F_eci_protocol_audit.md` 已检查标题结构、关键判定词和内部引用残留：101 行、7,815 bytes，无 `cite`/`turn...` 内部 token。
- 工作树仍包含接管前的代码与文档改动；本轮只新增/更新 replan 审计与规划记录，没有 staged changes，没有提交或推送。
### 2026-08-26：DR-G 文件接收

- 已收到 `docs/replan/G_maven_causal_protocol.md`（45,127 bytes）与 `G_maven_causal_protocol.pdf`（887,915 bytes）。
- 同目录存在两个 25-byte Windows `Zone.Identifier` 元数据文件；当前保留不动，不把它们当报告内容。
- 尚未接受报告结论；下一步先检查 PDF 可搜索性/链接证据链与 Markdown 结构，再逐项核验协议、论文身份和仓库执行闭环。

### 2026-08-26：DR-G 导出完整性初核

- Markdown 为 305 行/45,127 bytes，含 51 个 ChatGPT 内部 citation token 和 69 个 HTTPS URL。
- PDF 为 17 页、约 30,252 个可提取文本字符、未加密；共有 98 个链接注释、14 个唯一 URL。
- PDF 唯一链接几乎全部是 ACL Anthology 论文页/PDF，没有关键 GitHub、数据文件、split/evaluator 路径；故 PDF 不能单独支撑 repository execution audit。
- 报告章节覆盖 executive verdict、身份纠错、A/B/C 协议图、逐论文矩阵、仓库审计、独立团队、27GB、go/no-go 和未核项；下一步完整阅读 Markdown，并以其中原始 URL 逐项回查。

### 2026-08-26：DR-G 全文初读结论（待一手核验）

- G 正式判定为 `NO-GO`。其核心理由不是 MAVEN-ERE 数据/evaluator 不可冻结，而是 A 轴 hidden gold 不本地、B 轴 Chen 与 LLMERE 的 pair universe/evaluator 不同、C 轴 Xiang 公开仓库缺 MAVEN 路径，最终没有两个独立近期同轴可执行 baseline。
- 报告将 B（LLMERE-defined：official train seed42 切 8:2、official valid 作 test、all ordered mention pairs、官方语义的 causal micro positive P/R/F1）列为唯一值得保留的协议资产候选，但明确不建议在发现第二个 baseline 前做 GPU smoke。
- 报告实际检查了多个仓库文件路径，并指出关键执行缺口：Chen 缺 raw→split→cache/train/prediction 全链；LLMERE 有 split/convert/eval 但缺完整训练/推理包；Xiang 的 GLM4ECI 当前是 ESC topic37/41 + 5-fold 代码而非 MAVEN；KnowQA 当前 URL 404；TacoERE/MMD 未取得作者代码。
- 必须优先消解一个与本项目权威记录的数值冲突：G 引用论文 Appendix 称 public valid 有 9,698 causal relations，而 `docs/results/PHASE_C.md` 等本地权威记录使用 valid causal 6,599。需直接读取本地 MAVEN-ERE JSONL 与官方 evaluator，判断 event-level relation、mention-pair expansion 或字段过滤的具体口径。
- 还需核查 G 对官方 evaluator candidate universe 的描述、Chen sentence-level relation-bearing sampling、LLMERE seed42 split/evaluator、各仓库 HEAD/缺失文件和 27GB 声明。原始 G 文件保持不改。

### 2026-08-26：本地 MAVEN-ERE 数据资产确认

- 本地已有完整 official v1.0 风格文件：train 2,913、valid 710、test_unlabeled 857；`data/raw/maven_ere/` 与 `data/processed/maven_ere/` 对应文件 SHA-256/字节数一致，无需重新下载 Tsinghua Cloud。
- SHA-256：train `6a5519fe7c30448690adb13d49217c50d474fc57480eae10aecb29df7eb638b7`；valid `6faea0e4e16b4a2d5d9631e09ef6e1c6bac6e3f912490bfc48eeaceaf98c6153`；test input `aa34be601fc6397fec8256d796c4f73bd868f1230dea96e31675c18563f05bd7`。
- 本地还保留官方 evaluator `/tmp/maven-ere-eval.X7tKCf/evaluate.py`，以及此前克隆的 LLMERE `split_data.py` 与 `eval_causal.py`，可直接做 CPU 协议核验。
- 因此 G 的“官方文件 checksum 未取得”只描述其 Deep Research 沙箱，不是本项目剩余缺口；本地可把 B 的数据/split/evaluator 静态门进一步锁实。

### 2026-08-26：causal 9,698 / 6,599 口径冲突已消解

- 全量 official valid（710 docs）直接统计为 16,301 event clusters、17,780 mentions、9,698 条 event-level causal relations（CAUSE 1,623；PRECONDITION 8,075）；G 的论文表数字正确。
- 官方 evaluator 将 cluster-level relations 展开为 13,624 条正类 mention pairs（CAUSE 3,277；PRECONDITION 10,347），并在 613,706 个文档内有序 mention pairs 上汇总 positive-class micro P/R/F1；G 对 candidate universe/evaluator 的描述与官方代码一致。
- 本项目权威 6,599 明确来自 710 篇 valid 再切成 213 calibration + 497 test 后的 **497 篇子集**，不是全量 valid。因此两组数字都正确但 currency/split 不同：9,698 不能替代本地 497 子集的 6,599，6,599 也不能用来纠正官方 full-valid 表。
- train 同口径为 36,316 event-level causal relations（CAUSE 6,797；PRECONDITION 29,519），展开为 53,358 positive mention pairs，all ordered candidate universe 为 2,532,394。

### 2026-08-26：LLMERE-defined B split 本地复现

- 在临时目录直接运行 LLMERE commit `94d4ef278...` 的原始 `split_data.py`，输入本项目 official train/valid，成功得到固定的 2,330 train / 583 dev / 710 test；seed 42 split 可重建。
- 文件 SHA-256：B-train `1d80e35db423df87e8a87261fbb4ce576bb45ebdf602a9b4db43845dc3aa1f6a`；B-dev `961abc25c81e571182849d8388c5dd39c81a5f182c1a16512515aca45856a550`；B-test 与 official valid 相同，为 `6faea0e4...`。
- ID-manifest SHA-256：train `3884af697000d854f95f77b297c3ca686d56e3973e505b5a31aff7fba60a925a`；dev `8a2dfe00ff4fcaf12e1b6eb11492b43f5ec3bc9a312b6090bbe7e20275b8f3bd`；test `6c3fa23a4b2d1349aa16e61be245017cd1ae3a5e12f71eeebf85e4e004af7870`。
- 因此 G 的 B split conditional 在本项目中可升级为 PASS；临时产物位于 `/tmp/llmere-split-audit.EHYnwO`，未写入项目数据目录。
- LLMERE 仓库含 29,079 行 causal prediction 和预计算 `eval_results.json`，但没有 evaluator 运行所需的 `data/converted/MAVEN_ERE/causal/test_doc_split_num.json` 或 `data/MAVEN_ERE_split/test.jsonl`。需要先运行 converter 重建辅助文件，不能把“已有 output”写成 evaluator 开箱即跑。

### 2026-08-26：LLMERE evaluator 首次 smoke 的新缺口

- 按当前 official valid（17,780 event mentions）和 `convert_causal.py` 的分块公式独立重建 `test_doc_split_num`，应产生 29,080 条 prediction rows；发布的 `generated_predictions.jsonl` 只有 29,079 行，存在 1-row 差异。
- 这可能是作者使用的数据文件少一个 mention、发布 prediction 漏一行、或 converter/output 来自不同 revision；未定位前不能把预计算 F1 36.04399 视为当前 official file 上完全可重放。
- 第一次执行原 `eval_causal.py` 使用 shared document-tools Python，因该环境没有 `sklearn` 在 import 阶段失败，未生成结果。后续改用项目 `uv` 环境，不安装新包、不原样重复。

### 2026-08-26：LLMERE evaluator 本地重放通过

- “29,079 vs 29,080”不是数据/预测缺失：发布 prediction 有 29,080 个逻辑 JSON records，但最后一行无换行，故 `wc -l` 只报 29,079。
- 使用项目 `uv` 环境、official valid gold、按原 converter 公式重建的 `test_doc_split_num` 和发布 predictions，原始 `eval_causal.py` 成功重放：precision 34.98446、recall 37.16970、F1 36.04399，support 13,624。
- 重算结果与仓库预计算结果指标完全一致；JSON 仅因本地 scikit-learn 1.7.2 的浮点末位/`support` 序列化为 float 而字节不同，不是实验差异。
- 因此 LLMERE-defined B 的 official files、seed42 split、all-ordered mention-pair universe 和 causal evaluator 在本项目中均可判 PASS。剩余硬失败集中于：LLMERE 自身训练/推理包不完整，以及没有第二个独立近期同轴可执行 baseline。
## 2026-08-26 G：Chen 决定性核验入口

- G 报告把 Chen 2024 与 LLMERE 2025 都归到“original train 8:2、original valid=test”的 B-like split policy，但同时明确指出：Chen 的句子级样本排除四类关系全空的 event pair，LLMERE 则在文档级所有有序 gold mention pair 上补 `NONE`。因此二者不能只凭 split policy 相似就视为同一 causal benchmark protocol。
- 当前本地已把 LLMERE-defined B 的数据、seed-42 split、pair universe 和 evaluator 全部复现为 PASS；剩余决定性检查是 Chen 仓库/论文是否存在可恢复的 all-pairs prediction 或未公开于 G 报告的生成链。若不存在，双独立 baseline 门槛即正式 FAIL。
- 本轮不会为 Chen 新写 pair generator、scorer adapter 或训练代码；那会成为重实现/重定义 baseline，不能算公开可复现对手。
- 已完整克隆作者仓库，HEAD=`58de425c88ccb4d98aaaf0f8ad24a4c2ba066dfb`，共 7 个 commit，与 G 报告一致。公开 tree 仅含四份 cached prompt、MAVEN/CTB evaluator、`src/data.py`/`src/utils.py`、逻辑规则和 requirements；没有数据 split generator、训练入口、官方 MAVEN submission dumper。
- 仓库执行入口直接读取 `cached_prompts/{train,test}_sent_prompts_events.jsonl`；`--seed 42` 在 evaluator 末尾设置随机数种子，当前没有证据表明它曾生成 8:2 document split，因此不能把该 seed 推断成数据划分 seed。
- `evaluate_maven.py` 最终按四个关系轴分别调用 sklearn `classification_report`，没有把输出交给 MAVEN-ERE 官方 causal scorer。还需精读 `src/data.py` 与缓存内容，确认 candidate universe 和缓存是否包含可恢复的完整 all-pairs predictions。
- Chen 的公开 MAVEN cache 已定量核验：train/test 各只有 500 条 prompt；每条恰好 2 个 event IDs、2 个方向，所以 test 总计仅 1,000 个定向 pair，且只覆盖 302 个原始 valid 文档。相比之下，同一 710-doc public-valid 上的 LLMERE/官方 all-ordered-pair universe 是 613,706 个候选 pair。
- test cache 的 500 条样本中，零条满足“两个方向在四个关系轴上都为空”；这直接印证论文的 relation-bearing sentence-level sampling。虽然 1,000 个方向中有 372 个单方向在四轴上均为 `NO_*`，其反方向或同一 pair 的另一关系轴必有正关系，因此不能把它理解为保留了完整负例宇宙。
- `src/data.py` 内确有面向 encoder 的 document-level all-pair 数据类，但公开 evaluator 从未调用它；该模块只枚举无序 `index1 < index2` pair，且仓库没有对应训练入口、checkpoint、预测输出或把结果转成官方 causal evaluator 的链条。它不能把已发布的 500-sample LLM 实验升级为 LLMERE-defined B baseline。
- Chen cache 的文档来源已与本地官方数据逐 ID 对齐：train cache 的 401 个唯一文档全部来自 official train；test cache 的 302 个唯一文档全部来自 official valid；无未知 ID。test cache 的 causal 方向标签为 `NO_CAUSAL=877 / PRECONDITION=61 / CAUSE=62`，远小于 public-valid 全量 gold 的 13,624 个 mention-level causal positives，进一步证明它只是 sampled setting。
- 缓存 SHA-256：train=`8c06777cd102f4c6b929ddd52b3230fa62e6991b672b8647b2d482987cbd3f5a`；test=`e2fdcd3db8ae58e9cc04578b7ffeaf84336e5ec66740d7712ae1ddad7576966a`。
- 尝试通过 Web 工具直接打开 ACL Anthology 正式页/PDF未返回正文；后续改用本地下载并按 PDF skill 提取 Appendix E，不把空返回误作证据。
- 已从 ACL Anthology 官方 PDF 核验 Appendix E：论文明确写 original train 随机按 8:2 切分、original valid 作新 test；随后明确写 ERE 在 sentence level 采样、排除两个 events 没有任何 relations 的样本，并从 MAVEN-ERE 新 test 随机抽 500 examples 作为 testbed。故 Chen 主表是 500-sample multi-relation logical-prediction setting，而不是 710-doc all-pairs causal B。
- 已检查完整 7-commit git 历史、所有 commit tree 与 unreachable object：2024-06-21 一次性加入当前 evaluator/cache/src 文件，此后只改 README；历史上从未出现 split generator、cache generator、训练入口、checkpoint 或完整预测 artifact。不能把当前缺口解释为仅 HEAD 误删。
- 已将 LLMERE shallow clone 补全为完整历史：全仓库仅 5 个 commit；所有历史路径仍只有 conversion、eval、published prediction/result artifacts 与极简 README，从未出现 trainer、LLaMA-Factory config、inference entrypoint、requirements/environment 或 checkpoint。故“缺完整训练/推理闭环”不是 HEAD 偶然删除。
- Xiang/GLM4ECI 作者仓库已独立核验：HEAD=`742f311094b1d87e126364a531a883d292d0b25e`，仅 2 个 commit、8 个项目文件；`load_data.py` 读取未随仓库发布的 `train.npy`，排除 topics 37/41 并对其余文档做 5-fold。这是 EventStoryLine/DPJL lineage 的结构，不是论文所写 MAVEN-ERE original-dev-as-test / train-10%-as-dev setting；tree 无 MAVEN converter、manifest 或 evaluator。
- KnowQA 论文给出的 GitHub Web URL 在 2026-08-26 实访返回 HTTP 404；GitHub API 同次请求返回 403（可能为限流/访问策略），因此只采用 Web 404 作为“当前未取得”的下界，不声称仓库绝对不存在。其 sampled setting和原团队作者重叠即使仓库恢复也不能直接补 exact-B。

## 2026-08-26 G：最终资格判定

- 已生成 `docs/replan/G_maven_causal_protocol_audit.md`。DR-G 的核心 NO-GO 结论通过本地事实验收，但本地执行把 LLMERE-defined B 的数据、split、pair/labels、evaluator 四门从 CONDITIONAL 修正为 PASS。
- exact-B 仍因两个独立近期对手 FAIL、公开训练/推理闭环 FAIL 而不能成为论文主轴。该失败不能靠 GPU smoke 解决，因此本轮未运行 GPU。
- ECI 与 MAVEN-ERE 两个优先候选现均停在相同的双 baseline 硬门。Phase 8 不应自动启动；下一步需要作者决定扩大 benchmark 候选池，或明确调整资格规则。
- 收尾核验已确认 evaluator 临时目录、split 临时目录及原脚本仍存在，可进行一次完整 fresh rerun；不依赖先前日志作完成声明。
- fresh rerun 已通过：LLMERE 原 evaluator 输出 `rel_label_list=613706`、P=34.98446、R=37.16970、F1=36.04399、support=13,624；prediction logical records=29,080。official train/valid/test 与 B train/dev/test 哈希均逐项复核一致。
- 最终范围核验：原始 G Markdown=45,127 bytes、PDF=887,915 bytes；新增 audit=10,062 bytes/166 行。未产生 staged changes，未修改既有代码；工作树原有 v5/Ch1 修改和 untracked 文件全部保留。

## 2026-08-26 H：提示词设计

- 扩大候选池采用严格串行：第一储备为 MATRES / TB-Dense temporal relation；若失败，再单独审 ECB+/GVC/FCC event coreference，不一次混三条任务线。
- H 的关键风险不是模型创新，而是 underlying TimeBank/AQUAINT 文本许可、历史 preprocessing、test pair IDs、`VAGUE`/inverse label mapping、closure 和 evaluator 分裂。
- 已知必须筛查的近期候选包括 `2024.emnlp-main.1136`、ConTempo、Temporal Cognitive Tree、LLMERE temporal、GDLLM 与 consistent discourse-level TR；是否使用 exact MATRES/TB-Dense protocol 由网页版一手核验，不在提示词中预判。
- 为避免 PDF 宽表截断，H 明确限制表格不超过五列，并要求逐论文小标题与 plain-text URL registry。

## 2026-08-27 H：文件接收

- 已收到 `docs/replan/H_temporal_protocol.md`（43,951 bytes）与 `H_temporal_protocol.pdf`（1,080,000 bytes）。
- 两个文件均带 25-byte Windows `Zone.Identifier` sidecar；当前保留，不作删除。
- 接收登记已完成，下一步先检查 Markdown/PDF 的文本、来源和结论结构，再决定需要核验的一手数据/代码资产。

### H 报告结构初检

- H Markdown 共 545 行、43,951 bytes；含 101 个 ChatGPT 内部 citation token，但另有 51 个原始 URL（34 unique）和完整 plain-text Source Registry，可恢复关键来源。
- H PDF 为 17 页、未加密、可搜索，文本层约 29,069 chars；103 个 URI annotations、19 unique，主要覆盖 ACL 论文页/PDF、LDC、TimeML、CAEVO，仓库级证据仍以 Markdown plain-text URL 为主。
- 报告结论为 `NO-GO`：最接近的是 `MATRES-N837-VØ`，但数据许可、第二个独立同协议 executable baseline 和第二方法的 27GB 证明失败；split/pair/evaluator 仅 conditional。
- 报告把 Roccabruna 2024 RoBERTa 作为唯一第一候选，把 TCT 2024 视为最值得继续静态验尸但尚不能计数的第二候选。下一步优先本地取得并审计 TCT software.zip；在它通过前不做 GPU。
- 原始 H 报告保留不改；后续将以本地数据/代码核验层覆盖冲突。

### 本地 MATRES annotation 冻结

- 本地 `data/raw/matres/{timebank,aquaint,platinum}.txt` 与 H 报告列出的 CogComp commit Git blob IDs **逐项一致**：`0896639... / e07080d... / e986180...`，因此不是未知派生版本。
- 三份文件均为合法 6-field TSV、无 exact duplicate、无 directed pair-ID duplicate。统计为：TimeBank 6,336 rows / 182 docs；AQUAINT 6,404 rows / 73 docs；Platinum 837 rows / 20 docs。
- 文件 SHA-256：TimeBank=`217c7a5b51c7fa5feed36dd10c6feed5e3dfa4dd736d45ccb37bea21bcb09`；AQUAINT=`eb42b25d873809dfa0494ee0564da30f153942a2af663f5a74660928210a340b`；Platinum=`346be061630c01e8ac2624e16ed46b24506bf152334b0dee275ada7943d70daa`。
- sorted doc-ID manifest SHA-256：train/TimeBank=`853b2ddc2c3c2c95206d1844a35f55d7657442a4061209664ff503cf2a6f5063`；dev/AQUAINT=`0ef1f5b96639bffdd584a3525a1cb6e278ebd9bb4dd251853abf7e0cbca7d8ac`；test/Platinum=`61e8bca9cbc6e027357aef1cb096819ab1198d2f05d6d60d4a19cafaafefbf32`。
- `VAGUE`-drop 后 pair counts 为 train 5,481 / dev 5,728 / test 724；test labels=`BEFORE 424 / AFTER 269 / EQUAL 31`，与 Roccabruna 论文 Table 7 的 MATRES 724 test pairs 相符。
- `VAGUE`-drop ordered row-manifest SHA-256：train=`77d3d20c66ec4e8e059b8be785a239fffe1883d9f6a3f91da79a49f6f03b386c`；dev=`566526b29af875a342a9e9172da7e5549a49d3ec4c49feb64572db7c17ee19f9`；test=`14a707f2348d86c7c3611943ead3acc6e73402602da36a9fed0f10e307235be6`。
- 因此 H 的 annotation-level split 与 pair/labels 两项可从 CONDITIONAL 升为 PASS；source TML 合法取得/版本映射、loader duplication 与 evaluator aggregation 仍需分别核验，数据许可 FAIL 尚未改变。

### MATRES source text / 许可边界

- 全项目未发现 `.tml/.timeml` TempEval source corpus；本地 `data/raw/matres/` 只有 relation TSV 与 axis annotation CSV。现有文档把这批文件笼统记为 “MATRES raw”，但没有 LDC2006T08/TempEval archive、取得日期、license receipt 或 source-text hash。
- `data/raw/DATA_PROVENANCE.md` 只记录 MATRES “WSL/4090 ✅”，不能证明 Roccabruna formatter 所需的 TimeBank/AQUAINT/Platinum TML 已合法取得。因此 H 的数据与许可 FAIL 目前得到本地支持。
- Web 工具直接打开 TCT ACL 页面与 software.zip 本轮返回空结果；这不是附件不存在的证据，后续改用官方 URL 的 `curl` 下载到 `/tmp`。

### TCT archive 下载状态

- 官方 `software.zip` 下载目录为 `/tmp/tct-audit.llIu7V`。首次 `curl` 超过 30 秒工具返回窗口，但原进程仍 ALIVE，partial file 已达 573,440 bytes。
- 当前不能对 partial ZIP 做内容结论；将等待同一进程自然结束后再执行 `file`、SHA-256、`unzip -t` 和 tree 审计，不启动重复下载。
- 原下载进程现已 GONE，文件最终大小 1,364,620 bytes；下一步才开始完整性与内容校验。
## H：TCT 官方 software.zip 初步静态审计（2026-08-27）

- 官方附件：`https://aclanthology.org/attachments/2024.findings-emnlp.47.software.zip`
- 本地临时副本：`/tmp/tct-audit.llIu7V/software.zip`；1,364,620 bytes；SHA256
  `dbf11f4ad3cabd5b721bb18d8e37dcb51f5da0cc6878f3ff9522b87622160e4e`。
- ZIP 完整性校验通过，共 52 个文件，解压后约 32,999,033 bytes；包含已处理的 MATRES/TBD
  JSON，以及 BART 训练/测试辅助模块。
- 闭环材料缺失：无 README、依赖/环境文件、LICENSE、统一入口、参数构造器、原始数据预处理脚本、
  checkpoint、Git 历史。故目前不能把该附件认定为可独立复现的完整 baseline。
- 初步代码异常（待聚焦复核）：测试模块导入归档中不存在的 `Classifier.myModel` 与
  `Classifier.soft_embedding`；训练模块引用的部分数据集类疑似不存在；训练保存 `state_dict` 单文件，
  测试却疑似按 Hugging Face `from_pretrained` 目录加载。
- 下一步只做静态聚焦核验：统计附件 MATRES 的样本/标签，核对 VAGUE 是删除还是作为负类保留，
  并确认评测器实际报告的 micro-F1。若不能与 `MATRES-N837-VØ` 对齐或代码不能闭环，立即判定
  “第二条同口径 baseline”失败，不进入 GPU。

### TCT 聚焦复核结果

- 附件 MATRES JSON 不是候选协议的固定 split：
  - `train.json`：10,888 条（BEFORE 5,483 / AFTER 3,819 / VAGUE 1,227 / EQUAL 359）；
  - `val.json`：1,852 条（BEFORE 942 / AFTER 662 / VAGUE 189 / EQUAL 59）；
  - 两者合计 12,740，恰等于本地原始 TimeBank 6,336 + AQUAINT 6,404，说明它把两个语料合并后
    重新切分，而非 `TimeBank=train, AQUAINT=dev`。
  - `test.json`：837 条（BEFORE 427 / AFTER 271 / VAGUE 109 / EQUAL 30），与本地 CogComp
    Platinum（424 / 269 / 113 / 31）也不一致。
- 评测器先让全部 4 类参与预测，再以 `classification_report(..., labels=[BEFORE, AFTER, EQUAL])`
  排除 VAGUE 标签并把其中的 `micro avg` 作为最终 `micro_f1`；这是 **VAGUE-as-negative（Vneg）**，
  不是先删除 VAGUE 样本的 **VØ / 724-pair accuracy**。因此 TCT 不能作为
  `MATRES-N837-VØ` 的第二条同口径 baseline。
- 代码闭环问题得到确认：`dataset.py` 只定义 `BartDataset`、`SmallBartDataset`，但训练/测试模块
  导入不存在的 `T5Dataset`；同时还导入归档中不存在的 `Classifier.myModel`、
  `Classifier.soft_embedding`。训练用 `torch.save(model.state_dict(), *.bin)`，测试却把该 `.bin`
  传给 `from_pretrained`。即使不考虑口径差异，官方附件也不能原样执行闭环。
- 结论：TCT 从“可能的第二 baseline”降为 **不合格**；H 的“两条独立、近期、同口径 baseline”门槛
  仍为 FAIL，且静态证据已足以停止，无需 GPU。

## H：Roccabruna / LLMs-TRC 仓库取证（2026-08-27）

- 官方仓库 `https://github.com/BrownFortress/LLMs-TRC` 已完整克隆到临时目录；审计提交为
  `41eb1ed036cd4b5741b17dc07f809311cc915016`，最后提交时间 `2024-10-22T16:37:17+02:00`
  （提交说明 `v1`）。
- 仓库具备顶层 README、requirements、LICENSE，以及 `data_formatter`、`encoder_architecture`、
  `ICL_and_FT` 等目录；相较 TCT 附件，具备继续做静态闭环核验的基本结构。
- 下一步仅核对 MATRES formatter、RoBERTa 配置/入口、测试指标与产物，不执行模型下载或推理。

### Roccabruna 口径核验

- `data_formatter/matres_opener.py` 明确把 `timebank.txt`、`aquaint.txt`、`platinum.txt` 分别映射为
  train、valid、test，并从 TempEval TML 重建上下文；与 `MATRES-N837-VØ` 的 split 定义一致。
- `encoder_architecture/main.py` 对 MATRES 默认令 train/dev/test 的 `skip_vague=True`；数据加载器只在
  `rel_type != "VAGUE"` 时纳入样本。测试因此是删除 VAGUE 后的三分类，而不是 Vneg。
- `eval_loop` 对三类调用 sklearn `classification_report`；单标签三分类下报告的 `accuracy` 与
  micro-F1 等价。该实现可以作为候选协议的第一条公开 baseline 代码路径。
- 但“开箱即跑”仍不成立：README 推荐的 `run_exps.sh` 把三个数据集写成一个数组元素
  `("TB-DENSE MATRES TIMELINE")`，会违反 `--dataset` choices；还使用了被注释、未赋值的
  `model_name_large`，并引用仓库中不存在的
  `configs/word_conf_linear_dual_cls_as_context_robLarge.json`。复现时必须手工改成单条明确命令。
- 这些工程缺陷不改变其作为**一个**公开对手的资格，但进一步说明不能把“有仓库”等同于完全复现；
  H 的硬门槛要求多个对手，TCT 已不合格，因此总体仍 NO-GO。

### Roccabruna 论文—仓库 split 矛盾（终审需降级）

- 论文正文明确：所有模型使用 micro-F1，MATRES/TB-Dense 完全删除 VAGUE；附录给出 MATRES
  去 VAGUE 后的 train/dev/test 数量为 **9,074 / 2,133 / 724**，并报告 RoBERTa MATRES
  micro-F1 **87.6**；硬件为单张 NVIDIA 3090 Ti 24GB。
- 但仓库 formatter 固定 `timebank.txt -> train`、`aquaint.txt -> valid`，结合项目内与 CogComp
  完全一致的 annotation，应产生 **5,481 / 5,728 / 724**，并非论文的 9,074 / 2,133 / 724。
  两者训练+验证总量几乎相同（11,207 vs 11,209），更像论文在 TimeBank+AQUAINT 合并后另做重切分。
- 仓库 `data/`、`outputs/`、`bin/` 只有 `.keep`，未发布实际 pkl、预测、结果 JSON 或 checkpoint；
  因而不能从一手产物判定论文 87.6 对应哪一份 split，也不能把该数字登记为
  `TimeBank=train, AQUAINT=dev` 的公开可比 baseline。
- 修正此前判断：仓库**代码路径**支持 `MATRES-N837-VØ`，论文**已发表数字**只确认测试集 724 与
  VØ，训练/验证 split 不同或至少不可核实。按论文硬标准，应把 Roccabruna 从“合格 baseline”降为
  **条件候选/不可直接引用 87.6**，而不是无条件第一 baseline。

## H：交付校验

- 从项目内三份原始 TSV 重新计算 rows、docs、labels、文件 SHA-256、doc manifest SHA-256、
  VØ pair counts 与 ordered manifest SHA-256，全部与审计文档一致。
- 使用项目 `uv` 环境对一个三类 single-label 样例同时计算 accuracy 与 sklearn micro-F1，均为
  `0.6666666666666666`，确认候选 evaluator 恒等式。
- 未运行模型训练、推理或 GPU；未修改任何项目代码。

## I：事件共指资格验证启动边界（2026-08-27）

- 作者同意按推荐转审 ECB+ / GVC / FCC 事件共指，并继续严格串行。
- 本轮只生成网页版 Deep Research 提示词和最小附件清单；不在本地重复大规模检索，不下载论文，
  不运行 CPU/GPU 实验。
- 决策问题不是“事件共指是否有人研究”，而是能否冻结一个公开许可、exact split、mention universe、
  cluster gold 和官方 evaluator，并取得至少两个独立 2024–2026 正式方法的同协议执行闭环与约 27GB 路径。
- 必须重点防止四类串轴：ECB+ within-document vs cross-document、gold mentions vs predicted mentions、
  topic-known vs topic-unknown、CoNLL average vs 单项 MUC/B³/CEAF_e/LEA 或 pairwise F1。
- 现有一手审计已知 SECURE（ACL 2024）在 ECB+/GVC/FCC 的同一作者 scorer 下给出 direct GPT-4、
  RoBERTa-large 与 GPT-4 summaries + RoBERTa-large；这只能作为最先核验的协议锚，不能自动视为
  多个独立 baseline，也不能把闭源 GPT-4 辅助缓存算作 27GB 单卡闭环。
- 最小附件拟定为：`SYNTHESIS_DECISION.md`、`B_datasets_audit.md`、
  `C_methods_code_audit.md`、`H_temporal_protocol_audit.md`。不上传 PDF，不上传 F/G/H 原始报告。
- 预定交付名：`I_event_coref_protocol.md` 与 `I_event_coref_protocol.pdf`。

## 2026-08-27：作者纠正研究方法——从“语料资格淘汰”回到“论文问题分解”

- 作者明确指出：事件图谱构建已有大量论文，硕士论文应从中拆出若干相互衔接的具体问题；不要求全篇
  限定同一语料类型。
- 前述审计把“公开可比”过度收缩为“完全相同的作者原 split + 两个近期作者执行包 + 零修补 + 可自由
  再分发数据”，导致资格门不断增加。这不是仓库 `AGENTS.md` 的硬要求，也不是硕士论文成立的必要条件。
- 修正后的硬要求只有：每章在自己选定的公开 benchmark/主指标上实际比较并超过多个方法；我们冻结
  split/evaluator、统一重跑并如实记录修补。不同章节可以使用不同语料，只需共享统一事件图谱对象、
  构建流水线和总研究问题。
- 论文原分数与本地统一重跑必须分栏；论文 split 不同不会取消方法资格，只会禁止直接横比原分数。
  作者代码需要合理修补或忠实复现也不再一票否决。
- DR-I 窄语料资格审查暂停，不要求作者现在提交网页版事件共指报告；先回到顶层重建论文分解与章节
  连接，再决定哪些外部检索真正值得交给深度研究。

### 与现有仓库主线的对照

- `docs/SPEC.md` 现有 v5 本来就是完整构建流水线：Ch1 事件身份消解 → Ch2 事件关系抽取 → Ch3
  事件事实性检测 → Ch4 构建质量的下游代价与消费者依赖性；四章共享 `EventNode → RelationEdge /
  EventGraph → Prediction` 契约，但并没有要求共享同一语料。
- 当前不是四章都失败：Ch3 已在 MAVEN-FACT 主指标上超过多个方法；Ch2 已有统一 valid 的官方原版
  baseline 重跑和完整训练链；Ch1 已从错误剖析中定位到同词形事件的过并/欠并共同难点；Ch4 已取得
  “微调消费者对图改进零响应”这一稳定负结果，并与 ACL 2025 in-context 消费者的正面结果构成可检验冲突。
- 因此无需继续“重开论文主轴”或寻找一套覆盖全篇的万能数据。应恢复 v5 组件主线，允许每章选择最合适
  的公开 benchmark，并把本地统一重跑作为可比性来源。
- 真正需要修订的是 `SPEC` 中“公开可比”的操作定义：可以采用公开论文方法的忠实复现/合理修补；可以
  在我们冻结的新 split 上统一重跑；数据只需可合法用于研究与可说明获取方式，不要求随代码自由再分发。
  不同 split 的论文原数只作背景，不与本地结果直接相减。

### 顶层收敛结论

- 唯一推荐论文骨架就是现有 v5：身份消解、关系抽取、事实性、构建质量的消费者依赖性。
- MAVEN 家族可作为前三章到 Ch4 的集成桥梁；ECB+/GVC/FCC、MATRES、FactBank/MEANTIME、CRAB/叙事
  完形分别作为最适合对应组件的主任务或泛化验证，不要求彼此共享 annotation schema。
- 实施严格串行顺序：Ch2 → Ch1 → Ch3 → Ch4。外部深度研究以后只补具体实现/loader/baseline 缺口，
  不再负责对整套语料作资格淘汰。

## 2026-08-27：独立可行性审查验收要求

- 资源边界：本地 WSL2 只做 CPU 数据/测试/轻量 smoke；重训练可用 `gpu-4090`，`gpu-5090` 为逐次授权
  备用；不得依赖新增 GPU、人工标注或大规模闭源 API。
- 数据边界：允许各章使用不同现有公开/可合法研究使用语料，但不能要求作者新标数据；需要人工分析的
  error study 只能抽样解释，不得成为方法训练或主指标必需输入。
- 科学边界：每章必须有学界公认 headline metric、冻结 evaluator、多个实际可运行 baseline；辅助指标
  只能解释机制，不能代替主结果。
- 方法边界：需要明确相对前人增加了什么、为何可能改善、失败时如何收缩；不能只做工程拼接、换底座或
  数据集搬运。
- 工作量边界：四章应共享 schema/pipeline 又有各自方法与实验，足以支撑硕士论文；不能四章都只是一次
  小消融，也不能每章都要求重写一套大模型系统。
- 叙事边界：研究动机 → 三个构建环节 → 下游消费必须能形成因果顺序；Ch4 要消费前三章产物或其可控
  误差，不得只把另一套下游 benchmark 拼接成孤立章节。
- 独立审查者需要给出 PASS / CONDITIONAL / FAIL，总结必须区分硬阻塞、可工程解决项和非必要加分项。

## 2026-08-27 独立可行性审查（最终）

- 独立审查结论：**CONDITIONAL（有条件可行）**。在不新增人工标注、不依赖大模型训练的前提下，现有本地、RTX 4090 与 RTX 5090 资源足以完成“3 个方法章 + 1 个系统评估章”；估算总量为 95–180 单 GPU 小时。
- 通过条件不是增加语料限制，而是先冻结每章的 manifest、输入层级、evaluator 与主指标，再在同一协议下重跑多个代表性 baseline；原论文异 split 成绩仅作背景，不直接比较。
- 三个方法章的最小方法贡献分别收敛为：Ch1 上下文判别的事件身份建模；Ch2 关系族均衡的长上下文关系抽取；Ch3 证据与五分类事实性的条件耦合。Ch4 明确定位为系统评估章，必须在同一 1,908 个查询上真实消费前三章输出。
- 独立审查建议实验顺序：**协议冻结 → Ch2 → Ch3 → Ch1 → Ch4**；论文写作顺序仍为 Ch1 → Ch2 → Ch3 → Ch4。
- 当前硬事实复核通过：Ch1 MUC 77.47、过并 1,391/欠并 801；Ch2 official 31.37、当前 causal 28.50/subevent 21.05、历史 subevent 24.03；Ch3 macro-F1 .4823 且图输入仅改变 8/17,780 个标签；Ch4 为同一 1,908 个查询的配对评估。
- 两个最早的研究闸门：Ch3 的 48.23 不能当成同协议领先；Ch4 的“消费者依赖性”仍是假设，必须用同实例、同序列化以及同 backbone 的 frozen-vs-finetuned 控制才能升级为因果式表述。

## 2026-08-27 SPEC / phase 现状审计

- `docs/SPEC.md` 仍以 v4/v5 历史叙事为主体，319 行中混有大量已止损机制和旧 headline；其顶层仍写
  “四个有公开对手的任务”以及已被独立审查否定的 Ch3/Ch4暗示，不能继续作为可直接执行的总纲。
- `docs/EXPERIMENTS.md` 建于 2026-07-23，baseline 候选与大量实测记录混在同一文件；可复用的是
  valid-as-test、官方 evaluator、canonical serialization、三种子与如实报数纪律，章节方法矩阵需刷新。
- 四份现有活线契约均有过期方向：A2 仍混入复现修正与方法贡献；C3 仍围绕已被错误剖析推翻的非对称
  代价；D2 把跨 split 的 48.2 写成“已过线”；E2 使用不同语料/不同 backbone 的消费者比较，不能支撑
  “微调导致绕过图”的解释。
- 可直接保留的权威实测仍是 `docs/results/PHASE_A/C/D/E.md`；新 SPEC 必须只引用这些结果，不复制新
  数字，并把旧 phase 契约标为 superseded，而不是删除其历史内容。
- 后续 Gate G0 应先核“协议与资产是否存在”，再设计 GPU 方法实验；筛查本身只允许 CPU/只读命令。

## 2026-08-27 Gate G0 资产初筛

- 本地公开数据主文件齐全：MAVEN-ERE train/valid/test-unlabeled 为 2,913/710/857 文档，MAVEN-FACT
  train/valid 为 2,913/710 文档；但 `data/processed/*/manifest.json` 中的 `processed_dir/raw_dir` 仍指向
  旧 `Fin-EKG` 绝对路径，manifest 元数据需修复后才能称“可移植冻结协议”。
- MAVEN-ERE 官方 evaluator **不在仓库内**；本地 wrapper `scripts/score_maven_ere_official.py` 必须通过
  `--evaluator` 注入外部文件。历史记录称 evaluator 在远端 5090，故当前本地协议门只能判
  CONDITIONAL，直到把 evaluator 的固定 SHA-256、位置和 CPU 恒等 smoke 固化。
- Ch2 训练脚本已经从 train 内划 held-out dev 并按 dev 指标选 checkpoint，这是可复用的防 valid 调参
  基础；Ch1/Ch3 的选择逻辑仍需逐段核验，不能只凭脚本存在判 PASS。
- 本地已有 Ch1 checkpoint 与错误剖析、Ch2 官方口径结果/预测 dump、Ch3 valid 结果、Ch4 canonical
  1,908-query factorial 结果；关系、事实性与 SeDGPL 的完整训练 checkpoint 并未在本地 `runs/` 中全部
  就位，需要根据 `docs/results/`/GPU runbook 核远端位置，不能假定可直接回放。
- Ch4 的同实例基座已实证存在：`runs/cgep/ch4_propagation.json` 记录 710 docs、1,908 instances、
  canonical template order 和 gold/predicted/repaired arms。但当前 factuality 只通过净化/删节点进入，
  尚无“节点属性序列化”接口；frozen-vs-finetuned 同 backbone consumer 也未实现。
- Ch1 `train_coref_scorer.py` 目前对全部传入数据训练固定 epoch，没有 train-internal-dev、best checkpoint
  选择或显式 split manifest；G0 判为 BLOCKED，必须先修协议，不能直接开始新方法训练。
- Ch2 与 Ch3 已在代码中从 train 内划 dev 并按 dev 指标选模；但划分只由 seed/数量临时生成，没有保存
  doc-ID manifest 和 source hash，当前均为 CONDITIONAL，而不是可复现 PASS。
- 现有 CGEP `CgepNode` 只有类型、trigger、sentence、位置，不承载 factuality/evidence；传播脚本的
  factuality arms 只调用 purification 删除节点。Ch4 的事实性属性消费是明确的接口缺口，不能用现有
  “oracle 删除节点”结果冒充。
- 四个主数据文件的 SHA-256、记录数和 doc-ID 唯一性已实算；ERE 与 FACT 的 train 2,913 IDs、valid
  710 IDs 均逐集合完全一致，数据桥梁本身 PASS。
- 三份现有 valid 预测/边 dump 均为 710 条、无重复，且与 MAVEN-ERE valid ID 集合零缺失/零多余；
  Ch1/Ch2 历史产物可作为可追溯 baseline 输入，但仍缺统一 v6 stage bundle 元数据。
- 本地只完整保有 Ch1 encoder/head checkpoint；Ch2、Ch3 与 SeDGPL 的完整 checkpoint 不在本地。
  历史 metrics/dump 不能代替可重跑权重，远端位置须进一步核验。
- `runs/cgep/` 没有冻结的 query/instance manifest；当前 1,908 queries 是运行时重建后只留汇总/排名，
  不满足 v6 的显式 query-ID 冻结要求。
- `runs/` 中没有逐 mention factuality prediction bundle，只有汇总报告；Ch3→Ch4 真实节点属性桥尚未闭合。
- 七个关键 CLI 的本地 `--help` 均通过，说明入口和 CPU import 边界可用；现有消费者 registry 只有
  random/frequency/SeDGPL，没有 frozen 或 text-only consumer。代码搜索未发现主线依赖人工标注或闭源 API；
  `download_datasets.py` 的 manual 仅指需手动取得数据，不是新增人工标签。
- 4090 只读 SSH 核验成功：Ch1、Ch2、official-recipe、Ch3 两档 checkpoint 目录均存在；Ch3 预测边
  dump 与本地副本 SHA-256 完全一致；Ch4 `ch4_sedgpl.pt` 存在（约 1.54 GB）并取得 hash。
- MAVEN-ERE 官方 evaluator 在 4090 `/tmp/maven_evaluate.py` 存在，SHA-256 为
  `32919e86d98c6fafae6aa9505579e2c356caee12c32c1a8c719910acec359598`。它位于 `/tmp`，仍属易失位置；
  G0 需要把 hash 与恢复来源写进协议，并验证 gold-self smoke 后才能把 scorer 判 PASS。
- 本次没有访问 5090，也没有调用 GPU；4090 检查仅为文件存在性/hash。目录内部必需文件完整性尚需
  第二轮只读核验，不能把目录 `stat` 结果直接当可加载证明。
- 4090 第二轮文件清单确认五个 checkpoint 目录的 encoder、tokenizer 与任务 head 均齐全；Ch3 两档还
  包含 evidence head/labels，具备后续加载 smoke 的静态条件。
- 首次 evaluator 恒等 smoke 失败是输入格式错误：labelled raw 数据不能直接充当 official prediction。
  `build_maven_ere_submission.py --from-labeled` 的真实语义是“剥标签后走模型预测”，也不是 gold→prediction
  converter；仓库测试注释记录过 100 分，但当前没有可直接复跑的 gold official-shape fixture/命令。
  因而 evaluator gate 暂为 CONDITIONAL，必须补一个可机械重放的 gold-self 路径后才 PASS。
- 已按 evaluator 源码在本地生成真正 official prediction shape 的 710-doc gold 展开文件，大小
  18,066,953 bytes，SHA-256 为
  `79a2983c50bd8f22944b31e8ce51d9377a3b7a39c9a1a2c60a97abe0e42be508`。合并命令未在返回窗口内给出
  远端评分，故当前只确认本地转换产物，不把缺失输出当作 PASS。
- 远端临时文件 hash 与本地一致，使用固定 evaluator 对 710 文档重跑后 temporal、causal、subevent、
  B³、CEAFe、MUC、BLANC 的 P/R/F1 全部为 100；official scorer 与 mention-pair 展开语义 gate **PASS**。
  仍需把 evaluator 从易失 `/tmp` 迁到可恢复的固定工具位置或记录恢复来源，属于工程归档项而非指标阻塞。
- 全局本地目录与 4090 指定路径均未找到持久化的 MAVEN-ERE official/RESIJ、MAVEN-FACT baseline 或
  BART baseline 源码 checkout；历史 official checkpoint/result 在位，但复现代码只曾放 `/tmp`，现已消失。
  因而四章“多个 baseline 可重跑”当前全部是 CONDITIONAL，不能凭历史分数把 baseline closure 判 PASS。
# 2026-08-27：v6 独立反方审查（本轮）

- 审查范围严格限定为用户点名的 13 份文档及为核实关键外部事实所需的一手来源。
- 初始假设：G0=CONDITIONAL 是待验证结论；现有顺序、双 baseline 门、两轮上限及全局终止条件均不预设正确。
- 分类口径：A=论文可信度硬阻断；B=只在对应阶段开始前修；C=不应阻塞当前阶段。
- 本轮不启动本地或远端 GPU，不修改论文规划正文；只更新本技能的工作记忆文件并交付审查意见。
- SPEC/EXPERIMENTS 初核：四章总问题与组件层/端到端层分离成立，Ch4 明确定位为系统评估而非第四个算法；这两点不构成结构性 NO-GO。
- 首要指标风险：Ch1 把 MUC 单列 headline，可能奖励过合并；需以数据集论文/官方 scorer 核实是否应改为 CoNLL 平均或预注册的多指标联合门，MUC 不宜未经论证独占 promotion。
- “至少两个 baseline”存在口径漂移：总纲要求胜过两个且至少一个强公开实现，G1/G3 又要求先闭合三个代表 baseline，Ch3 实验矩阵写两个强 baseline。必须明确区分“主表最少纳入数”与“需胜过数”。
- G5 同时要求三方法章全部胜出，又称 G1 与 G2 均失败时可收缩为“两方法章 + 一系统章”；若两章失败则只剩一个已过线方法章，条文在算术与论文贡献结构上冲突。
- 历史 valid 已被查看后，internal-dev/final-valid 只能降低继续调参偏差，不能恢复 blind test；后续检查 phase 是否强制 final-valid 单次解封、配置签名和失败后禁止回调。
- Stage bundle 四件套和 hash/ID/schema fail-fast 是有效隔离机制；仍需区分“baseline 仓库工程修补轮次”和“主方法机制 pilot 轮次”，避免把可修复复现问题误升级成研究 NO-GO。
- 工具记录：两次追加发现的补丁因猜错文件中的标题位置/结尾上下文而原子失败，无部分写入；读取实际片段后改用当前精确上下文。
- 13 份指定文档已全部读完。串行 handoff 只要求前章交付 bundle/status、不要求前章 pass，能隔离状态且不会把局部方法失败自动传播为后章阻塞；这是合理设计。
- P1 过度前置：将完整 1,908-query Ch4 manifest列为进入 A3 的必需产物，与 G0 报告“Ch4 只约定接口、不阻塞 Ch2”的文字冲突。启动 A3 只需冻结共享 doc-ID/namespace 和生成器版本；完整 query/candidate manifest 可在 E3 前冻结。
- 三个 phase 的“incumbent/anchor”缺少同 split 明示：A3 pilot 在 internal-dev，却可能把历史 final-valid subevent 24.03 当 incumbent；C4 stop 写“official-valid baseline”。必须规定 promotion 对 internal-dev 重跑锚，最终裁决对 final-valid 重跑锚，禁止跨 split 门槛。
- D3 把“双向条件耦合”事实上升级为方法成立前提，过严。单向 evidence→label 若在标准五类 macro-F1 上稳定胜出且 evidence 不退，已经是可检验的方法贡献；label→evidence 应作为第二假设/消融，失败不应自动否定整章。
- E3 的 consumer validity 与核心假设矛盾：要求 frozen 与 fine-tuned 两消费者各自先有 graph/no-graph 信号，会预先排除“微调消费者忽略图”这一允许为零的结果。应把预测有效性（超过简单下界）与图敏感性分开；至少一个消费者通过图依赖正控即可开展质量效应估计，两者均无图信号才收缩。
- “噪声外退化/增益落入噪声”在各 phase 未机械定义。应预注册主锚、paired bootstrap 单位、CI 判据和最小容忍退化；否则 Done/Stop 仍含裁量空间。
- 全文收缩规则有硬逻辑错误：两个方法章失败只剩一个方法章，不能称“两方法章+系统章”。合理规则应为：一个失败可收缩到两方法章+系统章；两个失败则 v6 结构 NO-GO，必须另行重规划而非 H2 内补洞。
- 历史结果支持 Ch4 的资源可行性及固定 query/rank/paired-bootstrap 工具链，但也显示 factuality 以删节点方式进入是构造性零效应；E3 要求属性消费是必要的阶段前置，不是当前 A3 前置。
- 外部一手核实（MAVEN-ERE）：EMNLP 2022 论文明确用 MUC、B³、CEAFe、BLANC 评共指，其他三种关系用标准 micro P/R/F1；论文还用 MUC F1 画训练规模曲线，故本项目把 MUC 作为 singleton-heavy 数据上的 headline 有官方依据，但四指标仍须共同报告/设护栏。官方仓库公开 train/valid、隐藏 test、single/joint 代码和 evaluator。
- 外部一手核实（资源）：MAVEN-ERE 附录写明 RTX 3090，单项实验约 0.5–2.3 小时、joint 约 3.4 小时；因此 RoBERTa 级 baseline 在 4090/5090 上现实可运行，文档的 95–180 GPU 小时更像含大量复现/三种子/消融的保守总预算，不是单次训练需求。
- 外部一手核实（MAVEN-FACT）：Findings EMNLP 2024 论文与官方仓库确认五类 EFD、非事实 supporting evidence、macro-F1 主结果和 DMRoBERTa 等实现；五类 macro-F1 是公开主指标，不是自造指标。
- 外部一手核实（CGEP）：Findings EMNLP 2024 明确用 MRR 与 Hit@1/3/10/20/50，并在同一表适配 CSProm-KG、SimKG、BARTbase、MCPredictor、SeDGPL 等。MRR/Hit@k 可作 Ch4 公开主指标；`strict MRR`、unscorable、factorial effect/CI 是本项目严谨副指标，不能写成原 benchmark 官方 headline。
- 当前仍 UNVERIFIED：名为 `RESIJ-Trigger` 的确切论文/官方仓库及其与 MAVEN-ERE gold-mention candidate universe 的一致性；常规定向搜索未命中，不能在 P1 前把它预设为必然可用强 baseline。
- RESIJ 身份已核实为 2024 Information Processing & Management 论文 *A graph propagation model with rich event structures for joint event relation extraction*（DOI 10.1016/j.ipm.2024.103811）；它使用 AMR、跨句 arguments、GCN/子图传播和 triadic contrastive loss，并在 MAVEN-ERE 做 joint ERE。公开代码仓库仍未找到，故“论文方法存在”已核实，“代码存在需修/可在两轮内忠实适配”仍 UNVERIFIED。`RESIJ-Trigger` 也不是论文正式方法名，应改为 `RESIJ（若公开实现/忠实复现闭环）`。
- Ch2 创新边界被官方论文进一步压缩：MAVEN-ERE official joint 已手工调四任务 loss factors（0.4/2/4/4）。因此 A3 的 family balance 若只是固定权重/网格，不是新方法；必须在方法 pilot 前冻结一种区别于手工常数的风险归一化、动态梯度平衡或等价可证伪机制。
- Ch3 关键重叠：MAVEN-FACT 原论文的 supporting-word task 已采用“先预测 factuality，再按预测标签找 evidence”的 pipeline，即 label→evidence 已是公开常见方向。D3 的真正方法空间在 evidence→label 或联合软耦合；单独做 label→evidence 不能作为新贡献，双向失败也不应抹掉 evidence→label 的有效贡献。
- Ch3 baseline 结构：RoBERTa+CLS 与 DMRoBERTa 是同 backbone 的分类头 vs dynamic multi-pooling，最适合作为必含强对照；DMBERT是同机制换 BERT，GenEFD 是 FLAN-T5 生成式架构，可作多样性可选项。当前“RoBERTa+CLS + DMRoBERTa/DMBERT”可执行，但优先级应明确为 DMRoBERTa，DMBERT只是替代。
- 资源一手核实：MAVEN-FACT 原论文的 BERT/RoBERTa baselines 为 large 版、10 epochs、单张 RTX 3090；整篇实验约 200 GPU hours。4090/5090 足够，但 D3 的 15–30 小时只在少量 baseline/机制、有效 batch 适配和及时止损下可信，不能把整篇官方实验矩阵照搬。
- Ch4 原论文在 3090/3090 Ti 上以 RoBERTa-base、10 epochs 跑 CGEP-MAVEN，进一步确认单卡可行。公开同表强对照至少包含 BARTbase、CSProm-KG、SimKG、MCPredictor；本项目不必全部复现，但 BART/text-only 与 SeDGPL 是比仅 random/frequency 更有说服力的必含锚。
- 本地实算确认 MAVEN-ERE 与 MAVEN-FACT 的 train/valid 在 document、event、mention ID 三层均完全一致（train 73,939 mentions；valid 17,780；集合差均 0）。因此三章共享桥在身份层真实可行，不是仅凭 doc-ID 猜测；Ch3 属性可无损挂回 ERE 节点。
- P1 固定 291-doc hash internal-dev 上，MAVEN-FACT 的 PS-/Uu 仅 19/14 mentions（13/12 docs）。这不构成数据 NO-GO，但使“稀有类无噪声外退化”的单种子 promotion 很容易误阻断。最低修复不是换 valid，而是保存每类支持数、用 document-cluster bootstrap，并把 guardrail 定义为“不得系统性崩为零/CI 支持的退化”，不能按单点每类 F1 判停。
- 统计硬缺口：Ch1–Ch3 的 mentions/pairs、Ch4 的 1,908 queries 均嵌套于 documents。当前 query/instance-level bootstrap 会把同文档样本当独立，CI 偏窄；确认性 CI 应以 document 为 cluster 重采样，并在每次抽样中保留该文档全部实例。Ch4 多个主效应/交互还应预注册有限的主 contrasts，或对确认性家族做 Holm 校正。
- 强 baseline 的随机性条款过松：A3 写神经 baseline 三种子“尽量”。若最终声称三种子方法胜出，指定 primary anchor 也必须跑 matched 13/17/42（确定性下界可单跑）；否则 method mean 与单次幸运/倒霉 baseline 不对称。
- CGEP 一手边界：论文用 MAVEN-ERE original valid 作 test、从 original train 抽 20% 作 dev，并随机从其他图采 negative candidates；论文未在正文给出 1,908 数，官方仓库虽链接存在但本地既有审计确认缺 MAVEN 派生数据/构建器。故 1,908-query 轴应称“冻结的本地重建 CGEP-MAVEN 协议”，所有消费者统一重跑即可形成严谨系统评估，但不能声称逐项复现论文 Table 2 官方 split/candidates。
- 最终裁决：ACCEPT WITH REQUIRED REVISIONS。数据、标准指标、公开 gold、三层 ID 桥和单卡资源均无课题级硬阻断；现有文档在统计单位、主锚选择、P1 全局/章节条件混合、二级机制合取、consumer sanity 与收缩算术上必须先修。
- 论文级最低生存线：三个方法章全过时结构强度充足；若一个方法章失败，可经明确改纲降为“两方法章+系统评估”；若两个失败，只剩一个方法章，v6 主线 NO-GO，不能在 H2 内称作两方法章版本。
- P1 应拆语义状态：global protocol（数据/manifests/evaluator/bundle）失败才阻塞全部；A3 baseline closure 失败只产出 `A3 blocked/not-started` 状态并允许后续 D3/C4，在治理层决定是否降为两方法章路线。
- 方法胜出最低规则：预先指定同 split primary anchor；stochastic anchor 与 full method 用 matched 13/17/42；方法均值胜 primary anchor 和另一不同方法族 baseline；相对 primary anchor 的 document-cluster paired-bootstrap 95% CI 下界大于 0，护栏用预注册容忍界而非模糊“噪声外”。
- 二级机制不应合取阻断：A3 的 type/direction、D3 的 label→evidence/bidirectional、C4 的 calibrated clustering 失败时删除对应主张；只要核心 family balance、evidence→label、context-discriminative representation 通过公开主指标与消融，章节仍可 promotion。
- evaluator gold-self 必须保留但不充分；P1 还需一组手算非满分 adversarial fixtures（空预测、反向边、coref merge/split、缺 ID）才能检验 wrapper、方向与拒绝路径。

## 2026-08-27：v6 审查整改写回

- 整改只修改 v6 权威协议、阶段契约、实时状态与 G0 活动解释；历史实测数字和无关代码不动。
- 写回必须同时解决五类硬冲突：主锚/统计不可机械判定、局部失败被放大全局、二级机制合取、Ch4
  预测有效性与图敏感性混淆、P1 把 E3 完整 query manifest 过度前置。
- 统一状态模型将区分 `global_protocol_status` 与章节入口/阶段状态；严格串行的含义是必须先交付可审计
  handoff，而不是上阶段必须 PASS。
- 最终确认性比较统一按 document cluster 做 paired bootstrap；随机主锚与完整方法使用 matched
  seeds 13/17/42，final-valid 解封前固定配置、代码、checkpoint、阈值 hash 与访问账本。
- 总纲与实验协议首批修订已落地：Ch4 改称本地重建协议，official MRR/Hit@k 与项目副指标分层；Ch2
  固定权重、Ch3 label→evidence、Ch1 calibration 均不再被误列为必须成立的核心创新。
- 下一批阶段契约必须落实 `status=blocked, executed=false` 的局部 handoff 语义，否则“严格串行但局部
  失败可继续”仍只有原则、没有可执行状态转换。
- P1/A3/D3/C4/E3/H2、TODO 与 G0 已统一局部 handoff、baseline roster、核心/二级机制和 Ch4 正控语义；
  活动文档中未再检出 `RESIJ-Trigger`、query-level bootstrap 或“两章失败仍收缩为两方法章”的旧指令。
- 还需把三种子与 bootstrap 的聚合方式写成机械规则：逐 seed delta 至少 2/3 同向，并在每个文档簇重采样
  中重算三个 seed 的指标后取平均差，避免“CI 是对哪个聚合量”留下实现裁量。
- 第二轮一致性检查发现一个仍可造成泄漏的隐含路径：若 baseline final-valid 先于方法解封，方法仍可间接
  针对 pseudo-test 设计。已改为 baseline/主锚/方法三种子在方法冻结后同一 sealed batch 解封；仅无任何
  指标返回且 hashes 相同的基础设施失败可原样重试。
- Ch4 factorial 还必须冻结消费者权重：若每个 quality arm 各自重训，训练差异会混入构建质量效应。现已
  规定每个 consumer/seed 只训练一次、跨 12 个 quality arms 复用，并以 matched seeds 估计消费者噪声。
- P1 的 gold-self 本身会读取 final-valid gold，因此简单要求 `final access count=0` 会产生虚假账本。现已
  改为逐访问 purpose ledger，并单列 `v6_confirmatory_eval_count=0`；协议 fixture 访问如实记录但不算模型
  确认性评测。
- 串行顺序下 A3 早于 C4，原 A3 契约却要求立即跑 predicted-mention 端到端副表，形成真实反向依赖。现已
  推迟到 E3，并把 same-trigger 等辅助诊断从章节硬门降为仅约束对应 claim，防止自造指标错误阻断。
- 修订后规划层裁决可视为通过本次反方审查；这不等于实验资产 gate 已 PASS。当前唯一合法下一步仍是
  P1，须实际生成 manifests/fixtures/bundle、闭合三个 Ch2 smoke 并做获准的 4090 最长输入 smoke。

## 2026-08-27：P1 执行边界

- 成功标准分两层：共享 manifests/evaluator/bundle 通过才令 `global_protocol_status=pass`；三个 Ch2
  baseline schema smoke、anchor 规则、本地三件套与 4090 最长输入 smoke 通过才令 `a3_entry_status=pass`。
- P1 不运行完整 epoch、不看新模型 final-valid 指标、不访问 5090；gold-self 访问必须记为
  `purpose=protocol_fixture`，`v6_confirmatory_eval_count` 保持 0。
- 初始资产盘点：ERE/FACT 完整 train/valid 与旧 manifest 均存在，但 `data/protocols/v6/`、统一 stage bundle
  实现和 persistent official evaluator 尚未在已列文件中出现。
- `score_maven_ere_official.py` 当前仍要求外部 evaluator 路径且文档声称
  `build_maven_ere_submission.py --from-labeled` 可用于 gold-self；后者实际会走模型预测，不是 gold→official
  converter。P1.3 必须纠正文档并新增真正的 gold prediction 构造/fixture。
- 本地已有 relation loader、submission builder 与训练/评测测试，可复用其 official output schema；P1 应以
  小型垂直实现扩展，而不是另起不兼容协议层。
- 旧 processed manifests 的 `processed_dir/raw_dir` 确实指向已不存在的 `Fin-EKG` 绝对路径；ERE manifest
  还缺 source hashes，P1.2 需要实际修复两份文件而不是只记录问题。
- official evaluator 仍只存在于 `/tmp/maven-ere-eval.X7tKCf/evaluate.py`；当前仓库没有 official baseline
  checkout。该临时 evaluator 可用于比对 hash/内容，但必须从官方来源持久化到明确工具目录并记录来源。
- `train_supervised_relations.py` 已有 internal-dev 逻辑但尚需确认它能接显式 manifest；现有测试集中覆盖
  submission output schema，可作为 gold converter/adversarial scorer 扩展入口。
- 训练脚本确认只能用 `--dev-docs` + model seed shuffle 运行时切分，违反 P1 的显式 ID manifest；需新增
  `--train-manifest/--dev-manifest`（或等价）并让 split seed 与模型 seed 解耦。
- 浏览工具直接打开官方 GitHub/raw evaluator 本次仍返回空结果；不据此判断来源失效。下一步使用
  `git ls-remote`/`curl` 固定官方 commit 与内容 hash，并把网络失败如实保留。
- Git 一手核验成功：MAVEN-ERE `main/HEAD` 当前均为
  `ac81a9711a69f43f55bfbc50b3bb573fd11c64b0`；官方 raw `evaluate.py` 与本地临时副本 SHA-256 均为
  `32919e86d98c6fafae6aa9505579e2c356caee12c32c1a8c719910acec359598`。
- 仓库没有既定 `third_party/external/vendor` 目录；`data/*` 默认忽略且 P1 产物本就约定在
  `data/protocols/v6/`。适合把 pinned external checkout/tool 作为可重建本地产物放在那里，并以 tracked
  fetch/freeze 脚本和 protocol hashes 保证追溯，而不是把整个 GPL 仓库直接纳入当前 Git diff。
- 数据 schema 已核：ERE 使用 `causal_relations`，FACT 使用 `causal_relation`，FACT factuality/evidence 在
  event mention 上；manifest 生成器不能假设两套关系字段完全同名，但可按共享 doc/event/mention IDs 验证。
- 当前本地 relation candidate universe 是按文本顺序的全部有向 event-mention pairs（排除 self）；official
  scorer 同样枚举全部有向 mention pairs，并对 gold cluster-level relation 展开。P1 candidate digest 可据
  `doc_id/head_id/tail_id` 的稳定排序生成，并分别保存 docs/mentions/ordered-pairs/positive labels counts。
- official evaluator 不会拒绝重复/缺失 document IDs；拒绝逻辑必须在本项目 wrapper/bundle validator 中
  实现，不能把 fail-fast 责任推给官方脚本。
- 固定 commit 的官方源码已核实：`causal/src/data.py::Document.get_labels` 与
  `joint/src/data.py::Document.get_relation_labels` 都把事件级 causal/subevent 关系展开到两个 event
  cluster 的全部 mention 笛卡尔积，再对全部有序 mention 对赋标签。因此本地只标首 mention 的行为是
  A3 前必须修复的候选标签协议错误，不是可忽略的工程风格差异。
- 官方 causal/joint 的 `dump_result.py` 都按匿名 `event_mentions` 文本顺序枚举有序 mention 对并输出官方
  submission schema。P1 可用固定标签经过这些原始 adapter 做真实 I/O smoke，但产物必须标记
  `schema_only=true, model_execution=false`；它不能算 baseline 得分或复现证据。
- 历史 `docs/results/PHASE_A.md` 记录过官方 causal 原版在同一 historical valid 上跑通并得到 31.37；当时
  checkout/补丁位于 `/tmp`，且评的是完整 710-doc historical valid。它只证明路线曾可运行，不能替代
  v6 冻结 internal-dev 上的三路 smoke，也不得进入 v6 确证结果表。
- `train_supervised_relations.py` 还有两项必须随显式 manifest 一起修的污染：当前先从全部 train docs 构造并
  下采样 rows、算 class weights，再运行时抽 dev；同时 dev 评测复用了下采样后的 rows。这样 dev 文档会
  影响训练样本/权重且评测候选不完整。正确闭环应先按 manifest 拆 docs，只对 train rows 下采样/算权重，
  dev 始终使用未下采样的完整候选 universe。
- 现有 `RelationDocument.representative` 只保存 event→首 mention，无法从归一化对象还原所有 cluster members；
  最小兼容修复是在 loader 增加 event→all mention IDs 的 `clusters` 映射，并让 `pair_examples` 通过明确的
  `expand_event_relations=True` 参数展开非 coreference gold。保留旧默认可避免悄然改写历史结果，v6 manifest
  与训练脚本则必须显式启用并记录该参数。
- P1 源文件本地重新核验：ERE train/valid 为 2,913/710 docs，SHA-256 分别为
  `6a5519fe7c30448690adb13d49217c50d474fc57480eae10aecb29df7eb638b7`、
  `6faea0e4e16b4a2d5d9631e09ef6e1c6bac6e3f912490bfc48eeaceaf98c6153`；FACT train/valid 为
  2,913/710，hash 分别为 `190522b44f0702af030161924d7cb94c4a06bd5d6e2b40d79f8f1eaa5886bab7`、
  `396fcf0779b67f0229f2cdaad4df0771682d9238a94b082d61659059b8dc7cff`。这四个值应由 freeze 脚本重算后写入
  registry，不能硬编码成“预期通过”。
- FACT evidence 原字段是 mention 级 `evidence_word`/`evidence_offset`，不是 `evidence`；支持统计与 schema
  冻结必须读取真实字段名。processed manifests 的两个旧绝对目录均指向 `Fin-EKG`，ERE 还缺全部 source
  hashes，确认 P1.2 是实际数据治理修复而非文档清理。
- Ch4 已有实际生成器 `src/ekg/succession/data/cgep.py`，schema 是 `CgepInstance(instance_id, doc_id,
  nodes, edges, candidates, label)`，默认候选数 512；P1 应冻结该源码 hash、参数接口和共享 namespaced
  event-ID 规则，而不运行 `build_cgep` 或提前生成 1,908-query manifest。`scripts/build_cgep.py` 只是 CLI
  wrapper，其 hash也可记录为恢复入口，但 E3 才冻结具体 queries/candidates。
- 已实现并以 17 个 CPU 单测验证候选标签与 split 修复：loader 保存完整 clusters；v6 可显式启用官方
  mention 笛卡尔积标签；训练器接受 train/dev manifests，先拆 documents 再仅对 train 下采样/算权重，dev
  保持完整候选。旧运行时 split 仍仅为历史重放保留并打印 exploratory 警告，v6 命令必须显式传 manifest。
- official scorer 闭环已真实通过：固定 hash evaluator 对 710-doc valid 的 gold→mention-pair converter 在
  temporal/causal/subevent 与 B³/CEAFe/MUC/BLANC 全部返回满分；四个手算 fixture（empty、reverse causal、
  coref merge、coref split）的预期 F1 全部逐项断言通过。冻结候选 population digest 为
  `6afb6ae68449b1c1fb9024b92ff37009715e504b26cae78ccfe4f3f1cc71541a`；协议访问已写 ledger，确认性计数为 0。
- wrapper 现在会在调用官方 evaluator 前拒绝缺/多 doc、重复 doc、未知 endpoint、自环、重复/冲突 pair、
  subtype key 缺失及 candidate digest 漂移，切断官方原脚本“静默按 NONE 计分”造成的截断传播链。
- P1.1/P1.2 freeze 已首次完整通过：2,622 train、291 internal-dev、710 final-valid，6 份 ERE/FACT 显式
  manifests 均有 registry 外部自 hash；FACT dev 重新算得 CT+ 6,835、CT- 129、PS+ 198、PS- 19、Uu 14，
  PS-/Uu 文档支持 13/12，与契约完全一致。两份 processed manifest 已改为仓库相对路径并补齐每个 split
  的 records/hash。
- Ch2 冻结 population：train/internal-dev/final-valid 的 event mentions 为 66,744/7,195/17,780，全部
  ordered mention pairs 为 2,297,524/234,870/613,706；candidate 与 expanded-label digest 已分别保存。
  scorer wrapper 与 manifest 现已使用同一 text-order namespaced pair 编码；final-valid 两端独立重算均为
  `b551c033b4c265a72619f52fc0585e122328a78ed16f40e35264fff8e2a6d4e6`，不是以计数相等代替 hash 相等。
- Stage bundle 四件套已实现强校验：artifact hashes、schema、expected ID set/digest/count、population count、
  candidate digest 和 upstream bundle references 任一漂移都会 fail-fast；坏 hash、重复 ID、缺失 ID、未知
  upstream 四条传播路径均有单测并已通过。
- 固定官方 single/joint 源码在当前 transformers 栈确有两个可复现兼容点：两份 `main.py` 都从已移除的
  `transformers.AdamW` 导入；joint `src/model.py` 把 RoBERTa config 错按旧继承关系要求为 `BertConfig`，
  且默认模型路径硬编码 `/data/MODELS/roberta-base`。这些是透明工程 patch 的合法范围，不能改变数据、
  candidate 或 scorer；patch 文件/应用脚本需固定后才能把“可执行 source”判 PASS。
- 官方 causal 子目录自身没有 model 实现，`main.py` 通过 `sys.path.append('../')` 引用 checkout 顶层
  `utils/model.py`；后续 patch/静态闭环必须按这个真实共享模块布局，不能臆造 `causal/utils` 路径。
- Official source compatibility patch 现已由恢复脚本 cleanly apply 并通过 `git diff --check` 与四文件
  `py_compile`：仅把 AdamW 改从 torch 导入、把旧 BertConfig 继承判断换为 AutoModel；未改标签、候选、
  loader、dump adapter 或 evaluator。三份上游文件是 CRLF，应用器显式只忽略空白差异，仍禁止 partial/reject。
- P1.5 三路同一 10-doc fixture 已实际通过 strict wrapper：local pair、official single、official joint 都输出
  完整 official schema，10 docs/232 event mentions/6,508 ordered relation pairs 与 candidate digest
  `313ec48e657374bc5afb7d09df9282c32f1d7a3acfdbfe1bc35435765042df3c` 三路一致。此次用各自真实 dump
  adapter + constant NONE vectors，仅证明 I/O/candidate closure，已强制标 `schema_only=true,
  model_execution=false`，不得作为 baseline 指标。
- P1 本地完整 gate 已通过：`364 passed, 12 skipped`（skip 均为本地无 torch 的既有 GPU tests）、全量 ruff
  `All checks passed!`、`ekg-smoke OK`；命令、return code 与完整 stdout/stderr 已写
  `data/protocols/v6/local_gate.json`，不是仅在对话中声明。
- 历史 Ch2 交付路径按权威结果档案是 `runs/relations/window_dist_20ep_macro`（当前 v6 前最优）而非起点
  `supervised_maven`；P1.6 应先只读核 4090 实际文件，再以存在且 heads/config 齐全的历史档做 load/forward。
  若最优档只在另一台机器，不能未经授权搬运；可退回 4090 上明确存在的历史 checkpoint 做兼容 smoke，
  但 metadata 必须说明它验证的是接口兼容而非最佳模型能力。
- P1 条件 bundle 已生成并由真实 reader 重读通过：`global_protocol_status=pass`，仅
  `a3_entry_status=conditional`；四件套在 `runs/stages/P1/p1-v6-20260828/`。这证明全局 manifests/evaluator/
  bundle 已放行，4090 连接问题只保留为 A3 入口局部条件，未错误回滚全链。
- 冻结 291-doc internal-dev 中按公开 source token count 的最长文档为
  `c5e2a4e212ab534072d53d07101c1b75`（1,723 tokens）；相同选择规则、gold/test fixture 与 hashes 已加入
  baseline summary，供恢复连接后做真实前向，不从 final-valid 挑“最难样本”。
- 4090 隧道连续三次都未完成 SSH 握手（peer reset 一次、banner timeout 两次），故 P1.6 没有任何远端命令
  实际运行；按 runbook 不能推断 checkpoint/GPU 状态，更不能写成 smoke PASS。当前持久状态准确为
  `global_protocol_status=pass, a3_entry_status=conditional`，remaining condition 只剩 P1.6。
- Registry 与 bundle 已重读核对：global PASS、A3 conditional、confirmatory count 0、primary anchor null；
  这是 infrastructure 条件未闭合而非 baseline 科研失败，不应生成 A3 `blocked/executed=false` 假结论。
- 最终本地从 source restore 开始全链重放通过，确保 manifest/code hashes 指向最终文件：fetch→freeze→
  710-doc scorer gate→三路 baseline schema→364 tests/ruff/smoke→bundle rebuild 全部 PASS；随后独立复核六份
  manifest hashes、四 source hashes、evaluator hash、candidate digest、ledger、bundle reader 与六份文档链接，
  输出 `P1_FINAL_LOCAL_AUDIT_PASS`。
- 2026-08-28 恢复诊断：Codex 环境把 alias 解析为 `TJK@18.tcp.vip.cpolar.cn:14147`；TCP connect 立即成功，
  但直接 `nc` 等待 10 秒收不到 SSH server banner，`ssh` 因而在 banner exchange 超时。故不是本地 DNS/
  端口拒绝或 key 认证问题，阻塞发生在 cpolar 接入后、SSH 握手前；远端仍没有执行任何命令。
- 同一 WSL 用户下确有作者刚建立的活动进程 `ssh gpu-4090`（PID 66013，PTY `/dev/pts/13`），但未启用
  ControlMaster/control socket，Codex 不能安全复用该连接。不得向作者 PTY 注入命令或终止其 session；最小
  协作动作是请作者退出该临时交互 session 后再建立 Codex 的独立 SSH，或由作者明确选择在该 session 代跑。
# 2026-08-28 · P1 独立反方复验（续）

- A3 的项目内关系训练器支持显式 `--train-manifest` / `--dev-manifest`，并检查重叠与遗漏；但仍保留旧式 `--dev-docs` 动态切分路径，v6 正式运行必须在命令与结果记录中显式禁止该路径。
- MAVEN-ERE 官方 causal/joint 入口把数据目录与 `train.jsonl`、`valid.jsonl`、`test.jsonl` 写死为相对路径；当前 P1 只证明了 10 文档 schema smoke，不等于已存在一个会按冻结 manifest 生成/装配三份正式输入的 full-run adapter。A3.0 开跑前必须把这一输入假设和转换产物纳入可哈希验证的运行协议。
- A3 契约要求三个 baseline “使用相同 manifests”，但仓库中只有 schema smoke adapter；未找到 official single/joint 的正式 manifest materializer/launcher。官方入口还分别使用 `roberta-base` 网络名与 `/data/MODELS/roberta-base` 绝对路径，且输出目录固定，正式运行必须在 A3.0 做透明适配并冻结具体命令。
- 检索命令误把不存在的 `data/protocols/v6/baseline_smoke` 列为路径；`rg` 报错但其余目标结果有效。实际产物目录为 `data/protocols/v6/baselines/`。
- `validate_stage_bundle()` 只重算 bundle 内 `predictions.jsonl`、`metrics.json`、`status.json` 的哈希和 ID 集；它既不解析/重算 `protocol.hashes` 指向的数据、manifest、evaluator、config、code、checkpoint，也不接受一个可信的 `protocol.json` 预期哈希。因而修改外部证据甚至修改 `protocol.json` 中的外部哈希后，验证器仍可能 PASS。
- `registry.json` 虽写入 `p1_bundle_protocol_sha256`，仓库中没有任何下游读取或校验该字段；检索到的 `validate_stage_bundle()` 调用仅为 P1 builder 自检和单元测试。当前“hash-bound handoff”尚未形成可执行的信任链。
- `build_p1_bundle.py` 对 P1.6 的放行仅检查 `remote_smoke.json` 顶层 `status == "pass"`，未检查命令、git identity、checkpoint/input/output/log 哈希、return code、skipped docs 或日志计数，存在伪造/陈旧 pass 文件误放行风险。
- 隔离反证已证实上述两项不是理论风险：篡改临时 bundle 的 data/evaluator 声明哈希后 `validate_stage_bundle()` 仍 PASS；只提供 `{"status":"pass","checkpoint_hashes":{"fake":"not-a-sha256"}}` 的伪远端 JSON，P1 builder 返回 0 并写出 `a3_entry_status=pass`。
- 当前 P1 bundle 的 `hashes.candidate` 与 `population_counts` 只对应 10-doc smoke（digest `313ec48e...`，10 docs/232 mentions/6508 pairs），没有绑定正式三 split 的 `ch2_candidate_protocol.json`（文件 SHA-256 `2102c325...`）。正式 A3 candidate identity 只存在于可变的 registry/外部文件中。
- `access_ledger.json` 当前 SHA-256 为 `6b524a95...`，但 registry 和 bundle 都未记录该哈希；status 只记录路径。历史 final-valid 访问控制因此没有不可变绑定。
- `remote_smoke.json` 的现有 checkpoint/input/runtime/inference 证据已独立对账为真，但没有 exact command 或 elapsed time 字段（读取为 null/不存在）。这不推翻现有 smoke，却削弱可复现命令链。
- 文档与实现存在直接冲突：SPEC §6 要求下游读取 bundle 前验证所有 hashes；P1.4 要求读取校验 data/manifest/candidate/evaluator/config/code/checkpoint；PHASE_P1 结果又称 reader “重读通过”。实际 reader 只验证三个内置 artifact 哈希。故当前 `P1 COMPLETED/PASS` 和 `A3 ENTRY PASS` 对“错误隔离协议已闭合”的表述过强。
- P1 的底层数据、manifest、candidate、evaluator 与真实 4090 smoke 均经本轮独立重算/对账为正确；因此问题属于闸门实现与不可变封装缺陷，不应升级成课题级 NO-GO，也不要求重做 GPU inference。最小处理是修 validator/builder、将正式 candidate protocol 与 access ledger 哈希绑定进新版本 P1 bundle，再重新机械验收。
- G0/P1/TODO/phases/results 的状态文本彼此一致地写作 PASS，但它们共同依赖同一过弱 validator，而不是相互独立证据；这不是多源交叉验证。
- 访问账本目前能披露四次 protocol-fixture 访问和 `v6_confirmatory_eval_count=0`，但没有被 bundle 哈希绑定。更严重的是 `verify_p1_scorer.py::_record_access()` 每次运行都会无条件把计数赋回 0；若在以后已有确认性访问时误跑该工具，会抹掉计数。账本更新必须改成只追加且禁止递减，protocol fixture 不能重置全局计数。
- P1 preregistration 的 anchor roster、13/17/42、10,000 次 document-cluster bootstrap、1.0 F1-point subevent margin 与 sealed final-valid 规则均已明确，内容本身可执行。
- `freeze_v6_protocol.py::_update_access_ledger()` 与 `verify_p1_scorer.py::_record_access()` 两处都无条件执行 `v6_confirmatory_eval_count = 0`。这必须同时修复，否则任一 P1 重放都能回滚访问计数。
- 工作树已有大量 v6 规划/P1 相关未提交改动；本轮审查未改生产代码或权威结果，只新增/更新工作记忆 `task_plan.md`、`findings.md`、`progress.md`。registry 已诚实记录生成时 `working_tree_dirty=true`，但未来正式 code identity 不能只依赖 commit，应继续保留逐文件代码哈希。
- `run_p1_baseline_smokes.py` 的 schema wrapper 本身严格，三路 fixture 也已独立重放一致；但 smoke metadata 没有 P1.5 明文要求的 `input_assumptions`，且它只调用 official dump adapter，不调用官方 tokenizer/data loader/model/training loop。结论只能是 dump-schema 适配闭合，不能表述为正式 baseline 启动链已经闭合。
- `score_maven_ere_official.py` 的 `--candidate-digest` 是可选参数，且对 `--evaluator` 不做固定 SHA-256 校验，输出 JSON 也只含分数、没有 evaluator/gold/pred/candidate hashes。P1 fixture verifier 会严格检查 evaluator hash，但 A3 正式 scorer CLI 不会；这会允许 A3 误用不同 evaluator 或漏传 candidate digest。必须在第一轮 baseline 评分前 fail-fast。
- strict official prediction wrapper 对文档集合、endpoint、schema、自环、重复/冲突 pair 与 candidate digest 的检查逻辑成立；现有单测未显式覆盖 self-pair、缺 subtype、extra doc、重复 coref mention，尽管本轮手工反例已验证实现会拒绝。建议补成永久回归测试。
- P1 freezer 的 `_read_jsonl()` 会拒绝缺失/非字符串/重复 doc ID，且独立复算已确认现数据无此问题；该组件本身通过。
- A3 本地关系训练器把 `--official-mention-expansion` 文档化为 “required for v6”，却没有实际 `parser.error` 强制；漏传时会静默使用不同的 event-relation label expansion。它也只读取 manifest 的 `doc_ids`，不校验 manifest/source SHA 或冻结 candidate-label digest。第一轮 local-pair baseline 命令若少一个 flag 就会产生非同协议训练，当前闸门不会提前阻断。
- A3 训练器仍允许无 manifests 的 legacy 随机 split，只打印 WARNING。保留旧用法可以，但 v6 正式 launcher 必须是独立的 fail-fast 入口，强制两个 manifests、official mention expansion、预期 manifest/source/candidate hashes；不能依赖操作者手工不漏参数。
- 本地 trainer 的 checkpoint 保存只写 encoder/tokenizer 和 `heads.pt`；未保存训练 CLI、manifest hashes、candidate-label digest、seed、best epoch/dev metrics 等 run provenance。A3 契约要求 config/code/checkpoint 可追溯，因此正式 baseline 不能直接靠当前脚本裸跑，须先补 run metadata/bundle writer。
- `build_maven_ere_submission.py` 捕获关系推理 `ValueError` 后为该文档写空关系并仍返回 0。P1 smoke 恰好 `skipped_documents=0`，所以现有证据不受影响；但正式 A3 确认性导出必须在任何 skipped document 上失败，不能只打印警告继续。
- `evaluate_relation_pairs.py` 会用字典覆盖重复预测 doc、把缺失 doc 当空预测、忽略 extra doc，且不绑定 candidate digest；它不满足 v6 主表 fail-fast 规则。A3 主表应只走加固后的 official scorer；该脚本至多保留为明确标注的历史/诊断工具，或同步加严。
- 当前工作树复验：`uv run pytest` 为 364 passed / 12 个预期 no-torch skips；`uv run ruff check src tests scripts` PASS；`uv run ekg-smoke` PASS。普通回归门是绿的，但现有测试未覆盖本轮发现的协议反例。
- 最终独立门状态应暂时回退为 `global_protocol_status=CONDITIONAL`、`a3_entry_status=CONDITIONAL`；不是 BLOCKED。底层证据无需重做，完成 bundle/ledger/scorer/A3 launcher 的有界修复与新 bundle 复验即可恢复 PASS。
- 在修复前，不应启动第一轮 A3 GPU baseline；允许继续本地完成这些前置修复。Ch3/Ch1/Ch4 的远期缺口仍不得被提前拉入 P1。
- 远端 smoke 使用 clean HEAD `c642bb88...`，本地 bundle 生成于同一 HEAD 的 dirty worktree。相关本地 diff 中 `_parse_unlabeled` 只新增 singleton `clusters` 元数据，P1 回传输出又通过当前 strict schema/candidate 对账，因此现有 remote smoke 的接口结论仍成立；它不能替代未提交 v6 label-expansion 训练路径的正式 GPU smoke，这一点原结果文档已有 claim boundary。
- 工作记忆更新曾因 `task_plan.md` 的 Phase 13 实际条目措辞与补丁预期不一致而失败；该次 patch 原子失败，未改任何文件。随后分离更新并先读取真实段落。

## 2026-08-28 · Phase 14 实施决策

- P1.6 的实际 shell command 未持久化在仓库；日志、metadata 与会话记录足以重建等价 reproduction command，但不能诚实冒充原始 executed command。新 schema 将分别记录 `executed_command_available=false`、可重放命令与既有 wall-time 证据，正式 A3 起强制保存实际 argv。
- 新 P1 bundle 使用新 ID/schema，不覆盖 `p1-v6-20260828`；可信入口由 registry 的 protocol SHA-256 加 repository-root 外部证据重哈希共同构成。
## Phase 14 test-gap confirmation (2026-08-28)

- `tests/scripts/test_evaluate_relation_pairs.py` still invoked the evaluator without the newly required candidate digest and did not cover duplicate/missing/extra prediction documents.
- `tests/scripts/test_maven_ere_submission.py` covered payload shape only; it did not prove that skipped relation documents fail the default submission build.
- `tests/relations/test_maven_ere_official.py` covered several strict-wrapper failures but still lacked explicit extra-document, self-pair, missing-subtype, and repeated-coreference-mention counterexamples.
- These are protocol-boundary tests, not optional coverage: each omitted case can otherwise convert malformed output into an apparently valid score.

## Phase 14 scorer provenance check (2026-08-28)

- The tightened official scorer now has the required enforcement points: pinned evaluator hash from `source_lock.json`, exact prediction/gold document validation, required candidate-population digest, and a v2 report carrying evaluator/gold/prediction/source-lock hashes plus actual argv.
- It still lacked a direct regression test proving both the successful gold-self path and rejection of an evaluator whose bytes no longer match the source lock; those tests are required before treating the scorer wrapper itself as frozen evidence.

## Phase 14 A3 trainer boundary (2026-08-28)

- The current supervised trainer accepts arbitrary paired manifests and merely checks ID partitioning; it does not bind `registry.json`, source SHA-256, the registered train/internal-dev manifest bytes, or the frozen candidate/expanded-label digests.
- `--official-mention-expansion` remains optional even when manifests are supplied, so a command can consume the correct document IDs while training against the wrong label population.
- The correct fix is a CPU preflight before importing torch: require the P1 protocol root for v6, re-hash source/manifests/candidate protocol, recompute train and internal-dev summaries, and reject final-valid or any drift. Legacy exploratory mode may remain explicit but cannot count as A3 confirmation evidence.
- The trainer also needs a run metadata file containing actual argv, protocol/input/code hashes, seed/hyperparameters, final-valid non-access declaration, and checkpoint hashes/status.
- Both registered MAVEN-ERE train/internal-dev manifests already carry `dataset`, `split_role`, `source_path`, `source_sha256`, `source_records`, `doc_count`, and exact IDs; this is sufficient for fail-fast identity binding without inventing a second manifest format.
- A registry alone is not a trust root because coordinated edits to the registry and evidence could agree with each other. Formal A3 commands must also supply the frozen P1 `protocol.json` SHA-256 and validate the registry-selected v2 stage bundle against that external expected digest before training.

## Phase 14 official-baseline execution surface (2026-08-28)

- Official causal and joint code both hard-code `../data/MAVEN_ERE/{train,valid,test}.jsonl`, write checkpoints/output relative to their own task directory, and select checkpoints on `valid`; therefore an isolated source/data workspace can safely map P1 internal-dev to `valid` and map the same internal-dev IDs to an unlabeled-shape `test` for pre-final baseline selection.
- The causal entry loads tokenizer `roberta-base`; joint loads `/data/MODELS/roberta-base`. These are path assumptions, not scientific method differences, but they must be made explicit and preflighted rather than silently relying on a server cache.
- A launcher can preserve source fidelity by using the pinned patched checkout unchanged and constructing the expected relative directory layout. Model resolution should be checked before launch; changing upstream model/data semantics is unnecessary.
- A3.0 already requires all three baselines and forbids final-valid before anchor freeze, so the missing implementation is a CPU materializer plus a command-plan/launcher that records exact argv, cwd, hashes, model-path assumptions, and immutable output locations.
- The local pair trainer previously selected over all relation heads, including temporal; that contradicts A3's causal/subevent-only frozen candidate protocol and lets temporal dominate selection. Formal v6 local-pair runs must use exactly causal+subevent for loss/selection. The official joint baseline may remain faithful to its published multi-task implementation, while only causal/subevent enter the A3 primary table.
- The labelled MAVEN-ERE train source is about 97 MB and the pinned official checkout is under 1 MB, so an isolated three-file official workspace is practical on local disk and does not require GPU or a new dataset copy service.
- The official repository README pins the reproduction recipes more tightly than the Python defaults: causal uses 50 epochs/eval-500/batch-4; joint uses 100 epochs/eval-200/lr 3e-4/encoder-lr 2e-5/accumulation-4/batch-8. The execution plan should preserve these values and treat any later budget reduction as an explicitly different baseline variant.
- Training alone is not a full baseline result: the local trainer only writes a checkpoint, and official single writes a partial causal payload. The launcher must add deterministic inference/normalization and frozen scorer output before a run can enter the A3 table; raw checkpoint or upstream output existence is insufficient.
- The existing local inference path can be reused (`evaluate_relations.py` with raw/identity config), but the checkpoint must declare active families. Otherwise a formal causal+subevent run serializes an untrained temporal head and the generic extractor can emit random temporal edges. Loading `configuration.families` from run metadata and filtering inference is the minimal faithful fix.
- Tightening candidate-digest arguments also makes old CLI examples incomplete. Active help and phase documents must show an explicit frozen digest; archived historical commands may remain only when clearly labeled historical rather than executable v6 recipes.

## Phase 14 regenerated protocol evidence (2026-08-28)

- Pinned external assets revalidated at commit `ac81a9711a69f43f55bfbc50b3bb573fd11c64b0`; evaluator SHA-256 remains `32919e86...c359598`.
- Re-freezing produced the same Ch2 candidate-protocol SHA-256 `2102c325...8871b`, which independently confirms the refactored public summary is byte/semantics compatible with the prior frozen population.
- The append-only ledger retained all four disclosure entries and `v6_confirmatory_eval_count=0`; its full-file SHA-256 is now present in the registry (`6b524a95...1e3e9`).
- Freeze correctly reset global/A3 status to `conditional` and cleared the old bundle identity. No stage is re-promoted until the new local gate and v2 bundle validate.
- The first r1 bundle passed v2 validation, but subsequent A3 precheck exposed mixed local/remote run paths. Because the materializer/launcher are included in P1 code hashes, r1 must be superseded after the path fix; it cannot remain the selected trust root.

## Phase 14 final trust root and documentation drift (2026-08-28)

- After fixing remote path binding, the rebuilt `p1-v6-20260828-r2` bundle passes both creation-time and independent `--validate-only` checks. Its trusted `protocol.json` SHA-256 is `249b457675b212db3871be8d72044006906ee6ac922737d29d69be21857d002f`.
- The r2 A3 materializer validates 2,622 train + 291 internal-dev, explicitly records `final_valid_accessed=false`, and all three seed-13 no-execute launcher checks now print internally consistent `/data/TJK/ekg` commands/cwds/outputs.
- Active docs still cite the superseded unversioned P1 bundle and old test count (364 rather than 391), and A3 lacks the new trust-root/preflight command contract. These are documentation defects that must be corrected before handoff.
- Historical G0 tables retain pre-P1 conditional rows; their top execution-update section must clearly dominate those rows so readers do not mistake the archival static screen for current state.
- Active bundle paths/test counts have now been synchronized to r2/391; the remaining `checkout 待持久化` hits are in the Ch1 baseline table and are also stale because the shared official checkout is already pinned, although C4-specific full runs remain pending.

## Phase 14 final A3 plan binding (2026-08-28)

- The A3 execution plan is executable state, not merely documentation. The launcher now requires its externally supplied SHA-256 and rejects any extra/missing source or data file, so command tampering and unplanned Python injection cannot hide behind internally consistent file hashes.
- This last code change correctly invalidated r2. The selected final trust root is now `p1-v6-20260828-r3`, protocol SHA-256 `e449e7313c2b0b9235b413f3292877f1a842e4ed85be4d7ba020d28601c4f84f`.
- The deterministic r3 A3 plan SHA-256 is `9ea3aa84acc1e781256aadc45cf3078775952f91a71ba78526718356f2a18bdf`; all three seed-13 prechecks pass and an intentionally wrong plan hash is rejected before command display/execution.

## Phase 14 closure audit (2026-08-28)

- The authoritative P1 result and active A3 contract consistently name r3, protocol SHA-256 `e449e731...c4f84f`, and A3 plan SHA-256 `9ea3aa84...a18bdf`.
- Both documents preserve the evidence boundary: the plan is a local CPU preflight artifact, remote A3 must rematerialize it under `/data/TJK/ekg`, and no A3 GPU process has been started.
- r1/r2 remain immutable superseded audit artifacts; neither is selected or referenced as an executable trust root in active documents.
- The registry's canonical selection field is `p1_bundle_id`, not `selected_stage_bundle`; it resolves to `p1-v6-20260828-r3` and is paired with the externally revalidated `p1_bundle_protocol_sha256`. The initial empty lookup was a diagnostic field-name mistake, not missing state.

## Phase 15 handoff boundary (2026-08-28)

- The local tree predates Phase 15 with mixed uncommitted work: P1/A3/v6 changes coexist with older Ch1/v5 edits (`PHASE_C`, coreference metrics/profile code, old phase contracts). A blanket `git add -A` would incorrectly commit unrelated work.
- Git ignores both `data/*` and `runs/`. The remote cannot reconstruct/validate P1 r3 from the code commit alone: `data/protocols/v6` is 20 MB (dominated by the 18 MB official gold-self prediction) and the r3 four-file bundle is 28 KB. These must travel as data/artifacts with a dual-end SHA-256 check, while the 100 MB local A3 preflight should not be copied because the contract requires remote rematerialization.
- The small `patches/p1` and `tests/fixtures/p1` trees are source/test assets and belong in the Git commit. Planning scratch files, session handoff state, old Ch1 work, and the full 7.1 MB research/PDF archive are not required for the remote A3 executable surface.
- Active executable documents link only two replan artifacts: `G0_PROTOCOL_GATE_SCREENING.md` and `INDEPENDENT_THESIS_FEASIBILITY_REVIEW.md`. Raw Deep Research exports are not a runtime or link dependency and should remain uncommitted in this handoff; this also preserves their original formatting/citation state.
- The final staged boundary contains 55 P1/A3/v6 files (6,889 insertions, 902 deletions). Its 70 local Markdown links all resolve inside the Git index, cached whitespace is clean, and explicit exclusion checks confirm no planning scratch, old `PHASE_C` result, coreference metric implementation, or error-profile script is staged.
- Commit `53ce6f1` contains exactly that 55-file boundary and is one commit ahead of the fetched `origin/main`; no excluded path appears in its tree diff. The non-force push advanced `origin/main` from `c642bb8` to `53ce6f1` successfully.
- Remote `/data/TJK/ekg` was clean at `c642bb8`, had no project training process, and all four RTX 4090 cards were idle (17–18 MiB, 0% utilization). The runbook fetch/reset advanced it cleanly to `53ce6f1` without touching ignored run artifacts.
- The required ignored evidence was reduced to a 1.9 MiB archive containing only `data/protocols/v6` and P1 r3 (the local A3 preflight was excluded). Local and remote archive SHA-256 are both `65cc585464d8614b44a2c95d1aa05e2c016802b271d4c194d2b62bf103932a1a`.
- After the successful code/data transfers, the cpolar endpoint regressed to accepting TCP without emitting any SSH identification banner: `nc -vz` succeeds, but a 15-second raw read returns zero bytes. There is no local user SSH process or reusable control socket, and the alias still resolves to `18.tcp.vip.cpolar.cn:14147`. This isolates the current block before SSH authentication or remote command execution.
- Remote clean-checkout validation exposed that r3 is not portable: its protocol digest transfers intact, but `local_gate.json` records a repository-wide Python file count from the local dirty tree. Selectively excluding unrelated Ch1 work changes that count on clean `53ce6f1`, causing a legitimate fail-fast rejection. Copying or committing the unrelated files would hide the coupling; the gate must instead bind the controlled P1 code identity and reproducible commands, then be regenerated as a new immutable root.
- Source inspection refines the fix: `_validate_local_gate` is correctly enforcing the exact tree that the full pytest/ruff/smoke commands tested. Weakening it to P1-only files would overstate test coverage. The right repair is to rerun the local gate and build a new immutable bundle from a detached clean `53ce6f1` worktree, using a scoped copy of required ignored data rather than the 4.8 GB whole data tree.
- Initial dependency inventory limits the clean-worktree copy to the 68 KB fixtures, the MAVEN-ERE processed split files needed by P1 tests/builder, the 20 MB v6 protocol evidence, and the 4.6 MB ESC file used by two succession tests. Unrelated raw/processed corpora dominate the 4.8 GB tree and must not be copied speculatively.
- Direct test references confirm ERE train, v6 protocol, fixtures, and ESC; bundle construction also reads ERE valid. FACT may still be required indirectly by the stage bundle's frozen external hash set, so the clean copy scope remains provisional until the actual protocol schema keys are enumerated.
- The actual r3 schema uses `hashes`, not `artifacts`. Its data category requires processed ERE train/valid and FACT train/valid; checkpoint validation requires the existing `a4090_ctrl_accum1` triplet. For a temporary clean worktree, protocol v6 must be a physical in-tree copy because builder resolves the protocol root, while large source/checkpoint inputs may be read through scoped symlinks: they remain addressed by the same repository-relative evidence paths and are content-rehashed.
- Correction: checkpoint is intentionally outside `local_hash_categories`; local validation trusts only the rehashed returned remote-evidence snapshot for those remote-only weights. No local checkpoint directory exists, and none should be copied across machines for r4. Only ERE/FACT processed sources, protocol v6, and test data are required locally.
- Detached clean `53ce6f1` validation passes with 380 tests and 12 expected no-torch skips, plus clean ruff/smoke. The resulting immutable `p1-v6-20260828-r4` independently validates with protocol SHA-256 `09e7e392d807641bc0520f63c703299ee228a6a601fc85320afd73a95a85fc46`.
- The clean r4 CPU materializer again produces exactly 2,622 train + 291 internal-dev with no final-valid access. Its local plan SHA-256 is `4935bd2f72f7c83dd4b9e8694c06cbb9f06a50eb6ab037a8a5fcf2428f8f3444`; the launcher supports explicit `--preflight`, so r4 can be checked without changing code defaults before documentation is updated.
- All three r4 seed-13 no-execute launchers pass and print fully r4-scoped `/data/TJK/ekg` paths. The clean-generated registry/local gate, r4 bundle, and r4 preflight have been copied back to the ignored authoritative local areas; registry now selects r4 with global/A3 PASS.
- Active documentation has a bounded r3 drift in seven files plus the old 392 test count. Updating only Markdown/root instructions will not change the clean Python-tree local-gate hash. Because script defaults still name the historical r3 output paths, active A3 commands must explicitly supply both `--output ...r4/preflight` and `--preflight ...r4/preflight` rather than relying on defaults.
- Those seven authority files now name r4, clean-gate 380/12, and plan hash `4935...3444`; root instructions remain byte-identical. The P1 result explicitly records why r3 was superseded, preventing the portability failure from disappearing from the audit trail. Active A3 commands include both explicit r4 path arguments, so unchanged Python defaults cannot silently select r3.
- Two remaining status-index references were corrected, then a nine-file documentation-only commit `1d38dce` was pushed. No Python path changed after the r4 clean gate, so its tested-tree identity remains valid while the published authority now points to r4.
- Remote `1d38dce` plus the dual-hash r4 evidence archive validates P1 r4 successfully; the earlier r3 failure is therefore resolved without importing old Ch1 changes. Remote CPU materialization independently reproduces the exact local population and bit-identical plan SHA-256 `4935bd2f...f8f3444`, with final-valid explicitly untouched.
- Remote final HEAD is `132d69f`, clean and synchronized with origin. All three remote seed-13 launchers pass in no-execute mode with their exact r4 argv/cwd/outputs; an anchored process check finds no `/data/TJK/ekg/.venv/bin/python` process, and all four 4090s remained at 0% utilization. No A3 training has started.
- Final local assertions confirm HEAD equals origin, the index is empty, whitespace/root-instruction checks pass, registry selects r4, and both r4 hashes match. The remaining dirty paths are exactly the pre-existing Ch1/error-profile and untracked research/planning materials intentionally excluded from all three commits.

## Phase 16 A3.0 launch readiness (2026-08-28)

- The next scientific task is A3.0, not the new family-balancing method: run the three frozen baselines on train/internal-dev, produce official normalized predictions/scores, then freeze the primary anchor before any A3.2 result exists. Random baselines require matched seeds 13/17/42; final-valid remains sealed.
- The launcher executes one full train→inference→official-score pipeline synchronously in an immutable baseline/seed run directory. The nine planned run directories are independent, so concurrency across cards is structurally possible.
- User clarification supersedes the initial concurrency interpretation: permission is to accelerate one run with multiple cards, not to schedule independent experiments concurrently.
- Official single/joint wrap only the Hugging Face backbone inside `EventEncoder` with upstream `nn.DataParallel`; exposing multiple 4090s can distribute one run while preserving the planned global batch size, but actual speedup still requires measurement. The local pair trainer encodes one document/window batch at a time (leading batch dimension 1), so simple DataParallel would provide no meaningful acceleration; a real DDP rewrite would alter gradient accumulation/order and invalidate the frozen code identity. Recommended policy is official baseline = multi-card only after a throughput win, local pair = one single-card run, with no cross-seed concurrency.
- Source-level confirmation: official causal/joint collators concatenate independent token windows into tensor rows. `nn.DataParallel` receives only `input_ids` and `attention_mask`, scatters those rows, and gathers backbone outputs in original order; `event_spans` and cumulative `splits` remain outside the parallel wrapper and are applied only after gathering. Therefore the planned global batch 4 (single) or 8 (joint) is safe without LR/accumulation changes. Local pair's outer training unit is one document and its encoder receives a leading batch dimension of one, confirming that DataParallel cannot usefully split it.
- Remote readiness is otherwise strong: all nine immutable run directories are absent, `/data` has 32 TB free, torch 2.8.0+cu128/transformers 4.53.3 see four RTX 4090s, and all cards are idle at 17–18 MiB/0%. The sole hard pre-execution failure is the frozen model assumption: `/data/MODELS/roberta-base` (and `/data/MODELS`) does not exist.
- This is a phase-local, repairable NO-GO. The materializer already supports explicit `--model-path`, so an existing exact roberta-base cache can be transparently rebound with a new plan hash; no P1/code change is needed. Training must not start under the current plan because the launcher would correctly reject it.
- Independent guardrail audit found a second pre-result protocol defect: `primary_anchor` is chosen by causal mean from official single/joint, but the frozen subevent rule compares against `primary_anchor_mean`. Official single is causal-only, so if it wins the causal anchor, subevent has no scientifically meaningful anchor (the normalized empty subevent output would make the guardrail trivial). Before any baseline score exists, split the roles: causal primary anchor remains the causal-mean winner; subevent guardrail anchor is fixed to official joint, with the existing 1.0-point margin and matched seeds.
- Multi-GPU permission does not imply unconditional four-card use. Official single/joint are semantically safe on multiple cards, but their frozen global batches are only 4/8, so DataParallel communication may erase the speedup. After the model is available, run a short identical one-card versus four-card throughput smoke; use four cards only if it measurably accelerates the same run. Local pair remains one card. No independent baseline/seed jobs are scheduled concurrently.
- Final launch verdict is therefore NO-GO for the current r4 plan, but A3 itself remains PASS/feasible. Minimum repair is: freeze a concrete RoBERTa-base snapshot path/identity, correct the subevent guardrail reference before observing scores, rematerialize a new plan/trust root, then perform the bounded 1-vs-4-card throughput smoke. No full GPU baseline was started.

## Phase 17 path/backbone/release terminology correction (2026-08-28)

- `/data/TJK/ekg` is consistently the configured 4090 project root in `AGENTS.md`, `CLAUDE.md`, P1 remote evidence, and every Python/cwd/run-dir field in the A3 plan. The stray `/data/MODELS/roberta-base` is only the model artifact default: it originated in the upstream MAVEN-ERE joint source, while upstream causal used the network name `roberta-base`; the materializer incorrectly chose the upstream machine-specific joint path as the shared default instead of a server-local `/data/TJK/...` path.
- RoBERTa-base is not an accidental choice for the official baselines. The pinned official MAVEN-ERE checkout (EMNLP 2022, commit `ac81a971...`) explicitly instantiates `RobertaTokenizer` and a 768-dimensional RoBERTa/AutoModel encoder in both single-task and joint recipes. Replacing that backbone inside these two runs would stop being a faithful official baseline adaptation.
- This does not by itself justify using only RoBERTa-base for the thesis method. The correct separation is: (a) exact official-recipe reproduction on RoBERTa-base for public-method comparability; (b) same-backbone proposed method as the causal identification table; (c) a pre-registered modern same-scale backbone transfer/robustness table only if its tokenizer/hidden size/window adapter is implemented symmetrically for reproduction base and proposed method. Backbone upgrading cannot be counted as the family-balance contribution.
- Terminology needs correction: missing model artifact/path and an ambiguous pre-result guardrail are launch-readiness HOLD items, not research/task `NO-GO`. In the active v6 policy, `NO-GO` is reserved for protocol/evaluator impossibility or thesis-level failure arithmetic. P1 global and A3 entry remain PASS; only full A3 execution is temporarily held until the two small preregistration/materialization corrections are frozen.
- Primary-source verification confirms the benchmark identity: ACL Anthology `2022.emnlp-main.60` is the EMNLP 2022 MAVEN-ERE paper and its official repository is `THU-KEG/MAVEN-ERE`; the paper's relation-extraction result tables use RoBERTa_BASE. This supports retaining RoBERTa-base specifically for exact official reproduction, not treating it as the only acceptable 2026 encoder.
- A modern transfer candidate is now VERIFIED: the official `answerdotai/ModernBERT-base` model card identifies a 149M-parameter Apache-2.0 encoder with native 8,192-token context and Transformers support from 4.48.0. The 4090 environment already reports Transformers 4.53.3, so library version is compatible on paper. The model card recommends Flash Attention 2 for efficiency but does not make it mandatory; actual remote package/forward compatibility remains UNVERIFIED until SSH is available.
- DeBERTa-v3-base remains a credible older modernized encoder, but it does not directly solve the long-context motivation as cleanly as ModernBERT. For A3, ModernBERT-base is the better pre-registered transfer candidate because its scale remains close enough for a robustness table and its 8k native context directly tests whether family balancing transfers beyond RoBERTa windowing. It should not replace the official-recipe baseline axis.
- Current upstream model revisions were directly resolved from the official Hugging Face Git endpoints: `FacebookAI/roberta-base@e2da8e2f811d1448a5b465c236feacd80ffbac7b` and `answerdotai/ModernBERT-base@8949b909ec900327062f0ebf497f51aef5e6f0c8`. A reproducible server layout should use `/data/TJK/models/<model>/<revision>/`, not `/data/MODELS` and not an unpinned mutable `main` directory.
- The preregistration defect is generated by `scripts/freeze_v6_protocol.py`, not only present in the JSON output; a correct fix must update the generator, generated `data/protocols/v6/preregistration.json`, its registry digest, tests, P1 bundle, and A3 plan together. Editing only the prose or generated JSON would recreate the bug on the next freeze.
- The model-path default is generated by `scripts/prepare_a3_baselines.py`; the project already uses `/data/TJK/ekg` correctly for repository/Python/runs. The minimal path fix is to change only the model default to the pinned `/data/TJK/models/.../<revision>` path and rematerialize, without moving the repository or outputs.
- The local reproduction/proposed-method trainer already uses `AutoTokenizer`, `AutoModel`, and `encoder.config.hidden_size`, so ModernBERT-base does not require a hard-coded 768-dimensional rewrite there. Its default window budget is 512, however. The clean first transfer test should keep `max_length=512` for both reproduction base and family-balance method so the only changed factor is backbone; exploiting ModernBERT's 8k context is a separate context-length ablation, not part of the backbone comparison.
- `build_p1_bundle.py` hashes `preregistration.json` and controlled code into the trust root. Therefore the corrected preregistration generator/materializer necessarily creates a new P1 bundle identity and A3 plan hash, but it does not require repeating raw-data/evaluator research or the earlier checkpoint forward: those underlying evidence artifacts remain unchanged and are revalidated by hash.

## 2026-08-31 · 周四汇报与三日计划接管

- 用户意图不是只写一份汇报，而是把“论文总体结构、四章当前证据、未来三天可交付实验、文档治理、4090 调度”收敛成同一套执行计划；前三章是主线，Ch4 只做已成立系统证据与低成本扩展。
- `docs/HANDOFF.md`（2026-08-30）比根 planning scratch 更新：当前 P1 唯一可信根为 r11，A3 plan 为 r12；Ch1 两个机制周期均无效，Ch2 第二周期因逐位置阈值天花板 33.80 超过 33.17 主锚而重新获得明确机制机会，Ch3 在标签轴上不可区分，Ch4 图依赖正控已成立。
- `docs/reports/2026-09-03_阶段性报告.md` 的前半仍保留更早的“Ch1/Ch2/Ch3 正在训练”叙述，后半已写入 2026-08-30 负结果；同一文件内部存在时态、数值和下一步冲突，需整体收敛，不能只在末尾追加。
- 周四验收必须区分“已发生事实”和“预期进展”：报告正文只引用 `docs/results/` 的权威数字；未来三天结果使用 PASS / FAIL / 未完成三态，不预承诺正向分数。
- 目录整理优先做文档信息架构和活动/归档边界，不移动权威结果或大批历史文件，避免破坏现有链接与信任链。
- `docs/SPEC.md` 的学位验收仍要求每个方法章三种子超过主锚和另一强方法族且 paired CI 下界大于 0；截至 08-30，Ch1 已触发“两周期仍失败”的方法止损，Ch3 现有标签轴证据不足以满足该门，只有 Ch2 尚有一个由实测天花板支持的第二核心周期。
- active phase 契约与最新 handoff 存在身份漂移：`PHASE_A3_relation_balanced.md` 仍写 P1 r9 / 旧 preflight，而最新权威 handoff 写 r11 / r12；`TODO.md` 上半仍为 A3.0 早期状态、下半才是 08-30 收盘。目录治理必须同时解决“活动指令只留一个当前版本”的问题。
- D3/C4/E3 契约仍以严格串行 handoff 为准。当前 Ch1/Ch3/Ch4 的实测可作为研究进展汇报，但尚不能冒充对应正式 phase bundle 已验收；周四报告必须分别标注“科学证据状态”和“阶段/工程交付状态”。
- Ch2 第二周期的最小代码面已定位：`PairExample` 当前没有同句/跨句属性，trainer 只为每个 family 维护一个 offset；需要让 pair row 明确携带位置桶、让 controller 维护 3×2 个独立 offset，并在训练 loss 中按 row 只移动对应 NONE logit。推理仍保持原始 argmax，候选与 evaluator 不变。
- 可用的正确性测试应同时覆盖：同/跨句位置标签由 `sent_id` 决定；两个位置的最优 shift 可不同；训练侧 offset 映射不串桶；现有符号/闭环收敛测试继续成立。该实现涉及 `pairs.py`、`balance.py`、trainer，均属于 P1 受控代码面，长跑前必须重建 trust root。
- 只读远端审计的首个 ControlMaster 建连尝试未成功，但本地 `hold-4090.sh` 仍按 40 秒间隔继续运行，TCP 端口可达；远端命令尚未执行，GPU/进程状态仍未知。
- 远端审计最终确认：clean HEAD `3ec0464`；registry 选择 `p1-v6-20260830-r11`，protocol SHA-256=`22ddb933…e831a515`；A3 r12 plan SHA-256=`ba52708a…6f6df0b`；四张 4090 均 17–18 MiB、0%，没有 `/data/TJK/ekg/.venv/bin/python` 任务。根指令的 r9 已被实际远端状态与最新 handoff 双重证伪，需在新 bundle 生成后同步纠正。
- Ch2 位置化控制器已实现并通过 447 tests / 16 expected skips、ruff、CPU smoke 与 P1 local gate。代码提交 `91d32d8` 已推送；生产改动只涉及三个 P1 受控文件，测试明确覆盖同/跨句相反控制方向和桶映射。
- 用户重新排序了本轮价值：目录只做最小治理；核心交付是逐章公开方法/本地对手/当前方法指标、低分原因和文献技术到下一轮实验的映射。
- 远端已在 clean `91d32d8` 上构建 `p1-v6-20260831-r12`，global/A3 PASS，protocol SHA-256=`0bd33e87…58497`；A3 r13 preflight 为 2,622 train + 291 internal-dev、final-valid untouched，plan SHA-256=`b587b21d…1eda`。四张 4090 审计时空闲，尚未启动训练。
- ACL 一手主表给出的 MAVEN-ERE 背景量级：官方 RoBERTa/Joint coref MUC F1 81.4/82.1；Joint causal/subevent/temporal 为 31.5/27.5/56.0（论文 test）。后续 LLMERE 重报同数据集分类对手 ProtoERE causal/subevent/temporal=31.8/27.9/53.8，LLMERE Llama3-8B-base=36.0/28.2/54.7，coref 为四指标均值 90.9；这些只能作公开背景表，不能与本地 internal-dev 直接相减。
- TacoERE 在 MAVEN-ERE 论文 split 上 causal 34.1、subevent 30.6；其 cluster-aware compression 明确针对长距离与冗余。RepL4NLP 2025 的两阶段 retriever→cross-encoder 则直接针对 O(n²) 配对和无关系样本偏斜，并报告 MAVEN-ERE sampled subset 上最高 32.8；后二者与本项目跨句 2.6× 过发/precision .1998 的错误形态高度匹配。
- Ch1 方法检索支持从“再换 backbone/再加局部上下文”转向 event-aware度量和关系感知联合学习：within-document ECR 工作显式融合 event-alone linguistics features 与多种 event-pair similarity；MAVEN-ERE/LLMERE 的 joint/coreference-rationale 结果也说明跨任务结构值得测试。因现有两周期增益小于 seed sd，本周不再给 Ch1 排盲目长跑。
- MAVEN-FACT 一手论文确认 >80% 事件为事实类，公开 test macro-F1 为 BERT+CLS 46.1、RoBERTa+CLS 45.4、DMBERT 47.6、DMRoBERTa 47.1、GenEFD 45.1、GPT-4+CoT 42.8；论文还发现事件论元/关系能帮助 fine-tuned 模型。其 evidence 表中 DMRoBERTa supporting-evidence F1 45.4，支持把本项目的 evidence 轴作为主机制而非附属解释。
- A3 r13 2-epoch 4090 行为 smoke 完成：trainer macro .3178→.3328；六桶最终 offset
  [−.536,+.328]，12 条轨迹均有限，status complete、final-valid untouched。causal cross-sentence
  的最优 NONE shift 为 +.259/+.814（两轮均要求提高正例门槛），与跨句 2.6× 过发的独立诊断一致。
  该 trainer 入口不产生 official predictions，所以只放行 50-epoch seed-13，不能把 .3328 写进论文主表。
- 2026-08-31 用户新的操作约束高于旧 promotion 调度：单种子用于方案筛选；在所有待比方案的单种子均超 baseline/护栏且用户再次明确授权前，禁止任何多种子。GPU 并行只在不同方案/任务之间使用。
- r13 preflight 的 `local_pair` 命令仍是 baseline 默认 3 epoch，不是本轮 50-epoch
  `adaptive_workpoint` 方法流水线；不能误用 `run_a3_baseline.py --execute`。正式单种子应复用已通过
  smoke 的 trainer 参数，仅把 epochs 改为 50 并写入新的 immutable run-dir；训练完成后使用
  `score_a3_arm.py` 串行执行 native dump→冻结 candidate 归一化→official evaluator，candidate digest 为
  `15a3b1a5…dac10910`。
- 针对并行第二方案的一手搜索：RepL4NLP 2025 论文官方 ACL 页面确认方法是
  retriever→cross-encoder，直接解决 O(n²) 和 unrelated-pair 偏斜；论文检索片段还指出 k=5 是评估的候选设置。
  定向搜索没有找到作者官方代码仓库；TacoERE 的官方代码也未在本轮结果中出现。因此在启动 GPU1 前，
  必须先核论文 PDF 是否给出 code URL；若无，只实现项目内的最小 retriever 竖片，不重写整篇论文。
- PDF 一手核验确认两篇都**没有提供作者代码仓库**；TacoERE 只脚注 HuggingFace 库。Efficient DERE
  的可实现最小机制很明确：以 `<m>trigger</m>` 标记所在句做 bi-encoder 输入，点积做 related/
  unrelated 二分类，每个 event 取 top-5；Stage 2 用全部正例+检索出的 hard negatives 训 cross-encoder。
  论文 Table 4 在 ESC 上显示 k=5 优于 3/7/10；这不能当作 MAVEN-ERE 已调好的 k，但可作冻结的首个
  诊断点。论文 MAVEN-ERE 用 sampled subset，S-BERT+T5 的 non-negative F1 32.8，不可与当前 291-doc
  official 指标直接相减。
- TacoERE 完整方法需 K=3 句簇、生成式摘要预训练、事件链中介和 REINFORCE 联训，论文运行于
  2×RTX3090。在无官方代码情况下重写这套不是三日内高价值路线；只保留“句簇/上下文选择”作为
  retriever 通过后的后续可选机制。
- 代码库中无现成 relation retriever，但有足够的可复用基础：`load_maven_ere`、
  `gold_pair_labels(..., expand_event_relations=True)`、冻结 manifests、`encode_trigger_reps`。最小竖片应只针对
  **causal candidate retrieval**；subevent/temporal 继续保留全候选，否则 temporal 每个 mention 的稠密正例会让
  top-5 在结构上无法维持 50.63 护栏。实现前先用 gold causal 统计 oracle recall@5 和压缩率；
  若 oracle 本身不足，不写模型。
- gold oracle 已证明论文的 **k=5 不能直接照搬**：在本项目 official mention-expanded causal 口径上，
  internal-dev mention-level oracle recall@5 仅 .7832（候选压缩 84.7%）；即使先在 gold coreference cluster 级检索再
  展开 mentions，oracle 也只 .8032（压缩约 83.4%）。原因是 official Cartesian expansion 与高 causal out-degree：
  dev 有 224 个 mention heads / 128 个 cluster heads 拥有 >5 个正例 tail。下一步先扫结构上限的
  k={5,10,15,20}（不是模型调参），选择 oracle recall≥.95 且仍有实质压缩的最小 k。
- oracle grid 收口：mention-level k=10 仅 .9393，k=15 达 **.9810** 且仍压缩 **55.8%** 候选；
  cluster-level k=10 达 .9502/压缩 67.1%，但它需要推理时 gold/predicted coreference chain，会引入 Ch1 混淆。
  因此首个竖片冻结为**mention-level top-15**：不使用 gold cluster，只裁 causal 候选，subevent/temporal 不变。
- Ch3 的活动契约 `PHASE_D3_evidence_conditioned.md` 明确要求先取得 A3 immutable handoff；其输入、状态
  和后续消费者均绑定 A3 bundle。用户允许不同任务并行不改变这一有效性依赖，因此现在启动正式 D3
  会产生无法进入主表的结果。GPU2/3 暂时空闲是有意的；可以做 CPU 准备，但不能越过 A3 交接跑正式 Ch3。
- 2026-08-31 运行监测：GPU0 workpoint 完成 epoch 4，当前最佳 trainer macro=.3823（epoch 3）；
  GPU1 retriever epoch 0 已处理约 2,000/2,622 文档。两进程均存活、数值有限；这些都不是 official 主表指标。
- Stage-2 接线审计表明无需改变 official candidate population：若 Stage-1 通过，可只把未入 top-15 的
  causal rows 在训练时设为该 family 的 ignore、推理时强制 causal NONE；subevent/temporal 继续全量评分，
  最终仍输出完整候选结构给原 scorer。这样检索器是 causal admission gate，而不是偷换 evaluator 分母。
- Retriever epoch 0 实测 recall@15=.8455、cross-sentence=.7947、compression=.5580，低于预先冻结的
  .90/.85 门槛；分解后同句为 1,350/1,392=.9698，跨句为 2,705/3,404=.7947，损失几乎全部来自
  跨句排序而非 top-15 容量。按既定 3 epochs 继续，不能看到首轮低分后中途改 k、学习率或种子。
- r1 与论文的边界需准确表述：它采用文献的 bi-encoder/top-k 思路，但为最小接线复用了本项目
  `encode_trigger_reps` 的窗口内 trigger mean pooling；论文原式是把目标事件用 `<m>...</m>` 标记后编码
  所在句。故 r1 是“论文启发的竖片”而非忠实复现。若冻结 3 epochs 失败，下一单种子机制应改变
  event representation 为 marker-sentence，而不是调 k、重复 seed 或直接重写 TacoERE。
- Retriever epoch 1 为 recall@15=.8638、cross-sentence=.8231，虽较 epoch 0 上升，仍低于 .90/.85 门。
- 一手原文对 Stage 2 的最小要求已核：全部正例 + Stage-1 检出的 hard negatives 训练 pair classifier；
  推理只对检出的 pair 做关系分类。当前项目的 trigger mean + pair MLP 可承担 discriminative Stage 2，
  但必须在完整候选输出中把未检出的 causal pair 明确写为 NONE，不能从 scorer 输入中删除这些 pair。
- r1 最终 best epoch 2：overall recall@15=.8691、same=.9713、cross=.8273、compression=.5580；
  未过预设 .90/.85 门。进程已由成功 SSH 确认为 GONE，metadata status=complete、final-valid=false、
  confirmation_eligible=false，checkpoint 哈希集合逐项一致。按门停止，不接 Stage 2。
- marker-sentence r2 不能只靠当前 `EvidenceSpan` 重找 trigger：73,939 个 mentions 中 4,080 个所在句
  含多个同形 trigger，而 loader 的字符定位会取第一个；原始 JSONL 保留每个 mention 的 token offset，
  可无歧义插入 `<m>`/`</m>`。因此 r2 直接从冻结 input 的 `tokens + offset` 构造上下文，不改
  `EventNode` schema，也不改正在运行的 P1 受控 loader。
- r2 每篇最多 110 mentions（均值 25.38），marker sentence 编码需有界小批量，避免一次把全篇所有
  标记句堆进 GPU；这只是内存操作参数，不改变 top-15、数据、seed 或判定门。
- r2 实现保持单变量：新增 `representation=marker_sentence` 和 batch-size=16；tokenizer 注册 `<m>`/
  `</m>` special tokens，encoder resize 后以标记句的首 token 表示做既有 query/key 检索。原 r1
  `trigger_mean` 仍是默认值，旧命令语义未改变。
- 冻结 JSONL 的 73,939 个 event mentions 已全量对齐：ID 集合相同且每个上下文恰有一对 marker。
  本地门为 457 passed / 16 expected skips、ruff clean、`ekg-smoke` OK。
