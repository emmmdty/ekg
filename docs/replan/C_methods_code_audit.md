# DR-C 本地交叉核验

> 核验日期：2026-08-25（Asia/Taipei）
>
> 原始报告：`docs/replan/C_methods_code.md`
>
> 来源导出：`docs/replan/C_methods_code.pdf`

## 结论

DR-C 可作为后续调研输入，但必须带着本文件的证据降级和仓库更正使用。本轮验收状态为：
**有条件通过**。

报告最有价值的结论不是“某个 7B LLM 已经成为可直接采用的章节方案”，而是把方法边界分清：
direct prompting、监督 PEFT、LLM→SLM hybrid、cascade、RAG 和 true multi-agent 不能混报。现有一手证据
支持“直接提示通常落后监督模型，监督适配或混合流程可能改善”的方向性判断；但 TextEE、LLMERE、
CGEL 等证据分别存在 sampled protocol、split/baseline 来源、公开复现包不完整等限制，不能一律标成
严格公开主轴。

原始报告不修改；下列更正覆盖其证据等级和 GitHub 表。C 只定义可行的方法/工程包络，不替代 B/D
对公开 benchmark、竞争密度和研究问题价值的判断。

## PDF 来源恢复

- Markdown 共 326 行，保留 100 个 ChatGPT 内部 citation token，并含 10 个原始 URL。
- PDF 共 19 页，由 WeasyPrint 生成，有可搜索文本层；含 171 个 URI 注释、25 个唯一 URI，剔除
  ChatGPT 首页后可恢复 24 个真实 Web 来源。
- 表格正文以 Markdown 为准，论文/仓库链接由 PDF 注释恢复；不需要重跑或重新导出 DR-C。

## 方法分类核验

| 原报告分类 | 核验结果 | 后续允许的表述 |
|---|---|---|
| TextEE / Wei et al. 的 direct prompting | **分类确认** | 可作为 direct LLM 相对监督模型落后的反证，但必须逐项保留其 test/sampling 边界。 |
| LLMERE 的 LoRA/rationale | **分类确认** | 是监督 PEFT 正例；不能因模型为 8B 就推断其论文 recipe 已在 27GB 卡验证。 |
| SECURE 的 GPT-4→SLM | **分类确认** | 是 hybrid，不是 direct prompting；可作为严格同代码评测的混合方法正例。 |
| CALLMSAE | **分类确认** | 是多阶段 cascade；不得因包含多个模块就称 true multi-agent。 |
| EventRAG | **分类确认** | 是 graph→RAG；其仓库缺派生数据/evaluator，不能当成一键复现基线。 |
| TAG-EQA | **分类确认** | 是单模型多 prompt 的图问答流程，不是多智能体建图。 |
| CGEL / MMD-ERE | **分类确认** | 属 true multi-agent 方法实例；目前只足以证明范式存在，不足以证明成熟可复现 benchmark。 |

## 高影响实验证据核验

| DR-C 证据 | 核验结果 | 必须保留的边界 |
|---|---|---|
| TextEE Tables 6–7：direct LLM 明显落后监督方法 | **同论文趋势确认，A 级需降级** | 论文因 API 成本对每个数据集 sampled 250 documents，并省略 SPEED/MUC-4；未锁定抽样 seed/所属 split，也未声明表中 F1 的 micro/macro 聚合。可引用同表巨大差距，不得称“严格公开主指标”。 |
| Wei et al.：MAVEN-ERE official test 上 direct LLM 落后 RoBERTa | **确认** | 这是目前 direct LLM 反证中口径较强的一项；必须与 valid-as-test 或 sampled setting 分表。 |
| LLMERE Table 2：52.5 高于 ProtoERE 50.8 | **论文内部正证据确认，严格性有限** | Appendix C 采用 train 8:2、original valid 作 test；正文没有锁定 ProtoERE 是否在该 split 重跑，也未指定可执行 evaluator/commit。不能升级为完全公开可复现主轴。 |
| SECURE：GPT-4 summary + RoBERTa 优于复现 RoBERTa，direct GPT-4 更差 | **严格正证据确认** | ECB+/GVC/FCC 的同表、同 scorer 结果支持 hybrid 的价值；它证明的是特定 hybrid，不证明 direct LLM 或任意 cascade 有效。 |
| CGEL Table 1 的多智能体消融 | **内部消融确认，外部可比性不足** | 论文未声明可核的 train/dev/test，代码链接当前 404，且使用 GPT-4o 与 Llama-3.1-70B；不能作为 27GB 单卡候选或成熟公开主轴。 |
| MMD-ERE 是 true multi-agent ERE | **正式论文身份确认，其余降为未取得** | ACL 页面可确认 COLING 2025 发表和作者；未取得官方代码、完整硬件 recipe 或可执行 evaluator。作者与 MAVEN-ERE 原团队重叠，不能计作独立团队。 |

## GitHub 快照更正

以下为 2026-08-25 对官方仓库 API 与 `git ls-remote` 的快照。star 与 `pushed_at` 是动态信号，
不能当论文证据；HEAD 只证明当时仓库状态，不证明论文 recipe 可运行。

| 项目 | 当前 HEAD | 动态/许可快照 | 可复现性边界 |
|---|---|---|---|
| TextEE | `567baa9bf8461daf9d53c8afc5bbf3938b365dd3` | 61★；Apache-2.0 | 统一框架可用；LLM 250-document 表仍有 protocol 缺口。 |
| OmniEvent | `ec72e72763f191c577ea92f4c70b4172f604cbac` | 410★；MIT | 原报告 SHA `130efae…` 已过时或错配；是通用工具箱，不是单个新方法的复现证明。 |
| DeepKE | `77083bf1d9ccc386c02d5b7643f4f4d2251f4c30` | 4471★；MIT | 通用 IE 工具箱；不能替代具体论文的 split/evaluator 审计。 |
| MAVEN-ERE | `ac81a9711a69f43f55bfbc50b3bb573fd11c64b0` | 92★；GPL-3.0 | 官方数据/evaluator 资产有残值；CodaLab 新提交能力仍未实测。 |
| SECURE | `f1f532753be49a6ccd17c949dc6b3b561c971d02` | 12★；GPL-3.0 | 同代码 scorer 的 hybrid 证据可用。 |
| SeDGPL | `265b19b69856428a63819c809572865b5faebf3f` | 5★；未声明 license | 缺 MAVEN 派生文件与构图入口，不是一键完整复现包。 |
| CGEL | 无 | 论文给出的仓库 API 返回 404 | 不能按开源方法处理。 |
| CALLMSAE | `4a0f093ecedfdb136a12c82a82a534084f662fca` | 4★；GPL-3.0；最后 push 2025-02-02 | 原报告的 2★/2026-07-03 不准确；缺 HGS evaluator，完整 train 文本受 NYT 许可约束。 |
| EventRAG | `96a9de960bf4939c7b2d6e7350c5bbc95232517e` | 21★；未声明 license；最后 push 2025-02-16 | 原报告日期不准确；脚本引用未发布的 `RAG-Data`，缺 questions/outputs/evaluator。 |
| TAG-EQA | `fa3b0b9ae8211da07e14ae344b0471d741c4feee` | 0★；未声明 license；最后 push 2025-11-09 | 原报告 star/日期不准确；缺主数据、固定 test IDs 和 outputs。 |
| InstructUIE | `052a536abf9a01aa6bce1982fac2e803395e5f5c` | 396★；MIT | 是 arXiv-only 前序工作，不得替代正式发表方法的证据等级。 |
| LLMERE | `94d4ef2781ec7e071d38ac7fd8632a8fffbda798` | 9★；MIT；最后 push 2025-02-01 | 原报告 GitHub 表漏项；有转换脚本、evaluator 和示例结果，但缺训练入口、环境锁与 checkpoint。 |

## 27GB 单卡边界

DR-C 在这一项总体克制，可以保留为工程候选排序：encoder/seq2seq 监督方法风险最低；7B/8B 的
LoRA/QLoRA 或 hybrid 值得后续做显存探针；70B、多闭源 API 协同和未发布数据链路不适合作为本项目
主复现路径。

但必须补两条限制：

1. LLMERE 论文使用 A100 40GB、LoRA rank 64、max length 2048；这不是 27GB 实测证明。
2. “7B 4-bit 通常可放入 27GB”只说明候选模型权重可能装得下，不等于完整训练峰值、长序列、优化器、
   evaluator 和数据流程均可运行。方向确定后仍需做小批量显存 smoke test。

本轮未运行 GPU，未启动训练，也未把估算值写成实测值。

## 覆盖缺口与允许用途

- IEPile、ADELIE、KnowCoder、KnowCoder-X、ASEE 的标题、正式发表 venue 与年份已由 ACL Anthology
  核实；但 DR-C 对它们仅有简短方法行，没有形成 split、主表、代码 commit、硬件与复现命令的完整
  审计。因此它们可进入 D/E 的候选池，不能单独支撑最终章方向。
- TextEE 更适合作为统一实验基础设施候选，而不是一个 benchmark 结论。其包含的 ACE/RichERE 等
  非开放数据不能自动满足本项目“公开可比主指标”硬约束，最终只能选择经 B/D 再核的公开子集。
- C 没有证明某个方法已同时满足“公开数据 + 固定 test + 多个近年对手 + 统一 evaluator + 27GB 实测”。
  后续综合必须将方法可行性与 benchmark 成熟度相交，而不是从 C 单路直接选章。

## 可交给 DR-D 的稳定输入

- 将 direct prompting、监督 PEFT、hybrid、cascade、RAG、true multi-agent 分开比较，禁止统称
  “LLM 方法”。
- 对每个跨语言/风险候选，优先寻找公开 test、固定 evaluator、至少两个独立正式对手；方法新颖性和
  社会价值不得替代这些硬证据。
- 资源上优先考虑 encoder/seq2seq 与可做 27GB 显存探针的 7B/8B PEFT/hybrid；排除依赖 70B、
  多闭源 API、缺数据或缺 evaluator 才能复现的主路线。
- MAVEN-ERE 的 hidden test、valid-as-test、sampled setting 和 causal-only setting 必须继续分表。

## 一手来源入口

- [TextEE](https://aclanthology.org/2024.findings-acl.760/)
- [Wei et al. 的 LLM 事件关系评测](https://aclanthology.org/2024.findings-emnlp.1/)
- [LLMERE](https://aclanthology.org/2025.coling-main.500/)
- [SECURE](https://aclanthology.org/2024.acl-long.164/)
- [CGEL](https://aclanthology.org/2025.acl-long.1269/)
- [MMD-ERE](https://aclanthology.org/2025.coling-main.460/)
- [IEPile](https://aclanthology.org/2024.acl-short.13/)
- [ADELIE](https://aclanthology.org/2024.emnlp-main.419/)
- [KnowCoder](https://aclanthology.org/2024.acl-long.475/)
- [KnowCoder-X](https://aclanthology.org/2025.findings-acl.748/)
- [ASEE](https://aclanthology.org/2025.findings-emnlp.419/)

## 验收边界

本轮没有在 GPU 上复现训练，没有真实运行全部仓库，也没有穷尽每个通用 IE 方法在每个事件子任务上的
主表。MMD-ERE PDF 连续下载未完整落地后已停止重复请求，以免无效消耗；其代码/硬件结论保持未取得。
这些缺口不妨碍把 C 作为“方法范式与工程候选”的有条件输入，但会阻止任何“某 7B 方法已在 27GB
验证”“CGEL/MMD-ERE 已具成熟复现包”或“TextEE sampled 表就是公开严格主轴”的强结论。
