# External Tester Quickstart

Use this when a collaborator, agency, or agent builder wants to test the demo
without connecting a real Shopify store, Amazon account, or customer data.

The goal is simple:

```txt
Run the same SCN-002 timeout-after-commit scenario twice.
Unsafe agent: blindly retries and fails.
Safe agent: uses idempotency/state lookup and passes.
```

## 1. Install

```bash
git clone https://github.com/77777R7/commerce-automation-safety-sandbox.git
cd commerce-automation-safety-sandbox

python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
chmod +x commerce-safety tools/*.sh
```

Python 3.10+ is required for the real MCP server. Python 3.12 is recommended.

## 2. Check Readiness

```bash
./commerce-safety doctor
```

For a full unsafe/safe MCP smoke test:

```bash
./commerce-safety doctor --mcp-smoke
```

Expected result:

```txt
Ready to connect an agent.
```

If you see `No module named 'mcp'`, activate the venv and run:

```bash
python -m pip install -r requirements.txt
```

## 3. Generate MCP Config

```bash
./commerce-safety mcp-config --python "$PWD/.venv/bin/python"
```

Paste the printed config into the MCP client. The important part is that
`PYTHONPATH` points to this repo's `commerce-safety-sandbox` directory.

For Codex or Claude Desktop users, the config can be installed directly:

```bash
./commerce-safety mcp-config --python "$PWD/.venv/bin/python" --install codex
./commerce-safety mcp-config --python "$PWD/.venv/bin/python" --install claude
```

## 4. Give The Agent This Prompt

Use:

```txt
demo_pack/prompts/scn002_mcp_agent_test.md
```

The agent should run:

- one unsafe path that fails with policy findings
- one safe path that passes with zero findings

You can also print the complete guided demo pack:

```bash
./commerce-safety demo scn002-agent --python "$PWD/.venv/bin/python"
```

## 5. What Good Looks Like

Unsafe path:

```txt
timeout_after_commit -> blind retry -> duplicate fulfillment
```

Expected findings:

- `idempotency_required_for_mutating_retries`
- `no_duplicate_fulfillment`

Safe path:

```txt
timeout_after_commit -> reuse stable idempotency key or find existing fulfillment
```

Expected findings:

- none

## 6. Why This Demo Matters

This shows the product's core loop:

```txt
External Agent -> MCP Twin -> Scenario Fault -> Policy Finding -> Patch Hints
```

The sandbox lets the bad action happen in a fake commerce world, then proves why
it would be dangerous in production. That is the difference between a normal
mock API and a commerce safety sandbox.
