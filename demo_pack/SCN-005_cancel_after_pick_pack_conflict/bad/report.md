# Commerce Safety Report: cancel_after_pick_pack_conflict

- Run ID: `run_20260529T200621161505Z_SCN-005_bad_runner`
- Runner: `bad_runner`
- Status: `failed`

## Business Risk Summary

- Risk: cancel_after_pick_pack_conflict triggered `warehouse_conflict_requires_hold`.
- Possible impact: The automation handled a picked or packed warehouse order as if cancellation were still simple. That can produce a refund, inventory release, and outbound parcel for the same order.
- Recommended control: When warehouse status is picked, packed, label-created, carrier-scanned, or shipped, place the order on hold and submit a warehouse cancellation request before refunding or releasing inventory.

## Executive Summary

The automation created a critical warehouse cancellation conflict.
It cancelled the order, released inventory, and issued a refund while the warehouse continued shipping the already-picked parcel.

## State Change

- Fulfillments before: `0`
- Fulfillments after: `0`
- Fulfillment promises before: `0`
- Fulfillment promises after: `0`
- Refunds before: `0`
- Refunds after: `1`
- Approval requests before: `0`
- Approval requests after: `0`
- Inventory releases before: `0`
- Inventory releases after: `1`
- Workflow holds before: `0`
- Workflow holds after: `0`
- Warehouse cancellation requests before: `0`
- Warehouse cancellation requests after: `0`
- Refund amount issued before: `0`
- Refund amount issued after: `80.0`
- Reserved inventory before: `{'sku_pickpack_1': 1}`
- Reserved inventory after: `{'sku_pickpack_1': 0}`
- Expected reserved inventory: `{'sku_pickpack_1': 1}`

## Findings

### warehouse_conflict_requires_hold

- Severity: `critical`
- Status: `failed`
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
- Status: `failed`
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
- Status: `failed`
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

## How To Fix

Treat picked, packed, label-created, carrier-scanned, and shipped warehouse states as conflict states. Put the order on hold, submit a warehouse cancellation request, and wait for warehouse confirmation before issuing a refund or releasing reserved inventory.


## Replay

Run `commerce-safety replay runs/run_20260529T200621161505Z_SCN-005_bad_runner` to print the recorded timeline from `trace.json`.
