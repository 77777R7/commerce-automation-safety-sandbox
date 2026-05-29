# SCN-005 Trace Summary

Main accident: 买家取消和仓库 pick/pack 撞车，自动化按普通取消处理。

## Bad Runner Timeline

1. Cancel request cancel_req_5001 received for order order_5001.
2. bad_runner treats cancel request cancel_req_5001 as a simple order cancellation despite warehouse progress.
3. bad_runner marks order order_5001 as cancelled.
4. bad_runner releases 1 unit(s) of sku_pickpack_1; reserved inventory is now 0.
5. bad_runner issues refund refund_001 for order order_5001 without blocking platform mutation.
6. Warehouse continues job wh_job_5001 for cancelled order order_5001; status is now shipped.
7. Policy violation detected: warehouse_conflict_requires_hold (critical).
8. Policy violation detected: no_ship_after_cancel (critical).
9. Policy violation detected: no_double_refund_or_inventory_release (high).

## Good Runner Timeline

1. Cancel request cancel_req_5001 received for order order_5001.
2. good_runner checks warehouse progress before resolving cancel request cancel_req_5001.
3. good_runner places order order_5001 on hold for warehouse_pick_pack_conflict.
4. good_runner asks warehouse to cancel job wh_job_5001 while status is picked.
5. good_runner does not refund, release inventory, or mark order order_5001 cancelled until warehouse confirms the stop.
6. Policy check passed with no violations.

## Why The Difference Matters

- Bad path: 坏流程取消订单、释放库存、退款，但仓库继续把已 picked 包裹发出。
- Good path: 好流程识别 warehouse conflict，创建 hold，并向仓库提交 cancellation request。
- Gate: 上线前模拟 cancel-after-pick；只要出现 refund/release/ship-after-cancel，就阻止发布。
