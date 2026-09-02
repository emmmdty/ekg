# 配置状态

当前 v6 phase 的命令、配置身份和哈希只以对应 phase 契约及 stage bundle 为准。本目录不是任务队列，
不得因为某个 YAML 存在就启动实验。

| 配置 | 状态 |
|---|---|
| `relations/heuristic_baseline.yaml` | CPU 功能性基线样例 |
| `relations/supervised*.yaml` | 历史 Phase A/B 兼容；旧 checkpoint 结构限制见 `docs/ENGINEERING_NOTES.md` |
| `relations/ablation_no_{consistency,grounding,edge_admission}.yaml`、`crc_edge_admission.yaml` | 历史 v4 消融/诊断，不进入 v6 主线 |
| `relations/llm*.yaml` | 旧 LLM 抽取入口，不进入 v6 主线 |
| `relations/ccks_causal_zh.yaml` | 旧中文金融旁证，不进入 v6 主线 |

原 multi-agent YAML 会被普通 `RelationPipeline` 静默解析成同一配置，已删除。现在普通 pipeline 遇到
`relations.mode: multi_agent` 会直接报错，避免消融名义与实际执行不一致。
