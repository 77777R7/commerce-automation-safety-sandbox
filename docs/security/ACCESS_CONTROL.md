# Access Control

Stage 19 uses API token auth for hosted POC access.

Roles:

- `owner`: full POC workspace control.
- `operator`: can run sessions and view reports/artifacts.
- `viewer`: can view sessions/reports/artifacts only.
- `agent_token`: can start and operate sessions, but cannot export workspace data or read artifacts by default.

Scopes:

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

Workspace ids are taken from the authenticated token context. They are not
trusted from request bodies.
