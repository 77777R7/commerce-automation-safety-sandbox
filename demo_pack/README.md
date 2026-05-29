# Demo Pack Reader Guide

Start with `executive_summary.md`. For sales calls, use `sales_one_pager.md` and `demo_walkthrough.md`. Then open any scenario's `trace_summary.md` and `policy_findings.md`.

## Sales Materials

- [Executive summary](executive_summary.md)
- [Sales one-pager](sales_one_pager.md)
- [Demo walkthrough](demo_walkthrough.md)

## Scenarios

- [SCN-001 Duplicate Webhook Fulfillment](SCN-001_duplicate_webhook_fulfillment/trace_summary.md)
- [SCN-002 Timeout After Commit Unsafe Retry](SCN-002_timeout_after_commit_retry/trace_summary.md)
- [SCN-003 Stale Inventory Oversell](SCN-003_stale_inventory_oversell/trace_summary.md)
- [SCN-004 Refund After Shipment Approval Bypass](SCN-004_refund_after_shipment_bypass/trace_summary.md)
- [SCN-005 Cancel After Pick/Pack Warehouse Conflict](SCN-005_cancel_after_pick_pack_conflict/trace_summary.md)

## Artifact Contract

For every scenario, `bad/` and `good/` each contain the four raw run artifacts:

- `trace.json`
- `policy_report.json`
- `state_diff.json`
- `report.md`
