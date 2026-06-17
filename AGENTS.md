# Agent Operating Notes

For internal Codex and coding-agent use only.

Do not rely on local machine paths. This repository should stay shareable with
collaborators, investors, and POC customers without exposing personal local
environment details.

## Current Source Of Truth

- `README.md`
- `ROADMAP.md`
- `SCENARIO_LIBRARY.md`
- `MVP_ACCEPTANCE.md`
- `docs/DEMO_POC_READINESS.md`
- `docs/OFFLINE_AUDIT_POC_PLAYBOOK.md`
- `docs/MCP_SERVER_SETUP.md`
- `docs/openapi/live_twin_api.yaml`
- `docs/STAGE14_PRODUCTIONIZATION_GATE.md`
- `docs/STAGE15_RELEASE_HYGIENE_CI_GATE.md`
- `docs/STAGE16_SECURITY_ABUSE_HARDENING.md`
- `docs/STAGE17_RUN_MANIFEST_SCHEMA_VERSIONING.md`
- `docs/STAGE18_AGENT_INTEGRATION_EXAMPLES.md`
- `docs/STAGE19_HOSTED_DESIGN_PARTNER_TRUST_GATE.md`
- `docs/STAGE19_RELEASE_CANDIDATE.md`
- `docs/PR_STAGE19_DESCRIPTION.md`
- `docs/HOSTED_DESIGN_PARTNER_ONBOARDING.md`
- `docs/design_partner_poc/README.md`
- `design_partner_poc_package.yaml`
- `docs/security/SECURITY_OVERVIEW.md`
- `docs/security/CONTROL_MATRIX.md`
- `release_hygiene.yaml`
- `security_hardening.yaml`
- `.github/workflows/v35-ci.yml`

## Current Product Direction

The product is now `Agent Integration Safety Sandbox`: a pre-production crash
test layer for SaaS AI agents that touch billing, notifications, and developer
workflow state.

The V0 mainline twins are:

- `StripeTwin`
- `SlackTwin`
- `GitHubTwin`

The first SaaS cross-service policy demo is
`SAAS-001_failed_payment_success_notification`: failed Stripe payment must not
turn into Slack/GitHub success state, and Slack delivery failures must remain
visible.

`SAAS-002_private_channel_billing_alert_fallback` is the second SaaS billing
regression. It must keep using `policy_packs: [saas_billing_v0]` and prove
legacy commerce findings do not leak into SaaS runs.

SAAS-001 must be runnable through agent-facing HTTP/MCP actions. Do not write
new demo code that reaches into `session.environment.twins[...]` unless it is a
low-level unit test for a twin implementation.

Shopify, Amazon, fulfillment, warehouse, and inventory flows are legacy
commerce coverage. Keep them green while they exist, but do not extend them as
the product direction.

The V3.5 mainline is:

```txt
Live Agent Sandbox-first
```

Core narrative:

```txt
External Agent -> MCP/HTTP Twin -> Scenario Fault -> Policy Finding -> Patch Hints
```

MCP is not optional for V3.5. It is a required native interface for Codex,
Claude, and other agent builders. HTTP Twin API is also required for workflows,
scripts, and non-MCP clients.

`Offline Fulfillment Automation Audit` remains a useful supporting entrypoint,
but it is no longer the mainline for V3.5 execution.

## Hard MVP Principles

- Use `Permissive Twin + Policy Check`: unsafe actions are allowed to mutate
  twin state, then policies catch the resulting business incident.
- Scenario-backed live sessions must run only their active `policy_packs`:
  SaaS scenarios use `saas_billing_v0`, and legacy commerce scenarios use
  `legacy_commerce`.
- SaaS V0 supports only Stripe, Slack, and GitHub twins. Do not add Notion,
  Linear, HubSpot, Shopify, Amazon, warehouse, or inventory as new V0 product
  surfaces.
- No production Stripe keys, production Slack bot tokens, production GitHub
  installation tokens, customer PII, real refunds, or real PR writes in POC
  mode.
- Keep the legacy commerce P0 library to exactly five regression scenarios:
  `SCN-001 duplicate_webhook_fulfillment`,
  `SCN-002 timeout_after_commit_retry`,
  `SCN-003 stale_inventory_oversell`,
  `SCN-004 refund_after_shipment_bypass`, and
  `SCN-005 cancel_after_pick_pack_conflict`.
- Do not add a sixth P0 scenario. Tracking timing, SKU mapping, timezone,
  null discount, and similar cases belong in P1.
- The same scenario YAML must drive both `bad_runner` and `good_runner`.
- `bad_runner` must fail with structured policy findings and non-zero exit.
- `good_runner` must pass with zero findings.
- Replay must read from `trace.json`; it must not rerun the scenario.
- Run artifacts must include `trace.json`, `policy_report.json`,
  `state_diff.json`, `report.md`, `patch_hints.json`, and `run_manifest.json`.
- Keep `PolicyFinding` structured with `policy_id`, `severity`, `status`,
  `evidence`, `business_impact`, and `recommendation`.
- Every V3.5 stage must define and pass a strict gate before the next stage
  begins.

## Current Non-Goals

Do not build these in the current lane:

- Real GitHub App / PR writes
- Real Stripe API compatibility
- Real Slack OAuth
- Shopify-like or Amazon-like full API skin extensions
- New fulfillment, warehouse, or inventory product work
- Buyer simulator
- Agent container
- Egress proxy
- New P0 scenario classes
- Hosted multi-tenant control plane beyond the Stage 19 Design Partner Trust Gate
- Decorative dashboard polish before live agent validation works

## V3.5 Stage Gates

Stage 0 is the active rebaseline stage. Its gate is:

```bash
./tools/smoke_stage0_rebaseline.sh
```

After Stage 0, follow `ROADMAP.md` stage by stage:

1. Stage 1: Live Session Kernel.
2. Stage 2: HTTP Twin API Vertical Slice.
3. Stage 3: MCP Interface MVP.
4. Stage 4: Five P0 Live Coverage.
5. Stage 5: Action Log Adapter + CI Gate.
6. Stage 6: Agent-Readable Repair Loop.
7. Stage 7: V3.5 Demo Pack.
8. Stage 8: Arga-style Next Layer.
9. Stage 9: Real MCP + API Hardening.
10. Stage 10: Full P0 MCP/HTTP Coverage.
11. Stage 11: Strict OpenAPI Contract Hardening.
12. Stage 12: Shopify-like Skin V0 Vertical Slice.
13. Stage 13: Amazon Seller Ops Safety Skin V0.
14. Stage 14: Productionization Gate.
15. Stage 15: Release Hygiene + CI Gate.
16. Stage 16: Security / Abuse Hardening.
17. Stage 17: Run Manifest + Artifact Schema Versioning.
18. Stage 18: Agent Integration Examples.
19. Stage 19: Hosted Design Partner Trust Gate.

## Completion Gate

The current full baseline gate remains:

```bash
./tools/smoke_all.sh
```

The V3.5 release gate is:

```bash
./tools/smoke_v35.sh
```

Stage 9 MCP/API gates require Python 3.10+:

```bash
PYTHON=python3.12 ./tools/smoke_stage9_real_mcp.sh
PYTHON=python3.12 ./tools/smoke_stage9_api_hardening.sh
PYTHON=python3.12 ./tools/smoke_stage10_mcp_p0_all.sh
PYTHON=python3.12 ./tools/smoke_stage10_http_p0_all.sh
PYTHON=python3.12 ./tools/smoke_stage11_openapi_contract.sh
./tools/smoke_stage12_shopify_skin_v0.sh
./tools/smoke_stage13_amazon_skin_v0.sh
PYTHON=python3.12 ./tools/smoke_stage13_amazon_mcp_v0.sh
PYTHON=python3.12 ./tools/smoke_stage15_release_hygiene.sh
PYTHON=python3.12 ./tools/smoke_stage16_security_abuse.sh
PYTHON=python3.12 ./tools/smoke_stage17_run_manifest.sh
PYTHON=python3.12 ./tools/smoke_stage18_agent_examples.sh
PYTHON=python3.12 ./tools/smoke_stage19_release_candidate.sh
PYTHON=python3.12 ./tools/smoke_stage19_hosted_enterprise_poc.sh
```
