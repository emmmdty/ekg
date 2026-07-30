# MAVEN-ERE 官方 test 提交（CodaLab）

> 用途：拿 Ch1 共指 / Ch2 关系的**官方 test 分**，把「我们 valid vs 官方 test」这个跨 split 比较
> 拉平（这个数据集 dev 比 test 低 3.7–6.4 点，见 [`EXPERIMENTS.md`](EXPERIMENTS.md) Ch2 段）。
> 评测协议的三档定位见 `EXPERIMENTS.md` §1（本任务 = 档 A）。

## 0. 竞赛信息（2026-07-30 核）

| | |
|---|---|
| 竞赛 | **MAVEN-ERE Event Relation Extraction Challenge** |
| 地址 | `https://codalab.lisn.upsaclay.fr/competitions/8691` |
| 截止 | **Competition Ends: Never**（永久开放） |
| 上传件 | **`submission.zip`**，内含**单个文件 `test_prediction.jsonl`** |
| 主办方 | THU-KEG（`github.com/THU-KEG/MAVEN-ERE`，联系人 `wangxz098`） |

⚠️ **提交次数有上限，且只有登录后在 Participate 页才看得到具体配额。**
仓库硬规矩（`EXPERIMENTS.md` §1）：**官方 test 一次性，严禁拿 test 反复调参**，
所有超参 / 早停 / 模型选择只用 valid。

## 1. ⚠️ 先看清楚：test 的输入和 valid 不一样

本地 `data/processed/maven_ere/test_unlabeled.jsonl`（**857 篇**）实测字段：

```
顶层: ['TIMEX', 'event_mentions', 'id', 'sentences', 'title', 'tokens']
```

对比 valid 的 `events`（**已按共指聚好的事件簇**），test 只给 **`event_mentions`**——
一个**扁平的 mention 列表**，没有簇。含义有三：

1. **共指必须我们自己预测**。这会是 Ch1 与 Ch2 **第一次端到端接起来**（此前 Ch2 一直吃 gold 簇）。
2. **关系要输出在 mention id 上**，不是 event id。
3. **temporal 要覆盖 event–TIMEX 对**。原始 MAVEN-ERE 的 temporal 有 **39% 触及 TIMEX**，
   而我们的抽取器**没有 TIMEX 头**（`FAMILY_SUBTYPES` 只有 temporal/causal/subevent 三族，
   且 loader 会把 TIMEX 对静默丢掉）。
   ⇒ **这次提交的 temporal 分会很低，而且不冤**。要拿的是 **causal / subevent** 两个数
   —— 恰好也正是 Ch4 的 ECG 唯一读的两族。

## 2. 提交文件格式

`test_prediction.jsonl`，**每行一篇文档**：

```json
{
  "id": "<文档 id，与 test_unlabeled.jsonl 的 id 一致>",
  "coreference": [["mention_id_1", "mention_id_2", "..."], ["..."]],
  "temporal_relations": {
    "BEFORE": [["id_1", "id_2"]], "OVERLAP": [], "CONTAINS": [],
    "SIMULTANEOUS": [], "ENDS-ON": [], "BEGINS-ON": []
  },
  "causal_relations": { "CAUSE": [["id_1", "id_2"]], "PRECONDITION": [] },
  "subevent_relations": [["id_1", "id_2"]]
}
```

- `coreference` 是**簇**（每个内层 list 是一个共指链的 mention id 集合），不是边对。
- 关系用 **mention id**（`event_mentions[].id`）；temporal 还可用 **TIMEX id**（`TIMEX[].id`）。
- **六个 temporal 子类型和两个 causal 子类型的键都要在**，没有预测就给空列表。
- 857 篇**一篇都不能少**，包括没有任何预测的文档（各字段给空）。

## 3. 操作步骤

### 3.1 本地产出预测（**代码待写**）

现在**还没有**提交生成器。需要新增 `scripts/build_maven_ere_submission.py`，串三步：

1. 读 `data/processed/maven_ere/test_unlabeled.jsonl`（857 篇）。
2. **共指**：用 Ch1 的 `nodes/coref` + `nodes/canonical`，在每篇的 `event_mentions` 上聚簇
   → `coreference` 字段。checkpoint 是 `runs/nodes/coref_supervised_6ep`（当时训在 **5090**，
   要先确认它在哪台机器上、必要时经本地中转到 4090）。
3. **关系**：用 Phase A 的 `supervised` 抽取器（checkpoint `runs/relations/supervised_maven`，
   在 **4090**）对 mention 对打分，按 valid 上选定的阈值（**0.7**）二值化
   → 三个关系字段。**阈值不许在 test 上重调。**
4. 写 `test_prediction.jsonl`，逐篇自检：`id` 齐全、字段齐全、id 都在该篇的 mention/TIMEX 集合里。

### 3.2 打包

```bash
cd <产出目录>            # 注意：zip 里必须是裸文件，不能带目录层级
zip submission.zip test_prediction.jsonl
unzip -l submission.zip  # 确认只有 test_prediction.jsonl 一项、无路径前缀
```

### 3.3 上传

浏览器登录 CodaLab（需要账号），进竞赛页 → **Participate** 标签 → **Submit / View Results**
→ 上传 `submission.zip` → 等待 evaluation 跑完 → 在 **Results** 看官方分。
**这一步必须人工操作**（要登录凭据），我做不了。

## 4. 结果回填

拿到分后：

- 数字写进 [`results/PHASE_A.md`](results/PHASE_A.md)（单一事实源），标注 **官方 test / CodaLab / 提交日期**。
- [`TODO.md`](TODO.md) 的「对标与达成度」表把「我们(valid)」列换成 test 列，删掉那条 dev/test 外推警告。
- 若 causal test 分显著高于 valid 的 25.0（按 RESIJ 的 dev/test 落差，预期 +3~4），
  则「差 5.6 点」这个判断要相应改写，**不要留着旧结论**。

## 5. 已知风险

- **共指质量会拖累关系分**：test 上关系是在**我们预测的簇**上评的，Ch1 的 MUC 79.6 意味着
  簇本身有错，误差会传导。这恰好是 Ch4 「构建误差传播」在真实评测里的一次外部验证。
- **temporal 会很难看**（缺 TIMEX 头，39% 的金标对按构造抓不到）。报数时要显式说明这是
  实现范围问题而非模型问题，**不要用它下任何结论**。
- **提交配额有限**：先在本地用 valid 走一遍**同一条生成链路**（把 valid 当 test 格式跑通、用本地
  gold 自评），确认格式与数值合理，再动用一次 test 配额。
