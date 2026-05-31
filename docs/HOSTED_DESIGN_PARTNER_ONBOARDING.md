# Hosted Design Partner Onboarding

This is the customer-facing Stage 19 hosted POC flow.

## Boundary

Use staging agents and synthetic or redacted commerce data only.

Do not connect production Shopify, Amazon, Stripe, warehouse, refund,
fulfillment, or customer-message credentials.

## Flow

1. Create a private workspace for the design partner.
2. Issue API keys for the required role:
   - `agent_token` for staging agent/workflow execution.
   - `operator` for report review.
   - `owner` for token revocation, export, and deletion.
3. Choose scenario pack: the five P0 commerce accident scenarios.
4. Choose skin: `generic`, `shopify_like`, or `amazon_seller_ops`.
5. Run one smoke scenario through hosted MCP or HTTP.
6. Review run history.
7. Download `trace.json`, `policy_report.json`, `state_diff.json`,
   `report.md`, `patch_hints.json`, and `run_manifest.json`.
8. Revoke unused API keys.
9. Export or delete workspace data at POC end.

## Kill Switch

If a token leaks, traffic looks abusive, or a customer accidentally connects a
production workflow:

1. Revoke the token.
2. Suspend the workspace.
3. Abort active sessions.
4. Export audit logs.
5. Delete workspace data if requested.
