# Patch Hints: timeout_after_commit_retry

- Run ID: `sess_20260530T092502042629Z_SCN-002_382c2244`
- Status: `failed`

## idempotency_required_for_mutating_retries

- Severity: `critical`
- Root cause: The agent retried a mutating fulfillment action after timeout as a new request instead of treating the result as uncertain.
- Guardrails:
  - Use a stable idempotency key for create_fulfillment.
  - After timeout, query existing fulfillment state before retrying.
  - Never create a second fulfillment for the same order line without checking state.

## no_duplicate_fulfillment

- Severity: `critical`
- Root cause: The agent created more fulfillment quantity than the order line requires.
- Guardrails:
  - Check existing fulfillments by order_id and sku before creating another fulfillment.
  - Use order_id + sku + action_type as the stable fulfillment key.
