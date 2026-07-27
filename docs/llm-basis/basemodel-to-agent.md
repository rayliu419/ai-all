# Base Model → Agent

## LLM → Agent 的完整链路

### 1️⃣ 预训练（Base Model）

- 只学语言建模
- 目标是预测下一个 token
- 没有"对话意识"
- 没有"任务意识"

**举例：**
- OpenAI 的 GPT-3 base
- Meta 的 LLaMA base
- Google DeepMind 的 Gemini base

> 它不知道什么是"回答问题"或"写代码"。

### 2️⃣ 指令微调（SFT）

- 给出很多类似训练 chat 的训练集，在 base model 上继续训练。
- Supervised Fine-Tuning
- 识别 user / assistant 角色
- 给出"完整回答"
- 组织清晰结构
- 避免乱续写

**举例：**
- OpenAI 的 GPT-3 → ChatGPT
- Anthropic 的 Claude 系列
- Mistral AI 的 Instruct 模型

> 这一步结束以后 Base model → Chat model

### 3️⃣ 对齐训练（RLHF / DPO）

Direct Preference Optimization

SFT 之后模型已经能回答问题，但还不够：
- 可能啰嗦
- 可能不安全
- 可能答非所问

### 4️⃣ 工具使用能力训练

### 5️⃣ 记忆 / 规划 / 多步推理增强

现在模型还不能：
- 记忆长期信息
- 规划多步骤任务

这一部分已经不是模型训练问题，而是系统架构问题。

**短期记忆：**
- 对话上下文（prompt）

**长期记忆：**
- RAG
- 向量数据库
- 用户偏好存储

---

## 为什么通过 post-training 可以形成某种 Agent

LLM 本质是"条件概率机器"，它只是：在给定上下文条件下，预测最可能的下一个 token。

谁控制了"context 分布"，谁就控制了模型行为。

Post-training **改变了条件分布**。

- 通过大量的对话训练集，LLM 学会了在这种 prompt 结构下生成稳定的"assistant 风格输出"。

### 为什么这种变化是比较稳定的？

Transformer 是极强的模式拟合器。

它会在 embedding 空间中形成：
- "对话态分布"
- "文章态分布"
- "代码态分布"

SFT 本质是在强化"对话态"这个分布区域。

- 模型会被拉进**对话态流形（manifold）**
- 如果你 Post-train 时：
  - 只喂"客服对话数据"
  - 或只喂"代码审查数据"
  - 或只喂"数学推理数据"
- 那模型会把概率质量集中到那种行为区域。

> 这就像在参数空间里从一个"宽分布球体"压缩成一个"窄分布椭球体"。

**注意：** 虽然是稳定的，但不是数学意义上的绝对稳定。
- 本质概率模型 → 永远不是 100% 确定。

### 要多少数据量来保持稳定？

不是数据量本身，而是 $KL(P_{assistant} || P_{model})$ 足够小。

当模型的输出分布在对话上下文下已经接近人类标注分布时就算"收敛到对话态"。

---

## Memory

长期记忆都是 Agent 在做。

Agent 的 memory 本质是**选择性地把过去信息重新送入模型**。

> 模型没有真正"存储"。只是每次都重新读取外部状态。

**LLM 不维护 state，Agent 维护 state。**

---

## 长上下文概念的理解

长上下文能力，究竟来自模型结构，还是可以靠 Agent 优化"弥补"？

- 真正的"长上下文处理能力"来自模型架构与训练。
- 仅靠优化 Agent 是无法凭空获得的。
- 但 Agent 可以在系统层"模拟"或"绕开"部分限制。

**定义：** 模型在一次前向计算中，能够处理 N 个 token，并有效利用它们。

- Transformer 结构
- 位置编码机制（RoPE / ALiBi 等）
- 是否在长序列上训练过

这些都发生在预训练或长序列微调阶段。

## LLM Agent 架构全景

### 核心理解
- Agent 本身是把所有组件串起来的"胶水层"。
- LLM 是大脑核心——使用哪些 Tool、如何 Planning、记住什么，都由 LLM 决定。
- 光有大脑无法驱动，Agent 给大脑加上"眼睛"（感知）、"鼻子"（工具）、"反馈"（评估）。
- Agent 给大脑加上记忆（Memory）和外部输入信息。

### 架构
- 其实跟其他的agent也是跟coding agent类似的。
- https://github.com/rayliu419/learn-claude-code/blob/main/notes/standard_agent.png
