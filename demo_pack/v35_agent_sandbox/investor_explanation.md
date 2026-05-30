# Investor Explanation: V3.5 Live Agent Sandbox

## Thesis

AI commerce agents are moving from chat to operations. They will issue refunds, promise fulfillment, update inventory, process webhooks, retry APIs, and interact with warehouse workflows. The risk is not only prompt safety. The risk is business-state safety.

## Product

Commerce Automation Safety Sandbox is a pre-production crash-test layer for commerce automation and AI agents.

```txt
External Agent -> MCP/HTTP Twin -> Scenario Fault -> Policy Finding -> Patch Hints
```

The product uses permissive stateful twins. Bad actions are allowed to mutate sandbox state. The policy engine then detects whether the resulting state is a real commerce incident.

## Why This Is Different From A Mock Server

A mock server checks whether an API call has the right shape. This platform checks whether an automation created a bad business outcome across order, inventory, refund, fulfillment, warehouse, webhook, and retry state.

## V3.5 Proof Points

- Shopify-like skin: duplicate webhook and timeout-after-commit fulfillment accidents.
- Amazon Seller Ops skin: stale inventory promise and cancel-after-pick/pack warehouse conflict.
- MCP interface: agent-native tool calls for session start, twin actions, trace, policy, and patch hints.
- OpenAPI HTTP Twin API: workflow/script integration path.
- Agent-readable repair artifacts: `policy_report.json`, `trace.json`, `patch_hints.md`, `agent_summary.md`, `failure_explain.md`.

## Wedge

Start with AI agent builders, automation agencies, ERP/OMS/WMS implementers, and operational ecommerce teams that already know one bad workflow can create money or inventory loss.

## Moat

The moat is not breadth of platform clones. It is commerce incident semantics:

- real accident scenario library,
- stateful commerce twin behavior,
- policy oracle for business rules,
- trace replay,
- agent-readable repair loop,
- customer-specific regression scenarios.

## Gate

The release rule is direct: if a scenario run has policy findings, the automation should not ship.
