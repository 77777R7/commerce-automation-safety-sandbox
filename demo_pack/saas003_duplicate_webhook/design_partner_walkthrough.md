# Design Partner Walkthrough

## Bring This Workflow

Bring one staging or planned workflow where a Stripe webhook can trigger:

- a Slack incident or billing alert,
- a GitHub check, issue, or PR comment,
- a recovery action that should be idempotent.

Do not provide production credentials, customer PII, real refunds, or real PR
write access.

## What We Map

- Stripe webhook event ID -> dedupe key.
- Slack alert -> human-visible incident notification.
- GitHub check or issue -> engineering/recovery artifact.
- Duplicate delivery -> repeated external-service edge case.

## What You Receive

- `trace.json`: event ledger with both Stripe deliveries.
- `state_diff.json`: duplicate delivery and side-effect signals.
- `policy_report.json`: structured finding if duplicate side effects occurred.
- `github_check_summary.json` / `.md`: PR-check-style result.
- `patch_hints.json`: concrete guardrails for your agent.
- `run_manifest.json`: artifact contract for auditability.

## Success Criteria

- Unsafe path creates an obvious failure.
- Safe path still receives the duplicate webhook but creates no duplicate side effects.
- The recommended guardrail names the concrete idempotency key.
- No real platform writes are used.
