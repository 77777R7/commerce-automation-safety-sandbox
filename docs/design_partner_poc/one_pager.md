# Commerce Safety Sandbox: Design Partner POC

## The Problem

AI agents and automations are moving into commerce operations: orders,
inventory, fulfillment, refunds, cancellations, and warehouse workflows.

When these systems make a wrong decision, the result is not a test failure. It
can be duplicate shipment, oversell, refund loss, warehouse conflict, or
customer-support escalation.

## What We Do

Commerce Safety Sandbox is a pre-production crash-test layer for commerce
automation and AI agents.

We simulate stateful commerce accidents before your agent touches a real store:

- duplicate webhooks
- timeout after commit
- stale inventory
- refund after shipment
- cancellation versus warehouse pick/pack conflict

## Why It Is Different

Normal mocks ask:

```txt
Did the API call return the expected shape?
```

We ask:

```txt
Did the automation create unsafe commerce state?
```

Our twin is permissive. It lets the bad action happen in a fake commerce world,
then the policy engine catches the business incident and explains the fix.

## What The POC Tests

- Unsafe path: your staging agent or workflow handles the scenario badly.
- Safe path: your staging agent or workflow applies the right guardrail.
- Artifacts: trace, policy report, state diff, report, patch hints, manifest.

## Safety Boundary

We do not need:

- production Shopify or Amazon credentials
- real Stripe secrets
- real warehouse credentials
- real customer PII
- live refund or fulfillment permissions

Use staging agents, synthetic payloads, redacted data, or action logs.

## POC Outcome

At the end, you know:

- which accident classes your automation handles safely
- which accident classes produce policy findings
- what guardrails to add before production
- which failures should become regression tests

## Next Step

Pick one staging workflow and run `SCN-002 timeout_after_commit_retry` as the
first smoke test.
