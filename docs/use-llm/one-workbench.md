## goal
- OneWorkbench = **桌面总入口 + 一键 AI**。
- 核心不是看板，而是：**卡片上的一次点击，变成一段上下文齐备、按 skill 执行、且留下记录的对话**。

## 核心：一键 AI

```
看到异常（卡片 / 行 / 曲线点）
  → 点意图（看看怎么修 / 为什么没部署 / 准备发布）
  → 跳到对话（新建会话，上下文已装好，skill 已挂上）
  → 产出 patch / 结论 / 状态回写，并落一条 run 记录
```

### 上下文包三层

| 层 | 内容 | 来源 |
| --- | --- | --- |
| 实体 | 票号、PR、分支、环境、role、时间点 | 视图当前实体 |
| 现场 | 失败用例 + 报错片段、最近部署、时间窗变更、日志尾部 | 数据源（插件缓存） |
| 意图 | 动词 + 期望输出 + 绑定的 skill | 意图模板（插件资产） |

**必须把新鲜度传进去**（卡片上的「15:43 · 旧数据」），否则模型拿旧数据下结论。

### 四条规则

1. 一键不是零输入：可以补一句，不补也能跑。
2. 上下文由系统打包，用户不复制粘贴。
3. 结果必须有出口：patch / 状态回写 / 新建待办。
4. 意图模板 + skill 是资产，可版本化。

## 交互：一键 = 跳进对话

- **形态定案：跳转到对话页**（不弹窗、不抽屉）。对话才是活儿发生的地方，且能留历史。
- 顶部一排「引用胶囊」：`PEPS-5129` `CI` `15:43` `旧数据 ⟳`，点任一回到原卡片。
- 默认新建会话，避免串上下文；只有同票同视图才允许并进当前会话。
- 回到原视图时保留滚动与筛选；卡片状态若已变则刷新。

一次点击的时序：捕获视图快照 → 组装 bundle → 选会话 → 首条消息 = 意图模板 + bundle（可编辑再发）→ 落 run 记录。

## 执行链：意图 → skill → 记录

- 意图上挂 skill（我用的 `dev-flow`）：一键后按 skill 的步骤走（定位 → 复现 → 修复 → 验证），不是让模型自由发挥。
- 全程和「功能」挂钩，**产生 db 记录**：`run_id, feature_id, intent, skill+version, session_id, context_hash, steps[], output, status, cost, ts`。
- 收益：可追溯（三个月后能查这张票问过什么）、可统计（哪个意图最常用 / 哪一步常卡）、可复用（第二次一键直接带上上次记录）。

## UI：桌面总入口

- 形态对标 DeepSeek Desktop：顶部常驻输入（⌘K）+ 左侧插件与会话历史 + 中间看板。
- 差别：**面板是主体，对话是"跳过去"的另一个页面**，不是叠加层。
- 左侧栏每一项都是插件；关掉插件，入口和后台任务一起消失。

## 插件模型

插件声明：**侧栏入口 · 后台任务 · 凭证 · 卡片/意图**。

| 插件 | 侧栏 | 后台任务 | 动作 |
| --- | --- | --- | --- |
| Copilot | Devin | collectTasks 15s | 18 |
| 我的待办 | 常用 | jiraDailyScan 1m | 5 |
| 开发任务 | 开发测试 | importRegistrations 30s / refreshViewed 5m | 4 |
| Perm 与 Charles | 开发测试 | refreshPerms 1m | 5 |
| Change history | 可靠性 | syncAbc / syncDeploys 1h | 13 |
| Session 详情 | 调试 | — | 4 |
| 配置中心 | 设置 | — | 3 |

意图 = UI 按钮 + agent 能力的同一份数据。

## 票：8 个系统拼成一条流水线

建票(jira) → PR(gh) → 代码(gh) → CI(gh pr checks) → PERM(CouTest) → 测试(Charles+QA) → EERP → 发布(Couest)。

每张卡五元信息：状态 · 结论 · 来源 · 时间戳 · 旧数据标记，再加意图按钮。难点是实体对齐，规则公司特有、必须可配置。

## 技术选型

- **TS**：manifest → UI → 调度 → MCP → agent SDK 全栈同语言，类型共享；重计算交 Python CLI。
- **Electron**：需要本机凭据、文件系统、常驻快捷键；主进程即 Node，能直接加载 agent SDK。
- **agent 后端 = 接口 + 两实现**：
  - `piSdkBackend`（首选）：`createAgentSession()`，跑在 main 或 utilityProcess。注意 SDK 不自动加载内置扩展（MCP/codemode/tool_search 显式注册 + `bindExtensions()`），`agentDir` 做隔离。
  - `acpBackend`：接 Devin 这类外部 agent。
  - `piRpcBackend`：子进程 JSONL，仅作隔离降级项。
- **数据**：MCP 优先，没有就包 CLI / 薄 HTTP。

## 换一家公司

底座不动。换：数据源、插件集、意图模板 + skill、凭证、agent 规范。

## 落地

1. 一个插件 + 一张卡 + 一个意图（含 skill 与记录），硬编码跑通。
2. 抽 manifest，做第二个插件。
3. 跳转对话 + 引用胶囊 + 出口按钮。
4. 配置中心。
5. 第二个公司 profile。

## 未决

1. 新会话 vs 并入当前会话的判定规则。
2. 意图模板格式（纯 prompt / 结构化 steps / 混合）与 skill 的边界。
3. 记录粒度：一次一键一条，还是每步一条。
4. 回写权限：agent 能否直接改票、开 PR、触发发布。
5. 后台任务：App 内定时器 vs 外部 cron。

## 附：这套东西是怎么建起来的
- 造这个平台用的手法见 `docs/use-llm/vibe-coding.md`（六步骨架：mockup → DB → 流程图 → 命名 → 目录 → 分层）。
