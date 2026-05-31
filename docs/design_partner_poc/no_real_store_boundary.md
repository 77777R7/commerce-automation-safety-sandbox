# No-Real-Store Boundary

The POC must not connect production stores, real payment credentials, real
warehouse credentials, or real customer PII.

## Allowed Data

- Staging agent or workflow.
- Synthetic orders.
- Synthetic inventory.
- Synthetic refunds.
- Synthetic warehouse states.
- Fake Shopify-like payloads.
- Fake Amazon seller-ops payloads.
- Action logs.
- Redacted sample data.

## Not Allowed

- Production Shopify admin token.
- Production Amazon SP-API credentials.
- Real Stripe secret.
- Real warehouse or carrier credentials.
- Real customer name, email, phone, or address.
- Live refund credentials.
- Live fulfillment credentials.
- Production customer-message credentials.

## Why This Boundary Exists

The product tests decision safety, not production connectivity.

The question is:

```txt
If the agent sees duplicate webhooks, stale inventory, timeout ambiguity,
refund pressure, or warehouse race conditions, does it make a dangerous
commerce decision?
```

We can answer that with synthetic state and fake platform-shaped payloads.
Production access is unnecessary for the first POC.

## Lightweight PII / Secret Checks

The hosted POC includes lightweight warning checks for common secrets and PII
patterns. This is not full DLP.

Examples that trigger warnings:

- `sk_live_...`
- `shpat_...`
- `ghp_...`
- `xoxb-...`
- `AKIA...`
- email-like text
- phone-like text
- address-like free text

If a warning appears, remove the data and rerun with synthetic or redacted input.
