# SCN-003 Policy Findings



Main accident: 自动化相信过期库存快照，在真实可售为 0 时仍承诺发货。

Business loss: 超卖、取消订单、差评、补偿和客服工单。



## Bad Runner Findings



### reservation_required_before_promise

- Severity: `critical`
- Business impact: The automation promised fulfillment without reserving inventory for this order. If the visible stock was stale, the seller can oversell and later cancel or disappoint the customer.
- Recommendation: Reserve inventory for the order before promising fulfillment. If fresh inventory cannot be reserved, route the order to manual review.

Evidence:

```json
{
  "promise_id": "promise_001",
  "order_id": "order_3001",
  "sku": "sku_stale_1",
  "quantity": 1,
  "based_on_available": 1,
  "true_available_at_commit": 0,
  "reservation_id": null,
  "matching_reservations": []
}
```

### no_inventory_commit_from_stale_snapshot

- Severity: `high`
- Business impact: The automation committed a fulfillment promise from an outdated inventory snapshot. Stale stock data can turn a normal order into an oversell incident.
- Recommendation: Refresh inventory before committing customer-facing promises, and block or review the action when the inventory snapshot is stale.

Evidence:

```json
{
  "promise_id": "promise_001",
  "order_id": "order_3001",
  "sku": "sku_stale_1",
  "quantity": 1,
  "based_on_available": 1,
  "true_available_at_commit": 0,
  "stale_markers": {
    "last_synced_at": "stale",
    "snapshot_version": "stale"
  }
}
```

### no_oversell

- Severity: `critical`
- Business impact: The automation promised more units than were truly available, creating cancellation, backorder, extra support, and review risk.
- Recommendation: Only promise fulfillment after a successful reservation against fresh available inventory.

Evidence:

```json
{
  "promise_id": "promise_001",
  "order_id": "order_3001",
  "sku": "sku_stale_1",
  "promised_quantity": 1,
  "true_available_at_commit": 0,
  "oversell_quantity": 1
}
```



## Good Runner Findings



No policy findings.



## Recommended Fix



承诺发货前必须用新鲜库存做 reservation；库存不新鲜或 reserve 失败时进入人工处理。
