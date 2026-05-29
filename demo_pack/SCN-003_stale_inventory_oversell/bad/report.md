# Commerce Safety Report: stale_inventory_oversell

- Run ID: `run_20260529T063818043907Z_SCN-003_bad_runner`
- Runner: `bad_runner`
- Status: `failed`

## Business Risk Summary

- Risk: stale_inventory_oversell triggered `reservation_required_before_promise`.
- Possible impact: The automation promised fulfillment without reserving inventory for this order. If the visible stock was stale, the seller can oversell and later cancel or disappoint the customer.
- Recommended control: Reserve inventory for the order before promising fulfillment. If fresh inventory cannot be reserved, route the order to manual review.

## Executive Summary

The automation created a critical oversell risk.
It trusted a stale inventory snapshot showing one unit available, then promised fulfillment even though true availability was zero.

## State Change

- Fulfillments before: `0`
- Fulfillments after: `0`
- Fulfillment promises before: `0`
- Fulfillment promises after: `1`
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
- Reserved inventory before: `{'sku_stale_1': 1}`
- Reserved inventory after: `{'sku_stale_1': 1}`
- Expected reserved inventory: `{'sku_stale_1': 1}`

## Findings

### reservation_required_before_promise

- Severity: `critical`
- Status: `failed`
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
- Status: `failed`
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
- Status: `failed`
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

## How To Fix

Refresh inventory before making customer-facing fulfillment promises. Only promise fulfillment after a successful reservation against fresh available stock; otherwise route the order to manual review.


## Replay

Run `commerce-safety replay runs/run_20260529T063818043907Z_SCN-003_bad_runner` to print the recorded timeline from `trace.json`.
