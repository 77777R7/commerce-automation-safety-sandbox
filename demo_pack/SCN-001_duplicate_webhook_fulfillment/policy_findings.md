# SCN-001 Policy Findings



Main accident: 同一个 paid order webhook 被重复处理。

Business loss: 重复发货、重复扣库存、重复仓库通知和客服追损。



## Bad Runner Findings



### no_duplicate_fulfillment

- Severity: `critical`
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



## Good Runner Findings



No policy findings.



## Recommended Fix



把 webhook ID / delivery ID 存为幂等键；任何改变订单、库存、履约状态的动作前先检查是否已处理。
