# SCN-005 Policy Findings



Main accident: 买家取消和仓库 pick/pack 撞车，自动化按普通取消处理。

Business loss: 退款后仍发货、库存释放错误、仓库追货和账实不一致。



## Bad Runner Findings



### warehouse_conflict_requires_hold

- Severity: `critical`
- Business impact: The automation handled a picked or packed warehouse order as if cancellation were still simple. That can produce a refund, inventory release, and outbound parcel for the same order.
- Recommendation: When warehouse status is picked, packed, label-created, carrier-scanned, or shipped, place the order on hold and submit a warehouse cancellation request before refunding or releasing inventory.

Evidence:

```json
{
  "cancel_request_id": "cancel_req_5001",
  "order_id": "order_5001",
  "warehouse_jobs_at_request": [
    {
      "warehouse_job_id": "wh_job_5001",
      "order_id": "order_5001",
      "sku": "sku_pickpack_1",
      "quantity": 1,
      "status": "picked",
      "cancellation_requested": false,
      "hold_status": null,
      "continued_after_cancel": false
    }
  ],
  "order_status_after": "cancelled",
  "inventory_release_ids": [
    "release_001"
  ],
  "refund_ids": [
    "refund_001"
  ],
  "continued_warehouse_jobs": [
    "wh_job_5001"
  ],
  "hold_ids": [],
  "warehouse_cancellation_request_ids": []
}
```

### no_ship_after_cancel

- Severity: `critical`
- Business impact: The warehouse continued fulfillment after the order was marked cancelled, creating wrong-shipment and customer support recovery risk.
- Recommendation: Do not mark the order cancelled or clear downstream actions until the warehouse confirms the pick/pack job has been stopped.

Evidence:

```json
{
  "order_id": "order_5001",
  "warehouse_job_id": "wh_job_5001",
  "warehouse_status_after": "shipped",
  "continued_after_cancel": true,
  "order_status_after": "cancelled",
  "shipment_status_after": "shipped"
}
```

### no_double_refund_or_inventory_release

- Severity: `high`
- Business impact: The automation refunded the buyer and released inventory while the warehouse still shipped the goods. This creates money loss plus inventory ledger mismatch.
- Recommendation: Keep refund and inventory release pending until warehouse cancellation is confirmed. Resolve the warehouse state first, then perform the financial and inventory actions.

Evidence:

```json
{
  "order_id": "order_5001",
  "inventory_release_ids": [
    "release_001"
  ],
  "refund_ids": [
    "refund_001"
  ],
  "continued_warehouse_jobs": [
    "wh_job_5001"
  ],
  "warehouse_statuses_after": [
    "shipped"
  ]
}
```



## Good Runner Findings



No policy findings.



## Recommended Fix



picked/packed/label_created/carrier_scanned/shipped 都必须进入 hold；仓库确认前不得退款或释放库存。
