## goal
- 在某个 repo 下，以好的方式记录上下文，让 AI 能可预测地读取和更新，避免每个 session 都重新解释背景。

## 核心主张
- context 是有限的注意力预算，只放代码里看不出来的知识。
- 约定分两层：general（repo 级，全局共享）+ per-task（复杂任务级，专属背景）。

## general 层
- AGENTS.md（repo 根）
  - 只放"协议"：怎么读、怎么更新、指向哪。保持精简（<200 行）。
- CONTEXT.md（repo 根）
  - 只放"背景"：这是什么项目 / 目录结构 / 关键约定 / 重要决策(带日期) / 坑。
  - 按需加载，不自动塞进启动上下文（just-in-time）。
- 原则：从代码里能看出来的不要写。

## per-task 层
- 目录：`tasks/<slug>/`（repo 根，与代码一起版本化）。
- 判定阈值：跨多 session、多轮讨论、或实现周期 >1 天的任务才建目录。简单任务不建。
- 结构
  - `index.md` 入口 + 索引（有哪些资料/脚本、何时跑）。
  - `background.md` 上半=原始需求(会演化)；下半=append-only 决策 log(带日期，不重写历史)。
  - `status.md` 当前状态 + 下一步 + 剩余。
  - `scripts/` 确定性脚本（可选）。
- 与 skill 的关系：借结构不合并。
  - skill 是 general 的：全局、可复用，靠描述/名字自动触发。
  - task 目录是项目级/repo 级 memory：基于该项目的背景 + 以前讨论过的结论。
  - 触发词既能触发 skill，也能触发 memory 的读（回忆以前结论）和写（更新决策 log）。
  - 脚本被多个 task 复用 → 提升为 skill。

## recall skill（自动触发回忆）
- 项目级 memory 没有自动触发能力，skill 有。
- 用一个 `recall-memory` skill 承载触发词 + active task 列表（写进 description），body 写"怎么读"。
- 触发词/task 映射只写在 description（单一来源），AGENTS.md 只留协议 + 指向 skill。
- 维护：tasks 少时手动更新 description；多了再用脚本扫描 `tasks/` 重生成。
- 分工：skill = 自动触发路径（增强），AGENTS.md 读取协议 = 兜底。

## 读写协议（写进 AGENTS.md）
- 触发（任一）
  1. 用户显式要求（"更新 task 上下文 / 记录一下"）。
  2. 触发词：见 recall-memory skill 的 description（例：结论是 / 决定 / 记一下 / 更新背景 / 记住 / 继续 / 回忆）。
  3. 每 ~5 轮对话，或 session 结束前、/compact 前。
- 读：命中触发词或开新 session 时，触发 `recall-memory` skill 回忆（读 `index.md` 定位 task → `background.md`）；未触发时手动读。
- 执行 3 条清单
  1. 有新决策/结论/事实？→ append 到 background.md（带日期，精炼，不整段抄对话）。
  2. status.md 还反映当前状态？
  3. index.md 是否缺新文件/新脚本？
- 防噪：只记结论不记流水账；已有条目只追加、不重写。

## 参考
- AGENTS.md 开放标准：https://agents.md/
- Claude Code memory（MEMORY.md 索引 + 按需 topic 文件）：https://code.claude.com/docs/en/memory
- Anthropic context engineering（注意力预算 / just-in-time / structured note-taking）：https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- GitHub Spec Kit（specs/<slug>/ 每 feature 一目录）：https://github.com/github/spec-kit
