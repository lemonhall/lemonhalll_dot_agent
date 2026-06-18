# Audit Axes

当用户明确允许并发代理时，用这些维度拆任务，避免多个代理审同一块：

## 1. Security And Exposure

关注：

1. `dev-only` / internal helper 是否暴露到 preview / staging / shared env
2. XSS、越权读写、匿名查单、共享环境入口没锁
3. 结果页、callback 页、query 参数是否承担写职责

典型问题：

1. “不是 production 就当 development”
2. query / storage / HTML 渲染导致同源注入
3. GET 请求改支付状态

## 2. Money And Provider Fact

关注：

1. 支付 session / payment intent / refund 的 provider fact 是否优先
2. idempotency、并发、重复打款、重复造单
3. 本地 finalize 失败时是否会覆盖 provider 已成功事实

典型问题：

1. provider 已退款但本地打回 `refund_failed`
2. provider 已创建 session 但本地映射丢失
3. 并发 create attempt / retry 导致 unique key 500

## 3. Booking And Fulfillment Truth

关注：

1. `booking_orders` / `booking_order_lines` 是否是履约真相层
2. pending 阶段复用订单时，软履约字段是否被吞
3. paid 后修改预算是否有后端 guard

典型问题：

1. 联系人、住客、预计到店没有回写
2. 订单行金额和组选房总额语义混淆
3. logout / switch account 后浏览器残留上一位客户资料

## 4. State Machine And Authoritative Timers

关注：

1. hold、payment attempt、order status 的 authoritative writer 是谁
2. webhook 落库时用哪一个时钟裁决
3. happy path 和 exception path 的边界是否稳定

典型问题：

1. `providerConfirmedAt` 推翻本地 `held_until_at`
2. 已进入 exception handling 后又重回 happy path
3. superseded attempt 晚到成功污染主链

## 5. Admin Governance

关注：

1. 高敏后台动作是否有统一审计
2. retry / resend / sync / reconcile 是否可归责
3. 后台是否直接暴露“手改事实”的危险入口

典型问题：

1. route 传了 actor context，service 却忽略
2. `retry-refund` 非原子、重复入队
3. `resend-confirmation` 没进统一审计

## 6. Regression Gaps

关注：

1. 最危险的分支有没有被专门测试锁住
2. 是实现缺口还是测试空洞
3. 定向回归是否足以证明 contract

典型问题：

1. `paid_writeback_failed` 没有专门回归
2. late webhook / released inventory / superseded attempt 只覆盖了一部分
3. build 通过但关键 branch 没有 red-green 证据
