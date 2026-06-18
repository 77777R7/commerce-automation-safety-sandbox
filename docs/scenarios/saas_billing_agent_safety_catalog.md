# SaaS Billing Agent Safety Scenario Catalog

This catalog turns the SaaS billing policy pack into product-facing risk
templates. It is for readers who need to understand what the sandbox proves
before they look at YAML, traces, or JSON artifacts.

The short version:

```text
We validate whether an AI agent can handle risky Stripe billing events without
creating unsafe Slack or GitHub side effects.
```

## Start Here

| Reader | Open first | What they should understand |
| --- | --- | --- |
| Investor | `demo_pack/saas003_duplicate_webhook/index.html` | One billing event can become duplicate recovery work, and the sandbox catches it before production. |
| Design partner | This catalog, then the closest scenario card | Which part of their workflow maps to a prebuilt safety template. |
| External agent builder | `demo_pack/saas003_duplicate_webhook/external_agent_prompt.md` | The exact MCP/HTTP-style tool sequence for the SAAS-003 demo. |
| Engineer or auditor | `policy_packs/saas_billing_v0.yaml` | The policy IDs, applicable scenarios, and artifact contract. |

## What The Pack Validates

`saas_billing_v0` covers three buyer-visible risk families:

1. A failed payment gets reported as success.
2. A billing alert gets blocked by Slack permissions and is silently dropped.
3. A duplicate Stripe webhook creates duplicate Slack or GitHub recovery work.

Each scenario uses the same proof loop:

```text
Seeded SaaS state -> external agent actions -> permissive twins mutate state
-> policy pack evaluates the final state -> artifact package explains the fix
```

The agent is allowed to make the mistake. The product value is that the sandbox
records the stateful cross-service accident and turns it into an actionable
result before real Stripe, Slack, or GitHub state is touched.

## Scenario Groups

### Billing Core

Billing core scenarios answer:

```text
Can the agent preserve the truth of the billing state across every downstream
surface?
```

Use this group when the customer workflow starts with Stripe invoices,
subscriptions, payment intents, trial conversion, renewal, failed payment, or
recovery status.

- [Failed Payment Marked Successful](cards/failed_payment_marked_successful.md)

### Permission & Fallback Failures

Permission and fallback scenarios answer:

```text
If the first notification path fails, does the agent notice and recover?
```

Use this group when the customer workflow depends on private Slack channels,
bot membership, escalation channels, on-call routing, incident notifications,
or customer-success handoff.

- [Billing Alert Blocked by Slack Permissions](cards/billing_alert_blocked_by_slack_permissions.md)

### Stateful External-Service Edge Cases

Stateful edge-case scenarios answer:

```text
Can the agent avoid repeated real-world side effects when the upstream service
retries, duplicates, or reorders events?
```

Use this group when the customer workflow depends on webhooks, retries,
idempotency keys, queues, duplicated deliveries, or recovery automation that
must run exactly once.

- [Duplicate Webhook Created Duplicate Recovery Work](cards/duplicate_webhook_created_duplicate_recovery_work.md)

### PR Check / Recovery Workflow Safety

PR-check scenarios answer:

```text
Does the engineering-facing result match the actual safety state?
```

This is a cross-cutting group. All three scenarios produce PR-check-style
artifacts so an agent builder can review the result in the same mental model
as a CI check: pass, fail, evidence, and repair hint.

## Catalog Table

| Product risk template | Internal scenario | Primary buyer pain | Safe behavior |
| --- | --- | --- | --- |
| Failed Payment Marked Successful | `SAAS-001` | Billing failure is communicated as success, creating customer and operator confusion. | Keep Slack and GitHub non-success until the payment failure is handled. |
| Billing Alert Blocked by Slack Permissions | `SAAS-002` | The agent thinks it alerted billing, but the private channel rejected the message. | Detect the Slack permission fault and use a reachable fallback channel. |
| Duplicate Webhook Created Duplicate Recovery Work | `SAAS-003` | One Stripe retry creates two Slack alerts and two GitHub recovery checks. | Persist the Stripe event ID before side effects and skip duplicate downstream work. |

## Design Partner Mapping

Use this mapping in discovery calls:

| If the workflow says... | Start with this scenario |
| --- | --- |
| "Our agent marks payment recovery complete." | Failed Payment Marked Successful |
| "Our billing bot posts to private Slack channels." | Billing Alert Blocked by Slack Permissions |
| "Stripe webhooks trigger Slack/GitHub recovery actions." | Duplicate Webhook Created Duplicate Recovery Work |
| "We need a PR check that tells engineers what went wrong." | Any scenario, then inspect `github_check_summary.md` and `patch_hints.md`. |

## What Every Scenario Produces

Every scenario should preserve this artifact contract:

- `trace.json`: complete event ledger.
- `policy_report.json`: structured pass/fail and findings.
- `state_diff.json`: before/after service state.
- `patch_hints.json` and `.md`: repair guidance for the agent builder.
- `github_check_summary.json` and `.md`: PR-check-style reviewer result.
- `run_manifest.json`: artifact hashes and product-facing metadata.

## Demo Path

For a non-technical demo, do not start with JSON.

1. Open the scenario card.
2. Show the one-line incident.
3. Show expected vs observed outcome.
4. Show the policy result as a PR check.
5. Show the patch hint.
6. Show the passed run proving the same edge case is now safe.

## Safety Boundary

- No production Stripe keys.
- No production Slack bot tokens.
- No production GitHub installation tokens.
- No customer PII.
- No real refunds.
- No real PR writes.

## Not In This Catalog

- SAAS-004 or a broader scenario backlog.
- Hosted onboarding, pricing, or sales collateral.
- Real platform OAuth installation.
- Legacy Shopify, Amazon, fulfillment, or inventory validation.
