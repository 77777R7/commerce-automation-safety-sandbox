# Commerce Automation Safety Sandbox V3.5 Roadmap

This roadmap supersedes the earlier Offline Audit-first roadmap. The product
mainline is now `Live Agent Sandbox` first: external AI agents must be able to
connect to a stateful commerce twin, make real commerce mutations under seeded
scenario faults, and receive policy findings plus agent-readable repair
artifacts.

Core narrative:

```txt
External Agent -> MCP/HTTP Twin -> Scenario Fault -> Policy Finding -> Patch Hints
```

## Product Direction

Build one commerce automation incident validation core with live agent testing
as the primary entrypoint.

- Primary: `Live Commerce Agent Validation` for AI agents, workflows, and SaaS
  builders.
- Required V3.5 interface: MCP. MCP is not optional for V3.5 because agent
  builders need a native tool interface.
- Required V3.5 interface: HTTP Twin API for workflows, scripts, and non-MCP
  clients.
- Supporting entrypoint: `Offline Fulfillment Automation Audit` remains useful
  for operators and POCs, but it is no longer the project mainline.

## Existing Foundation

The repo already has a working incident core:

- Five P0 commerce accident scenarios.
- `Permissive Twin + Policy Check`.
- `bad_runner` / `good_runner` CLI validation.
- `trace.json`, `policy_report.json`, `state_diff.json`, and `report.md`.
- Regression scenario capture.
- Offline Audit v0.
- Demo pack and static demo viewer.

Do not rewrite this foundation. V3.5 builds live agent validation on top of it.

## Current Non-Goals

Do not build these before the relevant stage gate asks for them:

- Full Shopify GraphQL implementation.
- Full Amazon SP-API clone.
- Hosted multi-tenant control plane.
- Agent container, egress proxy, browser runner, or microVM runtime.
- Buyer simulator or autonomous red-team buyer.
- GitHub App / PR check before Stage 10.
- Decorative dashboard polish before the live agent sandbox core works.
- New P0 scenario classes.

## Global Stage Rule

Each stage must have a named gate. Do not move to the next stage until the
current stage gate passes in the current worktree.

The complete V3.5 objective is not achieved until Stage 9 passes. Stage 8 is
the Arga-style next-layer plan; Stage 9 hardens the real MCP and HTTP agent
interfaces.

## Stage 0: V3.5 Rebaseline

Goal: move the project source of truth from Offline Audit-first to Live Agent
Sandbox-first.

Deliverables:

- Update `ROADMAP.md`.
- Update `AGENTS.md`.
- Update `MVP_ACCEPTANCE.md`.
- Update `README.md` if needed for public orientation.
- Mark MCP as required for V3.5.
- Mark Offline Audit as a supporting entrypoint, not the mainline.
- Define strict gates for Stage 0 through Stage 9.

Gate:

```bash
./tools/smoke_stage0_rebaseline.sh
```

The gate must verify that source-of-truth docs contain:

- `Live Agent Sandbox-first`.
- `MCP is not optional for V3.5`.
- `External Agent -> MCP/HTTP Twin -> Scenario Fault -> Policy Finding -> Patch Hints`.
- `Offline Audit` described as supporting or secondary.
- Stage 0 through Stage 9 sections.

## Stage 1: Live Session Kernel

Goal: extract live validation session lifecycle before HTTP or MCP.

Deliverables:

- `LiveSession`.
- `SessionManager`.
- `complete_session`.
- Shared artifact writer for live runs.
- `patch_hints.md`.
- `patch_hints.json`.

Acceptance:

- A session can load `SCN-002_timeout_after_commit_retry`.
- A test can manually call twin methods inside that session.
- `complete_session` evaluates policies and writes:
  - `trace.json`
  - `policy_report.json`
  - `state_diff.json`
  - `report.md`
  - `patch_hints.md`
  - `patch_hints.json`
- Session state is isolated between two sessions created from the same scenario.

Gate:

```bash
python -m pytest tests/test_live_session_kernel.py
./tools/smoke_stage1_live_session.sh
```

Do not proceed to Stage 2 until both commands pass.

## Stage 2: HTTP Twin API Vertical Slice

Goal: complete the first true external-agent demo over HTTP.

Scope: only `SCN-002 timeout_after_commit_retry`.

Deliverables:

```txt
commerce-safety live serve
POST /sessions
GET /sessions/{session_id}/tasks/next
POST /sessions/{session_id}/twin/create_fulfillment
GET /sessions/{session_id}/trace
POST /sessions/{session_id}/complete
```

Acceptance:

- An external Python script calls the HTTP Twin API.
- Unsafe path triggers `timeout_after_commit` and retries blindly.
- Safe path uses a stable idempotency key and/or queries existing fulfillment.
- Unsafe path fails with policy findings.
- Safe path passes with zero findings.
- API remains permissive: unsafe commerce actions mutate state first and are
  caught by policy evaluation after completion.

Gate:

```bash
python -m pytest tests/test_live_http_scn002.py
./tools/smoke_stage2_http_scn002.sh
```

## Stage 3: MCP Interface MVP

Goal: give AI agents a native interface.

Required MCP tools:

```txt
commerce.start_session
commerce.get_task
commerce.create_fulfillment
commerce.find_fulfillment
commerce.complete_session
commerce.get_trace
commerce.get_policy_report
commerce.get_patch_hints
```

Acceptance:

- `SCN-002` unsafe and safe paths can run only through MCP tool calls.
- The proof does not use CLI `bad_runner` / `good_runner`.
- MCP outputs are structured enough for Codex/Claude to inspect trace, findings,
  and patch hints.

Gate:

```bash
python -m pytest tests/test_mcp_scn002.py
./tools/smoke_stage3_mcp_scn002.sh
```

## Stage 4: Five P0 Live Coverage

Goal: convert all five P0 scenarios to live mode.

Deliverables:

- Live external unsafe/safe flows for:
  - `SCN-001 duplicate_webhook_fulfillment`
  - `SCN-002 timeout_after_commit_retry`
  - `SCN-003 stale_inventory_oversell`
  - `SCN-004 refund_after_shipment_bypass`
  - `SCN-005 cancel_after_pick_pack_conflict`
- Twin/API actions needed by P0 live mode:
  - inventory promise
  - inventory refresh
  - manual review route
  - refund approval
  - warehouse hold/cancel
  - cancel order
  - release inventory
  - warehouse continues fulfillment
  - find fulfillment

Acceptance:

- Every P0 scenario has external unsafe fail and external safe pass.
- Every run writes the live artifact set.
- The twin stays permissive in all live flows.

Gate:

```bash
python -m pytest tests/test_live_p0_coverage.py
./tools/smoke_live_all.sh
```

## Stage 5: Action Log Adapter + CI Gate

Goal: serve AI SaaS and agency prospects who cannot connect directly by API yet.

Deliverables:

```txt
commerce-safety live from-action-log
commerce-safety gate
--json
```

Acceptance:

- `SCN-004 refund_after_shipment_bypass` action log can be replayed into a live
  session.
- Bad action log generates trace/report and exits `1`.
- Safe action log exits `0`.
- `--json` includes session id, status, artifact paths, and findings.

Gate:

```bash
python -m pytest tests/test_action_log_gate.py
./tools/smoke_stage5_action_log_gate.sh
```

## Stage 6: Agent-Readable Repair Loop

Goal: make the product start feeling Arga-like by producing repair artifacts
that Codex/Claude can directly use.

Deliverables:

```txt
patch_hints.json
agent_summary.md
failure_explain.md
likely_guardrails
replay command
```

Acceptance:

- For each supported policy finding, artifacts explain:
  - the unsafe agent step
  - root cause
  - violated policy
  - likely guardrail
  - replay command
  - suggested repair
- Codex/Claude can identify what to change without reading source code.

Gate:

```bash
python -m pytest tests/test_agent_repair_artifacts.py
./tools/smoke_stage6_repair_loop.sh
```

## Stage 7: V3.5 Demo Pack

Goal: replace the toy-like demo with an agent sandbox demo.

Deliverables:

```txt
demo_pack/live_agent_validation/
docs/LIVE_AGENT_VALIDATION.md
docs/MCP_AGENT_QUICKSTART.md
docs/ACTION_LOG_POC.md
```

Demo narrative:

```txt
External Agent -> MCP/HTTP Twin -> Scenario Fault -> Policy Finding -> Patch Hints
```

Acceptance:

- Demo pack shows at least:
  - HTTP external agent unsafe/safe path for `SCN-002`
  - MCP unsafe/safe path for `SCN-002`
  - Action-log replay for `SCN-004`
- A reader can understand why this is an AI agent sandbox, not an internal
  CLI-only demo.

Gate:

```bash
python -m pytest tests/test_live_demo_pack.py
./tools/smoke_stage7_demo_pack.sh
```

## Stage 8: Arga-Style Next Layer

Goal: add developer workflow and platform depth after V3.5 live validation
works.

Deferred capabilities:

- GitHub Actions gate.
- PR check.
- Scenario registry.
- Stub coverage.
- Trace streaming.
- Hosted sessions.
- Team workspace.

Acceptance:

- Stage 8 must be split into separate sub-goals before implementation.
- No Stage 8 work should begin until Stage 7 has passed.

Gate:

```bash
./tools/smoke_v35.sh
```

The Stage 8 gate must include all earlier stage gates plus any new developer
workflow checks introduced in Stage 8.

## Stage 9: Real MCP + API Hardening

Goal: turn the V3.5 interfaces from internal demo surfaces into real agent and
API contracts that can be called by external agent runtimes and tested by API
property tools.

Deliverables:

- Real MCP server using `modelcontextprotocol/python-sdk`.
- Eight core MCP tools:
  - `commerce.start_session`
  - `commerce.get_task`
  - `commerce.create_fulfillment`
  - `commerce.find_fulfillment`
  - `commerce.complete_session`
  - `commerce.get_trace`
  - `commerce.get_policy_report`
  - `commerce.get_patch_hints`
- `docs/MCP_SERVER_SETUP.md`.
- Real MCP smoke through official SDK client calls for `SCN-002` unsafe and safe
  paths.
- OpenAPI spec for the HTTP Twin API.
- Schemathesis API hardening gate for the HTTP vertical slice plus deterministic
  unsafe/safe state sequence.

Non-goals:

- Sandbox0.
- Firecracker or gVisor.
- Shopify/Amazon full API clones.
- Microcks full integration.
- Buyer simulator.

Gate:

```bash
python -m pytest tests/test_stage9_contracts.py
PYTHON=python3.12 ./tools/smoke_stage9_real_mcp.sh
PYTHON=python3.12 ./tools/smoke_stage9_api_hardening.sh
```

Stage 9 keeps the core product principle:

```txt
Permissive Twin + Policy Check
```

## Full V3.5 Gate

Once Stage 9 is implemented, the V3.5 release gate is:

```bash
./tools/smoke_v35.sh
```

This command must run:

- Existing core smoke checks.
- Stage 0 rebaseline check.
- Stage 1 live session checks.
- Stage 2 HTTP vertical slice.
- Stage 3 MCP vertical slice.
- Stage 4 five P0 live coverage.
- Stage 5 action-log/CI gate.
- Stage 6 repair artifacts.
- Stage 7 live demo pack generation.
- Stage 9 real MCP server and API hardening gates.
