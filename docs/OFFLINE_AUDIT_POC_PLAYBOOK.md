# Offline Fulfillment Automation Audit POC Playbook

## POC Offer

`Offline Fulfillment Automation Audit` is a lightweight accident review for
commerce teams before a promotion, ERP workflow change, warehouse process
change, or automation launch.

The buyer is not purchasing a sandbox. They are purchasing an incident checkup:

```txt
Can our current order, inventory, fulfillment, refund, and warehouse state
produce expensive automation accidents?
```

## Ideal First Customers

- Technical ecommerce agencies.
- Cross-border ERP / OMS / WMS implementation teams.
- n8n / Make / Zapier ecommerce automation agencies.
- AI support or after-sales SaaS teams with refund or reship permissions.

Avoid the first POC if the prospect only has FAQ automation, marketing-only
apps, or no order/inventory/refund authority.

## Data Request

Ask for four exports. CSV is best; XLSX is supported.

Use the starter files in `poc_templates/` when a customer does not already have
exports in this shape.

`orders`

```txt
order_id
buyer_id
sku
quantity
payment_status
order_status
created_at
```

`inventory`

```txt
sku
on_hand
reserved
warehouse
```

`fulfillments`

```txt
order_id
sku
quantity
fulfillment_status
tracking_number
warehouse_status
```

`refunds`

```txt
order_id
amount
refund_status
reason
approved_by
```

## Privacy Boundary

- Buyer identifiers are redacted in saved audit inputs.
- The POC does not need API credentials.
- The POC does not touch live Shopify, Amazon, ERP, WMS, or payment systems.
- Raw customer exports should not be committed to the repo.
- First-version POCs should only include the canonical fields listed above.
- Do not upload email, phone, address, customer name, shipping address, billing
  address, or free-form customer notes.
- If a customer must export sensitive fields, remove or redact them before the
  file reaches this tool.

## Local Sample Run

Risk sample:

```bash
./commerce-safety offline-audit \
  --orders commerce-safety-sandbox/offline_samples/p0_audit/orders.csv \
  --inventory commerce-safety-sandbox/offline_samples/p0_audit/inventory.csv \
  --fulfillments commerce-safety-sandbox/offline_samples/p0_audit/fulfillments.csv \
  --refunds commerce-safety-sandbox/offline_samples/p0_audit/refunds.csv \
  --mapping commerce-safety-sandbox/offline_samples/p0_audit/mapping.yaml
```

Clean sample:

```bash
./commerce-safety offline-audit \
  --orders commerce-safety-sandbox/offline_samples/clean_audit/orders.csv \
  --inventory commerce-safety-sandbox/offline_samples/clean_audit/inventory.csv \
  --fulfillments commerce-safety-sandbox/offline_samples/clean_audit/fulfillments.csv \
  --refunds commerce-safety-sandbox/offline_samples/clean_audit/refunds.csv
```

## POC Deliverables

Deliver one audit folder with:

- `manifest.json`
- `data_quality.json`
- `state_reconstruction.json`
- `policy_report.json`
- `report.md`
- `redacted_inputs/*.csv`

Also prepare a call summary with:

- Top risks.
- Affected order or SKU patterns.
- Likely business loss.
- Recommended process or automation guardrails.
- Suggested regression scenarios to save later.

## Operator Report Structure

The customer-facing report should answer:

1. What is the overall risk score?
2. Which accidents did we find?
3. Which orders, SKUs, warehouse statuses, or refund patterns triggered risk?
4. What money, inventory, or customer support loss could happen?
5. What should be fixed before the next automation change?

## First POC Success Criteria

- The customer recognizes at least one finding as a real operational risk.
- The report can be understood by an operator without reading code.
- The customer agrees on one follow-up:
  - another audit with richer exports,
  - a paid monthly scenario runner,
  - or a Live Validation pilot for an automation workflow.

## Suggested Commercial Shape

Start simple:

```txt
$500-$2,000 per Offline Audit POC
```

Include:

- One data mapping pass.
- One audit report.
- One review call.
- Three to five recommended fixes.

Do not promise a full platform integration in the first POC.
