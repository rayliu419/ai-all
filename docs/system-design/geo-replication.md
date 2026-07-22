# Geo Replication 笔记

> **📑 索引**
> 1. [定义](#%E5%AE%9A%E4%B9%89)
> 2. [目的](#%E7%9B%AE%E7%9A%84)
> 3. [相关术语](#%E7%9B%B8%E5%85%B3%E6%9C%AF%E8%AF%AD)
> 4. [设计原则](#%E5%8E%9F%E5%88%99)
> 5. [不同复制模式](#%E4%B8%8D%E5%90%8C%E5%A4%8D%E5%88%B6%E6%A8%A1%E5%BC%8F)
>    - [5.1 单向复制](#%E5%8D%95%E5%90%91%E5%A4%8D%E5%88%B6)
>    - [5.2 双向复制](#%E5%8F%8C%E5%90%91%E5%A4%8D%E5%88%B6)
>    - [5.3 Peer-to-Peer 复制](#peer-to-peer-%E5%A4%8D%E5%88%B6)
> 6. [通用架构](#%E9%80%9A%E7%94%A8%E6%9E%B6%E6%9E%84)
>    - [6.1 CDC 层](#61-cdc-%E5%B1%82)
>    - [6.2 流中间件层](#62-%E6%B5%81%E4%B8%AD%E9%97%B4%E4%BB%B6%E5%B1%82)
>    - [6.3 复制服务层](#63-%E5%A4%8D%E5%88%B6%E6%9C%8D%E5%8A%A1%E5%B1%82)
>    - [6.4 复制回环控制](#64-%E5%A4%8D%E5%88%B6%E5%9B%9E%E7%8E%AF%E6%8E%A7%E5%88%B6)
> 7. [冲突解决与最终一致性](#%E5%86%B2%E7%AA%81%E8%A7%A3%E5%86%B3%E5%92%8C%E6%9C%80%E7%BB%88%E4%B8%80%E8%87%B4%E6%80%A7)
>    - [7.1 冲突产生场景](#71-%E5%86%B2%E7%AA%81%E4%BA%A7%E7%94%9F%E5%9C%BA%E6%99%AF)
>    - [7.2 冲突解决策略](#72-%E5%86%B2%E7%AA%81%E8%A7%A3%E5%86%B3%E7%AD%96%E7%95%A5)
>    - [7.3 CRDT 详解](#73-crdt-%E8%AF%A6%E8%A7%A3)
> 8. [业界系统实践](#%E4%B8%9A%E7%95%8C%E7%B3%BB%E7%BB%9F%E5%AE%9E%E8%B7%B5)
>    - [8.1 Cassandra](#cassandra--dynamo-%E9%A3%8E%E6%A0%BC)
>    - [8.2 CockroachDB](#cockroachdb--raft--%E5%A4%9A-region)
>    - [8.3 全局对比](#%E5%85%A8%E7%90%83%E5%88%86%E5%B8%83%E5%BC%8F%E7%B3%BB%E7%BB%9F%E5%AF%B9%E6%AF%94)
> 9. [关键挑战与应对](#%E5%85%B3%E9%94%AE%E6%8C%91%E6%88%98%E4%B8%8E%E5%BA%94%E5%AF%B9)
>    - [9.1 复制延迟](#1-%E5%A4%8D%E5%88%B6%E5%BB%B6%E8%BF%9F-replication-lag)
>    - [9.2 数据冲突](#2-%E6%95%B0%E6%8D%AE%E5%86%B2%E7%AA%81)
>    - [9.3 脑裂](#3-%E8%84%91%E8%A3%82-split-brain)
>    - [9.4 幂等性](#4-%E5%A4%8D%E5%88%B6%E7%9A%84%E5%B9%82%E7%AD%89%E6%80%A7)
>    - [9.5 拓扑变更](#5-%E6%8B%93%E6%89%91%E5%8F%98%E6%9B%B4)
>    - [9.6 全量同步开销](#6-%E5%85%A8%E9%87%8F%E5%90%8C%E6%AD%A5%E7%9A%84%E5%BC%80%E9%94%80)
> 10. [最佳实践总结](#%E6%9C%80%E4%BD%B3%E5%AE%9E%E8%B7%B5)

## 定义

Geo Replication 是一种特别场景下的复制。

其特殊点在于：Geo 的复制通常延迟比较高，不能像 Etcd 那样在 AZ 间很短的等待同步的复制，基本上必须是异步复制。

同步写的方式一般可以用 2PC，Raft，Paxos 等，但是由于跨 Region 延迟太大，会极大的降低性能，导致事实情况下，基本不可用。跨 Region 网络延迟通常在几十毫秒到几百毫秒，远高于同 AZ 内亚毫秒级延迟。

**核心矛盾**：同步复制保证强一致性但跨 Region 延迟导致写入极慢；异步复制保证可用性和低延迟但引入数据不一致窗口。

## 目的

- 灾难恢复 (DR)：Region 级故障时快速切换，保证业务连续性。
- 跨 Region 容灾：容忍单个 Region 完全不可用（地震、断电、网络隔离等）。
- 提高系统性能，降低时延：数据靠近用户部署，减少读请求的跨 Region 延迟；写请求就近写入。
- 合规与数据主权：某些法规要求数据必须存储在特定地理区域内。

## 相关术语

- **CDC**（Change Data Capture）：变更数据捕获，通过读取数据库变更日志（如 MySQL binlog、PostgreSQL WAL）捕获数据变更。
- **Replication Loop**：复制回环。双向复制场景下，A 的写入复制到 B，B 又复制回 A，形成无限循环。
- **双向复制场景**：写入数据流有用户真实写和来自于其他 master 的复制写。对于后者，不应该再形成复制数据流，要区分这两种。
- **Replication ID / Offset**：每条复制流有唯一 ID 和位移标记，标识数据版本和增量同步位置（如 Redis 的 replication ID + offset）。
- **Partial Resync**：部分重同步，断连后仅同步缺失的增量（如 Redis PSYNC），效率远高于全量同步。
- **Full Resync**：全量重同步，复制流中断太久或复制 ID 变化时需重新同步全部数据。
- **Switchover**：计划内切换。运维人员主动发起的主备切换，通常有完整编排流程，可保证数据基本对齐后切换。
- **Failover**：计划外切换。主节点故障后的自动切换，数据可能尚未完全同步，需处理数据丢失或冲突。
- **Replication Lag**：复制延迟。从数据在主库写入到从库可见的时间差。Geo Replication 的延迟通常以秒甚至分钟计。

## 原则

- 保证数据的最终一致性。
- 一般是增量备份（全量复制代价极大，常态下只复制增量变更）。
- 尽量提高实时性（使用流式中间件、持续传输、并行复制等）。
- 可观测性：必须能监控复制延迟、数据积压、冲突数量等关键指标。
- 幂等性：复制操作应具有幂等性，以容忍重复发送。

## 不同复制模式

### 单向复制

一般意味着架构是一主多备（Master-Slave / Leader-Follower）。写入只在主节点进行，备节点只读。配置简单，不产生数据冲突。

- **优点**：架构简单，无冲突解决，容易运维。
- **缺点**：写性能受限于单主，备节点只能承担读流量；主节点故障时 Failover 需要补充机制。
- **典型系统**：MySQL 主从复制、Redis 主从复制、PostgreSQL Streaming Replication。

**Redis 单向复制要点**：
- 默认异步复制，性能高。
- 支持 `WAIT` 命令按需同步（但不提供强一致性）。
- 使用 Replication ID + Offset 标记数据集版本，断连后可尝试 PSYNC 部分重同步。
- 支持级联复制（从库挂载从库）。
- 主库关闭持久化 + 自动重启是危险操作：重启后数据集为空，从库可能被清空。

### 双向复制

一般是多主架构（Multi-Master）或者无主架构（Leaderless）。所有节点都可接受写入，相互复制变更。

- **优点**：高可用，写扩展性好，数据就近写入延迟低。
- **缺点**：必须处理数据冲突，复制回环问题复杂，运维难度大。
- **典型系统**：Cassandra（无主）、CouchDB、Active Directory。

### Peer-to-Peer 复制

双向复制在多 Region 场景下。多个 Region 的集群互为主备，Region 内通常采用强一致协议（Raft/Paxos），Region 间通过异步复制同步。

- Region 内：强一致（Raft / Paxos），确保本 Region 内数据可靠。
- Region 间：异步最终一致，通过流式 CDC 传输变更。
- 如 Spanner 的跨 Region 复制、Cassandra 的多 DC 部署。

## 通用架构

- 需要专门的复制服务，处理 CDC，复制回环和冲突解决问题。
- 有些存储内置提供 CDC，例如 MySQL 的 binlog、PostgreSQL 的 WAL、MongoDB 的 oplog 等。
- **Debezium** 是业界标准的 CDC 框架：基于 Kafka Connect 部署，支持多种数据库；还提供 Debezium Server（直接写入 Kinesis/GCP Pub/Sub/Pulsar）和 Debezium Engine（嵌入式库）。
- 需要流服务传递复制数据（Kafka、Pulsar、Kinesis 等），提供可靠性、持久化、重试和顺序保证。
- **关键设计**：不让远端服务直接写远端 DB，使用流式中间件解耦，提高可靠性和系统弹性。
- 需要记录复制数据的位移（offset），支持断点续传。

### 复制回环控制

双向复制场景下，写入数据流分为 **用户真实写** 和 **来自其他 Master 的复制写**。
对于复制来源的写，不能再形成新的复制数据流。实现方式：
- **Source Tagging**：每条变更带来源标记，复制服务根据标记跳过。
- **Session Context**：在写入时设置 session 或事务上下文变量，标记为复制写入。
- **Version Vector + Causality**：通过因果序判断是否是自身写入。

## 冲突解决和最终一致性

### 冲突产生场景

复制场景下，不可避免数据冲突。

- 在 Switchover 场景，可能还能用一些办法来编排，但是 Failover 的场景下，如果是双向复制，几乎不可避免的要碰到最终一致性和冲突解决问题。
- 主备切换，如果切换以后的新主能接受写，也会有问题。
- 主备切换后的二次切换，这个问题就变的更加复杂。

### 冲突解决策略

| 策略 | 原理 | 优点 | 缺点 |
|------|------|------|------|
| LWW (Last-Write-Wins) | 以时间戳或逻辑时钟最大的写为准 | 实现简单，收敛快 | 可能丢失数据；依赖时钟同步 |
| CRDT | 可交换、结合、幂等的合并操作保证自动收敛 | 数学保证收敛，无需协调 | 数据模型受限，存储和计算开销大 |
| Vector Clock / Version Vector | 每个副本维护版本向量，检测并发写冲突 | 不依赖物理时钟 | 向量可能无限增长；需用户介入 |
| Merge Semantics | 应用层自定义合并逻辑 | 最灵活，保留业务语义 | 需要应用层实现，复杂度高 |

### CRDT

CRDT（Conflict-free Replicated Data Type）是一种不需要协调就能保证最终收敛的分布式数据结构。

**基本特征**：任何副本可独立、并发地更新，无需协调；内建算法自动解决不一致；保证最终收敛到一致状态。

**两种类型**：

- **State-based CRDT (CvRDT)**：传播完整状态（或 Delta 增量），通过 Merge 函数合并。Merge 必须满足交换律、结合律、幂等性（Join Semilattice）。对网络要求低，支持 Gossip 协议，容忍消息重复和乱序。Delta CRDT 是优化版本，只传递增量。
- **Operation-based CRDT (CmRDT)**：传播操作（如 "+10"、"-20"），而不是状态。操作需满足交换律和结合律。需要通信中间件保证不丢不重（Exactly-Once Delivery）。操作通常小，带宽更省。
- 应该是 state-based。

**常见 CRDT 数据结构**：
- G-Counter：只增计数器，用于点赞数、访问量。
- PN-Counter：可增减计数器（G-Counter + 减法计数），用于库存、余额。
- G-Set / 2P-Set：集合 CRDT（只增/被删集合），用于黑名单。
- LWW-Element-Set：Last-Write-Wins 集合版，每个元素带时间戳（Cassandra 每行用此实现）。
- OR-Set (Observed-Remove Set)：观察删除集合，删除只移除特定版本，用于购物车、收藏列表。
- RGA / LSEQ：文本序列 CRDT，支持协作编辑（Google Docs、Figma）。

**NoSQL 实践**：
- LWW：CRDT 的一种。
- Time vector：也是 CRDT 的一种。

**行业应用**：
- Cassandra：使用 LWW-Element-Set CRDT 解决行级冲突。
- Redis Enterprise (CRDB)：部分数据类型支持 CRDT。
- Riak：全面基于 CRDT 做分布式 KV 存储。
- Cosmos DB：支持 CRDT 做多主复制。
- 协作编辑：Google Docs、Figma 等使用 RGA/LSEQ 文本 CRDT。

### Cassandra — Dynamo 风格

- 架构：无主 (Leaderless)，multi-master。
- 数据分布：一致性哈希 + Token Ring，支持 vnode（虚拟节点）。
- 复制层：每个 Partition 复制到 N 个节点（Replication Factor），可跨 DC 配置。
- 冲突解决：LWW CRDT，按时间戳决定最新版本。
- 一致性：可调一致性（Tunable Consistency）：`ONE`、`QUORUM`、`ALL` 等。
- 成员管理：Gossip 协议。
- Hinted Handoff：节点临时不可写时，协调节点代为存储写操作。

### CockroachDB — Raft + 多 Region

- 架构：Region 内 Raft 强一致，Region 间通过异步复制。
- Raft 组：每个 Range 一个 Raft 组，选举 Leader 协调写入。
- Non-voting Replica：只读副本，不参与 Raft 投票。
- Follower Reads：从非 Leader 副本读取，降低延迟。
- Per-replica Circuit Breaker：当 Range 不可用时自动触发断路器，避免请求无限挂起。
- Survival Goals：支持 Region 级别的故障容忍配置。

### 全球分布式系统对比

| 系统 | 跨 Region 复制方式 | 一致性 | 冲突解决 | 适用场景 |
|------|-------------------|--------|----------|----------|
| Cassandra | 无主异步 | 最终一致 | LWW CRDT | 高可用 KV，全球部署 |
| CockroachDB | Raft + 异步跨 Region | Serializable | Raft 强一致合并 | 金融、OLTP |
| Spanner | Paxos + 原子钟 | External Consistency | TrueTime 多版本 | 全球强一致事务 |
| Redis (Enterprise) | 主从异步 + CRDB | 最终一致 | CRDT | 缓存、实时数据 |
| DynamoDB Global Tables | 多主异步 | 最终一致 | LWW + Conflict Resolution | Serverless 全球应用 |
| MySQL Group Replication | 多主同步 | 强一致 | 无（同 Region） | Region 内高可用 |

## 关键挑战与应对

### 1. 复制延迟 (Replication Lag)

- **问题**：跨 Region 带宽和延迟导致数据同步滞后。写操作在主库完成后，到从库可见之间存在显著延迟，Geo 场景下可能从几秒到几分钟不等。
- **应对**：使用带宽压缩、并行复制、多线程应用；监控 Lag 并设置告警。

**📌 典型案例**

**案例 A：MySQL 跨 Region 主从延迟导致的读过期**
- 场景：某电商平台部署在美东（主）和美西（从），美西从库承担本地用户的读流量。
- 问题：促销秒杀时，用户在美西提交订单后立即刷新页面，从美西从库仍读到"未支付"状态——因为主从复制延迟了 3 秒，用户的订单支付记录还没传过来。
- 后果：用户重复提交订单，系统产生大量重复库存扣减。
- 解决：引入"写后读一致性"（Read-after-Write Consistency）：用户写完关键数据后，强制从主库读取，或者等待复制确认后再返回。

**案例 B：Kafka MirrorMaker 跨集群同步积压**
- 场景：使用 Kafka MirrorMaker 2 做跨 Region 数据同步，源集群在 AWS us-east-1，目标集群在 ap-southeast-1。
- 问题：新加坡业务高峰时 MirrorMaker 消费速度跟不上生产速度，造成 Topic 积压数十亿条消息，复制延迟达到 30 分钟。
- 根因：新加坡到美东的网络带宽受限，且生产端消息体积大（单条 50KB+）。
- 解决：启用压缩（Snappy/Zstd）、减少单条消息体积、增加 MirrorMaker 消费者并行度。

### 2. 数据冲突

- **问题**：多个 Region 的写请求同时更新同一数据，异步复制导致冲突。
- **应对**：CRDT、LWW、版本向量 + 业务自定义合并。

**📌 典型案例**

**案例 A：Gmail 早期联系人冲突**
- 场景：Gmail 联系人在手机和网页端均可编辑，两个客户端可能同时对同一条联系人记录做不同修改。
- 问题：两个修改在不同 Region 同时发生，复制时发现同一条记录的 name 字段被改成了不同值。
- 解决：Gmail 采用"字段级 LWW + 合并语义"：同字段用最新时间戳覆盖，不同字段则自动合并（手机改了电话，网页改了姓名，两者都保留）。

**案例 B：Cassandra 跨 DC 的 LWW 冲突**
- 场景：Cassandra 双数据中心部署，用户在 DC1 和 DC2 几乎同时对同一行做 UPDATE。
- 问题：Cassandra 使用 LWW-Element-Set CRDT，以时间戳决定最终值。但 NTP 时钟偏差可能导致较晚的修改被较早的覆盖。
- 解决：使用 Cassandra 的 "TimeUUID" 类型作为时间戳保证全局有序；同时部署精确 NTP 同步（PTP/NTP 服务），将跨 Region 时钟偏差控制在毫秒级。

**案例 C：Git 分布式协作**
- 场景：多个开发者在不同 Region 对同一个 Git 仓库提交代码。
- 问题：两个开发者修改了同一个文件的同一行，各自推送到不同 Region 的镜像仓库。
- 解决：Git 的 Merge + Conflict Resolution 模型——它本质上是一种操作型 CRDT。冲突标记出来由人工解决，这是应用层 Merge Semantics 的典型例子。

### 3. 脑裂 (Split-Brain)

- **问题**：网络分区时两个 Region 的节点无法通信，各自以为自己是主，都接受写入，导致数据分叉，合并时产生不可恢复的冲突。
- **应对**：Quorum 机制、Lease 机制、fencing token、STONITH（Shoot The Other Node In The Head）。

**📌 典型案例**

**案例 A：GitHub 2018 年 MySQL 脑裂事故**
- 场景：GitHub 使用 MySQL + Orchestrator 管理主从切换。某次网络故障导致 Orchestrator 与主库通信中断。
- 问题：Orchestrator 以为主库挂了，将另一个从库提升为新主。但原主库实际上还在运行并接受写入。两个库都在接受写请求，形成脑裂。
- 后果：数据出现分歧，约 15 分钟的数据无法自动恢复，GitHub 不得不从备份恢复部分数据。详细分析见 GitHub 官方博客 2018 年 10 月的事故报告。
- 解决：引入"强化的故障检测"——使用多路心跳（跨 AZ 的独立监控点），提升仲裁前必须确认原主已通过 STONITH/仲裁机制下线。

**案例 B：MongoDB 副本集脑裂**
- 场景：MongoDB 3 节点副本集分布在 2 个 AZ，主节点在 AZ-1，2 个从节点在 AZ-2。
- 问题：AZ-1 网络故障，主节点被孤立，但它仍认为自己是主继续接受写入；AZ-2 的 2 个节点选举出新主。
- 后果：故障恢复后，原主的数据与副本集不一致。
- 解决：MongoDB 采用 Raft 协议——主节点失去与大多数节点的通信后自动降级为从节点，不再接受写入。核心原则：写入需要超过半数的节点确认。

**案例 C：Pacemaker + DRBD 脑裂**
- 场景：传统 HA 集群使用 DRBD（网络 RAID）做数据同步，Pacemaker 管理故障切换。
- 问题：心跳网络中断 + 两个节点均认为对方失效，同时将 DRBD 设备提升为主角色，开启写入。
- 后果：DRBD 检测到脑裂后，必须选择丢弃一边的修改（discard/peer-diff），丢失数据。
- 解决：配置 Priority / Quorum 策略，引入仲裁节点（Witness），或使用 STONITH 强制关闭异常节点。

### 4. 复制的幂等性

- **问题**：CDC 或消息队列可能重复发送同一条变更事件，导致目标库重复应用。
- **应对**：设计幂等的应用逻辑；使用唯一事件 ID 去重；事务 ID 使重放安全。

**📌 典型案例**

**案例 A：Debezium + Kafka 的 Exactly-Once 问题**
- 场景：使用 Debezium 捕获 MySQL binlog 写入 Kafka，下游应用消费后写入 Elasticsearch。
- 问题：Kafka Connect 的 At-Least-Once 语义意味着消费者可能多次收到同一条 binlog 事件（如 Kafka 重平衡时 Offset 回退）。
- 后果：Elasticsearch 中同一文档被重复写入，产生重复记录。
- 解决：使用"唯一业务 ID + 幂等更新"——ES 的 `_id` 设置为数据库主键，`upsert` 操作天然幂等；或者 Kafka 开启 `idempotent=true` + `enable.idempotence=true` + 事务性 Producer。

**案例 B：Kafka 重复消费导致金额重复扣减**
- 场景：支付流水通过 CDC 流复制到下游风控系统，风控系统按事件做余额扣减。
- 问题：Kafka 消费者处理完成后发送 Offset 提交前崩溃，重启后重新消费已处理的事件。
- 后果：同一笔支付被扣款两次。
- 解决：在消费端维护"已处理事件 ID 去重表"（Redis Set 或 DB 唯一约束），处理前先检查是否已处理过该事件。

### 5. 拓扑变更

- **问题**：增加/移除 Region 时，需要将现有数据重新分布到新节点，涉及大量数据迁移。
- **应对**：一致性哈希（Cassandra）、自动 rebalance（CockroachDB）、逐步迁移。

**📌 典型案例**

**案例 A：Cassandra 扩容时的节点 Join**
- 场景：Cassandra 集群有 6 个节点（RF=3），需要扩容到 9 个节点。
- 过程：新节点加入时通过 Gossip 协议被集群发现，自动标记为 JOINING 状态。新节点从邻居节点流式传输（Streaming）属于自己 Token 范围的数据。
- 挑战：Streaming 期间大量数据跨机柜/跨 DC 传输，占用大量网络带宽，可能导致正常请求延迟上升。
- 解决：通过 `nodetool decommission` 逐步操作，使用 `nodetool cleanup` 在新增完成后清理冗余数据；生产环境在业务低峰期扩容。

**案例 B：Kafka 分区再均衡**
- 场景：跨 Region Kafka 集群，Cluster A（us-east-1）向 Cluster B（eu-west-1）做 MirrorMaker 同步时，目标集群新增 Broker。
- 问题：新 Broker 加入触发分区 Reassignment，大量数据 Replication 跨 Region 传输，造成带宽打满，正常业务流量受损。
- 解决：使用 `kafka-reassign-partitions.sh` 逐步迁移（一次只移少量分区）；限制 Reassignment 的带宽速度；先扩容 Broker 再逐步移动分区。

### 6. 全量同步的开销

- **问题**：新 Region 加入或复制流断链太久（Replication ID 过期），需要全量重同步所有数据，耗时巨大。
- **应对**：快照 + 增量同步；流式传输 + 快照并发提升速度。

**📌 典型案例**

**案例 A：Redis 全量重同步导致业务中断**
- 场景：Redis 主库在美东，从库在美西，网络闪断导致复制连接中断。由于中断时间较长，master 的 replication backlog 溢出，从库无法做 PSYNC 部分重同步。
- 问题：从库触发全量重同步（Full Resync），主库 fork 子进程生成 RDB 快照（可能造成 5-10 秒的延迟尖峰），然后将 GB 级的 RDB 文件传输到美西。
- 后果：跨 Region 传输大 RDB 文件耗时长（10GB 文件传输约需 2-3 分钟），期间从库丢弃所有数据提供服务。如果从库承担读流量，这段时间读请求全部失败。
- 解决：调整 `client-output-buffer-limit` 和 `repl-backlog-size` 为更大的值，使网络抖动时不至于溢出 backlog；尽量在同一 Region 放置主从减少断链概率。

**案例 B：MySQL 新从库搭建**
- 场景：在亚太新 Region 增加一个 MySQL 从库，需要从美东主库做全量备份和恢复。
- 过程：主库做 `mysqldump`（或 XtraBackup）生成全量快照，通过 S3 跨 Region 复制到亚太，再从快照恢复后追增量 binlog。
- 挑战：1TB 级别的数据库，全量备份耗时 2 小时，S3 跨 Region 复制 4 小时，增量追赶又需 30 分钟。整体需要 6-7 小时才能让从库追上主库。
- 解决：使用 Percona XtraBackup 的流式压缩传输，降低带宽消耗；从就近的同 Region 从库而非主库拉取数据，避免影响主库性能。

**案例 C：MongoDB 初始同步对主库性能冲击**
- 场景：向跨 Region 副本集添加新成员，触发 Initial Sync。
- 问题：初始同步过程中，主库需要持续提供 oplog 并响应新成员的数据拉取请求，可能造成主库的页面缓存（WiredTiger cache）被刷新，影响正常请求性能。
- 解决：MongoDB 4.4+ 支持"初始同步从最近的从库拉取"（通过 `initialSyncSource`），减轻主库负载；同时在从库端使用压缩降低跨 Region 带宽。
