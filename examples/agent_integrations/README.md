# Agent Integration Examples

Stage 18 packages the V3.5 live sandbox into copy-paste examples for external
agent builders. These examples prove the product narrative:

```txt
External Agent -> MCP/HTTP Twin -> Scenario Fault -> Policy Finding -> Patch Hints
```

They intentionally use the same scenario for unsafe and safe paths. The core
principle is `Permissive Twin + Policy Check`: unsafe actions mutate state
first; `PolicyEngine` catches the incident at completion.

## SAAS-001 Stripe/Slack/GitHub Hero Example

Run the first SaaS validation scenario through HTTP:

```bash
PYTHONPATH="$PWD/commerce-safety-sandbox" \
./commerce-safety live serve --runs-dir runs/saas001_http --host 127.0.0.1 --port 8765
```

In another terminal:

```bash
python examples/agent_integrations/http_saas001_failed_payment_agent.py \
  --base-url http://127.0.0.1:8765 \
  --mode unsafe \
  --json

python examples/agent_integrations/http_saas001_failed_payment_agent.py \
  --base-url http://127.0.0.1:8765 \
  --mode safe \
  --json
```

Run the same hero path through the real MCP server:

```bash
PYTHONPATH="$PWD/commerce-safety-sandbox" \
python examples/agent_integrations/mcp_saas001_failed_payment_agent.py \
  --root "$PWD" \
  --runs-dir runs/saas001_mcp \
  --mode unsafe \
  --json

PYTHONPATH="$PWD/commerce-safety-sandbox" \
python examples/agent_integrations/mcp_saas001_failed_payment_agent.py \
  --root "$PWD" \
  --runs-dir runs/saas001_mcp \
  --mode safe \
  --json
```

Expected result:

- `unsafe` fails with the SAAS-001 billing, Slack delivery, and GitHub false-success policies.
- `safe` passes with zero findings.
- Each run writes `trace.json`, `policy_report.json`, `state_diff.json`,
  `report.md`, `patch_hints.json`, and `run_manifest.json`.

## MCP Example

Run SCN-002 through the real MCP server using
`modelcontextprotocol/python-sdk`:

```bash
PYTHONPATH="$PWD/commerce-safety-sandbox" \
python examples/agent_integrations/mcp_scn002_timeout_retry_agent.py \
  --mode unsafe \
  --runs-dir runs/stage18_examples \
  --json

PYTHONPATH="$PWD/commerce-safety-sandbox" \
python examples/agent_integrations/mcp_scn002_timeout_retry_agent.py \
  --mode safe \
  --runs-dir runs/stage18_examples \
  --json
```

Expected result:

- `unsafe` fails with `idempotency_required_for_mutating_retries` and
  `no_duplicate_fulfillment`.
- `safe` passes with zero findings.
- Each run writes `trace.json`, `policy_report.json`, `state_diff.json`,
  `report.md`, `patch_hints.json`, and `run_manifest.json`.

## HTTP Example

Start the local HTTP Twin API:

```bash
PYTHONPATH="$PWD/commerce-safety-sandbox" \
./commerce-safety live serve --runs-dir runs/stage18_http --host 127.0.0.1 --port 8765
```

In another terminal:

```bash
python examples/agent_integrations/http_scn002_timeout_retry_agent.py \
  --base-url http://127.0.0.1:8765 \
  --mode unsafe \
  --json

python examples/agent_integrations/http_scn002_timeout_retry_agent.py \
  --base-url http://127.0.0.1:8765 \
  --mode safe \
  --json
```

## Action-Log Example

Use this for agencies or AI SaaS teams that can export actions but cannot wire
MCP/HTTP yet:

```bash
./commerce-safety gate \
  --scenario commerce-safety-sandbox/scenarios/SCN-004_refund_after_shipment_bypass.yaml \
  --action-log examples/agent_integrations/action_logs/scn004_refund_bad.jsonl \
  --runner-name example_action_log_unsafe_agent \
  --json

./commerce-safety gate \
  --scenario commerce-safety-sandbox/scenarios/SCN-004_refund_after_shipment_bypass.yaml \
  --action-log examples/agent_integrations/action_logs/scn004_refund_safe.jsonl \
  --runner-name example_action_log_safe_agent \
  --json
```

Expected result:

- The bad log exits `1` and finds refund-after-shipment approval violations.
- The safe log exits `0` and creates an approval request instead of issuing the
  refund directly.

## Verification

Run the Stage 18 gate:

```bash
PYTHON=python3.12 ./tools/smoke_stage18_agent_examples.sh
```

The gate runs the MCP example, the HTTP example, the action-log fixtures, and
manifest validation for generated run artifacts.
