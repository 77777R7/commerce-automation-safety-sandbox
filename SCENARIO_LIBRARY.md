# P0 Flagship Scenario Library

This is the canonical P0 scenario library for the next MVP phase.

Do not add a sixth P0 scenario. Tracking timing, SKU mapping, timezone,
discount/null-price issues, carrier scan timing, and similar cases belong in P1
scenario packs.

## Library Rules

1. Each scenario tells one main accident.
2. Each scenario uses one shared scenario YAML for `bad_runner` and
   `good_runner`.
3. `bad_runner` must fail and `good_runner` must pass.
4. The twin must be permissive: let unsafe actions mutate state first.
5. The Policy Engine catches the incident after mutation.
6. Each scenario must output `trace.json`, `policy_report.json`,
   `state_diff.json`, and `report.md`.
7. Each scenario should be useful for both future entrypoints:
   `Offline Fulfillment Automation Audit` and `Live Commerce Agent Validation`.
8. Keep the primary policy clean. Secondary policies can be present, but the
   report should not blur the main story.

## Scenario Index

| ID | Name | Main Accident | Main Loss |
| --- | --- | --- | --- |
| SCN-001 | `duplicate_webhook_fulfillment` | Same event processed twice | Duplicate shipment, duplicate inventory reservation |
| SCN-002 | `timeout_after_commit_retry` | First mutation committed but client timed out, then automation retried unsafely | Duplicate fulfillment/refund/order mutation |
| SCN-003 | `stale_inventory_oversell` | Automation trusts stale inventory | Oversell, cancellation, customer complaint |
| SCN-004 | `refund_after_shipment_bypass` | Refund issued after shipment without approval | Money-plus-goods loss |
| SCN-005 | `cancel_after_pick_pack_conflict` | Buyer cancellation races warehouse pick/pack | Wrong shipment, wrong refund, inventory mismatch |

## Implementation Order

0. `SCN-001 duplicate_webhook_fulfillment` - already the baseline.
1. `SCN-002 timeout_after_commit_retry` - next, because it makes
   `idempotency_key` value obvious.
2. `SCN-003 stale_inventory_oversell` - implemented; strongest seller/operator and ERP demo.
3. `SCN-004 refund_after_shipment_bypass` - implemented; strongest AI
   support/after-sales SaaS demo.
4. `SCN-005 cancel_after_pick_pack_conflict` - implemented; most complex P0
   scenario and the first warehouse race-condition slice.

## SCN-001 Duplicate Webhook Fulfillment

Main story:

`duplicate webhook not deduped -> duplicate fulfillment`

Keep the scenario clean. Reservation and warehouse notification duplication can
appear as downstream evidence, but the main story is repeated webhook handling
causing duplicate fulfillment.

Primary policy:

- `webhook_dedup_required`

Secondary policy:

- `no_duplicate_fulfillment`

Minimum bad behavior:

- Processes the same webhook delivery twice.
- Reserves inventory twice.
- Creates fulfillment twice.

Minimum good behavior:

- Stores processed webhook ID.
- Skips duplicate delivery before mutating order state.

## SCN-002 Timeout After Commit Retry

Main story:

`mutation committed internally -> client received timeout -> unsafe retry creates duplicate side effect`

This scenario proves the product tests dangerous state uncertainty, not just API
success or failure.

Primary policy:

- `idempotency_required_for_mutating_retries`

Secondary policy:

- `no_duplicate_fulfillment`

Minimum bad behavior:

- Calls `create_fulfillment` without a stable `idempotency_key`.
- The twin commits the fulfillment, then returns a timeout fault.
- Retries by creating another fulfillment.
- Does not query current fulfillment state before retrying.

Minimum good behavior:

- Uses stable idempotency key, such as `order_id + line_item_id + action_type`.
- On timeout, reuses the same idempotency key or queries existing fulfillment
  state before retry.
- Does not create a second fulfillment.

Minimum scenario shape:

```yaml
id: SCN-002
name: timeout_after_commit_retry
risk_level: critical

preconditions:
  order:
    id: order_1001
    status: paid
    fulfillment_status: unfulfilled
  inventory:
    sku_1:
      on_hand: 1
      reserved: 1
  warehouse:
    status: not_started

faults:
  - type: timeout_after_commit
    action: create_fulfillment

bad_runner_expected:
  - retry_without_idempotency_key
  - duplicate_fulfillment_attempt

good_runner_expected:
  - reuse_idempotency_key
  - query_existing_fulfillment_before_retry
```

## SCN-003 Stale Inventory Oversell

Main story:

`stale inventory trusted -> fulfillment promise without reservation -> oversell`

Primary policy:

- `reservation_required_before_promise`

Secondary policies:

- `no_inventory_commit_from_stale_snapshot`
- `no_oversell`

Minimum bad behavior:

- Reads `local_available: 1`.
- Ignores stale `source_version` or `last_synced_at`.
- Promises fulfillment without a fresh reservation.

Minimum good behavior:

- Refreshes inventory or detects stale inventory.
- Reserves inventory before promising fulfillment.
- Routes to manual review if the inventory snapshot is stale.

Minimum state fields:

- `on_hand`
- `reserved`
- `available`
- `committed`
- `source_version`
- `last_synced_at`

Minimum scenario shape:

```yaml
id: SCN-003
name: stale_inventory_oversell
risk_level: critical

preconditions:
  inventory:
    sku_1:
      local_available: 1
      true_available: 0
      reserved: 1
      last_synced_at: stale
  order:
    status: pending_promise

faults:
  - type: stale_inventory_snapshot

bad_runner_expected:
  - promise_fulfillment_without_reservation

good_runner_expected:
  - refresh_inventory
  - reserve_inventory_before_promise
  - route_to_manual_review_if_stale
```

## SCN-004 Refund After Shipment Approval Bypass

Main story:

`shipped order -> buyer asks for refund -> automation refunds without approval`

This tests business safety, not whether the platform technically permits a
refund.

Primary policy:

- `no_refund_after_shipment_without_approval`

Secondary policy:

- `high_value_refund_requires_approval`

Defer these to later:

- Partial refund complexity.
- Return not received.
- Reshipment conflict.
- Refund total versus captured amount, unless needed for the main flow.

Minimum bad behavior:

- Sees shipped/carrier-scanned order.
- Issues refund directly for a high-value request.
- Does not create approval request.

Minimum good behavior:

- Detects shipped state.
- Creates approval request.
- Holds refund until review.

Minimum scenario shape:

```yaml
id: SCN-004
name: refund_after_shipment_bypass
risk_level: high

preconditions:
  order:
    status: paid
    fulfillment_status: shipped
    shipment_status: carrier_scanned
    refund_status: none
  buyer_request:
    type: refund
    amount: 120

bad_runner_expected:
  - issue_refund_without_approval

good_runner_expected:
  - detect_shipped_status
  - create_approval_request
  - hold_refund_until_review
```

## SCN-005 Cancel After Pick/Pack Warehouse Conflict

Main story:

`buyer cancellation collides with warehouse pick/pack -> automation resolves as if cancellation were simple`

This is the most complex P0 scenario because it needs warehouse state. Do it
last.

Primary policy:

- `warehouse_conflict_requires_hold`

Secondary policies:

- `no_ship_after_cancel`
- `no_double_refund_or_inventory_release`

Minimum warehouse states:

- `not_submitted`
- `submitted_to_warehouse`
- `accepted_by_warehouse`
- `picked`
- `packed`
- `label_created`
- `carrier_scanned`
- `shipped`

Minimum bad behavior:

- Buyer cancel request arrives while warehouse is `picked`.
- Automation cancels order, releases inventory, and issues refund.
- Warehouse continues fulfillment.

Minimum good behavior:

- Detects warehouse conflict.
- Places hold or manual review.
- Submits cancellation request to warehouse.
- Does not release inventory until resolution.
- Does not refund as if the shipment were safely stopped.

Minimum scenario shape:

```yaml
id: SCN-005
name: cancel_after_pick_pack_conflict
risk_level: critical

preconditions:
  order:
    status: paid
    cancel_requested: true
  warehouse:
    status: picked
  fulfillment:
    status: submitted_to_warehouse
  inventory:
    reserved: 1

bad_runner_expected:
  - cancel_order
  - release_inventory
  - issue_refund
  - warehouse_continues_fulfillment

good_runner_expected:
  - detect_warehouse_conflict
  - place_hold_or_manual_review
  - submit_cancellation_request_to_warehouse
  - do_not_release_inventory_until_resolution
```

## P1 Deferred Scenario Ideas

These are valuable, but not P0:

- `tracking_uploaded_before_first_carrier_scan`
- SKU mapping mismatch.
- Timezone cutoff errors.
- Null discount or price edge cases.
- Carrier tracking timing.
- Promotion validation mismatch.

Do not let these displace the five P0 money-and-goods incidents.

## Failure Intelligence Expansion Backlog

This backlog comes from approved Failure Intelligence records in:

```txt
outputs/failure_intelligence/reddit_p0_deep_extract_20260528/
```

These scenarios are approved as useful Commerce Automation Safety Sandbox
scenarios, but they must not expand the P0 flagship set. Treat them as P1 packs
or as evidence that strengthens existing P0 scenarios.

### Already Covered By P0, Use As Evidence Or Variants

| FI Scenario | Relationship To P0 | Use |
| --- | --- | --- |
| `duplicate_fulfillment_after_retry_without_idempotency` | Covered by `SCN-002 timeout_after_commit_retry` | Add as evidence language and regression variant only |
| `cancel_after_fulfillment_before_warehouse_processing` | Narrower state-window variant of `SCN-005 cancel_after_pick_pack_conflict` | Use later as a label-created/not-picked variant |
| `peak_inventory_sync_lag_causes_oversell` | Broader multichannel variant of `SCN-003 stale_inventory_oversell` | Use as P1 inventory authority pack |
| `channel_to_channel_inventory_patchwork_causes_oversell` | Broader source-of-truth variant of `SCN-003 stale_inventory_oversell` | Use as P1 inventory authority pack |

## P1 Scenario Packs

### P1-A Tracking Visibility Pack

Scenario:

```txt
tracking_uploaded_before_first_carrier_scan
```

Main story:

```txt
label created -> tracking uploaded -> customer sees carrier page not ready -> support ticket
```

Why this matters:

This is not always a direct money-and-goods loss, but it creates avoidable
support volume and weakens customer trust. It is especially useful for Shopify,
n8n, carrier API, and AI customer-support demos.

Primary policies:

- `customer_notification_requires_carrier_visibility`
- `no_tracking_claim_before_first_carrier_scan`

Required twins:

- `ShipmentTwin`
- `TrackingTwin`
- `CarrierTwin`
- `CustomerNotificationTwin`

Minimum bad behavior:

- Creates a label.
- Uploads tracking immediately.
- Sends customer notification while carrier status is still
  `label_created_not_scanned`.

Minimum good behavior:

- Waits for first carrier scan or explicit carrier visibility.
- If notifying early, frames it as label-created only, not shipped/in-transit.

### P1-B Webhook Reliability And Reconciliation Pack

Scenario:

```txt
webhook_delivery_failure_requires_reconciliation
```

Main story:

```txt
critical order webhook missing -> automation never backfills -> fulfillment/inventory state silently diverges
```

Why this matters:

The P0 duplicate-webhook case tests duplicate delivery. This pack tests the
opposite failure: missing or dropped delivery. Real commerce systems need both
dedupe and reconciliation.

Primary policies:

- `critical_system_must_not_rely_only_on_webhook`
- `missing_webhook_requires_reconciliation`
- `webhook_subscription_health_alert_required`

Required twins:

- `WebhookTwin`
- `OrderTwin`
- `FulfillmentTwin`
- `ReconciliationTwin`

Minimum bad behavior:

- Treats webhooks as the only source of truth.
- Receives 8 of 10 expected order events.
- Does not backfill or alert on missing events.

Minimum good behavior:

- Logs webhook delivery.
- Detects gaps by sequence/count/time window.
- Runs periodic reconciliation against the order source.

### P1-C Multichannel Inventory Authority Pack

Scenarios:

```txt
peak_inventory_sync_lag_causes_oversell
channel_to_channel_inventory_patchwork_causes_oversell
```

Main story:

```txt
multiple sales channels share stock -> no single inventory authority -> stale or conflicting updates cause oversell
```

Why this matters:

This is likely one of the strongest Offline Fulfillment Automation Audit packs.
It maps cleanly to Shopify, Amazon, TikTok Shop, eBay, ERP, OMS, and WMS
operators who already feel multichannel inventory pain.

Primary policies:

- `single_inventory_authority_required`
- `no_oversell_from_stale_inventory`
- `inventory_conflict_rule_required`
- `sync_failure_alert_required`
- `safety_stock_required_for_peak_skus`

Required twins:

- `InventoryTwin`
- `ChannelInventoryTwin`
- `MarketplaceChannelTwin`
- `ConflictResolutionTwin`
- `AlertTwin`

Minimum bad behavior:

- Lets Shopify, Amazon, TikTok, or another channel patch stock into each other.
- Uses polling or stale channel quantity as truth during peak demand.
- Has no conflict rule when two channels sell the last unit.

Minimum good behavior:

- Declares one inventory authority.
- Pushes sellable quantity outward.
- Holds safety stock for high-risk SKUs.
- Alerts and fails closed on sync conflict.

### P1-D WMS And Bundle Mapping Pack

Scenario:

```txt
bundle_component_mapping_drift_causes_wrong_ship_count
```

Main story:

```txt
bundle/kitted item mapping changes -> automation reserves or releases wrong components -> warehouse ships wrong count
```

Why this matters:

This is a strong bridge into ERP/WMS/3PL buyers. It is less generic than
inventory sync and more specific to operators with bundles, kits, multi-SKU
orders, and warehouse execution.

Primary policies:

- `bundle_mapping_must_match_current_version`
- `bundle_component_reservation_required`
- `mapping_change_requires_test_run`

Required twins:

- `OrderTwin`
- `InventoryTwin`
- `BundleMappingTwin`
- `WarehouseTwin`

Minimum bad behavior:

- Uses stale bundle mapping.
- Reserves parent SKU without validating current components.
- Releases warehouse fulfillment with wrong component quantity.

Minimum good behavior:

- Validates bundle mapping version.
- Reserves components atomically.
- Blocks warehouse release if mapping changed since the automation rule was
  tested.

### P1-E Cancel Window Pack

Scenario:

```txt
cancel_after_fulfillment_before_warehouse_processing
```

Main story:

```txt
buyer cancels after label/fulfillment submission but before warehouse pick -> automation treats it as safely stopped or safely shipped
```

Why this matters:

This is the process-window version of `SCN-005`. It is useful when the customer
has distinct warehouse states such as `label_created`, `not_picked`, `picked`,
`packed`, and `carrier_scanned`.

Primary policies:

- `cancel_during_label_created_requires_hold`
- `warehouse_cancel_cutoff_must_be_checked`

Required twins:

- `OrderTwin`
- `FulfillmentTwin`
- `WarehouseTwin`
- `EventSimulator`

Minimum bad behavior:

- Receives cancellation during `label_created` or `submitted_to_warehouse`.
- Assumes cancellation succeeded without checking warehouse cutoff.
- Releases inventory or refunds before warehouse confirms cancellation.

Minimum good behavior:

- Moves order to hold/manual review.
- Submits warehouse cancel request.
- Does not release inventory or refund as final until warehouse outcome is
  known.

## Approved Policy Backlog

These policies are approved for future implementation. Some already exist in
the P0 engine; keep naming consistent when adding new ones.

| Policy | Severity | Applies To |
| --- | --- | --- |
| `idempotency_required_for_mutating_retries` | critical | fulfillment, refund, reshipment, label, reservation |
| `no_duplicate_fulfillment` | critical | fulfillment, warehouse release |
| `no_oversell_from_stale_inventory` | critical | order acceptance, reservation, inventory sync |
| `critical_system_must_not_rely_only_on_webhook` | high | order, inventory, fulfillment sync |
| `customer_notification_requires_carrier_visibility` | medium | tracking upload, notification |
| `cancel_during_label_created_requires_hold` | high | fulfillment, warehouse release, intercept |
| `bundle_mapping_must_match_current_version` | high | reservation, warehouse release, bundle routing |
| `single_inventory_authority_required` | high | multichannel inventory sync |
