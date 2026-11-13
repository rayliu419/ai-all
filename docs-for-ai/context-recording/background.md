# background

## 原始需求

- 在某个 repo 下，以好的方式记录上下文。
  - general 层：repo 级，全局共享。
  - per-task 层：复杂任务专属目录，记录整个实现过程背景 + 多轮讨论结论。
- 在 AGENTS.md 里记录 AI 怎么读取、更新这些内容。
- 搜索网络，看思路是否有更好的实现或补充。

## 动机（为什么需要这个约定）

- 完成复杂任务时，新 session 会忘记以前讨论过的工具、背景，需要反复重提。
- 已经给出的结论，新 session 里又要重新给一遍。
- 希望开新 session 时，模型知道"我在做哪个 task"，然后去读以前的知识。
- 这不是 skills（可复用的确定性 SOP），而是项目级 memory（随 task 演进的状态）。

## 决策 log（append-only，不重写历史）

### 2026-09-20

- Q1 交付范围：写方法论笔记 + 用 ai-all 本 repo 打样。
- Q2 general 层：`AGENTS.md`（协议，<200 行）+ `CONTEXT.md`（背景，5 节，按需加载不自动加载）。
- Q3 per-task 目录：`tasks/<slug>/`（repo 根，与代码一起版本化）。
- Q4 文件集：3 文件（`index.md` / `background.md` / `status.md`）+ `scripts/`（可选）；借 skill 结构不合并，脚本被多 task 复用 → 提升为 skill。
- Q5 更新协议：显式要求 + 触发词（结论是/决定/记一下/更新背景/记住）+ 每 ~5 轮或 session 结束前跑 3 条清单；防噪只追加、不重写。
- 参考来源：AGENTS.md 开放标准、Claude Code memory、Anthropic context engineering、GitHub Spec Kit。

### 2026-09-20（recall skill）
- 决定：把"触发项目级背景阅读"做成 recall-memory skill（`.claude/skills/`），利用 skill 的自动触发能力。
- 作用域：per-repo（随 repo 版本化）。
- 触发词单一来源：移到 skill 的 description，AGENTS.md 只留协议 + 指向 skill。
- 维护：tasks 少（<5）时手动更新 description；多了再用脚本扫描 `tasks/` 重生成。
- 分工：skill = 自动触发路径（增强），AGENTS.md 读取协议 = 兜底。

### 2026-11-13（目录改名：tasks/ → docs-for-ai/）
- 决定：任务上下文目录统一叫 `docs-for-ai/<slug>/`，弃用 `tasks/`。结构与三件套（index/background/status）不变。
- 原因：个人习惯上一直用 `docs-for-ai` 记录，`tasks/` 是本次约定的误命名。
- 范围提升：读写协议从 repo 级 `AGENTS.md` 提升为全局 `~/.pi/agent/AGENTS.md`，对所有工作目录生效；repo 级只写特化内容。
- 已迁移：`tasks/context-recording/` → `docs-for-ai/context-recording/`，`tasks/` 删除。
