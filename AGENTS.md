# AGENTS.md（ai-all 仓库层）

通用协议见全局 `~/.pi/agent/AGENTS.md`（上下文分层、docs-for-ai 结构、读写时机都在那里）。
本文件只写 **本 repo 特有** 的部分。

## 本 repo 的上下文位置

- 项目背景：`CONTEXT.md`（需要时读，不自动全量加载）。
- 任务上下文：`docs-for-ai/<slug>/`（三件套 `index.md` / `background.md` / `status.md`，可选 `scripts/`）。
- 触发词 / slug 路由：`.claude/skills/recall-memory/SKILL.md` 的 Active tasks 清单。

## 本 repo 额外约定

1. **区分两种产物**：`docs-for-ai/` 是给 AI 续接工作的上下文；`docs/<topic>/<note>.md` + `.html` 是给人读的成稿笔记。不要把成稿笔记写进 `docs-for-ai/`。
2. md 是 LLM 源，html 是阅读版；改 md 后同步重新生成对应 html，且**不修改**原 md。
3. 数学公式用 LaTeX（html 用 KaTeX）；数学图的图用 matplotlib 生成，不用 ASCII art。
4. 新增笔记后记得更新 `docs/index.html`。
5. 新建 `docs-for-ai/<slug>/` 时，同步把 slug + 触发词加进 `recall-memory` skill 的 Active tasks。
