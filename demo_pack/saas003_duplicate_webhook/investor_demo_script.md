# Investor Demo Script

## Opening

Most teams know webhooks can retry. The hard part is proving an AI agent will
not turn one retried event into two customer-facing or operator-facing actions.

SAAS-003 demonstrates exactly that.

## Who Pays

The buyer is a team shipping AI agents or automation into billing, support, or
developer workflows where the agent can call Stripe, Slack, GitHub, or similar
SaaS tools.

They pay because a normal unit test can pass while the agent still creates real
external-service damage: duplicate alerts, duplicate recovery work, false green
checks, or silent billing failures.

## Why Now

AI agents are moving from read-only copilots into tool-using operators. They can
post Slack messages, create GitHub checks, and trigger billing recovery flows.
Those actions need a sandbox that validates side effects before production.

## Why This Is Not A Mock

Static mock:

- returns fixture responses,
- does not remember duplicate webhook delivery,
- does not know whether Slack or GitHub was mutated downstream.

This sandbox:

- records Stripe delivery count,
- records Slack and GitHub state mutations,
- detects duplicate side effects for the same Stripe event ID,
- returns PR-check-style artifacts that explain the repair guardrail.

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
- The first screen says exactly what happened: one Stripe event created two
  Slack alerts and two GitHub recovery checks.

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
