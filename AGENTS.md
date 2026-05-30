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

## Current Product Direction

The product is `Commerce Automation Safety Sandbox`: a pre-production crash
test layer for commerce automation and AI agents.

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
- Every V3.5 stage must define and pass a strict gate before the next stage
  begins.

## Current Non-Goals

Do not build these in the current lane:

- GitHub PR check
- Shopify-like or Amazon-like full API skin
- Buyer simulator
- Agent container
- Egress proxy
- New P0 scenario classes
- Hosted multi-tenant control plane
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
```
