# Arga-Style Next Layer

Stage 8 is planning-only in this branch. Do not start implementation until the
next-layer work is split into separate goals, each with its own gate.

The V3.5 baseline is now:

```txt
External Agent -> MCP/HTTP Twin -> Scenario Fault -> Policy Finding -> Patch Hints
```

## Sub-Goals

### 1. GitHub Actions gate

Turn `commerce-safety gate` into a clean CI primitive that can run from GitHub
Actions against action logs or live validation scripts.

Gate:

```bash
./tools/smoke_github_actions_gate.sh
```

### 2. PR check

Create a GitHub PR check that reports commerce findings, artifacts, and replay
commands on pull requests.

Gate:

```bash
./tools/smoke_pr_check.sh
```

### 3. Scenario registry

Add a registry that can list scenarios, filter by risk category, and identify
which live actions each scenario needs.

Gate:

```bash
./tools/smoke_scenario_registry.sh
```

### 4. Stub coverage

Track contract-only or not-yet-stateful endpoints so the product can say which
actions are real stateful twins and which are placeholders. Stub coverage must
be visible in reports.

Gate:

```bash
./tools/smoke_stub_coverage.sh
```

### 5. Trace streaming

Add SSE or WebSocket style live events after the local trace model is stable.
The first target should be agent-readable event streaming, not a dashboard.

Gate:

```bash
./tools/smoke_trace_streaming.sh
```

### 6. Hosted sessions

Move from local sessions to hosted sessions with TTL, quotas, and isolation.
This is where runtime isolation decisions become relevant.

Gate:

```bash
./tools/smoke_hosted_sessions.sh
```

### 7. Team workspace

Add shared runs, scenario libraries, trace retention, and team-level access
controls.

Gate:

```bash
./tools/smoke_team_workspace.sh
```

### 8. MCP transport wrapper

Wrap the Stage 3 tool semantics in a real MCP transport without changing the
tool payload contract.

Gate:

```bash
./tools/smoke_mcp_transport.sh
```

## Non-Goals For This Branch

- Do not implement PR checks here.
- Do not build hosted infrastructure here.
- Do not add Shopify/Amazon full skins here.
- Do not add buyer simulator here.

Stage 8 exists to prevent vague platform sprawl. Each next-layer item must
become its own goal before implementation. The next goals are GitHub Actions
gate, PR check, scenario registry, stub coverage, trace streaming, hosted
sessions, team workspace, and MCP transport wrapper.
