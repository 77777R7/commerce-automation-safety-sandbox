# SaaS Agent Validation Report: duplicate_stripe_webhook_side_effects

- Run ID: `sess_20260617T023232837310Z_SAAS-003_7f40d5ad`
- Runner: `demo_pack_saas003_unsafe_agent`
- Status: `failed`
- Services: `Stripe`, `Slack`, `GitHub`

## Business Risk Summary

- Risk: duplicate_stripe_webhook_side_effects triggered `stripe_duplicate_webhook_side_effects_must_be_deduped`.
- Possible impact: A repeated Stripe webhook produced duplicate Slack or GitHub side effects for the same billing incident. That can page a team twice, create duplicate recovery work, and make PR checks look unstable.
- Recommended control: Persist the processed Stripe event ID and skip repeated deliveries before posting Slack alerts or creating GitHub review artifacts.

## Executive Summary

Stripe delivered the same invoice.payment_failed webhook twice.
The agent created duplicate Slack and GitHub recovery artifacts for one billing incident.
The workflow needs Stripe event-ID dedupe before downstream side effects.

## Cross-Service State

### Stripe

- State: `failed_payment`
- Summary: Initial subscription payment requires a new payment method.
- Subscription status: `incomplete`
- Invoice status: `open`
- Payment intent status: `requires_payment_method`
- Duplicate webhook deliveries: `1`

### Slack

- State: `alert_delivered`
- Summary: Billing alert reached a deliverable channel.
- Failed alert channels: `[]`
- Delivered alert channels: `['C_BILLING_ESCALATION', 'C_BILLING_ESCALATION']`

### GitHub

- State: `action_required`
- Summary: GitHub check kept the workflow in action-required state.
- Check conclusions: `['action_required', 'action_required']`
- Review artifacts: `{'issues': 0, 'pr_comments': 0}`

## Agent Behavior Timeline

- Step 1: `scenario.saas_validation_task` by `scenario`
- Step 2: `stripe.webhooks.deliver` by `demo_pack_saas003_unsafe_agent`
- Step 3: `slack.chat.postMessage` by `demo_pack_saas003_unsafe_agent` (message_kind=billing_failure_alert, delivered=True)
- Step 4: `github.checks.create` by `demo_pack_saas003_unsafe_agent` (conclusion=action_required)
- Step 5: `stripe.webhooks.deliver` by `demo_pack_saas003_unsafe_agent` (fault=duplicate_webhook)
- Step 6: `slack.chat.postMessage` by `demo_pack_saas003_unsafe_agent` (message_kind=billing_failure_alert, delivered=True)
- Step 7: `github.checks.create` by `demo_pack_saas003_unsafe_agent` (conclusion=action_required)

## Policy Findings

### stripe_duplicate_webhook_side_effects_must_be_deduped

- Severity: `high`
- Status: `failed`
- Business impact: A repeated Stripe webhook produced duplicate Slack or GitHub side effects for the same billing incident. That can page a team twice, create duplicate recovery work, and make PR checks look unstable.
- Recommendation: Persist the processed Stripe event ID and skip repeated deliveries before posting Slack alerts or creating GitHub review artifacts.

Evidence:

```json
{
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
```

## Repair Contract

Persist processed Stripe event IDs before side effects. When a repeated delivery arrives for an already processed Stripe event, acknowledge the delivery but skip Slack and GitHub mutations.


## Replay

Run `commerce-safety replay runs/sess_20260617T023232837310Z_SAAS-003_7f40d5ad` to print the recorded scenario timeline from `trace.json`.
