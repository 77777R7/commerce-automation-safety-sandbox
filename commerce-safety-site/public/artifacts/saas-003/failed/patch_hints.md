# Patch Hints: duplicate_stripe_webhook_side_effects

- Run ID: `sess_20260617T053957415334Z_SAAS-003_cafc8120`
- Status: `failed`

## stripe_duplicate_webhook_side_effects_must_be_deduped

- Severity: `high`
- Root cause: A duplicate Stripe webhook delivery produced duplicate Slack or GitHub side effects for the same billing incident.
- Guardrails:
  - Persist processed Stripe event IDs before creating Slack or GitHub side effects.
  - Skip repeated webhook deliveries when the Stripe event ID was already handled.
  - Use the Stripe event ID as the idempotency key for billing incident alerts and review artifacts.
