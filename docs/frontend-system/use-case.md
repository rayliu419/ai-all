# 浏览器存储机制：生命周期与适用范围

## 概述
前端开发中，浏览器提供了多种客户端存储方案。最常用的四种是 **Cookie**、**sessionStorage**、**localStorage** 和 **IndexedDB**。
它们各有不同的生命周期、容量限制、作用域和适用场景。理解这些差异，才能在选择时做出正确决策。

## 什么是同源策略
### 同源的定义
**同源策略（Same-Origin Policy）** 是浏览器最核心的安全机制。它限制来自不同源（origin）的文档或脚本对彼此资源的访问。
一个 **源（origin）** 由三部分组成：
```
协议（scheme） + 主机名（host） + 端口（port）
```
- `https://example.com:443` 和 `https://example.com`（默认端口）为同源，
- `http://example.com`（协议不同）和 `https://api.example.com`（子域名不同）则为不同源。

### 同源策略的作用
同源策略的本质是**隔离**：
- 页面 A 的脚本不能读取页面 B 的数据，除非它们同源。
- 这使得恶意网站无法通过 iframe 或 script 标签窃取用户在其他站点的数据。
- 跨域请求可以通过 CORS（Cross-Origin Resource Sharing）机制获得服务器的明确许可。
对于浏览器存储来说，同源策略意味着：一个源只能读写属于自己源的数据，无法访问其他源的数据。这是所有存储机制的共同基础。

### Cookie 的同源规则
- Cookie 的作用域由 **域名 + 路径** 共同决定，与严格 origin（protocol + host + port）不同。
- 例如 `https://app.example.com` 可以读取 `https://example.com` 设置的 Cookie（子域名共享）。
- 可通过 `Domain` 属性控制子域名共享范围，通过 `Path` 属性限定目录范围。
- 默认情况下，Cookie 不区分端口（HTTP/HTTPS 混合也有例外行为），这是 Cookie 与其他存储的最大区别。
- `SameSite` 属性进一步控制跨站发送行为，防御 CSRF 攻击。

### Web Storage 的同源规则
- `localStorage` 和 `sessionStorage` **严格按 origin 隔离**：协议、主机名、端口必须完全一致。
- `http://example.com` 和 `https://example.com` 被视为不同源，各自拥有独立的存储空间。
- 同一个域的不同路径（`/app` 和 `/blog`）共享同一份存储。
- 与 Cookie 不同，无法通过配置来放宽同源限制。

### IndexedDB 的同源规则
- 同样**严格按 origin 隔离**，与 Web Storage 一致。
- 不同源的页面无法读取或写入彼此的 IndexedDB 数据库。
- 一个 origin 下可以创建多个数据库，数据库名在同一 origin 内唯一。

### 第三方内容的影响
当第三方内容通过 `<iframe>` 嵌入时：
- `<script>` 注入的第三方脚本运行在主页面源的上下文中，读写的是**主页面的存储**。
- `<iframe>` 中的第三方内容拥有自己的 origin，读写的是**自己的存储**。
- 注意：如果用户禁用了第三方 Cookie，部分浏览器也会阻止第三方 iframe 访问 Web Storage。

## Cookie
### 生命周期
Cookie 的生命周期由 `Expires` 或 `Max-Age` 属性控制：
- **会话 Cookie**：不设置 `Expires` 和 `Max-Age`，关闭浏览器时清除。但部分浏览器支持"会话恢复"功能，可能使会话 Cookie 持续更久。
- **持久 Cookie**：设置 `Expires`（过期日期）或 `Max-Age`（存活秒数）。到期后自动删除。
- **立即删除**：将 `Expires` 设为过去时间，或 `Max-Age` 设为 `0` / 负数。
### 适用范围

```
客户端与服务器之间维护状态
├── 用户登录凭证 / Session ID
├── CSRF Token
├── 用户偏好（如语言、主题）
└── 追踪 / 分析（第三方 Cookie）
```

### 特点
- **自动发送**：每次 HTTP 请求都会带上同域 Cookie（可通过 `SameSite` 控制跨站行为），这在存储大量数据时会显著增加请求体积。
- **安全控制**：支持 `Secure`（仅 HTTPS）、`HttpOnly`（禁止 JS 读取）、`SameSite`（跨站限制）等属性。
- **容量极小**：每个 Cookie ~4KB，每个域名一般限制几十到上百个。
- **同源 + 路径**：Cookie 的作用域可以限定到特定路径，不同于其他存储机制仅以 Origin 为单位。

### 不适用场景
- 存储大量数据（导致每次请求体积膨胀）
- 存储敏感结构化数据（仅支持字符串）

## sessionStorage
### 生命周期
**存在于标签页（或窗口）的会话期间**：
- 关闭标签页或窗口时，数据被完全清除。
- 刷新页面或通过链接导航到同源页面，数据仍然保留。
- 不同标签页/窗口的数据完全隔离，即使打开的是同一个站点。
- 浏览器崩溃后重启，部分浏览器会恢复 sessionStorage，但无统一标准。
### 适用范围
```
与当前会话绑定的临时数据
├── 表单填写进度（多步骤表单防丢失）
├── 单页应用的路由状态 / 滚动位置
├── 临时选择的商品（未提交购物车）
├── 用户本次访问的临时偏好
└── 页面间临时传递数据（替代 URL 参数）
```

### 特点
- **标签页隔离**：不同标签页即使同源也互不共享，适合多标签独立操作。
- **同步操作**：会阻塞主线程，不适合频繁大量读写。
- **容量有限**：通常 5-10MB。
- **仅字符串**：存取前需要 `JSON.stringify` / `JSON.parse`。

## localStorage
### 生命周期
**持久存储，直到手动删除**：
- 关闭浏览器、重启设备后数据仍然保留。
- 数据不会自动过期。
- 清除方式：用户通过浏览器设置手动清除，或通过 JS 代码调用 `removeItem()` / `clear()`。
- 浏览器在存储空间不足时可能选择性地清除（视为 best-effort 数据）。
### 适用范围
```
跨会话持久化的简单数据
├── 用户偏好（深色模式、字体大小、布局设置）
├── 已浏览教程的「已读」标记
├── 离线缓存的应用配置
├── 购物车内容（非敏感、需跨会话保留）
└── 本地游戏最高分记录
```
### 特点
- **同源共享**：同一域名下所有页面共享同一份 localStorage。
- **同步阻塞**：读写操作同步，大量数据时影响 UI 响应。
- **容量有限**：通常 5-10MB。
- **仅字符串**：结构化数据需要手动序列化。

### 限制与注意事项
- 不应存储认证 Token 等敏感数据（XSS 攻击可读取）。
- Service Worker 和 Web Worker 无法直接访问。
- 浏览器可能因磁盘空间不足而清理（best-effort），但实践中极少发生。

## IndexedDB
### 生命周期
**持久存储，直到手动删除**：
- 数据在浏览器关闭后仍然保留。
- 无自动过期机制，需要代码显式删除。
- 可请求 **持久存储模式**（`navigator.storage.persist()`），用户不会在浏览时丢失数据。
- 私密浏览模式下，退出时数据通常被清除。
### 适用范围
```
大量结构化数据的客户端存储
├── 离线 Web 应用（PWA）的全部数据
├── 邮件客户端（缓存邮件列表、附件）
├── 笔记 / 编辑器（文档内容、历史版本）
├── 音视频元数据缓存
├── 数据库快照、配置数据
├── 用户生成的文件（通过 File / Blob 存储）
└── 需要索引查询的复杂数据
```

### 特点
- **大容量**：实际可用空间取决于磁盘，一般可达数百 MB 甚至 GB。Chrome 允许使用总磁盘的 60%（每个 origin），Firefox 允许每个 eTLD+1 组最大 2GB。
- **异步 API**：不阻塞主线程，适合大量数据处理。
- **支持结构化数据**：可存储对象、数组、File、Blob 等，支持结构化克隆算法。
- **索引查询**：支持创建索引，高效检索（类似 SQL 的 WHERE + ORDER BY）。
- **事务支持**：读写操作在事务内执行，保证数据一致性。
- **Worker 可访问**：在 Web Worker 和 Service Worker 中都可以使用。
- **API 较复杂**：原生的 IndexedDB API 基于事件回调，推荐使用封装库（如 idb、Dexie.js）。

## 推荐的现代做法
1. **Cookie** 只用于认证和服务器状态同步，不应作为通用存储方案。
2. **localStorage** 适合少量的、跨会话的简单键值数据，注意同步阻塞问题。
3. **sessionStorage** 适合标签页隔离的临时状态。
4. **IndexedDB** 是大多数"离线优先"应用的首选——利用异步特性，配合封装库（如 Dexie.js、idb）降低使用门槛。
5. 对于 PWA 的资源缓存，使用 **Cache Storage API**（通过 Service Worker）而非这些存储方案。

## 总结
- **生命周期**：Cookie 按配置过期，sessionStorage 随标签页消亡，localStorage 和 IndexedDB 持久保留。
- **容量**：Cookie(~4KB) < sessionStorage(~5MB) < localStorage(~5-10MB) << IndexedDB(GB 级)。
- **适用场景**：Cookie 管通信、sessionStorage 管会话、localStorage 管配置、IndexedDB 管数据。
- 选择存储方案时，应优先考虑异步方案（IndexedDB），避免同步 API 阻塞主线程影响用户体验。

## 实际案例分析：电商结算与 MFA 验证

### 场景描述

用户在电商网站上将商品加入购物车，进入 Cart 页面。点击「去结算」，系统要求进行 MFA 验证（如短信验证码或 TOTP），验证通过后才进入 Checkout 结算页面。

Cart 页持有即将结算的数据，包括：

- 购物车商品列表（sku、数量、价格）
- 选中的收货地址
- 选中的配送方式
- 优惠券信息
- 订单备注等

问题核心：**MFA 验证作为一个中间环节，如何确保 Cart 侧的数据完整传递到 Checkout 侧？**

---

### 方案 A：重定向路由

#### 实现流程

```
Cart 页面  ──(1) 携带数据跳转──►  MFA 页面  ──(2) 验证通过跳转──►  Checkout 页面
               /mfa?redirect=/checkout            /checkout
```

- 步骤 1：Cart 页面跳转到独立的 MFA 页面（URL 变为 `/mfa`），完成完整的页面卸载和重新加载。
- 步骤 2：MFA 验证成功后，后端（或前端）重定向到 `/checkout`，再次发生页面卸载和重新加载。
- 两次跳转都是**浏览器级导航**，JavaScript 内存中的状态完全丢失。

#### 数据如何跨跳转存活

每次导航都是全新的 JS 上下文，数据必须从**持久化存储**中恢复。有哪些选择？

| 存储方案 | 能否存活两次跳转？ | 评价 |
|----------|-------------------|------|
| **JavaScript 内存（变量/State/Redux）** | ❌ 页面卸载即丢失 | 完全不可用 |
| **URL query 参数** | ✅ 但受 URL 长度限制 | 只能传少量非敏感数据（如订单 ID），不适合传完整购物车 |
| **sessionStorage** | ✅ 同源导航下持久保留 | **最佳选择**，生命周期与标签页绑定，数据用完可清除 |
| **localStorage** | ✅ 持久保留 | 可用但数据会残留在磁盘上，需额外清理 |
| **IndexedDB** | ✅ 持久保留 | 异步 API 配合复杂，临时数据场景用力过猛 |
| **Cookie** | ✅ 随请求发送 | 容量仅 ~4KB，且每次 HTTP 请求都带上，浪费带宽 |
| **服务端 Session** | ✅ 服务端存储，客户端只留 Session ID | 依赖后端实现，需要 API 查询还原数据 |

#### sessionStorage 方案详解（推荐）

```javascript
// Cart 页面：跳转前缓存数据
const checkoutData = {
  items: cartItems,
  address: selectedAddress,
  shipping: selectedShipping,
  coupon: appliedCoupon
};
sessionStorage.setItem('checkout_data', JSON.stringify(checkoutData));

// 然后跳转到 /mfa
window.location.href = '/mfa?redirect=/checkout';

// ------------------------------------------------

// Checkout 页面：加载时恢复数据
const saved = sessionStorage.getItem('checkout_data');
if (saved) {
  const checkoutData = JSON.parse(saved);
  // 渲染结算页面
  sessionStorage.removeItem('checkout_data'); // 用完后清除
}
```

**为什么 sessionStorage > localStorage？**

1. **生命周期匹配**：sessionStorage 随标签页关闭而销毁。用户完成结算后关闭标签页，数据自动消失，无需手动清理。
2. **安全性更高**：localStorage 跨会话持久保留，敏感结算数据残留在磁盘上时间越长，风险越大。
3. **标签页隔离**：用户同时打开多个标签页对比购物车时，每个标签页的结算数据互不干扰。

#### 服务端 Session 方案（替代方案）

```
Cart 页面  ── POST /api/checkout/init ──►  服务端保存订单草稿，返回 checkoutId
           ── 跳转 /mfa?checkoutId=xxx  ──►  MFA 页面
                                            │
           ◄── 验证成功，跳转 /checkout?checkoutId=xxx ──┘
Checkout 页面  ── GET /api/checkout/draft?checkoutId=xxx ──►  服务端返回完整数据
```

- URL 只传一个 ID，不暴露敏感数据。
- 服务端承担存储责任，前端只负责拿 ID 复原。
- 缺点：需要额外的后端接口，增加网络往返。

---

### 方案 B：弹窗（Modal）

#### 实现流程

```
Cart 页面  ── 当前页面弹出 MFA Modal ──►  用户输入验证码 ──►  Modal 关闭 ──►  进入 Checkout
                  (前端路由不变)                         (同页面 / 前端路由跳转)
```

- MFA 验证以弹窗（Modal / Drawer）形式在当前页面上展开。
- 整个过程中 Cart 页面**从未卸载**，JavaScript 上下文持续存在。
- MFA 验证通过后，可以原地切换到 Checkout 视图（同一路由下切换组件），或通过前端路由跳转到 `/checkout`。

#### 数据流分析

**情景 1：Cart 和 Checkout 在同一路由下（SPA 组件切换）**

```
CartComponent ──(状态存储在父组件/Store中)──►  MfaModal
                                                  │
                   ◄── 验证成功 ───────────────┘
                                                  │
                   └── 切换为 CheckoutComponent（数据仍在 Store 中）
```

- 数据完全在**内存**中流转，不需要任何持久化存储。
- Component state、Redux/Zustand store、React Context 等均可直接传递。
- MFA 验证本质上是同一次页面会话中的一个步骤，没有跨导航问题。

**情景 2：Cart 和 Checkout 是不同前端路由（SPA 路由跳转）**

即使 Modal 关闭后通过 `react-router` 或 `vue-router` 跳转到 `/checkout`：

- 如果使用客户端路由（history.push/replace），仍然是**同一页面上下文**，JavaScript 状态不丢失。
- Redux/Zustand store 中的数据在路由切换后仍然可用。
- **不需要** sessionStorage 或任何浏览器存储来传递数据。

#### 对存储的需求

| 场景 | Cart → MFA → Checkout | 是否需要浏览器存储？ |
|------|----------------------|---------------------|
| 同路由组件切换 | MFA Modal 打开/关闭，页面不跳转 | ❌ 不需要 |
| 前端路由跳转 | history.push 切换路由，JS 上下文不丢 | ❌ 不需要 |
| 浏览器刷新 | 用户意外刷新 F5 | ✅ sessionStorage 可作为**降级恢复** |

---

### 方案对比

| 对比维度 | 重定向路由 | 弹窗（Modal） |
|----------|-----------|--------------|
| **页面导航次数** | 2 次完整导航（Cart→MFA→Checkout） | 0 次（同页完成） |
| **数据传递方式** | 需持久化存储（sessionStorage / 服务端 Session） | 内存直接传递 |
| **数据安全风险** | MFA 页面可访问存储，需防 XSS | 数据仅在当前页面内存中 |
| **网络开销** | MFA 页独立加载，额外 HTML/CSS/JS 下载 | 无额外页面加载 |
| **用户体验** | 白屏等待两次，URL 路径清晰 / SEO 友好 | 无整页刷新，流程连贯 |
| **浏览器兼容** | 所有浏览器工作一致 | 需前端 SPA 框架支持 |
| **URL 可分享性** | 每个步骤有独立 URL | MFA 过程不能在 URL 中体现 |
| **实现复杂度** | 低，服务端渲染场景天然合适 | 需 Modal 状态管理，MFA 逻辑内聚在当前页 |
| **从刷新中恢复** | 天然恢复（数据在存储中） | 需额外用 sessionStorage 做降级 |

### 存储方案选择总结

```
实现方式  ──  数据传递方式  ──  推荐存储方案

重定向路由  ──  跨导航持久  ──  sessionStorage（首选）
                                   ├── 生命周期匹配会话
                                   ├── 同源导航下可靠存活
                                   ├── 用完即清除
                                   └── 多标签页隔离
                              或 服务端 Session（备选）
                                   ├── 数据不上客户端
                                   ├── 需要额外 API
                                   └── URL 只传 ID 更安全

弹窗(Modal) ──  内存传递    ──  无需存储（理想情况）
                                  使用 sessionStorage 作为
                                  意外刷新的兜底恢复策略
```

### 结论

| 项目类型 | 推荐方案 | 理由 |
|----------|---------|------|
| 传统 MPA（多页应用） | 重定向路由 + sessionStorage | 天然多页面架构，sessionStorage 是唯一无需后端的可靠方案 |
| 传统 MPA（安全性优先） | 重定向路由 + 服务端 Session | 数据不落客户端，适合金融等高安全场景 |
| SPA（单页应用） | 弹窗 + 内存传递 | 体验流畅，无数据迁移问题，sessionStorage 仅作为 F5 刷新的兜底 |
| SPA（合规强制 MFA URL） | 前端路由跳转 + 内存传递 | 保留 SPA 优势，数据通过 Store 传递，URL 体现 MFA 步骤 |

---

### 与文档前述知识的关联

| 概念 | 本例中的应用 |
|------|-------------|
| **sessionStorage 生命周期** | 电商结算是一次典型会话，sessionStorage 的「标签页关闭即销毁」完美匹配「结算完成即结束」 |
| **localStorage 不适合临时数据** | 如果错误使用 localStorage，用户下次打开浏览器还能看到上次结算残留数据，需要额外清理逻辑 |
| **Cookie 容量限制** | 购物车数据通常远超 4KB，Cookie 无法承载 |
| **IndexedDB 异步特性** | 如果选择 IndexedDB 做结算暂存，异步读取会拖慢 Checkout 页面渲染，且临时数据不值得用 DB |
| **同源策略** | Cart、MFA、Checkout 必须在同一 origin 下，否则 sessionStorage 无法共享 |
| **SPA vs MPA 架构差异** | 决定是否需要浏览器存储参与数据流，本质是「JS 上下文是否持续存在」 |
