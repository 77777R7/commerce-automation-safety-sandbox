# Live Agent Validation Demo Pack

This is the V3.5 demo narrative:

```txt
External Agent -> MCP/HTTP Twin -> Scenario Fault -> Policy Finding -> Patch Hints
```

Commerce Automation Safety Sandbox is not a mock server. It is a permissive,
stateful accident sandbox for commerce automation and AI agents.

## What This Demo Proves

- An external agent can connect through MCP/HTTP Twin surfaces.
- The twin allows unsafe commerce actions to happen.
- The policy engine catches the resulting business accident.
- The trace and repair artifacts explain what happened and how to fix it.

## Primary Demo

Use `SCN-002 timeout-after-commit`.

The unsafe agent calls create_fulfillment, the twin commits it, then returns a
timeout. The unsafe agent blindly retries and creates `ful_002`. The policy
engine flags:

- `idempotency_required_for_mutating_retries`
- `no_duplicate_fulfillment`

The safe agent uses a stable idempotency key and checks existing fulfillment
state before retrying.

## Artifacts To Show

- `trace.json`
- `policy_report.json`
- `state_diff.json`
- `report.md`
- `patch_hints.json`
- `patch_hints.md`
- `agent_summary.md`
- `failure_explain.md`

## Positioning

Offline Audit remains useful for POCs, but the V3.5 product story is
Live Agent Sandbox-first: agents and workflows should be tested against a
stateful commerce twin before they touch real stores.
