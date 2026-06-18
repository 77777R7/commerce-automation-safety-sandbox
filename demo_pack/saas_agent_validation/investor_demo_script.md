# Investor Demo Script

## Title

Crash-test AI agents before they touch Stripe, Slack, and GitHub.

## Opening

AI agents are starting to operate billing, incident notification, and developer
workflow tools. The dangerous failure is not a single bad API call. It is a
cross-service lie: payment failed, humans were not notified, but the PR or
customer state still says success.

## Demo

SAAS-001 gives the agent local stateful twins for Stripe, Slack, and GitHub.
We inject a failed Stripe payment and a Slack private-channel permission fault.
The unsafe agent still publishes success state. The sandbox does not block the
calls upfront. It lets them happen, records the event ledger, then evaluates
policy.

The result is a traceable incident report:

- Stripe: payment requires a new payment method.
- Slack: billing alert failed with `not_in_channel`.
- GitHub: check run was marked `success`.
- Policy: false success state is blocked before production.

## Product Point

Official sandboxes prove API shape. This product proves workflow safety across
services. The buyer is the team shipping AI agents into billing, notification,
and DevOps workflows where false-green states are expensive.

## Close

The wedge is simple: bring one staging workflow or action log, run it against
the twins, and return `trace.json`, `policy_report.json`, `state_diff.json`,
`patch_hints.json`, and `run_manifest.json`.

