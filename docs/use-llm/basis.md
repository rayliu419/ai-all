## mcp
- 让LLM加入更多的数据源，改变LLM的预测Token。
- MCP实现
- 每个MCP有多个tools，其实都是编程实现的。
  - 类似为一个服务写API endpoint，只是这个API endpoint是给LLM使用的。
  - https://github.com/modelcontextprotocol/servers/blob/main/src/memory/index.ts
- 引用MCP的Tools
  - 在提示词或者skills中，用这样的方式引用MCP的Tool mcp__{mcp_sever_name}_{tool_name}。

## skills
1. 定义
- Skills are folders containing instructions, scripts, and resources。
  - SKILL.md。规定了 Skill 的名称和描述，这是模型识别并决定是否调用该技能的唯一凭据。
  - scripts。可选组件，包含 Python 或 Bash 等脚本，赋予了在沙箱环境中执行确定性操作的能力，例如复杂的数学计算、数据转换或特定的文件处理逻辑。对于确定性相关的，尤其数学计算，最好用程序来协助。
  - references：可选组件，包含供模型随时查阅的文档、API 规范或领域专业手册。这部分内容只有在模型认为需要时才会按需加载，极大地节省了初始上下文空间。
  - assets：可选组件，如公司品牌指南、特定的模板文件、图标或样式表，确保模型生成的输出（如文档或 PPT）符合特定的视觉和规范要求。
2. 解决的三大问题
- 重复提示。
  - 如果希望始终遵循特定的代码风格或品牌调性，必须在每一个新对话的开始处粘贴数千字的 System Prompt这种模式不仅增加了用户的认知负担，也极易因为提示词的微小差异导致模型输出的波动。
- “渐进式披露”架构。三层信息加载机制平衡模型的智能水平与Token 消耗成本。
  - 元数据加载
  - 在会话启动时，仅加载所有已安装技能的名称和描述。技能索引让模型知道自己“会做什么”而不需要知道“怎么做”。
- 指令加载
  - 检测到用户需求与某个技能匹配时，它才会读取SKILL.md全文。节省上下文。
  - 资源深入。
  - 在执行过程中，如果模型需要具体的API或脚本，进一步访问文件夹中的辅助文件。  

## RAG
- Retrieval-Augmented Generation。RAG = 外部知识库 + 大语言模型。
- **RAG 是目前让大模型进入企业生产、解决“落地难”问题的最主流方案。**
- 检索（Retrieval）
  - 当你问问题时，系统先去你的私有文档或数据库中搜索相关的资料。
- 生成（Generation）
  - 系统把搜到的资料和你的问题一起喂给大模型，让模型参考这些资料来回答。相当于改变了输入Token。
- 为什么需要 RAG？
  - 解决“幻觉”问题：模型有时会一本正经地编造事实。RAG 要求模型“看书说话”，回答必须基于检索到的证据，大大降低了造谣概率。
  - 解决时效性问题：大模型的知识停留在预训练结束时间。如果你问它昨天的科技新闻，它不知道。通过 RAG，你只需把最新的新闻放入检索库，模型就能立刻掌握最新动态，无需重新训练。
  - 保护数据隐私与私有化知识。企业的内部文档、财务报表、个人笔记是不可能发给 OpenAI 去训练模型的。通过 RAG，这些敏感数据留在你的本地服务器上，模型只在回答那一刻临时“阅读”一下，既安全又专业。

## Tools
- 最新知识要用搜索tool。
  - pretraining是基于历史数据训练。
  - base model是这个时间点之前的整体模糊记忆。
- 搜索结合原理
  - 搜索以后拿到返回，填充到上下文窗口，然后继续生成token。
  - 不再使用原来的token做sampling预测。
  - 显式指定使用可以降低幻觉。
- 生成各种图表，概念图，关系等。

## Deep research
- thinking + search tool
- 只能作为draft，还是可能有幻觉。
- 使用llm帮助读书，论文。
  - 在读某个章节时，最好把原文贴过去，因为现在llm只有模糊的记忆，可能效果不好。

## Prompt
- PerFECT原则
  - Persona
  - Examples
  - Context
  - Format
  - Task
- 其他技巧
  - zero/few shot prompt
  - tree of thoughts
    - 有三个工程师，需要对于某个设计有想法，他们需要考虑并讨论。
- Q & A strategy
  - windsurf一般全部做决策，这些决策的假设可能有错误。
  - 可以说如果有觉得不清楚的，可以问我。

## 图片和语音处理
- 一般都是先转录，转成文本。
  
## 高级语音模式
- 中间不再转化成text token，直接使用语音token。
- 能够具有比转换方式独特的能力。