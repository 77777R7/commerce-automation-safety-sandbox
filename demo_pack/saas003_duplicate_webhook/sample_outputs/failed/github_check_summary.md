# GitHub Check Summary: Agent validation failed: duplicate_stripe_webhook_side_effects

- Check: `agent-validation/policy-pack`
- Status: `completed`
- Conclusion: `failure`
- Policy status: `failed`
- Run ID: `sess_20260617T053957415334Z_SAAS-003_cafc8120`
- Policy packs: `['saas_billing_v0']`

## Summary

A duplicate Stripe `invoice.payment_failed` delivery created duplicate downstream side effects. Expected exactly one Slack billing alert and one GitHub recovery check; observed 2 Slack alert(s) and 2 GitHub check(s). Required fix: persist processed Stripe event IDs before Slack or GitHub mutations.

## Incident Card

One Stripe event created duplicate recovery work.

- Stripe event: `evt_000003`
- Event type: `invoice.payment_failed`
- Deliveries observed: `2`
- Required guardrail: Persist processed Stripe event IDs before creating Slack or GitHub side effects.

| Signal | Expected | Observed |
| --- | ---: | ---: |
| Stripe logical event | 1 | 2 deliveries |
| Slack billing alerts | 1 | 2 |
| GitHub recovery checks | 1 | 2 |

## Annotations

### stripe_duplicate_webhook_side_effects_must_be_deduped

- Level: `failure`
- Path: `policy_report.json`
- Message: A repeated Stripe webhook produced duplicate Slack or GitHub side effects for the same billing incident. That can page a team twice, create duplicate recovery work, and make PR checks look unstable.
- Severity: `high`
- Raw evidence: see `policy_report.json`.


## Repair Hints

### stripe_duplicate_webhook_side_effects_must_be_deduped

- Root cause: A duplicate Stripe webhook delivery produced duplicate Slack or GitHub side effects for the same billing incident.
- Guardrails:
  - Persist processed Stripe event IDs before creating Slack or GitHub side effects.
  - Skip repeated webhook deliveries when the Stripe event ID was already handled.
  - Use the Stripe event ID as the idempotency key for billing incident alerts and review artifacts.

## Artifact Refs

```json
{
  "trace": "trace.json",
  "policy_report": "policy_report.json",
  "patch_hints": "patch_hints.json",
  "state_diff": "state_diff.json"
}
```
