# Hosted Boundary

The hosted POC is a design-partner trust boundary, not a production commerce
processor and not SOC2 certification.

## What The Hosted Boundary Provides

- Private workspace for the design partner.
- API token authentication.
- Minimal roles and scopes.
- Workspace-scoped sessions.
- Workspace-scoped artifacts.
- Session TTL.
- Artifact retention metadata.
- Audit logs for key actions.
- Signed artifact download URLs.
- Token revoke and workspace suspend kill switch.

## What It Does Not Provide

- Production Shopify, Amazon, Stripe, or warehouse connectivity.
- SSO/SAML.
- Billing.
- Enterprise admin console.
- VPC/private deployment.
- Formal SOC2 report.
- Firecracker, gVisor, or untrusted code runtime isolation.

## Trust Boundary Model

```txt
Design Partner Token
        |
        v
Workspace Context
        |
        v
Hosted Session
        |
        v
Permissive Commerce Twin
        |
        v
Policy Engine + Artifacts
```

Workspace ids come from the authenticated token context. A request body cannot
choose another workspace.

## What We Log

We audit:

- token creation and revoke
- session create and complete
- MCP tool calls
- HTTP twin actions
- policy report generation
- artifact downloads
- workspace export and deletion
- auth failures
- authorization denials
- rate-limit events
- PII and secret warnings

## Kill Switch

If anything looks wrong:

1. Revoke the API token.
2. Suspend the workspace.
3. Abort active sessions.
4. Export audit logs.
5. Delete workspace data if requested.
