# SCN-004 Refund After Shipment Approval Bypass - bad_runner

- Run ID: `run_20260529T195554905642Z_SCN-004_bad_runner`
- Status: `failed`
- Runner: `bad_runner`
- Demo meaning: 失败：Policy Engine 抓到了真实业务事故。

## 这次运行证明了什么

坏流程不检查 shipment state，也不创建 approval request，直接 issue refund。

## Accident Signals

- `post_shipment_refund_without_approval`: `True`
- `high_value_refund_without_approval`: `True`

## Timeline

1. Refund request refund_req_4001 received for order order_4001 in the amount of 120.
2. bad_runner starts refund request refund_req_4001 without checking shipment approval requirements.
3. bad_runner issues refund refund_001 for order order_4001 without blocking platform mutation.
4. Policy violation detected: no_refund_after_shipment_without_approval (critical).
5. Policy violation detected: high_value_refund_requires_approval (high).

## 原始系统报告

# Commerce Safety Report: refund_after_shipment_bypass

- Run ID: `run_20260529T195554905642Z_SCN-004_bad_runner`
- Runner: `bad_runner`
- Status: `failed`

## Business Risk Summary

- Risk: refund_after_shipment_bypass triggered `no_refund_after_shipment_without_approval`.
- Possible impact: The automation issued a refund after the shipment had already left the controllable fulfillment stage. This can create money-plus-goods loss and manual recovery work.
- Recommended control: When an order is shipped or carrier-scanned, create an approval request and hold the refund until a reviewer confirms the correct after-shipment action.

## Executive Summary

The automation created a high-risk post-shipment refund incident.
It issued money back after the parcel had already been carrier-scanned, without requiring approval.

## State Change

- Fulfillments before: `0`
- Fulfillments after: `0`
- Fulfillment promises before: `0`
- Fulfillment promises after: `0`
- Refunds before: `0`
- Refunds after: `1`
- Approval requests before: `0`
- Approval requests after: `0`
- Inventory releases before: `0`
- Inventory releases after: `0`
- Workflow holds before: `0`
- Workflow holds after: `0`
- Warehouse cancellation requests before: `0`
- Warehouse cancellation requests after: `0`
- Refund amount issued before: `0`
- Refund amount issued after: `120.0`
- Reserved inventory before: `{'sku_shipped_1': 0}`
- Reserved inventory after: `{'sku_shipped_1': 0}`
- Expected reserved inventory: `{'sku_shipped_1': 1}`

## Findings

### no_refund_after_shipment_without_approval

- Severity: `critical`
- Status: `failed`
- Business impact: The automation issued a refund after the shipment had already left the controllable fulfillment stage. This can create money-plus-goods loss and manual recovery work.
- Recommendation: When an order is shipped or carrier-scanned, create an approval request and hold the refund until a reviewer confirms the correct after-shipment action.

Evidence:

```json
{
  "refund_id": "refund_001",
  "order_id": "order_4001",
  "amount": 120.0,
  "reason": "buyer_changed_mind",
  "fulfillment_status_at_issue": "shipped",
  "shipment_status_at_issue": "carrier_scanned",
  "approval_id": null,
  "approved_by": null,
  "source_event_id": "refund_req_4001"
}
```

### high_value_refund_requires_approval

- Severity: `high`
- Status: `failed`
- Business impact: The automation issued a high-value refund without approval, increasing avoidable cash-loss and fraud risk.
- Recommendation: Route refunds at or above the high-value threshold into an approval workflow before issuing money back to the buyer.

Evidence:

```json
{
  "refund_id": "refund_001",
  "order_id": "order_4001",
  "amount": 120.0,
  "threshold": 100.0,
  "approval_id": null,
  "approved_by": null,
  "source_event_id": "refund_req_4001"
}
```

## How To Fix

Treat shipped or carrier-scanned orders as approval-required before issuing refunds. Create a review task, keep the refund pending, and only issue money after an authorized reviewer confirms the right after-shipment action.


## Replay

Run `commerce-safety replay runs/run_20260529T195554905642Z_SCN-004_bad_runner` to print the recorded timeline from `trace.json`.
