# Sales One-Pager

## Product

Commerce Automation Safety Sandbox is a pre-production crash test layer for commerce automation and AI agents.

## Customer Promise

We help ecommerce teams find business accidents before automation touches real orders, inventory, refunds, fulfillment, warehouse tasks, or customer promises.

## Why Now

Commerce teams are adding rules, workflows, and AI agents to operations that move money and goods. Official sandboxes mostly test API functionality. They do not prove that a retry, duplicate webhook, stale inventory snapshot, refund request, or warehouse race leaves the business state safe.

## What The Demo Proves

- Bad automation is allowed to mutate state inside a permissive twin.
- The policy engine catches the resulting incident from trace and state diff.
- Good automation passes the same scenario, proving the gate is about safety controls rather than unrealistic test conditions.
- Reports explain what happened, why it matters, and how to fix it.

## Five P0 Accident Classes

- SCN-001 Duplicate Webhook Fulfillment: 重复发货、重复扣库存、重复仓库通知和客服追损。
- SCN-002 Timeout After Commit Unsafe Retry: 重复 fulfillment、重复出库、额外运费和库存损失。
- SCN-003 Stale Inventory Oversell: 超卖、取消订单、差评、补偿和客服工单。
- SCN-004 Refund After Shipment Approval Bypass: 钱货两失、高额退款失控、售后审批失效。
- SCN-005 Cancel After Pick/Pack Warehouse Conflict: 退款后仍发货、库存释放错误、仓库追货和账实不一致。

## First Sellable Wedge

Offline Fulfillment Automation Audit.

A seller, agency, ERP implementer, or automation team provides CSV/XLSX exports. We reconstruct order, inventory, fulfillment, refund, and warehouse state, then return a risk report before a promotion or automation rollout.

## POC Ask

$500-$2,000 for one audit package:

- Four exports: orders, inventory, fulfillments, refunds.
- One data mapping pass.
- One risk report.
- One review call.
- Three to five recommended fixes.

## Expansion Path

After the first audit, convert repeated failures into regression scenarios, then open Live Commerce Agent Validation for workflows, scripts, and AI agents.
