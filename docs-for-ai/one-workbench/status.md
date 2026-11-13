# status

## 当前状态

- **成稿 v1 已按 CouWork 原型重写**（产品视角）：
  - `docs/use-llm/one-workbench.md` / `.html` — 插件化个人工作站；含主窗口/对话/插件页线框、票流水线 SVG、四底座、落地五步。
  - `docs/index.html` 已登记为「使用 LLM 实践」第 7 篇。
- `design.md` 重写为 v1（以原型为准），v0 的协议细节降级为「工程细节」一节。
- v0 的核心误判已修正：**agent 不是中心，插件才是骨架**；v2 再修正：**真正的功能是一键 AI，看板只是载体**。

## 下一步

0. 确认 run 记录的字段与写入时机（它是 skill 与"功能"挂钩的落点，最该先定）。

1. 先定一件最小的事：**一张卡片 + 一个意图 + 抽屉**，跑通「点一下就有可执行结论」。
2. 同时验证 `piSdkBackend` 能在 Electron（main 或 utilityProcess）里跑通一次带上下文包的 prompt。
3. 再决定 plugin manifest 的字段（intents 的模板格式是第一个要拍的）。
4. 之后才建独立仓库、拆包。

## 剩余

- 交互与图示已对齐（跳对话 + drawio 5 页）；原型截图尚未归档进 repo（现在只记录了文字事实）；图已改为 draw.io 源（assets/one-workbench.drawio）。
- 「Perm 与 Charles」与「开发任务」的数据重叠未理清。

## 阻塞

- 无。
