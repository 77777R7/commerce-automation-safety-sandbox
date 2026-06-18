# Access Review

Stage 19 access review is designed for 1-3 hosted design partners.

Review cadence:

- Before issuing a design-partner token.
- At the end of each POC.
- Immediately after any suspected token leak or accidental production workflow connection.

Review checklist:

- Workspace owner is known.
- Issued tokens have the narrowest role that works.
- `agent_token` is used for staging agents and workflows.
- `owner` token is not used by automation.
- Expired or unused tokens are revoked.
- Suspended or deleted workspaces have no active tokens.
- Export and deletion receipts are retained when applicable.

Evidence:

- Token metadata in workspace export.
- `token.created` and `token.revoked` audit events.
- `workspace.suspended`, `workspace.delete_requested`, and `workspace.deleted` audit events.
