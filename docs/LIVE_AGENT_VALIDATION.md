# Live Agent Validation

V3.5 is Live Agent Sandbox-first.

```txt
External Agent -> MCP/HTTP Twin -> Scenario Fault -> Policy Finding -> Patch Hints
```

The core idea is `Permissive Twin + Policy Check`: unsafe actions are allowed to
mutate state first, then the policy engine decides whether a business accident
occurred.

## Demo Flow

1. Start a live session from a scenario.
2. The external agent gets the next scenario task.
3. The agent calls the MCP/HTTP Twin.
4. The scenario injects a fault such as `timeout_after_commit`.
5. The agent either handles the uncertainty safely or creates an accident.
6. `complete_session` evaluates policies and writes repair artifacts.

## Stage 7 Narrative

This is not a CLI-only demo and not a static mock. The product value is showing
how an external agent behaves when order, inventory, fulfillment, refund,
warehouse, webhook, and retry state collide.

## Main Proof

`SCN-002 timeout-after-commit` shows why successful operations can still be
dangerous. The first fulfillment commits, the caller receives a timeout, and an
unsafe retry creates duplicate fulfillment. The repair package explains the
guardrail: stable idempotency key plus existing-state check before retry.
