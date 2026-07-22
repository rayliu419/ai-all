# Attention Is All You Need (Vaswani 等, 2017)
提出了“自注意力机制”（Self-Attention），抛弃了以往效率低下的 RNN 和 LSTM 结构。Transformer 实现了高度并行的计算，使得模型能够处理超长上下文，并为后来算力和参数规模的“暴力美学”扩展奠定了基础。

# Improving Language Understanding by Generative Pre-Training (Radford 等, OpenAI, 2018) 
确立了“大规模无监督预训练 + 下游任务微调/提示”的范式。

# Language Models are Few-Shot Learners (GPT-3, 2020)
GPT-3 的论文，首次向世界展示了大模型的“涌现能力”和“少样本学习”（Few-Shot Learning）能力——即模型在不改变参数的情况下，仅靠提示词（Prompt）就能完成翻译、写代码、问答等多种复杂任务。

# Training language models to follow instructions with human feedback (Ouyang, OpenAI, 2022)
详细阐述了如何使用 RLHF 技术对模型进行微调，使其输出与人类的价值观和意图“对齐”（Alignment）。这是让模型从“只会盲目续写句子的机器”蜕变为“懂礼貌、有逻辑、能回答问题的对话助手”（即 ChatGPT 诞生的前置技术）的最关键一步。

# Scaling Laws for Neural Language Models (Kaplan 等, 2020)
首次用严密的实验证明了“大力出奇迹”的数学依据——模型的性能与计算量、参数量、数据量之间存在可预测的幂律关系（Power Law）。这给了科技巨头们豪赌千卡、万卡集群的底气。

# Training Compute-Optimal Large Language Models (Hoffmann 等, 2022)
纠正了 OpenAI 早期定律中的偏差，提出“参数量和高质量训练数据必须同比例增长”。这篇论文直接改变了行业风向，促使大家不再盲目追求极端的万亿参数，而是去疯狂清洗和挖掘高质量的数据，由此诞生了一批参数较小但性能强悍的模型（如 LLaMA 系列）。

# Proximal Policy Optimization Algorithms (Schulman 等, 2017)
虽然早于大模型爆发，但 PPO 是 RLHF（基于人类反馈的强化学习）的底层核心。它在稳定性和计算效率之间找到了完美的平衡，是 ChatGPT 得以成功的幕后英雄。

# Direct Preference Optimization: Your Language Model is Secretly a Reward Model (Rafailov 等, 2023)
传统的 RLHF 极其复杂且难以训练，而 DPO 提出了一种优雅的数学转换，绕过了复杂的强化学习框架，直接通过数据对比来训练模型。这极大地降低了大模型对齐的门槛，成为了如今开源模型（如 Llama 3、Qwen 等）的标配。

# DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning (DeepSeek, 2025)
1. 纯强化学习的奇迹（Zero-to-One）： R1 证明了即使不依赖海量的人类精标数据（SFT），仅靠纯粹的强化学习（如 GRPO 算法）和基于规则的奖励，模型就能“自我顿悟”，自动进化出超强的逻辑、数学和编程能力。
2. 开启了“Test-Time Scaling”（测试时缩放）的新范式——即给模型更多的思考时间，它就能输出更高质量的答案。这打破了之前预训练数据耗尽的焦虑，为大模型指明了通往 AGI（通用人工智能）的新路径。