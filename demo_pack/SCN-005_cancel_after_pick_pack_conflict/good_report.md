# SCN-005 Cancel After Pick/Pack Warehouse Conflict - good_runner

- Run ID: `run_20260529T053022755031Z_SCN-005_good_runner`
- Status: `passed`
- Runner: `good_runner`
- Demo meaning: 通过：同一场景下没有产生 policy violation。

## 这次运行证明了什么

好流程识别 warehouse conflict，创建 hold，并向仓库提交 cancellation request。

## Accident Signals

- No accident signals were true.

## Timeline

1. Cancel request cancel_req_5001 received for order order_5001.
2. good_runner checks warehouse progress before resolving cancel request cancel_req_5001.
3. good_runner places order order_5001 on hold for warehouse_pick_pack_conflict.
4. good_runner asks warehouse to cancel job wh_job_5001 while status is picked.
5. good_runner does not refund, release inventory, or mark order order_5001 cancelled until warehouse confirms the stop.
6. Policy check passed with no violations.

## 原始系统报告

# Commerce Safety Report: cancel_after_pick_pack_conflict

- Run ID: `run_20260529T053022755031Z_SCN-005_good_runner`
- Runner: `good_runner`
- Status: `passed`

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

Run `commerce-safety replay runs/run_20260529T053022755031Z_SCN-005_good_runner` to print the recorded timeline from `trace.json`.
