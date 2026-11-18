# docs-for-ai/one-workbench

把"每到一个公司就搭一个 workbench"产品化。原型是 **CouWork**：插件化的个人工作站，agent 只是插件之一。

## 资料索引

- `design.md` — **v2 工程细节**（插件 manifest、七插件六页面、票聚合根、四底座、进程模型、协议硬约束、路线、未决）；**§8 附录 A** = dsh 的 UI Slot 清单（侧栏 / main / 右侧栏 / 对话节点 / 设置 / 插件页）+ 权威 catalog 拿法；**§9 附录 B** = 押 dsh 时的 manifest 设计（client/host 拆分、字段→槽位映射、M0–M4）
- `background.md` — 原始想法 + 决策 log（含与 `rebuild-workstyle-with-llm.md` 的关系）
- `status.md` — 当前状态 + 下一步 + 待定问题
- `scripts/` — 暂空
- `../../docs/use-llm/assets/one-workbench.drawio` — 架构图源文件（draw.io 可编辑，导出 page1–5.svg）
- `../../docs/use-llm/assets/mock-*.svg` — UI 原型源文件（手写矢量，可直接导入 draw.io / Figma；改完用 Chrome headless 截图自检）

## 对外产出（人读）

- `docs/use-llm/one-workbench.md` / `.html` — 成稿章节：OneWorkbench，一个插件化的桌面工作台（原型 CouWork）
- `docs/use-llm/assets/mock-1-workbench.svg` / `mock-2-run-to-chat.svg` / `mock-3-config-approval.svg` — 三张带槽位编号的界面原型（图 6–8）
- `docs/use-llm/rebuild-workstyle-with-llm.md` / `.html` — 上游愿景（workbench 那一节已抽出，只留指路）

## 外部参考

- 想法源头：`docs/use-llm/rebuild-workstyle-with-llm.md`（build workbench + build tools）
- **dsh（第二内核候选，2026-11 起）**：`https://github.com/deepseek-ai/deepseek-harness`（MIT，developer preview）
  - `docs/architecture.md` — 插件树 / profile+bundle+patch / seam 三角 / 事件三分 / 扩展点表（答“新行为放哪里”那张表）
  - `docs/subsystems/conversation.md` — ConversationNodeDefinition / View target / Group definition（自定义看板视图必读）
  - `docs/defensive-patterns/client-components.md` + `docs/subsystems/slots.md` — Slot 注册与客户端组件约束
  - `docs/cookbook/adding-a-settings-card.md` — Config schema + 配置页 + client half 打包（`dsh.client`）
  - 同构参考实现：`ScarecrowFu/dsh-laofu-workbench`（内核 + 能力包 SDK + 锁上游）；UI 参考：`Aisland-SJL/dsh-worktable`（控制室 + 分屏 + overlay seat）
- pi 内核文档（本地安装）：`~/.pi/agent/install/releases/1.2.0/node_modules/@earendil-works/pi-coding-agent/docs/`
  - `rpc.md` / `rpc-commands.md` / `json.md` / `rpc-extension-ui.md` — 协议契约（写代码必读）
  - `mcp.md` — MCP 配置、exposure、OAuth
  - `configuration.md` — `PI_CODING_AGENT_DIR` 等目录与环境变量（profile 隔离的基础）

## 何时看哪个

- 要动手写代码 → `design.md` §1 插件 manifest + §3 进程模型（§5 是查漏用的协议硬约束）；**若押 dsh → §8 附录 A 的 Slot 清单 + §9 附录 B 的 manifest 设计**
- 要接公司平台 → `design.md` §2 四个底座 + §4 profile
- 要回忆定位为什么变了 → `background.md` 2026-11-13（原型截图修正）
- 要回忆为什么这么定 → `background.md` 决策 log
