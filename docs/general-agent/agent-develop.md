## 依赖环境
### 安装
- python3 -m venv .venv
- pip install jupyter ipykernel
- python -m ipykernel install --user --name ray

### 使用方法1：浏览器调用notebook
- source .venv/bin/activate
- jupyter notebook
### 使用方法2: 用visual studio
- 这种更方便，能做函数跳转什么的.

### LLM API key
- deepseek

## LangChain vs. LangGraph vs. DeepAgent vs. CrewAI vs. Raw
- LangChain是基础积木库。
  - 最全的框架。它是巨大的工具箱，提供了连接各种LLM、数据库、内存管理和Prompt模板的标准化接口。
  - LangChain实现不了复杂的逻辑，不要投入太多。
- LangGraph时一个带控制流的语句，它能够跳转，条件执行等，底层的编排。 - P0
  - LangGraph是最严谨的 ，精细的工业控制台。
- CrewAI集中在多Agent的配合。- P1
  - 主要重点在封装了复杂的团队协作协议。CrewAI快速落地，原型。
- Raw  - P0
  - 高端开发的选择，直接使用原生SDK。
- DeepAgent是偏高层的编排，封装了底层。 - 不要投入。
  - 提供一个开箱即用的高级Agent框架。

### Raw
- 直接使用Anthropic API和Open API的SDK。
- 能快速的使用原生API，不用等待框架实现。
- 框架中会过度封装，自动加入上下文等，反而会引起性能问题。
- **每一行都是可解释、可调试的。适合集成到你现有的后端服务中，因为不必再去适配框架复杂的异步逻辑。**

### LangChain 

#### Message
- 理解LLM调用的时候其实是每次将不同角色的Message作为历史一起传入。
  - SystemMessage
  - HumanMessage
  - AIMessage
  - ToolMessage
#### PromptTemplate
- 在实际开发中，你不会把给 AI 的指令死死地写在代码里，而是Java的String.format，根据用户输入动态填充内容。
#### OutputParser
- 模型返回的通常是字符串，但你可能需要 JSON、列表或特定的 Python 对象。解析器负责将 AI 的回复“格式化”为代码可以直接处理的数据结构。是打通MCP的tools的关键。
#### LCEL
- 仿照的是Unix的管道方式，构建pipeline。
- 类似Java的高阶函数，先把操作连起来，最后invoke的时候再开始传数据。
- 像个控制流模版，运行时做一定的参数改变就可以了。
#### 定制Agent类
- 现在很少用内置的Agent，还是使用定制化的方式更好。
- LangChain本身自带一些Agent，但是都是黑盒。

### LangGraph重点

#### State
- LangGraph = 节点（处理逻辑）+ 边（执行顺序）+ State（数据流动）
- 理解LangGraph的核心。State 就是一个数据流水本，记录了从开始到现在所有节点产生的数据。
- 想象一个城市的中心广场，所有人（节点）都会来这里：
  - 发布消息：把自己处理的结果贴到广场的公告板上。
  - 查看消息：看看别人贴了什么信息，作为自己工作的输入。
  - 信息汇总：所有人的工作成果都汇集在这个广场。
- 特点：
  - 可累积性。
  - State 像滚雪球一样，越滚越大，每个节点都往上加东西。
  - 可覆盖性。
  - 如果节点返回了同名字段，会覆盖旧值。
  - 可以自定义Reduce方式来改变默认行为。
  - 节点间通信的唯一方式。
  - 在 LangGraph 中，节点之间不能直接对话，只能通过State交流。

### CrewAI重点
- 能快速出活，多Agent协调。

### DeepAgent 
- 不要投入