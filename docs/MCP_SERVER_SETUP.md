# MCP Server Setup

Stage 9 turns the V3.5 MCP layer from an internal semantic wrapper into a real
MCP server built with `modelcontextprotocol/python-sdk`.

## Requirements

- Python 3.10+
- `mcp` from `modelcontextprotocol/python-sdk`
- The normal MVP dependencies in `requirements.txt`

Install:

```bash
python -m pip install -r requirements.txt
```

If your system `python3` is Python 3.9, create a Python 3.10+ virtualenv for the
MCP server:

```bash
python3.12 -m venv .venv-mcp
source .venv-mcp/bin/activate
python -m pip install -r requirements.txt
```

## Run The Server

From the repository root:

```bash
PYTHONPATH="$PWD/commerce-safety-sandbox" \
python -m commerce_safety.live.mcp_server --runs-dir runs
```

Or through the CLI:

```bash
PYTHONPATH="$PWD/commerce-safety-sandbox" \
./commerce-safety live mcp --runs-dir runs
```

For external testers, use the self-check and generated config first:

```bash
./commerce-safety doctor
./commerce-safety mcp-config --python "$PWD/.venv-mcp/bin/python"
```

The default transport is `stdio`, which is the right mode for local agent
clients such as Codex or Claude Desktop. The server also accepts
`--transport streamable-http` for later hosted experiments, but V3.5 does not
turn this into a hosted platform.

## Core Tools And P0 Action Tools

Stage 9 locked the eight core commerce tools:

```txt
commerce.start_session
commerce.get_task
commerce.create_fulfillment
commerce.find_fulfillment
commerce.complete_session
commerce.get_trace
commerce.get_policy_report
commerce.get_patch_hints
```

Stage 10 expands the real MCP server with the generic commerce actions needed
to run all five P0 scenarios through agent-facing tools:

```txt
commerce.reserve_inventory
commerce.promise_fulfillment
commerce.refresh_inventory
commerce.route_manual_review
commerce.create_refund
commerce.create_approval_request
commerce.cancel_order
commerce.release_inventory
commerce.place_workflow_hold
commerce.submit_warehouse_cancellation_request
commerce.warehouse_continue_fulfillment
commerce.skip_duplicate_webhook
```

This keeps the product surface centered on the V3.5 proof:

```txt
External Agent -> MCP/HTTP Twin -> Scenario Fault -> Policy Finding -> Patch Hints
```

## Smoke Test

Run:

```bash
PYTHON=python3.12 ./tools/smoke_stage9_real_mcp.sh
PYTHON=python3.12 ./tools/smoke_stage10_mcp_p0_all.sh
```

The Stage 9 smoke starts the MCP server over stdio, calls the eight core tools
through the official SDK client, and runs SCN-002 twice:

- unsafe agent: timeout after commit, blind retry, policy failure
- safe agent: stable idempotency key, find existing fulfillment, pass

The Stage 10 smoke uses the same real MCP server to drive unsafe and safe paths
for all five P0 scenarios.

## Scope Boundary

Stage 9 keeps the core principle:

```txt
Permissive Twin + Policy Check
```

Unsafe actions are not rejected up front. The twin records them, then the Policy
Oracle detects the business incident at session completion.

Stage 9 does not add:

- Sandbox0
- Firecracker
- gVisor
- Shopify/Amazon full API clones
- Microcks
- buyer simulator
