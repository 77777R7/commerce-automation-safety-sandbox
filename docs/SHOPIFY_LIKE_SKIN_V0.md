# Shopify-like Skin P0 Coverage

Stage 12 adds the first platform-shaped digital twin skin. It is intentionally
narrow: a thin Shopify-like adapter over the existing Commerce Incident
Validation Core. It now covers the five P0 scenarios without becoming a full
Shopify Admin API clone.

## What It Supports

- `POST /sessions/{session_id}/shopify/webhooks`
  - Supports `orders/paid` and `orders/cancelled`.
  - Reads `X-Shopify-Topic`.
  - Reads `X-Shopify-Webhook-Id` as the duplicate-delivery signal.
  - Resolves Shopify `id` / `admin_graphql_api_id` through the session binding
    into the canonical sandbox order id.
  - Also accepts `metadata.commerce_order_id` when a caller wants to be
    explicit.
  - Records a normalized `webhook_received` event in the existing twin.
  - Maps `orders/cancelled` into a normalized cancel request for warehouse
    conflict scenarios.
- `POST /sessions/{session_id}/shopify/webhooks/skip_duplicate`
  - Records a positive `duplicate_webhook_skipped` trace event for safe agents
    that dedupe by `X-Shopify-Webhook-Id`.
- `POST /sessions/{session_id}/shopify/admin/api/{version}/graphql.json`
  - Supports `fulfillmentCreate`.
  - Maps the mutation into `commerce.create_fulfillment`.
  - Resolves Shopify-like `fulfillmentOrderId` and
    `fulfillmentOrderLineItems[].id` through the session binding into
    canonical order/SKU state.
  - Supports `timeout_after_commit` for SCN-002.
  - Preserves `idempotency_key`, `request_id`, `source_event_id`, and
    `webhook_id` metadata.
  - Supports the P0 safety mappings for `inventoryAdjustQuantities`,
    `refundCreate`, `refundApprovalRequestCreate`, `orderCancel`,
    `fulfillmentOrderHold`,
    `fulfillmentOrderSubmitCancellationRequest`, and
    `fulfillmentOrderContinue`.
- `GET /sessions/{session_id}/shopify/admin/api/{version}/inventory_levels.json`
  - Returns stateful Shopify-like inventory levels with commerce-twin metadata
    for available, reserved, committed, true availability, and snapshot
    freshness.
- `POST /sessions/{session_id}/shopify/admin/api/{version}/inventory_levels/adjust.json`
  - Maps reservation-style adjustments into `commerce.reserve_inventory`.
  - Maps release-style adjustments into `commerce.release_inventory`.
- `POST /sessions/{session_id}/shopify/actions/{action}`
  - Supports the minimal P0 ops actions:
    `promise_fulfillment`, `route_manual_review`, `create_approval_request`,
    `cancel_order`, `release_inventory`, `place_fulfillment_hold`,
    `submit_fulfillment_cancellation_request`, and
    `warehouse_continue_fulfillment`.
- `GET /sessions/{session_id}/shopify/coverage`
  - Returns coverage and binding status.

## What It Does Not Support

- Full Shopify GraphQL parsing.
- OAuth.
- Checkout.
- Product catalog.
- Full Shopify API compatibility.

Unsupported mutations return an explicit stub response with
`_commerce_twin_stub: true` and `coverage: unsupported`.

## Binding Model

V0 is not a full Shopify API clone, but callers no longer need to send internal
`order_id` and `sku` fields on the main Shopify-shaped paths. When a session is
created, the adapter derives a small platform binding from the seeded commerce
state:

- `gid://shopify/Order/{number}` -> canonical order id.
- `gid://shopify/FulfillmentOrder/{number}` -> canonical order id.
- `gid://shopify/FulfillmentOrderLineItem/{number}-{index}` -> canonical SKU.
- `gid://shopify/InventoryItem/{sku-or-number}` -> canonical SKU.

For local tests and hand-written demos, callers may still send
`metadata.commerce_order_id` or `metadata.commerce_sku` explicitly.

## Machine-Readable Contract

The Stage 12 routes are included in
`docs/openapi/live_twin_api.yaml`:

- `/sessions/{session_id}/shopify/webhooks`
- `/sessions/{session_id}/shopify/webhooks/skip_duplicate`
- `/sessions/{session_id}/shopify/admin/api/{api_version}/graphql.json`
- `/sessions/{session_id}/shopify/admin/api/{api_version}/inventory_levels.json`
- `/sessions/{session_id}/shopify/admin/api/{api_version}/inventory_levels/adjust.json`
- `/sessions/{session_id}/shopify/actions/{action}`
- `/sessions/{session_id}/shopify/coverage`

## Design Principle

The skin is only an adapter:

```txt
Shopify-shaped request -> normalized commerce action/event -> permissive twin -> policy check
```

It must not reject unsafe business actions just because they are risky. Unsafe
actions should mutate the twin state first. `PolicyEngine` catches the resulting
business incident when the session is completed.

## Stage 12 Gate

```bash
python -m pytest tests/test_shopify_skin_manifests.py tests/test_shopify_webhook_mapper.py tests/test_shopify_graphql_router.py tests/test_shopify_skin_live_http.py
./tools/smoke_stage12_shopify_skin_v0.sh
```
