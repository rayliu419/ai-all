### session-debugger
- 对于cc来说，会把session的所有情况转录到.claude目录下。
- capture the full interaction between a user and the AI agent, including prompts, AI responses, file diffs, tool usages (e.g., bash commands, file reads/writes), and session metadata。
- 开发一个hooks和node server，hooks在SessionStart启动，node不断的读取转录文件。我们就可以通过node server来看看cc到底在后面做了什么。这也可以看到cc是怎么用我们的skills和subagent的。
- 实际上，可以看看.claude下面都有一些什么东西。

### Langfuse 集成到 Claude code
- 能够看到都做了一些什么事情。
- 从流程上来看，不如我的session-debugger清晰，但是有网状的图之类的。

### User Case驱动
- 我的方法是根据learn-claude-code或者agenatic pattern，让cc探索claude-code的具体实现方式，例如：
- 用户两次点击esc退出，发生了什么。
- cc的系统提示词是怎么组合的。
- 这些帮助理解一个好的agent都是怎么实现的。
- session-debugger则是一个cc动态运行时背后详细做了什么，相当于一个运行时的调试。
- 代码+运行时就可以很好的学习cc的设计和实现了。

### Singe Agent vs. Multi-Agent
- 在coding agent中，现在基本都是多agent模式了。

| 特征 | 单智能体 (Single Agent) | 多智能体 (Multi-Agent) |
| :--- | :--- | :--- |
| 核心架构 | 只有一个 LLM “大脑” 和一套工具集。 | 多个 LLM “大脑”（Agent），每个有自己的角色和工具集。 |
| 任务处理 | <u>**采用链式思考 (CoT) 或 ReAct 模式**</u>，尝试一步到位地分解和解决任务。 | 采用分工协作和流程编排，将大任务拆解给不同的专业 Agent 共同完成。 |
| 思考复杂度 | 高。单个 Agent 必须承担所有规划、执行和反思的责任。 | 低。每个 Agent 专注于一个子任务，降低了单个 LLM 的认知负荷。 |
| 协作/交互 | 无。所有交互都发生在 Agent 内部（如调用工具）。 | 有。Agent 之间相互交流、分享信息，甚至进行辩论或审查。 |
| 容错性 | 低。如果 Agent 在中间步骤 “出错” 或 “幻觉”，整个任务可能失败。 | 高。一个 Agent 的输出可以被另一个 Agent 审查或修正。 |
| 资源消耗 | 相对较低（只需运行一个 LLM 实例）。 | 相对较高（需要运行多个 LLM 实例和编排逻辑）。 |
| 适用场景 | 简单的查询、文本生成、一次性的工具调用任务。 | 复杂的、多领域的、需要高可靠性、需要专业知识协作的任务。 |