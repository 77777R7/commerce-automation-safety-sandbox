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

The default transport is `stdio`, which is the right mode for local agent
clients such as Codex or Claude Desktop. The server also accepts
`--transport streamable-http` for later hosted experiments, but V3.5 does not
turn this into a hosted platform.

## Core Tools

The real MCP server intentionally exposes the eight core commerce tools:

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

This keeps the product surface centered on the V3.5 proof:

```txt
External Agent -> MCP/HTTP Twin -> Scenario Fault -> Policy Finding -> Patch Hints
```

## Smoke Test

Run:

```bash
PYTHON=python3.12 ./tools/smoke_stage9_real_mcp.sh
```

The smoke starts the MCP server over stdio, calls the eight tools through the
official SDK client, and runs SCN-002 twice:

- unsafe agent: timeout after commit, blind retry, policy failure
- safe agent: stable idempotency key, find existing fulfillment, pass

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
