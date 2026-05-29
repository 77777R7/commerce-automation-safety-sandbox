# SCN-004 Refund After Shipment Approval Bypass - good_runner

- Run ID: `run_20260529T063819780760Z_SCN-004_good_runner`
- Status: `passed`
- Runner: `good_runner`
- Demo meaning: 通过：同一场景下没有产生 policy violation。

## 这次运行证明了什么

好流程发现已发货和高金额风险，创建审批并 hold refund。

## Accident Signals

- No accident signals were true.

## Timeline

1. Refund request refund_req_4001 received for order order_4001 in the amount of 120.
2. good_runner checks shipment state before refunding order order_4001.
3. good_runner creates approval request approval_001 before refunding order order_4001.
4. good_runner holds refund request refund_req_4001 until approval request approval_001 is reviewed.
5. Policy check passed with no violations.

## 原始系统报告

# Commerce Safety Report: refund_after_shipment_bypass

- Run ID: `run_20260529T063819780760Z_SCN-004_good_runner`
- Runner: `good_runner`
- Status: `passed`

## Business Risk Summary

- Risk: refund_after_shipment_bypass completed without policy findings.
- Possible impact: No immediate commerce accident was detected in this run.
- Recommended control: Keep the same guardrails and rerun this scenario after automation changes.

## Executive Summary

The automation avoided the post-shipment refund accident.
It detected that the order was already shipped, created an approval request, and held the refund for review.

## State Change

- Fulfillments before: `0`
- Fulfillments after: `0`
- Fulfillment promises before: `0`
- Fulfillment promises after: `0`
- Refunds before: `0`
- Refunds after: `0`
- Approval requests before: `0`
- Approval requests after: `1`
- Inventory releases before: `0`
- Inventory releases after: `0`
- Workflow holds before: `0`
- Workflow holds after: `0`
- Warehouse cancellation requests before: `0`
- Warehouse cancellation requests after: `0`
- Refund amount issued before: `0`
- Refund amount issued after: `0`
- Reserved inventory before: `{'sku_shipped_1': 0}`
- Reserved inventory after: `{'sku_shipped_1': 0}`
- Expected reserved inventory: `{'sku_shipped_1': 1}`

## Findings

No policy violations were detected.
## What Worked

The automation checked shipment state first, created an approval request, and avoided issuing a refund while the goods were already in transit.


## Replay

Run `commerce-safety replay runs/run_20260529T063819780760Z_SCN-004_good_runner` to print the recorded timeline from `trace.json`.
