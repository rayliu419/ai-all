# Serving具体架构

## Pre-training vs. Serving
- 大语言模型（LLM）的 Pre-training（预训练） 和 Serving（推理服务） 比喻为“读书”和“现场答辩”。
- 核心任务
  - pre-training: 像海绵一样吸收海量文本知识（如万亿 Token），学会预测下一个词。
  - Serving: 针对用户的具体输入（Prompt），实时生成高质量的回复。
- 计算特征
  - 吞吐量导向（Throughput）。追求GPU算力的极致利用率（MFU），通常使用极大的Batch Size。
  - 延迟导向（Latency）。追求首字延迟（TTFT）低、吞吐高，通常是动态变化的Batch Size。
- 数据流动
  - 双向/并行。前向传播计算 Loss，反向传播（Backpropagation）更新模型权重（Weight）。
  - 单向/前向。只有前向传播，模型权重被冻结（Freeze），不发生改变。
- 硬件需求
  - 超大规模GPU集群（几百到上万张卡），需要高带宽网络（InfiniBand）进行频繁的梯度同步。
  - 单张卡或较小的GPU集群（通过张量并行TP分布在几张卡上），更看重显存带宽（HBM）。

## 端到端处理流程
- 当一个用户在客户端点击发送，到屏幕上开始逐字蹦出回复，在服务端经历了一个完整的端到端生命周期。目前主流的Serving框架（如 vLLM, TensorRT-LLM）都遵循以下两个核心阶段：
- Prefill（预填充阶段 / 计算 Prompt）
  - 服务端的 Tokenizer 将文本切分成 Token ID，然后一次性喂给模型。模型会计算这些输入Token的Attention键值对，并将其缓存下来，这个缓存就叫 KV Cache。
- Decoding（解码阶段 / 逐字生成）
  - 基于前面的上下文，自回归（Autoregressive）地逐个生成后面的Token，直到遇到结束符（EOS）或达到最大长度。
  - 每次只输入上一步生成的单个Token，结合之前缓存的KV Cache，计算出下一个Token的概率分布，采样（Sampling）后输出。然后把新Token的KV写入缓存，循环往复。
  - 因为每次只处理一个Token，GPU 算力吃不满，时间都花在从显存中读取模型权重和KVCache上。

## KV cache
- KV到底指的是什么?
  - 在 Transformer 模型的每一层中，输入一个 Token（词），都会通过三个不同的线性变换矩阵（Q, K, V），计算出三个向量
    - Query (Q)：当前词“想要寻找什么”
    - Key (K)：当前词“能提供什么特征”，用来给别的词匹配。
    - Value (V)：当前词“包含的实际内容”，一旦匹配成功，就输出这部分内容。
- 假设用户进行了三轮对话，当用户发出 Round 3 的请求时，服务端的处理逻辑是：
  - 在服务端的网关或应用层，有一个会话管理器（如 Redis 或内存数据库）。它会把前两轮的所有对话文本按角色拼接成一个大文本。
  - Round 1 和 Round 2 产生的 KV Cache 并没有被释放，而是像物理内存页一样，保存在服务端的显存里，并与该用户的 Session_ID 绑定。
  - 当 Round 3 请求到来时，服务端发现前两轮文本的 Token 已经计算过 KV Cache 了。系统会直接复用（命中）这部分显存，只对 Round 3 新增的输入（"那第一部的导演是谁？"）进行 Prefill 计算。
  - 计算完新 Prompt 的 KV 后，将其追加到该 Session 的 KV Cache 链表后面，直接进入 Decoding 阶段，开始吐出答案。
- 怎么存的？存在哪
  - 不是Redis，是GPU的缓存。
  - KV Cache是直接存储在GPU的显存（HBM，高带宽内存）中的。
  - 为什么它必须在显存里？ 
    - 因为在 Decoding阶段，模型每生成一个新词，都要和之前所有词的KV Cache进行一次注意力（Attention）计算。这个过程是**访存密集型（Memory-bound）**的，如果把 KV Cache 放在 CPU 内存里，每一次生成新词都要经过 PCIe 总线传输数据，速度会慢几十倍，变成极其卡顿的“挤牙膏”式输出。
- GPU的架构