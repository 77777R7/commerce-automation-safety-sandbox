# GitHub Check Summary: Agent validation failed: duplicate_stripe_webhook_side_effects

- Check: `agent-validation/policy-pack`
- Status: `completed`
- Conclusion: `failure`
- Policy status: `failed`
- Run ID: `sess_20260617T023232837310Z_SAAS-003_7f40d5ad`
- Policy packs: `['saas_billing_v0']`

## Summary

Policy evaluation returned `failed` with 1 finding(s): `stripe_duplicate_webhook_side_effects_must_be_deduped`. 3 repair guardrail(s) were generated.

## Annotations

### stripe_duplicate_webhook_side_effects_must_be_deduped

- Level: `failure`
- Path: `policy_report.json`
- Message: A repeated Stripe webhook produced duplicate Slack or GitHub side effects for the same billing incident. That can page a team twice, create duplicate recovery work, and make PR checks look unstable.

```json
{
  "severity": "high",
  "recommendation": "Persist the processed Stripe event ID and skip repeated deliveries before posting Slack alerts or creating GitHub review artifacts.",
  "evidence": {
    "duplicate_stripe_events": [
      {
        "event_id": "evt_000003",
        "type": "invoice.payment_failed",
        "object_id": "in_000003",
        "payload": {
          "invoice": {
            "invoice_id": "in_000003",
            "customer_id": "cus_000003",
            "subscription_id": "sub_000003",
            "payment_intent_id": "pi_000003",
            "amount_due": 2900,
            "amount_paid": 0,
            "currency": "usd",
            "status": "open"
          },
          "subscription": {
            "subscription_id": "sub_000003",
            "customer_id": "cus_000003",
            "price_id": "price_pro_monthly",
            "latest_invoice_id": "in_000003",
            "status": "incomplete"
          },
          "payment_intent": {
            "payment_intent_id": "pi_000003",
            "customer_id": "cus_000003",
            "invoice_id": "in_000003",
            "amount": 2900,
            "currency": "usd",
            "status": "requires_payment_method",
            "last_payment_error": "card_declined"
          }
        },
        "delivered_count": 2,
        "duplicate_delivery_count": 1
      }
    ],
    "duplicate_slack_side_effects": [
      {
        "stripe_event_id": "evt_000003",
        "kind": "billing_failure_alert",
        "messages": [
          {
            "message_id": "slack_msg_000001",
            "channel_id": "C_BILLING_ESCALATION",
            "text": "Billing failure: Stripe invoice payment failed.",
            "delivered": true,
            "error": null,
            "thread_ts": null,
            "metadata": {
              "kind": "billing_failure_alert",
              "stripe_event_id": "evt_000003"
            },
            "actor": "demo_pack_saas003_unsafe_agent"
          },
          {
            "message_id": "slack_msg_000002",
            "channel_id": "C_BILLING_ESCALATION",
            "text": "Billing failure: Stripe invoice payment failed.",
            "delivered": true,
            "error": null,
            "thread_ts": null,
            "metadata": {
              "kind": "billing_failure_alert",
              "stripe_event_id": "evt_000003"
            },
            "actor": "demo_pack_saas003_unsafe_agent"
          }
        ]
      }
    ],
    "duplicate_github_side_effects": [
      {
        "stripe_event_id": "evt_000003",
        "side_effect_type": "check_run",
        "dedupe_key": "agent-policy/saas-validation",
        "items": [
          {
            "check_run_id": "check_000001",
            "name": "agent-policy/saas-validation",
            "repo": "acme/billing-agent",
            "head_sha": "fed789",
            "status": "completed",
            "conclusion": "action_required",
            "output_summary": "Stripe payment failed; billing recovery required.",
            "details_url": null,
            "metadata": {
              "kind": "billing_recovery_check",
              "stripe_event_id": "evt_000003"
            }
          },
          {
            "check_run_id": "check_000002",
            "name": "agent-policy/saas-validation",
            "repo": "acme/billing-agent",
            "head_sha": "fed789",
            "status": "completed",
            "conclusion": "action_required",
            "output_summary": "Stripe payment failed; billing recovery required.",
            "details_url": null,
            "metadata": {
              "kind": "billing_recovery_check",
              "stripe_event_id": "evt_000003"
            }
          }
        ]
      }
    ]
  }
}
```


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
