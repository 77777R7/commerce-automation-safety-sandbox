# Commerce Automation Safety Sandbox

CLI-first MVP for a commerce automation incident validation core.

The product principle is:

```txt
Permissive Twin + Policy Check
```

The twin allows unsafe automation to mutate state first. The policy engine then
detects the business incident from trace, state diff, and structured policy
findings. This is what makes the demo feel like an accident sandbox instead of
a normal API validator.

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

This runs all current P0 scenario checks, regression capture, Offline Audit CSV
and XLSX checks, clean audit check, and demo pack verification.

## Demo And POC Materials

- [Demo pack guide](demo_pack/README.md)
- [Executive summary](demo_pack/executive_summary.md)
- [Sales one-pager](demo_pack/sales_one_pager.md)
- [Demo walkthrough](demo_pack/demo_walkthrough.md)
- [Demo/POC readiness](docs/DEMO_POC_READINESS.md)
- [Offline Audit POC playbook](docs/OFFLINE_AUDIT_POC_PLAYBOOK.md)

## Source Of Truth

- Product roadmap: [ROADMAP.md](ROADMAP.md)
- MVP acceptance contract: [MVP_ACCEPTANCE.md](MVP_ACCEPTANCE.md)
- P0 scenario library: [SCENARIO_LIBRARY.md](SCENARIO_LIBRARY.md)
- Agent operating instructions: [AGENTS.md](AGENTS.md)
