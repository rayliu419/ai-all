# OneWorkbench 设计（v2 + 附录 A）

> v1 遗留问题：把「agent 是插件之一」写对了，但没把**核心**写出来。
> v2 的核心判断：**产品 = 桌面总入口 + 一键 AI**。UI 是壳，一键才是功能。
> v2.1（2026-11-18）：新增 **§8 附录 A — dsh 的 UI 扩展位（Slot 清单）**，对应「第二内核候选」；§3 末补了 dsh 侧对应物。
> v2.2（2026-11-18）：新增 **§9 附录 B — 插件 manifest 的 dsh 版**（client 半 / host 半拆分、字段→槽位映射、槽位分级、PEPS-5129 例子、M0–M4 切片）。
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

> **若改押 dsh**：这套接口的对应物是 `ctx.agents`（驱动）+ `agent.inject()`（灌上下文包）+ `session/event`（渲染）；UI 扩展位见 **附录 A（§8）**。

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

## 8. 附录 A：dsh 的 UI 扩展位（Slot 清单）

核对依据：dsh `master` 分支 `docs/subsystems/slots.md`（2026-11-18）+ `packages/client/*/README.md`。preview 会变，**动手前以 catalog 复核**（见本节末）。

### 8.1 三条通用机制

1. **注册 = effect**。`ctx.slots.register()` / `ctx.sidebarRightTabs.register()` 都是 Cordis effect，插件 dispose 时贡献撤回、**递归塌掉它声明的子槽**。往别人的槽位贡献必须用 `ctx.slots.inject(key, cb)`（只在 owner 声明存活期间跑，owner 重新挂载会再跑一次）。
2. **五 cardinality × 三 scope**。cardinality：`single`（一个中选者，优先级高者渲染）/ `list`（必带 `id`，按 `order` 排序）/ `keyed`（owner 派发 `entryKey`）/ `chain`（各自 `select(owner)`，首个非空渲染）/ `hoc`（层层包裹 owner 内容）。scope：`root` / `session-maybe` / `session`（后者要求已绑定的 Session）。
   - **`single` 和已占用的 `keyed` 是替换点**；加法扩展要用新的 `list`/`hoc` id 或空着的 key。
3. **组件输入走 inject 面，不走全局 store**。`inject()` 返回纯数据 + 回调，其中保留的 `hooks` 分隔区会被渲染器变成 `useXxx(selector)`，按字段订阅（否则长会话 streaming 下掉帧）。框架标准 hooks：`useSessions` / `useSession` / `useProjection` / `useAccess` / `useSessionStatus` / `useWorkspaces` / `usePanelInfo` / `useConversation` / `useInput` / `inputActions` / `useChat` / `useTrajectory`。

### 8.2 与 OneWorkbench 直接相关的槽位

| 用途 | 槽位 | 类型 | 归属包 | 备注 |
| --- | --- | --- | --- | --- |
| 侧栏入口 | `sidebar.panellist` | list / root | ui-sidebar | 图标+`label`+`order`；**同一 `id` 必须在 `main` 也注册**，否则选中即抛错 |
| 侧栏行尾 | `sidebar.panellist.trailing` | list / root | ui-sidebar | 非交互角标（计数/状态点），收 `wide` + `active` |
| 侧栏 More 菜单 | `sidebar.panellist.actions` | list / root | ui-sidebar | 面板多时的收纳行 |
| 侧栏品牌位 | `sidebar.brand.mark` / `.name` | single / root | ui-sidebar | 公司 Logo |
| 侧栏区域 | `sidebar.workspaces` / `sidebar.settings` | 子槽 | ui-workspace / ui-settings-general | 会话列表区 / 底部设置 |
| 会话行菜单 | `sidebar.workspaces.session.menu.item` | — | ui-workspace | 会话右键/更多项 |
| **面板主体** | `main` | keyed / root | ui-layout | `main[key=<panelId>]` → 我们的看板/插件页挂这里 |
| 右侧栏 tab | `sidebar.right.pane.tab` | keyed | ui-sidebar-right | 先 `ctx.sidebarRightTabs.register({ id, kind, patterns, canOpen, title, guide })`，再注册 body；`dsh-web-vscode` 就是这么塞 code-server |
| 右侧栏引导 | `sidebar.right.tab.guide.entry` / `.guide.actions` | keyed / list | ui-sidebar-right | 空右侧栏的卡片入口 |
| **对话视图目标** | `conversation.view` | keyed | ui-conversation | 现有 `chat` / `trajectory`；**新增「看板」= 新 key + 配套 View Definition（数据侧 builder）** |
| **对话节点** | `conversation.chat.node` | keyed dispatch | ui-chat | key 现有 `user` / `steering` / `assistant-step` / `tool-call` / `command-input` / `command` / `turn-tail`；**自定义卡片 = 新 key + `ConversationNodeDefinition`** |
| **工具调用卡片** | `tool.call.toolview` | keyed by 工具名 | ui-tool | 「一键」产出的结果卡片可长这里（按工具名分派） |
| 回合尾部 | `conversation.chat.turnTail` / `conversation.chat.assistant-actions` | — | ui-chat | 出口按钮（新建待办 / 回写）放这 |
| 代码块 | `conversation.chat.markdown.fence` | hoc / keyed by 语言 | ui-chat | 自定义渲染（diff 卡、日志高亮） |
| 会话头 | `conversation.session.header.actions` / `.utilities` / `.corner` / `.lineage` | list / — | ui-conversation | 引用胶囊、会话级动作 |
| View 切换 | `conversation.session.header.views.actions` | list / root | ui-conversation | View tabs 的 More 菜单 |
| **Session 详情面板** | `conversation.session.panel.section` (+ `.section.actions` keyed, `.panel.environment.row` list) | list / session | ui-session-panel | 「Session 详情」插件型面板 |
| 输入区工具条 | `conversation.composer.bar` 下的 `conversation.input.left` / `.right` / `.attachments` / `.model` / `.permission` / `.plan` / `.overlay` | — | ui-conversation | 一键入口可以放 `.right` |
| 输入区动作 | `conversation.input.activity` | single | ui-conversation | 模型选择器与 Send 之间的一个动作 |
| 输入区停靠 | `conversation.composer.dock` / `conversation.input.dock`(queue) | — | ui-conversation | 队列 / 待发消息 |
| 审批 | `conversation.approval.detail` | — | ui-approval | 回写确认（开 PR / 改票） |
| 计划审批 | `conversation.plan-review.actions` | — | ui-plan | 计划批准按钮 |
| **空白新会话页** | `conversation.hero.frame`(hoc) / `.brand.mark` / `.workspace` / `.agentPreset` / `.options` | — | ui-conversation | 总入口的「⌘K + 卡片区」最好的落点 |
| **设置页** | `settings.section` + `settings.section.view`(Factory) + `settings.section.icon`(inject 同 id) | — | ui-settings / ui-settings-general | 配置中心；图标靠 `inject('settings.section.icon')` 配同 id |
| 设置外围 | `settings.launcher` / `settings.notice` / `settings.onboarding` | single | ui-settings | 侧栏底部入口 / 横幅通知 / 引导步骤 |
| 插件页详情 | `plugins.detail.actions` / `.badge` / `.section` | list | ui-plugin-manager | 收 `subject`：`{kind:'bundle'|'row'|'item'}`，没内容返回 null |
| 插件页其它 | `plugins.row.config` / `plugins.add.actions` / `plugins.bundle.config` / `plugins.bundle.activation` | — | ui-plugin-manager | 配置行 / 安装菜单 / 启用后引导 |

### 8.3 两个必须记住的坑

- **面板要注册两处**：`sidebar.panellist`（图标 + 文案，进左侧导航）**和** `main`（keyed by 同一个 `id`，进主体）。漏了后者，用户点一下就抛「selecting a missing main entry」。
- **别抢渲染位置**：`single` 与已占用的 `keyed` 是替换语义。我们要加的是新 `id` / 新 key，不是覆盖 chat / trajectory。

### 8.4 权威清单怎么拿（别靠手抄）

- 源码 catalog：`packages/extensions/cordis-client-runner/src/client/slot-catalog.ts` —— 由 `pnpm run gen-client-catalog` 从 `SlotMap` 声明 + `slots.register()` 调用点生成，逐 key 列出 cardinality / scope / owner props / standard props / 当前占用者 / 声明归属 / 替换风险。
- 运行时查活树：`cordis_inspect what:"client"`（可加精确 key）。
- 文档：`docs/subsystems/slots.md`（含完整 Conversation 层级树）、`docs/defensive-patterns/client-components.md`（评审红线）。

## 9. 附录 B：插件 manifest 的 dsh 版（从槽位反推）

> 目标：§2 的 manifest 是**产品视角**（一个 `definePlugin` 描述全部）。押 dsh 时要把它拆成**两半 + 一个 profile**，因为 dsh 里 UI、能力、配置是三套不同的注册面，且它们共享 Cordis effect 生命周期。

### 9.1 三条反推结论

1. **manifest 必须拆成 client 半 / host 半**。`sidebar`、`page`、`cards` 的渲染是浏览器侧（`ctx.slots.register`）；`intents` 的执行、`tasks`、`credentials` 读出是主机侧（`ctx.agents` / `ctx.jobs` / credentials seam）。两半用**同一份 manifest 数据的类型**共享（`import type`），但**不在同一进程注册**。
2. **manifest 里不许有公司参数**。端点、字段映射、实体对齐规则、role 名一律进 profile 的 `cordis.patch.yml`；manifest 只声明"我需要一个名为 `ci` 的数据源"。否则「换公司只换 profile」当场破功（这是 §7 未决第 1 条的答案）。
3. **`intents` 要双注册**：一次作为 **tool**（模型可自己调，`ctx.tools`，`exposure` 用 `deferred`/`codemode` 省 prompt 预算），一次作为**人可点的动作**（client 按钮 → host route → 同一个执行函数）。这样"人点按钮"和"agent 自己调"天然是同一份能力，不会漂移。

### 9.2 manifest 类型草稿

```ts
// 共享类型：client 半与 host 半都 import type 这一份
export interface OnePluginManifest {
  id: string                  // = 面板 id，必须与 main 的 key 一致
  title: string
  sidebar: { group: string; order: number }
  credentials: CredRef[]      // 只声明"需要什么"，具体值在 profile
  datasources: DataSourceRef[]// 只声明名字与形状；实现由 profile 绑 MCP / CLI / HTTP
  tasks: TaskSpec[]           // → ctx.jobs
  cards: CardSpec[]           // 卡片形态（字段级），由面板组件渲染
  intents: IntentSpec[]       // → ctx.tools + host route + 卡片按钮
  page: PanelComponent        // → main[key=id]
  surfaces?: {                // 可选扩展位（见 9.4 分级）
    badge?: boolean           // sidebar.panellist.trailing
    runNode?: boolean         // conversation.chat.node 的 one-run key
    toolView?: boolean        // tool.call.toolview（按工具名）
    view?: boolean            // conversation.view 新 key（成本最高）
    composerAction?: boolean  // conversation.input.right
  }
}

export interface IntentSpec {
  id: string
  label: string
  when: string                       // 出现条件（卡片状态表达式）
  promptTemplate: string             // 意图模板（资产，版本化）
  skill: `${string}@${string}`       // dev-flow@v3
  outputShape: 'patch' | 'steps' | 'verdict' | 'checklist'
  allowedWrites: ('comment' | 'pr' | 'status')[]
  bundle: (snapshot: ViewSnapshot) => ContextBundle  // 纯函数，可单测
}
```

### 9.3 字段 → dsh 落点

| manifest 字段 | 哪一半 | dsh 落点 |
| --- | --- | --- |
| `id` / `title` / `sidebar` | client | `ctx.slots.register({ name: 'sidebar.panellist', id, order, label })` + 组件里用 `usePanelInfo()` 读选中态 |
| `page` | client | `ctx.slots.register({ name: 'main', key: id }, Panel)` —— **两处同 id**，漏了会抛 "selecting a missing main entry" |
| `cards` | client | 面板组件内部渲染；卡片状态来自 run 投影（`useProjection` / 自定义 projection） |
| `intents`（人点） | client→host | 卡片按钮 → host route（owner 校验）→ `ctx.agents` 创建/驱动 session，首条消息 = 模板 + bundle |
| `intents`（agent 调） | host | `ctx.tools` 注册同名工具（`exposure: 'deferred'`），execute 走同一个函数 |
| 上下文包注入 | host | `agent.inject()`（落进下一个被接纳的 request）；新鲜度作为文本块一起进 |
| `tasks` | host | `ctx.jobs` 注册；UI 侧 `ui-jobs` 插件自带展示，不用自己写 |
| `credentials` | host+client | Config schema + `role('secret')`；值放 credentials seam，插件只拿引用 |
| `datasources` | host | 自己的 service（如 `ctx.oneData`），注册表在 base profile 里，插件按名取 |
| run 记录 | host | 定义 `one/run-start` / `one/run-step` / `one/run-end` durable 事件 + `SessionEventMap` merge；落公司库 = 实现 `SessionPersistence` 或注册 projection |
| `surfaces.badge` | client | `sidebar.panellist.trailing`（非交互，收 `wide`/`active`） |
| `surfaces.runNode` | client+host | 事件族 + `ConversationNodeDefinition`（key `one-run`）+ `conversation.chat.node` 渲染器 |
| `surfaces.view` | client+host | **数据侧** View Definition（builder，新 target）+ **UI 侧** `conversation.view` 新 key |
| `surfaces.composerAction` | client | `conversation.input.right` |
| 面板内跳对话 | client | `useSessions` / `useSessionAccess` + layout selection（具体 API 见 `ui-layout` / `ui-session` README，待核） |

### 9.4 槽位分级（先做什么、什么别碰）

| 级别 | 槽位 | 理由 |
| --- | --- | --- |
| **必需** | `sidebar.panellist` + `main` | 没有这两处，插件在 UI 上不存在 |
| **必需（有任务/凭证时）** | `settings.section`（+ `settings.section.icon` 同 id）、`ctx.jobs` | 配置中心与后台任务是插件四要素之一 |
| **强烈建议** | `sidebar.panellist.trailing` | 角标承载"待处理数 / 数据新鲜度"，是产品辨识度所在 |
| **建议（第二阶段）** | `conversation.chat.node` + `tool.call.toolview` | 让一键的产出留在对话里可回看 |
| **可选（成本高）** | `conversation.view` | 要同时写数据侧 builder + 事件契约；先做 `runNode` 就够 |
| **可选** | `conversation.input.right`、`conversation.hero.*` | 输入区一键 / 空白页入口 |
| **别碰** | 任何 `single` 槽位（`sidebar.brand.*` 除外）、已占用的 `keyed`（`chat` / `trajectory` / 内置工具名） | 那是**替换**语义，会把上游或其他插件挤掉 |

### 9.5 例子：「开发任务」插件（PEPS-5129）

```ts
export const devTasks: OnePluginManifest = {
  id: 'dev-tasks',
  title: '开发任务',
  sidebar: { group: '开发测试', order: 20 },
  credentials: ['couest_token', 'jira_oauth'],
  datasources: [{ name: 'jira' }, { name: 'gh' }, { name: 'couest' }],
  tasks: [
    { id: 'importRegistrations', every: '30s' },
    { id: 'refreshViewed', every: '5m' },
  ],
  cards: [
    { kind: 'ticket', fields: ['status', 'verdict', 'source', 'ts', 'stale'] },
  ],
  intents: [
    { id: 'fix', label: '看看怎么修', when: 'ci==red',
      promptTemplate: '你是修复助手…{{evidence}}', skill: 'dev-flow@v3',
      outputShape: 'patch', allowedWrites: ['pr'], bundle: ticketBundle },
    { id: 'why-not-deployed', label: '为什么没部署', when: 'deploy==none&&ci==green',
      promptTemplate: '按发布链路排查…', skill: 'deploy-triage@v1',
      outputShape: 'steps', allowedWrites: [], bundle: ticketBundle },
  ],
  page: DevTasksPanel,
  surfaces: { badge: true, runNode: true },   // view: false（第二阶段再说）
}
```

### 9.6 按槽位反推的最小切片

| 里程碑 | 加什么 | 验收 |
| --- | --- | --- |
| M0 | `panellist` + `main` + 一个 `intent`（只走 host route）+ `one/run-end` 一条事件 | 点一下 → 新会话带着 bundle 跑完 → 面板上能看到这条 run |
| M1 | `settings.section`（凭证/开关）+ `ctx.jobs` + `panellist.trailing` 角标 | 关掉插件 → 入口、任务、角标一起消失 |
| M2 | `ConversationNodeDefinition(one-run)` + `conversation.chat.node` + `tool.call.toolview` | 一键的产出能在对话流里回看，且退出面板仍可见 |
| M3 | 第二个插件（复用 manifest，不改进程代码）+ 第二个 profile | 只写 manifest + patch，底座零改动 |
| M4（可选） | `conversation.view` 新 key「看板」 | 看板与对话是同一份 log 的两个视图 |

### 9.7 需要读源码才能定的四件事

1. **新建会话的 API 形状**：`ctx.agents.create()` 的签名（fork/seed 用法已在 arch.md 里见到，普通新建待核 `packages/core/agent` README）。
2. **panel 选中 → 对话跳转**的客户端 API（layout selection：`ui-layout` / `ui-session` README）。
3. **projection 注册粒度**：一个 `one.run` projection 服务 vs 每个插件各注册一份；关系到"跨插件看板"能不能做。
4. **host route 的 owner 校验约定**（`dsh-worktable` 用的是 owner-checked routes，抄它的写法比自创安全）。

