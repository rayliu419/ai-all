## goal
- 记录用LLM的best practice

## revisit prompt engineering 
- **提示词的表达依然还是很有用。**
- grill skill，很短的提示词，很好的效果。
  - 似乎某些场景的
- AGENTS.md里的incident的标准模版，大幅提高了回答的层次性和合理性。
  - summary.
  - root cause.
  - chain. 
  - actions.
- **从这点来看，一些比较常见的任务，还是应该寻找好的skills，这些skills会很大程度的改变LLM的回答质量。**
  - 可以认为改变了LLM的思维方法和习惯。
- 需要一个阅读仓库的skill，自己随意写的还是效果不好。
  - 类似GPT6，会给出很多无关细节的内容。
  - 需要标注的skill能
    - high level 
    - concrete workflow

## memory - 自动化的memory生成和触发效果不好
- 替代方式是使用一个docs-for-ai的文件夹，对于某一个可能偏长程的任务，记录相关资料。
- 目录结构暂时还不是很完美，需要迭代演进。
- 在继续任务时，手动触发llm阅读相关的文件夹资料。

## 积累domain工具和知识库
- example：couwatch = checkout 服务的 skill：查 log 用什么 label 过滤、查 metrics 用什么 label 查什么内容、不同故障的 SOP。
- skill 结构：SKILL.md（工作流+导航）+ reference/（label 含义、SOP，按域拆分）+ scripts/（确定性脚本）。

## 脚本自动化降cost
- 原理：确定性操作用脚本，LLM 只调用 + 看输出，不重新生成代码。
- 落地：手工重复 >1 次的操作 → 写成确定性脚本；脚本被多 task 复用 → 提升为 skill。
- 约定：单文件、stdlib、CLI 长选项、TTY/管道友好（见 CLI 工具约定）。

## 进入新领域三步：打通 → 说明 → 积累

### 打通（connect）
- 用 MCP 把数据源/tool 接进来；MCP = AI 的"USB-C 口"。
- 三个 primitive：tools（执行动作）、resources（提供上下文数据）、prompts（交互模板）。
- 落地：本地优先 stdio server，远程用 streamable HTTP；接完只算"连得上"。

### 说明（explain）
- 打通解决连通，还要告诉 AI"怎么用、何时用哪个" = ACI（agent-computer interface）。
- 像写 docstring 一样写 tool：参数名/描述清晰、写明与其他 tool 的边界、给 example usage。
- 衡量：人若无法判断该用哪个 tool，AI 更做不到 → 精简工具集、消除歧义。
- enrich: {ACI 好/坏 tool 描述对比}

### 积累（accumulate）
- 逐步积累 skill/知识库 + example 经验；触发以手动为主（见 §2）。
- 用少数 canonical example（few-shot）而非穷举规则；edge case 用 "old patterns" 折叠，不塞主路径。
- 反馈闭环：validator → 改 → 再验，写进 skill 的 workflow。

## 按任务强度路由模型
- 模型已分化：贵的模型慢且贵，不适合 incident 或要求响应快的需求。
- 人为判断任务强度，综合使用（而非一个模型打天下）：
  - 强模型（gpt6 / opus5.5 max 等，极贵）→ 复杂问题分析、设计。
    - **gpt6极其注意细节。**
  - flash模型 → 执行（直接写代码），快且便宜。
  - **有一种认知，认为不要用SOTA模型来做brainstorm，当然也不能用太差的模型。**
- grok4.7 brainstorm，opus55 + gpt6 评审。
- 强模型出方案/设计， flash 执行。
- enrich: {模型路由决策表}
