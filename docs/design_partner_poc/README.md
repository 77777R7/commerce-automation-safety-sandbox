# Design Partner POC Package

This package is for AI commerce SaaS teams, automation agencies, and workflow
builders who want to test staging agents or automations before production.

The goal is not to connect your real store. The goal is to prove whether your
agent or workflow behaves safely when commerce state becomes messy:

```txt
External Agent or Workflow -> MCP/HTTP Twin -> Scenario Fault -> Policy Finding -> Patch Hints
```

Core principle:

```txt
Permissive Twin + Policy Check
```

## What You Get

- A hosted design-partner trust boundary.
- No-real-store testing rules.
- MCP and HTTP integration steps.
- Five P0 commerce accident scenarios.
- Example artifacts and report shapes.
- Clear POC success criteria.

## Who This Is For

Best fit:

- AI customer support or after-sales SaaS.
- n8n, Make, Zapier, or custom automation agencies.
- ERP, OMS, or WMS automation implementers.
- Shopify or Amazon app builders working around fulfillment, refunds, inventory, or order operations.

Not a fit yet:

- Pure FAQ bots without order, refund, fulfillment, or inventory permissions.
- Teams that need production store access on day one.
- Teams looking for a full Shopify or Amazon API clone.

## POC Flow

1. Read the hosted and no-real-store boundaries.
2. Pick one integration path: MCP or HTTP.
3. Run one smoke scenario, usually `SCN-002 timeout_after_commit_retry`.
4. Run all five P0 scenarios against your staging agent or workflow.
5. Review artifacts with us.
6. Decide whether to save failures as regression tests.
7. Decide whether the POC found enough risk to justify a paid pilot.

## Package Contents

- [Customer one-pager](one_pager.md)
- [Hosted boundary](hosted_boundary.md)
- [No-real-store boundary](no_real_store_boundary.md)
- [MCP/HTTP integration steps](integration_steps.md)
- [Five P0 scenarios](p0_scenarios.md)
- [Artifact and report examples](artifact_report_examples.md)
- [POC success criteria](poc_success_criteria.md)
- Sample artifact excerpts:
  - [trace excerpt](samples/trace_excerpt.json)
  - [policy report excerpt](samples/policy_report_excerpt.json)
  - [state diff excerpt](samples/state_diff_excerpt.json)
  - [report excerpt](samples/report_excerpt.md)

## One-Sentence Pitch

Commerce Safety Sandbox is a pre-production crash-test layer for commerce
automation and AI agents. It finds oversell, duplicate fulfillment, unsafe
retry, refund, and warehouse conflict risks before the agent touches a real
store.
