# 统一评测协议表（论文第 2 章素材）

> 主表 ID **C-8**。本文回答一个问题：**第 3–6 章的每一个数字，是在哪批文档、用哪个评分器、
> 按哪条指标定义算出来的，以及怎么自己验一遍。**
> 每一格都能从 `runs/` 或 `docs/results/` 反查；下面每节末尾都给了**重算命令**。
> 数字本身不在这里，数字只在 [`results/`](results/README.md)。
>
> 冻结于 **2026-09-13**，仓库 commit `dfa4c5f`。本文列的 `src/` 与 `scripts/` 哈希是**该 commit 的**；
> `data/protocols/v6/` 与 `runs/` 下的哈希是**内容地址**，与仓库状态无关。

## 0. 口径三轴

A 类有效性要求三轴完全一致，跨臂、跨章、跨机器都一样：

| 轴 | 是什么 | 不一致的后果 |
|---|---|---|
| **manifest** | 哪些 `doc_id` 进哪个 split | 两个臂答的不是同一批题 |
| **候选全集** | 评分器眼里该文档有哪些 mention / 哪些对 | 分母不同，P/R 不可比 |
| **evaluator** | 打分的那份代码 | 同一份预测能打出不同的分 |

## 1. 数据源与 split（四章共用同一套 manifest 机制）

`data/protocols/v6/manifests/*.json`，schema `ekg.protocol_manifest.v1`，
由 `scripts/freeze_v6_protocol.py`（`234edb66…1c556`，commit `132d69f3`）生成，
每份都自带 `doc_ids` 全表、`source_sha256` 与 `source_records`。

| split | 文件 SHA-256 | doc_count | 源文件 | 源 SHA-256 | 划分来源 |
|---|---|---:|---|---|---|
| `maven_ere_train` | `47d19cc9a17e38259bfbb7f9206c675c7362f41252d23f414ea6cfd46015ca68` | 2,622 | `data/processed/maven_ere/train.jsonl`（2,913 条） | `6a5519fe…638b7` | 冻结 internal-dev 的补集 |
| `maven_ere_internal-dev` | `f5457b302be57663f8e618d977c492909c3210682804cb486bd67ccc8c171b5f` | 291 | 同上 | 同上 | 从公开 train 冻结抽出 |
| `maven_ere_final-valid` | `af979c11d07976e08de884a34203da5eb4b9f1af05d5d8ffde04c26861745480` | 710 | `data/processed/maven_ere/valid.jsonl` | `6faea0e4…c6153` | MAVEN-ERE 公开 valid 全量 |
| `maven_fact_train` | `e9a939440eb0dbea76e6ce56d0b06b5a1009118eefdfcb93ae85f4a38e8c609a` | 2,622 | `data/processed/maven_fact/train.jsonl`（2,913 条） | `190522b4…6bab7` | 同 ERE 的 doc_id 划分 |
| `maven_fact_internal-dev` | `8b41a18a37a60fb709af4559633a9ad6acf0a9f375076ab66971160425d2b258` | 291 | 同上 | 同上 | 同 ERE 的 doc_id 划分 |
| `maven_fact_final-valid` | `d39e83ddc0aaaff40f530528e78867d2e5a5683d550885c3958aeb2eceb776d5` | 710 | `data/processed/maven_fact/valid.jsonl` | `396fcf07…c7cff` | MAVEN-FACT 公开 valid 全量 |

⚠️ **MAVEN-ERE 的官方 test 拿不到**：CodaLab 提交通道已关闭（已核，`results/PHASE_R1.md`），
所以公开 valid 就是我们的 final-valid。这不是我们发明的做法——**MAQInstruct（2025）与
Ch6 的基座论文 SeDGPL（Findings of EMNLP 2024 §5.1）都拿 MAVEN-ERE 的 valid 当 test**
（SeDGPL 原文：*"we use the original development set as our test set"*）。

```bash
sha256sum data/protocols/v6/manifests/*.json          # 核上表第 2 列
python3 -c "import json;d=json.load(open('data/protocols/v6/manifests/maven_ere_train.json'));print(d['doc_count'],len(set(d['doc_ids'])),d['source_sha256'])"
```

## 2. 四章各自的协议

### 2.1 第 3 章 · 事件事实性检测（D4，MAVEN-FACT）

| 项 | 值 | 反查 |
|---|---|---|
| 评测单元 | **文档**；5 折 OOF，**全部 2,913 篇公开 train 各恰好一次** | `runs/stages/R1/r1-v61-20260904/factuality_cv/factuality_cv.json`（`3a724cf7…2c5c4`） |
| 折轮转 | `evaluation=i`／`selection_dev=(i+1) mod 5`／`train=其余`，seed **260904**，单 seed **13** | 同上 `config` |
| mention 计数 | **73,939**＝CT+ 69,782 ／ CT− 1,492 ／ PS+ 2,262 ／ PS− 285 ／ Uu 118 | 同上 `source.support` |
| 主指标 | **五类 macro-F1**，在**汇合后的 OOF 预测**上算一次（不是各折平均） | 同上 `config.primary_metric` |
| evaluator | `src/ekg/factuality/metrics.py::factuality_report`，`f09d8d318305b97f62ef22e12e4915c8eb7075df432d16d05212cc0c782fd998` | 本仓库 commit `dfa4c5f` |
| 缺失处理 | 有 gold 无预测、或预测到未知 mention，**直接抛异常**，不补默认值 | 同上函数体 |
| 配对统计 | 同一批 OOF 文档上的 document-cluster bootstrap | `factuality_cv.json` `config.paired_inference` |
| final-valid | **未打开** | `factuality_cv.json` `config.final_valid_accessed = false` |
| 本轮状态 | **failed**（typed-cue 家族已关闭） | `results/PHASE_D.md` |

### 2.2 第 4 章 · 事件关系抽取（A4，MAVEN-ERE）

| 项 | 值 | 反查 |
|---|---|---|
| 训练 / 评测 | train 2,622 篇 → internal-dev **291 篇** | §1 的两份 manifest |
| **候选全集** | **291 篇 / 7,195 event mentions / 1,719 TIMEX / 234,870 个有序对**，digest **`15a3b1a548625624642130190b39411e6346866ff8594c2af2020cfbdac10910`** | 本地可重算，命令见下 |
| evaluator | **组织方官方** `data/protocols/v6/tools/maven_ere_evaluate.py`，`32919e86d98c6fafae6aa9505579e2c356caee12c32c1a8c719910acec359598` | 内容地址，与 commit 无关 |
| 主指标 | causal / subevent / temporal 三族各自的 **P / R / F1**（官方口径：金标簇级关系展开到跨簇的每个 mention 对） | 官方 evaluate.py |
| 已知口径坑 | temporal 的 R 需要 TIMEX 头；不带 TIMEX 的训练/推理口径必须**成对**，否则 temporal 一列不可用 | `ENGINEERING_NOTES.md` |
| final-valid | **封存**，A4 只读 train 与 internal-dev | A4 preflight `protocol.json` 的 `final_valid_ledger` |
| 本轮状态 | A4.1 **PASS**（protocol `321309ac…d65451`，`code_files=7`） | `results/PHASE_A.md` |

```bash
uv run python - <<'PY'
import json
from pathlib import Path
from ekg.relations.maven_ere_official import candidate_population_digest
ids = set(json.loads(Path("data/protocols/v6/manifests/maven_ere_internal-dev.json").read_text())["doc_ids"])
gold = {r["id"]: r for r in map(json.loads, open("data/processed/maven_ere/train.jsonl")) if r["id"] in ids}
print(candidate_population_digest(gold))          # 期望 15a3b1a5… 与 291/7195/1719/234870
PY
```

### 2.3 第 5 章 · 事件身份消解（C5，MAVEN-ERE 文档内共指）

| 项 | 值 | 反查 |
|---|---|---|
| 训练 / 评测 | 与第 4 章**同一份** train 2,622 / internal-dev 291 | §1 |
| 候选全集 | 与第 4 章**同一个** digest `15a3b1a5…dac10910`（同一批 mention） | 同 §2.2 命令 |
| evaluator | **同一份官方** `maven_ere_evaluate.py` `32919e86…59598`，一次同时出四个共指指标 | 内容地址 |
| 主指标 | **MUC / B³ / CEAFe / BLANC**；主锚取 MUC | `results/PHASE_C.md` |
| final-valid | **封存**，C5 只读 train 与 internal-dev | C5 preflight 的 `final_valid_ledger` |
| 本轮状态 | C5.0 + 入口脚本齐备；C5.1 preflight 只差完整 mention-local 论元预测 | `results/PHASE_C.md` |

**第 4 / 5 章共用评分器不是省事，是 A 类要求**：两个 phase 的数字要能放进同一张协议表，
就必须由同一份代码、在同一个候选全集上打出来。

### 2.4 第 6 章 · 图谱构建与下游事件预测（E3，本地重建 CGEP-MAVEN）

| 项 | 值 | 反查 |
|---|---|---|
| 评测单元 | **冻结的 1,908 个实例**（437 篇有实例 / 761 个 ECG / 候选池 6,892 节点，分布在 607 篇 / 每题 512 候选） | `runs/stages/E3/e3-v61-20260917/manifest.json` |
| `queries.jsonl` | `f75e7e87272d718d68cb408163314519e906c50e90b3ba3a829a241a6baa11e6` | 同上 `unit.sha256` |
| ⚠️ 重新冻结 | 旧 `e3-v61-20260913`（`e92629bd…5aecf`）有 **68 个 `instance_id` 撞号**（`cgep.py` 的 id 用了每个 ECG 各自的节点下标），2026-09-17 修复并重新冻结。**逐行零差异**、`candidate_id_digest` 与源 sha256 均不变 ⇒ 与 `.1802/.1583` 并表的能力未丢 | `results/PHASE_E.md` |
| query-ID / candidate-ID digest | `3b700acc…15f6d` / `93915ae3…f27ee`（candidate 与旧 unit **相同**） | 同上 |
| 生成参数 | seed **209**（SeDGPL 的）· `min_nodes=4` · 含 subevent · 512 候选 | 同上 `generator.params` |
| 源 | `data/processed/maven_ere/valid.jsonl` `6faea0e4…c6153`（即 final-valid） | 同上 `source` |
| 主指标 | **MRR 与 Hit@1/3/10/20/50**，两种并列口径：`mrr`（SeDGPL 的，平局判给金标）与 `mrr_strict`（平局全算错） | `src/ekg/succession/predictor.py::evaluate` |
| evaluator | `src/ekg/succession/predictor.py` `43afe12cb366939c2b7a3babea40158caad8e426eea818b01d0e47617d58b514` + `src/ekg/succession/metrics.py` `bdba2614edf8bf5491776784f5465c557798bc47b95bd65a6e60273597e347fb` | commit `dfa4c5f` |
| 无法打分的实例 | 计为最差名次并记入 `n_unscorable`，**永不从分母里删** | 同上函数 docstring |
| 边序 | 主表**一律 canonical 序**；source 序只用于锚定已发表基线 | `results/PHASE_E.md`（纯重新序列化能造出 p=.02 的假效应） |
| 口径声明 | **本地重建协议**；SeDGPL 的 `MAVENSubWoRe.npy` 从未发布，其 CGEP-MAVEN 数字**不可同表** | `manifest.json` 的 `protocol` 字段 |
| **上游身份** | `gold` = MAVEN 发布标注；`predicted` = **v5 判别式抽取器在 valid 上的产物**（裁决 ② 取 (乙)，2026-09-17），**不是 C5/A4/D4**——那三章跑在 train 的切片上，与本 unit 文档集交集实测为 0。**表头必须写明** | `runs/stages/E3/e3-v61-20260917/upstream_registry.json` |
| final-valid | 建在公开 valid 上，**只用来定义题目**，不训练、不选模 | `manifest.json` 的 `final_valid_ledger` |

```bash
uv run python scripts/freeze_e3_evaluation_unit.py --verify runs/stages/E3/e3-v61-20260917
# 从源数据重建并比三件：源 sha256 / 盘上 queries.jsonl / 重建结果。期望 PASS
```

## 3. final-valid 封存台账

**A 类红线：final-valid 封存且不用于选模。** 以下是每一次访问的如实记录。

| 章 | 访问了吗 | 访问了什么 | 是否用于选模 |
|---|---|---|---|
| 第 3 章（D4） | **否** | — | — |
| 第 4 章（A4） | **否** | — | — |
| 第 5 章（C5） | **否** | — | — |
| 第 6 章（E3） | **是** | 公开 valid 的 mention、causal/subevent 金标边与文档文本，用来**定义 1,908 道题** | **否**：消费者在预注册训练图上只训一次，全部 arm 复用同一 checkpoint |
| R1 身份审计 | **是** | 公开 valid 的结构性 ID/offset/type/role 字段 | **否**：未算任何关系或事实性指标 | 

第 6 章那一次不是新开的口子：`results/PHASE_E.md` 2026-08-30 的图依赖正控就在这批文档上
（`historical_final_access_disclosed=true`），且那次是冻结权重 + 固定三臂。

## 4. 信任根与契约绑定

| 项 | 值 |
|---|---|
| P1 信任根 | `runs/stages/P1/p1-v6-20260904-r15`，`protocol.json` SHA-256 `1e31a9acef39261f776f7ed4069fd73f4531e8d12b55779bfc0fbd74c67f9655` |
| R1 契约 | `runs/stages/R1/r1-v61-20260904/protocol.json`，`phase_contracts` 绑定三章 |
| 第 3 章契约 | `docs/phases/PHASE_D4_typed_cue_factuality.md` `01e1ba2f…c49b1` |
| 第 4 章契约 | `docs/phases/PHASE_A4_pair_evidence.md` `79281df7…25e529` |
| 第 5 章契约 | `docs/phases/PHASE_C5_argument_uncertainty.md` `b504f29c…32d1f` |
| 第 6 章契约 | `docs/phases/PHASE_E3_graph_application.md`（E3 不在 R1 的三章契约内，它不是方法章） |
| 编码器 | 内容寻址 `roberta-base`，`71be7419a60dcce0fc276654c8f9213b41f8def71a0c3465d7fed2352c961ea9`（4090 线）；5090 的**全公开源**复现件是 `2c7ff1f1…49736`，**两条线不混表、不相减** |

```bash
uv run python scripts/audit_r1_consistency.py \
  --output runs/stages/R1/r1-v61-20260904/audit/cross_artifact_audit.json   # 期望 PASS: 36 requirements mapped
```

## 5. 这张表怎么维护

- 新增一章或换一次 split，**先改这里再跑实验**；表里出现「待补」就说明那一格还没资格进论文。
- `src/` 下的 evaluator 哈希会随 commit 变，所以每次冻结都要写明 commit；
  `data/protocols/v6/` 与 `runs/` 下的哈希是内容地址，**不随 commit 变，也不该变**。
- 本文只记协议，不记数字。数字降了就在 `results/` 里如实写，不在这里改口径。
