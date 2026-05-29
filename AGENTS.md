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

## Current Product Direction

The product is `Commerce Automation Safety Sandbox`: a pre-production crash
test layer for commerce automation and AI agents.

The current sellable wedge is:

```txt
Offline Fulfillment Automation Audit
```

## Hard MVP Principles

- Use `Permissive Twin + Policy Check`: unsafe actions are allowed to mutate
  twin state, then policies catch the resulting business incident.
- Keep the P0 library to exactly five flagship scenarios:
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
  `state_diff.json`, and `report.md`.
- Keep `PolicyFinding` structured with `policy_id`, `severity`, `status`,
  `evidence`, `business_impact`, and `recommendation`.

## Current Non-Goals

Do not build these in the current lane:

- API server
- GitHub PR check
- MCP server
- Shopify-like or Amazon-like full API skin
- Buyer simulator
- Agent container
- Egress proxy
- New P0 scenario classes

## Completion Gate

The full Demo/POC readiness gate is:

```bash
./tools/smoke_all.sh
```
