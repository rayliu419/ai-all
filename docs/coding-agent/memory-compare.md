# 比较不同的Agent的memory的运作方式

## 为什么需要memory
- 大模型的运作模式是每次对话，需要将前面所有的历史一起发过去。
  - 新的session只包含新的对话，不包含以前的内容。因此在老的session的背景知识，新session完全不知道。
- 记忆能让 Agent 跨越时间和 Session（对话阶段），记住关于你的核心信息。
  - 提高对话的效率。
- 现实世界中的任务很少能通过“一问一答”解决，往往需要拆解成几小时、甚至几天的工作流。
  - 在执行一个自动化爬虫并分析数据的任务时，Agent 需要记住第一步拿到了哪些 URL，第二步报错了需要重试哪一部分，第三步该合并哪个表格。
- 人类通过复盘来成长，Agent 也需要通过记忆来完成反思（Reflection）。
  - 没有记忆，Agent 就会陷入在同一个坑里反复跌倒的死循环。

## memory系统的难点
- 应该是在做开始做某个任务之前，怎么把以前相关的知识获取，能够更好的完成新的任务。
- 检索的精准度与高噪音（Retrieval Precision vs. Noise）
  - 向量相似度（如余弦相似度）只管“长得像”，不管“对不对”。检索出来的历史碎片可能包含大量无关信息，这会严重污染LLM的上下文，导致智能体判断失误。
- 虽然像 Gemini 等模型的上下文窗口已经扩展到非常大，但“能放下”不等于“能用好”。
- Agent 的记忆更新极难平衡。
  - 哪些是需要永久固化的“硬知识”（如用户的名字、核心偏好），哪些是应该随时间淡化的“临时记忆”？
  - 缺乏科学的衰减算法（Decay Mechanism）会导致记忆库无限膨胀。
- 如果仅仅是把聊天记录原封不动地存下来，Agent 的智商会非常受限。

## 当前的主要设计模式。
- 混合检索: 向量检索（看语义）+ 传统关键词检索（看精准度）+ 知识图谱（看因果和实体关系）。
- 为什么使用知识图谱作为memory信息的载体？
  - 传统的向量记忆让Agent知道哪些词”经常在一起出现”（相关性），而知识图谱让Agent明白”什么是原因，什么是结果”（因果性），从而让智能体具备了真正的逻辑推理与反思能力。
  - 散落的聊天记录只是无法直视的”信息噪音”；只有当 LLM 将其提炼为点与线、实体与关系的图谱时，记忆才真正凝聚成了高密度、可随时检索激活的”知识网络”。
  - 向量记忆给Agent带来了感性的”直觉”，而知识图谱记忆给Agent注入了理性的”骨架”。
  - 知识图谱的更多优势:
    - 多跳推理（Multi-hop Reasoning）：向量数据库无法遍历关系链。例如”哪些供应商同时给A公司和B公司的竞争对手供货？”——向量搜索从结构上就不可能完成这种查询。知识图谱通过显式的实体-关系边，支持确定性的多跳遍历。
    - 时序理解（Temporal Reasoning）：知识图谱支持双时间模型（bi-temporal），事实不会被删除而是标记为”过期”，实现完整的时光回溯查询。Zep/Graphiti 在时序推理任务上比纯向量方案高出18.5%的准确率。
    - 可解释性（Explainability）：向量检索的相似度分数是黑盒的，无法解释”为什么像”；知识图谱的每个答案都可以追溯到具体的节点和边路径，通过审计合规要求。
    - 冲突事实处理：向量数据库将每次输入视为不可变事实；当事实改变时，旧文本仍然存在，检索到冲突信息会混淆LLM。知识图谱可以将旧事实标记为 invalid_at，在保留历史的同时保持当前事实清晰。
    - 全局整体理解（Global Query）：在跨数据集的整体性问题（如”这个语料库的核心主题是什么？”）上，标准向量 RAG 在某些基准测试中准确率为0%，而 GraphRAG 通过社区检测和层次化摘要大幅领先。
- 异步记忆固化: 不在对话时实时处理记忆，而是利用后台进程，在Agent空闲时将散乱的Short-term记忆通过LLM提炼成高密度的Long-term知识或用户画像。

## memory plugin 
- https://github.com/thedotmack/claude-mem 是怎么做的？
    - 完全自动化地旁路观察系统。
    - 架构：Worker Service (HTTP server on port 37777) + SQLite 数据库 + AI 观察者模型。
    - 写入：用户对话 -> Claude Code 使用工具 -> Hook 触发 -> Worker Service 接收 -> AI 观察者模型分析 -> 写入 SQLite observations 表
        - 会话元数据 + 观察记录 + 每轮对话总结。
        - 图结构记录memory。
        - 异步调用小模型来总结。
    - 读取：
        - SessionStart hook 最后一步调用 context 子命令。
            - 基于当前项目 + 时间倒序 + 类型/概念过滤。概念什么的，应该是异步分析时打的标。
            - 注入到对话的格式（你在 Claude Code 启动时会看到的那段文字）。[project-name] recent context, 2026-06-11 5:51pm GMT+8
        - 对话中 - 提供了一个 mcp-search MCP server，可以搜索历史观察记录。
            - 用ChromaDB 向量搜索。基于当前 user prompt 的语义相似度。

## claude code memory 
- /Users/liurui/workspace/learn-claude-code/claude-code/notes/memory-system-analysis.html
- 分为会话内上下文管理（In-Session）和跨会话持久化记忆（Cross-Session / Persistent Memory）两大核心维度。
- CLAUDE.md就是每次session启动的memory之一。

## Hermes agent 
- 存储长效环境背景（活动项目、技术栈、核心依赖关系）。
- 所有 CLI 终端和消息网关（Telegram/Discord/Slack）的原始对话均无损保存于本地的 ~/.hermes/state.db中。
  - 结合了 SQLite 的 FTS5（全文检索）技术。 
  - 应用场景：当长对话被截断，而 Agent 需要查找几周前讨论的某句特定代码或特定 Bug 时，它会调用搜索工具直接在数据库中检索原始文本（而非依赖 LLM 模糊的总结），以此对抗“上下文失忆”。
  - 内存工具（The Memory Tool）：Agent自主维护记忆，通过add（添加）、replace（替换/合并）和remove（删除）三个原子操作管理USER.md和MEMORY.md。

## MemTensor/MemOS
- 层次化存储（Hierarchical Storage）
  - L1 轨迹层（Traces）：纯原始的对话和工具执行日志。
  - L2 策略层（Policies）：Agent 自己总结出的“用户喜欢什么样的代码风格”、“这个 Bug 应该怎么修”等规则。
  - L3 世界模型/知识库（World Models）：项目的核心架构、不可变的事实。
- 混合检索引擎（Hybrid Retrieval）
  - 向量检索（Vector Search）：负责模糊的、语义相关的记忆（“找一下之前聊过的关于高并发优化的地方”）。
  - 全文检索（SQLite FTS5）：负责精准的关键词匹配（“查找包含 auth_v2_final 这个函数名的历史对话”）。通过智能去重（Deduplication），确保用最少的 Token 带给 LLM 最精准的背景。
- 异步吞吐与调度（Asynchronous Ingestion via MemScheduler）
  - Agent 在前台和人类流畅对话，内存的写入、向量化（Embedding）、记忆的合并与擦除都在后台异步完成，延迟能达到毫秒级。
- 记忆反馈与自我进化（Self-Evolving & Correction）
  - 记忆整合（Consolidation）：当发现多条零散记忆都在说同一件事时，它会自动融合成一条高信息密度的记忆。
  - 反思与纠错（Feedback Loop）：人类可以说：“不对，刚才那个方案不安全，以后别用了。”Memory OS 收到指令后，会主动去定位旧的记忆，将其修改、补充或无痕替换。

## 动态Memory可能会导致Cache失效的问题
- 因为相当于在对话中动态插入了token。
- 如果设计不当，动态更新的 Memory 会高频触发 Cache Miss（缓存未命中），导致 API 费用暴涨、首字延迟飙升。

## 如何让 Memory 与 Cache 完美共存
- 严格控制 Prompt 拓扑结构（Static-to-Dynamic Layout）
    - 将最不容易变动的内容放在最前面，将最高频变动的内容放在最后面。
    - Prompt =
        - System Prompt + Tool Schemas {绝对固定 (100 Hit)
        - Chat History (Append Only) 线性增长 (自动追加缓存)
        - Dynamic Memory / Timestamp 置于末尾 (仅此处 Miss)