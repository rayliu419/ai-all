# 微服务中的幂等性 (Idempotency)

## 什么是幂等性
**定义**：对同一个操作执行一次和执行多次，产生的效果（副作用）是一样的。

- **为什么重要**：在分布式系统中，网络是不可靠的。上游服务调用下游服务时，可能出现：
    - 请求发出去了，但响应超时了（请求到底执行了没有？不知道）
    - 消息队列重复投递（Kafka rebalance 导致 offset 回退）
    - 用户手抖双击了“支付”按钮
    - 负载均衡器自动重试
- 如果下游操作不是幂等的，重试可能导致**重复扣款、重复下单、重复发货**——灾难性后果。

## Exactly-Once
**Exactly-Once 语义在分布式系统中是不可能直接实现的**（FLP 不可能性推论）。
**核心洞察**：上游负责“不丢”，下游负责“不重”。两者结合起来就是 Exactly-Once 的**效果**。

| 层 | 职责 | 实现 |
|---|---|---|
| **上游（发送方）** | **At-Least-Once**：保证消息至少发送一次，允许重复 | 超时重试、持久化消息（WAL、Outbox）、ACK 确认机制 |
| **下游（接收方）** | **At-Most-Once Processing**：保证同一个业务操作最多执行一次 | 幂等键去重、条件写入、绝对值写入 |

## 幂等性实现策略

### 策略一：使用绝对值而非增量（天然幂等）
**原理**：写操作不使用增量（`balance += 100`），而使用绝对值（`balance = 1100`）。无论执行多少次，结果都一样。

**适用场景**：
- 状态机更新（`SET status = 'SHIPPED'`，多次设置无影响）
- 用户信息覆盖写（`SET email = 'new@email.com'`）
- ES 的 `upsert`：以 `_id` 为主键，覆盖写天然幂等（参见 [geo-replication.md](./geo-replication.md) 中 Debezium 案例）
- DynamoDB 的 `PutItem`：整条覆盖写

**局限**：
- 很多业务场景必须用增量操作（如扣减库存、累加积分）
- 需要先“读”再“算”再“写”，有并发竞争风险
- 需要配合乐观锁（CAS / Conditional Write）保证并发安全（参见 [design-pattern.md](./design-pattern.md) 中 DynamoDB Conditional Write）

---

### 策略二：幂等键去重 (Idempotency Key / Deduplication)

**原理**：每个请求携带一个全局唯一的 `idempotency_key`（或 `message_id`、`request_id`）。下游在处理前检查该key是否已处理过；如果已处理，直接返回之前的结果。
**关键**：**幂等键的检查和业务逻辑必须在同一个事务中**，否则存在 check-then-act 的竞态条件。

**实现变体**：
#### 变体 A：数据库唯一约束（最常用）
```python
try:
    with db.transaction():
        db.execute("INSERT INTO processed_messages (message_id) VALUES (%s)", [msg_id])
        # 如果 message_id 已存在，INSERT 抛唯一约束异常 -> 事务回滚 -> 跳过处理
        process_business_logic(message)
except UniqueViolationError:
    log.info(f"Message {msg_id} already processed, skipping")
    return_previous_result(msg_id)
```

#### 变体 B：DynamoDB Conditional Write + TTL
- 利用 DDB 条件写入实现原子去重
```python
table.put_item(
Item={
'idempotency_key': f'pay-{order_id}',
'result': json.dumps(result),
'ttl': int(time.time()) + 86400  # 24小时后自动清理
},
ConditionExpression='attribute_not_exists(idempotency_key)'
)
# 如果 key 已存在 -> ConditionCheckFailedException -> 跳过
````

### 策略三：乐观锁 / 版本号 (Optimistic Locking / CAS)
- 原理：每次写入时检查版本号或前置条件，只有条件满足才执行。
```
  -- 带版本号的更新
  UPDATE orders
  SET status = 'PAID', version = version + 1
  WHERE order_id = 'order-123' AND version = 5;
  -- 如果 version 不再是 5（被其他人改过了），影响行数 = 0，更新失败
```

## 幂等设计的常见陷阱

### 幂等键过早失效
- 幂等记录 TTL 设太短（如 5 分钟），但上游的重试间隔可能长达几小时
- 解决：TTL 应覆盖上游最大可能的重试窗口（通常 24-72 小时）

### 幂等键选择不当
```python
# ❌ 用 UUID 做幂等键：每次重试生成新 UUID，根本起不到去重效果
idempotency_key = str(uuid.uuid4())

# ✅ 用业务标识做幂等键：同一笔订单的支付请求用同一个 key
idempotency_key = f"pay-{order_id}"
```

###只考虑了成功路径
- 第一次执行失败了（如DB超时），幂等记录是否写入了？
- 如果失败时幂等记录已写入 $\rightarrow$ 后续重试永远被跳过 $\rightarrow$ 
- 请求丢失解决：只在业务成功执行后才标记为已处理，或在事务中一起提交

### 返回值不一致
- 幂等不仅意味着"不重复执行"，还意味着"返回一样的结果"
- 第一次返回 {"status": "success", "transaction_id": "txn-456"}
- 第二次应该返回完全一样的结果，而不是 {"status": "duplicate"}