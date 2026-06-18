# Demo / POC Readiness

## Current Position

The V3.5 demo is ready for Demo/POC conversations when this command passes:

```bash
PYTHON=/private/tmp/commerce-safety-stage9-venv/bin/python ./tools/smoke_v35.sh
```

Latest verified state:

- `smoke_v35` passes end to end.
- Live Agent Sandbox-first is the current mainline.
- MCP and HTTP Twin API are both working agent-facing interfaces.
- Shopify-like Skin V0 is available for Shopify-shaped workflows.
- Amazon Seller Ops Skin V0 is available for Amazon-shaped seller ops flows.
- Five P0 accident classes remain the core safety library.
- Three high-ROI Shopify P1 variants are now available for sales demos.

The demo is still intentionally narrow. It proves the incident-validation
workflow, not a full Shopify clone, a full Amazon SP-API emulator, or a hosted
multi-tenant platform.

## What We Can Show Today

1. Five P0 commerce accidents.
2. Three Shopify-friendly P1 sales variants:
   - shared inventory pool race;
   - refund manual review boundary;
   - tracking before first carrier scan.
3. Same scenario, unsafe automation fails and safe automation passes.
4. Permissive twin allows unsafe state mutation before policy evaluation.
5. Policy engine catches the final business incident.
6. Trace replay explains the accident step by step.
7. `policy_report.json`, `state_diff.json`, `report.md`, and patch hints explain
   business impact and recommended fixes.
8. Live validation can be shown through CLI, HTTP Twin API, or MCP.

## Demo Narrative

Open with the simple product claim:

```txt
We help commerce teams find automation accidents before agents or workflows touch real orders.
```

Then pick the demo based on the prospect:

- Shopify merchant or agency: start with `P1-001 shared_inventory_pool_race` or
  `P1-003 tracking_before_first_carrier_scan`.
- AI support, Gorgias, after-sales SaaS: start with `P1-002
  refund_manual_review_boundary`.
- Agent builder, n8n, Make, Zapier, or custom scripts: start with `SCN-002
  timeout_after_commit_retry`, then show trace and patch hints.

Core contrast to explain:

- The bad flow is allowed to mutate the twin state.
- The policy engine judges whether the final commerce state is safe.
- The good flow runs the same scenario and passes because it has the right
  guardrails.
- The platform is not asking whether the API returned `200`; it is asking
  whether the business state is safe.

## Materials To Send

Use these after a demo call:

- `demo_pack/executive_summary.md`
- `demo_pack/sales_one_pager.md`
- `demo_pack/demo_walkthrough.md`
- `demo_pack/scripts/shopify_merchant_agency_demo.md`
- `demo_pack/scripts/ai_support_saas_demo.md`
- `demo_pack/scripts/agent_builder_workflow_demo.md`
- The scenario folder matching the prospect's pain.
- `docs/POC_OUTREACH_10_CONVERSATIONS.md`

For operators who cannot connect a live workflow yet, use anonymized exports or
workflow descriptions as the POC input. Offline Audit remains a supporting path,
but the current V3.5 story is Live Agent / Workflow Safety.

## Readiness Checklist

- `smoke_v35` passes in the current worktree.
- `tools/smoke_p1_variants.sh` passes.
- `demo_pack/executive_summary.md` includes both P0 and P1 scenarios.
- The prospect has a clear entrypoint:
  - Shopify merchant / agency: inventory, tracking, refund P1 demo.
  - AI support / after-sales SaaS: refund boundary and tracking visibility.
  - Agent builder / workflow agency: webhook, retry, idempotency, trace, patch hints.
- The ask is concrete:
  - one workflow or anonymized sample;
  - three to five scenario runs;
  - one risk report;
  - one review call;
  - $500-$2,000 paid POC.

## POC Ask

Use this wording:

```txt
If we use your anonymized workflow or sample order/inventory/refund data to run
3-5 accident scenarios and return a traceable risk report, would you pay
$500-$2,000 for a focused pre-production safety check?
```

The goal of the first 10 conversations is not to sell a full platform. It is to
test whether prospects recognize the scenarios, want their own flow tested, and
will pay for a narrow risk report.

## Do Not Sell Yet

Do not position this as:

- A full Shopify sandbox.
- A full Amazon SP-API emulator.
- A GitHub PR platform.
- A buyer red-team product.
- An autonomous fixer.
- A replacement for ERP, WMS, Shopify Flow, Gorgias, n8n, Make, or Zapier.

The current sellable wedge is:

```txt
Live Agent / Workflow Safety Demo + focused POC risk report.
```

Offline Audit remains useful when a merchant or operator cannot connect a live
workflow yet, but it should not displace the Live Agent Sandbox-first narrative.
