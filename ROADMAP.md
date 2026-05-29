# Commerce Automation Safety Sandbox Roadmap

This roadmap keeps the MVP focused on the incident-validation core before any
platform work.

## Product Direction

Build one commerce automation incident validation core with two future
entrypoints:

- `Offline Fulfillment Automation Audit` for seller/operator POCs.
- `Live Commerce Agent Validation` for agents, workflows, and SaaS builders.

The current repo is only implementing the Week 1 incident core demo.

## Non-Goals For The Current Lane

Do not build these yet:

- UI or dashboard.
- API server.
- GitHub App or PR check.
- MCP server.
- Offline Audit importer/reporting.
- Full Shopify GraphQL skin.
- Full Amazon SP-API subset.
- Egress proxy.
- Agent container.
- Browser runner.
- LLM buyer simulator.

## Stage 0: Lock The Current Slice

Goal: make `duplicate_webhook -> duplicate_fulfillment` a non-regression
baseline.

Scope:

- Preserve the permissive twin pattern: unsafe mutations are allowed first,
  then policies catch the incident.
- Keep one shared scenario:
  `commerce-safety-sandbox/scenarios/duplicate_webhook.yaml`.
- Under that same scenario, `bad_runner` must fail and `good_runner` must pass.
- `bad_runner` must exit non-zero by default when policy findings exist.
- `good_runner` must exit zero.
- Replay must read from `trace.json`, not rerun the scenario.
- Run artifacts must include `trace.json`, `policy_report.json`,
  `state_diff.json`, and `report.md`.

Completion line:

```bash
./tools/smoke_week1.sh
```

## Stage 1: Finish Week 1 Flagship Scenarios

Goal: prove the incident core across five deep scenarios before adding platform
surface area.

Canonical scenario library:

- See `SCENARIO_LIBRARY.md`.
- Do not add a sixth P0 flagship scenario.
- Tracking timing, SKU mapping, timezone, and null discount issues are P1.
- Each P0 scenario should tell one main accident.

Scenario order:

1. `SCN-001 duplicate_webhook_fulfillment` - done as the baseline slice.
2. `SCN-002 timeout_after_commit_retry` - implemented.
3. `SCN-003 stale_inventory_oversell` - implemented.
4. `SCN-004 refund_after_shipment_bypass` - implemented.
5. `SCN-005 cancel_after_pick_pack_conflict` - implemented.

Each scenario must have:

- One scenario YAML.
- `bad_runner` failure.
- `good_runner` pass.
- Permissive twin mutation before policy evaluation.
- Structured `PolicyFinding`.
- Trace-based replay.
- `trace.json`, `policy_report.json`, `state_diff.json`, and `report.md`.

## Stage 2: Make Reports Demo-Ready

Goal: make the output understandable without reading code.

Add or tighten:

- Boss-readable executive summary.
- Business impact language.
- Recommended fixes.
- Clear state change section.
- Good-run explanation.
- Demo pack with failing and passing reports for all five scenarios.

Completion line:

```bash
./tools/smoke_week1.sh
ls demo_pack/
```

## Stage 3: Regression Scenario Library

Goal: start turning failures into reusable test assets.

Minimal feature:

```bash
./commerce-safety save-regression runs/<run_id> --name <name>
```

Expected output:

```txt
regressions/<name>/
  scenario.yaml
  trace.json
  policy_report.json
  state_diff.json
  summary.md
```

Rules:

- Only failed runs with policy findings can be saved.
- New runs preserve their source `scenario.yaml` inside the run directory.
- `summary.md` must explain the incident, findings, saved artifacts, and future
  regression gate in non-engineering language.

Completion line:

```bash
./tools/smoke_stage3_regression.sh
```

## Stage 3.5: Failure Intelligence Scenario Expansion

Goal: keep expanding the scenario library without destabilizing the five P0
flagship scenarios.

Inputs:

- `outputs/failure_intelligence/reddit_p0_deep_extract_20260528/approved_scenarios.jsonl`
- `outputs/failure_intelligence/reddit_p0_deep_extract_20260528/policy_candidates.jsonl`
- `SCENARIO_LIBRARY.md`

Rules:

- Do not add a sixth P0 scenario.
- New approved scenarios should enter P1 packs first.
- Prefer packs that support both entrypoints:
  `Offline Fulfillment Automation Audit` and `Live Commerce Agent Validation`.
- Track whether a new approved scenario is:
  - already covered by an existing P0 scenario,
  - a P1 variant of an existing P0 scenario,
  - a genuinely new P1 pack.

Current approved P1 packs:

- Tracking visibility and first carrier scan.
- Webhook reliability and reconciliation.
- Multichannel inventory authority.
- WMS and bundle mapping.
- Cancel window between label creation and warehouse processing.

Do this in parallel with Demo Pack work only as documentation and backlog
curation. Do not implement new engine behavior until the demo pack is readable
and the five P0 scenarios are stable.

## Stage 4: Offline Fulfillment Automation Audit

Goal: open the first commercial entrypoint.

Inputs:

- `orders.csv`
- `inventory.csv`
- `fulfillments.csv`
- `refunds.csv`

Capabilities:

- Manual schema mapping.
- PII redaction.
- Data quality profiling.
- State reconstruction.
- Offline risk report.

Current v0 scope:

- CSV and XLSX importer.
- Optional YAML mapping from canonical fields to customer export headers.
- Optional worksheet selection for XLSX inputs.
- Redacted canonical copies of input files.
- Boss-readable markdown report.
- Structured JSON artifacts for future workflow integration.

Expected output:

```txt
offline_audits/<audit_id>/
  manifest.json
  data_quality.json
  state_reconstruction.json
  policy_report.json
  report.md
  redacted_inputs/
    orders.csv
    inventory.csv
    fulfillments.csv
    refunds.csv
```

Completion line:

```bash
./tools/smoke_stage4_offline_audit.sh
./tools/smoke_stage4_offline_audit_xlsx.sh
./tools/smoke_stage4_offline_audit_clean.sh
```

Deferred Stage 4 hardening:

- Richer customer-like ERP export fixtures.
- Financial impact estimates by shipping cost, refund amount, and inventory cost.
- More mapping presets for common Shopify/ERP/OMS column names.
- Optional multi-file audit bundle packaging for POC delivery.

## Stage 5: Demo / POC Polish

Goal: turn the working MVP into a repeatable sales and POC package.

Scope:

- Keep one repo entrypoint in `README.md`.
- Keep one full verification gate: `./tools/smoke_all.sh`.
- Keep `demo_pack/` readable as a standalone sales artifact.
- Add sales materials:
  - `demo_pack/sales_one_pager.md`
  - `demo_pack/demo_walkthrough.md`
- Add POC operating docs:
  - `docs/DEMO_POC_READINESS.md`
  - `docs/OFFLINE_AUDIT_POC_PLAYBOOK.md`
- Keep generated/runtime artifacts ignored:
  - `runs/`
  - `offline_audits/`
  - `regressions/`
  - `demo_pack/_generated_runs/`
  - `outputs/`

Completion line:

```bash
./tools/smoke_all.sh
```
