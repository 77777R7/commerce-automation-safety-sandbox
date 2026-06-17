# Design Partner Walkthrough

## Ask

Bring one staging workflow that touches billing, incident notification, or PR
status. Do not provide production credentials, customer PII, real refunds, or
real PR write access.

## What We Run

First we run SAAS-001 as the baseline:

```txt
failed Stripe payment -> Slack alert delivery failure -> GitHub false success
```

Then we map one part of your workflow to the closest twin action path:

- Billing action -> Stripe twin.
- Human notification -> Slack twin.
- PR/check/review state -> GitHub twin.

## What You Receive

- `trace.json`: ordered event ledger.
- `policy_report.json`: structured policy findings.
- `state_diff.json`: before/after business state.
- `patch_hints.json`: agent-readable guardrails.
- `run_manifest.json`: artifact contract for auditability.

## Success Criteria

- Unsafe path produces clear findings.
- Safe path passes with zero findings.
- The report names a concrete guardrail your agent or workflow can implement.
- No production keys, customer PII, real refunds, or real platform writes are used.

