# Investor Demo Script

## Opening

Most teams know webhooks can retry. The hard part is proving an AI agent will
not turn one retried event into two customer-facing or operator-facing actions.

SAAS-003 demonstrates exactly that.

## Demo Beat

Show the unsafe run:

```txt
Stripe duplicate webhook -> duplicate Slack alerts -> duplicate GitHub checks
```

Open:

- `sample_outputs/failed/github_check_summary.md`
- `sample_outputs/failed/state_diff.json`

Point out:

- The twin allowed the agent to make the mistake.
- The policy pack detected the duplicate side effects after the run.
- The artifact looks like something a PR reviewer or agent builder can consume.

## Safe Contrast

Open:

- `sample_outputs/passed/github_check_summary.md`
- `sample_outputs/passed/state_diff.json`

Point out:

- Duplicate delivery still happened.
- The agent preserved exactly one Slack alert and one GitHub check.
- The same policy pack now passes.

## Close

This is not a mock checkout flow. It is a repeatable validation harness for
stateful SaaS edge cases across external-service twins.
