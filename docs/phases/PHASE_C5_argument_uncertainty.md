# PHASE C5 — mention-local 论元不确定性感知的事件身份消解

> **BLOCKED / NOT FROZEN（E6 / T024，2026-09-07）。** E10 已证明唯一已核实的候选 ACCI 是 README-only
> 仓库，不能透明移植；作者尚未按 Ch1 的四条件指定替代第二方法族。本文件保留为待重新准入的草案，
> **不进入** R1 `protocol.json` 的 `phase_contracts`，不得实现、preflight、smoke 或启动 GPU。额外 seeds
> 未获授权，seed-13 pilot 过门前不得建立 seed-17/42 目录。

## Goal

待作者指定第二条满足四条件的方法族后，检验 independently predicted mention-local participant/place 精确
spans，以及由这些 hard spans 学得的 pairwise role-compatibility posterior 与缺失不确定性，能否在完整
MAVEN-ERE mention candidate 上减少角色冲突的高置信 false merge，并在官方 MUC 与全部 coreference 护栏上
超过 official joint、Qwen3 注册负面对照与新指定的第二方法族。Qwen3 本身不提供已校准 role posterior；
不得把生成字符串伪称为概率。

Specification coverage：RS-001、FR-001、FR-003–FR-007、FR-009–FR-015、QR-001–QR-004、QR-006–QR-007、
SC-001–SC-002、SC-006–SC-009。

## Inputs

- P1：`runs/stages/P1/p1-v6-20260904-r15/protocol.json`，SHA-256
  `1e31a9acef39261f776f7ed4069fd73f4531e8d12b55779bfc0fbd74c67f9655`；
- R1：`runs/stages/R1/r1-v61-20260904/protocol.json` 与同目录 `cross_artifact_audit.json`；protocol 的
  外部 SHA-256 必须与 `docs/results/PHASE_R1.md` 一致，audit 的外部 SHA-256 只从 `docs/HANDOFF.md` /
  `docs/TODO.md` 读取，避免 audit 对其哈希覆盖的结果页形成自引用；
- train/internal-dev manifest SHA-256：`47d19cc9a17e38259bfbb7f9206c675c7362f41252d23f414ea6cfd46015ca68` /
  `f5457b302be57663f8e618d977c492909c3210682804cb486bd67ccc8c171b5f`；
- MAVEN-ERE train SHA-256：`6a5519fe7c30448690adb13d49217c50d474fc57480eae10aecb29df7eb638b7`；
- internal-dev candidate digest：`15a3b1a548625624642130190b39411e6346866ff8594c2af2020cfbdac10910`；
- official evaluator SHA-256：`32919e86d98c6fafae6aa9505579e2c356caee12c32c1a8c719910acec359598`；
- encoder：ModelScope 可下载的 RoBERTa-base，冻结到本地内容寻址目录
  `.../roberta-base/71be7419a60dcce0fc276654c8f9213b41f8def71a0c3465d7fed2352c961ea9`；
- mention-local extractor：ModelScope `Qwen/Qwen3-8B`，config revision
  `8188480f040c5f1606a1bb3556abf14b31975155`、weight revision
  `7c9709d23bd2136dac1d6ea1fe30f4107d681cd6`；五片权重 SHA-256 为
  `31d6a825…cbf5f`、`5991236c…18282`、`c5185c47…96836`、`b5ee7de7…a917a`、
  `20c2d636…542ff`，完整 digest 由 R1 protocol 绑定；BF16、`enable_thinking=false`；
- extractor 只保留能唯一映回原句精确字符切片的 filler；模型的标点规范化可由连续 token 唯一对齐恢复，
  其他 JSON/role/span 错误必须逐 mention 写为 `partial` 或 `rejected`，保留原响应、原因和汇总计数；
- T020 baseline/input bundle：路径与 predictions/checkpoint/official-metrics SHA-256 只从 R1 protocol 读取，
  不从本文复制运行数字。

禁止把 MAVEN-ARG event-cluster arguments 复制给 mention；禁止缺失时回退到 gold；禁止改变 `EventNode`
字段、候选 mention、official threshold/scorer 或 final-valid 访问纪律。

## Baselines and causal matrix

同一 manifest/candidate/evaluator 下冻结：

1. MAVEN-ERE official joint primary anchor；
2. Qwen3 mention-local participant/place + learned argument-span pair pooling `qwen3-argument-s13-r2`；它低于
   anchor，是「朴素池化预测论元会掉点」的注册负面对照，**不是**第二方法族或 strong baseline；
3. 第二条方法族：**作者待指定**。ACCI 不可运行，IP&M 2024 无公开代码，均不得填入此项；
4. proposed span-conditioned role-compatibility posterior + missingness-aware uncertainty gate（full，待重新准入）；
5. full 去掉 role residual（remove-core，待重新准入）；
6. document×event-type 内 role posterior permutation（negative control，待重新准入）；
7. MAVEN-ARG event-level gold arguments 仅列 non-deployable oracle，不参与胜出门。

除注册组件外，2、以及重新准入后 3–6 的 encoder、pair population、optimizer steps、seed、预算和 scorer
必须逐位一致。旧的 annealed local pair classifier 与 hard-arguments-without-uncertainty 臂不在 E4 通过的
brief roster 中，故不纳入本草案。

## Tasks

### C5.0 implementation and local gate

实现 posterior/uncertainty sidecar、role-alignment residual、中介计数和 bundle exporter。单测覆盖完整 ID、
重复/缺失/坏 offset、未知 role、permutation、remove-core 单变量性与 `EventNode` schema lock。运行三件套。

### C5.1 immutable preflight and baseline replay

**不得执行，直到作者名单重新准入并写入新 T024 binding。** 届时物化
`runs/stages/C5/c5-v61-argument-uncertainty-r1/preflight/`，冻结 source/manifest/candidate/evaluator、
extractor、encoder、code/config/command hashes 与 final-valid ledger。重算 official joint、Qwen3 注册负面对照
与新第二方法族的 official MUC/B3/CEAFe/BLANC；任何 population 或 hash 漂移立即停止。

### C5.2 CPU/CUDA smoke

CPU fixture 覆盖空角色、多 filler、同字符串重复与全 singleton 文档。4090 单卡仅跑 10 documents、一次
forward/backward/export/reload；断言 logits/loss/uncertainty 有限，所有 mention 恰好一个 cluster，完整候选
未变，gold argument 未被读取。

### C5.3 seed-13 pilot

**不得执行，直到重新准入。** 届时只运行矩阵 4–6 的 seed 13。训练期仅读 train；internal-dev 只按固定
退火终点评分，不扫 threshold/epoch。
逐文档保存 official scorer sufficient statistics、false merge mediator、coverage 与 calibration。

### C5.4 promotion and handoff

seed-13 同时过主门、中介、负控和护栏后，只写 `confirmation_eligible=true` 并停下请求额外 seeds 授权。
若获授权，matched seeds 13/17/42 后进行 document-cluster paired bootstrap；配置完全冻结后才可 sealed
final-valid 一次。无论 pass/failed 都输出不可变 handoff。

## Promotion gate

- 本草案没有 seed-13 promotion 权限。重新准入后：full 的 MUC 必须严格高于 official joint、Qwen3 注册负
  对照与作者指定的第二方法族；full 相对 remove-core 降低注册的 incompatible-role false-merge rate，且
  permutation 消除该中介改善；
- internal-dev secondary floors：B3、CEAFe、BLANC 分别不低于 official-joint anchor 的 0.5 个绝对 F1 点；
- confirmation：仅在重新准入及授权后，matched seeds 13/17/42 的 mean MUC delta ≥ `+0.010`，至少 2/3 为正，
  10,000 次 document-cluster paired-bootstrap 95% CI 下界 > 0，且均值超过 official joint 与新第二方法族；
- coverage 必须是 manifest 的 291 documents / 7,195 mentions，全量显式 `ok` / `empty` / `partial` /
  `rejected`；拒绝率与原因必须报告，任何 silently dropped mention 直接失败。

## Stop conditions

- 未有作者指定且可按四条件运行的第二方法族：保持 blocked，不得把 Qwen3 或 ACCI 填作替身；
- Qwen3 artifact 不能完成 manifest、使用非 verbatim span、或需要 cluster gold 才能覆盖：停止输入线；
- full 不改变注册 mediator，或 permutation 保留同样 mediator 改善：机制 claim 失败；
- 任一有效周期未超过两条强 baseline 或 secondary floor：该周期失败；两个有效周期后封存家族；
- 不以更大 backbone、threshold/epoch sweep、换 split 或 oracle argument 救结果；失败身份进入 E3 fallback。

## Bundle

`runs/stages/C5/c5-v61-argument-uncertainty-r1/` 必含 `protocol.json`、逐 mention argument sidecar、逐实例
coreference predictions、raw official metrics、mediator/paired statistics、checkpoint hashes、`status.json` 与
`fallback_component_bundle_id`。结果数字只追加到 `docs/results/PHASE_C.md`。

## GPU command

此命令**当前禁止执行**。仅在作者指定第二方法族、R1 建立新的 C5 T024 binding、实现与 preflight 完成后，
固定入口为：

```bash
cd /data/TJK/ekg
CUDA_VISIBLE_DEVICES=0 .venv/bin/python -u scripts/run_c5_argument_uncertainty.py \
  --contract runs/stages/C5/c5-v61-argument-uncertainty-r1/preflight/protocol.json \
  --seed 13 \
  --output runs/stages/C5/c5-v61-argument-uncertainty-r1/pilot/seed-13
```

启动前须展示这条命令、`/data/TJK/ekg` 和预期目录，并重新核卡；长任务用 `setsid nohup`。脚本或
preflight 尚不存在、当前 commit 未过本地 gate、GPU 非空闲时均不得启动。
