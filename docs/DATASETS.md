# EKG v6 数据集与切分

> 数据文件不提交 Git。`data/raw/` 保存公开 release，`data/processed/` 保存项目口径输出，
> `data/fixtures/` 只放 CPU 测试样例。文件级来源与 SHA-256 见已跟踪的
> [`data/raw/DATA_PROVENANCE.md`](../data/raw/DATA_PROVENANCE.md)；v4 时期的数据资产快照见
> [`DATASET_SURVEY.md`](DATASET_SURVEY.md)，不得据此启动当前实验。

## v6 主干数据

| 章 | 数据集 | 任务 | WSL | 4090 | 项目状态 |
|---|---|---|---|---|---|
| Ch1 | MAVEN-ERE | 事件身份消解（gold mentions） | raw+processed | raw+processed | ✅ 主数据 |
| Ch1 辅助 | MAVEN-Arg | 局部论元语境 | raw+processed | raw+processed | ✅ 与 ERE 文档对齐 |
| Ch2 | MAVEN-ERE | temporal/causal/subevent | raw+processed | raw+processed | ✅ 主数据 |
| Ch3 | MAVEN-FACT | 5 类事实性 + evidence | raw+processed | raw+processed | ✅ train/valid；无公开 test |
| Ch4 | CGEP-MAVEN | 因果图后继事件预测 | 由 ERE 重建 | 由 ERE 重建 | ✅ 既有基线协议 |

MAVEN-ERE、MAVEN-Arg 和 MAVEN-FACT 的 train/valid doc-id 集合对齐，支持同一批文档上的
身份→结构→事实→传播实验。官方 test 标签隐藏，不得用于本地训练、调参或错误分析。

## 历史扩展数据（不在 v6 关键路径）

下列数据来自 v4/v5 的泛化或跨数据集计划。除非当前 phase 明确重新纳入，否则不能据此启动实验，
也不能把已有 raw/processed 文件当作 v6 待执行任务。

| 数据集 | 用途 | 当前真实状态 |
|---|---|---|
| DocEE | Ch1 长文档/中英泛化 | en 已 processed 并上传；zh/cross-domain 仅 WSL processed |
| RAMS | Ch1 文档级论元 | raw 已在 WSL/4090；**尚无项目预处理实现** |
| WikiEvents | Ch1 文档级论元 | raw 已在 WSL/4090；**尚无项目预处理实现** |
| ECB+ | Ch1 跨文档共指 | raw 已在 WSL/4090；**尚无项目预处理实现** |
| MATRES | Ch2 时序关系 | raw 已在 WSL/4090；**尚无项目预处理实现** |
| It-Happened / UDS-IH2 | Ch3 英文第二基准 | processed + manifest 已在 WSL/4090 |
| ModaFact | Ch3 意大利语 bonus | processed + manifest 已在 WSL/4090 |
| CLES | Ch1 中文跨文档泛化 | 尚未获取 |

“raw 已下载”不等于“可直接训练”。只有 `data/processed/<dataset>/manifest.json` 存在且相应 loader/
评测口径可用时，才可写成项目已预处理。

## 旧线与冻结数据（均不进入 v6 主表）

> 金融应用层（Phase G / SARGE）已移出主干，下列数据**不进入 v6 主表**。

| 数据集 | 当前定位 |
|---|---|
| CCKS-2021 FinCausal | 中文金融因果；仅保留历史 loader/数据兼容性，不是当前实验入口 |
| Astock、CMIN-CN、event_graph_zh | 已证死路（entity-mode 闭环）；**preparer 已于 2026-07-27 删除**，raw 数据仍在磁盘 |
| ICEWS14/18/05-15、FinDKG | 冻结 TKG 线兼容数据，不进入 v6 主表 |

## v6 切分硬约束

| 数据集 | 项目协议 |
|---|---|
| MAVEN-ERE | official train 2913 / valid 710 / test_unlabeled 857；本地评测用 valid |
| MAVEN-Arg | official train 2913 / valid 710 / test_unlabeled 857；与 ERE doc-id 对齐 |
| MAVEN-FACT | public train 2913 / valid 710；无本地 test |
| CGEP-MAVEN | 从 ERE train+valid 按 `succession/data/cgep.py` 重建；候选与查询规则以代码为准 |

历史兼容数据仍须保持原协议，但不得进入 v6 主表：

| 数据集 | 历史协议 |
|---|---|
| ESC | EventStoryLine topic 交叉验证；document split 只用于解释论文泄漏数字，不作主协议 |
| CCKS-2021 | 7000 labeled train；seed-42 本地 5600/700/700；官方 eval 1000 无标签 |
| ICEWS/FinDKG | 仅冻结旧线复现；保持 release split，不得为了好看重切 |

## 可复现处理

`scripts/preprocess_datasets.py` 默认只处理 v6 的 MAVEN-ERE、MAVEN-Arg、MAVEN-FACT。DocEE、
It-Happened、ModaFact 及旧金融/TKG preparer 仅为历史兼容，必须通过 `--only <dataset>` 显式选择。
脚本仍不支持 RAMS、WikiEvents、ECB+、MATRES；当前 phase 未重新纳入前不得补实现。

```bash
uv run python scripts/preprocess_datasets.py --help
```

## 许可

遵守各 release 的许可和引用要求。FinDKG 为 GPL-3.0；ModaFact 为 CC-BY-SA-4.0；RAMS 为
Apache-2.0；WikiEvents 为 MIT。仓库只提交 fixture、处理代码和溯源文档，不提交完整公开数据。
