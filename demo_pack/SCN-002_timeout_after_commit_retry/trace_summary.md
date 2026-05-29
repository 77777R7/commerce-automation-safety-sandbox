# SCN-002 Trace Summary

Main accident: 第一次履约已经提交成功，但客户端收到 timeout 后盲目重试。

## Bad Runner Timeline

1. Fulfillment task task_fulfill_2001 received for order order_2001 with fault timeout_after_commit.
2. bad_runner starts task task_fulfill_2001 without an idempotency key.
3. bad_runner creates fulfillment ful_001 for order order_2001, sku sku_retry_1.
4. Twin committed fulfillment ful_001, then returned timeout_after_commit.
5. bad_runner receives timeout_after_commit and assumes the fulfillment failed.
6. bad_runner creates fulfillment ful_002 for order order_2001, sku sku_retry_1.
7. Policy violation detected: idempotency_required_for_mutating_retries (critical).
8. Policy violation detected: no_duplicate_fulfillment (critical).

## Good Runner Timeline

1. Fulfillment task task_fulfill_2001 received for order order_2001 with fault timeout_after_commit.
2. good_runner starts task task_fulfill_2001 with stable idempotency key.
3. good_runner creates fulfillment ful_001 for order order_2001, sku sku_retry_1.
4. Twin committed fulfillment ful_001, then returned timeout_after_commit.
5. good_runner receives timeout_after_commit and checks existing fulfillment state before retrying.
6. good_runner confirms fulfillment ful_001 already committed.
7. Policy check passed with no violations.

## Why The Difference Matters

- Bad path: 坏流程没有稳定 idempotency_key，timeout 后直接创建第二个 fulfillment。
- Good path: 好流程使用稳定 idempotency_key，并在 timeout 后查询已提交的 fulfillment。
- Gate: 上线前注入 timeout_after_commit；只要 retry 造成第二个副作用，就阻止发布。
