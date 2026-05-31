# Stage 15: Release Hygiene + CI Gate

Stage 15 makes the V3.5 worktree reviewable by an outside engineer. It does
not add a new platform skin or scenario surface.

## Goals

- Keep source changes and generated artifacts in separate PRs.
- Make local machine path leaks fail before review.
- Make CI run the same gates that prove the agent-facing surface works.
- Pin CI dependencies so the release gate is repeatable.
- Preserve the current V3.5 product boundary: MCP/HTTP live validation first,
  no hosted control plane, no buyer simulator, no full Shopify or Amazon clone.

## Source PR vs Generated Artifacts PR

Use `release_hygiene.yaml` as the review manifest.

The source PR may include runtime code, tests, smoke gates, OpenAPI, docs, and
CI workflow changes.

Generated artifacts belong in a separate generated artifacts PR. This includes:

- `demo_pack/`
- `demo_viewer/`
- `failure_intelligence/`
- `commerce-safety-site/`
- runtime outputs such as `runs/`, `outputs/`, `offline_audits/`, and
  `regressions/`

This split keeps a reviewer from missing runtime risk inside regenerated demo
collateral.

## CI Gate

The GitHub Actions workflow is `.github/workflows/v35-ci.yml`.

It runs:

- Stage 15 release hygiene.
- Unit tests with `python -m pytest`.
- Real MCP/API hardening gates.
- Full P0 MCP and HTTP coverage.
- Strict OpenAPI contract gate with zero Schemathesis warnings.
- Shopify-like Skin V0 gate.
- Amazon Seller Ops Skin HTTP and MCP gates.

## Local Gate

Run:

```bash
PYTHON=python3.12 ./tools/smoke_stage15_release_hygiene.sh
```

The full V3.5 gate includes Stage 15:

```bash
PYTHON=python3.12 ./tools/smoke_v35.sh
```

## Non-Goals

- Do not delete or regenerate demo artifacts as part of the source PR.
- Do not add a new P0 scenario.
- Do not add a new platform skin.
- Do not build hosted sessions, an agent container, or a decorative dashboard.
