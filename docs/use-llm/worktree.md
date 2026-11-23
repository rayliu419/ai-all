## use-worktree-in-ai

### 核心主张

- 在 AI 编程场景下，worktree 从"可选工具"变成了"必要基建"。
- 标准形态只有一句话：**主仓目录常驻 master，每个任务一个 worktree 目录，worktree 统一放在 `<repo>-wt/` 下。**

### 标准布局

```
~/workspace/hello            master        主仓，常驻，不切分支，不开 IDEA
~/workspace/hello-wt/xxx     feat/payment  任务 1 的 worktree
~/workspace/hello-wt/yyy     fix/login     任务 2 的 worktree
```

- `hello` 只干三件事：托管 `.git`、当 review 的参照物、跑一次性命令。
- `hello-wt/xxx` 这种平级目录才放正在写的代码，每个目录一个任务、一个分支、一个 IDEA 窗口。
- `hello` 里 `git worktree list` 能看到全部 worktree；`git branch` 里，别的 worktree 正在用的分支前面会打 `+`，主仓当前分支是 `*`。

```
$ cd ~/workspace/hello
$ git worktree list
~/workspace/hello         8f3a1c2 [master]
~/workspace/hello-wt/xxx  4d9e07b [feat/payment]
~/workspace/hello-wt/yyy  1c77b20 [fix/login]

$ git branch
+ feat/payment
+ fix/login
* master
```

### 为什么：AI 并行开发让"切分支"变成成本

- **人不再一次只做一件事。** 有了 AI，人可以同时在两条分支上推进两个 feature：A 分支让 AI 跑测试，B 分支自己改设计。一个目录只有一个 working tree，只能靠频繁 `git switch` 硬扛。
- **切分支会打碎 AI 的上下文。** AI 手里握着的是上一次读到的文件内容、目录结构、搜索结果、测试输出。你在它脚下 `git switch`，这些缓存全部失真，模型却还以为自己看到的是当前代码——幻觉就是这么来的。
- **切分支会打碎人的上下文。** 来回切分支，人的编辑器 tab、构建产物、正在跟的那条报错也跟着一起换，每次都要重新热身。
- **review 需要一个稳定的对照物。** 主仓停在 master 不动，每个 worktree 的 `git diff master` 就是这次任务的全部改动，干净可比。

对照两种做法：

| 做法 | 一个目录反复 `git switch` | 主仓 + 每任务一个 worktree |
| :--- | :--- | :--- |
| AI 上下文 | 目录内容随时被换掉，缓存失真 | 目录稳定，AI 读到的就是它正在改的 |
| 并行任务 | 一次只能一个 | 几个 worktree 同时跑 |
| Review | 要记得自己在哪个分支上 diff | 主仓恒为 master，diff 基准固定 |
| 代价 | 无 | 多几个目录、多个 IDEA 索引 |

### 一个 .git，三个工作区，一份远端

```
工作区（文件，各一份）      工作区（文件，各一份）       工作区（文件，各一份）
 hello/   src/App.java      hello-wt/xxx/ src/Pay.java   hello-wt/yyy/ src/Login.java
 HEAD · index               HEAD · index                 HEAD · index
      │                          │                            │
      └───────────┬──────────────┴─────────────┬──────────────┘
                  ▼                            ▼
  ┌────────────────────────────────────────────────────────────────┐
  │ .git（只有一份）                                                │
  │ objects/     blob · tree · commit · commit …      ← 全部历史     │
  │ refs/heads/  master → ●  feat/payment → ●  fix/login → ●         │
  └────────────────────────────┬───────────────────────────────────┘
                    push ▼  │  ▲ fetch
  ┌────────────────────────────▼───────────────────────────────────┐
  │ GitHub · origin   同一个结构，bare：有 objects/refs，没有工作区  │
  └────────────────────────────────────────────────────────────────┘
```

- 工作区不存历史，只是把对象库里某个 commit 铺成文件。三个目录铺三份 → 能同时停在三个分支。
- `objects/` 只有一份，`refs/heads/` 只有一份，`HEAD` 与 `index` 每个工作区各一份。
- GitHub 上那份同样是 `.git`，只是 bare。`push` = 把缺的对象传上去 + 挪远端 `refs/heads/main`，所以没有"正本"，只有大家约定的 `origin`。
- 笔记页 `worktree.html` 有这张图的完整版。

### add 和 commit 到底写了哪些文件

| 命令 | 写进共享区 `hello/.git/` | 写进本 worktree |
| :--- | :--- | :--- |
| `git add` | `objects/` 里新增 blob（内容新才新增） | `worktrees/xxx/index`（暂存快照） |
| `git commit` | 新增 tree + commit；`refs/heads/<branch>` 指向新 commit | `worktrees/xxx/logs/HEAD`；`index` 被刷新 |

两个反直觉的点：`git add` 就已经在写对象了，不是等 commit 才写——add 完再丢弃改动，那个 blob 仍躺在 `objects/` 里，等 gc 才回收。commit 也不改 `HEAD`，`HEAD` 只记"我在哪个分支上"，变的是那条分支的指针。

worktree 里一次 commit 的落点：

```
# 共享：hello/.git/（全仓只有一份）
├── objects/0f2a…                新增 blob / tree / commit
├── refs/heads/feat/payment      挪到新 commit
└── logs/refs/heads/…            分支 reflog

# 这个 worktree 自己的：hello/.git/worktrees/xxx/
├── index                        只有这份被刷新
├── HEAD                         ref: refs/heads/feat/payment，没变
└── logs/HEAD                    本 worktree 的 reflog
```

主仓那个 `master` 一点没动：commit 的是 `feat/payment`，而且 master 正被主仓自己占着。

```
$ cd ~/workspace/hello-wt/xxx
$ cat .git                      # gitdir: .../hello/.git/worktrees/xxx
$ git commit -am "pay"
$ git rev-parse feat/payment    # 新 commit
$ cd ~/workspace/hello
$ git rev-parse master          # 完全没变
$ git log --oneline -1 feat/payment   # 主仓这边立刻能看到
```

`git log` 在主仓能看到别的 worktree 刚提交的东西，正因为对象和 ref 都写在同一个 `.git` 里。唯一的交叉风险是共享区里的 ref：两个 worktree 同时 commit 不会冲突（各写各的分支 ref），同时 commit 到同一分支根本不可能——git 不允许同一分支被两个 worktree 检出。

### 日常流程

```
# 0. 一次性：给 worktree 建个平级目录
mkdir -p ~/workspace/hello-wt

# 1. 开新任务：从主仓建 worktree（新分支 or 已有分支）
cd ~/workspace/hello
git worktree add ../hello-wt/xxx -b feat/payment
git worktree add ../hello-wt/yyy fix/login      # 检出已有分支

# 2. 干活：在 hello-wt/xxx 里让 AI 改代码
#    主仓 hello 全程停在 master，不动

# 3. review：回到主仓看这次任务的全部改动
cd ~/workspace/hello
git diff master...feat/payment

# 4. 合并：确认无误后在主仓合
git merge feat/payment

# 5. 收工：删目录 + 删分支
git worktree remove ../hello-wt/xxx
git branch -d feat/payment
```

### IDEA 怎么开

- **打开 `hello-wt/xxx`，不是 `hello`。** 每个 worktree 是独立的 IDEA 项目、独立的索引和构建缓存，`.idea/` 就落在各自目录里。
- **主仓 `hello` 不用开 IDEA。** 它只留在终端里当 git 和 diff 的基准。
- 依赖不会重复下载：Maven 的 `~/.m2`、Gradle 的 `~/.gradle` 是全局共享的，多开 worktree 只多花 IDEA 自己的索引空间，首次打开要等一次 index。
- 几个 worktree 同时开时，同名文件（`Application.java` 之类）在 tab 上只显示文件名，容易点错；把路径尾巴显示出来。
- 收工先关 IDEA 窗口，再 `git worktree remove`。反过来操作会让 IDEA 里留一个指向空目录的 ghost project。

### 常用命令速查

| 命令 | 作用 |
| :--- | :--- |
| `git worktree add <path> -b <branch>` | 建目录 + 建分支，一步到位 |
| `git worktree add <path> <branch>` | 检出已有分支到新目录 |
| `git worktree list` | 谁在哪个目录、什么 commit |
| `git worktree remove <path>` | 删除 worktree（有未提交改动会拒绝） |
| `git worktree prune` | 清掉手工 `rm -rf` 留下的登记残骸 |

### 注意事项

- 同一个分支不能被两个 worktree 同时 checkout，`git worktree add` 会直接报 `already checked out at`。要并行跑同一份代码，用 `--detach` 或另开分支。
- `git worktree remove` 拒绝删除有未提交改动的目录；确定要丢才加 `--force`，别把没合的东西一起删了。
- worktree 里的 `.git` 是一个文本文件，指向主仓的 `.git/worktrees/<name>`。它不是一个独立仓库，不要删、不要拷走。
- 主仓占着 master，所以 AI 拿不到主干。要改主干就在 `hello` 里做，这也是主仓存在的意义。
- 从 worktree 目录直接启动 AI 工具，让它看到的 `pwd` 就是真实位置；不要用 `--work-tree` 之类的参数把位置和目录拆开。
- worktree 只隔离代码和 git 状态，不隔离数据库、端口、容器名、本地配置。几个 worktree 同时跑服务时要自己改端口和库名，否则互相打架。
- 建议在 `AGENTS.md` / `CLAUDE.md` 里写一句"你在 worktree 中工作，主仓是 `~/workspace/hello`"，AI 才不会自己去主仓改代码。
