# background

## 原始需求（用户口述，2026-11-13）

开发 OneWorkbench 期间积累的 vibe coding 技巧，共 6 条：

1. 让 AI 出 mockup。
2. 让 AI 根据功能做 db 的设计。
3. 让 AI 出流程图解释。
4. 让 AI 做好函数的命名。
5. 定好开始时的目录结构。
6. 定好系统的层次。

问题：单独放一篇笔记，还是合并到已有笔记？

## 决策 log

### 2026-11-13

- **单独成篇**（`docs/use-llm/vibe-coding.md`），不并进 `best-practices.md`：
  - 它是**有顺序的一套骨架**，合并会被摊平成 bullet，丢掉「顺序即成本序」这个核心。
  - `harness.md` 管「让模型稳定」，`best-practices.md` 管「日常技巧」，本篇管「建系统时先固定哪六个形状」，是第三个维度。
- 在 `best-practices.md` 末尾加指针（合并入口），在 `one-workbench.md` 末尾加反向引用（实践出处）。
- 内容增强（超出原始 6 条的部分）：
  - 统一主张：**vibe coding 快在「改形状便宜」**，所以形状必须在写实现前定。
  - 每步补齐「产出物文件名 / 验收标准 / 为什么贵」。
  - 顺序依据：从「人一眼能判断」到「只能靠推演判断」。
  - 反模式 4 条 + 与其它笔记的关系表。
- 图：drawio 一页（`assets/vibe-coding.drawio` → `vibe-coding.svg`），展示六步 + 成本递增。
