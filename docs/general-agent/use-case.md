### BOT agent vs. traditional alert
| 特征 | 传统告警系统（Alerting） | AI 智能体（AI Agent） |
| :--- | :--- | :--- |
| **核心机制** | 基于硬编码规则和阈值。 | 基于大型语言模型的推理、规划和工具调用。 |
| **触发方式** | 某个指标超过预设值（例如：CPU > 90%）。 | 接收到复杂指令或检测到异常模式（例如：发布事件开始）。 |
| **输出结果** | 简单的通知（例如：邮件、短信、PagerDuty 呼叫）。 | **结构化的分析报告、根本原因分析 (RCA) 和自主行动。** |
| **思维能力** | 无。仅判断 True/False。 | 有。能分解任务、制定计划、反思、自我修正。 |
| **对数据的处理** | 仅关注单个指标是否超过阈值。 | <u>能够综合分析多个指标（延迟、错误率、日志、基线）之间的复杂关系。这应该是核心，因为LLM的具有核心的核心知识。</u> |
| **行动能力** | 主要是通知人来解决。 | 可以调用API执行 rollback()、isolate_traffic() 或 auto_fix() 等复杂操作。 |
| **主要目标** | 通知 SRE/DevOps 团队发生了什么问题。 | 解决 SRE/DevOps 团队<u>为什么发生问题，并主动处理。</u> |

### Prompt vs. Program
- 纯提示词构建的Agent稳定性和可靠性不够。
- 用Agent SDK构建的Agent稳定性和可靠性会强很多。
  - 考虑知识库的帮助Agent。
    - 提示词的会自主扩张搜索范围。某些情况下是好的，就像explore subagent，不断尝试grep不同的词获取信息。
    - 在Q&A Agent中，搜索到不好的数据源。使用了GAN的subagent来验证。
    - 但是如果用编程的方式，就会好很多，可以直接校验mcp tool查找的wiki数据源。
    - 因此提供更高的可靠性。
    - 程序的方式可以强制做定量处理，例如wiki搜索可以排序和打分。提示词是不能强制。

### Q&A agent经验
- Evidence Quote Gate - 对每个输出字段标注允许的证据来源，是目前看到的最精细的反幻觉模式。
- 对AI做的判断，要求其给出细致的原因，使得AI很难编造证据链。

### code-review-agent经验
- 使用了并行的多agent从不同方面review。
- **确定性脚本获取上下文和IO相关** + LLM判断。
  - 使用preflight脚本先获取所有的review上下文。
    - repo。
    - agent repo，获取review rule等。
    - GraphQL拉取评论线程。
    - 并行获取，上下文失败直接退出(diff)。
    - 多层级的rule，后面覆盖前面。
  - 使用publish.py来发布评论。
- **subagent视角分工。**
- Delta-only原则。
  - 解决了AI review最大的噪音源：对已有问题的重复报告。
- 使用了GAN的peer-review。
- 分类讨论。
  - re-evaluate机制，提供Loop功能。
  - 当PR作者回复AI评论质疑finding时，pipeline走re-evaluate路径。
- rule的设计。
  - 明确定义级别。
  - 加入**代码示例**，正反例。
  - 同一条规则也分级。
```text
## Checkpoint N: [问题名称] [Severity]
触发条件 (when)
检测逻辑 (what to check)
代码示例 (正例 / 反例)
Do NOT flag (排除条件)
```