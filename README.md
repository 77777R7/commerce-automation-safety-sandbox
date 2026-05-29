# Commerce Automation Safety Sandbox

V3.5 work is now focused on a Live Agent Sandbox for commerce automation and AI
agents.

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

## Current MVP

The current P0 demo covers five flagship commerce accidents:

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

## Quickstart

```bash
git clone https://github.com/77777R7/commerce-automation-safety-sandbox.git
cd commerce-automation-safety-sandbox

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

chmod +x commerce-safety tools/*.sh
./tools/smoke_all.sh
```

Run the unit tests directly:

```bash
python -m pytest
```

## Main Commands

```bash
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

Future V3.5 release gate:

```bash
./tools/smoke_v35.sh
```

## Demo And POC Materials

- [Static demo viewer](demo_viewer/index.html)
- [Demo pack guide](demo_pack/README.md)
- [Executive summary](demo_pack/executive_summary.md)
- [Sales one-pager](demo_pack/sales_one_pager.md)
- [Demo walkthrough](demo_pack/demo_walkthrough.md)
- [Demo/POC readiness](docs/DEMO_POC_READINESS.md)
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
- The current repo is not a full Shopify sandbox, Amazon emulator, API server,
  PR check platform, or buyer red-team product.
- The current repo has not yet completed the V3.5 live HTTP/MCP agent sandbox;
  see [ROADMAP.md](ROADMAP.md) for the staged gates.

## Source Of Truth

- Product roadmap: [ROADMAP.md](ROADMAP.md)
- MVP acceptance contract: [MVP_ACCEPTANCE.md](MVP_ACCEPTANCE.md)
- P0 scenario library: [SCENARIO_LIBRARY.md](SCENARIO_LIBRARY.md)
- Agent operating instructions: [AGENTS.md](AGENTS.md)
