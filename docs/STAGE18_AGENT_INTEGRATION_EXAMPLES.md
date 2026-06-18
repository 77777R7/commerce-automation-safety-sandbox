# Stage 18: Agent Integration Examples

Stage 18 closes the gap between a working V3.5 interface and a self-serve
agent-builder integration experience.

The core product narrative remains:

```txt
External Agent -> MCP/HTTP Twin -> Scenario Fault -> Policy Finding -> Patch Hints
```

## Goal

Make the V3.5 sandbox usable by an external AI agent developer without opening
the runtime source code.

Stage 18 does not add new commerce scenarios, platform skins, hosted sessions,
or UI polish. It packages the existing MCP, HTTP, and action-log surfaces into
runnable examples with a gate.

## Deliverables

- `examples/agent_integrations/README.md`.
- `examples/agent_integrations/mcp_scn002_timeout_retry_agent.py`.
- `examples/agent_integrations/http_scn002_timeout_retry_agent.py`.
- `examples/agent_integrations/action_logs/scn004_refund_bad.jsonl`.
- `examples/agent_integrations/action_logs/scn004_refund_safe.jsonl`.
- `tests/test_stage18_agent_integration_examples.py`.
- `tools/smoke_stage18_agent_examples.sh`.

## Acceptance

- The MCP example drives `SCN-002 timeout_after_commit_retry` through the real
  MCP server.
- The HTTP example drives the same `SCN-002` unsafe and safe paths through the
  local HTTP Twin API.
- The action-log fixtures drive `SCN-004 refund_after_shipment_bypass` through
  the CI-style `commerce-safety gate`.
- Unsafe examples fail with structured policy findings.
- Safe examples pass with zero findings.
- Every generated run path passes `tools/check_run_manifest.py`.
- The examples remain local-only and do not reference production Shopify,
  Amazon, Stripe, GitHub, or Slack credentials.

## Gate

```bash
PYTHON=python3.12 ./tools/smoke_stage18_agent_examples.sh
```

This gate runs the Stage 18 unit tests, MCP example, HTTP example, action-log
fixtures, and run-manifest validation.

## Non-Goals

- Full Shopify GraphQL implementation.
- Full Amazon SP-API clone.
- Hosted multi-tenant control plane.
- Buyer simulator.
- New P0 scenario classes.
- UI/dashboard work.
