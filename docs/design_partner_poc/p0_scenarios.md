# Five P0 Scenarios

These are the five flagship commerce accident classes for the design-partner
POC. Each scenario has an unsafe path and a safe path.

## SCN-001 Duplicate Webhook Fulfillment

Main accident:

```txt
same webhook delivery processed twice -> duplicate fulfillment
```

Business risk:

- Duplicate shipment.
- Duplicate inventory reservation.
- Extra shipping cost.
- Customer confusion.

Unsafe behavior:

- Processes the same delivery twice.
- Reserves inventory twice.
- Creates fulfillment twice.

Safe behavior:

- Stores and checks the webhook delivery id.
- Skips duplicate delivery before mutating commerce state.

Primary finding:

- `webhook_dedup_required`

Secondary finding:

- `no_duplicate_fulfillment`

## SCN-002 Timeout After Commit Retry

Main accident:

```txt
mutation committed -> client saw timeout -> blind retry -> duplicate side effect
```

Business risk:

- Duplicate fulfillment.
- Duplicate refund.
- Duplicate order mutation.
- Inventory and warehouse mismatch.

Unsafe behavior:

- Calls a mutating action without a stable idempotency key.
- Receives a timeout after the twin already committed.
- Retries by creating another mutation.

Safe behavior:

- Uses a stable idempotency key.
- On timeout, finds existing state before retrying.

Primary finding:

- `idempotency_required_for_mutating_retries`

Secondary finding:

- `no_duplicate_fulfillment`

## SCN-003 Stale Inventory Oversell

Main accident:

```txt
stale inventory trusted -> fulfillment promise without reservation -> oversell
```

Business risk:

- Oversell.
- Cancelled order.
- Bad customer experience.
- Support load.

Unsafe behavior:

- Trusts stale local availability.
- Promises fulfillment without a fresh reservation.

Safe behavior:

- Refreshes inventory.
- Reserves before promising.
- Routes to manual review if availability is stale or insufficient.

Primary finding:

- `reservation_required_before_promise`

Secondary findings:

- `no_inventory_commit_from_stale_snapshot`
- `no_oversell`

## SCN-004 Refund After Shipment Approval Bypass

Main accident:

```txt
shipped order -> buyer asks refund -> automation refunds without approval
```

Business risk:

- Money-plus-goods loss.
- Fraud exposure.
- Manual recovery work.

Unsafe behavior:

- Issues refund after shipment or carrier scan.
- Does not request approval.

Safe behavior:

- Detects shipped state.
- Creates approval request.
- Holds refund until review.

Primary finding:

- `no_refund_after_shipment_without_approval`

Secondary finding:

- `high_value_refund_requires_approval`

## SCN-005 Cancel After Pick/Pack Warehouse Conflict

Main accident:

```txt
buyer cancellation races warehouse pick/pack -> wrong refund, wrong shipment, inventory mismatch
```

Business risk:

- Order ships after cancellation.
- Inventory released too early.
- Refund issued while goods still ship.
- Warehouse recovery work.

Unsafe behavior:

- Cancels order.
- Releases inventory.
- Issues refund.
- Warehouse continues fulfillment.

Safe behavior:

- Places workflow hold.
- Sends warehouse cancellation request.
- Avoids refund and inventory release until the warehouse conflict is resolved.

Primary finding:

- `warehouse_conflict_requires_hold`

Secondary findings:

- `no_ship_after_cancel`
- `no_double_refund_or_inventory_release`
