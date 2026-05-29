# SCN-001 Duplicate Webhook Fulfillment - good_runner

- Run ID: `run_20260529T053022712725Z_duplicate_webhook_good_runner`
- Status: `passed`
- Runner: `good_runner`
- Demo meaning: 通过：同一场景下没有产生 policy violation。

## 这次运行证明了什么

好流程先做 webhook dedupe，第二次收到同一 delivery 直接跳过。

## Accident Signals

- No accident signals were true.

## Timeline

1. Webhook wh_paid_001 received for order order_1001.
2. good_runner starts processing webhook wh_paid_001 with dedupe.
3. good_runner reserves 1 unit(s) of sku_widget_1; reserved inventory is now 1.
4. good_runner creates fulfillment ful_001 for order order_1001, sku sku_widget_1.
5. Webhook wh_paid_001 received for order order_1001.
6. good_runner skips duplicate webhook wh_paid_001.
7. Policy check passed with no violations.

## 原始系统报告

# Commerce Safety Report: Duplicate webhook creates duplicate fulfillment

- Run ID: `run_20260529T053022712725Z_duplicate_webhook_good_runner`
- Runner: `good_runner`
- Status: `passed`

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

Run `commerce-safety replay runs/run_20260529T053022712725Z_duplicate_webhook_good_runner` to print the recorded timeline from `trace.json`.
