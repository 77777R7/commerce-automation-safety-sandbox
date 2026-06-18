# Website Guidelines

This site is the public product surface for the Agent Integration Safety Sandbox.

## Narrative

- Keep the hero general: the product validates AI agents that act across external systems.
- Do not position the product as only billing, notification, code-hosting, commerce, or marketplace automation.
- The current V0 demo is `SAAS-003`, but the category should feel broader than one scenario.
- Avoid exposing old storefront, inventory, fulfillment, or marketplace language in public pages.

## Reader Paths

- Investor: understand the incident in 30 seconds.
- Design partner: map one risky workflow to a repeatable validation scenario.
- Agent builder: run an external agent through MCP or HTTP and inspect evidence.

## Demo Contract

The primary demo route is `/demo/saas-003`.

The review page should always make these ideas obvious:

- one upstream event
- expected versus observed side effects
- unsafe versus safe path
- policy result
- state changes
- patch hints

The page should also link to the concrete evidence artifacts: PR-check summary, policy report, state diff, trace excerpt, patch hints, and run manifest.

## Local Preview

Use `npm run preview:local` for investor review. It builds the app and serves `dist/` with SPA fallback so `/demo/*` routes do not 404.

Builds automatically run `npm run sync:artifacts`, which copies selected files from `../demo_pack/saas003_duplicate_webhook` into `public/artifacts/saas-003`.
