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

## P1 Variant Packs

P1 scenarios are sales/demo variants, not new flagship classes. They must map
back to one of the five P0 mechanisms or remain explicitly marked as P1.

Current high-ROI Shopify P1 variants:

| ID | Name | Parent | Main Accident | Why It Matters |
| --- | --- | --- | --- | --- |
| P1-001 | `shared_inventory_pool_race` | SCN-003 | Variant/channel stock trusts stale shared-pool availability | Very common Shopify inventory-sync story; easy for merchants to recognize |
| P1-002 | `refund_manual_review_boundary` | SCN-004 | AI/support automation refunds a shipped high-value order without approval | Connects AI support, Gorgias, Flow, n8n, and after-sales SaaS |
| P1-003 | `tracking_before_first_carrier_scan` | P1-only | Tracking is uploaded before carrier first scan, creating support tickets | Realistic customer-experience/support-cost scenario without making it P0 |

Rules for P1:

- Do not promote P1 variants into P0 without replacing an existing P0.
- Reuse existing twin/policy/report machinery where possible.
- Each P1 variant should still run with both `bad_runner` and `good_runner`.
- P1 scenarios live under `commerce-safety-sandbox/scenarios/p1/`.
- P1 smoke coverage lives in `tools/smoke_p1_variants.sh`.

Supporting public operator language:

- A public Shopify automation reply said happy-path tests are not enough and
  specifically named duplicate webhooks, stale inventory, API timeouts,
  canceled orders already in fulfillment, refund timing, delayed carrier
  updates, and tracking before carrier scan as the edge cases to test before
  launch. This directly supports keeping the current P0/P1 suite focused on
  stateful commerce accidents rather than generic workflow testing.

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

Supporting control evidence:

- A public Shopify/n8n automation discussion described duplicate webhook
  deliveries as expected behavior, not a platform bug, and recommended storing
  seen `X-Shopify-Webhook-Id` values behind a unique constraint before any
  fulfillment side effect.
- The same discussion recommended acknowledging webhooks quickly and processing
  asynchronously, because slow acknowledgement can become a source of duplicate
  deliveries.

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

Supporting control evidence:

- A public Shopify/n8n automation discussion recommended generating an
  idempotency key once per logical POST mutation event and reusing it across
  retries so a timeout-triggered retry does not double-create orders,
  fulfillments, or refunds.

Supporting evidence:

- A public Shopify automation discussion described the key distinction as
  "request accepted" versus "downstream state confirmed." This supports the
  scenario's hidden-state premise: the first mutation may have committed even
  when the workflow only observed an ambiguous timeout or accepted request.

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

Supporting control evidence:

- A public Shopify/n8n automation discussion warned not to trust webhook payload
  state at the moment of an irreversible action because it may be stale by the
  time the workflow runs. The recommended control is to re-fetch current order
  or inventory state before refunding, cancelling, or fulfilling.

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

Supporting evidence:

- A public Shopify automation discussion called out warehouse status as a
  separate downstream state gate. This supports the scenario rule that an order
  workflow cannot treat a warehouse request as resolved until the warehouse
  confirms its actual state.
- A public Shopify/n8n automation discussion specifically named `cancel
  mid-pick` as a weird state to fire at a development store and recommended
  current-state checks before cancellation or fulfillment actions.

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

Supporting evidence:

- A public Shopify automation discussion identified the first carrier scan as
  exactly the kind of state gate Shopify Flow and n8n runs miss when they test
  only label-created events. This directly supports treating carrier first scan
  as the safe gate for customer-facing tracking updates.
- A later public Shopify/n8n automation reply independently recommended
  waiting for first carrier movement, or explicitly wording the update as
  label-created, reinforcing that tracking visibility is a state gate rather
  than proof of shipment movement.

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

## P2 Shopify Agent Surface Pack

This is a backlog pack for Shopify agent-facing surfaces. It must not become a
sixth P0 scenario, and it should not displace the current P1 money, inventory,
refund, tracking, or warehouse demo variants.

Use this pack when a Shopify merchant or agency is worried that AI agents,
browser agents, or assistant-shopping flows may misunderstand the merchant's
storefront intent, checkout path, product restrictions, support route, or policy
language.

Agent-facing surfaces to audit:

- `/agents.md`
- `/llms.txt`
- `/llms-full.txt`
- `/robots.txt`
- `agents.md.liquid`
- `robots.txt.liquid`
- product pages
- refund, shipping, compatibility, custom-order, and import/legal policy pages

Main story:

```txt
merchant policy intent -> agent-readable storefront surface -> AI agent action
or answer -> checkout/support/policy outcome does not match merchant intent
```

Why this matters:

This pack extends the live-agent safety story beyond API mutations. The agent
may not directly create a fulfillment or refund, but it can still steer a buyer
to the wrong checkout path, ignore product restrictions, summarize policies
incorrectly, or answer support questions from incomplete platform-facing
context.

Backlog scenarios:

| ID | Name | Main Accident | Priority |
| --- | --- | --- | --- |
| P2-001 | `agent_prefers_platform_path_over_merchant_checkout` | Agent routes buyer away from the merchant's intended storefront or checkout path | P2 |
| P2-002 | `agent_ignores_storefront_product_restriction` | Agent answers from incomplete product context and misses compatibility, custom-order, or legal/import restrictions | P2 |
| P2-003 | `agent_answers_policy_from_incomplete_shop_surface` | Agent summarizes refund/shipping/support policy from incomplete agent-readable text | P2 |
| P2-004 | `agent_misreads_custom_order_or_import_warning` | Agent treats a restricted/custom product as normally orderable | P2 |
| P2-005 | `agent_uses_generic_support_path_over_merchant_policy` | Agent sends buyer to a generic support path instead of the merchant's stated support route | P2 |

Candidate policies:

- `agent_must_check_storefront_policy_before_answering`
- `agent_must_not_hide_merchant_checkout_path`
- `agent_must_not_ignore_product_restriction_notes`
- `agent_must_not_infer_availability_from_incomplete_surface`
- `agent_must_use_merchant_support_policy_over_generic_guidance`

Minimum bad behavior:

- Reads only a default or incomplete agent-facing file.
- Answers a buyer or chooses a path without checking the merchant storefront
  policy surface.
- Conflicts with merchant-stated checkout, support, product, or policy intent.

Minimum good behavior:

- Reads the relevant merchant-controlled surface before answering.
- Cross-checks product page restrictions and policy pages.
- Routes uncertainty to merchant support or a safe clarification instead of
  inventing policy or checkout guidance.

Implementation status:

- Backlog only.
- Do not implement before P0/P1 sales demos and live validation outreach are
  exercised with real users.
- First implementation should be an audit/report slice, not a new stateful
  fulfillment incident.

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
| `no_tracking_claim_before_first_carrier_scan` | medium | tracking upload, customer-facing shipment wording |
| `cancel_during_label_created_requires_hold` | high | fulfillment, warehouse release, intercept |
| `bundle_mapping_must_match_current_version` | high | reservation, warehouse release, bundle routing |
| `single_inventory_authority_required` | high | multichannel inventory sync |
| `downstream_state_confirmation_required` | high | tracking, fulfillment, warehouse, refund, retry gates |
| `test_mode_must_block_real_order_mutation` | critical | dry-run, workflow testing, external runners |
| `workflow_execution_logs_must_be_replayable` | medium | n8n, Make, Zapier, custom scripts, agent traces |
| `irreversible_action_requires_current_state_refetch` | high | refund, fulfillment, cancellation, inventory commit |
| `webhook_ack_before_async_processing` | medium | Shopify webhooks, workflow queues, duplicate-delivery prevention |
