# SCN-004 Policy Findings



Main accident: 订单已经发货且 carrier scanned，自动化仍直接退款。

Business loss: 钱货两失、高额退款失控、售后审批失效。



## Bad Runner Findings



### no_refund_after_shipment_without_approval

- Severity: `critical`
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



## Good Runner Findings



No policy findings.



## Recommended Fix



发货后退款和高额退款必须进入审批；审批前不得 issue refund。
