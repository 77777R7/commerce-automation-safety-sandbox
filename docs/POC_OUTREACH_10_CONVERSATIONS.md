# 10-Conversation POC Outreach Plan

## Goal

Book 10 focused conversations with people who already operate or build commerce
automation that touches orders, inventory, fulfillment, tracking, refunds, or
warehouse state.

The goal is not generic feedback. The goal is to test whether they recognize the
P0/P1 accident scenarios and would pay $500-$2,000 for a focused safety POC.

## Target Mix

| Segment | Count | Best Demo |
| --- | ---: | --- |
| Shopify merchant / DTC operator | 3 | P1-001 shared inventory, P1-003 tracking, P1-002 refund |
| Shopify agency / automation consultant | 2 | P1 variants plus SCN-001/SCN-002 |
| AI support / Gorgias / after-sales SaaS | 2 | P1-002 refund boundary, P1-003 tracking |
| n8n / Make / Zapier commerce automation builder | 2 | SCN-001 webhook, SCN-002 retry, P1-003 tracking |
| ERP / OMS / WMS / 3PL implementer | 1 | SCN-003 inventory, SCN-005 warehouse conflict |

## First Message

```txt
Hey [Name], quick question. I am building a pre-production safety sandbox for
commerce automation and AI agents.

It tests failure cases like stale inventory causing oversell, duplicate webhooks
creating duplicate fulfillment, shipped orders being refunded without approval,
and tracking being sent before carrier first scan.

Would you be open to a 20-minute call? I am trying to learn whether teams would
pay $500-$2,000 for a focused safety report using one anonymized workflow or
sample export.
```

## Follow-Up If They Ask "What Do You Need From Me?"

```txt
For the first POC, only one of these:

1. a workflow/action log,
2. anonymized order/inventory/refund/fulfillment samples,
3. a description of one automation you are nervous about.

We run 3-5 accident scenarios and return trace replay, policy findings, and
recommended fixes. We do not need production credentials for the first pass.
```

## Call Structure

1. Ask what they automate today.
2. Ask which actions can move money or goods.
3. Show the closest P1/P0 scenario.
4. Ask whether this failure has happened or feels plausible.
5. Ask how they test before promos or workflow changes.
6. Ask the POC price question directly.

## Qualification Questions

- What system is the source of truth for inventory?
- Do you use Shopify Flow, n8n, Make, Zapier, Gorgias, ERP, WMS, 3PL, or custom scripts?
- Can automation trigger fulfillment, refund, cancellation, reshipment, or tracking upload?
- Do you have manual review queues for risky actions?
- When something fails, do you have a replayable trace?
- What was the last automation incident that cost money or support time?

## POC Close

```txt
If we run your flow through 3-5 scenarios and give you a risk report with
replayable traces and fix recommendations, is $500-$2,000 reasonable for a
first POC?
```

## Record After Each Call

Use a simple table:

| Field | Notes |
| --- | --- |
| Segment | Shopify merchant / agency / SaaS / workflow builder / ERP |
| Current automation | Tools and actions |
| Risk actions | Refund, fulfillment, tracking, inventory, cancel, reship |
| Recognized scenarios | Which P0/P1 made them nod |
| Real incident mentioned | Yes/no plus summary |
| POC willingness | No / maybe / yes |
| Price reaction | $500 / $1k / $2k / other |
| Next step | Demo, sample data, intro, no fit |
