# Commerce Automation Safety Sandbox Demo Pack

## 一句话

这是一个电商自动化上线前事故测试层。它不只是检查 API 是否返回成功，而是在一个允许坏动作真实发生的 stateful twin 里，提前抓出超卖、重复发货、错误退款、仓库冲突和不安全 retry 等业务事故。

## Demo 结论

- 同一个场景下，`bad_runner` 会真实制造事故并被 Policy Engine 抓住。
- 同一个场景下，`good_runner` 会通过，证明问题不是 scenario 本身太苛刻，而是流程是否有安全护栏。
- 每次运行都有 `trace.json`、`policy_report.json`、`state_diff.json`、`report.md`，可以给老板、运营、工程师和 coding agent 分别阅读。

## 五类 P0 事故

| 场景 | 事故机制 | 业务损失 | 上线 gate |
| --- | --- | --- | --- |
| SCN-001 Duplicate Webhook Fulfillment | 同一个 paid order webhook 被重复处理。 | 重复发货、重复扣库存、重复仓库通知和客服追损。 | bad path 必须触发 `no_duplicate_fulfillment, webhook_dedup_required`；good path 必须 0 findings。 |
| SCN-002 Timeout After Commit Unsafe Retry | 第一次履约已经提交成功，但客户端收到 timeout 后盲目重试。 | 重复 fulfillment、重复出库、额外运费和库存损失。 | bad path 必须触发 `idempotency_required_for_mutating_retries, no_duplicate_fulfillment`；good path 必须 0 findings。 |
| SCN-003 Stale Inventory Oversell | 自动化相信过期库存快照，在真实可售为 0 时仍承诺发货。 | 超卖、取消订单、差评、补偿和客服工单。 | bad path 必须触发 `reservation_required_before_promise, no_inventory_commit_from_stale_snapshot, no_oversell`；good path 必须 0 findings。 |
| SCN-004 Refund After Shipment Approval Bypass | 订单已经发货且 carrier scanned，自动化仍直接退款。 | 钱货两失、高额退款失控、售后审批失效。 | bad path 必须触发 `no_refund_after_shipment_without_approval, high_value_refund_requires_approval`；good path 必须 0 findings。 |
| SCN-005 Cancel After Pick/Pack Warehouse Conflict | 买家取消和仓库 pick/pack 撞车，自动化按普通取消处理。 | 退款后仍发货、库存释放错误、仓库追货和账实不一致。 | bad path 必须触发 `warehouse_conflict_requires_hold, no_ship_after_cancel, no_double_refund_or_inventory_release`；good path 必须 0 findings。 |

## 这不是普通 validation

普通 validation 往往在 API 层拒绝坏动作；这个 demo 的核心是 `Permissive Twin + Policy Check`：Twin 允许坏流程创建重复 fulfillment、发出退款、释放库存或让仓库继续发货，然后 Policy Engine 从最终状态、事件时间线和 state diff 中判断这是不是业务事故。

## 如何作为上线 gate

1. 对每次自动化流程、agent、workflow 或规则改动，跑这五个 P0 场景。
2. 如果任何 run 出现 `policy_report.json.findings`，上线 gate 失败。
3. 工程师或 agent 读取 `trace_summary.md` 和 `policy_findings.md` 定位根因。
4. 修复后重跑同一 scenario；只有 good path 类型的状态变化才允许上线。

## 推荐修复主题

- Webhook 去重：记录 delivery ID，避免重复副作用。
- 幂等 retry：mutating request 必须带稳定 idempotency key。
- 库存预留：承诺发货前必须刷新库存并成功 reservation。
- 退款审批：发货后退款和高金额退款必须进入 approval workflow。
- 仓库冲突：picked/packed 之后的取消必须 hold，等仓库确认后再退款或释放库存。

## 如何阅读这个 demo_pack

每个场景目录都包含：

- `bad_report.md`：坏流程如何制造事故。
- `good_report.md`：好流程如何通过。
- `trace_summary.md`：按时间线解释事故过程。
- `policy_findings.md`：Policy Engine 抓到什么，为什么危险，怎么修。
- `bad/` 和 `good/`：原始 `trace.json`、`policy_report.json`、`state_diff.json`、`report.md`。

Generated at: `2026-05-29T05:58:01.623076+00:00`
