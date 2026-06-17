# Agent Integration Safety Sandbox

This repository is being rebaselined from `Commerce Automation Safety Sandbox`
to a SaaS agent validation sandbox for stateful integrations.

The V0 product direction is:

```txt
Stripe + Slack + GitHub agent validation
```

We test AI agents and automation workflows against stateful Stripe, Slack, and
GitHub twins before they touch production billing, notifications, or PR checks.
The existing commerce implementation remains as the legacy foundation while the
SaaS twin bundle is introduced.

The product principle is:

```txt
Permissive Twin + Policy Check
```

The twin allows unsafe automation to mutate state first. The policy engine then
detects the business incident from trace, state diff, and structured policy
findings. This is what makes the demo feel like an accident sandbox instead of
a normal API validator.

V3.5 mainline:

```txt
External Agent -> MCP/HTTP Twin -> Scenario Fault -> Policy Finding -> Patch Hints
```

MCP is not optional for V3.5. HTTP Twin API and action-log replay are also
required surfaces, but MCP is the native interface for Codex, Claude, and other
agent builders. `Offline Fulfillment Automation Audit` remains as a supporting
entrypoint, not the mainline.

## SaaS V0 Boundary

Only these twins are V0 mainline:

- `StripeTwin`: billing state, subscriptions, invoices, payment intents,
  refunds, and webhook delivery/retry state.
- `SlackTwin`: workspace/channel/message state, bot membership, permission
  failures, and incident/support alert delivery.
- `GitHubTwin`: repository, pull request, check run, issue, and PR comment
  state.

Shopify, Amazon, fulfillment, warehouse, and inventory flows are now legacy
commerce surfaces. They can stay in tests and demos as regression coverage, but
they are no longer the product direction.

Scenario policy boundaries are explicit:

- SaaS validation scenarios use `policy_packs: [saas_billing_v0]`.
- Legacy commerce scenarios use `policy_packs: [legacy_commerce]`.
- The policy engine must not mix SaaS and legacy findings for a scenario-backed
  live session.

## Current MVP

The current P0 demo covers five legacy commerce accidents:

- `SCN-001 duplicate_webhook_fulfillment`
- `SCN-002 timeout_after_commit_retry`
- `SCN-003 stale_inventory_oversell`
- `SCN-004 refund_after_shipment_bypass`
- `SCN-005 cancel_after_pick_pack_conflict`

For every scenario, the same scenario YAML drives both paths:

- `bad_runner` creates the accident and exits non-zero.
- `good_runner` passes with zero findings.

Each run writes:

- `trace.json`
- `policy_report.json`
- `state_diff.json`
- `report.md`
- `patch_hints.json`
- `run_manifest.json`

SaaS validation runs must preserve the same artifact loop and add
agent-readable repair output rather than replacing it.

## SaaS V0 Hero Path

The first SaaS cross-service demo is:

- `SAAS-001 failed_payment_success_notification`

It runs against stateful Stripe, Slack, and GitHub twins. The unsafe path
creates a failed Stripe payment, misses the Slack billing failure alert, and
still publishes success state. The safe path delivers the billing alert and
keeps GitHub in a non-success review state.

SAAS-001 is exposed through the agent-facing surfaces:

- MCP: `stripe.create_customer`, `stripe.create_subscription`,
  `slack.post_message`, `github.create_check_run`, `github.create_issue`, and
  `github.comment_on_pr`.
- HTTP: `POST /sessions/{session_id}/twin/stripe_create_customer`,
  `stripe_create_subscription`, `slack_post_message`,
  `github_create_check_run`, `github_create_issue`, and
  `github_comment_on_pr`.

## Quickstart

```bash
git clone https://github.com/77777R7/commerce-automation-safety-sandbox.git
cd commerce-automation-safety-sandbox

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

chmod +x commerce-safety tools/*.sh
./commerce-safety doctor
./tools/smoke_all.sh
```

Run the unit tests directly:

```bash
python -m pytest
```

## Main Commands

```bash
./commerce-safety doctor
./commerce-safety mcp-config --python "$PWD/.venv/bin/python"
./commerce-safety demo saas001-agent --python "$PWD/.venv/bin/python"
./commerce-safety demo scn002-agent --python "$PWD/.venv/bin/python"
./commerce-safety init --path saas-mcp-agent
./commerce-safety init --path saas-http-workflow
./commerce-safety init --path n8n
./commerce-safety run commerce-safety-sandbox/scenarios/duplicate_webhook.yaml --runner bad_runner
./commerce-safety run commerce-safety-sandbox/scenarios/duplicate_webhook.yaml --runner good_runner
./commerce-safety replay runs/<run_id>
./commerce-safety report runs/<run_id> --format markdown
./commerce-safety save-regression runs/<run_id> --name "Timeout Retry Regression"
./commerce-safety offline-audit \
  --orders commerce-safety-sandbox/offline_samples/p0_audit/orders.csv \
  --inventory commerce-safety-sandbox/offline_samples/p0_audit/inventory.csv \
  --fulfillments commerce-safety-sandbox/offline_samples/p0_audit/fulfillments.csv \
  --refunds commerce-safety-sandbox/offline_samples/p0_audit/refunds.csv \
  --mapping commerce-safety-sandbox/offline_samples/p0_audit/mapping.yaml
```

## One Smoke Gate

```bash
./tools/smoke_all.sh
```

This runs unit tests, all current P0 scenario checks, regression capture,
Offline Audit CSV and XLSX checks, clean audit check, and demo pack
verification.

Stage 0 rebaseline gate:

```bash
./tools/smoke_stage0_rebaseline.sh
```

V3.5 live sandbox gate:

```bash
./tools/smoke_v35.sh
```

Stage 9-11 real MCP/API hardening gates require Python 3.10+ because the
official MCP SDK and Schemathesis gates run there. Stage 12/13 Shopify and
Amazon gates are legacy commerce regression gates, not the new mainline:

```bash
PYTHON=python3.12 ./tools/smoke_stage9_real_mcp.sh
PYTHON=python3.12 ./tools/smoke_stage9_api_hardening.sh
PYTHON=python3.12 ./tools/smoke_stage10_mcp_p0_all.sh
PYTHON=python3.12 ./tools/smoke_stage10_http_p0_all.sh
PYTHON=python3.12 ./tools/smoke_stage11_openapi_contract.sh
./tools/smoke_stage12_shopify_skin_v0.sh
./tools/smoke_stage13_amazon_skin_v0.sh
PYTHON=python3.12 ./tools/smoke_stage13_amazon_mcp_v0.sh
PYTHON=python3.12 ./tools/smoke_stage18_agent_examples.sh
```

## Demo And POC Materials

- [SAAS-001 Stripe/Slack/GitHub demo pack](demo_pack/saas_agent_validation/README.md)
- [SAAS-001 MCP agent test prompt](demo_pack/prompts/saas001_mcp_agent_test.md)
- [SAAS-001 HTTP agent example](examples/agent_integrations/http_saas001_failed_payment_agent.py)
- [SAAS-001 MCP agent example](examples/agent_integrations/mcp_saas001_failed_payment_agent.py)
- [Static demo viewer](demo_viewer/index.html)
- [Design Partner POC package](docs/design_partner_poc/README.md)
- [External tester quickstart](docs/QUICKSTART_EXTERNAL_TESTER.md)
- [HTTP and n8n quickstart](docs/HTTP_N8N_QUICKSTART.md)
- [Importable n8n SCN-002 workflow](demo_pack/n8n/scn002_timeout_retry_unsafe_safe.json)
- [SCN-002 MCP agent test prompt](demo_pack/prompts/scn002_mcp_agent_test.md)
- [Demo pack guide](demo_pack/README.md)
- [Executive summary](demo_pack/executive_summary.md)
- [Sales one-pager](demo_pack/sales_one_pager.md)
- [Demo walkthrough](demo_pack/demo_walkthrough.md)
- [Demo/POC readiness](docs/DEMO_POC_READINESS.md)
- [MCP server setup](docs/MCP_SERVER_SETUP.md)
- [Live Twin OpenAPI spec](docs/openapi/live_twin_api.yaml)
- [Shopify-like skin V0](docs/SHOPIFY_LIKE_SKIN_V0.md)
- [Amazon Seller Ops skin V0](docs/AMAZON_SELLER_OPS_SKIN_V0.md)
- [Agent integration examples](examples/agent_integrations/README.md)
- [Stage 18 agent integration examples](docs/STAGE18_AGENT_INTEGRATION_EXAMPLES.md)
- [Stage 19 hosted design-partner trust gate](docs/STAGE19_HOSTED_DESIGN_PARTNER_TRUST_GATE.md)
- [Stage 19 release candidate](docs/STAGE19_RELEASE_CANDIDATE.md)
- [Stage 19 PR description](docs/PR_STAGE19_DESCRIPTION.md)
- [Hosted design-partner onboarding](docs/HOSTED_DESIGN_PARTNER_ONBOARDING.md)
- [POC security evidence binder](docs/security/SECURITY_OVERVIEW.md)
- [Stage 12 PR readiness](docs/STAGE12_PR_READINESS.md)
- [Offline Audit POC playbook](docs/OFFLINE_AUDIT_POC_PLAYBOOK.md)
- [POC input templates](poc_templates/)

Open the static demo viewer locally:

```bash
open demo_viewer/index.html
```

## Known Issues / Current Limits

- Offline Audit v0 expects four canonical export tables: orders, inventory,
  fulfillments, and refunds.
- Real customer exports still require schema mapping when column names differ
  from the canonical fields.
- PII redaction currently applies only to the canonical `buyer_id` field.
- Customers should not provide email, phone, address, customer name, shipping
  address, billing address, or free-form customer notes in the first POC.
- SaaS POC mode must not use production Stripe keys, production Slack bot
  tokens, production GitHub installation tokens, customer PII, real refunds, or
  real PR writes unless an explicit future integration mode enables them.
- The current repo is not a full Shopify sandbox, Amazon emulator, full hosted
  enterprise SaaS, or buyer red-team product. Stage 19 is a hosted
  design-partner trust boundary only.
- Real MCP server and strict OpenAPI hardening support require Python 3.10+.
  The core CLI and legacy MVP tests still run under the older system Python
  used by this local workspace.
- V3.5 now has live HTTP, real MCP, action-log, and repair-artifact gates; see
  [ROADMAP.md](ROADMAP.md) for the staged boundaries.

## Source Of Truth

- Product roadmap: [ROADMAP.md](ROADMAP.md)
- MVP acceptance contract: [MVP_ACCEPTANCE.md](MVP_ACCEPTANCE.md)
- P0 scenario library: [SCENARIO_LIBRARY.md](SCENARIO_LIBRARY.md)
- Agent operating instructions: [AGENTS.md](AGENTS.md)
