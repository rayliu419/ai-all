## 容灾设计

容灾（Disaster Recovery, DR）是系统设计中最硬核的环节之一。和高可用（HA）的区别在于：HA 容忍单点故障（一台机器、一个进程挂掉），DR 容忍区域级故障（整个 AZ 掉电、整个 Region 网络中断）。

**核心指标：**
- **RTO (Recovery Time Objective)** — 从故障发生到恢复服务，能接受多长时间。
- **RPO (Recovery Point Objective)** — 能接受丢失多长时间的数据（即最近一次备份到故障点的时间差）。
- AZ 级容灾通常追求 RPO ≈ 0（同步复制，数据不丢）、RTO 秒级（自动切换）。
- Region 级容灾通常 RPO > 0（异步复制）、RTO 分钟级（DNS 切换、数据恢复）。

---

### AZ 级容灾

#### 原理

AZ（Availability Zone）是同一 Region 内隔离的数据中心集群，AZ 之间通过高速专用网络互联，延迟通常在 1-2ms 以内。这种低延迟使得**同步复制**成为可能。

AZ 级容灾的核心：**3AZ 部署 + 多数派协议（如 Raft/Paxos）**。

- 3AZ 是最常见的部署拓扑：3AZ 中任一 AZ 整体失效，剩余 2AZ 仍能形成多数派（Quorum = 2），继续提供服务。
- 强一致场景下，RPO = 0（同步复制确保不丢数据），只是性能有损耗（写操作的 p99 延迟会增加 1-3ms）。
- 少数派 AZ 中的节点自动变为只读或下线，不会导致脑裂。

#### 支持 AZ 级容灾的有状态中间件

以下中间件原生支持 3AZ 部署，能够在单个 AZ 完全掉电后继续提供服务（RPO ≈ 0，RTO 秒级自动切换）：

| 中间件 | 容灾机制 | 说明 |
|--------|----------|------|
| **Etcd / ZooKeeper** | Raft / ZAB 多数派协议 | 3 节点各部署在不同 AZ，任一 AZ 挂掉剩余 2 节点 ≥ Quorum，写入正常。 |
| **Kafka** | 分区副本跨 AZ 分布 | 每个分区 3 副本分布在 3AZ，ISR 同步复制。一个 AZ 挂掉后，剩余副本重新选举 leader。需注意：AZ 故障时部分 follower 可能不在 ISR 中，会暂时降低写入的 min.insync.replicas 满足度。 |
| **MongoDB** | Sharding + Raft (副本集) | 每个 shard 的副本集分布在 3AZ，primary 和 secondary 跨 AZ 部署。一个 AZ 挂掉，副本集自动选举新 primary。 |
| **CockroachDB** | Raft + 自动 rebalance | 每个 range 默认 3 副本跨 AZ/Region 分布，AZ 故障后自动在存活节点补充副本。 |
| **Redis Enterprise / ElastiCache** | 跨 AZ 副本 | 主从分属不同 AZ，AZ 故障触发自动 failover。注意：Redis 原生主从是异步复制，极端场景下可能丢少量数据。 |

> **纠偏：** 原始笔记中提到 "MongoDB 使用 sharding 模式，实际上先 sharding，再 raft 复制"。准确地说，MongoDB 的副本集（Replica Set）使用 Raft 协议（类）做数据复制和 leader 选举；Sharding 是数据分片，每个 shard 本身就是一个副本集。二者是正交的——即使不分片，单个副本集也能跨 AZ 部署。

#### K8s 控制面的 AZ 容灾

K8s 本身也支持 3AZ 部署控制面：

- **etcd 集群**：3 或 5 节点分布在 3AZ，容忍 1-2 个 AZ 故障。
- **API Server**：无状态，多副本部署在 3AZ，前面挂负载均衡。
- **Scheduler / Controller Manager**：Leader Election 机制，只有一个实例活跃，挂掉后自动切换。

#### 无状态服务的 AZ 部署

无状态服务本身不存储数据，容灾相对简单：**3AZ 多副本部署 + 负载均衡**。

- 每个 AZ 部署一定数量的 Pod 实例（如 N+1 容量规划：每个 AZ 容量能承载总流量的 50%，挂一个 AZ 后剩余两个能扛住）。
- Service Mesh（Istio 等）或 ALB/Nginx 负责跨 AZ 流量分发。
- 故障检测：Readiness Probe 检测 Pod 是否正常，异常的自动从 endpoints 剔除。

---

### Region 级容灾

#### 为什么比 AZ 级难得多

Region 级容灾是系统设计中最复杂的场景，原因：

| 因素 | AZ 级 | Region 级 |
|------|-------|-----------|
| 网络延迟 | 1-2ms（专用光纤） | 50-200ms（公网/跨洲） |
| 数据复制 | 同步复制可行 | 只能异步复制 |
| 数据冲突 | 一致性协议解决 | 多写冲突不可避免 |
| 流量切换 | 负载均衡自动切换 | DNS 切换（分钟级） |
| 状态迁移 | 无状态 + 共享存储 | 有状态数据需跨 Region 同步 |

正因为跨 Region 延迟高，**同步复制不可行**（一笔写入等 200ms 才返回，P99 延迟爆炸），所以 Region 级容灾必须接受**异步数据复制**，由此带来 RPO > 0 和数据冲突问题。

#### 多 Region 容灾的架构模式

**模式 1：Active-Passive（主备）**

- 一个 Region 承担所有读写流量，另一个 Region 只做数据同步，不接流量。
- 主 Region 挂掉后，DNS 解析切到备 Region，数据层恢复后即可继续服务。
- 优点：简单，无需处理数据冲突。
- 缺点：备 Region 资源闲置；切换有 1-10 分钟停服窗口（DNS TTL + 数据恢复）；备 Region 长期不接流量，真切换时可能各种问题。

**模式 2：Active-Active（多活）**

- 多个 Region 同时接受读写流量。
- 优点：用户就近访问延迟低；资源充分利用；一个 Region 挂掉后其他无缝接管。
- 缺点：必须处理数据冲突；架构复杂度大幅增加。

> **关于 "同步跨 Region 调用" 的澄清：** 原始笔记中写道 "同步的跨 region 调用需要被避免，应该尽量使用 regional 资源"。这条原则本身是对的——跨 Region 同步调用会让请求增加 50-200ms 延迟，且跨 Region 网络抖动会直接影响用户体验。
>
> 但这不是铁律。在一些场景下，**跨 Region 同步查询**是可接受的（例如只读查询，不涉及写入一致性），或者使用 **Async + Callback** 模式替代同步调用。需要具体分析：
> - 如果业务容忍高延迟：可以使用跨 Region 同步调用。
> - 如果业务不要求强一致：可以使用本地缓存 + 异步刷新。
> - 如果跨 Region 调用不可避免：考虑使用全球负载均衡（如 AWS Global Accelerator）优化路径。

#### 多 Region 容灾的基本要求

1. **异步数据复制** — 跨 Region 数据同步必须是异步的。需要考虑：
   - 数据冲突策略：LWW（Last Write Wins）、CRDT、按用户分片。
   - 复制延迟监控：延迟过大时触发告警或切换。

2. **全局网络基础设施** —
   - AWS 提供 Global Accelerator 和 Direct Connect 来优化跨 Region 网络路径。
   - 各云厂商都有高速专用网络做多 Region 数据拷贝。

3. **服务无状态化** — 服务本身不持有本地状态，所有状态存储在外部（DB、Cache）。这是多 Region 部署的前提。

4. **DNS 与流量路由** —
   - Route 53（AWS）或类似服务做基于延迟 / 地理位置的路由。
   - Health check 自动摘除故障 Region。

#### 云厂商的 Region 级容灾能力

| 云服务 | 容灾能力 | 一致性保证 |
|--------|----------|-----------|
| **AWS S3 跨 Region 复制** | 跨 Region 异步复制，自动同步 | 最终一致性。新版 Multi-Region Access Points 可实现 Active-Active。 |
| **DynamoDB Global Tables** | 多 Region 多写，自动冲突解决（LWW） | 最终一致性。同一 Region 内读自身写是强一致，跨 Region 读可能有部分秒级的滞后。 |
| **Aurora Global Database** | 一个 Region 主写，最多 5 个只读 Region，异步复制延迟 <1秒 | 主 Region 写完成后，其他 Region 异步复制，通常 1 秒内可见。 |
| **Spanner (GCP)** | TrueTime + 锁机制实现跨 Region 强一致 | 真正的强一致跨 Region 写入，但延迟较高（p99 约 50-100ms），成本极高。 |

> **纠偏：** 原始笔记中说 "相比 AZ 级的容灾差不少"。这话不完全准确。DDB Global Tables 和 Spanner 的 Region 级容灾确实有 RPO > 0（异步复制），但在**用户就近访问和 Region 级故障转移**方面，它们解决的是 AZ 级无法解决的问题——你的 AZ 级再多副本，整个 Region 断电了全都白搭。不能简单说"差不少"，只能说各有各的天花板。

---

### 容灾统一考虑

所有容灾手段归根结底都可以归纳为两件事：

#### 冗余

冗余在不同层面有不同的含义：

1. **组件自带的冗余** — 分布式存储的多数派复制（Raft 写多数节点才算成功），组件自身就有容错能力。
2. **相同功能组件的冗余** — 同一个功能有多个实现，例如大数据既用 DLI（华为）又有 MRS（另一种计算引擎），一个挂了用另一个。
3. **同组件不同实例的冗余** — 同一个服务部署多个实例，分布在多个 AZ 或 Region，例如 DLI 可以调用多个 Region 的计算资源。

#### 检测失败

冗余再多的组件，检测不到故障就没法切流：

- **无状态服务的健康检查** — Nginx/ALB 的主动健康探测，K8s 的 Liveness/Readiness Probe。
- **有状态服务的故障检测** — Raft leader 心跳超时、ZAB 的 follower 心跳、Kafka ISR 同步检测。
- **拨测（Probe）与 Readiness 结合** — 服务不仅检测自身进程是否活着，还检测依赖组件（DB、下游服务）是否可达。如果依赖挂了，Readiness 返回 false，让流量不要来。

---

### 容灾的 High-Level 设计思路

#### 第 1 步：找出故障点

列出系统中的所有组件，标注出：
- 核心路径上的组件（离开它业务就跑不了）。
- 单点故障（只有一个实例、单 AZ）。
- 弱依赖（挂了有降级方案，不影响核心功能）。

> 参见 [high-availability.md](./high-availability.md) 中 Graceful Degradation 的降级层次。

#### 第 2 步：区分有状态 / 无状态

- **有状态服务** — 数据通过多副本复制来提供容灾。优先使用原生支持 AZ 级容灾的组件（Etcd、Kafka、MongoDB、CockroachDB）。
- **无状态服务** — 容灾相对简单，主要考虑处理能力的冗余。通过 API Gateway、DNS 做流量分发。

#### 第 3 步：确定容灾级别

| 条件 | 建议 |
|------|------|
| 只有单 Region 可用 | AZ 级容灾，3AZ 部署 |
| 需要全球用户低延迟 | Region 级 Active-Active |
| 合规要求数据不出国 | 按 Region 隔离，每个 Region 独立部署 |
| 业务对数据一致性要求极高 | AZ 级强一致（同步复制），Region 级做灾备（异步 + 人工切换） |

#### 第 4 步：设计故障切换流程

- 什么时候触发切换？（监控指标、阈值）
- 切换是自动还是半自动？
- 切换后怎么恢复原状？（failback 流程）
- 有没有演练过？（定期 Chaos Engineering）

#### 第 5 步：考虑上游结合

- **重试 + 指数退避** — 上游客户端做好重试策略，配合下游容灾切换。
- **消息队列削峰** — Queue 可以帮助缓冲流量，延迟消费。即使下游暂时不可用，消息不丢。
- **熔断 + 降级** — 检测到跨 Region 延迟异常升高时熔断，走本地降级方案。

---

### 参考

1. [知乎：高可用架构设计](https://zhuanlan.zhihu.com/p/515303354)
2. [Azure: Building solutions for high availability](https://learn.microsoft.com/en-us/azure/architecture/high-availability/building-solutions-for-high-availability)
3. [AWS: How to get high availability in architecture](https://aws.amazon.com/cn/blogs/startups/how-to-get-high-availability-in-architecture/)
4. [RightScale: High Availability in the Cloud (PDF)](https://s3.amazonaws.com/aws001/guided_trek/GuidedTrek_RightScale_High%20Availability%20in%20the%20Cloud_SanFran.pdf)
5. [掘金小册：MySQL 实战宝典 - 高可用设计](https://learn.lianglianglee.com/%E4%B8%93%E6%A0%8F/MySQL%E5%AE%9E%E6%88%98%E5%AE%9D%E5%85%B8/17%20%20%E9%AB%98%E5%8F%AF%E7%94%A8%E8%AE%BE%E8%AE%A1%EF%BC%9A%E4%BD%A0%E6%80%8E%E4%B9%88%E6%B4%BB%E7%94%A8%E4%B8%89%E5%A4%A7%E6%9E%B6%E6%9E%84%E6%96%B9%E6%A1%88%EF%BC%9F.md)
6. [腾讯云：高可用架构设计](https://cloud.tencent.com/developer/article/1624636)
7. [知乎：异地多活架构设计](https://zhuanlan.zhihu.com/p/102245185)
8. [系统设计：高可用架构](https://dunwu.github.io/design/pages/9a462f/)
9. [ITPub：容灾高可用设计](http://blog.itpub.net/70024924/viewspace-2931140/)
10. [Pluralsight: How to build a multi-region active-active architecture on AWS](https://acloudguru.com/blog/engineering/why-and-how-do-we-build-a-multi-region-active-active-architecture)
11. [Azure: Architecture strategies for using availability zones and regions](https://learn.microsoft.com/en-us/azure/well-architected/design-guides/regions-availability-zones)
