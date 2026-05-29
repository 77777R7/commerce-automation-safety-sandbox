# Commerce Automation Safety Sandbox MVP

Week 1 vertical slice for `duplicate_webhook -> duplicate_fulfillment`.

The twin is intentionally permissive: unsafe mutations are allowed to happen, and
the policy engine detects the business incident after state changes are recorded.

## Commands

```bash
./commerce-safety run commerce-safety-sandbox/scenarios/duplicate_webhook.yaml --runner bad_runner
./commerce-safety run commerce-safety-sandbox/scenarios/duplicate_webhook.yaml --runner good_runner
./commerce-safety run commerce-safety-sandbox/scenarios/SCN-002_timeout_after_commit_retry.yaml --runner bad_runner
./commerce-safety run commerce-safety-sandbox/scenarios/SCN-002_timeout_after_commit_retry.yaml --runner good_runner
./commerce-safety run commerce-safety-sandbox/scenarios/SCN-003_stale_inventory_oversell.yaml --runner bad_runner
./commerce-safety run commerce-safety-sandbox/scenarios/SCN-003_stale_inventory_oversell.yaml --runner good_runner
./commerce-safety run commerce-safety-sandbox/scenarios/SCN-004_refund_after_shipment_bypass.yaml --runner bad_runner
./commerce-safety run commerce-safety-sandbox/scenarios/SCN-004_refund_after_shipment_bypass.yaml --runner good_runner
./commerce-safety run commerce-safety-sandbox/scenarios/SCN-005_cancel_after_pick_pack_conflict.yaml --runner bad_runner
./commerce-safety run commerce-safety-sandbox/scenarios/SCN-005_cancel_after_pick_pack_conflict.yaml --runner good_runner
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

`save-regression` only accepts failed runs with policy findings. It writes a
reusable regression asset to `regressions/<slug>/` with the source scenario,
trace, policy report, state diff, and a boss-readable summary.

## Smoke Gates

```bash
./tools/smoke_week1.sh
./tools/smoke_scn002.sh
./tools/smoke_scn003.sh
./tools/smoke_scn004.sh
./tools/smoke_scn005.sh
./tools/smoke_stage3_regression.sh
./tools/smoke_stage4_offline_audit.sh
./tools/smoke_stage4_offline_audit_xlsx.sh
./tools/smoke_stage4_offline_audit_clean.sh
```

## Offline Audit v0

The Stage 4 Offline Fulfillment Automation Audit accepts CSV and XLSX seller or
ERP exports. It applies an optional YAML schema mapping, can select worksheets
for XLSX workbooks, writes redacted canonical inputs, reconstructs commerce
state, runs offline policy checks, and generates a markdown report for
operators.

Output:

```txt
offline_audits/<audit_id>/
  manifest.json
  data_quality.json
  state_reconstruction.json
  policy_report.json
  report.md
  redacted_inputs/
```
