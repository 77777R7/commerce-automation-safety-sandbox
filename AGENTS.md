# Global Codex Operating Instructions

Before non-trivial work for Howard, read and apply this experience playbook:

`/Users/howard07/.codex/agent_docs/codex-operating-experience-playbook.md`

It contains the reusable execution lessons, product/UI preferences, and behavior rules distilled from prior Codex conversations and execution logs. Keep this file as a stable pointer rather than duplicating the full document here.

The same operating memory is also packaged as callable Codex skills:

- `$howard-operating-playbook`
- `$howard-execution-guardrails`
- `$howard-product-style-profile`
- `$howard-skill-distiller`

# Commerce Automation Safety Sandbox MVP

Current source of truth:

- Persistent strategy note: `/Users/howard07/.codex/memories/extensions/ad_hoc/notes/20260528T022459-0700-commerce-automation-safety-sandbox-final.md`
- MVP code root: `commerce-safety-sandbox/`
- CLI wrapper: `commerce-safety`

Current implementation lane:

- Strictly Week 1 Incident Core Demo.
- CLI-first only.
- No UI, API server, GitHub App, PR check, MCP, Offline Audit, full Shopify/Amazon skin, egress proxy, agent container, browser runner, or LLM buyer simulator yet.

Hard MVP principles:

- Use a permissive twin: unsafe actions are allowed to mutate state, then Policy Engine catches the business incident.
- Same scenario must prove both paths: `bad_runner` fails and `good_runner` passes under `commerce-safety-sandbox/scenarios/duplicate_webhook.yaml`.
- The P0 scenario library has exactly five flagship scenarios: `SCN-001 duplicate_webhook_fulfillment`, `SCN-002 timeout_after_commit_retry`, `SCN-003 stale_inventory_oversell`, `SCN-004 refund_after_shipment_bypass`, and `SCN-005 cancel_after_pick_pack_conflict`.
- Do not add a sixth P0 scenario. Tracking timing, SKU mapping, timezone, null discount, and similar cases are P1.
- Each P0 scenario should tell one main accident with one clean primary policy.
- CLI runs must exit non-zero when any policy finding is produced, so the MVP can become a CI/gate later.
- Replay must read from `trace.json`; it must not rerun the scenario.
- `PolicyFinding` must stay structured with `policy_id`, `severity`, `status`, `evidence`, `business_impact`, and `recommendation`.
- Inventory accident signals must compare reserved inventory to expected order quantity, not use a naive `reserved > 1` check.
- Duplicate webhook policy should evolve toward duplicate side effects generally, not only duplicate fulfillment. The current slice should at least consider reservation and fulfillment side effects.
- Run artifacts must include `trace.json`, `policy_report.json`, `state_diff.json`, and `report.md`.
- Stage 3 regression capture must save failed runs with policy findings into `regressions/<slug>/` with `scenario.yaml`, `trace.json`, `policy_report.json`, `state_diff.json`, and `summary.md`.
- Stage 4 Offline Audit v0 imports CSV or XLSX tables for orders, inventory, fulfillments, and refunds; support optional YAML schema mapping and worksheet selection; redact buyer identifiers; output `manifest.json`, `data_quality.json`, `state_reconstruction.json`, `policy_report.json`, `report.md`, and `redacted_inputs/*.csv`.

Current completion line:

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
