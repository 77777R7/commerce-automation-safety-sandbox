# Commerce Safety Report: cancel_after_pick_pack_conflict

- Run ID: `run_20260529T055801621185Z_SCN-005_good_runner`
- Runner: `good_runner`
- Status: `passed`

## Business Risk Summary

- Risk: cancel_after_pick_pack_conflict completed without policy findings.
- Possible impact: No immediate commerce accident was detected in this run.
- Recommended control: Keep the same guardrails and rerun this scenario after automation changes.

## Executive Summary

The automation avoided the warehouse cancellation conflict.
It detected that the warehouse had already picked the order, placed the case on hold, and asked the warehouse to cancel before touching refund or inventory state.

## State Change

- Fulfillments before: `0`
- Fulfillments after: `0`
- Fulfillment promises before: `0`
- Fulfillment promises after: `0`
- Refunds before: `0`
- Refunds after: `0`
- Approval requests before: `0`
- Approval requests after: `0`
- Inventory releases before: `0`
- Inventory releases after: `0`
- Workflow holds before: `0`
- Workflow holds after: `1`
- Warehouse cancellation requests before: `0`
- Warehouse cancellation requests after: `1`
- Refund amount issued before: `0`
- Refund amount issued after: `0`
- Reserved inventory before: `{'sku_pickpack_1': 1}`
- Reserved inventory after: `{'sku_pickpack_1': 1}`
- Expected reserved inventory: `{'sku_pickpack_1': 1}`

## Findings

No policy violations were detected.
## What Worked

The automation recognized that cancellation was no longer a simple order update, held the workflow, and avoided refunding or releasing inventory while warehouse resolution was still pending.


## Replay

Run `commerce-safety replay runs/run_20260529T055801621185Z_SCN-005_good_runner` to print the recorded timeline from `trace.json`.
