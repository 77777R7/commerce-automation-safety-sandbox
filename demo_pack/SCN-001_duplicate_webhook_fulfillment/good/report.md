# Commerce Safety Report: Duplicate webhook creates duplicate fulfillment

- Run ID: `run_20260529T055801576327Z_duplicate_webhook_good_runner`
- Runner: `good_runner`
- Status: `passed`

## Business Risk Summary

- Risk: Duplicate webhook creates duplicate fulfillment completed without policy findings.
- Possible impact: No immediate commerce accident was detected in this run.
- Recommended control: Keep the same guardrails and rerun this scenario after automation changes.

## Executive Summary

The automation handled the scenario without creating a business accident.
The final commerce state stayed within policy.

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
- Reserved inventory before: `{'sku_widget_1': 0}`
- Reserved inventory after: `{'sku_widget_1': 1}`
- Expected reserved inventory: `{'sku_widget_1': 1}`

## Findings

No policy violations were detected.
## What Worked

The automation avoided unsafe duplicate mutation and kept the state within policy.

## Replay

Run `commerce-safety replay runs/run_20260529T055801576327Z_duplicate_webhook_good_runner` to print the recorded timeline from `trace.json`.
