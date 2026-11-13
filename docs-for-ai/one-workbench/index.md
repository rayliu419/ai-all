# docs-for-ai/one-workbench

把"每到一个公司就搭一个 workbench"产品化。原型是 **CouWork**：插件化的个人工作站，agent 只是插件之一。

## 资料索引

- `design.md` — **v1 工程细节**（插件 manifest、七插件六页面、票聚合根、四底座、进程模型、协议硬约束、路线、未决）
- `background.md` — 原始想法 + 决策 log（含与 `rebuild-workstyle-with-llm.md` 的关系）
- `status.md` — 当前状态 + 下一步 + 待定问题
- `scripts/` — 暂空
- `../../docs/use-llm/assets/one-workbench.drawio` — 三张图的源文件（draw.io 可编辑）

## 对外产出（人读）

- `docs/use-llm/one-workbench.md` / `.html` — 成稿章节：OneWorkbench，一个插件化的桌面工作台（原型 CouWork）
- `docs/use-llm/rebuild-workstyle-with-llm.md` / `.html` — 上游愿景（workbench 那一节已抽出，只留指路）

## 外部参考

- 想法源头：`docs/use-llm/rebuild-workstyle-with-llm.md`（build workbench + build tools）
- pi 内核文档（本地安装）：`~/.pi/agent/install/releases/1.2.0/node_modules/@earendil-works/pi-coding-agent/docs/`
  - `rpc.md` / `rpc-commands.md` / `json.md` / `rpc-extension-ui.md` — 协议契约（写代码必读）
  - `mcp.md` — MCP 配置、exposure、OAuth
  - `configuration.md` — `PI_CODING_AGENT_DIR` 等目录与环境变量（profile 隔离的基础）

## 何时看哪个

- 要动手写代码 → `design.md` §1 插件 manifest + §3 进程模型（§5 是查漏用的协议硬约束）
- 要接公司平台 → `design.md` §2 四个底座 + §4 profile
- 要回忆定位为什么变了 → `background.md` 2026-11-13（原型截图修正）
- 要回忆为什么这么定 → `background.md` 决策 log
