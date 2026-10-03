# Grafana 实战笔记

Grafana 是"查询 + 渲染"层：它不存原始数据，只把数据源的查询结果画成图。因此排查问题时，**先怀疑采点与聚合，再怀疑业务**。

## 1. 模板变量（Template Variables）

用途：把一个 dashboard 复用到多组对象上（多机器、多实例、多集群），避免复制面板。

原始指标形如 `node_uname_info{nodename="xxxx", instance="yyyy"}`。

### 1.1 Query 变量

```promql
label_values(node_uname_info{nodename=~".*"}, nodename)
```

- `label_values(指标选择器, 标签名)`：先筛选时间序列，再取该标签的所有取值作为变量候选。
- 也可以用固定的候选值（枚举场景）。

主要配置项：

| 配置 | 含义 |
|---|---|
| Name | 变量名，面板里用 `$name` 引用 |
| Type | `Query` = 值来自查询；也可为 Custom/Interval 等 |
| Label | 在 dashboard 顶部显示的名字 |
| Data source | 变量查询走哪个数据源 |
| Refresh | 何时刷新：Never / On Dashboard Load / On Time Range Change |
| Query | 取值的表达式，如 `label_values(...)` |
| Regex | 对取到的值再做一次正则过滤/捕获 |
| Sort | 候选值排序 |
| Multi-value | 允许选多个值（查询里变成多个条件） |
| Include All | 是否提供 `All` 选项 |
| Preview of values | 候选项预览，用于确认查询写对 |

enrich: 变量配置界面每一项的截图与标注

### 1.2 级联变量

让一个变量的候选项依赖另一个变量的当前值：在查询里直接引用上游变量。

```promql
label_values(node_uname_info{nodename=~"$nodename", instance=~".*"}, instance)
```

- `$nodename` 是上游变量的值；通常配 `Refresh = On Dashboard Load`，保证顺序。
- 多选时 `$var` 会展开成多个值，正则匹配要用 `=~`。

enrich: 级联变量的界面截图（instance 引用 $nodename）

### 1.3 在面板中使用

```promql
(1 - avg(irate(node_cpu_seconds_total{mode='idle', nodename=~"$nodename", instance=~"$instance"}[5m])) by (instance)) * 100
```

- Panel title：`$instance CPU使用率`
- Legend：`{{instance}} CPU使用率`
- 条件变量：随其他变量取值而出现/隐藏，用于减少无关选项。

enrich: 面板中引用变量的截图（查询 + Legend + 标题）

## 2. 告警

链路：**Alert rule（判定）→ Notification policy（按 label 路由）→ Contact point（发送渠道）**。

- Alert rule：定义 Query、Condition、Evaluate；再 Add labels。
- Notification policy：决定"何时、通过什么渠道、发给谁"，按 label 匹配（例如 `rule_uid = checkout`）。
- Contact point：Slack / Webhook / VictorOps 等。
- 两个易漏参数：`pending`（FOR 持续时间，满足多久才算真正告警）、NO DATA 的处理方式。

### 2.1 状态机与两个易漏参数

状态迁移：OK —Rule TRUE(incl FOR)→ PENDING —FOR satisfied→ ALERTING；PENDING —FOR not satisfied→ OK；ALERTING —Rule TRUE(excl FOR)→ PENDING；ALERTING —Rule FALSE→ OK；任一状态无数据 → NO DATA，数据恢复 → OK。

enrich: Alert 状态机图 + 状态迁移表

### 2.2 Use Case：checkout_front_web landing 告警

| 表达式 | 作用 |
|---|---|
| `A = Mimir-PE` | 数据源查询，得到"landing 比率"的比值序列 |
| `B = hour() >= 0 and hour() < 15 or on() vector(-2)` | 时间标记：白天段为真，夜间段为 -2 |
| `C = Reduce, Last(A)` | 取区间内最新值（等价看板上的 Last） |
| `E = Reduce, Last(B)` | 取区间内最新的时间标记 |
| `D = Math, ($C < 30 && $E < -1) \|\| ($C < 60 && $E > -1)` | Alert condition，白天/夜间两套阈值 |

- `D` 是真正的告警条件：9–24 点降到 30% 以下，或 0–9 点降到 60% 以下 → 告警。
- Evaluation：每 1m 执行一次表达式，并定义 no data 行为。
- Labels 决定了路由：匹配到 `rule_uid = checkout` 的 notification policy，最终走 contact point `checkout-victorops-critical`。

## 3. PromQL

### 3.1 指标格式

```text
http_request_total{status="200", method="GET"} @14242512313   =>  93455
|---- 指标名 ----|--------- 标签 --------|     时间戳           值
```

- 标签由埋点/采集端写入；同一指标可有多个标签组合（每条组合是一条时间序列）。
- 时间过滤：`http_request_total[5m:1m]`，取最近 5 分钟、每 1m 一个数据点。
- 标签过滤：`=`、`!=`、`=~`、`!~`。
- 聚合：`sum`、`avg`、`max`… 默认**忽略标签**（全部聚合成一条）；`sum by (path)` 保留分组。

enrich: 指标结构图

关键语义：

- `increase(x[1m])` 是**逐条时间序列**算增量的（相同标签组合才参与同一条计算）。
- 聚合函数不能直接作用于时间选择器：`increase(sum(x[1m]))` 不合法。

### 3.2 Use Case 1：区间请求总量

```promql
sum(increase(http_request_total{path="/test"}[1m]))
```

以 20:00:00 这个时刻为例，求值顺序：

1. `http_request_total{path="/test"}`：筛出 path 为 `/test` 的数据点。
2. `[1m]`：取过去 1 分钟的数据点（`increase` 必须与 `[]` 搭配）。
3. `increase()`：范围内首末数据点之差，得到每秒计时序列上的增量。
4. `sum()`：把所有序列的增量相加。

得到的只是 20:00:00 这一个点；Grafana 会对 20:00:30、20:01:00… 各算一次，连成曲线。

**为什么不能写成 `increase(sum(http_request_total{path="/test"}[1m]))`**：`sum` 不能作用于时间选择器，其他聚合（`avg` 等）同理。

### 3.3 Use Case 2：P95 延迟

```promql
histogram_quantile(0.95,
  sum(rate(nginx_request_seconds_bucket{role=~"$role", instance_id=~"$instanceId"}[$time_range])) by (path, le)
)
```

`nginx_request_seconds_bucket` 是直方图类型（按 `le` 桶累计计数）。

1. 标签过滤 → 2. `rate(...[$time_range])`：时间范围内每秒落入各桶的请求数 → 3. `sum ... by (path, le)`：按路径和桶上限聚合 → 4. `histogram_quantile(0.95, ...)`：据此估算 95% 的请求落在多少秒内。

### 3.4 Use Case 3：同比（offset）

```promql
sum(increase(http_request_total{path="/test"}[1m]))            # 当前
sum(increase(http_request_total{path="/test"}[1m] offset 1m))  # 1 分钟前/昨天
```

比较今天与昨天、同一周的同一点，都用 `offset`。

### 3.5 Use Case 4：label_replace

改写标签值（例如去掉端口、统一命名），便于跨实例聚合。笔记只记用法名，细节按需查文档。

## 4. LogQL

与 PromQL 能力类似（过滤 + 聚合），**独有的能力是从日志文本中抽取信息**。

### 4.1 Use Case 1：错误日志计数

```logql
sum(count_over_time({role="$role", filenam!="access.log", host=~"${host}"} != "INFO" | json | level="ERROR" | line_format `{{.log}}`[$_range]))
```

1. 行过滤：`{...} != "INFO"` → `| json` 解析 → `| level="ERROR"` 过滤。
2. `count_over_time(...[$_range])`：统计日志条数，此时**未聚合**（日志没有类似 `http_server_requests_seconds_count` 的现成计数，要自己数）。
3. `sum()`：把多条流合并成一条。

### 4.2 Use Case 2：正则 / pattern 抽取字段

```logql
{cluster="eu-west-1", level="info"}
|= `completing block`
| json
| pattern `<_> userid=<id> <_>`
| line_format "{{.id}}"
```

逐级：关键字过滤 → JSON 解析 → pattern 抽取 `userid` → 只输出该字段。用于把"原始日志"变成可聚合的维度。

## 5. 图表细节（进阶）

### 5.1 Y scale 的极值问题

出现极值时坐标轴步长被拉大，正常波动被压平。Grafana 自动适配缩放，无法手动指定；只能过滤异常序列或用对数轴/单独面板隔离。

### 5.2 Last / Max / Mean

时间序列常用的三个统计量，显示在 panel 右上角——区间内最新值、最大值、平均值。与告警表达式里的 Reduce(Last/Max/Mean) 是同一套语义。

### 5.3 Repeat

按某个模板变量的取值批量复制 panel/row，多实例看板不用手工复制。

## 6. 工程陷阱：图上没看见 ≠ 没发生

核心结论：**采样会吃峰，缺失会断线，聚合会抹平单实例尖峰。图只能证明“看到了什么”，不能证明“没发生什么”。**

### 6.1 采样：spike 被吃掉的四个原因

切换时间范围时只有两个参数变化：查询时间跨度、图表像素宽度。二者决定步长：

$$
\text{step} = \frac{\text{查询时间跨度}}{\text{max data points}}
$$

四层原因（各自独立、可叠加）：

1. **查询窗口本身就是滤波器**：`rate(x[5m])` 每个点 = 窗口内平均速率，10s 的 spike 落进 5m 窗口只剩 1/30。
2. **步长 > 抓取间隔 → 漏点（aliasing）**：step 决定只看哪些时刻；instant selector 取该时刻前最近的样本（lookback delta 默认 5m）。step=1.68h 而 spike 只有 10s 时，命中概率 ≈ 5%。**这不是被平均，是根本没采到。**
3. **窗口首尾相接吞掉增量**：相邻窗口不重叠时，最后一个样本到下一个窗口第一个样本之间的增量不属于任何窗口（官方例子：2 小时一跳的 counter，所有峰凭空消失）。
4. **存储层降采样不可逆**：Thanos/Cortex/Mimir 把长周期块预聚合（avg/max 由降采样配置决定，与查询无关），读大范围时自动选低分辨率块。

enrich: 短时间范围 spike 可见 vs. 长时间范围被平滑掉的对比图 + 四层原因表

算一遍（max data points = 100）：

- 过去 1 小时 → 步长 3600/100 = 36s。
- 同一指标拉到 7 天 → 步长 7×24×3600/100 = **1.68 小时**，每 1.68 小时才出一个代表点。
- 持续 10s 的 CPU spike 被稀释 → 图上“消失”。
- 代表点的取法取决于查询写法：`avg` 会平均掉，`max` 可能保留。

### 6.2 不漏峰：四层对策

| 层 | 做法 | 为什么有效 |
|---|---|---|
| 检测层（最关键） | 告警规则 + recording rules 兜底，不靠看板 | 告警按自己的 evaluation interval 评估原始数据，**不受看板 step 影响** |
| 查询层 | `$__rate_interval` 代替硬编码窗口；峰用 `max_over_time(x[1h])` | 保证窗口覆盖足够样本且相邻重叠；把峰值带进大窗口 |
| 看板层 | 显式设 Min step / max data points，Query inspector 核对；峰单独面板或叠 `max()` | 先知道图到底采了多少点 |
| 存储层 | recording rules 预产峰值指标 | 把聚合从查询期搬到写入期 |

`$__rate_interval`：

- 取值 `max($__interval + 抓取间隔, 4 × 抓取间隔)`（抓取间隔取数据源 Scrape interval，Min step 会覆盖它）。
- 至少 4 倍：窗口里要够 4 个样本 `rate()` 才算得稳；否则常只覆盖 1 个样本 → No data。
- 再加 1 个抓取间隔：让相邻窗口**重叠**，避开 6.1 的③。
- 硬编码 `rate(x[5m])` 只在抓取间隔固定且远小于 5m 时安全。

### 6.3 缺失：指标消失 ≠ 0

Grafana 不画 null/NaN：序列消失 → 断线；全部消失 → “No data”。而 `0` 是真实值，会正常画出来。

| 场景 | 机制 | 图上表现 |
|---|---|---|
| 目标被移除/进程退出 | Prometheus 写 staleness marker，序列立刻消失 | 线突然断掉 |
| 抓取失败但目标还在 | lookback delta（默认 5m）内沿用旧样本 | 线“虚”5 分钟后断掉；`up == 0` 这段时间是有数据的 |
| 重启后标签变化（pod 名、instance IP） | 这是新序列，旧序列彻底消失 | 按 `pod` 聚合的线“少了一台” |
| counter 归零 | `rate`/`increase` 当 reset 处理；`delta` 不处理 | 跨重启第一个点偏小；用 `delta` 会出现负尖脉冲 |
| 除零 | `a/b` 分母为 0 得 ±Inf/NaN | 断线或分位数 NaN |

### 6.4 把缺失画成 0 / 检测“消失”

```promql
# 空查询补 0（单线）
sum(rate(http_requests_total{job="api"}[$__rate_interval])) or vector(0)

# 按标签补 0（RHS 必须能枚举出那些标签）
sum by (pod) (rate(http_requests_total{job="api"}[$__rate_interval]))
  or (0 * sum by (pod) (up{job="api"}))

# 告警“指标消失”（重启/断采场景该告这个）
absent_over_time(http_requests_total{job="api"}[10m])

# 归一化易变标签
label_replace(sum by (pod) (rate(x[5m])), "app", "$1", "pod", "(.*)-[a-z0-9]+-[a-z0-9]+")
```

`or` 是**按标签集合**补齐的：`A or B` 返回 A 的全部序列，外加 B 中标签集合在 A 里不存在的那些。所以按标签补 0 必须让 RHS 能枚举标签（`0 * sum by (pod)(up)`）；`vector(0)` 标签集为空，只在左边整体为空时生效。

面板层：折线图的 Connect null values 只能桥接断点，不会填 0；堆叠图把“缺失”当 0 会看成“这项没流量”。

### 6.5 其他高频坑

| 坑 | 现象 | 对策 |
|---|---|---|
| rate 窗口 < 4 × 抓取间隔 | 放大范围后整块 No data | 用 `$__rate_interval` |
| 窗口与 step 对齐 | 慢速 counter 的峰全消失 | `$__rate_interval`（窗口重叠一个抓取间隔） |
| counter reset 与 increase 外推 | 整数计数算出小数、低流量被量化（1m/4 样本 → 粒度 0.25） | `increase` 是外推估算值；精确计数靠 recording rule；别用 `delta` 处理 counter |
| `by (pod)` 线爆炸 | 几百条线的“视觉平均”埋掉单实例尖峰 | 聚合到有限维度（`max by (app)`）+ 单独“最差实例”面板 |
| `topk` 掩盖长尾 | 第 k+1 名永远看不见 | topk 只用来定位，关键指标做全量聚合 |
| 除零 NaN | 比值类指标断线 | `clamp_min(分母, 1e-9)`、`a/(b>0)`，或 `or vector(0)` 兜底 |
| `histogram_quantile` NaN | 分位数错误；`by` 漏了 `le` 永远算不出 | 必须 `sum(rate(_bucket)) by (le, ...)`；确认有 `+Inf` 桶；别混不同桶配置 |
| 看板窗口 ≠ 告警窗口 | 图上正常但告警已触发（或反之） | 对齐两边窗口/频率，写进看板注释 |
| 变量不刷新 | 新 pod 不出现在下拉框 | `Refresh = On Dashboard Load` 或手动刷新 |
| 自动刷新 × 长 range | 7 天窗口 + 5s 刷新反复打后端 | 长 range 关自动刷新 |

### 6.6 最佳实践

| 做法 | 说明 |
|---|---|
| 检测不依赖看板 | 告警/recording rules 按自己的节奏评估原始数据，这是“不漏峰”的根本保障 |
| 用 `$__rate_interval` | 别硬编码 `[5m]` |
| 峰看 `max_over_time`，趋势看平均 | 一条线兼顾不了两件事 |
| 慎设 `min step` | 手动覆盖自动步长会让查询性能极差；要用就用 4 倍抓取间隔 |
| 调大 `max data points` | 短期高细节图表用；平时很少需要手动改 |
| 后端做聚合规则（recording rules） | 根本解法：把 Grafana 与 Prometheus 的粒度对齐，减少对自动计算的依赖 |
| 谨慎选聚合函数 | `avg` / `max` / `last` 决定 spike 会不会被稀释 |
| 用 Query Inspector 看 `min step` | 先确认实际步长，再判断是“真没数据”还是“被采样掉了” |

## 7. 速查表与排查清单

### 7.1 常用写法速查

| 需求 | 写法 |
|---|---|
| 变量取值 | `label_values(指标{}, 标签)` |
| 级联变量 | 查询里引用 `$上游变量` + `Refresh = On Dashboard Load` |
| 面板引用变量 | 查询 `{label=~"$var"}`、Legend `{{label}}`、标题 `$var xxx` |
| 区间增量 | `sum(increase(metric{...}[5m]))` |
| 每秒速率 | `rate(metric{...}[$__rate_interval])`（瞬时用 `irate`） |
| 分位数 | `histogram_quantile(0.95, sum(rate(bucket{...}[$range])) by (le, path))` |
| 同比 | `...[1m] offset 1d` |
| 日志计数 | `sum(count_over_time({...} |= "ERROR" [$__range]))` |
| 日志抽字段 | `\| json \| pattern `<_> userid=<id> <_>` \| line_format "{{.id}}"` |
| 保峰 / 保谷 | `max_over_time(x[1h])` / `min_over_time(x[1h])` |
| 空查询补 0 | `sum(rate(x[$__rate_interval])) or vector(0)` |
| 按标签补 0 | `sum by (pod)(...) or (0 * sum by (pod)(up{job="api"}))` |
| 告警“指标消失” | `absent_over_time(x[10m])` |
| counter 重启次数 | `resets(x[1h])` |
| 归一化易变标签 | `label_replace(v, "app", "$1", "pod", "(.*)-[a-z0-9]+-[a-z0-9]+")` |
| 看实际查询参数 | Query inspector → `min step` / `max data points` |

### 7.2 图表异常时的排查顺序

1. **先问“是没发生，还是没看见”**：换到小范围（如 1 小时）看 spike/断点是否出现。
2. **看 Query Inspector**：实际 `min step`、返回点数、是否走了降采样数据。
3. **看数据是“空”还是“0”**：`count(x)` / `count(up{job="..."})` / `absent_over_time(x[10m])`，把“采集断了”和“真的归零”分开。
4. **查窗口与抓取间隔**：`rate` 类查询是否硬编码了小窗口 → 换 `$__rate_interval`。
5. **查聚合函数与维度**：`avg`、`by (pod)` 几百条线的视觉平均都会抹平尖峰 → 换 `max`/`max_over_time` 或聚合到上层维度。
6. **查 counter 重启**：负尖脉冲或计数不连续 → 看 `resets()`，确认用的是 `rate`/`increase` 而非 `delta`。
7. **查标签是否变了**：重启后 pod 名/instance 变了会让旧线消失 → `label_replace` 归一化。
8. **查模板变量**：先看 `Preview of values` 与 `Regex`；新实例没出现则看 Refresh 设置。
9. **查告警侧**：告警没响但图上正常（或反之）→ 对齐告警规则的窗口/频率，检查 FOR 时长与 NO DATA 处理。
