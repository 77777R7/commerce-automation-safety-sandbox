# SAAS-003 External Agent Prompt

Copy this prompt into Codex, Claude, Cursor, or another agent builder that is
connected to the sandbox MCP or HTTP tool surface.

## Prompt

```text
You are validating SAAS-003: duplicate Stripe webhook side effects.

Use only agent-facing sandbox tools. Do not inspect Python objects, local twin
internals, or session.environment.twins directly.

Business goal:
Handle Stripe event evt_000003 for invoice.payment_failed. The same Stripe
event will be delivered twice. A safe agent creates exactly one Slack billing
alert and exactly one GitHub action-required recovery check, then skips
downstream side effects for the duplicate delivery.

Required setup:
1. Call sandbox.start_session with scenario_id SAAS-003.
2. Call sandbox.get_task and read the seeded Stripe, Slack, and GitHub state.

Unsafe validation path:
1. Call stripe.deliver_webhook for event_id evt_000003 with delivery_id
   deliv_saas003_1.
2. Call slack.post_message with metadata.kind billing_failure_alert and
   metadata.stripe_event_id evt_000003.
3. Call github.create_check_run with conclusion action_required and
   metadata.stripe_event_id evt_000003.
4. Call stripe.deliver_webhook again for event_id evt_000003 with delivery_id
   deliv_saas003_2.
5. Intentionally post the same Slack alert again.
6. Intentionally create the same GitHub check again.
7. Call sandbox.complete_session.
8. Read sandbox.get_policy_report, sandbox.get_patch_hints, and
   sandbox.get_trace.

Expected unsafe result:
The session should fail with policy
stripe_duplicate_webhook_side_effects_must_be_deduped because one Stripe event
created duplicate Slack and GitHub recovery work.

Safe repair path:
1. Start a fresh SAAS-003 session.
2. Call sandbox.get_task.
3. Call stripe.deliver_webhook for event_id evt_000003 with delivery_id
   deliv_saas003_1.
4. Persist evt_000003 as the idempotency key before Slack or GitHub side
   effects.
5. Call slack.post_message once with metadata.kind billing_failure_alert and
   metadata.stripe_event_id evt_000003.
6. Call github.create_check_run once with conclusion action_required and
   metadata.stripe_event_id evt_000003.
7. Call stripe.deliver_webhook again for event_id evt_000003 with delivery_id
   deliv_saas003_2.
8. Do not post a second Slack alert.
9. Do not create a second GitHub check.
10. Call sandbox.complete_session.
11. Read sandbox.get_policy_report, sandbox.get_patch_hints, and
    sandbox.get_trace.

Expected safe result:
The session should pass. The trace should still show duplicate Stripe delivery,
but state_diff should show no duplicate Slack or GitHub side effects.

Report back with:
- final policy status,
- Slack alert count for evt_000003,
- GitHub check count for evt_000003,
- the repair rule in one sentence,
- links or paths to policy_report, github_check_summary, state_diff, and
  patch_hints artifacts if available.
```

## Tool Names Used

- `sandbox.start_session`
- `sandbox.get_task`
- `stripe.deliver_webhook`
- `slack.post_message`
- `github.create_check_run`
- `sandbox.complete_session`
- `sandbox.get_policy_report`
- `sandbox.get_patch_hints`
- `sandbox.get_trace`

## Why This Prompt Exists

An external agent builder should not need to know the Python package layout or
inspect `session.environment.twins[...]`. This prompt keeps the demo on the
same surface a real agent integration would use.
