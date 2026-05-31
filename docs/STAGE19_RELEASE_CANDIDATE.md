# Stage 19 Release Candidate

This document is the review surface for the Stage 19 hosted design-partner
trust gate. It exists because the current workspace contains historical demo
artifacts and generated files that should not distract from the Stage 19 PR.

## Include In Stage 19 Review

Review the paths listed in `stage19_release_candidate.yaml`.

The core source changes are:

- `commerce_safety.live.hosted`: workspace, token, RBAC, audit, limit,
  PII/secret warning, deletion/export, signed artifact URL primitives.
- `commerce_safety.live.hosted_mcp_tools`: hosted MCP semantic wrapper with
  API-token authorization and workspace isolation.
- `commerce_safety.live.http_api`: hosted trust-store integration around the
  existing permissive HTTP twin.
- `commerce_safety.live.sessions`: workspace, session TTL, and artifact
  retention metadata.
- `commerce_safety.artifacts`: run manifest workspace/session/retention
  metadata and artifact PII status.

The proof surface is:

- `tests/test_stage19_hosted_trust_gate.py`
- `tools/smoke_stage19_*.sh`
- `docs/STAGE19_HOSTED_DESIGN_PARTNER_TRUST_GATE.md`
- `docs/security/*`
- `docs/HOSTED_DESIGN_PARTNER_ONBOARDING.md`

## Exclude From Stage 19 Review

The Stage 19 release candidate should not include generated or deferred work
under these prefixes unless a separate PR explicitly owns them:

- `commerce-safety-site/`
- `demo_pack/`
- `demo_viewer/`
- `failure_intelligence/`
- `offline_audits/`
- `outputs/`
- `regressions/`
- `runs/`

## Required Gates

```bash
PYTHON=python3.12 ./tools/smoke_stage19_release_candidate.sh
PYTHON=python3.12 ./tools/smoke_stage19_hosted_enterprise_poc.sh
PYTHON=python3.12 ./tools/smoke_stage15_release_hygiene.sh
PYTHON=python3.12 ./tools/smoke_stage16_security_abuse.sh
PYTHON=python3.12 ./tools/smoke_v35.sh
```

`smoke_v35.sh` starts local HTTP servers. In this Codex sandbox it may require
elevated execution for `127.0.0.1` binding.

## Residual Worktree Noise

At the time this release candidate was prepared, the branch already contained
many historical modified/untracked files from previous stages, generated demo
artifacts, and failure-intelligence experiments. Do not treat those as Stage 19
source unless they appear in `stage19_release_candidate.yaml`.

## Stop Line

After Stage 19 passes, stop platform engineering. Move to 1-3 design partners,
real staging-agent/workflow integrations, incident feedback, and paid POC
validation.
