# V3.5 Demo Script: Live Agent Sandbox

Use this for a 5-8 minute demo. Keep the story tight: this is not a mock server; it is a permissive stateful twin plus policy oracle for commerce automation.

## 0:00-0:45 - Set The Frame

Commerce automation and AI agents are starting to touch operational state: orders, inventory, fulfillment, refunds, warehouse actions, webhooks, and API retries. A request can technically succeed while creating a business accident. Commerce Automation Safety Sandbox catches those accidents before production.

Core line:

```txt
External Agent -> MCP/HTTP Twin -> Scenario Fault -> Policy Finding -> Patch Hints
```

## 0:45-2:00 - Shopify Duplicate Webhook

Open `flows/01_shopify_duplicate_webhook/terminal_transcript.md`.

Narrate:

1. Shopify sends an `orders/paid` webhook.
2. The automation creates fulfillment `ful_001`.
3. The same webhook delivery is received again.
4. The permissive twin allows the bad automation to create `ful_002`.
5. Policy catches `webhook_dedup_required` and `no_duplicate_fulfillment`.

Takeaway: We do not stop the bad action at the API boundary. We let the accident happen in the sandbox, then explain the business risk.

## 2:00-3:15 - Shopify Timeout After Commit

Open `flows/02_shopify_timeout_after_commit/terminal_transcript.md`.

Narrate:

1. The first fulfillment mutation commits internally.
2. The client receives `timeout_after_commit`.
3. Unsafe automation retries with a new request instead of a stable idempotency key.
4. The twin now has duplicate fulfillment.
5. Policy catches unsafe retry and duplicate fulfillment.

Takeaway: The dangerous case is not just failure. It is success that the agent did not observe.

## 3:15-4:30 - Amazon Stale Inventory

Open `flows/03_amazon_stale_inventory/terminal_transcript.md`.

Narrate:

1. The Amazon-shaped inventory summary says fulfillable quantity is 1.
2. The twin exposes hidden truth: true available is 0 and the snapshot is stale.
3. Unsafe automation promises fulfillment anyway.
4. Policy catches stale-inventory promise, missing reservation, and oversell risk.

Takeaway: Official sandbox-style API success is not enough. We test business state safety.

## 4:30-5:45 - Amazon Cancel After Pick/Pack

Open `flows/04_amazon_cancel_after_pick_pack/terminal_transcript.md`.

Narrate:

1. Buyer cancellation arrives after warehouse pick/pack has started.
2. Bad automation cancels the order and still confirms shipment.
3. Policy catches shipment after cancellation and missing workflow hold.

Takeaway: Warehouse conflicts are process races, not simple API errors.

## 5:45-7:00 - MCP Agent Repair Loop

Open `flows/05_mcp_agent_repair_loop/terminal_transcript.md`, then `sample_patch_hints.md`.

Narrate:

1. An agent calls MCP tools directly.
2. It makes the unsafe retry.
3. It asks for trace, policy report, and patch hints.
4. The output tells Codex/Claude where the agent went wrong and what guardrail to add.

Takeaway: V3.5 is not just a dashboard. It is agent-readable safety infrastructure.

## Close

The gate is simple:

```txt
If policy_report.json has findings, the automation does not go live.
```
