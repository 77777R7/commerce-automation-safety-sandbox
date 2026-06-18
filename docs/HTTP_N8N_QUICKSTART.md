# HTTP And n8n Quickstart

Use this path when the tester does not use MCP. It is for n8n, Make, Zapier,
Shopify Flow-style automation, custom scripts, and HTTP-capable agents.

No real Shopify, Amazon, warehouse, carrier, or customer data is required.

## Importable n8n Workflow

The fastest n8n path is to import this workflow:

```txt
demo_pack/n8n/scn002_timeout_retry_unsafe_safe.json
```

It contains both branches:

- unsafe retry without idempotency
- safe retry with state lookup and a stable idempotency key

## 1. Start The Local Twin API

```bash
PYTHONPATH="$PWD/commerce-safety-sandbox" \
./commerce-safety live serve --host 127.0.0.1 --port 8765
```

Base URL:

```txt
http://127.0.0.1:8765
```

## 2. Import And Run The Workflow

In n8n:

1. Import `demo_pack/n8n/scn002_timeout_retry_unsafe_safe.json`.
2. Open the workflow.
3. Click **Execute workflow**.
4. Inspect `Complete Unsafe Session` and `Complete Safe Session`.

Expected:

- `Complete Unsafe Session` returns `status: failed`.
- `Complete Safe Session` returns `status: passed`.

## Manual HTTP Steps

Use these if the tester wants to build the workflow from scratch.

### 1. Create A Session

```bash
curl -sS -X POST http://127.0.0.1:8765/sessions \
  -H "Content-Type: application/json" \
  -d '{"scenario_path":"commerce-safety-sandbox/scenarios/SCN-002_timeout_after_commit_retry.yaml"}'
```

Copy the returned `session_id`.

### 2. Get The Task

```bash
curl -sS http://127.0.0.1:8765/sessions/$SESSION_ID/tasks/next
```

The task tells the workflow which order and SKU it is supposed to fulfill.

### 3. Unsafe Workflow Test

Call fulfillment without an idempotency key:

```bash
curl -sS -X POST http://127.0.0.1:8765/sessions/$SESSION_ID/twin/create_fulfillment \
  -H "Content-Type: application/json" \
  -d '{"order_id":"order_2001","sku":"sku_retry_1","quantity":1,"fault_type":"timeout_after_commit"}'
```

If the response is `timeout_after_commit`, blindly retrying the same action
without a stable idempotency key should create the unsafe duplicate.

### 4. Complete And Inspect

```bash
curl -sS -X POST http://127.0.0.1:8765/sessions/$SESSION_ID/complete \
  -H "Content-Type: application/json" \
  -d '{"runner_name":"n8n_unsafe_workflow"}'
```

Expected findings:

- `idempotency_required_for_mutating_retries`
- `no_duplicate_fulfillment`

The generated run folder contains:

- `trace.json`
- `policy_report.json`
- `state_diff.json`
- `patch_hints.md`
- `report.md`

## n8n Node Mapping

Use HTTP Request nodes:

1. `POST /sessions`
2. `GET /sessions/{{session_id}}/tasks/next`
3. `POST /sessions/{{session_id}}/twin/create_fulfillment`
4. IF node: if response error is `timeout_after_commit`
5. Unsafe branch: repeat create fulfillment without idempotency
6. Safe branch: call `find_fulfillment` or reuse the same idempotency key
7. `POST /sessions/{{session_id}}/complete`

The important design rule:

```txt
accepted request != downstream state confirmed
```

For mutating actions like fulfillment, refund, reshipment, inventory updates,
and tracking upload, the workflow should confirm state before retrying.
