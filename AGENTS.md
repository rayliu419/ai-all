# AGENTS.md

本文件是给 AI 的协议：怎么读、怎么更新本 repo 的上下文。背景内容见 CONTEXT.md，触发词见 recall-memory skill。

## 上下文读取约定

- 项目背景见 `CONTEXT.md`：需要时读，不要全文塞进每次启动上下文。
- 回忆/继续某 task 时，用 `recall-memory` skill（自动触发）；未触发时手动读 `tasks/<slug>/index.md` → `background.md` / `status.md`。

## 上下文更新约定

触发（任一）：

1. 用户显式要求（如"更新 task 上下文 / 记录一下 / 记到 background"）。
2. 命中触发词（清单见 `recall-memory` skill 的 description）。
3. 每 ~5 轮对话，或 session 结束前、`/compact` 前。

执行 3 条清单：

1. 有新决策/结论/事实？→ append 到 `tasks/<slug>/background.md`（带日期，精炼，不整段抄对话）。
2. `status.md` 还反映当前状态吗？
3. `index.md` 是否缺新文件/新脚本？

防噪：只记结论不记流水账；已有条目只追加、不重写。

## 目录约定

- `tasks/<slug>/`：
  - `index.md` — 入口 + 索引（有哪些资料/脚本、何时跑）
  - `background.md` — 原始需求（上半）+ 决策 log（下半，append-only，带日期）
  - `status.md` — 当前状态 + 下一步 + 剩余
  - `scripts/` — 确定性脚本（可选）
- 判定阈值：跨多 session、多轮讨论、或实现周期 >1 天的任务才建目录；简单任务不建。
- 脚本被多个 task 复用 → 提升为 skill。
- 新建 `tasks/<slug>/` 时，同步把 slug + 触发词加进 `recall-memory` skill 的 Active tasks。
