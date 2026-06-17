# SAAS-003 Demo Pack: Duplicate Stripe Webhook Side Effects

## What This Shows

SAAS-003 is the stateful external-service edge case:

```txt
duplicate Stripe invoice.payment_failed webhook
-> duplicate Slack billing alerts
-> duplicate GitHub recovery checks
-> policy failure
```

The safe path still receives the duplicate Stripe delivery, but the agent uses
the Stripe event ID as the idempotency key and skips the second Slack/GitHub
side effect.

## Audience

- Agent builders validating billing and incident-response agents.
- Investors evaluating whether this is more than a static mock.
- Design partners with workflows that touch Stripe webhooks, Slack alerts, or
  GitHub checks.

## Safety Boundary

- No production Stripe keys.
- No production Slack bot tokens.
- No production GitHub installation tokens.
- No customer PII.
- No real refunds.
- No real PR writes.

## Read First

- `runbook.md`
- `sample_outputs/failed/github_check_summary.md`
- `sample_outputs/failed/state_diff.json`
- `sample_outputs/passed/github_check_summary.md`
- `sample_outputs/passed/state_diff.json`

## Generated Artifacts

The sample outputs are generated from the HTTP action surface:

- `trace.json`
- `policy_report.json`
- `state_diff.json`
- `report.md`
- `patch_hints.json`
- `patch_hints.md`
- `agent_summary.md`
- `failure_explain.md`
- `github_check_summary.json`
- `github_check_summary.md`
- `run_manifest.json`

## Why This Matters

This is the kind of bug that simple unit tests miss. Stripe can deliver the same
event more than once. A permissive twin lets the agent make the mistake, while
the policy pack judges the final cross-service state.
