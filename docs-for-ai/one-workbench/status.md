# status

## 当前状态

- **成稿 v5**（2026-11-18）：dsh 章节加「界面原型」小节，三张带槽位编号的 mockup（图 6 主窗口 / 图 7 一键后对话 / 图 8 配置与审批），md + html 同步；画法改为手写矢量 SVG（架构图仍走 drawio）。
- **design.md v2.2**（2026-11-18）：新增两个附录——**§8 dsh UI Slot 清单**（29 个扩展位 + 三条通用机制 + 权威 catalog 拿法）、**§9 manifest 的 dsh 版**（client/host 两半拆分、字段→槽位映射、槽位四级分级、PEPS-5129 例子、M0–M4 切片）。
- 两条关键结论已进 design.md：① **manifest 里不许有公司参数**（否则「换公司只换 profile」破功），端点/字段映射/role 全进 `cordis.patch.yml`；② **intents 要双注册**（`ctx.tools` 给 agent 自己调 + host route 给人点，同一个执行函数）。
- **成稿 v4**：新增「备选内核：dsh（DeepSeek Harness）」一节（四层可扩展性 / UI 即插件 / 映射表 / 现成例子 / 三条边界 / 内容层 vs 结构层判据），md 与 html 已同步；TOC 9 → 10 条。
- 内核从单一「pi SDK」变为**两个候选**：pi（稳、契约细、工具暴露设计更成熟）vs dsh（无特权内核插件树、profile+patch 图层、UI 即插件；代价是 preview 期破坏性变更）。
- **成稿 v1 已按 CouWork 原型重写**（产品视角）：
  - `docs/use-llm/one-workbench.md` / `.html` — 插件化个人工作站；含主窗口/对话/插件页线框、票流水线 SVG、四底座、落地五步。
  - `docs/index.html` 已登记为「使用 LLM 实践」第 7 篇。
- `design.md` 重写为 v1（以原型为准），v0 的协议细节降级为「工程细节」一节。
- v0 的核心误判已修正：**agent 不是中心，插件才是骨架**；v2 再修正：**真正的功能是一键 AI，看板只是载体**。

## 下一步

0. **内核 A/B（优先）**：同一份需求（一张 PEPS-5129 卡片 + 一个意图 + 一条 run 记录）在 pi SDK 与 dsh 上各写一遍，记上手时间 / 代码行数 / 要绕的地方。dsh 侧直接按 `design.md` §9.6 的 **M0** 切片做（`panellist` + `main` + 一个 intent + 一条 `one/run-end`）。
1. 确认 run 记录的字段与写入时机（它是 skill 与"功能"挂钩的落点，最该先定）。若定 dsh，则直接设计为 `run/start` `run/step` `run/end` durable 事件族（要求可回放）+ 一个 Node Definition（卡片）+ 一个 View target（看板）。
2. 先定一件最小的事：**一张卡片 + 一个意图 + 跳对话**，跑通「点一下就有可执行结论」。
3. 同时验证 `piSdkBackend` 能在 Electron（main 或 utilityProcess）里跑通一次带上下文包的 prompt；dsh 侧对照 `dsh --profile web --dump-config` + 一层 patch 是否能完成同样的事。
4. 再决定 plugin manifest 的字段（intents 的模板格式是第一个要拍的）。
5. 之后才建独立仓库、拆包。

## 剩余

- 交互与图示已对齐（跳对话 + drawio 5 页）；原型截图尚未归档进 repo（现在只记录了文字事实）；图已改为 draw.io 源（assets/one-workbench.drawio）。
- 「Perm 与 Charles」与「开发任务」的数据重叠未理清。
- 若选 dsh：需补一份「上游跟随纪律」（`UPSTREAM.lock` + 快照发布），参考 `dsh-laofu-workbench` 的做法。
- dsh 的 UI slot 清单**已存** `design.md` §8 附录 A（2026-11-18 按 master 文档核对）；manifest 设计在 §9 附录 B。preview 会漂，动手前以 `slot-catalog.ts` / `cordis_inspect what:"client"` 复核。
- §9.7 列了四个「读源码才能定」的点：新建会话 API 形状、panel 选中→跳对话的客户端 API、projection 注册粒度、host route 的 owner 校验约定。

## 阻塞

- 无。
