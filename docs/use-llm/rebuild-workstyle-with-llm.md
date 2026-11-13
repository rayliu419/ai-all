## goal 
- 随着llm的普及，要改变工作的方式。

### build tools 
- 可以使用AI大量的build命令行工具。
  - 最好是linux那样，可以做成管道式的。
- workbench可以选择调用这些cli，也可以手动运行。

### build workbench → OneWorkbench
- 把常用操作聚合成一个入口（而不是散落的一堆命令）。
- 这一半已独立成章：**`docs/use-llm/one-workbench.md`** —— 形态是桌面 App（Electron + pi 内核 + MCP 打通公司平台），公司差异收进可替换的 profile。
- 核心关系：本篇负责「让 LLM 把造工具变便宜」，OneWorkbench 负责「把造出来的能力聚合成日常入口」。
