# V3.5 Agent Sandbox Demo Pack

This is the 5-8 minute demo package for Commerce Automation Safety Sandbox V3.5. It focuses on Live Agent Sandbox value, not Offline Audit.

## Start Here

- [Demo script](demo_script.md)
- [Terminal transcript](terminal_transcript.md)
- [Sample policy report](sample_policy_report.json)
- [Sample patch hints](sample_patch_hints.md)
- [Customer explanation](customer_explanation.md)
- [Investor explanation](investor_explanation.md)

## Demo Flows

| Flow | Status | Policy findings | Artifacts |
| --- | --- | --- | --- |
| Shopify duplicate webhook -> duplicate fulfillment | `failed` | `no_duplicate_fulfillment, webhook_dedup_required` | [`01_shopify_duplicate_webhook`](flows/01_shopify_duplicate_webhook/terminal_transcript.md) |
| Shopify timeout after commit -> unsafe retry | `failed` | `idempotency_required_for_mutating_retries, no_duplicate_fulfillment` | [`02_shopify_timeout_after_commit`](flows/02_shopify_timeout_after_commit/terminal_transcript.md) |
| Amazon stale inventory summary -> oversell risk | `failed` | `reservation_required_before_promise, no_inventory_commit_from_stale_snapshot, no_oversell, amazon_no_promise_from_stale_inventory_summary` | [`03_amazon_stale_inventory`](flows/03_amazon_stale_inventory/terminal_transcript.md) |
| Amazon buyer cancel after pick/pack -> confirmShipment anyway | `failed` | `warehouse_conflict_requires_hold, no_ship_after_cancel, amazon_no_confirm_shipment_after_buyer_cancel_without_review` | [`04_amazon_cancel_after_pick_pack`](flows/04_amazon_cancel_after_pick_pack/terminal_transcript.md) |
| MCP agent calls tools -> trace + policy + patch hints | `failed` | `idempotency_required_for_mutating_retries, no_duplicate_fulfillment` | [`05_mcp_agent_repair_loop`](flows/05_mcp_agent_repair_loop/terminal_transcript.md) |

## Core Narrative

```txt
External Agent -> MCP/HTTP Twin -> Scenario Fault -> Policy Finding -> Patch Hints
```

## Generated

`2026-05-30T09:25:02.050373+00:00`
