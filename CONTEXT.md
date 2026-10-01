# CONTEXT.md

本 repo 的背景知识。只放"从文件里看不出来的知识"，需要时读，不自动加载。

## 这是什么项目

- ai-all 是个人知识库：以 .md 记录核心知识（LLM 源），生成 .html 供人阅读。
- 通过 GitHub Pages 发布：https://rayliu419.github.io/ai-all/

## 目录结构

- `docs/<topic>/<note>.md` + 同名 `.html`：每个主题一个子目录，一篇笔记一对文件。
- `docs/index.html`：总索引（book-style，按章节列出各笔记）。
- `AGENTS.md`：给 AI 的协议（怎么读/更新上下文）。
- `tasks/<slug>/`：复杂任务的专属上下文目录。

## 关键约定

- md = LLM 源，记录简洁核心知识；html = 人类阅读，用例子、图表、更好排版丰富内容。
- 生成 html 时**不修改**原 md 文件。
- 数学公式用 LaTeX（html 用 KaTeX），矩阵用 `\begin{bmatrix}`，不用 HTML 表格或 `[[...]]` 模拟。
- 数学类笔记的图用 matplotlib 生成，不用 ASCII art。
- md 里 `enrich: {xxx}` 标注 = html 应在该点展开为例子或图。
- html 样式：bg `#f5faf6`、卡片 `#e8f5ec`、边框 `#c3dbcc`、文字 `#2d3a31`；非 index 页用 `.toc` 目录。

## 重要决策（带日期）

- 用 GitHub Pages 发布（README 记录）。
- （待补充：本 repo 的历史决策按需追加到这里。）

## 坑

- `rebuild-workstyle-with-llm.html` 已存在但尚未加入 `docs/index.html`。
- 每篇笔记的 md 与 html 需要手动保持一致；改 md 后需重新生成对应 html。
