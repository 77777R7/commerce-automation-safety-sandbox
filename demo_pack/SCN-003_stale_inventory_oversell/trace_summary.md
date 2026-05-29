# SCN-003 Trace Summary

Main accident: 自动化相信过期库存快照，在真实可售为 0 时仍承诺发货。

## Bad Runner Timeline

1. Inventory promise task task_promise_3001 received for order order_3001 with fault stale_inventory_snapshot.
2. bad_runner reads stale inventory for sku_stale_1: available=1, true_available=0.
3. bad_runner promises fulfillment for order order_3001, sku sku_stale_1, using available=1 without confirmed reservation.
4. Policy violation detected: reservation_required_before_promise (critical).
5. Policy violation detected: no_inventory_commit_from_stale_snapshot (high).
6. Policy violation detected: no_oversell (critical).

## Good Runner Timeline

1. Inventory promise task task_promise_3001 received for order order_3001 with fault stale_inventory_snapshot.
2. good_runner refreshes inventory for sku_stale_1; available is now 0.
3. good_runner routes order order_3001, sku sku_stale_1 to manual review.
4. Policy check passed with no violations.

## Why The Difference Matters

- Bad path: 坏流程读取 local available=1，没有刷新库存，也没有先做 reservation。
- Good path: 好流程刷新库存，发现 true available=0 后转人工 review。
- Gate: 上线前注入 stale inventory；只要流程基于 stale snapshot 做承诺，就阻止发布。
