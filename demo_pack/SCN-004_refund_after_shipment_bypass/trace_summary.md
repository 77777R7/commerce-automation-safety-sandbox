# SCN-004 Trace Summary

Main accident: 订单已经发货且 carrier scanned，自动化仍直接退款。

## Bad Runner Timeline

1. Refund request refund_req_4001 received for order order_4001 in the amount of 120.
2. bad_runner starts refund request refund_req_4001 without checking shipment approval requirements.
3. bad_runner issues refund refund_001 for order order_4001 without blocking platform mutation.
4. Policy violation detected: no_refund_after_shipment_without_approval (critical).
5. Policy violation detected: high_value_refund_requires_approval (high).

## Good Runner Timeline

1. Refund request refund_req_4001 received for order order_4001 in the amount of 120.
2. good_runner checks shipment state before refunding order order_4001.
3. good_runner creates approval request approval_001 before refunding order order_4001.
4. good_runner holds refund request refund_req_4001 until approval request approval_001 is reviewed.
5. Policy check passed with no violations.

## Why The Difference Matters

- Bad path: 坏流程不检查 shipment state，也不创建 approval request，直接 issue refund。
- Good path: 好流程发现已发货和高金额风险，创建审批并 hold refund。
- Gate: 上线前模拟 shipped refund request；只要直接退款，就阻止发布。
