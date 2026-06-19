## coding-agent底层的infra

### git worktree — 核心隔离原语
- 在现在的Coding Agent AI智能体中，git worktree几乎成为了核心的底层基础设施。
- 为什么是"大依赖"：
  - **并行 agent 的核心问题**：多个 agent 同时操作同一 repo 时，共享状态污染、交叉干扰、错误分支提交等结构性问题不可避免
  - **Worktree 提供的隔离**：独立工作目录、独立 HEAD、独立 index/staging、独立 cwd
  - **对比 git clone**：共享 .git 对象存储，近乎无额外磁盘开销，合并是本地分支 merge
  - **行业共识**：Clawt、Mothership、Agent Workspace Fabric、GitHub Copilot App、ait-vcs 均以 worktree 作为并行 agent 的标准隔离方案
- CMU CAID (Centralized Asynchronous Isolated Delegation) 论文的形式化描述：
  1. 先构建依赖图 (dependency graph)
  2. 只有所有依赖满足的单元才能委派给 agent
  3. 强依赖/循环依赖打包给同一个 agent
  4. 每个 agent 在独立 worktree 中工作
  5. 集成用 git merge，冲突由冲突方 agent 解决

### worktree 覆盖不到的隔离维度
- **运行时版本**：共享系统只有一份 node/python
- **系统级依赖**：apt/brew 安装互斥
- **端口冲突**：多个 agent 都 bind port 3000
- **守护进程/服务**：如 PostgreSQL 只能跑一份
- **GPU 资源**：显存不够分
- **缓存污染**：共享的 node_modules / ~/.cache
- **跨仓库依赖**：worktree 只能管一个 repo

### 多层隔离堆叠方案
```
         ┌─────────────────────────────┐
         │   Git Worktree (目录隔离)     │  ← 基础层
         ├─────────────────────────────┤
         │   Docker Compose (环境隔离)   │  ← 系统层
         ├─────────────────────────────┤
         │   独立 port mapping / 反向代理 │  ← 网络层
         ├─────────────────────────────┤
         │   独立 cache 目录 (CARGO_     │
         │   TARGET_DIR, npm prefix)   │  ← 缓存层
         ├─────────────────────────────┤
         │   Nix Flake (可复现依赖树)    │  ← 依赖层
         └─────────────────────────────┘
```
- **Docker 容器化**：每个 agent 一个 Docker Compose stack，解决运行时版本、系统包、端口、守护进程隔离
- **Nix/Flake**：声明式依赖树，每个 agent 可声明完全不同版本的 toolchain
- **远程沙箱**（E2B、Codespaces、StackBlitz）：云端独立 VM，物理级隔离
- **构建缓存重定向**：CARGO_TARGET_DIR、npm --prefix、PIP_CACHE_DIR 等环境变量

### 总结
Worktree 是最小可行隔离原语——用最低成本解决最频繁的冲突（文件修改冲突，约 80% 场景）。当冲突溢出到环境/网络/资源层时，需要向上堆叠 Docker 等隔离层。