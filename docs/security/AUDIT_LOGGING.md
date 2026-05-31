# Audit Logging

Stage 19 records audit events for hosted POC accountability.

Required event types:

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

Audit logs are workspace-scoped and are included in workspace export metadata.
Token secrets are never exported.
