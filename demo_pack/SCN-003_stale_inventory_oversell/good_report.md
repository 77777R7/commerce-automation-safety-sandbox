# SCN-003 Stale Inventory Oversell - good_runner

- Run ID: `run_20260529T053022732737Z_SCN-003_good_runner`
- Status: `passed`
- Runner: `good_runner`
- Demo meaning: 通过：同一场景下没有产生 policy violation。

## 这次运行证明了什么

好流程刷新库存，发现 true available=0 后转人工 review。

## Accident Signals

- No accident signals were true.

## Timeline

1. Inventory promise task task_promise_3001 received for order order_3001 with fault stale_inventory_snapshot.
2. good_runner refreshes inventory for sku_stale_1; available is now 0.
3. good_runner routes order order_3001, sku sku_stale_1 to manual review.
4. Policy check passed with no violations.

## 原始系统报告

# Commerce Safety Report: stale_inventory_oversell

- Run ID: `run_20260529T053022732737Z_SCN-003_good_runner`
- Runner: `good_runner`
- Status: `passed`

## Executive Summary

The automation avoided the stale inventory oversell.
It refreshed inventory first, saw no fresh availability, and routed the order to manual review instead of promising fulfillment.

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
- Workflow holds after: `0`
- Warehouse cancellation requests before: `0`
- Warehouse cancellation requests after: `0`
- Refund amount issued before: `0`
- Refund amount issued after: `0`
- Reserved inventory before: `{'sku_stale_1': 1}`
- Reserved inventory after: `{'sku_stale_1': 1}`
- Expected reserved inventory: `{'sku_stale_1': 1}`

## Findings

No policy violations were detected.
## What Worked

The automation treated stale inventory as unsafe, refreshed the snapshot, and avoided promising fulfillment when true availability was zero.


## Replay

Run `commerce-safety replay runs/run_20260529T053022732737Z_SCN-003_good_runner` to print the recorded timeline from `trace.json`.
