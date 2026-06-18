# Artifact And Report Examples

Every completed run produces machine-readable artifacts and a human-readable
report. These artifacts are designed for operators, engineers, and AI coding
agents.

## Run Folder

Typical run output:

```txt
runs/<session_id>/
  scenario.yaml
  trace.json
  policy_report.json
  state_diff.json
  report.md
  patch_hints.json
  patch_hints.md
  agent_summary.md
  failure_explain.md
  run_manifest.json
```

Standalone sample excerpts are included under `samples/`:

- `samples/trace_excerpt.json`
- `samples/policy_report_excerpt.json`
- `samples/state_diff_excerpt.json`
- `samples/report_excerpt.md`

## trace.json

Purpose:

- Shows what happened, step by step.
- Lets an engineer or agent replay the accident timeline.

Example excerpt:

```json
{
  "scenario_id": "SCN-002",
  "status": "failed",
  "timeline": [
    {
      "actor": "scenario",
      "event": "fulfillment_task_received",
      "message": "Agent received fulfillment task for order_2001."
    },
    {
      "actor": "external_agent",
      "event": "fulfillment_created",
      "message": "Fulfillment committed before timeout."
    },
    {
      "actor": "external_agent",
      "event": "fulfillment_created",
      "message": "Unsafe retry created a second fulfillment."
    },
    {
      "actor": "policy_engine",
      "event": "policy_violation_detected",
      "message": "Policy violation detected: no_duplicate_fulfillment."
    }
  ]
}
```

## policy_report.json

Purpose:

- Gives structured policy findings.
- Safe for CI gates and agent-readable repair loops.

Example excerpt:

```json
{
  "scenario_id": "SCN-002",
  "status": "failed",
  "findings": [
    {
      "policy_id": "idempotency_required_for_mutating_retries",
      "severity": "critical",
      "status": "failed",
      "evidence": {
        "action": "create_fulfillment",
        "retry_count": 2,
        "idempotency_key": null
      },
      "business_impact": "The workflow may duplicate fulfillment after an ambiguous timeout.",
      "recommendation": "Use a stable idempotency key and query existing fulfillment state before retrying."
    }
  ]
}
```

## state_diff.json

Purpose:

- Shows how commerce state changed.
- Makes the accident visible without reading code.

Example excerpt:

```json
{
  "before": {
    "fulfillments": 0,
    "reserved_inventory": 1
  },
  "after": {
    "fulfillments": 2,
    "reserved_inventory": 1
  },
  "signals": [
    "duplicate_fulfillment"
  ]
}
```

## report.md

Purpose:

- Gives a plain-English explanation for operators, founders, and customer teams.

Example excerpt:

```md
## Business Risk Summary

Risk: The automation retried a fulfillment after a timeout even though the first request had already committed.

Possible impact: duplicate shipment, extra shipping cost, inventory loss, and customer confusion.

Recommended control: use a stable idempotency key and verify current fulfillment state before retrying.
```

## patch_hints.json

Purpose:

- Gives Codex, Claude, or an engineering agent enough context to propose a fix.

Example excerpt:

```json
{
  "failure": "create_fulfillment committed internally, but the agent retried blindly after timeout.",
  "likely_guardrails": [
    "Persist idempotency key before calling mutating commerce action.",
    "On timeout, query existing fulfillment before retry.",
    "Treat accepted request and confirmed downstream state as separate states."
  ],
  "replay_command": "commerce-safety replay runs/<session_id>"
}
```

## run_manifest.json

Purpose:

- Proves artifact identity, hash, schema, workspace, session, and retention metadata.

Example excerpt:

```json
{
  "schema_version": "commerce_safety.run_manifest.v1",
  "workspace_id": "ws_design_partner",
  "session_id": "sess_demo",
  "retention": {
    "expires_at": "2026-06-14T00:00:00+00:00",
    "delete_after_expiry": true
  },
  "artifacts": [
    {
      "path": "trace.json",
      "artifact_type": "trace",
      "sha256": "..."
    }
  ]
}
```
