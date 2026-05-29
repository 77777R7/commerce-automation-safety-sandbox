# SCN-002 Timeout After Commit Unsafe Retry - good_runner

- Run ID: `run_20260529T200547175031Z_SCN-002_good_runner`
- Status: `passed`
- Runner: `good_runner`
- Demo meaning: 通过：同一场景下没有产生 policy violation。

## 这次运行证明了什么

好流程使用稳定 idempotency_key，并在 timeout 后查询已提交的 fulfillment。

## Accident Signals

- No accident signals were true.

## Timeline

1. Fulfillment task task_fulfill_2001 received for order order_2001 with fault timeout_after_commit.
2. good_runner starts task task_fulfill_2001 with stable idempotency key.
3. good_runner creates fulfillment ful_001 for order order_2001, sku sku_retry_1.
4. Twin committed fulfillment ful_001, then returned timeout_after_commit.
5. good_runner receives timeout_after_commit and checks existing fulfillment state before retrying.
6. good_runner confirms fulfillment ful_001 already committed.
7. Policy check passed with no violations.

## 原始系统报告

# Commerce Safety Report: timeout_after_commit_retry

- Run ID: `run_20260529T200547175031Z_SCN-002_good_runner`
- Runner: `good_runner`
- Status: `passed`

## Business Risk Summary

- Risk: timeout_after_commit_retry completed without policy findings.
- Possible impact: No immediate commerce accident was detected in this run.
- Recommended control: Keep the same guardrails and rerun this scenario after automation changes.

## Executive Summary

The automation handled timeout-after-commit without creating a duplicate fulfillment.
It used a stable idempotency key and confirmed the already-committed fulfillment before retrying.

## State Change

- Fulfillments before: `0`
- Fulfillments after: `1`
- Fulfillment promises before: `0`
- Fulfillment promises after: `0`
- Refunds before: `0`
- Refunds after: `0`
- Approval requests before: `0`
- Approval requests after: `0`
- Inventory releases before: `0`
- Inventory releases after: `0`
- Workflow holds before: `0`
- Workflow holds after: `0`
- Warehouse cancellation requests before: `0`
- Warehouse cancellation requests after: `0`
- Refund amount issued before: `0`
- Refund amount issued after: `0`
- Reserved inventory before: `{'sku_retry_1': 1}`
- Reserved inventory after: `{'sku_retry_1': 1}`
- Expected reserved inventory: `{'sku_retry_1': 1}`

## Findings

No policy violations were detected.
## What Worked

The automation treated timeout-after-commit as an uncertain state, reused a stable idempotency key, and confirmed the committed fulfillment instead of creating another one.


## Replay

Run `commerce-safety replay runs/run_20260529T200547175031Z_SCN-002_good_runner` to print the recorded timeline from `trace.json`.
