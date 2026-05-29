# Demo Walkthrough

Use this as a 12-15 minute sales demo script.

## 1. Position The Problem

Commerce automation is risky because order, inventory, fulfillment, refund, webhook, retry, and warehouse states overlap. A workflow can technically succeed while creating a business accident.

## 2. Show The Core Mechanic

Run the timeout-after-commit scenario because it is easy to understand:

```bash
./commerce-safety run commerce-safety-sandbox/scenarios/SCN-002_timeout_after_commit_retry.yaml --runner bad_runner
```

Explain:

- The first fulfillment commits inside the twin.
- The runner receives a timeout.
- Bad automation retries as a new mutation.
- Policy Engine catches duplicate fulfillment and missing idempotency.

Then replay:

```bash
./commerce-safety replay runs/<run_id>
```

## 3. Show The Contrast

Run the same scenario with the safe path:

```bash
./commerce-safety run commerce-safety-sandbox/scenarios/SCN-002_timeout_after_commit_retry.yaml --runner good_runner
```

Explain that the scenario did not change. The automation did.

## 4. Open The Demo Pack

Open `demo_pack/executive_summary.md`, then open the scenario's `policy_findings.md` and `trace_summary.md`.

Point out:

- Business impact.
- Evidence.
- Recommendation.
- State diff artifacts for engineering follow-up.

## 5. Transition To Offline Audit POC

For seller/operator prospects, do not sell a full sandbox first. Offer the audit:

```txt
Send us order, inventory, fulfillment, and refund exports. We will reconstruct the risk state and return a report showing where automation can create duplicate fulfillment, oversell, refund, or warehouse conflicts.
```

## 6. Close With The Gate

The future product gate is simple:

```txt
If policy_report.json has findings, automation does not go live.
```
