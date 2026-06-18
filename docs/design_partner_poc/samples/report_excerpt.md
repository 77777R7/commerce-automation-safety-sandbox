## Business Risk Summary

Risk: The automation retried a fulfillment after a timeout even though the first request had already committed.

Possible impact: duplicate shipment, extra shipping cost, inventory loss, and customer confusion.

Recommended control: use a stable idempotency key and verify current fulfillment state before retrying.

## What Happened

Principle: Permissive Twin + Policy Check.

The permissive twin allowed the unsafe retry to mutate state so the policy engine could detect the resulting business incident. This is intentional: the POC tests whether the automation creates unsafe commerce state, not whether a mock API rejects a request early.
