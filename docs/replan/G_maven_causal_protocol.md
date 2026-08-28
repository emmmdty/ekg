# MAVEN-ERE causal relation extraction / identification 公开复现协议审计

## Executive verdict

**结论：截至 2026-08-26，当前应判定为 `NO-GO`。**

这不是因为 MAVEN-ERE 数据本身不可用。恰恰相反，MAVEN-ERE 的公开 `train/valid`、因果标签语义、官方 prediction schema、官方 `evaluate.py`，以及一条可在公开 `valid` 上进行本地因果评测的路径都相当清楚。真正卡死“硕士论文主指标协议”的，是你设定的更高门槛：**没有找到一条 A/B/C 轴同时满足“协议完全公开可冻结 + 至少两个独立 2024–2026 正式方法拥有同协议公开执行闭环 + 两者都有可信单张约 27GB 路径”。**

三个主轴的状态可以概括为：

| 轴 | 当前结论 | 决定性问题 |
|---|---|---|
| **A 官方 hidden-test** | **FAIL** | `test.jsonl` 输入公开，但 test gold 明确不公开；官方 scorer 代码公开，却没有本地 hidden gold。CodaLab 页面可见不等于本审计已验证 2026 年仍可登录→提交→返回 score。因此 A 不能成为“完全本地可审计”主协议。官方论文与 Wei 2024 属于该轴；TacoERE 的主 PLM 表也采用官方 2913/710/857 split，但其代码闭环未取得。 citeturn20view0turn23view0turn28view2 |
| **B Chen / LLMERE original-valid-as-test** | **最接近可冻结，但仍 FAIL** | 两篇论文都写“original train 8:2、original valid→test”，但**只有 LLMERE 公开了 `random.seed(42)` 的 split script**；Chen 没有 split generator、seed 或 document manifest。更严重的是，Chen 的实际 pair universe/evaluator 与 LLMERE 不同：Chen 做句子级 pair sampling，并明确排除“四类关系均为空”的 event pair；LLMERE scorer 则对文档内所有有序 gold event-mention pair 加 `NONE`。所以二者只是“test split policy 相似”，不是同一 causal benchmark protocol。 citeturn27view0turn29view5 fileciteturn21file0 fileciteturn26file0 |
| **C Xiang causal-only** | **FAIL** | 论文写 original dev→test、original train 抽 10%→dev，但未锁定 seed/document manifest；作者公开 `GLM4ECI` 仓库实际 tree 中没有 MAVEN-ERE 数据转换代码，`load_data.py` 读取的是 `train.npy`、topic `37/41`、5-fold 逻辑，即 EventStoryLine 风格路径，而不是论文的 MAVEN-ERE C 轴。更没有第二个独立近期同轴可执行方法。 fileciteturn35file0 fileciteturn37file0 |

因此，**不能把 Chen + LLMERE 因为都写“8:2 + original valid as test”就算成两个同协议 baseline；也不能把 Wei/TacoERE 的 hidden-test 数字、KnowQA/MMD 的 sample 数字、Xiang 的 causal-only split 数字混进来凑两个对手。**

你已有的本地 MAVEN-ERE causal 记录——全量 public valid 上约 **28.50**，官方原版同 valid 约 **31.37**——只能证明“公开 valid + 官方 evaluator”这项本地资产已经存在。它们**不能**与 A hidden test、B 重新切分 train 后的 original-valid-as-test、或 C Xiang setting 做差值比较；本报告也不据此推荐方法。

**下一阶段唯一值得继续保留的轴是 B，但只能作为“协议资产候选”，还不能升级为论文主指标。** LLMERE 已把 B 的 split 和 causal scorer 写得足够接近可冻结；然而当前缺少第二个真正兼容、独立、近期、可执行的方法。A 不可能满足“hidden gold 本地可得”；C 则连作者自己的 MAVEN-ERE execution package 都未闭环。

## Paper identity corrections

身份首先按 ACL Anthology 正式条目/PDF冻结；仓库只有在作者名、论文内代码 URL、repo owner/commit author 能相互对应时才视为作者团队仓库。

| 用户简称 | ACL 正式身份 | DOI | 身份/名称更正 |
|---|---|---|---|
| **MAVEN-ERE 数据论文** | **MAVEN-ERE: A Unified Large-scale Dataset for Event Coreference, Temporal, Causal, and Subevent Relation Extraction**；Xiaozhi Wang, Yulin Chen, Ning Ding, Hao Peng, Zimu Wang, Yankai Lin, Xu Han, Lei Hou, Juanzi Li, Zhiyuan Liu, Peng Li, Jie Zhou；EMNLP 2022；ACL ID `2022.emnlp-main.60`。ACL: `https://aclanthology.org/2022.emnlp-main.60/`，PDF: `https://aclanthology.org/2022.emnlp-main.60.pdf`。 citeturn16search2turn20view0 | `10.18653/v1/2022.emnlp-main.60` | 无名称问题。注意官方论文的 **103,193 是 event coreference chains，不是 event mentions**；event mentions 是 **112,276**。 citeturn20view0turn22view1 |
| **Chen et al. 2024** | **Improving Large Language Models in Event Relation Logical Prediction**；Meiqi Chen, Yubo Ma, Kaitao Song, Yixin Cao, Yan Zhang, Dongsheng Li；ACL 2024 Long；ACL ID `2024.acl-long.512`。ACL: `https://aclanthology.org/2024.acl-long.512/`，PDF: `https://aclanthology.org/2024.acl-long.512.pdf`。 citeturn26view0 | `10.18653/v1/2024.acl-long.512` | 正式题名不是 repo/早期项目名称。论文明确给出代码 `https://github.com/chenmeiqii/Teach-LLM-LR`；repo HEAD commit author 为 Meiqi Chen，因此作者归属成立。 citeturn26view0 fileciteturn12file0 |
| **Wei et al. 2024** | **Are LLMs Good Annotators for Discourse-level Event Relation Extraction?**；Kangda Wei, Aayush Gautam, Ruihong Huang；Findings of EMNLP 2024；ACL ID `2024.findings-emnlp.1`。ACL: `https://aclanthology.org/2024.findings-emnlp.1/`，PDF: `https://aclanthology.org/2024.findings-emnlp.1.pdf`。 citeturn23view0 | `10.18653/v1/2024.findings-emnlp.1` | 作者仓库是 `https://github.com/WeiKangda/LLM-ERE`；owner/HEAD author 均对应 Kangda Wei，repo README 也写出正式题名与全体作者。 fileciteturn40file0 fileciteturn41file0 fileciteturn47file0 |
| **TacoERE** | **TacoERE: Cluster-aware Compression for Event Relation Extraction**；Yong Guan, Xiaozhi Wang, Lei Hou, Juanzi Li, Jeff Z. Pan, Jiaoyan Chen, Freddy Lecue；LREC-COLING 2024；ACL ID `2024.lrec-main.1348`。ACL: `https://aclanthology.org/2024.lrec-main.1348/`，PDF: `https://aclanthology.org/2024.lrec-main.1348.pdf`。 citeturn16search0turn28view0 | **ACL Anthology 正式页未列 DOI** | “TacoERE”是方法名也是正式题名的一部分。论文脚注中的 HuggingFace URL是 Transformers 依赖，不是 TacoERE 作者代码仓库；截至本审计检索范围未取得 TacoERE 作者官方 repo。 citeturn28view1 |
| **KnowQA** | **Document-level Causal Relation Extraction with Knowledge-guided Binary Question Answering**；Zimu Wang, Lei Xia, Wei Wang, Xinya Du；Findings of EMNLP 2024；ACL ID `2024.findings-emnlp.986`。ACL: `https://aclanthology.org/2024.findings-emnlp.986/`，PDF: `https://aclanthology.org/2024.findings-emnlp.986.pdf`。 citeturn13view2 | `10.18653/v1/2024.findings-emnlp.986` | 正式题名并不以 “KnowQA” 开头。论文给出的代码 URL 为 `https://github.com/du-nlp-lab/KnowQA`；但截至 2026-08-26 本审计对该地址取得的是 404，故只能记录“论文曾给出作者代码 URL；当前仓库未取得”，不能写“当前公开可运行”。 |
| **LLMERE** | **Large Language Model-Based Event Relation Extraction with Rationales**；Zhilei Hu, Zixuan Li, Xiaolong Jin, Long Bai, Jiafeng Guo, Xueqi Cheng；COLING 2025；ACL ID `2025.coling-main.500`。ACL: `https://aclanthology.org/2025.coling-main.500/`，PDF: `https://aclanthology.org/2025.coling-main.500.pdf`。 citeturn16search1 | **ACL Anthology 正式页未列 DOI** | “LLMERE”是方法名，不是完整题名。作者仓库 `https://github.com/HerbertHu/LLMERE` 的 README 直接指向该 COLING 论文。 fileciteturn51file0 |
| **MMD-ERE** | **MMD-ERE: Multi-Agent Multi-Sided Debate for Event Relation Extraction**；Yong Guan, Hao Peng, Lei Hou, Juanzi Li；COLING 2025；ACL ID `2025.coling-main.460`。ACL: `https://aclanthology.org/2025.coling-main.460/`，PDF: `https://aclanthology.org/2025.coling-main.460.pdf`。 citeturn13view4 | **ACL Anthology 正式页未列 DOI** | 无题名串线。当前未取得作者公开代码仓库。 |
| **Xiang et al. directional ECI** | **Evaluating Instructively Generated Statement by Large Language Models for Directional Event Causality Identification**；Wei Xiang, Chuanhong Zhan, Qing Zhang, Bang Wang；Findings of ACL 2025；ACL ID `2025.findings-acl.43`。ACL: `https://aclanthology.org/2025.findings-acl.43/`，PDF: `https://aclanthology.org/2025.findings-acl.43.pdf`。 citeturn13view5 | `10.18653/v1/2025.findings-acl.43` | 论文正文把 Wang et al. 2022 数据简称为 “MAVEN”，但引用和关系统计实际对应 **MAVEN-ERE**；此外它把 **103,193 错写为 event mentions**，而官方 MAVEN-ERE 是 112,276 mentions / 103,193 chains。作者仓库 `https://github.com/zhanchuanhong/GLM4ECI` 的描述直接写出该论文题名，因此归属成立。 citeturn20view0 fileciteturn33file0 |

作者独立性必须按**人名**而不是机构/缩写判断。MAVEN-ERE 原作者集合中包含 Xiaozhi Wang、Hao Peng、Zimu Wang、Lei Hou、Juanzi Li 等，因此 TacoERE 与原数据团队重叠 **Xiaozhi Wang / Lei Hou / Juanzi Li**；KnowQA 重叠 **Zimu Wang**；MMD-ERE 重叠 **Hao Peng / Lei Hou / Juanzi Li**。Chen 的 **Meiqi Chen** 与数据论文的 **Yulin Chen** 不是同一作者。Chen、Wei、LLMERE、Xiang 四组与 MAVEN-ERE 原团队没有作者交集。TacoERE 与 MMD-ERE 本身还共享 Yong Guan、Lei Hou、Juanzi Li，所以也不能把二者算成两个独立团队。上述作者表均来自各 ACL 正式页面/PDF。 citeturn16search2turn16search0turn16search1

## A/B/C protocol map and frozen data/evaluator specification

### 官方数据与 scorer 的可冻结部分

MAVEN-ERE 官方仓库是 `https://github.com/THU-KEG/MAVEN-ERE`。截至审计日，default branch 为 `main`，HEAD 为 **`ac81a9711a69f43f55bfbc50b3bb573fd11c64b0`**；仓库未 archived，license 为 **GPL-3.0**。GitHub Releases API 返回空数组；README 将公开数据称为 **version 1.0**。本审计未成功取得 tags 列表，故 tag 记“未核实”，不能用 version 1.0 推断存在同名 Git tag。 fileciteturn2file0 fileciteturn3file0 fileciteturn42file0

官方 README/data script 指向 `data/MAVEN_ERE/{train.jsonl,valid.jsonl,test.jsonl}`，下载入口由 `data/download_maven.sh` 固定为 Tsinghua Cloud。README 明确说明 **test annotations are kept unpublic**，并提供 CodaLab 与 `evaluate.py`。本审计沙箱对 Tsinghua Cloud 发生 DNS/下载失败，因此**没有伪造 SHA-256**；下面的统计使用正式论文 Table 13–16，而不是声称已经在当前沙箱重算。官方数据下载脚本：`https://github.com/THU-KEG/MAVEN-ERE/blob/ac81a9711a69f43f55bfbc50b3bb573fd11c64b0/data/download_maven.sh`。 fileciteturn5file0 fileciteturn6file0

因果任务的官方 split 统计为：

| split | documents | event mentions | causal relations |
|---|---:|---:|---:|
| train | 2,913 | 73,939 | 36,316 |
| development / `valid` | 710 | 17,780 | 9,698 |
| hidden test | 857 | 20,557 | 11,978 |
| **总计** | **4,480** | **112,276** | **57,992** |

这是正式论文 Appendix D, Table 15；总因果关系进一步由 Section 2.3 分成 **10,617 CAUSE + 47,375 PRECONDITION**。 citeturn21view0turn22view0turn22view1 原始 PDF：`https://aclanthology.org/2022.emnlp-main.60.pdf`。

这里有一个必须冻结清楚的语义差异：

**标注候选范围**与**评测 candidate universe**不是一回事。数据构建时，因果标注仅在已经标为 `BEFORE` 或 `OVERLAP` 的 event pair 上进行，以降低人工标注成本；但官方 causal evaluator **不是**只评这些 pair。它收集每个文档的 gold event mention IDs，枚举文档内所有 `m1 != m2` 的**有序 mention pair**，默认 `NONE`，再把 event-level gold `CAUSE/PRECONDITION` 展开到头尾 coreference cluster 的 mention 笛卡尔积。 citeturn20view0 fileciteturn7file0

所以官方 causal 任务应冻结为：

\[
U_d=\{(m_i,m_j)\mid m_i,m_j\in E_d,\ i\neq j\},
\]

标签是 `{NONE, PRECONDITION, CAUSE}`；`CAUSE(A,B)` 的反向 `(B,A)` 是另一个独立 candidate，除非 gold 另有关系，否则为 `NONE`。不存在“同句窗口”“邻句窗口”或“只枚举 gold-positive candidates”这一评测限制。官方 causal baseline README 也明确写 `n` 个 events 枚举 `n(n-1)` pairs。 fileciteturn43file0

官方 scorer `evaluate.py` 固定 `REL2ID["causal"]={"NONE":0,"PRECONDITION":1,"CAUSE":2}`，causal 只把 `[1,2]` 作为 positive labels，以 sklearn 的 **micro Precision / Recall / F1** 计算；`NONE` 不进入 positive-class F1。所有文档的 pair 被汇总后计算 micro，而不是先算每文档 F1 再平均，也不是 macro-F1。 fileciteturn7file0 原始代码：`https://github.com/THU-KEG/MAVEN-ERE/blob/ac81a9711a69f43f55bfbc50b3bb573fd11c64b0/evaluate.py`。

官方 prediction JSON 的 causal 部分是 mention-ID pair：

```text
{
  "id": "...",
  "causal_relations": {
    "CAUSE": [[mention_id_1, mention_id_2], ...],
    "PRECONDITION": [[mention_id_1, mention_id_2], ...]
  }
}
```

完整 submission 同时还有 coreference、temporal、subevent 字段。官方 competition wrapper 一次评四类任务；**直接调用已经存在的 `evaluate(golden, prediction, "causal")` 只选择 causal scorer，不改变 causal metric**，因此属于纯选择适配。反之，如果改成只评同句 pair、只评 gold relation candidate、合并方向、做 binary causal/non-causal，都会改变指标。 fileciteturn5file0 fileciteturn7file0

gold trigger 前提也要区分 split。公开 `train/valid` 的 `events` 给出 gold event mentions/coreference clusters，因此这里是 **gold-mention relation classification/extraction**。hidden `test.jsonl` 不公开完整 gold annotations，而是公开 `event_mentions` 候选，其中可包含 distractors；官方 scorer 最终只针对 hidden reference 中的 gold event mentions 计分。因此 A 轴不能简单描述成“测试时已知所有 gold triggers”。官方 baseline `causal/src/data.py` 在有 `events` 时使用 gold mentions；没有 `events` 的 test 则读取 `event_mentions`。 fileciteturn5file0 fileciteturn45file0

### 三条主轴与额外 setting

| 协议轴 | 数据切分 | pair / gold 前提 | evaluator | 文献归属 | 冻结判断 |
|---|---|---|---|---|---|
| **A 官方 hidden-test** | official train=2913，valid=710，test=857；test input 可下载、gold 隐藏。 citeturn22view0 | 官方 all ordered event-mention pairs；directed CAUSE/PRECONDITION/NONE。hidden test 的 gold mention filtering 也在私有 reference 中。 fileciteturn7file0 | 官方 `evaluate.py`；micro positive P/R/F1。 | MAVEN-ERE 2022；Wei 2024 明确 report whole 857-doc test；TacoERE PLM 使用相同 2913/710/857 split。 citeturn23view0turn28view2 | **本地主协议 FAIL**：hidden gold 不公开。 |
| **B Chen / LLMERE split policy** | original train→8:2 train/dev；original valid→test。Chen Appendix E 与 LLMERE Appendix C 都这样写。 citeturn27view0turn29view5 | **不能统一**。Chen 是句子级 sample，并排除“四类 event relations 全空”的 pair；LLMERE causal evaluator 枚举公开 test 文档内所有有序 gold event-mention pair。 | **不能统一**。Chen repo 用每个 relation axis 的 sklearn classification report；LLMERE 有独立 causal scorer，语义接近官方 micro-positive scorer。 | Chen 2024；LLMERE 2025。 | **split policy 同名，benchmark protocol 不同。** |
| **C Xiang causal-only** | 论文：original development→test；original training 的 10%→development。exact seed/IDs 未公开锁定。 | directional ECI；准确负例 universe/manifest 无法从公开 MAVEN code 重建。 | 论文 causal-only；公开 repo 没有 MAVEN scorer/pipeline。 | Xiang et al. 2025。 | **FAIL**。 |
| **D-KnowQA sampled** | “sample a subset from MAVEN-ERE”，并结合 MAVEN-ARG gold argument information；exact public manifest 未取得。 citeturn10view5 | knowledge-guided binary QA；非 A/B/C 全量 protocol。 | 自身 setting。 | KnowQA 2024。 | **单列，不准塞 B。** |
| **D-TacoERE LLM sample** | LLM 实验另取 MAVEN-ERE 50 docs、646 causal relations；与其 PLM 主表的 A 轴不同。 citeturn28view4 | 2-shot LLM relation prediction。 | 自身 sample。 | TacoERE 2024 Sec. 3.6/Table 5。 | **单列。** |
| **D-MMD-ERE sample** | 论文按关系类型抽 50 documents，MAVEN-ERE causal 得到约 605 relation instances。 citeturn10view3 | multi-agent debate sampled ERE。 | 自身 sample。 | MMD-ERE 2025。 | **单列。** |

### 为什么 B 不能把 Chen 与 LLMERE 强行并成一个协议

Chen Appendix E 写得很关键：MAVEN-ERE 因 test 不可访问而对 original train 做 8:2，再用 original valid 当 test；但紧接着又规定 **“sampling at sentence level” 且两个 events 没有任何 relations 的样本会被排除**。 citeturn27view0 这意味着它不是官方 all-pairs causal extraction universe。

Chen 的发布 cache 也反映了这种做法：每个 event pair 保存两个方向及四类关系 label；例如 causal 可以只在一个方向为 CAUSE。repo 的 `evaluate_maven.py` 对 causal/coreference/temporal/subevent 分别调用分类指标，而不是把预测 dump 成官方 `test_prediction.jsonl` 再跑 MAVEN `evaluate.py`。 fileciteturn29file0 fileciteturn15file0

相比之下，LLMERE `eval/MAVEN_ERE/eval_causal.py` 对 `doc.events_all` 枚举所有有序 `(e1,e2)`，缺省 `NONE`，报告 positive labels `[PRECONDITION,CAUSE]` 的 micro average。 fileciteturn26file0 fileciteturn27file0

因此这里不是一个微小 evaluator adaptation，而是**candidate universe 改了**。即使将来证明 Chen 恰好也用了 seed 42，Chen 与 LLMERE 仍然不能直接作为同一 causal main-metric protocol 的两个方法。

## Per-paper protocol matrix

| 正式身份 | 任务范围 / 数据 / 轴 | split 与 gold 前提 | pair / labels / metric | baseline 来源 | repo 与数据闭环 | 硬件与关键缺失 |
|---|---|---|---|---|---|---|
| **MAVEN-ERE**, `2022.emnlp-main.60`, DOI `10.18653/v1/2022.emnlp-main.60`。 citeturn16search2 | Full ERE；官方 v1.0 `train.jsonl/valid.jsonl/test.jsonl`；**A**。 | Original 2913/710/857；train/valid gold events，test gold hidden。 | Causal `{CAUSE,PRECONDITION,NONE}`，全篇所有有序 event-mention pairs；official `evaluate.py` micro positive P/R/F1。 fileciteturn7file0 | 原数据论文自己的 RoBERTa / joint baseline；仅作为 sanity，不能计近期两对手。 | `https://github.com/THU-KEG/MAVEN-ERE`；raw→train→predict→submission 代码存在；test local evaluate 被 hidden gold 截断。 | `causal/main.py` 默认 RoBERTa-base、max length 256；README command batch 4/50 epochs。论文/已核验代码未给出可作为本审计依据的 GPU 显存型号。 fileciteturn43file0 fileciteturn44file0 |
| **Chen et al.**, `2024.acl-long.512`, DOI `10.18653/v1/2024.acl-long.512`。 citeturn26view0 | Full four-relation logical prediction；**B-like**，不是 official causal all-pairs。 | Paper: original train 8:2, original valid=test；**split seed/IDs/manifest 未发布**。Repo 的 `--seed 42` 是运行 seed，不能证明是 data split seed。 | 句子级 relation-bearing pair samples；四 relation axes；main Table 1 是 ERE Micro-F1/LI，而不是一个公开正式 causal-only main score。代码能输出 causal classification report，但不是 official MAVEN causal evaluator。 citeturn27view6 | RoBERTa-Large 是作者 fine-tuning baseline；LLM results 为作者实验。不能视为 LLMERE all-pair setting 的重跑结果。 | `https://github.com/chenmeiqii/Teach-LLM-LR`，HEAD `58de425c...`；有 cached prompts + evaluation，但**无 raw→8:2 split→cache generator、无训练主链、无官方 prediction dump**。 fileciteturn13file0 | RoBERTa-Large: paper 单 V100，batch16，max256，20/50 epochs；LoRA 13B: single A100 **80GB**。repo local Vicuna/Llama2-13B 使用作者机器绝对路径并 FP16 load，默认又是 GPT API。27GB **FAIL**。 citeturn27view3turn27view4 fileciteturn15file0 |
| **Wei et al.**, `2024.findings-emnlp.1`, DOI `10.18653/v1/2024.findings-emnlp.1`。 citeturn23view0 | Full ERE；**A official hidden-test**。 | 10 train docs 作 demonstrations，10 valid docs 做 prompt design；最终 report **whole 857-doc official test**。 citeturn23view0 | 使用给定 event/TIMEX mentions；causal `CAUSE/PRECONDITION`；论文明确说 F1 用 Wang et al. 官方 evaluation script。 citeturn23view0turn24view1 | supervised RoBERTa baseline 明确跟随 Wang et al.; LLM/SFT 是本论文自己的运行。 | `https://github.com/WeiKangda/LLM-ERE`，HEAD `2f1d5c4d...`；包含官方 baseline 代码、LLM scripts、postprocess/evaluate 命令。**但 whole-test local F1 仍需要 hidden reference**。 fileciteturn46file0 fileciteturn49file0 | Llama2-7B；SFT 3 epochs, lr2e-4, 4-bit quantization, LoRA rank64/dropout.1；论文未声明 GPU 型号/显存，因此不能仅凭“7B 4-bit”判 27GB PASS。GPT3.5 路径依赖已过时的商业 API snapshot。 citeturn25view0 |
| **TacoERE**, `2024.lrec-main.1348`, ACL DOI 空。 citeturn16search0 | PLM 主实验：MAVEN causal / subevent，官方 2913/710/857 split，故 paper-level 属 **A**；LLM Sec.3.6 的 50-doc experiment 是另一个 **D**。 | PLM: official split；gold event triggers given；论文任务定义为 annotated document 中所有 event pairs。 citeturn28view2turn28view4 | directed causal；不 downsample negatives；P/R/F1。Table 1 的 legacy baselines 未提供可核验 rerun artifacts，审计按 reported/implementation provenance 未锁定处理，不能据表格本身认定全是同 split 重跑。 | **截至检索范围未取得作者官方 TacoERE repo**，故 raw→compression→train→predict→evaluate 闭环无法审计。 | PLM 每次 training/testing 用 **2× NVIDIA GeForce RTX 3090**；LLM 路径用 OpenAI GPT-4/ChatGPT/Text-Davinci APIs。论文公开路径不是单卡约27GB。 citeturn28view3 |
| **KnowQA**, `2024.findings-emnlp.986`, DOI `10.18653/v1/2024.findings-emnlp.986`。 citeturn13view2 | Document-level causal RE；MAVEN-ERE + MAVEN-ARG gold arguments；**D sampled**。 | Paper follows prior work to sample subset；未取得 exact document manifest/seed。 | Knowledge-guided binary QA for causal relations；非官方 all-4480/full valid setting。 citeturn10view5 | 论文 baseline comparison 不能外推到 A/B/C。 | Paper URL `https://github.com/du-nlp-lab/KnowQA` 在本审计日未取得（404）；当前 HEAD/license/tree 均记 **未取得**，故 execution closure FAIL。 | 具体 GPU/显存/完整训练命令本审计未能从现存一手代码核实；不得猜。另有 Zimu Wang 与 MAVEN-ERE 原团队重叠。 |
| **LLMERE**, `2025.coling-main.500`, ACL DOI 空。 citeturn16search1 | Full ERE；own results 属 **B**。 | Paper: train 8:2, original valid=test；repo `split_data.py` 明确 `random.seed(42)`、shuffle original `train.jsonl`、前80% train/后20% valid、复制 original `valid.jsonl` 为 test。 citeturn29view5 fileciteturn21file0 | causal test 使用 gold triggers；all ordered gold event-mention pairs；`NONE/PRECONDITION/CAUSE`；micro positive P/R/F1。 fileciteturn26file0 | Paper 的 legacy baseline 部分引用 Joint/Split/ProtoERE/Wei 等；由于 Wei 正式论文使用 A hidden test，而 LLMERE 改成 B，且 repo 没有这些 baseline 的 B 重跑训练闭环，**不能自动把引用数字认作 B 轴实跑结果**。 citeturn29view1 | `https://github.com/HerbertHu/LLMERE`, HEAD `94d4ef278...`, MIT；公开 root 主要是 data conversion、eval、output，README 只有论文链接，**没有完整 training/inference/environment command package**。因此不是 raw→train→predict→evaluate 的完整复现包。 fileciteturn18file0 fileciteturn51file0 fileciteturn52file0 | Paper: LLaMA2-7B/LLaMA3-8B + LoRA/LLaMA-Factory，rank64, max2048, 3 epochs on MAVEN，**single A100 40GB**。这不能直接证明 27GB。repo 又缺实际 trainer config，所以 27GB **FAIL/未证明**。 citeturn29view1turn29view2 |
| **MMD-ERE**, `2025.coling-main.460`, ACL DOI 空。 citeturn13view4 | Multi-agent full ERE method，但 MAVEN causal evaluation 为 **D sample**。 | 按关系类型抽 50 documents；causal sample ≈605 relation instances；exact public manifest 未取得。 citeturn10view3 | 自身 multi-agent sampled evaluator，不能与 A/B/C 合并。 | 论文表格为自身 sample setting。 | **作者官方 repo 未取得**；无法审计 imports、missing cache、API outputs、history。 | multi-agent LLM 路径不是已证明的本地单27GB baseline；具体 GPU local closure 未取得。且 Hao Peng/Lei Hou/Juanzi Li 与数据团队重叠。 |
| **Xiang et al.**, `2025.findings-acl.43`, DOI `10.18653/v1/2025.findings-acl.43`。 citeturn13view5 | **Directional ECI, causal-only；C**。 | Paper: original dev→test；original train 的10%→dev；**seed / IDs / manifest 未锁定**。 | causal directional classification；由于 public repo 没有 MAVEN conversion/evaluator，完整 negative universe 无法从代码冻结。 | 自身 directional ECI results。 | `https://github.com/zhanchuanhong/GLM4ECI`, HEAD `742f3110...`, no license；tree 只有8个小型 Python/README 文件。`load_data.py` 实际读取 `train.npy`、排除 topic37/41、5-fold split——不是 MAVEN-ERE。 fileciteturn34file0 fileciteturn35file0 fileciteturn37file0 | Paper 声明 BART-base / Llama-160M、batch16，在一张“GTX 3090”上运行；从算力本身看不构成明显 27GB 障碍，但**公开代码不含 MAVEN 路径**，所以不能算 baseline PASS。 |

LLMERE 还存在一个值得冻结到审计记录里的**论文—代码不一致**：论文 Section 4.2 写 temporal/causal/subevent/coreference 的 positive:negative 分别为 **4:1 / 1:1 / 2:3 / 2:3**；但公开 `data_handle_MAVEN_ERE/convert_causal.py` 在 causal training conversion 中计算 `neg_num = int(len(examples_pos)/2*3)`，即 causal 正:负为 **2:3**。 citeturn29view1 fileciteturn25file0 这不改变 test scorer，但会改变训练数据，因此在“完全复现论文方法”层面必须记为 unresolved，而不能自行选择其一。

## Repository execution audit

**MAVEN-ERE 官方仓库是目前唯一真正具备数据 schema、关系 baseline、prediction dump 和官方 scorer 全链条的核心资产。** HEAD 为 `ac81a971...`，tree 中可见 `evaluate.py`、`causal/main.py`、`causal/src/data.py`、`causal/src/dump_result.py`、下载脚本等。`causal/main.py` 的 imports 指向仓库内本地模块，读取 `../data/MAVEN_ERE/{train,valid,test}.jsonl`，用 `roberta-base`、max length 256，在 train 上优化、valid 选 best，再对 test dump submission。 fileciteturn4file0 fileciteturn44file0

它的缺口并不是代码，而是 **A 轴 test reference**。官方 README 明说 test annotation 不公开。也就是说：

| 性质 | 状态 |
|---|---|
| 官方数据下载入口存在 | **YES** |
| public `train/valid` gold 可见 | **YES** |
| public `test` input 可见 | **YES** |
| hidden test gold 本地可见 | **NO** |
| 官方 `evaluate.py` 本地代码可见 | **YES** |
| 使用 public valid 做 causal-only local scoring | **YES** |
| 使用 official hidden test 做 causal local scoring | **NO** |
| CodaLab competition 页面存在 | **YES** |
| 2026-08-26 已实证登录→提交→scorer 返回 | **本审计未验证** |

官方 CodaLab URL：`https://codalab.lisn.upsaclay.fr/competitions/8691`。只看到 competition page 或 “Ends: Never” 不满足你的提交可用性标准；本审计没有完成一次 authenticated submission round-trip，因此这里必须写“未验证”，而不是“仍可用”。即便该 round-trip 后续成功，A 仍然无法满足“所有 gold 本地可得”的主协议标准，因为 CodaLab 远程 scorer 并不会公开 hidden gold。

**Chen / Teach-LLM-LR** 的情况正相反：repo 存在，但只是论文推理实验的一部分，而非 benchmark reproduction package。HEAD `58de425c...` 的 tree 有 `cached_prompts/`、`evaluate_maven.py`、`evaluate_ctb.py`、`logic_rules/`、`src/data.py`、`src/utils.py` 等，却没有 8:2 split generator、document manifest、raw→cached-prompt conversion command、完整 model-training entrypoint 或官方 MAVEN prediction dumper。 fileciteturn13file0 README 的公开主命令就是直接运行 `evaluate_maven.py`。 fileciteturn14file0

而且 Chen 的 local open-model 配置写死了作者机器路径，例如 `/cpfs01/shared/.../Llama-2-13b-hf` 和 Vicuna-13B，加载路径用 FP16 `device_map="auto"`；默认模型则是 GPT-4/API 类路径。 fileciteturn15file0 这类绝对路径可以手工替换成本地 HuggingFace 路径，但那只能解决模型定位，**不能补回 unpublished split/cache-generation pipeline**。如果为了“让 Chen 成为 B all-pair causal baseline”重新写 pair generator 和 official scorer adapter，就已经从修补转成了**重新定义/重实现 baseline**。

**Wei / LLM-ERE** 比 Chen 完整。HEAD `2f1d5c4d...` 的 tree 包含从 MAVEN-ERE 继承的 supervised causal code、官方 `evaluate.py`，以及 `llm/` 下的 GPT/Llama scripts、post-processing 和 evaluator；README 给出了 Llama2 inference、fine-tuning、post-process、evaluate 命令。 fileciteturn46file0 fileciteturn49file0 但这个包执行的是 **A hidden test setting**；生成 prediction 是公开的，最终 whole-test reference 不是。因此它可以做 train/inference reproducibility audit，却不能做“完全本地最终 causal F1 audit”。

**LLMERE** 对 B 的数据和 evaluator 反而提供了非常重要的资产：`split_data.py` 把 seed 42 与 8:2 操作写死，`convert_causal.py` 把 gold event-level relation 展开到 mentions，`eval/MAVEN_ERE/eval_causal.py` 提供 causal-only micro scorer。 fileciteturn21file0 fileciteturn23file0 fileciteturn26file0 但仓库 root/README 没有完整 LLaMA-Factory training / inference execution package，README 甚至只有论文链接；因此不能把“有 preprocess/eval/output”误写成“完整复现包”。 fileciteturn51file0 fileciteturn52file0

所以 LLMERE 目前更适合充当 **B 轴协议定义参考实现**，而不是满足你门槛的“可从 raw 一键/明确命令链重训到最终 F1 的 baseline”。

**Xiang / GLM4ECI** 是最明确的代码—论文 task mismatch。repo HEAD `742f3110...` 的完整 tree 只有 README 与若干 Python 文件；没有 MAVEN JSONL、conversion、split manifest、requirements、MAVEN evaluator。 fileciteturn35file0 更决定性的是 `load_data.py`：

```text
data = np.load('train.npy', allow_pickle=True).item()
...
if topic != '37' and topic != '41':
...
fold1 ... fold5
...
dev_data = data['37'] + data['41']
```

这是一条 topic/fold 型 ECI pipeline，而不是 MAVEN-ERE original train/dev JSONL 的 C split。 fileciteturn37file0 repo history 本审计看到的提交量极少，当前/已检查历史中未取得曾经存在而后来删除的 MAVEN implementation；严谨表述应是“**未取得 MAVEN 实现**”，不是断言作者从未写过。

**KnowQA / TacoERE / MMD-ERE** 均不能进入当前“公开可执行对手”集合。KnowQA 论文曾公开 repo URL，但审计日地址未取得；TacoERE/MMD-ERE 则在本轮一手仓库检索中未取得作者代码。对于这三者，“有论文”“有 reported F1”“有方法描述”均不等于 raw→preprocess→train→predict→evaluate 闭环。

## Independent-team compatibility, baseline recommendation, and 27GB feasibility

### 独立团队与协议兼容矩阵

| 方法 | 2024–26 正式论文 | 与 MAVEN 原团队独立 | 当前作者代码可得 | 轴 | 与同轴第二方法真正同 pair/evaluator | 可计入“两独立 baseline” |
|---|---|---|---|---|---|---|
| Chen 2024 | YES | **YES** | 部分代码 YES | B-like | **NO**：与 LLMERE pair universe/evaluator 不同 | **NO** |
| Wei 2024 | YES | **YES** | YES | A | A 本身 hidden gold 不本地 | **NO** |
| TacoERE 2024 | YES | **NO** | **未取得** | A + D | — | **NO** |
| KnowQA 2024 | YES | **NO** | 当前未取得 | D | — | **NO** |
| LLMERE 2025 | YES | **YES** | 部分代码 YES | B | Chen 不兼容；自身 training closure 不全 | **NO** |
| MMD-ERE 2025 | YES | **NO** | **未取得** | D | — | **NO** |
| Xiang 2025 | YES | **YES** | YES，但 **MAVEN code absent** | C | 未找到第二同轴方法 | **NO** |

因此，**本报告无法按你的标准推荐两个 baseline**。

最容易产生误判的是 **Chen + LLMERE**。作者团队确实独立，年份也合格，论文都写了 8:2/original-valid-as-test；但这三点还不够。Chen 的候选样本是 sentence-level 且去掉 fully relationless pairs；LLMERE causal scorer 是 document-level all ordered gold mention pairs。Chen 没有公开 exact split seed/manifest；LLMERE 是 seed 42。因此把两篇表格并列成 “B 轴两个 baseline”会违反你本轮最核心的“不得混 setting / pair universe”的要求。 citeturn27view0turn29view5 fileciteturn21file0 fileciteturn26file0

第二个可能的误判是 **Wei + TacoERE**。两篇都可以在论文层面归到 official split A，但 A 的 hidden gold 本地不可得；TacoERE 又与 MAVEN 原团队重叠且公开代码未取得。因此也不能构成“两个独立、完全公开本地 baseline”。

第三个误判是 **Xiang + 任一 MAVEN causal 方法**。Xiang 的 C 轴 split 与 A/B 都不同，而且作者公开 repo 当前没有 MAVEN execution path；绝不能拿其分数与 Chen、LLMERE、Wei、TacoERE 表格直接比较。

### 27GB 审计

| 方法 | 论文硬件证据 | repo 静态证据 | 单张约27GB结论 |
|---|---|---|---|
| **Official RoBERTa 2022 sanity** | 已核验材料未给出可用于精确显存审计的 GPU 型号 | RoBERTa-base, max256, batch4，传统 encoder classifier。 fileciteturn43file0turn44file0 | 工程上风险低，但它是 **2022 sanity**，不能补近期对手门槛。 |
| **Chen** | RoBERTa-Large 单 V100；LLM LoRA 在 **A100 80GB**。 citeturn27view3turn27view4 | Vicuna/Llama2-13B 以 FP16 load，max length4096；默认还依赖 GPT API。 fileciteturn15file0 | **FAIL**。没有公开的论文级 27GB 13B 路径；改 4-bit 等属于另行重构，不可算 published path。 |
| **Wei** | 论文未声明 GPU 型号/显存；Llama2-7B SFT 使用 4-bit + LoRA rank64，3 epochs。 citeturn25view0 | README 单进程 `torchrun`, max seq4096/max batch6；SFT script公开。 fileciteturn49file0 | **CONDITIONAL only**。不能以“7B 4bit通常能装”直接判 PASS；需要一次真实单27GB GPU smoke。且 A hidden gold 仍独立 FAIL。 |
| **TacoERE PLM** | **2× RTX 3090** training/testing。 citeturn28view3 | 作者 repo 未取得。 | **FAIL**：论文没有单卡路径。 |
| **KnowQA** | 本审计未取得足以冻结的当前运行包/硬件配置 | repo 当前未取得 | **FAIL / 未证明**。 |
| **LLMERE** | **1× A100 40GB**，LLaMA2-7B/LLaMA3-8B、LoRA rank64、max2048。 citeturn29view1turn29view2 | 发布 repo 没有完整 trainer/inference/config package。 | **FAIL / 未证明**。A10040 “跑过”不等于27GB PASS；没有可执行 27GB 配置可 smoke。 |
| **MMD-ERE** | sampled multi-agent LLM setting | 作者 repo 未取得 | **FAIL / 未证明**，且本地闭源 API 限制不满足目标。 |
| **Xiang** | 论文称单 “GTX 3090”，BART-base/Llama-160M、batch16。 | 当前 repo 确有小模型代码，但不是 MAVEN pipeline。 fileciteturn37file0 | **算力层面较低风险，benchmark 层面 FAIL**；不能把 ESC code 的显存可行性移植成 MAVEN execution evidence。 |

因此即使暂时忽略协议问题，**也没有两个合格 baseline 同时达到“公开闭环 + 可信单27GB”**。Chen/TacoERE 明确不合；LLMERE 只有 A10040 paper run 且缺 trainer；Wei 的 7B 4-bit 最多是待 smoke 的 conditional，但它在 A hidden-test；Xiang 算力最轻，却没有 MAVEN code。

### Go / No-Go gates

以“目前最有希望的 **B 轴**”作为候选主协议进行最终门槛判断：

| 门槛 | 状态 | 审计理由 |
|---|---|---|
| **公开协议** | **CONDITIONAL** | LLMERE-defined B 可以使用全部公开 gold：official train 做8:2、original valid 作 test；因此从数据可见性上比 A 好。但不能把它称为“Chen 与 LLMERE 已共享验证过的同一 protocol”，因为 pair universe 不同。 |
| **Split** | **CONDITIONAL** | LLMERE 有 exact `random.seed(42)` split script；但当前审计环境没有成功下载官方 v1.0 文件并生成 document-ID manifest/SHA-256，Chen 又未公开自己的 seed/manifest。 fileciteturn21file0 |
| **Pair / labels** | **PASS for LLMERE-defined B; FAIL as Chen+LLMERE shared protocol** | LLMERE code可以锁定 all ordered mention pairs、`NONE/PRECONDITION/CAUSE`；Chen 是不同 candidate universe。 fileciteturn26file0turn27file0 |
| **Evaluator** | **PASS for LLMERE-defined B** | `eval/MAVEN_ERE/eval_causal.py` 能从 predictions 到 causal micro positive P/R/F1，语义与官方 scorer 核心一致。 fileciteturn26file0 |
| **两个独立近期对手** | **FAIL** | 截至本审计范围，B 只有 LLMERE 可提供明确 all-pair causal protocol；Chen 不能作为同 evaluator/pair universe 的第二个 baseline，且 LLMERE 自身 training closure 也不完整。 |
| **单张约27GB** | **FAIL** | 即便把 Chen/LLMERE勉强当候选，Chen published 13B LoRA path 是 A10080；LLMERE 是 A10040 且未发布完整 27GB trainer path。 |

**最终判定：`NO-GO`。**

这不是 `CONDITIONAL GO`，因为剩余问题绝不只是“一次 CPU smoke 或最小 GPU smoke”。真正的失败项——**第二个独立同轴公开 baseline 不存在于当前已取得资产中，以及 Chen/LLMERE pair protocol 不同**——不能靠一次运行解决。

## Unverified items, minimum local checks, and primary sources

下列项目在本轮没有被伪装成“已验证”。

首先，**官方 MAVEN-ERE v1.0 文件 SHA-256 未取得**。原因是当前执行环境未能成功落盘 Tsinghua Cloud ZIP，因此没有计算 `train.jsonl / valid.jsonl / test.jsonl` 的 SHA-256，也没有用实际 JSONL 重算 2913/710/857、73939/17780/20557 和 36316/9698/11978。论文 Table 15 已给出这些统计，但“paper statistic”与“本地 checksum 后重新统计”应继续区分。 citeturn22view0

第二，**CodaLab 当前提交闭环未验证**。competition page 的存在不等价于新 submission 能返回 scorer。一次真实的 authenticated smoke 能回答“2026 年远程 leaderboard/scorer 是否还活着”，但即便结果为 YES，也不会使 A 变为本地完全可审计，因为 hidden gold 仍未公开。

第三，**Chen 的 exact 8:2 document split 未核实**。论文只给比例；repo 没有生成器/manifest。`evaluate_maven.py --seed 42` 不能被倒推为 dataset split seed。一个最小 CPU audit 可以把 Chen 的 cached IDs 映射回 official doc IDs，再与 LLMERE seed-42 manifest 比较，但即使比较结果完全相同，**Chen 与 LLMERE 的 pair universe 仍不相同**，所以这项检查不能把当前 NO-GO 翻成 GO。

第四，**LLMERE 的协议层面值得做一次 CPU smoke**：用官方 v1.0 `train.jsonl` 跑 `split_data.py`，导出 train/dev document-ID manifests 和 SHA-256；再用 repo 已提供的 causal prediction/output 跑 `eval/MAVEN_ERE/eval_causal.py`，确认 scorer 的 P/R/F1 与预期一致。这可以把 B 的 protocol/split/evaluator 三项从 conditional 锁成 PASS，但仍不能制造第二个独立 baseline。对应源：`https://github.com/HerbertHu/LLMERE/blob/94d4ef2781ec7e071d38ac7fd8632a8fffbda798/data_handle_MAVEN_ERE/split_data.py` 和 `https://github.com/HerbertHu/LLMERE/blob/94d4ef2781ec7e071d38ac7fd8632a8fffbda798/eval/MAVEN_ERE/eval_causal.py`。 fileciteturn21file0 fileciteturn26file0

第五，**27GB GPU smoke 当前没有必要优先于 baseline discovery**。Wei 的 Llama2-7B 4-bit 路径可以通过最小 GPU smoke验证显存，但它属于 A；Xiang 的模型很小，却缺 MAVEN code；LLMERE 缺完整 training/inference package；Chen published local route 是13B FP16/A10080级设置。只验证其中一个“能装进27GB”，不会解决同轴双 baseline 门槛。

因此，“下一阶段最小动作”的优先级只有一个合理排序：**先冻结 LLMERE-defined B 的文件 checksum + split manifest + causal evaluator；然后只有在找到第二篇真正对该 exact B protocol 发布了可执行代码的方法时，才值得做 GPU smoke。** 在找到第二个方法之前，不应把任何 A/C/D 分数移进 B 表格。

### 一手来源清单

**MAVEN-ERE 正式论文**

`https://aclanthology.org/2022.emnlp-main.60/`  
`https://aclanthology.org/2022.emnlp-main.60.pdf`  
DOI: `https://doi.org/10.18653/v1/2022.emnlp-main.60`  
官方仓库：`https://github.com/THU-KEG/MAVEN-ERE`  
官方 causal README：`https://github.com/THU-KEG/MAVEN-ERE/blob/ac81a9711a69f43f55bfbc50b3bb573fd11c64b0/causal/README.md`  
官方 causal data code：`https://github.com/THU-KEG/MAVEN-ERE/blob/ac81a9711a69f43f55bfbc50b3bb573fd11c64b0/causal/src/data.py`  
官方 evaluator：`https://github.com/THU-KEG/MAVEN-ERE/blob/ac81a9711a69f43f55bfbc50b3bb573fd11c64b0/evaluate.py`  
官方 CodaLab：`https://codalab.lisn.upsaclay.fr/competitions/8691`

**Chen et al. 2024**

`https://aclanthology.org/2024.acl-long.512/`  
`https://aclanthology.org/2024.acl-long.512.pdf`  
DOI: `https://doi.org/10.18653/v1/2024.acl-long.512`  
作者仓库：`https://github.com/chenmeiqii/Teach-LLM-LR`  
审计 commit：`https://github.com/chenmeiqii/Teach-LLM-LR/commit/58de425c88ccb4d98aaaf0f8ad24a4c2ba066dfb`

**Wei et al. 2024**

`https://aclanthology.org/2024.findings-emnlp.1/`  
`https://aclanthology.org/2024.findings-emnlp.1.pdf`  
DOI: `https://doi.org/10.18653/v1/2024.findings-emnlp.1`  
作者仓库：`https://github.com/WeiKangda/LLM-ERE`  
审计 commit：`https://github.com/WeiKangda/LLM-ERE/commit/2f1d5c4d6b2986f1daaaa142c7024a7d00ebafd8`

**TacoERE**

`https://aclanthology.org/2024.lrec-main.1348/`  
`https://aclanthology.org/2024.lrec-main.1348.pdf`  
ACL Anthology 未列 DOI。作者官方复现仓库截至本审计未取得。

**KnowQA**

`https://aclanthology.org/2024.findings-emnlp.986/`  
`https://aclanthology.org/2024.findings-emnlp.986.pdf`  
DOI: `https://doi.org/10.18653/v1/2024.findings-emnlp.986`  
论文给出的代码地址：`https://github.com/du-nlp-lab/KnowQA`；审计日当前未取得。

**LLMERE**

`https://aclanthology.org/2025.coling-main.500/`  
`https://aclanthology.org/2025.coling-main.500.pdf`  
ACL Anthology 未列 DOI。  
作者仓库：`https://github.com/HerbertHu/LLMERE`  
审计 commit：`https://github.com/HerbertHu/LLMERE/commit/94d4ef2781ec7e071d38ac7fd8632a8fffbda798`

**MMD-ERE**

`https://aclanthology.org/2025.coling-main.460/`  
`https://aclanthology.org/2025.coling-main.460.pdf`  
ACL Anthology 未列 DOI。作者官方复现仓库截至本审计未取得。

**Xiang et al. directional ECI**

`https://aclanthology.org/2025.findings-acl.43/`  
`https://aclanthology.org/2025.findings-acl.43.pdf`  
DOI: `https://doi.org/10.18653/v1/2025.findings-acl.43`  
作者仓库：`https://github.com/zhanchuanhong/GLM4ECI`  
审计 commit：`https://github.com/zhanchuanhong/GLM4ECI/commit/742f311094b1d87e126364a531a883d292d0b25e`

**最终审计口径冻结为一句话：MAVEN-ERE 的公开 causal 数据/evaluator 足以冻结一个本地 benchmark；LLMERE 甚至足以把 B 轴 split/evaluator 基本写死，但截至 2026-08-26，仍没有两个独立的 2024–2026 正式方法在同一公开 B protocol 上提供可执行闭环，A 又受 hidden gold 限制，C 又缺 split/code 闭环。因此，作为硕士论文主指标协议，当前严格结论仍是 `NO-GO`。**