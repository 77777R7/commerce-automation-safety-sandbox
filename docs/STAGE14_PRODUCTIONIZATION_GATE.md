# Stage 14: Productionization Gate

Stage 14 turns the V3.5 live-agent sandbox from a local demo surface into a
safer external-agent integration surface. It does not add a new platform skin.

## Scope

- Scenario loading must go through the scenario registry.
- HTTP sessions may be protected by a local API token.
- Session state must stay isolated, including Amazon feed state.
- HTTP protocol errors must use one error envelope.
- V3.5 gates must fail early on unsupported Python versions.
- Amazon Seller Ops OpenAPI responses should use named response schemas instead
  of the old broad `AmazonGenericResponse`.

## Scenario Registry

External agents should start sessions by `scenario_id` when possible:

```json
{"scenario_id": "SCN-002"}
```

`scenario_path` is still accepted for existing local harnesses, but only when
the path resolves under `commerce-safety-sandbox/scenarios`.

## Local Auth

The HTTP server stays local-first, but can require a token:

```bash
./commerce-safety live serve --api-token local-dev-token
```

Clients then send either:

```txt
Authorization: Bearer local-dev-token
```

or:

```txt
X-Commerce-Safety-Token: local-dev-token
```

## Error Envelope

HTTP protocol errors use:

```json
{
  "ok": false,
  "error": {
    "code": "session_not_found",
    "message": "Live session not found: sess_missing",
    "status": 404
  }
}
```

Business-fault responses, such as `timeout_after_commit` or a simulated Amazon
429, can still return their domain-specific bodies because those are part of the
scenario behavior.

## PR Split

Use two review units when preparing this for merge:

1. `source PR`: runtime code, tests, OpenAPI, docs, smoke gates, and harnesses.
2. `generated artifacts PR`: regenerated `demo_pack/` and `demo_viewer/`
   collateral.

Keeping generated artifacts out of the source PR makes reviewable risk small and
prevents demo collateral churn from hiding runtime changes.

## Current Non-Goals

- No new Shopify/Amazon surface area.
- No hosted multi-tenant control plane.
- No buyer simulator.
- No Firecracker, gVisor, or agent container runtime.
