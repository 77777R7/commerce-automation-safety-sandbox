# SCN-001 Trace Summary

Main accident: 同一个 paid order webhook 被重复处理。

## Bad Runner Timeline

1. Webhook wh_paid_001 received for order order_1001.
2. bad_runner starts processing webhook wh_paid_001 without dedupe.
3. bad_runner reserves 1 unit(s) of sku_widget_1; reserved inventory is now 1.
4. bad_runner creates fulfillment ful_001 for order order_1001, sku sku_widget_1.
5. Webhook wh_paid_001 received for order order_1001.
6. bad_runner starts processing webhook wh_paid_001 without dedupe.
7. bad_runner reserves 1 unit(s) of sku_widget_1; reserved inventory is now 2.
8. bad_runner creates fulfillment ful_002 for order order_1001, sku sku_widget_1.
9. Policy violation detected: no_duplicate_fulfillment (critical).
10. Policy violation detected: webhook_dedup_required (critical).

## Good Runner Timeline

1. Webhook wh_paid_001 received for order order_1001.
2. good_runner starts processing webhook wh_paid_001 with dedupe.
3. good_runner reserves 1 unit(s) of sku_widget_1; reserved inventory is now 1.
4. good_runner creates fulfillment ful_001 for order order_1001, sku sku_widget_1.
5. Webhook wh_paid_001 received for order order_1001.
6. good_runner skips duplicate webhook wh_paid_001.
7. Policy check passed with no violations.

## Why The Difference Matters

- Bad path: 坏流程没有记录 webhook delivery ID，第二次收到同一事件时又预留库存并创建履约。
- Good path: 好流程先做 webhook dedupe，第二次收到同一 delivery 直接跳过。
- Gate: 上线前重放 duplicate webhook；只要产生重复 fulfillment 或重复 reservation，就阻止发布。
