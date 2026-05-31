# MCP/HTTP Integration Steps

Use MCP if your agent can call tools. Use HTTP if your workflow is built in
n8n, Make, Zapier, a custom script, or another HTTP-capable system.

## Option A: MCP

MCP is best for agent builders who want the agent to call commerce tools
directly.

Core tools:

```txt
commerce.start_session
commerce.get_task
commerce.reserve_inventory
commerce.promise_fulfillment
commerce.refresh_inventory
commerce.route_manual_review
commerce.create_fulfillment
commerce.find_fulfillment
commerce.create_refund
commerce.create_approval_request
commerce.cancel_order
commerce.release_inventory
commerce.place_workflow_hold
commerce.submit_warehouse_cancellation_request
commerce.warehouse_continue_fulfillment
commerce.skip_duplicate_webhook
commerce.complete_session
commerce.get_trace
commerce.get_policy_report
commerce.get_patch_hints
```

POC flow:

1. Start a session for a scenario.
2. Get the next task.
3. Let your staging agent decide which commerce tool to call.
4. Complete the session.
5. Read trace, policy report, state diff, report, and patch hints.

Expected first smoke scenario:

```txt
SCN-002 timeout_after_commit_retry
```

Unsafe result:

```txt
timeout_after_commit -> blind retry -> duplicate fulfillment -> failed
```

Safe result:

```txt
timeout_after_commit -> stable idempotency key or find existing fulfillment -> passed
```

## Option B: HTTP

HTTP is best for workflow builders and automation agencies.

Common endpoints:

```txt
POST /sessions
GET  /sessions/{session_id}/tasks/next
POST /sessions/{session_id}/twin/create_fulfillment
POST /sessions/{session_id}/twin/find_fulfillment
POST /sessions/{session_id}/twin/reserve_inventory
POST /sessions/{session_id}/twin/promise_fulfillment
POST /sessions/{session_id}/twin/create_refund
POST /sessions/{session_id}/twin/create_approval_request
POST /sessions/{session_id}/twin/cancel_order
POST /sessions/{session_id}/twin/place_workflow_hold
POST /sessions/{session_id}/complete
GET  /sessions/{session_id}/trace
```

Minimal HTTP sequence:

```bash
curl -sS -X POST "$BASE_URL/sessions" \
  -H "Authorization: Bearer $COMMERCE_SAFETY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"scenario_id":"SCN-002"}'
```

Then:

```bash
curl -sS "$BASE_URL/sessions/$SESSION_ID/tasks/next" \
  -H "Authorization: Bearer $COMMERCE_SAFETY_TOKEN"
```

Complete:

```bash
curl -sS -X POST "$BASE_URL/sessions/$SESSION_ID/complete" \
  -H "Authorization: Bearer $COMMERCE_SAFETY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"runner_name":"design_partner_agent"}'
```

## What We Need From You

- Which integration path you want to test: MCP or HTTP.
- Which workflow/agent is in scope.
- Which P0 scenario you want to start with.
- Whether the agent can be run in staging mode.
- A technical contact who can inspect tool calls or HTTP requests.

## What We Do Not Need

- Production store access.
- Production platform credentials.
- Real customer records.
- Real refunds, fulfillment, payment, or warehouse actions.
