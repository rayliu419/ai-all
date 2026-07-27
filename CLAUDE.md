# ai-all 笔记规范

## 笔记风格
- 中文编写，简洁要点式
- 用 `##` `###` `####` 分层，前缀数字序号
- 每行一个要点，bullet point 不用句号结尾
- 关键结论用 `**粗体**` 或 highlight card 强调

## HTML 生成规范

### TOC (目录)
- 使用 `<div class="toc">` 容器，内含 `<ol>` + CSS counter 实现编号
- 从上到下垂直排列，每行一条
- 仅列出 `h2` 标题，每个 h2 必须有 `id` 供锚点跳转
- TOC CSS:
  ```css
  .toc { background: #e8f5ec; border: 1px solid #c3dbcc; border-radius: 8px; padding: 12px 16px; margin: 12px 0 18px; }
  .toc-title { font-weight: 600; color: #1a3a24; font-size: 1em; margin-bottom: 6px; }
  .toc > ol { margin: 8px 0 0 22px; list-style: none; counter-reset: toc; padding: 0; }
  .toc > ol > li { counter-increment: toc; margin: 4px 0; }
  .toc > ol > li::before { content: counter(toc) ". "; font-weight: 600; color: #1a4a2e; }
  .toc a { color: #236b3e; text-decoration: none; font-size: 0.92em; }
  .toc a:hover { text-decoration: underline; color: #1a4a2e; }
  ```

### 侧边栏 TOC（可选）
- 当文档较长时，TOC 可放在左侧 sticky 侧边栏，随滚动保持可见
- 使用 flex 布局：`<aside class="sidebar">` + `<main class="content">`
- CSS:
  ```css
  .page-layout { display: flex; gap: 30px; margin: 0 auto; padding: 28px 20px; }
  .sidebar { width: 200px; flex-shrink: 0; align-self: flex-start; position: sticky; top: 28px; max-height: calc(100vh - 56px); overflow-y: auto; }
  .content { flex: 1; min-width: 0; }
  ```
- 窄屏（<800px）时折叠为普通内联 TOC

### 配色
- 背景 #f5faf6，卡片 #e8f5ec，边框 #c3dbcc，文字 #2d3a31
- 暖色卡片 (.card.warm)：背景 #fdf6ec，边框 #e6d5b8

### 字体
- body: 13px/1.45, h1: 1.35em, h2: 1.2em, h3: 1.02em, h4: 0.95em
- code: 0.88em, pre: 0.8em
