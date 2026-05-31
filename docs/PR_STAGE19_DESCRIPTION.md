# PR: Stage 19 Hosted Design Partner Trust Gate

## Summary

- Adds a hosted design-partner trust boundary around the existing MCP/HTTP live
  commerce sandbox: workspace isolation, API-token auth, RBAC/scopes, audit
  logging, rate limits, request-size limits, PII/secret warnings, session TTL,
  artifact retention metadata, signed artifact downloads, export/delete, token
  revoke, and workspace suspend.
- Keeps the permissive twin principle intact: unsafe commerce mutations are
  still allowed, then policy checks catch the business incident.
- Adds a POC Security Evidence Binder and hosted onboarding docs so a design
  partner can understand the no-real-store boundary before connecting staging
  agents or workflows.

## Review Scope

Use `stage19_release_candidate.yaml` as the authoritative file list for this
PR. Generated demo artifacts, failure-intelligence experiments, and unrelated
historical workspace noise should be excluded from this Stage 19 review unless
they appear in that manifest.

## Test Plan

- [x] `PYTHON=/private/tmp/commerce-safety-stage9-venv/bin/python ./tools/smoke_stage19_hosted_enterprise_poc.sh`
- [x] `PYTHON=/private/tmp/commerce-safety-stage9-venv/bin/python ./tools/smoke_stage15_release_hygiene.sh`
- [x] `PYTHON=/private/tmp/commerce-safety-stage9-venv/bin/python ./tools/smoke_stage16_security_abuse.sh`
- [x] `PYTHON=/private/tmp/commerce-safety-stage9-venv/bin/python ./tools/smoke_v35.sh`

## Non-Goals

- Full SOC2 certification.
- Full hosted enterprise SaaS.
- SSO/SAML.
- Billing.
- VPC/private deployment.
- Firecracker/gVisor.
- More platform skins.
- Buyer simulator.

## After Merge

Stop platform engineering and move to design-partner activation: 1-3 staging
agent/workflow integrations, incident feedback, and paid POC validation.
