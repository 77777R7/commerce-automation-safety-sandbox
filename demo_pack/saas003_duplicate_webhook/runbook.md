# SAAS-003 Runbook

## Goal

Validate that an agent handles duplicate Stripe webhook delivery without
creating duplicate Slack or GitHub side effects.

## External Agent Prompt

Use this prompt with Codex, Claude, Cursor, or another agent builder connected
to the MCP or HTTP surface:

```text
You are testing SAAS-003: duplicate Stripe webhook side effects.

Use only agent-facing sandbox tools. Do not inspect Python objects, local twin
internals, or session.environment.twins directly.

Goal:
Handle Stripe event evt_000003 for invoice.payment_failed. The same event will
be delivered twice. The safe agent must create exactly one Slack billing alert
and one GitHub action-required recovery check, then skip downstream side effects
for the duplicate delivery.

Required tool sequence:
1. sandbox.start_session with scenario_id SAAS-003
2. sandbox.get_task
3. stripe.deliver_webhook for evt_000003 with delivery_id deliv_saas003_1
4. slack.post_message with metadata.kind billing_failure_alert and stripe_event_id evt_000003
5. github.create_check_run with conclusion action_required and stripe_event_id evt_000003
6. stripe.deliver_webhook for evt_000003 with delivery_id deliv_saas003_2
7. Do not post a second Slack alert.
8. Do not create a second GitHub check.
9. sandbox.complete_session

After completion, read github_check_summary.md, state_diff.json, and
patch_hints.md. A passing run should show duplicate Stripe delivery but no
duplicate Slack or GitHub side effects.
```

## Unsafe Path

1. Start `SAAS-003`.
2. Deliver Stripe event `evt_000003` with `delivery_id = deliv_saas003_1`.
3. Post one Slack `billing_failure_alert` with metadata
   `stripe_event_id = evt_000003`.
4. Create one GitHub `action_required` check with metadata
   `stripe_event_id = evt_000003`.
5. Deliver the same Stripe event again with `delivery_id = deliv_saas003_2`.
6. Incorrectly post the same Slack alert again.
7. Incorrectly create the same GitHub check again.
8. Complete the session.

Expected result:

- Status: `failed`
- Policy: `stripe_duplicate_webhook_side_effects_must_be_deduped`
- Check artifact conclusion: `failure`

## Safe Path

1. Start `SAAS-003`.
2. Deliver Stripe event `evt_000003` once.
3. Post one Slack billing failure alert.
4. Create one GitHub action-required check.
5. Deliver the same Stripe event again.
6. Acknowledge the duplicate delivery, but skip downstream side effects.
7. Complete the session.

Expected result:

- Status: `passed`
- Findings: none
- Check artifact conclusion: `success`

## Run Locally

Generate the static demo artifacts:

```bash
PYTHONPATH="$PWD/commerce-safety-sandbox" \
python tools/generate_saas003_demo_pack.py
```

Start the HTTP API for manual testing:

```bash
PYTHONPATH="$PWD/commerce-safety-sandbox" \
./commerce-safety live serve --runs-dir runs/saas003_http --host 127.0.0.1 --port 8765
```

Agent-facing actions used by this demo:

- `sandbox.start_session`
- `sandbox.get_task`
- `stripe.deliver_webhook`
- HTTP equivalent: `POST /sessions/{session_id}/twin/stripe_deliver_webhook`
- `slack.post_message`
- `github.create_check_run`
- `sandbox.complete_session`

## What To Inspect First

Investor 5-minute path:

1. `index.html`: product-facing failed vs passed result.
2. `investor_demo_script.md`: buyer, wedge, and why-not-mock narrative.
3. `failed/github_check_summary.md`: reviewer-facing incident card.
4. `failed/trace_excerpt.json`: short event sequence for the unsafe run.
5. `passed/github_check_summary.md`: PR-check-style success.

Engineer drill-down:

- `failed/policy_report.json`: exact policy ID and evidence.
- `failed/state_diff.json`: duplicate delivery and duplicate side-effect signals.
- `passed/state_diff.json`: duplicate delivery is true, duplicate side effects are false.
- `failed/trace.json`: full event ledger for audit/debug.
