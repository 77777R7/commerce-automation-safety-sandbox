# SCN-001 Duplicate Webhook Fulfillment - bad_runner

- Run ID: `run_20260529T200529556621Z_duplicate_webhook_bad_runner`
- Status: `failed`
- Runner: `bad_runner`
- Demo meaning: 失败：Policy Engine 抓到了真实业务事故。

## 这次运行证明了什么

坏流程没有记录 webhook delivery ID，第二次收到同一事件时又预留库存并创建履约。

## Accident Signals

- `duplicate_fulfillment`: `True`
- `duplicated_reserved_inventory`: `True`
- `excess_reserved_inventory`: `{'sku_widget_1': 1}`

## Timeline

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

## 原始系统报告

# Commerce Safety Report: Duplicate webhook creates duplicate fulfillment

- Run ID: `run_20260529T200529556621Z_duplicate_webhook_bad_runner`
- Runner: `bad_runner`
- Status: `failed`

## Business Risk Summary

- Risk: Duplicate webhook creates duplicate fulfillment triggered `no_duplicate_fulfillment`.
- Possible impact: The automation created more fulfillment than the order requires, creating duplicate shipment and inventory loss risk.
- Recommended control: Check existing fulfillment state before creating another fulfillment, and use a stable dedupe or idempotency key for repeated delivery or retry paths.

## Executive Summary

The automation created a critical commerce incident.
The final commerce state violated policy and needs review.

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
- Reserved inventory before: `{'sku_widget_1': 0}`
- Reserved inventory after: `{'sku_widget_1': 2}`
- Expected reserved inventory: `{'sku_widget_1': 1}`

## Findings

### no_duplicate_fulfillment

- Severity: `critical`
- Status: `failed`
- Business impact: The automation created more fulfillment than the order requires, creating duplicate shipment and inventory loss risk.
- Recommendation: Check existing fulfillment state before creating another fulfillment, and use a stable dedupe or idempotency key for repeated delivery or retry paths.

Evidence:

```json
{
  "order_id": "order_1001",
  "sku": "sku_widget_1",
  "ordered_quantity": 1,
  "fulfilled_quantity": 2,
  "fulfillment_count": 2,
  "fulfillment_ids": [
    "ful_001",
    "ful_002"
  ],
  "webhook_ids": [
    "wh_paid_001",
    "wh_paid_001"
  ],
  "source_event_ids": [
    "wh_paid_001",
    "wh_paid_001"
  ],
  "idempotency_keys": [
    null,
    null
  ]
}
```

### webhook_dedup_required

- Severity: `critical`
- Status: `failed`
- Business impact: The duplicate webhook was processed as a new business event, so retries from the platform can trigger repeated state-changing work such as inventory reservation, refunds, or fulfillment.
- Recommendation: Store processed webhook IDs and skip repeat deliveries before performing mutating actions.

Evidence:

```json
{
  "webhook_id": "wh_paid_001",
  "times_received": 2,
  "side_effect_count": 4,
  "side_effects_from_same_webhook": [
    {
      "type": "reservation",
      "id": "res_001",
      "order_id": "order_1001",
      "sku": "sku_widget_1",
      "quantity": 1
    },
    {
      "type": "reservation",
      "id": "res_002",
      "order_id": "order_1001",
      "sku": "sku_widget_1",
      "quantity": 1
    },
    {
      "type": "fulfillment",
      "id": "ful_001",
      "order_id": "order_1001",
      "sku": "sku_widget_1",
      "quantity": 1
    },
    {
      "type": "fulfillment",
      "id": "ful_002",
      "order_id": "order_1001",
      "sku": "sku_widget_1",
      "quantity": 1
    }
  ],
  "dedupe_signal": "missing"
}
```

## How To Fix

Use webhook ID deduplication before mutating order state. For fulfillment actions, also check existing fulfillment state and use an idempotency key for mutating retries.

## Replay

Run `commerce-safety replay runs/run_20260529T200529556621Z_duplicate_webhook_bad_runner` to print the recorded timeline from `trace.json`.
