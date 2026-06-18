# Data Flow

Hosted design-partner flow:

1. Design partner receives a workspace and API token.
2. Staging agent or workflow calls MCP/HTTP with the token.
3. The token resolves to workspace, role, and scopes.
4. The scenario starts a workspace-scoped live session.
5. The permissive twin accepts commerce actions and records timeline events.
6. Policy engine evaluates the final state on completion.
7. Artifacts are written under per-session storage.
8. Artifact download requires workspace authorization and signed URL validation.
9. Audit events record token, session, policy, artifact, export, and deletion actions.

No real Shopify, Amazon, Stripe, warehouse, or customer systems are called.
