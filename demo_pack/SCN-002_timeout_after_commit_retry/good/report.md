# Commerce Safety Report: timeout_after_commit_retry

- Run ID: `run_20260529T053022722480Z_SCN-002_good_runner`
- Runner: `good_runner`
- Status: `passed`

## Executive Summary

The automation handled timeout-after-commit without creating a duplicate fulfillment.
It used a stable idempotency key and confirmed the already-committed fulfillment before retrying.

## State Change

- Fulfillments before: `0`
- Fulfillments after: `1`
- Fulfillment promises before: `0`
- Fulfillment promises after: `0`
- Refunds before: `0`
- Refunds after: `0`
- Approval requests before: `0`
- Approval requests after: `0`
- Inventory releases before: `0`
- Inventory releases after: `0`
- Workflow holds before: `0`
- Workflow holds after: `0`
- Warehouse cancellation requests before: `0`
- Warehouse cancellation requests after: `0`
- Refund amount issued before: `0`
- Refund amount issued after: `0`
- Reserved inventory before: `{'sku_retry_1': 1}`
- Reserved inventory after: `{'sku_retry_1': 1}`
- Expected reserved inventory: `{'sku_retry_1': 1}`

## Findings

No policy violations were detected.
## What Worked

The automation treated timeout-after-commit as an uncertain state, reused a stable idempotency key, and confirmed the committed fulfillment instead of creating another one.


## Replay

Run `commerce-safety replay runs/run_20260529T053022722480Z_SCN-002_good_runner` to print the recorded timeline from `trace.json`.
