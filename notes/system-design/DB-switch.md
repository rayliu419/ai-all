# DB 切换笔记

> **📑 索引**
> 1. [背景](#%E8%83%8C%E6%99%AF)
> 2. [通用解决思路](#%E9%80%9A%E7%94%A8%E8%A7%A3%E5%86%B3%E6%80%9D%E8%B7%AF)
> 3. [MySQL 切换](#mysql-%E5%88%87%E6%8D%A2)
>    - [3.1 Switchover](#mysql-switchover)
>    - [3.2 Failover](#mysql-failover)
>    - [3.3 GTID](#gtid)
> 4. [Redis 切换](#redis-%E5%88%87%E6%8D%A2)
>    - [4.1 Switchover](#redis-switchover)
>    - [4.2 Sentinel 自动故障转移](#4%E2%80%82sentinel-%E8%87%AA%E5%8A%A8%E6%95%85%E9%9A%9C%E8%BD%AC%E7%A7%BB)
>    - [4.3 Redis Cluster](#redis-cluster-%E8%87%AA%E5%8A%A8%E5%88%87%E6%8D%A2)
> 5. [ES 切换](#es-%E5%88%87%E6%8D%A2)
>    - [5.1 跨集群复制 (CCR)](#51-%E8%B7%A8%E9%9B%86%E7%BE%A4%E5%A4%8D%E5%88%B6-ccr)
>    - [5.2 切换策略](#52-%E5%88%87%E6%8D%A2%E7%AD%96%E7%95%A5)
> 6. [只读模式与业务降级](#%E5%8F%AA%E8%AF%BB%E6%A8%A1%E5%BC%8F%E4%B8%8E%E4%B8%9A%E5%8A%A1%E9%99%8D%E7%BA%A7)
> 7. [关键挑战与应对](#%E5%85%B3%E9%94%AE%E6%8C%91%E6%88%98%E4%B8%8E%E5%BA%94%E5%AF%B9)
> 8. [最佳实践](#%E6%9C%80%E4%BD%B3%E5%AE%9E%E8%B7%B5)

## 背景

DB 切换的解决方案，分为 **Switchover**（计划内切换）和 **Failover**（计划外切换）。

这里的 DB 可能包含多种类型：Redis、MySQL、ES 等。不同数据库的复制机制和切换策略有显著差异。

核心问题：
- 怎么执行数据复制和保证数据一致？
- 怎么保证切换中间不会出现数据不一致？

## 通用解决思路

核心步骤：

1. **建立备集群** — 准备好目标集群/实例。
2. **建立数据复制通路** — 建立从主到备的数据同步通道。
3. **根据情况决定是否将老库置为只读模式** — MySQL、Redis、ES 均支持只读模式。
4. **清除主备模式** — 解除原主备关系，使备库可以接受写入。
5. **切换** — 将流量切换到新主库。

如果要保证严格的数据一致性，多半中间都要设置只读模式，有一段时间会有业务降级。

### 关于"写冲突"的思考

以前有点陷入死胡同了，总是在考虑处理复制数据流和新写数据流的冲突处理。实际上对于关系数据库这种，处理写冲突太复杂了，基本不可能实现。

实际的操作是在某个时间点直接将主数据库设成只读模式，让短时间的写操作失败。这样反而更简单，因为其实只读模式的时间很短。

### 关于复制方式

好像现在都基本支持类似 binlog 的方式。
- MySQL 有 GTID 来保证主备数据是一致的。
- Redis 和 ES 似乎没有一种很靠谱的方式来保证数据严格一致。这两种 DB 一般对数据的严格一致性没有那么高的要求。

## MySQL 切换

### MySQL Switchover

对于计划内切换（switchover），有成熟的解决方案。

**标准流程**：

1. **确认复制状态**：确保从库已追上主库（`Seconds_Behind_Master = 0`），所有 relay log 已消费完。
2. **设置主库只读**：`SET GLOBAL read_only = ON`，等待已有事务完成。
3. **等待从库追上**：确认从库的 `Seconds_Behind_Master = 0`。
4. **解除主从关系**：在从库上执行 `STOP REPLICA`，然后 `RESET MASTER`。
5. **切换流量**：修改应用的数据库连接配置，指向新主。
6. **重建反向复制**（如需切换回来）：将原主变成新主的从库，`CHANGE REPLICATION SOURCE TO`。
7. **恢复写入**：在新主上关闭只读模式。

### MySQL Failover

计划外切换，主库不可用时自动或手动执行。

**流程**：

1. **检测故障**：健康检查或仲裁机制判定主库不可用。
2. **选择新主**：从从库中选择一个数据最新的（`SHOW REPLICA STATUS` 确认 `Exec_Master_Log_Pos` 最大）。
3. **晋升新主**：`STOP REPLICA` → `RESET MASTER` → 关闭 `read_only`。
4. **重建拓扑**：其余从库执行 `CHANGE REPLICATION SOURCE TO` 指向新主。
5. **重定向应用**：更新连接配置或使用 DNS/Proxy 切换。

**风险**：
- 异步复制下，新主可能缺少主库最后的一些事务（数据丢失）。
- 脑裂风险：主库并未真正故障，两个节点都接受写入。需要通过强化故障检测（多路心跳、STONITH）防止。

### GTID

GTID（Global Transaction Identifier）是 MySQL 5.6+ 引入的全局事务标识符。

**核心价值**：
- 每个事务有全局唯一 ID（`server_uuid:transaction_id`），简化了主从切换。
- GTID-based 复制不需要指定 binlog 文件名和位置，自动定位（Auto-Positioning）。
- 主从切换时，新主直接通过 GTID 集合与从库对齐，无需手动计算 binlog 位置。

**GTID 优势对比**：

| 特性 | 基于文件位置 | 基于 GTID |
|------|------------|-----------|
| 切换时指定位置 | 需要手动计算 `MASTER_LOG_FILE` 和 `MASTER_LOG_POS` | 自动定位，无需指定 |
| 数据一致性检查 | 需要手动比对 | 通过 GTID 集合自动保证 |
| 重复事务处理 | 可能重复应用 | GTID 相同的事务自动跳过 |
| 拓扑重构复杂度 | 高 | 低 |

**生产建议**：强烈建议开启 GTID + Row-Based Replication。

## Redis 切换

### Redis Switchover

- 在不使用分布式锁和 Lua 脚本的情况下，比 MySQL 更简单。
  - Cache 场景下，直接 warm up 备库再切换即可。因为 Redis 作为缓存，即使丢一小部分数据也可以容忍。
- 使用了分布式锁或者 Lua 脚本：
  - 这个会麻烦很多，因为锁状态和脚本执行结果在复制中没有保证。
  - 需要确认备库已完全追上（`INFO replication` 确认 `master_repl_offset` 对齐）。
- 双写：切换期间同时写入主备，然后逐步切换到新主。

**手动切换步骤（Sentinel 管理下）**：
1. 确认备库复制状态正常（`master_link_status:up`，offset 接近）。
2. 可选：将主库设为只读（`CONFIG SET slave-read-only yes`，实际 Redis 是通过 `RENAME` 或 ACL 限制写入）。
3. 执行 `SENTINEL FAILOVER <master-name>` 触发 Sentinel 切换。
4. Sentinel 会自动晋升一个备库为新主，并更新其他备库的复制关系。
5. 应用通过 Sentinel 发现新主地址。

### 2. Sentinel 自动故障转移

Redis Sentinel 是 Redis 官方提供的高可用方案。

**部署要求**：
- 至少 3 个 Sentinel 实例（奇数个），分布在不同故障域。
- Sentinel 之间通过 Gossip 通信，使用 Raft 风格的选举做故障决策。
- Quorum 数量决定几个 Sentinel 同意才能判定主库下线。

**Sentinel 工作流程**：
1. **Monitoring**：每个 Sentinel 定期 PING 所有已知节点。
2. **SDOWN（主观下线）**：单个 Sentinel 发现节点不可达。
3. **ODOWN（客观下线）**：多个 Sentinel 都报告不可达，达到 Quorum 数量。
4. **Leader 选举**：Sentinel 集群选举一个 Leader 负责执行故障切换。
5. **晋升**：Leader 选择一个备库晋升为新主（优先级最高 → offset 最新 → runid 最小）。
6. **重新配置**：Leader 通知其他备库复制新主，更新配置。
7. **通知客户端**：客户端通过 Sentinel API 获取新主地址。

**注意事项**：
- 异步复制导致切换时可能丢失写入数据。
- Sentinel 网络分区时不能保证安全切换。
- Sentinel + Docker 有 NAT/端口映射问题，需用 `--net=host`。

### 3. Redis Cluster 自动切换

Redis Cluster 提供自动分片和高可用。

**核心概念**：
- 16384 个 hash slots，每台 Master 负责一部分。
- 每个 Master 可以有多个 Replica。
- 节点间通过 Cluster Bus（端口 +10000）通信。

**故障切换**：
1. 节点定期 Ping-Pong 检查健康状态。
2. 如果某 Master 超过 `cluster-node-timeout` 不可达，其 Replica 发起选举。
3. 超过半数的 Master 投票同意后，Replica 晋升为新 Master。
4. 集群自动更新 slot 映射。

**一致性保证**：
- Redis Cluster **不保证强一致性**。
- 异步复制：Master 回复 OK → 传播到 Replica → 如果 Master 在传播前崩溃，写入丢失。
- 网络分区：客户端被隔离到 minority 分区时写入被丢弃。

## ES 切换

### 5.1 跨集群复制 (CCR)

Elasticsearch 的 Cross-Cluster Replication 采用 **Active-Passive 模式**。

**架构特点**：
- **Leader index**（主动索引）：接受写入的源索引。
- **Follower index**（从索引）：只读的副本索引，从 Leader 拉取变更。
- 从索引通过 Pull 模式从远程集群拉取数据，与 MySQL/Redis 的 Push 模式不同。

**拓扑模式**：
- **单向复制**：一个集群只有 Leader，另一个只有 Follower。
- **双向复制**：每个集群同时有 Leader 和 Follower，实现互备。
- **链式复制**：A → B → C 形成复制链。
- **一对多**：一个 Leader 复制到多个 Follower 集群做灾备。

**版本要求**：Follower 集群必须运行与 Leader 集群相同或更新的版本。

### 5.2 切换策略

同 Redis，ES 切换相对简单。

**手动切换**：
1. 确认 CCR 同步正常（`/_ccr/stats` API 检查 lag 和读写情况）。
2. 停止写入到 Leader。
3. 等待 Follower 追上（`follower_indexing_checkpoint` 对齐）。
4. 将 Follower index 设为可写（移除 `index.blocks.read_only` 限制）。
5. 修改应用连接指向 Follower。
6. 如需切换回来，重建反向 CCR（原 Leader 变成 Follower）。

**注意事项**：
- ES 的 CCR 使用 Pull 模式，数据从 Leader 主动拉取，因此备集群的 CCU 和带宽需要提前规划。
- 版本兼容性需要提前确认。

## 只读模式与业务降级

为了保证严格的数据一致性，大多数切换方案需要在某个时间点将老库设为只读。

**MySQL**：`SET GLOBAL read_only = ON`。超级用户仍可写，普通用户只读。完全阻断写需要额外使用 `super_read_only = ON`。

**Redis**：没有原生的 `read_only`，可以通过 `CONFIG SET` 修改 ACL 或 `RENAME_COMMAND` 限制写命令。但 Sentinel 切换时不存在只读中间状态。

**ES**：通过 `PUT _all/_settings` 设置 `index.blocks.read_only_allow_delete: true` 将整个集群设为只读；或通过 `index.blocks.write: true` 精确控制。

**业务降级时间**：只读窗口一般控制在秒级，但以下因素会延长：
- 大事务未完成（MySQL）。
- 慢查询阻塞切换。
- 备库追赶延迟过大（跨 Region 场景明显）。

## 关键挑战与应对

### 1. 切换时的数据丢失
- **问题**：异步复制下，主库的最后几笔写入可能尚未到达备库。切换后这些写入丢失。
- **应对**：
  - MySQL：开启 `sync_binlog = 1` + `innodb_flush_log_at_trx_commit = 1` 减少丢失窗口；半同步复制（`rpl_semi_sync_master_wait_point = AFTER_SYNC`）。
  - Redis：使用 `WAIT` 命令同步复制关键写入；但是会降低性能。
  - ES：等待 follower checkpoint 对齐后再切换。

### 2. 主备数据不一致
- **问题**：复制延迟导致主备数据差异。
- **应对**：
  - MySQL GTID 自动检测不一致并跳过或修复。
  - Redis `ROLE` / `INFO replication` 监控 offset。
  - ES `/_ccr/info` API 监控 checkpoint。

### 3. 切换期间的业务降级
- **问题**：只读窗口导致写失败，影响用户体验。
- **应对**：
  - 设计重试机制和队列缓冲。
  - 尽量缩短只读窗口（自动化切换步骤）。
  - 使用灰度切换逐步迁移流量。

### 4. 脑裂 (Split-Brain)
- **问题**：网络分区导致两边都认为自己是主，都接受写入。
- **应对**：
  - MySQL：使用仲裁工具（Orchestrator + 多路心跳）或 STONITH。
  - Redis Sentinel：少数派分区不会自动切换，保证至少 Quorum 个 Sentinel 可达。
  - Redis Cluster：Master 在 `cluster-node-timeout` 内无法与大多数 Master 通信则进入 FAIL 状态。

## 最佳实践

1. **自动化切换流程**：手工切换容易出错，所有切换步骤应脚本化、自动化。

2. **开启只读模式时做好超时**：设置较短的 `lock_wait_timeout`（MySQL），避免被长时间运行的事务阻塞切换。

3. **Swichover 优先**：计划内切换尽量用 switchover 而非 failover，可控性强。

4. **预留冗余容量**：备库/从集群需要足够的资源承载切换后的流量。

5. **DNS/Proxy 层解耦**：应用不直接连接数据库 IP，通过 DNS（修改 TTL）或 Proxy（如 ProxySQL / HAProxy / Envoy）切换，减少应用重启。

6. **DR 演练**：定期执行真正的切换演练（而非只在测试环境），验证流程并暴露隐患。

7. **监控切换关键指标**：
   - Replication Lag（秒级）
   - 只读窗口时间（毫秒级）
   - 切换失败率
   - 数据一致性校验结果

8. **考虑最终一致的影响**：切换完成后，应用层要能处理"写新库读不到旧库数据"的情况，做好补偿机制。
