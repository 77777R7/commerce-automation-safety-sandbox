# V3.5 Acceptance Contract

This document defines the non-negotiable behavior for the Commerce Automation
Safety Sandbox. It preserves the existing incident core and rebaselines V3.5
toward Live Agent Sandbox-first execution.

V3.5 core narrative:

```txt
External Agent -> MCP/HTTP Twin -> Scenario Fault -> Policy Finding -> Patch Hints
```

MCP is not optional for V3.5. HTTP Twin API and action-log replay are also
required surfaces. Offline Audit remains a supporting entrypoint and no longer
defines the mainline.

## Hard Rules

1. V3.5 is Live Agent Sandbox-first.
2. The twin is permissive: bad actions must be allowed to mutate state.
3. Policy Engine detects incidents after the twin records state changes.
4. Policy findings must make `commerce-safety run` exit non-zero by default.
5. The same scenario must exercise both safe and unsafe automation.
6. Replay reads from `trace.json`; it must not rerun the scenario.
7. Every run writes:
   - `trace.json`
   - `policy_report.json`
   - `state_diff.json`
   - `report.md`
8. `PolicyFinding` must include:
   - `policy_id`
   - `severity`
   - `status`
   - `evidence`
   - `business_impact`
   - `recommendation`
9. Inventory accident signals must compare actual reserved inventory to expected
   order quantity, not use a naive `reserved > 1` check.
10. Duplicate webhook detection should track duplicate side effects generally.
    The current slice must at least include reservations and fulfillments.
11. Every stage must define a strict gate and pass it before the next stage.
12. V3.5 live validation must prove unsafe and safe external-agent paths without
    relying only on internal `bad_runner` / `good_runner`.

## Stage Gate Acceptance

Stage 0 through Stage 9 must follow `ROADMAP.md`. The stage gates are:

```txt
Stage 0: ./tools/smoke_stage0_rebaseline.sh
Stage 1: python -m pytest tests/test_live_session_kernel.py
         ./tools/smoke_stage1_live_session.sh
Stage 2: python -m pytest tests/test_live_http_scn002.py
         ./tools/smoke_stage2_http_scn002.sh
Stage 3: python -m pytest tests/test_mcp_scn002.py
         ./tools/smoke_stage3_mcp_scn002.sh
Stage 4: python -m pytest tests/test_live_p0_coverage.py
         ./tools/smoke_live_all.sh
Stage 5: python -m pytest tests/test_action_log_gate.py
         ./tools/smoke_stage5_action_log_gate.sh
Stage 6: python -m pytest tests/test_agent_repair_artifacts.py
         ./tools/smoke_stage6_repair_loop.sh
Stage 7: python -m pytest tests/test_live_demo_pack.py
         ./tools/smoke_stage7_demo_pack.sh
Stage 8: ./tools/smoke_v35.sh
Stage 9: python -m pytest tests/test_stage9_contracts.py
         PYTHON=python3.12 ./tools/smoke_stage9_real_mcp.sh
         PYTHON=python3.12 ./tools/smoke_stage9_api_hardening.sh
```

No stage is considered complete without fresh gate evidence.

## Stage 0 Rebaseline Acceptance

Gate:

```bash
./tools/smoke_stage0_rebaseline.sh
```

Acceptance:

- `ROADMAP.md`, `AGENTS.md`, `MVP_ACCEPTANCE.md`, and `README.md` all identify
  V3.5 as Live Agent Sandbox-first.
- Source-of-truth docs state that MCP is required for V3.5.
- Source-of-truth docs include the narrative:
  `External Agent -> MCP/HTTP Twin -> Scenario Fault -> Policy Finding -> Patch Hints`.
- Offline Audit is described as supporting or secondary.
- `ROADMAP.md` defines Stage 0 through Stage 9 and gives each stage a gate.

## Stage 1 Live Session Kernel Acceptance

Acceptance:

- `LiveSession` and `SessionManager` exist.
- A session can load `SCN-002_timeout_after_commit_retry`.
- Manual twin calls can mutate state inside one session without affecting another
  session created from the same scenario.
- `complete_session` writes:
  - `trace.json`
  - `policy_report.json`
  - `state_diff.json`
  - `report.md`
  - `patch_hints.md`
  - `patch_hints.json`

## Stage 2 HTTP Twin API Vertical Slice Acceptance

Acceptance:

- `commerce-safety live serve` starts a local server.
- `POST /sessions` creates an isolated session.
- `GET /sessions/{session_id}/tasks/next` returns the seeded SCN-002 task.
- `POST /sessions/{session_id}/twin/create_fulfillment` mutates the twin.
- `GET /sessions/{session_id}/trace` returns recorded events.
- `POST /sessions/{session_id}/complete` evaluates policies and writes artifacts.
- External unsafe Python script fails and external safe Python script passes.

## Stage 3 MCP Interface MVP Acceptance

Acceptance:

- MCP tools exist for:
  - `commerce.start_session`
  - `commerce.get_task`
  - `commerce.create_fulfillment`
  - `commerce.find_fulfillment`
  - `commerce.complete_session`
  - `commerce.get_trace`
  - `commerce.get_policy_report`
  - `commerce.get_patch_hints`
- `SCN-002` unsafe/safe proof can run only through MCP tool calls.
- The proof does not require CLI `bad_runner` or `good_runner`.

## Stage 4 Five P0 Live Coverage Acceptance

Acceptance:

- All five P0 scenarios have external unsafe and external safe live flows.
- Unsafe flows fail with policy findings.
- Safe flows pass with zero findings.
- Live artifact set is written for every run.

## Stage 5 Action Log Adapter + CI Gate Acceptance

Acceptance:

- `commerce-safety live from-action-log` can replay at least SCN-004 refund logs.
- `commerce-safety gate` exits `1` for unsafe logs.
- `commerce-safety gate` exits `0` for safe logs.
- `--json` returns session id, status, artifacts, and findings.

## Stage 6 Agent-Readable Repair Loop Acceptance

Acceptance:

- `patch_hints.json`, `agent_summary.md`, and `failure_explain.md` exist for live
  failures.
- Artifacts identify unsafe agent step, root cause, violated policy, likely
  guardrail, replay command, and suggested repair.

## Stage 7 V3.5 Demo Pack Acceptance

Acceptance:

- `demo_pack/live_agent_validation/` exists.
- Docs exist:
  - `docs/LIVE_AGENT_VALIDATION.md`
  - `docs/MCP_AGENT_QUICKSTART.md`
  - `docs/ACTION_LOG_POC.md`
- Demo narrative is agent sandbox-first, not CLI-only.

## Stage 8 Arga-Style Next Layer Acceptance

Acceptance:

- Stage 8 is split into separate sub-goals before implementation.
- Stage 8 does not start until Stage 7 has passed.
- `./tools/smoke_v35.sh` includes all completed stage gates.

## Stage 9 Real MCP + API Hardening Acceptance

Acceptance:

- A real MCP server is implemented with `modelcontextprotocol/python-sdk`.
- The real MCP server exposes exactly the eight core commerce tools:
  `commerce.start_session`, `commerce.get_task`,
  `commerce.create_fulfillment`, `commerce.find_fulfillment`,
  `commerce.complete_session`, `commerce.get_trace`,
  `commerce.get_policy_report`, and `commerce.get_patch_hints`.
- `docs/MCP_SERVER_SETUP.md` explains Python 3.10+ setup and keeps scope away
  from Sandbox0, Firecracker, full Shopify/Amazon clones, Microcks, and buyer
  simulator.
- `docs/openapi/live_twin_api.yaml` covers the HTTP vertical slice:
  `POST /sessions`, `GET /tasks/next`, `POST /twin/create_fulfillment`,
  `GET /trace`, and `POST /complete`.
- `tools/smoke_stage9_real_mcp.sh` drives SCN-002 unsafe/safe paths through the
  official MCP SDK client, not the internal Python wrapper.
- `tools/smoke_stage9_api_hardening.sh` runs Schemathesis against the HTTP
  OpenAPI contract and then drives a deterministic unsafe/safe state sequence.
- Stage 9 preserves `Permissive Twin + Policy Check`.

## Current Baseline Scenario

Scenario:

```txt
commerce-safety-sandbox/scenarios/duplicate_webhook.yaml
```

Risk:

```txt
duplicate_webhook -> duplicate_fulfillment
```

Expected bad path:

```bash
./commerce-safety run commerce-safety-sandbox/scenarios/duplicate_webhook.yaml --runner bad_runner
```

Acceptance:

- Command exits `1`.
- Status is `failed`.
- `policy_report.json` includes:
  - `no_duplicate_fulfillment`
  - `webhook_dedup_required`
- `state_diff.json` shows:
  - before fulfillments: `0`
  - after fulfillments: `2`
  - expected reserved inventory for `sku_widget_1`: `1`
  - actual reserved inventory for `sku_widget_1`: `2`
  - `duplicated_reserved_inventory: true`
- `webhook_dedup_required.evidence.side_effects_from_same_webhook` includes
  both reservation and fulfillment side effects.

Expected good path:

```bash
./commerce-safety run commerce-safety-sandbox/scenarios/duplicate_webhook.yaml --runner good_runner
```

Acceptance:

- Command exits `0`.
- Status is `passed`.
- `policy_report.json` contains no findings.
- Replay shows the duplicate webhook was skipped.

Replay acceptance:

```bash
./commerce-safety replay runs/<run_id>
```

Acceptance:

- Output starts with `Replay from trace.json`.
- Output includes the recorded timeline.
- It does not execute the scenario again.

## Smoke Gate

The current MVP is considered intact when this passes:

```bash
./tools/smoke_week1.sh
```

The full Demo/POC readiness gate is:

```bash
./tools/smoke_all.sh
```

It runs the P0 scenario gates, regression capture, Offline Audit CSV/XLSX
checks, clean audit check, and demo pack verification.

## Stage 3 Regression Scenario Library Acceptance

Command:

```bash
./commerce-safety save-regression runs/<run_id> --name <name>
```

Acceptance:

- Only failed runs with policy findings can be saved.
- Each new run also captures its source `scenario.yaml`.
- Saved regression directory includes:
  - `scenario.yaml`
  - `trace.json`
  - `policy_report.json`
  - `state_diff.json`
  - `summary.md`
- `summary.md` explains:
  - source run id
  - scenario id and name
  - runner
  - policy findings
  - business impact
  - recommendation
  - future regression gate
- Replay can read the saved regression directory directly:

```bash
./commerce-safety replay regressions/<name>
```

Smoke gate:

```bash
./tools/smoke_stage3_regression.sh
```

## Stage 4 Offline Fulfillment Automation Audit Acceptance

Command:

```bash
./commerce-safety offline-audit \
  --orders orders.csv \
  --inventory inventory.csv \
  --fulfillments fulfillments.csv \
  --refunds refunds.csv \
  --mapping mapping.yaml
```

Current v0 acceptance:

- CLI-first only; no UI, API server, GitHub, MCP, or Offline Audit database.
- CSV and XLSX importer with optional YAML schema mapping.
- XLSX inputs can select worksheets per dataset.
- PII redaction must remove raw buyer identifiers from saved audit inputs.
- Audit output directory includes:
  - `manifest.json`
  - `data_quality.json`
  - `state_reconstruction.json`
  - `policy_report.json`
  - `report.md`
  - `redacted_inputs/orders.csv`
  - `redacted_inputs/inventory.csv`
  - `redacted_inputs/fulfillments.csv`
  - `redacted_inputs/refunds.csv`
- `data_quality.json` reports row counts, missing headers/values, duplicate
  order lines, orphan fulfillments/refunds, unknown inventory SKUs, and negative
  inventory rows.
- `state_reconstruction.json` reconstructs orders, inventory, fulfillments,
  refunds, and ordered/fulfilled/refunded aggregates.
- `policy_report.json` uses structured findings with:
  - `policy_id`
  - `severity`
  - `status`
  - `evidence`
  - `business_impact`
  - `recommendation`
- `report.md` must be readable by operators and explain risk score, top
  findings, business impact, and recommended fixes.
- The command exits non-zero when policy findings exist so Offline Audit can
  later become a gate.

Smoke gate:

```bash
./tools/smoke_stage4_offline_audit.sh
./tools/smoke_stage4_offline_audit_xlsx.sh
./tools/smoke_stage4_offline_audit_clean.sh
```

## P0 Scenario Library Acceptance

The P0 library has exactly five flagship scenarios:

1. `SCN-001 duplicate_webhook_fulfillment`
2. `SCN-002 timeout_after_commit_retry`
3. `SCN-003 stale_inventory_oversell`
4. `SCN-004 refund_after_shipment_bypass`
5. `SCN-005 cancel_after_pick_pack_conflict`

Acceptance rules for every P0 scenario:

- Do not add a sixth P0 scenario.
- Each scenario tells one main accident.
- Same scenario YAML drives both `bad_runner` and `good_runner`.
- `bad_runner` fails with a policy finding and non-zero exit.
- `good_runner` passes with zero exit.
- The twin permits unsafe state mutation before policy evaluation.
- `trace.json`, `policy_report.json`, `state_diff.json`, and `report.md`
  are written.
- Report narrative keeps one primary policy clear; secondary findings can
  support the main story but should not blur it.

Deferred P1 examples:

- Tracking uploaded before first carrier scan.
- SKU mapping mismatch.
- Timezone cutoff errors.
- Null discount or price edge cases.

## SCN-002 Timeout After Commit Retry

Scenario:

```txt
commerce-safety-sandbox/scenarios/SCN-002_timeout_after_commit_retry.yaml
```

Risk:

```txt
timeout_after_commit -> unsafe_retry -> duplicate_fulfillment
```

Expected bad path:

```bash
./commerce-safety run commerce-safety-sandbox/scenarios/SCN-002_timeout_after_commit_retry.yaml --runner bad_runner
```

Acceptance:

- Command exits `1`.
- Status is `failed`.
- `policy_report.json` includes:
  - `idempotency_required_for_mutating_retries`
  - `no_duplicate_fulfillment`
- Trace shows the twin committed the first fulfillment, then returned
  `timeout_after_commit`.
- Trace shows `bad_runner` created a second fulfillment after timeout.
- `state_diff.json` shows:
  - before fulfillments: `0`
  - after fulfillments: `2`
  - `duplicate_fulfillment: true`
  - `duplicated_reserved_inventory: false`

Expected good path:

```bash
./commerce-safety run commerce-safety-sandbox/scenarios/SCN-002_timeout_after_commit_retry.yaml --runner good_runner
```

Acceptance:

- Command exits `0`.
- Status is `passed`.
- `policy_report.json` contains no findings.
- Trace shows `good_runner` checks existing fulfillment state after timeout and
  confirms the already-committed fulfillment.

Smoke gate:

```bash
./tools/smoke_scn002.sh
```

## SCN-003 Stale Inventory Oversell

Scenario:

```txt
commerce-safety-sandbox/scenarios/SCN-003_stale_inventory_oversell.yaml
```

Risk:

```txt
stale_inventory -> promise_without_reservation -> oversell
```

Expected bad path:

```bash
./commerce-safety run commerce-safety-sandbox/scenarios/SCN-003_stale_inventory_oversell.yaml --runner bad_runner
```

Acceptance:

- Command exits `1`.
- Status is `failed`.
- `policy_report.json` includes:
  - `reservation_required_before_promise`
  - `no_inventory_commit_from_stale_snapshot`
  - `no_oversell`
- Trace shows `bad_runner` reads stale local inventory and promises fulfillment.
- `state_diff.json` shows:
  - before fulfillment promises: `0`
  - after fulfillment promises: `1`
  - `unreserved_fulfillment_promise: true`
  - `oversell_risk: true`

Expected good path:

```bash
./commerce-safety run commerce-safety-sandbox/scenarios/SCN-003_stale_inventory_oversell.yaml --runner good_runner
```

Acceptance:

- Command exits `0`.
- Status is `passed`.
- `policy_report.json` contains no findings.
- Trace shows `good_runner` refreshes inventory and routes the order to manual review.
- No fulfillment promise is created.

Smoke gate:

```bash
./tools/smoke_scn003.sh
```

## SCN-004 Refund After Shipment Approval Bypass

Scenario:

```txt
commerce-safety-sandbox/scenarios/SCN-004_refund_after_shipment_bypass.yaml
```

Risk:

```txt
shipped_order -> refund_without_approval -> money_plus_goods_loss
```

Expected bad path:

```bash
./commerce-safety run commerce-safety-sandbox/scenarios/SCN-004_refund_after_shipment_bypass.yaml --runner bad_runner
```

Acceptance:

- Command exits `1`.
- Status is `failed`.
- `policy_report.json` includes:
  - `no_refund_after_shipment_without_approval`
  - `high_value_refund_requires_approval`
- Trace shows `bad_runner` receives the refund request and issues the refund
  despite shipped/carrier-scanned state.
- `state_diff.json` shows:
  - before refunds: `0`
  - after refunds: `1`
  - after approval requests: `0`
  - refund amount issued: `120.0`
  - `post_shipment_refund_without_approval: true`
  - `high_value_refund_without_approval: true`

Expected good path:

```bash
./commerce-safety run commerce-safety-sandbox/scenarios/SCN-004_refund_after_shipment_bypass.yaml --runner good_runner
```

Acceptance:

- Command exits `0`.
- Status is `passed`.
- `policy_report.json` contains no findings.
- Trace shows `good_runner` checks shipment state, creates an approval request,
  and holds the refund until review.
- No refund is issued.

Smoke gate:

```bash
./tools/smoke_scn004.sh
```

## SCN-005 Cancel After Pick/Pack Warehouse Conflict

Scenario:

```txt
commerce-safety-sandbox/scenarios/SCN-005_cancel_after_pick_pack_conflict.yaml
```

Risk:

```txt
cancel_after_pick -> cancel_refund_release -> warehouse_still_ships
```

Expected bad path:

```bash
./commerce-safety run commerce-safety-sandbox/scenarios/SCN-005_cancel_after_pick_pack_conflict.yaml --runner bad_runner
```

Acceptance:

- Command exits `1`.
- Status is `failed`.
- `policy_report.json` includes:
  - `warehouse_conflict_requires_hold`
  - `no_ship_after_cancel`
  - `no_double_refund_or_inventory_release`
- Trace shows `bad_runner` marks the order cancelled, releases inventory,
  issues a refund, and warehouse still ships.
- `state_diff.json` shows:
  - before reserved inventory for `sku_pickpack_1`: `1`
  - after reserved inventory for `sku_pickpack_1`: `0`
  - after refunds: `1`
  - after inventory releases: `1`
  - after workflow holds: `0`
  - after warehouse cancellation requests: `0`
  - `warehouse_conflict_without_hold: true`
  - `ship_after_cancel: true`
  - `refund_and_inventory_release_while_warehouse_continued: true`

Expected good path:

```bash
./commerce-safety run commerce-safety-sandbox/scenarios/SCN-005_cancel_after_pick_pack_conflict.yaml --runner good_runner
```

Acceptance:

- Command exits `0`.
- Status is `passed`.
- `policy_report.json` contains no findings.
- Trace shows `good_runner` checks warehouse progress, creates a workflow hold,
  submits a warehouse cancellation request, and does not refund or release
  inventory yet.
- Order remains open while warehouse resolution is pending.

Smoke gate:

```bash
./tools/smoke_scn005.sh
```
