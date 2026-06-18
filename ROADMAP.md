# Agent Integration Safety Sandbox Roadmap

This roadmap supersedes the commerce-first roadmap. The product mainline is now
SaaS Agent Validation-first: external AI agents must be able to connect to
stateful Stripe, Slack, and GitHub twins, make realistic integration mutations
under seeded scenario faults, and receive policy findings plus agent-readable
repair artifacts before touching production systems.

Core narrative:

```txt
External Agent -> MCP/HTTP Twin -> Scenario Fault -> Policy Finding -> Patch Hints
```

## Product Direction

Build one agent integration validation core with live agent testing as the
primary entrypoint.

- Primary: `SaaS Agent Validation` for AI agents, workflows, and SaaS builders
  that touch billing, notifications, and developer workflow state.
- V0 twins: `StripeTwin`, `SlackTwin`, and `GitHubTwin`.
- Required V3.5 interface: MCP. MCP is not optional for V3.5 because agent
  builders need a native tool interface.
- Required V3.5 interface: HTTP Twin API for workflows, scripts, and non-MCP
  clients.
- Supporting entrypoint: `Offline Fulfillment Automation Audit` remains useful
  for operators and POCs, but it is no longer the project mainline.
- Legacy coverage: Shopify, Amazon, fulfillment, warehouse, and inventory
  remain as existing regression/demo coverage only. Do not extend them as the
  main product surface.

## Existing Foundation

The repo already has a working incident core:

- Five P0 commerce accident scenarios.
- `Permissive Twin + Policy Check`.
- `bad_runner` / `good_runner` CLI validation.
- `trace.json`, `policy_report.json`, `state_diff.json`, `report.md`, and
  `run_manifest.json`.
- Regression scenario capture.
- Offline Audit v0.
- Demo pack and static demo viewer.

Do not rewrite this foundation. The SaaS rebaseline keeps the session,
artifact, policy, MCP, HTTP, action-log, and hosted trust-boundary machinery
while replacing the product domain.

## Immediate SaaS Rebaseline Phases

Phase 0: Restore Worktree Readability

- Hydrate or replace the dataless local checkout with a readable Git worktree.
- Preserve a backup of the broken/dataless directory.
- Capture a clean baseline with Stage 0, unit tests, and `smoke_v35`.

Phase 1: SaaS Rebaseline Docs And Boundaries

- Update `README.md`, `ROADMAP.md`, `MVP_ACCEPTANCE.md`, and `AGENTS.md`.
- State that Stripe, Slack, and GitHub are the only V0 mainline twins.
- Mark Shopify, Amazon, fulfillment, warehouse, and inventory as legacy.
- Preserve `Permissive Twin + Policy Check`.
- Preserve the artifact loop: `trace.json`, `policy_report.json`,
  `state_diff.json`, `report.md`, `patch_hints.json`, and
  `run_manifest.json`.
- State POC safety boundaries: no production API keys, no customer PII, no real
  refunds, and no real PR writes.

Phase 2: Sandbox Environment Abstraction

- Add `SandboxEnvironment`.
- Add `TwinBundle`.
- Add `ToolCallEvent`.
- Expose `session.environment.twins["stripe"]`,
  `session.environment.twins["slack"]`, `session.environment.twins["github"]`,
  and `session.events`.
- Keep `CommerceTwin` as a legacy compatibility twin until Stripe/Slack/GitHub
  V0 implementations replace it in the active scenarios.

Phase 3: StripeTwin V0

- Add a narrow `StripeTwin`.
- Support customer, subscription, invoice, payment intent, refund, and Stripe
  event state.
- Support failed payment, invoice payment recovery, refund creation, event
  retrieval, and duplicate webhook delivery tracking.
- Keep the twin permissive: refunds and failed billing states mutate sandbox
  state first; policies evaluate the resulting state later.
- Expose the Stripe snapshot through `session.environment.twins["stripe"]`.

Phase 4: SlackTwin + GitHubTwin V0 And SAAS-001

- Add narrow `SlackTwin` and `GitHubTwin` surfaces.
- Slack V0 supports channel state, bot membership, message delivery, permission
  failures, billing failure alerts, and success notification signals.
- GitHub V0 supports repo context, pull requests, check runs, issues, PR
  comments, success-check signals, and review artifacts.
- Add `SAAS-001_failed_payment_success_notification` as the first cross-service
  policy demo.
- Declare `policy_packs: [saas_billing_v0]` for SAAS-001 so SaaS validation
  runs do not evaluate legacy commerce policies.
- Add `policy_packs/saas_billing_v0.yaml` as the auditable pack manifest for
  SaaS billing validation policies, applicable scenarios, non-goals, and
  artifact contract.
- Bad path: Stripe records failed payment, Slack alert delivery fails, and the
  agent still emits Slack/GitHub success state.
- Good path: Stripe failure stays non-success, Slack receives a billing failure
  alert, and GitHub records review/action-required state.
- Policy engine reads the service twin snapshots while legacy commerce policies
  remain isolated behind the `legacy_commerce` policy pack.
- Add `SAAS-002_private_channel_billing_alert_fallback` as the same
  `saas_billing_v0` pack's boundary regression: Slack private-channel delivery
  failure must recover through a delivered fallback alert, and legacy commerce
  findings must not appear in the SaaS run.

Phase 5: SAAS-001 Agent-Facing HTTP/MCP Surface

- Expose the SAAS-001 hero actions through HTTP and MCP so external agents no
  longer need direct access to `session.environment.twins[...]`.
- MCP tools:
  - `stripe.create_customer`
  - `stripe.create_subscription`
  - `stripe.deliver_webhook`
  - `slack.post_message`
  - `github.create_check_run`
  - `github.create_issue`
  - `github.comment_on_pr`
- HTTP actions:
  - `POST /sessions/{session_id}/twin/stripe_create_customer`
  - `POST /sessions/{session_id}/twin/stripe_create_subscription`
  - `POST /sessions/{session_id}/twin/stripe_deliver_webhook`
  - `POST /sessions/{session_id}/twin/slack_post_message`
  - `POST /sessions/{session_id}/twin/github_create_check_run`
  - `POST /sessions/{session_id}/twin/github_create_issue`
  - `POST /sessions/{session_id}/twin/github_comment_on_pr`
- `GET /sessions/{session_id}/trace` exposes `environment_state` and
  `event_ledger` for agent-readable cross-service inspection.
- Completed sessions write `github_check_summary.json` and
  `github_check_summary.md` so policy findings and patch hints render like a PR
  check result.
- Minimal sandbox lifecycle is available through `POST /sessions` provision
  with optional `ttl_seconds`, `GET /sessions/{session_id}/status`,
  `POST /sessions/{session_id}/reset`, and
  `POST /sessions/{session_id}/teardown`.

## Current Non-Goals

Do not build these before the relevant stage gate asks for them:

- Full Shopify GraphQL implementation or new Shopify product work.
- Full Amazon SP-API clone or new Amazon product work.
- New fulfillment, warehouse, or inventory product work.
- Hosted multi-tenant control plane.
- Agent container, egress proxy, browser runner, or microVM runtime.
- Buyer simulator or autonomous red-team buyer.
- Real GitHub App / real PR writes.
- Real Stripe API compatibility.
- Real Slack OAuth.
- Decorative dashboard polish before the live agent sandbox core works.
- New P0 scenario classes.

## Global Stage Rule

Each stage must have a named gate. Do not move to the next stage until the
current stage gate passes in the current worktree.

The complete V3.5 interface objective is not achieved until Stage 18 passes.
Stage 9 makes the interfaces real, Stage 10 proves all five P0 scenarios
through agent-facing MCP/HTTP paths, Stage 11 tightens the HTTP contract, Stage
12 adds the first platform-shaped adapter without becoming a full Shopify
clone, Stage 13 adds the Amazon Seller Ops Safety Skin V0 without becoming a
full Amazon SP-API clone, Stage 14 hardens production boundaries, Stage 15
makes the release reviewable through hygiene and CI gates, Stage 16 hardens
the local agent-facing surface against accidental exposure and abuse, and Stage
17 stabilizes run artifact contracts with manifests and schema versions. Stage
18 packages runnable external-agent examples so builders can validate MCP,
HTTP, and action-log integrations without reading source code. Stage 19 adds a
hosted design-partner trust boundary so 1-3 staging agents/workflows can use
the MCP/HTTP sandbox without production store access; it is not SOC2
certification or a full enterprise SaaS control plane.

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
- Define strict gates for Stage 0 through Stage 13.

Gate:

```bash
./tools/smoke_stage0_rebaseline.sh
```

The gate must verify that source-of-truth docs contain:

- `Live Agent Sandbox-first`.
- `MCP is not optional for V3.5`.
- `External Agent -> MCP/HTTP Twin -> Scenario Fault -> Policy Finding -> Patch Hints`.
- `Offline Audit` described as supporting or secondary.
- Stage 0 through Stage 13 sections.

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

## Stage 10: Full P0 MCP/HTTP Coverage

Goal: prove the five P0 scenarios run through real agent-facing interfaces, not
only through internal live tool calls.

Deliverables:

- MCP tools for the full P0 action surface:
  - `commerce.reserve_inventory`
  - `commerce.promise_fulfillment`
  - `commerce.refresh_inventory`
  - `commerce.route_manual_review`
  - `commerce.create_refund`
  - `commerce.create_approval_request`
  - `commerce.cancel_order`
  - `commerce.release_inventory`
  - `commerce.place_workflow_hold`
  - `commerce.submit_warehouse_cancellation_request`
  - `commerce.warehouse_continue_fulfillment`
  - `commerce.skip_duplicate_webhook`
- HTTP Twin API endpoints for the same generic commerce actions.
- `tools/smoke_stage10_mcp_p0_all.sh`.
- `tools/smoke_stage10_http_p0_all.sh`.

Acceptance:

- For every P0 scenario:
  - unsafe path via MCP fails with expected policy findings
  - safe path via MCP passes with zero findings
  - unsafe path via HTTP fails with expected policy findings
  - safe path via HTTP passes with zero findings
- Every legacy P0 scenario declares or resolves to `policy_packs:
  [legacy_commerce]`; SaaS policy findings must not appear in legacy P0 runs.
- No Shopify/Amazon clone is introduced; these remain generic commerce actions.
- `Permissive Twin + Policy Check` remains intact.

Gate:

```bash
python -m pytest tests/test_stage10_agent_interface_coverage.py
PYTHON=python3.12 ./tools/smoke_stage10_mcp_p0_all.sh
PYTHON=python3.12 ./tools/smoke_stage10_http_p0_all.sh
```

## Stage 11: Strict OpenAPI Contract Hardening

Goal: make the HTTP OpenAPI contract describe the real agent-facing API instead
of hiding important shapes behind broad objects.

Deliverables:

- Tight `TaskResponse.task` union.
- Tight `FulfillmentResponse.fulfillment`.
- Tight `TraceResponse.timeline`.
- Structured `PolicyFinding.evidence` union.
- Request and response examples for all agent-facing endpoints.
- Explicit Schemathesis warning allowlist for session-bound generated data.
- `tests/test_openapi_contract_shape.py`.
- `tools/smoke_stage11_openapi_contract.sh`.

Acceptance:

- Schemathesis examples, coverage, and stateful phases pass.
- `response_schema_conformance` passes.
- Any remaining schema warning is explicit, narrow, and covered by
  `docs/openapi/schemathesis_warning_allowlist.yaml`.

Gate:

```bash
python -m pytest tests/test_openapi_contract_shape.py
PYTHON=python3.12 ./tools/smoke_stage11_openapi_contract.sh
```

## Stage 12: Shopify-like Skin P0 Coverage

Goal: add the first platform-shaped digital twin skin while keeping the core
commerce twin and policy engine as the source of truth. The skin must cover all
five P0 scenarios without becoming a full Shopify clone.

Scope:

- Shopify-like `orders/paid` and `orders/cancelled` webhook ingestion.
- Shopify-like Admin GraphQL `fulfillmentCreate`, `refundCreate`,
  `inventoryAdjustQuantities`, order cancellation, fulfillment hold, and
  fulfillment cancellation/continuation mutations needed by the five P0
  scenarios.
- Shopify-like inventory level reads and adjustment/reservation mapping.
- Minimal Shopify ops actions for fulfillment promises, manual review, approval
  requests, and warehouse conflict handling.
- Unsupported Shopify mutations must return explicit stub/coverage metadata.

Deliverables:

- Shopify-like coverage and binding manifests.
- Webhook mapper for `X-Shopify-Topic` and `X-Shopify-Webhook-Id`.
- GraphQL mutation router for fulfillment, inventory, refund, approval, order
  cancellation, and warehouse conflict actions.
- Live HTTP routes:
  - `POST /sessions/{session_id}/shopify/webhooks`
  - `POST /sessions/{session_id}/shopify/webhooks/skip_duplicate`
  - `POST /sessions/{session_id}/shopify/admin/api/{version}/graphql.json`
  - `GET /sessions/{session_id}/shopify/admin/api/{version}/inventory_levels.json`
  - `POST /sessions/{session_id}/shopify/admin/api/{version}/inventory_levels/adjust.json`
  - `POST /sessions/{session_id}/shopify/actions/{action}`
  - `GET /sessions/{session_id}/shopify/coverage`
- Stage 12 smoke harness for unsafe/safe paths across all five P0 scenarios.

Acceptance:

- `duplicate_webhook` unsafe path through Shopify-like HTTP fails with
  `webhook_dedup_required` and `no_duplicate_fulfillment`.
- `duplicate_webhook` safe path through Shopify-like HTTP passes when the agent
  dedupes by webhook id, records a positive skip event, and does not create a
  second fulfillment.
- `SCN-002` unsafe path through Shopify-like HTTP fails with
  `idempotency_required_for_mutating_retries` and
  `no_duplicate_fulfillment`.
- `SCN-002` safe path through Shopify-like HTTP passes with a stable
  idempotency key.
- `SCN-003` unsafe/safe paths run through Shopify-like inventory query and
  promise/review actions.
- `SCN-004` unsafe/safe paths run through Shopify-like `refundCreate` and
  approval mapping.
- `SCN-005` unsafe/safe paths run through Shopify-like `orders/cancelled`,
  inventory release, refund, fulfillment hold, warehouse cancellation, and
  warehouse continuation mapping.
- The skin remains an adapter: it maps to generic commerce actions and does not
  perform policy decisions itself.
- No full Shopify GraphQL implementation, OAuth, checkout, product catalog, or
  additional P0 scenario class is introduced.

Gate:

```bash
python -m pytest tests/test_shopify_skin_manifests.py tests/test_shopify_webhook_mapper.py tests/test_shopify_graphql_router.py tests/test_shopify_skin_live_http.py
./tools/smoke_stage12_shopify_skin_v0.sh
```

## Stage 13: Amazon Seller Ops Safety Skin V0

Goal: add an Amazon-shaped seller operations skin that is deep enough to sell as
an automation safety demo, while keeping the core commerce twin and policy
engine as the source of truth. Do not expand into a full Amazon SP-API
emulator.

Scope:

- Only Amazon-shaped inventory/listing/order/feed/notification surfaces needed
  for `SCN-003 stale_inventory_oversell` and
  `SCN-005 cancel_after_pick_pack_conflict`.
- Only generic seller-ops actions that map into the existing permissive twin.
- Unsupported Amazon SP-API areas must stay explicit stubs/non-goals.

Deliverables:

- Amazon Seller Ops coverage and binding manifests.
- Amazon platform binding for `AmazonOrderId`, `OrderItemId`, `SellerSKU`,
  ASIN, FNSKU, marketplace id, and seller id.
- More realistic seller/account binding metadata for canonical seller id,
  seller aliases, marketplace ids, SellerSKU, ASIN, FNSKU, and order-item
  mappings.
- HTTP routes for FBA inventory summaries, Listings Items availability,
  listing quantity patch, Orders/orderItems, confirmShipment, Feeds status,
  Amazon notifications, Amazon seller-ops actions, and coverage metadata.
- Feed processing report metadata for accepted feeds.
- Retryable rate-limit behavior with `retryAfterSeconds` and trace events.
- Explicit stub coverage metadata for unsupported seller-ops surfaces.
- Clear buyer-cancel to confirmShipment conflict trace metadata.
- MCP tools for Amazon inventory, listing, feed, order, notification,
  confirmShipment, seller-ops actions, and coverage metadata.
- Amazon-specific policy findings:
  - `amazon_no_promise_from_stale_inventory_summary`
  - `amazon_no_confirm_shipment_after_buyer_cancel_without_review`
- Stage 13 HTTP and MCP smoke harnesses.

Acceptance:

- `SCN-003` unsafe path through Amazon HTTP fails with
  `amazon_no_promise_from_stale_inventory_summary`,
  `reservation_required_before_promise`, and `no_oversell`.
- `SCN-003` safe path through Amazon HTTP passes when the agent reads live
  listing availability and routes unavailable stock to manual review.
- `SCN-005` unsafe path through Amazon HTTP fails with
  `amazon_no_confirm_shipment_after_buyer_cancel_without_review`,
  `warehouse_conflict_requires_hold`, and `no_ship_after_cancel`.
- `SCN-005` safe path through Amazon HTTP passes when the agent holds the
  workflow and requests warehouse cancellation before confirming shipment.
- Feed submission returns a processing report after polling `getFeed`.
- Rate-limited Amazon-shaped calls return retryable 429 metadata and can be
  retried successfully.
- Unsupported Amazon-shaped notifications/actions return explicit stub coverage
  metadata rather than pretending to be full SP-API coverage.
- `confirmShipment` after buyer cancellation emits trace details showing the
  prior cancellation signal, warehouse status, and risk signal.
- Real MCP smoke proves Amazon tools can drive at least one unsafe and one safe
  Amazon-shaped path through the official MCP server.
- The skin remains an adapter: it maps Amazon-shaped requests to normalized
  commerce actions/events and does not perform business policy decisions.
- No LWA/SigV4 auth, real Amazon sandbox integration, full Orders API, full
  Feeds document flow, Reports API, FBA inbound, returns/refunds, or marketplace
  matrix is introduced.

Gate:

```bash
python -m pytest tests/test_amazon_mcp_server_contract.py tests/test_amazon_skin_manifests.py tests/test_amazon_binding.py tests/test_amazon_skin_live_http.py tests/test_amazon_skin_mcp_tools.py
./tools/smoke_stage13_amazon_skin_v0.sh
PYTHON=python3.12 ./tools/smoke_stage13_amazon_mcp_v0.sh
```

## Stage 14: Productionization Gate

Goal: harden the local live-agent surface without adding new platform skins.

Deliverables:

- Scenario registry and path allowlist.
- Local API token support for HTTP live server.
- Session-scoped Amazon feed store.
- Per-session locking around live tool execution.
- Unified HTTP protocol error envelope.
- Python version preflight for MCP/API gates.
- Named, tighter Amazon OpenAPI response schemas.
- Source PR vs generated artifacts PR guidance.

Gate:

```bash
python -m pytest tests/test_stage14_productionization.py tests/test_openapi_contract_shape.py
PYTHON=python3.12 ./tools/smoke_stage9_api_hardening.sh
PYTHON=python3.12 ./tools/smoke_stage11_openapi_contract.sh
```

## Stage 15: Release Hygiene + CI Gate

Goal: make V3.5 reviewable by an outside engineer and runnable in CI without
mixing runtime source changes with generated demo collateral.

Deliverables:

- `release_hygiene.yaml` source/generated PR manifest.
- `tools/check_release_hygiene.py` local path and PR split checker.
- `tools/smoke_stage15_release_hygiene.sh`.
- `.github/workflows/v35-ci.yml`.
- Pinned CI dependencies in `requirements.txt`.
- Stage 15 documentation.

Acceptance:

- Source PR paths are separate from generated artifact paths.
- Local machine paths fail the hygiene gate.
- Generated artifacts such as `demo_pack/`, `demo_viewer/`,
  `failure_intelligence/`, and runtime outputs are documented as a separate PR.
- GitHub Actions runs release hygiene, unit tests, MCP/HTTP/OpenAPI gates, and
  Shopify/Amazon skin gates.
- The full V3.5 gate includes Stage 15.

Gate:

```bash
python -m pytest tests/test_stage15_release_hygiene.py
PYTHON=python3.12 ./tools/smoke_stage15_release_hygiene.sh
```

## Stage 16: Security / Abuse Hardening

Goal: harden the local HTTP/MCP/action-log surface against accidental exposure,
abuse, and sensitive-data leakage while preserving `Permissive Twin + Policy
Check`.

Deliverables:

- Repository-scoped threat model for the V3.5 agent-facing surfaces.
- Non-loopback HTTP bind protection unless an API token is configured.
- Constant-time local token comparison.
- Bounded HTTP JSON request bodies.
- No-store and nosniff HTTP response headers.
- Agent-facing scenario path errors that do not leak local filesystem paths.
- Bounded JSONL action logs.
- `security_hardening.yaml` source scan config for high-confidence secret
  patterns and banned response fragments.
- `tools/check_security_hardening.py`.
- `tools/smoke_stage16_security_abuse.sh`.
- Stage 16 tests and documentation.

Acceptance:

- `0.0.0.0` or other non-loopback HTTP binds without a token fail before socket
  binding.
- Loopback HTTP binds still work without a token for local demos.
- Token-protected HTTP requests still pass with the correct token and reject
  the wrong token.
- Oversized JSON request bodies and action logs fail with explicit errors.
- Source scanning rejects high-confidence live secret patterns and wildcard
  CORS response fragments.
- Stage 16 is included in CI and the full V3.5 release gate.
- The twin remains permissive; Stage 16 must not turn business policy failures
  into early API validation rejects.

Gate:

```bash
python -m pytest tests/test_stage16_security_abuse.py
PYTHON=python3.12 ./tools/smoke_stage16_security_abuse.sh
```

## Stage 17: Run Manifest + Artifact Schema Versioning

Goal: make every generated run artifact consumable by CI, external agents, and
future hosted sessions without guessing schema shape or artifact integrity.

Deliverables:

- `run_manifest.json` for CLI and live-session runs.
- Artifact schema ids for `trace.json`, `policy_report.json`,
  `state_diff.json`, and `patch_hints.json`.
- Manifest entries for markdown artifacts with content type, bytes, and SHA-256.
- `commerce_safety.artifacts` module with manifest writer and validator.
- `tools/check_run_manifest.py`.
- `tools/smoke_stage17_run_manifest.sh`.
- Stage 17 tests and documentation.

Acceptance:

- CLI `run` writes `run_manifest.json`.
- Live `complete_session` writes `run_manifest.json` including repair artifacts.
- JSON artifacts carry stable `schema_version` values.
- Manifest validation checks file existence, byte size, SHA-256, and JSON
  schema version agreement.
- Tampered artifacts fail manifest validation.
- Stage 17 is included in CI and the full V3.5 release gate.
- The twin remains permissive; Stage 17 only contracts artifacts and does not
  reject unsafe commerce actions early.

Gate:

```bash
python -m pytest tests/test_stage17_run_manifest.py
PYTHON=python3.12 ./tools/smoke_stage17_run_manifest.sh
```

## Stage 18: Agent Integration Examples

Goal: turn the V3.5 live surfaces into self-serve external-agent examples.

Deliverables:

- Runnable MCP example for `SCN-002 timeout_after_commit_retry`.
- Runnable HTTP Twin API example for `SCN-002 timeout_after_commit_retry`.
- Committed action-log fixtures for `SCN-004 refund_after_shipment_bypass`.
- `examples/agent_integrations/README.md`.
- `docs/STAGE18_AGENT_INTEGRATION_EXAMPLES.md`.
- `tools/smoke_stage18_agent_examples.sh`.
- Stage 18 tests.

Acceptance:

- MCP unsafe path fails with `idempotency_required_for_mutating_retries` and
  `no_duplicate_fulfillment`.
- MCP safe path passes with zero findings.
- HTTP unsafe path fails with the same SCN-002 policy findings.
- HTTP safe path passes with zero findings.
- Action-log unsafe path exits `1` and finds refund-after-shipment approval
  violations.
- Action-log safe path exits `0`.
- All example-generated run paths pass manifest validation.
- Examples remain local-only and do not include production platform
  credentials.

Gate:

```bash
python -m pytest tests/test_stage18_agent_integration_examples.py
PYTHON=python3.12 ./tools/smoke_stage18_agent_examples.sh
```

## Stage 19: Hosted Design Partner Trust Gate

Goal: make the hosted commerce agent sandbox safe enough for 1-3 design
partners to connect staging agents/workflows to MCP/HTTP without giving us
production store access.

Subtitle:

```txt
Design Partner Trust Boundary, not SOC2 certification.
```

Non-goals:

- Full SOC2 certification.
- Full enterprise SaaS.
- SSO/SAML.
- Billing.
- VPC deployment.
- Firecracker/gVisor.
- Hosted dashboard polish.
- New platform skins.

Deliverables:

- Workspace and tenant boundary.
- API token auth.
- Minimal RBAC with `owner`, `operator`, `viewer`, and `agent_token`.
- Token scopes for sessions, twin/MCP calls, reports, artifacts, workspace
  export/delete, token management, and audit reads.
- Per-session run storage with workspace/session/retention metadata.
- Signed artifact download URLs.
- Audit log for token, session, twin action, policy report, artifact, export,
  delete, auth failure, authorization denial, rate limit, PII, and secret events.
- Request size limits.
- Rate limits.
- Session TTL.
- Artifact retention metadata.
- Lightweight PII/secret warnings.
- Workspace suspend and token revoke kill switch.
- Workspace export and deletion receipt.
- POC Security Evidence Binder under `docs/security/`.
- Hosted P0 validation for MCP and HTTP paths.

Acceptance:

- No token, invalid token, expired token, and revoked token return `401`.
- Wrong scope returns `403`.
- Viewer cannot create a session.
- Agent token cannot export workspace data.
- Workspace A cannot read, complete, or download artifacts from workspace B.
- Guessing a session id does not bypass object-level authorization.
- `run_manifest.json` includes `workspace_id`, `session_id`, and retention metadata.
- Artifact entries include SHA-256.
- Signed artifact URL expires.
- Artifact access is audited.
- Oversized request is rejected.
- Rate limit triggers.
- Session TTL blocks late writes.
- PII/secret warning is generated.
- Workspace export works.
- Workspace deletion produces a deletion receipt.
- All five P0 scenarios still work through hosted MCP and hosted HTTP paths.

Gate:

```bash
PYTHON=python3.12 ./tools/smoke_stage19_release_candidate.sh
PYTHON=python3.12 ./tools/smoke_stage19_hosted_enterprise_poc.sh
```

Sub-gates:

```bash
PYTHON=python3.12 ./tools/smoke_stage19_auth_rbac.sh
PYTHON=python3.12 ./tools/smoke_stage19_tenant_isolation.sh
PYTHON=python3.12 ./tools/smoke_stage19_artifacts_audit.sh
PYTHON=python3.12 ./tools/smoke_stage19_limits_redaction.sh
PYTHON=python3.12 ./tools/smoke_stage19_p0_hosted_live.sh
```

Stop line:

After Stage 19 passes, stop platform engineering and move to 1-3 design
partners, real staging-agent/workflow integrations, incident feedback, and paid
POC validation.

## Full V3.5 Gate

Once Stage 19 is implemented, the V3.5 release gate is:

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
- Stage 10 full P0 MCP/HTTP coverage gates.
- Stage 11 strict OpenAPI contract gate.
- Stage 12 Shopify-like skin V0 gate.
- Stage 13 Amazon Seller Ops skin V0 gates.
- Stage 15 release hygiene + CI gate.
- Stage 16 security / abuse hardening gate.
- Stage 17 run manifest + artifact schema versioning gate.
- Stage 18 agent integration examples gate.
