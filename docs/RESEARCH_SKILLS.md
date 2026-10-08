# 本项目的科研执行 skills

2026-10-08，按作者“检索 GitHub，有用就加载进项目”的授权安装。安装在项目 `.agents/skills/`，
没有改全局环境、安装依赖或接入第三方模型服务。完整文件 SHA-256 见
[`research_skills.lock.json`](research_skills.lock.json)；上游原文未改，每个目录补存 MIT 许可。

| Skill | 固定上游 | 用途与本轮实际应用 |
|---|---|---|
| scientific-critical-thinking | [K-Dense](https://github.com/K-Dense-AI/scientific-agent-skills/tree/92ace75ac21efe19a620434e0ca4e356081fe807/skills/scientific-critical-thinking) | 分开缺失报告、协议障碍和效果失败；C-35 将 base-logit 导数与共享参数梯度分开，不用前者替代后者 |
| hypothesis-generation | [K-Dense](https://github.com/K-Dense-AI/scientific-agent-skills/tree/92ace75ac21efe19a620434e0ca4e356081fe807/skills/hypothesis-generation) | 为各章记录竞争解释、证伪条件与不确定结果；使用本地 prediction/rival matrix validator 检查诊断设计结构 |
| systematic-debugging | [Superpowers](https://github.com/obra/superpowers/tree/8ca22dba9a94f28898bbce59f2537ff4d87c747d/skills/systematic-debugging) | 先重放错误再修复：定位 A4 gold 副本截断，按冻结 hash 恢复；不把读盘失败写成模型失败 |
| test-driven-development | [Superpowers](https://github.com/obra/superpowers/tree/8ca22dba9a94f28898bbce59f2537ff4d87c747d/skills/test-driven-development) | 为错误交换计数、错误 subtype 和缺失文档先写失败测试；torch 梯度测试需在服务器实跑 |
| verification-before-completion | [Superpowers](https://github.com/obra/superpowers/tree/8ca22dba9a94f28898bbce59f2537ff4d87c747d/skills/verification-before-completion) | 完成声明绑定新输出、hash 和三件套；本地 torch skip 不算远端通过 |

另检索了 Orchestra-Research/AI-Research-SKILLs、Toadoum/ai-research-skill。
本轮不安装整个合集：分布式大模型训练、完整论文写作流程不对准当前根因；已有 R1 检索 skill 保留。
K-Dense 仓库整包下载停滞后，停止该下载，用官方 installer 的 sparse git 模式成功安装指定两个目录。
许可查询遇到 GitHub API rate limit，改读同 revision 的 raw LICENSE；未把工具失败当作仓库无许可。

使用按需加载；当前会话已直接读取上述五份 SKILL.md 与调试/TDD/tool_reference 所需引用。
新会话从 `HANDOFF.md` 和此页进入，按任务读取本地 SKILL.md，无需再次安装。

## 与项目授权的关系

作者在 2026-10-08 已明确委托科研路线选择与裁决；项目有效性规则优先于通用 skill。
`hypothesis-generation` 的 “never automatically ... select ... scientific hypotheses” 和
`systematic-debugging` 的多次失败后再找人选择架构，是通用的人类裁决建议。
本项目按作者委托由执行代理作有证据的科研选择，记录理由和可证伪预期，**不再向作者索要科研选题**。
schema/lint 的 PASS 仅代表结构检查，不代表方法有效或有新颖性。
通用技能不得恢复已撤销的统计家族、强制写论文、触发子代理、上传未发表数据、扩 backbone、
使用 final-valid 或启动未授权 seeds/5090/跨机 checkpoint 传输。

## 重装

使用 Codex 自带 installer，固定 revision，`--dest "$PWD/.agents/skills"`。
目录已存在时不要覆盖；按 lock 校验即可。

```bash
uv run python /home/tjk/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo K-Dense-AI/scientific-agent-skills --ref 92ace75ac21efe19a620434e0ca4e356081fe807 \
  --path skills/scientific-critical-thinking skills/hypothesis-generation \
  --dest "$PWD/.agents/skills" --method git
uv run python /home/tjk/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo obra/superpowers --ref 8ca22dba9a94f28898bbce59f2537ff4d87c747d \
  --path skills/systematic-debugging skills/test-driven-development skills/verification-before-completion \
  --dest "$PWD/.agents/skills" --method git
```

软件来源：Kassis, Agarwal, He, Patel, Brueckner (2026),
[Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents](https://arxiv.org/abs/2609.00065v2)。
该文没有 task-level 效果评测；本项目不声称安装 skills 已提高实验指标。
