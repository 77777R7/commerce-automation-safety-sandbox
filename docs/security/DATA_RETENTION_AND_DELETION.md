# Data Retention And Deletion

Stage 19 hosted sessions include TTL and retention metadata.

Session controls:

- `ttl_expires_at` blocks late writes after session expiry.
- `retention_expires_at` is written to the run manifest for generated artifacts.

Deletion controls:

- Workspace deletion revokes workspace tokens.
- Deletion produces a `DeletionReceipt`.
- A minimal tombstone may remain to prove deletion occurred.

This is POC retention governance, not a full legal retention program.
