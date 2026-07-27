## use-worktree-in-ai

### 核心主张
- 在 AI 编程场景下，worktree 从"可选工具"变成了"必要基建"。
- AI 需要隔离的工作区、需要对比、需要同时维护多个上下文，worktree 提供了最轻量的解决方案。

### 为什么 AI 场景下 worktree 变得重要？

- **AI 需要独立工作区。** AI 编程工具（Claude Code, Cursor, Copilot 等）会在目录中生成缓存、索引、历史记录。如果 AI 和人在同一目录轮流工作，双方的上下文相互污染。
- **分支切换不再无害。** 传统开发中切分支只是代码变更，但 AI 编程工具有自己的状态（打开文件、对话历史、上下文缓存）。在 AI session 中间切分支，AI 记忆中的代码结构和实际目录状态会不一致，导致幻觉。
- **需要并行 holding 多个上下文。** AI 经常需要同时处理多个任务（一个任务等待测试结果时，另一个任务已经开始）。一个目录只有一个 working tree，无法支持真正的并行。
- **AI 生成代码需要独立 review。** AI 生成的代码需要与主分支的代码进行完整对比，worktree 天然提供了这种隔离，review 时通过 diff 即可清晰看到。
- **不同 AI 工具可以用不同 worktree。** 例如 Claude Code 用 worktree A 做后端开发，Cursor 用 worktree B 做前端，互不干扰。

### Worktree vs. Clone 对比

| 对比维度 | Worktree | Clone |
| :--- | :--- | :--- |
| **创建速度** | 即时（秒级） | 慢（取决于仓库大小，可能数分钟） |
| **磁盘占用** | 仅一份 .git，共享对象存储 | 每个 clone 一份完整 .git |
| **分支可见性** | 所有分支、tag 自动可见 | 需要手动 fetch、添加 remote |
| **同步机制** | 自动共享 ref，无需手动同步 | 需要 push/pull 来同步 |
| **AI 适配性** | 随时创建/销毁，适合 AI 的试错迭代 | 相对重量，不适合频繁创建 |

### Best Practice 示例

场景：你在 `main` 分支上工作，同时让 AI 在 `feature/new-api` 上开发新功能。

```
# 1. 基于当前仓库创建一个 AI 专用 worktree
git worktree add ../project-ai feature/new-api

# 2. AI 在 ../project-ai 目录下工作
#    - 目录与主工作区完全独立
#    - AI 可以随意修改、测试、调试
#    - 你在主目录继续开发互不干扰

# 3. AI 完成任务后，在主目录 review 变更
git diff feature/new-api

# 4. 确认无误后合并
git merge feature/new-api

# 5. 清理 worktree
git worktree remove ../project-ai
```

#### 更精细的 AI-Worktree 循环

```
# cycle 结构
main worktree (你)# → AI worktree → review → merge → 清理
                   ↘ 另一个 AI worktree（并行任务）
```

进阶用法：

```
# 为不同 AI 任务创建独立 worktree
git worktree add ../project-ai/feature-a feature/new-api
git worktree add ../project-ai/refactor-b refactor/db-opt

# AI 在各自的 worktree 中独立工作
# 你在主目录 review 每个 worktree 的 diff，选择性合并
```

#### 配合 review 流程

```
# 用 IDE 或 diff 工具对比两个 worktree
git diff worktree-a/main..worktree-b/feature/new-api

# 也可以在两个目录之间直接 diff
diff -rq project-main/ project-ai/ | grep -v '.git' | head -30
```

### 注意事项

- Worktree 的 HEAD 分支不能被删除，除非先 `git worktree remove`。
- 删除 worktree 前确保代码已合并或 stash。
- 不同 worktree 可以 check out 同一个分支，但只有一个是 writable，其余会被设为 detached HEAD。
- AI 工具最好从 worktree 目录启动，不要在 parent 目录设 `--work-tree` 参数——这会导致 AI 对文件位置产生困惑。
- 建议在 CLAUDE.md 或 project rules 中加入 worktree 使用说明，让 AI 知道自己运行在 worktree 环境中。
