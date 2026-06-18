# V3.5 Demo Terminal Transcript

This is a recorded transcript of the five demo flows. The commands are shown in operator form; every status, finding, and artifact path was generated from the current live twin implementation.

### Shopify duplicate webhook -> duplicate fulfillment

```text
$ POST /sessions scenario=SCN-001 -> session sess_20260530T092455537598Z_duplicate_webhook_6a3ec191
$ POST /shopify/webhooks X-Shopify-Webhook-Id=wh_paid_001 -> 202 event=wh_paid_001
$ mutation fulfillmentCreate(webhook_id=wh_paid_001) -> 200 id=gid://shopify/Fulfillment/ful_001
$ POST /shopify/webhooks duplicate X-Shopify-Webhook-Id=wh_paid_001 -> 202 duplicate delivery accepted by permissive twin
$ mutation fulfillmentCreate(replayed webhook) -> 200 id=gid://shopify/Fulfillment/ful_002
$ POST /complete -> failed findings=['no_duplicate_fulfillment', 'webhook_dedup_required']
```

- Status: `failed`
- Policy findings: `no_duplicate_fulfillment, webhook_dedup_required`
- Patch hints: `2`

### Shopify timeout after commit -> unsafe retry

```text
$ POST /sessions scenario=SCN-002 -> session sess_20260530T092457286630Z_SCN-002_00153377
$ GET /tasks/next -> task_fulfill_2001 fault=timeout_after_commit
$ mutation fulfillmentCreate(request_id=shopify_req_timeout_1) -> 504 timeout_after_commit; mutation already committed
$ mutation fulfillmentCreate(request_id=shopify_req_retry_2) -> 200 id=gid://shopify/Fulfillment/ful_002
$ POST /complete -> failed findings=['idempotency_required_for_mutating_retries', 'no_duplicate_fulfillment']
```

- Status: `failed`
- Policy findings: `idempotency_required_for_mutating_retries, no_duplicate_fulfillment`
- Patch hints: `2`

### Amazon stale inventory summary -> oversell risk

```text
$ POST /sessions scenario=SCN-003 -> session sess_20260530T092458116779Z_SCN-003_9afbb1d4
$ GET /amazon/sp-api/fba/inventory/v1/summaries?sellerSkus=sku_stale_1 -> 200 fulfillable=1 trueAvailable=0
$ POST /amazon/actions/promise_fulfillment -> 200 promise=promise_001
$ POST /complete -> failed findings=['reservation_required_before_promise', 'no_inventory_commit_from_stale_snapshot', 'no_oversell', 'amazon_no_promise_from_stale_inventory_summary']
```

- Status: `failed`
- Policy findings: `reservation_required_before_promise, no_inventory_commit_from_stale_snapshot, no_oversell, amazon_no_promise_from_stale_inventory_summary`
- Patch hints: `4`

### Amazon buyer cancel after pick/pack -> confirmShipment anyway

```text
$ POST /sessions scenario=SCN-005 -> session sess_20260530T092459654606Z_SCN-005_ce085f0c
$ POST /amazon/notifications ORDER_CHANGE BuyerRequestedCancel -> 202 event=cancel_request
$ POST /amazon/actions/cancel_order -> 200 ok=True
$ POST /amazon/sp-api/orders/v0/orders/AMZ-5001/shipmentConfirmation -> 200 shipmentStatus=confirmed
$ POST /complete -> failed findings=['warehouse_conflict_requires_hold', 'no_ship_after_cancel', 'amazon_no_confirm_shipment_after_buyer_cancel_without_review']
```

- Status: `failed`
- Policy findings: `warehouse_conflict_requires_hold, no_ship_after_cancel, amazon_no_confirm_shipment_after_buyer_cancel_without_review`
- Patch hints: `3`

### MCP agent calls tools -> trace + policy + patch hints

```text
$ MCP commerce.start_session(SCN-002) -> session sess_20260530T092502042629Z_SCN-002_382c2244
$ MCP commerce.get_task -> task_fulfill_2001 fault=timeout_after_commit
$ MCP commerce.create_fulfillment(request_id=mcp_req_timeout_1) -> ok=False error=timeout_after_commit; side effect committed
$ MCP commerce.create_fulfillment(request_id=mcp_req_retry_2) -> fulfillment=ful_002
$ MCP commerce.complete_session -> failed findings=['idempotency_required_for_mutating_retries', 'no_duplicate_fulfillment']
$ MCP commerce.get_trace -> 6 timeline events
$ MCP commerce.get_policy_report -> ['idempotency_required_for_mutating_retries', 'no_duplicate_fulfillment']
$ MCP commerce.get_patch_hints -> 2 repair hints
```

- Status: `failed`
- Policy findings: `idempotency_required_for_mutating_retries, no_duplicate_fulfillment`
- Patch hints: `2`
