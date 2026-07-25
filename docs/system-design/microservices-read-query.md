# 微服务中的 Read Query 处理

微服务架构下，由于"数据库 per 服务"模式，join 跨多个服务的数据变成一个难题。本文讨论实现跨服务查询的主流方案。

## 问题背景

- 单服务查询简单（自己的 DB 查自己的数据）。
- 跨服务查询困难：join 的数据分散在多个服务各自的数据库中，无法用传统 SQL join。
- 批量查询困难：某些场景需要按 status 过滤记录、批量查找未完成任务（如 CORS 大数据管理面、GIM Migration 服务）。直接查 status 字段在 MySQL 中易出现索引失效。
- 可用性与一致性权衡：跨服务网络交互降低可用性，多数据源带来一致性问题。

## 方案一：API Composer

### 原理

引入一个 API Composer（通常由 API Gateway 或一个独立的组合层承担），分别调用多个微服务的 API，然后在内存中做 join。

```
Client → API Composer → Service A (data_a)
                     → Service B (data_b)
                     → Service C (data_c)
                     ↓
              In-memory join → Response
```

### 优劣

| 优点 | 缺点 |
|---|---|
| 实现简单，不改变现有服务 | 多次网络交互增大延迟 |
| 无需额外存储 | 降低整体可用性 (A × B × C) |
| 适用于数据量小的场景 | 大数据集 in-memory join 低效 |
| 数据实时性最好 | 数据不一致（各服务返回时刻不同） |

### 适用场景

- 数据量小（翻页、聚合结果数可控）
- 实时性要求高
- 简单的主数据聚合（如查用户+查订单）
- 不适合大数据过滤、复杂聚合查询

## 方案二：CQRS

### 核心思想

命令（Command/Write）与查询（Query/Read）使用不同的模型，甚至不同的存储。

- **Command 侧**：负责数据变更，通常是业务拥有者（数据模型的设计者和修改者），写入自己的 DB。
- **Query 侧**：专门为查询优化——使用不同的 DB 类型、不同的 schema、不同的索引策略。

不要把 CQRS 等同于"读写分离"。读写分离通常指读写用同一类 DB（如 MySQL 主从），而 CQRS 允许用完全不同的 DB 来满足查询需求，比如用 ES（ElasticSearch）做全文搜索，用 MongoDB 做文档聚合，用 Neo4j 做图查询。

### 架构

```
Command Side                  Event Bus               Query Side
─────────────                                       ─────────────
Service A ──→ Domain Event ──────→ Event Handler ──→ View DB (ES)
Service B ──→ Domain Event ──────→ Event Handler ──→ View DB (MongoDB)
Service C ──→ Domain Event ──────→ Event Handler ──→ View DB (Neo4j)
```

每个服务发布领域事件（Domain Events），Query 侧监听这些事件，构建和维护自己的 View DB。

### 典型例子：Order History Service

从笔记中的例子"findHistoryOrder"：

1. Order Service 发布 `OrderCreated`、`OrderShipped` 等事件。
2. Kitchen Service、Delivery Service、Accounting Service 各自发布领域事件。
3. Order History Service 监听所有相关事件，在 View DB 中融合数据。
4. View DB 可以是一个文档数据库，schema 按查询需求设计（反范式化）。

好处：查询不需要 join——View DB 已经预先聚合好数据。代价：最终一致性（replication lag）。

### 优劣

| 优点 | 缺点 |
|---|---|
| 查询性能高，schema 按需优化 | 架构复杂度大幅增加 |
| 读写独立扩展 | 需要维护事件同步机制 |
| 可以混合使用多种 DB | 最终一致性，有延迟窗口 |
| Command 侧业务逻辑更简洁 | 代码一定程度重复 |

## 方案三：Materialized View（物化视图）

### 原理

预先在一个或多个数据源之上建立只读的、已聚合的视图，app 直接查这个视图。视图是完全可丢弃的——可以从源数据完整重建。

### 与 CQRS 的关系

CQRS 的一种实现方式：Command 侧写入，事件驱动更新 Materialized View，Query 侧读 Materialized View。Materialized View 是 CQRS 中 Read Model 的具体存储形式。

### 应用

- 多表 join 的复杂查询预计算
- 报表、大屏、统计场景
- 微服务场景下跨服务数据聚合

## 方案四：Event Sourcing

### 原理

不存储当前状态，而是存储所有变更事件（append-only log）。当前状态通过重放所有事件来计算（rehydration）。

### 与 CQRS 的协同

Event Sourcing 天然适合与 CQRS 组合：
- Command 侧：append 事件到 Event Store。
- Query 侧：监听事件，构建 Materialized View。
- Unified log 作为单一真相源（System of Record）。

### 注意

- Event Sourcing 引入极高的复杂度。
- 仅在需要审计追踪、时态查询、事件驱动协作的场景下使用。
- 对于大多数系统，传统 CRUD + CQRS 已足够。

## 方案五：Read-Your-Writes 一致性

CQRS 中 Command 侧写入 View DB 的同步存在延迟，导致用户刚写入的数据在查询时读不到（read-after-write inconsistency）。RYW（Read-Your-Writes）保证用户对自己写入的数据能立即读到一致的结果。

### 问题场景

```
User POST /orders (写成功)          ← 返回 200
User GET  /orders/123 (读不到)      ← View DB 尚未同步
```

本质矛盾：Command 侧写成功了，但 Query 侧还没来得及同步，用户看到"数据丢了"或"操作没生效"。

### 方案 A：Write-Through（同步刷新）

写入 Command 侧后，同步等待 View DB 更新完成再返回响应。

| 优点 | 缺点 |
|---|---|
| 逻辑简单，立即可见 | 写延迟增大（需等待所有 View DB） |
| 对客户端透明 | 写可用性降低（依赖 View DB） |

适用：需要严格 RYW、写频率不高的场景。

### 方案 B：Read-Your-Writes Session

为每个用户会话维护一个版本号或时间戳。

1. 写操作返回一个写入时间戳或 event ID。
2. 读请求携带该时间戳，Query 侧在同步未追平时阻塞等待或返回特殊状态。
3. 或由客户端等待一段时间后重试。

```
POST /orders → 返回 { orderId: 123, version: 42 }
GET  /orders/123?after_version=42 → View DB 检查版本
                                    → 未同步则等待或返回 425 Too Early
```

### 方案 C：Read from Command Side（直接读主库）

对于用户刚写入的数据，直接从 Command 侧（主库）读取。适用于用户的"我的订单"等个人数据查询。

| 优点 | 缺点 |
|---|---|
| 强一致性 | 增加 Command 侧读负载 |
| 无需同步机制 | 通常 Command 侧不是为读优化的 |

### 方案 D：Logical Replication with Monotonic Reads

利用数据库自身的复制机制（如 MySQL binlog、Kafka 分区），保证同一 partition key 的读写按顺序到达。

- 单用户的所有请求路由到同一 partition。
- Partition 内事件严格有序，读操作在写操作之后到达该 partition 的 View DB。
- 天然保证该用户的 RYW。

### 策略选择

| 策略 | 一致性 | 写延迟 | 复杂度 | 适用 |
|---|---|---|---|---|
| Write-Through | 强 | 升高 | 低 | 低频写，严格 RYW |
| RYW Session | 最终+RYW | 不影响 | 中 | 大部分 CQRS 场景 |
| Read from Command | 强 | 不影响 | 低 | 个人数据查询 |
| Monotonic Reads | 最终+RYW | 不影响 | 高 | 高吞吐 CQRS |

关键原则：优先保证用户在自己的数据上看到强一致性（RYW），对其他用户的数据可以接受最终一致。

## 批量查询与索引优化

笔记中提到的一些批量查询场景：

### 场景1：按 status 批量查询

某些服务需要批量查询"失败/未调度的记录"（如 CORS 大数据管理面），或"很久没有完成的任务"（如 GIM Migration 服务）。

**优化策略**：
- 不使用 status 直接过滤——MySQL 中低基数字段索引效率低。
- 使用创建时间作为索引字段，批量查询后再读取 status 处理。
- status 拆分到单独的表（压缩表、标志位表）。
- CQRS：利用 View DB（如 ES）做过滤，ES 对字段过滤效率极高。代价是引入额外存储。

### 场景2：DJS 查询下一分钟调度的记录

**方案**：在任务执行时，同时生成下次执行的时间戳，将时间戳作为 hash key，快速定位一批记录。

### 索引设计通用原则

- 查询需求驱动：确定哪些是常见查询，为它们创建索引。
- 列选择：WHERE、JOIN、ORDER BY 中频繁使用的列。
- 复合索引：多列查询条件考虑联合索引。
- 索引覆盖：尽量让索引包含查询所需的所有列，避免回表。
- 维护成本：不过度创建索引，DELETE/UPDATE 性能会受影响。
- 监控优化：使用 explain / 慢查询日志持续优化。

## 方案对比与选择

| 维度 | API Composer | CQRS + View DB | CQRS + RYW | Event Sourcing |
|---|---|---|---|---|
| 复杂度 | 低 | 中高 | 中 | 极高 |
| 数据实时性 | 实时 | 最终一致（秒级） | 最终一致 + RYW | 最终一致 |
| 查询灵活性 | 受限于各服务 API | 可任意优化 schema | 可优化 + 个人数据强一致 | 最灵活（可重放） |
| 适用规模 | 小数据量 | 中大规模 | 中大规模 | 需要审计/时态查询 |
| 运维成本 | 低 | 中 | 中 | 高 |
| 一致性保证 | 弱一致 | 最终一致 | 最终一致 + 读己之所写 | 最终一致 + 可校验 |

### 选择决策

```
是否需要跨服务查询？
├─ 否 → 单服务直接查自己的 DB
└─ 是 →
   ├─ 数据量小、实时性高 → API Composer
   ├─ 数据量大、查询模式复杂 →
   │  ├─ 无需强一致 → CQRS + View DB
   │  ├─ 需要 RYW → CQRS + RYW Session
   │  └─ 需要审计/事件溯源 → Event Sourcing + CQRS
   └─ 批量查询/过滤场景 →
      ├─ 数据量可控 → 索引优化（复合索引、覆盖索引）
      └─ 数据量大、过滤条件多 → CQRS + ES
```

## References

- Chris Richardson, *Microservices Patterns* — Chapter 7: Implementing Queries in a Microservice Architecture
- microservices.io: API Composition pattern, CQRS pattern
- Azure Architecture Center: CQRS pattern, Materialized View pattern, Event Sourcing pattern
- Martin Fowler: CQRS, Event Sourcing
- Google Spanner: TrueTime & external consistency
- Amazon DynamoDB: Read-Your-Writes consistency
- Pat Helland, "Building on Quicksand" (RYW in distributed systems)
