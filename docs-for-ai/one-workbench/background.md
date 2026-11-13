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
