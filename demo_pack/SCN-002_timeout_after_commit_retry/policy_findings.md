# SCN-002 Policy Findings



Main accident: 第一次履约已经提交成功，但客户端收到 timeout 后盲目重试。

Business loss: 重复 fulfillment、重复出库、额外运费和库存损失。



## Bad Runner Findings



### idempotency_required_for_mutating_retries

- Severity: `critical`
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



## Good Runner Findings



No policy findings.



## Recommended Fix



所有 mutating retry 都使用稳定幂等键；timeout 后先查询当前状态，再决定是否重试。
