---
name: recall-memory
description: 回忆本 repo 的项目级 memory（项目背景 + 以前讨论过的结论）。当用户提到之前讨论过的 task/项目、想继续某任务，或命中触发词（结论是 / 决定 / 记一下 / 更新背景 / 记住 / 继续 / 回忆 / 上次 / 背景 / OneWorkbench）时触发。
---

# Recall Project Memory

## 何时触发

- 用户提到本 repo 的某个 task、项目背景，或以前讨论过的结论。
- 触发词：结论是 / 决定 / 记一下 / 更新背景 / 记住 / 继续 / 回忆 / 上次 / 背景。

## Active tasks（触发词 → 目录）

- `context-recording` — 在 repo 里记录上下文的约定（项目级 memory）；触发词：上下文记录 / context recording / 项目级 memory / docs-for-ai。
- `one-workbench` — OneWorkbench（pi 内核 + Electron 桌面 + 公司 profile）；触发词：OneWorkbench / workbench / 桌面 App / 公司平台打通。
- `vibe-coding` — 用 AI 造系统的六步骨架；触发词：vibe coding / 造系统 / mockup / 六步 / 目录结构 / 分层。

## 怎么读

1. 先读 `CONTEXT.md` 了解项目背景。
2. 匹配到某 task 后，读 `docs-for-ai/<slug>/index.md` 定位资料 → `background.md`（回忆需求 + 决策 log）→ `status.md`（当前状态）。
3. 未匹配到具体 task 时，只读 `CONTEXT.md`。

## 怎么写

- 通用读写协议见全局 `~/.pi/agent/AGENTS.md`，本 repo 特化约定见 `AGENTS.md`。
- 核心动作：新结论 append 到 `docs-for-ai/<slug>/background.md`（带日期），刷新 `status.md`。
- 新建 task 目录时，把 slug + 触发词补进上面「Active tasks」。
