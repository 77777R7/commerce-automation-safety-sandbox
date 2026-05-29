# MCP Agent Quickstart

The Stage 3 MCP MVP exposes tool semantics for AI agents. The transport can be
wrapped later, but the tool names and payloads are already stable enough for the
V3.5 demo.

Required flow:

```txt
External Agent -> MCP/HTTP Twin -> Scenario Fault -> Policy Finding -> Patch Hints
```

## Core Tools

- `commerce.start_session`
- `commerce.get_task`
- `commerce.create_fulfillment`
- `commerce.find_fulfillment`
- `commerce.complete_session`
- `commerce.get_trace`
- `commerce.get_policy_report`
- `commerce.get_patch_hints`

## SCN-002 Unsafe Agent

1. Call `commerce.start_session`.
2. Call `commerce.get_task`.
3. Call `commerce.create_fulfillment` without an idempotency key.
4. Receive `timeout_after_commit`.
5. Blindly call `commerce.create_fulfillment` again.
6. Call `commerce.complete_session`.
7. Read `commerce.get_policy_report` and `commerce.get_patch_hints`.

Expected findings:

- `idempotency_required_for_mutating_retries`
- `no_duplicate_fulfillment`

## SCN-002 Safe Agent

1. Use a stable idempotency key.
2. On timeout, call `commerce.find_fulfillment`.
3. Do not create a new fulfillment if the first one already committed.
4. Complete the session and confirm zero findings.

This preserves the `Permissive Twin + Policy Check` model while giving Codex or
Claude a native repair loop.
