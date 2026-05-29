# Demo / POC Readiness

## Current Position

The MVP is ready for Demo/POC conversations when this command passes:

```bash
./tools/smoke_all.sh
```

The demo is intentionally narrow. It proves the incident-validation core, not a
full platform.

## What We Can Show Today

1. Five P0 commerce accidents.
2. Same scenario, bad automation fails and good automation passes.
3. Permissive twin allows unsafe state mutation.
4. Policy engine catches the resulting business incident.
5. Trace replay explains what happened step by step.
6. Markdown reports explain business impact and recommended fixes.
7. Offline Audit v0 imports CSV/XLSX exports and creates a risk report.

## Demo Narrative

Open with the simple product claim:

```txt
We help commerce teams find automation accidents before they touch real orders.
```

Then show one live scenario:

```bash
./commerce-safety run commerce-safety-sandbox/scenarios/SCN-002_timeout_after_commit_retry.yaml --runner bad_runner
./commerce-safety replay runs/<run_id>
./commerce-safety run commerce-safety-sandbox/scenarios/SCN-002_timeout_after_commit_retry.yaml --runner good_runner
```

Explain the key contrast:

- The bad flow retries after a timeout and creates duplicate fulfillment.
- The good flow uses a stable idempotency key and checks existing fulfillment
  state before retrying.
- The platform is not asking whether the API returned 200. It is asking whether
  the final commerce state is safe.

## Materials To Send

Use these after a demo call:

- `demo_pack/executive_summary.md`
- `demo_pack/sales_one_pager.md`
- `demo_pack/demo_walkthrough.md`
- One scenario folder that matches the prospect's pain.
- For operators, include `docs/OFFLINE_AUDIT_POC_PLAYBOOK.md`.

## Readiness Checklist

- `./tools/smoke_all.sh` passes.
- `demo_pack/executive_summary.md` is current.
- The prospect has a clear entrypoint:
  - Offline Audit for seller/operator/agency POC.
  - Live Validation later for agent/workflow builders.
- The ask is concrete: one export, one week, one risk report, one review call.

## Do Not Sell Yet

Do not position this as:

- A full Shopify sandbox.
- A full Amazon SP-API emulator.
- A GitHub PR platform.
- A buyer red-team product.
- An autonomous fixer.

The current sellable wedge is:

```txt
Offline Fulfillment Automation Audit for pre-promotion or pre-automation risk review.
```
