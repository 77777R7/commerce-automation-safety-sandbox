# SCN-002 Timeout After Commit Unsafe Retry - bad_runner

- Run ID: `run_20260529T195546843524Z_SCN-002_bad_runner`
- Status: `failed`
- Runner: `bad_runner`
- Demo meaning: 失败：Policy Engine 抓到了真实业务事故。

## 这次运行证明了什么

坏流程没有稳定 idempotency_key，timeout 后直接创建第二个 fulfillment。

## Accident Signals

- `duplicate_fulfillment`: `True`

## Timeline

1. Fulfillment task task_fulfill_2001 received for order order_2001 with fault timeout_after_commit.
2. bad_runner starts task task_fulfill_2001 without an idempotency key.
3. bad_runner creates fulfillment ful_001 for order order_2001, sku sku_retry_1.
4. Twin committed fulfillment ful_001, then returned timeout_after_commit.
5. bad_runner receives timeout_after_commit and assumes the fulfillment failed.
6. bad_runner creates fulfillment ful_002 for order order_2001, sku sku_retry_1.
7. Policy violation detected: idempotency_required_for_mutating_retries (critical).
8. Policy violation detected: no_duplicate_fulfillment (critical).

## 原始系统报告

# Commerce Safety Report: timeout_after_commit_retry

- Run ID: `run_20260529T195546843524Z_SCN-002_bad_runner`
- Runner: `bad_runner`
- Status: `failed`

## Business Risk Summary

- Risk: timeout_after_commit_retry triggered `idempotency_required_for_mutating_retries`.
- Possible impact: The first fulfillment committed, but the automation received a timeout and retried as a new mutation. This can create duplicate fulfillment when the system was actually successful.
- Recommended control: Use a stable idempotency key for mutating fulfillment requests and, after timeout, query existing fulfillment state before retrying.

## Executive Summary

The automation created a critical retry incident.
The first fulfillment committed inside the twin, but the runner saw a timeout and created a second fulfillment as if the first one had failed.

## State Change

- Fulfillments before: `0`
- Fulfillments after: `2`
- Fulfillment promises before: `0`
- Fulfillment promises after: `0`
- Refunds before: `0`
- Refunds after: `0`
- Approval requests before: `0`
- Approval requests after: `0`
- Inventory releases before: `0`
- Inventory releases after: `0`
- Workflow holds before: `0`
- Workflow holds after: `0`
- Warehouse cancellation requests before: `0`
- Warehouse cancellation requests after: `0`
- Refund amount issued before: `0`
- Refund amount issued after: `0`
- Reserved inventory before: `{'sku_retry_1': 1}`
- Reserved inventory after: `{'sku_retry_1': 1}`
- Expected reserved inventory: `{'sku_retry_1': 1}`

## Findings

### idempotency_required_for_mutating_retries

- Severity: `critical`
- Status: `failed`
- Business impact: The first fulfillment committed, but the automation received a timeout and retried as a new mutation. This can create duplicate fulfillment when the system was actually successful.
- Recommendation: Use a stable idempotency key for mutating fulfillment requests and, after timeout, query existing fulfillment state before retrying.

Evidence:

```json
{
  "source_event_id": "task_fulfill_2001",
  "fault": "timeout_after_commit",
  "action": "create_fulfillment",
  "order_id": "order_2001",
  "sku": "sku_retry_1",
  "fulfillment_ids": [
    "ful_001",
    "ful_002"
  ],
  "request_ids": [
    "task_fulfill_2001:attempt_1",
    "task_fulfill_2001:attempt_2"
  ],
  "idempotency_keys": [
    null,
    null
  ],
  "missing_idempotency_key": true
}
```

### no_duplicate_fulfillment

- Severity: `critical`
- Status: `failed`
- Business impact: The automation created more fulfillment than the order requires, creating duplicate shipment and inventory loss risk.
- Recommendation: Check existing fulfillment state before creating another fulfillment, and use a stable dedupe or idempotency key for repeated delivery or retry paths.

Evidence:

```json
{
  "order_id": "order_2001",
  "sku": "sku_retry_1",
  "ordered_quantity": 1,
  "fulfilled_quantity": 2,
  "fulfillment_count": 2,
  "fulfillment_ids": [
    "ful_001",
    "ful_002"
  ],
  "webhook_ids": [
    null,
    null
  ],
  "source_event_ids": [
    "task_fulfill_2001",
    "task_fulfill_2001"
  ],
  "idempotency_keys": [
    null,
    null
  ]
}
```

## How To Fix

Use a stable idempotency key for mutating fulfillment actions. If a timeout happens after a mutation request, query existing fulfillment state or retry with the same idempotency key before creating another fulfillment.


## Replay

Run `commerce-safety replay runs/run_20260529T195546843524Z_SCN-002_bad_runner` to print the recorded timeline from `trace.json`.
