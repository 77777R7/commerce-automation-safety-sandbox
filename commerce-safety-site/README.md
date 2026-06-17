# Agent Integration Safety Site

This is the product website for the SaaS Agent Validation Sandbox. It is now stored inside the main repo so the website source, demo narrative, and local preview path are all part of Git source of truth.

## Local Preview

Install dependencies once:

```bash
npm install
```

Run the canonical investor preview:

```bash
npm run preview:local
```

This syncs the SAAS-003 demo artifacts, builds the Vite app, and serves `dist/` on:

```text
http://127.0.0.1:5175
```

The preview server includes SPA fallback, so product routes such as these should return the app instead of a static-file 404:

```text
http://127.0.0.1:5175/demo/saas-003
http://127.0.0.1:5175/demo/connect
```

For source-mode development:

```bash
npm run dev
```

## Product Narrative

The site is no longer positioned around the previous storefront demo narrative. The public frame is now:

```text
Agent Integration Safety Sandbox
```

The first supported demo is `SAAS-003`, a duplicate-webhook incident review that shows:

- expected versus observed side effects
- failed versus passed agent behavior
- policy result
- state changes
- patch hints
- investor, design partner, and agent builder entry paths

Keep the hero general. The first V0 twins are billing, notification, and code-hosting workflows, but the website should describe the broader category: agents acting across external systems.

## Artifact Links

The site exposes selected SAAS-003 demo-pack artifacts under:

```text
/artifacts/saas-003/
```

Run this command whenever the demo pack changes:

```bash
npm run sync:artifacts
```

`npm run build` runs the same sync step automatically through `prebuild`.
