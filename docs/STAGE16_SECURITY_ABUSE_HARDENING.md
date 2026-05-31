# Stage 16: Security / Abuse Hardening

Stage 16 hardens the local V3.5 agent-facing surface against accidental exposure
and low-effort abuse. It does not add a new platform skin or hosted control
plane.

## Threat Model

Assets that matter:

- Local scenario state and generated run artifacts.
- API tokens used to protect local HTTP sessions.
- Agent-readable traces and reports.
- Developer machines and CI logs.
- The integrity of `Permissive Twin + Policy Check`.

Trust boundaries:

- External agents call MCP tools or the HTTP Twin API.
- HTTP callers can provide scenario ids, action payloads, Shopify/Amazon-shaped
  payloads, and action logs.
- Scenario YAML files are trusted only when resolved through the repo scenario
  registry.
- Demo artifacts are not trusted source and remain outside source PR review.

Repository-wide invariants:

- The live HTTP server must not bind to a non-loopback interface unless an API
  token is configured.
- HTTP responses should use no-store and nosniff headers, and should not add
  wildcard CORS by default.
- HTTP JSON request bodies and JSONL action logs must have bounded sizes.
- Agent-facing errors must not leak personal local filesystem paths.
- Source files must not contain real-looking production secrets.
- The twin remains permissive: unsafe commerce actions still mutate state, and
  policy evaluation catches the incident afterward.

## Implemented Controls

- `validate_live_server_security` rejects `0.0.0.0` or other non-loopback
  server binds without `--api-token` or `COMMERCE_SAFETY_API_TOKEN`.
- HTTP auth comparisons use constant-time token comparison.
- HTTP JSON bodies are capped at one megabyte and return
  `request_body_too_large` when exceeded.
- HTTP responses include:
  - `Cache-Control: no-store`
  - `X-Content-Type-Options: nosniff`
- Scenario path rejection copy no longer includes absolute local paths.
- JSONL action logs are capped by byte size and action count.
- MCP `streamable-http` transport is disabled until host binding and auth
  policy are explicitly gated. Local V3.5 MCP examples use stdio.
- `security_hardening.yaml` defines high-confidence secret patterns and banned
  response fragments for source scanning.

## Gate

Run:

```bash
PYTHON=python3.12 ./tools/smoke_stage16_security_abuse.sh
```

The full V3.5 release gate includes Stage 16:

```bash
PYTHON=python3.12 ./tools/smoke_v35.sh
```

## Non-Goals

- No hosted auth system.
- No tenant isolation or billing authorization.
- No agent container, egress proxy, Firecracker, or gVisor runtime.
- No OAuth, SigV4, Shopify OAuth, or production platform credential handling.
- No buyer simulator or autonomous red-team buyer.
