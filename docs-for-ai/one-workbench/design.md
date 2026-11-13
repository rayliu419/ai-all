# OneWorkbench 设计（v2）

> v1 遗留问题：把「agent 是插件之一」写对了，但没把**核心**写出来。
> v2 的核心判断：**产品 = 桌面总入口 + 一键 AI**。UI 是壳，一键才是功能。
> 人读成稿：`docs/use-llm/one-workbench.md` / `.html`（图源 `docs/use-llm/assets/one-workbench.drawio`）。

## 1. 核心循环（一切设计围绕它）

```
看到异常（卡片 / 行 / 曲线点）
  → 点意图（看看怎么修 / 为什么没部署 / 准备发布）
  → 系统打包 ContextBundle
  → agent 回答 / 产出 patch / 回写状态
```

四个必须先定的规格（漏一个，这个功能就退化成「聊天框」）：

### 1.1 ContextBundle（三层）

| 层 | 字段（建议） | 来源 |
| --- | --- | --- |
| Identity | ticketId, pr, branch, env, role, timePoint, viewId | 当前视图实体 |
| Evidence | failedCases[], logTail, recentDeploys[], changesInWindow[], metricSeries[], freshness | 插件缓存（不现打接口） |
| Intent | verb, expectedOutput(patch/steps/verdict/checklist), constraints | 意图模板 |

**必须传 freshness**：卡片上的「15:43 · 旧数据」要进 prompt，否则模型拿旧数据下结论。

### 1.2 意图模板（插件资产）

- 存 `intents: [{ id, label, when, promptTemplate, outputShape, allowedWrites }]`
- 版本化、可 A/B 对比，不散落在代码里
- 一张卡 2–4 个意图（不是一个「问 AI」）

### 1.3 交互形态：跳转对话（定案）

**卡片意图 → 跳转到对话页（Copilot）**。不弹窗、不抽屉、不叠加层。

时序：抓视图快照 → 组装 bundle → 选会话（默认新建）→ 首条消息 = 意图模板 + bundle（可编辑）→ 落 run 记录。

必须处理的三个问题：
- 不丢上下文：对话顶部引用胶囊（ticket / card / time / freshness），点回原卡片。
- 不串上下文：默认新建；同票同视图才允许并入当前会话。
- 不打断工作流：返回时保留滚动与筛选，卡片状态变化则刷新。

三种粒度：单卡意图 / 行级意图 / Cmd+K 全局意图（基于当前面板）。

### 1.4 执行链：意图 → skill → 记录

意图不只带 prompt，还带 `skill`（我用的 `dev-flow`）：一键后按 skill 的步骤走，不是自由发挥。

```ts
IntentSpec = {
  id, label, when,
  promptTemplate,
  skill: "dev-flow@v3",        // 规定步骤与检查项
  outputShape: "patch" | "steps" | "verdict" | "checklist",
  allowedWrites: ("comment" | "pr" | "status")[],
}
```

每次一键落一条 **run 记录**（db）：

| 字段 | 用途 |
| --- | --- |
| run_id / ts | 主键与时间 |
| feature_id | 票 / PR（"功能和意图挂起来"的关键外键） |
| view_id / intent / context_hash | 从哪个视图、哪个意图、哪份上下文发起 |
| skill + version | 走了哪套流程、哪一版 |
| session_id | 对应对话，可回看 |
| steps[] | 每步的结果与耗时（定位/复现/修复/验证） |
| output / status / cost | 产出形态、成功与否、token 花费 |

三个用途：**可追溯**（查历史）、**可统计**（哪个意图/哪步常失败）、**可复用**（第二次一键带上上次记录）。

### 1.5 结果出口（必须有）

`patch / 命令` · `状态回写（标记已处理）` · `新建待办` · `推给对话继续`。没有出口 = 解释器，不算解决问题。

## 2. 插件 manifest（v2：把 actions 换成 intents）

```ts
export default definePlugin({
  id, title,
  sidebar:   { group, order },
  credentials: ["couest_token"],
  tasks:     [{ id, every, run }],
  cards:     CardSpec[],          // 渲染什么
  intents:   IntentSpec[],        // 一键 AI 挂在哪
  page:      Component,
})
```

`intents` 是 UI 按钮与 agent 能力的**同一份数据**。

## 3. AgentBackend（可替换，但默认用 SDK）

```ts
interface AgentBackend {
  prompt(text: string, bundle: ContextBundle): Promise<void>
  abort(): Promise<void>
  on(evt: "delta" | "tool" | "done" | "error", cb): Unsubscribe
  session?: SessionHandle
}
```

| 实现 | 位置 | 用不用 |
| --- | --- | --- |
| `piSdkBackend` | Electron main 或 utilityProcess（Node） | **首选**：`createAgentSession()`，类型直通，能读 session/事件 |
| `acpBackend` | 连外部 agent（Devin） | 已在使用，作为可选后端 |
| `piRpcBackend` | `pi --mode rpc` 子进程 | 降级：要自己分帧 + 请求对账 |

SDK 注意点（写代码时会踩）：
- SDK 会话**不自动加载内置扩展**：MCP / codemode / tool_search 需显式注册到 extension factories，并 `bindExtensions()`。
- 配置目录隔离用 `agentDir`（等价于 CLI 的 `PI_CODING_AGENT_DIR`）。
- 若担心主进程稳定性，把 SDK 放进 `utilityProcess` 跑，接口照样是 AgentBackend。

## 4. 四个公共底座

1. **数据源注册表**（MCP / CLI / HTTP / DB，插件按名引用）
2. **凭证库**（keychain，插件声明依赖）
3. **后台任务调度**（App 开着才跑；错过补跑一次；插件关掉即停；保留运行记录）
4. **新鲜度缓存**（每源一份带时间戳缓存，视图不直连外部）

## 5. 技术判断

- **TS 合适**：manifest→UI→调度→MCP→agent SDK 全栈同语言，插件声明类型可被三方共享；Electron/React/MCP SDK/pi SDK/ACP 都是 TS 生态。重计算交给 Python CLI 进程。
- **Electron 合适**：需要本机凭据、文件系统、常驻快捷键，主进程就是 Node，能直接加载 agent SDK。Tauri 要多带 sidecar，不划算。
- **MCP 优先**：公司平台有 MCP 就接；没有就包薄 CLI/HTTP 客户端。
- **PTY 最后考虑**：只有 TUI/REPL 类工具才需要。

## 6. 落地（按「一键」长，不按框架长）

| 步 | 做什么 | 验收 |
| --- | --- | --- |
| 1 | 一个插件 + 一张卡片 + 一个意图（硬编码） | 连续 3 天不开原系统 |
| 2 | 抽 manifest，做第二个插件 | 不改第一个插件代码 |
| 3 | 跳转对话 + 引用胶囊 + 出口按钮 + run 记录 | 点一次有可执行结论，能回原卡，能查到记录 |
| 4 | 配置中心 | 新增数据源不改代码 |
| 5 | 第二个公司 profile | 只写插件 + 填配置 |

## 7. 未决问题

1. 新会话 vs 并入当前会话的判定规则。
2. 意图模板格式：纯 prompt / 结构化 steps / 混合。
3. 回写权限边界：agent 能否直接改票、开 PR、触发发布（建议：读自由，写需确认）。
4. 后台任务：App 内定时器 vs 外部 cron。
5. 插件边界：一插件多页面（「Perm 与 Charles」是两个东西）。
6. 「开发任务」与「Perm 与 Charles」数据重叠怎么消。
7. run 记录粒度：一次一键一条，还是每步一条（决定统计能力上限）。
