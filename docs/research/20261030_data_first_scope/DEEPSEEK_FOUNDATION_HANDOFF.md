# CDECR独立项目奠基：DeepSeek任务委托与验收说明

版本1.0，2026-10-30。委托方：作者；实施方：DeepSeek；复审方：作者后续指定的Codex。
本文件可单独交给实施方阅读。它规定要完成的建设任务，**不表示任何服务器已经扫描、
环境已经安装或新项目已经建立**。作者已指定扫描也由DeepSeek完成。

## 1. 项目身份与本轮交付范围

项目名采用`cdecr`：**Cross-Document Event Coreference Resolution，跨文档事件共指消解**。
课题是事件图谱构建中的事件身份归并技术：给定多文档的事件提及及文本，输出指向
同一事件的提及分区。它不承担本轮自动事件检测、关系抽取、事件预测或完整图谱平台。
不加`thesis`后缀；代码、配置、测试、运行名和目录不按`ch3`、`chapter4`等章号命名。

| 位置 | 新项目根目录 | 权限与职责 |
|---|---|---|
| 本地Ubuntu/WSL2 | `~/myProjects/masterProjects/cdecr` | 主开发、Git管理、CPU测试与数据检查；不跑GPU训练或GPU推理 |
| SSH别名`gpu-4090` | `/data/TJK/cdecr` | 独立环境与数据，可运行经授权的GPU任务；**没有管理员权限** |
| SSH别名`gpu-5090` | `/mnt/aidata/tongjiakai/cdecr` | 独立环境与数据；作者有管理员权限，不把它当默认系统重装授权 |

本轮完成：只读扫描、独立建仓、研究资料清理移交、统一Python环境、三端同机制数据
部署、最小基础工具和验收证据。可以实现数据校验、环境探针、统一评分自检等必要
基础代码；**不实现三项自有研究方法，不训练模型、不生成LLM辅助语料、不复现模型
成绩，不开展参数搜索**。公共预训练模型全量权重下载不作为本轮必需项。

旧项目仅是一次性、只读的移交来源：
`/home/tjk/myProjects/masterProjects/ekg`，本地研究来源基准commit为
`6d0cb790b5b2fac535a6d8cb390692b40da4761b`。后续执行时记录实际移交版本及文件hash。
新项目建成后运行、安装、测试和数据读取均不得依赖旧项目的存在。
本委托中的最新名称、统一环境、物理数据副本要求，优先于来源材料中的旧建议。

## 2. 作者明确的统一原则

1. **三端一份环境定义**：同一`.python-version`、`pyproject.toml`、`uv.lock`、依赖集合
   和安装入口；不建立local/4090/5090三份依赖配置，不用机器专属requirements修补主环境。
2. 三端各自新建`.venv`，不复制虚拟环境目录，不指向旧环境，不使用
   `--system-site-packages`。统一是软件定义相同，不是三台机器共享一个可写venv目录。
3. **三端一份数据机制**：同一个原件manifest、相同相对布局、相同reader、过滤/划分
   和校验入口；不写三套loader，不在不同机器重新抽split。
4. 本地改代码后，将同一Git提交同步到任一GPU服务器，直接运行同一代码与配置。
   机器配置仅容纳SSH别名、部署根目录、设备选择和硬件事实，不改变数据/模型/评价参数。
5. 主环境优先使用相同Python补丁版本、相同uv版本、相同包版本及Torch构建。三端若
   都为Linux x86_64，优先统一CUDA版Torch wheel；**本地不使用GPU不要求另装CPU版Torch**。
   本地GPU可用性不是验收要求，实际GPU操作仅在服务器短诊断中执行。
6. OS内核、宿主驱动、glibc、物理GPU可不同，须记录；不能因此声称Python依赖已完全
   相同，也不必为统一Python环境升级系统驱动。确有平台不兼容时先出具证据和共同
   解决方案，不能静默维护三套依赖后宣布完成。

## 3. 按功能独立、按接口组合

一个独立仓库，各项方法可以单独开发、训练、调试和评价，再组合成完整pipeline。
不建三个研究仓库，不写一个包揽所有阶段的大脚本。建议Python包名`cdecr`：

```text
cdecr/
  README.md
  AGENTS.md
  CLAUDE.md
  pyproject.toml
  uv.lock
  .python-version
  .gitignore
  docs/
    SPEC.md
    PROTOCOL.md
    BASELINES.md
    ENVIRONMENT.md
    DATA.md
    DEVELOPMENT.md
    HANDOFF.md
    provenance/
    results/
  configs/
    research.yaml
    deployment.example.yaml
  data/
    manifests/
    raw/{ecb,gvc,wec}/
  src/cdecr/
    data/
    semantic_assistance/
    retrieval/
    pairwise/
    clustering/
    evaluation/
    pipeline/
  scripts/
  tests/
  external/
  artifacts/
```

这是职责划分，不要求现在填充所有目录或写空壳模型。只建立本轮有实际功能的基础
组件，其余边界写进SPEC。需要第三方实现时直接复用，记录revision和透明补丁。

接口应先规定：

| 功能 | 输入→输出 | 独立性要求 |
|---|---|---|
| 数据 | 原件→文本/提及、训练/评价标签分离的数据视图 | reader/ID/坐标只有一套；测试gold不进入特征或提示 |
| 语义辅助 | 许可文本＋提及→带来源的语义辅助缓存 | 缓存绑定数据、mention、teacher和prompt身份，不能把生成内容当gold |
| 检索 | 提及/可用表示→去重候选事件对 | 可单独运行；固定后续判别/归并做归因 |
| 事件对判别 | 冻结候选及文本→pair分数 | 不要求重新训练/重跑检索，输入候选有hash |
| 簇归并 | seed候选、冻结评分函数/分数→覆盖全部提及的合法分区 | 必要的额外pair查询共用权限/预算，未知边不当负例 |
| 统一评价 | 同人口gold＋预测→标准指标及诊断 | 全部模块与消融共用；指标定义不随模块变化 |
| 组合运行 | 显式选择各模块版本→完整身份分区 | 支持缓存输入与逐模块替换，不依赖可变全局状态 |

运行产物以功能名组织，如`retrieval/gvc/...`、`pairwise/wec/...`。局部诊断用于解释，
完整系统CoNLL F1用于最终研究比较；不能把独立运行理解为各章另用一套数据或评价。

## 4. 执行顺序与检查点

1. 阅读本委托，核对目标路径是否已存在、有无他人文件；不得覆盖非空未知目录。
2. **先扫描三端，再选统一环境版本**。记录安装前报告及旧项目关键文件身份。
3. 提交统一环境决策和精简新SPEC，初始化独立Git历史；完成白名单资料与原数据复制。
4. 本地验证统一锁文件与CPU基础功能；以新项目Git提交/新仓库bundle部署到两服务器，
   从同一锁文件分别创建新环境，校验三端实际包清单。
5. 运行数据一致性、独立性、官方评分器自检；服务器分别运行短CUDA诊断。
6. 归档命令、日志、差异及提交；提供逐项验收报告，等待作者交Codex复审。

安装前必须有可审阅的版本选择、准确命令、工作目录和预期输出。正常项目级建设可
在本委托内推进；遇到驱动/权限/共享系统改动等超范围事项，记录具体缺口与所需动作，
不得扩大范围或以跳过验证宣称完成。扫描失败不等于服务器不存在，SSH中断不等于
安装进程已经停止；重连核实后再重试，避免重复安装/重复后台任务。

## 5. 三端扫描要求（由DeepSeek执行）

先只读扫描，输出带UTC时间、host别名、命令、退出码的报告。无工具时写明缺失，
不为完成扫描先安装系统软件。扫描日志不要包含密码、token、SSH私钥、代理凭据，
不整段导出`env`、pip认证配置或SSH配置。

| 类别 | 必须核实的事实 |
|---|---|
| 主机和权限 | `hostname`、`whoami`、`id`、`uname`、OS发行版/架构；目标父目录权限；区分SSH别名与实际GPU型号 |
| CPU/内存 | CPU架构/核数、可用内存、swap；不要用历史GPU文档当当前资源事实 |
| 磁盘 | 目标卷可用空间、inode、挂载/文件系统及写权限；估算venv、wheel下载、原数据和缓存空间 |
| GPU/驱动 | `nvidia-smi`及逐卡索引、UUID、型号、显存、驱动、占用；局部失败也保留退出码与可读结果 |
| CUDA | 区分驱动支持的CUDA上限、可选`nvcc`工具链与Torch自带运行时；未安装nvcc不自动判Torch不可用 |
| 工具 | Git、SSH、scp/rsync、Perl、uv、Python路径与版本；非交互PATH可能不同，记录准确可执行路径 |
| 旧环境经验 | 若存在，读取两个旧ekg路径的pyproject/lock及`.venv/bin/python`的版本/选定包metadata；不激活、不改包、不复制环境 |
| 环境污染因素 | 检查当前`VIRTUAL_ENV`、`UV_PROJECT_ENVIRONMENT`、`PYTHONPATH`、`LD_LIBRARY_PATH`、`LD_PRELOAD`等是否会带入旧项目，仅记录必要脱敏内容 |
| 网络与缓存 | 对包索引、PyTorch官方wheel源、HF及候选镜像作带超时的连通性检查；查询现有可复用下载缓存的身份/权限，不搬旧checkpoint |

4090必须全程使用用户态安装，不运行sudo。5090优先用户态；必要系统依赖要列明
包名和影响，管理员权限不用于默认升级驱动、修改共享CUDA、全局Python或他人环境。
旧文档提过的坏卡、NVML shim、镜像可达性仅是排查线索，必须重新核实；不默认复制shim。

扫描与安装前后对照至少包含：旧ekg的pyproject/lock哈希（若存在）、选定包metadata、
新目录之外计划修改的路径清单。禁止扫描旧实验预测/旧final-valid来为新研究选方案。

## 6. 统一Python环境建设

- 使用uv在用户态管理Python及项目venv。扫描后选择一个三端均可用的Python minor及
  补丁版本并写入`.python-version`；不要让三台机器各自选择“系统默认Python”。
- 新建精简`pyproject.toml`和**一份**`uv.lock`。三端安装同一依赖集合，开发工具也统一。
  主环境依赖应覆盖CPU数据/评价以及后续Torch、Transformers的基本开发条件；只加
  当前实际需要的包，不搬旧项目的RL、GNN、vLLM、音视频或所有历史baseline依赖。
- 选定Torch构建必须同时适配扫描得到的两台GPU/驱动。旧项目曾用Torch 2.8.0+cu128，
  这仅是已验证历史线索，不是本次指定版本；禁止不经扫描直接升级或照抄旧lock。
- 主环境须支持拟用任务encoder与Qwen3架构的配置/tokenizer接口。配置/tokenizer的小
  文件可以从固定revision获取并校验，不下载全量模型跑推理验证本轮环境。
- 三端统一安装入口，例如在各自项目根运行`uv sync --locked`；实际命令由统一依赖
  设计确定并写入ENVIRONMENT.md。uv版本、extras/groups及index选择必须一致、可复查。
  安装后运行优先用新项目`.venv/bin/python`，避免隐式再次同步或激活错环境。
- 核对安装目标确为新根`.venv`，不是旧项目或当前激活的venv。新环境依赖均由lock
  管理；不得用未记录的逐机`pip install`让验收暂时通过。
- 遇到网络差异可使用经校验的wheel缓存/下载镜像，源、版本及制品hash可追溯；不能
  因网络不同就更换软件版本。不要传输整个venv，Python环境必须在每台机器独立重建。
- 不修改全局shell初始化文件来自动激活项目；项目级缓存使用新根或中立公共缓存，
  不指向`ekg/.venv`、`ekg/runs`、`ekg/data`或其模型缓存。

旧项目曾因同步时遗漏extras卸掉GPU包，原因是环境与声明不一致。新项目应使用
完整、统一且受锁管理的声明；**不能把“旧环境禁止随便sync”变成新项目不使用锁文件**。
参考[uv锁定/同步说明](https://docs.astral.sh/uv/concepts/projects/sync/)及
[PyTorch官方构建表](https://pytorch.org/get-started/previous-versions/)，安装时再次核实。

## 7. 只移交白名单资料，不复制旧工程

以下源路径均相对旧ekg根。只有源路径用于溯源，不构成新项目运行依赖。

| 允许来源 | 新项目中应形成的内容 | 清理要求 |
|---|---|---|
| `docs/research/20261030_data_first_scope/THESIS_FRAMEWORK.md`、`READINESS_AUDIT.md` | 新SPEC与研究范围/待办 | 提取CDCR三层问题；删除旧队列、阶段名、旧主任务及“新规范已完成”的假设 |
| 同目录`METRIC_SPEC.md` | 新`docs/PROTOCOL.md` | 保留标准指标/输入/单例/GVC0/评分器身份；改为新项目本地链接，不带旧R编号作运行前提 |
| 同目录`EXTERNAL_READINESS.md` | 新`docs/BASELINES.md` | 保留论文来源、适配和真实发布状态；不把缺代码当文献收录障碍，不冒充已复现 |
| R130 `canonical_full_metrics.json`、`nine_full_tables.json`、`source_registry.json`、`extraction_receipts.json`、`source_coverage.json`、`metric_definition_sources.json` | `docs/results/`中的唯一已发表数字权威及可生成的九表、论文来源与缺失/异常说明 | 原数/变体/表号/页码保真，P/R顺序保真；仅迁当前选中记录，不引入未用语种/其他列的附注数字；缺报不补造 |
| R127 `dataset_inventory.json`、`ecb_audit.json`、`gvc_audit.json`、`wec_audit.json` | 新原件manifest、公开split/过滤依据及预期人口 | 改成新根相对路径；旧schema标签只留在provenance，不作为新包依赖 |
| R127 `repository_pins.json`、R128 `source_identities.json`及`review_decision.json`中的相关来源字段 | 第三方来源/固定revision及适配说明 | 只摘必要条目，不整包搬旧runs，也不抄旧任务状态 |
| R131 `gvc_zero_bucket_audit.json`、`source_receipts.json` | GVC语义审查及LEA来源记录 | 保留原生人口和固定非0投影的区别，不迁入“0是共享真实事件”的旧解释 |
| `docs/results/PHASE_R1.md`的§25.153—§25.154 | 必要原分脚注、当前审查事实核对 | 不整体复制大历史结果页；由上面JSON重建当前文献表，审查正文仅提取现行事实 |
| 旧`pyproject.toml`及`docs/GPU_RUNBOOK.md` | 环境建设经验来源 | 只读参考；不迁旧依赖全集、默认命令、权限表或历史硬件事实为新配置 |

R127/R128/R130/R131完整源目录分别为：

```text
runs/stages/R1/r1-v127-data-first-scope-20261030/
runs/stages/R1/r1-v128-external-readiness-20261030/
runs/stages/R1/r1-v130-full-metric-preparation-20261030/
runs/stages/R1/r1-v131-comprehensive-readiness-20261030/
```

**禁止整体复制**旧`.git`、`.venv`、`src/ekg`、`tests`、`runs`、checkpoints、日志、
旧SPEC/constitution、根AGENTS/CLAUDE/HANDOFF、历史任务表或`.agents`技能全集。
新AGENTS/CLAUDE自行精简编写且内容一致，只承载当前范围、数据有效性、资源边界、
入口和验收规则；不带旧多任务/预测要求、旧power数值及历史失败机制。

为每项实际移交记录源repo commit、源相对路径、内容hash、目标相对路径、复制/清理
方式与理由。外部代码保留许可证/来源和修改记录；无声明的来源不擅自改成MIT。
新规范允许将原项目名写在`docs/provenance/`中作历史溯源；运行配置不得引用旧根。

## 8. 原数据复制与三端统一机制

旧原件目录：`data/raw/research/cdcr-20261030/`。使用实际物理副本复制到新根
`data/raw/`，保留`ecb/`、`gvc/`、`wec/`和原文件名；不移动/删除旧原件，不使用回指
旧目录的软链接或硬链接。Git只提交清单、reader与校验机制，不提交大原数据。

新原件manifest至少含：dataset、相对路径、bytes、SHA-256、来源URL/revision/blob/LFS
身份、split角色、过滤依据。三端使用**同一份manifest文件及其hash**；host报告里的
绝对路径可不同，但不为每台机器维护一个原件manifest。

统一入口须支持`verify-data`与`audit-data`（最终CLI名可调整，文档/测试同步）：
前者逐文件完整hash，后者验证划分人口、ID/跨度/重复与过滤，输出稳定、可比较的
JSON；host和时间放外层元数据，不混入决定人口的统计结果。

### 必须保持的研究口径

- ECB+遵循发布句子过滤与公开原划分；plus句号偏移、CSV类型/空白等坐标映射有依据。
- GVC采用Bugert等已发表公开incident划分，不能改称创建者唯一官方划分；排除DCT、
  NEWLINE/空token时保持坐标映射。原标签0是泛指/未解决链接桶，不是真实共享事件。
  主native人口保持原件，所有方法将来在同批预测上另做固定非0提及投影评分；不在
  本轮擅改原件、删除0、将其单例化或把标签作为推理输入。
- WEC-Eng使用下表命名train及人工验证dev/test，禁止HF自动合并视图替代原split。
- 三语料分别训练/评价，三章共用同一人口。旧MAVEN成绩/权重不成为新CDCR结果。
- 主指标CoNLL F1为MUC/B³/CEAFₑ各自F1的均值；分项P/R/F1及LEA另报，候选/pair/
  聚类诊断不替代主指标。文献原条件成绩与本项目同协议控制表分开命名。

下表是迁入目标`data/raw/`相对路径及已核原件身份；实施时仍需检查来源存在并重算。

| 新根下相对路径 | bytes | SHA-256 |
|---|---:|---|
| `data/raw/ecb/ECB.zip` | 4470858 | `fe6ac2d76d8f7015f773ccc969927d7f3c33b331ed643b71efe31f28373eca90` |
| `data/raw/ecb/selected_sentences.csv` | 23008 | `afee49e0f5fe5084eec690e934aaade842d5eeff7a5704a36f59e7a49505f434` |
| `data/raw/gvc/gold.conll` | 9486746 | `a90cbc3f3810d5bd8aebcc4d3f3a0aa9785089325b717790d8290715515b0c3d` |
| `data/raw/gvc/train.csv` | 1760 | `2fda6c25d13535c3811320e30f6dcd5d8452d74464d154a4e09c6ac7ce8662b8` |
| `data/raw/gvc/dev.csv` | 360 | `e0b8e6001b06ce162eeb4e368d9eb751fe6751255135731d127f39634c14f5f8` |
| `data/raw/gvc/test.csv` | 330 | `d413352a044c84a3ef963dd9e359aa9958e22c178d45fb3ebec3ea6b45bded96` |
| `data/raw/gvc/gvc_doc_to_event.csv` | 20416 | `e94923d7d7e29e1dbcbdd618a5065941ecb2916a1320ff16bcf769d7e7161df6` |
| `data/raw/wec/Train_Event_gold_mentions.json` | 90177027 | `719e8e476a05b9c6abb01cd51f641c3ace67c6214e60f076dc5d1f26ef63c3a5` |
| `data/raw/wec/Dev_Event_gold_mentions_validated.json` | 2713689 | `08ab71161aa693445cdce555a891440d84ffebfcf8fdf3ebd635f606466bbf80` |
| `data/raw/wec/Test_Event_gold_mentions_validated.json` | 4093981 | `5213803a51b47151ec3caa5d41c995169cf0635eb8ae86fd7bfa784f39b5521a` |

## 9. 官方评分器与基础工具

MUC/B³/CEAFₑ采用`conll/reference-coreference-scorers`固定revision
`f49f3f8a0e1cdc5ceba7c2a33013897369df5543`；LEA采用同官方repo的原作者集成分支
`772e5a3fb76bea6c69e8cd7eb019b0eae5fcd970`。分别固定来源，使用同份序列化输入，
不要用改名函数/库默认行为冒充指标等价。

本轮验证评分入口、依赖和输入输出即可：准备包含非单例和单例的确定小fixture，
完美分区应有正确的标准得分，拆分/误合并的fixture应体现预期变化；同时检验重复、
缺失和额外mention ID被明确拒绝。这里是软件自检，不是论文模型实验，不据此宣称
三语料方法达标。不要把“测试skip”“只打印CUDA可用”当运行通过。

公共baseline只登记/取得所需公开来源及适配边界，本轮不要求复现论文原分。近年
CD-DCE/CohTP无可运行发布件不阻止文献表收录；不得写占位代码声称实现了它们。

## 10. Git与本地开发—远端运行

- 本地`git init -b main`建立**全新历史**；不要clone旧ekg再删文件，也不复制旧.git。
  目录已有未知内容时先检查，不`rm -rf`清场、不强推覆盖已有仓库。
- 按基础规范/来源、数据与环境、工具与验证等逻辑提交；提交真实可验收内容，主分支
  保持可运行。raw、`.venv`、缓存、权重及含凭据日志不入Git；校验manifest和锁文件入Git。
- 未提供新远端URL时，不以缺GitHub阻塞建设，也不指向ekg的origin；使用**新仓库的
  Git bundle**经SSH部署，三端均有完整独立Git仓库。以后作者提供新远端再接入。
  本委托不要求对外创建/公开仓库或擅自发送任何研究材料。
- 只传新项目提交与白名单数据。数据可从本地直接分别传两端；本任务已要求三端
  数据建设，允许其必要传输，不因此获得旧模型checkpoint跨机搬运或额外GPU实验授权。
- 明确写出同步流程：本地检查/提交→传Git提交或bundle→远端快进→核HEAD/锁hash→
  若lock变更才重建统一依赖→数据verify→运行。远端不临时改模型代码后忘记回传。
- 远端有未提交更改时先查清，不自动reset丢弃。禁`rsync --delete`、旧项目上的
  `git clean`、误删远端数据以及复制现有venv。新机器路径不进入模型/数据参数。
- 运行记录含被测commit、lock和manifest hash、准确命令、解释器、host/设备及产物。
  纯验收报告可以后提交；若代码/锁/数据清单变化，需要重验对应项目。

## 11. 验收矩阵：每项必须有证据

实施方可用脚本自动生成报告，但必须保留可复查的命令/退出码与原始日志；不能只
写“全部通过”。逐项用`PASS / FAIL / BLOCKED / NOT_REQUESTED`，必需项BLOCKED不能
算整体完成。设备忙导致未实测应标BLOCKED，不能标N/A后将GPU环境验收为通过。

| 编号 | 验收项 | 通过条件 | 必须提交的证据 |
|---|---|---|---|
| A01 | 三端扫描先于安装 | 三端有带时间的安装前扫描，版本选择引用实际硬件/软件；无猜测值充数 | 三端扫描JSON/文本、命令与退出码，统一环境决策 |
| A02 | 独立项目与历史 | 三目标目录正确，Git全新历史，无旧.git/任务队列/实验混入 | 根目录树、首提交说明、HEAD、Git状态、移交清单 |
| A03 | 功能模块边界 | SPEC定义数据→检索→pair→归并→评价接口，能缓存和独立运行；命名无章号 | SPEC、CLI/接口说明；本轮未实现的研究模块明确列出 |
| A04 | 一份环境声明 | 三端Python/uv/实际依赖版本与选定构建一致，同pyproject/lock及安装入口 | 三端解释器路径/版本、包清单规范化比较、文件hash和安装日志 |
| A05 | 隔离且可重建 | 三个新venv不指旧项目/系统site-packages；按lock从空环境能安装 | sys.prefix/sys.path、包解析路径、重建记录；不要只提交freeze列表 |
| A06 | 一份数据机制 | 三端同manifest和10件同hash原件；同reader同人口、无旧数据路径链接 | 三端verify/audit输出，传输前后hash、相对文件列表、跨度/ID/split检查 |
| A07 | 资料保真与清洁 | 当前研究、九表/来源/缺报/原文异常保留；旧结果不充新成绩 | 迁入源→目标及hash清单，当前文献表检查与provenance |
| A08 | 本地CPU基础验证 | 包可安装导入；数据、ID检查及评分fixture通过；本地未调用CUDA | CPU测试/静态检查/评分器自检的完整退出码，失败/skip明示 |
| A09 | 4090真实CUDA诊断 | 从新venv在空闲可用卡执行小张量运算、同步/结果及轻量反向检查，无CUDA kernel/ABI错误 | 准确命令/CWD/预期输出、卡UUID、Torch构建/设备能力与原始日志 |
| A10 | 5090真实CUDA诊断 | 同A09，验证真实设备及当前构建兼容性，不能仅`import torch` | 同A09；不照搬旧GPU能力/驱动结论 |
| A11 | 同一代码可双端运行 | 同代码提交、lock、数据机制在两端完成相同CPU数据/评分检查；最终HEAD同步 | 三端身份对照表、两端检查输出；允许硬件元数据和浮点容差内差异 |
| A12 | 无ekg运行依赖 | runtime无import ekg、旧根绝对路径、回指symlink、外部editable/.pth注入 | 新venv路径检查；清空继承PYTHONPATH后从项目外CWD运行；干净checkout/独立venv的CPU验证 |
| A13 | 旧项目未受影响 | 旧代码/lock/环境包未被安装/同步修改；不动旧数据、权重、日志 | 安装前后源文件/选定包metadata对照、实际修改路径清单 |
| A14 | Git与复审交付 | 提交清楚、无未说明脏改动/凭据/大数据；证据能定位被测版本与命令 | 提交列表、三端HEAD/status、验收矩阵、日志索引与已知问题 |

GPU诊断仅用于本次环境建设：每台一张空闲卡、小张量、短时运行，不调用研究模型、
不做训练任务。启动前列准确命令/CWD/预期输出并即时核占用，不能挤占他人资源。
本次委托不扩张5090后续研究训练、多seed、长任务或旧checkpoint迁移的权限。

A12允许provenance中出现旧repo名字和源路径；禁止的是运行依赖，不是擦除来源。
依赖锁/源码一致不意味着跨不同GPU训练必须逐bit相同，不把这种要求作为环境验收。

## 12. 交还作者与Codex的复审包

在新项目交付下列材料，并在最终回复给出绝对路径和被测提交：

1. `docs/HANDOFF.md`：新项目入口、任务范围、开发/同步/运行命令及当前未完成项。
2. `docs/ACCEPTANCE.md`：A01—A14逐项状态、证据路径、执行命令和准确缺口，不以平均分
   或文档数量代替验收。
3. `docs/provenance/transfer_manifest.json`：源版本/文件hash/目标/处理方式；原件清单
   位于`data/manifests/`，记录与三端verify结果对应。
4. 一份统一环境决策、锁文件、完整安装/重建命令；三端扫描、实际包清单及规范化
   差异报告。部署路径差异与软件版本差异分开，不把软件差异藏进host配置。
5. `artifacts/acceptance/`：原始扫描、安装、CPU/评分/GPU诊断日志及校验结果；大日志
   可不入Git，但索引与内容hash要能取到，不只留聊天截图。
6. 三端Git提交/状态及新项目全部实际改动的说明；若没有origin，注明bundle同步方式
   已验证，不虚构推送成功。

Codex复审将实际读取新仓库、manifest/lock和原始日志，抽查白名单迁移、旧依赖泄漏、
统一环境/数据及必要的短复核；实施方自评PASS不是最终复审结论。本轮完成意味着
独立工程基础可用，不意味着三项方法已实现或论文实验已完成。
