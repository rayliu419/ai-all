## goal
- 记录用 LLM 的 best practice：把"一次性经验"沉淀为"可复用资产"（skill / 脚本 / 知识库），下次自动触发，不再重复解释。

## 核心主张
- 上下文是有限注意力预算：token 越多，模型精确回忆越差（context rot），要精心挑选放进去的 token。
- 主线 = 渐进式披露（progressive disclosure）：只放当前需要的高信号 token。
- 三类资产，三种机制：
  - 程序性知识（怎么做）→ skill，靠 description 触发（任务模式可识别）。
  - 情景记忆（之前讨论/决定了什么）→ 系统提示词提示 + LLM 决策搜索，不是 skill。
  - 领域知识（label 含义 / SOP）→ 装进 skill 的 reference，随 skill 按需加载。
- 两个真难点——memory 的触发、积累的触发——都不靠自动规则：前者靠"提示 + LLM 判断"，后者靠"手动"。

## 1. memory：提示 + LLM 决策搜索，不是 skill
- memory 真正的难点是"何时触发什么"：你不知道历史里有没有相关内容，直到去查。
- 因此不适合做成 skill——description 匹配不了"有没有相关历史"这种模糊触发。
- 方案 = 系统提示词里给一句提示，让 LLM 自己决定何时去本地搜：
  - 例："tasks-for-ai/ 记录了我们讨论过的问题，有时可以去搜索一下有没有背景，尤其是 session 刚开始时。"
  - 本质是本地 keyword 搜索（grep）：便宜，命中才读详情。
  - 时机建议：session 刚开始优先 + 过几步再探索一下，是否搜由 LLM 决策。
- 索引一行一个主题（便宜扫）；命中才读 background/decision log（按需）→ 渐进式披露。
- 兜底：用户显式"继续 X / 回忆 X"也是可靠触发。
- enrich: {探索决策流程图}

## 2. 积累 domain 工具和知识库
- 目标：查问题/做任务不用反复说背景。核心在"逐步积累"。
- 积累的触发：自动积累很难触发准确 → 手动为主。
  - 触发信号：用户显式（"记录 / 沉淀 / 记住"）+ 固定时点（每 ~5 轮、/compact 前、session 结束前）。
  - 写路径预先定好，手动成本低：append 到 decision log，或加到 domain skill 的 reference。
- skill 结构：SKILL.md（工作流+导航）+ reference/（label 含义、SOP，按域拆分）+ scripts/（确定性脚本）。
- 引用一层深、命名/术语统一。
- example：couwatch = checkout 服务的 skill：查 log 用什么 label 过滤、查 metrics 用什么 label 查什么内容、不同故障的 SOP。
- enrich: {couwatch 目录结构 + label→含义 表}

## 3. 脚本自动化降 cost
- 原理：确定性操作用脚本，LLM 只调用 + 看输出，不重新生成代码。
- 落地：手工重复 >1 次的操作 → 写成确定性脚本；脚本被多 task 复用 → 提升为 skill。
- 约定：单文件、stdlib、CLI 长选项、TTY/管道友好（见 CLI 工具约定）。

## 4. 进入新领域三步：打通 → 说明 → 积累

### 4.1 打通（connect）
- 用 MCP 把数据源/tool 接进来；MCP = AI 的"USB-C 口"。
- 三个 primitive：tools（执行动作）、resources（提供上下文数据）、prompts（交互模板）。
- 落地：本地优先 stdio server，远程用 streamable HTTP；接完只算"连得上"。

### 4.2 说明（explain）
- 打通解决连通，还要告诉 AI"怎么用、何时用哪个" = ACI（agent-computer interface）。
- 像写 docstring 一样写 tool：参数名/描述清晰、写明与其他 tool 的边界、给 example usage。
- 衡量：人若无法判断该用哪个 tool，AI 更做不到 → 精简工具集、消除歧义。
- enrich: {ACI 好/坏 tool 描述对比}

### 4.3 积累（accumulate）
- 逐步积累 skill/知识库 + example 经验；触发以手动为主（见 §2）。
- 用少数 canonical example（few-shot）而非穷举规则；edge case 用 "old patterns" 折叠，不塞主路径。
- 反馈闭环：validator → 改 → 再验，写进 skill 的 workflow。

## 5. 按任务强度路由模型
- 模型已分化：贵的模型慢且贵，不适合 incident 或要求响应快的需求。
- 人为判断任务强度，综合使用（而非一个模型打天下）：
  - 强模型（gpt6 / opus5.5 max 等，极贵）→ 复杂问题分析、设计。
  - flash 类模型 → 执行（直接写代码），快且便宜。
- 一个任务可组合：强模型出方案/设计 → flash 执行。
- enrich: {模型路由决策表}

## 参考
- Effective context engineering: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- Building effective agents（附录 ACI）: https://www.anthropic.com/engineering/building-effective-agents
- Claude Code memory: https://code.claude.com/docs/en/memory
- Agent Skills overview: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview
- Skill authoring best practices: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- MCP intro: https://modelcontextprotocol.io/docs/getting-started/intro
- MCP architecture: https://modelcontextprotocol.io/docs/learn/architecture
