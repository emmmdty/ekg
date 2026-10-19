# 本项目的科研执行 skills

## 2026-10-19：以自主实验研究为目标的执行入口

作者明确：需要AI自主完成论文实验，在指标失败时自己检索、验证方法、寻找baseline、
推进有深度且满足既定毕业要求的研究；不是让作者学习工具或亲自补科研决策。
新的项目入口为[ekg-research-loop](../.agents/skills/ekg-research-loop/SKILL.md)。它改变
执行决策与失败后的接续方式，复用现有R1、主表、实验脚本与验收门，不新增一套研究框架。

本次直接检查官方GitHub README及关键源文件；下面的“采用”只指工作流借鉴，未安装、
启动或在MAVEN上验证这些框架。没有新API消费、后台任务、模型上传或GPU实验。

| 项目/核查入口 | 查到的真实能力 | 本项目选择与限制 |
|---|---|---|
| [Microsoft RD-Agent](https://github.com/microsoft/RD-Agent/tree/484776c211e4fbbeef03e0ec00d6bbee7362a4f4) | `rdagent/scenarios/data_science/loop.py`连接proposal、coding、running、feedback和trace；`dev/feedback.py`比较当前/既有最佳结果及代码diff | 借鉴按实验反馈决策。当前反馈实现明确说明部分observations/hypothesis字段不用于框架控制；不能把生成分析文字视为研究方向已改变。`general_model.py`从PDF提取并实现模型，但不等于自动完成MAVEN同协议复现。现有训练链已具备，不整体迁移到竞赛场景 |
| [HKUDS AI-Researcher](https://github.com/HKUDS/AI-Researcher) | `research_agent/run_infer_idea.py`实际调用论文/代码搜索、survey、prepare、plan、ML、judge、experiment analyser；README区分给定想法与参考论文驱动的任务 | 最接近检索→想法→实现→实验分析。可借鉴职责分工，但同框架多个角色不自动等于独立科学审稿；原生要求Docker/API并使用自有实验流程，不能原样接管冻结协议。未实跑；一次完整tree API读取中断，未据此判仓库不可运行，已直接核关键源码 |
| [Orchestra autoresearch](https://github.com/Orchestra-Research/AI-Research-SKILLs/blob/773a52944ba4747a18bd4ae9ade53fff041adcbc/0-autoresearch-skill/SKILL.md) | 内环执行假设/实验/测量，外环综合结果/找解释/重新检索/改方向；另有`21-research-ideation`两项技能 | 采用双循环与失败触发检索。原入口强制continuity loop、新状态目录、最终论文写作，并允许以连贯负结果结束；这些不适配本项目现有队列/阶段停止/正向方法验收。没有全装、执行上游指令或创建新定时器 |
| [Karpathy autoresearch](https://github.com/karpathy/autoresearch)及[program.md](https://github.com/karpathy/autoresearch/blob/master/program.md) | 固定评测/训练预算，agent修改train.py、比较指标、保留或撤销；原生场景为单卡语言模型训练 | 借鉴固定评测、真实运行、保留失败记录；它允许较广的模型/超参搜索，指标优化不自动满足新颖性/消融/毕业要求，不用它代替当前方法研发 |
| [Sakana AI Scientist v2](https://github.com/SakanaAI/AI-Scientist-v2) | 由experiment manager组织渐进树搜索，覆盖假设、实验、分析和写作；README明确更开放探索不保证优于v1 | 可供实验搜索设计参考；尚无本项目协议适配证据，完整自主写作不在当前范围，不部署 |
| [FutureHouse PaperQA](https://github.com/Future-House/paper-qa) | 在论文全文上检索证据并带引文回答；核了README及pyproject | 是可选文献核查组件，不能代替训练复现/主指标/创新验收；当前已有浏览和原文核查工具，不把新建论文库设为主任务前置 |

Zotero MCP、Open Notebook与Repomix亦已看官方文档。它们分别偏论文库接入、材料问答、
上下文打包，**不是本次主要解决方案**。作者已有无Zotero或是否亲自看项目均不影响主流程。
本次不要求作者先注册、配置或学习这些工具。源码检查不等于运行验证；公开项目的演示与
论文成果也不能替代本项目的适配验证，更不能保证指标上涨或学位验收。

### 接入方式与实际验收

`ekg-research-loop`是本项目新写的窄适配层，没有拷贝外部框架实现或改现有上游skills；
通过Git追踪，不混入下方记录原样安装文件的`research_skills.lock.json`。新会话从HANDOFF
按需读取；检索用已有工具，方法复现/训练/评分继续走既有入口。职责目前由单代理顺序
承担，不声称独立多模型审查；不因引用外部multi-agent框架而启动子代理。

验收分开记录：技能结构/路径检查只证明入口可读；封存失败案例走查只检验它是否引导
正确决策，不是独立前测；未来实际应用必须观察是否自主交付可执行的论文/代码证据、
强baseline、可证伪候选及完整实验裁决，并最终由原主指标/护栏/归因门验收。增加文档量、
流程次数或LLM好评均不抵扣科学缺口。不新增与既有主表并列的任务或质量分数。

## 2026-10-08：已安装的基础科研技能

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

C-37–C-39 的后续实际使用：一手文献与竞争解释指导三项固定诊断；TDD 在新增接口和 drift/smoke 闸门上先见 RED，
verification-before-completion 要求两机 torch CPU 真跑与部署后的资产校验。证据与限制见 `results/PHASE_R1.md` §25.35。
