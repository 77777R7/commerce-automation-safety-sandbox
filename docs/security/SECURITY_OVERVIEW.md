# Security Overview

Commerce Automation Safety Sandbox is a pre-production crash-test layer for
commerce automation and AI agents. Stage 19 adds a hosted design-partner trust
boundary around the existing MCP/HTTP live agent sandbox.

The hosted POC boundary is intentionally narrow:

- No production store tokens.
- No real payment credentials.
- No real warehouse credentials.
- No real customer PII.
- Synthetic or redacted commerce data only.

Primary assets:

- Workspace-scoped sessions.
- Run artifacts: trace, policy report, state diff, report, patch hints, manifest.
- API tokens and token metadata.
- Audit logs.
- Export and deletion receipts.

Primary risks:

- Cross-tenant access to sessions or artifacts.
- Token scope bypass.
- Artifact URL leakage.
- Resource exhaustion through oversized requests or high request volume.
- Accidental upload of secrets or PII.

The Stage 19 gate verifies these risks through tests and smoke scripts rather
than policy prose alone.
