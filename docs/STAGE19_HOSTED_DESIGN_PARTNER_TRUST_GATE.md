# Stage 19: Hosted Design Partner Trust Gate

Stage 19 makes the hosted commerce agent sandbox safe enough for 1-3 design
partners to connect staging agents or workflows to MCP/HTTP without giving us
production store access.

This is a trust boundary for hosted POCs. It is not SOC2 certification, a full
enterprise SaaS control plane, SSO/SAML, billing, VPC deployment, microVM
runtime work, or dashboard polish.

## No-Real-Store Boundary

Allowed:

- Staging agents.
- Test workflows.
- Synthetic order, inventory, refund, warehouse, and buyer-message data.
- Fake Shopify-like payloads.
- Fake Amazon seller-ops payloads.
- Action logs.
- Redacted sample data.

Not allowed:

- Production Shopify tokens.
- Production Amazon SP-API credentials.
- Real Stripe secrets.
- Real warehouse credentials.
- Real customer PII.
- Live refund, fulfillment, or payment credentials.

## Modules

### 19A Workspace & Tenant Boundary

Every hosted session and artifact is bound to a workspace. Workspace ids are
derived from the authenticated token context, not trusted from request bodies.

Required model concepts:

- `Workspace`
- `User`
- `ApiToken`
- `Session`
- `Artifact`
- `AuditEvent`
- `DeletionReceipt`

Required controls:

- Each hosted session has `workspace_id`.
- Each hosted run artifact has `workspace_id`, `session_id`, and retention metadata.
- A token from workspace A cannot read, complete, or download artifacts from workspace B.
- Guessing a session id does not bypass object-level authorization.

### 19B Auth, RBAC & Token Scopes

Minimum roles:

- `owner`
- `operator`
- `viewer`
- `agent_token`

Minimum scopes:

- `sessions:create`
- `sessions:read`
- `twin:call`
- `mcp:call`
- `reports:read`
- `artifacts:read`
- `workspace:export`
- `workspace:delete`
- `tokens:manage`
- `audit:read`

Required behavior:

- No token, invalid token, expired token, and revoked token return `401`.
- Valid token with the wrong scope returns `403`.
- `viewer` cannot create sessions.
- `agent_token` cannot export workspace data.

### 19C Hosted Session Runtime & Artifact Security

Hosted sessions reuse the permissive commerce twin and policy engine, but add
workspace-scoped storage and artifact governance.

Required controls:

- Per-session run storage.
- `run_manifest.json` with workspace, session, artifact, hash, and retention metadata.
- Artifact SHA-256.
- Signed artifact download URLs.
- Signed URL expiry.
- Session TTL.
- Artifact retention expiry.

### 19D Audit, Retention, Export & Deletion

Audit events must cover:

- `workspace.created`
- `token.created`
- `token.revoked`
- `session.created`
- `session.completed`
- `mcp.tool_called`
- `http.twin_action_called`
- `policy_report.generated`
- `artifact.downloaded`
- `workspace.export_requested`
- `workspace.delete_requested`
- `workspace.deleted`
- `rate_limit.exceeded`
- `pii.warning_detected`
- `secret.warning_detected`
- `auth.failed`
- `authorization.denied`

Deletion produces a `DeletionReceipt`. Export returns token metadata but never
token secrets.

### 19E POC Security Evidence Binder

The Stage 19 evidence binder lives in `docs/security/`. It is POC security
evidence, not a SOC2 report.

Required docs:

- `SECURITY_OVERVIEW.md`
- `CONTROL_MATRIX.md`
- `DATA_FLOW.md`
- `ACCESS_CONTROL.md`
- `AUDIT_LOGGING.md`
- `DATA_RETENTION_AND_DELETION.md`
- `ACCESS_REVIEW.md`
- `CHANGE_MANAGEMENT.md`
- `INCIDENT_RESPONSE.md`
- `VENDOR_INVENTORY.md`
- `DESIGN_PARTNER_DPA_NOTES.md`
- `../HOSTED_DESIGN_PARTNER_ONBOARDING.md`

### 19F Design Partner Onboarding & Kill Switch

Minimum hosted beta flow:

1. Create private workspace.
2. Create API token.
3. Choose scenario pack.
4. Choose platform skin: `generic`, `shopify_like`, or `amazon_seller_ops`.
5. Run smoke scenario.
6. View report.
7. Download artifacts.
8. Revoke token.
9. Export or delete workspace data.

Kill switch controls:

- `workspace.status = suspended`
- `token.revoked_at`
- `session.status = aborted`

## Stage 19 Gate

Primary gate:

```bash
PYTHON=python3.12 ./tools/smoke_stage19_hosted_enterprise_poc.sh
```

Sub-gates:

```bash
PYTHON=python3.12 ./tools/smoke_stage19_release_candidate.sh
PYTHON=python3.12 ./tools/smoke_stage19_auth_rbac.sh
PYTHON=python3.12 ./tools/smoke_stage19_tenant_isolation.sh
PYTHON=python3.12 ./tools/smoke_stage19_artifacts_audit.sh
PYTHON=python3.12 ./tools/smoke_stage19_limits_redaction.sh
PYTHON=python3.12 ./tools/smoke_stage19_p0_hosted_live.sh
```

The gate verifies:

1. no token -> `401`
2. invalid token -> `401`
3. expired token -> `401`
4. revoked token -> `401`
5. wrong scope -> `403`
6. viewer cannot create session
7. agent token cannot export workspace
8. workspace A cannot read workspace B session
9. workspace A cannot complete workspace B session
10. workspace A cannot download workspace B artifact
11. guessed session id still blocked
12. `run_manifest.json` includes workspace/session/retention metadata
13. artifact has SHA-256
14. signed URL expires
15. artifact access is logged
16. oversized request is rejected
17. rate limit triggers
18. session TTL blocks late writes
19. PII/secret scan warning is generated
20. export/delete flow produces a receipt
21. five P0 scenarios still pass through hosted MCP/HTTP paths

## Stop Line

After Stage 19 passes, stop platform engineering. Do not continue to full SOC2,
SSO/SAML, billing, admin console, VPC/private deployment, microVM runtime,
or more skins unless a design partner explicitly requires it.

The next action is design-partner validation: connect 1-3 real staging
agents/workflows, collect incident feedback, and validate paid POC willingness.
