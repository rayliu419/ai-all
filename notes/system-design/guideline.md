## 整体流程

### 理解问题和设计范围
- 理清需求，设计什么，主要功能需求是什么？就要讨论的特性列表达成一致，因为时间有限。
- 讨论非功能性需求，最好集中在性能和规模可扩展性。
- 其中性能和规模需要做估算，数据规模可能影响解决方案。估算很重要，一定需要估下，自己设计真实系统也是这样。
- 输出
  - feature列表
  - scalability 
  - capacity

### High level design
- 通过前面的特性分析，基本上可用抽取需要实现什么样的API，输入和输出是什么。有可能不是API，是S3的交互等。
- 微服务拆分和部署图，多个微服务怎么交互。
- 数据模型，包括数据访问模式和读写的比例，一致性要求等。数据库选择，索引建立等。
- 输出
  - API design 
  - High level design graph 
    - 我觉得是微服务图
  - Data model and schema

### Deep dive
- 哪个地方可能会出问题，尽量讨论多个不同方案的trade off。
- 讨论选择的原因。
- 输出
  - Articulate the problem
  - Come up with at least two solutions
  - Discuss the trade-offs of the solutions
  - Pick a solution and discuss it with the interviewer

### Wrap 
- 总结