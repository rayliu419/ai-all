# background

## 原始需求

- 核心想法（多轮验证过）：**每到一个公司，做一个 workbench。底座是一样的——一些 infra + 把公司各平台打通。**
- 形态：以 pi coding agent 的前端 UI 为基础，其他能力用 MCP 打通，做成 **OneWorkbench**，日常工作都通过它完成。
- 技术栈：主要用 TypeScript。
- 与 `docs/use-llm/rebuild-workstyle-with-llm.md` 的关系：那篇给的是"目标"（用 AI 造 all-in-one workbench + 造管道式 CLI 工具），本 task 给的是"怎么建"。

## 已确认的方向（2026-11-13）

- 交付物：先出架构设计文档（不写代码）。
- pi 的定位：**只当内核，我们只做前端**（`pi --mode rpc` 子进程）。
- 部署形态：**桌面 App**。
- 代码位置：**独立新仓库**（不在 ai-all 里）。

## 决策 log（append-only，不重写历史）

### 2026-11-13

- 四问定调：架构文档 / pi 当内核做前端 / 桌面 App / 独立仓库。
- pi 能力调研结论（决定可行性的三条）：
  1. `pi --mode rpc` 提供完整的双向 JSONL 协议（命令 + 事件 + 扩展 UI 子协议），足以支撑一个非终端 UI。
  2. `PI_CODING_AGENT_DIR` 可覆盖 agent 配置目录 → **公司差异可以整体关进一个 profile 目录**（mcp.json / extensions / skills / prompts / AGENTS.md / auth.json）。这是"底座复用"成立的技术关键。
  3. pi 的 engines 要求 node ≥ 22.19；npm 包同时导出 `RpcClient` 与 JSON 事件类型（`JsonAgentSessionEvent`），可直接复用类型。
- 选 Electron 而非 Tauri：pi 本身是 Node 程序，Electron 主进程即 Node，省掉 sidecar/Rust 壳；代价是包体积。
- UI 不硬编码业务按钮：发布/override 一律做成 pi extension command（`/deploy`），人点按钮 = 发 `/deploy`，agent 也能自己调 —— 与"build tools / 管道式 CLI"的思路一致。
- 审批策略放在扩展里（`tool_call` handler + `ctx.ui.confirm`），RPC 会把它转成 `extension_ui_request` 让 UI 渲染卡片；UI 保持通用。
- 已识别缺口：RPC 模式下 `custom()` / 主题 / TUI 组件不可用 → 表现层完全自己拥有。
- 任务上下文目录改用 `docs-for-ai/one-workbench/`（不再用 `tasks/`）。

### 2026-11-13（文档结构：workbench 抽成独立章节）
- `rebuild-workstyle-with-llm` 只保留「为什么重造 + build tools + 指路」，其中的 workbench 概念/架构/交互/落地路径/交互式工具附录全部抽出。
- 新章节 `docs/use-llm/one-workbench.md` + `.html`：面向人的成稿（三层复用、内核选型、进程模型、协议契约、profile、扩展命令、PTY 附录、路线、风险）。
- 已更新 `docs/index.html`：使用 LLM 实践 6 篇 → 7 篇，新增第 7 条。
- 分工：`docs/use-llm/one-workbench.*` = 人读成稿；`docs-for-ai/one-workbench/design.md` = AI 续接用的工程细节 + 未决问题。

### 2026-11-13（原型截图修正：它是插件化的个人工作站）
- 看到 CouWork 原型截图后推翻 v0 的定位：**v0 把 workbench 当成「agent 的前端」，写满了 JSONL / 协议细节；实际形态是「插件化的个人工作站」，agent 只是插件之一。**
- 原型事实（来自 6 张截图）：
  - 左侧栏 6 组插件：Devin(Copilot) / 可靠性(Change history, 排查场景) / 开发测试(开发任务, Perm 与 Charles) / 常用(我的待办) / 设置(配置中心, 插件) / 调试(Session 详情)。
  - 插件 manifest 三要素：**侧栏入口 + 后台任务 + 凭证**，外加 actions；关掉插件则侧栏消失、后台任务停止。
  - 「开发任务」把一张票（PEPS-5129）串 8 阶段：建票(jira MCP) → PR(gh #7976) → 代码(gh) → CI(gh pr checks) → PERM(CouTest) → 测试(Charles+QA) → EERP → 发布(Couest)。
  - 每张卡固定五元信息：状态 / 一句话 / 来源 / 时间戳 / 旧数据标记「15:38 · 旧数据 ⟳」；卡片上有「一键 Copilot：看看怎么修」。
  - 配置中心 7 tab：MCP 13 / Skill 56 / Token 16 / 数据库 2 / 定时任务 7 / 关注的 role / 对照指标。
  - 后台任务规则（原型页脚原文）：App 开着才跑；上次没跑完就跳过；到点没开则下次打开补一次；插件关掉任务一起停。
  - 凭证共享：`devin-oauth`、`couest_token` 被多个插件复用。
- 三个反常识（写入成稿）：agent 不是中心 / 数据有新鲜度而非实时 / 不需要给每个功能单独设计 AI 交互，只需一个动作入口。
- 文档改法：重写 `docs/use-llm/one-workbench.md` + `.html`（产品视角，删掉协议细节，只留「实现注记」5 条）；`design.md` 重写为 v1（插件模型 + 四底座 + 票聚合根 + 工程细节后置）。
- 新增未决：插件边界、action 统一形态、后台任务归属、聚合层是否独立、开发任务与 Perm 插件的数据重叠。

### 2026-11-13（v2：核心是一键 AI，不是看板）
- 用户点出核心：**① 一键 AI 功能——带着常见问题直接触发对话解决；② UI 是 deepseek desktop 那种总入口。交互设计是核心。**
- v1 的偏差：把「插件 + 看板」写成了主体，一键 AI 只是插件的附属；技术默认方案错选了子进程 RPC。
- 技术修正：
  - Devin 侧用的是 **ACP**。
  - **pi 可以直接用 SDK**（`createAgentSession()`，进程内 / utilityProcess），不必自己实现 JSONL 分帧与请求对账 → 定为默认后端；RPC 子进程降级为隔离选项；ACP 作为第二个实现。
  - 抽象放接口层：`AgentBackend { prompt / abort / on / session }`，两套实现（piSdk / acp）。
  - SDK 注意：不自动加载内置扩展（MCP/codemode/tool_search 显式注册 + bindExtensions），`agentDir` 做 profile 隔离。
- TS 结论：合适。manifest→UI→调度→MCP→agent SDK 全栈同语言，类型可共享；Electron/React/MCP SDK/pi SDK/ACP 都是 TS 生态；重计算交 Python CLI。
- 图：改用 **draw.io**，源文件 `docs/use-llm/assets/one-workbench.drawio`（3 页），用桌面版 CLI 导出 `page1-3.svg` 供 html 引用：
  `drawio -x -f svg -p <0-based index> -b 12 -o pageN.svg one-workbench.drawio`
- 文档结构改为「核心一键 AI → 交互设计 → 总入口 → 插件 → 票 → 技术选型 → 复用 → 落地」。

### 2026-11-13（v3：一键 = 跳对话的卡片；意图挂 skill 并落库）
- 交互定案：**不是抽屉/弹窗，是「跳对话的卡片」**——点卡片上的意图就跳到 Copilot 对话页，上下文以引用胶囊跟过去、可点回。已删除抽屉相关的设计与线框。
- 新增关键机制（用户自研）：意图上挂 **`dev-flow` skill**，一键后按 skill 走流程，并与「功能」挂钩**产生 db 记录**（run_id / feature_id / intent / skill+version / session_id / context_hash / steps / output / status / cost / ts）。
  - 价值：可追溯、可统计（哪个意图常用、哪步常卡）、可复用（第二次一键带上次记录）。
- 图：新增两页 drawio（`总入口布局`、`一键跳对话`），替换掉手写 ASCII 线框；现有 5 页：
  page1 一键AI数据流 / page2 架构 / page3 票流水线 / page4 总入口布局 / page5 一键跳对话。
- 教训：ASCII 线框不再用于 UI 示意（用户明确要求），统一走 drawio。

### 2026-11-18（v4：dsh 作为第二内核候选，写进成稿）

- 触发：用户提出"可以基于 **DeepSeek Harness（dsh）** 为核心做定制 workbench"，要求找现实例子。
- 事实核实（GitHub API + 仓库文档，非传闻）：
  - `deepseek-ai/deepseek-harness`：MIT / TypeScript / 2026-08 开源 / developer preview；底座 Cordis（"万物皆插件"）；**无特权内核**，模型适配器、tool registry、session log、agent loop 都是插件。
  - 组合模型：`profile → bundle → cordis.patch.yml → --patch` 有序图层，按 row id 整行替换；`dsh --profile web --dump-config` 可看整棵树；base 开 config-only HMR。
  - 模板 profile：`web` / `headless` / `sdk` / `sdk-minimal` / `acp`；自带 Electron 桌面（`apps/desktop`，独占 `profiles/desktop`）。
  - seam 三角（Definition + Provider + Consumer）：fs / subprocess / sandbox / terminals / subagent / persistence 都可换。
  - UI 即插件：`ctx.slots.register` + 父级 `renderSlot` + `children` 子槽；`package.json` 的 `dsh.client` + `./client` 由 client module system 按 Loader row 下发（row 关→页面及其 slot 一起消失）；可自定义 `View Definition` / `ConversationNodeDefinition`；配置页由 `Config`(schemastery + Volatile) 生成，凭证 `role('secret')`。
  - 持久化是唯一真源："model-visible means logged"；`SessionPersistence` / `sessionProjections` 可换；session 格式版本化 + 迁移链。
- 生态实例（均为真实仓库，`dsh-plugin` topic）：
  - `Aisland-SJL/dsh-worktable`（MIT，883★）：侧栏 app drawer + 可停靠分屏 + 控制室卡片网格；控制室 = 宿主 session 快照的**纯事件镜像**（不走模型）；分屏引擎自建塞 shell overlay seat；能嵌 `dsh-travelatlas` 当 pane。截图 `docs/assets/shot-{1,2,3}`。
  - `ScarecrowFu/dsh-laofu-workbench`：**与本方案同构**——内核（DSH Profile / 浏览器壳 / 包 SDK / 桌面打包 / 上游升级）+ 可动态装卸的「场景能力包」+ 私有会员包（`editions.json`）；`UPSTREAM.lock.json` 锁上游版本；PolyForm Noncommercial。
  - `AKS1st/dock`（VSCode 式 shell，暴露 `ctx.workbench`）、`virgoC0der/dsh-plugins`（PR+Jira+Calendar 看板）、`JianwuYang/dsh-ui-kanban`、`romainrg/dsh-system-monitor`、`suifei/dsh-ai-team`（任务+验收+ledger，装在独立 profile）。
  - 壳替换证据：`anywhere-labs/dsh-desktop`、`dataelement/dsh-desktop`、`ccch1mneyyy/dsh-Go`（Android）、`dsh-TUI`。
- 结论（写进成稿 `docs/use-llm/one-workbench.md` 新章节「备选内核：dsh」+ html）：
  - 判据不是"扩展点数量"，而是**改的是内容层还是结构层**；四层空间 L0 加能力 / L1 换实现 / L2 换骨架 / L3 长生态，**L2 是分水岭**，dsh 的 L2 由官方 dogfood（一个内核 → 五种 profile）坐实。
  - 我们三条硬需求的落点已经清楚：run 记录 → durable 事件族 + projection/SessionPersistence；卡片 → Node Definition；看板 → 第三方 View target；换公司 → profile + patch；"关掉插件一起消失" → effect 自动回卷。
  - 关键洞察：**dsh 里"看板"和"对话"是同一份 durable log 的两个视图**，比 v3 的"appendEntry + 另建 db + 自渲染"结构干净。
  - 三个边界：seam 接口由别人定；模型侧工具暴露 pi 更强（exposure 五档 / prepareLoadout / reachesTools）；换壳尽头是 fork 上游。
  - 风险同一枚硬币：preview 破坏性变更 + 社区插件钉死 rc 版本 → 若押 dsh，必须自建 `UPSTREAM.lock` + 快照发布纪律。
- 未定：内核选型不投票，先做**同需求 A/B**（一张 PEPS-5129 卡片 + 一个意图 + 一条 run 记录，两个内核各写一遍；记上手时间 / 代码行数 / 要绕的点）。已写入 `status.md` 下一步。

### 2026-11-18（原型图：三张「按槽位标注」的 mockup）

- 新增 `docs/use-llm/assets/mock-1-workbench.svg` / `mock-2-run-to-chat.svg` / `mock-3-config-approval.svg`，写进成稿（md 为 `![...]`，html 为 `<figure>`，图 6–8）。
  - 图 6 主窗口：`sidebar.brand.*` / `main[key=dev-tasks]` / `sidebar.panellist` / `.trailing` / `sidebar.settings` / IntentSpec（双注册）/ run 投影 / 8 阶段聚合。
  - 图 7 一键后的对话：引用胶囊（`conversation.session.header.actions`）/ `conversation.view` / `conversation.chat.node` 的 `one-run` / `conversation.chat.turnTail` / `tool.call.toolview` / `conversation.session.panel.section` / `conversation.input.right`。
  - 图 8 配置与审批：`settings.section` + `settings.section.icon` / 数据源绑定属 profile patch / `Config`+`role('secret')` / `ctx.jobs` / `conversation.approval.detail`。
- **画法决定（修正旧约定）**：此前记录"UI 示意统一走 drawio"。这次改用手写矢量 SVG，理由：mockup 需要精确的编号标注 + 可读小字 + 不依赖 GUI，且 SVG 可直接导入 draw.io / Figma 编辑。**旧约定继续约束架构图（page1–5 仍由 one-workbench.drawio 导出），UI mockup 走手写 SVG。**
- 校验方式（可复用）：`xml.etree` 验 XML → Chrome headless `--screenshot --window-size=<w>,<h>` 出图 → 人眼查溢出/遮挡。已修三类问题：文字超出卡片、编号压住文字、编号落在卡片边上。
